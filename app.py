import json
import os
import time
import random
import logging
from collections import defaultdict
from functools import wraps
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, send_from_directory, request, abort, render_template
from flask_cors import CORS

# =========================================================================
# 🔒 STRUCTURED LOGGING
# =========================================================================
logging.basicConfig(
    format='%(asctime)s %(levelname)s [%(name)s]: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('emberholm')

# =========================================================================
# 🚦 RATE LIMITING SYSTEM
# =========================================================================
# In-memory rate limit storage (for production, use Redis)
_rate_limit_storage = defaultdict(list)
_rate_limit_cleanup_last = time.time()

def _cleanup_rate_limits():
    """Clean up old rate limit entries periodically"""
    global _rate_limit_cleanup_last
    now = time.time()
    # Only cleanup every 60 seconds
    if now - _rate_limit_cleanup_last < 60:
        return
    _rate_limit_cleanup_last = now

    cutoff = now - 120  # Remove entries older than 2 minutes
    keys_to_remove = []
    for key, timestamps in _rate_limit_storage.items():
        _rate_limit_storage[key] = [t for t in timestamps if t > cutoff]
        if not _rate_limit_storage[key]:
            keys_to_remove.append(key)
    for key in keys_to_remove:
        del _rate_limit_storage[key]

def rate_limit(requests_per_minute=30, key_func=None):
    """
    Rate limiting decorator for Flask endpoints.

    Args:
        requests_per_minute: Maximum requests allowed per minute
        key_func: Optional function to extract rate limit key from request.
                  If None, uses wallet from JSON body or query params, falls back to IP.

    Usage:
        @app.route("/api/mission/start", methods=["POST"])
        @rate_limit(requests_per_minute=10)
        def api_mission_start():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            _cleanup_rate_limits()

            # Determine rate limit key
            if key_func:
                rate_key = key_func()
            else:
                # Try to get wallet from various sources
                data = request.get_json(silent=True) or {}
                wallet = data.get('wallet') or request.args.get('wallet')

                # Try URL parameters (e.g., /api/player/<wallet>)
                if not wallet and 'wallet' in kwargs:
                    wallet = kwargs['wallet']

                if wallet:
                    rate_key = f"wallet:{str(wallet).lower()}"
                else:
                    rate_key = f"ip:{request.remote_addr}"

            now = time.time()
            window = 60  # 1 minute window

            # Get timestamps within window
            timestamps = _rate_limit_storage[rate_key]
            timestamps = [t for t in timestamps if now - t < window]
            _rate_limit_storage[rate_key] = timestamps

            if len(timestamps) >= requests_per_minute:
                logger.warning(f"Rate limit exceeded: {rate_key} ({len(timestamps)}/{requests_per_minute} requests)")
                return jsonify({
                    'error': 'Rate limit exceeded. Please wait before making more requests.',
                    'retry_after': 60,
                    'limit': requests_per_minute,
                    'window': 'per minute'
                }), 429

            timestamps.append(now)
            _rate_limit_storage[rate_key] = timestamps

            return f(*args, **kwargs)
        return wrapper
    return decorator

# 🔥 POSTGRESQL INTEGRATION - Persistence module
try:
    import database as db
    from psycopg2.extras import RealDictCursor
    POSTGRESQL_AVAILABLE = db.is_postgresql_available()
    if POSTGRESQL_AVAILABLE:
        print("✅ PostgreSQL persistence enabled")
    else:
        print("⚠️ PostgreSQL not configured - using JSON fallback")
except Exception as e:
    print(f"⚠️ PostgreSQL module import failed: {e}")
    POSTGRESQL_AVAILABLE = False
    db = None
    RealDictCursor = None

# 🔥 AUTO-INITIALIZE POSTGRESQL TABLES ON STARTUP
def ensure_postgresql_schema():
    """
    Asegura que las tablas de PostgreSQL existan con todas las columnas necesarias.
    Ejecuta migraciones automáticamente al iniciar el servidor.
    """
    if not POSTGRESQL_AVAILABLE or not db:
        return False

    print("🔧 Checking PostgreSQL schema...")

    conn = None
    try:
        conn = db.get_connection()
        if not conn:
            print("⚠️ Could not get PostgreSQL connection for schema check")
            return False

        with conn.cursor() as cur:
            # 1. Crear tabla active_missions si no existe
            cur.execute("""
                CREATE TABLE IF NOT EXISTS active_missions (
                    mission_key VARCHAR(100) PRIMARY KEY,
                    wallet VARCHAR(42) NOT NULL,
                    hero_id VARCHAR(10),
                    hero_ids JSONB,
                    mission_id VARCHAR(10) NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    duration_hours INTEGER NOT NULL,
                    is_party BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # 2. Migraciones: agregar columnas faltantes
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name = 'active_missions' AND column_name = 'hero_ids') THEN
                        ALTER TABLE active_missions ADD COLUMN hero_ids JSONB;
                        RAISE NOTICE 'Added hero_ids column to active_missions';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name = 'active_missions' AND column_name = 'is_party') THEN
                        ALTER TABLE active_missions ADD COLUMN is_party BOOLEAN DEFAULT FALSE;
                        RAISE NOTICE 'Added is_party column to active_missions';
                    END IF;
                END $$;
            """)

            # 3. Hacer hero_id nullable (para party missions)
            cur.execute("""
                DO $$
                BEGIN
                    ALTER TABLE active_missions ALTER COLUMN hero_id DROP NOT NULL;
                EXCEPTION WHEN OTHERS THEN
                    NULL;
                END $$;
            """)

            # 4. Crear índices si no existen
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_active_missions_wallet ON active_missions(wallet);
                CREATE INDEX IF NOT EXISTS idx_active_missions_hero ON active_missions(hero_id);
                CREATE INDEX IF NOT EXISTS idx_active_missions_mission ON active_missions(mission_id);
            """)

            # 5. Verificar tabla nfts
            cur.execute("""
                CREATE TABLE IF NOT EXISTS nfts (
                    token_id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(255),
                    guild VARCHAR(100),
                    race_class VARCHAR(100),
                    last_known_owner VARCHAR(42),
                    image_url TEXT,
                    dynamic_state JSONB NOT NULL DEFAULT '{}'::jsonb,
                    last_update TIMESTAMP DEFAULT NOW(),
                    last_synced TIMESTAMP DEFAULT NOW(),
                    first_seen TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # 5b. Migración: agregar columnas faltantes a nfts
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name = 'nfts' AND column_name = 'last_synced') THEN
                        ALTER TABLE nfts ADD COLUMN last_synced TIMESTAMP DEFAULT NOW();
                        RAISE NOTICE 'Added last_synced column to nfts';
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name = 'nfts' AND column_name = 'first_seen') THEN
                        ALTER TABLE nfts ADD COLUMN first_seen TIMESTAMP DEFAULT NOW();
                        RAISE NOTICE 'Added first_seen column to nfts';
                    END IF;
                END $$;
            """)

            # 5c. EQUIPMENT COLUMNS - Agregar columnas para el sistema de equipamiento
            print("  🔧 Checking equipment columns...")
            equipment_columns = [
                ('weapon_id', 'VARCHAR(50)'),
                ('armor_id', 'VARCHAR(50)'),
                ('helmet_id', 'VARCHAR(50)'),
                ('accessory_id', 'VARCHAR(50)'),
                ('amulet_id', 'VARCHAR(50)'),
                ('rune_ids', 'TEXT[] DEFAULT ARRAY[]::TEXT[]')
            ]

            for col_name, col_type in equipment_columns:
                cur.execute(f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                       WHERE table_name = 'nfts' AND column_name = '{col_name}') THEN
                            ALTER TABLE nfts ADD COLUMN {col_name} {col_type};
                            RAISE NOTICE 'Added {col_name} column to nfts';
                        END IF;
                    END $$;
                """)

            print("  ✅ Equipment columns verified")

            # 6. Verificar que tenemos las misiones activas
            cur.execute("SELECT COUNT(*) FROM active_missions")
            count = cur.fetchone()[0]
            print(f"  ✅ active_missions table OK ({count} active missions)")

            # 7. 🔥 PLAYER STATS TABLE - Replaces JSON-based stats tracking
            print("  🔧 Checking player_stats table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS player_stats (
                    wallet VARCHAR(42) PRIMARY KEY,
                    total_missions INTEGER DEFAULT 0,
                    total_xp_earned BIGINT DEFAULT 0,
                    total_ember_earned BIGINT DEFAULT 0,
                    total_deaths INTEGER DEFAULT 0,
                    total_items_found INTEGER DEFAULT 0,
                    total_runes_found INTEGER DEFAULT 0,
                    total_sacrifices INTEGER DEFAULT 0,
                    total_energy_spent INTEGER DEFAULT 0,
                    longest_mission_streak INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_player_stats_wallet ON player_stats(wallet)")
            print("  ✅ player_stats table verified")

            # 8. 🔥 ADDITIONAL INDEXES FOR SCALABILITY
            print("  🔧 Creating additional performance indexes...")

            # Index for mission end time (for "missions about to complete" queries)
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                   WHERE table_name = 'active_missions' AND column_name = 'ends_at') THEN
                        ALTER TABLE active_missions ADD COLUMN ends_at TIMESTAMP;
                        RAISE NOTICE 'Added ends_at column to active_missions';
                    END IF;
                END $$;
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_active_missions_ends_at ON active_missions(ends_at)")

            # Indexes for equipment lookups
            cur.execute("CREATE INDEX IF NOT EXISTS idx_nfts_weapon ON nfts(weapon_id) WHERE weapon_id IS NOT NULL")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_nfts_armor ON nfts(armor_id) WHERE armor_id IS NOT NULL")

            # Composite index for common queries
            cur.execute("CREATE INDEX IF NOT EXISTS idx_nfts_owner_state ON nfts(last_known_owner, (dynamic_state->>'state'))")

            print("  ✅ Additional indexes created")

        conn.commit()
        print("✅ PostgreSQL schema verified/updated")
        return True

    except Exception as e:
        print(f"⚠️ PostgreSQL schema check failed: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False
    finally:
        # 🔥 SIEMPRE liberar la conexión en finally
        if conn:
            db.release_connection(conn)

# Ejecutar verificación de schema al iniciar
if POSTGRESQL_AVAILABLE:
    ensure_postgresql_schema()

# ⚠️ Web3 temporarily disabled due to Render deployment issues
# Will use local cache (wallet_nfts.json) for NFT data
WEB3_AVAILABLE = False
Web3 = None

# 🔥 ETH ACCOUNT FOR SIGNING DROPS (doesn't require full Web3 connection)
try:
    from eth_account import Account
    from eth_account.messages import encode_defunct
    from web3 import Web3 as Web3Lib
    SIGNING_AVAILABLE = True
    print("✅ eth_account signing enabled for drops")
except ImportError as e:
    print(f"⚠️ eth_account not available: {e}")
    SIGNING_AVAILABLE = False
    Account = None
    encode_defunct = None
    Web3Lib = None

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

# 🔥 IPFS CIDs de Base Mainnet
# Metadata JSON: bafybeidd7wtx7izjgsociwe6ynjz6c3xslqmcedr7z4wojcxs4yd5u7pim
# Imágenes PNG:  bafybeicnvc3zagcncablcovpxgt5mtuotowvuqom6kby754ve2gwbzdvkm
IPFS_MAINNET_METADATA_CID = "bafybeidd7wtx7izjgsociwe6ynjz6c3xslqmcedr7z4wojcxs4yd5u7pim"
IPFS_MAINNET_IMAGES_CID = "bafybeicnvc3zagcncablcovpxgt5mtuotowvuqom6kby754ve2gwbzdvkm"

# 🔥 IPFS Metadata Cache (in-memory, 10 minute TTL)
# Key: token_id (padded), Value: (metadata_dict, timestamp)
IPFS_METADATA_CACHE = {}
IPFS_CACHE_TTL_SECONDS = 600  # 10 minutes

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

# ---------------------------------
# DROP SYSTEM CONFIG (Items & Runes)
# ---------------------------------
# Base Mainnet contracts
CHAIN_ID = 8453
EMBER_RUNES_CONTRACT = "0xDa2D1085053c3700645a13498293D17c1cc3f595"
EMBER_ITEMS_CONTRACT = "0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA"

# 🔥 IPFS CIDs for Items and Runes metadata
ITEMS_METADATA_CID = "bafybeibs6mm5rghbpld7twbj35dbpryrfimmqkbnkev6ufs4kpbp343wfm"
RUNES_METADATA_CID = "bafybeiajq22kxgm764srr55wsiz4t65so5laxe2nmrryzgailzpmfes3nq"

# 🔥 $EMBER TOKEN CONTRACT CONFIG (Base Mainnet)
EMBER_TOKEN_ADDRESS = os.environ.get("EMBER_TOKEN_ADDRESS", "0xbA7723fBfb44C7712C0B78108ad873DcFd5Dd73b")
ASH_TOKEN_ADDRESS = os.environ.get("ASH_TOKEN_ADDRESS", "0xD4eef3eadb1Cf1B2905AA4Cd1022b8cCCC739DAb")
REWARDS_WALLET_ADDRESS = os.environ.get("REWARDS_WALLET_ADDRESS", "0xa84C45Eb435732FAe8A017861c07394c3aA7d815")
CLAIMER_WALLET_ADDRESS = os.environ.get("CLAIMER_WALLET_ADDRESS")
CLAIMER_PRIVATE_KEY = os.environ.get("CLAIMER_PRIVATE_KEY")

# ABI for $EMBER token claim functions
EMBER_TOKEN_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "claimTransfer",
        "outputs": [{"type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "recipients", "type": "address[]"},
            {"name": "amounts", "type": "uint256[]"}
        ],
        "name": "batchClaimTransfer",
        "outputs": [{"type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "rewardsRemaining",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# 🎮 EQUIPMENT BONUS TABLES (matches frontend inventory.js)
ITEM_BONUSES = {
    'common':    {'ember': 3,  'xp': 2,  'energy': 0, 'death': 0, 'speed': 0},
    'uncommon':  {'ember': 5,  'xp': 4,  'energy': 2, 'death': 0, 'speed': 0},
    'rare':      {'ember': 8,  'xp': 6,  'energy': 3, 'death': 2, 'speed': 0},
    'epic':      {'ember': 12, 'xp': 10, 'energy': 5, 'death': 4, 'speed': 3},
    'legendary': {'ember': 18, 'xp': 15, 'energy': 8, 'death': 6, 'speed': 5}
}

RUNE_BONUSES = {
    'common':    {'ember': 3,  'xp': 3,  'energy': 2,  'death': 2,  'speed': 2},
    'uncommon':  {'ember': 5,  'xp': 5,  'energy': 3,  'death': 3,  'speed': 3},
    'rare':      {'ember': 8,  'xp': 8,  'energy': 5,  'death': 5,  'speed': 5},
    'epic':      {'ember': 12, 'xp': 12, 'energy': 8,  'death': 8,  'speed': 8},
    'legendary': {'ember': 18, 'xp': 18, 'energy': 12, 'death': 12, 'speed': 12}
}

# Cache for IPFS metadata (in-memory, clears on server restart)
_ipfs_metadata_cache = {}

# Backend signer private key (MUST be set in environment)
BACKEND_SIGNER_PRIVATE_KEY = os.environ.get('BACKEND_SIGNER_PRIVATE_KEY', '')

# 🔥 LOG DROP SYSTEM STATUS
if SIGNING_AVAILABLE and BACKEND_SIGNER_PRIVATE_KEY:
    print(f"✅ DROP SYSTEM READY: Signing enabled, private key configured ({len(BACKEND_SIGNER_PRIVATE_KEY)} chars)")
elif SIGNING_AVAILABLE and not BACKEND_SIGNER_PRIVATE_KEY:
    print("⚠️ DROP SYSTEM PARTIAL: Signing available but BACKEND_SIGNER_PRIVATE_KEY not set!")
else:
    print("❌ DROP SYSTEM DISABLED: eth_account not available")

# Drop probabilities by difficulty (percentage)
DROP_RATES = {
    "EASY":   {"item": 5,  "rune": 1},
    "MEDIUM": {"item": 10, "rune": 3},
    "HARD":   {"item": 20, "rune": 8},
    "PARTY":  {"item": 25, "rune": 12}
}

# ---------------------------------
# ITEM GENERATION TEMPLATES
# ---------------------------------
# Item types and their possible names/stats based on rarity
ITEM_TEMPLATES = {
    "weapon": {
        "names": {
            "common": ["Iron Sword", "Wooden Staff", "Rusty Blade", "Simple Bow"],
            "rare": ["Steel Longsword", "Enchanted Staff", "Silver Blade", "Hunter's Bow"],
            "epic": ["Emberforged Blade", "Arcane Scepter", "Shadow Dagger", "Dragonbone Bow"],
            "legendary": ["Ashbringer", "Staff of the Void", "Soulreaver", "Bow of the Phoenix"]
        },
        "base_stats": {"attack": 10, "xp_boost": 5}
    },
    "armor": {
        "names": {
            "common": ["Leather Vest", "Cloth Robes", "Hide Armor", "Padded Tunic"],
            "rare": ["Chainmail", "Reinforced Robes", "Scale Armor", "Knight's Plate"],
            "epic": ["Emberforged Plate", "Arcane Vestments", "Shadow Cloak", "Dragonscale Armor"],
            "legendary": ["Armor of the Last Ember", "Robes of Eternity", "Voidwalker Cloak", "Phoenix Plate"]
        },
        "base_stats": {"defense": 10, "energy_regen": 5}
    },
    "helmet": {
        "names": {
            "common": ["Leather Cap", "Cloth Hood", "Iron Helm", "Simple Circlet"],
            "rare": ["Steel Helm", "Enchanted Hood", "Knight's Helm", "Silver Circlet"],
            "epic": ["Emberforged Helm", "Arcane Crown", "Shadow Mask", "Dragonbone Helm"],
            "legendary": ["Crown of Embers", "Diadem of the Void", "Mask of Shadows", "Phoenix Crest"]
        },
        "base_stats": {"defense": 5, "aura_boost": 5}
    },
    "accessory": {
        "names": {
            "common": ["Simple Ring", "Leather Bracelet", "Copper Pendant", "Bone Charm"],
            "rare": ["Silver Ring", "Enchanted Bracelet", "Gold Pendant", "Spirit Charm"],
            "epic": ["Emberstone Ring", "Arcane Bracelet", "Shadow Pendant", "Dragon Charm"],
            "legendary": ["Ring of the Last Ember", "Bracelet of Eternity", "Void Pendant", "Phoenix Charm"]
        },
        "base_stats": {"luck": 5, "ember_boost": 5}
    },
    "amulet": {
        "names": {
            "common": ["Stone Amulet", "Wooden Talisman", "Bone Necklace", "Simple Locket"],
            "rare": ["Crystal Amulet", "Enchanted Talisman", "Silver Necklace", "Spirit Locket"],
            "epic": ["Emberstone Amulet", "Arcane Talisman", "Shadow Necklace", "Dragon Locket"],
            "legendary": ["Amulet of the Last Ember", "Talisman of the Void", "Necklace of Shadows", "Phoenix Locket"]
        },
        "base_stats": {"aura_boost": 10, "xp_boost": 5}
    }
}

RUNE_TEMPLATES = {
    "names": {
        "common": ["Rune of Minor Power", "Rune of Small Fortune", "Rune of Light"],
        "rare": ["Rune of Strength", "Rune of Fortune", "Rune of Protection"],
        "epic": ["Rune of the Ember", "Rune of the Dragon", "Rune of the Void"],
        "legendary": ["Rune of the Last Ember", "Rune of Eternity", "Rune of the Phoenix"]
    },
    "base_stats": {"all_boost": 5}
}

# Rarity probabilities by difficulty
RARITY_RATES = {
    "EASY":   {"common": 70, "rare": 25, "epic": 4, "legendary": 1},
    "MEDIUM": {"common": 50, "rare": 35, "epic": 12, "legendary": 3},
    "HARD":   {"common": 30, "rare": 40, "epic": 23, "legendary": 7},
    "PARTY":  {"common": 20, "rare": 40, "epic": 30, "legendary": 10}
}

def generate_random_item(claim_type: str, difficulty: str, wallet: str) -> dict:
    """
    Generate a random item based on claim type and difficulty.

    Args:
        claim_type: "ITEM" or "RUNE"
        difficulty: "EASY", "MEDIUM", "HARD", or "PARTY"
        wallet: Player's wallet address

    Returns:
        dict with item data ready to insert into database
    """
    import random

    # Determine rarity based on difficulty
    rates = RARITY_RATES.get(difficulty.upper(), RARITY_RATES["EASY"])
    roll = random.randint(1, 100)

    cumulative = 0
    rarity = "common"
    for r, chance in [("common", rates["common"]), ("rare", rates["rare"]),
                      ("epic", rates["epic"]), ("legendary", rates["legendary"])]:
        cumulative += chance
        if roll <= cumulative:
            rarity = r
            break

    # Rarity multipliers for stats
    rarity_multipliers = {"common": 1, "rare": 2, "epic": 4, "legendary": 8}
    multiplier = rarity_multipliers.get(rarity, 1)

    if claim_type.upper() == "RUNE":
        # Generate rune
        names = RUNE_TEMPLATES["names"].get(rarity, RUNE_TEMPLATES["names"]["common"])
        name = random.choice(names)
        base_stats = RUNE_TEMPLATES["base_stats"]
        stats = {k: v * multiplier for k, v in base_stats.items()}
        item_type = "rune"
    else:
        # Generate item - random type
        item_types = list(ITEM_TEMPLATES.keys())
        item_type = random.choice(item_types)
        template = ITEM_TEMPLATES[item_type]
        names = template["names"].get(rarity, template["names"]["common"])
        name = random.choice(names)
        base_stats = template["base_stats"]
        stats = {k: v * multiplier for k, v in base_stats.items()}

    return {
        "name": name,
        "type": item_type,
        "rarity": rarity,
        "stats": stats,
        "owner_wallet": wallet.lower(),
        "image_url": f"/img/items/{item_type}_{rarity}.png"
    }

def insert_item_to_vault(item_data: dict) -> int:
    """
    Insert a generated item into the items table.

    Args:
        item_data: dict with name, type, rarity, stats, owner_wallet, image_url

    Returns:
        The inserted item's ID, or None if failed
    """
    if not POSTGRESQL_AVAILABLE:
        print("⚠️ PostgreSQL not available - cannot insert item")
        return None

    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO items (name, type, rarity, stats, owner_wallet, image_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                item_data["name"],
                item_data["type"],
                item_data["rarity"],
                json.dumps(item_data["stats"]),
                item_data["owner_wallet"],
                item_data.get("image_url", "")
            ))
            item_id = cur.fetchone()[0]
            conn.commit()
        db.release_connection(conn)
        print(f"✅ Inserted item '{item_data['name']}' (ID: {item_id}) to vault for {item_data['owner_wallet'][:8]}...")
        return item_id
    except Exception as e:
        print(f"❌ Error inserting item to vault: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_claim_details(claim_id: str) -> dict:
    """
    Get details of a pending claim by claim_id.

    Returns:
        dict with claim details or None if not found
    """
    if not POSTGRESQL_AVAILABLE:
        return None

    try:
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, wallet_address, claim_type, claim_id, difficulty, status
                FROM pending_claims
                WHERE claim_id = %s
            """, (claim_id,))
            claim = cur.fetchone()
        db.release_connection(conn)
        return dict(claim) if claim else None
    except Exception as e:
        print(f"❌ Error getting claim details: {e}")
        return None

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

# 🎮 EQUIPMENT BONUS SYSTEM
# Fetches item/rune metadata from IPFS and calculates mission bonuses

import requests

def fetch_ipfs_metadata(token_id: str, is_rune: bool = False) -> dict:
    """
    Fetch item/rune metadata from IPFS with caching.
    Returns metadata dict with 'rarity' field, or None if fetch fails.

    Handles ID formats:
    - "rune-1059" → extracts "1059" → pads to "01059"
    - "item-5120" → extracts "5120" → pads to "05120"
    - "1059" → pads to "01059"
    """
    # Extract numeric ID from formats like "rune-1059" or "item-5120"
    original_id = str(token_id)
    if '-' in original_id:
        numeric_id = original_id.split('-')[-1]  # "rune-1059" → "1059"
    else:
        numeric_id = original_id

    cache_key = f"{'rune' if is_rune else 'item'}_{numeric_id}"

    # Check cache first
    if cache_key in _ipfs_metadata_cache:
        return _ipfs_metadata_cache[cache_key]

    try:
        # Format token ID with leading zeros (5 digits)
        padded_id = numeric_id.zfill(5)
        cid = RUNES_METADATA_CID if is_rune else ITEMS_METADATA_CID
        url = f"{IPFS_GATEWAY}{cid}/{padded_id}.json"

        print(f"🔍 Fetching IPFS metadata: {original_id} → {padded_id}.json")

        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ IPFS fetch failed for {cache_key}: HTTP {response.status_code} (URL: {url})")
            return None

        metadata = response.json()

        # Extract rarity from attributes
        rarity = 'common'  # Default
        if 'attributes' in metadata and isinstance(metadata['attributes'], list):
            for attr in metadata['attributes']:
                if attr.get('trait_type', '').lower() == 'rarity':
                    rarity = str(attr.get('value', 'common')).lower()
                    break

        metadata['rarity'] = rarity

        # Cache the result
        _ipfs_metadata_cache[cache_key] = metadata
        print(f"📦 Cached IPFS metadata: {cache_key} → rarity={rarity}")

        return metadata

    except Exception as e:
        print(f"⚠️ IPFS fetch error for {cache_key}: {e}")
        return None


def get_emissary_bonuses(emissary_id: str) -> dict:
    """
    Calculate total equipment bonuses for an emissary.
    Queries database for equipped items/runes, fetches metadata from IPFS,
    and sums bonuses according to rarity tables.

    Uses 5-minute cache to reduce database/IPFS calls.

    Returns: {
        'ember': int,      # +% EMBER earned
        'xp': int,         # +% XP earned
        'energy': int,     # -% energy cost
        'death': int,      # -% death probability
        'speed': int,      # -% mission duration
        'item_count': int, # Number of equipped items
        'rune_count': int  # Number of equipped runes
    }
    """
    # Check cache first
    cached = db.get_cached_equipment_bonuses(emissary_id)
    if cached is not None:
        logger.debug(f"Equipment bonuses cache hit for {emissary_id}")
        return cached

    total_bonuses = {
        'ember': 0,
        'xp': 0,
        'energy': 0,
        'death': 0,
        'speed': 0,
        'item_count': 0,
        'rune_count': 0
    }

    if not POSTGRESQL_AVAILABLE:
        print(f"⚠️ get_emissary_bonuses: Database not available")
        return total_bonuses

    try:
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get equipped items and runes
        cursor.execute("""
            SELECT weapon_id, armor_id, helmet_id, accessory_id, amulet_id, rune_ids
            FROM nfts WHERE token_id = %s
        """, (emissary_id,))

        row = cursor.fetchone()
        db.release_connection(conn)

        if not row:
            print(f"⚠️ get_emissary_bonuses: Emissary {emissary_id} not found")
            return total_bonuses

        # Process equipped items (5 slots)
        item_slots = ['weapon_id', 'armor_id', 'helmet_id', 'accessory_id', 'amulet_id']
        for slot in item_slots:
            item_id = row.get(slot)
            if item_id:
                # Fetch metadata from IPFS
                metadata = fetch_ipfs_metadata(item_id, is_rune=False)
                if metadata:
                    rarity = metadata.get('rarity', 'common')
                    bonuses = ITEM_BONUSES.get(rarity, ITEM_BONUSES['common'])

                    total_bonuses['ember'] += bonuses['ember']
                    total_bonuses['xp'] += bonuses['xp']
                    total_bonuses['energy'] += bonuses['energy']
                    total_bonuses['death'] += bonuses['death']
                    total_bonuses['speed'] += bonuses['speed']
                    total_bonuses['item_count'] += 1

                    print(f"  ⚔️ Item {slot}={item_id} ({rarity}): +{bonuses['ember']}% ember, +{bonuses['xp']}% xp")

        # Process equipped runes (up to 2)
        rune_ids = row.get('rune_ids') or []
        for rune_id in rune_ids:
            if rune_id:
                # Fetch metadata from IPFS
                metadata = fetch_ipfs_metadata(rune_id, is_rune=True)
                if metadata:
                    rarity = metadata.get('rarity', 'common')
                    bonuses = RUNE_BONUSES.get(rarity, RUNE_BONUSES['common'])

                    total_bonuses['ember'] += bonuses['ember']
                    total_bonuses['xp'] += bonuses['xp']
                    total_bonuses['energy'] += bonuses['energy']
                    total_bonuses['death'] += bonuses['death']
                    total_bonuses['speed'] += bonuses['speed']
                    total_bonuses['rune_count'] += 1

                    print(f"  🔮 Rune {rune_id} ({rarity}): +{bonuses['ember']}% ember, +{bonuses['xp']}% xp")

        print(f"📊 TOTAL BONUSES for emissary {emissary_id}: " +
              f"ember +{total_bonuses['ember']}%, xp +{total_bonuses['xp']}%, " +
              f"energy -{total_bonuses['energy']}%, death -{total_bonuses['death']}%, " +
              f"speed -{total_bonuses['speed']}% " +
              f"({total_bonuses['item_count']} items, {total_bonuses['rune_count']} runes)")

        # Cache the result for future calls
        db.set_cached_equipment_bonuses(emissary_id, total_bonuses)

        return total_bonuses

    except Exception as e:
        print(f"⚠️ get_emissary_bonuses error: {e}")
        import traceback
        traceback.print_exc()
        return total_bonuses


def get_equipment_stats(hero_token_id: str) -> dict:
    """
    Get total stats from all equipped items for a hero.
    Returns dict with: attack, defense, xp_boost, aura_boost, luck, energy_regen, ember_boost, all_boost

    NOTE: Items are now on blockchain. This function returns default stats.
    Equipment bonuses are calculated on frontend from IPFS metadata.
    """
    total_stats = {
        "attack": 0,
        "defense": 0,
        "xp_boost": 0,
        "aura_boost": 0,
        "luck": 0,
        "energy_regen": 0,
        "ember_boost": 0,
        "all_boost": 0
    }

    # Items are on blockchain, not in database
    # Frontend calculates bonuses from IPFS metadata
    return total_stats

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

    # ⚔️ EQUIPMENT BONUS: Apply attack stat from equipped items
    hero_token_id = hero.get("token_id")
    if hero_token_id:
        equipment_stats = get_equipment_stats(hero_token_id)
        attack_bonus = equipment_stats.get("attack", 0)
        all_boost = equipment_stats.get("all_boost", 0)  # From runes
        total_equipment_bonus = attack_bonus + all_boost
        if total_equipment_bonus > 0:
            bonus += total_equipment_bonus
            print(f"⚔️ EQUIPMENT bonus applied: +{total_equipment_bonus}% (attack: {attack_bonus}, all: {all_boost})")

    # 🔮 EMBER ROLL BUFF: Success bonus
    ds = hero.get("dynamic_state", {})
    buff = ds.get("ember_roll_buff")
    if buff:
        expires_at = buff.get("expires_at")
        if expires_at:
            try:
                expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                if now < expires_dt:
                    # Buff is active
                    success_bonus = buff.get("success_bonus", 0)
                    if success_bonus != 0:
                        bonus += success_bonus
                        print(f"🔮 EMBER ROLL success buff applied: {'+' if success_bonus > 0 else ''}{success_bonus}%")
            except Exception as e:
                print(f"⚠️ Error parsing buff expiration: {e}")

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

def roll_mission_outcome(hero, mission, equipment_death_protection=0):
    """
    Roll for mission outcome.
    Args:
        equipment_death_protection: Additional death protection % from equipment (default 0)
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

        # 🔮 EMBER ROLL BUFF: XP bonus
        ds = hero.get("dynamic_state", {})
        buff = ds.get("ember_roll_buff")
        if buff:
            expires_at = buff.get("expires_at")
            if expires_at:
                try:
                    expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    if now < expires_dt:
                        # Buff is active
                        xp_bonus = buff.get("xp_bonus", 0)
                        if xp_bonus != 0:
                            original_xp = xp_reward
                            xp_reward = int(xp_reward * (100 + xp_bonus) / 100)
                            print(f"🔮 EMBER ROLL XP buff applied: {original_xp} → {xp_reward} ({'+' if xp_bonus > 0 else ''}{xp_bonus}%)")
                except Exception as e:
                    print(f"⚠️ Error parsing buff expiration: {e}")

        # ⚔️ EQUIPMENT BOOSTS: Apply XP and Aura boosts from items
        hero_token_id = hero.get("token_id")
        if hero_token_id:
            equipment_stats = get_equipment_stats(hero_token_id)
            xp_boost = equipment_stats.get("xp_boost", 0) + equipment_stats.get("all_boost", 0)
            aura_boost = equipment_stats.get("aura_boost", 0) + equipment_stats.get("all_boost", 0)

            if xp_boost > 0:
                original_xp = xp_reward
                xp_reward = int(xp_reward * (100 + xp_boost) / 100)
                print(f"⚔️ EQUIPMENT XP boost: {original_xp} → {xp_reward} (+{xp_boost}%)")

            if aura_boost > 0:
                original_aura = aura_reward
                aura_reward = int(aura_reward * (100 + aura_boost) / 100)
                print(f"⚔️ EQUIPMENT Aura boost: {original_aura} → {aura_reward} (+{aura_boost}%)")

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
            base_protection = calculate_death_protection(hero_level, hero_aura)

            # ⚔️ Add equipment death protection (capped at 80% total)
            protection = min(80, base_protection + equipment_death_protection)
            if equipment_death_protection > 0:
                print(f"⚔️ Equipment death protection: {base_protection}% + {equipment_death_protection}% = {protection}%")

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
        try:
            db.save_json_or_db(path, obj)
            return
        except Exception as e:
            print(f"⚠️ PostgreSQL save failed for {path}, falling back to JSON: {e}")

    # Fallback to JSON file
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ CRITICAL: Failed to save JSON to {path}: {e}")
        import traceback
        traceback.print_exc()
        raise

# ---------------------------------
# NFTs Database - Fuente de Verdad Centralizada
# ---------------------------------

def load_nfts_database():
    """
    Carga la base de datos centralizada de NFTs.
    Esta es la FUENTE DE VERDAD para todos los atributos dinámicos.

    🔥 POSTGRESQL FIRST: Intenta leer de PostgreSQL, si falla usa JSON como fallback.
    """
    # 🔥 POSTGRESQL: Try to load from database first
    if POSTGRESQL_AVAILABLE:
        conn = None
        try:
            conn = db.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT token_id, name, race_class, guild, image_url, dynamic_state,
                           last_known_owner, last_synced, first_seen
                    FROM nfts
                """)
                rows = cur.fetchall()

            if rows:
                nfts_db = {}
                for row in rows:
                    token_id = row['token_id']
                    # Parse dynamic_state from JSONB
                    ds = row['dynamic_state'] if row['dynamic_state'] else {}
                    if isinstance(ds, str):
                        import json as json_lib
                        ds = json_lib.loads(ds)

                    # Always use mainnet CID for image_url (ignore DB value which may be testnet)
                    padded_id = str(token_id).zfill(5)
                    mainnet_image_url = f"{IPFS_GATEWAY}{IPFS_MAINNET_IMAGES_CID}/{padded_id}.png"

                    nfts_db[token_id] = {
                        'token_id': token_id,
                        'name': row['name'] or f"Emissary #{token_id}",
                        'race_class': row['race_class'] or 'Unknown',
                        'guild': row['guild'] or 'Unassigned',
                        'image_url': mainnet_image_url,
                        'dynamic_state': ds,
                        'last_known_owner': row['last_known_owner'],
                        'last_synced': str(row['last_synced']) if row['last_synced'] else None,
                        'first_seen': str(row['first_seen']) if row['first_seen'] else None
                    }
                print(f"✅ Loaded {len(nfts_db)} NFTs from PostgreSQL")
                return nfts_db
        except Exception as e:
            print(f"⚠️ PostgreSQL load_nfts_database failed: {e}, falling back to JSON")
        finally:
            if conn:
                db.release_connection(conn)

    # Fallback to JSON file
    db_json = load_json(NFTS_DATABASE_PATH, {})
    # Filtrar comentarios de metadata
    return {k: v for k, v in db_json.items() if not k.startswith("_")}

def save_nfts_database(db_data):
    """
    Guarda la base de datos de NFTs.

    🔥 POSTGRESQL FIRST: Guarda en PostgreSQL Y en JSON (para backup).
    """
    # 🔥 POSTGRESQL: Save to database
    if POSTGRESQL_AVAILABLE:
        conn = None
        try:
            conn = db.get_connection()
            with conn.cursor() as cur:
                for token_id, nft in db_data.items():
                    if token_id.startswith("_"):
                        continue  # Skip comments

                    ds = nft.get('dynamic_state', {})
                    # Convert to JSON string for JSONB column
                    import json as json_lib
                    ds_json = json_lib.dumps(ds) if isinstance(ds, dict) else ds

                    cur.execute("""
                        INSERT INTO nfts (token_id, name, race_class, guild, image_url, dynamic_state, last_known_owner, last_synced)
                        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, NOW())
                        ON CONFLICT (token_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            race_class = EXCLUDED.race_class,
                            guild = EXCLUDED.guild,
                            image_url = EXCLUDED.image_url,
                            dynamic_state = EXCLUDED.dynamic_state,
                            last_known_owner = COALESCE(EXCLUDED.last_known_owner, nfts.last_known_owner),
                            last_synced = NOW()
                    """, (
                        token_id,
                        nft.get('name', f"Emissary #{token_id}"),
                        nft.get('race_class', 'Unknown'),
                        nft.get('guild', 'Unassigned'),
                        nft.get('image_url'),
                        ds_json,
                        nft.get('last_known_owner')
                    ))
                conn.commit()
            print(f"✅ Saved {len([k for k in db_data.keys() if not k.startswith('_')])} NFTs to PostgreSQL")
        except Exception as e:
            print(f"⚠️ PostgreSQL save_nfts_database failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                db.release_connection(conn)

    # Also save to JSON (backup/fallback)
    full_db = load_json(NFTS_DATABASE_PATH, {})
    comments = {k: v for k, v in full_db.items() if k.startswith("_")}
    full_db = {**comments, **db_data}
    save_json(NFTS_DATABASE_PATH, full_db)

# ---------------------------------
# Active Missions - PostgreSQL Persistence
# ---------------------------------

def load_active_missions():
    """
    Carga misiones activas desde PostgreSQL (fuente de verdad) con fallback a JSON.
    """
    if POSTGRESQL_AVAILABLE:
        conn = None
        try:
            conn = db.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT mission_key, wallet, hero_id, hero_ids, mission_id,
                           start_time, duration_hours, is_party
                    FROM active_missions
                """)
                rows = cur.fetchall()

            missions = {}
            for row in rows:
                mission_key = row['mission_key']
                # Parse hero_ids if it's a party mission
                hero_ids = row['hero_ids']
                if hero_ids and isinstance(hero_ids, str):
                    import json as json_lib
                    hero_ids = json_lib.loads(hero_ids)

                missions[mission_key] = {
                    'wallet': row['wallet'],
                    'hero_id': row['hero_id'],
                    'mission_id': row['mission_id'],
                    'start_time': row['start_time'].isoformat() if row['start_time'] else None,
                    'duration_hours': row['duration_hours'],
                    'is_party': row['is_party'] or False
                }
                if hero_ids:
                    missions[mission_key]['hero_ids'] = hero_ids

            if missions:
                print(f"✅ Loaded {len(missions)} active missions from PostgreSQL")
            return missions
        except Exception as e:
            print(f"⚠️ PostgreSQL load_active_missions failed: {e}, falling back to JSON")
        finally:
            if conn:
                db.release_connection(conn)

    # Fallback to JSON
    return load_json(ACTIVE_MISSIONS_PATH, {})

def save_active_missions(missions):
    """
    Guarda misiones activas en PostgreSQL Y JSON (backup).
    """
    if POSTGRESQL_AVAILABLE:
        conn = None
        try:
            conn = db.get_connection()
            with conn.cursor() as cur:
                # First, get existing mission keys to know what to delete
                cur.execute("SELECT mission_key FROM active_missions")
                existing_keys = set(row[0] for row in cur.fetchall())

                # Delete missions that are no longer active
                current_keys = set(missions.keys())
                keys_to_delete = existing_keys - current_keys
                if keys_to_delete:
                    for key in keys_to_delete:
                        cur.execute("DELETE FROM active_missions WHERE mission_key = %s", (key,))
                    print(f"  🗑️ Deleted {len(keys_to_delete)} completed missions from PostgreSQL")

                # Upsert current missions
                for mission_key, mission in missions.items():
                    hero_ids = mission.get('hero_ids')
                    hero_ids_json = None
                    if hero_ids:
                        import json as json_lib
                        hero_ids_json = json_lib.dumps(hero_ids)

                    # Parse start_time
                    start_time = mission.get('start_time')
                    if isinstance(start_time, str):
                        start_time = start_time.replace('Z', '+00:00')

                    cur.execute("""
                        INSERT INTO active_missions (mission_key, wallet, hero_id, hero_ids, mission_id, start_time, duration_hours, is_party)
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
                        mission.get('wallet'),
                        mission.get('hero_id'),
                        hero_ids_json,
                        mission.get('mission_id'),
                        start_time,
                        mission.get('duration_hours'),
                        mission.get('is_party', False)
                    ))
                conn.commit()
            print(f"✅ Saved {len(missions)} active missions to PostgreSQL")
        except Exception as e:
            print(f"⚠️ PostgreSQL save_active_missions failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                db.release_connection(conn)

    # Also save to JSON (backup)
    save_json(ACTIVE_MISSIONS_PATH, missions)

def delete_active_mission(mission_key):
    """
    Elimina una misión activa de PostgreSQL y JSON.
    """
    if POSTGRESQL_AVAILABLE:
        conn = None
        try:
            conn = db.get_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM active_missions WHERE mission_key = %s", (mission_key,))
                conn.commit()
            print(f"✅ Deleted mission {mission_key} from PostgreSQL")
        except Exception as e:
            print(f"⚠️ PostgreSQL delete_active_mission failed: {e}")
        finally:
            if conn:
                db.release_connection(conn)

    # Also delete from JSON
    missions = load_json(ACTIVE_MISSIONS_PATH, {})
    if mission_key in missions:
        del missions[mission_key]
        save_json(ACTIVE_MISSIONS_PATH, missions)

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
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def ensure_utc(dt_or_str):
    """
    Convierte cualquier datetime o string a UTC timezone-aware.
    Nunca devuelve naive datetime.
    """
    if dt_or_str is None:
        return None

    # Si es string, parsearlo primero
    if isinstance(dt_or_str, str):
        try:
            # Intentar con formato ISO
            clean = dt_or_str.replace("Z", "+00:00")
            dt_or_str = datetime.fromisoformat(clean)
        except Exception:
            return None

    # Si es datetime naive, asumir UTC
    if dt_or_str.tzinfo is None:
        dt_or_str = dt_or_str.replace(tzinfo=timezone.utc)

    return dt_or_str

def hours_since(ts_str):
    """Devuelve cuántas horas pasaron desde ts_str (ISO) hasta ahora."""
    if not ts_str:
        return 999999
    try:
        # Usar ensure_utc para garantizar timezone-aware
        t = ensure_utc(ts_str)
        if t is None:
            return 999999

        now = datetime.now(timezone.utc)

        # Debug logging para encontrar problemas
        # print(f"[DEBUG hours_since] ts_str={ts_str}, t={t}, t.tzinfo={t.tzinfo}, now.tzinfo={now.tzinfo}")

        delta = now - t
        return delta.total_seconds() / 3600.0
    except Exception as e:
        print(f"⚠️ hours_since error: {e} for ts_str={ts_str}")
        import traceback
        traceback.print_exc()
        return 999999

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
    # Primero intentar desde PostgreSQL/active_missions
    active_missions = load_active_missions()
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
    try:
        db = load_nfts_database()
        guilds_data = load_json(GUILDS_PATH, [])
    except Exception as e:
        print(f"❌ Error loading data for guild calculation: {e}")
        import traceback
        traceback.print_exc()
        return []

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
    try:
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
    except Exception as e:
        print(f"❌ Error updating guild data: {e}")
        import traceback
        traceback.print_exc()
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
# DROP SYSTEM: Signature Generation
# ---------------------------------

def generate_claim_signature(player_wallet: str, claim_type: str, mission_id: str) -> dict:
    """
    Generate a signed claim for item or rune drop.

    Args:
        player_wallet: Player's wallet address
        claim_type: "RUNE" or "ITEM"
        mission_id: ID of the completed mission

    Returns:
        dict with claim_id and signature, or None if signing unavailable
    """
    if not SIGNING_AVAILABLE or not BACKEND_SIGNER_PRIVATE_KEY:
        print("⚠️ Signing not available - missing eth_account or private key")
        return None

    try:
        # Generate unique claim ID
        timestamp = int(time.time() * 1000)
        claim_data = f"{claim_type}-{mission_id}-{player_wallet}-{timestamp}"
        claim_id = Web3Lib.keccak(text=claim_data)

        # Create message hash matching contract's expected format
        # keccak256(abi.encodePacked(player, claimId, claimType, chainId))
        message_hash = Web3Lib.solidity_keccak(
            ['address', 'bytes32', 'string', 'uint256'],
            [Web3Lib.to_checksum_address(player_wallet), claim_id, claim_type, CHAIN_ID]
        )

        # Sign the message
        message = encode_defunct(message_hash)
        signed = Account.sign_message(message, private_key=BACKEND_SIGNER_PRIVATE_KEY)

        print(f"✅ Generated {claim_type} claim for {player_wallet[:8]}... claim_id={claim_id.hex()[:16]}...")

        return {
            "claim_id": claim_id.hex(),
            "signature": signed.signature.hex()
        }
    except Exception as e:
        print(f"❌ Error generating claim signature: {e}")
        import traceback
        traceback.print_exc()
        return None

def calculate_drops(difficulty: str, is_party: bool = False) -> dict:
    """
    Calculate if player wins item or rune drop based on mission difficulty.

    Args:
        difficulty: Mission difficulty ("EASY", "MEDIUM", "HARD")
        is_party: True if this was a party mission

    Returns:
        dict with "item" and "rune" booleans
    """
    # Use PARTY rates if party mission, otherwise use difficulty rates
    if is_party:
        rates = DROP_RATES.get("PARTY", {"item": 25, "rune": 12})
    else:
        rates = DROP_RATES.get(difficulty.upper(), {"item": 5, "rune": 1})

    item_roll = random.randint(1, 100)
    rune_roll = random.randint(1, 100)

    won_item = item_roll <= rates["item"]
    won_rune = rune_roll <= rates["rune"]

    # Enhanced logging for debugging
    print(f"\n{'='*50}")
    print(f"🎲 DROP CALCULATION")
    print(f"   Difficulty: {difficulty}, Party: {is_party}")
    print(f"   Drop rates: item={rates['item']}%, rune={rates['rune']}%")
    print(f"   Item roll: {item_roll}/100 (need <= {rates['item']}) → {'🎁 WON ITEM!' if won_item else '💨 No item'}")
    print(f"   Rune roll: {rune_roll}/100 (need <= {rates['rune']}) → {'🎁 WON RUNE!' if won_rune else '💨 No rune'}")
    if won_item or won_rune:
        print(f"   🎉 PLAYER WON DROP(S)!")
    print(f"{'='*50}\n")

    return {
        "item": won_item,
        "rune": won_rune,
        "rates": rates
    }

def save_pending_claim(wallet: str, claim_type: str, claim_id: str, signature: str,
                       mission_id: str = None, hero_id: str = None, difficulty: str = None) -> bool:
    """
    Save a pending claim to the database.

    Returns:
        True if saved successfully, False otherwise
    """
    if not POSTGRESQL_AVAILABLE:
        print("⚠️ PostgreSQL not available - cannot save pending claim")
        return False

    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO pending_claims
                (wallet_address, claim_type, claim_id, signature, mission_id, hero_id, difficulty, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
                ON CONFLICT (claim_id) DO NOTHING
            """, (wallet.lower(), claim_type, claim_id, signature, mission_id, hero_id, difficulty))
            conn.commit()
        db.release_connection(conn)
        print(f"✅ Saved pending {claim_type} claim for {wallet[:8]}...")
        return True
    except Exception as e:
        print(f"❌ Error saving pending claim: {e}")
        return False

def get_pending_claims(wallet: str) -> list:
    """
    Get all pending claims for a wallet.

    Returns:
        List of pending claim objects
    """
    if not POSTGRESQL_AVAILABLE:
        return []

    try:
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, claim_type, claim_id, signature, mission_id, hero_id, difficulty,
                       created_at, status
                FROM pending_claims
                WHERE wallet_address = %s AND status = 'pending'
                ORDER BY created_at DESC
            """, (wallet.lower(),))
            claims = cur.fetchall()
        db.release_connection(conn)
        return [dict(c) for c in claims] if claims else []
    except Exception as e:
        print(f"❌ Error getting pending claims: {e}")
        return []

def mark_claim_as_claimed(claim_id: str, token_id: int = None, tx_hash: str = None) -> bool:
    """
    Mark a claim as claimed after blockchain confirmation.

    Returns:
        True if updated successfully
    """
    if not POSTGRESQL_AVAILABLE:
        return False

    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE pending_claims
                SET status = 'claimed', claimed_at = NOW(), token_id = %s, tx_hash = %s
                WHERE claim_id = %s
            """, (token_id, tx_hash, claim_id))
            conn.commit()
        db.release_connection(conn)
        return True
    except Exception as e:
        print(f"❌ Error marking claim as claimed: {e}")
        return False

# ---------------------------------
# Rutas estáticas base
# ---------------------------------

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/robots.txt")
def serve_robots():
    return send_from_directory(app.static_folder, "robots.txt")

@app.route("/sitemap.xml")
def serve_sitemap():
    return send_from_directory(app.static_folder, "sitemap.xml")

@app.route("/google66a4619b1c3d4430.html")
def google_verification():
    return send_from_directory(app.static_folder, "google66a4619b1c3d4430.html")

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
    """Stats globales y leaderboard desde las nuevas tablas PostgreSQL"""
    try:
        conn = db.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        stats = {}

        # Total emissaries minted
        cur.execute("SELECT COUNT(*) as count FROM emissaries_state WHERE minted = TRUE")
        result = cur.fetchone()
        stats['total_minted'] = result['count'] if result else 0

        # Total XP distribuido
        cur.execute("SELECT COALESCE(SUM(xp), 0) as total FROM emissaries_state")
        result = cur.fetchone()
        stats['total_xp'] = int(result['total']) if result else 0

        # Total misiones completadas
        cur.execute("SELECT COUNT(*) as count FROM missions_history")
        result = cur.fetchone()
        stats['total_missions'] = result['count'] if result else 0

        # Guild rankings
        cur.execute("""
            SELECT guild_id, guild_name, total_members, total_xp, total_missions
            FROM stats_guilds
            ORDER BY total_xp DESC
        """)
        stats['guild_rankings'] = cur.fetchall() or []

        # Top 10 emissaries por XP
        cur.execute("""
            SELECT m.token_id, m.name, m.race, m.class, m.guild,
                   COALESCE(s.xp, 0) as xp
            FROM emissaries_metadata m
            LEFT JOIN emissaries_state s ON m.token_id = s.token_id
            WHERE s.minted = TRUE
            ORDER BY s.xp DESC NULLS LAST
            LIMIT 10
        """)
        stats['leaderboard'] = cur.fetchall() or []

        # Campos adicionales para compatibilidad
        stats['active_guilds'] = 6
        stats['last_updated'] = now_utc_str()

        cur.close()
        db.release_connection(conn)

        return jsonify(stats)

    except Exception as e:
        print(f"Error in /api/stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# API: GUILDS
# ---------------------------------

@app.route("/api/guilds")
def api_guilds():
    """Obtener datos de guilds desde stats_guilds"""
    try:
        conn = db.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT guild_id, guild_name, total_members, total_xp,
                   total_missions, total_deaths,
                   CASE WHEN total_missions > 0
                        THEN ROUND((successful_missions::numeric / total_missions) * 100, 1)
                        ELSE 0
                   END as success_rate
            FROM stats_guilds
            ORDER BY total_xp DESC
        """)

        guilds = cur.fetchall() or []

        cur.close()
        db.release_connection(conn)

        return jsonify({
            "guilds": guilds,
            "last_updated": now_utc_str()
        })

    except Exception as e:
        print(f"Error in /api/guilds: {e}")
        # Fallback a la función anterior si hay error
        guilds_data = calculate_guilds_data()
        return jsonify({
            "guilds": guilds_data,
            "last_updated": now_utc_str()
        })

# ---------------------------------
# API: MINT REGISTER
# ---------------------------------

@app.route('/api/mint/register', methods=['POST'])
def register_mint():
    """Registrar un nuevo mint en la base de datos"""
    conn = None
    try:
        data = request.json
        token_id = data.get('token_id')
        wallet_address = data.get('wallet_address')

        if not token_id or not wallet_address:
            return jsonify({"error": "Missing token_id or wallet_address"}), 400

        conn = db.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Actualizar emissaries_state con el nuevo owner
        cur.execute("""
            UPDATE emissaries_state
            SET wallet_address = %s, minted = TRUE, minted_at = NOW()
            WHERE token_id = %s
        """, (wallet_address, token_id))

        # Obtener el guild del emissary para actualizar stats
        cur.execute("""
            SELECT guild FROM emissaries_metadata WHERE token_id = %s
        """, (token_id,))
        result = cur.fetchone()

        if result and result['guild']:
            guild_name = result['guild']
            # Actualizar contador de miembros del guild
            cur.execute("""
                UPDATE stats_guilds
                SET total_members = total_members + 1,
                    updated_at = NOW()
                WHERE guild_name = %s
            """, (guild_name,))

        # Actualizar stats globales si existe la columna
        cur.execute("""
            UPDATE global_stats
            SET total_minted = total_minted + 1
            WHERE id = 1
        """)

        conn.commit()
        cur.close()
        db.release_connection(conn)

        return jsonify({
            "success": True,
            "token_id": token_id,
            "wallet_address": wallet_address,
            "message": f"Emissary #{token_id} registered successfully"
        })

    except Exception as e:
        print(f"Error in /api/mint/register: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            db.release_connection(conn)
        return jsonify({"error": str(e)}), 500

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
    current_time = datetime.now(timezone.utc)

    for event in EVENTS:
        available_from_str = event.get("available_from")
        available_until_str = event.get("available_until")
        event_active = event.get("event_active", True)

        # Check if event is active
        if not event_active:
            continue

        # Parse dates - ensure timezone-aware
        try:
            available_from = datetime.fromisoformat(available_from_str.replace("Z", "+00:00"))
            available_until = datetime.fromisoformat(available_until_str.replace("Z", "+00:00"))

            # Ensure timezone-aware (in case the string didn't have timezone)
            if available_from.tzinfo is None:
                available_from = available_from.replace(tzinfo=timezone.utc)
            if available_until.tzinfo is None:
                available_until = available_until.replace(tzinfo=timezone.utc)

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
        timestamp = ensure_utc(timestamp_str)
        if timestamp is None:
            return "recently"
        now = datetime.now(timezone.utc)
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
        now = datetime.now(timezone.utc)

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
    2. Si no hay cache, busca en PostgreSQL (nfts_database por last_known_owner)
    3. Si no hay DB, intenta blockchain (solo si hay conexión)

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

    # 🔥 PRIORIDAD 2: Buscar en PostgreSQL (nfts_database por last_known_owner)
    # Esto sobrevive reinicios del servidor porque está en PostgreSQL
    try:
        nfts_db = load_nfts_database()
        db_tokens = []
        for token_id, nft in nfts_db.items():
            owner = nft.get("last_known_owner", "")
            if owner and owner.lower() == wallet_lower:
                db_tokens.append(token_id)

        if db_tokens:
            print(f"✅ Found {len(db_tokens)} NFTs in PostgreSQL for wallet {wallet[:6]}...{wallet[-4:]}")
            # Cachear para próximas llamadas en esta sesión
            wallet_nfts[wallet] = db_tokens
            save_json(WALLET_NFTS_PATH, wallet_nfts)
            return db_tokens
        else:
            print(f"⚠️ No NFTs found in PostgreSQL for wallet {wallet[:6]}...{wallet[-4:]}")
    except Exception as e:
        print(f"⚠️ Error querying PostgreSQL for wallet NFTs: {e}")

    # 🔥 PRIORIDAD 3: Si no hay cache ni DB, intentar blockchain (solo si hay conexión)
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

    # 🔥 Generar image_url usando CID de mainnet
    padded_token_id = str(token_id).zfill(5)
    mainnet_image_url = f"{IPFS_GATEWAY}{IPFS_MAINNET_IMAGES_CID}/{padded_token_id}.png"

    # Default hero template
    default_hero = {
        "token_id": padded_token_id,
        "name": f"Emissary #{padded_token_id}",
        "race_class": "Unknown",
        "guild": "Unassigned",
        "image_url": mainnet_image_url,
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

    if not os.path.exists(path):
        # Si no existe metadata, crear un hero básico
        return default_hero

    try:
        with open(path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️ Invalid JSON in metadata file {filename}: {e}")
        return default_hero
    except Exception as e:
        print(f"⚠️ Error reading metadata file {filename}: {e}")
        return default_hero

    # Extraer datos del fixed_profile
    fixed = metadata.get("fixed_profile", {})
    race = fixed.get("race", "Unknown")
    char_class = fixed.get("class", "Unknown")
    guild = fixed.get("starting_guild", "Unassigned")

    # Crear race_class combinado
    race_class = f"{race} {char_class}"

    # 🔥 Generar image_url usando el CID de mainnet directamente
    # Esto garantiza que siempre usemos las imágenes correctas de Base Mainnet
    padded_id = str(token_id).zfill(5)
    image_url = f"{IPFS_GATEWAY}{IPFS_MAINNET_IMAGES_CID}/{padded_id}.png"

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

def get_player_emissaries_from_new_tables(wallet):
    """
    Obtener emissaries de una wallet desde las nuevas tablas de metadata.
    NOTA: Este es un sistema LEGACY - el sistema principal usa la tabla 'nfts'.
    Si falla, retorna lista vacía sin afectar el funcionamiento.
    """
    try:
        conn = db.get_connection()
        if not conn:
            return []

        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Query simplificada - solo campos que sabemos que existen
        cur.execute("""
            SELECT m.token_id, m.name, m.race, m.class, m.guild, m.background,
                   m.base_power, m.image_cid,
                   COALESCE(s.xp, 0) as xp,
                   COALESCE(s.energy, 100) as energy,
                   COALESCE(s.deaths, 0) as deaths,
                   COALESCE(s.state, 'idle') as state,
                   COALESCE(s.total_missions, 0) as total_missions,
                   COALESCE(s.successful_missions, 0) as successful_missions,
                   COALESCE(s.aura, 0) as aura
            FROM emissaries_metadata m
            JOIN emissaries_state s ON m.token_id = s.token_id
            WHERE LOWER(s.wallet_address) = LOWER(%s)
            ORDER BY m.token_id
        """, (wallet,))

        emissaries = cur.fetchall() or []

        cur.close()
        db.release_connection(conn)

        return emissaries

    except Exception as e:
        # Falla silenciosamente - el sistema principal usa 'nfts'
        print(f"⚠️ emissaries_* tables not available (using nfts instead): {e}")
        if conn:
            try:
                db.release_connection(conn)
            except:
                pass
        return []

@app.route("/api/player/<wallet>", methods=["GET", "POST"])
@rate_limit(requests_per_minute=20)
def api_player(wallet):
    # 🔥 NORMALIZE wallet address to lowercase to avoid case sensitivity issues
    wallet = wallet.lower()

    print(f"\n{'='*60}")
    print(f"🔍 /api/player/{wallet[:6]}...{wallet[-4:]} - Method: {request.method}")

    # 🔥 CRITICAL FIX: Si es POST, SOLO guardar cache y retornar
    # Esto evita doble sincronización que causa pérdida de estado ON_MISSION
    if request.method == "POST":
        synced_count = 0
        try:
            # Step 1: Parse request data
            try:
                data = request.get_json(force=True)
                token_ids = data.get("token_ids", [])
                total_supply = data.get("total_supply", None)
                print(f"📦 POST data received: {len(token_ids)} token_ids, total_supply={total_supply}")
            except Exception as e:
                print(f"❌ Error parsing request data: {e}")
                return jsonify({"success": False, "error": f"Invalid request data: {str(e)}"}), 400

            # Step 2: Save wallet NFTs to cache
            if token_ids:
                try:
                    wallet_nfts = load_json(WALLET_NFTS_PATH, {})
                    print(f"📂 Current wallet_nfts keys: {list(wallet_nfts.keys())}")
                    wallet_nfts[wallet] = token_ids
                    save_json(WALLET_NFTS_PATH, wallet_nfts)
                    print(f"✅ Wallet {wallet[:6]}...{wallet[-4:]} registered with {len(token_ids)} NFTs: {token_ids}")
                    print(f"📂 Updated wallet_nfts keys: {list(wallet_nfts.keys())}")
                except Exception as e:
                    print(f"❌ Error saving wallet NFTs cache: {e}")
                    # Continue anyway - this is not critical

                # Step 3: Auto-sync NFTs to database
                try:
                    print(f"🔄 AUTO-SYNC: Syncing {len(token_ids)} NFTs to database...")
                    for token_id in token_ids:
                        try:
                            # Sincronizar NFT a DB (si existe preserva estado, si es nuevo lo crea)
                            nft = sync_nft_to_database(token_id, owner_wallet=wallet)
                            synced_count += 1
                            ds = nft.get("dynamic_state", {})
                            print(f"  ✅ {token_id} → DB (xp: {ds.get('xp_total', 0)}, state: {ds.get('state', 'READY')})")
                        except Exception as e:
                            print(f"  ⚠️ Error syncing token {token_id}: {e}")
                            import traceback
                            traceback.print_exc()
                            # Continue with other NFTs
                    print(f"✅ Auto-sync complete: {synced_count}/{len(token_ids)} NFTs synced to database")
                except Exception as e:
                    print(f"❌ Error during NFT sync process: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue anyway

                # Step 4: Recalculate guild stats
                try:
                    print(f"📊 AUTO-RECALC: Updating global stats...")
                    calculate_guilds_data()
                    print(f"✅ Guild stats updated")
                except Exception as e:
                    print(f"❌ Error calculating guild stats: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue anyway

            # Step 5: Update total supply
            if total_supply is not None:
                try:
                    stats_obj = load_json(STATS_PATH, {})
                    stats_obj["total_characters"] = total_supply
                    save_json(STATS_PATH, stats_obj)
                    print(f"✅ Contract total supply updated: {total_supply} characters")
                except Exception as e:
                    print(f"❌ Error updating total supply: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue anyway

            print(f"{'='*60}\n")
            # ✅ RETORNAR inmediatamente - NO llamar ensure_player() aquí
            return jsonify({
                "success": True,
                "token_ids_cached": len(token_ids) if token_ids else 0,
                "synced_to_database": synced_count
            })

        except Exception as e:
            print(f"❌ CRITICAL ERROR processing POST data: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return jsonify({
                "success": False,
                "error": str(e),
                "synced_count": synced_count
            }), 500

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

    # 🔥 NUEVO: Agregar emissaries de las nuevas tablas PostgreSQL
    try:
        new_emissaries = get_player_emissaries_from_new_tables(wallet)
        if new_emissaries:
            print(f"  📊 Found {len(new_emissaries)} emissaries in new tables")
            if 'heroes' not in player_obj:
                player_obj['heroes'] = []

            # Agregar los nuevos emissaries que no estén ya
            existing_ids = [h.get('token_id') for h in player_obj.get('heroes', [])]
            for emissary in new_emissaries:
                if emissary['token_id'] not in existing_ids:
                    player_obj['heroes'].append(emissary)
                    print(f"    ➕ Added emissary {emissary['token_id']} from new tables")
    except Exception as e:
        print(f"  ⚠️ Error merging emissaries from new tables: {e}")

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

    # 🔥 Add equipment data to each hero before returning
    if POSTGRESQL_AVAILABLE and player_obj and 'heroes' in player_obj:
        try:
            conn = db.get_connection()
            if conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                for hero in player_obj['heroes']:
                    token_id = hero.get('token_id')
                    if token_id:
                        cursor.execute("""
                            SELECT weapon_id, armor_id, helmet_id, accessory_id,
                                   amulet_id, rune_ids
                            FROM nfts WHERE token_id = %s
                        """, (token_id,))
                        equip_row = cursor.fetchone()
                        if equip_row:
                            hero['weapon_id'] = equip_row.get('weapon_id')
                            hero['armor_id'] = equip_row.get('armor_id')
                            hero['helmet_id'] = equip_row.get('helmet_id')
                            hero['accessory_id'] = equip_row.get('accessory_id')
                            hero['amulet_id'] = equip_row.get('amulet_id')
                            hero['rune_ids'] = equip_row.get('rune_ids') or []
                db.release_connection(conn)
        except Exception as e:
            print(f"⚠️ Error adding equipment data to heroes: {e}")

    # 🔥 Add active mission bonuses for heroes ON_MISSION
    try:
        active_missions = load_active_missions()
        for hero in player_obj.get('heroes', []):
            token_id = hero.get('token_id')
            ds = hero.get('dynamic_state', {})
            if token_id and ds.get('state') == 'ON_MISSION':
                mission_key = f"{wallet}_{token_id}"
                active_mission = active_missions.get(mission_key, {})
                if active_mission:
                    # Add equipment bonuses from active mission
                    equipment_bonuses = active_mission.get('equipment_bonuses', {})
                    if equipment_bonuses:
                        hero['active_mission_bonuses'] = {
                            'ember_boost': equipment_bonuses.get('ember', 0),
                            'xp_boost': equipment_bonuses.get('xp', 0),
                            'speed_bonus': equipment_bonuses.get('speed', 0),
                            'energy_reduction': equipment_bonuses.get('energy', 0),
                            'death_protection': equipment_bonuses.get('death', 0),
                            'item_count': equipment_bonuses.get('item_count', 0),
                            'rune_count': equipment_bonuses.get('rune_count', 0)
                        }
                    # Add stored duration (with speed bonus applied)
                    if active_mission.get('duration_hours'):
                        hero['active_mission_duration'] = active_mission.get('duration_hours')
                        hero['active_mission_base_duration'] = active_mission.get('base_duration_hours', active_mission.get('duration_hours'))
    except Exception as e:
        print(f"⚠️ Error adding active mission bonuses: {e}")

    return jsonify(player_obj)

# ---------------------------------
# API: PENDING CLAIMS (Items & Runes drops)
# ---------------------------------

@app.route("/api/claims/<wallet>", methods=["GET"])
@rate_limit(requests_per_minute=10)
def api_get_pending_claims(wallet):
    """
    Get all pending claims for a wallet.
    Returns list of claims that can be claimed on-chain.
    """
    wallet = wallet.lower()
    claims = get_pending_claims(wallet)

    # Format claims for frontend
    formatted_claims = []
    for claim in claims:
        formatted_claims.append({
            "id": claim["id"],
            "type": claim["claim_type"],
            "claim_id": claim["claim_id"],
            "signature": claim["signature"],
            "mission_id": claim["mission_id"],
            "difficulty": claim["difficulty"],
            "contract": EMBER_RUNES_CONTRACT if claim["claim_type"] == "RUNE" else EMBER_ITEMS_CONTRACT,
            "created_at": claim["created_at"].isoformat() if claim.get("created_at") else None
        })

    return jsonify({
        "wallet": wallet,
        "pending_claims": formatted_claims,
        "count": len(formatted_claims)
    })

@app.route("/api/claims/confirm", methods=["POST"])
@rate_limit(requests_per_minute=10)
def api_confirm_claim():
    """
    Confirm that a claim was successfully claimed on-chain.
    Called by frontend after successful blockchain transaction.
    Also generates the item and adds it to the player's vault.

    POST: { "claim_id": "0x...", "token_id": 123, "tx_hash": "0x...", "wallet": "0x..." }
    """
    data = request.get_json(force=True)
    claim_id = data.get("claim_id")
    token_id = data.get("token_id")
    tx_hash = data.get("tx_hash")
    frontend_wallet = data.get("wallet", "").lower()  # Fallback from frontend

    print(f"\n{'='*60}")
    print(f"🔔 CLAIM CONFIRM REQUEST")
    print(f"   claim_id: {claim_id}")
    print(f"   token_id: {token_id}")
    print(f"   tx_hash: {tx_hash[:20] if tx_hash else 'None'}...")
    print(f"   frontend_wallet: {frontend_wallet[:10] if frontend_wallet else 'None'}...")
    print(f"{'='*60}")

    if not claim_id:
        print("❌ Missing claim_id")
        abort(400, "Missing claim_id")

    # 🔒 Use locked version when enabled
    if USE_CLAIM_LOCKS and POSTGRESQL_AVAILABLE:
        print("   🔒 Using locked transaction for claim confirm")
        response, status_code = confirm_claim_with_lock(claim_id, token_id, tx_hash, frontend_wallet)
        return jsonify(response), status_code

    # 🔥 Get claim details BEFORE marking as claimed
    claim_details = get_claim_details(claim_id)
    generated_item = None

    print(f"📋 Claim details from DB: {claim_details}")

    if claim_details and claim_details.get("status") == "pending":
        # Generate item based on claim type and difficulty
        claim_type = claim_details.get("claim_type", "ITEM")
        difficulty = claim_details.get("difficulty") or "EASY"
        wallet = claim_details.get("wallet_address") or frontend_wallet

        if not wallet:
            print("⚠️ No wallet address found in claim or request!")

        print(f"🎁 Generating {claim_type} for wallet {wallet[:10] if wallet else 'NONE'}... (difficulty: {difficulty})")

        try:
            item_data = generate_random_item(claim_type, difficulty, wallet)
            print(f"   Item data: {item_data}")
            item_id = insert_item_to_vault(item_data)

            if item_id:
                generated_item = {
                    "id": item_id,
                    "name": item_data["name"],
                    "type": item_data["type"],
                    "rarity": item_data["rarity"],
                    "stats": item_data["stats"]
                }
                print(f"✅ Generated {item_data['rarity']} {item_data['type']}: {item_data['name']} (ID: {item_id})")
            else:
                print(f"⚠️ Failed to insert item to vault (but claim will still be marked)")
        except Exception as e:
            print(f"❌ Error generating item: {e}")
            import traceback
            traceback.print_exc()
    elif claim_details and claim_details.get("status") != "pending":
        print(f"⚠️ Claim {claim_id} already has status: {claim_details.get('status')}")
    else:
        print(f"⚠️ Claim {claim_id} not found in database")

    # Mark the claim as claimed
    success = mark_claim_as_claimed(claim_id, token_id, tx_hash)
    print(f"📝 Mark claim as claimed: {'SUCCESS' if success else 'FAILED'}")

    if success:
        response = {
            "success": True,
            "message": "Claim confirmed",
            "claim_id": claim_id,
            "token_id": token_id
        }
        if generated_item:
            response["item"] = generated_item
            response["message"] = f"Claim confirmed! You received: {generated_item['name']} ({generated_item['rarity']})"
        print(f"✅ Response: {response}")
        return jsonify(response)
    else:
        print(f"❌ Failed to mark claim as claimed")
        return jsonify({
            "success": False,
            "error": "Failed to confirm claim"
        }), 500

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
    try:
        print(f"\n🎮 PARTY MISSION START REQUEST:")
        print(f"  Wallet: {wallet}")
        print(f"  Hero IDs: {hero_ids}")
        print(f"  Mission ID: {mission_id}")

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
        active_missions = load_active_missions()
        mission_key = f"{wallet}_{mission_id}_party"
        active_missions[mission_key] = {
            "wallet": wallet,
            "hero_ids": hero_ids,
            "mission_id": mission_id,
            "start_time": now_utc,
            "duration_hours": mission["duration_hours"],
            "is_party": True
        }

        save_active_missions(active_missions)

        # Save player data
        players_all[wallet] = player_obj
        save_json(PLAYERS_PATH, players_all)
        save_json(STATS_PATH, stats_obj)

        print(f"\n🎮 PARTY MISSION STARTED SUCCESSFULLY:")
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

    except Exception as e:
        print(f"\n❌ PARTY MISSION START ERROR:")
        print(f"  Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Party mission start failed: {str(e)}"}), 500

@app.route("/api/mission/start", methods=["POST"])
@rate_limit(requests_per_minute=10)
def api_mission_start():
    """
    Start a mission (solo or party).
    POST solo: { "wallet": "0x...", "hero_id": "00001", "mission_id": "001" }
    POST party: { "wallet": "0x...", "hero_ids": ["00001", "00002", ...], "mission_id": "003" }
    """
    try:
        data = request.get_json(force=True)
        wallet = data.get("wallet")
        hero_id = data.get("hero_id")
        hero_ids = data.get("hero_ids")
        mission_id = data.get("mission_id")

        print(f"\n🚀 MISSION START REQUEST:")
        print(f"  Wallet: {wallet}")
        print(f"  Hero ID: {hero_id}")
        print(f"  Hero IDs: {hero_ids}")
        print(f"  Mission ID: {mission_id}")

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

        # 🔒 Use locked version for solo missions when enabled
        if USE_MISSION_LOCKS and POSTGRESQL_AVAILABLE:
            print("   🔒 Using locked transaction for solo mission start")
            response, status_code = start_mission_with_lock(wallet, hero_id, mission_id)
            return jsonify(response), status_code

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

        # Check energy (with potential buff reduction)
        base_energy_cost = mission["energy_cost"]  # Save original before reductions
        cost_energy = base_energy_cost
        energy_current = ds.get("energy_current", 0)

        # 🔮 APPLY ENERGY COST REDUCTION BUFF
        buff = ds.get("ember_roll_buff")
        energy_reduction = 0
        if buff:
            expires_at = buff.get("expires_at")
            if expires_at:
                try:
                    expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    if now < expires_dt:
                        # Buff is active
                        energy_reduction = buff.get("energy_reduction", 0)
                        if energy_reduction > 0:
                            original_cost = cost_energy
                            cost_energy = int(cost_energy * (100 - energy_reduction) / 100)
                            print(f"🔮 Energy cost reduction buff active: {original_cost} → {cost_energy} (-{energy_reduction}%)")
                except Exception as e:
                    print(f"⚠️ Error parsing buff expiration: {e}")

        # ⚔️ APPLY EQUIPMENT BONUSES (energy reduction from items/runes)
        equipment_bonuses = get_emissary_bonuses(hero_id)
        equipment_energy_reduction = equipment_bonuses.get('energy', 0)
        if equipment_energy_reduction > 0:
            original_cost = cost_energy
            cost_energy = max(1, int(cost_energy * (100 - equipment_energy_reduction) / 100))
            print(f"⚔️ Equipment energy reduction: {original_cost} → {cost_energy} (-{equipment_energy_reduction}%)")

        # ⚔️ APPLY SPEED BONUS (reduce mission duration)
        base_duration = mission["duration_hours"]
        equipment_speed_bonus = equipment_bonuses.get('speed', 0)
        if equipment_speed_bonus > 0:
            # Speed reduces duration, minimum 10% of original
            reduced_duration = max(base_duration * 0.1, base_duration * (100 - equipment_speed_bonus) / 100)
            effective_duration = round(reduced_duration, 2)
            print(f"⚔️ Equipment speed bonus: {base_duration}h → {effective_duration}h (-{equipment_speed_bonus}%)")
        else:
            effective_duration = base_duration

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

        # Track active mission (with equipment bonuses for completion)
        active_missions = load_active_missions()
        mission_key = f"{wallet}_{hero_id}"
        active_missions[mission_key] = {
            "wallet": wallet,
            "hero_id": hero_id,
            "mission_id": mission_id,
            "start_time": ds["mission_start_time"],
            "duration_hours": effective_duration,
            "base_duration_hours": base_duration,
            "equipment_bonuses": equipment_bonuses  # Store for completion rewards
        }

        print(f"\n🔥 SAVING ACTIVE MISSION:")
        print(f"  Mission Key: {mission_key}")
        print(f"  Wallet: {wallet}")
        print(f"  Hero ID: {hero_id}")
        print(f"  Mission ID: {mission_id}")
        print(f"  Start Time: {ds['mission_start_time']}")
        print(f"  Duration: {effective_duration}h (base: {base_duration}h)")
        print(f"  Equipment Bonuses: ember +{equipment_bonuses['ember']}%, xp +{equipment_bonuses['xp']}%")
        print(f"  Total active missions: {len(active_missions)}")

        save_active_missions(active_missions)

        # Verificar que se guardó correctamente
        verify_missions = load_active_missions()
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

        # Build response with equipment bonuses in correct format
        # Calculate actual duration in minutes for frontend display
        actual_duration_minutes = int(effective_duration * 60)

        response_data = {
            "success": True,
            "hero_id": hero_id,
            "mission_id": mission_id,
            "mission_name": mission["name"],
            "difficulty": mission["difficulty"],
            "estimated_success_rate": success_rate,
            "hero_energy_now": ds["energy_current"],
            "completion_time": (datetime.fromisoformat(ds["mission_start_time"].replace("Z", "+00:00")) + timedelta(hours=effective_duration)).isoformat(),
            # Duration info (for visual display: base tachado → actual en verde)
            "duration": {
                "base_hours": base_duration,
                "actual_hours": effective_duration,
                "actual_minutes": actual_duration_minutes
            },
            # Energy info (for visual display: base tachado → actual en verde)
            "energy": {
                "base": base_energy_cost,
                "actual": cost_energy
            },
            # Legacy fields for backwards compatibility
            "duration_hours": effective_duration,
            "base_duration_hours": base_duration,
            "energy_spent": cost_energy
        }

        # Include bonuses applied (for badge display)
        response_data["bonuses_applied"] = {
            "ember": equipment_bonuses['ember'],
            "xp": equipment_bonuses['xp'],
            "energy": equipment_bonuses['energy'],
            "death": equipment_bonuses['death'],
            "speed": equipment_bonuses['speed']
        }

        # Also include equipment_bonuses for backwards compatibility
        response_data["equipment_bonuses"] = {
            "ember_boost": equipment_bonuses['ember'],
            "xp_boost": equipment_bonuses['xp'],
            "energy_reduction": equipment_bonuses['energy'],
            "death_protection": equipment_bonuses['death'],
            "speed_bonus": equipment_bonuses['speed'],
            "item_count": equipment_bonuses['item_count'],
            "rune_count": equipment_bonuses['rune_count']
        }

        # 🔍 DEBUG: Log response data
        print(f"\n🔍 MISSION START RESPONSE DEBUG:")
        print(f"  base_duration: {base_duration}h")
        print(f"  effective_duration: {effective_duration}h")
        print(f"  actual_duration_minutes: {actual_duration_minutes}m")
        print(f"  base_energy_cost: {base_energy_cost}")
        print(f"  cost_energy: {cost_energy}")
        print(f"  equipment_bonuses: {equipment_bonuses}")
        print(f"  response_data['duration']: {response_data['duration']}")
        print(f"  response_data['energy']: {response_data['energy']}")
        print(f"  response_data['bonuses_applied']: {response_data['bonuses_applied']}")

        return jsonify(response_data)

    except Exception as e:
        print(f"\n❌ MISSION START ERROR:")
        print(f"  Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Mission start failed: {str(e)}"}), 500


@app.route("/api/mission/preview", methods=["POST"])
def api_mission_preview():
    """
    Preview mission with equipment bonuses applied.
    Shows base values vs boosted values before starting a mission.
    POST: { "wallet": "0x...", "hero_id": "00001", "mission_id": "001" }
    """
    try:
        data = request.get_json(force=True)
        wallet = data.get("wallet", "").lower()
        hero_id = data.get("hero_id")
        mission_id = data.get("mission_id")

        if not wallet or not hero_id or not mission_id:
            return jsonify({"error": "wallet, hero_id and mission_id required"}), 400

        # Find mission
        mission = None
        for m in MISSIONS:
            if m["id"] == mission_id:
                mission = m
                break
        if mission is None:
            for e in EVENTS:
                if e["id"] == mission_id:
                    mission = e
                    break
        if mission is None:
            return jsonify({"error": "Mission not found"}), 404

        # Get equipment bonuses for this emissary
        equipment_bonuses = get_emissary_bonuses(hero_id)

        # Calculate base values from mission config
        base_energy_cost = mission["energy_cost"]
        base_duration = mission["duration_hours"]
        base_xp_reward = mission["reward_xp"]
        base_aura_reward = mission["reward_aura"]
        base_death_chance = mission.get("death_chance", 0)

        # Calculate boosted values
        energy_reduction = equipment_bonuses.get('energy', 0)
        speed_bonus = equipment_bonuses.get('speed', 0)
        xp_boost = equipment_bonuses.get('xp', 0)
        ember_boost = equipment_bonuses.get('ember', 0)
        death_protection = equipment_bonuses.get('death', 0)

        # Apply reductions/boosts
        boosted_energy_cost = max(1, int(base_energy_cost * (100 - energy_reduction) / 100)) if energy_reduction > 0 else base_energy_cost
        boosted_duration = round(max(base_duration * 0.1, base_duration * (100 - speed_bonus) / 100), 2) if speed_bonus > 0 else base_duration
        boosted_xp_reward = int(base_xp_reward * (100 + xp_boost) / 100) if xp_boost > 0 else base_xp_reward
        boosted_aura_reward = int(base_aura_reward * (100 + ember_boost) / 100) if ember_boost > 0 else base_aura_reward

        # Death protection reduces effective death chance
        boosted_death_chance = round(base_death_chance * (100 - death_protection) / 100, 2) if death_protection > 0 and base_death_chance > 0 else base_death_chance

        return jsonify({
            "success": True,
            "hero_id": hero_id,
            "mission_id": mission_id,
            "mission_name": mission["name"],
            "difficulty": mission["difficulty"],

            # Base values (without equipment)
            "base": {
                "energy_cost": base_energy_cost,
                "duration_hours": base_duration,
                "xp_reward": base_xp_reward,
                "aura_reward": base_aura_reward,
                "death_chance": base_death_chance
            },

            # Boosted values (with equipment bonuses)
            "boosted": {
                "energy_cost": boosted_energy_cost,
                "duration_hours": boosted_duration,
                "xp_reward": boosted_xp_reward,
                "aura_reward": boosted_aura_reward,
                "death_chance": boosted_death_chance
            },

            # Equipment bonus details
            "equipment_bonuses": {
                "energy_reduction": energy_reduction,
                "speed_bonus": speed_bonus,
                "xp_boost": xp_boost,
                "ember_boost": ember_boost,
                "death_protection": death_protection,
                "item_count": equipment_bonuses.get('item_count', 0),
                "rune_count": equipment_bonuses.get('rune_count', 0)
            },

            # Has any bonuses active?
            "has_bonuses": equipment_bonuses.get('item_count', 0) > 0 or equipment_bonuses.get('rune_count', 0) > 0
        })

    except Exception as e:
        print(f"❌ Mission preview error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


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
        outcome, details = roll_mission_outcome(hero, mission)

        # Extract values from details dictionary
        xp_gain = details.get("xp_gain", 0)
        aura_gain = details.get("aura_gain", 0)
        xp_loss = details.get("xp_loss", 0)

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
    delete_active_mission(mission_key)

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

    # 🔥 DROP SYSTEM: Party missions have higher drop rates!
    # FAIL-SAFE: Wrap in try/except so mission completes even if drops fail
    drops = []
    drops_result = {"item": False, "rune": False, "rates": DROP_RATES.get("PARTY", {"item": 25, "rune": 12})}
    drop_error_reason = None

    # Only roll for drops if there was at least one success
    if successes > 0:
        try:
            drops_result = calculate_drops(mission.get("difficulty", "EASY"), is_party=True)

            if drops_result["item"]:
                item_claim = generate_claim_signature(wallet, "ITEM", mission_id)
                if item_claim:
                    save_pending_claim(wallet, "ITEM", item_claim["claim_id"], item_claim["signature"],
                                      mission_id, hero_ids[0], mission.get("difficulty", "EASY"))
                    drops.append({
                        "type": "ITEM",
                        "claim_id": item_claim["claim_id"],
                        "signature": item_claim["signature"],
                        "contract": EMBER_ITEMS_CONTRACT
                    })
                else:
                    print(f"⚠️ Item drop won but signature generation failed")
                    if not drop_error_reason:
                        drop_error_reason = "Signature generation unavailable - check BACKEND_SIGNER_PRIVATE_KEY"

            if drops_result["rune"]:
                rune_claim = generate_claim_signature(wallet, "RUNE", mission_id)
                if rune_claim:
                    save_pending_claim(wallet, "RUNE", rune_claim["claim_id"], rune_claim["signature"],
                                      mission_id, hero_ids[0], mission.get("difficulty", "EASY"))
                    drops.append({
                        "type": "RUNE",
                        "claim_id": rune_claim["claim_id"],
                        "signature": rune_claim["signature"],
                        "contract": EMBER_RUNES_CONTRACT
                    })
                else:
                    print(f"⚠️ Rune drop won but signature generation failed")
                    if not drop_error_reason:
                        drop_error_reason = "Signature generation unavailable - check BACKEND_SIGNER_PRIVATE_KEY"

        except Exception as drop_err:
            print(f"❌ DROP SYSTEM ERROR in party mission (mission still completes): {drop_err}")
            import traceback
            traceback.print_exc()
            drop_error_reason = f"Drop system error: {str(drop_err)}"
            # Mission continues - drops just won't be awarded this time

    response_data = {
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
        },
        "drops": drops,
        "drop_rates": drops_result["rates"]
    }

    if drop_error_reason:
        response_data["drop_error_reason"] = drop_error_reason

    return jsonify(response_data)

# Feature flags: Enable database locks to prevent race conditions
USE_MISSION_LOCKS = os.environ.get('USE_MISSION_LOCKS', 'true').lower() == 'true'
USE_EQUIPMENT_LOCKS = os.environ.get('USE_EQUIPMENT_LOCKS', 'true').lower() == 'true'
USE_CLAIM_LOCKS = os.environ.get('USE_CLAIM_LOCKS', 'true').lower() == 'true'

@app.route("/api/mission/complete", methods=["POST"])
@rate_limit(requests_per_minute=10)
def api_mission_complete():
    """
    Complete a mission (solo or party).
    POST solo: { "wallet": "0x...", "hero_id": "00001" }
    POST party: Mission is detected automatically from active_missions

    When USE_MISSION_LOCKS=true (default), uses database locks to prevent race conditions
    from concurrent requests completing the same mission twice.
    """
    print("\n" + "=" * 60)
    print("📥 MISSION COMPLETE REQUEST RECEIVED")
    print("=" * 60)

    try:
        # Step 1: Parse request data
        print("\n[STEP 1] Parsing request data...")
        data = request.get_json(force=True)
        print(f"   📦 Raw request data: {data}")

        wallet = data.get("wallet")
        hero_id = data.get("hero_id")

        print(f"   Wallet: {wallet}")
        print(f"   Hero ID: {hero_id}")

        if not wallet:
            print("   ❌ ERROR: Missing wallet")
            abort(400, "Missing wallet")

        # 🔒 NEW: Use locked version for solo missions when enabled
        # This prevents race conditions from double-clicks or concurrent requests
        if USE_MISSION_LOCKS and hero_id and POSTGRESQL_AVAILABLE:
            # Check if this is a party mission first
            wallet_lower = wallet.lower()
            active_missions = load_active_missions()
            is_party = False
            for key, mission_data in active_missions.items():
                if mission_data.get("is_party") and mission_data.get("wallet") == wallet_lower:
                    if hero_id in mission_data.get("hero_ids", []):
                        is_party = True
                        break

            if not is_party:
                # Solo mission - use locked version
                print("   🔒 Using locked transaction for solo mission completion")
                response, status_code = complete_mission_with_lock(wallet, hero_id)
                return jsonify(response), status_code

        # 🔥 NORMALIZE wallet address to lowercase
        wallet = wallet.lower()
        print(f"   Normalized wallet: {wallet}")

        # Step 2: Check for party mission
        print("\n[STEP 2] Loading active missions...")
        active_missions = load_active_missions()
        print(f"   Active missions count: {len(active_missions)}")

        # Look for party mission for this wallet
        party_mission = None
        for key, mission_data in active_missions.items():
            if mission_data.get("is_party") and mission_data.get("wallet") == wallet:
                # Check if the provided hero_id is part of this party
                if hero_id and hero_id in mission_data.get("hero_ids", []):
                    party_mission = mission_data.copy()
                    party_mission["mission_key"] = key
                    print(f"   Found party mission: {key}")
                    break

        if party_mission:
            # PARTY MISSION COMPLETION
            print("\n[STEP 3] Handling PARTY mission completion...")
            return handle_party_mission_complete(wallet, party_mission)

        # SOLO MISSION COMPLETION (EXISTING CODE CONTINUES)
        print("\n[STEP 3] Handling SOLO mission completion...")

        if not hero_id:
            print("   ❌ ERROR: Missing hero_id for solo mission")
            abort(400, "Missing hero_id for solo mission")

        # Step 4: Load stats and player
        print("\n[STEP 4] Loading stats and player data...")
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
        print(f"   Stats loaded: missions_completed={stats_obj.get('missions_completed', 0)}")

        player_obj, players_all = ensure_player(wallet)
        print(f"   Player loaded: {len(player_obj.get('heroes', []))} heroes")

        # Apply passive gains
        print("\n[STEP 5] Applying passive and regen...")
        player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

        # Step 6: Find hero
        print(f"\n[STEP 6] Finding hero {hero_id}...")
        hero = None
        for h in player_obj.get("heroes", []):
            if h.get("token_id") == hero_id:
                hero = h
                break

        if hero is None:
            print(f"   ❌ ERROR: Hero {hero_id} not found in player's heroes")
            print(f"   Available heroes: {[h.get('token_id') for h in player_obj.get('heroes', [])]}")
            abort(404, "Hero not found")

        print(f"   ✅ Hero found: {hero.get('name', 'Unknown')}")

        ds = hero["dynamic_state"]
        print(f"   Dynamic state: {ds.get('state')}, mission_id={ds.get('current_mission_id')}")

        # Step 7: Check if hero is on a mission
        print("\n[STEP 7] Checking mission state...")
        if ds.get("state") != "ON_MISSION":
            print(f"   ❌ ERROR: Hero state is '{ds.get('state')}', not ON_MISSION")
            abort(400, "Hero is not on a mission")

        mission_id = ds.get("current_mission_id")
        if not mission_id:
            print("   ❌ ERROR: No current_mission_id in dynamic_state")
            abort(400, "No active mission found")

        print(f"   ✅ Hero is on mission: {mission_id}")

        # Step 7b: Retrieve active mission data with equipment bonuses
        mission_key = f"{wallet}_{hero_id}"
        active_mission_data = active_missions.get(mission_key, {})
        stored_equipment_bonuses = active_mission_data.get("equipment_bonuses", {
            'ember': 0, 'xp': 0, 'energy': 0, 'death': 0, 'speed': 0,
            'item_count': 0, 'rune_count': 0
        })
        # Use stored duration if available (has speed bonus applied)
        stored_duration = active_mission_data.get("duration_hours")
        print(f"   📦 Active mission data found: duration={stored_duration}h, bonuses={stored_equipment_bonuses}")

        # Step 8: Find mission config
        print(f"\n[STEP 8] Finding mission config for {mission_id}...")
        mission = None
        for m in MISSIONS:
            if m["id"] == mission_id:
                mission = m
                print(f"   Found in MISSIONS: {m['name']}")
                break

        # If not found in missions, check events
        if mission is None:
            print("   Not found in MISSIONS, checking EVENTS...")
            for e in EVENTS:
                if e["id"] == mission_id:
                    mission = e
                    print(f"   Found in EVENTS: {e['name']}")
                    break

        if mission is None:
            print(f"   ❌ ERROR: Mission config not found for {mission_id}")
            abort(400, "Mission configuration not found")

        # Step 9: Check duration (use stored duration with speed bonus if available)
        print("\n[STEP 9] Checking mission duration...")
        start_time_str = ds.get("mission_start_time")
        if not start_time_str:
            print("   ❌ ERROR: No mission_start_time found")
            abort(400, "Mission start time not found")

        # Use stored duration (with speed bonus) if available, otherwise use mission config
        effective_duration = stored_duration if stored_duration is not None else mission["duration_hours"]
        print(f"   Start time: {start_time_str}")
        hours_elapsed = hours_since(start_time_str)
        print(f"   Hours elapsed: {hours_elapsed:.2f} / {effective_duration} required (base: {mission['duration_hours']}h)")

        if hours_elapsed < effective_duration:
            hours_left = effective_duration - hours_elapsed
            print(f"   ❌ ERROR: Mission not complete, {hours_left:.1f}h remaining")
            abort(400, f"Mission not yet complete. {hours_left:.1f} hours remaining")

        # Step 10: Roll for outcome (with equipment death protection)
        print("\n[STEP 10] Rolling mission outcome...")
        equipment_death_protection = stored_equipment_bonuses.get('death', 0)
        outcome, details = roll_mission_outcome(hero, mission, equipment_death_protection)
        print(f"   Outcome: {outcome}")
        print(f"   Details: {details}")

        hero_guild_name = hero.get("guild") or ds.get("current_guild", "Unknown Guild")
        total_missions_completed = ds.get("total_missions_completed", 0)
        print(f"   Guild: {hero_guild_name}, Total completed: {total_missions_completed}")

        # Step 11: Process outcome
        print(f"\n[STEP 11] Processing {outcome} outcome...")

        if outcome == "SUCCESS":
            print("   Processing SUCCESS...")
            xp_gain = details["xp_gain"]
            aura_gain = details["aura_gain"]

            # ⚔️ APPLY STORED EQUIPMENT BONUSES (EMBER→aura, XP→xp)
            # Note: Equipment bonuses from mission start are applied here
            xp_bonus = stored_equipment_bonuses.get('xp', 0)
            ember_bonus = stored_equipment_bonuses.get('ember', 0)

            if xp_bonus > 0:
                original_xp = xp_gain
                xp_gain = int(xp_gain * (100 + xp_bonus) / 100)
                print(f"   ⚔️ Equipment XP bonus: {original_xp} → {xp_gain} (+{xp_bonus}%)")

            if ember_bonus > 0:
                original_aura = aura_gain
                aura_gain = int(aura_gain * (100 + ember_bonus) / 100)
                print(f"   ⚔️ Equipment EMBER bonus: {original_aura} → {aura_gain} (+{ember_bonus}%)")

            print(f"   Final XP gain: {xp_gain}, Final Aura gain: {aura_gain}")

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
            print("\n[STEP 12] Updating guild stats...")
            stats_obj = update_guild_stats(hero_guild_name, xp_gain, aura_gain, stats_obj, success=True)

            # Check and grant achievements
            print("\n[STEP 13] Checking achievements...")
            achievements_granted = check_and_grant_mission_achievements(hero_id, total_missions_completed)
            print(f"   Achievements: {achievements_granted}")

            # Remove from active missions
            print("\n[STEP 14] Removing from active missions...")
            mission_key = f"{wallet}_{hero_id}"
            delete_active_mission(mission_key)
            print(f"   Deleted mission key: {mission_key}")

            # 🔥 GUARDAR a base de datos centralizada (fuente de verdad)
            print("\n[STEP 15] Saving to database...")
            ds["last_update"] = now_utc_str()
            update_nft_dynamic_state(hero_id, ds)
            print("   ✅ Database updated")

            # Guardar también a players.json (cache de sesión)
            print("\n[STEP 16] Saving to players.json cache...")
            player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)
            players_all[wallet] = player_obj
            save_json(PLAYERS_PATH, players_all)
            save_json(STATS_PATH, stats_obj)
            print("   ✅ JSON files saved")

            # 🔥 DROP SYSTEM: Calculate if player won item or rune
            print("\n[STEP 17] Calculating drops...")
            drops = []
            drops_result = {"item": False, "rune": False, "rates": DROP_RATES.get("EASY", {"item": 5, "rune": 1})}
            drop_error_reason = None

            try:
                drops_result = calculate_drops(mission.get("difficulty", "EASY"), is_party=False)
                print(f"   Drop result: item={drops_result['item']}, rune={drops_result['rune']}")

                if drops_result["item"]:
                    print("   🎁 Item drop won! Generating claim signature...")
                    item_claim = generate_claim_signature(wallet, "ITEM", mission_id)
                    if item_claim:
                        print(f"   Saving pending claim: {item_claim['claim_id']}")
                        save_pending_claim(wallet, "ITEM", item_claim["claim_id"], item_claim["signature"],
                                          mission_id, hero_id, mission.get("difficulty", "EASY"))
                        drops.append({
                            "type": "ITEM",
                            "claim_id": item_claim["claim_id"],
                            "signature": item_claim["signature"],
                            "contract": EMBER_ITEMS_CONTRACT
                        })
                        print("   ✅ Item claim saved")
                    else:
                        print("   ⚠️ Item drop won but signature generation failed")
                        if not drop_error_reason:
                            drop_error_reason = "Signature generation unavailable - check BACKEND_SIGNER_PRIVATE_KEY"

                if drops_result["rune"]:
                    print("   🎁 Rune drop won! Generating claim signature...")
                    rune_claim = generate_claim_signature(wallet, "RUNE", mission_id)
                    if rune_claim:
                        print(f"   Saving pending claim: {rune_claim['claim_id']}")
                        save_pending_claim(wallet, "RUNE", rune_claim["claim_id"], rune_claim["signature"],
                                          mission_id, hero_id, mission.get("difficulty", "EASY"))
                        drops.append({
                            "type": "RUNE",
                            "claim_id": rune_claim["claim_id"],
                            "signature": rune_claim["signature"],
                            "contract": EMBER_RUNES_CONTRACT
                        })
                        print("   ✅ Rune claim saved")
                    else:
                        print("   ⚠️ Rune drop won but signature generation failed")
                        if not drop_error_reason:
                            drop_error_reason = "Signature generation unavailable - check BACKEND_SIGNER_PRIVATE_KEY"

            except Exception as drop_err:
                print(f"   ❌ DROP SYSTEM ERROR (mission still completes): {drop_err}")
                import traceback
                traceback.print_exc()
                drop_error_reason = f"Drop system error: {str(drop_err)}"

            # Build response
            print("\n[STEP 18] Building response...")
            response_data = {
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
                "drops": drops,
                "drop_rates": drops_result["rates"],
                "message": f"🎉 SUCCESS! {hero.get('name', 'Emissary')} completed {mission['name']}!"
            }

            # Include equipment bonuses in response if any active
            if stored_equipment_bonuses.get('item_count', 0) > 0 or stored_equipment_bonuses.get('rune_count', 0) > 0:
                response_data["equipment_bonuses"] = {
                    "xp_boost": stored_equipment_bonuses.get('xp', 0),
                    "ember_boost": stored_equipment_bonuses.get('ember', 0),
                    "death_protection": stored_equipment_bonuses.get('death', 0),
                    "item_count": stored_equipment_bonuses.get('item_count', 0),
                    "rune_count": stored_equipment_bonuses.get('rune_count', 0)
                }

            if drop_error_reason:
                response_data["drop_error_reason"] = drop_error_reason

            print("=" * 60)
            print("✅ MISSION COMPLETE SUCCESS")
            print(f"   Hero: {hero_id}, Mission: {mission['name']}")
            print(f"   XP: +{xp_gain}, Aura: +{aura_gain}, Drops: {len(drops)}")
            print("=" * 60 + "\n")

            return jsonify(response_data)

        elif outcome == "FAILURE":
            print("   Processing FAILURE...")
            xp_loss = details["xp_loss"]
            print(f"   XP loss: {xp_loss}")

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
            mission_key = f"{wallet}_{hero_id}"
            delete_active_mission(mission_key)

            # 🔥 GUARDAR a base de datos centralizada (fuente de verdad)
            ds["last_update"] = now_utc_str()
            update_nft_dynamic_state(hero_id, ds)

            # Guardar también a players.json (cache de sesión)
            player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)
            players_all[wallet] = player_obj
            save_json(PLAYERS_PATH, players_all)
            save_json(STATS_PATH, stats_obj)

            print("=" * 60)
            print("⚠️ MISSION COMPLETE - FAILURE OUTCOME")
            print(f"   Hero: {hero_id}, Mission: {mission['name']}")
            print(f"   XP lost: {xp_loss}")
            print("=" * 60 + "\n")

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
            print("   Processing DEATH...")
            # Hero died
            ds["state"] = "FALLEN"
            ds["fallen_time"] = now_utc_str()
            ds["current_mission_id"] = None
            ds["mission_start_time"] = None
            ds["last_mission"] = f"{mission['name']} (Fallen)"

            # Increment death count
            death_count = ds.get("death_count", 0)
            ds["death_count"] = death_count + 1
            print(f"   Death count now: {ds['death_count']}")

            # Calculate reinvocation cost
            xp_cost, aura_cost = get_death_cost(death_count)
            print(f"   Reinvocation cost: XP={xp_cost}, Aura={aura_cost}")

            # Update stats
            stats_obj["missions_failed"] = stats_obj.get("missions_failed", 0) + 1
            stats_obj["total_deaths"] = stats_obj.get("total_deaths", 0) + 1

            # Remove from active missions
            mission_key = f"{wallet}_{hero_id}"
            delete_active_mission(mission_key)

            # 🔥 GUARDAR a base de datos centralizada (fuente de verdad)
            ds["last_update"] = now_utc_str()
            update_nft_dynamic_state(hero_id, ds)

            # Guardar también a players.json (cache de sesión)
            player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)
            players_all[wallet] = player_obj
            save_json(PLAYERS_PATH, players_all)
            save_json(STATS_PATH, stats_obj)

            print("=" * 60)
            print("💀 MISSION COMPLETE - DEATH OUTCOME")
            print(f"   Hero: {hero_id}, Mission: {mission['name']}")
            print("=" * 60 + "\n")

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
            print(f"   ❌ ERROR: Unknown outcome '{outcome}'")
            abort(500, "Unknown mission outcome")

    except Exception as e:
        # Global exception handler with full traceback
        import traceback
        print("\n" + "=" * 60)
        print("❌ MISSION COMPLETE CRITICAL ERROR")
        print("=" * 60)
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("=" * 60 + "\n")

        # Return detailed error for debugging
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }), 500

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

def fetch_ipfs_mainnet_metadata(token_id):
    """
    🔥 IPFS MAINNET: Fetch metadata from IPFS mainnet with caching.

    This is the source of truth for NFT base attributes (race, class, etc.)
    on Base mainnet. Uses in-memory cache with 10-minute TTL.

    Returns normalized metadata dict or None if fetch fails.
    """
    import time

    padded_id = str(token_id).zfill(5)

    # 1. Check cache first
    if padded_id in IPFS_METADATA_CACHE:
        cached_data, cached_time = IPFS_METADATA_CACHE[padded_id]
        if time.time() - cached_time < IPFS_CACHE_TTL_SECONDS:
            print(f"📦 IPFS cache hit for #{padded_id}")
            return cached_data

    # 2. Fetch from IPFS mainnet
    url = f"{IPFS_GATEWAY}{IPFS_MAINNET_METADATA_CID}/{padded_id}.json"
    print(f"🌐 Fetching IPFS mainnet metadata: {url}")

    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            print(f"⚠️ IPFS fetch failed for #{padded_id}: HTTP {response.status_code}")
            return None

        raw = response.json()

        # 3. Normalize metadata (same logic as load_base_metadata_for_token)
        mainnet_image = f"ipfs://{IPFS_MAINNET_IMAGES_CID}/{padded_id}.png"

        meta = {
            "token_id":        padded_id,
            "name":            raw.get("name", f"Emissary #{padded_id}"),
            "description":     raw.get("description", "Emissary of Emberholm."),
            "image":           mainnet_image,
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
            "power":           0,  # Static base power
        }

        # Extract from fixed_profile if present
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

        # Also check for power in dynamic_state (it's static but stored there in some formats)
        dyn_state = raw.get("dynamic_state", {})
        if isinstance(dyn_state, dict) and "power_current" in dyn_state:
            meta["power"] = dyn_state["power_current"]
        else:
            meta["power"] = 0

        # Fallback to attributes[] array (IPFS mainnet may store stats here)
        attrs = raw.get("attributes", [])
        for trait in attrs:
            ttype = trait.get("trait_type", "").lower()
            val   = trait.get("value")

            if ttype == "race" and meta["race"] == "Unknown":
                meta["race"] = val
            elif ttype == "class" and meta["class"] == "Unknown":
                meta["class"] = val
            elif ttype == "rarity" and meta["rarity"] == "Unknown":
                meta["rarity"] = val
            elif ttype == "guild" and meta["starting_guild"] == "Unknown":
                meta["starting_guild"] = val
            elif ttype == "starting guild" and meta["starting_guild"] == "Unknown":
                meta["starting_guild"] = val
            elif ttype == "age" and meta["age"] == 0:
                meta["age"] = val
            # 🔥 Extract stats from attributes[] if not in fixed_profile
            elif ttype == "str" and meta["str"] == 0:
                meta["str"] = val
            elif ttype == "dex" and meta["dex"] == 0:
                meta["dex"] = val
            elif ttype == "con" and meta["con"] == 0:
                meta["con"] = val
            elif ttype == "int" and meta["int"] == 0:
                meta["int"] = val
            elif ttype == "wis" and meta["wis"] == 0:
                meta["wis"] = val
            elif ttype == "cha" and meta["cha"] == 0:
                meta["cha"] = val
            elif ttype == "power" and meta.get("power", 0) == 0:
                meta["power"] = val

        # 4. Cache the result
        IPFS_METADATA_CACHE[padded_id] = (meta, time.time())
        print(f"✅ IPFS mainnet metadata cached for #{padded_id}: {meta['race']} {meta['class']}")

        return meta

    except requests.exceptions.Timeout:
        print(f"⚠️ IPFS fetch timeout for #{padded_id}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️ IPFS fetch error for #{padded_id}: {e}")
        return None
    except Exception as e:
        print(f"⚠️ IPFS fetch unexpected error for #{padded_id}: {e}")
        return None


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

    # 🔥 Generar image usando CID de mainnet directamente
    padded_id = str(token_id).zfill(5)
    mainnet_image = f"ipfs://{IPFS_MAINNET_IMAGES_CID}/{padded_id}.png"

    # base del resultado
    meta = {
        "token_id":        padded_id,
        "name":            raw.get("name", f"Emissary #{padded_id}"),
        "description":     raw.get("description", "Emissary of Emberholm."),
        "image":           mainnet_image,  # 🔥 Usar CID de mainnet
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
        "power":           0,  # Static base power
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

    # Also check for power in dynamic_state (it's static but stored there in some formats)
    dyn_state = raw.get("dynamic_state", {})
    if isinstance(dyn_state, dict) and "power_current" in dyn_state:
        meta["power"] = dyn_state["power_current"]

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
        elif ttype == "starting guild" and meta["starting_guild"] == "Unknown":
            meta["starting_guild"] = val
        elif ttype == "age" and meta["age"] == 0:
            meta["age"] = val
        # 🔥 Extract stats from attributes[] if not in fixed_profile
        elif ttype == "str" and meta["str"] == 0:
            meta["str"] = val
        elif ttype == "dex" and meta["dex"] == 0:
            meta["dex"] = val
        elif ttype == "con" and meta["con"] == 0:
            meta["con"] = val
        elif ttype == "int" and meta["int"] == 0:
            meta["int"] = val
        elif ttype == "wis" and meta["wis"] == 0:
            meta["wis"] = val
        elif ttype == "cha" and meta["cha"] == 0:
            meta["cha"] = val
        elif ttype == "power" and meta.get("power", 0) == 0:
            meta["power"] = val

    return meta


def ensure_nft_in_postgresql(token_id):
    """
    🔥 AUTO-CREATE: Verifica si un NFT existe en PostgreSQL, si no, lo crea.

    Flujo:
    1. Verificar si existe en PostgreSQL
    2. Si existe → return True
    3. Si no existe → cargar de data/metadata/
    4. Si encontrado en metadata → crear en PostgreSQL con dynamic_state inicial
    5. Return True si se creó exitosamente, False si no se encontró en ningún lado

    Esto permite que el endpoint /api/metadata/<token_id> funcione automáticamente
    sin necesidad de que el usuario conecte su wallet primero.
    """
    if not POSTGRESQL_AVAILABLE:
        return False

    token_id_padded = str(token_id).zfill(5)
    conn = None

    try:
        conn = db.get_connection()
        cur = conn.cursor()

        # 1. Verificar si ya existe en PostgreSQL
        cur.execute("SELECT token_id FROM nfts WHERE token_id = %s", (token_id_padded,))
        existing = cur.fetchone()

        if existing:
            # Ya existe, no hacer nada
            return True

        # 2. Cargar metadata base desde data/metadata/
        base_meta = load_base_metadata_for_token(token_id)
        if base_meta is None:
            # No existe en metadata, no podemos crearlo
            print(f"⚠️ ensure_nft_in_postgresql: Token {token_id_padded} not found in metadata")
            return False

        # 3. Crear dynamic_state inicial
        initial_dynamic_state = {
            "xp_total": 0,
            "xp_level": 1,
            "aura_level": 0,
            "energy_current": 100,
            "energy_max": 100,
            "power_current": 0,
            "last_update": now_utc_str(),
            "last_mission": "None",
            "total_missions_completed": 0,
            "death_count": 0,
            "state": "READY",
            "current_guild": base_meta.get("starting_guild", "Unassigned")
        }

        # 4. Insertar en PostgreSQL
        race_class = f"{base_meta.get('race', 'Unknown')} {base_meta.get('class', 'Unknown')}"

        cur.execute("""
            INSERT INTO nfts (token_id, name, race_class, guild, image_url, dynamic_state, last_synced)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, NOW())
            ON CONFLICT (token_id) DO NOTHING
        """, (
            token_id_padded,
            base_meta.get('name', f"Emissary #{token_id_padded}"),
            race_class,
            base_meta.get('starting_guild', 'Unassigned'),
            base_meta.get('image', ''),
            json.dumps(initial_dynamic_state)
        ))

        conn.commit()
        print(f"✅ Auto-created NFT {token_id_padded} in PostgreSQL via metadata endpoint")
        return True

    except Exception as e:
        print(f"⚠️ ensure_nft_in_postgresql failed for {token_id_padded}: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            db.release_connection(conn)


def ensure_nft_in_postgresql_with_metadata(token_id, base_meta):
    """
    🔥 AUTO-CREATE: Verifica si un NFT existe en PostgreSQL, si no, lo crea.

    Similar a ensure_nft_in_postgresql() pero usa metadata pre-cargada
    (ej: ya obtenida de IPFS mainnet) en vez de cargarla de archivos locales.

    Esto evita duplicar la llamada a IPFS y garantiza que la metadata
    almacenada en PostgreSQL coincida con la de mainnet.
    """
    if not POSTGRESQL_AVAILABLE:
        return False

    if base_meta is None:
        return False

    token_id_padded = str(token_id).zfill(5)
    conn = None

    try:
        conn = db.get_connection()
        cur = conn.cursor()

        # 1. Verificar si ya existe en PostgreSQL
        cur.execute("SELECT token_id FROM nfts WHERE token_id = %s", (token_id_padded,))
        existing = cur.fetchone()

        if existing:
            # Ya existe, no hacer nada
            return True

        # 2. Crear dynamic_state inicial
        initial_dynamic_state = {
            "xp_total": 0,
            "xp_level": 1,
            "aura_level": 0,
            "energy_current": 100,
            "energy_max": 100,
            "power_current": 0,
            "last_update": now_utc_str(),
            "last_mission": "None",
            "total_missions_completed": 0,
            "death_count": 0,
            "state": "READY",
            "current_guild": base_meta.get("starting_guild", "Unassigned")
        }

        # 3. Insertar en PostgreSQL con metadata de IPFS mainnet
        race_class = f"{base_meta.get('race', 'Unknown')} {base_meta.get('class', 'Unknown')}"

        cur.execute("""
            INSERT INTO nfts (token_id, name, race_class, guild, image_url, dynamic_state, last_synced)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, NOW())
            ON CONFLICT (token_id) DO NOTHING
        """, (
            token_id_padded,
            base_meta.get('name', f"Emissary #{token_id_padded}"),
            race_class,
            base_meta.get('starting_guild', 'Unassigned'),
            base_meta.get('image', ''),
            json.dumps(initial_dynamic_state)
        ))

        conn.commit()
        print(f"✅ Auto-created NFT {token_id_padded} in PostgreSQL (from IPFS mainnet metadata)")
        return True

    except Exception as e:
        print(f"⚠️ ensure_nft_in_postgresql_with_metadata failed for {token_id_padded}: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            db.release_connection(conn)


def find_dynamic_state_for_token(token_id):
    """
    Busca el dynamic_state de un token (XP / Aura / Energía / última misión).

    🔥 POSTGRESQL FIRST: Lee de la base de datos PostgreSQL (fuente de verdad).
    Fallback a players.json solo si PostgreSQL no está disponible.
    """
    token_id_padded = str(token_id).zfill(5)

    # 🔥 POSTGRESQL: Fuente de verdad para datos dinámicos
    if POSTGRESQL_AVAILABLE:
        try:
            nfts_db = load_nfts_database()  # Lee de PostgreSQL
            nft = nfts_db.get(token_id_padded)

            if nft and nft.get('dynamic_state'):
                ds = nft['dynamic_state']
                return {
                    "current_guild":   ds.get("current_guild", nft.get("guild", "Unknown")),
                    "xp_total":        ds.get("xp_total", 0),
                    "xp_level":        ds.get("xp_level", 1),
                    "aura_level":      ds.get("aura_level", 0),
                    "energy_current":  ds.get("energy_current", 100),
                    "energy_max":      ds.get("energy_max", 100),
                    "power_current":   ds.get("power_current", 0),
                    "last_update":     ds.get("last_update", now_utc_str()),
                    "last_mission":    ds.get("last_mission", "None"),
                    "total_missions_completed": ds.get("total_missions_completed", 0),
                    "death_count":     ds.get("death_count", 0),
                    "state":           ds.get("state", "READY"),
                }
        except Exception as e:
            print(f"⚠️ PostgreSQL find_dynamic_state failed: {e}, falling back to players.json")

    # 📁 FALLBACK: players.json (si PostgreSQL no está disponible)
    players_all = load_json(PLAYERS_PATH, {})

    for wallet_addr, pobj in players_all.items():
        for hero in pobj.get("heroes", []):
            if hero.get("token_id") == token_id_padded:
                ds = hero.get("dynamic_state", {})
                return {
                    "current_guild":   ds.get("current_guild", hero.get("guild", "Unknown")),
                    "xp_total":        ds.get("xp_total", 0),
                    "xp_level":        ds.get("xp_level", 1),
                    "aura_level":      ds.get("aura_level", 0),
                    "energy_current":  ds.get("energy_current", 100),
                    "energy_max":      ds.get("energy_max", 100),
                    "power_current":   ds.get("power_current", 0),
                    "last_update":     ds.get("last_update", now_utc_str()),
                    "last_mission":    ds.get("last_mission", "None"),
                }

    # 🆕 Token no encontrado - devolver defaults
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
@app.route("/api/metadata/<token_id>.json")
def api_metadata(token_id):
    """
    Endpoint que OpenSea/marketplaces pueden consultar como tokenURI.
    Soporta ambos formatos:
    - /api/metadata/19726
    - /api/metadata/19726.json (para contratos que agregan .json automáticamente)

    🔥 IPFS MAINNET FIRST: Lee metadata base de IPFS mainnet (con caché).
    Esto asegura que los atributos (race, class, etc.) coincidan con los
    que están en el contrato de Base mainnet.

    Combina:
    - metadata fija del héroe desde IPFS mainnet (race, STR, etc.)
    - estado dinámico actual desde PostgreSQL (XP, Aura, Energy, Last Mission)
    y lo devuelve TODO dentro de "attributes".
    """
    # Strip .json suffix if present (in case it comes through the first route)
    if token_id.endswith('.json'):
        token_id = token_id[:-5]

    # 🔥 IPFS MAINNET: Source of truth for base metadata
    base_meta = fetch_ipfs_mainnet_metadata(token_id)

    # Fallback to local files if IPFS fails
    if base_meta is None:
        print(f"⚠️ IPFS mainnet failed for #{token_id}, falling back to local files")
        base_meta = load_base_metadata_for_token(token_id)

    if base_meta is None:
        abort(404, "token metadata not found")

    # 🔥 AUTO-CREATE: Si el NFT no está en PostgreSQL, crearlo con la metadata de IPFS
    # Esto permite que OpenSea/marketplaces obtengan metadata sin que el usuario
    # haya conectado su wallet primero
    ensure_nft_in_postgresql_with_metadata(token_id, base_meta)

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
        {"trait_type": "Power",         "value": base_meta.get("power", 0)},  # 🔥 Static from IPFS, not PostgreSQL
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

    # Convert ipfs:// to HTTP gateway for MetaMask/wallet compatibility
    image_url = base_meta.get("image", "")
    if image_url.startswith("ipfs://"):
        image_url = image_url.replace("ipfs://", "https://ipfs.io/ipfs/")

    response = {
        "name":        base_meta.get("name", f"Emissary #{str(token_id).zfill(5)}"),
        "description": base_meta.get("description", "Emissary of Emberholm."),
        "image":       image_url,
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
        image_url TEXT,
        dynamic_state JSONB NOT NULL DEFAULT '{}'::jsonb,
        last_update TIMESTAMP DEFAULT NOW(),
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_nfts_owner ON nfts(last_known_owner);
    CREATE INDEX IF NOT EXISTS idx_nfts_guild ON nfts(guild);
    CREATE INDEX IF NOT EXISTS idx_nfts_state ON nfts((dynamic_state->>'state'));
    CREATE INDEX IF NOT EXISTS idx_nfts_xp ON nfts(((dynamic_state->>'xp_total')::int));
    CREATE INDEX IF NOT EXISTS idx_nfts_aura ON nfts(((dynamic_state->>'aura_level')::int));

    -- Add image_url column if it doesn't exist (migration for existing tables)
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'nfts' AND column_name = 'image_url') THEN
            ALTER TABLE nfts ADD COLUMN image_url TEXT;
        END IF;
    END $$;

    -- Add equipment columns if they don't exist (migration for equipment system)
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'nfts' AND column_name = 'weapon_id') THEN
            ALTER TABLE nfts ADD COLUMN weapon_id TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'nfts' AND column_name = 'armor_id') THEN
            ALTER TABLE nfts ADD COLUMN armor_id TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'nfts' AND column_name = 'helmet_id') THEN
            ALTER TABLE nfts ADD COLUMN helmet_id TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'nfts' AND column_name = 'accessory_id') THEN
            ALTER TABLE nfts ADD COLUMN accessory_id TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'nfts' AND column_name = 'amulet_id') THEN
            ALTER TABLE nfts ADD COLUMN amulet_id TEXT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'nfts' AND column_name = 'rune_ids') THEN
            ALTER TABLE nfts ADD COLUMN rune_ids TEXT[] DEFAULT ARRAY[]::TEXT[];
        END IF;
    END $$;

    CREATE TABLE IF NOT EXISTS active_missions (
        mission_key VARCHAR(100) PRIMARY KEY,
        wallet VARCHAR(42) NOT NULL,
        hero_id VARCHAR(10),
        hero_ids JSONB,
        mission_id VARCHAR(10) NOT NULL,
        start_time TIMESTAMP NOT NULL,
        duration_hours INTEGER NOT NULL,
        is_party BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    );

    -- Migration: Add missing columns if they don't exist
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'active_missions' AND column_name = 'hero_ids') THEN
            ALTER TABLE active_missions ADD COLUMN hero_ids JSONB;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'active_missions' AND column_name = 'is_party') THEN
            ALTER TABLE active_missions ADD COLUMN is_party BOOLEAN DEFAULT FALSE;
        END IF;
        -- Make hero_id nullable for party missions
        ALTER TABLE active_missions ALTER COLUMN hero_id DROP NOT NULL;
    END $$;

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

    -- ========== PENDING CLAIMS (Items & Runes drops) ==========
    CREATE TABLE IF NOT EXISTS pending_claims (
        id SERIAL PRIMARY KEY,
        wallet_address VARCHAR(42) NOT NULL,
        claim_type VARCHAR(10) NOT NULL,  -- 'RUNE' or 'ITEM'
        claim_id VARCHAR(66) NOT NULL UNIQUE,
        signature TEXT NOT NULL,
        mission_id VARCHAR(10),
        hero_id VARCHAR(10),
        difficulty VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        claimed_at TIMESTAMP,
        token_id INTEGER,
        tx_hash VARCHAR(66),
        status VARCHAR(20) DEFAULT 'pending'  -- 'pending', 'claimed', 'expired'
    );

    CREATE INDEX IF NOT EXISTS idx_pending_claims_wallet ON pending_claims(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_pending_claims_status ON pending_claims(status);
    CREATE INDEX IF NOT EXISTS idx_pending_claims_claim_id ON pending_claims(claim_id);

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
# 🔧 MIGRATION: Equipment Columns
# ---------------------------------

@app.route("/api/migrate/equipment-columns", methods=['GET', 'POST'])
def migrate_equipment_columns():
    """
    🔧 MIGRATION - Add equipment columns to nfts table

    This adds the columns needed for the equipment system:
    - weapon_id, armor_id, helmet_id, accessory_id, amulet_id (TEXT)
    - rune_ids (TEXT[])

    Safe to run multiple times (uses IF NOT EXISTS).
    Access: GET or POST /api/migrate/equipment-columns
    """
    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "error": "PostgreSQL not available"}), 503

    result = {
        "timestamp": now_utc_str(),
        "success": False,
        "columns_added": [],
        "columns_existing": [],
        "error": None
    }

    try:
        conn = db.get_connection()
        if not conn:
            result["error"] = "Could not connect to database"
            return jsonify(result), 500

        columns_to_add = [
            ("weapon_id", "TEXT"),
            ("armor_id", "TEXT"),
            ("helmet_id", "TEXT"),
            ("accessory_id", "TEXT"),
            ("amulet_id", "TEXT"),
            ("rune_ids", "TEXT[] DEFAULT ARRAY[]::TEXT[]")
        ]

        with conn.cursor() as cur:
            for col_name, col_type in columns_to_add:
                # Check if column exists
                cur.execute("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'nfts' AND column_name = %s
                """, (col_name,))

                if cur.fetchone():
                    result["columns_existing"].append(col_name)
                else:
                    # Add the column
                    cur.execute(f"ALTER TABLE nfts ADD COLUMN {col_name} {col_type}")
                    result["columns_added"].append(col_name)

        conn.commit()
        db.release_connection(conn)

        result["success"] = True
        if result["columns_added"]:
            result["message"] = f"✅ Added {len(result['columns_added'])} columns: {', '.join(result['columns_added'])}"
        else:
            result["message"] = "✅ All equipment columns already exist"

        return jsonify(result)

    except Exception as e:
        result["error"] = str(e)
        result["message"] = f"❌ Migration failed: {str(e)}"
        return jsonify(result), 500

# ---------------------------------
# 🔧 ADMIN: Force Equipment Migration
# ---------------------------------

@app.route("/api/admin/migrate-equipment", methods=['GET', 'POST'])
def admin_migrate_equipment():
    """
    🔧 ADMIN - Force equipment columns migration

    This is an admin endpoint to force-add equipment columns.
    Can be called via browser (GET) or programmatically (POST).
    """
    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "error": "PostgreSQL not available"}), 503

    columns_added = []
    columns_existing = []

    try:
        conn = db.get_connection()
        if not conn:
            return jsonify({"success": False, "error": "Could not connect to database"}), 500

        columns = [
            ('weapon_id', 'VARCHAR(50)'),
            ('armor_id', 'VARCHAR(50)'),
            ('helmet_id', 'VARCHAR(50)'),
            ('accessory_id', 'VARCHAR(50)'),
            ('amulet_id', 'VARCHAR(50)'),
            ('rune_ids', 'TEXT[] DEFAULT ARRAY[]::TEXT[]')
        ]

        with conn.cursor() as cur:
            for col_name, col_type in columns:
                # Check if column exists
                cur.execute("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'nfts' AND column_name = %s
                """, (col_name,))

                if cur.fetchone():
                    columns_existing.append(col_name)
                    print(f"  ✓ Column {col_name} already exists")
                else:
                    try:
                        cur.execute(f"ALTER TABLE nfts ADD COLUMN {col_name} {col_type}")
                        columns_added.append(col_name)
                        print(f"  ✅ Added column {col_name}")
                    except Exception as e:
                        print(f"  ⚠️ Error adding {col_name}: {e}")

        conn.commit()
        db.release_connection(conn)

        return jsonify({
            "success": True,
            "message": f"Migration complete. Added: {len(columns_added)}, Existing: {len(columns_existing)}",
            "columns_added": columns_added,
            "columns_existing": columns_existing,
            "all_columns": [c[0] for c in columns]
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------------
# 🔧 ADMIN: Reset EMBER Balances
# ---------------------------------

@app.route("/api/admin/reset-ember-balances", methods=['POST'])
def admin_reset_ember_balances():
    """
    🔧 ADMIN - Reset all EMBER balances to 0

    This resets ember_balance for all users in user_balances table.
    Used for testing or before enabling real token integration.
    """
    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "error": "PostgreSQL not available"}), 503

    try:
        conn = db.get_connection()
        if not conn:
            return jsonify({"success": False, "error": "Could not connect to database"}), 500

        with conn.cursor() as cur:
            # Get current stats before reset
            cur.execute("SELECT COUNT(*), SUM(ember_balance) FROM user_balances WHERE ember_balance > 0")
            before = cur.fetchone()
            users_with_balance = before[0] or 0
            total_ember = before[1] or 0

            # Reset all ember balances to 0
            cur.execute("UPDATE user_balances SET ember_balance = 0, last_update = NOW()")
            rows_updated = cur.rowcount

            conn.commit()

        db.release_connection(conn)

        return jsonify({
            "success": True,
            "message": f"Reset complete. {rows_updated} users updated.",
            "before": {
                "users_with_balance": users_with_balance,
                "total_ember_reset": int(total_ember)
            },
            "after": {
                "all_balances": 0
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

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
        active_missions = load_active_missions()
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

    # 2. Estado en active_missions (PostgreSQL)
    try:
        active_missions = load_active_missions()
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
        # Use the new helper function
        balance_info = db.get_or_create_user_balance(wallet)

        if balance_info is None:
            # Return default on error
            return jsonify({
                "ember_balance": 0,
                "ash_balance": 0,
                "gambit_rolls_today": 0,
                "gambit_rolls_max": 5
            })

        # Check if need to reset gambit rolls
        now = datetime.now(timezone.utc)
        next_reset = balance_info["gambit_next_reset"]
        gambit_rolls = balance_info["gambit_rolls_today"]

        # Handle timezone-aware vs naive datetime comparison
        should_reset = False
        if next_reset:
            try:
                # If next_reset is naive, make it UTC aware
                if next_reset.tzinfo is None:
                    next_reset = next_reset.replace(tzinfo=timezone.utc)
                should_reset = now >= next_reset
            except Exception:
                # Fallback: compare as UTC-aware
                now_utc = datetime.now(timezone.utc)
                if next_reset.tzinfo is None:
                    next_reset = next_reset.replace(tzinfo=timezone.utc)
                should_reset = now_utc >= next_reset

        if should_reset:
            # Reset rolls
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_balances
                    SET gambit_rolls_today = 0,
                        gambit_next_reset = %s,
                        last_update = NOW()
                    WHERE wallet = %s
                """, (now + timedelta(days=1), wallet))
                conn.commit()
                db.release_connection(conn)
                gambit_rolls = 0
            except Exception as e:
                print(f"⚠️ Error resetting gambit rolls: {e}")

        return jsonify({
            "ember_balance": balance_info["ember_balance"],
            "ash_balance": balance_info["ash_balance"] if FEATURES["ASH_PROTOCOL_ENABLED"] else 0,
            "gambit_rolls_today": gambit_rolls,
            "gambit_rolls_max": balance_info["gambit_rolls_max"]
        })

    except Exception as e:
        print(f"❌ Error getting balance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# $EMBER CLAIM API (Gasless Claims)
# ---------------------------------

# Initialize Web3 for Base Mainnet (for $EMBER claims)
ember_w3 = None
ember_contract = None

def init_ember_web3():
    """Initialize Web3 connection for EMBER claims"""
    global ember_w3, ember_contract
    if not Web3Lib:
        print("⚠️ Web3 not available for EMBER claims")
        return False

    try:
        ember_w3 = Web3Lib(Web3Lib.HTTPProvider("https://mainnet.base.org"))
        if ember_w3.is_connected():
            ember_contract = ember_w3.eth.contract(
                address=Web3Lib.to_checksum_address(EMBER_TOKEN_ADDRESS),
                abi=EMBER_TOKEN_ABI
            )
            print("✅ Web3 connected for $EMBER claims (Base Mainnet)")
            return True
        else:
            print("⚠️ Could not connect to Base Mainnet for EMBER claims")
            return False
    except Exception as e:
        print(f"⚠️ Error initializing EMBER Web3: {e}")
        return False

# Try to initialize on startup
init_ember_web3()

@app.route('/api/ember/balance/<wallet>', methods=['GET'])
@rate_limit(requests_per_minute=30)
def get_ember_token_balance(wallet):
    """
    Get detailed $EMBER balance for a wallet.
    Returns: pending (off-chain), on-chain, total_claimed, last_claim
    """
    try:
        wallet_checksum = Web3Lib.to_checksum_address(wallet) if Web3Lib else wallet
        wallet_lower = wallet.lower()

        # Default response
        response = {
            "pending": 0,
            "onchain": 0,
            "total_claimed": 0,
            "last_claim": None
        }

        # Get pending balance from database
        if POSTGRESQL_AVAILABLE and db:
            try:
                conn = db.get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT ember_balance, COALESCE(total_ember_claimed, 0) as total_claimed,
                           last_ember_claim_at
                    FROM user_balances
                    WHERE wallet = %s
                """, (wallet_lower,))

                result = cursor.fetchone()
                db.release_connection(conn)

                if result:
                    response["pending"] = float(result[0]) if result[0] else 0
                    response["total_claimed"] = float(result[1]) if result[1] else 0
                    response["last_claim"] = result[2].isoformat() if result[2] else None

            except Exception as e:
                print(f"⚠️ Error getting pending EMBER balance: {e}")

        # Get on-chain balance
        if ember_w3 and ember_contract:
            try:
                onchain_balance_wei = ember_contract.functions.balanceOf(wallet_checksum).call()
                response["onchain"] = float(Web3Lib.from_wei(onchain_balance_wei, 'ether'))
            except Exception as e:
                print(f"⚠️ Error getting on-chain EMBER balance: {e}")

        return jsonify(response)

    except Exception as e:
        print(f"❌ Error in get_ember_token_balance: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ember/claim', methods=['POST'])
@rate_limit(requests_per_minute=5)
def claim_ember_tokens():
    """
    Claim pending $EMBER tokens (gasless - paid by claimer wallet).
    The backend sends the transaction using the claimer wallet.
    """
    try:
        data = request.get_json()
        wallet = data.get('wallet')

        if not wallet:
            return jsonify({"error": "Wallet address required"}), 400

        # Validate claimer configuration
        if not CLAIMER_PRIVATE_KEY or not CLAIMER_WALLET_ADDRESS:
            return jsonify({"error": "Claimer wallet not configured"}), 503

        if not ember_w3 or not ember_contract:
            # Try to reinitialize
            if not init_ember_web3():
                return jsonify({"error": "Blockchain connection not available"}), 503

        wallet_checksum = Web3Lib.to_checksum_address(wallet)
        wallet_lower = wallet.lower()

        # 1. Get pending balance from database
        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ember_balance FROM user_balances
            WHERE wallet = %s
        """, (wallet_lower,))

        result = cursor.fetchone()

        if not result or result[0] <= 0:
            db.release_connection(conn)
            return jsonify({"error": "No EMBER balance to claim", "balance": 0}), 400

        pending_balance = float(result[0])

        # 2. Convert to wei (18 decimals)
        amount_wei = ember_w3.to_wei(pending_balance, 'ether')

        # 3. Check rewards pool has enough
        try:
            rewards_remaining = ember_contract.functions.rewardsRemaining().call()
            if amount_wei > rewards_remaining:
                db.release_connection(conn)
                return jsonify({"error": "Insufficient rewards in pool"}), 500
        except Exception as e:
            print(f"⚠️ Could not check rewards pool: {e}")
            # Continue anyway - let the transaction fail if pool is empty

        # 4. Build transaction
        claimer_address = Web3Lib.to_checksum_address(CLAIMER_WALLET_ADDRESS)
        nonce = ember_w3.eth.get_transaction_count(claimer_address)

        txn = ember_contract.functions.claimTransfer(
            wallet_checksum,
            amount_wei
        ).build_transaction({
            'chainId': CHAIN_ID,  # Base Mainnet (8453)
            'gas': 100000,
            'gasPrice': ember_w3.eth.gas_price,
            'nonce': nonce,
        })

        # 5. Sign and send transaction
        signed_txn = ember_w3.eth.account.sign_transaction(txn, CLAIMER_PRIVATE_KEY)
        tx_hash = ember_w3.eth.send_raw_transaction(signed_txn.raw_transaction)

        # 6. Wait for confirmation (with timeout)
        receipt = ember_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt['status'] == 1:
            # 7. Update database - reset pending balance, increment total claimed
            cursor.execute("""
                UPDATE user_balances
                SET ember_balance = 0,
                    total_ember_claimed = COALESCE(total_ember_claimed, 0) + %s,
                    last_ember_claim_at = NOW()
                WHERE wallet = %s
            """, (pending_balance, wallet_lower))

            conn.commit()
            db.release_connection(conn)

            print(f"✅ EMBER claimed: {pending_balance} to {wallet[:10]}... TX: {tx_hash.hex()}")

            return jsonify({
                "success": True,
                "amount": pending_balance,
                "tx_hash": tx_hash.hex(),
                "message": f"Successfully claimed {pending_balance} $EMBER"
            })
        else:
            db.release_connection(conn)
            return jsonify({"error": "Transaction failed on-chain"}), 500

    except Exception as e:
        print(f"❌ Error in claim_ember_tokens: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/ember/rewards-pool', methods=['GET'])
def get_ember_rewards_pool():
    """Get remaining $EMBER in the rewards pool"""
    try:
        if not ember_w3 or not ember_contract:
            if not init_ember_web3():
                return jsonify({"error": "Blockchain not available", "remaining": 0}), 503

        rewards_remaining_wei = ember_contract.functions.rewardsRemaining().call()
        rewards_remaining = float(Web3Lib.from_wei(rewards_remaining_wei, 'ether'))

        return jsonify({
            "remaining": rewards_remaining,
            "contract": EMBER_TOKEN_ADDRESS
        })
    except Exception as e:
        print(f"❌ Error getting rewards pool: {e}")
        return jsonify({"error": str(e), "remaining": 0}), 500

# ---------------------------------
# VAULT API
# ---------------------------------

@app.route('/api/vault', methods=['GET'])
@rate_limit(requests_per_minute=20)
def get_vault():
    """
    Get vault items.
    Items now come from blockchain, not database.
    This endpoint returns empty array - frontend loads from blockchain.
    """
    wallet = request.args.get('wallet', '').lower()

    if not wallet:
        return jsonify({"error": "Wallet address required"}), 400

    # Items are loaded from blockchain on frontend
    # This endpoint is kept for backwards compatibility
    return jsonify({"items": []})

@app.route('/api/vault/add-item', methods=['POST'])
def add_item_to_vault():
    """
    Manually add an item to a wallet's vault.
    Useful for recovering items that were claimed on-chain but not recorded in the database.

    POST: { "wallet": "0x...", "type": "weapon/armor/rune/etc", "rarity": "common/rare/epic/legendary" }
    """
    data = request.get_json()
    wallet = data.get('wallet', '').lower()
    item_type = data.get('type', 'weapon')
    rarity = data.get('rarity', 'common')

    if not wallet:
        return jsonify({"error": "wallet required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"error": "Database not available"}), 503

    try:
        # Generate item
        claim_type = "RUNE" if item_type == "rune" else "ITEM"
        item_data = generate_random_item(claim_type, "HARD", wallet)

        # Override rarity if specified
        if rarity in ["common", "rare", "epic", "legendary"]:
            item_data["rarity"] = rarity
            # Recalculate stats based on rarity
            rarity_multipliers = {"common": 1, "rare": 2, "epic": 4, "legendary": 8}
            multiplier = rarity_multipliers.get(rarity, 1)
            if claim_type == "RUNE":
                item_data["stats"] = {"all_boost": 5 * multiplier}
            else:
                # Get base stats for type
                base = ITEM_TEMPLATES.get(item_type, {}).get("base_stats", {"attack": 10})
                item_data["stats"] = {k: v * multiplier for k, v in base.items()}

        # Override type if item (not rune)
        if claim_type == "ITEM" and item_type in ITEM_TEMPLATES:
            item_data["type"] = item_type
            names = ITEM_TEMPLATES[item_type]["names"].get(rarity, ITEM_TEMPLATES[item_type]["names"]["common"])
            import random
            item_data["name"] = random.choice(names)
            item_data["image_url"] = f"/img/items/{item_type}_{rarity}.png"

        item_id = insert_item_to_vault(item_data)

        if item_id:
            return jsonify({
                "success": True,
                "message": f"Item added to vault",
                "item": {
                    "id": item_id,
                    "name": item_data["name"],
                    "type": item_data["type"],
                    "rarity": item_data["rarity"],
                    "stats": item_data["stats"]
                }
            })
        else:
            return jsonify({"error": "Failed to insert item"}), 500

    except Exception as e:
        print(f"Error adding item to vault: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# EQUIPMENT API (Legacy - Deprecated)
# ---------------------------------

@app.route('/api/equip', methods=['POST'])
def equip_item():
    """DEPRECATED: Use /api/equipment/equip instead"""
    return jsonify({"error": "Use /api/equipment/equip instead"}), 410

@app.route('/api/unequip', methods=['POST'])
def unequip_item():
    """DEPRECATED: Use /api/equipment/unequip instead"""
    return jsonify({"error": "Use /api/equipment/unequip instead"}), 410

# ---------------------------------
# EQUIPMENT API (Routes used by inventory modal)
# ---------------------------------

@app.route('/api/equipment/<emissary_id>', methods=['GET'])
def get_emissary_equipment(emissary_id):
    """
    Get equipment slots for an emissary.
    Returns: weapon_id, armor_id, helmet_id, accessory_id, amulet_id, rune_ids
    """
    if not POSTGRESQL_AVAILABLE:
        return jsonify({"error": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT token_id, name, weapon_id, armor_id, helmet_id,
                   accessory_id, amulet_id, rune_ids,
                   dynamic_state->>'state' as state
            FROM nfts WHERE token_id = %s
        """, (emissary_id,))

        row = cursor.fetchone()
        db.release_connection(conn)

        if not row:
            return jsonify({"error": "Emissary not found"}), 404

        return jsonify({
            "token_id": row['token_id'],
            "name": row['name'],
            "state": row['state'] or 'READY',
            "equipment": {
                "weapon_id": row['weapon_id'],
                "armor_id": row['armor_id'],
                "helmet_id": row['helmet_id'],
                "accessory_id": row['accessory_id'],
                "amulet_id": row['amulet_id'],
                "rune_ids": row['rune_ids'] or []
            }
        })

    except Exception as e:
        print(f"Error getting equipment: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/equipment/equipped-items', methods=['GET'])
def get_equipped_items():
    """
    Get all equipped items for a wallet.
    Returns a mapping of item_id -> emissary_id for quick lookup.
    """
    wallet = request.args.get('wallet', '').lower()

    if not wallet:
        return jsonify({"error": "wallet required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"error": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get all emissaries with their equipment
        cursor.execute("""
            SELECT token_id, name, weapon_id, armor_id, helmet_id,
                   accessory_id, amulet_id, rune_ids
            FROM nfts
            WHERE last_known_owner = %s
        """, (wallet,))

        rows = cursor.fetchall()
        db.release_connection(conn)

        # Build a map of item_id -> {emissary_id, emissary_name, slot}
        equipped_map = {}

        for row in rows:
            emissary_id = row['token_id']
            emissary_name = row['name'] or f"#{emissary_id}"

            # Check each slot
            slots = ['weapon_id', 'armor_id', 'helmet_id', 'accessory_id', 'amulet_id']
            for slot in slots:
                item_id = row.get(slot)
                if item_id:
                    equipped_map[item_id] = {
                        "emissary_id": emissary_id,
                        "emissary_name": emissary_name,
                        "slot": slot.replace('_id', '')
                    }

            # Check runes
            rune_ids = row.get('rune_ids') or []
            for i, rune_id in enumerate(rune_ids):
                if rune_id:
                    equipped_map[rune_id] = {
                        "emissary_id": emissary_id,
                        "emissary_name": emissary_name,
                        "slot": f"rune_{i+1}"
                    }

        return jsonify({
            "equipped": equipped_map,
            "total_equipped": len(equipped_map)
        })

    except Exception as e:
        print(f"Error getting equipped items: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/equipment/equip', methods=['POST'])
@rate_limit(requests_per_minute=20)
def equipment_equip():
    """
    Equip an item/rune to an emissary.
    Items come from blockchain, we just store the item_id in the nfts table.
    """
    data = request.get_json()
    wallet = data.get('wallet', '').lower()
    emissary_id = data.get('emissary_id')
    item_id = data.get('item_id')  # e.g. "item-1" or "rune-2" (string, not int)
    item_type = data.get('item_type')  # weapon, armor, helmet, accessory, amulet, or rune
    slot = data.get('slot')  # Alternative to item_type
    token_id = data.get('token_id')  # blockchain token ID

    # Convert item_id to string if it came as int
    if item_id is not None:
        item_id = str(item_id)

    if not wallet or not emissary_id or not item_id:
        return jsonify({"error": "wallet, emissary_id and item_id required"}), 400

    # Use slot if item_type not provided
    if not item_type and slot:
        item_type = slot

    if not item_type:
        return jsonify({"error": "item_type required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"success": False, "error": "Database not available"}), 503

    # 🔒 Use locked version when enabled
    if USE_EQUIPMENT_LOCKS:
        logger.debug(f"Using locked transaction for equip: {emissary_id}, {item_type}")
        response, status_code = equip_item_with_lock(wallet, emissary_id, item_id, item_type)
        return jsonify(response), status_code

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Verify emissary belongs to wallet AND check state
        cursor.execute("""
            SELECT token_id, dynamic_state->>'state' as state
            FROM nfts WHERE token_id = %s AND last_known_owner = %s
        """, (emissary_id, wallet))
        row = cursor.fetchone()

        if not row:
            db.release_connection(conn)
            return jsonify({"error": "Emissary not found or doesn't belong to you"}), 404

        # Block equipment changes if emissary is on mission
        emissary_state = row[1] if row[1] else 'READY'
        if emissary_state == 'ON_MISSION':
            db.release_connection(conn)
            return jsonify({"error": "Cannot change equipment while emissary is on a mission"}), 400

        # Handle runes specially (can have up to 2)
        if item_type == "rune":
            # First check current rune count
            cursor.execute("""
                SELECT COALESCE(array_length(rune_ids, 1), 0) as rune_count
                FROM nfts WHERE token_id = %s
            """, (emissary_id,))
            row = cursor.fetchone()
            rune_count = row[0] if row else 0

            if rune_count >= 2:
                db.release_connection(conn)
                return jsonify({"error": "Cannot equip more than 2 runes"}), 400

            # Check if this rune is already equipped
            cursor.execute("""
                SELECT %s = ANY(COALESCE(rune_ids, ARRAY[]::TEXT[])) as already_equipped
                FROM nfts WHERE token_id = %s
            """, (item_id, emissary_id))
            if cursor.fetchone()[0]:
                db.release_connection(conn)
                return jsonify({"error": "This rune is already equipped"}), 400

            # Add rune to array
            cursor.execute("""
                UPDATE nfts
                SET rune_ids = array_append(COALESCE(rune_ids, ARRAY[]::TEXT[]), %s)
                WHERE token_id = %s
            """, (item_id, emissary_id))
        else:
            column_map = {
                "weapon": "weapon_id",
                "armor": "armor_id",
                "helmet": "helmet_id",
                "accessory": "accessory_id",
                "amulet": "amulet_id"
            }
            column = column_map.get(item_type)
            if not column:
                db.release_connection(conn)
                return jsonify({"error": f"Invalid item type: {item_type}"}), 400

            # Equip new item (replaces existing)
            cursor.execute(f"UPDATE nfts SET {column} = %s WHERE token_id = %s", (item_id, emissary_id))

        conn.commit()
        db.release_connection(conn)

        # Invalidate equipment bonuses cache for this emissary
        db.invalidate_equipment_cache(emissary_id)
        logger.info(f"Equipment equipped: emissary={emissary_id}, type={item_type}, item={item_id}")

        return jsonify({
            "success": True,
            "message": f"{item_type.capitalize()} equipped successfully"
        })

    except Exception as e:
        print(f"Error equipping item: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/equipment/unequip', methods=['POST'])
@rate_limit(requests_per_minute=20)
def equipment_unequip():
    """
    Unequip a single item/rune from an emissary.
    Items are on blockchain, we just clear the reference in nfts table.
    """
    data = request.get_json()
    wallet = data.get('wallet', '').lower()
    emissary_id = data.get('emissary_id')
    item_id = data.get('item_id')  # e.g. "item-1" or "rune-2"
    item_type = data.get('item_type')  # weapon, armor, helmet, accessory, amulet, or rune
    slot = data.get('slot')  # Alternative to item_type

    if not wallet or not emissary_id:
        return jsonify({"error": "wallet and emissary_id required"}), 400

    # Use slot if item_type not provided
    if not item_type and slot:
        item_type = slot

    if not item_type and not item_id:
        return jsonify({"error": "item_type or item_id required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"error": "Database not available"}), 503

    # 🔒 Use locked version when enabled
    if USE_EQUIPMENT_LOCKS:
        logger.debug(f"Using locked transaction for unequip: {emissary_id}, {item_type}")
        response, status_code = unequip_item_with_lock(wallet, emissary_id, item_type, item_id)
        return jsonify(response), status_code

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Verify emissary belongs to wallet AND check state
        cursor.execute("""
            SELECT token_id, dynamic_state->>'state' as state
            FROM nfts WHERE token_id = %s AND last_known_owner = %s
        """, (emissary_id, wallet))
        row = cursor.fetchone()

        if not row:
            db.release_connection(conn)
            return jsonify({"error": "Emissary not found or doesn't belong to you"}), 404

        # Block equipment changes if emissary is on mission
        emissary_state = row[1] if row[1] else 'READY'
        if emissary_state == 'ON_MISSION':
            db.release_connection(conn)
            return jsonify({"error": "Cannot change equipment while emissary is on a mission"}), 400

        # Handle runes (remove from array)
        if item_type == "rune" and item_id:
            cursor.execute("""
                UPDATE nfts SET rune_ids = array_remove(rune_ids, %s) WHERE token_id = %s
            """, (item_id, emissary_id))
        elif item_type:
            # Clear the equipment slot
            column_map = {
                "weapon": "weapon_id",
                "armor": "armor_id",
                "helmet": "helmet_id",
                "accessory": "accessory_id",
                "amulet": "amulet_id"
            }
            column = column_map.get(item_type)
            if column:
                cursor.execute(f"UPDATE nfts SET {column} = NULL WHERE token_id = %s", (emissary_id,))

        conn.commit()
        db.release_connection(conn)

        # Invalidate equipment bonuses cache for this emissary
        db.invalidate_equipment_cache(emissary_id)
        logger.info(f"Equipment unequipped: emissary={emissary_id}, type={item_type}")

        return jsonify({"success": True, "message": "Item unequipped"})

    except Exception as e:
        print(f"Error unequipping item: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/equipment/unequip-all', methods=['POST'])
@rate_limit(requests_per_minute=10)
def equipment_unequip_all():
    """Unequip all items from an emissary"""
    data = request.get_json()
    wallet = data.get('wallet', '').lower()
    emissary_id = data.get('emissary_id')

    if not wallet or not emissary_id:
        return jsonify({"error": "wallet and emissary_id required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"error": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Clear all equipment slots on emissary
        cursor.execute("""
            UPDATE nfts
            SET weapon_id = NULL, armor_id = NULL, helmet_id = NULL,
                accessory_id = NULL, amulet_id = NULL, rune_ids = ARRAY[]::TEXT[]
            WHERE token_id = %s AND last_known_owner = %s
        """, (emissary_id, wallet))

        conn.commit()
        db.release_connection(conn)

        # Invalidate equipment bonuses cache for this emissary
        db.invalidate_equipment_cache(emissary_id)
        logger.info(f"All equipment unequipped: emissary={emissary_id}")

        return jsonify({"success": True, "message": "All items unequipped"})

    except Exception as e:
        print(f"Error unequipping all items: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/equipment/inventory/<emissary_id>', methods=['GET'])
def get_emissary_inventory(emissary_id):
    """
    Get equipped item IDs for an emissary.
    Items details come from blockchain/vaultItems on frontend.
    """
    wallet = request.args.get('wallet', '').lower()

    if not wallet:
        return jsonify({"error": "wallet required"}), 400

    if not POSTGRESQL_AVAILABLE:
        return jsonify({"error": "Database not available"}), 503

    try:
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get emissary equipment slots
        cursor.execute("""
            SELECT token_id, name, weapon_id, armor_id, helmet_id,
                   accessory_id, amulet_id, rune_ids
            FROM nfts
            WHERE token_id = %s AND last_known_owner = %s
        """, (emissary_id, wallet))

        emissary = cursor.fetchone()
        db.release_connection(conn)

        if not emissary:
            return jsonify({"error": "Emissary not found"}), 404

        # Return just the item IDs - frontend matches with vaultItems
        return jsonify({
            "emissary_id": emissary_id,
            "emissary_name": emissary.get('name'),
            "equipped": {
                "weapon": emissary.get('weapon_id'),
                "armor": emissary.get('armor_id'),
                "helmet": emissary.get('helmet_id'),
                "accessory": emissary.get('accessory_id'),
                "amulet": emissary.get('amulet_id')
            },
            "rune_ids": emissary.get('rune_ids') or []
        })

    except Exception as e:
        print(f"Error getting inventory: {e}")
        import traceback
        traceback.print_exc()
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

        # Ensure start_time is timezone-aware before arithmetic
        if start_time and start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

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
# ============================================================================
# EMBER ROLL SYSTEM - Sistema Simple de D20
# ============================================================================
# - 5 rolls máximo por día
# - Primer roll GRATIS, resto 75 $EMBER
# - Reset diario automático
# - Buffs guardados en hero.dynamic_state.ember_roll_buff
# ============================================================================

# Tabla de recompensas D20 (simplificada)
EMBER_ROLL_REWARDS = {
    1:  {"name": "CRITICAL FAIL", "ember": -100, "success": -20, "xp": -10, "energy": 0, "hours": 24},
    2:  {"name": "NOTHING", "ember": 0, "success": 0, "xp": 0, "energy": 0, "hours": 0},
    3:  {"name": "NOTHING", "ember": 0, "success": 0, "xp": 0, "energy": 0, "hours": 0},
    4:  {"name": "NOTHING", "ember": 0, "success": 0, "xp": 0, "energy": 0, "hours": 0},
    5:  {"name": "NOTHING", "ember": 0, "success": 0, "xp": 0, "energy": 0, "hours": 0},
    6:  {"name": "GRAZE", "ember": 50, "success": 5, "xp": 0, "energy": 0, "hours": 12},
    7:  {"name": "GRAZE", "ember": 50, "success": 5, "xp": 0, "energy": 0, "hours": 12},
    8:  {"name": "GRAZE", "ember": 50, "success": 5, "xp": 0, "energy": 0, "hours": 12},
    9:  {"name": "HIT", "ember": 100, "success": 10, "xp": 5, "energy": 0, "hours": 24},
    10: {"name": "HIT", "ember": 100, "success": 10, "xp": 5, "energy": 0, "hours": 24},
    11: {"name": "HIT", "ember": 100, "success": 10, "xp": 5, "energy": 0, "hours": 24},
    12: {"name": "SOLID HIT", "ember": 200, "success": 15, "xp": 10, "energy": 0, "hours": 24},
    13: {"name": "SOLID HIT", "ember": 200, "success": 15, "xp": 10, "energy": 0, "hours": 24},
    14: {"name": "SOLID HIT", "ember": 200, "success": 15, "xp": 10, "energy": 0, "hours": 24},
    15: {"name": "GREAT HIT", "ember": 350, "success": 20, "xp": 15, "energy": 0, "hours": 24},
    16: {"name": "GREAT HIT", "ember": 350, "success": 20, "xp": 15, "energy": 0, "hours": 24},
    17: {"name": "GREAT HIT", "ember": 350, "success": 20, "xp": 15, "energy": 0, "hours": 24},
    18: {"name": "CRITICAL", "ember": 500, "success": 25, "xp": 20, "energy": 10, "hours": 48},
    19: {"name": "SUPERIOR", "ember": 500, "success": 30, "xp": 25, "energy": 15, "hours": 48},
    20: {"name": "NATURAL 20", "ember": 1000, "success": 35, "xp": 30, "energy": 25, "hours": 72}
}

# ---------------------------------
# EMBER ROLL API
# ---------------------------------

@app.route('/api/ember-roll/status', methods=['GET'])
def ember_roll_status():
    """Get EMBER ROLL status for today"""
    wallet = request.args.get('wallet', '').lower()

    if not wallet:
        return jsonify({"error": "Wallet required"}), 400

    try:
        balance = db.get_or_create_user_balance(wallet)
        if not balance:
            return jsonify({"rolls_used": 0, "rolls_max": 5, "rolls_remaining": 5})

        rolls_used = balance["gambit_rolls_today"]
        rolls_max = balance["gambit_rolls_max"]
        next_reset = balance["gambit_next_reset"]

        # Check if reset needed (handle timezone-aware vs naive)
        now = datetime.now(timezone.utc)
        if next_reset:
            try:
                if next_reset.tzinfo is None:
                    next_reset = next_reset.replace(tzinfo=timezone.utc)
                if now >= next_reset:
                    rolls_used = 0
            except Exception:
                pass  # Keep current rolls_used if comparison fails

        return jsonify({
            "rolls_used": rolls_used,
            "rolls_max": rolls_max,
            "rolls_remaining": rolls_max - rolls_used
        })

    except Exception as e:
        print(f"❌ Error getting EMBER ROLL status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ember-roll/perform', methods=['POST'])
def ember_roll_perform():
    """Perform an EMBER ROLL"""
    data = request.get_json()
    wallet = data.get('wallet', '').lower()
    emissary_id = data.get('emissary_id')

    if not wallet or not emissary_id:
        return jsonify({"error": "Wallet and emissary_id required"}), 400

    conn = None
    try:
        # Get status
        balance = db.get_or_create_user_balance(wallet)
        if not balance:
            return jsonify({"error": "User not found"}), 404

        rolls_used = balance["gambit_rolls_today"]
        rolls_max = balance["gambit_rolls_max"]

        if rolls_used >= rolls_max:
            return jsonify({"error": "No rolls remaining today"}), 400

        # Calculate cost (first roll free)
        cost = 0 if rolls_used == 0 else 75

        # Check balance
        current_balance = balance["ember_balance"]
        if current_balance < cost:
            return jsonify({"error": f"Insufficient EMBER (need {cost}, have {current_balance})"}), 400

        # Start transaction
        conn = db.get_connection()
        cursor = conn.cursor()

        # Deduct cost and increment counter
        cursor.execute("""
            UPDATE user_balances
            SET ember_balance = ember_balance - %s,
                gambit_rolls_today = gambit_rolls_today + 1
            WHERE wallet = %s
        """, (cost, wallet))

        # Roll D20
        roll = random.randint(1, 20)
        reward = EMBER_ROLL_REWARDS[roll]

        # Apply EMBER change
        cursor.execute("""
            UPDATE user_balances
            SET ember_balance = ember_balance + %s
            WHERE wallet = %s
            RETURNING ember_balance
        """, (reward["ember"], wallet))

        new_balance = cursor.fetchone()[0]
        conn.commit()

        # Save buff to emissary
        buff_saved = False
        if reward["hours"] > 0:
            try:
                player, _ = load_or_init_player(wallet)
                for hero in player.get("heroes", []):
                    if str(hero.get("token_id")) == str(emissary_id):
                        ds = hero.setdefault("dynamic_state", {})
                        expires = datetime.now(timezone.utc) + timedelta(hours=reward["hours"])

                        ds["ember_roll_buff"] = {
                            "roll": roll,
                            "name": reward["name"],
                            "success_bonus": reward["success"],
                            "xp_bonus": reward["xp"],
                            "energy_reduction": reward["energy"],
                            "expires_at": expires.isoformat()
                        }

                        save_player(wallet, player)
                        buff_saved = True
                        print(f"✅ Buff saved to emissary {emissary_id}")
                        break
            except Exception as e:
                print(f"⚠️ Failed to save buff: {e}")

        # Return result
        return jsonify({
            "success": True,
            "roll": roll,
            "name": reward["name"],
            "ember_change": reward["ember"],
            "new_balance": new_balance,
            "cost_paid": cost,
            "rolls_used": rolls_used + 1,
            "rolls_max": rolls_max,
            "buff": {
                "success_bonus": reward["success"],
                "xp_bonus": reward["xp"],
                "energy_reduction": reward["energy"],
                "duration_hours": reward["hours"],
                "saved": buff_saved
            }
        })

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error performing EMBER ROLL: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            db.release_connection(conn)


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
# 🔒 DATABASE LOCK HELPERS (Prevent Race Conditions)
# ---------------------------------

class LockAcquisitionError(Exception):
    """Raised when a database lock cannot be acquired"""
    pass


def acquire_hero_lock(cursor, hero_id, wallet):
    """
    Acquire an exclusive lock on a hero record using SELECT ... FOR UPDATE NOWAIT.

    Args:
        cursor: Database cursor (must be within a transaction)
        hero_id: The hero token_id to lock
        wallet: The wallet address (for ownership verification)

    Returns:
        dict: The hero record with dynamic_state

    Raises:
        LockAcquisitionError: If the lock cannot be acquired (hero is being processed)
    """
    try:
        cursor.execute("""
            SELECT token_id, dynamic_state, weapon_id, armor_id,
                   helmet_id, accessory_id, amulet_id, rune_ids, last_known_owner
            FROM nfts
            WHERE token_id = %s AND LOWER(last_known_owner) = %s
            FOR UPDATE NOWAIT
        """, (str(hero_id).zfill(5), wallet.lower()))

        hero = cursor.fetchone()
        if not hero:
            raise LockAcquisitionError(f"Hero {hero_id} not found or not owned by wallet")

        logger.debug(f"Lock acquired on hero {hero_id} for wallet {wallet[:10]}...")
        return hero

    except Exception as e:
        error_str = str(e).lower()
        if 'could not obtain lock' in error_str or 'nowait' in error_str or 'lock' in error_str:
            logger.warning(f"Lock conflict on hero {hero_id}: {e}")
            raise LockAcquisitionError(f"Hero {hero_id} is being processed by another request")
        raise


def acquire_mission_lock(cursor, hero_id, wallet):
    """
    Acquire an exclusive lock on an active mission record.

    Args:
        cursor: Database cursor (must be within a transaction)
        hero_id: The hero token_id
        wallet: The wallet address

    Returns:
        dict: The mission record if found, None if no active mission

    Raises:
        LockAcquisitionError: If the lock cannot be acquired
    """
    try:
        cursor.execute("""
            SELECT mission_key, wallet, hero_id, mission_id,
                   start_time, duration_hours, is_party, hero_ids
            FROM active_missions
            WHERE hero_id = %s AND LOWER(wallet) = %s
            FOR UPDATE NOWAIT
        """, (str(hero_id).zfill(5), wallet.lower()))

        mission = cursor.fetchone()
        if mission:
            logger.debug(f"Lock acquired on mission for hero {hero_id}")
        return mission

    except Exception as e:
        error_str = str(e).lower()
        if 'could not obtain lock' in error_str or 'nowait' in error_str or 'lock' in error_str:
            logger.warning(f"Lock conflict on mission for hero {hero_id}: {e}")
            raise LockAcquisitionError(f"Mission for hero {hero_id} is being processed")
        raise


def acquire_claim_lock(cursor, claim_id):
    """
    Acquire an exclusive lock on a pending claim record.

    Args:
        cursor: Database cursor (must be within a transaction)
        claim_id: The unique claim identifier

    Returns:
        dict: The claim record if found

    Raises:
        LockAcquisitionError: If the lock cannot be acquired or claim not found
    """
    try:
        cursor.execute("""
            SELECT id, wallet_address, claim_type, claim_id, signature,
                   mission_id, hero_id, difficulty, status, created_at
            FROM pending_claims
            WHERE claim_id = %s AND status = 'pending'
            FOR UPDATE NOWAIT
        """, (claim_id,))

        claim = cursor.fetchone()
        if not claim:
            raise LockAcquisitionError(f"Claim {claim_id} not found or already claimed")

        logger.debug(f"Lock acquired on claim {claim_id}")
        return claim

    except Exception as e:
        error_str = str(e).lower()
        if 'could not obtain lock' in error_str or 'nowait' in error_str or 'lock' in error_str:
            logger.warning(f"Lock conflict on claim {claim_id}: {e}")
            raise LockAcquisitionError(f"Claim {claim_id} is being processed")
        raise


def complete_mission_with_lock(wallet, hero_id):
    """
    Complete a solo mission with database locks to prevent race conditions.

    This function acquires exclusive locks on both the hero and the active mission,
    then processes the mission completion atomically.

    Args:
        wallet: The wallet address
        hero_id: The hero token_id

    Returns:
        tuple: (response_dict, http_status_code)
    """
    wallet = wallet.lower()
    hero_id_padded = str(hero_id).zfill(5)

    if not POSTGRESQL_AVAILABLE:
        return {'error': 'Database not available'}, 503

    try:
        with db.get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Step 1: Acquire lock on hero
                try:
                    hero_row = acquire_hero_lock(cur, hero_id_padded, wallet)
                except LockAcquisitionError as e:
                    return {'error': str(e), 'retry': True}, 409

                ds = hero_row.get('dynamic_state') or {}

                # Step 2: Verify hero is on mission
                if ds.get('state') != 'ON_MISSION':
                    return {'error': f"Hero is not on a mission (state: {ds.get('state')})"}, 400

                mission_id = ds.get('current_mission_id')
                if not mission_id:
                    return {'error': 'No active mission found'}, 400

                # Step 3: Acquire lock on active mission
                try:
                    mission_row = acquire_mission_lock(cur, hero_id_padded, wallet)
                except LockAcquisitionError as e:
                    return {'error': str(e), 'retry': True}, 409

                if not mission_row:
                    return {'error': 'Active mission not found in database'}, 404

                # Step 4: Check mission duration
                start_time = mission_row.get('start_time')
                duration_hours = mission_row.get('duration_hours', 1)

                if start_time:
                    # Calculate time elapsed
                    now = datetime.now(timezone.utc)
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    elif start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)

                    elapsed_hours = (now - start_time).total_seconds() / 3600

                    if elapsed_hours < duration_hours:
                        remaining = duration_hours - elapsed_hours
                        return {'error': f'Mission not complete. {remaining:.1f} hours remaining'}, 400

                # Step 5: Find mission config
                mission_config = None
                for m in MISSIONS:
                    if m['id'] == mission_id:
                        mission_config = m
                        break
                if not mission_config:
                    for e in EVENTS:
                        if e['id'] == mission_id:
                            mission_config = e
                            break

                if not mission_config:
                    return {'error': f'Mission config not found for {mission_id}'}, 400

                # Step 6: Get equipment bonuses (from cache)
                equipment_bonuses = get_emissary_bonuses(hero_id_padded)

                # Step 7: Roll outcome
                death_protection = equipment_bonuses.get('death', 0)
                outcome, details = roll_mission_outcome_simple(ds, mission_config, death_protection)

                # Step 8: Process outcome and update hero state
                xp_gained = 0
                aura_gained = 0
                xp_lost = 0

                if outcome == 'SUCCESS':
                    xp_gained = details.get('xp_gain', 0)
                    aura_gained = details.get('aura_gain', 0)

                    # Apply equipment bonuses
                    xp_bonus = equipment_bonuses.get('xp', 0)
                    ember_bonus = equipment_bonuses.get('ember', 0)

                    if xp_bonus > 0:
                        xp_gained = int(xp_gained * (100 + xp_bonus) / 100)
                    if ember_bonus > 0:
                        aura_gained = int(aura_gained * (100 + ember_bonus) / 100)

                    ds['xp_total'] = ds.get('xp_total', 0) + xp_gained
                    ds['aura_level'] = ds.get('aura_level', 0) + aura_gained
                    ds['state'] = 'READY'
                    ds['total_missions_completed'] = ds.get('total_missions_completed', 0) + 1

                elif outcome == 'FAILURE':
                    xp_lost = details.get('xp_loss', 0)
                    ds['xp_total'] = max(0, ds.get('xp_total', 0) - xp_lost)
                    ds['state'] = 'READY'

                elif outcome == 'DEATH':
                    ds['state'] = 'FALLEN'
                    ds['fallen_time'] = now_utc_str()
                    ds['death_count'] = ds.get('death_count', 0) + 1

                # Common updates
                ds['current_mission_id'] = None
                ds['mission_start_time'] = None
                ds['last_mission'] = mission_config['name']
                ds['last_update'] = now_utc_str()

                # Update mission history
                mission_hist = ds.get('mission_history', {})
                mission_hist[mission_id] = now_utc_str()
                ds['mission_history'] = mission_hist

                # Step 9: Update hero in database (within same transaction)
                cur.execute("""
                    UPDATE nfts SET dynamic_state = %s, last_update = NOW()
                    WHERE token_id = %s
                """, (json.dumps(ds), hero_id_padded))

                # Step 10: Delete active mission
                cur.execute("""
                    DELETE FROM active_missions WHERE hero_id = %s AND wallet = %s
                """, (hero_id_padded, wallet))

                # Step 11: Update player stats
                cur.execute("""
                    INSERT INTO player_stats (wallet, total_missions, total_xp_earned, total_ember_earned,
                                             total_deaths, updated_at)
                    VALUES (%s, 1, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (wallet) DO UPDATE SET
                        total_missions = player_stats.total_missions + 1,
                        total_xp_earned = player_stats.total_xp_earned + EXCLUDED.total_xp_earned,
                        total_ember_earned = player_stats.total_ember_earned + EXCLUDED.total_ember_earned,
                        total_deaths = player_stats.total_deaths + EXCLUDED.total_deaths,
                        updated_at = CURRENT_TIMESTAMP
                """, (wallet, xp_gained, aura_gained, 1 if outcome == 'DEATH' else 0))

                # Transaction commits automatically via context manager
                logger.info(f"Mission complete (locked): hero={hero_id_padded}, outcome={outcome}, xp={xp_gained}")

        # Step 12: Invalidate caches (after transaction commits)
        db.invalidate_wallet_cache(wallet)

        # Step 13: Build response
        response = {
            'success': True,
            'outcome': outcome,
            'hero_id': hero_id_padded,
            'mission_name': mission_config['name'],
            'locked_transaction': True  # Indicates this used the new locking system
        }

        if outcome == 'SUCCESS':
            response['xp_gained'] = xp_gained
            response['aura_gained'] = aura_gained
            response['hero_xp_now'] = ds['xp_total']
            response['hero_aura_now'] = ds['aura_level']
            response['message'] = f"🎉 SUCCESS! Completed {mission_config['name']}!"
        elif outcome == 'FAILURE':
            response['xp_lost'] = xp_lost
            response['hero_xp_now'] = ds['xp_total']
            response['message'] = f"⚠️ FAILED: Lost {xp_lost} XP"
        elif outcome == 'DEATH':
            response['death_count'] = ds['death_count']
            xp_cost, aura_cost = get_death_cost(ds['death_count'] - 1)
            response['reinvocation_cost'] = {'xp': xp_cost, 'aura': aura_cost}
            response['message'] = f"💀 FALLEN: Hero has died!"

        return response, 200

    except LockAcquisitionError as e:
        logger.warning(f"Lock acquisition failed: {e}")
        return {'error': str(e), 'retry': True}, 409

    except Exception as e:
        logger.error(f"Mission complete error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': f'Internal error: {str(e)}'}, 500


def roll_mission_outcome_simple(hero_ds, mission_config, death_protection=0):
    """
    Simplified mission outcome roll for use within locked transactions.

    Args:
        hero_ds: Hero dynamic state dict
        mission_config: Mission configuration dict
        death_protection: % reduction in death probability from equipment

    Returns:
        tuple: (outcome, details)
    """
    import random

    # Base success rate from mission
    difficulty = mission_config.get('difficulty', 'EASY')

    # Difficulty-based success rates
    success_rates = {
        'EASY': 85,
        'MEDIUM': 70,
        'HARD': 55,
        'PARTY': 75
    }

    success_rate = success_rates.get(difficulty, 75)

    # Apply hero level bonus (simplified)
    xp_total = hero_ds.get('xp_total', 0)
    level = min(10, xp_total // 1000)  # Rough level calculation
    success_rate += level * 2

    # Cap success rate
    success_rate = min(95, success_rate)

    roll = random.randint(1, 100)

    if roll <= success_rate:
        # Success
        base_xp = mission_config.get('xp_reward', 50)
        base_aura = mission_config.get('aura_reward', 10)

        # Randomize slightly
        xp_gain = int(base_xp * random.uniform(0.9, 1.2))
        aura_gain = int(base_aura * random.uniform(0.9, 1.2))

        return 'SUCCESS', {'xp_gain': xp_gain, 'aura_gain': aura_gain}

    else:
        # Failed - check for death
        death_chance = {'EASY': 5, 'MEDIUM': 10, 'HARD': 20, 'PARTY': 8}.get(difficulty, 10)

        # Apply death protection
        if death_protection > 0:
            death_chance = max(1, death_chance - death_protection)

        death_roll = random.randint(1, 100)

        if death_roll <= death_chance:
            return 'DEATH', {}
        else:
            xp_loss = int(mission_config.get('xp_reward', 50) * 0.3)
            return 'FAILURE', {'xp_loss': xp_loss}


def start_mission_with_lock(wallet, hero_id, mission_id, equipment_bonuses=None):
    """
    Start a mission with database locks to prevent race conditions.
    Locks the hero to prevent concurrent mission starts.

    Args:
        wallet: The wallet address
        hero_id: The hero token_id
        mission_id: The mission to start
        equipment_bonuses: Pre-calculated equipment bonuses (optional)

    Returns:
        tuple: (response_dict, http_status_code)
    """
    wallet = wallet.lower()
    hero_id_padded = str(hero_id).zfill(5)

    if not POSTGRESQL_AVAILABLE:
        return {'error': 'Database not available'}, 503

    try:
        with db.get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Step 1: Acquire lock on hero
                try:
                    hero_row = acquire_hero_lock(cur, hero_id_padded, wallet)
                except LockAcquisitionError as e:
                    return {'error': str(e), 'retry': True}, 409

                ds = hero_row.get('dynamic_state') or {}

                # Step 2: Verify hero state
                state = ds.get('state', 'READY')
                if state == 'FALLEN':
                    return {'error': 'Hero is fallen. Perform reinvocation ritual first.'}, 400
                if state == 'ON_MISSION':
                    return {'error': 'Hero is already on a mission'}, 400

                # Step 3: Find mission config
                mission_config = None
                for m in MISSIONS:
                    if m['id'] == mission_id:
                        mission_config = m
                        break
                if not mission_config:
                    for e in EVENTS:
                        if e['id'] == mission_id:
                            mission_config = e
                            break

                if not mission_config:
                    return {'error': f'Mission not found: {mission_id}'}, 404

                # Step 4: Check energy
                base_energy_cost = mission_config.get('energy_cost', 10)
                cost_energy = base_energy_cost
                energy_current = ds.get('energy_current', 0)

                # Apply energy reduction buffs
                buff = ds.get('ember_roll_buff')
                if buff:
                    expires_at = buff.get('expires_at')
                    if expires_at:
                        try:
                            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                            now = datetime.now(timezone.utc)
                            if now < expires_dt:
                                energy_reduction = buff.get('energy_reduction', 0)
                                if energy_reduction > 0:
                                    cost_energy = int(cost_energy * (100 - energy_reduction) / 100)
                        except Exception:
                            pass

                # Apply equipment energy reduction
                if equipment_bonuses is None:
                    equipment_bonuses = get_emissary_bonuses(hero_id_padded)

                equip_energy_reduction = equipment_bonuses.get('energy', 0)
                if equip_energy_reduction > 0:
                    cost_energy = max(1, int(cost_energy * (100 - equip_energy_reduction) / 100))

                if energy_current < cost_energy:
                    return {'error': f'Not enough energy. Required: {cost_energy}, Available: {energy_current}'}, 400

                # Step 5: Check mission cooldown
                mission_hist = ds.get('mission_history', {})
                last_run_ts = mission_hist.get(mission_id)
                if last_run_ts and hours_since(last_run_ts) < ROTATION_HOURS:
                    hours_left = ROTATION_HOURS - hours_since(last_run_ts)
                    hours_int = int(hours_left)
                    minutes_int = int((hours_left - hours_int) * 60)
                    return {
                        'error': 'mission_cooldown',
                        'error_type': 'cooldown',
                        'hours': hours_int,
                        'minutes': minutes_int,
                        'mission_name': mission_config['name'],
                        'message': f'This Emissary has recently completed "{mission_config["name"]}". The Order requires {hours_int}h {minutes_int}m recovery before redeployment to this same mission. Choose a different assignment.'
                    }, 400

                # Step 6: Calculate duration with speed bonus
                base_duration = mission_config.get('duration_hours', 1)
                speed_bonus = equipment_bonuses.get('speed', 0)
                if speed_bonus > 0:
                    effective_duration = max(base_duration * 0.1, base_duration * (100 - speed_bonus) / 100)
                else:
                    effective_duration = base_duration

                # Step 7: Update hero state
                ds['energy_current'] = max(0, energy_current - cost_energy)
                ds['state'] = 'ON_MISSION'
                start_time = now_utc_str()
                ds['mission_start_time'] = start_time
                ds['current_mission_id'] = mission_id
                ds['last_update'] = start_time

                cur.execute("""
                    UPDATE nfts SET dynamic_state = %s, last_update = NOW()
                    WHERE token_id = %s
                """, (json.dumps(ds), hero_id_padded))

                # Step 8: Insert active mission record
                mission_key = f"{wallet}_{hero_id_padded}"
                cur.execute("""
                    INSERT INTO active_missions (mission_key, wallet, hero_id, mission_id,
                                                 start_time, duration_hours, is_party, hero_ids)
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE, %s::jsonb)
                    ON CONFLICT (mission_key) DO UPDATE SET
                        mission_id = EXCLUDED.mission_id,
                        start_time = EXCLUDED.start_time,
                        duration_hours = EXCLUDED.duration_hours
                """, (mission_key, wallet, hero_id_padded, mission_id,
                      start_time, effective_duration, json.dumps([hero_id_padded])))

                # Transaction commits via context manager
                logger.info(f"Mission started (locked): hero={hero_id_padded}, mission={mission_id}")

        # Invalidate caches
        db.invalidate_wallet_cache(wallet)

        # Calculate completion time
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        completion_time = (start_dt + timedelta(hours=effective_duration)).isoformat()

        # Calculate duration in minutes
        actual_duration_minutes = int(effective_duration * 60)

        # Build full response matching original mission start format
        return {
            'success': True,
            'hero_id': hero_id_padded,
            'mission_id': mission_id,
            'mission_name': mission_config['name'],
            'difficulty': mission_config.get('difficulty', 'EASY'),
            'hero_energy_now': ds['energy_current'],
            'completion_time': completion_time,
            # Duration info (for visual display)
            'duration': {
                'base_hours': base_duration,
                'actual_hours': effective_duration,
                'actual_minutes': actual_duration_minutes
            },
            # Energy info (for visual display)
            'energy': {
                'base': base_energy_cost,
                'actual': cost_energy
            },
            # Legacy fields for backwards compatibility
            'duration_hours': effective_duration,
            'base_duration_hours': base_duration,
            'energy_spent': cost_energy,
            # Bonuses applied
            'bonuses_applied': {
                'ember': equipment_bonuses.get('ember', 0),
                'xp': equipment_bonuses.get('xp', 0),
                'energy': equipment_bonuses.get('energy', 0),
                'death': equipment_bonuses.get('death', 0),
                'speed': equipment_bonuses.get('speed', 0)
            },
            'equipment_bonuses': {
                'ember_boost': equipment_bonuses.get('ember', 0),
                'xp_boost': equipment_bonuses.get('xp', 0),
                'energy_reduction': equipment_bonuses.get('energy', 0),
                'death_protection': equipment_bonuses.get('death', 0),
                'speed_bonus': equipment_bonuses.get('speed', 0),
                'item_count': equipment_bonuses.get('item_count', 0),
                'rune_count': equipment_bonuses.get('rune_count', 0)
            },
            'locked_transaction': True
        }, 200

    except LockAcquisitionError as e:
        logger.warning(f"Lock acquisition failed for mission start: {e}")
        return {'error': str(e), 'retry': True}, 409

    except Exception as e:
        logger.error(f"Mission start error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': f'Internal error: {str(e)}'}, 500


def equip_item_with_lock(wallet, emissary_id, item_id, item_type):
    """
    Equip an item with database locks to prevent race conditions.
    Locks the hero to prevent concurrent equipment changes.

    Args:
        wallet: The wallet address
        emissary_id: The emissary token_id
        item_id: The item ID to equip
        item_type: The equipment slot type

    Returns:
        tuple: (response_dict, http_status_code)
    """
    wallet = wallet.lower()
    emissary_id_padded = str(emissary_id).zfill(5)

    if not POSTGRESQL_AVAILABLE:
        return {'error': 'Database not available'}, 503

    try:
        with db.get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Step 1: Acquire lock on hero
                try:
                    hero_row = acquire_hero_lock(cur, emissary_id_padded, wallet)
                except LockAcquisitionError as e:
                    return {'error': str(e), 'retry': True}, 409

                ds = hero_row.get('dynamic_state') or {}

                # Step 2: Verify hero is not on mission
                state = ds.get('state', 'READY')
                if state == 'ON_MISSION':
                    return {'error': 'Cannot change equipment while emissary is on a mission'}, 400

                # Step 3: Handle runes specially
                if item_type == "rune":
                    # Check current rune count
                    cur.execute("""
                        SELECT COALESCE(array_length(rune_ids, 1), 0) as rune_count,
                               COALESCE(rune_ids, ARRAY[]::TEXT[]) as rune_ids
                        FROM nfts WHERE token_id = %s
                    """, (emissary_id_padded,))
                    row = cur.fetchone()
                    rune_count = row['rune_count'] if row else 0
                    current_runes = row['rune_ids'] if row else []

                    if rune_count >= 2:
                        return {'error': 'Cannot equip more than 2 runes'}, 400

                    if item_id in current_runes:
                        return {'error': 'This rune is already equipped'}, 400

                    # Add rune
                    cur.execute("""
                        UPDATE nfts
                        SET rune_ids = array_append(COALESCE(rune_ids, ARRAY[]::TEXT[]), %s)
                        WHERE token_id = %s
                    """, (item_id, emissary_id_padded))
                else:
                    # Standard equipment slot
                    column_map = {
                        "weapon": "weapon_id",
                        "armor": "armor_id",
                        "helmet": "helmet_id",
                        "accessory": "accessory_id",
                        "amulet": "amulet_id"
                    }
                    column = column_map.get(item_type)
                    if not column:
                        return {'error': f'Invalid item type: {item_type}'}, 400

                    cur.execute(f"UPDATE nfts SET {column} = %s WHERE token_id = %s",
                               (item_id, emissary_id_padded))

                # Transaction commits via context manager
                logger.info(f"Equipment equipped (locked): emissary={emissary_id_padded}, type={item_type}, item={item_id}")

        # Invalidate equipment cache
        db.invalidate_equipment_cache(emissary_id)

        return {
            'success': True,
            'message': f'{item_type.capitalize()} equipped successfully',
            'locked_transaction': True
        }, 200

    except LockAcquisitionError as e:
        logger.warning(f"Lock acquisition failed for equip: {e}")
        return {'error': str(e), 'retry': True}, 409

    except Exception as e:
        logger.error(f"Equip item error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': f'Internal error: {str(e)}'}, 500


def unequip_item_with_lock(wallet, emissary_id, item_type, item_id=None):
    """
    Unequip an item with database locks to prevent race conditions.

    Args:
        wallet: The wallet address
        emissary_id: The emissary token_id
        item_type: The equipment slot type
        item_id: The specific item ID (required for runes)

    Returns:
        tuple: (response_dict, http_status_code)
    """
    wallet = wallet.lower()
    emissary_id_padded = str(emissary_id).zfill(5)

    if not POSTGRESQL_AVAILABLE:
        return {'error': 'Database not available'}, 503

    try:
        with db.get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Step 1: Acquire lock on hero
                try:
                    hero_row = acquire_hero_lock(cur, emissary_id_padded, wallet)
                except LockAcquisitionError as e:
                    return {'error': str(e), 'retry': True}, 409

                ds = hero_row.get('dynamic_state') or {}

                # Step 2: Verify hero is not on mission
                state = ds.get('state', 'READY')
                if state == 'ON_MISSION':
                    return {'error': 'Cannot change equipment while emissary is on a mission'}, 400

                # Step 3: Perform unequip
                if item_type == "rune" and item_id:
                    cur.execute("""
                        UPDATE nfts SET rune_ids = array_remove(rune_ids, %s) WHERE token_id = %s
                    """, (item_id, emissary_id_padded))
                elif item_type:
                    column_map = {
                        "weapon": "weapon_id",
                        "armor": "armor_id",
                        "helmet": "helmet_id",
                        "accessory": "accessory_id",
                        "amulet": "amulet_id"
                    }
                    column = column_map.get(item_type)
                    if column:
                        cur.execute(f"UPDATE nfts SET {column} = NULL WHERE token_id = %s",
                                   (emissary_id_padded,))

                # Transaction commits via context manager
                logger.info(f"Equipment unequipped (locked): emissary={emissary_id_padded}, type={item_type}")

        # Invalidate equipment cache
        db.invalidate_equipment_cache(emissary_id)

        return {
            'success': True,
            'message': 'Item unequipped',
            'locked_transaction': True
        }, 200

    except LockAcquisitionError as e:
        logger.warning(f"Lock acquisition failed for unequip: {e}")
        return {'error': str(e), 'retry': True}, 409

    except Exception as e:
        logger.error(f"Unequip item error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': f'Internal error: {str(e)}'}, 500


def confirm_claim_with_lock(claim_id, token_id=None, tx_hash=None, frontend_wallet=None):
    """
    Confirm a claim with database locks to prevent double-claiming.

    Args:
        claim_id: The unique claim identifier
        token_id: The blockchain token ID (optional)
        tx_hash: The transaction hash (optional)
        frontend_wallet: Fallback wallet from frontend (optional)

    Returns:
        tuple: (response_dict, http_status_code)
    """
    if not claim_id:
        return {'error': 'Missing claim_id'}, 400

    if not POSTGRESQL_AVAILABLE:
        return {'error': 'Database not available'}, 503

    try:
        generated_item = None

        with db.get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Step 1: Acquire lock on claim
                try:
                    claim_row = acquire_claim_lock(cur, claim_id)
                except LockAcquisitionError as e:
                    return {'error': str(e), 'retry': True}, 409

                # Step 2: Get claim details
                claim_type = claim_row.get('claim_type', 'ITEM')
                difficulty = claim_row.get('difficulty') or 'EASY'
                wallet = claim_row.get('wallet_address') or frontend_wallet

                if not wallet:
                    return {'error': 'No wallet address found'}, 400

                wallet = wallet.lower()

                # Step 3: Generate item
                try:
                    item_data = generate_random_item(claim_type, difficulty, wallet)
                    item_id = insert_item_to_vault(item_data)

                    if item_id:
                        generated_item = {
                            'id': item_id,
                            'name': item_data['name'],
                            'type': item_data['type'],
                            'rarity': item_data['rarity'],
                            'stats': item_data['stats']
                        }
                        logger.info(f"Generated {item_data['rarity']} {item_data['type']}: {item_data['name']}")
                except Exception as e:
                    logger.error(f"Error generating item: {e}")
                    # Continue - we still want to mark claim as used

                # Step 4: Mark claim as claimed (within same transaction)
                cur.execute("""
                    UPDATE pending_claims
                    SET status = 'claimed',
                        claimed_at = CURRENT_TIMESTAMP,
                        tx_hash = %s
                    WHERE claim_id = %s
                """, (tx_hash, claim_id))

                logger.info(f"Claim confirmed (locked): claim_id={claim_id[:20]}...")

        return {
            'success': True,
            'message': 'Claim confirmed',
            'generated_item': generated_item,
            'locked_transaction': True
        }, 200

    except LockAcquisitionError as e:
        logger.warning(f"Lock acquisition failed for claim: {e}")
        return {'error': str(e), 'retry': True}, 409

    except Exception as e:
        logger.error(f"Claim confirm error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': f'Internal error: {str(e)}'}, 500


# ---------------------------------
# 🏥 HEALTH CHECK & MONITORING ENDPOINTS
# ---------------------------------

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns system status including database connectivity.
    """
    status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '2.0.0',
        'components': {}
    }

    # Check database
    try:
        with db.get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        status['components']['database'] = 'connected'
    except Exception as e:
        status['components']['database'] = f'error: {str(e)[:50]}'
        status['status'] = 'degraded'

    # Pool info
    if db.connection_pool:
        try:
            status['components']['pool'] = {
                'min': db.POOL_MIN_CONN,
                'max': db.POOL_MAX_CONN,
                'available': True
            }
        except:
            status['components']['pool'] = 'unknown'
    else:
        status['components']['pool'] = 'not_initialized'
        status['status'] = 'degraded'

    # Check signing capability
    status['components']['signing'] = 'available' if SIGNING_AVAILABLE and BACKEND_SIGNER_PRIVATE_KEY else 'unavailable'

    http_code = 200 if status['status'] == 'healthy' else 503
    return jsonify(status), http_code


@app.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Basic metrics endpoint for monitoring.
    """
    try:
        metrics = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'rate_limits': {
                'active_keys': len(_rate_limit_storage),
            },
            'cache': {
                'wallet_nfts': len(db._wallet_nfts_cache) if hasattr(db, '_wallet_nfts_cache') else 0,
                'equipment_bonuses': len(db._equipment_bonuses_cache) if hasattr(db, '_equipment_bonuses_cache') else 0,
                'ipfs_metadata': len(_ipfs_metadata_cache),
            }
        }

        # Get active missions count
        if POSTGRESQL_AVAILABLE:
            try:
                with db.get_db() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM active_missions")
                        metrics['active_missions'] = cur.fetchone()[0]

                        cur.execute("SELECT COUNT(*) FROM nfts")
                        metrics['total_nfts'] = cur.fetchone()[0]

                        cur.execute("SELECT COUNT(DISTINCT last_known_owner) FROM nfts WHERE last_known_owner IS NOT NULL")
                        metrics['unique_wallets'] = cur.fetchone()[0]
            except:
                pass

        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/debug/nft-status/<wallet>')
def debug_nft_status(wallet):
    """
    🔍 DIAGNOSTIC ENDPOINT: Check NFT metadata status for a wallet.

    Returns for each NFT:
    - PostgreSQL data (dynamic_state, XP, Aura)
    - Metadata endpoint data
    - Comparison of both sources

    Usage: GET /api/debug/nft-status/0xYourWallet
    """
    wallet = wallet.lower()

    if not POSTGRESQL_AVAILABLE:
        return jsonify({'error': 'PostgreSQL not available'}), 503

    results = {
        'wallet': wallet,
        'summary': {
            'total_nfts': 0,
            'with_dynamic_state': 0,
            'without_dynamic_state': 0,
            'with_xp': 0,
            'metadata_matches_db': 0,
            'metadata_mismatches': 0
        },
        'nfts': []
    }

    try:
        # Get all NFTs for this wallet from PostgreSQL
        with db.get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT token_id, name, dynamic_state, last_synced, last_known_owner
                    FROM nfts
                    WHERE LOWER(last_known_owner) = %s
                    ORDER BY token_id
                """, (wallet,))
                db_nfts = cur.fetchall()

        results['summary']['total_nfts'] = len(db_nfts)

        for nft in db_nfts:
            token_id = nft['token_id']
            ds = nft['dynamic_state'] or {}

            # Get PostgreSQL data
            db_xp = ds.get('xp_total', 0) if ds else 0
            db_aura = ds.get('aura_level', 0) if ds else 0
            db_state = ds.get('state', 'UNKNOWN') if ds else 'NO_DATA'
            has_dynamic_state = bool(ds and len(ds) > 0)

            # Get metadata endpoint data
            metadata_data = find_dynamic_state_for_token(token_id)
            meta_xp = metadata_data.get('xp_total', 0)
            meta_aura = metadata_data.get('aura_level', 0)

            # Compare
            xp_match = db_xp == meta_xp
            aura_match = db_aura == meta_aura
            all_match = xp_match and aura_match

            # Update summary
            if has_dynamic_state:
                results['summary']['with_dynamic_state'] += 1
            else:
                results['summary']['without_dynamic_state'] += 1

            if db_xp > 0:
                results['summary']['with_xp'] += 1

            if all_match:
                results['summary']['metadata_matches_db'] += 1
            else:
                results['summary']['metadata_mismatches'] += 1

            # Add NFT details
            results['nfts'].append({
                'token_id': token_id,
                'name': nft['name'],
                'last_synced': str(nft['last_synced']) if nft['last_synced'] else None,
                'postgresql': {
                    'has_dynamic_state': has_dynamic_state,
                    'xp_total': db_xp,
                    'aura_level': db_aura,
                    'state': db_state,
                    'energy': ds.get('energy_current', 0) if ds else 0,
                    'level': ds.get('xp_level', 1) if ds else 1,
                    'total_missions': ds.get('total_missions_completed', 0) if ds else 0
                },
                'metadata_endpoint': {
                    'xp_total': meta_xp,
                    'aura_level': meta_aura,
                    'energy': metadata_data.get('energy_current', 0),
                    'level': metadata_data.get('xp_level', 1)
                },
                'comparison': {
                    'xp_match': xp_match,
                    'aura_match': aura_match,
                    'all_match': all_match,
                    'issue': None if all_match else f"DB: XP={db_xp}, Aura={db_aura} | Metadata: XP={meta_xp}, Aura={meta_aura}"
                }
            })

        return jsonify(results)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/debug/sync-nft/<token_id>')
def debug_sync_nft(token_id):
    """
    🔧 Force sync a specific NFT to PostgreSQL.

    Usage: GET /api/debug/sync-nft/19726
    """
    wallet = request.args.get('wallet', '').lower()

    try:
        token_id_padded = str(token_id).zfill(5)

        # Get current state before sync
        before = get_nft_from_database(token_id_padded)
        before_ds = before.get('dynamic_state', {}) if before else None

        # Force sync
        result = sync_nft_to_database(token_id_padded, owner_wallet=wallet if wallet else None)

        after_ds = result.get('dynamic_state', {}) if result else None

        return jsonify({
            'success': True,
            'token_id': token_id_padded,
            'action': 'updated' if before else 'created',
            'before': {
                'existed': bool(before),
                'xp': before_ds.get('xp_total', 0) if before_ds else None,
                'aura': before_ds.get('aura_level', 0) if before_ds else None
            },
            'after': {
                'xp': after_ds.get('xp_total', 0) if after_ds else 0,
                'aura': after_ds.get('aura_level', 0) if after_ds else 0,
                'state': after_ds.get('state', 'UNKNOWN') if after_ds else 'UNKNOWN'
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ---------------------------------
# 📊 PLAYER STATS HELPER FUNCTIONS
# ---------------------------------

def update_player_stats(wallet, xp_earned=0, ember_earned=0, missions=0, deaths=0, items=0, runes=0, energy_spent=0, sacrifices=0):
    """
    Update player stats in PostgreSQL (atomic operation).
    Replaces JSON-based stats tracking for scalability.
    """
    if not POSTGRESQL_AVAILABLE:
        return False

    try:
        with db.get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO player_stats (
                        wallet, total_missions, total_xp_earned, total_ember_earned,
                        total_deaths, total_items_found, total_runes_found,
                        total_energy_spent, total_sacrifices, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (wallet) DO UPDATE SET
                        total_missions = player_stats.total_missions + EXCLUDED.total_missions,
                        total_xp_earned = player_stats.total_xp_earned + EXCLUDED.total_xp_earned,
                        total_ember_earned = player_stats.total_ember_earned + EXCLUDED.total_ember_earned,
                        total_deaths = player_stats.total_deaths + EXCLUDED.total_deaths,
                        total_items_found = player_stats.total_items_found + EXCLUDED.total_items_found,
                        total_runes_found = player_stats.total_runes_found + EXCLUDED.total_runes_found,
                        total_energy_spent = player_stats.total_energy_spent + EXCLUDED.total_energy_spent,
                        total_sacrifices = player_stats.total_sacrifices + EXCLUDED.total_sacrifices,
                        updated_at = CURRENT_TIMESTAMP
                """, (wallet.lower(), missions, xp_earned, ember_earned, deaths, items, runes, energy_spent, sacrifices))
        logger.info(f"Player stats updated: wallet={wallet[:10]}..., missions={missions}, xp={xp_earned}")
        return True
    except Exception as e:
        logger.error(f"Error updating player stats: {e}")
        return False


def get_player_stats(wallet):
    """Get player stats from PostgreSQL."""
    if not POSTGRESQL_AVAILABLE:
        return None

    try:
        with db.get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM player_stats WHERE wallet = %s
                """, (wallet.lower(),))
                return cur.fetchone()
    except Exception as e:
        logger.error(f"Error getting player stats: {e}")
        return None


# ---------------------------------

if __name__ == "__main__":
    # 🔥 VALIDAR INTEGRIDAD AL INICIAR
    validate_database_integrity()

    app.run(debug=True)
