"""Shading / normals rules. Standard: Standards/ECLIPSE_SHADING_STANDARD.md

Covers the requested validate_normals script. Normals are read from the
evaluated mesh (custom normals and Weighted Normal modifier included).
"""

from __future__ import annotations

import math

from . import mathutil as mu
from .bpy_helpers import material_images, meshes, snapshot
from .core import INFO, PASS, WARN, Context, info, make_result, rule

DOC = "Standards/ECLIPSE_SHADING_STANDARD.md"
TOPO_CHANGING_AFTER_WN = {"BEVEL", "BOOLEAN", "SUBSURF", "REMESH", "DECIMATE", "SOLIDIFY", "WELD",
                          "EDGE_SPLIT", "SCREW", "ARRAY", "MULTIRES", "NODES"}


def _face_max_dev(s, pi):
    n = s.face_normals[pi]
    worst = 0.0
    for li in s.poly_loops[pi]:
        cn = s.corner_normals[li]
        d = max(-1.0, min(1.0, n.dot(cn)))
        worst = max(worst, math.degrees(math.acos(d)))
    return worst


@rule("SHD001", "shading", "Shading summary (smooth/flat, custom normals)", DOC + "#modele-de-normals")
def shading_summary(ctx: Context):
    rows = {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        if not s.polys:
            continue
        smooth = sum(1 for f in s.poly_smooth if f)
        rows[ob.name] = {
            "smooth_faces_pct": round(100.0 * smooth / len(s.polys), 1),
            "custom_normals": s.has_custom_normals,
            "weighted_normal_modifier": any(m.type == "WEIGHTED_NORMAL" for m in ob.modifiers),
            "sharp_edges": sum(1 for f in s.edge_sharp if f),
        }
    return info("SHD001", f"{len(rows)} mesh objects inspected.", {"per_object": rows})


@rule("SHD002", "shading", "Gradients on large flat faces", DOC + "#weighted-normals")
def big_face_gradients(ctx: Context):
    max_dev = ctx.threshold("big_face_max_normal_dev_deg", 1.0)
    pct = ctx.threshold("big_face_area_percentile", 80)
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        if not s.polys or not any(s.poly_smooth):
            continue
        cutoff = mu.percentile(s.face_areas, pct)
        worst, count = 0.0, 0
        for pi, a in enumerate(s.face_areas):
            if a < cutoff or a <= 1e-8 or not s.poly_smooth[pi]:
                continue
            d = _face_max_dev(s, pi)
            worst = max(worst, d)
            if d > max_dev:
                count += 1
        if count:
            bad.append(ob.name)
            details[ob.name] = {"large_faces_with_gradient": count, "worst_deviation_deg": round(worst, 2),
                                "threshold_deg": max_dev}
    return make_result(ctx, "SHD002", bool(bad), WARN, "Large faces shade flat (normals perpendicular).",
                       "Large faces carry interpolated normals → visible gradients / 'soft' look (melted plastic). "
                       "Use Weighted Normal (Face Area, weight 100, Keep Sharp) or sharp edges.",
                       bad, details)


@rule("SHD003", "shading", "Extreme custom-normal deviation", DOC + "#roblox")
def extreme_normals(ctx: Context):
    limit = ctx.threshold("extreme_normal_deviation_deg", 75.0)
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        count = 0
        for pi, a in enumerate(s.face_areas):
            if a <= 1e-10:
                continue
            if _face_max_dev(s, pi) > limit:
                count += 1
        if count:
            bad.append(ob.name)
            details[ob.name] = {"faces_over_limit": count, "limit_deg": limit}
    return make_result(ctx, "SHD003", bool(bad), WARN, "No extreme normal deviation.",
                       "Corner normals almost perpendicular to their face: black triangles, and on Roblox a reported "
                       "'glowing' artifact at grazing angles. Check the faces (usually tiny bevel faces) in-engine.",
                       bad, details)


@rule("SHD004", "shading", "Weighted Normal modifier setup", DOC + "#weighted-normals")
def weighted_normal_setup(ctx: Context):
    min_w = ctx.threshold("wn_min_weight", 90)
    bad, details, seen = [], {}, 0
    for ob in meshes(ctx):
        mods = list(ob.modifiers)
        wn_idx = [i for i, m in enumerate(mods) if m.type == "WEIGHTED_NORMAL"]
        if not wn_idx:
            continue
        seen += 1
        issues = []
        wn = mods[wn_idx[-1]]
        if wn.weight < min_w:
            issues.append(f"weight {wn.weight} < {min_w} (weight 50 leaves ~5° gradients on large faces, measured)")
        if not wn.keep_sharp:
            issues.append("keep_sharp disabled")
        if wn.mode != "FACE_AREA":
            issues.append(f"mode {wn.mode} (ECLIPSE default FACE_AREA)")
        for m in mods[wn_idx[-1] + 1:]:
            if m.type in TOPO_CHANGING_AFTER_WN and m.show_viewport:
                issues.append(f"{m.type} '{m.name}' after Weighted Normal (normals computed before topology change)")
            if m.type == "TRIANGULATE" and not getattr(m, "keep_custom_normals", False):
                issues.append("Triangulate after Weighted Normal without keep_custom_normals")
        if issues:
            bad.append(ob.name)
            details[ob.name] = issues
    if not seen:
        return info("SHD004", "No Weighted Normal modifier in scope.")
    return make_result(ctx, "SHD004", bool(bad), WARN, f"{seen} Weighted Normal modifier(s) correctly configured.",
                       "Weighted Normal configuration issues.", bad, details)


@rule("SHD005", "shading", "Beveled smooth mesh without normal control", DOC + "#weighted-normals")
def bevel_without_wn(ctx: Context):
    bad = []
    for ob in meshes(ctx):
        has_bevel = any(m.type == "BEVEL" and m.show_viewport for m in ob.modifiers)
        if not has_bevel:
            continue
        s = snapshot(ctx, ob)
        smooth_ratio = sum(s.poly_smooth) / max(1, len(s.polys))
        has_wn = any(m.type == "WEIGHTED_NORMAL" for m in ob.modifiers)
        if smooth_ratio > 0.5 and not has_wn and not s.has_custom_normals:
            bad.append(ob.name)
    return make_result(ctx, "SHD005", bool(bad), WARN, "Beveled meshes have normal control.",
                       "Smooth-shaded beveled meshes without Weighted Normal/custom normals: gradients spread across "
                       "whole panels (a primary cause of the 'melted' look).", bad)


@rule("SHD006", "shading", "Bevel 'Harden Normals' in use", DOC + "#harden-normals")
def harden_normals(ctx: Context):
    users = [ob.name for ob in meshes(ctx)
             for m in ob.modifiers if m.type == "BEVEL" and getattr(m, "harden_normals", False)]
    if not users:
        return make_result(ctx, "SHD006", False, INFO, "Harden Normals not used.", "", [])
    return info("SHD006", "Bevel 'Harden Normals' is used. Regressions were reported after the 4.1 normals "
                "refactor (blender issues #132292, #133978); it worked in our 5.0.1 synthetic test. Prefer a final "
                "Weighted Normal modifier and verify visually.", objects=users)


@rule("SHD007", "shading", "Sharp edges without UV seam on normal-mapped meshes", DOC + "#hard-edges-et-uv")
def sharp_without_seam(ctx: Context):
    bad, details = [], {}
    for ob in meshes(ctx):
        uses_nm = any(usage == "normal" for slot in ob.material_slots if slot.material
                      for (_img, usage, _n) in material_images(slot.material))
        if not uses_nm:
            continue
        s = snapshot(ctx, ob)
        n = sum(1 for sh, se in zip(s.edge_sharp, s.edge_seam) if sh and not se)
        if n:
            bad.append(ob.name)
            details[ob.name] = {"sharp_edges_without_seam": n}
    return make_result(ctx, "SHD007", bool(bad), WARN, "Every hard edge of normal-mapped meshes is a UV seam.",
                       "Hard edges without UV split on a normal-mapped mesh bake a visible seam line "
                       "(Marmoset/Polycount rule: hard edge ⇒ UV split).", bad, details)
