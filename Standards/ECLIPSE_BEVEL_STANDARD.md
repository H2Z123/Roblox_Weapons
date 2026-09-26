# ECLIPSE — Standard de bevel

Un bevel n'est pas « un bevel partout » : c'est une **décision par classe d'arête**, dimensionnée pour être vue à la distance d'usage, sans gonfler la forme, et au coût maîtrisé. Tags : voir `BLENDER_PRODUCTION_STANDARD.md`. Faits de référence : `Knowledge/Blender/ROBLOX_PLATFORM_FACTS.md`.

<a id="hierarchie"></a>
## 1. Classes d'arêtes

| Classe | Arêtes concernées | Largeur relative | VM | WM |
|---|---|---|---|---|
| **B1** | Silhouette, arêtes des masses PRIMARY | 1 | géométrie, 1 seg (2–3 si silhouette haute proche caméra) | géométrie 0–1 seg, **seulement si elle porte la silhouette** |
| **B2** | Panneaux, tranches d'ouverture, bords de pièces SECONDARY | ≈ 0,5 | géométrie 1 seg | normal map bakée depuis le VM, sinon arête vive |
| **B3** | Petites pièces, fixations, rainures | ≈ 0,25 | géométrie si ≥ 2 px en **inspection**, sinon normal map | omis |
| **B0** | Arête vive volontaire (intérieurs, arêtes très courtes, contraste) | 0 | arête marquée sharp | idem |

`[ECLIPSE]` Le ratio 1 : 0,5 : 0,25 donne l'écart d'échelle « grand/moyen/petit » exigé par HARDSURFACE §1. La présence de **B0** est volontaire : quelques arêtes vives rendent les autres lisibles (anti « rounded everything »).

**Encodage recommandé** `[VÉRIFIÉ]` V9 : un attribut d'arête flottant `bevel_class` (1,0 / 0,5 / 0,25), un seul modificateur Bevel `Limit Method = Weight`, `Edge Weight = bevel_class`, `Width = largeur B1`. La largeur appliquée est multipliée par le poids → la hiérarchie est garantie et se change en un seul champ.

<a id="largeur"></a>
## 2. Déterminer la largeur

Trois bornes, toutes calculables (`eclipse_validator/mathutil.py`) :

1. **Borne basse — visibilité** `[ECLIPSE]` : `w ≥ min_px / ppu(d)` avec `ppu(d) = H / (2·d·tan(FOV/2))`, FOV 70° verticale `[OFFICIEL]`, H = 1080, `min_px = 2`. En dessous, le bevel coûte des triangles sans se voir (`BEV002`).
2. **Borne haute — forme** `[ECLIPSE]` : `w ≤ 10 %` de la plus petite dimension de la pièce et ≤ 1/3 de la plus étroite des deux faces adjacentes (`BEV003`). Au-delà : volumes gonflés (ANTI_MELTED #1).
3. **Borne bake** `[PRO]` S38 : un bevel bakté doit couvrir **≥ 3 texels** à la résolution cible (`w × texel_density ≥ 3`), sinon il disparaît aux mips ; exagérer ×1,5–2 dans le high-poly.

**Table de visibilité** (1080p, FOV 70) :

| Distance (studs) | px/stud | largeur mini (2 px) | largeur « lisible » (4 px) | Usage |
|---:|---:|---:|---:|---|
| 1,0 | 771 | 0,0026 | 0,0052 | inspection |
| 1,5 | 514 | 0,0039 | 0,0078 | VM, avant de l'arme proche |
| 2,0 | 386 | 0,0052 | 0,0104 | **VM typique** |
| 3,0 | 257 | 0,0078 | 0,0156 | VM, bouche |
| 12 | 64 | 0,031 | 0,062 | **WM typique** |
| 20 | 39 | 0,052 | 0,104 | WM |
| 50 | 15 | 0,13 | 0,26 | WM lointain |

En 1440p multiplier px/stud par 1,33. Conséquence directe : **aucun bevel < 0,03 stud n'a de sens en géométrie sur un Worldmodel**.

**Valeurs de départ ECLIPSE-1** `[ECLIPSE]` (arme ≈ 1,2–1,5 stud de long vue à ≈ 2 studs ; à recalibrer après mesure réelle) :

| Classe | VM | WM |
|---|---|---|
| B1 | 0,012–0,020 stud (≈ 5–8 px) | 0,03–0,05 stud, seulement sur la silhouette |
| B2 | 0,006–0,010 stud (≈ 2,5–4 px) | bake depuis le VM |
| B3 | 0,004–0,006 stud (≥ 2 px à 1 stud en inspection) | omis |

<a id="segments"></a>
## 3. Segments

Coût mesuré `[VÉRIFIÉ]` V1 : boîte 12 → 44 → 108 → 188 → 300 tris pour 0 → 4 segments ; cylindre 32 côtés 124 → 252 → 380 → 508 → 636.

- **VM** : **1 segment** (chanfrein) + Weighted Normal par défaut `[PRO]` S37 ; **2–3** pour les arêtes B1 de la silhouette haute proches de la caméra, les grands rayons et les extrémités de cylindres visibles ; **jamais > 3** (`BEV001`).
- **WM** : 0–1 segment, B1 de silhouette seulement.
- Profil : 0,5 (circulaire) par défaut. `[EXPÉRIMENTAL]` 0,6–0,7 pour un rendu « usiné » plus tendu à 2–3 segments — à comparer en capture.

<a id="reglages"></a>
## 4. Réglages du modificateur (Blender ≥ 4.2)

| Réglage | Valeur ECLIPSE | Raison |
|---|---|---|
| Width Type | Offset (ou Width), **absolu** | largeur en studs, mesurable |
| Limit Method | **Weight** (attribut `bevel_class`) ; Angle 30° accepté en blocage/itération | contrôle de la hiérarchie ; Angle = tout arrondir |
| Clamp Overlap | ON | évite les géométries qui se croisent (`BEV005`) |
| Loop Slide | ON | conserve la répartition |
| Miter Outer | Sharp ; Patch/Arc si pincement aux coins à 3 arêtes | propreté des coins |
| Harden Normals | OFF (Weighted Normal en dernier à la place) | régressions post-4.1 (S25, `SHD006`) |
| Face Strength | optionnel (`Affected`/`New`) si WN utilise Face Influence | contrôle fin des normals |
| Ordre de pile | Mirror → Boolean(s) → Bevel → (Triangulate, export) → **Weighted Normal** | le bevel doit voir les arêtes booléennes ; WN voit la topologie finale |

Les arêtes créées par un booléen n'ont pas de poids : soit on applique le booléen puis on pose `bevel_class`, soit on ajoute un Bevel en `Angle` dédié aux coupes (documenté dans le nom du modificateur).

<a id="echelle"></a>
## 5. Échelle

Le Bevel travaille en espace **local** : une pièce à l'échelle (2, 1, 1) reçoit des chanfreins déformés et des largeurs fausses. **Échelle appliquée (1, 1, 1)** avant de régler un bevel (`BEV004`, `TRF001`).

## 6. Bevel et shading / baking

- Chanfrein 1 segment **sans** normals contrôlées = dégradés sur les grandes faces (`SHD005`) → Weighted Normal Face Area, **weight 100**, Keep Sharp `[VÉRIFIÉ]` V2.
- Pour le bake WM depuis le VM : B1/B2 du VM suffisent comme « high-poly » ; vérifier la borne bake (≥ 3 texels à 512).
- Viewmodel peut justifier plus de qualité ; Worldmodel doit être économique : c'est la même arme, deux budgets (VIEWMODEL_WORLDMODEL).

## 7. Contrôles automatiques

`BEV001` segments · `BEV002` trop petit pour être vu · `BEV003` trop large (fondu) · `BEV004` échelle · `BEV005` limit/clamp · `BEV006` distribution des largeurs (hiérarchie).
