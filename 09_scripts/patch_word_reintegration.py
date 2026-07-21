# -*- coding: utf-8 -*-
"""Script de reintegration des modifications Word dans les fichiers Markdown."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\M.Diouf\OneDrive\Bureau\RDC Bulletin V1\Bulletin_rdc_2026_agents"
import os

def read(rel): 
    p = os.path.join(BASE, rel)
    with open(p, encoding='utf-8-sig') as f: return f.read()

def write(rel, content):
    p = os.path.join(BASE, rel)
    with open(p, 'w', encoding='utf-8') as f: f.write(content)
    print(f"  Modifie: {rel}")

def patch(rel, old, new, desc=""):
    content = read(rel)
    if old in content:
        write(rel, content.replace(old, new, 1))
        print(f"  OK [{desc}]")
        return True
    else:
        print(f"  INTROUVABLE [{desc}]: {old[:80]}")
        return False

changes = []

# =============================================================
# DIFF #1 — remerciements.md
# "sa profonde reconnaissance" -> "sa reconnaissance"
# =============================================================
f1 = "01_pages_preliminaires/remerciements.md"
changes.append((f1, "sa profonde reconnaissance", "sa reconnaissance", "D1-remerciements"))

# =============================================================
# DIFF #5 — 0_1_contexte_demographique.md
# Supprimer "une densite moyenne... mais " dans la phrase
# =============================================================
f_demo = "02_introduction_generale/0_1_contexte_demographique.md"
changes.append((f_demo,
    'avec une densit\u00e9 moyenne de <a href="/files/06_sources/officielles_web/ONU_WPP_2024_RDC_population.txt" title="Source : Division de la population des Nations Unies (2024) \u2014 Perspectives mondiales de la population 2024" class="source-ref nv">51 habitants par km\u00b2</a> sur un territoire de plus de 2,3 millions de km\u00b2, mais des',
    'avec et des',
    "D5-urbanisation-densite"))

# =============================================================
# DIFF #6 — 0_1_contexte_demographique.md
# Supprimer la derniere phrase du dernier paragraphe
# =============================================================
changes.append((f_demo,
    " Ces constats, combin\u00e9s aux donn\u00e9es \u00e9conomiques pr\u00e9sent\u00e9es dans la section suivante, permettront d\u2019appr\u00e9cier plus finement les conditions dans lesquelles l\u2019extension de la couverture devra se r\u00e9aliser.",
    "",
    "D6-enlever-derniere-phrase-demo"))

# =============================================================
# DIFF #7 — 0_2_contexte_economique_emploi.md
# =============================================================
f_eco = "02_introduction_generale/0_2_contexte_economique_emploi.md"
changes.append((f_eco, "est largement port\u00e9e par le secteur minier", "est notamment port\u00e9e par le secteur minier", "D7a-portee"))
changes.append((f_eco, "par une am\u00e9lioration sensible du niveau de vie moyen", "par une am\u00e9lioration proportionnelle du niveau de vie moyen", "D7b-amelioration"))
changes.append((f_eco, "demeurent marqu\u00e9es entre groupes sociaux et entre provinces.", "demeurent marqu\u00e9es.", "D7c-disparites"))

# =============================================================
# DIFF #8 — 0_2_contexte_economique_emploi.md
# =============================================================
changes.append((f_eco,
    "chez les femmes, ces derni\u00e8res \u00e9tant plus fr\u00e9quemment maintenues hors du march\u00e9 du travail visible du fait de responsabilit\u00e9s familiales et de barri\u00e8res d\u2019acc\u00e8s \u00e0 l\u2019emploi.",
    "chez les femmes.",
    "D8a-taux-activite-femmes"))
changes.append((f_eco, "pr\u00e9dominance \u00e9crasante de l\u2019emploi informel", "pr\u00e9dominance de l\u2019emploi informel", "D8b-predominance"))
changes.append((f_eco, "taux de ch\u00f4mage officiel relativement faible", "taux de ch\u00f4mage relativement faible", "D8c-chomage"))

# =============================================================
# DIFF #9 — 0_2_contexte_economique_emploi.md
# Supprimer derniere phrase du paragraphe "risques professionnels"
# =============================================================
changes.append((f_eco,
    " Ces r\u00e9alit\u00e9s renforcent l\u2019importance d\u2019un suivi statistique rigoureux des affili\u00e9s, des cotisants actifs et des victimes d\u2019accidents du travail \u2014 donn\u00e9es au c\u0153ur du pr\u00e9sent bulletin.",
    "",
    "D9-secteurs-risques-derniere-phrase"))

# =============================================================
# DIFF #10 — 0_2_contexte_economique_emploi.md
# Supprimer sentence sur "majorite des travailleurs"
# =============================================================
changes.append((f_eco,
    " La majorit\u00e9 des travailleurs n\u2019est pas enregistr\u00e9e aupr\u00e8s des r\u00e9gimes contributifs formels, ce qui limite \u00e0 la fois l\u2019assiette de cotisation des institutions et l\u2019acc\u00e8s effectif aux prestations pour les assur\u00e9s potentiels.",
    "",
    "D10-enjeux-extension"))

# =============================================================
# DIFF #11 — 0_3_strategie_donnees_statistiques.md
# =============================================================
f_strat = "02_introduction_generale/0_3_strategie_donnees_statistiques.md"
changes.append((f_strat, "jusqu\u2019\u00e0 d\u00e9cembre 2025", "2019-\u00a02025", "D11a-periode"))
changes.append((f_strat, "Le chapitre 1 pr\u00e9sente le cadre conceptuel", "Le chapitre 2 pr\u00e9sente le cadre conceptuel", "D11b-chapitre"))

# =============================================================
# DIFF #12 — 0_3_strategie_donnees_statistiques.md
# =============================================================
changes.append((f_strat,
    "\u00e2ge, province ou secteur \u2014 n\u2019est",
    "\u00e2ge,\u2014 n\u2019est",
    "D12-desagregation"))

# =============================================================
# DIFF #13 — 2_1_cartographie_tableaux.md
# "quatre grandes categories" -> "cinq grandes categories" (liste numerotee)
# =============================================================
f_carto = "03_chapitres/chapitre_2/2_1_cartographie_tableaux.md"
old13 = """Cette cartographie distingue quatre grandes cat\u00e9gories : la s\u00e9curit\u00e9 sociale contributive obligatoire, qui couvre les travailleurs du secteur priv\u00e9 formel via la CNSS et les agents publics affili\u00e9s \u00e0 la CNSSAP (Tableau 2.1) ; les dispositifs statutaires financ\u00e9s directement par le budget de l\u2019\u00c9tat, qui regroupent les r\u00e9gimes sp\u00e9ciaux formellement constitu\u00e9s et, lorsqu\u2019elle est effectivement document\u00e9e, la protection budg\u00e9taire d\u2019autres agents publics hors CNSSAP (Tableau 2.2) ; la protection de la sant\u00e9, organis\u00e9e par segment de population (Tableau 2.3) ; les programmes d\u2019assistance sociale et initiatives non contributives destin\u00e9s aux populations non couvertes par les r\u00e9gimes formels (Tableau 2.4) ; enfin, un ensemble de politiques sectorielles \u00e0 dimension protectrice \u2014 gratuit\u00e9s, programmes d\u2019activation par l\u2019emploi, acc\u00e8s subventionn\u00e9 aux services de base \u2014 dont la finalit\u00e9 sociale est \u00e9tablie mais qui ne rel\u00e8vent pas \u00e0 proprement parler de l\u2019assistance sociale (Tableau 2.5, mention contextuelle)."""
new13 = """Cette cartographie distingue cinq grandes cat\u00e9gories :

1) la s\u00e9curit\u00e9 sociale contributive obligatoire, hors sant\u00e9, qui couvre les travailleurs du secteur priv\u00e9 formel via la CNSS et les agents publics affili\u00e9s \u00e0 la CNSSAP (Tableau 2.1) ;

2) les dispositifs statutaires, hors sant\u00e9, financ\u00e9s directement par le budget de l\u2019\u00c9tat, qui regroupent les r\u00e9gimes sp\u00e9ciaux formellement constitu\u00e9s et la protection des agents publics qui ne sont pas encore transf\u00e9r\u00e9s formellement \u00e0 la CNSSAP (Tableau 2.2) ;

3) la protection de la sant\u00e9, organis\u00e9e par segment de population (Tableau 2.3) ;

4) les programmes d\u2019assistance sociale et initiatives non contributives destin\u00e9s aux populations non couvertes par les r\u00e9gimes formels (Tableau 2.4) ;

5) enfin, un ensemble de politiques sectorielles \u00e0 dimension protectrice \u2014 gratuit\u00e9s, programmes d\u2019activation par l\u2019emploi, acc\u00e8s subventionn\u00e9 aux services de base \u2014 dont la finalit\u00e9 sociale est \u00e9tablie mais qui ne rel\u00e8vent pas \u00e0 proprement parler de l\u2019assistance sociale (Tableau 2.5, mention contextuelle)."""
changes.append((f_carto, old13, new13, "D13-cinq-categories"))

# DIFF #13 suite: renommer le sous-titre de section
changes.append((f_carto,
    "### S\u00e9curit\u00e9 sociale contributive obligatoire <span",
    "### 1) S\u00e9curit\u00e9 sociale contributive obligatoire hors sant\u00e9 <span",
    "D13b-titre-secu-sociale"))

# DIFF #14: "Dispositifs statutaires..." -> "2) Dispositifs statutaires..."
changes.append((f_carto,
    "### Dispositifs statutaires financ\u00e9s directement par le budget de l\u2019\u00c9tat <span",
    "### 2) Dispositifs statutaires financ\u00e9s directement par le budget de l\u2019\u00c9tat <span",
    "D14-titre-dispositifs"))

# DIFF #15: "la protection est effectivement assuree..." -> version enrichie
old15 = "La seconde cat\u00e9gorie recouvre les **agents publics hors CNSSAP dont la protection est effectivement assur\u00e9e par un dispositif statutaire financ\u00e9 directement par le budget de l\u2019\u00c9tat**, sans s\u2019inscrire dans un r\u00e9gime sp\u00e9cial formellement constitu\u00e9. La m\u00e9canisation \u2014 entendue comme l\u2019int\u00e9gration administrative et salariale dans le syst\u00e8me de paie de l\u2019\u00c9tat \u2014 facilite la retenue r\u00e9guli\u00e8re des cotisations et le passage \u00e0 une couverture contributive effective par la CNSSAP. Toutefois, l\u2019absence de m\u00e9canisation ou d\u2019affiliation \u00e0 la CNSSAP ne suffit pas, \u00e0 elle seule, \u00e0 \u00e9tablir l\u2019existence d\u2019une couverture budg\u00e9taire effective. Celle-ci doit \u00eatre attest\u00e9e par des droits identifiables, une population d\u00e9nombrable et une prise en charge budg\u00e9taire document\u00e9e. Qualifier cette population de \u00ab r\u00e9gime sp\u00e9cial \u00bb serait inexact : elle rel\u00e8ve des dispositions g\u00e9n\u00e9rales applicables aux agents de l\u2019\u00c9tat, et non d\u2019un r\u00e9gime sp\u00e9cial distinct."
new15 = """La seconde cat\u00e9gorie recouvre les **agents publics hors CNSSAP dont la protection est encore effectivement assur\u00e9e par un dispositif statutaire financ\u00e9 directement par le budget de l\u2019\u00c9tat**.

Historiquement, la protection sociale des agents de l\u2019\u00c9tat \u00e9tait assur\u00e9e par un syst\u00e8me de r\u00e9gimes dit \u00ab octroy\u00e9s \u00bb : un ensemble de prestations (sous condition d\u2019\u00e9ligibilit\u00e9) \u00e9tait garanti aux agents de l\u2019\u00c9tat et directement financ\u00e9 par le budget national, sans recourir \u00e0 un m\u00e9canisme assuranciel. Un programme de transf\u00e8rement de ces effectifs sous la responsabilit\u00e9 de la CNSSAP est en cours depuis 2022. Ce m\u00e9canisme est d\u00e9sign\u00e9 comme la r\u00e9forme de transf\u00e8rement.

Cependant, la fourniture de protection sociale par un syst\u00e8me non contributif et non assuranciel persiste sous deux formes : d\u2019une part les r\u00e9gimes sp\u00e9ciaux (tel que les r\u00e9gimes des magistrats civils, r\u00e9gimes des parlementaires, etc.) et d\u2019autre part par le personnel non encore effectivement transf\u00e9r\u00e9 \u00e0 la CNSSAP.

La m\u00e9canisation est entendue comme l\u2019int\u00e9gration administrative et salariale dans le syst\u00e8me de paie de l\u2019\u00c9tat. Elle facilite la retenue r\u00e9guli\u00e8re des cotisations et le passage \u00e0 une couverture contributive effective par la CNSSAP. Toutefois, l\u2019absence de m\u00e9canisation totale des agents publics de l\u2019\u00c9tat implique qu\u2019une partie des travailleurs ne sont ni couverts par le syst\u00e8me contributif de la CNSSAP, ni par un r\u00e9gime sp\u00e9cial ou octroy\u00e9."""
changes.append((f_carto, old15, new15, "D15-seconde-categorie"))

# DIFF #16: "enti\u00e8rement finances" -> "finances"; derniere phrase
changes.append((f_carto,
    "ils sont enti\u00e8rement financ\u00e9s par des ressources publiques",
    "ils sont financ\u00e9s par des ressources publiques",
    "D16a-entierement"))
changes.append((f_carto,
    "ils sont n\u00e9anmoins recens\u00e9s ici car ils constituent, pour les populations concern\u00e9es, la seule forme de protection sociale accessible.",
    "D\u00e9cision a \u00e9t\u00e9 cependant prise d\u2019int\u00e9grer le programme des cantines scolaires du PAM dans la protection sociale des enfants.",
    "D16b-PAM"))

# =============================================================
# DIFF #20 — 4.3_age_actif.md: "Protection maternite" -> "Beneficiaires de prestations de maternite"
# =============================================================
f43 = "03_chapitres/chapitre_4/4.3_age_actif.md"
changes.append((f43,
    "### Protection maternit\u00e9 <span",
    "### B\u00e9n\u00e9ficiaires de prestations de maternit\u00e9 en esp\u00e8ce <span",
    "D20-titre-maternite"))

# DIFF #21: Note maternite CNSS: enlever la derniere phrase; renommer AT/MP
changes.append((f43,
    "Elle ne doit pas \u00eatre interpr\u00e9t\u00e9e comme un faible recours aux soins obst\u00e9tricaux. Un encadr\u00e9 m\u00e9thodologique sp\u00e9cifique est pr\u00e9vu dans le bulletin pour documenter cette limite.",
    "Elle ne doit pas \u00eatre interpr\u00e9t\u00e9e comme un faible recours aux soins obst\u00e9tricaux.",
    "D21a-note-maternite"))

changes.append((f43,
    "### Accidents du travail et maladies professionnelles <span",
    "### Protection contre les accidents du travail et maladies professionnelles <span",
    "D21b-titre-atmp"))

# DIFF #22: Supprimer la note methodologique AT/MP (tout le bloc)
old22 = """> **Note m\u00e9thodologique \u2014 Couverture AT/MP et d\u00e9nominateur :** Le taux de couverture en accidents du travail et maladies professionnelles (AT/MP) est calcul\u00e9 en rapportant le nombre de cotisants/assur\u00e9s actifs AT/MP \u00e0 la population en emploi (et non \u00e0 la population active). Cette correction m\u00e9thodologique exclut les ch\u00f4meurs, qui ne courent par d\u00e9finition aucun risque d\u2019accident du travail. Le r\u00e9sultat est exprim\u00e9 en % de la population totale, conform\u00e9ment aux standards OIT. Cette approche harmonise le traitement de l\u2019indicateur AT/MP avec celui de l\u2019indicateur handicap/invalidit\u00e9 (ODD 1.3.1). Pour plus de d\u00e9tails, voir section 5 (Indicateurs ODD)."""
new22 = "> **Ad\u00e9quation des indemnit\u00e9s \u2014 Rentes/allocations incapacit\u00e9 AT/MP**"
changes.append((f43, old22, new22, "D22-note-atmp"))

print("Debut de l'application des patches...")
applied = 0
failed = 0
for (filepath, old, new, desc) in changes:
    print(f"\n[{desc}]")
    content = read(filepath)
    if old in content:
        write(filepath, content.replace(old, new, 1))
        applied += 1
    else:
        print(f"  INTROUVABLE: '{old[:100]}'")
        failed += 1

print(f"\n{'='*50}")
print(f"Patches appliques : {applied}")
print(f"Introuvables      : {failed}")