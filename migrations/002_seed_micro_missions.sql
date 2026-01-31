-- =========================================================================
-- EMBERHOLM PORTAL - MIGRATION 002: Seed Micro Missions
-- =========================================================================
-- Este script inserta las micro-misiones básicas para la mini app
-- SEGURO: Usa ON CONFLICT DO UPDATE para no duplicar datos
-- =========================================================================
-- Ejecutar DESPUÉS de 001_mini_app_tables.sql
-- =========================================================================

BEGIN;

-- =========================================================================
-- MICRO-MISSIONS: EASY (30-60 segundos, 10-25 $EMBER)
-- =========================================================================

INSERT INTO micro_missions (id, name, description, difficulty, duration_seconds, energy_cost, pyre_reward_min, pyre_reward_max, xp_reward_min, xp_reward_max, ember_reward_min, ember_reward_max, aura_chance, narrative_intro, cooldown_minutes, is_active)
VALUES
('MM-E001', 'The Whispering Flame', 'A faint voice calls from the eternal brazier. Listen to its wisdom.', 'EASY', 60, 5, 10, 15, 5, 10, 10, 20, 5.00, 'The flames flicker as you approach the ancient brazier. A voice, barely audible, speaks of forgotten truths...', 0, TRUE),
('MM-E002', 'Ember Gathering', 'Collect scattered embers in the Ashen Fields before they fade.', 'EASY', 45, 5, 8, 12, 3, 8, 8, 15, 3.00, 'Glowing embers dot the ashen landscape. Quick - gather them before they return to the void!', 0, TRUE),
('MM-E003', 'Patrol the Perimeter', 'A routine patrol around the portal''s edge. Stay vigilant.', 'EASY', 60, 5, 10, 15, 5, 10, 10, 20, 5.00, 'You take your position at the portal''s edge. The mists swirl with unknown dangers...', 0, TRUE),
('MM-E004', 'Rune Meditation', 'Meditate before the ancient rune stone to absorb its power.', 'EASY', 30, 3, 5, 10, 2, 5, 5, 12, 2.00, 'The rune stone hums with ancient energy. Close your eyes and let its power flow through you...', 0, TRUE),
('MM-E005', 'Forge Apprentice', 'Assist the blacksmith with simple tasks at the Eternal Forge.', 'EASY', 45, 5, 8, 12, 3, 8, 8, 15, 3.00, 'The heat of the forge washes over you. The blacksmith nods - there is work to be done.', 0, TRUE)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    difficulty = EXCLUDED.difficulty,
    duration_seconds = EXCLUDED.duration_seconds,
    energy_cost = EXCLUDED.energy_cost,
    pyre_reward_min = EXCLUDED.pyre_reward_min,
    pyre_reward_max = EXCLUDED.pyre_reward_max,
    xp_reward_min = EXCLUDED.xp_reward_min,
    xp_reward_max = EXCLUDED.xp_reward_max,
    ember_reward_min = EXCLUDED.ember_reward_min,
    ember_reward_max = EXCLUDED.ember_reward_max,
    aura_chance = EXCLUDED.aura_chance,
    narrative_intro = EXCLUDED.narrative_intro,
    is_active = EXCLUDED.is_active;

-- =========================================================================
-- MICRO-MISSIONS: MEDIUM (60-120 segundos, 20-50 $EMBER)
-- =========================================================================

INSERT INTO micro_missions (id, name, description, difficulty, duration_seconds, energy_cost, pyre_reward_min, pyre_reward_max, xp_reward_min, xp_reward_max, ember_reward_min, ember_reward_max, aura_chance, narrative_intro, cooldown_minutes, is_active)
VALUES
('MM-M001', 'Void Echoes Investigation', 'Strange sounds emanate from the void. Investigate their source.', 'MEDIUM', 120, 10, 20, 30, 10, 20, 25, 40, 10.00, 'The void whispers secrets that mortal ears were not meant to hear. Do you dare listen?', 5, TRUE),
('MM-M002', 'Guild Messenger', 'Deliver an urgent message between guild outposts.', 'MEDIUM', 90, 8, 15, 25, 8, 15, 20, 35, 8.00, 'A sealed scroll bears the mark of your guild. Time is of the essence - deliver it swiftly!', 3, TRUE),
('MM-M003', 'Ash Beast Tracking', 'Track the movements of ash beasts near the settlement.', 'MEDIUM', 120, 10, 20, 30, 10, 20, 25, 40, 10.00, 'Strange tracks mark the ashen ground. The beasts are near - proceed with caution.', 5, TRUE),
('MM-M004', 'Crystal Harvesting', 'Harvest resonance crystals from the Singing Caves.', 'MEDIUM', 90, 8, 15, 25, 8, 15, 20, 35, 8.00, 'The caves sing with crystal harmonies. Extract the resonant gems carefully...', 3, TRUE),
('MM-M005', 'Spirit Communion', 'Commune with the spirits of fallen emissaries.', 'MEDIUM', 120, 10, 20, 30, 10, 20, 25, 40, 12.00, 'The veil between worlds grows thin. The spirits of the fallen seek to share their wisdom...', 5, TRUE)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    difficulty = EXCLUDED.difficulty,
    duration_seconds = EXCLUDED.duration_seconds,
    energy_cost = EXCLUDED.energy_cost,
    pyre_reward_min = EXCLUDED.pyre_reward_min,
    pyre_reward_max = EXCLUDED.pyre_reward_max,
    xp_reward_min = EXCLUDED.xp_reward_min,
    xp_reward_max = EXCLUDED.xp_reward_max,
    ember_reward_min = EXCLUDED.ember_reward_min,
    ember_reward_max = EXCLUDED.ember_reward_max,
    aura_chance = EXCLUDED.aura_chance,
    narrative_intro = EXCLUDED.narrative_intro,
    cooldown_minutes = EXCLUDED.cooldown_minutes,
    is_active = EXCLUDED.is_active;

-- =========================================================================
-- MICRO-MISSIONS: HARD (180-300 segundos, 40-100 $EMBER)
-- =========================================================================

INSERT INTO micro_missions (id, name, description, difficulty, duration_seconds, energy_cost, pyre_reward_min, pyre_reward_max, xp_reward_min, xp_reward_max, ember_reward_min, ember_reward_max, aura_chance, narrative_intro, cooldown_minutes, is_active)
VALUES
('MM-H001', 'Void Rift Sealing', 'A dangerous rift has opened. Seal it before creatures emerge.', 'HARD', 180, 15, 35, 50, 20, 35, 50, 80, 20.00, 'The fabric of reality tears before you. Dark energies pour through - seal the rift or face the consequences!', 10, TRUE),
('MM-H002', 'Ancient Guardian Trial', 'Face the trial of the Ancient Guardian to prove your worth.', 'HARD', 240, 20, 40, 60, 25, 40, 60, 100, 25.00, 'The stone guardian awakens. Only the worthy may pass this ancient trial.', 15, TRUE),
('MM-H003', 'Legendary Artifact Recovery', 'A legendary artifact has been detected. Retrieve it from dangerous territory.', 'HARD', 300, 25, 50, 75, 30, 50, 80, 120, 30.00, 'The artifact pulses with power in the distance. Many have sought it - none have returned.', 20, TRUE),
('MM-H004', 'Elite Ash Beast Hunt', 'An elite ash beast threatens the realm. Hunt it down.', 'HARD', 240, 20, 40, 60, 25, 40, 60, 100, 25.00, 'Massive tracks scar the landscape. The alpha beast must be eliminated before it breeds.', 15, TRUE),
('MM-H005', 'Forge of Legends', 'Assist in forging a legendary weapon at the Eternal Forge.', 'HARD', 180, 15, 35, 50, 20, 35, 50, 80, 20.00, 'The master smith summons you. Today, legend shall be forged in flame and steel.', 10, TRUE)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    difficulty = EXCLUDED.difficulty,
    duration_seconds = EXCLUDED.duration_seconds,
    energy_cost = EXCLUDED.energy_cost,
    pyre_reward_min = EXCLUDED.pyre_reward_min,
    pyre_reward_max = EXCLUDED.pyre_reward_max,
    xp_reward_min = EXCLUDED.xp_reward_min,
    xp_reward_max = EXCLUDED.xp_reward_max,
    ember_reward_min = EXCLUDED.ember_reward_min,
    ember_reward_max = EXCLUDED.ember_reward_max,
    aura_chance = EXCLUDED.aura_chance,
    narrative_intro = EXCLUDED.narrative_intro,
    cooldown_minutes = EXCLUDED.cooldown_minutes,
    is_active = EXCLUDED.is_active;

-- =========================================================================
-- EVENTO: The First Spark
-- =========================================================================

INSERT INTO events (name, slug, description, start_condition, end_condition, item_drop_multiplier, rune_drop_multiplier)
VALUES (
    'The First Spark',
    'the-first-spark',
    'The Portal opens. Two prophecies await fulfillment.',
    'mint >= 1',
    'mint >= 35000',
    3.00,
    2.00
)
ON CONFLICT (slug) DO NOTHING;

-- Premios del evento
INSERT INTO event_prizes (event_id, prize_name, prize_type, trophy_token_id, reward_eth)
SELECT
    e.id,
    'The Fortunate',
    'random_drop',
    1,
    1.0000
FROM events e
WHERE e.slug = 'the-first-spark'
  AND NOT EXISTS (
    SELECT 1 FROM event_prizes ep
    WHERE ep.event_id = e.id AND ep.prize_name = 'The Fortunate'
  );

INSERT INTO event_prizes (event_id, prize_name, prize_type, trophy_token_id, reward_eth)
SELECT
    e.id,
    'The Worthy',
    'leaderboard',
    2,
    1.0000
FROM events e
WHERE e.slug = 'the-first-spark'
  AND NOT EXISTS (
    SELECT 1 FROM event_prizes ep
    WHERE ep.event_id = e.id AND ep.prize_name = 'The Worthy'
  );

COMMIT;

-- =========================================================================
-- VERIFICACIÓN
-- =========================================================================
SELECT 'Micro-missions seeded successfully!' as status;
SELECT id, name, difficulty, duration_seconds, ember_reward_min, ember_reward_max
FROM micro_missions
ORDER BY difficulty, id;
