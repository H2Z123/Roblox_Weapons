"""Asset inventory: the factual BEFORE/AFTER snapshot attached to every report."""

from __future__ import annotations

import math
from typing import Any, Dict

import bpy

from .bpy_helpers import meshes, roblox_name, snapshot
from .core import Context

MOD_KEYS = {
    "BEVEL": ("width", "segments", "limit_method", "offset_type", "harden_normals", "profile"),
    "WEIGHTED_NORMAL": ("mode", "weight", "keep_sharp", "use_face_influence"),
    "BOOLEAN": ("operation", "solver"),
    "TRIANGULATE": ("quad_method", "ngon_method", "keep_custom_normals"),
    "MIRROR": ("use_axis",),
    "SUBSURF": ("levels", "render_levels"),
    "ARMATURE": (),
}


def _mod_info(m) -> Dict[str, Any]:
    d = {"type": m.type, "name": m.name, "viewport": m.show_viewport, "render": m.show_render}
    for k in MOD_KEYS.get(m.type, ()):
        v = getattr(m, k, None)
        if hasattr(v, "__len__") and not isinstance(v, str):
            v = list(v)
        d[k] = v
    if m.type == "BOOLEAN":
        d["operand"] = m.object.name if getattr(m, "object", None) else (m.collection.name if getattr(m, "collection", None) else None)
    return d


def build_inventory(ctx: Context) -> Dict[str, Any]:
    objs = []
    total = 0
    mats = set()
    for ob in ctx.scope:
        row: Dict[str, Any] = {
            "name": ob.name, "type": ob.type, "roblox_name": roblox_name(ob),
            "parent": ob.parent.name if ob.parent else None,
            "collections": [c.name for c in ob.users_collection],
            "location": [round(v, 5) for v in ob.matrix_world.translation],
            "rotation_deg": [round(math.degrees(v), 3) for v in ob.matrix_world.to_euler()],
            "scale": [round(v, 5) for v in ob.scale],
            "custom_props": {k: (str(ob[k]) if not isinstance(ob[k], (int, float, str, bool)) else ob[k])
                             for k in ob.keys() if k.startswith("eclipse_") or k == "roblox_name"},
        }
        if ob.type == "MESH":
            s = snapshot(ctx, ob)
            total += s.tri_count
            row.update({
                "tris": s.tri_count,
                "base_tris": sum(max(0, len(p.vertices) - 2) for p in ob.data.polygons),
                "verts": len(s.verts),
                "dimensions": [round(v, 5) for v in s.dimensions()],
                "surface_area": round(s.total_area(), 6),
                "materials": [m for m in s.material_names if m],
                "uv_maps": s.uv_names,
                "smooth_pct": round(100.0 * sum(s.poly_smooth) / max(1, len(s.polys)), 1),
                "custom_normals": s.has_custom_normals,
                "modifiers": [_mod_info(m) for m in ob.modifiers],
            })
            mats.update(m for m in s.material_names if m)
        objs.append(row)
    return {
        "objects": objs,
        "total_tris": total,
        "mesh_count": len(meshes(ctx)),
        "material_count": len(mats),
        "excluded_objects": ctx.cache.get("excluded", []),
        "scene_units": {"system": bpy.context.scene.unit_settings.system,
                        "scale_length": bpy.context.scene.unit_settings.scale_length},
        "collections": [c.name for c in bpy.data.collections],
    }
