# Dossier entrants — Sources à traiter

Ce dossier est la **zone de réception** des sources brutes : fichiers téléchargés manuellement, reçus par email, ou transmis par les institutions avant traitement.

## Comment l'utiliser

1. **Déposer** le fichier ici (PDF, XLSX, PPTX, DOCX, etc.)
2. **Signaler** à l'agent : *« J'ai déposé un fichier dans _entrants, traite-le »*
3. L'agent applique **PROC-008** et déplace le fichier dans le bon sous-dossier de `06_sources/`

## Ce qui se passe ensuite (PROC-008)

```
_entrants/fichier.pdf
      ↓ identification du type et de la source
      ↓ proposition de nommage normalisé
      ↓ déplacement vers le bon sous-dossier
      ↓ conversion .txt (si PDF)
      ↓ création de la fiche de métadonnées
      ↓ enregistrement dans registre_donnees.md et registre_sources.json
      ↓ confirmation à l'utilisateur
```

## Règle

Ce dossier doit toujours être **vide après traitement**. Un fichier qui y séjourne trop longtemps signale un traitement en suspens.
