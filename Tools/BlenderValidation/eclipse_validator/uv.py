"""UV rules: presence, 0-1 range, degenerate UVs, texel density, padding, overlap, stretch.

Covers the requested validate_uv script.
Standard: Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#uv
"""

from __future__ import annotations

import math
from typing import Dict, List

from mathutils import kdtree, Vector

from . import mathutil as mu
from .bpy_helpers import meshes, snapshot, uv_islands, uv_poly_area
from .core import FAIL, INFO, WARN, Context, info, make_result, rule

DOC = "Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md"


def _textured(ob) -> bool:
    return any(slot.material for slot in ob.material_slots)


@rule("UV001", "uv", "UV map present", DOC + "#uv")
def has_uv(ctx: Context):
    bad = [ob.name for ob in meshes(ctx) if _textured(ob) and not snapshot(ctx, ob).uv]
    return make_result(ctx, "UV001", bool(bad), FAIL, "Every textured mesh has a UV map.",
                       "Textured meshes without UVs.", bad)


@rule("UV002", "uv", "Single UV set", DOC + "#uv")
def single_uv(ctx: Context):
    bad = {ob.name: snapshot(ctx, ob).uv_names for ob in meshes(ctx) if len(snapshot(ctx, ob).uv_names) > 1}
    return make_result(ctx, "UV002", bool(bad), WARN, "One UV set per mesh.",
                       "Several UV maps: Roblox uses a single UV set [OFFICIEL]; only the active one matters. "
                       "Remove extras in the export copy.", list(bad), {"uv_maps": bad})


@rule("UV003", "uv", "UVs inside 0-1", DOC + "#uv")
def in_unit_square(ctx: Context):
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        if not s.uv:
            continue
        out = sum(1 for u, v in s.uv if u < -1e-4 or u > 1.0001 or v < -1e-4 or v > 1.0001)
        if out:
            bad.append(ob.name)
            details[ob.name] = {"loops_outside": out, "total_loops": len(s.uv)}
    return make_result(ctx, "UV003", bool(bad), WARN, "All UVs in 0-1.",
                       "UVs outside 0-1: Roblox expects 0:1 space [OFFICIEL]. Legitimate only in the SOURCE for "
                       "mirrored shells offset by exactly 1 tile during baking.", bad, details)


@rule("UV004", "uv", "Degenerate UV faces", DOC + "#uv")
def degenerate_uv(ctx: Context):
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        if not s.uv:
            continue
        n = sum(1 for pi, a in enumerate(s.face_areas) if a > 1e-8 and abs(uv_poly_area(s, pi)) < 1e-12)
        if n:
            bad.append(ob.name)
            details[ob.name] = {"zero_uv_area_faces": n}
    return make_result(ctx, "UV004", bool(bad), FAIL, "No collapsed UV faces.",
                       "Faces with zero UV area: texture smears and tangent space breaks (normal-map artifacts).",
                       bad, details)


def _density_rows(ctx: Context, res: int):
    rows = {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        if not s.uv:
            continue
        pairs = []
        tot_uv = tot_3d = 0.0
        for pi, a in enumerate(s.face_areas):
            if a <= 1e-9:
                continue
            ua = abs(uv_poly_area(s, pi))
            tot_uv += ua
            tot_3d += a
            pairs.append((mu.texel_density(ua, a, res), a))
        if not pairs:
            continue
        rows[ob.name] = {
            "td_overall": round(mu.texel_density(tot_uv, tot_3d, res), 1),
            "td_p10": round(mu.weighted_percentile(pairs, 10), 1),
            "td_p50": round(mu.weighted_percentile(pairs, 50), 1),
            "td_p90": round(mu.weighted_percentile(pairs, 90), 1),
            "surface_area": round(tot_3d, 5),
            "uv_area": round(tot_uv, 5),
        }
    return rows


@rule("UV005", "uv", "Texel density (level and uniformity)", DOC + "#texel-density")
def texel_density(ctx: Context):
    res = int(ctx.options.get("texture_resolution") or ctx.threshold("texture_resolution", 1024))
    target = ctx.threshold("min_texel_density", 256)
    spread_max = ctx.threshold("texel_density_max_spread", 2.0)
    packing = ctx.threshold("packing_efficiency_assumed", 0.7)
    rows = _density_rows(ctx, res)
    if not rows:
        return info("UV005", "No UV data to measure.")
    low, spread = [], []
    total_area = sum(r["surface_area"] for r in rows.values())
    for name, r in rows.items():
        if r["td_p50"] < target:
            low.append(name)
        if r["td_p10"] > 0 and r["td_p90"] / r["td_p10"] > spread_max:
            spread.append(name)
    details = {"texture_resolution_assumed": res, "target_px_per_stud": target,
               "recommended_resolution_for_target": mu.recommended_resolution(total_area, target, packing),
               "per_object": rows,
               "note": "px/stud; 1 stud = 28 cm → 10.24 px/cm (AAA first-person reference) ≈ 287 px/stud"}
    return make_result(ctx, "UV005", bool(low or spread), WARN,
                       f"Texel density ≥ {target} px/stud and uniform (p90/p10 ≤ {spread_max}).",
                       "Texel density too low and/or non-uniform. Roblox texture streaming picks one resolution per "
                       "texture and recommends near-uniform density [OFFICIEL].", low + spread, details)


@rule("UV006", "uv", "UV island padding", DOC + "#padding")
def padding(ctx: Context):
    res = int(ctx.options.get("texture_resolution") or ctx.threshold("texture_resolution", 1024))
    # profile value, but never below the resolution rule (res/64): 2K needs 32 px, not 16
    min_pad = max(ctx.threshold("uv_padding_px", 0), mu.padding_px(res))
    bad, details = [], {}
    # islands of all objects sharing a material share the texture: check per material
    per_mat: Dict[str, List] = {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        if not s.uv:
            continue
        for isl in uv_islands(s):
            mat = s.poly_mat[isl[0]]
            mname = s.material_names[mat] if mat < len(s.material_names) else ""
            pts = [s.uv[li] for pi in isl for li in s.poly_loops[pi]]
            # add edge midpoints for a denser boundary sampling
            for pi in isl:
                loops = s.poly_loops[pi]
                for k in range(len(loops)):
                    a, b = s.uv[loops[k]], s.uv[loops[(k + 1) % len(loops)]]
                    pts.append(((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5))
            per_mat.setdefault(mname or ob.name, []).append((ob.name, pts))
    for mname, islands in per_mat.items():
        if len(islands) < 2:
            continue
        total = sum(len(p) for _, p in islands)
        tree = kdtree.KDTree(total)
        owner = []
        idx = 0
        for isl_id, (_obn, pts) in enumerate(islands):
            for u, v in pts:
                tree.insert(Vector((u, v, 0.0)), idx)
                owner.append(isl_id)
                idx += 1
        tree.balance()
        radius = min_pad / float(res)
        worst = None
        offenders = set()
        idx = 0
        for isl_id, (obn, pts) in enumerate(islands):
            for u, v in pts:
                for (_co, j, d) in tree.find_range(Vector((u, v, 0.0)), radius):
                    if owner[j] != isl_id:
                        dpx = d * res
                        worst = dpx if worst is None else min(worst, dpx)
                        offenders.add(obn)
                        offenders.add(islands[owner[j]][0])
                idx += 1
        if worst is not None:
            bad.extend(sorted(offenders))
            details[mname] = {"closest_islands_px": round(worst, 2), "required_px": min_pad,
                              "resolution": res, "islands": len(islands)}
    return make_result(ctx, "UV006", bool(bad), WARN, f"Island spacing ≥ {min_pad}px at {res}px.",
                       "UV islands closer than the padding rule (vertex/edge-midpoint sampling; overlapping or "
                       "touching islands also land here). Low padding + mipmaps = fine lines along UV seams "
                       "(classic Worldmodel artifact).", bad, details)


def _raster_islands(s, islands, res):
    """Rasterise islands on a res×res grid, return (coverage_cells, overlap_cells)."""
    grid: Dict[int, int] = {}
    overlap = set()
    for isl_id, isl in enumerate(islands):
        cells = set()
        for pi in isl:
            loops = s.poly_loops[pi]
            uv = [s.uv[li] for li in loops]
            for k in range(1, len(uv) - 1):
                cells |= _raster_tri(uv[0], uv[k], uv[k + 1], res)
        for c in cells:
            if c in grid and grid[c] != isl_id:
                overlap.add(c)
            else:
                grid[c] = isl_id
    return len(grid), len(overlap)


def _raster_tri(a, b, c, res):
    xs = [a[0] * res, b[0] * res, c[0] * res]
    ys = [a[1] * res, b[1] * res, c[1] * res]
    x0, x1 = max(0, int(math.floor(min(xs)))), min(res - 1, int(math.ceil(max(xs))))
    y0, y1 = max(0, int(math.floor(min(ys)))), min(res - 1, int(math.ceil(max(ys))))
    out = set()

    def edge(ax, ay, bx, by, px, py):
        return (bx - ax) * (py - ay) - (by - ay) * (px - ax)

    area = edge(xs[0], ys[0], xs[1], ys[1], xs[2], ys[2])
    if abs(area) < 1e-12:
        return out
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px, py = x + 0.5, y + 0.5
            w0 = edge(xs[1], ys[1], xs[2], ys[2], px, py)
            w1 = edge(xs[2], ys[2], xs[0], ys[0], px, py)
            w2 = edge(xs[0], ys[0], xs[1], ys[1], px, py)
            if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (w0 <= 0 and w1 <= 0 and w2 <= 0):
                out.add(y * res + x)
    return out


@rule("UV007", "uv", "UV overlap and packing efficiency", DOC + "#uv")
def overlap(ctx: Context):
    res = ctx.threshold("uv_raster_resolution", 256)
    min_eff = ctx.threshold("uv_min_packing_efficiency", 0.45)
    rows, overlapping, low_eff = {}, [], []
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        if not s.uv:
            continue
        cov, ovl = _raster_islands(s, uv_islands(s), res)
        eff = cov / float(res * res)
        rows[ob.name] = {"coverage": round(eff, 3), "overlap_cells_share": round(ovl / float(max(1, cov)), 4)}
        if ovl:
            overlapping.append(ob.name)
        if eff < min_eff:
            low_eff.append(ob.name)
    if not rows:
        return info("UV007", "No UV data.")
    res_ = make_result(ctx, "UV007", bool(low_eff), WARN, "UV coverage OK.",
                       f"UV coverage below {min_eff:.0%} of the texture (wasted texels — or the object shares its "
                       "texture with other meshes: then judge the combined layout).", low_eff,
                       {"per_object": rows, "overlapping_objects": overlapping,
                        "note": "Overlaps are allowed by Roblox [OFFICIEL] but must be intentional (mirroring/stacking) "
                                "and never baked twice."})
    return res_


@rule("UV008", "uv", "UV stretching", DOC + "#uv")
def stretch(ctx: Context):
    ratio = ctx.threshold("uv_stretch_ratio", 4.0)
    max_share = ctx.threshold("uv_stretch_max_share", 0.05)
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        if not s.uv:
            continue
        vals = []
        for pi, a in enumerate(s.face_areas):
            ua = abs(uv_poly_area(s, pi))
            if a > 1e-9 and ua > 1e-14:
                vals.append((ua / a, a))
        if len(vals) < 4:
            continue
        med = mu.weighted_percentile(vals, 50)
        bad_area = sum(a for r, a in vals if r > med * ratio or r < med / ratio)
        share = bad_area / sum(a for _, a in vals)
        if share > max_share:
            bad.append(ob.name)
            details[ob.name] = {"area_share_off_by_%sx" % ratio: round(share, 3)}
    return make_result(ctx, "UV008", bool(bad), WARN, "No significant UV stretching.",
                       "Parts of the surface have a texel density off by more than the ratio from the median "
                       "(stretched or crushed islands).", bad, details)


@rule("UV009", "uv", "Mirrored (flipped) UV faces", DOC + "#miroir")
def flipped(ctx: Context):
    rows = {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        if not s.uv:
            continue
        n = sum(1 for pi in range(len(s.polys)) if uv_poly_area(s, pi) < -1e-14)
        if n:
            rows[ob.name] = n
    if not rows:
        return make_result(ctx, "UV009", False, INFO, "No mirrored UV faces.", "", [])
    return info("UV009", "Mirrored UV faces (fine if intentional; mirrored shells must be offset by 1 tile when "
                "baking and their tangents flip — check normal-map seams on the mirror line).",
                {"flipped_faces": rows}, list(rows))
