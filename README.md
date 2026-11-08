<p align="center"><img src="docs/logo_voltride_clair.png" alt="VoltRide Motors" width="160"></p>

# VoltRide Africa — Analyse stratégique

Analyse de 6 mois d'activité (mai - octobre 2026) pour éclairer l'ouverture de **20 nouvelles stations au S1 2027**.
Énoncé : `docs/enonce_projet.docx`.

## Livrables

| Livrable | Fichier |
|---|---|
| **Présentation PowerPoint pour la direction** (17 diapositives, notes de présentation) | `reports/VoltRide_Presentation_Direction.pptx` |
| **Rapport complet PDF** (12 pages, sommaire, page de garde) | `reports/VoltRide_Rapport_Strategique.pdf` (source Word : `.docx`) |
| Résumé exécutif (5 pages) | `reports/resume_executif.pdf` (source Word : `.docx`) |
| Dashboard interactif Streamlit | `app/streamlit_app.py` — publication : [DEPLOIEMENT_STREAMLIT.md](DEPLOIEMENT_STREAMLIT.md) |
| Notebook structuré et commenté | `notebooks/01_analyse_voltride_africa.ipynb` (HTML : `reports/analyse_voltride_africa.html`) |
| 5 recommandations stratégiques | `docs/recommandations_strategiques.md` |
| Audit des données | `docs/audit_qualite.md` |
| Dataset propre `df_clean` | `data/processed/df_clean.csv` |

## Charte graphique (extraite du logo)

| Élément | Valeur |
|---|---|
| Noir anthracite | `#1B2A30` |
| Vert VoltRide (aplats, pastilles) | `#10EC27` |
| Vert profond (texte et graphiques sur fond blanc) | `#0A8F1E` |
| Gris ardoise / gris clair | `#5B6770` / `#EEF2F3` |
| Alerte / attention | `#D93025` / `#F59E0B` |
| Police | Calibri |

Logos : `docs/logo_voltride_clair.png` (fond clair), `docs/logo_voltride_sombre.png` (fond sombre).
Le thème Streamlit est défini dans `.streamlit/config.toml`.

## Structure

```
PROJET VOLTRIDE/
├── data/raw/ · data/processed/            # brut (intact) · df_clean.csv, journal_nettoyage.csv
├── src/voltride/                          # cleaning.py · features.py · analysis.py
├── notebooks/01_analyse_voltride_africa.ipynb
├── app/streamlit_app.py
├── .streamlit/config.toml                 # thème Streamlit
├── scripts/                               # run_cleaning.py · build_notebook.py · export_deck_data.py
│                                          # build_deck.js · build_report.py · build_summary.py
├── reports/                               # PPTX, PDF, DOCX, HTML, figures/, deck_data.json
├── docs/                                  # énoncé, logos, audit, recommandations
├── requirements.txt                       # dépendances du dashboard (déploiement)
└── requirements-dev.txt                   # chaîne complète (notebook, rapports)
```

## Reproduire

```bash
pip install -r requirements-dev.txt
python scripts/run_cleaning.py         # nettoyage + variables -> data/processed/
python scripts/build_notebook.py       # exécute le notebook, écrit les figures et l'audit
python scripts/build_summary.py        # résumé exécutif (.docx)
python scripts/export_deck_data.py     # chiffres du PowerPoint et du rapport -> reports/deck_data.json
python scripts/build_report.py         # rapport (.docx, + PDF si Microsoft Word est installé)
cd scripts && npm install && cd ..     # une seule fois : installe pptxgenjs
node scripts/build_deck.js             # présentation PowerPoint
streamlit run app/streamlit_app.py     # dashboard
```

## Définitions clés
* **CA** = quantité × prix × (1 − remise), hors transactions annulées (définition de l'énoncé ; inclut les ventes ensuite remboursées).
* **Profit net** = marge brute − coût marketing ; **profit net réel** = après retrait des ventes remboursées.
* **Taux d'annulation** = annulées / toutes ; **taux de remboursement** = remboursées / non annulées.
* **ROI marketing** = (CA − coût marketing) / coût marketing.

## Résultat en une phrase
VoltRide gagne de l'argent grâce à l'abonnement mensuel et à Abidjan, mais en perd une partie par les remboursements, les remises et un marketing mal réparti :
ouvrir 8 stations à Abidjan, 4 à Dakar, 3 à Cotonou, 3 à Lomé et 2 à Douala **sous condition** de correction de l'exécution.

> Les fichiers d'origine (CSV, énoncé, logo) sont aussi présents à la racine du dossier ; les copies de travail sont dans `data/raw/` et `docs/`.
