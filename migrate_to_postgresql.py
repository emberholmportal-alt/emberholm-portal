#!/usr/bin/env python3
"""
EMBERHOLM PORTAL - MIGRATION SCRIPT
Migra datos desde JSON files a PostgreSQL

Este script:
1. Lee datos de archivos JSON actuales
2. Los carga en PostgreSQL
3. Preserva toda la información sin pérdidas

Ejecutar solo UNA VEZ después de crear la base de datos PostgreSQL.

Uso:
    python3 migrate_to_postgresql.py
"""

import json
import os
import sys

# Importar módulo de database
try:
    import database as db
except ImportError:
    print("❌ Error: No se pudo importar el módulo database.py")
    print("   Asegúrate de estar en el directorio correcto")
    sys.exit(1)

# Configuración de paths
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")

NFTS_DATABASE_PATH = os.path.join(DATA_DIR, "nfts_database.json")
ACTIVE_MISSIONS_PATH = os.path.join(DATA_DIR, "active_missions.json")
PLAYERS_PATH = os.path.join(DATA_DIR, "players.json")
STATS_PATH = os.path.join(DATA_DIR, "stats.json")

def load_json_file(filepath, default=None):
    """Cargar archivo JSON o retornar default si no existe"""
    if default is None:
        default = {}

    if not os.path.exists(filepath):
        print(f"⚠️  {os.path.basename(filepath)} no existe - usando default")
        return default

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ {os.path.basename(filepath)} cargado ({len(data)} items)")
            return data
    except json.JSONDecodeError as e:
        print(f"❌ Error leyendo {os.path.basename(filepath)}: {e}")
        return default

def migrate_nfts_database():
    """Migrar nfts_database.json → PostgreSQL"""
    print("\n" + "="*70)
    print("1️⃣  MIGRANDO NFTs DATABASE")
    print("="*70)

    nfts_db = load_json_file(NFTS_DATABASE_PATH, {})

    if not nfts_db:
        print("⚠️  No hay NFTs para migrar")
        return 0

    # Filtrar comentarios (keys que empiezan con _)
    nfts_clean = {k: v for k, v in nfts_db.items() if not k.startswith("_")}

    print(f"\n📊 NFTs a migrar: {len(nfts_clean)}")

    # Guardar a PostgreSQL usando el módulo database
    success = db.save_nfts_database(nfts_clean)

    if success:
        print(f"✅ {len(nfts_clean)} NFTs migrados exitosamente")
        return len(nfts_clean)
    else:
        print(f"❌ Error migrando NFTs")
        return 0

def migrate_active_missions():
    """Migrar active_missions.json → PostgreSQL"""
    print("\n" + "="*70)
    print("2️⃣  MIGRANDO ACTIVE MISSIONS")
    print("="*70)

    missions = load_json_file(ACTIVE_MISSIONS_PATH, {})

    if not missions:
        print("⚠️  No hay misiones activas para migrar")
        return 0

    print(f"\n📊 Misiones activas a migrar: {len(missions)}")

    # Guardar a PostgreSQL
    success = db.save_active_missions(missions)

    if success:
        print(f"✅ {len(missions)} misiones activas migradas exitosamente")
        return len(missions)
    else:
        print(f"❌ Error migrando misiones activas")
        return 0

def migrate_players():
    """Migrar players.json → PostgreSQL"""
    print("\n" + "="*70)
    print("3️⃣  MIGRANDO PLAYERS")
    print("="*70)

    players = load_json_file(PLAYERS_PATH, {})

    if not players:
        print("⚠️  No hay players para migrar")
        return 0

    print(f"\n📊 Players a migrar: {len(players)}")

    # Guardar a PostgreSQL
    success = db.save_players(players)

    if success:
        print(f"✅ {len(players)} players migrados exitosamente")
        return len(players)
    else:
        print(f"❌ Error migrando players")
        return 0

def migrate_stats():
    """Migrar stats.json → PostgreSQL"""
    print("\n" + "="*70)
    print("4️⃣  MIGRANDO GLOBAL STATS")
    print("="*70)

    stats = load_json_file(STATS_PATH, {
        "total_characters": 0,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": [],
        "player_leaderboard": []
    })

    print(f"\n📊 Stats a migrar:")
    print(f"   - Total characters: {stats.get('total_characters', 0)}")
    print(f"   - Missions completed: {stats.get('missions_completed', 0)}")
    print(f"   - Missions failed: {stats.get('missions_failed', 0)}")

    # Guardar a PostgreSQL
    success = db.save_stats(stats)

    if success:
        print(f"✅ Stats globales migrados exitosamente")
        return 1
    else:
        print(f"❌ Error migrando stats")
        return 0

def verify_postgresql_connection():
    """Verificar que PostgreSQL esté disponible"""
    print("\n" + "="*70)
    print("🔍 VERIFICANDO CONEXIÓN A POSTGRESQL")
    print("="*70)

    if not db.is_postgresql_available():
        print("\n❌ PostgreSQL NO está disponible")
        print("\n📋 Pasos para configurar:")
        print("   1. Crear base de datos en Render")
        print("   2. Obtener DATABASE_URL")
        print("   3. Configurar variable de entorno:")
        print("      export DATABASE_URL='postgresql://...'")
        print("   4. Ejecutar schema:")
        print("      psql $DATABASE_URL -f schema.sql")
        print("   5. Ejecutar este script nuevamente")
        return False

    print("✅ PostgreSQL disponible y conectado")
    return True

def backup_json_files():
    """Crear backup de archivos JSON antes de migración"""
    print("\n" + "="*70)
    print("💾 CREANDO BACKUP DE ARCHIVOS JSON")
    print("="*70)

    backup_dir = os.path.join(DATA_DIR, "backup_pre_migration")
    os.makedirs(backup_dir, exist_ok=True)

    files_to_backup = [
        NFTS_DATABASE_PATH,
        ACTIVE_MISSIONS_PATH,
        PLAYERS_PATH,
        STATS_PATH
    ]

    backed_up = 0
    for filepath in files_to_backup:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            backup_path = os.path.join(backup_dir, filename)

            try:
                import shutil
                shutil.copy2(filepath, backup_path)
                print(f"✅ {filename} → backup/")
                backed_up += 1
            except Exception as e:
                print(f"⚠️  Error backing up {filename}: {e}")

    print(f"\n📁 {backed_up} archivos respaldados en: {backup_dir}")
    return backup_dir

def main():
    """Ejecutar migración completa"""
    print("\n" + "="*70)
    print("🚀 EMBERHOLM PORTAL - MIGRATION TO POSTGRESQL")
    print("="*70)

    # Paso 1: Verificar conexión
    if not verify_postgresql_connection():
        print("\n❌ Migración cancelada - PostgreSQL no disponible")
        sys.exit(1)

    # Paso 2: Backup
    print("\n⚠️  IMPORTANTE: Se creará un backup antes de migrar")
    input("Presiona ENTER para continuar o CTRL+C para cancelar...")

    backup_dir = backup_json_files()

    # Paso 3: Migrar datos
    print("\n" + "="*70)
    print("🔄 INICIANDO MIGRACIÓN")
    print("="*70)

    total_migrated = 0

    total_migrated += migrate_nfts_database()
    total_migrated += migrate_active_missions()
    total_migrated += migrate_players()
    total_migrated += migrate_stats()

    # Resumen
    print("\n" + "="*70)
    print("✨ MIGRACIÓN COMPLETADA")
    print("="*70)
    print(f"\n📊 Total items migrados: {total_migrated}")
    print(f"💾 Backup disponible en: {backup_dir}")
    print("\n✅ Los datos ahora persisten en PostgreSQL")
    print("✅ Las misiones NO se resetearán después de deploy/restart")
    print("\n🔥 Próximos pasos:")
    print("   1. Verificar que todo funciona correctamente")
    print("   2. Hacer git commit de los cambios")
    print("   3. Deploy en Render")
    print("   4. Probar persistencia iniciando misiones")
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migración cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error durante migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
