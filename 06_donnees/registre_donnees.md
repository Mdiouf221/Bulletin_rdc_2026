# Registre des données et documents sources

<!-- NOTE_INTERNE
Objet du fichier :
Inventorier tous les documents et données disponibles dans 06_donnees/, quelle que soit leur source.
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

## institutions/ — Documents transmis par les institutions

| Fichier | Institution | Type | Description | Période | Converti | Statut |
|---|---|---|---|---|---|---|
| _(à déposer)_ | — | — | — | — | — | — |

---

## officielles_web/ — Documents officiels trouvés en ligne

| Fichier | Source | Type | Description | Lien d'origine | Période | Converti | Statut |
|---|---|---|---|---|---|---|---|
| `ONU_WPP_2024_RDC_population.txt` | Division de la population des Nations Unies | Base de données / rapport | Estimations et projections de population pour la RDC : population totale, structure par âge, urbanisation, densité, taux de croissance | https://population.un.org/wpp/ | 2024 | Oui (.txt) | **Disponible** |
| `UNFPA_World_Population_Dashboard_RDC_2024.txt` | UNFPA | Tableau de bord statistique | Part de la population 0–14 ans, indicateurs démographiques RDC | https://www.unfpa.org/data/world-population/CD | 2024 | Oui (.txt) | **Disponible** |
| `BanqueMondiale_WDI_RDC_PIB_2023.txt` | Banque mondiale | Base de données WDI | PIB, RNB/habitant, pauvreté, emploi informel, dépenses santé, couverture protection sociale | https://data.worldbank.org/country/CD | 2023–2024 | Oui (.txt) | **Disponible** |
| `FAO_RDC_agriculture_emploi.txt` | Organisation des Nations Unies pour l'alimentation et l'agriculture (FAO) | Base de données / profil pays | Part de l'agriculture dans l'emploi (~68 %), sécurité alimentaire RDC | https://www.fao.org/faostat/ | 2022–2023 | Oui (.txt) | **Disponible** |
| `BIT_World_Social_Protection_Report_2020-22.txt` | Bureau International du Travail (BIT / OIT) | Rapport mondial | Définition de la protection sociale, indicateurs mondiaux de couverture, cadre de référence ODD 1.3.1 | https://www.ilo.org/wcmsp5/groups/public/---dgreports/---dcomm/---publ/documents/publication/wcms_817572.pdf | 2021 (rapport 2020–22) | Oui (.txt) | **Disponible** |
| `RDC_SNPS_2016.txt` | Gouvernement de la RDC — PNPS | Document de politique nationale | Stratégie nationale de la protection sociale (SNPS) : vision 2030, 3 axes stratégiques, cadre juridique | Transmission institutionnelle / Archives PNPS | 2016 | Oui (.txt) | **Disponible** |
| `CNSS_RDC_branches_prestations.txt` | Caisse Nationale de Sécurité Sociale (CNSS) | Site officiel institutionnel | Branches couvertes par la CNSS : accidents du travail, prestations familiales/maternité, vieillesse/invalidité/survivants | https://www.cnss.cd/ | 2026 (consulté) | Oui (.txt) | **Disponible** |
| `CNSSAP_RDC_branches_prestations.txt` | Caisse Nationale de Sécurité Sociale des Agents Publics (CNSSAP) | Site officiel institutionnel | Branches couvertes par la CNSSAP : pensions, risques professionnels, prestations aux familles ; textes légaux fondateurs | https://www.cnssap.cd/qui-sommes-nous/ | 2026 (consulté) | Oui (.txt) | **Disponible** |
| `FSS_RDC_produits_regimes.txt` | Fonds de Solidarité de Santé (FSS) | Site officiel institutionnel | Mission, 3 produits (Afia Bora, Kobota Ofele, Afia Bora Prime), statut opérationnel 2026, base légale (Loi 18/035 + Décret 22/13) | https://www.fss.cd/ | 2026 (consulté) | Oui (.txt) | **Disponible** |
| `PAM_RDC_programmes_transferts_2026.txt` | Programme Alimentaire Mondial (PAM) | Site officiel institutionnel | Transferts sans conditions (4 037 575 bénéficiaires 2021 ; 3 795 530 en 2022 ; 1,3 M dans l'Est depuis janv. 2026) ; cantines scolaires pilote (2023) ; nutrition | https://www.wfp.org/countries/democratic-republic-congo | 2021–2026 | Oui (.txt) | **Disponible** |
| `RDC_programmes_non_contributifs_gouvernementaux.txt` | Gouvernement RDC + Banque mondiale | Synthesis / sources officielles | STEP Phase III (470 000 bénéficiaires transferts + 150 000 THIMO, clôture fév. 2024) ; gratuité enseignement primaire (instruction MEPST 2019 ; +4,4 M élèves 2023-24) ; gratuité maternité ; PNPS | Sources multiples (Banque mondiale, MEPST, MINAS) | 2016–2024 | Oui (.txt) | **Disponible** |
| `UNICEF_RDC_transferts_monetaires_2021-2022.txt` | UNICEF + FAO | Données programmes humanitaires | Cash+Nutrition Tanganyika 2021 (226 648 enfants) ; transferts UNICEF+FAO 2022 (4 000 ménages vulnérables) | Premier bulletin RDC (2023) citant données UNICEF/FAO | 2021–2022 | Oui (.txt) | **Disponible** |

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
