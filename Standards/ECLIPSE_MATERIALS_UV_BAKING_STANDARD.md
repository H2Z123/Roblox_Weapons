# ECLIPSE — Matériaux, UV, texel density, PBR, roughness, baking

Objectif : une arme **premium, utilisée, propre** — ni plastique, ni rouillée, ni sale — lisible alors qu'elle est presque noire. Tags : voir `BLENDER_PRODUCTION_STANDARD.md`. Faits : `Knowledge/Blender/ROBLOX_PLATFORM_FACTS.md`.

<a id="materiaux-roblox"></a>
## 1. Contraintes Roblox `[OFFICIEL]`

- **Un matériau par MeshPart** ; un seul UV set ; UV en 0–1 ; overlaps permis (S06). Plusieurs matériaux dans une même mesh Blender = à éviter (`MAT001`) : séparer en MeshParts ou fusionner en un seul set.
- **SurfaceAppearance** : ColorMap (+alpha), NormalMap (**OpenGL tangent**), RoughnessMap, MetalnessMap, EmissiveMask — **cartes séparées**, pas de packing ORM (S07).
- Tint gratuit via `SurfaceAppearance.Color` (multiplie la ColorMap) : variantes de couleur sans nouvelle texture (S07, S09).
- Nommage : `M_<Asset>_<Surface>` pour les matériaux, `T_<Asset>_<Part>_<Map>` pour les images (NAMING).

<a id="uv"></a>
## 2. UV

`[PRO]` S40/S41 + `[ECLIPSE]` :
- **Coutures** : sur les arêtes dures (obligatoire si normal map, `SHD007`), aux changements de matériau, dans les zones cachées (dessous, arrière des pièces, intérieur du pontet), jamais au milieu d'un grand plan visible.
- **Îlots redressés** (alignés H/V) pour les pièces hard-surface : moins d'aliasing aux mips, meilleur packing.
- Pas d'étirement : `UV008` (surface dont la densité s'écarte ×4 de la médiane).
- Pas d'îlot dégénéré (`UV004`).
- **Un seul UV set** (`UV002`), 0–1 à l'export (`UV003`).
- Échelle d'îlot proportionnelle à la surface 3D (densité uniforme), puis **exceptions volontaires** : +25–50 % pour ce que la caméra VM voit de près (dessus arrière, trappe, viseur), −50 % pour ce qu'elle ne voit qu'en inspection (dessous).

<a id="texel-density"></a>
### Texel density

Références pro `[PRO]` S39 : 10,24 px/cm (héros / FPS) ≈ **287 px/stud** ; 5,12 px/cm ≈ **143 px/stud** (1 stud = 28 cm).
Dérivation ECLIPSE (rapport texel/pixel ≈ 1 à la distance d'usage) : VM à 2 studs = 386 px/stud en 1080p ; WM à 12 studs = 64 px/stud.

| Profil | Minimum (`UV005`) | Cible | Uniformité |
|---|---|---|---|
| Viewmodel | 256 px/stud | 384–512 (zones proches) | p90/p10 ≤ 2 |
| Worldmodel | 48 px/stud | 64–96 | p90/p10 ≤ 2,5 |

Roblox recommande une densité **quasi uniforme** pour que le streaming choisisse la bonne résolution (S10).

<a id="padding"></a>
### Padding

`[ECLIPSE]` C10 : espacement des îlots ≥ **résolution / 64** : 8 px @512, 16 px @1K, 32 px @2K (`UV006`). Marge de bake au moins égale, mode `Extend`. Un padding trop faible produit les **fines lignes le long des coutures** au loin (SHADING §6).

<a id="miroir"></a>
### Miroir, superposition, trim sheets

- Superposition/miroir autorisés (Roblox, S06) **seulement** pour des parties sans usure unique ni marquage (faces intérieures, pièces symétriques cachées). Les faces principales visibles du VM restent **uniques** (usure asymétrique crédible).
- Pour baker : coquilles miroir/superposées **décalées d'exactement 1 tuile UV**, jamais supprimées ; à remettre en 0–1 dans la copie d'export `[PRO]` S40.
- Trim sheets : réservés aux décors ; **un set de textures par arme** (C9).

<a id="resolution"></a>
## 3. Résolution de texture (stratégie adaptative)

Calculée, pas dogmatique (C7) : `résolution = next_pow2( sqrt(surface_dépliée × densité² / efficacité_de_packing) )` — fournie par `UV005` (`recommended_resolution_for_target`).

| Surface dépliée (stud²) | VM 256 px/stud | VM 384 | VM 512 | WM 64 | WM 96 |
|---:|---:|---:|---:|---:|---:|
| 1,5 | 512 | 1024 | 1024 | 128 | 256 |
| 2,5 | 512 | 1024 | 1024 | 128 | 256 |
| 4,0 | 1024 | 1024 | 2048 | 256 | 256 |
| 6,0 | 1024 | 2048 | 2048 | 256 | 512 |

(efficacité de packing supposée 0,7). Règles `[ECLIPSE]` : VM **1K** par défaut, **2K** si le calcul l'exige ou si l'inspection rapproche la caméra à ~1 stud ; WM **512** par défaut (l'historique 1K/512 d'ECLIPSE reste valable si la densité est atteinte) ; **jamais 4K** ; puissances de deux (`MAT004`). Le streaming Roblox redescend automatiquement sur appareils faibles (S10/S15) mais la mémoire reste ∝ pixels (S09).

<a id="valeurs-pbr"></a>
## 4. PBR : bibliothèque de surfaces ECLIPSE

Principes `[PRO]` S33/S34 + `[OFFICIEL]` S07 : metalness **binaire** ; albedo diélectrique ≥ 30 sRGB (idéal ≥ 40–50) ; métal nu ≥ 160–180 sRGB (mesures S49 : fer 192, titane 177, inox 214) ; la **roughness porte la variation**. Décision « finition sombre » : C3.

| Surface | Metallic | Base color (sRGB) | Roughness de base | Notes |
|---|---|---|---|---|
| Revêtement industriel sombre (carcasse, trappe) | 0 | 38–55, neutre à légèrement froid | 0,55–0,70 (±0,1 par zone) | surface principale ; « noir » = revêtement, pas métal |
| Polymère texturé (poignée, inserts) | 0 | 30–45 | 0,65–0,80 | micro-relief en normal map ; contraste de roughness avec la carcasse |
| Métal usiné (âme, couronne de bouche, nœuds de charnière, contacts) | 1 | 150–190 (acier) | 0,25–0,40 | seulement sur surfaces fonctionnelles et arêtes usées |
| Métal brossé (accents) | 1 | 170–200 | 0,30–0,45 | Roblox n'a pas d'anisotropie : stries fines en roughness/normal dans la direction d'usinage |
| Métal peint (panneau d'accent) | 0 | selon DA | 0,35–0,55 | réf. Roblox « painted metal » R 0,3 / M 0 (S08) |
| Cartouche (alliage type laiton) | 1 | ≈ 245, 228, 175 (laiton mesuré, S49) | 0,25–0,40 | culot plus rugueux, arêtes plus lisses |
| Accents lumineux | 0 | sombre | 0,5 | EmissiveMask + EmissiveStrength modérée (pas de Neon) |
| « Gunmetal » (exception C3) | 1 | 110–150 | 0,3–0,5 | **exception documentée seulement**, comparée en Studio ; `MAT007` avertit |

Valeurs = points de départ `[ECLIPSE]` ; ajustement final **dans Roblox Studio**, jamais seulement dans Blender (S07 : ne pas régler pour un seul éclairage).

<a id="roughness"></a>
## 5. Roughness : ce qui empêche une arme noire d'être une masse noire

Sur une surface sombre, la couleur varie peu : ce sont les **reflets** (donc la roughness) qui dessinent les plans. Construire la roughness **comme une couleur**, en couches `[PRO]` S33/S36 :

| Couche | Rôle | Amplitude indicative (VM) |
|---|---|---|
| 1. Base par zone | Distinguer panneaux, pièces et matériaux sans changer la couleur (carcasse 0,62 / trappe 0,55 / poignée 0,75) | écarts de 0,05–0,15 entre zones voisines |
| 2. Grande échelle | Zones plus lisses là où la main frotte (dos de poignée, bord de trappe) ; plus mates dans les recoins | ±0,05–0,1, dégradés doux |
| 3. Micro-variation | Casser la perfection CG (bruit fin, micro-rayures directionnelles selon la manipulation) | ±0,03–0,08, haute fréquence **mais** lisible à la résolution (pas de bruit sous-pixel) |
| 4. Usure d'arête | Arêtes B1 exposées : revêtement usé → métal plus lisse | 1–3 texels de large au VM, < 3–5 % de la surface |
| 5. Traces | Empreintes/huile très légères près des contacts (trappe, poignée) | −0,05 à −0,1, quasi invisibles hors reflet |
| 6. Cavités | Poussière légère dans les creux (plus mat) | +0,05, surtout en inspection |

Interdits : roughness uniforme (look plastique, `MAT008` : écart-type < 0,02) ; bruit uniforme sans logique ; roughness très basse partout (chrome) ; usure en liseré propre et continu (l'usure réelle = micro-dégâts, S36).
Contrôles : afficher la roughness seule en niveaux de gris (les panneaux doivent se lire) ; Studio sous deux éclairages ; si reflet trop fort en incidence rasante → +0,1 (S07).

## 6. Usure « premium, utilisée, propre »

- Usure uniquement là où elle a une cause : arêtes B1 saillantes, bord de trappe, couronne de bouche, contour de chambre, dos de poignée.
- Pas de rouille, pas de crasse accumulée, pas de coulures ; AO de cavité discret.
- Asymétrie crédible (côté manipulé plus usé).
- WM : usure réduite à quelques accents de roughness (sinon bruit au loin).

<a id="espaces-couleur"></a>
## 7. Espaces couleur et formats

Base color **sRGB** ; normal, roughness, metalness, émissif **Non-Color** (`MAT005`). PNG 8 bits (24 bits pour color/normal). Normal map **OpenGL (Y+)** — Blender bake déjà +X +Y +Z `[VÉRIFIÉ]` V7 ; ne pas inverser le vert.

<a id="normal-maps"></a>
## 8. Normal maps

- Tangent space (`MAT006`) ; intensité réaliste ; pas de grands bevels simulés sur le VM (C1).
- Sur le WM, adoucir les hautes fréquences (aliasing spéculaire au loin, SHADING §6).
- Base tangente : Blender = MikkTSpace ; celle de Roblox non documentée → test de calibration (C5).

## 9. Baking (quand un asset plus complexe l'exige)

Workflow robuste `[PRO]` S31/S32/S40 :
1. **Low-poly final** : topologie figée, **triangulée**, UV finales (hard edges ⇔ coutures), échelle 1.
2. **High-poly** : même position ; bevels exagérés ×1,5–2 (≥ 3 texels à la résolution cible).
3. **Cage** : cage *moyennée* (ou extrusion Cycles) englobant le high sans le traverser ; ajuster la distance max de rayon ; même topologie que le low si cage manuelle (S24).
4. **Miroir/superposition** : décaler d'1 tuile ; bake ; revenir en 0–1 dans la copie d'export.
5. **Cartes** : Normal (tangent OpenGL) ; AO (option, souvent intégré à l'albedo WM très légèrement) ; Curvature/ID pour les **masques** d'usure (non exportés).
6. **Blender (Cycles)** : Bake Type Normal, Space Tangent, Selected to Active, Cage ou Extrusion, marge ≥ padding, `Extend`.
7. **Contrôler** : coutures, *skewing* sur vis/trous (corriger par cage locale ou géométrie de support), bords d'îlots.
8. **Tester dans Roblox** : couture visible ? → vérifier C5 et §8.

Cas ECLIPSE principal : **bake VM → WM** (le VM mid-poly est le high-poly du WM, C1).

<a id="budgets"></a>
## 10. Budgets matériaux/textures

| | VM | WM |
|---|---|---|
| Sets de textures | 1 (+1 émissif/verre si indispensable) | 1 |
| Résolution | 1K (2K justifié) | 512 (256 possible) |
| Maps | Color, Normal, Roughness, Metalness (+EmissiveMask) | Color, Normal, Roughness, Metalness |
| Matériaux Blender distincts | ≤ 4 (`MAT009`) | ≤ 2 |

## 11. Contrôles automatiques

`MAT001–MAT009`, `UV001–UV009`, `SHD007`, `NAM002/NAM003`.
