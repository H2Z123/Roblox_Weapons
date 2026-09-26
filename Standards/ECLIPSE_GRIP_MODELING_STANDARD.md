# ECLIPSE — Poignée, ergonomie FPS et chaîne GRIP → PALM → WRIST → FOREARM

La poignée est le **contrat** entre le modèle et les bras. Bug actuel à rendre impossible par construction : pendant certaines phases d'inspection, un bras n'est visuellement **pas** sur la poignée. Tags : voir `BLENDER_PRODUCTION_STANDARD.md`.

## 1. Données ergonomiques de référence

| Donnée | Valeur | Nature |
|---|---|---|
| Angle de poignée (par rapport à la perpendiculaire à l'axe du canon) | 1911 ≈ 18°, Glock ≈ 22° | `[PRO]` S46 |
| Principe | « Bend the tool, not the wrist » : l'angle de l'outil garde le poignet neutre | `[PRO]` S45 (CCOHS) |
| Diamètre de prise cylindrique confortable | 30–40 mm, optimum ≈ 33 mm | `[PRO]` S45 (étude publiée) |
| Diamètre optimal relatif | ≈ **19,7 % de la longueur de main** | `[PRO]` S45 |
| Longueur de prise | ≥ largeur de main (≈ 85–90 mm adulte) | `[PRO]` S45 |

**Transposition ECLIPSE** `[ECLIPSE]` : les bras Roblox ECLIPSE ne sont pas à l'échelle humaine → on dimensionne **à partir du rig de bras**, pas en centimètres. Mesurer sur le mesh de bras FPS la longueur de main `Lh` (pli du poignet → bout du majeur), en studs :

| Cote de poignée | Formule de départ | Remarque |
|---|---|---|
| Épaisseur équivalente (circonférence / π) | ≈ 0,20 × Lh | section **ovale / rectangle arrondi**, pas un cylindre |
| Profondeur avant-arrière | ≈ 0,25–0,30 × Lh | |
| Largeur latérale | ≈ 0,15–0,19 × Lh | |
| Hauteur de prise utile | ≥ 0,50 × Lh | la main entière + l'auriculaire |
| Angle de poignée (rake) | **15–25°** (validator tolère 10–28°) | `GRP001` |
| Portée de détente (dos de poignée → face de détente) | ≈ 0,35–0,40 × Lh | `[EXPÉRIMENTAL]` à valider sur la pose de main |

Ce sont des **points de départ** : la vérité est la pose de main ECLIPSE vue en FPS.

## 2. Lisibilité en première personne

- En VM, la main **cache** l'essentiel de la poignée : le budget de détail va au **dos de la carcasse près de la main**, au *tang*/bec (zone pouce-index) et au bas de poignée (visible en inspection), pas aux flancs couverts.
- Éviter les **rainures de doigts** marquées : elles imposent une pose de doigts exacte et trahissent la moindre dérive d'animation. Préférer un renflement de paume doux + texture de grip.
- Hauteur d'axe du canon au-dessus de la main = bras de levier du relevé : un hand-cannon à axe haut « relève » davantage ; cohérent si le pivot de recul est au `Grip_Att`.
- Garder dégagé le **corridor central** de l'écran en idle/ADS (S43).

<a id="repere-grip"></a>
## 3. Le repère `Grip_Att` (définition exacte)

- **Type** : Empty nommé `Grip_Att`, enfant de la pièce qui porte la poignée (souvent `MainBody`) → Attachment dans Roblox.
- **Position** : centre de la zone de contact de la **paume** sur l'axe médian de la poignée, à hauteur du **majeur** (≈ 40–50 % de la hauteur de prise depuis le haut). Il doit être **à l'intérieur** du volume de la poignée (`GRP001`).
- **Orientation** : identité = axes de l'arme ; puis rotation autour de l'axe latéral (X Blender) de l'angle de poignée, de sorte que **local +Z = axe de poignée (bas → haut), incliné vers la bouche**. Avec `blender_forward = -Y` : rotation **+rake** autour de X (vérifié : +20° → rake mesuré 20°) ; avec `+Y` : rotation −rake.
- **Racine** : recommandé `[ECLIPSE]` que l'origine du monde (racine de l'arme) coïncide avec la **position** de `Grip_Att`, pour VM **et** WM (PIVOTS §2). Si le rig existant utilise une autre racine : la conserver et documenter l'offset.

## 4. La chaîne GRIP → PALM → WRIST → FOREARM

| Maillon | Règle de modèle | Règle de rig (à appliquer côté Roblox/animation) |
|---|---|---|
| GRIP | `Grip_Att` exporté avec le mesh ; identique VM/WM | — |
| PALM | La paume épouse la poignée sans interpénétration visible ; aucune pièce mobile ne balaie la zone de la main (tester avec un proxy de main, §5) | L'arme est **enfant de la main** (joint Main → Arme) avec un offset **constant** : `C0` = paume dans l'espace main, `C1` = `Grip_Att` dans l'espace arme (S43 : arme parentée à la main) |
| WRIST | Rake 15–25° → poignet neutre quand l'avant-bras suit l'axe du canon ; < 10° = déviation cubitale forcée ; > 30° = extension forcée | L'animation ne corrige pas un mauvais rake : corriger le modèle |
| FOREARM | Rien à l'arrière de l'arme (tang, trappe ouverte, arcs de levier) ne doit croiser le poignet/l'avant-bras | Avant-bras aligné, légèrement sous l'axe du canon en idle |

**Causes typiques du bug « main hors de la poignée en inspection »** (diagnostic, à vérifier localement — ne pas corriger à l'aveugle) :
1. Pendant l'inspection, l'arme est pilotée par un **autre joint** (caméra/racine) que la main → deux trajectoires indépendantes qui divergent.
2. Offset main→arme **différent** entre le rig d'animation (Blender/Moon) et le rig runtime (C0/C1).
3. **Origine/pivot de l'arme modifié** après l'authoring des animations (ré-import avec une autre origine).
4. Contraintes/IK non **bakées** : l'outil d'animation résolvait une IK que Roblox ne rejoue pas.
5. Différence d'échelle entre rig d'animation et runtime.
Le modèle aide en fournissant `Grip_Att` + une racine stable ; la correction relève de la mission Animation.

## 5. Contrôles

- Validator : `GRP001` (présence, rake dans [10°, 28°], point à l'intérieur de la poignée), `PIV003` (marqueur requis), `MOV003` avec un **proxy de main** statique (mesh de la main en pose de prise, collection `ECLIPSE1_VM_Proxies` incluse dans la validation mais exclue de l'export) pour vérifier que trappe/cartouche ne traversent pas la main.
- Visuel : captures VM idle, ADS, inspection (début/milieu/fin) — la paume reste sur la poignée, aucun doigt ne traverse la carcasse ou le pontet.
- Roblox (plus tard, mission Animation) : mesurer chaque frame l'écart entre `main.CFrame * C0` et `Grip_Att.WorldCFrame` (objectif : < 1 px à 1080p en VM).
