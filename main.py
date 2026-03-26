import sys
import os
import math
import numpy as np
import pygame
import moderngl

from dashboard import run_dashboard


def resource_path(filename):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)
from camera import Camera
from config import (
    WIDTH, HEIGHT, TITLE, FPS,
    REGIONS, COLORMAPS, VOID, INTRO, MINIMAP, ADVANCED_DEFAULTS,
    HEIGHT_EXP, WORLD_SCALE_MIN, WORLD_SCALE_MAX, WORLD_SCALE_ZOOM_FACTOR
)

CMAP_INDEX = {name: i for i, name in enumerate(COLORMAPS)}

STATE_INTRO    = "intro"
STATE_WALK     = "walk"
STATE_VOID     = "void"
STATE_RESPAWN  = "respawn"
DE_MAX_ITER = 512


def py_de(cx, cz):
    zr, zi   = 0.0, 0.0
    dzr, dzi = 0.0, 0.0
    for _ in range(DE_MAX_ITER):
        dzr, dzi = 2*(zr*dzr - zi*dzi) + 1, 2*(zr*dzi + zi*dzr)
        zr, zi   = zr*zr - zi*zi + cx, 2*zr*zi + cz
        m2 = zr*zr + zi*zi
        if m2 > 256.0:
            dm2 = max(dzr*dzr + dzi*dzi, 1e-20)
            return 0.5 * math.sqrt(m2 / dm2) * math.log(m2)
    return 0.0


def py_escape_iter(cx, cz, max_iter=72):
    zr, zi = 0.0, 0.0
    for i in range(max_iter):
        zr, zi = zr*zr - zi*zi + cx, 2*zr*zi + cz
        if zr*zr + zi*zi > 4.0:
            return i
    return -1


class App:
    def __init__(self, settings):
        self.settings = settings

        # Inject advanced defaults if dashboard omitted them
        self.settings.setdefault("eye_height", ADVANCED_DEFAULTS["eye_height"])
        self.settings.setdefault("slab_thickness", ADVANCED_DEFAULTS["slab_thickness"])
        self.settings.setdefault("world_scale", ADVANCED_DEFAULTS["world_scale"])
        self.settings.setdefault("ground_follow_speed", ADVANCED_DEFAULTS["ground_follow_speed"])
        self.settings.setdefault("water_y", VOID["water_y"])
        self.settings.setdefault("height_exp", HEIGHT_EXP)

        pygame.init()
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        pygame.display.set_mode((WIDTH, HEIGHT), flags)
        pygame.display.set_caption(TITLE)
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        self.ctx   = moderngl.create_context()
        self.clock = pygame.time.Clock()

        self._build_quad()
        self._build_program()
        self._init_session()
        self._build_minimap()

    def _build_quad(self):
        verts = np.array([
            -1, -1,   1, -1,  -1, 1,
             1, -1,   1,  1,  -1, 1,
        ], dtype=np.float32)
        self.vbo = self.ctx.buffer(verts.tobytes())

    def _build_program(self):
        with open(resource_path("vert.glsl"), "r", encoding="utf-8") as f:
            vert = f.read()
        with open(resource_path("frag.glsl"), "r", encoding="utf-8") as f:
            frag = f.read()
        self.prog = self.ctx.program(vertex_shader=vert, fragment_shader=frag)
        self.vao  = self.ctx.vertex_array(self.prog, [(self.vbo, "2f", "in_vert")])

    def _u(self, name, val):
        if name in self.prog:
            self.prog[name].value = val

    #===========
    # Coordinates / terrain
    #===========

    def _world_to_fractal(self, x, z):
        s = self.settings["world_scale"]
        return x / s, z / s

    def _scale_xz(self, v, factor):
        if v is None:
            return
        v[0] *= factor
        v[2] *= factor

    def _apply_world_scale(self, new_scale):
        old_scale = self.settings["world_scale"]
        if abs(new_scale - old_scale) < 1e-9:
            return
        factor = new_scale / old_scale
        self.settings["world_scale"] = new_scale

        self._scale_xz(self.camera.pos, factor)
        self._scale_xz(self.camera.orbit_target, factor)
        self._scale_xz(self.spawn_pos, factor)
        self._scale_xz(self.last_safe_pos, factor)
        self._scale_xz(self.void_entry, factor)
        self._scale_xz(self.intro_from, factor)
        self._scale_xz(self.intro_to, factor)
        self.camera.orbit_radius *= factor

    def _adjust_world_scale(self, factor):
        new_scale = float(np.clip(self.settings["world_scale"] * factor, WORLD_SCALE_MIN, WORLD_SCALE_MAX))
        self._apply_world_scale(new_scale)

    def _de_world(self, x, z):
        fx, fz = self._world_to_fractal(x, z)
        return py_de(float(fx), float(fz))

    def _surface_y(self, x, z):
        de = max(self._de_world(x, z), 0.0)
        return (de ** self.settings["height_exp"]) * self.settings["height_scale"]

    #===========
    # Safe spawn search
    #===========

    def _find_safe_spawn_xz(self, seed_x, seed_z):
        cfg = ADVANCED_DEFAULTS["safe_spawn"]
        min_de = cfg["min_de"]
        r0 = cfg["search_r0"] * self.settings["world_scale"]
        rmax = cfg["search_rmax"] * self.settings["world_scale"]
        rings = cfg["rings"]
        samples = cfg["samples"]

        # Try seed first
        if self._de_world(seed_x, seed_z) >= min_de:
            return np.array([seed_x, seed_z], dtype=np.float32)

        best = None
        best_score = -1e9

        for ri in range(rings):
            t = ri / max(1, rings - 1)
            r = r0 + (rmax - r0) * t
            for si in range(samples):
                a = (2.0 * math.pi) * (si / samples)
                x = seed_x + math.cos(a) * r
                z = seed_z + math.sin(a) * r
                de = self._de_world(x, z)

                # Prefer safe DE and flatter local patch
                eps = 0.02 * self.settings["world_scale"]
                gx = abs(self._surface_y(x + eps, z) - self._surface_y(x - eps, z))
                gz = abs(self._surface_y(x, z + eps) - self._surface_y(x, z - eps))
                slope = gx + gz
                score = de * 2.0 - slope * 0.8 - r * 0.02

                if de >= min_de and score > best_score:
                    best_score = score
                    best = (x, z)

        if best is not None:
            return np.array(best, dtype=np.float32)

        # Hard fallback: shift outward on +x in world space
        return np.array([seed_x + 0.35 * self.settings["world_scale"], seed_z], dtype=np.float32)

    def _init_session(self):
        region = REGIONS[self.settings["region"]]
        raw_sp = np.array(region["spawn"], dtype=np.float32)
        raw_if = np.array(region["intro_from"], dtype=np.float32)
        scale = self.settings["world_scale"]
        seed_x = float(raw_sp[0] * scale)
        seed_z = float(raw_sp[2] * scale)
        safe_xz = self._find_safe_spawn_xz(seed_x, seed_z)

        eye_h = self.settings["eye_height"]
        sy = self._surface_y(float(safe_xz[0]), float(safe_xz[1]))
        spawn = np.array([safe_xz[0], sy + eye_h, safe_xz[1]], dtype=np.float32)

        intro = raw_if.copy()
        intro[0] = safe_xz[0]
        intro[2] = safe_xz[1]
        intro[1] = max(float(raw_if[1]), float(spawn[1] + 2.8))

        self.camera = Camera(
            position=list(intro),
            fov=self.settings["fov"],
            aspect=WIDTH / HEIGHT,
        )
        self.camera.speed = self.settings["speed"]
        self.camera.pitch = -60.0
        self.camera._update_vectors()

        self.intro_from  = intro.copy()
        self.intro_to    = spawn.copy()
        self.intro_t     = 0.0

        self.spawn_pos   = spawn.copy()
        self.spawn_pitch = -15.0
        self.spawn_yaw   = self.camera.yaw

        self.last_safe_pos = spawn.copy()

        self.state       = STATE_INTRO
        self.time        = 0.0
        self.in_void     = False
        self.fade        = 0.0
        self.void_entry  = np.zeros(3, dtype=np.float32)
        self.fall_vel    = 0.0
        self.fall_dist   = 0.0
        self.fullscreen  = False
        self.orbital_drag = False
        self.respawn_grace_t = VOID["respawn_grace"]

    #===========
    # Minimap
    #===========

    def _build_minimap(self):
        size = int(MINIMAP["size"])
        x0, x1 = MINIMAP["x_range"]
        z0, z1 = MINIMAP["z_range"]
        max_iter = int(MINIMAP["max_iter"])

        arr = np.zeros((size, size, 3), dtype=np.uint8)

        for py in range(size):
            tz = py / (size - 1)
            z = z1 + (z0 - z1) * tz
            for px in range(size):
                tx = px / (size - 1)
                x = x0 + (x1 - x0) * tx

                it = py_escape_iter(x, z, max_iter=max_iter)
                if it < 0:
                    c = (8, 8, 12)
                else:
                    t = it / max_iter
                    c = (
                        int(20 + 180 * t),
                        int(30 + 120 * (1 - t)),
                        int(80 + 140 * (1 - t * 0.7)),
                    )
                arr[py, px] = c

        surf = pygame.image.frombuffer(arr.tobytes(), (size, size), "RGB")
        self.minimap_surface = surf.convert()
        panel_w = size + 8
        panel_h = size + 8
        self.minimap_panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        self.minimap_texture = self.ctx.texture((panel_w, panel_h), 4)
        self.minimap_texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.minimap_texture.repeat_x = False
        self.minimap_texture.repeat_y = False

        margin = int(MINIMAP["margin"])
        x0 = margin / WIDTH
        x1 = (margin + panel_w) / WIDTH
        y1 = 1.0 - margin / HEIGHT
        y0 = y1 - (panel_h / HEIGHT)
        self.minimap_rect_uv = (x0, y0, x1, y1)

    def _world_to_minimap_px(self, wx, wz):
        size = int(MINIMAP["size"])
        x0, x1 = MINIMAP["x_range"]
        z0, z1 = MINIMAP["z_range"]

        # world -> fractal coords for map
        fx, fz = self._world_to_fractal(wx, wz)

        tx = (fx - x0) / (x1 - x0)
        tz = (fz - z0) / (z1 - z0)
        px = int(np.clip(tx, 0.0, 1.0) * (size - 1))
        py = int((1.0 - np.clip(tz, 0.0, 1.0)) * (size - 1))
        return px, py

    def _update_minimap_texture(self):
        panel = self.minimap_panel
        panel.fill((0, 0, 0, 130))
        panel.blit(self.minimap_surface, (4, 4))

        px, py = self._world_to_minimap_px(float(self.camera.pos[0]), float(self.camera.pos[2]))
        dot_col = (255, 235, 80) if not self.in_void else (120, 200, 255)
        pygame.draw.circle(panel, dot_col, (4 + px, 4 + py), 3)

        fx, fz = float(self.camera.front[0]), float(self.camera.front[2])
        end = (4 + px + int(fx * 12), 4 + py - int(fz * 12))
        pygame.draw.line(panel, dot_col, (4 + px, 4 + py), end, 1)

        data = pygame.image.tostring(panel, "RGBA", True)
        self.minimap_texture.write(data)

    #===========
    # State transitions
    #===========

    def _enter_void(self):
        self.void_entry = self.camera.pos.copy()
        self.fall_vel   = 0.0
        self.fall_dist  = 0.0
        self.in_void    = True
        self.state      = STATE_VOID

    def _respawn(self):
        self.state   = STATE_RESPAWN
        self.fade    = 0.0
        self.in_void = False

    def _finish_respawn(self):
        # prefer last known safe, else spawn
        p = self.last_safe_pos.copy()
        de = self._de_world(float(p[0]), float(p[2]))
        if de <= ADVANCED_DEFAULTS["safe_spawn"]["min_de"]:
            p = self.spawn_pos.copy()

        p[1] = self._surface_y(float(p[0]), float(p[2])) + self.settings["eye_height"]

        self.camera.pos   = p
        self.camera.yaw   = self.spawn_yaw
        self.camera.pitch = self.spawn_pitch
        self.camera._update_vectors()

        self.fall_dist = 0.0
        self.fall_vel  = 0.0
        self.fade      = 1.0
        self.state     = STATE_WALK
        self.respawn_grace_t = VOID["respawn_grace"]

    #===========
    # Updates
    #===========

    def _update_intro(self, dt):
        self.intro_t += dt / INTRO["duration"]
        if self.intro_t >= 1.0:
            self.intro_t = 1.0
            self.state   = STATE_WALK
        self.camera.set_lerp(
            self.intro_from, self.intro_to,
            -70.0, self.spawn_pitch,
            self.intro_t,
        )

    def _update_walk(self, dt, keys, mdx, mdy):
        if self.camera.orbital:
            if self.orbital_drag:
                self.camera.update_orbital(mdx, mdy, self.scroll)
        else:
            self.camera.update_fps(
                dt,
                {
                    "forward":  keys[pygame.K_w],
                    "backward": keys[pygame.K_s],
                    "left":     keys[pygame.K_a],
                    "right":    keys[pygame.K_d],
                    "up":       keys[pygame.K_SPACE],
                    "down":     keys[pygame.K_LCTRL],
                },
                mdx, mdy, keys[pygame.K_LSHIFT]
            )

        # Grounded eye-level follow
        surf_y = self._surface_y(float(self.camera.pos[0]), float(self.camera.pos[2]))
        target_y = surf_y + self.settings["eye_height"]
        follow = self.settings["ground_follow_speed"]
        self.camera.pos[1] += (target_y - self.camera.pos[1]) * min(1.0, follow * dt)

        de = self._de_world(float(self.camera.pos[0]), float(self.camera.pos[2]))

        # Track safe point when comfortably outside interior
        if de >= ADVANCED_DEFAULTS["safe_spawn"]["min_de"] * 1.1:
            self.last_safe_pos = self.camera.pos.copy()

        # Grace window after spawn/respawn
        if self.respawn_grace_t > 0.0:
            self.respawn_grace_t = max(0.0, self.respawn_grace_t - dt)
        else:
            # Enter void on interior or significant terrain penetration
            if de <= VOID["interior_eps"] or self.camera.pos[1] < (surf_y - VOID["threshold"]):
                self._enter_void()

        if self.fade > 0.0:
            self.fade = max(0.0, self.fade - VOID["fade_speed"] * dt)

    def _update_void(self, dt):
        self.fall_vel  += VOID["gravity"] * dt
        self.fall_dist += self.fall_vel * dt
        self.camera.pos[1] -= self.fall_vel * dt
        if self.fall_dist >= self.settings["fall_depth"]:
            self._respawn()

    def _update_respawn(self, dt):
        self.fade += VOID["fade_speed"] * dt
        if self.fade >= 1.0:
            self._finish_respawn()

    def _upload_uniforms(self):
        cam = self.camera
        self._u("u_cam_pos",      tuple(cam.pos))
        self._u("u_cam_front",    tuple(cam.front))
        self._u("u_cam_right",    tuple(cam.right))
        self._u("u_cam_up",       tuple(cam.up))
        self._u("u_fov",          float(cam.fov))
        self._u("u_aspect",       float(cam.aspect))

        self._u("u_height_scale", float(self.settings["height_scale"]))
        self._u("u_height_exp",   float(self.settings["height_exp"]))
        self._u("u_colormap",     CMAP_INDEX.get(self.settings["colormap"], 0))
        self._u("u_time",         float(self.time))

        self._u("u_in_void",      1 if self.in_void else 0)
        self._u("u_fall_depth",   float(self.settings["fall_depth"]))
        self._u("u_fade",         float(self.fade))
        self._u("u_void_entry",   tuple(self.void_entry))

        self._u("u_slab_thickness", float(self.settings["slab_thickness"]))
        self._u("u_water_y",        float(self.settings["water_y"]))
        self._u("u_world_scale",    float(self.settings["world_scale"]))
        self._u("u_minimap_rect",   tuple(self.minimap_rect_uv))
        self._u("u_minimap",        0)
        self.minimap_texture.use(location=0)

    def run(self):

        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.time += dt
            mdx = mdy = 0
            self.scroll = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        settings = run_dashboard()
                        self.__init__(settings)
                        return self.run()
                    elif event.key == pygame.K_TAB:
                        self.camera.orbital = not self.camera.orbital
                        if self.camera.orbital:
                            self.camera.orbit_target = self.camera.pos + self.camera.front
                            self.camera.orbit_radius = 1.0
                            pygame.mouse.set_visible(True)
                            pygame.event.set_grab(False)
                        else:
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                    elif event.key == pygame.K_f:
                        self.fullscreen = not self.fullscreen
                        flag = pygame.OPENGL | pygame.DOUBLEBUF
                        if self.fullscreen:
                            flag |= pygame.FULLSCREEN
                        pygame.display.set_mode((WIDTH, HEIGHT), flag)
                    elif event.key == pygame.K_RIGHTBRACKET:
                        self._adjust_world_scale(WORLD_SCALE_ZOOM_FACTOR)
                    elif event.key == pygame.K_LEFTBRACKET:
                        self._adjust_world_scale(1.0 / WORLD_SCALE_ZOOM_FACTOR)
                    elif event.key == pygame.K_SPACE and self.state == STATE_INTRO:
                        self.intro_t = 1.0

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.orbital_drag = True
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.orbital_drag = False
                if event.type == pygame.MOUSEWHEEL:
                    self.scroll = event.y
                if event.type == pygame.MOUSEMOTION:
                    mdx += event.rel[0]
                    mdy += event.rel[1]

            if self.state == STATE_INTRO:
                self._update_intro(dt)
            elif self.state == STATE_WALK:
                keys = pygame.key.get_pressed()
                self._update_walk(dt, keys, mdx, mdy)
            elif self.state == STATE_VOID:
                self._update_void(dt)
            elif self.state == STATE_RESPAWN:
                self._update_respawn(dt)
            self._update_minimap_texture()

            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            self._upload_uniforms()
            self.vao.render(moderngl.TRIANGLES)
            pygame.display.flip()


if __name__ == "__main__":
    settings = run_dashboard()
    App(settings).run()
