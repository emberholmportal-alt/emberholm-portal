# REPORTE DE ANALISIS - EMBERHOLM PORTAL PARA KINDLING

**Fecha:** 2026-01-26
**Version:** 2.0
**Estado:** Decisiones Confirmadas - Pendiente Aprobacion para Implementar

---

## 1. RESUMEN EJECUTIVO

### Que es KINDLING

KINDLING es una mini-app complementaria para Emberholm Portal que funciona en el ecosistema Farcaster/Base. Es un sistema de micro-aventuras estilo "Elige tu propia aventura" donde:

- Los jugadores toman decisiones que afectan el resultado
- Se ganan XP, Aura, $EMBER (via Sparks), Items y Runas
- Los logros se guardan por NFT y son compartibles en Farcaster
- Todo se sincroniza con el juego principal en tiempo real
- Un NFT no puede estar activo en ambos lugares simultaneamente

### Decisiones Confirmadas

| Aspecto | Decision | Detalle |
|---------|----------|---------|
| **Ratio Sparks** | 1000 sparks = 1 $EMBER | Cap diario: 500 sparks |
| **Muerte en Kindling** | NO | NFT nunca pasa a FALLEN desde Kindling |
| **Sincronizacion XP/Aura** | SI | Exito suma, fallo resta XP |
| **Dominio** | Ruta `/kindling` | `emberholmportal.xyz/kindling` |

### Estado del Proyecto Base

Emberholm Portal es un juego NFT maduro con:
- **35,000 NFTs** (Emissaries) en Base Mainnet
- **Sistema de misiones** completo con exito/fallo/muerte
- **Sistema de rewards** (XP, Aura, Items, Runes, $EMBER)
- **Sistema de equipamiento** (5 slots + 2 runas)
- **Sistema de Guilds** (6 guilds con bonificaciones)
- **Sistema de locks** PostgreSQL para prevenir race conditions
- **Backend signer** para claims de drops

### Viabilidad

**VIABLE CON MODIFICACIONES MENORES**

| Componente | Estado | Accion Requerida |
|------------|--------|------------------|
| Sistema de estados NFT | Existe | Agregar estado `IN_KINDLING` |
| Sistema de locks | Existe | Extender para locks cross-app |
| Sistema de rewards | Existe | Reutilizar calculos existentes |
| Backend signing | Existe | Reutilizar para claims |
| Base de datos | PostgreSQL | Agregar 6 tablas nuevas |
| CORS | Configurado | No requiere cambios (mismo origen) |
| Rate limiting | Existe | Agregar endpoints nuevos |

---

## 2. ENDPOINTS EXISTENTES REUTILIZABLES

### 2.1 Endpoints de NFTs/Emissaries

| Endpoint | Metodo | Uso en Kindling | Referencia |
|----------|--------|-----------------|------------|
| `/api/player/<wallet>` | GET | Obtener lista de NFTs disponibles | app.py:3541 |
| `/api/player/<wallet>` | POST | Sincronizar NFTs al backend | app.py:3541 |
| `/api/metadata/<token_id>` | GET | Obtener estado completo del NFT | app.py:6047 |
| `/api/equipment/<emissary_id>` | GET | Ver equipo del NFT (para bonos) | app.py:8127 |

### 2.2 Endpoints de Balance/Economia

| Endpoint | Metodo | Uso en Kindling | Referencia |
|----------|--------|-----------------|------------|
| `/api/balance?wallet=` | GET | Consultar balance $EMBER | inventory.js:383 |
| `/api/ember/balance/<wallet>` | GET | Balance on-chain | app.py:7630 |

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

**Estructura de `dynamic_state` (JSONB) - Actual:**
```json
{
  "xp_total": 0,
  "aura_level": 0,
  "energy_current": 100,
  "energy_max": 100,
  "state": "READY",
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

**Campos NUEVOS a agregar para Kindling:**
```json
{
  "kindling_session_id": null,
  "kindling_started_at": null,
  "last_kindling_adventure": null,
  "kindling_adventures_completed": 0
}
```

### 3.2 Tabla: `active_missions`

| Campo | Tipo | Uso en Kindling |
|-------|------|-----------------|
| `mission_key` | VARCHAR(100) PK | wallet_heroId |
| `wallet` | VARCHAR(42) | Propietario |
| `hero_id` | VARCHAR(10) | Token ID del NFT |
| `mission_id` | VARCHAR(10) | Mision activa |
| `start_time` | TIMESTAMP | Inicio de mision |
| `duration_hours` | INTEGER | Duracion |

### 3.3 Tabla: `items`

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

| Campo | Tipo | Uso en Kindling |
|-------|------|-----------------|
| `wallet` | VARCHAR(42) PK | Wallet |
| `ember_balance` | INTEGER | Balance $EMBER pendiente |
| `ash_balance` | INTEGER | Balance $ASH |
| `total_ember_claimed` | NUMERIC | Total reclamado |

### 3.5 Tabla: `pending_claims`

| Campo | Tipo | Uso en Kindling |
|-------|------|-----------------|
| `id` | SERIAL PK | ID del claim |
| `wallet_address` | VARCHAR(42) | Wallet |
| `claim_type` | VARCHAR(10) | RUNE/ITEM |
| `claim_id` | VARCHAR(66) | Hash unico |
| `signature` | TEXT | Firma del backend |
| `status` | VARCHAR(20) | pending/claimed/expired |

### 3.6 Tabla: `achievements`

| Campo | Tipo | Uso en Kindling |
|-------|------|-----------------|
| `token_id` | VARCHAR(10) | NFT |
| `achievement_id` | VARCHAR(100) | ID del logro |
| `granted_at` | TIMESTAMP | Cuando se otorgo |

---

## 4. SISTEMA DE ESTADOS

### 4.1 Diagrama de Estados (Actualizado con Kindling)

```
                                    MAIN GAME
                    +----------------------------------------+
                    |                                        |
                    v                                        |
    +--------+    START    +------------+                    |
    | READY  |------------>| ON_MISSION |                    |
    +--------+             +------------+                    |
        |  ^                     |                           |
        |  |                     | (complete)                |
        |  |                     v                           |
        |  |            +----------------+                   |
        |  |            | SUCCESS/FAILURE|                   |
        |  |            +----------------+                   |
        |  |                  |    |                         |
        |  +------------------+    |                         |
        |  (success/fail)         | (death roll failed)     |
        |                         v                          |
        |                   +---------+                      |
        |                   | FALLEN  |-----(revive)--------+
        |                   +---------+
        |
        |                      KINDLING
        |   +--------------------------------------------+
        |   |                                            |
        v   v                                            |
    +-------------+                                      |
    | IN_KINDLING |------(complete/abandon)-------------+
    +-------------+
         ^
         |
    (start adventure)
         |
    +--------+
    | READY  |
    +--------+
```

### 4.2 Estados y Transiciones

| Estado | Descripcion | Puede Main Game | Puede Kindling |
|--------|-------------|-----------------|----------------|
| `READY` | Disponible | SI | SI |
| `ON_MISSION` | En mision principal | NO | NO |
| `FALLEN` | Muerto/Caido | NO (requiere revive) | NO |
| `IN_KINDLING` | En micro-aventura | NO | NO (ya esta) |

### 4.3 Transiciones Permitidas

**Desde Main Game:**
- `READY` → `ON_MISSION`: Iniciar mision
- `ON_MISSION` → `READY`: Completar mision (exito o fallo sin muerte)
- `ON_MISSION` → `FALLEN`: Muerte en mision
- `FALLEN` → `READY`: Revive con $EMBER

**Desde Kindling:**
- `READY` → `IN_KINDLING`: Iniciar aventura
- `IN_KINDLING` → `READY`: Completar o abandonar aventura
- `IN_KINDLING` → `FALLEN`: **NO PERMITIDO** (decision confirmada)

---

## 5. ECONOMIA DE KINDLING

### 5.1 Sistema de Sparks

**Ratio confirmado:** 1000 sparks = 1 $EMBER

**Cap diario:** 500 sparks maximo por wallet

### 5.2 Fuentes de Sparks

| Fuente | Sparks | Frecuencia | Notas |
|--------|--------|------------|-------|
| Aventura EMBER (facil) | 50-100 | Ilimitada | Base segun outcome |
| Aventura FLAME (media) | 100-200 | Ilimitada | Base segun outcome |
| Aventura INFERNO (dificil) | 200-400 | Ilimitada | Base segun outcome |
| Vigil check-in | 50 | 1/dia | Por NFT |
| Racha Vigil 7 dias | +100 bonus | Semanal | Acumulativo |
| Racha Vigil 30 dias | +500 bonus | Mensual | Acumulativo |
| Achievement comun | 100 | One-time | Por logro |
| Achievement raro | 250 | One-time | Por logro |
| Achievement epico | 500 | One-time | Por logro |

### 5.3 Proyeccion de Ganancias

| Tipo Jugador | Actividad | Sparks/Semana | $EMBER/Semana |
|--------------|-----------|---------------|---------------|
| Casual | 1-2 aventuras/dia | ~700-1000 | ~0.7-1 |
| Regular | 3-4 aventuras/dia + vigil | ~2000-2500 | ~2-2.5 |
| Activo | 5+ aventuras/dia + vigil | ~3500 (cap) | ~3.5 |

*Nota: Cap diario de 500 sparks limita el farming excesivo*

### 5.4 Sincronizacion con Main Game

**XP:**
- Exito en aventura: `+XP` (se suma al total del NFT)
- Fallo en aventura: `-XP` (se resta, minimo 0)

**Aura:**
- Exito en aventura: `+Aura` (se suma al nivel)
- Fallo en aventura: Sin penalizacion de Aura

**Items/Runas:**
- Drops van al vault comun del wallet
- Mismo sistema de claim con firma

---

## 6. NUEVAS TABLAS NECESARIAS

### 6.1 Tabla: `kindling_adventures`

```sql
-- Definicion de aventuras disponibles
CREATE TABLE kindling_adventures (
    id SERIAL PRIMARY KEY,
    adventure_id VARCHAR(20) UNIQUE NOT NULL,  -- "K001", "K002", etc.
    name VARCHAR(255) NOT NULL,
    description TEXT,
    difficulty VARCHAR(20) NOT NULL,           -- "EMBER", "FLAME", "INFERNO"

    -- Estructura narrativa (arbol de decisiones)
    story_nodes JSONB NOT NULL,
    total_nodes INTEGER NOT NULL,
    estimated_duration_minutes INTEGER DEFAULT 5,

    -- Requisitos
    min_level INTEGER DEFAULT 1,
    required_guild VARCHAR(100),               -- NULL = cualquier guild
    required_class VARCHAR(100),               -- NULL = cualquier clase

    -- Rewards base
    base_xp_reward INTEGER NOT NULL,
    base_aura_reward INTEGER NOT NULL,
    base_sparks_min INTEGER NOT NULL,
    base_sparks_max INTEGER NOT NULL,

    -- Penalizacion por fallo
    xp_loss_on_fail INTEGER DEFAULT 0,

    -- Drop chances (porcentajes)
    item_drop_chance DECIMAL(5,2) DEFAULT 0,
    rune_drop_chance DECIMAL(5,2) DEFAULT 0,

    -- Disponibilidad
    is_daily BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_kindling_adventures_active ON kindling_adventures(is_active);
CREATE INDEX idx_kindling_adventures_difficulty ON kindling_adventures(difficulty);
```

**Estructura de `story_nodes` (JSONB):**
```json
{
  "0": {
    "text": "Te encuentras en la entrada de una cueva oscura...",
    "choices": [
      {"text": "Entrar con antorcha", "next_node": 1, "success_modifier": 0.1},
      {"text": "Entrar sigilosamente", "next_node": 2, "success_modifier": -0.1},
      {"text": "Buscar otra entrada", "next_node": 3, "success_modifier": 0}
    ]
  },
  "1": {
    "text": "La luz revela un tesoro, pero tambien despierta...",
    "choices": [...]
  },
  "final_success": {
    "text": "Has completado la aventura con exito!",
    "outcome": "SUCCESS",
    "bonus_multiplier": 1.0
  },
  "final_fail": {
    "text": "La aventura no salio como esperabas...",
    "outcome": "FAIL",
    "bonus_multiplier": 0
  }
}
```

### 6.2 Tabla: `kindling_sessions`

```sql
-- Sesiones de aventura en progreso
CREATE TABLE kindling_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(66) UNIQUE NOT NULL,    -- UUID

    -- Participante
    wallet VARCHAR(42) NOT NULL,
    token_id VARCHAR(10) NOT NULL,

    -- Aventura
    adventure_id VARCHAR(20) NOT NULL,

    -- Estado de la sesion
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, completed, abandoned
    current_node INTEGER NOT NULL DEFAULT 0,
    choices_made JSONB DEFAULT '[]'::jsonb,
    path_taken TEXT[] DEFAULT '{}',

    -- Modificadores acumulados por decisiones
    cumulative_success_modifier DECIMAL(5,2) DEFAULT 0,

    -- Tracking temporal
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_action_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,             -- TTL: 2 horas desde inicio

    -- Resultados (se llenan al completar)
    outcome VARCHAR(20),                       -- SUCCESS, FAIL
    xp_earned INTEGER DEFAULT 0,
    xp_lost INTEGER DEFAULT 0,
    aura_earned INTEGER DEFAULT 0,
    sparks_earned INTEGER DEFAULT 0,
    items_dropped JSONB DEFAULT '[]'::jsonb,
    runes_dropped JSONB DEFAULT '[]'::jsonb,

    CONSTRAINT fk_kindling_session_adventure
        FOREIGN KEY (adventure_id) REFERENCES kindling_adventures(adventure_id)
);

-- Solo 1 sesion activa por NFT
CREATE UNIQUE INDEX idx_kindling_sessions_active_token
    ON kindling_sessions(token_id) WHERE status = 'active';
CREATE INDEX idx_kindling_sessions_wallet ON kindling_sessions(wallet);
CREATE INDEX idx_kindling_sessions_expires ON kindling_sessions(expires_at)
    WHERE status = 'active';
```

### 6.3 Tabla: `kindling_achievements`

```sql
-- Logros obtenidos en Kindling
CREATE TABLE kindling_achievements (
    id SERIAL PRIMARY KEY,
    token_id VARCHAR(10) NOT NULL,
    achievement_id VARCHAR(100) NOT NULL,
    achievement_type VARCHAR(50) NOT NULL,     -- story, collection, streak, exploration

    -- Metadata del logro
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rarity VARCHAR(20) DEFAULT 'common',       -- common, rare, epic, legendary
    sparks_reward INTEGER DEFAULT 0,

    -- Contexto de obtencion
    adventure_id VARCHAR(20),
    session_id VARCHAR(66),
    earned_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Para sharing en Farcaster
    share_image_url TEXT,
    share_text TEXT,
    farcaster_cast_hash VARCHAR(66),
    shared_at TIMESTAMP,

    CONSTRAINT pk_kindling_achievement PRIMARY KEY (token_id, achievement_id)
);

CREATE INDEX idx_kindling_achievements_token ON kindling_achievements(token_id);
CREATE INDEX idx_kindling_achievements_rarity ON kindling_achievements(rarity);
```

### 6.4 Tabla: `vigil_streaks`

```sql
-- Sistema de check-in diario
CREATE TABLE vigil_streaks (
    wallet VARCHAR(42) PRIMARY KEY,

    -- Racha actual
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,

    -- Check-in tracking
    last_checkin_date DATE,
    last_checkin_at TIMESTAMP,
    last_checkin_token_id VARCHAR(10),
    total_checkins INTEGER DEFAULT 0,

    -- Rewards acumulados
    total_sparks_from_vigil INTEGER DEFAULT 0,

    -- Tokens usados hoy (max 1 por dia)
    today_date DATE,
    token_used_today VARCHAR(10),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_vigil_streaks_current ON vigil_streaks(current_streak DESC);
```

### 6.5 Tabla: `ember_kindling_vault`

```sql
-- Vault de Sparks por wallet
CREATE TABLE ember_kindling_vault (
    wallet VARCHAR(42) PRIMARY KEY,

    -- Balance actual (1000 sparks = 1 $EMBER)
    sparks_balance INTEGER DEFAULT 0,
    sparks_earned_today INTEGER DEFAULT 0,
    today_date DATE,

    -- Estadisticas lifetime
    sparks_lifetime_earned INTEGER DEFAULT 0,
    ember_claimed_total NUMERIC(18,8) DEFAULT 0,

    -- Tracking por fuente
    sparks_from_adventures INTEGER DEFAULT 0,
    sparks_from_vigil INTEGER DEFAULT 0,
    sparks_from_achievements INTEGER DEFAULT 0,

    -- Ultimo claim
    last_claim_at TIMESTAMP,
    last_claim_amount NUMERIC(18,8),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ember_vault_claimable ON ember_kindling_vault(sparks_balance)
    WHERE sparks_balance >= 1000;
```

### 6.6 Tabla: `nft_activity_locks`

```sql
-- Locks centralizados cross-app
CREATE TABLE nft_activity_locks (
    token_id VARCHAR(10) PRIMARY KEY,

    -- Estado del lock
    is_locked BOOLEAN DEFAULT FALSE,
    locked_by VARCHAR(20),                     -- 'MAIN_GAME' o 'KINDLING'
    lock_type VARCHAR(50),                     -- 'mission', 'adventure'

    -- Referencia al registro que tiene el lock
    lock_reference_id VARCHAR(100),            -- mission_key o session_id

    -- Timing con TTL
    locked_at TIMESTAMP,
    expires_at TIMESTAMP,                      -- Auto-release despues de esto

    -- Info del wallet
    locked_by_wallet VARCHAR(42)
);

CREATE INDEX idx_activity_locks_active ON nft_activity_locks(is_locked)
    WHERE is_locked = TRUE;
CREATE INDEX idx_activity_locks_expires ON nft_activity_locks(expires_at)
    WHERE is_locked = TRUE;
```

---

## 7. NUEVOS ENDPOINTS

### 7.1 Endpoints de Aventuras

```
POST /api/kindling/start-adventure
    Body: {
        "wallet": "0x...",
        "token_id": "00001",
        "adventure_id": "K001"
    }
    Response: {
        "success": true,
        "session_id": "uuid",
        "adventure_name": "La Cueva del Dragon",
        "difficulty": "FLAME",
        "current_node": 0,
        "story_text": "Te encuentras en...",
        "choices": [
            {"index": 0, "text": "Entrar con antorcha"},
            {"index": 1, "text": "Entrar sigilosamente"}
        ],
        "expires_at": "2026-01-26T14:00:00Z"
    }
    Errors: 400 (invalid_input), 403 (not_owner), 423 (nft_locked)
    Rate Limit: 10/min

POST /api/kindling/make-choice
    Body: {
        "wallet": "0x...",
        "session_id": "uuid",
        "choice_index": 0
    }
    Response: {
        "success": true,
        "current_node": 1,
        "story_text": "La luz revela...",
        "choices": [...],
        "is_final": false
    }
    // Si is_final = true:
    Response: {
        "success": true,
        "is_final": true,
        "outcome": "SUCCESS",
        "story_text": "Has completado...",
        "rewards_preview": {
            "xp": 150,
            "aura": 10,
            "sparks": 180,
            "drops": []
        }
    }
    Rate Limit: 30/min

POST /api/kindling/complete-adventure
    Body: {
        "wallet": "0x...",
        "session_id": "uuid"
    }
    Response: {
        "success": true,
        "outcome": "SUCCESS",
        "xp_earned": 150,
        "aura_earned": 10,
        "sparks_earned": 180,
        "new_xp_total": 1500,
        "new_aura_level": 5,
        "drops": [
            {"type": "item", "id": "item-123", "name": "Espada de Fuego"}
        ],
        "achievements_granted": [
            {"id": "first_flame", "name": "Primera Llama", "sparks": 100}
        ],
        "daily_sparks_remaining": 320
    }
    // Si outcome = FAIL:
    Response: {
        "success": true,
        "outcome": "FAIL",
        "xp_lost": 50,
        "new_xp_total": 1450,
        "sparks_earned": 0,
        "daily_sparks_remaining": 500
    }
    Rate Limit: 10/min

POST /api/kindling/abandon-adventure
    Body: {
        "wallet": "0x...",
        "session_id": "uuid"
    }
    Response: {
        "success": true,
        "token_id": "00001",
        "message": "Adventure abandoned. No rewards or penalties."
    }
    Rate Limit: 5/min
```

### 7.2 Endpoints de Aventuras Disponibles

```
GET /api/kindling/adventures
    Query: ?wallet=0x...
    Response: {
        "adventures": [
            {
                "adventure_id": "K001",
                "name": "La Cueva del Dragon",
                "difficulty": "FLAME",
                "description": "Una misteriosa cueva...",
                "estimated_minutes": 5,
                "rewards": {
                    "xp_range": [100, 200],
                    "aura_range": [5, 15],
                    "sparks_range": [100, 200]
                },
                "requirements": {
                    "min_level": 1,
                    "guild": null,
                    "class": null
                }
            }
        ],
        "daily_sparks_earned": 180,
        "daily_sparks_cap": 500,
        "daily_sparks_remaining": 320
    }
    Rate Limit: 30/min

GET /api/kindling/adventure/<adventure_id>
    Response: {
        "adventure_id": "K001",
        "name": "La Cueva del Dragon",
        "difficulty": "FLAME",
        "description": "Una misteriosa cueva...",
        "full_description": "Hace siglos, un dragon...",
        "estimated_minutes": 5,
        "total_nodes": 12,
        "possible_endings": 4,
        "rewards": {...},
        "requirements": {...},
        "completion_stats": {
            "total_attempts": 1523,
            "success_rate": 0.67,
            "avg_completion_time_minutes": 4.2
        }
    }
    Rate Limit: 60/min
```

### 7.3 Endpoints de Vigil

```
POST /api/kindling/vigil-checkin
    Body: {
        "wallet": "0x...",
        "token_id": "00001"
    }
    Response: {
        "success": true,
        "current_streak": 8,
        "sparks_earned": 50,
        "streak_bonus": 0,
        "next_bonus_at_streak": 30,
        "next_bonus_amount": 500,
        "message": "Day 8! Keep the flame alive!"
    }
    Errors: 400 (already_checked_in_today), 403 (not_owner)
    Rate Limit: 5/min

GET /api/kindling/vigil-status
    Query: ?wallet=0x...
    Response: {
        "current_streak": 8,
        "longest_streak": 15,
        "last_checkin": "2026-01-25",
        "can_checkin_today": true,
        "token_used_today": null,
        "available_tokens": ["00001", "00002", "00003"],
        "total_sparks_from_vigil": 450,
        "streak_milestones": [
            {"days": 7, "bonus": 100, "reached": true},
            {"days": 30, "bonus": 500, "reached": false}
        ]
    }
    Rate Limit: 30/min
```

### 7.4 Endpoints de Vault

```
GET /api/kindling/vault-status
    Query: ?wallet=0x...
    Response: {
        "sparks_balance": 2350,
        "ember_equivalent": 2.35,
        "can_claim": true,
        "min_claim_sparks": 1000,
        "daily_stats": {
            "earned_today": 180,
            "cap": 500,
            "remaining": 320
        },
        "lifetime_stats": {
            "total_sparks_earned": 15000,
            "total_ember_claimed": 12.5,
            "from_adventures": 10000,
            "from_vigil": 3000,
            "from_achievements": 2000
        }
    }
    Rate Limit: 30/min

POST /api/kindling/claim-ember
    Body: {
        "wallet": "0x...",
        "sparks_to_convert": 2000
    }
    Response: {
        "success": true,
        "ember_claimed": 2.0,
        "sparks_used": 2000,
        "sparks_remaining": 350,
        "new_ember_balance": 125.5,
        "claim_id": "claim_uuid"
    }
    Errors: 400 (insufficient_sparks, below_minimum)
    Rate Limit: 5/min
```

### 7.5 Endpoints de Achievements y Sharing

```
GET /api/kindling/achievements/<token_id>
    Response: {
        "token_id": "00001",
        "total_achievements": 12,
        "achievements": [
            {
                "achievement_id": "first_flame",
                "name": "Primera Llama",
                "description": "Completa tu primera aventura",
                "rarity": "common",
                "earned_at": "2026-01-20T10:30:00Z",
                "sparks_reward": 100,
                "shared": false
            }
        ],
        "by_rarity": {
            "common": 8,
            "rare": 3,
            "epic": 1,
            "legendary": 0
        }
    }
    Rate Limit: 30/min

GET /api/kindling/share-card/<token_id>/<achievement_id>
    Response: {
        "image_url": "https://emberholmportal.xyz/api/kindling/card/00001/first_flame.png",
        "share_text": "🔥 Mi Emissary #00001 obtuvo 'Primera Llama' en KINDLING!",
        "farcaster_intent_url": "https://warpcast.com/~/compose?text=...",
        "og_metadata": {
            "title": "KINDLING Achievement",
            "description": "Primera Llama - Completa tu primera aventura",
            "image": "https://..."
        }
    }
    Rate Limit: 60/min

POST /api/kindling/record-share
    Body: {
        "wallet": "0x...",
        "token_id": "00001",
        "achievement_id": "first_flame",
        "platform": "farcaster",
        "cast_hash": "0x..."
    }
    Response: {
        "success": true,
        "bonus_sparks": 25,
        "message": "Thanks for sharing!"
    }
    Rate Limit: 10/min
```

### 7.6 Endpoints de Estado

```
GET /api/kindling/nft-status/<token_id>
    Response: {
        "token_id": "00001",
        "available_for_kindling": true,
        "current_state": "READY",
        "current_lock": null,
        "active_session": null,
        "stats": {
            "adventures_completed": 25,
            "adventures_failed": 8,
            "total_sparks_earned": 5000,
            "achievements_count": 12
        }
    }
    // Si esta en Kindling:
    Response: {
        "token_id": "00001",
        "available_for_kindling": false,
        "current_state": "IN_KINDLING",
        "current_lock": {
            "locked_by": "KINDLING",
            "locked_at": "2026-01-26T12:00:00Z",
            "expires_at": "2026-01-26T14:00:00Z"
        },
        "active_session": {
            "session_id": "uuid",
            "adventure_id": "K001",
            "adventure_name": "La Cueva del Dragon",
            "started_at": "2026-01-26T12:00:00Z",
            "current_node": 3
        }
    }
    Rate Limit: 60/min

GET /api/kindling/session/<session_id>
    Response: {
        "session_id": "uuid",
        "status": "active",
        "token_id": "00001",
        "adventure_id": "K001",
        "adventure_name": "La Cueva del Dragon",
        "current_node": 3,
        "choices_made": 3,
        "time_elapsed_minutes": 2.5,
        "expires_at": "2026-01-26T14:00:00Z"
    }
    Rate Limit: 30/min
```

---

## 8. MODIFICACIONES AL CODIGO EXISTENTE

### 8.1 Agregar Estado IN_KINDLING

**Archivo:** app.py

**Linea ~3340-3359 (dynamic_state defaults):**
```python
# Agregar campos para Kindling
DEFAULT_DYNAMIC_STATE = {
    # ... campos existentes ...
    "kindling_session_id": None,      # NUEVO
    "kindling_started_at": None,      # NUEVO
    "last_kindling_adventure": None,  # NUEVO
    "kindling_adventures_completed": 0 # NUEVO
}
```

**Linea ~6189-6208 (validacion de estados):**
```python
VALID_STATES = ["READY", "ON_MISSION", "FALLEN", "IN_KINDLING"]  # Agregar IN_KINDLING
```

### 8.2 Bloquear Misiones si en Kindling

**Archivo:** app.py

**Linea ~9680-9684 (start_mission validation):**
```python
# AGREGAR despues de validacion de FALLEN y ON_MISSION:
if ds.get('state') == 'IN_KINDLING':
    return {
        'error': 'hero_in_kindling',
        'error_type': 'locked',
        'message': 'This Emissary is on a Kindling adventure. Complete or abandon it first.',
        'kindling_session_id': ds.get('kindling_session_id'),
        'kindling_started_at': ds.get('kindling_started_at')
    }, 423  # HTTP 423 Locked
```

### 8.3 Rate Limits para Kindling

**Archivo:** app.py

**Agregar despues de linea ~105:**
```python
KINDLING_RATE_LIMITS = {
    '/api/kindling/start-adventure': 10,
    '/api/kindling/make-choice': 30,
    '/api/kindling/complete-adventure': 10,
    '/api/kindling/abandon-adventure': 5,
    '/api/kindling/adventures': 30,
    '/api/kindling/vigil-checkin': 5,
    '/api/kindling/vigil-status': 30,
    '/api/kindling/vault-status': 30,
    '/api/kindling/claim-ember': 5,
    '/api/kindling/achievements': 30,
    '/api/kindling/share-card': 60,
    '/api/kindling/nft-status': 60,
    '/api/kindling/session': 30,
}
```

### 8.4 Ruta para Servir Mini App

**Archivo:** app.py

**Agregar nueva ruta:**
```python
@app.route('/kindling')
@app.route('/kindling/<path:subpath>')
def serve_kindling_app(subpath=''):
    """Serve KINDLING mini-app SPA from /kindling route"""
    return send_from_directory('static/kindling', 'index.html')
```

### 8.5 CORS (No requiere cambios)

Como usamos la ruta `/kindling` en el mismo dominio, no hay problemas de CORS. Las llamadas a `/api/kindling/*` son same-origin.

---

## 9. SISTEMA DE LOCKS CROSS-APP

### 9.1 Arquitectura

```
+------------------+     +------------------+
|    MAIN GAME     |     |     KINDLING     |
+------------------+     +------------------+
         |                        |
         v                        v
+-----------------------------------------------+
|           nft_activity_locks                   |
|  (tabla central con TTL automatico)           |
+-----------------------------------------------+
                    |
                    v
+-----------------------------------------------+
|              nfts.dynamic_state                |
|  state: READY | ON_MISSION | FALLEN | IN_KINDLING |
+-----------------------------------------------+
```

### 9.2 Funcion de Lock

```python
def acquire_cross_app_lock(cursor, token_id, wallet, lock_source, ttl_hours=2):
    """
    Adquiere lock exclusivo para un NFT.

    Args:
        token_id: ID del NFT
        wallet: Wallet del owner
        lock_source: 'MAIN_GAME' o 'KINDLING'
        ttl_hours: Tiempo maximo de lock

    Returns:
        (success: bool, error_info: dict or None)
    """
    try:
        # 1. Verificar estado actual del NFT
        cursor.execute("""
            SELECT dynamic_state->>'state' as state,
                   last_known_owner
            FROM nfts
            WHERE token_id = %s
            FOR UPDATE NOWAIT
        """, (token_id,))

        nft = cursor.fetchone()
        if not nft:
            return False, {'error': 'nft_not_found'}

        if nft['last_known_owner'].lower() != wallet.lower():
            return False, {'error': 'not_owner'}

        state = nft['state']

        # 2. Verificar si puede ser locked
        if state == 'FALLEN':
            return False, {'error': 'nft_fallen', 'message': 'Revive first'}

        if state in ('ON_MISSION', 'IN_KINDLING'):
            return False, {
                'error': 'nft_busy',
                'current_state': state,
                'message': f'NFT is currently {state}'
            }

        # 3. Verificar/crear lock en tabla central
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

        cursor.execute("""
            INSERT INTO nft_activity_locks
                (token_id, is_locked, locked_by, lock_type, locked_at, expires_at, locked_by_wallet)
            VALUES (%s, TRUE, %s, %s, NOW(), %s, %s)
            ON CONFLICT (token_id) DO UPDATE
            SET is_locked = TRUE,
                locked_by = EXCLUDED.locked_by,
                lock_type = EXCLUDED.lock_type,
                locked_at = NOW(),
                expires_at = EXCLUDED.expires_at,
                locked_by_wallet = EXCLUDED.locked_by_wallet
            WHERE nft_activity_locks.is_locked = FALSE
               OR nft_activity_locks.expires_at < NOW()
            RETURNING token_id
        """, (token_id, lock_source, 'adventure' if lock_source == 'KINDLING' else 'mission',
              expires_at, wallet.lower()))

        if cursor.fetchone() is None:
            # Lock existe y no expiro
            cursor.execute("""
                SELECT locked_by, expires_at FROM nft_activity_locks
                WHERE token_id = %s AND is_locked = TRUE
            """, (token_id,))
            existing = cursor.fetchone()
            return False, {
                'error': 'already_locked',
                'locked_by': existing['locked_by'],
                'expires_at': existing['expires_at'].isoformat()
            }

        return True, None

    except psycopg2.errors.LockNotAvailable:
        return False, {'error': 'concurrent_access', 'message': 'Try again'}
```

### 9.3 Funcion de Release

```python
def release_cross_app_lock(cursor, token_id, lock_source):
    """Libera el lock de un NFT."""
    cursor.execute("""
        UPDATE nft_activity_locks
        SET is_locked = FALSE,
            locked_by = NULL,
            lock_type = NULL,
            lock_reference_id = NULL
        WHERE token_id = %s
          AND locked_by = %s
          AND is_locked = TRUE
        RETURNING token_id
    """, (token_id, lock_source))

    return cursor.fetchone() is not None
```

### 9.4 Cleanup de Locks Expirados

```python
def cleanup_expired_locks():
    """Ejecutar cada 5 minutos via cron/scheduler."""
    with get_db() as cursor:
        # 1. Encontrar locks expirados
        cursor.execute("""
            SELECT token_id, locked_by, lock_reference_id
            FROM nft_activity_locks
            WHERE is_locked = TRUE AND expires_at < NOW()
        """)
        expired = cursor.fetchall()

        for lock in expired:
            # 2. Limpiar sesiones Kindling abandonadas
            if lock['locked_by'] == 'KINDLING' and lock['lock_reference_id']:
                cursor.execute("""
                    UPDATE kindling_sessions
                    SET status = 'abandoned', completed_at = NOW()
                    WHERE session_id = %s AND status = 'active'
                """, (lock['lock_reference_id'],))

            # 3. Resetear estado del NFT
            cursor.execute("""
                UPDATE nfts
                SET dynamic_state = jsonb_set(
                    jsonb_set(dynamic_state, '{state}', '"READY"'),
                    '{kindling_session_id}', 'null'
                )
                WHERE token_id = %s
                  AND dynamic_state->>'state' = 'IN_KINDLING'
            """, (lock['token_id'],))

        # 4. Liberar todos los locks expirados
        cursor.execute("""
            UPDATE nft_activity_locks
            SET is_locked = FALSE, locked_by = NULL, lock_type = NULL
            WHERE is_locked = TRUE AND expires_at < NOW()
        """)

        cursor.connection.commit()
        return len(expired)
```

---

## 10. CONSIDERACIONES DE SEGURIDAD

### 10.1 Verificacion de Ownership

Antes de cualquier accion, verificar que el wallet es dueno del NFT:

```python
def verify_nft_ownership(token_id, wallet):
    """Verifica ownership en la base de datos."""
    with get_db() as cursor:
        cursor.execute("""
            SELECT last_known_owner FROM nfts WHERE token_id = %s
        """, (token_id,))
        nft = cursor.fetchone()

        if not nft:
            return False, "NFT not found"

        if nft['last_known_owner'].lower() != wallet.lower():
            return False, "Not owner"

        return True, None
```

### 10.2 Validacion de Inputs

```python
import re

def validate_kindling_input(data, schema_type):
    """Valida inputs de Kindling endpoints."""
    schemas = {
        'start_adventure': {
            'wallet': r'^0x[a-fA-F0-9]{40}$',
            'token_id': r'^\d{1,5}$',
            'adventure_id': r'^K\d{3}$'
        },
        'make_choice': {
            'wallet': r'^0x[a-fA-F0-9]{40}$',
            'session_id': r'^[a-f0-9-]{36}$',
            'choice_index': lambda x: isinstance(x, int) and 0 <= x <= 10
        }
    }

    schema = schemas.get(schema_type, {})
    errors = []

    for field, validator in schema.items():
        value = data.get(field)
        if value is None:
            errors.append(f"Missing field: {field}")
        elif callable(validator):
            if not validator(value):
                errors.append(f"Invalid value for: {field}")
        elif not re.match(validator, str(value)):
            errors.append(f"Invalid format for: {field}")

    return errors if errors else None
```

### 10.3 Rate Limiting por NFT

```python
def check_nft_rate_limit(token_id, action, max_per_hour=20):
    """Rate limit por NFT para prevenir abuso."""
    key = f"kindling:rate:{token_id}:{action}"

    # Usando cache en memoria o Redis
    count = cache.incr(key)
    if count == 1:
        cache.expire(key, 3600)  # 1 hora

    return count <= max_per_hour
```

### 10.4 Cap Diario de Sparks

```python
def add_sparks_with_cap(cursor, wallet, sparks_to_add, source):
    """Agrega sparks respetando el cap diario."""
    today = date.today()

    cursor.execute("""
        INSERT INTO ember_kindling_vault (wallet, sparks_balance, sparks_earned_today, today_date)
        VALUES (%s, 0, 0, %s)
        ON CONFLICT (wallet) DO UPDATE
        SET today_date = CASE
            WHEN ember_kindling_vault.today_date != %s THEN %s
            ELSE ember_kindling_vault.today_date
        END,
        sparks_earned_today = CASE
            WHEN ember_kindling_vault.today_date != %s THEN 0
            ELSE ember_kindling_vault.sparks_earned_today
        END
        RETURNING sparks_earned_today
    """, (wallet, today, today, today, today))

    current_today = cursor.fetchone()['sparks_earned_today']

    DAILY_CAP = 500
    remaining_cap = DAILY_CAP - current_today

    if remaining_cap <= 0:
        return 0, "Daily cap reached"

    actual_sparks = min(sparks_to_add, remaining_cap)

    cursor.execute("""
        UPDATE ember_kindling_vault
        SET sparks_balance = sparks_balance + %s,
            sparks_earned_today = sparks_earned_today + %s,
            sparks_lifetime_earned = sparks_lifetime_earned + %s,
            sparks_from_adventures = sparks_from_adventures + CASE WHEN %s = 'adventure' THEN %s ELSE 0 END,
            sparks_from_vigil = sparks_from_vigil + CASE WHEN %s = 'vigil' THEN %s ELSE 0 END,
            sparks_from_achievements = sparks_from_achievements + CASE WHEN %s = 'achievement' THEN %s ELSE 0 END,
            updated_at = NOW()
        WHERE wallet = %s
        RETURNING sparks_balance, sparks_earned_today
    """, (actual_sparks, actual_sparks, actual_sparks,
          source, actual_sparks, source, actual_sparks, source, actual_sparks, wallet))

    result = cursor.fetchone()
    return actual_sparks, {
        'sparks_added': actual_sparks,
        'daily_earned': result['sparks_earned_today'],
        'daily_remaining': DAILY_CAP - result['sparks_earned_today'],
        'total_balance': result['sparks_balance']
    }
```

---

## 11. ESTRUCTURA DE ARCHIVOS PARA MINI APP

```
static/
└── kindling/
    ├── index.html          # SPA entry point
    ├── css/
    │   ├── kindling.css    # Estilos principales
    │   └── animations.css  # Animaciones narrativas
    ├── js/
    │   ├── kindling.js     # Logica principal
    │   ├── adventure.js    # Motor de aventuras
    │   ├── vault.js        # Gestion de sparks
    │   └── share.js        # Integracion Farcaster
    ├── assets/
    │   ├── backgrounds/    # Fondos de aventuras
    │   ├── icons/          # Iconos UI
    │   └── achievements/   # Imagenes de logros
    └── data/
        └── achievements.json  # Definiciones de logros
```

---

## 12. ROADMAP DE IMPLEMENTACION

### Fase 1: Infraestructura (Dias 1-5)

- [ ] Crear las 6 tablas nuevas en PostgreSQL
- [ ] Implementar sistema de locks cross-app
- [ ] Agregar estado IN_KINDLING a validaciones existentes
- [ ] Agregar rate limits para endpoints Kindling
- [ ] Tests unitarios de locks

### Fase 2: Core API (Dias 6-12)

- [ ] Endpoint POST /api/kindling/start-adventure
- [ ] Endpoint POST /api/kindling/make-choice
- [ ] Endpoint POST /api/kindling/complete-adventure
- [ ] Endpoint POST /api/kindling/abandon-adventure
- [ ] Motor de aventuras (parser de story_nodes)
- [ ] Calculo de outcomes y rewards
- [ ] Sincronizacion de XP/Aura con NFT

### Fase 3: Economia (Dias 13-18)

- [ ] Sistema de Sparks con cap diario
- [ ] Endpoint GET /api/kindling/vault-status
- [ ] Endpoint POST /api/kindling/claim-ember
- [ ] Integracion con user_balances existente
- [ ] Tests de economia

### Fase 4: Vigil System (Dias 19-23)

- [ ] Endpoint POST /api/kindling/vigil-checkin
- [ ] Endpoint GET /api/kindling/vigil-status
- [ ] Logica de rachas y bonuses
- [ ] Tests de vigil

### Fase 5: Achievements (Dias 24-28)

- [ ] Sistema de logros
- [ ] Endpoint GET /api/kindling/achievements
- [ ] Definir achievements iniciales (15-20)
- [ ] Triggers automaticos de achievements

### Fase 6: Sharing (Dias 29-33)

- [ ] Generador de share cards (imagen)
- [ ] Endpoint GET /api/kindling/share-card
- [ ] Integracion con Farcaster intents
- [ ] Endpoint POST /api/kindling/record-share

### Fase 7: Frontend Mini App (Dias 34-45)

- [ ] Estructura HTML/CSS base
- [ ] Pantalla de seleccion de Emissary
- [ ] Pantalla de aventura (narrativa + choices)
- [ ] Pantalla de resultados
- [ ] Pantalla de vault
- [ ] Pantalla de vigil
- [ ] Pantalla de achievements

### Fase 8: Contenido (Dias 46-52)

- [ ] Escribir 3 aventuras EMBER (faciles)
- [ ] Escribir 3 aventuras FLAME (medias)
- [ ] Escribir 2 aventuras INFERNO (dificiles)
- [ ] Crear assets visuales
- [ ] Balancear rewards

### Fase 9: Testing y QA (Dias 53-60)

- [ ] Tests de integracion end-to-end
- [ ] Tests de carga
- [ ] Audit de seguridad
- [ ] Beta cerrada con usuarios reales
- [ ] Fix de bugs encontrados

### Fase 10: Launch (Dias 61-65)

- [ ] Deploy a produccion
- [ ] Monitoreo inicial 24/7
- [ ] Documentacion para usuarios
- [ ] Anuncio en Farcaster

---

## 13. RIESGOS Y MITIGACIONES

### Riesgos Tecnicos

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|--------------|---------|------------|
| Race conditions en locks | Media | Alto | FOR UPDATE NOWAIT + tests de concurrencia |
| Sesiones huerfanas | Media | Medio | TTL de 2h + cleanup cada 5min |
| Desync de XP entre apps | Baja | Alto | Transacciones atomicas, logs de auditoria |
| Overflow de sparks | Baja | Alto | BIGINT + validacion antes de operaciones |

### Riesgos de Seguridad

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|--------------|---------|------------|
| Farming automatizado | Alta | Medio | Rate limits por NFT + cap diario |
| Manipulacion de choices | Media | Alto | Validar server-side, no confiar en cliente |
| Robo de NFT mid-adventure | Baja | Medio | Verificar ownership antes de rewards |

### Riesgos de Negocio

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|--------------|---------|------------|
| Inflacion de $EMBER | Media | Alto | Cap diario de 500 sparks, ajustar ratios |
| Baja adopcion | Media | Medio | Incentivos iniciales, contenido atractivo |
| Aventuras repetitivas | Alta | Medio | Plan de contenido mensual, eventos especiales |

---

## APENDICE A: CONTRATOS RELEVANTES

```
Base Mainnet (Chain ID: 8453)

EmberholmPortal NFT:    0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3
EmberToken ($EMBER):    0xbA7723fBfb44C7712C0B78108ad873DcFd5Dd73b
AshToken ($ASH):        0xD4eef3eadb1Cf1B2905AA4Cd1022b8cCCC739DAb
EmberItems (ERC-1155):  0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA
EmberRunes (ERC-1155):  0xDa2D1085053c3700645a13498293D17c1cc3f595

Treasury Wallet:        0x31d6E19aAE43B5E2fbeDb01b6FF82AD1e8B576DC
Rewards Wallet:         0xa84C45Eb435732FAe8A017861c07394c3aA7d815
```

## APENDICE B: RESUMEN DE CAMBIOS A ARCHIVOS EXISTENTES

| Archivo | Cambio | Lineas Aproximadas |
|---------|--------|-------------------|
| app.py | Agregar campos Kindling a DEFAULT_DYNAMIC_STATE | ~3340-3359 |
| app.py | Agregar IN_KINDLING a VALID_STATES | ~6189-6208 |
| app.py | Bloquear misiones si IN_KINDLING | ~9680-9700 |
| app.py | Agregar KINDLING_RATE_LIMITS | ~105 |
| app.py | Agregar ruta /kindling para SPA | Nueva |
| app.py | Agregar todos los endpoints /api/kindling/* | Nueva seccion |
| schema.sql | Agregar 6 tablas nuevas | EOF |

---

## APENDICE C: CHECKLIST PRE-IMPLEMENTACION

- [x] Ratio sparks confirmado: 1000 = 1 $EMBER
- [x] Cap diario confirmado: 500 sparks
- [x] Sin muerte en Kindling confirmado
- [x] Sincronizacion XP/Aura confirmada
- [x] Dominio confirmado: /kindling (mismo dominio)
- [ ] **PENDIENTE: Aprobacion para iniciar implementacion**

---

*Documento v2.0 - Con decisiones confirmadas*
*Generado: 2026-01-26*
*Esperando aprobacion para proceder con implementacion*
