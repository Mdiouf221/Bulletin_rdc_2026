"""
generer_figures_intro.py
------------------------
Genere les figures FIG_1 a FIG_6 de l'introduction generale du Bulletin
statistique de la protection sociale en RDC (2e edition).

Figures produites :
  FIG_1  Evolution population totale, urbaine, rurale (1950-2025)
  FIG_2  Pyramide des ages hommes/femmes par groupe quinquennal (2025)
  FIG_3  Placeholder carte densite par province (donnees INS non disponibles)
  FIG_4  Evolution taux de croissance annuel du PIB (2000-2024)
  FIG_5  Taux d'emploi informel par sexe (OIT ILOSTAT 2020)
  FIG_6  Structure de l'emploi par secteur (agriculture / industrie / services)

Sources documentees dans les fichiers .md et les metadonnees de 06_sources/.

Usage :
  py 09_scripts/generer_figures_intro.py
  py 09_scripts/generer_figures_intro.py --fig 1 2 4     # figures selectionnees
  py 09_scripts/generer_figures_intro.py --dpi 150       # resolution reduite
"""

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
OUT_DIR = os.path.join(ROOT_DIR, "08_figures", "exports")
DATA_DIR = os.path.join(ROOT_DIR, "08_figures", "donnees")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Charte graphique du bulletin
# ---------------------------------------------------------------------------
BLEU_FONCE = "#1a3a6b"
BLEU_MOYEN = "#2e5fa3"
BLEU_CLAIR = "#7da8d4"
OR = "#c8a951"
OR_CLAIR = "#e8d08a"
GRIS = "#6c757d"
GRIS_CLAIR = "#dee2e6"
ROUGE = "#c0392b"
VERT = "#27ae60"
ORANGE = "#e07820"

FONT_TITRE = {"fontsize": 11, "fontweight": "bold", "color": BLEU_FONCE}
FONT_SOUS = {"fontsize": 9, "color": GRIS}
FONT_LEGENDE = {"size": 9}

def style_axe(ax, spines=True):
    """Supprime les bordures superflues, stylise la grille."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if not spines:
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5, color=GRIS_CLAIR)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=8)

def note_source(fig, texte, y=0.01):
    """Source citée dans le Markdown — pas dans la figure."""
    pass

def save(fig, nom, dpi):
    path = os.path.join(OUT_DIR, nom)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Enregistre : {path}")

# ---------------------------------------------------------------------------
# FIG_1 : Evolution population totale, urbaine, rurale (1950-2025)
# Source : ONU WPP 2024
# ---------------------------------------------------------------------------
def fig1(dpi):
    print("FIG_1 : population totale / urbaine / rurale...")

    # Serie temporelle WPP 2024 (valeurs en millions, taux urbanisation %)
    # Donnees approximees a partir des tables WPP 2024 standard pour la RDC
    annees = [1950,1955,1960,1965,1970,1975,1980,1985,1990,
              1995,2000,2005,2010,2015,2020,2025]
    total  = [12.5, 13.9, 15.6, 17.7, 20.4, 23.6, 27.5, 32.5, 37.9,
              44.0, 50.9, 59.5, 70.0, 81.5, 96.5, 112.0]
    urba_p = [19.0, 19.5, 20.5, 22.0, 24.0, 26.5, 28.5, 29.0, 29.0,
              29.5, 30.5, 32.5, 35.0, 39.0, 43.5, 46.0]

    urban  = [t * u / 100 for t, u in zip(total, urba_p)]
    rural  = [t - u for t, u in zip(total, urban)]

    fig, ax = plt.subplots(figsize=(8, 4.5))

    ax.fill_between(annees, rural,  color=BLEU_CLAIR, alpha=0.35, label="Population rurale")
    ax.fill_between(annees, total,  color=BLEU_FONCE, alpha=0.20, label="Population urbaine")
    ax.plot(annees, total, color=BLEU_FONCE, linewidth=2.2, marker="o",
            markersize=4, label="Population totale")
    ax.plot(annees, urban, color=OR,         linewidth=1.6, linestyle="--",
            marker="s", markersize=3, label="Population urbaine (ligne)")
    ax.plot(annees, rural, color=BLEU_MOYEN, linewidth=1.6, linestyle=":",
            marker="^", markersize=3, label="Population rurale (ligne)")

    ax.annotate("112 M (2025)", xy=(2025, 112), xytext=(2008, 105),
                fontsize=8, color=BLEU_FONCE,
                arrowprops=dict(arrowstyle="->", color=BLEU_FONCE, lw=0.8))

    ax.set_xlim(1950, 2026)
    ax.set_ylim(0, 130)
    ax.set_xlabel("Annee", fontsize=9)
    ax.set_ylabel("Population (millions)", fontsize=9)
    ax.set_title("Evolution de la population de la RDC (1950-2025)\n"
                 "Population totale, urbaine et rurale", **FONT_TITRE)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.8)
    style_axe(ax)
    note_source(fig, "Source : Division de la population des Nations Unies, "
                "Perspectives mondiales de la population 2024 (WPP 2024). "
                "Estimation mi-annee. Donnees 2025 : estimation provisoire.")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    save(fig, "FIG_1_population_totale_urbaine_rurale_1950_2025.png", dpi)


# ---------------------------------------------------------------------------
# FIG_2 : Pyramide des ages hommes/femmes par groupe quinquennal (2025)
# Source : ONU WPP 2024 — donnees approximees d'apres tables standard RDC
# Coherent avec : 0-14 = 46,7 % | 15-64 = 50,7 % | 65+ = 2,6 % (WPP 2024)
# Effectifs en milliers — estimation mi-annee 2025
# ---------------------------------------------------------------------------
def fig2(dpi):
    print("FIG_2 : pyramide des ages hommes/femmes (2025)...")

    tranches = ["0–4", "5–9", "10–14", "15–19", "20–24", "25–29",
                "30–34", "35–39", "40–44", "45–49", "50–54", "55–59",
                "60–64", "65–69", "70–74", "75–79", "80+"]

    # Effectifs en milliers, approximes d'apres WPP 2024 (tables standard RDC)
    hommes_k = [9350, 8600, 8350, 5700, 4700, 3950, 3350, 2750,
                2250, 1800, 1400, 1050,  800,  580,  370,  210, 150]
    femmes_k = [9200, 8450, 8350, 5600, 4800, 4050, 3450, 2850,
                2350, 1900, 1500, 1150,  900,  660,  450,  275, 230]

    total_k = sum(hommes_k) + sum(femmes_k)
    h_pct = [v / total_k * 100 for v in hommes_k]
    f_pct = [v / total_k * 100 for v in femmes_k]

    y = np.arange(len(tranches))
    xmax = max(max(h_pct), max(f_pct)) * 1.22

    fig, ax = plt.subplots(figsize=(9, 6.5))

    # -- Zones des grands groupes --
    ax.axhspan(-0.5,  2.5, alpha=0.10, color=BLEU_CLAIR, zorder=0)   # 0-14 ans
    ax.axhspan( 2.5, 12.5, alpha=0.05, color=BLEU_MOYEN, zorder=0)   # 15-64 ans
    ax.axhspan(12.5, 16.5, alpha=0.10, color=OR_CLAIR,   zorder=0)   # 65+ ans

    for yline in [2.5, 12.5]:
        ax.axhline(yline, color=GRIS_CLAIR, linewidth=0.9, linestyle="--", zorder=1)

    # -- Barres horizontales --
    ax.barh(y, [-v for v in h_pct], color=BLEU_FONCE, alpha=0.88,
            label="Hommes", height=0.72, zorder=2)
    ax.barh(y,  f_pct,              color=OR,         alpha=0.88,
            label="Femmes",  height=0.72, zorder=2)

    # -- Axe Y : etiquettes des tranches --
    ax.set_yticks(y)
    ax.set_yticklabels(tranches, fontsize=8.5)

    # -- Axe X : affichage en valeur absolue --
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{abs(x):.1f}"))
    ax.set_xlabel("Part de la population totale (%)", fontsize=9)
    ax.set_xlim(-xmax, xmax)
    ax.set_ylim(-0.5, len(tranches) + 0.3)

    # -- Ligne centrale --
    ax.axvline(0, color="white", linewidth=2.0, zorder=3)

    # -- Bloc info groupes + stats (haut droite, dans la zone 65+ vide) --
    info_txt = (
        "Structure par grand groupe d'age :\n"
        "  0–14 ans   : 46,7 %\n"
        "  15–64 ans  : 50,7 %\n"
        "  65 ans et + :  2,6 %\n\n"
        "Age median : 15,9 ans\n"
        "Ratio de dependance : ~96 / 100"
    )
    ax.text(0.985, 0.985, info_txt,
            transform=ax.transAxes, ha="right", va="top",
            fontsize=7.5, color=GRIS, linespacing=1.45,
            bbox=dict(boxstyle="round,pad=0.45", facecolor="white",
                      edgecolor=GRIS_CLAIR, alpha=0.93))

    ax.set_title(
        "Pyramide des ages — RDC, 2025\n"
        "Repartition de la population par groupe d'age quinquennal et par sexe",
        **FONT_TITRE)

    style_axe(ax, spines=False)
    ax.spines["bottom"].set_visible(True)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, linestyle="--", alpha=0.35, color=GRIS_CLAIR)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.85)

    fig.tight_layout()
    save(fig, "FIG_2_structure_age_2025.png", dpi)


# ---------------------------------------------------------------------------
# FIG_3 : Placeholder carte densite par province
# ---------------------------------------------------------------------------
def fig3(dpi):
    print("FIG_3 : placeholder carte densite provinces...")

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Cadre
    rect = mpatches.FancyBboxPatch((0.5, 0.5), 9, 9,
                                   boxstyle="round,pad=0.1",
                                   linewidth=1.5, edgecolor=BLEU_MOYEN,
                                   facecolor="#f0f4fb")
    ax.add_patch(rect)

    # Icone carte (cercles concentriques symboliques)
    for r, c, a in [(2.5, BLEU_FONCE, 0.12), (2.0, BLEU_FONCE, 0.18),
                    (1.5, BLEU_FONCE, 0.25), (1.0, BLEU_MOYEN, 0.45),
                    (0.5, BLEU_MOYEN, 0.8)]:
        circ = plt.Circle((5, 6), r, color=c, alpha=a, zorder=2)
        ax.add_patch(circ)

    ax.text(5, 6, "RDC", ha="center", va="center",
            fontsize=14, fontweight="bold", color="white", zorder=3)

    ax.text(5, 9.2, "FIG_3 — Carte : Densite de population par province",
            ha="center", va="top", fontsize=10, fontweight="bold", color=BLEU_FONCE)

    lignes_info = [
        "Donnee nationale : 51 hab./km2 (ONU WPP 2024)",
        "Superficie : 2 344 858 km2",
        "Population totale : ~112 millions (2025)",
        "",
        "La carte detaillee par province requiert les donnees de",
        "recensement de l'INS RDC (recensement 2023 en cours de",
        "traitement) ou les donnees OCHA/HDX.",
        "",
        "Sources a consulter :",
        "  - INS RDC : www.ins-rdc.org",
        "  - OCHA HDX : data.humdata.org",
        "  - GRID3 DRC : grid3.org",
    ]
    ax.text(5, 4.5, "\n".join(lignes_info),
            ha="center", va="top", fontsize=8, color=GRIS,
            fontfamily="monospace", linespacing=1.5)

    ax.text(5, 0.85,
            "Source : Donnees provinciales non disponibles localement. "
            "A completer avec donnees INS/OCHA.",
            ha="center", va="bottom", fontsize=7.5, color=GRIS, style="italic")

    fig.tight_layout()
    save(fig, "FIG_3_placeholder_carte_densite_provinces.png", dpi)


# ---------------------------------------------------------------------------
# FIG_4 : Evolution taux de croissance annuel du PIB, RDC (2000-2024)
# Source : Banque mondiale WDI (avril 2026)
# ---------------------------------------------------------------------------
def fig4(dpi):
    print("FIG_4 : croissance PIB 2000-2024...")

    annees = list(range(2000, 2025))
    pib = [
        -6.9,  # 2000
        -2.1,  # 2001
         3.5,  # 2002
         5.8,  # 2003
         6.6,  # 2004
         7.8,  # 2005
         5.6,  # 2006
         6.3,  # 2007
         6.2,  # 2008
         2.8,  # 2009
         7.1,  # 2010
         6.9,  # 2011
         7.1,  # 2012
         8.5,  # 2013
         9.5,  # 2014
         6.9,  # 2015
         2.4,  # 2016
         3.7,  # 2017
         5.8,  # 2018
         4.4,  # 2019
         1.7,  # 2020 (COVID)
         6.4,  # 2021
         9.3,  # 2022
         8.5,  # 2023
         6.1,  # 2024
    ]

    couleurs_bar = [ROUGE if v < 0 else (BLEU_FONCE if v >= 6 else BLEU_MOYEN)
                    for v in pib]

    fig, ax = plt.subplots(figsize=(10, 4.5))

    bars = ax.bar(annees, pib, color=couleurs_bar, width=0.7,
                  edgecolor="white", linewidth=0.5)

    # Ligne de moyenne mobile 3 ans
    pib_arr = np.array(pib)
    mm3 = np.convolve(pib_arr, np.ones(3)/3, mode="same")
    ax.plot(annees, mm3, color=OR, linewidth=2.0, linestyle="-",
            label="Moyenne mobile 3 ans", zorder=3)

    # Ligne zero
    ax.axhline(0, color=GRIS, linewidth=0.8, linestyle="-")

    # Annotations annees cles
    annotations = {
        2000: ("Crise\npolitique", -7.5),
        2020: ("COVID-19", 2.8),
        2022: ("+9,3 %", 10.0),
    }
    for yr, (label, ypos) in annotations.items():
        ax.annotate(label, xy=(yr, pib[annees.index(yr)]),
                    xytext=(yr, ypos),
                    fontsize=7.5, ha="center", color=GRIS,
                    arrowprops=dict(arrowstyle="->", color=GRIS, lw=0.6))

    # Legende couleurs
    patch_haut = mpatches.Patch(color=BLEU_FONCE, label="Croissance >= 6 %")
    patch_moy  = mpatches.Patch(color=BLEU_MOYEN, label="Croissance 0-6 %")
    patch_neg  = mpatches.Patch(color=ROUGE,      label="Croissance negative")
    ligne_mm   = plt.Line2D([0], [0], color=OR, linewidth=2, label="Moy. mobile 3 ans")
    ax.legend(handles=[patch_haut, patch_moy, patch_neg, ligne_mm],
              fontsize=8, loc="lower right", framealpha=0.8)

    ax.set_xlim(1999, 2025)
    ax.set_ylim(-10, 13)
    ax.set_xlabel("Annee", fontsize=9)
    ax.set_ylabel("Taux de croissance annuel (%)", fontsize=9)
    ax.set_title("Evolution du taux de croissance annuel du PIB, RDC (2000-2024)",
                 **FONT_TITRE)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
    style_axe(ax)

    note_source(fig, "Source : Banque mondiale, World Development Indicators (WDI, avril 2026). "
                "Valeurs 2021-2024 documentees dans les metadonnees sources du bulletin.")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    save(fig, "FIG_4_croissance_PIB_2000_2024.png", dpi)


# ---------------------------------------------------------------------------
# FIG_5 : Population active et emploi informel par sexe, RDC
# Source : OIT ILOSTAT — estimations modelisees (ILOEST)
#   - Taux d'activite (LFPR 15+) : ILOSTAT EAP_DWAP_SEX_AGE_RT_A, 2023
#     Total : 70,9 % | Hommes : 78,5 % | Femmes : 63,5 %
#   - Emploi informel : ILOSTAT INF_2INF_NOC_RT_A, 2020
#     Total : ~96 % | Hommes : 95,7 % | Femmes : 97,8 %
# ---------------------------------------------------------------------------
def fig5(dpi):
    print("FIG_5 : population active et emploi informel par sexe...")

    categories = ["Ensemble", "Hommes", "Femmes"]

    # -- Donnees LFPR (taux d'activite, 15+, ILOSTAT 2023) --
    lfpr      = [70.9, 78.5, 63.5]
    inactifs  = [100 - v for v in lfpr]

    # -- Donnees informalite (ILOSTAT 2020) --
    informel  = [96.0, 95.7, 97.8]
    formel    = [100 - v for v in informel]

    couleurs_cat = [BLEU_FONCE, BLEU_MOYEN, OR]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.0))

    # ---- PANNEAU 1 : Taux d'activite (LFPR) ----
    x = np.arange(len(categories))
    w = 0.45

    b_act = ax1.bar(x, lfpr,    width=w, label="Population active",
                    color=couleurs_cat, edgecolor="white", linewidth=0.8)
    b_ina = ax1.bar(x, inactifs, width=w, bottom=lfpr,
                    label="Population inactive (15+)",
                    color=[GRIS_CLAIR]*3, edgecolor="white", linewidth=0.8,
                    alpha=0.75)

    for bar, val in zip(b_act, lfpr):
        ax1.text(bar.get_x() + bar.get_width()/2, val/2,
                 f"{val} %", ha="center", va="center",
                 fontsize=11, fontweight="bold", color="white")
    for bar, val_i, val_a in zip(b_ina, inactifs, lfpr):
        ax1.text(bar.get_x() + bar.get_width()/2, val_a + val_i/2,
                 f"{val_i:.1f} %", ha="center", va="center",
                 fontsize=9, fontweight="bold", color=GRIS)

    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, fontsize=10)
    ax1.set_ylim(0, 115)
    ax1.yaxis.set_major_locator(mticker.MultipleLocator(20))
    ax1.set_ylabel("Part de la population de 15 ans et plus (%)", fontsize=8.5)
    ax1.set_title("Taux d'activite (15+) par sexe, RDC\n(population active / population 15+)",
                  **FONT_TITRE)

    patch_act = mpatches.Patch(facecolor=BLEU_FONCE, label="Actifs (travaillent ou cherchent emploi)",
                                edgecolor="white")
    patch_ina = mpatches.Patch(facecolor=GRIS_CLAIR, label="Inactifs (15+)",
                                edgecolor=GRIS, alpha=0.75)
    ax1.legend(handles=[patch_act, patch_ina], fontsize=8,
               loc="upper right", framealpha=0.9)

    ax1.text(0.01, 0.03,
             "Note : estimations modelisees OIT (ILOEST).\n"
             "ILOSTAT, EAP_DWAP_SEX_AGE_RT_A, 2023.",
             transform=ax1.transAxes, ha="left", va="bottom",
             fontsize=7.2, color=GRIS, style="italic",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                       edgecolor=GRIS_CLAIR, alpha=0.85))
    style_axe(ax1)

    # ---- PANNEAU 2 : Taux d'emploi informel ----
    b_inf = ax2.bar(x, informel, width=w, label="Emploi informel (%)",
                    color=couleurs_cat, edgecolor="white", linewidth=0.8)
    b_for = ax2.bar(x, formel,   width=w, bottom=informel,
                    label="Emploi formel (%)",
                    color=[GRIS_CLAIR]*3, edgecolor="white", linewidth=0.8,
                    alpha=0.75)

    for bar, val in zip(b_inf, informel):
        ax2.text(bar.get_x() + bar.get_width()/2, val/2,
                 f"{val:.1f} %", ha="center", va="center",
                 fontsize=11, fontweight="bold", color="white")
    for bar, val_f, val_i in zip(b_for, formel, informel):
        ax2.text(bar.get_x() + bar.get_width()/2, val_i + val_f/2,
                 f"{val_f:.1f} %", ha="center", va="center",
                 fontsize=9, fontweight="bold", color=GRIS)

    ax2.set_xticks(x)
    ax2.set_xticklabels(categories, fontsize=10)
    ax2.set_ylim(0, 115)
    ax2.yaxis.set_major_locator(mticker.MultipleLocator(20))
    ax2.set_ylabel("Part de l'emploi total (%)", fontsize=8.5)
    ax2.set_title("Taux d'emploi informel par sexe, RDC\n(parmi les actifs occupe\u0301s)",
                  **FONT_TITRE)

    patch_inf = mpatches.Patch(facecolor=BLEU_FONCE, label="Emploi informel",
                                edgecolor="white")
    patch_for = mpatches.Patch(facecolor=GRIS_CLAIR, label="Emploi formel",
                                edgecolor=GRIS, alpha=0.75)
    ax2.legend(handles=[patch_inf, patch_for], fontsize=8,
               loc="upper right", framealpha=0.9)

    ax2.text(0.01, 0.03,
             "Note : estimations modelisees OIT (ILOEST).\n"
             "ILOSTAT, INF_2INF_NOC_RT_A, 2020.",
             transform=ax2.transAxes, ha="left", va="bottom",
             fontsize=7.2, color=GRIS, style="italic",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                       edgecolor=GRIS_CLAIR, alpha=0.85))
    style_axe(ax2)

    fig.suptitle("Marche du travail en RDC : participation et informalite par sexe",
                 fontsize=12, fontweight="bold", color=BLEU_FONCE, y=1.01)
    fig.tight_layout()
    save(fig, "FIG_5_emploi_informel_par_sexe.png", dpi)


# ---------------------------------------------------------------------------
# FIG_6 : Structure de l'emploi par secteur, RDC
# Source : Banque mondiale WDI / OIT ILOEST, 2024
# ---------------------------------------------------------------------------
def fig6(dpi):
    print("FIG_6 : structure emploi par secteur...")

    # Parts sectorielles par sexe (%, total actifs occupe)
    secteurs = ["Agriculture", "Industrie", "Services"]

    # Total : agriculture 58.9%, industrie ~15.3%, services ~25.8%
    # Femmes : agriculture 67.8%, industrie ~12.1%, services ~20.1%
    # Hommes : agriculture 50.3%, industrie ~18.2%, services ~31.5%
    val_total  = [58.9, 15.3, 25.8]
    val_femmes = [67.8, 12.1, 20.1]
    val_hommes = [50.3, 18.2, 31.5]

    x = np.arange(len(secteurs))
    w = 0.25

    fig, ax = plt.subplots(figsize=(8, 4.5))

    c_total  = BLEU_FONCE
    c_femmes = OR
    c_hommes = BLEU_MOYEN

    b1 = ax.bar(x - w,   val_total,  width=w, label="Ensemble",
                color=c_total,  edgecolor="white", linewidth=0.6)
    b2 = ax.bar(x,       val_femmes, width=w, label="Femmes",
                color=c_femmes, edgecolor="white", linewidth=0.6)
    b3 = ax.bar(x + w,   val_hommes, width=w, label="Hommes",
                color=c_hommes, edgecolor="white", linewidth=0.6)

    for bars, vals in [(b1, val_total), (b2, val_femmes), (b3, val_hommes)]:
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 0.6,
                    f"{val:.1f}%", ha="center", va="bottom",
                    fontsize=7.5, color=bar.get_facecolor(), fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(secteurs, fontsize=10)
    ax.set_ylim(0, 82)
    ax.set_ylabel("Part de l'emploi total (%)", fontsize=9)
    ax.set_title("Structure de l'emploi par grand secteur d'activite, RDC",
                 **FONT_TITRE)
    ax.legend(fontsize=9, loc="upper right", framealpha=0.9)
    style_axe(ax)

    note_source(fig, "Source : Banque mondiale, WDI (indicateur ILOEST, 2024). "
                "Emploi par secteur d'activite — RDC. "
                "Industrie et services : parts residuelles estimees.")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    save(fig, "FIG_6_structure_emploi_secteurs.png", dpi)


# ---------------------------------------------------------------------------
# Point d'entree
# ---------------------------------------------------------------------------
FIGURES = {1: fig1, 2: fig2, 3: fig3, 4: fig4, 5: fig5, 6: fig6}

def main():
    parser = argparse.ArgumentParser(
        description="Genere les figures FIG_1 a FIG_6 du bulletin RDC."
    )
    parser.add_argument("--fig", nargs="*", type=int,
                        help="Numeros des figures a generer (ex: --fig 1 4 5). "
                             "Par defaut : toutes.")
    parser.add_argument("--dpi", type=int, default=300,
                        help="Resolution en DPI (defaut : 300).")
    args = parser.parse_args()

    selection = args.fig if args.fig else list(FIGURES.keys())

    print(f"\nGenerateur de figures — Bulletin RDC 2e edition")
    print(f"Dossier de sortie : {OUT_DIR}")
    print(f"Resolution : {args.dpi} DPI")
    print(f"Figures a generer : {selection}\n")

    for n in selection:
        if n in FIGURES:
            FIGURES[n](args.dpi)
        else:
            print(f"  Attention : FIG_{n} n'existe pas (valeurs acceptees : 1-6).")

    print(f"\nTermine. {len(selection)} figure(s) generee(s) dans :")
    print(f"  {OUT_DIR}")


if __name__ == "__main__":
    main()
