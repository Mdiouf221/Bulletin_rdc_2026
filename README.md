# Deuxième Bulletin statistique de la protection sociale en RDC

Ce workspace contient les fichiers de pilotage, de rédaction, de documentation méthodologique, de données, de tableaux, de figures et de sortie liés à la préparation du deuxième Bulletin statistique de la protection sociale en RDC.

## Objectif du workspace

- Organiser la rédaction du bulletin par sections modulaires.
- Conserver les notes internes de rédaction dans les fichiers Markdown.
- Faciliter le travail avec des agents dans VS Code.
- Préparer l’assemblage progressif d’un document Word final.

## Organisation générale

- `00_pilotage/` : architecture générale, décisions méthodologiques, feuille de route et journal des modifications.
- `01_pages_preliminaires/` : avant-propos, remerciements, sigles, listes des tableaux, graphiques et encadrés.
- `02_introduction_generale/` : sections de l’introduction générale.
- `03_chapitres/` : chapitres principaux du bulletin.
- `04_annexes/` : annexes prévues.
- `05_references/` : glossaire, conventions terminologiques, sources et instructions rédactionnelles.
- `06_sources/` : documents et données sources classés par niveau de fiabilité (`institutions/`, `officielles_web/`, `sources_incertaines/`). Chaque sous-dossier contient un sous-dossier `_texte/` pour les versions lisibles par les agents. Le registre `registre_donnees.md` inventorie tous les documents déposés.
- `07_tableaux/` : tableaux sources, exports et registre des tableaux.
- `08_figures/` : figures sources, exports et registre des figures.
- `09_scripts/` : scripts d’assemblage, nettoyage et export.
- `10_output/` : versions assemblées du bulletin.
- `06_sources/` : documents de référence externes (bulletins RDC précédents, bulletins comparatifs, rapports OIT/BIT).

## Convention de rédaction

Chaque fichier de section contient :

1. un titre ;
2. une note interne entre commentaires `<!-- NOTE_INTERNE ... -->` ;
3. une section `## Texte rédigé`.

Les notes internes guident la rédaction mais ne doivent pas apparaître dans la version finale destinée à publication.