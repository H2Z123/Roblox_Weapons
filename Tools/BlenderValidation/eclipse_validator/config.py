"""Configuration loading (pure Python)."""

from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.normpath(os.path.join(HERE, "..", "config", "eclipse_default.json"))


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge ``override`` into a copy of ``base``.

    Dicts merge key by key; any other type (lists included) is replaced.
    """
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load the default config, then merge the optional user config on top."""
    with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            cfg = deep_merge(cfg, json.load(fh))
    validate_config(cfg)
    return cfg


def validate_config(cfg: Dict[str, Any]) -> None:
    """Raise ValueError on structural mistakes that would silently break rules."""
    if "profiles" not in cfg or not isinstance(cfg["profiles"], dict):
        raise ValueError("config: 'profiles' must be an object")
    for name, prof in cfg["profiles"].items():
        if name.startswith("_"):
            continue
        for key in ("view_distance", "texture_resolution", "max_texture_resolution"):
            if key not in prof:
                raise ValueError(f"config: profile '{name}' misses '{key}'")
        if prof["view_distance"] <= 0:
            raise ValueError(f"config: profile '{name}' view_distance must be > 0")
    valid = {"PASS", "INFO", "WARN", "FAIL", "SKIP"}
    for stage, overrides in cfg.get("stage_severity", {}).items():
        for rid, sev in overrides.items():
            if sev not in valid:
                raise ValueError(f"config: stage '{stage}' severity '{sev}' for {rid} is invalid")
    fwd = cfg.get("orientation", {}).get("blender_forward", "-Y")
    if fwd not in ("+X", "-X", "+Y", "-Y", "+Z", "-Z"):
        raise ValueError("config: orientation.blender_forward must be one of +X -X +Y -Y +Z -Z")


def motion_for(cfg: Dict[str, Any], names) -> Optional[Dict[str, Any]]:
    """Return the configured motion for the first matching name, if any."""
    table = cfg.get("moving_parts", {})
    for n in names:
        if n and n in table and not str(n).startswith("_"):
            return dict(table[n])
    return None
