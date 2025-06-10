#!pip install streamlit
#!pip install plotly

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

df_2025 = pd.read_csv("predictions_immobilier_2025.csv")

st.set_page_config(page_title="Prédictions immobilières 2025", layout="wide")

# ------------------------
# 1. Titre et présentation
# ------------------------
st.title("📊 Prédiction de la valeur foncière en 2025")
st.markdown("""
Ce tableau de bord présente les **résultats de prédiction immobilière pour 2025** (par mois, département, etc.) à partir d’un modèle de machine learning Random Forest entraîné sur les données de 2020 à 2024, issues de la tanche de prix de allant de 470 000 à 1.3M d'euros.

**Démarche résumée :**
- Préparation des données (feature engineering, nettoyage…)
- Entraînement et validation du modèle
- Génération des prédictions 2025 (par département, par mois)
""")

st.markdown("---")

# ------------------------
# 2. Exploration interactive
# ------------------------
st.header("🔎 Explorer les prédictions 2025")

# Sélection du département (ou tous)
departements = sorted(df_2025['departement'].unique())
dep_selection = st.selectbox("Choisir un département :", options=['Tous'] + departements)

# Filtre
if dep_selection != 'Tous':
    df_affiche = df_2025[df_2025['departement'] == dep_selection]
else:
    df_affiche = df_2025.copy()

# Affiche le dataframe
st.dataframe(df_affiche)

# ------------------------
# 3. Visualisations simples
# ------------------------
st.markdown("### 📈 Évolution de la valeur foncière prédite")

if 'mois' in df_affiche.columns:
    chart_df = (
        df_affiche.groupby(['mois', 'departement'])['valeur_fonciere_predite']
        .mean()
        .reset_index()
    )

    # Filtre si besoin
    if dep_selection != 'Tous':
        chart_df = chart_df[chart_df['departement'] == dep_selection]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(chart_df['mois'], chart_df['valeur_fonciere_predite'], marker='o')
    ax.set_xlabel("Mois")
    ax.set_ylabel("Valeur foncière prédite (€)")
    if dep_selection != 'Tous':
        ax.set_title(f"Évolution 2025 – Département {dep_selection}")
    else:
        ax.set_title("Évolution 2025 – Moyenne sur tous les départements")
    st.pyplot(fig)
else:
    st.info("Pas de variable 'mois' détectée pour la visualisation.")

valeurs_par_dept = (
    df_2025.groupby('departement')['valeur_fonciere_predite']
    .mean()
    .reset_index()
)

# ------------------------
# 4. Statistiques globales
# ------------------------
st.markdown("### 📋 Statistiques globales")
st.write(df_affiche['valeur_fonciere_predite'].describe())

# ------------------------
# 5. Carte
# ------------------------

st.markdown("### Carte intéractive des départements les plus/moins chers")

valeurs_par_dept['departement'] = valeurs_par_dept['departement'].astype(str).str.zfill(2)

fig = px.choropleth(
    valeurs_par_dept,
    geojson='https://france-geojson.gregoiredavid.fr/repo/departements.geojson',
    locations='departement',
    featureidkey="properties.code",
    color='valeur_fonciere_predite',
    color_continuous_scale=["green", "yellow", "red"],  # Vert -> Jaune -> Rouge
    scope="europe",
    labels={'valeur_fonciere_predite': 'Valeur foncière moyenne (€)'},
    title="Valeur foncière prédite par département (2025)"
)
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(
    width=800,  # Largeur de la figure (ajuste à volonté)
    height=600,
    margin={"r":0,"t":50,"l":0,"b":0},
    font=dict(size=16)
)

st.plotly_chart(fig, use_container_width=True)


# ------------------------
# 6. Hauts/bas
# ------------------------

st.markdown("### 🏆 Plus/moins chers des départements (valeur foncière moyenne 2025)")

top5 = valeurs_par_dept.sort_values('valeur_fonciere_predite', ascending=False).head(5)
flop5 = valeurs_par_dept.sort_values('valeur_fonciere_predite', ascending=True).head(5)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Top 5 des plus chers")
    st.table(top5)
with col2:
    st.subheader("Top 5 des moins chers")
    st.table(flop5)


# ------------------------
# 5. Téléchargement
# ------------------------
st.markdown("### 💾 Télécharger les résultats")
csv = df_affiche.to_csv(index=False).encode()
st.download_button("Télécharger au format CSV", csv, "prediction_immobiliere_2025.csv")