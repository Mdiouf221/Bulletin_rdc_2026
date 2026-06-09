# PROC-009 — Instruction de l'inclusion d'un programme ou régime dans les indicateurs ODD

<!-- NOTE_INTERNE
Objet du fichier :
Définir la procédure standardisée pour décider si un programme ou régime doit être inclus
dans le calcul des indicateurs ODD 1.3.1 (et indicateurs connexes), et pour documenter
cette décision dans le registre d'inclusion.

Règle de travail :
Ce processus s'applique à tout programme ou régime dont l'inclusion n'est pas évidente.
Les programmes clairement statutaires et contributifs (CNSS, CNSSAP régime de base)
n'ont pas besoin de passer par ce processus — leur inclusion est acquise.
Ce processus est requis pour : programmes non contributifs, humanitaires, partenariaux,
programmes d'appui extérieur, programmes temporaires, régimes partiellement opérationnels.
-->

## Principe fondateur

L'inclusion d'un programme dans un indicateur ODD demande du **jugement**. La décision n'est pas toujours évidente et ne repose pas sur un seul critère. Plusieurs angles doivent être examinés simultanément. Lorsque les critères ne sont pas unanimes, la décision doit être **motivée explicitement** et documentée dans le registre des décisions d'inclusion (`registre_inclusion_programmes.md`).

---

## Étapes du processus

### Étape 1 — Identification du programme à instruire

Préciser :
- Nom du programme / régime
- Institution responsable
- Année(s) concernée(s)
- Indicateur ODD concerné (global, enfants, maternité, AT/MP, vieillesse, vulnérables, etc.)
- Motif d'instruction (première intégration, changement institutionnel, données nouvelles)

### Étape 2 — Examen selon la grille des 5 critères

Répondre à chacun des 5 critères ci-dessous. Une réponse négative n'est pas automatiquement éliminatoire, mais doit être motivée.

| # | Critère | Question | Réponse | Motivation |
|---|---------|----------|---------|-----------|
| C1 | **Nature de la prestation** | La prestation est-elle versée en espèces (cash) ? Les prestations en nature (alimentation, soins, biens) sont exclues de ODD 1.3.1. | Oui / Non / Partiel | |
| C2 | **Cadre statutaire** | Le programme est-il inscrit dans un texte légal, réglementaire ou statutaire national (loi, décret, arrêté) ? | Oui / Non / Partiel | |
| C3 | **Responsabilité primaire de l'État** | L'État (gouvernement national) est-il le garant principal et responsable juridique du programme ? Un programme co-géré ou délégué à une organisation externe (PAM, ONG, Banque mondiale) mais sous responsabilité étatique primaire peut être inclus. | Oui / Non / Partiel | |
| C4 | **Permanence** | Le programme a-t-il un caractère permanent (ou prévu comme tel), par opposition à une intervention ponctuelle, humanitaire ou liée à un projet à durée déterminée ? | Oui / Non / Partiel | |
| C5 | **Financement** | Le programme est-il principalement financé par le budget national (impôts, cotisations) ? Un financement mixte (budget + aide externe) est acceptable si la part nationale est significative et structurelle. | Oui / Non / Partiel | |

### Étape 3 — Lecture globale et décision

Après examen des 5 critères :

**Profil A — Inclusion directe** : C1 = Oui ET au moins 3 critères parmi C2–C5 = Oui
→ Inclure dans ODD 1.3.1, documenter dans le registre avec statut « Inclus ».

**Profil B — Exclusion directe** : C1 = Non (prestation en nature)
→ Exclure de ODD 1.3.1 systématiquement. Peut être présenté dans des indicateurs connexes (alimentation, santé, éducation). Documenter avec statut « Exclu — prestation en nature ».

**Profil C — Zone grise (jugement requis)** : C1 = Oui MAIS 2 critères ou plus parmi C2–C5 = Non
→ Soumettre à discussion. La décision doit être **motivée par écrit** et validée avant intégration. Documenter avec statut « Exclu — non statutaire/humanitaire » ou « Inclus avec réserve » selon la décision.

**Profil D — Indicateur connexe uniquement** : Programme non inclus dans ODD 1.3.1 mais présentant un intérêt statistique
→ Inclure dans le tableau « Programmes non statutaires et humanitaires ». Ne pas comptabiliser dans ODD 1.3.1.

### Étape 4 — Documentation

Remplir une fiche dans `registre_inclusion_programmes.md` avec :
- Les réponses aux 5 critères
- La décision finale (Inclus / Exclu / Inclus avec réserve / Indicateur connexe)
- La motivation en 2–5 phrases
- La référence à la décision méthodologique (DM-0XX) si actée
- La date et l'auteur de l'instruction

### Étape 5 — Mise à jour des outils de calcul

Si la décision est **Inclus** ou **Exclu** :
- Mettre à jour la grille de calcul dans `indicateurs_odd_regles_calcul.md` (section 3.2)
- Vérifier l'impact sur les doubles comptages (section 3.2 du même fichier)
- Si impact sur une décision méthodologique transversale : mettre à jour `decisions_methodologiques.md`

---

## Cas particuliers

### Programmes à responsabilité partagée État/partenaire
Exemple : programme STEP (Banque mondiale / IDA), cantines scolaires MEPST co-financées.
→ Appliquer C3 avec nuance : si l'État a signé un accord de co-responsabilité et que le programme figure dans les rapports institutionnels nationaux, C3 peut être considéré comme « Partiel » et non « Non ». La décision reste du profil C (jugement requis).

### Programmes clôturés mais dont les données restent dans la série historique
Exemple : STEP clôturé en février 2024.
→ Appliquer la décision d'inclusion/exclusion de manière rétroactive et cohérente sur toute la série. Un programme exclu pour 2024 doit être exclu pour toutes les années antérieures également, sauf décision motivée contraire.

### Changement de nature d'un programme dans le temps
Exemple : un programme humanitaire qui devient progressivement un programme national permanent.
→ Documenter le point de bascule (année, texte légal ou décision institutionnelle) et appliquer l'inclusion à partir de cette année.

---

## Référence croisée

- `registre_inclusion_programmes.md` — décisions programme par programme
- `indicateurs_odd_regles_calcul.md` — règles de calcul et mapping ESS
- `decisions_methodologiques.md` — décisions transversales (DM-010, DM-011…)
- PROC-002 — Intégration d'une donnée institutionnelle
- PROC-004 — Vérification terminologique

---

*Processus créé le 2026-06-09.*
