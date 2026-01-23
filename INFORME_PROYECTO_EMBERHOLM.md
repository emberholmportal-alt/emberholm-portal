# INFORME COMPLETO: EMBERHOLM PORTAL

> **Documento de Presentación del Proyecto**
> Versión 2.1 | Enero 2026

---

## TABLA DE CONTENIDOS

1. [Introducción y Lore](#1-introducción-y-lore)
2. [Funcionamiento del Juego](#2-funcionamiento-del-juego)
3. [NFTs con Metadata Dinámica](#3-nfts-con-metadata-dinámica)
4. [Sistema de Items y Runas](#4-sistema-de-items-y-runas)
5. [Sistema de Dropeo](#5-sistema-de-dropeo)
6. [Economía: Token $EMBER](#6-economía-token-ember)
7. [Token $ASH - Gobernanza](#7-token-ash---gobernanza)
8. [Sistema de Rankings](#8-sistema-de-rankings)
9. [Sistema de Achievements](#9-sistema-de-achievements)
10. [Infraestructura Técnica](#10-infraestructura-técnica)
11. [Resumen Ejecutivo Q&A](#11-resumen-ejecutivo-qa)

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

| Dificultad | Duración | XP | Aura | $EMBER | Tasa Éxito | Muerte | Energía |
|------------|----------|----|----- |--------|------------|--------|---------|
| **EASY** | 3 horas | 60 | 4 | 10-25 | 92% | 0% | 10 |
| **MEDIUM** | 6 horas | 150 | 10 | 30-75 | 78% | 0.5% | 18 |
| **HARD** | 12 horas | 350 | 25 | 80-200 | 60% | 2.0% | 25 |
| **PARTY** | Variable | +20% | +20% | +20% | Variable | Variable | Variable |

> **Misiones Party**: Requieren 5 héroes y otorgan un **multiplicador de 1.2x** en TODAS las recompensas.

### 2.2 Resultados de Misión

| Resultado | XP | Aura | $EMBER | Consecuencia |
|-----------|----|----- |--------|--------------|
| **ÉXITO** | 100% | 100% | 100% | Recompensas completas + chance de drop |
| **FALLO** | -25 a -60 | 0 | 0 | Pierde XP según dificultad |
| **MUERTE** | -100% | -100% | -100% | Héroe en estado FALLEN |

### 2.3 Cálculo de Éxito

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

### 2.4 Sistema de Progresión

#### Atributos del Héroe

| Atributo | Descripción | Rango |
|----------|-------------|-------|
| `xp_total` | XP total acumulado | 0 - ∞ |
| `level` | Nivel = 1 + (XP / 1000) | 1 - ∞ |
| `aura_level` | Aura total acumulada | 0 - ∞ |
| `energy_current` | Energía disponible | 0 - 100 |
| `state` | Estado actual | READY / ON_MISSION / FALLEN |

#### Generación Pasiva (cada 24 horas)

- **+5 XP** por día por héroe
- **+1 Aura** por día por héroe

#### Regeneración de Energía

- Recuperación completa cada **48 horas**
- Energía inicial: **100 puntos**

### 2.5 Sistema de Muerte y Resurrección

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

#### Costos de Resurrección con $EMBER

| Muerte # | Costo $EMBER | Descripción |
|----------|--------------|-------------|
| 1ra | **200 EMBER** | "La muerte es misericordiosa. El ritual es simple." |
| 2da | **500 EMBER** | "Cobra su precio. Los espíritus demandan más." |
| 3ra | **1,000 EMBER** | "Es severa. Tu alma se debilita con cada retorno." |
| 4ta | **2,500 EMBER** | "El velo se resiste a liberarte." |
| 5ta | **5,000 EMBER** | "Las fuerzas del más allá te reclaman." |
| 6ta+ | **10,000 EMBER** | "Precio máximo. Tu existencia pende de un hilo." |

**Estado post-resurrección:**
- XP reinicia a **100**
- Aura reinicia a **20**
- Energía al **50%**

---

## 3. NFTs CON METADATA DINÁMICA

### 3.1 Arquitectura de Metadata

Los NFTs de Emberholm son **dinámicos**: su metadata cambia en tiempo real según las acciones del jugador.

#### Perfil Fijo (Inmutable)

Estos datos se establecen al mintear y **NUNCA cambian**:

```json
{
  "token_id": "00001",
  "name": "Entara, Bearer of Economy",
  "race": "Gith",
  "class": "Druid",
  "rarity": "Rare",
  "age": 127,
  "starting_guild": "Circle of Mist",
  "base_stats": {
    "str": 11, "dex": 12, "con": 12,
    "int": 15, "wis": 15, "cha": 11
  }
}
```

#### Estado Dinámico (Actualizado en Tiempo Real)

Estos datos cambian con cada acción:

```json
{
  "dynamic_state": {
    "current_guild": "Circle of Mist",
    "xp_total": 2500,
    "xp_level": 3,
    "aura_level": 150,
    "energy_current": 80,
    "energy_max": 100,
    "power_current": 18,
    "state": "READY",
    "death_count": 0,
    "total_missions_completed": 25,
    "last_mission": "Echoes of the Deep",
    "mission_history": {
      "forest_patrol": "2026-01-20T10:00:00Z"
    },
    "ember_roll_buff": {
      "success_bonus": 15,
      "xp_bonus": 10,
      "expires": "2026-01-24T12:00:00Z"
    },
    "equipped_items": {
      "weapon_id": "W-0042",
      "armor_id": "A-0015",
      "helmet_id": null,
      "accessory_id": "AC-0003",
      "amulet_id": null,
      "rune_ids": ["R-0001", "R-0008"]
    },
    "achievements": ["first_mission", "10_missions", "reach_level_10"]
  }
}
```

### 3.2 Cuándo se Actualiza la Metadata

| Evento | Cambios en Metadata |
|--------|---------------------|
| Completar misión | XP, Aura, missions_completed, last_mission |
| Morir | state → FALLEN, death_count++ |
| Resucitar | state → READY, XP/Aura reset, energy 50% |
| Equipar item | equipped_items actualizado |
| Ember Roll | ember_roll_buff con expiración |
| Cambiar guild | current_guild actualizado |
| Obtener logro | achievements[] actualizado |

### 3.3 Visualización en Marketplaces

La metadata dinámica se refleja automáticamente en OpenSea y otros marketplaces vía el endpoint `/api/metadata/<token_id>`, mostrando:

- Nivel actual del héroe
- Aura acumulada
- Misiones completadas
- Logros desbloqueados
- Estado (READY/ON_MISSION/FALLEN)

---

## 4. SISTEMA DE ITEMS Y RUNAS

### 4.1 Tipos de Equipamiento

| Tipo | Stats Base | Efecto Principal |
|------|------------|------------------|
| **WEAPON** | +10 ataque, +5 XP boost | Aumenta tasa de éxito |
| **ARMOR** | +10 defensa, +5 energy_regen | Protección y regeneración |
| **HELMET** | +5 defensa, +5 aura_boost | Boost de aura |
| **ACCESSORY** | +5 luck, +5 ember_boost | Más $EMBER |
| **AMULET** | +10 aura_boost, +5 xp_boost | Doble boost |
| **RUNE** | +5 all_boost | Afecta TODOS los stats |

### 4.2 Rarezas y Multiplicadores

| Rareza | Multiplicador Base | Color |
|--------|-------------------|-------|
| Common | 1x | Gris |
| Uncommon | 1.5x | Verde |
| Rare | 2x | Azul |
| Epic | 4x | Púrpura |
| Legendary | 8x | Dorado |

### 4.3 Bonificaciones por Rareza

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

### 4.4 Items Legendarios (Ejemplos)

**Armas:**
- Ashbringer, Staff of the Void, Soulreaver, Bow of the Phoenix

**Armaduras:**
- Armor of the Last Ember, Robes of Eternity, Voidwalker Cloak, Phoenix Plate

**Accesorios:**
- Ring of the Last Ember, Void Pendant, Phoenix Charm

**Runas:**
- Rune of the Last Ember, Rune of Eternity, Rune of the Phoenix

### 4.5 Cómo Afecta el Equipo

| Stat | Efecto en Gameplay |
|------|-------------------|
| Attack Bonus | Se suma directo a la tasa de éxito |
| XP Boost | `new_xp = xp × (100 + boost%) / 100` |
| Aura Boost | `new_aura = aura × (100 + boost%) / 100` |
| Energy Cost | Reduce el consumo de energía de misiones |
| Death Protection | Reduce la probabilidad efectiva de muerte |
| Speed | Reduce la duración de las misiones |

---

## 5. SISTEMA DE DROPEO

### 5.1 Probabilidades de Drop por Dificultad

| Dificultad | Drop Item | Drop Runa |
|------------|-----------|-----------|
| **EASY** | 5% | 1% |
| **MEDIUM** | 10% | 3% |
| **HARD** | 20% | 8% |
| **PARTY** | 25% | 12% |

### 5.2 Distribución de Rareza por Dificultad

#### Al Obtener un Item/Runa:

| Dificultad | Common | Rare | Epic | Legendary |
|------------|--------|------|------|-----------|
| **EASY** | 70% | 25% | 4% | 1% |
| **MEDIUM** | 50% | 35% | 12% | 3% |
| **HARD** | 30% | 40% | 23% | 7% |
| **PARTY** | 20% | 40% | 30% | 10% |

### 5.3 Probabilidad Combinada (Drop × Rareza)

**Ejemplo: Obtener un Item Legendary**

| Dificultad | Cálculo | Probabilidad Final |
|------------|---------|-------------------|
| EASY | 5% × 1% | **0.05%** |
| MEDIUM | 10% × 3% | **0.30%** |
| HARD | 20% × 7% | **1.40%** |
| PARTY | 25% × 10% | **2.50%** |

> Las misiones PARTY tienen **50 veces** más probabilidad de drop Legendary que las EASY.

---

## 6. ECONOMÍA: TOKEN $EMBER

### 6.1 Formas de Obtener $EMBER

#### Método 1: Recompensas de Misiones

| Dificultad | $EMBER Mínimo | $EMBER Máximo | Promedio |
|------------|---------------|---------------|----------|
| EASY | 10 | 25 | ~17 |
| MEDIUM | 30 | 75 | ~52 |
| HARD | 80 | 200 | ~140 |
| PARTY | +20% sobre base | +20% sobre base | Variable |

> Con equipo Legendary (+18% EMBER): multiplicar recompensas × 1.18

#### Método 2: Ember Roll (D20)

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
- Reset diario a las 00:00 UTC

#### Método 3: Staking de NFTs (Planificado Q3 2025)

| Modo | $EMBER/día por NFT |
|------|-------------------|
| Sin stake (en wallet) | 10 EMBER |
| Staked (bloqueado) | 25 EMBER |
| Lock 30 días | 20 EMBER |
| Lock 90 días | 30 EMBER (+50%) |
| Lock 180 días | 45 EMBER (+125%) |
| Lock 365 días | 70 EMBER (+250%) |

### 6.2 Valor Esperado del Ember Roll

**Probabilidades (D20):**
```
P(1)     = 5%  → -100 $EMBER
P(2-5)   = 20% → 0 $EMBER
P(6-8)   = 15% → +50 $EMBER
P(9-11)  = 15% → +100 $EMBER
P(12-14) = 15% → +200 $EMBER
P(15-17) = 15% → +350 $EMBER
P(18)    = 5%  → +500 $EMBER
P(19)    = 5%  → +500 $EMBER
P(20)    = 5%  → +1,000 $EMBER

EV = +200 $EMBER por tirada
```

> El sistema tiene **valor esperado positivo** de +200 $EMBER por tirada.

### 6.3 Usos de $EMBER

| Uso | Costo $EMBER |
|-----|-------------|
| **Recarga +25 Energía** | 30 |
| **Recarga +50 Energía** | 75 |
| **Recarga +100 Energía** | 150 |
| **Ember Roll adicional** | 75 |
| **Resurrección (1ra muerte)** | 200 |
| **Resurrección (6ta+ muerte)** | 10,000 |
| **Conversión a $ASH** | 1,000 = 1 ASH |

### 6.4 Distribución del Token $EMBER

**Supply Total: 100,000,000 EMBER**

| Asignación | Cantidad | Porcentaje | Vesting |
|------------|----------|------------|---------|
| **Staking Rewards** | 40,000,000 | 40% | 4 años |
| **Team & Development** | 20,000,000 | 20% | 2 años (lineal) |
| **Liquidity Pools** | 15,000,000 | 15% | Inmediato |
| **Marketing & Partnerships** | 10,000,000 | 10% | Según necesidad |
| **Treasury/DAO Reserve** | 10,000,000 | 10% | Gobernanza |
| **Initial Airdrop** | 5,000,000 | 5% | Al lanzamiento |

### 6.5 Emisiones Anuales (Staking)

```
Año 1: 15,000,000 EMBER (~41,000/día)
Año 2: 12,000,000 EMBER (~33,000/día)
Año 3:  8,000,000 EMBER (~22,000/día)
Año 4:  5,000,000 EMBER (~14,000/día)
─────────────────────────────────────
Total:  40,000,000 EMBER (4 años)
```

### 6.6 Mecanismos Deflacionarios

| Mecanismo | Descripción | % Quemado |
|-----------|-------------|-----------|
| Crafting Burns | Cada craft quema EMBER | 100% |
| Upgrade Burns | Mejoras de guild/items | 100% |
| Marketplace Fees | Fee de cada trade | 2% |
| Resurrecciones | EMBER gastado en revivir | 100% |

> **Proyección 5 años**: Supply podría reducirse a 80-85M EMBER.

### 6.7 Vesting del Team

| Hito | Porcentaje Liberado |
|------|---------------------|
| TGE (lanzamiento) | 0% |
| 6 meses | 25% |
| 12 meses | 50% |
| 18 meses | 75% |
| 24 meses | 100% |

---

## 7. TOKEN $ASH - GOBERNANZA

### 7.1 Concepto

**$ASH** es el token de gobernanza premium de Emberholm, obtenido quemando $EMBER.

### 7.2 Obtención

```
1,000 $EMBER = 1 $ASH (quema permanente)
```

- Mínimo para convertir: 100 EMBER (produce 0.1 ASH)
- Sin límite máximo de conversión
- Proceso irreversible (EMBER se quema)

### 7.3 Utilidades de $ASH

| Utilidad | Descripción |
|----------|-------------|
| **Gobernanza DAO** | 1 ASH stakeado = 1 voto |
| **Propuestas** | Crear propuestas de cambio |
| **Decisiones comunitarias** | Votar en: nuevas misiones, balance de recompensas, distribución de treasury, partnerships |
| **Acceso Premium** | Features exclusivos (futuro) |
| **Treasury Management** | Participación en decisiones de tesorería |

### 7.4 Poder de Voto

```
Poder de Voto = ASH stakeado × multiplicador de tiempo

Multiplicadores:
- 1 mes stake:   1.0x
- 3 meses stake: 1.25x
- 6 meses stake: 1.5x
- 12 meses stake: 2.0x
```

### 7.5 Estado Actual

> **NOTA**: El protocolo ASH está actualmente **DESHABILITADO** (ASH_PROTOCOL_ENABLED = False) durante la fase beta. Se activará en una actualización futura.

---

## 8. SISTEMA DE RANKINGS

### 8.1 Ranking de Guilds

Las 6 guilds compiten por la supremacía basada en el desempeño colectivo de sus miembros.

**Métricas de Ranking:**

| Métrica | Descripción | Peso |
|---------|-------------|------|
| **XP Total** | Suma de XP de todos los miembros activos | Principal |
| **Aura Total** | Suma de Aura de todos los miembros | Secundario |
| **Success Rate** | % de misiones exitosas | Terciario |
| **Miembros Activos** | Jugadores con actividad reciente | Bonus |

**Clasificación Actual:**

| Posición | Guild | Miembros | Filosofía |
|----------|-------|----------|-----------|
| 1 | Circle of Mist | 10,599 | Conocimiento arcano |
| 2 | Order of Dawn | 6,341 | Protección sagrada |
| 3 | Shadow Guild | 6,234 | Información y sigilo |
| 4 | Forge Legion | 4,538 | Fuerza militar |
| 5 | Void Echoes | 4,302 | Artes oscuras |
| 6 | Horizon Watch | 2,986 | Exploración |

### 8.2 Leaderboard de Jugadores

**Métricas individuales:**

| Métrica | Descripción |
|---------|-------------|
| XP Total (All Heroes) | Suma de XP de todos los héroes del jugador |
| Aura Total (All Heroes) | Suma de Aura de todos los héroes |
| Heroes Count | Cantidad de NFTs que posee |
| Missions Completed | Total de misiones completadas |

**Títulos por Rango:**

| XP Total | Título |
|----------|--------|
| 0 - 999 | Initiate |
| 1,000 - 4,999 | Apprentice |
| 5,000 - 14,999 | Journeyman |
| 15,000 - 49,999 | Expert |
| 50,000 - 149,999 | Master |
| 150,000+ | Grandmaster |

### 8.3 Cálculo de Nivel Individual

```
Nivel = 1 + (XP Total ÷ 1,000)
```

| XP | Nivel |
|----|-------|
| 0-999 | 1 |
| 1,000-1,999 | 2 |
| 2,000-2,999 | 3 |
| 10,000-10,999 | 11 |
| 50,000-50,999 | 51 |

### 8.4 Sistema de Rangos por NFT (Emissary Rank)

Cada NFT individual tiene un **rango** que determina bonificaciones de recompensas.

#### Rangos y Requisitos

| Rango | Tier | XP Requerido | Aura Req. | Misiones | Bonus $EMBER |
|-------|------|--------------|-----------|----------|--------------|
| **Novice** | Tier 1 | 0 | 0 | 0 | +2% |
| **Apprentice** | Tier 2 | 1,000 | 50 | 5 | +5% |
| **Journeyman** | Tier 3 | 5,000 | 150 | 15 | +10% |
| **Adept** | Tier 4 | 15,000 | 400 | 35 | +15% |
| **Expert** | Tier 5 | 35,000 | 800 | 60 | +22% |
| **Master** | Tier 6 | 70,000 | 1,500 | 100 | +30% |
| **Grandmaster** | Tier 7 | 120,000 | 3,000 | 150 | +40% |
| **Legendary** | Tier 8 | 200,000 | 5,000 | 250 | +50% |

> Para subir de rango se requiere cumplir **TODOS** los requisitos (XP + Aura + Misiones).

#### Beneficios por Rango

| Rango | $EMBER% | XP% | Éxito% | Muerte% | Descripción |
|-------|---------|-----|--------|---------|-------------|
| Novice | +2% | +0% | +0% | 0% | "Recién llegado al reino" |
| Apprentice | +5% | +2% | +1% | -1% | "Aprendiendo los caminos" |
| Journeyman | +10% | +5% | +2% | -2% | "Viajero experimentado" |
| Adept | +15% | +8% | +4% | -3% | "Domina las artes básicas" |
| Expert | +22% | +12% | +6% | -5% | "Reconocido en el reino" |
| Master | +30% | +18% | +8% | -8% | "Maestro de su oficio" |
| Grandmaster | +40% | +25% | +10% | -12% | "Leyenda viviente" |
| Legendary | +50% | +35% | +12% | -15% | "Inmortalizado en la historia" |

#### Visualización del Rango

El rango aparece en:
- **Metadata del NFT**: Visible en OpenSea como trait
- **Interfaz del juego**: Junto al nombre del héroe
- **Leaderboards**: Como indicador de progreso

#### Fórmula de Cálculo

```
function getEmissaryRank(xp, aura, missions):
    if xp >= 200000 AND aura >= 5000 AND missions >= 250:
        return "Legendary (Tier 8)"
    elif xp >= 120000 AND aura >= 3000 AND missions >= 150:
        return "Grandmaster (Tier 7)"
    elif xp >= 70000 AND aura >= 1500 AND missions >= 100:
        return "Master (Tier 6)"
    elif xp >= 35000 AND aura >= 800 AND missions >= 60:
        return "Expert (Tier 5)"
    elif xp >= 15000 AND aura >= 400 AND missions >= 35:
        return "Adept (Tier 4)"
    elif xp >= 5000 AND aura >= 150 AND missions >= 15:
        return "Journeyman (Tier 3)"
    elif xp >= 1000 AND aura >= 50 AND missions >= 5:
        return "Apprentice (Tier 2)"
    else:
        return "Novice (Tier 1)"
```

#### Tiempo Estimado para Alcanzar Rangos

| Rango | Tiempo Estimado | Misiones Aprox. |
|-------|-----------------|-----------------|
| Novice → Apprentice | ~1 semana | 5-10 |
| Apprentice → Journeyman | ~3 semanas | 15-25 |
| Journeyman → Adept | ~2 meses | 35-50 |
| Adept → Expert | ~4 meses | 60-80 |
| Expert → Master | ~8 meses | 100-120 |
| Master → Grandmaster | ~1 año | 150-180 |
| Grandmaster → Legendary | ~2 años | 250+ |

> Los tiempos asumen juego activo diario con misiones de dificultad media-alta.

---

## 9. SISTEMA DE ACHIEVEMENTS

### 9.1 Logros Disponibles

| ID | Nombre | Requisito | Icono |
|----|--------|-----------|-------|
| `first_mission` | First Mission | Completar 1ra misión | 🎯 |
| `10_missions` | Veteran Explorer | Completar 10 misiones | ⚔️ |
| `50_missions` | Seasoned Warrior | Completar 50 misiones | 🏆 |
| `100_missions` | Legendary Hero | Completar 100 misiones | 👑 |
| `reach_level_10` | Level 10 Achieved | Alcanzar nivel 10 | ⭐ |
| `reach_level_50` | Level 50 Achieved | Alcanzar nivel 50 | 💫 |
| `guild_master` | Guild Master | Convertirse en líder de guild | 🏅 |
| `dragon_slayer` | Dragon Slayer | Derrotar dragón legendario | 🐉 |
| `void_walker` | Void Walker | Completar todas las misiones Void Echoes | 🌌 |
| `forge_master` | Forge Master | Completar todas las misiones Forge Legion | ⚒️ |

### 9.2 Mecánicas de Achievements

- **Auto-otorgados**: Se desbloquean automáticamente al cumplir requisitos
- **Almacenamiento**: Guardados en `achievements.json` por token_id
- **Visibilidad**: Aparecen en la metadata del NFT en OpenSea
- **Progresión**: Representan hitos importantes del héroe

### 9.3 Achievements Especiales

| Achievement | Dificultad | Requisito Especial |
|-------------|------------|---------------------|
| Dragon Slayer | Muy Alta | Completar "Dragons Crucible" en HARD |
| Void Walker | Alta | 5+ misiones de Void Echoes |
| Guild Master | Épica | Top 1 en ranking de tu guild |
| Legendary Hero | Épica | 100 misiones = ~1,200 horas de gameplay |

---

## 10. INFRAESTRUCTURA TÉCNICA

### 10.1 Arquitectura General

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

### 10.2 Smart Contracts (Base Mainnet)

| Contrato | Dirección | Función |
|----------|-----------|---------|
| **EmberholmPortal** | `0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3` | NFTs ERC721 (35,000) |
| **EmberToken** | `0xbA7723fBfb44C7712C0B78108ad873DcFd5Dd73b` | Token $EMBER ERC20 |
| **AshToken** | `0xD4eef3eadb1Cf1B2905AA4Cd1022b8cCCC739DAb` | Token $ASH ERC20 |
| **EmberRunes** | `0xDa2D1085053c3700645a13498293D17c1cc3f595` | NFTs de Runas |
| **EmberItems** | `0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA` | NFTs de Items |

### 10.3 Costos para el Usuario

#### Costo de Minteo

| Concepto | Valor |
|----------|-------|
| Precio por NFT | 0.0011 ETH (~$2-3 USD) |
| Gas estimado | ~0.0002-0.0005 ETH |
| Máx. por transacción | 10 NFTs |
| Supply total | 35,000 NFTs |

#### Costos de Transacción (Estimados en Base L2)

| Operación | Gas Estimado | Costo ~USD |
|-----------|--------------|------------|
| Mint 1 NFT | ~100,000 gas | ~$0.02-0.05 |
| Stake Token | ~50,000 gas | ~$0.01-0.02 |
| Claim Item/Rune | ~80,000 gas | ~$0.02-0.03 |
| Equipar Item | ~60,000 gas | ~$0.01-0.02 |
| Revivir héroe | ~70,000 gas | ~$0.01-0.03 |

> Base L2 ofrece costos **~100x menores** que Ethereum mainnet.

### 10.4 Base de Datos PostgreSQL

#### Esquema de Tablas

**Tabla `nfts`** (35,000+ registros)
```sql
CREATE TABLE nfts (
    token_id VARCHAR(5) PRIMARY KEY,
    owner_address VARCHAR(42),
    guild VARCHAR(50),
    dynamic_state JSONB,
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
    player_data JSONB,
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

### 10.5 Flujo de Persistencia de Datos

```
1. Usuario conecta wallet → Frontend llama tokensOfOwner()
2. Frontend envía POST /api/player/{wallet}
3. Backend sincroniza con PostgreSQL
4. Backend recalcula stats y rankings
5. Usuario juega → dynamic_state se actualiza
6. Metadata dinámica disponible via /api/metadata/{id}
7. OpenSea y marketplaces ven cambios en tiempo real
```

### 10.6 Almacenamiento IPFS

| Contenido | CID |
|-----------|-----|
| Items Metadata | `bafybeibs6mm5rghbpld7twbj35dbpryrfimmqkbnkev6ufs4kpbp343wfm` |
| Items Images | `bafybeiegbqf3ypcn7uukahdf275yrmxu2g4zt4xmmrfwguufppbhzs4yx4` |
| Runes Metadata | `bafybeiajq22kxgm764srr55wsiz4t65so5laxe2nmrryzgailzpmfes3nq` |
| Runes Images | `bafybeibmivzieas7beofrxspoqo5iughrzyvg3wgjibe626eqt37zg3sae` |

### 10.7 Stack Tecnológico Completo

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

## 11. RESUMEN EJECUTIVO Q&A

### Preguntas Generales

**Q: ¿Qué es Emberholm Portal?**
> A: Un RPG medieval de fantasía play-to-earn donde 35,000 NFTs únicos (Emissaries) completan misiones para ganar tokens $EMBER, progresar y determinar el destino de un reino amenazado por el Vacío.

**Q: ¿Cuánto cuesta empezar a jugar?**
> A: El minteo de un Emissary cuesta 0.0011 ETH (~$2-3 USD) + gas fees mínimos en Base (~$0.02-0.05).

**Q: ¿Cuántos NFTs existen?**
> A: 35,000 Emissaries únicos con diferentes razas, clases, guilds y estadísticas.

**Q: ¿Los NFTs cambian con el tiempo?**
> A: Sí, tienen **metadata dinámica**. XP, Aura, nivel, equipamiento y logros se actualizan en tiempo real y se reflejan en marketplaces como OpenSea.

### Preguntas de Gameplay

**Q: ¿Cómo funcionan las misiones?**
> A: Los héroes se envían a misiones de 3-12 horas. Al completarse, ganan XP, Aura, $EMBER, y tienen chance de dropear items/runas.

**Q: ¿Qué pasa si mi héroe muere?**
> A: El héroe queda en estado FALLEN. Puedes resucitarlo pagando $EMBER. El costo aumenta con cada muerte (200 EMBER primera vez, hasta 10,000 EMBER la sexta+).

**Q: ¿Cuál es la mejor dificultad para farmear?**
> A: Depende de tu objetivo:
> - **Items Legendary**: PARTY (2.5% probabilidad)
> - **Seguridad**: EASY (0% muerte, 92% éxito)
> - **Balance XP/$EMBER**: MEDIUM (150 XP, 30-75 EMBER)
> - **Máximo $EMBER**: HARD (80-200 EMBER, 2% muerte)

**Q: ¿Cómo maximizo las recompensas?**
> A: Alinea guild/clase/raza con la misión (1.5x multiplicador), equipa items Legendary (+18% EMBER), usa Party missions (1.2x bonus), y haz Ember Rolls (EV +200).

### Preguntas Económicas

**Q: ¿Cómo gano $EMBER?**
> A: Tres formas principales:
> 1. **Misiones**: 10-200 EMBER por misión según dificultad
> 2. **Ember Roll**: Sistema D20 con EV +200 EMBER/tirada
> 3. **Staking** (futuro): 10-70 EMBER/día por NFT según lock

**Q: ¿Qué puedo hacer con $EMBER?**
> A: Comprar energía, hacer Ember Rolls, resucitar héroes caídos, y convertir 1,000 EMBER en 1 $ASH.

**Q: ¿Qué es $ASH?**
> A: El token de gobernanza. Se obtiene quemando $EMBER (1,000:1). Permite votar en decisiones del DAO.

**Q: ¿Hay inflación de tokens?**
> A: Controlada. Supply de 100M con emisiones decrecientes (40M en 4 años). Mecanismos de quema en crafting, resurrecciones y marketplace fees.

### Preguntas Técnicas

**Q: ¿Dónde se guardan mis datos?**
> A: Propiedad on-chain (Base). Progreso (XP, Aura) en PostgreSQL. Metadatos e imágenes en IPFS.

**Q: ¿Los NFTs son realmente dinámicos?**
> A: Sí. La metadata se actualiza en tiempo real. Los cambios son visibles en OpenSea y otros marketplaces.

**Q: ¿Qué blockchain usa?**
> A: Base Mainnet (L2 de Ethereum). Transacciones rápidas y económicas (~$0.01-0.05).

**Q: ¿Es seguro?**
> A: Sí. NFTs ERC721 estándar. Durante misiones los tokens se stakean para prevenir transferencias. Contrato auditado con 5% royalty.

### Preguntas de Items/Runas

**Q: ¿Cuál es la diferencia entre Items y Runas?**
> A: Items dan bonuses específicos por tipo (arma = ataque). Runas dan bonus balanceado a TODOS los stats.

**Q: ¿Qué tan raro es obtener un Legendary?**
> A: EASY: 0.05% | MEDIUM: 0.30% | HARD: 1.40% | PARTY: 2.50%

**Q: ¿Los items están on-chain?**
> A: Sí. Contratos EmberItems y EmberRunes. Claims firmados criptográficamente.

### Preguntas de Rankings

**Q: ¿Cómo funcionan los rankings?**
> A: Hay ranking de guilds (por XP total de miembros) y leaderboard de jugadores (por XP de todos sus héroes).

**Q: ¿Qué beneficios dan los logros?**
> A: Los achievements aparecen en la metadata del NFT y representan hitos. Son marcadores de prestigio visibles en marketplaces.

### Preguntas de Rangos de NFT

**Q: ¿Qué es el Emissary Rank?**
> A: Cada NFT tiene un rango individual (Tier 1-8) basado en su XP, Aura y misiones completadas. A mayor rango, mayores bonificaciones.

**Q: ¿Cuántos rangos existen?**
> A: 8 rangos: Novice (Tier 1), Apprentice (Tier 2), Journeyman (Tier 3), Adept (Tier 4), Expert (Tier 5), Master (Tier 6), Grandmaster (Tier 7), Legendary (Tier 8).

**Q: ¿Qué bonus da el rango máximo?**
> A: Legendary (Tier 8) da: +50% $EMBER, +35% XP, +12% éxito, -15% muerte. Requiere 200,000 XP, 5,000 Aura y 250 misiones.

**Q: ¿Cuánto tiempo toma llegar a Legendary?**
> A: Aproximadamente 2+ años de juego activo. Es el máximo prestigio alcanzable.

**Q: ¿El rango afecta el valor del NFT?**
> A: Sí. Un NFT con rango alto tiene más valor porque produce más $EMBER y tiene mejor desempeño en misiones. El rango es visible en la metadata.

---

## ANEXO: FÓRMULAS CLAVE

### Nivel
```
nivel = 1 + (xp_total ÷ 1,000)
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
recompensa_party = recompensa_base × 1.2 (solo en éxito)
```

### Conversión ASH
```
ASH = EMBER_quemado ÷ 1,000
```

### Valor Esperado Ember Roll
```
EV = +200 $EMBER por tirada gratuita
EV_neto = +125 $EMBER por tirada pagada (200 - 75 costo)
```

### Cálculo de Rango de NFT (Emissary Rank)
```
Rango = max_tier donde:
  - XP >= xp_requerido[tier]
  - Aura >= aura_requerido[tier]
  - Misiones >= misiones_requerido[tier]

Bonus Total = ember_bonus[tier] + xp_bonus[tier] + exito_bonus[tier] - muerte_reduccion[tier]
```

### Bonus Acumulativo Total
```
Bonus_Final = (1 + Rango%) × (1 + Equipo%) × (1 + Runas%) × (1 + Alineamiento%)

Ejemplo Máximo:
= (1 + 0.50) × (1 + 0.90) × (1 + 0.30) × (1 + 0.50)
= 1.50 × 1.90 × 1.30 × 1.50
= 5.56x (456% bonus sobre base)
```

---

*Documento generado para presentación del proyecto Emberholm Portal*
*Versión 2.0 | Enero 2026*
