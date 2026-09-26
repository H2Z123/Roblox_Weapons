# ECLIPSE — Standard de topologie (et workflow booléen)

Pas de dogme « tout en quads » : la bonne topologie est celle qui **shade juste, s'exporte de façon prévisible, se modifie facilement et coûte ce qu'elle rapporte**. Tags : voir `BLENDER_PRODUCTION_STANDARD.md`. Désaccord de fond : `Knowledge/Blender/CONTROVERSIES_AND_DECISIONS.md` C4, C6.

## 1. Deux catégories, deux règles

| | STATIC HARD-SURFACE (rigide) | DEFORMING / ANIMATED GEOMETRY |
|---|---|---|
| Exemples ECLIPSE | Carcasse, canon, trappe, cartouche, détente, poignée (toutes les pièces Motor6D) | Bras FPS, gants, manches, sangles |
| Triangles | Acceptés partout où ils shadent bien | À éviter dans les zones de pli |
| N-gons | Acceptés en SOURCE si **plans et convexes** | Interdits dans les zones de pli |
| Quads | Utiles pour les surfaces courbes lissées et pour l'édition | Obligatoires aux articulations ; boucles autour des plis |
| Pôles | Hors des surfaces courbes visibles (pincements) | Jamais sur un pli |
| Priorité | Shading + silhouette + coût | Déformation propre, influences ≤ 4 `[OFFICIEL]` |

Toutes les pièces d'ECLIPSE-1 sont **rigides** : la colonne de gauche s'applique ; la colonne de droite concerne les futurs bras.

<a id="manifold"></a>
## 2. Intégrité

- **Fermé / manifold** : Roblox exige une géométrie *watertight* `[OFFICIEL]` S01. Arêtes ouvertes = lieu privilégié des fissures (T-junctions). Exception déclarée par la propriété `eclipse_allow_open=True` (ex. plan de décal). → `GEO001`.
- Pas de sommets isolés ni d'arêtes filaires (`GEO002`).

<a id="degenerate"></a>
- Pas de faces d'aire nulle ni d'arêtes de longueur nulle (`GEO003`) ; pas de faces dupliquées (`GEO008`) ; pas de triangles « aiguilles » (angle min < 1°, `GEO009`).

<a id="normals-orientation"></a>
- **Winding cohérent**, coques fermées orientées vers l'extérieur (`GEO006`) ; pas d'échelle négative (`TRF002`).

<a id="n-gons"></a>
## 3. N-gons

`[PRO]` S47 + fils Polycount : les n-gons plans sur surfaces planes sont inoffensifs ; le problème est la **triangulation imprévisible** des n-gons **non plans** ou **concaves** (moteur ≠ baker → artefacts).
- SOURCE : n-gons autorisés s'ils sont plans (écart < 0,2 % de leur diagonale) et convexes (`GEO007` : INFO sinon WARN).
- Surfaces courbes lissées : quads réguliers (le WN et l'interpolation y dépendent d'une répartition régulière).
- EXPORT : triangulation **explicite** (§4).

## 4. Triangulation

Toute géométrie est triangulée au final. Il faut **choisir** quand et comment :
- **Mid-poly sans bake (VM)** : Triangulate (Beauty) avec `keep_custom_normals`, **avant** le Weighted Normal ou juste avant l'export — les deux conservent les normals `[VÉRIFIÉ]` V3/V5. **Ne pas** utiliser l'option FBX `Triangulate Faces` (altère les weighted normals de 0,27°, V5).
- **Avec bake (WM, tertiaire)** : trianguler **avant le bake** et exporter exactement cette triangulation `[PRO]` S31.
- L'outil `tools/eclipse_export.py --triangulate` le fait dans la copie d'export.

## 5. Cylindres et formes courbes : combien de côtés ?

La qualité d'un cylindre se juge **à la silhouette** : l'écart maximal entre le polygone et le cercle (la *flèche*) doit rester sous ~0,5 px. `n ≥ π / acos(1 − e / (r·ppu))` (`mathutil.cylinder_sides`).

| Rayon (studs) | VM 2 studs 1080p | VM 1,5 stud 1440p (inspection) | WM 12 studs | WM 20 studs |
|---:|---:|---:|---:|---:|
| 0,02 | 10 | 12 | 6 | 6 |
| 0,04 | 14 | 18 | 6 | 6 |
| 0,06 | 16 | 22 | 8 | 6 |
| 0,10 | 20 | 26 | 8 | 8 |
| 0,15 | 24 | 32 | 10 | 8 |

`[ECLIPSE]` : prendre la colonne de la distance **la plus proche réellement atteinte** par cette pièce. Le langage ECLIPSE préfère d'ailleurs les **octogones** assumés (8 côtés + chanfreins) aux cylindres ronds pour les pièces non fonctionnelles.

## 6. Densité et pôles (statique)

- Densité proportionnelle à la **courbure visible**, pas uniforme : les grands plans n'ont besoin que de leurs contours.
- Pas de boucles de support inutiles (héritage de la subdivision) sur un asset mid-poly.
- Éviter les longs triangles qui traversent un plan éclairé de biais (interpolation + aliasing) : couper au plus court (`Shortest Diagonal`/`Beauty`).

## 7. Booléens : non destructif vs nettoyage

`[OFFICIEL]` S20/S23 : solvers **Exact** (défaut, robuste), **Float** (rapide, fragile aux coplanaires), **Manifold** (≥ 4.5, rapide et fiable, **opérandes manifold obligatoires**).

**Pratique ECLIPSE** `[ECLIPSE]` (C6) :
1. **SOURCE** : booléens vivants autorisés (itération, variantes). Coupeurs dans une collection exclue de l'export (`*_Cutters`), affichage *Bounds*/*Wire*, cachés au rendu (`EXP002` bloque sinon).
2. **Pile** : Mirror → Boolean(s) → Bevel → Triangulate → Weighted Normal.
3. **Solver** : Manifold si opérandes fermés (vitesse), sinon Exact ; Float déconseillé.
4. **Copie d'export** : tout est appliqué (`eclipse_export.py --apply-modifiers`), le validator tourne sur le résultat.
5. **Nettoyage destructif obligatoire** (dans une nouvelle version SOURCE, jamais sur place) si, sur le mesh évalué :
   - slivers (`GEO009`) ou n-gons concaves/non plans (`GEO007`) autour de la coupe ;
   - dégradés que WN ne corrige pas (`SHD002`) ;
   - un bake est prévu sur la pièce ;
   - coupe ronde sur surface courbe visible (ajouter la géométrie de support nécessaire).
6. **Ne jamais** laisser un booléen dont l'opérande est une pièce exportée (mélange de rôles).

## 8. Checklist topologie

- [ ] `GEO001–GEO010` sans FAIL ; WARN justifiés.
- [ ] N-gons restants plans et convexes.
- [ ] Triangulation explicite dans la copie d'export (normals conservées).
- [ ] Cylindres dimensionnés par la table §5.
- [ ] Booléens : coupeurs exclus, résultat propre ou nettoyé.
