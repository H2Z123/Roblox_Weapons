# SOURCE_INDEX — Blender / Hard-surface / Game-ready (ECLIPSE)

Date d'accès de toutes les sources : **2026-09-26**. Identifiants `Sxx` cités dans tous les standards.

## Comment lire ce fichier

**Mode d'accès** — c'est important pour juger la confiance :

- **PLEIN TEXTE** : document lu en entier (dépôt GitHub officiel `Roblox/creator-docs` lu en `raw`, code source Blender, README GitHub, jeu de données).
- **SYNTHÈSE** : la session cloud avait un proxy réseau qui **bloquait** `create.roblox.com`, `docs.blender.org`, `developer.blender.org`, `polycount.com`, `marmoset.co`, `80.lv`, `adobe.com`, YouTube, etc. Ces sources ont été consultées via des résumés de moteur de recherche (extraits + synthèse), **pas lues intégralement**. Les passages exacts doivent être relus localement avant de citer un chiffre en dehors de ce projet.
- **MESURÉ** : expérience reproduite dans cette session avec `bpy` 5.0.1 (Blender en module Python) sur scènes synthétiques. Côté Blender uniquement : **rien n'a été testé dans Roblox Studio**.

**Confiance** : A = officiel ou mesuré · B = pratique pro convergente (plusieurs sources) · C = source isolée / communautaire / à vérifier.

**Vidéos** : YouTube et GDC Vault étaient bloqués. Aucune vidéo n'a été regardée. Le seul contenu vidéo utilisé (GDC 2015 Bungie, S43) l'a été via des résumés écrits ; il est traité au format « technique » demandé à la fin de ce fichier, avec cette réserve.

---

## 1. Roblox — officiel (PLEIN TEXTE via `raw.githubusercontent.com/Roblox/creator-docs`)

### S01 — General specifications (`art/modeling/specifications.md`)
- Auteur : Roblox · Catégorie : doc officielle · Confiance : A · Sujet : limites mesh / rig.
- Enseignements : **20 000 triangles max par mesh** ; géométrie **watertight** ; « pas de n-gons, quads si possible » ; pas d'épaisseur nulle. Rig : bones gelés (scale 1, rotation 0), **root bone en 0,0,0**, **max 4 influences / vertex**, **aucune influence sur le root**.
- Pertinent ECLIPSE : plafond dur par MeshPart (règle `BUD001`), règles d'armature (`ARM001`).
- Non pertinent : cages (layered clothing), specs avatar.
- Note : « no n-gons » est écrit pour des assets génériques ; en pratique l'exporteur/importeur triangule. ECLIPSE triangule volontairement dans la copie d'export (voir TOPOLOGY).

### S02 — Export settings (`art/modeling/export-requirements.md`)
- Roblox · doc officielle · A · export FBX depuis Blender.
- Enseignements : Path Mode **Copy** + **Embed Textures** ; **Apply Scalings = FBX Unit Scale** ; **Add Leaf Bones = off** ; **Bake Animation = off** sauf animation.
- Pertinent : preset d'export (`config/eclipse_default.json → export_preset`).

### S03 — Blender guide (`art/blender.md`)
- Roblox · doc officielle · A · configuration Blender ↔ Studio.
- Enseignements : Units → **Unit System None**, Rotation Degrees ; export Blender : **Forward = Z Forward, Up = Y Up**, Apply Scalings FBX Unit Scale ; import Studio : **World Forward = Front, World Up = Top, Scale Unit = Stud**, « Insert Using Scene Position » ; tableau des 3 méthodes d'échelle (FBX Unit Scale recommandée ; Scale 0.01 ; Unit Scale 0.01 déconseillé car pose problèmes aux modifiers) ; « glTF n'a pas besoin de ces réglages d'échelle ».
- Pertinent : base du standard d'export. Le document reconnaît lui-même que « tutoriels et ressources utilisent des échelles incohérentes → tester ».

### S04 — Importer (`studio/importer.md`)
- Roblox · doc officielle · A · options de l'importeur 3D.
- Enseignements : formats **.fbx, .gltf, .obj** ; options : Import Only As Model (on), Upload to Roblox (on), Add to Workspace, Insert Using Scene Position (off), **Set Pivot to Scene Origin (on)**, Anchored, Uses Cage, Rig Type, **World Forward / World Up**, **Scale Unit (Studs)**, **Merge Meshes (off)**, **Invert Negative Faces (off)**, par objet **Use Imported Pivot (on)**, **Make Double Sided (off, coûteux)**, Ignore Vertex Colors ; presets d'import sauvegardables.
- Pertinent : réglages d'import ECLIPSE ; « Upload to Roblox = off » pour itérer sans polluer l'inventaire.

### S05 — Meshes (`parts/meshes.md`)
- Roblox · A · MeshPart.
- Enseignements : objets suffixés **`_Att` → Attachment**, `_OuterCage`/`_InnerCage` → Wrap* ; **RenderFidelity Automatic : <250 studs = max, 250–500 = moyen, >500 = bas** ; CollisionFidelity (Box, Hull, Default, PreciseConvexDecomposition, Tunable) ; SurfaceAppearance prioritaire sur MaterialVariant pour les textures.
- Pertinent : pivots/charnières via `_Att`, collisions des armes (Box/Hull suffisent).

### S06 — Texture specifications (`art/modeling/texture-specifications.md`)
- Roblox · A · textures.
- Enseignements : upload jusqu'à **4096×4096** ; guides de taille (≈256 px par cube 2×2×2 studs ; 5×5 → 256, 10×10 → 512, 20×20 → 1024) ; **un seul matériau par mesh** ; normal map **OpenGL tangent space uniquement** ; roughness/metalness 8 bits ; **un seul UV set**, UV en **0–1**, **overlaps autorisés**.
- **Contradiction interne** : la même page dit ailleurs « maximum 1024×1024 » (onglet PBR / section UV). Explication la plus probable : texte antérieur au passage 4K (S15). Décision : voir CONTROVERSIES §C8.

### S07 — PBR textures / SurfaceAppearance (`art/modeling/surface-appearance.md`)
- Roblox · A · PBR.
- Enseignements : 5 maps (Color, Normal, Roughness, Metalness, Emissive mask) ; **metalness workflow**, valeurs 0 ou 1 « dans la plupart des cas » ; Fresnel : « si la surface paraît trop brillante sous certains angles, ajouter ~**+0.1 de roughness** » ; `SurfaceAppearance.Color` multiplie la ColorMap (tint gratuit) ; AlphaMode Overlay par défaut ; SurfaceAppearance non modifiable par script en jeu (pré-traitement).
- Pertinent : matériaux ECLIPSE, variantes de teinte sans nouvelle texture.

### S08 — Material reference (`art/modeling/material-reference.md`)
- Roblox · A (valeurs indicatives) · Enseignements : *Painted metal* R 0.3 / M 0.0 ; *Pure metals* R 0.2–0.3 / M 1 ; *Worn metals* R 0.2–0.4 / M 1 ; *Matte plastic* R 0.4 / M 0 ; *Glossy plastic* R 0.1.
- Pertinent : points de départ, **à ajuster** (la roughness 0.4 uniforme = look « plastique mat » à éviter pour ECLIPSE).

### S09 — Improve performance (`performance-optimization/improve.md`)
- Roblox · A · perf rendu.
- Enseignements : **instancing** : meshes de même `MeshContent` en un draw call si SurfaceAppearance identiques (sinon TextureContent identiques) ; draw calls > triangles en importance ; **mémoire texture = nombre de pixels** (1024² = 4× 512²) ; éviter les uploads dupliqués (l'importeur ne dé-duplique pas) ; teinter via `SurfaceAppearance.Color` plutôt que dupliquer une texture ; trim sheets ; RenderFidelity Precise coûteux.
- Pertinent : stratégie Worldmodel (N joueurs × WM identiques = instancing), budget MeshParts.

### S10 — Textures and decals → Texture streaming (`parts/textures-decals.md`)
- Roblox · A · streaming.
- Enseignements : streaming automatique pour MeshPart, SurfaceAppearance, Decal, Texture, MaterialVariant… ; qualité selon importance à l'écran ; **bonnes pratiques officielles : préférer des textures uniques plutôt que des atlas (sauf parts batchables) ; texel density quasi uniforme**.
- Pertinent : décision « un set de textures par arme (VM) / par WM » plutôt qu'un atlas multi-armes.

### S11 — Roblox units (`physics/units.md`) — A — **1 stud = 28 cm**.
### S12 — Camera API (`reference/engine/classes/Camera.yaml`) — A — `FieldOfView` **vertical**, défaut **70°**, borné 1–120.
### S13 — BasePart/MeshPart API (`BasePart.yaml`, `MeshPart.yaml`) — A — `PivotOffset` = décalage du pivot par rapport au `CFrame` ; `RenderFidelity` ; `DoubleSided`.
### S14 — Rigging and skinning (`art/modeling/rigging.md`) — A — R1/R15, Bones visibles, les bones n'affectent pas la collision.

### S15 — DevForum : « 4k Texture Rendering » (janv. 2026) et « Introducing Texture Streaming » (déploiement à partir du 23 mars 2026)
- Roblox (annonces staff) · SYNTHÈSE · A- · Le moteur n'utilise >1K que si l'objet le justifie (importance à l'écran) et si l'appareil a la mémoire.
- Pertinent : un VM en 2K est désormais légitime si la texel density le demande ; les appareils faibles redescendent automatiquement.

### S16 — DevForum : « [Full Release] Privacy for Newly-Created Image, Mesh, and Decal Assets »
- Roblox · SYNTHÈSE · A- · Assets image/mesh/decal **Restricted** par défaut pour les nouveaux comptes/groupes ; Open Use sinon.
- Pertinent : licences (un asset tiers uploadé en Open Use devient réutilisable par d'autres → risque de redistribution).

### S17 — DevForum : rapports de bugs communautaires
- « glTF importer invalid normals » (2023), « GLTF Importer unusable due to normal issue » (2024), « Custom mesh normals cause glowing/shining artifacts from certain angles » (2023), fils « white lines on mesh texture » (padding/merge).
- Communauté · SYNTHÈSE · C · Pertinent : choix **FBX** (normals préservées selon la communauté), vigilance sur les normals très déviées, diagnostic des lignes fines. Statut 2026 inconnu → à re-tester (calibration).

## 2. Blender — officiel

### S20 — API Python Blender 5.0.1 (introspection locale de `bpy`) — MESURÉ — A
- Propriétés et défauts exacts : FBX (`apply_scale_options` défaut `FBX_SCALE_NONE`, `axis_forward -Z`, `axis_up Y`, `mesh_smooth_type OFF`=« Normals Only », `use_triangles`, `bake_space_transform`…), Weighted Normal (`weight 50`, `mode FACE_AREA`, `keep_sharp`, `use_face_influence`), Bevel (`harden_normals`, `face_strength_mode`, `limit_method ANGLE` 30°…), Boolean (**solvers FLOAT / EXACT / MANIFOLD**), Triangulate (`keep_custom_normals`), Bake (**tangent +X +Y +Z = OpenGL**, margin 16 px, `ADJACENT_FACES`).
- Pertinent : toutes les valeurs de preset et du validator.

### S21 — Code source de l'exporteur FBX (`scripts/addons_core/io_scene_fbx`, Blender 5.0) — PLEIN TEXTE — A
- `units_blender_to_fbx_factor` : 100 si Unit System = None, sinon 100 × Unit Scale.
- `FBX_SCALE_NONE` (« All Local ») : l'échelle d'unité est appliquée aux **transforms d'objets** (Lcl Scaling ×100), UnitScaleFactor = 1.
- `FBX_SCALE_UNITS` (« FBX Units Scale ») : géométrie 1:1, **UnitScaleFactor = 100**.
- `bake_space_transform` (« Apply Transform ») : « EXPERIMENTAL… known to be broken with armatures/animations ».

### S22 — Blender 4.1 release notes, Modeling — SYNTHÈSE — A-
- **Auto Smooth supprimé** ; remplacé par le modificateur/asset **« Smooth by Angle »** ; la netteté est stockée dans les attributs `sharp_edge` / `sharp_face` ; les custom normals n'ont plus besoin d'Auto Smooth.
- Pertinent : ne JAMAIS appliquer un tutoriel pré-4.1 parlant d'« Auto Smooth » sans traduction.

### S23 — Blender 4.5 LTS release notes, Modeling — SYNTHÈSE — A-
- Nouveau solver booléen **Manifold** : aussi rapide ou plus que Float, fiable, **exige des opérandes manifold**.

### S24 — Manuel Blender 5.2 LTS (Weighted Normal, Bevel, Render Baking) — SYNTHÈSE — A-
- WN : pondération par aire/angle, Keep Sharp, Face Influence (forces Weak/Medium/Strong posées par Bevel « Face Strength »). Baking : Selected to Active, cage / extrusion / max ray distance, cage de même topologie.

### S25 — Issues Blender #132292 et #133978 — SYNTHÈSE — B
- « Harden Normals » du Bevel dégradé/cassé dans certains cas après la suppression d'Auto Smooth (signalé sur 4.4 alpha). Dans notre test 5.0.1 simple, il fonctionnait (S20).

### S26 — Blender 5.0 (18 nov. 2025) ; manuel courant = **5.2 LTS** (sept. 2026) — SYNTHÈSE — A-
- 5.0 : importeur FBX C++ par défaut. `Material.use_nodes` **déprécié** (retrait prévu en 6.0) — constaté en MESURÉ.

## 3. Pratique professionnelle (SYNTHÈSE sauf mention)

### S30 — Polycount Wiki « Face weighted normals » + fils Polycount « Weighted Normals (Mid Poly) Workflow »
- Communauté pro · B · FWVN : chanfreins + normals perpendiculaires aux grandes faces → le dégradé de shading est « poussé » dans les petits chanfreins.
- Pertinent : cœur du look ECLIPSE (surfaces planes, arêtes qui accrochent la lumière).

### S31 — Polycount Wiki « Normal Map Technical Details », « Texture Baking » + fils « synced tangent basis »
- B · Baker et moteur doivent partager la **même base tangente** (MikkTSpace le plus courant) ; **trianguler avant le bake** ; en workflow synchronisé, un seul smoothing group possible.
- Pertinent : risque ECLIPSE → la base tangente de Roblox n'est pas documentée publiquement (voir C5).

### S32 — Marmoset « The Toolbag Baking Tutorial » + docs cage / tips
- Éditeur pro · B · **Hard edge ⇒ split UV** (sinon couture) ; cage **moyennée (averaged)** recommandée (sinon trous aux hard edges) ; *skew* corrigeable (skew painting) ; hard edges aux coutures UV = bakes plus robustes aux mips/LOD.

### S33 — Marmoset « Physically-Based Rendering, And You Can Too! » (Joe Wilson)
- B · La **microsurface (roughness/gloss) porte l'essentiel de la variation de surface** ; roughness ≠ intensité spéculaire.

### S34 — Adobe Substance « PBR Guide » + nœuds « PBR BaseColor/Metallic Validate »
- Éditeur · B · Albedo diélectrique minimum **30–50 sRGB** (charbon ≈ 50), maximum ≈ 240 ; métaux 70–100 % de réflectance (**≈180–255 sRGB**, seuil tolérant 60 %) ; metallic binaire.

### S35 — Polycount : « Should gun coating be treated as metallic? », « Some artists using metallic values in painted metal for guns? », « Approach for PBR correctness of coated or treated metal surfaces »
- Communauté · B/C · **Désaccord** : bleuissage/parkerisation = oxydes (diélectriques) vs rendu « metal sombre » préféré par certains artistes. Voir C3.

### S36 — 80.lv, articles et digest « Texturing weapons » / « Weapon Art: Tips for Design, Texturing and Presentation » / « How to Create A Realistic Weapon »
- Artistes publiés · B · « Construire la roughness comme la couleur » ; usure de bord = **micro-dégâts**, pas une ligne propre ; traces de doigts/huile autour des pièces manipulées ; éviter l'uniformité ; ordre de travail Fill → Edges → Cavities/AO → Variation → Roughness.

### S37 — Mid-poly : Blacksteinn « MIDPOLY: the ultimate guide », Matthias Patscheider « The mid-poly workflow », 80.lv « Creating Assets Within the Mid Poly Workflow in UE5 »
- B · Chanfrein **1 segment** + Weighted Normals = méthode la plus répandue ; **2–3 segments** suffisent pour qu'une arête paraisse ronde ; flexibilité, itération rapide, pas de bake obligatoire.

### S38 — Polycount « Fighting normal map's resolution », « Bevelling, Smoothing & Edge Padding », wiki « Normal Map Modeling »
- B · **Exagérer les bevels** pour qu'ils survivent aux mips ; les micro-bevels réalistes aliasent ; « pensez à la taille à l'écran et à la résolution disponible ».

### S39 — Texel density : Polycount « Texel Density Standards for AAA First-Person Shooter Games? », Beyond Extent « Texel Density » (Timothy Dries), document de Leonardo Iezzi
- B · Références courantes : **10,24 px/cm** (héros / FPS proche), **5,12 px/cm** (arrière-plan / 3e personne). Converti : **≈ 287 px/stud** et **≈ 143 px/stud** (1 stud = 28 cm).

### S40 — Polycount : UV miroir et bake (« Normal mapping seam on mirrored UVs », « Overlapping/mirroring UVs and normal maps »)
- B · **Décaler de 1 tuile UV les coquilles miroir/superposées avant le bake** ; ne jamais supprimer la moitié avant le bake.

### S41 — Polycount « Why straight UVs with hardsurface », « UV Unwrapping Best Practice » + padding (« Mip mapping and the importance of pixel padding », Daz3D/forums)
- B · UV redressées = moins d'aliasing, meilleur packing ; **padding ≈ 12 px à 1K, moitié à 512** ; 8–16 px au bake courant.

### S42 — The Rookies « Ultimate Guide to Making Guns for FPS Games »
- B · Armes FPS **5k–40k tris** (souvent 4k–10k en vue FPS selon l'arme) ; densité UV plus forte là où la caméra s'approche (viseurs).

### S43 — GDC 2015, David Helsby (Bungie) « The Art of First Person Animation for Destiny » — voir fiche vidéo en fin de fichier.

### S44 — Bohemia Interactive, wiki Arma Reforger « Weapon Animation / Basic Tutorial », « Weapon Creation / Asset Preparation »
- Studio · B · Squelette d'arme : `w_root`, `w_trigger`, `w_bolt`, `w_charging_handle`… ; tout ce qui ne bouge pas est skinné au root ; nommage `_LODn`.
- Pertinent : convention de pièces mobiles et pivots (ECLIPSE utilise des MeshParts + Motor6D, même logique).

### S45 — Ergonomie : Kong & Lowe (2005) « Optimal cylindrical handle diameter for grip force tasks » ; Seo et al. « Optimum tool handle diameter for a cylinder grip » (J Hand Ther 2003) ; CCOHS « Hand Tool Ergonomics – Tool Design »
- Recherche publiée + organisme officiel · B · diamètres **30–40 mm** jugés les plus confortables, optimum ≈ **33 mm**, ≈ **19,7 % de la longueur de main** ; poignées cylindriques/ovales ; longueur de poignée ≥ largeur de main ; « **bend the tool, not the wrist** » (poignet neutre).

### S46 — Angles de poignée d'armes de poing (NRA American Rifleman / NRA Family, forums spécialisés)
- B · 1911 ≈ **18°**, Glock ≈ **22°** par rapport à la perpendiculaire à l'axe du canon ; hauteur d'axe du canon au-dessus de la main influence le relevé.

### S47 — Blender Bros « Hard Surface Game Asset Course 2.0 » (75 $) — B — booléens + n-gons + weighted normals, sans retopo ; export moteur.
### S48 — Viewmodel FOV (blog Sahil Dhanju, forums Unreal) — B — FOV séparée pour le viewmodel dans beaucoup de FPS ; les animateurs animent à une FOV fixe.

### S49 — Physically Based API (Anton Palmqvist) — PLEIN TEXTE (CC0) — A
- Couleurs mesurées (linéaire → sRGB 8 bits calculé) : fer **192,190,187** ; titane **177,170,162** ; inox **214,209,203** ; chrome **211,216,218** ; nickel **217,209,198** ; aluminium **245,246,246**.
- Pertinent : un métal nu n'est **jamais** sombre en albedo.

### S50 — MikkTSpace (Morten Mikkelsen, GitHub) + `intern/mikktspace` dans le code Blender — PLEIN TEXTE — A
- Base tangente standard ; Blender l'utilise pour le calcul des tangentes et le bake.

### S51 — MCP for Blender (anciennement `blender-mcp`, ahujasid) — PLEIN TEXTE — A
- Paquet `mcp-for-blender` ; outils `get_scene_info`, `get_object_info`, `get_viewport_screenshot`, `execute_blender_code`, `export_scene`, `bpy_api_lookup` ; **exécute du Python arbitraire → sauvegarder avant** ; `BLENDER_MCP_SAFE_MODE=1` pour filtrer.

### S53 — Roblox « Connect to the Roblox Studio MCP server » (`studio/mcp.md`) + README `Roblox/studio-rust-mcp-server` — PLEIN TEXTE — A
- Serveur MCP **intégré à Studio** (Assistant → Manage MCP Servers → Enable Studio as MCP server ; quick connect Claude Code). Outils : `execute_luau` (Edit/Client/Server), `inspect_instance`, `search_game_tree`, `script_read/multi_edit/script_search/script_grep`, `screen_capture` (position/cible de caméra optionnelles), `start_stop_play`, `get_studio_state`, `get_console_output`, `insert_asset` (par ID), `search_asset`, `upload_image` (**uploade**), `generate_mesh`/`generate_material` (IA), entrées clavier/souris simulées, `list_roblox_studios` (chaque appel prend un `studio_id`).
- Le serveur Rust séparé est **déprécié** au profit de l'intégré.
- Pertinent : inspection et captures automatisées côté Studio ; **pas d'outil d'import FBX local** → l'import reste une action utilisateur (Importer). `upload_image` et `generate_*` hors périmètre sans accord explicite.

### S52 — Construction de canons (Wikipedia « Built-up gun », pages techniques navales)
- C (référence technique générale) · Tubes frettés en couches (A-tube, jaquette, frettes), **conicité vers la bouche (« chase »)**, évasement en cloche à la bouche.
- Pertinent : vocabulaire crédible pour stratifier le canon d'ECLIPSE-1 sans copier une arme.

## 4. Licences et ressources

### S60 — Poly Haven, licence (CC0) — A · S61 — ambientCG, licence (CC0) — A
### S62 — Superhive (ex-Blender Market) : « Royalty Free License », « Understanding Product License Types », GPL — A-
- Royalty Free : usage perso/commercial, **pas de revente/redistribution** ; code = GPL/MIT obligatoire ; produits mixtes = plusieurs licences.
### S63 — Sketchfab « Licenses » — A- — CC BY (commercial OK avec crédit), **CC BY-NC (pas commercial)**, CC BY-SA (partage à l'identique), Standard (commercial, pas de redistribution standalone), **Editorial (interdit en jeu)**.
### S64 — Fab (Epic) « Fab Standard License » / docs « Licenses and Pricing » — B (texte intégral non lu)
- Utilisable avec tout outil/moteur (pas limité à Unreal), commercial ; **relire l'EULA** pour la clause de redistribution avant usage Roblox.
### S65 — Roblox Terms of Use / Creator terms — B
- Le créateur accorde à Roblox une licence mondiale, perpétuelle, sous-licenciable sur son UGC ; il doit détenir tous les droits.

### S70–S76 — Add-ons et logiciels (pages produit, SYNTHÈSE) — B
- S70 MACHIN3 : MESHmachine 0.20 (Blender 4.2 → 5.0), MACHIN3tools Prime 5 $ / DeusEx 15 $ ; DECALmachine. · S71 Hard Ops / BoxCutter (Superhive, maintenu, v26.x en 2026). · S72 UVPackmaster 3 (39–44 $ solo, Blender 5 supporté). · S73 Zen UV 5 (39 $). · S74 TexTools (gratuit, GPL, GitHub franMarz). · S75 BoltFactory (gratuit, plateforme Extensions). · S76 Substance 3D Painter 2026 (Steam, 199,99 $ perpétuel), InstaMAT (gratuit < 100 k$/an avec crédit), ArmorPaint (≈16–20 $ binaires, open source).

## 5. Expériences MESURÉES dans cette session (bpy 5.0.1, scènes synthétiques)

| ID | Expérience | Résultat |
|---|---|---|
| V1 | Coût des segments de bevel (Bevel mod, angle 30°) | Boîte : 12 → 44 → 108 → 188 → 300 tris (0→4 segments). Cylindre 32 côtés : 124 → 252 → 380 → 508 → 636. |
| V2 | Weighted Normal sur boîte 1×0,5×0,25 chanfreinée (1 seg) | Déviation max des normals des grandes faces : lissé sans WN 28,9° ; WN weight 50 **5,38°** ; weight 75 0,48° ; **weight 100 0,00°**. |
| V3 | Trianguler après WN | Sans `keep_custom_normals` : 0,27° d'erreur ; avec : 0°. Trianguler **avant** WN : 0°. |
| V4 | Données brutes FBX (boîte 1×0,5×0,25) | `FBX_SCALE_NONE` : géométrie 1:1 mais **Lcl Scaling = 100** sur l'objet ; `FBX_SCALE_UNITS` : pas d'échelle, **UnitScaleFactor = 100**. Sans « Apply Transform » : rotation d'objet −90° X (preset −Z) ou (90°,0,180°) (preset Z) ; avec : géométrie convertie, aucune rotation. |
| V5 | Aller-retour FBX des weighted normals | « Normals Only » : **identiques** ; `use_triangles=True` : 0,27° d'écart ; Triangulate(`keep_custom_normals`) puis export : identiques. |
| V6 | Table de vérité des axes (`axis_conversion`) | Preset Roblox (Forward Z, Up Y) : Blender −Y → fichier −Z ; −X → +X ; +Z → +Y. Preset par défaut (−Z, Y) : +Y → −Z ; +X → +X. |
| V7 | Réglages de bake par défaut | Tangent space, swizzle **+X +Y +Z (OpenGL)**, marge 16 px, `ADJACENT_FACES`. |
| V8 | Harden Normals (Bevel seul, cas simple) | Grandes faces planes (0°) en 5.0.1 — les régressions S25 sont situationnelles. |
| V9 | Bevel `limit_method=WEIGHT` + attribut d'arête nommé (`edge_weight="bevel_class"`) | Poids 1 / 0,5 / 0,25 → offsets **0,100 / 0,050 / 0,025** : la largeur est multipliée par le poids (un seul modificateur encode B1/B2/B3). |

---

## Fiche vidéo (format demandé) — S43, GDC 2015 « The Art of First Person Animation for Destiny »

> Réserve : vidéo non visionnée (GDC Vault/YouTube bloqués) ; contenu reconstitué depuis des résumés publiés (GDC Vault, Game Anim, CG Cookie). Pas de timestamps disponibles.

| Élément | Contenu |
|---|---|
| SOURCE | David Helsby, Senior Animator, Bungie — GDC 2015. |
| TECHNIQUE 1 | **« Combat corridor »** : garder dégagée la bande centrale de l'écran (visée, cible). |
| POURQUOI | Le joueur y concentre son attention ; une arme ou un bras qui y entre masque l'information de jeu. |
| QUAND | Poses idle/ADS/rechargement/inspection ; conception de la silhouette VM (hauteur du canon, viseurs). |
| QUAND PAS | Inspection *explicitement* déclenchée par le joueur (l'arme peut alors traverser le centre). |
| RISQUES | Arme trop basse = faible lisibilité ; trop haute = masque la cible. |
| APPLICATION ECLIPSE | Vérifier en QA visuelle que le haut de l'arme (trappe, viseur) n'envahit pas le corridor en idle/ADS. |
| VALIDATION | Capture VM à FOV 70, grille au tiers central, checklist VISUAL_QA §Lisibilité. |
| TECHNIQUE 2 | **Arme parentée à la main** (plutôt que main parentée à l'arme) pour séparer les actions « personnage » et « arme ». |
| POURQUOI | Le mouvement de la main entraîne l'arme ; les mouvements propres de l'arme (trappe, cartouche) restent dans leur propre action. |
| APPLICATION ECLIPSE | Relation GRIP → PALM → WRIST : le repère `Grip_Att` du modèle doit coïncider avec l'attache de la main (voir GRIP standard) — directement lié au bug « bras hors de la poignée en inspection ». |
| VALIDATION | `GRP001` + test en Studio : inspection complète sans dérive main/poignée > 1 px à 1080p. |
| TECHNIQUE 3 | Mouvements de caméra très atténués (pas de balancement réaliste de la tête). |
| APPLICATION ECLIPSE | Hors périmètre modélisation ; noté pour la future section Animation. |
