"""Fonctions d'analyse partagées par le notebook, le dashboard et le résumé exécutif."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLEAN_PATH = ROOT / "data" / "processed" / "df_clean.csv"

# Charte graphique VoltRide (extraite du logo) : noir anthracite + vert électrique
NOIR, VERT_LOGO, VERT_PROFOND = "#1B2A30", "#10EC27", "#0A8F1E"
VERT = "#18C02F"                                # vert du logo légèrement adouci pour les graphiques sur fond blanc
VERT_TEXTE = VERT_PROFOND                      # le vert du logo est trop clair pour du texte sur fond blanc
ANTHRACITE, GRIS, GRIS_CLAIR, ROUGE, ORANGE = NOIR, "#8A96A0", "#EEF2F3", "#D93025", "#F59E0B"
PALETTE_CAT = [NOIR, VERT, "#3B82F6", ORANGE, "#8B5CF6", "#06B6D4", GRIS]


def load_clean(path: Path = CLEAN_PATH) -> pd.DataFrame:
    d = pd.read_csv(path, parse_dates=["date_transaction", "mois"], keep_default_na=False, na_values=[""])
    d["frequence_client"] = pd.Categorical(
        d["frequence_client"], ["Occasionnel (1-2)", "Régulier (3-5)", "Fidèle (6+)"], ordered=True)
    d["remise_tranche"] = pd.Categorical(d["remise_tranche"], ["0 %", "5 %", "10 %", "15 %", "20 %"], ordered=True)
    return d


def _eff(d: pd.DataFrame) -> pd.DataFrame:
    """Transactions non annulées."""
    return d[d["statut"] != "Annulée"]


def kpis(d: pd.DataFrame) -> dict:
    eff = _eff(d)
    return {
        "transactions": len(d),
        "clients": d["id_client"].nunique(),
        "ca_total": d["chiffre_affaires"].sum(),
        "ca_net": d["ca_net"].sum(),
        "marge_brute": d["marge_brute"].sum(),
        "marketing": d["cout_marketing_fcfa"].sum(),
        "profit_net": d["profit_net"].sum(),
        "profit_net_reel": d["profit_net_reel"].sum(),
        "panier_moyen": eff["chiffre_affaires"].mean() if len(eff) else np.nan,
        "taux_annulation": d["indicateur_annulation"].mean() if len(d) else np.nan,
        "taux_remboursement": eff["indicateur_remboursement"].mean() if len(eff) else np.nan,
        "marge_pct": d["marge_brute"].sum() / d["chiffre_affaires"].sum() if d["chiffre_affaires"].sum() else np.nan,
        "note_moyenne": d["note_client"].mean(),
    }


def group_table(d: pd.DataFrame, by) -> pd.DataFrame:
    """Tableau de synthèse par dimension (service, ville, canal, segment...)."""
    g = d.groupby(by, observed=True)
    eff = _eff(d).groupby(by, observed=True)
    t = pd.DataFrame({
        "transactions": g.size(),
        "ca": g["chiffre_affaires"].sum(),
        "ca_net": g["ca_net"].sum(),
        "marge_brute": g["marge_brute"].sum(),
        "marketing": g["cout_marketing_fcfa"].sum(),
        "profit_net": g["profit_net"].sum(),
        "profit_net_reel": g["profit_net_reel"].sum(),
        "panier_moyen": eff["chiffre_affaires"].mean(),
        "taux_annulation": g["indicateur_annulation"].mean(),
        "taux_remboursement": eff["indicateur_remboursement"].mean(),
        "note_moyenne": g["note_client"].mean(),
    })
    t["marge_pct"] = t["marge_brute"] / t["ca"]
    t["roi_marketing"] = (t["ca"] - t["marketing"]) / t["marketing"]
    t["roi_marge"] = (t["marge_brute"] - t["marketing"]) / t["marketing"]
    t["part_ca"] = t["ca"] / t["ca"].sum()
    return t


def monthly(d: pd.DataFrame, by=None) -> pd.DataFrame:
    keys = ["mois"] if by is None else ["mois", by]
    return d.groupby(keys, observed=True).agg(
        ca=("chiffre_affaires", "sum"), profit_net=("profit_net", "sum"),
        transactions=("id_transaction", "size"), annulation=("indicateur_annulation", "mean")).reset_index()


def client_table(d: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par client (transactions effectives = non annulées)."""
    eff = _eff(d)
    c = eff.groupby("id_client").agg(
        transactions=("id_transaction", "size"), ca=("chiffre_affaires", "sum"),
        profit_net=("profit_net", "sum"), mois_actifs=("mois", "nunique"),
        remboursements=("indicateur_remboursement", "sum"), note=("note_client", "mean"))
    connu = d[d["canal_acquisition"] != "Non renseigné"]
    c["canal"] = c.index.map(connu.groupby("id_client")["canal_acquisition"].agg(lambda s: s.mode().iat[0]))
    c["type_client"] = c.index.map(d.groupby("id_client")["type_client"].agg(lambda s: s.mode().iat[0]))
    c["recurrent"] = c["transactions"] >= 2
    c["retenu"] = c["mois_actifs"] >= 2
    c["frequence"] = pd.cut(c["transactions"], [0, 2, 5, np.inf],
                            labels=["Occasionnel (1-2)", "Régulier (3-5)", "Fidèle (6+)"])
    return c


def pareto(c: pd.DataFrame, col: str = "ca") -> pd.DataFrame:
    s = c[[col]].sort_values(col, ascending=False)
    s["part_cum"] = s[col].cumsum() / s[col].sum()
    s["pct_clients"] = np.arange(1, len(s) + 1) / len(s)
    return s


def station_table(d: pd.DataFrame) -> pd.DataFrame:
    """Contribution mensuelle moyenne par station (marge brute - marketing)."""
    s = d[d["station"] != "Non renseigné"]
    nb_mois = max(s["mois"].nunique(), 1)
    t = s.groupby(["ville", "station"]).agg(
        transactions=("id_transaction", "size"), ca=("chiffre_affaires", "sum"),
        marge=("marge_brute", "sum"), marketing=("cout_marketing_fcfa", "sum")).reset_index()
    t["contribution_mensuelle"] = (t["marge"] - t["marketing"]) / nb_mois
    t["transactions_mensuelles"] = t["transactions"] / nb_mois
    t["ca_mensuel"] = t["ca"] / nb_mois
    return t


def breakeven(contribution_mensuelle: float, capex: float, charges_fixes: float,
              montee_en_charge: int = 3, taux_initial: float = 0.5, horizon: int = 72) -> dict:
    """Point mort d'une station.

    * mois 1..``montee_en_charge`` : la contribution vaut ``taux_initial`` x le régime de croisière ;
    * les charges fixes sont dues dès le 1er mois ;
    * ``mois_equilibre_mensuel`` : 1er mois où le résultat mensuel est >= 0 ;
    * ``mois_retour`` : 1er mois où le cash cumulé (après capex) redevient >= 0.
    """
    cum, eq, retour = -capex, None, None
    for m in range(1, horizon + 1):
        contrib = contribution_mensuelle * (taux_initial if m <= montee_en_charge else 1.0)
        net = contrib - charges_fixes
        cum += net
        if eq is None and net >= 0:
            eq = m
        if retour is None and cum >= 0:
            retour = m
    return {"mois_equilibre_mensuel": eq, "mois_retour": retour, "cash_cumule_fin": cum}
