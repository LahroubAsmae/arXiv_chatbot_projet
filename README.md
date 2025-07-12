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
├── .vscode/                          # Configuration VS Code
├── config/
│   ├── __pycache__/
│   └── api_config.py                 # Configuration API Scopus
├── data/
│   ├── embeddings/
│   │   └── article_embeddings.pkl   # Embeddings pré-calculés
│   ├── indexes/                      # Index de recherche
│   ├── processed/
│   │   └── scopus_database.db       # Base de données SQLite
│   └── raw/
│       ├── test_extraction.csv      # Données brutes CSV
│       └── test_extraction.json     # Données brutes JSON
├── logs/                            # Fichiers de logs
├── src/
│   ├── chatbot_interface.py         # Interface utilisateur Streamlit
│   ├── data_processor.py            # Traitement des données
│   ├── scopus_extractor.py          # Extraction API Scopus
│   └── semantic_indexer.py          # Indexation sémantique
├── venv/                            # Environnement virtuel
├── .env                             # Variables d'environnement
├── README.md                        # Documentation
├── requirements.txt                 # Dépendances Python
└── validate_step2.py                # Validation des étapes
```

## Installation

### Prérequis

- Python 3.8+
- 4 Go de RAM minimum
- Clé API Scopus

### Installation des dépendances

```bash
# Cloner le repository
git clone https://github.com/votre-username/scopus-chatbot.git
cd scopus-chatbot

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Configuration

### Configuration de l'API Scopus

1. Créer un compte sur le portail développeur d'Elsevier
2. Obtenir une clé API gratuite
3. Configurer la clé dans `config/api_config.py` :

```python
API_KEY = "VOTRE_CLE_API_SCOPUS"
BASE_URL = "https://api.elsevier.com/content/search/scopus"
```

### Variables d'environnement

Créer un fichier `.env` à la racine du projet :

```env
SCOPUS_API_KEY=your_api_key_here
DATABASE_PATH=data/processed/scopus_database.db
EMBEDDINGS_PATH=data/embeddings/article_embeddings.pkl
```

## Utilisation

### Étapes d'exécution

#### 1. Extraction des données
```bash
python src/scopus_extractor.py
```
**Résultat :** Données sauvegardées dans `data/raw/`

#### 2. Traitement des données
```bash
python src/data_processor.py
```
**Résultat :** Base de données créée dans `data/processed/scopus_database.db`

#### 3. Indexation sémantique
```bash
python src/semantic_indexer.py
```
**Résultat :** Embeddings sauvegardés dans `data/embeddings/`

#### 4. Validation (optionnel)
```bash
python validate_step2.py
```

#### 5. Lancement du chatbot
```bash
streamlit run src/chatbot_interface.py
```

Accéder à l'interface : http://localhost:8501

## Structure des Données

### Base de données SQLite

**Table Articles**
- id : Identifiant unique
- title : Titre de l'article
- abstract : Résumé
- keywords : Mots-clés
- year : Année de publication
- doi : Identifiant DOI
- citation_count : Nombre de citations
- source_title : Nom de la revue
- authors : Auteurs

### Formats de données

**CSV** (`data/raw/test_extraction.csv`)
- Format tabulaire pour analyse
- Colonnes : title, abstract, authors, year, doi, citations

**JSON** (`data/raw/test_extraction.json`)
- Format structuré pour l'API
- Métadonnées complètes des articles

## Technologies Utilisées

### Backend
- **Python 3.8+** : Langage principal
- **SQLite** : Base de données relationnelle
- **Pandas** : Manipulation de données
- **Requests** : Appels API

### Intelligence Artificielle
- **Sentence Transformers** : Génération d'embeddings
- **FAISS** : Recherche vectorielle rapide
- **ChromaDB** : Base vectorielle flexible

### Interface
- **Streamlit** : Interface web interactive
- **Plotly** : Visualisations dynamiques

## Exemples d'Utilisation

### Questions types

```python
"Quelles sont les dernières recherches en intelligence artificielle ?"
"Trouve des articles sur le machine learning médical"
"Articles sur le NLP depuis 2020"
"Qui sont les auteurs principaux en computer vision ?"
"Montre-moi les tendances de recherche en deep learning"
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
Solution: Vérifier la clé dans config/api_config.py ou .env
```

**Mémoire insuffisante**
```
MemoryError during embedding creation
Solution: Réduire la taille des batches dans semantic_indexer.py
```

**Module manquant**
```
ModuleNotFoundError: No module named 'xxx'
Solution: pip install [module_manquant]
```

**Base de données corrompue**
```
sqlite3.DatabaseError: database disk image is malformed
Solution: Supprimer data/processed/scopus_database.db et relancer data_processor.py
```

**Problème d'environnement virtuel**
```
Erreur: Module non trouvé malgré l'installation
Solution: Vérifier que l'environnement virtuel est activé
```

## Développement

### Structure du code

- `src/scopus_extractor.py` : Extraction des données via API
- `src/data_processor.py` : Nettoyage et structuration
- `src/semantic_indexer.py` : Création des embeddings
- `src/chatbot_interface.py` : Interface utilisateur
- `config/api_config.py` : Configuration centralisée
- `validate_step2.py` : Tests de validation

### Logs et debugging

Les logs sont sauvegardés dans le dossier `logs/` pour faciliter le debugging.

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
- Vérifier les logs dans le dossier `logs/`
- Créer une issue GitHub si nécessaire

---

Développé pour faciliter la recherche scientifique
