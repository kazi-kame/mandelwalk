import pygame
import sys
import json
import time
import numpy as np

from mandelbrot import compute_mandelbrot, adaptive_max_iter, warmup_jit
from colors import iterations_to_rgb
from ui import UIManager
from config import (
    RESOLUTION,
    DASHBOARD_RESOLUTION,
    ZOOM_TARGETS,
    SETTINGS_FILE,
)

# --------------------------
# Persistence
# --------------------------
def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        data = {
            "fps": 60,
            "colormap": "inferno",
            "target": "seahorse_valley",
            "zoom_factor": 1.05,
            "duration": 20,
        }
    return data


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)


# --------------------------
# Mapping helpers
# --------------------------
def camera_to_viewport(center, view_w, aspect):
    cx, cy = center
    view_h = view_w / aspect
    top_left = (cx - view_w * 0.5, cy + view_h * 0.5)
    bottom_right = (cx + view_w * 0.5, cy - view_h * 0.5)
    return top_left, bottom_right


def screen_to_complex(px, py, screen_size, top_left, bottom_right):
    w, h = screen_size
    rx = px / max(1, w - 1)
    ry = py / max(1, h - 1)
    x = top_left[0] + rx * (bottom_right[0] - top_left[0])
    y = top_left[1] + ry * (bottom_right[1] - top_left[1])
    return x, y


# --------------------------
# Dashboard loop
# --------------------------
def run_dashboard(clock, settings):
    screen = pygame.display.set_mode(DASHBOARD_RESOLUTION)
    pygame.display.set_caption("Mandelbrot Zoom Simulator")
    ui = UIManager(screen)

    # Optional preload support
    if hasattr(ui, "apply_settings"):
        ui.apply_settings(settings)

    while True:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            ui.process_events(event)

        ui.update(dt)
        ui.draw()
        pygame.display.flip()

        if ui.get_play_state():
            return ui.get_all_settings()


# --------------------------
# Navigator mode (fullscreen)
# --------------------------
def run_navigator(clock, settings):
    screen = pygame.display.set_mode(RESOLUTION, pygame.FULLSCREEN)
    pygame.display.set_caption("Mandelbrot Navigator")

    W, H = RESOLUTION
    aspect = W / H

    # Spawn from selected target
    target_name = settings.get("target", "seahorse_valley")
    target = ZOOM_TARGETS.get(target_name, next(iter(ZOOM_TARGETS.values())))
    top_left0 = target["top_left"]
    bottom_right0 = target["bottom_right"]
    center = [
        (top_left0[0] + bottom_right0[0]) * 0.5,
        (top_left0[1] + bottom_right0[1]) * 0.5,
    ]
    base_view_w = (bottom_right0[0] - top_left0[0])
    if base_view_w <= 0:
        base_view_w = 3.5

    view_w = float(base_view_w)
    colormap = settings.get("colormap", "inferno")
    target_fps = int(settings.get("fps", 60))

    # Motion tuning
    pan_speed = 0.75        # fraction of view width per second
    zoom_speed = 1.5        # exponential zoom rate
    min_view_w = 1e-15
    max_view_w = 4.0

    # Drag state
    dragging = False
    last_mouse = (0, 0)

    # Render quality scaling: lower while moving, full when idle
    moving_recently_t = 0.0
    moving_timeout = 0.18
    render_scale_idle = 1.0
    render_scale_move = 0.65

    font = pygame.font.SysFont("consolas", 18)
    clock_fps = pygame.time.Clock()
    running = True

    while running:
        dt = clock_fps.tick(target_fps) / 1000.0
        now = time.time()

        # Input flags
        moved_this_frame = False
        recenter_click = None
        wheel_in = 0
        wheel_out = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "dashboard"
                if event.key == pygame.K_r:
                    center = [
                        (top_left0[0] + bottom_right0[0]) * 0.5,
                        (top_left0[1] + bottom_right0[1]) * 0.5,
                    ]
                    view_w = float(base_view_w)
                    moved_this_frame = True
                if event.key == pygame.K_c:
                    # cycle colormaps quickly
                    names = ["inferno", "electric", "lava", "ice", "gold", "psychedelic"]
                    if colormap not in names:
                        colormap = names[0]
                    else:
                        colormap = names[(names.index(colormap) + 1) % len(names)]
                    moved_this_frame = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    dragging = True
                    last_mouse = event.pos
                elif event.button == 3:
                    recenter_click = event.pos
                elif event.button == 4:
                    wheel_in += 1
                elif event.button == 5:
                    wheel_out += 1

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False

            elif event.type == pygame.MOUSEMOTION and dragging:
                mx, my = event.pos
                dx = mx - last_mouse[0]
                dy = my - last_mouse[1]
                last_mouse = (mx, my)

                top_left, bottom_right = camera_to_viewport(center, view_w, aspect)
                # Drag world opposite of mouse motion
                world_dx = -(dx / W) * (bottom_right[0] - top_left[0])
                world_dy = +(dy / H) * (top_left[1] - bottom_right[1])
                center[0] += world_dx
                center[1] += world_dy
                moved_this_frame = True

        # Keyboard continuous movement
        keys = pygame.key.get_pressed()
        speed_mul = 1.0
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            speed_mul = 0.3
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            speed_mul = 2.2

        pan_amount = pan_speed * view_w * dt * speed_mul
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            center[0] -= pan_amount
            moved_this_frame = True
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            center[0] += pan_amount
            moved_this_frame = True
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            center[1] += pan_amount
            moved_this_frame = True
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            center[1] -= pan_amount
            moved_this_frame = True

        # Keyboard zoom
        zoom_dir = 0.0
        if keys[pygame.K_q] or keys[pygame.K_EQUALS] or keys[pygame.K_KP_PLUS]:
            zoom_dir += 1.0
        if keys[pygame.K_e] or keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
            zoom_dir -= 1.0

        if zoom_dir != 0.0:
            factor = np.exp(-zoom_dir * zoom_speed * dt * speed_mul)
            view_w *= float(factor)
            view_w = float(np.clip(view_w, min_view_w, max_view_w))
            moved_this_frame = True

        # Wheel zoom (towards/away)
        if wheel_in:
            view_w *= (0.88 ** wheel_in)
            moved_this_frame = True
        if wheel_out:
            view_w *= (1.12 ** wheel_out)
            moved_this_frame = True
        view_w = float(np.clip(view_w, min_view_w, max_view_w))

        # Right click recenter
        if recenter_click is not None:
            top_left, bottom_right = camera_to_viewport(center, view_w, aspect)
            cx, cy = screen_to_complex(
                recenter_click[0], recenter_click[1],
                (W, H), top_left, bottom_right
            )
            center[0], center[1] = cx, cy
            moved_this_frame = True

        if moved_this_frame:
            moving_recently_t = now

        moving = (now - moving_recently_t) < moving_timeout
        render_scale = render_scale_move if moving else render_scale_idle

        rw = max(320, int(W * render_scale))
        rh = max(180, int(H * render_scale))

        # Compute viewport for render resolution
        top_left, bottom_right = camera_to_viewport(center, view_w, aspect)
        max_iter = adaptive_max_iter(top_left, bottom_right)
        smooth = compute_mandelbrot(rw, rh, top_left, bottom_right, max_iter)
        rgb = iterations_to_rgb(smooth, max_iter, colormap)

        surf = pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))
        if rw != W or rh != H:
            surf = pygame.transform.smoothscale(surf, (W, H))
        screen.blit(surf, (0, 0))

        # HUD
        hud_lines = [
            "ESC: dashboard  |  WASD/Arrows: move  |  Q/E or Wheel: zoom  |  RMB: recenter  |  LMB drag: pan  |  R: reset  |  C: colormap",
            f"center=({center[0]:.12f}, {center[1]:.12f})  view_w={view_w:.3e}  max_iter={max_iter}  fps={clock_fps.get_fps():.1f}  cmap={colormap}",
        ]
        y = 10
        for line in hud_lines:
            txt = font.render(line, True, (230, 230, 230))
            bg = pygame.Surface((txt.get_width() + 10, txt.get_height() + 6), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 130))
            screen.blit(bg, (8, y - 2))
            screen.blit(txt, (13, y + 1))
            y += txt.get_height() + 8

        pygame.display.flip()

    return "dashboard"


def main():
    pygame.init()

    # warmup splash
    splash = pygame.display.set_mode(DASHBOARD_RESOLUTION)
    pygame.display.set_caption("Mandelbrot Zoom Simulator")
    splash.fill((15, 15, 15))
    font = pygame.font.SysFont("monospace", 24)
    msg = font.render("Warming up JIT compiler — one moment...", True, (170, 170, 170))
    splash.blit(msg, (DASHBOARD_RESOLUTION[0] // 2 - msg.get_width() // 2,
                      DASHBOARD_RESOLUTION[1] // 2 - msg.get_height() // 2))
    pygame.display.flip()
    warmup_jit()

    settings = load_settings()
    master_clock = pygame.time.Clock()

    while True:
        # dashboard
        picked = run_dashboard(master_clock, settings)
        if picked is None:
            break
        settings.update(picked)
        save_settings(settings)

        # navigator
        result = run_navigator(master_clock, settings)
        if result == "quit":
            break
        # "dashboard" loops back automatically

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()