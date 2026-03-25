#===========
# Rendering resolution (used for fullscreen simulation)
#===========
RESOLUTION = (1920, 1080)

#===========
# Dashboard window resolution (always windowed)
#===========
DASHBOARD_RESOLUTION = (1280, 720)

#===========
# Base max iterations (floor for adaptive scaling)
#===========
MAX_ITERATIONS = 64

#===========
# Target frame rate
#===========
FRAME_RATE = 60

#===========
# Zoom speed bounds
#===========
ZOOM_SPEED_MIN = 1.01
ZOOM_SPEED_MAX = 1.15

#===========
# Duration control limits
#===========
MIN_DURATION_SECONDS = 10
MAX_FRAMES = 1200

#===========
# Default viewport in the complex plane
#===========
INITIAL_TOP_LEFT     = (-2.5, 1.0)
INITIAL_BOTTOM_RIGHT = (1.0, -1.0)

#===========
# Zoom targets — boundary-focused coordinates for persistent detail
#===========
ZOOM_TARGETS = {
    "seahorse_valley": {
        "top_left": (-0.75390, 0.11370),
        "bottom_right": (-0.74590, 0.10570),
        "zoom_point": (-0.74955, 0.10052),
    },
    "elephant_valley": {
        "top_left": (0.25480, 0.00060),
        "bottom_right": (0.26580, -0.01040),
        "zoom_point": (0.25895, -0.00145),
    },
    "double_spiral_valley": {
        "top_left": (-0.74890, 0.11110),
        "bottom_right": (-0.74290, 0.10510),
        "zoom_point": (-0.74530, 0.10800),
    },
    "feigenbaum_point": {
        "top_left": (-1.40700, 0.00350),
        "bottom_right": (-1.39550, -0.00350),
        "zoom_point": (-1.401155, 0.0),
    },
    "triple_spiral": {
        "top_left": (-0.15780, 1.04350),
        "bottom_right": (-0.14780, 1.03350),
        "zoom_point": (-0.15280, 1.03970),
    },
}

#===========
# Consecutive dropped frames before falling back to pre-render mode
#===========
REALTIME_DROP_THRESHOLD = 10

#===========
# Max frames to hold in RAM during pre-render (~6MB each at 1080p)
#===========
PRERENDER_MAX_FRAMES = 300

#===========
# Hue rotation speed in degrees per frame (kept for optional post effects)
#===========
COLOR_CYCLE_SPEED = 0.5

#===========
# Settings persistence file
#===========
SETTINGS_FILE = "settings.json"