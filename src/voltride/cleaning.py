"""Nettoyage du dataset VoltRide Africa.

Chaque règle est appliquée par une fonction dédiée et son impact est consigné
dans un journal (``log``) afin de pouvoir être restitué dans l'audit.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date

import numpy as np
import pandas as pd

DATE_MIN, DATE_MAX = pd.Timestamp("2026-05-01"), pd.Timestamp("2026-10-31")

VILLE_PAYS = {
    "Abidjan": "Côte d'Ivoire",
    "Dakar": "Sénégal",
    "Douala": "Cameroun",
    "Cotonou": "Bénin",
    "Lomé": "Togo",
}
STATION_VILLE = {"ABI": "Abidjan", "DAK": "Dakar", "DOU": "Douala", "COT": "Cotonou", "LOM": "Lomé"}

CANAUX_BRUTS = {"Meta Ads (Facebook/Instagram)", "TikTok Ads", "Partenariat chauffeurs VTC", "Parrainage",
                "WhatsApp Business", "Affichage & stations"}
PAIEMENTS_BRUTS = {"Mobile Money (Orange/MTN/Moov/Wave)", "Espèces à la station", "Carte bancaire"}
SERVICES = ["Swap batterie", "Location journalière", "Abonnement mensuel", "Accessoires & maintenance"]
NON_RENSEIGNE = "Non renseigné"
MOIS_FR = {
    "janv": 1, "janvier": 1, "fevr": 2, "fev": 2, "fevrier": 2, "mars": 3, "avr": 4, "avril": 4,
    "mai": 5, "juin": 6, "juil": 7, "juillet": 7, "aout": 8, "sept": 9, "septembre": 9,
    "oct": 10, "octobre": 10, "nov": 11, "novembre": 11, "dec": 12, "decembre": 12,
}


# --------------------------------------------------------------------------- utilitaires
def _norm(s) -> str | float:
    """minuscule, sans accents, espaces normalisés."""
    if pd.isna(s):
        return np.nan
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def load_raw(path) -> pd.DataFrame:
    """Lecture brute : tout en texte, 'N/A' conservé comme valeur (pas comme manquant)."""
    return pd.read_csv(path, dtype=str, encoding="utf-8", keep_default_na=False, na_values=[""])


# --------------------------------------------------------------------------- dates
def parse_date(s) -> pd.Timestamp:
    """Interprète les 6 formats rencontrés. Renvoie NaT si absente ou impossible."""
    if pd.isna(s):
        return pd.NaT
    s = str(s).strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):                       # 2026-10-13
            y, m, d = map(int, s.split("-"))
        elif re.fullmatch(r"\d{4}/\d{2}/\d{2}", s):                     # 2026/10/13
            y, m, d = map(int, s.split("/"))
        elif re.fullmatch(r"\d{2}/\d{2}/\d{4}", s):                     # 28/06/2026 (jj/mm/aaaa)
            d, m, y = map(int, s.split("/"))
        elif re.fullmatch(r"\d{2}-\d{2}-\d{4}", s):                     # 10-18-2026 (mm-jj-aaaa)
            m, d, y = map(int, s.split("-"))
        elif re.fullmatch(r"\d{2}-\d{2}-\d{2}", s):                     # 13-06-26 (jj-mm-aa)
            d, m, y = map(int, s.split("-"))
            y += 2000
        else:                                                           # 17 août 2026
            parts = _norm(s).replace(".", "").split(" ")
            d, m, y = int(parts[0]), MOIS_FR[parts[1]], int(parts[2])
        return pd.Timestamp(date(y, m, d))
    except (ValueError, KeyError, IndexError):
        return pd.NaT


# --------------------------------------------------------------------------- catégories
def map_service(s) -> str | float:
    n = _norm(s)
    if pd.isna(n):
        return np.nan
    if "swap" in n or "echange" in n:
        return "Swap batterie"
    if n.startswith("loc"):
        return "Location journalière"
    if n.startswith("abo"):
        return "Abonnement mensuel"
    if n.startswith("access"):
        return "Accessoires & maintenance"
    return np.nan


def map_ville(s) -> str | float:
    """Corrige les fautes de frappe par proximité de préfixe / distance d'édition."""
    n = _norm(s)
    if pd.isna(n):
        return np.nan
    from difflib import get_close_matches

    cibles = {_norm(v): v for v in VILLE_PAYS}
    m = get_close_matches(n, list(cibles), n=1, cutoff=0.6)
    return cibles[m[0]] if m else np.nan


def map_canal(s) -> str:
    n = _norm(s)
    if pd.isna(n):
        return NON_RENSEIGNE
    if "tik" in n:
        return "TikTok Ads"
    if "meta" in n or "facebook" in n:
        return "Meta Ads"
    if "vtc" in n or "partenariat" in n:
        return "Partenariat chauffeurs VTC"
    if "rain" in n:
        return "Parrainage"
    if "whats" in n:
        return "WhatsApp Business"
    if "affichage" in n:
        return "Affichage & stations"
    return NON_RENSEIGNE


def map_paiement(s) -> str:
    n = _norm(s)
    if pd.isna(n):
        return NON_RENSEIGNE
    if "mobile" in n:
        return "Mobile Money"
    if "esp" in n or "cash" in n:
        return "Espèces"
    if "carte" in n or n == "cb":
        return "Carte bancaire"
    return NON_RENSEIGNE


def map_statut(s) -> str | float:
    n = _norm(s)
    if pd.isna(n):
        return np.nan
    if n.startswith("termin") or n.startswith("complet"):
        return "Terminée"
    if n.startswith("annul") or n.startswith("cancel"):
        return "Annulée"
    if n.startswith("rembours") or n.startswith("refund"):
        return "Remboursée"
    return np.nan


# --------------------------------------------------------------------------- pipeline
def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retourne ``(df_clean, log)``. ``log`` liste chaque règle et le nombre de lignes touchées."""
    log: list[dict] = []

    def note(regle: str, n: int, traitement: str):
        log.append({"regle": regle, "lignes_concernees": int(n), "traitement": traitement})

    df = raw.copy()
    n0 = len(df)

    # --- types numériques
    for c in ["quantite", "prix_unitaire_fcfa", "remise_pct", "cout_unitaire_fcfa",
              "cout_marketing_fcfa", "note_client"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # --- identifiants
    df["id_transaction"] = df["id_transaction"].str.strip().str.upper()
    df["id_client"] = df["id_client"].str.strip().str.upper()

    # --- doublons (après normalisation des identifiants, car certains diffèrent par la casse)
    # 1) lignes strictement identiques une fois les ids normalisés
    n = df.duplicated().sum()
    df = df.drop_duplicates()
    note("Doublons exacts (ids normalisés)", n, "Suppression, 1re occurrence conservée")
    # 2) même id_transaction, contenu différent
    n = df.duplicated("id_transaction").sum()
    df = df.drop_duplicates("id_transaction", keep="first")
    note("id_transaction répété (contenu différent)", n, "Suppression, 1re occurrence conservée")

    # --- dates
    df["date_transaction_brut"] = df["date_transaction"]
    df["date_transaction"] = df["date_transaction"].map(parse_date)
    n_formats = (~df["date_transaction_brut"].fillna("2026-01-01").str.fullmatch(r"\d{4}-\d{2}-\d{2}")).sum()
    note("Dates dans un format non ISO", n_formats, "Conversion vers AAAA-MM-JJ")
    hors = df["date_transaction"].notna() & ~df["date_transaction"].between(DATE_MIN, DATE_MAX)
    n_imposs = df["date_transaction"].isna().sum()
    df.loc[hors, "date_transaction"] = pd.NaT
    note("Dates manquantes, impossibles ou hors période", n_imposs + hors.sum(),
         "Suppression (impossible de rattacher la ligne à un mois)")
    df = df.dropna(subset=["date_transaction"])

    # --- statut
    df["statut"] = df["statut"].map(map_statut)
    note("Statuts hétérogènes (casse, accents, anglais)", (raw["statut"] != raw["statut"].map(map_statut)).sum(),
         "Uniformisation : Terminée / Annulée / Remboursée")
    df = df.dropna(subset=["statut"])

    # --- ville / pays
    v_brut = df["ville"]
    df["ville"] = df["ville"].map(map_ville)
    corrige = (v_brut.notna() & (v_brut != df["ville"])).sum()
    note("Villes mal orthographiées (casse, espaces, fautes)", corrige, "Correction par proximité de chaîne")
    df["station"] = df["station"].str.strip().str.upper()
    manq = df["ville"].isna()
    df.loc[manq, "ville"] = df.loc[manq, "station"].str[3:6].map(STATION_VILLE)
    note("Villes manquantes", manq.sum(), "Reconstituée depuis le code station (ST-XXX-NN)")
    df = df.dropna(subset=["ville"])
    pays_brut = df["pays"]
    df["pays"] = df["ville"].map(VILLE_PAYS)
    note("Pays à reconstituer (encodage ou incohérence avec la ville)", (pays_brut != df["pays"]).sum(),
         "Pays dérivé de la ville corrigée (référentiel)")
    df["station"] = df["station"].fillna(NON_RENSEIGNE)

    # --- service (les manquants sont inférés par le coût de revient, très discriminant)
    s_brut = df["service_brut"] = df["type_service"]
    df["type_service"] = df["type_service"].map(map_service)
    note("Libellés de service hétérogènes", (s_brut.notna() & (s_brut != df["type_service"])).sum(),
         "Uniformisation vers les 4 lignes de service")
    cout_ref = df.groupby("type_service")["cout_unitaire_fcfa"].median()
    manq = df["type_service"].isna()

    def infer_service(r):
        if pd.notna(r["cout_unitaire_fcfa"]):
            return (cout_ref - r["cout_unitaire_fcfa"]).abs().idxmin()
        return np.nan

    df.loc[manq, "type_service"] = df[manq].apply(infer_service, axis=1)
    note("Service manquant", manq.sum(), "Inféré par le coût unitaire le plus proche ; supprimé si coût absent")
    df = df.dropna(subset=["type_service"])

    # --- autres catégories
    df["canal_acquisition"] = df["canal_acquisition"].map(map_canal)
    df["mode_paiement"] = df["mode_paiement"].map(map_paiement)
    note("Canaux d'acquisition hétérogènes ou manquants", (~raw["canal_acquisition"].isin(CANAUX_BRUTS)).sum(),
         "Uniformisation vers 6 canaux, manquants -> 'Non renseigné'")
    note("Modes de paiement hétérogènes ou manquants", (~raw["mode_paiement"].isin(PAIEMENTS_BRUTS)).sum(),
         "Uniformisation vers 3 modes, manquants -> 'Non renseigné'")
    df["type_client"] = df["type_client"].fillna(NON_RENSEIGNE)
    df["type_batterie"] = df["type_batterie"].replace({"N/A": "Sans objet"}).fillna(NON_RENSEIGNE)

    # --- quantités
    zero = df["quantite"] == 0
    neg = df["quantite"] < 0
    irreal = df["quantite"] > 10
    note("Quantités nulles", zero.sum(), "Suppression")
    note("Quantités négatives", neg.sum(), "Valeur absolue (erreur de signe)")
    note("Quantités irréalistes (> 10 unités)", irreal.sum(), "Suppression")
    df.loc[neg, "quantite"] = df.loc[neg, "quantite"].abs()
    df = df[~zero & ~irreal]

    # --- prix unitaires : référence = médiane par service ; correction des facteurs 10 / 100
    df["prix_unitaire_fcfa"] = df["prix_unitaire_fcfa"].abs()
    ref = df.loc[df["prix_unitaire_fcfa"] > 0].groupby("type_service")["prix_unitaire_fcfa"].median()
    ratio = df["prix_unitaire_fcfa"] / df["type_service"].map(ref)
    df["flag_prix_corrige"] = 0
    neg_prix = (raw["prix_unitaire_fcfa"].astype(float) < 0).sum()
    note("Prix négatifs", neg_prix, "Valeur absolue")
    x10 = ratio.between(8, 12)
    x100 = ratio.between(80, 120)
    nul = df["prix_unitaire_fcfa"] == 0
    autre = ~ratio.between(0.5, 1.6) & ~x10 & ~x100 & ~nul
    df.loc[x10, "prix_unitaire_fcfa"] /= 10
    df.loc[x100, "prix_unitaire_fcfa"] /= 100
    df.loc[nul | autre, "prix_unitaire_fcfa"] = df.loc[nul | autre, "type_service"].map(ref)
    df.loc[x10 | x100 | nul | autre, "flag_prix_corrige"] = 1
    note("Prix multipliés par 10", x10.sum(), "Division par 10")
    note("Prix multipliés par 100", x100.sum(), "Division par 100")
    note("Prix nuls ou hors tolérance", (nul | autre).sum(), "Remplacés par la médiane du service")

    # --- remises
    r = df["remise_pct"]
    anorm = (r < 0) | (r > 100)
    note("Remises négatives", (r < 0).sum(), "Remplacées par 0 % (non vérifiable)")
    note("Remises > 100 %", (r > 100).sum(), "Remplacées par 0 % (non vérifiable)")
    df.loc[anorm, "remise_pct"] = 0.0

    # --- coûts
    cm = df["cout_unitaire_fcfa"].isna()
    df.loc[cm, "cout_unitaire_fcfa"] = df.loc[cm, "type_service"].map(df.groupby("type_service")["cout_unitaire_fcfa"].median())
    note("Coûts unitaires manquants", cm.sum(), "Médiane du service")

    seuil = 5000  # le P99.5 des coûts marketing est ~2 800 ; au-delà : saisie aberrante
    mm = df["cout_marketing_fcfa"].isna()
    ma = df["cout_marketing_fcfa"] > seuil
    med_canal = df.loc[~ma].groupby("canal_acquisition")["cout_marketing_fcfa"].median()
    df.loc[mm | ma, "cout_marketing_fcfa"] = df.loc[mm | ma, "canal_acquisition"].map(med_canal).fillna(
        df["cout_marketing_fcfa"].median())
    note("Coûts marketing manquants", mm.sum(), "Médiane du canal")
    note(f"Coûts marketing aberrants (> {seuil} FCFA)", ma.sum(), "Médiane du canal")

    df = df.drop(columns=["date_transaction_brut", "service_brut"]).sort_values("date_transaction").reset_index(drop=True)
    df["quantite"] = df["quantite"].astype(int)
    note("Lignes finales", len(df), f"{n0 - len(df)} lignes retirées sur {n0}")
    return df, pd.DataFrame(log)
