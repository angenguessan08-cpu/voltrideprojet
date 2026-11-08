"""Génère reports/resume_executif.docx (5 pages max) à partir de df_clean et des figures du notebook.

Usage : python scripts/build_summary.py   (après scripts/build_notebook.py)
"""
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from voltride.analysis import group_table, kpis, load_clean  # noqa: E402

FIG = ROOT / "reports" / "figures"
VERT, ANTH = RGBColor(0x0A, 0x8F, 0x1E), RGBColor(0x1B, 0x2A, 0x30)

d = load_clean()
k = kpis(d)
M = lambda x: f"{x/1e6:.1f} M".replace(".", ",")  # noqa: E731
P = lambda x: f"{x*100:.1f} %".replace(".", ",")  # noqa: E731

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(1.8)
sec.top_margin, sec.bottom_margin = Cm(2.0), Cm(1.3)
sec.header_distance = Cm(0.6)
_hp = sec.header.paragraphs[0]
_hp.paragraph_format.tab_stops.add_tab_stop(Cm(17.4), alignment=2)
_hp.add_run().add_picture(str(ROOT / "docs" / "logo_voltride_clair.png"), height=Cm(1.0))
_r = _hp.add_run("	VoltRide Motors · Résumé exécutif · Novembre 2026"); _r.font.size = Pt(8.5); _r.font.color.rgb = RGBColor(0x5B, 0x67, 0x70)
st = doc.styles["Normal"]
st.font.name, st.font.size = "Calibri", Pt(10)
st.paragraph_format.space_after = Pt(3)
st.paragraph_format.line_spacing = 1.05


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def h(text, size=13, color=ANTH, before=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(before), Pt(2)
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size); r.font.color.rgb = color
    return p


def para(text, bold_lead=None, size=10):
    p = doc.add_paragraph()
    if bold_lead:
        r = p.add_run(bold_lead); r.bold = True; r.font.size = Pt(size)
    r = p.add_run(text); r.font.size = Pt(size)
    return p


def bullet(text, lead=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(1)
    if lead:
        r = p.add_run(lead); r.bold = True
    p.add_run(text)
    return p


def table(rows, header, widths, size=9, head_fill="1B2A30"):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, hd in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""
        r = c.paragraphs[0].add_run(hd); r.bold = True; r.font.size = Pt(size); r.font.color.rgb = RGBColor(255, 255, 255)
        shade(c, head_fill)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
            if i == 0:
                r.bold = True
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.space_after = Pt(0)
    return t


def fig(name, width_cm=17.2, caption=None):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(FIG / name), width=Cm(width_cm))
    if caption:
        c = doc.add_paragraph(caption); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.runs[0].italic = True; c.runs[0].font.size = Pt(8)


# ============================================================ PAGE 1 : synthèse
t = doc.add_paragraph()
r = t.add_run("VoltRide Africa — Résumé exécutif"); r.bold = True; r.font.size = Pt(20); r.font.color.rgb = ANTH
s = doc.add_paragraph()
r = s.add_run("Analyse stratégique avant l'ouverture de 20 stations au S1 2027  ·  Période : mai - octobre 2026  ·  Destinataire : comité de direction")
r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

h("La réponse en 30 secondes", 13, VERT, 4)
para("VoltRide gagne de l'argent grâce à l'abonnement mensuel et à Abidjan, mais en perd une partie par les remboursements, les remises et un "
     "marketing mal réparti. Ouvrir 20 stations sans corriger ces fuites reviendrait à dupliquer le modèle actuel, défauts compris. "
     "Nous recommandons d'ouvrir 18 stations en vague 1 (8 Abidjan, 4 Dakar, 3 Cotonou, 3 Lomé), de subordonner 2 stations à Douala à la "
     "correction de son taux d'annulation, et de lancer 5 chantiers dès le 1er trimestre 2027.", size=10.5)

h("Chiffres clés (6 mois)", 12)
table([
    ["Chiffre d'affaires (hors annulées)", M(k["ca_total"]) + " FCFA", "Taux d'annulation", P(k["taux_annulation"])],
    ["Marge brute", f"{M(k['marge_brute'])} FCFA ({P(k['marge_pct'])})", "Taux de remboursement", P(k["taux_remboursement"])],
    ["Profit net estimé", M(k["profit_net"]) + " FCFA", "Panier moyen", f"{k['panier_moyen']:,.0f} FCFA".replace(",", " ")],
    ["Profit net réel (après remboursements)", M(k["profit_net_reel"]) + " FCFA", "Clients / transactions", f"{k['clients']:,} / {k['transactions']:,}".replace(",", " ")],
], ["Indicateur", "Valeur", "Indicateur", "Valeur"], [5.6, 4.2, 4.2, 3.4])
para("Les remboursements (8,4 M FCFA) effacent un tiers du profit net estimé. Le CA a progressé de +24 % entre mai et octobre ; le creux de juillet (−3 %) "
     "explique l'irrégularité perçue.", size=9)

h("Cinq constats", 12)
bullet(" 57 % du CA, 75 % du profit net, 35 % de marge. C'est la ligne à protéger et à développer.", "L'abonnement est le moteur :")
bullet(" 49 % des transactions et 49 % du budget marketing pour 1,6 % du profit (panier de 3 500 FCFA pour ~1 100 FCFA de marketing par transaction).", "Le swap est une porte d'entrée, pas un centre de profit :")
bullet(" 14 % de remboursements sur la location et les accessoires : ils effacent 79 % et 71 % de leur profit.", "La qualité de service coûte cher :")
bullet(" Parrainage ROI 35,9 contre 7,4 pour TikTok, qui absorbe 30 % du budget pour 18 % du CA.", "Le marketing est mal réparti :")
bullet(" 15,5 % d'annulation à Douala (deux fois les autres villes), chaque mois et dans presque toutes les stations ; les remises ne génèrent aucun volume supplémentaire.", "L'exécution et les remises détruisent de la valeur :")

h("Où ouvrir les 20 stations", 12)
table([
    ["Abidjan", "8", "Stations 2x plus productives (181 k FCFA de contribution/mois contre 66-94 k) ; +23 % ; point mort ~21 mois"],
    ["Dakar", "4", "Ville la plus saine (remboursement 6,2 %, annulation 8,2 %) ; croissance faible (+2 %) : renforcement"],
    ["Cotonou", "3", "Croissance la plus forte (+38 %) mais productivité faible : ouverture par paliers"],
    ["Lomé", "3", "+19 % ; surveiller les remboursements (8,4 %)"],
    ["Douala", "2 (conditionnel)", "Corriger l'exécution d'abord : ouvrir si l'annulation passe sous 10 %"],
], ["Ville", "Stations", "Justification"], [2.6, 3.0, 11.8], size=9)
doc.add_page_break()

# ============================================================ PAGE 2 : services & villes
h("1. Services : prioriser l'abonnement, assainir la location, repenser le swap", 13, VERT, 0)
fig("04_services.png", 17.4)
sv = group_table(d, "type_service").sort_values("ca", ascending=False)
table([[i, M(r.ca), P(r.marge_pct), M(r.profit_net), M(r.profit_net_reel), P(r.taux_remboursement), f"{r.roi_marketing:.1f}"]
       for i, r in sv.iterrows()], ["Service", "CA", "Marge", "Profit net", "Profit réel", "Remb.", "ROI mkt"], [5.2, 2.0, 1.9, 2.3, 2.3, 1.8, 1.9], size=8.5)
para("Question stratégique — quelle ligne prioriser ? L'abonnement, en y convertissant les clients swap ; optimiser en urgence la location et les accessoires "
     "(le levier est la qualité : batteries défectueuses, pannes, retards), et ne plus acquérir de clients swap via des canaux chers.", size=9.5)

h("2. Villes : où ouvrir, où corriger", 13, VERT, 8)
fig("05_villes.png", 17.4)
vl = group_table(d, "ville").sort_values("ca", ascending=False)
table([[i, M(r.ca), M(r.profit_net_reel), P(r.taux_annulation), P(r.taux_remboursement)] for i, r in vl.iterrows()],
      ["Ville", "CA", "Profit réel", "Annulation", "Remboursement"], [4.0, 3.0, 3.2, 3.2, 3.6], size=8.5)
para("Douala concentre le défaut d'exécution (15,5 % d'annulation contre 7,8-9,5 % ailleurs), de façon persistante : c'est un problème structurel de "
     "disponibilité ou de logistique, à traiter avant tout investissement supplémentaire.", size=9.5)
doc.add_page_break()

# ============================================================ PAGE 3 : marketing & clients
h("3. Marketing : réallouer vers Parrainage, WhatsApp et partenariats VTC", 13, VERT, 0)
fig("07_canaux.png", 17.4)
bullet(" ROI 35,9, 441 FCFA par transaction, rétention 72,6 %. 17,7 % du CA pour 6,8 % du budget.", "Parrainage :")
bullet(" ROI 7,4, 30 % du budget, annulation 13,1 %, remboursement 11 %, rétention la plus faible (61,3 %). Un client swap acquis via TikTok fait perdre 340 k FCFA au total.", "TikTok Ads :")
bullet(" À budget constant, transférer ~1 M FCFA de TikTok vers Parrainage/WhatsApp/VTC représenterait environ +4,5 M FCFA de CA (hypothèse : rendement marginal de 50 % du ROI moyen).", "Potentiel :")

h("4. Clients : concentration et rétention", 13, VERT, 8)
fig("08_pareto_segments.png", 15.6)
bullet(" 30 % des clients (318) font 80 % du CA ; les 230 clients fidèles (6+ transactions) font 68 % du CA. 70 % des clients sont récurrents, 66 % actifs sur au moins 2 mois.", "Portefeuille concentré :")
bullet(" les transactions remboursées sont notées 1,87/5 contre 3,93 ; aucune note ≥ 4 n'est remboursée. Une note ≤ 2 est un signal d'alerte exploitable avant le remboursement.", "Satisfaction :")
bullet(" 44 % des clients swap ont déjà un abonnement ; 469 restent « swap uniquement ». Un abonné rapporte ~9 600 FCFA de marge par mois contre ~400. "
       "5-10 % de conversion = +0,6 à 1,3 M FCFA de marge sur 6 mois.", "Swap → abonnement :")
doc.add_page_break()

# ============================================================ PAGE 4 : bonus
h("5. Segments, remises et point mort d'une station", 13, VERT, 0)
para("PME / flottes : segment le plus rentable (panier 23 600 FCFA, 5 064 FCFA de profit réel par transaction, le double des chauffeurs moto-taxi). "
     "Chauffeurs moto-taxi : le volume (40 % du CA). Particuliers : le moins rentable (11,7 % de remboursement, swap déficitaire).", size=9.5)
fig("11_remises.png", 17.0, "Les remises ne font pas acheter plus mais divisent par 2,6 la marge par transaction à 20 %")
para("Les promotions détruisent de la valeur : la quantité moyenne par transaction est plate (2,42 → 2,48), la marge par transaction chute de 62 % à 20 % de remise, "
     "le remboursement monte à 12,5 % et le profit réel devient négatif. Coût total : 3,3 M FCFA de CA sacrifié, soit 10,8 % de la marge brute.", size=9.5)
fig("12_point_mort.png", 12.5, "Cash cumulé d'une station neuve (capex 2,5 M FCFA, charges fixes 45 k FCFA/mois, montée en charge 3 mois à 50 %)")
para("Point mort cash : Abidjan ~21 mois, Dakar ~54, Douala ~63, Lomé et Cotonou au-delà de 72 mois au niveau de productivité actuel. "
     "Un gain de +40 % de contribution (fin des remises ≥ 15 %, marketing rééquilibré) ramène une station moyenne de 49 à 29 mois. "
     "Hypothèses de capex et de charges fixes à confirmer avec la Finance.", size=9.5)
doc.add_page_break()

# ============================================================ PAGE 5 : recommandations
h("Cinq recommandations stratégiques", 14, VERT, 0)
table([
    ["1", "Concentrer les ouvertures sur Abidjan et Dakar ; Douala conditionnel (8 / 4 / 3 / 3 / 2)",
     "Abidjan : stations 2x plus productives, point mort 21 mois. Douala : 15,5 % d'annulation, structurel.", "Évite de financer des stations non rentables"],
    ["2", "Rééquilibrer le marketing vers Parrainage, WhatsApp et VTC ; plafonner TikTok/Meta pour le swap",
     "ROI 35,9 vs 7,4 ; TikTok = 30 % du budget pour 18 % du CA.", "≈ +4,5 M FCFA de CA par M FCFA transféré (hypothèse prudente)"],
    ["3", "Faire de l'abonnement le cœur de l'offre : offre dès le 5e swap, essai plafonné, ciblage des 469 clients « swap seul »",
     "Abonnement = 75 % du profit ; 9 600 vs 400 FCFA de marge/mois.", "+0,6 à 1,3 M FCFA de marge sur 6 mois"],
    ["4", "Plan « zéro remboursement » location et accessoires : contrôle qualité des batteries, délais, alerte sur toute note ≤ 2",
     "14 % de remboursements ; 79 % et 71 % du profit effacés ; 4,3 M FCFA rendus sur ces deux lignes.", "≈ +2,2 M FCFA conservés si divisés par 2"],
    ["5", "Encadrer les remises (plus de ≥ 15 %, validation > 10 %) et cibler les PME/flottes",
     "Aucun effet volume ; marge divisée par 2,6 à 20 % ; PME = profit réel/transaction x2.", "Jusqu'à 3,3 M FCFA préservés ; mix plus rentable"],
], ["#", "Recommandation", "Pourquoi", "Impact (6 mois)"], [0.7, 6.2, 6.1, 4.2], size=8.5)

h("Conclusion : décisions demandées au comité", 12)
bullet(" 8 Abidjan, 4 Dakar, 3 Cotonou, 3 Lomé, 2 Douala sous condition (annulation < 10 %).", "Valider la répartition des 20 stations :")
bullet(" geler les remises ≥ 15 % et rééquilibrer le marketing dès le 1er trimestre 2027.", "Agir sur les fuites :")
bullet(" anti-remboursement (location, accessoires), exécution Douala, conversion swap → abonnement.", "Lancer trois chantiers :")
bullet(" capex et charges fixes d'une station avant d'engager l'investissement.", "Confirmer avec la Finance :")

h("Indicateurs de pilotage (dashboard Streamlit)", 11, ANTH, 6)
table([["Taux de remboursement", "7,4 %", "< 5 %"], ["Taux d'annulation Douala", "15,5 %", "< 10 %"],
       ["Remises ≥ 15 % (part des transactions)", "10,1 %", "0 %"], ["ROI marketing global", "13,2", "> 18"],
       ["Abonnés parmi les clients swap", "44 %", "> 55 %"], ["Rétention (actifs ≥ 2 mois)", "66 %", "> 72 %"]],
      ["KPI", "Aujourd'hui", "Cible T2 2027"], [8.0, 3.5, 3.5], size=8.5)
para("Limites : 6 mois de données (pas de saisonnalité annuelle) ; marketing alloué par transaction (ROI par canal approximatif) ; ~6 % des lignes corrigées "
     "statistiquement ; hypothèses de point mort non issues des données ; données fictives. Détail et méthode : notebook "
     "notebooks/01_analyse_voltride_africa.ipynb.", size=8.5)

out = ROOT / "reports" / "resume_executif.docx"
doc.save(out)
print("OK :", out)
