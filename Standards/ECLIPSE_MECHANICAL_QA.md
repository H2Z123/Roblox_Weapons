# ECLIPSE — QA mécanique

Prévenir les collisions MainBody / TopHatch / Cartridge et tout ce qui casse les animations. Automatique d'abord (validator), visuel ensuite (Blender puis Studio). Standard : `ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md`.

## Automatique (validator, profil `viewmodel` puis `worldmodel`)

| Contrôle | Règle | Attendu |
|---|---|---|
| Interpénétration au repos | `MOV001` | PASS (paires tolérées listées dans la config avec justification) |
| Jeu minimal des pièces mobiles | `MOV002` | ≥ 0,002 stud ou WARN justifié |
| Balayage trappe (0 → ouverture max) | `MOV003` scénario `hatch` | PASS |
| Insertion cartouche (trappe ouverte max) | `MOV003` scénario `reload` | PASS |
| Main (proxy) vs pièces mobiles | `MOV003` avec `_Proxies` dans le périmètre | PASS |
| Pièces mobiles définies | `MOV004` | PASS |
| Pivots | `PIV001`, `PIV002`, `PIV004` | PASS |
| Repère de poignée | `GRP001` | PASS |

## Visuel — Blender (pose manuelle ou driver, sur une copie)

**Trappe**
- [ ] Axe de charnière coaxial aux nœuds visibles ; rotation autour de l'axe attendu (pas d'orbite).
- [ ] Amplitude : fermée (0°) = affleurante ; ouverte max = sur une **butée** visible ; aucune pièce traversée à 25/50/75/100 % de l'arc.
- [ ] Dessous de trappe et intérieur de chambre finis (visibles en position ouverte).
- [ ] Jeu régulier trappe/carcasse en position fermée, sans z-fighting.

**Cartouche**
- [ ] Trajectoire rectiligne le long de `Chamber_Att`, libre quand la trappe est ouverte.
- [ ] Position chambrée : culot en contact, sans interpénétration ; jeu radial régulier.
- [ ] Position hors de l'arme : aucune géométrie d'arme sur la trajectoire de la main qui l'amène.

**Poignée / main**
- [ ] Proxy de main en prise : aucun doigt dans la carcasse/pontet ; paume sur `Grip_Att`.
- [ ] Trappe et cartouche ne balaient ni le pouce ni le poignet.

**États**
- [ ] Pose de repos Blender = frame 0 de l'animation Roblox (fermée, cartouche chambrée ou absente selon convention).
- [ ] Toute pièce mobile modifiée → balayage refait **et** animations existantes revues (keyframes aux extrêmes).

## Studio (après import, place de test)
- [ ] Motor6D créés sur les `_Att` de charnière (articulation au bon endroit).
- [ ] Rechargement complet et inspection complète sans traversée visible (ralenti ×0,25 si possible).
- [ ] Main sur la poignée pendant toute l'inspection (GRIP §4).
