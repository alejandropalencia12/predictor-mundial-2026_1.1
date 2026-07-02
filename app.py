"""
app.py - Streamlit app para Predictor Mundial 2026
Con autenticación por contraseña
"""

import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import os

st.set_page_config(page_title="Predictor Mundial 2026", layout="wide", initial_sidebar_state="expanded")

# ============================================================
# AUTENTICACIÓN (CONTRASEÑA)
# ============================================================
def check_password():
    """Returns True si el usuario ingresa la contraseña correcta."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.markdown("""
        <div style='text-align: center; margin-top: 5rem;'>
            <h1>🔐 Predictor Mundial 2026</h1>
            <h3>Acceso Restringido</h3>
        </div>
        """, unsafe_allow_html=True)
        
        password = st.text_input("🔑 Ingresa la contraseña:", type="password", placeholder="Contraseña")
        
        if password:
            if password == "mundial2026":  # ← CAMBIA ESTO A TU CONTRASEÑA
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta. Intenta de nuevo.")
        return False
    return True

# Verificar contraseña antes de mostrar la app
if not check_password():
    st.stop()

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
    except:
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
        
        st.markdown("""
        ### ¿Cómo se generaron estas predicciones?
        
        El modelo usa múltiples factores para calcular la probabilidad de cada resultado:
        
        - **ELO Rating**: Sistema de calificación dinámico basado en resultados históricos
        - **Forma reciente**: Promedio de goles en últimos 5 y 10 partidos
        - **Rankings FIFA**: Posición oficial de cada selección
        - **Valor de plantilla**: Estimación de calidad de jugadores
        - **xG (Expected Goals)**: Goles esperados según oportunidades
        
        Con esta información, el modelo:
        1. Calcula la **probabilidad 1X2** (victoria local, empate, victoria visitante)
        2. Estima los **goles esperados** de cada equipo (xG)
        3. Usa la **distribución de Poisson** para generar los **3 marcadores más probables**
        """)
        
        st.dataframe(
            predictions_df,
            column_config={
                'Fecha': st.column_config.TextColumn("Fecha", width="small"),
                'Partido': st.column_config.TextColumn("Partido", width="medium"),
                'Prob 1': st.column_config.NumberColumn("🏠 Local %", format="%.1f"),
                'Prob X': st.column_config.NumberColumn("Empate %", format="%.1f"),
                'Prob 2': st.column_config.NumberColumn("✈️ Visita %", format="%.1f"),
                'xG Local': st.column_config.NumberColumn("xG Local", format="%.2f"),
                'xG Visita': st.column_config.NumberColumn("xG Visita", format="%.2f"),
                'Top1': st.column_config.TextColumn("🥇", width="small"),
                'Top2': st.column_config.TextColumn("🥈", width="small"),
                'Top3': st.column_config.TextColumn("🥉", width="small"),
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
        
        # Obtener lista de equipos únicos
        todos_equipos = sorted(
            set(historico_df
