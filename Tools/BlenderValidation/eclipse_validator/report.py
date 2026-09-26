"""Report building and serialisation (JSON + Markdown). Pure Python."""

from __future__ import annotations

import datetime as _dt
import json
import os
from typing import Any, Dict, List

from .core import ALL_STATUSES, FAIL, INFO, PASS, SKIP, STATUS_ORDER, WARN, ERROR, RuleResult, worst

REPORT_SCHEMA_VERSION = 1


def summarize(results: List[RuleResult]) -> Dict[str, Any]:
    counts = {s: 0 for s in ALL_STATUSES}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    by_cat: Dict[str, Dict[str, int]] = {}
    for r in results:
        cat = by_cat.setdefault(r.category or "misc", {s: 0 for s in ALL_STATUSES})
        cat[r.status] = cat.get(r.status, 0) + 1
    return {"overall": worst(r.status for r in results), "counts": counts, "by_category": by_cat}


def build_report(results: List[RuleResult], meta: Dict[str, Any], inventory: Dict[str, Any] | None = None) -> Dict[str, Any]:
    ordered = sorted(results, key=lambda r: (-STATUS_ORDER.get(r.status, 0), r.rule_id))
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "meta": meta,
        "summary": summarize(results),
        "results": [r.to_dict() for r in ordered],
        "inventory": inventory or {},
    }


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.4g}"
    if isinstance(v, (list, tuple)):
        return ", ".join(_fmt(x) for x in v)
    return str(v)


def to_markdown(report: Dict[str, Any], max_objects: int = 12, max_details: int = 10) -> str:
    meta = report.get("meta", {})
    summ = report.get("summary", {})
    counts = summ.get("counts", {})
    lines: List[str] = []
    lines.append(f"# ECLIPSE validation report — {meta.get('file_name', '?')}")
    lines.append("")
    lines.append(f"- **Overall:** `{summ.get('overall', '?')}`")
    lines.append(f"- Profile: `{meta.get('profile')}` · Stage: `{meta.get('stage')}` · Scope: {meta.get('scope_description', '?')}")
    lines.append(f"- Blender: {meta.get('blender_version', 'n/a')} · Validator: {meta.get('validator_version', '?')} · Generated: {report.get('generated_at')}")
    lines.append(f"- File: `{meta.get('file_path', '?')}`")
    lines.append("")
    lines.append("| FAIL | WARN | INFO | PASS | SKIP | ERROR |")
    lines.append("|---:|---:|---:|---:|---:|---:|")
    lines.append(" | ".join(["", *(str(counts.get(s, 0)) for s in (FAIL, WARN, INFO, PASS, SKIP, ERROR)), ""]).strip())
    lines.append("")
    lines.append("> The validator only detects. Every fix is a human/agent decision — see the linked standard.")
    lines.append("")

    results = report.get("results", [])
    for status, heading in ((ERROR, "Validator errors"), (FAIL, "FAIL — must fix"),
                            (WARN, "WARN — decide"), (INFO, "INFO — measurements")):
        subset = [r for r in results if r["status"] == status]
        if not subset:
            continue
        lines.append(f"## {heading} ({len(subset)})")
        lines.append("")
        for r in subset:
            lines.append(f"### `{r['rule_id']}` {r['title']}")
            lines.append(f"{r['message']}")
            if r.get("objects"):
                objs = r["objects"]
                more = f" … (+{len(objs) - max_objects})" if len(objs) > max_objects else ""
                lines.append(f"- Objects: {', '.join('`' + o + '`' for o in objs[:max_objects])}{more}")
            det = r.get("details") or {}
            shown = 0
            for k, v in det.items():
                if k == "traceback" or shown >= max_details:
                    continue
                if isinstance(v, dict) and len(v) > 8:
                    v = dict(list(v.items())[:8])
                    v["…"] = "truncated"
                lines.append(f"- {k}: {_fmt(v) if not isinstance(v, dict) else json.dumps(v, default=str)}")
                shown += 1
            if r.get("doc"):
                lines.append(f"- Standard: `{r['doc']}`")
            lines.append("")

    passed = [r for r in results if r["status"] in (PASS, SKIP)]
    if passed:
        lines.append(f"## PASS / SKIP ({len(passed)})")
        lines.append("")
        lines.append(", ".join(f"`{r['rule_id']}`{'' if r['status'] == PASS else ' (skip)'}" for r in passed))
        lines.append("")

    inv = report.get("inventory") or {}
    objs = inv.get("objects") or []
    if objs:
        lines.append("## Inventory")
        lines.append("")
        lines.append(f"Total triangles (evaluated): **{inv.get('total_tris', '?')}** · Mesh objects: {inv.get('mesh_count', '?')} · Materials: {inv.get('material_count', '?')}")
        lines.append("")
        lines.append("| Object | Roblox name | Tris | Dimensions (studs) | Scale | Mats | UVs | Modifiers |")
        lines.append("|---|---|---:|---|---|---:|---:|---|")
        for o in objs:
            dims = "×".join(f"{d:.3f}" for d in o.get("dimensions", []))
            scale = "×".join(f"{s:.3g}" for s in o.get("scale", []))
            mods = ", ".join(m.get("type", "?") for m in o.get("modifiers", []))
            lines.append(f"| `{o.get('name')}` | {o.get('roblox_name', '')} | {o.get('tris', '')} | {dims} | {scale} | "
                         f"{len(o.get('materials', []))} | {len(o.get('uv_maps', []))} | {mods} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_report(report: Dict[str, Any], out_dir: str, basename: str = "validation_report") -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    jpath = os.path.join(out_dir, basename + ".json")
    mpath = os.path.join(out_dir, basename + ".md")
    with open(jpath, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    with open(mpath, "w", encoding="utf-8") as fh:
        fh.write(to_markdown(report))
    return {"json": jpath, "markdown": mpath}
