# REPORTE DE ANALISIS - EMBERHOLM PORTAL PARA KINDLING

**Fecha:** 2026-01-26
**Version:** 1.0
**Estado:** Analisis Completo - Pendiente Validacion

---

## 1. RESUMEN EJECUTIVO

### Estado Actual del Proyecto

Emberholm Portal es un juego NFT maduro y bien estructurado con:
- **35,000 NFTs** (Emissaries) en Base Mainnet
- **Sistema de misiones** completo con exito/fallo/muerte
- **Sistema de rewards** (XP, Aura, Items, Runes, $EMBER)
- **Sistema de equipamiento** (5 slots + 2 runas)
- **Sistema de Guilds** (6 guilds con bonificaciones)
- **Sistema de locks** PostgreSQL para prevenir race conditions
- **Backend signer** para claims de drops

### Viabilidad de KINDLING

**VIABLE CON MODIFICACIONES MENORES**

El proyecto tiene una arquitectura solida que soporta la implementacion de KINDLING:

| Componente | Estado | Accion Requerida |
|------------|--------|------------------|
| Sistema de estados NFT | Existe | Agregar estado `IN_KINDLING` |
| Sistema de locks | Existe | Extender para locks cross-app |
| Sistema de rewards | Existe | Reutilizar calculos existentes |
| Backend signing | Existe | Reutilizar para claims |
| Base de datos | PostgreSQL | Agregar 5-6 tablas nuevas |
| CORS | Configurado | Agregar dominio kindling |
| Rate limiting | Existe | Agregar endpoints nuevos |

---

## 2. ENDPOINTS EXISTENTES REUTILIZABLES

### 2.1 Endpoints de NFTs/Emissaries

| Endpoint | Metodo | Uso en Kindling | Referencia |
|----------|--------|-----------------|------------|
| `/api/player/<wallet>` | GET | Obtener lista de NFTs disponibles | app.py:3541 |
| `/api/player/<wallet>` | POST | Sincronizar NFTs al backend | app.py:3541 |
| `/api/metadata/<token_id>` | GET | Obtener estado completo del NFT | app.py:6047 |
| `/api/equipment/<emissary_id>` | GET | Ver equipo del NFT | app.py:8127 |

### 2.2 Endpoints de Balance/Economia

| Endpoint | Metodo | Uso en Kindling | Referencia |
|----------|--------|-----------------|------------|
| `/api/balance?wallet=` | GET | Consultar balance $EMBER | inventory.js:383 |
| `/api/ember/balance/<wallet>` | GET | Balance on-chain | app.py:7630 |
| `/api/ember/claim` | POST | Claim de $EMBER (con modificaciones) | app.py:7700 |

### 2.3 Endpoints de Guilds

| Endpoint | Metodo | Uso en Kindling | Referencia |
|----------|--------|-----------------|------------|
| `/api/guilds` | GET | Obtener rankings de guilds | app.py:2786 |

### 2.4 Funciones Internas Reutilizables

| Funcion | Ubicacion | Uso en Kindling |
|---------|-----------|-----------------|
| `get_emissary_bonuses()` | app.py:1078-1187 | Calcular bonos de equipo para aventuras |
| `generate_claim_signature()` | app.py:2405-2448 | Firmar drops de items/runas |
| `calculate_drops()` | app.py:2544-2606 | Determinar drops post-aventura |
| `acquire_hero_lock()` | app.py:9265-9301 | Lock exclusivo de NFT |
| `now_utc_str()` | app.py:1976-1977 | Timestamps UTC consistentes |
| `hours_since()` | app.py:2002-2023 | Calcular tiempo transcurrido |

---

## 3. TABLAS DE BASE DE DATOS EXISTENTES

### 3.1 Tabla Principal: `nfts`

**Ubicacion:** schema.sql:14-27, database.py:202-236

| Campo | Tipo | Uso en Kindling |
|-------|------|-----------------|
| `token_id` | VARCHAR(10) PK | Identificador unico del NFT |
| `name` | VARCHAR(255) | Nombre del Emissary |
| `guild` | VARCHAR(100) | Guild asignada (bonificaciones) |
| `last_known_owner` | VARCHAR(42) | Wallet propietaria |
| `dynamic_state` | JSONB | **CRITICO** - Estado mutable del NFT |
| `weapon_id`, `armor_id`, etc. | INTEGER FK | Equipamiento actual |
| `rune_ids` | INTEGER[] | Runas equipadas |

**Estructura de `dynamic_state` (JSONB):**
```json
{
  "xp_total": 0,
  "aura_level": 0,
  "energy_current": 100,
  "energy_max": 100,
  "state": "READY",           // READY, ON_MISSION, FALLEN
  "current_guild": "...",
  "last_update": "ISO_TIMESTAMP",
  "mission_history": {},
  "total_missions_completed": 0,
  "death_count": 0,
  "current_mission_id": null,
  "mission_start_time": null,
  "fallen_time": null
}
```

### 3.2 Tabla: `active_missions`

**Ubicacion:** schema.sql:39-58

| Campo | Tipo | Uso en Kindling |
|-------|------|-----------------|
| `mission_key` | VARCHAR(100) PK | wallet_heroId |
| `wallet` | VARCHAR(42) | Propietario |
| `hero_id` | VARCHAR(10) | Token ID del NFT |
| `mission_id` | VARCHAR(10) | Mision activa |
| `start_time` | TIMESTAMP | Inicio de mision |
| `duration_hours` | INTEGER | Duracion |
| `is_party` | BOOLEAN | Mision grupal |

### 3.3 Tabla: `items`

**Ubicacion:** schema.sql:182-195

| Campo | Tipo | Uso en Kindling |
|-------|------|-----------------|
| `id` | SERIAL PK | ID del item |
| `name` | VARCHAR(255) | Nombre |
| `type` | VARCHAR(50) | weapon/armor/helmet/accessory/amulet/rune |
| `rarity` | VARCHAR(50) | common/uncommon/rare/epic/legendary |
| `stats` | JSONB | Bonificaciones del item |
| `equipped_by` | VARCHAR(10) | NFT que lo equipa |
| `owner_wallet` | VARCHAR(42) | Wallet propietaria |

### 3.4 Tabla: `user_balances`

**Ubicacion:** schema.sql:228-250

| Campo | Tipo | Uso en Kindling |
|-------|------|-----------------|
| `wallet` | VARCHAR(42) PK | Wallet |
| `ember_balance` | INTEGER | Balance $EMBER pendiente |
| `ash_balance` | INTEGER | Balance $ASH |
| `gambit_rolls_today` | INTEGER | Rolls diarios usados |
| `total_ember_claimed` | NUMERIC | Total reclamado |
| `total_ember_burned` | BIGINT | Total quemado |

### 3.5 Tabla: `pending_claims`

**Ubicacion:** app.py:6532-6550

| Campo | Tipo | Uso en Kindling |
|-------|------|-----------------|
| `id` | SERIAL PK | ID del claim |
| `wallet_address` | VARCHAR(42) | Wallet |
| `claim_type` | VARCHAR(10) | RUNE/ITEM |
| `claim_id` | VARCHAR(66) | Hash unico |
| `signature` | TEXT | Firma del backend |
| `status` | VARCHAR(20) | pending/claimed/expired |

### 3.6 Tabla: `achievements`

**Ubicacion:** schema.sql:103-116

| Campo | Tipo | Uso en Kindling |
|-------|------|-----------------|
| `token_id` | VARCHAR(10) | NFT |
| `achievement_id` | VARCHAR(100) | ID del logro |
| `granted_at` | TIMESTAMP | Cuando se otorgo |

---

## 4. SISTEMA DE ESTADOS ACTUAL

### 4.1 Diagrama de Estados

```
                    +------------------+
                    |                  |
                    v                  |
    +--------+    START    +------------+
    | READY  |------------>| ON_MISSION |
    +--------+             +------------+
        ^                       |
        |                       | (complete)
        |                       v
        |              +----------------+
        |              | SUCCESS/FAILURE|
        |              +----------------+
        |                    |    |
        +--------------------+    |
        (success/fail)            | (death roll failed)
                                  v
                            +---------+
                            | FALLEN  |
                            +---------+
                                  |
                                  | (revive + $EMBER)
                                  v
                            +--------+
                            | READY  |
                            +--------+
```

### 4.2 Estados Actuales

| Estado | Descripcion | Puede Iniciar Mision | Puede Iniciar Kindling |
|--------|-------------|---------------------|------------------------|
| `READY` | Disponible | SI | SI (propuesto) |
| `ON_MISSION` | En mision principal | NO | NO |
| `FALLEN` | Muerto/Caido | NO | NO |

### 4.3 Nuevo Estado Propuesto

| Estado | Descripcion | Puede Iniciar Mision | Puede Iniciar Kindling |
|--------|-------------|---------------------|------------------------|
| `IN_KINDLING` | En micro-aventura | NO | NO |

### 4.4 Transiciones de Estado

**Actuales (app.py):**
- READY -> ON_MISSION: `start_mission_with_lock()` (line 9648)
- ON_MISSION -> READY: `complete_mission_with_lock()` success (line 5021)
- ON_MISSION -> FALLEN: death roll (line 5223)
- FALLEN -> READY: `revive_emissary()` (line 9214)

**Nuevas para Kindling:**
- READY -> IN_KINDLING: `start_kindling_adventure()`
- IN_KINDLING -> READY: `complete_kindling_adventure()`
- IN_KINDLING -> FALLEN: (NO - Kindling no tiene permadeath)

---

## 5. NUEVAS TABLAS NECESARIAS

### 5.1 Tabla: `kindling_adventures` (Definicion de Aventuras)

```sql
CREATE TABLE kindling_adventures (
    id SERIAL PRIMARY KEY,
    adventure_id VARCHAR(20) UNIQUE NOT NULL,  -- "K001", "K002", etc.
    name VARCHAR(255) NOT NULL,
    description TEXT,
    difficulty VARCHAR(20) NOT NULL,           -- "EMBER", "FLAME", "INFERNO"

    -- Estructura narrativa
    story_nodes JSONB NOT NULL,                -- Arbol de decisiones
    total_nodes INTEGER NOT NULL,              -- Numero de nodos
    estimated_duration_minutes INTEGER,        -- Duracion estimada

    -- Requisitos
    min_level INTEGER DEFAULT 1,
    required_guild VARCHAR(100),               -- NULL = cualquier guild
    required_class VARCHAR(100),               -- NULL = cualquier clase
    energy_cost INTEGER DEFAULT 0,             -- 0 para Kindling base

    -- Rewards base
    base_xp_reward INTEGER NOT NULL,
    base_aura_reward INTEGER NOT NULL,
    ember_spark_reward INTEGER NOT NULL,       -- Sparks (fracciones de $EMBER)

    -- Drop chances (porcentajes)
    item_drop_chance DECIMAL(5,2) DEFAULT 0,
    rune_drop_chance DECIMAL(5,2) DEFAULT 0,

    -- Disponibilidad
    is_daily BOOLEAN DEFAULT FALSE,            -- Aventura diaria rotativa
    available_from TIMESTAMP,
    available_until TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indices
CREATE INDEX idx_kindling_adventures_active ON kindling_adventures(is_active);
CREATE INDEX idx_kindling_adventures_daily ON kindling_adventures(is_daily);
CREATE INDEX idx_kindling_adventures_difficulty ON kindling_adventures(difficulty);
```

### 5.2 Tabla: `kindling_sessions` (Sesiones en Progreso)

```sql
CREATE TABLE kindling_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(66) UNIQUE NOT NULL,    -- UUID o hash unico

    -- Participante
    wallet VARCHAR(42) NOT NULL,
    token_id VARCHAR(10) NOT NULL,

    -- Aventura
    adventure_id VARCHAR(20) NOT NULL REFERENCES kindling_adventures(adventure_id),

    -- Estado de la sesion
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, completed, abandoned
    current_node INTEGER NOT NULL DEFAULT 0,
    choices_made JSONB DEFAULT '[]'::jsonb,    -- Array de decisiones tomadas
    path_taken TEXT[],                         -- Secuencia de nodos visitados

    -- Tracking temporal
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_action_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,             -- TTL para auto-liberacion

    -- Resultados (se llenan al completar)
    outcome VARCHAR(20),                       -- SUCCESS, PARTIAL, FAILED
    xp_earned INTEGER DEFAULT 0,
    aura_earned INTEGER DEFAULT 0,
    sparks_earned INTEGER DEFAULT 0,
    items_dropped JSONB DEFAULT '[]'::jsonb,
    runes_dropped JSONB DEFAULT '[]'::jsonb,

    -- Lock info
    lock_acquired_at TIMESTAMP,
    lock_source VARCHAR(20) DEFAULT 'KINDLING',

    CONSTRAINT fk_kindling_session_nft FOREIGN KEY (token_id) REFERENCES nfts(token_id),
    CONSTRAINT fk_kindling_session_adventure FOREIGN KEY (adventure_id)
        REFERENCES kindling_adventures(adventure_id)
);

-- Indices criticos
CREATE INDEX idx_kindling_sessions_wallet ON kindling_sessions(wallet);
CREATE INDEX idx_kindling_sessions_token ON kindling_sessions(token_id);
CREATE INDEX idx_kindling_sessions_status ON kindling_sessions(status);
CREATE INDEX idx_kindling_sessions_expires ON kindling_sessions(expires_at);
CREATE UNIQUE INDEX idx_kindling_sessions_active_token
    ON kindling_sessions(token_id) WHERE status = 'active';  -- Solo 1 sesion activa por NFT
```

### 5.3 Tabla: `kindling_achievements` (Logros de Kindling)

```sql
CREATE TABLE kindling_achievements (
    id SERIAL PRIMARY KEY,
    token_id VARCHAR(10) NOT NULL,
    achievement_id VARCHAR(100) NOT NULL,
    achievement_type VARCHAR(50) NOT NULL,     -- story, collection, streak, special

    -- Metadata del logro
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rarity VARCHAR(20) DEFAULT 'common',       -- common, rare, epic, legendary

    -- Cuando se obtuvo
    adventure_id VARCHAR(20),                  -- NULL para logros meta
    session_id VARCHAR(66),
    earned_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Para sharing en Farcaster
    share_image_url TEXT,
    share_message TEXT,
    farcaster_cast_hash VARCHAR(66),           -- Si ya se compartio

    PRIMARY KEY (token_id, achievement_id),
    CONSTRAINT fk_kindling_achievement_nft FOREIGN KEY (token_id) REFERENCES nfts(token_id)
);

-- Indices
CREATE INDEX idx_kindling_achievements_token ON kindling_achievements(token_id);
CREATE INDEX idx_kindling_achievements_type ON kindling_achievements(achievement_type);
CREATE INDEX idx_kindling_achievements_rarity ON kindling_achievements(rarity);
```

### 5.4 Tabla: `vigil_streaks` (Sistema de Rachas Diarias)

```sql
CREATE TABLE vigil_streaks (
    wallet VARCHAR(42) PRIMARY KEY,

    -- Racha actual
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,

    -- Check-in tracking
    last_checkin_date DATE,
    last_checkin_at TIMESTAMP,
    total_checkins INTEGER DEFAULT 0,

    -- Rewards acumulados por rachas
    streak_sparks_earned INTEGER DEFAULT 0,
    streak_bonuses_claimed JSONB DEFAULT '[]'::jsonb,

    -- Tokens usados en vigil (uno por dia max)
    tokens_used_today JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Para consultas de leaderboard
CREATE INDEX idx_vigil_streaks_current ON vigil_streaks(current_streak DESC);
CREATE INDEX idx_vigil_streaks_longest ON vigil_streaks(longest_streak DESC);
```

### 5.5 Tabla: `ember_kindling_vault` (Vault de Sparks)

```sql
CREATE TABLE ember_kindling_vault (
    wallet VARCHAR(42) PRIMARY KEY,

    -- Sparks acumulados (1000 sparks = 1 $EMBER)
    sparks_balance INTEGER DEFAULT 0,
    sparks_lifetime_earned INTEGER DEFAULT 0,

    -- Conversion a $EMBER
    ember_claimed_from_sparks NUMERIC(18,8) DEFAULT 0,
    last_claim_at TIMESTAMP,

    -- Tracking por fuente
    sparks_from_adventures INTEGER DEFAULT 0,
    sparks_from_vigil INTEGER DEFAULT 0,
    sparks_from_achievements INTEGER DEFAULT 0,
    sparks_from_bonuses INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Para claims
CREATE INDEX idx_ember_vault_balance ON ember_kindling_vault(sparks_balance)
    WHERE sparks_balance >= 1000;
```

### 5.6 Tabla: `nft_activity_locks` (Locks Cross-App)

```sql
CREATE TABLE nft_activity_locks (
    token_id VARCHAR(10) PRIMARY KEY,

    -- Estado del lock
    is_locked BOOLEAN DEFAULT FALSE,
    locked_by VARCHAR(20),                     -- 'MAIN_GAME', 'KINDLING', 'MAINTENANCE'
    lock_type VARCHAR(50),                     -- 'mission', 'adventure', 'equipment', etc.
    lock_reason TEXT,

    -- Referencias
    lock_reference_id VARCHAR(100),            -- mission_key o session_id
    lock_reference_table VARCHAR(50),          -- 'active_missions' o 'kindling_sessions'

    -- Timing
    locked_at TIMESTAMP,
    expires_at TIMESTAMP,                      -- TTL para auto-liberacion

    -- Fallback info
    last_known_wallet VARCHAR(42),

    CONSTRAINT fk_activity_lock_nft FOREIGN KEY (token_id) REFERENCES nfts(token_id)
);

-- Indices
CREATE INDEX idx_activity_locks_locked ON nft_activity_locks(is_locked) WHERE is_locked = TRUE;
CREATE INDEX idx_activity_locks_expires ON nft_activity_locks(expires_at) WHERE is_locked = TRUE;
CREATE INDEX idx_activity_locks_source ON nft_activity_locks(locked_by);
```

---

## 6. NUEVOS ENDPOINTS NECESARIOS

### 6.1 Endpoints de Aventuras

```
POST /api/kindling/start-adventure
    Body: { wallet, token_id, adventure_id }
    Response: {
        success, session_id, adventure_name,
        current_node, story_text, choices[],
        estimated_duration, expires_at
    }
    Rate Limit: 10/min

POST /api/kindling/make-choice
    Body: { wallet, session_id, choice_index }
    Response: {
        success, current_node, story_text, choices[],
        is_final_node, outcome_preview
    }
    Rate Limit: 30/min

POST /api/kindling/complete-adventure
    Body: { wallet, session_id }
    Response: {
        success, outcome, xp_earned, aura_earned,
        sparks_earned, drops[], achievements_granted[],
        share_card_url
    }
    Rate Limit: 10/min

POST /api/kindling/abandon-adventure
    Body: { wallet, session_id }
    Response: { success, token_id, refund_info }
    Rate Limit: 5/min
```

### 6.2 Endpoints de Aventuras Diarias

```
GET /api/kindling/daily-adventures
    Query: ?wallet=0x...
    Response: {
        adventures[],
        daily_reset_at,
        adventures_completed_today,
        vigil_bonus_active
    }
    Rate Limit: 30/min

GET /api/kindling/adventure/<adventure_id>
    Response: {
        adventure_details, requirements,
        rewards_preview, completion_stats
    }
    Rate Limit: 60/min
```

### 6.3 Endpoints de Vigil (Check-in Diario)

```
POST /api/kindling/vigil-checkin
    Body: { wallet, token_id }
    Response: {
        success, current_streak, sparks_earned,
        streak_bonus, next_milestone,
        tokens_used_today
    }
    Rate Limit: 5/min (1 check-in real por dia)

GET /api/kindling/vigil-status
    Query: ?wallet=0x...
    Response: {
        current_streak, longest_streak,
        last_checkin, can_checkin_today,
        available_tokens[], streak_rewards_pending
    }
    Rate Limit: 30/min
```

### 6.4 Endpoints de Vault/Sparks

```
GET /api/kindling/vault-status
    Query: ?wallet=0x...
    Response: {
        sparks_balance, ember_equivalent,
        can_claim, min_claim_sparks,
        lifetime_stats
    }
    Rate Limit: 30/min

POST /api/kindling/claim-ember
    Body: { wallet, sparks_amount }
    Response: {
        success, ember_claimed, sparks_remaining,
        tx_hash
    }
    Rate Limit: 5/min
```

### 6.5 Endpoints de Logros y Sharing

```
GET /api/kindling/achievements/<token_id>
    Response: {
        achievements[],
        total_count,
        by_rarity,
        recent[]
    }
    Rate Limit: 30/min

GET /api/kindling/share-card/<token_id>/<achievement_id>
    Response: {
        image_url,
        share_text,
        farcaster_intent_url,
        og_metadata
    }
    Rate Limit: 60/min

POST /api/kindling/record-share
    Body: { wallet, token_id, achievement_id, platform, cast_hash }
    Response: { success, bonus_sparks }
    Rate Limit: 10/min
```

### 6.6 Endpoints de Estado/Sync

```
GET /api/kindling/nft-status/<token_id>
    Response: {
        available_for_kindling,
        current_lock,
        lock_expires_at,
        active_session
    }
    Rate Limit: 60/min

GET /api/kindling/session/<session_id>
    Response: {
        session_details,
        current_progress,
        time_remaining
    }
    Rate Limit: 30/min

POST /api/kindling/heartbeat
    Body: { session_id }
    Response: { success, expires_at }
    Rate Limit: 60/min (para mantener sesion activa)
```

---

## 7. MODIFICACIONES REQUERIDAS

### 7.1 Modificacion a `dynamic_state` del NFT

**Archivo:** app.py (lineas 3340-3359, 6189-6208)

**Cambios:**
```python
# Agregar nuevo estado valido
VALID_STATES = ["READY", "ON_MISSION", "FALLEN", "IN_KINDLING"]  # Nuevo

# Agregar campos a dynamic_state
"kindling_session_id": None,      # ID de sesion Kindling activa
"kindling_started_at": None,      # Timestamp inicio
"last_kindling_adventure": None,  # Ultimo adventure_id completado
"kindling_adventures_completed": 0,  # Contador total
```

### 7.2 Modificacion al Sistema de Locks

**Archivo:** app.py (lineas 9265-9376)

**Nueva funcion:**
```python
def acquire_cross_app_lock(cursor, token_id, wallet, lock_source, lock_type, ttl_hours=24):
    """
    Adquiere lock cross-app con TTL automatico.

    Args:
        lock_source: 'MAIN_GAME' o 'KINDLING'
        lock_type: 'mission', 'adventure', 'equipment'
        ttl_hours: Tiempo maximo de lock (default 24h)

    Returns:
        (success, lock_info) o (False, existing_lock_info)
    """
    # 1. Verificar estado actual del NFT
    cursor.execute("""
        SELECT dynamic_state->>'state' as state,
               dynamic_state->>'current_mission_id' as mission_id,
               dynamic_state->>'kindling_session_id' as kindling_id
        FROM nfts
        WHERE token_id = %s AND LOWER(last_known_owner) = %s
        FOR UPDATE NOWAIT
    """, (token_id, wallet.lower()))

    # 2. Verificar tabla de locks
    cursor.execute("""
        SELECT * FROM nft_activity_locks
        WHERE token_id = %s AND is_locked = TRUE
        FOR UPDATE NOWAIT
    """, (token_id,))

    # 3. Si hay lock existente, verificar si expiro
    # 4. Crear nuevo lock con TTL
    # 5. Retornar resultado
```

### 7.3 Modificacion a Validacion de Misiones

**Archivo:** app.py (linea 9680-9684)

**Cambio:**
```python
# Antes:
if ds.get('state') == 'FALLEN':
    return {'error': 'hero_fallen', ...}, 400
if ds.get('state') == 'ON_MISSION':
    return {'error': 'already_on_mission', ...}, 400

# Despues:
if ds.get('state') == 'FALLEN':
    return {'error': 'hero_fallen', ...}, 400
if ds.get('state') == 'ON_MISSION':
    return {'error': 'already_on_mission', ...}, 400
if ds.get('state') == 'IN_KINDLING':  # NUEVO
    return {
        'error': 'hero_in_kindling',
        'error_type': 'locked',
        'message': 'This Emissary is currently on a Kindling adventure. Complete or abandon the adventure first.',
        'kindling_session_id': ds.get('kindling_session_id')
    }, 400
```

### 7.4 Modificacion a CORS

**Archivo:** app.py (lineas 2374-2388)

**Cambio:**
```python
CORS(app,
     origins=[
         "https://www.emberholmportal.xyz",
         "https://emberholmportal.xyz",
         "https://kindling.emberholmportal.xyz",  # NUEVO
         "https://*.farcaster.xyz",                # NUEVO - Mini Apps
         "http://localhost:*",
         "http://127.0.0.1:*"
     ],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Farcaster-Auth"],  # NUEVO header
     expose_headers=["Content-Type"],
     supports_credentials=True,
     resources={r"/api/*": {"origins": origins}})
```

### 7.5 Nuevos Rate Limits

**Archivo:** app.py (agregar despues de linea 105)

```python
KINDLING_RATE_LIMITS = {
    '/api/kindling/start-adventure': 10,
    '/api/kindling/make-choice': 30,
    '/api/kindling/complete-adventure': 10,
    '/api/kindling/abandon-adventure': 5,
    '/api/kindling/daily-adventures': 30,
    '/api/kindling/vigil-checkin': 5,
    '/api/kindling/vigil-status': 30,
    '/api/kindling/vault-status': 30,
    '/api/kindling/claim-ember': 5,
    '/api/kindling/achievements': 30,
    '/api/kindling/share-card': 60,
    '/api/kindling/nft-status': 60,
    '/api/kindling/heartbeat': 60,
}
```

---

## 8. SISTEMA DE LOCKS PROPUESTO

### 8.1 Arquitectura de Lock Cross-App

```
                         +----------------------+
                         |  nft_activity_locks  |
                         |    (tabla central)   |
                         +----------------------+
                                   |
                    +--------------+--------------+
                    |                             |
            +-------v-------+             +-------v-------+
            |   MAIN GAME   |             |   KINDLING    |
            +---------------+             +---------------+
            | active_missions|            | kindling_     |
            |               |            | sessions      |
            +---------------+             +---------------+
                    |                             |
                    v                             v
            +-----------------------------------------------+
            |              dynamic_state (nfts)              |
            | state: READY | ON_MISSION | FALLEN | IN_KINDLING |
            +-----------------------------------------------+
```

### 8.2 Flujo de Adquisicion de Lock

```python
def start_kindling_adventure(wallet, token_id, adventure_id):
    with get_db() as cursor:
        try:
            # 1. Intentar adquirir lock exclusivo
            lock_success, lock_info = acquire_cross_app_lock(
                cursor, token_id, wallet,
                lock_source='KINDLING',
                lock_type='adventure',
                ttl_hours=2  # Aventuras max 2 horas
            )

            if not lock_success:
                return {
                    'error': 'nft_locked',
                    'locked_by': lock_info['locked_by'],
                    'expires_at': lock_info['expires_at'],
                    'message': f"Emissary is currently in {lock_info['lock_type']}"
                }, 423  # HTTP 423 Locked

            # 2. Actualizar dynamic_state
            cursor.execute("""
                UPDATE nfts
                SET dynamic_state = dynamic_state
                    || '{"state": "IN_KINDLING"}'::jsonb
                    || jsonb_build_object('kindling_session_id', %s)
                    || jsonb_build_object('kindling_started_at', %s)
                WHERE token_id = %s
            """, (session_id, now_utc_str(), token_id))

            # 3. Crear sesion de kindling
            cursor.execute("""
                INSERT INTO kindling_sessions (...)
                VALUES (...)
            """)

            cursor.connection.commit()
            return {'success': True, 'session_id': session_id}

        except psycopg2.errors.LockNotAvailable:
            cursor.connection.rollback()
            return {'error': 'concurrent_lock', 'message': 'Try again'}, 409
```

### 8.3 Sistema de TTL Automatico

```python
# Cron job o scheduled task (cada 5 minutos)
def cleanup_expired_locks():
    with get_db() as cursor:
        # 1. Liberar locks expirados
        cursor.execute("""
            UPDATE nft_activity_locks
            SET is_locked = FALSE,
                locked_by = NULL,
                lock_type = NULL,
                lock_reference_id = NULL
            WHERE is_locked = TRUE
              AND expires_at < NOW()
            RETURNING token_id, locked_by, lock_reference_id
        """)
        expired_locks = cursor.fetchall()

        # 2. Limpiar sesiones kindling abandonadas
        for lock in expired_locks:
            if lock['locked_by'] == 'KINDLING':
                cursor.execute("""
                    UPDATE kindling_sessions
                    SET status = 'abandoned'
                    WHERE session_id = %s AND status = 'active'
                """, (lock['lock_reference_id'],))

                # 3. Resetear estado del NFT
                cursor.execute("""
                    UPDATE nfts
                    SET dynamic_state = dynamic_state
                        || '{"state": "READY"}'::jsonb
                        || '{"kindling_session_id": null}'::jsonb
                    WHERE token_id = %s
                      AND dynamic_state->>'state' = 'IN_KINDLING'
                """, (lock['token_id'],))

        cursor.connection.commit()
```

### 8.4 Verificacion Antes de Cualquier Accion

```python
def can_use_nft(token_id, wallet, intended_action):
    """
    Verifica si un NFT puede ser usado para una accion.

    Returns:
        (can_use: bool, reason: str, lock_info: dict)
    """
    with get_db() as cursor:
        # 1. Verificar ownership
        cursor.execute("""
            SELECT last_known_owner, dynamic_state
            FROM nfts WHERE token_id = %s
        """, (token_id,))
        nft = cursor.fetchone()

        if not nft or nft['last_known_owner'].lower() != wallet.lower():
            return (False, 'not_owner', None)

        ds = nft['dynamic_state']
        state = ds.get('state', 'READY')

        # 2. Verificar estado
        if state == 'FALLEN':
            return (False, 'fallen', {'death_count': ds.get('death_count', 0)})

        if state == 'ON_MISSION':
            return (False, 'on_mission', {
                'mission_id': ds.get('current_mission_id'),
                'started_at': ds.get('mission_start_time')
            })

        if state == 'IN_KINDLING':
            return (False, 'in_kindling', {
                'session_id': ds.get('kindling_session_id'),
                'started_at': ds.get('kindling_started_at')
            })

        # 3. Verificar lock en tabla central
        cursor.execute("""
            SELECT * FROM nft_activity_locks
            WHERE token_id = %s AND is_locked = TRUE
        """, (token_id,))
        lock = cursor.fetchone()

        if lock and lock['expires_at'] > datetime.now(timezone.utc):
            return (False, 'locked', {
                'locked_by': lock['locked_by'],
                'lock_type': lock['lock_type'],
                'expires_at': lock['expires_at'].isoformat()
            })

        return (True, 'available', None)
```

---

## 9. CONSIDERACIONES DE SEGURIDAD

### 9.1 Autenticacion para Farcaster Mini Apps

**Problema:** Verificar que el usuario de Farcaster es dueno del NFT.

**Solucion Propuesta:**

```python
# Verificar signature de Farcaster
def verify_farcaster_auth(request):
    """
    Verifica autenticacion de Farcaster Mini App.

    Headers esperados:
    - X-Farcaster-Auth: signature
    - X-Farcaster-FID: farcaster_id
    - X-Farcaster-Timestamp: timestamp
    """
    signature = request.headers.get('X-Farcaster-Auth')
    fid = request.headers.get('X-Farcaster-FID')
    timestamp = request.headers.get('X-Farcaster-Timestamp')

    if not all([signature, fid, timestamp]):
        return None, "Missing Farcaster auth headers"

    # Verificar timestamp (max 5 min)
    ts = int(timestamp)
    if abs(time.time() - ts) > 300:
        return None, "Timestamp expired"

    # Verificar signature (usando SDK de Farcaster)
    # ...

    # Obtener wallets vinculadas al FID
    wallets = get_farcaster_verified_addresses(fid)

    return wallets, None

# Endpoint que usa ambos metodos
@app.route('/api/kindling/start-adventure', methods=['POST'])
def kindling_start():
    data = request.get_json()
    wallet = data.get('wallet')

    # Metodo 1: Wallet directo (para web app)
    if wallet:
        # Verificar ownership via blockchain
        pass

    # Metodo 2: Farcaster auth (para mini app)
    else:
        fc_wallets, error = verify_farcaster_auth(request)
        if error:
            return {'error': 'auth_failed', 'message': error}, 401
        wallet = fc_wallets[0]  # Usar primera wallet verificada

    # Continuar con logica...
```

### 9.2 Rate Limiting Especifico para Mini Apps

```python
# Rate limits mas estrictos para mini apps
MINI_APP_RATE_LIMITS = {
    '/api/kindling/start-adventure': 5,   # vs 10 para web
    '/api/kindling/make-choice': 20,      # vs 30 para web
    '/api/kindling/claim-ember': 2,       # vs 5 para web
}

def get_rate_limit(endpoint, is_mini_app=False):
    if is_mini_app:
        return MINI_APP_RATE_LIMITS.get(endpoint, 10)
    return KINDLING_RATE_LIMITS.get(endpoint, 20)
```

### 9.3 Validacion de Inputs

```python
# Schema de validacion para aventuras
ADVENTURE_SCHEMA = {
    'start': {
        'wallet': {'type': 'string', 'pattern': r'^0x[a-fA-F0-9]{40}$'},
        'token_id': {'type': 'string', 'pattern': r'^\d{1,5}$'},
        'adventure_id': {'type': 'string', 'pattern': r'^K\d{3}$'}
    },
    'choice': {
        'session_id': {'type': 'string', 'minlength': 32, 'maxlength': 66},
        'choice_index': {'type': 'integer', 'min': 0, 'max': 10}
    }
}
```

### 9.4 Prevencion de Exploits

```python
# 1. Verificar que el NFT sigue perteneciendo al wallet
async def verify_current_ownership(token_id, wallet):
    """Verifica ownership on-chain antes de dar rewards."""
    contract = get_nft_contract()
    current_owner = await contract.functions.ownerOf(int(token_id)).call()
    return current_owner.lower() == wallet.lower()

# 2. Rate limit por NFT (no solo por wallet)
def check_nft_rate_limit(token_id, action, limit_per_hour=10):
    key = f"nft_rate:{token_id}:{action}"
    count = redis.incr(key)
    if count == 1:
        redis.expire(key, 3600)
    return count <= limit_per_hour

# 3. Detectar comportamiento sospechoso
def detect_suspicious_patterns(wallet, session_id):
    """Detectar patrones como completar aventuras demasiado rapido."""
    # Tiempo minimo entre choices
    # Patrones de respuesta identicos
    # Multiples sesiones simultaneas desde misma IP
    pass
```

---

## 10. ROADMAP DE IMPLEMENTACION

### Fase 1: Infraestructura Base (Semana 1-2)

1. **Base de Datos**
   - [ ] Crear tabla `nft_activity_locks`
   - [ ] Crear tabla `kindling_adventures`
   - [ ] Crear tabla `kindling_sessions`
   - [ ] Crear indices y constraints

2. **Sistema de Locks**
   - [ ] Implementar `acquire_cross_app_lock()`
   - [ ] Implementar `release_cross_app_lock()`
   - [ ] Implementar cleanup de locks expirados
   - [ ] Tests de concurrencia

3. **Modificaciones al Main Game**
   - [ ] Agregar estado `IN_KINDLING` a validaciones
   - [ ] Actualizar CORS para nuevo dominio
   - [ ] Agregar rate limits para Kindling

### Fase 2: Core de Kindling (Semana 3-4)

4. **Endpoints Basicos**
   - [ ] `POST /api/kindling/start-adventure`
   - [ ] `POST /api/kindling/make-choice`
   - [ ] `POST /api/kindling/complete-adventure`
   - [ ] `POST /api/kindling/abandon-adventure`

5. **Motor de Aventuras**
   - [ ] Parser de story_nodes (JSON)
   - [ ] Logica de transiciones
   - [ ] Calculo de outcomes
   - [ ] Generacion de rewards

6. **Contenido Inicial**
   - [ ] 3 aventuras de prueba (1 por dificultad)
   - [ ] Tests end-to-end

### Fase 3: Economia y Rewards (Semana 5-6)

7. **Sistema de Sparks**
   - [ ] Crear tabla `ember_kindling_vault`
   - [ ] Endpoint `GET /api/kindling/vault-status`
   - [ ] Endpoint `POST /api/kindling/claim-ember`
   - [ ] Integracion con sistema de claims existente

8. **Sistema Vigil**
   - [ ] Crear tabla `vigil_streaks`
   - [ ] Endpoint `POST /api/kindling/vigil-checkin`
   - [ ] Endpoint `GET /api/kindling/vigil-status`
   - [ ] Logica de rachas y bonificaciones

### Fase 4: Logros y Social (Semana 7-8)

9. **Sistema de Achievements**
   - [ ] Crear tabla `kindling_achievements`
   - [ ] Definir achievements iniciales
   - [ ] Endpoint `GET /api/kindling/achievements/<token_id>`

10. **Sharing en Farcaster**
    - [ ] Generador de share cards (imagen)
    - [ ] Endpoint `GET /api/kindling/share-card`
    - [ ] Integracion con Farcaster intents
    - [ ] Tracking de shares

### Fase 5: Mini App Frontend (Semana 9-10)

11. **Autenticacion Farcaster**
    - [ ] Implementar verificacion de signature
    - [ ] Mapeo FID -> wallets
    - [ ] Middleware de auth

12. **UI de Mini App**
    - [ ] Pantalla de seleccion de Emissary
    - [ ] Pantalla de aventura (narrativa + choices)
    - [ ] Pantalla de resultados
    - [ ] Pantalla de vault/vigil

### Fase 6: Testing y Launch (Semana 11-12)

13. **QA Completo**
    - [ ] Tests de integracion
    - [ ] Tests de carga
    - [ ] Audit de seguridad
    - [ ] Beta con usuarios reales

14. **Launch**
    - [ ] Deploy a produccion
    - [ ] Monitoreo inicial
    - [ ] Documentacion final

---

## 11. RIESGOS Y MITIGACIONES

### 11.1 Riesgos Tecnicos

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Race conditions en locks | Media | Alto | Tests de concurrencia exhaustivos, FOR UPDATE NOWAIT |
| Sesiones huerfanas | Media | Medio | TTL automatico, cleanup job cada 5 min |
| Overflow de sparks | Baja | Alto | Usar BIGINT, validar antes de operaciones |
| Fallo de verificacion Farcaster | Media | Medio | Fallback a wallet signature, cache de FID->wallet |

### 11.2 Riesgos de Seguridad

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Replay attacks en claims | Media | Alto | Nonce unico por claim, verificar on-chain |
| Farming automatizado | Alta | Medio | Rate limits por NFT, CAPTCHA en suspicious patterns |
| Robo de NFT durante aventura | Baja | Alto | Verificar ownership antes de rewards |
| XSS en share cards | Baja | Medio | Sanitizar todos los inputs, CSP headers |

### 11.3 Riesgos de UX

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| NFT bloqueado sin poder liberarlo | Media | Alto | UI clara de estado, opcion de abandon |
| Confusion entre apps | Media | Medio | Mensajes claros indicando donde esta el NFT |
| Perdida de progreso | Baja | Alto | Autosave cada choice, recovery endpoint |

### 11.4 Riesgos de Negocio

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Inflacion de $EMBER por sparks | Media | Alto | Cap diario de sparks, ajustar ratios |
| Baja adopcion | Media | Medio | Incentivos iniciales, contenido atractivo |
| Conflicto con main game | Baja | Medio | Balancear rewards, evitar competir por tiempo |

---

## 12. PREGUNTAS PENDIENTES

1. **Economia de Sparks:**
   - Cuantos sparks = 1 $EMBER? (Propuesta: 1000 sparks = 1 $EMBER)
   - Hay cap diario de sparks ganables?
   - Los sparks expiran?

2. **Aventuras Diarias:**
   - Cuantas aventuras diarias hay?
   - Rotan o son las mismas?
   - Hay cooldown entre aventuras?

3. **Sistema Vigil:**
   - Un check-in por wallet o por NFT?
   - Que pasa si se pierde la racha? (propuesta: reset a 0)
   - Hay "streak shields" comprables?

4. **Muerte en Kindling:**
   - Puede morir un NFT en Kindling? (propuesta: NO)
   - Hay consecuencias negativas posibles?

5. **Integracion con Main Game:**
   - Los XP/Aura ganados en Kindling afectan level del NFT?
   - Los items/runas van al vault comun?

6. **Mini App:**
   - Dominio confirmado: kindling.emberholmportal.xyz?
   - Hay diseno UI/UX definido?
   - Soporte offline/PWA?

---

## APENDICE A: CONTRATOS RELEVANTES

```
Base Mainnet (Chain ID: 8453)

EmberholmPortal NFT:    0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3
EmberToken ($EMBER):    0xbA7723fBfb44C7712C0B78108ad873DcFd5Dd73b
AshToken ($ASH):        0xD4eef3eadb1Cf1B2905AA4Cd1022b8cCCC739DAb
EmberItems (ERC-1155):  0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA
EmberRunes (ERC-1155):  0xDa2D1085053c3700645a13498293D17c1cc3f595
Trophies (ERC-1155):    0x99bB074468DF7acED00a7a4960c52c4e22543ab8

Treasury Wallet:        0x31d6E19aAE43B5E2fbeDb01b6FF82AD1e8B576DC
Rewards Wallet:         0xa84C45Eb435732FAe8A017861c07394c3aA7d815
```

## APENDICE B: ARCHIVOS CLAVE MODIFICADOS

| Archivo | Lineas | Cambios |
|---------|--------|---------|
| app.py | 3340-3359 | Agregar campos kindling a dynamic_state |
| app.py | 6189-6208 | Validar nuevo estado IN_KINDLING |
| app.py | 9680-9684 | Bloquear misiones si IN_KINDLING |
| app.py | 2374-2388 | Agregar dominios CORS |
| app.py | 24-105 | Agregar rate limits Kindling |
| schema.sql | EOF | Agregar nuevas tablas |
| database.py | EOF | Agregar funciones para nuevas tablas |

---

*Documento generado automaticamente por analisis de codebase.*
*Requiere validacion antes de proceder con implementacion.*
