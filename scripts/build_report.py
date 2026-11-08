"""Génère le rapport complet : reports/VoltRide_Rapport_Strategique.docx (+ PDF via Word si disponible).

Usage : python scripts/export_deck_data.py && python scripts/build_report.py
Tous les chiffres viennent de reports/deck_data.json (calculé depuis df_clean).
"""
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FIG, DOCS, REP = ROOT / "reports" / "figures", ROOT / "docs", ROOT / "reports"
D = json.loads((REP / "deck_data.json").read_text(encoding="utf-8"))
K, S, V, CN, CL, R, SG, CV, I, PM = (D[x] for x in ["kpi", "services", "villes", "canaux", "clients", "remises", "segments", "conversion", "impacts", "point_mort"])

NOIR, VERT_P = RGBColor(0x1B, 0x2A, 0x30), RGBColor(0x0A, 0x8F, 0x1E)
GRIS = RGBColor(0x5B, 0x67, 0x70)
NB = "\u00A0"


def num(x, dec=0):
    s = f"{abs(x):,.{dec}f}".replace(",", NB).replace(".", ",")
    return ("\u2212" if x < 0 else "") + s


pct = lambda x, dec=1: f"{num(x, dec)}{NB}%"  # noqa: E731
Mf = lambda x, dec=1: f"{num(x, dec)}{NB}M{NB}FCFA"  # noqa: E731
iS = lambda n: S["noms"].index(n)  # noqa: E731
iV = lambda n: V["noms"].index(n)  # noqa: E731
iC = lambda n: CN["noms"].index(n)  # noqa: E731

# ------------------------------------------------------------------ page de garde (image pleine page, charte du logo)
def make_cover(path: Path):
    W, H = 2480, 3508
    img = Image.new("RGB", (W, H), "#1B2A30")
    logo = Image.open(DOCS / "logo_voltride_sombre.png").convert("RGBA")
    logo = logo.resize((1250, int(1250 * logo.height / logo.width)))
    img.paste(logo, ((W - logo.width) // 2, 420), logo)
    d = ImageDraw.Draw(img)
    f = lambda name, size: ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)  # noqa: E731
    d.text((190, 2050), "Rapport d'analyse", font=f("calibrib.ttf", 150), fill="#FFFFFF")
    d.text((190, 2230), "stratégique", font=f("calibrib.ttf", 150), fill="#FFFFFF")
    d.text((190, 2520), "Ouverture de 20 nouvelles stations au S1 2027", font=f("calibri.ttf", 70), fill="#C9D3D8")
    d.text((190, 2640), "Diagnostic de performance et recommandations", font=f("calibri.ttf", 70), fill="#C9D3D8")
    d.text((190, 3150), "Direction générale  ·  Novembre 2026", font=f("calibri.ttf", 56), fill="#C9D3D8")
    d.text((190, 3235), "Période analysée : mai - octobre 2026", font=f("calibri.ttf", 56), fill="#C9D3D8")
    d.text((W - 190 - d.textlength("Drive the future.", font=f("calibrib.ttf", 56)), 3235), "Drive the future.", font=f("calibrib.ttf", 56), fill="#10EC27")
    img.save(path, quality=92)


cover_png = REP / "figures" / "_cover.png"
make_cover(cover_png)

# ------------------------------------------------------------------ document
doc = Document()
st = doc.styles["Normal"]
st.font.name, st.font.size = "Calibri", Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.paragraph_format.space_after, st.paragraph_format.line_spacing = Pt(5), 1.1
for name, size, color, before in [("Heading 1", 18, NOIR, 0), ("Heading 2", 13, VERT_P, 10)]:
    h = doc.styles[name]
    h.font.name, h.font.size, h.font.bold, h.font.color.rgb = "Calibri", Pt(size), True, color
    h.element.rPr.rFonts.set(qn("w:ascii"), "Calibri"); h.element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    h.paragraph_format.space_before, h.paragraph_format.space_after, h.paragraph_format.keep_with_next = Pt(before), Pt(5), True

# --- section 1 : couverture sans marges
s0 = doc.sections[0]
s0.page_width, s0.page_height = Cm(21), Cm(29.7)
s0.left_margin = s0.right_margin = s0.top_margin = s0.bottom_margin = Cm(0)
s0.header_distance = s0.footer_distance = Cm(0)
p = doc.paragraphs[0] if doc.paragraphs else doc.add_paragraph()
p.paragraph_format.space_after = Pt(0)
p.add_run().add_picture(str(cover_png), width=Cm(20.9), height=Cm(29.55))

# --- section 2 : corps
s1 = doc.add_section(WD_SECTION.NEW_PAGE)
s1.page_width, s1.page_height = Cm(21), Cm(29.7)
s1.left_margin = s1.right_margin = Cm(2.2)
s1.top_margin, s1.bottom_margin = Cm(2.6), Cm(2.0)
s1.header_distance, s1.footer_distance = Cm(0.9), Cm(0.8)
s1.header.is_linked_to_previous = False
s1.footer.is_linked_to_previous = False


def fld(par, code):
    for t, txt in (("begin", None), (None, code), ("end", None)):
        r = par.add_run()
        if t:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), t); r._r.append(e)
        else:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; r._r.append(e)
        r.font.size = Pt(9); r.font.color.rgb = GRIS


hp = s1.header.paragraphs[0]
hp.paragraph_format.tab_stops.add_tab_stop(Cm(16.6), alignment=2)
hp.add_run().add_picture(str(DOCS / "logo_voltride_clair.png"), height=Cm(1.1))
r = hp.add_run("\tRapport d'analyse stratégique · VoltRide Africa"); r.font.size = Pt(9); r.font.color.rgb = GRIS
fp = s1.footer.paragraphs[0]
fp.paragraph_format.tab_stops.add_tab_stop(Cm(16.6), alignment=2)
r = fp.add_run("VoltRide Motors · Novembre 2026 · Document confidentiel\tPage "); r.font.size = Pt(9); r.font.color.rgb = GRIS
fld(fp, "PAGE")


def shade(cell, fill):
    pr = cell._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill); pr.append(sh)


def para(text="", bold_lead=None, size=10.5, color=None, italic=False, after=5, align=None):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(after)
    if align:
        p.alignment = align
    if bold_lead:
        r = p.add_run(bold_lead); r.bold = True; r.font.size = Pt(size)
    r = p.add_run(text); r.font.size = Pt(size); r.italic = italic
    if color:
        r.font.color.rgb = color
    return p


def bullet(text, lead=None):
    p = doc.add_paragraph(style="List Bullet"); p.paragraph_format.space_after = Pt(2)
    if lead:
        r = p.add_run(lead); r.bold = True
    p.add_run(text)


def table(rows, header, widths, size=9, first_bold=True):
    t = doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    for i, hd in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""
        r = c.paragraphs[0].add_run(hd); r.bold = True; r.font.size = Pt(size); r.font.color.rgb = RGBColor(255, 255, 255)
        shade(c, "1B2A30")
    for n, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
            r.bold = bool(first_bold and i == 0)
            if n % 2:
                shade(cells[i], "F3F6F7")
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
        for c in row.cells:
            for pp in c.paragraphs:
                pp.paragraph_format.space_after = Pt(1); pp.paragraph_format.line_spacing = 1.0
    sp = doc.add_paragraph(); sp.paragraph_format.space_after = Pt(0); sp.paragraph_format.line_spacing = Pt(5)
    return t


def fig(name, width=16.4, caption=None):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(2); p.paragraph_format.keep_with_next = bool(caption)
    p.add_run().add_picture(str(FIG / name), width=Cm(width))
    if caption:
        c = doc.add_paragraph(caption); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; c.paragraph_format.space_after = Pt(8)
        c.runs[0].italic = True; c.runs[0].font.size = Pt(8.5); c.runs[0].font.color.rgb = GRIS


def callout(title, text, fill="EEF2F3"):
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    c = t.rows[0].cells[0]; c.width = Cm(16.6); shade(c, fill); c.text = ""
    r = c.paragraphs[0].add_run(title); r.bold = True; r.font.size = Pt(10.5); r.font.color.rgb = VERT_P if fill == "EEF2F3" else RGBColor(0x10, 0xEC, 0x27)
    q = c.add_paragraph(); rr = q.add_run(text); rr.font.size = Pt(10.5)
    if fill != "EEF2F3":
        rr.font.color.rgb = RGBColor(255, 255, 255)
    for pp in c.paragraphs:
        pp.paragraph_format.space_after = Pt(3)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ------------------------------------------------------------------ sommaire (champ TOC mis à jour par Word)
doc.add_heading("Sommaire", 1)
tp = doc.add_paragraph()
fb = OxmlElement("w:fldChar"); fb.set(qn("w:fldCharType"), "begin")
it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = 'TOC \\o "1-2" \\h \\z \\u'
fs = OxmlElement("w:fldChar"); fs.set(qn("w:fldCharType"), "separate")
tt = OxmlElement("w:t"); tt.text = "Sommaire à mettre à jour (clic droit > Mettre à jour les champs)."
fe = OxmlElement("w:fldChar"); fe.set(qn("w:fldCharType"), "end")
for el in (fb, it, fs):
    rr = tp.add_run(); rr._r.append(el)
rr = tp.add_run(); rr._r.append(tt)
rr = tp.add_run(); rr._r.append(fe)
page_break()

# ================================================================== 1. Synthèse
doc.add_heading("1. Synthèse exécutive", 1)
callout("La réponse en bref",
        "VoltRide gagne de l'argent grâce à l'abonnement mensuel et à Abidjan, mais en perd une partie par les remboursements, les remises et un marketing "
        "mal réparti. Nous recommandons d'ouvrir 18 stations en vague 1 (8 Abidjan, 4 Dakar, 3 Cotonou, 3 Lomé), de subordonner 2 stations à Douala à la "
        "correction de son taux d'annulation, et de lancer cinq chantiers dès le premier trimestre 2027.", fill="1B2A30")
table([
    ["Chiffre d'affaires (hors annulées)", Mf(K["ca_total"] / 1e6), "Taux d'annulation", pct(K["taux_annulation"] * 100)],
    ["Marge brute", f"{Mf(K['marge_brute'] / 1e6)} ({pct(K['marge_pct'] * 100)})", "Taux de remboursement", pct(K["taux_remboursement"] * 100)],
    ["Profit net estimé", Mf(K["profit_net"] / 1e6), "Panier moyen", f"{num(K['panier_moyen'])}{NB}FCFA"],
    ["Profit net réel (après remboursements)", Mf(K["profit_net_reel"] / 1e6), "Clients / transactions", f"{num(K['clients'])} / {num(K['transactions'])}"],
], ["Indicateur", "Valeur", "Indicateur", "Valeur"], [5.6, 4.0, 4.0, 3.0])
doc.add_heading("Les cinq constats", 2)
bullet(f" {pct(S['part_ca'][0], 0)} du CA, {pct(S['part_profit'][0], 0)} du profit net, {pct(S['marge_pct'][0] * 100, 0)} de marge. C'est la ligne à protéger et à développer.", "L'abonnement est le moteur :")
bullet(f" {pct(S['part_tx'][iS('Swap batterie')], 0)} des transactions et {pct(S['part_mkt'][iS('Swap batterie')], 0)} du budget marketing pour {pct(S['part_profit'][iS('Swap batterie')])} du profit.", "Le swap est une porte d'entrée, pas un centre de profit :")
bullet(f" environ 14{NB}% de remboursements sur la location et les accessoires ; ils effacent {pct(S['chute_profit'][iS('Location journalière')] * 100, 0)} et {pct(S['chute_profit'][iS('Accessoires & maintenance')] * 100, 0)} de leur profit.", "La qualité de service coûte cher :")
bullet(f" ROI de {num(CN['roi'][0], 1)} pour le parrainage contre {num(CN['roi'][iC('TikTok Ads')], 1)} pour TikTok, qui absorbe {pct(CN['part_mkt'][iC('TikTok Ads')], 0)} du budget pour {pct(CN['part_ca'][iC('TikTok Ads')], 0)} du CA.", "Le marketing est mal réparti :")
bullet(f" {pct(V['annulation'][iV('Douala')])} d'annulation à Douala, deux fois les autres villes ; les remises ne génèrent aucun volume supplémentaire.", "L'exécution et les remises détruisent de la valeur :")
doc.add_heading("Décisions demandées", 2)
bullet(" 8 Abidjan, 4 Dakar, 3 Cotonou, 3 Lomé, 2 Douala sous condition (annulation inférieure à 10 %).", "Valider la répartition des 20 stations :")
bullet(" geler les remises supérieures ou égales à 15 % et rééquilibrer le marketing dès le 1er trimestre 2027.", "Agir sur les fuites de rentabilité :")
bullet(" anti-remboursement, exécution à Douala, conversion du swap vers l'abonnement.", "Lancer trois chantiers :")
bullet(" capex et charges fixes d'une station avant d'engager l'investissement.", "Confirmer avec la Finance :")
page_break()

# ================================================================== 2. Contexte & méthode
doc.add_heading("2. Contexte, données et méthode", 1)
para("VoltRide Africa est une entreprise de mobilité électrique présente à Abidjan, Dakar, Douala, Cotonou et Lomé. Elle équipe les chauffeurs de moto-taxi, les livreurs, "
     "les particuliers et les PME en deux-roues électriques et propose un réseau d'échange de batteries (swap). Quatre lignes de service : swap batterie, location journalière, "
     "abonnement mensuel, accessoires et maintenance.")
para("Face à la hausse du prix du carburant, la direction a lancé en 2026 une phase d'expansion financée par des investisseurs à impact. Les actionnaires attendent des preuves de "
     "rentabilité. La direction constate un chiffre d'affaires irrégulier, des remboursements préoccupants, un marketing coûteux et de fortes disparités entre villes. "
     "Ce rapport éclaire la décision d'ouvrir 20 nouvelles stations au premier semestre 2027.")
doc.add_heading("Données", 2)
para("Six mois d'activité commerciale (1er mai - 31 octobre 2026), 6 390 lignes brutes issues de 40 stations. Le fichier contient volontairement des incohérences, des erreurs de saisie, "
     "des doublons et des valeurs aberrantes.")
journal = pd.read_csv(ROOT / "data" / "processed" / "journal_nettoyage.csv")
doc.add_heading("Qualité et nettoyage", 2)
para("L'audit montre que 78 % des lignes présentent au moins une incohérence, mais l'essentiel est de forme (formats de date, libellés). 13 % des lignes ont une anomalie de valeur "
     "(manquant, aberrant, doublon). Au final, 280 lignes sur 6 390 (4,4 %) sont retirées et le jeu propre compte 6 110 transactions et 1 098 clients.")
keep = ["Doublons exacts (ids normalisés)", "Dates dans un format non ISO", "Dates manquantes, impossibles ou hors période", "Statuts hétérogènes (casse, accents, anglais)",
        "Villes mal orthographiées (casse, espaces, fautes)", "Libellés de service hétérogènes", "Quantités nulles", "Prix multipliés par 10", "Prix multipliés par 100",
        "Remises négatives", "Remises > 100 %", "Coûts marketing manquants"]
rows = []
for _, r_ in journal[journal.regle.isin(keep)].iterrows():
    rows.append([r_.regle, num(r_.lignes_concernees), r_.traitement])
table(rows, ["Anomalie", "Lignes", "Traitement"], [6.4, 1.6, 8.6], size=8.5)
doc.add_heading("Définitions des indicateurs", 2)
bullet(" quantité × prix × (1 − remise), hors transactions annulées (elle inclut donc les ventes ensuite remboursées).", "Chiffre d'affaires :")
bullet(" marge brute − coût marketing ; le profit net réel retire en plus les ventes remboursées (le coût du service reste engagé).", "Profit net :")
bullet(" annulées / toutes les transactions ; remboursées / transactions non annulées.", "Taux d'annulation et de remboursement :")
bullet(" (CA − coût marketing) / coût marketing.", "ROI marketing :")
page_break()

# ================================================================== 3. Performance globale
doc.add_heading("3. Performance globale", 1)
para(f"VoltRide a facturé {Mf(K['ca_total'] / 1e6)} sur six mois pour {Mf(K['profit_net'] / 1e6)} de profit net estimé, soit 25{NB}% du CA. Les remboursements ({Mf(I['remb_total_M'])}) "
     f"ramènent le profit net réel à {Mf(K['profit_net_reel'] / 1e6)} : ils effacent un tiers du profit.")
fig("03_ca_profit_mensuel.png", 14.5, "Figure 1 - CA et profit net par mois")
para(f"Le CA a progressé de {pct(D['mois']['croissance_mai_oct'] * 100, 0)} entre mai et octobre. L'irrégularité perçue vient d'un creux en juillet (−3{NB}%) suivi d'un rebond de +11{NB}% en août "
     f"puis en octobre. Une transaction sur dix est annulée ({pct(K['taux_annulation'] * 100)}) et {pct(K['taux_remboursement'] * 100)} des ventes finalisées sont remboursées : "
     "l'exécution est un levier de profit aussi important que la croissance.")
page_break()

# ================================================================== 4. Services
doc.add_heading("4. Performance par ligne de service", 1)
fig("04_services.png", 16.6, "Figure 2 - CA, marge, profit réel, remboursement et répartition par service")
table([[n, num(S["ca"][i], 1), pct(S["marge_pct"][i] * 100, 0), num(S["profit_net"][i], 1), num(S["profit_reel"][i], 1), pct(S["remb"][i]), pct(S["part_mkt"][i], 0)]
       for i, n in enumerate(S["noms"])], ["Service", "CA (M)", "Marge", "Profit net (M)", "Profit réel (M)", "Remb.", "Part marketing"], [4.6, 1.7, 1.6, 2.3, 2.4, 1.8, 2.2], size=8.5)
bullet(f" {pct(S['part_ca'][0], 0)} du CA et {pct(S['part_profit'][0], 0)} du profit net ; ROI marketing de 45. À protéger et à développer.", "Abonnement mensuel :")
bullet(" meilleure marge unitaire (38 %) mais panier de 3 500 FCFA pour environ 1 100 FCFA de marketing par transaction. Le coût d'acquisition par transaction est quasiment identique pour tous "
       "les services : il écrase le swap.", "Swap batterie :")
bullet(f" marges d'environ 25{NB}% et plus de 13{NB}% de remboursements, qui effacent {pct(S['chute_profit'][iS('Location journalière')] * 100, 0)} et "
       f"{pct(S['chute_profit'][iS('Accessoires & maintenance')] * 100, 0)} du profit.", "Location journalière et accessoires :")
callout("Réponse à la question stratégique : quelle ligne prioriser ?",
        "Prioriser l'abonnement en y convertissant les clients swap ; optimiser en urgence la location et les accessoires (le levier est la qualité : batteries défectueuses, pannes, "
        "retards de livraison) ; ne plus acquérir de clients swap par des canaux chers.")
page_break()

# ================================================================== 5. Villes
doc.add_heading("5. Analyse géographique", 1)
fig("05_villes.png", 16.6, "Figure 3 - CA, profit net réel et taux d'annulation par ville")
table([[n, num(V["ca"][i], 1), num(V["profit_reel"][i], 1), pct(V["annulation"][i]), pct(V["remb"][i]), ("+" if V["croissance"][i] > 0 else "") + pct(V["croissance"][i], 0),
        f"{num(V['contrib_station'][i])} k", num(V["tx_station"][i], 1)] for i, n in enumerate(V["noms"])],
      ["Ville", "CA (M)", "Profit réel (M)", "Annulation", "Remb.", "Croissance*", "Contribution/station/mois", "Transactions/station/mois"], [2.2, 1.5, 2.0, 1.9, 1.5, 2.0, 2.9, 2.6], size=8)
para("* 3 derniers mois contre 3 premiers mois.", size=8.5, color=GRIS, italic=True)
bullet(f" {pct(V['part_ca'][0], 0)} du CA, stations deux fois plus productives que les autres ({V['contrib_station'][0]} k FCFA de contribution mensuelle contre 66 à 94 k) : la demande dépasse l'offre de stations.", "Abidjan :")
bullet(f" ville la plus saine (annulation {pct(V['annulation'][iV('Dakar')])}, remboursement {pct(V['remb'][iV('Dakar')])}) mais croissance faible (+2{NB}%).", "Dakar :")
bullet(f" croissance la plus forte (+{num(V['croissance'][iV('Cotonou')], 0)}{NB}%) mais productivité encore faible (15 transactions par station et par mois).", "Cotonou :")
bullet(f" {pct(V['annulation'][iV('Douala')])} d'annulation, soit le double des autres villes, chaque mois (12 à 17{NB}%), dans la quasi-totalité des stations (jusqu'à 19{NB}%) et surtout sur "
       "l'abonnement (15,8 %) et les accessoires (21,9 %). Un défaut persistant et généralisé est structurel : disponibilité des batteries, logistique ou process.", "Douala :")
fig("06_heatmaps_villes.png", 16.4, "Figure 4 - CA mensuel par ville et annulation par ville et par service")
page_break()
doc.add_heading("Répartition recommandée des 20 stations", 2)
table([["Abidjan", "8", "Stations 2x plus productives, +23 % de croissance, point mort le plus court (21 mois)"],
       ["Dakar", "4", "Ville la plus saine ; croissance faible : renforcement plutôt que pari"],
       ["Cotonou", "3", "Plus forte croissance mais faible productivité : ouverture par paliers"],
       ["Lomé", "3", "+19,5 % de croissance ; surveiller les remboursements"],
       ["Douala", "2 (conditionnelles)", "Corriger l'exécution d'abord : ouvrir si l'annulation passe sous 10 %"]],
      ["Ville", "Stations", "Justification"], [2.4, 3.2, 11.0], size=9)
para("Le score d'attractivité (contribution par station 35 %, croissance 30 %, exécution 20 %, qualité du profit 15 %) classe Abidjan nettement en tête et Douala en dernier. "
     "Cotonou passe devant Dakar au score uniquement grâce à sa croissance ; mais c'est la ville où une station neuve se rentabilise le moins. Elle est donc ouverte par paliers "
     "(3 stations) tandis que Dakar, plus productive et plus saine, est renforcée (4 stations).")
doc.add_heading("Point mort d'une nouvelle station", 2)
hyp = PM["hyp"]
para(f"Hypothèses à valider avec la Finance : investissement de {num(hyp['capex'] / 1e6, 1)}{NB}M{NB}FCFA, charges fixes de {num(hyp['fixes'] / 1e3)}{NB}k{NB}FCFA par mois, montée en charge de "
     f"{hyp['ramp']} mois à {num(hyp['taux0'] * 100, 0)}{NB}% de l'activité. La contribution de croisière est la moyenne observée des stations de la ville (marge brute moins marketing).")
fig("12_point_mort.png", 11.5, "Figure 5 - Cash cumulé d'une station neuve selon la ville")
para(f"Point mort cash : Abidjan {V['point_mort'][iV('Abidjan')]} mois, Dakar {V['point_mort'][iV('Dakar')]} mois, Douala {V['point_mort'][iV('Douala')]} mois ; Lomé et Cotonou au-delà de 72 mois au niveau de "
     f"productivité actuel. Un gain de +40{NB}% de contribution (fin des remises élevées, marketing rééquilibré) ramène une station moyenne de {PM['moyenne_base']} à {PM['moyenne_plus40']} mois. "
     "Ouvrir 20 stations à l'identique hors d'Abidjan ne crée donc pas de valeur à horizon raisonnable : la rentabilité dépend de la contribution par transaction, du mix en faveur de "
     "l'abonnement et du coût d'installation.")
page_break()

# ================================================================== 6. Marketing
doc.add_heading("6. Analyse marketing et acquisition", 1)
fig("07_canaux.png", 16.0, "Figure 6 - ROI, budget face au CA apporté et rétention par canal")
table([[n, num(CN["roi"][i], 1), pct(CN["part_mkt"][i], 1), pct(CN["part_ca"][i], 1), f"{num(CN['cout_tx'][i])} FCFA", pct(CN["retention"][i]), pct(CN["annulation"][i]), pct(CN["remb"][i])]
       for i, n in enumerate(CN["noms"])], ["Canal", "ROI", "Part du budget", "Part du CA", "Coût / transaction", "Rétention", "Annulation", "Remb."], [3.8, 1.2, 2.0, 1.8, 2.5, 1.9, 1.9, 1.5], size=8)
bullet(f" ROI de {num(CN['roi'][0], 1)}, {num(CN['cout_tx'][0])} FCFA par transaction, rétention de {pct(CN['retention'][0])} (la meilleure). Il apporte {pct(CN['part_ca'][0], 0)} du CA pour {pct(CN['part_mkt'][0], 1)} du budget.", "Parrainage :")
bullet(f" ROI de {num(CN['roi'][1], 1)} et {num(CN['roi'][2], 1)} : rentables et fidélisants.", "WhatsApp Business et partenariats VTC :")
t = iC("TikTok Ads")
bullet(f" {pct(CN['part_mkt'][t], 0)} du budget pour {pct(CN['part_ca'][t], 0)} du CA, ROI le plus bas ({num(CN['roi'][t], 1)}), annulation {pct(CN['annulation'][t])}, remboursement {pct(CN['remb'][t], 0)}, "
       f"rétention la plus faible ({pct(CN['retention'][t])}).", "TikTok Ads :")
sw = CN["swap_profit_k"]
bullet(f" avec un panier de 3 500 FCFA, acquérir un client swap via TikTok ou Meta fait perdre de l'argent (profit swap : {num(sw['TikTok Ads'])} k et {num(sw['Meta Ads'])} k FCFA), alors que "
       f"parrainage ({num(sw['Parrainage'])} k), WhatsApp ({num(sw['WhatsApp Business'])} k) et VTC ({num(sw['Partenariat chauffeurs VTC'])} k) dégagent un profit.", "Effet sur le swap :")
callout("Réponse à la question stratégique : quel canal mérite plus de budget ?",
        f"Plus de budget : parrainage (programme à renforcer), WhatsApp Business, partenariats VTC. À optimiser : TikTok et Meta (cibler abonnements et PME, plafonner le coût d'acquisition du swap). "
        f"Transférer 1{NB}M{NB}FCFA de TikTok vers les trois canaux performants représenterait environ +{num(I['gain_marketing_M'], 1)}{NB}M{NB}FCFA de CA (rendement marginal supposé à 50{NB}% du ROI moyen).")
page_break()

# ================================================================== 7. Clients
doc.add_heading("7. Analyse clients", 1)
para(f"{num(CL['total'])} clients au total ({num(CL['actifs'])} avec au moins une transaction non annulée). {pct(CL['recurrents'] * 100, 0)} sont récurrents (au moins 2 transactions) et "
     f"{pct(CL['retenus'] * 100, 0)} sont actifs sur au moins deux mois.")
fig("08_pareto_segments.png", 14.2, "Figure 7 - Courbe de Pareto et segmentation par fréquence")
bullet(f" {CL['n80']} clients ({pct(CL['pct80'] * 100, 0)}) font 80{NB}% du CA ; les 230 clients fidèles (6 transactions ou plus, 21{NB}% des clients) font {pct(CL['freq_part_ca'][2], 0)} du CA. "
       f"Le top 10 pèse {pct(CL['top10_part'] * 100, 1)} du CA (dont le n° 1 : 4,0{NB}M{NB}FCFA).", "Portefeuille concentré :")
bullet(f" {pct(CL['freq_part_clients'][0], 0)} des clients sont occasionnels et ne pèsent que {pct(CL['freq_part_ca'][0], 0)} du CA : l'enjeu est leur rétention, pas l'acquisition à tout prix.", "Rétention :")
doc.add_heading("Satisfaction et remboursement", 2)
fig("09_satisfaction.png", 11.5, "Figure 8 - Distribution des notes et taux de remboursement selon la note")
para(f"Note moyenne de {num(K['note_moyenne'], 2)}/5. Les transactions remboursées sont notées {num(CL['note_remb'], 2)} contre {num(CL['note_term'], 2)} pour les terminées. Aucune note supérieure ou égale à 4 "
     "n'est remboursée ; une note inférieure ou égale à 2 sur quatre l'est. La note est donc un signal d'alerte précoce : agir avant le remboursement (rappel, geste commercial, échange de batterie) "
     "coûte moins cher que rembourser. 38 % des transactions remboursées n'ont pas de note : le sondage doit être systématique et immédiat.")
doc.add_heading("Convertir le swap en abonnement", 2)
sc = CV["scenarios"]
para(f"{CV['clients_swap']} clients ont utilisé le swap ; {pct(CV['deja_abonnes_pct'] * 100, 0)} ont déjà un abonnement et {CV['swap_only']} sont « swap uniquement ». Un abonné rapporte environ "
     f"{num(round(CV['abo_marge_mois'], -2))} FCFA de marge par mois contre environ {num(round(CV['swap_marge_mois'], -2))} FCFA pour un client swap seul. Ces clients dépensent aujourd'hui peu en swap "
     "(environ 2 700 FCFA de CA par mois) alors que l'abonnement coûte 28 000 FCFA : un taux de conversion réaliste se situe entre 5 et 10 %.")
table([[pct(r["taux"] * 100, 0), str(r["clients"]), f"+{num(r['gain_M'], 2)}{NB}M{NB}FCFA"] for r in sc], ["Taux de conversion", "Clients convertis", "Gain de marge sur 6 mois"], [4.5, 4.5, 6.0], size=9)
para("Hypothèse : 3 mois d'abonnement en moyenne ; le gain est la marge d'abonnement moins la marge swap abandonnée. Actions : proposer l'abonnement dès le 5e swap, essai plafonné (pas de remise "
     "générale), cibler d'abord les 59 clients « swap uniquement » ayant fait au moins 8 swaps, relancer tout client sans transaction au deuxième mois.", size=9.5)
page_break()

# ================================================================== 8. Bonus
doc.add_heading("8. Segments clients et effet des remises", 1)
doc.add_heading("Quel segment est le plus rentable ?", 2)
fig("10_segments_clients.png", 15.2, "Figure 9 - Profit réel par transaction, remboursement et profit total par segment")
table([[n, f"{num(SG['panier'][i])} FCFA", pct(SG["part_ca"][i], 0), pct(SG["remb"][i]), f"{num(SG['profit_reel_tx'][i])} FCFA"] for i, n in enumerate(SG["noms"])],
      ["Segment", "Panier moyen", "Part du CA", "Remboursement", "Profit réel / transaction"], [4.4, 3.0, 2.4, 3.0, 3.8], size=9)
para("Les PME et flottes sont le segment le plus rentable (panier le plus élevé, annulation la plus basse, profit réel par transaction deux fois supérieur à celui des chauffeurs). Les chauffeurs "
     "moto-taxi font le volume (40 % du CA), grâce à l'abonnement. Les particuliers sont le segment le moins rentable (11,7 % de remboursement, swap déficitaire) : il faut traiter la qualité "
     "de service avant d'en acquérir davantage.")
doc.add_heading("Les promotions détruisent-elles de la valeur ?", 2)
fig("11_remises.png", 15.2, "Figure 10 - Quantité, marge par transaction et remboursement selon la remise")
para(f"Oui. La quantité moyenne par transaction est plate ({num(R['q'][0], 2)} sans remise, {num(R['q'][4], 2)} à 20{NB}%) : les remises ne font pas acheter plus. La marge par transaction passe de "
     f"{num(R['marge_par_tx'][0])} à {num(R['marge_par_tx'][4])} FCFA à 20{NB}% de remise, le remboursement monte à {pct(R['remb'][4])} et le profit réel devient négatif. "
     f"{pct(R['part_remisees'] * 100, 1)} des transactions sont remisées : {Mf(R['sacrifice_M'])} de CA sacrifié, soit {pct(R['sacrifice_pct_marge'] * 100, 1)} de la marge brute. "
     "Les remises sont accordées par habitude, pas par stratégie.")
page_break()

# ================================================================== 9. Recommandations
doc.add_heading("9. Cinq recommandations stratégiques", 1)
table([
    ["1", "Concentrer les ouvertures sur Abidjan et Dakar ; Douala sous condition (8 / 4 / 3 / 3 / 2)",
     "Abidjan : stations 2x plus productives, point mort de 21 mois. Douala : 15,5 % d'annulation, structurel.", "Évite de financer des stations non rentables"],
    ["2", "Rééquilibrer le marketing vers Parrainage, WhatsApp et VTC ; plafonner TikTok et Meta pour le swap",
     f"ROI {num(CN['roi'][0], 1)} contre {num(CN['roi'][t], 1)} ; TikTok = {pct(CN['part_mkt'][t], 0)} du budget pour {pct(CN['part_ca'][t], 0)} du CA.", f"≈ +{num(I['gain_marketing_M'], 1)} M FCFA de CA par M FCFA transféré"],
    ["3", "Faire de l'abonnement le cœur de l'offre : offre dès le 5e swap, essai plafonné, ciblage des 469 clients « swap seul »",
     f"Abonnement = {pct(S['part_profit'][0], 0)} du profit ; 9 600 contre 400 FCFA de marge par mois.", f"+{num(sc[0]['gain_M'], 1)} à {num(sc[1]['gain_M'], 1)} M FCFA de marge sur 6 mois"],
    ["4", "Plan « zéro remboursement » sur la location et les accessoires : contrôle qualité des batteries, délais de livraison, alerte sur toute note ≤ 2",
     f"≈ 14 % de remboursements ; {Mf(I['remb_loc_acc_M'])} rendus sur ces deux lignes.", f"≈ +{num(I['gain_remb_M'], 1)} M FCFA conservés si divisés par 2"],
    ["5", "Encadrer les remises (plus de remise ≥ 15 %, validation au-delà de 10 %) et cibler les PME et flottes",
     "Aucun effet volume ; marge divisée par 2,6 à 20 % ; PME = profit réel par transaction x2.", f"Jusqu'à {num(R['sacrifice_M'], 1)} M FCFA de CA préservé"],
], ["#", "Recommandation", "Pourquoi", "Impact (6 mois)"], [0.7, 6.4, 5.4, 4.1], size=8.5)
para("Les gains sont des ordres de grandeur issus de scénarios sur six mois ; ils ne se cumulent pas intégralement.", size=9, italic=True, color=GRIS)

# ================================================================== 10. Plan d'action
doc.add_heading("10. Conclusion et plan d'action", 1)
para("Le diagnostic en une phrase : VoltRide gagne de l'argent grâce à l'abonnement mensuel et à Abidjan, mais en perd une partie par les remboursements, les remises et un marketing mal réparti. "
     "Ouvrir 20 stations sans corriger ces trois fuites reviendrait à dupliquer le modèle actuel, défauts compris.")
doc.add_heading("Feuille de route", 2)
table([["Immédiat", "Gel des remises ≥ 15 % ; validation au-delà de 10 % ; lancement de la vague 1 (Abidjan, Dakar)", "Direction commerciale"],
       ["T1 2027", "Réallocation du budget marketing ; programme de conversion swap vers abonnement ; plan anti-remboursement", "Marketing, Opérations"],
       ["T1 2027", "Plan d'exécution Douala (disponibilité des batteries, logistique) ; confirmation du capex et des charges fixes", "Opérations, Finance"],
       ["T2 2027", "Ouverture par paliers à Cotonou et Lomé ; décision sur les 2 stations de Douala si annulation < 10 %", "Direction générale"]],
      ["Échéance", "Action", "Responsable"], [2.4, 10.4, 3.8], size=9)
doc.add_heading("Indicateurs de pilotage", 2)
table([["Taux de remboursement", pct(K["taux_remboursement"] * 100), "< 5 %"], ["Taux d'annulation à Douala", pct(V["annulation"][iV("Douala")]), "< 10 %"],
       ["Remises ≥ 15 % (part des transactions)", pct(R["part_ge15"] * 100), "0 %"], ["ROI marketing global", num(I["roi_global"], 1), "> 18"],
       ["Abonnés parmi les clients swap", pct(CV["deja_abonnes_pct"] * 100, 0), "> 55 %"], ["Rétention (actifs sur au moins 2 mois)", pct(CL["retenus"] * 100, 0), "> 72 %"]],
      ["Indicateur", "Aujourd'hui", "Cible T2 2027"], [8.6, 4.0, 4.0], size=9)
doc.add_heading("Limites de l'analyse", 2)
bullet(" pas de saisonnalité annuelle ; croissances par ville calculées sur trois mois contre trois mois.", "Six mois de données :")
bullet(" coût marketing alloué par transaction (ROI par canal approximatif) ; environ 6 % des lignes corrigées statistiquement ; investissement et charges fixes d'une station en hypothèses.", "Méthode :")
bullet(" les données de ce cas sont fictives. Les indicateurs ci-dessus sont suivis dans le tableau de bord Streamlit.", "Données :")

out = REP / "VoltRide_Rapport_Strategique.docx"
doc.save(out)
print("OK :", out)

# ------------------------------------------------------------------ PDF via Word (mise à jour du sommaire incluse)
pdf = out.with_suffix(".pdf")
ps = f"""
$w = New-Object -ComObject Word.Application; $w.Visible = $false
try {{
  $d = $w.Documents.Open('{out}', $false, $false)
  $d.TablesOfContents.Item(1).Update()
  $d.Repaginate()
  $d.TablesOfContents.Item(1).Update()
  $d.Save()
  $d.ExportAsFixedFormat('{pdf}', 17)
  "pages=" + $d.ComputeStatistics(2)
  $d.Close($false)
}} finally {{ $w.Quit() }}
"""
try:
    res = subprocess.run(["pwsh", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=240)
    print(res.stdout.strip() or res.stderr.strip()[:300])
except Exception as e:  # noqa: BLE001
    print("PDF non généré (Word indisponible) :", e)
