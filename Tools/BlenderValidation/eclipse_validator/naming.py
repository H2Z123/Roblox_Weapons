"""Naming rules. Standard: Standards/ECLIPSE_NAMING_VERSIONING_STANDARD.md

Pure functions (``check_names``) are unit-tested without Blender; the rules
only gather names from the scene.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List

from .core import INFO, WARN, Context, make_result, rule

DOC = "Standards/ECLIPSE_NAMING_VERSIONING_STANDARD.md"


def check_names(names: Iterable[str], patterns: List[str], legacy: Iterable[str] = ()) -> List[str]:
    """Return names matching none of ``patterns`` and not listed as legacy."""
    legacy = set(legacy)
    compiled = [re.compile(p) for p in patterns]
    bad = []
    for n in names:
        base = re.sub(r"\.\d{3}$", "", n)  # Blender duplicate suffix is itself a problem
        if n != base:
            bad.append(n)
            continue
        if n in legacy:
            continue
        if not any(c.match(n) for c in compiled):
            bad.append(n)
    return bad


@rule("NAM001", "naming", "Object names", DOC + "#objets")
def object_names(ctx: Context):
    cfg = ctx.config.get("naming", {})
    names = [ob.name for ob in ctx.scope if ob.type in {"MESH", "EMPTY", "ARMATURE"}]
    bad = check_names(names, cfg.get("object_patterns", []), cfg.get("legacy_names", []))
    return make_result(ctx, "NAM001", bool(bad), WARN, "Object names follow the convention.",
                       "Names outside the convention or with Blender '.001' suffixes (never rename existing Roblox-"
                       "facing parts without updating Motor6D/animations — use roblox_name instead).", bad)


@rule("NAM002", "naming", "Material names", DOC + "#materiaux")
def material_names(ctx: Context):
    cfg = ctx.config.get("naming", {})
    names = sorted({s.material.name for ob in ctx.scope if ob.type == "MESH"
                    for s in ob.material_slots if s.material})
    bad = check_names(names, [cfg.get("material_pattern", r"^M_.+$")])
    return make_result(ctx, "NAM002", bool(bad), INFO, "Material names follow M_<Asset>_<Surface>.",
                       "Material names outside M_<Asset>_<Surface>.", [], {"materials": bad})


@rule("NAM003", "naming", "Texture image names", DOC + "#textures")
def texture_names(ctx: Context):
    from .bpy_helpers import material_images
    cfg = ctx.config.get("naming", {})
    names = set()
    for ob in ctx.scope:
        if ob.type != "MESH":
            continue
        for s in ob.material_slots:
            for img, _u, _n in material_images(s.material):
                names.add(re.sub(r"\.(png|tga|jpg|jpeg|exr|tif|tiff)$", "", img.name, flags=re.I))
    bad = check_names(sorted(names), [cfg.get("texture_pattern", r"^T_.+$")])
    return make_result(ctx, "NAM003", bool(bad), INFO, "Texture names follow T_<Asset>_<Part>_<Map>.",
                       "Texture names outside T_<Asset>_<Part>_<Map>.", [], {"textures": bad})
