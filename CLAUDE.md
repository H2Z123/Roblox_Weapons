# ECLIPSE — Studio de développement d'armes (Roblox)

Travail Blender / 3D / export Roblox : lire d'abord `Standards/BLENDER_LOCAL_AGENT_HANDOFF.md`, puis `Standards/BLENDER_PRODUCTION_STANDARD.md`. Carte du contexte : `Knowledge/KNOWLEDGE_INDEX.md`.

Règles permanentes :
- Ne jamais modifier une version SOURCE `.blend` existante : sauvegarder une nouvelle version avant toute modification ; exporter uniquement via `Tools/BlenderValidation/tools/eclipse_export.py`.
- Ne jamais toucher la version Roblox active ; aucune publication, aucun upload, aucun achat sans accord explicite de l'utilisateur.
- Ne pas renommer les parts/rigs Roblox existants (`MainBody`, `TopHatch`, `Cartridge`, `ECLIPSE1_*_Rig_v01`) : utiliser la propriété `roblox_name`.
- ECLIPSE-1 s'améliore, il ne se redessine pas ; toute modification de silhouette demande l'accord de l'utilisateur sur captures BEFORE/AFTER.
- Le validator (`Tools/BlenderValidation/`) détecte ; les corrections sont proposées puis validées.
- Tests du validator : `python -m pytest Tools/BlenderValidation/tests -q` (bpy requis pour les tests d'intégration).
