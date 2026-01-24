# SISTEMA ECONOMICO DE MISIONES
## Emberholm Portal - Reporte Detallado

---

## TABLA DE CONTENIDOS

1. [Resumen del Sistema](#1-resumen-del-sistema)
2. [Misiones por Dificultad](#2-misiones-por-dificultad)
3. [Calculo de Tasa de Exito](#3-calculo-de-tasa-de-exito)
4. [Sistema de Recompensas](#4-sistema-de-recompensas)
5. [Sistema de Drops (Items/Runas)](#5-sistema-de-drops-itemsrunas)
6. [Modificadores y Bonuses](#6-modificadores-y-bonuses)
7. [Analisis de Valor Esperado](#7-analisis-de-valor-esperado)
8. [Estrategias Optimas](#8-estrategias-optimas)

---

## 1. RESUMEN DEL SISTEMA

### Flujo de una Mision

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CICLO DE MISION                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. INICIO                                                           │
│     └── Consumo de Energia (10/18/25 segun dificultad)              │
│                                                                      │
│  2. DURACION                                                         │
│     └── Tiempo real (3h/6h/12h segun dificultad)                    │
│                                                                      │
│  3. RESOLUCION                                                       │
│     ├── Roll de exito vs tasa de exito                              │
│     └── Si falla MEDIUM/HARD: Roll de muerte                        │
│                                                                      │
│  4. RESULTADO                                                        │
│     ├── EXITO: +XP, +Aura, +$EMBER claimable, chance de drop        │
│     ├── FALLO: -XP (segun dificultad), sin otras recompensas        │
│     └── MUERTE: Estado FALLEN, requiere resurreccion                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. MISIONES POR DIFICULTAD

### Tabla Comparativa Completa

| Atributo | EASY | MEDIUM | HARD | PARTY |
|----------|------|--------|------|-------|
| **Duracion** | 3 horas | 6 horas | 12 horas | Variable |
| **Energia** | 10 | 18 | 25 | Base x5 |
| **XP Base** | 60 | 150 | 350 | Base x1.2 |
| **Aura Base** | 4 | 10 | 25 | Base x1.2 |
| **$EMBER Rango** | 10-25 | 30-75 | 80-200 | Base x1.2 |
| **Tasa Exito Base** | 92% | 78% | 60% | Variable |
| **Riesgo Muerte** | 0% | 0.5% | 2.0% | Segun base |
| **XP Perdido (fallo)** | -25 | -60 | -140 | Segun base |
| **Drop Item** | 5% | 10% | 20% | 25% |
| **Drop Runa** | 1% | 3% | 8% | 12% |

### Misiones Disponibles (Configuracion Actual)

#### EASY (3 misiones)

| ID | Nombre | Guild Favorecida | Clase | Raza |
|----|--------|------------------|-------|------|
| 001 | The Lost Forge | Forge Legion | Warrior | Orc |
| 002 | Circle Interference Node | Circle of Mist | Wizard | Human |
| 003 | Dawn Patrol (PARTY) | Order of Dawn | Paladin | Elf |

#### MEDIUM (3 misiones)

| ID | Nombre | Guild Favorecida | Clase | Raza |
|----|--------|------------------|-------|------|
| 004 | Shadow Infiltration | Shadow Guild | Rogue | Halfling |
| 005 | Horizon Survey | Horizon Watch | Ranger | Elf |
| 006 | Veil Breach Containment (PARTY) | Void Echoes | Necromancer | Undead |

#### HARD (3 misiones)

| ID | Nombre | Guild Favorecida | Clase | Raza |
|----|--------|------------------|-------|------|
| 007 | Dragons Crucible | Forge Legion | Warrior | Orc |
| 008 | Void Descent | Void Echoes | Necromancer | Undead |
| 009 | Eclipse Ritual (PARTY) | Circle of Mist | Wizard | Human |

---

## 3. CALCULO DE TASA DE EXITO

### Formula Principal

```
Tasa Final = min(98%, Tasa Base + Bonificaciones)
```

> **Nota**: La tasa de exito tiene un tope maximo de 98%. Siempre hay un 2% de riesgo de fallo.

### Bonificaciones Aplicables

| Factor | Bonus | Condicion |
|--------|-------|-----------|
| **Guild Match** | +12% | Guild del heroe = Guild favorecida de mision |
| **Class Match** | +8% | Clase del heroe = Clase favorecida |
| **Race Match** | +5% | Raza del heroe = Raza favorecida |
| **Nivel** | +1% por cada 10 niveles | Calculado desde XP total |
| **Aura** | +1% por cada 100 Aura | Aura acumulada del heroe |
| **Equipo** | Variable | Attack bonus de items equipados |
| **Ember Roll Buff** | Variable | Si tiene buff activo de Ember Roll |

### Ejemplo de Calculo

```
Mision: Dragons Crucible (HARD)
Tasa Base: 60%

Heroe:
- Guild: Forge Legion (MATCH) → +12%
- Clase: Warrior (MATCH) → +8%
- Raza: Orc (MATCH) → +5%
- Nivel: 35 (35 ÷ 10 = 3) → +3%
- Aura: 250 (250 ÷ 100 = 2) → +2%
- Equipo: Attack +5 → +5%

Calculo:
60% + 12% + 8% + 5% + 3% + 2% + 5% = 95%

Tasa Final: 95% (por debajo del cap de 98%)
```

### Alineamiento Perfecto

Cuando **Guild + Clase + Raza** coinciden con la mision:

- **Multiplicador de recompensas: 1.5x**
- Aplica a: XP, Aura, y $EMBER

```
Ejemplo con Perfect Alignment:
- XP Base: 350 → 350 x 1.5 = 525 XP
- Aura Base: 25 → 25 x 1.5 = 37 Aura
- $EMBER Base: 140 → 140 x 1.5 = 210 $EMBER
```

---

## 4. SISTEMA DE RECOMPENSAS

### XP y Aura

| Dificultad | XP Exito | Aura Exito | XP Fallo |
|------------|----------|------------|----------|
| EASY | 60 | 4 | -25 |
| MEDIUM | 150 | 10 | -60 |
| HARD | 350 | 25 | -140 |

### $EMBER por Mision

Las recompensas de $EMBER se calculan con variabilidad:

| Dificultad | Minimo | Maximo | Promedio |
|------------|--------|--------|----------|
| EASY | 10 | 25 | ~17.5 |
| MEDIUM | 30 | 75 | ~52.5 |
| HARD | 80 | 200 | ~140 |

### Bonuses que Afectan $EMBER

| Fuente | Bonus Maximo |
|--------|--------------|
| Perfect Alignment | +50% (x1.5) |
| Equipo Legendary | +18% por pieza |
| Runas Legendary | +18% por runa |
| Rank (Legendary Tier 8) | +50% |
| Party Mission | +20% |

### Calculo de $EMBER Maximo Teorico

```
Base HARD: 200 $EMBER
+ Perfect Alignment (x1.5): 300
+ Legendary Weapon (+18%): 354
+ Legendary Armor (+18%): 417
+ Legendary Helmet (+18%): 492
+ Legendary Accessory (+18%): 580
+ Legendary Amulet (+18%): 685
+ 2x Legendary Runes (+36%): 931
+ Rank Legendary (+50%): 1,396
+ Party Bonus (+20%): 1,676 $EMBER

MAXIMO TEORICO POR MISION: ~1,676 $EMBER
(Requiere: Perfect alignment, full legendary gear, Rank 8, Party mission)
```

---

## 5. SISTEMA DE DROPS (ITEMS/RUNAS)

### Probabilidades de Drop

| Dificultad | Item Drop | Runa Drop |
|------------|-----------|-----------|
| EASY | 5% | 1% |
| MEDIUM | 10% | 3% |
| HARD | 20% | 8% |
| PARTY | 25% | 12% |

### Distribucion de Rareza (al obtener drop)

| Dificultad | Common | Rare | Epic | Legendary |
|------------|--------|------|------|-----------|
| EASY | 70% | 25% | 4% | 1% |
| MEDIUM | 50% | 35% | 12% | 3% |
| HARD | 30% | 40% | 23% | 7% |
| PARTY | 20% | 40% | 30% | 10% |

### Probabilidad Combinada (Drop x Rareza)

**Obtener un Item Legendary:**

| Dificultad | Calculo | Probabilidad |
|------------|---------|--------------|
| EASY | 5% x 1% | **0.05%** |
| MEDIUM | 10% x 3% | **0.30%** |
| HARD | 20% x 7% | **1.40%** |
| PARTY | 25% x 10% | **2.50%** |

**Obtener una Runa Legendary:**

| Dificultad | Calculo | Probabilidad |
|------------|---------|--------------|
| EASY | 1% x 1% | **0.01%** |
| MEDIUM | 3% x 3% | **0.09%** |
| HARD | 8% x 7% | **0.56%** |
| PARTY | 12% x 10% | **1.20%** |

---

## 6. MODIFICADORES Y BONUSES

### Bonuses de Equipo por Rareza

#### Items

| Rareza | $EMBER% | XP% | Energia% | Muerte% | Velocidad% |
|--------|---------|-----|----------|---------|------------|
| Common | +3% | +2% | 0% | 0% | 0% |
| Uncommon | +5% | +4% | -2% | 0% | 0% |
| Rare | +8% | +6% | -3% | -2% | 0% |
| Epic | +12% | +10% | -5% | -4% | +3% |
| Legendary | +18% | +15% | -8% | -6% | +5% |

#### Runas (Balanceadas)

| Rareza | $EMBER% | XP% | Energia% | Muerte% | Velocidad% |
|--------|---------|-----|----------|---------|------------|
| Common | +3% | +3% | -2% | -2% | +2% |
| Uncommon | +5% | +5% | -3% | -3% | +3% |
| Rare | +8% | +8% | -5% | -5% | +5% |
| Epic | +12% | +12% | -8% | -8% | +8% |
| Legendary | +18% | +18% | -12% | -12% | +12% |

### Bonuses de Rango (Emissary Rank)

| Rango | Tier | $EMBER% | XP% | Exito% | Muerte% |
|-------|------|---------|-----|--------|---------|
| Novice | 1 | +2% | +0% | +0% | 0% |
| Apprentice | 2 | +5% | +2% | +1% | -1% |
| Journeyman | 3 | +10% | +5% | +2% | -2% |
| Adept | 4 | +15% | +8% | +4% | -3% |
| Expert | 5 | +22% | +12% | +6% | -5% |
| Master | 6 | +30% | +18% | +8% | -8% |
| Grandmaster | 7 | +40% | +25% | +10% | -12% |
| Legendary | 8 | +50% | +35% | +12% | -15% |

---

## 7. ANALISIS DE VALOR ESPERADO

### Valor Esperado por Mision (Sin Bonuses)

```
EV = (Prob_Exito x Reward_Exito) + (Prob_Fallo x Penalty_Fallo)
```

#### EASY

```
Tasa Exito: 92%
Tasa Fallo: 8%
Muerte: 0%

EV_XP = (0.92 x 60) + (0.08 x -25) = 55.2 - 2 = 53.2 XP
EV_Aura = 0.92 x 4 = 3.68 Aura
EV_EMBER = 0.92 x 17.5 = 16.1 $EMBER

Por hora: 53.2/3 = 17.7 XP/h, 5.37 $EMBER/h
```

#### MEDIUM

```
Tasa Exito: 78%
Tasa Fallo: 21.5% (22% - 0.5% muerte)
Muerte: 0.5%

EV_XP = (0.78 x 150) + (0.215 x -60) = 117 - 12.9 = 104.1 XP
EV_Aura = 0.78 x 10 = 7.8 Aura
EV_EMBER = 0.78 x 52.5 = 40.95 $EMBER

Por hora: 104.1/6 = 17.35 XP/h, 6.83 $EMBER/h
```

#### HARD

```
Tasa Exito: 60%
Tasa Fallo: 38% (40% - 2% muerte)
Muerte: 2%

EV_XP = (0.60 x 350) + (0.38 x -140) = 210 - 53.2 = 156.8 XP
EV_Aura = 0.60 x 25 = 15 Aura
EV_EMBER = 0.60 x 140 = 84 $EMBER

Por hora: 156.8/12 = 13.07 XP/h, 7 $EMBER/h
```

### Tabla Resumen de Eficiencia

| Dificultad | XP/hora | Aura/hora | $EMBER/hora | Riesgo |
|------------|---------|-----------|-------------|--------|
| EASY | **17.7** | 1.23 | 5.37 | 0% |
| MEDIUM | 17.35 | 1.30 | 6.83 | 0.5% |
| HARD | 13.07 | **1.25** | **7.00** | 2% |

### Analisis por Objetivo

| Objetivo | Mejor Opcion | Razon |
|----------|--------------|-------|
| **Maximo XP/hora** | EASY | 17.7 XP/h, sin riesgo |
| **Maximo $EMBER/hora** | HARD | 7 $EMBER/h |
| **Maximo Items Legendary** | PARTY HARD | 2.5% probabilidad |
| **Sin riesgo de muerte** | EASY | 0% muerte |
| **Balance riesgo/recompensa** | MEDIUM | Riesgo moderado, buenas recompensas |

---

## 8. ESTRATEGIAS OPTIMAS

### Para Nuevos Jugadores (Nivel 1-10)

```
Recomendacion: EASY exclusivamente
- Sin riesgo de muerte
- Construir XP y Aura base
- Aprender mecanicas del juego
- Obtener primeros items (aunque sean Common)

Objetivo: Alcanzar Rank Apprentice (Tier 2)
Requisitos: 1,000 XP, 50 Aura, 5 misiones
Tiempo estimado: ~1 semana
```

### Para Jugadores Intermedios (Nivel 10-30)

```
Recomendacion: Mezcla EASY + MEDIUM
- Alternar segun energia disponible
- Usar MEDIUM cuando tengas Perfect Alignment
- EASY para grinding seguro
- Empezar a equipar items Rare/Epic

Objetivo: Alcanzar Rank Journeyman (Tier 3)
Requisitos: 5,000 XP, 150 Aura, 15 misiones
```

### Para Jugadores Avanzados (Nivel 30+)

```
Recomendacion: MEDIUM + HARD + PARTY
- HARD solo con buen equipo (proteccion muerte)
- PARTY para maximizar drops Legendary
- Enfocarse en Perfect Alignment siempre que sea posible

Objetivo: Alcanzar Rank Master+ (Tier 6+)
Prioridad: Farmear items Legendary para reducir riesgo
```

### Maximizar $EMBER

```
1. Equipa TODO Legendary (si es posible)
2. Busca misiones con Perfect Alignment
3. Usa Party Missions (+20% bonus)
4. Sube de Rank (hasta +50% en Tier 8)
5. Haz Ember Roll diario (primera tirada gratis, EV +200)

Configuracion Optima:
- 6 slots de equipo Legendary: +108% $EMBER
- 2 Runas Legendary: +36% $EMBER
- Rank Legendary: +50% $EMBER
- Perfect Alignment: +50% $EMBER
- Party Bonus: +20% $EMBER

Total Bonus: +264% sobre base
```

### Minimizar Riesgo de Muerte

```
Proteccion por Nivel:
- Nivel 10+: +5% proteccion
- Nivel 30+: +15% proteccion
- Nivel 50+: +30% proteccion

Proteccion por Aura:
- 100+ Aura: +5% proteccion
- 250+ Aura: +10% proteccion
- 500+ Aura: +20% proteccion

Proteccion por Equipo:
- Items Epic/Legendary reducen death_chance
- Runas dan -12% muerte (Legendary)

MAXIMO: 80% proteccion total

Con 80% proteccion en HARD (2% base):
Muerte efectiva = 2% x (1 - 0.80) = 0.4%
```

---

## FORMULAS CLAVE

### Tasa de Exito
```
success_rate = min(98%, base_rate + guild_bonus + class_bonus + race_bonus + level_bonus + aura_bonus + equipment_bonus)
```

### Recompensa de XP
```
xp_final = xp_base x alignment_multiplier x (1 + equipment_boost%) x (1 + rank_boost%)
```

### Recompensa de $EMBER
```
ember_final = ember_base x alignment_multiplier x (1 + equipment_boost%) x (1 + rank_boost%) x party_multiplier
```

### Probabilidad de Muerte Efectiva
```
death_effective = death_base x (1 - protection_total)
protection_total = min(80%, level_protection + aura_protection + equipment_protection)
```

### Valor Esperado de Mision
```
EV = (success_rate x reward) + ((1 - success_rate - death_rate) x penalty) + (death_rate x death_cost)
```

---

*Documento de Economia de Misiones — Emberholm Portal*
*Basado en missions_config.json y app.py*
*Version 1.0 | Enero 2026*
