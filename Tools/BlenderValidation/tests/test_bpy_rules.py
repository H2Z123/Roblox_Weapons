"""Integration tests on synthetic scenes (requires bpy). Not a validation of ECLIPSE-1."""

import math
import os
import subprocess
import sys

import pytest

from conftest import HAS_BPY, ROOT, requires_bpy

pytestmark = requires_bpy

if HAS_BPY:
    import bpy
    import eclipse_validator as ev
    import scene_builders as sb


def run(rules, profile="viewmodel", stage="source", **kw):
    rep = ev.run(profile=profile, stage=stage, rules=rules, **kw)
    return {r["rule_id"]: r for r in rep["results"]}, rep


def st(res, rid):
    return res[rid]["status"]


# -- geometry -------------------------------------------------------------------

def test_clean_box_passes_geometry():
    sb.reset()
    sb.box("MainBody")
    res, _ = run(["GEO001", "GEO002", "GEO003", "GEO004", "GEO005", "GEO006", "GEO008", "GEO009"])
    assert all(st(res, r) == "PASS" for r in res), {k: v["status"] for k, v in res.items()}


def test_open_plane_is_flagged_unless_allowed():
    sb.reset()
    p = sb.plane("Panel")
    res, _ = run(["GEO001"])
    assert st(res, "GEO001") == "WARN"
    p["eclipse_allow_open"] = True
    res, _ = run(["GEO001"])
    assert st(res, "GEO001") == "PASS"


def test_duplicate_vertices_and_faces():
    sb.reset()
    ob = sb.box("MainBody")
    me = ob.data
    # duplicate the whole geometry in place -> coincident verts + duplicate faces
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.duplicate(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    res, _ = run(["GEO004", "GEO008"])
    assert st(res, "GEO004") == "WARN"
    assert st(res, "GEO008") == "FAIL"


def test_t_junction_detected():
    sb.reset()
    ob = sb.t_junction_mesh("Seam")
    ob["eclipse_allow_open"] = True
    res, _ = run(["GEO005"])
    assert st(res, "GEO005") == "WARN"
    assert res["GEO005"]["details"]["Seam"]["t_junctions"] >= 1


def test_flipped_face_and_inside_out():
    sb.reset()
    ob = sb.box("MainBody")
    ob.data.polygons[0].flip()
    res, _ = run(["GEO006"])
    assert st(res, "GEO006") == "FAIL"
    sb.reset()
    ob = sb.box("MainBody")
    for p in ob.data.polygons:
        p.flip()
    res, _ = run(["GEO006"])
    assert res["GEO006"]["details"]["MainBody"]["inside_out_closed_shells"] == 1


def test_triangle_hard_limit():
    sb.reset()
    sb.dense_grid("Dense", subdiv=110)  # 109*109*2 = 23762 tris > 20000
    res, _ = run(["BUD001"])
    assert st(res, "BUD001") == "FAIL"


# -- transforms -----------------------------------------------------------------

def test_unapplied_scale_escalates_at_export():
    sb.reset()
    ob = sb.box("MainBody")
    ob.scale = (2, 1, 1)
    res, _ = run(["TRF001"], stage="source")
    assert st(res, "TRF001") == "WARN"
    res, _ = run(["TRF001"], stage="export")
    assert st(res, "TRF001") == "FAIL"
    res, _ = run(["TRF001"], profile="source")
    assert st(res, "TRF001") == "INFO"


def test_negative_scale_and_units():
    sb.reset()
    ob = sb.box("MainBody")
    ob.scale = (-1, 1, 1)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 0.01
    res, _ = run(["TRF002", "TRF006"])
    assert st(res, "TRF002") == "FAIL"
    assert st(res, "TRF006") == "FAIL"


def test_forward_axis_with_muzzle_marker():
    sb.reset()
    sb.box("MainBody", size=(0.2, 1.0, 0.3))
    sb.empty("Muzzle_Att", loc=(0, -0.6, 0))
    res, _ = run(["ORI001"])  # default blender_forward = -Y
    assert st(res, "ORI001") == "PASS"
    bpy.data.objects["Muzzle_Att"].location = (0, 0.6, 0)
    res, _ = run(["ORI001"])
    assert st(res, "ORI001") == "WARN"


# -- shading --------------------------------------------------------------------

def _beveled(weight=None):
    sb.reset()
    ob = sb.box("MainBody")
    for p in ob.data.polygons:
        p.use_smooth = True
    b = ob.modifiers.new("Bevel", "BEVEL")
    b.width = 0.02
    b.segments = 1
    if weight is not None:
        wn = ob.modifiers.new("WN", "WEIGHTED_NORMAL")
        wn.weight = weight
        wn.keep_sharp = True
    return ob


def test_smooth_bevel_without_wn_is_soft():
    _beveled()
    res, _ = run(["SHD002", "SHD005"])
    assert st(res, "SHD002") == "WARN"
    assert st(res, "SHD005") == "WARN"


def test_weighted_normal_weight_100_is_flat_and_50_is_flagged():
    _beveled(100)
    res, _ = run(["SHD002", "SHD004"])
    assert st(res, "SHD002") == "PASS"
    assert st(res, "SHD004") == "PASS"
    _beveled(50)
    res, _ = run(["SHD002", "SHD004"])
    assert st(res, "SHD002") == "WARN"   # measured ~5.4° on large faces
    assert st(res, "SHD004") == "WARN"


def test_triangulate_after_wn_flagged():
    ob = _beveled(100)
    t = ob.modifiers.new("Tri", "TRIANGULATE")
    t.keep_custom_normals = False
    res, _ = run(["SHD004"])
    assert st(res, "SHD004") == "WARN"


# -- bevel ----------------------------------------------------------------------

def test_bevel_rules():
    ob = _beveled(100)
    ob.modifiers["Bevel"].segments = 6
    ob.modifiers["Bevel"].width = 0.0005
    res, _ = run(["BEV001", "BEV002"], profile="viewmodel")
    assert st(res, "BEV001") == "WARN"
    assert st(res, "BEV002") == "WARN"
    ob.modifiers["Bevel"].width = 0.08      # 0.08 / 0.25 = 0.32 > 0.1
    ob.modifiers["Bevel"].segments = 2
    res, _ = run(["BEV001", "BEV003"])
    assert st(res, "BEV001") == "PASS"
    assert st(res, "BEV003") == "WARN"


# -- materials / uv ---------------------------------------------------------------

def test_material_rules():
    sb.reset()
    ob = sb.box("MainBody")
    m1 = sb.material("M_ECLIPSE1_Body", metallic=0.5)
    m2 = sb.material("M_ECLIPSE1_Dark", metallic=1.0, base=(0.02, 0.02, 0.02, 1))
    ob.data.materials.append(m1)
    ob.data.materials.append(m2)
    ob.data.polygons[0].material_index = 1
    res, _ = run(["MAT001", "MAT007"])
    assert st(res, "MAT001") == "WARN"
    assert st(res, "MAT007") == "WARN"


def test_uv_rules():
    sb.reset()
    ob = sb.box("MainBody", uv=False)
    ob.data.materials.append(sb.material("M_X"))
    res, _ = run(["UV001"])
    assert st(res, "UV001") == "FAIL"
    sb.reset()
    ob = sb.box("MainBody")
    uv = ob.data.uv_layers.active.data
    for l in ob.data.polygons[0].loop_indices:
        uv[l].uv = (uv[l].uv[0] + 1.5, uv[l].uv[1])
    res, _ = run(["UV003"])
    assert st(res, "UV003") == "WARN"
    for l in ob.data.polygons[1].loop_indices:
        uv[l].uv = (0.3, 0.3)
    res, _ = run(["UV004"])
    assert st(res, "UV004") == "FAIL"


def test_texel_density_reports_values():
    sb.reset()
    sb.box("MainBody")
    res, _ = run(["UV005"], texture_resolution=1024)
    det = res["UV005"]["details"]["per_object"]["MainBody"]
    assert det["td_overall"] > 0
    assert "recommended_resolution_for_target" in res["UV005"]["details"]


def test_uv_padding_tight_islands():
    sb.reset()
    ob = sb.box("MainBody")  # create_cube lays out ONE cross-shaped island
    ob.data.materials.append(sb.material("M_X"))
    res, _ = run(["UV006"], texture_resolution=1024)
    assert st(res, "UV006") == "PASS"
    # detach face 4 as its own island, only 2 px away at 1024 (rule: 16 px)
    uv = ob.data.uv_layers.active.data
    for l in ob.data.polygons[4].loop_indices:
        uv[l].uv = (uv[l].uv[0] - 2 / 1024, uv[l].uv[1])
    res, _ = run(["UV006"], texture_resolution=1024)
    assert st(res, "UV006") == "WARN"
    assert res["UV006"]["details"]["M_X"]["closest_islands_px"] == pytest.approx(2.0, abs=0.1)
    # a second mesh sharing the material and the same layout overlaps the first one
    for l in ob.data.polygons[4].loop_indices:
        uv[l].uv = (uv[l].uv[0] + 2 / 1024, uv[l].uv[1])
    other = sb.box("Other", loc=(2, 0, 0))
    other.data.materials.append(bpy.data.materials["M_X"])
    res, _ = run(["UV006"], texture_resolution=1024)
    assert st(res, "UV006") == "WARN"


# -- moving parts ---------------------------------------------------------------

def _hatch_scene(hinge_ok=True):
    sb.reset()
    body = sb.box("MainBody", size=(0.4, 1.0, 0.3), loc=(0, 0, 0))
    hatch = sb.box("TopHatch", size=(0.3, 0.4, 0.04), loc=(0, 0.1, 0.18))
    # a block standing right behind the hatch on the body top
    sb.box("RearSight", size=(0.1, 0.05, 0.12), loc=(0, 0.33, 0.21))
    # Hinge on the FRONT edge (y = -0.1). Correct: on the TOP-front corner (z = 0.20).
    # Wrong: on the BOTTOM-front corner (z = 0.16): past 90° the top-front corner
    # swings below the pivot and digs into MainBody (a classic hatch bug).
    hinge_z = 0.20 if hinge_ok else 0.16
    sb.set_origin(hatch, (0, -0.1, hinge_z))
    hatch["eclipse_role"] = "moving"
    hatch["eclipse_motion_type"] = "ROTATE"
    hatch["eclipse_motion_axis"] = "X"
    hatch["eclipse_motion_min"] = 0.0
    hatch["eclipse_motion_max"] = 110.0      # +X rotation lifts the rear of the hatch
    return body, hatch


def test_rest_contact_is_tolerated_but_penetration_fails():
    sb.reset()
    sb.box("A", size=(1, 1, 1), loc=(0, 0, 0))
    sb.box("B", size=(1, 1, 1), loc=(1.0, 0, 0))   # face contact only
    res, _ = run(["MOV001"])
    assert st(res, "MOV001") == "PASS"
    bpy.data.objects["B"].location = (0.8, 0, 0)     # 0.2 penetration
    res, _ = run(["MOV001"])
    assert st(res, "MOV001") == "FAIL"


def test_hatch_sweep_collision_detected_and_cleared():
    _hatch_scene(hinge_ok=False)
    res, _ = run(["MOV003", "MOV001"])
    assert st(res, "MOV001") == "PASS"
    assert st(res, "MOV003") == "FAIL", res["MOV003"]
    _hatch_scene(hinge_ok=True)
    res, _ = run(["MOV003"])
    assert st(res, "MOV003") == "PASS", res["MOV003"]


def test_default_origin_on_rotating_part():
    sb.reset()
    sb.box("MainBody")
    h = sb.box("TopHatch", size=(0.3, 0.3, 0.04), loc=(0, 0, 0.5))
    h["eclipse_role"] = "moving"
    h["eclipse_motion_type"] = "ROTATE"
    res, _ = run(["PIV002", "MOV004"])
    assert st(res, "PIV002") == "WARN"


# -- grip -----------------------------------------------------------------------

def test_grip_reference_rake_and_inside():
    sb.reset()
    sb.box("Grip", size=(0.12, 0.15, 0.5), loc=(0, 0.3, -0.25))
    # forward is -Y: top of grip leans toward -Y => rotate about X by +20° tilts +Z toward -Y? check sign
    g = sb.empty("Grip_Att", loc=(0, 0.3, -0.25), rot_deg=(20, 0, 0))
    res, _ = run(["GRP001"])
    rake = res["GRP001"]["details"]["rake_deg"]
    assert rake == pytest.approx(20, abs=0.5), rake
    assert st(res, "GRP001") == "PASS"
    g.rotation_euler = (math.radians(-15), 0, 0)
    res, _ = run(["GRP001"])
    assert st(res, "GRP001") == "WARN"


# -- export ---------------------------------------------------------------------

def test_visible_cutter_in_scope_fails():
    sb.reset()
    body = sb.box("MainBody")
    cutter = sb.box("Cutter_Slot", size=(0.2, 0.2, 0.6))
    m = body.modifiers.new("Bool", "BOOLEAN")
    m.object = cutter
    res, _ = run(["EXP002"])
    assert st(res, "EXP002") == "FAIL"
    coll = sb.collection("ECLIPSE1_VM_Cutters")
    bpy.context.scene.collection.objects.unlink(cutter)
    coll.objects.link(cutter)
    res, _ = run(["EXP002"])
    assert st(res, "EXP002") == "PASS"


def test_roblox_name_duplicates_fail():
    sb.reset()
    a = sb.box("ECLIPSE1_VM_MainBody")
    b = sb.box("ECLIPSE1_WM_MainBody")
    a["roblox_name"] = "MainBody"
    b["roblox_name"] = "MainBody"
    res, _ = run(["EXP005"])
    assert st(res, "EXP005") == "FAIL"


def test_vm_wm_comparison():
    sb.reset()
    vm = sb.collection("ECLIPSE1_VM")
    wm = sb.collection("ECLIPSE1_WM")
    v = sb.box("ECLIPSE1_VM_MainBody", coll=vm)
    b = v.modifiers.new("Bevel", "BEVEL")
    b.segments = 3
    b.width = 0.02
    sb.box("ECLIPSE1_WM_MainBody", coll=wm)
    res, _ = run(["VMWM001"])
    assert st(res, "VMWM001") == "PASS", res["VMWM001"]


# -- full run + CLI -------------------------------------------------------------

def test_full_run_writes_reports(tmp_path):
    _hatch_scene(hinge_ok=True)
    rep = ev.run(profile="viewmodel", out_dir=str(tmp_path))
    assert os.path.exists(rep["written"]["json"]) and os.path.exists(rep["written"]["markdown"])
    assert not [r for r in rep["results"] if r["status"] == "ERROR"], [r for r in rep["results"] if r["status"] == "ERROR"]
    assert rep["inventory"]["mesh_count"] == 3


def test_cli_end_to_end(tmp_path):
    _hatch_scene(hinge_ok=False)
    blend = str(tmp_path / "synthetic_SRC_v001.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    cli = os.path.join(ROOT, "validate_eclipse_asset.py")
    out = str(tmp_path / "report")
    code = (
        "import bpy, sys, runpy\n"
        f"bpy.ops.wm.open_mainfile(filepath={blend!r})\n"
        f"sys.argv = ['x', '--', '--profile', 'viewmodel', '--out', {out!r}]\n"
        f"runpy.run_path({cli!r}, run_name='__main__')\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300)
    assert proc.returncode == 1, proc.stdout + proc.stderr     # MOV003 FAIL expected
    assert "MOV003" in proc.stdout
    assert os.path.exists(os.path.join(out, "validation_report.md"))


def test_config_driven_motion_and_combined_scenario(tmp_path):
    """Motions declared in a project config (not in the .blend); the cartridge is swept
    with the hatch held open, then with the hatch closed (must collide)."""
    import json
    sb.reset()
    sb.box("MainBody", size=(0.4, 1.0, 0.3))
    hatch = sb.box("TopHatch", size=(0.3, 0.4, 0.04), loc=(0, 0.1, 0.18))
    sb.set_origin(hatch, (0, -0.1, 0.20))
    # cartridge floating above the opening, travelling down (-Z) through the hatch area
    sb.box("Cartridge", size=(0.06, 0.06, 0.2), loc=(0, 0.15, 0.45))
    cfg = {
        "moving_parts": {
            "TopHatch": {"type": "ROTATE", "axis": "X", "min": 0, "max": 110},
            "Cartridge": {"type": "TRANSLATE", "axis": "-Z", "min": 0, "max": 0.2},
        },
        "sweep_scenarios": [
            {"name": "reload_hatch_open", "set": {"TopHatch": "max"}, "sweep": "Cartridge"},
            {"name": "reload_hatch_closed", "set": {}, "sweep": "Cartridge"},
        ],
    }
    path = tmp_path / "eclipse1.json"
    path.write_text(json.dumps(cfg))
    res, _ = run(["MOV003"], config_path=str(path))
    scen = res["MOV003"]["details"]["scenarios"]
    assert scen["reload_hatch_open"] == "clear", scen
    assert isinstance(scen["reload_hatch_closed"], dict) and scen["reload_hatch_closed"]["against"] == "TopHatch", scen
    assert st(res, "MOV003") == "FAIL"
