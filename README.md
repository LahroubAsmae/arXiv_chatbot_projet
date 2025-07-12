# 🔬 Chatbot Scopus - Guide Complet

Ce projet implémente un chatbot intelligent capable d'interroger une base de données d'articles scientifiques extraits de Scopus en utilisant des techniques de traitement du langage naturel et de recherche sémantique.

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du Projet](#architecture-du-projet)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Utilisation](#utilisation)
6. [Structure des Données](#structure-des-données)
7. [Technologies Utilisées](#technologies-utilisées)
8. [Dépannage](#dépannage)

## 🎯 Vue d'ensemble

Le chatbot Scopus permet de :
- ✅ Extraire automatiquement des données depuis l'API Scopus
- ✅ Nettoyer et structurer les données bibliographiques
- ✅ Créer des index sémantiques pour la recherche intelligente
- ✅ Fournir une interface conversationnelle intuitive
- ✅ Générer des visualisations et statistiques

## 🏗️ Architecture du Projet

\`\`\`
scopus_chatbot/
├── scripts/
│   ├── 1_extract_scopus_data.py      # Extraction API Scopus
│   ├── 2_clean_and_store_data.py     # Nettoyage et stockage
│   ├── 3_semantic_indexing.py        # Indexation sémantique
│   ├── 4_streamlit_chatbot.py        # Interface utilisateur
│   ├── 5_requirements.py             # Gestion des dépendances
│   ├── 6_run_complete_pipeline.py    # Pipeline complet
│   └── database_schema.sql           # Schéma de base de données
├── data/
│   ├── raw_scopus_data.csv          # Données brutes
│   ├── scopus_database.db           # Base SQLite
│   ├── scopus_faiss.index           # Index FAISS
│   └── faiss_metadata.pkl           # Métadonnées
├── chroma_db/                       # Base ChromaDB
├── requirements.txt                 # Dépendances Python
└── README.md                       # Ce fichier
\`\`\`

## 🚀 Installation

### 1. Prérequis
- Python 3.8 ou supérieur
- Clé API Scopus (gratuite sur https://dev.elsevier.com/)
- 4GB RAM minimum (8GB recommandé)

### 2. Installation des dépendances

\`\`\`bash
# Cloner ou télécharger le projet
cd scopus_chatbot

# Installer les packages Python
pip install -r requirements.txt

# Ou installation manuelle :
pip install pandas numpy requests sentence-transformers faiss-cpu chromadb streamlit plotly scikit-learn transformers torch
\`\`\`

### 3. Configuration de l'API Scopus

1. Créez un compte sur https://dev.elsevier.com/
2. Obtenez votre clé API gratuite
3. Modifiez le fichier `scripts/1_extract_scopus_data.py` :
   ```python
   API_KEY = "VOTRE_CLE_API_ICI"
   \`\`\`

## ⚙️ Configuration

### Paramètres d'extraction
Dans `1_extract_scopus_data.py`, vous pouvez modifier :
- Les requêtes de recherche
- Le nombre d'articles à extraire
- Les champs de données à récupérer

### Paramètres de recherche sémantique
Dans `3_semantic_indexing.py` :
- Modèle de sentence transformer (défaut: 'all-MiniLM-L6-v2')
- Paramètres FAISS et ChromaDB

## 🎮 Utilisation


#### Étape 1: Extraction des données
\`\`\`bash
python scripts/1_extract_scopus_data.py
\`\`\`
- Extrait les articles depuis Scopus
- Crée `raw_scopus_data.csv`

#### Étape 2: Nettoyage et stockage
\`\`\`bash
python scripts/2_clean_and_store_data.py
\`\`\`
- Nettoie les données
- Crée la base SQLite `scopus_database.db`

#### Étape 3: Indexation sémantique
\`\`\`bash
python scripts/3_semantic_indexing.py
\`\`\`
- Crée les index FAISS et ChromaDB
- Génère les embeddings sémantiques

#### Étape 4: Lancement du chatbot
\`\`\`bash
streamlit run scripts/4_streamlit_chatbot.py
\`\`\`

## 📊 Structure des Données

### Tables Principales
- **articles**: Informations des publications
- **authors**: Données des auteurs
- **affiliations**: Institutions de recherche
- **article_authors**: Relations article-auteur

### Champs Clés
- `title`: Titre de l'article
- `abstract`: Résumé
- `keywords`: Mots-clés
- `year`: Année de publication
- `doi`: Identifiant DOI
- `citation_count`: Nombre de citations

## 🛠️ Technologies Utilisées

### Backend
- **Python 3.8+**: Langage principal
- **SQLite**: Base de données relationnelle
- **Pandas**: Manipulation de données
- **Requests**: Appels API

### Intelligence Artificielle
- **Sentence Transformers**: Embeddings sémantiques
- **FAISS**: Recherche vectorielle rapide
- **ChromaDB**: Base de données vectorielle
- **Transformers**: Modèles de langage

### Interface Utilisateur
- **Streamlit**: Interface web interactive
- **Plotly**: Visualisations dynamiques

## 🔧 Dépannage

### Problèmes Courants

#### 1. Erreur d'API Scopus
\`\`\`
Erreur: Invalid API key
\`\`\`
**Solution**: Vérifiez votre clé API dans `1_extract_scopus_data.py`

#### 2. Mémoire insuffisante
\`\`\`
MemoryError during embedding creation
\`\`\`
**Solution**: 
- Réduisez la taille des batches
- Utilisez un modèle plus léger
- Augmentez la RAM disponible

#### 3. Packages manquants
\`\`\`
ModuleNotFoundError: No module named 'sentence_transformers'
\`\`\`
**Solution**: 
\`\`\`bash
pip install sentence-transformers
\`\`\`

#### 4. Base de données corrompue
\`\`\`
sqlite3.DatabaseError: database disk image is malformed
\`\`\`
**Solution**: Supprimez `scopus_database.db` et relancez l'étape 2

### Optimisations

#### Performance
- Utilisez `faiss-gpu` si vous avez un GPU
- Augmentez `batch_size` pour les machines puissantes
- Utilisez SSD pour le stockage

#### Qualité des Résultats
- Expérimentez avec différents modèles Sentence Transformers
- Ajustez les paramètres de recherche
- Enrichissez les requêtes d'extraction

## 📈 Exemples d'Utilisation

### Questions Types
- "Quelles sont les dernières recherches sur l'IA ?"
- "Trouve des articles sur le machine learning médical"
- "Combien d'articles parlent de NLP depuis 2020 ?"
- "Qui sont les auteurs principaux en computer vision ?"

### Filtres Disponibles
- **Par année**: Articles depuis une année donnée
- **Par auteur**: Publications d'un chercheur spécifique
- **Par domaine**: Filtrage par sujet de recherche
- **Par revue**: Articles d'une publication particulière

## 🤝 Contribution

Pour contribuer au projet :
1. Forkez le repository
2. Créez une branche feature
3. Committez vos changements
4. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la documentation Scopus API
- Vérifiez les logs d'erreur dans la console

---

**Développé avec ❤️ pour la recherche scientifique**
