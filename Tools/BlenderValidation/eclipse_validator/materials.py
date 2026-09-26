"""Material, texture and PBR-value rules.

Covers the requested validate_materials script.
Standard: Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md
"""

from __future__ import annotations

import os

import bpy

from . import mathutil as mu
from .bpy_helpers import material_images, meshes, principled_nodes, snapshot
from .core import FAIL, INFO, WARN, Context, info, make_result, rule

DOC = "Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md"
NON_COLOR_USAGES = {"normal", "roughness", "metallic", "alpha"}


def _scope_materials(ctx: Context):
    mats = {}
    for ob in meshes(ctx):
        for slot in ob.material_slots:
            if slot.material:
                mats.setdefault(slot.material.name, (slot.material, []))[1].append(ob.name)
    return mats


@rule("MAT001", "materials", "One material per mesh object", DOC + "#materiaux-roblox")
def one_material(ctx: Context):
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        used = sorted(set(s.poly_mat))
        if len(used) > 1:
            bad.append(ob.name)
            details[ob.name] = {"material_indices_used": used,
                                "materials": [s.material_names[i] if i < len(s.material_names) else "?" for i in used]}
    return make_result(ctx, "MAT001", bool(bad), WARN, "Each mesh uses a single material.",
                       "Mesh objects using several materials: Roblox supports one material/SurfaceAppearance per "
                       "MeshPart [OFFICIEL]. Split into parts deliberately, or merge into one texture set.", bad, details)


@rule("MAT002", "materials", "Missing / empty material slots", DOC + "#materiaux-roblox")
def empty_slots(ctx: Context):
    bad, details = [], {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        used = set(s.poly_mat)
        empty_used = [i for i in used if i >= len(ob.material_slots) or ob.material_slots[i].material is None]
        if not ob.material_slots or empty_used:
            bad.append(ob.name)
            details[ob.name] = {"slots": len(ob.material_slots), "faces_on_empty_slot_indices": empty_used}
    return make_result(ctx, "MAT002", bool(bad), WARN, "Every face has a material.",
                       "Faces without material: Roblox imports them untextured.", bad, details)


@rule("MAT003", "materials", "Unused material slots", DOC + "#materiaux-roblox")
def unused_slots(ctx: Context):
    rows = {}
    for ob in meshes(ctx):
        s = snapshot(ctx, ob)
        used = set(s.poly_mat)
        unused = [ob.material_slots[i].name for i in range(len(ob.material_slots)) if i not in used]
        if unused:
            rows[ob.name] = unused
    if not rows:
        return make_result(ctx, "MAT003", False, INFO, "No unused slots.", "", [])
    return info("MAT003", "Unused material slots (clean in the export copy).", {"unused": rows}, list(rows))


@rule("MAT004", "materials", "Texture files and resolutions", DOC + "#resolution")
def textures(ctx: Context):
    hard = ctx.threshold("texture_max_resolution_hard", 4096)
    soft = ctx.threshold("max_texture_resolution", 2048)
    fails, warns, details = [], [], {}
    for name, (mat, users) in _scope_materials(ctx).items():
        for img, usage, _node in material_images(mat):
            w, h = img.size[0], img.size[1]
            entry = {"material": name, "usage": usage, "size": [w, h]}
            path = bpy.path.abspath(img.filepath) if img.filepath else ""
            missing = (not img.packed_file) and (not path or not os.path.exists(path)) and img.source == "FILE"
            if missing:
                entry["problem"] = "file missing"
                fails.extend(users)
            elif max(w, h) > hard:
                entry["problem"] = f"> {hard}px (Roblox max) [OFFICIEL]"
                fails.extend(users)
            elif max(w, h) > soft:
                entry["problem"] = f"> profile budget {soft}px"
                warns.extend(users)
            elif w and h and (w & (w - 1) or h & (h - 1)):
                entry["problem"] = "not power of two"
                warns.extend(users)
            if "problem" in entry:
                details[img.name] = entry
    status_fail = bool(fails)
    res = make_result(ctx, "MAT004", bool(fails or warns), FAIL if status_fail else WARN,
                      "Texture files present, within budget, power of two.",
                      "Texture issues found.", fails + warns, details)
    return res


@rule("MAT005", "materials", "Texture color spaces", DOC + "#espaces-couleur")
def color_spaces(ctx: Context):
    bad, details = [], {}
    for name, (mat, users) in _scope_materials(ctx).items():
        for img, usage, _node in material_images(mat):
            cs = img.colorspace_settings.name
            wrong = (usage in NON_COLOR_USAGES and cs not in {"Non-Color", "Linear Rec.709", "Raw", "Utility - Raw"}) or \
                    (usage == "base_color" and cs in {"Non-Color", "Raw"})
            if wrong:
                bad.extend(users)
                details[img.name] = {"usage": usage, "colorspace": cs}
    return make_result(ctx, "MAT005", bool(bad), WARN, "Color spaces match map usage.",
                       "Data maps (normal/roughness/metalness) must be Non-Color; base color must be sRGB. "
                       "Wrong spaces bake/preview wrong values.", bad, details)


@rule("MAT006", "materials", "Normal map node space", DOC + "#normal-maps")
def normal_map_space(ctx: Context):
    bad, details, seen = [], {}, 0
    for name, (mat, users) in _scope_materials(ctx).items():
        if not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "NORMAL_MAP":
                seen += 1
                if node.space != "TANGENT":
                    bad.extend(users)
                    details[name] = node.space
    if not seen:
        return make_result(ctx, "MAT006", False, INFO, "No normal map node.", "", [])
    return make_result(ctx, "MAT006", bool(bad), WARN,
                       "Normal maps are tangent space (Roblox: OpenGL tangent-space only [OFFICIEL]; Blender bakes "
                       "OpenGL +X+Y+Z by default [VÉRIFIÉ]).",
                       "Normal map node not in tangent space.", bad, details)


@rule("MAT007", "materials", "PBR constant values plausibility", DOC + "#valeurs-pbr")
def pbr_constants(ctx: Context):
    tol = ctx.threshold("metallic_binary_tolerance", 0.05)
    metal_min = ctx.threshold("metal_min_linear_luminance", 0.35)
    diel_min = ctx.threshold("dielectric_min_linear_luminance", 0.013)
    bad, details = [], {}
    for name, (mat, users) in _scope_materials(ctx).items():
        for node in principled_nodes(mat):
            issues = []
            met_s = node.inputs.get("Metallic")
            base_s = node.inputs.get("Base Color")
            if met_s is None or base_s is None:
                continue
            met = met_s.default_value if not met_s.is_linked else None
            base = tuple(base_s.default_value)[:3] if not base_s.is_linked else None
            if met is not None and tol < met < 1 - tol:
                issues.append(f"metallic {met:.2f} not binary")
            if met is not None and base is not None:
                lum = mu.luminance_linear(base)
                if met >= 1 - tol and lum < metal_min:
                    issues.append(f"metal with dark base color (linear lum {lum:.3f} < {metal_min}); real metals "
                                  "are ≥ ~0.4 linear — dark gun finishes are coatings (dielectric) or need a documented exception")
                if met <= tol and lum < diel_min:
                    issues.append(f"dielectric base color darker than ~30 sRGB (linear lum {lum:.4f})")
            if issues:
                bad.extend(users)
                details[f"{name}/{node.name}"] = issues
    return make_result(ctx, "MAT007", bool(bad), WARN, "Unlinked PBR constants look plausible.",
                       "PBR values outside physically plausible ranges (see the gunmetal decision in the standard).",
                       bad, details)


@rule("MAT008", "materials", "Texture content analysis (optional)", DOC + "#roughness")
def texture_content(ctx: Context):
    if not ctx.options.get("analyze_textures"):
        return make_result(ctx, "MAT008", False, INFO, "Skipped (use --analyze-textures).", "", [])
    try:
        import numpy as np
    except ImportError:
        return info("MAT008", "numpy unavailable in this Blender build; skipped.")
    tol = ctx.threshold("metallic_binary_tolerance", 0.05)
    nonbin_max = ctx.threshold("metallic_nonbinary_max_share", 0.2)
    rough_min_std = ctx.threshold("roughness_min_stddev", 0.02)
    bad, details = [], {}
    done = set()
    for name, (mat, users) in _scope_materials(ctx).items():
        for img, usage, _node in material_images(mat):
            if img.name in done or usage not in {"metallic", "roughness", "base_color"} or not img.has_data and img.size[0] == 0:
                continue
            done.add(img.name)
            px = np.empty(img.size[0] * img.size[1] * img.channels, dtype=np.float32)
            img.pixels.foreach_get(px)
            px = px.reshape(-1, img.channels)
            ch0 = px[:, 0]
            entry = {"usage": usage}
            if usage == "metallic":
                share = float(np.mean((ch0 > tol) & (ch0 < 1 - tol)))
                entry["non_binary_share"] = round(share, 3)
                if share > nonbin_max:
                    entry["problem"] = "metalness mostly non-binary (reads as plastic/satin)"
            elif usage == "roughness":
                std = float(np.std(ch0))
                entry["mean"] = round(float(np.mean(ch0)), 3)
                entry["stddev"] = round(std, 4)
                if std < rough_min_std:
                    entry["problem"] = "uniform roughness: flat, CG/plastic look on dark surfaces"
            elif usage == "base_color":
                lum = 0.2126 * px[:, 0] + 0.7152 * px[:, 1] + 0.0722 * px[:, 2]
                entry["p1_luminance"] = round(float(np.percentile(lum, 1)), 4)
                entry["p50_luminance"] = round(float(np.percentile(lum, 50)), 4)
            details[img.name] = entry
            if "problem" in entry:
                bad.extend(users)
    return make_result(ctx, "MAT008", bool(bad), WARN, "Texture content analysed.",
                       "Texture content issues.", bad, details)


@rule("MAT009", "materials", "Material count vs profile budget", DOC + "#budgets")
def material_budget(ctx: Context):
    mx = ctx.threshold("material_max", 4)
    mats = _scope_materials(ctx)
    return make_result(ctx, "MAT009", len(mats) > mx, WARN, f"{len(mats)} material(s) ≤ {mx}.",
                       f"{len(mats)} materials > profile budget {mx} (each distinct texture set = more memory; each "
                       "MeshPart = one draw call).", [], {"materials": sorted(mats)})
