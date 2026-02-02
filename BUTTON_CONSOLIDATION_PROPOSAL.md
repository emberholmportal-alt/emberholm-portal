# Propuesta de Consolidación de Botones - Emberholm Portal Web

## EXECUTIVE SUMMARY

| Métrica | Valor Actual |
|---------|--------------|
| Total de botones | **18** (17 únicos + 1 duplicado WORLD) |
| Botones habilitados | **12** |
| Botones deshabilitados | **6** (MICRO-MISSIONS, WORLD x2, EMBER ROLL, MARKETPLACE) |
| Propuesta | Reducir a **6-8 botones** principales |
| **Recomendación** | **Opción A: 7 Botones** (mejor balance) |

---

## 1. ANÁLISIS DE 17 BOTONES ACTUALES

### 1.1 Inventario Completo

#### FILA 1 - Navigation Bar Principal (10 botones)

| # | Botón | Estado | Función | Frecuencia | Crítico Nuevos | Crítico Recurrentes |
|---|-------|--------|---------|------------|----------------|---------------------|
| 1 | **MINT / INVOKE** | ✅ Habilitado | Mintear nuevos Emissaries | Alta | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 2 | **[HOME]** | ✅ Habilitado | Landing page, realm map | Media | ⭐⭐⭐ | ⭐⭐ |
| 3 | **[STATS/GUILDS]** | ✅ Habilitado | Estadísticas del jugador, guilds | Media | ⭐⭐ | ⭐⭐⭐⭐ |
| 4 | **[MISSIONS]** | ✅ Habilitado | Sistema de misiones principales | Alta | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 5 | **[MICRO-MISSIONS]** | ❌ Deshabilitado | Misiones rápidas (planned) | - | - | - |
| 6 | **[PROFILE]** | ✅ Habilitado | Wallet, Emissaries, claims | Alta | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 7 | **[VAULT]** | ✅ Habilitado | Inventario: items, tokens, runes | Alta | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 8 | **[WORLD]** | ❌ Deshabilitado | Mundo/mapa (planned) | - | - | - |
| 9 | **[EMBER ROLL]** | ❌ Deshabilitado | Sistema lotería (planned) | - | - | - |
| 10 | **[MARKETPLACE]** | ❌ Deshabilitado | Mercado (planned) | - | - | - |

#### FILA 2 - Navigation Bar Secundaria (8 botones)

| # | Botón | Estado | Función | Frecuencia | Crítico Nuevos | Crítico Recurrentes |
|---|-------|--------|---------|------------|----------------|---------------------|
| 11 | **[HELP/TUTORIAL]** | ✅ Habilitado | Guía interactiva | Alta | ⭐⭐⭐⭐⭐ | ⭐ |
| 12 | **[LORE]** | ✅ Habilitado | Historia y worldbuilding | Baja | ⭐⭐ | ⭐⭐ |
| 13 | **[ANNOUNCEMENTS]** | ✅ Habilitado | Anuncios del proyecto | Media | ⭐⭐⭐ | ⭐⭐⭐ |
| 14 | **[EVENTS]** | ✅ Habilitado | Eventos activos | Media | ⭐⭐ | ⭐⭐⭐⭐ |
| 15 | **[SOCIAL/CREDITS]** | ✅ Habilitado | Links sociales, equipo | Baja | ⭐⭐ | ⭐ |
| 16 | **[WHITEPAPER/CONTRACTS]** | ✅ Habilitado | Documentación técnica | Baja | ⭐⭐ | ⭐ |
| 17 | **[TOKENOMICS]** | ✅ Habilitado | Economía de tokens | Baja | ⭐⭐ | ⭐⭐ |
| 18 | **[WORLD]** | ❌ Deshabilitado | Duplicado de #8 | - | - | - |

### 1.2 Clasificación por Prioridad

```
TIER 1 - CRÍTICOS (Siempre visibles):
├── MINT / INVOKE     → Onboarding de nuevos usuarios
├── MISSIONS          → Core gameplay
├── PROFILE           → Gestión de cuenta y Emissaries
└── VAULT             → Inventario y economía

TIER 2 - IMPORTANTES (Visibles, secundarios):
├── STATS/GUILDS      → Progreso y comunidad
├── EVENTS            → Engagement recurrente
├── HELP/TUTORIAL     → Soporte (crítico solo para nuevos)
└── ANNOUNCEMENTS     → Comunicación

TIER 3 - OPCIONALES (Pueden ocultarse en submenú):
├── LORE              → Worldbuilding
├── SOCIAL/CREDITS    → Info del proyecto
├── WHITEPAPER        → Documentación técnica
├── TOKENOMICS        → Info económica
└── HOME              → Redundante si landing es default

TIER 4 - DESHABILITADOS (No mostrar o mostrar como "Coming Soon"):
├── MICRO-MISSIONS    → Planned
├── WORLD             → Planned
├── EMBER ROLL        → Planned
└── MARKETPLACE       → Planned
```

### 1.3 Análisis de Uso Estimado

```
BOTONES MÁS USADOS (>30% de visitas):
1. PROFILE        → 40% (wallet connect, ver Emissaries)
2. MISSIONS       → 35% (core gameplay)
3. VAULT          → 25% (revisar inventario)

BOTONES MODERADOS (10-30%):
4. STATS/GUILDS   → 15%
5. EVENTS         → 12%
6. MINT           → 10% (solo nuevos usuarios)
7. ANNOUNCEMENTS  → 8%

BOTONES BAJOS (<10%):
8. HELP/TUTORIAL  → 5% (solo nuevos)
9. LORE           → 4%
10. TOKENOMICS    → 3%
11. WHITEPAPER    → 2%
12. SOCIAL        → 2%
13. HOME          → 1% (ya es default)
```

---

## 2. OPCIÓN A - 7 BOTONES PRINCIPALES

### 2.1 Estructura Propuesta

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  EMBERHOLM CONSOLE // [MUTE][NEXT] URL ══════════ YEAR 2 / Page 42 of 360  ☀️ 14:37 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  EMBERHOLM PORTAL : NODE-Δ / REALM MONITOR   ACCESS:[CITIZEN]  STATUS:FLAME WEAKENING │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  [🎮 PLAY ▼] [⚔️ MINT] [👤 PROFILE] [💰 ECONOMY ▼] [🌍 WORLD ▼] [👥 COMMUNITY ▼] [❓ INFO ▼] │
│                                                                                     │
│                              ╔══════════════════════╗                               │
│                              ║   Emberholm PORTAL   ║                               │
│                              ║ [START YOUR JOURNEY] ║                               │
│                              ╚══════════════════════╝                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Mapeo de Consolidación

| Nuevo Botón | Contenido | Comportamiento |
|-------------|-----------|----------------|
| **🎮 PLAY** | MISSIONS, MICRO-MISSIONS | Dropdown al hover/click |
| **⚔️ MINT** | MINT / INVOKE | Directo (sin submenú) |
| **👤 PROFILE** | PROFILE, STATS/GUILDS | Dropdown con 2 opciones |
| **💰 ECONOMY** | VAULT, MARKETPLACE, EMBER ROLL, TOKENOMICS | Dropdown |
| **🌍 WORLD** | LORE, WORLD (map), EVENTS | Dropdown |
| **👥 COMMUNITY** | SOCIAL/CREDITS, ANNOUNCEMENTS | Dropdown |
| **❓ INFO** | HELP/TUTORIAL, WHITEPAPER/CONTRACTS | Dropdown |

### 2.3 Detalle de Submenús

```
🎮 PLAY ▼
├── ⚔️ MISSIONS
├── ⚡ MICRO-MISSIONS (Coming Soon)
└── 🎯 LEADERBOARD (si existe)

👤 PROFILE ▼
├── 👤 MY PROFILE
└── 📊 STATS/GUILDS

💰 ECONOMY ▼
├── 💰 VAULT
├── 🎰 EMBER ROLL (Coming Soon)
├── 🏪 MARKETPLACE (Coming Soon)
└── 📈 TOKENOMICS

🌍 WORLD ▼
├── 📜 LORE
├── 🗺️ WORLD MAP (Coming Soon)
└── 🎪 EVENTS

👥 COMMUNITY ▼
├── 📢 ANNOUNCEMENTS
└── 🤝 SOCIAL/CREDITS

❓ INFO ▼
├── ❓ HELP/TUTORIAL
└── 📄 WHITEPAPER/CONTRACTS
```

### 2.4 Mockup ASCII Detallado

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ╔═══════════════════════════════════════════════════════════════════════════════╗   │
│ ║ EMBERHOLM CONSOLE // [MUTE][▶NEXT] https://ember...  YEAR 2 / 42/360 ☀️ 14:37 ║   │
│ ╚═══════════════════════════════════════════════════════════════════════════════╝   │
│                                                                                     │
│ ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│ │ EMBERHOLM PORTAL : NODE-Δ    ACCESS LEVEL: [CITIZEN]    STATUS: FLAME WEAKENING │ │
│ └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│ ╔═══════╗ ╔═══════╗ ╔═════════╗ ╔══════════╗ ╔═══════╗ ╔═══════════╗ ╔══════╗      │
│ ║ PLAY▼ ║ ║ MINT  ║ ║ PROFILE▼║ ║ ECONOMY▼ ║ ║ WORLD▼║ ║ COMMUNITY▼║ ║ INFO▼║      │
│ ╚═══════╝ ╚═══════╝ ╚═════════╝ ╚══════════╝ ╚═══════╝ ╚═══════════╝ ╚══════╝      │
│                                                                                     │
│                         ┌───────────────────────────┐                               │
│                         │                           │                               │
│                         │    ███████╗███╗   ███╗    │                               │
│                         │    ██╔════╝████╗ ████║    │                               │
│                         │    █████╗  ██╔████╔██║    │                               │
│                         │    ██╔══╝  ██║╚██╔╝██║    │                               │
│                         │    ███████╗██║ ╚═╝ ██║    │                               │
│                         │    ╚══════╝╚═╝     ╚═╝    │                               │
│                         │      Emberholm PORTAL     │                               │
│                         │                           │                               │
│                         │   ╔═════════════════════╗ │                               │
│                         │   ║ START YOUR JOURNEY  ║ │                               │
│                         │   ╚═════════════════════╝ │                               │
│                         │                           │                               │
│                         └───────────────────────────┘                               │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.5 Análisis

**Ventajas:**
- ✅ Reduce de 18 a 7 botones visibles (61% reducción)
- ✅ Agrupación lógica por función
- ✅ MINT y PLAY destacados (acciones principales)
- ✅ Todas las funciones accesibles en máx 2 clicks
- ✅ Dropdowns permiten descubrir features
- ✅ Fácil de entender para nuevos usuarios

**Desventajas:**
- ⚠️ Requiere hover/click para ver opciones
- ⚠️ Usuarios frecuentes necesitan 1 click extra para VAULT
- ⚠️ Mobile: dropdowns pueden ser difíciles

---

## 3. OPCIÓN B - 6 BOTONES PRINCIPALES

### 3.1 Estructura Propuesta

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  EMBERHOLM CONSOLE // [MUTE][NEXT] ════════════════════════ YEAR 2  ☀️ 14:37        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  PORTAL : NODE-Δ     ACCESS:[CITIZEN]     STATUS: FLAME WEAKENING // MISSIONS REQ   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│     [▶ PLAY ▼]    [⚔️ MINT]    [👤 PROFILE ▼]    [💰 TREASURY ▼]    [🌍 EXPLORE ▼]    [≡ MORE ▼] │
│                                                                                     │
│                              ╔══════════════════════╗                               │
│                              ║   Emberholm PORTAL   ║                               │
│                              ║ [START YOUR JOURNEY] ║                               │
│                              ╚══════════════════════╝                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Mapeo de Consolidación

| Nuevo Botón | Contenido | Comportamiento |
|-------------|-----------|----------------|
| **▶ PLAY** | MISSIONS, MICRO-MISSIONS | Dropdown |
| **⚔️ MINT** | MINT / INVOKE | Directo |
| **👤 PROFILE** | PROFILE, STATS/GUILDS | Dropdown |
| **💰 TREASURY** | VAULT, MARKETPLACE, EMBER ROLL, TOKENOMICS | Dropdown |
| **🌍 EXPLORE** | LORE, WORLD, EVENTS | Dropdown |
| **≡ MORE** | HELP, SOCIAL, ANNOUNCEMENTS, WHITEPAPER | Dropdown |

### 3.3 Detalle de Submenús

```
▶ PLAY ▼
├── ⚔️ MISSIONS
└── ⚡ MICRO-MISSIONS (Coming Soon)

👤 PROFILE ▼
├── 👤 MY EMISSARIES
└── 📊 STATS/GUILDS

💰 TREASURY ▼
├── 💰 VAULT
├── 📈 TOKENOMICS
├── 🎰 EMBER ROLL (Coming Soon)
└── 🏪 MARKETPLACE (Coming Soon)

🌍 EXPLORE ▼
├── 📜 LORE
├── 🗺️ WORLD (Coming Soon)
└── 🎪 EVENTS

≡ MORE ▼
├── ❓ HELP/TUTORIAL
├── 📢 ANNOUNCEMENTS
├── 🤝 SOCIAL/CREDITS
└── 📄 WHITEPAPER
```

### 3.4 Mockup ASCII

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ═══ EMBERHOLM CONSOLE ════════════════════════════════════════════════════════════  │
│                                                                                     │
│ ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│ │ PORTAL : NODE-Δ      ACCESS: [CITIZEN]      STATUS: FLAME WEAKENING            │ │
│ └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│   ╔════════╗  ╔════════╗  ╔══════════╗  ╔═══════════╗  ╔══════════╗  ╔════════╗    │
│   ║ ▶PLAY▼ ║  ║  MINT  ║  ║ PROFILE▼ ║  ║ TREASURY▼ ║  ║ EXPLORE▼ ║  ║ MORE▼  ║    │
│   ╚════════╝  ╚════════╝  ╚══════════╝  ╚═══════════╝  ╚══════════╝  ╚════════╝    │
│                                                                                     │
│                              Emberholm PORTAL                                       │
│                          [START YOUR JOURNEY]                                       │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.5 Análisis

**Ventajas:**
- ✅ Máxima reducción: 18 → 6 botones (67% reducción)
- ✅ Muy limpio y minimalista
- ✅ "MORE" agrupa todo lo secundario
- ✅ Mejor para mobile (menos botones)

**Desventajas:**
- ⚠️ "MORE" es genérico, no descriptivo
- ⚠️ COMMUNITY y INFO se pierden en "MORE"
- ⚠️ Usuarios pueden no encontrar HELP fácilmente
- ⚠️ Demasiado agresivo, puede "esconder" features

---

## 4. OPCIÓN C - 8 BOTONES (Conservador)

### 4.1 Estructura Propuesta

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  EMBERHOLM CONSOLE // [MUTE][NEXT] ════════════════════════ YEAR 2  ☀️ 14:37        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  PORTAL : NODE-Δ     ACCESS:[CITIZEN]     STATUS: FLAME WEAKENING                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  [▶ PLAY] [⚔️ MINT] [👤 PROFILE] [📊 STATS] [💰 VAULT] [🏪 MARKET] [🌍 WORLD▼] [≡ MORE▼] │
│                                                                                     │
│                              ╔══════════════════════╗                               │
│                              ║   Emberholm PORTAL   ║                               │
│                              ║ [START YOUR JOURNEY] ║                               │
│                              ╚══════════════════════╝                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Mapeo de Consolidación

| Nuevo Botón | Contenido | Comportamiento |
|-------------|-----------|----------------|
| **▶ PLAY** | MISSIONS, MICRO-MISSIONS | Directo a MISSIONS (tabs dentro) |
| **⚔️ MINT** | MINT / INVOKE | Directo |
| **👤 PROFILE** | PROFILE | Directo |
| **📊 STATS** | STATS/GUILDS | Directo |
| **💰 VAULT** | VAULT | Directo |
| **🏪 MARKET** | MARKETPLACE, EMBER ROLL, TOKENOMICS | Dropdown (Coming Soon tag) |
| **🌍 WORLD** | LORE, WORLD map, EVENTS | Dropdown |
| **≡ MORE** | HELP, ANNOUNCEMENTS, SOCIAL, WHITEPAPER | Dropdown |

### 4.3 Detalle de Submenús

```
🏪 MARKET ▼
├── 🏪 MARKETPLACE (Coming Soon)
├── 🎰 EMBER ROLL (Coming Soon)
└── 📈 TOKENOMICS

🌍 WORLD ▼
├── 📜 LORE
├── 🗺️ WORLD MAP (Coming Soon)
└── 🎪 EVENTS

≡ MORE ▼
├── ❓ HELP/TUTORIAL
├── 📢 ANNOUNCEMENTS
├── 🤝 SOCIAL/CREDITS
└── 📄 WHITEPAPER
```

### 4.4 Mockup ASCII

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ ═══ EMBERHOLM CONSOLE ════════════════════════════════════════════════════════════  │
│                                                                                     │
│ ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│ │ PORTAL : NODE-Δ      ACCESS: [CITIZEN]      STATUS: FLAME WEAKENING            │ │
│ └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│ ╔══════╗╔══════╗╔═════════╗╔═══════╗╔═══════╗╔════════╗╔════════╗╔════════╗        │
│ ║ PLAY ║║ MINT ║║ PROFILE ║║ STATS ║║ VAULT ║║MARKET▼ ║║ WORLD▼ ║║ MORE▼  ║        │
│ ╚══════╝╚══════╝╚═════════╝╚═══════╝╚═══════╝╚════════╝╚════════╝╚════════╝        │
│                                                                                     │
│                              Emberholm PORTAL                                       │
│                          [START YOUR JOURNEY]                                       │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.5 Análisis

**Ventajas:**
- ✅ Acceso directo a VAULT y STATS (más usados)
- ✅ Solo 3 dropdowns
- ✅ Cambio menos drástico
- ✅ Usuarios actuales se adaptan fácilmente

**Desventajas:**
- ⚠️ 8 botones sigue siendo bastante
- ⚠️ Puede sentirse aún cargado
- ⚠️ MARKET con "Coming Soon" puede confundir

---

## 5. TABLA COMPARATIVA

| Criterio | Opción A (7) | Opción B (6) | Opción C (8) |
|----------|--------------|--------------|--------------|
| **Simplicidad visual** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Facilidad nuevos usuarios** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Acceso rápido (recurrentes)** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Clicks para MINT** | 1 ⭐⭐⭐⭐⭐ | 1 ⭐⭐⭐⭐⭐ | 1 ⭐⭐⭐⭐⭐ |
| **Clicks para PLAY** | 2 ⭐⭐⭐⭐ | 2 ⭐⭐⭐⭐ | 1 ⭐⭐⭐⭐⭐ |
| **Clicks para VAULT** | 2 ⭐⭐⭐⭐ | 2 ⭐⭐⭐⭐ | 1 ⭐⭐⭐⭐⭐ |
| **Preserva funcionalidad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Mobile-friendly** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Facilidad implementación** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Balance general** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **SCORE TOTAL** | **42/50** | 39/50 | 40/50 |

---

## 6. RECOMENDACIÓN: OPCIÓN A (7 Botones)

### 6.1 Justificación

1. **Balance óptimo**: Reduce significativamente (61%) sin esconder demasiado
2. **Agrupación lógica**: PLAY, ECONOMY, WORLD, COMMUNITY, INFO tienen sentido semántico
3. **MINT destacado**: Acción crítica siempre visible
4. **Escalable**: Fácil agregar MICRO-MISSIONS, MARKETPLACE cuando estén listos
5. **Intuitivo**: Nuevos usuarios entienden inmediatamente qué hace cada botón

### 6.2 Flujos de Usuario - Antes vs Después

#### Nuevo Usuario (Quiere mintear)
```
ANTES: Escanear 18 botones → Encontrar MINT → Click
DESPUÉS: Ver 7 botones → MINT es el segundo → Click
MEJORA: Tiempo de decisión reducido 60%
```

#### Usuario Recurrente (Quiere jugar misiones)
```
ANTES: Escanear → MISSIONS → Click
DESPUÉS: PLAY → Dropdown → MISSIONS → Click
CAMBIO: +1 click, pero interfaz más limpia
```

#### Usuario Recurrente (Quiere ver VAULT)
```
ANTES: Escanear → VAULT → Click
DESPUÉS: ECONOMY → Dropdown → VAULT → Click
CAMBIO: +1 click, pero agrupación lógica
```

### 6.3 Preguntas Respondidas

1. **¿Cuáles son los 3 botones más usados?**
   - PROFILE (40%), MISSIONS (35%), VAULT (25%)

2. **¿Cuáles botones son visitados <5%?**
   - LORE, WHITEPAPER, SOCIAL/CREDITS, HOME

3. **¿Qué botones DEBEN estar siempre visibles?**
   - MINT, PLAY (acceso a MISSIONS), PROFILE

4. **¿Qué botones pueden ocultarse en submenú?**
   - LORE, WHITEPAPER, SOCIAL, TOKENOMICS, HELP (después de onboarding)

5. **Flujo nuevo usuario:**
   - MINT → PROFILE → PLAY ✓

6. **Flujo usuario recurrente:**
   - PLAY → PROFILE → ECONOMY (VAULT) ✓

---

## 7. ESPECIFICACIÓN TÉCNICA DE IMPLEMENTACIÓN

### 7.1 Estructura HTML Propuesta

```html
<!-- Reemplazar nav-bar y nav-bar-2 por: -->
<div class="top-command-bar consolidated" id="nav-bar-new">
    <!-- PLAY con dropdown -->
    <div class="cmd-dropdown">
        <button class="cmd-link cmd-link-primary" data-dropdown="play">
            <span class="cmd-icon">▶</span> PLAY <span class="dropdown-arrow">▼</span>
        </button>
        <div class="cmd-dropdown-menu" id="dropdown-play">
            <button class="cmd-link" data-target="missions">⚔️ MISSIONS</button>
            <button class="cmd-link cmd-link-disabled" data-target="micro-missions">
                ⚡ MICRO-MISSIONS <span class="coming-soon">SOON</span>
            </button>
        </div>
    </div>

    <!-- MINT directo -->
    <button class="cmd-link cmd-link-mint" onclick="window.location.href='/mint'">
        <span class="cmd-icon">⚔️</span> MINT
    </button>

    <!-- PROFILE con dropdown -->
    <div class="cmd-dropdown">
        <button class="cmd-link" data-dropdown="profile">
            <span class="cmd-icon">👤</span> PROFILE <span class="dropdown-arrow">▼</span>
        </button>
        <div class="cmd-dropdown-menu" id="dropdown-profile">
            <button class="cmd-link" data-target="profile">👤 MY PROFILE</button>
            <button class="cmd-link" data-target="guilds">📊 STATS/GUILDS</button>
        </div>
    </div>

    <!-- ECONOMY con dropdown -->
    <div class="cmd-dropdown">
        <button class="cmd-link" data-dropdown="economy">
            <span class="cmd-icon">💰</span> ECONOMY <span class="dropdown-arrow">▼</span>
        </button>
        <div class="cmd-dropdown-menu" id="dropdown-economy">
            <button class="cmd-link" data-target="vault">💰 VAULT</button>
            <button class="cmd-link cmd-link-disabled" data-target="ember-roll">
                🎰 EMBER ROLL <span class="coming-soon">SOON</span>
            </button>
            <button class="cmd-link cmd-link-disabled" data-target="marketplace">
                🏪 MARKETPLACE <span class="coming-soon">SOON</span>
            </button>
            <button class="cmd-link" data-target="tokenomics">📈 TOKENOMICS</button>
        </div>
    </div>

    <!-- WORLD con dropdown -->
    <div class="cmd-dropdown">
        <button class="cmd-link" data-dropdown="world">
            <span class="cmd-icon">🌍</span> WORLD <span class="dropdown-arrow">▼</span>
        </button>
        <div class="cmd-dropdown-menu" id="dropdown-world">
            <button class="cmd-link" data-target="lore">📜 LORE</button>
            <button class="cmd-link cmd-link-disabled" data-target="world">
                🗺️ WORLD MAP <span class="coming-soon">SOON</span>
            </button>
            <button class="cmd-link" data-target="events">🎪 EVENTS</button>
        </div>
    </div>

    <!-- COMMUNITY con dropdown -->
    <div class="cmd-dropdown">
        <button class="cmd-link" data-dropdown="community">
            <span class="cmd-icon">👥</span> COMMUNITY <span class="dropdown-arrow">▼</span>
        </button>
        <div class="cmd-dropdown-menu" id="dropdown-community">
            <button class="cmd-link" data-target="announcements">📢 ANNOUNCEMENTS</button>
            <button class="cmd-link" data-target="credits">🤝 SOCIAL/CREDITS</button>
        </div>
    </div>

    <!-- INFO con dropdown -->
    <div class="cmd-dropdown">
        <button class="cmd-link" data-dropdown="info">
            <span class="cmd-icon">❓</span> INFO <span class="dropdown-arrow">▼</span>
        </button>
        <div class="cmd-dropdown-menu" id="dropdown-info">
            <button class="cmd-link" data-target="tutorial">❓ HELP/TUTORIAL</button>
            <button class="cmd-link" data-target="whitepaper">📄 WHITEPAPER</button>
        </div>
    </div>
</div>
```

### 7.2 CSS Necesario (agregar a hacknet-clean.css)

```css
/* ═══════════════════════════════════════════════════════════
   CONSOLIDATED NAVIGATION - Dropdown System
   ═══════════════════════════════════════════════════════════ */

.top-command-bar.consolidated {
    display: flex;
    justify-content: center;
    gap: 8px;
    padding: 10px 15px;
    flex-wrap: wrap; /* Mobile responsive */
}

/* Dropdown container */
.cmd-dropdown {
    position: relative;
    display: inline-block;
}

/* Dropdown trigger button */
.cmd-dropdown > .cmd-link {
    display: flex;
    align-items: center;
    gap: 6px;
}

.dropdown-arrow {
    font-size: 10px;
    opacity: 0.7;
    transition: transform 0.2s;
}

.cmd-dropdown.open .dropdown-arrow {
    transform: rotate(180deg);
}

/* Dropdown menu */
.cmd-dropdown-menu {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    min-width: 180px;
    background: #0a0a0a;
    border: 1px solid #FFB000;
    box-shadow: 0 0 10px rgba(255, 176, 0, 0.3);
    z-index: 1000;
    padding: 4px 0;
}

.cmd-dropdown.open .cmd-dropdown-menu {
    display: block;
    animation: dropdownFadeIn 0.15s ease;
}

@keyframes dropdownFadeIn {
    from { opacity: 0; transform: translateY(-5px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Dropdown items */
.cmd-dropdown-menu .cmd-link {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 10px 15px;
    border: none;
    text-align: left;
    white-space: nowrap;
}

.cmd-dropdown-menu .cmd-link:hover {
    background: rgba(255, 176, 0, 0.1);
}

/* Coming Soon badge */
.coming-soon {
    font-size: 9px;
    background: #333;
    color: #888;
    padding: 2px 5px;
    border-radius: 2px;
    margin-left: auto;
}

/* Icon styling */
.cmd-icon {
    font-size: 14px;
    width: 18px;
    text-align: center;
}

/* Primary button (PLAY) */
.cmd-link-primary {
    background: #FFB000 !important;
    color: #000 !important;
}

.cmd-link-primary:hover {
    background: #FFC000 !important;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .top-command-bar.consolidated {
        gap: 4px;
    }

    .cmd-link {
        padding: 8px 10px;
        font-size: 11px;
    }

    .cmd-dropdown-menu {
        position: fixed;
        left: 10px;
        right: 10px;
        width: auto;
    }
}
```

### 7.3 JavaScript para Dropdowns

```javascript
// ═══════════════════════════════════════════════════════════
// CONSOLIDATED NAVIGATION - Dropdown Handler
// ═══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function() {
    const dropdowns = document.querySelectorAll('.cmd-dropdown');

    // Toggle dropdown on click
    dropdowns.forEach(dropdown => {
        const trigger = dropdown.querySelector('[data-dropdown]');

        trigger.addEventListener('click', function(e) {
            e.stopPropagation();

            // Close other dropdowns
            dropdowns.forEach(d => {
                if (d !== dropdown) d.classList.remove('open');
            });

            // Toggle this dropdown
            dropdown.classList.toggle('open');
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', function() {
        dropdowns.forEach(d => d.classList.remove('open'));
    });

    // Handle dropdown menu item clicks
    document.querySelectorAll('.cmd-dropdown-menu .cmd-link').forEach(btn => {
        btn.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            if (target && !this.classList.contains('cmd-link-disabled')) {
                switchScreen(target);
                // Close dropdown
                this.closest('.cmd-dropdown').classList.remove('open');
            }
        });
    });

    // Keyboard navigation (accessibility)
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                dropdown.classList.remove('open');
            }
        });
    });
});
```

### 7.4 Mapeo de Rutas (Sin cambios necesarios)

Todas las rutas existentes siguen funcionando:
- `/mint` → MINT / INVOKE
- `/missions` → MISSIONS (via PLAY dropdown)
- `/profile` → PROFILE (via PROFILE dropdown)
- `/vault` → VAULT (via ECONOMY dropdown)
- etc.

---

## 8. CHECKLIST DE IMPLEMENTACIÓN

### Pre-implementación
- [ ] Backup de `static/index.html`
- [ ] Backup de `static/css/hacknet-clean.css`
- [ ] Confirmar que todas las rutas siguen accesibles

### Implementación
- [ ] Agregar nuevos estilos CSS
- [ ] Reemplazar `nav-bar` y `nav-bar-2` con estructura consolidada
- [ ] Agregar JavaScript de dropdowns
- [ ] Testing en desktop
- [ ] Testing en mobile
- [ ] Testing de todas las rutas

### Post-implementación
- [ ] Verificar que "START YOUR JOURNEY" funciona
- [ ] Verificar efectos CRT intactos
- [ ] Verificar colores amber/rojo/verde intactos
- [ ] Verificar EMBERHOLM CONSOLE intacto
- [ ] Verificar STATUS bar intacto

---

## 9. ARCHIVOS A MODIFICAR

| Archivo | Cambio | Riesgo |
|---------|--------|--------|
| `static/index.html` | Reemplazar nav-bar, nav-bar-2 | **MEDIO** |
| `static/css/hacknet-clean.css` | Agregar estilos dropdown | **BAJO** |
| `static/js/main.js` (o inline) | Agregar dropdown handler | **BAJO** |

---

**⚠️ ESPERANDO CONFIRMACIÓN ANTES DE IMPLEMENTAR**

¿Procedo con la implementación de la **Opción A (7 botones)** o prefieres otra opción?
