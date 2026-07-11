"""
train_model.py
Pipeline completo de predicción Mundial 2026 — versión no interactiva para
correr en GitHub Actions. No depende de Colab ni de descargas manuales.

Requiere las variables de entorno KAGGLE_USERNAME y KAGGLE_KEY
(se configuran como GitHub Secrets, nunca en este archivo).
"""

import os
import subprocess
import pandas as pd
import numpy as np
import pickle
from collections import defaultdict
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from scipy.stats import poisson

print("=" * 60)
print("ENTRENAMIENTO AUTOMÁTICO - PREDICTOR MUNDIAL 2026")
print("=" * 60)

# ==========================================
# 1. CARGAR HISTÓRICO Y PENDIENTES (desde el propio repo)
# ==========================================
print("\n[1/9] Cargando historico y pendientes desde el repo...")

if not os.path.exists("historical_data.csv") or not os.path.exists("pending_matches.csv"):
    raise RuntimeError(
        "No se encontraron historical_data.csv / pending_matches.csv en el repo. "
        "Este script ahora usa esos archivos como fuente de datos (ya no descarga de Kaggle)."
    )

historico = pd.read_csv("historical_data.csv")
historico['date'] = pd.to_datetime(historico['date'])

pendientes = pd.read_csv("pending_matches.csv")
pendientes['date'] = pd.to_datetime(pendientes['date'])

print(f"Base repo: {len(historico)} jugados, {len(pendientes)} pendientes")

# ==========================================
# 2. INCORPORAR RESULTADOS MANUALES
# ==========================================
print("\n[2/9] Incorporando resultados_manual.csv...")

RUTA_MANUAL = "resultados_manual.csv"

if os.path.exists(RUTA_MANUAL):
    manual_df = pd.read_csv(RUTA_MANUAL)
else:
    manual_df = pd.DataFrame(columns=['fecha', 'home_team', 'away_team', 'home_score', 'away_score'])

if len(manual_df) > 0:
    manual_df['date'] = pd.to_datetime(manual_df['fecha'])
    manual_df = manual_df.sort_values('date')

    ya_existe = set(zip(historico['date'], historico['home_team'], historico['away_team']))
    nuevas_filas = []

    for _, row in manual_df.iterrows():
        key = (row['date'], row['home_team'], row['away_team'])
        if key in ya_existe:
            continue

        match_pend = pendientes[
            (pendientes['date'] == row['date']) &
            (pendientes['home_team'] == row['home_team']) &
            (pendientes['away_team'] == row['away_team'])
        ]
        tournament = match_pend.iloc[0]['tournament'] if len(match_pend) > 0 else 'FIFA World Cup'
        neutral = match_pend.iloc[0]['neutral'] if len(match_pend) > 0 else True

        nuevas_filas.append({
            'date': row['date'], 'home_team': row['home_team'], 'away_team': row['away_team'],
            'home_score': row['home_score'], 'away_score': row['away_score'],
            'tournament': tournament, 'city': None, 'country': None, 'neutral': neutral
        })

    if nuevas_filas:
        historico = pd.concat([historico, pd.DataFrame(nuevas_filas)], ignore_index=True) \
                      .sort_values('date').reset_index(drop=True)

        jugados_keys = {(r['date'], r['home_team'], r['away_team']) for r in nuevas_filas}
        pendientes = pendientes[
            ~pendientes.apply(lambda r: (r['date'], r['home_team'], r['away_team']) in jugados_keys, axis=1)
        ].reset_index(drop=True)

        print(f"{len(nuevas_filas)} resultado(s) manual(es) incorporado(s)")
    else:
        print("Resultados manuales ya estaban todos incorporados")
else:
    print("No hay resultados manuales pendientes de incorporar")

historico_ml = historico[historico['date'] >= '2020-01-01'].copy()

# ==========================================
# 2b. INCORPORAR PARTIDOS NUEVOS (fixtures que Kaggle ya no actualiza)
# ==========================================
print("\n[2b/9] Incorporando partidos_manual.csv...")

RUTA_PARTIDOS_MANUAL = "partidos_manual.csv"

if os.path.exists(RUTA_PARTIDOS_MANUAL):
    partidos_nuevos_df = pd.read_csv(RUTA_PARTIDOS_MANUAL)
else:
    partidos_nuevos_df = pd.DataFrame(columns=['fecha', 'home_team', 'away_team', 'tournament', 'country', 'neutral'])

if len(partidos_nuevos_df) > 0:
    partidos_nuevos_df['date'] = pd.to_datetime(partidos_nuevos_df['fecha'])

    ya_en_pendientes = set(zip(pendientes['date'], pendientes['home_team'], pendientes['away_team']))
    ya_en_historico = set(zip(historico['date'], historico['home_team'], historico['away_team']))

    filas_nuevas = []
    for _, row in partidos_nuevos_df.iterrows():
        key = (row['date'], row['home_team'], row['away_team'])
        if key in ya_en_pendientes or key in ya_en_historico:
            continue  # ya estaba, no duplicar
        filas_nuevas.append({
            'date': row['date'], 'home_team': row['home_team'], 'away_team': row['away_team'],
            'home_score': None, 'away_score': None,
            'tournament': row.get('tournament', 'FIFA World Cup'),
            'city': None, 'country': row.get('country', None),
            'neutral': row.get('neutral', True)
        })

    if filas_nuevas:
        pendientes = pd.concat([pendientes, pd.DataFrame(filas_nuevas)], ignore_index=True).sort_values('date').reset_index(drop=True)
        print(f"{len(filas_nuevas)} partido(s) nuevo(s) agregado(s) a pendientes")
    else:
        print("Los partidos en partidos_manual.csv ya estaban incorporados")
else:
    print("No hay partidos manuales nuevos que incorporar")

# ==========================================
# 3. ELO HISTÓRICO
# ==========================================
print("\n[3/9] Calculando ELO...")

K = 20

def expected_score(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))

def update_elo(rh, ra, resultado):
    eh, ea = expected_score(rh, ra), expected_score(ra, rh)
    return rh + K * (resultado - eh), ra + K * ((1 - resultado) - ea)

historico = historico.sort_values('date')
elo = defaultdict(lambda: 1500)
elo_rows = []

for _, row in historico.iterrows():
    home, away = row['home_team'], row['away_team']
    home_elo, away_elo = elo[home], elo[away]
    elo_rows.append({'date': row['date'], 'home_team': home, 'away_team': away,
                      'home_elo': home_elo, 'away_elo': away_elo, 'elo_diff': home_elo - away_elo})
    if row['home_score'] > row['away_score']:
        resultado = 1
    elif row['home_score'] < row['away_score']:
        resultado = 0
    else:
        resultado = 0.5
    elo[home], elo[away] = update_elo(home_elo, away_elo, resultado)

elo_df = pd.DataFrame(elo_rows)
elo_lookup = {
    (r['date'], r['home_team'], r['away_team']): {
        'home_elo': r['home_elo'], 'away_elo': r['away_elo'], 'elo_diff': r['elo_diff']
    } for _, r in elo_df.iterrows()
}
elo_actual = dict(elo)
print(f"ELO calculado para {len(elo_actual)} selecciones")

# ==========================================
# 4. FORMA RECIENTE (team_stats_before_match)
# ==========================================
print("\n[4/9] Calculando forma reciente...")

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
            gf += p['home_score']; gc += p['away_score']
            if p['home_score'] > p['away_score']: wins += 1
        else:
            gf += p['away_score']; gc += p['home_score']
            if p['away_score'] > p['home_score']: wins += 1
    n = len(partidos)
    return {'gf': gf / n, 'gc': gc / n, 'winrate': wins / n}

def team_drawrate_before_match(team, fecha, n_matches):
    partidos = historico[
        ((historico['home_team'] == team) | (historico['away_team'] == team))
        & (historico['date'] < fecha)
    ].sort_values('date', ascending=False).head(n_matches)
    if len(partidos) == 0:
        return 0
    empates = (partidos['home_score'] == partidos['away_score']).sum()
    return empates / len(partidos)

# ==========================================
# 5. RANKINGS FIFA / VALOR DE PLANTILLA
# ==========================================
print("\n[5/9] Cargando rankings FIFA...")

datos_selecciones = {
    'team': [
        'Canada', 'United States', 'Mexico', 'Panama', 'Curaçao', 'Haiti',
        'Argentina', 'Brazil', 'Uruguay', 'Colombia', 'Ecuador', 'Paraguay',
        'Germany', 'Austria', 'Belgium', 'Bosnia and Herzegovina', 'Croatia', 'Czech Republic',
        'Scotland', 'Spain', 'France', 'England', 'Norway', 'Netherlands',
        'Portugal', 'Serbia', 'Switzerland', 'Turkey', 'Algeria', 'Cape Verde',
        'Ivory Coast', 'Egypt', 'Ghana', 'Morocco', 'DR Congo',
        'Senegal', 'South Africa', 'Tunisia', 'Saudi Arabia', 'Australia', 'South Korea',
        'Iran', 'Japan', 'Jordan', 'Qatar', 'Uzbekistan', 'Iraq', 'New Zealand', 'Sweden'
    ],
    'ranking_fifa': [
        40, 18, 15, 41, 85, 90, 1, 5, 11, 12, 30, 56, 13, 22, 4, 75, 10, 36,
        39, 3, 2, 4, 45, 7, 6, 32, 19, 26, 43, 65, 38, 35, 64, 14, 62,
        17, 59, 28, 53, 24, 23, 20, 16, 70, 34, 68, 58, 104, 25
    ],
    'valor_plantilla_m': [
        180, 350, 220, 25, 12, 15, 850, 1000, 480, 280, 230, 110, 750, 280, 550, 60, 320, 150,
        210, 950, 1200, 1300, 450, 650, 980, 240, 260, 300, 190, 20, 320, 140, 160, 380, 70,
        340, 40, 110, 60, 40, 180, 50, 290, 15, 30, 35, 18, 10, 320
    ]
}
selecciones_df = pd.DataFrame(datos_selecciones)
ranking_dict = dict(zip(selecciones_df['team'], selecciones_df['ranking_fifa']))
valor_dict = dict(zip(selecciones_df['team'], selecciones_df['valor_plantilla_m']))

# ==========================================
# 6. DATASET DE FEATURES (vectorizado)
# ==========================================
print("\n[6/9] Construyendo dataset de features...")

historico_idx = historico.reset_index().rename(columns={'index': 'match_id'})

home_persp = pd.DataFrame({
    'match_id': historico_idx['match_id'], 'team': historico_idx['home_team'], 'date': historico_idx['date'],
    'gf': historico_idx['home_score'], 'gc': historico_idx['away_score'],
    'win': (historico_idx['home_score'] > historico_idx['away_score']).astype(int),
    'draw': (historico_idx['home_score'] == historico_idx['away_score']).astype(int), 'side': 'home'
})
away_persp = pd.DataFrame({
    'match_id': historico_idx['match_id'], 'team': historico_idx['away_team'], 'date': historico_idx['date'],
    'gf': historico_idx['away_score'], 'gc': historico_idx['home_score'],
    'win': (historico_idx['away_score'] > historico_idx['home_score']).astype(int),
    'draw': (historico_idx['home_score'] == historico_idx['away_score']).astype(int), 'side': 'away'
})
team_long = pd.concat([home_persp, away_persp], ignore_index=True).sort_values(['team', 'date', 'match_id']).reset_index(drop=True)

def rolling_stats(group, n):
    return pd.DataFrame({
        f'gf_{n}': group['gf'].rolling(n, min_periods=1).mean().shift(1),
        f'gc_{n}': group['gc'].rolling(n, min_periods=1).mean().shift(1),
        f'winrate_{n}': group['win'].rolling(n, min_periods=1).mean().shift(1),
        f'drawrate_{n}': group['draw'].rolling(n, min_periods=1).mean().shift(1),
    })

for n in [5, 10]:
    stats_n = team_long.groupby('team', group_keys=False)[['gf', 'gc', 'win', 'draw']].apply(rolling_stats, n=n)
    team_long = pd.concat([team_long, stats_n], axis=1)

stat_cols = [c for c in team_long.columns if c.startswith(('gf_', 'gc_', 'winrate_', 'drawrate_'))]
team_long[stat_cols] = team_long[stat_cols].fillna(0)

home_feats = team_long[team_long['side'] == 'home'][['match_id'] + stat_cols].rename(
    columns={c: f'home_{c.split("_")[0]}_{c.split("_")[1]}' for c in stat_cols})
away_feats = team_long[team_long['side'] == 'away'][['match_id'] + stat_cols].rename(
    columns={c: f'away_{c.split("_")[0]}_{c.split("_")[1]}' for c in stat_cols})

historico_ml_idx = historico_ml.reset_index().rename(columns={'index': 'match_id'})
dataset = historico_ml_idx.merge(home_feats, on='match_id', how='left').merge(away_feats, on='match_id', how='left')

def get_elo(row):
    data = elo_lookup.get((row['date'], row['home_team'], row['away_team']))
    if data is None:
        return pd.Series({'home_elo': 1500, 'away_elo': 1500, 'elo_diff': 0})
    return pd.Series(data)

dataset[['home_elo', 'away_elo', 'elo_diff']] = dataset.apply(get_elo, axis=1)

dataset['home_ranking'] = dataset['home_team'].map(ranking_dict).fillna(50)
dataset['away_ranking'] = dataset['away_team'].map(ranking_dict).fillna(50)
dataset['ranking_diff'] = dataset['away_ranking'] - dataset['home_ranking']
dataset['home_valor'] = dataset['home_team'].map(valor_dict).fillna(100)
dataset['away_valor'] = dataset['away_team'].map(valor_dict).fillna(100)
dataset['valor_diff'] = dataset['home_valor'] - dataset['away_valor']

dataset['target'] = np.select(
    [dataset['home_score'] > dataset['away_score'], dataset['home_score'] < dataset['away_score']],
    [1, -1], default=0
)
dataset['neutral'] = dataset['neutral'].astype(int)

dataset['gf5_diff'] = dataset['home_gf_5'] - dataset['away_gf_5']
dataset['gc5_diff'] = dataset['home_gc_5'] - dataset['away_gc_5']
dataset['gf10_diff'] = dataset['home_gf_10'] - dataset['away_gf_10']
dataset['gc10_diff'] = dataset['home_gc_10'] - dataset['away_gc_10']
dataset['winrate5_diff'] = dataset['home_winrate_5'] - dataset['away_winrate_5']
dataset['winrate10_diff'] = dataset['home_winrate_10'] - dataset['away_winrate_10']
dataset['drawrate5_avg'] = (dataset['home_drawrate_5'] + dataset['away_drawrate_5']) / 2
dataset['drawrate10_avg'] = (dataset['home_drawrate_10'] + dataset['away_drawrate_10']) / 2
dataset['abs_elo_diff'] = dataset['elo_diff'].abs()
dataset['abs_ranking_diff'] = dataset['ranking_diff'].abs()
dataset['abs_valor_diff'] = dataset['valor_diff'].abs()

dataset['is_friendly'] = (dataset['tournament'] == 'Friendly').astype(int)
dataset['is_world_cup'] = (dataset['tournament'] == 'FIFA World Cup').astype(int)
dataset['is_qualifier'] = dataset['tournament'].str.contains('qualification', case=False, na=False).astype(int)
dataset['is_nations_league'] = dataset['tournament'].str.contains('Nations League', case=False, na=False).astype(int)
dataset['is_continental_cup'] = dataset['tournament'].isin([
    'UEFA Euro', 'Copa América', 'Gold Cup', 'African Cup of Nations', 'AFC Asian Cup'
]).astype(int)

dataset_xgb = dataset

features = [
    'home_gf_5', 'home_gc_5', 'away_gf_5', 'away_gc_5',
    'home_gf_10', 'home_gc_10', 'away_gf_10', 'away_gc_10',
    'home_winrate_5', 'away_winrate_5', 'home_winrate_10', 'away_winrate_10',
    'home_drawrate_5', 'away_drawrate_5', 'home_drawrate_10', 'away_drawrate_10',
    'drawrate5_avg', 'drawrate10_avg',
    'home_elo', 'away_elo', 'elo_diff',
    'home_ranking', 'away_ranking', 'ranking_diff', 'abs_ranking_diff',
    'home_valor', 'away_valor', 'valor_diff', 'abs_valor_diff',
    'neutral',
    'gf5_diff', 'gc5_diff', 'gf10_diff', 'gc10_diff',
    'winrate5_diff', 'winrate10_diff', 'abs_elo_diff',
    'is_friendly', 'is_world_cup', 'is_qualifier', 'is_nations_league', 'is_continental_cup'
]

print(f"Dataset: {dataset_xgb.shape}, {len(features)} features")

# ==========================================
# 7. ENTRENAR MODELOS (producción: con todo el histórico)
# ==========================================
print("\n[7/9] Entrenando modelos...")

modelo_oficial = Pipeline([('scaler', StandardScaler()), ('model', LogisticRegression(max_iter=10000, random_state=42))])
modelo_oficial.fit(dataset_xgb[features], dataset_xgb['target'])

home_goal_model = RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42)
away_goal_model = RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42)
home_goal_model.fit(dataset_xgb[features], dataset_xgb['home_score'])
away_goal_model.fit(dataset_xgb[features], dataset_xgb['away_score'])

print("Modelos entrenados con", len(dataset_xgb), "partidos")

# ==========================================
# 8. PREDICCIONES PARA PARTIDOS PENDIENTES
# ==========================================
print("\n[8/9] Generando predicciones...")

HOST_ADVANTAGE = {"Mexico": 100, "United States": 100, "Canada": 100}

def build_match_features(home, away, fecha=None, country=None):
    if fecha is None:
        fecha = pd.Timestamp.today()
    home5 = team_stats_before_match(home, fecha, 5)
    away5 = team_stats_before_match(away, fecha, 5)
    home10 = team_stats_before_match(home, fecha, 10)
    away10 = team_stats_before_match(away, fecha, 10)

    # El bono de anfitrión solo aplica si el partido se juega REALMENTE en el
    # país de ese equipo. Ej: Canadá vs Marruecos en Houston -> Canadá NO
    # recibe el bono, porque no está jugando en su propio país.
    # Si no se especifica el país (llamadas manuales de prueba), se asume
    # que el equipo local juega en su país, para no romper usos existentes.
    bonus_home = HOST_ADVANTAGE.get(home, 0) if (country is None or country == home) else 0
    bonus_away = HOST_ADVANTAGE.get(away, 0) if (country == away) else 0

    home_elo = elo_actual.get(home, 1500) + bonus_home
    away_elo = elo_actual.get(away, 1500) + bonus_away
    home_ranking = ranking_dict.get(home, 150)
    away_ranking = ranking_dict.get(away, 150)
    home_valor = valor_dict.get(home, 0)
    away_valor = valor_dict.get(away, 0)

    fila = {
        'home_gf_5': home5['gf'], 'home_gc_5': home5['gc'], 'away_gf_5': away5['gf'], 'away_gc_5': away5['gc'],
        'home_gf_10': home10['gf'], 'home_gc_10': home10['gc'], 'away_gf_10': away10['gf'], 'away_gc_10': away10['gc'],
        'home_winrate_5': home5['winrate'], 'away_winrate_5': away5['winrate'],
        'home_winrate_10': home10['winrate'], 'away_winrate_10': away10['winrate'],
        'home_drawrate_5': team_drawrate_before_match(home, fecha, 5),
        'away_drawrate_5': team_drawrate_before_match(away, fecha, 5),
        'home_drawrate_10': team_drawrate_before_match(home, fecha, 10),
        'away_drawrate_10': team_drawrate_before_match(away, fecha, 10),
        'home_elo': home_elo, 'away_elo': away_elo, 'elo_diff': home_elo - away_elo,
        'abs_elo_diff': abs(home_elo - away_elo),
        'home_ranking': home_ranking, 'away_ranking': away_ranking,
        'ranking_diff': home_ranking - away_ranking, 'abs_ranking_diff': abs(home_ranking - away_ranking),
        'home_valor': home_valor, 'away_valor': away_valor,
        'valor_diff': home_valor - away_valor, 'abs_valor_diff': abs(home_valor - away_valor),
        'gf5_diff': home5['gf'] - away5['gf'], 'gc5_diff': home5['gc'] - away5['gc'],
        'gf10_diff': home10['gf'] - away10['gf'], 'gc10_diff': home10['gc'] - away10['gc'],
        'winrate5_diff': home5['winrate'] - away5['winrate'], 'winrate10_diff': home10['winrate'] - away10['winrate'],
        'neutral': 1, 'is_friendly': 0, 'is_world_cup': 1, 'is_qualifier': 0,
        'is_nations_league': 0, 'is_continental_cup': 0
    }
    fila['drawrate5_avg'] = (fila['home_drawrate_5'] + fila['away_drawrate_5']) / 2
    fila['drawrate10_avg'] = (fila['home_drawrate_10'] + fila['away_drawrate_10']) / 2
    return pd.DataFrame([fila])[features]

def top_scores(home, away, fecha=None, country=None, max_goals=6, top_n=3):
    x = build_match_features(home, away, fecha, country=country)
    lambda_home = home_goal_model.predict(x)[0]
    lambda_away = away_goal_model.predict(x)[0]
    resultados = []
    for hg in range(max_goals + 1):
        for ag in range(max_goals + 1):
            prob = poisson.pmf(hg, lambda_home) * poisson.pmf(ag, lambda_away)
            resultados.append({'marcador': f'{hg}-{ag}', 'probabilidad': prob})
    tabla = pd.DataFrame(resultados).sort_values('probabilidad', ascending=False).reset_index(drop=True)
    return tabla.head(top_n), lambda_home, lambda_away

MESES_ES = {1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
            7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'}

def formatear_fecha(fecha):
    return f"{fecha.day:02d}-{MESES_ES[fecha.month]}-{str(fecha.year)[2:]}"

filas = []
for _, row in pendientes.iterrows():
    home, away, fecha = row['home_team'], row['away_team'], row['date']
    pais_partido = row.get('country', None)
    x = build_match_features(home, away, fecha, country=pais_partido)
    probas = modelo_oficial.predict_proba(x)[0]
    top3, lambda_home, lambda_away = top_scores(home, away, fecha, country=pais_partido, top_n=3)
    marcadores = top3['marcador'].tolist()
    while len(marcadores) < 3:
        marcadores.append("-")
    filas.append({
        'Fecha': formatear_fecha(fecha), 'Partido': f"{home} vs {away}",
        'Prob 1': round(probas[2] * 100, 1), 'Prob X': round(probas[1] * 100, 1), 'Prob 2': round(probas[0] * 100, 1),
        'xG Local': round(lambda_home, 2), 'xG Visita': round(lambda_away, 2),
        'Top1': marcadores[0], 'Top2': marcadores[1], 'Top3': marcadores[2]
    })

tabla_predicciones = pd.DataFrame(filas)
print(f"{len(tabla_predicciones)} partidos predichos")

# ==========================================
# 9. EXPORTAR ARCHIVOS PARA STREAMLIT
# ==========================================
print("\n[9/9] Exportando archivos...")

tabla_predicciones.to_csv('predictions.csv', index=False)
historico.to_csv('historical_data.csv', index=False)
pendientes.to_csv('pending_matches.csv', index=False)

paquete_modelos = {
    'classifier': modelo_oficial,
    'home_goal_model': home_goal_model,
    'away_goal_model': away_goal_model,
    'features': features,
    'ranking_dict': ranking_dict,
    'valor_dict': valor_dict,
    'elo_actual': elo_actual,
    'host_advantage': HOST_ADVANTAGE,
}
with open('models.pkl', 'wb') as f:
    pickle.dump(paquete_modelos, f)

print("\n" + "=" * 60)
print("ENTRENAMIENTO COMPLETADO")
print("=" * 60)
print("Archivos generados: predictions.csv, historical_data.csv, pending_matches.csv, models.pkl")
