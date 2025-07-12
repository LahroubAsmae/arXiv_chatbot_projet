"""
ÉTAPE 2 : Nettoyage et stockage des données Scopus
"""
import pandas as pd
import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime

class ScopusDataProcessor:
    def __init__(self):
        self.db_path = 'data/processed/scopus_database.db'
        print("🔧 Initialisation du processeur de données Scopus")
        self.setup_database()
    
    def setup_database(self):
        """
        ÉTAPE 2.1 : Création de la structure de base de données
        Selon les spécifications du prof : tables relationnelles
        """
        print("🏗️ Création de la structure de base de données...")
        
        # Créer le dossier s'il n'existe pas
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        
        # Table articles (champs requis par le prof)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scopus_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                abstract TEXT,
                cover_date TEXT,
                year INTEGER,
                publication_name TEXT,
                doi TEXT,
                keywords TEXT,
                subject_areas TEXT,
                citation_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Table 'articles' créée")
        
        # Table auteurs (selon spécifications)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scopus_author_id TEXT,
                preferred_name TEXT NOT NULL,
                orcid TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Table 'authors' créée")
        
        # Table affiliations (selon spécifications)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS affiliations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scopus_affiliation_id TEXT,
                institution_name TEXT NOT NULL,
                country TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Table 'affiliations' créée")
        
        # Relations auteur-article (many-to-many)
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
        print("  ✅ Table 'article_authors' (relations) créée")
        
        # Index pour optimisation (comme demandé par le prof)
        conn.execute('CREATE INDEX IF NOT EXISTS idx_articles_year ON articles(year)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title)')
        print("  ✅ Index d'optimisation créés")
        
        conn.commit()
        conn.close()
        print("✅ Structure de base de données terminée\n")
    
    def clean_text(self, text):
        """
        ÉTAPE 2.2 : Nettoyage des caractères spéciaux
        Traitement des caractères spéciaux et valeurs manquantes (requis par le prof)
        """
        if pd.isna(text) or text == '':
            return ''
        
        text = str(text)
        # Suppression des caractères de contrôle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        # Normalisation des espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_year(self, date_str):
        """
        ÉTAPE 2.3 : Extraction de l'année depuis cover_date
        """
        if pd.isna(date_str) or date_str == '':
            return None
        
        # Recherche de l'année (4 chiffres)
        year_match = re.search(r'(\d{4})', str(date_str))
        if year_match:
            year = int(year_match.group(1))
            # Validation de l'année
            if 1900 <= year <= 2030:
                return year
        return None
    
    def normalize_authors(self, authors_str):
        """
        ÉTAPE 2.4 : Normalisation des auteurs
        Selon spécifications : normalisation des auteurs
        """
        if pd.isna(authors_str) or authors_str == '':
            return []
        
        # Séparation par virgule, point-virgule ou "and"
        authors = re.split(r'[;,]|\sand\s', str(authors_str))
        
        # Nettoyage de chaque nom
        clean_authors = []
        for author in authors:
            author = self.clean_text(author)
            if len(author) > 1:  # Éviter les initiales seules
                clean_authors.append(author)
        
        return clean_authors
    
    def load_and_clean_data(self, json_file_path):
        """
        ÉTAPE 2.5 : Chargement et nettoyage avec Pandas
        Utilisation de Pandas comme demandé par le prof
        """
        print(f"📂 Chargement des données depuis {json_file_path}")
        
        # Chargement du fichier JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Conversion en DataFrame Pandas
        df = pd.DataFrame(data)
        print(f"📊 {len(df)} articles chargés dans Pandas DataFrame")
        
        print("🧹 Nettoyage des données avec Pandas...")
        
        # ÉTAPE 2.5.1 : Suppression des doublons (requis par le prof)
        initial_count = len(df)
        df = df.drop_duplicates(subset=['scopus_id'], keep='first')
        duplicates_removed = initial_count - len(df)
        if duplicates_removed > 0:
            print(f"  🗑️ {duplicates_removed} doublons supprimés")
        else:
            print("  ✅ Aucun doublon détecté")
        
        # ÉTAPE 2.5.2 : Nettoyage des champs textuels
        print("  🧽 Nettoyage des caractères spéciaux...")
        text_fields = ['title', 'publication_name', 'keywords', 'subject_areas']
        for field in text_fields:
            if field in df.columns:
                df[field] = df[field].apply(self.clean_text)
                print(f"    ✅ Champ '{field}' nettoyé")
        
        # ÉTAPE 2.5.3 : Extraction de l'année
        print("  📅 Extraction des années...")
        df['year'] = df['cover_date'].apply(self.extract_year)
        years_extracted = df['year'].notna().sum()
        print(f"    ✅ {years_extracted} années extraites")
        
        # ÉTAPE 2.5.4 : Traitement des valeurs manquantes
        print("  🔧 Traitement des valeurs manquantes...")
        df['abstract'] = df['abstract'].fillna('')
        df['keywords'] = df['keywords'].fillna('')
        df['subject_areas'] = df['subject_areas'].fillna('')
        df['citation_count'] = pd.to_numeric(df['citation_count'], errors='coerce').fillna(0)
        print("    ✅ Valeurs manquantes traitées")
        
        print(f"✅ Nettoyage terminé : {len(df)} articles propres\n")
        return df
    
    def store_articles(self, df):
        """
        ÉTAPE 2.6 : Stockage des articles en base relationnelle
        """
        print("💾 Stockage des articles en base de données...")
        
        conn = sqlite3.connect(self.db_path)
        articles_stored = 0
        
        try:
            for _, row in df.iterrows():
                # Insertion de chaque article
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO articles 
                    (scopus_id, title, abstract, cover_date, year, publication_name, 
                     doi, keywords, subject_areas, citation_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['scopus_id'],
                    row['title'],
                    row.get('abstract', ''),
                    row['cover_date'],
                    row['year'],
                    row['publication_name'],
                    row.get('doi', ''),
                    row['keywords'],
                    row['subject_areas'],
                    int(row['citation_count'])
                ))
                articles_stored += 1
            
            conn.commit()
            print(f"  ✅ {articles_stored} articles stockés")
            
        except Exception as e:
            conn.rollback()
            print(f"  ❌ Erreur lors du stockage : {e}")
            raise
        finally:
            conn.close()
        
        return articles_stored
    
    def store_authors_and_relations(self, df):
        """
        ÉTAPE 2.7 : Stockage des auteurs et création des relations
        Relations auteur-article comme demandé par le prof
        """
        print("👥 Traitement des auteurs et relations...")
        
        conn = sqlite3.connect(self.db_path)
        authors_stored = 0
        relations_created = 0
        
        try:
            for _, row in df.iterrows():
                # Récupération de l'ID de l'article
                cursor = conn.execute('SELECT id FROM articles WHERE scopus_id = ?', (row['scopus_id'],))
                article_result = cursor.fetchone()
                if not article_result:
                    continue
                
                article_id = article_result[0]
                
                # Traitement des auteurs
                authors = self.normalize_authors(row.get('authors', ''))
                
                for author_name in authors:
                    if author_name:
                        # Insertion ou récupération de l'auteur
                        conn.execute('''
                            INSERT OR IGNORE INTO authors (preferred_name)
                            VALUES (?)
                        ''', (author_name,))
                        
                        # Récupération de l'ID de l'auteur
                        cursor = conn.execute('''
                            SELECT id FROM authors WHERE preferred_name = ?
                        ''', (author_name,))
                        author_id = cursor.fetchone()[0]
                        
                        # Création de la relation article-auteur
                        cursor = conn.execute('''
                            INSERT OR IGNORE INTO article_authors (article_id, author_id)
                            VALUES (?, ?)
                        ''', (article_id, author_id))
                        
                        if cursor.rowcount > 0:
                            relations_created += 1
                        
                        authors_stored += 1
            
            conn.commit()
            
            # Comptage des auteurs uniques
            cursor = conn.execute('SELECT COUNT(*) FROM authors')
            unique_authors = cursor.fetchone()[0]
            
            print(f"  ✅ {unique_authors} auteurs uniques stockés")
            print(f"  ✅ {relations_created} relations article-auteur créées")
            
        except Exception as e:
            conn.rollback()
            print(f"  ❌ Erreur lors du traitement des auteurs : {e}")
            raise
        finally:
            conn.close()
        
        return unique_authors, relations_created
    
    def generate_statistics(self):
        """
        ÉTAPE 2.8 : Génération des statistiques de validation
        """
        print("📊 Génération des statistiques...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Statistiques générales
        cursor = conn.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        
        cursor = conn.execute('SELECT COUNT(*) FROM authors')
        total_authors = cursor.fetchone()[0]
        
        cursor = conn.execute('SELECT COUNT(*) FROM article_authors')
        total_relations = cursor.fetchone()[0]
        
        # Articles par année
        cursor = conn.execute('''
            SELECT year, COUNT(*) 
            FROM articles 
            WHERE year IS NOT NULL 
            GROUP BY year 
            ORDER BY year DESC
        ''')
        by_year = cursor.fetchall()
        
        # Échantillon d'articles
        cursor = conn.execute('''
            SELECT title, year, publication_name 
            FROM articles 
            LIMIT 3
        ''')
        sample_articles = cursor.fetchall()
        
        conn.close()
        
        # Affichage des statistiques
        print("\n📈 STATISTIQUES FINALES:")
        print(f"  📚 Articles stockés: {total_articles}")
        print(f"  👥 Auteurs uniques: {total_authors}")
        print(f"  🔗 Relations créées: {total_relations}")
        
        if by_year:
            print("  📅 Articles par année:")
            for year, count in by_year:
                print(f"    {year}: {count} articles")
        
        print("\n📖 Échantillon d'articles:")
        for i, (title, year, journal) in enumerate(sample_articles, 1):
            print(f"  {i}. {title[:50]}...")
            print(f"     Année: {year}, Journal: {journal}")
        
        return {
            'total_articles': total_articles,
            'total_authors': total_authors,
            'total_relations': total_relations,
            'by_year': by_year
        }
    
    def process_complete_pipeline(self, json_file_path):
        """
        PIPELINE COMPLET : Exécute toutes les étapes de nettoyage et stockage
        """
        print("🚀 DÉBUT DU PIPELINE DE NETTOYAGE ET STOCKAGE")
        print("=" * 60)
        
        try:
            # ÉTAPE 1 : Chargement et nettoyage avec Pandas
            df = self.load_and_clean_data(json_file_path)
            
            # ÉTAPE 2 : Stockage des articles
            articles_count = self.store_articles(df)
            
            # ÉTAPE 3 : Stockage des auteurs et relations
            authors_count, relations_count = self.store_authors_and_relations(df)
            
            # ÉTAPE 4 : Génération des statistiques
            stats = self.generate_statistics()
            
            print(f"\n✅ PIPELINE TERMINÉ AVEC SUCCÈS!")
            print(f"📁 Base de données créée: {self.db_path}")
            print(f"🎓 Conforme aux spécifications du professeur")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERREUR DANS LE PIPELINE: {e}")
            return False

def main():
    """
    FONCTION PRINCIPALE : Point d'entrée du script
    """
    print("🎓 PROJET SCOPUS CHATBOT - ÉTAPE 2")
    print("Nettoyage et stockage des données")
    print("=" * 40)
    
    # Recherche automatique du fichier JSON
    import glob
    json_files = glob.glob('data/raw/*.json')
    
    if not json_files:
        print("❌ ERREUR: Aucun fichier JSON trouvé dans data/raw/")
        print("📋 Actions à faire:")
        print("  1. Vérifiez que l'étape 1 (extraction) a été exécutée")
        print("  2. Vérifiez que le fichier JSON existe dans data/raw/")
        return
    
    json_file = json_files[0]
    print(f"🎯 Fichier de données trouvé: {json_file}")
    
    # Exécution du pipeline
    processor = ScopusDataProcessor()
    success = processor.process_complete_pipeline(json_file)
    
    if success:
        print("\n🎉 ÉTAPE 2 TERMINÉE AVEC SUCCÈS!")
        print("🚀 Prêt pour l'étape 3 : Indexation sémantique")
    else:
        print("\n❌ ÉCHEC DE L'ÉTAPE 2")
        print("Consultez les messages d'erreur ci-dessus")

if __name__ == "__main__":
    main()
