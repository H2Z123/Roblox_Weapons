# ECLIPSE — Standard de shading et de normals

Objectif : grandes faces planes, arêtes qui accrochent la lumière, aucune ligne parasite dans Roblox. Tags : voir `BLENDER_PRODUCTION_STANDARD.md`.

<a id="modele-de-normals"></a>
## 1. Modèle de normals dans Blender ≥ 4.1 `[OFFICIEL]` (S22, S20)

- **Auto Smooth n'existe plus.** La netteté est stockée dans des attributs : `sharp_edge` (arêtes) et `sharp_face` (faces plates). « Shade Smooth », « Shade Flat », « **Shade Auto Smooth** » (ajoute le modificateur/asset **Smooth by Angle**) et « Set Sharpness by Angle » (édition) les écrivent.
- Les **custom normals** (dont celles du modificateur Weighted Normal) s'utilisent directement, sans case à cocher.
- API : `Mesh.corner_normals` (normals par coin), `Mesh.has_custom_normals`, `Mesh.normals_domain`.
- **Traduction des tutoriels anciens** : « activer Auto Smooth 30° » = « Shade Auto Smooth 30° » (modificateur Smooth by Angle) ; « Auto Smooth requis pour Weighted Normal / Harden Normals » = plus nécessaire.

<a id="weighted-normals"></a>
## 2. Weighted Normals — le réglage ECLIPSE

`[PRO]` S30/S37 : chanfreins + normals perpendiculaires aux grandes faces → le dégradé de lumière est confiné aux chanfreins. `[VÉRIFIÉ]` V2 : sur une boîte chanfreinée, déviation résiduelle des grandes faces : lissé sans WN **28,9°** ; WN weight 50 (défaut Blender) **5,4°** ; weight 75 **0,5°** ; weight 100 **0°**.

**Réglage ECLIPSE** `[ECLIPSE]` :
| Paramètre | Valeur |
|---|---|
| Position | **dernier** modificateur de la pile (après Bevel, Boolean, Triangulate) |
| Mode | Face Area |
| Weight | **100** (≥ 90 accepté, `SHD004`) |
| Threshold | 0,01 (défaut) |
| Keep Sharp | ON |
| Face Influence | OFF (ON seulement avec Bevel « Face Strength ») |
| Shading de l'objet | Smooth (le WN n'a de sens que sur faces lissées) |

**Pièges** :
- Un modificateur qui change la topologie **après** WN (Bevel, Boolean, Subdivision, Solidify…) invalide ses normals (`SHD004`).
- Trianguler après WN sans `keep_custom_normals` altère les normals (0,27° mesuré, V3). Trianguler **avant** WN, ou avec `keep_custom_normals`.
- Surfaces courbes (cylindres, canon rond) : WN Face Area fonctionne si les facettes sont régulières ; sinon zones de facettage → soit plus de côtés (TOPOLOGY §Cylindres), soit exclure la zone via groupe de sommets.

<a id="harden-normals"></a>
## 3. Harden Normals (Bevel) `[PRO]` + prudence

Fonctionnait dans notre cas simple en 5.0.1 (V8), mais régressions signalées après 4.1 (S25). ECLIPSE : **désactivé**, remplacé par WN. S'il est utilisé : captures de contrôle obligatoires (`SHD006` le signale).

<a id="hard-edges-et-uv"></a>
## 4. Arêtes dures, coutures UV et normal maps `[PRO]` S31/S32

- Sur un mesh qui reçoit une **normal map bakée** : **toute arête dure (sharp) doit être une couture UV** (sinon ligne de couture dans le bake) — `SHD007`. L'inverse n'est pas vrai (une couture peut rester douce).
- Workflow mid-poly sans bake (VM) : arêtes dures seulement là où l'angle est franc et où WN ne suffit pas ; sinon laisser WN gérer.
- Trianguler **avant** le bake et exporter la **même** triangulation (TOPOLOGY §Triangulation).

<a id="roblox"></a>
## 5. Ce qui arrive dans Roblox

- FBX « Normals Only » (défaut) exporte les normals par coin ; l'aller-retour Blender les conserve exactement (V5). La communauté rapporte que l'importeur **FBX** Roblox les préserve ; l'importeur **glTF** a eu des bugs (S17) → FBX. `[EXPÉRIMENTAL]` : confirmer avec `CAL_WeightedNormals` de l'asset de calibration.
- Normals très déviées de leur face (> 75°) : triangles noirs et un artefact de « brillance » signalé à incidence rasante dans Roblox (S17) → `SHD003`. Typiquement sur de minuscules faces de chanfrein : vérifier en Studio sous plusieurs angles de soleil.
- `Make Double Sided` à l'import : **off** (coûteux, S04) ; des faces invisibles de dos = winding inversé à corriger (`GEO006`), pas à masquer.

<a id="diagnostic-des-fines-lignes"></a>
## 6. Diagnostic des fines lignes (problème déjà rencontré sur des Worldmodels)

Procédure : **localiser → identifier le motif → mesurer → corriger → prévenir**.

1. **Localiser** : dans Studio, orbiter autour du WM à 8, 12, 25 studs ; noter si les lignes suivent (a) des coutures UV, (b) des arêtes du mesh, (c) des bords de pièces, (d) n'apparaissent qu'au loin, (e) scintillent.
2. **Identifier** avec la table :

| Motif | Cause la plus probable | Vérification Blender | Correction |
|---|---|---|---|
| Suit les **coutures UV**, s'accentue au loin | Padding insuffisant → fuite de couleur de fond aux mips (textures WM 512 descendent vite) ; compression | `UV006` (espacement < 8 px @512), marge de bake | Espacer les îlots (res/64), marge de bake en `EXTEND`, remplir le fond avec la couleur moyenne (dilatation) |
| Suit une **arête dure** avec normal map | Arête sharp sans couture UV ; base tangente différente | `SHD007` | Couture UV sur chaque arête dure ; re-bake ; test de calibration C5 |
| Pixels clairs/sombres qui **scintillent** le long d'une jonction | Sommets non soudés / **T-junction** : fissure de rastérisation | `GEO004`, `GEO005` | Merge by Distance ; ajouter le sommet manquant sur l'arête opposée |
| **Scintillement** entre deux surfaces | Faces coplanaires dupliquées (z-fighting) | `GEO008`, `MOV001` | Supprimer le doublon ; jeu ≥ 0,002 stud entre pièces |
| Liseré sombre/clair sur **triangles très fins** | Slivers (souvent issus de booléens / n-gons) → interpolation et aliasing spéculaire | `GEO009`, `GEO007` | Retopologie locale, triangulation contrôlée |
| Ligne sur la **silhouette** ou face noire | Winding inversé / faces de dos | `GEO006` | Recalculer à l'extérieur (sur copie), vérifier |
| Lignes brillantes **seulement au loin**, aspect « crénelé » | Aliasing spéculaire : normal map/rugosité trop détaillées pour la résolution WM | revue des maps WM | Adoucir la normal map WM, +0,05–0,1 de roughness sur le WM (S07 évoque +0,1 contre la brillance rasante) |

3. **Mesurer** : relancer le validator profil `worldmodel` ; joindre captures avant/après.
4. **Prévenir** : ces règles sont dans le profil `worldmodel` du validator et dans `ECLIPSE_VISUAL_QA_CHECKLIST.md`.

## 7. Checklist shading

- [ ] Grandes faces planes (`SHD002` PASS au profil concerné).
- [ ] WN dernier, weight ≥ 90, Keep Sharp (`SHD004`).
- [ ] Pas de bevel lissé sans contrôle de normals (`SHD005`).
- [ ] Pas de normals extrêmes (`SHD003`) ou vérifiées en Studio.
- [ ] Hard edges = coutures UV sur les meshes à normal map (`SHD007`).
- [ ] Pas de sommets non soudés / T-junctions / doublons / slivers (`GEO004/005/008/009`).
- [ ] Rendu Studio contrôlé sous au moins deux orientations de soleil.
