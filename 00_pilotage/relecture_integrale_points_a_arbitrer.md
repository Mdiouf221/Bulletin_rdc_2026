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

## A. Données à confirmer auprès des institutions

### A1. CNSS — enfants couverts identiques en 2021 et 2023 (Tableau 4.6)
- **Fichier :** `03_chapitres/chapitre_4/4.4_enfants_familles.md`, Tableau 4.6 ; repris en Annexe C (C.1, ligne allocations familiales).
- **Constat :** 2021 = 2023 = 1 256 585 enfants, valeur strictement identique.
- **Vérification :** la base ESS (`prestations_historique`) contient bien 1 256 584,83 pour les deux années — la transcription est fidèle, mais la source elle-même est suspecte (duplication probable dans l'ESS CNSS 2023).
- **Gravité :** critique (indicateur enfants ODD 1.3.1 affecté).
- **Arbitrage proposé :** interroger la CNSS/l'équipe ESS ; en attendant, ajouter une note de prudence sous le Tableau 4.6.

### A2. CNSS — allocation des frais funéraires : série erratique et incohérence 4.12/4.13
- **Fichier :** `03_chapitres/chapitre_4/4.6_deces_survie.md`, Tableaux 4.12 et 4.13.
- **Constat :** (i) montants unitaires 180K/220K/320K/320K/180K/320K CDF sans logique temporelle ; (ii) T4.12 affiche [N/D] pour 2024 (bénéficiaires écartés au titre de l'anomalie « 2 853 » — DM-021) alors que T4.13 affiche un montant 2024 de 320 000 CDF.
- **Vérification :** la base ESS reflète fidèlement ces valeurs (deux lignes distinctes « allocation des frais funéraires » et « frais funéraires » coexistent, avec montants différents : 320 000 vs 230 000 en 2024).
- **Gravité :** majeur.
- **Arbitrage proposé :** demander à la CNSS la distinction entre les deux prestations funéraires et la validation des montants ; harmoniser ensuite T4.12/T4.13.

### A3. CNSS — indemnité journalière de maternité : 2, 2, 17, 2, 71 bénéficiaires (2020–2024)
- **Fichier :** `03_chapitres/chapitre_4/4.3_age_actif.md`, Tableau 4.4 ; Annexe C.
- **Constat :** effectifs implausiblement faibles au regard des cotisantes CNSS. Le texte signale déjà la fragilité.
- **Gravité :** majeur.
- **Arbitrage proposé :** vérification auprès de la CNSS (taux de recours, exhaustivité de la déclaration ESS). Conserver la mention de prudence existante.

### A4. CNSSAP — rupture 2022→2023 des cotisants (198 399 → 1 004 106) — DM-019
- **Statut : transparence renforcée (2026-09-03).** Un « point de vigilance (DM-019) » a été ajouté dans la section 4.9 : il signale explicitement que le numérateur 2023-2024 du tableau de bord intègre ces effectifs alors que le Tableau 4.3 les écarte, et que les taux 2023-2024 doivent être lus comme des valeurs hautes provisoires. **L'arbitrage de fond (N3 vs N4) reste entier** et nécessite la confirmation de la CNSSAP.
- **Fichiers :** chapitre 4 (Tableau 4.3, [N/D] appliqué), Annexe B (B.2.3/B.2.5), Annexe C (C.1 : la ligne « Régime de base (CNSSAP, cotisants) » affiche 1 004 106 en 2023 et 1 013 104 en 2024).
- **Constat :** le chapitre 4 écarte prudemment ces valeurs ([N/D]) alors que l'Annexe C les intègre au numérateur ODD 1.3.1 — traitement non homogène d'une même donnée.
- **Gravité :** critique (cohérence inter-chapitres et niveau de l'indicateur global).
- **Arbitrage proposé :** trancher au niveau DM-019 : soit affiliés (N3, à exclure du numérateur « cotisants actifs »), soit cotisants (N4, à réintégrer partout). Appliquer ensuite le même traitement au chapitre 4, à l'Annexe B et à l'Annexe C/tableau de bord.

### A5. CNSSAP — périmètre des agrégats financiers 2023–2024 (Tableaux 4.16 et 4.17)
- **Fichier :** `03_chapitres/chapitre_4/4.8_depenses_financement.md`.
- **Constat :** les notes de source indiquent que « les agrégats 2023–2024 intègrent les composantes déclarées dans les ESS » ; or les valeurs affichées correspondent au **régime de base seul** (recettes 2023 : 281,6 Mds = R1 ; total toutes composantes ≈ 353,7 Mds ; prestations 2023 : 24,3 Mds = R1 ; R2 déclare en outre 8,6 Mds).
- **Vérification :** table `indicateurs_regime` (source ESS CNSSAP 2023/2024).
- **Gravité :** majeur.
- **Arbitrage proposé :** décider du périmètre (régime de base seul ou somme des composantes), corriger la note de source ou les valeurs en conséquence.
- **Note :** le ratio d'efficience 2023 de 63,3 % (Tableau 4.18) a été revérifié avec les valeurs exactes de la base : il est **correct** (41 841/66 105 = 63,29 %).

### A6. SESOPA — effectifs strictement identiques 2019–2026, y compris année non écoulée (2026)
- **Fichiers :** `03_chapitres/chapitre_4/4.6_deces_survie.md` (T4.12), Annexe B (B.6.3/B.6.7), Annexe C (C.1).
- **Constat :** 2 315 cotisants / 964+277+718 bénéficiaires reconduits chaque année, y compris 2026. DM-020 documente déjà l'anomalie.
- **Gravité :** majeur.
- **Arbitrage proposé :** confirmer auprès du SESOPA ; décider si la colonne 2026 doit être affichée ou remplacée par [N/D].

### A7. TRESOR (proxy budgétaire) — rupture 2022→2023 : 1 424 573 → 420 894, puis 713 896 en 2024
- **Fichier :** Annexe B (B.7.2), Annexe C (C.1, ligne « Pensions de retraite octroyé de la fonction publique »).
- **Constat :** rupture non expliquée dans la fiche ; estimation de la Fonction publique déjà marquée « provisoire, à confirmer ».
- **Gravité :** majeur.
- **Arbitrage proposé :** documenter la cause (changement de méthode d'estimation ?) ou marquer la série comme non comparable.

### A8. FSS — « Population cible (ville-province de Kinshasa) : 1618 millions » (Tableau B.5.3)
- **Statut : traité partiellement (2026-09-03).** La valeur absurde a été remplacée par [N/D] avec note explicative (« valeur transmise manifestement erronée, à confirmer auprès du FSS ; référence : ~17 M selon ONU WUP 2024 »). La valeur exacte reste à obtenir du FSS.
- **Fichier :** `04_annexes/annexe_B_fiches_institutionnelles.md`, ligne « Population cible ».
- **Constat initial :** valeur manifestement mal saisie. Aucune source dans le dépôt ne permet de trancher entre « 16–18 millions » (fourchette FSS) et une autre valeur. Référence externe : ONU WUP donne ≈ 17,0 M d'habitants pour l'agglomération de Kinshasa en 2024.
- **Gravité :** critique (valeur absurde en l'état) — corrigée en [N/D], valeur définitive à confirmer.
- **Arbitrage restant :** obtenir la valeur exacte du document FSS d'origine.

---

## B. Choix méthodologiques à trancher

### B1. ODD 1.3.1 — écart entre la valeur calculée (≈ 4,6 % en 2022) et la valeur publiée par l'OIT (5,2 % en 2022)
- **Statut : traité (2026-09-03).** Source ILOSTAT archivée (`06_sources/officielles_web/OIT_ILOSTAT_RDC_ODD131_couverture_2022.txt`, enregistrée dans les deux registres) ; paragraphe comparatif ajouté dans 4.9 et ligne « RDC (valeur publiée par l'OIT) » ajoutée au tableau de comparaison. Le choix de conserver le calcul national comme valeur principale reste à confirmer formellement (DM à acter).
- **Fichiers :** `03_chapitres/chapitre_4/4.9_odd_131.md`, Annexe C.
- **Vérification Internet :** ILOSTAT (`SDG_0131_SEX_SOC_RT_A`, ref_area=COD) publie **5,2 %** pour 2022 (source XA:6472) ; détail par branche : pension 1,0 ; AT 1,8 ; enfants 2,5 ; etc. — https://rplumber.ilo.org/data/indicator/?id=SDG_0131_SEX_SOC_RT_A&ref_area=COD&format=.csv
- **Constat :** le bulletin calcule à partir des ESS nationales (option documentée dans `indicateurs_odd_regles_calcul.md`) ; l'OIT publie une estimation différente. Aucune des deux n'est « fausse », mais l'écart doit être explicité.
- **Gravité :** majeur (comparabilité internationale).
- **Arbitrage proposé :** conserver le calcul national ET ajouter un encadré comparatif citant la valeur OIT publiée (5,2 % en 2022) avec explication de l'écart, dans 4.9 et dans la ligne RDC du tableau de comparaison régionale.

### B2. Seuil de pauvreté : 72 420 CDF/mois (2019–2023) puis 170 400 CDF/mois (2024)
- **Statut : traité partiellement (2026-09-03).** Note de rupture de série 2024 (passage Enquête 1-2-3 → ECVM 2024, conversion à confirmer auprès de l'INS) ajoutée aux notes ¹ des tableaux concernés dans 4.2, 4.4, 4.5 et 4.6. La confirmation INS de la conversion ×30 reste à obtenir.
- **Fichiers :** Tableaux 4.2, 4.7, 4.10 ; Annexe A.3.
- **Constat :** saut de +135 % non commenté dans les notes de tableau. Vraisemblablement passage de l'Enquête 1-2-3 à l'ECVM 2024 (INS), mais non documenté explicitement à côté des valeurs.
- **Gravité :** majeur (le ratio pension/seuil change de base en 2024).
- **Arbitrage proposé :** confirmer auprès de l'INS ; ajouter une note commune aux trois tableaux renvoyant à l'Annexe A.3 et signalant la rupture de série 2024.

### B3. Sous-indicateur « Enfants » : 0–14 ans (4.9) vs 0–17 ans (règles de calcul)
- **Statut : instruit (2026-09-03).** Vérification faite : le tableau de bord calcule effectivement avec la population 0–14 ans (`integrer_dashboard_bulletin.py`, mapping `ind_22_enfants` → `age-0-14`). Le libellé du tableau 4.9 est donc conforme à l'implémentation ; c'est `00_pilotage/indicateurs_odd_regles_calcul.md` (0–15/0–17) qui diverge. Décision à acter : conserver 0–14 (et amender la règle écrite) ou basculer le dénominateur sur 0–15/0–17 (et recalculer).
- **Fichiers :** `4.9_odd_131.md` (tableau : « Enfants 0–14 ans ») vs `00_pilotage/indicateurs_odd_regles_calcul.md` (dénominateur : population 0–17, option 0–15 WSPR).
- **Gravité :** majeur (le taux dépend directement du dénominateur retenu).
- **Arbitrage proposé :** identifier le dénominateur réellement utilisé par le tableau de bord (`integrer_dashboard_bulletin.py`) et aligner le libellé du tableau 4.9 sur celui-ci ; documenter le choix dans une DM.

### B4. Cantines scolaires PAM — « décision a été prise d'intégrer » non documentée
- **Statut : traité (2026-09-03).** Phrase reformulée dans la note du Tableau 2.4 : le programme est présenté dans la cartographie de la protection sociale des enfants mais demeure exclu de l'ODD 1.3.1 (prestation en nature), avec renvoi explicite à FICHE-002 et DM-011 — conforme au registre d'inclusion.
- **Fichier :** `03_chapitres/chapitre_2/2_1_cartographie_tableaux.md` (note du Tableau 2.4) vs `00_pilotage/registre_inclusion_programmes.md` (FICHE-002 : exclu de ODD 1.3.1, prestation en nature).
- **Gravité :** majeur (contradiction apparente entre cartographie et registre).
- **Arbitrage proposé :** soit référencer une décision méthodologique explicite (nouvelle DM), soit reformuler la note pour préciser que l'intégration vaut pour la cartographie (protection sociale des enfants au sens large) et non pour l'indicateur ODD 1.3.1.

### B5. MINAS présent dans le Tableau 2.4 (transferts) et le Tableau 2.5 (services — niveau 3)
- **Fichier :** `2_1_cartographie_tableaux.md`.
- **Gravité :** mineur à majeur (risque de double lecture).
- **Arbitrage proposé :** distinguer explicitement « programmes de transferts MINAS » (2.4) et « centres de promotion sociale MINAS » (2.5).

### B6. Terminologie « régimes octroyés » / « dispositif statutaire budgétaire »
- **Statut : traité (2026-09-03).** Entrée « Régime octroyé » ajoutée au glossaire (`05_references/glossaire.md`), rattachée explicitement à la catégorie « dispositif statutaire budgétaire », avec règle d'usage (conserver l'intitulé exact des sources).
- **Fichiers :** `4.2_vieillesse.md`, `4.3_age_actif.md`, Annexe C (« Pensions de retraite octroyé de la fonction publique »).
- **Constat :** « régime octroyé » n'est pas défini dans `05_references/glossaire.md` (qui définit « dispositif statutaire budgétaire »). Accord grammatical également à revoir (« retraite octroyé »).
- **Gravité :** mineur.
- **Arbitrage proposé :** ajouter une entrée au glossaire ou unifier vers « dispositif statutaire budgétaire ».

### B7. Millésime FMI WEO à préciser
- **Fichier :** `02_introduction_generale/0_2_contexte_economique_emploi.md` ; source `06_sources/officielles_web/FMI_WEO_RDC_croissance_pib_pib_habitant_2024.txt`.
- **Vérification Internet :** les valeurs (+6,4 ; +9,3 ; +8,5 ; +6,1) correspondent exactement au DataMapper FMI **courant** (édition 2025/2026), pas au WEO d'octobre 2024 (qui donnait 5,9 ; 8,8 ; 8,4 ; 4,7).
- **Gravité :** mineur (chiffres justes, millésime imprécis).
- **Arbitrage proposé :** renommer/mettre à jour le fichier source et la citation avec le millésime exact du WEO utilisé.

### B8. Ratification C102 — ajouter la date exacte
- **Statut : traité (2026-09-03).** « ratifiée en 1987 » précisé en « ratifiée le 3 avril 1987 » dans `1_2_approche_bit_oit.md` (NORMLEX).
- **Vérification Internet :** NORMLEX confirme : Parties V, VII, IX, X acceptées, en vigueur, ratification du **3 avril 1987**. Le bulletin dit « ratifiée en 1987 » : exact.
- **Gravité :** aucun problème — simple enrichissement possible (« le 3 avril 1987 »).

---

## C. Sections incomplètes (à signaler, pas à inventer)

| Élément | Fichier | État |
|---|---|---|
| Avant-propos | `01_pages_preliminaires/avant_propos.md` | non rédigé (nécessite signature institutionnelle) |
| Table des matières | `01_pages_preliminaires/table_des_matieres.md` | placeholder |
| Listes tableaux/figures/encadrés | `01_pages_preliminaires/listes_tableaux_figures_encadres.md` | « À compléter » |
| Annexes A1, A2, D, E, F, G | `04_annexes/` | structures initiales, à rédiger |
| Fiche FNPSS | Annexe B, section B.3 | vide ([N/D] partout) |
| Figures FIG_CH4_4.2 à 4.7 | notes internes des sections 4.2–4.8 | prévues, non générées (aucun fichier dans `08_figures/`) |
| Tableau 4.19 (dépenses/PIB) | `4.8_depenses_financement.md` | entièrement [N/D] |
| Comparaisons régionales ODD 1.3.1 | `4.9_odd_131.md` | [N/D] — valeurs WSPR à intégrer |
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
- Ratio d'efficience CNSSAP 2023 = 63,3 % : **exact** avec les valeurs non arrondies de la base.
- Annexe C, numérateur 2025 = 4 274 : cohérent (somme des seules composantes SESOPA disponibles en 2025 : 2 315 + 964 + 277 + 718) ; la note de lecture du tableau et le texte 4.9 expliquent le caractère partiel de 2025.
- Population Kinshasa ≈ 17,1 M (2024) : confirmée (ONU World Urbanization Prospects) — à sourcer « ONU DESA, WUP » et non « WPP » le cas échéant.
