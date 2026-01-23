# INFORME COMPLETO: EMBERHOLM PORTAL

> **Documento de Presentación del Proyecto**
> Versión 1.0 | Enero 2026

---

## TABLA DE CONTENIDOS

1. [Introducción y Lore](#1-introducción-y-lore)
2. [Funcionamiento del Juego](#2-funcionamiento-del-juego)
3. [Sistema de Items y Runas](#3-sistema-de-items-y-runas)
4. [Sistema de Dropeo](#4-sistema-de-dropeo)
5. [Economía: Obtención de $EMBER](#5-economía-obtención-de-ember)
6. [Infraestructura Técnica](#6-infraestructura-técnica)
7. [Resumen Ejecutivo Q&A](#7-resumen-ejecutivo-qa)

---

## 1. INTRODUCCIÓN Y LORE

### 1.1 Concepto General

**Emberholm Portal** es un RPG medieval de fantasía donde **35,000 Emissaries NFT únicos** emprenden misiones, obtienen tokens **$EMBER** y determinan el destino de un **reino moribundo**.

### 1.2 El Mundo de Emberholm

El juego se desarrolla en **Emberholm**, un reino amenazado por fuerzas cósmicas:

- **La Llama Eterna**: Fuego sagrado en el corazón de Emberholm que proporciona estabilidad al reino. Una vez al año arde con intensidad extraordinaria.
- **El Núcleo Ember**: Corazón del reino que provee estabilidad y aura a todos sus habitantes.
- **El Velo**: Barrera que separa el mundo de los vivos del **Vacío**. Cuando se desgarra, consecuencias catastróficas amenazan la realidad.
- **El Vacío**: Dimensión de horror donde entidades que no deberían existir acechan, esperando cruzar.

### 1.3 Las Seis Facciones

| Facción | Miembros | Filosofía | Rol |
|---------|----------|-----------|-----|
| **Circle of Mist** | 10,599 | Alquimia, maná, conocimiento prohibido | Mantienen los nodos arcanos que regulan el flujo mágico |
| **Order of Dawn** | 6,341 | Clérigos y paladines del Core | Guardianes de la luz, protectores de la civilización |
| **Shadow Guild** | 6,234 | Información, silencio, crimen sancionado | Operaciones encubiertas, recopilación de inteligencia |
| **Forge Legion** | 4,538 | Fuerza, acero, juramentos | Guerreros, herreros, estrategas militares |
| **Void Echoes** | 4,302 | Nigromancia, espectrales, derechos de muerte | Especialistas en el Vacío, sellan brechas dimensionales |
| **Horizon Watch** | 2,986 | Exploradores, vigías del confín | Scouts y cartógrafos en el borde de la civilización |

### 1.4 Razas y Clases

**Razas disponibles**: Gith, Human, Tiefling, Draconid, Elf, Dwarf, Triton, Goliath

**Clases disponibles**: Hunter, Druid, Cleric, Explorer, Bard, Rogue, Paladin

---

## 2. FUNCIONAMIENTO DEL JUEGO

### 2.1 Sistema de Misiones

Los héroes completan **misiones** que consumen tiempo y energía a cambio de recompensas.

#### Tipos de Misión por Dificultad

| Dificultad | Duración | XP | Aura | Tasa Éxito | Riesgo Muerte | Energía |
|------------|----------|----|----- |------------|---------------|---------|
| **EASY** | 3 horas | 60 | 4 | 92% | 0% | 10 |
| **MEDIUM** | 6 horas | 150 | 10 | 78% | 0.5% | 18 |
| **HARD** | 12 horas | 350 | 25 | 60% | 2.0% | 25 |
| **PARTY** | Variable | +20% | +20% | Variable | Variable | Variable |

> **Misiones Party**: Requieren 5 héroes y otorgan un **multiplicador de 1.2x** en las recompensas.

### 2.2 Cálculo de Éxito

La tasa de éxito base se modifica por varios factores:

```
Tasa Final = min(98%, Tasa Base + Bonificaciones)
```

**Bonificaciones aplicables:**

| Factor | Bonus |
|--------|-------|
| Guild coincide | +12% |
| Clase coincide | +8% |
| Raza coincide | +5% |
| Por cada 10 niveles | +1% |
| Por cada 100 Aura | +1% |
| Bonus de ataque del equipo | Directo |
| Buffs de Ember Roll | Variable |

> **Alineamiento Perfecto**: Si guild, clase Y raza coinciden = **multiplicador 1.5x** en recompensas.

### 2.3 Sistema de Progresión

#### Atributos del Héroe

| Atributo | Descripción | Rango |
|----------|-------------|-------|
| `xp_total` | XP total acumulado | 0 - ∞ |
| `level` | Nivel = XP / 100 | 0 - ∞ |
| `aura_level` | Aura total acumulada | 0 - ∞ |
| `energy_current` | Energía disponible | 0 - 100 |
| `state` | Estado actual | READY / ON_MISSION / FALLEN |

#### Generación Pasiva (cada 24 horas)

- **+5 XP** por día por héroe
- **+1 Aura** por día por héroe

#### Regeneración de Energía

- Recuperación completa cada **48 horas**
- Energía inicial: **100 puntos**

### 2.4 Sistema de Muerte

#### Protección contra la Muerte

Los héroes ganan protección según su progreso:

**Por Nivel:**
| Nivel | Protección |
|-------|------------|
| 10+ | +5% |
| 30+ | +15% |
| 50+ | +30% |

**Por Aura:**
| Aura | Protección |
|------|------------|
| 100+ | +5% |
| 250+ | +10% |
| 500+ | +20% |

- **Máximo de nivel/aura**: 50%
- **Equipo puede agregar**: hasta 30%
- **Protección total máxima**: 80%

#### Costos de Resurrección (Reinvocación)

| Muerte # | Costo XP | Costo Aura | Narrativa |
|----------|----------|------------|-----------|
| 1ra | 500 | 100 | "Es misericordiosa. El ritual es simple." |
| 2da | 1,500 | 300 | "Cobra su precio. Los espíritus demandan más." |
| 3ra | 5,000 | 1,000 | "Es severa. Tu alma se debilita con cada retorno." |
| 4ta+ | 10,000 | 2,500 | "Más allá de la tercera muerte, el precio es astronómico." |

---

## 3. SISTEMA DE ITEMS Y RUNAS

### 3.1 Tipos de Equipamiento

| Tipo | Stats Base | Efecto Principal |
|------|------------|------------------|
| **WEAPON** | +10 ataque, +5 XP boost | Aumenta tasa de éxito |
| **ARMOR** | +10 defensa, +5 energy_regen | Protección y regeneración |
| **HELMET** | +5 defensa, +5 aura_boost | Boost de aura |
| **ACCESSORY** | +5 luck, +5 ember_boost | Más $EMBER |
| **AMULET** | +10 aura_boost, +5 xp_boost | Doble boost |
| **RUNE** | +5 all_boost | Afecta TODOS los stats |

### 3.2 Rarezas y Multiplicadores

| Rareza | Multiplicador Base |
|--------|-------------------|
| Common | 1x |
| Uncommon | 1.5x |
| Rare | 2x |
| Epic | 4x |
| Legendary | 8x |

### 3.3 Bonificaciones por Rareza

#### Items

| Rareza | $EMBER% | XP% | Energía% | Muerte% | Velocidad% |
|--------|---------|-----|----------|---------|------------|
| Common | +3% | +2% | 0% | 0% | 0% |
| Uncommon | +5% | +4% | -2% | 0% | 0% |
| Rare | +8% | +6% | -3% | -2% | 0% |
| Epic | +12% | +10% | -5% | -4% | +3% |
| Legendary | +18% | +15% | -8% | -6% | +5% |

#### Runas (Más Balanceadas)

| Rareza | $EMBER% | XP% | Energía% | Muerte% | Velocidad% |
|--------|---------|-----|----------|---------|------------|
| Common | +3% | +3% | -2% | -2% | +2% |
| Uncommon | +5% | +5% | -3% | -3% | +3% |
| Rare | +8% | +8% | -5% | -5% | +5% |
| Epic | +12% | +12% | -8% | -8% | +8% |
| Legendary | +18% | +18% | -12% | -12% | +12% |

### 3.4 Items Legendarios (Ejemplos)

**Armas:**
- Ashbringer, Staff of the Void, Soulreaver, Bow of the Phoenix

**Armaduras:**
- Armor of the Last Ember, Robes of Eternity, Voidwalker Cloak, Phoenix Plate

**Accesorios:**
- Ring of the Last Ember, Void Pendant, Phoenix Charm

**Runas:**
- Rune of the Last Ember, Rune of Eternity, Rune of the Phoenix

### 3.5 Cómo Afecta el Equipo

| Stat | Efecto en Gameplay |
|------|-------------------|
| Attack Bonus | Se suma directo a la tasa de éxito |
| XP Boost | `new_xp = xp × (100 + boost%) / 100` |
| Aura Boost | `new_aura = aura × (100 + boost%) / 100` |
| Energy Cost | Reduce el consumo de energía de misiones |
| Death Protection | Reduce la probabilidad efectiva de muerte |
| Speed | Reduce la duración de las misiones |

---

## 4. SISTEMA DE DROPEO

### 4.1 Probabilidades de Drop por Dificultad

| Dificultad | Drop Item | Drop Runa |
|------------|-----------|-----------|
| **EASY** | 5% | 1% |
| **MEDIUM** | 10% | 3% |
| **HARD** | 20% | 8% |
| **PARTY** | 25% | 12% |

### 4.2 Distribución de Rareza por Dificultad

#### Al Obtener un Item/Runa:

| Dificultad | Common | Rare | Epic | Legendary |
|------------|--------|------|------|-----------|
| **EASY** | 70% | 25% | 4% | 1% |
| **MEDIUM** | 50% | 35% | 12% | 3% |
| **HARD** | 30% | 40% | 23% | 7% |
| **PARTY** | 20% | 40% | 30% | 10% |

### 4.3 Probabilidad Combinada (Drop × Rareza)

**Ejemplo: Obtener un Item Legendary**

| Dificultad | Cálculo | Probabilidad Final |
|------------|---------|-------------------|
| EASY | 5% × 1% | **0.05%** |
| MEDIUM | 10% × 3% | **0.30%** |
| HARD | 20% × 7% | **1.40%** |
| PARTY | 25% × 10% | **2.50%** |

> Las misiones PARTY tienen **50 veces** más probabilidad de drop Legendary que las EASY.

---

## 5. ECONOMÍA: OBTENCIÓN DE $EMBER

### 5.1 Método Principal: Ember Roll (D20)

Sistema de dados que permite ganar $EMBER con riesgo/recompensa.

| Tirada | Resultado | $EMBER | Bonus Éxito | Bonus XP | Duración |
|--------|-----------|--------|-------------|----------|----------|
| 1 | CRITICAL FAIL | **-100** | -20% | -10 | 24h |
| 2-5 | NOTHING | 0 | 0 | 0 | - |
| 6-8 | GRAZE | +50 | +5% | 0 | 12h |
| 9-11 | HIT | +100 | +10% | +5 | 24h |
| 12-14 | SOLID HIT | +200 | +15% | +10 | 24h |
| 15-17 | GREAT HIT | +350 | +20% | +15 | 24h |
| 18 | CRITICAL | +500 | +25% | +20 | 48h |
| 19 | SUPERIOR | +500 | +30% | +25 | 48h |
| **20** | **NATURAL 20** | **+1,000** | +35% | +30 | 72h |

**Reglas del Ember Roll:**
- Máximo **5 tiradas por día**
- **1ra tirada**: GRATIS
- **2da-5ta tiradas**: 75 $EMBER cada una
- Reset diario

### 5.2 Valor Esperado del Ember Roll

**Probabilidades (D20):**
- P(1) = 5% → -100 $EMBER
- P(2-5) = 20% → 0 $EMBER
- P(6-8) = 15% → +50 $EMBER
- P(9-11) = 15% → +100 $EMBER
- P(12-14) = 15% → +200 $EMBER
- P(15-17) = 15% → +350 $EMBER
- P(18) = 5% → +500 $EMBER
- P(19) = 5% → +500 $EMBER
- P(20) = 5% → +1,000 $EMBER

**Valor Esperado por Tirada:**
```
EV = (0.05 × -100) + (0.20 × 0) + (0.15 × 50) + (0.15 × 100) +
     (0.15 × 200) + (0.15 × 350) + (0.05 × 500) + (0.05 × 500) + (0.05 × 1000)
   = -5 + 0 + 7.5 + 15 + 30 + 52.5 + 25 + 25 + 50
   = +200 $EMBER por tirada
```

> El sistema tiene **valor esperado positivo** de +200 $EMBER por tirada.

### 5.3 Costos de Energía (Sink de $EMBER)

| Recarga | Costo $EMBER |
|---------|-------------|
| +25 Energía | 30 $EMBER |
| +50 Energía | 75 $EMBER |
| +100 Energía (Full) | 150 $EMBER |

### 5.4 Conversión a $ASH

```
1,000 $EMBER = 1 $ASH
```

$ASH es el token de valor premium del ecosistema.

---

## 6. INFRAESTRUCTURA TÉCNICA

### 6.1 Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   HTML/JS   │  │   CSS       │  │   Web3 (ethers.js)  │  │
│  │  Vanilla    │  │  Hacknet    │  │   MetaMask          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Flask     │  │  PostgreSQL │  │   API Endpoints     │  │
│  │   Python    │  │  Database   │  │   /api/*            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      BLOCKCHAIN                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Base       │  │  Smart      │  │   IPFS              │  │
│  │  Mainnet    │  │  Contracts  │  │   Metadata          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Smart Contracts (Base Mainnet)

| Contrato | Dirección | Función |
|----------|-----------|---------|
| **EmberholmPortal** | `0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3` | NFTs ERC721 (35,000) |
| **EmberToken** | `0xbA7723fBfb44C7712C0B78108ad873DcFd5Dd73b` | Token $EMBER ERC20 |
| **AshToken** | `0xD4eef3eadb1Cf1B2905AA4Cd1022b8cCCC739DAb` | Token $ASH ERC20 |
| **EmberRunes** | `0xDa2D1085053c3700645a13498293D17c1cc3f595` | NFTs de Runas |
| **EmberItems** | `0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA` | NFTs de Items |

### 6.3 Costos para el Usuario

#### Costo de Minteo

| Concepto | Valor |
|----------|-------|
| Precio por NFT | 0.0011 ETH |
| Gas estimado | ~0.0002-0.0005 ETH |
| Máx. por transacción | 10 NFTs |
| Supply total | 35,000 NFTs |

#### Costos de Transacción (Estimados en Base)

| Operación | Gas Estimado | Costo ~USD |
|-----------|--------------|------------|
| Mint 1 NFT | ~100,000 gas | ~$0.02-0.05 |
| Stake Token | ~50,000 gas | ~$0.01-0.02 |
| Claim Item/Rune | ~80,000 gas | ~$0.02-0.03 |
| Equipar Item | ~60,000 gas | ~$0.01-0.02 |

> Base L2 ofrece costos **~100x menores** que Ethereum mainnet.

### 6.4 Base de Datos PostgreSQL

#### Esquema de Tablas

**Tabla `nfts`** (35,000+ registros)
```sql
CREATE TABLE nfts (
    token_id VARCHAR(5) PRIMARY KEY,  -- "00001", "00002"...
    owner_address VARCHAR(42),
    guild VARCHAR(50),
    dynamic_state JSONB,               -- XP, Aura, Energy, State
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
-- Índices: owner_address, guild, state
```

**Tabla `active_missions`**
```sql
CREATE TABLE active_missions (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(42),
    hero_id VARCHAR(5),
    mission_id VARCHAR(10),
    start_time TIMESTAMP,
    duration_hours INTEGER
);
```

**Tabla `players`** (Cache de sesión)
```sql
CREATE TABLE players (
    wallet_address VARCHAR(42) PRIMARY KEY,
    player_data JSONB,  -- Cache completo, puede limpiarse
    last_sync TIMESTAMP
);
```

**Tabla `global_stats`** (Singleton)
```sql
CREATE TABLE global_stats (
    id INTEGER PRIMARY KEY DEFAULT 1,
    total_missions_completed INTEGER,
    total_missions_failed INTEGER,
    total_xp_collected BIGINT,
    total_aura_collected BIGINT,
    total_deaths INTEGER
);
```

### 6.5 Estructura de Datos del Héroe

```json
{
  "fixed_profile": {
    "token_id": "00001",
    "name": "Entara, Bearer of Economy",
    "race": "Gith",
    "class": "Druid",
    "guild": "Circle of Mist",
    "rarity": "Rare",
    "str": 11, "dex": 12, "con": 12,
    "int": 15, "wis": 15, "cha": 11
  },
  "dynamic_state": {
    "xp_total": 250,
    "xp_level": 2,
    "aura_level": 15,
    "energy_current": 80,
    "energy_max": 100,
    "power_current": 18,
    "state": "READY",
    "total_missions_completed": 3,
    "death_count": 0,
    "ember_roll_buff": null,
    "equipped_items": {
      "weapon": null,
      "armor": null,
      "boots": null,
      "accessory": null
    }
  }
}
```

### 6.6 Flujo de Persistencia de Datos

```
1. Usuario conecta wallet → Frontend llama tokensOfOwner()
2. Frontend envía POST /api/player/{wallet} con token IDs
3. Backend sincroniza con PostgreSQL (tabla nfts)
4. Backend recalcula stats globales y rankings de guild
5. Frontend carga datos de /api/player/{wallet}
6. Usuario juega misiones → Backend actualiza dynamic_state
7. Todos los cambios persisten entre sesiones
```

### 6.7 Almacenamiento IPFS

| Contenido | CID |
|-----------|-----|
| Items Metadata | `bafybeibs6mm5rghbpld7twbj35dbpryrfimmqkbnkev6ufs4kpbp343wfm` |
| Items Images | `bafybeiegbqf3ypcn7uukahdf275yrmxu2g4zt4xmmrfwguufppbhzs4yx4` |
| Runes Metadata | `bafybeiajq22kxgm764srr55wsiz4t65so5laxe2nmrryzgailzpmfes3nq` |
| Runes Images | `bafybeibmivzieas7beofrxspoqo5iughrzyvg3wgjibe626eqt37zg3sae` |

### 6.8 Stack Tecnológico Completo

| Capa | Tecnología |
|------|------------|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **UI Theme** | Hacknet-inspired terminal aesthetic |
| **Backend** | Python Flask |
| **Database** | PostgreSQL (Render) |
| **Blockchain** | Base Mainnet (L2) |
| **Smart Contracts** | Solidity 0.8.20 |
| **Wallet** | MetaMask |
| **Web3 Library** | ethers.js |
| **Hosting** | Render.com |
| **Storage** | IPFS (metadata e imágenes) |

---

## 7. RESUMEN EJECUTIVO Q&A

### Preguntas Generales

**Q: ¿Qué es Emberholm Portal?**
> A: Un RPG medieval de fantasía play-to-earn donde 35,000 NFTs únicos (Emissaries) completan misiones para ganar tokens $EMBER y progresar en un mundo amenazado por el Vacío.

**Q: ¿Cuánto cuesta empezar a jugar?**
> A: El minteo de un Emissary cuesta 0.0011 ETH (~$2-3 USD) + gas fees mínimos en Base (~$0.02-0.05).

**Q: ¿Cuántos NFTs existen?**
> A: 35,000 Emissaries únicos con diferentes razas, clases, guilds y estadísticas.

### Preguntas de Gameplay

**Q: ¿Cómo funcionan las misiones?**
> A: Los héroes se envían a misiones que duran 3-12 horas. Al completarse, se calcula éxito/fallo y se otorgan recompensas (XP, Aura, posibles drops de items/runas).

**Q: ¿Qué pasa si mi héroe muere?**
> A: El héroe queda en estado FALLEN. Puedes resucitarlo pagando XP y Aura. El costo aumenta con cada muerte (500 XP primera vez, hasta 10,000 XP la cuarta+).

**Q: ¿Cuál es la mejor dificultad para farmear?**
> A: Depende de tu objetivo:
> - **Items Legendary**: PARTY (2.5% probabilidad)
> - **Seguridad**: EASY (0% muerte, 92% éxito)
> - **Balance XP/Riesgo**: MEDIUM (150 XP, 0.5% muerte)

**Q: ¿Cómo maximizo las recompensas?**
> A: Alinea guild, clase y raza con la misión (1.5x multiplicador), equipa items de alta rareza (+18% $EMBER legendary), y usa Party missions (1.2x bonus).

### Preguntas Económicas

**Q: ¿Cómo gano $EMBER?**
> A: Principalmente a través del Ember Roll (D20). La primera tirada es gratis, las siguientes cuestan 75 $EMBER. Valor esperado: +200 $EMBER por tirada.

**Q: ¿Qué puedo hacer con $EMBER?**
> A: Comprar energía para más misiones, hacer más Ember Rolls, y convertir 1,000 $EMBER en 1 $ASH (token premium).

**Q: ¿Hay inflación de tokens?**
> A: El sistema tiene sinks (costos de energía, rolls adicionales, resurrecciones) que equilibran la generación de tokens.

### Preguntas Técnicas

**Q: ¿Dónde se guardan mis datos?**
> A: Los datos de propiedad están on-chain (Base). El progreso del juego (XP, Aura, misiones) se almacena en PostgreSQL con backup. Los metadatos e imágenes están en IPFS.

**Q: ¿Es seguro?**
> A: Sí. Los NFTs usan el estándar ERC721. Durante misiones, los tokens se "stakean" para prevenir transferencias fraudulentas. El contrato tiene 5% royalty.

**Q: ¿Qué blockchain usa?**
> A: Base Mainnet (L2 de Ethereum), ofreciendo transacciones rápidas y económicas (~$0.01-0.05 por operación).

**Q: ¿Necesito MetaMask?**
> A: Sí, MetaMask es necesario para conectar tu wallet y firmar transacciones.

### Preguntas de Items/Runas

**Q: ¿Cuál es la diferencia entre Items y Runas?**
> A: Los items dan bonuses específicos por tipo (arma = ataque, armadura = defensa). Las runas dan bonus balanceado a TODOS los stats.

**Q: ¿Qué tan raro es obtener un Legendary?**
> A: En misiones HARD: 1.4% (20% drop × 7% legendary). En PARTY: 2.5%. En EASY: solo 0.05%.

**Q: ¿Los items están on-chain?**
> A: Sí, existe un contrato EmberItems y EmberRunes. Los claims se firman criptográficamente en el backend y se reclaman on-chain.

---

## ANEXO: FÓRMULAS CLAVE

### Nivel
```
nivel = xp_total ÷ 100
```

### Tasa de Éxito
```
tasa_éxito = min(98%, tasa_base + bonificaciones)
```

### Multiplicador de Alineamiento
```
multiplicador = 1.5x si (guild + clase + raza coinciden)
```

### Aplicación de Stats de Equipo
```
stat_final = stat_base × (100 + bonus%) ÷ 100
```

### Mitigación de Muerte
```
muerte_efectiva = muerte_base × (1 - protección_total%)
protección_total = min(80%, nivel + aura + equipo)
```

### Bonus de Party
```
recompensa_party = recompensa_base × 1.2x (solo en éxito)
```

---

*Documento generado para presentación del proyecto Emberholm Portal*
*Enero 2026*
