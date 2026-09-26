"""Export-readiness and Viewmodel/Worldmodel comparison rules.

Covers the requested validate_export_readiness / validate_viewmodel_worldmodel scripts.
Standards: Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md,
           Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md
"""

from __future__ import annotations

import re

import bpy

from .bpy_helpers import (EXPORTABLE_TYPES, boolean_operands, cutters_in_scope, meshes, roblox_name,
                          snapshot, world_bbox_of)
from .core import FAIL, INFO, WARN, Context, info, make_result, rule, skip

DOC = "Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md"
DOC_VMWM = "Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md"


@rule("EXP001", "export", "File saved and clean", DOC + "#source-vs-export")
def saved(ctx: Context):
    path = bpy.data.filepath
    # is_dirty is meaningless in background mode (always True without a window manager)
    dirty = bpy.data.is_dirty and not bpy.app.background
    bad = (not path) or dirty
    return make_result(ctx, "EXP001", bad, WARN, "File saved with no pending changes.",
                       "Unsaved file or unsaved changes: the report would not describe a reproducible state. "
                       "Save a new version before exporting.", [], {"path": path, "dirty": dirty})


@rule("EXP002", "export", "Boolean cutters would be exported", DOC + "#cutters")
def cutters(ctx: Context):
    bad = []
    for ob in cutters_in_scope(ctx):
        try:
            visible = ob.visible_get()
        except RuntimeError:  # not in the active view layer
            visible = False
        if visible or not ob.hide_render:
            bad.append(ob.name)
    ops = ctx.cache.setdefault("bool_operands", boolean_operands())
    return make_result(ctx, "EXP002", bool(bad), FAIL, "No boolean cutter inside the export scope.",
                       "Boolean operand objects are inside the export scope: the FBX exporter writes them as extra "
                       "MeshParts. Move cutters to an excluded collection (e.g. 'ECLIPSE1_VM_Cutters').",
                       bad, {"operands": {k: v for k, v in ops.items() if k in bad}})


@rule("EXP003", "export", "Non-exportable object types in scope", DOC + "#preset-fbx")
def object_types(ctx: Context):
    bad = {ob.name: ob.type for ob in ctx.scope if ob.type not in EXPORTABLE_TYPES}
    return make_result(ctx, "EXP003", bool(bad), WARN, "Only meshes, empties and armatures in scope.",
                       "Cameras/lights/curves/text in scope: convert curves/text to meshes in the export copy and "
                       "exclude the rest.", list(bad), {"types": bad})


@rule("EXP004", "export", "Hidden objects inside the export scope", DOC + "#preset-fbx")
def hidden(ctx: Context):
    def _hidden(ob):
        try:
            return ob.hide_get() or ob.hide_viewport
        except RuntimeError:  # object not in the active view layer
            return True
    bad = [ob.name for ob in ctx.scope if _hidden(ob)]
    return make_result(ctx, "EXP004", bool(bad), WARN, "No hidden object in scope.",
                       "Hidden objects in scope: the FBX exporter ignores viewport visibility unless 'Visible Objects' "
                       "is ticked, so hidden helpers leak into Roblox. Exclude them explicitly.", bad)


@rule("EXP005", "export", "Roblox names valid and unique", DOC + "#noms-roblox")
def roblox_names(ctx: Context):
    valid = ctx.config.get("naming", {}).get("roblox_name_valid", r"^[A-Za-z][A-Za-z0-9_]*$")
    names = {}
    invalid = []
    for ob in ctx.scope:
        if ob.type not in {"MESH", "EMPTY"}:
            continue
        n = roblox_name(ob) or ob.name
        names.setdefault(n, []).append(ob.name)
        if not re.match(valid, n):
            invalid.append(ob.name)
    dups = {n: obs for n, obs in names.items() if len(obs) > 1}
    bad = invalid + [o for obs in dups.values() for o in obs]
    res = make_result(ctx, "EXP005", bool(bad), WARN, "Roblox-facing names are valid and unique.",
                      "Invalid or duplicated Roblox-facing names (roblox_name custom property, else object name). "
                      "Motor6D, animations and scripts address parts BY NAME.", bad,
                      {"invalid": invalid, "duplicates": dups})
    if dups:
        res.status = ctx.severity("EXP005", FAIL)
    return res


@rule("EXP006", "export", "Modifier stack summary", DOC + "#source-vs-export")
def modifiers(ctx: Context):
    rows = {ob.name: [f"{m.type}:{m.name}" for m in ob.modifiers] for ob in meshes(ctx) if len(ob.modifiers)}
    if not rows:
        return make_result(ctx, "EXP006", False, INFO, "No live modifiers (destructive or export copy).", "", [])
    msg = ("Live modifiers are applied by the FBX exporter (use_mesh_modifiers). In a SOURCE file this is expected; "
           "in an EXPORT copy prefer applying them so the file is exactly what Roblox receives.")
    return info("EXP006", msg, {"modifiers": rows}, list(rows))


@rule("EXP007", "export", "Source vs export file naming", DOC + "#source-vs-export")
def file_kind(ctx: Context):
    pat = ctx.config.get("naming", {}).get("export_file_pattern", r"(?i)_export(_v\d+)?\.blend$")
    path = bpy.data.filepath or ""
    is_export_file = bool(re.search(pat, path))
    if ctx.stage == "export" and path and not is_export_file:
        return make_result(ctx, "EXP007", True, WARN, "", "Stage 'export' on a file that is not named as an export "
                           "copy: never apply destructive export steps to the SOURCE file.", [], {"path": path})
    if ctx.stage != "export" and is_export_file:
        return info("EXP007", "Export copy validated with a non-export stage.", {"path": path})
    return make_result(ctx, "EXP007", False, INFO, "File kind consistent with the stage.", "", [])


@rule("EXP008", "export", "Hierarchy and root", DOC + "#hierarchie")
def hierarchy(ctx: Context):
    roots = [ob.name for ob in ctx.scope if ob.parent is None]
    orphans = [ob.name for ob in ctx.scope if ob.parent is not None and ob.parent not in ctx.scope]
    if orphans:
        return make_result(ctx, "EXP008", True, WARN, "", "Objects parented to something outside the scope: their "
                           "exported transform includes an invisible parent.", orphans, {"roots": roots})
    return info("EXP008", f"{len(roots)} root object(s) in scope.", {"roots": roots})


@rule("EXP009", "export", "roblox_name contract", DOC + "#noms-roblox")
def roblox_name_contract(ctx: Context):
    missing = [ob.name for ob in meshes(ctx) if not roblox_name(ob)]
    return make_result(ctx, "EXP009", bool(missing), INFO, "Every mesh declares its roblox_name.",
                       "Meshes without the roblox_name custom property: the Blender object name will be used as the "
                       "MeshPart name. Declare it when Blender names are prefixed (VM_/WM_) to keep Roblox names stable.",
                       missing)


# ---------------------------------------------------------------------------
# Viewmodel vs Worldmodel
# ---------------------------------------------------------------------------

def _collect(pattern: str):
    obs = []
    for coll in bpy.data.collections:
        if re.search(pattern, coll.name):
            obs.extend(o for o in coll.all_objects if o.type == "MESH")
    return list({o.name: o for o in obs}.values())


@rule("VMWM001", "viewmodel_worldmodel", "Worldmodel cheaper than Viewmodel", DOC_VMWM + "#comparaison")
def vm_wm_budget(ctx: Context):
    sc = ctx.config.get("scope", {})
    vm = _collect(sc.get("vm_collection_pattern", "(?i)(^|_)(vm|viewmodel)($|_)"))
    wm = _collect(sc.get("wm_collection_pattern", "(?i)(^|_)(wm|worldmodel)($|_)"))
    if not vm or not wm:
        return skip("VMWM001", "Needs both VM and WM collections in the file.")
    tv = sum(snapshot(ctx, o).tri_count for o in vm)
    tw = sum(snapshot(ctx, o).tri_count for o in wm)
    ratio = tw / max(1, tv)
    mats_v = {s.material.name for o in vm for s in o.material_slots if s.material}
    mats_w = {s.material.name for o in wm for s in o.material_slots if s.material}
    lo_v, hi_v = world_bbox_of(vm)
    lo_w, hi_w = world_bbox_of(wm)
    dv, dw = hi_v - lo_v, hi_w - lo_w
    dim_dev = max(abs(dv[i] - dw[i]) / max(1e-6, dv[i]) for i in range(3))
    issues = []
    if ratio > 0.4:
        issues.append(f"WM/VM triangle ratio {ratio:.2f} > 0.40")
    if len(mats_w) > len(mats_v):
        issues.append("WM uses more materials than VM")
    if dim_dev > 0.03:
        issues.append(f"bounding boxes differ by {dim_dev:.1%} (silhouette/scale not preserved?)")
    if len(wm) > len(vm):
        issues.append("WM has more MeshParts than VM")
    return make_result(ctx, "VMWM001", bool(issues), WARN, f"WM {tw} tris vs VM {tv} ({ratio:.0%}), same envelope.",
                       "Viewmodel/Worldmodel relationship issues.", [],
                       {"vm_tris": tv, "wm_tris": tw, "ratio": round(ratio, 3), "vm_parts": len(vm),
                        "wm_parts": len(wm), "vm_materials": sorted(mats_v), "wm_materials": sorted(mats_w),
                        "bbox_max_relative_diff": round(dim_dev, 4), "issues": issues})
