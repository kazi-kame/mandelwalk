#===========
# Window
#===========
WIDTH, HEIGHT = 1280, 720
TITLE = "MandelWalk"
FPS   = 60

#===========
# Keybindings
#===========
KEYS = {
    "sprint":        "lshift",
    "up":            "space",
    "down":          "lctrl",
    "toggle_orbital":"tab",
    "fullscreen":    "f",
    "zoom_in":       "rightbracket",
    "zoom_out":      "leftbracket",
    "skip_intro":    "space",
    "back":          "escape",
}

#===========
# Camera defaults
#===========
CAMERA_DEFAULTS = {
    "fov":          75.0,
    "speed":        0.8,
    "sensitivity":  0.15,
    "sprint_mult":  4.0,
    "near":         0.001,
    "far":          250.0,
}

#===========
# Void / fall mechanic
#===========
VOID = {
    "threshold":        0.06,     # feet below terrain by this amount => void
    "interior_eps":     1e-6,     # DE <= eps treated as interior edge
    "gravity":          9.8,
    "fall_depth":       10.0,
    "fade_speed":       2.0,
    "water_y":         -8.0,
    "respawn_grace":    1.25,     # seconds of immunity after spawn/respawn
}

#===========
# Cinematic intro
#===========
INTRO = {
    "duration":      5.0,
    "start_height":  3.5,
    "end_height":    0.15,
}

#===========
# Regions
#===========
REGIONS = {
    "seahorse_valley": {
        "label":       "Seahorse Valley",
        "description": "Classic spiral canyon on the main cardioid boundary",
        "focal":       (-0.7499, 0.1010),
        "spawn":       (-0.7499, 0.18, 0.1010),
        "intro_from":  (-0.7499, 3.5,  0.1010),
    },
    "elephant_valley": {
        "label":       "Elephant Valley",
        "description": "Trunk arches along the positive real axis",
        "focal":       (0.2602, -0.0010),
        "spawn":       (0.2602, 0.18, -0.0010),
        "intro_from":  (0.2602, 3.5,  -0.0010),
    },
    "feigenbaum_point": {
        "label":       "Feigenbaum Corridor",
        "description": "Infinite period-doubling spike — never voids out",
        "focal":       (-1.4012, 0.0),
        "spawn":       (-1.4012, 0.18, 0.0),
        "intro_from":  (-1.4012, 3.5,  0.0),
    },
    "triple_spiral": {
        "label":       "Triple Spiral",
        "description": "Three-armed spiral node on the upper lobe",
        "focal":       (-0.1543, 1.0327),
        "spawn":       (-0.1543, 0.18, 1.0327),
        "intro_from":  (-0.1543, 3.5,  1.0327),
    },
    "main_cardioid_edge": {
        "label":       "Cardioid Cliff",
        "description": "The great smooth cliff face of the primary bulb",
        "focal":       (-0.52, 0.52),
        "spawn":       (-0.52, 0.18, 0.52),
        "intro_from":  (-0.52, 3.5,  0.52),
    },
}

#===========
# Colormaps available in the shader
#===========
COLORMAPS = ["inferno", "electric", "lava", "ice", "gold"]

#===========
# Height field
#===========
HEIGHT_SCALE_DEFAULT = 1.2
HEIGHT_SCALE_MIN     = 0.2
HEIGHT_SCALE_MAX     = 4.0
HEIGHT_EXP           = 0.60

#===========
# Fall depth slider range
#===========
FALL_DEPTH_MIN = 2.0
FALL_DEPTH_MAX = 24.0

#===========
# Minimap
#===========
MINIMAP = {
    "size":     128,
    "margin":   14,
    "x_range":  (-2.0, 1.0),   # Mandelbrot coordinates
    "z_range":  (-1.4, 1.4),
    "max_iter": 72,
}

#===========
# World scale slider range
#===========
WORLD_SCALE_MIN = 2.0
WORLD_SCALE_MAX = 24.0
WORLD_SCALE_ZOOM_FACTOR = 1.08

#===========
# Advanced defaults
#===========
ADVANCED_DEFAULTS = {
    "eye_height":      0.10,
    "slab_thickness":  0.55,

    # Scale factor: world -> mandelbrot
    # c = world_xz / world_scale
    "world_scale":     8.0,

    # Ground snapping (camera eye level stability)
    "ground_follow_speed": 14.0,

    # Safe spawn resolver
    "safe_spawn": {
        "min_de":      0.002,
        "search_r0":   0.02,
        "search_rmax": 0.55,
        "rings":       16,
        "samples":     40,
    },
}