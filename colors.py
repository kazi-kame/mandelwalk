import numpy as np

#===========
# LUT-based colormaps (256 x 3 uint8)
#===========

def _lerp_palette(stops, size=256):
    """
    stops: list of (position_0_to_1, (r,g,b))
    returns uint8 LUT shape (size, 3)
    """
    lut = np.zeros((size, 3), dtype=np.float32)
    xs = np.linspace(0.0, 1.0, size, dtype=np.float32)

    stops = sorted(stops, key=lambda x: x[0])
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if p1 <= p0:
            continue
        mask = (xs >= p0) & (xs <= p1)
        t = (xs[mask] - p0) / (p1 - p0)
        c0 = np.array(c0, dtype=np.float32)
        c1 = np.array(c1, dtype=np.float32)
        lut[mask] = c0 + (c1 - c0) * t[:, None]

    lut[xs < stops[0][0]] = np.array(stops[0][1], dtype=np.float32)
    lut[xs > stops[-1][0]] = np.array(stops[-1][1], dtype=np.float32)
    return np.clip(lut, 0, 255).astype(np.uint8)


def _hsv_to_rgb_lut():
    h = np.linspace(0.0, 1.0, 256, endpoint=False, dtype=np.float32)
    s = np.ones_like(h, dtype=np.float32)
    v = np.ones_like(h, dtype=np.float32)

    h6 = h * 6.0
    i = np.floor(h6).astype(np.int32) % 6
    f = h6 - np.floor(h6)
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)

    rgb = np.zeros((256, 3), dtype=np.float32)
    for idx, (r_val, g_val, b_val) in enumerate([
        (v, t, p), (q, v, p), (p, v, t),
        (p, q, v), (t, p, v), (v, p, q),
    ]):
        mask = (i == idx)
        rgb[mask, 0] = r_val[mask]
        rgb[mask, 1] = g_val[mask]
        rgb[mask, 2] = b_val[mask]

    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)


INFERNO_LUT = _lerp_palette([
    (0.00, (0, 0, 0)),
    (0.25, (30, 10, 60)),
    (0.55, (120, 30, 80)),
    (0.80, (220, 90, 20)),
    (1.00, (255, 240, 100)),
])

ELECTRIC_LUT = _lerp_palette([
    (0.00, (0, 0, 20)),
    (0.35, (0, 40, 180)),
    (0.70, (0, 220, 255)),
    (1.00, (255, 255, 255)),
])

LAVA_LUT = _lerp_palette([
    (0.00, (0, 0, 0)),
    (0.35, (90, 0, 0)),
    (0.65, (220, 30, 0)),
    (0.90, (255, 140, 0)),
    (1.00, (255, 255, 255)),
])

ICE_LUT = _lerp_palette([
    (0.00, (0, 10, 30)),
    (0.40, (0, 80, 140)),
    (0.75, (80, 210, 220)),
    (1.00, (245, 255, 255)),
])

GOLD_LUT = _lerp_palette([
    (0.00, (0, 0, 0)),
    (0.45, (70, 0, 0)),
    (0.75, (170, 90, 0)),
    (1.00, (255, 215, 0)),
])

PSYCHEDELIC_LUT = _hsv_to_rgb_lut()

COLORMAPS = {
    "inferno": INFERNO_LUT,
    "electric": ELECTRIC_LUT,
    "lava": LAVA_LUT,
    "ice": ICE_LUT,
    "gold": GOLD_LUT,
    "psychedelic": PSYCHEDELIC_LUT,
}

#===========
# Map smooth iteration counts to RGB via LUT colourmap
#===========
def iterations_to_rgb(smooth_iter, max_iter, colormap="inferno"):
    norm = np.clip(smooth_iter / max_iter, 0.0, 1.0).astype(np.float32)
    in_set = (smooth_iter >= max_iter)

    # light contrast shaping for better visual separation
    shaped = np.power(norm, 0.85)
    idx = np.clip((shaped * 255.0).astype(np.int32), 0, 255)

    lut = COLORMAPS.get(colormap, INFERNO_LUT)
    rgb = lut[idx]  # (H, W, 3), uint8

    # interior of set -> black
    rgb = rgb.copy()
    rgb[in_set] = 0
    return rgb

#===========
# No-op kept for compatibility with existing pipeline call sites
#===========
def apply_color_cycle(rgb_image, frame_number):
    return rgb_image