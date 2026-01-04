"""
EMBERHOLM PORTAL - DATABASE MODULE
PostgreSQL wrapper para reemplazar JSON files con persistencia real

Este módulo mantiene la MISMA INTERFAZ que las funciones JSON originales
para garantizar compatibilidad con app.py sin romper nada.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
from datetime import datetime

# =========================================================================
# CONFIGURACIÓN
# =========================================================================

DATABASE_URL = os.environ.get('DATABASE_URL')

# Connection pool (reutiliza conexiones para mejor performance)
connection_pool = None

def init_connection_pool():
    """Inicializar connection pool de PostgreSQL"""
    global connection_pool
    if connection_pool is None and DATABASE_URL:
        try:
            connection_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=DATABASE_URL
            )
            print("✅ PostgreSQL connection pool initialized")
        except Exception as e:
            print(f"❌ Error initializing PostgreSQL pool: {e}")
            connection_pool = None

def get_connection():
    """Obtener conexión del pool"""
    if connection_pool:
        return connection_pool.getconn()
    return None

def release_connection(conn):
    """Devolver conexión al pool"""
    if connection_pool and conn:
        connection_pool.putconn(conn)

def is_postgresql_available():
    """Check si PostgreSQL está disponible"""
    return DATABASE_URL is not None and connection_pool is not None

# =========================================================================
# NFTs DATABASE FUNCTIONS
# =========================================================================

def load_nfts_database():
    """
    Cargar toda la base de datos de NFTs desde PostgreSQL.
    Retorna dict compatible con JSON: {token_id: nft_data, ...}

    🔥 COMPATIBLE con código original que usaba load_json("nfts_database.json")
    """
    if not is_postgresql_available():
        return {}

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    token_id,
                    name,
                    guild,
                    race_class,
                    last_known_owner,
                    image_url,
                    dynamic_state,
                    last_update
                FROM nfts
            """)
            rows = cur.fetchall()

            # Convertir a formato dict original
            nfts_db = {}
            for row in rows:
                nfts_db[row['token_id']] = {
                    'token_id': row['token_id'],
                    'name': row['name'],
                    'guild': row['guild'],
                    'race_class': row['race_class'],
                    'last_known_owner': row['last_known_owner'],
                    'image_url': row.get('image_url', '/img/emissary-placeholder.png'),
                    'dynamic_state': row['dynamic_state'],
                    'last_update': row['last_update'].isoformat() if row['last_update'] else None
                }

            return nfts_db
    except Exception as e:
        print(f"❌ Error loading NFTs database: {e}")
        return {}
    finally:
        release_connection(conn)

def save_nfts_database(nfts_db):
    """
    Guardar toda la base de datos de NFTs a PostgreSQL.
    Acepta dict compatible con JSON: {token_id: nft_data, ...}

    🔥 COMPATIBLE con código original que usaba save_json("nfts_database.json", data)
    """
    if not is_postgresql_available():
        return False

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for token_id, nft_data in nfts_db.items():
                cur.execute("""
                    INSERT INTO nfts (
                        token_id, name, guild, race_class,
                        last_known_owner, image_url, dynamic_state, last_update
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (token_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        guild = EXCLUDED.guild,
                        race_class = EXCLUDED.race_class,
                        last_known_owner = EXCLUDED.last_known_owner,
                        image_url = EXCLUDED.image_url,
                        dynamic_state = EXCLUDED.dynamic_state,
                        last_update = NOW()
                """, (
                    token_id,
                    nft_data.get('name'),
                    nft_data.get('guild'),
                    nft_data.get('race_class'),
                    nft_data.get('last_known_owner'),
                    nft_data.get('image_url', '/img/emissary-placeholder.png'),
                    Json(nft_data.get('dynamic_state', {}))
                ))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error saving NFTs database: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

def get_nft_from_database(token_id):
    """
    Obtener un NFT específico desde PostgreSQL.

    🔥 COMPATIBLE con código original
    """
    if not is_postgresql_available():
        return None

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    token_id, name, guild, race_class,
                    last_known_owner, image_url, dynamic_state, last_update
                FROM nfts
                WHERE token_id = %s
            """, (token_id,))

            row = cur.fetchone()
            if row:
                return {
                    'token_id': row['token_id'],
                    'name': row['name'],
                    'guild': row['guild'],
                    'race_class': row['race_class'],
                    'last_known_owner': row['last_known_owner'],
                    'image_url': row.get('image_url', '/img/emissary-placeholder.png'),
                    'dynamic_state': row['dynamic_state'],
                    'last_update': row['last_update'].isoformat() if row['last_update'] else None
                }
            return None
    except Exception as e:
        print(f"❌ Error getting NFT {token_id}: {e}")
        return None
    finally:
        release_connection(conn)

def update_nft_dynamic_state(token_id, dynamic_state):
    """
    Actualizar solo el dynamic_state de un NFT.

    🔥 COMPATIBLE con código original
    """
    if not is_postgresql_available():
        return False

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE nfts
                SET dynamic_state = %s, last_update = NOW()
                WHERE token_id = %s
            """, (Json(dynamic_state), token_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating NFT {token_id} dynamic state: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

# =========================================================================
# ACTIVE MISSIONS FUNCTIONS
# =========================================================================

def load_active_missions():
    """
    Cargar todas las misiones activas desde PostgreSQL.
    Retorna dict compatible: {mission_key: mission_data, ...}

    🔥 COMPATIBLE con load_json("active_missions.json")
    🔥 UPDATED: Includes hero_ids and is_party for party missions
    """
    if not is_postgresql_available():
        return {}

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    mission_key, wallet, hero_id, hero_ids, mission_id,
                    start_time, duration_hours, is_party
                FROM active_missions
            """)
            rows = cur.fetchall()

            missions = {}
            for row in rows:
                mission_data = {
                    'wallet': row['wallet'],
                    'hero_id': row['hero_id'],
                    'mission_id': row['mission_id'],
                    'start_time': row['start_time'].isoformat() if row['start_time'] else None,
                    'duration_hours': row['duration_hours'],
                    'is_party': row.get('is_party') or False
                }
                # Include hero_ids for party missions
                hero_ids = row.get('hero_ids')
                if hero_ids:
                    if isinstance(hero_ids, str):
                        import json as json_lib
                        mission_data['hero_ids'] = json_lib.loads(hero_ids)
                    else:
                        mission_data['hero_ids'] = hero_ids
                missions[row['mission_key']] = mission_data

            return missions
    except Exception as e:
        print(f"❌ Error loading active missions: {e}")
        return {}
    finally:
        release_connection(conn)

def save_active_missions(missions_dict):
    """
    Guardar todas las misiones activas a PostgreSQL usando UPSERT.
    Acepta dict: {mission_key: mission_data, ...}

    🔥 COMPATIBLE con save_json("active_missions.json", data)
    🔥 FIXED: Uses UPSERT instead of DELETE ALL - preserves existing missions
    🔥 UPDATED: Includes hero_ids and is_party for party missions
    """
    if not is_postgresql_available():
        return False

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Get existing keys to know which to delete
            cur.execute("SELECT mission_key FROM active_missions")
            existing_keys = set(row[0] for row in cur.fetchall())

            # Delete missions that are no longer in the dict
            current_keys = set(missions_dict.keys())
            keys_to_delete = existing_keys - current_keys
            if keys_to_delete:
                for key in keys_to_delete:
                    cur.execute("DELETE FROM active_missions WHERE mission_key = %s", (key,))
                print(f"  🗑️ Removed {len(keys_to_delete)} completed missions")

            # UPSERT current missions (INSERT or UPDATE if exists)
            for mission_key, mission_data in missions_dict.items():
                # Handle hero_ids for party missions
                hero_ids = mission_data.get('hero_ids')
                hero_ids_json = None
                if hero_ids:
                    import json as json_lib
                    hero_ids_json = json_lib.dumps(hero_ids)

                # Parse start_time if it's a string with 'Z'
                start_time = mission_data.get('start_time')
                if isinstance(start_time, str):
                    start_time = start_time.replace('Z', '+00:00')

                cur.execute("""
                    INSERT INTO active_missions (
                        mission_key, wallet, hero_id, hero_ids, mission_id,
                        start_time, duration_hours, is_party
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (mission_key) DO UPDATE SET
                        wallet = EXCLUDED.wallet,
                        hero_id = EXCLUDED.hero_id,
                        hero_ids = EXCLUDED.hero_ids,
                        mission_id = EXCLUDED.mission_id,
                        start_time = EXCLUDED.start_time,
                        duration_hours = EXCLUDED.duration_hours,
                        is_party = EXCLUDED.is_party
                """, (
                    mission_key,
                    mission_data.get('wallet'),
                    mission_data.get('hero_id'),
                    hero_ids_json,
                    mission_data.get('mission_id'),
                    start_time,
                    mission_data.get('duration_hours'),
                    mission_data.get('is_party', False)
                ))
        conn.commit()
        print(f"✅ Saved {len(missions_dict)} active missions to PostgreSQL")
        return True
    except Exception as e:
        print(f"❌ Error saving active missions: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        release_connection(conn)

def add_active_mission(mission_key, mission_data):
    """
    Agregar una misión activa (helper rápido)
    🔥 UPDATED: Includes hero_ids and is_party for party missions
    """
    if not is_postgresql_available():
        return False

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Handle hero_ids for party missions
            hero_ids = mission_data.get('hero_ids')
            hero_ids_json = None
            if hero_ids:
                import json as json_lib
                hero_ids_json = json_lib.dumps(hero_ids)

            # Parse start_time if it's a string with 'Z'
            start_time = mission_data.get('start_time')
            if isinstance(start_time, str):
                start_time = start_time.replace('Z', '+00:00')

            cur.execute("""
                INSERT INTO active_missions (
                    mission_key, wallet, hero_id, hero_ids, mission_id,
                    start_time, duration_hours, is_party
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (mission_key) DO UPDATE SET
                    wallet = EXCLUDED.wallet,
                    hero_id = EXCLUDED.hero_id,
                    hero_ids = EXCLUDED.hero_ids,
                    mission_id = EXCLUDED.mission_id,
                    start_time = EXCLUDED.start_time,
                    duration_hours = EXCLUDED.duration_hours,
                    is_party = EXCLUDED.is_party
            """, (
                mission_key,
                mission_data.get('wallet'),
                mission_data.get('hero_id'),
                hero_ids_json,
                mission_data.get('mission_id'),
                start_time,
                mission_data.get('duration_hours'),
                mission_data.get('is_party', False)
            ))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error adding active mission: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

def remove_active_mission(mission_key):
    """Eliminar una misión activa (helper rápido)"""
    if not is_postgresql_available():
        return False

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM active_missions WHERE mission_key = %s", (mission_key,))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error removing active mission: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

# =========================================================================
# PLAYERS FUNCTIONS (Session cache)
# =========================================================================

def load_players():
    """
    Cargar todos los players desde PostgreSQL.
    Retorna dict: {wallet: player_data, ...}

    🔥 COMPATIBLE con load_json("players.json")
    """
    if not is_postgresql_available():
        return {}

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT wallet, player_data FROM players")
            rows = cur.fetchall()

            players = {}
            for row in rows:
                players[row['wallet']] = row['player_data']

            return players
    except Exception as e:
        print(f"❌ Error loading players: {e}")
        return {}
    finally:
        release_connection(conn)

def save_players(players_dict):
    """
    Guardar todos los players a PostgreSQL.

    🔥 COMPATIBLE con save_json("players.json", data)
    """
    if not is_postgresql_available():
        return False

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for wallet, player_data in players_dict.items():
                cur.execute("""
                    INSERT INTO players (wallet, player_data, last_update)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (wallet) DO UPDATE SET
                        player_data = EXCLUDED.player_data,
                        last_update = NOW()
                """, (wallet, Json(player_data)))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error saving players: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

# =========================================================================
# STATS FUNCTIONS
# =========================================================================

def load_stats():
    """
    Cargar stats globales desde PostgreSQL.

    🔥 COMPATIBLE con load_json("stats.json")
    """
    if not is_postgresql_available():
        return {
            "total_characters": 0,
            "active_guilds": 6,
            "missions_completed": 0,
            "missions_failed": 0,
            "total_exp_collected": 0,
            "total_aura_collected": 0,
            "guild_ranking": [],
            "player_leaderboard": []
        }

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT stats_data FROM global_stats WHERE id = 1")
            row = cur.fetchone()
            return row['stats_data'] if row else {}
    except Exception as e:
        print(f"❌ Error loading stats: {e}")
        return {}
    finally:
        release_connection(conn)

def save_stats(stats_data):
    """
    Guardar stats globales a PostgreSQL.

    🔥 COMPATIBLE con save_json("stats.json", data)
    """
    if not is_postgresql_available():
        return False

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE global_stats
                SET stats_data = %s, last_update = NOW()
                WHERE id = 1
            """, (Json(stats_data),))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error saving stats: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

# =========================================================================
# GENERIC LOAD/SAVE (Wrapper para otros archivos JSON)
# =========================================================================

def load_json_or_db(filepath, default_value):
    """
    Helper genérico: intenta cargar desde PostgreSQL, si falla usa JSON.

    Mapeo de archivos:
    - nfts_database.json → load_nfts_database()
    - active_missions.json → load_active_missions()
    - players.json → load_players()
    - stats.json → load_stats()
    - Otros → load desde archivo JSON (guilds, missions_config, etc.)
    """
    filename = os.path.basename(filepath)

    if not is_postgresql_available():
        # Fallback a JSON file
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading {filename}: {e}")
        return default_value

    # Usar PostgreSQL
    if filename == "nfts_database.json":
        return load_nfts_database()
    elif filename == "active_missions.json":
        return load_active_missions()
    elif filename == "players.json":
        return load_players()
    elif filename == "stats.json":
        return load_stats()
    else:
        # Para otros archivos (guilds, missions_config), usar JSON
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading {filename}: {e}")
        return default_value

def save_json_or_db(filepath, data):
    """
    Helper genérico: intenta guardar a PostgreSQL, si falla usa JSON.
    """
    filename = os.path.basename(filepath)

    if not is_postgresql_available():
        # Fallback a JSON file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️ Error saving {filename}: {e}")
            return False

    # Usar PostgreSQL
    if filename == "nfts_database.json":
        return save_nfts_database(data)
    elif filename == "active_missions.json":
        return save_active_missions(data)
    elif filename == "players.json":
        return save_players(data)
    elif filename == "stats.json":
        return save_stats(data)
    else:
        # Para otros archivos (guilds, missions_config), usar JSON
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️ Error saving {filename}: {e}")
            return False

# =========================================================================
# USER BALANCES - EMBER GAMBIT ECONOMY
# =========================================================================

def ensure_user_balances_table():
    """
    Ensure user_balances table exists. Create it if it doesn't.
    """
    if not is_postgresql_available():
        return False

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_balances (
                    wallet VARCHAR(42) PRIMARY KEY,
                    ember_balance INTEGER DEFAULT 0,
                    ash_balance INTEGER DEFAULT 0,
                    gambit_rolls_today INTEGER DEFAULT 0,
                    gambit_rolls_max INTEGER DEFAULT 5,
                    gambit_next_reset TIMESTAMP,
                    last_update TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Create index if doesn't exist
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_balances_wallet
                ON user_balances(wallet)
            """)

        conn.commit()
        print("✅ user_balances table verified/created")
        return True
    except Exception as e:
        print(f"❌ Error ensuring user_balances table: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

def get_or_create_user_balance(wallet):
    """
    Get user balance, creating entry if doesn't exist.
    Returns dict with balance info or None on error.
    """
    if not is_postgresql_available():
        return {
            "ember_balance": 0,
            "ash_balance": 0,
            "gambit_rolls_today": 0,
            "gambit_rolls_max": 5,
            "gambit_next_reset": None
        }

    # Ensure table exists first
    ensure_user_balances_table()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Try to get existing balance
            cur.execute("""
                SELECT ember_balance, ash_balance, gambit_rolls_today,
                       gambit_rolls_max, gambit_next_reset
                FROM user_balances
                WHERE wallet = %s
            """, (wallet,))

            row = cur.fetchone()

            if row:
                return {
                    "ember_balance": row[0],
                    "ash_balance": row[1],
                    "gambit_rolls_today": row[2],
                    "gambit_rolls_max": row[3],
                    "gambit_next_reset": row[4]
                }

            # Create new entry with starting balance
            cur.execute("""
                INSERT INTO user_balances
                (wallet, ember_balance, ash_balance, gambit_rolls_today, gambit_rolls_max)
                VALUES (%s, 0, 0, 0, 5)
                RETURNING ember_balance, ash_balance, gambit_rolls_today,
                          gambit_rolls_max, gambit_next_reset
            """, (wallet,))

            row = cur.fetchone()
            conn.commit()

            return {
                "ember_balance": row[0],
                "ash_balance": row[1],
                "gambit_rolls_today": row[2],
                "gambit_rolls_max": row[3],
                "gambit_next_reset": row[4]
            }

    except Exception as e:
        print(f"❌ Error getting/creating user balance: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return None
    finally:
        release_connection(conn)

# =========================================================================
# INICIALIZACIÓN
# =========================================================================

# Auto-inicializar pool al importar el módulo
init_connection_pool()

# Initialize critical tables
if is_postgresql_available():
    ensure_user_balances_table()
