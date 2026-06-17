import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="⚽ Predictor", page_icon="⚽", layout="wide")

st.title("⚽ Predictor de Resultados - Mundial 2026")

with st.sidebar:
    st.header("🎯 Opciones")
    view = st.radio("Selecciona:", ["📊 Dashboard", "🔮 Predicciones", "👥 Por Equipo"])

try:
    df = pd.read_csv('predictions.csv')
except:
    st.error("No se encontró predictions.csv")
    st.stop()

if view == "📊 Dashboard":
    st.subheader("Resumen")
    st.metric("Total Partidos", len(df))
    st.divider()
    st.subheader("Próximos Partidos")
    for i, row in df.head(10).iterrows():
        st.write(f"**{row['Partido']}**")
        st.write(f"1️⃣ {row['Prob 1']}% | ❌ {row['Prob X']}% | 2️⃣ {row['Prob 2']}%")
        st.write(f"Predicción: {row['Marcador']}")
        st.divider()

elif view == "🔮 Predicciones":
    st.subheader("Tabla de Predicciones")
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False)
    st.download_button("📥 Descargar", csv, "predicciones.csv", "text/csv")

elif view == "👥 Por Equipo":
    st.subheader("Por Equipo")
    equipos = set()
    for p in df['Partido']:
        e = str(p).split(' vs ')
        equipos.add(e[0].strip())
        if len(e) > 1:
            equipos.add(e[1].strip())
    
    equipo = st.selectbox("Equipo:", sorted(list(equipos)))
    resultado = df[df['Partido'].str.contains(equipo)]
    
    st.write(f"### {equipo}")
    for i, row in resultado.iterrows():
        st.write(f"**{row['Partido']}**")
        st.write(f"Predicción: {row['Marcador']}")
        st.divider()

st.caption("⚽ Predictor - Mundial 2026")
