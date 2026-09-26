# ECLIPSE — Index de connaissances (charger seulement le nécessaire)

Point d'entrée d'un agent : `Standards/BLENDER_LOCAL_AGENT_HANDOFF.md`. Ce fichier sert de carte pour ne charger que le contexte utile.

Légende des tags (tous les documents) : `[OFFICIEL]` doc Roblox/Blender · `[VÉRIFIÉ]` mesuré en bpy 5.0.1 · `[PRO]` pratique professionnelle · `[ECLIPSE]` décision projet · `[EXPÉRIMENTAL]` à valider localement.

## BLENDER (rempli — 2026-09-26)

| Besoin | Document | Taille / quand le charger |
|---|---|---|
| Démarrer | `Standards/BLENDER_LOCAL_AGENT_HANDOFF.md` | toujours en premier |
| Référence principale | `Standards/BLENDER_PRODUCTION_STANDARD.md` | toujours (court) |
| Procédure pas à pas | `Standards/ECLIPSE_WEAPON_MODELING_WORKFLOW.md` | toute mission de modélisation |
| Hard-surface / design | `Standards/ECLIPSE_HARDSURFACE_STANDARD.md` | forme, détails, fixations, kitbash |
| Anti « plastique fondu » | `Standards/ECLIPSE_ANTI_MELTED_PLASTIC.md` | revue de qualité de surface |
| Bevels | `Standards/ECLIPSE_BEVEL_STANDARD.md` | chanfreins, segments, largeurs |
| Shading / normals / fines lignes | `Standards/ECLIPSE_SHADING_STANDARD.md` | normals, artefacts |
| Topologie / booléens / cylindres | `Standards/ECLIPSE_TOPOLOGY_STANDARD.md` | géométrie |
| Viewmodel vs Worldmodel, budgets | `Standards/ECLIPSE_VIEWMODEL_WORLDMODEL_STANDARD.md` | optimisation, multi-MeshPart |
| UV, texel density, PBR, roughness, textures, bake | `Standards/ECLIPSE_MATERIALS_UV_BAKING_STANDARD.md` | texturing |
| Pivots, repères, mécanismes | `Standards/ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md` | trappe, cartouche, rig |
| Poignée / ergonomie / bras | `Standards/ECLIPSE_GRIP_MODELING_STANDARD.md` | poignée, bug d'inspection |
| Export Roblox | `Standards/ECLIPSE_BLENDER_ROBLOX_EXPORT.md` | échelle, axes, transforms, import |
| Nommage / versions / rollback | `Standards/ECLIPSE_NAMING_VERSIONING_STANDARD.md` | fichiers, noms Roblox |
| QA visuelle / mécanique / perf | `Standards/ECLIPSE_VISUAL_QA_CHECKLIST.md`, `ECLIPSE_MECHANICAL_QA.md`, `ECLIPSE_PERFORMANCE_QA.md` | avant livraison |
| Faits Roblox + faits Blender mesurés | `Knowledge/Blender/ROBLOX_PLATFORM_FACTS.md` | chiffres officiels |
| Désaccords et décisions | `Knowledge/Blender/CONTROVERSIES_AND_DECISIONS.md` | justifier/contester une règle |
| Sources | `Knowledge/Blender/SOURCE_INDEX.md` | traçabilité (long) |
| Canon d'ECLIPSE-1 | `Knowledge/Blender/ECLIPSE1_BARREL_DESIGN_NOTES.md` | travail sur le canon |
| Licences | `Knowledge/Blender/ASSET_LICENSE_GUIDE.md` | tout asset externe |
| Calibration Blender→Roblox | `Knowledge/Blender/CALIBRATION_LOG.md` | à compléter localement |
| Ressources / add-ons | `PREMIUM_BLENDER_ASSET_SHORTLIST.md` | décisions d'achat (humaines) |
| Validator et outils | `Tools/BlenderValidation/README.md` | exécuter/étendre les contrôles |

## ANIMATION — à venir

À créer : standards d'animation FPS (idle, ADS, tir, recul, rechargement, inspection), rig bras ↔ arme, résolution du bug « main hors de la poignée ». Points d'appui déjà présents : `ECLIPSE_GRIP_MODELING_STANDARD.md` §4, `ECLIPSE_PIVOTS_MECHANISMS_STANDARD.md` §6, fiche vidéo GDC Destiny dans `SOURCE_INDEX.md`.

## AUDIO — existant (hors de ce dépôt)

Connaissances audio existantes côté projet ECLIPSE, non présentes dans ce dépôt au 2026-09-26 : y ajouter un lien ou les migrer ici (`Knowledge/Audio/`).

## VFX — à venir

À créer : effets de tir, bouche (`Muzzle_Att`), éjection (`Eject_Att`), traces ; contraintes Roblox (ParticleEmitter, overdraw de transparence — S09).

## ROBLOX (général)

Faits de plateforme utiles à la modélisation : `Knowledge/Blender/ROBLOX_PLATFORM_FACTS.md`. Les futurs standards de scripts/rigs Roblox iront dans `Knowledge/Roblox/`.
