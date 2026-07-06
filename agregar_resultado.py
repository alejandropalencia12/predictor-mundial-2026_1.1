"""
agregar_resultado.py
Valida un resultado ingresado desde el formulario de GitHub Actions
(workflow_dispatch) contra pending_matches.csv, y si coincide, lo agrega
a resultados_manual.csv. Si no coincide con ningún partido pendiente,
falla con un mensaje claro en vez de agregar datos silenciosamente malos.
"""

import sys
import pandas as pd
import os

def main():
    home_team = sys.argv[1].strip()
    away_team = sys.argv[2].strip()
    home_score = sys.argv[3].strip()
    away_score = sys.argv[4].strip()

    # --- Validar que los goles sean números enteros no negativos ---
    try:
        home_score_int = int(home_score)
        away_score_int = int(away_score)
        if home_score_int < 0 or away_score_int < 0:
            raise ValueError
    except ValueError:
        print(f"ERROR: los goles deben ser números enteros >= 0. Recibido: "
              f"home_score='{home_score}', away_score='{away_score}'")
        sys.exit(1)

    # --- Validar que el partido exista en pending_matches.csv ---
    if not os.path.exists("pending_matches.csv"):
        print("ERROR: no se encontró pending_matches.csv. Corre primero el entrenamiento (train_model.py).")
        sys.exit(1)

    pendientes = pd.read_csv("pending_matches.csv")

    match = pendientes[
        (pendientes['home_team'].str.strip().str.lower() == home_team.lower()) &
        (pendientes['away_team'].str.strip().str.lower() == away_team.lower())
    ]

    if len(match) == 0:
        equipos_disponibles = sorted(set(pendientes['home_team']) | set(pendientes['away_team']))
        print(f"ERROR: no se encontró un partido pendiente '{home_team} vs {away_team}'.")
        print(f"Revisa que el nombre del equipo esté escrito exactamente como en pending_matches.csv.")
        print(f"Equipos disponibles: {', '.join(equipos_disponibles)}")
        sys.exit(1)

    fecha = match.iloc[0]['date']
    home_team_real = match.iloc[0]['home_team']  # usar el nombre exacto tal como está en el dataset
    away_team_real = match.iloc[0]['away_team']

    # --- Agregar a resultados_manual.csv (o crearlo si no existe) ---
    if os.path.exists("resultados_manual.csv"):
        manual_df = pd.read_csv("resultados_manual.csv")
    else:
        manual_df = pd.DataFrame(columns=['fecha', 'home_team', 'away_team', 'home_score', 'away_score'])

    # Evitar duplicados si ya se había agregado este resultado
    ya_existe = (
        (manual_df['home_team'] == home_team_real) &
        (manual_df['away_team'] == away_team_real) &
        (manual_df['fecha'] == str(fecha))
    ).any()

    if ya_existe:
        print(f"AVISO: {home_team_real} vs {away_team_real} ya estaba en resultados_manual.csv. No se duplicó.")
        sys.exit(0)

    nueva_fila = pd.DataFrame([{
        'fecha': str(fecha)[:10],  # formato YYYY-MM-DD
        'home_team': home_team_real,
        'away_team': away_team_real,
        'home_score': home_score_int,
        'away_score': away_score_int
    }])

    manual_df = pd.concat([manual_df, nueva_fila], ignore_index=True)
    manual_df.to_csv("resultados_manual.csv", index=False)

    print(f"OK: agregado {home_team_real} {home_score_int}-{away_score_int} {away_team_real} "
          f"({str(fecha)[:10]}) a resultados_manual.csv")

    # --- Guardar en predictions_historico.csv: predicción vigente + resultado real ---
    # Esto hay que hacerlo AHORA, antes de que train_model.py recalcule
    # predictions.csv y la predicción de este partido se pierda.
    nombre_partido = f"{home_team_real} vs {away_team_real}"
    resultado_real_str = f"{home_score_int}-{away_score_int}"

    if os.path.exists("predictions.csv"):
        predicciones = pd.read_csv("predictions.csv")
        fila_pred = predicciones[predicciones['Partido'] == nombre_partido]
    else:
        fila_pred = pd.DataFrame()

    if len(fila_pred) == 0:
        print(f"AVISO: no se encontró una predicción previa para '{nombre_partido}' en predictions.csv. "
              f"No se puede registrar en predictions_historico.csv (¿ya se había procesado este partido?).")
    else:
        p = fila_pred.iloc[0]

        # Acierto 1X2: ¿el modelo predijo bien local/empate/visitante?
        if home_score_int > away_score_int:
            real_1x2 = '1'
        elif home_score_int < away_score_int:
            real_1x2 = '2'
        else:
            real_1x2 = 'X'

        probs = {'1': p['Prob 1'], 'X': p['Prob X'], '2': p['Prob 2']}
        pred_1x2 = max(probs, key=probs.get)
        acierto_1x2 = '✓' if real_1x2 == pred_1x2 else '✗'

        # Acierto Marcador: ¿el resultado real está en Top1, Top2 o Top3?
        acierto_marcador = '✓' if resultado_real_str in [str(p['Top1']), str(p['Top2']), str(p['Top3'])] else '✗'

        fila_historico = pd.DataFrame([{
            'Fecha': p['Fecha'], 'Partido': nombre_partido,
            'Prob 1': p['Prob 1'], 'Prob X': p['Prob X'], 'Prob 2': p['Prob 2'],
            'xG Local': p.get('xG Local', ''), 'xG Visita': p.get('xG Visita', ''),
            'Top1': p['Top1'], 'Top2': p['Top2'], 'Top3': p['Top3'],
            'Resultado Real': resultado_real_str,
            'Acierto 1X2': acierto_1x2, 'Acierto Marcador': acierto_marcador
        }])

        if os.path.exists("predictions_historico.csv"):
            historico_pred = pd.read_csv("predictions_historico.csv")
            ya_registrado = (historico_pred['Partido'] == nombre_partido).any()
            if ya_registrado:
                print(f"AVISO: {nombre_partido} ya estaba en predictions_historico.csv. No se duplicó.")
                return
            historico_pred = pd.concat([historico_pred, fila_historico], ignore_index=True)
        else:
            historico_pred = fila_historico

        historico_pred.to_csv("predictions_historico.csv", index=False)
        print(f"OK: {nombre_partido} agregado a predictions_historico.csv "
              f"(1X2: {acierto_1x2}, Marcador: {acierto_marcador})")


if __name__ == "__main__":
    main()
