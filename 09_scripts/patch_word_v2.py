# -*- coding: utf-8 -*-
"""Patch v2 - apostrophes corrigees (U+0027)."""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\M.Diouf\OneDrive\Bureau\RDC Bulletin V1\Bulletin_rdc_2026_agents"

def read(rel):
    with open(os.path.join(BASE, rel), encoding='utf-8-sig') as f: return f.read()

def write(rel, content):
    with open(os.path.join(BASE, rel), 'w', encoding='utf-8') as f: f.write(content)

def patch(rel, old, new, desc):
    content = read(rel)
    if old in content:
        write(rel, content.replace(old, new, 1))
        print(f"  OK [{desc}]")
        return True
    else:
        print(f"  INTROUVABLE [{desc}]")
        return False

applied = failed = 0

def do(rel, old, new, desc):
    global applied, failed
    if patch(rel, old, new, desc):
        applied += 1
    else:
        failed += 1

f_demo  = "02_introduction_generale/0_1_contexte_demographique.md"
f_eco   = "02_introduction_generale/0_2_contexte_economique_emploi.md"
f_strat = "02_introduction_generale/0_3_strategie_donnees_statistiques.md"
f_carto = "03_chapitres/chapitre_2/2_1_cartographie_tableaux.md"
f43     = "03_chapitres/chapitre_4/4.3_age_actif.md"
f44     = "03_chapitres/chapitre_4/4.4_enfants_familles.md"
f45     = "03_chapitres/chapitre_4/4.5_invalidite.md"
f46     = "03_chapitres/chapitre_4/4.6_deces_survie.md"
f47     = "03_chapitres/chapitre_4/4.7_sante.md"
f48     = "03_chapitres/chapitre_4/4.8_depenses_financement.md"
f49     = "03_chapitres/chapitre_4/4.9_odd_131.md"

# ========== D6 ==========
do(f_demo,
   " Ces constats, combin\u00e9s aux donn\u00e9es \u00e9conomiques pr\u00e9sent\u00e9es dans la section suivante, permettront d'appr\u00e9cier plus finement les conditions dans lesquelles l'extension de la couverture devra se r\u00e9aliser.",
   "",
   "D6-derniere-phrase-demo")

# ========== D8a: femmes ==========
do(f_eco,
   "chez les femmes, ces derni\u00e8res \u00e9tant plus fr\u00e9quemment maintenues hors du march\u00e9 du travail visible du fait de responsabilit\u00e9s familiales et de barri\u00e8res d'acc\u00e8s \u00e0 l'emploi.",
   "chez les femmes.",
   "D8a-femmes-marche-travail")

# ========== D8b: predominance ==========
do(f_eco,
   "pr\u00e9dominance \u00e9crasante de l'emploi informel",
   "pr\u00e9dominance de l'emploi informel",
   "D8b-predominance")

# ========== D9: dernier phrase risques pro ==========
do(f_eco,
   " Ces r\u00e9alit\u00e9s renforcent l'importance d'un suivi statistique rigoureux des affili\u00e9s, des cotisants actifs et des victimes d'accidents du travail \u2014 donn\u00e9es au c\u0153ur du pr\u00e9sent bulletin.",
   "",
   "D9-risques-pro-derniere-phrase")

# ========== D10: majorite travailleurs ==========
do(f_eco,
   " La majorit\u00e9 des travailleurs n'est pas enregistr\u00e9e aupr\u00e8s des r\u00e9gimes contributifs formels, ce qui limite \u00e0 la fois l'assiette de cotisation des institutions et l'acc\u00e8s effectif aux prestations pour les assur\u00e9s potentiels.",
   "",
   "D10-enjeux-extension")

# ========== D11a: periode ==========
do(f_strat,
   "jusqu'\u00e0 d\u00e9cembre 2025",
   "2019\u20132025",
   "D11a-periode")

# ========== D12: desagregation ==========
do(f_strat,
   "\u00e2ge, province ou secteur \u2014 n'est",
   "\u00e2ge \u2014 n'est",
   "D12-desagregation")

# ========== D13: quatre -> cinq ==========
old13 = "Cette cartographie distingue quatre grandes cat\u00e9gories : la s\u00e9curit\u00e9 sociale contributive obligatoire, qui couvre les travailleurs du secteur priv\u00e9 formel via la CNSS et les agents publics affili\u00e9s \u00e0 la CNSSAP (Tableau 2.1) ; les dispositifs statutaires financ\u00e9s directement par le budget de l'\u00c9tat, qui regroupent les r\u00e9gimes sp\u00e9ciaux formellement constitu\u00e9s et, lorsqu'elle est effectivement document\u00e9e, la protection budg\u00e9taire d'autres agents publics hors CNSSAP (Tableau 2.2) ; la protection de la sant\u00e9, organis\u00e9e par segment de population (Tableau 2.3) ; les programmes d'assistance sociale et initiatives non contributives destin\u00e9s aux populations non couvertes par les r\u00e9gimes formels (Tableau 2.4) ; enfin, un ensemble de politiques sectorielles \u00e0 dimension protectrice \u2014 gratuit\u00e9s, programmes d'activation par l'emploi, acc\u00e8s subventionn\u00e9 aux services de base \u2014 dont la finalit\u00e9 sociale est \u00e9tablie mais qui ne rel\u00e8vent pas \u00e0 proprement parler de l'assistance sociale (Tableau 2.5, mention contextuelle)."
new13 = """Cette cartographie distingue cinq grandes cat\u00e9gories :

1) la s\u00e9curit\u00e9 sociale contributive obligatoire, hors sant\u00e9, qui couvre les travailleurs du secteur priv\u00e9 formel via la CNSS et les agents publics affili\u00e9s \u00e0 la CNSSAP (Tableau 2.1) ;

2) les dispositifs statutaires, hors sant\u00e9, financ\u00e9s directement par le budget de l'\u00c9tat, qui regroupent les r\u00e9gimes sp\u00e9ciaux formellement constitu\u00e9s et la protection des agents publics qui ne sont pas encore transf\u00e9r\u00e9s formellement \u00e0 la CNSSAP (Tableau 2.2) ;

3) la protection de la sant\u00e9, organis\u00e9e par segment de population (Tableau 2.3) ;

4) les programmes d'assistance sociale et initiatives non contributives destin\u00e9s aux populations non couvertes par les r\u00e9gimes formels (Tableau 2.4) ;

5) enfin, un ensemble de politiques sectorielles \u00e0 dimension protectrice \u2014 gratuit\u00e9s, programmes d'activation par l'emploi, acc\u00e8s subventionn\u00e9 aux services de base \u2014 dont la finalit\u00e9 sociale est \u00e9tablie mais qui ne rel\u00e8vent pas \u00e0 proprement parler de l'assistance sociale (Tableau 2.5, mention contextuelle)."""
do(f_carto, old13, new13, "D13-cinq-categories")

# ========== D14: titre dispositifs ==========
do(f_carto,
   "### Dispositifs statutaires financ\u00e9s directement par le budget de l'\u00c9tat <span",
   "### 2) Dispositifs statutaires financ\u00e9s directement par le budget de l'\u00c9tat <span",
   "D14-titre-dispositifs")

# ========== D15: seconde categorie ==========
old15 = "La seconde cat\u00e9gorie recouvre les **agents publics hors CNSSAP dont la protection est effectivement assur\u00e9e par un dispositif statutaire financ\u00e9 directement par le budget de l'\u00c9tat**, sans s'inscrire dans un r\u00e9gime sp\u00e9cial formellement constitu\u00e9. La m\u00e9canisation \u2014 entendue comme l'int\u00e9gration administrative et salariale dans le syst\u00e8me de paie de l'\u00c9tat \u2014 facilite la retenue r\u00e9guli\u00e8re des cotisations et le passage \u00e0 une couverture contributive effective par la CNSSAP. Toutefois, l'absence de m\u00e9canisation ou d'affiliation \u00e0 la CNSSAP ne suffit pas, \u00e0 elle seule, \u00e0 \u00e9tablir l'existence d'une couverture budg\u00e9taire effective. Celle-ci doit \u00eatre attest\u00e9e par des droits identifiables, une population d\u00e9nombrable et une prise en charge budg\u00e9taire document\u00e9e. Qualifier cette population de \u00ab r\u00e9gime sp\u00e9cial \u00bb serait inexact : elle rel\u00e8ve des dispositions g\u00e9n\u00e9rales applicables aux agents de l'\u00c9tat, et non d'un r\u00e9gime sp\u00e9cial distinct."
new15 = """La seconde cat\u00e9gorie recouvre les **agents publics hors CNSSAP dont la protection est encore effectivement assur\u00e9e par un dispositif statutaire financ\u00e9 directement par le budget de l'\u00c9tat**.

Historiquement, la protection sociale des agents de l'\u00c9tat \u00e9tait assur\u00e9e par un syst\u00e8me de r\u00e9gimes dit \u00ab octroy\u00e9s \u00bb : un ensemble de prestations (sous condition d'\u00e9ligibilit\u00e9) \u00e9tait garanti aux agents de l'\u00c9tat et directement financ\u00e9 par le budget national, sans recourir \u00e0 un m\u00e9canisme assuranciel. Un programme de transf\u00e8rement de ces effectifs sous la responsabilit\u00e9 de la CNSSAP est en cours depuis 2022. Ce m\u00e9canisme est d\u00e9sign\u00e9 comme la r\u00e9forme de transf\u00e8rement.

Cependant, la fourniture de protection sociale par un syst\u00e8me non contributif et non assuranciel persiste sous deux formes : d'une part les r\u00e9gimes sp\u00e9ciaux (tel que les r\u00e9gimes des magistrats civils, r\u00e9gimes des parlementaires, etc.) et d'autre part par le personnel non encore effectivement transf\u00e9r\u00e9 \u00e0 la CNSSAP.

La m\u00e9canisation est entendue comme l'int\u00e9gration administrative et salariale dans le syst\u00e8me de paie de l'\u00c9tat. Elle facilite la retenue r\u00e9guli\u00e8re des cotisations et le passage \u00e0 une couverture contributive effective par la CNSSAP."""
do(f_carto, old15, new15, "D15-seconde-categorie")

# ========== D16a: entierement ==========
do(f_carto,
   "ils sont enti\u00e8rement financ\u00e9s par des ressources publiques",
   "ils sont financ\u00e9s par des ressources publiques",
   "D16a-entierement")

# ========== D22: note AT/MP ==========
old22 = "> **Note m\u00e9thodologique \u2014 Couverture AT/MP et d\u00e9nominateur :** Le taux de couverture en accidents du travail et maladies professionnelles (AT/MP) est calcul\u00e9 en rapportant le nombre de cotisants/assur\u00e9s actifs AT/MP \u00e0 la population en emploi (et non \u00e0 la population active). Cette correction m\u00e9thodologique exclut les ch\u00f4meurs, qui ne courent par d\u00e9finition aucun risque d'accident du travail. Le r\u00e9sultat est exprim\u00e9 en % de la population totale, conform\u00e9ment aux standards OIT. Cette approche harmonise le traitement de l'indicateur AT/MP avec celui de l'indicateur handicap/invalidit\u00e9 (ODD 1.3.1). Pour plus de d\u00e9tails, voir section 5 (Indicateurs ODD)."
do(f43, old22,
   "> **Ad\u00e9quation des indemnit\u00e9s \u2014 Rentes/allocations incapacit\u00e9 AT/MP**",
   "D22-note-atmp")

# ========== CHAPTER 4 remaining changes ==========

# Lecture des autres fichiers chapitres 4
def try_files(filenames, old, new, desc):
    """Try multiple possible filename variants."""
    for fn in filenames:
        fp = os.path.join(BASE, fn)
        if os.path.exists(fp):
            do(fn, old, new, desc)
            return
    print(f"  FICHIER MANQUANT [{desc}]")

# D24: 4.4 enfants
if os.path.exists(os.path.join(BASE, f44)):
    do(f44,
       "Programmes non contributifs ciblant enfants et familles",
       "Enfants b\u00e9n\u00e9ficiaires de prestations non contributives",
       "D24a-titre-enfants-nc")
    do(f44,
       "ainsi que les donn\u00e9es de couverture disponibles pour la p\u00e9riode consid\u00e9r\u00e9e.",
       "consid\u00e9r\u00e9 comme p\u00e9renne bien que non statutaire.",
       "D24b-texte-enfants")
else:
    print(f"  FICHIER ABSENT: {f44}")

# D25-D27: 4.5 invalidite
if os.path.exists(os.path.join(BASE, f45)):
    do(f45,
       "### Pensions d'invalidit\u00e9 \u2014 r\u00e9gimes contributifs <span",
       "### B\u00e9n\u00e9ficiaires de pensions d'invalidit\u00e9 \u2014 r\u00e9gimes contributifs <span",
       "D25-titre-invalidite")
    do(f45,
       "Dans les r\u00e9gimes de la CNSS, la pension d'invalidit\u00e9 et la pension de vieillesse sont fix\u00e9es au m\u00eame montant unitaire mensuel par arr\u00eat\u00e9.",
       "Dans les r\u00e9gimes de la CNSS, la pension minimale d'invalidit\u00e9 et la pension de vieillesse sont fix\u00e9es au m\u00eame montant unitaire mensuel par arr\u00eat\u00e9.",
       "D26a-pension-minimale")
    do(f45,
       "Ad\u00e9quation de la pension d'invalidit\u00e9 CNSS et seuil de pauvret\u00e9 (2019\u20132025)",
       "Ad\u00e9quation de la pension d'invalidit\u00e9 minimale de CNSS et de la CNSSAP et seuil de pauvret\u00e9 (2019\u20132025)",
       "D26b-tableau-titre")
    do(f45,
       "### Programmes non contributifs pour les personnes handicap\u00e9es <span",
       "### B\u00e9n\u00e9ficiaires des programmes non contributifs pour les personnes handicap\u00e9es <span",
       "D27-titre-handicapes")
else:
    print(f"  FICHIER ABSENT: {f45}")

# D28: 4.6 deces
if os.path.exists(os.path.join(BASE, f46)):
    do(f46,
       "### Pensions de survie et prestations aux ayants droit <span",
       "### B\u00e9n\u00e9ficiaires de pensions de survie et prestations aux ayants droit <span",
       "D28-titre-survie")
else:
    print(f"  FICHIER ABSENT: {f46}")

# D29-D31: 4.7 sante
if os.path.exists(os.path.join(BASE, f47)):
    do(f47,
       "### Le FSS \u2014 Fonds de Solidarit\u00e9 de Sant\u00e9 <span",
       "### Protection statutaire en mati\u00e8re de sant\u00e9 : Le FSS \u2014 Fonds de Solidarit\u00e9 de Sant\u00e9 <span",
       "D29-FSS-titre")
    do(f47,
       "### La MESP \u2014 Mutuelle des Enseignants de l'EPST <span",
       "### Protection statutaire en mati\u00e8re de sant\u00e9 : La MESP \u2014 Mutuelle des Enseignants de l'EPST <span",
       "D30a-MESP-titre")
    do(f47,
       "La Mutuelle des Enseignants de l'Enseignement Primaire, Secondaire et Technique (MESP) est un r\u00e9gime de sant\u00e9 statutaire obligatoire ant\u00e9rieur au FSS. Elle couvre les enseignants relevant du minist\u00e8re de l'EPST selon un m\u00e9canisme contributif.",
       "La Mutuelle des Enseignants de l'Enseignement Primaire, Secondaire et Technique (MESP) est la seule mutuelle de sant\u00e9 statutaire et obligatoire. Elle est ant\u00e9rieure au FSS et couvre les enseignants relevant du minist\u00e8re de l'EPST selon un m\u00e9canisme contributif.",
       "D30b-MESP-texte")
    do(f47,
       "### Mutuelles de sant\u00e9 volontaires <span",
       "### Protection volontaire en mati\u00e8re de sant\u00e9 : Les mutuelles de sant\u00e9 volontaires <span",
       "D31a-mutuelles-titre")
    do(f47,
       "Elles incluent notamment les structures d'assurance m\u00e9dicale du secteur priv\u00e9 (type SESOPA pour les secteurs p\u00e9trolier et bancaire) ainsi que les mutuelles communautaires et associatives. Ces dispositifs sont mentionn\u00e9s \u00e0 titre contextuel : ils ne font pas l'objet d'une collecte statistique consolid\u00e9e dans le cadre de la pr\u00e9sente \u00e9dition du bulletin et leurs donn\u00e9es de couverture ne sont pas agr\u00e9g\u00e9es dans les indicateurs.",
       "Elles incluent notamment les structures d'assurance m\u00e9dicale du secteur priv\u00e9 ainsi que les mutuelles communautaires et associatives sous l'\u00e9gide du SESOPA.",
       "D31b-mutuelles-texte")
else:
    print(f"  FICHIER ABSENT: {f47}")

# D32-D33: 4.8 depenses
if os.path.exists(os.path.join(BASE, f48)):
    do(f48,
       "cotisations salariales et patronales. Le financement des r\u00e9gimes non contributifs",
       "cotisations salariales et patronales comprenant l'\u00c9tat employeur. Le financement des r\u00e9gimes non contributifs",
       "D32-cotisations-etat")
    do(f48,
       "conform\u00e9ment aux standards de l'OIT. Les valeurs sont",
       "conform\u00e9ment aux standards de l'OIT,. Les valeurs sont",
       "D33-depenses-OIT")
else:
    print(f"  FICHIER ABSENT: {f48}")

# D35: 4.9 odd_131
if os.path.exists(os.path.join(BASE, f49)):
    old35 = "L'indicateur ODD 1.3.1 mesure la proportion de la population effectivement couverte par au moins une prestation de protection sociale. Il est calcul\u00e9 selon la m\u00e9thodologie de l'OIT, qui distingue la couverture l\u00e9gale (droit formel \u00e0 une prestation) de la couverture effective (b\u00e9n\u00e9fice r\u00e9el d'une prestation). Seule la couverture effective est retenue dans le pr\u00e9sent bulletin."
    new35 = """L'indicateur 1.3.1 des Objectifs de D\u00e9veloppement Durable (ODD) surveille l'am\u00e9lioration mondiale et r\u00e9gionale de la couverture de protection sociale. L'indicateur global mesure la proportion de la population prot\u00e9g\u00e9e par au moins une branche de la s\u00e9curit\u00e9 sociale.

L'indicateur ODD 1.3.1 mesure la proportion de la population effectivement couverte par au moins une prestation de protection sociale. Il est calcul\u00e9 selon la m\u00e9thodologie de l'OIT, qui distingue la couverture l\u00e9gale (droit formel \u00e0 une prestation) de la couverture effective (b\u00e9n\u00e9fice r\u00e9el d'une prestation). Seule la couverture effective est retenue dans le pr\u00e9sent bulletin."""
    do(f49, old35, new35, "D35-odd-intro")

    # D36: supprimer note AT/MP
    old36 = "> **Note m\u00e9thodologique :** \u00c0 partir de la pr\u00e9sente \u00e9dition, le sous-indicateur AT/MP (accidents du travail et maladies professionnelles) est calcul\u00e9 selon la m\u00e9thodologie r\u00e9vis\u00e9e du BIT : le num\u00e9rateur (assur\u00e9s actifs AT/MP) est rapport\u00e9 \u00e0 la population en emploi (et non \u00e0 la population active), et le r\u00e9sultat est exprim\u00e9 en % de la population totale (conform\u00e9ment aux standards ODD 1.3.1). Cette correction assure la comparabilit\u00e9 avec d'autres indicateurs de couverture et exclut les ch\u00f4meurs, qui ne courent aucun risque professionnel. Pour plus de d\u00e9tails, voir l'encadr\u00e9 m\u00e9thodologique \u00e0 la fin de la section 4.3."
    do(f49, old36, "", "D36-supprimer-note-atmp")
else:
    print(f"  FICHIER ABSENT: {f49}")

print(f"\n{'='*50}")
print(f"Patches appliques : {applied}")
print(f"Introuvables      : {failed}")