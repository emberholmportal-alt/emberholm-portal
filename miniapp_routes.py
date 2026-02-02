"""
EMBERHOLM MINI APP - ROUTES MODULE
===================================
Endpoints para la Mini App de Farcaster.
Incluye: $PYRE system, Micro-Missions, Realm Status, Full Emissary Status, Social Chat.

Importar en app.py:
    from miniapp_routes import register_miniapp_routes
    register_miniapp_routes(app)
"""

import json
import random
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import jsonify, request

# Import narrative data for micro-missions
from narrative_data import get_all_narratives, MISSION_CATEGORIES

# Database import (will be set by register function)
db = None
POSTGRESQL_AVAILABLE = False

# =========================================================================
# REALM STATUS CONFIG
# =========================================================================

# Emberholm tiene su propio calendario (siempre en el año 1978 de la Era de la Llama)
REALM_YEAR = 1978
REALM_ERA = "Era of the Flame"

# Weather patterns for immersion
WEATHER_PATTERNS = [
    {"name": "Sunny", "icon": "sun", "description": "The Eternal Flame burns bright"},
    {"name": "Cloudy", "icon": "cloud", "description": "Mist from the Circle shrouds the land"},
    {"name": "Stormy", "icon": "cloud-lightning", "description": "The Void Echoes stir the skies"},
    {"name": "Ember Rain", "icon": "cloud-drizzle", "description": "Sparks fall from the heavens"},
    {"name": "Clear Night", "icon": "moon", "description": "Stars align over Emberholm"},
    {"name": "Ash Wind", "icon": "wind", "description": "Whispers from the Forge Legion"},
]

# Flame states based on global activity
FLAME_STATES = {
    "dormant": {"name": "Dormant", "color": "#666", "description": "The flame rests"},
    "flickering": {"name": "Flickering", "color": "#f90", "description": "Embers stir"},
    "burning": {"name": "Burning", "color": "#f60", "description": "The flame grows"},
    "blazing": {"name": "Blazing", "color": "#f30", "description": "Power surges through Emberholm"},
    "inferno": {"name": "Inferno", "color": "#f00", "description": "The Eternal Flame roars!"},
}


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def get_db_connection():
    """Get database connection using the db module"""
    if not POSTGRESQL_AVAILABLE or not db:
        return None
    return db.get_db()


def get_current_realm_time():
    """
    Get current Emberholm realm time.
    The realm runs on its own timeline - always year 1978.
    """
    now = datetime.now(timezone.utc)

    # Realm uses the same month/day/hour but year 1978
    realm_date = now.strftime(f"%B %d, {REALM_YEAR}")
    realm_time = now.strftime("%H:%M")

    # Determine weather based on hour (changes every 4 hours)
    weather_index = (now.hour // 4) % len(WEATHER_PATTERNS)
    weather = WEATHER_PATTERNS[weather_index]

    return {
        "date": realm_date,
        "time": realm_time,
        "era": REALM_ERA,
        "year": REALM_YEAR,
        "weather": weather
    }


def get_flame_state():
    """
    Determine the Eternal Flame state based on recent activity.
    This creates a sense of shared world state.
    """
    if not POSTGRESQL_AVAILABLE:
        return FLAME_STATES["flickering"]

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Count missions completed in last hour
                cur.execute("""
                    SELECT COUNT(*) FROM active_missions
                    WHERE start_time > NOW() - INTERVAL '1 hour'
                """)
                recent_missions = cur.fetchone()[0]

                # Count active micro-missions
                cur.execute("""
                    SELECT COUNT(*) FROM active_micro_missions
                    WHERE status IN ('active', 'choice_pending')
                """)
                active_micros = cur.fetchone()[0]

        total_activity = recent_missions + (active_micros * 2)

        if total_activity >= 50:
            return FLAME_STATES["inferno"]
        elif total_activity >= 30:
            return FLAME_STATES["blazing"]
        elif total_activity >= 15:
            return FLAME_STATES["burning"]
        elif total_activity >= 5:
            return FLAME_STATES["flickering"]
        else:
            return FLAME_STATES["dormant"]

    except Exception as e:
        print(f"Error getting flame state: {e}")
        return FLAME_STATES["flickering"]


def validate_emissary_ownership(wallet, token_id):
    """Verify that wallet owns the emissary"""
    if not POSTGRESQL_AVAILABLE:
        return False, "Database not available"

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT last_known_owner FROM nfts
                    WHERE token_id = %s
                """, (str(token_id).zfill(5),))
                row = cur.fetchone()

                if not row:
                    return False, "Emissary not found"

                if row[0] and row[0].lower() != wallet.lower():
                    return False, "You don't own this emissary"

                return True, None
    except Exception as e:
        return False, str(e)


def get_emissary_state(token_id):
    """
    Get unified state of an emissary.
    Returns: READY, ON_MISSION, ON_MICRO_MISSION, FALLEN, CLAIMING
    """
    if not POSTGRESQL_AVAILABLE:
        return "READY", None, None

    token_id_padded = str(token_id).zfill(5)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check for active normal mission
                cur.execute("""
                    SELECT mission_id, start_time, duration_hours
                    FROM active_missions
                    WHERE hero_id = %s
                """, (token_id_padded,))
                mission = cur.fetchone()

                if mission:
                    end_time = mission[1] + timedelta(hours=mission[2])
                    if datetime.now(timezone.utc).replace(tzinfo=None) < end_time:
                        return "ON_MISSION", mission[0], end_time
                    else:
                        return "CLAIMING", mission[0], end_time

                # Check for active micro-mission
                cur.execute("""
                    SELECT micro_mission_id, ends_at, status
                    FROM active_micro_missions
                    WHERE emissary_token_id = %s
                    AND status IN ('active', 'choice_pending')
                """, (token_id_padded,))
                micro = cur.fetchone()

                if micro:
                    return "ON_MICRO_MISSION", micro[0], micro[1]

                # Check if FALLEN
                cur.execute("""
                    SELECT dynamic_state->>'state' as state
                    FROM nfts WHERE token_id = %s
                """, (token_id_padded,))
                nft = cur.fetchone()

                if nft and nft[0] == 'FALLEN':
                    return "FALLEN", None, None

                return "READY", None, None

    except Exception as e:
        print(f"Error getting emissary state: {e}")
        return "READY", None, None


# =========================================================================
# NARRATIVE GENERATOR FOR MULTI-STEP MISSIONS
# =========================================================================

def generate_linear_narrative(steps_content, endings_config):
    """
    Generate a linear narrative structure with scoring-based endings.

    Args:
        steps_content: List of dicts with 'text', 'choice_a', 'choice_b'
        endings_config: Dict with ending thresholds and texts

    The narrative tracks "bold_score" - choosing B adds 1, A adds 0.
    Final ending is determined by bold_score / total_steps ratio.
    """
    total_steps = len(steps_content)
    steps = {}

    for i, step in enumerate(steps_content):
        step_num = i + 1
        is_last = (step_num == total_steps)

        if is_last:
            # Final step leads to score-based ending
            steps[str(step_num)] = {
                "text": step['text'],
                "choices": [
                    {"id": "A", "text": step.get('choice_a', 'Conclude carefully'), "next": "CALC_END", "bold": 0},
                    {"id": "B", "text": step.get('choice_b', 'Finish with flair'), "next": "CALC_END", "bold": 1}
                ]
            }
        else:
            # Regular step leads to next
            steps[str(step_num)] = {
                "text": step['text'],
                "choices": [
                    {"id": "A", "text": step.get('choice_a', 'Be cautious'), "next": str(step_num + 1), "bold": 0},
                    {"id": "B", "text": step.get('choice_b', 'Be bold'), "next": str(step_num + 1), "bold": 1}
                ]
            }

    return {
        "steps": steps,
        "endings": endings_config,
        "total_steps": total_steps,
        "scoring": True  # Flag for scoring-based ending calculation
    }


# Standard endings for all missions (can be overridden)
STANDARD_ENDINGS = {
    "END_LEGENDARY": {"type": "LEGENDARY", "text": "Legendary success! Your choices were masterful.", "xp_mod": 2.0, "ember_mod": 2.0},
    "END_PERFECT": {"type": "PERFECT", "text": "Excellent work! Your balance of caution and boldness paid off.", "xp_mod": 1.5, "ember_mod": 1.5},
    "END_GOOD": {"type": "GOOD", "text": "Well done! The mission concludes successfully.", "xp_mod": 1.2, "ember_mod": 1.2},
    "END_NEUTRAL": {"type": "NEUTRAL", "text": "The mission is complete, though it could have gone better.", "xp_mod": 1.0, "ember_mod": 1.0}
}


# =========================================================================
# ROUTE REGISTRATION
# =========================================================================

def register_miniapp_routes(app, database_module=None, postgresql_available=False):
    """
    Register all Mini App routes with the Flask app.

    Args:
        app: Flask application instance
        database_module: The database module (database.py)
        postgresql_available: Boolean indicating if PostgreSQL is available
    """
    global db, POSTGRESQL_AVAILABLE
    db = database_module
    POSTGRESQL_AVAILABLE = postgresql_available

    print("🎮 Registering Mini App routes...")

    # Run database migrations if PostgreSQL is available
    if postgresql_available:
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # FIX: Ensure ember_balance supports decimal values (0.1, 0.5, etc.)
                    # This migration converts INTEGER to NUMERIC for proper EMBER tracking
                    cur.execute("""
                        DO $$
                        BEGIN
                            ALTER TABLE user_balances ALTER COLUMN ember_balance TYPE NUMERIC(18,2);
                        EXCEPTION WHEN undefined_table THEN
                            -- Table doesn't exist yet, will be created with correct type
                            NULL;
                        END $$;
                    """)

                    # =========================================================
                    # MIGRATION 003: Micro-Missions Narrative System
                    # =========================================================

                    # Add narrative columns to micro_missions table
                    cur.execute("""
                        ALTER TABLE micro_missions ADD COLUMN IF NOT EXISTS narrative_choices JSONB DEFAULT '[]'::jsonb;
                    """)
                    cur.execute("""
                        ALTER TABLE micro_missions ADD COLUMN IF NOT EXISTS narrative_outcomes JSONB DEFAULT '{}'::jsonb;
                    """)
                    cur.execute("""
                        ALTER TABLE micro_missions ADD COLUMN IF NOT EXISTS category VARCHAR(20) DEFAULT 'PATROL';
                    """)
                    cur.execute("""
                        ALTER TABLE micro_missions ADD COLUMN IF NOT EXISTS lore_connection TEXT;
                    """)
                    cur.execute("""
                        ALTER TABLE micro_missions ADD COLUMN IF NOT EXISTS achievements JSONB DEFAULT '{}'::jsonb;
                    """)
                    # Add narrative_steps for multi-step adventures
                    cur.execute("""
                        ALTER TABLE micro_missions ADD COLUMN IF NOT EXISTS narrative_steps JSONB DEFAULT '{}'::jsonb;
                    """)

                    # Create active_micro_missions table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS active_micro_missions (
                            id SERIAL PRIMARY KEY,
                            wallet VARCHAR(42) NOT NULL,
                            emissary_token_id VARCHAR(10) NOT NULL,
                            micro_mission_id VARCHAR(20) NOT NULL REFERENCES micro_missions(id),
                            current_step VARCHAR(10) DEFAULT '1',
                            choices_path JSONB DEFAULT '[]'::jsonb,
                            choice_made VARCHAR(50),
                            score INTEGER DEFAULT 0,
                            status VARCHAR(20) DEFAULT 'active',
                            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            ends_at TIMESTAMP,
                            completed_at TIMESTAMP,
                            outcome_type VARCHAR(20),
                            outcome_text TEXT,
                            pyre_earned NUMERIC(18,2) DEFAULT 0,
                            xp_earned INTEGER DEFAULT 0,
                            aura_earned INTEGER DEFAULT 0,
                            rewards_claimed BOOLEAN DEFAULT FALSE
                        )
                    """)
                    # Add choices_path column if missing
                    cur.execute("""
                        ALTER TABLE active_micro_missions ADD COLUMN IF NOT EXISTS choices_path JSONB DEFAULT '[]'::jsonb
                    """)
                    # Add ending_reached column for multi-step narrative endings
                    cur.execute("""
                        ALTER TABLE active_micro_missions ADD COLUMN IF NOT EXISTS ending_reached VARCHAR(50) DEFAULT NULL
                    """)
                    # Update current_step to VARCHAR if it's INTEGER (for step keys like "2A", "2B")
                    cur.execute("""
                        ALTER TABLE active_micro_missions ALTER COLUMN current_step TYPE VARCHAR(10) USING current_step::VARCHAR
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_active_micro_missions_wallet ON active_micro_missions(wallet)
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_active_micro_missions_status ON active_micro_missions(status)
                    """)

                    # Create micro_mission_cooldowns table (per emissary, not per wallet)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS micro_mission_cooldowns (
                            id SERIAL PRIMARY KEY,
                            emissary_token_id VARCHAR(10) NOT NULL,
                            mission_id VARCHAR(20) NOT NULL,
                            cooldown_until TIMESTAMP NOT NULL,
                            UNIQUE(emissary_token_id, mission_id)
                        )
                    """)

                    # Create micro_mission_history table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS micro_mission_history (
                            id SERIAL PRIMARY KEY,
                            wallet VARCHAR(42) NOT NULL,
                            emissary_token_id VARCHAR(10) NOT NULL,
                            micro_mission_id VARCHAR(20) NOT NULL,
                            choice_made VARCHAR(50),
                            outcome_type VARCHAR(20),
                            score INTEGER DEFAULT 0,
                            pyre_earned NUMERIC(18,2) DEFAULT 0,
                            xp_earned INTEGER DEFAULT 0,
                            ember_earned NUMERIC(18,2) DEFAULT 0,
                            aura_earned BOOLEAN DEFAULT FALSE,
                            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # =========================================================
                    # FORCE FIX: Update mission durations UNCONDITIONALLY
                    # EASY=120s (2min), MEDIUM=240s (4min), HARD=300s (5min)
                    # =========================================================
                    print("[Migration] Forcing duration updates for all missions...")
                    # EASY = 2 minutes (120s)
                    cur.execute("""
                        UPDATE micro_missions SET duration_seconds = 120
                        WHERE difficulty = 'EASY'
                    """)
                    easy_updated = cur.rowcount
                    # MEDIUM = 3 minutes (180s)
                    cur.execute("""
                        UPDATE micro_missions SET duration_seconds = 180
                        WHERE difficulty = 'MEDIUM'
                    """)
                    medium_updated = cur.rowcount
                    # HARD = 5 minutes (300s)
                    cur.execute("""
                        UPDATE micro_missions SET duration_seconds = 300
                        WHERE difficulty = 'HARD'
                    """)
                    hard_updated = cur.rowcount

                    # FORCE FIX: Any mission with duration > 600s (10 min) is broken
                    cur.execute("""
                        UPDATE micro_missions SET duration_seconds = 120
                        WHERE duration_seconds > 600 OR duration_seconds IS NULL
                    """)
                    broken_fixed = cur.rowcount

                    print(f"[Migration] Duration updates: EASY={easy_updated}, MEDIUM={medium_updated}, HARD={hard_updated}, broken_fixed={broken_fixed}")

                    # =========================================================
                    # FORCE FIX: Set PYRE rewards to 0 (NO PYRE in micro-missions)
                    # =========================================================
                    print("[Migration] Setting PYRE rewards to 0...")
                    cur.execute("""
                        UPDATE micro_missions SET pyre_reward_min = 0, pyre_reward_max = 0
                    """)
                    pyre_reset = cur.rowcount
                    print(f"[Migration] Reset PYRE to 0 for {pyre_reset} missions")

                    # =========================================================
                    # FULL RESET: Delete ALL active micro-missions and cooldowns
                    # Start fresh with clean state
                    # =========================================================
                    print("[Migration] Resetting micro-missions system...")

                    # Delete ALL active missions
                    cur.execute("DELETE FROM active_micro_missions")
                    active_deleted = cur.rowcount
                    print(f"[Migration] Deleted {active_deleted} active micro-missions")

                    # Recreate cooldowns table with correct schema (per emissary)
                    cur.execute("DROP TABLE IF EXISTS micro_mission_cooldowns CASCADE")
                    cur.execute("""
                        CREATE TABLE micro_mission_cooldowns (
                            id SERIAL PRIMARY KEY,
                            emissary_token_id VARCHAR(10) NOT NULL,
                            mission_id VARCHAR(20) NOT NULL,
                            cooldown_until TIMESTAMP NOT NULL,
                            UNIQUE(emissary_token_id, mission_id)
                        )
                    """)
                    print("[Migration] Recreated micro_mission_cooldowns table with emissary-based schema")

                    # Reset ALL emissaries stuck in ON_MICRO_MISSION state
                    cur.execute("""
                        UPDATE nfts SET
                            dynamic_state = jsonb_set(
                                COALESCE(dynamic_state, '{}'::jsonb),
                                '{state}',
                                '"READY"'
                            ),
                            last_update = NOW()
                        WHERE dynamic_state->>'state' = 'ON_MICRO_MISSION'
                    """)
                    emissaries_reset = cur.rowcount
                    print(f"[Migration] Reset {emissaries_reset} emissaries from ON_MICRO_MISSION to READY")

                    # =========================================================
                    # POPULATE NARRATIVES FROM narrative_data.py
                    # EASY=10 steps, MEDIUM=20 steps, HARD=35 steps
                    # =========================================================
                    print("[Migration] Populating narratives from narrative_data.py...")
                    narratives = get_all_narratives()
                    categories = MISSION_CATEGORIES
                    
                    for mission_id, narrative in narratives.items():
                        category = categories.get(mission_id, 'PATROL')
                        cur.execute("""
                            UPDATE micro_missions 
                            SET narrative_steps = %s::jsonb, category = %s
                            WHERE id = %s
                        """, (json.dumps(narrative), category, mission_id))
                    
                    print(f"[Migration] Updated narratives for {len(narratives)} missions")

                    # =========================================================
                    # FULL CLEANUP: Delete ALL active micro-missions (fresh start)
                    # This prevents issues with corrupted data formats
                    # =========================================================
                    cur.execute("DELETE FROM active_micro_missions WHERE status IN ('active', 'choice_pending')")
                    deleted = cur.rowcount
                    print(f"🧹 Deleted {deleted} active micro-missions (fresh start)")

                    # Reset ALL emissaries from ON_MICRO_MISSION to READY
                    cur.execute("""
                        UPDATE nfts SET
                            dynamic_state = jsonb_set(
                                COALESCE(dynamic_state, '{}'::jsonb),
                                '{state}',
                                '"READY"'
                            )
                        WHERE dynamic_state->>'state' = 'ON_MICRO_MISSION'
                    """)
                    reset_count = cur.rowcount
                    print(f"🔄 Reset {reset_count} emissaries from ON_MICRO_MISSION to READY")

                    # =========================================================
                    # FIX DURATIONS: EASY=120s (2min), MEDIUM=180s (3min), HARD=300s (5min)
                    # =========================================================
                    cur.execute("UPDATE micro_missions SET duration_seconds = 120 WHERE difficulty = 'EASY'")
                    cur.execute("UPDATE micro_missions SET duration_seconds = 180 WHERE difficulty = 'MEDIUM'")
                    cur.execute("UPDATE micro_missions SET duration_seconds = 300 WHERE difficulty = 'HARD'")
                    print("⏱️ Fixed mission durations (EASY=2min, MEDIUM=3min, HARD=5min)")

                    print("✅ Database migrations applied (including narrative system)")
        except Exception as e:
            print(f"⚠️ Database migration warning: {e}")

    # =====================================================================
    # REALM STATUS
    # =====================================================================

    @app.route('/api/realm-status', methods=['GET'])
    def api_realm_status():
        """
        Get current realm status: weather, time, date, flame state.
        Used by Mini App immersive bar.
        """
        realm_time = get_current_realm_time()
        flame = get_flame_state()

        return jsonify({
            "success": True,
            "realm": {
                "date": realm_time["date"],
                "time": realm_time["time"],
                "era": realm_time["era"],
                "year": realm_time["year"],
                "weather": realm_time["weather"],
                "flame": flame
            }
        })

    # =====================================================================
    # $PYRE ENDPOINTS
    # =====================================================================

    @app.route('/api/pyre/<wallet>', methods=['GET'])
    def api_pyre_balance(wallet):
        """Get $PYRE balance for a wallet"""
        wallet = wallet.lower()

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get or create balance
                    cur.execute("""
                        INSERT INTO pyre_balances (wallet, balance, total_earned, total_spent)
                        VALUES (%s, 0, 0, 0)
                        ON CONFLICT (wallet) DO NOTHING
                    """, (wallet,))

                    cur.execute("""
                        SELECT balance, total_earned, total_spent, daily_streak, last_daily_claim
                        FROM pyre_balances WHERE wallet = %s
                    """, (wallet,))
                    row = cur.fetchone()

                    if row:
                        # Check if daily claim is available
                        last_claim = row[4]
                        daily_available = True
                        if last_claim:
                            next_claim = last_claim + timedelta(days=1)
                            daily_available = datetime.now(timezone.utc).replace(tzinfo=None) >= next_claim

                        return jsonify({
                            "success": True,
                            "wallet": wallet,
                            "balance": row[0],
                            "total_earned": row[1],
                            "total_spent": row[2],
                            "daily_streak": row[3] or 0,
                            "daily_available": daily_available,
                            "last_daily_claim": row[4].isoformat() if row[4] else None
                        })

                    return jsonify({
                        "success": True,
                        "wallet": wallet,
                        "balance": 0,
                        "total_earned": 0,
                        "total_spent": 0,
                        "daily_streak": 0,
                        "daily_available": True,
                        "last_daily_claim": None
                    })

        except Exception as e:
            print(f"Error getting pyre balance: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/pyre/earn', methods=['POST'])
    def api_pyre_earn():
        """
        Add $PYRE to a wallet (internal use - from micro-missions, etc.)

        Body: {
            "wallet": "0x...",
            "amount": 50,
            "transaction_type": "micro_mission",
            "reference_id": "MM-E001",
            "description": "Completed The Whispering Flame"
        }
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()
        amount = data.get('amount', 0)
        tx_type = data.get('transaction_type', 'unknown')
        ref_id = data.get('reference_id', '')
        description = data.get('description', '')

        if not wallet or amount <= 0:
            return jsonify({"error": "Invalid wallet or amount"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Update balance
                    cur.execute("""
                        INSERT INTO pyre_balances (wallet, balance, total_earned)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (wallet) DO UPDATE SET
                            balance = pyre_balances.balance + %s,
                            total_earned = pyre_balances.total_earned + %s,
                            updated_at = NOW()
                        RETURNING balance, total_earned
                    """, (wallet, amount, amount, amount, amount))
                    row = cur.fetchone()

                    # Record transaction
                    cur.execute("""
                        INSERT INTO pyre_transactions
                        (wallet, amount, transaction_type, reference_id, description)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (wallet, amount, tx_type, ref_id, description))

                    return jsonify({
                        "success": True,
                        "wallet": wallet,
                        "amount_earned": amount,
                        "new_balance": row[0],
                        "total_earned": row[1]
                    })

        except Exception as e:
            print(f"Error earning pyre: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/pyre/spend', methods=['POST'])
    def api_pyre_spend():
        """
        Spend $PYRE from a wallet

        Body: {
            "wallet": "0x...",
            "amount": 100,
            "transaction_type": "energy_boost",
            "reference_id": "emissary_00042",
            "description": "Energy boost for Emissary #42"
        }
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()
        amount = data.get('amount', 0)
        tx_type = data.get('transaction_type', 'spend')
        ref_id = data.get('reference_id', '')
        description = data.get('description', '')

        if not wallet or amount <= 0:
            return jsonify({"error": "Invalid wallet or amount"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check balance first
                    cur.execute("""
                        SELECT balance FROM pyre_balances WHERE wallet = %s
                    """, (wallet,))
                    row = cur.fetchone()

                    if not row or row[0] < amount:
                        return jsonify({
                            "error": "Insufficient $PYRE balance",
                            "balance": row[0] if row else 0,
                            "required": amount
                        }), 400

                    # Deduct balance
                    cur.execute("""
                        UPDATE pyre_balances SET
                            balance = balance - %s,
                            total_spent = total_spent + %s,
                            updated_at = NOW()
                        WHERE wallet = %s
                        RETURNING balance, total_spent
                    """, (amount, amount, wallet))
                    row = cur.fetchone()

                    # Record transaction (negative amount)
                    cur.execute("""
                        INSERT INTO pyre_transactions
                        (wallet, amount, transaction_type, reference_id, description)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (wallet, -amount, tx_type, ref_id, description))

                    return jsonify({
                        "success": True,
                        "wallet": wallet,
                        "amount_spent": amount,
                        "new_balance": row[0],
                        "total_spent": row[1]
                    })

        except Exception as e:
            print(f"Error spending pyre: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/pyre/history/<wallet>', methods=['GET'])
    def api_pyre_history(wallet):
        """Get $PYRE transaction history for a wallet"""
        wallet = wallet.lower()
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, amount, transaction_type, reference_id, description, created_at
                        FROM pyre_transactions
                        WHERE wallet = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (wallet, limit, offset))
                    rows = cur.fetchall()

                    transactions = []
                    for row in rows:
                        transactions.append({
                            "id": row[0],
                            "amount": row[1],
                            "type": row[2],
                            "reference_id": row[3],
                            "description": row[4],
                            "created_at": row[5].isoformat() if row[5] else None
                        })

                    return jsonify({
                        "success": True,
                        "wallet": wallet,
                        "transactions": transactions,
                        "count": len(transactions),
                        "limit": limit,
                        "offset": offset
                    })

        except Exception as e:
            print(f"Error getting pyre history: {e}")
            return jsonify({"error": str(e)}), 500

    # =====================================================================
    # MICRO-MISSIONS ENDPOINTS
    # =====================================================================

    @app.route('/api/micro-missions', methods=['GET'])
    def api_micro_missions_list():
        """Get list of available micro-missions"""
        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, name, description, difficulty, duration_seconds,
                               energy_cost, pyre_reward_min, pyre_reward_max,
                               xp_reward_min, xp_reward_max, aura_chance,
                               narrative_intro, cooldown_minutes,
                               ember_reward_min, ember_reward_max
                        FROM micro_missions
                        WHERE is_active = TRUE
                        ORDER BY difficulty, id
                    """)
                    rows = cur.fetchall()

                    missions = []
                    for row in rows:
                        # Normalize difficulty to uppercase (frontend expects EASY/MEDIUM/HARD)
                        difficulty = (row[3] or 'EASY').upper()
                        # Map 'LEGENDARY' to 'HARD' for frontend compatibility
                        if difficulty == 'LEGENDARY':
                            difficulty = 'HARD'

                        missions.append({
                            "id": row[0],
                            "name": row[1],
                            "description": row[2],
                            "difficulty": difficulty,
                            "duration_seconds": row[4],
                            "energy_cost": row[5],
                            "pyre_reward": {"min": row[6], "max": row[7]},
                            "xp_reward": {"min": row[8], "max": row[9]},
                            "aura_chance": float(row[10]) if row[10] else 0,
                            "narrative_intro": row[11],
                            "cooldown_minutes": row[12],
                            # Include ember_reward for frontend
                            "ember_reward": {"min": row[13] or row[6], "max": row[14] or row[7]}
                        })

                    return jsonify({
                        "success": True,
                        "missions": missions,
                        "count": len(missions)
                    })

        except Exception as e:
            print(f"Error getting micro-missions: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/micro-mission/<mission_id>', methods=['GET'])
    def api_micro_mission_detail(mission_id):
        """Get detailed info about a specific micro-mission"""
        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, name, description, difficulty, duration_seconds,
                               energy_cost, pyre_reward_min, pyre_reward_max,
                               xp_reward_min, xp_reward_max, aura_chance,
                               narrative_intro, narrative_choices, narrative_outcomes,
                               cooldown_minutes
                        FROM micro_missions
                        WHERE id = %s AND is_active = TRUE
                    """, (mission_id,))
                    row = cur.fetchone()

                    if not row:
                        return jsonify({"error": "Micro-mission not found"}), 404

                    return jsonify({
                        "success": True,
                        "mission": {
                            "id": row[0],
                            "name": row[1],
                            "description": row[2],
                            "difficulty": row[3],
                            "duration_seconds": row[4],
                            "energy_cost": row[5],
                            "pyre_reward": {"min": row[6], "max": row[7]},
                            "xp_reward": {"min": row[8], "max": row[9]},
                            "aura_chance": float(row[10]) if row[10] else 0,
                            "narrative_intro": row[11],
                            "narrative_choices": row[12] or [],
                            "narrative_outcomes": row[13] or {},
                            "cooldown_minutes": row[14]
                        }
                    })

        except Exception as e:
            print(f"Error getting micro-mission detail: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/micro-mission/start', methods=['POST'])
    def api_micro_mission_start():
        """
        Start a micro-mission with an emissary.

        Body: {
            "wallet": "0x...",
            "emissary_token_id": "00042",
            "micro_mission_id": "MM-E001"
        }
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()
        token_id = str(data.get('emissary_token_id', '')).zfill(5)
        mission_id = data.get('micro_mission_id', '')

        if not wallet or not token_id or not mission_id:
            return jsonify({"error": "Missing required fields"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        # Validate ownership
        valid, error = validate_emissary_ownership(wallet, token_id)
        if not valid:
            return jsonify({"error": error}), 403

        # Check emissary state (EXCLUSIVITY VALIDATION)
        state, active_id, ends_at = get_emissary_state(token_id)

        if state == "ON_MISSION":
            return jsonify({
                "error": "Emissary is on a normal mission",
                "state": state,
                "mission_id": active_id,
                "ends_at": ends_at.isoformat() if ends_at else None
            }), 400

        if state == "ON_MICRO_MISSION":
            return jsonify({
                "error": "Emissary is already on a micro-mission",
                "state": state,
                "micro_mission_id": active_id,
                "ends_at": ends_at.isoformat() if ends_at else None
            }), 400

        if state == "FALLEN":
            return jsonify({
                "error": "Emissary is fallen and needs recovery",
                "state": state
            }), 400

        if state == "CLAIMING":
            return jsonify({
                "error": "Emissary has pending rewards to claim",
                "state": state
            }), 400

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get mission details including narrative_steps for multi-step adventures
                    cur.execute("""
                        SELECT id, name, duration_seconds, energy_cost, narrative_intro,
                               narrative_choices, narrative_steps
                        FROM micro_missions
                        WHERE id = %s AND is_active = TRUE
                    """, (mission_id,))
                    mission = cur.fetchone()

                    if not mission:
                        return jsonify({"error": "Micro-mission not found"}), 404

                    # Check energy (optional - depends on mission)
                    if mission[3] > 0:  # energy_cost
                        cur.execute("""
                            SELECT dynamic_state->>'energy_current' as energy
                            FROM nfts WHERE token_id = %s
                        """, (token_id,))
                        energy_row = cur.fetchone()
                        current_energy = int(energy_row[0]) if energy_row and energy_row[0] else 100

                        if current_energy < mission[3]:
                            return jsonify({
                                "error": "Not enough energy",
                                "current_energy": current_energy,
                                "required_energy": mission[3]
                            }), 400

                        # Deduct energy
                        cur.execute("""
                            UPDATE nfts SET
                                dynamic_state = jsonb_set(
                                    dynamic_state,
                                    '{energy_current}',
                                    to_jsonb(%s)
                                ),
                                last_update = NOW()
                            WHERE token_id = %s
                        """, (current_energy - mission[3], token_id))

                    # Check 24-hour cooldown per emissary
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    cur.execute("""
                        SELECT cooldown_until FROM micro_mission_cooldowns
                        WHERE emissary_token_id = %s AND mission_id = %s
                        AND cooldown_until > %s
                    """, (token_id, mission_id, now))
                    cooldown_row = cur.fetchone()

                    if cooldown_row:
                        cooldown_until = cooldown_row[0]
                        remaining = (cooldown_until - now).total_seconds()
                        hours_remaining = int(remaining // 3600)
                        mins_remaining = int((remaining % 3600) // 60)
                        return jsonify({
                            "error": f"This emissary must wait before repeating this mission",
                            "cooldown_until": cooldown_until.isoformat(),
                            "time_remaining": f"{hours_remaining}h {mins_remaining}m"
                        }), 400

                    # Calculate end time
                    ends_at = now + timedelta(seconds=mission[2])

                    # Create active micro-mission with current_step = "1"
                    cur.execute("""
                        INSERT INTO active_micro_missions
                        (wallet, emissary_token_id, micro_mission_id, started_at, ends_at, status, current_step, choices_path)
                        VALUES (%s, %s, %s, %s, %s, 'active', '1', '[]'::jsonb)
                        RETURNING id
                    """, (wallet, token_id, mission_id, now, ends_at))
                    active_id = cur.fetchone()[0]

                    # Update emissary state
                    cur.execute("""
                        UPDATE nfts SET
                            dynamic_state = jsonb_set(
                                dynamic_state,
                                '{state}',
                                '"ON_MICRO_MISSION"'
                            ),
                            last_update = NOW()
                        WHERE token_id = %s
                    """, (token_id,))

                    # Extract first step from narrative_steps for multi-step adventures
                    narrative_steps_raw = mission[6]

                    # Parse narrative_steps if it's a string
                    if isinstance(narrative_steps_raw, str):
                        import json as json_module
                        try:
                            narrative_steps = json_module.loads(narrative_steps_raw)
                        except:
                            narrative_steps = {}
                    else:
                        narrative_steps = narrative_steps_raw or {}

                    steps = narrative_steps.get('steps', {}) if isinstance(narrative_steps, dict) else {}
                    first_step = steps.get('1', {})

                    # Use multi-step narrative if available
                    if first_step:
                        narrative_text = first_step.get('text', mission[4] or 'Your journey begins...')
                        choices = first_step.get('choices', mission[5] or [])
                    elif mission[4] or mission[5]:
                        # Legacy fallback
                        narrative_text = mission[4] or 'Your journey begins...'
                        choices = mission[5] or []
                    else:
                        # Generic fallback for missions without any narrative data
                        print(f"[MicroMission] WARNING: No narrative data for {mission_id}, using generic fallback")
                        narrative_text = "Your emissary embarks on the mission. The path ahead is uncertain, but your resolve is strong."
                        choices = [
                            {"id": "A", "text": "Take the cautious approach"},
                            {"id": "B", "text": "Act boldly and decisively"}
                        ]

                    # Return structure for multi-step adventures
                    return jsonify({
                        "success": True,
                        "active_micro_mission_id": active_id,
                        "active_mission": {
                            "active_id": active_id,
                            "mission_id": mission[0],
                            "name": mission[1],
                            "duration_seconds": mission[2],
                            "narrative_intro": narrative_text,
                            "choices": choices,
                            "current_step": "1",
                            "choices_path": [],
                            "ending_reached": None,
                            "started_at": now.isoformat(),
                            "ends_at": ends_at.isoformat(),
                            "emissary_token_id": token_id,
                            "status": "active",
                            "choice_made": None
                        }
                    })

        except Exception as e:
            print(f"Error starting micro-mission: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/micro-mission/choice', methods=['POST'])
    def api_micro_mission_choice():
        """
        Handle multi-step narrative progression in micro-missions.

        Body: {
            "wallet": "0x...",
            "active_micro_mission_id": 123,
            "choice": "A"  // A or B
        }

        Returns:
        - If more steps remain: next step text and choices
        - If ending reached: ending info and readiness for completion
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()
        active_id = data.get('active_micro_mission_id')
        choice = data.get('choice', '').upper()

        if not wallet or not active_id or not choice:
            return jsonify({"error": "Missing required fields"}), 400

        if choice not in ['A', 'B', 'C']:
            return jsonify({"error": "Invalid choice. Must be A, B, or C"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get mission data including narrative_steps and current progress
                    cur.execute("""
                        SELECT amm.id, amm.status, amm.micro_mission_id,
                               COALESCE(amm.current_step, '1') as current_step,
                               COALESCE(amm.choices_path, '[]'::jsonb) as choices_path,
                               amm.ending_reached,
                               mm.narrative_steps, mm.name
                        FROM active_micro_missions amm
                        JOIN micro_missions mm ON amm.micro_mission_id = mm.id
                        WHERE amm.id = %s AND amm.wallet = %s
                    """, (active_id, wallet))
                    row = cur.fetchone()

                    if not row:
                        return jsonify({"error": "Active micro-mission not found"}), 404

                    status = row[1]
                    current_step = str(row[3]) if row[3] else "1"
                    choices_path = row[4] if row[4] else []

                    print(f"[MicroMission] Choice API - active_id: {active_id}, current_step: {current_step}, status: {status}")
                    ending_reached = row[5]
                    narrative_steps_raw = row[6]
                    mission_name = row[7]

                    # Parse narrative_steps if it's a string
                    if isinstance(narrative_steps_raw, str):
                        import json as json_module
                        try:
                            narrative_steps = json_module.loads(narrative_steps_raw)
                        except:
                            narrative_steps = {}
                    else:
                        narrative_steps = narrative_steps_raw or {}

                    print(f"[MicroMission] narrative_steps type: {type(narrative_steps)}, has steps: {'steps' in narrative_steps if isinstance(narrative_steps, dict) else 'N/A'}")

                    # Check if ending already reached
                    if ending_reached:
                        return jsonify({
                            "error": "Mission ending already reached. Claim your rewards.",
                            "ending_reached": ending_reached
                        }), 400

                    if status not in ['active', 'choice_pending']:
                        return jsonify({"error": f"Cannot make choice in status: {status}"}), 400

                    # Get steps and endings from narrative_steps
                    if not isinstance(narrative_steps, dict):
                        narrative_steps = {}

                    steps = narrative_steps.get('steps', {})
                    endings = narrative_steps.get('endings', {})

                    # FALLBACK: If no steps defined, use generic narrative
                    if not steps:
                        print(f"[MicroMission] WARNING: No narrative_steps for mission {row[2]}, using fallback")
                        steps = {
                            "1": {
                                "text": "Your emissary embarks on the mission. The path ahead is uncertain.",
                                "choices": [
                                    {"id": "A", "text": "Take the cautious approach", "next": "2A"},
                                    {"id": "B", "text": "Act boldly and decisively", "next": "2B"}
                                ]
                            },
                            "2A": {
                                "text": "Your careful approach pays off. You make steady progress.",
                                "choices": [
                                    {"id": "A", "text": "Continue with caution", "next": "END_GOOD"},
                                    {"id": "B", "text": "Take a calculated risk", "next": "END_PERFECT"}
                                ]
                            },
                            "2B": {
                                "text": "Your boldness is rewarded! Opportunities present themselves.",
                                "choices": [
                                    {"id": "A", "text": "Press your advantage", "next": "END_LEGENDARY"},
                                    {"id": "B", "text": "Consolidate your gains", "next": "END_GOOD"}
                                ]
                            }
                        }
                        endings = {
                            "END_LEGENDARY": {"type": "LEGENDARY", "text": "Outstanding success!", "pyre_mod": 2.0, "xp_mod": 2.0},
                            "END_PERFECT": {"type": "PERFECT", "text": "Excellent work!", "pyre_mod": 1.5, "xp_mod": 1.4},
                            "END_GOOD": {"type": "GOOD", "text": "Well done!", "pyre_mod": 1.2, "xp_mod": 1.2},
                            "END_NEUTRAL": {"type": "NEUTRAL", "text": "Mission complete.", "pyre_mod": 1.0, "xp_mod": 1.0}
                        }

                    print(f"[MicroMission] Available steps: {list(steps.keys())}")

                    # For linear narratives (new format), step is just the number based on choices made
                    # For branching narratives (old format), step might be like "2A", "2B"
                    # current_step from DB is the authoritative source
                    step_key = str(current_step) if current_step else "1"
                    current_step_data = steps.get(step_key, {})

                    if not current_step_data:
                        # Try finding the step another way - maybe it's like "2A" after first choice
                        # Reconstruct from choices_path (handle both old string format and new dict format)
                        if len(choices_path) > 0:
                            last_choice = choices_path[-1]
                            # Handle new format {"choice": "A", "bold": 0} or old format "A"
                            choice_letter = last_choice.get('choice', last_choice) if isinstance(last_choice, dict) else last_choice
                            step_key = str(len(choices_path) + 1) + str(choice_letter)
                            current_step_data = steps.get(step_key, {})

                    if not current_step_data:
                        return jsonify({
                            "error": f"Step {step_key} not found in narrative",
                            "available_steps": list(steps.keys())
                        }), 500

                    # Find the chosen option
                    choices_list = current_step_data.get('choices', [])
                    chosen_option = None
                    for opt in choices_list:
                        if opt.get('id', '').upper() == choice:
                            chosen_option = opt
                            break

                    if not chosen_option:
                        return jsonify({
                            "error": f"Choice {choice} not available in current step",
                            "available_choices": [c.get('id') for c in choices_list]
                        }), 400

                    # Get the next step and bold value for scoring
                    next_step = chosen_option.get('next', '')
                    bold_value = chosen_option.get('bold', 0)

                    # Update choices_path with choice and bold tracking
                    new_choices_path = choices_path + [{"choice": choice, "bold": bold_value}]

                    # Check if this leads to an ending
                    if next_step.startswith('END_') or next_step == 'CALC_END':
                        # Calculate ending based on scoring if CALC_END
                        if next_step == 'CALC_END':
                            # Calculate bold_score from all choices
                            total_bold = sum(c.get('bold', 0) if isinstance(c, dict) else 0 for c in new_choices_path)
                            total_steps = len(new_choices_path)
                            bold_ratio = total_bold / total_steps if total_steps > 0 else 0.5

                            # Determine ending based on bold_ratio
                            # 80%+ bold = LEGENDARY, 60%+ = PERFECT, 40%+ = GOOD, else NEUTRAL
                            if bold_ratio >= 0.8:
                                next_step = 'END_LEGENDARY'
                            elif bold_ratio >= 0.6:
                                next_step = 'END_PERFECT'
                            elif bold_ratio >= 0.4:
                                next_step = 'END_GOOD'
                            else:
                                next_step = 'END_NEUTRAL'

                            print(f"[MicroMission] CALC_END: bold_score={total_bold}/{total_steps}, ratio={bold_ratio:.2f}, ending={next_step}")

                        ending_data = endings.get(next_step, {})
                        ending_type = ending_data.get('type', 'NEUTRAL')
                        ending_text = ending_data.get('text', 'Your journey concludes...')

                        # Store ending info and mark ready for completion
                        cur.execute("""
                            UPDATE active_micro_missions SET
                                choices_path = %s,
                                ending_reached = %s,
                                outcome_text = %s,
                                status = 'choice_pending'
                            WHERE id = %s
                        """, (json.dumps(new_choices_path), next_step, ending_text, active_id))

                        return jsonify({
                            "success": True,
                            "choice": choice,
                            "ending_reached": True,
                            "ending_type": ending_type,
                            "ending_id": next_step,
                            "ending_text": ending_text,
                            "choices_path": new_choices_path,
                            "steps_completed": len(new_choices_path),
                            "message": "Mission complete! Claim your rewards now."
                        })
                    else:
                        # More steps to go - update current step
                        next_step_data = steps.get(next_step, {})
                        next_text = next_step_data.get('text', 'The story continues...')
                        next_choices = next_step_data.get('choices', [])

                        # Get total steps if available (for progress display)
                        total_steps = narrative_steps.get('total_steps', len(steps))

                        cur.execute("""
                            UPDATE active_micro_missions SET
                                current_step = %s,
                                choices_path = %s,
                                status = 'active'
                            WHERE id = %s
                        """, (next_step, json.dumps(new_choices_path), active_id))

                        return jsonify({
                            "success": True,
                            "choice": choice,
                            "ending_reached": False,
                            "current_step": next_step,
                            "step_number": len(new_choices_path) + 1,
                            "total_steps": total_steps,
                            "narrative_text": next_text,
                            "choices": next_choices,
                            "choices_path": new_choices_path,
                            "message": f"Step {len(new_choices_path) + 1} of {total_steps}"
                        })

        except Exception as e:
            print(f"Error recording choice: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/micro-mission/complete', methods=['POST'])
    def api_micro_mission_complete():
        """
        Complete a micro-mission and calculate rewards.

        Body: {
            "wallet": "0x...",
            "active_micro_mission_id": 123
        }
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()
        active_id = data.get('active_micro_mission_id')

        if not wallet or not active_id:
            return jsonify({"error": "Missing required fields"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get active mission details including multi-step narrative data
                    cur.execute("""
                        SELECT amm.id, amm.status, amm.emissary_token_id, amm.ends_at,
                               amm.choice_made, amm.outcome_text,
                               mm.pyre_reward_min, mm.pyre_reward_max,
                               mm.xp_reward_min, mm.xp_reward_max,
                               mm.aura_chance, mm.name, mm.narrative_outcomes,
                               COALESCE(mm.ember_reward_min, 0), COALESCE(mm.ember_reward_max, 0),
                               amm.ending_reached, mm.narrative_steps
                        FROM active_micro_missions amm
                        JOIN micro_missions mm ON amm.micro_mission_id = mm.id
                        WHERE amm.id = %s AND amm.wallet = %s
                    """, (active_id, wallet))
                    row = cur.fetchone()

                    if not row:
                        return jsonify({"error": "Active micro-mission not found"}), 404

                    if row[1] == 'completed':
                        return jsonify({"error": "Micro-mission already completed"}), 400

                    if row[1] == 'claimed':
                        return jsonify({"error": "Rewards already claimed"}), 400

                    # Extract ending data first to check completion status
                    ending_reached = row[15]
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    time_expired = now >= row[3]  # ends_at

                    # NEW FLOW:
                    # - If ending_reached → SUCCESS (immediate completion allowed)
                    # - If time_expired but no ending → FAILED (auto-fail)
                    # - If time not expired and no ending → still in progress

                    if not ending_reached and not time_expired:
                        remaining = (row[3] - now).total_seconds()
                        return jsonify({
                            "error": "Mission still in progress. Complete all steps or wait for timeout.",
                            "remaining_seconds": int(remaining)
                        }), 400

                    # Determine if mission is a success or failure
                    mission_failed = time_expired and not ending_reached
                    narrative_steps_raw = row[16]

                    # Parse narrative_steps if needed
                    if isinstance(narrative_steps_raw, str):
                        import json as json_module
                        try:
                            narrative_steps = json_module.loads(narrative_steps_raw)
                        except:
                            narrative_steps = {}
                    else:
                        narrative_steps = narrative_steps_raw or {}

                    endings = narrative_steps.get('endings', {}) if isinstance(narrative_steps, dict) else {}

                    token_id = row[2]
                    mission_name = row[11]

                    # Handle FAILED mission (timeout without completing)
                    if mission_failed:
                        xp_earned = 0
                        ember_earned = 0
                        aura_earned = 0
                        ending_type = 'FAILED'
                        outcome_text = "Time ran out! The mission has failed. Complete all steps faster next time."

                        # Update active mission as failed
                        cur.execute("""
                            UPDATE active_micro_missions SET
                                status = 'failed',
                                pyre_earned = 0,
                                xp_earned = 0,
                                aura_earned = 0
                            WHERE id = %s
                        """, (active_id,))

                        # Reset emissary to READY
                        cur.execute("""
                            UPDATE nfts SET
                                dynamic_state = jsonb_set(
                                    dynamic_state,
                                    '{state}',
                                    '"READY"'
                                ),
                                last_update = NOW()
                            WHERE token_id = %s
                        """, (token_id,))

                        print(f"[MicroMission] FAILED (timeout): {mission_name}")

                        return jsonify({
                            "success": True,
                            "completed": False,
                            "failed": True,
                            "rewards": {
                                "xp": 0,
                                "ember": 0,
                                "aura": 0
                            },
                            "mission_name": mission_name,
                            "outcome_text": outcome_text,
                            "ending_type": ending_type,
                            "emissary_token_id": token_id
                        })

                    # SUCCESS: Calculate rewards
                    xp_earned = random.randint(row[8], row[9])     # xp_reward_min/max
                    aura_earned = 1 if random.random() * 100 < float(row[10] or 0) else 0

                    # EMBER REWARD
                    ember_min = row[13] or 0
                    ember_max = row[14] or 0
                    ember_earned = random.randint(ember_min, ember_max) if ember_min > 0 and ember_max > 0 else 0

                    # Apply ending modifiers
                    ending_type = None
                    if ending_reached and ending_reached in endings:
                        ending_data = endings[ending_reached]
                        ending_type = ending_data.get('type', 'NEUTRAL')

                        xp_mod = ending_data.get('xp_mod', 1.0)
                        ember_mod = ending_data.get('ember_mod', 1.0)

                        xp_earned = int(xp_earned * xp_mod)
                        ember_earned = int(ember_earned * ember_mod)

                        # Aura boost for legendary endings
                        if ending_type == 'LEGENDARY' and aura_earned == 0:
                            aura_earned = 1 if random.random() < 0.5 else 0

                    outcome_text = row[5] or "The mission concludes successfully!"

                    # Update active mission (no pyre)
                    cur.execute("""
                        UPDATE active_micro_missions SET
                            status = 'completed',
                            pyre_earned = 0,
                            xp_earned = %s,
                            aura_earned = %s
                        WHERE id = %s
                    """, (xp_earned, aura_earned, active_id))

                    # Update emissary XP and aura
                    cur.execute("""
                        UPDATE nfts SET
                            dynamic_state = jsonb_set(
                                jsonb_set(
                                    jsonb_set(
                                        dynamic_state,
                                        '{state}',
                                        '"READY"'
                                    ),
                                    '{xp_total}',
                                    to_jsonb(COALESCE((dynamic_state->>'xp_total')::int, 0) + %s)
                                ),
                                '{aura_level}',
                                to_jsonb(COALESCE((dynamic_state->>'aura_level')::int, 0) + %s)
                            ),
                            last_update = NOW()
                        WHERE token_id = %s
                    """, (xp_earned, aura_earned, token_id))

                    # Add $EMBER to wallet (if earned)
                    if ember_earned > 0:
                        cur.execute("""
                            INSERT INTO user_balances (wallet, ember_balance, total_ember_earned, created_at, last_update)
                            VALUES (%s, %s, %s, NOW(), NOW())
                            ON CONFLICT (wallet) DO UPDATE SET
                                ember_balance = user_balances.ember_balance + EXCLUDED.ember_balance,
                                total_ember_earned = COALESCE(user_balances.total_ember_earned, 0) + EXCLUDED.total_ember_earned,
                                last_update = NOW()
                        """, (wallet, ember_earned, ember_earned))
                        print(f"[MicroMission] EMBER +{ember_earned} for {wallet}")

                    print(f"[MicroMission] Complete: {mission_name} -> XP:{xp_earned}, EMBER:{ember_earned}, AURA:{aura_earned}")

                    # Set 24-hour cooldown for this emissary/mission combo
                    cooldown_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)
                    cur.execute("""
                        INSERT INTO micro_mission_cooldowns (emissary_token_id, mission_id, cooldown_until)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (emissary_token_id, mission_id) DO UPDATE SET
                            cooldown_until = EXCLUDED.cooldown_until
                    """, (token_id, row[2], cooldown_until))

                    return jsonify({
                        "success": True,
                        "completed": True,
                        "rewards": {
                            "xp": xp_earned,
                            "ember": ember_earned,
                            "aura": aura_earned
                        },
                        "mission_name": mission_name,
                        "outcome_text": outcome_text,
                        "ending_type": ending_type,
                        "ending_reached": ending_reached,
                        "emissary_token_id": token_id,
                        "cooldown_hours": 24
                    })

        except Exception as e:
            print(f"Error completing micro-mission: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/micro-mission/abandon', methods=['POST'])
    def api_micro_mission_abandon():
        """
        Abandon an active micro-mission with XP penalty based on difficulty.

        Body: {
            "wallet": "0x...",
            "active_micro_mission_id": 123
        }

        Penalty by difficulty:
        - EASY: -5 XP
        - MEDIUM: -10 XP
        - HARD: -15 XP
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()
        active_id = data.get('active_micro_mission_id')

        if not wallet or not active_id:
            return jsonify({"error": "Missing required fields"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        # XP penalty by difficulty
        XP_PENALTY_MAP = {
            'EASY': 5,
            'MEDIUM': 10,
            'HARD': 15
        }

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Verify ownership, status, and get difficulty
                    cur.execute("""
                        SELECT amm.id, amm.status, amm.emissary_token_id, mm.name, mm.difficulty
                        FROM active_micro_missions amm
                        JOIN micro_missions mm ON amm.micro_mission_id = mm.id
                        WHERE amm.id = %s AND amm.wallet = %s
                    """, (active_id, wallet))
                    row = cur.fetchone()

                    if not row:
                        return jsonify({"error": "Active micro-mission not found"}), 404

                    if row[1] not in ['active', 'choice_pending']:
                        return jsonify({"error": f"Cannot abandon mission in status: {row[1]}"}), 400

                    token_id = row[2]
                    mission_name = row[3]
                    difficulty = row[4] or 'EASY'
                    xp_penalty = XP_PENALTY_MAP.get(difficulty, 10)

                    # Mark as abandoned
                    cur.execute("""
                        UPDATE active_micro_missions SET
                            status = 'abandoned',
                            completed_at = NOW()
                        WHERE id = %s
                    """, (active_id,))

                    # Apply XP penalty to nfts table using dynamic_state JSONB
                    # Pad token_id to 5 digits for consistency
                    token_id_padded = str(token_id).zfill(5)
                    cur.execute("""
                        UPDATE nfts SET
                            dynamic_state = jsonb_set(
                                COALESCE(dynamic_state, '{}'::jsonb),
                                '{xp_total}',
                                to_jsonb(GREATEST(0, COALESCE((dynamic_state->>'xp_total')::int, 0) - %s))
                            ),
                            last_update = NOW()
                        WHERE token_id = %s
                    """, (xp_penalty, token_id_padded))

                    # Record in history
                    cur.execute("""
                        INSERT INTO micro_mission_history
                        (wallet, emissary_token_id, micro_mission_id, outcome_type, xp_earned)
                        SELECT wallet, emissary_token_id, micro_mission_id, 'abandoned', %s
                        FROM active_micro_missions WHERE id = %s
                    """, (-xp_penalty, active_id))

                    return jsonify({
                        "success": True,
                        "abandoned": True,
                        "mission_name": mission_name,
                        "difficulty": difficulty,
                        "xp_penalty": xp_penalty,
                        "message": f"Mission abandoned. You lost {xp_penalty} XP."
                    })

        except Exception as e:
            print(f"Error abandoning micro-mission: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/micro-mission/active/<wallet>', methods=['GET'])
    def api_micro_mission_active(wallet):
        """Get active micro-mission for a wallet with multi-step adventure support"""
        wallet = wallet.lower()

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Include current_step, choices_path, ending_reached for multi-step
                    cur.execute("""
                        SELECT amm.id, amm.emissary_token_id, amm.micro_mission_id,
                               amm.started_at, amm.ends_at, amm.status, amm.choice_made,
                               mm.name, mm.narrative_intro, mm.narrative_choices,
                               COALESCE(amm.current_step, '1') as current_step,
                               COALESCE(amm.choices_path, '[]'::jsonb) as choices_path,
                               amm.ending_reached, amm.outcome_text,
                               mm.narrative_steps
                        FROM active_micro_missions amm
                        JOIN micro_missions mm ON amm.micro_mission_id = mm.id
                        WHERE amm.wallet = %s AND amm.status IN ('active', 'choice_pending')
                        ORDER BY amm.started_at DESC
                        LIMIT 1
                    """, (wallet,))
                    row = cur.fetchone()

                    if not row:
                        return jsonify({
                            "success": True,
                            "active": False,
                            "message": "No active micro-mission"
                        })

                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    remaining = max(0, (row[4] - now).total_seconds())

                    # Extract current step data from narrative_steps
                    current_step = str(row[10]) if row[10] else "1"
                    choices_path = row[11] if row[11] else []
                    ending_reached = row[12]
                    outcome_text = row[13]
                    narrative_steps_raw = row[14]

                    # Parse narrative_steps if it's a string
                    if isinstance(narrative_steps_raw, str):
                        import json as json_module
                        try:
                            narrative_steps = json_module.loads(narrative_steps_raw)
                        except:
                            narrative_steps = {}
                    else:
                        narrative_steps = narrative_steps_raw or {}

                    steps = narrative_steps.get('steps', {}) if isinstance(narrative_steps, dict) else {}
                    endings = narrative_steps.get('endings', {}) if isinstance(narrative_steps, dict) else {}

                    # FALLBACK: If no steps defined, use generic narrative
                    if not steps:
                        steps = {
                            "1": {
                                "text": "Your emissary embarks on the mission. The path ahead is uncertain.",
                                "choices": [
                                    {"id": "A", "text": "Take the cautious approach", "next": "2A"},
                                    {"id": "B", "text": "Act boldly and decisively", "next": "2B"}
                                ]
                            },
                            "2A": {
                                "text": "Your careful approach pays off. You make steady progress.",
                                "choices": [
                                    {"id": "A", "text": "Continue with caution", "next": "END_GOOD"},
                                    {"id": "B", "text": "Take a calculated risk", "next": "END_PERFECT"}
                                ]
                            },
                            "2B": {
                                "text": "Your boldness is rewarded! Opportunities present themselves.",
                                "choices": [
                                    {"id": "A", "text": "Press your advantage", "next": "END_LEGENDARY"},
                                    {"id": "B", "text": "Consolidate your gains", "next": "END_GOOD"}
                                ]
                            }
                        }
                        endings = {
                            "END_LEGENDARY": {"type": "LEGENDARY", "text": "Outstanding success!", "pyre_mod": 2.0, "xp_mod": 2.0},
                            "END_PERFECT": {"type": "PERFECT", "text": "Excellent work!", "pyre_mod": 1.5, "xp_mod": 1.4},
                            "END_GOOD": {"type": "GOOD", "text": "Well done!", "pyre_mod": 1.2, "xp_mod": 1.2},
                            "END_NEUTRAL": {"type": "NEUTRAL", "text": "Mission complete.", "pyre_mod": 1.0, "xp_mod": 1.0}
                        }

                    # Get total steps from narrative
                    total_steps = narrative_steps.get('total_steps', len(steps)) if isinstance(narrative_steps, dict) else len(steps)

                    # Determine what to show based on current state
                    if ending_reached:
                        # Show ending text and no more choices
                        ending_data = endings.get(ending_reached, {})
                        narrative_text = outcome_text or ending_data.get('text', 'Your journey concludes...')
                        choices = []  # No more choices at ending
                        ending_type = ending_data.get('type', 'NEUTRAL')
                    else:
                        # Show current step text and choices
                        current_step_data = steps.get(current_step, {})
                        if current_step_data:
                            narrative_text = current_step_data.get('text', row[8] or 'Your journey continues...')
                            choices = current_step_data.get('choices', row[9] or [])
                        elif row[8] or row[9]:
                            # Fallback to legacy fields
                            narrative_text = row[8] or 'Your journey begins...'
                            choices = row[9] or []
                        else:
                            # Generic fallback
                            narrative_text = "Your emissary is on a mission. Make your choice."
                            choices = [
                                {"id": "A", "text": "Take the cautious approach", "next": "2A"},
                                {"id": "B", "text": "Act boldly and decisively", "next": "2B"}
                            ]
                        ending_type = None

                    # Calculate current step number from choices_path
                    step_number = len(choices_path) + 1 if choices_path else 1

                    return jsonify({
                        "success": True,
                        "active": True,
                        "micro_mission": {
                            "active_id": row[0],
                            "emissary_token_id": row[1],
                            "mission_id": row[2],
                            "started_at": row[3].isoformat() if row[3] else None,
                            "ends_at": row[4].isoformat() if row[4] else None,
                            "remaining_seconds": int(remaining),
                            "status": row[5],
                            "choice_made": row[6],
                            "name": row[7],
                            "narrative_intro": narrative_text,
                            "choices": choices,
                            "current_step": current_step,
                            "step_number": step_number,
                            "total_steps": total_steps,
                            "choices_path": choices_path,
                            "ending_reached": ending_reached,
                            "ending_type": ending_type
                        }
                    })

        except Exception as e:
            print(f"Error getting active micro-mission: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/micro-mission/emergency-cleanup', methods=['POST'])
    def api_micro_mission_emergency_cleanup():
        """
        EMERGENCY: Force reload ALL narratives and fix ALL durations.
        Deletes all active missions and resets all emissaries.
        """
        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    results = {}

                    # 1. Delete ALL active micro-missions
                    cur.execute("DELETE FROM active_micro_missions WHERE status IN ('active', 'choice_pending')")
                    results['deleted_missions'] = cur.rowcount

                    # 2. Reset ALL emissaries from ON_MICRO_MISSION to READY
                    cur.execute("""
                        UPDATE nfts SET
                            dynamic_state = jsonb_set(
                                COALESCE(dynamic_state, '{}'::jsonb),
                                '{state}',
                                '"READY"'
                            ),
                            last_update = NOW()
                        WHERE dynamic_state->>'state' = 'ON_MICRO_MISSION'
                    """)
                    results['emissaries_reset'] = cur.rowcount

                    # 3. Recreate cooldowns table with correct schema
                    cur.execute("DROP TABLE IF EXISTS micro_mission_cooldowns CASCADE")
                    cur.execute("""
                        CREATE TABLE micro_mission_cooldowns (
                            id SERIAL PRIMARY KEY,
                            emissary_token_id VARCHAR(10) NOT NULL,
                            mission_id VARCHAR(20) NOT NULL,
                            cooldown_until TIMESTAMP NOT NULL,
                            UNIQUE(emissary_token_id, mission_id)
                        )
                    """)
                    results['cooldowns_table_recreated'] = True

                    # 4. Force update ALL durations
                    cur.execute("UPDATE micro_missions SET duration_seconds = 120 WHERE difficulty = 'EASY'")
                    cur.execute("UPDATE micro_missions SET duration_seconds = 180 WHERE difficulty = 'MEDIUM'")
                    cur.execute("UPDATE micro_missions SET duration_seconds = 300 WHERE difficulty = 'HARD'")
                    results['durations_fixed'] = True

                    # 4. Load narratives from narrative_data.py
                    narratives = get_all_narratives()
                    categories = MISSION_CATEGORIES

                    for mission_id, narrative in narratives.items():
                        category = categories.get(mission_id, 'PATROL')
                        cur.execute("""
                            UPDATE micro_missions
                            SET narrative_steps = %s::jsonb, category = %s
                            WHERE id = %s
                        """, (json.dumps(narrative), category, mission_id))

                    results['narratives_loaded'] = len(narratives)

                    # 5. Verify narratives loaded correctly
                    cur.execute("""
                        SELECT id,
                               (narrative_steps->'total_steps')::int as total_steps,
                               difficulty,
                               duration_seconds
                        FROM micro_missions
                        WHERE id LIKE 'MM-%%'
                        ORDER BY id
                    """)
                    missions = []
                    for row in cur.fetchall():
                        missions.append({
                            "id": row[0],
                            "total_steps": row[1],
                            "difficulty": row[2],
                            "duration_seconds": row[3]
                        })
                    results['missions'] = missions

                    return jsonify({
                        "success": True,
                        "results": results,
                        "message": f"Emergency cleanup complete! Loaded {len(narratives)} narratives with correct step counts."
                    })

        except Exception as e:
            print(f"Error in emergency cleanup: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    # =====================================================================
    # EMISSARY FULL STATUS
    # =====================================================================

    @app.route('/api/emissary/<token_id>/full-status', methods=['GET'])
    def api_emissary_full_status(token_id):
        """
        Get complete status of an emissary including:
        - Basic stats
        - Current state (READY, ON_MISSION, ON_MICRO_MISSION, FALLEN, CLAIMING)
        - Active mission info (if any)
        - Active micro-mission info (if any)
        - Equipment summary
        - Chronicle summary
        """
        token_id = str(token_id).zfill(5)

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get NFT data
                    cur.execute("""
                        SELECT token_id, name, guild, race_class, last_known_owner,
                               image_url, dynamic_state,
                               weapon_id, armor_id, helmet_id, accessory_id, amulet_id, rune_ids
                        FROM nfts WHERE token_id = %s
                    """, (token_id,))
                    nft = cur.fetchone()

                    if not nft:
                        return jsonify({"error": "Emissary not found"}), 404

                    dynamic_state = nft[6] or {}

                    # Get current state
                    state, active_id, ends_at = get_emissary_state(token_id)

                    # Get active mission details if ON_MISSION
                    active_mission = None
                    if state == "ON_MISSION" or state == "CLAIMING":
                        cur.execute("""
                            SELECT mission_id, start_time, duration_hours
                            FROM active_missions WHERE hero_id = %s
                        """, (token_id,))
                        mission_row = cur.fetchone()
                        if mission_row:
                            mission_end = mission_row[1] + timedelta(hours=mission_row[2])
                            now = datetime.now(timezone.utc).replace(tzinfo=None)
                            active_mission = {
                                "mission_id": mission_row[0],
                                "started_at": mission_row[1].isoformat(),
                                "ends_at": mission_end.isoformat(),
                                "remaining_seconds": max(0, (mission_end - now).total_seconds())
                            }

                    # Get active micro-mission details if ON_MICRO_MISSION
                    active_micro = None
                    if state == "ON_MICRO_MISSION":
                        cur.execute("""
                            SELECT amm.id, amm.micro_mission_id, amm.started_at, amm.ends_at,
                                   amm.status, amm.choice_made, mm.name
                            FROM active_micro_missions amm
                            JOIN micro_missions mm ON amm.micro_mission_id = mm.id
                            WHERE amm.emissary_token_id = %s
                            AND amm.status IN ('active', 'choice_pending')
                        """, (token_id,))
                        micro_row = cur.fetchone()
                        if micro_row:
                            now = datetime.now(timezone.utc).replace(tzinfo=None)
                            active_micro = {
                                "active_id": micro_row[0],
                                "mission_id": micro_row[1],
                                "mission_name": micro_row[6],
                                "started_at": micro_row[2].isoformat() if micro_row[2] else None,
                                "ends_at": micro_row[3].isoformat() if micro_row[3] else None,
                                "remaining_seconds": max(0, (micro_row[3] - now).total_seconds()) if micro_row[3] else 0,
                                "status": micro_row[4],
                                "choice_made": micro_row[5]
                            }

                    # Build response
                    return jsonify({
                        "success": True,
                        "emissary": {
                            "token_id": nft[0],
                            "name": nft[1],
                            "guild": nft[2],
                            "race_class": nft[3],
                            "owner": nft[4],
                            "image_url": nft[5],
                            "stats": {
                                "level": dynamic_state.get('xp_level', 1),
                                "xp_total": dynamic_state.get('xp_total', 0),
                                "aura_level": dynamic_state.get('aura_level', 0),
                                "energy_current": dynamic_state.get('energy_current', 100),
                                "energy_max": dynamic_state.get('energy_max', 100),
                                "power": dynamic_state.get('power_current', 10),
                                "death_count": dynamic_state.get('death_count', 0)
                            },
                            "current_state": state,
                            "active_mission": active_mission,
                            "active_micro_mission": active_micro,
                            "equipment": {
                                "weapon_id": nft[7],
                                "armor_id": nft[8],
                                "helmet_id": nft[9],
                                "accessory_id": nft[10],
                                "amulet_id": nft[11],
                                "rune_ids": nft[12] or []
                            },
                            "chronicle": {
                                "total_missions": dynamic_state.get('total_missions_completed', 0),
                                "total_deaths": dynamic_state.get('death_count', 0),
                                "items_found": dynamic_state.get('items_found', 0),
                                "runes_found": dynamic_state.get('runes_found', 0)
                            }
                        }
                    })

        except Exception as e:
            print(f"Error getting emissary full status: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    # =====================================================================
    # SOCIAL ENDPOINTS (Chat 1:1)
    # =====================================================================

    @app.route('/api/social/profile', methods=['POST'])
    def api_social_profile_update():
        """
        Create or update user profile (country, display name, etc.)

        Body: {
            "wallet": "0x...",
            "country_code": "USA",
            "display_name": "Player123",
            "farcaster_fid": 12345,
            "farcaster_username": "player123",
            "farcaster_pfp_url": "https://..."
        }
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()
        country_code = data.get('country_code', '').upper()[:3]
        display_name = data.get('display_name', '')
        fid = data.get('farcaster_fid')
        username = data.get('farcaster_username', '')
        pfp_url = data.get('farcaster_pfp_url', '')

        if not wallet:
            return jsonify({"error": "Wallet required"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Ensure table exists
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS user_profiles (
                            id SERIAL PRIMARY KEY,
                            wallet VARCHAR(42) UNIQUE NOT NULL,
                            farcaster_fid INTEGER,
                            farcaster_username VARCHAR(100),
                            farcaster_pfp_url TEXT,
                            country_code CHAR(3),
                            display_name VARCHAR(100),
                            last_seen TIMESTAMP DEFAULT NOW(),
                            created_at TIMESTAMP DEFAULT NOW()
                        )
                    """)

                    cur.execute("""
                        INSERT INTO user_profiles
                        (wallet, country_code, display_name, farcaster_fid, farcaster_username, farcaster_pfp_url)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (wallet) DO UPDATE SET
                            country_code = COALESCE(EXCLUDED.country_code, user_profiles.country_code),
                            display_name = COALESCE(EXCLUDED.display_name, user_profiles.display_name),
                            farcaster_fid = COALESCE(EXCLUDED.farcaster_fid, user_profiles.farcaster_fid),
                            farcaster_username = COALESCE(EXCLUDED.farcaster_username, user_profiles.farcaster_username),
                            farcaster_pfp_url = COALESCE(EXCLUDED.farcaster_pfp_url, user_profiles.farcaster_pfp_url),
                            last_seen = NOW()
                        RETURNING id, wallet, country_code, display_name, farcaster_username
                    """, (wallet, country_code or None, display_name or None, fid, username or None, pfp_url or None))
                    row = cur.fetchone()

                    print(f"[Social] Profile updated for {wallet[:10]}...: country={country_code}")

                    return jsonify({
                        "success": True,
                        "profile": {
                            "id": row[0],
                            "wallet": row[1],
                            "country_code": row[2],
                            "display_name": row[3],
                            "farcaster_username": row[4]
                        }
                    })

        except Exception as e:
            print(f"Error updating profile: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/profile/<wallet>', methods=['GET'])
    def api_social_profile_get(wallet):
        """Get user profile"""
        wallet = wallet.lower()

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Ensure table exists
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS user_profiles (
                            id SERIAL PRIMARY KEY,
                            wallet VARCHAR(42) UNIQUE NOT NULL,
                            farcaster_fid INTEGER,
                            farcaster_username VARCHAR(100),
                            farcaster_pfp_url TEXT,
                            country_code CHAR(3),
                            display_name VARCHAR(100),
                            last_seen TIMESTAMP DEFAULT NOW(),
                            created_at TIMESTAMP DEFAULT NOW()
                        )
                    """)

                    cur.execute("""
                        SELECT id, wallet, country_code, display_name,
                               farcaster_fid, farcaster_username, farcaster_pfp_url, last_seen
                        FROM user_profiles WHERE wallet = %s
                    """, (wallet,))
                    row = cur.fetchone()

                    if not row:
                        return jsonify({"success": True, "profile": None})

                    # Trim whitespace from CHAR(3) country_code
                    country_code = row[2].strip() if row[2] else None

                    return jsonify({
                        "success": True,
                        "profile": {
                            "id": row[0],
                            "wallet": row[1],
                            "country_code": country_code,
                            "display_name": row[3],
                            "farcaster_fid": row[4],
                            "farcaster_username": row[5],
                            "farcaster_pfp_url": row[6],
                            "last_seen": row[7].isoformat() if row[7] else None
                        }
                    })

        except Exception as e:
            print(f"Error getting profile: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/countries', methods=['GET'])
    def api_social_countries():
        """Get list of countries with user counts (for 3D globe)"""
        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT country_code,
                               COUNT(*) as user_count,
                               COUNT(CASE WHEN last_seen > NOW() - INTERVAL '15 minutes' THEN 1 END) as online_count
                        FROM user_profiles
                        WHERE country_code IS NOT NULL
                        GROUP BY country_code
                        ORDER BY user_count DESC
                    """)
                    rows = cur.fetchall()

                    countries = []
                    for row in rows:
                        countries.append({
                            "country_code": row[0],
                            "user_count": row[1],
                            "online_count": row[2]
                        })

                    return jsonify({
                        "success": True,
                        "countries": countries,
                        "total_countries": len(countries)
                    })

        except Exception as e:
            print(f"Error getting countries: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/country/<country_code>/users', methods=['GET'])
    def api_social_country_users(country_code):
        """Get users from a specific country"""
        country_code = country_code.upper()[:3]
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT wallet, display_name, farcaster_username, farcaster_pfp_url, last_seen,
                               (last_seen > NOW() - INTERVAL '15 minutes') as is_online
                        FROM user_profiles
                        WHERE country_code = %s
                        ORDER BY last_seen DESC
                        LIMIT %s OFFSET %s
                    """, (country_code, limit, offset))
                    rows = cur.fetchall()

                    users = []
                    for row in rows:
                        users.append({
                            "wallet": row[0],
                            "display_name": row[1],
                            "farcaster_username": row[2],
                            "farcaster_pfp_url": row[3],
                            "last_seen": row[4].isoformat() if row[4] else None,
                            "is_online": row[5]
                        })

                    return jsonify({
                        "success": True,
                        "country_code": country_code,
                        "users": users,
                        "count": len(users)
                    })

        except Exception as e:
            print(f"Error getting country users: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/conversations/<wallet>', methods=['GET'])
    def api_social_conversations(wallet):
        """Get list of conversations for a wallet"""
        wallet = wallet.lower()

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get all unique conversations with last message
                    cur.execute("""
                        WITH conversations AS (
                            SELECT
                                CASE
                                    WHEN from_wallet = %s THEN to_wallet
                                    ELSE from_wallet
                                END as other_wallet,
                                message,
                                created_at,
                                CASE WHEN to_wallet = %s AND read = FALSE THEN 1 ELSE 0 END as unread
                            FROM private_messages
                            WHERE from_wallet = %s OR to_wallet = %s
                            ORDER BY created_at DESC
                        ),
                        latest AS (
                            SELECT DISTINCT ON (other_wallet)
                                other_wallet, message, created_at
                            FROM conversations
                            ORDER BY other_wallet, created_at DESC
                        ),
                        unread_counts AS (
                            SELECT other_wallet, SUM(unread) as unread_count
                            FROM conversations
                            GROUP BY other_wallet
                        )
                        SELECT l.other_wallet, l.message, l.created_at,
                               COALESCE(u.unread_count, 0) as unread_count,
                               p.display_name, p.farcaster_username, p.farcaster_pfp_url
                        FROM latest l
                        LEFT JOIN unread_counts u ON l.other_wallet = u.other_wallet
                        LEFT JOIN user_profiles p ON l.other_wallet = p.wallet
                        ORDER BY l.created_at DESC
                    """, (wallet, wallet, wallet, wallet))
                    rows = cur.fetchall()

                    conversations = []
                    for row in rows:
                        conversations.append({
                            "other_wallet": row[0],
                            "last_message": row[1][:100] if row[1] else None,
                            "last_message_at": row[2].isoformat() if row[2] else None,
                            "unread_count": row[3],
                            "other_user": {
                                "display_name": row[4],
                                "farcaster_username": row[5],
                                "farcaster_pfp_url": row[6]
                            }
                        })

                    return jsonify({
                        "success": True,
                        "conversations": conversations,
                        "count": len(conversations)
                    })

        except Exception as e:
            print(f"Error getting conversations: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/messages/<wallet>/<other_wallet>', methods=['GET'])
    def api_social_messages(wallet, other_wallet):
        """Get messages between two wallets"""
        wallet = wallet.lower()
        other_wallet = other_wallet.lower()
        limit = request.args.get('limit', 50, type=int)
        before_id = request.args.get('before_id', type=int)

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get messages
                    if before_id:
                        cur.execute("""
                            SELECT id, from_wallet, to_wallet, message, read, created_at
                            FROM private_messages
                            WHERE ((from_wallet = %s AND to_wallet = %s)
                                   OR (from_wallet = %s AND to_wallet = %s))
                              AND id < %s
                            ORDER BY created_at DESC
                            LIMIT %s
                        """, (wallet, other_wallet, other_wallet, wallet, before_id, limit))
                    else:
                        cur.execute("""
                            SELECT id, from_wallet, to_wallet, message, read, created_at
                            FROM private_messages
                            WHERE (from_wallet = %s AND to_wallet = %s)
                               OR (from_wallet = %s AND to_wallet = %s)
                            ORDER BY created_at DESC
                            LIMIT %s
                        """, (wallet, other_wallet, other_wallet, wallet, limit))
                    rows = cur.fetchall()

                    messages = []
                    for row in rows:
                        messages.append({
                            "id": row[0],
                            "from_wallet": row[1],
                            "to_wallet": row[2],
                            "message": row[3],
                            "read": row[4],
                            "created_at": row[5].isoformat() if row[5] else None,
                            "is_mine": row[1] == wallet
                        })

                    # Mark messages as read
                    cur.execute("""
                        UPDATE private_messages SET read = TRUE
                        WHERE from_wallet = %s AND to_wallet = %s AND read = FALSE
                    """, (other_wallet, wallet))

                    return jsonify({
                        "success": True,
                        "messages": list(reversed(messages)),  # Chronological order
                        "count": len(messages)
                    })

        except Exception as e:
            print(f"Error getting messages: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/message', methods=['POST'])
    def api_social_send_message():
        """
        Send a private message

        Body: {
            "from_wallet": "0x...",
            "to_wallet": "0x...",
            "message": "Hello!"
        }
        """
        data = request.get_json() or {}
        from_wallet = data.get('from_wallet', '').lower()
        to_wallet = data.get('to_wallet', '').lower()
        message = data.get('message', '').strip()

        if not from_wallet or not to_wallet:
            return jsonify({"error": "Both wallets required"}), 400

        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400

        if len(message) > 1000:
            return jsonify({"error": "Message too long (max 1000 chars)"}), 400

        if from_wallet == to_wallet:
            return jsonify({"error": "Cannot message yourself"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Insert message
                    cur.execute("""
                        INSERT INTO private_messages (from_wallet, to_wallet, message)
                        VALUES (%s, %s, %s)
                        RETURNING id, created_at
                    """, (from_wallet, to_wallet, message))
                    row = cur.fetchone()

                    # Update sender's last_seen
                    cur.execute("""
                        UPDATE user_profiles SET last_seen = NOW()
                        WHERE wallet = %s
                    """, (from_wallet,))

                    return jsonify({
                        "success": True,
                        "message": {
                            "id": row[0],
                            "from_wallet": from_wallet,
                            "to_wallet": to_wallet,
                            "message": message,
                            "created_at": row[1].isoformat() if row[1] else None
                        }
                    })

        except Exception as e:
            print(f"Error sending message: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/message/read', methods=['POST'])
    def api_social_mark_read():
        """
        Mark messages as read

        Body: {
            "wallet": "0x...",       // The reader
            "from_wallet": "0x..."   // The sender
        }
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()
        from_wallet = data.get('from_wallet', '').lower()

        if not wallet or not from_wallet:
            return jsonify({"error": "Both wallets required"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE private_messages SET read = TRUE
                        WHERE from_wallet = %s AND to_wallet = %s AND read = FALSE
                        RETURNING id
                    """, (from_wallet, wallet))
                    rows = cur.fetchall()

                    return jsonify({
                        "success": True,
                        "marked_read": len(rows)
                    })

        except Exception as e:
            print(f"Error marking read: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/online-stats', methods=['GET'])
    def api_social_online_stats():
        """Get global online statistics"""
        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            COUNT(*) as total_users,
                            COUNT(CASE WHEN last_seen > NOW() - INTERVAL '15 minutes' THEN 1 END) as online_now,
                            COUNT(DISTINCT country_code) as countries_represented
                        FROM user_profiles
                    """)
                    row = cur.fetchone()

                    return jsonify({
                        "success": True,
                        "stats": {
                            "total_users": row[0],
                            "online_now": row[1],
                            "countries_represented": row[2]
                        }
                    })

        except Exception as e:
            print(f"Error getting online stats: {e}")
            return jsonify({"error": str(e)}), 500

    # =========================================================================
    # SOCIAL REWARDS ENDPOINTS ($EMBER rewards for social actions)
    # =========================================================================

    # Social reward amounts (in $EMBER)
    SOCIAL_REWARDS = {
        'daily_login': 0.5,
        'streak_7': 5.0,
        'streak_30': 25.0,
        'referral': 2.0,
        'share': 0.1,
        'tutorial': 3.0,
        'first_mint': 5.0
    }

    # Daily limits
    SOCIAL_LIMITS = {
        'referral': 10,  # max referrals per day
        'share': 5       # max shares per day
    }

    @app.route('/api/social/daily-login', methods=['POST'])
    def api_social_daily_login():
        """
        Process daily login and award EMBER.
        Also handles streak tracking and streak milestone rewards.

        Body: { "wallet": "0x..." }
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()

        if not wallet:
            return jsonify({"error": "Missing wallet"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    today = datetime.now(timezone.utc).date()

                    # Get or create user streak record
                    cur.execute("""
                        INSERT INTO user_streaks (wallet, current_streak, last_login_date, created_at)
                        VALUES (%s, 0, NULL, NOW())
                        ON CONFLICT (wallet) DO NOTHING
                    """, (wallet,))

                    cur.execute("""
                        SELECT current_streak, last_login_date, streak_7_claimed_at, streak_30_claimed_at
                        FROM user_streaks WHERE wallet = %s
                    """, (wallet,))
                    streak_row = cur.fetchone()

                    current_streak = streak_row[0] or 0
                    last_login = streak_row[1]
                    streak_7_claimed = streak_row[2]
                    streak_30_claimed = streak_row[3]

                    total_ember_earned = 0
                    rewards_given = []

                    # Check if already logged in today
                    if last_login == today:
                        return jsonify({
                            "success": True,
                            "already_claimed": True,
                            "current_streak": current_streak,
                            "ember_earned": 0,
                            "message": "Already claimed today's login reward"
                        })

                    # Calculate new streak
                    yesterday = today - timedelta(days=1)
                    if last_login == yesterday:
                        # Consecutive day
                        new_streak = current_streak + 1
                    elif last_login is None:
                        # First login ever
                        new_streak = 1
                    else:
                        # Streak broken
                        new_streak = 1

                    # Award daily login EMBER
                    daily_ember = SOCIAL_REWARDS['daily_login']
                    total_ember_earned += daily_ember
                    rewards_given.append({'type': 'daily_login', 'ember': daily_ember})

                    # Check for streak 7 milestone
                    if new_streak >= 7:
                        # Check if already claimed this week
                        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
                        if streak_7_claimed is None or streak_7_claimed < week_ago:
                            streak_7_ember = SOCIAL_REWARDS['streak_7']
                            total_ember_earned += streak_7_ember
                            rewards_given.append({'type': 'streak_7', 'ember': streak_7_ember})
                            cur.execute("""
                                UPDATE user_streaks SET streak_7_claimed_at = NOW() WHERE wallet = %s
                            """, (wallet,))

                    # Check for streak 30 milestone
                    if new_streak >= 30:
                        # Check if already claimed this month
                        month_ago = datetime.now(timezone.utc) - timedelta(days=30)
                        if streak_30_claimed is None or streak_30_claimed < month_ago:
                            streak_30_ember = SOCIAL_REWARDS['streak_30']
                            total_ember_earned += streak_30_ember
                            rewards_given.append({'type': 'streak_30', 'ember': streak_30_ember})
                            cur.execute("""
                                UPDATE user_streaks SET streak_30_claimed_at = NOW() WHERE wallet = %s
                            """, (wallet,))

                    # Update streak
                    cur.execute("""
                        UPDATE user_streaks SET
                            current_streak = %s,
                            longest_streak = GREATEST(longest_streak, %s),
                            last_login_date = %s,
                            updated_at = NOW()
                        WHERE wallet = %s
                    """, (new_streak, new_streak, today, wallet))

                    # Add EMBER to balance
                    if total_ember_earned > 0:
                        cur.execute("""
                            INSERT INTO user_balances (wallet, ember_balance, total_ember_earned, created_at, last_update)
                            VALUES (%s, %s, %s, NOW(), NOW())
                            ON CONFLICT (wallet) DO UPDATE SET
                                ember_balance = user_balances.ember_balance + EXCLUDED.ember_balance,
                                total_ember_earned = COALESCE(user_balances.total_ember_earned, 0) + EXCLUDED.total_ember_earned,
                                last_update = NOW()
                        """, (wallet, total_ember_earned, total_ember_earned))

                        # Log each reward
                        for reward in rewards_given:
                            cur.execute("""
                                INSERT INTO social_rewards_log (wallet, action_type, ember_earned, description)
                                VALUES (%s, %s, %s, %s)
                            """, (wallet, reward['type'], reward['ember'], f"Streak day {new_streak}"))

                    # Calculate next milestone
                    if new_streak < 7:
                        next_milestone = 7
                        days_to_next = 7 - new_streak
                    elif new_streak < 30:
                        next_milestone = 30
                        days_to_next = 30 - new_streak
                    else:
                        next_milestone = new_streak + (30 - (new_streak % 30))
                        days_to_next = next_milestone - new_streak

                    return jsonify({
                        "success": True,
                        "current_streak": new_streak,
                        "ember_earned": total_ember_earned,
                        "rewards": rewards_given,
                        "next_milestone": next_milestone,
                        "days_to_next": days_to_next,
                        "message": "The Flame welcomes you back, Operator."
                    })

        except Exception as e:
            print(f"Error processing daily login: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/tutorial-complete', methods=['POST'])
    def api_social_tutorial_complete():
        """
        Award EMBER for completing the tutorial.
        Can only be claimed once per wallet.

        Body: {
            "wallet": "0x...",
            "sections_completed": ["intro", "missions", "vault", "emissary", "pyre", "lore"]
        }
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()
        sections = data.get('sections_completed', [])

        if not wallet:
            return jsonify({"error": "Missing wallet"}), 400

        # Required sections to complete tutorial
        required_sections = {'intro', 'missions', 'vault', 'emissary', 'pyre', 'lore'}
        completed_sections = set(sections)

        if not required_sections.issubset(completed_sections):
            missing = required_sections - completed_sections
            return jsonify({
                "error": "Tutorial not complete",
                "missing_sections": list(missing)
            }), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if already completed
                    cur.execute("""
                        SELECT tutorial_completed FROM user_streaks WHERE wallet = %s
                    """, (wallet,))
                    row = cur.fetchone()

                    if row and row[0]:
                        return jsonify({
                            "success": True,
                            "already_completed": True,
                            "ember_earned": 0,
                            "message": "Tutorial already completed"
                        })

                    # Award EMBER
                    ember_reward = SOCIAL_REWARDS['tutorial']

                    # Update/create streak record
                    cur.execute("""
                        INSERT INTO user_streaks (wallet, tutorial_completed, created_at)
                        VALUES (%s, TRUE, NOW())
                        ON CONFLICT (wallet) DO UPDATE SET
                            tutorial_completed = TRUE,
                            updated_at = NOW()
                    """, (wallet,))

                    # Add EMBER to balance
                    cur.execute("""
                        INSERT INTO user_balances (wallet, ember_balance, total_ember_earned, created_at, last_update)
                        VALUES (%s, %s, %s, NOW(), NOW())
                        ON CONFLICT (wallet) DO UPDATE SET
                            ember_balance = user_balances.ember_balance + EXCLUDED.ember_balance,
                            total_ember_earned = COALESCE(user_balances.total_ember_earned, 0) + EXCLUDED.total_ember_earned,
                            last_update = NOW()
                    """, (wallet, ember_reward, ember_reward))

                    # Log reward
                    cur.execute("""
                        INSERT INTO social_rewards_log (wallet, action_type, ember_earned, description)
                        VALUES (%s, 'tutorial', %s, 'Completed all tutorial sections')
                    """, (wallet, ember_reward))

                    return jsonify({
                        "success": True,
                        "ember_earned": ember_reward,
                        "message": "Knowledge is the first spark."
                    })

        except Exception as e:
            print(f"Error processing tutorial complete: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/first-mint-reward', methods=['POST'])
    def api_social_first_mint_reward():
        """
        Award EMBER for first mint in the mini app.
        Can only be claimed once per wallet.

        Body: { "wallet": "0x..." }
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()

        if not wallet:
            return jsonify({"error": "Missing wallet"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if already rewarded
                    cur.execute("""
                        SELECT first_mint_rewarded FROM user_streaks WHERE wallet = %s
                    """, (wallet,))
                    row = cur.fetchone()

                    if row and row[0]:
                        return jsonify({
                            "success": True,
                            "already_rewarded": True,
                            "ember_earned": 0,
                            "message": "First mint reward already claimed"
                        })

                    # Award EMBER
                    ember_reward = SOCIAL_REWARDS['first_mint']

                    # Update/create streak record
                    cur.execute("""
                        INSERT INTO user_streaks (wallet, first_mint_rewarded, created_at)
                        VALUES (%s, TRUE, NOW())
                        ON CONFLICT (wallet) DO UPDATE SET
                            first_mint_rewarded = TRUE,
                            updated_at = NOW()
                    """, (wallet,))

                    # Add EMBER to balance
                    cur.execute("""
                        INSERT INTO user_balances (wallet, ember_balance, total_ember_earned, created_at, last_update)
                        VALUES (%s, %s, %s, NOW(), NOW())
                        ON CONFLICT (wallet) DO UPDATE SET
                            ember_balance = user_balances.ember_balance + EXCLUDED.ember_balance,
                            total_ember_earned = COALESCE(user_balances.total_ember_earned, 0) + EXCLUDED.total_ember_earned,
                            last_update = NOW()
                    """, (wallet, ember_reward, ember_reward))

                    # Log reward
                    cur.execute("""
                        INSERT INTO social_rewards_log (wallet, action_type, ember_earned, description)
                        VALUES (%s, 'first_mint', %s, 'First Emissary minted in mini app')
                    """, (wallet, ember_reward))

                    return jsonify({
                        "success": True,
                        "ember_earned": ember_reward,
                        "message": "Your journey begins, Operator."
                    })

        except Exception as e:
            print(f"Error processing first mint reward: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/share-reward', methods=['POST'])
    def api_social_share_reward():
        """
        Award EMBER for sharing on Farcaster.
        Limited to 5 shares per day per wallet.

        Body: {
            "wallet": "0x...",
            "cast_hash": "0x..."  # Farcaster cast hash
        }
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()
        cast_hash = data.get('cast_hash', '')

        if not wallet or not cast_hash:
            return jsonify({"error": "Missing required fields"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

                    # Check if this cast was already rewarded
                    cur.execute("""
                        SELECT id FROM social_rewards_log
                        WHERE wallet = %s AND action_type = 'share' AND reference_id = %s
                    """, (wallet, cast_hash))
                    if cur.fetchone():
                        return jsonify({
                            "success": True,
                            "already_rewarded": True,
                            "ember_earned": 0,
                            "message": "This cast was already rewarded"
                        })

                    # Check daily limit
                    cur.execute("""
                        SELECT COUNT(*) FROM social_rewards_log
                        WHERE wallet = %s AND action_type = 'share' AND created_at >= %s
                    """, (wallet, today_start))
                    shares_today = cur.fetchone()[0]

                    if shares_today >= SOCIAL_LIMITS['share']:
                        return jsonify({
                            "success": True,
                            "limit_reached": True,
                            "ember_earned": 0,
                            "shares_today": shares_today,
                            "max_shares": SOCIAL_LIMITS['share'],
                            "message": "Daily share limit reached"
                        })

                    # Award EMBER
                    ember_reward = SOCIAL_REWARDS['share']

                    # Add EMBER to balance
                    cur.execute("""
                        INSERT INTO user_balances (wallet, ember_balance, total_ember_earned, created_at, last_update)
                        VALUES (%s, %s, %s, NOW(), NOW())
                        ON CONFLICT (wallet) DO UPDATE SET
                            ember_balance = user_balances.ember_balance + EXCLUDED.ember_balance,
                            total_ember_earned = COALESCE(user_balances.total_ember_earned, 0) + EXCLUDED.total_ember_earned,
                            last_update = NOW()
                    """, (wallet, ember_reward, ember_reward))

                    # Log reward
                    cur.execute("""
                        INSERT INTO social_rewards_log (wallet, action_type, ember_earned, reference_id, description)
                        VALUES (%s, 'share', %s, %s, 'Farcaster share')
                    """, (wallet, ember_reward, cast_hash))

                    return jsonify({
                        "success": True,
                        "ember_earned": ember_reward,
                        "shares_today": shares_today + 1,
                        "max_shares": SOCIAL_LIMITS['share'],
                        "message": "The word spreads across the realm."
                    })

        except Exception as e:
            print(f"Error processing share reward: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/referral-reward', methods=['POST'])
    def api_social_referral_reward():
        """
        Award EMBER for referring a new user who mints.
        Limited to 10 referrals per day per referrer.

        Body: {
            "referrer_wallet": "0x...",  # The person who referred
            "referred_wallet": "0x..."   # The new user who minted
        }
        """
        data = request.get_json() or {}
        referrer = data.get('referrer_wallet', '').lower()
        referred = data.get('referred_wallet', '').lower()

        if not referrer or not referred:
            return jsonify({"error": "Missing required fields"}), 400

        if referrer == referred:
            return jsonify({"error": "Cannot refer yourself"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

                    # Check if this referred wallet was already rewarded
                    cur.execute("""
                        SELECT id FROM social_rewards_log
                        WHERE wallet = %s AND action_type = 'referral' AND reference_id = %s
                    """, (referrer, referred))
                    if cur.fetchone():
                        return jsonify({
                            "success": True,
                            "already_rewarded": True,
                            "ember_earned": 0,
                            "message": "This referral was already rewarded"
                        })

                    # Check daily limit
                    cur.execute("""
                        SELECT COUNT(*) FROM social_rewards_log
                        WHERE wallet = %s AND action_type = 'referral' AND created_at >= %s
                    """, (referrer, today_start))
                    referrals_today = cur.fetchone()[0]

                    if referrals_today >= SOCIAL_LIMITS['referral']:
                        return jsonify({
                            "success": True,
                            "limit_reached": True,
                            "ember_earned": 0,
                            "referrals_today": referrals_today,
                            "max_referrals": SOCIAL_LIMITS['referral'],
                            "message": "Daily referral limit reached"
                        })

                    # Award EMBER to referrer
                    ember_reward = SOCIAL_REWARDS['referral']

                    # Add EMBER to referrer's balance
                    cur.execute("""
                        INSERT INTO user_balances (wallet, ember_balance, total_ember_earned, created_at, last_update)
                        VALUES (%s, %s, %s, NOW(), NOW())
                        ON CONFLICT (wallet) DO UPDATE SET
                            ember_balance = user_balances.ember_balance + EXCLUDED.ember_balance,
                            total_ember_earned = COALESCE(user_balances.total_ember_earned, 0) + EXCLUDED.total_ember_earned,
                            last_update = NOW()
                    """, (referrer, ember_reward, ember_reward))

                    # Log reward
                    cur.execute("""
                        INSERT INTO social_rewards_log (wallet, action_type, ember_earned, reference_id, description)
                        VALUES (%s, 'referral', %s, %s, 'Referred new user who minted')
                    """, (referrer, ember_reward, referred))

                    return jsonify({
                        "success": True,
                        "ember_earned": ember_reward,
                        "referrals_today": referrals_today + 1,
                        "max_referrals": SOCIAL_LIMITS['referral'],
                        "message": "New blood joins the cause."
                    })

        except Exception as e:
            print(f"Error processing referral reward: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/rewards-history/<wallet>', methods=['GET'])
    def api_social_rewards_history(wallet):
        """Get social rewards history for a wallet"""
        wallet = wallet.lower()

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT action_type, ember_earned, reference_id, description, created_at
                        FROM social_rewards_log
                        WHERE wallet = %s
                        ORDER BY created_at DESC
                        LIMIT 50
                    """, (wallet,))
                    rows = cur.fetchall()

                    history = [{
                        "action_type": row[0],
                        "ember_earned": float(row[1]),
                        "reference_id": row[2],
                        "description": row[3],
                        "created_at": row[4].isoformat() if row[4] else None
                    } for row in rows]

                    # Get totals
                    cur.execute("""
                        SELECT action_type, SUM(ember_earned) as total
                        FROM social_rewards_log
                        WHERE wallet = %s
                        GROUP BY action_type
                    """, (wallet,))
                    totals_rows = cur.fetchall()
                    totals = {row[0]: float(row[1]) for row in totals_rows}

                    return jsonify({
                        "success": True,
                        "history": history,
                        "totals": totals
                    })

        except Exception as e:
            print(f"Error getting rewards history: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/streak/<wallet>', methods=['GET'])
    def api_social_streak(wallet):
        """Get streak information for a wallet"""
        wallet = wallet.lower()

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT current_streak, longest_streak, last_login_date,
                               tutorial_completed, first_mint_rewarded
                        FROM user_streaks WHERE wallet = %s
                    """, (wallet,))
                    row = cur.fetchone()

                    if not row:
                        return jsonify({
                            "success": True,
                            "current_streak": 0,
                            "longest_streak": 0,
                            "last_login": None,
                            "tutorial_completed": False,
                            "first_mint_rewarded": False
                        })

                    today = datetime.now(timezone.utc).date()
                    last_login = row[2]

                    # Check if login today
                    logged_in_today = last_login == today if last_login else False

                    # Calculate next milestone
                    streak = row[0] or 0
                    if streak < 7:
                        next_milestone = 7
                    elif streak < 30:
                        next_milestone = 30
                    else:
                        next_milestone = streak + (30 - (streak % 30))

                    return jsonify({
                        "success": True,
                        "current_streak": streak,
                        "longest_streak": row[1] or 0,
                        "last_login": last_login.isoformat() if last_login else None,
                        "logged_in_today": logged_in_today,
                        "next_milestone": next_milestone,
                        "days_to_next": next_milestone - streak,
                        "tutorial_completed": row[3] or False,
                        "first_mint_rewarded": row[4] or False
                    })

        except Exception as e:
            print(f"Error getting streak: {e}")
            return jsonify({"error": str(e)}), 500

    # =====================================================================
    # PLAYER ENDPOINTS (Required by Mini App)
    # =====================================================================

    @app.route('/api/player/<wallet>', methods=['GET'])
    def api_player_get(wallet):
        """
        Get player data including their emissaries.
        This is the main endpoint for loading user's NFTs in the mini app.
        """
        wallet = wallet.lower()

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get all NFTs owned by this wallet
                    cur.execute("""
                        SELECT token_id, name, guild, race_class, image_url, dynamic_state
                        FROM nfts
                        WHERE last_known_owner = %s
                        ORDER BY token_id
                    """, (wallet,))
                    rows = cur.fetchall()

                    heroes = []
                    for row in rows:
                        dynamic_state = row[5] or {}
                        heroes.append({
                            "token_id": row[0],
                            "name": row[1] or f"Emissary #{row[0]}",
                            "guild": row[2] or "Unknown",
                            "race_class": row[3] or "Unknown",
                            "image_url": row[4] or "",
                            "dynamic_state": dynamic_state,
                            "level": dynamic_state.get('xp_level', 1),
                            "xp": dynamic_state.get('xp_total', 0),
                            "aura": dynamic_state.get('aura_level', 0),
                            "energy": dynamic_state.get('energy_current', 100),
                            "state": dynamic_state.get('state', 'READY')
                        })

                    # Get EMBER balance
                    cur.execute("""
                        SELECT ember_balance, total_ember_earned
                        FROM user_balances
                        WHERE wallet = %s
                    """, (wallet,))
                    balance_row = cur.fetchone()

                    return jsonify({
                        "success": True,
                        "wallet": wallet,
                        "player": {
                            "heroes": heroes,
                            "heroes_count": len(heroes)
                        },
                        "ember_balance": balance_row[0] if balance_row else 0,
                        "total_ember_earned": balance_row[1] if balance_row else 0
                    })

        except Exception as e:
            print(f"Error getting player data: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/player/<wallet>', methods=['POST'])
    def api_player_register(wallet):
        """
        Register/sync NFTs for a wallet.
        Called when user connects wallet to sync blockchain data to database.

        Body: {
            "token_ids": ["00001", "00002", ...],
            "total_supply": 1234
        }
        """
        wallet = wallet.lower()
        data = request.get_json() or {}
        token_ids = data.get('token_ids', [])
        total_supply = data.get('total_supply', 0)

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        if not token_ids:
            return jsonify({
                "success": True,
                "message": "No token_ids provided",
                "token_ids_cached": 0,
                "synced_to_database": 0
            })

        try:
            synced = 0
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    for token_id in token_ids:
                        # Pad token_id to 5 digits
                        token_id_padded = str(token_id).zfill(5)

                        # Update or insert NFT with owner
                        cur.execute("""
                            INSERT INTO nfts (token_id, last_known_owner, name)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (token_id) DO UPDATE SET
                                last_known_owner = %s,
                                last_update = NOW()
                        """, (
                            token_id_padded,
                            wallet,
                            f"Emissary #{token_id_padded}",
                            wallet
                        ))
                        synced += 1

                    # Ensure user_balances entry exists
                    cur.execute("""
                        INSERT INTO user_balances (wallet, ember_balance, ash_balance)
                        VALUES (%s, 0, 0)
                        ON CONFLICT (wallet) DO NOTHING
                    """, (wallet,))

            return jsonify({
                "success": True,
                "wallet": wallet,
                "token_ids_cached": len(token_ids),
                "synced_to_database": synced,
                "total_supply": total_supply
            })

        except Exception as e:
            print(f"Error registering player NFTs: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/player/<wallet>/ember', methods=['GET'])
    def api_player_ember(wallet):
        """Get $EMBER balance for a wallet"""
        wallet = wallet.lower()

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT ember_balance, total_ember_earned, ash_balance
                        FROM user_balances
                        WHERE wallet = %s
                    """, (wallet,))
                    row = cur.fetchone()

                    if row:
                        return jsonify({
                            "success": True,
                            "wallet": wallet,
                            "ember_balance": row[0] or 0,
                            "total_ember_earned": row[1] or 0,
                            "ash_balance": row[2] or 0
                        })
                    else:
                        return jsonify({
                            "success": True,
                            "wallet": wallet,
                            "ember_balance": 0,
                            "total_ember_earned": 0,
                            "ash_balance": 0
                        })

        except Exception as e:
            print(f"Error getting ember balance: {e}")
            return jsonify({"error": str(e)}), 500

    # =====================================================================
    # GLOBAL CHAT ENDPOINTS
    # =====================================================================

    # Daily message limit and EMBER reward per message
    DAILY_MESSAGE_LIMIT = 50
    EMBER_PER_MESSAGE = 0.1

    @app.route('/api/social/global-chat', methods=['GET'])
    def api_social_global_chat_get():
        """
        Get global chat messages with country flags.
        Query params:
        - limit: max messages to return (default 100)
        - before_id: pagination cursor
        - wallet: (optional) include message count for this wallet
        """
        limit = request.args.get('limit', 100, type=int)
        before_id = request.args.get('before_id', type=int)
        wallet = request.args.get('wallet', '').lower()

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if global_messages table exists, create with country_code if not
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS global_messages (
                            id SERIAL PRIMARY KEY,
                            wallet VARCHAR(42) NOT NULL,
                            message TEXT NOT NULL,
                            country_code CHAR(3),
                            created_at TIMESTAMP DEFAULT NOW()
                        )
                    """)
                    # Add country_code column if it doesn't exist (for existing tables)
                    cur.execute("""
                        ALTER TABLE global_messages ADD COLUMN IF NOT EXISTS country_code CHAR(3)
                    """)
                    # Create index for faster queries
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_global_messages_created ON global_messages(created_at DESC)
                    """)

                    if before_id:
                        cur.execute("""
                            SELECT gm.id, gm.wallet, gm.message, gm.created_at, gm.country_code,
                                   up.display_name, up.farcaster_username, up.farcaster_pfp_url,
                                   up.country_code as profile_country
                            FROM global_messages gm
                            LEFT JOIN user_profiles up ON gm.wallet = up.wallet
                            WHERE gm.id < %s
                            ORDER BY gm.id DESC
                            LIMIT %s
                        """, (before_id, limit))
                    else:
                        cur.execute("""
                            SELECT gm.id, gm.wallet, gm.message, gm.created_at, gm.country_code,
                                   up.display_name, up.farcaster_username, up.farcaster_pfp_url,
                                   up.country_code as profile_country
                            FROM global_messages gm
                            LEFT JOIN user_profiles up ON gm.wallet = up.wallet
                            ORDER BY gm.id DESC
                            LIMIT %s
                        """, (limit,))

                    rows = cur.fetchall()
                    messages = []
                    for row in rows:
                        # Use message country_code, fallback to profile country
                        country = row[4] or row[8]
                        messages.append({
                            "id": row[0],
                            "wallet": row[1],
                            "message": row[2],
                            "created_at": row[3].isoformat() if row[3] else None,
                            "country_code": country,
                            "display_name": row[5],
                            "farcaster_username": row[6],
                            "farcaster_pfp_url": row[7]
                        })

                    # Return in chronological order
                    messages.reverse()

                    # Get message count for wallet if provided
                    messages_today = 0
                    if wallet:
                        cur.execute("""
                            SELECT COUNT(*) FROM global_messages
                            WHERE wallet = %s
                            AND created_at >= CURRENT_DATE
                        """, (wallet,))
                        messages_today = cur.fetchone()[0]

                    return jsonify({
                        "success": True,
                        "messages": messages,
                        "messages_today": messages_today,
                        "daily_limit": DAILY_MESSAGE_LIMIT,
                        "ember_per_message": EMBER_PER_MESSAGE
                    })

        except Exception as e:
            print(f"Error getting global chat: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/social/global-chat', methods=['POST'])
    def api_social_global_chat_post():
        """
        Send a message to global chat.
        Rewards: +0.1 EMBER per message, max 50 messages/day (5 EMBER/day)

        Body: {
            "wallet": "0x...",
            "message": "Hello world!"
        }
        """
        data = request.get_json() or {}
        wallet = data.get('wallet', '').lower()
        message = data.get('message', '').strip()

        if not wallet or not message:
            return jsonify({"error": "Missing wallet or message"}), 400

        if len(message) > 500:
            return jsonify({"error": "Message too long (max 500 chars)"}), 400

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Create table if not exists
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS global_messages (
                            id SERIAL PRIMARY KEY,
                            wallet VARCHAR(42) NOT NULL,
                            message TEXT NOT NULL,
                            country_code CHAR(3),
                            created_at TIMESTAMP DEFAULT NOW()
                        )
                    """)
                    cur.execute("""
                        ALTER TABLE global_messages ADD COLUMN IF NOT EXISTS country_code CHAR(3)
                    """)

                    # Check daily message limit
                    cur.execute("""
                        SELECT COUNT(*) FROM global_messages
                        WHERE wallet = %s
                        AND created_at >= CURRENT_DATE
                    """, (wallet,))
                    messages_today = cur.fetchone()[0]

                    if messages_today >= DAILY_MESSAGE_LIMIT:
                        return jsonify({
                            "error": f"Daily message limit reached ({DAILY_MESSAGE_LIMIT}/day)",
                            "messages_today": messages_today,
                            "daily_limit": DAILY_MESSAGE_LIMIT
                        }), 429

                    # Get user profile including country_code
                    cur.execute("""
                        SELECT display_name, farcaster_username, farcaster_pfp_url, country_code
                        FROM user_profiles WHERE wallet = %s
                    """, (wallet,))
                    profile = cur.fetchone()
                    country_code = profile[3] if profile else None

                    # Insert message with country_code
                    cur.execute("""
                        INSERT INTO global_messages (wallet, message, country_code)
                        VALUES (%s, %s, %s)
                        RETURNING id, created_at
                    """, (wallet, message, country_code))
                    row = cur.fetchone()
                    message_id = row[0]
                    created_at = row[1]

                    # Award EMBER for sending message
                    ember_earned = EMBER_PER_MESSAGE
                    cur.execute("""
                        INSERT INTO user_balances (wallet, ember_balance, total_ember_earned, created_at, last_update)
                        VALUES (%s, %s, %s, NOW(), NOW())
                        ON CONFLICT (wallet) DO UPDATE SET
                            ember_balance = user_balances.ember_balance + EXCLUDED.ember_balance,
                            total_ember_earned = COALESCE(user_balances.total_ember_earned, 0) + EXCLUDED.total_ember_earned,
                            last_update = NOW()
                    """, (wallet, ember_earned, ember_earned))

                    # Update last_seen in user_profiles
                    cur.execute("""
                        UPDATE user_profiles SET last_seen = NOW() WHERE wallet = %s
                    """, (wallet,))

                    print(f"💬 Global chat: {wallet[:8]}... sent message, +{ember_earned} EMBER ({messages_today + 1}/{DAILY_MESSAGE_LIMIT} today)")

                    return jsonify({
                        "success": True,
                        "message": {
                            "id": message_id,
                            "wallet": wallet,
                            "message": message,
                            "created_at": created_at.isoformat() if created_at else None,
                            "country_code": country_code,
                            "display_name": profile[0] if profile else None,
                            "farcaster_username": profile[1] if profile else None,
                            "farcaster_pfp_url": profile[2] if profile else None
                        },
                        "ember_earned": ember_earned,
                        "messages_today": messages_today + 1,
                        "daily_limit": DAILY_MESSAGE_LIMIT
                    })

        except Exception as e:
            print(f"Error posting to global chat: {e}")
            return jsonify({"error": str(e)}), 500

    # =====================================================================
    # OPERATORS ENDPOINT
    # =====================================================================

    @app.route('/api/social/operators', methods=['GET'])
    def api_social_operators():
        """Get list of all operators (NFT holders with profiles)"""
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT
                            up.wallet,
                            up.display_name,
                            up.farcaster_username,
                            up.farcaster_pfp_url,
                            up.last_seen,
                            up.country_code,
                            (SELECT COUNT(*) FROM nfts WHERE last_known_owner = up.wallet) as nft_count
                        FROM user_profiles up
                        WHERE EXISTS (SELECT 1 FROM nfts WHERE last_known_owner = up.wallet)
                        ORDER BY up.last_seen DESC NULLS LAST
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    rows = cur.fetchall()

                    users = []
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    for row in rows:
                        last_seen = row[4]
                        is_online = False
                        if last_seen:
                            is_online = (now - last_seen).total_seconds() < 900  # 15 min

                        users.append({
                            "wallet": row[0],
                            "display_name": row[1],
                            "farcaster_username": row[2],
                            "farcaster_pfp_url": row[3],
                            "last_seen": row[4].isoformat() if row[4] else None,
                            "country_code": row[5],
                            "nft_count": row[6],
                            "is_online": is_online
                        })

                    return jsonify({
                        "success": True,
                        "users": users,
                        "count": len(users),
                        "limit": limit,
                        "offset": offset
                    })

        except Exception as e:
            print(f"Error getting operators: {e}")
            return jsonify({"error": str(e)}), 500

    # =====================================================================
    # EVENTS ENDPOINT (Database version - for Mini App)
    # =====================================================================

    @app.route('/api/events/db', methods=['GET'])
    def api_events_from_db():
        """
        Get active events from database.
        Alternative to /api/events which uses in-memory EVENTS constant.
        """
        if not POSTGRESQL_AVAILABLE:
            return jsonify({"events": [], "event_settings": None})

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get active events
                    cur.execute("""
                        SELECT id, name, slug, status, description,
                               item_drop_multiplier, rune_drop_multiplier, created_at
                        FROM events
                        WHERE status = 'active'
                        ORDER BY created_at DESC
                    """, ())
                    rows = cur.fetchall()

                    events = []
                    for row in rows:
                        events.append({
                            "id": str(row[0]),
                            "name": row[1],
                            "slug": row[2],
                            "status": row[3],
                            "description": row[4],
                            "item_drop_multiplier": float(row[5]) if row[5] else 1.0,
                            "rune_drop_multiplier": float(row[6]) if row[6] else 1.0,
                            "event_active": row[3] == 'active'
                        })

                    return jsonify({
                        "events": events,
                        "event_settings": {
                            "max_concurrent_events": 3,
                            "cooldown_hours": 1,
                            "bonus_multiplier": 1.0
                        }
                    })

        except Exception as e:
            print(f"Error getting events: {e}")
            return jsonify({"events": [], "event_settings": None})

    print("✅ Mini App routes registered successfully")
    print("   - GET  /api/realm-status")
    print("   - GET  /api/pyre/<wallet>")
    print("   - POST /api/pyre/earn")
    print("   - POST /api/pyre/spend")
    print("   - GET  /api/pyre/history/<wallet>")
    print("   - GET  /api/micro-missions")
    print("   - GET  /api/micro-mission/<id>")
    print("   - POST /api/micro-mission/start")
    print("   - POST /api/micro-mission/choice")
    print("   - POST /api/micro-mission/complete")
    print("   - GET  /api/micro-mission/active/<wallet>")
    print("   - GET  /api/emissary/<id>/full-status")
    print("   - POST /api/social/profile")
    print("   - GET  /api/social/profile/<wallet>")
    print("   - GET  /api/social/countries")
    print("   - GET  /api/social/country/<code>/users")
    print("   - GET  /api/social/conversations/<wallet>")
    print("   - GET  /api/social/messages/<wallet>/<other>")
    print("   - POST /api/social/message")
    print("   - POST /api/social/message/read")
    print("   - GET  /api/social/online-stats")
    print("   - GET  /api/player/<wallet> (NEW)")
    print("   - POST /api/player/<wallet> (NEW)")
    print("   - GET  /api/player/<wallet>/ember (NEW)")
    print("   - GET  /api/social/global-chat (NEW)")
    print("   - POST /api/social/global-chat (NEW)")
    print("   - GET  /api/social/operators (NEW)")
    print("   - GET  /api/events (NEW)")
