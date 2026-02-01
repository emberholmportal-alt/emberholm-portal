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

                    # Create micro_mission_cooldowns table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS micro_mission_cooldowns (
                            id SERIAL PRIMARY KEY,
                            wallet VARCHAR(42) NOT NULL,
                            micro_mission_id VARCHAR(20) NOT NULL REFERENCES micro_missions(id),
                            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            cooldown_until TIMESTAMP NOT NULL,
                            UNIQUE(wallet, micro_mission_id)
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
                    cur.execute("""
                        UPDATE micro_missions SET duration_seconds = 120
                        WHERE difficulty = 'EASY'
                    """)
                    easy_updated = cur.rowcount
                    cur.execute("""
                        UPDATE micro_missions SET duration_seconds = 240
                        WHERE difficulty = 'MEDIUM'
                    """)
                    medium_updated = cur.rowcount
                    cur.execute("""
                        UPDATE micro_missions SET duration_seconds = 300
                        WHERE difficulty = 'HARD'
                    """)
                    hard_updated = cur.rowcount
                    print(f"[Migration] Duration updates: EASY={easy_updated}, MEDIUM={medium_updated}, HARD={hard_updated}")

                    # FORCE fix all active missions with wrong end times (over 10 minutes)
                    cur.execute("""
                        UPDATE active_micro_missions amm SET
                            ends_at = amm.started_at + (mm.duration_seconds * INTERVAL '1 second')
                        FROM micro_missions mm
                        WHERE amm.micro_mission_id = mm.id
                        AND amm.status IN ('active', 'choice_pending')
                        AND (amm.ends_at - amm.started_at) > INTERVAL '10 minutes'
                    """)
                    active_fixed = cur.rowcount
                    print(f"[Migration] Fixed {active_fixed} active missions with wrong end times")

                    # =========================================================
                    # POPULATE MULTI-STEP NARRATIVE DATA FOR MISSIONS
                    # Structure: EASY=2 steps, MEDIUM=3 steps, HARD=4 steps
                    # =========================================================

                    # MM-E001: The Whispering Flame (EASY - 2 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'LORE',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "The ancient brazier burns with an otherworldly flame. Whispers echo from its depths, speaking in a language older than the Portal itself.",
                                        "choices": [
                                            {"id": "A", "text": "Kneel and listen reverently", "next": "2A"},
                                            {"id": "B", "text": "Cast your own ember into the flame", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "The whispers grow clearer. They speak of the First Flame, the source of all power in Emberholm. The voice asks what knowledge you seek.",
                                        "choices": [
                                            {"id": "A", "text": "Ask about the Portals creation", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Ask about your own path forward", "next": "END_GOOD"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "Your ember merges with the ancient flame. It burns brighter, and a powerful presence acknowledges your offering.",
                                        "choices": [
                                            {"id": "A", "text": "Request a blessing of power", "next": "END_NEUTRAL"},
                                            {"id": "B", "text": "Offer yourself in service to the Flame", "next": "END_PERFECT"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "The First Flame reveals secrets of creation itself! Ancient power flows through you.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "The Flame blesses your devotion. You are marked as a true servant of the eternal fire.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "Visions of your future battles and triumphs fill your mind. You leave with renewed purpose.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "The Flame grants power, but warns that such requests come with hidden costs.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-E001'
                    """)

                    # MM-E002: Ember Gathering (EASY - 2 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'PATROL',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "Glowing embers dot the Ashen Fields, fading slowly into the void. You must act quickly to gather them before they disappear forever.",
                                        "choices": [
                                            {"id": "A", "text": "Rush to collect as many as possible", "next": "2A"},
                                            {"id": "B", "text": "Follow the brightest ember trail", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "Your hands are full of embers, but you notice an unusual glow deeper in the field. Time is running out.",
                                        "choices": [
                                            {"id": "A", "text": "Secure what you have and return", "next": "END_GOOD"},
                                            {"id": "B", "text": "Risk it all for the mysterious glow", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "The trail leads to a hidden alcove where embers congregate. But something moves in the shadows nearby.",
                                        "choices": [
                                            {"id": "A", "text": "Quietly gather and retreat", "next": "END_GOOD"},
                                            {"id": "B", "text": "Investigate the shadow", "next": "END_LEGENDARY"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "The shadow was a spirit guardian! Impressed by your courage, it reveals a mother ember - source of all others.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "You discover an ember nest untouched for centuries. A magnificent haul!", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "A solid collection of quality embers. The realm will benefit from your diligence.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "You gather a modest amount before the embers fade completely.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-E002'
                    """)

                    # MM-E003: Patrol the Perimeter (EASY - 2 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'PATROL',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "You take your position at the Portals edge. The mists swirl with unknown dangers, and strange sounds echo in the distance.",
                                        "choices": [
                                            {"id": "A", "text": "Maintain position and observe", "next": "2A"},
                                            {"id": "B", "text": "Venture into the mists to investigate", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "Your patience pays off. You notice a subtle disturbance in the veil between worlds - a small tear forming.",
                                        "choices": [
                                            {"id": "A", "text": "Signal for backup before acting", "next": "END_GOOD"},
                                            {"id": "B", "text": "Attempt to seal it yourself immediately", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "Deep in the mists, you discover tracks. Something has crossed from the void recently.",
                                        "choices": [
                                            {"id": "A", "text": "Follow the tracks cautiously", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Mark the location and report back", "next": "END_GOOD"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "You track and neutralize a void scout before it can report back. The realm is saved from invasion!", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "You seal the tear with ancient techniques. The veil strengthens around your repair.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "Your report enables a coordinated response. The threat is contained efficiently.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "A quiet patrol. Sometimes the absence of danger is the best outcome.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-E003'
                    """)

                    # MM-E004: Rune Meditation (EASY - 2 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'LORE',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "The ancient rune stone hums with power older than memory. As you approach, your mind begins to resonate with its energy.",
                                        "choices": [
                                            {"id": "A", "text": "Empty your mind completely", "next": "2A"},
                                            {"id": "B", "text": "Focus your will upon the rune", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "In the void of your empty mind, visions begin to form. Ancient symbols dance at the edge of comprehension.",
                                        "choices": [
                                            {"id": "A", "text": "Let the visions flow through you", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Try to grasp and hold the symbols", "next": "END_NEUTRAL"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "The rune responds to your will. A presence stirs within it - one of the First Runesmiths, their consciousness preserved in stone.",
                                        "choices": [
                                            {"id": "A", "text": "Ask them to teach you", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Simply listen to their wisdom", "next": "END_GOOD"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "The First Runesmith shares forbidden knowledge! A new rune sears itself into your memory.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "The visions reveal the true nature of runic magic. Understanding floods your consciousness.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "Ancient wisdom settles in your mind. You leave with deeper insight into the old ways.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "The symbols slip away like sand. But fragments remain, useful if incomplete.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-E004'
                    """)

                    # MM-E005: Forge Apprentice (EASY - 2 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'GUILD',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "The heat of the Eternal Forge washes over you. The master smith glances up from his work, measuring you with ancient eyes.",
                                        "choices": [
                                            {"id": "A", "text": "Offer to work the bellows", "next": "2A"},
                                            {"id": "B", "text": "Ask to observe his technique", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "Your steady rhythm pleases the master. As the forge reaches perfect heat, he gestures for you to approach the anvil.",
                                        "choices": [
                                            {"id": "A", "text": "Attempt to shape the metal yourself", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Assist while he demonstrates", "next": "END_GOOD"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "The master nods slowly. Few show such humility. He begins to work, and you notice his hammer strikes form an ancient pattern.",
                                        "choices": [
                                            {"id": "A", "text": "Memorize the pattern carefully", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Focus on the basic techniques", "next": "END_GOOD"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "The pattern was a secret of the founding smiths! The master grins - you passed his test.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "Under his guidance, you forge your first true piece. The master nods in approval.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "A productive day at the forge. Your skills have improved noticeably.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "The work is done well enough. Foundation before mastery, as they say.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-E005'
                    """)

                    # MM-M001: Void Echoes Investigation (MEDIUM - 3 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'EXPLORATION',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "Strange sounds emanate from a tear in reality. The void whispers secrets that mortal ears were never meant to hear.",
                                        "choices": [
                                            {"id": "A", "text": "Cast protective wards before approaching", "next": "2A"},
                                            {"id": "B", "text": "Move closer to hear more clearly", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "Your wards hold as void energy washes over you. Through the barrier, you see shapes moving in the darkness beyond.",
                                        "choices": [
                                            {"id": "A", "text": "Try to communicate with the shapes", "next": "3AA"},
                                            {"id": "B", "text": "Document everything from safety", "next": "3AB"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "The whispers grow into voices. They speak of ancient times, before the Portal, before the Flame.",
                                        "choices": [
                                            {"id": "A", "text": "Ask about the time before creation", "next": "3BA"},
                                            {"id": "B", "text": "Demand to know their purpose", "next": "3BB"}
                                        ]
                                    },
                                    "3AA": {
                                        "text": "The shapes pause. One approaches your barrier, curious rather than hostile.",
                                        "choices": [
                                            {"id": "A", "text": "Lower your wards as a sign of trust", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Maintain the barrier while speaking", "next": "END_GOOD"}
                                        ]
                                    },
                                    "3AB": {
                                        "text": "Your detailed notes capture phenomena never before recorded.",
                                        "choices": [
                                            {"id": "A", "text": "Risk getting closer for more detail", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Compile your findings and retreat", "next": "END_GOOD"}
                                        ]
                                    },
                                    "3BA": {
                                        "text": "The voices reveal glimpses of the Void Before - a time of perfect emptiness. They offer to show you more.",
                                        "choices": [
                                            {"id": "A", "text": "Accept their offer", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Decline but thank them for the knowledge", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "3BB": {
                                        "text": "Silence. Then laughter. They find your demand amusing, but they answer nonetheless.",
                                        "choices": [
                                            {"id": "A", "text": "Press for more information", "next": "END_NEUTRAL"},
                                            {"id": "B", "text": "Accept what they offer and withdraw", "next": "END_GOOD"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "You glimpse the truth of creation itself! Your mind expands with forbidden knowledge.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "Incredible discoveries that will reshape understanding of the Void.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "Valuable intelligence gathered safely. A successful investigation.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "You return with fragments of knowledge, your curiosity only partially satisfied.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-M001'
                    """)

                    # MM-M002: Guild Rivalry (MEDIUM - 3 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'GUILD',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "The tavern falls silent as you enter. Scarred smiths of the Forge Legion glare at hooded Shadow Guild figures. A body lies on the floor - not dead, but beaten badly.",
                                        "choices": [
                                            {"id": "A", "text": "Tend to the wounded first", "next": "2A"},
                                            {"id": "B", "text": "Demand an explanation from both sides", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "Both sides pause as you help the fallen. The wounded man whispers that he saw something - a third party started this.",
                                        "choices": [
                                            {"id": "A", "text": "Announce this to everyone", "next": "3AA"},
                                            {"id": "B", "text": "Quietly investigate the room", "next": "3AB"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "Both guilds shout accusations. The Forge Legion claims cheating. The Shadow Guild claims provocation. Neither will back down.",
                                        "choices": [
                                            {"id": "A", "text": "Appeal to their shared history against the Void", "next": "3BA"},
                                            {"id": "B", "text": "Propose a formal challenge to settle this", "next": "3BB"}
                                        ]
                                    },
                                    "3AA": {
                                        "text": "Your announcement causes both sides to pause. They want proof.",
                                        "choices": [
                                            {"id": "A", "text": "Search the room together for evidence", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Ask the wounded man to identify the saboteur", "next": "END_GOOD"}
                                        ]
                                    },
                                    "3AB": {
                                        "text": "In the shadows, you find marked cards and a sigil belonging to neither guild - the Cult of the Void!",
                                        "choices": [
                                            {"id": "A", "text": "Reveal this to unite both guilds against the real enemy", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Quietly inform the guild leaders in private", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "3BA": {
                                        "text": "You remind them of the Battle of Cinderpeak, when both guilds fought side by side. Some veterans lower their weapons.",
                                        "choices": [
                                            {"id": "A", "text": "Press the advantage - call for peace", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Let them work it out now that tempers have cooled", "next": "END_GOOD"}
                                        ]
                                    },
                                    "3BB": {
                                        "text": "They agree to a formal duel. The champions step forward.",
                                        "choices": [
                                            {"id": "A", "text": "Offer to referee fairly", "next": "END_GOOD"},
                                            {"id": "B", "text": "This is escalation - intervene to stop it", "next": "END_NEUTRAL"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "Both guilds unite against the Void cultists! You have forged an alliance that will change history.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "Peace is restored and both guilds owe you a debt. Your reputation soars.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "The immediate crisis is resolved. Relations remain tense but no blood is shed.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "The duel happens despite your efforts. At least only pride was wounded.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-M002'
                    """)

                    # MM-M003: Ash Beast Tracking (MEDIUM - 3 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'PATROL',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "Massive tracks scar the ashen ground. The ash beasts have been active - and close. The wind shifts, carrying their acrid scent.",
                                        "choices": [
                                            {"id": "A", "text": "Follow the tracks with stealth", "next": "2A"},
                                            {"id": "B", "text": "Find high ground to observe", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "The tracks lead to a ravine. You hear growling below. Through the haze, you see not one beast, but a pack resting in the shadows.",
                                        "choices": [
                                            {"id": "A", "text": "Observe their hierarchy and behavior", "next": "3AA"},
                                            {"id": "B", "text": "Count their numbers and map escape routes", "next": "3AB"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "From the ridge, you spot movement in multiple directions. The beasts are hunting - and their prey appears to be heading toward the settlement.",
                                        "choices": [
                                            {"id": "A", "text": "Race to warn the settlement", "next": "3BA"},
                                            {"id": "B", "text": "Create a distraction to divert the beasts", "next": "3BB"}
                                        ]
                                    },
                                    "3AA": {
                                        "text": "You identify the alpha - a massive scarred beast. Understanding their structure could be key to controlling future encounters.",
                                        "choices": [
                                            {"id": "A", "text": "Continue observing their communication patterns", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Retreat with your current intelligence", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "3AB": {
                                        "text": "Your tactical assessment is thorough. This information could save many lives.",
                                        "choices": [
                                            {"id": "A", "text": "Risk getting closer for exact numbers", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Return immediately with your report", "next": "END_GOOD"}
                                        ]
                                    },
                                    "3BA": {
                                        "text": "You arrive just in time. The settlement can prepare defenses.",
                                        "choices": [
                                            {"id": "A", "text": "Help coordinate the defense personally", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Deliver your warning and return to tracking", "next": "END_GOOD"}
                                        ]
                                    },
                                    "3BB": {
                                        "text": "You create noise and light, drawing the pack toward you. Risky, but effective.",
                                        "choices": [
                                            {"id": "A", "text": "Lead them into a trap zone", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Escape while they investigate", "next": "END_GOOD"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "Your actions have turned the tide! The pack is neutralized and you understand their ways.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "Exceptional intelligence gathering. Your report will guide patrols for months.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "Solid work. The information you gathered will prove valuable.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "Basic tracking completed. The beasts remain a threat but you return safely.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-M003'
                    """)

                    # MM-M004: Crystal Harvesting (MEDIUM - 3 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'EXPLORATION',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "The Singing Caves resonate with crystalline harmonies. Each step releases new notes from the formations around you. The deeper caves pulse with brighter light.",
                                        "choices": [
                                            {"id": "A", "text": "Harvest the outer crystals first", "next": "2A"},
                                            {"id": "B", "text": "Venture deeper toward the source", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "The outer crystals yield easily. As you work, you notice the cave song changing - it seems to respond to your harvesting.",
                                        "choices": [
                                            {"id": "A", "text": "Harvest in rhythm with the song", "next": "3AA"},
                                            {"id": "B", "text": "Work quickly before anything changes", "next": "3AB"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "The deeper caves reveal crystals of extraordinary size and clarity. But the song here is almost deafening, and the light hurts your eyes.",
                                        "choices": [
                                            {"id": "A", "text": "Push through to the heart of the caves", "next": "3BA"},
                                            {"id": "B", "text": "Harvest these exceptional crystals and retreat", "next": "3BB"}
                                        ]
                                    },
                                    "3AA": {
                                        "text": "The cave song harmonizes with your work. Crystals seem to practically offer themselves to you.",
                                        "choices": [
                                            {"id": "A", "text": "Follow the song deeper into the caves", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Complete your harvest in harmony", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "3AB": {
                                        "text": "The song becomes discordant. The cave rumbles.",
                                        "choices": [
                                            {"id": "A", "text": "Drop everything and run", "next": "END_NEUTRAL"},
                                            {"id": "B", "text": "Grab what you can on the way out", "next": "END_GOOD"}
                                        ]
                                    },
                                    "3BA": {
                                        "text": "At the heart of the caves, you find it - a Mother Crystal, source of all resonance in these depths.",
                                        "choices": [
                                            {"id": "A", "text": "Carefully harvest a fragment of the Mother Crystal", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Study it but leave it intact", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "3BB": {
                                        "text": "These crystals are the finest you have ever seen. Pure and powerful.",
                                        "choices": [
                                            {"id": "A", "text": "Take only the best specimens", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Harvest as many as you can carry", "next": "END_GOOD"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "A fragment of the Mother Crystal! Its power alone is worth more than a hundred normal crystals.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "Exceptional crystals of rare purity. The harmonics they produce are beautiful.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "A good haul of quality resonance crystals.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "You escape safely but with meager findings.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-M004'
                    """)

                    # MM-M005: Spirit Communion (MEDIUM - 3 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'LORE',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "The veil between worlds grows thin. Ghostly shapes of fallen emissaries shimmer before you, their eyes carrying the weight of centuries.",
                                        "choices": [
                                            {"id": "A", "text": "Kneel in respect and wait for them to speak", "next": "2A"},
                                            {"id": "B", "text": "Call out to them with questions", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "The spirits appreciate your humility. An ancient warrior steps forward, his spectral form bearing scars from legendary battles.",
                                        "choices": [
                                            {"id": "A", "text": "Ask him about the old wars", "next": "3AA"},
                                            {"id": "B", "text": "Ask if there is anything you can do for him", "next": "3AB"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "Your boldness amuses them. A scholar spirit drifts closer, her form surrounded by ghostly tomes.",
                                        "choices": [
                                            {"id": "A", "text": "Request knowledge of forbidden arts", "next": "3BA"},
                                            {"id": "B", "text": "Ask about the true history of the Portal", "next": "3BB"}
                                        ]
                                    },
                                    "3AA": {
                                        "text": "The warrior speaks of battles against the Void, strategies lost to time. His words carry the weight of hard-won wisdom.",
                                        "choices": [
                                            {"id": "A", "text": "Ask him to train you in spirit combat", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Thank him and commit his words to memory", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "3AB": {
                                        "text": "The warrior is surprised. No one has asked in centuries. He speaks of a message for his descendant in the realm.",
                                        "choices": [
                                            {"id": "A", "text": "Swear to deliver it, whatever the cost", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Promise to try your best", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "3BA": {
                                        "text": "The scholar hesitates. Such knowledge is dangerous. But your desire to learn moves her.",
                                        "choices": [
                                            {"id": "A", "text": "Accept whatever consequences may come", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Ask for only what is safe to know", "next": "END_GOOD"}
                                        ]
                                    },
                                    "3BB": {
                                        "text": "The scholar reveals the Portal was not created - it was awakened. There was something here before, sleeping...",
                                        "choices": [
                                            {"id": "A", "text": "Press for more about what sleeps", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Accept this revelation and retreat", "next": "END_PERFECT"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "The spirits bestow their blessing! Your soul is marked with their eternal wisdom.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "Deep communion achieved. The spirits have shared precious knowledge.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "The spirits shared what they could. You leave with new understanding.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "Brief contact with the other side. Fragments of wisdom, nothing more.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-M005'
                    """)

                    # MM-H001: Void Rift Sealing (HARD - 4 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'LEGENDARY',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "A tear in reality screams before you. Void energy pours through, corrupting everything it touches. Dark shapes move on the other side, waiting to cross.",
                                        "choices": [
                                            {"id": "A", "text": "Begin weaving sealing runes immediately", "next": "2A"},
                                            {"id": "B", "text": "Study the rift to understand its nature", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "Your runes flare against the void energy. The rift resists, pushing back. One of the dark shapes notices your presence.",
                                        "choices": [
                                            {"id": "A", "text": "Pour more power into the sealing", "next": "3AA"},
                                            {"id": "B", "text": "Adapt your runes to harmonize with the void", "next": "3AB"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "The rift is unstable, created by accident or sabotage. You notice the void energy follows patterns, like a language.",
                                        "choices": [
                                            {"id": "A", "text": "Try to communicate through the patterns", "next": "3BA"},
                                            {"id": "B", "text": "Use the patterns to predict the rifts behavior", "next": "3BB"}
                                        ]
                                    },
                                    "3AA": {
                                        "text": "The dark shape fully emerges - a void sentinel! It moves to stop you.",
                                        "choices": [
                                            {"id": "A", "text": "Fight while continuing the seal", "next": "4AAA"},
                                            {"id": "B", "text": "Abandon the seal and defend yourself", "next": "4AAB"}
                                        ]
                                    },
                                    "3AB": {
                                        "text": "Your adapted runes begin to work! The rift shrinks, but the void energy seeks a new host - you.",
                                        "choices": [
                                            {"id": "A", "text": "Accept the energy and redirect it", "next": "4ABA"},
                                            {"id": "B", "text": "Reject it completely and finish the seal", "next": "4ABB"}
                                        ]
                                    },
                                    "3BA": {
                                        "text": "The patterns shift in response! Something intelligent watches from the other side - not hostile, merely curious.",
                                        "choices": [
                                            {"id": "A", "text": "Propose a mutual sealing - peace between realms", "next": "4BAA"},
                                            {"id": "B", "text": "Demand they close their side of the rift", "next": "4BAB"}
                                        ]
                                    },
                                    "3BB": {
                                        "text": "The patterns reveal the rifts weakness - a point where reality is thinnest.",
                                        "choices": [
                                            {"id": "A", "text": "Strike the weak point with all your power", "next": "4BBA"},
                                            {"id": "B", "text": "Carefully repair the weakness with precision magic", "next": "4BBB"}
                                        ]
                                    },
                                    "4AAA": {
                                        "text": "Against impossible odds, you battle and seal simultaneously!",
                                        "choices": [
                                            {"id": "A", "text": "Finish the seal, risking the sentinels final strike", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Destroy the sentinel first, then seal", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4AAB": {
                                        "text": "The sentinel falls but the rift grows. You must act fast.",
                                        "choices": [
                                            {"id": "A", "text": "Sacrifice some of your essence to close it", "next": "END_GOOD"},
                                            {"id": "B", "text": "Use emergency sealing - crude but effective", "next": "END_NEUTRAL"}
                                        ]
                                    },
                                    "4ABA": {
                                        "text": "Void energy courses through you! You become a conduit, redirecting it back through the rift.",
                                        "choices": [
                                            {"id": "A", "text": "Channel it all, whatever the cost", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Release it gradually and safely", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4ABB": {
                                        "text": "Pure rejection! The void recoils from your will.",
                                        "choices": [
                                            {"id": "A", "text": "Push your advantage and seal it completely", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Maintain the seal until reinforcements arrive", "next": "END_GOOD"}
                                        ]
                                    },
                                    "4BAA": {
                                        "text": "The entity agrees! You witness beings from the void weaving their own seal from the other side.",
                                        "choices": [
                                            {"id": "A", "text": "Work together for a permanent seal", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Accept temporary peace", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4BAB": {
                                        "text": "They find your demand amusing but comply - partially.",
                                        "choices": [
                                            {"id": "A", "text": "Accept the partial closure and seal your side", "next": "END_GOOD"},
                                            {"id": "B", "text": "Demand complete closure", "next": "END_NEUTRAL"}
                                        ]
                                    },
                                    "4BBA": {
                                        "text": "Your strike is true! The rift collapses in a cascade of energy.",
                                        "choices": [
                                            {"id": "A", "text": "Absorb the released energy", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Let it dissipate harmlessly", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4BBB": {
                                        "text": "Delicate work, but effective. The rift seals perfectly.",
                                        "choices": [
                                            {"id": "A", "text": "Reinforce the seal with permanent wards", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Leave it as is - stable enough", "next": "END_GOOD"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "You have not just sealed the rift - you have gained power from the void itself! The realm will remember this day.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "The rift is sealed perfectly. Your mastery of the situation was exemplary.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "The rift is closed. It cost you, but the realm is safe.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "The rift is sealed, though imperfectly. It may need attention later.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-H001'
                    """)

                    # MM-H002: Ancient Guardian Trial (HARD - 4 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'LEGENDARY',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "The stone guardian awakens, ancient eyes burning with judgment. It speaks: You seek to prove your worth. Choose your trial.",
                                        "choices": [
                                            {"id": "A", "text": "I choose the Trial of Strength", "next": "2A"},
                                            {"id": "B", "text": "I choose the Trial of Wisdom", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "The guardian raises a massive stone fist. Survive my assault. A barrage of attacks begins.",
                                        "choices": [
                                            {"id": "A", "text": "Meet force with force - attack back", "next": "3AA"},
                                            {"id": "B", "text": "Focus on defense and endurance", "next": "3AB"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "The guardian asks: What is the true purpose of the Portal? The question seems simple, but you sense depth beneath it.",
                                        "choices": [
                                            {"id": "A", "text": "To connect realms and enable travel", "next": "3BA"},
                                            {"id": "B", "text": "To serve a purpose we do not yet understand", "next": "3BB"}
                                        ]
                                    },
                                    "3AA": {
                                        "text": "Your counterattack staggers the guardian! It pauses, surprised. You have shown unexpected power.",
                                        "choices": [
                                            {"id": "A", "text": "Press the advantage - overwhelm it", "next": "4AAA"},
                                            {"id": "B", "text": "Hold back - this is a test, not a war", "next": "4AAB"}
                                        ]
                                    },
                                    "3AB": {
                                        "text": "Wave after wave crashes against you. Your defense holds. The guardian nods with respect.",
                                        "choices": [
                                            {"id": "A", "text": "Now strike back with everything", "next": "4ABA"},
                                            {"id": "B", "text": "Maintain defense until it relents", "next": "4ABB"}
                                        ]
                                    },
                                    "3BA": {
                                        "text": "The guardian considers. A surface answer. Tell me - why do YOU use the Portal?",
                                        "choices": [
                                            {"id": "A", "text": "To protect those who cannot protect themselves", "next": "4BAA"},
                                            {"id": "B", "text": "To grow stronger and face any threat", "next": "4BAB"}
                                        ]
                                    },
                                    "3BB": {
                                        "text": "The guardian tilts its head. Humility before mystery. Intriguing. Tell me what you would do if you knew the Portals true purpose would destroy you.",
                                        "choices": [
                                            {"id": "A", "text": "I would serve the purpose regardless", "next": "4BBA"},
                                            {"id": "B", "text": "I would seek another way to fulfill it", "next": "4BBB"}
                                        ]
                                    },
                                    "4AAA": {
                                        "text": "You drive the guardian back! Stone cracks under your assault.",
                                        "choices": [
                                            {"id": "A", "text": "Finish it - prove absolute dominance", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Offer mercy - the point is proven", "next": "END_LEGENDARY"}
                                        ]
                                    },
                                    "4AAB": {
                                        "text": "The guardian relaxes. You understand. Strength without wisdom destroys itself.",
                                        "choices": [
                                            {"id": "A", "text": "Ask to learn its wisdom", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Accept its acknowledgment", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4ABA": {
                                        "text": "Your strike lands true! The guardian yields.",
                                        "choices": [
                                            {"id": "A", "text": "Demand the highest reward for victory", "next": "END_GOOD"},
                                            {"id": "B", "text": "Thank it for the lesson", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4ABB": {
                                        "text": "The assault ends. You stand unbroken. The trial is complete.",
                                        "choices": [
                                            {"id": "A", "text": "Ask what you have proven", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Request the next trial", "next": "END_LEGENDARY"}
                                        ]
                                    },
                                    "4BAA": {
                                        "text": "The guardian is moved. Selfless dedication. The rarest answer.",
                                        "choices": [
                                            {"id": "A", "text": "It is simply truth", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "I try to be worthy of the Portal", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4BAB": {
                                        "text": "Honest ambition. This I can respect.",
                                        "choices": [
                                            {"id": "A", "text": "Strength serves the realm", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Will you help me grow stronger?", "next": "END_GOOD"}
                                        ]
                                    },
                                    "4BBA": {
                                        "text": "The guardians eyes flare. True devotion! You would give everything.",
                                        "choices": [
                                            {"id": "A", "text": "The realm demands no less", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "I hope it never comes to that", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4BBB": {
                                        "text": "Creative loyalty. You would find a way.",
                                        "choices": [
                                            {"id": "A", "text": "There is always another way", "next": "END_PERFECT"},
                                            {"id": "B", "text": "I believe in balance", "next": "END_GOOD"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "The guardian kneels! It has not done so in a thousand years. You have proven yourself beyond measure.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "The guardian bestows its blessing. You have proven worthy of the ancient trust.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "The trial is passed. You have shown your quality.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "The guardian allows you to leave. Perhaps next time.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-H002'
                    """)

                    # MM-H003: Legendary Artifact Recovery (HARD - 4 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'LEGENDARY',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "The artifact pulses with power in the distance. Ancient defenses surround it - traps, guardians, and worse. Many have sought it. None have returned.",
                                        "choices": [
                                            {"id": "A", "text": "Scout the perimeter for weaknesses", "next": "2A"},
                                            {"id": "B", "text": "Move directly toward the artifact", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "You identify three paths: a trapped main corridor, a narrow crevice, and an ancient air shaft.",
                                        "choices": [
                                            {"id": "A", "text": "Navigate the narrow crevice", "next": "3AA"},
                                            {"id": "B", "text": "Climb through the air shaft", "next": "3AB"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "Traps spring! You dodge blades and flames, but now the guardians know you are here.",
                                        "choices": [
                                            {"id": "A", "text": "Fight through the guardians", "next": "3BA"},
                                            {"id": "B", "text": "Use the chaos to slip past them", "next": "3BB"}
                                        ]
                                    },
                                    "3AA": {
                                        "text": "The crevice leads to an ancient chamber. Writings on the walls speak of the artifacts true nature - it was meant to be found.",
                                        "choices": [
                                            {"id": "A", "text": "Study the writings first", "next": "4AAA"},
                                            {"id": "B", "text": "Press on to the artifact", "next": "4AAB"}
                                        ]
                                    },
                                    "3AB": {
                                        "text": "The air shaft opens above the artifact chamber. You can see it below - and the guardian directly beneath you.",
                                        "choices": [
                                            {"id": "A", "text": "Drop down in a surprise attack", "next": "4ABA"},
                                            {"id": "B", "text": "Wait for the guardian to move", "next": "4ABB"}
                                        ]
                                    },
                                    "3BA": {
                                        "text": "Guardian after guardian falls. Your path is littered with stone fragments. The artifact chamber lies ahead.",
                                        "choices": [
                                            {"id": "A", "text": "Claim the artifact immediately", "next": "4BAA"},
                                            {"id": "B", "text": "Check for one final trap", "next": "4BAB"}
                                        ]
                                    },
                                    "3BB": {
                                        "text": "You slip through during the confusion. The artifact gleams before you, unguarded for this moment.",
                                        "choices": [
                                            {"id": "A", "text": "Grab it and run", "next": "4BBA"},
                                            {"id": "B", "text": "Carefully disconnect it from its pedestal", "next": "4BBB"}
                                        ]
                                    },
                                    "4AAA": {
                                        "text": "The writings reveal this was a test all along. Those worthy enough to seek knowledge first deserve the artifact.",
                                        "choices": [
                                            {"id": "A", "text": "Accept the title of Seeker", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Take the artifact humbly", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4AAB": {
                                        "text": "You reach the artifact. As you touch it, visions flood your mind.",
                                        "choices": [
                                            {"id": "A", "text": "Embrace the visions fully", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Take the artifact and leave quickly", "next": "END_GOOD"}
                                        ]
                                    },
                                    "4ABA": {
                                        "text": "Your attack destroys the guardian! The artifact is yours.",
                                        "choices": [
                                            {"id": "A", "text": "Attune to its power immediately", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Secure it for later study", "next": "END_GOOD"}
                                        ]
                                    },
                                    "4ABB": {
                                        "text": "The guardian leaves. You descend silently and retrieve the artifact without conflict.",
                                        "choices": [
                                            {"id": "A", "text": "Study its nature before leaving", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Escape before anything changes", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4BAA": {
                                        "text": "The artifact is yours! But it feels... incomplete?",
                                        "choices": [
                                            {"id": "A", "text": "Search for what is missing", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Leave with what you have", "next": "END_GOOD"}
                                        ]
                                    },
                                    "4BAB": {
                                        "text": "Your instinct was right - a pressure plate! You disable it and claim your prize.",
                                        "choices": [
                                            {"id": "A", "text": "Check if there is more", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Take the artifact and go", "next": "END_GOOD"}
                                        ]
                                    },
                                    "4BBA": {
                                        "text": "Alarms blare! You run with the artifact as the temple collapses.",
                                        "choices": [
                                            {"id": "A", "text": "Dive for the exit", "next": "END_GOOD"},
                                            {"id": "B", "text": "Use the artifacts power to escape", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4BBB": {
                                        "text": "You carefully disconnect it. The temple remains stable. You have time.",
                                        "choices": [
                                            {"id": "A", "text": "Explore for additional treasures", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Leave while fortune favors you", "next": "END_PERFECT"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "The artifact recognizes you as a true Seeker! Additional rewards manifest from the ancient vaults.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "The legendary artifact is yours! Its power already responds to your touch.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "You escape with the artifact. A successful recovery.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "The artifact is secured, though the journey cost you much.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-H003'
                    """)

                    # MM-H004: Elite Ash Beast Hunt (HARD - 4 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'PATROL',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "Massive tracks scar the landscape. The alpha ash beast - a creature of legend and nightmare. Its pack decimated a patrol last night. This ends now.",
                                        "choices": [
                                            {"id": "A", "text": "Track it to its lair", "next": "2A"},
                                            {"id": "B", "text": "Set an ambush at the water source", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "The tracks lead to a volcanic cave. Heat radiates from within. You hear the beast breathing.",
                                        "choices": [
                                            {"id": "A", "text": "Enter the cave for close combat", "next": "3AA"},
                                            {"id": "B", "text": "Smoke it out with fire bombs", "next": "3AB"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "You wait at the ashen spring. As dusk falls, the massive form appears. It is even larger than the reports suggested.",
                                        "choices": [
                                            {"id": "A", "text": "Spring the trap immediately", "next": "3BA"},
                                            {"id": "B", "text": "Wait for it to drink and lower its guard", "next": "3BB"}
                                        ]
                                    },
                                    "3AA": {
                                        "text": "The beast lunges from the darkness! In the confined space, its size becomes a weakness.",
                                        "choices": [
                                            {"id": "A", "text": "Use your agility to strike vital points", "next": "4AAA"},
                                            {"id": "B", "text": "Collapse the cave entrance, trapping it", "next": "4AAB"}
                                        ]
                                    },
                                    "3AB": {
                                        "text": "The beast charges out, enraged and partially blinded by smoke. Other pack members follow.",
                                        "choices": [
                                            {"id": "A", "text": "Focus on the alpha - the pack will scatter", "next": "4ABA"},
                                            {"id": "B", "text": "Separate the alpha from its pack first", "next": "4ABB"}
                                        ]
                                    },
                                    "3BA": {
                                        "text": "Your trap catches its leg! The beast howls in fury and turns toward you.",
                                        "choices": [
                                            {"id": "A", "text": "Press the attack while it is restrained", "next": "4BAA"},
                                            {"id": "B", "text": "Keep distance and wear it down", "next": "4BAB"}
                                        ]
                                    },
                                    "3BB": {
                                        "text": "Patient hunter. The beast drinks deeply, unaware. You have the perfect angle.",
                                        "choices": [
                                            {"id": "A", "text": "Strike for an instant kill", "next": "4BBA"},
                                            {"id": "B", "text": "Wound it first, then finish carefully", "next": "4BBB"}
                                        ]
                                    },
                                    "4AAA": {
                                        "text": "You dance around its strikes, blade finding weakness after weakness.",
                                        "choices": [
                                            {"id": "A", "text": "Go for the killing blow", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Drive it from its lair defeated", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4AAB": {
                                        "text": "The cave collapses! You escape as the beast is buried.",
                                        "choices": [
                                            {"id": "A", "text": "Confirm the kill in the rubble", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Report it destroyed and leave", "next": "END_GOOD"}
                                        ]
                                    },
                                    "4ABA": {
                                        "text": "The alpha falls! Without their leader, the pack flees into the wastes.",
                                        "choices": [
                                            {"id": "A", "text": "Hunt down the remaining pack", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Let them scatter - the alpha was the goal", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4ABB": {
                                        "text": "You draw the alpha away. Alone, it is still deadly but manageable.",
                                        "choices": [
                                            {"id": "A", "text": "Finish it in single combat", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Lead it into a secondary trap", "next": "END_GOOD"}
                                        ]
                                    },
                                    "4BAA": {
                                        "text": "Your assault is relentless! The beast cannot defend and free itself.",
                                        "choices": [
                                            {"id": "A", "text": "End it with honor", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "End it quickly", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4BAB": {
                                        "text": "Blood loss weakens the beast. It finally collapses.",
                                        "choices": [
                                            {"id": "A", "text": "Grant it a warriors end", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Ensure it cannot recover", "next": "END_GOOD"}
                                        ]
                                    },
                                    "4BBA": {
                                        "text": "One perfect strike! The alpha falls without knowing what killed it.",
                                        "choices": [
                                            {"id": "A", "text": "Take a trophy to prove the kill", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Leave its body as warning to others", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4BBB": {
                                        "text": "Wounded, the beast still fights. But its strength fails.",
                                        "choices": [
                                            {"id": "A", "text": "Finish what you started", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Let it bleed out - no need to risk more", "next": "END_GOOD"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "The alpha falls and you become legend! Songs will be sung of this hunt for generations.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "A masterful hunt! The beast is slain and the realm is safer.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "The hunt is successful. The alpha will threaten no more.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "The beast is driven off. It may return, but not today.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-H004'
                    """)

                    # MM-H005: Forge of Legends (HARD - 4 steps)
                    cur.execute("""
                        UPDATE micro_missions SET
                            category = 'GUILD',
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "The master smith has summoned you. Today, legend shall be forged. The metal is ancient starmetal, the forge burns with First Flame essence. This is a sacred moment.",
                                        "choices": [
                                            {"id": "A", "text": "Ask what role you will play", "next": "2A"},
                                            {"id": "B", "text": "Offer your ember essence to the forging", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "The master explains: You will hold the intention. As I shape the metal, you must focus your will upon what this weapon shall become.",
                                        "choices": [
                                            {"id": "A", "text": "Focus on protection - a guardians weapon", "next": "3AA"},
                                            {"id": "B", "text": "Focus on destruction - a conquerors weapon", "next": "3AB"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "The master pauses, surprised. You would give of yourself? He nods slowly. Then your essence shall be part of the legend.",
                                        "choices": [
                                            {"id": "A", "text": "Give freely, without reservation", "next": "3BA"},
                                            {"id": "B", "text": "Give carefully, maintaining your strength", "next": "3BB"}
                                        ]
                                    },
                                    "3AA": {
                                        "text": "The metal glows with defensive sigils. But the master asks: What would you protect?",
                                        "choices": [
                                            {"id": "A", "text": "The innocent who cannot fight", "next": "4AAA"},
                                            {"id": "B", "text": "The realm and all within it", "next": "4AAB"}
                                        ]
                                    },
                                    "3AB": {
                                        "text": "The metal crackles with destructive force. The master asks: What would you destroy?",
                                        "choices": [
                                            {"id": "A", "text": "The enemies of the realm", "next": "4ABA"},
                                            {"id": "B", "text": "The darkness that threatens all light", "next": "4ABB"}
                                        ]
                                    },
                                    "3BA": {
                                        "text": "Your essence pours into the metal. You feel weakened but the weapon glows with incredible power.",
                                        "choices": [
                                            {"id": "A", "text": "Give even more - make it perfect", "next": "4BAA"},
                                            {"id": "B", "text": "Trust that what you gave is enough", "next": "4BAB"}
                                        ]
                                    },
                                    "3BB": {
                                        "text": "Your measured contribution stabilizes the forging. The weapon will be excellent, if not transcendent.",
                                        "choices": [
                                            {"id": "A", "text": "Add more - reach for greatness", "next": "4BBA"},
                                            {"id": "B", "text": "Excellence is achievement enough", "next": "4BBB"}
                                        ]
                                    },
                                    "4AAA": {
                                        "text": "The Defenders Intent! The weapon becomes a shield-blade, protecting its wielder and those behind them.",
                                        "choices": [
                                            {"id": "A", "text": "Name it in honor of the fallen", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Let its deeds name it", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4AAB": {
                                        "text": "The Realms Intent! The weapon resonates with the land itself.",
                                        "choices": [
                                            {"id": "A", "text": "Bind it to the Portal", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Let it find its own purpose", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4ABA": {
                                        "text": "The Warriors Intent! The weapon hungers for battle.",
                                        "choices": [
                                            {"id": "A", "text": "Temper it with wisdom", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Let it be what it is", "next": "END_GOOD"}
                                        ]
                                    },
                                    "4ABB": {
                                        "text": "The Lights Intent! The weapon burns with inner fire that void creatures will fear.",
                                        "choices": [
                                            {"id": "A", "text": "Dedicate it to the First Flame", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Let it carry its own light", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4BAA": {
                                        "text": "You give everything. The weapon achieves a perfection rarely seen. But you collapse.",
                                        "choices": [
                                            {"id": "A", "text": "It was worth any cost", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "The master catches you - you survive", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4BAB": {
                                        "text": "The forging completes. The weapon is exceptional - touched by your essence.",
                                        "choices": [
                                            {"id": "A", "text": "Request to wield it yourself", "next": "END_PERFECT"},
                                            {"id": "B", "text": "Let the master decide its fate", "next": "END_GOOD"}
                                        ]
                                    },
                                    "4BBA": {
                                        "text": "The additional essence pushes the forging higher! The master works in awe.",
                                        "choices": [
                                            {"id": "A", "text": "See it through to the end", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Trust the master to finish", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "4BBB": {
                                        "text": "The weapon forms beautifully - excellent craftsmanship with a touch of your essence.",
                                        "choices": [
                                            {"id": "A", "text": "Be proud of your contribution", "next": "END_GOOD"},
                                            {"id": "B", "text": "Learn from the experience for next time", "next": "END_GOOD"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "A weapon of legend is born! Your contribution will be remembered as long as the weapon exists.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "An exceptional weapon forged with your essence! The master smith bows in respect.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "You contributed to the forging of a fine weapon. The experience was invaluable.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "The forging completes. Your role was small but you learned much.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE id = 'MM-H005'
                    """)

                    # =========================================================
                    # GENERIC FALLBACK: Add narrative_steps for ANY mission without it
                    # This ensures ALL missions work with the multi-step system
                    # =========================================================
                    print("[Migration] Adding generic narrative for missions without narrative_steps...")
                    cur.execute("""
                        UPDATE micro_missions SET
                            narrative_steps = '{
                                "steps": {
                                    "1": {
                                        "text": "Your emissary embarks on the mission. The path ahead is uncertain, but your resolve is strong.",
                                        "choices": [
                                            {"id": "A", "text": "Take the cautious approach", "next": "2A"},
                                            {"id": "B", "text": "Act boldly and decisively", "next": "2B"}
                                        ]
                                    },
                                    "2A": {
                                        "text": "Your careful approach pays off. You avoid potential dangers and make steady progress.",
                                        "choices": [
                                            {"id": "A", "text": "Continue with caution to the end", "next": "END_GOOD"},
                                            {"id": "B", "text": "Take a calculated risk for greater reward", "next": "END_PERFECT"}
                                        ]
                                    },
                                    "2B": {
                                        "text": "Your boldness is rewarded! Opportunities present themselves to those who dare.",
                                        "choices": [
                                            {"id": "A", "text": "Press your advantage further", "next": "END_LEGENDARY"},
                                            {"id": "B", "text": "Consolidate your gains", "next": "END_GOOD"}
                                        ]
                                    }
                                },
                                "endings": {
                                    "END_LEGENDARY": {"type": "LEGENDARY", "text": "Outstanding success! Your emissary has achieved legendary results.", "pyre_mod": 2.0, "xp_mod": 2.0},
                                    "END_PERFECT": {"type": "PERFECT", "text": "Excellent work! Your calculated risk has paid off handsomely.", "pyre_mod": 1.5, "xp_mod": 1.4},
                                    "END_GOOD": {"type": "GOOD", "text": "Well done! The mission concludes successfully.", "pyre_mod": 1.2, "xp_mod": 1.2},
                                    "END_NEUTRAL": {"type": "NEUTRAL", "text": "The mission is complete. You have fulfilled your duty.", "pyre_mod": 1.0, "xp_mod": 1.0}
                                }
                            }'::jsonb
                        WHERE narrative_steps IS NULL
                           OR narrative_steps = '{}'::jsonb
                           OR narrative_steps::text = '{}'
                           OR NOT (narrative_steps ? 'steps')
                    """)
                    generic_updated = cur.rowcount
                    print(f"[Migration] Added generic narrative to {generic_updated} missions")

                    # AGGRESSIVE CLEANUP: Remove ALL expired/corrupted micro-missions
                    # This prevents emissaries from getting stuck with no action buttons

                    # 1. Delete any micro-mission that has already ended
                    cur.execute("""
                        DELETE FROM active_micro_missions
                        WHERE status IN ('active', 'choice_pending')
                        AND ends_at < NOW()
                    """)

                    # 2. Delete any micro-mission older than 10 minutes (max should be 5 min)
                    cur.execute("""
                        DELETE FROM active_micro_missions
                        WHERE status IN ('active', 'choice_pending')
                        AND started_at < NOW() - INTERVAL '10 minutes'
                    """)

                    # 3. Delete any micro-mission with NULL ends_at (corrupted data)
                    cur.execute("""
                        DELETE FROM active_micro_missions
                        WHERE status IN ('active', 'choice_pending')
                        AND ends_at IS NULL
                    """)

                    # 4. Force complete any stuck micro-missions
                    cur.execute("""
                        UPDATE active_micro_missions
                        SET status = 'expired', completed_at = NOW()
                        WHERE status IN ('active', 'choice_pending')
                        AND (
                            ends_at < NOW() - INTERVAL '1 minute'
                            OR started_at < NOW() - INTERVAL '15 minutes'
                        )
                    """)

                    print("🧹 Cleaned up expired/corrupted micro-missions")

                    # =========================================================
                    # FIX DURATIONS: EASY=120s, MEDIUM=240s, HARD=360s
                    # =========================================================
                    cur.execute("""
                        UPDATE micro_missions SET duration_seconds = 120 WHERE difficulty = 'EASY'
                    """)
                    cur.execute("""
                        UPDATE micro_missions SET duration_seconds = 240 WHERE difficulty = 'MEDIUM'
                    """)
                    cur.execute("""
                        UPDATE micro_missions SET duration_seconds = 300 WHERE difficulty = 'HARD'
                    """)

                    # Also fix ends_at for any active missions with wrong duration
                    cur.execute("""
                        UPDATE active_micro_missions amm SET
                            ends_at = amm.started_at + (mm.duration_seconds * interval '1 second')
                        FROM micro_missions mm
                        WHERE amm.micro_mission_id = mm.id
                        AND amm.status IN ('active', 'choice_pending')
                    """)
                    print("⏱️ Fixed mission durations (EASY=2min, MEDIUM=4min, HARD=6min)")

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

                    # Calculate end time
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
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

                    # Find current step (can be "1", "2A", "2B", "3A", etc.)
                    # First step is always "1", subsequent steps are stored in choices_path progression
                    if len(choices_path) == 0:
                        step_key = "1"
                    else:
                        # Reconstruct step key from choices_path
                        step_key = str(len(choices_path) + 1) + choices_path[-1] if choices_path else "1"
                        # Actually, we store the step key directly after first choice
                        # Let's use a simpler approach: store the current step key
                        pass

                    # For simplicity, let's use current_step as the step key directly
                    step_key = str(current_step) if current_step else "1"
                    current_step_data = steps.get(step_key, {})

                    if not current_step_data:
                        # Try finding the step another way - maybe it's like "2A" after first choice
                        # Reconstruct from choices_path
                        if len(choices_path) > 0:
                            step_key = str(len(choices_path) + 1) + choices_path[-1]
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

                    # Get the next step
                    next_step = chosen_option.get('next', '')

                    # Update choices_path
                    new_choices_path = choices_path + [choice]

                    # Check if this leads to an ending
                    if next_step.startswith('END_'):
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
                            "message": "The story reaches its conclusion. Wait for the timer to claim rewards."
                        })
                    else:
                        # More steps to go - update current step
                        next_step_data = steps.get(next_step, {})
                        next_text = next_step_data.get('text', 'The story continues...')
                        next_choices = next_step_data.get('choices', [])

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
                            "narrative_text": next_text,
                            "choices": next_choices,
                            "choices_path": new_choices_path,
                            "message": "Continue your journey..."
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

                    # Check if time has passed
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    if now < row[3]:  # ends_at
                        remaining = (row[3] - now).total_seconds()
                        return jsonify({
                            "error": "Mission not yet complete",
                            "remaining_seconds": int(remaining)
                        }), 400

                    # Extract ending data for multi-step adventures
                    ending_reached = row[15]
                    narrative_steps = row[16] or {}
                    endings = narrative_steps.get('endings', {})

                    # Calculate base rewards
                    pyre_earned = random.randint(row[6], row[7])  # pyre_reward_min/max
                    xp_earned = random.randint(row[8], row[9])     # xp_reward_min/max
                    aura_earned = 1 if random.random() * 100 < float(row[10] or 0) else 0

                    # EMBER REWARD: Calculate ember from micro-mission
                    ember_min = row[13] or 0  # ember_reward_min
                    ember_max = row[14] or 0  # ember_reward_max
                    ember_earned = random.randint(ember_min, ember_max) if ember_min > 0 and ember_max > 0 else 0

                    # Apply ending modifiers for multi-step adventures
                    ending_type = None
                    if ending_reached and ending_reached in endings:
                        ending_data = endings[ending_reached]
                        ending_type = ending_data.get('type', 'NEUTRAL')

                        # Apply modifiers based on ending
                        pyre_mod = ending_data.get('pyre_mod', 1.0)
                        xp_mod = ending_data.get('xp_mod', 1.0)
                        ember_mod = ending_data.get('ember_mod', pyre_mod)  # Default ember to pyre modifier
                        aura_mod = ending_data.get('aura_mod', 1.0)

                        pyre_earned = int(pyre_earned * pyre_mod)
                        xp_earned = int(xp_earned * xp_mod)
                        ember_earned = int(ember_earned * ember_mod)

                        # Aura boost for legendary endings
                        if ending_type == 'LEGENDARY' and aura_earned == 0:
                            # 50% extra chance for aura on legendary endings
                            aura_earned = 1 if random.random() < 0.5 else 0
                    else:
                        # Legacy: Apply choice modifier if applicable
                        choice = row[4]
                        outcomes = row[12] or {}
                        if choice and choice in outcomes:
                            modifier = outcomes[choice].get('pyre_modifier', 1.0)
                            pyre_earned = int(pyre_earned * modifier)
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
                        "ending_type": ending_type,
                        "ending_reached": ending_reached,
                        "emissary_token_id": token_id
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
        EMERGENCY: Clean up ALL corrupted active micro-missions.
        This will free all emissaries stuck in ON_MICRO_MISSION state.
        """
        if not POSTGRESQL_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Count before cleanup
                    cur.execute("SELECT COUNT(*) FROM active_micro_missions WHERE status IN ('active', 'choice_pending')")
                    count_before = cur.fetchone()[0]

                    # Get emissary token IDs from active micro missions (to reset their state)
                    cur.execute("""
                        SELECT DISTINCT emissary_token_id FROM active_micro_missions
                        WHERE status IN ('active', 'choice_pending')
                    """)
                    stuck_emissary_tokens = [row[0] for row in cur.fetchall()]

                    # Delete ALL active/pending micro missions
                    cur.execute("""
                        DELETE FROM active_micro_missions
                        WHERE status IN ('active', 'choice_pending')
                    """)
                    deleted = cur.rowcount

                    # Reset emissary states to READY for all stuck emissaries
                    emissaries_reset = 0
                    for token_id in stuck_emissary_tokens:
                        cur.execute("""
                            UPDATE nfts SET
                                dynamic_state = jsonb_set(
                                    COALESCE(dynamic_state, '{}'::jsonb),
                                    '{state}',
                                    '"READY"'
                                ),
                                last_update = NOW()
                            WHERE token_id = %s
                        """, (token_id,))
                        emissaries_reset += cur.rowcount

                    # Also reset any emissary with ON_MICRO_MISSION state that doesn't have an active mission
                    cur.execute("""
                        UPDATE nfts SET
                            dynamic_state = jsonb_set(
                                COALESCE(dynamic_state, '{}'::jsonb),
                                '{state}',
                                '"READY"'
                            ),
                            last_update = NOW()
                        WHERE dynamic_state->>'state' = 'ON_MICRO_MISSION'
                        AND token_id NOT IN (
                            SELECT emissary_token_id FROM active_micro_missions
                            WHERE status IN ('active', 'choice_pending')
                        )
                    """)
                    orphaned_reset = cur.rowcount

                    print(f"[Emergency Cleanup] Deleted {deleted} missions, reset {emissaries_reset} emissaries, fixed {orphaned_reset} orphaned states")

                    # Force update narrative data (remove restrictive conditions)
                    cur.execute("""
                        UPDATE micro_missions SET
                            narrative_choices = '[
                                {"id": "A", "text": "Listen closely to the whispers", "icon": "ear"},
                                {"id": "B", "text": "Add fuel to strengthen the flame", "icon": "flame"},
                                {"id": "C", "text": "Attempt to communicate back", "icon": "chat"}
                            ]'::jsonb,
                            narrative_outcomes = '{
                                "A": {"type": "GOOD", "text": "The whispers reveal ancient knowledge.", "pyre_modifier": 1.2, "xp_modifier": 1.3},
                                "B": {"type": "PERFECT", "text": "The flame bestows a blessing!", "pyre_modifier": 1.5, "xp_modifier": 1.4},
                                "C": {"type": "NEUTRAL", "text": "The flame does not respond.", "pyre_modifier": 0.9, "xp_modifier": 1.0}
                            }'::jsonb
                        WHERE id = 'MM-E001'
                    """)

                    cur.execute("""
                        UPDATE micro_missions SET
                            narrative_choices = '[
                                {"id": "A", "text": "Gather quickly before they fade", "icon": "run"},
                                {"id": "B", "text": "Select only the brightest embers", "icon": "gem"},
                                {"id": "C", "text": "Follow the ember trail to its source", "icon": "compass"}
                            ]'::jsonb,
                            narrative_outcomes = '{
                                "A": {"type": "GOOD", "text": "Quick reflexes save many embers!", "pyre_modifier": 1.2, "xp_modifier": 1.1},
                                "B": {"type": "NEUTRAL", "text": "Fewer but exceptional embers.", "pyre_modifier": 1.0, "xp_modifier": 1.0},
                                "C": {"type": "PERFECT", "text": "You discover a hidden ember nest!", "pyre_modifier": 1.4, "xp_modifier": 1.5}
                            }'::jsonb
                        WHERE id = 'MM-E002'
                    """)

                    cur.execute("""
                        UPDATE micro_missions SET
                            narrative_choices = '[
                                {"id": "A", "text": "Maintain vigilant watch", "icon": "eye"},
                                {"id": "B", "text": "Investigate the mists", "icon": "search"},
                                {"id": "C", "text": "Signal other guards", "icon": "bell"}
                            ]'::jsonb,
                            narrative_outcomes = '{
                                "A": {"type": "NEUTRAL", "text": "A quiet but successful patrol.", "pyre_modifier": 1.0, "xp_modifier": 1.0},
                                "B": {"type": "PERFECT", "text": "You seal a tear in the veil!", "pyre_modifier": 1.5, "xp_modifier": 1.4},
                                "C": {"type": "GOOD", "text": "Teamwork neutralizes a threat.", "pyre_modifier": 1.2, "xp_modifier": 1.2}
                            }'::jsonb
                        WHERE id = 'MM-E003'
                    """)

                    cur.execute("""
                        UPDATE micro_missions SET
                            narrative_choices = '[
                                {"id": "A", "text": "Empty your mind completely", "icon": "mind"},
                                {"id": "B", "text": "Focus on a specific question", "icon": "question"},
                                {"id": "C", "text": "Let the rune guide you", "icon": "rune"}
                            ]'::jsonb,
                            narrative_outcomes = '{
                                "A": {"type": "GOOD", "text": "Power flows through your empty mind.", "pyre_modifier": 1.2, "xp_modifier": 1.1},
                                "B": {"type": "NEUTRAL", "text": "The rune offers no clear answer.", "pyre_modifier": 0.9, "xp_modifier": 1.0},
                                "C": {"type": "PERFECT", "text": "Ancient Runesmiths speak through time!", "pyre_modifier": 1.4, "xp_modifier": 1.5}
                            }'::jsonb
                        WHERE id = 'MM-E004'
                    """)

                    cur.execute("""
                        UPDATE micro_missions SET
                            narrative_choices = '[
                                {"id": "A", "text": "Pump the bellows", "icon": "wind"},
                                {"id": "B", "text": "Sort the metal ingots", "icon": "boxes"},
                                {"id": "C", "text": "Watch the master work", "icon": "eye"}
                            ]'::jsonb,
                            narrative_outcomes = '{
                                "A": {"type": "GOOD", "text": "Perfect forge temperature achieved.", "pyre_modifier": 1.2, "xp_modifier": 1.2},
                                "B": {"type": "NEUTRAL", "text": "Organization is the foundation.", "pyre_modifier": 1.0, "xp_modifier": 1.0},
                                "C": {"type": "PERFECT", "text": "The master shares a secret technique!", "pyre_modifier": 1.3, "xp_modifier": 1.5}
                            }'::jsonb
                        WHERE id = 'MM-E005'
                    """)

                    # Update all remaining missions with default choices
                    cur.execute("""
                        UPDATE micro_missions SET
                            narrative_choices = '[
                                {"id": "A", "text": "Take the cautious approach", "icon": "shield"},
                                {"id": "B", "text": "Act boldly and swiftly", "icon": "sword"},
                                {"id": "C", "text": "Seek a clever solution", "icon": "book"}
                            ]'::jsonb,
                            narrative_outcomes = '{
                                "A": {"type": "NEUTRAL", "text": "Caution serves you well.", "pyre_modifier": 1.0, "xp_modifier": 1.0},
                                "B": {"type": "GOOD", "text": "Fortune favors the bold!", "pyre_modifier": 1.3, "xp_modifier": 1.2},
                                "C": {"type": "PERFECT", "text": "Your wit earns great rewards!", "pyre_modifier": 1.5, "xp_modifier": 1.5}
                            }'::jsonb
                        WHERE narrative_choices IS NULL OR narrative_choices = '[]'::jsonb OR narrative_choices::text = '[]'
                    """)

                    # Verify updates
                    cur.execute("SELECT COUNT(*) FROM micro_missions WHERE narrative_choices IS NOT NULL AND narrative_choices::text != '[]'")
                    missions_updated = cur.fetchone()[0]

                    total_emissaries_fixed = emissaries_reset + orphaned_reset
                    return jsonify({
                        "success": True,
                        "deleted_missions": deleted,
                        "emissaries_reset": total_emissaries_fixed,
                        "missions_with_narrative": missions_updated,
                        "message": f"Cleanup complete! Deleted {deleted} corrupted missions, reset {total_emissaries_fixed} emissary states. {missions_updated} missions now have narrative data."
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
