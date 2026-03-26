#version 330 core

in  vec2 uv;
out vec4 fragColor;

// Camera
uniform vec3  u_cam_pos;
uniform vec3  u_cam_front;
uniform vec3  u_cam_right;
uniform vec3  u_cam_up;
uniform float u_fov;
uniform float u_aspect;

// World
uniform float u_height_scale;
uniform float u_height_exp;
uniform int   u_colormap;
uniform float u_time;
uniform float u_slab_thickness;
uniform float u_world_scale;

// Void
uniform int   u_in_void;
uniform float u_fall_depth;
uniform float u_fade;
uniform vec3  u_void_entry;
uniform float u_water_y;
uniform sampler2D u_minimap;
uniform vec4  u_minimap_rect;

#define MAX_STEPS   180
#define MIN_DIST    0.00035
#define MAX_DIST    200.0
#define SURF_EPS    0.0007
#define DE_ITER     512

float mandelbrot_de(vec2 c) {
    vec2  z  = vec2(0.0);
    vec2  dz = vec2(0.0);
    float m2 = 0.0;
    for (int i = 0; i < DE_ITER; i++) {
        dz = 2.0 * vec2(z.x * dz.x - z.y * dz.y, z.x * dz.y + z.y * dz.x) + vec2(1.0, 0.0);
        z  = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
        m2 = dot(z, z);
        if (m2 > 256.0) break;
    }
    return 0.5 * sqrt(m2 / max(dot(dz, dz), 1e-12)) * log(max(m2, 1.00001));
}

vec4 sample_minimap(vec2 uv) {
    vec2 mn = u_minimap_rect.xy;
    vec2 mx = u_minimap_rect.zw;
    if (uv.x < mn.x || uv.x > mx.x || uv.y < mn.y || uv.y > mx.y) return vec4(0.0);
    vec2 muv = (uv - mn) / (mx - mn);
    return texture(u_minimap, muv);
}

float mandelbrot_smooth(vec2 c) {
    vec2  z  = vec2(0.0);
    float m2 = 0.0;
    for (int i = 0; i < DE_ITER; i++) {
        z  = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
        m2 = dot(z, z);
        if (m2 > 256.0) {
            return float(i) + 1.0 - log2(log2(m2) * 0.5);
        }
    }
    return -1.0;
}

vec2 world_to_fractal(vec2 xz) {
    return xz / u_world_scale;
}

// Inverted exterior height + finite slab
float scene_de(vec3 p) {
    vec2 c  = world_to_fractal(p.xz);
    float de = mandelbrot_de(c);
    float top = pow(max(de, 0.0), u_height_exp) * u_height_scale;
    float bot = top - u_slab_thickness;

    float d_top  = p.y - top;
    float d_bot  = bot - p.y;
    float d_slab = max(d_top, d_bot);
    return d_slab;
}

vec3 calc_normal(vec3 p) {
    vec2 e = vec2(0.0012, 0.0);
    return normalize(vec3(
        scene_de(p + e.xyy) - scene_de(p - e.xyy),
        scene_de(p + e.yxy) - scene_de(p - e.yxy),
        scene_de(p + e.yyx) - scene_de(p - e.yyx)
    ));
}

vec3 colormap_inferno(float t) {
    t = clamp(t, 0.0, 1.0);
    vec3 c0 = vec3(0.000, 0.000, 0.016);
    vec3 c1 = vec3(0.258, 0.008, 0.341);
    vec3 c2 = vec3(0.576, 0.047, 0.396);
    vec3 c3 = vec3(0.867, 0.318, 0.227);
    vec3 c4 = vec3(0.988, 0.702, 0.031);
    vec3 c5 = vec3(0.988, 1.000, 0.643);
    float s = t * 5.0; int i = int(s); float f = fract(s);
    if (i == 0) return mix(c0, c1, f);
    if (i == 1) return mix(c1, c2, f);
    if (i == 2) return mix(c2, c3, f);
    if (i == 3) return mix(c3, c4, f);
    return mix(c4, c5, f);
}
vec3 colormap_electric(float t) {
    t = clamp(t, 0.0, 1.0);
    vec3 c0 = vec3(0.000, 0.000, 0.100);
    vec3 c1 = vec3(0.000, 0.200, 0.700);
    vec3 c2 = vec3(0.000, 0.700, 0.900);
    vec3 c3 = vec3(0.200, 0.950, 1.000);
    vec3 c4 = vec3(1.000);
    float s = t * 4.0; int i = int(s); float f = fract(s);
    if (i == 0) return mix(c0, c1, f);
    if (i == 1) return mix(c1, c2, f);
    if (i == 2) return mix(c2, c3, f);
    return mix(c3, c4, f);
}
vec3 colormap_lava(float t) {
    t = clamp(t, 0.0, 1.0);
    vec3 c0 = vec3(0.000);
    vec3 c1 = vec3(0.400, 0.000, 0.000);
    vec3 c2 = vec3(0.800, 0.100, 0.000);
    vec3 c3 = vec3(1.000, 0.500, 0.050);
    vec3 c4 = vec3(1.000, 0.900, 0.400);
    vec3 c5 = vec3(1.000);
    float s = t * 5.0; int i = int(s); float f = fract(s);
    if (i == 0) return mix(c0, c1, f);
    if (i == 1) return mix(c1, c2, f);
    if (i == 2) return mix(c2, c3, f);
    if (i == 3) return mix(c3, c4, f);
    return mix(c4, c5, f);
}
vec3 colormap_ice(float t) {
    t = clamp(t, 0.0, 1.0);
    vec3 c0 = vec3(0.000, 0.000, 0.050);
    vec3 c1 = vec3(0.000, 0.100, 0.400);
    vec3 c2 = vec3(0.000, 0.450, 0.650);
    vec3 c3 = vec3(0.300, 0.800, 0.900);
    vec3 c4 = vec3(0.850, 0.970, 1.000);
    float s = t * 4.0; int i = int(s); float f = fract(s);
    if (i == 0) return mix(c0, c1, f);
    if (i == 1) return mix(c1, c2, f);
    if (i == 2) return mix(c2, c3, f);
    return mix(c3, c4, f);
}
vec3 colormap_gold(float t) {
    t = clamp(t, 0.0, 1.0);
    vec3 c0 = vec3(0.000);
    vec3 c1 = vec3(0.200, 0.050, 0.000);
    vec3 c2 = vec3(0.600, 0.200, 0.000);
    vec3 c3 = vec3(0.900, 0.650, 0.050);
    vec3 c4 = vec3(1.000, 0.950, 0.600);
    float s = t * 4.0; int i = int(s); float f = fract(s);
    if (i == 0) return mix(c0, c1, f);
    if (i == 1) return mix(c1, c2, f);
    if (i == 2) return mix(c2, c3, f);
    return mix(c3, c4, f);
}
vec3 apply_colormap(float t) {
    if (u_colormap == 0) return colormap_inferno(t);
    if (u_colormap == 1) return colormap_electric(t);
    if (u_colormap == 2) return colormap_lava(t);
    if (u_colormap == 3) return colormap_ice(t);
    return colormap_gold(t);
}

float hash31(vec3 p) {
    p = fract(p * 0.1031);
    p += dot(p, p.yzx + 33.33);
    return fract((p.x + p.y) * p.z);
}

float calc_ao(vec3 p, vec3 n) {
    float ao = 0.0;
    float w  = 1.0;
    for (int i = 1; i <= 5; i++) {
        float h = 0.03 * float(i);
        float d = scene_de(p + n * h);
        ao += (h - d) * w;
        w *= 0.72;
    }
    return clamp(1.0 - ao * 1.65, 0.20, 1.0);
}

vec3 surface_color(vec3 p) {
    vec2 c = world_to_fractal(p.xz);
    float s = mandelbrot_smooth(c);
    if (s < 0.0) return vec3(0.02);

    float t = clamp(s / 48.0, 0.0, 1.0);
    t = fract(t + u_time * 0.02);
    vec3 base = apply_colormap(t);

    float r = hash31(vec3(p.x * 13.0, p.y * 9.0, p.z * 13.0));
    float grain = mix(0.88, 1.08, r);
    return base * grain;
}

vec3 sky_color(vec3 rd) {
    float sky_t = clamp(rd.y * 0.5 + 0.5, 0.0, 1.0);
    return mix(vec3(0.01, 0.01, 0.02), vec3(0.04, 0.04, 0.08), sky_t);
}

vec3 march(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = scene_de(p);

        if (d < SURF_EPS) {
            vec3 n = calc_normal(p);
            vec3 base = surface_color(p);

            vec3 L1 = normalize(vec3(0.8, 1.0, 0.5));
            vec3 L2 = normalize(vec3(-0.6, 0.4, -0.8));
            float diff1 = max(dot(n, L1), 0.0);
            float diff2 = max(dot(n, L2), 0.0) * 0.33;
            float amb   = 0.10;

            vec3 refl = reflect(-L1, n);
            float spec = pow(max(dot(refl, -rd), 0.0), 24.0) * 0.16;

            float ao = calc_ao(p, n);
            vec3 col = base * (amb + (diff1 + diff2) * ao) + vec3(spec);

            float fog = exp(-t * 0.03);
            col = mix(vec3(0.01, 0.01, 0.02), col, fog);
            return col;
        }

        if (t > MAX_DIST) break;
        t += max(abs(d) * 0.45, MIN_DIST);
    }
    return sky_color(rd);
}

vec3 void_water(vec3 ro, vec3 rd) {
    if (abs(rd.y) < 1e-5) return vec3(0.0);
    float t = (u_water_y - ro.y) / rd.y;
    if (t <= 0.0) return vec3(0.0);

    vec3 hit = ro + rd * t;
    vec3 n = vec3(0.0, 1.0, 0.0);

    float wave = sin(hit.x * 1.8 + u_time * 1.3) * 0.02 + sin(hit.z * 2.6 - u_time * 1.0) * 0.02;
    n = normalize(vec3(-wave, 1.0, wave));

    vec3 refl = sky_color(reflect(rd, n));
    vec3 deep = vec3(0.01, 0.02, 0.03);

    float fres = pow(1.0 - max(dot(-rd, n), 0.0), 4.0);
    vec3 water = mix(deep, refl, 0.44 + 0.42 * fres);

    float dist_fade = exp(-t * 0.025);
    return water * dist_fade;
}

vec3 void_glow(vec3 ray_origin, vec3 ray_dir) {
    float ry = ray_dir.y;
    if (abs(ry) < 1e-5) return vec3(0.0);

    float t = (0.0 - ray_origin.y) / ry;
    if (t < 0.0) return vec3(0.0);

    vec3 hit = ray_origin + t * ray_dir;
    float dist = length(hit.xz - u_void_entry.xz);
    float r = 0.35;
    float ring = smoothstep(r + 0.06, r, dist) * smoothstep(r - 0.18, r, dist);
    float pulse = 0.6 + 0.4 * sin(u_time * 3.0);
    return apply_colormap(0.7) * ring * pulse * 0.6;
}

void main() {
    vec2  ndc  = uv * 2.0 - 1.0;
    float ftan = tan(radians(u_fov) * 0.5);
    vec3  rd   = normalize(
        u_cam_front +
        u_cam_right * ndc.x * ftan * u_aspect +
        u_cam_up    * ndc.y * ftan
    );

    vec3 col;
    if (u_in_void == 1) {
        vec3 w = void_water(u_cam_pos, rd);
        vec3 g = void_glow(u_cam_pos, rd);
        col = max(w, g);
    } else {
        col = march(u_cam_pos, rd);
    }
    vec4 mm = sample_minimap(uv);
    col = mix(col, mm.rgb, mm.a);

    col = mix(col, vec3(1.0), u_fade);
    fragColor = vec4(col, 1.0);
}