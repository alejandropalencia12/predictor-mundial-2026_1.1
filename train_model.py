"""
SCRIPT DE ENTRENAMIENTO - Ejecutar en Google Colab o local
Genera los archivos necesarios para la app Streamlit
"""

import pandas as pd
import numpy as np
import pickle
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("ENTRENAMIENTO DEL MODELO DE PREDICCIÓN - MUNDIAL 2026")
print("=" * 60)

# ==========================================
# 1. CARGAR DATOS HISTÓRICOS
# ==========================================

print("\n[1/7] Cargando datos históricos...")

try:
    # Si estás en Colab, descomenta estas líneas:
    # !pip install -q kaggle
    # !kaggle datasets download -d martj42/international-football-results-from-1872-to-2017
    # !unzip -o international-football-results-from-1872-to-2017.zip
    
    df = pd.read_csv("results.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # Separar histórico de pendientes
    historico = df[df['home_score'].notna()].copy()
    pendientes = df[df['home_score'].isna()].copy()
    
    print(f"✓ Datos cargados: {len(historico)} partidos jugados, {len(pendientes)} pendientes")
    
except Exception as e:
    print(f"❌ Error al cargar datos: {e}")
    exit(1)

# ==========================================
# 2. CONSTRUIR RATINGS ELO
# ==========================================

print("\n[2/7] Construyendo ratings ELO...")

from collections import defaultdict

K = 20

def expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_elo(rating_home, rating_away, resultado):
    exp_home = expected_score(rating_home, rating_away)
    exp_away = expected_score(rating_away, rating_home)
    
    new_home = rating_home + K * (resultado - exp_home)
    new_away = rating_away + K * ((1 - resultado) - exp_away)
    
    return new_home, new_away

historico = historico.sort_values('date')
elo = defaultdict(lambda: 1500)
elo_rows = []

for _, row in historico.iterrows():
    home = row['home_team']
    away = row['away_team']
    
    home_elo = elo[home]
    away_elo = elo[away]
    
    elo_rows.append({
        'date': row['date'],
        'home_team': home,
        'away_team': away,
        'home_elo': home_elo,
        'away_elo': away_elo,
        'elo_diff': home_elo - away_elo
    })
    
    if row['home_score'] > row['away_score']:
        resultado = 1
    elif row['home_score'] < row['away_score']:
        resultado = 0
    else:
        resultado = 0.5
    
    elo[home], elo[away] = update_elo(home_elo, away_elo, resultado)

elo_df = pd.DataFrame(elo_rows)
print(f"✓ ELO calculado para {len(elo)} equipos")

# ==========================================
# 3. CREAR LOOKUP ELO
# ==========================================

print("\n[3/7] Creando diccionario ELO...")

elo_lookup = {}
for _, row in elo_df.iterrows():
    key = (row['date'], row['home_team'], row['away_team'])
    elo_lookup[key] = {
        'home_elo': row['home_elo'],
        'away_elo': row['away_elo'],
        'elo_diff': row['elo_diff']
    }

print(f"✓ Lookup ELO creado: {len(elo_lookup)} registros")

# ==========================================
# 4. ESTADÍSTICAS DE EQUIPOS
# ==========================================

print("\n[4/7] Calculando estadísticas de equipos...")

def team_stats_before_match(team, fecha, n_matches):
    partidos = historico[
        ((historico['home_team'] == team) | (historico['away_team'] == team))
        & (historico['date'] < fecha)
    ].sort_values('date', ascending=False).head(n_matches)
    
    if len(partidos) == 0:
        return {'gf': 0, 'gc': 0, 'winrate': 0}
    
    gf = gc = wins = 0
    
    for _, p in partidos.iterrows():
        if p['home_team'] == team:
            gf += p['home_score']
            gc += p['away_score']
            if p['home_score'] > p['away_score']:
                wins += 1
        else:
            gf += p['away_score']
            gc += p['home_score']
            if p['away_score'] > p['home_score']:
                wins += 1
    
    return {'gf': gf / len(partidos), 'gc': gc / len(partidos), 'winrate': wins / len(partidos)}

# Dataset para ML (últimos años)
historico_ml = historico[historico['date'] >= '2020-01-01'].copy()

# Construir dataset con features
rows = []
for _, row in historico_ml.iterrows():
    fecha = row['date']
    home = row['home_team']
    away = row['away_team']
    
    home5 = team_stats_before_match(home, fecha, 5)
    away5 = team_stats_before_match(away, fecha, 5)
    home10 = team_stats_before_match(home, fecha, 10)
    away10 = team_stats_before_match(away, fecha, 10)
    
    key = (fecha, home, away)
    if key not in elo_lookup:
        continue
    
    elo_data = elo_lookup[key]
    
    if row['home_score'] > row['away_score']:
        target = 1
    elif row['home_score'] < row['away_score']:
        target = -1
    else:
        target = 0
    
    rows.append({
        'date': fecha,
        'tournament': row['tournament'],
        'home_team': home,
        'away_team': away,
        'home_gf_5': home5['gf'],
        'home_gc_5': home5['gc'],
        'away_gf_5': away5['gf'],
        'away_gc_5': away5['gc'],
        'home_gf_10': home10['gf'],
        'home_gc_10': home10['gc'],
        'away_gf_10': away10['gf'],
        'away_gc_10': away10['gc'],
        'home_winrate_5': home5['winrate'],
        'away_winrate_5': away5['winrate'],
        'home_winrate_10': home10['winrate'],
        'away_winrate_10': away10['winrate'],
        'home_elo': elo_data['home_elo'],
        'away_elo': elo_data['away_elo'],
        'elo_diff': elo_data['elo_diff'],
        'neutral': int(row['neutral']),
        'target': target
    })

dataset_xgb = pd.DataFrame(rows)
print(f"✓ Dataset creado: {len(dataset_xgb)} partidos")

# ==========================================
# 5. FEATURES DERIVADAS
# ==========================================

print("\n[5/7] Creando features derivadas...")

dataset_xgb['gf5_diff'] = dataset_xgb['home_gf_5'] - dataset_xgb['away_gf_5']
dataset_xgb['gc5_diff'] = dataset_xgb['home_gc_5'] - dataset_xgb['away_gc_5']
dataset_xgb['gf10_diff'] = dataset_xgb['home_gf_10'] - dataset_xgb['away_gf_10']
dataset_xgb['gc10_diff'] = dataset_xgb['home_gc_10'] - dataset_xgb['away_gc_10']
dataset_xgb['winrate5_diff'] = dataset_xgb['home_winrate_5'] - dataset_xgb['away_winrate_5']
dataset_xgb['winrate10_diff'] = dataset_xgb['home_winrate_10'] - dataset_xgb['away_winrate_10']

features = [
    'home_gf_5', 'home_gc_5', 'away_gf_5', 'away_gc_5',
    'home_gf_10', 'home_gc_10', 'away_gf_10', 'away_gc_10',
    'home_winrate_5', 'away_winrate_5', 'home_winrate_10', 'away_winrate_10',
    'home_elo', 'away_elo', 'elo_diff', 'neutral',
    'gf5_diff', 'gc5_diff', 'gf10_diff', 'gc10_diff',
    'winrate5_diff', 'winrate10_diff'
]

print(f"✓ Features: {len(features)} variables")

# ==========================================
# 6. ENTRENAR MODELOS
# ==========================================

print("\n[6/7] Entrenando modelos XGBoost y Random Forest...")

from xgboost import XGBClassifier, XGBRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Split train-test para clasificación (resultados)
X_train = dataset_xgb[dataset_xgb['date'] < '2025-01-01'][features]
y_train = dataset_xgb[dataset_xgb['date'] < '2025-01-01']['target']

# Entrenar clasificador
lr = XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    random_state=42,
    verbosity=0
)
lr.fit(X_train, y_train)

# Entrenar regresor de goles
home_goal_model = RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42)
away_goal_model = RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42)

home_goal_model.fit(X_train, dataset_xgb[dataset_xgb['date'] < '2025-01-01']['home_score'])
away_goal_model.fit(X_train, dataset_xgb[dataset_xgb['date'] < '2025-01-01']['away_score'])

print("✓ Modelos entrenados")

# ==========================================
# 7. GENERAR PREDICCIONES MUNDIAL 2026
# ==========================================

print("\n[7/7] Generando predicciones para Mundial 2026...")

from scipy.stats import poisson

# Variables globales para el modelo
elo_actual = elo.copy()
historico_complete = historico.copy()

def build_match_features(home, away):
    """Construye features para un partido"""
    fecha = pd.Timestamp.now()
    
    home5 = team_stats_before_match(home, fecha, 5)
    away5 = team_stats_before_match(away, fecha, 5)
    home10 = team_stats_before_match(home, fecha, 10)
    away10 = team_stats_before_match(away, fecha, 10)
    
    home_elo_val = elo_actual.get(home, 1500)
    away_elo_val = elo_actual.get(away, 1500)
    
    return pd.DataFrame({
        'home_gf_5': [home5['gf']],
        'home_gc_5': [home5['gc']],
        'away_gf_5': [away5['gf']],
        'away_gc_5': [away5['gc']],
        'home_gf_10': [home10['gf']],
        'home_gc_10': [home10['gc']],
        'away_gf_10': [away10['gf']],
        'away_gc_10': [away10['gc']],
        'home_winrate_5': [home5['winrate']],
        'away_winrate_5': [away5['winrate']],
        'home_winrate_10': [home10['winrate']],
        'away_winrate_10': [away10['winrate']],
        'home_elo': [home_elo_val],
        'away_elo': [away_elo_val],
        'elo_diff': [home_elo_val - away_elo_val],
        'neutral': [1],
        'gf5_diff': [home5['gf'] - away5['gf']],
        'gc5_diff': [home5['gc'] - away5['gc']],
        'gf10_diff': [home10['gf'] - away10['gf']],
        'gc10_diff': [home10['gc'] - away10['gc']],
        'winrate5_diff': [home5['winrate'] - away5['winrate']],
        'winrate10_diff': [home10['winrate'] - away10['winrate']]
    })

# Generar predicciones para partidos pendientes
tabla_quiniela = []

for _, row in pendientes.iterrows():
    home = row['home_team']
    away = row['away_team']
    
    try:
        x = build_match_features(home, away)
        probas = lr.predict_proba(x)[0]
        
        lambda_home = home_goal_model.predict(x)[0]
        lambda_away = away_goal_model.predict(x)[0]
        
        # Encontrar mejor marcador
        mejor_score = None
        mejor_prob = 0
        
        for hg in range(7):
            for ag in range(7):
                p = poisson.pmf(hg, lambda_home) * poisson.pmf(ag, lambda_away)
                if p > mejor_prob:
                    mejor_prob = p
                    mejor_score = f"{hg}-{ag}"
        
        tabla_quiniela.append({
            'Fecha': row['date'],
            'Partido': f"{home} vs {away}",
            'Prob 1': round(probas[2]*100, 1),
            'Prob X': round(probas[1]*100, 1),
            'Prob 2': round(probas[0]*100, 1),
            'Marcador': mejor_score,
            'Confianza': round(mejor_prob*100, 2)
        })
    except Exception as e:
        print(f"⚠️ Error prediciendo {home} vs {away}: {e}")
        continue

tabla_quiniela_df = pd.DataFrame(tabla_quiniela)

# ==========================================
# 8. GUARDAR RESULTADOS
# ==========================================

print("\n[GUARDANDO ARCHIVOS]")

# Guardar predicciones
tabla_quiniela_df.to_csv('predictions.csv', index=False)
print("✓ predictions.csv guardado")

# Guardar datos históricos
historico.to_csv('historical_data.csv', index=False)
print("✓ historical_data.csv guardado")

# Guardar partidos pendientes
pendientes.to_csv('pending_matches.csv', index=False)
print("✓ pending_matches.csv guardado")

# Guardar modelos
models = {
    'classifier': lr,
    'home_goal_model': home_goal_model,
    'away_goal_model': away_goal_model,
    'features': features,
    'elo': elo_actual
}

with open('models.pkl', 'wb') as f:
    pickle.dump(models, f)
print("✓ models.pkl guardado")

# ==========================================
# RESUMEN FINAL
# ==========================================

print("\n" + "=" * 60)
print("✅ ENTRENAMIENTO COMPLETADO")
print("=" * 60)
print(f"\n📊 Predicciones generadas: {len(tabla_quiniela_df)}")
print(f"📅 Rango de fechas: {tabla_quiniela_df['Fecha'].min()} - {tabla_quiniela_df['Fecha'].max()}")
print(f"🎯 Confianza promedio: {tabla_quiniela_df['Confianza'].mean():.2f}%")
print("\n📁 Archivos generados:")
print("   - predictions.csv")
print("   - historical_data.csv")
print("   - pending_matches.csv")
print("   - models.pkl")
print("\n✨ ¡La app está lista para usar!")
