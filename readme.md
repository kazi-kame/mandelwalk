# MandelWalk

check the other brach for the latest release
---

<table>
  <tr>
    <td><img src="assets/mandelwalk.gif" width="400"></td>
    <td><img src="assets/mandelwalk_2.gif" width="450"></td>
  </tr>
  <tr>
    <td align="center">zooming in</td>
    <td align="center">zooming out</td>
  </tr>
</table>

---

## What this is

This project renders the Mandelbrot set and lets you zoom into it until your laptop starts questioning your life choices.

It has:

* a full-screen navigator for zooming and moving around
* Numba acceleration so it runs fast enough 
* multiple colormaps

---

## The math

The Mandelbrot set is defined by the recurrence:

$$
z_{n+1} = z_n^2 + c, \quad z_0 = 0
$$

For each complex number $c$, we check whether this sequence stays bounded.

* If it does → point is in the set (colored black)
* If it escapes → we color it based on how fast it escapes

Instead of raw iteration count, this uses **smooth coloring**:

$$
\text{smooth} \approx n + 1 - \log_2(\log |z_n|)
$$

Translation: fewer ugly bands, more nice gradients.

---

## Features

* real-time Mandelbrot rendering
* zoom targets like:

  * Seahorse Valley
  * elephant valley
  * some other places I found cool
* keyboard + mouse navigation
* adaptive iteration scaling (zoom more → compute more → suffer more)
* resolution drops while moving, so it doesn’t lag like crazy
* LUT-based colormaps:

  * inferno
  * electric
  * lava
  * ice
  * gold
  * psychedelic (yes)

---

## Controls

### Dashboard

* Set zoom speed, FPS, duration, colormap, target
* Click **Start Navigator**

### Navigator

* **WASD / Arrows** → move
* **Q / E** → zoom in / out
* **Mouse wheel** → zoom
* **Left click + drag** → pan
* **Right click** → recenter
* **R** → reset
* **C** → change colormap
* **ESC** → go back

---

## How it works (simplified)

1. UI collects settings
2. Current viewport in complex plane is computed
3. Mandelbrot kernel runs (Numba JIT)
4. Smooth iteration values are mapped to colors
5. Frame is rendered with pygame
6. If you move → resolution drops → FPS survives

---

## Project structure

* `main.py` → everything comes together here
* `mandelbrot.py` → heavy computation (Numba stuff)
* `colors.py` → color mapping and LUTs
* `ui.py` → dashboard UI
* `mapping.py` → coordinate conversions
* `config.py` → constants and presets

---

## Flaws

* This is a visualizer, not deep math or research
* Some functions (like coordinate mapping) exist in multiple places
* UI looks decent, but still clearly student-level
* Performance drops at very deep zoom
* No built-in benchmarking or analysis
* Dependencies are not pinned → might randomly break in future
* I probably overdid the colormaps
* The dashboard still reads fps and stuff that doesn't exactly make sense coz it was supposed to be something else but I came up with a better idea but got lazy and didn't change the UI. So like the dashboard is almost entirely useless

---

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python main.py
```

---

## Notes

* Adaptive iterations prevent instant death at deep zooms
* Lower render resolution while moving is a hack, but it works
* JIT warmup exists so the first frame doesn’t take forever

---

## Why this exists

Because:

* Fractals look cool
* Complex numbers deserve screen time
* and apparently, I make graphics engines when I should be revising

If nothing else, this was a productive way to procrastinate.
