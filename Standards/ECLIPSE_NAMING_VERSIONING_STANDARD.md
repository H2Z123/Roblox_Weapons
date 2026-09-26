# ECLIPSE — Nommage, versioning, rollback

Principe : **respecter d'abord l'existant**. Le dépôt ne contenait aucune convention Blender au moment de cette recherche ; les seules conventions connues sont celles du brief : parts Roblox `MainBody`, `TopHatch`, `Cartridge` ; rigs `ECLIPSE1_Viewmodel_Rig_v01`, `ECLIPSE1_Worldmodel_Rig_v01`. **Aucun renommage de masse.** Tags : voir `BLENDER_PRODUCTION_STANDARD.md`.

## 1. Deux espaces de noms

| Espace | Qui le lit | Règle |
|---|---|---|
| **Noms Roblox** (MeshParts, Attachments, Models) | Motor6D, animations, scripts — **par nom** | Stables. Les noms existants sont des contrats. |
| **Noms Blender** (objets, collections, matériaux, fichiers) | Humains, validator, outils | Uniques dans le fichier (Blender l'impose), préfixés par asset et par modèle |

Le pont entre les deux = la propriété personnalisée **`roblox_name`** sur chaque objet exporté ; `tools/eclipse_export.py` renomme dans la copie d'export. (`EXP005` unicité/validité, `EXP009` présence.)

<a id="objets"></a>
## 2. Objets et collections Blender

| Élément | Convention | Exemple |
|---|---|---|
| Collection modèle | `<ASSET>_VM`, `<ASSET>_WM` | `ECLIPSE1_VM` |
| Sous-collections exclues | `_Cutters`, `_Proxies` (exclue de l'export seulement), `_WIP`, `_REF` | `ECLIPSE1_VM_Cutters` |
| Pièce | `<ASSET>_<VM/WM>_<Part>` + `roblox_name = <Part>` | `ECLIPSE1_VM_TopHatch` → `TopHatch` |
| Repère | `<ASSET>_<VM/WM>_<Nom>_Att` + `roblox_name = <Nom>_Att` | `ECLIPSE1_WM_Grip_Att` → `Grip_Att` |
| Coupeur | `<ASSET>_<VM/WM>_Cutter_<Rôle>` | `ECLIPSE1_VM_Cutter_HatchSlot` |
| Proxy | `<ASSET>_Proxy_<Nom>` | `ECLIPSE1_Proxy_RightHand_Grip` |

- Noms Roblox valides : `^[A-Za-z][A-Za-z0-9_]*$` ; jamais de suffixe Blender `.001` (`NAM001`).
- Le validator accepte aussi les noms historiques (liste `naming.legacy_names`) pour ne pas forcer de renommage.

<a id="materiaux"></a>
## 3. Matériaux

`M_<ASSET>_<Surface>` : `M_ECLIPSE1_Coating`, `M_ECLIPSE1_Polymer`, `M_ECLIPSE1_MachinedSteel`, `M_ECLIPSE1_Cartridge`, `M_ECLIPSE1_Emissive` (`NAM002`).

<a id="textures"></a>
## 4. Textures

`T_<ASSET>_<VM/WM>[_<Part>]_<Map>` avec `<Map>` ∈ BaseColor, Normal, Roughness, Metalness, Emissive (AO seulement comme source) : `T_ECLIPSE1_VM_BaseColor.png`, `T_ECLIPSE1_WM_Normal.png` (`NAM003`).

## 5. Versioning

| Niveau | Fichier / objet | Règle |
|---|---|---|
| **Source** | `Source/ECLIPSE1/ECLIPSE1_SRC_vNNN.blend` (VM + WM dans le même fichier) | toute modification = nouvelle version ; jamais d'écrasement d'une version déjà exportée |
| Nature du changement | `Source/ECLIPSE1/CHANGELOG.md` : une ligne par version, type ∈ `MODEL`, `MECHFIX`, `RIGPREP`, `GAMEREADY`, `EXPORTFIX` + résumé + rapport validator + dossier de captures | la nature est une étiquette, pas un nouveau schéma de nom |
| **Export** | `Export/ECLIPSE1/ECLIPSE1_VM_vNNN.fbx` (+ `_EXPORT_vNNN.blend`, `_manifest.json`, `_validation.md`) | **même NNN que la source** d'origine → traçabilité 1:1 ; immuable (l'outil refuse d'écraser) |
| **Rig Roblox** | `ECLIPSE1_Viewmodel_Rig_vNN`, `ECLIPSE1_Worldmodel_Rig_vNN` (existant) | +1 à chaque remplacement de géométrie ; noter « Rig_v02 ← SRC_v014 » dans le CHANGELOG et le manifeste |
| Rapports | `Reports/validation/<ASSET>_vNNN_<profil>_<BEFORE/AFTER>/` | JSON + MD du validator |
| Captures | `Reports/screenshots/<ASSET>_vNNN/<vue>_<BEFORE/AFTER>.png` | vues : `VM_idle`, `VM_ADS`, `VM_inspect_1..3`, `WM_12`, `WM_25`, `silhouette_VM`, `silhouette_WM64` |

## 6. Rollback

- Blender : rouvrir `ECLIPSE1_SRC_v(NNN−1).blend` — rien n'est jamais supprimé.
- Export : les versions précédentes restent (immuables, hash dans le manifeste).
- Roblox : l'ancien rig (`…_Rig_v01`) reste intact à côté du nouveau dans le Studio d'armes ; basculer la référence ; ne jamais modifier la version Roblox active pendant une mission de modélisation.
- Git : versionner les **manifestes, rapports et standards** ; pour les binaires (`.blend`, `.fbx`, `.png`) utiliser **Git LFS** ou un stockage externe référencé par hash dans les manifestes (le dépôt n'a pas encore de politique LFS — décision utilisateur). Ignorer `*.blend1`.
