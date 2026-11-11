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

Le sous-indicateur 2.6 (chômage) est non applicable : aucun régime d'assurance chômage n'existe dans le périmètre du bulletin. Le sous-indicateur relatif aux personnes vulnérables est calculé à partir des enfants bénéficiaires de prestations familiales ; son dénominateur est construit conformément au guide statistique de l'OIT. Voir Annexe D pour les dispositifs hors périmètre OIT néanmoins recensés.

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

**Cas particulier de l'hypothèse TRESOR hors CNSSAP.** Le code technique « TRESOR » ne désigne ni une institution ni un régime. Il qualifie une hypothèse de travail relative aux cotisants actifs estimés parmi les agents publics hors CNSSAP. Ces effectifs sont calculés par différence entre un total public de référence et les cotisants CNSSAP, afin d'éviter leur double compte ; ils sont retenus uniquement dans le sous-indicateur 2.9 des cotisants actifs à la retraite. Ils ne constituent pas une donnée administrative directe et restent exclus du numérateur global de l'ODD 1.3.1.

*Source des tableaux et figures C.1 à C.9 : ESS OIT et données institutionnelles intégrées dans la base du bulletin, avec application des décisions d'inclusion du tableau de bord. Les sources propres aux dénominateurs sont précisées dans les tableaux. Légende : « [N/D] » = donnée attendue mais indisponible ou non vérifiable ; « [N/A] » = composante non applicable, hors périmètre ou non mise en œuvre ; « 0 » = valeur nulle déclarée.*

---

<!-- AUTO_GENERE:global_131:DEBUT -->
## C.1 — ODD 1.3.1 — Global

**Définition (BIT/OIT).** Proportion de la population couverte par au moins une prestation en espèces de protection sociale ou cotisant activement à au moins un régime de sécurité sociale.

**Numérateur.** Nombre de personnes recevant au moins une prestation en espèces de protection sociale, hors soins de santé et indemnités journalières de maladie ou de maternité, ou cotisant activement à au moins un régime de sécurité sociale, sans double comptage.

**Dénominateur.** Population totale.

**Formule.** Population couverte par au moins une prestation ou cotisant activement ÷ population totale × 100.


<p class="table-caption"><strong>Tableau C.1</strong> — Indicateur de couverture, numérateur et dénominateur — ODD 1.3.1 — Global (2019–2025)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **1,7** | **1,8** | **2,4** | **2,2** | **3,0** | **2,8** | **1,7** |
| **Numérateur (nombre de personnes)** | **1 594 016** | **1 687 762** | **2 344 287** | **2 262 834** | **3 188 896** | **3 111 478** | **1 900 698** |
| *Dont Prestations familiales (CNSS, cotisants)* | *676 179* | *508 708* | *591 130* | *613 761* | *578 272* | *800 486* | *[N/D]* |
| *↳ allocation de maternité (bénéf.)* | *0* | *108* | *167* | *414* | *167* | *390* | *[N/D]* |
| *↳ allocations familiales (bénéf.)* | *847 801* | *933 077* | *1 256 585* | *1 129 861* | *1 256 585* | *911 125* | *[N/D]* |
| *↳ allocations prénatales (bénéf.)* | *0* | *162* | *184* | *532* | *531* | *365* | *[N/D]* |
| *Dont Risques professionnels (CNSS, cotisants)* | *676 179* | *508 708* | *591 130* | *613 761* | *578 272* | *800 486* | *[N/D]* |
| *↳ Rente ou allocation d'incapacité (bénéf.)* | *1 082* | *1 020* | *955* | *1 053* | *1 020* | *2 853* | *[N/D]* |
| *↳ allocation des frais funéraires (bénéf.)* | *[N/D]* | *589* | *849* | *533* | *[N/D]* | *[N/D]* | *[N/D]* |
| *↳ frais de réadaptation fonctionnelle  ou de reclassement de la victime (bénéf.)* | *[N/D]* | *[N/D]* | *[N/D]* | *677* | *[N/D]* | *[N/D]* | *[N/D]* |
| *↳ rentes de survivants (bénéf.)* | *1 476* | *1 608* | *1 845* | *1 781* | *1 608* | *1 107* | *[N/D]* |
| *Dont Pension (CNSS, cotisants)* | *676 179* | *508 708* | *591 130* | *613 761* | *578 272* | *800 486* | *[N/D]* |
| *↳ Pension d'invalidité (bénéf.)* | *883* | *568* | *524* | *728* | *432* | *439* | *[N/D]* |
| *↳ Pension de retraite (bénéf.)* | *38 641* | *39 465* | *42 407* | *44 094* | *43 601* | *44 937* | *[N/D]* |
| *↳ Pension de retraite anticipée (bénéf.)* | *0* | *78* | *272* | *1 235* | *696* | *940* | *[N/D]* |
| *↳ Pension des survivants (bénéf.)* | *24 725* | *25 720* | *28 355* | *31 524* | *30 778* | *33 506* | *[N/D]* |
| *Dont Régime de base (CNSSAP, cotisants)* | *[N/D]* | *172 304* | *190 545* | *198 399* | *1 004 106* | *1 013 104* | *1 470 429* |
| *↳ Pension de retraite (bénéf.)* | *[N/D]* | *814* | *780* | *1 329* | *6 238* | *10 485* | *9 136* |
| *↳ Rente de survie au conjoint survivants (bénéf.)* | *[N/D]* | *50* | *114* | *184* | *738* | *2 378* | *[N/D]* |
| *↳ Rente de survie pour l'orphelin (bénéf.)* | *[N/D]* | *40* | *103* | *187* | *738* | *2 378* | *448* |
| *Dont Réforme du transfert (CNSSAP, cotisants)* | *[N/D]* | *[N/D]* | *[N/D]* | *[N/D]* | *[N/D]* | *[N/D]* | *262 419* |
| *↳ Pension de retraite (bénéf.)* | *[N/D]* | *[N/D]* | *[N/D]* | *3 653* | *4 522* | *2 510* | *[N/D]* |
| *↳ Rente de survie au conjoint survivants (bénéf.)* | *[N/D]* | *[N/D]* | *[N/D]* | *6 044* | *8 922* | *7 508* | *[N/D]* |
| *↳ Rente de survie pour l'orphelin (bénéf.)* | *[N/D]* | *[N/D]* | *[N/D]* | *549* | *8 922* | *720* | *[N/D]* |
| *Dont Prestations en cas d'accident du travail — Risques professionnels (CNSSAP, bénéf.)* | *[N/D]* | *[N/D]* | *[N/D]* | *[N/D]* | *[N/D]* | *2* | *2* |
| *↳ Prestations en cas de maladie professionnelle (bénéf.)* | *[N/D]* | *[N/D]* | *[N/D]* | *[N/D]* | *[N/D]* | *0* | *[N/D]* |
| *Dont Pension de retraite — Réforme de basculement (CNSSAP, bénéf.)* | *[N/A]* | *[N/A]* | *[N/A]* | *[N/D]* | *[N/D]* | *[N/D]* | *4 038* |
| *↳ Rente de survie au conjoint survivants (bénéf.)* | *[N/A]* | *[N/A]* | *[N/A]* | *[N/D]* | *[N/D]* | *[N/D]* | *4 383* |
| *↳ Rente de survie pour l'orphelin (bénéf.)* | *[N/A]* | *[N/A]* | *[N/A]* | *[N/D]* | *[N/D]* | *[N/D]* | *550* |
| *Dont Repas scolaires PAM — PAM_R1 (PAM, bénéf.)* | *[N/D]* | *[N/D]* | *226 000* | *222 800* | *237 000* | *272 000* | *145 030* |
| *Dont Branche des pensions  de retraite et de réversion (SESOPA, cotisants)* | *1 815* | *1 815* | *1 815* | *1 815* | *2 315* | *2 315* | *2 315* |
| *↳ Pension de retraite contributive (bénéf.)* | *1 018* | *1 031* | *1 021* | *1 029* | *1 023* | *1 256* | *1 277* |
| *↳ Pension de réversion (rente viagère du conjoint survivant) (bénéf.)* | *396* | *605* | *636* | *652* | *682* | *674* | *671* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population totale ; 2025 : src-unwpp-2024jul-rev [var-c-popsx / sex-t / age-0+] — population 0+.</span> | 92 947 442 | 95 989 998 | 99 148 932 | 102 396 968 | 105 789 731 | 109 276 265 | 112 832 473 |

<p class="fig-caption"><strong>Figure C.1</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — ODD 1.3.1 — Global (2019–2025)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_global_131_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_global_131_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:global_131:FIN -->

---

<!-- AUTO_GENERE:ind_22_enfants:DEBUT -->
## C.2 — 2.2 Population 0–17 ans

**Définition (BIT/OIT).** Proportion de la population âgée de 0 à 17 ans bénéficiant d'au moins une prestation en espèces de protection sociale destinée aux enfants ou aux familles.

**Numérateur.** Nombre de bénéficiaires âgés de 0 à 17 ans recevant au moins une prestation en espèces pour enfants ou famille, hors indemnités journalières de maladie ou de maternité.

**Dénominateur.** Population totale âgée de 0 à 17 ans.

**Formule.** Bénéficiaires âgés de 0 à 17 ans ÷ population totale âgée de 0 à 17 ans × 100.


<p class="table-caption"><strong>Tableau C.2</strong> — Indicateur de couverture, numérateur et dénominateur — 2.2 Population 0–17 ans (2019–2025)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **1,7** | **1,9** | **2,4** | **2,1** | **2,3** | **1,6** | **0,0** |
| **Numérateur (nombre de personnes)**<span class="footnote">Pour les allocations familiales de la CNSS, le nombre d'enfants bénéficiaires est estimé en multipliant par 3,17 le nombre de titulaires de prestations familiales communiqué par la CNSS. Ce facteur correspond au nombre moyen d'enfants de moins de 20 ans par foyer en RDC en 2013, d'après UN HH Size and Composition 2019. Il s'agit donc d'une estimation et non d'un décompte administratif direct d'enfants.</span> | **847 801** | **933 117** | **1 256 688** | **1 130 597** | **1 266 245** | **914 223** | **448** |
| *Dont allocations familiales — Prestations familiales (CNSS, bénéf.)* | *847 801* | *933 077* | *1 256 585* | *1 129 861* | *1 256 585* | *911 125* | *[N/D]* |
| *Dont Rente de survie pour l'orphelin — Régime de base (CNSSAP, bénéf.)* | *[N/D]* | *40* | *103* | *187* | *738* | *2 378* | *448* |
| *Dont Rente de survie pour l'orphelin — Réforme du transfert (CNSSAP, bénéf.)* | *[N/D]* | *[N/D]* | *[N/D]* | *549* | *8 922* | *720* | *[N/D]* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population 0–17 ans (A3), calculee = % INS x population totale INS (2019) ; proportion INS approximative ; 2020 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population 0–17 ans (A3), calculee = % INS x population totale INS (2020) ; proportion INS approximative ; 2021 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population 0–17 ans (A3), calculee = % INS x population totale INS (2021) ; proportion INS approximative ; 2022 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population 0–17 ans (A3), calculee = % INS x population totale INS (2022) ; proportion INS approximative ; 2023 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population 0–17 ans (A3), calculee = % INS x population totale INS (2023) ; proportion INS approximative ; 2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population 0–17 ans (A3), calculee = % INS x population totale INS (2024) ; proportion INS approximative.</span> | 48 797 407 | 50 394 749 | 51 954 040 | 53 553 614 | 55 222 240 | 56 932 934 | 59 229 488 |

<p class="fig-caption"><strong>Figure C.2</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.2 Population 0–17 ans (2019–2025)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_22_enfants_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_22_enfants_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_22_enfants:FIN -->

---

<!-- AUTO_GENERE:ind_23_maternite:DEBUT -->
## C.3 — 2.3 Maternité

**Définition (BIT/OIT).** Proportion de femmes ayant accouché qui reçoivent une prestation en espèces de maternité.

**Numérateur.** Nombre de bénéficiaires de l'allocation de maternité de la CNSS. Les indemnités journalières de maternité sont exclues.

**Dénominateur.** Nombre total de femmes ayant accouché au cours de la même année, estimé directement ou à partir des naissances vivantes corrigées des naissances multiples.

**Formule.** Femmes bénéficiaires d'une prestation de maternité ÷ femmes ayant accouché × 100.


<p class="table-caption"><strong>Tableau C.3</strong> — Indicateur de couverture, numérateur et dénominateur — 2.3 Maternité (2019–2025)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **0,0** | **[N/D]** |
| **Numérateur (nombre de personnes)** | **0** | **108** | **167** | **414** | **167** | **390** | **[N/D]** |
| *Dont allocation de maternité — Prestations familiales (CNSS, bénéf.)* | *0* | *108* | *167* | *414* | *167* | *390* | *[N/D]* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019 : Estimation démographique : population totale INS/RDC (92 947 442) × taux brut de natalité DonnéesMondiales.com (42,5 pour 1 000) ; 2020 : Saisie manuelle - INS/RDC, canevas de collecte 2026 : nombre de naissances vivantes (2020), utilise comme approximation du nombre de femmes ayant accouche ; 2021 : Estimation démographique : population totale INS/RDC (99 148 932) × taux brut de natalité DonnéesMondiales.com (41,9 pour 1 000) ; 2022 : Estimation démographique : population totale INS/RDC (102 396 968) × taux brut de natalité DonnéesMondiales.com (41,6 pour 1 000) ; 2023 : Estimation démographique : population totale INS/RDC (105 789 731) × taux brut de natalité DonnéesMondiales.com (41,3 pour 1 000) ; 2024 : Estimation démographique : population totale INS/RDC (109 276 265) × taux brut de natalité DonnéesMondiales.com (40,9 pour 1 000).</span> | 3 950 266 | 719 335 | 4 154 340 | 4 259 714 | 4 369 116 | 4 469 399 | [N/D] |

<p class="fig-caption"><strong>Figure C.3</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.3 Maternité (2019–2025)</p>

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


<p class="table-caption"><strong>Tableau C.4</strong> — Indicateur de couverture, numérateur et dénominateur — 2.4 Handicap / invalidité (2019–2025)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **0,1** | **0,1** | **0,0** | **0,1** | **0,0** | **0,1** | **[N/D]** |
| **Numérateur (nombre de personnes)** | **1 965** | **1 588** | **1 479** | **1 781** | **1 452** | **3 292** | **[N/D]** |
| *Dont Rente ou allocation d'incapacité — Risques professionnels (CNSS, bénéf.)* | *1 082* | *1 020* | *955* | *1 053* | *1 020* | *2 853* | *[N/D]* |
| *Dont Pension d'invalidité — Pension (CNSS, bénéf.)* | *883* | *568* | *524* | *728* | *432* | *439* | *[N/D]* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Estimation BIT/OMS : population totale INS/RDC × 3 % (handicap grave) ; 2025 : Estimation BIT/OMS : population totale ONU WPP 2024 (112 832 473) × 3 % (handicap grave).</span> | 2 788 423 | 2 879 700 | 2 974 468 | 3 071 909 | 3 173 692 | 3 278 288 | 3 384 974 |

<p class="fig-caption"><strong>Figure C.4</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.4 Handicap / invalidité (2019–2025)</p>

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


<p class="table-caption"><strong>Tableau C.5</strong> — Indicateur de couverture, numérateur et dénominateur — 2.5 AT/MP (2019–2025)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **1,4** | **1,0** | **1,1** | **1,1** | **1,0** | **1,4** | **[N/D]** |
| **Numérateur (nombre de personnes)** | **678 737** | **511 336** | **593 930** | **616 595** | **580 900** | **804 446** | **[N/D]** |
| *Dont Risques professionnels (CNSS, cotisants)* | *676 179* | *508 708* | *591 130* | *613 761* | *578 272* | *800 486* | *[N/D]* |
| *↳ Rente ou allocation d'incapacité (bénéf.)* | *1 082* | *1 020* | *955* | *1 053* | *1 020* | *2 853* | *[N/D]* |
| *↳ rentes de survivants (bénéf.)* | *1 476* | *1 608* | *1 845* | *1 781* | *1 608* | *1 107* | *[N/D]* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population active 15 ans et plus, calculee = % INS x population totale INS.</span> | 50 191 619 | 51 642 619 | 53 143 828 | 54 679 981 | 56 280 137 | 57 916 420 | 39 847 328 |

<p class="fig-caption"><strong>Figure C.5</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.5 AT/MP (2019–2025)</p>

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


*[N/A] — aucun régime d'assurance chômage n'existe dans le périmètre du bulletin. Aucune allocation de chômage ne peut donc être mesurée.*

<!-- AUTO_GENERE:ind_26_chomage:FIN -->

---

<!-- AUTO_GENERE:ind_27_vieillesse:DEBUT -->
## C.7 — 2.7 Vieillesse

**Définition (BIT/OIT).** Proportion de personnes ayant atteint l'âge légal de la retraite qui reçoivent une prestation de vieillesse contributive ou non contributive.

**Numérateur.** Nombre de bénéficiaires d'une pension de vieillesse, y compris les pensions de retraite anticipée. Ces dernières peuvent concerner des personnes âgées de moins de 60 ans.

**Dénominateur.** Population totale âgée de 60 ans et plus. Ce seuil unique correspond à l'âge d'ouverture du droit à pension CNSS ; la mise à la retraite d'office intervient à 65 ans.

**Formule.** Bénéficiaires de prestations de vieillesse ÷ population ayant atteint l'âge légal de la retraite × 100.


<p class="table-caption"><strong>Tableau C.7</strong> — Indicateur de couverture, numérateur et dénominateur — 2.7 Vieillesse (2019–2025)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **1,0** | **1,0** | **1,0** | **1,1** | **1,1** | **1,1** | **[N/D]** |
| **Numérateur (nombre de personnes)** | **39 659** | **41 388** | **44 480** | **51 340** | **56 080** | **60 128** | **[N/D]** |
| *Dont Pension de retraite — Pension (CNSS, bénéf.)* | *38 641* | *39 465* | *42 407* | *44 094* | *43 601* | *44 937* | *[N/D]* |
| *↳ Pension de retraite anticipée (bénéf.)* | *0* | *78* | *272* | *1 235* | *696* | *940* | *[N/D]* |
| *Dont Pension de retraite — Régime de base (CNSSAP, bénéf.)* | *[N/D]* | *814* | *780* | *1 329* | *6 238* | *10 485* | *[N/D]* |
| *Dont Pension de retraite — Réforme du transfert (CNSSAP, bénéf.)* | *[N/D]* | *[N/D]* | *[N/D]* | *3 653* | *4 522* | *2 510* | *[N/D]* |
| *Dont Pension de retraite contributive — SESOPA_R1 (SESOPA, bénéf.)* | *1 018* | *1 031* | *1 021* | *1 029* | *1 023* | *1 256* | *[N/D]* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : population 60 ans et plus, seuil unique retenu.</span> | 3 996 740 | 4 223 560 | 4 461 702 | 4 710 261 | 4 972 117 | 5 245 261 | [N/D] |

<p class="fig-caption"><strong>Figure C.7</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.7 Vieillesse (2019–2025)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_27_vieillesse_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_27_vieillesse_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_27_vieillesse:FIN -->

---

<!-- AUTO_GENERE:ind_28_vulnerables:DEBUT -->
## C.8 — 2.8 Vulnérables / assistance

**Définition (BIT/OIT).** Proportion de personnes vulnérables qui reçoivent une intervention d'assistance sociale, en espèces ou en nature.

**Numérateur.** Somme des enfants bénéficiaires de prestations familiales et des enfants servis par les repas scolaires PAM.

**Dénominateur.** Population totale, moins les cotisants actifs dédupliqués, TRESOR inclus, et les bénéficiaires de pensions de vieillesse.

**Formule.** Enfants bénéficiaires de prestations familiales + enfants servis par les repas scolaires PAM, le tout ÷ population vulnérable × 100.


<p class="table-caption"><strong>Tableau C.8</strong> — Indicateur de couverture, numérateur et dénominateur — 2.8 Vulnérables / assistance (2019–2025)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **0,9** | **1,0** | **1,5** | **1,4** | **1,5** | **1,1** | **[N/D]** |
| **Numérateur (nombre de personnes)**<span class="footnote">Le numérateur additionne les enfants bénéficiaires de prestations familiales, dont les allocations familiales CNSS déjà estimées à partir de 3,17 enfants par titulaire, et les enfants servis par les repas scolaires PAM (2021-2025). Faute d'identifiant individuel commun, cette somme ne déduplique pas un éventuel recoupement entre les deux interventions. En 2024, la valeur PAM retenue est 272 000 enfants, avec réserve : le tableau détaillé du rapport indique 194 636 enfants servis sur site. Le dénominateur est la population totale, moins les cotisants actifs dédupliqués, TRESOR inclus, et les bénéficiaires de pensions de vieillesse.</span> | **847 801** | **933 117** | **1 482 688** | **1 353 397** | **1 503 245** | **1 186 223** | **145 478** |
| *Dont allocations familiales — Prestations familiales (CNSS, bénéf.)* | *847 801* | *933 077* | *1 256 585* | *1 129 861* | *1 256 585* | *911 125* | *[N/D]* |
| *Dont Rente de survie pour l'orphelin — Régime de base (CNSSAP, bénéf.)* | *[N/D]* | *40* | *103* | *187* | *738* | *2 378* | *448* |
| *Dont Rente de survie pour l'orphelin — Réforme du transfert (CNSSAP, bénéf.)* | *[N/D]* | *[N/D]* | *[N/D]* | *549* | *8 922* | *720* | *[N/D]* |
| *Dont Repas scolaires PAM — PAM_R1 (PAM, bénéf.)* | *[N/D]* | *[N/D]* | *226 000* | *222 800* | *237 000* | *272 000* | *145 030* |
| Dénominateur (population de référence)<span class="footnote">Dénominateur : population totale moins les cotisants actifs dédupliqués, TRESOR inclus, et les bénéficiaires de pensions de vieillesse.</span> | 90 779 121 | 93 815 115 | 96 888 535 | 100 107 080 | 103 530 092 | 106 686 336 | [N/D] |

<p class="fig-caption"><strong>Figure C.8</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.8 Vulnérables / assistance (2019–2025)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_28_vulnerables_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_28_vulnerables_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_28_vulnerables:FIN -->

---

<!-- AUTO_GENERE:ind_29_cotisants:DEBUT -->
## C.9 — 2.9 Cotisants actifs retraite

**Définition (BIT/OIT).** Proportion de la population en âge de travailler qui cotise activement à un régime de retraite contributif.

**Numérateur.** Nombre de personnes cotisant activement à un régime de retraite contributif.

**Dénominateur.** Population en âge de travailler (15-64 ans, Banque mondiale SP.POP.1564.TO).

**Formule.** Cotisants actifs à un régime de retraite ÷ population en âge de travailler (15-64 ans) × 100.


<p class="table-caption"><strong>Tableau C.9</strong> — Indicateur de couverture, numérateur et dénominateur — 2.9 Cotisants actifs retraite (2019–2025)</p>

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **Indicateur de couverture (%)** | **4,5** | **4,4** | **4,4** | **4,3** | **4,2** | **4,7** | **[N/D]** |
| **Numérateur (nombre de personnes)**<span class="footnote">Pour la CNSSAP, les cotisants du régime complémentaire 2023–2024 sont présentés dans l'Annexe B mais exclus de cet indicateur : l'absence d'identifiant commun ne permet pas de vérifier qu'ils sont distincts des cotisants du régime de base.</span> | **2 128 662** | **2 133 495** | **2 215 917** | **2 238 548** | **2 203 559** | **2 529 801** | **[N/D]** |
| *Dont Pension (CNSS, cotisants)* | *676 179* | *508 708* | *591 130* | *613 761* | *578 272* | *800 486* | *[N/D]* |
| *Dont Régime de base (CNSSAP, cotisants)* | *[N/D]* | *172 304* | *190 545* | *198 399* | *1 004 106* | *1 013 104* | *[N/D]* |
| *Dont Branche des pensions  de retraite et de réversion (SESOPA, cotisants)* | *1 815* | *1 815* | *1 815* | *1 815* | *2 315* | *2 315* | *[N/D]* |
| *Dont Hypothèse TRESOR hors CNSSAP — cotisants actifs estimés de la fonction publique* | *1 450 668* | *1 450 668* | *1 432 427* | *1 424 573* | *618 866* | *713 896* | *[N/D]* |
| Dénominateur (population de référence)<span class="footnote">Sources du dénominateur — 2019–2024 : Saisie manuelle — INS/RDC, canevas de collecte 2026 : approximation calculee a partir des donnees INS : population active 15 ans et plus moins population 65 ans et plus.</span> | 47 589 090 | 48 858 909 | 50 169 360 | 51 505 675 | 52 894 866 | 54 310 304 | 57 506 566 |

<p class="fig-caption"><strong>Figure C.9</strong> — Évolution de l'indicateur de couverture (%) et du numérateur (effectifs) — 2.9 Cotisants actifs retraite (2019–2025)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_29_cotisants_indicateur.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_C_ind_29_cotisants_numerateur.png" style="width:100%; height:auto;"></td></tr>
</table>

<!-- AUTO_GENERE:ind_29_cotisants:FIN -->

## C.10 — Réconciliation avec le premier bulletin (2019–2022)

Le tableau ci-dessous rapproche les valeurs publiées dans le premier Bulletin statistique de la protection sociale en RDC et les valeurs des mêmes années recalculées selon les règles retenues dans la présente édition. Les valeurs sont arrondies à une décimale dans la colonne de recalcul. Une absence de comparabilité signifie que le concept, et non seulement la source, a changé.

<p class="table-caption"><strong>Tableau C.10</strong> — Réconciliation des indicateurs avec le premier bulletin (2019–2022)</p>
| Sous-indicateur | Premier bulletin : 2019 / 2020 / 2021 / 2022 | Méthode actuelle recalculée : 2019 / 2020 / 2021 / 2022 | Réconciliation et comparabilité |
|---|---|---|---|
| Enfants | 1,78 % / 1,90 % / 2,47 % / 2,15 % | 1,7 % / 1,9 % / 2,4 % / 2,1 % | Même logique de numérateur, y compris l'estimation CNSS de 3,17 enfants par titulaire. Le dénominateur est désormais explicitement la population de 0 à 17 ans et les valeurs sont présentées à une décimale. Comparabilité élevée, sous réserve de l'arrondi. |
| AT/MP | 2,14 % / 1,62 % / 1,76 % / 1,76 % | 1,4 % / 1,0 % / 1,1 % / 1,1 % | Le numérateur de 2022 reste 616 595 personnes. La rupture provient du dénominateur : la population active de l'ancien bulletin est remplacée par la force de travail de 15 ans et plus de la série actuelle. Comparabilité limitée. |
| Vieillesse | 0,94 % / 0,93 % / 0,98 % / 1,03 % | 1,0 % / 1,0 % / 1,0 % / 1,1 % | Le dénominateur est harmonisé à la population de 60 ans et plus. Le numérateur actuel intègre les composantes ESS disponibles, y compris les pensions de retraite anticipée. Comparabilité partielle. |
| Invalidité / handicap | 0 % / 0 % / 0 % / 0 % | 0,1 % / 0,1 % / 0,0 % / 0,1 % | Le numérateur reste composé des pensions d'invalidité et des rentes d'incapacité. L'écart apparent résulte principalement du passage d'un affichage à zéro entier à un arrondi à une décimale. Comparabilité élevée. |
| Personnes vulnérables — assistance sociale | 0,94 % / 1,00 % / 1,31 % / 1,14 % | 0,9 % / 1,0 % / 1,5 % / 1,4 % | Le dénominateur actuel retire les cotisants actifs dédupliqués, TRESOR inclus, et les pensionnés de vieillesse. À partir de 2021, le numérateur ajoute les repas scolaires PAM ; il ne déduplique pas un éventuel recoupement avec les prestations familiales. Comparabilité limitée. |
| Cotisants et couverture statutaire des actifs | 2,76 % / 2,25 % / 2,41 % / 2,42 % | 4,5 % / 4,4 % / 4,4 % / 4,3 % | L'ancien indicateur associait cotisants et bénéficiaires de prestations de long terme rapportés à la population active. L'indicateur actuel ne mesure que les cotisants actifs, rapportés à la population de 15 à 64 ans, avec une déduplication Q1 et l'hypothèse TRESOR. Non directement comparable. |
| Maternité | Pas de série de couverture publiée selon le format actuel | 0,0 % / 0,0 % / 0,0 % / 0,0 % | Le numérateur actuel est limité aux bénéficiaires de l'allocation de maternité CNSS, à l'exclusion des indemnités journalières. Le dénominateur est constitué des naissances vivantes observées ou estimées. Nouvelle série. |
| Chômage | Absence de régime constatée | N/A | Aucun régime d'assurance chômage n'est identifié dans les deux éditions. La présente édition affiche donc N/A plutôt qu'un taux nul. |

*Source : premier Bulletin statistique de la protection sociale en RDC, tableaux 13 à 20, et recalculs de la présente édition à partir des ESS, des décisions d'inclusion et des dénominateurs documentés dans la présente annexe.*
