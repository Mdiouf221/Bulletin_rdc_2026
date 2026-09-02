# Annexe C — Détail des indicateurs de couverture

<!-- NOTE_INTERNE
Objectif de l'annexe :
Présenter individuellement chaque indicateur de couverture ODD 1.3.1 / BIT retenu dans le bulletin (indicateur global et sous-indicateurs par contingence sociale), l'un après l'autre, avec pour chacun : son évolution dans le temps (2019-2025), le détail du calcul de son numérateur (régimes et prestations inclus, par année) et la valeur de son dénominateur. Cette annexe est le pendant statistique, au niveau des indicateurs, de l'Annexe B (pendant institutionnel).

Positionnement éditorial :
Le chapitre 4 présente les indicateurs de couverture agrégés par contingence sociale, dans une lecture narrative. Cette annexe donne la traçabilité complète du calcul de chaque indicateur : quelle valeur est utilisée comme numérateur, quels régimes/prestations y contribuent année par année, et quel dénominateur est retenu. Elle reprend la structure de l'onglet « Indicateurs » du tableau de bord interactif.

Structure par indicateur (inspirée du Tableau 14 du premier bulletin RDC) :
- Encadré méthodologique (définition, numérateur, dénominateur, formule — cadre BIT/OIT)
- Tableau de synthèse unique 2019-2025, mêmes colonnes années sur toutes les lignes :
  - ligne « Indicateur de couverture (%) »
  - ligne « Numérateur (nombre de personnes) », suivie immédiatement de ses lignes de détail « Dont … » en italique (un régime/une prestation par ligne, « — » = non inclus ou absent cette année-là)
  - ligne « Dénominateur (population de référence) », dont le détail de construction par année est renvoyé en note de bas de page plutôt qu'affiché en clair
- Représentation graphique de l'indicateur (%) et du numérateur (nombre) — pas de graphique pour le dénominateur

Indicateurs couverts (ordre du sélecteur du tableau de bord) :
- ODD 1.3.1 — Indicateur global
- 2.2 Enfants ; 2.3 Maternité ; 2.4 Handicap/invalidité ; 2.5 AT/MP ; 2.6 Chômage ;
  2.7 Vieillesse ; 2.8 Vulnérables/assistance ; 2.9 Cotisants actifs retraite

Les sous-indicateurs 2.6 (chômage) et 2.8 (vulnérables) sont documentés (définition, numérateur, dénominateur) mais non calculés : aucune donnée ESS ne permet actuellement de les quantifier (absence de régime d'assurance chômage opérationnel identifié ; absence de mesure individualisable de la population vulnérable et de ses bénéficiaires d'assistance sociale). Voir Annexe D pour les dispositifs hors périmètre OIT néanmoins recensés.

Fichiers associés :
- annexe_B_fiches_institutionnelles.md : détail institution par institution (pendant institutionnel de cette annexe)
- annexe_E_definitions_indicateurs.md : définitions détaillées des indicateurs
- 00_pilotage/indicateurs_odd_regles_calcul.md : règles de calcul détaillées

Statut : structure initiale
-->

## Texte rédigé

<!-- NOTE_INTERNE
Le contenu de cette section (tableaux, graphiques, détail des numérateurs) est généré
automatiquement à partir de la base ESS et des décisions d'inclusion/exclusion du tableau
de bord (10_output/dashboard_settings.json), via `py 09_scripts/generer_annexe_c_visuels.py`
— sans navigateur, sans saisie manuelle — et se régénère à chaque mise à jour des données
ou des décisions (`rafraichir_ess.py`, puis édition des décisions dans l'onglet « Indicateurs »
du tableau de bord).

Ne pas modifier manuellement le contenu situé entre les marqueurs AUTO_GENERE : il sera
écrasé au prochain lancement du script. Le texte d'introduction ci-dessous, hors marqueurs,
peut être rédigé librement.
-->

Cette annexe présente, indicateur par indicateur, la construction complète des mesures de couverture effective du bulletin : la valeur de l'indicateur dans le temps, le détail des régimes et prestations qui composent son numérateur année par année, et la population de référence retenue comme dénominateur. Elle reprend la logique de l'onglet « Indicateurs » du tableau de bord interactif, où les décisions d'inclusion et d'exclusion de chaque régime ou prestation peuvent être consultées et ajustées.

Pour rester lisible malgré la densité des données, cette annexe désigne les institutions par leur sigle (voir la [Liste des sigles et acronymes](../01_pages_preliminaires/sigles_acronymes.md)) et regroupe le détail du numérateur par régime : chaque ligne « Dont … » introduit un régime contributeur, ses prestations étant listées juste en dessous sous la forme « ↳ … », sans répéter l'institution ni le régime déjà indiqués. Le détail de construction du dénominateur (source retenue par année) est renvoyé en note de bas de page et factorisé par plage d'années partageant la même source.

---

<!-- AUTO_GENERE:global_131:DEBUT -->
## C.1 — ODD 1.3.1 — Global

> **Définition (BIT/OIT).** Proportion de la population couverte par au moins une prestation en espèces de protection sociale ou cotisant activement à au moins un régime de sécurité sociale.
>
> **Numérateur.** Nombre de personnes recevant au moins une prestation en espèces de protection sociale, hors soins de santé, ou cotisant activement à au moins un régime de sécurité sociale, sans double comptage.
>
> **Dénominateur.** Population totale.
>
> **Formule.** Population couverte par au moins une prestation ou cotisant activement ÷ population totale × 100.


<p class="table-caption"><strong>Tableau C.1</strong> — Indicateur de couverture, numérateur et dénominateur — ODD 1.3.1 — Global (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **4,1** | **3,7** | **3,9** | **3,8** | **1,2** | **1,2** | **[N/D]** | **0,0** |
| **Numérateur (nombre de personnes)** | **3,815,223** | **3,513,666** | **3,869,318** | **3,915,212** | **1,253,085** | **1,258,412** | **[N/D]** | **0** |
| *Dont Branche des Prestations aux familles (CNSS, cotisants)* | *676,179* | *508,708* | *591,130* | *613,761* | *—* | *—* | *[N/D]* | *—* |
| *↳ allocation de maternité (bénéf.)* | *—* | *108* | *167* | *414* | *—* | *—* | *[N/D]* | *—* |
| *↳ allocations familiales (bénéf.)* | *267,445* | *294,346* | *396,399* | *356,423* | *—* | *—* | *[N/D]* | *—* |
| *↳ allocations prénatales (bénéf.)* | *—* | *162* | *184* | *532* | *—* | *—* | *[N/D]* | *—* |
| *↳ indemnité journalière de maternité (bénéf.)* | *—* | *2* | *2* | *17* | *—* | *—* | *[N/D]* | *—* |
| *Dont Branche des Risques Professionnels (CNSS, cotisants)* | *676,179* | *508,708* | *591,130* | *613,761* | *—* | *—* | *[N/D]* | *—* |
| *↳ Rente ou allocation d'incapacité (bénéf.)* | *1,082* | *1,020* | *955* | *1,053* | *—* | *—* | *[N/D]* | *—* |
| *↳ allocation des frais funéraires (bénéf.)* | *1,766* | *589* | *849* | *533* | *—* | *—* | *[N/D]* | *—* |
| *↳ frais de réadaptation fonctionnelle  ou de reclassement de la victime (bénéf.)* | *—* | *—* | *—* | *677* | *—* | *—* | *[N/D]* | *—* |
| *↳ rentes de survivants (bénéf.)* | *1,476* | *1,608* | *1,845* | *1,781* | *—* | *—* | *[N/D]* | *—* |
| *Dont Branche des Pensions (CNSS, cotisants)* | *676,179* | *508,708* | *591,130* | *613,761* | *—* | *—* | *[N/D]* | *—* |
| *↳ Pension d'invalidité (bénéf.)* | *883* | *568* | *524* | *728* | *—* | *—* | *[N/D]* | *—* |
| *↳ Pension de retraite (bénéf.)* | *38,641* | *39,465* | *42,407* | *44,094* | *—* | *—* | *[N/D]* | *—* |
| *↳ Pension de retraite anticipée (bénéf.)* | *—* | *78* | *272* | *1,235* | *—* | *—* | *[N/D]* | *—* |
| *↳ Pension des survivants (bénéf.)* | *24,725* | *25,720* | *28,355* | *31,524* | *—* | *—* | *[N/D]* | *—* |
| *Dont Régime de base (CNSSAP, cotisants)* | *—* | *172,304* | *190,545* | *198,399* | *1,004,106* | *1,013,104* | *[N/D]* | *—* |
| *↳ Pension de retraite (bénéf.)* | *—* | *814* | *780* | *1,329* | *6,238* | *10,485* | *[N/D]* | *—* |
| *↳ Rente de survie au conjoint survivants (bénéf.)* | *—* | *50* | *114* | *184* | *738* | *2,378* | *[N/D]* | *—* |
| *↳ Rente de survie pour l'orphelin (bénéf.)* | *—* | *40* | *103* | *187* | *738* | *2,378* | *[N/D]* | *—* |
| *Dont Pension de retraite — Réforme du transfert (CNSSAP, bénéf.)* | *—* | *—* | *—* | *3,653* | *4,522* | *2,510* | *[N/D]* | *—* |
| *↳ Rente de survie au conjoint survivants (bénéf.)* | *—* | *—* | *—* | *6,044* | *8,922* | *7,508* | *[N/D]* | *—* |
| *↳ Rente de survie pour l'orphelin (bénéf.)* | *—* | *—* | *—* | *549* | *8,922* | *720* | *[N/D]* | *—* |
| *Dont Prestations en cas d'accident du travail — Risques professionnels (CNSSAP, bénéf.)* | *—* | *—* | *—* | *—* | *—* | *2* | *[N/D]* | *—* |
| *Dont Régime Complémentaire (CNSSAP, cotisants)* | *—* | *—* | *—* | *—* | *218,899* | *219,327* | *[N/D]* | *—* |
| *Dont Pensions de retraite octroyé de la fonction publique (estimation) (Trésor, cotisants)* | *1,450,668* | *1,450,668* | *1,432,427* | *1,424,573* | *—* | *—* | *[N/D]* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population totale ; 2026 : Saisie manuelle : valeur manquante pour 2026.</span> | 92,947,442 | 95,989,998 | 99,148,932 | 102,396,968 | 105,789,731 | 109,276,265 | [N/D] | 116,452,162 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.1</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — ODD 1.3.1 — Global (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_global_131_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_global_131_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:global_131:FIN -->

---

<!-- AUTO_GENERE:ind_22_enfants:DEBUT -->
## C.2 — 2.2 Enfants

> **Définition (BIT/OIT).** Proportion d'enfants bénéficiant d'au moins une prestation en espèces de protection sociale destinée aux enfants ou aux familles.
>
> **Numérateur.** Nombre d'enfants recevant au moins une prestation en espèces pour enfants ou famille.
>
> **Dénominateur.** Population totale des enfants dans la tranche d'âge retenue.
>
> **Formule.** Enfants bénéficiaires ÷ population totale des enfants × 100.


<p class="table-caption"><strong>Tableau C.2</strong> — Indicateur de couverture, numérateur et dénominateur — 2.2 Enfants (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **0,6** | **0,7** | **0,9** | **0,8** | **0,0** | **0,0** | **[N/D]** | **0,0** |
| **Numérateur (nombre de personnes)** | **267,445** | **294,386** | **396,502** | **357,159** | **9,660** | **3,098** | **[N/D]** | **0** |
| *Dont allocations familiales — Prestations familiales (CNSS, bénéf.)* | *267,445* | *294,346* | *396,399* | *356,423* | *—* | *—* | *[N/D]* | *—* |
| *Dont Rente de survie pour l'orphelin — Régime de base (CNSSAP, bénéf.)* | *—* | *40* | *103* | *187* | *738* | *2,378* | *[N/D]* | *—* |
| *Dont Rente de survie pour l'orphelin — Réforme du transfert (CNSSAP, bénéf.)* | *—* | *—* | *—* | *549* | *8,922* | *720* | *[N/D]* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population 0–14 ans, calculee = % INS x population totale INS.</span> | 42,737,234 | 44,203,394 | 45,697,743 | 47,215,242 | 48,758,487 | 50,299,865 | [N/D] | 53,371,488 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.2</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.2 Enfants (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_22_enfants_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_22_enfants_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_22_enfants:FIN -->

---

<!-- AUTO_GENERE:ind_23_maternite:DEBUT -->
## C.3 — 2.3 Maternité

> **Définition (BIT/OIT).** Proportion de femmes ayant accouché qui reçoivent une prestation en espèces de maternité.
>
> **Numérateur.** Nombre de femmes ayant accouché et percevant une indemnité ou une allocation de maternité en espèces.
>
> **Dénominateur.** Nombre total de femmes ayant accouché au cours de la même année, estimé directement ou à partir des naissances vivantes corrigées des naissances multiples.
>
> **Formule.** Femmes bénéficiaires d'une prestation de maternité ÷ femmes ayant accouché × 100.


<p class="table-caption"><strong>Tableau C.3</strong> — Indicateur de couverture, numérateur et dénominateur — 2.3 Maternité (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **[N/D]** | **0,0** |
| **Numérateur (nombre de personnes)** | **0** | **110** | **169** | **431** | **0** | **0** | **[N/D]** | **0** |
| *Dont allocation de maternité — Prestations familiales (CNSS, bénéf.)* | *—* | *108* | *167* | *414* | *—* | *—* | *[N/D]* | *—* |
| *↳ indemnité journalière de maternité (bénéf.)* | *—* | *2* | *2* | *17* | *—* | *—* | *[N/D]* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019 : Base locale ONU WPP 2024 — femmes 15–49 (B-MA) ; 2020 : Saisie manuelle - INS/RDC, canevas de collecte 2026 : nombre de naissances vivantes (2020), utilise comme approximation du nombre de femmes ayant accouche ; 2021–2024 : Base locale ONU WPP 2024 — femmes 15–49 (B-MA).</span> | 3,926,761 | 719,335 | 4,127,847 | 4,230,812 | 4,337,283 | 4,435,281 | [N/D] | 4,602,608 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.3</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.3 Maternité (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_23_maternite_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_23_maternite_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_23_maternite:FIN -->

---

<!-- AUTO_GENERE:ind_24_handicap:DEBUT -->
## C.4 — 2.4 Handicap / invalidité

> **Définition (BIT/OIT).** Proportion de personnes en situation de handicap grave qui reçoivent une prestation en espèces d'invalidité.
>
> **Numérateur.** Nombre de personnes en situation de handicap grave percevant une prestation en espèces d'invalidité.
>
> **Dénominateur.** Population estimée de personnes en situation de handicap grave.
>
> **Formule.** Bénéficiaires de prestations d'invalidité ÷ population en situation de handicap grave × 100.


<p class="table-caption"><strong>Tableau C.4</strong> — Indicateur de couverture, numérateur et dénominateur — 2.4 Handicap / invalidité (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **[N/D]** | **0,0** |
| **Numérateur (nombre de personnes)** | **1,965** | **1,588** | **1,479** | **1,781** | **0** | **0** | **[N/D]** | **0** |
| *Dont Rente ou allocation d'incapacité — Risques professionnels (CNSS, bénéf.)* | *1,082* | *1,020* | *955* | *1,053* | *—* | *—* | *[N/D]* | *—* |
| *Dont Pension d'invalidité — Pension (CNSS, bénéf.)* | *883* | *568* | *524* | *728* | *—* | *—* | *[N/D]* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Base locale — population × prévalence 15 % (proxy).</span> | 13,942,116 | 14,398,500 | 14,872,340 | 15,359,545 | 15,868,460 | 16,391,440 | [N/D] | 17,467,824 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.4</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.4 Handicap / invalidité (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_24_handicap_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_24_handicap_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_24_handicap:FIN -->

---

<!-- AUTO_GENERE:ind_25_atmp:DEBUT -->
## C.5 — 2.5 AT/MP

> **Définition (BIT/OIT).** Proportion de la main-d'œuvre couverte par un régime assurant une protection en cas d'accident du travail ou de maladie professionnelle.
>
> **Numérateur.** Nombre de personnes appartenant à la main-d'œuvre et couvertes en cas d'accident du travail ou de maladie professionnelle.
>
> **Dénominateur.** Main-d'œuvre totale, composée des personnes en emploi et des personnes au chômage.
>
> **Formule.** Main-d'œuvre couverte contre les accidents du travail et maladies professionnelles ÷ main-d'œuvre totale × 100.


<p class="table-caption"><strong>Tableau C.5</strong> — Indicateur de couverture, numérateur et dénominateur — 2.5 AT/MP (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **1,4** | **1,0** | **1,1** | **1,1** | **0,0** | **0,0** | **[N/D]** | **0,0** |
| **Numérateur (nombre de personnes)** | **678,737** | **511,336** | **593,930** | **616,595** | **0** | **0** | **[N/D]** | **0** |
| *Dont Branche des Risques Professionnels (CNSS, cotisants)* | *676,179* | *508,708* | *591,130* | *613,761* | *—* | *—* | *[N/D]* | *—* |
| *↳ Rente ou allocation d'incapacité (bénéf.)* | *1,082* | *1,020* | *955* | *1,053* | *—* | *—* | *[N/D]* | *—* |
| *↳ rentes de survivants (bénéf.)* | *1,476* | *1,608* | *1,845* | *1,781* | *—* | *—* | *[N/D]* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population active 15 ans et plus, calculee = % INS x population totale INS.</span> | 50,191,619 | 51,642,619 | 53,143,828 | 54,679,981 | 56,280,137 | 57,916,420 | [N/D] | 41,199,460 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.5</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.5 AT/MP (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_25_atmp_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_25_atmp_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_25_atmp:FIN -->

---

<!-- AUTO_GENERE:ind_26_chomage:DEBUT -->
## C.6 — 2.6 Chômage

> **Définition (BIT/OIT).** Proportion de personnes au chômage qui reçoivent une prestation en espèces de chômage.
>
> **Numérateur.** Nombre de personnes au chômage percevant effectivement une allocation de chômage en espèces.
>
> **Dénominateur.** Nombre total de personnes au chômage selon la définition du BIT.
>
> **Formule.** Chômeurs indemnisés ÷ nombre total de chômeurs × 100.


*Aucun régime d'assurance chômage opérationnel n'est identifié dans les ESS disponibles : ni numérateur ni dénominateur ne peuvent être calculés à ce stade.*

<!-- AUTO_GENERE:ind_26_chomage:FIN -->

---

<!-- AUTO_GENERE:ind_27_vieillesse:DEBUT -->
## C.7 — 2.7 Vieillesse

> **Définition (BIT/OIT).** Proportion de personnes ayant atteint l'âge légal de la retraite qui reçoivent une prestation de vieillesse contributive ou non contributive.
>
> **Numérateur.** Nombre de personnes ayant atteint l'âge légal de la retraite et percevant effectivement une pension ou une prestation de vieillesse.
>
> **Dénominateur.** Population totale ayant atteint l'âge légal de la retraite, lequel peut différer selon le sexe ou le régime.
>
> **Formule.** Bénéficiaires de prestations de vieillesse ÷ population ayant atteint l'âge légal de la retraite × 100.


<p class="table-caption"><strong>Tableau C.7</strong> — Indicateur de couverture, numérateur et dénominateur — 2.7 Vieillesse (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **1,0** | **1,0** | **1,0** | **1,1** | **0,2** | **0,2** | **[N/D]** | **[N/D]** |
| **Numérateur (nombre de personnes)** | **38,641** | **40,357** | **43,459** | **50,311** | **10,760** | **12,995** | **[N/D]** | **0** |
| *Dont Pension de retraite — Pension (CNSS, bénéf.)* | *38,641* | *39,465* | *42,407* | *44,094* | *—* | *—* | *[N/D]* | *—* |
| *↳ Pension de retraite anticipée (bénéf.)* | *—* | *78* | *272* | *1,235* | *—* | *—* | *[N/D]* | *—* |
| *Dont Pension de retraite — Régime de base (CNSSAP, bénéf.)* | *—* | *814* | *780* | *1,329* | *6,238* | *10,485* | *[N/D]* | *—* |
| *Dont Pension de retraite — Réforme du transfert (CNSSAP, bénéf.)* | *—* | *—* | *—* | *3,653* | *4,522* | *2,510* | *[N/D]* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population 60 ans et plus (age legal CNSSAP), calculee = % INS x population totale INS.</span> | 3,996,740 | 4,223,560 | 4,461,702 | 4,710,261 | 4,972,117 | 5,245,261 | [N/D] | [N/D] |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.7</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.7 Vieillesse (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_27_vieillesse_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_27_vieillesse_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_27_vieillesse:FIN -->

---

<!-- AUTO_GENERE:ind_28_vulnerables:DEBUT -->
## C.8 — 2.8 Vulnérables / assistance

> **Définition (BIT/OIT).** Proportion de personnes vulnérables qui reçoivent une prestation d'assistance sociale en espèces.
>
> **Numérateur.** Nombre de personnes vulnérables percevant une prestation d'assistance sociale en espèces.
>
> **Dénominateur.** Population vulnérable, obtenue en retranchant de la population totale les personnes en âge de travailler cotisant à une assurance sociale ou percevant une prestation contributive, ainsi que les personnes d'âge légal de la retraite percevant une prestation contributive.
>
> **Formule.** Personnes vulnérables bénéficiaires d'une prestation d'assistance sociale ÷ population vulnérable × 100.


*La population vulnérable et ses bénéficiaires d'assistance sociale ne font l'objet d'aucune mesure individualisable dans les sources actuellement disponibles : cet indicateur n'est pas calculé dans la présente édition.*

<!-- AUTO_GENERE:ind_28_vulnerables:FIN -->

---

<!-- AUTO_GENERE:ind_29_cotisants:DEBUT -->
## C.9 — 2.9 Cotisants actifs retraite

> **Définition (BIT/OIT).** Proportion de la main-d'œuvre qui cotise activement à un régime de retraite contributif.
>
> **Numérateur.** Nombre de personnes cotisant activement à un régime de retraite contributif.
>
> **Dénominateur.** Main-d'œuvre totale.
>
> **Formule.** Cotisants actifs à un régime de retraite ÷ main-d'œuvre totale × 100.


<p class="table-caption"><strong>Tableau C.9</strong> — Indicateur de couverture, numérateur et dénominateur — 2.9 Cotisants actifs retraite (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **4,5** | **4,4** | **4,4** | **4,3** | **2,3** | **2,3** | **[N/D]** | **0,0** |
| **Numérateur (nombre de personnes)** | **2,126,847** | **2,131,680** | **2,214,102** | **2,236,733** | **1,223,005** | **1,232,431** | **[N/D]** | **0** |
| *Dont Branche des Pensions (CNSS, cotisants)* | *676,179* | *508,708* | *591,130* | *613,761* | *—* | *—* | *[N/D]* | *—* |
| *Dont Régime de base (CNSSAP, cotisants)* | *—* | *172,304* | *190,545* | *198,399* | *1,004,106* | *1,013,104* | *[N/D]* | *—* |
| *Dont Régime Complémentaire (CNSSAP, cotisants)* | *—* | *—* | *—* | *—* | *218,899* | *219,327* | *[N/D]* | *—* |
| *Dont Pensions de retraite octroyé de la fonction publique (estimation) (Trésor, cotisants)* | *1,450,668* | *1,450,668* | *1,432,427* | *1,424,573* | *—* | *—* | *[N/D]* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : approximation calculee a partir des donnees INS : population active 15 ans et plus moins population 65 ans et plus.</span> | 47,589,090 | 48,858,909 | 50,169,360 | 51,505,675 | 52,894,866 | 54,310,304 | [N/D] | 59,478,100 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.9</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.9 Cotisants actifs retraite (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_29_cotisants_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_29_cotisants_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_29_cotisants:FIN -->
