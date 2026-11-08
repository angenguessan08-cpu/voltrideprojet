/* Génère reports/VoltRide_Presentation_Direction.pptx
 *
 * Prérequis : npm install pptxgenjs   (dans ce dossier)  puis  python scripts/export_deck_data.py
 * Usage     : node scripts/build_deck.js
 * Charte    : couleurs extraites du logo (anthracite #1B2A30, vert #10EC27), police Calibri.
 */
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const ROOT = path.resolve(__dirname, "..");
const { applyTheme } = require(process.env.PPTX_SKILL_APPLY_THEME || path.join(__dirname, "apply_theme.js"));

const D = JSON.parse(fs.readFileSync(path.join(ROOT, "reports", "deck_data.json"), "utf8"));
const LOGO_CLAIR = path.join(ROOT, "docs", "logo_voltride_clair.png");
const LOGO_SOMBRE = path.join(ROOT, "docs", "logo_voltride_sombre.png");

// ------------------------------------------------------------------ charte
const NOIR = "1B2A30", VERT = "10EC27", VERT_P = "0A8F1E", GRIS = "5B6770", GRIS_C = "EEF2F3", ROUGE = "D93025", ORANGE = "F59E0B", BLEU = "3B82F6";
const THEME = {
  name: "VoltRide Motors", headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: { dk1: NOIR, lt1: "FFFFFF", dk2: "26373F", lt2: GRIS_C, accent1: VERT, accent2: VERT_P, accent3: BLEU, accent4: ORANGE, accent5: ROUGE, accent6: "8A96A0", hlink: VERT_P, folHlink: "8A96A0" },
};

// ------------------------------------------------------------------ formats
const NB = " "; // espace insécable : un chiffre ne se sépare jamais de son unité
const num = (x, dec = 0) => {
  const s = Math.abs(x).toFixed(dec).replace(".", ",");
  const [i, f] = s.split(",");
  const g = i.replace(/\B(?=(\d{3})+(?!\d))/g, NB);
  return (x < 0 ? "−" : "") + g + (f ? "," + f : "");
};
const pct = (x, dec = 1) => num(x, dec) + NB + "%";
const M = (x, dec = 1) => num(x, dec) + NB + "M";
const nb = (s) => s.replace(/ (%|M|k|FCFA|mois|stations)/g, NB + "$1");

// ------------------------------------------------------------------ deck
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "VoltRide Africa - Analyse stratégique";
pres.author = "Direction Data & Analyse";
pres.company = "VoltRide Motors";
const C = pres.SchemeColor;
const W = 13.33, LM = 0.6, CW = W - 2 * LM;

pres.defineSlideMaster({
  title: "COVER", background: { color: NOIR },
  objects: [
    { image: { path: LOGO_SOMBRE, x: 7.6, y: 1.05, w: 5.2, h: 5.21 } },
    { placeholder: { options: { name: "title", type: "title", x: LM, y: 2.35, w: 6.8, h: 1.9, fontSize: 40, bold: true, color: "FFFFFF", align: "left", valign: "top", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: LM, y: 4.45, w: 6.8, h: 1.0, fontSize: 20, color: "C9D3D8", align: "left", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  objects: [
    { image: { path: LOGO_CLAIR, x: W - LM - 0.5, y: 6.88, w: 0.5, h: 0.5 } },
    { text: { text: "VoltRide Africa · Analyse stratégique · Novembre 2026", options: { x: LM, y: 7.0, w: 7, h: 0.3, fontSize: 10, color: GRIS, margin: 0, isTextBox: true } } },
    { placeholder: { options: { name: "title", type: "title", x: LM, y: 0.38, w: CW, h: 1.05, fontSize: 28, bold: true, color: NOIR, align: "left", valign: "top", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: W - LM - 1.2, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: GRIS, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSING", background: { color: NOIR },
  objects: [
    { image: { path: LOGO_SOMBRE, x: 4.67, y: 0.7, w: 4.0, h: 4.01 } },
    { placeholder: { options: { name: "title", type: "title", x: LM, y: 4.9, w: CW, h: 0.9, fontSize: 38, bold: true, color: "FFFFFF", align: "center", valign: "top", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: LM, y: 5.8, w: CW, h: 0.6, fontSize: 18, color: "C9D3D8", align: "center", valign: "top", margin: 0 }, text: "" } },
  ],
});

// ------------------------------------------------------------------ helpers (options toujours neufs : pptxgenjs les modifie en place)
const txt = (s, o) => Object.assign({ isTextBox: true, margin: 0, fontFace: "Calibri", color: NOIR, fontSize: 14, valign: "top" }, o);
function card(slide, x, y, w, h, name, fill = GRIS_C) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.08, objectName: name });
}
function stat(slide, x, y, w, h, value, label, o = {}) {
  card(slide, x, y, w, h, "Carte " + label.slice(0, 20), o.fill || GRIS_C);
  slide.addText(value, txt("", { x: x + 0.25, y: y + 0.16, w: w - 0.5, h: h * 0.5, fontSize: o.size || 36, bold: true, color: o.color || NOIR, valign: "middle", objectName: "Valeur " + label.slice(0, 20) }));
  slide.addText(label, txt("", { x: x + 0.25, y: y + h * 0.58, w: w - 0.5, h: h * 0.36, fontSize: 14, color: o.labelColor || GRIS, objectName: "Libellé " + label.slice(0, 20) }));
}
function point(slide, x, y, w, lead, body, o = {}) {
  slide.addText([{ text: lead, options: { bold: true, color: o.leadColor || NOIR, fontSize: o.leadSize || 16, breakLine: true } },
                 { text: body, options: { color: GRIS, fontSize: 14 } }],
                txt("", { x, y, w, h: o.h || 1.2, paraSpaceAfter: 3, objectName: "Point " + lead.slice(0, 20) }));
}
function chartBase(extra) {
  return Object.assign({
    showTitle: false, showLegend: false, legendPos: "b", legendFontSize: 12, legendColor: NOIR, legendFontFace: "+mn-lt",
    catAxisLabelFontSize: 12, catAxisLabelColor: NOIR, catAxisLabelFontFace: "+mn-lt",
    valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showValue: true, dataLabelFontSize: 12, dataLabelColor: NOIR, dataLabelFontFace: "+mn-lt", dataLabelPosition: "outEnd",
  }, extra);
}
let slideIndex = 0;
function content(section, title, notes) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(nb(title), { placeholder: "title" });
  s.addNotes(notes);
  slideIndex += 1;
  return s;
}

const K = D.kpi, S = D.services, V = D.villes, CN = D.canaux, CL = D.clients, R = D.remises, SG = D.segments, CV = D.conversion, I = D.impacts;
const idxS = (n) => S.noms.indexOf(n), idxV = (n) => V.noms.indexOf(n), idxC = (n) => CN.noms.indexOf(n);
const profitPerdu = 1 - K.profit_net_reel / K.profit_net;

// =================================================================== 1. Couverture
pres.addSection({ title: "Introduction" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "Introduction" });
  s.addText("Ouvrir 20 stations sans reproduire nos fuites de rentabilité", { placeholder: "title" });
  s.addText("Analyse stratégique VoltRide Africa · Comité de direction · Novembre 2026", { placeholder: "body" });
  s.addNotes("Ouverture : l'analyse porte sur 6 mois d'activité (mai à octobre 2026) dans 5 villes. Objectif de la séance : décider où et comment ouvrir les 20 stations du S1 2027.");
}

// =================================================================== 2. Réponse en bref
{
  const s = content("Introduction", "La réponse en bref : ouvrir, mais d'abord colmater trois fuites de rentabilité",
    "Message clé : l'expansion est justifiée à Abidjan et Dakar, mais trois fuites (remboursements, remises, marketing mal réparti) réduisent la rentabilité. À corriger en parallèle des ouvertures.");
  const y = 1.75;
  stat(s, LM, y, 3.8, 1.9, pct(S.part_profit[idxS("Abonnement mensuel")], 0), "du profit net vient de l'abonnement mensuel", { color: VERT_P, size: 44 });
  stat(s, LM + 4.15, y, 3.8, 1.9, M(I.remb_total_M) + NB + "FCFA", "remboursés : un tiers du profit net estimé", { color: ROUGE, size: 40 });
  stat(s, LM + 8.3, y, 3.8, 1.9, pct(V.annulation[idxV("Douala")]), "d'annulation à Douala, deux fois les autres villes", { color: ROUGE, size: 44 });
  card(s, LM, 3.95, CW, 2.7, "Bandeau décision", NOIR);
  s.addText("Notre recommandation", txt("", { x: LM + 0.4, y: 4.15, w: 5, h: 0.4, fontSize: 14, bold: true, color: VERT }));
  s.addText([
    { text: "Vague 1 (T1 2027) : 18 stations", options: { bold: true, breakLine: true } },
    { text: "8 Abidjan · 4 Dakar · 3 Cotonou · 3 Lomé", options: { breakLine: true } },
    { text: "Vague 2 : 2 stations à Douala, après correction de l'exécution", options: { bold: true, breakLine: true } },
    { text: "En parallèle : réallouer le marketing, geler les remises ≥ 15 %, convertir le swap en abonnement, réduire les remboursements.", options: {} },
  ], txt("", { x: LM + 0.4, y: 4.6, w: CW - 0.8, h: 1.95, fontSize: 18, color: "FFFFFF", paraSpaceAfter: 6 }));
}

// =================================================================== 3. Performance globale
pres.addSection({ title: "Diagnostic" });
{
  const s = content("Diagnostic", `Un CA en hausse de ${num(D.mois.croissance_mai_oct * 100, 0)} % en six mois, mais un tiers du profit s'évapore en remboursements`,
    "Le CA passe de 14,8 M en mai à 18,4 M en octobre, avec un creux en juillet. Le profit net estimé de 24,2 M tombe à 15,8 M une fois les remboursements déduits.");
  const w = 2.85, g = (CW - 4 * w) / 3;
  const cards = [
    [M(K.ca_total / 1e6) + NB + "FCFA", "Chiffre d'affaires (hors annulées)", NOIR],
    [M(K.profit_net / 1e6) + NB + "FCFA", "Profit net estimé", NOIR],
    [M(K.profit_net_reel / 1e6) + NB + "FCFA", "Profit net réel, après remboursements", VERT_P],
    [pct(K.taux_annulation * 100) + " / " + pct(K.taux_remboursement * 100), "Annulation / remboursement", ROUGE],
  ];
  cards.forEach((c, i) => stat(s, LM + i * (w + g), 1.65, w, 1.35, c[0], c[1], { size: i === 3 ? 26 : 28, color: c[2] }));
  s.addChart(pres.charts.BAR, [
    { name: "CA (M FCFA)", labels: D.mois.labels, values: D.mois.ca },
    { name: "Profit net (M FCFA)", labels: D.mois.labels, values: D.mois.profit },
  ], chartBase({ x: LM, y: 3.2, w: CW, h: 3.6, barDir: "col", barGrouping: "clustered", barGapWidthPct: 60, chartColors: [NOIR, VERT], showLegend: true, dataLabelFormatCode: "0.0" }));
}

// =================================================================== 4. Services
{
  const s = content("Diagnostic", "L'abonnement fait 75 % du profit ; le swap consomme la moitié du marketing pour 1,6 % du profit",
    "Lecture : pour chaque service, trois barres. Le swap pèse 49 % des transactions et 49 % du budget marketing mais 1,6 % du profit : le panier est de 3 500 FCFA pour environ 1 100 FCFA de marketing par transaction.");
  s.addChart(pres.charts.BAR, [
    { name: "Part du CA", labels: S.noms, values: S.part_ca },
    { name: "Part du marketing", labels: S.noms, values: S.part_mkt },
    { name: "Part du profit net", labels: S.noms, values: S.part_profit },
  ], chartBase({ x: LM, y: 1.65, w: 7.7, h: 5.0, barDir: "col", barGrouping: "clustered", barGapWidthPct: 45, chartColors: [GRIS, ORANGE, VERT_P], showLegend: true, dataLabelFormatCode: '0"%"', dataLabelFontSize: 11, catAxisLabelFontSize: 11 }));
  const x = 8.75, w = CW - (x - LM);
  point(s, x, 1.8, w, "Abonnement : le moteur", `${pct(S.part_ca[0], 0)} du CA, ${pct(S.part_profit[0], 0)} du profit, marge de ${pct(S.marge_pct[0] * 100, 0)}.`, { leadColor: VERT_P });
  point(s, x, 3.2, w, "Swap : porte d'entrée, pas centre de profit", `${pct(S.part_tx[idxS("Swap batterie")], 0)} des transactions, ${pct(S.part_mkt[idxS("Swap batterie")], 0)} du marketing, ${pct(S.part_profit[idxS("Swap batterie")])} du profit.`, { leadColor: ROUGE, h: 1.5 });
  point(s, x, 5.0, w, "À faire", "Prioriser l'abonnement, assainir la location, repenser l'acquisition du swap.", { h: 1.4 });
}

// =================================================================== 5. Remboursements
{
  const s = content("Diagnostic", "Les remboursements effacent 79 % du profit de la location et 71 % de celui des accessoires",
    "Le taux de remboursement atteint environ 14 % sur la location journalière et les accessoires (batteries défectueuses, pannes, retards de livraison). Cela représente 4,3 M FCFA rendus sur ces deux lignes.");
  s.addChart(pres.charts.BAR, [
    { name: "Profit net estimé (M FCFA)", labels: S.noms, values: S.profit_net },
    { name: "Profit net réel, après remboursements (M FCFA)", labels: S.noms, values: S.profit_reel },
  ], chartBase({ x: LM, y: 1.65, w: 7.7, h: 5.0, barDir: "col", barGrouping: "clustered", barGapWidthPct: 45, chartColors: [GRIS, VERT_P], showLegend: true, dataLabelFormatCode: "0.0", dataLabelFontSize: 11, catAxisLabelFontSize: 11 }));
  const x = 8.75, w = CW - (x - LM);
  const il = idxS("Location journalière"), ia = idxS("Accessoires & maintenance");
  stat(s, x, 1.75, w, 1.5, "−" + pct(S.chute_profit[il] * 100, 0), "de profit sur la location journalière", { color: ROUGE, size: 40 });
  stat(s, x, 3.45, w, 1.5, "−" + pct(S.chute_profit[ia] * 100, 0), "de profit sur les accessoires", { color: ROUGE, size: 40 });
  point(s, x, 5.2, w, "Le levier est la qualité", `Remboursement : ${pct(S.remb[il], 0)} (location), ${pct(S.remb[ia], 0)} (accessoires), contre ${pct(S.remb[idxS("Swap batterie")], 1)} pour le swap.`, { h: 1.5 });
}

// =================================================================== 6. Villes / Douala
{
  const s = content("Diagnostic", "Douala annule une commande sur six : un défaut structurel à corriger avant d'y investir",
    "Douala est à 12-17 % d'annulation chaque mois, dans presque toutes les stations et sur tous les services : ce n'est pas un accident local mais un problème de disponibilité ou de logistique.");
  s.addChart(pres.charts.BAR, [{ name: "Taux d'annulation (%)", labels: V.noms, values: V.annulation }],
    chartBase({ x: LM, y: 1.65, w: 6.2, h: 5.0, barDir: "col", barGapWidthPct: 50, chartColors: V.noms.map((n) => (n === "Douala" ? ROUGE : NOIR)), dataLabelFormatCode: '0.0"%"', dataLabelFontSize: 14, catAxisLabelFontSize: 13 }));
  const rows = [[{ text: "Ville", options: { bold: true, color: "FFFFFF", fill: { color: NOIR } } }, { text: "CA (M)", options: { bold: true, color: "FFFFFF", fill: { color: NOIR }, align: "right" } },
                 { text: "Croissance*", options: { bold: true, color: "FFFFFF", fill: { color: NOIR }, align: "right" } }, { text: "Remb.", options: { bold: true, color: "FFFFFF", fill: { color: NOIR }, align: "right" } }]];
  V.noms.forEach((n, i) => rows.push([{ text: n, options: { bold: true } }, { text: num(V.ca[i], 1), options: { align: "right" } },
    { text: (V.croissance[i] > 0 ? "+" : "") + pct(V.croissance[i], 0), options: { align: "right", color: V.croissance[i] > 10 ? VERT_P : (V.croissance[i] < 0 ? ROUGE : NOIR) } },
    { text: pct(V.remb[i], 1), options: { align: "right" } }]));
  s.addTable(rows, { x: 7.1, y: 1.9, w: CW - 6.5, colW: [1.6, 1.2, 1.5, 1.2], fontSize: 14, fontFace: "Calibri", color: NOIR, rowH: 0.52, border: { type: "solid", pt: 0.75, color: "D5DDE0" }, valign: "middle" });
  s.addText("* 3 derniers mois contre 3 premiers mois", txt("", { x: 7.1, y: 5.3, w: 5.4, h: 0.3, fontSize: 11, color: GRIS }));
}

// =================================================================== 7. Où ouvrir
pres.addSection({ title: "Expansion" });
{
  const s = content("Expansion", "Où ouvrir les 20 stations : Abidjan en priorité, Douala sous condition",
    "Répartition 8-4-3-3-2. Abidjan : stations deux fois plus productives. Dakar : la plus saine. Cotonou : forte croissance mais faible productivité donc ouverture par paliers. Douala : seulement si l'annulation passe sous 10 %.");
  const alloc = [
    ["Abidjan", 8, `Stations 2x plus productives (${V.contrib_station[idxV("Abidjan")]}${NB}k${NB}FCFA/mois). +${num(V.croissance[idxV("Abidjan")], 0)}${NB}% de croissance.`],
    ["Dakar", 4, `Ville la plus saine : annulation ${pct(V.annulation[idxV("Dakar")])}, remboursement ${pct(V.remb[idxV("Dakar")])}.`],
    ["Cotonou", 3, `+${num(V.croissance[idxV("Cotonou")], 0)}${NB}% de croissance mais faible productivité : ouvrir par paliers.`],
    ["Lomé", 3, `+${num(V.croissance[idxV("Lomé")], 0)}${NB}% de croissance. Surveiller les remboursements (${pct(V.remb[idxV("Lomé")])}).`],
    ["Douala", 2, `Sous condition : ${pct(V.annulation[idxV("Douala")])} d'annulation, à corriger avant d'ouvrir.`],
  ];
  const w = 2.25, g = (CW - 5 * w) / 4;
  alloc.forEach((a, i) => {
    const x = LM + i * (w + g), cond = a[0] === "Douala";
    if (cond) s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.7, w, h: 3.75, fill: { color: "FFFFFF" }, line: { color: ROUGE, width: 1.5, dashType: "dash" }, rectRadius: 0.08, objectName: "Carte Douala" });
    else card(s, x, 1.7, w, 3.75, "Carte " + a[0]);
    s.addText(a[0], txt("", { x: x + 0.2, y: 1.85, w: w - 0.4, h: 0.4, fontSize: 18, bold: true }));
    s.addText(String(a[1]), txt("", { x: x + 0.2, y: 2.3, w: w - 0.4, h: 1.0, fontSize: 56, bold: true, color: cond ? ROUGE : VERT_P, valign: "middle" }));
    s.addText("stations", txt("", { x: x + 0.2, y: 3.3, w: w - 0.4, h: 0.3, fontSize: 14, bold: true, color: GRIS }));
    s.addText(a[2], txt("", { x: x + 0.2, y: 3.75, w: w - 0.4, h: 1.6, fontSize: 14, color: NOIR }));
  });
  card(s, LM, 5.7, CW, 1.0, "Bandeau vagues", NOIR);
  s.addText(nb("Vague 1 (T1 2027) : 18 stations   ·   Vague 2 : 2 stations à Douala si l'annulation passe sous 10 %"), txt("", { x: LM + 0.4, y: 5.7, w: CW - 0.8, h: 1.0, fontSize: 18, bold: true, color: "FFFFFF", valign: "middle" }));
}

// =================================================================== 8. Point mort
{
  const hyp = D.point_mort.hyp;
  const s = content("Expansion", "Un point mort sous deux ans à Abidjan seulement : ailleurs, la productivité doit d'abord progresser",
    "Le point mort cash est le mois où le cash cumulé, après l'investissement initial, redevient positif. Hypothèses à valider avec la Finance. Lomé et Cotonou n'atteignent pas le point mort en 72 mois au niveau actuel.");
  const labels = V.noms.map((n, i) => (V.point_mort[i] === null ? n + " (> 72)" : n));
  const vals = V.point_mort.map((m) => (m === null ? 72 : m));
  s.addChart(pres.charts.BAR, [{ name: "Mois avant point mort cash", labels, values: vals }],
    chartBase({ x: LM, y: 1.65, w: 7.3, h: 5.0, barDir: "col", barGapWidthPct: 50, chartColors: V.point_mort.map((m) => (m !== null && m <= 24 ? VERT_P : (m === null ? ROUGE : GRIS))), dataLabelFormatCode: '0" mois"', dataLabelFontSize: 13, catAxisLabelFontSize: 12 }));
  const x = 8.2, w = CW - (x - LM);
  card(s, x, 1.75, w, 2.55, "Carte hypothèses");
  s.addText([{ text: "Hypothèses (à valider avec la Finance)", options: { bold: true, breakLine: true, fontSize: 16 } },
             { text: `Investissement : ${num(hyp.capex / 1e6, 1)}${NB}M${NB}FCFA`, options: { bullet: true, breakLine: true } },
             { text: `Charges fixes : ${num(hyp.fixes / 1e3, 0)}${NB}k${NB}FCFA par mois`, options: { bullet: true, breakLine: true } },
             { text: `Montée en charge : ${hyp.ramp} mois à ${num(hyp.taux0 * 100, 0)}${NB}%`, options: { bullet: true, breakLine: true } },
             { text: "Contribution : moyenne observée des stations de la ville", options: { bullet: true } }],
    txt("", { x: x + 0.25, y: 1.9, w: w - 0.5, h: 2.3, fontSize: 14, paraSpaceAfter: 4 }));
  stat(s, x, 4.5, w, 2.15, `${D.point_mort.moyenne_base} → ${D.point_mort.moyenne_plus40} mois`, "point mort d'une station moyenne avec +40 % de contribution (fin des remises élevées, marketing rééquilibré)", { size: 34, color: VERT_P, fill: GRIS_C });
}

// =================================================================== 9. Marketing
pres.addSection({ title: "Leviers de rentabilité" });
{
  const t = idxC("TikTok Ads"), p = idxC("Parrainage");
  const s = content("Leviers de rentabilité", "Chaque franc investi en parrainage rapporte près de cinq fois plus qu'en TikTok",
    "ROI = (CA - coût marketing) / coût marketing. Parrainage 35,9 contre 7,4 pour TikTok, qui absorbe 30 % du budget pour 18 % du CA. Pour le swap (panier de 3 500 FCFA), acquérir via TikTok ou Meta fait perdre de l'argent.");
  s.addChart(pres.charts.BAR, [{ name: "ROI marketing", labels: CN.noms, values: CN.roi }],
    chartBase({ x: LM, y: 1.65, w: 7.0, h: 5.0, barDir: "bar", catAxisOrientation: "maxMin", barGapWidthPct: 40, chartColors: CN.roi.map((r) => (r >= 15 ? VERT_P : (r >= 9 ? ORANGE : ROUGE))), dataLabelFormatCode: "0.0", dataLabelFontSize: 13, catAxisLabelFontSize: 12 }));
  const x = 7.9, w = CW - (x - LM);
  point(s, x, 1.8, w, "Parrainage : le meilleur canal", `ROI ${num(CN.roi[p], 1)}, ${num(CN.cout_tx[p], 0)}${NB}FCFA par transaction, rétention ${pct(CN.retention[p])}.`, { leadColor: VERT_P, h: 1.3 });
  point(s, x, 3.3, w, "TikTok : le canal à corriger", `${pct(CN.part_mkt[t], 0)} du budget pour ${pct(CN.part_ca[t], 0)} du CA. Annulation ${pct(CN.annulation[t])}, remboursement ${pct(CN.remb[t], 0)}.`, { leadColor: ROUGE, h: 1.5 });
  point(s, x, 5.1, w, "Impact estimé", `Transférer 1${NB}M${NB}FCFA de TikTok vers Parrainage, WhatsApp et VTC : environ +${num(I.gain_marketing_M, 1)}${NB}M${NB}FCFA de CA.`, { h: 1.5 });
}

// =================================================================== 10. Clients
{
  const s = content("Leviers de rentabilité", `${pct(CL.pct80 * 100, 0)} des clients font 80 % du CA : la rétention des occasionnels est l'enjeu`,
    "318 clients sur 1 072 génèrent 80 % du CA. Les 230 clients fidèles (6 transactions ou plus) pèsent 68 % du CA. Le numéro 1 représente 4 M FCFA, le top 10 environ 17 % : surveiller la dépendance.");
  const w = 4.0;
  stat(s, LM, 1.7, w, 1.5, `${CL.n80} clients`, "font 80 % du chiffre d'affaires", { size: 34, color: VERT_P });
  stat(s, LM, 3.4, w, 1.5, pct(CL.freq_part_ca[2], 0), `du CA vient des ${num(Math.round(CL.actifs * CL.freq_part_clients[2] / 100), 0)} clients fidèles`, { size: 34, color: VERT_P });
  stat(s, LM, 5.1, w, 1.5, pct(CL.retenus * 100, 0), "des clients actifs sur au moins 2 mois", { size: 34 });
  s.addChart(pres.charts.BAR, [
    { name: "% des clients", labels: CL.freq_noms, values: CL.freq_part_clients },
    { name: "% du CA", labels: CL.freq_noms, values: CL.freq_part_ca },
  ], chartBase({ x: 5.0, y: 1.65, w: W - 5.0 - LM, h: 5.0, barDir: "col", barGrouping: "clustered", barGapWidthPct: 50, chartColors: [GRIS, VERT_P], showLegend: true, dataLabelFormatCode: '0"%"', dataLabelFontSize: 13 }));
}

// =================================================================== 11. Swap -> abonnement
{
  const sc = CV.scenarios;
  const s = content("Leviers de rentabilité", `Convertir le swap en abonnement : +${num(sc[0].gain_M, 1)} à ${num(sc[1].gain_M, 1)} M FCFA de marge sans coût d'acquisition`,
    "469 clients swap uniquement. Un abonné rapporte environ 9 600 FCFA de marge par mois contre 400 pour un client swap seul. Hypothèse : 3 mois d'abonnement en moyenne. Taux réaliste 5 à 10 %.");
  const w = 3.85, g = (CW - 3 * w) / 2;
  const steps = [
    ["1", "Repérer", `${CV.swap_only} clients « swap uniquement » sur ${CV.clients_swap} clients swap (${num(CV.deja_abonnes_pct * 100, 0)}${NB}% sont déjà abonnés).`],
    ["2", "Proposer", "Dès le 5e swap : comparer ce que le client a payé avec le prix de l'abonnement. Essai plafonné, pas de remise générale."],
    ["3", "Retenir", "Relancer tout client sans transaction au 2e mois. Alerte immédiate sur toute note ≤ 2."],
  ];
  steps.forEach((st, i) => {
    const x = LM + i * (w + g);
    card(s, x, 1.7, w, 2.55, "Étape " + st[1]);
    s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: 1.9, w: 0.55, h: 0.55, fill: { color: VERT }, line: { color: VERT, width: 0 }, objectName: "Pastille " + st[0] });
    s.addText(st[0], txt("", { x: x + 0.25, y: 1.9, w: 0.55, h: 0.55, fontSize: 18, bold: true, align: "center", valign: "middle" }));
    s.addText(st[1], txt("", { x: x + 0.95, y: 1.9, w: w - 1.2, h: 0.55, fontSize: 20, bold: true, valign: "middle" }));
    s.addText(nb(st[2]), txt("", { x: x + 0.25, y: 2.65, w: w - 0.5, h: 1.5, fontSize: 14 }));
  });
  const head = (t, al) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: NOIR }, align: al || "left" } });
  const rows = [[head("Taux de conversion"), head("Clients convertis", "right"), head("Gain de marge sur 6 mois", "right")]];
  sc.forEach((r) => rows.push([{ text: pct(r.taux * 100, 0), options: { bold: true } }, { text: String(r.clients), options: { align: "right" } }, { text: "+" + num(r.gain_M, 2) + NB + "M" + NB + "FCFA", options: { align: "right", bold: true, color: VERT_P } }]));
  s.addTable(rows, { x: LM, y: 4.55, w: 7.4, colW: [2.4, 2.2, 2.8], fontSize: 14, fontFace: "Calibri", color: NOIR, rowH: 0.5, border: { type: "solid", pt: 0.75, color: "D5DDE0" }, valign: "middle" });
  s.addText(nb(`Marge mensuelle : abonné ≈ ${num(Math.round(CV.abo_marge_mois / 100) * 100, 0)} FCFA, client swap seul ≈ ${num(Math.round(CV.swap_marge_mois / 100) * 100, 0)} FCFA. Hypothèse : 3 mois d'abonnement en moyenne.`),
    txt("", { x: 8.4, y: 4.6, w: CW - 7.8, h: 1.8, fontSize: 14, color: GRIS }));
}

// =================================================================== 12. Remises
{
  const s = content("Leviers de rentabilité", "Les remises ne font pas acheter plus : elles divisent la marge par transaction par 2,6",
    "La quantité moyenne par transaction est plate (2,42 sans remise, 2,48 à 20 %). Un tiers des transactions est remisé. À 20 %, le remboursement monte à 12,5 % et le profit réel devient négatif.");
  s.addChart(pres.charts.BAR, [{ name: "Marge brute par transaction (FCFA)", labels: R.tranches.map((t) => "Remise " + t), values: R.marge_par_tx }],
    chartBase({ x: LM, y: 1.65, w: 7.4, h: 5.0, barDir: "col", barGapWidthPct: 45, chartColors: [VERT_P, GRIS, GRIS, GRIS, ROUGE], dataLabelFormatCode: "#,##0", dataLabelFontSize: 13 }));
  const x = 8.4, w = CW - (x - LM);
  stat(s, x, 1.75, w, 1.5, `${num(R.q[0], 2)} → ${num(R.q[4], 2)}`, "quantité moyenne : aucun effet volume", { size: 32 });
  stat(s, x, 3.45, w, 1.5, M(R.sacrifice_M) + NB + "FCFA", `de CA sacrifié, soit ${pct(R.sacrifice_pct_marge * 100, 1)} de la marge brute`, { size: 32, color: ROUGE });
  stat(s, x, 5.15, w, 1.5, pct(R.remb[4]), "de remboursement à 20 % de remise (7 % sans)", { size: 32, color: ROUGE });
}

// =================================================================== 13. Segments
{
  const s = content("Leviers de rentabilité", "Les PME et flottes sont le segment le plus rentable, les particuliers le moins rentable",
    "Profit réel par transaction : PME 5 064 FCFA, moto-taxis 2 762, livreurs 1 678, particuliers 1 441. Les particuliers cumulent un taux de remboursement de 11,7 % et un swap déficitaire.");
  s.addChart(pres.charts.BAR, [{ name: "Profit net réel par transaction (FCFA)", labels: SG.noms, values: SG.profit_reel_tx }],
    chartBase({ x: LM, y: 1.65, w: 7.4, h: 5.0, barDir: "col", barGapWidthPct: 50, chartColors: [VERT_P, NOIR, GRIS, ROUGE], dataLabelFormatCode: "#,##0", dataLabelFontSize: 13, catAxisLabelFontSize: 12 }));
  const x = 8.4, w = CW - (x - LM);
  point(s, x, 1.8, w, "PME / flottes", `Panier ${num(SG.panier[0], 0)}${NB}FCFA, profit réel par transaction 2x celui des moto-taxis. Cibler les contrats flotte.`, { leadColor: VERT_P, h: 1.5 });
  point(s, x, 3.5, w, "Chauffeurs moto-taxi", `${pct(SG.part_ca[1], 0)} du CA : le volume, sécurisé par l'abonnement.`, { h: 1.2 });
  point(s, x, 4.9, w, "Particuliers", `Remboursement ${pct(SG.remb[3])}. Traiter la qualité de service avant d'en acquérir davantage.`, { leadColor: ROUGE, h: 1.5 });
}

// =================================================================== 14. Recommandations
pres.addSection({ title: "Décisions" });
{
  const s = content("Décisions", "Cinq recommandations pour sécuriser l'expansion",
    "Les gains sont des ordres de grandeur sur 6 mois et ne se cumulent pas intégralement. Chaque recommandation est détaillée dans le rapport.");
  const recs = [
    ["Concentrer les ouvertures sur Abidjan et Dakar ; Douala sous condition", "Évite de financer des stations non rentables"],
    ["Rééquilibrer le marketing vers Parrainage, WhatsApp et VTC ; plafonner TikTok et Meta pour le swap", `≈ +${num(I.gain_marketing_M, 1)} M FCFA de CA par M FCFA transféré`],
    ["Faire de l'abonnement le cœur de l'offre : convertir les clients swap", `+${num(CV.scenarios[0].gain_M, 1)} à ${num(CV.scenarios[1].gain_M, 1)} M FCFA de marge sur 6 mois`],
    ["Plan « zéro remboursement » sur la location et les accessoires", `≈ +${num(I.gain_remb_M, 1)} M FCFA conservés si divisés par 2`],
    ["Encadrer les remises (plus de ≥ 15 %) et cibler les PME et flottes", `Jusqu'à ${num(R.sacrifice_M, 1)} M FCFA de CA préservé`],
  ];
  const h = 0.92, gap = 0.12;
  recs.forEach((r, i) => {
    const y = 1.6 + i * (h + gap);
    card(s, LM, y, CW, h, "Recommandation " + (i + 1));
    s.addShape(pres.shapes.OVAL, { x: LM + 0.25, y: y + 0.18, w: 0.56, h: 0.56, fill: { color: VERT }, line: { color: VERT, width: 0 }, objectName: "Pastille reco " + (i + 1) });
    s.addText(String(i + 1), txt("", { x: LM + 0.25, y: y + 0.18, w: 0.56, h: 0.56, fontSize: 18, bold: true, align: "center", valign: "middle" }));
    s.addText(nb(r[0]), txt("", { x: LM + 1.05, y, w: 7.4, h, fontSize: 16, bold: true, valign: "middle" }));
    s.addText(nb(r[1]), txt("", { x: LM + 8.7, y, w: CW - 8.95, h, fontSize: 14, color: VERT_P, bold: true, valign: "middle" }));
  });
}

// =================================================================== 15. Décisions & KPI
{
  const s = content("Décisions", "Décisions demandées aujourd'hui et indicateurs de suivi",
    "Quatre décisions. Les KPI sont suivis mensuellement dans le dashboard Streamlit. La Finance doit confirmer investissement et charges fixes d'une station avant tout engagement.");
  const decisions = [
    ["Valider la répartition des 20 stations", "8 Abidjan · 4 Dakar · 3 Cotonou · 3 Lomé · 2 Douala sous condition"],
    ["Geler les remises ≥ 15 % et rééquilibrer le marketing", "Dès le 1er trimestre 2027"],
    ["Lancer trois chantiers", "Anti-remboursement, exécution Douala, conversion swap vers abonnement"],
    ["Confirmer avec la Finance", "Investissement et charges fixes d'une station"],
  ];
  decisions.forEach((d, i) => {
    const y = 1.7 + i * 1.28;
    s.addShape(pres.shapes.OVAL, { x: LM, y: y + 0.05, w: 0.5, h: 0.5, fill: { color: NOIR }, line: { color: NOIR, width: 0 }, objectName: "Pastille décision " + (i + 1) });
    s.addText(String(i + 1), txt("", { x: LM, y: y + 0.05, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle" }));
    s.addText([{ text: d[0], options: { bold: true, fontSize: 16, breakLine: true } }, { text: nb(d[1]), options: { fontSize: 14, color: GRIS } }], txt("", { x: LM + 0.75, y, w: 5.6, h: 1.15 }));
  });
  const head = (t, al) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: NOIR }, align: al || "left" } });
  const kp = [
    ["Taux de remboursement", pct(K.taux_remboursement * 100), "< 5 %"],
    ["Annulation à Douala", pct(V.annulation[idxV("Douala")]), "< 10 %"],
    ["Remises ≥ 15 % (part des transactions)", pct(R.part_ge15 * 100), "0 %"],
    ["ROI marketing global", num(I.roi_global, 1), "> 18"],
    ["Abonnés parmi les clients swap", pct(CV.deja_abonnes_pct * 100, 0), "> 55 %"],
    ["Rétention (actifs ≥ 2 mois)", pct(CL.retenus * 100, 0), "> 72 %"],
  ];
  const rows = [[head("Indicateur"), head("Aujourd'hui", "right"), head("Cible T2 2027", "right")]];
  kp.forEach((r) => rows.push([{ text: r[0], options: { bold: true } }, { text: r[1], options: { align: "right" } }, { text: r[2], options: { align: "right", bold: true, color: VERT_P } }]));
  s.addTable(rows, { x: 6.9, y: 1.75, w: CW - 6.3, colW: [3.1, 1.3, 1.4], fontSize: 14, fontFace: "Calibri", color: NOIR, rowH: 0.62, border: { type: "solid", pt: 0.75, color: "D5DDE0" }, valign: "middle" });
}

// =================================================================== 16. Clôture
{
  const s = pres.addSlide({ masterName: "CLOSING", sectionTitle: "Décisions" });
  s.addText("Merci · Questions", { placeholder: "title" });
  s.addText("Drive the future.", { placeholder: "body" });
  s.addNotes("Ouvrir la discussion sur les quatre décisions demandées. Rapport complet, notebook et dashboard disponibles pour le détail.");
}

// =================================================================== 17. Annexe
{
  const s = content("Décisions", "Annexe : définitions, hypothèses et limites de l'analyse",
    "Annexe de référence pour répondre aux questions de méthode.");
  const colW = (CW - 0.5) / 2;
  card(s, LM, 1.65, colW, 3.9, "Carte définitions");
  s.addText([{ text: "Définitions", options: { bold: true, fontSize: 16, breakLine: true } },
    { text: "CA = quantité × prix × (1 − remise), hors transactions annulées", options: { bullet: true, breakLine: true } },
    { text: "Profit net = marge brute − coût marketing", options: { bullet: true, breakLine: true } },
    { text: "Profit net réel = après retrait des ventes remboursées", options: { bullet: true, breakLine: true } },
    { text: "Annulation = annulées / toutes les transactions", options: { bullet: true, breakLine: true } },
    { text: "Remboursement = remboursées / non annulées", options: { bullet: true, breakLine: true } },
    { text: "ROI marketing = (CA − coût marketing) / coût marketing", options: { bullet: true } }],
    txt("", { x: LM + 0.3, y: 1.85, w: colW - 0.6, h: 3.5, fontSize: 14, paraSpaceAfter: 6 }));
  card(s, LM + colW + 0.5, 1.65, colW, 3.9, "Carte limites");
  s.addText([{ text: "Hypothèses et limites", options: { bold: true, fontSize: 16, breakLine: true } },
    { text: "6 mois de données : pas de saisonnalité annuelle", options: { bullet: true, breakLine: true } },
    { text: "Coût marketing alloué par transaction : ROI par canal approximatif", options: { bullet: true, breakLine: true } },
    { text: "4,4 % des lignes supprimées, environ 6 % corrigées statistiquement (prix, coûts)", options: { bullet: true, breakLine: true } },
    { text: "Point mort : investissement et charges fixes non issus des données", options: { bullet: true, breakLine: true } },
    { text: "Gains annoncés : ordres de grandeur sur 6 mois, non cumulables en totalité", options: { bullet: true, breakLine: true } },
    { text: "Données fictives à visée pédagogique", options: { bullet: true } }],
    txt("", { x: LM + colW + 0.8, y: 1.85, w: colW - 0.6, h: 3.5, fontSize: 14, paraSpaceAfter: 6 }));
}

// ------------------------------------------------------------------ écriture
const out = path.join(ROOT, "reports", "VoltRide_Presentation_Direction.pptx");
(async () => {
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("OK :", out);
})();
