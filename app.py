import streamlit as st
import pandas as pd

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
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"1️⃣ {row['Prob 1']}%")
        with col2:
            st.write(f"❌ {row['Prob X']}%")
        with col3:
            st.write(f"2️⃣ {row['Prob 2']}%")
        st.divider()

elif view == "🔮 Predicciones":
    st.subheader("Tabla de Predicciones")
    st.dataframe(df, use_container_width=True, height=400)
    csv = df.to_csv(index=False)
    st.download_button("📥 Descargar CSV", csv, "predicciones.csv", "text/csv")

elif view == "👥 Por Equipo":
    st.subheader("Predicciones por Equipo")
    
    equipos = set()
    for p in df['Partido']:
        e = str(p).split(' vs ')
        if len(e) >= 2:
            equipos.add(e[0].strip())
            equipos.add(e[1].strip())
    
    equipo = st.selectbox("Selecciona equipo:", sorted(list(equipos)))
    resultado = df[df['Partido'].str.contains(equipo, na=False)]
    
    st.write(f"### {equipo} ({len(resultado)} partidos)")
    st.divider()
    
    for i, row in resultado.iterrows():
        st.write(f"**{row['Partido']}**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"1️⃣ {row['Prob 1']}%")
        with col2:
            st.write(f"❌ {row['Prob X']}%")
        with col3:
            st.write(f"2️⃣ {row['Prob 2']}%")
        st.divider()

st.caption("⚽ Predictor - Mundial 2026")
