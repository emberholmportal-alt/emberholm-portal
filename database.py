"""
EMBERHOLM PORTAL - DATABASE MODULE
PostgreSQL wrapper para reemplazar JSON files con persistencia real

Este módulo mantiene la MISMA INTERFAZ que las funciones JSON originales
para garantizar compatibilidad con app.py sin romper nada.
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

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
    """
    if not is_postgresql_available():
        return {}

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    mission_key, wallet, hero_id, mission_id,
                    start_time, duration_hours
                FROM active_missions
            """)
            rows = cur.fetchall()

            missions = {}
            for row in rows:
                missions[row['mission_key']] = {
                    'wallet': row['wallet'],
                    'hero_id': row['hero_id'],
                    'mission_id': row['mission_id'],
                    'start_time': row['start_time'].isoformat() if row['start_time'] else None,
                    'duration_hours': row['duration_hours']
                }

            return missions
    except Exception as e:
        print(f"❌ Error loading active missions: {e}")
        return {}
    finally:
        release_connection(conn)

def save_active_missions(missions_dict):
    """
    Guardar todas las misiones activas a PostgreSQL.
    Acepta dict: {mission_key: mission_data, ...}

    🔥 COMPATIBLE con save_json("active_missions.json", data)
    """
    if not is_postgresql_available():
        return False

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Limpiar tabla primero
            cur.execute("DELETE FROM active_missions")

            # Insertar todas las misiones
            for mission_key, mission_data in missions_dict.items():
                cur.execute("""
                    INSERT INTO active_missions (
                        mission_key, wallet, hero_id, mission_id,
                        start_time, duration_hours
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    mission_key,
                    mission_data.get('wallet'),
                    mission_data.get('hero_id'),
                    mission_data.get('mission_id'),
                    mission_data.get('start_time'),
                    mission_data.get('duration_hours')
                ))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error saving active missions: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)

def add_active_mission(mission_key, mission_data):
    """Agregar una misión activa (helper rápido)"""
    if not is_postgresql_available():
        return False

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO active_missions (
                    mission_key, wallet, hero_id, mission_id,
                    start_time, duration_hours
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (mission_key) DO UPDATE SET
                    wallet = EXCLUDED.wallet,
                    hero_id = EXCLUDED.hero_id,
                    mission_id = EXCLUDED.mission_id,
                    start_time = EXCLUDED.start_time,
                    duration_hours = EXCLUDED.duration_hours
            """, (
                mission_key,
                mission_data.get('wallet'),
                mission_data.get('hero_id'),
                mission_data.get('mission_id'),
                mission_data.get('start_time'),
                mission_data.get('duration_hours')
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
# 🔥 ATOMIC TRANSACTIONS - ACID Compliance
# =========================================================================

class DatabaseTransaction:
    """
    Context manager para transacciones ACID en PostgreSQL.

    Usage:
        with DatabaseTransaction() as (conn, cur):
            cur.execute("UPDATE ...")
            cur.execute("INSERT ...")
            # Auto-commit al salir sin excepciones
            # Auto-rollback si hay excepción
    """
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        if not is_postgresql_available():
            raise RuntimeError("PostgreSQL not available")

        self.conn = get_connection()
        if not self.conn:
            raise RuntimeError("Could not get database connection")

        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        return self.conn, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                # No exceptions - commit transaction
                self.conn.commit()
                logger.info("✅ Transaction committed successfully")
            else:
                # Exception occurred - rollback
                self.conn.rollback()
                logger.error(f"❌ Transaction rolled back due to: {exc_val}")
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                release_connection(self.conn)

        # Don't suppress exceptions
        return False

def atomic_mission_complete(hero_id, xp_gain, aura_gain, mission_id, wallet):
    """
    Complete mission with ACID transaction.

    This ensures:
    - NFT dynamic_state is updated
    - Stats are updated
    - Active mission is removed
    - All changes commit together or rollback together

    Args:
        hero_id: Token ID of hero
        xp_gain: XP to add
        aura_gain: Aura to add
        mission_id: Mission ID
        wallet: Player wallet address

    Returns:
        bool: Success status

    Raises:
        Exception: If transaction fails
    """
    if not is_postgresql_available():
        return False

    try:
        with DatabaseTransaction() as (conn, cur):
            # 1. Update NFT dynamic state
            cur.execute("""
                UPDATE nfts
                SET dynamic_state = jsonb_set(
                    jsonb_set(
                        dynamic_state,
                        '{xp_total}',
                        (COALESCE((dynamic_state->>'xp_total')::int, 0) + %s)::text::jsonb
                    ),
                    '{aura_level}',
                    (COALESCE((dynamic_state->>'aura_level')::int, 0) + %s)::text::jsonb
                ),
                last_update = NOW()
                WHERE token_id = %s
            """, (xp_gain, aura_gain, hero_id))

            # 2. Update global stats
            cur.execute("""
                UPDATE global_stats
                SET stats_data = jsonb_set(
                    jsonb_set(
                        stats_data,
                        '{missions_completed}',
                        (COALESCE((stats_data->>'missions_completed')::int, 0) + 1)::text::jsonb
                    ),
                    '{total_exp_collected}',
                    (COALESCE((stats_data->>'total_exp_collected')::int, 0) + %s)::text::jsonb
                ),
                last_update = NOW()
                WHERE id = 1
            """, (xp_gain,))

            # 3. Remove active mission
            cur.execute("""
                DELETE FROM active_missions
                WHERE mission_key = %s
            """, (f"{wallet}_{hero_id}",))

            # Transaction will auto-commit here
            return True

    except Exception as e:
        logger.error(f"❌ Atomic mission complete failed: {e}", exc_info=True)
        raise

# =========================================================================
# 🔥 AUDIT LOG TABLE
# =========================================================================

def log_operation(operation_type, entity_type, entity_id, details=None):
    """
    Log an operation to audit trail.

    Args:
        operation_type: 'INSERT', 'UPDATE', 'DELETE', 'MISSION_START', 'MISSION_COMPLETE', etc.
        entity_type: 'NFT', 'MISSION', 'PLAYER', 'STATS'
        entity_id: ID of entity affected
        details: Optional JSON details
    """
    if not is_postgresql_available():
        return

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO audit_log (operation_type, entity_type, entity_id, details)
                VALUES (%s, %s, %s, %s)
            """, (operation_type, entity_type, entity_id, Json(details or {})))
        conn.commit()
    except Exception as e:
        logger.warning(f"Failed to log operation: {e}")
        conn.rollback()
    finally:
        release_connection(conn)

# =========================================================================
# INICIALIZACIÓN
# =========================================================================

# Auto-inicializar pool al importar el módulo
init_connection_pool()
