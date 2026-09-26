"""Geometry rules (evaluated meshes, world space).

Covers the requested validate_mesh / validate_non_manifold / validate_degenerate /
validate_duplicate_vertices scripts. Standard: Standards/ECLIPSE_TOPOLOGY_STANDARD.md
"""

from __future__ import annotations

import math
from typing import Dict, List

from mathutils import kdtree

from . import mathutil as mu
from .bpy_helpers import edge_face_map, face_components, meshes, snapshot
from .core import FAIL, INFO, PASS, WARN, Context, make_result, rule, skip

DOC = "Standards/ECLIPSE_TOPOLOGY_STANDARD.md"
DOC_SHADING = "Standards/ECLIPSE_SHADING_STANDARD.md#diagnostic-des-fines-lignes"


def _allow_open(ob) -> bool:
    return bool(ob.get("eclipse_allow_open", False))


@rule("GEO001", "geometry", "Non-manifold / open edges", DOC + "#manifold")
def non_manifold(ctx: Context):
    bad_open, bad_multi, details = [], [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        efm = edge_face_map(s)
        boundary = sum(1 for users in efm.values() if len(users) == 1)
        multi = sum(1 for users in efm.values() if len(users) > 2)
        if boundary and not _allow_open(ob):
            bad_open.append(ob.name)
        if multi:
            bad_multi.append(ob.name)
        if boundary or multi:
            details[ob.name] = {"boundary_edges": boundary, "edges_with_3plus_faces": multi}
    violated = bool(bad_open or bad_multi)
    return make_result(ctx, "GEO001", violated, WARN,
                       "All meshes are closed and manifold.",
                       "Open or non-manifold edges found. Roblox requires watertight geometry "
                       "[OFFICIEL]; open edges are also where T-junction cracks appear. Mark intentional "
                       "open shells with the custom property eclipse_allow_open=True.",
                       bad_open + bad_multi, details)


@rule("GEO002", "geometry", "Loose vertices / wire edges", DOC + "#manifold")
def loose(ctx: Context):
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        used_v = set(v for p in s.polys for v in p)
        loose_v = len(s.verts) - len(used_v)
        efm = edge_face_map(s)
        wire = sum(1 for e in s.edges if (min(e), max(e)) not in efm)
        if loose_v or wire:
            bad.append(ob.name)
            details[ob.name] = {"loose_vertices": loose_v, "wire_edges": wire}
    return make_result(ctx, "GEO002", bool(bad), FAIL, "No loose vertices or wire edges.",
                       "Loose vertices or wire edges (invisible data that pollutes bounds, pivots and export).",
                       bad, details)


@rule("GEO003", "geometry", "Degenerate faces and zero-length edges", DOC + "#degenerate")
def degenerate(ctx: Context):
    area_eps = ctx.threshold("degenerate_area", 1e-10)
    len_eps = ctx.threshold("degenerate_edge_length", 1e-6)
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        zero_faces = sum(1 for a in s.face_areas if a < area_eps)
        zero_edges = sum(1 for a, b in s.edges if (s.verts[a] - s.verts[b]).length < len_eps)
        if zero_faces or zero_edges:
            bad.append(ob.name)
            details[ob.name] = {"zero_area_faces": zero_faces, "zero_length_edges": zero_edges}
    return make_result(ctx, "GEO003", bool(bad), FAIL, "No degenerate faces or edges.",
                       "Degenerate faces/edges: they break normals, baking and Roblox import.",
                       bad, details)


@rule("GEO004", "geometry", "Duplicate (unwelded) vertices", DOC_SHADING)
def duplicate_vertices(ctx: Context):
    dist = ctx.threshold("merge_distance", 1e-5)
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        if not s.verts:
            continue
        tree = kdtree.KDTree(len(s.verts))
        for i, v in enumerate(s.verts):
            tree.insert(v, i)
        tree.balance()
        dup = 0
        for i, v in enumerate(s.verts):
            for (_co, j, _d) in tree.find_range(v, dist):
                if j > i:
                    dup += 1
        if dup:
            bad.append(ob.name)
            details[ob.name] = {"coincident_vertex_pairs": dup, "merge_distance": dist}
    return make_result(ctx, "GEO004", bool(bad), WARN, "No coincident vertices.",
                       "Coincident but unwelded vertices: typical cause of hairline cracks and "
                       "shading seams. Intentional split shells (e.g. separate panels) are acceptable — decide per case.",
                       bad, details)


@rule("GEO005", "geometry", "T-junctions on open borders", DOC_SHADING)
def t_junctions(ctx: Context):
    tol = ctx.threshold("tjunction_tolerance", 1e-4)
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        efm = edge_face_map(s)
        bedges = [k for k, users in efm.items() if len(users) == 1]
        if not bedges:
            continue
        bverts = sorted(set(v for e in bedges for v in e))
        tree = kdtree.KDTree(len(bverts))
        for i, vi in enumerate(bverts):
            tree.insert(s.verts[vi], vi)
        tree.balance()
        count = 0
        for a, b in bedges:
            pa, pb = s.verts[a], s.verts[b]
            mid = (pa + pb) * 0.5
            radius = (pb - pa).length * 0.5 + tol
            for (_co, vi, _d) in tree.find_range(mid, radius):
                if vi in (a, b):
                    continue
                d, t = mu.segment_point_distance(pa, pb, s.verts[vi])
                if d < tol and 1e-3 < t < 1 - 1e-3:
                    count += 1
        if count:
            bad.append(ob.name)
            details[ob.name] = {"t_junctions": count}
    return make_result(ctx, "GEO005", bool(bad), WARN, "No T-junctions detected.",
                       "Vertices lying on another border edge (T-junctions): rasterisation leaves "
                       "sparkling pixels/fine lines along the seam. Weld or add the matching vertex.",
                       bad, details)


@rule("GEO006", "geometry", "Face winding consistency / inside-out shells", DOC + "#normals-orientation")
def winding(ctx: Context):
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        efm = edge_face_map(s)
        inconsistent = 0
        for users in efm.values():
            if len(users) == 2 and users[0][1] == users[1][1]:
                inconsistent += 1
        inverted_shells = 0
        for comp in face_components(s):
            closed = True
            comp_set = set(comp)
            for pi in comp:
                poly = s.polys[pi]
                for k in range(len(poly)):
                    a, b = poly[k], poly[(k + 1) % len(poly)]
                    users = efm[(min(a, b), max(a, b))]
                    if len(users) != 2 or not all(u[0] in comp_set for u in users):
                        closed = False
                        break
                if not closed:
                    break
            if not closed:
                continue
            vol = 0.0
            for pi in comp:
                pts = [s.verts[i] for i in s.polys[pi]]
                for k in range(1, len(pts) - 1):
                    vol += pts[0].dot(pts[k].cross(pts[k + 1])) / 6.0
            if vol < 0:
                inverted_shells += 1
        if inconsistent or inverted_shells:
            bad.append(ob.name)
            details[ob.name] = {"inconsistent_edges": inconsistent, "inside_out_closed_shells": inverted_shells}
    return make_result(ctx, "GEO006", bool(bad), FAIL, "Winding is consistent and closed shells face outward.",
                       "Flipped faces or inside-out shells: back-face culling in Roblox makes them "
                       "disappear or shade black. Recalculate outside on a copy and re-check.",
                       bad, details)


@rule("GEO007", "geometry", "N-gons (non-planar / concave)", DOC + "#n-gons")
def ngons(ctx: Context):
    ratio = ctx.threshold("ngon_planarity_ratio", 0.002)
    risky_objs, details, total = [], {}, 0
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        n_total = nonplanar = concave = 0
        for pi, poly in enumerate(s.polys):
            if len(poly) <= 4:
                continue
            n_total += 1
            pts = [s.verts[i] for i in poly]
            nrm, center = s.face_normals[pi], s.face_centers[pi]
            diag = max((p - center).length for p in pts) * 2 or 1.0
            if max(abs((p - center).dot(nrm)) for p in pts) > ratio * diag:
                nonplanar += 1
            sign = 0
            for k in range(len(pts)):
                c = (pts[(k + 1) % len(pts)] - pts[k]).cross(pts[(k + 2) % len(pts)] - pts[(k + 1) % len(pts)])
                d = c.dot(nrm)
                if abs(d) < 1e-12:
                    continue
                sg = 1 if d > 0 else -1
                if sign == 0:
                    sign = sg
                elif sg != sign:
                    concave += 1
                    break
        total += n_total
        if nonplanar or concave:
            risky_objs.append(ob.name)
        if n_total:
            details[ob.name] = {"ngons": n_total, "non_planar": nonplanar, "concave": concave}
    if not details:
        return make_result(ctx, "GEO007", False, INFO, "No n-gons.", "", [], {})
    res = make_result(ctx, "GEO007", bool(risky_objs), WARN,
                      f"{total} planar convex n-gons (acceptable on static flat surfaces; triangulate in the export copy).",
                      "Non-planar or concave n-gons: triangulation becomes unpredictable (engine vs baker) "
                      "and creates shading artifacts. Fix or triangulate deliberately.",
                      risky_objs, details)
    if res.status == PASS:
        res.status = INFO
        res.details = details
    return res


@rule("GEO008", "geometry", "Duplicate / overlapping faces", DOC_SHADING)
def duplicate_faces(ctx: Context):
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        seen: Dict[tuple, int] = {}
        dup = 0
        for poly in s.polys:
            key = tuple(sorted((round(s.verts[i].x, 5), round(s.verts[i].y, 5), round(s.verts[i].z, 5)) for i in poly))
            seen[key] = seen.get(key, 0) + 1
        dup = sum(c - 1 for c in seen.values() if c > 1)
        if dup:
            bad.append(ob.name)
            details[ob.name] = {"duplicate_faces": dup}
    return make_result(ctx, "GEO008", bool(bad), FAIL, "No duplicate faces.",
                       "Faces sharing the exact same vertices (z-fighting flicker, doubled tris).",
                       bad, details)


@rule("GEO009", "geometry", "Sliver triangles", DOC_SHADING)
def slivers(ctx: Context):
    min_angle = ctx.threshold("sliver_min_angle_deg", 1.0)
    min_area = ctx.threshold("sliver_min_area", 1e-8)
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        count = 0
        for (a, b, c), _pi in s.tris:
            pa, pb, pc = s.verts[a], s.verts[b], s.verts[c]
            area = (pb - pa).cross(pc - pa).length * 0.5
            if area < min_area:
                continue
            if mu.triangle_min_angle(pa, pb, pc) < min_angle:
                count += 1
        if count:
            bad.append(ob.name)
            details[ob.name] = {"sliver_triangles": count, "min_angle_deg": min_angle}
    return make_result(ctx, "GEO009", bool(bad), WARN, "No sliver triangles.",
                       "Very thin triangles: normal interpolation and specular aliasing produce fine "
                       "bright/dark lines, especially on the Worldmodel. Usually a boolean or n-gon triangulation side effect.",
                       bad, details)


@rule("GEO010", "geometry", "Micro-geometry islands (probably invisible)", "Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md#valeur-cout")
def micro_islands(ctx: Context):
    dist = ctx.threshold("view_distance", 2.0)
    fov = ctx.threshold("camera_vertical_fov_deg", 70.0)
    h = ctx.threshold("screen_height_px", 1080)
    min_px = ctx.threshold("micro_min_projected_px", 3.0)
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        small = 0
        small_tris = 0
        for comp in face_components(s):
            vs = [s.verts[i] for pi in comp for i in s.polys[pi]]
            lo = [min(v[k] for v in vs) for k in range(3)]
            hi = [max(v[k] for v in vs) for k in range(3)]
            diag = math.sqrt(sum((hi[k] - lo[k]) ** 2 for k in range(3)))
            if mu.projected_px(diag, dist, fov, h) < min_px:
                small += 1
                small_tris += sum(max(0, len(s.polys[pi]) - 2) for pi in comp)
        if small:
            bad.append(ob.name)
            details[ob.name] = {"islands_below_px": small, "tris_in_them": small_tris,
                                "threshold_px": min_px, "view_distance": dist}
    return make_result(ctx, "GEO010", bool(bad), WARN, "No invisible micro-islands at the profile distance.",
                       "Disconnected pieces smaller than the pixel threshold at the profile viewing distance: "
                       "triangles without visual value (move to normal map/texture or delete in the WM).",
                       bad, details)
