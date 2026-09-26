"""Pivots, moving parts, collisions/sweeps, grip reference and armature rules.

Covers the requested validate_pivots / validate_moving_parts scripts.
Standards: Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md,
           Standards/ECLIPSE_GRIP_MODELING_STANDARD.md

Motion definition (per moving object), from custom properties first, then
config ``moving_parts[<object name or roblox_name>]``:
    eclipse_motion_type  : "ROTATE" | "TRANSLATE"
    eclipse_motion_axis  : "X" | "Y" | "Z" | "-X" ... (local axis of the pivot)
    eclipse_motion_min / eclipse_motion_max : degrees (ROTATE) or studs (TRANSLATE)
    eclipse_motion_pivot : optional name of an Empty defining the pivot frame
                           (default: the object's own origin/orientation)
"""

from __future__ import annotations

import math
import re
from itertools import combinations
from typing import Dict, List, Optional, Tuple

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from . import mathutil as mu
from .bpy_helpers import descendants, meshes, role, roblox_name, snapshot
from .config import motion_for
from .core import FAIL, INFO, WARN, Context, info, make_result, rule, skip

DOC = "Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md"
DOC_GRIP = "Standards/ECLIPSE_GRIP_MODELING_STANDARD.md"
CONTACT_SHRINK = 1e-4  # studs; removes exact face contacts from intersection tests


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def motion(ctx: Context, ob) -> Optional[Dict]:
    m = None
    if "eclipse_motion_type" in ob.keys():
        m = {"type": str(ob["eclipse_motion_type"]).upper(),
             "axis": str(ob.get("eclipse_motion_axis", "X")),
             "min": float(ob.get("eclipse_motion_min", 0.0)),
             "max": float(ob.get("eclipse_motion_max", 0.0)),
             "pivot": str(ob.get("eclipse_motion_pivot", "") or "")}
    else:
        m = motion_for(ctx.config, [ob.name, roblox_name(ob)])
        if m:
            m.setdefault("pivot", "")
            m["type"] = str(m.get("type", "ROTATE")).upper()
    return m


def is_moving(ctx: Context, ob) -> bool:
    return role(ob) == "moving" or motion(ctx, ob) is not None


def _pivot_matrix(ob, m) -> Matrix:
    piv = bpy.data.objects.get(m.get("pivot") or "") if m.get("pivot") else None
    mw = (piv or ob).matrix_world
    loc, rot, _sc = mw.decompose()
    return Matrix.Translation(loc) @ rot.to_matrix().to_4x4()


def pose_matrix(ob, m, value: float) -> Matrix:
    """World-space delta matrix moving ``ob`` by ``value`` along its motion."""
    P = _pivot_matrix(ob, m)
    ax = Vector(mu.axis_vector(m.get("axis", "X")))
    if m["type"] == "ROTATE":
        local = Matrix.Rotation(math.radians(value), 4, ax)
    else:
        local = Matrix.Translation(ax * value)
    return P @ local @ P.inverted()


def _resolve_value(m, v) -> float:
    if v == "min":
        return m["min"]
    if v == "max":
        return m["max"]
    return float(v)


def _bvh(verts, polys, shrink: float = 0.0) -> BVHTree:
    if shrink > 0:
        vnorm = [Vector((0, 0, 0)) for _ in verts]
        for poly in polys:
            if len(poly) < 3:
                continue
            n = (verts[poly[1]] - verts[poly[0]]).cross(verts[poly[2]] - verts[poly[0]])
            if n.length > 0:
                n.normalize()
                for i in poly:
                    vnorm[i] += n
        verts = [v - (n.normalized() * shrink if n.length > 0 else n) for v, n in zip(verts, vnorm)]
    return BVHTree.FromPolygons([tuple(v) for v in verts], [list(p) for p in polys])


class _Solid:
    """BVH + closedness + bbox of one part in a given pose (for containment tests)."""

    def __init__(self, verts, polys):
        self.tree = _bvh(verts, polys)
        edges = {}
        for poly in polys:
            for k in range(len(poly)):
                a, b = poly[k], poly[(k + 1) % len(poly)]
                key = (min(a, b), max(a, b))
                edges[key] = edges.get(key, 0) + 1
        self.closed = bool(edges) and all(c == 2 for c in edges.values())
        self.lo = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts))) if verts else Vector()
        self.hi = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts))) if verts else Vector()

    def contains_any(self, points, tol: float) -> int:
        """Number of points strictly inside this closed solid (deeper than ``tol``)."""
        if not self.closed:
            return 0
        n = 0
        for p in points:
            if not all(self.lo[i] - tol <= p[i] <= self.hi[i] + tol for i in range(3)):
                continue
            hit = self.tree.find_nearest(p)
            if hit[0] is None or hit[3] <= tol:
                continue
            if _inside(self.tree, p):
                n += 1
        return n


def _probe_points(verts, polys):
    pts = list(verts)
    for poly in polys:
        c = Vector((0.0, 0.0, 0.0))
        for i in poly:
            c += verts[i]
        pts.append(c / max(1, len(poly)))
    return pts


def _ignored(ctx: Context, a: str, b: str) -> bool:
    for pair in ctx.config.get("collision_ignore_pairs", []):
        if len(pair) == 2 and {a, b} == {pair[0], pair[1]}:
            return True
    return False


def _collidables(ctx: Context):
    return [ob for ob in meshes(ctx) if role(ob) != "reference" and not ob.get("eclipse_no_collision")]


# ---------------------------------------------------------------------------
# pivots
# ---------------------------------------------------------------------------

@rule("PIV001", "pivots", "Origin far outside the part", DOC + "#pivots")
def origin_outside(ctx: Context):
    ratio = ctx.threshold("origin_max_distance_ratio", 0.5)
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        lo, hi = s.bbox()
        diag = (hi - lo).length
        if diag <= 1e-9:
            continue
        o = ob.matrix_world.translation
        closest = Vector((min(max(o[i], lo[i]), hi[i]) for i in range(3)))
        d = (o - closest).length
        if d > ratio * diag:
            bad.append(ob.name)
            details[ob.name] = {"distance_to_bbox": round(d, 4), "bbox_diagonal": round(diag, 4)}
    return make_result(ctx, "PIV001", bool(bad), WARN, "Origins sit on or near their parts.",
                       "Origin far away from the part: rotations/animations will orbit around a wrong point "
                       "(unless this is an intentional hinge — then document it with eclipse_motion_pivot).",
                       bad, details)


@rule("PIV002", "pivots", "Moving part with default (bbox-centre) origin", DOC + "#pivots")
def default_origin(ctx: Context):
    bad = []
    for ob in meshes(ctx):
        if not is_moving(ctx, ob):
            continue
        m = motion(ctx, ob) or {}
        if m.get("pivot"):
            continue
        lo, hi = snapshot(ctx, ob).bbox()
        c = (lo + hi) * 0.5
        if (ob.matrix_world.translation - c).length < 1e-4 * max(1.0, (hi - lo).length) and m.get("type", "ROTATE") == "ROTATE":
            bad.append(ob.name)
    return make_result(ctx, "PIV002", bool(bad), WARN, "Rotating parts have intentional pivots.",
                       "Rotating part whose origin is exactly its bounding-box centre (Blender default after "
                       "'Origin to Geometry'): a hinge almost never is. Put the origin on the hinge axis or set "
                       "eclipse_motion_pivot.", bad)


@rule("PIV003", "pivots", "Required reference markers", DOC + "#reperes")
def required_markers(ctx: Context):
    req = ctx.threshold("required_markers", [])
    pats = ctx.config.get("markers", {})
    missing = []
    found = {}
    for key in req:
        pat = pats.get(key)
        hits = [ob.name for ob in ctx.scope if pat and re.search(pat, ob.name)]
        if hits:
            found[key] = hits
        else:
            missing.append(key)
    if not req:
        return skip("PIV003", "No markers required by this profile.")
    return make_result(ctx, "PIV003", bool(missing), WARN, f"Markers present: {found}.",
                       f"Missing reference markers: {missing} (Empties named e.g. Grip_Att / Muzzle_Att).",
                       [], {"missing": missing, "found": found, "patterns": {k: pats.get(k) for k in req}})


@rule("PIV004", "pivots", "Roblox attachment objects (_Att)", DOC + "#attachments")
def attachments(ctx: Context):
    atts = [ob for ob in ctx.scope if ob.name.endswith("_Att")]
    if not atts:
        return make_result(ctx, "PIV004", False, INFO, "No _Att objects.", "", [])
    bad = [ob.name for ob in atts if ob.parent is None or ob.parent.type != "MESH" or ob.parent not in ctx.scope]
    return make_result(ctx, "PIV004", bool(bad), WARN,
                       f"{len(atts)} _Att object(s), all parented to exported meshes (the Roblox importer converts "
                       "'_Att' objects to Attachments [OFFICIEL]).",
                       "_Att objects must be children of the MeshPart they belong to.", bad,
                       {"attachments": [a.name for a in atts]})


# ---------------------------------------------------------------------------
# collisions & motion
# ---------------------------------------------------------------------------

def _world_geo(ctx: Context, ob, delta: Optional[Matrix] = None):
    s = snapshot(ctx, ob)
    verts = s.verts if delta is None else [delta @ v for v in s.verts]
    return verts, s.polys


@rule("MOV001", "moving_parts", "Intersections between parts at rest", DOC + "#collisions")
def rest_intersections(ctx: Context):
    obs = _collidables(ctx)
    geo = {ob.name: _world_geo(ctx, ob) for ob in obs}
    trees = {n: _bvh(*g, shrink=CONTACT_SHRINK) for n, g in geo.items()}
    solids = {n: _Solid(*g) for n, g in geo.items()}
    probes = {n: _probe_points(*g) for n, g in geo.items()}
    hits = {}
    for a, b in combinations(obs, 2):
        if _ignored(ctx, a.name, b.name):
            continue
        crossing = len(trees[a.name].overlap(trees[b.name]))
        inside = solids[a.name].contains_any(probes[b.name], CONTACT_SHRINK) + \
            solids[b.name].contains_any(probes[a.name], CONTACT_SHRINK)
        if crossing or inside:
            hits[f"{a.name} × {b.name}"] = {"crossing_triangle_pairs": crossing, "points_inside": inside}
    return make_result(ctx, "MOV001", bool(hits), FAIL, "No interpenetration at rest.",
                       "Parts interpenetrate in the rest pose (surface crossings or points buried inside another "
                       "closed part; contact within 1e-4 stud is tolerated). Whitelist intentional overlaps in "
                       "config.collision_ignore_pairs.",
                       sorted(set(n for k in hits for n in k.split(" × "))), {"pairs": hits})


@rule("MOV002", "moving_parts", "Clearance around moving parts", DOC + "#jeux-et-clearances")
def clearance(ctx: Context):
    cmin = ctx.threshold("clearance_min", 0.002)
    obs = _collidables(ctx)
    movers = [ob for ob in obs if is_moving(ctx, ob)]
    if not movers:
        return skip("MOV002", "No moving parts defined (eclipse_role='moving' or motion definition).")
    rows, bad = {}, []
    for mv in movers:
        mv_set = {mv.name} | {d.name for d in descendants(mv)}
        for other in obs:
            if other.name in mv_set or _ignored(ctx, mv.name, other.name):
                continue
            tree = _bvh(*_world_geo(ctx, other))
            best = math.inf
            for v in snapshot(ctx, mv).verts:
                hit = tree.find_nearest(v, cmin * 4)
                if hit[0] is not None:
                    best = min(best, hit[3])
            if best < cmin:
                rows[f"{mv.name} ↔ {other.name}"] = round(best, 5)
                bad.append(mv.name)
    return make_result(ctx, "MOV002", bool(bad), WARN, f"Moving parts keep ≥ {cmin} stud clearance (vertex sampling).",
                       f"Moving part(s) closer than {cmin} stud to another part: z-fighting/flicker and collision "
                       "risk during animation.", bad, {"min_distance": rows, "clearance_min": cmin})


def _sweep(ctx: Context, mover, preset: Dict[str, float], steps: int):
    m = motion(ctx, mover)
    if not m:
        return None, "no motion definition"
    obs = _collidables(ctx)
    by_name = {o.name: o for o in obs}
    # static deltas for pre-posed parts (and their descendants)
    deltas: Dict[str, Matrix] = {}
    for pname, val in preset.items():
        pob = by_name.get(pname) or next((o for o in obs if roblox_name(o) == pname), None)
        pm = motion(ctx, pob) if pob else None
        if pob is None or pm is None:
            continue
        d = pose_matrix(pob, pm, _resolve_value(pm, val))
        for o in [pob] + descendants(pob):
            deltas[o.name] = d
    mv_set = [mover] + [d for d in descendants(mover) if d in obs]
    mv_names = {o.name for o in mv_set}
    statics = [o for o in obs if o.name not in mv_names]
    static_geo = {o.name: _world_geo(ctx, o, deltas.get(o.name)) for o in statics}
    static_trees = {n: _bvh(*g) for n, g in static_geo.items()}
    static_solids = {n: _Solid(*g) for n, g in static_geo.items()}
    lo, hi = m["min"], m["max"]
    for k in range(steps + 1):
        val = lo + (hi - lo) * k / max(1, steps)
        d = pose_matrix(mover, m, val)
        for o in mv_set:
            base = deltas.get(o.name)
            # own motion expressed at rest, then carried by the pre-posed parent
            delta = d if base is None else base @ d
            verts, polys = _world_geo(ctx, o, delta)
            t = _bvh(verts, polys, shrink=CONTACT_SHRINK)
            pts = _probe_points(verts, polys)
            for sname, st in static_trees.items():
                if _ignored(ctx, o.name, sname):
                    continue
                if t.overlap(st) or static_solids[sname].contains_any(pts, CONTACT_SHRINK):
                    return {"value": round(val, 4), "part": o.name, "against": sname,
                            "unit": "deg" if m["type"] == "ROTATE" else "stud"}, None
    return {}, None


@rule("MOV003", "moving_parts", "Motion sweep collisions", DOC + "#balayage")
def sweeps(ctx: Context):
    steps = int(ctx.threshold("sweep_steps", 24))
    scenarios = list(ctx.config.get("sweep_scenarios", []))
    if not scenarios:
        scenarios = [{"name": f"{ob.name}_alone", "sweep": ob.name, "set": {}}
                     for ob in _collidables(ctx) if motion(ctx, ob)]
    if not scenarios:
        return skip("MOV003", "No motion definitions; see Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md#balayage.")
    rows, bad = {}, []
    for sc in scenarios:
        mover = bpy.data.objects.get(sc.get("sweep", ""))
        if mover is None:
            mover = next((o for o in ctx.scope if roblox_name(o) == sc.get("sweep")), None)
        if mover is None or mover not in ctx.scope:
            rows[sc.get("name", "?")] = "mover not in scope"
            continue
        hit, err = _sweep(ctx, mover, sc.get("set", {}), steps)
        if err:
            rows[sc.get("name", "?")] = err
        elif hit:
            rows[sc.get("name", "?")] = hit
            bad.append(mover.name)
        else:
            rows[sc.get("name", "?")] = "clear"
    return make_result(ctx, "MOV003", bool(bad), FAIL, f"{len(scenarios)} motion sweep(s) clear.",
                       "Collision during a motion sweep (first colliding value reported). Fix the pivot, the "
                       "clearance or the motion range — never hide it in animation.", bad,
                       {"scenarios": rows, "steps": steps})


@rule("MOV004", "moving_parts", "Moving parts without motion definition", DOC + "#balayage")
def undefined_motion(ctx: Context):
    bad = [ob.name for ob in meshes(ctx) if role(ob) == "moving" and motion(ctx, ob) is None]
    return make_result(ctx, "MOV004", bool(bad), WARN, "Every 'moving' part has a motion definition.",
                       "Parts tagged eclipse_role='moving' without eclipse_motion_* properties or config entry: "
                       "their sweep cannot be validated.", bad)


# ---------------------------------------------------------------------------
# grip
# ---------------------------------------------------------------------------

def _inside(tree: BVHTree, p: Vector, direction=Vector((0.577, 0.577, 0.577))) -> bool:
    count, origin = 0, p.copy()
    for _ in range(64):
        loc, _n, _i, _d = tree.ray_cast(origin, direction)
        if loc is None:
            break
        count += 1
        origin = loc + direction * 1e-5
    return count % 2 == 1


@rule("GRP001", "grip", "Grip reference frame", DOC_GRIP + "#repere-grip")
def grip_reference(ctx: Context):
    pat = ctx.config.get("markers", {}).get("grip", "(?i)grip")
    marks = [ob for ob in ctx.scope if re.search(pat, ob.name) and ob.type == "EMPTY"]
    if not marks:
        return skip("GRP001", "No grip reference Empty (see the grip standard).")
    g = marks[0]
    fwd = Vector(mu.axis_vector(ctx.config.get("orientation", {}).get("blender_forward", "-Y")))
    up = Vector((0, 0, 1))
    axis = (g.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    angle = math.degrees(math.atan2(axis.dot(fwd), axis.dot(up)))
    amin, amax = ctx.threshold("grip_angle_min_deg", 10.0), ctx.threshold("grip_angle_max_deg", 28.0)
    issues = []
    if not (amin <= angle <= amax):
        issues.append(f"grip axis rake {angle:.1f}° outside [{amin}, {amax}] (top of the grip should lean toward the muzzle)")
    obs = meshes(ctx)
    inside_any = False
    for ob in obs:
        verts, polys = _world_geo(ctx, ob)
        if _inside(_bvh(verts, polys), g.matrix_world.translation):
            inside_any = True
            break
    if not inside_any:
        issues.append("grip reference point is not inside any mesh volume (should sit inside the grip, on its axis)")
    return make_result(ctx, "GRP001", bool(issues), WARN,
                       f"Grip reference '{g.name}': rake {angle:.1f}°, inside the grip volume.",
                       "Grip reference frame issues.", [g.name],
                       {"marker": g.name, "rake_deg": round(angle, 2), "issues": issues})


# ---------------------------------------------------------------------------
# armature (Roblox skinning rules)
# ---------------------------------------------------------------------------

@rule("ARM001", "rig", "Armature / skinning rules (Roblox)", "Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#armatures")
def armature_rules(ctx: Context):
    arms = [ob for ob in ctx.scope if ob.type == "ARMATURE"]
    if not arms:
        return skip("ARM001", "No armature in scope (Motor6D rigs made of separate MeshParts need none).")
    issues: Dict[str, List[str]] = {}
    fail = False
    for arm in arms:
        ii = issues.setdefault(arm.name, [])
        if not (abs(arm.matrix_world.determinant() - 1) < 1e-4 and arm.matrix_world.to_euler().to_quaternion().angle < 1e-4
                and arm.matrix_world.translation.length < 1e-4):
            ii.append("armature object transform is not identity (Roblox: frozen transforms, root at 0,0,0)")
        roots = [b for b in arm.data.bones if b.parent is None]
        for rb in roots:
            if rb.head_local.length > 1e-4:
                ii.append(f"root bone '{rb.name}' head not at origin")
        for pb in arm.pose.bones:
            if pb.rotation_mode == "QUATERNION":
                rot_off = pb.rotation_quaternion.angle > 1e-6
            elif pb.rotation_mode == "AXIS_ANGLE":
                rot_off = abs(pb.rotation_axis_angle[0]) > 1e-6
            else:
                rot_off = any(abs(v) > 1e-6 for v in pb.rotation_euler)
            if pb.location.length > 1e-6 or rot_off or any(abs(v - 1) > 1e-6 for v in pb.scale):
                ii.append(f"pose bone '{pb.name}' not at rest (export in rest pose)")
                break
        root_names = {b.name for b in roots}
        for ob in meshes(ctx):
            if not any(m.type == "ARMATURE" and m.object == arm for m in ob.modifiers):
                continue
            gi = {g.index: g.name for g in ob.vertex_groups}
            over4 = root_w = unweighted = 0
            for v in ob.data.vertices:
                ws = [g for g in v.groups if g.weight > 1e-6 and gi.get(g.group) in arm.data.bones]
                if len(ws) > 4:
                    over4 += 1
                if not ws:
                    unweighted += 1
                if any(gi.get(g.group) in root_names for g in ws):
                    root_w += 1
            if over4:
                fail = True
                ii.append(f"{ob.name}: {over4} vertices with > 4 bone influences [OFFICIEL max 4]")
            if root_w:
                ii.append(f"{ob.name}: {root_w} vertices weighted to the root bone [OFFICIEL: no root influences]")
            if unweighted:
                ii.append(f"{ob.name}: {unweighted} unweighted vertices")
    bad = [k for k, v in issues.items() if v]
    return make_result(ctx, "ARM001", bool(bad), FAIL if fail else WARN, "Armatures follow Roblox skinning rules.",
                       "Armature/skinning issues.", bad, {k: v for k, v in issues.items() if v})
