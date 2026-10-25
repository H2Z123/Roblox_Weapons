# LastOne — bibliothèque de matières (v01)

Matières **procédurales** Blender (aucune image téléchargée), pour que toutes les armes aient le même look
et pour faire des skins en changeant seulement des réglages.

| Groupe | Matière |
|---|---|
| `LO_AcierNoir` | Acier noir mat microrayé |
| `LO_OrGrave` | Or gravé (vrai métal, Métal = 1,0) |
| `LO_CaoutchoucPoignee` | Caoutchouc / polymère de poignée |
| `LO_PanneauGris` | Panneau gris |
| `LO_AcierBrosse` | Acier brossé terni |
| `LO_BordeauxModule` | Bordeaux du module `#80282E` |

Réglages communs : Couleur, Couleur usure, Usure, Rugosité, Rugosité usure, Métal, Métal usure,
Rayures, Relief, Saleté, Échelle (valeurs par défaut dans `PRESETS`).

```python
import lastone_materials as lom
mat = lom.make_material("AcierNoir")
skin = lom.make_skin("OrGrave", "Skin_OrRose", Couleur=lom.srgb("#F2B8A0"))
lom.bake_roblox_maps(obj, "textures", "T_ION_Coque", size=1024)  # Color, Normal (OpenGL), Roughness, Metalness
```

Planche de test (sphère | cube | cube refait avec les 4 cartes 1024) :

```
python build_board.py <sortie> 1024 96     # pip bpy 5.2.1 ou blender -b -P
python make_planche.py <sortie>
```

Cycles seulement (masque d'arêtes par nœud Bevel). `bake_roblox_maps` marche avec toute matière à Principled BSDF ;
l'objet doit avoir des UV 0-1 sans chevauchement. Rien n'est envoyé sur Roblox.
