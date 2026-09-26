"""ECLIPSE export copy: SOURCE .blend (untouched) → EXPORT .blend copy + FBX + manifest.

    blender -b Source/ECLIPSE1_SRC_v012.blend --python Tools/BlenderValidation/tools/eclipse_export.py -- \
        --collection ECLIPSE1_VM --name ECLIPSE1_VM --version 012 --out-dir Export/ECLIPSE1 \
        [--apply-modifiers] [--triangulate] [--profile viewmodel] [--dry-run]

What it does, in memory only (the SOURCE file on disk is never written):
  1. refuses to run on an unsaved/dirty file;
  2. optionally applies the evaluated modifier stack (--apply-modifiers) and adds a
     Triangulate modifier with keep_custom_normals (--triangulate) — FBX
     'use_triangles' is NOT used because it altered weighted normals by ~0.27° in
     our Blender 5.0.1 round-trip test, while Triangulate(keep_custom_normals) kept them exact;
  3. renames objects to their ``roblox_name`` custom property (so VM_/WM_ prefixed
     Blender names become the stable Roblox part names);
  4. runs the validator with stage=export and stores its report;
  5. saves <name>_EXPORT_v<version>.blend (copy), exports <name>_v<version>.fbx with the
     preset from config/eclipse_default.json and writes <name>_v<version>_manifest.json.

Status: Blender side tested on synthetic scenes with bpy 5.0.1.
NOT VERIFIED IN ROBLOX STUDIO — run tools/make_calibration_asset.py first.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import eclipse_validator as ev  # noqa: E402
from eclipse_validator import config as evconfig  # noqa: E402


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse(argv):
    p = argparse.ArgumentParser(prog="eclipse_export")
    p.add_argument("--collection", required=True)
    p.add_argument("--name", required=True, help="asset name, e.g. ECLIPSE1_VM")
    p.add_argument("--version", required=True, help="3-digit version, e.g. 012")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--profile", default="viewmodel")
    p.add_argument("--config")
    p.add_argument("--apply-modifiers", action="store_true")
    p.add_argument("--triangulate", action="store_true")
    p.add_argument("--allow-fail", action="store_true", help="export even if the validator reports FAIL")
    p.add_argument("--dry-run", action="store_true", help="validate and plan, write nothing")
    return p.parse_args(argv)


def scope_objects(coll_name, cfg):
    import re
    coll = bpy.data.collections.get(coll_name)
    if coll is None:
        raise SystemExit(f"Collection '{coll_name}' not found")
    sc = cfg.get("scope", {})
    # proxies (hand proxy...) are validated for collisions but never exported
    pats = sc.get("exclude_collection_patterns", []) + sc.get("export_exclude_collection_patterns", [])
    out = []
    for ob in coll.all_objects:
        colls = [c.name for c in ob.users_collection]
        if colls and all(any(re.search(p, c) for p in pats) for c in colls):
            continue
        out.append(ob)
    return out


def apply_modifiers(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in objs:
        if ob.type != "MESH" or not ob.modifiers:
            continue
        ev_ob = ob.evaluated_get(dg)
        new_me = bpy.data.meshes.new_from_object(ev_ob, preserve_all_data_layers=True, depsgraph=dg)
        old = ob.data
        ob.modifiers.clear()
        ob.data = new_me
        if old.users == 0:
            bpy.data.meshes.remove(old)


def add_triangulate(objs):
    for ob in objs:
        if ob.type != "MESH":
            continue
        t = ob.modifiers.new("ECLIPSE_Triangulate", "TRIANGULATE")
        t.keep_custom_normals = True
        t.quad_method = "BEAUTY"
        t.ngon_method = "BEAUTY"
        # keep a Weighted Normal modifier last if one exists
        names = [m.name for m in ob.modifiers]
        wn = [m for m in ob.modifiers if m.type == "WEIGHTED_NORMAL"]
        if wn:
            idx = names.index(wn[-1].name)
            with bpy.context.temp_override(object=ob):
                bpy.ops.object.modifier_move_to_index(modifier=t.name, index=idx)


def rename_to_roblox(objs):
    renamed = {}
    # two passes to avoid transient name clashes
    for ob in objs:
        target = str(ob.get("roblox_name", "") or "")
        if target and target != ob.name:
            renamed[ob.name] = target
            ob.name = "__tmp__" + target
    for ob in objs:
        if ob.name.startswith("__tmp__"):
            ob.name = ob.name[len("__tmp__"):]
    bad = [ob.name for ob in objs if ob.name.endswith((".001", ".002", ".003"))]
    if bad:
        raise SystemExit(f"Name clash after roblox_name renaming: {bad} (another object already uses that name)")
    return renamed


def main(argv=None):
    if argv is None:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    a = parse(argv)
    cfg = evconfig.load_config(a.config)
    source = bpy.data.filepath
    if not source:
        raise SystemExit("Open a saved SOURCE .blend first.")
    # In background mode (blender -b) the file was just loaded from disk and
    # bpy.data.is_dirty is unreliable (always True without a window manager).
    if bpy.data.is_dirty and not bpy.app.background:
        raise SystemExit("Source has unsaved changes: save a new version first.")
    src_hash = sha256(source)
    objs = scope_objects(a.collection, cfg)
    plan = {"source": source, "objects": [o.name for o in objs], "apply_modifiers": a.apply_modifiers,
            "triangulate": a.triangulate}
    if a.apply_modifiers:
        apply_modifiers(objs)
    if a.triangulate:
        add_triangulate(objs)
    renamed = rename_to_roblox(objs)
    bpy.context.view_layer.update()

    rep = ev.run(profile=a.profile, stage="export", objects=[o.name for o in objs], config_path=a.config)
    fails = [r["rule_id"] for r in rep["results"] if r["status"] in ("FAIL", "ERROR") and r["rule_id"] != "EXP001"
             and r["rule_id"] != "EXP007"]
    base = f"{a.name}_v{a.version}"
    out_dir = os.path.abspath(a.out_dir)
    fbx_path = os.path.join(out_dir, base + ".fbx")
    blend_copy = os.path.join(out_dir, f"{a.name}_EXPORT_v{a.version}.blend")
    manifest_path = os.path.join(out_dir, base + "_manifest.json")
    if os.path.abspath(blend_copy) == os.path.abspath(source):
        raise SystemExit("Export copy path equals the source path — refusing.")
    for pth in (fbx_path, blend_copy):
        if os.path.exists(pth):
            raise SystemExit(f"Refusing to overwrite {pth}: bump --version.")
    if a.dry_run:
        print(json.dumps({"plan": plan, "renamed": renamed, "validator_fails": fails,
                          "would_write": [blend_copy, fbx_path, manifest_path]}, indent=2))
        return 0
    if fails and not a.allow_fail:
        print(f"[ECLIPSE] export blocked by validator FAIL: {fails}")
        ev.report.write_report(rep, out_dir, base + "_validation_BLOCKED")
        return 1

    os.makedirs(out_dir, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_copy, copy=True)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.hide_set(False)
        ob.select_set(True)
    preset = {k: v for k, v in cfg["export_preset"].items() if not k.startswith("_") and k != "format"}
    preset["object_types"] = set(preset.get("object_types", ["MESH", "EMPTY", "ARMATURE"]))
    bpy.ops.export_scene.fbx(filepath=fbx_path, use_selection=True, **preset)
    written = ev.report.write_report(rep, out_dir, base + "_validation")
    manifest = {
        "asset": a.name, "version": a.version,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "blender_version": bpy.app.version_string,
        "source_blend": source, "source_sha256": src_hash,
        "source_unchanged": sha256(source) == src_hash,
        "export_blend": blend_copy, "fbx": fbx_path, "fbx_sha256": sha256(fbx_path),
        "preset": {k: (sorted(v) if isinstance(v, set) else v) for k, v in preset.items()},
        "steps": plan, "renamed_to_roblox": renamed,
        "validator": {"overall": rep["summary"]["overall"], "counts": rep["summary"]["counts"],
                      "report": written["markdown"]},
        "roblox_import_settings": {"World Forward": "Front", "World Up": "Top", "Scale Unit": "Stud",
                                   "Set Pivot to Scene Origin": True, "Use Imported Pivot": True,
                                   "Upload to Roblox": "only when validated", "Merge Meshes": False},
        "roblox_status": "NOT IMPORTED — fill after import (asset ids, screenshots)",
    }
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"[ECLIPSE] exported {fbx_path}\n[ECLIPSE] manifest {manifest_path}")
    return 0


if __name__ == "__main__":
    code = main()
    if "--" in sys.argv:
        sys.exit(code)
