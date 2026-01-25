#!/usr/bin/env python3
"""
EMBERHOLM PORTAL - DATABASE SETUP SCRIPT
Inicializa el schema de PostgreSQL automáticamente en deploy

Este script se ejecuta automáticamente en Render para:
1. Crear las tablas si no existen
2. Crear índices
3. Crear funciones helper
4. Verificar conexión

Es SEGURO ejecutarlo múltiples veces (usa IF NOT EXISTS)
"""

import os
import sys
import psycopg2

# Obtener DATABASE_URL de environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("⚠️  DATABASE_URL no configurado - saltando setup de PostgreSQL")
    print("   La aplicación funcionará con JSON fallback")
    sys.exit(0)

# Schema SQL (inline para no depender de archivo externo)
SCHEMA_SQL = """
-- EMBERHOLM PORTAL - POSTGRESQL SCHEMA

-- Extensión para JSONB
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- TABLA: NFTs
CREATE TABLE IF NOT EXISTS nfts (
    token_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    guild VARCHAR(100),
    race_class VARCHAR(100),
    last_known_owner VARCHAR(42),
    dynamic_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_update TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para NFTs
CREATE INDEX IF NOT EXISTS idx_nfts_owner ON nfts(last_known_owner);
CREATE INDEX IF NOT EXISTS idx_nfts_guild ON nfts(guild);
CREATE INDEX IF NOT EXISTS idx_nfts_state ON nfts((dynamic_state->>'state'));
CREATE INDEX IF NOT EXISTS idx_nfts_xp ON nfts(((dynamic_state->>'xp_total')::int));
CREATE INDEX IF NOT EXISTS idx_nfts_aura ON nfts(((dynamic_state->>'aura_level')::int));

-- TABLA: ACTIVE MISSIONS
CREATE TABLE IF NOT EXISTS active_missions (
    mission_key VARCHAR(100) PRIMARY KEY,
    wallet VARCHAR(42) NOT NULL,
    hero_id VARCHAR(10) NOT NULL,
    mission_id VARCHAR(10) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    duration_hours INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para active_missions
CREATE INDEX IF NOT EXISTS idx_active_missions_wallet ON active_missions(wallet);
CREATE INDEX IF NOT EXISTS idx_active_missions_hero ON active_missions(hero_id);
CREATE INDEX IF NOT EXISTS idx_active_missions_mission ON active_missions(mission_id);

-- TABLA: PLAYERS
CREATE TABLE IF NOT EXISTS players (
    wallet VARCHAR(42) PRIMARY KEY,
    player_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_update TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índice para players
CREATE INDEX IF NOT EXISTS idx_players_wallet ON players(wallet);

-- TABLA: GLOBAL STATS
CREATE TABLE IF NOT EXISTS global_stats (
    id INTEGER PRIMARY KEY DEFAULT 1,
    stats_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_update TIMESTAMP DEFAULT NOW(),
    CONSTRAINT single_row_stats CHECK (id = 1)
);

-- Inicializar stats globales
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

-- TABLA: ACHIEVEMENTS
CREATE TABLE IF NOT EXISTS achievements (
    token_id VARCHAR(10),
    achievement_id VARCHAR(100),
    granted_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (token_id, achievement_id)
);

-- Índices para achievements
CREATE INDEX IF NOT EXISTS idx_achievements_token ON achievements(token_id);
CREATE INDEX IF NOT EXISTS idx_achievements_id ON achievements(achievement_id);

-- FUNCIÓN: Contar misiones activas
CREATE OR REPLACE FUNCTION count_active_missions()
RETURNS INTEGER AS $$
    SELECT COUNT(*)::INTEGER FROM active_missions;
$$ LANGUAGE SQL;

-- TABLA: EVENTS (Sistema de eventos escalable)
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

-- Índices para events
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_slug ON events(slug);

-- TABLA: EVENT_PRIZES
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

-- Índices para event_prizes
CREATE INDEX IF NOT EXISTS idx_event_prizes_event ON event_prizes(event_id);
CREATE INDEX IF NOT EXISTS idx_event_prizes_trophy ON event_prizes(trophy_token_id);
CREATE INDEX IF NOT EXISTS idx_event_prizes_winner ON event_prizes(winner_wallet);

-- Datos iniciales: Evento "The First Spark"
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
SELECT e.id, 'The Fortunate', 'random_drop', 1, 1.0000
FROM events e WHERE e.slug = 'the-first-spark'
  AND NOT EXISTS (SELECT 1 FROM event_prizes ep WHERE ep.event_id = e.id AND ep.prize_name = 'The Fortunate');

INSERT INTO event_prizes (event_id, prize_name, prize_type, trophy_token_id, reward_eth)
SELECT e.id, 'The Worthy', 'leaderboard', 2, 1.0000
FROM events e WHERE e.slug = 'the-first-spark'
  AND NOT EXISTS (SELECT 1 FROM event_prizes ep WHERE ep.event_id = e.id AND ep.prize_name = 'The Worthy');

-- VIEW: Event XP Leaderboard (Solo emissaries vivos)
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
"""

def setup_database():
    """Ejecutar setup de base de datos"""
    print("\n" + "="*70)
    print("🔧 EMBERHOLM PORTAL - DATABASE SETUP")
    print("="*70)

    try:
        # Conectar a PostgreSQL
        print("\n🔗 Conectando a PostgreSQL...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True

        print("✅ Conexión exitosa")

        # Ejecutar schema
        print("\n📝 Ejecutando schema SQL...")
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)

        print("✅ Schema ejecutado correctamente")

        # Verificar tablas creadas
        print("\n🔍 Verificando tablas...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = cur.fetchall()

            print(f"\n📊 Tablas creadas ({len(tables)}):")
            for table in tables:
                print(f"   ✅ {table[0]}")

        # Verificar stats inicializados
        print("\n🔍 Verificando stats globales...")
        with conn.cursor() as cur:
            cur.execute("SELECT stats_data FROM global_stats WHERE id = 1")
            row = cur.fetchone()
            if row:
                print("✅ Stats globales inicializados correctamente")
            else:
                print("⚠️  Stats globales no encontrados")

        conn.close()

        print("\n" + "="*70)
        print("✨ DATABASE SETUP COMPLETADO")
        print("="*70)
        print("\n✅ PostgreSQL está listo para usar")
        print("✅ Las misiones persistirán después de restart")
        print("\n" + "="*70 + "\n")

        return True

    except psycopg2.Error as e:
        print(f"\n❌ Error de PostgreSQL: {e}")
        print("\n⚠️  La aplicación funcionará con JSON fallback")
        return False

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("\n⚠️  La aplicación funcionará con JSON fallback")
        return False

if __name__ == "__main__":
    try:
        setup_database()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelado")
        sys.exit(0)
