# ECLIPSE — Viewmodel vs Worldmodel (budgets, valeur/coût, multi-MeshPart)

Une arme ECLIPSE = **deux produits** : le **Viewmodel** (VM, vu par un seul joueur, de très près, une seule instance) et le **Worldmodel** (WM, vu par tous, de loin, N instances simultanées). Même identité, budgets opposés. Tags : voir `BLENDER_PRODUCTION_STANDARD.md`.

## 1. Conditions de vue

| | Viewmodel | Worldmodel |
|---|---|---|
| Distance caméra | 1,5–3 studs (≈ 1 en inspection) | 8–50 studs typiquement |
| px/stud (1080p, FOV 70) | 257–514 (771 en inspection) | 15–96 |
| Faces vues | **arrière, dessus, flanc gauche** (arme à droite de l'écran) ; tout en inspection | silhouette et 2–3 masses |
| Instances | 1 | 1 par joueur armé (8–24+) |
| Coût dominant | triangles/texture de **une** arme, proche | draw calls × N, mémoire texture |

`[OFFICIEL]` RenderFidelity Automatic ne réduit le détail qu'au-delà de **250 studs** (S05) : pour un FPS, le WM est de fait **le seul LOD** → il doit être économique par construction. Garder `RenderFidelity = Automatic` (jamais Precise, S09).

<a id="valeur-cout"></a>
## 2. Quel détail en géométrie, normal map, roughness, texture ou rien ?

Règle de décision `[ECLIPSE]` fondée sur la taille à l'écran (calcul : `mathutil.projected_px`, table BEVEL §2) et sur le rôle du détail :

| Taille à la distance d'usage | Change la silhouette ou montre un mécanisme | Détail de surface sur une face plane |
|---|---|---|
| **≥ 8 px** | **Géométrie** (VM et WM) | VM : géométrie si peu coûteuse (≲ 100 tris), sinon normal map · WM : normal map |
| **3–8 px** | VM : géométrie · WM : normal map (bakée du VM) | VM : normal map · WM : roughness/albedo |
| **< 3 px** | VM : normal map · WM : omis ou roughness | Roughness / albedo, ou **omis** |
| **Jamais visible** (aucun état, inspection comprise) | **Supprimé** | **Supprimé** |

Table indicative pour ECLIPSE-1 :

| Élément | VM | WM |
|---|---|---|
| Silhouette, masses PRIMARY | géométrie | géométrie (simplifiée) |
| Trappe, charnière, chambre, cartouche | géométrie (état ouvert modélisé) | géométrie simplifiée si la trappe s'ouvre en 3e personne, sinon fermée et fusionnée |
| Lignes de panneau | géométrie (jeu réel) ou normal map | normal map / roughness |
| Chanfreins B1 / B2 / B3 | géométrie / géométrie / géométrie ou normal | silhouette seulement / bake / omis |
| Vis, inserts | géométrie si ≥ 6–8 px, sinon normal | omis ou texture |
| Rainures, texture de grip | normal map | roughness |
| Marquages, textes | albedo/roughness | omis |
| Micro-rayures, usure, traces | roughness (+ albedo léger) | roughness très atténuée |
| Âme du canon | géométrie (profondeur visible) + intérieur sombre | 1 anneau + intérieur noir en texture |

`BUD004` fournit la table réelle (tris, part du total, taille à l'écran) et signale les pièces petites à l'écran mais lourdes ; `GEO010` les micro-îlots invisibles.

<a id="budgets"></a>
## 3. Budgets

| | Limite | VM | WM | Nature |
|---|---|---|---|---|
| Triangles par MeshPart | **20 000** | ≤ 12 000 | ≤ 4 000 | `[OFFICIEL]` + `[ECLIPSE]` |
| Triangles total arme | — | 15 000–30 000 | 2 000–6 000 et ≤ 40 % du VM | `[ECLIPSE]` (S42 : armes FPS 5k–40k) |
| MeshParts | — | ≤ 16 (pièces mobiles + matériaux distincts) | ≤ 6 (idéal 1–3) | `[ECLIPSE]` |
| Sets de textures | — | 1 principal (+1 émissif/verre si besoin) | 1 | `[ECLIPSE]` C9 |
| Résolution | 4096 max | 1K (2K si justifié) | 512 (256 possible) | `[OFFICIEL]` + C7 |
| Segments de bevel | — | ≤ 3 | ≤ 1 | `[ECLIPSE]` |

Ces cibles sont des **points de départ** : le premier audit d'ECLIPSE-1 les recalibre (consigner dans ce fichier).

**Pourquoi le WM est serré** `[OFFICIEL]` S09 : chaque MeshPart au mesh unique ≈ un draw call ; l'**instancing** regroupe les meshes au même `MeshContent` **et** au SurfaceAppearance identique. Tous les WM d'ECLIPSE-1 partagent les mêmes IDs → N joueurs ≈ quelques draw calls, *à condition* de ne pas dupliquer les uploads ni d'individualiser les SurfaceAppearance par joueur. Mémoire texture ∝ pixels : 1K = 4 × 512.

<a id="multi-meshpart"></a>
## 4. Multi-MeshPart : quand séparer une pièce ?

`[ECLIPSE]` (C17 : MeshParts + Motor6D conservés).

**Séparer** si au moins une condition est vraie :
1. La pièce **bouge indépendamment** (trappe, cartouche, détente, chien…) → obligatoire (Motor6D).
2. Elle doit être **montrée/cachée** indépendamment (cartouche éjectée/insérée).
3. Elle exige un **matériau** qu'on ne peut pas partager (émissif, transparent).
4. La pièce fusionnée dépasserait **20 000 triangles**.
5. Elle est **interchangeable** (accessoire, skin structurel).

**Ne pas séparer** pour : l'organisation (utiliser des collections Blender), les détails statiques (vis, panneaux fixes → fusionnés à leur support), « au cas où ».

| | Plusieurs MeshParts | Mesh unique |
|---|---|---|
| + | pièces animables, pivots explicites, visibilité par pièce, limite 20k par pièce | 1 draw call, un seul pivot, WM idéal |
| − | 1 draw call par pièce, plus de Motor6D, risque de jeux/collisions | aucune animation interne |
| Culling | par pièce (frustum/occlusion) | global |

WM : fusionner tout ce qui ne s'anime pas **en 3e personne** (souvent tout sauf, éventuellement, trappe et cartouche).

## 5. Dériver le WM depuis le VM (procédure)

1. Dupliquer la collection `ECLIPSE1_VM` → `ECLIPSE1_WM` (nouvelle version SOURCE).
2. Supprimer ce qui n'est jamais visible de l'extérieur à 8+ studs (intérieurs, dessous cachés), sauf si une animation 3e personne l'ouvre.
3. Retirer les bevels B2/B3, garder B1 de silhouette (0–1 segment) ; réduire les cylindres (TOPOLOGY §5, colonne WM).
4. Fusionner les pièces statiques ; ne garder séparées que les pièces animées en 3e personne.
5. UV : un set 512 (texel density ≥ 48 px/stud, padding 8 px) ; **bake normal (+ AO éventuel) depuis le VM** (C1).
6. Vérifier : même enveloppe que le VM (écart de boîte ≤ 3 %), silhouette superposée en capture, `VMWM001`.
7. Noms : mêmes `roblox_name` que la convention WM existante (voir NAMING).

<a id="comparaison"></a>
## 6. Contrôles automatiques

`VMWM001` (ratio de triangles ≤ 0,40, matériaux, nombre de parts, enveloppe ±3 %) · `BUD001–BUD004` · `GEO010` · `BEV001/BEV002` (profil worldmodel : bevel invisible < 0,03 stud à 12 studs).

## 7. Réglages Roblox associés (à l'import, hors Blender)

VM : `CanCollide/CanTouch/CanQuery = false`, `CastShadow` selon le rendu voulu, `CollisionFidelity = Box` (mémoire minimale, S09). WM : `CollisionFidelity = Box`, `RenderFidelity = Automatic`. Ne pas modifier la SurfaceAppearance d'un WM par joueur (casse l'instancing).
