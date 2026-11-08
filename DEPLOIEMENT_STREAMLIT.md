# Publier le dashboard sur Streamlit Community Cloud

Le dashboard (`app/streamlit_app.py`) est prêt à être publié : `requirements.txt` à la racine contient uniquement les 4 dépendances d'exécution
(streamlit, pandas, numpy, plotly). Il a été testé dans un environnement Python vierge avec ce seul fichier.

## Fichiers nécessaires dans le dépôt GitHub

| Fichier / dossier | Rôle |
|---|---|
| `requirements.txt` | Dépendances installées automatiquement par Streamlit Cloud |
| `app/streamlit_app.py` | Point d'entrée du dashboard |
| `src/voltride/` | Fonctions d'analyse importées par l'app (`analysis.py`) |
| `data/processed/df_clean.csv` | Données nettoyées lues par l'app |
| `docs/logo_voltride_clair.png` | Logo affiché dans la barre latérale et l'onglet du navigateur |
| `.streamlit/config.toml` | Thème aux couleurs VoltRide (noir anthracite, vert) |

Le reste du projet (notebook, rapports, scripts) peut rester dans le dépôt sans gêner : seul `requirements.txt` est lu pour installer l'app.
`requirements-dev.txt` sert uniquement à régénérer le notebook, le rapport et le résumé en local.

## Étapes

1. **Créer un dépôt GitHub** et y envoyer le dossier du projet (le `.gitignore` fourni exclut les fichiers inutiles) :
   ```bash
   git init
   git add .
   git commit -m "Dashboard VoltRide Africa"
   git branch -M main
   git remote add origin https://github.com/<votre-compte>/voltride-dashboard.git
   git push -u origin main
   ```
2. Aller sur **https://share.streamlit.io**, se connecter avec GitHub, cliquer sur **Create app**.
3. Renseigner :
   * **Repository** : `<votre-compte>/voltride-dashboard`
   * **Branch** : `main`
   * **Main file path** : `app/streamlit_app.py`
   * **Advanced settings > Python version** : 3.12 ou 3.13
4. Cliquer sur **Deploy**. La première installation prend 1 à 3 minutes ; l'URL publique est du type `https://<nom>.streamlit.app`.

## Points d'attention

* **Données** : le fichier `df_clean.csv` est fictif (cas pédagogique). Pour des données réelles, utilisez un dépôt **privé** (Streamlit Cloud sait les déployer)
  et, si besoin, `st.secrets` plutôt qu'un fichier dans le dépôt.
* **Mise à jour des données** : relancez `python scripts/run_cleaning.py`, committez le nouveau `data/processed/df_clean.csv` et poussez : l'app se met à jour seule.
* **Accès restreint** : dans Streamlit Cloud, *Settings > Sharing* permet de limiter l'accès à des adresses e-mail précises.
* **Test local avant publication** :
  ```bash
  pip install -r requirements.txt
  streamlit run app/streamlit_app.py
  ```
