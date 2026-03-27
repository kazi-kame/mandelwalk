# MandelWalk v2

### You are no longer looking at the set. You are in it!!

<tr>
  <td><img src="assets/MandelWalk.gif" width="800"></td>
</tr>

---

## What this is

v1 (branched) let you zoom into the Mandelbrot set.

v2 lets you walk around inside it.

The set is rendered as a 3D volumetric slab using a GLSL ray marcher running on your GPU. The boundary becomes a cliff. The spirals become canyons. The interior is a void you can fall into.

It has:
- a ray-marched 3D renderer (ModernGL + GLSL)
- a proper distance estimator so the geometry is mathematically exact
- a void fall mechanic with water, a glow ring, and a respawn
- a minimap rendered as a GL texture overlay with a direction arrow
- FPS and orbital camera modes
- world scale zoom so you can pull back or push in without moving
- safe spawn search so you don't start inside a wall
- ground following so walking feels physical
- the same colormaps as before because they looked good

---

## The math

Still the same recurrence:

$$
z_{n+1} = z_n^2 + c, \quad z_0 = 0
$$

But now instead of coloring pixels from above, we're ray marching through 3D space.

The key is the **distance estimator** (Quilez, derived from Hubbard-Douady potential theory):

$$
DE(c) = \frac{1}{2} \cdot \frac{|z_n|}{\left|\frac{dz_n}{dc}\right|} \cdot \log|z_n|
$$

This gives the exact distance from any point in the complex plane to the nearest point on the Mandelbrot boundary. We use it two ways:

- **Geometry**: the DE defines a volumetric slab. Exterior is open terrain, shaped by `DE^exp * scale`. Boundary is cliff faces cutting through the slab vertically. Interior is the void drop.
- **Ray marching**: at each step along the ray, DE tells us the safe step size — we can't overshoot the surface within that radius.

The slab surface sits at:

$$
y_{\text{top}} = \text{DE}^{\gamma} \cdot s, \quad y_{\text{bot}} = y_{\text{top}} - t
$$

where $\gamma$ is the height exponent (default 0.6, controls cliff steepness), $s$ is the height scale, and $t$ is the slab thickness. The ray marcher solves `max(p.y - y_top, y_bot - p.y) = 0`.

Coloring still uses smooth iteration:

$$
\text{smooth} \approx n + 1 - \log_2(\log_2 |z_n|)
$$

Normals are estimated via central differences on the scene DE. AO is a 5-sample cone march. Surface grain is a hash-based per-point noise multiply.

---

## Features

- **5 regions** to spawn into:
  - Seahorse Valley
  - Elephant Valley
  - Feigenbaum Corridor *(infinite period-doubling spike, never voids out)*
  - Triple Spiral
  - Cardioid Cliff
- **void mechanic** — fall off the slab into darkness, a water plane with waves and fresnel below, a pulsing glow ring at the entry point above, respawn at last safe position
- **respawn grace period** — brief immunity after spawning so you don't immediately fall again
- **minimap** — rendered as a GL texture directly in the fragment shader, bottom-left corner, player dot + direction arrow, updates every frame
- **world scale zoom** — `[` and `]` zoom the fractal in/out without moving the camera, all positions rescale correctly
- **safe spawn search** — scans outward in rings from the target coordinate to find a flat, exterior spawn point
- **ground following** — camera eye height smoothly tracks terrain so walking feels continuous
- **FPS + orbital camera** — Tab to toggle
- **cinematic intro** per region
- **LUT colormaps**: inferno, electric, lava, ice, gold
- **AO + surface grain** on cliff faces
- **fullscreen toggle**

---

## Controls

### Dashboard
- Region, colormap, movement speed, FOV, cliff height, void depth
- Advanced: eye height, slab thickness, world scale, ground follow speed
- Click **Enter the Set**

### In-world
| Key | Action |
|-----|--------|
| `WASD` | Move |
| `Mouse` | Look |
| `Shift` | Sprint |
| `Space / Ctrl` | Up / Down |
| `[ / ]` | Zoom fractal out / in |
| `Tab` | Toggle FPS / Orbital |
| `F` | Fullscreen |
| `Space` *(intro)* | Skip cinematic |
| `Esc` | Back to dashboard |

Orbital mode: click-drag to rotate around a focal point, scroll to zoom.

---

## How it works (simplified)

1. Dashboard collects settings
2. Safe spawn search scans the terrain for a valid exterior starting point
3. Cinematic intro flies you in from above using smoothstep interpolation
4. Every frame: for each pixel, cast a ray from the camera
5. March using `scene_de()` — a slab DE built from the Mandelbrot DE
6. On hit: compute normal via central differences, AO via cone march, shade with two lights + specular
7. Color from smooth iteration → colormap LUT + grain noise
8. Minimap texture is sampled directly in the fragment shader as a UV overlay
9. If DE ≤ interior threshold or you fall below terrain → void state
10. Void: water plane with wave normals + fresnel, glow ring at entry point
11. After `fall_depth` units → fade to white → respawn at last safe position

---

## Project structure

- `main.py` → app loop, state machine, terrain queries, minimap texture, world scale
- `frag.glsl` → ray marcher, slab DE, lighting, colormaps, void effects, minimap sampling
- `vert.glsl` → passthrough vertex shader
- `camera.py` → FPS + orbital camera, view matrix
- `dashboard.py` → standalone pygame dashboard window
- `ui.py` → dashboard UI elements and sliders
- `config.py` → regions, constants, keybindings, advanced defaults

---

## EXE is available for those who wanna try it on their devices without cloning the whole thing

Right hand side under `Releases`
```
click on '+1 releases' 
Locate `MandelWalk_2` 
click on the exe file under that release 
open the downloaded file and launch it 
a warning will appear click on 'More info' 
'Run Anyway'
```

---

## Setup

```bash
pip install -r requirements.txt
python main.py
```

---

## Flaws

- Still student-level, just student-level with shaders now
- Integrated GPU means 720p or it starts to struggle at 512 DE iterations
- Walking *into* spirals works but finding the right canyon entry takes exploration — there's no compass pointing at interesting geometry
- Void detection has a grace period hack to prevent instant re-trigger on respawn
- The safe spawn search is a heuristic ring scan, not guaranteed to find the optimal point
- World scale zoom rescales all positions but orbital pivot can drift slightly
- The minimap uses a fixed color scheme regardless of selected colormap
- Ground following speed interacts weirdly with fast movement near cliff edges — you can briefly clip through thin overhangs
- No save/load of positions, so finding something interesting means finding it again next time
- Dependencies are not pinned

---

## Why this exists

Because v1 answered "what does it look like from above" and I wanted to know what it looks like from inside.

Also:
- The distance estimator is genuinely beautiful math
- Complex numbers still deserve screen time
- and apparently I write ray marchers when I should be studying for exams

If nothing else, this was a productive way to procrastinate. Again.
