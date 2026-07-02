"""
app.py - Streamlit app para Predictor Mundial 2026
Muestra predicciones pendientes e histórico de resultados
"""

import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Predictor Mundial 2026", layout="wide", initial_sidebar_state="expanded")

# ============================================================
# DICCIONARIO DE BANDERAS DE PAÍSES (SIMPLIFICADO)
# ============================================================
FLAGS = {
    'Canada': '🇨🇦', 'United States': '🇺🇸', 'Mexico': '🇲🇽', 'Panama': '🇵🇦', 'Haiti': '🇭🇹',
    'Argentina': '🇦🇷', 'Brazil': '🇧🇷', 'Uruguay': '🇺🇾', 'Colombia': '🇨🇴', 'Ecuador': '🇪🇨', 'Paraguay': '🇵🇾',
    'Germany': '🇩🇪', 'Austria': '🇦🇹', 'Belgium': '🇧🇪', 'Bosnia and Herzegovina': '🇧🇦', 'Croatia': '🇭🇷', 'Czech Republic': '🇨🇿',
    'Spain': '🇪🇸', 'France': '🇫🇷', 'England': '🇬🇧', 'Norway': '🇳🇴', 'Netherlands': '🇳🇱',
    'Portugal': '🇵🇹', 'Serbia': '🇷🇸', 'Switzerland': '🇨🇭', 'Turkey': '🇹🇷', 'Algeria': '🇩🇿', 'Cape Verde': '🇨🇻',
    'Ivory Coast': '🇨🇮', 'Egypt': '🇪🇬', 'Ghana': '🇬🇭', 'Morocco': '🇲🇦', 'DR Congo': '🇨🇩',
    'Senegal': '🇸🇳', 'South Africa': '🇿🇦', 'Tunisia': '🇹🇳', 'Saudi Arabia': '🇸🇦', 'Australia': '🇦🇺', 'South Korea': '🇰🇷',
    'Iran': '🇮🇷', 'Japan': '🇯🇵', 'Jordan': '🇯🇴', 'Qatar': '🇶🇦', 'Uzbekistan': '🇺🇿', 'Iraq': '🇮🇶', 'New Zealand': '🇳🇿', 'Sweden': '🇸🇪'
}

def get_flag(country):
    """Retorna la bandera del país o el nombre si no existe"""
    return FLAGS.get(country, country)

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
seccion = st.sidebar.radio("Selecciona una sección:", 
                           ["Predicciones", "Últimos Partidos", "Histórico", "Información"])

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
        Las predicciones se basan en:
        - **ELO Rating** de cada equipo
        - **Forma reciente** (últimos 5 y 10 partidos)
        - **Rankings FIFA** y valor de plantilla
        - **xG (Expected Goals)** - Fuerza de ataque
        """)
        
        st.dataframe(
            predictions_df,
            column_config={
                'Fecha': st.column_config.TextColumn("📅 Fecha", width="small"),
                'Partido': st.column_config.TextColumn("⚽ Partido", width="medium"),
                'Prob 1': st.column_config.NumberColumn("Local %", format="%.1f"),
                'Prob X': st.column_config.NumberColumn("Empate %", format="%.1f"),
                'Prob 2': st.column_config.NumberColumn("Visita %", format="%.1f"),
                'xG Local': st.column_config.NumberColumn("xG Local", format="%.2f"),
                'xG Visita': st.column_config.NumberColumn("xG Visita", format="%.2f"),
                'Top1': st.column_config.TextColumn("🥇 Top1", width="small"),
                'Top2': st.column_config.TextColumn("🥈 Top2", width="small"),
                'Top3': st.column_config.TextColumn("🥉 Top3", width="small"),
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
            set(historico_df['home_team'].unique()) | set(historico_df['away_team'].unique())
        )
        
        # Selector de equipo
        equipo_seleccionado = st.selectbox(
            "Selecciona un equipo:",
            todos_equipos,
            format_func=lambda x: f"{get_flag(x)} {x}"
        )
        
        # Filtrar partidos del equipo
        partidos_equipo = historico_df[
            (historico_df['home_team'] == equipo_seleccionado) | 
            (historico_df['away_team'] == equipo_seleccionado)
        ].sort_values('date', ascending=False)
        
        if len(partidos_equipo) > 0:
            # Selector de cantidad de partidos
            cantidad = st.slider("Últimos partidos a mostrar:", 5, 20, 10)
            
            # Preparar datos para mostrar
            ultimos_partidos = []
            for _, row in partidos_equipo.head(cantidad).iterrows():
                es_local = row['home_team'] == equipo_seleccionado
                
                if es_local:
                    rival = row['away_team']
                    goles_favor = int(row['home_score'])
                    goles_contra = int(row['away_score'])
                    resultado = "V" if goles_favor > goles_contra else ("E" if goles_favor == goles_contra else "P")
                else:
                    rival = row['home_team']
                    goles_favor = int(row['away_score'])
                    goles_contra = int(row['home_score'])
                    resultado = "V" if goles_favor > goles_contra else ("E" if goles_favor == goles_contra else "P")
                
                ultimos_partidos.append({
                    'Fecha': row['date'].strftime('%d-%m-%Y'),
                    'Resultado': resultado,
                    f'{equipo_seleccionado}': f"{goles_favor}",
                    'Rival': f"{get_flag(rival)} {rival}",
                    'Rival Goles': f"{goles_contra}",
                    'Torneo': row['tournament']
                })
            
            df_mostrar = pd.DataFrame(ultimos_partidos)
            
            st.dataframe(
                df_mostrar,
                column_config={
                    'Fecha': st.column_config.TextColumn("📅 Fecha", width="small"),
                    'Resultado': st.column_config.TextColumn("Res.", width="tiny"),
                    f'{equipo_seleccionado}': st.column_config.TextColumn("Goles", width="small"),
                    'Rival': st.column_config.TextColumn("Rival", width="medium"),
                    'Rival Goles': st.column_config.TextColumn("Goles", width="small"),
                    'Torneo': st.column_config.TextColumn("Torneo", width="medium"),
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Estadísticas rápidas
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            df_ultimos = df_mostrar.head(cantidad)
            victorias = (df_ultimos['Resultado'] == 'V').sum()
            empates = (df_ultimos['Resultado'] == 'E').sum()
            derrotas = (df_ultimos['Resultado'] == 'P').sum()
            goles_a_favor = df_ultimos[f'{equipo_seleccionado}'].astype(int).sum()
            
            with col1:
                st.metric("Victorias", victorias)
            with col2:
                st.metric("Empates", empates)
            with col3:
                st.metric("Derrotas", derrotas)
            with col4:
                st.metric("Goles (últimos)", goles_a_favor)
        else:
            st.info(f"No hay datos de partidos para {equipo_seleccionado}")
    else:
        st.warning("⚠️ El archivo de histórico aún no está disponible.")

# ============================================================
# SECCIÓN: HISTÓRICO (RESULTADOS DE DIECISÉISAVOS EN ADELANTE)
# ============================================================
elif seccion == "Histórico":
    st.header("🏆 Histórico - Predicciones vs Resultados (Dieciséisavos)")
    
    if os.path.exists('predictions_historico.csv'):
        historico_df = pd.read_csv('predictions_historico.csv')
        
        if len(historico_df) > 0:
            st.markdown("""
            Esta tabla muestra todos los partidos jugados desde dieciséisavos en adelante,
            con las predicciones del modelo y los resultados reales.
            
            - ✓ = Acertó el marcador Top1
            - ✗ = No acertó el marcador Top1
            """)
            
            st.dataframe(
                historico_df,
                column_config={
                    'Fecha': st.column_config.TextColumn("📅 Fecha", width="small"),
                    'Partido': st.column_config.TextColumn("⚽ Partido", width="medium"),
                    'Prob 1': st.column_config.NumberColumn("Local %", format="%.1f"),
                    'Prob X': st.column_config.NumberColumn("Empate %", format="%.1f"),
                    'Prob 2': st.column_config.NumberColumn("Visita %", format="%.1f"),
                    'xG Local': st.column_config.NumberColumn("xG Local", format="%.2f"),
                    'xG Visita': st.column_config.NumberColumn("xG Visita", format="%.2f"),
                    'Top1': st.column_config.TextColumn("Predicción", width="small"),
                    'Top2': st.column_config.TextColumn("Alt2", width="small"),
                    'Top3': st.column_config.TextColumn("Alt3", width="small"),
                    'Resultado Real': st.column_config.TextColumn("Resultado", width="small"),
                    'Acierto': st.column_config.TextColumn("Acierto", width="tiny"),
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Estadísticas
            st.markdown("---")
            st.subheader("📊 Estadísticas del Modelo")
            
            aciertos = (historico_df['Acierto'] == '✓').sum()
            total = len(historico_df)
            precision = round(aciertos / total * 100, 1) if total > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📈 Partidos Jugados", total)
            with col2:
                st.metric("🎯 Aciertos (Top1)", aciertos)
            with col3:
                st.metric("✅ Precisión", f"{precision}%")
            with col4:
                if precision >= 40:
                    st.metric("📊 Rendimiento", "Bueno ✓")
                elif precision >= 30:
                    st.metric("📊 Rendimiento", "Normal")
                else:
                    st.metric("📊 Rendimiento", "Por mejorar")
        else:
            st.info("📝 No hay resultados aún.")
    else:
        st.info("📝 El histórico estará disponible cuando se terminen los dieciséisavos.")

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
