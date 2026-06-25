import sqlite3, os, re

DB  = os.path.join("06_donnees", "protection_sociale_rdc.db")
CH4 = os.path.join("03_chapitres", "chapitre_4")
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

def nb(v):
    if v is None: return "0"
    return f"{int(v):,}".replace(",", "\u00a0")
def cdf(v):
    if v is None: return "—"
    return f"{int(v):,}\u00a0CDF".replace(",", "\u00a0")
def mds(v):
    if v is None or v == 0: return "0"
    return f"{v/1e9:.1f}\u00a0Mds\u00a0CDF".replace(".", ",")

def benef(inst, like, a):
    r = conn.execute("SELECT SUM(beneficiaires_total) FROM prestations_historique WHERE institution=? AND nom_fr LIKE ? AND annee=?", (inst, f"%{like}%", a)).fetchone()[0]
    return r or 0
def benef_fct(inst, fct, a):
    r = conn.execute("SELECT SUM(beneficiaires_total) FROM prestations_historique WHERE institution=? AND fonction_oit=? AND annee=?", (inst, fct, a)).fetchone()[0]
    return r or 0
def montant(inst, like, a):
    r = conn.execute("SELECT montant_unitaire_cdf FROM prestations_historique WHERE institution=? AND nom_fr LIKE ? AND annee=? AND montant_unitaire_cdf IS NOT NULL LIMIT 1", (inst, f"%{like}%", a)).fetchone()
    return r[0] if r else None
def cotis(inst, a):
    r = conn.execute("SELECT cotisants_total FROM indicateurs_regime WHERE institution=? AND annee=? AND cotisants_total IS NOT NULL LIMIT 1", (inst, a)).fetchone()
    return r[0] if r else None
def rec(inst, a):
    r = conn.execute("SELECT MAX(recettes_cdf) FROM indicateurs_regime WHERE institution=? AND annee=?", (inst, a)).fetchone()[0]
    return r
def dep(inst, a):
    r = conn.execute("SELECT MAX(depenses_prestations_cdf) FROM indicateurs_regime WHERE institution=? AND annee=?", (inst, a)).fetchone()[0]
    return r
def adm(inst, a):
    r = conn.execute("SELECT MAX(depenses_admin_cdf) FROM indicateurs_regime WHERE institution=? AND annee=? AND depenses_admin_cdf IS NOT NULL AND depenses_admin_cdf > 0", (inst, a)).fetchone()
    return r[0] if r else None

AN = [2019, 2020, 2021, 2022]

# Dictionnaire : label_recherché_dans_ligne → {année: valeur}
RULES = {
    # 4.1
    "CNSS — cotisants actifs":                {a: nb(cotis("CNSS",a))   for a in AN},
    "CNSSAP — cotisants actifs":              {a: nb(cotis("CNSSAP",a)) for a in AN},
    "CNSS — bénéficiaires de prestations":    {a: nb(sum([benef_fct("CNSS","Vieillesse",a), benef_fct("CNSS","Invalidité/handicap",a), benef_fct("CNSS","Survivants",a), benef_fct("CNSS","Accident du travail",a), benef_fct("CNSS","Maternité",a), benef_fct("CNSS","Enfants",a)])) for a in AN},
    "CNSSAP — bénéficiaires de prestations":  {a: nb(benef_fct("CNSSAP","Vieillesse",a)+benef_fct("CNSSAP","Survivants",a)) for a in AN},
    # 4.2
    "CNSS | Pension de retraite (bénéf.)":    {a: nb(benef("CNSS","Pension de retraite",a) - benef("CNSS","anticip",a)) for a in AN},
    "CNSS | Pension de retraite anticipée":   {a: nb(benef("CNSS","anticip",a))    for a in AN},
    "CNSSAP | Pension de vieillesse":         {a: nb(benef_fct("CNSSAP","Vieillesse",a)) for a in AN},
    "Pension CNSS — montant unitaire":        {a: cdf(montant("CNSS","Pension de retraite",a)) for a in AN},
    # 4.3
    "CNSS | Cotisants actifs (total)":        {a: nb(cotis("CNSS",a))   for a in AN},
    "CNSSAP | Cotisants actifs (total)":      {a: nb(cotis("CNSSAP",a)) for a in AN},
    "Bénéf. indemnité journalière maternité": {a: nb(benef("CNSS","journali",a))   for a in AN},
    "Bénéf. allocation de maternité":         {a: nb(benef("CNSS","allocation de maternit",a)) for a in AN},
    "Bénéf. allocations prénatales":          {a: nb(benef("CNSS","prénatales",a)) for a in AN},
    "Rentes/allocations incapacité AT/MP":    {a: nb(benef("CNSS","incapacit",a))  for a in AN},
    "Frais de réadaptation fonctionnelle":    {a: nb(benef("CNSS","readapt",a)) if a==2022 else "0" for a in AN},
    "Montant unitaire rente AT/MP":           {a: cdf(montant("CNSS","incapacit",a)) for a in AN},
    # 4.4
    "CNSS | Enfants couverts (allocations familiales)":   {a: nb(benef("CNSS","allocations familiales",a)) for a in AN},
    "CNSSAP | Enfants couverts (allocations familiales)": {a: "0" for a in AN},
    "Montant allocation familiale CNSS":      {a: "—" for a in AN},
    # 4.5
    "CNSS | Pensionnés invalidité (total)":   {a: nb(benef("CNSS","invalidit",a))  for a in AN},
    "CNSSAP | Pensionnés invalidité (total)": {a: "0" for a in AN},
    "Pension invalidité CNSS":                {a: cdf(montant("CNSS","invalidit",a)) for a in AN},
    "Pension vieillesse CNSS":                {a: cdf(montant("CNSS","Pension de retraite",a)) for a in AN},
    # 4.6
    "CNSS | Pension des survivants (bénéf.)": {a: nb(benef("CNSS","Pension des survivants",a)) for a in AN},
    "CNSS | Rentes de survivants AT/MP":      {a: nb(benef("CNSS","rentes de survivants",a))   for a in AN},
    "CNSS | Allocation frais funéraires":     {a: nb(benef("CNSS","funéraires",a)) for a in AN},
    "CNSSAP | Pension des survivants":        {a: nb(benef_fct("CNSSAP","Survivants",a)) for a in AN},
    "Pension survie CNSS":                    {a: cdf(montant("CNSS","Pension des survivants",a)) for a in AN},
    "Montant frais funéraires CNSS":          {a: cdf(montant("CNSS","funéraires",a)) for a in AN},
    # 4.7
    "CNSS — recettes totales":                {a: mds(rec("CNSS",a))   for a in AN},
    "CNSSAP — recettes totales":              {a: mds(rec("CNSSAP",a)) for a in AN},
    "CNSS — dépenses de prestations":         {a: mds(dep("CNSS",a))   for a in AN},
    "CNSSAP — dépenses de prestations":       {a: mds(dep("CNSSAP",a)) for a in AN},
    "CNSS — dépenses administratives":        {a: mds(adm("CNSS",a))   for a in AN},
    "CNSSAP — dépenses administratives":      {a: mds(adm("CNSSAP",a)) for a in AN},
}

def replace_ess_in_line(line, vals):
    """Remplace les [ESS XXXX] dans une ligne par les valeurs correspondantes."""
    for annee in AN:
        tag = f"[ESS {annee}]"
        if tag in line:
            line = line.replace(tag, str(vals[annee]), 1)
    return line

# ── Traitement des fichiers ──────────────────────────────────────────────────
files = [f for f in os.listdir(CH4) if f.startswith("4.") and f.endswith(".md")]
total_replacements = 0

for fname in sorted(files):
    fpath = os.path.join(CH4, fname)
    with open(fpath, encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    count = 0
    for line in lines:
        matched = False
        for label, vals in RULES.items():
            if label in line and any(f"[ESS {a}]" in line for a in AN):
                new_line = replace_ess_in_line(line, vals)
                new_lines.append(new_line)
                count += 1
                matched = True
                break
        if not matched:
            new_lines.append(line)

    with open(fpath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"  {fname:40s}  {count} ligne(s) remplies")
    total_replacements += count

print(f"\nTotal : {total_replacements} lignes remplacées dans {len(files)} fichiers.")
