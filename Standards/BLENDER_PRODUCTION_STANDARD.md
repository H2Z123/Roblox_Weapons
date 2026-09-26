# BLENDER PRODUCTION STANDARD — ECLIPSE (à lire en premier)

Référence principale pour tout travail Blender sur les armes ECLIPSE (Viewmodel, Worldmodel, pièces mobiles, export Roblox). Concis par construction : les détails vivent dans les standards spécialisés (liens en fin de fichier). Version 1.0 — 2026-09-26.

## Légende (utilisée dans tous les standards)

| Tag | Sens |
|---|---|
| `[OFFICIEL]` | Documentation Roblox/Blender ou code source Blender |
| `[VÉRIFIÉ]` | Mesuré dans Blender 5.0.1 (bpy) sur scènes synthétiques — côté Blender seulement |
| `[PRO]` | Pratique professionnelle documentée (Polycount, Marmoset, Adobe, artistes publiés) |
| `[ECLIPSE]` | Décision du projet — point de départ recalibrable après audit d'ECLIPSE-1 |
| `[EXPÉRIMENTAL]` | Hypothèse à valider localement (Roblox Studio / ECLIPSE-1) avant d'en faire une règle |

## 1. Principes non négociables

1. **La source est sacrée.** On ne modifie jamais un fichier SOURCE versionné : on crée `vNNN+1`. L'export se fait depuis une **copie d'export** (`tools/eclipse_export.py`), jamais en appliquant des modificateurs dans la source. → EXPORT, NAMING_VERSIONING.
2. **Hiérarchie visuelle stricte : PRIMARY → SECONDARY → TERTIARY.** Interdit de compenser une silhouette faible par des micro-détails. → HARDSURFACE.
3. **Plans nets, arêtes qui accrochent la lumière.** Surfaces planes + chanfreins dimensionnés + Weighted Normal (Face Area, **weight 100**, Keep Sharp) en dernier. Jamais de « rounded everything ». → ANTI_MELTED_PLASTIC, BEVEL, SHADING.
4. **Chaque triangle se justifie à l'écran.** Un détail < ~3 px à la distance d'usage ne mérite pas de géométrie. → VIEWMODEL_WORLDMODEL (valeur/coût).
5. **1 Blender unit = 1 stud**, Unit Scale 1, échelle d'objet appliquée avant rig/export. → EXPORT.
6. **Les pivots sont des décisions**, posés sur les axes réels (charnière, chambre, poignée), jamais « Origin to Geometry » par défaut sur une pièce mobile. → PIVOTS_MECHANISMS.
7. **Aucune collision mécanique**, au repos comme pendant le mouvement : le balayage (`MOV003`) doit être propre avant l'animation. → PIVOTS_MECHANISMS, MECHANICAL_QA.
8. **La poignée est le contrat avec les bras** : repère `Grip_Att` = paume. → GRIP.
9. **PBR plausible** : grandes surfaces sombres = revêtement diélectrique à roughness travaillée ; métal nu seulement là où il est crédible. → MATERIALS_UV_BAKING.
10. **Détecter avant de corriger.** Le validator ne modifie rien ; toute correction est proposée, versionnée et validée visuellement par l'utilisateur.

## 2. Ordre des opérations (résumé)

AUDIT de l'existant → PRIMARY (silhouette, masses) → SECONDARY (panneaux, ruptures, mécanismes) → LOGIQUE MÉCANIQUE (pivots, jeux, balayages) → GRIP / clearances d'animation → TERTIARY (fixations, rainures) → SHADING → UV → PBR → optimisation VM → dérivation WM → VALIDATOR → COPIE D'EXPORT → IMPORT ROBLOX → PLAY TEST → VALIDATION UTILISATEUR.
Procédure détaillée : `ECLIPSE_WEAPON_MODELING_WORKFLOW.md`.

## 3. Décisions clés (une ligne chacune)

| Sujet | Décision | Détail |
|---|---|---|
| Stratégie normals | Hybride : VM mid-poly (géométrie + WN), WM low + normal map bakée depuis le VM | C1 |
| Bevel | 3 classes B1/B2/B3 ≈ 1 : 0,5 : 0,25 ; ≥ 2 px à la distance d'usage ; ≤ 10 % de la plus petite dimension ; VM 1 segment (2–3 sur silhouette haute), WM 0–1 | BEVEL |
| Topologie | Statique rigide : n-gons plans/convexes OK en source, triangulation explicite à l'export ; déformable : quads | TOPOLOGY, C4 |
| Booléens | Vivants en source ; appliqués dans la copie d'export ; nettoyage destructif seulement sur signal du validator | TOPOLOGY, C6 |
| Budgets | Limite dure 20 000 tris/MeshPart `[OFFICIEL]` ; cibles `[ECLIPSE]` VM ≤ 30k total, WM ≤ 6k et ≤ 40 % du VM | VIEWMODEL_WORLDMODEL |
| Textures | Résolution calculée depuis la texel density (VM ≥ 256 px/stud, WM ≥ 48) ; VM 1K (2K si justifié), WM 512 ; jamais 4K | MATERIALS, C7 |
| Padding | résolution/64 (16 px @1K) | MATERIALS, C10 |
| Export | FBX, Apply Scalings = FBX Units Scale, preset d'axes = celui prouvé par la calibration (défaut officiel Forward Z / Up Y) | EXPORT, C11–C13 |
| Pièces mobiles | MeshParts + Motor6D (existant conservé) ; charnières via Empties `_Att` | PIVOTS_MECHANISMS, C17 |
| Noms | Noms Roblox existants intouchables (`MainBody`, `TopHatch`, `Cartridge`…) ; noms Blender préfixés + propriété `roblox_name` | NAMING_VERSIONING |

## 4. À faire / à ne pas faire

**À faire**
- Mesurer avant d'agir : inventaire + rapport validator « BEFORE » sur une copie.
- Travailler dans l'ordre PRIMARY → TERTIARY, capture VM (FOV 70) + capture WM (12 et 25 studs) à chaque étape.
- Garder un petit nombre de largeurs de bevel (classes), mesurées en studs sur des objets à échelle 1.
- Poser les marqueurs : `Grip_Att`, `Muzzle_Att`, charnières `*_Hinge_Att`, chambre `Chamber_Att`.
- Déclarer les mouvements (`eclipse_motion_*`) et faire passer `MOV003`.
- Exporter via `Tools/BlenderValidation/tools/eclipse_export.py` (manifeste + rapport attachés à chaque FBX).

**À ne pas faire**
- Redessiner ECLIPSE-1 de zéro, ou changer sa silhouette sans validation utilisateur.
- Renommer des parts Roblox existantes (casse Motor6D/animations/scripts).
- Appliquer scale/rotation/modificateurs dans la source « pour exporter ».
- Ajouter des vis/rainures pour « faire détaillé » avant que PRIMARY et SECONDARY soient validés.
- Bevels > 3 segments, bevels identiques partout, Weighted Normal à weight 50.
- Métal à albedo noir, roughness uniforme, metalness à 0,5.
- Uploader dans Roblox des assets tiers sans statut `LICENSE_OK`.
- Faire confiance à un tutoriel Blender < 4.1 qui parle d'« Auto Smooth » sans le traduire (S22).

## 5. Portes qualité

| Porte | Outil | Critère de passage |
|---|---|---|
| Géométrie / normals / UV / budget / pivots / export | `validate_eclipse_asset.py` profils `viewmodel`, `worldmodel`, stage `export` | 0 FAIL ; chaque WARN justifié dans le rapport de PR/tâche |
| Visuel | `ECLIPSE_VISUAL_QA_CHECKLIST.md` | toutes les cases, captures BEFORE/AFTER |
| Mécanique | `ECLIPSE_MECHANICAL_QA.md` | trappe, cartouche, poignée, états ouvert/fermé |
| Performance | `ECLIPSE_PERFORMANCE_QA.md` | budgets VM/WM, textures, MeshParts |
| Roblox | calibration + import + play test | orientation/échelle/pivots/normals conformes, aucune ligne de shading |
| Humaine | l'utilisateur | validation explicite des captures |

## 6. Carte des standards

| Fichier | Contenu |
|---|---|
| `ECLIPSE_WEAPON_MODELING_WORKFLOW.md` | Procédure pas à pas, livrables par étape |
| `ECLIPSE_HARDSURFACE_STANDARD.md` | Hiérarchie PRIMARY/SECONDARY/TERTIARY, langage de formes, design de prop, fixations/kitbash |
| `ECLIPSE_ANTI_MELTED_PLASTIC.md` | Symptômes, causes, corrections, checklist |
| `ECLIPSE_BEVEL_STANDARD.md` | Classes, largeurs, segments, réglages |
| `ECLIPSE_SHADING_STANDARD.md` | Modèle de normals ≥ 4.1, Weighted Normal, diagnostic des fines lignes |
| `ECLIPSE_TOPOLOGY_STANDARD.md` | Statique vs déformable, n-gons, cylindres, booléens |
| `ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md` | Stratégie VM/WM, valeur/coût, budgets, multi-MeshPart |
| `ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md` | UV, texel density, padding, PBR, roughness, résolution, baking |
| `ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md` | Origines, repères, jeux, balayages, rig Motor6D |
| `ECLIPSE_GRIP_MODELING_STANDARD.md` | Poignée, repère GRIP→PALM→WRIST→FOREARM |
| `ECLIPSE_BLENDER_ROBLOX_EXPORT.md` | Échelle, axes, transforms, source vs export, import Studio, calibration |
| `ECLIPSE_NAMING_VERSIONING_STANDARD.md` | Nommage, `roblox_name`, versions, rollback |
| `ECLIPSE_VISUAL_QA_CHECKLIST.md` / `ECLIPSE_MECHANICAL_QA.md` / `ECLIPSE_PERFORMANCE_QA.md` | Checklists |
| `BLENDER_LOCAL_AGENT_HANDOFF.md` | Mode d'emploi pour l'agent Claude local |
| `../Knowledge/KNOWLEDGE_INDEX.md` | Index de chargement du contexte |
| `../Tools/BlenderValidation/README.md` | Validator, outils, règles |
