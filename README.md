# VoltRide Africa — Analyse stratégique avant l'ouverture de 20 stations

![VoltRide Motors](docs/logo_voltride_clair.png)

Projet de Data Analyst : audit, nettoyage et analyse de 6 mois d'activité commerciale (mai - octobre 2026) de **VoltRide Africa**, entreprise de mobilité électrique (deux-roues électriques et stations d'échange de batteries) présente à Abidjan, Dakar, Douala, Cotonou et Lomé.
L'objectif est d'éclairer le comité de direction avant l'ouverture de **20 nouvelles stations au premier semestre 2027**.

> Les données de ce cas sont fictives et créées à des fins pédagogiques. L'énoncé complet est dans `docs/enonce_projet.docx`.

---

## Sommaire

1. [Résultat en bref](#1-résultat-en-bref)
2. [Livrables](#2-livrables)
3. [Les données](#3-les-données)
4. [Méthode](#4-méthode)
5. [Principaux résultats](#5-principaux-résultats)
6. [Les 5 recommandations](#6-les-5-recommandations)
7. [Structure du projet](#7-structure-du-projet)
8. [Installation et utilisation](#8-installation-et-utilisation)
9. [Dashboard Streamlit](#9-dashboard-streamlit)
10. [Charte graphique](#10-charte-graphique)
11. [Définitions des indicateurs](#11-définitions-des-indicateurs)
12. [Hypothèses et limites](#12-hypothèses-et-limites)

---

## 1. Résultat en bref

VoltRide gagne de l'argent grâce à **l'abonnement mensuel** et à **Abidjan**, mais en perd une partie par **les remboursements, les remises et un marketing mal réparti**. Ouvrir 20 stations sans corriger ces fuites reviendrait à reproduire le modèle actuel, défauts compris.

**Recommandation :** ouvrir 18 stations en vague 1 (T1 2027) : **8 Abidjan, 4 Dakar, 3 Cotonou, 3 Lomé**, et subordonner **2 stations à Douala** à la correction de son taux d'annulation (objectif : moins de 10 %).

| Indicateur (6 mois) | Valeur |
|---|---|
| Chiffre d'affaires (hors annulées) | 95,3 M FCFA |
| Marge brute | 30,9 M FCFA (32,4 % du CA) |
| Profit net estimé | 24,2 M FCFA |
| Profit net réel (après remboursements) | 15,8 M FCFA |
| Taux d'annulation / de remboursement | 9,8 % / 7,4 % |
| Panier moyen | 17 287 FCFA |
| Transactions / clients (après nettoyage) | 6 110 / 1 098 |

---

## 2. Livrables

| Livrable | Fichier |
|---|---|
| Présentation PowerPoint pour la direction (17 diapositives, notes de présentation) | `reports/VoltRide_Presentation_Direction.pptx` |
| Rapport complet PDF (12 pages, sommaire, page de garde) | `reports/VoltRide_Rapport_Strategique.pdf` (source : `.docx`) |
| Résumé exécutif (5 pages) | `reports/resume_executif.pdf` (source : `.docx`) |
| Dashboard interactif Streamlit | `app/streamlit_app.py` |
| Notebook structuré et commenté | `notebooks/01_analyse_voltride_africa.ipynb` (version HTML : `reports/analyse_voltride_africa.html`) |
| 5 recommandations stratégiques | `docs/recommandations_strategiques.md` |
| Résumé d'audit des données | `docs/audit_qualite.md` |
| Dataset propre `df_clean` | `data/processed/df_clean.csv` |
| Journal des corrections appliquées | `data/processed/journal_nettoyage.csv` |
| Guide de publication Streamlit | `DEPLOIEMENT_STREAMLIT.md` |

---

## 3. Les données

Fichier source : `data/raw/voltride_dataset_senior.csv` — **6 390 lignes × 18 colonnes**, issues de 40 stations. Il contient volontairement des incohérences, des erreurs de saisie, des doublons et des valeurs aberrantes.

| Colonne | Description |
|---|---|
| `id_transaction`, `id_client` | Identifiants |
| `date_transaction` | Date (6 formats différents dans le fichier brut) |
| `ville`, `pays`, `station` | Localisation (code station du type `ST-ABI-03`) |
| `type_service` | Swap batterie, Location journalière, Abonnement mensuel, Accessoires & maintenance |
| `type_client` | Chauffeur moto-taxi, Livreur, Particulier, PME / flotte |
| `canal_acquisition` | Parrainage, WhatsApp Business, Partenariat VTC, Affichage, Meta Ads, TikTok Ads |
| `type_batterie` | Standard 48V, Longue autonomie 60V (sans objet pour les accessoires) |
| `quantite`, `prix_unitaire_fcfa`, `remise_pct` | Volume, prix catalogue, remise commerciale |
| `cout_unitaire_fcfa`, `cout_marketing_fcfa` | Coût de revient par unité, coût marketing alloué à la transaction |
| `mode_paiement`, `statut`, `note_client` | Paiement, Terminée / Annulée / Remboursée, satisfaction de 1 à 5 |

**Qualité constatée :** 78 % des lignes présentent au moins une incohérence (essentiellement de forme : dates, libellés) et 13 % une anomalie de valeur (manquant, aberrant, doublon). Après nettoyage, **280 lignes sur 6 390 (4,4 %)** sont retirées.

---

## 4. Méthode

Le projet suit le déroulé demandé par l'énoncé.

1. **Audit** : structure, types, valeurs manquantes, doublons, valeurs aberrantes, problèmes de qualité (`docs/audit_qualite.md`).
2. **Nettoyage** (`src/voltride/cleaning.py`) : chaque règle est codée une fois, journalisée et rejouable.
   * dates : lecture des 6 formats, suppression des dates impossibles ;
   * villes, services, canaux, paiements, statuts : normalisation (casse, accents, fautes, anglais) ; pays reconstitué depuis la ville, ville manquante reconstituée depuis le code station ;
   * prix : correction des valeurs multipliées par 10 ou 100 (comparaison à la médiane du service), valeurs négatives ou nulles traitées ;
   * remises négatives ou supérieures à 100 % mises à 0 % ; quantités nulles ou irréalistes supprimées ;
   * coûts manquants ou aberrants remplacés par la médiane du service ou du canal ;
   * doublons supprimés, y compris ceux masqués par une différence de casse sur l'identifiant client.
3. **Variables créées** (`src/voltride/features.py`) : `chiffre_affaires`, `marge_brute`, `profit_net`, `ca_net`, `profit_net_reel`, `mois`, `indicateur_remboursement`, `nombre_transactions_par_client`, `valeur_vie_client` (CLV simplifiée).
4. **Analyses** (`src/voltride/analysis.py`) : performance globale, services, villes, marketing (ROI, rétention), clients (Pareto 80/20, segmentation, satisfaction).
5. **Bonus senior** : rentabilité par segment client, effet des remises, point mort d'une nouvelle station, scénario de conversion swap vers abonnement.

Le notebook contient des contrôles automatiques (le nettoyage échoue si une règle n'est pas respectée) et un recalcul indépendant du chiffre d'affaires.

---

## 5. Principaux résultats

* **L'abonnement mensuel est le moteur** : 57 % du CA et 75 % du profit net, 35 % de marge.
* **Le swap est une porte d'entrée, pas un centre de profit** : 49 % des transactions et 49 % du budget marketing pour 1,6 % du profit (panier de 3 500 FCFA pour environ 1 100 FCFA de marketing par transaction).
* **Les remboursements coûtent cher** : environ 14 % sur la location et les accessoires ; ils effacent 79 % et 71 % de leur profit. Au total, 8,4 M FCFA remboursés, soit un tiers du profit net estimé.
* **Le marketing est mal réparti** : le parrainage a un ROI de 35,9 (441 FCFA par transaction, rétention de 72,6 %) contre 7,4 pour TikTok, qui absorbe 30 % du budget pour 18 % du CA. Acquérir un client swap via TikTok ou Meta fait perdre de l'argent.
* **Douala a un défaut d'exécution structurel** : 15,5 % d'annulation (le double des autres villes), chaque mois et dans presque toutes les stations.
* **Abidjan est la ville la plus attractive** : 37 % du CA, stations deux fois plus productives, point mort cash d'une station neuve estimé à 21 mois.
* **Les remises ne font pas acheter plus** : la quantité moyenne par transaction est plate (2,42 sans remise, 2,48 à 20 %), alors que la marge par transaction est divisée par 2,6. Coût : 3,3 M FCFA de CA sacrifié, soit 10,8 % de la marge brute.
* **Portefeuille concentré** : 30 % des clients (318) font 80 % du CA ; les clients fidèles pèsent 68 % du CA.
* **Les PME et flottes sont le segment le plus rentable** (profit réel par transaction deux fois supérieur à celui des moto-taxis) ; les particuliers, le moins (11,7 % de remboursement).
* **Satisfaction** : les transactions remboursées sont notées 1,87/5 contre 3,93 pour les terminées. Une note inférieure ou égale à 2 est un signal d'alerte avant le remboursement.

Répartition recommandée des 20 stations :

| Ville | Stations | Justification |
|---|---|---|
| Abidjan | 8 | Stations 2x plus productives, +23 % de croissance, point mort le plus court |
| Dakar | 4 | Ville la plus saine (annulation 8,2 %, remboursement 6,2 %) |
| Cotonou | 3 | Plus forte croissance (+38 %) mais faible productivité : ouverture par paliers |
| Lomé | 3 | +19,5 % de croissance, remboursements à surveiller |
| Douala | 2 (conditionnelles) | Corriger l'exécution d'abord : ouvrir si l'annulation passe sous 10 % |

---

## 6. Les 5 recommandations

1. **Concentrer les ouvertures sur Abidjan et Dakar ; Douala sous condition.** Évite de financer des stations non rentables.
2. **Rééquilibrer le marketing vers Parrainage, WhatsApp et partenariats VTC ; plafonner TikTok et Meta pour le swap.** Environ +4,5 M FCFA de CA par million FCFA transféré (hypothèse prudente de rendement marginal).
3. **Faire de l'abonnement le cœur de l'offre** : proposition dès le 5e swap, essai plafonné, ciblage des 469 clients « swap uniquement ». Entre +0,6 et +1,3 M FCFA de marge sur 6 mois pour 5 à 10 % de conversion.
4. **Plan « zéro remboursement » sur la location et les accessoires** : contrôle qualité des batteries, délais de livraison, alerte sur toute note inférieure ou égale à 2. Environ +2,2 M FCFA conservés si les remboursements sont divisés par deux.
5. **Encadrer les remises et cibler les PME et flottes** : plus de remise supérieure ou égale à 15 %, validation au-delà de 10 %. Jusqu'à 3,3 M FCFA de CA préservé.

Les gains sont des ordres de grandeur sur 6 mois et ne se cumulent pas intégralement. Détail dans `docs/recommandations_strategiques.md`.

---

## 7. Structure du projet

```
PROJET VOLTRIDE/
├── data/
│   ├── raw/voltride_dataset_senior.csv      # données brutes (jamais modifiées)
│   └── processed/                           # df_clean.csv, journal_nettoyage.csv
├── src/voltride/
│   ├── cleaning.py                          # règles de nettoyage journalisées
│   ├── features.py                          # CA, marge, profit, CLV...
│   └── analysis.py                          # KPI, tableaux, Pareto, point mort, palette
├── notebooks/
│   └── 01_analyse_voltride_africa.ipynb     # analyse complète, commentée
├── app/
│   └── streamlit_app.py                     # dashboard interactif
├── .streamlit/config.toml                   # thème Streamlit aux couleurs VoltRide
├── scripts/
│   ├── run_cleaning.py                      # brut -> df_clean
│   ├── build_notebook.py                    # génère et exécute le notebook
│   ├── build_summary.py                     # résumé exécutif (.docx)
│   ├── export_deck_data.py                  # chiffres du PowerPoint et du rapport
│   ├── build_report.py                      # rapport complet (.docx + PDF)
│   ├── build_deck.js                        # présentation PowerPoint
│   ├── apply_theme.js, package.json         # dépendances de la génération du deck
├── reports/                                 # PPTX, PDF, DOCX, HTML, figures/, deck_data.json
├── docs/                                    # énoncé, logos, audit, recommandations
├── requirements.txt                         # dépendances du dashboard (déploiement)
├── requirements-dev.txt                     # chaîne complète (notebook, rapports)
├── DEPLOIEMENT_STREAMLIT.md                 # guide de publication
└── README.md
```

Les fichiers d'origine (CSV, énoncé, logo) sont aussi présents à la racine du dossier ; les copies de travail sont dans `data/raw/` et `docs/`.

---

## 8. Installation et utilisation

**Prérequis :** Python 3.12 ou supérieur. Node.js uniquement pour régénérer le PowerPoint. Microsoft Word uniquement pour exporter le rapport en PDF automatiquement.

### Lancer uniquement le dashboard

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

### Régénérer toute la chaîne

```bash
pip install -r requirements-dev.txt

python scripts/run_cleaning.py         # nettoyage et variables -> data/processed/
python scripts/build_notebook.py       # exécute le notebook, écrit figures et audit
python scripts/build_summary.py        # résumé exécutif (.docx)
python scripts/export_deck_data.py     # chiffres du PowerPoint et du rapport -> reports/deck_data.json
python scripts/build_report.py         # rapport (.docx, et PDF si Word est installé)

cd scripts && npm install && cd ..     # une seule fois : installe pptxgenjs
node scripts/build_deck.js             # présentation PowerPoint
```

Tous les chiffres des livrables proviennent de `df_clean` : aucun chiffre n'est saisi à la main dans le PowerPoint ni dans le rapport.

---

## 9. Dashboard Streamlit

Filtres dans la barre latérale : **période, ville, service, canal d'acquisition, type de client**.

| Onglet | Contenu |
|---|---|
| Performance | KPI, CA / profit net / annulation par mois, CA par mode de paiement |
| Services | CA, marge et profit réel par service, remboursement, évolution mensuelle |
| Villes | CA, profit réel, annulation, heatmaps ville × mois et ville × service |
| Marketing | ROI par canal, budget face au CA, rétention |
| Clients | Pareto 80/20, segmentation par fréquence, top 10, note et remboursement |
| Nouvelle station | Simulateur de point mort (investissement, charges fixes, montée en charge, gain visé) |

**Publication sur Streamlit Community Cloud :** voir [DEPLOIEMENT_STREAMLIT.md](DEPLOIEMENT_STREAMLIT.md). Fichier principal : `app/streamlit_app.py` ; dépendances : `requirements.txt` (streamlit, pandas, numpy, plotly).

---

## 10. Charte graphique

Les couleurs sont extraites du logo VoltRide Motors.

| Élément | Valeur |
|---|---|
| Noir anthracite | `#1B2A30` |
| Vert VoltRide (aplats, pastilles) | `#10EC27` |
| Vert profond (texte et graphiques sur fond blanc) | `#0A8F1E` |
| Gris ardoise / gris clair | `#5B6770` / `#EEF2F3` |
| Alerte / attention | `#D93025` / `#F59E0B` |
| Police | Calibri |

Logos : `docs/logo_voltride_clair.png` (fond clair) et `docs/logo_voltride_sombre.png` (fond sombre). Le thème Streamlit est défini dans `.streamlit/config.toml`.

---

## 11. Définitions des indicateurs

* **Chiffre d'affaires (CA)** = quantité × prix unitaire × (1 − remise), pour les transactions non annulées (définition de l'énoncé). Il inclut donc les ventes ensuite remboursées.
* **CA net** = CA hors transactions remboursées.
* **Marge brute** = CA − quantité × coût unitaire.
* **Profit net** = marge brute − coût marketing. Une transaction annulée n'a ni CA ni coût de service, mais son coût marketing est dépensé.
* **Profit net réel** = profit après retrait des ventes remboursées (le CA remboursé est rendu au client, le coût du service reste engagé).
* **Taux d'annulation** = transactions annulées / toutes les transactions.
* **Taux de remboursement** = transactions remboursées / transactions non annulées.
* **ROI marketing** = (CA − coût marketing) / coût marketing ; le ROI sur marge, plus exigeant, sert de contre-test dans le notebook.
* **Client récurrent** = au moins 2 transactions non annulées ; **client retenu** = actif sur au moins 2 mois.
* **Valeur vie client (CLV simplifiée)** = profit net cumulé du client sur la période.

---

## 12. Hypothèses et limites

* **Six mois de données seulement** : pas de saisonnalité annuelle ; les croissances par ville comparent les 3 derniers mois aux 3 premiers.
* **Coût marketing alloué par transaction** (et non par campagne) : le ROI par canal est une approximation.
* **Corrections statistiques** : environ 6 % des lignes ont des prix ou des coûts corrigés par la médiane ou un facteur 10 / 100 ; l'impact sur les totaux est faible mais non nul. Les remises invalides sont mises à 0 % faute de pouvoir les vérifier.
* **Point mort d'une station** : investissement de 2,5 M FCFA, charges fixes de 45 k FCFA par mois et montée en charge de 3 mois à 50 % sont des **hypothèses**, non issues des données. Elles sont modifiables dans le dashboard et doivent être confirmées avec la Finance avant tout engagement.
* **Scénarios de gains** (marketing, conversion, remboursements, remises) : ordres de grandeur sur 6 mois, non cumulables en totalité.
* **Données fictives** à visée pédagogique.
