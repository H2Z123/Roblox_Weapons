# ECLIPSE — Workflow de modélisation d'arme

Procédure opérationnelle. Chaque étape a un **livrable** et une **porte** ; on ne passe pas une porte sans son critère. Principes et décisions : `BLENDER_PRODUCTION_STANDARD.md`. Pour ECLIPSE-1 (modèle existant) : **améliorer, pas redessiner**.

```
AUDIT → PRIMARY → SECONDARY → LOGIQUE MÉCANIQUE → GRIP / CLEARANCES → TERTIARY → SHADING → UV → PBR
      → OPTIM. VM → DÉRIVATION WM → VALIDATOR → COPIE D'EXPORT → IMPORT ROBLOX → PLAY TEST → VALIDATION UTILISATEUR
```

Convention de captures (toutes étapes) : `VM_idle`, `VM_ADS`, `VM_inspect_1..3` (FOV 70, 1080p), `WM_12`, `WM_25`, silhouettes noires VM et WM 64 px. Dossier : NAMING §5.

---

### 0. AUDIT du modèle existant (référence)
- **Actions** : ouvrir la dernière source en **copie de travail** ; inventaire (objets, tris, matériaux, textures, modificateurs, origines, orientations, noms Roblox) ; validator profils `source`, `viewmodel`, `worldmodel` → rapports **BEFORE** ; captures BEFORE ; relever les dimensions réelles (longueur, hauteur, Ø canon, poignée) et la longueur de main du rig de bras ; identifier l'orientation historique (EXPORT §2).
- **Livrable** : `Reports/validation/ECLIPSE1_v<N>_*_BEFORE/` + captures + note d'audit (forces à préserver, problèmes classés PRIMARY/SECONDARY/TERTIARY/technique).
- **Porte** : l'utilisateur valide la liste des problèmes et les priorités.

### 1. PRIMARY — silhouette et masses
- **Actions** : corriger proportions/épaisseurs/étagements des masses **existantes** ; tester la silhouette noire aux deux distances ; aucune vis, aucune rainure.
- **Livrable** : SRC vN+1 (type MODEL), captures silhouette.
- **Porte** : silhouette reconnaissable, « compacte et lourde », distincte d'une arme réelle ; validation utilisateur. → HARDSURFACE §1–3.

### 2. SECONDARY — plans, panneaux, matériaux, lecture du mécanisme
- **Actions** : ruptures de plans sur les grandes faces, séparation trappe/carcasse lisible, logique de charnière, séparations de matériaux fonctionnelles, bevels classes B1/B2 (poids `bevel_class`), WN.
- **Porte** : en gris neutre on comprend comment l'arme s'ouvre et se tient ; `SHD002` PASS ; `BEV003` PASS. → HARDSURFACE §4, BEVEL, SHADING.

### 3. LOGIQUE MÉCANIQUE — pivots, jeux, balayages
- **Actions** : origines sur les axes ; `_Att` (charnière, chambre, bouche) ; propriétés `eclipse_motion_*` ; jeux ≥ 0,002 stud ; épaisseurs visibles en position ouverte.
- **Porte** : `MOV001`, `MOV003` PASS (tous scénarios), `MOV002` sans WARN non justifié ; `ECLIPSE_MECHANICAL_QA.md`. → PIVOTS_MECHANISMS.

### 4. GRIP / CLEARANCES D'ANIMATION
- **Actions** : dimensionner la poignée depuis la main du rig ; `Grip_Att` ; proxy de main en pose de prise dans `_Proxies` ; vérifier que trappe/cartouche/levier ne balaient ni la main ni le poignet.
- **Porte** : `GRP001` PASS ; balayages PASS avec proxy ; captures idle/ADS/inspection sans interpénétration. → GRIP.

### 5. TERTIARY — détails fonctionnels
- **Actions** : fixations aux jonctions (2–3 tailles), rainures, micro-découpes ; géométrie seulement ≥ 6–8 px en VM, sinon noté pour normal map/texture ; grappes près des points fonctionnels, zones de repos préservées.
- **Porte** : `BUD004` sans pièce « petite mais lourde », `GEO010` PASS ; checklist anti-« détails sans design » (HARDSURFACE §7).

### 6. SHADING
- **Actions** : WN dernier (Face Area, weight 100, Keep Sharp), sharp edges ciblées, vérifier normals extrêmes, soudures.
- **Porte** : `SHD001–SHD007`, `GEO004/005/008/009` PASS/justifiés. → SHADING.

### 7. UV
- **Actions** : coutures (arêtes dures, matériaux, zones cachées), îlots redressés, densité cible par profil, padding res/64, miroir seulement sur l'invisible.
- **Porte** : `UV001–UV009` PASS/justifiés ; résolution recommandée par `UV005` acceptée. → MATERIALS §2–3.

### 8. PBR
- **Actions** : bibliothèque de surfaces ECLIPSE ; roughness en 6 couches ; usure causale ; normal map tertiaire (VM) ; bake VM→WM (WM).
- **Porte** : `MAT001–MAT009` PASS (option `--analyze-textures`) ; roughness seule lisible en niveaux de gris ; validation en Studio sous 2 éclairages. → MATERIALS §4–9.

### 9. OPTIMISATION VIEWMODEL
- **Actions** : table valeur/coût ; segments de bevel ≤ 3 ; suppression des faces invisibles dans **tous** les états ; fusion des statiques ; budget VM.
- **Porte** : `BUD001–BUD003`, `BEV001/002` au profil `viewmodel`. → VIEWMODEL_WORLDMODEL.

### 10. DÉRIVATION / OPTIMISATION WORLDMODEL
- **Actions** : procédure VIEWMODEL_WORLDMODEL §5 (duplication, simplification, fusion, 512, bake depuis VM).
- **Porte** : `VMWM001` PASS ; profil `worldmodel` sans FAIL ; captures WM 12/25 et vignette 64 px.

### 11. VALIDATOR (complet)
- **Actions** : `validate_eclipse_asset.py` profils `viewmodel` et `worldmodel`, puis stage `export` ; rapports **AFTER**.
- **Porte** : 0 FAIL ; chaque WARN restant expliqué dans la note de livraison.

### 12. COPIE D'EXPORT
- **Actions** : `tools/eclipse_export.py --collection ECLIPSE1_VM --name ECLIPSE1_VM --version NNN --out-dir Export/ECLIPSE1 --apply-modifiers --triangulate` (idem WM).
- **Porte** : manifeste `source_unchanged = true` ; rapport export 0 FAIL. → EXPORT §5–6.

### 13. IMPORT ROBLOX
- **Actions** : calibration faite au moins une fois (EXPORT §8) ; import avec les réglages EXPORT §7 dans le **Studio d'armes**, jamais dans la version active ; recréer/raccorder les Motor6D sur les `_Att` ; appliquer SurfaceAppearance.
- **Porte** : tailles, orientation, pivots, attachments conformes ; nouveau `…_Rig_vNN+1` à côté de l'ancien.

### 14. PLAY TEST
- **Actions** : idle, ADS, tir, recul, rechargement complet (trappe + cartouche), inspection complète ; WM vu par un 2e client à 8–50 studs ; Render Stats (Shift+F2) pour draw calls/mémoire.
- **Porte** : `ECLIPSE_VISUAL_QA_CHECKLIST.md`, `ECLIPSE_MECHANICAL_QA.md`, `ECLIPSE_PERFORMANCE_QA.md` cochées ; aucune ligne de shading, aucune collision visible, main sur la poignée.

### 15. VALIDATION UTILISATEUR
- **Actions** : planche BEFORE/AFTER (mêmes vues), résumé des changements, rapports, WARN restants, risques ; demander la décision.
- **Porte** : accord explicite. Sans accord : rollback (NAMING §6) ou itération.
