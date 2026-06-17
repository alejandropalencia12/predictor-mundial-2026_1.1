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
        ["📊 Dashboard", "🔮 Predicciones", "👥 Por Equipo"]
    )

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
        st.metric("🎯 Confianza Prom.", f"{df_pred['Confianza'].mean():.1f}%")
    with col3:
        st.metric("⚽ Predicciones", len(df_pred))
    
    st.divider()
    st.subheader("🔜 Próximos Partidos")
    
    for idx, row in df_pred.head(10).iterrows():
        st.write(f"**{row['Partido']}**")
        st.write(f"1️⃣ {row['Prob 1']:.0f}% | ❌ {row['Prob X']:.0f}% | 2️⃣ {row['Prob 2']:.0f}%")
        st.write(f"Marcador: **{row['Marcador']}** | Confianza: {row['Confianza']:.2f}%")
        st.divider()

# PREDICCIONES
elif view_mode == "🔮 Predicciones":
    st.subheader("Tabla de Predicciones")
    st.dataframe(df_pred, use_container_width=True)
    
    csv = df_pred.to_csv(index=False)
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name="predicciones.csv",
        mime="text/csv"
    )

# POR EQUIPO
elif view_mode == "👥 Por Equipo":
    st.subheader("Predicciones por Equipo")
    
    # Obtener equipos
    equipos = set()
    for p in df_pred['Partido']:
        e = p.split(' vs ')
        equipos.add(e[0].strip())
        if len(e) > 1:
            equipos.add(e[1].strip())
    
    equipos = sorted(list(equipos))
    equipo = st.selectbox("Selecciona equipo:", equipos)
    
    # Filtrar
    resultado = df_pred[df_pred['Partido'].str.contains(equipo)]
    
    if len(resultado) > 0:
        st.write(f"### {equipo} - {len(resultado)} partidos")
        for idx, row in resultado.iterrows():
            st.write(f"**{row['Partido']}**")
            st.write(f"1️⃣ {row['Prob 1']:.0f}% | ❌ {row['Prob X']:.0f}% | 2️⃣ {row['Prob 2']:.0f}%")
            st.write(f"Predicción: {row['Marcador']} ({row['Confianza']:.2f}%)")
            st.divider()
    else:
        st.info("Sin partidos para este equipo")

st.divider()
st.caption("⚽ Predictor - Mundial 2026 | " + datetime.now().strftime("%d/%m/%Y"))
