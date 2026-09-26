"""Transforms, units, orientation and scale rules.

Covers the requested validate_transforms / validate_orientation / validate_scale /
validate_scene scripts. Standard: Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md
"""

from __future__ import annotations

import math
import re

import bpy
from mathutils import Vector

from . import mathutil as mu
from .bpy_helpers import is_identity, meshes, role, snapshot, world_bbox_of
from .core import FAIL, INFO, WARN, Context, info, make_result, rule, skip

DOC = "Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md"


@rule("TRF001", "transforms", "Unapplied scale", DOC + "#politique-transforms")
def unapplied_scale(ctx: Context):
    bad, details = [], {}
    for ob in ctx.scope:
        if ob.type not in {"MESH", "ARMATURE"}:
            continue
        sc = ob.scale
        if any(abs(v - 1.0) > 1e-5 for v in sc):
            bad.append(ob.name)
            details[ob.name] = [round(v, 5) for v in sc]
    return make_result(ctx, "TRF001", bool(bad), WARN, "All mesh/armature scales are (1,1,1).",
                       "Unapplied object scale: bevel/solidify widths, texel density and Roblox sizes stop matching "
                       "what you measure. Apply scale (on a versioned copy) before rigging/export.", bad, details)


@rule("TRF002", "transforms", "Negative scale (mirrored transform)", DOC + "#politique-transforms")
def negative_scale(ctx: Context):
    bad = [ob.name for ob in ctx.scope if ob.type in {"MESH", "EMPTY", "ARMATURE"}
           and ob.matrix_world.to_3x3().determinant() < 0]
    return make_result(ctx, "TRF002", bool(bad), FAIL, "No negative scale.",
                       "Negative scale flips winding/normals and breaks the exported orientation.", bad)


@rule("TRF003", "transforms", "Non-zero rotation on parts", DOC + "#politique-transforms")
def rotation(ctx: Context):
    bad, details = [], {}
    for ob in ctx.scope:
        if ob.type != "MESH" or role(ob) in {"moving", "reference"} or ob.get("eclipse_allow_rotation"):
            continue
        rot = ob.rotation_euler if ob.rotation_mode not in {"QUATERNION", "AXIS_ANGLE"} else ob.matrix_basis.to_euler()
        if any(abs(v) > 1e-5 for v in rot):
            bad.append(ob.name)
            details[ob.name] = [round(math.degrees(v), 3) for v in rot]
    return make_result(ctx, "TRF003", bool(bad), WARN, "Static parts have zero rotation.",
                       "Rotated static parts: the rotation travels into Roblox as part orientation/pivot and "
                       "confuses Motor6D setup. Apply rotation, or tag moving parts with eclipse_role='moving' "
                       "when the local axes intentionally match a hinge.", bad, details)


@rule("TRF004", "transforms", "Delta transforms", DOC + "#politique-transforms")
def delta(ctx: Context):
    bad = []
    for ob in ctx.scope:
        if (any(abs(v) > 1e-6 for v in ob.delta_location) or any(abs(v) > 1e-6 for v in ob.delta_rotation_euler)
                or any(abs(v - 1) > 1e-6 for v in ob.delta_scale)):
            bad.append(ob.name)
    return make_result(ctx, "TRF004", bool(bad), FAIL, "No delta transforms.",
                       "Delta transforms are hidden offsets: remove them.", bad)


@rule("TRF005", "transforms", "Parent inverse matrices", DOC + "#politique-transforms")
def parent_inverse(ctx: Context):
    bad = [ob.name for ob in ctx.scope if ob.parent is not None and not is_identity(ob.matrix_parent_inverse)]
    if not bad:
        return make_result(ctx, "TRF005", False, INFO, "Parent inverse matrices are identity.", "", [])
    return info("TRF005", "Children with a non-identity parent inverse: their visible transform differs from "
                "their stored local values. Harmless for FBX but confusing when setting pivots by numbers "
                "(use 'Clear Parent Inverse' on a copy if you rely on local values).", objects=bad)


@rule("TRF006", "scene", "Scene units (1 BU = 1 stud)", DOC + "#echelle")
def units(ctx: Context):
    us = bpy.context.scene.unit_settings
    details = {"system": us.system, "scale_length": us.scale_length}
    bad = us.system != "NONE" and abs(us.scale_length - 1.0) > 1e-6
    res = make_result(ctx, "TRF006", bad, FAIL, "Unit scale is neutral (1 BU exported as 1 stud).",
                      "Scene Unit Scale ≠ 1: depending on FBX 'Apply Scalings' it multiplies either the object "
                      "transforms or the file UnitScaleFactor (verified in the 5.0 exporter source) — sizes in Roblox "
                      "become ambiguous. ECLIPSE convention: 1 Blender unit = 1 stud (Unit Scale 1).", [], details)
    if not bad and us.system != "NONE":
        res.status = INFO
        res.message = ("Unit system is not 'None' (Roblox docs recommend None). Harmless with Unit Scale 1 "
                       "(the FBX factor is identical), but lengths display in metres — read them as studs.")
    return res


@rule("TRF007", "transforms", "Asset root at world origin", DOC + "#origine")
def root_origin(ctx: Context):
    roots = [ob for ob in ctx.scope if ob.parent is None and ob.type in {"MESH", "EMPTY", "ARMATURE"}]
    if not roots:
        return skip("TRF007", "No root objects in scope.")
    lo, hi = world_bbox_of([o for o in ctx.scope if o.type == "MESH"])
    size = (hi - lo).length or 1.0
    far = [ob.name for ob in roots if ob.matrix_world.translation.length > 0.5 * size]
    return make_result(ctx, "TRF007", bool(far), WARN, "Root objects sit near the world origin.",
                       "Root objects far from the world origin: with 'Set Pivot to Scene Origin' the Roblox model "
                       "pivot ends up away from the weapon.", far,
                       {"asset_size": round(size, 4)})


def _forward_marker(ctx: Context):
    pat = ctx.config.get("markers", {}).get("muzzle", "(?i)muzzle")
    for ob in ctx.scope:
        if re.search(pat, ob.name):
            return ob
    return None


@rule("ORI001", "orientation", "Weapon forward axis", DOC + "#table-de-verite-des-axes")
def forward_axis(ctx: Context):
    fwd = mu.axis_vector(ctx.config.get("orientation", {}).get("blender_forward", "-Y"))
    fwd_v = Vector(fwd)
    mesh_obs = meshes(ctx)
    if not mesh_obs:
        return skip("ORI001", "No meshes in scope.")
    lo, hi = world_bbox_of(mesh_obs)
    center = (lo + hi) * 0.5
    dims = hi - lo
    marker = _forward_marker(ctx)
    details = {"expected_forward": ctx.config.get("orientation", {}).get("blender_forward", "-Y"),
               "bbox_dimensions": [round(v, 4) for v in dims]}
    if marker is not None:
        rel = marker.matrix_world.translation - center
        along = rel.dot(fwd_v)
        details["muzzle_marker"] = marker.name
        details["muzzle_offset_along_forward"] = round(along, 4)
        bad = along <= 0
        return make_result(ctx, "ORI001", bad, WARN, f"Muzzle marker '{marker.name}' is on the forward side.",
                           "The muzzle marker is behind the asset centre along the configured forward axis: "
                           "the weapon points the wrong way (or orientation.blender_forward is wrong).",
                           [marker.name], details)
    axis_idx = [abs(c) for c in fwd].index(1.0)
    longest = max(range(3), key=lambda i: dims[i])
    details["heuristic"] = "no muzzle marker: longest bbox axis should be the forward axis"
    bad = longest != axis_idx
    res = make_result(ctx, "ORI001", bad, WARN, "Longest dimension is along the forward axis (heuristic).",
                      "Longest dimension is not along the configured forward axis. Add a 'Muzzle' empty to make "
                      "this check exact.", [], details)
    if not bad:
        res.status = INFO
        res.message += " Direction (+/-) cannot be verified without a Muzzle marker."
    return res


@rule("SCL001", "scale", "Overall dimensions sanity", DOC + "#echelle")
def dimensions(ctx: Context):
    rng = ctx.threshold("dimensions_range", [0.2, 8.0])
    mesh_obs = meshes(ctx)
    if not mesh_obs:
        return skip("SCL001", "No meshes in scope.")
    lo, hi = world_bbox_of(mesh_obs)
    longest = max(hi - lo)
    details = {"longest_dimension_studs": round(longest, 4), "expected_range": rng,
               "real_world_cm_if_1stud_28cm": round(longest * mu.STUD_IN_CM, 1)}
    bad = not (rng[0] <= longest <= rng[1])
    res = make_result(ctx, "SCL001", bad, WARN, f"Asset length {longest:.3f} studs within the expected range.",
                      "Asset size outside the expected range: wrong unit scale or wrong export factor (×100).",
                      [], details)
    if not bad:
        res.status = INFO
        res.details = details
    return res
