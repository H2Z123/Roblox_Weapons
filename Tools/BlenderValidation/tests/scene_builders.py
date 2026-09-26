"""Synthetic scenes for the bpy integration tests (NOT ECLIPSE-1 data)."""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "NONE"
    bpy.context.scene.unit_settings.scale_length = 1.0


def collection(name):
    coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    return coll


def box(name, size=(1.0, 0.5, 0.25), loc=(0, 0, 0), coll=None, uv=True):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    if uv:
        bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=uv)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    return ob


def plane(name, coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def t_junction_mesh(name):
    """Two quads side by side; the right one has an extra vertex on the shared border
    (not welded): a classic T-junction."""
    verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),        # left quad
             (1, 0, 0), (2, 0, 0), (2, 1, 0), (1, 1, 0), (1, 0.5, 0)]  # right quad + mid vertex
    faces = [(0, 1, 2, 3), (4, 5, 6, 7, 8)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def material(name, metallic=0.0, base=(0.8, 0.8, 0.8, 1.0), roughness=0.5):
    mat = bpy.data.materials.new(name)
    if mat.node_tree is None:  # Blender < 5 needs use_nodes; 5.x materials always have a tree
        mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def empty(name, loc=(0, 0, 0), rot_deg=(0, 0, 0), parent=None, coll=None):
    ob = bpy.data.objects.new(name, None)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot_deg]
    if parent is not None:
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob


def set_origin(ob, world_point):
    """Move the object origin to world_point without moving the geometry."""
    bpy.context.view_layer.update()  # matrix_world is stale right after setting .location
    wp = Vector(world_point)
    local = ob.matrix_world.inverted() @ wp
    ob.data.transform(Matrix.Translation(-local))
    ob.matrix_world = ob.matrix_world @ Matrix.Translation(local)


def dense_grid(name, subdiv=110):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=subdiv, y_subdivisions=subdiv, size=1)
    ob = bpy.context.active_object
    ob.name = name
    return ob
