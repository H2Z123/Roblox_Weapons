# Faits plateforme Roblox + faits Blender vérifiés (référence unique)

Ce fichier regroupe **uniquement des faits** (officiels ou mesurés), sans recommandation. Les standards y renvoient pour ne pas les répéter. Dernière vérification : 2026-09-26. Sources détaillées : `SOURCE_INDEX.md`.

## Géométrie et import

| Fait | Valeur | Source |
|---|---|---|
| Triangles max par mesh (MeshPart) | **20 000** (des sources tierces citent 21 000 appliqué par Studio) | S01 |
| Géométrie | watertight, volume non nul, quads « si possible » | S01 |
| Formats d'import | `.fbx`, `.gltf`, `.obj` | S04 |
| Réglages d'import clés | World Forward (Front), World Up (Top), Scale Unit (Studs), Merge Meshes (off), Set Pivot to Scene Origin (on), Use Imported Pivot (on, par objet), Make Double Sided (off, coûteux), Invert Negative Faces (off), Upload to Roblox (on), Insert Using Scene Position (off) | S04 |
| Conversion par nom | `*_Att` → Attachment ; `*_OuterCage`/`*_InnerCage` → WrapTarget/WrapLayer | S05 |
| Position d'une MeshPart | CFrame au centre de la boîte englobante ; le pivot importé devient `PivotOffset` | S13, S17 (communauté) |
| RenderFidelity Automatic | < 250 studs : max · 250–500 : moyen · > 500 : bas | S05 |
| CollisionFidelity | Box, Hull, Default, PreciseConvexDecomposition, Tunable | S05 |
| Échelle | **1 stud = 28 cm** | S11 |
| Caméra | FieldOfView **verticale**, défaut **70°**, bornée 1–120 | S12 |

## Rig / skinning

Bones gelés (scale 1, rotation 0) · root en 0,0,0 · **max 4 influences par vertex** · pas d'influence sur le root · une seule piste d'animation par export (S01). Les bones n'affectent pas la collision (S14).

## Textures / PBR

| Fait | Valeur | Source |
|---|---|---|
| Résolution max upload | **4096×4096** (même page : « max 1024 » — texte obsolète, voir C8) | S06, S15 |
| Streaming de textures | automatique (depuis mars 2026) ; qualité selon importance à l'écran ; >1K seulement si justifié et si l'appareil le permet | S10, S15 |
| Bonnes pratiques streaming | textures uniques > atlas (sauf parts batchables) ; **texel density quasi uniforme** | S10 |
| Maps SurfaceAppearance | ColorMap (RGB + alpha), NormalMap, RoughnessMap, MetalnessMap, EmissiveMask (+ EmissiveStrength/Tint) | S07 |
| Normal map | **OpenGL, tangent space uniquement** ; (127,127,255) = plat | S06, S07 |
| Workflow | metalness (0 ou 1 dans la plupart des cas) | S07 |
| Fresnel | surfaces trop brillantes en rasant → ~+0.1 roughness | S07 |
| Tint | `SurfaceAppearance.Color` multiplie la ColorMap (sans coût mémoire) | S07, S09 |
| Matériaux | **un matériau par mesh** ; un seul UV set ; UV 0–1 ; overlaps autorisés | S06 |
| Mémoire | proportionnelle aux pixels (1024² = 4 × 512²) | S09 |
| Instancing | même MeshContent **et** SurfaceAppearance identique (ou TextureContent identique) → un draw call | S09 |
| Confidentialité | nouveaux assets image/mesh/decal **Restricted** par défaut (nouveaux comptes/groupes) | S16 |

## Export Blender → Roblox (officiel)

Units : Unit System **None** · Export FBX : **Forward = Z, Up = Y**, **Apply Scalings = FBX Unit Scale**, Path Mode Copy + Embed Textures, **Add Leaf Bones off**, **Bake Animation off** (sauf animation) · Import : World Forward Front, World Up Top, Scale Unit Stud (S02, S03).

## Faits Blender vérifiés dans cette session (bpy 5.0.1)

| Fait | Détail | ID |
|---|---|---|
| Défauts de l'exporteur FBX | `apply_scale_options=FBX_SCALE_NONE` (« All Local »), `axis_forward=-Z`, `axis_up=Y`, `mesh_smooth_type=OFF` (Normals Only), `add_leaf_bones=True`, `bake_anim=True`, `use_triangles=False`, `bake_space_transform=False` | S20 |
| Pourquoi le ×100 | « All Local » écrit `Lcl Scaling = 100` sur chaque objet ; « FBX Units Scale » écrit la géométrie 1:1 avec `UnitScaleFactor = 100` | V4, S21 |
| Unit System None | l'Unit Scale de la scène est ignoré par l'exporteur (facteur 100 fixe) | S21 |
| Axes, preset officiel (Z, Y) | Blender **−Y → −Z** Roblox (LookVector) · **−X → +X** (RightVector) · +Z → +Y | V6 |
| Axes, preset défaut (−Z, Y) | Blender **+Y → −Z** · **+X → +X** · +Z → +Y | V6 |
| Rotation d'objet dans le FBX | sans « Apply Transform » : (−90°,0,0) en preset −Z, (90°,0,180°) en preset Z ; avec : aucune | V4 |
| Normals | « Normals Only » conserve exactement les weighted normals (aller-retour FBX) ; `use_triangles` les altère (0,27°) ; Triangulate(`keep_custom_normals`) les conserve | V5, V3 |
| Weighted Normal | weight 50 → 5,4° de dégradé résiduel sur grandes faces ; 100 → 0° | V2 |
| Bevel : coût | boîte 12/44/108/188/300 tris pour 0–4 segments | V1 |
| Bake | tangent space **+X +Y +Z (OpenGL)**, marge 16 px, `ADJACENT_FACES` par défaut | V7 |
| Normals (≥ 4.1) | plus d'Auto Smooth : attributs `sharp_edge`/`sharp_face`, modificateur « Smooth by Angle », `Mesh.corner_normals` | S22, S20 |
| Booléen | solvers FLOAT / EXACT (défaut) / MANIFOLD (≥ 4.5, opérandes manifold) | S20, S23 |
| Arrière-plan | `bpy.data.is_dirty` est toujours vrai sans window manager (mode `-b`) | mesuré |
| Dépréciation | `Material.use_nodes` déprécié en 5.0 (retrait prévu en 6.0) | S26 |

## Ce qui n'est PAS vérifié (à faire localement avec l'asset de calibration)

1. Le traitement par l'importeur Roblox des rotations d'objets FBX (V4) et du preset d'axes historique d'ECLIPSE.
2. La préservation des custom normals par l'importeur Roblox en 2026 (communautaire : oui en FBX, S17).
3. La base tangente exacte de Roblox (seul « OpenGL tangent space » est documenté).
4. La conversion des Empties `_Att` issus d'un FBX Blender (position ET orientation).
5. Le comportement de glTF en 2026.
