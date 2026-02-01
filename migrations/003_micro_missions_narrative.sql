-- =========================================================================
-- EMBERHOLM PORTAL - MIGRATION 003: Micro-Missions Narrative System
-- =========================================================================
-- Este script añade las columnas y tablas necesarias para el sistema
-- narrativo "choose your own adventure" de micro-misiones
-- =========================================================================
-- Ejecutar DESPUÉS de 002_seed_micro_missions.sql
-- =========================================================================

BEGIN;

-- =========================================================================
-- 1. AÑADIR COLUMNAS NARRATIVAS A micro_missions
-- =========================================================================

-- Columna para las opciones de decisión (JSONB array)
ALTER TABLE micro_missions
ADD COLUMN IF NOT EXISTS narrative_choices JSONB DEFAULT '[]'::jsonb;

-- Columna para los resultados según la elección (JSONB object)
ALTER TABLE micro_missions
ADD COLUMN IF NOT EXISTS narrative_outcomes JSONB DEFAULT '{}'::jsonb;

-- Columna para categoría de misión (PATROL, EXPLORATION, LORE, GUILD, LEGENDARY)
ALTER TABLE micro_missions
ADD COLUMN IF NOT EXISTS category VARCHAR(20) DEFAULT 'PATROL';

-- Columna para conexión con lore del mundo
ALTER TABLE micro_missions
ADD COLUMN IF NOT EXISTS lore_connection TEXT;

-- Columna para logros desbloqueables
ALTER TABLE micro_missions
ADD COLUMN IF NOT EXISTS achievements JSONB DEFAULT '{}'::jsonb;

-- =========================================================================
-- 2. CREAR TABLA active_micro_missions (misiones en progreso)
-- =========================================================================

CREATE TABLE IF NOT EXISTS active_micro_missions (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(42) NOT NULL,
    emissary_token_id VARCHAR(10) NOT NULL,
    micro_mission_id VARCHAR(20) NOT NULL REFERENCES micro_missions(id),
    current_step INTEGER DEFAULT 0,
    choice_made VARCHAR(50),
    score INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'choice_pending', 'completed', 'claimed', 'abandoned', 'failed')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ends_at TIMESTAMP,
    completed_at TIMESTAMP,
    outcome_type VARCHAR(20),
    outcome_text TEXT,
    pyre_earned NUMERIC(18,2) DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    aura_earned INTEGER DEFAULT 0,
    rewards_claimed BOOLEAN DEFAULT FALSE
);

-- Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_active_micro_missions_wallet ON active_micro_missions(wallet);
CREATE INDEX IF NOT EXISTS idx_active_micro_missions_status ON active_micro_missions(status);
CREATE INDEX IF NOT EXISTS idx_active_micro_missions_wallet_status ON active_micro_missions(wallet, status);

-- =========================================================================
-- 3. CREAR TABLA micro_mission_cooldowns (cooldowns por misión específica)
-- =========================================================================

CREATE TABLE IF NOT EXISTS micro_mission_cooldowns (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(42) NOT NULL,
    micro_mission_id VARCHAR(20) NOT NULL REFERENCES micro_missions(id),
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cooldown_until TIMESTAMP NOT NULL,
    UNIQUE(wallet, micro_mission_id)
);

-- Índice para consultas de cooldown
CREATE INDEX IF NOT EXISTS idx_cooldowns_wallet_mission ON micro_mission_cooldowns(wallet, micro_mission_id);

-- =========================================================================
-- 4. CREAR TABLA micro_mission_history (historial completo)
-- =========================================================================

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
);

-- Índice para historial por wallet
CREATE INDEX IF NOT EXISTS idx_history_wallet ON micro_mission_history(wallet);

-- =========================================================================
-- 5. ACTUALIZAR MISIONES EXISTENTES CON DATOS NARRATIVOS
-- =========================================================================

-- MM-E001: The Whispering Flame (LORE)
UPDATE micro_missions SET
    category = 'LORE',
    narrative_choices = '[
        {"id": "A", "text": "Listen closely to the whispers", "icon": "ear"},
        {"id": "B", "text": "Add fuel to strengthen the flame", "icon": "flame"},
        {"id": "C", "text": "Attempt to communicate back", "icon": "chat"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "GOOD",
            "text": "The whispers reveal a fragment of ancient knowledge. The flame seems pleased with your patience, sharing visions of Emberholm''s founding days.",
            "pyre_modifier": 1.2,
            "xp_modifier": 1.3
        },
        "B": {
            "type": "PERFECT",
            "text": "As you add sacred kindling, the flame roars to life! It speaks clearly now, bestowing upon you a blessing of the First Flame. Your connection to Emberholm deepens.",
            "pyre_modifier": 1.5,
            "xp_modifier": 1.4
        },
        "C": {
            "type": "NEUTRAL",
            "text": "Your words echo strangely in the chamber. The flame flickers but does not respond directly. Perhaps you''ll understand its language another day.",
            "pyre_modifier": 0.9,
            "xp_modifier": 1.0
        }
    }'::jsonb,
    lore_connection = 'The Eternal Brazier has burned since the First Spark, a direct connection to the primal flames that birthed Emberholm.',
    achievements = '{
        "flame_listener": {
            "name": "Flame Listener",
            "description": "Heard the whispers of the Eternal Brazier",
            "icon": "flame"
        }
    }'::jsonb
WHERE id = 'MM-E001';

-- MM-E002: Ember Gathering (PATROL)
UPDATE micro_missions SET
    category = 'PATROL',
    narrative_choices = '[
        {"id": "A", "text": "Gather quickly before they fade", "icon": "run"},
        {"id": "B", "text": "Carefully select only the brightest embers", "icon": "gem"},
        {"id": "C", "text": "Follow the ember trail to its source", "icon": "compass"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "GOOD",
            "text": "You dash across the fields, scooping embers into your pouch. Your quick reflexes save many from fading back to void!",
            "pyre_modifier": 1.2,
            "xp_modifier": 1.1
        },
        "B": {
            "type": "NEUTRAL",
            "text": "You take your time, selecting only the finest embers. Fewer in number, but each one burns with exceptional intensity.",
            "pyre_modifier": 1.0,
            "xp_modifier": 1.0
        },
        "C": {
            "type": "PERFECT",
            "text": "Following the trail, you discover a hidden ember nest! A concentration of power that few have ever witnessed. You gather a magnificent haul.",
            "pyre_modifier": 1.4,
            "xp_modifier": 1.5
        }
    }'::jsonb,
    lore_connection = 'Embers scatter across Emberholm when the veil between worlds weakens. Gathering them strengthens the realm.',
    achievements = '{
        "ember_collector": {
            "name": "Ember Collector",
            "description": "Gathered embers from the Ashen Fields",
            "icon": "sparkle"
        }
    }'::jsonb
WHERE id = 'MM-E002';

-- MM-E003: Patrol the Perimeter (PATROL)
UPDATE micro_missions SET
    category = 'PATROL',
    narrative_choices = '[
        {"id": "A", "text": "Maintain vigilant watch from your post", "icon": "eye"},
        {"id": "B", "text": "Investigate suspicious movement in the mists", "icon": "search"},
        {"id": "C", "text": "Signal other guards about unusual activity", "icon": "bell"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "NEUTRAL",
            "text": "Your watch passes uneventfully. The mists swirl but reveal no threats. A quiet patrol is still a successful patrol.",
            "pyre_modifier": 1.0,
            "xp_modifier": 1.0
        },
        "B": {
            "type": "PERFECT",
            "text": "You creep into the mists and discover a tear forming in the veil! Quick action allows you to seal it before any void creatures emerge. The realm is safer for your bravery.",
            "pyre_modifier": 1.5,
            "xp_modifier": 1.4
        },
        "C": {
            "type": "GOOD",
            "text": "Your signal brings reinforcements. Together you identify and neutralize a potential threat. The guard captain commends your teamwork.",
            "pyre_modifier": 1.2,
            "xp_modifier": 1.2
        }
    }'::jsonb,
    lore_connection = 'The Portal''s edge requires constant vigilance. Things from the void are always seeking entry.',
    achievements = '{
        "vigilant_guard": {
            "name": "Vigilant Guard",
            "description": "Completed a patrol without incident",
            "icon": "shield"
        }
    }'::jsonb
WHERE id = 'MM-E003';

-- MM-E004: Rune Meditation (LORE)
UPDATE micro_missions SET
    category = 'LORE',
    narrative_choices = '[
        {"id": "A", "text": "Empty your mind completely", "icon": "mind"},
        {"id": "B", "text": "Focus on a specific question", "icon": "question"},
        {"id": "C", "text": "Let the rune guide your thoughts", "icon": "rune"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "GOOD",
            "text": "In the emptiness, power flows freely. The rune''s energy fills you without resistance, granting a measure of its ancient strength.",
            "pyre_modifier": 1.2,
            "xp_modifier": 1.1
        },
        "B": {
            "type": "NEUTRAL",
            "text": "The rune considers your question but offers no clear answer. Some mysteries are not meant to be solved through force of will.",
            "pyre_modifier": 0.9,
            "xp_modifier": 1.0
        },
        "C": {
            "type": "PERFECT",
            "text": "Surrendering to the rune''s guidance, you experience visions of its creation. The First Runesmiths speak through time, and you understand a fragment of their art.",
            "pyre_modifier": 1.4,
            "xp_modifier": 1.5
        }
    }'::jsonb,
    lore_connection = 'The rune stones were carved by the First Runesmiths, encoding the fundamental laws of Emberholm.',
    achievements = '{
        "rune_touched": {
            "name": "Rune Touched",
            "description": "Meditated before an ancient rune stone",
            "icon": "rune"
        }
    }'::jsonb
WHERE id = 'MM-E004';

-- MM-E005: Forge Apprentice (GUILD)
UPDATE micro_missions SET
    category = 'GUILD',
    narrative_choices = '[
        {"id": "A", "text": "Pump the bellows to heat the forge", "icon": "wind"},
        {"id": "B", "text": "Sort and organize the metal ingots", "icon": "boxes"},
        {"id": "C", "text": "Watch and learn the master''s technique", "icon": "eye"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "GOOD",
            "text": "Your steady rhythm brings the forge to perfect temperature. The blacksmith nods approvingly - you have the makings of a smith.",
            "pyre_modifier": 1.2,
            "xp_modifier": 1.2
        },
        "B": {
            "type": "NEUTRAL",
            "text": "The workshop is now orderly and efficient. Simple work, but the foundation of any craft is organization.",
            "pyre_modifier": 1.0,
            "xp_modifier": 1.0
        },
        "C": {
            "type": "PERFECT",
            "text": "The master, noticing your keen attention, demonstrates a secret technique passed down through generations. Few apprentices earn such trust.",
            "pyre_modifier": 1.3,
            "xp_modifier": 1.5
        }
    }'::jsonb,
    lore_connection = 'The Eternal Forge never cools. It is said to contain a spark from the First Flame itself.',
    achievements = '{
        "forge_initiate": {
            "name": "Forge Initiate",
            "description": "Assisted at the Eternal Forge",
            "icon": "anvil"
        }
    }'::jsonb
WHERE id = 'MM-E005';

-- MM-M001: Void Echoes Investigation (EXPLORATION)
UPDATE micro_missions SET
    category = 'EXPLORATION',
    narrative_choices = '[
        {"id": "A", "text": "Record the sounds for analysis", "icon": "scroll"},
        {"id": "B", "text": "Attempt to trace them to their source", "icon": "compass"},
        {"id": "C", "text": "Use protective wards before proceeding", "icon": "shield"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "GOOD",
            "text": "Your recordings capture patterns previously unknown. The Lore Keepers will pay handsomely for this data.",
            "pyre_modifier": 1.2,
            "xp_modifier": 1.3
        },
        "B": {
            "type": "PERFECT",
            "text": "The echoes lead you to a hidden void pocket containing residual energy from the realm''s creation! A discovery of immense value.",
            "pyre_modifier": 1.5,
            "xp_modifier": 1.4
        },
        "C": {
            "type": "NEUTRAL",
            "text": "Your caution is wise but limits discovery. The wards hold and you return safely with modest findings.",
            "pyre_modifier": 1.0,
            "xp_modifier": 1.0
        }
    }'::jsonb,
    lore_connection = 'The void speaks in frequencies beyond mortal hearing. Those who learn to listen discover secrets of creation itself.',
    achievements = '{
        "void_listener": {
            "name": "Void Listener",
            "description": "Investigated the echoes of the void",
            "icon": "void"
        }
    }'::jsonb
WHERE id = 'MM-M001';

-- MM-M002: Guild Messenger (GUILD)
UPDATE micro_missions SET
    category = 'GUILD',
    name = 'Guild Rivalry',
    description = 'Tensions between the Shadow Guild and Forge Legion threaten to boil over. Diplomacy is required.',
    duration_seconds = 150,
    narrative_intro = 'The tavern falls silent as you enter. On one side, scarred smiths of the Forge Legion nurse their ales with murderous glares. On the other, hooded figures from the Shadow Guild return the sentiment with cold calculation. In the center, a table lies overturned, cards scattered - and blood on the floor.',
    narrative_choices = '[
        {"id": "A", "text": "Examine the cards for evidence of cheating", "icon": "search"},
        {"id": "B", "text": "Appeal to guild honor and shared history", "icon": "scroll"},
        {"id": "C", "text": "Propose a different contest to settle the dispute", "icon": "balance"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "GOOD",
            "text": "Your careful examination reveals the truth: a THIRD party planted marked cards to frame the Shadow Guild! Both sides unite to track down the real culprit.",
            "pyre_modifier": 1.3,
            "xp_modifier": 1.2
        },
        "B": {
            "type": "PERFECT",
            "text": "\"Do you not remember the Battle of Cinderpeak?\" you ask. The room grows quiet as you recount the history of cooperation. Grudgingly, both sides shake hands. The guild masters send generous rewards.",
            "pyre_modifier": 1.45,
            "xp_modifier": 1.35
        },
        "C": {
            "type": "NEUTRAL",
            "text": "You propose an arm-wrestling contest instead. It''s absurd enough to break the tension. The crisis is averted, though neither side is fully satisfied.",
            "pyre_modifier": 0.9,
            "xp_modifier": 1.0
        }
    }'::jsonb,
    lore_connection = 'The six guilds of Emberholm have a long and complicated history. Though they work together, old rivalries never truly die.',
    achievements = '{
        "peacekeeper": {
            "name": "Peacekeeper",
            "description": "Resolve a dispute between guilds",
            "icon": "dove"
        },
        "guild_historian": {
            "name": "Guild Historian",
            "description": "Use knowledge of history to resolve conflict",
            "icon": "book",
            "condition": "choice_B"
        }
    }'::jsonb
WHERE id = 'MM-M002';

-- MM-M003: Ash Beast Tracking (PATROL)
UPDATE micro_missions SET
    category = 'PATROL',
    narrative_choices = '[
        {"id": "A", "text": "Follow the tracks stealthily", "icon": "footprints"},
        {"id": "B", "text": "Set up a surveillance position", "icon": "eye"},
        {"id": "C", "text": "Mark the territory for other patrols", "icon": "flag"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "PERFECT",
            "text": "Your stealth is rewarded! You discover an entire ash beast den, mapping it for future reference. This intelligence is invaluable for the realm''s defense.",
            "pyre_modifier": 1.5,
            "xp_modifier": 1.4
        },
        "B": {
            "type": "GOOD",
            "text": "From your vantage point, you observe the beasts'' patrol patterns and feeding times. Solid reconnaissance work.",
            "pyre_modifier": 1.2,
            "xp_modifier": 1.3
        },
        "C": {
            "type": "NEUTRAL",
            "text": "Your markers will guide future patrols safely through the area. Practical work, if not glamorous.",
            "pyre_modifier": 1.0,
            "xp_modifier": 1.0
        }
    }'::jsonb,
    lore_connection = 'Ash beasts are creatures corrupted by void energy. They were once normal animals before the First Cataclysm.',
    achievements = '{
        "beast_tracker": {
            "name": "Beast Tracker",
            "description": "Track ash beasts to their territory",
            "icon": "paw"
        }
    }'::jsonb
WHERE id = 'MM-M003';

-- MM-M004: Crystal Harvesting (EXPLORATION)
UPDATE micro_missions SET
    category = 'EXPLORATION',
    narrative_choices = '[
        {"id": "A", "text": "Harvest the most accessible crystals", "icon": "gem"},
        {"id": "B", "text": "Seek the deeper, more resonant formations", "icon": "compass"},
        {"id": "C", "text": "Attune to the cave''s song before harvesting", "icon": "music"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "NEUTRAL",
            "text": "You gather a standard haul of resonance crystals. The guild will be satisfied with your work.",
            "pyre_modifier": 1.0,
            "xp_modifier": 1.0
        },
        "B": {
            "type": "GOOD",
            "text": "The deeper formations yield crystals of exceptional purity. Their resonance is stronger than common varieties.",
            "pyre_modifier": 1.3,
            "xp_modifier": 1.2
        },
        "C": {
            "type": "PERFECT",
            "text": "By harmonizing with the cave''s frequency, you locate a mother crystal - the source of all others. You harvest a fragment of immense power.",
            "pyre_modifier": 1.5,
            "xp_modifier": 1.5
        }
    }'::jsonb,
    lore_connection = 'The Singing Caves formed when the First Flame''s energy crystallized underground, creating natural resonators.',
    achievements = '{
        "crystal_singer": {
            "name": "Crystal Singer",
            "description": "Attune to the Singing Caves",
            "icon": "crystal"
        }
    }'::jsonb
WHERE id = 'MM-M004';

-- MM-M005: Spirit Communion (LORE)
UPDATE micro_missions SET
    category = 'LORE',
    narrative_choices = '[
        {"id": "A", "text": "Ask the spirits for tactical wisdom", "icon": "sword"},
        {"id": "B", "text": "Request knowledge of ancient history", "icon": "book"},
        {"id": "C", "text": "Offer to carry a message to the living", "icon": "scroll"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "GOOD",
            "text": "The warrior spirits share battle techniques lost to time. You feel stronger, more capable.",
            "pyre_modifier": 1.2,
            "xp_modifier": 1.3
        },
        "B": {
            "type": "GOOD",
            "text": "The spirits reveal fragments of history erased from mortal records. Knowledge is power, and you now possess both.",
            "pyre_modifier": 1.3,
            "xp_modifier": 1.4
        },
        "C": {
            "type": "PERFECT",
            "text": "Your selfless offer deeply moves the spirits. They bestow their blessing upon you and entrust you with messages for their descendants. Such honor is rare.",
            "pyre_modifier": 1.5,
            "xp_modifier": 1.5
        }
    }'::jsonb,
    lore_connection = 'Fallen emissaries do not truly die - their spirits linger in Emberholm, watching over those who came after.',
    achievements = '{
        "spirit_touched": {
            "name": "Spirit Touched",
            "description": "Commune with the spirits of fallen emissaries",
            "icon": "ghost"
        }
    }'::jsonb
WHERE id = 'MM-M005';

-- MM-H001: Void Rift Sealing (LEGENDARY)
UPDATE micro_missions SET
    category = 'LEGENDARY',
    narrative_choices = '[
        {"id": "A", "text": "Use raw power to force the rift closed", "icon": "fist"},
        {"id": "B", "text": "Employ ancient sealing runes", "icon": "rune"},
        {"id": "C", "text": "Redirect the void energy back through the rift", "icon": "void"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "NEUTRAL",
            "text": "Your strength succeeds, but barely. The rift is sealed but the strain leaves you exhausted. Effective, but costly.",
            "pyre_modifier": 0.9,
            "xp_modifier": 1.0
        },
        "B": {
            "type": "GOOD",
            "text": "The ancient runes flare with power as you invoke them. The rift seals cleanly, leaving no residual instability.",
            "pyre_modifier": 1.3,
            "xp_modifier": 1.3
        },
        "C": {
            "type": "PERFECT",
            "text": "A brilliant technique! By redirecting the energy, you not only seal the rift but harness some of its power. The void itself becomes your reward.",
            "pyre_modifier": 1.6,
            "xp_modifier": 1.5
        }
    }'::jsonb,
    lore_connection = 'Void rifts are tears in reality itself. Each one sealed protects Emberholm from the entities that lurk beyond.',
    achievements = '{
        "rift_sealer": {
            "name": "Rift Sealer",
            "description": "Seal a void rift",
            "icon": "seal"
        },
        "void_master": {
            "name": "Void Master",
            "description": "Harness void energy to seal a rift",
            "icon": "void",
            "condition": "choice_C"
        }
    }'::jsonb
WHERE id = 'MM-H001';

-- MM-H002: Ancient Guardian Trial (LEGENDARY)
UPDATE micro_missions SET
    category = 'LEGENDARY',
    narrative_choices = '[
        {"id": "A", "text": "Face the trial of strength", "icon": "sword"},
        {"id": "B", "text": "Choose the trial of wisdom", "icon": "book"},
        {"id": "C", "text": "Accept the trial of heart", "icon": "heart"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "GOOD",
            "text": "You overcome the guardian''s physical challenges through sheer determination. Battered but victorious, you prove your martial worth.",
            "pyre_modifier": 1.3,
            "xp_modifier": 1.2
        },
        "B": {
            "type": "GOOD",
            "text": "The guardian poses riddles from the dawn of time. Your answers demonstrate deep understanding of Emberholm''s nature.",
            "pyre_modifier": 1.2,
            "xp_modifier": 1.4
        },
        "C": {
            "type": "PERFECT",
            "text": "The trial of heart reveals your truest self. The guardian sees your dedication to Emberholm and deems you worthy of its greatest blessing.",
            "pyre_modifier": 1.5,
            "xp_modifier": 1.5
        }
    }'::jsonb,
    lore_connection = 'The Ancient Guardians were created by the First Flame to test those who would defend Emberholm.',
    achievements = '{
        "trial_complete": {
            "name": "Trial Complete",
            "description": "Pass the Ancient Guardian''s trial",
            "icon": "trophy"
        },
        "heart_proven": {
            "name": "Heart Proven",
            "description": "Pass the trial of heart",
            "icon": "heart",
            "condition": "choice_C"
        }
    }'::jsonb
WHERE id = 'MM-H002';

-- MM-H003: Legendary Artifact Recovery (LEGENDARY)
UPDATE micro_missions SET
    category = 'LEGENDARY',
    narrative_choices = '[
        {"id": "A", "text": "Approach through the main path, ready for combat", "icon": "sword"},
        {"id": "B", "text": "Find an alternate route to avoid detection", "icon": "stealth"},
        {"id": "C", "text": "Study the area first to understand its dangers", "icon": "eye"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "NEUTRAL",
            "text": "You fight your way through, sustaining injuries but reaching the artifact. The prize is yours, though at a cost.",
            "pyre_modifier": 1.0,
            "xp_modifier": 1.1
        },
        "B": {
            "type": "GOOD",
            "text": "Your alternative path avoids most dangers. You reach the artifact relatively unscathed and retrieve it successfully.",
            "pyre_modifier": 1.3,
            "xp_modifier": 1.3
        },
        "C": {
            "type": "PERFECT",
            "text": "Your patience reveals the territory''s true nature - it was a test! The guardians recognize your wisdom and willingly surrender the artifact, plus additional rewards.",
            "pyre_modifier": 1.6,
            "xp_modifier": 1.6
        }
    }'::jsonb,
    lore_connection = 'Legendary artifacts are remnants of the First Age, when Emberholm''s power was uncontained and shaped the world.',
    achievements = '{
        "artifact_hunter": {
            "name": "Artifact Hunter",
            "description": "Recover a legendary artifact",
            "icon": "artifact"
        },
        "true_seeker": {
            "name": "True Seeker",
            "description": "Understand the true nature of an artifact''s test",
            "icon": "wisdom",
            "condition": "choice_C"
        }
    }'::jsonb
WHERE id = 'MM-H003';

-- MM-H004: Elite Ash Beast Hunt (PATROL)
UPDATE micro_missions SET
    category = 'PATROL',
    narrative_choices = '[
        {"id": "A", "text": "Engage the beast in direct combat", "icon": "sword"},
        {"id": "B", "text": "Lure it into a prepared trap", "icon": "trap"},
        {"id": "C", "text": "Use the terrain to gain advantage", "icon": "mountain"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "NEUTRAL",
            "text": "A fierce battle ensues. You defeat the beast but the fight leaves you drained. The realm is safer, at personal cost.",
            "pyre_modifier": 1.0,
            "xp_modifier": 1.1
        },
        "B": {
            "type": "GOOD",
            "text": "Your trap springs perfectly! The beast is neutralized efficiently. Your tactical mind impresses the hunting guild.",
            "pyre_modifier": 1.3,
            "xp_modifier": 1.3
        },
        "C": {
            "type": "PERFECT",
            "text": "Using the terrain masterfully, you outmaneuver the beast and strike from an impossible angle. A clean victory worthy of legend.",
            "pyre_modifier": 1.5,
            "xp_modifier": 1.5
        }
    }'::jsonb,
    lore_connection = 'Elite ash beasts are alphas of their kind, corrupted by decades of void exposure. Their elimination is vital.',
    achievements = '{
        "beast_slayer": {
            "name": "Beast Slayer",
            "description": "Eliminate an elite ash beast",
            "icon": "skull"
        },
        "master_hunter": {
            "name": "Master Hunter",
            "description": "Defeat a beast using superior tactics",
            "icon": "crown",
            "condition": "choice_C"
        }
    }'::jsonb
WHERE id = 'MM-H004';

-- MM-H005: Forge of Legends (GUILD)
UPDATE micro_missions SET
    category = 'GUILD',
    narrative_choices = '[
        {"id": "A", "text": "Contribute your own ember essence to the forging", "icon": "flame"},
        {"id": "B", "text": "Maintain perfect rhythm with the master smith", "icon": "anvil"},
        {"id": "C", "text": "Channel ancestral knowledge of metallurgy", "icon": "book"}
    ]'::jsonb,
    narrative_outcomes = '{
        "A": {
            "type": "GOOD",
            "text": "Your essence merges with the weapon. It will forever carry a piece of you. The smith is impressed by your sacrifice.",
            "pyre_modifier": 1.3,
            "xp_modifier": 1.2
        },
        "B": {
            "type": "GOOD",
            "text": "Strike after strike, you match the master''s tempo. The weapon forms flawlessly. You have earned the smith''s respect.",
            "pyre_modifier": 1.2,
            "xp_modifier": 1.3
        },
        "C": {
            "type": "PERFECT",
            "text": "Knowledge flows through you from smiths long dead. You suggest an ancient technique - the weapon achieves impossible perfection. You have helped create a true legend.",
            "pyre_modifier": 1.6,
            "xp_modifier": 1.5
        }
    }'::jsonb,
    lore_connection = 'Legendary weapons forged here have turned the tide of countless battles against the void.',
    achievements = '{
        "legend_forger": {
            "name": "Legend Forger",
            "description": "Help forge a legendary weapon",
            "icon": "sword"
        },
        "ancestral_smith": {
            "name": "Ancestral Smith",
            "description": "Channel ancient smithing knowledge",
            "icon": "ancestor",
            "condition": "choice_C"
        }
    }'::jsonb
WHERE id = 'MM-H005';

COMMIT;

-- =========================================================================
-- VERIFICACIÓN
-- =========================================================================
SELECT 'Migration 003 completed successfully!' as status;

SELECT id, name, category,
       CASE WHEN narrative_choices IS NOT NULL AND narrative_choices::text != '[]' THEN 'YES' ELSE 'NO' END as has_choices,
       CASE WHEN narrative_outcomes IS NOT NULL AND narrative_outcomes::text != '{}' THEN 'YES' ELSE 'NO' END as has_outcomes
FROM micro_missions
ORDER BY category, id;
