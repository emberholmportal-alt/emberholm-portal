#!/usr/bin/env python3
"""
MIGRACIÓN: Sistema de Eventos y Trofeos
========================================
Ejecutar UNA VEZ para crear las tablas de eventos en producción.

Uso:
    python migrate_events.py

Requiere:
    - DATABASE_URL configurado en environment
    - O ejecutar con: DATABASE_URL='postgresql://...' python migrate_events.py
"""

import os
import sys

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 no instalado. Ejecuta: pip install psycopg2-binary")
    sys.exit(1)

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL no configurado")
    print("   Configúralo con: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

MIGRATION_SQL = """
-- =========================================================================
-- MIGRACIÓN: Sistema de Eventos y Trofeos (The First Spark)
-- =========================================================================

-- Tabla: events
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

-- Tabla: event_prizes
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

-- View: Leaderboard XP por wallet (solo emissaries vivos)
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

-- Insertar evento: The First Spark
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

-- Insertar premios del evento
INSERT INTO event_prizes (event_id, prize_name, prize_type, trophy_token_id, reward_eth)
SELECT e.id, 'The Fortunate', 'random_drop', 1, 1.0000
FROM events e WHERE e.slug = 'the-first-spark'
  AND NOT EXISTS (SELECT 1 FROM event_prizes ep WHERE ep.event_id = e.id AND ep.prize_name = 'The Fortunate');

INSERT INTO event_prizes (event_id, prize_name, prize_type, trophy_token_id, reward_eth)
SELECT e.id, 'The Worthy', 'leaderboard', 2, 1.0000
FROM events e WHERE e.slug = 'the-first-spark'
  AND NOT EXISTS (SELECT 1 FROM event_prizes ep WHERE ep.event_id = e.id AND ep.prize_name = 'The Worthy');
"""

def run_migration():
    print("\n" + "="*70)
    print("🔧 MIGRACIÓN: Sistema de Eventos y Trofeos")
    print("="*70)

    try:
        print("\n🔗 Conectando a PostgreSQL...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        print("✅ Conexión exitosa")

        print("\n📝 Ejecutando migración...")
        with conn.cursor() as cur:
            cur.execute(MIGRATION_SQL)
        print("✅ Migración ejecutada")

        # Verificar resultados
        print("\n🔍 Verificando tablas creadas...")
        with conn.cursor() as cur:
            # Check events table
            cur.execute("SELECT COUNT(*) FROM events")
            events_count = cur.fetchone()[0]
            print(f"   ✅ events: {events_count} registro(s)")

            # Check event_prizes table
            cur.execute("SELECT COUNT(*) FROM event_prizes")
            prizes_count = cur.fetchone()[0]
            print(f"   ✅ event_prizes: {prizes_count} registro(s)")

            # Show event details
            cur.execute("SELECT name, slug, status, item_drop_multiplier, rune_drop_multiplier FROM events")
            events = cur.fetchall()
            print("\n📊 Eventos:")
            for e in events:
                print(f"   - {e[0]} ({e[1]}) | Status: {e[2]} | Items: x{e[3]}, Runes: x{e[4]}")

            # Show prizes
            cur.execute("""
                SELECT ep.prize_name, ep.prize_type, ep.trophy_token_id, ep.reward_eth, ep.winner_wallet
                FROM event_prizes ep
                JOIN events e ON ep.event_id = e.id
                WHERE e.slug = 'the-first-spark'
            """)
            prizes = cur.fetchall()
            print("\n🏆 Premios de 'The First Spark':")
            for p in prizes:
                winner = p[4][:10] + "..." if p[4] else "No encontrado"
                print(f"   - {p[0]} | Type: {p[1]} | Token: {p[2]} | Reward: {p[3]} ETH | Winner: {winner}")

        conn.close()

        print("\n" + "="*70)
        print("✨ MIGRACIÓN COMPLETADA")
        print("="*70)
        print("\n✅ Las tablas de eventos están listas")
        print("✅ El evento 'The First Spark' está activo")
        print("\n" + "="*70 + "\n")

        return True

    except psycopg2.Error as e:
        print(f"\n❌ Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
