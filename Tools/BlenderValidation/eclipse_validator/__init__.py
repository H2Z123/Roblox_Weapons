"""ECLIPSE Blender asset validator.

Detects production problems in a Blender scene and writes a JSON + Markdown
report. It never modifies the scene.

Usage inside Blender (CLI):
    blender -b ECLIPSE1_SRC_v012.blend --python Tools/BlenderValidation/validate_eclipse_asset.py -- \
        --profile viewmodel --collection ECLIPSE1_VM --out Reports/validation/ECLIPSE1_VM_before

Usage from a live session (Blender MCP ``execute_blender_code``):
    import sys; sys.path.insert(0, r"<repo>/Tools/BlenderValidation")
    import eclipse_validator as ev
    rep = ev.run(profile="viewmodel", collection="ECLIPSE1_VM", out_dir=r"<repo>/Reports/validation/x")
    print(rep["summary"])
"""

from __future__ import annotations

import importlib
import os
from typing import Any, Dict, Iterable, List, Optional

from . import core, config as _config, report as _report

__version__ = "0.1.0"

RULE_MODULES = ("geometry", "shading", "bevel", "transforms", "materials", "uv", "budget",
                "rig", "export", "naming")

# Aliases matching the script names requested in the mission brief.
CHECK_ALIASES: Dict[str, Dict[str, List[str]]] = {
    "validate_scene": {"categories": ["scene"], "rules": ["EXP001"]},
    "validate_mesh": {"categories": ["geometry"], "rules": []},
    "validate_transforms": {"categories": ["transforms"], "rules": []},
    "validate_orientation": {"categories": ["orientation"], "rules": []},
    "validate_scale": {"categories": ["scale"], "rules": ["TRF006"]},
    "validate_normals": {"categories": ["shading"], "rules": ["GEO006"]},
    "validate_non_manifold": {"categories": [], "rules": ["GEO001", "GEO002", "GEO005"]},
    "validate_degenerate": {"categories": [], "rules": ["GEO003", "GEO009", "UV004"]},
    "validate_duplicate_vertices": {"categories": [], "rules": ["GEO004", "GEO008"]},
    "validate_materials": {"categories": ["materials"], "rules": []},
    "validate_uv": {"categories": ["uv"], "rules": []},
    "validate_triangle_budget": {"categories": ["budget"], "rules": ["GEO010"]},
    "validate_pivots": {"categories": ["pivots", "grip"], "rules": []},
    "validate_moving_parts": {"categories": ["moving_parts"], "rules": []},
    "validate_viewmodel_worldmodel": {"categories": ["viewmodel_worldmodel"], "rules": []},
    "validate_export_readiness": {"categories": ["export", "naming"], "rules": ["TRF001", "TRF002", "TRF006"]},
    "validate_bevels": {"categories": ["bevel"], "rules": []},
    "validate_rig": {"categories": ["rig"], "rules": []},
}


def bpy_available() -> bool:
    try:
        import bpy  # noqa: F401
        return True
    except ImportError:
        return False


def load_rules(reload: bool = False) -> None:
    """Import (or reload) rule modules; they register themselves in core."""
    if not bpy_available():
        importlib.import_module(__name__ + ".naming")
        return
    for name in ("bpy_helpers",) + RULE_MODULES + ("inventory",):
        mod = importlib.import_module(f"{__name__}.{name}")
        if reload:
            importlib.reload(mod)


def resolve_checks(checks: Iterable[str]):
    cats, rules = set(), set()
    for c in checks or []:
        if c in CHECK_ALIASES:
            cats.update(CHECK_ALIASES[c]["categories"])
            rules.update(CHECK_ALIASES[c]["rules"])
        else:
            cats.add(c)
    return cats, rules


def run(profile: str = "source", stage: str = "source", collection: Optional[str] = None,
        objects: Optional[List[str]] = None, out_dir: Optional[str] = None, config_path: Optional[str] = None,
        checks: Optional[Iterable[str]] = None, rules: Optional[Iterable[str]] = None,
        analyze_textures: bool = False, texture_resolution: Optional[int] = None,
        reload: bool = False) -> Dict[str, Any]:
    """Validate the open Blender file. Returns the report dict (and writes it if out_dir)."""
    load_rules(reload=reload)
    cfg = _config.load_config(config_path)
    if profile not in cfg["profiles"]:
        raise ValueError(f"Unknown profile '{profile}'. Available: {sorted(k for k in cfg['profiles'] if not k.startswith('_'))}")
    opts = {"collection": collection, "objects": objects, "analyze_textures": analyze_textures,
            "texture_resolution": texture_resolution}
    ctx = core.Context(cfg, profile, stage, [], opts)
    have_bpy = bpy_available()
    meta: Dict[str, Any] = {"profile": profile, "stage": stage, "validator_version": __version__,
                            "config": config_path or os.path.basename(_config.DEFAULT_CONFIG_PATH)}
    inventory: Dict[str, Any] = {}
    if have_bpy:
        import bpy
        from .bpy_helpers import resolve_scope
        from .inventory import build_inventory
        # Refresh matrix_world / evaluated data (read-only; does not change the file).
        bpy.context.view_layer.update()
        ctx.scope = resolve_scope(ctx)
        meta.update({"blender_version": bpy.app.version_string, "file_path": bpy.data.filepath or "<unsaved>",
                     "file_name": os.path.basename(bpy.data.filepath) or "<unsaved>",
                     "scope_description": ctx.cache.get("scope_description", ""),
                     "scope_objects": [o.name for o in ctx.scope]})
    cats, rule_ids = resolve_checks(checks or [])
    rule_ids |= set(rules or [])
    if cats and rule_ids:
        # union semantics: run a rule if its category OR its id was requested
        selected = [rid for rid, spec in core.registry().items() if spec.category in cats or rid in rule_ids]
        results = core.run_rules(ctx, only_rules=selected, bpy_available=have_bpy)
    else:
        results = core.run_rules(ctx, only_categories=cats or None, only_rules=rule_ids or None,
                                 bpy_available=have_bpy)
    if have_bpy:
        inventory = build_inventory(ctx)
    rep = _report.build_report(results, meta, inventory)
    if out_dir:
        rep["written"] = _report.write_report(rep, out_dir)
    return rep
