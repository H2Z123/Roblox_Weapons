# ECLIPSE — Export Blender → Roblox (échelle, orientation, transforms, source vs export)

Conventions historiques ECLIPSE **conservées** : 1 Blender unit = 1 stud ; Unit Scale = 1 ; import Roblox Scale Unit = Stud ; orientation corrigée ; dans Roblox **avant = −Z (LookVector), droite = +X (RightVector)**. On ne les remplace pas sans preuve (C12). Tags : voir `BLENDER_PRODUCTION_STANDARD.md`. Faits : `Knowledge/Blender/ROBLOX_PLATFORM_FACTS.md`.

<a id="echelle"></a>
## 1. Échelle

- Scène : **Unit System = None** (recommandé Roblox, S03) ou Metric avec **Unit Scale = 1** (`TRF006`). Avec None, l'exporteur ignore l'Unit Scale (facteur fixe) `[VÉRIFIÉ]` S21.
- FBX : **Apply Scalings = « FBX Units Scale »** `[OFFICIEL]` S02/S03. Pourquoi `[VÉRIFIÉ]` V4 : le défaut « All Local » écrit un `Lcl Scaling = 100` sur chaque objet → modèle ×100 dans Studio ; « FBX Units Scale » écrit la géométrie 1:1 avec `UnitScaleFactor = 100`, que Studio (Scale Unit = Stud) lit comme 1 BU = 1 stud.
- Ne jamais combiner plusieurs corrections d'échelle (Scale export 0,01 + Unit Scale…) — S03 l'illustre.
- Contrôle : `SCL001` (dimension la plus longue dans la plage du profil ; ×100 détecté), calibration `CAL_Cube_1x1x1` → `Size = 1,1,1`.

<a id="table-de-verite-des-axes"></a>
## 2. Orientation — table de vérité `[VÉRIFIÉ]` V6

| Preset FBX (Forward, Up) | Blender → Roblox | L'avant de l'arme (bouche) doit pointer vers | La droite du tireur est |
|---|---|---|---|
| **Z, Y** (officiel Roblox, S03) | −Y → −Z · −X → +X · +Z → +Y | **Blender −Y** (convention « Front » de Blender) | Blender −X |
| −Z, Y (défaut de l'exporteur) | +Y → −Z · +X → +X · +Z → +Y | Blender +Y | Blender +X |

Import Studio correspondant : **World Forward = Front, World Up = Top** `[OFFICIEL]` S03/S04.

**Procédure pour ECLIPSE-1** (ne rien supposer) :
1. Ouvrir la source ; noter où pointe la bouche (±Y) et où est l'avant de la trappe.
2. Choisir la ligne de la table qui envoie cette direction vers −Z Roblox ; régler `orientation.blender_forward` dans la config (`-Y` par défaut).
3. Confirmer avec l'asset de calibration (§8). Consigner dans `Knowledge/Blender/CALIBRATION_LOG.md`.
4. `ORI001` vérifie ensuite que le `Muzzle_Att` est du bon côté.

« **Apply Transform** » (bake_space_transform) : **off** (C13). Sans lui, les objets portent une rotation de conversion d'axes dans le FBX (V4) ; si la calibration montre des MeshParts à orientation parasite, tester « on » **uniquement sans armature** (option expérimentale, cassée avec armatures, S21).

<a id="politique-transforms"></a>
## 3. Politique de transforms

| Élément | SOURCE | COPIE D'EXPORT |
|---|---|---|
| Échelle d'objet | **appliquée (1,1,1)** avant rig/bevel/UV (`TRF001` : WARN en source, **FAIL** au stage export) | idem, jamais négative (`TRF002`) |
| Rotation d'objet | 0 pour les statiques (`TRF003`) ; pièces mobiles : 0 si l'axe est parallèle aux axes de l'arme, sinon orientation de l'axe (`eclipse_role=moving`) | idem |
| Delta transforms | interdits (`TRF004`) | interdits |
| Parent inverse | toléré, signalé (`TRF005`) | idem |
| Modificateurs | **vivants** (Mirror, Boolean, Bevel, WN…) | **appliqués** (`eclipse_export.py --apply-modifiers`) |
| Triangulation | non (n-gons plans OK) | Triangulate + `keep_custom_normals` (`--triangulate`) |
| Noms | préfixés (`ECLIPSE1_VM_…`) + `roblox_name` | renommés en `roblox_name` |

Appliquer une échelle/rotation **modifie** la source : se fait dans une **nouvelle version** SOURCE, jamais sur place, puis re-validation (bevels et UV dépendent de l'échelle).

<a id="origine"></a>
## 4. Origine et hiérarchie

- Racine de l'arme à l'origine du monde (`TRF007`) ; définition du point : PIVOTS §2 / GRIP §3.
- « Set Pivot to Scene Origin » (défaut Studio) → pivot du Model = origine Blender.
- « Use Imported Pivot » (défaut) → origine de chaque objet = `PivotOffset` de la MeshPart ; son `CFrame` reste au centre de sa boîte.

<a id="hierarchie"></a>
- Hiérarchie **plate** sous la racine pour les MeshParts ; `_Att` parentés à leur MeshPart (`PIV004`) ; aucun parent hors du périmètre exporté (`EXP008`). `[EXPÉRIMENTAL]` comment l'importeur reproduit une hiérarchie Blender imbriquée → à observer à la calibration.

<a id="source-vs-export"></a>
## 5. SOURCE vs COPIE D'EXPORT

- **SOURCE** (`Source/ECLIPSE1/ECLIPSE1_SRC_vNNN.blend`) : modificateurs utiles vivants, collections organisées, coupeurs, proxies, historique ; jamais « préparée pour l'export » à la main.
- **COPIE D'EXPORT** (`Export/ECLIPSE1/<Nom>_EXPORT_vNNN.blend` + `<Nom>_vNNN.fbx` + `_manifest.json` + rapport) : produite **uniquement** par `Tools/BlenderValidation/tools/eclipse_export.py`, qui :
  1. refuse une source non sauvegardée (en mode interface) et n'écrase jamais une version existante ;
  2. applique modificateurs / triangulation **en mémoire** ; renomme en `roblox_name` ;
  3. lance le validator au stage `export` (bloque sur FAIL sauf `--allow-fail` explicite) ;
  4. écrit la copie `.blend`, le FBX (preset ci-dessous), le manifeste (hash SHA-256 de la source **avant/après** → preuve qu'elle est intacte) et le rapport.
- Testé côté Blender sur scène synthétique : source inchangée, coupeur absent du FBX, noms Roblox corrects, `UnitScaleFactor = 100` (`tests/test_bpy_tools.py`). **Non testé dans Studio.**

<a id="preset-fbx"></a>
## 6. Preset FBX ECLIPSE

| Option (UI) | Propriété bpy | Valeur | Source |
|---|---|---|---|
| Limit to Selected | `use_selection` | ✔ (sélection = périmètre) | S03 |
| Object Types | `object_types` | Mesh, Empty, Armature | ECLIPSE |
| Apply Scalings | `apply_scale_options` | **FBX Units Scale** | S02 |
| Forward / Up | `axis_forward` / `axis_up` | **Z / Y** (ou le preset historique prouvé) | S03, C12 |
| Apply Transform | `bake_space_transform` | ✘ | C13 |
| Apply Modifiers | `use_mesh_modifiers` | ✔ (déjà appliqués dans la copie) | — |
| Smoothing | `mesh_smooth_type` | **Normals Only** (`OFF`) — conserve les weighted normals (V5) | V5 |
| Triangulate Faces | `use_triangles` | ✘ (altère les normals, V5 ; trianguler via modificateur) | V5 |
| Tangent Space | `use_tspace` | ✘ (Roblox calcule ses tangentes) | ECLIPSE |
| Add Leaf Bones | `add_leaf_bones` | ✘ | S02 |
| Bake Animation | `bake_anim` | ✘ (sauf export d'animation) | S02 |
| Path Mode / Embed | `path_mode` / `embed_textures` | Copy / ✔ | S02 |

Le preset vit dans `config/eclipse_default.json → export_preset`. Objets cachés : l'exporteur ne filtre pas la visibilité sans « Visible Objects » → `EXP004` ; coupeurs → `EXP002`.

<a id="cutters"></a>
Coupeurs booléens : collection `*_Cutters` (motif exclu), jamais dans la sélection exportée.

## 7. Import dans Roblox Studio (réglages ECLIPSE)

| Réglage | Valeur | Remarque |
|---|---|---|
| Import Only As Model | ✔ | un Model contenant les MeshParts |
| Upload to Roblox | ✘ pendant les essais ; ✔ pour la version validée | évite de polluer l'inventaire (S04) |
| Creator | groupe/compte du projet | droits d'usage |
| Add to Workspace | ✔ (place de test / Studio d'armes, **jamais la version Roblox active**) | |
| Insert Using Scene Position | ✔ pour comparer à l'ancienne version côte à côte | |
| Set Pivot to Scene Origin | ✔ | pivot = racine Blender |
| Anchored | ✔ en place de test | |
| World Forward / World Up | Front / Top | |
| Scale Unit | **Stud** | |
| Merge Meshes | ✘ | garder les pièces mobiles séparées |
| Invert Negative Faces | ✘ | corriger en Blender (`GEO006`) |
| Use Imported Pivot (objet) | ✔ | |
| Make Double Sided (objet) | ✘ | coûteux |
| Rig Type | No Rig (Motor6D créés côté Roblox) | sauf futur mesh skinné |

Presets d'import : sauvegarder « ECLIPSE Weapon » dans l'importeur (S04). Assets : **Asset Privacy = Restricted** (S16).

## 8. Calibration (obligatoire avant la première exportation d'ECLIPSE-1)

`tools/make_calibration_asset.py --out Calibration/ECLIPSE_CAL_Orientation_v001.blend [--forward -Y|+Y]` crée : `CAL_Cube_1x1x1`, `CAL_Box_X1_Y2_Z4` (attendu Roblox `Size = 1, 4, 2`), `CAL_Arrow` + `Muzzle_Att`, `CAL_RightMarker`, `CAL_PivotOffset` (origine en bout de barre), `CAL_Hinge_Att` (Attachment incliné de 30°), `CAL_WeightedNormals` vs `CAL_SmoothNoWN`, et un fichier `_EXPECTED.md` à cocher. Exporter via `eclipse_export.py`, importer avec §7, cocher, consigner dans `CALIBRATION_LOG.md`.

<a id="noms-roblox"></a>
## 9. Noms côté Roblox

Les MeshParts portent le nom de l'objet exporté. Les noms existants (`MainBody`, `TopHatch`, `Cartridge`, rigs `ECLIPSE1_Viewmodel_Rig_v01`…) sont des **contrats** avec les Motor6D, animations et scripts → propriété `roblox_name` sur chaque objet exporté (`EXP005` unicité/validité, `EXP009` présence). Détails : NAMING.

<a id="armatures"></a>
## 10. Armatures (si un jour un mesh skinné est exporté)

`[OFFICIEL]` S01 : bones gelés (scale 1, rotation 0), root en 0,0,0, **≤ 4 influences/vertex**, aucune influence sur le root, Add Leaf Bones off, une piste d'animation par fichier. Contrôle `ARM001`. Les pièces d'arme ECLIPSE restent des MeshParts + Motor6D (C17).

## 11. glTF

`[EXPÉRIMENTAL]` : Roblox importe `.gltf` sans réglage d'échelle (S03), mais des bugs de normals ont été signalés (S17). À re-tester avec l'asset de calibration avant toute adoption (C11).
