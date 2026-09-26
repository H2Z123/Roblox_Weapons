"""Core data model of the ECLIPSE validator.

Pure Python: importable without Blender so reports, configs and rule
bookkeeping can be unit-tested outside Blender.

Vocabulary
----------
* A *rule* is a function registered with :func:`rule`. It receives a
  :class:`Context` and returns one :class:`RuleResult` (or a list of them).
* A *status* is one of PASS / INFO / WARN / FAIL / SKIP / ERROR.
  - PASS  : rule checked, nothing to report.
  - INFO  : measurement or reminder, never blocks.
  - WARN  : likely problem, needs a human/agent decision.
  - FAIL  : breaks a hard requirement (official limit, broken geometry...).
  - SKIP  : rule not applicable (no data, disabled by config/profile).
  - ERROR : the rule itself crashed (bug in the validator, not the asset).

The validator DETECTS. It never modifies the scene.
"""

from __future__ import annotations

import dataclasses
import time
import traceback
from typing import Any, Callable, Dict, Iterable, List, Optional

PASS = "PASS"
INFO = "INFO"
WARN = "WARN"
FAIL = "FAIL"
SKIP = "SKIP"
ERROR = "ERROR"

STATUS_ORDER = {PASS: 0, SKIP: 0, INFO: 1, WARN: 2, FAIL: 3, ERROR: 4}
ALL_STATUSES = (PASS, INFO, WARN, FAIL, SKIP, ERROR)


def worst(statuses: Iterable[str]) -> str:
    """Return the most severe status of an iterable (PASS if empty)."""
    result = PASS
    for s in statuses:
        if STATUS_ORDER.get(s, 0) > STATUS_ORDER.get(result, 0):
            result = s
    return result


@dataclasses.dataclass
class RuleResult:
    rule_id: str
    category: str
    title: str
    status: str
    message: str = ""
    objects: List[str] = dataclasses.field(default_factory=list)
    details: Dict[str, Any] = dataclasses.field(default_factory=dict)
    doc: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class RuleSpec:
    rule_id: str
    category: str
    title: str
    doc: str
    func: Callable[["Context"], Any]
    needs_bpy: bool = True


_REGISTRY: Dict[str, RuleSpec] = {}


def rule(rule_id: str, category: str, title: str, doc: str = "", needs_bpy: bool = True):
    """Decorator registering a rule function.

    ``doc`` points to the standard section that justifies the rule, e.g.
    ``Standards/ECLIPSE_SHADING_STANDARD.md#weighted-normals``.
    """

    def deco(func):
        prev = _REGISTRY.get(rule_id)
        # Re-registration from the same module happens on importlib.reload()
        # inside a live Blender session (Blender MCP); anything else is a bug.
        if prev is not None and prev.func.__module__ != func.__module__:
            raise ValueError(f"Duplicate rule id {rule_id} ({prev.func.__module__} vs {func.__module__})")
        _REGISTRY[rule_id] = RuleSpec(rule_id, category, title, doc, func, needs_bpy)
        return func

    return deco


def registry() -> Dict[str, RuleSpec]:
    return dict(_REGISTRY)


class Context:
    """Everything a rule needs: config, profile, stage, scope and helpers.

    ``scope`` is a list of objects (Blender objects when running in Blender,
    or any stand-in in tests). ``cache`` lets rules share expensive data
    (evaluated meshes, bmesh stats...) within one run.
    """

    def __init__(self, config: Dict[str, Any], profile: str, stage: str = "source",
                 scope: Optional[list] = None, options: Optional[Dict[str, Any]] = None):
        self.config = config
        self.profile_name = profile
        self.stage = stage
        self.scope = scope or []
        self.options = options or {}
        self.cache: Dict[str, Any] = {}

    # -- configuration helpers -------------------------------------------
    @property
    def profile(self) -> Dict[str, Any]:
        return self.config["profiles"][self.profile_name]

    def threshold(self, key: str, default: Any = None) -> Any:
        """Profile value first, then global ``thresholds``, then default."""
        if key in self.profile:
            return self.profile[key]
        return self.config.get("thresholds", {}).get(key, default)

    def severity(self, rule_id: str, default: str) -> str:
        """Severity for a *violation* of ``rule_id``.

        Resolution order: stage override, profile override, default.
        """
        stage_over = self.config.get("stage_severity", {}).get(self.stage, {})
        if rule_id in stage_over:
            return stage_over[rule_id]
        prof_over = self.profile.get("severity", {})
        if rule_id in prof_over:
            return prof_over[rule_id]
        return default

    def rule_enabled(self, rule_id: str) -> bool:
        disabled = set(self.config.get("disabled_rules", [])) | set(self.profile.get("disabled_rules", []))
        return rule_id not in disabled


def run_rules(ctx: Context, only_categories: Optional[Iterable[str]] = None,
              only_rules: Optional[Iterable[str]] = None, bpy_available: bool = True) -> List[RuleResult]:
    """Run every registered rule matching the filters; never raises."""
    only_categories = set(only_categories or [])
    only_rules = set(only_rules or [])
    results: List[RuleResult] = []
    for spec in sorted(_REGISTRY.values(), key=lambda s: s.rule_id):
        if only_categories and spec.category not in only_categories:
            continue
        if only_rules and spec.rule_id not in only_rules:
            continue
        if not ctx.rule_enabled(spec.rule_id):
            results.append(RuleResult(spec.rule_id, spec.category, spec.title, SKIP,
                                      "Disabled by configuration.", doc=spec.doc))
            continue
        if spec.needs_bpy and not bpy_available:
            results.append(RuleResult(spec.rule_id, spec.category, spec.title, SKIP,
                                      "Requires Blender (bpy).", doc=spec.doc))
            continue
        t0 = time.perf_counter()
        try:
            out = spec.func(ctx)
        except Exception as exc:  # the validator must never crash the whole run
            out = RuleResult(spec.rule_id, spec.category, spec.title, ERROR,
                             f"Rule crashed: {exc!r}",
                             details={"traceback": traceback.format_exc(limit=6)})
        dt = (time.perf_counter() - t0) * 1000.0
        outs = out if isinstance(out, list) else [out]
        for r in outs:
            if r is None:
                continue
            r.rule_id = r.rule_id or spec.rule_id
            r.category = r.category or spec.category
            r.title = r.title or spec.title
            r.doc = r.doc or spec.doc
            r.duration_ms = round(dt / max(1, len(outs)), 2)
            results.append(r)
    return results


def make_result(ctx: Context, rule_id: str, violated: bool, default_severity: str,
                ok_message: str, bad_message: str, objects: Optional[List[str]] = None,
                details: Optional[Dict[str, Any]] = None) -> RuleResult:
    """Build a result: PASS when not violated, else the configured severity."""
    spec = _REGISTRY.get(rule_id)
    title = spec.title if spec else rule_id
    category = spec.category if spec else ""
    doc = spec.doc if spec else ""
    if not violated:
        return RuleResult(rule_id, category, title, PASS, ok_message, [], details or {}, doc)
    return RuleResult(rule_id, category, title, ctx.severity(rule_id, default_severity),
                      bad_message, sorted(set(objects or [])), details or {}, doc)


def info(rule_id: str, message: str, details: Optional[Dict[str, Any]] = None,
         objects: Optional[List[str]] = None) -> RuleResult:
    spec = _REGISTRY.get(rule_id)
    return RuleResult(rule_id, spec.category if spec else "", spec.title if spec else rule_id,
                      INFO, message, sorted(set(objects or [])), details or {}, spec.doc if spec else "")


def skip(rule_id: str, message: str) -> RuleResult:
    spec = _REGISTRY.get(rule_id)
    return RuleResult(rule_id, spec.category if spec else "", spec.title if spec else rule_id,
                      SKIP, message, [], {}, spec.doc if spec else "")
