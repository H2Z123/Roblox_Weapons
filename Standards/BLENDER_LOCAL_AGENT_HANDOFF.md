# BLENDER — Handoff pour l'agent Claude LOCAL

> Phrase de démarrage prévue : « Lis `Standards/BLENDER_LOCAL_AGENT_HANDOFF.md` et continue. »
> Ce fichier suffit pour démarrer ; il dit quoi lire ensuite, dans quel ordre, et comment travailler.

## 0. Contexte en 12 lignes

- Projet : **ECLIPSE**, FPS Roblox premium, équipe de 2. Périmètre : le **Studio de développement d'armes** (armes, VM/WM, bras, animations, tir, recul, ADS, effets, rechargements, inspections). Hors périmètre : hub, matchmaking, boutique, économie, modes.
- Arme de référence : **ECLIPSE-1**, hand-cannon futuriste de précision à **une cartouche** ; industriel premium, noir/gris, hard-surface, trapèzes/octogones. **Le modèle existe : on l'améliore, on ne le redessine pas.**
- Une session **cloud** (sans Blender GUI, sans Roblox Studio, sans les fichiers ECLIPSE) a produit : standards (`Standards/`), base de connaissances (`Knowledge/`), validator + outils (`Tools/BlenderValidation/`), shortlist (`PREMIUM_BLENDER_ASSET_SHORTLIST.md`).
- Le dépôt ne contenait **aucun** fichier ECLIPSE (pas de `ECLIPSE_STATE.md`, pas de `.blend`) : les conventions viennent du brief utilisateur.
- Validator : 77 règles, testées sur scènes synthétiques avec bpy 5.0.1 ; **jamais exécuté sur ECLIPSE-1 ni dans Blender GUI/MCP**. Rien n'a été vérifié dans **Roblox Studio**.
- Faits historiques à préserver : 1 BU = 1 stud ; Unit Scale 1 ; import Scale Unit = Stud ; avant Roblox = −Z, droite = +X ; noms `MainBody`, `TopHatch`, `Cartridge`, `ECLIPSE1_Viewmodel_Rig_v01`, `ECLIPSE1_Worldmodel_Rig_v01`.
- Problèmes connus : collisions MainBody/TopHatch/Cartridge ; fines lignes de shading sur des Worldmodels ; un bras hors de la poignée pendant l'inspection.

## 1. Mise en place (une fois)

1. **Localiser les fichiers ECLIPSE** : demander à l'utilisateur le chemin de la source `.blend` d'ECLIPSE-1, du Studio d'armes (place Roblox) et d'un éventuel `ECLIPSE_STATE.md`. Ne pas fouiller tout le disque.
2. **Blender** ≥ 4.2 LTS (5.x conseillé ; le manuel courant est 5.2 LTS).
3. **MCP for Blender** (S51) : `claude mcp add blender uvx mcp-for-blender` ; `uvx mcp-for-blender install-addon` ; dans Blender : Préférences → Add-ons → *Interface: MCP for Blender* ; panneau N → *Start MCP Server*. Désactiver Poly Haven/Sketchfab/Hyper3D dans le panneau (pas d'assets externes non licenciés).
4. **Roblox Studio MCP intégré** (S53) : Studio → Assistant → … → *Manage MCP Servers* → *Enable Studio as MCP server* → Quick connect *Claude Code*. Chaque appel prend un `studio_id` (`list_roblox_studios`).
5. **Tests du validator** (facultatif mais recommandé) : `Tools/BlenderValidation/README.md` §Tests.
6. Créer les dossiers de travail s'ils manquent : `Source/ECLIPSE1/`, `Export/ECLIPSE1/`, `Reports/validation/`, `Reports/screenshots/`, `Calibration/`. Décider avec l'utilisateur si les binaires vont dans Git LFS ou hors dépôt (NAMING §6).

## 2. Quoi lire, dans quel ordre (économie de tokens)

Toujours : **ce fichier** → `Standards/BLENDER_PRODUCTION_STANDARD.md` → `Knowledge/KNOWLEDGE_INDEX.md`. Ensuite **seulement** ce que la tâche demande :

| Tâche | Lire |
|---|---|
| Audit / amélioration de forme | `ECLIPSE_HARDSURFACE_STANDARD.md`, `ECLIPSE_ANTI_MELTED_PLASTIC.md`, `ECLIPSE_WEAPON_MODELING_WORKFLOW.md` |
| Bevels, normals, lignes de shading | `ECLIPSE_BEVEL_STANDARD.md`, `ECLIPSE_SHADING_STANDARD.md`, `ECLIPSE_TOPOLOGY_STANDARD.md` |
| Canon | `Knowledge/Blender/ECLIPSE1_BARREL_DESIGN_NOTES.md` |
| Trappe, cartouche, pivots, collisions | `ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md`, `ECLIPSE_MECHANICAL_QA.md` |
| Poignée / bras | `ECLIPSE_GRIP_MODELING_STANDARD.md` |
| UV, PBR, textures, bake | `ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md` |
| VM/WM, budgets | `ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md`, `ECLIPSE_PERFORMANCE_QA.md` |
| Export / import Roblox | `ECLIPSE_BLENDER_ROBLOX_EXPORT.md`, `ECLIPSE_NAMING_VERSIONING_STANDARD.md`, `Knowledge/Blender/ROBLOX_PLATFORM_FACTS.md` |
| « Pourquoi cette règle ? » | `Knowledge/Blender/CONTROVERSIES_AND_DECISIONS.md`, `SOURCE_INDEX.md` |
| Assets externes | `Knowledge/Blender/ASSET_LICENSE_GUIDE.md`, `PREMIUM_BLENDER_ASSET_SHORTLIST.md` |

## 3. Règles de sécurité (non négociables)

1. **Jamais** modifier une version SOURCE existante : `Save As` → `ECLIPSE1_SRC_v(N+1).blend` **avant** toute modification. **Sauvegarder avant chaque `execute_blender_code`** (S51).
2. **Jamais** toucher la version Roblox active ; travailler dans le Studio d'armes / une place de test.
3. **Aucune publication, aucun upload** (images, meshes, packages) sans accord explicite de l'utilisateur. Pas d'achat. Pas d'asset tiers sans `LICENSE_OK`.
4. **Ne pas renommer** les parts/rigs Roblox existants (Motor6D, animations et scripts les adressent par nom) → `roblox_name`.
5. Le validator **détecte** ; les corrections sont proposées, versionnées, puis validées visuellement par l'utilisateur. Aucune correction destructive automatique (topologie, UV, normals importantes, suppression de meshes, application de modificateurs dans la source).
6. Toute modification de **silhouette** = proposition avec captures, accord explicite avant application.

## 4. Inspecter un asset

**Interactif (Blender MCP)** : `get_scene_info`, `get_object_info(<nom>)`, `get_viewport_screenshot`. Pour du bpy : `execute_blender_code`.

**Rapport reproductible (recommandé)** — processus Blender séparé sur le fichier **sauvegardé** :
```bash
blender -b "<chemin>/ECLIPSE1_SRC_vNNN.blend" --python Tools/BlenderValidation/validate_eclipse_asset.py -- \
  --profile viewmodel --collection <collection VM> --out Reports/validation/ECLIPSE1_vNNN_viewmodel_BEFORE
```
(idem `--profile worldmodel` ; `--profile source` sans collection pour une vue d'ensemble ; `--analyze-textures` pour les maps.)

**Depuis la session MCP** (si le mode *safe* de MCP est désactivé — il bloque l'écriture de fichiers) :
```python
import sys; sys.path.insert(0, r"<repo>/Tools/BlenderValidation")
import eclipse_validator as ev
rep = ev.run(profile="viewmodel", collection="<collection VM>", out_dir=r"<repo>/Reports/validation/<nom>", reload=True)
print(rep["summary"]); print([(r["rule_id"], r["status"], r["objects"][:4]) for r in rep["results"] if r["status"] in ("FAIL","WARN")])
```

**Premier passage sur ECLIPSE-1** : les collections/propriétés ECLIPSE (`roblox_name`, `eclipse_motion_*`, `_Att`) n'existent probablement pas encore → attendre des WARN `PIV003`, `EXP009`, `MOV004`, `NAM001` : c'est normal, c'est la liste de préparation. Déclarer les mouvements de la trappe et de la cartouche dans une config projet (`Tools/BlenderValidation/config/eclipse1.json`, fusionnée via `--config`) plutôt que dans la source.

**Captures comparables** : reproduire la caméra VM Roblox dans Blender — lire via Studio MCP (`inspect_instance`) l'offset du viewmodel par rapport à la caméra, créer dans une collection `_REF` une caméra Blender *Sensor Fit = Vertical*, angle **70°**, à cet offset ; mêmes cadrages BEFORE/AFTER (NAMING §5). Dans Studio : `screen_capture` avec position/cible explicites.

## 5. Proposer une modification

Format (une fiche par changement, regroupées PRIMARY / SECONDARY / TERTIARY / TECHNIQUE) :

| Champ | Contenu |
|---|---|
| Problème | constat + preuve (ID de règle, capture, mesure) |
| Changement proposé | précis (pièce, valeur, méthode) |
| Standard | section qui le justifie |
| Impact | tris ±, matériaux, visuel attendu |
| Risque | ce qui peut casser (animations, noms, pivots) |
| Réversibilité | version de départ / d'arrivée |

Ordre d'application : **techniques sans impact visuel** (soudures, WN weight, unités) → SECONDARY/shading → PRIMARY seulement après accord. Petits pas, un changement vérifiable à la fois, validator relancé après chaque lot.

## 6. Rollback

1. Avant tout lot : `Save As` nouvelle version + ligne `CHANGELOG.md` (type MODEL/MECHFIX/…).
2. Revenir = rouvrir la version précédente (rien n'est supprimé).
3. Exports immuables (l'outil refuse d'écraser) ; Roblox : l'ancien `…_Rig_vNN` reste à côté du nouveau.

## 7. Travailler avec Blender MCP — bonnes pratiques

- Découper : une opération par appel, lire le résultat, puis continuer.
- Dans `execute_blender_code`, opérateurs → `with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):` ; préférer l'API de données (`ob.modifiers.new`, `mesh.attributes`) aux `bpy.ops`.
- Ne jamais appliquer de modificateur dans la source ; utiliser `Tools/BlenderValidation/tools/eclipse_export.py` pour la copie d'export.
- Après chaque lot : `get_viewport_screenshot` + validator.
- Pour poser les hiérarchies de bevel : attribut d'arête `bevel_class` (1 / 0,5 / 0,25) + Bevel en mode Weight (BEVEL §1).

## 8. Préparer Roblox

1. **Calibration d'abord** (une fois par combinaison Blender/Studio/preset) : `tools/make_calibration_asset.py` → `eclipse_export.py` → import manuel par l'utilisateur (Importer, réglages EXPORT §7) → contrôles via Studio MCP (`search_game_tree`, `inspect_instance` : `Size`, `PivotOffset`, Attachments) → `Knowledge/Blender/CALIBRATION_LOG.md`.
2. **Export ECLIPSE-1** : `eclipse_export.py --collection … --name ECLIPSE1_VM --version NNN --out-dir Export/ECLIPSE1 --apply-modifiers --triangulate` (idem WM) ; vérifier le manifeste (`source_unchanged: true`).
3. **Import** : par l'utilisateur (pas d'outil MCP d'import de FBX local), dans le Studio d'armes, *Upload to Roblox* seulement pour la version validée.
4. **Rig** (place de test) : `execute_luau` (Edit) pour recréer les Motor6D sur les Attachments de charnière (PIVOTS §6) ; textures : l'upload nécessite l'accord de l'utilisateur.
5. **Tests** : `start_stop_play`, `get_console_output`, `screen_capture` ; checklists VISUAL / MECHANICAL / PERFORMANCE.

## 9. Rapporter les résultats

Rapport `Reports/ECLIPSE1_vNNN_session_<date>.md` :
1. Résumé (3–5 lignes) et décision demandée.
2. Fichiers créés/modifiés (versions source/export, manifestes).
3. Tableau validator BEFORE → AFTER (FAIL/WARN/INFO par catégorie, tris VM/WM, matériaux, résolution).
4. Planche de captures BEFORE/AFTER (mêmes vues).
5. Changements appliqués (fiches §5) et changements proposés non appliqués.
6. WARN restants avec justification ; risques ; points non vérifiés.
7. Prochaines étapes et questions à l'utilisateur.

## 10. NEXT LOCAL MISSION (exacte)

1. **Lire** ce fichier, `Standards/BLENDER_PRODUCTION_STANDARD.md`, `Knowledge/KNOWLEDGE_INDEX.md`, puis `Standards/ECLIPSE_WEAPON_MODELING_WORKFLOW.md`.
2. **Mise en place** §1 (demander les chemins ECLIPSE à l'utilisateur ; connecter Blender MCP et Studio MCP) ; lancer les tests du validator.
3. **Ouvrir ECLIPSE-1** : `Save As` immédiat en copie de travail `ECLIPSE1_SRC_v(N+1).blend` (la source d'origine n'est plus touchée).
4. **Audit Blender** : inventaire (collections, objets, noms Roblox, origines, orientation de la bouche, dimensions, tris, matériaux, textures, modificateurs), longueur de main du rig de bras, correspondance avec les parts Roblox existantes (Studio MCP : `search_game_tree` sur `ECLIPSE1_Viewmodel_Rig_v01` / `…Worldmodel…`).
5. **Validators** : profils `source`, `viewmodel`, `worldmodel` (+ `--analyze-textures`) → **rapports BEFORE** ; captures BEFORE (VM idle/ADS/inspection, WM 12/25, silhouettes).
6. **Calibration** Blender→Roblox (EXPORT §8) si aucune ligne n'existe dans `CALIBRATION_LOG.md` ; en déduire `orientation.blender_forward` et le preset d'axes réellement utilisé historiquement.
7. **Identifier les améliorations** : classer PRIMARY / SECONDARY / TERTIARY / TECHNIQUE ; priorités suggérées : (a) collisions trappe/cartouche (`MOV001/003` avec mouvements déclarés), (b) fines lignes WM (SHADING §6), (c) shading des grandes faces (`SHD002`) et bevels (`BEV*`), (d) canon (notes dédiées), (e) matériaux/roughness, (f) `Grip_Att` + proxy de main (support du bug d'inspection).
8. **Proposer** les fiches §5 à l'utilisateur ; **attendre** son accord pour tout ce qui touche la silhouette.
9. **Créer une version réversible** et appliquer **seulement** les corrections approuvées, par petits lots, validator après chaque lot.
10. **Exporter** via `eclipse_export.py` (VM puis WM), vérifier manifestes et rapports AFTER.
11. **Importer dans Roblox** (par l'utilisateur, place de test du Studio d'armes), rig de test, play test (rechargement complet + inspection complète, WM vu par un 2e client).
12. **Captures BEFORE/AFTER** identiques (Blender et Studio) + rapport §9.
13. **Demander la validation utilisateur** ; en cas de refus : rollback §6.

## 11. À vérifier en priorité (inconnues de la session cloud)

Orientation/rotations des MeshParts importées (V4) · préservation des custom normals par l'importeur Roblox · conversion et orientation des `_Att` · base tangente Roblox (bake de test) · comportement de l'hiérarchie imbriquée · budgets `[ECLIPSE]` à recalibrer sur ECLIPSE-1 · paramètres d'animation réels (angle max de la trappe, trajectoire de la cartouche). Chaque résultat → `CALIBRATION_LOG.md` ou mise à jour du standard concerné (avec date et source).
