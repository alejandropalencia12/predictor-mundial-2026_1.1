import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(
    page_title="⚽ Predictor Mundial 2026",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Predictor de Resultados - Mundial 2026")

# Sidebar
with st.sidebar:
    st.header("🎯 Opciones")
    view_mode = st.radio(
        "Selecciona vista:",
        ["📊 Dashboard", "🔮 Predicciones", "📈 Histórico", "⚙️ Admin"]
    )

# Cargar datos
try:
    df_pred = pd.read_csv('predictions.csv')
    df_hist = pd.read_csv('historical_data.csv')
except:
    st.error("Error al cargar datos")
    st.stop()

# DASHBOARD
if view_mode == "📊 Dashboard":
    st.subheader("Resumen de Predicciones")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 Total Partidos", len(df_pred))
    with col2:
        st.metric("⏳ Pendientes", len(df_pred))
    with col3:
        st.metric("✅ Jugados", len(df_hist) if len(df_hist) > 0 else 0)
    with col4:
        st.metric("🎯 Confianza Promedio", f"{df_pred['Confianza'].mean():.1f}%")
    
    st.divider()
    st.subheader("🔜 Próximos 10 Partidos")
    
    for idx, row in df_pred.head(10).iterrows():
        col1, col2, col3 = st.columns([2, 2, 1.5])
        with col1:
            st.write(f"**{row['Partido']}**")
            st.caption(f"📅 {row['Fecha']}
