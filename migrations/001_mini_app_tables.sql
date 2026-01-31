-- =========================================================================
-- EMBERHOLM PORTAL - MIGRATION 001: Mini App Tables
-- =========================================================================
-- Este script crea todas las tablas necesarias para la mini app de Farcaster
-- SEGURO: Usa IF NOT EXISTS para no borrar datos existentes
-- =========================================================================
-- Ejecutar: psql $DATABASE_URL -f migrations/001_mini_app_tables.sql
-- =========================================================================

BEGIN;

-- =========================================================================
-- PASO 1: EXTENSIONES
-- =========================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================================================
-- PASO 2: COLUMNAS FALTANTES EN TABLAS EXISTENTES
-- =========================================================================

-- Añadir image_url a nfts si no existe
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS image_url TEXT;

-- Añadir columnas de equipamiento si no existen (por si acaso)
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS weapon_id INTEGER;
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS armor_id INTEGER;
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS helmet_id INTEGER;
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS accessory_id INTEGER;
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS amulet_id INTEGER;
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS rune_ids INTEGER[];
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS land_id INTEGER;

-- =========================================================================
-- PASO 3: TABLAS DE $PYRE (Mini App Economy)
-- =========================================================================

CREATE TABLE IF NOT EXISTS pyre_balances (
    wallet VARCHAR(42) PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    total_earned INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0,
    last_daily_claim TIMESTAMP,
    daily_streak INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pyre_balances_wallet ON pyre_balances(wallet);

CREATE TABLE IF NOT EXISTS pyre_transactions (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(42) NOT NULL,
    amount INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    reference_id VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pyre_transactions_wallet ON pyre_transactions(wallet);
CREATE INDEX IF NOT EXISTS idx_pyre_transactions_type ON pyre_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_pyre_transactions_date ON pyre_transactions(created_at);

-- =========================================================================
-- PASO 4: TABLAS DE MICRO-MISSIONS
-- =========================================================================

CREATE TABLE IF NOT EXISTS micro_missions (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    difficulty VARCHAR(20) NOT NULL,
    duration_seconds INTEGER NOT NULL,
    energy_cost INTEGER DEFAULT 0,
    pyre_reward_min INTEGER NOT NULL,
    pyre_reward_max INTEGER NOT NULL,
    xp_reward_min INTEGER DEFAULT 0,
    xp_reward_max INTEGER DEFAULT 0,
    ember_reward_min INTEGER DEFAULT 0,
    ember_reward_max INTEGER DEFAULT 0,
    aura_chance DECIMAL(5,2) DEFAULT 0,
    narrative_intro TEXT,
    narrative_choices JSONB DEFAULT '[]'::jsonb,
    narrative_outcomes JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    cooldown_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_micro_missions_difficulty ON micro_missions(difficulty);
CREATE INDEX IF NOT EXISTS idx_micro_missions_active ON micro_missions(is_active);

CREATE TABLE IF NOT EXISTS active_micro_missions (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(42) NOT NULL,
    emissary_token_id VARCHAR(10) NOT NULL,
    micro_mission_id VARCHAR(20) NOT NULL REFERENCES micro_missions(id),
    started_at TIMESTAMP DEFAULT NOW(),
    ends_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    current_step INTEGER DEFAULT 0,
    choice_made VARCHAR(50),
    pyre_earned INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    aura_earned INTEGER DEFAULT 0,
    outcome_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_active_micro_wallet ON active_micro_missions(wallet);
CREATE INDEX IF NOT EXISTS idx_active_micro_emissary ON active_micro_missions(emissary_token_id);
CREATE INDEX IF NOT EXISTS idx_active_micro_status ON active_micro_missions(status);
CREATE INDEX IF NOT EXISTS idx_active_micro_ends ON active_micro_missions(ends_at);

-- =========================================================================
-- PASO 5: TABLAS SOCIALES (Mini App Social Features)
-- =========================================================================

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
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_wallet ON user_profiles(wallet);
CREATE INDEX IF NOT EXISTS idx_user_profiles_country ON user_profiles(country_code);
CREATE INDEX IF NOT EXISTS idx_user_profiles_fid ON user_profiles(farcaster_fid);

CREATE TABLE IF NOT EXISTS private_messages (
    id SERIAL PRIMARY KEY,
    from_wallet VARCHAR(42) NOT NULL,
    to_wallet VARCHAR(42) NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_private_messages_from ON private_messages(from_wallet);
CREATE INDEX IF NOT EXISTS idx_private_messages_to ON private_messages(to_wallet);
CREATE INDEX IF NOT EXISTS idx_private_messages_date ON private_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_private_messages_conversation ON private_messages(from_wallet, to_wallet);

CREATE TABLE IF NOT EXISTS global_messages (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(42) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_global_messages_wallet ON global_messages(wallet);
CREATE INDEX IF NOT EXISTS idx_global_messages_date ON global_messages(created_at);

-- =========================================================================
-- PASO 6: TABLAS DE RECOMPENSAS SOCIALES
-- =========================================================================

CREATE TABLE IF NOT EXISTS social_rewards_log (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(42) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    ember_earned DECIMAL(18,2) NOT NULL,
    reference_id VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_social_rewards_wallet ON social_rewards_log(wallet);
CREATE INDEX IF NOT EXISTS idx_social_rewards_type ON social_rewards_log(action_type);
CREATE INDEX IF NOT EXISTS idx_social_rewards_date ON social_rewards_log(created_at);
CREATE INDEX IF NOT EXISTS idx_social_rewards_wallet_type_date ON social_rewards_log(wallet, action_type, created_at);

CREATE TABLE IF NOT EXISTS user_streaks (
    wallet VARCHAR(42) PRIMARY KEY,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_login_date DATE,
    streak_7_claimed_at TIMESTAMP,
    streak_30_claimed_at TIMESTAMP,
    tutorial_completed BOOLEAN DEFAULT FALSE,
    first_mint_rewarded BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_streaks_wallet ON user_streaks(wallet);

-- =========================================================================
-- PASO 7: TABLAS DE EVENTOS
-- =========================================================================

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    description TEXT,
    start_condition VARCHAR(255),
    end_condition VARCHAR(255),
    item_drop_multiplier DECIMAL(5,2) DEFAULT 1.00,
    rune_drop_multiplier DECIMAL(5,2) DEFAULT 1.00,
    created_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_slug ON events(slug);

CREATE TABLE IF NOT EXISTS event_prizes (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    prize_name VARCHAR(100) NOT NULL,
    prize_type VARCHAR(50) NOT NULL,
    trophy_token_id INTEGER NOT NULL,
    reward_eth DECIMAL(10,4) DEFAULT 0,
    winner_wallet VARCHAR(42) NULL,
    trophy_minted BOOLEAN DEFAULT FALSE,
    reward_sent BOOLEAN DEFAULT FALSE,
    found_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_prizes_event ON event_prizes(event_id);
CREATE INDEX IF NOT EXISTS idx_event_prizes_trophy ON event_prizes(trophy_token_id);
CREATE INDEX IF NOT EXISTS idx_event_prizes_winner ON event_prizes(winner_wallet);

CREATE TABLE IF NOT EXISTS event_participation (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    wallet VARCHAR(42) NOT NULL,
    progress INTEGER DEFAULT 0,
    milestones_claimed JSONB DEFAULT '[]'::jsonb,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(event_id, wallet)
);

CREATE INDEX IF NOT EXISTS idx_event_participation_event ON event_participation(event_id);
CREATE INDEX IF NOT EXISTS idx_event_participation_wallet ON event_participation(wallet);

-- =========================================================================
-- PASO 8: VIEWS ÚTILES
-- =========================================================================

CREATE OR REPLACE VIEW country_stats AS
SELECT
    country_code,
    COUNT(*) as user_count,
    COUNT(CASE WHEN last_seen > NOW() - INTERVAL '15 minutes' THEN 1 END) as online_count
FROM user_profiles
WHERE country_code IS NOT NULL
GROUP BY country_code;

CREATE OR REPLACE VIEW user_conversations AS
SELECT DISTINCT
    CASE
        WHEN from_wallet < to_wallet THEN from_wallet
        ELSE to_wallet
    END as user1,
    CASE
        WHEN from_wallet < to_wallet THEN to_wallet
        ELSE from_wallet
    END as user2,
    MAX(created_at) as last_message_at
FROM private_messages
GROUP BY user1, user2;

COMMIT;

-- =========================================================================
-- VERIFICACIÓN
-- =========================================================================
SELECT 'Tables created successfully!' as status;
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'pyre_balances', 'pyre_transactions',
    'micro_missions', 'active_micro_missions',
    'user_profiles', 'private_messages',
    'social_rewards_log', 'user_streaks',
    'events', 'event_prizes', 'event_participation'
)
ORDER BY table_name;
