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

**Lecture du numérateur et règle de dédoublonnage.** Un même régime peut apparaître sous plusieurs branches lorsque ses cotisants relèvent simultanément de plusieurs risques couverts (par exemple, les cotisants de la CNSS financent à la fois la branche des pensions, celle des risques professionnels et celle des prestations familiales). Dans ce cas, les lignes « Dont … » répètent le même effectif de cotisants sous chaque branche à laquelle il contribue, afin de montrer la composition complète du calcul. Ces lignes ne s'additionnent donc pas entre elles : chaque cotisant n'est comptabilisé qu'une seule fois dans la ligne « Numérateur » de l'indicateur global, quel que soit le nombre de branches auxquelles il est rattaché. Le numérateur global correspond à l'union dédupliquée des personnes couvertes par au moins une des composantes retenues, et non à la somme brute des lignes « Dont … ».

**Cas particulier de la protection budgétaire hors CNSSAP.** Le code « TRESOR » utilisé dans la base ne désigne pas une institution. Il représente, à titre d'hypothèse de travail, la part estimée des agents publics hors CNSSAP considérée comme relevant d'un dispositif non contributif financé par allocation budgétaire. Les effectifs associés sont des estimations de personnes potentiellement couvertes et non des cotisants.

---

<!-- AUTO_GENERE:global_131:DEBUT -->
## C.1 — ODD 1.3.1 — Global

**Définition (BIT/OIT).** Proportion de la population couverte par au moins une prestation en espèces de protection sociale ou cotisant activement à au moins un régime de sécurité sociale.

**Numérateur.** Nombre de personnes recevant au moins une prestation en espèces de protection sociale, hors soins de santé, ou cotisant activement à au moins un régime de sécurité sociale, sans double comptage.

**Dénominateur.** Population totale.

**Formule.** Population couverte par au moins une prestation ou cotisant activement ÷ population totale × 100.


<p class="table-caption"><strong>Tableau C.1</strong> — Indicateur de couverture, numérateur et dénominateur — ODD 1.3.1 — Global (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **4,7** | **4,3** | **4,8** | **4,6** | **4,5** | **4,9** | **0,0** | **[N/D]** |
| **Numérateur (nombre de personnes)** | **4,399,853** | **4,156,671** | **4,733,778** | **4,692,924** | **4,748,489** | **5,402,045** | **4,274** | **[N/D]** |
| *Dont Branche des Prestations aux familles (CNSS, cotisants)* | *676,179* | *508,708* | *591,130* | *613,761* | *578,272* | *800,486* | *—* | *—* |
| *↳ allocation de maternité (bénéf.)* | *—* | *108* | *167* | *414* | *167* | *390* | *—* | *—* |
| *↳ allocations familiales (bénéf.)* | *847,801* | *933,077* | *1,256,585* | *1,129,861* | *1,256,585* | *911,125* | *—* | *—* |
| *↳ allocations prénatales (bénéf.)* | *—* | *162* | *184* | *532* | *531* | *365* | *—* | *—* |
| *↳ indemnité journalière de maternité (bénéf.)* | *—* | *2* | *2* | *17* | *2* | *71* | *—* | *—* |
| *Dont Branche des Risques Professionnels (CNSS, cotisants)* | *676,179* | *508,708* | *591,130* | *613,761* | *578,272* | *800,486* | *—* | *—* |
| *↳ Rente ou allocation d'incapacité (bénéf.)* | *1,082* | *1,020* | *955* | *1,053* | *1,020* | *2,853* | *—* | *—* |
| *↳ allocation des frais funéraires (bénéf.)* | *1,766* | *589* | *849* | *533* | *—* | *2,853* | *—* | *—* |
| *↳ assistance médicale, chirurgicale et soins dentaires (bénéf.)* | *—* | *—* | *—* | *—* | *—* | *2,853* | *—* | *—* |
| *↳ fourniture des produits pharmaceutiques (bénéf.)* | *—* | *—* | *—* | *—* | *—* | *2,853* | *—* | *—* |
| *↳ fourniture, entretien et renouvellement des appareils prophèse et d'orthopédie (bénéf.)* | *—* | *—* | *—* | *—* | *—* | *2,853* | *—* | *—* |
| *↳ frais de réadaptation fonctionnelle  ou de reclassement de la victime (bénéf.)* | *—* | *—* | *—* | *677* | *—* | *2,853* | *—* | *—* |
| *↳ indemnité journalière (bénéf.)* | *—* | *—* | *—* | *—* | *—* | *2,853* | *—* | *—* |
| *↳ lunettes, soins infirmiers et visites à domicile (bénéf.)* | *—* | *—* | *—* | *—* | *—* | *2,853* | *—* | *—* |
| *↳ rentes de survivants (bénéf.)* | *1,476* | *1,608* | *1,845* | *1,781* | *1,608* | *2,853* | *—* | *—* |
| *↳ réadaptation fonctionnelle ou reclassement de la victime. (bénéf.)* | *—* | *—* | *—* | *—* | *—* | *2,853* | *—* | *—* |
| *↳ transport de la victime (bénéf.)* | *—* | *—* | *—* | *—* | *—* | *2,853* | *—* | *—* |
| *Dont Branche des Pensions (CNSS, cotisants)* | *676,179* | *508,708* | *591,130* | *613,761* | *578,272* | *800,486* | *—* | *—* |
| *↳ Pension d'invalidité (bénéf.)* | *883* | *568* | *524* | *728* | *432* | *439* | *—* | *—* |
| *↳ Pension de retraite (bénéf.)* | *38,641* | *39,465* | *42,407* | *44,094* | *43,601* | *44,937* | *—* | *—* |
| *↳ Pension de retraite anticipée (bénéf.)* | *—* | *78* | *272* | *1,235* | *696* | *940* | *—* | *—* |
| *↳ Pension des survivants (bénéf.)* | *24,725* | *25,720* | *28,355* | *31,524* | *30,778* | *33,506* | *—* | *—* |
| *↳ frais funéraires (bénéf.)* | *—* | *—* | *—* | *—* | *—* | *849* | *—* | *—* |
| *Dont Régime de base (CNSSAP, cotisants)* | *—* | *172,304* | *190,545* | *198,399* | *1,004,106* | *1,013,104* | *—* | *—* |
| *↳ Pension de retraite (bénéf.)* | *—* | *814* | *780* | *1,329* | *6,238* | *10,485* | *—* | *—* |
| *↳ Rente de survie au conjoint survivants (bénéf.)* | *—* | *50* | *114* | *184* | *738* | *2,378* | *—* | *—* |
| *↳ Rente de survie pour l'orphelin (bénéf.)* | *—* | *40* | *103* | *187* | *738* | *2,378* | *—* | *—* |
| *Dont Pension de retraite — Réforme du transfert (CNSSAP, bénéf.)* | *—* | *—* | *—* | *3,653* | *4,522* | *2,510* | *—* | *—* |
| *↳ Rente de survie au conjoint survivants (bénéf.)* | *—* | *—* | *—* | *6,044* | *8,922* | *7,508* | *—* | *—* |
| *↳ Rente de survie pour l'orphelin (bénéf.)* | *—* | *—* | *—* | *549* | *8,922* | *720* | *—* | *—* |
| *Dont Prestations en cas d'accident du travail — Risques professionnels (CNSSAP, bénéf.)* | *—* | *—* | *—* | *—* | *—* | *2* | *—* | *—* |
| *Dont Régime Complémentaire (CNSSAP, cotisants)* | *—* | *—* | *—* | *—* | *218,899* | *219,327* | *—* | *—* |
| *Dont Branche des pensions  de retraite et de réversion (SESOPA, cotisants)* | *2,315* | *2,315* | *2,315* | *2,315* | *2,315* | *2,315* | *2,315* | *—* |
| *↳ Pension de retraite contributive (bénéf.)* | *964* | *964* | *964* | *964* | *964* | *964* | *964* | *—* |
| *↳ Pension de retraite des anciens parlementaires non cotisants prise en charge par le Trésor public (bénéf.)* | *277* | *277* | *277* | *277* | *277* | *277* | *277* | *—* |
| *↳ Pension de réversion (rente viagère du conjoint survivant) (bénéf.)* | *718* | *718* | *718* | *718* | *718* | *718* | *718* | *—* |
| *Dont Pensions de retraite octroyé de la fonction publique (estimation) (proxy budgétaire hors CNSSAP, personnes potentiellement couvertes estimées)* | *1,450,668* | *1,450,668* | *1,432,427* | *1,424,573* | *420,894* | *713,896* | *—* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population totale ; 2025 : src-unwpp-2024jul-rev [var-c-popsx / sex-t / age-0+] — population 0+ ; 2026 : Saisie manuelle : valeur manquante pour 2026.</span> | 92,947,442 | 95,989,998 | 99,148,932 | 102,396,968 | 105,789,731 | 109,276,265 | 112,832,473 | 116,452,162 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.1</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — ODD 1.3.1 — Global (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_global_131_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_global_131_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:global_131:FIN -->

---

<!-- AUTO_GENERE:ind_22_enfants:DEBUT -->
## C.2 — 2.2 Enfants

**Définition (BIT/OIT).** Proportion d'enfants bénéficiant d'au moins une prestation en espèces de protection sociale destinée aux enfants ou aux familles.

**Numérateur.** Nombre d'enfants recevant au moins une prestation en espèces pour enfants ou famille.

**Dénominateur.** Population totale des enfants dans la tranche d'âge retenue.

**Formule.** Enfants bénéficiaires ÷ population totale des enfants × 100.


<p class="table-caption"><strong>Tableau C.2</strong> — Indicateur de couverture, numérateur et dénominateur — 2.2 Enfants (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **2,0** | **2,1** | **2,7** | **2,4** | **2,6** | **1,8** | **0,0** | **0,0** |
| **Numérateur (nombre de personnes)**<span class="footnote">Pour les allocations familiales de la CNSS, le nombre d'enfants bénéficiaires est estimé en multipliant par 3,17 le nombre de titulaires de prestations familiales communiqué par la CNSS. Ce facteur correspond au nombre moyen d'enfants de moins de 20 ans par foyer en RDC en 2013, d'après UN HH Size and Composition 2019. Il s'agit donc d'une estimation et non d'un décompte administratif direct d'enfants.</span> | **847,801** | **933,117** | **1,256,688** | **1,130,597** | **1,266,245** | **914,223** | **0** | **0** |
| *Dont allocations familiales — Prestations familiales (CNSS, bénéf.)* | *847,801* | *933,077* | *1,256,585* | *1,129,861* | *1,256,585* | *911,125* | *—* | *—* |
| *Dont Rente de survie pour l'orphelin — Régime de base (CNSSAP, bénéf.)* | *—* | *40* | *103* | *187* | *738* | *2,378* | *—* | *—* |
| *Dont Rente de survie pour l'orphelin — Réforme du transfert (CNSSAP, bénéf.)* | *—* | *—* | *—* | *549* | *8,922* | *720* | *—* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population 0–14 ans, calculee = % INS x population totale INS.</span> | 42,737,234 | 44,203,394 | 45,697,743 | 47,215,242 | 48,758,487 | 50,299,865 | 51,846,285 | 53,371,488 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.2</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.2 Enfants (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_22_enfants_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_22_enfants_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_22_enfants:FIN -->

---

<!-- AUTO_GENERE:ind_23_maternite:DEBUT -->
## C.3 — 2.3 Maternité

**Définition (BIT/OIT).** Proportion de femmes ayant accouché qui reçoivent une prestation en espèces de maternité.

**Numérateur.** Nombre de femmes ayant accouché et percevant une indemnité ou une allocation de maternité en espèces.

**Dénominateur.** Nombre total de femmes ayant accouché au cours de la même année, estimé directement ou à partir des naissances vivantes corrigées des naissances multiples.

**Formule.** Femmes bénéficiaires d'une prestation de maternité ÷ femmes ayant accouché × 100.


<p class="table-caption"><strong>Tableau C.3</strong> — Indicateur de couverture, numérateur et dénominateur — 2.3 Maternité (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **[N/D]** | **[N/D]** |
| **Numérateur (nombre de personnes)** | **0** | **110** | **169** | **431** | **169** | **461** | **[N/D]** | **[N/D]** |
| *Dont allocation de maternité — Prestations familiales (CNSS, bénéf.)* | *—* | *108* | *167* | *414* | *167* | *390* | *—* | *—* |
| *↳ indemnité journalière de maternité (bénéf.)* | *—* | *2* | *2* | *17* | *2* | *71* | *—* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019 : Base locale ONU WPP 2024 — femmes 15–49 (B-MA) ; 2020 : Saisie manuelle - INS/RDC, canevas de collecte 2026 : nombre de naissances vivantes (2020), utilise comme approximation du nombre de femmes ayant accouche ; 2021–2024 : Base locale ONU WPP 2024 — femmes 15–49 (B-MA).</span> | 3,926,761 | 719,335 | 4,127,847 | 4,230,812 | 4,337,283 | 4,435,281 | 4,527,231 | 4,602,608 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.3</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.3 Maternité (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_23_maternite_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_23_maternite_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_23_maternite:FIN -->

---

<!-- AUTO_GENERE:ind_24_handicap:DEBUT -->
## C.4 — 2.4 Handicap / invalidité

**Définition (BIT/OIT).** Proportion de personnes en situation de handicap grave qui reçoivent une prestation en espèces d'invalidité.

**Numérateur.** Nombre de personnes en situation de handicap grave percevant une prestation en espèces d'invalidité.

**Dénominateur.** Population estimée de personnes en situation de handicap grave.

**Formule.** Bénéficiaires de prestations d'invalidité ÷ population en situation de handicap grave × 100.


<p class="table-caption"><strong>Tableau C.4</strong> — Indicateur de couverture, numérateur et dénominateur — 2.4 Handicap / invalidité (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **[N/D]** |
| **Numérateur (nombre de personnes)** | **1,965** | **1,588** | **1,479** | **1,781** | **1,452** | **3,292** | **0** | **[N/D]** |
| *Dont Rente ou allocation d'incapacité — Risques professionnels (CNSS, bénéf.)* | *1,082* | *1,020* | *955* | *1,053* | *1,020* | *2,853* | *—* | *—* |
| *Dont Pension d'invalidité — Pension (CNSS, bénéf.)* | *883* | *568* | *524* | *728* | *432* | *439* | *—* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Base locale — population × prévalence 15 % (proxy).</span> | 13,942,116 | 14,398,500 | 14,872,340 | 15,359,545 | 15,868,460 | 16,391,440 | 16,924,871 | 17,467,824 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.4</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.4 Handicap / invalidité (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_24_handicap_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_24_handicap_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_24_handicap:FIN -->

---

<!-- AUTO_GENERE:ind_25_atmp:DEBUT -->
## C.5 — 2.5 AT/MP

**Définition (BIT/OIT).** Proportion de la main-d'œuvre couverte par un régime assurant une protection en cas d'accident du travail ou de maladie professionnelle.

**Numérateur.** Nombre de personnes appartenant à la main-d'œuvre et couvertes en cas d'accident du travail ou de maladie professionnelle.

**Dénominateur.** Main-d'œuvre totale, composée des personnes en emploi et des personnes au chômage.

**Formule.** Main-d'œuvre couverte contre les accidents du travail et maladies professionnelles ÷ main-d'œuvre totale × 100.


<p class="table-caption"><strong>Tableau C.5</strong> — Indicateur de couverture, numérateur et dénominateur — 2.5 AT/MP (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **1,4** | **1,0** | **1,1** | **1,1** | **1,0** | **1,4** | **0,0** | **[N/D]** |
| **Numérateur (nombre de personnes)** | **678,737** | **511,336** | **593,930** | **616,595** | **580,900** | **809,045** | **0** | **[N/D]** |
| *Dont Branche des Risques Professionnels (CNSS, cotisants)* | *676,179* | *508,708* | *591,130* | *613,761* | *578,272* | *800,486* | *—* | *—* |
| *↳ Rente ou allocation d'incapacité (bénéf.)* | *1,082* | *1,020* | *955* | *1,053* | *1,020* | *2,853* | *—* | *—* |
| *↳ indemnité journalière (bénéf.)* | *—* | *—* | *—* | *—* | *—* | *2,853* | *—* | *—* |
| *↳ rentes de survivants (bénéf.)* | *1,476* | *1,608* | *1,845* | *1,781* | *1,608* | *2,853* | *—* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population active 15 ans et plus, calculee = % INS x population totale INS.</span> | 50,191,619 | 51,642,619 | 53,143,828 | 54,679,981 | 56,280,137 | 57,916,420 | 39,847,328 | 41,199,460 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.5</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.5 AT/MP (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_25_atmp_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_25_atmp_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_25_atmp:FIN -->

---

<!-- AUTO_GENERE:ind_26_chomage:DEBUT -->
## C.6 — 2.6 Chômage

**Définition (BIT/OIT).** Proportion de personnes au chômage qui reçoivent une prestation en espèces de chômage.

**Numérateur.** Nombre de personnes au chômage percevant effectivement une allocation de chômage en espèces.

**Dénominateur.** Nombre total de personnes au chômage selon la définition du BIT.

**Formule.** Chômeurs indemnisés ÷ nombre total de chômeurs × 100.


*Aucun régime d'assurance chômage opérationnel n'est identifié dans les ESS disponibles : ni numérateur ni dénominateur ne peuvent être calculés à ce stade.*

<!-- AUTO_GENERE:ind_26_chomage:FIN -->

---

<!-- AUTO_GENERE:ind_27_vieillesse:DEBUT -->
## C.7 — 2.7 Vieillesse

**Définition (BIT/OIT).** Proportion de personnes ayant atteint l'âge légal de la retraite qui reçoivent une prestation de vieillesse contributive ou non contributive.

**Numérateur.** Nombre de personnes ayant atteint l'âge légal de la retraite et percevant effectivement une pension ou une prestation de vieillesse.

**Dénominateur.** Population totale ayant atteint l'âge légal de la retraite, lequel peut différer selon le sexe ou le régime.

**Formule.** Bénéficiaires de prestations de vieillesse ÷ population ayant atteint l'âge légal de la retraite × 100.


<p class="table-caption"><strong>Tableau C.7</strong> — Indicateur de couverture, numérateur et dénominateur — 2.7 Vieillesse (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **1,0** | **1,0** | **1,0** | **1,1** | **1,1** | **1,1** | **[N/D]** | **[N/D]** |
| **Numérateur (nombre de personnes)** | **39,882** | **41,598** | **44,700** | **51,552** | **56,298** | **60,113** | **[N/D]** | **[N/D]** |
| *Dont Pension de retraite — Pension (CNSS, bénéf.)* | *38,641* | *39,465* | *42,407* | *44,094* | *43,601* | *44,937* | *—* | *—* |
| *↳ Pension de retraite anticipée (bénéf.)* | *—* | *78* | *272* | *1,235* | *696* | *940* | *—* | *—* |
| *Dont Pension de retraite — Régime de base (CNSSAP, bénéf.)* | *—* | *814* | *780* | *1,329* | *6,238* | *10,485* | *—* | *—* |
| *Dont Pension de retraite — Réforme du transfert (CNSSAP, bénéf.)* | *—* | *—* | *—* | *3,653* | *4,522* | *2,510* | *—* | *—* |
| *Dont Pension de retraite contributive — SESOPA_R1 (SESOPA, bénéf.)* | *964* | *964* | *964* | *964* | *964* | *964* | *—* | *—* |
| *↳ Pension de retraite des anciens parlementaires non cotisants prise en charge par le Trésor public (bénéf.)* | *277* | *277* | *277* | *277* | *277* | *277* | *—* | *—* |
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

**Définition (BIT/OIT).** Proportion de personnes vulnérables qui reçoivent une prestation d'assistance sociale en espèces.

**Numérateur.** Nombre de personnes vulnérables percevant une prestation d'assistance sociale en espèces.

**Dénominateur.** Population vulnérable, obtenue en retranchant de la population totale les personnes en âge de travailler cotisant à une assurance sociale ou percevant une prestation contributive, ainsi que les personnes d'âge légal de la retraite percevant une prestation contributive.

**Formule.** Personnes vulnérables bénéficiaires d'une prestation d'assistance sociale ÷ population vulnérable × 100.


*La population vulnérable et ses bénéficiaires d'assistance sociale ne font l'objet d'aucune mesure individualisable dans les sources actuellement disponibles : cet indicateur n'est pas calculé dans la présente édition.*

<!-- AUTO_GENERE:ind_28_vulnerables:FIN -->

---

<!-- AUTO_GENERE:ind_29_cotisants:DEBUT -->
## C.9 — 2.9 Cotisants actifs retraite

**Définition (BIT/OIT).** Proportion de la population en âge de travailler qui cotise activement à un régime de retraite contributif.

**Numérateur.** Nombre de personnes cotisant activement à un régime de retraite contributif.

**Dénominateur.** Population en âge de travailler (15-64 ans, Banque mondiale SP.POP.1564.TO) — voir DM-016.

**Formule.** Cotisants actifs à un régime de retraite ÷ population en âge de travailler (15-64 ans) × 100.


<p class="table-caption"><strong>Tableau C.9</strong> — Indicateur de couverture, numérateur et dénominateur — 2.9 Cotisants actifs retraite (2019–2026)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **4,5** | **4,4** | **4,4** | **4,3** | **4,2** | **5,1** | **[N/D]** | **[N/D]** |
| **Numérateur (nombre de personnes)** | **2,129,162** | **2,133,995** | **2,216,417** | **2,239,048** | **2,224,486** | **2,749,128** | **[N/D]** | **[N/D]** |
| *Dont Branche des Pensions (CNSS, cotisants)* | *676,179* | *508,708* | *591,130* | *613,761* | *578,272* | *800,486* | *—* | *—* |
| *Dont Régime de base (CNSSAP, cotisants)* | *—* | *172,304* | *190,545* | *198,399* | *1,004,106* | *1,013,104* | *—* | *—* |
| *Dont Régime Complémentaire (CNSSAP, cotisants)* | *—* | *—* | *—* | *—* | *218,899* | *219,327* | *—* | *—* |
| *Dont Branche des pensions  de retraite et de réversion (SESOPA, cotisants)* | *2,315* | *2,315* | *2,315* | *2,315* | *2,315* | *2,315* | *—* | *—* |
| *Dont Pensions de retraite octroyé de la fonction publique (estimation) (proxy budgétaire hors CNSSAP, personnes potentiellement couvertes estimées)* | *1,450,668* | *1,450,668* | *1,432,427* | *1,424,573* | *420,894* | *713,896* | *—* | *—* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : approximation calculee a partir des donnees INS : population active 15 ans et plus moins population 65 ans et plus.</span> | 47,589,090 | 48,858,909 | 50,169,360 | 51,505,675 | 52,894,866 | 54,310,304 | 57,506,566 | 59,478,100 |

*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations (« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et acronymes). « — » : composante non incluse cette année-là (ou décision non encore documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*

<p class="fig-caption"><strong>Figure C.9</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.9 Cotisants actifs retraite (2019–2026)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_29_cotisants_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_29_cotisants_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_29_cotisants:FIN -->
