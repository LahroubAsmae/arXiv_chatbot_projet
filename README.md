# Chatbot Scopus

Un système intelligent de recherche d'articles scientifiques utilisant l'API Scopus et le traitement du langage naturel.

## Description

Ce projet implémente un chatbot conversationnel capable d'interroger une base de données d'articles scientifiques issus de Scopus. Il utilise des techniques avancées de recherche sémantique et d'indexation vectorielle pour fournir des réponses pertinentes aux requêtes des utilisateurs.

## Fonctionnalités

- **Extraction automatique** des données depuis l'API Scopus
- **Nettoyage et structuration** des données scientifiques
- **Indexation sémantique** avec embeddings vectoriels
- **Interface conversationnelle** intuitive
- **Visualisations interactives** des résultats
- **Recherche par similarité** contextuelle

## Architecture du Projet

```
scopus_chatbot/
├── scripts/
│   ├── 1_extract_scopus_data.py
│   ├── 2_clean_and_store_data.py
│   ├── 3_semantic_indexing.py
│   ├── 4_streamlit_chatbot.py
│   ├── 5_requirements.py
│   ├── 6_run_complete_pipeline.py
│   └── database_schema.sql
├── data/
│   ├── raw_scopus_data.csv
│   ├── scopus_database.db
│   ├── scopus_faiss.index
│   └── faiss_metadata.pkl
├── chroma_db/
├── requirements.txt
└── README.md
```

## Installation

### Prérequis

- Python 3.8+
- 4 Go de RAM minimum
- Clé API Scopus

### Installation des dépendances

```bash
pip install -r requirements.txt
```

Ou manuellement :

```bash
pip install pandas numpy requests sentence-transformers faiss-cpu chromadb streamlit plotly scikit-learn transformers torch
```

## Configuration

### Configuration de l'API Scopus

1. Créer un compte sur le portail développeur d'Elsevier
2. Obtenir une clé API gratuite
3. Configurer la clé dans `scripts/1_extract_scopus_data.py` :

```python
API_KEY = "VOTRE_CLE_API_SCOPUS"
```

## Utilisation

### Méthode rapide

```bash
python scripts/6_run_complete_pipeline.py
```

### Étapes détaillées

#### 1. Extraction des données
```bash
python scripts/1_extract_scopus_data.py
```

#### 2. Nettoyage et stockage
```bash
python scripts/2_clean_and_store_data.py
```

#### 3. Indexation sémantique
```bash
python scripts/3_semantic_indexing.py
```

#### 4. Lancement du chatbot
```bash
streamlit run scripts/4_streamlit_chatbot.py
```

Accéder à l'interface : http://localhost:8501

## Structure des Données

### Tables principales

**Articles**
- id, title, abstract, keywords
- year, doi, citation_count
- source_title, authors

**Authors**
- id, name, affiliation, email

**Article_Authors**
- article_id, author_id

## Technologies Utilisées

### Backend
- Python 3.8+
- SQLite
- Pandas
- Requests

### Intelligence Artificielle
- Sentence Transformers
- FAISS
- ChromaDB

### Interface
- Streamlit
- Plotly

## Exemples d'Utilisation

### Questions types

```
"Quelles sont les dernières recherches en intelligence artificielle ?"
"Trouve des articles sur le machine learning médical"
"Articles sur le NLP depuis 2020"
"Qui sont les auteurs principaux en computer vision ?"
```

### Filtres disponibles

- Par année de publication
- Par auteur
- Par domaine de recherche
- Par revue scientifique
- Par nombre de citations

## Résolution de Problèmes

### Erreurs communes

**Clé API invalide**
```
Erreur: Invalid API key
Solution: Vérifier la clé dans 1_extract_scopus_data.py
```

**Mémoire insuffisante**
```
MemoryError during embedding creation
Solution: Réduire la taille des batches
```

**Module manquant**
```
ModuleNotFoundError: No module named 'xxx'
Solution: pip install [module_manquant]
```

**Base de données corrompue**
```
sqlite3.DatabaseError: database disk image is malformed
Solution: Supprimer le fichier .db et relancer l'étape 2
```

## Contribution

Pour contribuer au projet :

1. Fork le repository
2. Créer une branche feature
3. Commiter les changements
4. Pusher vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Support

### Ressources utiles

- [Documentation API Scopus](https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl)
- [Guide Streamlit](https://docs.streamlit.io/)
- [Sentence-Transformers](https://www.sbert.net/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss/wiki)

### Contact

Pour toute question ou problème :
- Consulter la documentation
- Vérifier les issues GitHub
- Créer une nouvelle issue si nécessaire

---

Développé pour faciliter la recherche scientifique
