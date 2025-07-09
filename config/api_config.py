import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class ScopusConfig:
    API_KEY = os.getenv('SCOPUS_API_KEY')
    BASE_URL = os.getenv('SCOPUS_BASE_URL', 'https://api.elsevier.com/content')
    
    # Endpoints
    SEARCH_URL = f"{BASE_URL}/search/scopus"
    ABSTRACT_URL = f"{BASE_URL}/abstract/scopus_id"
    AUTHOR_URL = f"{BASE_URL}/author/author_id"
    
    # Limites API
    MAX_REQUESTS_PER_SECOND = int(os.getenv('MAX_REQUESTS_PER_SECOND', 9))
    MAX_RESULTS_PER_REQUEST = int(os.getenv('MAX_RESULTS_PER_REQUEST', 200))
    
    # Headers HTTP
    HEADERS = {
        'X-ELS-APIKey': API_KEY,
        'Accept': 'application/json',
        'User-Agent': 'ScopusChatbot/1.0'
    }
    
    # Champs à extraire (SEULEMENT les champs valides testés)
    SEARCH_FIELDS = [
        'dc:identifier',
        'dc:title', 
        'dc:creator',
        'prism:publicationName',
        'prism:coverDate',
        'prism:doi',
        'citedby-count'
    ]
    
    @classmethod
    def validate_config(cls):
        """Valide la configuration"""
        if not cls.API_KEY:
            raise ValueError("SCOPUS_API_KEY non définie dans le fichier .env")
        return True