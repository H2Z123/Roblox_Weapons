# Désaccords professionnels et décisions ECLIPSE

Chaque fois que les sources divergent, ce fichier expose **méthode A / méthode B**, avantages, inconvénients, quand utiliser chacune, puis la décision ECLIPSE. Les standards renvoient ici au lieu de répéter l'argumentation. Sources : voir `SOURCE_INDEX.md` (Sxx, Vx).

Légende : `[OFFICIEL]` doc Roblox/Blender · `[VÉRIFIÉ]` mesuré en bpy 5.0.1 · `[PRO]` pratique pro · `[ECLIPSE]` décision projet · `[EXPÉRIMENTAL]` à valider localement.

---

## C1 — Mid-poly (géométrie + weighted normals) vs high→low bake

| | A. Mid-poly (S30, S37, S47) | B. High-poly → low-poly bake (S31, S32) |
|---|---|---|
| Principe | Chanfreins réels (1–3 segments) + normals pondérées ; pas ou peu de normal map | Bevels et détails dans un high-poly, projetés dans une normal map sur un low-poly |
| + | Itération rapide, pas de bake, indépendant de la base tangente du moteur, arêtes nettes à toute distance | Très peu de triangles, détails fins (gravures, vis) gratuits en géométrie |
| − | Plus de triangles, micro-détails coûteux en géométrie | Dépend d'une base tangente synchronisée (non documentée chez Roblox, C5), coutures, mips qui effacent les bevels fins, pipeline lourd |
| Quand | Armes vues de près, surfaces planes, équipe réduite | Worldmodels, détails tertiaires, assets très denses |

**Décision [ECLIPSE]** — hybride :
- **Viewmodel** : mid-poly pour PRIMARY/SECONDARY (chanfreins réels + Weighted Normal). Normal map *optionnelle* réservée au TERTIARY (gravures, micro-rainures, texture de grip), jamais pour simuler les grands bevels.
- **Worldmodel** : low-poly (bevels réels seulement sur la silhouette) + **normal map bakée depuis le Viewmodel** (le VM sert de high-poly du WM) → les chanfreins du VM sont conservés visuellement pour quelques triangles.
- Justification : moins de dépendance à la base tangente là où la caméra est proche ; économies là où l'arme est petite à l'écran.

## C2 — Contrôle des normals : Harden Normals vs Weighted Normal vs normals manuelles

| | A. Bevel « Harden Normals » | B. Modificateur Weighted Normal | C. Custom normals manuelles (Set from faces, outils add-on) |
|---|---|---|---|
| + | Un seul modificateur | Non destructif, prévisible, dernier de la pile | Contrôle total |
| − | Régressions signalées après 4.1 (S25) | Défaut `weight 50` insuffisant (V2) | Destructif, se perd si la topologie change |

**Décision [ECLIPSE]** : B par défaut — Weighted Normal **en dernier**, `Face Area`, **`weight 100`**, `Keep Sharp` ON (V2 : 5,4° de dégradé résiduel à 50 → 0° à 100). A toléré s'il est vérifié visuellement (`SHD006`). C seulement dans la copie d'export pour un cas local documenté.

## C3 — Finition sombre d'arme : revêtement diélectrique vs « métal sombre »

| | A. Revêtement = diélectrique (S34, S35 partie, S49) | B. Métal à albedo sombre (S35 partie) |
|---|---|---|
| Principe | Peinture, Cerakote, polymère, oxyde (bleuissage/parkerisation) = non-métaux : metallic 0, albedo 30–60 sRGB | metallic 1, albedo 60–120 sRGB |
| + | Physiquement plausible, stable sous tous les éclairages, validé par les validateurs PBR | Reflets « métal précieux », apprécié de certains artistes |
| − | Peut paraître « plastique » si la roughness est uniforme | Hors plage des métaux réels (fer ≈ 190 sRGB, S49) ; sous certains éclairages → « chrome noir » ou masse noire |

**Décision [ECLIPSE]** : A pour les grandes surfaces (carcasse, trappe) avec une roughness **travaillée** (voir MATERIALS §Roughness) — c'est la roughness, pas la couleur, qui évite le plastique. Le métal nu (metallic 1, albedo ≥ 160 sRGB) n'apparaît que là où il est **crédible** : arêtes usées, surfaces usinées fonctionnelles (âme du canon, couronne de bouche, charnière, culot de cartouche). B autorisé seulement comme **exception documentée** par matériau, après comparaison côte à côte en Studio (`MAT007` avertit en dessous de 0,35 de luminance linéaire ≈ 160 sRGB).

## C4 — Topologie : « tout en quads » vs n-gons/triangles pour le hard-surface statique

A (dogme quads) : nécessaire pour la subdivision et la déformation. B (S47, fils Polycount) : les n-gons plans sont inoffensifs sur surfaces planes statiques ; tout est triangulé au final ; ce qui compte est la triangulation contrôlée et le shading.

**Décision [ECLIPSE]** : pièces d'arme = rigides (Motor6D) → **B** : n-gons autorisés dans la SOURCE s'ils sont **plans et convexes** (`GEO007`) ; triangulation **explicite** dans la copie d'export (Triangulate + `keep_custom_normals`, V3/V5). **A** obligatoire pour ce qui se déforme (bras, gants, sangles).

## C5 — Base tangente : synchronisée vs « on suppose MikkTSpace »

Roblox ne documente publiquement que « OpenGL tangent space » (S06/S07), **pas** l'algorithme de tangentes. Blender bake en MikkTSpace OpenGL (S50, V7).
- A : supposer MikkTSpace et baker normalement (standard industrie).
- B : limiter la dépendance aux normal maps fortes (bevels en géométrie).

**Décision [ECLIPSE]** : B pour le VM (voir C1), A pour le WM et le tertiaire, **avec test** : bake de calibration (cube chanfreiné low + high) importé en Studio ; s'il n'y a pas de couture visible → consigner « tangent basis compatible » dans `CALIBRATION_LOG.md`. `[EXPÉRIMENTAL]` tant que ce test n'est pas fait.

## C6 — Booléens non destructifs conservés vs nettoyage destructif

A : garder les modificateurs Boolean vivants jusqu'à l'export (itération, variantes). B : appliquer et nettoyer (topologie finale maîtrisée, pas de surprise de triangulation).

**Décision [ECLIPSE]** : A dans la **SOURCE** ; la **copie d'export** applique tout (`eclipse_export.py --apply-modifiers`). Nettoyage destructif (dans une nouvelle version SOURCE) uniquement si le validator signale sur le mesh évalué : slivers (`GEO009`), n-gons concaves/non plans (`GEO007`), dégradés (`SHD002`), ou si un bake est prévu sur cette pièce. Détails : TOPOLOGY §Booléens.

## C7 — Résolution de texture : historique 1K VM / 512 WM vs 2K (4K possible depuis 2026)

A : garder 1024/512 (historique ECLIPSE). B : monter en 2K puisque Roblox streame et supporte la 4K (S15). **Décision [ECLIPSE]** : la résolution se **calcule** depuis la texel density cible et la surface (MATERIALS §Résolution, `UV005` donne la recommandation). VM : 1K par défaut, 2K si la surface dépliée l'exige ou si l'inspection rapproche la caméra ; WM : 512 par défaut, 256 si la surface est petite ; **jamais 4K** pour une arme. Le streaming (S10) redescend sur appareils faibles, mais la mémoire reste le poste le plus coûteux (S09).

## C8 — Doc Roblox contradictoire : texture max 4096 ou 1024 ?

S06 dit « jusqu'à 4096 » puis « maximum 1024 » ; S15 (annonces 2026) confirme la 4K. **Décision** : limite dure **4096** (`MAT004` FAIL au-delà), budget ECLIPSE plus bas par profil (`max_texture_resolution`).

## C9 — Atlas vs textures uniques

Perf Roblox (S09) : trim sheets pour réutiliser la texture (environnements). Streaming (S10) : préférer les textures uniques aux atlas **sauf** pour des parts batchables, car demander une haute résolution sur un morceau d'atlas streame tout l'atlas.
**Décision [ECLIPSE]** : **un set de textures par arme et par modèle (VM, WM)**, partagé par toutes les MeshParts de cette arme (même importance à l'écran). Pas d'atlas multi-armes. Trim sheets réservés aux décors.

## C10 — Padding UV

Pro : ≈12 px à 1K, 6 px à 512 (S41) ; Blender : marge de bake 16 px par défaut (V7). **Décision [ECLIPSE]** : `padding = résolution / 64` (16 px @1K, 8 px @512, 32 px @2K, min 4) pour l'espacement des îlots ; marge de bake = même valeur au minimum, mode `EXTEND` pour les maps qui descendent en mip (`UV006`).

## C11 — FBX vs glTF vers Roblox

S03 : glTF évite les réglages d'échelle. S17 : l'importeur glTF de Roblox a eu des bugs de normals (arêtes vives lissées, normal maps cassées — 2023/2024). **Décision [ECLIPSE]** : **FBX** (historique validé, normals préservées). glTF `[EXPÉRIMENTAL]` : à retester avec l'asset de calibration avant toute adoption.

## C12 — Preset d'axes FBX : officiel Roblox (Forward Z, Up Y) vs défaut Blender (−Z, Y)

V6 : les deux sont cohérents, ils diffèrent de 180° autour de l'axe vertical. Officiel : l'avant du modèle est **Blender −Y** (convention « Front » de Blender). Défaut : l'avant est **Blender +Y**. ECLIPSE a « corrigé l'orientation » historiquement sans que le preset exact soit archivé.
**Décision [ECLIPSE]** : **ne rien changer sans preuve**. Le futur agent local lit l'orientation d'ECLIPSE-1 dans Blender (où pointe la bouche ?) et la compare à la table ; il confirme avec l'asset de calibration. Défaut du validator : `blender_forward = -Y` (preset officiel), modifiable dans la config.

## C13 — « Apply Transform » (bake_space_transform) à l'export FBX

A : désactivé (défaut, preset Roblox) → les objets portent une rotation de conversion d'axes (V4). B : activé → géométrie convertie, aucune rotation d'objet ; marqué **expérimental** et cassé avec armatures/animations (S21).
**Décision [ECLIPSE]** : A. B seulement si la calibration montre des orientations parasites sur les MeshParts **et** qu'aucune armature n'est exportée.

## C14 — Nombre de segments de bevel

1 segment + WN (S37 : méthode la plus répandue) vs 2–3 segments (arête « ronde » à l'œil) vs beaucoup de segments (« crime contre le temps réel », S24/S37).
**Décision [ECLIPSE]** : VM **1** par défaut ; **2–3** sur les arêtes de silhouette haute proches de la caméra et les grands rayons ; **max 3** (`BEV001`) ; WM **0–1**. Coût mesuré V1.

## C15 — Kitbash / pièces tierces

A : tout modéliser (identité maximale). B : bibliothèque de fixations génériques (vitesse, cohérence).
**Décision [ECLIPSE]** : B pour les **petites pièces génériques** (vis, écrous, inserts) si licence OK ; interdiction des pièces reconnaissables ou de grande taille provenant d'assets tiers. Voir HARDSURFACE §Fixations et ASSET_LICENSE_GUIDE.

## C16 — Échelle du Viewmodel : réaliste vs ajustée à la vue FPS

Beaucoup de FPS utilisent une FOV de viewmodel séparée (S48). Roblox n'en a pas nativement ; le VM est placé en espace caméra et dimensionné pour les bras.
**Décision [ECLIPSE]** : modéliser à l'**échelle du rig de bras ECLIPSE** (mesurée localement), sans ré-échelle dans Roblox (sinon texel density, bevels et clearances mentent). Toute astuce de FOV/échelle scriptée doit être documentée dans le rig.

## C17 — Mécanismes : MeshParts + Motor6D vs mesh skinné (bones)

A : pièces rigides séparées, Motor6D (pratique Roblox FPS courante, visibilité par pièce, pivots explicites). B : un mesh skinné avec bones (moins de parts, mais pièces rigides skinnées = poids à 1.0, rig plus lourd à maintenir, problèmes d'attache décrits en S17 communauté).
**Décision [ECLIPSE]** : conserver **A** (déjà en place). Bones réservés aux éléments déformables (aucun sur ECLIPSE-1).
