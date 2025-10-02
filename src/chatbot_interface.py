import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import plotly.express as px
from pathlib import Path


# ================================
# CLASS PRINCIPALE
# ================================
class ArxivChatbot:
    def __init__(self):
        self.db_path = 'data/processed/arxiv_database.db'
        self.model_name = 'all-MiniLM-L6-v2'
        self.model = None
        self.faiss_index = None
        self.article_ids = []

        # Configuration de la page Streamlit
        st.set_page_config(
            page_title="ArXiv Research Assistant",
            page_icon="📚",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        self.setup_chatbot()

    # ================================
    # CHARGEMENT RESSOURCES
    # ================================
    @st.cache_resource
    def load_model(_self):
        return SentenceTransformer(_self.model_name)

    @st.cache_resource
    def load_faiss_index(_self):
        try:
            faiss_path = 'data/indexes/arxiv_faiss.index'
            metadata_path = 'data/indexes/arxiv_faiss_metadata.pkl'

            if Path(faiss_path).exists() and Path(metadata_path).exists():
                index = faiss.read_index(faiss_path)
                with open(metadata_path, 'rb') as f:
                    metadata = pickle.load(f)
                return index, metadata['article_ids']
            else:
                return None, []
        except Exception as e:
            st.error(f"Erreur FAISS: {e}")
            return None, []

    @st.cache_data
    def load_articles_data(_self):
        try:
            conn = sqlite3.connect(_self.db_path)
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
                ORDER BY a.year DESC, a.title
            '''
            df = pd.read_sql_query(query, conn)
            conn.close()

            # Charger aussi auteurs
            conn = sqlite3.connect(_self.db_path)
            authors_df = pd.read_sql_query('''
                SELECT aa.article_id, au.preferred_name
                FROM article_authors aa
                JOIN authors au ON aa.author_id = au.id
            ''', conn)
            conn.close()

            authors_grouped = authors_df.groupby('article_id')['preferred_name'].apply(list).reset_index()
            df = df.merge(authors_grouped, left_on='id', right_on='article_id', how='left')
            df.rename(columns={'preferred_name': 'authors'}, inplace=True)
            return df
        except Exception as e:
            st.error(f"Erreur chargement articles: {e}")
            return pd.DataFrame()

    # ================================
    # INIT CHATBOT
    # ================================
    def setup_chatbot(self):
        with st.spinner("Chargement du système..."):
            self.model = self.load_model()
            self.faiss_index, self.article_ids = self.load_faiss_index()
            self.articles_df = self.load_articles_data()

        if self.faiss_index is None:
            st.error("⚠️ Index FAISS manquant. Exécutez l’étape 3 (indexation sémantique).")
            st.stop()

    # ================================
    # RECHERCHE SÉMANTIQUE
    # ================================
    def semantic_search(self, query, k=5):
        if not query.strip():
            return []

        try:
            query_emb = self.model.encode([query]).astype('float32')
            faiss.normalize_L2(query_emb)

            scores, indices = self.faiss_index.search(query_emb, k=k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.article_ids):
                    article_id = self.article_ids[idx]
                    row = self.articles_df[self.articles_df['id'] == article_id]
                    if not row.empty:
                        article = row.iloc[0]
                        results.append({
                            'score': float(score),
                            'article': article.to_dict()
                        })
            return results
        except Exception as e:
            st.error(f"Erreur recherche: {e}")
            return []

    # ================================
    # AFFICHAGE RESULTAT
    # ================================
    def display_article_card(self, article, score=None):
        with st.container():
            st.markdown("----")
            st.subheader(article['title'])

            if article.get('pdf_url'):
                st.markdown(f"[📄 PDF disponible]({article['pdf_url']})")

            if article.get('year'):
                st.write(f"📅 Année : {article['year']}")

            if article.get('categories'):
                st.write(f"🏷️ Catégories : {article['categories']}")

            if article.get('authors'):
                st.write(f"✍️ Auteurs : {', '.join(article['authors'])}")

            if score is not None:
                st.write(f"🔎 Score de pertinence : {score:.3f}")

            if article.get('abstract'):
                with st.expander("Résumé"):
                    st.write(article['abstract'])

    # ================================
    # VISUALISATIONS
    # ================================
    def create_visualizations(self):
        if self.articles_df.empty:
            return

        st.subheader("📊 Visualisations interactives")

        col1, col2 = st.columns(2)

        with col1:
            years = self.articles_df['year'].value_counts().sort_index()
            fig_years = px.bar(
                x=years.index,
                y=years.values,
                title="Distribution des articles par année",
                labels={'x': 'Année', 'y': "Nombre d'articles"}
            )
            st.plotly_chart(fig_years, use_container_width=True)

        with col2:
            cats = self.articles_df['categories'].value_counts().head(10)
            if not cats.empty:
                fig_cats = px.pie(
                    values=cats.values,
                    names=cats.index,
                    title="Top 10 des catégories"
                )
                st.plotly_chart(fig_cats, use_container_width=True)

        # Top auteurs
        if 'authors' in self.articles_df.columns:
            all_authors = self.articles_df.explode('authors')['authors'].dropna()
            top_authors = all_authors.value_counts().head(10)
            if not top_authors.empty:
                fig_authors = px.bar(
                    x=top_authors.index,
                    y=top_authors.values,
                    title="Top 10 des auteurs les plus prolifiques",
                    labels={'x': 'Auteur', 'y': "Nombre d'articles"}
                )
                st.plotly_chart(fig_authors, use_container_width=True)

    # ================================
    # INTERFACE PRINCIPALE
    # ================================
    def run_interface(self):
        st.title("📚 ArXiv Research Assistant")
        st.caption("Chatbot scientifique basé sur indexation sémantique")

        # Zone de saisie
        query = st.text_input(
            "❓ Posez une question :",
            placeholder="Ex: Articles récents sur le deep learning en médecine..."
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            search_button = st.button("🔍 Rechercher")

        # Filtres
        st.sidebar.header("🔎 Filtres")
        year_filter = st.sidebar.multiselect(
            "Filtrer par année",
            options=sorted(self.articles_df['year'].dropna().unique(), reverse=True)
        )
        author_filter = st.sidebar.multiselect(
            "Filtrer par auteur",
            options=sorted(set([a for lst in self.articles_df['authors'].dropna() for a in lst]))
        )
        cat_filter = st.sidebar.multiselect(
            "Filtrer par catégorie",
            options=sorted(set(self.articles_df['categories'].dropna().unique()))
        )

        if search_button and query:
            with st.spinner("Recherche en cours..."):
                results = self.semantic_search(query, k=10)

                if year_filter:
                    results = [r for r in results if r['article']['year'] in year_filter]
                if author_filter:
                    results = [r for r in results if r['article'].get('authors') and
                               any(a in r['article']['authors'] for a in author_filter)]
                if cat_filter:
                    results = [r for r in results if r['article']['categories'] in cat_filter]

                if results:
                    st.subheader("📑 Résultats trouvés")
                    for res in results:
                        self.display_article_card(res['article'], res['score'])
                else:
                    st.warning("Aucun résultat avec ces critères.")

        # Tabs
        tab1, tab2 = st.tabs(["📊 Analyse du corpus", "📂 Base documentaire"])
        with tab1:
            self.create_visualizations()
        with tab2:
            st.dataframe(self.articles_df)


# ================================
# MAIN
# ================================
def main():
    try:
        chatbot = ArxivChatbot()
        chatbot.run_interface()
    except Exception as e:
        st.error(f"Erreur interface: {e}")


if __name__ == "__main__":
    main()
