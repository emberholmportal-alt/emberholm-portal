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
                    # Get active mission details (including ember_reward fields)
                    cur.execute("""
                        SELECT amm.id, amm.status, amm.emissary_token_id, amm.ends_at,
                               amm.choice_made, amm.outcome_text,
                               mm.pyre_reward_min, mm.pyre_reward_max,
                               mm.xp_reward_min, mm.xp_reward_max,
                               mm.aura_chance, mm.name, mm.narrative_outcomes,
                               COALESCE(mm.ember_reward_min, 0), COALESCE(mm.ember_reward_max, 0)
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
                    pyre_earned = random.randint(row[6], row[7])  # pyre_reward_min/max
                    xp_earned = random.randint(row[8], row[9])     # xp_reward_min/max
                    aura_earned = 1 if random.random() * 100 < float(row[10] or 0) else 0

                    # 🔥 EMBER REWARD: Calculate ember from micro-mission
                    ember_min = row[13] or 0  # ember_reward_min
                    ember_max = row[14] or 0  # ember_reward_max
                    ember_earned = random.randint(ember_min, ember_max) if ember_min > 0 and ember_max > 0 else 0

                    # Apply choice modifier if applicable
                    choice = row[4]
                    outcomes = row[12] or {}
                    if choice and choice in outcomes:
                        modifier = outcomes[choice].get('pyre_modifier', 1.0)
                        pyre_earned = int(pyre_earned * modifier)
                        # Also apply modifier to ember if specified
                        ember_modifier = outcomes[choice].get('ember_modifier', 1.0)
                        ember_earned = int(ember_earned * ember_modifier)

                    token_id = row[2]
                    mission_name = row[11]
                    outcome_text = row[5] or "The mission concludes..."

                    # Update active mission
                    cur.execute("""
                        UPDATE active_micro_missions SET
                            status = 'completed',
                            pyre_earned = %s,
                            xp_earned = %s,
                            aura_earned = %s
                        WHERE id = %s
                    """, (pyre_earned, xp_earned, aura_earned, active_id))

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

                    # Add $PYRE to wallet
                    cur.execute("""
                        INSERT INTO pyre_balances (wallet, balance, total_earned)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (wallet) DO UPDATE SET
                            balance = pyre_balances.balance + %s,
                            total_earned = pyre_balances.total_earned + %s,
                            updated_at = NOW()
                    """, (wallet, pyre_earned, pyre_earned, pyre_earned, pyre_earned))

                    # 🔥 Add $EMBER to wallet (if earned)
                    if ember_earned > 0:
                        cur.execute("""
                            INSERT INTO user_balances (wallet, ember_balance, total_ember_earned, created_at, last_update)
                            VALUES (%s, %s, %s, NOW(), NOW())
                            ON CONFLICT (wallet) DO UPDATE SET
                                ember_balance = user_balances.ember_balance + EXCLUDED.ember_balance,
                                total_ember_earned = COALESCE(user_balances.total_ember_earned, 0) + EXCLUDED.total_ember_earned,
                                last_update = NOW()
                        """, (wallet, ember_earned, ember_earned))
                        print(f"🔥 EMBER +{ember_earned} for {wallet} (micro-mission complete)")

                    # Record transaction
                    cur.execute("""
                        INSERT INTO pyre_transactions
                        (wallet, amount, transaction_type, reference_id, description)
                        VALUES (%s, %s, 'micro_mission', %s, %s)
                    """, (wallet, pyre_earned, str(active_id), f"Completed: {mission_name}"))

                    return jsonify({
                        "success": True,
                        "completed": True,
                        "rewards": {
                            "pyre": pyre_earned,
                            "xp": xp_earned,
                            "aura": aura_earned,
                            "ember": ember_earned
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
                    cur.execute("""
                        SELECT id, wallet, country_code, display_name,
                               farcaster_fid, farcaster_username, farcaster_pfp_url, last_seen
                        FROM user_profiles WHERE wallet = %s
                    """, (wallet,))
                    row = cur.fetchone()

                    if not row:
                        return jsonify({"success": True, "profile": None})

                    return jsonify({
                        "success": True,
                        "profile": {
                            "id": row[0],
                            "wallet": row[1],
                            "country_code": row[2],
                            "display_name": row[3],
                            "farcaster_fid": row[4],
                            "farcaster_username": row[5],
                            "farcaster_pfp_url": row[6],
                            "last_seen": row[7].isoformat() if row[7] else None
                        }
                    })

        except Exception as e:
            print(f"Error getting profile: {e}")
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
    # EVENTS ENDPOINT (Wrapper for /api/events/active)
    # =====================================================================

    @app.route('/api/events', methods=['GET'])
    def api_events():
        """
        Get active events.
        This is a wrapper that redirects to the existing events endpoint format.
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
