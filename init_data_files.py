#!/usr/bin/env python3
"""
Script de inicialización de archivos de datos dinámicos.
Ejecutar este script cuando se hace un fresh deploy para crear
los archivos de datos vacíos necesarios para el sistema.

Uso:
    python3 init_data_files.py
"""

import json
import os
from pathlib import Path

# Directorio de datos
DATA_DIR = Path(__file__).parent / "data"

# Archivos a crear con sus contenidos iniciales
DATA_FILES = {
    "nfts_database.json": {},
    "active_missions.json": {},
    "players.json": {},
    "wallet_nfts.json": {},
    "achievements.json": {},
    "stats.json": {
        "total_characters": 0,
        "active_guilds": 6,
        "missions_completed": 0,
        "missions_failed": 0,
        "missions_in_progress": 0,
        "total_exp_collected": 0,
        "total_aura_collected": 0,
        "guild_ranking": []
    },
    "guilds.json": {
        "Forge Legion": {
            "name": "Forge Legion",
            "total_members": 0,
            "total_xp": 0,
            "total_aura": 0,
            "missions_completed": 0,
            "description": "Masters of smithing and warfare"
        },
        "Circle of Mist": {
            "name": "Circle of Mist",
            "total_members": 0,
            "total_xp": 0,
            "total_aura": 0,
            "missions_completed": 0,
            "description": "Wielders of arcane knowledge"
        },
        "Order of Dawn": {
            "name": "Order of Dawn",
            "total_members": 0,
            "total_xp": 0,
            "total_aura": 0,
            "missions_completed": 0,
            "description": "Paladins of light and justice"
        },
        "Shadow Guild": {
            "name": "Shadow Guild",
            "total_members": 0,
            "total_xp": 0,
            "total_aura": 0,
            "missions_completed": 0,
            "description": "Silent operatives in the dark"
        },
        "Horizon Watch": {
            "name": "Horizon Watch",
            "total_members": 0,
            "total_xp": 0,
            "total_aura": 0,
            "missions_completed": 0,
            "description": "Scouts and explorers of the frontier"
        },
        "Void Echoes": {
            "name": "Void Echoes",
            "total_members": 0,
            "total_xp": 0,
            "total_aura": 0,
            "missions_completed": 0,
            "description": "Those who commune with the abyss"
        }
    }
}

def init_data_files():
    """Crea archivos de datos si no existen."""
    # Crear directorio data si no existe
    DATA_DIR.mkdir(exist_ok=True)

    created_files = []
    skipped_files = []

    for filename, content in DATA_FILES.items():
        filepath = DATA_DIR / filename

        if filepath.exists():
            skipped_files.append(filename)
            print(f"⏭️  {filename} ya existe, omitiendo...")
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=4, ensure_ascii=False)
            created_files.append(filename)
            print(f"✅ {filename} creado")

    print("\n" + "="*50)
    print(f"✨ Inicialización completa")
    print(f"📁 Archivos creados: {len(created_files)}")
    print(f"⏭️  Archivos existentes: {len(skipped_files)}")

    if created_files:
        print("\n🔥 Archivos creados:")
        for f in created_files:
            print(f"   - {f}")

    if skipped_files:
        print("\n⏭️  Archivos omitidos (ya existían):")
        for f in skipped_files:
            print(f"   - {f}")

    print("\n⚠️  IMPORTANTE:")
    print("   Estos archivos NO deben incluirse en git (.gitignore los excluye)")
    print("   Son archivos dinámicos que cambian con el juego")
    print("="*50)

if __name__ == "__main__":
    print("🚀 Inicializando archivos de datos dinámicos...\n")
    init_data_files()
