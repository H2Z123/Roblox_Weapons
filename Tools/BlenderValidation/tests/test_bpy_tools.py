"""Tests for tools/make_calibration_asset.py and tools/eclipse_export.py (requires bpy)."""

import hashlib
import importlib
import json
import os
import subprocess
import sys

import pytest

from conftest import HAS_BPY, ROOT, requires_bpy

pytestmark = requires_bpy

if HAS_BPY:
    import bpy
    import scene_builders as sb

TOOLS = os.path.join(ROOT, "tools")


def _run_script(script, args, blend=None):
    pre = f"bpy.ops.wm.open_mainfile(filepath={blend!r})\n" if blend else ""
    code = ("import bpy, sys, runpy\n" + pre +
            f"sys.argv = ['x', '--'] + {args!r}\n"
            f"runpy.run_path({script!r}, run_name='__main__')\n")
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300)


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def test_calibration_asset(tmp_path):
    out = str(tmp_path / "Calibration" / "ECLIPSE_CAL_Orientation_v001.blend")
    proc = _run_script(os.path.join(TOOLS, "make_calibration_asset.py"), ["--out", out])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert os.path.exists(out)
    expected = open(out.replace(".blend", "_EXPECTED.md"), encoding="utf-8").read()
    assert "Size = (1, 4, 2)" in expected and "RightMarker at Blender -X" in expected.replace("CAL_RightMarker at Blender", "RightMarker at Blender")
    # refuses to overwrite
    proc = _run_script(os.path.join(TOOLS, "make_calibration_asset.py"), ["--out", out])
    assert proc.returncode != 0
    # the calibration arrow passes the forward check
    bpy.ops.wm.open_mainfile(filepath=out)
    import eclipse_validator as ev
    rep = ev.run(profile="source", rules=["ORI001", "GEO006", "PIV004"])
    res = {r["rule_id"]: r["status"] for r in rep["results"]}
    assert res["ORI001"] == "PASS", rep["results"]
    assert res["GEO006"] == "PASS"


def _parse_fbx(path):
    pf = importlib.import_module("io_scene_fbx.parse_fbx")
    root, _ver = pf.parse(path)
    names, unit = [], None
    for e in root.elems:
        if e.id == b"Objects":
            for g in e.elems:
                if g.id == b"Model":
                    names.append(g.props[1].split(b"\x00")[0].decode())
        if e.id == b"GlobalSettings":
            for sub in e.elems:
                if sub.id == b"Properties70":
                    for p in sub.elems:
                        if p.props and p.props[0] == b"UnitScaleFactor":
                            unit = p.props[-1]
    return names, unit


def test_export_copy_leaves_source_untouched(tmp_path):
    sb.reset()
    vm = sb.collection("ECLIPSE1_VM")
    body = sb.box("ECLIPSE1_VM_MainBody", size=(0.4, 1.0, 0.3), coll=vm)
    body["roblox_name"] = "MainBody"
    for p in body.data.polygons:
        p.use_smooth = True
    b = body.modifiers.new("Bevel", "BEVEL")
    b.width = 0.01
    b.segments = 1
    w = body.modifiers.new("WN", "WEIGHTED_NORMAL")
    w.weight = 100
    w.keep_sharp = True
    body.data.materials.append(sb.material("M_ECLIPSE1_Body", metallic=0.0, base=(0.05, 0.05, 0.05, 1)))
    hatch = sb.box("ECLIPSE1_VM_TopHatch", size=(0.3, 0.4, 0.04), loc=(0, 0.1, 0.18), coll=vm)
    hatch["roblox_name"] = "TopHatch"
    hatch.data.materials.append(bpy.data.materials["M_ECLIPSE1_Body"])
    cut = sb.collection("ECLIPSE1_VM_Cutters")
    vm.children.link(cut)
    bpy.context.scene.collection.children.unlink(cut)
    c = sb.box("Cutter_Slot", size=(0.1, 0.1, 0.5), coll=cut)
    m = body.modifiers.new("Bool", "BOOLEAN")
    m.object = c
    with bpy.context.temp_override(object=body):
        bpy.ops.object.modifier_move_to_index(modifier="Bool", index=0)
    src = str(tmp_path / "ECLIPSE1_SRC_v001.blend")
    bpy.ops.wm.save_as_mainfile(filepath=src)
    before = _sha(src)
    out = str(tmp_path / "Export")
    args = ["--collection", "ECLIPSE1_VM", "--name", "ECLIPSE1_VM", "--version", "001", "--out-dir", out,
            "--apply-modifiers", "--triangulate", "--allow-fail"]
    proc = _run_script(os.path.join(TOOLS, "eclipse_export.py"), args, blend=src)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _sha(src) == before, "source file was modified"
    fbx = os.path.join(out, "ECLIPSE1_VM_v001.fbx")
    man = json.load(open(os.path.join(out, "ECLIPSE1_VM_v001_manifest.json")))
    assert man["source_unchanged"] is True
    assert man["renamed_to_roblox"] == {"ECLIPSE1_VM_MainBody": "MainBody", "ECLIPSE1_VM_TopHatch": "TopHatch"}
    names, unit = _parse_fbx(fbx)
    assert "MainBody" in names and "TopHatch" in names
    assert "Cutter_Slot" not in names, "cutter leaked into the FBX"
    assert unit == pytest.approx(100.0)  # FBX_SCALE_UNITS: geometry 1:1, UnitScaleFactor 100
    assert os.path.exists(os.path.join(out, "ECLIPSE1_VM_EXPORT_v001.blend"))
    # second run refuses to overwrite the same version
    proc = _run_script(os.path.join(TOOLS, "eclipse_export.py"), args, blend=src)
    assert proc.returncode != 0
