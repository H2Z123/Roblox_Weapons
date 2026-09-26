# ECLIPSE Blender Validation Tools

Validator central + outils de pipeline pour les armes ECLIPSE. **Détecte, ne corrige pas** : aucun script de ce dossier ne modifie un fichier SOURCE. Standards : `Standards/BLENDER_PRODUCTION_STANDARD.md`.

## Statut de test (honnête)

| Élément | Statut |
|---|---|
| Cœur pur Python (config, rapport, maths, nommage, catalogue) | **Testé** (pytest, sans Blender) |
| 77 règles bpy | **Testées sur scènes synthétiques** avec `bpy` 5.0.1 (Blender en module Python, Linux) : 47 tests (18 purs + 29 d'intégration bpy), tous verts ; sans bpy : 18 passent, 29 ignorés |
| `tools/eclipse_export.py`, `tools/make_calibration_asset.py` | **Testés côté Blender** (source inchangée, coupeurs exclus, noms Roblox, `UnitScaleFactor=100`) |
| Exécution dans Blender **GUI** / via **Blender MCP** / sur **ECLIPSE-1** | **NOT EXECUTED** — à faire par l'agent local (voir `Standards/BLENDER_LOCAL_AGENT_HANDOFF.md`) |
| Comportement dans **Roblox Studio** | **NOT VERIFIED** — calibration obligatoire (`Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md` §8) |
| Versions Blender | écrit pour 4.2 LTS → 5.x ; testé 5.0.1 ; repli pour l'API normals < 4.1 non testé |

## Architecture

```
Tools/BlenderValidation/
├── validate_eclipse_asset.py      # CLI (dans Blender) — point d'entrée
├── config/eclipse_default.json    # profils, seuils, sévérités, preset FBX, marqueurs, mouvements
├── eclipse_validator/
│   ├── __init__.py    # run(), alias des scripts demandés, chargement des règles
│   ├── core.py        # modèle PASS/INFO/WARN/FAIL/SKIP/ERROR, registre @rule, runner (ne plante jamais)
│   ├── config.py      # chargement + fusion + validation de config
│   ├── report.py      # rapport JSON + Markdown
│   ├── mathutil.py    # maths écran/texels/cylindres/couleur (pur Python, testé)
│   ├── bpy_helpers.py # périmètre, snapshot du mesh ÉVALUÉ en espace monde, îlots UV
│   ├── geometry.py    # GEO001–GEO010
│   ├── shading.py     # SHD001–SHD007
│   ├── bevel.py       # BEV001–BEV006
│   ├── transforms.py  # TRF001–TRF007, ORI001, SCL001
│   ├── materials.py   # MAT001–MAT009
│   ├── uv.py          # UV001–UV009
│   ├── budget.py      # BUD001–BUD004
│   ├── rig.py         # PIV001–PIV004, MOV001–MOV004, GRP001, ARM001
│   ├── export.py      # EXP001–EXP009, VMWM001
│   ├── naming.py      # NAM001–NAM003
│   └── inventory.py   # inventaire factuel joint à chaque rapport (BEFORE/AFTER)
├── tools/
│   ├── make_calibration_asset.py  # crée un .blend de calibration Blender→Roblox (+ _EXPECTED.md)
│   └── eclipse_export.py          # SOURCE → copie d'export + FBX + manifeste (source jamais écrite)
└── tests/                          # pytest : purs + intégration bpy
```

Les règles lisent le mesh **évalué** (modificateurs appliqués), c'est-à-dire ce que l'exporteur FBX écrit.

## Utilisation

### En ligne de commande (Blender installé)

```bash
# rapport BEFORE du Viewmodel
blender -b Source/ECLIPSE1/ECLIPSE1_SRC_v012.blend --python Tools/BlenderValidation/validate_eclipse_asset.py -- \
  --profile viewmodel --collection ECLIPSE1_VM --out Reports/validation/ECLIPSE1_v012_viewmodel_BEFORE

# seulement les UV et les normals, WM, stage export
blender -b <copie_export>.blend --python Tools/BlenderValidation/validate_eclipse_asset.py -- \
  --profile worldmodel --stage export --collection ECLIPSE1_WM --check validate_uv,validate_normals

# catalogue des règles
blender -b --python Tools/BlenderValidation/validate_eclipse_asset.py -- --list-rules
```

Code de sortie : `0` aucun FAIL/ERROR · `1` au moins un FAIL/ERROR · `2` crash.

### Depuis une session Blender ouverte (Blender MCP → `execute_blender_code`)

```python
import sys; sys.path.insert(0, r"<repo>/Tools/BlenderValidation")
import eclipse_validator as ev
rep = ev.run(profile="viewmodel", collection="ECLIPSE1_VM",
             out_dir=r"<repo>/Reports/validation/ECLIPSE1_v012_viewmodel_BEFORE", reload=True)
print(rep["summary"])            # overall + compteurs
print([ (r["rule_id"], r["status"]) for r in rep["results"] if r["status"] in ("FAIL","WARN") ])
```
`reload=True` recharge les modules si le code a changé pendant la session.

### Options

| Option | Rôle |
|---|---|
| `--profile` (source / viewmodel / worldmodel) | jeu de seuils (distance de vue, budgets, résolution, padding…) |
| `--stage` (source / export) | `export` durcit certaines règles (TRF001, EXP001, MAT002 → FAIL) |
| `--collection` / `--objects` | périmètre (sinon toute la scène) ; collections `_Cutters/_WIP/_REF/...` exclues |
| `--check` | catégorie ou alias (tableau ci-dessous) |
| `--rules` | identifiants explicites |
| `--config` | JSON fusionné sur `config/eclipse_default.json` (ex. `moving_parts`, `sweep_scenarios`, `orientation.blender_forward`) |
| `--texture-resolution` | résolution supposée pour texel density / padding |
| `--analyze-textures` | lit les pixels (metalness binaire, écart-type de roughness, luminance albedo) |
| `--out` | écrit `validation_report.json` + `validation_report.md` |

### Correspondance avec les scripts demandés

Architecture centrale plutôt que 16 scripts : chaque script demandé est un **alias** (`--check <nom>`).

| Script demandé | Couverture |
|---|---|
| validate_scene | catégorie `scene` + `EXP001` |
| validate_mesh | catégorie `geometry` |
| validate_transforms | catégorie `transforms` |
| validate_orientation | `ORI001` |
| validate_scale | `SCL001`, `TRF006` |
| validate_normals | catégorie `shading` + `GEO006` |
| validate_non_manifold | `GEO001`, `GEO002`, `GEO005` |
| validate_degenerate | `GEO003`, `GEO009`, `UV004` |
| validate_duplicate_vertices | `GEO004`, `GEO008` |
| validate_materials | catégorie `materials` |
| validate_uv | catégorie `uv` |
| validate_triangle_budget | catégorie `budget` + `GEO010` |
| validate_pivots | catégories `pivots`, `grip` |
| validate_moving_parts | catégorie `moving_parts` |
| validate_viewmodel_worldmodel | `VMWM001` |
| validate_export_readiness | catégories `export`, `naming` + `TRF001`, `TRF002`, `TRF006` |
| (en plus) validate_bevels, validate_rig | catégories `bevel`, `rig` |

## Rapport

JSON (`schema_version`, `meta`, `summary{overall, counts, by_category}`, `results[]{rule_id, category, title, status, message, objects, details, doc}`, `inventory`) + Markdown lisible (FAIL → WARN → INFO → PASS, puis inventaire). Chaque résultat pointe vers la section du standard qui le justifie.

## Métadonnées Blender utilisées (propriétés personnalisées d'objet)

| Propriété | Sens |
|---|---|
| `roblox_name` | nom de la MeshPart/Attachment côté Roblox (renommage dans la copie d'export) |
| `eclipse_role` | `moving`, `reference` (ignoré des collisions) |
| `eclipse_motion_type/axis/min/max/pivot` | définition de mouvement pour `MOV003` |
| `eclipse_allow_open` | coque ouverte volontaire (`GEO001`) |
| `eclipse_allow_rotation` | rotation d'objet volontaire (`TRF003`) |
| `eclipse_no_collision` | exclure un objet des tests de collision |
| attribut d'arête `bevel_class` | poids 1 / 0,5 / 0,25 pour B1/B2/B3 (Bevel en mode Weight) |

## Catalogue des règles (généré depuis le registre)

| ID | Catégorie | Titre | Standard |
|---|---|---|---|
| `ARM001` | rig | Armature / skinning rules (Roblox) | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#armatures` |
| `BEV001` | bevel | Bevel segment count vs profile | `Standards/ECLIPSE_BEVEL_STANDARD.md#segments` |
| `BEV002` | bevel | Bevel too small to be seen | `Standards/ECLIPSE_BEVEL_STANDARD.md#largeur` |
| `BEV003` | bevel | Bevel too wide for the form (melted risk) | `Standards/ECLIPSE_ANTI_MELTED_PLASTIC.md` |
| `BEV004` | bevel | Bevel on unapplied / non-uniform scale | `Standards/ECLIPSE_BEVEL_STANDARD.md#echelle` |
| `BEV005` | bevel | Bevel limit method / clamp | `Standards/ECLIPSE_BEVEL_STANDARD.md#reglages` |
| `BEV006` | bevel | Bevel width distribution (hierarchy) | `Standards/ECLIPSE_BEVEL_STANDARD.md#hierarchie` |
| `BUD001` | budget | Triangles per MeshPart (official hard limit) | `Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md#budgets` |
| `BUD002` | budget | Total triangles vs profile | `Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md#budgets` |
| `BUD003` | budget | MeshPart count vs profile | `Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md#multi-meshpart` |
| `BUD004` | budget | Detail value / cost table | `Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md#valeur-cout` |
| `EXP001` | export | File saved and clean | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#source-vs-export` |
| `EXP002` | export | Boolean cutters would be exported | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#cutters` |
| `EXP003` | export | Non-exportable object types in scope | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#preset-fbx` |
| `EXP004` | export | Hidden objects inside the export scope | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#preset-fbx` |
| `EXP005` | export | Roblox names valid and unique | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#noms-roblox` |
| `EXP006` | export | Modifier stack summary | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#source-vs-export` |
| `EXP007` | export | Source vs export file naming | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#source-vs-export` |
| `EXP008` | export | Hierarchy and root | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#hierarchie` |
| `EXP009` | export | roblox_name contract | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#noms-roblox` |
| `GEO001` | geometry | Non-manifold / open edges | `Standards/ECLIPSE_TOPOLOGY_STANDARD.md#manifold` |
| `GEO002` | geometry | Loose vertices / wire edges | `Standards/ECLIPSE_TOPOLOGY_STANDARD.md#manifold` |
| `GEO003` | geometry | Degenerate faces and zero-length edges | `Standards/ECLIPSE_TOPOLOGY_STANDARD.md#degenerate` |
| `GEO004` | geometry | Duplicate (unwelded) vertices | `Standards/ECLIPSE_SHADING_STANDARD.md#diagnostic-des-fines-lignes` |
| `GEO005` | geometry | T-junctions on open borders | `Standards/ECLIPSE_SHADING_STANDARD.md#diagnostic-des-fines-lignes` |
| `GEO006` | geometry | Face winding consistency / inside-out shells | `Standards/ECLIPSE_TOPOLOGY_STANDARD.md#normals-orientation` |
| `GEO007` | geometry | N-gons (non-planar / concave) | `Standards/ECLIPSE_TOPOLOGY_STANDARD.md#n-gons` |
| `GEO008` | geometry | Duplicate / overlapping faces | `Standards/ECLIPSE_SHADING_STANDARD.md#diagnostic-des-fines-lignes` |
| `GEO009` | geometry | Sliver triangles | `Standards/ECLIPSE_SHADING_STANDARD.md#diagnostic-des-fines-lignes` |
| `GEO010` | geometry | Micro-geometry islands (probably invisible) | `Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md#valeur-cout` |
| `GRP001` | grip | Grip reference frame | `Standards/ECLIPSE_GRIP_MODELING_STANDARD.md#repere-grip` |
| `MAT001` | materials | One material per mesh object | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#materiaux-roblox` |
| `MAT002` | materials | Missing / empty material slots | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#materiaux-roblox` |
| `MAT003` | materials | Unused material slots | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#materiaux-roblox` |
| `MAT004` | materials | Texture files and resolutions | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#resolution` |
| `MAT005` | materials | Texture color spaces | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#espaces-couleur` |
| `MAT006` | materials | Normal map node space | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#normal-maps` |
| `MAT007` | materials | PBR constant values plausibility | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#valeurs-pbr` |
| `MAT008` | materials | Texture content analysis (optional) | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#roughness` |
| `MAT009` | materials | Material count vs profile budget | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#budgets` |
| `MOV001` | moving_parts | Intersections between parts at rest | `Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md#collisions` |
| `MOV002` | moving_parts | Clearance around moving parts | `Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md#jeux-et-clearances` |
| `MOV003` | moving_parts | Motion sweep collisions | `Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md#balayage` |
| `MOV004` | moving_parts | Moving parts without motion definition | `Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md#balayage` |
| `NAM001` | naming | Object names | `Standards/ECLIPSE_NAMING_VERSIONING_STANDARD.md#objets` |
| `NAM002` | naming | Material names | `Standards/ECLIPSE_NAMING_VERSIONING_STANDARD.md#materiaux` |
| `NAM003` | naming | Texture image names | `Standards/ECLIPSE_NAMING_VERSIONING_STANDARD.md#textures` |
| `ORI001` | orientation | Weapon forward axis | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#table-de-verite-des-axes` |
| `PIV001` | pivots | Origin far outside the part | `Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md#pivots` |
| `PIV002` | pivots | Moving part with default (bbox-centre) origin | `Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md#pivots` |
| `PIV003` | pivots | Required reference markers | `Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md#reperes` |
| `PIV004` | pivots | Roblox attachment objects (_Att) | `Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md#attachments` |
| `SCL001` | scale | Overall dimensions sanity | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#echelle` |
| `SHD001` | shading | Shading summary (smooth/flat, custom normals) | `Standards/ECLIPSE_SHADING_STANDARD.md#modele-de-normals` |
| `SHD002` | shading | Gradients on large flat faces | `Standards/ECLIPSE_SHADING_STANDARD.md#weighted-normals` |
| `SHD003` | shading | Extreme custom-normal deviation | `Standards/ECLIPSE_SHADING_STANDARD.md#roblox` |
| `SHD004` | shading | Weighted Normal modifier setup | `Standards/ECLIPSE_SHADING_STANDARD.md#weighted-normals` |
| `SHD005` | shading | Beveled smooth mesh without normal control | `Standards/ECLIPSE_SHADING_STANDARD.md#weighted-normals` |
| `SHD006` | shading | Bevel 'Harden Normals' in use | `Standards/ECLIPSE_SHADING_STANDARD.md#harden-normals` |
| `SHD007` | shading | Sharp edges without UV seam on normal-mapped meshes | `Standards/ECLIPSE_SHADING_STANDARD.md#hard-edges-et-uv` |
| `TRF001` | transforms | Unapplied scale | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#politique-transforms` |
| `TRF002` | transforms | Negative scale (mirrored transform) | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#politique-transforms` |
| `TRF003` | transforms | Non-zero rotation on parts | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#politique-transforms` |
| `TRF004` | transforms | Delta transforms | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#politique-transforms` |
| `TRF005` | transforms | Parent inverse matrices | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#politique-transforms` |
| `TRF006` | scene | Scene units (1 BU = 1 stud) | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#echelle` |
| `TRF007` | transforms | Asset root at world origin | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md#origine` |
| `UV001` | uv | UV map present | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#uv` |
| `UV002` | uv | Single UV set | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#uv` |
| `UV003` | uv | UVs inside 0-1 | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#uv` |
| `UV004` | uv | Degenerate UV faces | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#uv` |
| `UV005` | uv | Texel density (level and uniformity) | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#texel-density` |
| `UV006` | uv | UV island padding | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#padding` |
| `UV007` | uv | UV overlap and packing efficiency | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#uv` |
| `UV008` | uv | UV stretching | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#uv` |
| `UV009` | uv | Mirrored (flipped) UV faces | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md#miroir` |
| `VMWM001` | viewmodel_worldmodel | Worldmodel cheaper than Viewmodel | `Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md#comparaison` |

Sévérités par défaut : voir le code de chaque règle ; surcharges par profil (`profiles.<p>.severity`) et par stage (`stage_severity`). Toute règle se désactive via `disabled_rules`.

## Tests

```bash
# Option A — Blender en module Python (ce qui a été utilisé ici) : Python 3.11
python3.11 -m venv .venv && .venv/bin/pip install bpy==5.0.1 pytest
.venv/bin/python -m pytest Tools/BlenderValidation/tests -q

# Option B — Python embarqué de Blender
blender -b --python-expr "import sys, pytest; sys.exit(pytest.main(['-q', 'Tools/BlenderValidation/tests']))"
# (installer pytest dans le Python de Blender au préalable)
```
Sans bpy, les tests d'intégration sont ignorés (skip) et seuls les tests purs tournent.

## Limites connues

- Détection de collision par intersection de surfaces **et** points enfouis (sommets + centres de faces) dans des volumes fermés : une interpénétration entre deux pièces **ouvertes** peut échapper au test de contenance.
- `MOV002` mesure le jeu à partir des sommets (pas arête-arête).
- `UV006` échantillonne sommets et milieux d'arêtes : approximation du vrai écart entre îlots.
- `ORI001` sans `Muzzle_Att` n'est qu'une heuristique (axe le plus long).
- Le validator ne voit ni l'esthétique, ni les licences, ni Roblox : QA visuelle, guide de licences et calibration restent humains.
