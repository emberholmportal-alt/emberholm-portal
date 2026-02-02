# Análisis Completo - Rediseño Portal Web Principal Emberholm

**Fecha de Análisis:** 2026-02-02
**URL del Portal:** https://www.emberholmportal.xyz/
**Branch de Trabajo:** `claude/redesign-portal-navigation-e99wn`

---

## 1. PROYECTO IDENTIFICADO

### 1.1 Ubicación
```
UBICACIÓN DEL PORTAL WEB: /home/user/emberholm-portal/
TIPO DE PROYECTO: Vanilla HTML/CSS/JavaScript SPA con Flask Backend
NO ES: Next.js / React / Vue (la carpeta /mini-app/ es un proyecto SEPARADO)
```

### 1.2 Stack Tecnológico
```
STACK IDENTIFICADO:
- Frontend: Vanilla JavaScript ES6+, HTML5, CSS3
- Backend: Python Flask
- Blockchain: Web3.js, ethers.js (Base network)
- Base de Datos: PostgreSQL + JSON fallback
- Estilos: CSS Variables, efectos CRT retro
- Fuentes: Pixelify Sans, Alagard, Share Tech Mono
```

### 1.3 Estructura de Archivos Principal
```
/home/user/emberholm-portal/
├── app.py                          # Flask backend (NO TOCAR)
├── static/
│   ├── index.html                  # ⭐ ARCHIVO PRINCIPAL (14,073 líneas)
│   ├── css/
│   │   └── hacknet-clean.css       # ⭐ ESTILOS PRINCIPALES (5,497 líneas)
│   ├── js/
│   │   ├── hacknet-ui.js           # Utilidades UI
│   │   └── wallet.js               # Conexión wallet
│   └── img/                        # Assets de imágenes
├── mini-app/                       # ❌ PROYECTO SEPARADO - NO TOCAR
└── contracts/                      # Smart contracts - NO TOCAR
```

---

## 2. COMPONENTES ACTUALES

### 2.1 Componentes de Layout (NO TOCAR)

#### Console Bar (líneas 1374-1424)
```html
<!-- EMBERHOLM CONSOLE // REALM AMBIENCE + TIME SYSTEM -->
<div class="ember-console-bar" id="ember-console">
    <!-- SECTION 1: MUSIC -->
    <div class="console-section console-music">...</div>
    <!-- SECTION 2: CALENDAR (Era, Year, Day) -->
    <div class="console-section console-calendar">...</div>
    <!-- SECTION 3: PHASE + WEATHER + TIME -->
    <div class="console-section console-time">...</div>
</div>
```
**Archivo:** `static/index.html` líneas 1374-1424
**Estado:** ✅ NO TOCAR

#### Status Bar / Header (líneas 1432-1473)
```html
<header class="top-header">
    <div class="top-status-row">
        <span>EMBERHOLM PORTAL : NODE-Δ / REALM MONITOR</span>
        <span id="access-level">ACCESS LEVEL: [CITIZEN]</span>
        <span>STATUS: FLAME WEAKENING // MISSIONS REQUIRED</span>
    </div>
    <!-- Navigation bars van aquí -->
</header>
```
**Archivo:** `static/index.html` líneas 1432-1437
**Estado:** ✅ NO TOCAR (excepto los botones de navegación)

#### Progress Bar (líneas 1464-1466)
```html
<div class="nav-progress-bar">
    <div class="nav-progress-fill"></div>
</div>
```
**Estado:** ✅ NO TOCAR

#### Command Hint (líneas 1468-1470)
```html
<div class="command-hint">
    USE COMMAND KEYS TO NAVIGATE. ACCESS OUTSIDE AUTHORIZATION WILL BE LOGGED...
</div>
```
**Estado:** ✅ NO TOCAR

#### Home Screen - Logo y Texto Central (líneas 1476-1497)
```html
<section class="screen active" data-screen="home">
    <div class="logo-wrapper">
        <img src="img/logo-site2.png" class="project-logo-img" alt="Emberholm Portal" />
        <div class="center-text-line">EMBER PROTOCOL v0.1972 // RETRO RPG INTERFACE</div>
        <div class="center-text-line">UNAUTHORIZED ACCESS WILL BE LOGGED...</div>
        <button class="cmd site-tour-btn">[START YOUR JOURNEY]</button>
    </div>
</section>
```
**Estado:** ✅ NO TOCAR

### 2.2 Botones de Navegación Actuales (SÍ MODIFICAR)

**Ubicación:** `static/index.html` líneas 1440-1461

#### Navigation Row 1 (9 botones)
```html
<div class="top-command-bar" id="nav-bar">
    <button class="cmd-link cmd-link-mint" onclick="window.location.href='/mint'">MINT / INVOKE</button>
    <button class="cmd-link" data-target="home">[HOME]</button>
    <button class="cmd-link" data-target="guilds">[STATS/GUILDS]</button>
    <button class="cmd-link" data-target="missions">[MISSIONS]</button>
    <button class="cmd-link cmd-link-disabled" data-target="micro-missions">[MICRO-MISSIONS]</button>
    <button class="cmd-link" data-target="profile">[PROFILE]</button>
    <button class="cmd-link" data-target="vault">[VAULT]</button>
    <button class="cmd-link cmd-link-disabled" data-target="ember-roll">[EMBER ROLL]</button>
    <button class="cmd-link cmd-link-disabled" data-target="marketplace">[MARKETPLACE]</button>
</div>
```

#### Navigation Row 2 (8 botones)
```html
<div class="top-command-bar" id="nav-bar-2">
    <button class="cmd-link" data-target="tutorial">[HELP/TUTORIAL]</button>
    <button class="cmd-link" data-target="lore">[LORE]</button>
    <button class="cmd-link" data-target="announcements">[ANNOUNCEMENTS]</button>
    <button class="cmd-link" data-target="events">[EVENTS]</button>
    <button class="cmd-link" data-target="credits">[SOCIAL/CREDITS]</button>
    <button class="cmd-link" data-target="whitepaper">[WHITEPAPER/CONTRACTS]</button>
    <button class="cmd-link" data-target="tokenomics">[TOKENOMICS]</button>
    <button class="cmd-link cmd-link-disabled" data-target="world">[WORLD]</button>
</div>
```

**Total actual:** 17 botones
**Estado:** ⚠️ REEMPLAZAR POR 6 BOTONES

### 2.3 Screens Existentes (16 en total)

| # | Screen | data-screen | Línea HTML | Estado |
|---|--------|-------------|------------|--------|
| 1 | Home | `home` | 1476 | ACTIVO |
| 2 | Stats/Guilds | `guilds` | 1615 | ACTIVO |
| 3 | Missions | `missions` | 1649 | ACTIVO |
| 4 | Micro-Missions | `micro-missions` | 1661 | DESHABILITADO |
| 5 | World | `world` | 1687 | DESHABILITADO |
| 6 | Profile | `profile` | 1755 | ACTIVO |
| 7 | Vault | `vault` | 1854 | ACTIVO |
| 8 | Tutorial | `tutorial` | 1983 | ACTIVO |
| 9 | Lore | `lore` | 3176 | ACTIVO |
| 10 | Announcements | `announcements` | 3297 | ACTIVO |
| 11 | Events | `events` | 3341 | ACTIVO |
| 12 | Credits | `credits` | 3484 | ACTIVO |
| 13 | Whitepaper | `whitepaper` | 3533 | ACTIVO |
| 14 | Tokenomics | `tokenomics` | 3632 | ACTIVO |
| 15 | Ember Roll | `ember-roll` | 4052 | DESHABILITADO |
| 16 | Marketplace | `marketplace` | 4100 | DESHABILITADO |

---

## 3. SISTEMA DE NAVEGACIÓN ACTUAL

### 3.1 Función Principal (líneas 5032-5041)
```javascript
function switchScreen(screenName){
    console.log("🔘 switchScreen called:", screenName);
    document.querySelectorAll(".screen").forEach(s=>{
        if(s.getAttribute("data-screen") === screenName){
            s.classList.add("active");
        } else {
            s.classList.remove("active");
        }
    });
}
```

### 3.2 Event Listeners (líneas 5043-5148)
```javascript
const navButtons = document.querySelectorAll(".cmd-link");

function setActiveButton(btn) {
    navButtons.forEach(b => b.classList.remove("is-active"));
    if (btn) btn.classList.add("is-active");
}

navButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-target");
        if (target) {
            // Botones deshabilitados no hacen nada
            if (btn.classList.contains('cmd-link-disabled')) {
                return;
            }
            switchScreen(target);
            setActiveButton(btn);
            // Auto-load data según la sección...
        }
    });
});
```

### 3.3 Carga de Datos por Sección
- **guilds:** `fetchStatsAndRender()` + `fetchGuildsAndRender()`
- **missions:** `fetchMissionsAndRender()` (requiere wallet)
- **events:** `fetchEventsAndRender()`
- **profile:** `loadPlayerAndRender()` (requiere wallet)
- **vault:** `loadVault()` + balances (requiere wallet)
- **tutorial:** `loadTutorialMissions()`
- **world:** `initSocialSection()` (requiere wallet)
- **micro-missions:** `initMicroMissionsSection()` (requiere wallet)

---

## 4. SISTEMA DE ESTADO

### 4.1 Variables Globales
```javascript
// Estado de wallet
let connectedWallet = null;

// Datos cacheados
let cachedHeroesData = null;
let cachedMissionsData = null;

// Estado de música
let musicIndex = 0;
let musicMuted = false;

// Estado de tutorial
let currentTutorialStep = 0;
let tutorialActive = false;

// Estado de misiones
let selectedHeroForMission = null;
let selectedPartyHeroes = [];
```

### 4.2 Almacenamiento
- **sessionStorage:** `portalCrossed` (flag de entrada al portal)
- **localStorage:** `emberholm_boot_seen` (flag de secuencia de boot)

### 4.3 Fuentes de Datos para Badges

| Badge | Dato | Fuente | Disponibilidad |
|-------|------|--------|----------------|
| Misiones activas | Cantidad de misiones en curso | `cachedHeroesData` filtrando `state === "ON_MISSION"` | ✅ Disponible |
| Eventos activos | Eventos con `active: true` | `/api/events/active` | ✅ Disponible |
| Balance $EMBER | Pending + On-chain | `/api/player/<wallet>` | ✅ Disponible |

---

## 5. BOTONES ACTUALES VS PROPUESTOS

### 5.1 Mapeo de 17 Botones → 6 Botones

```
ESTRUCTURA ACTUAL (17 botones):
┌────────────────────────────────────────────────────────────────┐
│ Row 1: MINT | HOME | STATS/GUILDS | MISSIONS | MICRO-MISSIONS  │
│        PROFILE | VAULT | EMBER ROLL | MARKETPLACE              │
├────────────────────────────────────────────────────────────────┤
│ Row 2: HELP/TUTORIAL | LORE | ANNOUNCEMENTS | EVENTS           │
│        SOCIAL/CREDITS | WHITEPAPER/CONTRACTS | TOKENOMICS      │
│        WORLD                                                    │
└────────────────────────────────────────────────────────────────┘

ESTRUCTURA PROPUESTA (6 botones):
┌────────────────────────────────────────────────────────────────┐
│   [MINT / INVOKE]  │  [PLAY] (n)  │  [COMO JUGAR]              │
│   [VAULT]          │  [WORLD CHAT] │  [INFO]                   │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 Detalle de Cada Botón Nuevo

#### BOTÓN 1: MINT / INVOKE
- **Tipo:** Rojo, mantener igual
- **Acción:** `window.location.href='/mint'`
- **Cambio:** NINGUNO

#### BOTÓN 2: PLAY (con tabs internas)
- **Tipo:** Naranja, con badge de número
- **Badge:** Suma de (misiones activas + eventos nuevos)
- **Tabs internas:**
  - 👤 **PROFILE** → screen `profile`
  - 📊 **STATS** → screen `guilds`
  - ⚔️ **MISSIONS** → screen `missions` (con badge)
  - 📅 **EVENTS** → screen `events` (con badge "NEW")
  - 📜 **LORE** → screen `lore`
  - 🎲 **MICRO-MISSIONS** → screen `micro-missions` (futuro)
  - 🛒 **MARKET** → screen `marketplace` (placeholder)

#### BOTÓN 3: COMO JUGAR
- **Tipo:** Naranja
- **Acción:** `switchScreen('tutorial')`
- **Cambio:** Solo renombrar de "HELP/TUTORIAL"

#### BOTÓN 4: VAULT
- **Tipo:** Naranja
- **Acción:** `switchScreen('vault')`
- **Cambio:** NINGUNO

#### BOTÓN 5: WORLD CHAT
- **Tipo:** Naranja
- **Acción:** Mostrar placeholder "En desarrollo"
- **Cambio:** Crear nueva screen placeholder

#### BOTÓN 6: INFO (con tabs internas)
- **Tipo:** Naranja
- **Tabs internas:**
  - 📢 **ANNOUNCEMENTS** → screen `announcements`
  - 👥 **SOCIAL/CREDITS** → screen `credits`
  - 📄 **WHITEPAPER** → screen `whitepaper`
  - 💰 **TOKENOMICS** → screen `tokenomics`

### 5.3 Mapeo Completo: Botón Viejo → Destino Nuevo

| Botón Actual | Destino Nuevo | Ubicación |
|--------------|---------------|-----------|
| MINT / INVOKE | MINT / INVOKE | Botón directo |
| HOME | - | Se elimina (redundante) |
| STATS/GUILDS | PLAY → STATS tab | Tab en PLAY |
| MISSIONS | PLAY → MISSIONS tab | Tab en PLAY |
| MICRO-MISSIONS | PLAY → MICRO-MISSIONS tab | Tab en PLAY (futuro) |
| PROFILE | PLAY → PROFILE tab | Tab en PLAY |
| VAULT | VAULT | Botón directo |
| EMBER ROLL | PLAY → EMBER ROLL tab | Tab en PLAY (futuro) |
| MARKETPLACE | PLAY → MARKET tab | Tab en PLAY (placeholder) |
| HELP/TUTORIAL | COMO JUGAR | Botón directo (renombrado) |
| LORE | PLAY → LORE tab | Tab en PLAY |
| ANNOUNCEMENTS | INFO → ANNOUNCEMENTS tab | Tab en INFO |
| EVENTS | PLAY → EVENTS tab | Tab en PLAY |
| SOCIAL/CREDITS | INFO → SOCIAL tab | Tab en INFO |
| WHITEPAPER/CONTRACTS | INFO → WHITEPAPER tab | Tab en INFO |
| TOKENOMICS | INFO → TOKENOMICS tab | Tab en INFO |
| WORLD | WORLD CHAT | Botón placeholder |

---

## 6. RESPUESTAS A PREGUNTAS

### Pregunta 1: ¿MICRO-MISSIONS se fusiona con MISSIONS o es tab separado?
**RESPUESTA:** Tab separado en PLAY. Actualmente está deshabilitado, pero cuando se active será un tab independiente porque tiene funcionalidad diferente (misiones de 1-5 minutos vs misiones de 72h).

### Pregunta 2: ¿STATS/GUILDS va dentro de PROFILE o es tab independiente?
**RESPUESTA:** Tab independiente llamado "STATS" en PLAY. PROFILE es para datos personales del jugador, STATS es para rankings globales y guilds.

### Pregunta 3: ¿EMBER ROLL va dentro de VAULT o es tab en PLAY?
**RESPUESTA:** Tab en PLAY (futuro). Es un sistema de loot/gacha que es parte del gameplay, no del almacenamiento.

### Pregunta 4: ¿MARKETPLACE existe ya como componente o es placeholder?
**RESPUESTA:** Es placeholder. El screen existe (línea 4100) pero está deshabilitado. En la nueva estructura será tab en PLAY con mensaje "Coming Soon".

### Pregunta 5: ¿ANNOUNCEMENTS va en INFO o en PLAY?
**RESPUESTA:** Va en INFO. Los anuncios son información meta del proyecto, no gameplay.

### Pregunta 6: ¿WORLD va en INFO o se fusiona con LORE?
**RESPUESTA:** WORLD actual (social/chat) → se convierte en "WORLD CHAT" (botón placeholder).
LORE → va como tab en PLAY (es parte del contenido de juego).

### Pregunta 7: ¿De dónde vienen los datos de misiones activas?
**RESPUESTA:** De `cachedHeroesData` filtrando emissaries con `state === "ON_MISSION"`. Se puede obtener contando:
```javascript
const activeMissions = cachedHeroesData?.filter(h => h.state === "ON_MISSION").length || 0;
```

### Pregunta 8: ¿De dónde vienen los datos de eventos activos?
**RESPUESTA:** De `/api/events/active`. La función `fetchEventsAndRender()` ya hace este request.

### Pregunta 9: ¿El balance de $EMBER está disponible en el store?
**RESPUESTA:** Sí, disponible vía `/api/player/<wallet>` que devuelve `ember_pending` y el balance on-chain se obtiene del contrato.

### Pregunta 10: ¿Hay algún componente crítico que no identifiqué?
**RESPUESTA:** No identificado ninguno adicional. Los componentes críticos son:
- Console Bar (música, calendario, tiempo)
- Status Bar (nivel de acceso)
- Portal Entry Overlay (intro)
- Boot Sequence (primera visita)
- Todos estos NO se tocan.

---

## 7. ARCHIVOS A CREAR

### 7.1 Ningún archivo nuevo necesario

Dado que es vanilla HTML/JS, NO se crean archivos separados. Todo se agrega en:
- `static/index.html` - Nuevas secciones HTML
- `static/css/hacknet-clean.css` - Nuevos estilos

---

## 8. ARCHIVOS A MODIFICAR

### 8.1 static/index.html

#### Cambio 1: Reemplazar Navigation Bars (líneas 1440-1461)
**ANTES:**
```html
<div class="top-command-bar" id="nav-bar">
    <!-- 9 botones -->
</div>
<div class="top-command-bar" id="nav-bar-2">
    <!-- 8 botones -->
</div>
```

**DESPUÉS:**
```html
<div class="top-command-bar top-command-bar-redesign" id="nav-bar">
    <button class="cmd-link cmd-link-mint" onclick="window.location.href='/mint'">MINT / INVOKE</button>
    <button class="cmd-link cmd-link-play" data-target="play-hub" id="btn-play">
        [PLAY]
        <span class="nav-badge" id="play-badge" style="display:none;">0</span>
    </button>
    <button class="cmd-link" data-target="tutorial">[COMO JUGAR]</button>
    <button class="cmd-link" data-target="vault">[VAULT]</button>
    <button class="cmd-link" data-target="world-chat">[WORLD CHAT]</button>
    <button class="cmd-link" data-target="info-hub">[INFO]</button>
</div>
```

#### Cambio 2: Agregar PLAY HUB Screen (después de home screen, ~línea 1610)
```html
<!-- PLAY HUB (NEW) -->
<section class="screen" data-screen="play-hub">
    <div class="section-block">
        <div class="section-title">PLAY // ADVENTURE HUB</div>

        <!-- PLAY TABS -->
        <div class="play-tabs">
            <button class="play-tab active" data-play-tab="profile">
                👤 PROFILE
            </button>
            <button class="play-tab" data-play-tab="guilds">
                📊 STATS
            </button>
            <button class="play-tab" data-play-tab="missions">
                ⚔️ MISSIONS
                <span class="tab-badge" id="missions-badge" style="display:none;">0</span>
            </button>
            <button class="play-tab" data-play-tab="events">
                📅 EVENTS
                <span class="tab-badge tab-badge-new" id="events-badge" style="display:none;">NEW</span>
            </button>
            <button class="play-tab" data-play-tab="lore">
                📜 LORE
            </button>
            <button class="play-tab cmd-link-disabled" data-play-tab="micro-missions">
                🎲 MICRO
            </button>
            <button class="play-tab cmd-link-disabled" data-play-tab="marketplace">
                🛒 MARKET
            </button>
        </div>

        <!-- PLAY CONTENT (loads existing screens) -->
        <div class="play-content" id="play-content">
            <!-- Content dynamically loaded from existing screens -->
        </div>

        <!-- BACK BUTTON -->
        <div class="back-btn-container">
            <button class="terminal-btn" onclick="switchScreen('home')">[← BACK TO HOME]</button>
        </div>
    </div>
</section>
```

#### Cambio 3: Agregar INFO HUB Screen (después de PLAY HUB)
```html
<!-- INFO HUB (NEW) -->
<section class="screen" data-screen="info-hub">
    <div class="section-block">
        <div class="section-title">INFO // PROJECT DOCUMENTATION</div>

        <!-- INFO TABS -->
        <div class="info-tabs">
            <button class="info-tab active" data-info-tab="announcements">
                📢 ANNOUNCEMENTS
            </button>
            <button class="info-tab" data-info-tab="credits">
                👥 SOCIAL
            </button>
            <button class="info-tab" data-info-tab="whitepaper">
                📄 WHITEPAPER
            </button>
            <button class="info-tab" data-info-tab="tokenomics">
                💰 TOKENOMICS
            </button>
        </div>

        <!-- INFO CONTENT -->
        <div class="info-content" id="info-content">
            <!-- Content dynamically loaded from existing screens -->
        </div>

        <!-- BACK BUTTON -->
        <div class="back-btn-container">
            <button class="terminal-btn" onclick="switchScreen('home')">[← BACK TO HOME]</button>
        </div>
    </div>
</section>
```

#### Cambio 4: Agregar WORLD CHAT Placeholder Screen
```html
<!-- WORLD CHAT PLACEHOLDER (NEW) -->
<section class="screen" data-screen="world-chat">
    <div class="section-block">
        <div class="section-title">WORLD CHAT // COMING SOON</div>

        <div class="placeholder-content" style="text-align:center; padding:60px 20px;">
            <div style="font-size:48px; margin-bottom:20px;">🌍💬</div>
            <div style="color:var(--gold); font-size:18px; margin-bottom:15px;">
                INTER-REALM COMMUNICATION
            </div>
            <div style="color:var(--dim-green); max-width:500px; margin:0 auto;">
                The World Chat system is being developed by the Circle of Mist.
                Soon, operators from across realms will be able to communicate
                in real-time.
            </div>
            <div style="margin-top:30px; color:#888; font-size:12px;">
                STATUS: IN DEVELOPMENT
            </div>
        </div>

        <!-- BACK BUTTON -->
        <div class="back-btn-container">
            <button class="terminal-btn" onclick="switchScreen('home')">[← BACK TO HOME]</button>
        </div>
    </div>
</section>
```

#### Cambio 5: Agregar JavaScript para Hub Navigation (al final del script)
```javascript
/* ========== PLAY HUB NAVIGATION ========== */
let currentPlayTab = 'profile';

function switchPlayTab(tabName) {
    currentPlayTab = tabName;

    // Update tab buttons
    document.querySelectorAll('.play-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.getAttribute('data-play-tab') === tabName) {
            tab.classList.add('active');
        }
    });

    // Load content from existing screen
    const contentContainer = document.getElementById('play-content');
    const sourceScreen = document.querySelector(`[data-screen="${tabName}"]`);

    if (sourceScreen) {
        contentContainer.innerHTML = sourceScreen.innerHTML;

        // Trigger data loading for the tab
        if (tabName === 'guilds') {
            fetchStatsAndRender();
            fetchGuildsAndRender();
        } else if (tabName === 'missions') {
            if (!connectedWallet) {
                showInfoModal("WALLET REQUIRED", "Connect wallet to access missions.");
            } else {
                fetchMissionsAndRender();
            }
        } else if (tabName === 'events') {
            fetchEventsAndRender();
        } else if (tabName === 'profile') {
            if (connectedWallet) {
                loadPlayerAndRender();
            }
        }
    }
}

// Play tab click listeners
document.querySelectorAll('.play-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        if (tab.classList.contains('cmd-link-disabled')) return;
        switchPlayTab(tab.getAttribute('data-play-tab'));
    });
});

/* ========== INFO HUB NAVIGATION ========== */
let currentInfoTab = 'announcements';

function switchInfoTab(tabName) {
    currentInfoTab = tabName;

    // Update tab buttons
    document.querySelectorAll('.info-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.getAttribute('data-info-tab') === tabName) {
            tab.classList.add('active');
        }
    });

    // Load content from existing screen
    const contentContainer = document.getElementById('info-content');
    const sourceScreen = document.querySelector(`[data-screen="${tabName}"]`);

    if (sourceScreen) {
        contentContainer.innerHTML = sourceScreen.innerHTML;
    }
}

// Info tab click listeners
document.querySelectorAll('.info-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        switchInfoTab(tab.getAttribute('data-info-tab'));
    });
});

/* ========== BADGE UPDATES ========== */
function updatePlayBadge() {
    const badge = document.getElementById('play-badge');
    const missionsBadge = document.getElementById('missions-badge');

    // Count active missions from cached data
    let activeMissions = 0;
    if (cachedHeroesData) {
        activeMissions = cachedHeroesData.filter(h => h.state === "ON_MISSION").length;
    }

    // Update missions badge
    if (missionsBadge) {
        if (activeMissions > 0) {
            missionsBadge.textContent = activeMissions;
            missionsBadge.style.display = 'inline-flex';
        } else {
            missionsBadge.style.display = 'none';
        }
    }

    // Update main PLAY badge
    if (badge) {
        if (activeMissions > 0) {
            badge.textContent = activeMissions;
            badge.style.display = 'inline-flex';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Call badge update when data loads
// Add to existing data fetch functions
```

### 8.2 static/css/hacknet-clean.css

#### Agregar Estilos Nuevos (al final del archivo)
```css
/* ===============================================================
   NAVIGATION REDESIGN - 6 BUTTON LAYOUT
   =============================================================== */

/* Single row layout for 6 buttons */
.top-command-bar-redesign {
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
}

/* PLAY button special styling */
.cmd-link-play {
    position: relative;
    background: var(--orange-light);
}

/* Badge for nav buttons */
.nav-badge {
    position: absolute;
    top: -8px;
    right: -8px;
    background: var(--error-red);
    color: #000;
    font-size: 10px;
    font-weight: bold;
    min-width: 18px;
    height: 18px;
    border-radius: 9px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 4px;
    animation: pulse-badge 2s infinite;
}

@keyframes pulse-badge {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

/* ===============================================================
   PLAY HUB STYLES
   =============================================================== */

.play-tabs,
.info-tabs {
    display: flex;
    gap: 4px;
    border-bottom: 1px solid var(--border-primary);
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.play-tab,
.info-tab {
    position: relative;
    padding: 10px 16px;
    background: transparent;
    border: 1px solid var(--border-primary);
    border-bottom: none;
    color: var(--dim-green);
    font-family: 'Pixelify Sans', monospace;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.play-tab:hover,
.info-tab:hover {
    background: rgba(255, 153, 0, 0.1);
    color: var(--bright-green);
}

.play-tab.active,
.info-tab.active {
    background: rgba(255, 153, 0, 0.2);
    color: var(--gold);
    border-color: var(--gold);
}

.play-tab.cmd-link-disabled,
.info-tab.cmd-link-disabled {
    color: #555;
    cursor: not-allowed;
}

/* Tab badges */
.tab-badge {
    position: absolute;
    top: -6px;
    right: -6px;
    background: var(--warning-orange);
    color: #000;
    font-size: 9px;
    font-weight: bold;
    min-width: 16px;
    height: 16px;
    border-radius: 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 3px;
}

.tab-badge-new {
    background: var(--error-red);
    color: #fff;
}

/* Content area */
.play-content,
.info-content {
    min-height: 400px;
}

/* Back button */
.back-btn-container {
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid var(--border-primary);
    text-align: center;
}

/* ===============================================================
   PLACEHOLDER STYLES
   =============================================================== */

.placeholder-content {
    background: rgba(0, 0, 0, 0.3);
    border: 1px dashed var(--border-primary);
    border-radius: 4px;
}

/* ===============================================================
   RESPONSIVE - MOBILE ADJUSTMENTS
   =============================================================== */

@media (max-width: 768px) {
    .top-command-bar-redesign {
        gap: 6px;
    }

    .top-command-bar-redesign .cmd-link {
        font-size: 11px !important;
        padding: 8px 10px !important;
    }

    .play-tabs,
    .info-tabs {
        gap: 2px;
    }

    .play-tab,
    .info-tab {
        padding: 8px 10px;
        font-size: 10px;
    }
}
```

---

## 9. ARCHIVOS A NO TOCAR

- ❌ `app.py` - Backend Flask
- ❌ `mini-app/` - Proyecto separado completo
- ❌ `contracts/` - Smart contracts
- ❌ Console Bar HTML (líneas 1374-1424)
- ❌ Status Bar texto (líneas 1433-1437)
- ❌ Progress Bar (líneas 1464-1466)
- ❌ Command Hint (líneas 1468-1470)
- ❌ Home Screen logo/texto (líneas 1476-1497)
- ❌ Todas las screens existentes internamente (solo se reubicarán)
- ❌ Funciones de carga de datos existentes
- ❌ Sistema de wallet connection
- ❌ Efectos CRT (scanlines, noise, vignette)

---

## 10. PLAN DE IMPLEMENTACIÓN

### Paso 1: Backup
```bash
# Crear backup antes de cambios
cp static/index.html static/index.html.backup.$(date +%Y%m%d)
cp static/css/hacknet-clean.css static/css/hacknet-clean.css.backup.$(date +%Y%m%d)
```

### Paso 2: Agregar estilos CSS
- Agregar nuevos estilos al final de `hacknet-clean.css`
- NO modificar estilos existentes

### Paso 3: Agregar nuevos screens HTML
- Agregar PLAY HUB screen después del HOME screen
- Agregar INFO HUB screen después de PLAY HUB
- Agregar WORLD CHAT placeholder después de INFO HUB

### Paso 4: Modificar navigation bar
- Reemplazar las dos filas de botones por una fila de 6 botones
- Mantener clases CSS existentes donde aplique

### Paso 5: Agregar JavaScript
- Agregar funciones de navegación para hubs
- Agregar sistema de badges
- Conectar con funciones de datos existentes

### Paso 6: Testing
- [ ] MINT funciona (va a /mint)
- [ ] PLAY abre hub con tabs
- [ ] Cada tab en PLAY carga contenido correcto
- [ ] COMO JUGAR va a tutorial
- [ ] VAULT funciona igual
- [ ] WORLD CHAT muestra placeholder
- [ ] INFO abre hub con tabs
- [ ] Cada tab en INFO carga contenido correcto
- [ ] Badges se muestran cuando hay datos
- [ ] Console Bar no afectada
- [ ] Status Bar no afectada
- [ ] Efectos CRT funcionan
- [ ] Responsive en mobile

---

## 11. RIESGOS Y MITIGACIONES

### Riesgo 1: Romper navegación existente
- **Probabilidad:** Media
- **Impacto:** Alto
- **Mitigación:** Las screens existentes se mantienen intactas, solo se agregan hubs que las referencian.

### Riesgo 2: Funciones JS no encontradas
- **Probabilidad:** Baja
- **Impacto:** Medio
- **Mitigación:** Verificar que todas las funciones existen antes de llamarlas.

### Riesgo 3: Estilos en conflicto
- **Probabilidad:** Baja
- **Impacto:** Bajo
- **Mitigación:** Usar clases nuevas específicas para el redesign.

### Riesgo 4: Badges no actualizan
- **Probabilidad:** Media
- **Impacto:** Bajo (cosmético)
- **Mitigación:** Llamar `updatePlayBadge()` después de cada carga de datos.

### Plan de Rollback
```bash
# Si algo falla
git checkout static/index.html
git checkout static/css/hacknet-clean.css
# O restaurar desde backups
cp static/index.html.backup.YYYYMMDD static/index.html
cp static/css/hacknet-clean.css.backup.YYYYMMDD static/css/hacknet-clean.css
```

---

## 12. CÓDIGO PROPUESTO

### 12.1 MainMenu - Navigation Bar DESPUÉS
```html
<!-- Navigation Row (REDESIGNED - 6 buttons) -->
<div class="top-command-bar top-command-bar-redesign" id="nav-bar">
    <button class="cmd-link cmd-link-mint" onclick="window.location.href='/mint'">MINT / INVOKE</button>
    <button class="cmd-link cmd-link-play" data-target="play-hub" id="btn-play">
        [PLAY]
        <span class="nav-badge" id="play-badge" style="display:none;">0</span>
    </button>
    <button class="cmd-link" data-target="tutorial">[COMO JUGAR]</button>
    <button class="cmd-link" data-target="vault">[VAULT]</button>
    <button class="cmd-link" data-target="world-chat">[WORLD CHAT]</button>
    <button class="cmd-link" data-target="info-hub">[INFO]</button>
</div>
<!-- Remove nav-bar-2 completely -->
```

### 12.2 Resumen de Líneas a Modificar en index.html
- Líneas 1440-1461: Reemplazar dos barras de navegación por una
- Después de línea ~1610: Agregar PLAY HUB section
- Después de PLAY HUB: Agregar INFO HUB section
- Después de INFO HUB: Agregar WORLD CHAT section
- Al final del `<script>`: Agregar funciones de hubs y badges

---

## 13. CHECKLIST COMPLETO

### Pre-implementación
- [ ] Backup de index.html creado
- [ ] Backup de hacknet-clean.css creado
- [ ] Branch de trabajo confirmado

### Implementación CSS
- [ ] Estilos de .top-command-bar-redesign agregados
- [ ] Estilos de .nav-badge agregados
- [ ] Estilos de .play-tabs y .info-tabs agregados
- [ ] Estilos de .play-tab y .info-tab agregados
- [ ] Estilos de .tab-badge agregados
- [ ] Estilos de .placeholder-content agregados
- [ ] Estilos responsive agregados

### Implementación HTML
- [ ] Navigation bar reemplazado (17 → 6 botones)
- [ ] PLAY HUB section agregado
- [ ] INFO HUB section agregado
- [ ] WORLD CHAT section agregado

### Implementación JS
- [ ] switchPlayTab() agregado
- [ ] switchInfoTab() agregado
- [ ] updatePlayBadge() agregado
- [ ] Event listeners para tabs agregados
- [ ] Integración con funciones de datos existentes

### Testing Funcional
- [ ] MINT / INVOKE → va a /mint
- [ ] PLAY → abre hub con tabs
- [ ] PLAY → PROFILE tab funciona
- [ ] PLAY → STATS tab funciona
- [ ] PLAY → MISSIONS tab funciona
- [ ] PLAY → EVENTS tab funciona
- [ ] PLAY → LORE tab funciona
- [ ] COMO JUGAR → va a tutorial
- [ ] VAULT → funciona igual
- [ ] WORLD CHAT → muestra placeholder
- [ ] INFO → abre hub con tabs
- [ ] INFO → ANNOUNCEMENTS tab funciona
- [ ] INFO → SOCIAL tab funciona
- [ ] INFO → WHITEPAPER tab funciona
- [ ] INFO → TOKENOMICS tab funciona
- [ ] Botón BACK funciona en cada hub

### Testing Visual
- [ ] Console Bar no afectada
- [ ] Status Bar no afectada
- [ ] Logo y textos no afectados
- [ ] Efectos CRT funcionan
- [ ] Badges se muestran correctamente
- [ ] Badges pulsan con animación
- [ ] Colores correctos (rojo MINT, naranja otros)
- [ ] Tabs deshabilitados en gris
- [ ] Responsive en 768px
- [ ] Responsive en 480px

### Testing de Datos
- [ ] Badge de misiones actualiza
- [ ] Badge de eventos actualiza
- [ ] Datos de PROFILE cargan
- [ ] Datos de STATS cargan
- [ ] Datos de MISSIONS cargan
- [ ] Datos de EVENTS cargan
- [ ] Wallet connection funciona

### Post-implementación
- [ ] No hay errores en consola
- [ ] Build sin errores
- [ ] Git commit con mensaje descriptivo
- [ ] Git push a branch de trabajo

---

## 14. CONFIRMACIÓN REQUERIDA

**⚠️ IMPORTANTE: Antes de proceder con cualquier cambio de código, necesito confirmación explícita del usuario de que:**

1. ✅ El análisis del proyecto es correcto (vanilla HTML/JS, no React)
2. ✅ La identificación de archivos es correcta
3. ✅ El mapeo de 17 → 6 botones está aprobado
4. ✅ Las respuestas a las 10 preguntas están correctas
5. ✅ Los tabs propuestos para PLAY son correctos
6. ✅ Los tabs propuestos para INFO son correctos
7. ✅ El plan de implementación está aprobado
8. ✅ Se entienden los riesgos y el plan de rollback

**Por favor confirmar con:** "APROBADO" o indicar cambios necesarios.

---

*Documento generado el 2026-02-02*
*Branch: claude/redesign-portal-navigation-e99wn*
