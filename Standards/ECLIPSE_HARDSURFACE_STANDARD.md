# ECLIPSE — Standard hard-surface et design de prop

Portée : forme, hiérarchie visuelle, langage de formes, logique de construction et détails des armes ECLIPSE. Bevels → `ECLIPSE_BEVEL_STANDARD.md` ; shading → `ECLIPSE_SHADING_STANDARD.md` ; contre-exemples → `ECLIPSE_ANTI_MELTED_PLASTIC.md`.

## 1. La règle de hiérarchie visuelle ECLIPSE

On travaille **toujours** dans cet ordre, et on ne passe au niveau suivant qu'après validation par capture. `[ECLIPSE]` fondé sur `[PRO]` (S36, S42, principes « big/medium/small » et « rest areas » communs au design hard-surface).

| Niveau | Contenu | Part de l'attention visuelle | Test de passage |
|---|---|---|---|
| **PRIMARY** | Silhouette, 3 à 5 masses (bloc carcasse/chambre, ensemble canon, poignée, trappe supérieure, pontet) et leurs proportions | ≈ 60–70 % | Silhouette **noire** reconnaissable à l'angle VM (FOV 70) **et** en vignette 64 px (WM) ; distincte d'une arme réelle |
| **SECONDARY** | Ruptures de plans, panneaux, séparations de matériaux, mécanismes lisibles (trappe, chambre, charnière), marches et renfoncements — 5 à 12 éléments | ≈ 25–30 % | En gris neutre sans texture, on comprend « comment ça s'ouvre, où va la cartouche, où va la main » |
| **TERTIARY** | Fixations, rainures, micro-découpes, marquages, texture de grip, usure | ≤ 10 % | Groupé autour des points fonctionnels ; ≥ 30–40 % de la surface visible reste calme |

**Interdictions** :
- Commencer le TERTIARY avant que PRIMARY et SECONDARY soient validés par l'utilisateur.
- « Réparer » une silhouette faible par des micro-détails (le travers classique des générations procédurales/IA : densité uniforme, rien ne domine).
- Répartir les détails uniformément : la **densité doit varier** (zones de repos contre grappes de détails).

**Règle d'écart d'échelle** : deux niveaux consécutifs diffèrent d'au moins **2 à 3×** en taille (grand / moyen / petit). Tout « moyen partout » est refusé.

## 2. Langage de formes ECLIPSE

`[ECLIPSE]` (direction artistique fournie : industriel premium, trapézoïdal/octogonal, plan, angulaire).

- **Dominant** : sections **trapézoïdales** (effilées vers l'avant ou le haut), cylindres traités en **octogones** (pans coupés à 45°), grands **plans**.
- **Vocabulaire d'angles restreint** : 45° principal, 30°/60° secondaires. Pas d'angles arbitraires : chaque angle se répète ailleurs sur l'arme.
- **Répétition à trois échelles** : le même motif (trapèze à pans coupés) sur une masse PRIMARY, un panneau SECONDARY et un évent TERTIARY → cohérence immédiate.
- **Dur / doux** : ≈ 80 % de plans durs, ≈ 20 % de formes douces **uniquement là où la main ou une pièce entre en contact** (renflement de paume, détente, culot de cartouche). Le contraste dur/doux est ce qui rend les zones douces précieuses.
- **Lignes directrices** : les lignes principales suivent l'**axe du canon** ; les lignes secondaires reprennent les angles du vocabulaire. Une ligne qui ne mène nulle part est supprimée.

## 3. Poids visuel « compact mais lourd »

- Masse concentrée **autour de l'axe du canon et au-dessus de la main** ; l'avant peut s'effiler, l'arrière reste massif.
- **Épaisseur de paroi visible** aux ouvertures (trappe ouverte, bouche, évents) : une coque fine lue en tranche = jouet/plastique. Montrer une matière pleine avec un chanfrein B2 sur la tranche.
- Marches et plans étagés plutôt que transitions lissées : chaque marche projette une ombre qui « pèse ».
- Pas de pièces flottantes : tout élément est **tenu** (vis, glissière, charnière, emboîtement visible).

## 4. Construction crédible (logique mécanique)

Chaque pièce doit répondre à trois questions — sinon elle est redessinée ou supprimée :
1. **Comment est-elle tenue ?** (vis, goupille, glissière, soudure, emboîtement)
2. **Comment est-elle assemblée/démontée ?** (lignes de panneau aux jonctions réelles, pas décoratives)
3. **Comment bouge-t-elle ?** (axe visible : nœuds de charnière, butées, jeux — voir PIVOTS_MECHANISMS)

- **Lignes de panneau** : suivent les jonctions de construction ; commencent et finissent sur une arête ou un élément ; ne traversent pas une forme au hasard ; largeur d'une seule classe par arme.
- **Séparation des matériaux** = fonction : carcasse revêtue, canon/âme en métal usiné, poignée polymère texturée, arêtes usinées sur les pièces manipulées.
- **Intersections** : soit une jonction booléenne propre avec chanfrein, soit une pièce séparée avec un **jeu** et une ligne d'ombre. Jamais d'interpénétration « qui passe » (`MOV001`).
- **Point focal unique** : la zone trappe/chambre (mécanisme signature d'une arme à une cartouche) ou la bouche. Contraste et densité de détail les plus forts s'y trouvent ; le reste la soutient.
- **Narration minimale** : usure là où la main et la cartouche frottent, pas ailleurs (voir MATERIALS §Usure).

## 5. Lisibilité à trois distances

| Distance | Ce qui doit se lire | Contrôle |
|---|---|---|
| VM (1,5–3 studs) | Silhouette haute, mécanisme de chargement, qualité des arêtes, matériaux | Capture FOV 70 à 1080p ; 1440p pour l'inspection |
| Inspection (≈ 1 stud) | Transitions, fixations, usure, tranches | Capture caméra d'inspection |
| WM (8–50 studs) | Silhouette et 2–3 masses de valeur contrastée | Capture 12 et 25 studs ; vignette 64 px |

Voir `ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md` pour ce qui devient géométrie, normal map, roughness ou disparaît.

## 6. Fixations, inserts et kitbash

`[PRO]` + `[ECLIPSE]` :
- **2 à 3 tailles** de vis maximum par arme ; têtes **noyées** (lamage) pour le look premium ; empreinte cohérente (hex ou Torx-like générique) sur toute l'arme.
- Placement **aux jonctions** (là où deux pièces se tiennent), en **paires ou alignements réguliers** ; jamais « saupoudrées ».
- Géométrie réelle dans le VM seulement si la tête fait **≥ 6–8 px** à la distance VM (≈ 0,016–0,02 stud de diamètre à 2 studs, 1080p). En dessous : normal map/texture. WM : omission ou texture.
- Cylindres de fixation : nombre de côtés selon `TOPOLOGY §Cylindres` (une tête de vis n'a presque jamais besoin de plus de 8–12 côtés).
- **Kitbash** : autorisé pour de **petites pièces génériques** (vis, écrous, inserts, ressorts) avec statut `LICENSE_OK` ; **interdit** pour toute pièce reconnaissable ou de grande taille provenant d'un asset tiers (identité et droits). Voir `Knowledge/Blender/ASSET_LICENSE_GUIDE.md` et C15.
- Outil gratuit utile : BoltFactory (S75) pour générer des bases de vis à ré-optimiser (il génère trop de segments pour le temps réel : réduire).

## 7. Garde-fous contre « beaucoup de détails, aucun design »

Avant chaque ajout TERTIARY, répondre oui aux quatre :
1. La silhouette et les masses sont-elles validées (captures) ?
2. Ce détail explique-t-il une fonction (tenue, assemblage, mouvement, prise) ?
3. Est-il dans une grappe voisine d'un point fonctionnel, en laissant une zone de repos ?
4. Est-il visible (≥ 3 px) à la distance où il sera vu ?

Mesures d'appui : `BUD004` (table valeur/coût), `GEO010` (micro-îlots invisibles), `BEV006` (distribution des largeurs de bevel).

## 8. Application à ECLIPSE-1 (sans redessin)

- Conserver l'identité : silhouette générale, proportions de la trappe, logique « une cartouche ».
- Audit PRIMARY : la silhouette lit-elle « lourde et compacte » ? Sinon, ajuster des **volumes existants** (épaisseurs, étagements) plutôt qu'ajouter des pièces.
- Audit SECONDARY : ruptures de plans sur les grandes faces latérales (sinon masse noire uniforme), séparation lisible trappe/carcasse, logique de charnière visible.
- Canon : notes dédiées `Knowledge/Blender/ECLIPSE1_BARREL_DESIGN_NOTES.md`.
- Toute modification de silhouette = proposition avec captures avant/après, validée par l'utilisateur.
