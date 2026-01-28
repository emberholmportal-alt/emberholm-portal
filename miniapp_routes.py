"""
EMBERHOLM MINI APP - ROUTES MODULE
===================================
Endpoints para la Mini App de Farcaster.
Incluye: $SPARK system, Micro-Missions, Realm Status, Full Emissary Status.

Importar en app.py:
    from miniapp_routes import register_miniapp_routes
    register_miniapp_routes(app)
"""

import json
import random
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import jsonify, request

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
    # $SPARK ENDPOINTS
    # =====================================================================

    @app.route('/api/spark/<wallet>', methods=['GET'])
    def api_spark_balance(wallet):
        """Get $SPARK balance for a wallet"""
        wallet = wallet.lower()

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get or create balance
                    cur.execute("""
                        INSERT INTO spark_balances (wallet, balance, total_earned, total_spent)
                        VALUES (%s, 0, 0, 0)
                        ON CONFLICT (wallet) DO NOTHING
                    """, (wallet,))

                    cur.execute("""
                        SELECT balance, total_earned, total_spent, daily_streak, last_daily_claim
                        FROM spark_balances WHERE wallet = %s
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
            print(f"Error getting spark balance: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/spark/earn', methods=['POST'])
    def api_spark_earn():
        """
        Add $SPARK to a wallet (internal use - from micro-missions, etc.)

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
                        INSERT INTO spark_balances (wallet, balance, total_earned)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (wallet) DO UPDATE SET
                            balance = spark_balances.balance + %s,
                            total_earned = spark_balances.total_earned + %s,
                            updated_at = NOW()
                        RETURNING balance, total_earned
                    """, (wallet, amount, amount, amount, amount))
                    row = cur.fetchone()

                    # Record transaction
                    cur.execute("""
                        INSERT INTO spark_transactions
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
            print(f"Error earning spark: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/spark/spend', methods=['POST'])
    def api_spark_spend():
        """
        Spend $SPARK from a wallet

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
                        SELECT balance FROM spark_balances WHERE wallet = %s
                    """, (wallet,))
                    row = cur.fetchone()

                    if not row or row[0] < amount:
                        return jsonify({
                            "error": "Insufficient $SPARK balance",
                            "balance": row[0] if row else 0,
                            "required": amount
                        }), 400

                    # Deduct balance
                    cur.execute("""
                        UPDATE spark_balances SET
                            balance = balance - %s,
                            total_spent = total_spent + %s,
                            updated_at = NOW()
                        WHERE wallet = %s
                        RETURNING balance, total_spent
                    """, (amount, amount, wallet))
                    row = cur.fetchone()

                    # Record transaction (negative amount)
                    cur.execute("""
                        INSERT INTO spark_transactions
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
            print(f"Error spending spark: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/spark/history/<wallet>', methods=['GET'])
    def api_spark_history(wallet):
        """Get $SPARK transaction history for a wallet"""
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
                        FROM spark_transactions
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
            print(f"Error getting spark history: {e}")
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
                               energy_cost, spark_reward_min, spark_reward_max,
                               xp_reward_min, xp_reward_max, aura_chance,
                               narrative_intro, cooldown_minutes
                        FROM micro_missions
                        WHERE is_active = TRUE
                        ORDER BY difficulty, id
                    """)
                    rows = cur.fetchall()

                    missions = []
                    for row in rows:
                        missions.append({
                            "id": row[0],
                            "name": row[1],
                            "description": row[2],
                            "difficulty": row[3],
                            "duration_seconds": row[4],
                            "energy_cost": row[5],
                            "spark_reward": {"min": row[6], "max": row[7]},
                            "xp_reward": {"min": row[8], "max": row[9]},
                            "aura_chance": float(row[10]) if row[10] else 0,
                            "narrative_intro": row[11],
                            "cooldown_minutes": row[12]
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
                               energy_cost, spark_reward_min, spark_reward_max,
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
                            "spark_reward": {"min": row[6], "max": row[7]},
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
                    # Get mission details
                    cur.execute("""
                        SELECT id, name, duration_seconds, energy_cost, narrative_intro,
                               narrative_choices
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

                    # Calculate end time
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    ends_at = now + timedelta(seconds=mission[2])

                    # Create active micro-mission
                    cur.execute("""
                        INSERT INTO active_micro_missions
                        (wallet, emissary_token_id, micro_mission_id, started_at, ends_at, status)
                        VALUES (%s, %s, %s, %s, %s, 'active')
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

                    return jsonify({
                        "success": True,
                        "active_micro_mission_id": active_id,
                        "mission": {
                            "id": mission[0],
                            "name": mission[1],
                            "duration_seconds": mission[2],
                            "narrative_intro": mission[4],
                            "choices": mission[5] or []
                        },
                        "started_at": now.isoformat(),
                        "ends_at": ends_at.isoformat(),
                        "emissary_token_id": token_id
                    })

        except Exception as e:
            print(f"Error starting micro-mission: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/micro-mission/choice', methods=['POST'])
    def api_micro_mission_choice():
        """
        Register player's choice in a micro-mission.

        Body: {
            "wallet": "0x...",
            "active_micro_mission_id": 123,
            "choice": "A"  // A, B, or C
        }
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
                    # Verify ownership and status
                    cur.execute("""
                        SELECT amm.id, amm.status, amm.micro_mission_id, mm.narrative_outcomes
                        FROM active_micro_missions amm
                        JOIN micro_missions mm ON amm.micro_mission_id = mm.id
                        WHERE amm.id = %s AND amm.wallet = %s
                    """, (active_id, wallet))
                    row = cur.fetchone()

                    if not row:
                        return jsonify({"error": "Active micro-mission not found"}), 404

                    if row[1] not in ['active', 'choice_pending']:
                        return jsonify({"error": f"Cannot make choice in status: {row[1]}"}), 400

                    outcomes = row[3] or {}
                    outcome = outcomes.get(choice, {})

                    # Update with choice
                    cur.execute("""
                        UPDATE active_micro_missions SET
                            choice_made = %s,
                            status = 'choice_pending',
                            outcome_text = %s
                        WHERE id = %s
                    """, (choice, outcome.get('text', ''), active_id))

                    return jsonify({
                        "success": True,
                        "choice": choice,
                        "outcome_preview": outcome.get('text', 'Your choice has been recorded...'),
                        "message": "Wait for the mission to complete to see full results"
                    })

        except Exception as e:
            print(f"Error recording choice: {e}")
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
                    # Get active mission details
                    cur.execute("""
                        SELECT amm.id, amm.status, amm.emissary_token_id, amm.ends_at,
                               amm.choice_made, amm.outcome_text,
                               mm.spark_reward_min, mm.spark_reward_max,
                               mm.xp_reward_min, mm.xp_reward_max,
                               mm.aura_chance, mm.name, mm.narrative_outcomes
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

                    # Check if time has passed
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    if now < row[3]:  # ends_at
                        remaining = (row[3] - now).total_seconds()
                        return jsonify({
                            "error": "Mission not yet complete",
                            "remaining_seconds": int(remaining)
                        }), 400

                    # Calculate rewards
                    spark_earned = random.randint(row[6], row[7])  # spark_reward_min/max
                    xp_earned = random.randint(row[8], row[9])     # xp_reward_min/max
                    aura_earned = 1 if random.random() * 100 < float(row[10] or 0) else 0

                    # Apply choice modifier if applicable
                    choice = row[4]
                    outcomes = row[12] or {}
                    if choice and choice in outcomes:
                        modifier = outcomes[choice].get('spark_modifier', 1.0)
                        spark_earned = int(spark_earned * modifier)

                    token_id = row[2]
                    mission_name = row[11]
                    outcome_text = row[5] or "The mission concludes..."

                    # Update active mission
                    cur.execute("""
                        UPDATE active_micro_missions SET
                            status = 'completed',
                            spark_earned = %s,
                            xp_earned = %s,
                            aura_earned = %s
                        WHERE id = %s
                    """, (spark_earned, xp_earned, aura_earned, active_id))

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

                    # Add $SPARK to wallet
                    cur.execute("""
                        INSERT INTO spark_balances (wallet, balance, total_earned)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (wallet) DO UPDATE SET
                            balance = spark_balances.balance + %s,
                            total_earned = spark_balances.total_earned + %s,
                            updated_at = NOW()
                    """, (wallet, spark_earned, spark_earned, spark_earned, spark_earned))

                    # Record transaction
                    cur.execute("""
                        INSERT INTO spark_transactions
                        (wallet, amount, transaction_type, reference_id, description)
                        VALUES (%s, %s, 'micro_mission', %s, %s)
                    """, (wallet, spark_earned, str(active_id), f"Completed: {mission_name}"))

                    return jsonify({
                        "success": True,
                        "completed": True,
                        "rewards": {
                            "spark": spark_earned,
                            "xp": xp_earned,
                            "aura": aura_earned
                        },
                        "mission_name": mission_name,
                        "outcome_text": outcome_text,
                        "choice_made": choice,
                        "emissary_token_id": token_id
                    })

        except Exception as e:
            print(f"Error completing micro-mission: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/micro-mission/active/<wallet>', methods=['GET'])
    def api_micro_mission_active(wallet):
        """Get active micro-mission for a wallet"""
        wallet = wallet.lower()

        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT amm.id, amm.emissary_token_id, amm.micro_mission_id,
                               amm.started_at, amm.ends_at, amm.status, amm.choice_made,
                               mm.name, mm.narrative_intro, mm.narrative_choices
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
                            "narrative_intro": row[8],
                            "choices": row[9] or []
                        }
                    })

        except Exception as e:
            print(f"Error getting active micro-mission: {e}")
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

    print("✅ Mini App routes registered successfully")
    print("   - GET  /api/realm-status")
    print("   - GET  /api/spark/<wallet>")
    print("   - POST /api/spark/earn")
    print("   - POST /api/spark/spend")
    print("   - GET  /api/spark/history/<wallet>")
    print("   - GET  /api/micro-missions")
    print("   - GET  /api/micro-mission/<id>")
    print("   - POST /api/micro-mission/start")
    print("   - POST /api/micro-mission/choice")
    print("   - POST /api/micro-mission/complete")
    print("   - GET  /api/micro-mission/active/<wallet>")
    print("   - GET  /api/emissary/<id>/full-status")
