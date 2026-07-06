"""
app.py - Streamlit app para Predictor Mundial 2026
"""

import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import os

st.set_page_config(page_title="Predictor Mundial 2026", layout="wide", initial_sidebar_state="expanded")

# ============================================================
# DICCIONARIO DE CÓDIGOS DE PAÍS (ISO 3166-1 alpha-2)
# ============================================================
COUNTRY_CODES = {
    'Canada': 'ca', 'United States': 'us', 'Mexico': 'mx', 'Panama': 'pa', 'Haiti': 'ht',
    'Argentina': 'ar', 'Brazil': 'br', 'Uruguay': 'uy', 'Colombia': 'co', 'Ecuador': 'ec', 'Paraguay': 'py',
    'Germany': 'de', 'Austria': 'at', 'Belgium': 'be', 'Bosnia and Herzegovina': 'ba', 'Croatia': 'hr', 'Czech Republic': 'cz',
    'Spain': 'es', 'France': 'fr', 'England': 'gb', 'Norway': 'no', 'Netherlands': 'nl',
    'Portugal': 'pt', 'Serbia': 'rs', 'Switzerland': 'ch', 'Turkey': 'tr', 'Algeria': 'dz', 'Cape Verde': 'cv',
    'Ivory Coast': 'ci', 'Egypt': 'eg', 'Ghana': 'gh', 'Morocco': 'ma', 'DR Congo': 'cd',
    'Senegal': 'sn', 'South Africa': 'za', 'Tunisia': 'tn', 'Saudi Arabia': 'sa', 'Australia': 'au', 'South Korea': 'kr',
    'Iran': 'ir', 'Japan': 'jp', 'Jordan': 'jo', 'Qatar': 'qa', 'Uzbekistan': 'uz', 'Iraq': 'iq', 'New Zealand': 'nz', 'Sweden': 'se',
    'Curaçao': 'cw', 'Scotland': 'gb'
}

def get_flag_image(country):
    """Obtiene la bandera de un país desde flagcdn.com"""
    code = COUNTRY_CODES.get(country, None)
    if not code:
        return None

    url = f"https://flagcdn.com/w160/{code}.png"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception:
        pass
    return None

# ============================================================
# ESTILOS PERSONALIZADOS
# ============================================================
st.markdown("""
<style>
    .header-main {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-main">⚽ Predictor Mundial 2026</div>', unsafe_allow_html=True)

# ============================================================
# SIDEBAR - NAVEGACIÓN
# ============================================================
st.sidebar.title("📊 Navegación")
opciones = {
    "🔮 Predicciones": "Predicciones",
    "⚽ Últimos Partidos": "Últimos Partidos",
    "🏆 Histórico": "Histórico",
    "📖 Información": "Información"
}

seccion_display = st.sidebar.radio("Selecciona una sección:", list(opciones.keys()))
seccion = opciones[seccion_display]

# ============================================================
# SECCIÓN: INFORMACIÓN (QUÉ ES xG)
# ============================================================
if seccion == "Información":
    st.header("📖 ¿Qué es xG (Expected Goals)?")

    st.markdown("""
    ### Definición Simple

    **xG (Goles Esperados)** mide la **fuerza de ataque** o **capacidad de anotar goles**
    de un equipo basada en sus oportunidades de tiro.

    Es un número que te dice: *"¿Cuántos goles debería anotar este equipo?"*

    ### Cómo interpretarlo
    """)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.info("""
        **xG < 0.8**

        Equipo débil ofensivamente.
        Probablemente anote 0-1 gol.
        """)

    with col2:
        st.success("""
        **xG 0.8 - 1.5**

        Equipo con buen ataque.
        Probablemente anote 1-2 goles.
        """)

    with col3:
        st.warning("""
        **xG 1.5 - 2.5**

        Equipo muy fuerte ofensivo.
        Probablemente anote 2-3 goles.
        """)

    with col4:
        st.error("""
        **xG > 2.5**

        Equipo dominante.
        Probablemente anote 3+ goles.
        """)

    st.markdown("""
    ### Ejemplos Prácticos

    **Suiza 1.41 vs Argelia 0.93**
    - Suiza ataca mejor (1.41 > 0.93)
    - Probable: Suiza 1-0 o 2-1

    **España 2.2 vs Austria 0.64**
    - España domina ofensivamente (2.2 vs 0.64)
    - Probable: España 2-0 o 3-0
    """)

# ============================================================
# SECCIÓN: PREDICCIONES (PARTIDOS PENDIENTES)
# ============================================================
elif seccion == "Predicciones":
    st.header("📅 Partidos Pendientes - Predicciones")

    if os.path.exists('predictions.csv'):
        predictions_df = pd.read_csv('predictions.csv')

        columnas_reordenadas = [
            'Fecha', 'Partido',
            'Top1', 'Top2', 'Top3',
            'Prob 1', 'Prob X', 'Prob 2',
            'xG Local', 'xG Visita'
        ]
        predictions_df_display = predictions_df[columnas_reordenadas]

        st.dataframe(
            predictions_df_display,
            column_config={
                'Fecha': st.column_config.TextColumn("Fecha", width="small"),
                'Partido': st.column_config.TextColumn("Partido", width="medium"),
                'Top1': st.column_config.TextColumn("🥇 Top1", width="small"),
                'Top2': st.column_config.TextColumn("🥈 Top2", width="small"),
                'Top3': st.column_config.TextColumn("🥉 Top3", width="small"),
                'Prob 1': st.column_config.NumberColumn("🏠 Local %", format="%.1f"),
                'Prob X': st.column_config.NumberColumn("Empate %", format="%.1f"),
                'Prob 2': st.column_config.NumberColumn("✈️ Visita %", format="%.1f"),
                'xG Local': st.column_config.NumberColumn("xG Local", format="%.2f"),
                'xG Visita': st.column_config.NumberColumn("xG Visita", format="%.2f"),
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("⚠️ El archivo de predicciones aún no está disponible.")

# ============================================================
# SECCIÓN: ÚLTIMOS PARTIDOS (FILTRO POR SELECCIÓN)
# ============================================================
elif seccion == "Últimos Partidos":
    st.header("📊 Últimos Partidos de Cada Selección")

    if os.path.exists('historical_data.csv'):
        historico_df = pd.read_csv('historical_data.csv')
        historico_df['date'] = pd.to_datetime(historico_df['date'])

        todos_equipos = sorted(
            set(historico_df['home_team'].unique()) | set(historico_df['away_team'].unique())
        )

        col1, col2, col3 = st.columns([1, 3, 2])

        with col2:
            equipo_seleccionado = st.selectbox(
                "Selecciona un equipo:",
                todos_equipos,
                key="team_select"
            )

        with col1:
            flag_img = get_flag_image(equipo_seleccionado)
            if flag_img:
                st.image(flag_img, width=100)

        partidos_equipo = historico_df[
            (historico_df['home_team'] == equipo_seleccionado) |
            (historico_df['away_team'] == equipo_seleccionado)
        ].sort_values('date', ascending=False)

        if len(partidos_equipo) > 0:
            cantidad = st.slider("Últimos partidos a mostrar:", 5, 20, 10)

            ultimos_partidos = []
            for _, row in partidos_equipo.head(cantidad).iterrows():
                es_local = row['home_team'] == equipo_seleccionado

                if es_local:
                    rival = row['away_team']
                    goles_favor = int(row['home_score'])
                    goles_contra = int(row['away_score'])
                    resultado = "✅ V" if goles_favor > goles_contra else ("🤝 E" if goles_favor == goles_contra else "❌ P")
                else:
                    rival = row['home_team']
                    goles_favor = int(row['away_score'])
                    goles_contra = int(row['home_score'])
                    resultado = "✅ V" if goles_favor > goles_contra else ("🤝 E" if goles_favor == goles_contra else "❌ P")

                ultimos_partidos.append({
                    'Fecha': row['date'].strftime('%d-%m-%Y'),
                    'Resultado': resultado,
                    'Goles': f"{goles_favor}",
                    'Rival': rival,
                    'Rival Goles': f"{goles_contra}",
                    'Torneo': row['tournament']
                })

            df_mostrar = pd.DataFrame(ultimos_partidos)

            st.dataframe(
                df_mostrar,
                column_config={
                    'Fecha': st.column_config.TextColumn("Fecha", width="small"),
                    'Resultado': st.column_config.TextColumn("Res.", width="small"),
                    'Goles': st.column_config.TextColumn("Goles", width="tiny"),
                    'Rival': st.column_config.TextColumn("Rival", width="medium"),
                    'Rival Goles': st.column_config.TextColumn("Goles", width="tiny"),
                    'Torneo': st.column_config.TextColumn("Torneo", width="medium"),
                },
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)

            victorias = (df_mostrar['Resultado'].str.contains('V')).sum()
            empates = (df_mostrar['Resultado'].str.contains('E')).sum()
            derrotas = (df_mostrar['Resultado'].str.contains('P')).sum()
            goles_a_favor = df_mostrar['Goles'].astype(int).sum()

            with col1:
                st.metric("✅ Victorias", victorias)
            with col2:
                st.metric("🤝 Empates", empates)
            with col3:
                st.metric("❌ Derrotas", derrotas)
            with col4:
                st.metric("⚽ Goles (últimos)", goles_a_favor)
        else:
            st.info(f"No hay datos de partidos para {equipo_seleccionado}")
    else:
        st.warning("⚠️ El archivo de histórico aún no está disponible.")

# ============================================================
# SECCIÓN: HISTÓRICO (PREDICCIONES VS RESULTADOS REALES)
# ============================================================
elif seccion == "Histórico":
    st.header("🏆 Histórico - Predicciones vs Resultados")

    if os.path.exists('predictions_historico.csv'):
        historico_df = pd.read_csv('predictions_historico.csv')

        if len(historico_df) > 0:
            st.markdown("""
            Esta tabla muestra todos los partidos ya jugados, con las predicciones
            del modelo y los resultados reales.

            - **Acierto 1X2**: ✓ si el modelo predijo bien si ganaba el local, empataba, o ganaba el visitante
            - **Acierto Marcador**: ✓ si el resultado real está entre los 3 marcadores más probables (Top1, Top2 o Top3)
            """)

            st.dataframe(
                historico_df,
                column_config={
                    'Fecha': st.column_config.TextColumn("Fecha", width="small"),
                    'Partido': st.column_config.TextColumn("Partido", width="medium"),
                    'Prob 1': st.column_config.NumberColumn("🏠 Local %", format="%.1f"),
                    'Prob X': st.column_config.NumberColumn("Empate %", format="%.1f"),
                    'Prob 2': st.column_config.NumberColumn("✈️ Visita %", format="%.1f"),
                    'xG Local': st.column_config.NumberColumn("xG Local", format="%.2f"),
                    'xG Visita': st.column_config.NumberColumn("xG Visita", format="%.2f"),
                    'Top1': st.column_config.TextColumn("Predicción", width="small"),
                    'Top2': st.column_config.TextColumn("Alt2", width="small"),
                    'Top3': st.column_config.TextColumn("Alt3", width="small"),
                    'Resultado Real': st.column_config.TextColumn("Resultado", width="small"),
                    'Acierto 1X2': st.column_config.TextColumn("1X2", width="small"),
                    'Acierto Marcador': st.column_config.TextColumn("Marcador", width="small"),
                },
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            st.subheader("📊 Estadísticas del Modelo")

            total = len(historico_df)
            aciertos_1x2 = (historico_df['Acierto 1X2'] == '✓').sum()
            aciertos_marcador = (historico_df['Acierto Marcador'] == '✓').sum()
            precision_1x2 = round(aciertos_1x2 / total * 100, 1) if total > 0 else 0
            precision_marcador = round(aciertos_marcador / total * 100, 1) if total > 0 else 0

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Partidos Jugados", total)
            with col2:
                st.metric("Acierto 1X2", f"{aciertos_1x2}/{total} ({precision_1x2}%)")
            with col3:
                st.metric("Acierto Marcador (Top1-3)", f"{aciertos_marcador}/{total} ({precision_marcador}%)")
        else:
            st.info("📝 No hay resultados aún.")
    else:
        st.info("📝 El histórico estará disponible cuando se jueguen los primeros partidos.")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p>Predictor Mundial 2026 | Desarrollado por Alejandro Castillo Palencia</p>
    <p>Modelos: Logistic Regression (1X2) + Random Forest (Goles esperados) + Poisson Distribution</p>
</div>
""", unsafe_allow_html=True)
