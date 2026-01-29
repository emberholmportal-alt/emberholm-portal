#!/usr/bin/env python3
"""
EMBERHOLM MINI APP - Seed Micro Missions
=========================================
Este script carga las micro-misiones desde archivos JSON a la base de datos PostgreSQL.

Uso:
    python seed_micro_missions.py

Requisitos:
    - PostgreSQL database configurada (DATABASE_URL)
    - Tablas de mini app creadas (schema.sql ejecutado)
"""

import os
import json
import sys
from datetime import datetime

# Configurar path para importar database module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import database as db
    from psycopg2.extras import Json
except ImportError as e:
    print(f"Error importing database module: {e}")
    print("Make sure psycopg2-binary is installed: pip install psycopg2-binary")
    sys.exit(1)

# Directorio donde están los archivos JSON de micro-misiones
MICRO_MISSIONS_DIR = os.path.join(os.path.dirname(__file__), "data", "micro-missions")


def load_micro_mission_from_json(filepath):
    """Carga una micro-misión desde un archivo JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def seed_micro_mission(conn, mission_data):
    """Inserta o actualiza una micro-misión en la base de datos"""

    # Extraer datos del JSON
    mission_id = mission_data['id']
    name = mission_data['name']
    description = mission_data.get('description', '')
    difficulty = mission_data['difficulty']
    duration_seconds = mission_data['duration_seconds']
    energy_cost = mission_data.get('energy_cost', 0)

    pyre_reward = mission_data.get('pyre_reward', {})
    pyre_reward_min = pyre_reward.get('min', 10)
    pyre_reward_max = pyre_reward.get('max', 20)

    xp_reward = mission_data.get('xp_reward', {})
    xp_reward_min = xp_reward.get('min', 0)
    xp_reward_max = xp_reward.get('max', 0)

    ember_reward = mission_data.get('ember_reward', {})
    ember_reward_min = ember_reward.get('min', 0)
    ember_reward_max = ember_reward.get('max', 0)

    aura_chance = mission_data.get('aura_chance', 0)
    cooldown_minutes = mission_data.get('cooldown_minutes', 0)
    is_active = mission_data.get('is_active', True)

    # Narrativa
    narrative = mission_data.get('narrative', {})
    narrative_intro = narrative.get('intro', '')
    narrative_choices = narrative.get('choices', [])
    narrative_outcomes = narrative.get('outcomes', {})

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO micro_missions (
                id, name, description, difficulty, duration_seconds,
                energy_cost, pyre_reward_min, pyre_reward_max,
                xp_reward_min, xp_reward_max, ember_reward_min, ember_reward_max,
                aura_chance, narrative_intro, narrative_choices, narrative_outcomes,
                cooldown_minutes, is_active
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                difficulty = EXCLUDED.difficulty,
                duration_seconds = EXCLUDED.duration_seconds,
                energy_cost = EXCLUDED.energy_cost,
                pyre_reward_min = EXCLUDED.pyre_reward_min,
                pyre_reward_max = EXCLUDED.pyre_reward_max,
                xp_reward_min = EXCLUDED.xp_reward_min,
                xp_reward_max = EXCLUDED.xp_reward_max,
                ember_reward_min = EXCLUDED.ember_reward_min,
                ember_reward_max = EXCLUDED.ember_reward_max,
                aura_chance = EXCLUDED.aura_chance,
                narrative_intro = EXCLUDED.narrative_intro,
                narrative_choices = EXCLUDED.narrative_choices,
                narrative_outcomes = EXCLUDED.narrative_outcomes,
                cooldown_minutes = EXCLUDED.cooldown_minutes,
                is_active = EXCLUDED.is_active
        """, (
            mission_id, name, description, difficulty, duration_seconds,
            energy_cost, pyre_reward_min, pyre_reward_max,
            xp_reward_min, xp_reward_max, ember_reward_min, ember_reward_max,
            aura_chance, narrative_intro, Json(narrative_choices), Json(narrative_outcomes),
            cooldown_minutes, is_active
        ))

    return mission_id


def main():
    """Función principal que carga todas las micro-misiones"""

    print("=" * 60)
    print("EMBERHOLM MINI APP - Seed Micro Missions")
    print("=" * 60)
    print()

    # Verificar que PostgreSQL está disponible
    if not db.is_postgresql_available():
        print("ERROR: PostgreSQL no está disponible.")
        print("Asegúrate de que DATABASE_URL está configurada correctamente.")
        sys.exit(1)

    # Verificar que el directorio existe
    if not os.path.exists(MICRO_MISSIONS_DIR):
        print(f"ERROR: Directorio no encontrado: {MICRO_MISSIONS_DIR}")
        sys.exit(1)

    # Listar archivos JSON
    json_files = [f for f in os.listdir(MICRO_MISSIONS_DIR) if f.endswith('.json')]

    if not json_files:
        print(f"No se encontraron archivos JSON en {MICRO_MISSIONS_DIR}")
        sys.exit(1)

    print(f"Encontrados {len(json_files)} archivos de micro-misiones:")
    for f in sorted(json_files):
        print(f"  - {f}")
    print()

    # Cargar cada micro-misión
    loaded = 0
    errors = 0

    try:
        with db.get_db() as conn:
            for filename in sorted(json_files):
                filepath = os.path.join(MICRO_MISSIONS_DIR, filename)
                try:
                    mission_data = load_micro_mission_from_json(filepath)
                    mission_id = seed_micro_mission(conn, mission_data)

                    difficulty = mission_data['difficulty']
                    name = mission_data['name']

                    print(f"  [{difficulty}] {mission_id}: {name}")
                    loaded += 1

                except json.JSONDecodeError as e:
                    print(f"  ERROR parsing {filename}: {e}")
                    errors += 1
                except KeyError as e:
                    print(f"  ERROR missing key in {filename}: {e}")
                    errors += 1
                except Exception as e:
                    print(f"  ERROR loading {filename}: {e}")
                    errors += 1

            # Commit solo si no hubo errores
            if errors == 0:
                conn.commit()
                print()
                print(f"SUCCESS: Loaded {loaded} micro-missions")
            else:
                conn.rollback()
                print()
                print(f"ROLLED BACK due to {errors} errors")

    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Verificar carga
    print()
    print("Verificando micro-misiones en la base de datos...")

    try:
        with db.get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, difficulty, duration_seconds,
                           pyre_reward_min, pyre_reward_max, is_active
                    FROM micro_missions
                    ORDER BY difficulty, id
                """)
                rows = cur.fetchall()

                print()
                print(f"Total micro-misiones en BD: {len(rows)}")
                print("-" * 60)
                print(f"{'ID':<10} {'Nombre':<25} {'Diff':<8} {'Dur':<6} {'$PYRE':<12}")
                print("-" * 60)

                for row in rows:
                    mission_id, name, diff, dur, spark_min, spark_max, active = row
                    status = "" if active else "(INACTIVE)"
                    print(f"{mission_id:<10} {name[:24]:<25} {diff:<8} {dur:<6} {spark_min}-{spark_max:<6} {status}")

    except Exception as e:
        print(f"Error verificando: {e}")

    print()
    print("=" * 60)
    print("Seed completado!")
    print("=" * 60)


if __name__ == "__main__":
    main()
