# Shortlist ressources Blender pour ECLIPSE (add-ons, kits, PBR, outils, formation)

**Rien n'a été acheté ni téléchargé.** Prix relevés le 2026-09-26 via pages produit/résumés de recherche (SOURCE_INDEX S70–S76) ; « non vérifié » = prix non confirmé dans cette session. Statuts de licence : `Knowledge/Blender/ASSET_LICENSE_GUIDE.md`. Règle : le pipeline ECLIPSE **ne doit dépendre d'aucun add-on propriétaire** — validator et export sont en bpy natif ; les add-ons ne sont que des accélérateurs.

## 1. Add-ons (analyse demandée : utilité réelle, maintenance, lock-in, alternative bpy)

| Nom | Créateur | URL | Prix | Licence | Maintenu (2026) | Gain réel ECLIPSE | Lock-in | Natif suffisant ? | Priorité |
|---|---|---|---|---|---|---|---|---|---|
| **MCP for Blender** (ex-blender-mcp) | ahujasid | https://github.com/ahujasid/blender-mcp | gratuit | MIT | oui (paquet `mcp-for-blender`) | **indispensable** : pilotage Blender par Claude local (scène, captures, exécution Python) | faible (le code exécuté est du bpy standard) | — | **HIGH** |
| **TexTools** | franMarz (communauté) | https://github.com/franMarz/TexTools-Blender | gratuit | GPL | oui | texel density, alignement/redressement d'îlots, bake helpers | nul | partiellement (le validator mesure la densité) | **HIGH** |
| **MESHmachine** | MACHIN3 | https://machin3.gumroad.com/l/MESHmachine | non vérifié | commerciale (code GPL) | oui (0.20 : Blender 4.2–5.0) | **Unchamfer/Unfuse** : modifier des bevels **déjà appliqués** sur ECLIPSE-1 sans remodéliser ; transferts de normals | faible (résultat = mesh standard) | non pour l'édition de bevels appliqués | **HIGH si** ECLIPSE-1 a des bevels appliqués, sinon MEDIUM |
| MACHIN3tools | MACHIN3 | https://machin3.gumroad.com/l/MACHIN3tools | Prime 5 $ / DeusEx 15 $ | commerciale | oui | confort (pie menus, alignements, clean-up) | nul | oui | MEDIUM |
| Hard Ops / BoxCutter | masterxeon1001 & co | https://superhivemarket.com/products/hard-ops--boxcutter-ultimate-bundle | non vérifié | commerciale | oui (v26.x en 2026) | vitesse de blockout booléen | moyen (habitudes de travail ; les modificateurs restent natifs) | oui (Boolean/Bevel/WN natifs) | MEDIUM |
| UVPackmaster 3 | glukoz | https://superhivemarket.com/products/uvpackmaster | 39–44 $ (solo) | commerciale | oui (Blender 5) | packing plus dense → moins de texels perdus | nul | pack natif correct mais moins efficace | MEDIUM |
| Zen UV 5 | Zen Masters | https://superhivemarket.com/products/zen-uv | 39 $ | commerciale | oui | UV complet (densité, trim, checker) | faible | redondant avec TexTools + UVPackmaster | LOW |
| DECALmachine | MACHIN3 | https://machin3.gumroad.com/ | non vérifié | commerciale | oui | décals/trims ; pour Roblox, tout doit finir baké dans un set unique | moyen | — | LOW |
| BoltFactory | Blender (Extensions) | https://extensions.blender.org/add-ons/boltfactory/ | gratuit | GPL | oui | génération de vis/écrous (à décimer) | nul | — | MEDIUM |
| Bool Tool | Blender (Extensions) | extensions.blender.org | gratuit | GPL | oui | raccourcis booléens | nul | oui | LOW |

Verdict : installer **MCP for Blender** et **TexTools** ; **MESHmachine** seulement après l'audit (si bevels appliqués) ; le reste à la demande.

## 2. Kits de fixations / hard-surface (petites pièces génériques uniquement)

| Nom | Créateur | URL | Prix | Licence | Utilité | Priorité |
|---|---|---|---|---|---|---|
| Hard Surface Kitbash Bundle (168+ assets dont 80+ vis/écrous/brides) | VictorVDR9 | https://victorvdr9.gumroad.com/l/kYXvZ | non vérifié | vendeur (à lire) → `PAID_CANDIDATE` | bibliothèque de fixations cohérente | MEDIUM |
| Hard Surface Kitbash vol.1 | Ian Taylor (Frosted Ice) | https://superhivemarket.com/products/hardsurfacekitbashvol1 | 5 $ | Royalty Free (Superhive) | boulons, écrous, radiaux | MEDIUM |
| Hard Surface Kitbash vol.2 (120 objets) | Ian Taylor | https://frostedice.gumroad.com | 5 $ | vendeur (à lire) | idem | LOW |
| Screws and Bolts Pack (43) | Pitiwazou | https://pitiwazou.gumroad.com/l/CvKaa | non vérifié | vendeur (à lire) | vis simples | LOW |

Toujours : ré-optimiser (côtés, bevels) selon TOPOLOGY §5 et HARDSURFACE §6 ; jamais de grosse pièce reconnaissable.

## 3. PBR, matériaux, références de valeurs

| Nom | URL | Prix | Licence | Utilité | Priorité |
|---|---|---|---|---|---|
| Physically Based (base de valeurs mesurées) | https://physicallybased.info | gratuit | CC0 | valeurs de métaux (fer, titane, inox…) | **HIGH** |
| Poly Haven | https://polyhaven.com | gratuit | CC0 | textures/masques de base (rayures, grain) à retravailler | **HIGH** |
| ambientCG | https://ambientcg.com | gratuit | CC0 | idem, 2000+ matériaux | HIGH |
| Fab (Megascans, etc.) | https://www.fab.com | variable (partie gratuite) | Fab Standard License | vaste bibliothèque ; **EULA à relire pour Roblox** | MEDIUM (`LICENSE_UNKNOWN` jusque-là) |

## 4. Logiciels de texturing / baking (décision utilisateur)

| Nom | URL | Prix | Licence | Intérêt ECLIPSE | Priorité |
|---|---|---|---|---|---|
| Substance 3D Painter 2026 | https://store.steampowered.com/app/4329260/Substance_3D_Painter_2026/ | 199,99 $ (Steam, perpétuel) | commerciale, sans plafond de revenus (Steam) | standard de l'industrie, smart masks d'usure, export par map | HIGH (si budget) |
| InstaMAT | https://instamaterial.com | gratuit < 100 k$/an (crédit requis) | licence « Pioneer » | alternative la plus complète à Painter | HIGH (option gratuite) |
| ArmorPaint | https://armorpaint.org | ≈ 16–20 $ (binaires) | open source | peinture PBR légère | LOW |
| Marmoset Toolbag | https://marmoset.co/toolbag/ | non vérifié | commerciale | meilleur baker (skew painting), rendus de présentation | MEDIUM |
| Blender (Cycles bake + Texture Paint) | — | gratuit | GPL | suffisant pour le bake VM→WM et des masques simples | déjà disponible |

## 5. Formation (sélection courte et pertinente)

| Ressource | Auteur | URL | Prix | Pourquoi | Priorité |
|---|---|---|---|---|---|
| Hard Surface Game Asset Course 2.0 | The Blender Bros | https://www.blenderbros.com/gameasset | 75 $ | booléens + n-gons + weighted normals en Blender, export moteur (workflow ECLIPSE) | MEDIUM |
| MIDPOLY: the ultimate guide | Blacksteinn | https://blacksteinn.artstation.com/blog/7o3WB/midpoly-the-ultimate-guide-with-all-working-nuances | gratuit | mid-poly en détail | **HIGH** |
| The Toolbag Baking Tutorial | Marmoset | https://marmoset.co/posts/toolbag-baking-tutorial/ | gratuit | bake : hard edges, cages, skew | HIGH |
| Polycount Wiki (Face weighted normals, Normal Map Technical Details, Texture Baking) | communauté | http://wiki.polycount.com/wiki/Face_weighted_normals | gratuit | fondamentaux normals/bake | HIGH |
| Texel Density deep dive | Beyond Extent (T. Dries) | https://www.beyondextent.com/deep-dives/deepdive-texeldensity | gratuit | densité de texels | MEDIUM |
| The PBR Guide | Adobe (Substance) | site Adobe Substance « The PBR Guide » (URL à confirmer localement) | gratuit | règles PBR (plages d'albedo, metalness) | HIGH |
| Modeling Weapons for a First Person Shooter | CG Cookie | https://www.cgcookie.com/courses/modeling-weapons-for-a-first-person-shooter | abonnement | modélisation d'armes FPS en Blender | LOW |
| The Art of First Person Animation for Destiny (GDC 2015) | David Helsby, Bungie | https://www.gdcvault.com/play/1022297/The-Art-of-First-Person | gratuit/vault | lisibilité FPS, arme parentée à la main | MEDIUM (mission Animation) |
| Roblox Creator Docs (modeling, PBR, importer, performance) | Roblox | https://github.com/Roblox/creator-docs | gratuit | vérité officielle Roblox | **HIGH** |
