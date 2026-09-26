"""Create the ECLIPSE Blender→Roblox calibration file (a NEW .blend, nothing else touched).

    blender -b --python Tools/BlenderValidation/tools/make_calibration_asset.py -- \
        --out Calibration/ECLIPSE_CAL_Orientation_v001.blend [--forward -Y]

The file contains simple, asymmetric test objects whose expected Roblox results
are written next to it (``*_EXPECTED.md``). Export it with the ECLIPSE preset
(tools/eclipse_export.py), import it in Roblox Studio with the documented
settings, and compare. This is how the local agent PROVES the orientation,
scale, pivot, attachment and normals behaviour instead of assuming it.
"""

import argparse
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

AXES = {"+X": (1, 0, 0), "-X": (-1, 0, 0), "+Y": (0, 1, 0), "-Y": (0, -1, 0)}


def _box(name, size, loc, coll):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.location = loc
    return ob


def _arrow(name, forward, coll):
    """Long box + wedge tip pointing to ``forward`` (XY plane)."""
    f = Vector(AXES[forward])
    side = Vector((-f.y, f.x, 0))
    verts, faces = [], []
    L, W, H = 1.0, 0.12, 0.08
    body = [(-W, 0), (W, 0), (W, L), (-W, L)]
    tip = [(-2.2 * W, L), (2.2 * W, L), (0, L + 0.35)]
    for z in (-H, H):
        for s, t in body + tip:
            p = side * s + f * t
            verts.append((p.x, p.y, z))
    n = len(body) + len(tip)
    faces += [(0, 1, 2, 3), (n + 3, n + 2, n + 1, n)]           # body bottom/top
    faces += [(4, 5, 6), (n + 6, n + 5, n + 4)]                 # tip bottom/top
    ring_body = [0, 1, 2, 3]
    for k in range(4):
        a, b = ring_body[k], ring_body[(k + 1) % 4]
        faces.append((a, b, b + n, a + n))
    for a, b in ((4, 5), (5, 6), (6, 4)):
        faces.append((a, b, b + n, a + n))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def build(forward: str):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "NONE"
    sc.unit_settings.scale_length = 1.0
    coll = bpy.data.collections.new("ECLIPSE_CAL")
    sc.collection.children.link(coll)
    f = Vector(AXES[forward])
    right = f.cross(Vector((0, 0, 1)))  # shooter's right when looking along forward, Z up

    arrow = _arrow("CAL_Arrow", forward, coll)
    tip = bpy.data.objects.new("Muzzle_Att", None)
    coll.objects.link(tip)
    tip.parent = arrow
    tip.location = f * 1.35
    rmark = _box("CAL_RightMarker", (0.15, 0.15, 0.15), right * 0.6, coll)

    _box("CAL_Cube_1x1x1", (1, 1, 1), (3, 0, 0), coll)
    _box("CAL_Box_X1_Y2_Z4", (1, 2, 4), (6, 0, 0), coll)

    piv = _box("CAL_PivotOffset", (0.2, 1.0, 0.2), (0, 0, 3), coll)
    # origin moved to one end of the bar: Roblox should expose it as PivotOffset
    bpy.context.view_layer.update()
    local = Vector((0, -0.5, 0))
    piv.data.transform(Matrix.Translation(-local))
    piv.matrix_world = piv.matrix_world @ Matrix.Translation(local)

    hinge = bpy.data.objects.new("CAL_Hinge_Att", None)
    coll.objects.link(hinge)
    hinge.parent = piv
    hinge.location = (0, 0, 0.1)
    hinge.rotation_euler = (0, 0, math.radians(30))

    wn = _box("CAL_WeightedNormals", (1.0, 0.5, 0.25), (-3, 0, 0), coll)
    for p in wn.data.polygons:
        p.use_smooth = True
    b = wn.modifiers.new("Bevel", "BEVEL")
    b.width = 0.03
    b.segments = 1
    w = wn.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    w.weight = 100
    w.keep_sharp = True
    soft = _box("CAL_SmoothNoWN", (1.0, 0.5, 0.25), (-3, 0, 1.0), coll)
    for p in soft.data.polygons:
        p.use_smooth = True
    b2 = soft.modifiers.new("Bevel", "BEVEL")
    b2.width = 0.03
    b2.segments = 1
    for ob in coll.objects:
        ob["roblox_name"] = ob.name
    return right


EXPECTED = """# ECLIPSE calibration — expected Roblox results (forward = {forward})

Import settings: File Transform World Forward = Front, World Up = Top; File Geometry Scale Unit = Stud;
Set Pivot to Scene Origin = on; Use Imported Pivot = on (default). Export with tools/eclipse_export.py.

| Test | Blender | Expected in Roblox Studio | Status |
|---|---|---|---|
| Scale | CAL_Cube_1x1x1 is 1×1×1 BU | MeshPart.Size = 1, 1, 1 | ☐ |
| Axis mapping | CAL_Box_X1_Y2_Z4 is X=1, Y=2, Z=4 | Size = (1, 4, 2): Blender Z→Roblox Y (up), Blender Y→Roblox Z | ☐ |
| Forward | CAL_Arrow + Muzzle_Att point to Blender {forward} | Arrow tip toward the model's LookVector (-Z) | ☐ |
| Right | CAL_RightMarker at Blender {right} | Marker on +X (RightVector) of the model | ☐ |
| Pivot | CAL_PivotOffset origin at one end | Part pivot (PivotOffset) at that end, CFrame at bbox centre | ☐ |
| Attachment | CAL_Hinge_Att (Empty, child of CAL_PivotOffset, rotated 30° about Blender Z) | Attachment under CAL_PivotOffset, 30° about Roblox Y | ☐ |
| Normals | CAL_WeightedNormals vs CAL_SmoothNoWN | WN box: flat large faces, soft highlight only on chamfers; the other shows gradients | ☐ |

If Forward/Right fail but everything else passes, switch the preset (FBX Forward Z ↔ -Z) or set
orientation.blender_forward (+Y/-Y) in the validator config — then re-run this calibration.
Record the result in Knowledge/Blender/CALIBRATION_LOG.md (date, Blender/Studio versions, preset, outcome).
"""


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--forward", default="-Y", choices=sorted(AXES))
    a = p.parse_args(argv)
    out = os.path.abspath(a.out)
    if os.path.exists(out):
        raise SystemExit(f"Refusing to overwrite {out}")
    right = build(a.forward)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    rname = {(1, 0, 0): "+X", (-1, 0, 0): "-X", (0, 1, 0): "+Y", (0, -1, 0): "-Y"}[tuple(round(c) for c in right)]
    with open(os.path.splitext(out)[0] + "_EXPECTED.md", "w", encoding="utf-8") as fh:
        fh.write(EXPECTED.format(forward=a.forward, right=rname))
    print(f"[ECLIPSE] calibration file written: {out}")


if __name__ == "__main__":
    main()
