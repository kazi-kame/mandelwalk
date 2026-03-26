import numpy as np
from config import CAMERA_DEFAULTS

#===========
# Helpers
#===========
def _normalize(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-10 else v

def _look_at(eye, target, up):
    f = _normalize(target - eye)
    r = _normalize(np.cross(f, up))
    u = np.cross(r, f)
    m = np.eye(4, dtype=np.float32)
    m[0, :3] =  r
    m[1, :3] =  u
    m[2, :3] = -f
    m[0, 3]  = -np.dot(r, eye)
    m[1, 3]  = -np.dot(u, eye)
    m[2, 3]  =  np.dot(f, eye)
    return m

def _perspective(fov_deg, aspect, near, far):
    f   = 1.0 / np.tan(np.radians(fov_deg) / 2.0)
    m   = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] =  f / aspect
    m[1, 1] =  f
    m[2, 2] =  (far + near) / (near - far)
    m[2, 3] =  (2 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


class Camera:
    def __init__(self, position, fov=None, aspect=16/9):
        cfg  = CAMERA_DEFAULTS
        self.pos         = np.array(position, dtype=np.float32)
        self.yaw         = -90.0
        self.pitch       = -15.0
        self.fov         = fov or cfg["fov"]
        self.speed       = cfg["speed"]
        self.sensitivity = cfg["sensitivity"]
        self.sprint_mult = cfg["sprint_mult"]
        self.near        = cfg["near"]
        self.far         = cfg["far"]
        self.aspect      = aspect

        #===========
        # Orbital mode state
        #===========
        self.orbital      = False
        self.orbit_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.orbit_radius = 1.5
        self.orbit_yaw    = 0.0
        self.orbit_pitch  = 30.0

        self._update_vectors()

    def _update_vectors(self):
        yaw_r   = np.radians(self.yaw)
        pitch_r = np.radians(self.pitch)
        self.front = _normalize(np.array([
            np.cos(pitch_r) * np.cos(yaw_r),
            np.sin(pitch_r),
            np.cos(pitch_r) * np.sin(yaw_r),
        ], dtype=np.float32))
        self.right = _normalize(np.cross(self.front, np.array([0,1,0], dtype=np.float32)))
        self.up    = np.cross(self.right, self.front)

    #===========
    # FPS movement — call each frame with dt and key/mouse state
    #===========
    def update_fps(self, dt, keys, mouse_dx, mouse_dy, sprinting=False):
        spd = self.speed * (self.sprint_mult if sprinting else 1.0) * dt

        flat_front = _normalize(np.array([self.front[0], 0, self.front[2]], dtype=np.float32))
        if keys["forward"]:  self.pos += flat_front * spd
        if keys["backward"]: self.pos -= flat_front * spd
        if keys["left"]:     self.pos -= self.right * spd
        if keys["right"]:    self.pos += self.right * spd
        if keys["up"]:       self.pos[1] += spd
        if keys["down"]:     self.pos[1] -= spd

        self.yaw   += mouse_dx * self.sensitivity
        self.pitch  = np.clip(self.pitch - mouse_dy * self.sensitivity, -89.0, 89.0)
        self._update_vectors()

    #===========
    # Orbital movement — mouse drag rotates around orbit_target
    #===========
    def update_orbital(self, mouse_dx, mouse_dy, scroll=0):
        self.orbit_yaw   += mouse_dx * self.sensitivity
        self.orbit_pitch  = np.clip(self.orbit_pitch - mouse_dy * self.sensitivity, 5.0, 85.0)
        self.orbit_radius = np.clip(self.orbit_radius - scroll * 0.2, 0.1, 20.0)

        yr = np.radians(self.orbit_yaw)
        pr = np.radians(self.orbit_pitch)
        self.pos = self.orbit_target + self.orbit_radius * np.array([
            np.cos(pr) * np.cos(yr),
            np.sin(pr),
            np.cos(pr) * np.sin(yr),
        ], dtype=np.float32)
        self.front = _normalize(self.orbit_target - self.pos)
        self.right = _normalize(np.cross(self.front, np.array([0,1,0], dtype=np.float32)))
        self.up    = np.cross(self.right, self.front)

    #===========
    # Smoothly interpolate position/yaw/pitch for cinematic intro
    #===========
    def set_lerp(self, start_pos, end_pos, start_pitch, end_pitch, t):
        t_smooth = t * t * (3 - 2 * t)   # smoothstep
        self.pos   = start_pos + (end_pos - start_pos) * t_smooth
        self.pitch = start_pitch + (end_pitch - start_pitch) * t_smooth
        self._update_vectors()

    def view_matrix(self):
        return _look_at(self.pos, self.pos + self.front, np.array([0,1,0], dtype=np.float32))

    def proj_matrix(self):
        return _perspective(self.fov, self.aspect, self.near, self.far)
