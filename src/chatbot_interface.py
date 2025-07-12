"""
ÉTAPE 4 : Interface Chatbot Scopus Professionnelle
Interface web pour interroger la base d'articles Scopus
"""
import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import plotly.express as px
from pathlib import Path

# Configuration CSS personnalisée
st.markdown("""
<style>
    .header-title {
        font-size: 28px;
        font-weight: 600;
        color: #1a3c6c;
        margin-bottom: 10px;
    }
    .header-subtitle {
        font-size: 16px;
        color: #4a6fa5;
        margin-bottom: 30px;
    }
    .section-title {
        font-size: 20px;
        font-weight: 600;
        color: #1a3c6c;
        margin: 25px 0 15px 0;
        border-bottom: 1px solid #e1e8ed;
        padding-bottom: 8px;
    }
    .metric-card {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e1e8ed;
    }
    .article-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        border: 1px solid #e1e8ed;
        transition: all 0.3s ease;
    }
    .article-card:hover {
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .search-box {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
        border: 1px solid #e1e8ed;
    }
    .result-highlight {
        background-color: #e6f2ff;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
        border-left: 4px solid #1a73e8;
    }
    .tabs-container {
        margin-top: 30px;
    }
    .stButton>button {
        background-color: #1a73e8;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 8px 16px;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #1557b0;
        color: white;
    }
    .clear-btn {
        background-color: #f1f3f4 !important;
        color: #5f6368 !important;
    }
    .clear-btn:hover {
        background-color: #e8eaed !important;
    }
</style>
""", unsafe_allow_html=True)

class ScopusChatbot:
    def __init__(self):
        self.db_path = 'data/processed/scopus_database.db'
        self.model_name = 'all-MiniLM-L6-v2'
        self.model = None
        self.faiss_index = None
        self.article_ids = []
        
        # Configuration de la page Streamlit
        st.set_page_config(
            page_title="Scopus Research Assistant",
            page_icon=":books:",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        self.setup_chatbot()
    
    @st.cache_resource
    def load_model(_self):
        """Charge le modèle Sentence Transformer (avec cache)"""
        return SentenceTransformer(_self.model_name)
    
    @st.cache_resource
    def load_faiss_index(_self):
        """Charge l'index FAISS (avec cache)"""
        try:
            faiss_path = 'data/indexes/scopus_faiss.index'
            metadata_path = 'data/indexes/faiss_metadata.pkl'
            
            if Path(faiss_path).exists() and Path(metadata_path).exists():
                index = faiss.read_index(faiss_path)
                with open(metadata_path, 'rb') as f:
                    metadata = pickle.load(f)
                return index, metadata['article_ids']
            else:
                return None, []
        except Exception as e:
            st.error(f"Erreur lors du chargement de l'index FAISS: {e}")
            return None, []
    
    @st.cache_data
    def load_articles_data(_self):
        """Charge les données des articles (avec cache)"""
        try:
            conn = sqlite3.connect(_self.db_path)
            query = '''
                SELECT 
                    a.id,
                    a.scopus_id,
                    a.title,
                    a.abstract,
                    a.keywords,
                    a.subject_areas,
                    a.year,
                    a.publication_name,
                    a.doi,
                    a.citation_count
                FROM articles a
                ORDER BY a.year DESC, a.title
            '''
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erreur lors du chargement des articles: {e}")
            return pd.DataFrame()
    
    def setup_chatbot(self):
        """Initialise le chatbot"""
        with st.spinner("Initialisation du système..."):
            self.model = self.load_model()
            self.faiss_index, self.article_ids = self.load_faiss_index()
            self.articles_df = self.load_articles_data()
        
        if self.faiss_index is None:
            st.error("Index FAISS non trouvé. Veuillez exécuter l'étape d'indexation sémantique.")
            st.stop()
    
    def semantic_search(self, query, k=5):
        """Effectue une recherche sémantique"""
        if not query.strip():
            return []
        
        try:
            # Vectorisation de la requête
            query_embedding = self.model.encode([query]).astype('float32')
            faiss.normalize_L2(query_embedding)
            
            # Recherche dans l'index FAISS
            scores, indices = self.faiss_index.search(query_embedding, k=k)
            
            # Récupération des résultats
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.article_ids):
                    article_id = self.article_ids[idx]
                    article_row = self.articles_df[self.articles_df['id'] == article_id]
                    if not article_row.empty:
                        article = article_row.iloc[0]
                        results.append({
                            'score': float(score),
                            'article': article.to_dict()
                        })
            
            return results
        except Exception as e:
            st.error(f"Erreur lors de la recherche: {e}")
            return []
    
    def generate_answer(self, query, search_results):
        """Génère une réponse basée sur les résultats de recherche"""
        if not search_results:
            return "Aucun résultat trouvé pour votre requête."
        
        # Construction de la réponse
        answer_parts = []
        
        answer_parts.append(f"**Votre recherche :** \"{query}\"")
        answer_parts.append(f"**Articles pertinents :** {len(search_results)} résultats trouvés")
        
        top_result = search_results[0]
        answer_parts.append(f"\n**Article le plus pertinent :**")
        answer_parts.append(f"- **Titre :** {top_result['article']['title']}")
        answer_parts.append(f"- **Année :** {top_result['article']['year']}")
        answer_parts.append(f"- **Journal :** {top_result['article']['publication_name']}")
        answer_parts.append(f"- **Score de pertinence :** {top_result['score']:.3f}")
        
        # Analyse des tendances
        years = [r['article']['year'] for r in search_results if r['article']['year']]
        if years:
            avg_year = sum(years) / len(years)
            answer_parts.append(f"\n**Analyse des résultats :**")
            answer_parts.append(f"- Année moyenne : {avg_year:.0f}")
            answer_parts.append(f"- Score moyen : {np.mean([r['score'] for r in search_results]):.3f}")
        
        return "\n".join(answer_parts)
    
    def display_article_card(self, article, score=None):
        """Affiche une carte d'article professionnelle"""
        with st.container():
            st.markdown(f'<div class="article-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Titre avec lien DOI si disponible
                if article.get('doi'):
                    st.markdown(f"<h4>{article['title']}</h4>", unsafe_allow_html=True)
                    st.markdown(f"[Accéder à l'article](https://doi.org/{article['doi']})", unsafe_allow_html=True)
                else:
                    st.markdown(f"<h4>{article['title']}</h4>", unsafe_allow_html=True)
                
                # Informations de base
                if article.get('publication_name'):
                    st.markdown(f"**Journal:** {article['publication_name']}")
                
                if article.get('year'):
                    st.markdown(f"**Année:** {article['year']}")
                
                if article.get('keywords'):
                    st.markdown(f"**Mots-clés:** {article['keywords']}")
                
                # Résumé (si disponible)
                if article.get('abstract'):
                    with st.expander("Voir le résumé"):
                        st.write(article['abstract'])
            
            with col2:
                # Metrics
                st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
                
                if article.get('citation_count'):
                    st.markdown(f"**Citations:** {article['citation_count']}")
                else:
                    st.markdown(f"**Citations:** 0")
                
                if score is not None:
                    st.markdown(f"**Score:** {score:.3f}")
                
                if article.get('scopus_id'):
                    st.markdown(f"**ID Scopus:** {article['scopus_id']}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def create_visualizations(self):
        """Crée les visualisations des données"""
        if self.articles_df.empty:
            return
        
        st.markdown('<div class="section-title">Analyse du corpus</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution par année
            year_counts = self.articles_df['year'].value_counts().sort_index()
            fig_years = px.bar(
                x=year_counts.index, 
                y=year_counts.values,
                title="Distribution par année",
                labels={'x': 'Année', 'y': 'Nombre d\'articles'}
            )
            fig_years.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_years, use_container_width=True)
        
        with col2:
            # Distribution des citations
            fig_citations = px.histogram(
                self.articles_df, 
                x='citation_count',
                title="Distribution des citations",
                labels={'citation_count': 'Nombre de citations', 'count': 'Nombre d\'articles'},
                nbins=20
            )
            fig_citations.update_layout(plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_citations, use_container_width=True)
        
        # Top journaux
        if 'publication_name' in self.articles_df.columns:
            journal_counts = self.articles_df['publication_name'].value_counts().head(5)
            if not journal_counts.empty:
                fig_journals = px.pie(
                    values=journal_counts.values,
                    names=journal_counts.index,
                    title="Top 5 des journaux"
                )
                st.plotly_chart(fig_journals, use_container_width=True)
    
    def run_interface(self):
        """Lance l'interface principale"""
        # En-tête
        st.markdown('<div class="header-title">Scopus Research Assistant</div>', unsafe_allow_html=True)
        st.markdown('<div class="header-subtitle">Interrogez intelligemment votre corpus d\'articles scientifiques</div>', unsafe_allow_html=True)
        
        # Sidebar avec statistiques
        with st.sidebar:
            st.markdown('<div class="section-title">Statistiques du corpus</div>', unsafe_allow_html=True)
            
            if not self.articles_df.empty:
                st.markdown(f'<div class="metric-card"><b>Articles indexés</b><br>{len(self.articles_df)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-card"><b>Années couvertes</b><br>{self.articles_df["year"].min():.0f} - {self.articles_df["year"].max():.0f}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-card"><b>Citations totales</b><br>{self.articles_df["citation_count"].sum()}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-card"><b>Vecteurs indexés</b><br>{len(self.article_ids)}</div>', unsafe_allow_html=True)
            
            st.divider()
            
            # Exemples de questions
            st.markdown('<div class="section-title">Exemples de requêtes</div>', unsafe_allow_html=True)
            example_queries = [
                "Recherche sur l'IA médicale",
                "Applications du machine learning",
                "Études récentes en endoscopie",
                "Développements en intelligence artificielle",
                "Articles sur les réseaux de neurones"
            ]
            
            for query in example_queries:
                if st.button(query, key=f"example_{query}"):
                    st.session_state.query_input = query
        
        # Section de recherche
        st.markdown('<div class="section-title">Recherche scientifique</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="search-box">', unsafe_allow_html=True)
            
            # Zone de saisie
            query = st.text_input(
                "Tapez votre question ici :",
                placeholder="Ex: Quels sont les articles sur l'intelligence artificielle en médecine ?",
                key="query_input",
                label_visibility="collapsed"
            )
            
            # Boutons
            col1, col2, _ = st.columns([1, 1, 8])
            with col1:
                search_button = st.button("Rechercher", type="primary")
            with col2:
                clear_button = st.button("Effacer", key="clear_btn")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        if clear_button:
            st.session_state.query_input = ""
            st.rerun()
        
        # Traitement de la recherche
        if search_button and query:
            with st.spinner("Analyse en cours..."):
                # Recherche sémantique
                results = self.semantic_search(query, k=5)
                
                if results:
                    # Génération de la réponse
                    answer = self.generate_answer(query, results)
                    
                    # Affichage de la réponse
                    st.markdown('<div class="section-title">Résultats de recherche</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="result-highlight">{answer}</div>', unsafe_allow_html=True)
                    
                    # Affichage des articles trouvés
                    st.markdown('<div class="section-title">Articles pertinents</div>', unsafe_allow_html=True)
                    
                    for i, result in enumerate(results, 1):
                        st.markdown(f"#### Résultat {i}")
                        self.display_article_card(result['article'], result['score'])
                else:
                    st.warning("Aucun résultat trouvé. Veuillez reformuler votre requête.")
        
        # Onglets pour fonctionnalités supplémentaires
        st.markdown('<div class="tabs-container">', unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["Analyse du corpus", "Base documentaire", "À propos"])
        
        with tab1:
            self.create_visualizations()
        
        with tab2:
            st.markdown('<div class="section-title">Base documentaire complète</div>', unsafe_allow_html=True)
            if not self.articles_df.empty:
                # Filtres
                col1, col2 = st.columns(2)
                with col1:
                    year_filter = st.selectbox(
                        "Filtrer par année :",
                        ["Toutes"] + sorted(self.articles_df['year'].dropna().unique().tolist(), reverse=True)
                    )
                with col2:
                    sort_by = st.selectbox(
                        "Trier par :",
                        ["Année (récent)", "Année (ancien)", "Citations", "Titre"]
                    )
                
                # Application des filtres
                filtered_df = self.articles_df.copy()
                if year_filter != "Toutes":
                    filtered_df = filtered_df[filtered_df['year'] == year_filter]
                
                # Tri
                if sort_by == "Année (récent)":
                    filtered_df = filtered_df.sort_values('year', ascending=False)
                elif sort_by == "Année (ancien)":
                    filtered_df = filtered_df.sort_values('year', ascending=True)
                elif sort_by == "Citations":
                    filtered_df = filtered_df.sort_values('citation_count', ascending=False)
                elif sort_by == "Titre":
                    filtered_df = filtered_df.sort_values('title')
                
                # Affichage
                for _, article in filtered_df.iterrows():
                    self.display_article_card(article.to_dict())
        
        with tab3:
            st.markdown('<div class="section-title">À propos du système</div>', unsafe_allow_html=True)
            st.markdown("""
            **Scopus Research Assistant** est une plateforme d'analyse scientifique permettant d'explorer et d'interroger un corpus de publications académiques.
            
            #### Fonctionnalités principales
            - Recherche sémantique avancée
            - Analyse bibliométrique
            - Exploration thématique
            - Visualisation des tendances de recherche
            
            #### Technologies utilisées
            - **Moteur de recherche**: FAISS (Facebook AI Similarity Search)
            - **Modèle sémantique**: all-MiniLM-L6-v2
            - **Base de données**: SQLite
            - **Interface**: Streamlit
            
            #### Caractéristiques du corpus
            - **Articles indexés**: 10 publications
            - **Période couverte**: 2026
            - **Domaines**: Intelligence Artificielle, Machine Learning, Informatique Médicale
            
            Ce système a été développé à des fins de recherche et démonstration.
            """)
            
            st.divider()
            st.markdown("© 2023 Scopus Research Assistant | Tous droits réservés")
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Fonction principale"""
    try:
        chatbot = ScopusChatbot()
        chatbot.run_interface()
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation: {e}")
        st.info("Veuillez vérifier la configuration du système.")

if __name__ == "__main__":
    main()