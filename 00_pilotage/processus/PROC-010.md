# PROC-010 — Suppression propre d'un import ESS en base

<!-- NOTE_INTERNE
Objet du fichier :
Décrire la procédure standard pour supprimer un import ESS de la base SQLite sans laisser d'orphelins.

Statut : actif
Version : 1.0
Date : 2026-06-11
-->

---

## Déclencheur

Ce processus est activé lorsque :
- un ESS a été importé avec une erreur (année, institution, fichier) ;
- un doublon ESS est détecté dans la base ;
- l'utilisateur demande explicitement la suppression d'un import ESS.

---

## Étape 1 — Identifier la cible

Choisir **au moins un** critère :
- `source_id` ;
- institution ;
- année ;
- nom de fichier.

Ne pas lancer de suppression sans critère, sauf demande explicite de purge totale.

---

## Étape 2 — Simulation obligatoire

Exécuter une simulation :

```bash
py 09_scripts/extraire_ess.py --delete [critères] --dry-run
```

Vérifier les volumes annoncés :
- nombre de sources ESS ciblées ;
- lignes liées dans `regimes_historique` ;
- lignes liées dans `indicateurs_regime` ;
- lignes liées dans `prestations_historique`.

---

## Étape 3 — Exécution

Après validation de la cible :

```bash
py 09_scripts/extraire_ess.py --delete [critères] --force
```

Cas exceptionnel (purge totale ESS) :

```bash
py 09_scripts/extraire_ess.py --delete --all --force
```

---

## Étape 4 — Vérification post-suppression

Confirmer :
- plus aucune source ESS ciblée dans `sources_ingestion` ;
- absence de lignes orphelines dans les trois tables liées.

---

## Étape 5 — Traçabilité

Ajouter une ligne dans `00_pilotage/journal_modifications.md` :

```
| [Date] | `09_scripts/extraire_ess.py` | PROC-010 | Suppression ESS en base ([critères]) | [auteur] |
```

---

## Livrables attendus

- [ ] Cible identifiée avec critères explicites
- [ ] Simulation `--dry-run` réalisée
- [ ] Suppression exécutée avec `--force`
- [ ] Vérification post-suppression effectuée
- [ ] Journal des modifications mis à jour

