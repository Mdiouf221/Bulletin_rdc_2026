"""
generer_figures_intro.py
------------------------
Genere les figures FIG_1 a FIG_6 de l'introduction generale du Bulletin
statistique de la protection sociale en RDC (2e edition).

Figures produites :
  FIG_1  Evolution population totale, urbaine, rurale (1950-2025)
  FIG_2  Structure par grand groupe d'age (2025)
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
    """Ajoute une note source en bas de figure."""
    fig.text(0.5, y, texte, ha="center", fontsize=7.5, color=GRIS,
             style="italic", wrap=True)

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
# FIG_2 : Structure par grand groupe d'age (2025)
# Source : ONU WPP 2024
# ---------------------------------------------------------------------------
def fig2(dpi):
    print("FIG_2 : structure par groupe d'age...")

    groupes = ["0-14 ans\n(jeunes)", "15-64 ans\n(actifs potentiels)", "65 ans et plus\n(seniors)"]
    valeurs = [46.7, 50.7, 2.6]
    couleurs = [BLEU_CLAIR, BLEU_FONCE, OR]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4.5))

    # -- Histogramme --
    bars = ax1.bar(groupes, valeurs, color=couleurs, width=0.5, edgecolor="white", linewidth=0.8)
    for bar, val in zip(bars, valeurs):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
                 f"{val} %", ha="center", va="bottom", fontsize=10, fontweight="bold",
                 color=bar.get_facecolor())
    ax1.set_ylim(0, 62)
    ax1.set_ylabel("Part de la population (%)", fontsize=9)
    ax1.set_title("Structure par grand groupe d'age\n(RDC, 2025)", **FONT_TITRE)
    style_axe(ax1)
    ax1.spines["bottom"].set_visible(True)

    # Annotation ratio de dependance
    ax1.text(0.98, 0.97,
             "Age median : 15,9 ans\nRatio de dependance : ~96 pour 100 actifs",
             transform=ax1.transAxes, ha="right", va="top",
             fontsize=7.5, color=GRIS,
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=GRIS_CLAIR, alpha=0.8))

    # -- Camembert --
    wedges, texts, autotexts = ax2.pie(
        valeurs, labels=None, colors=couleurs,
        autopct="%1.1f%%", startangle=90,
        pctdistance=0.72,
        wedgeprops=dict(edgecolor="white", linewidth=1.5)
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_fontweight("bold")
        at.set_color("white")
    ax2.legend(wedges, groupes, loc="lower center", bbox_to_anchor=(0.5, -0.12),
               fontsize=8, ncol=1, framealpha=0.8)
    ax2.set_title("Repartition en parts (%)", **FONT_TITRE)

    note_source(fig, "Source : Division de la population des Nations Unies, WPP 2024. "
                "Estimation 2025. Age median : 15,9 ans (ONU WPP 2024).")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
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
# FIG_5 : Taux d'emploi informel par sexe, RDC
# Source : OIT ILOSTAT, estimations modelisees 2020
# ---------------------------------------------------------------------------
def fig5(dpi):
    print("FIG_5 : emploi informel par sexe...")

    categories = ["Ensemble", "Femmes", "Hommes"]
    valeurs    = [96.0, 97.8, 95.7]
    formel     = [100 - v for v in valeurs]
    couleurs   = [BLEU_FONCE, OR, BLEU_MOYEN]

    fig, ax = plt.subplots(figsize=(7, 4.2))

    x = np.arange(len(categories))
    w = 0.4

    b1 = ax.bar(x, valeurs, width=w, label="Emploi informel (%)",
                color=couleurs, edgecolor="white", linewidth=0.8)
    b2 = ax.bar(x, formel,  width=w, bottom=valeurs,
                label="Emploi formel (%)",
                color=[GRIS_CLAIR]*3, edgecolor="white", linewidth=0.8)

    for bar, val in zip(b1, valeurs):
        ax.text(bar.get_x() + bar.get_width()/2, val/2,
                f"{val} %", ha="center", va="center",
                fontsize=11, fontweight="bold", color="white")
    for bar, val, tot in zip(b2, formel, valeurs):
        ax.text(bar.get_x() + bar.get_width()/2, tot + val/2 + 1.0,
                f"{val:.1f}%", ha="center", va="bottom",
                fontsize=8.5, color="#555555", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0, 115)
    ax.set_ylabel("Part de l'emploi total (%)", fontsize=9)
    ax.set_title("Taux d'emploi informel par sexe, RDC",
                 **FONT_TITRE)

    # Echelle 0-100 uniquement
    ax.yaxis.set_major_locator(mticker.MultipleLocator(20))
    ax.set_ylim(0, 110)

    informel_patch = mpatches.Patch(facecolor=BLEU_FONCE, label="Emploi informel",
                                    edgecolor="white")
    formel_patch   = mpatches.Patch(facecolor=GRIS_CLAIR, label="Emploi formel",
                                    edgecolor=GRIS)
    ax.legend(handles=[informel_patch, formel_patch], fontsize=9,
              loc="upper right", framealpha=0.9)
    style_axe(ax)

    # Note methodologique (en bas, sans chevauchement avec les barres)
    ax.text(0.01, 0.03,
            "Note : estimations modelisees OIT (ILOEST).\n"
            "Donnees 2020, les plus recentes disponibles.",
            transform=ax.transAxes, ha="left", va="bottom",
            fontsize=7.5, color=GRIS, style="italic",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor=GRIS_CLAIR, alpha=0.85))

    note_source(fig, "Source : OIT, ILOSTAT — estimations modelisees de l'emploi informel (ILOEST), 2020. "
                "In : Banque mondiale, WDI 2024.")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
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

    # Annotation ecart femmes/hommes agriculture
    ax.annotate("", xy=(x[0] + w, val_femmes[0]),
                xytext=(x[0] + w*2, val_hommes[0]),
                arrowprops=dict(arrowstyle="<->", color=GRIS, lw=1.2))
    ax.text(x[0] + w*1.5, (val_femmes[0] + val_hommes[0])/2 + 2,
            "+17,5 pts\n(F vs H)", ha="center", fontsize=7.5, color=GRIS)

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
