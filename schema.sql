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

-- =========================================================================
-- SCHEMA COMPLETO
-- =========================================================================
-- Ejecutar este script en PostgreSQL para crear todas las tablas
-- Comando: psql $DATABASE_URL -f schema.sql
-- =========================================================================
