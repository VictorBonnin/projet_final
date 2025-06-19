import streamlit as st
from pymongo import MongoClient
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta

# Configuration de la page
st.set_page_config(
    page_title="Mongo DB Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé pour un design moderne
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main {
        padding: 0rem 1rem;
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Style pour les métriques */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 1rem;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    .metric-delta {
        font-size: 0.9rem;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    /* Cartes de couleurs différentes */
    .metric-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .metric-success {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .metric-warning {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
    
    .metric-danger {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }
    
    .metric-info {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        color: #333 !important;
    }
    
    .metric-dark {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    }
    
    /* Header */
    .dashboard-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .dashboard-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Refresh button */
    .refresh-container {
        display: flex;
        justify-content: center;
        margin: 1rem 0;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-online {
        background-color: #4CAF50;
        animation: pulse 2s infinite;
    }
    
    .status-offline {
        background-color: #f44336;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .metric-value {
            font-size: 2rem;
        }
        .dashboard-title {
            font-size: 2rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Connexion MongoDB avec indicateur de status
@st.cache_resource
def connect_mongo():
    try:
        client = MongoClient("mongodb://mongodb:27017", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        return client, True
    except Exception as e:
        return None, False

# Fonction pour créer une carte de métrique
def create_metric_card(title, value, delta=None, delta_color="normal", card_class="metric-primary"):
    delta_html = ""
    if delta is not None:
        delta_class = "metric-delta"
        if delta_color == "normal":
            delta_html = f'<div class="{delta_class}">△ {delta}</div>'
        elif delta_color == "inverse":
            delta_html = f'<div class="{delta_class}">▽ {delta}</div>'
    
    return f"""
    <div class="metric-card {card_class}">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{title}</div>
        {delta_html}
    </div>
    """

# Fonction pour calculer les KPI
def calculate_kpi(df):
    if df.empty:
        return {}
    
    kpi = {}
    
    # KPI de base
    kpi['total_records'] = len(df)
    kpi['columns_count'] = len(df.columns)
    
    # Analyse des données numériques
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        kpi['numeric_columns'] = len(numeric_cols)
        kpi['avg_numeric_value'] = df[numeric_cols].mean().mean()
        kpi['null_percentage'] = (df[numeric_cols].isnull().sum().sum() / (len(df) * len(numeric_cols))) * 100
    else:
        kpi['numeric_columns'] = 0
        kpi['avg_numeric_value'] = 0
        kpi['null_percentage'] = 0
    
    # Analyse temporelle si possible
    date_cols = df.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0:
        kpi['has_dates'] = True
        latest_date = df[date_cols[0]].max()
        kpi['latest_record'] = latest_date.strftime('%Y-%m-%d %H:%M') if pd.notna(latest_date) else "N/A"
    else:
        kpi['has_dates'] = False
        kpi['latest_record'] = "N/A"
    
    # Analyse de la diversité des données
    kpi['unique_values_avg'] = df.nunique().mean()
    kpi['memory_usage'] = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
    
    return kpi

# Header du dashboard
st.markdown("""
<div class="dashboard-header">
    <h1 class="dashboard-title">📊 Dashboard Analytics</h1>
    <p class="dashboard-subtitle">Monitoring en temps réel de vos données</p>
</div>
""", unsafe_allow_html=True)

# Connexion et status
client, is_connected = connect_mongo()

# Indicateur de connexion
col_status1, col_status2, col_status3 = st.columns([1, 2, 1])
with col_status2:
    if is_connected:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <span class="status-indicator status-online"></span>
            <strong>Connecté à MongoDB</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <span class="status-indicator status-offline"></span>
            <strong>Déconnecté de MongoDB</strong>
        </div>
        """, unsafe_allow_html=True)
        st.error("❌ Impossible de se connecter à MongoDB")
        st.stop()

# Bouton de rafraîchissement centré
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🔄 Actualiser les données", use_container_width=True):
        st.session_state["refresh"] = True
        st.rerun()

# Initialisation des données
if "refresh" not in st.session_state:
    st.session_state["refresh"] = True

if st.session_state.get("refresh", True):
    with st.spinner("Chargement des données..."):
        db = client["projet_final"]
        collection = db["streaming_resultats"]
        
        # Limitation pour les gros volumes - prendre seulement un échantillon pour les KPI
        sample_size = 10000  # Ajustez selon vos besoins
        documents = list(collection.find({}, {"_id": 0}).limit(sample_size))
        
        st.session_state["documents"] = documents
        st.session_state["total_count"] = collection.count_documents({})
        st.session_state["refresh"] = False

documents = st.session_state.get("documents", [])
total_count = st.session_state.get("total_count", 0)

if documents:
    df = pd.DataFrame(documents)
    kpi = calculate_kpi(df)
    
    # Ligne 1 - KPI principaux
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(create_metric_card(
            "Total Enregistrements", 
            f"{total_count:,}",
            card_class="metric-primary"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(
            "Échantillon Analysé", 
            f"{len(df):,}",
            card_class="metric-success"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(create_metric_card(
            "Colonnes", 
            f"{kpi['columns_count']}",
            card_class="metric-warning"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(create_metric_card(
            "Colonnes Numériques", 
            f"{kpi['numeric_columns']}",
            card_class="metric-info"
        ), unsafe_allow_html=True)
    
    with col5:
        st.markdown(create_metric_card(
            "Valeurs Uniques (moy)", 
            f"{kpi['unique_values_avg']:.1f}",
            card_class="metric-danger"
        ), unsafe_allow_html=True)
    
    with col6:
        st.markdown(create_metric_card(
            "Taille Mémoire", 
            f"{kpi['memory_usage']:.1f} MB",
            card_class="metric-dark"
        ), unsafe_allow_html=True)
    
    # Ligne 2 - KPI de qualité des données
    col7, col8, col9, col10 = st.columns(4)
    
    with col7:
        st.markdown(create_metric_card(
            "Données Manquantes", 
            f"{kpi['null_percentage']:.1f}%",
            card_class="metric-warning" if kpi['null_percentage'] > 10 else "metric-success"
        ), unsafe_allow_html=True)
    
    with col8:
        st.markdown(create_metric_card(
            "Dernier Enregistrement", 
            kpi['latest_record'],
            card_class="metric-info"
        ), unsafe_allow_html=True)
    
    with col9:
        completeness = ((1 - kpi['null_percentage']/100) * 100)
        st.markdown(create_metric_card(
            "Complétude", 
            f"{completeness:.1f}%",
            card_class="metric-success" if completeness > 90 else "metric-warning"
        ), unsafe_allow_html=True)
    
    with col10:
        efficiency = min(100, (kpi['unique_values_avg'] / len(df)) * 100)
        st.markdown(create_metric_card(
            "Diversité", 
            f"{efficiency:.1f}%",
            card_class="metric-primary"
        ), unsafe_allow_html=True)
    
    # Graphiques de visualisation (optionnel, légers)
    if st.checkbox("Afficher les graphiques détaillés", value=False):
        st.subheader("📈 Visualisations")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Graphique des types de données
            if not df.empty:
                dtype_counts = df.dtypes.value_counts()
                fig_pie = px.pie(
                    values=dtype_counts.values, 
                    names=dtype_counts.index.astype(str),
                    title="Répartition des Types de Données",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_chart2:
            # Graphique des valeurs manquantes par colonne
            if not df.empty:
                null_counts = df.isnull().sum().sort_values(ascending=False).head(10)
                if null_counts.sum() > 0:
                    fig_bar = px.bar(
                        x=null_counts.index, 
                        y=null_counts.values,
                        title="Top 10 - Colonnes avec Valeurs Manquantes",
                        color=null_counts.values,
                        color_continuous_scale="Reds"
                    )
                    fig_bar.update_layout(height=400)
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.success("🎉 Aucune valeur manquante détectée!")

else:
    # État vide avec style
    st.markdown("""
    <div style="text-align: center; padding: 3rem; color: #666;">
        <h2>📭 Aucune donnée disponible</h2>
        <p>Les données apparaîtront ici une fois la connexion établie.</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666; border-top: 1px solid #eee; margin-top: 2rem;">
    <p>Dashboard Analytics - Dernière mise à jour: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)