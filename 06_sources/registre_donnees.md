# Registre des données et documents sources

<!-- NOTE_INTERNE
Objet du fichier :
Inventorier tous les documents et données disponibles dans 06_sources/, quelle que soit leur source.
Ce registre sert à la fois de mémoire de travail et de base pour la documentation des sources dans les sections et annexes du bulletin.

Règle de travail :
- Ajouter une ligne dans ce registre dès qu'un nouveau document est déposé dans l'un des sous-dossiers.
- Indiquer si le document a été converti en .txt pour lecture par les agents.
- Signaler le niveau de fiabilité de chaque source.
-->

## Organisation des sous-dossiers

| Sous-dossier | Type de source | Contenu attendu |
|---|---|---|
| `institutions/` | **Source primaire — transmission directe** | Données, rapports, statistiques, décrets, lois, règlements et tout document transmis directement par une institution nationale (CNSS, CNSSAP, FNPSS, SESOPA, ministères, etc.) |
| `officielles_web/` | **Source secondaire — officielle en ligne** | Documents officiels retrouvés sur le web : publications d'organisations internationales (OIT, Banque mondiale, INS, UNICEF…), journaux officiels, lois et décrets disponibles en ligne, bases de données publiques |
| `sources_incertaines/` | **Source à traiter avec prudence** | Données issues de sites moins fiables, estimations non documentées, articles de presse, sources à vérifier. À utiliser uniquement à titre indicatif et avec mention explicite dans le texte |

Chaque sous-dossier contient un sous-dossier `_texte/` pour les versions converties en `.txt`, lisibles par les agents.

---

## bulletins_rdc/ — Premier bulletin RDC (référence directe)

Ce dossier contient le premier Bulletin statistique de la protection sociale en RDC. C'est la **référence principale de continuité** pour le présent projet.

| Fichier | Chemin | Type | Description | Période | Converti | Statut |
|---|---|---|---|---|---|---|
| `Bulletin Statistique RDC- premiere édition.pdf` | `06_sources/bulletins_rdc/` | Bulletin officiel | Premier bulletin statistique de la protection sociale en RDC | 2023 | Oui (`_texte/`) | **Disponible** |

> Fichier texte lisible : `06_sources/bulletins_rdc/_texte/Bulletin Statistique RDC- premiere édition.txt`

---

## bulletins_comparaison/ — Bulletins d'autres pays (références de style)

Ces bulletins servent de **références de forme** : structure, mise en page, formulations types. Ne pas en reprendre le fond sans adaptation.

| Fichier | Chemin | Pays | Description | Converti | Statut |
|---|---|---|---|---|---|
| `2º Boletim de Estatísticas da Protecção Social de Angola.txt` | `06_sources/bulletins_comparaison/_texte/` | Angola | 2e bulletin statistique | Oui | **Disponible** |
| `Boletim de Estatísticas da Protecção Social de Angola.txt` | `06_sources/bulletins_comparaison/_texte/` | Angola | 1er bulletin statistique | Oui | **Disponible** |
| `Mozambique_1er_Boletim_Estatistico_Proteccao_Social_2019_v2.txt` | `06_sources/bulletins_comparaison/_texte/` | Mozambique | 1er bulletin 2019 — **doublon** de `Mozambique - 1er Boletim Estatistico da Proteccao Social, 2019.txt` (même contenu, ancien nom = identifiant de téléchargement `55986`) | Oui | **Doublon — à vérifier** |
| `Guinee_Bissau_1er_Boletim_Estatistico_PS_2023.txt` | `06_sources/bulletins_comparaison/_texte/` | Guinée-Bissau | 1er bulletin statistique 2023 | Oui | **Disponible** |
| `Jordan - Statistical Bulletin of Social Protection Indicators, 2020-2021.txt` | `06_sources/bulletins_comparaison/_texte/` | Jordanie | Bulletin indicateurs protection sociale 2020–2021 | Oui | **Disponible** |
| `Mozambique - 1er Boletim Estatistico da Proteccao Social, 2019.txt` | `06_sources/bulletins_comparaison/_texte/` | Mozambique | 1er bulletin 2019 | Oui | **Disponible** |
| `Mozambique - 2e Boletim Estatistico da Proteccao Social, 2020.txt` | `06_sources/bulletins_comparaison/_texte/` | Mozambique | 2e bulletin 2020 | Oui | **Disponible** |
| `Mozambique - 3e Boletim Estatistico da Proteccao Social, 2021.txt` | `06_sources/bulletins_comparaison/_texte/` | Mozambique | 3e bulletin 2021 | Oui | **Disponible** |
| `Sao-Tome-et-Principe - 1er Boletim Estatistico da Proteccao Social.txt` | `06_sources/bulletins_comparaison/_texte/` | Sao Tomé-et-Príncipe | 1er bulletin | Oui | **Disponible** |
| `Timor_Leste_1er_Boletim_Estatistico_PS_2017_2024.txt` | `06_sources/bulletins_comparaison/_texte/` | Timor-Leste | 1er bulletin 2017–2024 | Oui | **Disponible** |
| `Mozambique_VII_Boletim_Estatistico_Proteccao_Social_2025.txt` | `06_sources/bulletins_comparaison/_texte/` | Mozambique | **7e bulletin 2025** (données 2020–2024) — édition la plus récente, référence de style prioritaire pour le bulletin RDC | Oui | **Disponible** |

---

## ESS/ — Fichiers ESS du dernier bulletin (sources primaires institutionnelles)

Ces fichiers sont les tableaux ESS (format OIT) utilisés pour la production du premier Bulletin statistique de la protection sociale en RDC. Ils constituent des **sources primaires**. Ils serviront de base de comparaison et de continuité pour le deuxième bulletin.

> ⚠️ **Note sur la couverture temporelle :** La série CNSS couvre 2019–2022, la série CNSSAP couvre 2020–2022. Cette asymétrie doit être signalée dans les sections analytiques comparatives.
> ⚠️ **Note sur le fichier consolidé :** `ESS RDC tous régimes.xlsx` ne porte pas d'année dans son nom. La période couverte doit être vérifiée à l'ouverture du fichier et précisée dans les citations.

### ESS_CNSS/

| Fichier | Chemin | Institution | Type | Description | Période | Converti | Statut |
|---|---|---|---|---|---|---|---|
| `ESS CNSS 2019.xlsm` | `06_sources/ESS/ESS_CNSS/` | CNSS | Tableau ESS OIT | Données statistiques standardisées CNSS | 2019 | Oui (`_texte/`) | **Disponible** |
| `ESS CNSS 2020.xlsm` | `06_sources/ESS/ESS_CNSS/` | CNSS | Tableau ESS OIT | Données statistiques standardisées CNSS — fichier correct, intégré via PROC-008 le 2026-06-09 | 2020 | Oui (`_texte/ESS_CNSS_2020.txt`) | **Disponible** |
| `ESS CNSS 2020_ANOMALIE.xlsm` | `06_sources/ESS/ESS_CNSS/` | ? | Tableau ESS OIT | **⚠️ ANOMALIE** : nommé CNSS 2020 mais contenu CNSSAP (feuille "CNSAP Régime de base") — conservé à titre de traçabilité | 2020 (?) | Oui (`_texte/ESS_CNSS_2020_ANOMALIE.txt`) | **Archivé — ne pas citer** |
| `ESS CNSS 2021.xlsm` | `06_sources/ESS/ESS_CNSS/` | CNSS | Tableau ESS OIT | Données statistiques standardisées CNSS | 2021 | Oui (`_texte/`) | **Disponible** |
| `ESS CNSS 2022.xlsm` | `06_sources/ESS/ESS_CNSS/` | CNSS | Tableau ESS OIT | Données statistiques standardisées CNSS | 2022 | Oui (`_texte/`) | **Disponible** |

### ESS_CNSSAP/

| Fichier | Chemin | Institution | Type | Description | Période | Converti | Statut |
|---|---|---|---|---|---|---|---|
| `ESS CNSSAP 2020.xlsm` | `06_sources/ESS/ESS_CNSSAP/` | CNSSAP | Tableau ESS OIT | Données statistiques standardisées CNSSAP — 1 régime (pensions) — date interne affiche 2022 | 2020 | Oui (`_texte/`) | **Disponible** |
| `ESS CNSSAP 2021.xlsm` | `06_sources/ESS/ESS_CNSSAP/` | CNSSAP | Tableau ESS OIT | Données statistiques standardisées CNSSAP — 1 régime (pensions) — date interne affiche 2022 | 2021 | Oui (`_texte/`) | **Disponible** |
| `ESS CNSSAP 2022.xlsm` | `06_sources/ESS/ESS_CNSSAP/` | CNSSAP | Tableau ESS OIT | Données statistiques standardisées CNSSAP — 2 régimes (pensions + réforme du transfert) | 2022 | Oui (`_texte/`) | **Disponible** |

### ESS_RDC_tous_regimes/

| Fichier | Chemin | Institution | Type | Description | Période | Converti | Statut |
|---|---|---|---|---|---|---|---|
| `ESS RDC tous régimes.xlsx` | `06_sources/ESS/ESS_RDC_tous_regimes/` | Compilation multi-régimes | Tableau ESS OIT consolidé | 15 régimes : CNSS (3), CNSSAP (3), FSS (5), MESP, MINAS, MEPST, STEP/IDA | 2023 | Oui (`_texte/`) | **Disponible** |

---

## institutions/ — Documents transmis par les institutions

| Fichier | Chemin | Institution | Type | Description | Période | Converti | Statut |
|---|---|---|---|---|---|---|---|
| _(à déposer)_ | `06_sources/institutions/` | — | — | — | — | — | — |

---

## officielles_web/ — Documents officiels trouvés en ligne

| Fichier | Chemin | Source | Type | Description | Lien d'origine | Période | Converti | Statut |
|---|---|---|---|---|---|---|---|---|
| `ONU_WPP_2024_RDC_population.txt` | `06_sources/officielles_web/` | Division de la population des Nations Unies | Base de données / rapport | Estimations et projections de population pour la RDC : population totale, structure par âge, urbanisation, densité, taux de croissance | https://population.un.org/wpp/ | 2024 | Oui | **Disponible** |
| `UNFPA_World_Population_Dashboard_RDC_2024.txt` | `06_sources/officielles_web/` | UNFPA | Tableau de bord statistique | Part de la population 0–14 ans, indicateurs démographiques RDC | https://www.unfpa.org/data/world-population/CD | 2024 | Oui | **Disponible** |
| `BanqueMondiale_WDI_RDC_PIB_2023.txt` | `06_sources/officielles_web/` | Banque mondiale | Base de données WDI | PIB, RNB/habitant, pauvreté, emploi informel, dépenses santé, couverture protection sociale | https://data.worldbank.org/country/CD | 2023–2024 | Oui | **Disponible** |
| `FMI_WEO_RDC_croissance_pib_pib_habitant_2024.txt` | `06_sources/officielles_web/` | FMI | Base de données macroéconomique | Croissance du PIB réel (2021–2024) et série PIB/habitant WEO | https://www.imf.org/external/datamapper/ | 2021–2024 | Oui | **Disponible** |
| `INS_RDC_ECVM_pauvrete_inegalites_2024.txt` | `06_sources/officielles_web/` | INS-RDC | Publication/statistiques nationales | Niveau de pauvreté et inégalités (ECVM 2024 et tableau de bord INS) | https://ins.gouv.cd/statistiques/pauvrete | 2024 | Oui | **Disponible** |
| `OIT_ILOSTAT_RDC_emploi_secteur_chomage_2021_2024.txt` | `06_sources/officielles_web/` | OIT, ILOSTAT | Base de données travail | Emploi agricole (total et sexe) et chômage BIT (15+) pour la RDC | https://ilostat.ilo.org/data/ | 2021–2024 (informalité : 2020) | Oui | **Disponible** |
| `FAO_RDC_agriculture_emploi.txt` | `06_sources/officielles_web/` | FAO | Base de données / profil pays | Part de l'agriculture dans l'emploi (~68 %), sécurité alimentaire RDC | https://www.fao.org/faostat/ | 2022–2023 | Oui | **Disponible** |
| `BIT_World_Social_Protection_Report_2020-22.txt` | `06_sources/officielles_web/` | BIT / OIT | Rapport mondial | Définition de la protection sociale, indicateurs mondiaux de couverture, cadre ODD 1.3.1 | https://www.ilo.org/wcmsp5/groups/public/---dgreports/---dcomm/---publ/documents/publication/wcms_817572.pdf | 2021 (rapport 2020–22) | Oui | **Disponible** |
| `RDC_SNPS_2016.txt` | `06_sources/officielles_web/` | Gouvernement RDC — PNPS | Document de politique nationale | Stratégie nationale de la protection sociale (SNPS) : vision 2030, 3 axes stratégiques, cadre juridique | Transmission institutionnelle / Archives PNPS | 2016 | Oui | **Disponible** |
| `CNSS_RDC_branches_prestations.txt` | `06_sources/officielles_web/` | CNSS | Site officiel institutionnel | Branches couvertes par la CNSS : accidents du travail, prestations familiales/maternité, vieillesse/invalidité/survivants | https://www.cnss.cd/ | 2026 (consulté) | Oui | **Disponible** |
| `CNSSAP_RDC_branches_prestations.txt` | `06_sources/officielles_web/` | CNSSAP | Site officiel institutionnel | Branches couvertes par la CNSSAP : pensions, risques professionnels, prestations aux familles ; textes légaux fondateurs | https://www.cnssap.cd/qui-sommes-nous/ | 2026 (consulté) | Oui | **Disponible** |
| `FSS_RDC_produits_regimes.txt` | `06_sources/officielles_web/` | FSS | Site officiel institutionnel | Mission, 3 produits (Afia Bora, Kobota Ofele, Afia Bora Prime), statut opérationnel 2026, base légale (Loi 18/035 + Décret 22/13) | https://www.fss.cd/ | 2026 (consulté) | Oui | **Disponible** |
| `PAM_RDC_programmes_transferts_2026.txt` | `06_sources/officielles_web/` | PAM | Site officiel institutionnel | Transferts sans conditions (4 037 575 bénéficiaires 2021 ; 3 795 530 en 2022 ; 1,3 M dans l'Est depuis janv. 2026) ; cantines scolaires pilote (2023) ; nutrition | https://www.wfp.org/countries/democratic-republic-congo | 2021–2026 | Oui | **Disponible** |
| `RDC_programmes_non_contributifs_gouvernementaux.txt` | `06_sources/officielles_web/` | Gouvernement RDC + Banque mondiale | Synthesis / sources officielles | STEP Phase III (470 000 bénéficiaires transferts + 150 000 THIMO, clôture fév. 2024) ; gratuité enseignement primaire ; gratuité maternité ; PNPS | Sources multiples (Banque mondiale, MEPST, MINAS) | 2016–2024 | Oui | **Disponible** |
| `UNICEF_RDC_transferts_monetaires_2021-2022.txt` | `06_sources/officielles_web/` | UNICEF + FAO | Données programmes humanitaires | Cash+Nutrition Tanganyika 2021 (226 648 enfants) ; transferts UNICEF+FAO 2022 (4 000 ménages vulnérables) | Premier bulletin RDC (2023) citant données UNICEF/FAO | 2021–2022 | Oui | **Disponible** |

---

## sources_incertaines/ — Sources à utiliser avec prudence

| Fichier | Source | Type | Description | Lien d'origine | Niveau de fiabilité | Converti | Statut |
|---|---|---|---|---|---|---|---|
| _(à déposer)_ | — | — | — | — | — | — | — |

---

## Instructions pour les agents

- **Ne jamais citer une donnée sans indiquer son sous-dossier source et son niveau de fiabilité.**
- Les données de `institutions/` peuvent être citées comme sources primaires.
- Les données de `officielles_web/` peuvent être citées comme sources secondaires avec mention de l'organisation et de l'année.
- Les données de `sources_incertaines/` doivent être présentées avec une réserve explicite : *« Selon une estimation non confirmée… »* ou *« D'après une source à confirmer… »*
- Pour convertir un PDF en texte lisible : relancer `09_scripts/convertir_pdf_en_texte.py` après dépôt.
