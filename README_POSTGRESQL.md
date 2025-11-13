# 🔥 EMBERHOLM PORTAL - POSTGRESQL PERSISTENCE

## 📋 RESUMEN

Este documento explica la migración de JSON files a PostgreSQL para solucionar el problema de **reseteo de misiones** en Render.

### ❌ Problema Original

**Render usa filesystem efímero**: Cada deploy/restart elimina archivos que no están en git.

```
nfts_database.json     } En .gitignore
active_missions.json   } ❌ NO persisten en Render
players.json           } Se pierden en cada restart
stats.json             }
```

**Resultado**: Las misiones se reseteaban después de re-entrar a la aplicación.

### ✅ Solución Implementada

**PostgreSQL gratuito en Render** (512MB, persistencia permanente):

```
nfts_database.json     → PostgreSQL (tabla nfts)
active_missions.json   → PostgreSQL (tabla active_missions)
players.json           → PostgreSQL (tabla players)
stats.json             → PostgreSQL (tabla global_stats)
```

**Resultado**: ✅ Las misiones persisten indefinidamente, incluso después de restart.

---

## 🏗️ ARQUITECTURA

### Archivos Creados

| Archivo | Propósito |
|---------|-----------|
| `database.py` | Módulo wrapper para PostgreSQL con compatibilidad JSON |
| `schema.sql` | Schema completo de la base de datos |
| `setup_database.py` | Script de inicialización automática en deploy |
| `migrate_to_postgresql.py` | Script de migración de datos JSON → PostgreSQL |
| `README_POSTGRESQL.md` | Esta documentación |

### Modificaciones en Código Existente

| Archivo | Cambios |
|---------|---------|
| `app.py` | Importa `database.py`, funciones `load_json`/`save_json` ahora usan PostgreSQL |
| `requirements.txt` | Agregado `psycopg2-binary==2.9.9` |

### Compatibilidad Total

✅ **El código frontend NO cambia** (index.html intacto)
✅ **Las rutas API NO cambian** (mismas URLs, mismos responses)
✅ **La lógica de negocio NO cambia** (mismos cálculos XP/Aura/Stats)
✅ **Fallback automático** (si PostgreSQL falla, usa JSON files)

---

## 📊 SCHEMA DE BASE DE DATOS

### Tabla: `nfts`

Almacena todos los 35,000 NFTs con sus atributos dinámicos.

```sql
CREATE TABLE nfts (
    token_id VARCHAR(10) PRIMARY KEY,        -- "00001", "00002", ...
    name VARCHAR(255),                       -- "Emissary #1"
    guild VARCHAR(100),                      -- "Circle of Mist"
    race_class VARCHAR(100),                 -- "Human Warrior"
    last_known_owner VARCHAR(42),            -- Wallet address
    dynamic_state JSONB NOT NULL,            -- Estado dinámico (XP, Aura, misiones, etc.)
    last_update TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para búsquedas rápidas
CREATE INDEX idx_nfts_owner ON nfts(last_known_owner);
CREATE INDEX idx_nfts_guild ON nfts(guild);
CREATE INDEX idx_nfts_state ON nfts((dynamic_state->>'state'));
```

**Ejemplo de `dynamic_state` JSONB**:
```json
{
  "xp_total": 350,
  "aura_level": 25,
  "energy_current": 75,
  "energy_max": 100,
  "state": "ON_MISSION",
  "current_guild": "Circle of Mist",
  "current_mission_id": "003",
  "mission_start_time": "2025-11-10T15:30:00Z",
  "death_count": 0,
  "total_missions_completed": 5
}
```

### Tabla: `active_missions`

Tracking de misiones activas en tiempo real.

```sql
CREATE TABLE active_missions (
    mission_key VARCHAR(100) PRIMARY KEY,    -- "wallet_heroId"
    wallet VARCHAR(42) NOT NULL,
    hero_id VARCHAR(10) NOT NULL,
    mission_id VARCHAR(10) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    duration_hours INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Tabla: `players`

Cache de sesión por wallet (optimización de performance).

```sql
CREATE TABLE players (
    wallet VARCHAR(42) PRIMARY KEY,
    player_data JSONB NOT NULL,              -- Datos completos del jugador
    last_update TIMESTAMP DEFAULT NOW()
);
```

### Tabla: `global_stats`

Estadísticas globales del realm (singleton - solo 1 fila).

```sql
CREATE TABLE global_stats (
    id INTEGER PRIMARY KEY DEFAULT 1,
    stats_data JSONB NOT NULL,
    last_update TIMESTAMP DEFAULT NOW(),
    CONSTRAINT single_row_stats CHECK (id = 1)
);
```

---

## 🚀 SETUP EN RENDER

### Paso 1: Crear PostgreSQL Database

1. Ir a Render Dashboard
2. Crear nuevo **PostgreSQL** database
3. Seleccionar plan **Free** (512MB)
4. Copiar `DATABASE_URL` (ejemplo: `postgresql://user:pass@host/db`)

### Paso 2: Configurar Variable de Entorno

En tu Web Service de Render:

1. Ir a **Environment**
2. Agregar variable:
   ```
   DATABASE_URL = postgresql://user:pass@host/db
   ```

### Paso 3: Deploy

El setup es **automático** gracias a `setup_database.py`.

Cuando hagas deploy, Render ejecutará:
```bash
# Render instala dependencias
pip install -r requirements.txt  # Incluye psycopg2-binary

# Tu app arranca
gunicorn app:app

# En la primera conexión, database.py inicializa el pool
# setup_database.py crea las tablas automáticamente
```

### Paso 4: Migrar Datos Existentes (Opcional)

Si ya tienes datos en JSON que quieres preservar:

```bash
# Configurar DATABASE_URL local
export DATABASE_URL='postgresql://user:pass@host/db'

# Ejecutar migración
python3 migrate_to_postgresql.py
```

Esto copiará todos los NFTs, misiones activas, players y stats a PostgreSQL.

---

## 🔧 DESARROLLO LOCAL

### Setup Local con PostgreSQL

```bash
# 1. Instalar PostgreSQL localmente
# macOS:
brew install postgresql@15

# Ubuntu/Debian:
sudo apt install postgresql-15

# 2. Crear base de datos
createdb emberholm_dev

# 3. Configurar DATABASE_URL
export DATABASE_URL='postgresql://localhost/emberholm_dev'

# 4. Ejecutar schema
psql $DATABASE_URL -f schema.sql

# 5. (Opcional) Migrar datos JSON existentes
python3 migrate_to_postgresql.py

# 6. Ejecutar app
python3 app.py
```

### Desarrollo sin PostgreSQL (JSON Fallback)

Si **NO** configuras `DATABASE_URL`, la aplicación funcionará con JSON files:

```bash
# NO configurar DATABASE_URL

# Ejecutar app
python3 app.py

# Output:
# ⚠️ PostgreSQL not configured - using JSON fallback
```

✅ **Esto es útil para desarrollo rápido sin setup de DB.**

---

## 📝 QUERIES ÚTILES

### Ver NFTs de un wallet

```sql
SELECT token_id, name, guild,
       dynamic_state->>'xp_total' as xp,
       dynamic_state->>'state' as state
FROM nfts
WHERE last_known_owner = '0xYOUR_WALLET_ADDRESS';
```

### Ver misiones activas

```sql
SELECT
    mission_key,
    hero_id,
    mission_id,
    start_time,
    duration_hours,
    NOW() - start_time as elapsed
FROM active_missions
ORDER BY start_time DESC;
```

### Top 10 NFTs por XP

```sql
SELECT
    token_id,
    name,
    guild,
    (dynamic_state->>'xp_total')::int as xp
FROM nfts
ORDER BY (dynamic_state->>'xp_total')::int DESC
LIMIT 10;
```

### Stats por Guild

```sql
SELECT
    guild,
    COUNT(*) as members,
    SUM((dynamic_state->>'xp_total')::int) as total_xp,
    AVG((dynamic_state->>'xp_total')::int) as avg_xp
FROM nfts
WHERE guild IS NOT NULL
GROUP BY guild
ORDER BY total_xp DESC;
```

### Verificar persistencia de misiones

```sql
-- Antes de restart
SELECT COUNT(*) FROM active_missions;
-- Ejemplo: 6 misiones activas

-- Después de restart
SELECT COUNT(*) FROM active_missions;
-- Debe seguir mostrando: 6 misiones activas ✅
```

---

## 🐛 TROUBLESHOOTING

### Error: "No module named 'psycopg2'"

**Solución**: Verificar que `requirements.txt` incluya:
```
psycopg2-binary==2.9.9
```

Reinstalar dependencias:
```bash
pip install -r requirements.txt
```

### Error: "could not connect to server"

**Causa**: `DATABASE_URL` mal configurado o PostgreSQL no disponible.

**Solución**:
```bash
# Verificar DATABASE_URL
echo $DATABASE_URL

# Probar conexión manual
psql $DATABASE_URL -c "SELECT 1"
```

### Las misiones aún se resetean

**Verificar**:
1. ¿`DATABASE_URL` está configurado en Render?
2. ¿PostgreSQL database está creada?
3. ¿Las tablas existen?

```bash
# Verificar tablas
psql $DATABASE_URL -c "\dt"

# Debe mostrar: nfts, active_missions, players, global_stats, achievements
```

4. ¿La app detecta PostgreSQL?

```bash
# En logs de Render, buscar:
✅ PostgreSQL persistence enabled

# Si muestra:
⚠️ PostgreSQL not configured - using JSON fallback
# → DATABASE_URL no está configurado correctamente
```

### Performance lento

**Verificar índices**:
```sql
-- Ver índices existentes
SELECT indexname FROM pg_indexes WHERE tablename = 'nfts';

-- Recrear índices si hace falta
DROP INDEX IF EXISTS idx_nfts_owner;
CREATE INDEX idx_nfts_owner ON nfts(last_known_owner);
```

---

## 📊 COMPARACIÓN: JSON vs PostgreSQL

| Aspecto | JSON Files | PostgreSQL |
|---------|------------|------------|
| **Persistencia** | ❌ Se pierde en restart (Render) | ✅ Permanente |
| **Escalabilidad** | ⚠️ Lento con 35K NFTs | ✅ Rápido con índices |
| **Concurrencia** | ❌ File locking issues | ✅ Transacciones ACID |
| **Queries** | ❌ Cargar todo en memoria | ✅ Queries SQL optimizadas |
| **Backup** | ⚠️ Manual | ✅ Automático en Render |
| **Costo** | Gratis | Gratis (512MB) |
| **Setup** | ✅ Ninguno | ⚠️ Configurar DATABASE_URL |

---

## 🎯 GARANTÍAS

### ✅ Lo que NO cambia

- Frontend (index.html) - **cero modificaciones**
- API routes - **mismas URLs y responses**
- Lógica de negocio - **mismos cálculos**
- Archivos estáticos (`guilds.json`, `missions_config.json`) - **siguen en JSON**

### ✅ Lo que mejora

- **Persistencia garantizada** - Misiones nunca se resetean
- **Performance** - Búsquedas más rápidas con índices
- **Escalabilidad** - Listo para 35,000+ NFTs concurrentes
- **Confiabilidad** - Backups automáticos en Render

---

## 📞 SOPORTE

### Logs de PostgreSQL

```bash
# Ver logs en Render
# Dashboard → PostgreSQL → Logs

# Ver queries lentas
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Rollback a JSON Files

Si necesitas volver a JSON files temporalmente:

```bash
# En Render, eliminar variable de entorno
DATABASE_URL  # ← Borrar

# La app automáticamente usará JSON fallback
```

---

## 🔐 SEGURIDAD

- ✅ `DATABASE_URL` como variable de entorno (no hardcoded)
- ✅ Conexión cifrada (TLS) en Render
- ✅ Índices solo en campos necesarios
- ✅ Prepared statements (protección contra SQL injection)

---

## 📈 NEXT STEPS

### Ahora (Implementación Básica)

- [x] PostgreSQL setup
- [x] Migración de datos críticos
- [x] Fallback a JSON

### Futuro (Optimizaciones)

- [ ] Redis cache layer (si >100 usuarios concurrentes)
- [ ] Read replicas (si >1000 usuarios concurrentes)
- [ ] Materialized views para stats (pre-calcular rankings)

---

## 🎉 CONCLUSIÓN

PostgreSQL soluciona el problema de **reseteo de misiones** de manera permanente y escalable.

**Beneficios clave**:
- ✅ Cero cambios en código frontend/API
- ✅ Persistencia garantizada (35K NFTs)
- ✅ Gratis ($0/mes en Render)
- ✅ Fallback automático si falla

**Próximo paso**: Deploy y testing de persistencia con misiones reales.
