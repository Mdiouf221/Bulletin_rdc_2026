# Règles de calcul des indicateurs ODD 1.3.1 — Document de référence

<!-- NOTE_INTERNE
Objet du fichier :
Document de référence méthodologique stabilisant les règles de calcul des indicateurs ODD 1.3.1
pour la préparation du deuxième Bulletin statistique sur la protection sociale en RDC.

Sources mobilisées :
- BIT, World Social Protection Report 2024-26 (source principale, Annex 2 méthodologie)
- BIT, World Social Protection Report 2020-22
- Bulletins comparateurs : Angola (2e éd.), Mozambique (7e éd.), Timor-Leste, São Tomé-et-Príncipe, Guinée-Bissau
- ESS RDC tous régimes 2023 + ESS CNSS 2019-2022 + ESS CNSSAP 2020-2022
- 1er Bulletin statistique RDC (critique interne)

Statut : rédigé — version de travail à discuter et stabiliser avant calcul
-->

---

## 1. Définition officielle de l'indicateur

**Libellé officiel ODD 1.3.1 (WSPR 2024-26) :**
> *"Proportion of population covered by social protection floors/systems, by sex, distinguishing children, unemployed persons, older persons, persons with disabilities, pregnant women, newborns, work injury victims and the poor and the vulnerable."*

L'indicateur mesure la **couverture effective**, pas seulement la couverture légale. Il inclut :
- les personnes recevant effectivement au moins une prestation en espèces, **ou**
- les personnes cotisant activement à au moins un régime de protection sociale.

**Exclusion critique :** les prestations de soins de santé (couverture maladie) et les indemnités journalières de maladie ou de maternité sont **exclues** des indicateurs ODD 1.3.1. La santé relève des indicateurs ODD 3.8.1 et 3.8.2. Cette exclusion s'applique même lorsque le régime parent est inclus ; elle évite de compter comme personnes couvertes par une prestation des bénéficiaires ponctuels déjà comptabilisés parmi les cotisants actifs.

### Convention de disponibilité des valeurs

Dans les sorties ODD, `0` signifie une valeur explicitement observée égale à zéro dans l’ESS. `N/D` indique qu’une donnée attendue est indisponible ou non vérifiable ; une valeur `NULL` de la base doit donc rester `N/D` jusqu’à la sortie. `N/A` désigne un programme, une prestation ou un élément structurellement hors périmètre, y compris avant sa mise en œuvre. Ces statuts ne sont pas interchangeables.

---

## 2. Les neuf sous-indicateurs officiels

### 2.1 Indicateur global — Population couverte par au moins une branche

| Élément | Définition |
|---------|-----------|
| **Numérateur** | Nombre de personnes recevant au moins une prestation en espèces de protection sociale (hors santé) ou cotisant activement à au moins un régime |
| **Dénominateur** | Population totale |
| **Source OIT recommandée** | ILO World Social Protection Database, Social Security Inquiry (SSI), ILOSTAT |
| **Référence mondiale 2023** | 52,4 % (Afrique : 19,1 %) |
| **Référence mondiale 2020** | 46,9 % |
| **Unité** | % de la population totale |
| **Note** | Cet indicateur est la somme non-dupliquée des sous-indicateurs 2.2 à 2.8 ; le double comptage entre groupes doit être évité |

### 2.2 Population âgée de 0–17 ans — Prestations famille/enfants

| Élément | Définition |
|---------|-----------|
| **Numérateur** | Nombre de bénéficiaires âgés de 0 à 17 ans recevant au moins une prestation en espèces pour enfants ou famille |
| **Dénominateur** | Population totale âgée de 0 à 17 ans |
| **Source OIT recommandée** | ESS — feuille famille/enfants (bénéficiaires allocations familiales, allocations prénatales, pensions d'orphelins) |
| **Référence mondiale 2023** | 28,2 % (enfants 0–15) / 23,9 % (enfants 0–18) |
| **Référence mondiale 2020** | 26,4 % |
| **Unité** | % de la population âgée de 0 à 17 ans |
| **Note** | En RDC, la CNSS déclare des allocations familiales (bénéficiaires = enfants imputés via un facteur de conversion) ; la CNSSAP déclare des orphelins. L'actualisation du facteur de conversion enfants/foyer est critique. |

### 2.3 Femmes ayant accouché — Prestations de maternité

| Élément | Définition |
|---------|-----------|
| **Numérateur** | Nombre de femmes ayant accouché recevant une prestation en espèces de maternité, à l'exclusion des indemnités journalières de maternité retenues hors des indicateurs ODD |
| **Dénominateur** | Nombre total de naissances vivantes dans l'année (ou femmes ayant accouché) |
| **Source OIT recommandée** | ESS — feuille maternité (indemnités journalières versées), données état civil (naissances) |
| **Référence mondiale 2023** | 36,4 % |
| **Référence mondiale 2020** | 44,9 % |
| **Unité** | % des femmes ayant accouché |
| **Note** | En RDC, les indemnités journalières de maternité déclarées dans les ESS sont conservées comme données institutionnelles, mais exclues des indicateurs ODD pour éviter le double comptage avec les cotisants actifs. Le numérateur retient les bénéficiaires de l'allocation de maternité CNSS. Le dénominateur applique une règle stable : naissances vivantes observées lorsqu'elles sont disponibles ; à défaut, estimation démographique documentée à partir du taux brut de natalité et de la population de la même année. |

### 2.4 Personnes en situation de handicap grave — Prestations d'invalidité

| Élément | Définition |
|---------|-----------|
| **Numérateur** | Nombre de personnes en situation de handicap grave recevant une prestation en espèces pour invalidité |
| **Dénominateur** | Population estimée de personnes en situation de handicap grave : 3 % de la population totale, à défaut de donnée nationale annuelle |
| **Source OIT recommandée** | ESS — feuille invalidité (pensions d'invalidité, rentes d'incapacité permanente) ; enquêtes ménages sur le handicap |
| **Référence mondiale 2023** | 38,9 % |
| **Référence mondiale 2020** | 33,5 % |
| **Unité** | % des personnes en situation de handicap grave |
| **Note** | En RDC : le premier bulletin retient une estimation BIT fondée sur les données OMS et ONU. En l'absence de donnée nationale annuelle comparable, le présent bulletin applique 3 % de la population totale : point médian de la fourchette internationale OMS de 2 à 4 % pour les limitations fonctionnelles graves. Cette valeur est une estimation, non une observation nationale. |

### 2.5 Travailleurs en cas d'accidents du travail — Prestations AT/MP

| Élément | Définition |
|---------|-----------|
| **Numérateur** | Nombre de personnes de la main-d'œuvre couvertes par des prestations en espèces en cas d'accident du travail ou maladie professionnelle (cotisants actifs AT/MP) |
| **Dénominateur** | Force de travail 15+ (labour force = personnes en emploi + chômeurs) |
| **Source OIT recommandée** | ESS — feuille risques professionnels (cotisants/assurés actifs AT/MP) ; ILOSTAT (taux de participation à la force de travail 63,44 %, MICS 2020) |
| **Référence mondiale 2023** | 37,4 % |
| **Référence mondiale 2020** | 35,4 % |
| **Unité** | % de la force de travail |
| **Note** | Le libellé officiel ILOSTAT est « Labour force covered in the event of work injury ». La CNSS Régime 2 est la source principale ; la CNSSAP AT/MP n'était pas opérationnelle avant 2023. L'estimation ILOSTAT de 1,8 % pour 2022 est une référence externe : elle ne doit pas être substituée au taux de 1,1 % calculé dans le bulletin avec les effectifs ESS et le dénominateur national retenu. |

### 2.6 Chômeurs — Protection contre le chômage

| Élément | Définition |
|---------|-----------|
| **Numérateur** | Nombre de personnes chômeurs recevant effectivement des allocations de chômage |
| **Dénominateur** | Nombre total de personnes au chômage (BIT) |
| **Source OIT recommandée** | ESS — feuille chômage ; enquêtes sur les forces de travail |
| **Référence mondiale 2023** | 16,7 % |
| **Référence mondiale 2020** | 18,6 % |
| **Unité** | % des chômeurs |
| **Statut en RDC** | N/A — aucun régime d'assurance chômage n'existe dans le périmètre du bulletin. |

### 2.7 Personnes âgées — Pension de vieillesse

| Élément | Définition |
|---------|-----------|
| **Numérateur** | Nombre de bénéficiaires d'une pension de vieillesse, y compris les pensions de retraite anticipée ; ces dernières peuvent concerner des personnes âgées de moins de 60 ans |
| **Dénominateur** | Population totale au-dessus de l'âge légal de la retraite |
| **Source OIT recommandée** | ESS — feuille vieillesse (nombre de pensionnés) ; projections démographiques ONU pour le dénominateur |
| **Référence mondiale 2023** | 79,6 % |
| **Référence mondiale 2020** | 77,5 % |
| **Unité** | % de la population au-delà de l'âge légal de la retraite |
| **Note** | En RDC : le dénominateur unique retient la population âgée de 60 ans et plus. Le numérateur conserve les pensions de retraite anticipée ouvertes dès 55 ans sous conditions ; cette différence de périmètre est explicitement signalée dans le bulletin. |

### 2.8 Personnes vulnérables — Assistance sociale

| Élément | Définition |
|---------|-----------|
| **Numérateur** | Somme des enfants bénéficiaires de prestations familiales, dont les allocations familiales CNSS, et des enfants servis par les repas scolaires PAM |
| **Dénominateur** | Population totale, moins les cotisants actifs dédupliqués, TRESOR inclus, et les bénéficiaires de pensions de vieillesse |
| **Source OIT recommandée** | ESS — programmes non contributifs (MINAS, transferts monétaires, programmes d'assistance) ; enquêtes ménages sur la pauvreté |
| **Référence mondiale 2023** | 37,3 % |
| **Référence mondiale 2020** | 28,9 % |
| **Unité** | % de la population vulnérable |
| **Note** | Tous les enfants relèvent de la population vulnérable selon le guide statistique de l'OIT. Les allocations familiales CNSS sont déjà exprimées comme une estimation d'enfants bénéficiaires, sur la base historique de 3,17 enfants par titulaire ; elles ne sont pas multipliées une seconde fois. Les repas scolaires PAM sont une intervention non contributive en nature ; les séries disponibles couvrent 2021–2025. Faute d'identifiant individuel commun, le numérateur ne déduplique pas un éventuel recoupement entre les deux interventions. La valeur PAM 2024 de 272 000 enfants est retenue avec réserve, car le tableau détaillé du même rapport indique 194 636 enfants servis sur site. L'estimation OIT de 2,9 % en 2022 reste une référence externe, distincte du calcul du bulletin. |

### 2.9 Cotisants actifs à un régime de retraite (indicateur complémentaire)

| Élément | Définition |
|---------|-----------|
| **Numérateur** | Nombre de personnes cotisant activement à un régime de retraite contributif |
| **Dénominateur** | Population en âge de travailler de 15 à 64 ans |
| **Source OIT recommandée** | ESS — feuilles retraite (cotisants actifs) ; population âgée de 15 à 64 ans |
| **Référence** | Variable selon pays |
| **Unité** | % de la population âgée de 15 à 64 ans |
| **Note** | Indicateur complémentaire mesurant la couverture contributive, distinct de la couverture effective par prestations. Le dénominateur de 15 à 64 ans est retenu uniformément pour toutes les années de la série. |

---

## 3. Mapping données ESS RDC → indicateurs ODD 1.3.1

### 3.1 Disponibilité des données par régime et branche

| Régime | Institution | Fonction | Données disponibles | Qualité | Années ESS |
|--------|-------------|----------|---------------------|---------|-----------|
| CNSS — Familles | CNSS | Enfants, Maternité | Allocations familiales (foyers), indemnités journalières maternité | Bonne | 2019–2022 |
| CNSS — AT/MP | CNSS | Risques professionnels | Bénéficiaires rentes, indemnités journalières AT | Bonne | 2019–2022 |
| CNSS — Pensions | CNSS | Vieillesse, Invalidité, Survivants | Pensionnés (vieillesse, invalidité, survie), cotisants actifs | Excellente | 2019–2022 |
| CNSSAP — Régime de base | CNSSAP | Vieillesse, Invalidité, Survivants | Pensionnés, cotisants actifs | Bonne | 2020–2022 |
| CNSSAP — Allocations familiales | CNSSAP | Enfants, Famille, Maternité | Non opérationnel en 2022 | Absente | — |
| CNSSAP — AT/MP | CNSSAP | Risques professionnels | Non opérationnel en 2022 | Absente | — |
| FSS — Santé | FSS | Santé | Non inclus ODD 1.3.1 (exclusion santé) | N/A | — |
| MINAS | MINAS | Assistance sociale | Bénéficiaires programmes (partiel), pas d'effectifs annuels précis | Fragmentée | 2023 |
| MEPST — Cantines | MEPST | Alimentation/nutrition | Repas servis (non monétaire) | Partielle | 2023 |
| STEP (Banque mondiale) | IDA | Transferts + santé | Bénéficiaires (clôturé en juin 2025) | Ponctuelle | 2023 |
| PAM | PAM | Transferts, repas | Bénéficiaires estimés (très larges) | Externe | Annuelle |
| MESP | MESP | Santé enseignants | Non inclus ODD 1.3.1 (exclusion santé) | N/A | — |

### 3.2 Mapping sous-indicateur → source ESS disponible

| Sous-indicateur ODD | Source primaire ESS | Données numérateur | Données dénominateur | Disponibilité |
|---------------------|--------------------|--------------------|----------------------|---------------|
| 2.2 — Population 0–17 ans | CNSS Familles, CNSSAP Familles | Foyers bénéficiaires × facteur enfants | Population 0–17 ans (INS/RDC, A3) | ⚠ Partielle (CNSSAP familles non opérationnel 2022) |
| 2.3 Maternité | CNSS Familles | Indemnités journalières maternité | Naissances vivantes (INS) | ⚠ Possible mais non réalisé dans 1er bulletin |
| 2.4 Handicap | CNSS Pensions (invalidité) | Bénéficiaires pensions invalidité | Population handicapée grave (à estimer) | ✗ Dénominateur absent |
| 2.5 AT/MP | CNSS AT/MP, CNSSAP AT/MP | Cotisants/assurés actifs AT/MP | Force de travail 15+ (ILOSTAT LFP × pop 15+) | ✓ Bonne (CNSS seule pour 2019-2022) |
| 2.6 Chômage | Aucune | N/A — assurance chômage inexistante | Chômeurs (ILOSTAT) | N/A |
| 2.7 Vieillesse | CNSS Pensions, CNSSAP Base | Pensionnés vieillesse | Pop. au-delà âge légal (ONU WPP) | ✓ Bonne |
| 2.8 Assistance sociale | MINAS, PAM, STEP | Bénéficiaires programmes | Population totale | ⚠ Fragmentée, double comptage |
| 2.9 Cotisants retraite | CNSS Pensions, CNSSAP Base | Cotisants actifs déclarés | Force de travail (ILOSTAT) | ⚠ Rupture CNSSAP 2022–2023, réserve de comparabilité |

---

## 4. Critique du premier bulletin RDC — Incohérences identifiées

### 4.1 Surestimation du taux de cotisants retraite (CNSSAP)

**Problème :** Le 1er bulletin utilise 1 623 000 comme nombre de cotisants CNSSAP (équivalent aux fonctionnaires publics selon ILOSTAT 2020), alors que l'ESS CNSSAP 2022 déclare seulement 198 399 cotisants actifs réels.

| Indicateur | Valeur affichée (Tableau 23) | Calcul avec données réelles | Écart |
|-----------|-----------------------------|-----------------------------|-------|
| Cotisants actifs retraite | 6,4 % | (613 761 CNSS + 198 399 CNSSAP) / 35 059 191 ≈ **2,3 %** | **+4,1 points** |

**Explication du bulletin :** *"Basé, entre autres, sur une estimation du nombre de contributeurs de la CNSSAP égal au nombre d'employés de la fonction publique en 2020 (1 623 000 selon ILOSTAT)."*

**Évaluation critique :** Cette estimation est celle utilisée par le tableau de bord OIT (qui ne dispose pas des données ESS directes). Elle est défendable à des fins de comparaison internationale, mais trompeuse si présentée sans mention explicite. Le 2e bulletin doit :
- Présenter les deux chiffres (données ESS réelles + estimation OIT) ;
- Expliquer l'écart (réforme CNSSAP en cours, sous-enregistrement) ;
- Ou choisir les données ESS réelles et documenter la raison de l'écart avec le tableau de bord OIT.

### 4.2 Taux assistance sociale non réconcilié (Tableau 23 vs Tableau 20)

**Problème :** Le taux affiché pour les « personnes vulnérables couvertes par l'assistance sociale » (2,9 %) ne correspond à aucun calcul identifiable à partir des tableaux détaillés.

| Indicateur | Tableau 23 | Calcul possible (T20) | Écart |
|-----------|-----------|----------------------|-------|
| Vulnérables — assistance sociale | 2,9 % | 1 130 048 / 99 010 212 ≈ **1,14 %** | **+1,76 points** |

**Hypothèse :** Le 2,9 % pourrait inclure les bénéficiaires PAM (non documentés dans le tableau). Si c'est le cas, cela contredit la note de bas de page qui dit inclure le PAM dans l'ODD global, mais sans en détailler le calcul.

### 4.3 Taux enfants non réconcilié

| Indicateur | Tableau 23 | Calcul possible | Écart |
|-----------|-----------|-----------------|-------|
| Population 0–14 ans | 2,6 % | 1 130 048 / 52 490 412 ≈ **2,15 %** | **+0,45 points** |

**Cause probable :** facteur enfants/foyer différent ou population de référence différente (0–14 vs 0–17).

### 4.4 PAM mentionné mais non intégré

**Problème :** Le 1er bulletin déclare (p. 30) : *"L'indicateur ODD 1.3.1 prend également en compte le nombre de bénéficiaires de repas scolaires et de transferts monétaires du PAM."*

Or le Tableau 23 ne décompose pas la contribution PAM. Le PAM représente 3,8 millions de bénéficiaires (246 530 repas + 3 790 107 transferts en 2022) — soit un potentiel d'augmentation de l'indicateur global de ~3 à 4 points.

**Décision à prendre pour le 2e bulletin :**
- Inclure le PAM dans l'indicateur global (en précisant la méthodologie) ;
- Ou l'exclure et documenter pourquoi (caractère non-statutaire, données insuffisamment fiables).

### 4.5 Régimes CNSSAP non opérationnels en 2022

La CNSSAP n'avait pas mis en œuvre les branches Allocations familiales ni AT/MP en 2022. Ces données sont donc légitimement absentes. En revanche, leur absence doit être documentée explicitement dans le 2e bulletin (et leur mise en œuvre progressive à partir de 2023 mérite un encadré).

### 4.6 Anomalie ESS CNSS 2020 — ✅ RÉSOLUE

L'ESS CNSS 2020 (fichier `ESS_CNSS_2020_ANOMALIE.txt`) contenait des données CNSSAP. Un fichier corrigé `ESS_CNSS_2020.txt` a été intégré via PROC-008 le 2026-06-10. La série temporelle CNSS 2019–2022 est désormais complète.

### 4.7 Source ODD 1.3.1 : tableau de bord OIT vs calcul à partir des ESS

**Constat fondamental :** Les valeurs ODD 1.3.1 du 1er bulletin proviennent du tableau de bord OIT (https://www.social-protection.org), qui utilise des estimations modélisées par l'OIT et non les données ESS directes. Cela explique les écarts avec les calculs possibles à partir des ESS.

**Impact pour le 2e bulletin :** Il faut décider explicitement entre :
1. **Option A** — Reproduire les estimations du tableau de bord OIT pour ODD 1.3.1 (comparabilité internationale, mais perte de rigueur interne) ;
2. **Option B** — Calculer ODD 1.3.1 directement à partir des ESS nationales (plus rigoureux, mais résultats différents des estimations OIT) ;
3. **Option C** — Présenter les deux : calcul ESS + estimation OIT en comparaison explicite (recommandé).

---

## 5. Questions ouvertes à trancher avant calcul

| N° | Question | Impact | Priorité |
|----|----------|--------|----------|
| Q1 | ~~Quel facteur enfants/foyer utiliser pour la CNSS ?~~ → **RÉSOLUE — voir DM-010** | Sous-indicateur 2.2 | ✅ |
| Q2 | Inclure ou exclure le PAM dans ODD 1.3.1 ? Et dans quel sous-indicateur ? | Sous-indicateurs 2.2 et 2.8 | Haute |
| Q3 | Utiliser estimation CNSSAP (1,6M) ou données ESS réelles (198 399) pour les cotisants ? | Sous-indicateur 2.9 | Haute |
| Q4 | Quel dénominateur pour les personnes âgées ? (âge légal retraite = 60 ou 65 ans selon régime) | Sous-indicateur 2.7 | Haute |
| Q5 | Comment traiter le CNSSAP AT/MP et familles (non opérationnel 2022) dans la série temporelle ? | Tous sous-indicateurs | Moyenne |
| Q6 | Comment traiter l'ESS CNSS 2020 (données manquantes/corrompues) ? | Série temporelle | Moyenne |
| Q7 | Intégrer les régimes spéciaux (militaires, magistrats, parlementaires) ? Données disponibles ? | Indicateur global | Moyenne |
| Q8 | Quel est le dénominateur pour le sous-indicateur handicap (prévalence nationale du handicap grave) ? | Sous-indicateur 2.4 | Haute |
| Q9 | ODD calculé à partir des ESS ou tableau de bord OIT ? (Options A/B/C — voir section 4.7) | Tous | Critique |
| Q10 | Traitement du double comptage entre programmes non statutaires (PAM, MINAS) et régimes officiels ? | Indicateur global | Haute |
| Q11 | Intégrer l'ESS RDC tous régimes 2023 comme référence principale ou comparer 2022 vs 2023 ? | Structure temporelle | Moyenne |
| Q12 | **[RÉSOLUE]** Utiliser population en emploi (au lieu de population active) comme dénominateur pour AT/MP ? | Sous-indicateur 2.5 | ✅ **OUI** |

---

## 5a. Méthodologie AT/MP — Dénominateur = Force de travail (labour force 15+)

### Définition OIT confirmée

Le sous-indicateur ODD 1.3.1 2.5 mesure la couverture contre les accidents du travail et maladies professionnelles. Le libellé officiel ILOSTAT (SDG_0131_SEX_SOC_RT_A) est :

> **« Labour force covered in the event of work injury »**

Le dénominateur est donc la **force de travail 15+** (labour force = personnes en emploi + chômeurs), et non la population totale ni la population en emploi seule.

**Règle appliquée dans le bulletin :** le numérateur est constitué des cotisants
AT/MP et des bénéficiaires de rentes AT/MP inclus dans les ESS ; le dénominateur est
la force de travail 15+ correspondante, selon les valeurs annuelles retenues dans le
canevas INS/RDC. Cette règle est appliquée uniformément à chaque année calculée.

### Exemple de calcul (année 2022)

- Numérateur ESS retenu : 616 595 personnes ;
- Force de travail 15+ retenue : 54 679 981 personnes ;
- **Taux du bulletin : 616 595 / 54 679 981 = 1,1 %**.

La valeur ILOSTAT publiée de 1,8 % pour 2022 est une référence externe fondée sur
un périmètre et un dénominateur distincts ; elle n'est pas utilisée pour modifier la
série du bulletin.

### Sources de données utilisées

| Données | Source | Référence |
|---------|--------|-----------|
| Force de travail 15+ | INS/RDC, canevas de collecte 2026 | Valeurs annuelles retenues pour la série |
| Cotisants AT/MP | CNSS ESS, CNSSAP ESS | `06_sources/ESS/` |

**Règle :** Si une source ne produit que la population active (sans taux de chômage associé), appliquer le taux de chômage RDC par défaut (4,4 %, 2024) ou utiliser l'année spécifique si disponible.

---

## 6. Méthodologie recommandée pour le 2e bulletin

### 6.1 Principe général

Calculer les indicateurs ODD 1.3.1 à partir des données ESS RDC (Option B ou C), en distinguant :
- Les données **administratives directes** (cotisants CNSS, pensionnés CNSSAP, rentes AT/MP) → chiffres robustes ;
- Les données **estimées ou partielles** (CNSSAP cotisants, enfants via facteur, MINAS) → signalées explicitement ;
- Les données **absentes** sont indiquées comme N/D ; une branche inexistante, telle que l'assurance chômage, est indiquée N/A.

### 6.2 Arbre de décision pour chaque sous-indicateur

```
Pour chaque sous-indicateur ODD 1.3.1 :
  1. Identifier le numérateur dans les ESS disponibles (CNSS, CNSSAP, MINAS, ESS consolidé 2023)
  2. Identifier le dénominateur approprié (ONU WPP, ILOSTAT, INS RDC)
  3. Vérifier l'absence de double comptage entre régimes
  4. Documenter le niveau de fiabilité (robuste / estimé / absent)
  5. Comparer avec la valeur du tableau de bord OIT et expliquer tout écart > 1 point
```

### 6.3 Sources recommandées par dénominateur

| Dénominateur | Source | Référence |
|-------------|--------|-----------|
| Population totale | ONU WPP 2024 RDC | `06_sources/officielles_web/_texte/ONU_WPP_2024_RDC_population.txt` |
| Population 0–17 ans | INS/RDC, canevas de collecte 2026 (A3) | Idem |
| Population au-delà âge légal retraite | ONU WPP 2024 | Idem |
| Force de travail / population active | ILOSTAT Modelled Estimates | `EAP_DWAP_SEX_AGE_RT_A` (population 15+, tous indicateurs sauf AT/MP) |
| Population en emploi (AT/MP) | ILOSTAT (population active × (1 - taux chômage)) | Calculée à partir de `EAP_DWAP_SEX_AGE_RT_A` et `UNE_DEUI_RT_A` |
| Naissances vivantes | INS RDC (ou ONU WPP) | À confirmer |
| Population handicapée grave | Estimation OMS (15 % pop. générale, dont ~3–4 % grave) | À documenter |

---

## 7. Grille de calcul (squelette)

Pour chaque année disponible (2019, 2021, 2022, 2023) :

```
SOUS-INDICATEUR 2.2 — Enfants
  Numérateur = Foyers bénéficiaires CNSS Familles × facteur_enfants [à valider]
               + Orphelins CNSSAP (si disponible)
               + Enfants bénéficiaires PAM [si décision d'inclure]
  Dénominateur = Population 0-17 ans (ONU WPP)

SOUS-INDICATEUR 2.3 — Maternité
  Numérateur = Indemnités journalières maternité CNSS versées (bénéficiaires uniques)
  Dénominateur = Naissances vivantes RDC (INS)

SOUS-INDICATEUR 2.5 — AT/MP
  Numérateur = Cotisants/assurés actifs AT/MP (CNSS Régime 2)
               + Cotisants/assurés actifs CNSSAP AT/MP (à partir 2023)
  Dénominateur = Force de travail 15+ (pop 15+ × taux participation 63,44% ILOSTAT)
                 [Voir section 5a pour formule de calcul]
  Résultat = % de la population totale
  Numérateur = Pensionnés vieillesse CNSS
               + Pensionnés CNSSAP
               + Pensionnés régimes spéciaux [si données disponibles]
  Dénominateur = Population au-delà âge légal retraite (ONU WPP)

SOUS-INDICATEUR 2.8 — Assistance sociale
  Numérateur = Bénéficiaires MINAS [à préciser]
               ± Transferts PAM [si inclus]
               ± Cantines MEPST [si inclus]
  Dénominateur = Population totale (ou population pauvre, à décider)

SOUS-INDICATEUR 2.9 — Cotisants retraite
  Numérateur = Cotisants actifs CNSS Pensions
               + Cotisants actifs CNSSAP Régime base [données ESS réelles]
  Dénominateur = Force de travail 15+ (ILOSTAT)
  [Comparer avec estimation OIT utilisant 1 623 000 CNSSAP]

INDICATEUR GLOBAL
  = Part de la population couverte par AU MOINS UN des sous-indicateurs ci-dessus
  [Nécessite déduplification entre régimes]
```

---

## 8. Pratiques des bulletins comparateurs

| Pays | Couverture globale ODD 1.3.1 | Approche notable |
|------|------------------------------|-----------------|
| **Timor-Leste** (2024) | 27,0 % | Distinction contributif (12,2 %) / non-contributif (14,8 %) présentée séparément |
| **São Tomé-et-Príncipe** (2021) | 22,1 % | Tableau par régime et par sexe (H/F) ; limites du secteur informel documentées |
| **Mozambique** (2025) | N.D. | Métadonnées complètes (numérateur/dénominateur) publiées en annexe ; seuil national de pauvreté utilisé |
| **Angola** (2024) | N.D. | Méthode Alkire-Foster pour définir la vulnérabilité ; 3 piliers distincts |
| **Guinée-Bissau** | N.D. | Premier bulletin, données limitées |

**Pratique recommandée :** publier les métadonnées en annexe (numérateur, dénominateur, source, année, note de fiabilité) — comme le fait le Mozambique.

---

## 9. Journal des décisions à prendre

Les questions de la section 5 doivent être arbitrées lors d'une session de discussion avant le calcul. Les décisions prises devront être documentées dans `00_pilotage/decisions_methodologiques.md` (comme DM-010 et suivantes).

---

*Document produit le 2026-06-09. À mettre à jour après discussion avec l'équipe OIT/RDC.*
