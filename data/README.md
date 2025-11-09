# Data Directory

Este directorio contiene archivos de datos para el sistema de misiones de Emberholm Portal.

## Archivos Estáticos (en Git)

- **`missions_config.json`** - Configuración de misiones (9 misiones, costos, recompensas, death penalties, bonuses)
  - ✅ Este archivo DEBE estar en git
  - ⚙️ Contiene configuración estática del juego

## Archivos Dinámicos (NO en Git)

Los siguientes archivos son dinámicos y **NO** deben incluirse en git:

- **`nfts_database.json`** - Base de datos completa de 35,000 NFTs con sus estados dinámicos
- **`active_missions.json`** - Tracking de misiones actualmente en progreso
- **`players.json`** - Cache de sesión de datos de jugadores
- **`wallet_nfts.json`** - Mapeo de wallets a token IDs de NFTs
- **`stats.json`** - Estadísticas globales del realm
- **`guilds.json`** - Estadísticas agregadas por guild
- **`achievements.json`** - Sistema de logros (futuro)

### ⚠️ IMPORTANTE

Estos archivos dinámicos:
- ❌ NO deben committearse a git (ya están en `.gitignore`)
- 💾 Persisten localmente y almacenan el progreso del juego
- 🔄 Se actualizan constantemente durante el juego
- 🚀 En fresh deploy, ejecutar `python3 ../init_data_files.py` para crearlos

## Inicialización en Fresh Deploy

Si haces un fresh deploy o los archivos dinámicos no existen, ejecuta:

```bash
python3 init_data_files.py
```

Este script creará versiones vacías/iniciales de todos los archivos dinámicos necesarios.

## Estructura de Datos

### nfts_database.json
```json
{
  "token_id": {
    "token_id": "1",
    "metadata": { "name": "...", "class": "...", "race": "...", "guild": "..." },
    "dynamic_state": {
      "xp_total": 0,
      "aura_level": 0,
      "energy_current": 100,
      "energy_max": 100,
      "state": "READY",
      "current_guild": "...",
      "last_update": "2025-11-09T12:00:00Z",
      "last_energy_refresh": "2025-11-09T12:00:00Z",
      "mission_history": {},
      "power_current": 100,
      "xp_level": 1,
      "last_mission": "None",
      "total_missions_completed": 0,
      "death_count": 0,
      "current_mission_id": null,
      "mission_start_time": null,
      "fallen_time": null
    }
  }
}
```

### active_missions.json
```json
{
  "token_id": {
    "mission_id": "001",
    "start_time": "2025-11-09T12:00:00Z",
    "wallet": "0x..."
  }
}
```

### stats.json
```json
{
  "total_characters": 35000,
  "active_guilds": 6,
  "missions_completed": 0,
  "missions_failed": 0,
  "missions_in_progress": 0,
  "total_exp_collected": 0,
  "total_aura_collected": 0,
  "guild_ranking": []
}
```

## Sistema de Validación

El servidor ejecuta validación automática en cada inicio (`validate_database_integrity()`) que:
- ✅ Verifica que todos los NFTs tengan los 17 campos dinámicos requeridos
- 🔧 Auto-corrige campos faltantes con valores por defecto
- 📊 Reporta cuántos NFTs fueron corregidos

## Escalabilidad

El sistema está preparado para manejar:
- 🎮 **35,000 NFTs** con estados individuales
- 👥 **Miles de wallets** con diferentes cantidades de NFTs
- ⚔️ **Múltiples misiones simultáneas** por wallet
- 📈 **Estadísticas globales** actualizadas en tiempo real
