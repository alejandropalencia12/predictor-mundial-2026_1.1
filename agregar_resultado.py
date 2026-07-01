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


if __name__ == "__main__":
    main()
