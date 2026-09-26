# ECLIPSE — QA performance

Budgets et justification : `ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md` §3 et `ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md` §10. Chiffres `[OFFICIEL]` : 20 000 tris/MeshPart, 4096 px max, instancing = même MeshContent + SurfaceAppearance identique.

| # | Contrôle | VM | WM | Outil |
|---|---|---|---|---|
| 1 | Triangles par MeshPart | ≤ 12 000 (FAIL > 20 000) | ≤ 4 000 | `BUD001` |
| 2 | Triangles total | 15–30k | 2–6k et ≤ 40 % VM | `BUD002`, `VMWM001` |
| 3 | Nombre de MeshParts | ≤ 16 | ≤ 6 (idéal 1–3) | `BUD003` |
| 4 | Matériaux / sets de textures | ≤ 4 mat., 1 set (+1) | ≤ 2 mat., 1 set | `MAT009`, `VMWM001` |
| 5 | Résolution | 1K (2K justifié par `UV005`) | 512 | `MAT004`, `UV005` |
| 6 | Texel density uniforme | p90/p10 ≤ 2 | ≤ 2,5 | `UV005` |
| 7 | Segments de bevel | ≤ 3 | ≤ 1 | `BEV001` |
| 8 | Bevels invisibles (tris sans valeur) | aucun < 2 px à 2 studs | aucun < 2 px à 12 studs | `BEV002` |
| 9 | Micro-géométrie invisible | aucune | aucune | `GEO010`, `BUD004` |
| 10 | Géométrie dupliquée / faces en double | 0 | 0 | `GEO004`, `GEO008` |
| 11 | Géométrie cachée dans tous les états | supprimée | supprimée | visuel + `BUD004` |
| 12 | Coupeurs / objets cachés exportés | 0 | 0 | `EXP002`, `EXP004` |
| 13 | Uploads dupliqués (même mesh, IDs différents) | 0 | 0 | Studio (script de la doc perf S09) |
| 14 | SurfaceAppearance identiques entre instances WM | — | oui (instancing) | Studio |
| 15 | RenderFidelity | Automatic | Automatic (jamais Precise) | Studio |
| 16 | CollisionFidelity | Box | Box | Studio |
| 17 | Draw calls / mémoire | Render Stats (Shift+F2), avant/après, 1 VM + 16 WM à l'écran | | Studio |

**Règle valeur/coût** : un dépassement de budget n'est acceptable que si la table `BUD004` montre que les triangles supplémentaires vont à des éléments **grands à l'écran** (silhouette, mécanisme) et qu'aucune pièce petite à l'écran n'est lourde. Consigner la justification et recalibrer les budgets du standard après le premier audit d'ECLIPSE-1.
