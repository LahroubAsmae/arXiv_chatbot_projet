"""
Validation de l'étape 2 - Vérification que tout est conforme
"""
import sqlite3
import pandas as pd
from pathlib import Path

def validate_database():
    """Valide que la base respecte les spécifications du prof"""
    print("🔍 VALIDATION DE L'ÉTAPE 2")
    print("=" * 30)
    
    db_path = 'data/processed/scopus_database.db'
    
    # Vérification de l'existence du fichier
    if not Path(db_path).exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        print("Exécutez d'abord: python src/data_processor.py")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 1. Vérification des tables requises par le prof
        print("📋 Vérification des tables:")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['articles', 'authors', 'affiliations', 'article_authors']
        
        for table in required_tables:
            if table in tables:
                print(f"  ✅ Table '{table}' présente")
            else:
                print(f"  ❌ Table '{table}' manquante")
        
        # 2. Vérification des données articles
        print(f"\n📚 Vérification des articles:")
        cursor = conn.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        print(f"  📊 Total articles: {article_count}")
        
        # Vérification des champs requis par le prof
        cursor = conn.execute("PRAGMA table_info(articles)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_fields = ['title', 'abstract', 'cover_date', 'publication_name', 'doi', 'scopus_id', 'keywords', 'subject_areas']
        
        print("  🔍 Champs requis par le professeur:")
        all_fields_present = True
        for field in required_fields:
            if field in columns:
                print(f"    ✅ {field}")
            else:
                print(f"    ❌ {field} MANQUANT")
                all_fields_present = False
        
        # 3. Vérification de la qualité des données
        print(f"\n🧹 Vérification du nettoyage:")
        
        # Articles avec titre non vide
        cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE title != '' AND title IS NOT NULL")
        articles_with_title = cursor.fetchone()[0]
        print(f"  📝 Articles avec titre: {articles_with_title}/{article_count}")
        
        # Articles avec année extraite
        cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE year IS NOT NULL")
        articles_with_year = cursor.fetchone()[0]
        print(f"  📅 Articles avec année: {articles_with_year}/{article_count}")
        
        # 4. Vérification des auteurs et relations
        print(f"\n👥 Vérification des auteurs:")
        cursor = conn.execute("SELECT COUNT(*) FROM authors")
        author_count = cursor.fetchone()[0]
        print(f"  👤 Auteurs uniques: {author_count}")
        
        cursor = conn.execute("SELECT COUNT(*) FROM article_authors")
        relations_count = cursor.fetchone()[0]
        print(f"  🔗 Relations article-auteur: {relations_count}")
        
        # 5. Échantillon de données pour vérification manuelle
        print(f"\n📖 Échantillon de données:")
        df = pd.read_sql_query('''
            SELECT a.title, a.year, a.publication_name, au.preferred_name as author
            FROM articles a
            LEFT JOIN article_authors aa ON a.id = aa.article_id
            LEFT JOIN authors au ON aa.author_id = au.id
            LIMIT 5
        ''', conn)
        
        for _, row in df.iterrows():
            print(f"  • {row['title'][:40]}...")
            print(f"    Auteur: {row['author']}, Année: {row['year']}")
            print(f"    Journal: {row['publication_name']}")
        
        conn.close()
        
        # 6. Résumé de validation
        print(f"\n📊 RÉSUMÉ DE VALIDATION:")
        print(f"  📚 Articles traités: {article_count}")
        print(f"  👥 Auteurs identifiés: {author_count}")
        print(f"  🔗 Relations créées: {relations_count}")
        
        if all_fields_present and article_count > 0:
            print(f"\n✅ VALIDATION RÉUSSIE!")
            print(f"🎓 Base conforme aux spécifications du professeur")
            print(f"🚀 Prêt pour l'étape 3 (Indexation sémantique)")
            return True
        else:
            print(f"\n⚠️ VALIDATION PARTIELLE")
            print(f"Certains éléments nécessitent attention")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la validation: {e}")
        return False

def show_database_content():
    """Affiche le contenu détaillé de la base pour vérification"""
    print(f"\n🔍 CONTENU DÉTAILLÉ DE LA BASE:")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect('data/processed/scopus_database.db')
        
        # Tous les articles
        print("📚 TOUS LES ARTICLES:")
        df_articles = pd.read_sql_query('''
            SELECT scopus_id, title, year, publication_name
            FROM articles
            ORDER BY year DESC, title
        ''', conn)
        
        for i, row in df_articles.iterrows():
            print(f"  {i+1}. {row['title']}")
            print(f"     ID: {row['scopus_id']}, Année: {row['year']}")
            print(f"     Journal: {row['publication_name']}")
            print()
        
        # Tous les auteurs
        print("👥 TOUS LES AUTEURS:")
        df_authors = pd.read_sql_query('''
            SELECT preferred_name, COUNT(*) as article_count
            FROM authors a
            JOIN article_authors aa ON a.id = aa.author_id
            GROUP BY a.id, preferred_name
            ORDER BY article_count DESC
        ''', conn)
        
        for _, row in df_authors.iterrows():
            print(f"  • {row['preferred_name']} ({row['article_count']} article(s))")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    # Validation principale
    success = validate_database()
    
    # Affichage détaillé si demandé
    if success:
        show_detail = input("\n❓ Voulez-vous voir le contenu détaillé ? (o/n): ")
        if show_detail.lower() == 'o':
            show_database_content()
