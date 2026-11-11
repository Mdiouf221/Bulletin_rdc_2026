# Relecture intégrale — Points à arbitrer

<!-- NOTE_INTERNE
Objet du fichier :
Consigner les constats de la relecture intégrale du 3 septembre 2026 qui ne peuvent pas être corrigés
directement parce qu'ils comportent une incertitude de fond (donnée, définition, périmètre, source).
Les corrections manifestes (fautes, liens cassés, typographie) ont été appliquées directement et sont
tracées dans `00_pilotage/journal_modifications.md`.

Règle : ne rien trancher ici sans vérification auprès de la source (institution, INS, OIT).

Statut : rédigé — 2026-09-03
-->

## Méthode

Relecture croisée : fichiers sources Markdown, base `06_donnees/protection_sociale_rdc.db` (ESS),
prévisualisation navigateur, tableau de bord, et vérification Internet sur sources officielles
(NORMLEX, ILOSTAT, FMI DataMapper, Banque mondiale PIP/WDI, ONU WPP/WUP, WSPR 2024-26).

Chaque point indique : localisation, constat, éléments de vérification, gravité, options d'arbitrage.

---

## Note de suivi — Observations techniques retirées de la version publique (2026-11-11)

Les observations ci-dessous sont maintenues dans ce registre de travail ; elles ne figurent plus dans le bulletin destiné à la publication.

- Les ruptures de séries et les réserves de comparabilité relatives aux effectifs CNSSAP 2023–2024 sont documentées au point A4.
- La stabilité des effectifs SESOPA sur la période 2019–2025 est documentée au point A6.
- Les valeurs identiques des enfants couverts par la CNSS en 2021 et 2023 sont documentées au point A1.
- Les contrôles relatifs aux données CNSS 2024 de la branche des risques professionnels, ainsi qu'aux agrégats financiers CNSSAP, relèvent du suivi technique des données et ne font pas l'objet d'une note dans le bulletin.
- Les écarts de définition entre les séries et les choix de périmètre restent consignés dans les décisions méthodologiques et les sources de calcul, sans renvoi dans la version publique.

---

## Note de suivi — Reprise de la relecture PROC-003 (2026-11-11)

La revue des sections 4.2 à 4.9 du chapitre 4 et des annexes B et C a été reprise après interruption. Aucun texte du bulletin n'a été modifié dans le cadre de cette passe : conformément à PROC-003, les corrections ci-dessous restent soumises à confirmation avant intervention dans les sections rédigées.

### Constats à traiter après confirmation

1. **Traçabilité des séries pluriannuelles.** Plusieurs tableaux des sections 4.2 à 4.8 et des annexes B et C renvoient à une seule ESS, souvent CNSS 2022, alors que les valeurs couvrent plusieurs institutions et années. Les sources annuelles pertinentes, leurs annotations de validation et les sources des dénominateurs doivent être ajoutées.
2. **CNSSAP, famille et invalidité.** La valeur `0` de la branche familiale CNSSAP en 2022 doit être requalifiée en `N/A`, la branche n'étant pas opérationnelle. La série CNSS 2021/2023 identique doit conserver une réserve explicite ; les périodicités et sources des montants familiaux et des seuils de pauvreté doivent être vérifiées.
3. **Cohérence méthodologique PAM/TRESOR.** `decisions_methodologiques.md` exclut les repas scolaires PAM de l'ODD 1.3.1 strict, tandis que `indicateurs_odd_regles_calcul.md` les retient pour le sous-indicateur national 2.8 des personnes vulnérables. Cette distinction doit être rendue explicite dans les sorties. De même, le libellé de l'indicateur 2.9 doit refléter l'hypothèse TRESOR admise pour cet indicateur complémentaire, sans l'assimiler à une donnée administrative contributive directe.
4. **Annexes.** L'Annexe B contient un bloc résiduel SESOPA/TRESOR non structuré, en doublon des fiches générées, et ses titres de paragraphe ne portent pas systématiquement les badges de validation requis. Les tableaux de l'Annexe C nécessitent des captions et références interactives plus précises.
5. **Points de fond à vérifier auprès des institutions.** Restent notamment à confirmer : la série CNSS des frais funéraires, les données FSS (unités, périmètres et coûts), les données des mutuelles CGAT 2024-2025, les sources primaires des seuils de pauvreté et les données CNSSAP 2025.

### Contrôles effectués

- Les NOTE_INTERNE, la numérotation et les badges déjà présents dans les sections du chapitre 4 ont été préservés.
- Les exclusions des indemnités journalières de maladie et de maternité, ainsi que l'exclusion de la santé de l'ODD 1.3.1, sont correctement appliquées.
- La valeur OIT 2022 est séparée du calcul national dans la section 4.9.
- `py -3 -m unittest discover -s 09_scripts -p "test_*.py" -v` : 40 tests réussis.
- `git diff --check` : aucune erreur d'espacement.

---

## A. Données à confirmer auprès des institutions

### A1. CNSS — enfants couverts identiques en 2021 et 2023 (Tableau 4.6)
- **Statut : réserve ajoutée (2026-11-10).** La valeur est conservée, mais une note de prudence signale la duplication apparente et demande confirmation à la CNSS.
- **Fichier :** `03_chapitres/chapitre_4/4.4_enfants_familles.md`, Tableau 4.6 ; repris en Annexe C (C.1, ligne allocations familiales).
- **Constat :** 2021 = 2023 = 1 256 585 enfants, valeur strictement identique.
- **Vérification :** la base ESS (`prestations_historique`) contient bien 1 256 584,83 pour les deux années — la transcription est fidèle, mais la source elle-même est suspecte (duplication probable dans l'ESS CNSS 2023).
- **Gravité :** critique (indicateur enfants ODD 1.3.1 affecté).
- **Arbitrage proposé :** interroger la CNSS/l'équipe ESS ; en attendant, ajouter une note de prudence sous le Tableau 4.6.

### A2. CNSS — allocation des frais funéraires : série erratique et incohérence 4.12/4.13
- **Statut : vérifié et requalifié (2026-11-10).** Le fichier ESS CNSS 2024 ne contient qu'une seule prestation funéraire, « allocation des frais funéraires », avec un montant unitaire de 320 000 CDF ; cette ligne est également la seule retrouvée dans l'import `source_id=228`. Le montant de 230 000 CDF concerne des pensions et non une seconde prestation funéraire.
- **Fichier :** `03_chapitres/chapitre_4/4.6_deces_survie.md`, Tableaux 4.12 et 4.13.
- **Constat restant :** la série historique des montants unitaires doit toujours être confirmée auprès de la CNSS ; la réserve ne repose toutefois plus sur une prétendue seconde ligne funéraire en 2024.
- **Vérification :** le classeur source et la base ESS concordent sur l'unique ligne funéraire 2024 ; aucune fusion ni correction de donnée n'est effectuée.
- **Gravité :** majeur.
- **Arbitrage proposé :** demander à la CNSS la distinction entre les deux prestations funéraires et la validation des montants ; harmoniser ensuite T4.12/T4.13.

### A3. CNSS — indemnité journalière de maternité : 2, 2, 17, 2, 71 bénéficiaires (2020–2024)
- **Statut : vérifié et réservé (2026-11-10).** Les valeurs du tableau concordent avec les imports ESS CNSS 2020–2024 : 2, 2, 17, 2 et 71 bénéficiaires. Aucune correction de donnée n'est justifiée sans confirmation de la CNSS.
- **Fichier :** `03_chapitres/chapitre_4/4.3_age_actif.md`, Tableau 4.4 ; Annexe C.
- **Constat :** effectifs implausiblement faibles au regard des cotisantes CNSS. Le texte signale déjà la fragilité.
- **Gravité :** majeur.
- **Arbitrage proposé :** vérification auprès de la CNSS (taux de recours, exhaustivité de la déclaration ESS). Conserver la mention de prudence existante.

### A4. CNSSAP — rupture 2022→2023 des cotisants (198 399 → 1 004 106) — DM-019
- **Statut : arbitrage acté avec réserve (2026-11-10).** Les effectifs 2023–2024 sont traités comme des cotisants actifs N4 et réintégrés de manière homogène dans le Tableau 4.3, le tableau de bord et les annexes. La rupture de série et la répétition de l'effectif dans les prestations restent signalées comme réserves de comparabilité.
- **Fichiers :** chapitre 4 (Tableau 4.3, [N/D] appliqué), Annexe B (B.2.3/B.2.5), Annexe C (C.1 : la ligne « Régime de base (CNSSAP, cotisants) » affiche 1 004 106 en 2023 et 1 013 104 en 2024).
- **Constat résolu :** le chapitre 4, l'Annexe C et le tableau de bord appliquent désormais le même traitement N4.
- **Gravité :** critique (cohérence inter-chapitres et niveau de l'indicateur global).
- **Arbitrage appliqué :** retenir N4 dans l'ensemble des sorties, avec réserve explicite sur la rupture 2022–2023.

### A5. CNSSAP — périmètre des agrégats financiers 2023–2024 (Tableaux 4.16 et 4.17)
- **Statut : vérifié et traité (2026-11-10).** Les agrégats et ratios concordent avec la somme des composantes ESS disponibles ; la réserve sur les doublons potentiels est maintenue.
- **Fichier :** `03_chapitres/chapitre_4/4.8_depenses_financement.md`.
- **Constat corrigé :** les valeurs ont été recalculées sur l'ensemble des composantes déclarées dans les ESS (recettes 2023 : 353,8 Mds ; 2024 : 569,2 Mds ; prestations 2023 : 32,8 Mds ; 2024 : 51,3 Mds).
- **Vérification :** table `indicateurs_regime` (source ESS CNSSAP 2023/2024).
- **Gravité :** majeur.
- **Traitement :** la somme des composantes est retenue pour 2023–2025, avec réserve sur l'absence éventuelle de doublons. Les ratios d'efficience sont recalculés sur ce même périmètre : 56,0 % en 2023 et 58,9 % en 2024.

### A6. SESOPA — effectifs strictement identiques 2019–2026, y compris année non écoulée (2026)
- **Statut : traitement éditorial arbitré (2026-11-10).** Le bulletin reste limité à 2019–2025 ; les données SESOPA 2026, disponibles pour janvier–juillet seulement, sont conservées dans l'ESS et la base mais ne figurent pas dans les tableaux ni les graphiques. Elles pourront être mentionnées uniquement dans le texte.
- **Fichiers :** `03_chapitres/chapitre_4/4.6_deces_survie.md` (T4.12), Annexe B (B.6.3/B.6.7), Annexe C (C.1).
- **Constat :** 2 315 cotisants / 964+277+718 bénéficiaires reconduits chaque année, y compris 2026. DM-020 documente déjà l'anomalie.
- **Gravité :** majeur.
- **Traitement retenu :** ne pas afficher de colonne 2026 dans les tableaux du bulletin ; conserver la donnée ESS 2026 comme information documentaire, avec mention explicite de la couverture janvier–juillet uniquement dans le texte si nécessaire.

### A7. TRESOR (hypothèse de cotisants actifs hors CNSSAP) — série révisée
- **Statut : arbitré (2026-11-11).** Les effectifs TRESOR sont retenus dans le sous-indicateur des cotisants actifs à la retraite (2.9), mais restent exclus de l'indicateur global ODD 1.3.1. Ils sont estimés par différence, sans double compte avec la CNSSAP.
- **Fichier :** Annexe B (B.7.2), Annexe C (C.1, ligne « Pensions de retraite octroyé de la fonction publique »).
- **Constat :** en l'absence de total public homogène pour 2023, le calcul reprend l'observation ILOSTAT 2020 (1 622 972) et donne 618 866 après soustraction des 1 004 106 cotisants CNSSAP. En 2024, le total de 1 727 000 agents rémunérés, rapporté par Radio Okapi à partir de « La Fonction publique en chiffres », donne 713 896.
- **Gravité :** majeur.
- **Réserve maintenue :** les totaux de référence 2019–2024 ne constituent pas encore une série administrative homogène. Le rapport gouvernemental primaire et une ventilation institutionnelle des agents publics restent à obtenir.

### A8. FSS — « Population cible (ville-province de Kinshasa) : 1618 millions » (Tableau B.5.3)
- **Statut : traité avec intégration des données de l'atelier (2026-11-11).** La valeur manifestement erronée est retirée. Les données institutionnelles FSS 2023–2025 sont désormais présentées comme une source distincte de l'ESS, sous l'intitulé original « Kobota Ofele (non contributif) », avec distinction entre le programme quantifié et les programmes non renseignés ou non opérationnels.
- **Fichier :** `04_annexes/annexe_B_fiches_institutionnelles.md`, ligne « Population cible ».
- **Constat initial :** valeur manifestement mal saisie. Aucune source dans le dépôt ne permet de trancher entre « 16–18 millions » (fourchette FSS) et une autre valeur. Référence externe : ONU WUP donne ≈ 17,0 M d'habitants pour l'agglomération de Kinshasa en 2024.
- **Gravité :** critique (valeur absurde en l'état) — corrigée en [N/D], valeur définitive à confirmer.
- **Réserve maintenue :** les totaux additionnent femmes enceintes et nouveau-nés et les périmètres varient selon l'année ; ils ne sont pas assimilés à des personnes uniques ni intégrés aux agrégats ESS.

---

## B. Choix méthodologiques à trancher

### B1. ODD 1.3.1 — écart entre la valeur calculée (≈ 4,6 % en 2022) et la valeur publiée par l'OIT (5,2 % en 2022)
- **Statut : traité et acté (2026-11-11).** La source ILOSTAT est archivée ; le paragraphe comparatif et la ligne « RDC (valeur publiée par l'OIT) » sont présents. Le calcul national reste la valeur principale et la valeur OIT (5,2 % en 2022) est présentée séparément, conformément à DM-023.
- **Fichiers :** `03_chapitres/chapitre_4/4.9_odd_131.md`, Annexe C.
- **Vérification Internet :** ILOSTAT (`SDG_0131_SEX_SOC_RT_A`, ref_area=COD) publie **5,2 %** pour 2022 (source XA:6472) ; détail par branche : pension 1,0 ; AT 1,8 ; enfants 2,5 ; etc. — https://rplumber.ilo.org/data/indicator/?id=SDG_0131_SEX_SOC_RT_A&ref_area=COD&format=.csv
- **Constat :** le bulletin calcule à partir des ESS nationales (option documentée dans `indicateurs_odd_regles_calcul.md`) ; l'OIT publie une estimation différente. Aucune des deux n'est « fausse », mais l'écart doit être explicité.
- **Gravité :** majeur (comparabilité internationale).
- **Traitement retenu :** conserver le calcul national et présenter la valeur OIT séparément, sans les additionner ni les substituer l'une à l'autre.

### B2. Seuil de pauvreté : 72 420 CDF/mois (2019–2023, provisoire) puis environ 172 774 CDF/mois (2024)
- **Statut : traité avec réserve (2026-11-11).** Le seuil ECVM 2024 de 5 680 CDF/jour est corroboré par les résultats publics ; le montant mensuel retenu est dérivé du seuil annuel publié (2 073 282 CDF / 12). La valeur 2 414 CDF/jour pour 2019–2023 n'a pas été retrouvée dans une publication publique vérifiable et reste provisoire.
- **Fichiers :** Tableaux 4.2, 4.7, 4.10 ; Annexe A.3.
- **Constat :** saut de +135 % non commenté dans les notes de tableau. Vraisemblablement passage de l'Enquête 1-2-3 à l'ECVM 2024 (INS), mais non documenté explicitement à côté des valeurs.
- **Gravité :** majeur (le ratio pension/seuil change de base en 2024).
- **Traitement retenu :** conserver les deux périodes avec une note de rupture méthodologique ; ne pas présenter 2 414 CDF/jour comme une valeur INS définitivement confirmée.

### B3. Sous-indicateur « Enfants » : dénominateur INS 0–17 ans
- **Statut : traité (2026-11-11, arbitrage révisé).** Le dénominateur INS/RDC A3 est prioritaire pour le sous-indicateur : population âgée de 0 à 17 ans. Les effectifs 2019–2024 sont dérivés des proportions A3 arrondies et de la population totale INS ; cette précision est conservée dans les métadonnées et les notes méthodologiques.
- **Fichiers :** `4.9_odd_131.md`, `00_pilotage/indicateurs_odd_regles_calcul.md`, `10_output/dashboard_settings.json`.
- **Gravité :** majeur (le taux dépend directement du dénominateur retenu).
- **Arbitrage retenu :** utiliser le dénominateur INS A3 0–17 ans et documenter le choix dans DM-024.

### B4. Cantines scolaires PAM — « décision a été prise d'intégrer » non documentée
- **Statut : traité (2026-09-03).** Phrase reformulée dans la note du Tableau 2.4 : le programme est présenté dans la cartographie de la protection sociale des enfants mais demeure exclu de l'ODD 1.3.1 (prestation en nature), avec renvoi explicite à FICHE-002 et DM-011 — conforme au registre d'inclusion.
- **Fichier :** `03_chapitres/chapitre_2/2_1_cartographie_tableaux.md` (note du Tableau 2.4) vs `00_pilotage/registre_inclusion_programmes.md` (FICHE-002 : exclu de ODD 1.3.1, prestation en nature).
- **Gravité :** majeur (contradiction apparente entre cartographie et registre).
- **Arbitrage proposé :** soit référencer une décision méthodologique explicite (nouvelle DM), soit reformuler la note pour préciser que l'intégration vaut pour la cartographie (protection sociale des enfants au sens large) et non pour l'indicateur ODD 1.3.1.

### B5. MINAS présent dans le Tableau 2.4 (transferts) et le Tableau 2.5 (services — niveau 3)
- **Statut : vérifié (2026-11-10).** La version actuelle du Tableau 2.4 ne contient pas de programme MINAS de transferts ; le MINAS n'apparaît que dans le Tableau 2.5, pour les centres de promotion sociale et d'apprentissage professionnel. Le risque de double lecture n'est donc pas constaté dans la version actuelle.
- **Fichier :** `2_1_cartographie_tableaux.md`.
- **Gravité :** mineur à majeur (risque de double lecture).
- **Traitement :** aucune modification supplémentaire nécessaire ; conserver la distinction actuelle entre assistance sociale et politique sectorielle de niveau 3.

### B5 bis. Mutuelles volontaires (POMUCO/CGAT) — séries manquantes
- **Statut : traité (2026-11-10).** Les formulaires ESS CGAT 2024 et 2025 et la présentation institutionnelle POMUCO/CGAT ont été extraits des entrants, classés et intégrés. La série couvre désormais trois mutuelles sur 2021–2025 ; les années 2019–2020 restent [N/D]. Ces régimes volontaires ne sont pas inclus dans les indicateurs de couverture.
- **Fichier :** `04_annexes/annexe_B_fiches_institutionnelles.md`, section B.8.
- **Traitement :** les effectifs 2024–2025 sont ajoutés sans extrapolation. Les montants financiers libellés en dollars sont conservés comme données de source mais ne sont pas convertis en CDF sans taux documenté.

### B6. Terminologie « régimes octroyés » / « dispositif statutaire budgétaire »
- **Statut : traité (2026-09-03).** Entrée « Régime octroyé » ajoutée au glossaire (`05_references/glossaire.md`), rattachée explicitement à la catégorie « dispositif statutaire budgétaire », avec règle d'usage (conserver l'intitulé exact des sources).
- **Fichiers :** `4.2_vieillesse.md`, `4.3_age_actif.md`, Annexe C (« Pensions de retraite octroyé de la fonction publique »).
- **Constat :** « régime octroyé » n'est pas défini dans `05_references/glossaire.md` (qui définit « dispositif statutaire budgétaire »). Accord grammatical également à revoir (« retraite octroyé »).
- **Gravité :** mineur.
- **Arbitrage proposé :** ajouter une entrée au glossaire ou unifier vers « dispositif statutaire budgétaire ».

### B7. Millésime FMI WEO à préciser
- **Statut : clôturé (2026-11-11).** Les valeurs sont attribuées explicitement au FMI, WEO/DataMapper, millésime 2026 dans la citation de la source ; la mention erronée de la Banque mondiale WDI dans le résumé de section a été corrigée. Le millésime 2026 est conservé, car les données correspondent à la série DataMapper courante consultée le 15 juillet 2026.
- **Fichier :** `02_introduction_generale/0_2_contexte_economique_emploi.md` ; source `06_sources/officielles_web/FMI_WEO_RDC_croissance_pib_pib_habitant_2024.txt`.
- **Vérification Internet :** les valeurs (+6,4 ; +9,3 ; +8,5 ; +6,1) correspondent exactement au DataMapper FMI **courant** (édition 2025/2026), pas au WEO d'octobre 2024 (qui donnait 5,9 ; 8,8 ; 8,4 ; 4,7).
- **Gravité :** mineur (chiffres justes, millésime imprécis).
- **Traitement :** aucune modification supplémentaire nécessaire pour la présente édition.

### B8. Ratification C102 — ajouter la date exacte
- **Statut : clôturé (2026-11-11).** La date exacte est bien indiquée dans `1_2_approche_bit_oit.md` : « ratifiée le 3 avril 1987 » (NORMLEX).
- **Vérification Internet :** NORMLEX confirme : Parties V, VII, IX, X acceptées, en vigueur, ratification du **3 avril 1987**. Le bulletin dit « ratifiée en 1987 » : exact.
- **Traitement :** aucune modification supplémentaire nécessaire pour la présente édition.

---

## C. Sections incomplètes (à signaler, pas à inventer)

| Élément | Fichier | État |
|---|---|---|
| Avant-propos | `01_pages_preliminaires/avant_propos.md` | non rédigé (nécessite signature institutionnelle) |
| Table des matières | `01_pages_preliminaires/table_des_matieres.md` | placeholder |
| Listes tableaux/figures/encadrés | `01_pages_preliminaires/listes_tableaux_figures_encadres.md` | « À compléter » |
| Annexes A1, A2, D, E, F, G | `04_annexes/` | structures initiales, à rédiger |
| Figures FIG_CH4_4.2 à 4.7 | notes internes des sections 4.2–4.8 | prévues, non générées (aucun fichier dans `08_figures/`) |
| Comparaisons régionales ODD 1.3.1 | `4.9_odd_131.md` | traité — Afrique subsaharienne 19,1 % et monde 52,4 % (2023), pays comparables non chiffrés faute de valeur vérifiée |
| Données CNSS 2023–2025 (cotisants, dépenses de prestations) | ch. 4, Annexes B et C | à obtenir auprès de la CNSS |

---

## D. Points vérifiés et confirmés (aucune action)

- Numérotation « dossier chapitre_N / titre Chapitre N+1 » : **documentée et assumée** (note de cohérence de `00_pilotage/architecture_rapport.md`, juin 2026) — les signalements des relecteurs sur ce point sont des faux positifs.
- Références normatives OIT : C102 (1952, 9 branches, ratification RDC 1987 — Parties V, VII, IX, X) et R202 (2012) : **confirmées** (NORMLEX).
- WSPR 2024-26 : 52,4 % monde / 19,1 % Afrique (données 2023) : **confirmés**.
- Gini 0,447 (2020, Banque mondiale PIP) et 0,381 (INS ECVM 2024) : les deux valeurs existent ; la note de bas de page du fichier 0_2 explique déjà l'écart.
- Croissance démographique 3,3 %/an (92,9 M → 109,3 M sur 2019–2024) : **calcul exact** ((109,3/92,9)^(1/5)−1 = 3,3 %).
- Taux d'activité 63,44 % (ILOSTAT/MICS 2020), emploi informel ≈ 96 % (96,3 % en 2020) : **confirmés**.
- Chômage 4,4 % : correspond à l'estimation modélisée ILOEST 2024 (4,421 %), sourcée dans `06_sources/officielles_web/OIT_ILOSTAT_RDC_emploi_secteur_chomage_2021_2024.txt` — cohérent (l'enquête MICS 2020 donne 1,47 %, série différente ; le texte cite bien la définition BIT/estimation OIT).
- Ratio d'efficience CNSSAP 2023 = 56,0 % : **recalculé** après intégration des composantes ESS déclarées.
- Annexe C, numérateur 2025 = 4 274 : cohérent (somme des seules composantes SESOPA disponibles en 2025 : 2 315 + 964 + 277 + 718) ; la note de lecture du tableau et le texte 4.9 expliquent le caractère partiel de 2025.
- Population Kinshasa ≈ 17,1 M (2024) : confirmée (ONU World Urbanization Prospects) — à sourcer « ONU DESA, WUP » et non « WPP » le cas échéant.
