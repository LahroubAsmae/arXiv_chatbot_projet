
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
    def __init__(self, db_path='data/processed/arxiv_database.db'):
        self.db_path = db_path
        self.model_name = 'all-MiniLM-L6-v2'  # Modèle léger et rapide
        self.model = None
        self.faiss_index = None
        self.article_ids = []
        self.chroma_client = None

        print(" Initialisation de l'indexeur sémantique (ArXiv)")
        self.setup_directories()

    def setup_directories(self):
        """Création des dossiers nécessaires"""
        Path('data/indexes').mkdir(parents=True, exist_ok=True)
        Path('data/embeddings').mkdir(parents=True, exist_ok=True)
        print(" Dossiers d'indexation créés")

    def load_sentence_transformer(self):
        """
        ÉTAPE 3.1 : Chargement du modèle Sentence Transformer
        """
        print(f"Chargement du modèle: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print(" Modèle chargé")

        # Test rapide
        test_text = "artificial intelligence in medicine"
        test_embedding = self.model.encode([test_text])
        print(f"Test réussi - Dimension vecteur: {test_embedding.shape[1]}")
        return test_embedding.shape[1]

    def load_articles_from_database(self):
        """
        ÉTAPE 3.2 : Charger les articles depuis la base ArXiv
        """
        print(" Chargement des articles depuis la base ArXiv...")
        conn = sqlite3.connect(self.db_path)

        query = '''
            SELECT 
                a.id,
                a.arxiv_id,
                a.title,
                a.abstract,
                a.categories,
                a.year,
                a.pdf_url
            FROM articles a
            ORDER BY a.id
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()

        print(f" {len(df)} articles trouvés")
        print(f"   Avec résumé: {(df['abstract'].notna() & (df['abstract'] != '')).sum()}")
        print(f"   Avec catégories: {(df['categories'].notna() & (df['categories'] != '')).sum()}")
        return df

    def prepare_text_for_embedding(self, row):
        """
        ÉTAPE 3.3 : Combinaison du titre + résumé + catégories
        """
        parts = []
        if pd.notna(row['title']) and row['title']:
            parts.append(f"Title: {row['title']}")
        if pd.notna(row['abstract']) and row['abstract']:
            parts.append(f"Abstract: {row['abstract']}")
        if pd.notna(row['categories']) and row['categories']:
            parts.append(f"Categories: {row['categories']}")
        return " ".join(parts)

    def create_embeddings(self, df):
        """
        ÉTAPE 3.4 : Générer les embeddings avec Sentence Transformers
        """
        print(" Génération des embeddings...")
        texts = [self.prepare_text_for_embedding(row) for _, row in df.iterrows()]

        embeddings = self.model.encode(
            texts,
            batch_size=8,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        print(f" Embeddings créés - Shape: {embeddings.shape}")

        embeddings_path = 'data/embeddings/article_embeddings_arxiv.npy'
        np.save(embeddings_path, embeddings)
        print(f"Sauvegardés: {embeddings_path}")
        return embeddings

    def create_faiss_index(self, embeddings, df):
        """
        ÉTAPE 3.5 : Création de l’index FAISS
        """
        print("Création de l’index FAISS...")
        embeddings = embeddings.astype('float32')
        faiss.normalize_L2(embeddings)

        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)
        self.faiss_index.add(embeddings)

        self.article_ids = df['id'].tolist()
        print(f"Index FAISS créé ({self.faiss_index.ntotal} vecteurs)")

        faiss_path = 'data/indexes/arxiv_faiss.index'
        faiss.write_index(self.faiss_index, faiss_path)

        metadata = {
            'article_ids': self.article_ids,
            'model_name': self.model_name,
            'dimension': dimension
        }
        with open('data/indexes/arxiv_faiss_metadata.pkl', 'wb') as f:
            pickle.dump(metadata, f)

        print(f"FAISS sauvegardé: {faiss_path}")

    def create_chromadb_collection(self, df):
        """
        ÉTAPE 3.6 : Création d’une collection ChromaDB (avec batching)
        """
        print("Création ChromaDB...")
        self.chroma_client = chromadb.PersistentClient(path="data/indexes/chroma_db")

        try:
            self.chroma_client.delete_collection("arxiv_articles")
        except:
            pass

        collection = self.chroma_client.create_collection(
            name="arxiv_articles",
            metadata={"description": "Collection d'articles ArXiv avec embeddings"}
        )

        documents, metadatas, ids = [], [], []
        for _, row in df.iterrows():
            text = self.prepare_text_for_embedding(row)
            documents.append(text)
            metadata = {
                'arxiv_id': str(row['arxiv_id']),
                'title': str(row['title']),
                'year': int(row['year']) if pd.notna(row['year']) else 0,
                'categories': str(row['categories']) if pd.notna(row['categories']) else '',
                'has_abstract': bool(pd.notna(row['abstract']) and row['abstract'])
            }
            metadatas.append(metadata)
            ids.append(str(row['id']))

        # Ajout par batches (max ~5000 pour être safe)
        batch_size = 5000
        for i in range(0, len(documents), batch_size):
            end = i + batch_size
            collection.add(
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end]
            )
            print(f"   Batch {i//batch_size+1} ajouté ({end if end < len(documents) else len(documents)}/{len(documents)})")

        print(f"Collection ChromaDB créée ({len(documents)} documents)")


    def test_semantic_search(self, df):
        """
        ÉTAPE 3.7 : Test de recherche sémantique
        """
        print(" Test recherche sémantique...")
        queries = ["artificial intelligence", "deep learning in physics", "medical imaging"]

        for query in queries:
            print(f"\n Query: {query}")

            # Test FAISS
            if self.faiss_index:
                q_emb = self.model.encode([query]).astype('float32')
                faiss.normalize_L2(q_emb)
                scores, indices = self.faiss_index.search(q_emb, k=3)
                print("   FAISS top 3:")
                for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                    if idx < len(self.article_ids):
                        art_id = self.article_ids[idx]
                        art = df[df['id'] == art_id].iloc[0]
                        print(f"    {i+1}. ({score:.3f}) {art['title'][:60]}...")

            # Test ChromaDB
            if self.chroma_client:
                try:
                    col = self.chroma_client.get_collection("arxiv_articles")
                    results = col.query(query_texts=[query], n_results=3)
                    print("   ChromaDB top 3:")
                    for i, md in enumerate(results['metadatas'][0]):
                        print(f"    {i+1}. {md['title'][:60]}...")
                except Exception as e:
                    print(f" Erreur ChromaDB: {e}")

    def save_indexing_report(self, df, embeddings):
        """
        ÉTAPE 3.8 : Sauvegarde d’un rapport JSON
        """
        report = {
            'indexing_date': pd.Timestamp.now().isoformat(),
            'model_used': self.model_name,
            'total_articles': len(df),
            'embedding_dimension': embeddings.shape[1],
            'faiss_index_size': self.faiss_index.ntotal if self.faiss_index else 0,
            'articles_by_year': {str(k): int(v) for k, v in df['year'].value_counts().to_dict().items()},
            'has_abstract_count': int((df['abstract'].notna() & (df['abstract'] != '')).sum())
        }
        with open('data/indexes/indexing_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(" Rapport d’indexation sauvegardé")
        return report

    def process_complete_indexing(self):
        """
        Pipeline complet d’indexation ArXiv
        """
        print(" DÉBUT INDEXATION ARXIV")
        print("="*50)

        try:
            dim = self.load_sentence_transformer()
            df = self.load_articles_from_database()
            if len(df) == 0:
                print(" Aucun article trouvé")
                return False

            embeddings = self.create_embeddings(df)
            self.create_faiss_index(embeddings, df)
            self.create_chromadb_collection(df)
            self.test_semantic_search(df)
            report = self.save_indexing_report(df, embeddings)

            print("\n INDEXATION TERMINÉE")
            print(f"Articles: {report['total_articles']}")
            print(f" Modèle: {report['model_used']}")
            print(f" Dimension: {report['embedding_dimension']}")
            print(f" FAISS vecteurs: {report['faiss_index_size']}")
            return True

        except Exception as e:
            print(f"\n Erreur: {e}")
            import traceback; traceback.print_exc()
            return False


def main():
    print("PROJET ARXIV CHATBOT - ÉTAPE 3")
    print("Indexation sémantique avec Sentence Transformers")
    print("="*50)

    db_path = 'data/processed/arxiv_database.db'
    if not Path(db_path).exists():
        print(f" Base non trouvée: {db_path}")
        return

    indexer = SemanticIndexer(db_path)
    success = indexer.process_complete_indexing()

    if success:
        print("\n Étape 3 réussie ! Prêt pour l’interface utilisateur")
    else:
        print("\nÉchec de l’étape 3")


if __name__ == "__main__":
    main()
