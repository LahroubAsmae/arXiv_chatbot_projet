"""
ÉTAPE 4 : Interface Chatbot Streamlit
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
import plotly.graph_objects as go
from pathlib import Path
import json
from datetime import datetime

class ScopusChatbot:
    def __init__(self):
        self.db_path = 'data/processed/scopus_database.db'
        self.model_name = 'all-MiniLM-L6-v2'
        self.model = None
        self.faiss_index = None
        self.article_ids = []
        
        # Configuration de la page Streamlit
        st.set_page_config(
            page_title="🔬 Scopus Research Chatbot",
            page_icon="🔬",
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
        with st.spinner("🔧 Initialisation du chatbot..."):
            self.model = self.load_model()
            self.faiss_index, self.article_ids = self.load_faiss_index()
            self.articles_df = self.load_articles_data()
        
        if self.faiss_index is None:
            st.error("❌ Index FAISS non trouvé. Exécutez d'abord l'étape 3 (indexation sémantique)")
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
            return "❌ Aucun article pertinent trouvé pour votre question."
        
        # Analyse de la requête pour personnaliser la réponse
        query_lower = query.lower()
        
        # Construction de la réponse
        answer_parts = []
        
        # Introduction contextuelle
        if any(word in query_lower for word in ['artificial intelligence', 'ai', 'intelligence artificielle']):
            answer_parts.append("🤖 **Concernant l'Intelligence Artificielle dans votre corpus :**")
        elif any(word in query_lower for word in ['machine learning', 'apprentissage automatique']):
            answer_parts.append("🧠 **Concernant l'Apprentissage Automatique dans votre corpus :**")
        elif any(word in query_lower for word in ['endoscopy', 'endoscopie']):
            answer_parts.append("🏥 **Concernant l'Endoscopie dans votre corpus :**")
        else:
            answer_parts.append(f"🔍 **Résultats pour votre recherche '{query}' :**")
        
        # Résumé des résultats
        top_result = search_results[0]
        answer_parts.append(f"\n**Article le plus pertinent** (score: {top_result['score']:.3f}) :")
        answer_parts.append(f"📄 *{top_result['article']['title']}*")
        answer_parts.append(f"📅 Année: {top_result['article']['year']}")
        answer_parts.append(f"📖 Journal: {top_result['article']['publication_name']}")
        
        # Analyse des tendances
        years = [r['article']['year'] for r in search_results if r['article']['year']]
        if years:
            avg_year = sum(years) / len(years)
            answer_parts.append(f"\n📊 **Analyse des résultats :**")
            answer_parts.append(f"• {len(search_results)} articles pertinents trouvés")
            answer_parts.append(f"• Année moyenne des publications: {avg_year:.0f}")
            answer_parts.append(f"• Score de pertinence moyen: {np.mean([r['score'] for r in search_results]):.3f}")
        
        # Suggestions
        answer_parts.append(f"\n💡 **Suggestions :**")
        answer_parts.append("• Consultez les détails des articles ci-dessous")
        answer_parts.append("• Utilisez les mots-clés des articles pour affiner votre recherche")
        answer_parts.append("• Explorez les articles connexes par année ou journal")
        
        return "\n".join(answer_parts)
    
    def display_article_card(self, article, score=None):
        """Affiche une carte d'article"""
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Titre avec lien DOI si disponible
                if article.get('doi'):
                    st.markdown(f"### 📄 [{article['title']}](https://doi.org/{article['doi']})")
                else:
                    st.markdown(f"### 📄 {article['title']}")
                
                # Informations de base
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.metric("📅 Année", article.get('year', 'N/A'))
                with col_info2:
                    st.metric("📊 Citations", article.get('citation_count', 0))
                with col_info3:
                    if score is not None:
                        st.metric("🎯 Score", f"{score:.3f}")
                
                # Journal
                if article.get('publication_name'):
                    st.markdown(f"**📖 Journal:** {article['publication_name']}")
                
                # Mots-clés
                if article.get('keywords'):
                    st.markdown(f"**🏷️ Mots-clés:** {article['keywords']}")
                
                # Résumé (si disponible)
                if article.get('abstract'):
                    with st.expander("📝 Résumé"):
                        st.write(article['abstract'])
            
            with col2:
                # Informations techniques
                st.markdown("**🔍 Détails:**")
                st.markdown(f"**ID Scopus:** `{article.get('scopus_id', 'N/A')}`")
                if article.get('subject_areas'):
                    st.markdown(f"**Domaines:** {article['subject_areas']}")
            
            st.divider()
    
    def create_visualizations(self):
        """Crée les visualisations des données"""
        if self.articles_df.empty:
            return
        
        st.subheader("📊 Analyse de votre corpus")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution par année
            year_counts = self.articles_df['year'].value_counts().sort_index()
            fig_years = px.bar(
                x=year_counts.index, 
                y=year_counts.values,
                title="📅 Distribution des articles par année",
                labels={'x': 'Année', 'y': 'Nombre d\'articles'}
            )
            fig_years.update_layout(showlegend=False)
            st.plotly_chart(fig_years, use_container_width=True)
        
        with col2:
            # Distribution des citations
            fig_citations = px.histogram(
                self.articles_df, 
                x='citation_count',
                title="📈 Distribution des citations",
                labels={'citation_count': 'Nombre de citations', 'count': 'Nombre d\'articles'}
            )
            st.plotly_chart(fig_citations, use_container_width=True)
        
        # Top journaux
        if 'publication_name' in self.articles_df.columns:
            journal_counts = self.articles_df['publication_name'].value_counts().head(5)
            if not journal_counts.empty:
                fig_journals = px.pie(
                    values=journal_counts.values,
                    names=journal_counts.index,
                    title="📖 Top 5 des journaux"
                )
                st.plotly_chart(fig_journals, use_container_width=True)
    
    def run_interface(self):
        """Lance l'interface principale"""
        # En-tête
        st.title("🔬 Scopus Research Chatbot")
        st.markdown("*Interrogez intelligemment votre corpus d'articles scientifiques*")
        
        # Sidebar avec statistiques
        with st.sidebar:
            st.header("📊 Statistiques du corpus")
            
            if not self.articles_df.empty:
                st.metric("📚 Total articles", len(self.articles_df))
                st.metric("📅 Années couvertes", 
                         f"{self.articles_df['year'].min():.0f} - {self.articles_df['year'].max():.0f}")
                st.metric("📈 Citations totales", self.articles_df['citation_count'].sum())
                st.metric("🧠 Vecteurs indexés", len(self.article_ids))
            
            st.divider()
            
            # Exemples de questions
            st.subheader("💡 Exemples de questions")
            example_queries = [
                "Articles sur l'IA médicale",
                "Machine learning pour les matériaux",
                "Endoscopie assistée par IA",
                "Réseaux de neurones",
                "Intelligence artificielle 2026"
            ]
            
            for query in example_queries:
                if st.button(f"🔍 {query}", key=f"example_{query}"):
                    st.session_state.query_input = query
        
        # Interface de chat principale
        st.subheader("💬 Posez votre question")
        
        # Zone de saisie
        query = st.text_input(
            "Tapez votre question ici:",
            placeholder="Ex: Quels sont les articles sur l'intelligence artificielle en médecine ?",
            key="query_input"
        )
        
        # Bouton de recherche
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            search_button = st.button("🔍 Rechercher", type="primary")
        with col2:
            clear_button = st.button("🗑️ Effacer")
        
        if clear_button:
            st.session_state.query_input = ""
            st.rerun()
        
        # Traitement de la recherche
        if search_button and query:
            with st.spinner("🔍 Recherche en cours..."):
                # Recherche sémantique
                results = self.semantic_search(query, k=5)
                
                if results:
                    # Génération de la réponse
                    answer = self.generate_answer(query, results)
                    
                    # Affichage de la réponse
                    st.subheader("🤖 Réponse du chatbot")
                    st.markdown(answer)
                    
                    # Affichage des articles trouvés
                    st.subheader("📚 Articles pertinents")
                    
                    for i, result in enumerate(results, 1):
                        st.markdown(f"#### 📄 Résultat {i}")
                        self.display_article_card(result['article'], result['score'])
                else:
                    st.warning("❌ Aucun article pertinent trouvé. Essayez avec d'autres mots-clés.")
        
        # Onglets pour fonctionnalités supplémentaires
        tab1, tab2, tab3 = st.tabs(["📊 Visualisations", "📚 Tous les articles", "ℹ️ À propos"])
        
        with tab1:
            self.create_visualizations()
        
        with tab2:
            st.subheader("📚 Corpus complet")
            if not self.articles_df.empty:
                # Filtres
                col1, col2 = st.columns(2)
                with col1:
                    year_filter = st.selectbox(
                        "Filtrer par année:",
                        ["Toutes"] + sorted(self.articles_df['year'].dropna().unique().tolist(), reverse=True)
                    )
                with col2:
                    sort_by = st.selectbox(
                        "Trier par:",
                        ["Année (desc)", "Année (asc)", "Citations (desc)", "Titre"]
                    )
                
                # Application des filtres
                filtered_df = self.articles_df.copy()
                if year_filter != "Toutes":
                    filtered_df = filtered_df[filtered_df['year'] == year_filter]
                
                # Tri
                if sort_by == "Année (desc)":
                    filtered_df = filtered_df.sort_values('year', ascending=False)
                elif sort_by == "Année (asc)":
                    filtered_df = filtered_df.sort_values('year', ascending=True)
                elif sort_by == "Citations (desc)":
                    filtered_df = filtered_df.sort_values('citation_count', ascending=False)
                elif sort_by == "Titre":
                    filtered_df = filtered_df.sort_values('title')
                
                # Affichage
                for _, article in filtered_df.iterrows():
                    self.display_article_card(article.to_dict())
        
        with tab3:
            st.subheader("ℹ️ À propos de ce chatbot")
            st.markdown("""
            ### 🎓 Projet Scopus Chatbot
            
            **Développé dans le cadre du cours de [Nom du cours]**
            
            #### 🔧 Technologies utilisées:
            - **Extraction de données**: API Scopus
            - **Nettoyage**: Pandas, SQLite
            - **Indexation sémantique**: Sentence Transformers, FAISS
            - **Interface**: Streamlit
            - **Visualisations**: Plotly
            
            #### 📊 Corpus analysé:
            - **Articles**: 10 publications scientifiques
            - **Domaines**: Intelligence Artificielle, Machine Learning
            - **Période**: 2026
            - **Sources**: Base Scopus
            
            #### 🚀 Fonctionnalités:
            - ✅ Recherche sémantique intelligente
            - ✅ Réponses contextualisées
            - ✅ Visualisations interactives
            - ✅ Interface web moderne
            
            ---
            *Développé avec ❤️ pour l'analyse scientifique*
            """)

def main():
    """Fonction principale"""
    try:
        chatbot = ScopusChatbot()
        chatbot.run_interface()
    except Exception as e:
        st.error(f"❌ Erreur lors de l'initialisation: {e}")
        st.info("📋 Vérifiez que les étapes précédentes ont été exécutées correctement.")

if __name__ == "__main__":
    main()
