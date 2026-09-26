# ECLIPSE — Pivots, repères et mécanismes animables

Objectif : des pièces mobiles qui **ne se traversent jamais**, des pivots **intentionnels** et un transfert propre vers le rig Roblox (MeshParts + Motor6D, C17). Problème historique à prévenir : collisions MainBody / TopHatch / Cartridge. Tags : voir `BLENDER_PRODUCTION_STANDARD.md`.

## 1. Ce que Roblox fait des origines `[OFFICIEL]` + communauté

- Le `CFrame` d'une MeshPart est au **centre de sa boîte englobante** ; l'origine Blender devient son **`PivotOffset`** si « Use Imported Pivot » est actif (défaut) (S04, S13, S17).
- Le pivot du **Model** importé = origine de la scène si « Set Pivot to Scene Origin » (défaut).
- Un **Motor6D** ne lit pas le pivot : l'articulation est définie par `C0`/`C1`. Le moyen fiable de transporter une charnière de Blender à Roblox est un **Empty `*_Att`** → converti en **Attachment** (S05).
- `[EXPÉRIMENTAL]` : conservation exacte de l'orientation des `_Att` issus d'un FBX Blender → à confirmer avec `CAL_Hinge_Att` (asset de calibration).

<a id="pivots"></a>
## 2. Règles d'origine `[ECLIPSE]`

| Objet | Origine | Rotation d'objet |
|---|---|---|
| **Racine de l'arme** (monde 0,0,0) | Point de référence de l'arme. Si le rig existant en définit un : **le conserver**. Sinon : **point de paume de la poignée** (= `Grip_Att`, voir GRIP) — VM et WM partagent alors le même point d'attache main | — |
| Pièces **statiques** (carcasse, canon fixe, pontet…) | à la racine (0,0,0) → toutes les parts partagent le pivot de l'arme dans Studio | (0,0,0), échelle appliquée (`TRF001`, `TRF003`) |
| Pièces **mobiles** (trappe, cartouche, détente, chien…) | **sur l'axe du mouvement** : ligne de charnière pour une rotation ; point de référence de la trajectoire pour une translation | (0,0,0) si l'axe est parallèle à un axe de l'arme (cas courant) ; sinon rotation = orientation de l'axe, et `eclipse_role="moving"` |
| Repères (`*_Att`) | au point exact (voir §3) | identité = aligné sur l'arme, sauf `Grip_Att` (inclinaison de la poignée) |

Interdit : « Origin to Geometry » sur une pièce mobile (`PIV002`), origine loin de sa pièce sans raison (`PIV001`), échelle ou rotation non appliquées sur les statiques.

<a id="reperes"></a>
<a id="attachments"></a>
## 3. Repères standard (Empties, suffixe `_Att`)

Parentés à la MeshPart à laquelle ils appartiennent (`PIV004`) ; convention d'axes : **identité = mêmes axes que l'arme** (avant = axe `orientation.blender_forward` de la config, haut = +Z).

| Nom | Parent | Position | Axe principal | Usage |
|---|---|---|---|---|
| `Grip_Att` | pièce poignée / MainBody | centre de la surface de paume, sur l'axe de poignée, hauteur du majeur | **local +Z = axe de poignée** (bas → haut), incliné de l'angle de poignée | attache main, ADS de référence (GRIP) |
| `Muzzle_Att` | canon / MainBody | centre de la sortie d'âme | axe avant | effets de tir, sens de l'arme (`ORI001`) |
| `Aim_Att` | MainBody | point de visée (ligne de mire) | axe avant | alignement ADS |
| `Chamber_Att` | MainBody | centre de la chambre, cartouche en place | axe avant (axe de l'âme) | trajectoire d'insertion |
| `TopHatch_Hinge_Att` | MainBody | sur l'axe de charnière | **local X = axe de charnière** | Motor6D de la trappe |
| `Cartridge_Seat_Att` | Cartridge | référence du culot en position chambrée | axe avant | Motor6D / animation de la cartouche |
| `Eject_Att` | MainBody | fenêtre/zone de sortie | direction d'éjection | éjection éventuelle |

Profils : le validator exige `grip` + `muzzle` en VM et `grip` en WM (`PIV003`, config `markers`).

## 4. Règles de modélisation mécanique

<a id="jeux-et-clearances"></a>
### Jeux et clearances `[ECLIPSE]`

| Situation | Jeu | Raison |
|---|---|---|
| Pièces mobiles, partout pendant le mouvement | **≥ 0,002 stud** (≈ 0,6 mm ; ≈ 0,8 px en VM) | pas de z-fighting ni de contact numérique (`MOV002`) |
| Ligne de panneau / fente visible | 0,003–0,006 stud avec fond sombre (AO/ombre) | lisible comme une fente nette (≥ 1–2 px en VM) |
| Emboîtement caché | contact toléré (≤ 1e-4 stud), jamais d'interpénétration | `MOV001` |
| Cartouche dans la chambre | Ø chambre ≥ Ø cartouche + 2 × 0,002 ; profondeur ≥ longueur | insertion crédible |

### Arcs de rotation (trappe, capot, levier)

- La charnière se place **à l'arête où la pièce pivote**, **au niveau ou au-dessus** de la surface d'appui et **hors du volume** de la carcasse ; sinon, prévoir un **dégagement** (rayon ≥ distance axe → coin le plus éloigné + jeu).
- Piège vérifié sur scène de test : charnière posée sur le coin **bas** avant d'une trappe → au-delà de 90° le coin **haut** passe sous l'axe et entre dans la carcasse (collision détectée à ≈ 105° par `MOV003`) ; posée sur le coin **haut** avant → balayage 0–110° propre.
- Modéliser les **nœuds de charnière** coaxiaux à l'axe et une **butée** visible qui justifie l'angle d'ouverture maximal.

### Trajectoire d'insertion (cartouche)

- Trajet **rectiligne** le long de l'axe de chambre (`Chamber_Att`), dégagé quand la trappe est à son ouverture max.
- Les surfaces vues **uniquement en position ouverte** (intérieur de chambre, dessous de trappe, lèvres d'alimentation) doivent exister et être finies ; on ne supprime une face que si elle est cachée **dans tous les états**, inspection comprise.
- Contacts (culot/chambre, trappe/carcasse fermée) : contact ou jeu minimal, jamais d'interpénétration.

### Séparation des pièces mobiles

- Chaque pièce mobile = objet séparé (aucun sommet partagé), une MeshPart, un `roblox_name` stable.
- Pas d'enfant statique sous une pièce mobile (il bougerait avec elle) ; les descendants d'une pièce mobile bougent avec elle dans les balayages du validator.

<a id="balayage"></a>
<a id="collisions"></a>
## 5. Déclarer les mouvements et les tester

Propriétés personnalisées sur l'objet (ou `moving_parts` dans une config JSON du projet) :

| Propriété | Exemple trappe | Exemple cartouche |
|---|---|---|
| `eclipse_role` | `moving` | `moving` |
| `eclipse_motion_type` | `ROTATE` | `TRANSLATE` |
| `eclipse_motion_axis` | `X` (axe local) | `-Y` (ou `+Y` selon l'orientation) |
| `eclipse_motion_min` / `max` | `0` / `110` (degrés, à mesurer sur l'animation réelle) | `-0.35` / `0` (studs : dehors → chambrée) |
| `eclipse_motion_pivot` | *(vide = origine)* ou `TopHatch_Hinge_Att` | *(vide)* |

Scénarios combinés (config) : `"sweep_scenarios": [{"name":"hatch","sweep":"TopHatch"}, {"name":"reload","set":{"TopHatch":"max"},"sweep":"Cartridge"}]`.

Contrôles : `MOV001` (interpénétration au repos : croisements de surfaces **et** points enfouis), `MOV002` (jeu minimal), `MOV003` (collisions pendant le balayage, premier angle/offset en faute), `MOV004` (pièce mobile sans définition), `PIV001/PIV002`.
**Règle** : un FAIL `MOV003` se corrige par le **pivot, le jeu ou l'amplitude** — jamais en « trichant » dans l'animation.

## 6. Du modèle au rig Roblox (préparation)

- Un **Motor6D par pièce mobile** : `Part0` = pièce porteuse (souvent `MainBody`), `Part1` = pièce mobile ; articulation **à l'Attachment de charnière** :
  `C0 = Part0.CFrame:Inverse() * HingeAtt.WorldCFrame` ; `C1 = Part1.CFrame:Inverse() * HingeAtt.WorldCFrame` (`[EXPÉRIMENTAL]`, non exécuté dans cette session).
- Les animations et scripts adressent les pièces **par nom** : ne jamais renommer `MainBody`, `TopHatch`, `Cartridge` ; utiliser `roblox_name` si les noms Blender diffèrent (NAMING).
- Après import : vérifier que l'angle 0 de l'animation = pose de repos Blender, et que l'ouverture max ne dépasse pas l'amplitude validée par `MOV003`.
- Toute nouvelle version géométrique d'une pièce mobile impose de refaire le balayage **et** de vérifier les keyframes existantes (une trappe plus épaisse peut entrer en collision sur une animation déjà validée).

Checklist complète : `ECLIPSE_MECHANICAL_QA.md`.
