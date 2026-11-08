"""Dashboard VoltRide Africa.

Lancer :  streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from voltride.analysis import (ANTHRACITE, GRIS, PALETTE_CAT, ROUGE, VERT, breakeven, client_table,  # noqa: E402
                               group_table, kpis, load_clean, monthly, pareto, station_table)

_ICON = ROOT / "docs" / "logo_voltride_clair.png"
st.set_page_config(page_title="VoltRide Africa - Dashboard", page_icon=str(_ICON) if _ICON.exists() else None, layout="wide")


@st.cache_data
def get_data() -> pd.DataFrame:
    return load_clean()


def fcfa(x: float) -> str:
    return f"{x/1e6:,.1f} M".replace(",", " ") if abs(x) >= 1e6 else f"{x/1e3:,.0f} k".replace(",", " ")


def pct(x: float, n: int = 1) -> str:
    return "–" if pd.isna(x) else f"{x*100:.{n}f} %".replace(".", ",")


df_all = get_data()

# ------------------------------------------------------------------ barre latérale : filtres
logo = ROOT / "docs" / "logo_voltride_clair.png"
if logo.exists():
    st.sidebar.image(str(logo), width="stretch", alt="Logo VoltRide Motors")
st.sidebar.header("Filtres")
dmin, dmax = df_all["date_transaction"].min().date(), df_all["date_transaction"].max().date()
periode = st.sidebar.date_input("Période", (dmin, dmax), min_value=dmin, max_value=dmax)
villes = st.sidebar.multiselect("Ville", sorted(df_all["ville"].unique()), default=sorted(df_all["ville"].unique()))
services = st.sidebar.multiselect("Service", sorted(df_all["type_service"].unique()), default=sorted(df_all["type_service"].unique()))
canaux = st.sidebar.multiselect("Canal d'acquisition", sorted(df_all["canal_acquisition"].unique()),
                                default=sorted(df_all["canal_acquisition"].unique()))
segments = st.sidebar.multiselect("Type de client", sorted(df_all["type_client"].unique()),
                                  default=sorted(df_all["type_client"].unique()))

start, end = (periode[0], periode[-1]) if isinstance(periode, (tuple, list)) and len(periode) else (dmin, dmax)
df = df_all[
    df_all["date_transaction"].between(pd.Timestamp(start), pd.Timestamp(end))
    & df_all["ville"].isin(villes) & df_all["type_service"].isin(services)
    & df_all["canal_acquisition"].isin(canaux) & df_all["type_client"].isin(segments)
]
st.sidebar.caption(f"{len(df):,} transactions sélectionnées sur {len(df_all):,}".replace(",", " "))

st.title("VoltRide Africa · Tableau de bord stratégique")
st.caption("6 mois d'activité (mai - octobre 2026) · CA hors transactions annulées · montants en FCFA · données fictives")

if df.empty:
    st.warning("Aucune transaction ne correspond aux filtres. Élargissez la sélection.")
    st.stop()

k = kpis(df)
c = st.columns(6)
c[0].metric("Chiffre d'affaires", fcfa(k["ca_total"]))
c[1].metric("Profit net estimé", fcfa(k["profit_net"]))
c[2].metric("Profit net réel", fcfa(k["profit_net_reel"]), help="Après remboursements : le CA remboursé est rendu, le coût reste engagé.")
c[3].metric("Panier moyen", f"{k['panier_moyen']:,.0f}".replace(",", " "))
c[4].metric("Taux d'annulation", pct(k["taux_annulation"]))
c[5].metric("Taux de remboursement", pct(k["taux_remboursement"]))

tab_perf, tab_svc, tab_geo, tab_mkt, tab_cli, tab_station = st.tabs(
    ["📈 Performance", "🔋 Services", "🌍 Villes", "📣 Marketing", "👥 Clients", "🏪 Nouvelle station"])

# ------------------------------------------------------------------ performance
with tab_perf:
    mo = monthly(df)
    fig = go.Figure()
    fig.add_bar(x=mo["mois"], y=mo["ca"], name="CA", marker_color=ANTHRACITE)
    fig.add_bar(x=mo["mois"], y=mo["profit_net"], name="Profit net", marker_color=VERT)
    fig.add_scatter(x=mo["mois"], y=mo["annulation"] * 100, name="Annulation (%)", yaxis="y2", mode="lines+markers",
                    line=dict(color=ROUGE))
    fig.update_layout(barmode="overlay", title="CA, profit net et taux d'annulation par mois", height=420,
                      yaxis2=dict(overlaying="y", side="right", range=[0, max(15, mo["annulation"].max() * 130)], title="%"),
                      legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")
    col1, col2 = st.columns(2)
    k_tab = pd.DataFrame({
        "Indicateur": ["Transactions", "Clients", "CA total", "CA net des remboursements", "Marge brute (% CA)", "Coût marketing"],
        "Valeur": [f"{k['transactions']:,}".replace(",", " "), f"{k['clients']:,}".replace(",", " "), fcfa(k["ca_total"]), fcfa(k["ca_net"]),
                   f"{fcfa(k['marge_brute'])} ({pct(k['marge_pct'])})", fcfa(k["marketing"])]})
    col1.dataframe(k_tab, hide_index=True, width="stretch")
    mode = df.groupby("mode_paiement")["chiffre_affaires"].sum().reset_index()
    col2.plotly_chart(px.pie(mode, names="mode_paiement", values="chiffre_affaires", hole=0.5, title="CA par mode de paiement",
                             color_discrete_sequence=PALETTE_CAT), width="stretch")

# ------------------------------------------------------------------ services
with tab_svc:
    sv = group_table(df, "type_service").sort_values("ca", ascending=False).reset_index()
    col1, col2 = st.columns(2)
    fig = go.Figure()
    for nom, col, couleur in [("CA", "ca", ANTHRACITE), ("Marge brute", "marge_brute", GRIS), ("Profit net réel", "profit_net_reel", VERT)]:
        fig.add_bar(x=sv["type_service"], y=sv[col], name=nom, marker_color=couleur)
    fig.update_layout(barmode="group", title="CA, marge et profit réel par service", height=380, legend=dict(orientation="h", y=-0.25))
    col1.plotly_chart(fig, width="stretch")
    col2.plotly_chart(px.bar(sv, x="type_service", y=sv["taux_remboursement"] * 100, title="Taux de remboursement (%)",
                             color_discrete_sequence=[ROUGE], labels={"y": "%", "type_service": ""}).update_layout(height=380),
                      width="stretch")
    ms = monthly(df, "type_service")
    st.plotly_chart(px.line(ms, x="mois", y="ca", color="type_service", markers=True, color_discrete_sequence=PALETTE_CAT,
                            title="Évolution mensuelle du CA par service").update_layout(height=380, legend=dict(orientation="h", y=-0.2)),
                    width="stretch")
    show = sv.set_index("type_service")[["transactions", "ca", "marge_pct", "marketing", "profit_net", "profit_net_reel", "taux_annulation",
                                         "taux_remboursement", "roi_marketing"]]
    st.dataframe(show.style.format({"ca": "{:,.0f}", "marketing": "{:,.0f}", "profit_net": "{:,.0f}", "profit_net_reel": "{:,.0f}",
                                    "marge_pct": "{:.1%}", "taux_annulation": "{:.1%}", "taux_remboursement": "{:.1%}", "roi_marketing": "{:.1f}"}),
                 width="stretch")

# ------------------------------------------------------------------ villes
with tab_geo:
    vl = group_table(df, "ville").sort_values("ca", ascending=False).reset_index()
    col1, col2, col3 = st.columns(3)
    col1.plotly_chart(px.bar(vl, x="ville", y="ca", title="CA par ville", color_discrete_sequence=[ANTHRACITE]).update_layout(height=340),
                      width="stretch")
    col2.plotly_chart(px.bar(vl, x="ville", y="profit_net_reel", title="Profit net réel par ville",
                             color_discrete_sequence=[VERT]).update_layout(height=340), width="stretch")
    col3.plotly_chart(px.bar(vl, x="ville", y=vl["taux_annulation"] * 100, title="Taux d'annulation (%)", color_discrete_sequence=[ROUGE],
                             labels={"y": "%"}).update_layout(height=340), width="stretch")
    hm = df.pivot_table(index="ville", columns="mois", values="chiffre_affaires", aggfunc="sum")
    hm.columns = [m.strftime("%Y-%m") for m in hm.columns]
    st.plotly_chart(px.imshow(hm / 1e6, text_auto=".1f", color_continuous_scale="Greens", aspect="auto",
                              title="CA mensuel (M FCFA) : ville x mois", labels={"color": "M FCFA"}).update_layout(height=340),
                    width="stretch")
    an = df.pivot_table(index="ville", columns="type_service", values="indicateur_annulation", aggfunc="mean") * 100
    st.plotly_chart(px.imshow(an, text_auto=".1f", color_continuous_scale="Reds", aspect="auto",
                              title="Taux d'annulation (%) : ville x service").update_layout(height=340), width="stretch")

# ------------------------------------------------------------------ marketing
with tab_mkt:
    cn = group_table(df[df["canal_acquisition"] != "Non renseigné"], "canal_acquisition")
    cc = client_table(df)
    cn["retention"] = cc.groupby("canal")["retenu"].mean()
    cn = cn.sort_values("roi_marketing", ascending=False).reset_index()
    col1, col2 = st.columns(2)
    col1.plotly_chart(px.bar(cn, x="roi_marketing", y="canal_acquisition", orientation="h", title="ROI marketing = (CA − coût) / coût",
                             color="roi_marketing", color_continuous_scale="RdYlGn", text_auto=".1f").update_layout(
        height=380, yaxis=dict(autorange="reversed"), coloraxis_showscale=False), width="stretch")
    col2.plotly_chart(px.scatter(cn, x="marketing", y="roi_marketing", size="ca", color="taux_remboursement", text="canal_acquisition",
                                 color_continuous_scale="RdYlGn_r", title="Budget vs ROI (taille = CA, couleur = remboursement)",
                                 labels={"marketing": "Coût marketing (FCFA)", "roi_marketing": "ROI"}).update_traces(
        textposition="top center").update_layout(height=380), width="stretch")
    st.dataframe(cn.set_index("canal_acquisition")[["ca", "marketing", "roi_marketing", "roi_marge", "taux_annulation",
                                                    "taux_remboursement", "retention"]]
                 .style.format({"ca": "{:,.0f}", "marketing": "{:,.0f}", "roi_marketing": "{:.1f}", "roi_marge": "{:.1f}",
                                "taux_annulation": "{:.1%}", "taux_remboursement": "{:.1%}", "retention": "{:.1%}"}),
                 width="stretch")

# ------------------------------------------------------------------ clients
with tab_cli:
    cl = client_table(df)
    if cl.empty:
        st.info("Aucun client actif sur cette sélection.")
    else:
        a, b, c3, d4 = st.columns(4)
        a.metric("Clients actifs", f"{len(cl):,}".replace(",", " "))
        b.metric("Clients récurrents (≥ 2 transactions)", pct(cl["recurrent"].mean()))
        c3.metric("Clients retenus (≥ 2 mois actifs)", pct(cl["retenu"].mean()))
        d4.metric("Note moyenne", f"{df['note_client'].mean():.2f} / 5")
        p = pareto(cl)
        n80 = int((p["part_cum"] <= 0.8).sum() + 1)
        col1, col2 = st.columns(2)
        fig = go.Figure()
        fig.add_scatter(x=p["pct_clients"] * 100, y=p["part_cum"] * 100, mode="lines", line=dict(color=ANTHRACITE, width=3), name="CA cumulé")
        fig.add_hline(y=80, line_dash="dash", line_color=GRIS)
        fig.update_layout(title=f"Pareto : {n80} clients ({n80/len(p):.0%}) = 80 % du CA", xaxis_title="% cumulé des clients",
                          yaxis_title="% cumulé du CA", height=380)
        col1.plotly_chart(fig, width="stretch")
        seg = cl.groupby("frequence", observed=True).agg(clients=("ca", "size"), ca=("ca", "sum")).reset_index()
        col2.plotly_chart(px.bar(seg, x="frequence", y="ca", text="clients", title="CA par segment de fréquence (étiquette = nb clients)",
                                 color_discrete_sequence=[VERT]).update_layout(height=380), width="stretch")
        top = cl.sort_values("ca", ascending=False).head(10)[["type_client", "canal", "transactions", "ca", "profit_net"]]
        st.subheader("Top 10 clients")
        st.dataframe(top.style.format({"ca": "{:,.0f}", "profit_net": "{:,.0f}"}), width="stretch")
        nt = df.dropna(subset=["note_client"])
        if len(nt):
            r = nt.groupby(nt["note_client"].astype(int))["indicateur_remboursement"].mean().reset_index()
            st.plotly_chart(px.bar(r, x="note_client", y=r["indicateur_remboursement"] * 100, title="% de transactions remboursées selon la note",
                                   color_discrete_sequence=[ROUGE], labels={"y": "%", "note_client": "Note"}).update_layout(height=320),
                            width="stretch")

# ------------------------------------------------------------------ simulateur de station
with tab_station:
    st.subheader("Point mort d'une nouvelle station")
    st.caption("Hypothèses modifiables (à valider avec la Finance). La contribution de croisière est mesurée sur les stations existantes de la ville "
               "(marge brute − marketing), sur la sélection de filtres courante.")
    h1, h2, h3, h4 = st.columns(4)
    capex = h1.number_input("Investissement (FCFA)", 500_000, 20_000_000, 2_500_000, 100_000)
    fixes = h2.number_input("Charges fixes / mois (FCFA)", 0, 500_000, 45_000, 5_000)
    ramp = h3.slider("Mois de montée en charge", 0, 12, 3)
    taux0 = h4.slider("Activité pendant la montée", 0.1, 1.0, 0.5, 0.05)
    uplift = st.slider("Gain de contribution visé (remises, mix, marketing)", 0, 60, 0, 5, format="+%d %%") / 100
    stn = station_table(df_all[df_all["ville"].isin(villes)])
    if stn.empty:
        st.info("Aucune station sur cette sélection de villes.")
    else:
        rows = []
        fig = go.Figure()
        for ville, g in stn.groupby("ville"):
            contrib = g["contribution_mensuelle"].mean() * (1 + uplift)
            be = breakeven(contrib, capex, fixes, ramp, taux0)
            rows.append({"Ville": ville, "Contribution / mois": round(contrib), "Transactions / mois": round(g["transactions_mensuelles"].mean(), 1),
                         "Équilibre mensuel (mois)": str(be["mois_equilibre_mensuel"] or "> 72"),
                         "Point mort cash (mois)": str(be["mois_retour"] or "> 72")})
            cum = [-capex]
            for m in range(1, 61):
                cum.append(cum[-1] + contrib * (taux0 if m <= ramp else 1) - fixes)
            fig.add_scatter(x=list(range(61)), y=np.array(cum) / 1e6, mode="lines", name=ville)
        fig.add_hline(y=0, line_color="black")
        fig.update_layout(title="Cash cumulé d'une station (M FCFA)", xaxis_title="Mois depuis l'ouverture", height=400,
                          legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, width="stretch")
        st.dataframe(pd.DataFrame(rows).set_index("Ville"), width="stretch")

st.divider()
st.caption("Source : data/processed/df_clean.csv (voir notebooks/01_analyse_voltride_africa.ipynb pour le nettoyage et les analyses).")
