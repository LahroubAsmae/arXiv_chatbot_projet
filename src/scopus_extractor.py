import requests
import pandas as pd
import json
import time
from datetime import datetime
from tqdm import tqdm
import logging
from typing import List, Dict, Optional
import sys
import os

# Supprimer le module du cache pour forcer le rechargement
if 'config.api_config' in sys.modules:
    del sys.modules['config.api_config']

# Ajouter le dossier parent au path pour importer config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_config import ScopusConfig

class ScopusExtractor:
    def __init__(self):
        # Valider la configuration
        ScopusConfig.validate_config()
        
        self.config = ScopusConfig()
        self.session = requests.Session()
        self.session.headers.update(self.config.HEADERS)
        
        # Configuration du logging
        self.setup_logging()
        
        # DEBUG: Afficher les champs utilisés
        self.logger.info(f"🔍 Champs utilisés: {self.config.SEARCH_FIELDS}")
        
        # Statistiques
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
    
    def setup_logging(self):
        """Configure le système de logging"""
        import os
        
        # Obtenir le chemin du dossier racine du projet
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(project_root, 'logs')
        
        # Créer le dossier logs s'il n'existe pas
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'extraction.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def search_articles(self, query: str, count: int = 25, start: int = 0) -> Dict:
        """
        Recherche d'articles via l'API Scopus
        """
        params = {
            'query': query,
            'count': min(count, self.config.MAX_RESULTS_PER_REQUEST),
            'start': start,
            'field': ','.join(self.config.SEARCH_FIELDS)
        }
        
        try:
            self.total_requests += 1
            response = self.session.get(self.config.SEARCH_URL, params=params)
            
            # Gestion du rate limiting
            if response.status_code == 429:
                self.logger.warning("Rate limit atteint, pause de 60 secondes...")
                time.sleep(60)
                response = self.session.get(self.config.SEARCH_URL, params=params)
            
            response.raise_for_status()
            self.successful_requests += 1
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.failed_requests += 1
            self.logger.error(f"Erreur lors de la requête: {e}")
            return {}
    
    def extract_all_results(self, query: str, max_results: int = 5000) -> List[Dict]:
        """
        Extrait tous les résultats pour une requête donnée
        """
        self.logger.info(f"Début extraction pour: {query}")
        
        # Première requête pour connaître le nombre total
        first_result = self.search_articles(query, count=1)
        
        if 'search-results' not in first_result:
            self.logger.error("Pas de résultats trouvés")
            return []
        
        total_results = int(first_result['search-results'].get('opensearch:totalResults', 0))
        self.logger.info(f"Total d'articles disponibles: {total_results}")
        
        # Limiter au maximum demandé
        results_to_extract = min(total_results, max_results)
        self.logger.info(f"Articles à extraire: {results_to_extract}")
        
        all_articles = []
        batch_size = self.config.MAX_RESULTS_PER_REQUEST
        
        # Barre de progression
        with tqdm(total=results_to_extract, desc="Extraction") as pbar:
            for start in range(0, results_to_extract, batch_size):
                current_batch_size = min(batch_size, results_to_extract - start)
                
                # Requête pour ce batch
                batch_result = self.search_articles(query, current_batch_size, start)
                
                if 'search-results' in batch_result:
                    entries = batch_result['search-results'].get('entry', [])
                    articles = self.process_articles(entries)
                    all_articles.extend(articles)
                    
                    pbar.update(len(articles))
                    self.logger.info(f"Traité {start + len(articles)}/{results_to_extract} articles")
                
                # Pause pour respecter le rate limiting
                time.sleep(1.0 / self.config.MAX_REQUESTS_PER_SECOND)
        
        self.logger.info(f"Extraction terminée: {len(all_articles)} articles récupérés")
        return all_articles
    
    def process_articles(self, entries: List[Dict]) -> List[Dict]:
        """
        Traite les entrées brutes de l'API - Version corrigée
        """
        processed_articles = []
        
        for entry in entries:
            # Debug: afficher les champs disponibles pour le premier article
            if len(processed_articles) == 0:
                self.logger.info(f"🔍 Champs disponibles dans l'API: {list(entry.keys())}")
            
            article = {
                'scopus_id': self.safe_get(entry, 'dc:identifier', '').replace('SCOPUS_ID:', ''),
                'title': self.safe_get(entry, 'dc:title', ''),
                'publication_name': self.safe_get(entry, 'prism:publicationName', ''),
                'cover_date': self.safe_get(entry, 'prism:coverDate', ''),
                'doi': self.safe_get(entry, 'prism:doi', ''),
                'citation_count': int(self.safe_get(entry, 'citedby-count', 0)),
                'authors': self.safe_get(entry, 'dc:creator', ''),
                'extraction_date': datetime.now().isoformat(),
                # Champs qui seront vides avec la configuration actuelle
                'abstract': '',  # dc:description pas dans SEARCH_FIELDS
                'keywords': '',  # authkeywords pas dans SEARCH_FIELDS
                'subject_areas': ''  # subject-area pas dans SEARCH_FIELDS
            }
            processed_articles.append(article)
        
        return processed_articles
    
    def safe_get(self, dictionary: Dict, key: str, default=''):
        """Récupération sécurisée des valeurs"""
        return dictionary.get(key, default) if dictionary else default
    
    def save_data(self, articles: List[Dict], filename: str):
        """Sauvegarde les données"""
        if not articles:
            self.logger.warning("Aucun article à sauvegarder")
            return
        
        # Obtenir le chemin du dossier racine du projet
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, 'data', 'raw')
        
        # Créer le dossier data/raw s'il n'existe pas
        os.makedirs(data_dir, exist_ok=True)
        
        # Sauvegarde JSON
        json_file = os.path.join(data_dir, f"{filename}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        # Sauvegarde CSV (version aplatie)
        csv_file = os.path.join(data_dir, f"{filename}.csv")
        df = self.articles_to_dataframe(articles)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        self.logger.info(f"Données sauvegardées: {json_file} et {csv_file}")
    
    def articles_to_dataframe(self, articles: List[Dict]) -> pd.DataFrame:
        """Convertit les articles en DataFrame"""
        # Conversion directe - tous les champs sont maintenant des chaînes simples
        return pd.DataFrame(articles)
    
    def get_statistics(self):
        """Retourne les statistiques d'extraction"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        }

# Script de test
if __name__ == "__main__":
    print("🚀 Démarrage de l'extracteur Scopus...")
    
    try:
        extractor = ScopusExtractor()
        
        # Test avec une petite requête
        test_query = "TITLE-ABS-KEY(artificial intelligence)"
        print(f"📝 Requête de test: {test_query}")
        
        articles = extractor.extract_all_results(test_query, max_results=10)
        
        if articles:
            extractor.save_data(articles, "test_extraction")
            print(f"✅ Test réussi: {len(articles)} articles extraits")
            print("📊 Statistiques:", extractor.get_statistics())
            
            # Afficher un exemple d'article
            if len(articles) > 0:
                print("\n📄 Exemple d'article extrait:")
                example = articles[0]
                for key, value in example.items():
                    if value:  # Afficher seulement les champs non vides
                        print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
        else:
            print("❌ Aucun article extrait")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()