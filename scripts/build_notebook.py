"""Génère puis exécute notebooks/01_analyse_voltride_africa.ipynb.

Usage : python scripts/build_notebook.py
Les chiffres de la narration (cellules Markdown) ont été vérifiés sur les sorties ;
les cellules "Lecture" imprimées par le code recalculent les valeurs clés.
"""
from pathlib import Path

import nbformat as nbf
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
NB_PATH = ROOT / "notebooks" / "01_analyse_voltride_africa.ipynb"

cells = []


def md(s: str):
    cells.append(nbf.v4.new_markdown_cell(s.strip("\n")))


def code(s: str):
    cells.append(nbf.v4.new_code_cell(s.strip("\n")))


# =====================================================================================
md("""
<img src="../docs/logo_voltride_clair.png" alt="VoltRide Motors" width="150">

# VoltRide Africa — Analyse stratégique avant l'ouverture de 20 stations (S1 2027)

**Rôle :** Data Analyst — mandat confié par le comité de direction
**Période :** 1er mai → 31 octobre 2026 (6 mois) · **Source :** `data/raw/voltride_dataset_senior.csv` (6 390 lignes brutes)

### Question centrale
> *Où et comment investir pour que les 20 nouvelles stations créent de la valeur, alors que le CA est irrégulier, que les remboursements et annulations pèsent, et que le marketing coûte cher ?*

### Plan du notebook
| # | Section | Livrable |
|---|---|---|
| 1 | Audit & compréhension des données | Résumé d'audit (`docs/audit_qualite.md`) |
| 2 | Data cleaning | `df_clean` + journal de nettoyage |
| 3 | Feature engineering | CA, marge, profit, CLV… |
| 4 | Analyses (performance, services, villes, marketing, clients) | Réponses aux 5 questions stratégiques |
| 5 | Bonus senior | Segments, remises, point mort d'une station |
| 6 | Recommandations & conclusion | 5 recommandations chiffrées |

### Conventions de calcul (à lire avant les chiffres)
* **Chiffre d'affaires (CA)** = quantité × prix × (1 − remise) pour les transactions **non annulées** (définition de l'énoncé). Il inclut donc les ventes ensuite remboursées.
* **CA net** = CA hors transactions remboursées. **Profit net réel** = profit après remboursements (le CA remboursé est rendu au client, le coût du service reste engagé).
* **Profit net** (définition de l'énoncé) = marge brute − coût marketing. Une transaction annulée n'a ni CA ni coût de service, mais son coût marketing est dépensé.
* **Taux d'annulation** = annulées / toutes les transactions. **Taux de remboursement** = remboursées / transactions non annulées.
* **ROI marketing** = (CA − coût marketing) / coût marketing (formule de l'énoncé). Le *ROI sur marge* = (marge brute − marketing) / marketing est plus exigeant et sert de contre-test.
* Montants en **FCFA**.
""")

# =====================================================================================
md("## 0. Configuration")
code("""
import sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from IPython.display import display, Markdown

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
from voltride.cleaning import load_raw, clean, parse_date, map_service, map_ville, NON_RENSEIGNE
from voltride.features import add_features
from voltride.analysis import (kpis, group_table, monthly, client_table, pareto, station_table, breakeven,
                               VERT, ANTHRACITE, GRIS, ROUGE, ORANGE, PALETTE_CAT)

warnings.filterwarnings("ignore")
pio.renderers.default = "notebook_connected"
pio.templates.default = "plotly_white"
FIG = ROOT / "reports" / "figures"; FIG.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", context="notebook", palette=PALETTE_CAT)
plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 12})
pd.options.display.float_format = lambda x: f"{x:,.2f}"
pd.options.display.max_columns = 40
pd.options.display.width = 200

def M(x):   # millions de FCFA
    return f"{x/1e6:,.2f} M".replace(",", " ")
def pct(x, n=1):
    return f"{x*100:.{n}f} %".replace(".", ",")
def millions(x, pos=None):
    return f"{x/1e6:.0f} M"
def save(fig, name):
    fig.savefig(FIG / name, dpi=160, bbox_inches="tight", facecolor="white")
print("Configuration OK - racine du projet :", ROOT)
""")

# =====================================================================================
md("""
# 1. Audit & compréhension des données

Objectif : mesurer précisément l'état des données **avant** toute correction, pour que chaque traitement du §2 soit justifié par un constat.
""")
code("""
raw = load_raw(ROOT / "data" / "raw" / "voltride_dataset_senior.csv")
print(f"{raw.shape[0]:,} lignes x {raw.shape[1]} colonnes".replace(",", " "))
display(raw.head(8))
""")
md("### 1.1 Structure et types")
code("""
# Le fichier est lu en texte : le typage réel est inféré ci-dessous pour détecter les colonnes mal typées.
num_cols = ["quantite", "prix_unitaire_fcfa", "remise_pct", "cout_unitaire_fcfa", "cout_marketing_fcfa", "note_client"]
types = pd.DataFrame({
    "type_lu": raw.dtypes.astype(str),
    "type_attendu": ["texte (id)", "texte (id)", "date", "catégorie", "catégorie", "catégorie", "catégorie", "catégorie",
                     "texte (code)", "catégorie", "entier", "numérique", "numérique %", "numérique", "numérique", "catégorie",
                     "catégorie", "numérique (1-5)"],
    "valeurs_distinctes": raw.nunique(),
})
display(types)
print("Mémoire :", f"{raw.memory_usage(deep=True).sum()/1e6:.1f} Mo")
""")
md("""
**Constat :** tout est lu en texte. `date_transaction` doit devenir une vraie date, et les colonnes numériques sont à contrôler (valeurs aberrantes). Les **variables catégorielles ont trop de valeurs distinctes** (ex. `ville` : 26 variantes pour 5 villes) — signe de saisies non normalisées.
""")
md("### 1.2 Valeurs manquantes")
code("""
manq = (raw.isna().sum().to_frame("manquants").assign(pct=lambda x: x.manquants / len(raw) * 100)
        .sort_values("manquants", ascending=False))
display(manq[manq.manquants > 0])

fig, ax = plt.subplots(figsize=(8, 4))
mm = manq[manq.manquants > 0].sort_values("pct")
ax.barh(mm.index, mm.pct, color=ANTHRACITE)
for i, (v, n) in enumerate(zip(mm.pct, mm.manquants)):
    ax.text(v + 0.3, i, f"{v:.1f} % ({n})", va="center", fontsize=9)
ax.set_xlabel("% de lignes manquantes"); ax.set_title("Valeurs manquantes par colonne")
ax.set_xlim(0, mm.pct.max() * 1.25)
save(fig, "01_audit_manquants.png"); plt.show()
""")
md("""
**Constat :** `note_client` (20,7 %) est manquante surtout pour les transactions **annulées** (pas d'expérience à noter) : ce n'est pas une erreur, on **ne l'impute pas**. `type_batterie` vaut `N/A` pour les accessoires : c'est une valeur légitime (pas de batterie), conservée comme « Sans objet ». Les manquants **à traiter** sont : `cout_marketing_fcfa` (204), `canal_acquisition` (116), `mode_paiement` (105), `ville` (77), `station` (73), `cout_unitaire_fcfa` (69), `type_client` (57), `type_service` (34), `date_transaction` (12).
""")
md("### 1.3 Doublons")
code("""
dup_exact = raw.duplicated().sum()
dup_id = raw["id_transaction"].duplicated().sum()
norm = raw.assign(id_client=raw.id_client.str.upper(), id_transaction=raw.id_transaction.str.upper())
dup_norm = norm.duplicated().sum()
print(f"Doublons exacts (brut)                         : {dup_exact}")
print(f"id_transaction répétés                         : {dup_id}")
print(f"Doublons exacts après normalisation des id     : {dup_norm}")
print("Exemple : même transaction, id_client écrit 'CLI00309' puis 'cli00309'")
display(raw[raw.id_transaction == "TRX000080"][["id_transaction", "id_client", "date_transaction", "ville", "type_service", "quantite", "statut"]])
""")
md("""
**Constat :** 183 doublons exacts + 7 doublons masqués par une **casse différente de `id_client`** (`CLI00309` / `cli00309`) = **190 lignes en trop** (3,0 %). Les ignorer gonflerait le CA.
""")
md("### 1.4 Incohérences de format et de libellé")
code("""
# --- dates : motifs rencontrés
motif = raw.date_transaction.fillna("<vide>").str.replace(r"[0-9]", "9", regex=True).str.replace(r"[a-zéû\\.]+", "mmm", regex=True)
fmt = motif.value_counts().rename("lignes").to_frame()
fmt["exemple"] = [raw.date_transaction[motif == m].iloc[0] if m != "<vide>" else "" for m in fmt.index]
fmt["lecture retenue"] = fmt.index.map({
    "9999-99-99": "AAAA-MM-JJ (ISO)", "99/99/9999": "JJ/MM/AAAA (jamais de 2e bloc > 12)",
    "99-99-99": "JJ-MM-AA", "99-99-9999": "MM-JJ-AAAA (le 2e bloc dépasse 12 -> impossible en JJ-MM)",
    "9999/99/99": "AAAA/MM/JJ", "9 mmm 9999": "JJ mois AAAA (français)", "99 mmm 9999": "JJ mois AAAA (français)", "<vide>": "manquante"}).fillna("")
display(fmt)

# --- libellés : variantes par colonne catégorielle
cat_cols = ["ville", "pays", "type_service", "type_client", "canal_acquisition", "mode_paiement", "statut"]
var = pd.DataFrame({"variantes_brutes": [raw[c].nunique() for c in cat_cols],
                    "valeurs_attendues": [5, 5, 4, 4, 6, 3, 3]}, index=cat_cols)
display(var)
print("Exemples pour 'statut' :", sorted(raw.statut.unique()))
""")
md("""
**Constat :** **6 formats de date** coexistent. Deux sont ambigus : `JJ/MM/AAAA` (le premier bloc dépasse 12 dans 1 019 cas et le second jamais → c'est bien jour/mois) et `MM-JJ-AAAA` (ex. `10-18-2026`). Les libellés sont pollués par la casse, les espaces, les fautes (« Abidjian », « Doaula »), l'anglais (« Completed », « Refunded ») et les abréviations (« Abo mensuel », « Loc. journalière »).
""")
md("### 1.5 Valeurs aberrantes")
code("""
n = raw.copy()
for c in num_cols:
    n[c] = pd.to_numeric(n[c], errors="coerce")
n["service"] = n.type_service.map(map_service)
ref = n.assign(p=n.prix_unitaire_fcfa.abs()).query("p > 0").groupby("service").p.median()
ratio = n.prix_unitaire_fcfa.abs() / n.service.map(ref)

anomalies = pd.DataFrame([
    ("quantite", "Quantité nulle", (n.quantite == 0).sum()),
    ("quantite", "Quantité négative", (n.quantite < 0).sum()),
    ("quantite", "Quantité irréaliste (> 10, max normal = 5)", (n.quantite > 10).sum()),
    ("prix_unitaire_fcfa", "Prix négatif", (n.prix_unitaire_fcfa < 0).sum()),
    ("prix_unitaire_fcfa", "Prix nul", (n.prix_unitaire_fcfa == 0).sum()),
    ("prix_unitaire_fcfa", "Prix x10 (ratio 8-12 vs médiane du service)", ratio.between(8, 12).sum()),
    ("prix_unitaire_fcfa", "Prix x100 (ratio 80-120)", ratio.between(80, 120).sum()),
    ("remise_pct", "Remise négative", (n.remise_pct < 0).sum()),
    ("remise_pct", "Remise > 100 %", (n.remise_pct > 100).sum()),
    ("cout_marketing_fcfa", "Coût marketing aberrant (> 5 000 ; P99,5 = 2 817)", (n.cout_marketing_fcfa > 5000).sum()),
    ("cout_unitaire_fcfa", "Coût unitaire manquant", n.cout_unitaire_fcfa.isna().sum()),
    ("cout_marketing_fcfa", "Coût marketing manquant", n.cout_marketing_fcfa.isna().sum()),
], columns=["colonne", "anomalie", "lignes"])
display(anomalies)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
bx = n[n.service.notna()].assign(prix=lambda t: t.prix_unitaire_fcfa.abs().clip(lower=1))
sns.boxplot(data=bx, y="service", x="prix", ax=axes[0], color=GRIS, fliersize=2)
axes[0].set_xscale("log"); axes[0].set_xlabel("Prix unitaire (FCFA, échelle log)"); axes[0].set_ylabel("")
axes[0].set_title("Prix bruts : des points isolés x10 / x100")
sns.histplot(n.cout_marketing_fcfa.dropna(), bins=60, ax=axes[1], color=ANTHRACITE)
axes[1].set_yscale("log"); axes[1].set_xlabel("Coût marketing (FCFA)"); axes[1].set_title("Coût marketing brut (échelle log) : 12 valeurs > 5 000")
save(fig, "02_audit_aberrants.png"); plt.show()
""")
md("""
**Constat :** les prix d'un service sont très stables (ex. swap ≈ 1 500 FCFA) : les valeurs x10 / x100 sont donc des **erreurs de saisie** reconnaissables et **corrigeables**, pas de vrais prix. Les remises réelles vont de 0 à 20 % ; les valeurs négatives ou > 100 % sont invalides.
""")
md("### 1.6 Résumé d'audit")
code("""
audit = pd.DataFrame([
    ("Doublons", "id_transaction / id_client", "190 lignes (3,0 %)", "Doublons exacts, dont 7 masqués par la casse de id_client", "Suppression"),
    ("Dates", "date_transaction", "2 803 lignes non ISO ; 12 vides ; ~13 impossibles", "6 formats ; certaines dates inexistantes", "Conversion + suppression des impossibles"),
    ("Villes", "ville", "916 variantes fautives ; 77 vides", "26 graphies pour 5 villes", "Correction + reconstitution via la station"),
    ("Services", "type_service", "1 010 libellés non standard ; 34 vides", "21 graphies pour 4 services", "Uniformisation + inférence par le coût"),
    ("Canaux / paiement", "canal_acquisition, mode_paiement", "765 / 607 non standard ou vides", "25 et 9 graphies", "Uniformisation, 'Non renseigné'"),
    ("Statuts", "statut", "956 lignes non standard", "18 graphies (FR/EN, casse, accents)", "Uniformisation en 3 statuts"),
    ("Quantités", "quantite", "61 nulles, 6 négatives, 5 irréalistes", "Erreurs de saisie", "Suppression / valeur absolue"),
    ("Prix", "prix_unitaire_fcfa", "~70 anormaux (négatifs, nuls, x10, x100)", "Écart net avec la médiane du service", "Correction par facteur ou médiane"),
    ("Remises", "remise_pct", "79 invalides (< 0 ou > 100 %)", "Remises réelles : 0-20 %", "Mise à 0 %"),
    ("Coûts", "cout_unitaire_fcfa, cout_marketing_fcfa", "69 + 204 manquants ; 12 marketing aberrants", "Valeurs absentes ou 20-40x la normale", "Médiane par service / par canal"),
    ("Satisfaction", "note_client", "1 325 vides (20,7 %)", "Surtout les annulations : normal", "Conservée telle quelle"),
], columns=["Thème", "Colonne(s)", "Volume", "Constat", "Traitement prévu"])
display(audit)

md_lines = ["# Audit qualité des données — VoltRide Africa", "",
            f"Fichier brut : {len(raw):,} lignes x {raw.shape[1]} colonnes (1er mai - 31 oct. 2026).".replace(",", " "), "",
            "| " + " | ".join(audit.columns) + " |", "|" + "---|" * len(audit.columns)]
md_lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in audit.itertuples(index=False)]
md_lines += ["", "Le détail chiffré de chaque correction figure dans `data/processed/journal_nettoyage.csv`."]
(ROOT / "docs" / "audit_qualite.md").write_text("\\n".join(md_lines), encoding="utf-8")
""")
code("""
# Part de lignes touchées (diagnostic global)
fmt_flags = pd.DataFrame({
    "date": ~raw.date_transaction.fillna("x").str.fullmatch(r"\\d{4}-\\d{2}-\\d{2}"), "ville": ~raw.ville.isin(["Abidjan", "Dakar", "Douala", "Cotonou", "Lomé"]),
    "service": ~raw.type_service.isin(["Swap batterie", "Location journalière", "Abonnement mensuel", "Accessoires & maintenance"]),
    "canal": ~raw.canal_acquisition.isin(["Meta Ads (Facebook/Instagram)", "TikTok Ads", "Partenariat chauffeurs VTC", "Parrainage", "WhatsApp Business", "Affichage & stations"]),
    "paiement": ~raw.mode_paiement.isin(["Mobile Money (Orange/MTN/Moov/Wave)", "Espèces à la station", "Carte bancaire"]),
    "statut": ~raw.statut.isin(["Terminée", "Annulée", "Remboursée"]), "id_client": raw.id_client != raw.id_client.str.upper()})
val_flags = pd.DataFrame({
    "quantité": (n.quantite <= 0) | (n.quantite > 10), "prix": (n.prix_unitaire_fcfa <= 0) | ~ratio.between(0.5, 1.6),
    "remise": (n.remise_pct < 0) | (n.remise_pct > 100), "marketing": n.cout_marketing_fcfa.isna() | (n.cout_marketing_fcfa > 5000),
    "coût": n.cout_unitaire_fcfa.isna(), "doublon": raw.duplicated(), "station": raw.station.isna(), "type_client": raw.type_client.isna()})
print(f"Lignes avec au moins une incohérence de format/libellé : {fmt_flags.any(axis=1).mean():.0%}")
print(f"Lignes avec au moins une anomalie de valeur (manquant, aberrant, doublon) : {val_flags.any(axis=1).mean():.0%}")
print(f"Lignes avec au moins un problème : {pd.concat([fmt_flags, val_flags], axis=1).any(axis=1).mean():.0%}")
""")
md("""
**Verdict d'audit :** les données sont exploitables mais **pas fiables en l'état** : **78 % des lignes** présentent au moins une incohérence, mais l'essentiel est de **forme** (formats de date, libellés) et se corrige par règle ; **13 % des lignes** ont une anomalie de **valeur** (manquant, aberrant, doublon). Aucune anomalie n'est irrécupérable : seules **4,4 %** des lignes sont finalement supprimées.
""")

# =====================================================================================
md("""
# 2. Data cleaning

Principe : **chaque règle est codée une fois** dans `src/voltride/cleaning.py`, journalisée, et rejouable (`python scripts/run_cleaning.py`). On préfère corriger quand la valeur correcte est déductible (format, référentiel, médiane du service), et supprimer quand elle ne l'est pas (date impossible, quantité 0).
""")
code("""
df_clean, journal = clean(raw)
display(journal)
print(f"{len(raw):,} lignes brutes -> {len(df_clean):,} lignes propres ({len(raw)-len(df_clean)} retirées, {(len(raw)-len(df_clean))/len(raw):.1%})".replace(",", " "))
""")
md("""
### Arbitrages assumés
| Sujet | Décision | Justification |
|---|---|---|
| Dates `JJ/MM/AAAA` vs `MM-JJ-AAAA` | Lecture déduite du contenu (bloc > 12) | Aucune ambiguïté résiduelle sur les formats avec tiret et AAAA |
| Dates impossibles / manquantes | Suppression (25 lignes) | Impossible de les rattacher à un mois |
| Prix x10 / x100 | Division par 10 / 100 | Le ratio à la médiane du service est quasi parfait |
| Remises invalides | 0 % | Non vérifiables ; hypothèse prudente (n'invente pas de remise) |
| Marketing manquant / aberrant | Médiane du canal | Le coût varie surtout selon le canal |
| Service manquant | Inféré par le coût unitaire le plus proche | Les 4 services ont des coûts très distincts (≈ 900 / 4 300 / 6 500 / 17 500) |
| Annulées | **Conservées** | Nécessaires pour le taux d'annulation |
""")
code("""
# --- Contrôles de qualité post-nettoyage (le notebook échoue si une règle n'est pas respectée)
assert df_clean.id_transaction.is_unique
assert df_clean.date_transaction.between("2026-05-01", "2026-10-31").all()
assert set(df_clean.ville) == {"Abidjan", "Cotonou", "Dakar", "Douala", "Lomé"}
assert df_clean.type_service.nunique() == 4 and df_clean.statut.nunique() == 3
assert df_clean.quantite.between(1, 10).all()
assert df_clean.prix_unitaire_fcfa.gt(0).all() and df_clean.remise_pct.between(0, 100).all()
assert df_clean.cout_marketing_fcfa.between(0, 5000).all() and df_clean.cout_unitaire_fcfa.notna().all()
assert not df_clean.drop(columns="note_client").isna().any().any()
print("Tous les contrôles passent.")

avant_apres = pd.DataFrame({"avant": [raw[c].nunique() for c in cat_cols], "après": [df_clean[c].nunique() for c in cat_cols]}, index=cat_cols)
display(avant_apres)
""")

# =====================================================================================
md("""
# 3. Feature engineering

Les variables sont créées dans `src/voltride/features.py` (même code pour le notebook et le dashboard).

| Variable | Définition |
|---|---|
| `chiffre_affaires` | quantité × prix × (1 − remise), 0 si annulée |
| `marge_brute` | CA − quantité × coût unitaire |
| `profit_net` | marge brute − coût marketing |
| `ca_net`, `profit_net_reel` | idem, après retrait des ventes remboursées |
| `mois` | mois de la transaction |
| `indicateur_remboursement` | 1 si remboursée |
| `nombre_transactions_par_client` | nb de transactions non annulées du client |
| `valeur_vie_client` | profit net cumulé du client sur la période (CLV simplifiée) |
""")
code("""
df = add_features(df_clean)
new_cols = ["chiffre_affaires", "marge_brute", "profit_net", "ca_net", "profit_net_reel", "mois_label",
            "indicateur_remboursement", "nombre_transactions_par_client", "valeur_vie_client", "frequence_client"]
display(df[["id_transaction", "type_service", "statut", "quantite", "prix_unitaire_fcfa", "remise_pct"] + new_cols].head(6))

# Contrôle de cohérence : recalcul indépendant du CA
ok = df[df.statut != "Annulée"]
recalc = (ok.quantite * ok.prix_unitaire_fcfa * (1 - ok.remise_pct / 100)).sum()
assert np.isclose(recalc, df.chiffre_affaires.sum()) and (df.loc[df.statut == "Annulée", "chiffre_affaires"] == 0).all()
print(f"CA recalculé indépendamment = CA du dataset = {M(recalc)} FCFA")
df.to_csv(ROOT / "data" / "processed" / "df_clean.csv", index=False, encoding="utf-8-sig")
""")

# =====================================================================================
md("""
# 4. Analyses

## 4.1 Performance globale
""")
code("""
k = kpis(df)
tab = pd.DataFrame({"Indicateur": ["Transactions", "Clients", "CA total (hors annulées)", "CA net des remboursements", "Marge brute",
                                   "Coût marketing", "Profit net estimé", "Profit net réel (après remboursements)", "Panier moyen",
                                   "Taux d'annulation", "Taux de remboursement"],
                    "Valeur": [f"{k['transactions']:,}".replace(",", " "), f"{k['clients']:,}".replace(",", " "), M(k['ca_total']) + " FCFA",
                               M(k['ca_net']) + " FCFA", M(k['marge_brute']) + f" FCFA ({pct(k['marge_pct'])} du CA)", M(k['marketing']) + " FCFA",
                               M(k['profit_net']) + " FCFA", M(k['profit_net_reel']) + " FCFA", f"{k['panier_moyen']:,.0f} FCFA".replace(",", " "),
                               pct(k['taux_annulation']), pct(k['taux_remboursement'])]})
display(tab.set_index("Indicateur"))

mo = monthly(df)
mo["label"] = mo.mois.dt.strftime("%b %Y")
fig, ax = plt.subplots(figsize=(9, 4.2))
ax.bar(mo.label, mo.ca, color=ANTHRACITE, label="CA")
ax.bar(mo.label, mo.profit_net, color=VERT, label="Profit net")
for x, v in zip(mo.label, mo.ca):
    ax.text(x, v + 2e5, M(v), ha="center", fontsize=8)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(millions)); ax.set_ylabel("FCFA")
ax.set_title("CA et profit net par mois"); ax.legend(frameon=False)
save(fig, "03_ca_profit_mensuel.png"); plt.show()

fig = go.Figure()
fig.add_bar(x=mo.mois, y=mo.ca, name="CA", marker_color=ANTHRACITE)
fig.add_scatter(x=mo.mois, y=mo.annulation * 100, name="Taux d'annulation (%)", yaxis="y2", mode="lines+markers", line=dict(color=ROUGE))
fig.update_layout(title="Interactif - CA mensuel et taux d'annulation", yaxis2=dict(overlaying="y", side="right", title="%", range=[0, 15]),
                  height=380, legend=dict(orientation="h", y=-0.2))
fig.show()
croiss = mo.ca.iloc[-1] / mo.ca.iloc[0] - 1
print(f"Lecture : CA oct. vs mai = {pct(croiss)} ; mois le plus faible = {mo.loc[mo.ca.idxmin(), 'label']} ; "
      f"le profit net suit le CA (marge de profit stable ≈ {pct(df.profit_net.sum()/df.chiffre_affaires.sum())}).")
""")
md("""
**Lecture business.**
* VoltRide a facturé **95,3 M FCFA** sur 6 mois pour **24,2 M FCFA de profit net estimé** (25 % du CA), mais **8,4 M FCFA de ventes sont ensuite remboursées** : le profit net réel tombe à **15,8 M FCFA**. **Les remboursements effacent un tiers du profit.**
* Le « CA irrégulier » vient surtout d'un **creux de juillet (−3 %)** suivi d'un rebond (+11 % en août, +11 % en octobre) ; la tendance est nettement haussière (**+24 % entre mai et octobre**).
* 1 transaction sur 10 est annulée (9,8 %) et 7,4 % des ventes finalisées sont remboursées : l'exécution est un levier de profit aussi important que la croissance.
""")

md("## 4.2 Analyse par ligne de service")
code("""
sv = group_table(df, "type_service").sort_values("ca", ascending=False)
display(sv[["transactions", "ca", "marge_pct", "marketing", "profit_net", "profit_net_reel", "panier_moyen",
            "taux_annulation", "taux_remboursement", "roi_marketing", "part_ca"]])

fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
x = np.arange(len(sv)); w = 0.27
axes[0].bar(x - w, sv.ca, w, color=ANTHRACITE, label="CA")
axes[0].bar(x, sv.marge_brute, w, color=GRIS, label="Marge brute")
axes[0].bar(x + w, sv.profit_net_reel, w, color=VERT, label="Profit net réel")
axes[0].set_xticks(x); axes[0].set_xticklabels([s.replace(" & ", "\\n& ").replace(" ", "\\n", 1) for s in sv.index], fontsize=8)
axes[0].yaxis.set_major_formatter(mtick.FuncFormatter(millions)); axes[0].legend(frameon=False, fontsize=8); axes[0].set_title("CA, marge et profit réel")
sns.barplot(x=sv.index, y=sv.taux_remboursement * 100, ax=axes[1], color=ROUGE)
axes[1].set_title("Taux de remboursement (%)"); axes[1].set_xlabel(""); axes[1].set_ylabel(""); axes[1].tick_params(axis="x", labelrotation=20, labelsize=8)
for i, v in enumerate(sv.taux_remboursement * 100): axes[1].text(i, v + 0.2, f"{v:.1f}", ha="center", fontsize=9)
part = pd.DataFrame({"Part du CA": sv.part_ca, "Part des transactions": sv.transactions / sv.transactions.sum(),
                     "Part du marketing": sv.marketing / sv.marketing.sum(), "Part du profit net": sv.profit_net / sv.profit_net.sum()}).T
part.plot(kind="bar", stacked=True, ax=axes[2], color=PALETTE_CAT[:4], width=0.7, legend=True)
axes[2].legend(fontsize=7, frameon=False, bbox_to_anchor=(1, 1)); axes[2].set_title("Qui consomme le marketing ? qui crée le profit ?")
axes[2].yaxis.set_major_formatter(mtick.PercentFormatter(1)); axes[2].tick_params(axis="x", labelrotation=15, labelsize=8)
plt.tight_layout(); save(fig, "04_services.png"); plt.show()

ms = monthly(df, "type_service")
fig = px.line(ms, x="mois", y="ca", color="type_service", markers=True, color_discrete_sequence=PALETTE_CAT,
              title="Interactif - Évolution mensuelle du CA par service", labels={"ca": "CA (FCFA)", "mois": "", "type_service": ""})
fig.update_layout(height=380, legend=dict(orientation="h", y=-0.2)); fig.show()

sw = sv.loc["Swap batterie"]
print(f"Lecture : le swap = {sv.loc['Swap batterie','transactions']/sv.transactions.sum():.0%} des transactions, {pct(sv.loc['Swap batterie','part_ca'],0)} du CA, "
      f"mais {sw.marketing/sv.marketing.sum():.0%} du marketing -> profit net = {sw.profit_net/1e3:,.0f} k FCFA ({sw.profit_net/sv.profit_net.sum():.1%} du total).")
""")
md("""
**Lecture business.**
* **L'abonnement mensuel est le moteur** : 57 % du CA, **75 % du profit net**, 35 % de marge, remboursement modéré (6,7 %), ROI marketing de 45. C'est la ligne à protéger et à développer.
* **Le swap est un piège de rentabilité** : c'est la ligne la plus fréquente (49 % des transactions) avec la meilleure marge unitaire (38 %), mais le panier est de **3 500 FCFA** alors que le coût marketing alloué par transaction est quasiment le même pour tous les services (≈ 1 100 FCFA). Résultat : **49 % du budget marketing pour 1,6 % du profit** (profit réel ≈ 45 k FCFA). Le swap est une porte d'entrée, pas un centre de profit.
* **Location journalière et accessoires** ont des marges faibles (≈ 25 %) et surtout **~14 % de remboursements** : après remboursements, leur profit chute de **79 %** pour la location (3,68 M → 0,76 M) et de **71 %** pour les accessoires (1,97 M → 0,58 M).

**Réponse à la question stratégique — quelle ligne prioriser / optimiser ?**
1. **Prioriser l'abonnement** (porte d'entrée swap → abonnement, voir §4.5).
2. **Optimiser en urgence la location et les accessoires** : le levier n'est pas le prix mais la qualité (pannes, retards de livraison, batteries défectueuses → remboursements).
3. **Redéfinir l'économie du swap** : cesser de l'acquérir via les canaux chers (§4.4).
""")

md("## 4.3 Analyse géographique")
code("""
vl = group_table(df, "ville").sort_values("ca", ascending=False)
mv = monthly(df, "ville").pivot(index="mois", columns="ville", values="ca")
vl["croissance_T2_vs_T1"] = (mv.iloc[3:].sum() / mv.iloc[:3].sum() - 1)   # 3 derniers mois vs 3 premiers
vl["profit_reel_pct_ca"] = vl.profit_net_reel / vl.ca
display(vl[["transactions", "ca", "profit_net", "profit_net_reel", "profit_reel_pct_ca", "taux_annulation", "taux_remboursement",
            "croissance_T2_vs_T1", "panier_moyen"]])

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
colors = [ROUGE if v == "Douala" else ANTHRACITE for v in vl.index]
axes[0].bar(vl.index, vl.ca, color=colors); axes[0].yaxis.set_major_formatter(mtick.FuncFormatter(millions)); axes[0].set_title("CA par ville")
axes[1].bar(vl.index, vl.profit_net_reel, color=VERT); axes[1].yaxis.set_major_formatter(mtick.FuncFormatter(millions)); axes[1].set_title("Profit net réel par ville")
axes[2].bar(vl.index, vl.taux_annulation * 100, color=colors); axes[2].set_title("Taux d'annulation (%)")
for i, v in enumerate(vl.taux_annulation * 100): axes[2].text(i, v + 0.2, f"{v:.1f}", ha="center", fontsize=9)
plt.tight_layout(); save(fig, "05_villes.png"); plt.show()

fig, axes = plt.subplots(1, 2, figsize=(14, 4.2))
hm = mv.copy(); hm.index = hm.index.strftime("%b"); hm = hm.T.loc[vl.index]
sns.heatmap(hm / 1e6, annot=True, fmt=".1f", cmap="Greens", ax=axes[0], cbar_kws={"label": "M FCFA"}); axes[0].set_title("CA mensuel (M FCFA) - ville x mois"); axes[0].set_xlabel(""); axes[0].set_ylabel("")
an = df.pivot_table(index="ville", columns="type_service", values="indicateur_annulation", aggfunc="mean").loc[vl.index] * 100
sns.heatmap(an, annot=True, fmt=".1f", cmap="Reds", ax=axes[1], cbar_kws={"label": "%"}); axes[1].set_title("Taux d'annulation (%) - ville x service"); axes[1].set_xlabel(""); axes[1].set_ylabel("")
axes[1].tick_params(axis="x", labelrotation=15, labelsize=8)
plt.tight_layout(); save(fig, "06_heatmaps_villes.png"); plt.show()

an_m = df.pivot_table(index="mois", columns="ville", values="indicateur_annulation", aggfunc="mean") * 100
fig = px.line(an_m.reset_index().melt("mois", value_name="annulation", var_name="ville"), x="mois", y="annulation", color="ville",
              markers=True, title="Interactif - Taux d'annulation mensuel par ville (%)", color_discrete_sequence=PALETTE_CAT)
fig.update_layout(height=360, legend=dict(orientation="h", y=-0.2)); fig.show()

st = station_table(df)
stv = st.groupby("ville").agg(stations=("station", "size"), transactions_mois=("transactions_mensuelles", "mean"),
                              ca_mois=("ca_mensuel", "mean"), contribution_mois=("contribution_mensuelle", "mean")).loc[vl.index]
print("Productivité moyenne d'une station existante (par mois) :")
display(stv)
""")
md("""
**Lecture business.**
* **Abidjan** pèse 37 % du CA et **ses stations sont 2 fois plus productives** que les autres (181 k FCFA de contribution mensuelle par station contre 66-94 k ailleurs ; 45 transactions/mois contre 15-24) : la demande y dépasse l'offre de stations. Croissance : +23 %.
* **Cotonou** est la petite ville qui **accélère le plus (+38 %)**, mais par station elle reste la moins productive (15 transactions/mois) : le potentiel est là, la maturité non.
* **Lomé** progresse (+19 %), avec un taux de remboursement élevé (8,4 %).
* **Dakar** est stable (+2 %) mais **la plus saine** : annulation 8,2 %, remboursement le plus bas (6,2 %), le meilleur profit réel rapporté au CA.
* **Douala est le problème d'exécution** : **15,5 % d'annulation** (le double des autres), **à tous les mois** (12-17 %), **dans la quasi-totalité des stations** (jusqu'à 19 %) et surtout sur les services à engagement (abonnement 15,8 %, accessoires 21,9 %). CA stable (−1 %). Un défaut persistant et généralisé est **structurel** (disponibilité des batteries, logistique, process), pas un accident local.
""")
code("""
# Score d'attractivité pour répartir les 20 stations (pondérations explicites, modifiables)
poids = {"contribution": 0.35, "croissance": 0.30, "execution": 0.20, "qualite": 0.15}
sc = pd.DataFrame({"contribution": stv.contribution_mois, "croissance": vl.croissance_T2_vs_T1,
                   "execution": 1 - vl.taux_annulation, "qualite": vl.profit_reel_pct_ca})
norm = (sc - sc.min()) / (sc.max() - sc.min())
sc["score"] = sum(norm[c] * w for c, w in poids.items())
sc = sc.sort_values("score", ascending=False)
display(sc.round(3))

# Répartition proposée des 20 stations
repartition = pd.DataFrame({"stations": {"Abidjan": 8, "Dakar": 4, "Cotonou": 3, "Lomé": 3, "Douala": 2}})
repartition["vague"] = ["Vague 1 (T1 2027)", "Vague 1 (T1 2027)", "Vague 1 (T1 2027)", "Vague 1 (T1 2027)", "Vague 2 - conditionnelle (taux d'annulation < 10 %)"]
repartition["stations_existantes"] = stv.stations
repartition["score"] = sc.score
display(repartition.sort_values("score", ascending=False))
assert repartition.stations.sum() == 20
""")
md("""
**Réponse à la question stratégique — où ouvrir les 20 stations ? où corriger d'abord ?**

| Ville | Stations | Raison |
|---|---|---|
| **Abidjan** | **8** | Stations 2x plus productives, demande saturée, +23 % de croissance ; c'est là qu'une station neuve se rentabilise le plus vite (§5.3) |
| **Dakar** | **4** | Ville la plus saine (annulation et remboursement bas) ; croissance faible → ouvrir en renforcement, pas en pari |
| **Cotonou** | **3** | Plus forte croissance (+38 %) mais productivité encore faible → ouvrir par paliers |
| **Lomé** | **3** | +19 % de croissance ; surveiller les remboursements |
| **Douala** | **2, conditionnelles** | **Corriger l'exécution d'abord** : ouvrir seulement si l'annulation passe sous 10 % |

Le score classe Abidjan très nettement en tête et Douala en dernier. **Cotonou passe devant Dakar au score uniquement grâce à sa croissance (+38 %)**, mais c'est la ville où une station neuve se rentabilise le moins (§5.3) : on l'ouvre donc **par paliers (3)**, et on renforce **Dakar (4)**, plus productive et plus saine. La répartition finale combine ainsi le score, le point mort et le **risque d'exécution** (on ne finance pas une ouverture là où 1 commande sur 6 est annulée). Ordre des priorités : **Abidjan > Dakar > Cotonou ≈ Lomé > Douala (après correction)**.
""")

md("## 4.4 Analyse marketing (acquisition)")
code("""
cn = group_table(df[df.canal_acquisition != NON_RENSEIGNE], "canal_acquisition").sort_values("roi_marketing", ascending=False)
cn["cout_par_transaction"] = cn.marketing / cn.transactions
cc = client_table(df)
cn["retention"] = cc.groupby("canal").retenu.mean()
cn["clients"] = cc.groupby("canal").size()
cn["part_marketing"] = cn.marketing / cn.marketing.sum()
display(cn[["ca", "marketing", "part_marketing", "part_ca", "roi_marketing", "roi_marge", "cout_par_transaction", "profit_net_reel",
            "taux_annulation", "taux_remboursement", "retention"]])
print(f"({NON_RENSEIGNE} exclu : 111 transactions, 1,98 % du CA)")

fig, axes = plt.subplots(1, 3, figsize=(16, 4.4))
roi = cn.roi_marketing.sort_values()
axes[0].barh(roi.index, roi, color=[VERT if v >= 15 else (ORANGE if v >= 9 else ROUGE) for v in roi])
for i, v in enumerate(roi): axes[0].text(v + 0.5, i, f"{v:.1f}", va="center", fontsize=9)
axes[0].set_title("ROI marketing = (CA - coût) / coût"); axes[0].tick_params(axis="y", labelsize=8)
axes[1].barh(np.arange(len(cn)) - 0.2, cn.part_marketing, 0.4, color=ANTHRACITE, label="Part du budget marketing")
axes[1].barh(np.arange(len(cn)) + 0.2, cn.part_ca, 0.4, color=VERT, label="Part du CA")
axes[1].set_yticks(np.arange(len(cn))); axes[1].set_yticklabels(cn.index, fontsize=8); axes[1].invert_yaxis()
axes[1].xaxis.set_major_formatter(mtick.PercentFormatter(1)); axes[1].legend(frameon=False, fontsize=8); axes[1].set_title("Budget vs CA apporté")
rt = cn.retention.sort_values()
axes[2].barh(rt.index, rt * 100, color=[VERT if v >= .7 else (ROUGE if v < .63 else GRIS) for v in rt]); axes[2].set_xlim(50, 80)
for i, v in enumerate(rt * 100): axes[2].text(v + 0.3, i, f"{v:.1f} %", va="center", fontsize=9)
axes[2].set_title("Rétention (clients actifs sur >= 2 mois)"); axes[2].tick_params(axis="y", labelsize=8)
plt.tight_layout(); save(fig, "07_canaux.png"); plt.show()

fig = px.scatter(cn.reset_index(), x="marketing", y="roi_marketing", size="ca", color="taux_remboursement", text="canal_acquisition",
                 color_continuous_scale="RdYlGn_r", title="Interactif - Budget (x) vs ROI (y) ; taille = CA, couleur = taux de remboursement",
                 labels={"marketing": "Coût marketing (FCFA)", "roi_marketing": "ROI", "taux_remboursement": "Remb."})
fig.update_traces(textposition="top center"); fig.update_layout(height=430); fig.show()

swc = df[df.type_service == "Swap batterie"].groupby("canal_acquisition").agg(transactions=("profit_net", "size"), profit_net=("profit_net", "sum"),
                                                                           cout_mkt_moyen=("cout_marketing_fcfa", "mean"), marge_moy=("marge_brute", "mean")).sort_values("profit_net")
print("Swap uniquement : profit net par canal d'acquisition")
display(swc)
""")
md("""
**Lecture business.**
* **Parrainage = le meilleur canal sur tous les critères** : ROI de **35,9**, coût de seulement **441 FCFA/transaction** (contre 1 820 pour TikTok), **72,6 % de rétention** (le meilleur), 6 % de remboursement. Il apporte 17,7 % du CA pour **6,8 % du budget**.
* **WhatsApp Business (ROI 23,8)** et **Partenariat chauffeurs VTC (ROI 19,6)** sont également rentables et fidélisants.
* **TikTok Ads est le canal à corriger** : **30 % du budget marketing** (2,03 M FCFA) pour 17,9 % du CA, **ROI le plus bas (7,4)**, **taux d'annulation 13,1 %**, **remboursement 11 %**, **rétention la plus faible (61,3 %)**. Son profit réel (1,2 M) est 3x inférieur à celui du parrainage (3,86 M) alors que le CA est équivalent.
* **Meta Ads** et **Affichage** ont un ROI moyen (9-10) mais un coût par transaction élevé (1 570 et 1 290 FCFA).
* **Effet sur le swap** : avec un panier de 3 500 FCFA, acquérir un client swap via TikTok (1 832 FCFA) ou Meta (1 568 FCFA) **fait perdre de l'argent** (profit swap : −340 k et −177 k FCFA), alors que Parrainage, WhatsApp et VTC dégagent un profit positif.

**Réponse à la question stratégique.**
* **Plus de budget :** Parrainage (programme à renforcer : bonus pour parrain et filleul), WhatsApp Business, Partenariat VTC.
* **À optimiser :** TikTok (cibler les abonnements et les PME plutôt que le swap, ou plafonner le coût d'acquisition), Meta Ads (même logique).
* **À réduire en premier :** la part de TikTok/Meta dédiée à l'acquisition de clients swap.
""")

md("## 4.5 Analyse clients")
code("""
cl = client_table(df)
print(f"Clients (toutes transactions)             : {df.id_client.nunique():,}".replace(",", " "))
print(f"Clients avec >= 1 transaction non annulée : {len(cl):,}".replace(",", " "))
print(f"% de clients récurrents (>= 2 transactions): {pct(cl.recurrent.mean())}")
print(f"% de clients retenus (actifs sur >= 2 mois) : {pct(cl.retenu.mean())}")

p = pareto(cl, "ca")
n80 = int((p.part_cum <= 0.8).sum() + 1)
print(f"\\nPareto : {n80} clients ({n80/len(p):.1%}) génèrent 80 % du CA ; les 20 % meilleurs en génèrent {p.part_cum.iloc[int(len(p)*.2)-1]:.1%}")

fig, axes = plt.subplots(1, 2, figsize=(13, 4.3))
axes[0].plot(p.pct_clients * 100, p.part_cum * 100, color=ANTHRACITE, lw=2.5)
axes[0].axhline(80, color=GRIS, ls="--"); axes[0].axvline(n80 / len(p) * 100, color=VERT, ls="--")
axes[0].plot([0, 100], [0, 100], color=GRIS, lw=1)
axes[0].annotate(f"{n80/len(p):.0%} des clients\\n= 80 % du CA", (n80 / len(p) * 100, 80), (45, 55), arrowprops=dict(arrowstyle="->"), fontsize=10)
axes[0].set_xlabel("% cumulé des clients (du plus gros au plus petit)"); axes[0].set_ylabel("% cumulé du CA"); axes[0].set_title("Courbe de Pareto 80/20")
seg = cl.groupby("frequence", observed=True).agg(clients=("ca", "size"), ca=("ca", "sum"), profit=("profit_net", "sum"))
seg["part_clients"] = seg.clients / seg.clients.sum(); seg["part_ca"] = seg.ca / seg.ca.sum()
seg[["part_clients", "part_ca"]].T.plot(kind="bar", stacked=True, ax=axes[1], color=[GRIS, ORANGE, VERT], width=0.5)
axes[1].yaxis.set_major_formatter(mtick.PercentFormatter(1)); axes[1].set_title("Segmentation par fréquence : poids en clients vs en CA")
axes[1].set_xticklabels(["% des clients", "% du CA"], rotation=0); axes[1].legend(fontsize=8, frameon=False)
plt.tight_layout(); save(fig, "08_pareto_segments.png"); plt.show()
display(seg)

top10 = cl.sort_values("ca", ascending=False).head(10)[["type_client", "canal", "transactions", "ca", "profit_net", "mois_actifs"]]
top10.index.name = "client"
print("Top 10 clients :"); display(top10)
print(f"Les 10 premiers clients = {top10.ca.sum()/cl.ca.sum():.1%} du CA ; type : {top10.type_client.value_counts().to_dict()}")
""")
md("""
**Lecture business.**
* **Portefeuille concentré :** **30 % des clients (318) font 80 % du CA** ; les **230 clients « fidèles »** (6+ transactions, 21 % des clients) génèrent **68 % du CA**. À l'inverse, 52 % des clients sont occasionnels (1-2 transactions) et ne pèsent que 13 % du CA.
* **70 % de clients récurrents**, **66 % actifs sur au moins 2 mois** : la base est fidèle, mais **le nombre de clients actifs décroît avec l'ancienneté** (365 clients actifs 1 seul mois, 82 sur les 6 mois) — l'enjeu est la **rétention des occasionnels**, pas l'acquisition à tout prix.
* Le **top 10 pèse 17,5 % du CA** (le n° 1 à lui seul : 4,0 M FCFA, 208 transactions) : un risque de dépendance à surveiller (4 PME/flottes, 4 chauffeurs, 2 particuliers).
""")
code("""
# --- Satisfaction et remboursement
nt = df.dropna(subset=["note_client"]).copy()
nt["note"] = nt.note_client.astype(int)
by_note = nt.groupby("note").agg(transactions=("note", "size"), taux_remb=("indicateur_remboursement", "mean"))
mean_notes = df.groupby("statut").note_client.mean()

fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))
axes[0].bar(by_note.index, by_note.transactions, color=ANTHRACITE); axes[0].set_title("Distribution des notes"); axes[0].set_xlabel("Note client")
axes[1].bar(by_note.index, by_note.taux_remb * 100, color=ROUGE); axes[1].set_title("% de transactions remboursées selon la note"); axes[1].set_xlabel("Note client")
for i, v in zip(by_note.index, by_note.taux_remb * 100): axes[1].text(i, v + 0.8, f"{v:.0f} %", ha="center")
plt.tight_layout(); save(fig, "09_satisfaction.png"); plt.show()
print(f"Note moyenne : {df.note_client.mean():.2f}/5  |  terminées : {mean_notes['Terminée']:.2f}  |  remboursées : {mean_notes['Remboursée']:.2f}")
print(f"Part de notes <= 2 : {(df.note_client <= 2).sum()/df.note_client.notna().sum():.1%} ; parmi elles, {df[df.note_client <= 2].indicateur_remboursement.mean():.0%} sont remboursées ; "
      f"aucune note >= 4 n'est remboursée.")
print("Notes manquantes : 10 % des terminées, 38 % des remboursées -> les clients mécontents répondent moins.")
""")
md("""
**Lecture business.**
* Note moyenne **3,82/5**. Les transactions remboursées sont notées **1,87** contre **3,93** pour les terminées. **Aucune note ≥ 4 n'est remboursée ; 1 note ≤ 2 sur 4 l'est.**
* **La note est donc un signal d'alerte précoce** : une note ≤ 2 prédit un remboursement. Agir **avant** le remboursement (rappel du client, geste commercial, échange de batterie) coûte moins cher que rembourser (8,4 M FCFA remboursés sur la période).
* 38 % des transactions remboursées n'ont pas de note : le sondage doit être **systématique et immédiat** (SMS/WhatsApp post-service).
""")
code("""
# --- Conversion swap -> abonnement mensuel
e = df[df.statut != "Annulée"]
mix = e.pivot_table(index="id_client", columns="type_service", values="quantite", aggfunc="sum", fill_value=0)
swap_cl = mix[mix["Swap batterie"] > 0]
a_abo = swap_cl["Abonnement mensuel"] > 0
swap_only = swap_cl[~a_abo].index
print(f"Clients ayant utilisé le swap : {len(swap_cl)} | dont déjà abonnés : {a_abo.sum()} ({a_abo.mean():.0%}) | swap uniquement : {len(swap_only)}")

abo = e[e.type_service == "Abonnement mensuel"]
abo_marge_mois = abo.marge_brute.sum() / abo.quantite.sum()
sw_only = e[(e.type_service == "Swap batterie") & e.id_client.isin(swap_only)]
sw_marge_mois = sw_only.groupby("id_client").marge_brute.sum().mean() / 6
gain_net_mois = abo_marge_mois - sw_marge_mois
print(f"Marge brute mensuelle d'un abonné = {abo_marge_mois:,.0f} FCFA ; marge swap mensuelle d'un client 'swap uniquement' = {sw_marge_mois:,.0f} FCFA".replace(",", " "))

H = {"mois_abonnement_moyen": 3}
scen = pd.DataFrame({"taux de conversion": [0.05, 0.10, 0.15, 0.20]})
scen["clients convertis"] = (len(swap_only) * scen["taux de conversion"]).round().astype(int)
scen["gain de marge (M FCFA / 6 mois)"] = scen["clients convertis"] * gain_net_mois * H["mois_abonnement_moyen"] / 1e6
scen["en % du profit net actuel"] = scen["gain de marge (M FCFA / 6 mois)"] * 1e6 / df.profit_net.sum()
display(scen)
print("Hypothèse : chaque client converti garde l'abonnement 3 mois en moyenne et abandonne ses swaps ; le gain = marge abonnement - marge swap perdue.")
""")
md("""
**Lecture business — comment convertir le swap en abonnement ?**
* **44 % des clients swap** ont déjà un abonnement : la bascule se produit naturellement pour une partie d'entre eux. Il reste **469 clients « swap uniquement »** à convertir.
* Un abonné rapporte ≈ **9 600 FCFA de marge par mois** contre ≈ **400 FCFA** pour un client « swap uniquement » : **une conversion rapporte ~9 000 FCFA de marge supplémentaire par mois**. Attention : ces clients dépensent aujourd'hui peu en swap (≈ 2 700 FCFA/mois de CA) alors que l'abonnement coûte 28 000 FCFA : un taux de conversion réaliste se situe plutôt à **5-10 %** et la cible prioritaire doit être celle des gros utilisateurs.
* **5 à 10 % de conversion** (23 à 47 clients) apporterait **0,6 à 1,3 M FCFA de marge sur 6 mois** (3 à 5 % du profit net), sans coût d'acquisition puisque ces clients sont déjà acquis.

**Actions proposées :** (1) proposer l'abonnement **dès le 5ᵉ swap** (« vous avez payé X FCFA ce mois, l'abonnement vous coûterait Y ») ; (2) abonnement **d'essai** ou 1er mois à tarif réduit **plafonné** (et non des remises générales, §5.2) ; (3) cibler d'abord les **59 clients « swap uniquement » ayant fait au moins 8 swaps**, les plus proches de l'équivalent d'un abonnement ; (4) objectif de **rétention** : relancer tout client occasionnel ayant un 2ᵉ mois sans transaction.
""")

# =====================================================================================
md("""
# 5. Bonus senior

## 5.1 Quel segment client est le plus rentable ?
""")
code("""
sg = group_table(df[df.type_client != NON_RENSEIGNE], "type_client")
sg["profit_reel_par_transaction"] = sg.profit_net_reel / sg.transactions
sg["profit_par_transaction"] = sg.profit_net / sg.transactions
sg = sg.sort_values("profit_reel_par_transaction", ascending=False)
display(sg[["transactions", "ca", "part_ca", "panier_moyen", "marge_pct", "taux_annulation", "taux_remboursement", "roi_marketing",
            "profit_par_transaction", "profit_reel_par_transaction", "profit_net_reel"]])

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
axes[0].bar(sg.index, sg.profit_reel_par_transaction, color=[VERT, ANTHRACITE, GRIS, GRIS]); axes[0].set_title("Profit net réel par transaction (FCFA)")
axes[1].bar(sg.index, sg.taux_remboursement * 100, color=ROUGE); axes[1].set_title("Taux de remboursement (%)")
axes[2].bar(sg.index, sg.profit_net_reel, color=VERT); axes[2].yaxis.set_major_formatter(mtick.FuncFormatter(millions)); axes[2].set_title("Profit net réel total")
for a in axes: a.tick_params(axis="x", labelrotation=15, labelsize=8)
plt.tight_layout(); save(fig, "10_segments_clients.png"); plt.show()

pv = df[df.type_client != NON_RENSEIGNE].pivot_table(index="type_client", columns="type_service", values="profit_net_reel", aggfunc="sum") / 1e6
plt.figure(figsize=(8, 3.2)); sns.heatmap(pv, annot=True, fmt=".2f", cmap="RdYlGn", center=0, cbar_kws={"label": "M FCFA"})
plt.title("Profit net réel (M FCFA) : segment x service"); plt.xlabel(""); plt.ylabel(""); plt.xticks(fontsize=8); plt.show()
""")
md("""
**Lecture business.**
* **PME / flotte = segment le plus rentable par transaction** : panier le plus haut (23 600 FCFA), meilleure marge (33,5 %), annulation la plus basse (7,9 %), ROI marketing 22 et **5 064 FCFA de profit réel par transaction** (le double des chauffeurs : 2 762).
* **Chauffeurs moto-taxi = le volume** (40 % du CA, 7,1 M de profit réel), rentables essentiellement grâce à l'**abonnement** (6,5 M).
* **Particuliers = le segment le moins rentable** : **11,7 % de remboursement**, marge de 29,9 %, et un profit réel par transaction de 1 441 FCFA ; le **swap des particuliers perd de l'argent** (−40 k FCFA). Ils achètent surtout de la location et des accessoires, les services les plus remboursés.
* **Livreurs** : correct mais le plus exposé aux annulations (10,7 %) ; potentiel via l'abonnement.

**Recommandation segmentée :** développer la **prospection PME/flottes** (contrats flotte, facturation mensuelle), sécuriser les moto-taxis par l'abonnement, et **traiter la qualité de service avant d'acquérir de nouveaux particuliers**.
""")

md("## 5.2 Les promotions détruisent-elles de la valeur ?")
code("""
e = df[df.statut != "Annulée"]
rm = e.groupby("remise_tranche", observed=True).agg(transactions=("quantite", "size"), quantite_moy=("quantite", "mean"),
                                                   panier_moy=("chiffre_affaires", "mean"), marge_par_trans=("marge_brute", "mean"),
                                                   taux_remb=("indicateur_remboursement", "mean"), profit_reel=("profit_net_reel", "sum"))
rm["marge_pct"] = e.groupby("remise_tranche", observed=True).marge_brute.sum() / e.groupby("remise_tranche", observed=True).chiffre_affaires.sum()
ann = df.groupby("remise_tranche", observed=True).indicateur_annulation.mean()
rm["taux_annulation"] = ann
display(rm)
ca_sacrifie = (e.quantite * e.prix_unitaire_fcfa * e.remise_pct / 100).sum()
print(f"{(df.remise_pct > 0).mean():.1%} des transactions sont remisées ; CA sacrifié = {M(ca_sacrifie)} FCFA = {ca_sacrifie/df.chiffre_affaires.sum():.1%} du CA = {ca_sacrifie/df.marge_brute.sum():.1%} de la marge brute.")

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
axes[0].plot(rm.index.astype(str), rm.quantite_moy, "o-", color=ANTHRACITE, lw=2.5); axes[0].set_ylim(0, 3.5)
axes[0].set_title("Quantité moyenne par transaction"); axes[0].set_xlabel("Remise");
axes[1].bar(rm.index.astype(str), rm.marge_par_trans, color=[VERT, GRIS, GRIS, GRIS, ROUGE]); axes[1].set_title("Marge brute par transaction (FCFA)"); axes[1].set_xlabel("Remise")
axes[2].bar(rm.index.astype(str), rm.taux_remb * 100, color=ROUGE); axes[2].set_title("Taux de remboursement (%)"); axes[2].set_xlabel("Remise")
plt.tight_layout(); save(fig, "11_remises.png"); plt.show()
""")
md("""
**Lecture business : OUI, les remises détruisent de la valeur.**
* **Aucun effet volume** : la quantité moyenne par transaction est **plate** (2,42 sans remise → 2,48 à 20 %) ; le taux d'annulation aussi. Les remises ne font pas acheter plus.
* **Effet marge sévère** : la marge par transaction passe de **6 305 FCFA (sans remise) à 2 421 FCFA (−62 %) à 20 %**.
* **À 20 % de remise, le remboursement bondit à 12,5 %** (contre 7 % sans remise) et le **profit réel devient négatif** (−142 k FCFA sur les transactions non annulées).
* **Coût total : 3,3 M FCFA de CA sacrifié**, soit 3,5 % du CA mais **10,8 % de la marge brute**. Un tiers des transactions (33,5 %) est remisé sans différence de comportement : les remises sont **accordées par habitude, pas par stratégie**.

**Recommandation :** supprimer les remises ≥ 15 % ; réserver 5-10 % à des objectifs précis (essai d'abonnement, contrat flotte, parrainage) avec suivi du ROI ; instaurer une validation au-delà de 10 %.
""")

md("## 5.3 Point mort d'une nouvelle station")
md("""
### Hypothèses (à valider avec la Finance)
Le dataset donne la **marge de contribution** d'une station (marge brute − marketing), mais pas ses charges fixes ni son investissement. Les hypothèses suivantes sont **cohérentes avec l'échelle d'activité observée** (CA moyen d'une station ≈ 400 k FCFA/mois) ; elles sont **volontairement modifiables** (cellule ci-dessous et dashboard Streamlit) :

| Hypothèse | Valeur | Justification |
|---|---|---|
| Investissement initial (capex) | **2,5 M FCFA** | Borne de charge/échange, enseigne, installation, stock initial de batteries |
| Charges fixes mensuelles | **45 k FCFA** | Loyer d'emplacement, agent à temps partiel, énergie fixe, connexion |
| Montée en charge | **3 mois à 50 %** de la contribution de croisière | Le temps de faire connaître la station |
| Contribution de croisière | **Moyenne observée des stations de la ville** | Mesurée sur 6 mois de données réelles |
| Horizon | 72 mois | |

**Point mort = mois où le cash cumulé (après capex) redevient positif.** Le *point mort mensuel* (équilibre d'exploitation) est le 1er mois où contribution ≥ charges fixes.
""")
code("""
HYP = dict(capex=2_500_000, charges_fixes=45_000, montee_en_charge=3, taux_initial=0.5)

rows = []
for ville, g in station_table(df).groupby("ville"):
    c = g.contribution_mensuelle.mean()
    be = breakeven(c, HYP["capex"], HYP["charges_fixes"], HYP["montee_en_charge"], HYP["taux_initial"])
    marge_trans = (g.marge.sum() - g.marketing.sum()) / g.transactions.sum()
    rows.append({"ville": ville, "contribution_mensuelle": c, "transactions_mois_observees": g.transactions_mensuelles.mean(),
                 "contribution_par_transaction": marge_trans,
                 "transactions_pour_equilibre": HYP["charges_fixes"] / marge_trans,
                 "mois_equilibre_mensuel": be["mois_equilibre_mensuel"], "mois_point_mort_cash": be["mois_retour"]})
pm = pd.DataFrame(rows).set_index("ville").sort_values("contribution_mensuelle", ascending=False)
display(pm.fillna("> 72"))

horizon = np.arange(0, 61)
fig, ax = plt.subplots(figsize=(9, 4.4))
for (ville, r), col in zip(pm.iterrows(), PALETTE_CAT):
    cum = [-HYP["capex"]]
    for m in range(1, 61):
        cum.append(cum[-1] + r.contribution_mensuelle * (HYP["taux_initial"] if m <= HYP["montee_en_charge"] else 1) - HYP["charges_fixes"])
    ax.plot(horizon, np.array(cum) / 1e6, label=ville, color=col, lw=2.3)
ax.axhline(0, color="black", lw=1); ax.set_xlabel("Mois depuis l'ouverture"); ax.set_ylabel("Cash cumulé (M FCFA)")
ax.set_title("Point mort d'une station neuve selon la ville"); ax.legend(frameon=False, ncol=2)
save(fig, "12_point_mort.png"); plt.show()

# Sensibilité : station "moyenne" (toutes villes) selon la contribution et les charges fixes
c_moy = station_table(df).contribution_mensuelle.mean()
sens = pd.DataFrame({f"charges fixes {int(f/1e3)} k": [breakeven(c_moy * (1 + u), HYP["capex"], f)["mois_retour"] or np.nan for u in [0, .2, .4]]
                     for f in [30_000, 45_000, 60_000]}, index=["contribution observée", "+20 %", "+40 %"])
print(f"Sensibilité - mois de point mort cash d'une station 'moyenne' (contribution = {c_moy:,.0f} FCFA/mois) :".replace(",", " "))
display(sens.fillna("> 72"))
""")
md("""
**Lecture business.**
* **Abidjan : point mort cash en ~21 mois** — c'est la seule ville où l'investissement est repris en moins de 2 ans. Une station abidjanaise a besoin de ~11 transactions/mois pour couvrir ses charges fixes et en réalise 45.
* **Dakar (~54 mois) et Douala (~63 mois)** : l'activité couvre les charges fixes mais l'investissement est très long à récupérer. **Cotonou et Lomé** n'atteignent pas le point mort cash en 6 ans au niveau de productivité actuel.
* **Ce que cela implique :** ouvrir 20 stations « à l'identique » en dehors d'Abidjan **ne crée pas de valeur à horizon raisonnable**. La rentabilité des nouvelles stations dépend de **trois leviers** : (1) la contribution par transaction (réduire le coût marketing du swap, supprimer les remises), (2) le mix (plus d'abonnements), (3) le coût d'installation (stations légères en dehors d'Abidjan). Un gain de **+40 %** de contribution (réaliste en cumulant fin des remises ≥ 15 % et marketing rééquilibré vers parrainage/WhatsApp/VTC) ramène le point mort d'une station moyenne de **49 à 29 mois** (35 mois si les charges fixes sont de 60 k).
* Ces chiffres dépendent des hypothèses ci-dessus : **la Finance doit confirmer le capex et les charges fixes avant décision d'investissement**.
""")

# =====================================================================================
md("""
# 6. Recommandations stratégiques

| # | Recommandation | Pourquoi (chiffres) | Impact attendu | Priorité |
|---|---|---|---|---|
| **1** | **Concentrer les ouvertures sur Abidjan et Dakar ; Douala conditionnel** : 8 Abidjan, 4 Dakar, 3 Cotonou, 3 Lomé, 2 Douala (si annulation < 10 %) | Abidjan : stations 2x plus productives, point mort 21 mois ; Douala : 15,5 % d'annulation, structurel | Évite de financer des stations qui ne se rentabilisent pas ; protège le capex | Immédiat |
| **2** | **Rééquilibrer le marketing vers Parrainage, WhatsApp et VTC ; plafonner TikTok/Meta pour le swap** | Parrainage ROI 35,9 vs TikTok 7,4 ; TikTok = 30 % du budget pour 18 % du CA, swap via TikTok = −340 k FCFA | Transférer ~1 M FCFA de TikTok vers Parrainage/WhatsApp/VTC ≈ **+4,5 M FCFA de CA** à budget constant (rendement marginal supposé = 50 % du ROI moyen) | T1 2027 |
| **3** | **Faire de l'abonnement le cœur de l'offre : convertir les clients swap** (offre dès le 5ᵉ swap, essai plafonné, ciblage des 469 clients « swap seul ») | Abonnement = 75 % du profit ; 1 abonné ≈ 9 600 FCFA de marge/mois vs 400 pour un client « swap seul » | 5-10 % de conversion ≈ **+0,6 à 1,3 M FCFA de marge / 6 mois** (+3 à 5 % du profit) | T1 2027 |
| **4** | **Plan « zéro remboursement » sur la location et les accessoires** (contrôle qualité des batteries, délais de livraison, alerte sur toute note ≤ 2) | 14 % de remboursements ; les remboursements effacent 79 % du profit de la location et 71 % de celui des accessoires ; 8,4 M FCFA rendus | Diviser par 2 les remboursements de ces deux lignes ≈ **+2,2 M FCFA de CA conservé / 6 mois** (coût du service déjà engagé : c'est autant de profit réel) | T1 2027 |
| **5** | **Encadrer les remises et cibler les PME/flottes** : plus de remise ≥ 15 %, validation > 10 %, offres flotte | Remises : aucun effet sur le volume, marge /2,6 à 20 % ; PME = profit réel/transaction x2 vs moto-taxis | **jusqu'à 3,3 M FCFA** de CA préservé (≈ 10 % de la marge) puisque les remises ne génèrent pas de volume ; mix plus rentable | Immédiat |

*Les gains sont des ordres de grandeur issus des scénarios du notebook (§4.4 à §5.3), sur une base de 6 mois ; ils ne se cumulent pas intégralement.*
""")
code("""
# Vérification des ordres de grandeur annoncés dans les recommandations 2, 4 et 5
remb_tot = df[df.statut == "Remboursée"].chiffre_affaires.sum()
loc_acc = df[df.type_service.isin(["Location journalière", "Accessoires & maintenance"])]
remb_la = loc_acc[loc_acc.statut == "Remboursée"].chiffre_affaires.sum()
print(f"CA remboursé total : {M(remb_tot)} FCFA | dont location + accessoires : {M(remb_la)} FCFA")
print(f"Reco 4 - diviser par 2 les remboursements location+accessoires : CA conservé ≈ {M(remb_la/2)} FCFA "
      "(= profit réel supplémentaire, le coût du service étant déjà engagé).")

# Reco 2 : réallouer 1 M FCFA de TikTok vers un mix Parrainage/WhatsApp/VTC (ROI marginal supposé = 50 % du ROI moyen, rendements décroissants)
cn2 = cn.copy()
mix_cible = cn2.loc[["Parrainage", "WhatsApp Business", "Partenariat chauffeurs VTC"]]
roi_cible = (mix_cible.ca.sum() - mix_cible.marketing.sum()) / mix_cible.marketing.sum()
roi_tiktok = cn2.loc["TikTok Ads", "roi_marketing"]
transfert = 1_000_000
# CA généré par FCFA investi = ROI + 1 ; rendement marginal du mix cible supposé = 50 % de sa moyenne
gain_ca = transfert * 0.5 * (roi_cible + 1) - transfert * (roi_tiktok + 1)
print(f"Reco 2 - ROI moyen mix cible = {roi_cible:.1f}, TikTok = {roi_tiktok:.1f} ; gain de CA d'un transfert de 1 M FCFA (rendements décroissants 50 %) ≈ {M(gain_ca)} FCFA")
""")
md("""
# 7. Conclusion business orientée action

**Le diagnostic en une phrase :** VoltRide gagne de l'argent grâce à **l'abonnement mensuel et à Abidjan**, mais en perd une partie par **les remboursements, les remises et un marketing mal réparti** ; ouvrir 20 stations sans corriger ces trois fuites reviendrait à **dupliquer le modèle actuel, y compris ses défauts**.

### Décisions demandées au comité de direction
1. **Valider la répartition des 20 stations** : 8 Abidjan · 4 Dakar · 3 Cotonou · 3 Lomé · **2 Douala conditionnelles**.
2. **Geler** les remises ≥ 15 % et **rééquilibrer** le budget marketing (TikTok/Meta → Parrainage, WhatsApp, VTC) **dès le 1er trimestre 2027**.
3. **Lancer deux chantiers qualité** : plan anti-remboursement (location, accessoires) et plan « exécution Douala ».
4. **Lancer le programme de conversion swap → abonnement**.
5. **Confirmer avec la Finance** capex et charges fixes d'une station (hypothèses du §5.3) avant d'engager l'investissement.

### Indicateurs de pilotage (à suivre mensuellement dans le dashboard)
| KPI | Aujourd'hui | Cible T2 2027 |
|---|---|---|
| Taux de remboursement | 7,4 % | < 5 % |
| Taux d'annulation Douala | 15,5 % | < 10 % |
| Part des remises ≥ 15 % | 10,1 % des transactions | 0 % |
| ROI marketing global | 13,2 | > 18 |
| Part des abonnés parmi les clients swap | 44 % | > 55 % |
| Rétention (actifs ≥ 2 mois) | 66 % | > 72 % |

### Limites de l'analyse
* **6 mois seulement** : pas de saisonnalité annuelle ; les croissances par ville se basent sur 3 mois contre 3 mois.
* Le **coût marketing est alloué par transaction** (pas de dépenses par campagne) : le ROI par canal est une approximation.
* **Corrections statistiques** (prix, marketing, coûts manquants) : ~6 % des lignes ; leur impact sur les totaux est faible mais non nul.
* **Point mort** : hypothèses de capex/charges fixes non issues des données.
* Les données sont **fictives** (cas pédagogique).
""")
code("""
# Vérification des KPI cibles cités dans la conclusion
print("Remises >= 15 % :", pct((df.remise_pct >= 15).mean()), "des transactions")
print("ROI marketing global :", f"{(df.chiffre_affaires.sum() - df.cout_marketing_fcfa.sum()) / df.cout_marketing_fcfa.sum():.1f}")
print("Taux de remboursement :", pct(kpis(df)['taux_remboursement']), "| annulation Douala :", pct(df[df.ville == 'Douala'].indicateur_annulation.mean()))
print("Livrables : df_clean ->", ROOT / "data/processed/df_clean.csv")
""")

# =====================================================================================
nb = nbf.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"}})
NB_PATH.parent.mkdir(exist_ok=True)
print("Exécution du notebook…")
ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
ep.preprocess(nb, {"metadata": {"path": str(NB_PATH.parent)}})
nbf.write(nb, NB_PATH)
html, _ = HTMLExporter().from_notebook_node(nb)
(ROOT / "reports" / "analyse_voltride_africa.html").write_text(html, encoding="utf-8")
print("OK :", NB_PATH)
