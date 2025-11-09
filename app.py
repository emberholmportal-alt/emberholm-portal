import json
import os
import time
import random
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory, request, abort, render_template

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

# Missions configuration (loaded at startup)
MISSIONS_CONFIG = {}
MISSIONS = []
DEATH_COSTS = {}
BONUSES = {}

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
    if not os.path.exists(path):
        return fallback
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return fallback

def save_json(path, obj):
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
    Calcula el ranking de guilds REAL desde players.json.
    Devuelve lista ordenada por XP total descendente.
    INCLUYE TODOS LOS GREMIOS, incluso los que tienen 0 miembros.
    """
    players_all = load_json(PLAYERS_PATH, {})
    stats_obj = load_json(STATS_PATH, {})

    # Lista de todos los gremios conocidos
    all_guilds = [
        "Forge Legion",
        "Circle of Mist",
        "Shadow Guild",
        "Horizon Watch",
        "Dawnkeepers",
        "Echoes of the Veil"
    ]

    # Inicializar stats para TODOS los gremios
    guild_stats = {}
    for g in all_guilds:
        guild_stats[g] = {
            "xp_total": 0,
            "aura_total": 0,
            "members": 0
        }

    # Recorrer todos los héroes de todos los jugadores
    for wallet, pdata in players_all.items():
        for hero in pdata.get("heroes", []):
            guild = hero.get("guild") or hero.get("dynamic_state", {}).get("current_guild", "Unknown")
            ds = hero.get("dynamic_state", {})

            if guild not in guild_stats:
                guild_stats[guild] = {
                    "xp_total": 0,
                    "aura_total": 0,
                    "members": 0
                }

            guild_stats[guild]["xp_total"] += ds.get("xp_total", 0)
            guild_stats[guild]["aura_total"] += ds.get("aura_level", 0)
            guild_stats[guild]["members"] += 1

    # Agregar success rate desde stats.json
    guild_ranking_stats = stats_obj.get("guild_ranking", {})

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
            "members": data["members"],
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
    Cuenta cuántos NFTs están actualmente en misión (estado ON_MISSION).
    Lee desde la base de datos centralizada.
    """
    db = load_nfts_database()
    count = 0

    for token_id, nft in db.items():
        ds = nft.get("dynamic_state", {})
        if ds.get("state") == "ON_MISSION":
            count += 1

    return count

def calculate_guilds_data():
    """
    Actualiza guilds.json con datos reales de members, avg_xp, avg_aura.
    Lee desde la base de datos centralizada de NFTs.
    """
    db = load_nfts_database()
    guilds_data = load_json(GUILDS_PATH, [])

    # Calcular stats reales por gremio desde la DB centralizada
    guild_stats = {}
    for token_id, nft in db.items():
        guild = nft.get("guild") or nft.get("dynamic_state", {}).get("current_guild", "Unknown")
        ds = nft.get("dynamic_state", {})

        if guild not in guild_stats:
            guild_stats[guild] = {
                "total_xp": 0,
                "total_aura": 0,
                "members": 0
            }

        guild_stats[guild]["total_xp"] += ds.get("xp_total", 0)
        guild_stats[guild]["total_aura"] += ds.get("aura_level", 0)
        guild_stats[guild]["members"] += 1
    
    # Actualizar guilds.json con datos reales
    for g in guilds_data:
        guild_name = g.get("name", "")
        if guild_name in guild_stats:
            stats = guild_stats[guild_name]
            g["members"] = stats["members"]
            g["total_xp"] = stats["total_xp"]
            g["total_aura"] = stats["total_aura"]
            g["avg_xp"] = round(stats["total_xp"] / stats["members"], 2) if stats["members"] > 0 else 0
            g["avg_aura"] = round(stats["total_aura"] / stats["members"], 2) if stats["members"] > 0 else 0
        else:
            # Si no hay datos, poner en 0
            g["members"] = 0
            g["total_xp"] = 0
            g["total_aura"] = 0
            g["avg_xp"] = 0
            g["avg_aura"] = 0
    
    save_json(GUILDS_PATH, guilds_data)
    return guilds_data

def update_guild_stats(guild_name, xp_gain, aura_gain, stats_obj, success=True):
    """
    - Suma XP/Aura ganadas por ese gremio a stats["guild_ranking"].
    - Refleja actividad en guilds.json (members, avg_xp, avg_aura).
    - Actualiza success/failure count.
    """
    if not guild_name:
        return stats_obj

    # 1) stats["guild_ranking"]
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

    # 2) Recalcular guilds.json con datos reales
    calculate_guilds_data()

    return stats_obj

# ---------------------------------
# Flask App
# ---------------------------------

app = Flask(
    __name__,
    static_folder="static",
    static_url_path=""  # sirve /img/... /music/... directo
)

# Initialize missions configuration
MISSIONS_CONFIG = load_missions_config()
MISSIONS = MISSIONS_CONFIG.get("missions", [])
DEATH_COSTS = MISSIONS_CONFIG.get("death_costs", {})
BONUSES = MISSIONS_CONFIG.get("bonuses", {})

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
        "player_leaderboard":   leaderboard
    }
    return jsonify(resp)

# ---------------------------------
# API: GUILDS
# ---------------------------------

@app.route("/api/guilds")
def api_guilds():
    # 🔥 Recalcular datos reales antes de devolver
    guilds_data = calculate_guilds_data()
    return jsonify(guilds_data)

# ---------------------------------
# API: MISSIONS
# ---------------------------------

@app.route("/api/missions")
def api_missions():
    """Return all available missions"""
    return jsonify({"missions": MISSIONS})

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
                "state": "READY",
                "current_guild": "Unassigned",
                "last_update": now_utc_str(),
                "last_energy_refresh": now_utc_str(),
                "mission_history": {},
                "power_current": 10,
                "xp_level": 1,
                "last_mission": "None"
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
            "state": "READY",
            "current_guild": guild,
            "last_update": now_utc_str(),
            "last_energy_refresh": now_utc_str(),
            "mission_history": {},
            "power_current": power_current,
            "xp_level": 1,
            "last_mission": "None"
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

    # guardar cambios
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

@app.route("/api/mission/start", methods=["POST"])
def api_mission_start():
    """
    Start a mission (with staking integration).
    POST: { "wallet": "0x...", "hero_id": "00001", "mission_id": "001" }
    """
    data = request.get_json(force=True)
    wallet = data.get("wallet")
    hero_id = data.get("hero_id")
    mission_id = data.get("mission_id")

    if not wallet or not hero_id or not mission_id:
        abort(400, "Missing wallet, hero_id, or mission_id")

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

    # Find mission
    mission = None
    for m in MISSIONS:
        if m["id"] == mission_id:
            mission = m
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
        abort(400, f"Mission on cooldown. {hours_left:.1f} hours remaining")

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
    save_json(ACTIVE_MISSIONS_PATH, active_missions)

    # 🔥 GUARDAR a base de datos centralizada (fuente de verdad)
    update_nft_dynamic_state(hero_id, ds)

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

@app.route("/api/mission/complete", methods=["POST"])
def api_mission_complete():
    """
    Complete a mission (with probability-based outcome).
    POST: { "wallet": "0x...", "hero_id": "00001" }
    """
    data = request.get_json(force=True)
    wallet = data.get("wallet")
    hero_id = data.get("hero_id")

    if not wallet or not hero_id:
        abort(400, "Missing wallet or hero_id")

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

    # Find mission
    mission = None
    for m in MISSIONS:
        if m["id"] == mission_id:
            mission = m
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
# Run local dev server
# ---------------------------------

if __name__ == "__main__":
    app.run(debug=True)
