# ECLIPSE — QA visuelle (ce que l'automatique ne voit pas)

À remplir sur **captures** (mêmes cadrages BEFORE/AFTER, NAMING §5) : Blender (viewport Material/Rendered) **puis** Roblox Studio (au moins deux orientations de soleil). Chaque ligne : ✅ / ❌ + commentaire. Une ligne ❌ bloque la livraison sauf dérogation écrite de l'utilisateur.

## Silhouette et proportions
- [ ] Silhouette noire reconnaissable en VM (FOV 70) et en vignette WM 64 px.
- [ ] Lecture « compacte mais lourde » ; masse autour de l'axe du canon.
- [ ] Distincte de toute arme réelle identifiable.
- [ ] Proportions PRIMARY cohérentes (canon / carcasse / poignée / trappe) ; identité ECLIPSE-1 conservée.

## Lisibilité première personne
- [ ] Corridor central de l'écran dégagé en idle et ADS (S43).
- [ ] Mécanisme signature (trappe/chambre) lisible depuis la vue VM.
- [ ] Aucun élément ne masque la visée ; ligne de mire claire en ADS (pas d'obstruction du viseur).
- [ ] Lecture correcte à 1080p **et** 1440p.

## Qualité de surface (anti « plastique fondu »)
- [ ] Checklist de `ECLIPSE_ANTI_MELTED_PLASTIC.md` §3 intégralement cochée.
- [ ] Hiérarchie de surface : zones de repos + grappes de détails autour des points fonctionnels.
- [ ] Aucun détail « décoratif » sans fonction évidente ; pas de bruit visuel.
- [ ] Pas d'intersection bizarre (pièces qui se traversent, raccords booléens sales, ombres de contact absentes).

## Matériaux
- [ ] Carcasse, trappe, poignée et métal usiné se distinguent **sans** changer la couleur (roughness).
- [ ] Rendu premium / utilisé / propre : pas de plastique, pas de rouille, pas de saleté excessive.
- [ ] Usure uniquement causale (arêtes exposées, contacts) ; asymétrie crédible.
- [ ] Pas de reflets « chrome noir » ni de masse noire uniforme (Studio, 2 éclairages).

## Canon (voir `Knowledge/Blender/ECLIPSE1_BARREL_DESIGN_NOTES.md`)
- [ ] Profondeur et stratification lisibles (≥ 2 niveaux de volume).
- [ ] Bouche : couronne nette, âme sombre avec profondeur visible en inspection.
- [ ] Pas de surcharge « cyberpunk » (≤ 1 rythme répétitif, ≤ 1 accent).

## Poignée et mains
- [ ] Main en contact crédible (idle, ADS, inspection début/milieu/fin).
- [ ] Aucun doigt ne traverse carcasse, pontet ou détente ; poignet naturel.

## Artefacts de rendu (Roblox)
- [ ] Aucune fine ligne claire/sombre le long des coutures UV, des arêtes ou des jonctions (SHADING §6).
- [ ] Aucun scintillement (z-fighting) ; aucune face noire/transparente.
- [ ] Normals conformes à Blender (comparaison côte à côte).
- [ ] WM sans aliasing spéculaire gênant à 12–25 studs.
