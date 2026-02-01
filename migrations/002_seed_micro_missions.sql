-- =========================================================================
-- EMBERHOLM PORTAL - MIGRATION 002: Seed Micro Missions
-- =========================================================================
-- Micro-missions reward: XP, EMBER, AURA only (NO PYRE)
-- Durations: EASY=2min, MEDIUM=4min, HARD=5min
-- =========================================================================

BEGIN;

-- =========================================================================
-- MICRO-MISSIONS: EASY (120 segundos = 2 minutos)
-- Rewards: XP 5-10, EMBER 10-20, Aura 2-5%
-- =========================================================================

INSERT INTO micro_missions (id, name, description, difficulty, duration_seconds, energy_cost, pyre_reward_min, pyre_reward_max, xp_reward_min, xp_reward_max, ember_reward_min, ember_reward_max, aura_chance, narrative_intro, cooldown_minutes, is_active)
VALUES
('MM-E001', 'The Whispering Flame', 'A faint voice calls from the eternal brazier. Listen to its wisdom.', 'EASY', 120, 5, 0, 0, 5, 10, 10, 20, 5.00, 'The flames flicker as you approach the ancient brazier. A voice, barely audible, speaks of forgotten truths...', 0, TRUE),
('MM-E002', 'Ember Gathering', 'Collect scattered embers in the Ashen Fields before they fade.', 'EASY', 120, 5, 0, 0, 3, 8, 8, 15, 3.00, 'Glowing embers dot the ashen landscape. Quick - gather them before they return to the void!', 0, TRUE),
('MM-E003', 'Patrol the Perimeter', 'A routine patrol around the portal''s edge. Stay vigilant.', 'EASY', 120, 5, 0, 0, 5, 10, 10, 20, 5.00, 'You take your position at the portal''s edge. The mists swirl with unknown dangers...', 0, TRUE),
('MM-E004', 'Rune Meditation', 'Meditate before the ancient rune stone to absorb its power.', 'EASY', 120, 3, 0, 0, 2, 5, 5, 12, 2.00, 'The rune stone hums with ancient energy. Close your eyes and let its power flow through you...', 0, TRUE),
('MM-E005', 'Forge Apprentice', 'Assist the blacksmith with simple tasks at the Eternal Forge.', 'EASY', 120, 5, 0, 0, 3, 8, 8, 15, 3.00, 'The heat of the forge washes over you. The blacksmith nods - there is work to be done.', 0, TRUE)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    difficulty = EXCLUDED.difficulty,
    duration_seconds = EXCLUDED.duration_seconds,
    energy_cost = EXCLUDED.energy_cost,
    pyre_reward_min = 0,
    pyre_reward_max = 0,
    xp_reward_min = EXCLUDED.xp_reward_min,
    xp_reward_max = EXCLUDED.xp_reward_max,
    ember_reward_min = EXCLUDED.ember_reward_min,
    ember_reward_max = EXCLUDED.ember_reward_max,
    aura_chance = EXCLUDED.aura_chance,
    narrative_intro = EXCLUDED.narrative_intro,
    is_active = EXCLUDED.is_active;

-- =========================================================================
-- MICRO-MISSIONS: MEDIUM (180 segundos = 3 minutos)
-- Rewards: XP 8-20, EMBER 20-40, Aura 8-12%
-- =========================================================================

INSERT INTO micro_missions (id, name, description, difficulty, duration_seconds, energy_cost, pyre_reward_min, pyre_reward_max, xp_reward_min, xp_reward_max, ember_reward_min, ember_reward_max, aura_chance, narrative_intro, cooldown_minutes, is_active)
VALUES
('MM-M001', 'Void Echoes Investigation', 'Strange sounds emanate from the void. Investigate their source.', 'MEDIUM', 180, 10, 0, 0, 10, 20, 25, 40, 10.00, 'The void whispers secrets that mortal ears were not meant to hear. Do you dare listen?', 5, TRUE),
('MM-M002', 'Guild Messenger', 'Deliver an urgent message between guild outposts.', 'MEDIUM', 180, 8, 0, 0, 8, 15, 20, 35, 8.00, 'A sealed scroll bears the mark of your guild. Time is of the essence - deliver it swiftly!', 3, TRUE),
('MM-M003', 'Ash Beast Tracking', 'Track the movements of ash beasts near the settlement.', 'MEDIUM', 180, 10, 0, 0, 10, 20, 25, 40, 10.00, 'Strange tracks mark the ashen ground. The beasts are near - proceed with caution.', 5, TRUE),
('MM-M004', 'Crystal Harvesting', 'Harvest resonance crystals from the Singing Caves.', 'MEDIUM', 180, 8, 0, 0, 8, 15, 20, 35, 8.00, 'The caves sing with crystal harmonies. Extract the resonant gems carefully...', 3, TRUE),
('MM-M005', 'Spirit Communion', 'Commune with the spirits of fallen emissaries.', 'MEDIUM', 180, 10, 0, 0, 10, 20, 25, 40, 12.00, 'The veil between worlds grows thin. The spirits of the fallen seek to share their wisdom...', 5, TRUE)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    difficulty = EXCLUDED.difficulty,
    duration_seconds = EXCLUDED.duration_seconds,
    energy_cost = EXCLUDED.energy_cost,
    pyre_reward_min = 0,
    pyre_reward_max = 0,
    xp_reward_min = EXCLUDED.xp_reward_min,
    xp_reward_max = EXCLUDED.xp_reward_max,
    ember_reward_min = EXCLUDED.ember_reward_min,
    ember_reward_max = EXCLUDED.ember_reward_max,
    aura_chance = EXCLUDED.aura_chance,
    narrative_intro = EXCLUDED.narrative_intro,
    cooldown_minutes = EXCLUDED.cooldown_minutes,
    is_active = EXCLUDED.is_active;

-- =========================================================================
-- MICRO-MISSIONS: HARD (300 segundos = 5 minutos)
-- Rewards: XP 20-50, EMBER 50-120, Aura 20-30%
-- =========================================================================

INSERT INTO micro_missions (id, name, description, difficulty, duration_seconds, energy_cost, pyre_reward_min, pyre_reward_max, xp_reward_min, xp_reward_max, ember_reward_min, ember_reward_max, aura_chance, narrative_intro, cooldown_minutes, is_active)
VALUES
('MM-H001', 'Void Rift Sealing', 'A dangerous rift has opened. Seal it before creatures emerge.', 'HARD', 300, 15, 0, 0, 20, 35, 50, 80, 20.00, 'The fabric of reality tears before you. Dark energies pour through - seal the rift or face the consequences!', 10, TRUE),
('MM-H002', 'Ancient Guardian Trial', 'Face the trial of the Ancient Guardian to prove your worth.', 'HARD', 300, 20, 0, 0, 25, 40, 60, 100, 25.00, 'The stone guardian awakens. Only the worthy may pass this ancient trial.', 15, TRUE),
('MM-H003', 'Legendary Artifact Recovery', 'A legendary artifact has been detected. Retrieve it from dangerous territory.', 'HARD', 300, 25, 0, 0, 30, 50, 80, 120, 30.00, 'The artifact pulses with power in the distance. Many have sought it - none have returned.', 20, TRUE),
('MM-H004', 'Elite Ash Beast Hunt', 'An elite ash beast threatens the realm. Hunt it down.', 'HARD', 300, 20, 0, 0, 25, 40, 60, 100, 25.00, 'Massive tracks scar the landscape. The alpha beast must be eliminated before it breeds.', 15, TRUE),
('MM-H005', 'Forge of Legends', 'Assist in forging a legendary weapon at the Eternal Forge.', 'HARD', 300, 15, 0, 0, 20, 35, 50, 80, 20.00, 'The master smith summons you. Today, legend shall be forged in flame and steel.', 10, TRUE)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    difficulty = EXCLUDED.difficulty,
    duration_seconds = EXCLUDED.duration_seconds,
    energy_cost = EXCLUDED.energy_cost,
    pyre_reward_min = 0,
    pyre_reward_max = 0,
    xp_reward_min = EXCLUDED.xp_reward_min,
    xp_reward_max = EXCLUDED.xp_reward_max,
    ember_reward_min = EXCLUDED.ember_reward_min,
    ember_reward_max = EXCLUDED.ember_reward_max,
    aura_chance = EXCLUDED.aura_chance,
    narrative_intro = EXCLUDED.narrative_intro,
    cooldown_minutes = EXCLUDED.cooldown_minutes,
    is_active = EXCLUDED.is_active;

COMMIT;

-- =========================================================================
-- VERIFICATION
-- =========================================================================
SELECT 'Micro-missions seeded successfully!' as status;
SELECT id, name, difficulty, duration_seconds, xp_reward_min, xp_reward_max, ember_reward_min, ember_reward_max, aura_chance
FROM micro_missions
ORDER BY difficulty, id;
