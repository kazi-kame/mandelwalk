import numpy as np
from numba import njit, prange
from config import RESOLUTION, MAX_ITERATIONS, INITIAL_TOP_LEFT, INITIAL_BOTTOM_RIGHT

#===========
# Numba-JIT parallel Mandelbrot kernel with smooth fractional escape colouring
#===========
@njit(parallel=True, fastmath=True, cache=True)
def _mandelbrot_kernel(xs, ys, max_iter):
    height = len(ys)
    width  = len(xs)
    out    = np.empty((height, width), dtype=np.float32)

    for row in prange(height):
        cy = ys[row]
        for col in range(width):
            cx = xs[col]
            zr, zi = 0.0, 0.0
            smooth  = float(max_iter)

            for i in range(max_iter):
                zr2 = zr * zr
                zi2 = zi * zi
                if zr2 + zi2 > 4.0:
                    modulus = (zr2 + zi2) ** 0.5
                    log_log = np.log(np.log(modulus + 1e-10)) / np.log(2.0)
                    smooth  = float(i) + 1.0 - log_log
                    break
                zi = 2.0 * zr * zi + cy
                zr = zr2 - zi2 + cx

            out[row, col] = smooth

    return out


def compute_mandelbrot(width, height, top_left, bottom_right, max_iter=MAX_ITERATIONS):
    xs = np.linspace(top_left[0], bottom_right[0], width, dtype=np.float64)
    ys = np.linspace(top_left[1], bottom_right[1], height, dtype=np.float64)
    return _mandelbrot_kernel(xs, ys, max_iter)


def adaptive_max_iter(top_left, bottom_right, base=MAX_ITERATIONS):
    pixel_width = (bottom_right[0] - top_left[0]) / RESOLUTION[0]
    if pixel_width <= 0:
        return base
    zoom_depth = max(1.0, 1.0 / pixel_width)
    return int(np.clip(int(base * np.log2(zoom_depth)), base, 2048))


def warmup_jit():
    xs = np.linspace(-2.0, 1.0, 64, dtype=np.float64)
    ys = np.linspace(-1.0, 1.0, 36, dtype=np.float64)
    _mandelbrot_kernel(xs, ys, 32)


def get_initial_frame():
    w, h = RESOLUTION
    return compute_mandelbrot(w, h, INITIAL_TOP_LEFT, INITIAL_BOTTOM_RIGHT)