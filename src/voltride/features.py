"""Feature engineering : indicateurs financiers et clients."""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les variables demandées (CA, marge, profit, remboursement, CLV…).

    Conventions
    -----------
    * ``chiffre_affaires`` = qté x prix x (1 - remise) pour les transactions non annulées (énoncé).
    * ``ca_net`` = idem mais nul pour les transactions remboursées (argent rendu au client).
    * Une transaction annulée n'a ni CA ni coût de service ; le coût marketing, lui, est dépensé.
    """
    d = df.copy()
    annulee = d["statut"].eq("Annulée")
    rembours = d["statut"].eq("Remboursée")

    d["chiffre_affaires"] = np.where(
        annulee, 0.0, d["quantite"] * d["prix_unitaire_fcfa"] * (1 - d["remise_pct"] / 100))
    d["cout_service"] = np.where(annulee, 0.0, d["quantite"] * d["cout_unitaire_fcfa"])
    d["marge_brute"] = d["chiffre_affaires"] - d["cout_service"]
    d["profit_net"] = d["marge_brute"] - d["cout_marketing_fcfa"]

    # version prudente : le CA remboursé est rendu au client, le coût reste engagé
    d["ca_net"] = np.where(rembours, 0.0, d["chiffre_affaires"])
    d["profit_net_reel"] = d["ca_net"] - d["cout_service"] - d["cout_marketing_fcfa"]

    d["mois"] = d["date_transaction"].dt.to_period("M").dt.to_timestamp()
    d["mois_label"] = d["date_transaction"].dt.strftime("%Y-%m")
    d["indicateur_remboursement"] = rembours.astype(int)
    d["indicateur_annulation"] = annulee.astype(int)

    # clients : nombre de transactions effectives (hors annulées)
    effectif = d[~annulee]
    d["nombre_transactions_par_client"] = d["id_client"].map(effectif.groupby("id_client").size()).fillna(0).astype(int)
    d["valeur_vie_client"] = d["id_client"].map(d.groupby("id_client")["profit_net"].sum())
    d["frequence_client"] = pd.cut(
        d["nombre_transactions_par_client"], bins=[-1, 2, 5, np.inf],
        labels=["Occasionnel (1-2)", "Régulier (3-5)", "Fidèle (6+)"])
    d["remise_tranche"] = pd.cut(d["remise_pct"], bins=[-0.1, 0, 5, 10, 15, 20],
                                 labels=["0 %", "5 %", "10 %", "15 %", "20 %"])
    return d
