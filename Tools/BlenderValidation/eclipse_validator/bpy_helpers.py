"""Blender-side helpers: scope resolution and evaluated-mesh snapshots.

Targets Blender 4.2 LTS → 5.x (tested on bpy 5.0.1). Falls back to the
pre-4.1 normals API when ``Mesh.corner_normals`` is missing.

Rules read *evaluated* meshes (modifiers applied) because that is what the
FBX exporter writes with its default ``use_mesh_modifiers=True``.
"""

from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Tuple

import bpy  # noqa: F401  (imported for side effects in Blender)
import bmesh  # noqa: F401
from mathutils import Matrix, Vector

from .core import Context

EXPORTABLE_TYPES = {"MESH", "EMPTY", "ARMATURE"}


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------

def _collection_excluded(coll_name: str, patterns: List[str]) -> bool:
    return any(re.search(p, coll_name) for p in patterns)


def boolean_operands() -> Dict[str, List[str]]:
    """Map operand object name -> list of objects using it in a Boolean modifier."""
    out: Dict[str, List[str]] = {}
    for ob in bpy.data.objects:
        for md in getattr(ob, "modifiers", []):
            if md.type != "BOOLEAN":
                continue
            ops = []
            if getattr(md, "operand_type", "OBJECT") == "COLLECTION" and md.collection:
                ops = list(md.collection.all_objects)
            elif md.object:
                ops = [md.object]
            for op in ops:
                out.setdefault(op.name, []).append(ob.name)
    return out


def resolve_scope(ctx: Context) -> List["bpy.types.Object"]:
    """Objects to validate, according to --collection / --objects options.

    Objects living only in excluded collections (cutters, WIP, refs...) are
    removed from the scope but remembered in ``ctx.cache['excluded']``.
    """
    opts = ctx.options
    patterns = ctx.config.get("scope", {}).get("exclude_collection_patterns", [])
    if opts.get("objects"):
        objs = [bpy.data.objects[n] for n in opts["objects"] if n in bpy.data.objects]
        desc = "objects: " + ", ".join(opts["objects"])
    elif opts.get("collection"):
        coll = bpy.data.collections.get(opts["collection"])
        if coll is None:
            raise ValueError(f"Collection '{opts['collection']}' not found")
        objs = list(coll.all_objects)
        desc = f"collection '{coll.name}' (recursive)"
    else:
        objs = list(bpy.context.scene.objects)
        desc = "whole scene"

    kept, excluded = [], []
    for ob in objs:
        colls = [c.name for c in ob.users_collection]
        if colls and all(_collection_excluded(c, patterns) for c in colls):
            excluded.append(ob.name)
        else:
            kept.append(ob)
    ctx.cache["excluded"] = excluded
    ctx.cache["scope_description"] = desc + (f" — {len(excluded)} excluded" if excluded else "")
    return kept


def meshes(ctx: Context) -> List["bpy.types.Object"]:
    """Mesh objects in scope that are not boolean cutters."""
    ops = ctx.cache.setdefault("bool_operands", boolean_operands())
    return [o for o in ctx.scope if o.type == "MESH" and o.name not in ops]


def cutters_in_scope(ctx: Context) -> List["bpy.types.Object"]:
    ops = ctx.cache.setdefault("bool_operands", boolean_operands())
    return [o for o in ctx.scope if o.name in ops]


def roblox_name(ob) -> str:
    return str(ob.get("roblox_name", "") or "")


def role(ob) -> str:
    return str(ob.get("eclipse_role", "") or "")


# ---------------------------------------------------------------------------
# Mesh snapshot
# ---------------------------------------------------------------------------

class MeshSnapshot:
    """Plain-Python copy of an evaluated mesh in WORLD space."""

    def __init__(self, ob):
        self.name = ob.name
        self.matrix_world = ob.matrix_world.copy()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        try:
            self._read(me)
        finally:
            ev.to_mesh_clear()

    def _read(self, me):
        mw = self.matrix_world
        nmat = mw.to_3x3().inverted_safe().transposed()
        self.verts_local = [v.co.copy() for v in me.vertices]
        self.verts = [mw @ v for v in self.verts_local]
        self.loop_verts = [l.vertex_index for l in me.loops]
        self.polys: List[Tuple[int, ...]] = []
        self.poly_loops: List[Tuple[int, ...]] = []
        self.poly_smooth: List[bool] = []
        self.poly_mat: List[int] = []
        for p in me.polygons:
            self.polys.append(tuple(p.vertices))
            self.poly_loops.append(tuple(range(p.loop_start, p.loop_start + p.loop_total)))
            self.poly_smooth.append(bool(p.use_smooth))
            self.poly_mat.append(p.material_index)
        # world-space face data
        self.face_normals: List[Vector] = []
        self.face_areas: List[float] = []
        self.face_centers: List[Vector] = []
        for poly in self.polys:
            n, a, c = _poly_normal_area_center([self.verts[i] for i in poly])
            self.face_normals.append(n)
            self.face_areas.append(a)
            self.face_centers.append(c)
        # corner normals (world)
        self.corner_normals = [(nmat @ n).normalized() for n in _corner_normals(me)]
        self.has_custom_normals = bool(getattr(me, "has_custom_normals", False))
        # triangles
        me.calc_loop_triangles()
        self.tris = [(tuple(t.vertices), t.polygon_index) for t in me.loop_triangles]
        # edges
        self.edges = [tuple(e.vertices) for e in me.edges]
        self.edge_sharp = _edge_sharp_flags(me)
        self.edge_seam = [bool(e.use_seam) for e in me.edges]
        # UVs
        self.uv_names = [uv.name for uv in me.uv_layers]
        active = me.uv_layers.active
        if active is not None:
            data = active.data
            self.uv = [tuple(data[i].uv) for i in range(len(me.loops))]
        else:
            self.uv = []
        self.material_names = [m.name if m else "" for m in me.materials]

    # -- derived helpers -------------------------------------------------
    @property
    def tri_count(self) -> int:
        return len(self.tris)

    def bbox(self) -> Tuple[Vector, Vector]:
        if not self.verts:
            return Vector((0, 0, 0)), Vector((0, 0, 0))
        xs = [v.x for v in self.verts]
        ys = [v.y for v in self.verts]
        zs = [v.z for v in self.verts]
        return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))

    def dimensions(self) -> Vector:
        lo, hi = self.bbox()
        return hi - lo

    def total_area(self) -> float:
        return sum(self.face_areas)


def _poly_normal_area_center(pts):
    # Newell's method: robust for n-gons, gives area * 2 as length
    nx = ny = nz = 0.0
    n = len(pts)
    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]
        nx += (a.y - b.y) * (a.z + b.z)
        ny += (a.z - b.z) * (a.x + b.x)
        nz += (a.x - b.x) * (a.y + b.y)
    normal = Vector((nx, ny, nz))
    area = normal.length * 0.5
    if normal.length > 0:
        normal.normalize()
    center = Vector((0, 0, 0))
    for p in pts:
        center += p
    center /= max(1, n)
    return normal, area, center


def _corner_normals(me) -> List[Vector]:
    if hasattr(me, "corner_normals"):
        return [Vector(cn.vector) for cn in me.corner_normals]
    me.calc_normals_split()  # Blender < 4.1
    return [Vector(l.normal) for l in me.loops]


def _edge_sharp_flags(me) -> List[bool]:
    attr = me.attributes.get("sharp_edge") if hasattr(me, "attributes") else None
    if attr is not None and attr.domain == "EDGE":
        return [bool(d.value) for d in attr.data]
    return [bool(getattr(e, "use_edge_sharp", False)) for e in me.edges]


def snapshot(ctx: Context, ob) -> MeshSnapshot:
    key = "snap::" + ob.name
    if key not in ctx.cache:
        ctx.cache[key] = MeshSnapshot(ob)
    return ctx.cache[key]


# ---------------------------------------------------------------------------
# Topology helpers on snapshots
# ---------------------------------------------------------------------------

def edge_face_map(snap: MeshSnapshot) -> Dict[Tuple[int, int], List[Tuple[int, int, int]]]:
    """edge key (min,max) -> list of (poly index, directed a, directed b)."""
    out: Dict[Tuple[int, int], List[Tuple[int, int, int]]] = {}
    for pi, poly in enumerate(snap.polys):
        n = len(poly)
        for k in range(n):
            a, b = poly[k], poly[(k + 1) % n]
            out.setdefault((min(a, b), max(a, b)), []).append((pi, a, b))
    return out


def face_components(snap: MeshSnapshot) -> List[List[int]]:
    """Connected components of faces sharing an edge."""
    efm = edge_face_map(snap)
    parent = list(range(len(snap.polys)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for users in efm.values():
        for i in range(1, len(users)):
            ra, rb = find(users[0][0]), find(users[i][0])
            if ra != rb:
                parent[ra] = rb
    comps: Dict[int, List[int]] = {}
    for i in range(len(snap.polys)):
        comps.setdefault(find(i), []).append(i)
    return list(comps.values())


def uv_islands(snap: MeshSnapshot, eps: float = 1e-6) -> List[List[int]]:
    """Faces grouped into UV islands (faces sharing an edge with identical UVs)."""
    if not snap.uv:
        return []
    parent = list(range(len(snap.polys)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    edge_uv: Dict[Tuple[int, int], List[Tuple[int, tuple, tuple]]] = {}
    for pi, loops in enumerate(snap.poly_loops):
        n = len(loops)
        for k in range(n):
            la, lb = loops[k], loops[(k + 1) % n]
            va, vb = snap.loop_verts[la], snap.loop_verts[lb]
            ua, ub = snap.uv[la], snap.uv[lb]
            if va > vb:
                va, vb, ua, ub = vb, va, ub, ua
            edge_uv.setdefault((va, vb), []).append((pi, ua, ub))
    for users in edge_uv.values():
        if len(users) < 2:
            continue
        p0, a0, b0 = users[0]
        for pi, a, b in users[1:]:
            if (abs(a[0] - a0[0]) < eps and abs(a[1] - a0[1]) < eps and
                    abs(b[0] - b0[0]) < eps and abs(b[1] - b0[1]) < eps):
                ra, rb = find(p0), find(pi)
                if ra != rb:
                    parent[ra] = rb
    groups: Dict[int, List[int]] = {}
    for i in range(len(snap.polys)):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def uv_poly_area(snap: MeshSnapshot, pi: int) -> float:
    """Signed UV area of polygon ``pi`` (shoelace)."""
    loops = snap.poly_loops[pi]
    s = 0.0
    n = len(loops)
    for k in range(n):
        u0, v0 = snap.uv[loops[k]]
        u1, v1 = snap.uv[loops[(k + 1) % n]]
        s += u0 * v1 - u1 * v0
    return 0.5 * s


def world_bbox_of(obs) -> Tuple[Vector, Vector]:
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for ob in obs:
        for corner in ob.bound_box:
            w = ob.matrix_world @ Vector(corner)
            lo = Vector((min(lo[i], w[i]) for i in range(3)))
            hi = Vector((max(hi[i], w[i]) for i in range(3)))
    if lo.x == math.inf:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    return lo, hi


def descendants(ob) -> List["bpy.types.Object"]:
    out = []
    stack = list(ob.children)
    while stack:
        c = stack.pop()
        out.append(c)
        stack.extend(c.children)
    return out


def is_identity(m: Matrix, eps: float = 1e-6) -> bool:
    ident = Matrix.Identity(4)
    return all(abs(m[i][j] - ident[i][j]) < eps for i in range(4) for j in range(4))


def material_images(mat) -> List[Tuple["bpy.types.Image", str, "bpy.types.Node"]]:
    """(image, usage, node) for image textures feeding a Principled BSDF.

    usage ∈ {base_color, normal, roughness, metallic, emission, alpha, other}.
    """
    out = []
    if not mat or not mat.node_tree or not getattr(mat, "use_nodes", True):
        return out
    nt = mat.node_tree
    for node in nt.nodes:
        if node.type != "TEX_IMAGE" or node.image is None:
            continue
        usage = _trace_usage(node)
        out.append((node.image, usage, node))
    return out


def _trace_usage(node, depth: int = 0) -> str:
    if depth > 6:
        return "other"
    for out_sock in node.outputs:
        for link in out_sock.links:
            to_node, to_sock = link.to_node, link.to_socket
            name = to_sock.name.lower()
            if to_node.type == "BSDF_PRINCIPLED":
                if name.startswith("base color"):
                    return "base_color"
                if name == "roughness":
                    return "roughness"
                if name == "metallic":
                    return "metallic"
                if name.startswith("emission"):
                    return "emission"
                if name == "alpha":
                    return "alpha"
                if name == "normal":
                    return "normal"
            if to_node.type == "NORMAL_MAP":
                return "normal"
            if to_node.type in {"SEPRGB", "SEPARATE_COLOR", "SEPXYZ", "MATH", "MIX", "MIX_RGB",
                                "INVERT", "VALTORGB", "GAMMA", "BRIGHTCONTRAST", "HUE_SAT", "CURVE_RGB",
                                "BUMP", "REROUTE"}:
                u = _trace_usage(to_node, depth + 1)
                if u != "other":
                    return u
    return "other"


def principled_nodes(mat):
    if not mat or not mat.node_tree or not getattr(mat, "use_nodes", True):
        return []
    return [n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
