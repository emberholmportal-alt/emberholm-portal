import json
import os
import time
import random
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory, request, abort, render_template
from flask_cors import CORS

# 🔥 POSTGRESQL INTEGRATION - Persistence module
try:
    import database as db
    POSTGRESQL_AVAILABLE = db.is_postgresql_available()
    if POSTGRESQL_AVAILABLE:
        print("✅ PostgreSQL persistence enabled")
    else:
        print("⚠️ PostgreSQL not configured - using JSON fallback")
except Exception as e:
    print(f"⚠️ PostgreSQL module import failed: {e}")
    POSTGRESQL_AVAILABLE = False
    db = None

# ⚠️ Web3 temporarily disabled due to Render deployment issues
# Will use local cache (wallet_nfts.json) for NFT data
WEB3_AVAILABLE = False
Web3 = None

# ---------------------------------
# Config
# ---------------------------------

BASE_DIR     = os.path.dirname(__file__)
DATA_DIR     = os.path.join(BASE_DIR, "data")
PLAYERS_PATH = os.path.join(DATA_DIR, "players.json")
STATS_PATH   = os.path.join(DATA_DIR, "stats.json")
GUILDS_PATH  = os.path.join(DATA_DIR, "guilds.json")
WALLET_NFTS_PATH = os.path.join(DATA_DIR, "wallet_nfts.json")
ACHIEVEMENTS_PATH = os.path.join(DATA_DIR, "achievements.json")
MISSIONS_CONFIG_PATH = os.path.join(DATA_DIR, "missions_config.json")
ACTIVE_MISSIONS_PATH = os.path.join(DATA_DIR, "active_missions.json")
NFTS_DATABASE_PATH = os.path.join(DATA_DIR, "nfts_database.json")  # 🔥 Base de datos centralizada

# Carpeta donde guardaste los metadatas base (00001.json, 00002.json, etc.)
METADATA_DIR = os.path.join(DATA_DIR, "metadata")

# IPFS Gateway para convertir URLs de IPFS a URLs HTTP
IPFS_GATEWAY = "https://ipfs.io/ipfs/"

# ---------------------------------
# Blockchain Config (TEMPORARILY DISABLED)
# ---------------------------------
# Note: Blockchain integration temporarily disabled for deployment
# Using local cache (wallet_nfts.json) for NFT data
# Will re-enable once deployment is stable

w3 = None
nft_contract = None
print("⚠️ Using local cache for NFT data (wallet_nfts.json)")

# Ganancia pasiva cada 24h por héroe
PASSIVE_XP_PER_DAY   = 5
PASSIVE_AURA_PER_DAY = 1

# Cada cuántas horas se refresca la energía natural completa
ENERGY_FULL_REFRESH_HOURS = 48

# Coste de RECOVER: cuánta XP cuesta recuperar 1 punto de energía
XP_COST_PER_ENERGY = 5

# En cuántas horas se resetea el cooldown de misión
ROTATION_HOURS = 72

# Load missions configuration from JSON
def load_missions_config():
    """Load missions configuration from missions_config.json"""
    return load_json(MISSIONS_CONFIG_PATH, {
        "missions": [],
        "death_costs": {},
        "bonuses": {}
    })

# Load events configuration from JSON
def load_events_config():
    """Load events configuration from events_config.json"""
    events_path = os.path.join(DATA_DIR, "events_config.json")
    return load_json(events_path, {
        "events": [],
        "event_settings": {}
    })

# Missions configuration (loaded at startup)
MISSIONS_CONFIG = {}
MISSIONS = []
DEATH_COSTS = {}
BONUSES = {}

# Events configuration (loaded at startup)
EVENTS_CONFIG = {}
EVENTS = []
EVENT_SETTINGS = {}

# ---------------------------------
# Achievements System
# ---------------------------------

AVAILABLE_ACHIEVEMENTS = {
    "first_mission": {
        "name": "First Mission",
        "description": "Complete your first mission",
        "icon": "🎯"
    },
    "10_missions": {
        "name": "Veteran Explorer",
        "description": "Complete 10 missions",
        "icon": "⚔️"
    },
    "50_missions": {
        "name": "Seasoned Warrior",
        "description": "Complete 50 missions",
        "icon": "🏆"
    },
    "100_missions": {
        "name": "Legendary Hero",
        "description": "Complete 100 missions",
        "icon": "👑"
    },
    "reach_level_10": {
        "name": "Level 10 Achieved",
        "description": "Reach level 10",
        "icon": "⭐"
    },
    "reach_level_50": {
        "name": "Level 50 Achieved",
        "description": "Reach level 50",
        "icon": "💫"
    },
    "guild_master": {
        "name": "Guild Master",
        "description": "Become a guild leader",
        "icon": "🏅"
    },
    "dragon_slayer": {
        "name": "Dragon Slayer",
        "description": "Defeat a legendary dragon",
        "icon": "🐉"
    },
    "void_walker": {
        "name": "Void Walker",
        "description": "Complete all Void Echoes missions",
        "icon": "🌌"
    },
    "forge_master": {
        "name": "Forge Master",
        "description": "Complete all Forge Legion missions",
        "icon": "⚒️"
    }
}

def get_token_achievements(token_id):
    """Get all achievements for a token"""
    achievements_db = load_json(ACHIEVEMENTS_PATH, {})
    token_id_str = str(token_id).zfill(5)
    return achievements_db.get(token_id_str, [])

def grant_achievement(token_id, achievement_id):
    """Grant an achievement to a token"""
    if achievement_id not in AVAILABLE_ACHIEVEMENTS:
        return False, "Invalid achievement ID"

    achievements_db = load_json(ACHIEVEMENTS_PATH, {})
    token_id_str = str(token_id).zfill(5)

    if token_id_str not in achievements_db:
        achievements_db[token_id_str] = []

    if achievement_id not in achievements_db[token_id_str]:
        achievements_db[token_id_str].append(achievement_id)
        save_json(ACHIEVEMENTS_PATH, achievements_db)
        return True, "Achievement granted"

    return False, "Achievement already exists"

def check_and_grant_mission_achievements(token_id, total_missions):
    """Auto-grant achievements based on mission count"""
    achievements = []

    if total_missions == 1:
        success, msg = grant_achievement(token_id, "first_mission")
        if success:
            achievements.append("first_mission")

    if total_missions == 10:
        success, msg = grant_achievement(token_id, "10_missions")
        if success:
            achievements.append("10_missions")

    if total_missions == 50:
        success, msg = grant_achievement(token_id, "50_missions")
        if success:
            achievements.append("50_missions")

    if total_missions == 100:
        success, msg = grant_achievement(token_id, "100_missions")
        if success:
            achievements.append("100_missions")

    return achievements

# ---------------------------------
# Mission System - Probability & Outcome Calculation
# ---------------------------------

def calculate_mission_success_rate(hero, mission):
    """
    Calculate total success rate for a mission based on hero attributes.
    Returns: success_rate (0-98)
    """
    base_rate = mission["success_rate"]
    bonus = 0

    # Extract hero data
    hero_guild = hero.get("dynamic_state", {}).get("current_guild", hero.get("guild", "Unknown"))
    hero_level = calculate_level_from_xp(hero.get("dynamic_state", {}).get("xp_total", 0))
    hero_aura = hero.get("dynamic_state", {}).get("aura_level", 0)

    # Extract race and class from metadata
    race_class = hero.get("race_class", "")
    hero_race = race_class.split()[0] if race_class else "Unknown"
    hero_class = race_class.split()[1] if len(race_class.split()) > 1 else "Unknown"

    # Guild bonus
    if hero_guild == mission.get("favored_guild"):
        bonus += BONUSES.get("guild_match", 12)

    # Class bonus
    if hero_class == mission.get("favored_class"):
        bonus += BONUSES.get("class_match", 8)

    # Race bonus
    if hero_race == mission.get("favored_race"):
        bonus += BONUSES.get("race_match", 5)

    # Level bonus (1% per 10 levels)
    level_bonus = (hero_level // 10) * BONUSES.get("level_per_10", 1)
    bonus += level_bonus

    # Aura bonus (1% per 100 Aura)
    aura_bonus = (hero_aura // 100) * BONUSES.get("aura_per_100", 1)
    bonus += aura_bonus

    # Cap at 98% (never 100%)
    total_success_rate = min(98, base_rate + bonus)

    return total_success_rate, bonus

def calculate_level_from_xp(xp):
    """Simple level calculation: 1 level per 100 XP"""
    return max(1, xp // 100)

def calculate_death_protection(hero_level, hero_aura):
    """
    Calculate death protection percentage.
    Level 50+ and Aura 500+ provides significant protection.
    Returns: protection percentage (0-50)
    """
    protection = 0

    # Level protection (max 30%)
    if hero_level >= 50:
        protection += 30
    elif hero_level >= 30:
        protection += 15
    elif hero_level >= 10:
        protection += 5

    # Aura protection (max 20%)
    if hero_aura >= 500:
        protection += 20
    elif hero_aura >= 250:
        protection += 10
    elif hero_aura >= 100:
        protection += 5

    return min(50, protection)

def roll_mission_outcome(hero, mission):
    """
    Roll for mission outcome.
    Returns: ("SUCCESS", details) | ("FAILURE", details) | ("DEATH", details)
    """
    # Calculate success rate
    success_rate, bonus = calculate_mission_success_rate(hero, mission)

    # Roll for success
    roll = random.randint(1, 100)

    if roll <= success_rate:
        # Mission succeeded
        reward_multiplier = 1.0

        # Check perfect alignment (all 3 match: guild, class, race)
        hero_guild = hero.get("dynamic_state", {}).get("current_guild", hero.get("guild", "Unknown"))
        race_class = hero.get("race_class", "")
        hero_race = race_class.split()[0] if race_class else "Unknown"
        hero_class = race_class.split()[1] if len(race_class.split()) > 1 else "Unknown"

        perfect_alignment = (
            hero_guild == mission.get("favored_guild") and
            hero_class == mission.get("favored_class") and
            hero_race == mission.get("favored_race")
        )

        if perfect_alignment:
            reward_multiplier = BONUSES.get("perfect_alignment_multiplier", 1.5)

        xp_reward = int(mission["reward_xp"] * reward_multiplier)
        aura_reward = int(mission["reward_aura"] * reward_multiplier)

        return ("SUCCESS", {
            "xp_gain": xp_reward,
            "aura_gain": aura_reward,
            "perfect_alignment": perfect_alignment,
            "success_rate": success_rate,
            "roll": roll
        })
    else:
        # Mission failed - check for death
        death_chance = mission.get("death_chance", 0)

        if death_chance > 0:
            # Calculate death protection
            hero_level = calculate_level_from_xp(hero.get("dynamic_state", {}).get("xp_total", 0))
            hero_aura = hero.get("dynamic_state", {}).get("aura_level", 0)
            protection = calculate_death_protection(hero_level, hero_aura)

            # Reduce death chance by protection
            effective_death_chance = death_chance * (1 - protection / 100)

            # Roll for death
            death_roll = random.uniform(0, 100)

            if death_roll <= effective_death_chance:
                # Hero died
                return ("DEATH", {
                    "death_roll": death_roll,
                    "death_chance": effective_death_chance,
                    "protection": protection,
                    "success_rate": success_rate,
                    "roll": roll
                })

        # Failed but survived
        xp_loss = mission.get("xp_loss_on_fail", 0)

        return ("FAILURE", {
            "xp_loss": xp_loss,
            "success_rate": success_rate,
            "roll": roll
        })

def get_death_cost(death_count):
    """
    Get reinvocation cost based on death count.
    Returns: (xp_cost, aura_cost)
    """
    if death_count == 0:
        cost = DEATH_COSTS.get("first_death", {"xp_cost": 500, "aura_cost": 100})
    elif death_count == 1:
        cost = DEATH_COSTS.get("second_death", {"xp_cost": 1500, "aura_cost": 300})
    elif death_count == 2:
        cost = DEATH_COSTS.get("third_death", {"xp_cost": 5000, "aura_cost": 1000})
    else:
        cost = DEATH_COSTS.get("fourth_plus", {"xp_cost": 10000, "aura_cost": 2500})

    return cost["xp_cost"], cost["aura_cost"]

# ---------------------------------
# Helpers de lectura/escritura JSON
# ---------------------------------

def load_json(path, fallback):
    """
    Load JSON with PostgreSQL support for critical files.

    🔥 SMART WRAPPER:
    - nfts_database.json → PostgreSQL
    - active_missions.json → PostgreSQL
    - players.json → PostgreSQL
    - stats.json → PostgreSQL
    - Others (guilds, missions_config) → JSON files
    """
    if POSTGRESQL_AVAILABLE and db:
        return db.load_json_or_db(path, fallback)

    # Fallback to JSON file
    if not os.path.exists(path):
        return fallback
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return fallback

def save_json(path, obj):
    """
    Save JSON with PostgreSQL support for critical files.

    🔥 SMART WRAPPER:
    - nfts_database.json → PostgreSQL
    - active_missions.json → PostgreSQL
    - players.json → PostgreSQL
    - stats.json → PostgreSQL
    - Others (guilds, missions_config) → JSON files
    """
    if POSTGRESQL_AVAILABLE and db:
        db.save_json_or_db(path, obj)
        return

    # Fallback to JSON file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4)

# ---------------------------------
# NFTs Database - Fuente de Verdad Centralizada
# ---------------------------------

def load_nfts_database():
    """
    Carga la base de datos centralizada de NFTs.
    Esta es la FUENTE DE VERDAD para todos los atributos dinámicos.
    """
    db = load_json(NFTS_DATABASE_PATH, {})
    # Filtrar comentarios de metadata
    return {k: v for k, v in db.items() if not k.startswith("_")}

def save_nfts_database(db):
    """Guarda la base de datos de NFTs."""
    # Preservar comentarios
    full_db = load_json(NFTS_DATABASE_PATH, {})
    comments = {k: v for k, v in full_db.items() if k.startswith("_")}
    full_db = {**comments, **db}
    save_json(NFTS_DATABASE_PATH, full_db)

def get_nft_from_database(token_id):
    """
    Obtiene un NFT de la base de datos.
    Returns: NFT object o None si no existe
    """
    token_id_padded = str(token_id).zfill(5)
    db = load_nfts_database()
    return db.get(token_id_padded)

def upsert_nft_to_database(token_id, nft_data, owner_wallet=None):
    """
    Inserta o actualiza un NFT en la base de datos.

    Args:
        token_id: ID del token
        nft_data: Datos del NFT (debe incluir dynamic_state)
        owner_wallet: Wallet del dueño (opcional, para tracking)

    Returns:
        El NFT actualizado
    """
    token_id_padded = str(token_id).zfill(5)
    db = load_nfts_database()

    now = now_utc_str()

    if token_id_padded in db:
        # Actualizar NFT existente
        existing = db[token_id_padded]
        existing.update(nft_data)
        existing["last_synced"] = now
        if owner_wallet:
            existing["last_known_owner"] = owner_wallet.lower()
        db[token_id_padded] = existing
    else:
        # Nuevo NFT
        nft_data["token_id"] = token_id_padded
        nft_data["first_seen"] = now
        nft_data["last_synced"] = now
        if owner_wallet:
            nft_data["last_known_owner"] = owner_wallet.lower()
        else:
            nft_data["last_known_owner"] = None
        db[token_id_padded] = nft_data

    save_nfts_database(db)
    return db[token_id_padded]

def sync_nft_to_database(token_id, owner_wallet=None):
    """
    Sincroniza un NFT desde metadata a la base de datos.
    Si ya existe, preserva dynamic_state.
    Si es nuevo, crea con dynamic_state inicial.

    Args:
        token_id: ID del token
        owner_wallet: Wallet del dueño (opcional)

    Returns:
        El NFT sincronizado
    """
    token_id_padded = str(token_id).zfill(5)
    existing = get_nft_from_database(token_id_padded)

    if existing:
        # Ya existe: solo actualizar owner y last_synced
        db = load_nfts_database()
        db[token_id_padded]["last_synced"] = now_utc_str()
        if owner_wallet:
            db[token_id_padded]["last_known_owner"] = owner_wallet.lower()
        save_nfts_database(db)
        return db[token_id_padded]
    else:
        # Nuevo: crear desde metadata
        hero = create_hero_from_metadata(token_id)
        return upsert_nft_to_database(token_id_padded, hero, owner_wallet)

def update_nft_dynamic_state(token_id, dynamic_state_updates):
    """
    Actualiza solo el dynamic_state de un NFT en la base de datos.

    Args:
        token_id: ID del token
        dynamic_state_updates: Dict con campos a actualizar en dynamic_state

    Returns:
        El NFT actualizado o None si no existe
    """
    token_id_padded = str(token_id).zfill(5)
    nft = get_nft_from_database(token_id_padded)

    if not nft:
        print(f"⚠️ update_nft_dynamic_state: NFT {token_id_padded} not found in database")
        return None

    # Actualizar dynamic_state
    if "dynamic_state" not in nft:
        nft["dynamic_state"] = {}

    nft["dynamic_state"].update(dynamic_state_updates)
    nft["dynamic_state"]["last_update"] = now_utc_str()

    # Guardar
    return upsert_nft_to_database(token_id_padded, nft)

def populate_database_on_startup(max_nfts=100):
    """
    🔥 SISTEMA AUTOMÁTICO: Poblado inicial de la base de datos al iniciar el servidor.

    Escanea la carpeta de metadata y sincroniza NFTs encontrados a nfts_database.json.
    Solo crea NFTs nuevos, preserva los existentes.
    Esto asegura que STATS y GUILDS muestren datos reales desde el inicio.

    Args:
        max_nfts: Número máximo de NFTs a sincronizar (default: 100)
                  Use None para sincronizar todos los archivos encontrados.

    NO requiere intervención manual - se ejecuta automáticamente al iniciar el servidor.
    """
    print("\n" + "="*70)
    print("🔥 STARTUP: Auto-populating NFTs database from metadata files...")
    print("="*70)

    if not os.path.exists(METADATA_DIR):
        print(f"⚠️ Metadata directory not found: {METADATA_DIR}")
        return

    # Escanear archivos de metadata (solo primeros max_nfts)
    metadata_files = []
    try:
        for filename in sorted(os.listdir(METADATA_DIR)):
            if filename.endswith('.json') and filename[0:5].isdigit():
                token_id = filename[0:5]
                metadata_files.append(token_id)
                # Limitar a max_nfts para evitar sincronizar 35000 archivos
                if max_nfts and len(metadata_files) >= max_nfts:
                    break
    except Exception as e:
        print(f"❌ Error scanning metadata directory: {e}")
        return

    if not metadata_files:
        print("⚠️ No metadata files found")
        return

    total_available = len([f for f in os.listdir(METADATA_DIR) if f.endswith('.json')])
    print(f"📁 Found {total_available} metadata files total")
    print(f"📊 Syncing first {len(metadata_files)} NFTs to database...")

    # Sincronizar cada NFT a la base de datos
    synced_count = 0
    skipped_count = 0
    error_count = 0

    for token_id in metadata_files:
        try:
            # Verificar si ya existe
            existing = get_nft_from_database(token_id)

            if existing:
                skipped_count += 1
            else:
                # Sincronizar nuevo NFT (sin owner por ahora)
                nft = sync_nft_to_database(token_id, owner_wallet=None)
                synced_count += 1

                # Log cada 10 NFTs
                if synced_count % 10 == 0:
                    print(f"  ✅ Synced {synced_count} NFTs...")

        except Exception as e:
            error_count += 1
            if error_count <= 5:  # Solo mostrar primeros 5 errores
                print(f"  ⚠️ Error syncing {token_id}: {e}")

    print(f"\n📊 Sync complete:")
    print(f"  ✅ {synced_count} NFTs added to database")
    print(f"  ⏭️  {skipped_count} NFTs already in database (preserved)")
    if error_count > 0:
        print(f"  ⚠️ {error_count} errors")

    # Recalcular stats globales
    print(f"\n📊 Recalculating global stats...")
    try:
        calculate_guilds_data()

        # Actualizar total_characters en stats.json
        db = load_nfts_database()
        total_nfts = len(db)

        stats_obj = load_json(STATS_PATH, {})
        stats_obj["total_characters"] = total_nfts
        save_json(STATS_PATH, stats_obj)

        print(f"  ✅ Guilds data updated")
        print(f"  ✅ Stats updated (Total characters: {total_nfts})")
    except Exception as e:
        print(f"  ⚠️ Error updating stats: {e}")

    print("="*70)
    print("🎯 Database ready! STATS and GUILDS will show real data.")
    print("="*70 + "\n")

# ---------------------------------
# Helpers de tiempo
# ---------------------------------

def now_utc_str():
    return datetime.utcnow().isoformat() + "Z"

def hours_since(ts_str):
    """Devuelve cuántas horas pasaron desde ts_str (ISO) hasta ahora."""
    if not ts_str:
        return 999999
    try:
        clean = ts_str.replace("Z", "")
        t = datetime.fromisoformat(clean)
    except Exception:
        return 999999
    delta = datetime.utcnow() - t
    return delta.total_seconds() / 3600.0

# ---------------------------------
# Progresión pasiva + regeneración de energía
# ---------------------------------

def apply_passive_and_regen(player_obj, stats_obj):
    """
    - Goteo pasivo XP/Aura cada 24h.
    - Regeneración completa de energía cada 48h.
    - Recalcula totales del jugador.
    - Acumula XP/Aura global en stats.json.
    """
    heroes = player_obj.get("heroes", [])
    wallet_tot_xp = 0
    wallet_tot_aura = 0
    wallet_tot_energy_avail = 0

    changed_global_xp = 0
    changed_global_aura = 0

    for hero in heroes:
        ds = hero.setdefault("dynamic_state", {})
        xp_total        = ds.get("xp_total", 0)
        aura_level      = ds.get("aura_level", 0)
        energy_current  = ds.get("energy_current", 100)
        energy_max      = ds.get("energy_max", 100)
        last_update     = ds.get("last_update")
        last_energy_ref = ds.get("last_energy_refresh")

        # Goteo pasivo cada 24h
        if hours_since(last_update) >= 24:
            xp_total   += PASSIVE_XP_PER_DAY
            aura_level += PASSIVE_AURA_PER_DAY

            changed_global_xp   += PASSIVE_XP_PER_DAY
            changed_global_aura += PASSIVE_AURA_PER_DAY

            ds["last_update"] = now_utc_str()

        # Regen natural de energía cada 48h
        if hours_since(last_energy_ref) >= ENERGY_FULL_REFRESH_HOURS:
            energy_current = energy_max
            ds["last_energy_refresh"] = now_utc_str()

        ds["xp_total"]       = xp_total
        ds["aura_level"]     = aura_level
        ds["energy_current"] = energy_current

        wallet_tot_xp            += xp_total
        wallet_tot_aura          += aura_level
        wallet_tot_energy_avail  += energy_current

    stats_obj["total_exp_collected"]  = stats_obj.get("total_exp_collected", 0) + changed_global_xp
    stats_obj["total_aura_collected"] = stats_obj.get("total_aura_collected", 0) + changed_global_aura

    player_obj["totals"] = {
        "heroes_count": len(heroes),
        "xp_total_all": wallet_tot_xp,
        "aura_total_all": wallet_tot_aura,
        "energy_total_available": wallet_tot_energy_avail
    }

    return player_obj, stats_obj

# ---------------------------------
# Ranking y stats de gremios
# ---------------------------------

def calculate_guild_ranking():
    """
    🔥 Calcula el ranking de guilds combinando:
    - Member counts REALES desde guilds.json (35,000 NFTs)
    - XP/Aura dinámicos desde nfts_database.json (NFTs que completaron misiones)

    Devuelve lista ordenada por XP total descendente.
    """
    guilds_data = load_json(GUILDS_PATH, [])
    db = load_nfts_database()  # Solo para XP/Aura de NFTs activos
    stats_obj = load_json(STATS_PATH, {})

    # Construir dict de stats por gremio desde guilds.json (member counts reales)
    guild_stats = {}
    for guild in guilds_data:
        guild_name = guild.get("name", "")
        guild_stats[guild_name] = {
            "members": guild.get("members", 0),  # 🔥 Count REAL de 35,000 NFTs
            "xp_total": guild.get("total_xp", 0),
            "aura_total": guild.get("total_aura", 0)
        }

    # 🔥 Actualizar XP/Aura solo desde nfts_database.json (NFTs que jugaron misiones)
    # NO actualizar member counts - esos son fijos desde guilds.json
    for token_id, nft in db.items():
        guild = nft.get("guild")
        # Mapear nombres antiguos a nuevos
        if guild == "Dawnkeepers":
            guild = "Order of Dawn"
        elif guild == "Echoes of the Veil":
            guild = "Void Echoes"

        if not guild:
            guild = nft.get("dynamic_state", {}).get("current_guild", "Unknown")

        ds = nft.get("dynamic_state", {})
        xp = ds.get("xp_total", 0)
        aura = ds.get("aura_level", 0)

        # Si el gremio no existe en guild_stats, crearlo
        if guild not in guild_stats:
            guild_stats[guild] = {
                "members": 0,
                "xp_total": 0,
                "aura_total": 0
            }

        # Solo agregar XP/Aura si el NFT tiene progreso
        # NO incrementar members (ya están correctos desde guilds.json)
        if xp > 0 or aura > 0:
            guild_stats[guild]["xp_total"] += xp
            guild_stats[guild]["aura_total"] += aura

    # Agregar success rate desde stats.json
    guild_ranking_stats = stats_obj.get("guild_ranking", {})

    # 🔥 FIX: Si guild_ranking es una lista (error de formato antiguo), convertir a dict
    if isinstance(guild_ranking_stats, list):
        print("⚠️ guild_ranking was a list, converting to dict...")
        guild_ranking_stats = {}
        stats_obj["guild_ranking"] = guild_ranking_stats
        save_json(STATS_PATH, stats_obj)

    result = []
    for guild_name, data in guild_stats.items():
        rank_data = guild_ranking_stats.get(guild_name, {})
        successes = rank_data.get("successes", 0)
        failures = rank_data.get("failures", 0)
        total_missions = successes + failures
        success_rate = round((successes / total_missions * 100), 1) if total_missions > 0 else 0

        result.append({
            "name": guild_name,
            "xp_total": data["xp_total"],
            "aura_total": data["aura_total"],
            "members": data["members"],  # 🔥 Count REAL de 35,000 NFTs
            "success_rate": f"{success_rate}%"
        })

    # 🔥 ORDENAR por XP total descendente
    result.sort(key=lambda x: x["xp_total"], reverse=True)
    return result

def calculate_player_leaderboard():
    """
    Calcula el leaderboard de jugadores desde la base de datos centralizada.
    Agrupa NFTs por last_known_owner y suma stats.
    Devuelve lista ordenada por XP total descendente.
    """
    db = load_nfts_database()

    # Agrupar NFTs por wallet (last_known_owner)
    wallet_stats = {}
    for token_id, nft in db.items():
        owner = nft.get("last_known_owner")
        if not owner:
            owner = "unknown"

        ds = nft.get("dynamic_state", {})
        xp = ds.get("xp_total", 0)
        aura = ds.get("aura_level", 0)

        if owner not in wallet_stats:
            wallet_stats[owner] = {
                "wallet": owner,
                "heroes_count": 0,
                "xp_total_all": 0,
                "aura_total_all": 0
            }

        wallet_stats[owner]["heroes_count"] += 1
        wallet_stats[owner]["xp_total_all"] += xp
        wallet_stats[owner]["aura_total_all"] += aura

    # Convertir a lista y ordenar
    leaderboard = list(wallet_stats.values())
    leaderboard.sort(key=lambda x: x["xp_total_all"], reverse=True)
    return leaderboard

def count_active_missions():
    """
    Cuenta cuántos NFTs están actualmente en misión.

    🔥 Lee desde active_missions.json (tracking específico de misiones activas)
    Fallback: cuenta desde nfts_database.json si active_missions está vacío
    """
    # Primero intentar desde active_missions.json (más rápido y específico)
    active_missions = load_json(ACTIVE_MISSIONS_PATH, {})
    count = len(active_missions)

    # Si active_missions está vacío, contar desde DB como fallback
    if count == 0:
        db = load_nfts_database()
        for token_id, nft in db.items():
            ds = nft.get("dynamic_state", {})
            if ds.get("state") == "ON_MISSION":
                count += 1

    return count

def calculate_guilds_data():
    """
    🔥 Actualiza guilds.json con datos dinámicos desde nfts_database.
    - Members: cuenta real de NFTs registrados (empieza en 0, crece orgánicamente)
    - XP/Aura: suma total desde dynamic_state de todos los NFTs
    """
    db = load_nfts_database()
    guilds_data = load_json(GUILDS_PATH, [])

    # Calcular stats por gremio desde la DB de NFTs registrados
    guild_stats = {}
    for token_id, nft in db.items():
        guild = nft.get("guild")
        # Mapear nombres antiguos a nuevos
        if guild == "Dawnkeepers":
            guild = "Order of Dawn"
        elif guild == "Echoes of the Veil":
            guild = "Void Echoes"

        if not guild:
            guild = nft.get("dynamic_state", {}).get("current_guild", "Unknown")

        ds = nft.get("dynamic_state", {})

        if guild not in guild_stats:
            guild_stats[guild] = {
                "members": 0,        # 🔥 Contador dinámico (empieza en 0)
                "total_xp": 0,
                "total_aura": 0
            }

        # 🔥 Incrementar contador por cada NFT registrado en DB
        guild_stats[guild]["members"] += 1
        guild_stats[guild]["total_xp"] += ds.get("xp_total", 0)
        guild_stats[guild]["total_aura"] += ds.get("aura_level", 0)

    # 🔥 Actualizar guilds.json con conteos REALES (no hardcoded)
    for g in guilds_data:
        guild_name = g.get("name", "")

        if guild_name in guild_stats:
            stats = guild_stats[guild_name]

            # 🔥 Actualizar con datos reales desde nfts_database
            g["members"] = stats["members"]              # Dinámico: empieza en 0, crece orgánicamente
            g["total_xp"] = stats["total_xp"]
            g["total_aura"] = stats["total_aura"]
            g["avg_xp"] = round(stats["total_xp"] / stats["members"], 2) if stats["members"] > 0 else 0
            g["avg_aura"] = round(stats["total_aura"] / stats["members"], 2) if stats["members"] > 0 else 0
        else:
            # Guild sin NFTs registrados: todo en 0
            g["members"] = 0                              # 🔥 0 en vez de preservar hardcoded
            g["total_xp"] = 0
            g["total_aura"] = 0
            g["avg_xp"] = 0
            g["avg_aura"] = 0

    save_json(GUILDS_PATH, guilds_data)
    return guilds_data

def update_guild_stats(guild_name, xp_gain, aura_gain, stats_obj, success=True):
    """
    🔥 Actualiza stats del gremio cuando un NFT completa/falla una misión:
    - Acumula XP/Aura ganadas en stats["guild_ranking"]
    - Incrementa total_missions_completed/failed en guilds.json
    - Recalcula avg_xp/avg_aura en guilds.json
    """
    if not guild_name:
        return stats_obj

    # Mapear nombres antiguos a nuevos
    if guild_name == "Dawnkeepers":
        guild_name = "Order of Dawn"
    elif guild_name == "Echoes of the Veil":
        guild_name = "Void Echoes"

    # 1) Actualizar stats["guild_ranking"] (para success rate)
    guild_ranking = stats_obj.get("guild_ranking", {})
    if guild_name not in guild_ranking:
        guild_ranking[guild_name] = {
            "xp": 0,
            "aura": 0,
            "successes": 0,
            "failures": 0
        }

    guild_ranking[guild_name]["xp"]   += xp_gain
    guild_ranking[guild_name]["aura"] += aura_gain

    if success:
        guild_ranking[guild_name]["successes"] = guild_ranking[guild_name].get("successes", 0) + 1
    else:
        guild_ranking[guild_name]["failures"] = guild_ranking[guild_name].get("failures", 0) + 1

    stats_obj["guild_ranking"] = guild_ranking

    # 2) 🔥 Actualizar guilds.json directamente
    guilds_data = load_json(GUILDS_PATH, [])
    for guild in guilds_data:
        if guild.get("name") == guild_name:
            # Incrementar contador de misiones
            if success:
                guild["total_missions_completed"] = guild.get("total_missions_completed", 0) + 1
            else:
                guild["total_missions_failed"] = guild.get("total_missions_failed", 0) + 1

            # Actualizar XP/Aura total del gremio
            guild["total_xp"] = guild.get("total_xp", 0) + xp_gain
            guild["total_aura"] = guild.get("total_aura", 0) + aura_gain

            # Recalcular promedios
            members = guild.get("members", 1)
            guild["avg_xp"] = round(guild["total_xp"] / members, 2) if members > 0 else 0
            guild["avg_aura"] = round(guild["total_aura"] / members, 2) if members > 0 else 0
            break

    save_json(GUILDS_PATH, guilds_data)

    return stats_obj

# ---------------------------------
# Flask App
# ---------------------------------

app = Flask(
    __name__,
    static_folder="static",
    static_url_path=""  # sirve /img/... /music/... directo
)

# Configure CORS to allow requests from www.emberholmportal.xyz
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://www.emberholmportal.xyz",
            "https://emberholmportal.xyz",
            "http://localhost:*",
            "http://127.0.0.1:*"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Initialize missions configuration
MISSIONS_CONFIG = load_missions_config()
MISSIONS = MISSIONS_CONFIG.get("missions", [])
DEATH_COSTS = MISSIONS_CONFIG.get("death_costs", {})
BONUSES = MISSIONS_CONFIG.get("bonuses", {})

# Initialize events configuration
EVENTS_CONFIG = load_events_config()
EVENTS = EVENTS_CONFIG.get("events", [])
EVENT_SETTINGS = EVENTS_CONFIG.get("event_settings", {})

# ---------------------------------
# Rutas estáticas base
# ---------------------------------

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")
@app.route("/mint")
def serve_mint():
    # mint.html está en la carpeta raíz del proyecto (C:\EmberholmServer)
    return render_template("mint.html")
# servir whitepapers desde /static/docs
@app.route("/docs/<path:filename>")
def serve_docs(filename):
    docs_dir = os.path.join(app.static_folder, "docs")
    return send_from_directory(docs_dir, filename)

# ---------------------------------
# API: STATS
# ---------------------------------

@app.route("/api/stats")
def api_stats():
    stats_obj = load_json(STATS_PATH, {})

    # 🔥 Calcular ranking real de guilds
    guild_rank_list = calculate_guild_ranking()

    # 🔥 Calcular leaderboard real de jugadores
    leaderboard = calculate_player_leaderboard()

    # 🔥 Contar misiones activas en tiempo real
    missions_in_progress = count_active_missions()

    resp = {
        "total_characters":     stats_obj.get("total_characters", 0),  # 🔥 Real value from blockchain contract
        "active_guilds":        stats_obj.get("active_guilds", 6),
        "missions_completed":   stats_obj.get("missions_completed", 0),
        "missions_failed":      stats_obj.get("missions_failed", 0),
        "missions_in_progress": missions_in_progress,  # 🔥 Real-time count
        "total_exp_collected":  stats_obj.get("total_exp_collected", 0),
        "total_aura_collected": stats_obj.get("total_aura_collected", 0),
        "guild_ranking":        guild_rank_list,
        "player_leaderboard":   leaderboard,
        "last_updated":         now_utc_str()  # 🔥 Timestamp de actualización
    }
    return jsonify(resp)

# ---------------------------------
# API: GUILDS
# ---------------------------------

@app.route("/api/guilds")
def api_guilds():
    # 🔥 Recalcular datos reales antes de devolver
    guilds_data = calculate_guilds_data()

    return jsonify({
        "guilds": guilds_data,
        "last_updated": now_utc_str()  # 🔥 Timestamp de actualización
    })

# ---------------------------------
# API: MISSIONS
# ---------------------------------

@app.route("/api/missions")
def api_missions():
    """Return all available missions"""
    return jsonify({"missions": MISSIONS})

@app.route("/api/events")
def api_events():
    """Return all active events (filtered by availability dates)"""
    from datetime import datetime

    active_events = []
    current_time = datetime.utcnow()

    for event in EVENTS:
        available_from_str = event.get("available_from")
        available_until_str = event.get("available_until")
        event_active = event.get("event_active", True)

        # Check if event is active
        if not event_active:
            continue

        # Parse dates
        try:
            available_from = datetime.fromisoformat(available_from_str.replace("Z", ""))
            available_until = datetime.fromisoformat(available_until_str.replace("Z", ""))

            # Check if current time is within event window
            if available_from <= current_time <= available_until:
                # Calculate time remaining
                time_remaining_seconds = (available_until - current_time).total_seconds()
                event_copy = event.copy()
                event_copy["time_remaining_hours"] = round(time_remaining_seconds / 3600, 1)
                active_events.append(event_copy)
        except (ValueError, AttributeError) as e:
            print(f"⚠️ Error parsing event dates for {event.get('name')}: {e}")
            continue

    return jsonify({
        "events": active_events,
        "event_settings": EVENT_SETTINGS
    })

# ---------------------------------
# API: REALM DISPATCH LIVE FEED
# ---------------------------------
# REALM FEED EVENT POOLS
# ---------------------------------

# Pool de eventos de gremios (48 eventos variados)
GUILD_EVENTS_POOL = {
    'Circle of Mist': [
        'performing arcane node stabilization ritual at Crystal Spire',
        'containing mana overflow in the Western Sanctum',
        'discovered forbidden tome in Ancient Library ruins',
        'repairing reality fracture near Veilweaver Sanctum',
        'achieved major alchemical breakthrough - new elixir formula',
        'emergency response to portal experiment malfunction',
        'investigating temporal anomaly at Chronokeep Tower',
        'confirms successful transmutation of Void Essence'
    ],
    'Order of Dawn': [
        'conducting dawn blessing ceremony for new recruits',
        'reinforcing Ember Core protection barriers',
        'hosting sacred oath renewal at Cathedral of Light',
        'opening new healing sanctuary in Southern Quarter',
        'completing Light barrier reinforcement around city walls',
        'leading corruption cleansing operation in Blighted Woods',
        'witnessing paladin vow ceremony - 12 new paladins sworn',
        'report successful consecration of new temple grounds'
    ],
    'Shadow Guild': [
        'expanded intelligence network into Northern Territories',
        'completed covert operation - target eliminated cleanly',
        'negotiating black market trade agreement with outlanders',
        'extracted high-value informant from enemy compound',
        'assassination contract executed - no witnesses',
        'discovered new smuggling route through Undercity',
        'upgraded surveillance system - 47 new monitoring points',
        'intercepted enemy communications - intel gathered'
    ],
    'Forge Legion': [
        'master weaponsmith forged legendary blade - Dragon\'s Fang',
        'completed defense fortification of Eastern Battlements',
        'conducting battle formation drills - 200 warriors training',
        'war council assembled - strategy session in progress',
        'restored ancient armor set from First Age',
        'deployed siege engines to Northern Front',
        'warrior oath ceremony - 30 new legionnaires sworn',
        'reports successful stress test of new fortress design'
    ],
    'Void Echoes': [
        'sealed major Veil breach at coordinates [X:334, Y:891]',
        'negotiating with spectral entity - treaty terms discussed',
        'death-right contract signed with House Mournveil',
        'performing forbidden necromantic ritual at Bone Crypts',
        'completed soul binding ceremony - 5 spectrals bound',
        'contained dangerous Void entity attempting incursion',
        'resurrection rite completed - subject returned from beyond',
        'reports successful communion with ancient death god'
    ],
    'Horizon Watch': [
        'mapped uncharted territory - 40 square miles surveyed',
        'detected border incursion at Western Frontier',
        'observing unusual tide patterns near Coastal Cliffs',
        'tracking wild beast migration through Thunder Plains',
        'issued storm warning - severe conditions approaching',
        'discovered new settlement ruins in Deep Wilderness',
        'established trade route to remote village of Thornhaven',
        'reports sighting of rare creatures near Mistwood Forest'
    ]
}

# Pool de eventos generales del reino (20 eventos)
REALM_EVENTS_POOL = [
    {'type': 'realm_alert', 'content': 'ALERT: Ember Core fluctuation detected - Realm stability at 78%', 'severity': 'high'},
    {'type': 'realm_alert', 'content': 'ALERT: Ember Core fluctuation detected - Realm stability at 85%', 'severity': 'medium'},
    {'type': 'realm_alert', 'content': 'ALERT: Void Storm approaching from Northern territories', 'severity': 'high'},
    {'type': 'merchant_arrival', 'content': 'Wandering Merchant arrived at Central Plaza with rare artifacts', 'severity': 'info'},
    {'type': 'merchant_arrival', 'content': 'Traveling Alchemist selling exotic potions at Market Square', 'severity': 'info'},
    {'type': 'weather_event', 'content': 'Ash Storm detected - visibility reduced across Eastern District', 'severity': 'medium'},
    {'type': 'weather_event', 'content': 'Blood Moon rising tonight - magical energies amplified', 'severity': 'info'},
    {'type': 'ritual_completion', 'content': 'Grand Eclipse Ritual completed - Realm blessed with protection for 7 days', 'severity': 'success'},
    {'type': 'ritual_completion', 'content': 'Consecration Ceremony concluded - all shrines restored', 'severity': 'success'},
    {'type': 'resource_discovery', 'content': 'Rich Aether Vein discovered near Forgotten Mines', 'severity': 'success'},
    {'type': 'resource_discovery', 'content': 'Ancient Mana Well located in Deep Caverns', 'severity': 'success'},
    {'type': 'creature_sighting', 'content': 'Ancient Dragon spotted circling Eastern Mountains', 'severity': 'high'},
    {'type': 'creature_sighting', 'content': 'Void Beast tracks found near village outskirts', 'severity': 'medium'},
    {'type': 'portal_activity', 'content': 'Unstable portal opened at coordinates [X:245, Y:892]', 'severity': 'high'},
    {'type': 'portal_activity', 'content': 'Rift stabilized at Old Battlefield site', 'severity': 'medium'},
    {'type': 'celebration', 'content': 'Festival of Embers begins - XP bonus active realm-wide', 'severity': 'success'},
    {'type': 'celebration', 'content': 'Harvest Moon Festival declared - markets overflow with goods', 'severity': 'success'},
    {'type': 'realm_alert', 'content': 'SYSTEM: Mana network operating at optimal capacity', 'severity': 'info'},
    {'type': 'realm_alert', 'content': 'WARNING: Anomalous energy signature detected in Void Quarter', 'severity': 'medium'},
    {'type': 'realm_alert', 'content': 'NOTICE: Realm defenses reinforced - threat level reduced', 'severity': 'info'}
]

# Nombres de misiones para eventos simulados
MISSION_NAMES = [
    'The Lost Forge', 'Circle Interference Node', 'Dawn Patrol', 'Shadow Infiltration',
    'Horizon Survey', 'Veil Breach Containment', 'Dragons Crucible', 'Void Descent',
    'Eclipse Ritual'
]

# ---------------------------------

def get_time_ago(timestamp_str):
    """
    Convierte un timestamp ISO a formato "X hours ago"
    """
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.utcnow()
        delta = now - timestamp

        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"
    except:
        return "recently"

@app.route('/api/realm-feed')
def get_realm_feed():
    """
    Retorna los últimos eventos del reino para el Live Feed
    Incluye: misiones reales, eventos simulados de emisarios, alertas de gremios, eventos del reino
    """
    try:
        feed_items = []
        now = datetime.utcnow()

        # 1. EVENTOS REALES - Cargar datos de NFTs para obtener misiones recientes (20% del feed)
        nfts_data = load_nfts_database()
        mission_events = []
        for nft_id, nft in nfts_data.items():
            if 'dynamic_state' in nft:
                state = nft['dynamic_state']
                if state.get('last_update'):
                    last_mission = state.get('last_mission_name', 'Unknown Mission')
                    xp_total = state.get('xp_total', 0)
                    aura = state.get('aura_level', 0)

                    mission_events.append({
                        'type': 'mission_complete',
                        'time': get_time_ago(state['last_update']),
                        'content': f"Emissary #{nft_id} completed {last_mission}",
                        'highlight': f"+{xp_total} XP, +{aura} Aura",
                        'timestamp': state['last_update'],
                        'severity': 'success'
                    })

        mission_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        feed_items.extend(mission_events[:2])  # Solo 2 eventos reales

        # 2. EVENTOS SIMULADOS DE EMISARIOS (50% del feed - más variedad)
        emissary_events = []

        # Generar 10 eventos simulados de emisarios
        for i in range(10):
            event_type = random.choice(['mission_started', 'mission_failed', 'mission_in_progress',
                                       'emissary_death', 'party_formed', 'level_up'])
            emissary_id = f"{random.randint(100, 999):05d}"
            mission = random.choice(MISSION_NAMES)
            hours_ago = random.randint(1, 48)
            time_ago = f"{hours_ago} hour{'s' if hours_ago > 1 else ''} ago"

            if event_type == 'mission_started':
                emissary_events.append({
                    'type': 'mission_started',
                    'content': f"Emissary #{emissary_id} embarked on {mission}",
                    'time': time_ago,
                    'severity': 'info'
                })

            elif event_type == 'mission_failed':
                xp_loss = random.randint(50, 200)
                aura_loss = random.randint(10, 50)
                emissary_events.append({
                    'type': 'mission_failed',
                    'content': f"Emissary #{emissary_id} failed {mission}",
                    'highlight': f"-{xp_loss} XP, -{aura_loss} Aura",
                    'time': time_ago,
                    'severity': 'danger'
                })

            elif event_type == 'mission_in_progress':
                hours_remain = random.randint(1, 12)
                emissary_events.append({
                    'type': 'mission_in_progress',
                    'content': f"Emissary #{emissary_id} undertaking {mission}",
                    'highlight': f"{hours_remain}h remaining",
                    'time': time_ago,
                    'severity': 'info'
                })

            elif event_type == 'emissary_death':
                death_num = random.randint(1, 3)
                emissary_events.append({
                    'type': 'emissary_death',
                    'content': f"FALLEN: Emissary #{emissary_id} perished in {mission}",
                    'highlight': f"Death #{death_num}",
                    'time': time_ago,
                    'severity': 'danger'
                })

            elif event_type == 'party_formed':
                leader_id = f"{random.randint(100, 999):05d}"
                emissary_events.append({
                    'type': 'party_formed',
                    'content': f"Party of 5 assembled for {mission}",
                    'highlight': f"Leader: #{leader_id}",
                    'time': time_ago,
                    'severity': 'success'
                })

            elif event_type == 'level_up':
                new_level = random.randint(5, 30)
                guild = random.choice(list(GUILD_EVENTS_POOL.keys()))
                emissary_events.append({
                    'type': 'level_up',
                    'content': f"Emissary #{emissary_id} ascended to Level {new_level}",
                    'highlight': f"Guild: {guild}",
                    'time': time_ago,
                    'severity': 'success'
                })

        feed_items.extend(emissary_events)

        # 3. EVENTOS DE GREMIOS (20% del feed)
        guild_events = []
        for _ in range(4):
            guild = random.choice(list(GUILD_EVENTS_POOL.keys()))
            activity = random.choice(GUILD_EVENTS_POOL[guild])
            hours_ago = random.randint(1, 72)
            time_ago = f"{hours_ago} hour{'s' if hours_ago > 1 else ''} ago"

            guild_events.append({
                'type': 'guild_alert',
                'guild': guild,
                'content': activity,
                'time': time_ago,
                'severity': 'info'
            })

        feed_items.extend(guild_events)

        # 4. EVENTOS GENERALES DEL REINO (10% del feed)
        realm_events = []
        for _ in range(2):
            event = random.choice(REALM_EVENTS_POOL)
            hours_ago = random.randint(1, 96)
            time_ago = f"{hours_ago} hour{'s' if hours_ago > 1 else ''} ago"

            realm_events.append({
                'type': event['type'],
                'content': event['content'],
                'time': time_ago,
                'severity': event['severity']
            })

        feed_items.extend(realm_events)

        # 5. Mezclar y limitar
        random.shuffle(feed_items)
        feed_items = feed_items[:25]  # Aumentado a 25 eventos para más variedad

        return jsonify({
            'success': True,
            'feed': feed_items
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ---------------------------------
# Helpers para NFTs y metadata
# ---------------------------------

def ipfs_to_http(ipfs_url):
    """
    Convierte una URL IPFS a HTTP usando un gateway público.
    Ejemplo: ipfs://bafybeiabc123/00001.png -> https://ipfs.io/ipfs/bafybeiabc123/00001.png
    """
    if not ipfs_url:
        return ""
    if ipfs_url.startswith("ipfs://"):
        # Extraer el hash CID y el path
        ipfs_path = ipfs_url.replace("ipfs://", "")
        return IPFS_GATEWAY + ipfs_path
    return ipfs_url

def get_wallet_token_ids(wallet):
    """
    🔥 Obtiene los token_ids que posee una billetera.

    PRIORIDAD:
    1. Lee desde wallet_nfts.json (cache poblado por frontend)
    2. Si no hay cache, intenta blockchain (solo si hay conexión)

    Returns:
        list: Lista de token_ids (como strings con formato "00001") que posee la wallet
    """

    # 🔥 PRIORIDAD 1: Leer desde cache (poblado por frontend cuando conecta wallet)
    wallet_nfts = load_json(WALLET_NFTS_PATH, {})
    wallet_lower = wallet.lower()

    for w, tokens in wallet_nfts.items():
        if w.lower() == wallet_lower:
            print(f"✅ Using cached NFTs for wallet {wallet[:6]}...{wallet[-4:]}: {len(tokens)} NFTs")
            return tokens

    # 🔥 PRIORIDAD 2: Si no hay cache, intentar blockchain (solo si hay conexión)
    if w3 is None or nft_contract is None:
        print(f"⚠️ No blockchain connection and no cache for wallet: {wallet}")
        return []

    try:
        # Convertir wallet a checksum address
        if Web3 is not None:
            checksum_wallet = Web3.to_checksum_address(wallet)
        else:
            checksum_wallet = wallet

        # 🔥 Usar tokensOfOwner() - una sola llamada eficiente
        print(f"🔍 Querying blockchain for wallet {wallet[:6]}...{wallet[-4:]}")
        token_ids_raw = nft_contract.functions.tokensOfOwner(checksum_wallet).call()

        # Formatear token_ids como strings con 5 dígitos
        token_ids = [str(tid).zfill(5) for tid in token_ids_raw]
        print(f"✅ Blockchain returned {len(token_ids)} NFTs")

        # Cache los resultados para próxima vez
        if token_ids:
            wallet_nfts[wallet] = token_ids
            save_json(WALLET_NFTS_PATH, wallet_nfts)
            print(f"✅ Cached NFTs for wallet {wallet[:6]}...{wallet[-4:]}")

        return token_ids

    except Exception as e:
        print(f"❌ Error querying blockchain for wallet {wallet}: {e}")
        print(f"⚠️ No cache available - returning empty list")
        return []

def create_hero_from_metadata(token_id):
    """
    Crea un objeto hero desde el archivo de metadata del token_id.
    """
    # Cargar metadata base
    filename = f"{str(token_id).zfill(5)}.json"
    path = os.path.join(METADATA_DIR, filename)

    if not os.path.exists(path):
        # Si no existe metadata, crear un hero básico
        return {
            "token_id": str(token_id).zfill(5),
            "name": f"Emissary #{str(token_id).zfill(5)}",
            "race_class": "Unknown",
            "guild": "Unassigned",
            "image_url": "/img/emissary-placeholder.png",
            "dynamic_state": {
                "xp_total": 0,
                "aura_level": 0,
                "energy_current": 100,
                "energy_max": 100,
                "state": "READY",  # READY, ON_MISSION, FALLEN
                "current_guild": "Unassigned",
                "last_update": now_utc_str(),
                "last_energy_refresh": now_utc_str(),
                "mission_history": {},  # {mission_id: timestamp}
                "power_current": 10,
                "xp_level": 1,
                "last_mission": "None",
                # 🔥 CAMPOS ADICIONALES para sistema de misiones completo
                "total_missions_completed": 0,
                "death_count": 0,
                "current_mission_id": None,
                "mission_start_time": None,
                "fallen_time": None
            }
        }

    with open(path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Extraer datos del fixed_profile
    fixed = metadata.get("fixed_profile", {})
    race = fixed.get("race", "Unknown")
    char_class = fixed.get("class", "Unknown")
    guild = fixed.get("starting_guild", "Unassigned")

    # Crear race_class combinado
    race_class = f"{race} {char_class}"

    # Convertir IPFS URL a HTTP usando gateway público
    image_url = ipfs_to_http(metadata.get("image", ""))
    if not image_url:
        image_url = "/img/emissary-placeholder.png"

    # Calcular power_current desde stats (aproximación)
    str_val = fixed.get("str", 10)
    dex_val = fixed.get("dex", 10)
    con_val = fixed.get("con", 10)
    power_current = int((str_val + dex_val + con_val) / 3)

    # Crear hero
    hero = {
        "token_id": str(token_id).zfill(5),
        "name": metadata.get("name", f"Emissary #{str(token_id).zfill(5)}"),
        "race_class": race_class,
        "guild": guild,
        "image_url": image_url,
        "dynamic_state": {
            "xp_total": 0,
            "aura_level": 0,
            "energy_current": 100,
            "energy_max": 100,
            "state": "READY",  # READY, ON_MISSION, FALLEN
            "current_guild": guild,
            "last_update": now_utc_str(),
            "last_energy_refresh": now_utc_str(),
            "mission_history": {},  # {mission_id: timestamp}
            "power_current": power_current,
            "xp_level": 1,
            "last_mission": "None",
            # 🔥 CAMPOS ADICIONALES para sistema de misiones completo
            "total_missions_completed": 0,
            "death_count": 0,
            "current_mission_id": None,
            "mission_start_time": None,
            "fallen_time": None
        }
    }

    return hero

# ---------------------------------
# Helper: asegurar jugador
# ---------------------------------

def ensure_player(wallet):
    """
    🔥 NUEVA VERSIÓN CON BASE DE DATOS CENTRALIZADA

    Devuelve el objeto del jugador para esa wallet.

    FUENTE DE VERDAD: nfts_database.json (atributos dinámicos)
    players.json: Solo cache de sesión para UI

    Flujo:
    1. Obtiene token_ids de la wallet
    2. Sincroniza cada NFT a nfts_database.json
    3. Lee atributos dinámicos desde DB (no desde players.json)
    4. Construye objeto player para la sesión
    """
    # 🔥 NORMALIZE wallet address to lowercase to avoid case sensitivity issues
    wallet = wallet.lower()

    print(f"  🔧 ensure_player() called for {wallet[:6]}...{wallet[-4:]}")

    # Obtener los token_ids que debería tener esta billetera
    expected_token_ids = get_wallet_token_ids(wallet)
    print(f"  📋 expected_token_ids from cache: {expected_token_ids}")

    # 🔥 SINCRONIZAR cada NFT a la base de datos centralizada
    heroes = []
    for token_id in expected_token_ids:
        # Sincronizar NFT a DB (preserva dynamic_state si ya existe)
        nft = sync_nft_to_database(token_id, owner_wallet=wallet)
        heroes.append(nft)
        ds = nft.get("dynamic_state", {})
        print(f"    🔗 NFT {token_id} → DB (state: {ds.get('state', 'READY')}, xp: {ds.get('xp_total', 0)})")

    # Construir objeto player para la sesión (cache temporal)
    total_xp = sum(h["dynamic_state"]["xp_total"] for h in heroes)
    total_aura = sum(h["dynamic_state"]["aura_level"] for h in heroes)
    total_energy = sum(h["dynamic_state"]["energy_current"] for h in heroes)

    player_obj = {
        "wallet": wallet,
        "heroes": heroes,
        "totals": {
            "heroes_count": len(heroes),
            "xp_total_all": total_xp,
            "aura_total_all": total_aura,
            "energy_total_available": total_energy
        }
    }

    # Guardar en players.json (solo cache de sesión, NO fuente de verdad)
    players = load_json(PLAYERS_PATH, {})
    players[wallet] = player_obj
    save_json(PLAYERS_PATH, players)

    print(f"  ✅ Player synced: {len(heroes)} NFTs → DB updated, session cached")

    return player_obj, players

# ---------------------------------
# API: PLAYER PROFILE
# ---------------------------------

@app.route("/api/player/<wallet>", methods=["GET", "POST"])
def api_player(wallet):
    # 🔥 NORMALIZE wallet address to lowercase to avoid case sensitivity issues
    wallet = wallet.lower()

    print(f"\n{'='*60}")
    print(f"🔍 /api/player/{wallet[:6]}...{wallet[-4:]} - Method: {request.method}")

    # 🔥 CRITICAL FIX: Si es POST, SOLO guardar cache y retornar
    # Esto evita doble sincronización que causa pérdida de estado ON_MISSION
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            token_ids = data.get("token_ids", [])
            total_supply = data.get("total_supply", None)

            print(f"📦 POST data received: {len(token_ids)} token_ids, total_supply={total_supply}")

            if token_ids:
                # Guardar los NFTs que posee esta wallet en cache
                wallet_nfts = load_json(WALLET_NFTS_PATH, {})
                print(f"📂 Current wallet_nfts keys: {list(wallet_nfts.keys())}")
                wallet_nfts[wallet] = token_ids
                save_json(WALLET_NFTS_PATH, wallet_nfts)
                print(f"✅ Wallet {wallet[:6]}...{wallet[-4:]} registered with {len(token_ids)} NFTs: {token_ids}")
                print(f"📂 Updated wallet_nfts keys: {list(wallet_nfts.keys())}")

                # 🔥 AUTO-SINCRONIZACIÓN: Sincronizar cada NFT a la base de datos centralizada
                print(f"🔄 AUTO-SYNC: Syncing {len(token_ids)} NFTs to database...")
                synced_count = 0
                for token_id in token_ids:
                    try:
                        # Sincronizar NFT a DB (si existe preserva estado, si es nuevo lo crea)
                        nft = sync_nft_to_database(token_id, owner_wallet=wallet)
                        synced_count += 1
                        ds = nft.get("dynamic_state", {})
                        print(f"  ✅ {token_id} → DB (xp: {ds.get('xp_total', 0)}, state: {ds.get('state', 'READY')})")
                    except Exception as e:
                        print(f"  ⚠️ Error syncing {token_id}: {e}")

                # 🔥 AUTO-RECALCULAR STATS: Actualizar guilds.json con datos reales
                print(f"📊 AUTO-RECALC: Updating global stats...")
                calculate_guilds_data()
                print(f"✅ Auto-sync complete: {synced_count}/{len(token_ids)} NFTs synced to database")

            # 🔥 Guardar total_supply real del contrato para STATS
            if total_supply is not None:
                stats_obj = load_json(STATS_PATH, {})
                stats_obj["total_characters"] = total_supply
                save_json(STATS_PATH, stats_obj)
                print(f"✅ Contract total supply updated: {total_supply} characters")

            print(f"{'='*60}\n")
            # ✅ RETORNAR inmediatamente - NO llamar ensure_player() aquí
            return jsonify({"success": True, "token_ids_cached": len(token_ids), "synced_to_database": synced_count if token_ids else 0})

        except Exception as e:
            print(f"❌ Error processing POST data: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return jsonify({"success": False, "error": str(e)}), 500

    # 🔥 Si es GET, sincronizar jugador y retornar datos
    print(f"🔄 Calling ensure_player() for wallet {wallet[:6]}...{wallet[-4:]}")

    stats_obj = load_json(STATS_PATH, {
        "total_characters": 0,  # 🔥 Will be updated from blockchain contract
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": {},
        "player_leaderboard": []
    })

    player_obj, players_all = ensure_player(wallet)

    # Log estado de heroes
    if player_obj and "heroes" in player_obj:
        for h in player_obj["heroes"]:
            ds = h.get("dynamic_state", {})
            state = ds.get("state", "UNKNOWN")
            token_id = h.get("token_id", "???")
            print(f"  👤 Hero {token_id}: state={state}")
    print(f"{'='*60}\n")

    # aplicar pasivo/regen antes de mostrar
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # 🔥 CRITICAL: Guardar cambios de pasivo/regen de vuelta a la base de datos
    # Si no hacemos esto, los cambios se pierden al reconectar
    for hero in player_obj.get("heroes", []):
        token_id = hero.get("token_id")
        ds = hero.get("dynamic_state", {})
        if token_id:
            # Actualizar solo los campos que apply_passive_and_regen() modifica
            update_nft_dynamic_state(token_id, {
                "xp_total": ds.get("xp_total"),
                "aura_level": ds.get("aura_level"),
                "energy_current": ds.get("energy_current"),
                "last_update": ds.get("last_update"),
                "last_energy_refresh": ds.get("last_energy_refresh")
            })

    # guardar cambios en cache de sesión
    players_all[wallet] = player_obj
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)

    return jsonify(player_obj)

# ---------------------------------
# API: RECOVER ENERGY (gastar XP para recargar energía temprano)
# ---------------------------------

@app.route("/api/player/spend_xp_for_energy", methods=["POST"])
def api_spend_xp():
    data = request.get_json(force=True)
    wallet     = data.get("wallet")
    hero_id    = data.get("hero_id")
    energy_req = int(data.get("energy_request", 0))

    if not wallet or not hero_id or energy_req <= 0:
        abort(400, "invalid input")

    stats_obj = load_json(STATS_PATH, {
        "total_characters": 0,  # 🔥 Will be updated from blockchain contract
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": {},
        "player_leaderboard": []
    })
    player_obj, players_all = ensure_player(wallet)

    # refrescamos pasivo/energía
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # buscar héroe
    hero = None
    for h in player_obj.get("heroes", []):
        if h.get("token_id") == hero_id:
            hero = h
            break
    if not hero:
        abort(404, "hero not found")

    ds = hero["dynamic_state"]
    xp_total       = ds.get("xp_total", 0)
    aura_level     = ds.get("aura_level", 0)
    energy_current = ds.get("energy_current", 0)
    energy_max     = ds.get("energy_max", 100)

    xp_cost = energy_req * XP_COST_PER_ENERGY
    if xp_total < xp_cost:
        abort(400, "not enough xp")

    # aplicar recuperación
    xp_total       -= xp_cost
    energy_current = min(energy_max, energy_current + energy_req)

    ds["xp_total"]       = xp_total
    ds["aura_level"]     = aura_level
    ds["energy_current"] = energy_current
    ds["last_update"]    = now_utc_str()

    # recalcular totales de wallet (llama pasivo otra vez para coherencia)
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    players_all[wallet] = player_obj
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)

    return jsonify({
        "hero_id": hero_id,
        "energy_current": energy_current,
        "xp_total": xp_total
    })

# ---------------------------------
# API: NEW MISSION SYSTEM
# ---------------------------------

def handle_party_mission_start(wallet, hero_ids, mission_id):
    """
    Handle party mission start (5 heroes required)
    """
    # Validate party size
    if len(hero_ids) != 5:
        abort(400, f"Party missions require exactly 5 heroes. Received: {len(hero_ids)}")

    # Find mission
    mission = None
    for m in MISSIONS:
        if m["id"] == mission_id:
            mission = m
            break

    if mission is None:
        # Check if it's an event
        for e in EVENTS:
            if e["id"] == mission_id:
                mission = e
                break

    if mission is None:
        abort(400, "Mission not found")

    # Verify it's a party mission
    if mission.get("party_size") != 5:
        abort(400, "This mission is not a party mission")

    # Load player data
    stats_obj = load_json(STATS_PATH, {
        "total_characters": 0,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": {},
        "player_leaderboard": []
    })
    player_obj, players_all = ensure_player(wallet)
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # Validate all 5 heroes
    heroes = []
    for hero_id in hero_ids:
        hero = None
        for h in player_obj.get("heroes", []):
            if h.get("token_id") == hero_id:
                hero = h
                break

        if hero is None:
            abort(404, f"Hero {hero_id} not found")

        ds = hero["dynamic_state"]

        # Validations
        if ds.get("state") == "FALLEN":
            abort(400, f"Hero {hero_id} is fallen. Perform reinvocation ritual first.")

        if ds.get("state") == "ON_MISSION":
            abort(400, f"Hero {hero_id} is already on a mission")

        # Check energy
        cost_energy = mission["energy_cost"]
        energy_current = ds.get("energy_current", 0)
        if energy_current < cost_energy:
            abort(400, f"Hero {hero_id} doesn't have enough energy. Required: {cost_energy}, Available: {energy_current}")

        # TEMPORARY: Skip cooldown validation for party missions
        # Reason: Mission 003/006/009 can be done solo OR party mode
        # Heroes who did it solo should be able to do party version
        # Future: These missions will be party-only, this won't be needed
        # mission_hist = ds.get("mission_history", {})
        # last_run_ts = mission_hist.get(mission_id)
        # if last_run_ts and hours_since(last_run_ts) < ROTATION_HOURS:
        #     hours_left = ROTATION_HOURS - hours_since(last_run_ts)
        #     abort(400, f"Hero {hero_id} already completed this mission. Cooldown: {hours_left:.1f}h remaining.")

        heroes.append(hero)

    # All validations passed - start mission for all 5 heroes
    now_utc = now_utc_str()

    for hero in heroes:
        ds = hero["dynamic_state"]

        # Deduct energy
        ds["energy_current"] = max(0, ds["energy_current"] - mission["energy_cost"])

        # Set hero state to ON_MISSION
        ds["state"] = "ON_MISSION"
        ds["mission_start_time"] = now_utc
        ds["current_mission_id"] = mission_id
        ds["last_update"] = now_utc

        # Update NFT dynamic state in database
        update_nft_dynamic_state(hero["token_id"], ds)

    # Track active mission (party format)
    active_missions = load_json(ACTIVE_MISSIONS_PATH, {})
    mission_key = f"{wallet}_{mission_id}_party"
    active_missions[mission_key] = {
        "wallet": wallet,
        "hero_ids": hero_ids,
        "mission_id": mission_id,
        "start_time": now_utc,
        "duration_hours": mission["duration_hours"],
        "is_party": True
    }

    save_json(ACTIVE_MISSIONS_PATH, active_missions)

    # Save player data
    players_all[wallet] = player_obj
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)

    print(f"\n🎮 PARTY MISSION STARTED:")
    print(f"  Wallet: {wallet}")
    print(f"  Heroes: {hero_ids}")
    print(f"  Mission: {mission_id} - {mission['name']}")
    print(f"  Duration: {mission['duration_hours']}h")

    # Calculate average success rate
    total_success_rate = 0
    for hero in heroes:
        success_rate, bonus = calculate_mission_success_rate(hero, mission)
        total_success_rate += success_rate

    avg_success_rate = total_success_rate / 5

    return jsonify({
        "success": True,
        "party": True,
        "hero_ids": hero_ids,
        "mission_id": mission_id,
        "mission_name": mission["name"],
        "energy_spent_per_hero": mission["energy_cost"],
        "total_energy_spent": mission["energy_cost"] * 5,
        "duration_hours": mission["duration_hours"],
        "estimated_success_rate": round(avg_success_rate, 2),
        "party_bonus": "+20% rewards for successful heroes",
        "message": f"Party of 5 heroes embarked on {mission['name']}! Duration: {mission['duration_hours']}h"
    })

@app.route("/api/mission/start", methods=["POST"])
def api_mission_start():
    """
    Start a mission (solo or party).
    POST solo: { "wallet": "0x...", "hero_id": "00001", "mission_id": "001" }
    POST party: { "wallet": "0x...", "hero_ids": ["00001", "00002", ...], "mission_id": "003" }
    """
    data = request.get_json(force=True)
    wallet = data.get("wallet")
    hero_id = data.get("hero_id")
    hero_ids = data.get("hero_ids")
    mission_id = data.get("mission_id")

    if not wallet or not mission_id:
        abort(400, "Missing wallet or mission_id")

    # Detect party mission
    is_party = hero_ids is not None and len(hero_ids) > 0

    if is_party:
        # PARTY MISSION (5 HEROES)
        return handle_party_mission_start(wallet.lower(), hero_ids, mission_id)

    # SOLO MISSION (EXISTING CODE CONTINUES)
    if not hero_id:
        abort(400, "Missing hero_id for solo mission")

    # 🔥 NORMALIZE wallet address to lowercase
    wallet = wallet.lower()

    stats_obj = load_json(STATS_PATH, {
        "total_characters": 0,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": {},
        "player_leaderboard": []
    })
    player_obj, players_all = ensure_player(wallet)

    # Apply passive gains
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # Find mission (check both MISSIONS and EVENTS)
    mission = None
    for m in MISSIONS:
        if m["id"] == mission_id:
            mission = m
            break

    # If not found in missions, check events
    if mission is None:
        for e in EVENTS:
            if e["id"] == mission_id:
                mission = e
                break

    if mission is None:
        abort(400, "Mission not found")

    # Find hero
    hero = None
    for h in player_obj.get("heroes", []):
        if h.get("token_id") == hero_id:
            hero = h
            break
    if hero is None:
        abort(404, "Hero not found")

    ds = hero["dynamic_state"]

    # Check if hero is fallen
    if ds.get("state") == "FALLEN":
        abort(400, "Hero is fallen. Perform reinvocation ritual first.")

    # Check if hero is already on a mission
    if ds.get("state") == "ON_MISSION":
        abort(400, "Hero is already on a mission")

    # Check energy
    cost_energy = mission["energy_cost"]
    energy_current = ds.get("energy_current", 0)
    if energy_current < cost_energy:
        abort(400, f"Not enough energy. Required: {cost_energy}, Available: {energy_current}")

    # Check mission cooldown (72h)
    mission_hist = ds.get("mission_history", {})
    last_run_ts = mission_hist.get(mission_id)
    if last_run_ts and hours_since(last_run_ts) < ROTATION_HOURS:
        hours_left = ROTATION_HOURS - hours_since(last_run_ts)
        abort(400, f"This Emissary has already served on this operation. The Order requires {hours_left:.1f}h recovery before redeployment to this mission. Select another assignment.")

    # Deduct energy
    ds["energy_current"] = max(0, energy_current - cost_energy)

    # Set hero state to ON_MISSION
    ds["state"] = "ON_MISSION"
    ds["mission_start_time"] = now_utc_str()
    ds["current_mission_id"] = mission_id
    ds["last_update"] = now_utc_str()

    # Track active mission
    active_missions = load_json(ACTIVE_MISSIONS_PATH, {})
    mission_key = f"{wallet}_{hero_id}"
    active_missions[mission_key] = {
        "wallet": wallet,
        "hero_id": hero_id,
        "mission_id": mission_id,
        "start_time": ds["mission_start_time"],
        "duration_hours": mission["duration_hours"]
    }

    print(f"\n🔥 SAVING ACTIVE MISSION:")
    print(f"  Mission Key: {mission_key}")
    print(f"  Wallet: {wallet}")
    print(f"  Hero ID: {hero_id}")
    print(f"  Mission ID: {mission_id}")
    print(f"  Start Time: {ds['mission_start_time']}")
    print(f"  Duration: {mission['duration_hours']}h")
    print(f"  Total active missions: {len(active_missions)}")

    save_json(ACTIVE_MISSIONS_PATH, active_missions)

    # Verificar que se guardó correctamente
    verify_missions = load_json(ACTIVE_MISSIONS_PATH, {})
    print(f"  ✅ Verified: {len(verify_missions)} missions in database after save")
    if mission_key in verify_missions:
        print(f"  ✅ Mission {mission_key} confirmed in database")
    else:
        print(f"  ❌ WARNING: Mission {mission_key} NOT found in database after save!")

    # 🔥 GUARDAR a base de datos centralizada (fuente de verdad)
    print(f"\n🔥 UPDATING NFT DYNAMIC STATE IN DATABASE:")
    print(f"  Token ID: {hero_id}")
    print(f"  New State: {ds['state']}")
    print(f"  Mission ID: {ds['current_mission_id']}")
    print(f"  Start Time: {ds['mission_start_time']}")

    update_result = update_nft_dynamic_state(hero_id, ds)
    if update_result:
        print(f"  ✅ NFT dynamic state updated successfully")
    else:
        print(f"  ❌ WARNING: Failed to update NFT dynamic state!")

    # Verificar que se guardó el NFT
    verify_nft = get_nft_from_database(hero_id)
    if verify_nft:
        verify_ds = verify_nft.get("dynamic_state", {})
        print(f"  ✅ Verified NFT state: {verify_ds.get('state')}")
        print(f"  ✅ Verified mission ID: {verify_ds.get('current_mission_id')}")
    else:
        print(f"  ❌ WARNING: NFT {hero_id} not found in database!")

    # Guardar también a players.json (cache de sesión)
    players_all[wallet] = player_obj
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)

    # Calculate success rate for display
    success_rate, bonus = calculate_mission_success_rate(hero, mission)

    return jsonify({
        "success": True,
        "hero_id": hero_id,
        "mission_id": mission_id,
        "mission_name": mission["name"],
        "energy_spent": cost_energy,
        "hero_energy_now": ds["energy_current"],
        "duration_hours": mission["duration_hours"],
        "completion_time": datetime.fromisoformat(ds["mission_start_time"].replace("Z", "")) + timedelta(hours=mission["duration_hours"]),
        "estimated_success_rate": success_rate,
        "difficulty": mission["difficulty"],
        "message": f"{hero.get('name', 'Emissary')} has embarked on {mission['name']}! Duration: {mission['duration_hours']}h"
    })

def handle_party_mission_complete(wallet, party_mission):
    """
    Complete party mission (process all 5 heroes individually)
    """
    hero_ids = party_mission["hero_ids"]
    mission_id = party_mission["mission_id"]
    mission_key = party_mission.get("mission_key", f"{wallet}_{mission_id}_party")

    # Find mission
    mission = None
    for m in MISSIONS:
        if m["id"] == mission_id:
            mission = m
            break

    if mission is None:
        # Check events
        for e in EVENTS:
            if e["id"] == mission_id:
                mission = e
                break

    if mission is None:
        abort(400, "Mission not found")

    # Load player data
    stats_obj = load_json(STATS_PATH, {
        "total_characters": 0,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": {},
        "player_leaderboard": []
    })
    player_obj, players_all = ensure_player(wallet)
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # Check if mission is ready to complete
    start_time_str = party_mission.get("start_time")
    if not start_time_str:
        abort(400, "Mission start time not found")

    hours_elapsed = hours_since(start_time_str)
    duration_required = mission["duration_hours"]

    if hours_elapsed < duration_required:
        hours_remaining = duration_required - hours_elapsed
        abort(400, f"Mission not ready. {hours_remaining:.1f} hours remaining")

    # Process each hero individually
    results = []
    total_xp = 0
    total_aura = 0
    party_bonus_multiplier = mission.get("party_bonus_multiplier", 1.2)
    guild_name = None

    for hero_id in hero_ids:
        # Find hero
        hero = None
        for h in player_obj.get("heroes", []):
            if h.get("token_id") == hero_id:
                hero = h
                break

        if hero is None:
            continue

        ds = hero["dynamic_state"]

        # Check if hero is on this mission
        if ds.get("state") != "ON_MISSION" or ds.get("current_mission_id") != mission_id:
            continue

        # Get guild name (for stats update)
        if guild_name is None:
            guild_name = hero.get("guild")

        # Roll outcome for THIS SPECIFIC HERO
        outcome, xp_gain, aura_gain, xp_loss = roll_mission_outcome(hero, mission)

        # Apply party bonus if success
        if outcome == "SUCCESS":
            xp_gain = int(xp_gain * party_bonus_multiplier)
            aura_gain = int(aura_gain * party_bonus_multiplier)

            ds["xp_total"] = ds.get("xp_total", 0) + xp_gain
            ds["aura_level"] = ds.get("aura_level", 0) + aura_gain
            ds["state"] = "READY"
            ds["total_missions_completed"] = ds.get("total_missions_completed", 0) + 1

            # Update mission history
            if "mission_history" not in ds:
                ds["mission_history"] = {}
            ds["mission_history"][mission_id] = now_utc_str()

            # Update global stats
            stats_obj["missions_completed"] = stats_obj.get("missions_completed", 0) + 1
            stats_obj["total_exp_collected"] = stats_obj.get("total_exp_collected", 0) + xp_gain
            stats_obj["total_aura_collected"] = stats_obj.get("total_aura_collected", 0) + aura_gain

            # Update guild stats
            if guild_name:
                update_guild_stats(guild_name, xp_gain, aura_gain, stats_obj)

            total_xp += xp_gain
            total_aura += aura_gain

            # Check and grant achievements
            total_missions_completed = ds.get("total_missions_completed", 0)
            achievements_granted = check_and_grant_mission_achievements(hero_id, total_missions_completed)

        elif outcome == "FAILURE":
            ds["xp_total"] = max(0, ds.get("xp_total", 0) - xp_loss)
            ds["state"] = "READY"
            ds["total_missions_failed"] = ds.get("total_missions_failed", 0) + 1

            # Update mission history (even on failure, still cooldown)
            if "mission_history" not in ds:
                ds["mission_history"] = {}
            ds["mission_history"][mission_id] = now_utc_str()

            stats_obj["missions_failed"] = stats_obj.get("missions_failed", 0) + 1

        elif outcome == "DEATH":
            ds["xp_total"] = max(0, ds.get("xp_total", 0) - xp_loss)
            ds["state"] = "FALLEN"
            ds["death_count"] = ds.get("death_count", 0) + 1
            ds["total_missions_failed"] = ds.get("total_missions_failed", 0) + 1

            # Update mission history (even on death, still cooldown)
            if "mission_history" not in ds:
                ds["mission_history"] = {}
            ds["mission_history"][mission_id] = now_utc_str()

            stats_obj["missions_failed"] = stats_obj.get("missions_failed", 0) + 1

        # Clear mission state
        ds["mission_start_time"] = None
        ds["current_mission_id"] = None
        ds["last_update"] = now_utc_str()

        # Update NFT dynamic state in database
        update_nft_dynamic_state(hero_id, ds)

        results.append({
            "hero_id": hero_id,
            "hero_name": hero.get("name"),
            "outcome": outcome,
            "xp_gain": xp_gain if outcome == "SUCCESS" else 0,
            "aura_gain": aura_gain if outcome == "SUCCESS" else 0,
            "xp_loss": xp_loss if outcome != "SUCCESS" else 0,
            "new_xp_total": ds.get("xp_total", 0),
            "new_aura_total": ds.get("aura_level", 0),
            "new_state": ds.get("state")
        })

    # Remove from active missions
    active_missions = load_json(ACTIVE_MISSIONS_PATH, {})
    if mission_key in active_missions:
        del active_missions[mission_key]
        save_json(ACTIVE_MISSIONS_PATH, active_missions)

    # Save player data
    players_all[wallet] = player_obj
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)

    # Calculate summary
    successes = len([r for r in results if r["outcome"] == "SUCCESS"])
    failures = len([r for r in results if r["outcome"] == "FAILURE"])
    deaths = len([r for r in results if r["outcome"] == "DEATH"])

    print(f"\n🎮 PARTY MISSION COMPLETED:")
    print(f"  Mission: {mission['name']}")
    print(f"  Successes: {successes}, Failures: {failures}, Deaths: {deaths}")
    print(f"  Total XP: {total_xp}, Total Aura: {total_aura}")

    return jsonify({
        "success": True,
        "party": True,
        "mission_name": mission["name"],
        "results": results,
        "summary": {
            "successes": successes,
            "failures": failures,
            "deaths": deaths,
            "total_xp": total_xp,
            "total_aura": total_aura,
            "party_bonus": f"+{int((party_bonus_multiplier - 1) * 100)}%"
        }
    })

@app.route("/api/mission/complete", methods=["POST"])
def api_mission_complete():
    """
    Complete a mission (solo or party).
    POST solo: { "wallet": "0x...", "hero_id": "00001" }
    POST party: Mission is detected automatically from active_missions
    """
    data = request.get_json(force=True)
    wallet = data.get("wallet")
    hero_id = data.get("hero_id")

    if not wallet:
        abort(400, "Missing wallet")

    # 🔥 NORMALIZE wallet address to lowercase
    wallet = wallet.lower()

    # Check if this is a party mission
    active_missions = load_json(ACTIVE_MISSIONS_PATH, {})

    # Look for party mission for this wallet
    party_mission = None
    for key, mission_data in active_missions.items():
        if mission_data.get("is_party") and mission_data.get("wallet") == wallet:
            # Check if the provided hero_id is part of this party
            if hero_id and hero_id in mission_data.get("hero_ids", []):
                party_mission = mission_data.copy()
                party_mission["mission_key"] = key
                break

    if party_mission:
        # PARTY MISSION COMPLETION
        return handle_party_mission_complete(wallet, party_mission)

    # SOLO MISSION COMPLETION (EXISTING CODE CONTINUES)
    if not hero_id:
        abort(400, "Missing hero_id for solo mission")

    stats_obj = load_json(STATS_PATH, {
        "total_characters": 0,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": {},
        "player_leaderboard": []
    })
    player_obj, players_all = ensure_player(wallet)

    # Apply passive gains
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # Find hero
    hero = None
    for h in player_obj.get("heroes", []):
        if h.get("token_id") == hero_id:
            hero = h
            break
    if hero is None:
        abort(404, "Hero not found")

    ds = hero["dynamic_state"]

    # Check if hero is on a mission
    if ds.get("state") != "ON_MISSION":
        abort(400, "Hero is not on a mission")

    mission_id = ds.get("current_mission_id")
    if not mission_id:
        abort(400, "No active mission found")

    # Find mission (check both MISSIONS and EVENTS)
    mission = None
    for m in MISSIONS:
        if m["id"] == mission_id:
            mission = m
            break

    # If not found in missions, check events
    if mission is None:
        for e in EVENTS:
            if e["id"] == mission_id:
                mission = e
                break

    if mission is None:
        abort(400, "Mission configuration not found")

    # Check if mission duration has elapsed
    start_time_str = ds.get("mission_start_time")
    if not start_time_str:
        abort(400, "Mission start time not found")

    hours_elapsed = hours_since(start_time_str)
    if hours_elapsed < mission["duration_hours"]:
        hours_left = mission["duration_hours"] - hours_elapsed
        abort(400, f"Mission not yet complete. {hours_left:.1f} hours remaining")

    # Roll for outcome
    outcome, details = roll_mission_outcome(hero, mission)

    hero_guild_name = hero.get("guild") or ds.get("current_guild", "Unknown Guild")
    total_missions_completed = ds.get("total_missions_completed", 0)

    # Process outcome
    if outcome == "SUCCESS":
        # Mission succeeded
        xp_gain = details["xp_gain"]
        aura_gain = details["aura_gain"]

        ds["xp_total"] = ds.get("xp_total", 0) + xp_gain
        ds["aura_level"] = ds.get("aura_level", 0) + aura_gain
        ds["state"] = "READY"
        ds["last_mission"] = mission["name"]
        ds["current_mission_id"] = None
        ds["mission_start_time"] = None

        # Update mission history
        mission_hist = ds.get("mission_history", {})
        mission_hist[mission_id] = now_utc_str()
        ds["mission_history"] = mission_hist

        # Update mission count
        total_missions_completed += 1
        ds["total_missions_completed"] = total_missions_completed

        # Update stats
        stats_obj["missions_completed"] = stats_obj.get("missions_completed", 0) + 1
        stats_obj["total_exp_collected"] = stats_obj.get("total_exp_collected", 0) + xp_gain
        stats_obj["total_aura_collected"] = stats_obj.get("total_aura_collected", 0) + aura_gain

        # Update guild stats
        stats_obj = update_guild_stats(hero_guild_name, xp_gain, aura_gain, stats_obj, success=True)

        # Check and grant achievements
        achievements_granted = check_and_grant_mission_achievements(hero_id, total_missions_completed)

        # Remove from active missions
        active_missions = load_json(ACTIVE_MISSIONS_PATH, {})
        mission_key = f"{wallet}_{hero_id}"
        if mission_key in active_missions:
            del active_missions[mission_key]
            save_json(ACTIVE_MISSIONS_PATH, active_missions)

        # 🔥 GUARDAR a base de datos centralizada (fuente de verdad)
        ds["last_update"] = now_utc_str()
        update_nft_dynamic_state(hero_id, ds)

        # Guardar también a players.json (cache de sesión)
        player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)
        players_all[wallet] = player_obj
        save_json(PLAYERS_PATH, players_all)
        save_json(STATS_PATH, stats_obj)

        return jsonify({
            "success": True,
            "outcome": "SUCCESS",
            "hero_id": hero_id,
            "mission_name": mission["name"],
            "xp_gained": xp_gain,
            "aura_gained": aura_gain,
            "perfect_alignment": details.get("perfect_alignment", False),
            "hero_xp_now": ds["xp_total"],
            "hero_aura_now": ds["aura_level"],
            "achievements_granted": achievements_granted,
            "message": f"🎉 SUCCESS! {hero.get('name', 'Emissary')} completed {mission['name']}!"
        })

    elif outcome == "FAILURE":
        # Mission failed but hero survived
        xp_loss = details["xp_loss"]

        current_xp = ds.get("xp_total", 0)
        ds["xp_total"] = max(0, current_xp - xp_loss)
        ds["state"] = "READY"
        ds["last_mission"] = f"{mission['name']} (Failed)"
        ds["current_mission_id"] = None
        ds["mission_start_time"] = None

        # Update stats
        stats_obj["missions_failed"] = stats_obj.get("missions_failed", 0) + 1

        # Update guild stats
        stats_obj = update_guild_stats(hero_guild_name, -xp_loss, 0, stats_obj, success=False)

        # Remove from active missions
        active_missions = load_json(ACTIVE_MISSIONS_PATH, {})
        mission_key = f"{wallet}_{hero_id}"
        if mission_key in active_missions:
            del active_missions[mission_key]
            save_json(ACTIVE_MISSIONS_PATH, active_missions)

        # 🔥 GUARDAR a base de datos centralizada (fuente de verdad)
        ds["last_update"] = now_utc_str()
        update_nft_dynamic_state(hero_id, ds)

        # Guardar también a players.json (cache de sesión)
        player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)
        players_all[wallet] = player_obj
        save_json(PLAYERS_PATH, players_all)
        save_json(STATS_PATH, stats_obj)

        return jsonify({
            "success": True,
            "outcome": "FAILURE",
            "hero_id": hero_id,
            "mission_name": mission["name"],
            "xp_lost": xp_loss,
            "hero_xp_now": ds["xp_total"],
            "message": f"⚠️ FAILED: {hero.get('name', 'Emissary')} failed {mission['name']} and lost {xp_loss} XP."
        })

    elif outcome == "DEATH":
        # Hero died
        ds["state"] = "FALLEN"
        ds["fallen_time"] = now_utc_str()
        ds["current_mission_id"] = None
        ds["mission_start_time"] = None
        ds["last_mission"] = f"{mission['name']} (Fallen)"

        # Increment death count
        death_count = ds.get("death_count", 0)
        ds["death_count"] = death_count + 1

        # Calculate reinvocation cost
        xp_cost, aura_cost = get_death_cost(death_count)

        # Update stats
        stats_obj["missions_failed"] = stats_obj.get("missions_failed", 0) + 1
        stats_obj["total_deaths"] = stats_obj.get("total_deaths", 0) + 1

        # Remove from active missions
        active_missions = load_json(ACTIVE_MISSIONS_PATH, {})
        mission_key = f"{wallet}_{hero_id}"
        if mission_key in active_missions:
            del active_missions[mission_key]
            save_json(ACTIVE_MISSIONS_PATH, active_missions)

        # 🔥 GUARDAR a base de datos centralizada (fuente de verdad)
        ds["last_update"] = now_utc_str()
        update_nft_dynamic_state(hero_id, ds)

        # Guardar también a players.json (cache de sesión)
        player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)
        players_all[wallet] = player_obj
        save_json(PLAYERS_PATH, players_all)
        save_json(STATS_PATH, stats_obj)

        return jsonify({
            "success": True,
            "outcome": "DEATH",
            "hero_id": hero_id,
            "mission_name": mission["name"],
            "death_count": ds["death_count"],
            "reinvocation_cost": {
                "xp": xp_cost,
                "aura": aura_cost
            },
            "message": f"💀 FALLEN: {hero.get('name', 'Emissary')} has fallen in {mission['name']}. Reinvocation ritual required."
        })

    else:
        abort(500, "Unknown mission outcome")

@app.route("/api/ritual/reinvoke", methods=["POST"])
def api_ritual_reinvoke():
    """
    Perform reinvocation ritual for a fallen hero.
    POST: {
        "wallet": "0x...",
        "fallen_hero_id": "00001",
        "sacrifices": [
            {"hero_id": "00002", "xp_donate": 300, "aura_donate": 50},
            {"hero_id": "00003", "xp_donate": 200, "aura_donate": 50}
        ]
    }
    """
    data = request.get_json(force=True)
    wallet = data.get("wallet")
    fallen_hero_id = data.get("fallen_hero_id")
    sacrifices = data.get("sacrifices", [])

    if not wallet or not fallen_hero_id or not sacrifices:
        abort(400, "Missing wallet, fallen_hero_id, or sacrifices")

    stats_obj = load_json(STATS_PATH, {
        "total_characters": 0,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": {},
        "player_leaderboard": []
    })
    player_obj, players_all = ensure_player(wallet)

    # Apply passive gains
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # Find fallen hero
    fallen_hero = None
    for h in player_obj.get("heroes", []):
        if h.get("token_id") == fallen_hero_id:
            fallen_hero = h
            break
    if fallen_hero is None:
        abort(404, "Fallen hero not found")

    ds = fallen_hero["dynamic_state"]

    # Check if hero is fallen
    if ds.get("state") != "FALLEN":
        abort(400, "Hero is not fallen")

    # Get death count and calculate cost
    death_count = ds.get("death_count", 0)
    if death_count == 0:
        death_count = 1  # At least first death
    xp_cost, aura_cost = get_death_cost(death_count - 1)

    # Calculate total sacrifice
    total_xp_donated = 0
    total_aura_donated = 0

    for sacrifice in sacrifices:
        sacrifice_hero_id = sacrifice.get("hero_id")
        xp_donate = sacrifice.get("xp_donate", 0)
        aura_donate = sacrifice.get("aura_donate", 0)

        # Find sacrifice hero
        sacrifice_hero = None
        for h in player_obj.get("heroes", []):
            if h.get("token_id") == sacrifice_hero_id:
                sacrifice_hero = h
                break

        if sacrifice_hero is None:
            abort(404, f"Sacrifice hero {sacrifice_hero_id} not found")

        # Check if sacrifice hero is from same wallet
        if sacrifice_hero.get("token_id") == fallen_hero_id:
            abort(400, "Cannot sacrifice the fallen hero itself")

        # Check if sacrifice hero has enough resources
        sac_ds = sacrifice_hero["dynamic_state"]
        sac_xp = sac_ds.get("xp_total", 0)
        sac_aura = sac_ds.get("aura_level", 0)

        if sac_xp < xp_donate:
            abort(400, f"Sacrifice hero {sacrifice_hero_id} doesn't have enough XP")
        if sac_aura < aura_donate:
            abort(400, f"Sacrifice hero {sacrifice_hero_id} doesn't have enough Aura")

        # Deduct from sacrifice hero
        sac_ds["xp_total"] = max(0, sac_xp - xp_donate)
        sac_ds["aura_level"] = max(0, sac_aura - aura_donate)
        sac_ds["last_update"] = now_utc_str()

        total_xp_donated += xp_donate
        total_aura_donated += aura_donate

    # Check if total donation is sufficient
    if total_xp_donated < xp_cost:
        abort(400, f"Insufficient XP. Required: {xp_cost}, Donated: {total_xp_donated}")
    if total_aura_donated < aura_cost:
        abort(400, f"Insufficient Aura. Required: {aura_cost}, Donated: {total_aura_donated}")

    # Revive fallen hero
    ds["state"] = "READY"
    ds["xp_total"] = 100  # Revive with 100 XP
    ds["aura_level"] = 20  # Revive with 20 Aura
    ds["energy_current"] = ds.get("energy_max", 100) // 2  # Revive with 50% energy
    ds["last_update"] = now_utc_str()
    ds["fallen_time"] = None

    # Update stats
    stats_obj["total_reinvocations"] = stats_obj.get("total_reinvocations", 0) + 1

    # Save
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)
    players_all[wallet] = player_obj
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)

    return jsonify({
        "success": True,
        "hero_id": fallen_hero_id,
        "xp_donated": total_xp_donated,
        "aura_donated": total_aura_donated,
        "hero_xp_now": ds["xp_total"],
        "hero_aura_now": ds["aura_level"],
        "hero_energy_now": ds["energy_current"],
        "message": f"✨ REINVOKED: {fallen_hero.get('name', 'Emissary')} has been brought back from the fallen state!"
    })

# ---------------------------------
# API: ADMIN - Poblar base de datos
# ---------------------------------

@app.route("/api/admin/populate_database", methods=["POST"])
def api_admin_populate_database():
    """
    🔥 Endpoint de administración para poblar la base de datos centralizada
    con todos los NFTs desde los archivos de metadata.

    POST: {
        "start_token": 1,        # Token ID inicial (default: 1)
        "end_token": 100,        # Token ID final (default: 100)
        "overwrite": false       # Si true, sobrescribe NFTs existentes
    }

    Útil para:
    - Poblar DB inicial con NFTs ya minteados
    - Sincronizar NFTs sin esperar a que usuarios conecten wallets
    - Mantener estadísticas globales actualizadas
    """
    data = request.get_json(force=True)
    start_token = data.get("start_token", 1)
    end_token = data.get("end_token", 100)
    overwrite = data.get("overwrite", False)

    synced = []
    skipped = []
    errors = []

    print(f"\n🔄 Populating database: tokens {start_token} to {end_token}")

    for token_id in range(start_token, end_token + 1):
        token_id_padded = str(token_id).zfill(5)

        try:
            # Check if metadata file exists
            metadata_file = os.path.join(METADATA_DIR, f"{token_id_padded}.json")
            if not os.path.exists(metadata_file):
                skipped.append({"token_id": token_id_padded, "reason": "metadata file not found"})
                continue

            # Check if already exists in DB
            existing = get_nft_from_database(token_id_padded)
            if existing and not overwrite:
                skipped.append({"token_id": token_id_padded, "reason": "already in database (use overwrite=true)"})
                continue

            # Sync to database
            nft = sync_nft_to_database(token_id, owner_wallet=None)
            synced.append({
                "token_id": token_id_padded,
                "name": nft.get("name"),
                "guild": nft.get("guild"),
                "xp": nft.get("dynamic_state", {}).get("xp_total", 0)
            })
            print(f"  ✅ Synced: {token_id_padded} - {nft.get('name')}")

        except Exception as e:
            errors.append({"token_id": token_id_padded, "error": str(e)})
            print(f"  ❌ Error syncing {token_id_padded}: {e}")

    # Recalcular stats y guilds
    print(f"\n📊 Recalculating global stats...")
    calculate_guilds_data()

    return jsonify({
        "success": True,
        "synced_count": len(synced),
        "skipped_count": len(skipped),
        "errors_count": len(errors),
        "synced": synced,
        "skipped": skipped,
        "errors": errors,
        "message": f"Database populated: {len(synced)} NFTs synced, {len(skipped)} skipped, {len(errors)} errors"
    })

# ---------------------------------
# Helpers internos para metadata dinámica (OpenSea-style)
# ---------------------------------

def load_base_metadata_for_token(token_id):
    """
    Carga data/metadata/<token_id>.json (ej 00001.json)
    y normaliza la info fija:
    - name / description / image
    - fixed_profile{}  (race, class, str, etc.)
    - attributes[]     (fallback si falta algo)
    Devuelve todo en un dict plano usable.
    """
    filename = f"{str(token_id).zfill(5)}.json"
    path = os.path.join(METADATA_DIR, filename)
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # base del resultado
    meta = {
        "token_id":        str(token_id).zfill(5),
        "name":            raw.get("name", f"Emissary #{str(token_id).zfill(5)}"),
        "description":     raw.get("description", "Emissary of Emberholm."),
        "image":           raw.get("image", ""),
        "race":            "Unknown",
        "class":           "Unknown",
        "rarity":          "Unknown",
        "age":             0,
        "starting_guild":  "Unknown",
        "str":             0,
        "dex":             0,
        "con":             0,
        "int":             0,
        "wis":             0,
        "cha":             0,
    }

    # 1) fixed_profile: tu formato real
    fixed = raw.get("fixed_profile", {})
    if isinstance(fixed, dict):
        if "token_id"       in fixed: meta["token_id"]        = fixed["token_id"]
        if "race"           in fixed: meta["race"]            = fixed["race"]
        if "class"          in fixed: meta["class"]           = fixed["class"]
        if "rarity"         in fixed: meta["rarity"]          = fixed["rarity"]
        if "age"            in fixed: meta["age"]             = fixed["age"]
        if "starting_guild" in fixed: meta["starting_guild"]  = fixed["starting_guild"]
        if "str"            in fixed: meta["str"]             = fixed["str"]
        if "dex"            in fixed: meta["dex"]             = fixed["dex"]
        if "con"            in fixed: meta["con"]             = fixed["con"]
        if "int"            in fixed: meta["int"]             = fixed["int"]
        if "wis"            in fixed: meta["wis"]             = fixed["wis"]
        if "cha"            in fixed: meta["cha"]             = fixed["cha"]

    # 2) fallback desde attributes[] si todavía faltan cosas
    attrs = raw.get("attributes", [])
    for trait in attrs:
        ttype = trait.get("trait_type", "").lower()
        val   = trait.get("value")

        if ttype == "id" and meta["token_id"] == str(token_id).zfill(5):
            # ya tenemos token_id, no lo pisamos
            pass
        elif ttype == "race" and meta["race"] == "Unknown":
            meta["race"] = val
        elif ttype == "class" and meta["class"] == "Unknown":
            meta["class"] = val
        elif ttype == "rarity" and meta["rarity"] == "Unknown":
            meta["rarity"] = val
        elif ttype == "guild" and meta["starting_guild"] == "Unknown":
            meta["starting_guild"] = val
        elif ttype == "age" and meta["age"] == 0:
            meta["age"] = val

    return meta


def find_dynamic_state_for_token(token_id):
    """
    Busca en players.json qué wallet contiene este héroe
    y devuelve su dynamic_state (XP / Aura / Energía / última misión).
    Si no está todavía, devolvemos defaults.
    """
    players_all = load_json(PLAYERS_PATH, {})

    for wallet_addr, pobj in players_all.items():
        for hero in pobj.get("heroes", []):
            if hero.get("token_id") == str(token_id).zfill(5):
                ds = hero.get("dynamic_state", {})
                last_mission_name = ds.get("last_mission", "None")
                return {
                    "current_guild":   ds.get("current_guild", hero.get("guild","Unknown")),
                    "xp_total":        ds.get("xp_total", 0),
                    "xp_level":        ds.get("xp_level", 1),
                    "aura_level":      ds.get("aura_level", 0),
                    "energy_current":  ds.get("energy_current", 100),
                    "energy_max":      ds.get("energy_max", 100),
                    "power_current":   ds.get("power_current", 0),
                    "last_update":     ds.get("last_update", now_utc_str()),
                    "last_mission":    last_mission_name,
                }

    return {
        "current_guild":   "Unassigned",
        "xp_total":        0,
        "xp_level":        1,
        "aura_level":      0,
        "energy_current":  100,
        "energy_max":      100,
        "power_current":   0,
        "last_update":     now_utc_str(),
        "last_mission":    "None"
    }

# ---------------------------------
# API: ACHIEVEMENTS
# ---------------------------------

@app.route("/api/achievements")
def api_achievements_list():
    """List all available achievements"""
    return jsonify({
        "success": True,
        "achievements": AVAILABLE_ACHIEVEMENTS
    })

@app.route("/api/achievements/<token_id>")
def api_token_achievements(token_id):
    """Get achievements for a specific token"""
    achievements = get_token_achievements(token_id)

    # Format achievements with details
    detailed_achievements = []
    for ach_id in achievements:
        if ach_id in AVAILABLE_ACHIEVEMENTS:
            ach = AVAILABLE_ACHIEVEMENTS[ach_id]
            detailed_achievements.append({
                "id": ach_id,
                "name": ach["name"],
                "description": ach["description"],
                "icon": ach["icon"]
            })

    return jsonify({
        "success": True,
        "token_id": token_id,
        "achievements": detailed_achievements,
        "total": len(achievements)
    })

@app.route("/api/achievements/grant", methods=["POST"])
def api_grant_achievement():
    """
    Grant an achievement to a token
    POST body: { "token_id": "00042", "achievement_id": "first_mission" }
    """
    data = request.get_json()

    if not data or "token_id" not in data or "achievement_id" not in data:
        return jsonify({"success": False, "error": "Missing token_id or achievement_id"}), 400

    token_id = data["token_id"]
    achievement_id = data["achievement_id"]

    success, message = grant_achievement(token_id, achievement_id)

    return jsonify({
        "success": success,
        "message": message,
        "token_id": token_id,
        "achievement_id": achievement_id
    })

# ---------------------------------
# API: NFT METADATA dinámica tipo DX Terminal / OpenSea
# ---------------------------------

@app.route("/api/metadata/<token_id>")
def api_metadata(token_id):
    """
    Endpoint que OpenSea/marketplaces pueden consultar como tokenURI.
    Combina:
    - metadata fija del héroe (race, STR, etc.)
    - estado dinámico actual (XP, Aura, Energy, Last Mission)
    y lo devuelve TODO dentro de "attributes".
    """
    base_meta = load_base_metadata_for_token(token_id)
    if base_meta is None:
        abort(404, "token metadata not found")

    dyn = find_dynamic_state_for_token(token_id)

    current_guild = dyn.get("current_guild", base_meta.get("starting_guild", "Unknown"))
    starting_guild = base_meta.get("starting_guild", "Unknown")
    energy_str = f"{dyn.get('energy_current',0)} / {dyn.get('energy_max',0)}"

    # Get achievements for this token
    achievements = get_token_achievements(token_id)

    traits = [
        {"trait_type": "Token ID",      "value": base_meta.get("token_id")},
        {"trait_type": "Race",          "value": base_meta.get("race")},
        {"trait_type": "Class",         "value": base_meta.get("class")},
        {"trait_type": "Rarity",        "value": base_meta.get("rarity")},
        {"trait_type": "Starting Guild", "value": starting_guild},
        {"trait_type": "Current Guild",  "value": current_guild},
        {"trait_type": "Age",           "value": base_meta.get("age")},
        {"trait_type": "STR",           "value": base_meta.get("str")},
        {"trait_type": "DEX",           "value": base_meta.get("dex")},
        {"trait_type": "CON",           "value": base_meta.get("con")},
        {"trait_type": "INT",           "value": base_meta.get("int")},
        {"trait_type": "WIS",           "value": base_meta.get("wis")},
        {"trait_type": "CHA",           "value": base_meta.get("cha")},
        {"trait_type": "XP Total",      "value": dyn.get("xp_total", 0)},
        {"trait_type": "Level",         "value": dyn.get("xp_level", 1)},
        {"trait_type": "Aura",          "value": dyn.get("aura_level", 0)},
        {"trait_type": "Energy",        "value": energy_str},
        {"trait_type": "Power",         "value": dyn.get("power_current", 0)},
        {"trait_type": "Last Mission",  "value": dyn.get("last_mission", "None")},
        {"trait_type": "Last Update",   "value": dyn.get("last_update", now_utc_str())}
    ]

    # Add achievements to attributes
    for ach_id in achievements:
        if ach_id in AVAILABLE_ACHIEVEMENTS:
            ach = AVAILABLE_ACHIEVEMENTS[ach_id]
            traits.append({
                "trait_type": f"Achievement: {ach['name']}",
                "value": "✅"
            })

    # Add total achievements count
    if len(achievements) > 0:
        traits.append({
            "display_type": "number",
            "trait_type": "Total Achievements",
            "value": len(achievements)
        })

    response = {
        "name":        base_meta.get("name", f"Emissary #{str(token_id).zfill(5)}"),
        "description": base_meta.get("description", "Emissary of Emberholm."),
        "image":       base_meta.get("image", ""),
        "attributes":  traits
    }

    return jsonify(response)

# ---------------------------------
# Auto-populate database on startup
# ---------------------------------

# 🔥 NO sincronizar metadata al inicio - los member counts son fijos en guilds.json
# Solo sincronizar NFTs cuando los usuarios conecten sus wallets (auto-sync en POST /api/player)
# XP/Aura/Misiones se acumulan desde nfts_database.json cuando los NFTs juegan misiones
print("✅ Server initialized - member counts fixed at 35,000 NFTs")
print("   XP/Aura will accumulate as NFTs complete missions")

# ---------------------------------
# Run local dev server
# ---------------------------------
# 🔥 VALIDACIÓN DE INTEGRIDAD DE DATOS
# ---------------------------------

def validate_nft_dynamic_state(nft):
    """
    Valida que un NFT tenga todos los campos dinámicos requeridos.
    Si faltan campos, los agrega con valores por defecto.

    Args:
        nft: Objeto NFT desde nfts_database.json

    Returns:
        NFT validado y corregido
    """
    if "dynamic_state" not in nft:
        nft["dynamic_state"] = {}

    ds = nft["dynamic_state"]

    # 🔥 CAMPOS REQUERIDOS con valores por defecto
    required_fields = {
        "xp_total": 0,
        "aura_level": 0,
        "energy_current": 100,
        "energy_max": 100,
        "state": "READY",
        "current_guild": nft.get("guild", "Unassigned"),
        "last_update": now_utc_str(),
        "last_energy_refresh": now_utc_str(),
        "mission_history": {},
        "power_current": 10,
        "xp_level": 1,
        "last_mission": "None",
        "total_missions_completed": 0,
        "death_count": 0,
        "current_mission_id": None,
        "mission_start_time": None,
        "fallen_time": None
    }

    # Agregar campos faltantes
    for field, default_value in required_fields.items():
        if field not in ds:
            ds[field] = default_value

    nft["dynamic_state"] = ds
    return nft

def validate_database_integrity():
    """
    🔥 VALIDACIÓN COMPLETA DE INTEGRIDAD DE LA BASE DE DATOS

    Verifica que todos los NFTs en nfts_database.json tengan:
    - Todos los campos dinámicos requeridos
    - Valores válidos (no None donde no debe ser)
    - Estructura correcta

    Se ejecuta al iniciar el servidor para garantizar integridad.
    """
    print("\n" + "="*70)
    print("🔍 VALIDATING DATABASE INTEGRITY...")
    print("="*70)

    db = load_nfts_database()
    total_nfts = len(db)
    fixed_count = 0

    print(f"📊 Total NFTs in database: {total_nfts}")

    for token_id, nft in db.items():
        original_nft = json.dumps(nft, sort_keys=True)
        validated_nft = validate_nft_dynamic_state(nft)

        if json.dumps(validated_nft, sort_keys=True) != original_nft:
            db[token_id] = validated_nft
            fixed_count += 1

    if fixed_count > 0:
        print(f"🔧 Fixed {fixed_count} NFTs with missing/invalid fields")
        save_nfts_database(db)
        print(f"✅ Database integrity validated and fixed")
    else:
        print(f"✅ All {total_nfts} NFTs have complete and valid data")

    print("="*70 + "\n")
    return total_nfts, fixed_count

# ---------------------------------
# DEBUG ENDPOINT - PostgreSQL Verification
# ---------------------------------

@app.route("/api/debug/postgresql")
def api_debug_postgresql():
    """
    🔍 DEBUG ENDPOINT - Verificar estado de PostgreSQL

    Este endpoint temporal verifica:
    - Si DATABASE_URL está configurado
    - Si PostgreSQL está disponible
    - Qué tablas existen
    - Cuántos registros hay en cada tabla

    Acceder desde: https://emberholm-portal.onrender.com/api/debug/postgresql
    """
    import os

    result = {
        "timestamp": now_utc_str(),
        "database_url_configured": False,
        "postgresql_available": False,
        "connection_error": None,
        "tables": [],
        "data_counts": {},
        "module_imported": False
    }

    # Check 1: DATABASE_URL configurado
    database_url = os.environ.get('DATABASE_URL')
    result["database_url_configured"] = database_url is not None
    if database_url:
        # Ocultar password en output
        result["database_url_host"] = database_url.split('@')[1].split('/')[0] if '@' in database_url else "unknown"

    # Check 1.5: Verificar si archivos existen
    import os as os_module
    base_dir = os_module.path.dirname(__file__)
    result["files_exist"] = {
        "database.py": os_module.path.exists(os_module.path.join(base_dir, "database.py")),
        "schema.sql": os_module.path.exists(os_module.path.join(base_dir, "schema.sql")),
        "setup_database.py": os_module.path.exists(os_module.path.join(base_dir, "setup_database.py"))
    }

    # Check 2: Módulo database importado
    try:
        result["module_imported"] = POSTGRESQL_AVAILABLE
        result["postgresql_available"] = POSTGRESQL_AVAILABLE
        result["db_module_exists"] = db is not None
    except Exception as e:
        result["module_imported"] = False
        result["postgresql_available"] = False
        result["import_error"] = str(e)
        result["db_module_exists"] = False

        # Intentar importar nuevamente para capturar el error exacto
        try:
            import database as test_db
            result["reimport_test"] = "Success"
        except Exception as reimport_error:
            result["reimport_error"] = str(reimport_error)
            result["reimport_error_type"] = type(reimport_error).__name__

    # Check 3: Intentar conexión y verificar tablas
    if result["postgresql_available"]:
        try:
            conn = db.get_connection()
            if conn:
                with conn.cursor() as cur:
                    # Verificar tablas
                    cur.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """)
                    tables = [row[0] for row in cur.fetchall()]
                    result["tables"] = tables

                    # Contar registros en cada tabla
                    for table in tables:
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cur.fetchone()[0]
                            result["data_counts"][table] = count
                        except Exception as e:
                            result["data_counts"][table] = f"Error: {str(e)}"

                db.release_connection(conn)
                result["status"] = "✅ PostgreSQL funcionando correctamente"
            else:
                result["connection_error"] = "No se pudo obtener conexión del pool"
                result["status"] = "❌ Error obteniendo conexión"
        except Exception as e:
            result["connection_error"] = str(e)
            result["status"] = f"❌ Error conectando: {str(e)}"
    else:
        result["status"] = "⚠️ PostgreSQL no disponible - usando JSON fallback"

    # Check 4: Verificar si hay misiones activas
    if "active_missions" in result["data_counts"]:
        missions_count = result["data_counts"]["active_missions"]
        if isinstance(missions_count, int):
            if missions_count > 0:
                result["missions_status"] = f"✅ {missions_count} misiones activas en PostgreSQL"
            else:
                result["missions_status"] = "⚠️ No hay misiones activas en PostgreSQL"

    # Check 5: Verificar psycopg2
    result["psycopg2_check"] = {}
    try:
        import psycopg2
        result["psycopg2_check"]["installed"] = True
        result["psycopg2_check"]["version"] = psycopg2.__version__
    except ImportError as e:
        result["psycopg2_check"]["installed"] = False
        result["psycopg2_check"]["error"] = str(e)
    except Exception as e:
        result["psycopg2_check"]["installed"] = False
        result["psycopg2_check"]["error"] = f"Unexpected error: {str(e)}"

    # Check 6: Ver qué paquetes están instalados
    try:
        import pkg_resources
        installed_packages = [f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set]
        postgres_related = [pkg for pkg in installed_packages if 'psycopg' in pkg.lower() or 'postgres' in pkg.lower()]
        result["installed_postgres_packages"] = postgres_related
    except:
        result["installed_postgres_packages"] = "Unable to check"

    return jsonify(result)

@app.route("/api/setup/postgresql")
def api_setup_postgresql():
    """
    🔧 SETUP ENDPOINT - Crear tablas de PostgreSQL

    Este endpoint ejecuta el schema SQL para crear todas las tablas.
    Solo debe ejecutarse UNA VEZ después de configurar PostgreSQL.

    Acceder desde: https://emberholm-portal.onrender.com/api/setup/postgresql
    """
    if not POSTGRESQL_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "PostgreSQL no está disponible"
        })

    # Schema SQL (inline para no depender de archivo externo)
    SCHEMA_SQL = """
    -- EMBERHOLM PORTAL - POSTGRESQL SCHEMA

    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    CREATE TABLE IF NOT EXISTS nfts (
        token_id VARCHAR(10) PRIMARY KEY,
        name VARCHAR(255),
        guild VARCHAR(100),
        race_class VARCHAR(100),
        last_known_owner VARCHAR(42),
        dynamic_state JSONB NOT NULL DEFAULT '{}'::jsonb,
        last_update TIMESTAMP DEFAULT NOW(),
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_nfts_owner ON nfts(last_known_owner);
    CREATE INDEX IF NOT EXISTS idx_nfts_guild ON nfts(guild);
    CREATE INDEX IF NOT EXISTS idx_nfts_state ON nfts((dynamic_state->>'state'));
    CREATE INDEX IF NOT EXISTS idx_nfts_xp ON nfts(((dynamic_state->>'xp_total')::int));
    CREATE INDEX IF NOT EXISTS idx_nfts_aura ON nfts(((dynamic_state->>'aura_level')::int));

    CREATE TABLE IF NOT EXISTS active_missions (
        mission_key VARCHAR(100) PRIMARY KEY,
        wallet VARCHAR(42) NOT NULL,
        hero_id VARCHAR(10) NOT NULL,
        mission_id VARCHAR(10) NOT NULL,
        start_time TIMESTAMP NOT NULL,
        duration_hours INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_active_missions_wallet ON active_missions(wallet);
    CREATE INDEX IF NOT EXISTS idx_active_missions_hero ON active_missions(hero_id);
    CREATE INDEX IF NOT EXISTS idx_active_missions_mission ON active_missions(mission_id);

    CREATE TABLE IF NOT EXISTS players (
        wallet VARCHAR(42) PRIMARY KEY,
        player_data JSONB NOT NULL DEFAULT '{}'::jsonb,
        last_update TIMESTAMP DEFAULT NOW(),
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_players_wallet ON players(wallet);

    CREATE TABLE IF NOT EXISTS global_stats (
        id INTEGER PRIMARY KEY DEFAULT 1,
        stats_data JSONB NOT NULL DEFAULT '{}'::jsonb,
        last_update TIMESTAMP DEFAULT NOW(),
        CONSTRAINT single_row_stats CHECK (id = 1)
    );

    INSERT INTO global_stats (id, stats_data)
    VALUES (1, '{
        "total_characters": 0,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "missions_in_progress": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": [],
        "player_leaderboard": []
    }'::jsonb)
    ON CONFLICT (id) DO NOTHING;

    CREATE TABLE IF NOT EXISTS achievements (
        token_id VARCHAR(10),
        achievement_id VARCHAR(100),
        granted_at TIMESTAMP DEFAULT NOW(),
        PRIMARY KEY (token_id, achievement_id)
    );

    CREATE INDEX IF NOT EXISTS idx_achievements_token ON achievements(token_id);
    CREATE INDEX IF NOT EXISTS idx_achievements_id ON achievements(achievement_id);

    CREATE OR REPLACE FUNCTION count_active_missions()
    RETURNS INTEGER AS $$
        SELECT COUNT(*)::INTEGER FROM active_missions;
    $$ LANGUAGE SQL;
    """

    result = {
        "timestamp": now_utc_str(),
        "success": False,
        "tables_created": [],
        "indexes_created": 0,
        "error": None
    }

    try:
        conn = db.get_connection()
        if not conn:
            result["error"] = "No se pudo obtener conexión a PostgreSQL"
            return jsonify(result)

        with conn.cursor() as cur:
            # Ejecutar schema
            cur.execute(SCHEMA_SQL)

            # Verificar tablas creadas
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
            result["tables_created"] = tables

            # Contar índices
            cur.execute("""
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE schemaname = 'public'
            """)
            result["indexes_created"] = cur.fetchone()[0]

        conn.commit()
        db.release_connection(conn)

        result["success"] = True
        result["message"] = f"✅ Setup completado: {len(tables)} tablas creadas, {result['indexes_created']} índices"

    except Exception as e:
        result["error"] = str(e)
        result["message"] = f"❌ Error durante setup: {str(e)}"

    return jsonify(result)

# ---------------------------------
# 🔍 AUDITORÍA COMPLETA DEL SISTEMA
# ---------------------------------

@app.route("/api/audit/system")
def api_audit_system():
    """
    🔍 AUDITORÍA COMPLETA - Verifica integridad del sistema completo

    Verifica:
    - PostgreSQL: conexión, tablas, conteos
    - Misiones activas: estado, progreso, ready to complete
    - NFTs: estados, distribución, totales
    - Estadísticas globales: XP, Aura, success rate
    - Estadísticas por guild: distribución, totales
    - Integridad: inconsistencias, datos corruptos
    """

    audit_result = {
        "timestamp": now_utc_str(),
        "postgresql": {},
        "active_missions": {},
        "nfts": {},
        "global_stats": {},
        "guild_stats": {},
        "integrity_checks": {},
        "recommendations": []
    }

    try:
        # ========================================================================
        # 1. POSTGRESQL STATUS
        # ========================================================================
        audit_result["postgresql"]["available"] = POSTGRESQL_AVAILABLE

        if POSTGRESQL_AVAILABLE and db:
            audit_result["postgresql"]["status"] = "✅ Connected"

            # Verificar tablas y conteos
            try:
                conn = db.get_connection()
                with conn.cursor() as cur:
                    # Contar registros en cada tabla
                    cur.execute("SELECT COUNT(*) FROM nfts")
                    nfts_count = cur.fetchone()[0]

                    cur.execute("SELECT COUNT(*) FROM active_missions")
                    missions_count = cur.fetchone()[0]

                    cur.execute("SELECT COUNT(*) FROM players")
                    players_count = cur.fetchone()[0]

                    cur.execute("SELECT COUNT(*) FROM global_stats")
                    stats_count = cur.fetchone()[0]

                    audit_result["postgresql"]["tables"] = {
                        "nfts": nfts_count,
                        "active_missions": missions_count,
                        "players": players_count,
                        "global_stats": stats_count
                    }
                db.release_connection(conn)
            except Exception as e:
                audit_result["postgresql"]["error"] = str(e)
        else:
            audit_result["postgresql"]["status"] = "❌ Not available"

        # ========================================================================
        # 2. ACTIVE MISSIONS ANALYSIS
        # ========================================================================
        active_missions = load_json(ACTIVE_MISSIONS_PATH, {})
        audit_result["active_missions"]["total"] = len(active_missions)

        missions_by_status = {
            "in_progress": 0,
            "ready_to_complete": 0,
            "details": []
        }

        for mission_key, mission_data in active_missions.items():
            start_time_str = mission_data.get("start_time")
            duration_hours = mission_data.get("duration_hours", 0)

            if start_time_str:
                hours_elapsed = hours_since(start_time_str)
                hours_remaining = duration_hours - hours_elapsed
                progress_pct = min(100, int((hours_elapsed / duration_hours) * 100)) if duration_hours > 0 else 0

                status = "ready_to_complete" if hours_remaining <= 0 else "in_progress"
                missions_by_status[status] += 1

                missions_by_status["details"].append({
                    "mission_key": mission_key,
                    "hero_id": mission_data.get("hero_id"),
                    "mission_id": mission_data.get("mission_id"),
                    "status": status,
                    "progress": f"{progress_pct}%",
                    "hours_elapsed": round(hours_elapsed, 2),
                    "hours_remaining": round(max(0, hours_remaining), 2)
                })

        audit_result["active_missions"]["by_status"] = {
            "in_progress": missions_by_status["in_progress"],
            "ready_to_complete": missions_by_status["ready_to_complete"]
        }
        audit_result["active_missions"]["missions"] = missions_by_status["details"]

        # ========================================================================
        # 3. NFTs ANALYSIS
        # ========================================================================
        nfts_db = load_nfts_database()

        nfts_by_state = {"READY": 0, "ON_MISSION": 0, "FALLEN": 0, "UNKNOWN": 0}
        nfts_by_guild = {}
        total_xp = 0
        total_aura = 0

        for token_id, nft in nfts_db.items():
            ds = nft.get("dynamic_state", {})
            state = ds.get("state", "UNKNOWN")
            guild = nft.get("guild", "Unknown")

            # Mapear nombres
            if guild == "Dawnkeepers":
                guild = "Order of Dawn"
            elif guild == "Echoes of the Veil":
                guild = "Void Echoes"

            nfts_by_state[state] = nfts_by_state.get(state, 0) + 1

            if guild not in nfts_by_guild:
                nfts_by_guild[guild] = {"count": 0, "xp": 0, "aura": 0}

            nfts_by_guild[guild]["count"] += 1
            nfts_by_guild[guild]["xp"] += ds.get("xp_total", 0)
            nfts_by_guild[guild]["aura"] += ds.get("aura_level", 0)

            total_xp += ds.get("xp_total", 0)
            total_aura += ds.get("aura_level", 0)

        audit_result["nfts"]["total"] = len(nfts_db)
        audit_result["nfts"]["by_state"] = nfts_by_state
        audit_result["nfts"]["by_guild"] = nfts_by_guild
        audit_result["nfts"]["totals"] = {
            "xp": total_xp,
            "aura": total_aura
        }

        # ========================================================================
        # 4. GLOBAL STATS
        # ========================================================================
        stats_obj = load_json(STATS_PATH, {})

        audit_result["global_stats"]["missions_completed"] = stats_obj.get("missions_completed", 0)
        audit_result["global_stats"]["missions_failed"] = stats_obj.get("missions_failed", 0)
        audit_result["global_stats"]["total_exp_collected"] = stats_obj.get("total_exp_collected", 0)
        audit_result["global_stats"]["total_aura_collected"] = stats_obj.get("total_aura_collected", 0)

        total_missions = stats_obj.get("missions_completed", 0) + stats_obj.get("missions_failed", 0)
        if total_missions > 0:
            success_rate = round((stats_obj.get("missions_completed", 0) / total_missions) * 100, 2)
        else:
            success_rate = 0

        audit_result["global_stats"]["success_rate"] = f"{success_rate}%"
        audit_result["global_stats"]["total_missions"] = total_missions

        # ========================================================================
        # 5. GUILD STATS
        # ========================================================================
        guilds_data = load_json(GUILDS_PATH, [])
        guild_ranking = stats_obj.get("guild_ranking", {})

        # Fix: Si guild_ranking es lista, convertir a dict
        if isinstance(guild_ranking, list):
            guild_ranking = {}

        guild_stats_summary = []
        for guild in guilds_data:
            guild_name = guild.get("name", "")

            rank_data = guild_ranking.get(guild_name, {})
            successes = rank_data.get("successes", 0)
            failures = rank_data.get("failures", 0)
            total = successes + failures

            guild_stats_summary.append({
                "name": guild_name,
                "members": guild.get("members", 0),
                "total_xp": guild.get("total_xp", 0),
                "total_aura": guild.get("total_aura", 0),
                "avg_xp": guild.get("avg_xp", 0),
                "avg_aura": guild.get("avg_aura", 0),
                "missions_completed": successes,
                "missions_failed": failures,
                "success_rate": f"{round((successes / total * 100), 1) if total > 0 else 0}%"
            })

        audit_result["guild_stats"]["guilds"] = guild_stats_summary

        # ========================================================================
        # 6. INTEGRITY CHECKS
        # ========================================================================
        integrity_issues = []

        # Check 1: NFTs ON_MISSION sin active_mission correspondiente
        active_mission_heroes = set(m.get("hero_id") for m in active_missions.values())

        nfts_on_mission_without_active = []
        for token_id, nft in nfts_db.items():
            ds = nft.get("dynamic_state", {})
            if ds.get("state") == "ON_MISSION":
                if token_id not in active_mission_heroes:
                    nfts_on_mission_without_active.append(token_id)

        if nfts_on_mission_without_active:
            integrity_issues.append({
                "type": "nft_on_mission_without_active_mission",
                "count": len(nfts_on_mission_without_active),
                "nfts": nfts_on_mission_without_active
            })

        # Check 2: Active missions sin NFT correspondiente o con estado != ON_MISSION
        missions_without_nft = []
        missions_with_wrong_state = []

        for mission_key, mission_data in active_missions.items():
            hero_id = mission_data.get("hero_id")
            nft = nfts_db.get(hero_id)

            if not nft:
                missions_without_nft.append(mission_key)
            else:
                ds = nft.get("dynamic_state", {})
                if ds.get("state") != "ON_MISSION":
                    missions_with_wrong_state.append({
                        "mission_key": mission_key,
                        "hero_id": hero_id,
                        "current_state": ds.get("state")
                    })

        if missions_without_nft:
            integrity_issues.append({
                "type": "active_mission_without_nft",
                "count": len(missions_without_nft),
                "missions": missions_without_nft
            })

        if missions_with_wrong_state:
            integrity_issues.append({
                "type": "active_mission_with_wrong_state",
                "count": len(missions_with_wrong_state),
                "details": missions_with_wrong_state
            })

        # Check 3: Verificar que guild_ranking sea dict (no lista)
        if isinstance(stats_obj.get("guild_ranking"), list):
            integrity_issues.append({
                "type": "guild_ranking_wrong_type",
                "message": "guild_ranking es una lista, debería ser dict"
            })

        audit_result["integrity_checks"]["issues_found"] = len(integrity_issues)
        audit_result["integrity_checks"]["issues"] = integrity_issues

        # ========================================================================
        # 7. RECOMMENDATIONS
        # ========================================================================
        if len(integrity_issues) > 0:
            audit_result["recommendations"].append("⚠️ Se encontraron problemas de integridad - revisar integrity_checks.issues")

        if missions_by_status["ready_to_complete"] > 0:
            audit_result["recommendations"].append(f"🎯 {missions_by_status['ready_to_complete']} misiones listas para completar - los usuarios pueden reclamar recompensas")

        if nfts_by_state.get("FALLEN", 0) > 0:
            audit_result["recommendations"].append(f"💀 {nfts_by_state['FALLEN']} NFTs caídos - requieren reinvocación")

        if len(integrity_issues) == 0:
            audit_result["recommendations"].append("✅ No se encontraron problemas de integridad")

        if missions_by_status["in_progress"] > 0:
            audit_result["recommendations"].append(f"🔥 {missions_by_status['in_progress']} misiones en progreso")

        # ========================================================================
        # FINAL STATUS
        # ========================================================================
        if len(integrity_issues) == 0 and POSTGRESQL_AVAILABLE:
            audit_result["overall_status"] = "✅ Sistema funcionando correctamente"
        elif len(integrity_issues) > 0:
            audit_result["overall_status"] = "⚠️ Sistema funcional con problemas de integridad menores"
        else:
            audit_result["overall_status"] = "❌ Problemas críticos detectados"

    except Exception as e:
        audit_result["error"] = str(e)
        audit_result["overall_status"] = "❌ Error durante auditoría"
        import traceback
        audit_result["traceback"] = traceback.format_exc()

    return jsonify(audit_result)

# ---------------------------------
# 🔍 DEBUG: Estado completo de un hero
# ---------------------------------

@app.route("/api/debug/hero/<wallet>/<hero_id>")
def api_debug_hero(wallet, hero_id):
    """
    🔍 DEBUG ENDPOINT - Ver estado completo de un hero específico

    Muestra:
    - Estado en nfts_database (PostgreSQL)
    - Estado en active_missions (PostgreSQL)
    - Estado en players.json (cache)
    """
    wallet = wallet.lower()
    hero_id_padded = str(hero_id).zfill(5)

    result = {
        "wallet": wallet,
        "hero_id": hero_id_padded,
        "nft_in_database": None,
        "active_mission": None,
        "player_cache": None,
        "timestamp": now_utc_str()
    }

    # 1. Estado en nfts_database
    try:
        nft = get_nft_from_database(hero_id_padded)
        if nft:
            result["nft_in_database"] = {
                "exists": True,
                "name": nft.get("name"),
                "guild": nft.get("guild"),
                "dynamic_state": nft.get("dynamic_state", {}),
                "last_update": nft.get("last_update")
            }
        else:
            result["nft_in_database"] = {"exists": False}
    except Exception as e:
        result["nft_in_database"] = {"error": str(e)}

    # 2. Estado en active_missions
    try:
        active_missions = load_json(ACTIVE_MISSIONS_PATH, {})
        mission_key = f"{wallet}_{hero_id_padded}"

        result["active_mission"] = {
            "mission_key": mission_key,
            "exists": mission_key in active_missions,
            "data": active_missions.get(mission_key),
            "total_active_missions": len(active_missions),
            "all_missions_keys": list(active_missions.keys())
        }
    except Exception as e:
        result["active_mission"] = {"error": str(e)}

    # 3. Estado en players.json (cache)
    try:
        players = load_json(PLAYERS_PATH, {})
        player = players.get(wallet)

        if player:
            hero_in_cache = None
            for h in player.get("heroes", []):
                if h.get("token_id") == hero_id_padded:
                    hero_in_cache = h
                    break

            result["player_cache"] = {
                "player_exists": True,
                "hero_in_cache": hero_in_cache is not None,
                "hero_data": hero_in_cache if hero_in_cache else None
            }
        else:
            result["player_cache"] = {"player_exists": False}
    except Exception as e:
        result["player_cache"] = {"error": str(e)}

    return jsonify(result)

# ---------------------------------
# 🔧 MIGRATION: Agregar columna image_url a tabla nfts
# ---------------------------------

@app.route("/api/migration/add_image_url")
def api_migration_add_image_url():
    """
    🔧 MIGRATION ENDPOINT - Agregar columna image_url a tabla nfts

    Esta migración agrega la columna image_url que faltaba en el schema original.
    Es seguro ejecutarla múltiples veces (usa IF NOT EXISTS).
    """
    if not POSTGRESQL_AVAILABLE or not db:
        return jsonify({
            "success": False,
            "error": "PostgreSQL no está disponible"
        }), 500

    result = {
        "success": False,
        "migration": "add_image_url_column",
        "steps_completed": []
    }

    try:
        conn = db.get_connection()

        with conn.cursor() as cur:
            # 1. Agregar columna image_url si no existe
            print("🔧 Adding image_url column to nfts table...")
            cur.execute("""
                ALTER TABLE nfts
                ADD COLUMN IF NOT EXISTS image_url TEXT DEFAULT '/img/emissary-placeholder.png'
            """)
            result["steps_completed"].append("Added image_url column")
            print("✅ Column image_url added successfully")

            # 2. Actualizar registros existentes con image_url desde metadata
            print("🔄 Updating existing NFTs with image_url from metadata...")
            cur.execute("SELECT token_id FROM nfts WHERE image_url IS NULL OR image_url = '/img/emissary-placeholder.png'")
            nfts_to_update = [row[0] for row in cur.fetchall()]

            updated_count = 0
            for token_id in nfts_to_update:
                # Obtener image_url desde metadata
                try:
                    from app import create_hero_from_metadata  # Import local
                    hero = create_hero_from_metadata(token_id)
                    image_url = hero.get('image_url', '/img/emissary-placeholder.png')

                    cur.execute("""
                        UPDATE nfts
                        SET image_url = %s
                        WHERE token_id = %s
                    """, (image_url, token_id))
                    updated_count += 1
                except Exception as e:
                    print(f"⚠️ Error updating image_url for {token_id}: {e}")

            result["steps_completed"].append(f"Updated {updated_count} NFTs with image_url")
            print(f"✅ Updated {updated_count} NFTs with image_url from metadata")

        conn.commit()

        result["success"] = True
        result["message"] = f"✅ Migration completed: image_url column added and {updated_count} NFTs updated"

        print(f"🎉 Migration successful: {result['message']}")

    except Exception as e:
        result["error"] = str(e)
        result["message"] = f"❌ Migration failed: {str(e)}"
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if conn:
            db.release_connection(conn)

    return jsonify(result)

# =========================================================================
# INVENTORY & VAULT SYSTEM - API ENDPOINTS
# =========================================================================

# Feature Flags
FEATURES = {
    "ASH_PROTOCOL_ENABLED": False,  # Set to True when ASH protocol is ready
    "EMBER_GAMBIT_ENABLED": True,
    "EMBER_PUSH_ENABLED": True,
    "LAND_STAKING_ENABLED": False
}

# Economy Configuration
PUSH_COSTS = {
    "easy": {"push25": 50, "push50": 150, "push100": 400},
    "medium": {"push25": 100, "push50": 300, "push100": 800},
    "hard": {"push25": 200, "push50": 600, "push100": 1500},
    "legendary": {"push25": 500, "push50": 1500, "push100": 4000}
}

ENERGY_RESTORE_COSTS = {
    25: 30,
    50: 75,
    100: 150
}

REVIVE_COSTS = {
    1: 25,
    2: 50,
    3: 100,
    4: 200  # Max cost for 4+ deaths
}

BURN_RATE = 100  # 100 EMBER = 1 ASH

D20_REWARDS = {
    1: {"type": "critical_fail", "ember": -100, "item": None},
    2: {"type": "nothing", "ember": 0, "item": None},
    3: {"type": "nothing", "ember": 0, "item": None},
    4: {"type": "nothing", "ember": 0, "item": None},
    5: {"type": "nothing", "ember": 0, "item": None},
    6: {"type": "ember", "ember": 50, "item": None},
    7: {"type": "ember", "ember": 50, "item": None},
    8: {"type": "ember", "ember": 50, "item": None},
    9: {"type": "ember", "ember": 100, "item": None},
    10: {"type": "ember", "ember": 100, "item": None},
    11: {"type": "ember", "ember": 100, "item": None},
    12: {"type": "ember", "ember": 200, "item": None},
    13: {"type": "ember", "ember": 200, "item": None},
    14: {"type": "ember", "ember": 200, "item": None},
    15: {"type": "ember", "ember": 350, "item": None},
    16: {"type": "ember", "ember": 350, "item": None},
    17: {"type": "ember", "ember": 350, "item": None},
    18: {"type": "ember_and_item", "ember": 500, "item": "random_common"},
    19: {"type": "ember_and_item", "ember": 500, "item": "random_common"},
    20: {"type": "natural_20", "ember": 1000, "item": "random_rare_or_epic"}
}

# ---------------------------------
# BALANCE API
# ---------------------------------

@app.route('/api/balance', methods=['GET'])
def get_balance():
    """Get user balance (EMBER, ASH, Gambit rolls)"""
    wallet = request.args.get('wallet', '').lower()

    if not wallet:
        return jsonify({"error": "Wallet address required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({
            "ember_balance": 0,
            "ash_balance": 0,
            "gambit_rolls_today": 0,
            "gambit_rolls_max": 5
        })

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get or create balance
        cursor.execute("""
            INSERT INTO user_balances (wallet, ember_balance, ash_balance, gambit_rolls_today, gambit_rolls_max, gambit_next_reset)
            VALUES (%s, 1000, 0, 0, 5, NOW() + INTERVAL '1 day')
            ON CONFLICT (wallet) DO NOTHING
        """, (wallet,))

        cursor.execute("""
            SELECT ember_balance, ash_balance, gambit_rolls_today, gambit_rolls_max, gambit_next_reset
            FROM user_balances
            WHERE wallet = %s
        """, (wallet,))

        row = cursor.fetchone()

        if not row:
            return jsonify({
                "ember_balance": 1000,
                "ash_balance": 0,
                "gambit_rolls_today": 0,
                "gambit_rolls_max": 5
            })

        # Check if need to reset gambit rolls
        now = datetime.utcnow()
        next_reset = row[4]
        gambit_rolls = row[2]

        if next_reset and now >= next_reset:
            # Reset rolls
            cursor.execute("""
                UPDATE user_balances
                SET gambit_rolls_today = 0, gambit_next_reset = %s
                WHERE wallet = %s
            """, (now + timedelta(days=1), wallet))
            conn.commit()
            gambit_rolls = 0

        db.release_connection(conn)

        return jsonify({
            "ember_balance": row[0],
            "ash_balance": row[1] if FEATURES["ASH_PROTOCOL_ENABLED"] else 0,
            "gambit_rolls_today": gambit_rolls,
            "gambit_rolls_max": row[3]
        })

    except Exception as e:
        print(f"Error getting balance: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# VAULT API
# ---------------------------------

@app.route('/api/vault', methods=['GET'])
def get_vault():
    """Get all items in vault"""
    wallet = request.args.get('wallet', '').lower()
    item_type = request.args.get('type')

    if not wallet:
        return jsonify({"error": "Wallet address required"}), 400

    if not POSTGRESQL_AVAILABLE:
        # Return mock data for testing
        return jsonify({"items": []})

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        if item_type:
            cursor.execute("""
                SELECT i.id, i.name, i.type, i.rarity, i.image_url, i.stats, i.equipped_by,
                       n.name as equipped_by_name
                FROM items i
                LEFT JOIN nfts n ON i.equipped_by = n.token_id
                WHERE i.owner_wallet = %s AND i.type = %s
                ORDER BY
                    CASE i.rarity
                        WHEN 'legendary' THEN 1
                        WHEN 'epic' THEN 2
                        WHEN 'rare' THEN 3
                        WHEN 'common' THEN 4
                    END,
                    i.name
            """, (wallet, item_type))
        else:
            cursor.execute("""
                SELECT i.id, i.name, i.type, i.rarity, i.image_url, i.stats, i.equipped_by,
                       n.name as equipped_by_name
                FROM items i
                LEFT JOIN nfts n ON i.equipped_by = n.token_id
                WHERE i.owner_wallet = %s
                ORDER BY
                    CASE i.rarity
                        WHEN 'legendary' THEN 1
                        WHEN 'epic' THEN 2
                        WHEN 'rare' THEN 3
                        WHEN 'common' THEN 4
                    END,
                    i.name
            """, (wallet,))

        rows = cursor.fetchall()
        items = []

        for row in rows:
            items.append({
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "rarity": row[3],
                "image_url": row[4],
                "stats": row[5],
                "equipped_by": row[6],
                "equipped_by_name": row[7]
            })

        db.release_connection(conn)

        return jsonify({"items": items})

    except Exception as e:
        print(f"Error getting vault: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# EQUIPMENT API
# ---------------------------------

@app.route('/api/equip', methods=['POST'])
def equip_item():
    """Equip an item to an emissary"""
    data = request.get_json()
    item_id = data.get('item_id')
    emissary_id = data.get('emissary_id')

    if not item_id or not emissary_id:
        return jsonify({"error": "item_id and emissary_id required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "message": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get item type
        cursor.execute("SELECT type, equipped_by FROM items WHERE id = %s", (item_id,))
        item_row = cursor.fetchone()

        if not item_row:
            return jsonify({"error": "Item not found"}), 404

        item_type = item_row[0]
        already_equipped_by = item_row[1]

        if already_equipped_by:
            return jsonify({"error": "Item already equipped"}), 400

        # Determine which column to update based on item type
        if item_type == "rune":
            # Handle runes separately (array)
            cursor.execute("""
                UPDATE nfts
                SET rune_ids = array_append(COALESCE(rune_ids, ARRAY[]::integer[]), %s)
                WHERE token_id = %s AND array_length(COALESCE(rune_ids, ARRAY[]::integer[]), 1) < 2
            """, (item_id, emissary_id))
        else:
            # Regular equipment
            column_map = {
                "weapon": "weapon_id",
                "armor": "armor_id",
                "helmet": "helmet_id",
                "accessory": "accessory_id",
                "amulet": "amulet_id"
            }

            column = column_map.get(item_type)
            if not column:
                return jsonify({"error": "Invalid item type"}), 400

            # Update emissary
            cursor.execute(f"""
                UPDATE nfts
                SET {column} = %s
                WHERE token_id = %s
            """, (item_id, emissary_id))

        # Mark item as equipped
        cursor.execute("""
            UPDATE items
            SET equipped_by = %s
            WHERE id = %s
        """, (emissary_id, item_id))

        conn.commit()
        db.release_connection(conn)

        return jsonify({"success": True, "message": "Item equipped successfully"})

    except Exception as e:
        print(f"Error equipping item: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/unequip', methods=['POST'])
def unequip_item():
    """Unequip an item"""
    data = request.get_json()
    item_id = data.get('item_id')

    if not item_id:
        return jsonify({"error": "item_id required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "message": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get item details
        cursor.execute("SELECT type, equipped_by FROM items WHERE id = %s", (item_id,))
        item_row = cursor.fetchone()

        if not item_row:
            return jsonify({"error": "Item not found"}), 404

        item_type = item_row[0]
        equipped_by = item_row[1]

        if not equipped_by:
            return jsonify({"error": "Item not equipped"}), 400

        # Unequip from emissary
        if item_type == "rune":
            cursor.execute("""
                UPDATE nfts
                SET rune_ids = array_remove(rune_ids, %s)
                WHERE token_id = %s
            """, (item_id, equipped_by))
        else:
            column_map = {
                "weapon": "weapon_id",
                "armor": "armor_id",
                "helmet": "helmet_id",
                "accessory": "accessory_id",
                "amulet": "amulet_id"
            }

            column = column_map.get(item_type)
            if column:
                cursor.execute(f"""
                    UPDATE nfts
                    SET {column} = NULL
                    WHERE token_id = %s AND {column} = %s
                """, (equipped_by, item_id))

        # Clear equipped_by in item
        cursor.execute("""
            UPDATE items
            SET equipped_by = NULL
            WHERE id = %s
        """, (item_id,))

        conn.commit()
        db.release_connection(conn)

        return jsonify({"success": True, "message": "Item unequipped successfully"})

    except Exception as e:
        print(f"Error unequipping item: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# LAND BINDING API
# ---------------------------------

@app.route('/api/bind-land', methods=['POST'])
def bind_land():
    """Bind a land to an emissary"""
    data = request.get_json()
    land_id = data.get('land_id')
    emissary_id = data.get('emissary_id')

    if not land_id or not emissary_id:
        return jsonify({"error": "land_id and emissary_id required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "message": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Check if land exists and has space
        cursor.execute("""
            SELECT bound_emissaries, max_emissaries
            FROM lands
            WHERE id = %s
        """, (land_id,))

        land_row = cursor.fetchone()
        if not land_row:
            return jsonify({"error": "Land not found"}), 404

        bound_emissaries = land_row[0] or []
        max_emissaries = land_row[1]

        if len(bound_emissaries) >= max_emissaries:
            return jsonify({"error": "Land is full"}), 400

        # Bind emissary to land
        cursor.execute("""
            UPDATE nfts
            SET land_id = %s
            WHERE token_id = %s
        """, (land_id, emissary_id))

        # Add emissary to land's bound list
        cursor.execute("""
            UPDATE lands
            SET bound_emissaries = array_append(bound_emissaries, %s)
            WHERE id = %s
        """, (emissary_id, land_id))

        conn.commit()
        db.release_connection(conn)

        return jsonify({"success": True, "message": "Land bound successfully"})

    except Exception as e:
        print(f"Error binding land: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/unbind-land', methods=['POST'])
def unbind_land():
    """Unbind land from emissary"""
    data = request.get_json()
    emissary_id = data.get('emissary_id')

    if not emissary_id:
        return jsonify({"error": "emissary_id required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "message": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get current land_id
        cursor.execute("SELECT land_id FROM nfts WHERE token_id = %s", (emissary_id,))
        row = cursor.fetchone()

        if not row or not row[0]:
            return jsonify({"error": "No land bound"}), 400

        land_id = row[0]

        # Unbind from emissary
        cursor.execute("""
            UPDATE nfts
            SET land_id = NULL
            WHERE token_id = %s
        """, (emissary_id,))

        # Remove from land's bound list
        cursor.execute("""
            UPDATE lands
            SET bound_emissaries = array_remove(bound_emissaries, %s)
            WHERE id = %s
        """, (emissary_id, land_id))

        conn.commit()
        db.release_connection(conn)

        return jsonify({"success": True, "message": "Land unbound successfully"})

    except Exception as e:
        print(f"Error unbinding land: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# EMBER PUSH (Accelerate Mission)
# ---------------------------------

@app.route('/api/mission/push', methods=['POST'])
def push_mission():
    """Accelerate mission using EMBER"""
    if not FEATURES["EMBER_PUSH_ENABLED"]:
        return jsonify({"error": "Feature not enabled"}), 403

    data = request.get_json()
    emissary_id = data.get('emissary_id')
    push_percent = data.get('push_percent')  # 25, 50, or 100
    wallet = data.get('wallet', '').lower()

    if not all([emissary_id, push_percent, wallet]):
        return jsonify({"error": "Missing required fields"}), 400

    if push_percent not in [25, 50, 100]:
        return jsonify({"error": "Invalid push_percent"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "message": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get mission details
        cursor.execute("""
            SELECT mission_id, start_time, duration_hours
            FROM active_missions
            WHERE hero_id = %s AND wallet = %s
        """, (emissary_id, wallet))

        mission_row = cursor.fetchone()
        if not mission_row:
            return jsonify({"error": "No active mission found"}), 404

        mission_id = mission_row[0]
        start_time = mission_row[1]
        duration_hours = mission_row[2]

        # Get mission difficulty
        # (Simplified - you should get this from missions config)
        difficulty = "easy"  # Default

        # Get cost
        cost_key = f"push{push_percent}"
        cost = PUSH_COSTS.get(difficulty, {}).get(cost_key, 0)

        # Check balance
        cursor.execute("SELECT ember_balance FROM user_balances WHERE wallet = %s", (wallet,))
        balance_row = cursor.fetchone()

        if not balance_row or balance_row[0] < cost:
            return jsonify({"error": "Insufficient EMBER balance"}), 400

        # Deduct EMBER
        cursor.execute("""
            UPDATE user_balances
            SET ember_balance = ember_balance - %s
            WHERE wallet = %s
        """, (cost, wallet))

        # Calculate time reduction
        time_reduction_hours = (duration_hours * push_percent) / 100.0

        # Update mission start time (make it started earlier)
        new_start_time = start_time - timedelta(hours=time_reduction_hours)

        cursor.execute("""
            UPDATE active_missions
            SET start_time = %s
            WHERE hero_id = %s AND wallet = %s
        """, (new_start_time, emissary_id, wallet))

        conn.commit()
        db.release_connection(conn)

        return jsonify({
            "success": True,
            "message": f"Mission accelerated by {push_percent}%",
            "ember_spent": cost,
            "time_reduced_hours": time_reduction_hours
        })

    except Exception as e:
        print(f"Error pushing mission: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# ENERGY RECOVERY (Restore Energy with EMBER)
# ---------------------------------

@app.route('/api/energy/recover', methods=['POST'])
def recover_energy():
    """Restore emissary energy using EMBER"""
    data = request.get_json()
    emissary_id = data.get('emissary_id')
    amount = data.get('amount')  # 25, 50, or 100
    wallet = data.get('wallet', '').lower()

    if not all([emissary_id, amount, wallet]):
        return jsonify({"error": "Missing required fields"}), 400

    if amount not in [25, 50, 100]:
        return jsonify({"error": "Invalid amount"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "message": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get cost
        cost = ENERGY_RESTORE_COSTS.get(amount, 0)

        # Check balance
        cursor.execute("SELECT ember_balance FROM user_balances WHERE wallet = %s", (wallet,))
        balance_row = cursor.fetchone()

        if not balance_row or balance_row[0] < cost:
            return jsonify({"error": "Insufficient EMBER balance"}), 400

        # Deduct EMBER
        cursor.execute("""
            UPDATE user_balances
            SET ember_balance = ember_balance - %s
            WHERE wallet = %s
        """, (cost, wallet))

        conn.commit()
        db.release_connection(conn)

        # Update energy in player data (JSON storage)
        player_obj, _ = load_or_init_player(wallet)
        heroes = player_obj.get("heroes", [])

        for hero in heroes:
            if str(hero.get("token_id")) == str(emissary_id):
                ds = hero.setdefault("dynamic_state", {})
                energy_current = ds.get("energy_current", 100)
                energy_max = ds.get("energy_max", 100)

                # Add energy (cap at max)
                new_energy = min(energy_max, energy_current + amount)
                ds["energy_current"] = new_energy

                # Save updated player data
                save_player(wallet, player_obj)

                return jsonify({
                    "success": True,
                    "message": f"Restored {amount} energy",
                    "ember_spent": cost,
                    "new_energy": new_energy,
                    "energy_max": energy_max
                })

        return jsonify({"error": "Emissary not found"}), 404

    except Exception as e:
        print(f"Error recovering energy: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# EMBER GAMBIT (D20 Dice Roll)
# ---------------------------------

@app.route('/api/gambit/status', methods=['GET'])
def gambit_status():
    """Get gambit roll status"""
    if not FEATURES["EMBER_GAMBIT_ENABLED"]:
        return jsonify({"error": "Feature not enabled"}), 403

    wallet = request.args.get('wallet', '').lower()

    if not wallet:
        return jsonify({"error": "Wallet required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"rolls_remaining": 5, "next_reset": None})

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT gambit_rolls_today, gambit_rolls_max, gambit_next_reset
            FROM user_balances
            WHERE wallet = %s
        """, (wallet,))

        row = cursor.fetchone()
        db.release_connection(conn)

        if not row:
            return jsonify({"rolls_remaining": 5, "next_reset": None})

        rolls_used = row[0]
        rolls_max = row[1]
        next_reset = row[2]

        # Check if reset needed
        if next_reset and datetime.utcnow() >= next_reset:
            rolls_used = 0

        return jsonify({
            "rolls_remaining": max(0, rolls_max - rolls_used),
            "next_reset": next_reset.isoformat() if next_reset else None
        })

    except Exception as e:
        print(f"Error getting gambit status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/gambit/roll', methods=['POST'])
def gambit_roll():
    """Roll the D20 gambit dice"""
    if not FEATURES["EMBER_GAMBIT_ENABLED"]:
        return jsonify({"error": "Feature not enabled"}), 403

    data = request.get_json()
    wallet = data.get('wallet', '').lower()

    if not wallet:
        return jsonify({"error": "Wallet required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "message": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Check balance and rolls
        cursor.execute("""
            SELECT ember_balance, gambit_rolls_today, gambit_rolls_max
            FROM user_balances
            WHERE wallet = %s
        """, (wallet,))

        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Balance not found"}), 404

        ember_balance = row[0]
        rolls_today = row[1]
        rolls_max = row[2]

        # Check if can roll
        if rolls_today >= rolls_max:
            return jsonify({"error": "No rolls remaining today"}), 400

        roll_cost = 100
        if ember_balance < roll_cost:
            return jsonify({"error": "Insufficient EMBER"}), 400

        # Deduct cost
        cursor.execute("""
            UPDATE user_balances
            SET ember_balance = ember_balance - %s,
                gambit_rolls_today = gambit_rolls_today + 1
            WHERE wallet = %s
        """, (roll_cost, wallet))

        # Roll D20
        roll_result = random.randint(1, 20)
        reward = D20_REWARDS[roll_result]

        # Apply reward
        ember_change = reward["ember"]

        cursor.execute("""
            UPDATE user_balances
            SET ember_balance = ember_balance + %s
            WHERE wallet = %s
        """, (ember_change, wallet))

        conn.commit()
        db.release_connection(conn)

        return jsonify({
            "success": True,
            "roll": roll_result,
            "reward_type": reward["type"],
            "ember_change": ember_change,
            "item": reward["item"]
        })

    except Exception as e:
        print(f"Error rolling gambit: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# ENERGY RESTORE
# ---------------------------------

@app.route('/api/energy/restore', methods=['POST'])
def restore_energy():
    """Restore energy using EMBER"""
    data = request.get_json()
    emissary_id = data.get('emissary_id')
    amount = data.get('amount')  # 25, 50, or 100
    wallet = data.get('wallet', '').lower()

    if not all([emissary_id, amount, wallet]):
        return jsonify({"error": "Missing required fields"}), 400

    if amount not in [25, 50, 100]:
        return jsonify({"error": "Invalid amount"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "message": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get cost
        cost = ENERGY_RESTORE_COSTS.get(amount, 0)

        # Check balance
        cursor.execute("SELECT ember_balance FROM user_balances WHERE wallet = %s", (wallet,))
        balance_row = cursor.fetchone()

        if not balance_row or balance_row[0] < cost:
            return jsonify({"error": "Insufficient EMBER"}), 400

        # Deduct EMBER
        cursor.execute("""
            UPDATE user_balances
            SET ember_balance = ember_balance - %s
            WHERE wallet = %s
        """, (cost, wallet))

        # Restore energy (update dynamic_state)
        cursor.execute("""
            UPDATE nfts
            SET dynamic_state = jsonb_set(
                dynamic_state,
                '{energy_current}',
                to_jsonb(LEAST(100, COALESCE((dynamic_state->>'energy_current')::int, 0) + %s))
            )
            WHERE token_id = %s
        """, (amount, emissary_id))

        conn.commit()
        db.release_connection(conn)

        return jsonify({
            "success": True,
            "message": f"Restored {amount} energy",
            "ember_spent": cost
        })

    except Exception as e:
        print(f"Error restoring energy: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# ASH PROTOCOL (Only if enabled)
# ---------------------------------

@app.route('/api/burn', methods=['POST'])
def burn_ember():
    """Burn EMBER to get ASH"""
    if not FEATURES["ASH_PROTOCOL_ENABLED"]:
        return jsonify({"error": "ASH Protocol not enabled"}), 403

    data = request.get_json()
    wallet = data.get('wallet', '').lower()
    ember_amount = data.get('ember_amount', 0)

    if not wallet or ember_amount <= 0:
        return jsonify({"error": "Invalid request"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "message": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Check balance
        cursor.execute("SELECT ember_balance FROM user_balances WHERE wallet = %s", (wallet,))
        row = cursor.fetchone()

        if not row or row[0] < ember_amount:
            return jsonify({"error": "Insufficient EMBER"}), 400

        # Calculate ASH
        ash_received = ember_amount // BURN_RATE

        if ash_received == 0:
            return jsonify({"error": "Minimum 100 EMBER required"}), 400

        # Update balances
        cursor.execute("""
            UPDATE user_balances
            SET ember_balance = ember_balance - %s,
                ash_balance = ash_balance + %s
            WHERE wallet = %s
        """, (ember_amount, ash_received, wallet))

        conn.commit()
        db.release_connection(conn)

        return jsonify({
            "success": True,
            "ember_burned": ember_amount,
            "ash_received": ash_received
        })

    except Exception as e:
        print(f"Error burning EMBER: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/revive', methods=['POST'])
def revive_emissary():
    """Revive a dead emissary using ASH"""
    if not FEATURES["ASH_PROTOCOL_ENABLED"]:
        return jsonify({"error": "ASH Protocol not enabled"}), 403

    data = request.get_json()
    emissary_id = data.get('emissary_id')
    wallet = data.get('wallet', '').lower()

    if not all([emissary_id, wallet]):
        return jsonify({"error": "Missing required fields"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "message": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get emissary death count
        cursor.execute("""
            SELECT dynamic_state->>'deaths', dynamic_state->>'state'
            FROM nfts
            WHERE token_id = %s
        """, (emissary_id,))

        nft_row = cursor.fetchone()
        if not nft_row:
            return jsonify({"error": "Emissary not found"}), 404

        deaths = int(nft_row[0] or 0)
        state = nft_row[1]

        if state != 'dead':
            return jsonify({"error": "Emissary is not dead"}), 400

        # Get revive cost based on deaths
        death_count = min(deaths, 4)
        cost = REVIVE_COSTS.get(death_count, REVIVE_COSTS[4])

        # Check ASH balance
        cursor.execute("SELECT ash_balance FROM user_balances WHERE wallet = %s", (wallet,))
        balance_row = cursor.fetchone()

        if not balance_row or balance_row[0] < cost:
            return jsonify({"error": "Insufficient ASH"}), 400

        # Deduct ASH
        cursor.execute("""
            UPDATE user_balances
            SET ash_balance = ash_balance - %s
            WHERE wallet = %s
        """, (cost, wallet))

        # Revive emissary
        cursor.execute("""
            UPDATE nfts
            SET dynamic_state = jsonb_set(
                jsonb_set(dynamic_state, '{state}', '"ready"'),
                '{energy_current}',
                '100'
            )
            WHERE token_id = %s
        """, (emissary_id,))

        conn.commit()
        db.release_connection(conn)

        return jsonify({
            "success": True,
            "message": "Emissary revived",
            "ash_spent": cost
        })

    except Exception as e:
        print(f"Error reviving emissary: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------------------------

if __name__ == "__main__":
    # 🔥 VALIDAR INTEGRIDAD AL INICIAR
    validate_database_integrity()

    app.run(debug=True)
