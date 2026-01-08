"""
EMBERHOLM PORTAL - DATABASE MODULE
PostgreSQL wrapper optimizado para 35,000 NFTs y miles de wallets.

Arquitectura:
- ThreadedConnectionPool thread-safe
- Context manager con retry logic
- Batch operations para reducir queries
- Cache en memoria para reducir carga
"""

import os
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import ThreadedConnectionPool, PoolError
from contextlib import contextmanager
from datetime import datetime, timedelta

# =========================================================================
# CONFIGURACIÓN
# =========================================================================

DATABASE_URL = os.environ.get('DATABASE_URL')

# Connection pool (thread-safe para Flask/Gunicorn)
connection_pool = None

# =========================================================================
# CACHE EN MEMORIA
# =========================================================================

# Cache de NFTs por wallet (reduce queries dramáticamente)
_wallet_nfts_cache = {}
_wallet_cache_expiry = {}

# Cache de misiones activas por wallet
_wallet_missions_cache = {}
_missions_cache_expiry = {}

# Tiempo de expiración del cache (segundos)
CACHE_TTL_SECONDS = 30

def _cache_get(cache_dict, expiry_dict, key):
    """Obtener valor del cache si no ha expirado"""
    if key in cache_dict and key in expiry_dict:
        if datetime.now() < expiry_dict[key]:
            return cache_dict[key]
    return None

def _cache_set(cache_dict, expiry_dict, key, value, ttl=CACHE_TTL_SECONDS):
    """Guardar valor en cache con TTL"""
    cache_dict[key] = value
    expiry_dict[key] = datetime.now() + timedelta(seconds=ttl)

def invalidate_wallet_cache(wallet):
    """Invalidar cache de una wallet específica (llamar después de cambios)"""
    wallet = wallet.lower()
    _wallet_nfts_cache.pop(wallet, None)
    _wallet_cache_expiry.pop(wallet, None)
    _wallet_missions_cache.pop(wallet, None)
    _missions_cache_expiry.pop(wallet, None)

def clear_all_cache():
    """Limpiar todo el cache (para debug)"""
    _wallet_nfts_cache.clear()
    _wallet_cache_expiry.clear()
    _wallet_missions_cache.clear()
    _missions_cache_expiry.clear()
    _equipment_bonuses_cache.clear()

# =========================================================================
# 🔥 EQUIPMENT BONUSES CACHE
# =========================================================================

# Cache for equipment bonuses (5 minute TTL)
_equipment_bonuses_cache = {}
EQUIPMENT_CACHE_TTL = 300  # 5 minutes

def get_cached_equipment_bonuses(emissary_id):
    """
    Get cached equipment bonuses for an emissary.
    Returns cached value or None if not cached/expired.
    """
    cache_key = str(emissary_id).zfill(5)
    now = time.time()

    if cache_key in _equipment_bonuses_cache:
        cached = _equipment_bonuses_cache[cache_key]
        if now - cached['timestamp'] < EQUIPMENT_CACHE_TTL:
            return cached['bonuses']
        else:
            # Expired
            del _equipment_bonuses_cache[cache_key]
    return None

def set_cached_equipment_bonuses(emissary_id, bonuses):
    """Cache equipment bonuses for an emissary."""
    cache_key = str(emissary_id).zfill(5)
    _equipment_bonuses_cache[cache_key] = {
        'bonuses': bonuses,
        'timestamp': time.time()
    }

def invalidate_equipment_cache(emissary_id):
    """Invalidate equipment cache when equipment changes."""
    cache_key = str(emissary_id).zfill(5)
    if cache_key in _equipment_bonuses_cache:
        del _equipment_bonuses_cache[cache_key]
    print(f"🔄 Equipment cache invalidated for emissary {cache_key}")

# =========================================================================
# CONNECTION POOL (Optimized for scalability)
# =========================================================================

# Pool configuration - adjust based on deployment tier
POOL_MIN_CONN = int(os.environ.get('DB_POOL_MIN', 5))
POOL_MAX_CONN = int(os.environ.get('DB_POOL_MAX', 30))

def init_connection_pool():
    """Inicializar connection pool de PostgreSQL (thread-safe con retry)"""
    global connection_pool
    if connection_pool is None and DATABASE_URL:
        for attempt in range(3):
            try:
                connection_pool = ThreadedConnectionPool(
                    minconn=POOL_MIN_CONN,
                    maxconn=POOL_MAX_CONN,
                    dsn=DATABASE_URL
                )
                print(f"✅ PostgreSQL ThreadedConnectionPool initialized ({POOL_MIN_CONN}-{POOL_MAX_CONN} connections)")
                return True
            except Exception as e:
                print(f"❌ Pool init attempt {attempt+1}/3 failed: {e}")
                time.sleep(1)
        print("❌ Could not initialize connection pool after 3 attempts")
    return False

def get_connection():
    """Obtener conexión del pool con retry"""
    if not connection_pool:
        return None

    for attempt in range(3):
        try:
            conn = connection_pool.getconn()
            if conn:
                return conn
        except PoolError as e:
            print(f"⚠️ Pool exhausted, attempt {attempt+1}/3: {e}")
            time.sleep(0.2 * (attempt + 1))  # Backoff: 0.2s, 0.4s, 0.6s
        except Exception as e:
            print(f"❌ Error getting connection: {e}")
            break
    return None

def release_connection(conn):
    """Devolver conexión al pool (SIEMPRE llamar esto!)"""
    if connection_pool and conn:
        try:
            connection_pool.putconn(conn)
        except Exception as e:
            print(f"⚠️ Error releasing connection: {e}")

@contextmanager
def get_db():
    """
    Context manager para conexiones de DB - SIEMPRE garantiza liberación.

    Uso:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT ...")
    """
    conn = None
    try:
        conn = get_connection()
        if conn is None:
            raise Exception("Database pool exhausted - could not get connection")
        yield conn
        conn.commit()
    except Exception:
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise
    finally:
        if conn:
            release_connection(conn)

def is_postgresql_available():
    """Check si PostgreSQL está disponible"""
    return DATABASE_URL is not None and connection_pool is not None

# =========================================================================
# NFTs - BATCH OPERATIONS (Crítico para escalar)
# =========================================================================

def get_nfts_by_wallet(wallet_address):
    """
    Obtener TODOS los NFTs de una wallet en UNA sola query.
    Usa cache en memoria para reducir queries.

    Returns: list de NFTs
    """
    wallet = wallet_address.lower()

    # Check cache first
    cached = _cache_get(_wallet_nfts_cache, _wallet_cache_expiry, wallet)
    if cached is not None:
        return cached

    if not is_postgresql_available():
        return []

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT token_id, name, guild, race_class,
                           last_known_owner, image_url, dynamic_state, last_update
                    FROM nfts
                    WHERE LOWER(last_known_owner) = %s
                    ORDER BY token_id
                """, (wallet,))
                nfts = cur.fetchall()

        # Cache result
        _cache_set(_wallet_nfts_cache, _wallet_cache_expiry, wallet, nfts)
        return nfts
    except Exception as e:
        print(f"❌ Error getting NFTs for wallet {wallet[:8]}...: {e}")
        return []

def get_active_missions_by_wallet(wallet_address):
    """
    Obtener TODAS las misiones activas de una wallet en UNA sola query.
    Usa cache en memoria.

    Returns: list de misiones
    """
    wallet = wallet_address.lower()

    # Check cache first
    cached = _cache_get(_wallet_missions_cache, _missions_cache_expiry, wallet)
    if cached is not None:
        return cached

    if not is_postgresql_available():
        return []

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT mission_key, wallet, hero_id, hero_ids, mission_id,
                           start_time, duration_hours, is_party
                    FROM active_missions
                    WHERE LOWER(wallet) = %s
                """, (wallet,))
                missions = cur.fetchall()

        # Cache result
        _cache_set(_wallet_missions_cache, _missions_cache_expiry, wallet, missions)
        return missions
    except Exception as e:
        print(f"❌ Error getting missions for wallet {wallet[:8]}...: {e}")
        return []

def update_nfts_batch(nfts_list):
    """
    Actualizar múltiples NFTs en UNA sola transacción.
    Mucho más eficiente que queries individuales.

    Args:
        nfts_list: lista de dicts con token_id, owner, dynamic_state, etc.
    """
    if not is_postgresql_available() or not nfts_list:
        return False

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                for nft in nfts_list:
                    cur.execute("""
                        INSERT INTO nfts (token_id, name, guild, race_class,
                                         last_known_owner, image_url, dynamic_state, last_update)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (token_id) DO UPDATE SET
                            name = COALESCE(EXCLUDED.name, nfts.name),
                            guild = COALESCE(EXCLUDED.guild, nfts.guild),
                            race_class = COALESCE(EXCLUDED.race_class, nfts.race_class),
                            last_known_owner = COALESCE(EXCLUDED.last_known_owner, nfts.last_known_owner),
                            image_url = COALESCE(EXCLUDED.image_url, nfts.image_url),
                            dynamic_state = COALESCE(EXCLUDED.dynamic_state, nfts.dynamic_state),
                            last_update = NOW()
                    """, (
                        nft.get('token_id'),
                        nft.get('name'),
                        nft.get('guild'),
                        nft.get('race_class'),
                        nft.get('last_known_owner', '').lower() if nft.get('last_known_owner') else None,
                        nft.get('image_url'),
                        Json(nft.get('dynamic_state', {}))
                    ))

        # Invalidar cache de wallets afectadas
        for nft in nfts_list:
            if nft.get('last_known_owner'):
                invalidate_wallet_cache(nft['last_known_owner'])

        return True
    except Exception as e:
        print(f"❌ Error batch updating NFTs: {e}")
        return False

# =========================================================================
# NFTs - FUNCIONES INDIVIDUALES (Compatibilidad con código existente)
# =========================================================================

def load_nfts_database():
    """
    Cargar toda la base de datos de NFTs desde PostgreSQL.
    ADVERTENCIA: Para 35,000 NFTs, esto es costoso. Usar get_nfts_by_wallet() cuando sea posible.
    """
    if not is_postgresql_available():
        return {}

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT token_id, name, guild, race_class,
                           last_known_owner, image_url, dynamic_state, last_update
                    FROM nfts
                """)
                rows = cur.fetchall()

        nfts_db = {}
        for row in rows:
            nfts_db[row['token_id']] = {
                'token_id': row['token_id'],
                'name': row['name'],
                'guild': row['guild'],
                'race_class': row['race_class'],
                'last_known_owner': row['last_known_owner'],
                'image_url': row.get('image_url', '/img/emissary-placeholder.png'),
                'dynamic_state': row['dynamic_state'] or {},
                'last_update': row['last_update'].isoformat() if row['last_update'] else None
            }
        return nfts_db
    except Exception as e:
        print(f"❌ Error loading NFTs database: {e}")
        return {}

def save_nfts_database(nfts_db):
    """Guardar base de datos de NFTs. Usa batch internamente."""
    if not nfts_db:
        return True
    nfts_list = list(nfts_db.values())
    return update_nfts_batch(nfts_list)

def get_nft_from_database(token_id):
    """Obtener un NFT específico"""
    if not is_postgresql_available():
        return None

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT token_id, name, guild, race_class,
                           last_known_owner, image_url, dynamic_state, last_update
                    FROM nfts WHERE token_id = %s
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
                'dynamic_state': row['dynamic_state'] or {},
                'last_update': row['last_update'].isoformat() if row['last_update'] else None
            }
        return None
    except Exception as e:
        print(f"❌ Error getting NFT {token_id}: {e}")
        return None

def update_nft_dynamic_state(token_id, dynamic_state):
    """Actualizar solo el dynamic_state de un NFT"""
    if not is_postgresql_available():
        return False

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE nfts
                    SET dynamic_state = %s, last_update = NOW()
                    WHERE token_id = %s
                    RETURNING last_known_owner
                """, (Json(dynamic_state), token_id))
                result = cur.fetchone()

        # Invalidar cache si hay owner
        if result and result[0]:
            invalidate_wallet_cache(result[0])
        return True
    except Exception as e:
        print(f"❌ Error updating NFT {token_id}: {e}")
        return False

# =========================================================================
# ACTIVE MISSIONS
# =========================================================================

def load_active_missions():
    """Cargar todas las misiones activas"""
    if not is_postgresql_available():
        return {}

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT mission_key, wallet, hero_id, hero_ids, mission_id,
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
            hero_ids = row.get('hero_ids')
            if hero_ids:
                if isinstance(hero_ids, str):
                    mission_data['hero_ids'] = json.loads(hero_ids)
                else:
                    mission_data['hero_ids'] = hero_ids
            missions[row['mission_key']] = mission_data
        return missions
    except Exception as e:
        print(f"❌ Error loading active missions: {e}")
        return {}

def save_active_missions(missions_dict):
    """Guardar todas las misiones activas usando UPSERT"""
    if not is_postgresql_available():
        return False

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Get existing keys
                cur.execute("SELECT mission_key FROM active_missions")
                existing_keys = set(row[0] for row in cur.fetchall())

                # Delete removed missions
                current_keys = set(missions_dict.keys())
                for key in existing_keys - current_keys:
                    cur.execute("DELETE FROM active_missions WHERE mission_key = %s", (key,))

                # UPSERT all missions
                for mission_key, m in missions_dict.items():
                    hero_ids_json = json.dumps(m['hero_ids']) if m.get('hero_ids') else None
                    start_time = m.get('start_time', '').replace('Z', '+00:00') if isinstance(m.get('start_time'), str) else m.get('start_time')

                    cur.execute("""
                        INSERT INTO active_missions (mission_key, wallet, hero_id, hero_ids,
                                                     mission_id, start_time, duration_hours, is_party)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (mission_key) DO UPDATE SET
                            wallet = EXCLUDED.wallet,
                            hero_id = EXCLUDED.hero_id,
                            hero_ids = EXCLUDED.hero_ids,
                            mission_id = EXCLUDED.mission_id,
                            start_time = EXCLUDED.start_time,
                            duration_hours = EXCLUDED.duration_hours,
                            is_party = EXCLUDED.is_party
                    """, (mission_key, m.get('wallet'), m.get('hero_id'), hero_ids_json,
                          m.get('mission_id'), start_time, m.get('duration_hours'), m.get('is_party', False)))

                    # Invalidar cache de wallet
                    if m.get('wallet'):
                        invalidate_wallet_cache(m['wallet'])

        print(f"✅ Saved {len(missions_dict)} active missions")
        return True
    except Exception as e:
        print(f"❌ Error saving active missions: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_active_mission(mission_key, mission_data):
    """Agregar una misión activa"""
    if not is_postgresql_available():
        return False

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                hero_ids_json = json.dumps(mission_data['hero_ids']) if mission_data.get('hero_ids') else None
                start_time = mission_data.get('start_time', '').replace('Z', '+00:00') if isinstance(mission_data.get('start_time'), str) else mission_data.get('start_time')

                cur.execute("""
                    INSERT INTO active_missions (mission_key, wallet, hero_id, hero_ids,
                                                 mission_id, start_time, duration_hours, is_party)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (mission_key) DO UPDATE SET
                        wallet = EXCLUDED.wallet,
                        hero_id = EXCLUDED.hero_id,
                        hero_ids = EXCLUDED.hero_ids,
                        mission_id = EXCLUDED.mission_id,
                        start_time = EXCLUDED.start_time,
                        duration_hours = EXCLUDED.duration_hours,
                        is_party = EXCLUDED.is_party
                """, (mission_key, mission_data.get('wallet'), mission_data.get('hero_id'),
                      hero_ids_json, mission_data.get('mission_id'), start_time,
                      mission_data.get('duration_hours'), mission_data.get('is_party', False)))

        # Invalidar cache
        if mission_data.get('wallet'):
            invalidate_wallet_cache(mission_data['wallet'])
        return True
    except Exception as e:
        print(f"❌ Error adding mission: {e}")
        return False

def remove_active_mission(mission_key):
    """Eliminar una misión activa"""
    if not is_postgresql_available():
        return False

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Get wallet before delete for cache invalidation
                cur.execute("SELECT wallet FROM active_missions WHERE mission_key = %s", (mission_key,))
                row = cur.fetchone()
                wallet = row[0] if row else None

                cur.execute("DELETE FROM active_missions WHERE mission_key = %s", (mission_key,))

        if wallet:
            invalidate_wallet_cache(wallet)
        return True
    except Exception as e:
        print(f"❌ Error removing mission: {e}")
        return False

# =========================================================================
# PLAYERS (Session cache)
# =========================================================================

def load_players():
    """Cargar todos los players"""
    if not is_postgresql_available():
        return {}

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT wallet, player_data FROM players")
                rows = cur.fetchall()
        return {row['wallet']: row['player_data'] for row in rows}
    except Exception as e:
        print(f"❌ Error loading players: {e}")
        return {}

def save_players(players_dict):
    """Guardar players (batch)"""
    if not is_postgresql_available() or not players_dict:
        return False

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                for wallet, player_data in players_dict.items():
                    cur.execute("""
                        INSERT INTO players (wallet, player_data, last_update)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (wallet) DO UPDATE SET
                            player_data = EXCLUDED.player_data,
                            last_update = NOW()
                    """, (wallet, Json(player_data)))
        return True
    except Exception as e:
        print(f"❌ Error saving players: {e}")
        return False

# =========================================================================
# STATS
# =========================================================================

def load_stats():
    """Cargar stats globales"""
    default_stats = {
        "total_characters": 0,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": [],
        "player_leaderboard": []
    }

    if not is_postgresql_available():
        return default_stats

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT stats_data FROM global_stats WHERE id = 1")
                row = cur.fetchone()
        return row['stats_data'] if row else default_stats
    except Exception as e:
        print(f"❌ Error loading stats: {e}")
        return default_stats

def save_stats(stats_data):
    """Guardar stats globales"""
    if not is_postgresql_available():
        return False

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE global_stats SET stats_data = %s, last_update = NOW() WHERE id = 1
                """, (Json(stats_data),))
        return True
    except Exception as e:
        print(f"❌ Error saving stats: {e}")
        return False

# =========================================================================
# GENERIC LOAD/SAVE (Wrapper para archivos JSON)
# =========================================================================

def load_json_or_db(filepath, default_value):
    """Helper genérico: PostgreSQL para datos críticos, JSON para configs"""
    filename = os.path.basename(filepath)

    if is_postgresql_available():
        if filename == "nfts_database.json":
            return load_nfts_database()
        elif filename == "active_missions.json":
            return load_active_missions()
        elif filename == "players.json":
            return load_players()
        elif filename == "stats.json":
            return load_stats()

    # JSON fallback para otros archivos
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading {filename}: {e}")
    return default_value

def save_json_or_db(filepath, data):
    """Helper genérico: PostgreSQL para datos críticos, JSON para otros"""
    filename = os.path.basename(filepath)

    if is_postgresql_available():
        if filename == "nfts_database.json":
            return save_nfts_database(data)
        elif filename == "active_missions.json":
            return save_active_missions(data)
        elif filename == "players.json":
            return save_players(data)
        elif filename == "stats.json":
            return save_stats(data)

    # JSON para otros archivos
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"⚠️ Error saving {filename}: {e}")
        return False

# =========================================================================
# USER BALANCES
# =========================================================================

def ensure_user_balances_table():
    """Ensure user_balances table exists"""
    if not is_postgresql_available():
        return False

    try:
        with get_db() as conn:
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
                cur.execute("CREATE INDEX IF NOT EXISTS idx_balances_wallet ON user_balances(wallet)")
        print("✅ user_balances table verified")
        return True
    except Exception as e:
        print(f"❌ Error ensuring user_balances table: {e}")
        return False

def get_or_create_user_balance(wallet):
    """Get user balance, creating if doesn't exist"""
    default = {"ember_balance": 0, "ash_balance": 0, "gambit_rolls_today": 0,
               "gambit_rolls_max": 5, "gambit_next_reset": None}

    if not is_postgresql_available():
        return default

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_balances (wallet, ember_balance, ash_balance, gambit_rolls_today, gambit_rolls_max)
                    VALUES (%s, 0, 0, 0, 5)
                    ON CONFLICT (wallet) DO NOTHING
                """, (wallet,))

                cur.execute("""
                    SELECT ember_balance, ash_balance, gambit_rolls_today, gambit_rolls_max, gambit_next_reset
                    FROM user_balances WHERE wallet = %s
                """, (wallet,))
                row = cur.fetchone()

        if row:
            return {"ember_balance": row[0], "ash_balance": row[1], "gambit_rolls_today": row[2],
                    "gambit_rolls_max": row[3], "gambit_next_reset": row[4]}
        return default
    except Exception as e:
        print(f"❌ Error getting user balance: {e}")
        return default

# =========================================================================
# INICIALIZACIÓN
# =========================================================================

# Auto-inicializar pool al importar
init_connection_pool()

# Crear tablas críticas si PostgreSQL disponible
if is_postgresql_available():
    ensure_user_balances_table()
    print("✅ Database module ready")
