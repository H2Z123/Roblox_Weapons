# ECLIPSE — Anti « plastique fondu »

Un hard-surface paraît « fondu » ou « généré » quand l'œil ne trouve plus de plans nets, d'arêtes qui accrochent la lumière ni de hiérarchie. Les causes sont **géométriques, de shading et de matériau** — souvent cumulées. Tags : voir `BLENDER_PRODUCTION_STANDARD.md`.

## 1. Symptômes → causes → corrections

| # | Symptôme visible | Cause probable | Correction | Détection |
|---|---|---|---|---|
| 1 | Les formes semblent gonflées, « savonnette » | Bevels trop larges par rapport à la forme | Largeur ≤ 10 % de la plus petite dimension de la pièce ; classes B1/B2/B3 | `BEV003` |
| 2 | Tout est arrondi pareil, rien ne domine | Même bevel sur toutes les arêtes (`limit_method NONE`, une seule largeur) | Hiérarchie d'arêtes : silhouette B1, panneaux B2, petites pièces B3 ; certaines arêtes restent vives | `BEV005`, `BEV006` |
| 3 | Dégradés sombres qui traversent les grandes faces | Normals interpolées sur toute la face (lissage sans contrôle) | Weighted Normal (Face Area, **weight 100**, Keep Sharp) en dernier ; ou sharp edges `[VÉRIFIÉ]` V2 | `SHD002`, `SHD005` |
| 4 | Reflets « coulants », pincements sur surfaces courbes | Subdivision sans boucles de support ; pôles sur surfaces courbes visibles ; n-gons non plans | Retopologie locale, boucles de support ou chanfreins réels ; n-gons plans uniquement | `GEO007`, visuel |
| 5 | Pas de plans : tout est bombé | Courbes décoratives sans fonction ; transitions lissées au lieu d'étagements | Revenir au langage trapèze/octogone ; remplacer les « blends » par des marches + chanfreins | visuel (HARDSURFACE §2) |
| 6 | Masse uniforme, lecture « bloc » | Aucune rupture de plan ni séparation de matériaux sur les grandes faces | Ajouter des ruptures SECONDARY (marches, panneaux fonctionnels), pas des micro-détails | visuel |
| 7 | Surfaces « plastique mat » | Roughness uniforme (~0,4–0,5), pas de variation | Roughness par zones + microvariation + usure (MATERIALS §Roughness) | `MAT008` (écart-type) |
| 8 | Métal qui ressemble à du plastique noir brillant | metallic 1 + albedo très sombre, ou metallic 0,5 | Revêtement diélectrique sombre OU métal crédible (≥ 160 sRGB) ; metallic binaire (C3) | `MAT007`, `MAT008` |
| 9 | Arêtes molles au loin (WM), crénelées de près | Bevels sous le seuil de visibilité ; normal map avec bevels trop fins qui disparaissent aux mips | Bevels ≥ 2 px à la distance d'usage ; bevels « exagérés » dans les bakes `[PRO]` S38 | `BEV002` |
| 10 | Détails « posés » sans raison, bruit visuel | Densité uniforme de micro-détails ; aucun point focal | Règle PRIMARY → SECONDARY → TERTIARY ; grappes + zones de repos | `BUD004`, `GEO010` |
| 11 | Tranches fines aux ouvertures | Coque sans épaisseur visible | Épaisseur de paroi montrée + chanfrein B2 sur la tranche | visuel |
| 12 | Shading faceté sur cylindres | Trop peu de côtés pour la taille à l'écran, ou trop + lissage raté | Côtés selon la formule de flèche (TOPOLOGY §Cylindres) + WN | visuel |

## 2. Principes de correction

1. **Corriger la forme avant le shading, le shading avant le matériau.** Un matériau ne sauve pas un volume mou.
2. **Aplatir** : rendre aux grandes faces leur planéité (normals perpendiculaires) ; la lumière doit se « casser » sur les chanfreins.
3. **Contraste d'arêtes** : quelques arêtes très nettes (petit chanfrein) à côté d'arêtes plus douces → l'œil lit la dureté.
4. **Moins mais mieux** : réduire le nombre de largeurs de bevel et d'angles plutôt qu'en ajouter.
5. **Roughness d'abord** pour les surfaces sombres : c'est elle qui dessine les plans et les panneaux (MATERIALS §Roughness).

## 3. Checklist (à cocher sur captures VM FOV 70 + WM 12 studs)

- [ ] Les grandes faces latérales et supérieures paraissent **planes** (reflet d'environnement non déformé).
- [ ] Chaque arête de silhouette accroche un liseré de lumière fin et continu.
- [ ] Au moins 3 niveaux de netteté d'arête distincts sont lisibles (B1/B2/B3 ou vif).
- [ ] Aucune face ne montre de dégradé sombre traversant (`SHD002` PASS).
- [ ] Aucun bevel > 10 % de la plus petite dimension de sa pièce (`BEV003` PASS) — ou exception justifiée.
- [ ] Les formes douces sont limitées aux zones de contact (paume, détente, cartouche).
- [ ] La surface sombre n'est pas une masse noire : panneaux et matériaux se distinguent par la **roughness**.
- [ ] metallic binaire ; métal nu ≥ 160 sRGB ; revêtements sombres ≥ 30 sRGB (`MAT007`).
- [ ] Les ouvertures montrent une épaisseur de matière.
- [ ] Il existe un point focal et des zones de repos.
