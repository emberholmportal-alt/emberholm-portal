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

-- TABLA: AUDIT LOG
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100),
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para audit_log
CREATE INDEX IF NOT EXISTS idx_audit_log_type ON audit_log(operation_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);

-- TABLA: ERROR LOG
CREATE TABLE IF NOT EXISTS error_log (
    id SERIAL PRIMARY KEY,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    context JSONB DEFAULT '{}'::jsonb,
    severity VARCHAR(20) DEFAULT 'ERROR',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para error_log
CREATE INDEX IF NOT EXISTS idx_error_log_type ON error_log(error_type);
CREATE INDEX IF NOT EXISTS idx_error_log_severity ON error_log(severity);
CREATE INDEX IF NOT EXISTS idx_error_log_created ON error_log(created_at DESC);

-- TABLA: PERFORMANCE METRICS
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    status_code INTEGER,
    user_wallet VARCHAR(42),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para performance_metrics
CREATE INDEX IF NOT EXISTS idx_perf_endpoint ON performance_metrics(endpoint);
CREATE INDEX IF NOT EXISTS idx_perf_created ON performance_metrics(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_perf_wallet ON performance_metrics(user_wallet);
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
