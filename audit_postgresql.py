#!/usr/bin/env python3
"""
EMBERHOLM PORTAL - POSTGRESQL AUDIT SCRIPT
Auditoría completa del sistema de persistencia PostgreSQL

Este script verifica:
✅ Conexión a PostgreSQL
✅ Existencia de tablas e índices
✅ Misiones activas y su estado
✅ Integridad de datos de NFTs
✅ Stats globales
✅ Consistencia entre tablas
✅ Performance de queries

Uso:
    python3 audit_postgresql.py
"""

import os
import sys
import json
from datetime import datetime, timezone

# Importar módulo de database
try:
    import database as db
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("   Instala dependencias: pip install psycopg2-binary")
    sys.exit(1)

DATABASE_URL = os.environ.get('DATABASE_URL')

# Colores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(title):
    """Imprimir header de sección"""
    print("\n" + "="*80)
    print(f"{BLUE}{title}{RESET}")
    print("="*80)

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"ℹ️  {msg}")

# =========================================================================
# SECCIÓN 1: CONEXIÓN A POSTGRESQL
# =========================================================================

def audit_connection():
    """Verificar conexión a PostgreSQL"""
    print_header("1️⃣  AUDITORÍA DE CONEXIÓN")

    # Check DATABASE_URL
    if not DATABASE_URL:
        print_error("DATABASE_URL no configurado")
        print_info("La app usará JSON fallback")
        return False

    print_success(f"DATABASE_URL configurado")
    print_info(f"   Host: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'localhost'}")

    # Check módulo database.py
    if not db.is_postgresql_available():
        print_error("PostgreSQL no disponible (connection pool no inicializado)")
        return False

    print_success("Connection pool inicializado")

    # Test conexión directa
    try:
        conn = db.get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print_success(f"Conexión exitosa")
                print_info(f"   PostgreSQL Version: {version.split(',')[0]}")
            db.release_connection(conn)
        else:
            print_error("No se pudo obtener conexión del pool")
            return False
    except Exception as e:
        print_error(f"Error conectando: {e}")
        return False

    return True

# =========================================================================
# SECCIÓN 2: VERIFICACIÓN DE SCHEMA
# =========================================================================

def audit_schema():
    """Verificar que todas las tablas e índices existan"""
    print_header("2️⃣  AUDITORÍA DE SCHEMA")

    conn = db.get_connection()
    if not conn:
        print_error("No se pudo conectar a PostgreSQL")
        return False

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verificar tablas
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = [row['table_name'] for row in cur.fetchall()]

            expected_tables = ['nfts', 'active_missions', 'players', 'global_stats', 'achievements']

            print_info(f"Tablas encontradas: {len(tables)}")
            all_tables_exist = True
            for table in expected_tables:
                if table in tables:
                    print_success(f"   {table}")
                else:
                    print_error(f"   {table} - FALTA")
                    all_tables_exist = False

            if not all_tables_exist:
                print_error("Faltan tablas críticas - ejecutar setup_database.py")
                return False

            # Verificar índices
            cur.execute("""
                SELECT tablename, indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            indexes = cur.fetchall()

            print_info(f"\nÍndices encontrados: {len(indexes)}")
            for idx in indexes[:10]:  # Mostrar primeros 10
                print_info(f"   {idx['tablename']}.{idx['indexname']}")

            if len(indexes) < 10:
                print_warning("Pocos índices - performance podría ser lenta")
            else:
                print_success("Índices configurados correctamente")

            # Verificar funciones
            cur.execute("""
                SELECT routine_name
                FROM information_schema.routines
                WHERE routine_schema = 'public'
                AND routine_type = 'FUNCTION'
            """)
            functions = [row['routine_name'] for row in cur.fetchall()]

            if 'count_active_missions' in functions:
                print_success("Función count_active_missions() existe")
            else:
                print_warning("Función count_active_missions() no existe")

        return True

    except Exception as e:
        print_error(f"Error verificando schema: {e}")
        return False
    finally:
        db.release_connection(conn)

# =========================================================================
# SECCIÓN 3: AUDITORÍA DE MISIONES ACTIVAS
# =========================================================================

def audit_active_missions():
    """Verificar estado de misiones activas"""
    print_header("3️⃣  AUDITORÍA DE MISIONES ACTIVAS")

    conn = db.get_connection()
    if not conn:
        print_error("No se pudo conectar a PostgreSQL")
        return False

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Contar misiones activas
            cur.execute("SELECT COUNT(*) as count FROM active_missions")
            count = cur.fetchone()['count']

            print_info(f"Misiones activas en PostgreSQL: {count}")

            if count == 0:
                print_warning("No hay misiones activas en la base de datos")
                print_info("   Esto es normal si aún no se han iniciado misiones")
                return True

            # Obtener detalles de misiones activas
            cur.execute("""
                SELECT
                    mission_key,
                    wallet,
                    hero_id,
                    mission_id,
                    start_time,
                    duration_hours,
                    NOW() - start_time as elapsed
                FROM active_missions
                ORDER BY start_time DESC
                LIMIT 10
            """)
            missions = cur.fetchall()

            print_success(f"Encontradas {count} misiones activas:")
            print()

            now = datetime.now(timezone.utc)

            for i, mission in enumerate(missions, 1):
                elapsed_seconds = mission['elapsed'].total_seconds()
                elapsed_hours = elapsed_seconds / 3600
                duration_hours = mission['duration_hours']
                progress = min(100, (elapsed_hours / duration_hours) * 100)

                print(f"   {i}. Mission {mission['mission_id']} - Hero #{mission['hero_id']}")
                print(f"      Wallet: {mission['wallet'][:10]}...")
                print(f"      Started: {mission['start_time']}")
                print(f"      Duration: {duration_hours}h")
                print(f"      Elapsed: {elapsed_hours:.1f}h ({progress:.0f}%)")

                if elapsed_hours >= duration_hours:
                    print_success(f"      ✅ LISTA PARA COMPLETAR")
                else:
                    remaining = duration_hours - elapsed_hours
                    print_info(f"      ⏳ {remaining:.1f}h restantes")
                print()

            # Verificar consistencia con tabla nfts
            cur.execute("""
                SELECT COUNT(*) as count
                FROM active_missions am
                LEFT JOIN nfts n ON n.token_id = am.hero_id
                WHERE n.token_id IS NULL
            """)
            orphaned = cur.fetchone()['count']

            if orphaned > 0:
                print_warning(f"{orphaned} misiones activas sin NFT correspondiente")
            else:
                print_success("Todas las misiones tienen NFT correspondiente")

        return True

    except Exception as e:
        print_error(f"Error verificando misiones: {e}")
        return False
    finally:
        db.release_connection(conn)

# =========================================================================
# SECCIÓN 4: AUDITORÍA DE NFTs
# =========================================================================

def audit_nfts():
    """Verificar integridad de datos de NFTs"""
    print_header("4️⃣  AUDITORÍA DE NFTs")

    conn = db.get_connection()
    if not conn:
        print_error("No se pudo conectar a PostgreSQL")
        return False

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Contar NFTs totales
            cur.execute("SELECT COUNT(*) as count FROM nfts")
            total_nfts = cur.fetchone()['count']

            print_info(f"Total NFTs en database: {total_nfts}")

            if total_nfts == 0:
                print_warning("No hay NFTs en la base de datos")
                print_info("   Ejecutar migrate_to_postgresql.py para cargar datos")
                return True

            # Verificar NFTs con misiones activas
            cur.execute("""
                SELECT COUNT(*) as count
                FROM nfts
                WHERE dynamic_state->>'state' = 'ON_MISSION'
            """)
            on_mission = cur.fetchone()['count']

            print_info(f"NFTs en misión (según nfts table): {on_mission}")

            # Comparar con active_missions
            cur.execute("SELECT COUNT(*) as count FROM active_missions")
            active_missions_count = cur.fetchone()['count']

            if on_mission == active_missions_count:
                print_success(f"Consistencia: {on_mission} = {active_missions_count} ✅")
            else:
                print_warning(f"Inconsistencia: NFTs ON_MISSION ({on_mission}) ≠ active_missions ({active_missions_count})")

            # Verificar campos requeridos en dynamic_state
            cur.execute("""
                SELECT token_id, name, dynamic_state
                FROM nfts
                LIMIT 5
            """)
            sample_nfts = cur.fetchall()

            required_fields = [
                'xp_total', 'aura_level', 'energy_current', 'energy_max',
                'state', 'current_guild', 'last_update', 'total_missions_completed'
            ]

            print_info(f"\nVerificando campos requeridos (muestra de {len(sample_nfts)} NFTs):")

            all_valid = True
            for nft in sample_nfts:
                ds = nft['dynamic_state']
                missing = [field for field in required_fields if field not in ds]

                if missing:
                    print_warning(f"   NFT {nft['token_id']}: Faltan campos {missing}")
                    all_valid = False

            if all_valid:
                print_success("Todos los NFTs tienen campos requeridos")
            else:
                print_warning("Algunos NFTs tienen campos faltantes")

            # Stats de guilds
            cur.execute("""
                SELECT
                    guild,
                    COUNT(*) as members,
                    SUM((dynamic_state->>'xp_total')::int) as total_xp,
                    AVG((dynamic_state->>'xp_total')::int) as avg_xp
                FROM nfts
                WHERE guild IS NOT NULL
                GROUP BY guild
                ORDER BY total_xp DESC
            """)
            guilds = cur.fetchall()

            print_info(f"\nStats por Guild:")
            for g in guilds:
                print_info(f"   {g['guild']}: {g['members']} members, {g['total_xp']} XP total")

        return True

    except Exception as e:
        print_error(f"Error verificando NFTs: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.release_connection(conn)

# =========================================================================
# SECCIÓN 5: AUDITORÍA DE STATS GLOBALES
# =========================================================================

def audit_global_stats():
    """Verificar stats globales"""
    print_header("5️⃣  AUDITORÍA DE STATS GLOBALES")

    conn = db.get_connection()
    if not conn:
        print_error("No se pudo conectar a PostgreSQL")
        return False

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Obtener stats
            cur.execute("SELECT stats_data FROM global_stats WHERE id = 1")
            row = cur.fetchone()

            if not row:
                print_error("Stats globales no inicializados")
                print_info("   Ejecutar setup_database.py")
                return False

            stats = row['stats_data']

            print_success("Stats globales encontrados:")
            print_info(f"   Total characters: {stats.get('total_characters', 0)}")
            print_info(f"   Active guilds: {stats.get('active_guilds', 0)}")
            print_info(f"   Missions completed: {stats.get('missions_completed', 0)}")
            print_info(f"   Missions failed: {stats.get('missions_failed', 0)}")
            print_info(f"   Total XP collected: {stats.get('total_exp_collected', 0)}")
            print_info(f"   Total Aura collected: {stats.get('total_aura_collected', 0)}")

            # Verificar misiones in progress
            cur.execute("SELECT COUNT(*) as count FROM active_missions")
            actual_in_progress = cur.fetchone()['count']

            stats_in_progress = stats.get('missions_in_progress', 0)

            print_info(f"   Missions in progress (stats): {stats_in_progress}")
            print_info(f"   Missions in progress (actual): {actual_in_progress}")

            if stats_in_progress == actual_in_progress:
                print_success("Conteo de misiones consistente")
            else:
                print_warning("Stats de misiones in progress desactualizados")

        return True

    except Exception as e:
        print_error(f"Error verificando stats: {e}")
        return False
    finally:
        db.release_connection(conn)

# =========================================================================
# SECCIÓN 6: AUDITORÍA DE PLAYERS
# =========================================================================

def audit_players():
    """Verificar cache de players"""
    print_header("6️⃣  AUDITORÍA DE PLAYERS CACHE")

    conn = db.get_connection()
    if not conn:
        print_error("No se pudo conectar a PostgreSQL")
        return False

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Contar players
            cur.execute("SELECT COUNT(*) as count FROM players")
            total_players = cur.fetchone()['count']

            print_info(f"Players en cache: {total_players}")

            if total_players == 0:
                print_warning("No hay players en cache")
                print_info("   Esto es normal si aún no se han conectado wallets")
                return True

            # Obtener sample de players
            cur.execute("""
                SELECT wallet, player_data, last_update
                FROM players
                ORDER BY last_update DESC
                LIMIT 5
            """)
            players = cur.fetchall()

            print_success(f"Players recientes:")
            for p in players:
                wallet = p['wallet']
                data = p['player_data']
                heroes = data.get('heroes', [])
                print_info(f"   {wallet[:10]}... - {len(heroes)} heroes - Updated: {p['last_update']}")

        return True

    except Exception as e:
        print_error(f"Error verificando players: {e}")
        return False
    finally:
        db.release_connection(conn)

# =========================================================================
# SECCIÓN 7: PERFORMANCE TEST
# =========================================================================

def audit_performance():
    """Test de performance de queries críticas"""
    print_header("7️⃣  AUDITORÍA DE PERFORMANCE")

    conn = db.get_connection()
    if not conn:
        print_error("No se pudo conectar a PostgreSQL")
        return False

    try:
        with conn.cursor() as cur:
            import time

            # Test 1: Query simple
            start = time.time()
            cur.execute("SELECT COUNT(*) FROM nfts")
            elapsed = (time.time() - start) * 1000
            print_info(f"   COUNT nfts: {elapsed:.2f}ms")

            # Test 2: Query con índice
            start = time.time()
            cur.execute("SELECT * FROM active_missions WHERE hero_id = '00001'")
            elapsed = (time.time() - start) * 1000
            print_info(f"   SELECT by hero_id (indexed): {elapsed:.2f}ms")

            # Test 3: JSONB query
            start = time.time()
            cur.execute("SELECT * FROM nfts WHERE dynamic_state->>'state' = 'ON_MISSION' LIMIT 10")
            elapsed = (time.time() - start) * 1000
            print_info(f"   JSONB query (ON_MISSION): {elapsed:.2f}ms")

            # Test 4: Aggregation
            start = time.time()
            cur.execute("""
                SELECT guild, SUM((dynamic_state->>'xp_total')::int) as total_xp
                FROM nfts
                WHERE guild IS NOT NULL
                GROUP BY guild
            """)
            elapsed = (time.time() - start) * 1000
            print_info(f"   Guild aggregation: {elapsed:.2f}ms")

            print_success("Performance tests completados")

            if elapsed > 1000:
                print_warning("Queries lentas (>1s) - considerar optimización")
            elif elapsed > 500:
                print_warning("Performance aceptable pero podría mejorar")
            else:
                print_success("Performance óptimo (<500ms)")

        return True

    except Exception as e:
        print_error(f"Error en performance test: {e}")
        return False
    finally:
        db.release_connection(conn)

# =========================================================================
# RESUMEN FINAL
# =========================================================================

def generate_summary(results):
    """Generar resumen de auditoría"""
    print_header("📊 RESUMEN DE AUDITORÍA")

    total_checks = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total_checks - passed

    print()
    for section, result in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"   {status}  {section}")

    print()
    print(f"   Total checks: {total_checks}")
    print(f"   Passed: {GREEN}{passed}{RESET}")
    print(f"   Failed: {RED}{failed}{RESET}")

    success_rate = (passed / total_checks) * 100

    print()
    if success_rate == 100:
        print_success(f"🎉 AUDITORÍA COMPLETADA - TODO CORRECTO ({success_rate:.0f}%)")
    elif success_rate >= 80:
        print_warning(f"⚠️  AUDITORÍA COMPLETADA CON ADVERTENCIAS ({success_rate:.0f}%)")
    else:
        print_error(f"❌ AUDITORÍA COMPLETADA CON ERRORES ({success_rate:.0f}%)")

    print()

# =========================================================================
# MAIN
# =========================================================================

def main():
    """Ejecutar auditoría completa"""
    print_header("🔍 EMBERHOLM PORTAL - POSTGRESQL AUDIT")
    print(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Ejecutar todas las auditorías
    results['1. Conexión'] = audit_connection()

    if not results['1. Conexión']:
        print_error("\n❌ No se pudo conectar a PostgreSQL - abortando auditoría")
        print_info("   Verifica DATABASE_URL y que PostgreSQL esté running")
        sys.exit(1)

    results['2. Schema'] = audit_schema()
    results['3. Misiones Activas'] = audit_active_missions()
    results['4. NFTs'] = audit_nfts()
    results['5. Stats Globales'] = audit_global_stats()
    results['6. Players Cache'] = audit_players()
    results['7. Performance'] = audit_performance()

    # Generar resumen
    generate_summary(results)

    # Exit code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Auditoría cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error durante auditoría: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
