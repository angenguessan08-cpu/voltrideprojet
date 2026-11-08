# Audit qualité des données — VoltRide Africa

Fichier brut : 6 390 lignes x 18 colonnes (1er mai - 31 oct. 2026).

| Thème | Colonne(s) | Volume | Constat | Traitement prévu |
|---|---|---|---|---|
| Doublons | id_transaction / id_client | 190 lignes (3,0 %) | Doublons exacts, dont 7 masqués par la casse de id_client | Suppression |
| Dates | date_transaction | 2 803 lignes non ISO ; 12 vides ; ~13 impossibles | 6 formats ; certaines dates inexistantes | Conversion + suppression des impossibles |
| Villes | ville | 916 variantes fautives ; 77 vides | 26 graphies pour 5 villes | Correction + reconstitution via la station |
| Services | type_service | 1 010 libellés non standard ; 34 vides | 21 graphies pour 4 services | Uniformisation + inférence par le coût |
| Canaux / paiement | canal_acquisition, mode_paiement | 765 / 607 non standard ou vides | 25 et 9 graphies | Uniformisation, 'Non renseigné' |
| Statuts | statut | 956 lignes non standard | 18 graphies (FR/EN, casse, accents) | Uniformisation en 3 statuts |
| Quantités | quantite | 61 nulles, 6 négatives, 5 irréalistes | Erreurs de saisie | Suppression / valeur absolue |
| Prix | prix_unitaire_fcfa | ~70 anormaux (négatifs, nuls, x10, x100) | Écart net avec la médiane du service | Correction par facteur ou médiane |
| Remises | remise_pct | 79 invalides (< 0 ou > 100 %) | Remises réelles : 0-20 % | Mise à 0 % |
| Coûts | cout_unitaire_fcfa, cout_marketing_fcfa | 69 + 204 manquants ; 12 marketing aberrants | Valeurs absentes ou 20-40x la normale | Médiane par service / par canal |
| Satisfaction | note_client | 1 325 vides (20,7 %) | Surtout les annulations : normal | Conservée telle quelle |

Le détail chiffré de chaque correction figure dans `data/processed/journal_nettoyage.csv`.