import streamlit as st
from pymongo import MongoClient
import pandas as pd
import time

# Style personnalisé
st.markdown("""
    <style>
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    .dataframe-container {
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

# Connexion MongoDB
def connect_mongo():
    tries = 5
    for attempt in range(tries):
        try:
            client = MongoClient("mongodb://mongodb:27017", serverSelectionTimeoutMS=2000)
            client.admin.command('ping')
            return client
        except Exception as e:
            st.warning(f"Tentative de connexion à MongoDB... (essai {attempt+1}/{tries})")
            time.sleep(3)
    st.error("❌ Impossible de se connecter à MongoDB après plusieurs essais.")
    st.stop()

client = connect_mongo()
db = client["projet_final"]
collection = db["streaming_resultats"]

st.title("Visualisation des données - Projet Final")

# Rafraîchissement
if st.button("🔄 Rafraîchir les données"):
    st.session_state["refresh"] = True

if "refresh" not in st.session_state:
    st.session_state["refresh"] = True

if st.session_state["refresh"]:
    documents = list(collection.find({}, {"_id": 0}))
    st.session_state["documents"] = documents
    st.session_state["refresh"] = False

documents = st.session_state.get("documents", [])

# Affichage
if documents:
    df = pd.DataFrame(documents)

    st.subheader("🔍 Aperçu des données (100 premières lignes)")
    st.dataframe(df.head(100), use_container_width=True, height=500)

    st.subheader("📊 Statistiques")
    st.metric("Nombre d'enregistrements chargés", len(df))

    if not df.empty:
        with st.expander("Types de colonnes et valeurs manquantes"):
            info_df = pd.DataFrame({
                "Type": df.dtypes,
                "Valeurs nulles (%)": df.isnull().mean() * 100
            })
            st.dataframe(info_df, use_container_width=True)
else:
    st.warning("Aucune donnée disponible pour l'instant.")
