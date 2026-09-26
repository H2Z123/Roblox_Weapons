# Guide de sourcing et de licences des assets 3D (ECLIPSE)

Ce guide n'est pas un avis juridique : il fixe une **procédure prudente** pour une petite équipe. En cas de doute → `LICENSE_UNKNOWN` et on n'utilise pas. Sources : S60–S65 (`SOURCE_INDEX.md`).

## 1. Statuts

| Statut | Définition | Usage autorisé |
|---|---|---|
| `LICENSE_OK` | Licence lue et archivée, compatible usage commercial dans un jeu Roblox, conditions (crédit…) connues | production |
| `LICENSE_UNKNOWN` | Licence absente, ambiguë ou non archivée | **aucun** (ni prototype publié) |
| `REFERENCE_ONLY` | Utilisable comme référence visuelle (proportions, mécanique), jamais importé dans un fichier de production | moodboard, observation |
| `REJECTED` | Interdit (NC, Editorial, ripped, licence violée, pièce reconnaissable) | aucun |
| `PAID_CANDIDATE` | Payant, licence compatible *a priori*, non acheté | décision utilisateur ; rien n'est acheté par un agent |

## 2. Licences courantes

| Licence / source | Statut par défaut | Conditions clés |
|---|---|---|
| **CC0** (Poly Haven S60, ambientCG S61, Physically Based S49) | `LICENSE_OK` | aucune ; conserver l'URL |
| **CC BY** | `LICENSE_OK` si crédit possible | crédit obligatoire (écran crédits / description) ; texte exact archivé |
| **CC BY-SA** | `REFERENCE_ONLY` | le partage à l'identique est inadapté à un asset de jeu fermé |
| **CC BY-NC / NC-SA / NC-ND** | `REJECTED` | usage commercial interdit (un jeu Roblox monétisable l'est) |
| **CC BY-ND** | `REJECTED` | pas de modification |
| Sketchfab **Standard** (achat) | `PAID_CANDIDATE` → `LICENSE_OK` | commercial, pas de redistribution « standalone » (S63) |
| Sketchfab **Editorial** | `REJECTED` | interdit dans un jeu (S63) |
| Superhive **Royalty Free** | `PAID_CANDIDATE` → `LICENSE_OK` | commercial ; pas de revente/redistribution (S62) |
| Fab **Standard License** | `PAID_CANDIDATE` / `LICENSE_UNKNOWN` tant que l'EULA n'est pas relue pour Roblox | utilisable avec tout moteur (S64) ; **vérifier** la clause de distribution d'assets extractibles |
| Gumroad / ArtStation (licence du vendeur) | `LICENSE_UNKNOWN` jusqu'à lecture | chaque vendeur a sa licence |
| Add-ons Blender (GPL/MIT) | outils : OK | la GPL couvre le **code**, pas les modèles produits avec (S62) |
| Roblox Creator Store (modèles d'autres créateurs) | `REFERENCE_ONLY` | pas d'extraction vers Blender pour réutilisation ; qualité/propriété incertaines |
| Assets extraits (« ripped ») d'autres jeux | `REJECTED` | contrefaçon |
| Génération IA (via Blender MCP : Hyper3D, Hunyuan3D…) | `REFERENCE_ONLY` | conditions variables selon le service ; identité ECLIPSE non garantie |
| Poly Pizza (via Blender MCP) | CC0 → OK ; CC BY → OK avec crédit | ~69 % du catalogue est CC BY (S51) |

## 3. Spécificités Roblox

- Uploader = accorder à Roblox une licence large et sous-licenciable sur l'UGC ; il faut **détenir tous les droits** (S65).
- Activer l'**Asset Privacy = Restricted** pour les meshes/images (défaut pour les nouveaux comptes, S16) : un asset tiers uploadé en *Open Use* devient réutilisable par d'autres créateurs, ce qui peut constituer une **redistribution** interdite par les licences Royalty Free/Standard.
- Ne jamais uploader un pack tiers « tel quel » (textures brutes, kit complet) : seulement l'asset final intégré.

## 4. Règles ECLIPSE de réutilisation

1. **Petites pièces génériques** (vis, écrous, inserts, ressorts, textures de base) : autorisées si `LICENSE_OK` (HARDSURFACE §6).
2. **Pièces reconnaissables ou de grande taille** issues d'un asset tiers (carcasse, canon, viseur distinctif) : `REJECTED` même si la licence le permet → identité ECLIPSE.
3. Textures CC0 : utilisables comme **sources** (masques, micro-détails) retravaillées, pas comme apparence finale reconnaissable.
4. Aucun achat par un agent ; les `PAID_CANDIDATE` sont listés dans `PREMIUM_BLENDER_ASSET_SHORTLIST.md` pour décision humaine.

## 5. Registre (à tenir à chaque import d'asset externe)

Créer/compléter `Knowledge/Blender/ASSET_REGISTRY.md` :

| Asset | Source (URL) | Auteur | Licence (+ version) | Preuve archivée (capture/PDF, date) | Statut | Utilisé dans | Modifications | Crédit à afficher |
|---|---|---|---|---|---|---|---|---|
| *ex. vis M3 générique* | *URL* | *auteur* | *CC0* | *Reports/licenses/…png, 2026-10-02* | `LICENSE_OK` | `ECLIPSE1_SRC_v015` | *têtes redimensionnées* | — |

Le validator ne contrôle pas les licences : c'est une étape humaine de la checklist de livraison.
