"""Planche de test de la bibliothèque LastOne : par matière, sphère + cube procéduraux + cube refait avec les 4 cartes 1024.

  python build_board.py <dossier_sortie> [taille_bake=1024] [échantillons_rendu=64]
Écrit : <sortie>/textures/<Matière>/T_LO_<Matière>_{Color,Normal,Roughness,Metalness}.png,
        <sortie>/rendus/<Matière>.png, <sortie>/planche_materiaux_v01.png, <sortie>/LO_Materiaux_v01.blend
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lastone_materials as lom  # noqa: E402

OUT = os.path.abspath(sys.argv[1])
SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
SPP = int(sys.argv[3]) if len(sys.argv) > 3 else 64
ONLY = sys.argv[4].split(",") if len(sys.argv) > 4 else list(lom.PRESETS)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1200, 520
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Base Contrast"
sc.view_settings.exposure = -0.6


def link(o):
    sc.collection.objects.link(o)
    return o


# ------------------------------------------------------------------ objets de test
def uv_sphere(name, x):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=0.5, location=(x, 0, 0))
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    return o


def bevel_cube(name, x):
    bpy.ops.mesh.primitive_cube_add(size=0.82, location=(x, 0, 0), rotation=(math.radians(22), 0, math.radians(38)))
    o = bpy.context.active_object
    o.name = name
    m = o.modifiers.new("Bevel", "BEVEL")
    m.width, m.segments, m.limit_method = 0.035, 4, "NONE"
    bpy.ops.object.modifier_apply(modifier="Bevel")
    bpy.ops.object.shade_smooth()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    o.data.uv_layers[0].name = "UVMap"
    return o


sphere = uv_sphere("LO_Test_Sphere", -1.25)
cube = bevel_cube("LO_Test_Cube", 0.0)
cube_bk = bevel_cube("LO_Test_Cube_Cartes", 1.25)

# ------------------------------------------------------------------ studio (aucune image : dégradé + panneaux lumineux)
w = bpy.data.worlds.new("LO_Studio")
sc.world = w
w.use_nodes = True
wn = w.node_tree
bg = wn.nodes["Background"]
tc = wn.nodes.new("ShaderNodeTexCoord")
sep = wn.nodes.new("ShaderNodeSeparateXYZ")
ramp = wn.nodes.new("ShaderNodeValToRGB")
wn.links.new(tc.outputs["Generated"], sep.inputs[0])
wn.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.35, (0.012, 0.012, 0.014, 1)
ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.75, (0.16, 0.165, 0.18, 1)
wn.links.new(ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0


def area(name, loc, rot, size, energy, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape, ld.size, ld.energy, ld.color = "RECTANGLE", size, energy, color
    ld.size_y = size * 0.5
    o = link(bpy.data.objects.new(name, ld))
    o.location, o.rotation_euler = loc, rot
    return o


area("Key", (-2.5, -3.0, 3.2), (math.radians(50), 0, math.radians(-38)), 3.0, 900)
area("Fill", (3.5, -2.5, 0.8), (math.radians(78), 0, math.radians(55)), 3.0, 250, (0.85, 0.9, 1.0))
area("Rim", (0.5, 3.5, 2.5), (math.radians(-55), 0, math.radians(180)), 4.0, 700)
# panneau visible seulement dans les reflets (les métaux en ont besoin)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -2.8, 2.6), rotation=(math.radians(-60), 0, 0))
soft = bpy.context.active_object
soft.scale = (6, 1.2, 1)
sm = bpy.data.materials.new("LO_Softbox")
sm.use_nodes = True
sm.node_tree.nodes.clear()
e = sm.node_tree.nodes.new("ShaderNodeEmission")
e.inputs["Strength"].default_value = 3.0
o_ = sm.node_tree.nodes.new("ShaderNodeOutputMaterial")
sm.node_tree.links.new(e.outputs[0], o_.inputs[0])
soft.data.materials.append(sm)
soft.visible_camera = False
soft.visible_diffuse = False

cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 70
cam = link(bpy.data.objects.new("Cam", cam_d))
cam.location = (0, -7.6, 1.55)
cam.rotation_euler = (math.radians(79), 0, 0)
sc.camera = cam

# ------------------------------------------------------------------ boucle matières
os.makedirs(os.path.join(OUT, "rendus"), exist_ok=True)
report = {}
for name in ONLY:
    mat = lom.make_material(name)
    for o in (sphere, cube, cube_bk):
        o.data.materials.clear()
    sphere.data.materials.append(mat)
    cube.data.materials.append(mat)
    # bake sur une copie du cube (le cube « cartes » est au même endroit relatif : on bake celui-là)
    cube_bk.data.materials.append(mat)
    maps = lom.bake_roblox_maps(cube_bk, os.path.join(OUT, "textures", name), f"T_LO_{name}", size=SIZE)
    report[name] = maps
    cube_bk.data.materials.clear()
    cube_bk.data.materials.append(lom.baked_material(f"M_LO_{name}_Cartes{SIZE}", maps))
    sc.cycles.samples = SPP
    sc.render.filepath = os.path.join(OUT, "rendus", f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("LO_RENDER_OK", name, flush=True)

# fichier de travail : une rangée par matière, prête à régler dans Blender
for o in (sphere, cube, cube_bk):
    o.data.materials.clear()
for i, name in enumerate(lom.PRESETS):
    for src in (sphere, cube):
        c = src.copy()
        c.data = src.data.copy()
        c.name = f"{src.name}_{name}"
        c.location.z = -1.3 * (i + 1)
        c.data.materials.append(bpy.data.materials.get(f"M_LO_{name}") or lom.make_material(name))
        link(c)
bpy.data.objects.remove(cube_bk)
sc.render.filepath = ""
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "LO_Materiaux_v01.blend"))
print("LO_BOARD_OK", report)
