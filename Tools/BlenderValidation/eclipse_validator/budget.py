"""Triangle / MeshPart budgets and the detail value/cost table.

Covers the requested validate_triangle_budget script.
Standard: Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md#budgets
"""

from __future__ import annotations

from . import mathutil as mu
from .bpy_helpers import meshes, snapshot
from .core import FAIL, INFO, WARN, Context, info, make_result, rule

DOC = "Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md"


@rule("BUD001", "budget", "Triangles per MeshPart (official hard limit)", DOC + "#budgets")
def per_part_hard(ctx: Context):
    hard = ctx.threshold("max_tris_per_meshpart_hard", 20000)
    soft = ctx.threshold("tris_soft_max_part", 12000)
    fails, warns, details = [], [], {}
    for ob in meshes(ctx):
        n = snapshot(ctx, ob).tri_count
        if n > hard:
            fails.append(ob.name)
            details[ob.name] = n
        elif n > soft:
            warns.append(ob.name)
            details[ob.name] = n
    if fails:
        return make_result(ctx, "BUD001", True, FAIL, "", f"MeshPart(s) above the {hard}-triangle import limit "
                           "[OFFICIEL]: import will be rejected. Split or reduce.", fails + warns,
                           {"tris": details, "hard_limit": hard, "soft_limit": soft})
    return make_result(ctx, "BUD001", bool(warns), WARN, f"Every part ≤ {soft} tris (hard limit {hard}).",
                       f"Part(s) above the profile soft limit {soft}.", warns, {"tris": details})


@rule("BUD002", "budget", "Total triangles vs profile", DOC + "#budgets")
def total(ctx: Context):
    soft = ctx.threshold("tris_soft_max_total", 30000)
    n = sum(snapshot(ctx, ob).tri_count for ob in meshes(ctx))
    return make_result(ctx, "BUD002", n > soft, WARN, f"Total {n} tris ≤ {soft}.",
                       f"Total {n} tris > profile target {soft}. Use the value/cost table (BUD004) to decide.",
                       [], {"total_tris": n, "target": soft})


@rule("BUD003", "budget", "MeshPart count vs profile", DOC + "#multi-meshpart")
def part_count(ctx: Context):
    mx = ctx.threshold("meshpart_max", 16)
    n = len(meshes(ctx))
    return make_result(ctx, "BUD003", n > mx, WARN, f"{n} mesh parts ≤ {mx}.",
                       f"{n} mesh parts > {mx}: each MeshPart with a unique mesh is at least one draw call "
                       "(instancing only merges identical MeshContent + identical SurfaceAppearance [OFFICIEL]). "
                       "Merge static parts that never move independently.", [], {"count": n, "max": mx})


@rule("BUD004", "budget", "Detail value / cost table", DOC + "#valeur-cout")
def value_cost(ctx: Context):
    dist = ctx.threshold("view_distance", 2.0)
    fov = ctx.threshold("camera_vertical_fov_deg", 70.0)
    h = ctx.threshold("screen_height_px", 1080)
    min_px = ctx.threshold("micro_min_projected_px", 3.0)
    obs = meshes(ctx)
    total = sum(snapshot(ctx, ob).tri_count for ob in obs) or 1
    rows, suspicious = {}, []
    for ob in obs:
        s = snapshot(ctx, ob)
        dims = sorted(s.dimensions())
        size = dims[-1] if dims else 0.0
        px = mu.projected_px(size, dist, fov, h)
        tris_per_px = s.tri_count / max(1.0, px * px)
        rows[ob.name] = {"tris": s.tri_count, "share_pct": round(100.0 * s.tri_count / total, 1),
                         "largest_dim_studs": round(size, 4), "screen_px": round(px, 1),
                         "tris_per_screen_px2": round(tris_per_px, 3)}
        if px < 4 * min_px and s.tri_count > 150:
            suspicious.append(ob.name)
    res = make_result(ctx, "BUD004", bool(suspicious), WARN,
                      "No small-on-screen part carries a large triangle count.",
                      "Parts that are small on screen at the profile distance but carry many triangles: candidates "
                      "for normal map / texture / omission.", suspicious,
                      {"profile_distance": dist, "table": rows})
    if not suspicious:
        res.status = INFO
        res.details = {"profile_distance": dist, "table": rows}
    return res
