import streamlit as st
import pandas as pd
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
        ["📊 Dashboard", "🔮 Predicciones", "📈 Histórico"]
    )
    st.divider()
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.success("✅ Datos actualizados")

# Cargar datos
try:
    df_pred = pd.read_csv('predictions.csv')
except:
    st.error("❌ Error: No se encontró predictions.csv")
    st.stop()

# DASHBOARD
if view_mode == "📊 Dashboard":
    st.subheader("Resumen de Predicciones")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📅 Total Partidos", len(df_pred))
    
    with col2:
        confianza_prom = df_pred['Confianza'].mean() if 'Confianza' in df_pred.columns else 0
        st.metric("🎯 Confianza Promedio", f"{confianza_prom:.1f}%")
    
    with col3:
        st.metric("⚽ Predicciones Generadas", len(df_pred))
    
    st.divider()
    st.subheader("🔜 Próximos Partidos")
    
    if len(df_pred) > 0:
        for idx, row in df_pred.head(15).iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 1.5, 1])
            
            with col1:
                st.write(f"**{row['Partido']}**")
            with col2:
                prob_1 = row['Prob 1'] if 'Prob 1' in row else 0
                prob_x = row['Prob X'] if 'Prob X' in row else 0
                prob_2 = row['Prob 2'] if 'Prob 2' in row else 0
                st.write(f"1️⃣ {prob_1:.0f}% | ❌ {prob_x:.0f}% | 2️⃣ {prob_2:.0f}%")
            with col3:
                marcador = row['Marcador'] if 'Marcador' in row else "N/A"
                st.write(f"**{marcador}**")
            with col4:
                conf = row['Confianza'] if 'Confianza' in row else 0
                st.write(f"{conf:.1f}%")
            
            st.divider()

# PREDICCIONES
elif view_mode == "🔮 Predicciones":
    st.subheader("Tabla Completa de Predicciones")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**Total: {len(df_pred)} partidos**")
    
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
    st.subheader("Información del Modelo")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Predicciones", len(df_pred))
    with col2:
        st.metric("🤖 Modelo", "XGBoost")
    with col3:
        st.metric("📈 Features", "22 variables")
    
    st.divider()
    st.info("📌 Los resultados se actualizarán cuando se jueguen los partidos.")

st.divider()
st.caption("⚽ Predictor - Mundial 2026 | " + datetime.now().strftime("%d/%m/%Y %H:%M"))
