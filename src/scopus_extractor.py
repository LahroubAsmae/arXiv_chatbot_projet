"""
Extracteur Scopus MASSIF - Version pour récupérer beaucoup d'articles
Optimisé pour récupérer 100-500 articles en une fois
"""
import requests
import json
import pandas as pd
from datetime import datetime
import time
import os
from pathlib import Path

class MassiveScopusExtractor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.elsevier.com/content/search/scopus"
        self.headers = {
            'X-ELS-APIKey': api_key,
            'Accept': 'application/json'
        }
        self.all_articles = []
        
        # Création des dossiers
        Path('data/raw').mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
        
        print("🚀 Extracteur Scopus MASSIF initialisé")
    
    def search_articles_batch(self, query, start=0, count=25):
        """
        Recherche un batch d'articles
        """
        params = {
            'query': query,
            'start': start,
            'count': count,
            'field': 'dc:identifier,dc:title,dc:creator,prism:publicationName,prism:coverDate,prism:doi,authkeywords,dc:description,citedby-count,prism:aggregationType,subtype,subtypeDescription,source-id,prism:issn'
        }
        
        try:
            print(f"📡 Requête API - Start: {start}, Count: {count}")
            response = requests.get(self.base_url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"❌ Erreur API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de la requête: {e}")
            return None
    
    def extract_article_info(self, entry):
        """
        Extrait les informations d'un article
        """
        try:
            # ID Scopus
            scopus_id = entry.get('dc:identifier', '').replace('SCOPUS_ID:', '')
            
            # Titre
            title = entry.get('dc:title', '')
            
            # Auteurs
            authors = entry.get('dc:creator', '')
            
            # Journal
            publication_name = entry.get('prism:publicationName', '')
            
            # Date
            cover_date = entry.get('prism:coverDate', '')
            
            # DOI
            doi = entry.get('prism:doi', '')
            
            # Mots-clés
            keywords = entry.get('authkeywords', '')
            
            # Résumé (description)
            abstract = entry.get('dc:description', '')
            
            # Citations
            citation_count = entry.get('citedby-count', '0')
            
            # Type de document
            subtype = entry.get('subtypeDescription', '')
            
            # Domaines (approximation)
            subject_areas = subtype
            
            return {
                'scopus_id': scopus_id,
                'title': title,
                'authors': authors,
                'publication_name': publication_name,
                'cover_date': cover_date,
                'doi': doi,
                'keywords': keywords,
                'abstract': abstract,
                'citation_count': citation_count,
                'subject_areas': subject_areas,
                'document_type': subtype
            }
            
        except Exception as e:
            print(f"⚠️ Erreur extraction article: {e}")
            return None
    
    def massive_extraction(self, queries, max_articles_per_query=100):
        """
        Extraction massive avec plusieurs requêtes
        """
        print("🎯 DÉBUT DE L'EXTRACTION MASSIVE")
        print("=" * 50)
        
        total_extracted = 0
        
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 REQUÊTE {i}/{len(queries)}: {query}")
            print("-" * 40)
            
            # Première requête pour connaître le total
            initial_data = self.search_articles_batch(query, start=0, count=25)
            
            if not initial_data or 'search-results' not in initial_data:
                print(f"❌ Pas de résultats pour: {query}")
                continue
            
            total_results = int(initial_data['search-results'].get('opensearch:totalResults', 0))
            print(f"📊 {total_results} articles trouvés pour cette requête")
            
            # Limiter le nombre d'articles par requête
            max_to_extract = min(total_results, max_articles_per_query)
            print(f"🎯 Extraction de {max_to_extract} articles")
            
            # Extraction par batches de 25
            extracted_for_query = 0
            start = 0
            
            while extracted_for_query < max_to_extract:
                # Calcul du nombre d'articles à récupérer dans ce batch
                remaining = max_to_extract - extracted_for_query
                count = min(25, remaining)
                
                # Requête API
                data = self.search_articles_batch(query, start=start, count=count)
                
                if not data or 'search-results' not in data:
                    print(f"❌ Erreur lors du batch start={start}")
                    break
                
                entries = data['search-results'].get('entry', [])
                
                if not entries:
                    print(f"ℹ️ Pas d'articles dans ce batch")
                    break
                
                # Traitement des articles
                for entry in entries:
                    article_info = self.extract_article_info(entry)
                    if article_info and article_info['title']:
                        self.all_articles.append(article_info)
                        extracted_for_query += 1
                        total_extracted += 1
                
                print(f"  ✅ Batch traité: {len(entries)} articles (+{extracted_for_query} total)")
                
                # Pause pour respecter les limites de l'API
                time.sleep(1)
                start += count
            
            print(f"✅ Requête terminée: {extracted_for_query} articles extraits")
            
            # Pause entre les requêtes
            if i < len(queries):
                print("⏳ Pause de 2 secondes...")
                time.sleep(2)
        
        print(f"\n🎉 EXTRACTION TERMINÉE!")
        print(f"📊 TOTAL: {total_extracted} articles extraits")
        
        return total_extracted
    
    def save_articles(self):
        """
        Sauvegarde tous les articles
        """
        if not self.all_articles:
            print("❌ Aucun article à sauvegarder")
            return
        
        # Suppression des doublons basée sur scopus_id
        seen_ids = set()
        unique_articles = []
        
        for article in self.all_articles:
            if article['scopus_id'] not in seen_ids:
                seen_ids.add(article['scopus_id'])
                unique_articles.append(article)
        
        duplicates_removed = len(self.all_articles) - len(unique_articles)
        if duplicates_removed > 0:
            print(f"🗑️ {duplicates_removed} doublons supprimés")
        
        # Sauvegarde JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f'data/raw/scopus_articles_massive_{timestamp}.json'
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(unique_articles, f, indent=2, ensure_ascii=False)
        
        # Sauvegarde CSV
        csv_filename = f'data/raw/scopus_articles_massive_{timestamp}.csv'
        df = pd.DataFrame(unique_articles)
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        
        print(f"💾 Articles sauvegardés:")
        print(f"  📄 JSON: {json_filename}")
        print(f"  📊 CSV: {csv_filename}")
        print(f"  📈 Total unique: {len(unique_articles)} articles")
        
        # Statistiques
        self.show_statistics(unique_articles)
        
        return json_filename
    
    def show_statistics(self, articles):
        """
        Affiche des statistiques sur les articles extraits
        """
        print(f"\n📊 STATISTIQUES D'EXTRACTION:")
        print("=" * 30)
        
        df = pd.DataFrame(articles)
        
        # Articles par année
        if 'cover_date' in df.columns:
            df['year'] = pd.to_datetime(df['cover_date'], errors='coerce').dt.year
            year_counts = df['year'].value_counts().sort_index().tail(10)
            print(f"📅 Articles par année (top 10):")
            for year, count in year_counts.items():
                if pd.notna(year):
                    print(f"  {int(year)}: {count} articles")
        
        # Top journaux
        if 'publication_name' in df.columns:
            journal_counts = df['publication_name'].value_counts().head(5)
            print(f"\n📰 Top 5 journaux:")
            for journal, count in journal_counts.items():
                print(f"  • {journal[:50]}... ({count})")
        
        # Citations
        if 'citation_count' in df.columns:
            df['citations'] = pd.to_numeric(df['citation_count'], errors='coerce')
            avg_citations = df['citations'].mean()
            max_citations = df['citations'].max()
            print(f"\n📈 Citations:")
            print(f"  Moyenne: {avg_citations:.1f}")
            print(f"  Maximum: {int(max_citations) if pd.notna(max_citations) else 0}")

def main():
    """
    Fonction principale pour l'extraction massive
    """
    print("🎓 PROJET SCOPUS CHATBOT - EXTRACTION MASSIVE")
    print("=" * 50)
    
    # Clé API (remplacez par la vôtre)
    API_KEY = "7f59af901d2d86f78a1fd60c1bf9426a"
    
    # Requêtes pour extraction massive
    queries = [
        # IA et Machine Learning
        "TITLE-ABS-KEY(artificial intelligence) AND PUBYEAR > 2020",
        "TITLE-ABS-KEY(machine learning) AND PUBYEAR > 2020",
        "TITLE-ABS-KEY(deep learning) AND PUBYEAR > 2020",
        "TITLE-ABS-KEY(neural networks) AND PUBYEAR > 2020",
        
        # Domaines d'application
        "TITLE-ABS-KEY(artificial intelligence AND medicine) AND PUBYEAR > 2020",
        "TITLE-ABS-KEY(machine learning AND materials) AND PUBYEAR > 2020",
        "TITLE-ABS-KEY(AI AND healthcare) AND PUBYEAR > 2020",
        "TITLE-ABS-KEY(computer vision) AND PUBYEAR > 2020",
        
        # Technologies émergentes
        "TITLE-ABS-KEY(transformer AND attention) AND PUBYEAR > 2021",
        "TITLE-ABS-KEY(large language model) AND PUBYEAR > 2021",
    ]
    
    print(f"🎯 {len(queries)} requêtes préparées")
    print(f"📊 Objectif: ~{len(queries) * 50} articles")
    
    # Extraction
    extractor = MassiveScopusExtractor(API_KEY)
    total_extracted = extractor.massive_extraction(queries, max_articles_per_query=50)
    
    if total_extracted > 0:
        json_file = extractor.save_articles()
        
        print(f"\n🎉 EXTRACTION MASSIVE TERMINÉE!")
        print(f"📊 {total_extracted} articles extraits")
        print(f"📁 Fichier créé: {json_file}")
        print(f"\n🚀 Prochaine étape: Relancez le nettoyage avec ces nouvelles données!")
        print(f"   python src/data_processor.py")
    else:
        print(f"\n❌ Aucun article extrait")

if __name__ == "__main__":
    main()
