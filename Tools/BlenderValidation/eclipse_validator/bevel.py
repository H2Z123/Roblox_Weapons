"""Bevel rules. Standard: Standards/ECLIPSE_BEVEL_STANDARD.md

Bevel widths are measured in studs: modifier width × object scale (the modifier
works in local space). Screen size uses the profile viewing distance.
"""

from __future__ import annotations

from . import mathutil as mu
from .bpy_helpers import meshes, snapshot
from .core import INFO, WARN, Context, info, make_result, rule

DOC = "Standards/ECLIPSE_BEVEL_STANDARD.md"


def _bevels(ob):
    return [m for m in ob.modifiers if m.type == "BEVEL" and m.show_viewport]


def _width_studs(ob, m):
    if m.offset_type == "PERCENT":
        return None
    sc = ob.matrix_world.to_scale()
    return m.width * (abs(sc.x) + abs(sc.y) + abs(sc.z)) / 3.0


@rule("BEV001", "bevel", "Bevel segment count vs profile", DOC + "#segments")
def segments(ctx: Context):
    max_seg = ctx.threshold("max_bevel_segments", 3)
    bad, details = [], {}
    for ob in meshes(ctx):
        for m in _bevels(ob):
            if m.segments > max_seg:
                bad.append(ob.name)
                details[f"{ob.name}/{m.name}"] = {"segments": m.segments, "max": max_seg}
    return make_result(ctx, "BEV001", bool(bad), WARN, f"All bevels ≤ {max_seg} segments.",
                       "Bevel segments above the profile budget (measured cost on a box: 12→44→108→188→300 tris "
                       "for 0→4 segments).", bad, details)


@rule("BEV002", "bevel", "Bevel too small to be seen", DOC + "#largeur")
def too_small(ctx: Context):
    dist = ctx.threshold("view_distance", 2.0)
    fov = ctx.threshold("camera_vertical_fov_deg", 70.0)
    h = ctx.threshold("screen_height_px", 1080)
    min_px = ctx.threshold("min_bevel_px", 2.0)
    min_w = mu.min_visible_width(min_px, dist, fov, h)
    bad, details = [], {}
    for ob in meshes(ctx):
        for m in _bevels(ob):
            w = _width_studs(ob, m)
            if w is not None and w < min_w:
                bad.append(ob.name)
                details[f"{ob.name}/{m.name}"] = {"width_studs": round(w, 5), "min_visible_studs": round(min_w, 5),
                                                  "px_at_profile_distance": round(mu.projected_px(w, dist, fov, h), 2)}
    return make_result(ctx, "BEV002", bool(bad), WARN, f"All bevels ≥ {min_px}px at {dist} studs.",
                       "Bevels narrower than the visibility threshold at the profile distance cost triangles "
                       "without reading on screen (WM: remove; VM: widen or move to normal map).", bad,
                       dict(details, **{"profile_distance": dist, "min_visible_width": round(min_w, 5)}))


@rule("BEV003", "bevel", "Bevel too wide for the form (melted risk)", "Standards/ECLIPSE_ANTI_MELTED_PLASTIC.md")
def too_wide(ctx: Context):
    max_ratio = ctx.threshold("max_bevel_ratio", 0.1)
    bad, details = [], {}
    for ob in meshes(ctx):
        bevs = _bevels(ob)
        if not bevs:
            continue
        dims = sorted(d for d in snapshot(ctx, ob).dimensions() if d > 1e-6)
        if not dims:
            continue
        smallest = dims[0]
        for m in bevs:
            w = _width_studs(ob, m)
            if w is not None and w / smallest > max_ratio:
                bad.append(ob.name)
                details[f"{ob.name}/{m.name}"] = {"width_studs": round(w, 5), "smallest_dimension": round(smallest, 4),
                                                  "ratio": round(w / smallest, 3), "max_ratio": max_ratio}
    return make_result(ctx, "BEV003", bool(bad), WARN, "Bevel widths stay proportionate.",
                       "Bevel width is large relative to the part's smallest dimension: forms inflate and read soft.",
                       bad, details)


@rule("BEV004", "bevel", "Bevel on unapplied / non-uniform scale", DOC + "#echelle")
def bevel_scale(ctx: Context):
    bad, details = [], {}
    for ob in meshes(ctx):
        if not _bevels(ob):
            continue
        sc = ob.matrix_world.to_scale()
        if max(abs(sc.x), abs(sc.y), abs(sc.z)) - min(abs(sc.x), abs(sc.y), abs(sc.z)) > 1e-4 or abs(sc.x - 1) > 1e-4:
            bad.append(ob.name)
            details[ob.name] = {"world_scale": [round(v, 4) for v in sc]}
    return make_result(ctx, "BEV004", bool(bad), WARN, "Beveled objects have scale 1.",
                       "Bevel widths are evaluated in local space: a scaled object gets distorted/inconsistent bevels.",
                       bad, details)


@rule("BEV005", "bevel", "Bevel limit method / clamp", DOC + "#reglages")
def limit_method(ctx: Context):
    rows = {}
    for ob in meshes(ctx):
        for m in _bevels(ob):
            notes = []
            if m.limit_method == "NONE":
                notes.append("limit NONE: every edge rounded ('rounded everything' risk)")
            if not m.use_clamp_overlap:
                notes.append("clamp overlap off: overlapping geometry risk")
            if notes:
                rows[f"{ob.name}/{m.name}"] = notes
    if not rows:
        return make_result(ctx, "BEV005", False, INFO, "Bevel limits and clamp look sane.", "", [])
    return info("BEV005", "Bevel settings to review.", {"modifiers": rows},
                objects=[k.split("/")[0] for k in rows])


@rule("BEV006", "bevel", "Bevel width distribution (hierarchy)", DOC + "#hierarchie")
def width_distribution(ctx: Context):
    widths = {}
    for ob in meshes(ctx):
        for m in _bevels(ob):
            w = _width_studs(ob, m)
            if w is not None:
                widths[f"{ob.name}/{m.name}"] = round(w, 5)
    if not widths:
        return info("BEV006", "No bevel modifiers (bevels may be applied in the mesh).")
    distinct = sorted(set(widths.values()))
    return info("BEV006", f"{len(distinct)} distinct bevel widths: {distinct[:12]}. ECLIPSE expects a small "
                "set of classes (B1 primary / B2 secondary / B3 tertiary ≈ 1 : 0.5 : 0.25).",
                {"widths": widths})
