"""Pure-Python math used by the rules and by the standards.

Everything here is deterministic and unit-tested without Blender.
Units: lengths in studs (1 Blender unit = 1 stud in ECLIPSE), angles in degrees.

Screen-space model
------------------
A vertical FOV ``fov`` rendered on ``screen_h`` pixels shows, at distance ``d``,
a world height of ``2 * d * tan(fov / 2)``. Hence the number of screen pixels
covered by one stud at that distance:

    ppu(d) = screen_h / (2 * d * tan(fov / 2))

Roblox Camera.FieldOfView is vertical and defaults to 70 degrees [OFFICIEL].
"""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

ROBLOX_DEFAULT_FOV = 70.0
STUD_IN_CM = 28.0  # Roblox units page [OFFICIEL]


def pixels_per_stud(distance: float, fov_deg: float = ROBLOX_DEFAULT_FOV, screen_h: int = 1080) -> float:
    if distance <= 0:
        raise ValueError("distance must be > 0")
    return screen_h / (2.0 * distance * math.tan(math.radians(fov_deg) / 2.0))


def projected_px(size_studs: float, distance: float, fov_deg: float = ROBLOX_DEFAULT_FOV,
                 screen_h: int = 1080) -> float:
    """Approximate on-screen size (pixels) of a feature facing the camera."""
    return size_studs * pixels_per_stud(distance, fov_deg, screen_h)


def min_visible_width(min_px: float, distance: float, fov_deg: float = ROBLOX_DEFAULT_FOV,
                      screen_h: int = 1080) -> float:
    """Smallest feature width (studs) that still covers ``min_px`` pixels."""
    return min_px / pixels_per_stud(distance, fov_deg, screen_h)


def cylinder_sides(radius: float, ppu: float, max_error_px: float = 0.5, minimum: int = 6,
                   multiple_of: int = 2) -> int:
    """Segment count so that the silhouette facet error (sagitta) stays under ``max_error_px``.

    Sagitta of a regular n-gon inscribed in radius r: s = r * (1 - cos(pi / n)).
    Solve s * ppu <= e  =>  n >= pi / acos(1 - e / (r * ppu)).
    """
    r_px = radius * ppu
    if r_px <= max_error_px:
        n = minimum
    else:
        n = math.ceil(math.pi / math.acos(1.0 - max_error_px / r_px))
    n = max(minimum, n)
    if multiple_of > 1 and n % multiple_of:
        n += multiple_of - n % multiple_of
    return n


def texel_density(uv_area: float, area_3d: float, resolution: int) -> float:
    """Texels per stud for a surface of ``area_3d`` stud^2 using ``uv_area`` (0-1 space)."""
    if area_3d <= 0 or uv_area <= 0:
        return 0.0
    return math.sqrt(uv_area * resolution * resolution / area_3d)


def next_pow2(value: float) -> int:
    v = max(1, int(math.ceil(value)))
    return 1 << (v - 1).bit_length()


def recommended_resolution(area_3d: float, target_td: float, packing: float = 0.7,
                           cap: int = 4096) -> int:
    """Smallest power-of-two square texture reaching ``target_td`` px/stud."""
    if area_3d <= 0 or target_td <= 0:
        return 0
    side = math.sqrt(area_3d * target_td * target_td / max(1e-6, packing))
    return min(cap, next_pow2(side))


def padding_px(resolution: int) -> int:
    """ECLIPSE padding rule: resolution / 64 (16 px @1K, 8 px @512, 32 px @2K), min 4.

    Survives ~4 mip levels, consistent with the professional guidance
    'about 12 px at 1K, half at 512' [PRO] while rounding to powers of two.
    """
    return max(4, resolution // 64)


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c: float) -> float:
    c = max(0.0, c)
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1.0 / 2.4)) - 0.055


def luminance_linear(rgb: Sequence[float]) -> float:
    """Rec.709 luminance of a linear RGB triplet."""
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def percentile(values: Sequence[float], p: float) -> float:
    """Linear-interpolated percentile (0-100) without numpy."""
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (p / 100.0)
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def weighted_percentile(pairs: Iterable[Tuple[float, float]], p: float) -> float:
    """Percentile of values weighted by weights; pairs = (value, weight)."""
    items = sorted((v, w) for v, w in pairs if w > 0)
    if not items:
        return 0.0
    total = sum(w for _, w in items)
    target = total * p / 100.0
    acc = 0.0
    for v, w in items:
        acc += w
        if acc >= target:
            return v
    return items[-1][0]


def segment_point_distance(a: Sequence[float], b: Sequence[float], p: Sequence[float]) -> Tuple[float, float]:
    """Distance from p to segment ab and the parameter t in [0,1] of the closest point."""
    ab = [b[i] - a[i] for i in range(3)]
    ap = [p[i] - a[i] for i in range(3)]
    denom = sum(x * x for x in ab)
    if denom <= 0:
        return math.sqrt(sum(x * x for x in ap)), 0.0
    t = max(0.0, min(1.0, sum(ab[i] * ap[i] for i in range(3)) / denom))
    closest = [a[i] + ab[i] * t for i in range(3)]
    return math.sqrt(sum((p[i] - closest[i]) ** 2 for i in range(3))), t


def triangle_min_angle(a, b, c) -> float:
    """Smallest interior angle (degrees) of triangle abc; 0 for degenerate."""
    def sub(u, v):
        return [u[i] - v[i] for i in range(3)]

    def ang(u, v):
        nu = math.sqrt(sum(x * x for x in u))
        nv = math.sqrt(sum(x * x for x in v))
        if nu == 0 or nv == 0:
            return 0.0
        d = max(-1.0, min(1.0, sum(u[i] * v[i] for i in range(3)) / (nu * nv)))
        return math.degrees(math.acos(d))

    return min(ang(sub(b, a), sub(c, a)), ang(sub(a, b), sub(c, b)), ang(sub(a, c), sub(b, c)))


def axis_vector(axis: str) -> Tuple[float, float, float]:
    axis = axis.strip().upper()
    sign = -1.0 if axis.startswith("-") else 1.0
    letter = axis.lstrip("+-")
    idx = {"X": 0, "Y": 1, "Z": 2}[letter]
    v = [0.0, 0.0, 0.0]
    v[idx] = sign
    return tuple(v)  # type: ignore[return-value]


def bevel_table(distances: Iterable[float], min_px: float = 2.0, fov_deg: float = ROBLOX_DEFAULT_FOV,
                screen_h: int = 1080) -> List[Tuple[float, float, float]]:
    """(distance, px_per_stud, min visible width) rows used in the bevel standard."""
    rows = []
    for d in distances:
        ppu = pixels_per_stud(d, fov_deg, screen_h)
        rows.append((d, ppu, min_px / ppu))
    return rows
