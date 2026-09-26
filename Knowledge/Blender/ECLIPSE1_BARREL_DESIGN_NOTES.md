# ECLIPSE-1 — Notes de design du canon

Objectif : donner au canon davantage de **profondeur, volume, stratification, texture et crédibilité** sans le transformer en canon cyberpunk surchargé, et **sans redessiner** ECLIPSE-1. Ces notes n'ont pas été appliquées au modèle (session cloud sans le fichier) : ce sont des pistes à auditer puis proposer à l'utilisateur. Tags : voir `Standards/BLENDER_PRODUCTION_STANDARD.md`.

## 1. Comment le canon est vu

| Situation | Ce que la caméra voit | Priorité |
|---|---|---|
| VM idle / tir / ADS | **dessus et flanc gauche**, en fuite vers l'avant, à 2–3 studs (257–386 px/stud) | profil de dessus, plans supérieurs, transitions carcasse → canon |
| Inspection | bouche de face, flanc droit, dessous, ~1 stud | couronne, âme, épaisseurs, fixations |
| WM | silhouette de profil à 8–50 studs | rapport de longueur, 1 marche de volume, âme sombre |

Conséquence : le dessus du canon est **toujours** visible → c'est là que les plans et la roughness travaillent ; la face avant ne se détaille qu'au niveau exigé par l'inspection.

## 2. Principes

1. **Stratifier en 3 couches au maximum** `[PRO]` (logique des canons frettés, S52) : (a) manchon/carénage extérieur revêtu, (b) tube intérieur en métal usiné qui dépasse d'une **marche**, (c) âme sombre et profonde. Chaque couche = un matériau et une classe de bevel.
2. **La profondeur se lit par emboîtement** : à la bouche, trois contours concentriques décalés de ≥ 4–8 px en VM (lèvre du manchon > couronne du tube > âme). Une **couronne en retrait** (lamage) crée un anneau d'ombre net.
3. **Âme** : cylindre intérieur réellement modélisé sur **≥ 2–3 diamètres** de profondeur en VM, dégradé sombre (AO/texture) ; sinon l'inspection révèle un « trou peint ».
4. **Ouvertures qui révèlent la couche intérieure** : quelques évents/fenêtres dans le manchon laissant voir le tube = l'indice de profondeur le plus fort — à condition de modéliser l'intérieur (VM) ; en WM, remplacer par texture sombre.
5. **Langage ECLIPSE** : section de manchon **octogonale ou trapézoïdale** avec un **méplat supérieur** (plan qui accroche la lumière depuis la vue VM et sert de ligne de mire) ; le tube intérieur peut rester rond (contraste dur/doux, fonction).
6. **Un seul rythme répétitif** (3–5 évents trapézoïdaux *ou* 4 cannelures) + **un seul accent** (couronne usinée claire). Pas de lignes lumineuses, pas de greebles aléatoires, pas de multiples rythmes superposés.
7. **Conicité** (« chase », S52) : profil de côté légèrement trapézoïdal vers l'avant → dynamisme et lecture « lourde à l'arrière ».
8. **Crédibilité** : le manchon est **tenu** (1–2 fixations aux jonctions, ou queue d'aronde) ; le tube a un épaulement visible à l'entrée de la carcasse ; pour un hand-cannon, 1–2 **ports de compensateur** sur le dessus près de la bouche justifient le recul (optionnel).

## 3. Matériaux (voir MATERIALS §4–5)

| Couche | Surface | Roughness |
|---|---|---|
| Manchon | revêtement industriel sombre, metallic 0 | 0,55–0,7, légèrement plus lisse sur le méplat supérieur (manipulation) |
| Tube intérieur | métal usiné, metallic 1, 150–190 sRGB | 0,25–0,4, **stries longitudinales** fines (usinage) |
| Couronne de bouche | métal usiné poli (accent focal) | 0,2–0,3, arête B1 légèrement usée |
| Âme | métal très sombre par AO/texture (pas un albedo métal noir) | 0,4–0,6 |

Traces de chaleur/poudre : très légères, près des ports et de la couronne uniquement ; jamais de suie étalée.

## 4. Budgets et topologie

- VM : le canon ≈ 15–25 % des triangles du VM. Côtés : TOPOLOGY §5 (rayon 0,06 stud → 16 côtés à 2 studs ; ou octogone 8 + chanfreins B1/B2). Âme : 10–12 côtés suffisent (vue de face seulement en inspection).
- Évents : booléens vivants en source (coupeurs dans `_Cutters`), nettoyés si `GEO009`/`SHD002` le demandent.
- WM : manchon + marche du tube + âme en texture ; évents en normal/roughness ou omis ; 6–8 côtés (colonne WM).

## 5. Trois variantes à explorer (blockout, puis choix utilisateur)

| Variante | Description | Force | Risque |
|---|---|---|---|
| **A. Manchon octogonal** | Manchon octogonal à méplat supérieur ; tube rond qui dépasse d'une marche ; couronne en retrait ; 3 évents trapézoïdaux latéraux révélant le tube | fidèle au langage octogonal ; profondeur forte | évents = coût triangles + intérieur à finir |
| **B. Conicité étagée** | Canon en deux étages (arrière épais 60 % / avant fin 40 %) séparés par une bague trapézoïdale ; 2 ports de compensateur sur le dessus | silhouette dynamique, logique « hand-cannon » | ports visibles en VM → à dimensionner ≥ 8 px |
| **C. Nervure et cannelures** | Nervure supérieure plane (ligne de mire) ; flancs plats ; 4 cannelures longitudinales sur le tube visibles sous la nervure ; léger évasement de bouche | très lisible de dessus, sobre | peut paraître « réel » si trop proche d'une arme existante |

Pour chaque variante : captures `VM_idle`, `VM_inspect` (bouche), `WM_12`, silhouette ; mêmes matériaux de test. Choisir **une** variante, puis appliquer B1/B2/B3 et la roughness.

## 6. Questions d'audit du canon actuel (à remplir localement)

- [ ] Le canon lit-il comme **un** cylindre uniforme ? (→ stratification manquante)
- [ ] Combien de niveaux de volume à la bouche ? (objectif ≥ 2–3)
- [ ] L'âme a-t-elle une profondeur modélisée ? Longueur ?
- [ ] Le dessus du canon offre-t-il un plan qui accroche la lumière depuis la vue VM ?
- [ ] Les proportions canon/carcasse lisent-elles « hand-cannon compact et lourd » ?
- [ ] Nombre de rythmes répétitifs présents (objectif : 1) ; accents (objectif : 1).
- [ ] Tris du canon / total VM ; côtés vs table ; bevels vs classes.
- [ ] Identité : quels éléments du canon actuel sont **à conserver absolument** ?
