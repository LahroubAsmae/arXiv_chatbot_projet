
import feedparser
import json
import pandas as pd
from datetime import datetime
import time
import os
from pathlib import Path
import urllib.parse
import requests


class MassiveArxivExtractor:
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.headers = {
            'User-Agent': 'MyArxivBot/0.1 (contact: lhroubasmae2018@gmail.com)'
        }
        self.all_articles = []

        # Création des dossiers
        Path('data/raw').mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(exist_ok=True)

        print("Extracteur ArXiv MASSIF initialisé")

   
    def search_articles_batch(self, query, start=0, max_results=50):
        """
        Recherche un batch d'articles via ArXiv API
        """
        # Encodage partiel : ne pas encoder :, ", ()
        query_encoded = urllib.parse.quote(query, safe=':"()')

        url = f"{self.base_url}?search_query={query_encoded}&start={start}&max_results={max_results}"
        print(f"Requête API ArXiv - URL: {url}")

        # Utilisation de requests pour inclure User-Agent
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            print(f"Erreur API ArXiv: {response.status_code}")
            return []

        feed = feedparser.parse(response.text)
        return feed.entries


    def extract_article_info(self, entry):
        """
        Extrait les informations d'un article ArXiv
        """
        try:
            return {
                'arxiv_id': entry.id.split('/')[-1],
                'title': entry.title,
                'authors': [author.name for author in entry.authors],
                'abstract': entry.summary,
                'published': entry.published,
                'pdf_url': next((l.href for l in entry.links if 'pdf' in l.href), None),
                'categories': [t['term'] for t in entry.tags] if hasattr(entry, 'tags') else []
            }
        except Exception as e:
            print(f"Erreur extraction article: {e}")
            return None

    def massive_extraction(self, queries, max_articles_per_query=100):
        """
        Extraction massive avec plusieurs requêtes
        """
        print("DÉBUT DE L'EXTRACTION MASSIVE")
        print("=" * 50)

        total_extracted = 0

        for i, query in enumerate(queries, 1):
            print(f"\n REQUÊTE {i}/{len(queries)}: {query}")
            print("-" * 40)

            extracted_for_query = 0
            start = 0

            while extracted_for_query < max_articles_per_query:
                remaining = max_articles_per_query - extracted_for_query
                count = min(50, remaining)  # ArXiv max = 50 par requête

                entries = self.search_articles_batch(query, start=start, max_results=count)

                if not entries:
                    print("Pas d'articles dans ce batch")
                    break

                # Traitement des articles
                for entry in entries:
                    article_info = self.extract_article_info(entry)
                    if article_info and article_info['title']:
                        self.all_articles.append(article_info)
                        extracted_for_query += 1
                        total_extracted += 1

                print(f" Batch traité: {len(entries)} articles (+{extracted_for_query} total)")

                time.sleep(5)  # Pause pour éviter surcharge
                start += count

                if extracted_for_query >= max_articles_per_query:
                    break

            print(f"Requête terminée: {extracted_for_query} articles extraits")

            if i < len(queries):
                print(" Pause de 2 secondes...")
                time.sleep(5)

        print(f"\n EXTRACTION TERMINÉE!")
        print(f"TOTAL: {total_extracted} articles extraits")

        return total_extracted

    def save_articles(self):
        """
        Sauvegarde tous les articles
        """
        if not self.all_articles:
            print("Aucun article à sauvegarder")
            return

        # Suppression des doublons basée sur arxiv_id
        seen_ids = set()
        unique_articles = []

        for article in self.all_articles:
            if article['arxiv_id'] not in seen_ids:
                seen_ids.add(article['arxiv_id'])
                unique_articles.append(article)

        duplicates_removed = len(self.all_articles) - len(unique_articles)
        if duplicates_removed > 0:
            print(f" {duplicates_removed} doublons supprimés")

        # Sauvegarde JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f'data/raw/arxiv_articles_massive_{timestamp}.json'

        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(unique_articles, f, indent=2, ensure_ascii=False)

        # Sauvegarde CSV
        csv_filename = f'data/raw/arxiv_articles_massive_{timestamp}.csv'
        df = pd.DataFrame(unique_articles)
        df.to_csv(csv_filename, index=False, encoding='utf-8')

        print(f" Articles sauvegardés:")
        print(f"   JSON: {json_filename}")
        print(f"  CSV: {csv_filename}")
        print(f"  Total unique: {len(unique_articles)} articles")

        return json_filename


def main():
    """
    Fonction principale pour l'extraction massive
    """
    print(" PROJET ARXIV CHATBOT - EXTRACTION MASSIVE")
    print("=" * 50)

    # Requêtes pour extraction massive (avec espaces possibles)
    queries = [
        # -- IA / ML / Deep Learning (déjà présents mais utiles)
        'ti:"artificial intelligence" OR abs:"artificial intelligence"',
        'ti:"machine learning" OR abs:"machine learning"',
        'ti:"deep learning" OR abs:"deep learning"',
        'ti:"neural networks" OR abs:"neural networks"',
        'ti:"computer vision" OR abs:"computer vision"',
        'ti:"natural language processing" OR abs:"NLP"',
        'ti:"transformer" OR abs:"transformer"',
        'ti:"large language model" OR abs:"LLM"',
        'ti:"reinforcement learning" OR abs:"reinforcement learning"',
        'ti:"speech recognition" OR abs:"speech recognition"',

        # -- Nouvelles sous-disciplines IA
        'ti:"graph neural networks" OR abs:"graph neural networks"',
        'ti:"generative adversarial networks" OR abs:"GAN"',
        'ti:"self-supervised learning" OR abs:"self-supervised learning"',
        'ti:"federated learning" OR abs:"federated learning"',
        'ti:"explainable AI" OR abs:"XAI"',
        'ti:"robotics" OR abs:"robotics"',
        'ti:"speech synthesis" OR abs:"speech synthesis"',
        'ti:"multimodal learning" OR abs:"multimodal learning"',
        'ti:"meta-learning" OR abs:"meta-learning"',
        'ti:"transfer learning" OR abs:"transfer learning"',

        # -- Domaines d’application
        'ti:"bioinformatics" OR abs:"bioinformatics"',
        'ti:"medical imaging" OR abs:"medical imaging"',
        'ti:"drug discovery" OR abs:"drug discovery"',
        'ti:"healthcare AI" OR abs:"healthcare AI"',
        'ti:"autonomous driving" OR abs:"autonomous driving"',
        'ti:"smart cities" OR abs:"smart cities"',
        'ti:"cybersecurity" OR abs:"cybersecurity"',
        'ti:"edge computing" OR abs:"edge computing"',
        'ti:"cloud computing" OR abs:"cloud computing"',
        'ti:"internet of things" OR abs:"IoT"',

        # -- Champs plus larges liés aux maths et data
        'ti:"data mining" OR abs:"data mining"',
        'ti:"big data" OR abs:"big data"',
        'ti:"optimization" OR abs:"optimization"',
        'ti:"statistical learning" OR abs:"statistical learning"',
        'ti:"pattern recognition" OR abs:"pattern recognition"',
        'ti:"knowledge graph" OR abs:"knowledge graph"',
        'ti:"semantic web" OR abs:"semantic web"',
        'ti:"information retrieval" OR abs:"information retrieval"',
    ]




    print(f" {len(queries)} requêtes préparées")
    print(f"Objectif: ~{len(queries) * 50} articles")

    # Extraction
    extractor = MassiveArxivExtractor()
    total_extracted = extractor.massive_extraction(queries, max_articles_per_query=500)

    if total_extracted > 0:
        json_file = extractor.save_articles()

        print(f"\n EXTRACTION MASSIVE TERMINÉE!")
        print(f"{total_extracted} articles extraits")
        print(f"Fichier créé: {json_file}")
        print(f"\n Prochaine étape: Relancez le nettoyage avec ces nouvelles données!")
        print(f"   python src/data_processor.py")
    else:
        print(f"\n Aucun article extrait")


if __name__ == "__main__":
    main()
