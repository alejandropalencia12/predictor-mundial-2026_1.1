"""
agregar_partido.py
Agrega un partido futuro (fixture) que el dataset de Kaggle ya no incluye
-- por ejemplo, cruces de cuartos de final que dependen de resultados
previos y que nadie podía anticipar de antemano.

A diferencia de agregar_resultado.py, este NO lleva marcador: solo anuncia
que ese cruce va a existir, para que el modelo pueda generar una predicción.
"""

import sys
import os
import pandas as pd


def main():
    home_team = sys.argv[1].strip()
    away_team = sys.argv[2].strip()
    fecha = sys.argv[3].strip()
    country = sys.argv[4].strip() if len(sys.argv) > 4 and sys.argv[4].strip() else ""
    tournament = sys.argv[5].strip() if len(sys.argv) > 5 and sys.argv[5].strip() else "FIFA World Cup"

    # --- Validar formato de fecha ---
    try:
        fecha_dt = pd.to_datetime(fecha)
    except Exception:
        print(f"ERROR: la fecha '{fecha}' no tiene un formato válido. Usa AAAA-MM-DD, por ejemplo 2026-07-11.")
        sys.exit(1)

    # --- Validar que no sea un duplicado exacto ---
    if os.path.exists("partidos_manual.csv"):
        partidos_df = pd.read_csv("partidos_manual.csv")
    else:
        partidos_df = pd.DataFrame(columns=['fecha', 'home_team', 'away_team', 'tournament', 'country', 'neutral'])

    ya_existe = (
        (partidos_df['home_team'] == home_team) &
        (partidos_df['away_team'] == away_team) &
        (pd.to_datetime(partidos_df['fecha']) == fecha_dt if len(partidos_df) > 0 else False)
    ).any() if len(partidos_df) > 0 else False

    if ya_existe:
        print(f"AVISO: {home_team} vs {away_team} ({fecha}) ya estaba en partidos_manual.csv. No se duplicó.")
        sys.exit(0)

    # --- Determinar sede efectiva y si es neutral ---
    # Si no se especifica país, se asume que el partido se juega en el país del local.
    country_efectivo = country if country else home_team
    neutral = not (country_efectivo == home_team or country_efectivo == away_team)

    nueva_fila = pd.DataFrame([{
        'fecha': fecha_dt.strftime('%Y-%m-%d'),
        'home_team': home_team,
        'away_team': away_team,
        'tournament': tournament,
        'country': country_efectivo,
        'neutral': neutral
    }])

    partidos_df = pd.concat([partidos_df, nueva_fila], ignore_index=True)
    partidos_df.to_csv("partidos_manual.csv", index=False)

    print(f"OK: agregado el partido {home_team} vs {away_team} ({fecha_dt.strftime('%Y-%m-%d')}) "
          f"[{tournament}, sede: {country_efectivo}, neutral: {neutral}]")


if __name__ == "__main__":
    main()
