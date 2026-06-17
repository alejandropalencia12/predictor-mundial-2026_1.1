import streamlit as st
import pandas as pd
import numpy as np
import pickle
import sqlite3
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================

st.set_page_config(
    page_title="⚽ Predictor Mundial 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
    <style>
    .prediction-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .match-title {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .prob-high {
        color: #2ecc71;
        font-weight: bold;
    }
    .prob-medium {
        color: #f39c12;
        font-weight: bold;
    }
    .prob-low {
        color: #e74c3c;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# INICIALIZAR BASE DE DATOS
# ==========================================

@st.cache_resource
def init_db():
    conn = sqlite3.connect('predictions.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY,
            date TEXT,
            home_team TEXT,
            away_team TEXT,
            prob_home REAL,
            prob_draw REAL,
            prob_away REAL,
            predicted_score TEXT,
            confidence REAL,
            actual_home_score INTEGER,
            actual_away_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# ==========================================
# CARGAR MODELOS Y DATOS
# ==========================================

@st.cache_resource
def load_models():
    """Carga los modelos entrenados"""
    try:
        with open('models.pkl', 'rb') as f:
            models = pickle.load(f)
        return models
    except:
        st.error("⚠️ Modelos no encontrados. Primero ejecuta el script de entrenamiento.")
        return None

@st.cache_data
def load_prediction_data():
    """Carga datos históricos y dataset"""
    try:
        df_historical = pd.read_csv('historical_data.csv')
        df_pending = pd.read_csv('pending_matches.csv')
        df_predictions = pd.read_csv('predictions.csv')
        return df_historical, df_pending, df_predictions
    except:
        return None, None, None

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def get_prob_color(prob):
    """Retorna color según probabilidad"""
    if prob > 60:
        return "prob-high"
    elif prob > 40:
        return "prob-medium"
    else:
        return "prob-low"

def format_probability(prob):
    """Formatea probabilidad con emoji"""
    if prob > 60:
        return f"<span class='prob-high'>🔥 {prob:.1f}%</span>"
    elif prob > 40:
        return f"<span class='prob-medium'>⚖️ {prob:.1f}%</span>"
    else:
        return f"<span class='prob-low'>❄️ {prob:.1f}%</span>"

def save_prediction_to_db(row):
    """Guarda predicción en la base de datos"""
    c = conn.cursor()
    c.execute('''
        INSERT INTO predictions 
        (date, home_team, away_team, prob_home, prob_draw, prob_away, predicted_score, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        row['Fecha'],
        row['Partido'].split(' vs ')[0],
        row['Partido'].split(' vs ')[1],
        row['Prob 1'],
        row['Prob X'],
        row['Prob 2'],
        row['Marcador'],
        row['Confianza']
    ))
    conn.commit()

def update_match_result(match_id, home_score, away_score):
    """Actualiza el resultado real de un partido"""
    c = conn.cursor()
    c.execute('''
        UPDATE predictions 
        SET actual_home_score = ?, actual_away_score = ?
        WHERE id = ?
    ''', (home_score, away_score, match_id))
    conn.commit()

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

st.title("⚽ Predictor de Resultados - Mundial 2026")

# Sidebar
with st.sidebar:
    st.header("🎯 Opciones")
    
    view_mode = st.radio(
        "Selecciona vista:",
        ["📊 Dashboard", "🔮 Predicciones", "📈 Histórico", "⚙️ Admin"],
        key="view_mode"
    )
    
    st.divider()
    
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("✅ Datos actualizados")
        st.rerun()

# ==========================================
# VISTA: DASHBOARD
# ==========================================

if view_mode == "📊 Dashboard":
    st.subheader("Resumen de Predicciones")
    
    df_hist, df_pending, df_pred = load_prediction_data()
    
    if df_pred is not None:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📅 Total Partidos", len(df_pred))
        
        with col2:
            st.metric("⏳ Pendientes", len(df_pred[df_pred['Confianza'].notna()]))
        
        with col3:
            if len(df_hist) > 0:
                st.metric("✅ Jugados", len(df_hist))
        
        with col4:
            st.metric("🎯 Confianza Promedio", f"{df_pred['Confianza'].mean():.1f}%")
        
        st.divider()
        
        # Próximos 5 partidos
        st.subheader("🔜 Próximos Partidos")
        
        if len(df_pred) > 0:
            for idx, row in df_pred.head(10).iterrows():
                col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1])
                
                with col1:
                    st.markdown(f"**{row['Partido']}**")
                    st.caption(f"📅 {row['Fecha']}")
                
                with col2:
                    st.markdown(f"<div class='prediction-box'>"
                               f"1️⃣ {format_probability(row['Prob 1'])}<br>"
                               f"❌ {format_probability(row['Prob X'])}<br>"
                               f"2️⃣ {format_probability(row['Prob 2'])}"
                               f"</div>", unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"<div class='prediction-box'>"
                               f"<strong>Marcador:</strong><br>"
                               f"{row['Marcador']}<br>"
                               f"<small>Confianza: {row['Confianza']:.1f}%</small>"
                               f"</div>", unsafe_allow_html=True)
                
                with col4:
                    if st.button("✏️ Resultado", key=f"result_{idx}"):
                        st.session_state[f"show_result_{idx}"] = True
                
                if st.session_state.get(f"show_result_{idx}"):
                    col_h, col_a = st.columns(2)
                    with col_h:
                        h_score = st.number_input(f"Goles {row['Partido'].split(' vs ')[0]}", 
                                                 min_value=0, key=f"h_{idx}")
                    with col_a:
                        a_score = st.number_input(f"Goles {row['Partido'].split(' vs ')[1]}", 
                                                 min_value=0, key=f"a_{idx}")
                    
                    if st.button("💾 Guardar", key=f"save_{idx}"):
                        st.success(f"✅ Resultado guardado: {h_score}-{a_score}")
                
                st.divider()

# ==========================================
# VISTA: PREDICCIONES
# ==========================================

elif view_mode == "🔮 Predicciones":
    st.subheader("Tabla Completa de Predicciones")
    
    df_hist, df_pending, df_pred = load_prediction_data()
    
    if df_pred is not None:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            equipos = sorted(pd.concat([
                df_pred['Partido'].str.split(' vs ').str[0],
                df_pred['Partido'].str.split(' vs ').str[1]
            ]).unique())
            selected_team = st.multiselect("🏆 Filtrar por equipo", equipos)
        
        with col2:
            min_confidence = st.slider("Confianza mínima", 0, 100, 0)
        
        with col3:
            sort_by = st.selectbox("Ordenar por", ["Fecha", "Confianza", "Probabilidad"])
        
        # Filtrar
        df_filtered = df_pred.copy()
        
        if selected_team:
            mask = df_filtered['Partido'].str.contains('|'.join(selected_team))
            df_filtered = df_filtered[mask]
        
        df_filtered = df_filtered[df_filtered['Confianza'] >= min_confidence]
        
        if sort_by == "Confianza":
            df_filtered = df_filtered.sort_values('Confianza', ascending=False)
        elif sort_by == "Probabilidad":
            df_filtered = df_filtered.sort_values('Prob 1', ascending=False)
        
        # Mostrar tabla
        st.dataframe(
            df_filtered,
            use_container_width=True,
            height=400,
            column_config={
                "Fecha": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Prob 1": st.column_config.NumberColumn(format="%.1f%%"),
                "Prob X": st.column_config.NumberColumn(format="%.1f%%"),
                "Prob 2": st.column_config.NumberColumn(format="%.1f%%"),
                "Confianza": st.column_config.NumberColumn(format="%.2f%%"),
            }
        )
        
        # Descargar
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name="predicciones_mundial_2026.csv",
            mime="text/csv"
        )

# ==========================================
# VISTA: HISTÓRICO
# ==========================================

elif view_mode == "📈 Histórico":
    st.subheader("Resultados Históricos")
    
    df_hist, df_pending, df_pred = load_prediction_data()
    
    if df_hist is not None and len(df_hist) > 0:
        c = conn.cursor()
        c.execute('SELECT * FROM predictions WHERE actual_home_score IS NOT NULL')
        played_matches = c.fetchall()
        
        if played_matches:
            col_names = [description[0] for description in c.description]
            df_results = pd.DataFrame(played_matches, columns=col_names)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                correct = sum([
                    (row['actual_home_score'] > row['actual_away_score'] and row['prob_home'] > 50) or
                    (row['actual_away_score'] > row['actual_home_score'] and row['prob_away'] > 50) or
                    (row['actual_home_score'] == row['actual_away_score'] and row['prob_draw'] > 50)
                    for _, row in df_results.iterrows()
                ])
                st.metric("✅ Aciertos", f"{correct}/{len(df_results)}")
            
            with col2:
                accuracy = (correct / len(df_results) * 100) if len(df_results) > 0 else 0
                st.metric("🎯 Precisión", f"{accuracy:.1f}%")
            
            with col3:
                avg_confidence = df_results['confidence'].mean()
                st.metric("📊 Confianza Promedio", f"{avg_confidence:.2f}%")
            
            st.divider()
            st.dataframe(df_results, use_container_width=True)
        else:
            st.info("ℹ️ Aún no hay resultados registrados")
    else:
        st.info("ℹ️ Sin datos históricos disponibles")

# ==========================================
# VISTA: ADMINISTRACIÓN
# ==========================================

elif view_mode == "⚙️ Admin":
    st.subheader("Panel de Administración")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 📊 Información de Base de Datos")
        
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM predictions')
        total_preds = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM predictions WHERE actual_home_score IS NOT NULL')
        completed_preds = c.fetchone()[0]
        
        st.metric("Total Predicciones", total_preds)
        st.metric("Resultados Registrados", completed_preds)
        
        if st.button("🗑️ Limpiar Base de Datos", use_container_width=True):
            c.execute('DELETE FROM predictions')
            conn.commit()
            st.success("✅ Base de datos limpiada")
    
    with col2:
        st.write("### 📁 Archivos Disponibles")
        
        files = {
            'models.pkl': '🤖 Modelos Entrenados',
            'historical_data.csv': '📊 Datos Históricos',
            'pending_matches.csv': '⏳ Partidos Pendientes',
            'predictions.csv': '🔮 Predicciones'
        }
        
        for filename, description in files.items():
            if os.path.exists(filename):
                size = os.path.getsize(filename) / 1024
                st.write(f"✅ {description}: {size:.1f} KB")
            else:
                st.write(f"❌ {description}: No encontrado")
        
        st.info("📌 Para actualizar los modelos y datos, ejecuta el script de entrenamiento")

# ==========================================
# FOOTER
# ==========================================

st.divider()
st.caption("⚽ Predictor de Resultados - Mundial 2026 | Última actualización: " + datetime.now().strftime("%d/%m/%Y %H:%M"))
