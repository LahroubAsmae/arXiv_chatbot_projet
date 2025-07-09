"""
ÉTAPE 3 : Indexation sémantique des résumés
Utilise Sentence Transformers + FAISS comme demandé par le prof
"""
import sqlite3
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import chromadb
from pathlib import Path
import json

class SemanticIndexer:
    def __init__(self, db_path='data/processed/scopus_database.db'):
        self.db_path = db_path
        self.model_name = 'all-MiniLM-L6-v2'  # Modèle léger et efficace
        self.model = None
        self.faiss_index = None
        self.article_ids = []
        self.chroma_client = None
        
        print("🔧 Initialisation de l'indexeur sémantique")
        self.setup_directories()
    
    def setup_directories(self):
        """Crée les dossiers nécessaires"""
        Path('data/indexes').mkdir(parents=True, exist_ok=True)
        Path('data/embeddings').mkdir(parents=True, exist_ok=True)
        print("📁 Dossiers d'indexation créés")
    
    def load_sentence_transformer(self):
        """
        ÉTAPE 3.1 : Chargement du modèle Sentence Transformer
        Utilise BERT/MiniLM comme spécifié par le prof
        """
        print(f"🤖 Chargement du modèle Sentence Transformer: {self.model_name}")
        print("   (Première fois = téléchargement, peut prendre quelques minutes)")
        
        self.model = SentenceTransformer(self.model_name)
        print("✅ Modèle Sentence Transformer chargé")
        
        # Test du modèle
        test_text = "artificial intelligence in medicine"
        test_embedding = self.model.encode([test_text])
        print(f"🧪 Test réussi - Dimension des vecteurs: {test_embedding.shape[1]}")
        
        return test_embedding.shape[1]  # Retourne la dimension
    
    def load_articles_from_database(self):
        """
        ÉTAPE 3.2 : Chargement des articles depuis la base
        """
        print("📚 Chargement des articles depuis la base de données...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Requête pour récupérer les articles avec leurs informations
        query = '''
            SELECT 
                a.id,
                a.scopus_id,
                a.title,
                a.abstract,
                a.keywords,
                a.subject_areas,
                a.year,
                a.publication_name
            FROM articles a
            ORDER BY a.id
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"📊 {len(df)} articles chargés pour l'indexation")
        
        # Vérification des données
        has_abstract = (df['abstract'].notna() & (df['abstract'] != '')).sum()
        has_keywords = (df['keywords'].notna() & (df['keywords'] != '')).sum()
        
        print(f"   📝 Articles avec résumé: {has_abstract}")
        print(f"   🏷️ Articles avec mots-clés: {has_keywords}")
        
        return df
    
    def prepare_text_for_embedding(self, row):
        """
        ÉTAPE 3.3 : Préparation du texte pour vectorisation
        Combine titre + résumé + mots-clés pour un contexte riche
        """
        text_parts = []
        
        # Titre (toujours présent)
        if pd.notna(row['title']) and row['title']:
            text_parts.append(f"Title: {row['title']}")
        
        # Résumé (si disponible)
        if pd.notna(row['abstract']) and row['abstract']:
            text_parts.append(f"Abstract: {row['abstract']}")
        
        # Mots-clés (si disponibles)
        if pd.notna(row['keywords']) and row['keywords']:
            text_parts.append(f"Keywords: {row['keywords']}")
        
        # Domaines de recherche (si disponibles)
        if pd.notna(row['subject_areas']) and row['subject_areas']:
            text_parts.append(f"Subject: {row['subject_areas']}")
        
        # Combinaison de tous les éléments
        combined_text = " ".join(text_parts)
        
        return combined_text
    
    def create_embeddings(self, df):
        """
        ÉTAPE 3.4 : Création des embeddings (vectorisation)
        Transforme chaque article en vecteur numérique
        """
        print("🔄 Création des embeddings sémantiques...")
        
        # Préparation des textes
        texts = []
        for _, row in df.iterrows():
            text = self.prepare_text_for_embedding(row)
            texts.append(text)
        
        print(f"📝 {len(texts)} textes préparés pour vectorisation")
        
        # Vectorisation par batch pour optimiser la mémoire
        print("🧠 Vectorisation avec Sentence Transformers...")
        embeddings = self.model.encode(
            texts, 
            batch_size=8,  # Petits batches pour éviter les problèmes de mémoire
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        print(f"✅ Embeddings créés - Shape: {embeddings.shape}")
        
        # Sauvegarde des embeddings
        embeddings_path = 'data/embeddings/article_embeddings.npy'
        np.save(embeddings_path, embeddings)
        print(f"💾 Embeddings sauvegardés: {embeddings_path}")
        
        return embeddings
    
    def create_faiss_index(self, embeddings, df):
        """
        ÉTAPE 3.5 : Création de l'index FAISS
        Index vectoriel pour recherche sémantique rapide
        """
        print("🏗️ Création de l'index FAISS...")
        
        # Conversion en float32 (requis par FAISS)
        embeddings = embeddings.astype('float32')
        
        # Normalisation pour similarité cosinus
        faiss.normalize_L2(embeddings)
        
        # Création de l'index FAISS (Inner Product pour cosinus après normalisation)
        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)
        
        # Ajout des vecteurs à l'index
        self.faiss_index.add(embeddings)
        
        # Sauvegarde des IDs d'articles correspondants
        self.article_ids = df['id'].tolist()
        
        print(f"✅ Index FAISS créé avec {self.faiss_index.ntotal} vecteurs")
        
        # Sauvegarde de l'index
        faiss_path = 'data/indexes/scopus_faiss.index'
        faiss.write_index(self.faiss_index, faiss_path)
        
        # Sauvegarde des métadonnées
        metadata = {
            'article_ids': self.article_ids,
            'model_name': self.model_name,
            'dimension': dimension
        }
        
        with open('data/indexes/faiss_metadata.pkl', 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"💾 Index FAISS sauvegardé: {faiss_path}")
        
    def create_chromadb_collection(self, df):
        """
        ÉTAPE 3.6 : Création de la collection ChromaDB
        Alternative moderne à FAISS
        """
        print("🔄 Création de la collection ChromaDB...")
        
        # Initialisation du client ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="data/indexes/chroma_db")
        
        # Suppression de la collection existante si elle existe
        try:
            self.chroma_client.delete_collection("scopus_articles")
        except:
            pass
        
        # Création de la nouvelle collection
        collection = self.chroma_client.create_collection(
            name="scopus_articles",
            metadata={"description": "Collection d'articles Scopus avec embeddings sémantiques"}
        )
        
        # Préparation des données pour ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for _, row in df.iterrows():
            # Texte pour l'embedding
            text = self.prepare_text_for_embedding(row)
            documents.append(text)
            
            # Métadonnées
            metadata = {
                'scopus_id': str(row['scopus_id']),
                'title': str(row['title']),
                'year': int(row['year']) if pd.notna(row['year']) else 0,
                'publication_name': str(row['publication_name']) if pd.notna(row['publication_name']) else '',
                'has_abstract': bool(pd.notna(row['abstract']) and row['abstract'])
            }
            metadatas.append(metadata)
            
            # ID unique
            ids.append(str(row['id']))
        
        # Ajout à la collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ Collection ChromaDB créée avec {len(documents)} documents")
        
    def test_semantic_search(self, df):
        """
        ÉTAPE 3.7 : Test de la recherche sémantique
        Validation que l'indexation fonctionne
        """
        print("🧪 Test de la recherche sémantique...")
        
        # Requêtes de test
        test_queries = [
            "artificial intelligence in medicine",
            "machine learning for materials",
            "endoscopy and AI",
            "neural networks"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Test: '{query}'")
            
            # Test avec FAISS
            if self.faiss_index is not None:
                query_embedding = self.model.encode([query]).astype('float32')
                faiss.normalize_L2(query_embedding)
                
                scores, indices = self.faiss_index.search(query_embedding, k=3)
                
                print("  📊 Résultats FAISS (top 3):")
                for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                    if idx < len(self.article_ids):
                        article_id = self.article_ids[idx]
                        article_row = df[df['id'] == article_id].iloc[0]
                        title = article_row['title'][:60] + "..."
                        print(f"    {i+1}. Score: {score:.3f} - {title}")
            
            # Test avec ChromaDB
            if self.chroma_client is not None:
                try:
                    collection = self.chroma_client.get_collection("scopus_articles")
                    results = collection.query(
                        query_texts=[query],
                        n_results=3
                    )
                    
                    print("  📊 Résultats ChromaDB (top 3):")
                    if results['documents'] and results['documents'][0]:
                        for i, metadata in enumerate(results['metadatas'][0]):
                            title = metadata['title'][:60] + "..."
                            distance = results['distances'][0][i]
                            print(f"    {i+1}. Distance: {distance:.3f} - {title}")
                except Exception as e:
                    print(f"    ⚠️ Erreur ChromaDB: {e}")
    
    def save_indexing_report(self, df, embeddings):
        """
        ÉTAPE 3.8 : Génération du rapport d'indexation
        """
        print("📝 Génération du rapport d'indexation...")
        
        report = {
            'indexing_date': pd.Timestamp.now().isoformat(),
            'model_used': self.model_name,
            'total_articles': len(df),
            'embedding_dimension': embeddings.shape[1],
            'faiss_index_size': self.faiss_index.ntotal if self.faiss_index else 0,
            'articles_by_year': {str(k): int(v) for k, v in df['year'].value_counts().to_dict().items()},
            'has_abstract_count': int((df['abstract'].notna() & (df['abstract'] != '')).sum()),
            'has_keywords_count': int((df['keywords'].notna() & (df['keywords'] != '')).sum())
        }
        
        with open('data/indexes/indexing_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("✅ Rapport d'indexation sauvegardé")
        return report
    
    def process_complete_indexing(self):
        """
        PIPELINE COMPLET : Indexation sémantique complète
        """
        print("🚀 DÉBUT DE L'INDEXATION SÉMANTIQUE")
        print("=" * 50)
        
        try:
            # ÉTAPE 1 : Chargement du modèle
            embedding_dim = self.load_sentence_transformer()
            
            # ÉTAPE 2 : Chargement des articles
            df = self.load_articles_from_database()
            
            if len(df) == 0:
                print("❌ Aucun article trouvé dans la base de données")
                return False
            
            # ÉTAPE 3 : Création des embeddings
            embeddings = self.create_embeddings(df)
            
            # ÉTAPE 4 : Création de l'index FAISS
            self.create_faiss_index(embeddings, df)
            
            # ÉTAPE 5 : Création de la collection ChromaDB
            self.create_chromadb_collection(df)
            
            # ÉTAPE 6 : Tests de validation
            self.test_semantic_search(df)
            
            # ÉTAPE 7 : Rapport final
            report = self.save_indexing_report(df, embeddings)
            
            print("\n🎉 INDEXATION SÉMANTIQUE TERMINÉE!")
            print("=" * 40)
            print(f"📊 Articles indexés: {report['total_articles']}")
            print(f"🧠 Modèle utilisé: {report['model_used']}")
            print(f"📐 Dimension des vecteurs: {report['embedding_dimension']}")
            print(f"🔍 Index FAISS: {report['faiss_index_size']} vecteurs")
            
            print("\n📁 Fichiers créés:")
            print("  ✅ data/indexes/scopus_faiss.index")
            print("  ✅ data/indexes/faiss_metadata.pkl")
            print("  ✅ data/indexes/chroma_db/")
            print("  ✅ data/embeddings/article_embeddings.npy")
            print("  ✅ data/indexes/indexing_report.json")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERREUR LORS DE L'INDEXATION: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """
    FONCTION PRINCIPALE : Lancement de l'indexation sémantique
    """
    print("🎓 PROJET SCOPUS CHATBOT - ÉTAPE 3")
    print("Indexation sémantique avec Sentence Transformers")
    print("=" * 50)
    
    # Vérification de la base de données
    db_path = 'data/processed/scopus_database.db'
    if not Path(db_path).exists():
        print(f"❌ ERREUR: Base de données non trouvée: {db_path}")
        print("📋 Exécutez d'abord l'étape 2 (nettoyage et stockage)")
        return
    
    # Lancement de l'indexation
    indexer = SemanticIndexer(db_path)
    success = indexer.process_complete_indexing()
    
    if success:
        print("\n🎉 ÉTAPE 3 TERMINÉE AVEC SUCCÈS!")
        print("🚀 Prêt pour l'étape 4 : Interface utilisateur (Chatbot)")
    else:
        print("\n❌ ÉCHEC DE L'ÉTAPE 3")
        print("Consultez les messages d'erreur ci-dessus")

if __name__ == "__main__":
    main()
