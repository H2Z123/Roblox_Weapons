"""Tests that run without Blender: math, config, report, naming, core runner."""

import json
import math
import os
import re

import pytest

from eclipse_validator import CHECK_ALIASES, config, core, mathutil as mu, report
from eclipse_validator.naming import check_names

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# -- mathutil ---------------------------------------------------------------

def test_pixels_per_stud_matches_formula():
    # FOV 70 vertical, 1080p, 2 studs: 1080 / (2*2*tan35°) ≈ 385.6
    assert mu.pixels_per_stud(2.0) == pytest.approx(385.6, abs=0.2)
    assert mu.pixels_per_stud(1.0) == pytest.approx(2 * mu.pixels_per_stud(2.0))


def test_min_visible_width_roundtrip():
    w = mu.min_visible_width(2.0, 2.0)
    assert mu.projected_px(w, 2.0) == pytest.approx(2.0)


def test_cylinder_sides_sagitta():
    ppu = mu.pixels_per_stud(2.0)
    n = mu.cylinder_sides(0.06, ppu, 0.5)
    r_px = 0.06 * ppu
    assert r_px * (1 - math.cos(math.pi / n)) <= 0.5 + 1e-9
    assert n % 2 == 0
    # far away the minimum applies
    assert mu.cylinder_sides(0.06, mu.pixels_per_stud(50.0)) == 6


def test_texel_density_and_resolution():
    # 1 stud² fully covering a 512 texture -> 512 px/stud
    assert mu.texel_density(1.0, 1.0, 512) == pytest.approx(512)
    assert mu.texel_density(0.25, 1.0, 1024) == pytest.approx(512)
    assert mu.recommended_resolution(2.5, 400, 0.7) == 1024
    assert mu.recommended_resolution(6.0, 400, 0.7) == 2048
    assert mu.next_pow2(513) == 1024


def test_padding_rule():
    assert mu.padding_px(1024) == 16
    assert mu.padding_px(512) == 8
    assert mu.padding_px(2048) == 32
    assert mu.padding_px(128) == 4


def test_srgb_roundtrip_and_luminance():
    for v in (0.0, 0.02, 0.2, 0.5, 1.0):
        assert mu.linear_to_srgb(mu.srgb_to_linear(v)) == pytest.approx(v, abs=1e-6)
    assert mu.srgb_to_linear(30 / 255) == pytest.approx(0.0130, abs=5e-4)
    assert mu.luminance_linear((1, 1, 1)) == pytest.approx(1.0)


def test_percentiles():
    assert mu.percentile([1, 2, 3, 4, 5], 50) == 3
    assert mu.weighted_percentile([(1, 1), (10, 9)], 50) == 10


def test_geometry_helpers():
    d, t = mu.segment_point_distance((0, 0, 0), (2, 0, 0), (1, 1, 0))
    assert d == pytest.approx(1) and t == pytest.approx(0.5)
    assert mu.triangle_min_angle((0, 0, 0), (1, 0, 0), (0, 1, 0)) == pytest.approx(45)
    assert mu.axis_vector("-Y") == (0.0, -1.0, 0.0)


# -- config -------------------------------------------------------------------

def test_default_config_loads_and_has_profiles():
    cfg = config.load_config()
    for p in ("source", "viewmodel", "worldmodel"):
        assert p in cfg["profiles"]
    assert cfg["thresholds"]["max_tris_per_meshpart_hard"] == 20000  # official Roblox limit


def test_deep_merge_and_validation(tmp_path):
    user = tmp_path / "c.json"
    user.write_text(json.dumps({"profiles": {"viewmodel": {"view_distance": 3.0}},
                                "orientation": {"blender_forward": "+Y"}}))
    cfg = config.load_config(str(user))
    assert cfg["profiles"]["viewmodel"]["view_distance"] == 3.0
    assert cfg["profiles"]["viewmodel"]["texture_resolution"] == 1024  # untouched
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"orientation": {"blender_forward": "forward"}}))
    with pytest.raises(ValueError):
        config.load_config(str(bad))


def test_motion_lookup():
    cfg = {"moving_parts": {"TopHatch": {"type": "ROTATE", "axis": "X", "min": 0, "max": 110}}}
    assert config.motion_for(cfg, ["X", "TopHatch"])["max"] == 110
    assert config.motion_for(cfg, ["Nope"]) is None


# -- core / report ------------------------------------------------------------

def _ctx(stage="source"):
    return core.Context(config.load_config(), "viewmodel", stage)


def test_severity_resolution_stage_over_profile():
    ctx = _ctx("export")
    assert ctx.severity("TRF001", "WARN") == "FAIL"
    assert _ctx("source").severity("TRF001", "WARN") == "WARN"
    src = core.Context(config.load_config(), "source", "source")
    assert src.severity("TRF001", "WARN") == "INFO"


def test_runner_catches_crashes_and_skips_bpy_rules():
    @core.rule("TST001", "test", "crashing rule", needs_bpy=False)
    def _boom(ctx):
        raise RuntimeError("boom")

    @core.rule("TST002", "test", "bpy rule", needs_bpy=True)
    def _needs(ctx):  # pragma: no cover
        return None

    @core.rule("TST003", "test", "ok rule", needs_bpy=False)
    def _ok(ctx):
        return core.make_result(ctx, "TST003", True, core.WARN, "ok", "bad", ["A", "A", "B"])

    res = {r.rule_id: r for r in core.run_rules(_ctx(), only_categories=["test"], bpy_available=False)}
    assert res["TST001"].status == core.ERROR
    assert res["TST002"].status == core.SKIP
    assert res["TST003"].status == core.WARN and res["TST003"].objects == ["A", "B"]


def test_report_json_and_markdown(tmp_path):
    results = [core.RuleResult("GEO001", "geometry", "Non-manifold", core.FAIL, "bad", ["Body"], {"x": 1}, "doc#a"),
               core.RuleResult("UV001", "uv", "UV", core.PASS, "ok")]
    rep = report.build_report(results, {"profile": "viewmodel", "stage": "source", "file_name": "t.blend"},
                              {"objects": [{"name": "Body", "tris": 12, "dimensions": [1, 1, 1], "scale": [1, 1, 1],
                                            "materials": [], "uv_maps": [], "modifiers": []}],
                               "total_tris": 12, "mesh_count": 1, "material_count": 0})
    assert rep["summary"]["overall"] == core.FAIL
    assert rep["results"][0]["rule_id"] == "GEO001"  # most severe first
    paths = report.write_report(rep, str(tmp_path))
    data = json.load(open(paths["json"]))
    assert data["summary"]["counts"]["FAIL"] == 1
    md = open(paths["markdown"]).read()
    assert "FAIL — must fix" in md and "`Body`" in md and "## Inventory" in md


# -- naming -------------------------------------------------------------------

def test_check_names_legacy_and_suffix():
    pats = config.load_config()["naming"]["object_patterns"]
    bad = check_names(["ECLIPSE1_VM_MainBody", "MainBody", "TopHatch.001", "weird name", "Grip_Att"],
                      pats, ["MainBody"])
    assert bad == ["TopHatch.001", "weird name"]


# -- catalogue ----------------------------------------------------------------

def test_every_requested_script_has_an_alias():
    requested = ["validate_scene", "validate_mesh", "validate_transforms", "validate_orientation", "validate_scale",
                 "validate_normals", "validate_non_manifold", "validate_degenerate", "validate_duplicate_vertices",
                 "validate_materials", "validate_uv", "validate_triangle_budget", "validate_pivots",
                 "validate_moving_parts", "validate_viewmodel_worldmodel", "validate_export_readiness"]
    for name in requested:
        assert name in CHECK_ALIASES


def test_rule_ids_unique_and_documented_statically():
    """Scan sources: every @rule id is unique and points to an existing standard file."""
    pkg = os.path.join(ROOT, "eclipse_validator")
    ids, docs = [], []
    for fn in os.listdir(pkg):
        if fn.endswith(".py"):
            src = open(os.path.join(pkg, fn), encoding="utf-8").read()
            ids += re.findall(r'@rule\("([A-Z]+\d+)"', src)
    assert len(ids) == len(set(ids)), "duplicate rule ids"
    assert len(ids) >= 50
    repo = os.path.dirname(os.path.dirname(ROOT))
    for fn in os.listdir(pkg):
        if fn.endswith(".py"):
            src = open(os.path.join(pkg, fn), encoding="utf-8").read()
            docs += re.findall(r'(Standards/[A-Z_]+\.md)', src)
    missing = sorted({d for d in docs if not os.path.exists(os.path.join(repo, d))})
    assert not missing, f"rules reference missing standards: {missing}"


def test_rule_doc_anchors_exist():
    """Every 'Standards/X.md#anchor' referenced by a rule has a matching <a id> or heading."""
    pkg = os.path.join(ROOT, "eclipse_validator")
    repo = os.path.dirname(os.path.dirname(ROOT))
    refs = set()
    for fn in os.listdir(pkg):
        if fn.endswith(".py"):
            src = open(os.path.join(pkg, fn), encoding="utf-8").read()
            refs |= set(re.findall(r'(Standards/[A-Z_]+\.md)(?:"\s*\+\s*"|)#([a-z0-9-]+)', src))
            for doc_var, anchor in re.findall(r'(DOC\w*)\s*\+\s*"#([a-z0-9-]+)"', src):
                m = re.search(doc_var + r'\s*=\s*"(Standards/[A-Z_]+\.md)', src)
                if m:
                    refs.add((m.group(1), anchor))
    assert refs
    missing = []
    for doc, anchor in sorted(refs):
        text = open(os.path.join(repo, doc), encoding="utf-8").read()
        if f'id="{anchor}"' not in text:
            missing.append(f"{doc}#{anchor}")
    assert not missing, missing
