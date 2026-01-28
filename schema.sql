-- =========================================================================
-- EMBERHOLM PORTAL - POSTGRESQL SCHEMA
-- =========================================================================
-- Base de datos para persistencia de 35,000 NFTs y sistema de misiones
-- Reemplaza archivos JSON por PostgreSQL para garantizar persistencia
-- =========================================================================

-- Extensión para JSONB (búsquedas rápidas en JSON)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -------------------------------------------------------------------------
-- TABLA PRINCIPAL: NFTs (35,000 emissaries)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nfts (
    token_id VARCHAR(10) PRIMARY KEY,                    -- "00001", "00002", etc.
    name VARCHAR(255),                                   -- "Emissary #1"
    guild VARCHAR(100),                                  -- "Circle of Mist", etc.
    race_class VARCHAR(100),                             -- "Human Warrior"
    last_known_owner VARCHAR(42),                        -- Wallet address (lowercase)

    -- Dynamic state como JSONB para búsquedas rápidas
    dynamic_state JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Metadata
    last_update TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_nfts_owner ON nfts(last_known_owner);
CREATE INDEX IF NOT EXISTS idx_nfts_guild ON nfts(guild);
CREATE INDEX IF NOT EXISTS idx_nfts_state ON nfts((dynamic_state->>'state'));
CREATE INDEX IF NOT EXISTS idx_nfts_xp ON nfts(((dynamic_state->>'xp_total')::int));
CREATE INDEX IF NOT EXISTS idx_nfts_aura ON nfts(((dynamic_state->>'aura_level')::int));

-- -------------------------------------------------------------------------
-- TABLA: MISIONES ACTIVAS
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS active_missions (
    mission_key VARCHAR(100) PRIMARY KEY,                -- "wallet_heroId" (e.g. "0x123_00001")
    wallet VARCHAR(42) NOT NULL,                         -- Wallet address
    hero_id VARCHAR(10) NOT NULL,                        -- Token ID
    mission_id VARCHAR(10) NOT NULL,                     -- Mission ID ("001", "002", etc.)
    start_time TIMESTAMP NOT NULL,                       -- Mission start timestamp
    duration_hours INTEGER NOT NULL,                     -- Mission duration in hours

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    -- Foreign key (opcional - no crítico si el NFT no existe aún)
    CONSTRAINT fk_active_mission_nft FOREIGN KEY (hero_id)
        REFERENCES nfts(token_id) ON DELETE CASCADE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_active_missions_wallet ON active_missions(wallet);
CREATE INDEX IF NOT EXISTS idx_active_missions_hero ON active_missions(hero_id);
CREATE INDEX IF NOT EXISTS idx_active_missions_mission ON active_missions(mission_id);

-- -------------------------------------------------------------------------
-- TABLA: PLAYERS (Cache de sesión por wallet)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS players (
    wallet VARCHAR(42) PRIMARY KEY,                      -- Wallet address (lowercase)
    player_data JSONB NOT NULL DEFAULT '{}'::jsonb,      -- Datos completos del jugador
    last_update TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índice
CREATE INDEX IF NOT EXISTS idx_players_wallet ON players(wallet);

-- -------------------------------------------------------------------------
-- TABLA: STATS GLOBALES
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS global_stats (
    id INTEGER PRIMARY KEY DEFAULT 1,                    -- Solo 1 fila (singleton)
    stats_data JSONB NOT NULL DEFAULT '{}'::jsonb,       -- Stats globales
    last_update TIMESTAMP DEFAULT NOW(),

    -- Constraint para garantizar solo 1 fila
    CONSTRAINT single_row_stats CHECK (id = 1)
);

-- Inicializar stats globales si no existe
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

-- -------------------------------------------------------------------------
-- TABLA: ACHIEVEMENTS
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS achievements (
    token_id VARCHAR(10),                                -- NFT token ID
    achievement_id VARCHAR(100),                         -- Achievement ID
    granted_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (token_id, achievement_id),

    CONSTRAINT fk_achievement_nft FOREIGN KEY (token_id)
        REFERENCES nfts(token_id) ON DELETE CASCADE
);

-- Índice
CREATE INDEX IF NOT EXISTS idx_achievements_token ON achievements(token_id);
CREATE INDEX IF NOT EXISTS idx_achievements_id ON achievements(achievement_id);

-- -------------------------------------------------------------------------
-- FUNCIONES HELPER (Opcional - para queries comunes)
-- -------------------------------------------------------------------------

-- Función: Contar misiones activas
CREATE OR REPLACE FUNCTION count_active_missions()
RETURNS INTEGER AS $$
    SELECT COUNT(*)::INTEGER FROM active_missions;
$$ LANGUAGE SQL;

-- Función: Obtener NFTs por wallet
CREATE OR REPLACE FUNCTION get_nfts_by_wallet(wallet_address VARCHAR(42))
RETURNS TABLE (
    token_id VARCHAR(10),
    name VARCHAR(255),
    guild VARCHAR(100),
    race_class VARCHAR(100),
    dynamic_state JSONB
) AS $$
    SELECT token_id, name, guild, race_class, dynamic_state
    FROM nfts
    WHERE last_known_owner = wallet_address;
$$ LANGUAGE SQL;

-- Función: Actualizar stats globales
CREATE OR REPLACE FUNCTION update_global_stats(new_stats JSONB)
RETURNS VOID AS $$
    UPDATE global_stats
    SET stats_data = new_stats, last_update = NOW()
    WHERE id = 1;
$$ LANGUAGE SQL;

-- -------------------------------------------------------------------------
-- VIEWS (Para queries complejas)
-- -------------------------------------------------------------------------

-- View: Guild statistics (agregado desde NFTs)
CREATE OR REPLACE VIEW guild_stats AS
SELECT
    guild,
    COUNT(*) as members,
    SUM((dynamic_state->>'xp_total')::int) as total_xp,
    SUM((dynamic_state->>'aura_level')::int) as total_aura,
    AVG((dynamic_state->>'xp_total')::int) as avg_xp,
    AVG((dynamic_state->>'aura_level')::int) as avg_aura
FROM nfts
WHERE guild IS NOT NULL
GROUP BY guild;

-- View: Player leaderboard (agregado por wallet)
CREATE OR REPLACE VIEW player_leaderboard AS
SELECT
    last_known_owner as wallet,
    COUNT(*) as heroes_count,
    SUM((dynamic_state->>'xp_total')::int) as xp_total_all,
    SUM((dynamic_state->>'aura_level')::int) as aura_total_all
FROM nfts
WHERE last_known_owner IS NOT NULL
GROUP BY last_known_owner
ORDER BY xp_total_all DESC;

-- -------------------------------------------------------------------------
-- TABLA: ITEMS (Inventory System)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,                       -- weapon, armor, helmet, accessory, amulet, rune
    rarity VARCHAR(50) NOT NULL,                     -- common, rare, epic, legendary
    image_url TEXT,
    stats JSONB NOT NULL DEFAULT '{}'::jsonb,        -- { ember_boost: 20, xp_boost: 20, ... }
    equipped_by VARCHAR(10),                         -- token_id del emissary o null
    owner_wallet VARCHAR(42) NOT NULL,               -- Wallet address
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_item_emissary FOREIGN KEY (equipped_by)
        REFERENCES nfts(token_id) ON DELETE SET NULL
);

-- Índices para items
CREATE INDEX IF NOT EXISTS idx_items_owner ON items(owner_wallet);
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_rarity ON items(rarity);
CREATE INDEX IF NOT EXISTS idx_items_equipped ON items(equipped_by);

-- -------------------------------------------------------------------------
-- TABLA: LANDS (Land Binding System)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    land_token_id VARCHAR(10) UNIQUE,                -- Token ID de la land NFT
    rarity VARCHAR(50) NOT NULL,                     -- common, rare, epic, legendary
    region VARCHAR(100),                             -- "Ashfall Wastes", etc.
    image_url TEXT,
    stats JSONB NOT NULL DEFAULT '{}'::jsonb,        -- { ember_boost: 5, xp_boost: 5, ... }
    bound_emissaries TEXT[],                         -- Array de token_ids vinculados
    max_emissaries INTEGER DEFAULT 5,                -- Max emissaries que pueden vincularse
    owner_wallet VARCHAR(42) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para lands
CREATE INDEX IF NOT EXISTS idx_lands_owner ON lands(owner_wallet);
CREATE INDEX IF NOT EXISTS idx_lands_rarity ON lands(rarity);
CREATE INDEX IF NOT EXISTS idx_lands_token ON lands(land_token_id);

-- -------------------------------------------------------------------------
-- TABLA: USER BALANCES (EMBER & ASH Economy)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_balances (
    wallet VARCHAR(42) PRIMARY KEY,
    ember_balance INTEGER DEFAULT 0,
    ash_balance INTEGER DEFAULT 0,
    gambit_rolls_today INTEGER DEFAULT 0,
    gambit_rolls_max INTEGER DEFAULT 5,
    gambit_next_reset TIMESTAMP,
    last_update TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índice
CREATE INDEX IF NOT EXISTS idx_balances_wallet ON user_balances(wallet);

-- Add EMBER claim tracking columns
ALTER TABLE user_balances ADD COLUMN IF NOT EXISTS total_ember_claimed NUMERIC DEFAULT 0;
ALTER TABLE user_balances ADD COLUMN IF NOT EXISTS last_ember_claim_at TIMESTAMP;

-- Add EMBER burn tracking column
ALTER TABLE user_balances ADD COLUMN IF NOT EXISTS total_ember_burned BIGINT DEFAULT 0;

-- Add EMBER historical earned tracking column (never decreases, only sums)
ALTER TABLE user_balances ADD COLUMN IF NOT EXISTS total_ember_earned BIGINT DEFAULT 0;

-- -------------------------------------------------------------------------
-- EXTENSIÓN DE TABLA NFTs: Añadir columnas de equipamiento
-- -------------------------------------------------------------------------
-- Añadir columnas de equipamiento si no existen
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS weapon_id INTEGER REFERENCES items(id) ON DELETE SET NULL;
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS armor_id INTEGER REFERENCES items(id) ON DELETE SET NULL;
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS helmet_id INTEGER REFERENCES items(id) ON DELETE SET NULL;
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS accessory_id INTEGER REFERENCES items(id) ON DELETE SET NULL;
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS amulet_id INTEGER REFERENCES items(id) ON DELETE SET NULL;
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS rune_ids INTEGER[];
ALTER TABLE nfts ADD COLUMN IF NOT EXISTS land_id INTEGER REFERENCES lands(id) ON DELETE SET NULL;

-- -------------------------------------------------------------------------
-- FUNCIONES HELPER ADICIONALES
-- -------------------------------------------------------------------------

-- Función: Obtener items disponibles (no equipados) por wallet
CREATE OR REPLACE FUNCTION get_available_items(wallet_address VARCHAR(42), item_type VARCHAR(50))
RETURNS TABLE (
    id INTEGER,
    name VARCHAR(255),
    type VARCHAR(50),
    rarity VARCHAR(50),
    image_url TEXT,
    stats JSONB
) AS $$
    SELECT id, name, type, rarity, image_url, stats
    FROM items
    WHERE owner_wallet = wallet_address
      AND equipped_by IS NULL
      AND (item_type IS NULL OR type = item_type);
$$ LANGUAGE SQL;

-- Función: Calcular total de boosts de un emissary
CREATE OR REPLACE FUNCTION calculate_emissary_boosts(emissary_id VARCHAR(10))
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    weapon_stats JSONB;
    armor_stats JSONB;
    helmet_stats JSONB;
    accessory_stats JSONB;
    amulet_stats JSONB;
    land_stats JSONB;
BEGIN
    -- Obtener stats de cada item equipado
    SELECT stats INTO weapon_stats FROM items WHERE id = (SELECT weapon_id FROM nfts WHERE token_id = emissary_id);
    SELECT stats INTO armor_stats FROM items WHERE id = (SELECT armor_id FROM nfts WHERE token_id = emissary_id);
    SELECT stats INTO helmet_stats FROM items WHERE id = (SELECT helmet_id FROM nfts WHERE token_id = emissary_id);
    SELECT stats INTO accessory_stats FROM items WHERE id = (SELECT accessory_id FROM nfts WHERE token_id = emissary_id);
    SELECT stats INTO amulet_stats FROM items WHERE id = (SELECT amulet_id FROM nfts WHERE token_id = emissary_id);
    SELECT stats INTO land_stats FROM lands WHERE id = (SELECT land_id FROM nfts WHERE token_id = emissary_id);

    -- Sumar todos los boosts (implementación simplificada)
    result := '{}'::jsonb;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- -------------------------------------------------------------------------
-- TABLA: REVIVE LOG (Death/Revival System)
-- -------------------------------------------------------------------------
-- Tracks all emissary revives with on-chain transaction hashes
-- Prevents double-spending by enforcing unique tx_hash
CREATE TABLE IF NOT EXISTS revive_log (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(42) NOT NULL,                         -- Wallet address
    emissary_id VARCHAR(10) NOT NULL,                    -- Token ID of the emissary
    amount INTEGER NOT NULL,                             -- $EMBER amount spent
    tx_hash VARCHAR(66) NOT NULL UNIQUE,                 -- On-chain transaction hash
    death_count INTEGER NOT NULL,                        -- Death count at time of revive
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_revive_log_nft FOREIGN KEY (emissary_id)
        REFERENCES nfts(token_id) ON DELETE CASCADE
);

-- Índices para revive_log
CREATE INDEX IF NOT EXISTS idx_revive_log_wallet ON revive_log(wallet);
CREATE INDEX IF NOT EXISTS idx_revive_log_emissary ON revive_log(emissary_id);
CREATE INDEX IF NOT EXISTS idx_revive_log_tx ON revive_log(tx_hash);

-- -------------------------------------------------------------------------
-- TABLA: EVENTS (Sistema de eventos escalable)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,                          -- "The First Spark"
    slug VARCHAR(50) UNIQUE NOT NULL,                    -- "the-first-spark"
    status VARCHAR(20) DEFAULT 'active',                 -- active, ended
    description TEXT,
    start_condition VARCHAR(255),                        -- "mint >= 1"
    end_condition VARCHAR(255),                          -- "mint >= 35000"
    item_drop_multiplier DECIMAL(5,2) DEFAULT 1.00,      -- 3 para este evento
    rune_drop_multiplier DECIMAL(5,2) DEFAULT 1.00,      -- 2 para este evento
    created_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP NULL
);

-- Índices para events
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_slug ON events(slug);

-- -------------------------------------------------------------------------
-- TABLA: EVENT_PRIZES (Premios de cada evento)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS event_prizes (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    prize_name VARCHAR(100) NOT NULL,                    -- "The Fortunate", "The Worthy"
    prize_type VARCHAR(50) NOT NULL,                     -- "random_drop", "leaderboard"
    trophy_token_id INTEGER NOT NULL,                    -- 1 para Golden Rune, 2 para Eternal Torch
    reward_eth DECIMAL(10,4) DEFAULT 0,                  -- 1 ETH
    winner_wallet VARCHAR(42) NULL,                      -- Se llena cuando se determina
    trophy_minted BOOLEAN DEFAULT FALSE,                 -- Si ya se minteó el trofeo
    reward_sent BOOLEAN DEFAULT FALSE,                   -- Si ya se envió el ETH
    found_at TIMESTAMP NULL,                             -- Cuando se encontró/determinó
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para event_prizes
CREATE INDEX IF NOT EXISTS idx_event_prizes_event ON event_prizes(event_id);
CREATE INDEX IF NOT EXISTS idx_event_prizes_trophy ON event_prizes(trophy_token_id);
CREATE INDEX IF NOT EXISTS idx_event_prizes_winner ON event_prizes(winner_wallet);

-- -------------------------------------------------------------------------
-- DATOS INICIALES: Evento "The First Spark"
-- -------------------------------------------------------------------------
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

-- Premios del evento (requiere que el evento exista)
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

-- -------------------------------------------------------------------------
-- VIEW: Event XP Leaderboard (Solo emissaries vivos)
-- -------------------------------------------------------------------------
CREATE OR REPLACE VIEW event_xp_leaderboard AS
SELECT
    last_known_owner as wallet,
    COUNT(*) as emissary_count,
    SUM((dynamic_state->>'xp_total')::int) as total_xp
FROM nfts
WHERE last_known_owner IS NOT NULL
  AND dynamic_state->>'state' != 'FALLEN'
GROUP BY last_known_owner
ORDER BY total_xp DESC;

-- =========================================================================
-- MINI APP TABLES ($SPARK & MICRO-MISSIONS)
-- =========================================================================

-- -------------------------------------------------------------------------
-- TABLA: SPARK BALANCES (Token off-chain para Mini App)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS spark_balances (
    wallet VARCHAR(42) PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    total_earned INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0,
    last_daily_claim TIMESTAMP,
    daily_streak INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índice para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_spark_balances_wallet ON spark_balances(wallet);

-- -------------------------------------------------------------------------
-- TABLA: SPARK TRANSACTIONS (Historial de $SPARK)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS spark_transactions (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(42) NOT NULL,
    amount INTEGER NOT NULL,                          -- Positivo = ganado, Negativo = gastado
    transaction_type VARCHAR(50) NOT NULL,            -- micro_mission, daily_bonus, purchase, convert, spend
    reference_id VARCHAR(100),                        -- ID de la misión, item, etc.
    description TEXT,                                 -- Descripción legible
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para historial
CREATE INDEX IF NOT EXISTS idx_spark_transactions_wallet ON spark_transactions(wallet);
CREATE INDEX IF NOT EXISTS idx_spark_transactions_type ON spark_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_spark_transactions_date ON spark_transactions(created_at);

-- -------------------------------------------------------------------------
-- TABLA: MICRO MISSIONS (Definiciones de aventuras cortas)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS micro_missions (
    id VARCHAR(20) PRIMARY KEY,                       -- "MM-E001", "MM-M001", "MM-H001"
    name VARCHAR(100) NOT NULL,
    description TEXT,
    difficulty VARCHAR(20) NOT NULL,                  -- EASY, MEDIUM, HARD
    duration_seconds INTEGER NOT NULL,                -- 60-300 segundos
    energy_cost INTEGER DEFAULT 0,
    spark_reward_min INTEGER NOT NULL,
    spark_reward_max INTEGER NOT NULL,
    xp_reward_min INTEGER DEFAULT 0,
    xp_reward_max INTEGER DEFAULT 0,
    aura_chance DECIMAL(5,2) DEFAULT 0,               -- Probabilidad de +1 aura (0-100)
    narrative_intro TEXT,                             -- Texto inicial
    narrative_choices JSONB DEFAULT '[]'::jsonb,      -- Array de opciones con textos
    narrative_outcomes JSONB DEFAULT '{}'::jsonb,     -- Resultados por opción
    is_active BOOLEAN DEFAULT TRUE,
    cooldown_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_micro_missions_difficulty ON micro_missions(difficulty);
CREATE INDEX IF NOT EXISTS idx_micro_missions_active ON micro_missions(is_active);

-- -------------------------------------------------------------------------
-- TABLA: ACTIVE MICRO MISSIONS (Sesiones activas)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS active_micro_missions (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(42) NOT NULL,
    emissary_token_id VARCHAR(10) NOT NULL,
    micro_mission_id VARCHAR(20) NOT NULL REFERENCES micro_missions(id),
    started_at TIMESTAMP DEFAULT NOW(),
    ends_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'active',              -- active, choice_pending, completed, claimed
    current_step INTEGER DEFAULT 0,                   -- Paso narrativo actual
    choice_made VARCHAR(50),                          -- Decisión tomada (A, B, C)
    spark_earned INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    aura_earned INTEGER DEFAULT 0,
    outcome_text TEXT,                                -- Texto del resultado
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_micro_emissary FOREIGN KEY (emissary_token_id)
        REFERENCES nfts(token_id) ON DELETE CASCADE
);

-- Índices para micro-misiones activas
CREATE INDEX IF NOT EXISTS idx_active_micro_wallet ON active_micro_missions(wallet);
CREATE INDEX IF NOT EXISTS idx_active_micro_emissary ON active_micro_missions(emissary_token_id);
CREATE INDEX IF NOT EXISTS idx_active_micro_status ON active_micro_missions(status);
CREATE INDEX IF NOT EXISTS idx_active_micro_ends ON active_micro_missions(ends_at);

-- -------------------------------------------------------------------------
-- FUNCIÓN: Obtener estado unificado de emissary (incluye micro-misiones)
-- -------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_emissary_unified_state(p_token_id VARCHAR(10))
RETURNS TABLE (
    token_id VARCHAR(10),
    name VARCHAR(255),
    guild VARCHAR(100),
    race_class VARCHAR(100),
    dynamic_state JSONB,
    current_state VARCHAR(30),
    mission_ends_at TIMESTAMP,
    micro_mission_ends_at TIMESTAMP,
    active_mission_id VARCHAR(10),
    active_micro_mission_id VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.token_id,
        n.name,
        n.guild,
        n.race_class,
        n.dynamic_state,
        CASE
            WHEN am.mission_key IS NOT NULL THEN 'ON_MISSION'
            WHEN amm.status = 'active' OR amm.status = 'choice_pending' THEN 'ON_MICRO_MISSION'
            WHEN (n.dynamic_state->>'state') = 'FALLEN' THEN 'FALLEN'
            WHEN EXISTS (
                SELECT 1 FROM active_missions am2
                WHERE am2.hero_id = n.token_id
                AND am2.start_time + (am2.duration_hours || ' hours')::interval < NOW()
            ) THEN 'CLAIMING'
            ELSE 'READY'
        END::VARCHAR(30) as current_state,
        (am.start_time + (am.duration_hours || ' hours')::interval) as mission_ends_at,
        amm.ends_at as micro_mission_ends_at,
        am.mission_id as active_mission_id,
        amm.micro_mission_id as active_micro_mission_id
    FROM nfts n
    LEFT JOIN active_missions am ON n.token_id = am.hero_id
    LEFT JOIN active_micro_missions amm ON n.token_id = amm.emissary_token_id
        AND amm.status IN ('active', 'choice_pending')
    WHERE n.token_id = p_token_id;
END;
$$ LANGUAGE plpgsql;

-- =========================================================================
-- SCHEMA COMPLETO
-- =========================================================================
-- Ejecutar este script en PostgreSQL para crear todas las tablas
-- Comando: psql $DATABASE_URL -f schema.sql
-- =========================================================================
