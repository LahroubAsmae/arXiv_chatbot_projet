# Chatbot ArXiv

Un système intelligent de recherche d'articles scientifiques utilisant l'API arXiv et le traitement du langage naturel.

## Description

Ce projet implémente un chatbot conversationnel capable d'interroger une base de données d'articles scientifiques issus d'arXiv. Il utilise des techniques avancées de recherche sémantique et d'indexation vectorielle pour fournir des réponses pertinentes aux requêtes des utilisateurs.

## Fonctionnalités

- **Extraction automatique** des données depuis l'API arXiv
- **Nettoyage et structuration** des données scientifiques
- **Indexation sémantique** avec embeddings vectoriels
- **Interface conversationnelle** intuitive
- **Visualisations interactives** des résultats
- **Recherche par similarité** contextuelle

## Architecture du Projet

\`\`\`
arxiv_chatbot/
├── .vscode/                          # Configuration VS Code
├── config/
│   ├── __pycache__/
│   └── api_config.py                 # Configuration API arXiv
├── data/
│   ├── embeddings/
│   │   └── article_embeddings_arxiv.npy   # Embeddings pré-calculés
│   ├── indexes/
│   │   ├── faiss_index.bin          # Index FAISS
│   │   └── chroma_db/               # Collection ChromaDB
│   ├── processed/
│   │   └── arxiv_database.db        # Base de données SQLite
│   └── raw/
│       ├── arxiv_extraction.csv     # Données brutes CSV
│       └── arxiv_extraction.json    # Données brutes JSON
├── logs/                            # Fichiers de logs
├── src/
│   ├── chatbot_interface.py         # Interface utilisateur Streamlit
│   ├── data_processor.py            # Traitement des données
│   ├── arxiv_extractor_massive.py   # Extraction API arXiv
│   └── semantic_indexer.py          # Indexation sémantique
├── venv/                            # Environnement virtuel
├── .env                             # Variables d'environnement
├── README.md                        # Documentation
├── requirements.txt                 # Dépendances Python
└── validate_step2.py                # Validation des étapes
\`\`\`

## Installation

### Prérequis

- Python 3.13+
- 4 Go de RAM minimum
- Connexion Internet (pas de clé API requise pour arXiv)

### Installation des dépendances

\`\`\`bash
# Cloner le repository
git clone https://github.com/votre-username/arxiv-chatbot.git
cd arxiv-chatbot

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
\`\`\`

## Configuration

### Configuration de l'API arXiv

L'API arXiv est **gratuite et ne nécessite pas de clé API**. Cependant, il est important de respecter les limites de taux :

- Maximum 1 requête toutes les 3 secondes
- Pagination automatique pour les grands corpus
- Gestion automatique des erreurs réseau avec retry exponentiel

Configuration dans `config/api_config.py` :

\`\`\`python
BASE_URL = "http://export.arxiv.org/api/query"
RATE_LIMIT_DELAY = 3  # secondes entre chaque requête
MAX_RESULTS_PER_REQUEST = 2000
\`\`\`

### Variables d'environnement

Créer un fichier `.env` à la racine du projet :

\`\`\`env
DATABASE_PATH=data/processed/arxiv_database.db
EMBEDDINGS_PATH=data/embeddings/article_embeddings_arxiv.npy
FAISS_INDEX_PATH=data/indexes/faiss_index.bin
CHROMA_DB_PATH=data/indexes/chroma_db
\`\`\`

## Utilisation

### Étapes d'exécution

#### 1. Extraction des données
\`\`\`bash
python src/arxiv_extractor_massive.py
\`\`\`
**Résultat :** 13,641 articles extraits et sauvegardés dans `data/raw/`

**Stratégie d'extraction :**
- Par catégories : cs.AI, cs.LG, cs.CV, cs.CL (2020-2025)
- Par mots-clés : "deep learning", "transformer", "neural networks"
- Articles à fort impact scientifique

#### 2. Traitement des données
\`\`\`bash
python src/data_processor.py
\`\`\`
**Résultat :** Base de données créée dans `data/processed/arxiv_database.db`

**Pipeline de nettoyage :**
- Déduplication (151 doublons supprimés)
- Normalisation textuelle
- Extraction temporelle
- Normalisation des auteurs
- Validation des catégories

#### 3. Indexation sémantique
\`\`\`bash
python src/semantic_indexer.py
\`\`\`
**Résultat :** 
- Embeddings sauvegardés dans `data/embeddings/article_embeddings_arxiv.npy`
- Index FAISS créé dans `data/indexes/faiss_index.bin`
- Collection ChromaDB dans `data/indexes/chroma_db/`

**Modèle utilisé :** all-MiniLM-L6-v2 (384 dimensions)

#### 4. Validation (optionnel)
\`\`\`bash
python validate_step2.py
\`\`\`

#### 5. Lancement du chatbot
\`\`\`bash
streamlit run src/chatbot_interface.py
\`\`\`

Accéder à l'interface : http://localhost:8501

## Structure des Données

### Base de données SQLite

**Table articles**
- id : Identifiant arXiv unique
- title : Titre de l'article
- abstract : Résumé complet
- published : Date de publication
- categories : Catégories arXiv (format JSON)
- doi : Identifiant DOI (si disponible)
- pdf_url : Lien vers le PDF

**Table authors**
- id : Identifiant auto-incrémenté
- name : Nom normalisé
- affiliation : Affiliation (si disponible)
- orcid : Identifiant ORCID (si disponible)

**Table article_authors**
- article_id : Référence vers articles
- author_id : Référence vers authors
- author_order : Ordre de signature

**Table categories**
- code : Code de catégorie (ex: cs.AI)
- name : Nom complet
- description : Description de la catégorie

### Formats de données

**CSV** (`data/raw/arxiv_extraction.csv`)
- Format tabulaire pour analyse
- Colonnes : id, title, abstract, authors, published, categories, doi, pdf_url

**JSON** (`data/raw/arxiv_extraction.json`)
- Format structuré pour l'API
- Métadonnées complètes des articles au format arXiv

## Technologies Utilisées

### Backend
- **Python 3.13** : Langage principal
- **SQLite** : Base de données relationnelle (450 MB)
- **Pandas** : Manipulation de données
- **Requests** : Appels API avec gestion du rate limiting

### Intelligence Artificielle
- **Sentence Transformers** : Génération d'embeddings (all-MiniLM-L6-v2)
- **FAISS** : Recherche vectorielle ultra-rapide (< 0.1ms)
- **ChromaDB** : Base vectorielle avec métadonnées

### Interface
- **Streamlit** : Interface web interactive
- **Plotly** : Visualisations dynamiques

## Statistiques du Corpus

- **13,490 articles uniques** (après déduplication)
- **~35,000 auteurs uniques**
- **45 catégories arXiv**
- **Période couverte :** 2020-2025
- **Complétude :** 100% (titre, résumé, auteurs)
- **Précision@5 :** 84%
- **Temps de recherche :** < 0.8s

## Exemples d'Utilisation

### Questions types

\`\`\`python
"Quelles sont les dernières recherches en intelligence artificielle ?"
"Trouve des articles sur le machine learning médical"
"Articles sur les transformers en NLP"
"Qui sont les auteurs principaux en computer vision ?"
"Montre-moi les tendances de recherche en deep learning"
"Articles sur reinforcement learning depuis 2023"
\`\`\`

### Filtres disponibles

- Par année de publication (2020-2025)
- Par catégorie arXiv (cs.AI, cs.LG, cs.CV, cs.CL, etc.)
- Par auteur
- Tri par pertinence, année, ou citations

## Résolution de Problèmes

### Erreurs communes

**Rate limiting dépassé**
\`\`\`
Erreur: 429 Too Many Requests
Solution: Le système gère automatiquement les délais. Attendre 3 secondes entre requêtes.
\`\`\`

**Mémoire insuffisante**
\`\`\`
MemoryError during embedding creation
Solution: Réduire batch_size à 4 dans semantic_indexer.py
\`\`\`

**Module manquant**
\`\`\`
ModuleNotFoundError: No module named 'sentence_transformers'
Solution: pip install sentence-transformers
\`\`\`

**Base de données corrompue**
\`\`\`
sqlite3.DatabaseError: database disk image is malformed
Solution: Supprimer data/processed/arxiv_database.db et relancer data_processor.py
\`\`\`

**Index FAISS introuvable**
\`\`\`
FileNotFoundError: faiss_index.bin not found
Solution: Relancer python src/semantic_indexer.py
\`\`\`

**Problème d'environnement virtuel**
\`\`\`
Erreur: Module non trouvé malgré l'installation
Solution: Vérifier que l'environnement virtuel est activé (venv\Scripts\activate)
\`\`\`

## Développement

### Structure du code

- `src/arxiv_extractor_massive.py` : Extraction massive via API arXiv
- `src/data_processor.py` : Nettoyage et structuration (5 étapes)
- `src/semantic_indexer.py` : Création des embeddings et index
- `src/chatbot_interface.py` : Interface Streamlit avec visualisations
- `config/api_config.py` : Configuration centralisée
- `validate_step2.py` : Tests de validation

### Logs et debugging

Les logs sont sauvegardés dans le dossier `logs/` avec horodatage pour faciliter le debugging.

### Optimisations

- **Caching Streamlit** : Modèle et index chargés une seule fois
- **Batch processing** : Traitement par lots de 8 articles
- **Index FAISS** : Recherche exhaustive exacte (IndexFlatIP)
- **Normalisation L2** : Conversion produit scalaire → similarité cosinus

## Métriques de Qualité

- **Complétude :** 100% (titre, résumé, auteurs)
- **Cohérence :** 100% (IDs, dates, catégories valides)
- **Unicité :** 0 doublon résiduel
- **Précision@5 :** 84%
- **Précision@10 :** 79%
- **Temps de réponse médian :** 0.8s

## Contribution

Pour contribuer au projet :

1. Fork le repository
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commiter les changements (`git commit -m 'Add AmazingFeature'`)
4. Pusher vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## Perspectives d'Évolution

### Court terme (3-6 mois)
- Extension à 50K+ articles
- Export BibTeX/RIS
- Alertes automatiques par email

### Moyen terme (6-12 mois)
- Analyse texte intégral (PDFs)
- Extraction d'informations (méthodes, résultats, datasets)
- Recommandations personnalisées
- Intégration PubMed, HAL

### Long terme (1-2 ans)
- Résumés générés par LLM
- Graphes de connaissances
- Détection de tendances émergentes
- Plateforme collaborative

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Support

### Ressources utiles

- [Documentation API arXiv](https://arxiv.org/help/api)
- [Guide Sentence-Transformers](https://www.sbert.net/)
- [Documentation FAISS](https://github.com/facebookresearch/faiss/wiki)
- [Guide Streamlit](https://docs.streamlit.io/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

### Contact

Pour toute question ou problème :
- Consulter la documentation complète dans le rapport PDF
- Vérifier les logs dans le dossier `logs/`
- Créer une issue GitHub si nécessaire

---

**Développé par :** Asmae LAHROUB, Saida ALABA, Wissal ENNAJAH  
**Encadré par :** Pr. Abdlellah Madani  
**Université Chouaib Doukkali - Faculté des Sciences**  
**Master : Ingénierie informatique et analyse données**  
**Année Universitaire 2024/2025**

---

*Développé pour faciliter la recherche scientifique et démocratiser l'accès à la connaissance*
\`\`\`
