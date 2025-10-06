
import pandas as pd
import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime

class ArxivDataProcessor:
    def __init__(self):
        self.db_path = 'data/processed/arxiv_database.db'
        print("🔧 Initialisation du processeur de données ArXiv")
        self.setup_database()
    
    def setup_database(self):
        """
        Création de la structure de base de données adaptée à ArXiv
        """
        print("Création de la structure de base de données...")
        
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        
        # Table articles
        conn.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arxiv_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                abstract TEXT,
                published TEXT,
                year INTEGER,
                pdf_url TEXT,
                categories TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print(" Table 'articles' créée")
        
        # Table auteurs
        conn.execute('''
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preferred_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print(" Table 'authors' créée")
        
        # Relations article–auteur
        conn.execute('''
            CREATE TABLE IF NOT EXISTS article_authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                FOREIGN KEY (article_id) REFERENCES articles (id),
                FOREIGN KEY (author_id) REFERENCES authors (id),
                UNIQUE(article_id, author_id)
            )
        ''')
        print(" Table 'article_authors' créée")
        
        # Index
        conn.execute('CREATE INDEX IF NOT EXISTS idx_articles_year ON articles(year)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title)')
        
        conn.commit()
        conn.close()
        print("Structure de base de données terminée\n")
    
    def clean_text(self, text):
        """
        Nettoyage des caractères spéciaux
        """
        if pd.isna(text) or text == '':
            return ''
        text = str(text)
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_year(self, date_str):
        """
        Extraction de l'année depuis la date de publication
        """
        if pd.isna(date_str) or date_str == '':
            return None
        year_match = re.search(r'(\d{4})', str(date_str))
        if year_match:
            year = int(year_match.group(1))
            if 1900 <= year <= 2030:
                return year
        return None
    
    def load_and_clean_data(self, json_file_path):
        """
        Chargement et nettoyage des données ArXiv
        """
        print(f"Chargement des données depuis {json_file_path}")
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        print(f"{len(df)} articles chargés dans Pandas DataFrame")
        
        print("Nettoyage des données avec Pandas...")
        
        # Suppression des doublons
        initial_count = len(df)
        df = df.drop_duplicates(subset=['arxiv_id'], keep='first')
        print(f"  {initial_count - len(df)} doublons supprimés")
        
        # Nettoyage des champs
        df['title'] = df['title'].apply(self.clean_text)
        df['abstract'] = df['abstract'].fillna('').apply(self.clean_text)
        
        # Conversion catégories (list -> string)
        df['categories'] = df['categories'].apply(
            lambda x: ', '.join(x) if isinstance(x, list) else ''
        )
        
        # Extraction de l’année
        df['year'] = df['published'].apply(self.extract_year)
        
        print(f" Nettoyage terminé : {len(df)} articles propres\n")
        return df
    
    def store_articles(self, df):
        """
        Stockage des articles
        """
        print(" Stockage des articles en base de données...")
        conn = sqlite3.connect(self.db_path)
        articles_stored = 0
        
        try:
            for _, row in df.iterrows():
                conn.execute('''
                    INSERT OR REPLACE INTO articles 
                    (arxiv_id, title, abstract, published, year, pdf_url, categories)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['arxiv_id'],
                    row['title'],
                    row['abstract'],
                    row['published'],
                    row['year'],
                    row['pdf_url'],
                    row['categories']
                ))
                articles_stored += 1
            conn.commit()
            print(f"  {articles_stored} articles stockés")
        except Exception as e:
            conn.rollback()
            print(f" Erreur stockage articles: {e}")
        finally:
            conn.close()
        return articles_stored
    
    def store_authors_and_relations(self, df):
        """
        Stockage des auteurs et relations
        """
        print(" Stockage des auteurs et relations...")
        conn = sqlite3.connect(self.db_path)
        relations_created = 0
        
        try:
            for _, row in df.iterrows():
                cursor = conn.execute(
                    'SELECT id FROM articles WHERE arxiv_id = ?', (row['arxiv_id'],)
                )
                article = cursor.fetchone()
                if not article:
                    continue
                article_id = article[0]
                
                authors = row.get('authors', [])
                if not isinstance(authors, list):
                    authors = []
                
                for author_name in authors:
                    author_name = self.clean_text(author_name)
                    if not author_name:
                        continue
                    
                    conn.execute('INSERT OR IGNORE INTO authors (preferred_name) VALUES (?)', (author_name,))
                    
                    cursor = conn.execute('SELECT id FROM authors WHERE preferred_name = ?', (author_name,))
                    author_id = cursor.fetchone()[0]
                    
                    conn.execute('''
                        INSERT OR IGNORE INTO article_authors (article_id, author_id)
                        VALUES (?, ?)
                    ''', (article_id, author_id))
                    
                    relations_created += 1
            
            conn.commit()
            
            total_authors = conn.execute('SELECT COUNT(*) FROM authors').fetchone()[0]
            print(f"   {total_authors} auteurs uniques stockés")
            print(f"  {relations_created} relations créées")
        except Exception as e:
            conn.rollback()
            print(f" Erreur stockage auteurs: {e}")
        finally:
            conn.close()
    
    def generate_statistics(self):
        """
        Génération des stats
        """
        print("Génération des statistiques...")
        conn = sqlite3.connect(self.db_path)
        
        total_articles = conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
        total_authors = conn.execute('SELECT COUNT(*) FROM authors').fetchone()[0]
        total_relations = conn.execute('SELECT COUNT(*) FROM article_authors').fetchone()[0]
        
        by_year = conn.execute('SELECT year, COUNT(*) FROM articles WHERE year IS NOT NULL GROUP BY year ORDER BY year DESC').fetchall()
        sample_articles = conn.execute('SELECT title, year FROM articles LIMIT 3').fetchall()
        
        conn.close()
        
        print(f"   Articles: {total_articles}")
        print(f"  Auteurs: {total_authors}")
        print(f"   Relations: {total_relations}")
        print("   Articles par année:", by_year[:5])
        print(" Échantillon:")
        for t, y in sample_articles:
            print(f"   - {y}: {t[:60]}...")
    
    def process_complete_pipeline(self, json_file_path):
        print("PIPELINE COMPLET DE NETTOYAGE & STOCKAGE (ArXiv)")
        print("=" * 60)
        df = self.load_and_clean_data(json_file_path)
        self.store_articles(df)
        self.store_authors_and_relations(df)
        self.generate_statistics()

def main():
    print(" PROJET ARXIV CHATBOT - ÉTAPE 2 (Nettoyage & stockage)")
    print("=" * 50)
    
    import glob
    json_files = glob.glob('data/raw/*.json')
    if not json_files:
        print("Aucun fichier JSON trouvé")
        return
    
    json_file = json_files[-1]  # Prend le plus récent
    print(f"Fichier sélectionné: {json_file}")

    processor = ArxivDataProcessor()
    processor.process_complete_pipeline(json_file)

if __name__ == "__main__":
    main()
