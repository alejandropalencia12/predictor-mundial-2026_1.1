import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="⚽ Predictor Mundial 2026",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Predictor de Resultados - Mundial 2026")

# DICCIONARIO DE BANDERAS (emojis de países)
BANDERAS = {
    'Argentina': '🇦🇷', 'Brazil': '🇧🇷', 'France': '🇫🇷', 'England': '🇬🇧',
    'Spain': '🇪🇸', 'Germany': '🇩🇪', 'Belgium': '🇧🇪', 'Italy': '🇮🇹',
    'Netherlands': '🇳🇱', 'Portugal': '🇵🇹', 'Uruguay': '🇺🇾', 'Mexico': '🇲🇽',
    'USA': '🇺🇸', 'Canada': '🇨🇦', 'Japan': '🇯🇵', 'South Korea': '🇰🇷',
    'Australia': '🇦🇺', 'New Zealand': '🇳🇿', 'Senegal': '🇸🇳', 'Tunisia': '🇹🇳',
    'Morocco': '🇲🇦', 'Egypt': '🇪🇬', 'Nigeria': '🇳🇬', 'Cameroon': '🇨🇲',
    'South Africa': '🇿🇦', 'Ghana': '🇬🇭', 'Ivory Coast': '🇨🇮', 'Saudi Arabia': '🇸🇦',
    'Iran': '🇮🇷', 'Iraq': '🇮🇶', 'Qatar': '🇶🇦', 'United Arab Emirates': '🇦🇪',
    'Costa Rica': '🇨🇷', 'Panama': '🇵🇦', 'Honduras': '🇭🇳', 'Jamaica': '🇯🇲',
    'Greece': '🇬🇷', 'Sweden': '🇸🇪', 'Poland': '🇵🇱', 'Turkey': '🇹🇷',
    'Ukraine': '🇺🇦', 'Austria': '🇦🇹', 'Czech Republic': '🇨🇿', 'Denmark': '🇩🇰',
    'Finland': '🇫🇮', 'Norway': '🇳🇴', 'Russia': '🇷🇺', 'Serbia': '🇷🇸',
    'Croatia': '🇭🇷', 'Slovenia': '🇸🇮', 'Slovakia': '🇸🇰', 'Romania': '🇷🇴',
    'Bulgaria': '🇧🇬', 'Hungary': '🇭🇺', 'Switzerland': '🇨🇭', 'Ireland': '🇮🇪',
    'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'Wales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿', 'Chile': '🇨🇱', 'Colombia': '🇨🇴',
    'Peru': '🇵🇪', 'Ecuador': '🇪🇨', 'Paraguay': '🇵🇾', 'Bolivia': '🇧🇴'
}

def get_bandera(equipo):
    """Retorna la bandera del equipo o un emoji genérico"""
    return BANDERAS.get(equipo, '⚽')

# Sidebar
with st.sidebar:
    st.header("🎯 Opciones")
    view_mode = st.radio(
        "Selecciona vista:",
        ["📊 Dashboard", "🔮 Predicciones", "👥 Por Equipo", "📈 Histórico"]
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
            partido = row['Partido']
            equipos = partido.split(' vs ')
            home = equipos[0].strip()
            away = equipos[1].strip() if len(equipos) > 1 else "?"
            
            col1, col2, col3, col4 = st.columns([2, 2, 1.5, 1])
            
            with col1:
                st.write(f"**{get_bandera(home)} {home}** vs **{away} {get_bandera(away)}**")
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
    
    # Agregar columna con banderas
    df_display = df_pred.copy()
    df_display['Equipo_Casa'] = df_display['Partido'].str.split(' vs ').str[0]
    df_display['Equipo_Visitante'] = df_display['Partido'].str.split(' vs ').str[1]
    
    df_display['Partido_con_Banderas'] = df_display.apply(
        lambda row: f"{get_bandera(row['Equipo_Casa'])} {row['Equipo_Casa']} vs {row['Equipo_Visitante']} {get_bandera(row['Equipo_Visitante'])}",
        axis=1
    )
    
    # Agregar columna de resultado (por ahora NA, se actualizará cuando haya resultados)
    df_display['Resultado_Real'] = 'N/A'
    
    # Mostrar tabla
    columnas_mostrar = ['Partido_con_Banderas', 'Prob 1', 'Prob X', 'Prob 2', 'Marcador', 'Confianza', 'Resultado_Real']
    df_mostrar = df_display[columnas_mostrar].copy()
    df_mostrar.columns = ['Partido', 'Prob 1', 'Prob X', 'Prob 2', 'Marcador', 'Confianza', 'Resultado Real']
    
    st.dataframe(df_mostrar, use_container_width=True, height=400)
    
    # Descargar
    csv = df_mostrar.to_csv(index=False)
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name="predicciones_mundial_2026.csv",
        mime="text/csv"
    )

# POR EQUIPO
elif view_mode == "👥 Por Equipo":
    st.subheader("Predicciones por Equipo")
    
    # Obtener lista de equipos
    todos_equipos = set()
    for partido in df_pred['Partido']:
        equipos = partido.split(' vs ')
        todos_equipos.add(equipos[0].strip())
        todos_equipos.add(equipos[1].strip())
    
    equipos_ordenados = sorted(list(todos_equipos))
    
    # Desplegable para seleccionar equipo
    equipo_seleccionado = st.selectbox(
        "🏆 Selecciona un equipo:",
        equipos_ordenados,
        format_func=lambda x: f"{get_bandera(x)} {x}"
    )
    
    # Filtrar partidos del equipo seleccionado
    partidos_equipo = df_pred[
        df_pred['Partido'].str.contains(equipo_seleccionado)
    ].copy()
    
    if len(partidos_equipo) > 0:
        st.write(f"### {get_bandera(equipo_seleccionado)} {equipo_seleccionado} - {len(partidos_equipo)} partidos")
        st.divider()
        
        for idx, row in partidos_equipo.iterrows():
            partido = row['Partido']
            equipos = partido.split(' vs ')
            home = equipos[0].strip()
            away = equipos[1].strip() if len(equipos) > 1 else "?"
            
            # Determinar si es local o visitante
            es_local = (home == equipo_seleccionado)
            
            col1, col2, col3, col4 = st.columns([2.5, 2, 1.5, 1])
            
            with col1:
                if es_local:
                    st.write(f"**{get_bandera(home)} {home}** 🏠 vs {away} {get_bandera(away)}")
                else:
                    st.write(f"{get_bandera(home)} {home} vs 🏠 **{away} {get_bandera(away)}**")
            
            with col2:
                prob_1 = row['Prob 1'] if 'Prob 1' in row else 0
                prob_x = row['Prob X'] if 'Prob X' in row else 0
                prob_2 = row['Prob 2'] if 'Prob 2' in row else 0
                
                if es_local:
                    st.write(f"1️⃣ {prob_1:.0f}% | ❌ {prob_x:.0f}% | 2️⃣ {prob_2:.0f}%")
                else:
                    st.write(f"2️⃣ {prob_2:.0f}% | ❌ {prob_x:.0f}% | 1️⃣ {prob_1:.0f}%")
            
            with col3:
                marcador = row['Marcador'] if 'Marcador' in row else "N/A"
                st.write(f"**{marcador}**")
            
            with col4:
                conf = row['Confianza'] if 'Confianza' in row else 0
                st.write(f"{conf:.1f}%")
            
            st.divider()
    else:
        st.info(f"ℹ️ {equipo_seleccionado} no tiene partidos predichos")

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
    st.info("📌 Los resultados se actualizarán cuando se jueguen los partidos en el CSV.")

st.divider()
st.caption("⚽ Predictor - Mundial 2026 | " + datetime.now().strftime("%d/%m/%Y %H:%M"))
