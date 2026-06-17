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
            st.caption(f"📅 {row['Fecha']}")
        with col2:
            st.write(f"1️⃣ {row['Prob 1']:.1f}% | ❌ {row['Prob X']:.1f}% | 2️⃣ {row['Prob 2']:.1f}%")
        with col3:
            st.write(f"**{row['Marcador']}**")
            st.caption(f"Conf: {row['Confianza']:.2f}%")
        st.divider()

# PREDICCIONES
elif view_mode == "🔮 Predicciones":
    st.subheader("Tabla Completa de Predicciones")
    st.dataframe(df_pred, use_container_width=True, height=400)
    
    csv = df_pred.to_csv(index=False)
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name="predicciones_mundial_2026.csv",
        mime="text/csv"
    )

# HISTÓRICO
elif view_mode == "📈 Histórico":
    st.subheader("Resultados Históricos")
    
    if len(df_hist) > 0:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 Total Partidos", len(df_hist))
        with col2:
            st.metric("📅 Último Partido", df_hist['date'].max() if 'date' in df_hist.columns else "N/A")
        
        st.divider()
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("ℹ️ Sin datos históricos disponibles")

# ADMIN
elif view_mode == "⚙️ Admin":
    st.subheader("Panel de Administración")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📊 Información")
        st.write(f"✅ Predicciones cargadas: {len(df_pred)}")
        st.write(f"📈 Histórico cargado: {len(df_hist)}")
    
    with col2:
        st.write("### 📁 Estado")
        st.write("✅ predictions.csv: OK")
        st.write("✅ historical_data.csv: OK")

st.divider()
st.caption("⚽ Predictor - Mundial 2026 | " + datetime.now().strftime("%d/%m/%Y %H:%M"))
