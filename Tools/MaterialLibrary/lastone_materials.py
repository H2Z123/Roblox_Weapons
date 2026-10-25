"""LastOne — bibliothèque de matières procédurales (Blender 5.x, sans aucune image).

Chaque matière est un groupe de nœuds « LO_<Nom> » avec la même interface réglable :
  Couleur, Couleur usure, Usure, Rugosité, Rugosité usure, Métal, Métal usure,
  Rayures, Relief, Saleté, Échelle
Un skin = la même matière avec d'autres valeurs (voir make_skin).

Utilisation dans Blender (ou avec le module pip bpy) :
    import lastone_materials as lom
    mat = lom.make_material("AcierNoir")                     # réglages par défaut
    skin = lom.make_skin("AcierNoir", "Skin_Rouille", Couleur=(0.25, 0.08, 0.03), Usure=0.8)
    obj.data.materials.append(mat)
    lom.bake_roblox_maps(obj, "/chemin/textures", "T_ION_Coque", size=1024)

Moteur : Cycles (le masque d'arêtes utilise le nœud Bevel, l'usure n'apparaît qu'en Cycles et au bake).
Échelle : les motifs sont pensés pour un objet d'environ 1 unité Blender. Pour une pièce plus petite
ou plus grande, régler « Échelle » (ex. pièce de 0,25 unité -> Échelle = 4).
"""
import os

import bpy


def srgb(hex_or_rgb):
    """'#80282E' ou (128, 40, 46) -> couleur linéaire Blender (r, g, b)."""
    if isinstance(hex_or_rgb, str):
        h = hex_or_rgb.lstrip("#")
        rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    else:
        rgb = hex_or_rgb
    f = lambda c: (c / 255) / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4
    return tuple(f(c) for c in rgb)


# ------------------------------------------------------------------ réglages par défaut (premier lot)
# motif : microrayures | grave | caoutchouc | peinture | brosse
PRESETS = {
    "AcierNoir": dict(
        label="Acier noir mat microrayé", motif="microrayures",
        Couleur=srgb("#1C1D20"), Couleur_usure=srgb("#C4C7CB"), Usure=0.55,
        Rugosite=0.62, Rugosite_usure=0.34, Metal=0.0, Metal_usure=1.0,
        Rayures=0.6, Relief=0.25, Salete=0.15, Echelle=1.0),
    "OrGrave": dict(
        label="Or gravé (vrai métal)", motif="grave",
        Couleur=srgb("#FFE29D"), Couleur_usure=srgb("#FFF0C8"), Usure=0.35,
        Rugosite=0.28, Rugosite_usure=0.16, Metal=1.0, Metal_usure=1.0,
        Rayures=0.5, Relief=0.6, Salete=0.12, Echelle=1.0),
    "CaoutchoucPoignee": dict(
        label="Caoutchouc / polymère de poignée", motif="caoutchouc",
        Couleur=srgb("#1E1F21"), Couleur_usure=srgb("#3C3E42"), Usure=0.45,
        Rugosite=0.82, Rugosite_usure=0.55, Metal=0.0, Metal_usure=0.0,
        Rayures=0.2, Relief=1.0, Salete=0.2, Echelle=1.0),
    "PanneauGris": dict(
        label="Panneau gris", motif="peinture",
        Couleur=srgb("#5C5F65"), Couleur_usure=srgb("#8C8F96"), Usure=0.45,
        Rugosite=0.55, Rugosite_usure=0.45, Metal=0.0, Metal_usure=0.0,
        Rayures=0.35, Relief=0.2, Salete=0.15, Echelle=1.0),
    "AcierBrosse": dict(
        label="Acier brossé terni", motif="brosse",
        Couleur=srgb("#92959A"), Couleur_usure=srgb("#BABDC2"), Usure=0.4,
        Rugosite=0.48, Rugosite_usure=0.3, Metal=1.0, Metal_usure=1.0,
        Rayures=0.45, Relief=0.25, Salete=0.25, Echelle=1.0),
    "BordeauxModule": dict(
        label="Bordeaux du module #80282E", motif="peinture",
        Couleur=srgb("#80282E"), Couleur_usure=srgb("#A8ABB0"), Usure=0.4,
        Rugosite=0.42, Rugosite_usure=0.3, Metal=0.0, Metal_usure=1.0,
        Rayures=0.3, Relief=0.15, Salete=0.1, Echelle=1.0),
}

# (nom du socket, type, défaut, min, max)
INPUTS = [
    ("Couleur", "NodeSocketColor", None, None, None),
    ("Couleur usure", "NodeSocketColor", None, None, None),
    ("Usure", "NodeSocketFloat", 0.5, 0.0, 1.0),
    ("Rugosité", "NodeSocketFloat", 0.5, 0.0, 1.0),
    ("Rugosité usure", "NodeSocketFloat", 0.3, 0.0, 1.0),
    ("Métal", "NodeSocketFloat", 0.0, 0.0, 1.0),
    ("Métal usure", "NodeSocketFloat", 1.0, 0.0, 1.0),
    ("Rayures", "NodeSocketFloat", 0.5, 0.0, 1.0),
    ("Relief", "NodeSocketFloat", 0.3, 0.0, 2.0),
    ("Saleté", "NodeSocketFloat", 0.2, 0.0, 1.0),
    ("Échelle", "NodeSocketFloat", 1.0, 0.01, 100.0),
]
# clé de PRESETS (sans accents) -> nom du socket
KEY2SOCK = {"Couleur": "Couleur", "Couleur_usure": "Couleur usure", "Usure": "Usure",
            "Rugosite": "Rugosité", "Rugosite_usure": "Rugosité usure", "Metal": "Métal",
            "Metal_usure": "Métal usure", "Rayures": "Rayures", "Relief": "Relief",
            "Salete": "Saleté", "Echelle": "Échelle"}


# ------------------------------------------------------------------ petit assistant de nœuds
class _G:
    def __init__(self, tree):
        self.t, self.n, self.l = tree, tree.nodes, tree.links

    def link(self, a, b):
        self.l.new(a, b)

    def _set(self, sock, v):
        if v is None:
            return
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = (*v, 1.0) if len(v) == 3 and sock.type == "RGBA" else v
        else:
            self.link(v, sock)

    def math(self, op, a, b=None, clamp=False):
        m = self.n.new("ShaderNodeMath")
        m.operation, m.use_clamp = op, clamp
        self._set(m.inputs[0], a)
        if b is not None:
            self._set(m.inputs[1], b)
        return m.outputs[0]

    def vmath(self, op, a, b):
        m = self.n.new("ShaderNodeVectorMath")
        m.operation = op
        self._set(m.inputs[0], a)
        self._set(m.inputs[1], b)
        return m.outputs[0]

    def maprange(self, v, a, b, c=0.0, d=1.0, smooth=False):
        m = self.n.new("ShaderNodeMapRange")
        m.clamp = True
        if smooth:
            m.interpolation_type = "SMOOTHSTEP"
        self._set(m.inputs["Value"], v)
        for s, x in (("From Min", a), ("From Max", b), ("To Min", c), ("To Max", d)):
            self._set(m.inputs[s], x)
        return m.outputs["Result"]

    def mix(self, fac, a, b, kind="RGBA"):
        m = self.n.new("ShaderNodeMix")
        m.data_type = kind
        want = "RGBA" if kind == "RGBA" else "VALUE"
        self._set(m.inputs["Factor"], fac)
        ins = [i for i in m.inputs if i.type == want and i.name in ("A", "B")]
        self._set(ins[0], a)
        self._set(ins[1], b)
        return [o for o in m.outputs if o.type == want][0]

    def mapping(self, vec, scale=(1, 1, 1), rot=(0, 0, 0)):
        m = self.n.new("ShaderNodeMapping")
        self._set(m.inputs["Vector"], vec)
        m.inputs["Scale"].default_value = scale
        m.inputs["Rotation"].default_value = rot
        return m.outputs["Vector"]

    def noise(self, vec, scale, detail=4.0, rough=0.55, dist=0.0, dims="3D"):
        t = self.n.new("ShaderNodeTexNoise")
        t.noise_dimensions = dims
        self._set(t.inputs["Vector"], vec)
        t.inputs["Scale"].default_value = scale
        t.inputs["Detail"].default_value = detail
        t.inputs["Roughness"].default_value = rough
        t.inputs["Distortion"].default_value = dist
        return t.outputs["Fac"]

    def voronoi(self, vec, scale, feature="F1", rand=1.0):
        t = self.n.new("ShaderNodeTexVoronoi")
        t.feature = feature
        self._set(t.inputs["Vector"], vec)
        t.inputs["Scale"].default_value = scale
        t.inputs["Randomness"].default_value = rand
        return t.outputs["Distance"]

    def wave(self, vec, scale, dist, detail=2.0, kind="BANDS", profile="SIN"):
        t = self.n.new("ShaderNodeTexWave")
        t.wave_type, t.wave_profile = kind, profile
        self._set(t.inputs["Vector"], vec)
        t.inputs["Scale"].default_value = scale
        t.inputs["Distortion"].default_value = dist
        t.inputs["Detail"].default_value = detail
        return t.outputs["Fac"]


def _scratch_plane(g, u, v, scale, stretch, angle, width, seed):
    """Rayures fines dans un plan : bords de cellules Voronoi 2D très étirées, gardées au hasard."""
    cmb = g.n.new("ShaderNodeCombineXYZ")
    g._set(cmb.inputs["X"], u)
    g._set(cmb.inputs["Y"], v)
    cmb.inputs["Z"].default_value = seed
    rot = g.mapping(cmb.outputs["Vector"], rot=(0, 0, angle))
    st = g.mapping(rot, scale=(1.0, stretch, 1.0))
    t = g.n.new("ShaderNodeTexVoronoi")
    t.voronoi_dimensions, t.feature = "2D", "DISTANCE_TO_EDGE"
    g.link(st, t.inputs["Vector"])
    t.inputs["Scale"].default_value = scale
    line = g.maprange(t.outputs["Distance"], 0.0, width, 1.0, 0.0)
    keep = g.maprange(g.noise(cmb.outputs["Vector"], 2.5, 2.0), 0.54, 0.68)
    return g.math("MULTIPLY", line, keep)


def _scratches(g, co, normal):
    """Rayures projetées sur les 3 plans (X, Y, Z) et fondues selon la normale : pas de « fissures »."""
    sep = g.n.new("ShaderNodeSeparateXYZ")
    g._set(sep.inputs[0], co)
    X, Y, Z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
    nsep = g.n.new("ShaderNodeSeparateXYZ")
    g._set(nsep.inputs[0], normal)
    ws = [g.math("POWER", g.math("ABSOLUTE", nsep.outputs[a]), 4.0) for a in ("X", "Y", "Z")]
    tot = g.math("ADD", g.math("ADD", ws[0], ws[1]), ws[2])
    acc = None
    for (u, v), w, seed in (((Y, Z), ws[0], 1.3), ((X, Z), ws[1], 2.7), ((X, Y), ws[2], 4.1)):
        a = _scratch_plane(g, u, v, 5.0, 0.04, 0.5, 0.006, seed)
        b = _scratch_plane(g, u, v, 7.0, 0.035, -0.9, 0.005, seed + 0.5)
        layer = g.math("MULTIPLY", g.math("MAXIMUM", a, b), g.math("DIVIDE", w, tot))
        acc = layer if acc is None else g.math("ADD", acc, layer)
    return acc


def _build_group(name, motif):
    """Crée (ou recrée) le groupe LO_<name> pour un motif donné."""
    gname = f"LO_{name}"
    old = bpy.data.node_groups.get(gname)
    if old:
        bpy.data.node_groups.remove(old)
    tree = bpy.data.node_groups.new(gname, "ShaderNodeTree")
    for sname, stype, dflt, mn, mx in INPUTS:
        s = tree.interface.new_socket(sname, in_out="INPUT", socket_type=stype)
        if dflt is not None:
            s.default_value = dflt
            s.min_value, s.max_value = mn, mx
    for sname, stype in (("Couleur", "NodeSocketColor"), ("Rugosité", "NodeSocketFloat"),
                         ("Métal", "NodeSocketFloat"), ("Normale", "NodeSocketVector")):
        tree.interface.new_socket(sname, in_out="OUTPUT", socket_type=stype)
    g = _G(tree)
    gi = g.n.new("NodeGroupInput")
    go = g.n.new("NodeGroupOutput")
    I = gi.outputs
    tc = g.n.new("ShaderNodeTexCoord")
    geo = g.n.new("ShaderNodeNewGeometry")
    co = g.vmath("MULTIPLY", tc.outputs["Object"], I["Échelle"])

    # --- masque d'arêtes (Bevel vs normale réelle), cassé par un bruit
    bv = g.n.new("ShaderNodeBevel")
    bv.samples = 8
    bv.inputs["Radius"].default_value = 0.05
    dn = g.n.new("ShaderNodeVectorMath")
    dn.operation = "DOT_PRODUCT"
    g.link(bv.outputs["Normal"], dn.inputs[0])
    g.link(geo.outputs["Normal"], dn.inputs[1])
    dot = dn.outputs["Value"]
    edge = g.maprange(g.math("SUBTRACT", 1.0, dot), 0.001, 0.02)
    brk = g.noise(co, 9.0, 6.0, 0.62)
    edge_brk = g.maprange(g.math("MULTIPLY", edge, g.math("ADD", g.maprange(brk, 0.35, 0.65), 0.25)), 0.25, 0.6, smooth=True)
    # Usure 0 -> rien, 1 -> arêtes franches très marquées
    wear = g.math("MULTIPLY", edge_brk, g.maprange(I["Usure"], 0.0, 1.0, 0.0, 1.6), clamp=True)

    # --- motif propre à la matière : height (relief), micro (variation rugosité), extra (rayures/creux)
    scr = _scratches(g, co, geo.outputs["Normal"])
    scr = g.math("MULTIPLY", scr, I["Rayures"])
    cavity = None
    if motif == "microrayures":
        fine = g.noise(co, 180.0, 3.0, 0.5)
        height = g.math("SUBTRACT", g.math("MULTIPLY", fine, 0.15), g.math("MULTIPLY", scr, 0.5))
        micro = g.maprange(g.noise(co, 4.0, 5.0, 0.6), 0.3, 0.7, -0.06, 0.06)
        reveal = g.math("MULTIPLY", scr, 0.85)          # les rayures montrent le métal dessous
    elif motif == "grave":
        # gravure croisée : deux familles de plans fins (lignes droites sur toutes les faces), creusées dans l'or
        w1 = g.wave(g.mapping(co, rot=(0.0, 0.6, 0.79)), 14.0, 0.0, 0.0, "BANDS", "SIN")
        w2 = g.wave(g.mapping(co, rot=(0.5, -0.6, -0.79)), 14.0, 0.0, 0.0, "BANDS", "SIN")
        groove = g.math("MAXIMUM", g.maprange(w1, 0.0, 0.12, 1.0, 0.0, smooth=True),
                        g.maprange(w2, 0.0, 0.12, 1.0, 0.0, smooth=True))
        cavity = groove
        height = g.math("SUBTRACT", 0.0, g.math("ADD", groove, g.math("MULTIPLY", scr, 0.3)))
        micro = g.maprange(g.noise(co, 5.0, 4.0, 0.6), 0.3, 0.7, -0.05, 0.05)
        reveal = g.math("MULTIPLY", scr, 0.5)
    elif motif == "caoutchouc":
        stip = g.voronoi(co, 80.0, "F1")
        bumps = g.maprange(stip, 0.0, 0.5, 1.0, 0.0)
        height = g.math("ADD", g.math("MULTIPLY", bumps, 0.6), g.math("MULTIPLY", g.noise(co, 60.0, 3.0), 0.4))
        micro = g.maprange(g.noise(co, 6.0, 4.0, 0.6), 0.3, 0.7, -0.05, 0.05)
        reveal = g.math("MULTIPLY", scr, 0.4)
    elif motif == "brosse":
        streak = g.noise(g.mapping(co, scale=(2.0, 260.0, 260.0)), 1.0, 2.0, 0.5)
        height = g.math("SUBTRACT", g.math("MULTIPLY", streak, 0.6), g.math("MULTIPLY", scr, 0.4))
        micro = g.math("ADD", g.maprange(streak, 0.3, 0.7, -0.07, 0.07),
                       g.maprange(g.noise(co, 3.0, 4.0, 0.6), 0.3, 0.7, -0.05, 0.06))
        reveal = g.math("MULTIPLY", scr, 0.6)
    else:  # peinture
        orange = g.noise(co, 90.0, 2.0, 0.5)
        height = g.math("SUBTRACT", g.math("MULTIPLY", orange, 0.12), g.math("MULTIPLY", scr, 0.5))
        micro = g.maprange(g.noise(co, 4.0, 5.0, 0.6), 0.3, 0.7, -0.05, 0.06)
        reveal = g.math("MULTIPLY", scr, 0.8)

    # --- mélange base / usure
    expose = g.math("MAXIMUM", wear, reveal)
    col = g.mix(expose, I["Couleur"], I["Couleur usure"])
    if cavity is not None:   # fond de gravure : même métal, plus sombre et un peu plus mat
        dark = g.mix(1.0, col, (0.35, 0.3, 0.22))
        g.n[-1].blend_type = "MULTIPLY"
        col = g.mix(g.math("MULTIPLY", cavity, 0.6), col, dark)
    rough = g.mix(expose, g.math("ADD", I["Rugosité"], micro, clamp=True), I["Rugosité usure"], "FLOAT")
    metal = g.mix(expose, I["Métal"], I["Métal usure"], "FLOAT")

    # --- saleté légère dans les creux (AO) et la gravure
    ao = g.n.new("ShaderNodeAmbientOcclusion")
    ao.samples = 8
    ao.inputs["Distance"].default_value = 0.08
    dirt = g.maprange(ao.outputs["AO"], 0.4, 1.0, 1.0, 0.0)
    if cavity is not None:
        dirt = g.math("MAXIMUM", dirt, g.math("MULTIPLY", cavity, 0.35))
    dirt = g.math("MULTIPLY", g.math("MULTIPLY", dirt, I["Saleté"]), g.math("SUBTRACT", 1.0, wear), clamp=True)
    col = g.mix(g.math("MULTIPLY", dirt, 0.75), col, (0.012, 0.011, 0.010))
    rough = g.mix(dirt, rough, 0.85, "FLOAT")

    # --- relief
    bump = g.n.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.002
    g._set(bump.inputs["Strength"], g.math("MULTIPLY", I["Relief"], 0.5, clamp=True))
    g.link(height, bump.inputs["Height"])

    g.link(col, go.inputs["Couleur"])
    g.link(rough, go.inputs["Rugosité"])
    g.link(metal, go.inputs["Métal"])
    g.link(bump.outputs["Normal"], go.inputs["Normale"])
    tree["lastone_motif"] = motif
    return tree


def make_material(name, mat_name=None, **overrides):
    """Matière LastOne prête à poser. overrides : clés de PRESETS (Couleur, Usure, Rugosite…)."""
    preset = dict(PRESETS[name])
    preset.update(overrides)
    tree = bpy.data.node_groups.get(f"LO_{name}") or _build_group(name, preset["motif"])
    mat = bpy.data.materials.new(mat_name or f"M_LO_{name}")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    grp = nt.nodes.new("ShaderNodeGroup")
    grp.node_tree = tree
    grp.name = "LO_GROUP"
    grp.location, p.location, out.location = (-400, 0), (0, 0), (300, 0)
    for k, sock in KEY2SOCK.items():
        if k in preset:
            v = preset[k]
            grp.inputs[sock].default_value = (*v, 1.0) if isinstance(v, tuple) else v
    for a, b in (("Couleur", "Base Color"), ("Rugosité", "Roughness"), ("Métal", "Metallic"), ("Normale", "Normal")):
        nt.links.new(grp.outputs[a], p.inputs[b])
    nt.links.new(p.outputs["BSDF"], out.inputs["Surface"])
    mat["lastone_preset"] = name
    return mat


def make_skin(base, skin_name, **overrides):
    """Skin = même matière, autres valeurs. Ex. make_skin('OrGrave', 'Skin_OrRose', Couleur=srgb('#F2B8A0'))."""
    return make_material(base, f"M_LO_{base}_{skin_name}", **overrides)


# ------------------------------------------------------------------ bake des 4 cartes Roblox
def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def bake_roblox_maps(obj, out_dir, prefix, size=1024, samples=16, margin=8):
    """Bake ColorMap (sRGB), NormalMap (OpenGL, tangent), RoughnessMap, MetalnessMap pour SurfaceAppearance.

    obj doit avoir un jeu d'UV 0-1 sans chevauchement. Marche avec toute matière à Principled BSDF
    (pas seulement celles de la bibliothèque). Retourne {carte: chemin}. Ne touche pas aux matières à la fin.
    """
    sc = bpy.context.scene
    prev_engine = sc.render.engine
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.render.bake.margin = margin
    sc.render.bake.margin_type = "EXTEND"
    os.makedirs(out_dir, exist_ok=True)
    mats = [m for m in obj.data.materials if m]
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    def new_img(label, data):
        im = bpy.data.images.new(f"{prefix}_{label}", size, size, alpha=False)
        im.colorspace_settings.name = "Non-Color" if data else "sRGB"
        for m in mats:
            nt = m.node_tree
            node = nt.nodes.get("LO_BAKE_TARGET") or nt.nodes.new("ShaderNodeTexImage")
            node.name = "LO_BAKE_TARGET"
            node.image = im
            nt.nodes.active = node
        return im

    def save(im, label):
        path = os.path.join(out_dir, f"{prefix}_{label}.png")
        im.filepath_raw, im.file_format = path, "PNG"
        im.save()
        return path

    saved = {}
    for m in mats:
        nt = m.node_tree
        p = _principled(m)
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        em = nt.nodes.get("LO_BAKE_EMIT") or nt.nodes.new("ShaderNodeEmission")
        em.name = "LO_BAKE_EMIT"
        saved[m.name] = (p, out, em)

    res = {}
    for label, sock, data in (("Color", "Base Color", False), ("Roughness", "Roughness", True), ("Metalness", "Metallic", True)):
        im = new_img(label, data)
        for m in mats:
            p, out, em = saved[m.name]
            nt = m.node_tree
            for l in list(em.inputs["Color"].links):
                nt.links.remove(l)
            src = p.inputs[sock]
            if src.links:
                nt.links.new(src.links[0].from_socket, em.inputs["Color"])
            else:
                v = src.default_value
                em.inputs["Color"].default_value = tuple(v) if sock == "Base Color" else (v, v, v, 1.0)
            nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
        bpy.ops.object.bake(type="EMIT")
        res[label] = save(im, label)
    for m in mats:
        p, out, em = saved[m.name]
        m.node_tree.links.new(p.outputs["BSDF"], out.inputs["Surface"])
    im = new_img("Normal", True)
    sc.render.bake.normal_space = "TANGENT"
    bpy.ops.object.bake(type="NORMAL")
    res["Normal"] = save(im, "Normal")
    for m in mats:   # le nœud image cible reste actif sinon : on le retire
        n = m.node_tree.nodes.get("LO_BAKE_TARGET")
        if n:
            m.node_tree.nodes.remove(n)
    sc.render.engine = prev_engine
    return res


def baked_material(name, maps):
    """Matière « comme dans Roblox » : seulement les 4 cartes, pour comparer au procédural."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    p = _principled(mat)
    uv = nt.nodes.new("ShaderNodeUVMap")
    for label, sock, data in (("Color", "Base Color", False), ("Roughness", "Roughness", True), ("Metalness", "Metallic", True)):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(maps[label], check_existing=True)
        t.image.colorspace_settings.name = "Non-Color" if data else "sRGB"
        nt.links.new(uv.outputs["UV"], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], p.inputs[sock])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(maps["Normal"], check_existing=True)
    t.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(uv.outputs["UV"], t.inputs["Vector"])
    nt.links.new(t.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
    return mat
