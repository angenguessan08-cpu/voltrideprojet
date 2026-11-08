"""Exporte les chiffres du PowerPoint dans reports/deck_data.json (lu par scripts/build_deck.js).

Aucun chiffre n'est saisi à la main dans le deck : tout provient de df_clean.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from voltride.analysis import (breakeven, client_table, group_table, kpis, load_clean, monthly, pareto,  # noqa: E402
                               station_table)

d = load_clean()
k = kpis(d)
e = d[d["statut"] != "Annulée"]
out: dict = {"kpi": {a: float(b) for a, b in k.items()}}

mo = monthly(d)
out["mois"] = {"labels": [["Janv", "Févr", "Mars", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"][m.month - 1] for m in mo["mois"]], "ca": (mo["ca"] / 1e6).round(2).tolist(),
               "profit": (mo["profit_net"] / 1e6).round(2).tolist(), "croissance_mai_oct": float(mo["ca"].iloc[-1] / mo["ca"].iloc[0] - 1)}

sv = group_table(d, "type_service").sort_values("ca", ascending=False)
out["services"] = {
    "noms": sv.index.tolist(), "ca": (sv.ca / 1e6).round(2).tolist(), "marge_pct": sv.marge_pct.round(3).tolist(),
    "profit_net": (sv.profit_net / 1e6).round(2).tolist(), "profit_reel": (sv.profit_net_reel / 1e6).round(2).tolist(),
    "remb": (sv.taux_remboursement * 100).round(1).tolist(),
    "part_ca": (sv.ca / sv.ca.sum() * 100).round(3).tolist(), "part_mkt": (sv.marketing / sv.marketing.sum() * 100).round(3).tolist(),
    "part_profit": (sv.profit_net / sv.profit_net.sum() * 100).round(3).tolist(),
    "part_tx": (sv.transactions / sv.transactions.sum() * 100).round(3).tolist(),
    "chute_profit": (1 - sv.profit_net_reel / sv.profit_net).round(3).tolist(),
}

vl = group_table(d, "ville").sort_values("ca", ascending=False)
mv = monthly(d, "ville").pivot(index="mois", columns="ville", values="ca")
st = station_table(d)
stv = st.groupby("ville").agg(contrib=("contribution_mensuelle", "mean"), tx=("transactions_mensuelles", "mean"))
HYP = dict(capex=2_500_000, fixes=45_000, ramp=3, taux0=0.5)
pm = {}
for v, g in st.groupby("ville"):
    pm[v] = breakeven(g.contribution_mensuelle.mean(), HYP["capex"], HYP["fixes"], HYP["ramp"], HYP["taux0"])["mois_retour"]
c_moy = st.contribution_mensuelle.mean()
out["villes"] = {
    "noms": vl.index.tolist(), "ca": (vl.ca / 1e6).round(2).tolist(), "profit_reel": (vl.profit_net_reel / 1e6).round(2).tolist(),
    "annulation": (vl.taux_annulation * 100).round(1).tolist(), "remb": (vl.taux_remboursement * 100).round(1).tolist(),
    "croissance": [round(float(mv[v].iloc[3:].sum() / mv[v].iloc[:3].sum() - 1) * 100, 1) for v in vl.index],
    "contrib_station": [round(float(stv.loc[v, "contrib"]) / 1e3) for v in vl.index],
    "tx_station": [round(float(stv.loc[v, "tx"]), 1) for v in vl.index],
    "point_mort": [pm[v] for v in vl.index],
    "part_ca": (vl.ca / vl.ca.sum() * 100).round(1).tolist(),
}
out["point_mort"] = {
    "hyp": HYP,
    "moyenne_base": breakeven(c_moy, HYP["capex"], HYP["fixes"], HYP["ramp"], HYP["taux0"])["mois_retour"],
    "moyenne_plus40": breakeven(c_moy * 1.4, HYP["capex"], HYP["fixes"], HYP["ramp"], HYP["taux0"])["mois_retour"],
}

cn = group_table(d[d.canal_acquisition != "Non renseigné"], "canal_acquisition").sort_values("roi_marketing", ascending=False)
cl = client_table(d)
cn["retention"] = cl.groupby("canal")["retenu"].mean()
swc = d[(d.type_service == "Swap batterie")].groupby("canal_acquisition").profit_net.sum()
out["canaux"] = {
    "noms": cn.index.tolist(), "roi": cn.roi_marketing.round(1).tolist(), "part_mkt": (cn.marketing / d.cout_marketing_fcfa.sum() * 100).round(3).tolist(),
    "part_ca": (cn.ca / d.chiffre_affaires.sum() * 100).round(3).tolist(), "cout_tx": (cn.marketing / cn.transactions).round(0).tolist(),
    "retention": (cn.retention * 100).round(1).tolist(), "annulation": (cn.taux_annulation * 100).round(1).tolist(),
    "remb": (cn.taux_remboursement * 100).round(1).tolist(), "swap_profit_k": {c: round(float(swc[c]) / 1e3) for c in cn.index},
}

p = pareto(cl)
n80 = int((p.part_cum <= 0.8).sum() + 1)
seg = cl.groupby("frequence", observed=True).agg(clients=("ca", "size"), ca=("ca", "sum"))
out["clients"] = {
    "total": int(d.id_client.nunique()), "actifs": int(len(cl)), "recurrents": float(cl.recurrent.mean()), "retenus": float(cl.retenu.mean()),
    "n80": n80, "pct80": float(n80 / len(p)), "freq_noms": [str(i) for i in seg.index],
    "freq_part_clients": (seg.clients / seg.clients.sum() * 100).round(1).tolist(), "freq_part_ca": (seg.ca / seg.ca.sum() * 100).round(1).tolist(),
    "top10_part": float(p.part_cum.iloc[9]),
    "note_remb": float(d[d.statut == "Remboursée"].note_client.mean()), "note_term": float(d[d.statut == "Terminée"].note_client.mean()),
}

mix = e.pivot_table(index="id_client", columns="type_service", values="quantite", aggfunc="sum", fill_value=0)
swap_cl = mix[mix["Swap batterie"] > 0]
swap_only = swap_cl[swap_cl["Abonnement mensuel"] == 0].index
abo = e[e.type_service == "Abonnement mensuel"]
abo_marge = abo.marge_brute.sum() / abo.quantite.sum()
sw_marge = e[(e.type_service == "Swap batterie") & e.id_client.isin(swap_only)].groupby("id_client").marge_brute.sum().mean() / 6
gain_mois = abo_marge - sw_marge
out["conversion"] = {
    "clients_swap": int(len(swap_cl)), "deja_abonnes_pct": float((swap_cl["Abonnement mensuel"] > 0).mean()), "swap_only": int(len(swap_only)),
    "abo_marge_mois": float(abo_marge), "swap_marge_mois": float(sw_marge),
    "scenarios": [{"taux": t, "clients": int(round(len(swap_only) * t)), "gain_M": round(len(swap_only) * t * gain_mois * 3 / 1e6, 4)} for t in (0.05, 0.10, 0.15)],
}

rm = e.groupby("remise_tranche", observed=True).agg(q=("quantite", "mean"), marge=("marge_brute", "mean"), remb=("indicateur_remboursement", "mean"))
sacrifice = float((e.quantite * e.prix_unitaire_fcfa * e.remise_pct / 100).sum())
out["remises"] = {
    "tranches": [str(i) for i in rm.index], "q": rm.q.round(2).tolist(), "marge_par_tx": rm.marge.round(0).tolist(),
    "remb": (rm.remb * 100).round(1).tolist(), "part_remisees": float((d.remise_pct > 0).mean()), "sacrifice_M": round(sacrifice / 1e6, 2),
    "sacrifice_pct_marge": float(sacrifice / d.marge_brute.sum()), "part_ge15": float((d.remise_pct >= 15).mean()),
}

sg = group_table(d[d.type_client != "Non renseigné"], "type_client")
sg["pr"] = sg.profit_net_reel / sg.transactions
sg = sg.sort_values("pr", ascending=False)
out["segments"] = {"noms": sg.index.tolist(), "profit_reel_tx": sg.pr.round(0).tolist(), "remb": (sg.taux_remboursement * 100).round(1).tolist(),
                   "part_ca": (sg.part_ca * 100).round(1).tolist(), "panier": sg.panier_moyen.round(0).tolist()}

loc_acc = d[d.type_service.isin(["Location journalière", "Accessoires & maintenance"]) & (d.statut == "Remboursée")].chiffre_affaires.sum()
cible = group_table(d[d.canal_acquisition.isin(["Parrainage", "WhatsApp Business", "Partenariat chauffeurs VTC"])].assign(g="x"), "g")
roi_cible = float(cible.roi_marketing.iloc[0])
roi_tik = float(cn.loc["TikTok Ads", "roi_marketing"])
out["impacts"] = {
    "remb_total_M": round(float(d[d.statut == "Remboursée"].chiffre_affaires.sum()) / 1e6, 2), "remb_loc_acc_M": round(float(loc_acc) / 1e6, 4),
    "gain_remb_M": round(float(loc_acc) / 2e6, 4), "gain_marketing_M": round((0.5 * (roi_cible + 1) - (roi_tik + 1)), 4),
    "roi_global": float((d.chiffre_affaires.sum() - d.cout_marketing_fcfa.sum()) / d.cout_marketing_fcfa.sum()),
}
dest = ROOT / "reports" / "deck_data.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else float(o)), encoding="utf-8")
print("OK :", dest)
