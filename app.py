import streamlit as st
import pandas as pd

st.set_page_config(page_title="⚽ Predictor", page_icon="⚽", layout="wide")
st.title("⚽ Predictor de Resultados - Mundial 2026")

with st.sidebar:
    st.header("🎯 Opciones")
    view = st.radio("Selecciona:", ["🔮 Predicciones", "📊 Dashboard", "👥 Por Equipo", "📜 Resultados"])

try:
    df_pred = pd.read_csv('predictions.csv')
    df_hist = pd.read_csv('historical_data.csv')
except Exception:
    st.error("Error al cargar archivos")
    st.stop()

if view == "📊 Dashboard":
    st.subheader("Resumen")
    st.metric("Total Partidos Predichos", len(df_pred))
    st.divider()
    st.subheader("Próximos Partidos")
    for i, row in df_pred.head(10).iterrows():
        st.write(f"**{row['Partido']}**")
        st.write(f"1️⃣ {row['Prob 1']}% | ❌ {row['Prob X']}% | 2️⃣ {row['Prob 2']}%")
        st.caption(f"Marcadores más probables: {row['Top1']} · {row['Top2']} · {row['Top3']}")
        st.divider()

elif view == "🔮 Predicciones":
    st.subheader("Tabla de Predicciones")
    st.dataframe(df_pred, use_container_width=True, height=400)
    csv = df_pred.to_csv(index=False)
    st.download_button("📥 Descargar", csv, "predicciones.csv", "text/csv")

elif view == "👥 Por Equipo":
    st.subheader("Predicciones por Equipo")

    equipos = set()
    for p in df_pred['Partido']:
        e = str(p).split(' vs ')
        if len(e) >= 2:
            equipos.add(e[0].strip())
            equipos.add(e[1].strip())

    equipo = st.selectbox("Selecciona equipo:", sorted(list(equipos)))
    resultado = df_pred[df_pred['Partido'].str.contains(equipo, na=False)]

    st.write(f"### {equipo} - {len(resultado)} partidos predichos")
    st.divider()

    for i, row in resultado.iterrows():
        st.write(f"**{row['Partido']}**")
        st.write(f"1️⃣ {row['Prob 1']}% | ❌ {row['Prob X']}% | 2️⃣ {row['Prob 2']}%")
        st.caption(f"Marcadores más probables: {row['Top1']} · {row['Top2']} · {row['Top3']}")
        st.divider()

elif view == "📜 Resultados":
    st.subheader("Resultados de Partidos Jugados")

    df_mundial = df_hist[df_hist['tournament'].str.contains('World Cup', na=False)].copy()

    if len(df_mundial) == 0:
        st.info("ℹ️ No hay resultados del Mundial disponibles aún")
    else:
        equipos = set(df_mundial['home_team']) | set(df_mundial['away_team'])
        equipo = st.selectbox("Selecciona equipo:", sorted(list(equipos)))

        partidos = df_mundial[
            (df_mundial['home_team'] == equipo) | (df_mundial['away_team'] == equipo)
        ].sort_values('date', ascending=False)

        st.write(f"### {equipo} - {len(partidos)} partidos jugados")
        st.divider()

        for i, row in partidos.iterrows():
            if pd.isna(row['home_score']) or pd.isna(row['away_score']):
                resultado = "N/A"
            else:
                resultado = f"{int(row['home_score'])} - {int(row['away_score'])}"

            st.write(f"**{row['home_team']} vs {row['away_team']}**")
            st.write(f"Resultado: **{resultado}**")
            st.write(f"Fecha: {row['date']}")
            st.divider()

st.caption("⚽ Predictor - Mundial 2026 · Actualizado automáticamente vía GitHub Actions")
