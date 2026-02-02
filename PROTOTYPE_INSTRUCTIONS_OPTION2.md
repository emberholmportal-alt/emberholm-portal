# PROTOTIPO HTML - OPCION 2: DASHBOARD DINAMICO

## Instrucciones de Implementacion

---

## 1. ESTRUCTURA VISUAL FINAL

```
┌─────────────────────────────────────────────────────────────┐
│                      IMMERSION BAR                          │
│ [🔊][🎵]        🔥 STEADY · 14:32        [☀️ Clear]        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    [EMBERHOLM LOGO]                    [⚙️] │
│                       MINI APP                              │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                   STATUS CARD                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [🟢 0x1234...5678]                    142 🔥 EMBER     │ │
│ │ 3 Emissaries · 1 Active Mission                   [→]  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│              ═══════ GAMEPLAY ═══════                       │
│                                                             │
│  ╔══════════════════════════════════════════════════════╗   │
│  ║  ▶  PLAY                                             ║   │
│  ║     Start missions and earn $EMBER                   ║   │
│  ╚══════════════════════════════════════════════════════╝   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ◈  MINT EMISSARY                                    │   │
│  │     Join the ranks of Emberholm                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│              ═══════ FEATURES ═══════                       │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ 💰 VAULT        │  │ 🔮 SOCIAL       │  │ 🏆 RANKS    │  │
│  │ Items & Tokens  │  │ (3) messages    │  │ #142 global │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│              ═══════ WORLD ═══════                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  📜 EVENTS (2)   │   🔥 LORE   │   ? GUIDE           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. CAMBIOS ESPECIFICOS EN MainMenu.tsx

### 2.1 Nueva Estructura de Secciones

```tsx
// ANTES: Lista plana de 7 botones
const menuItems: MenuItem[] = [
  { id: 'play', title: 'PLAY', ... },
  { id: 'mint', title: 'MINT EMISSARY', ... },
  { id: 'social-globe', title: 'SOCIAL', ... },
  { id: 'vault', title: 'VAULT', ... },
  { id: 'events', title: 'EVENTS', ... },
  { id: 'lore', title: 'LORE', ... },
  { id: 'tutorial', title: 'TUTORIAL', ... },
];

// DESPUES: Secciones organizadas
const sections = {
  gameplay: [
    { id: 'play', title: 'PLAY', subtitle: 'Start missions and earn $EMBER', primary: true },
    { id: 'mint', title: 'MINT EMISSARY', subtitle: 'Join the ranks of Emberholm' },
  ],
  features: [
    { id: 'vault', title: 'VAULT', subtitle: 'Items & Tokens' },
    { id: 'social-globe', title: 'SOCIAL', subtitle: 'messages', badge: unreadMessages },
    { id: 'leaderboard', title: 'RANKS', subtitle: 'global' },  // NUEVO: extraido de PlayScreen
  ],
  world: [
    { id: 'events', title: 'EVENTS', badge: activeEventsCount },
    { id: 'lore', title: 'LORE' },
    { id: 'tutorial', title: 'GUIDE' },  // Renombrado de TUTORIAL
  ],
};
```

### 2.2 Nuevo Componente: StatusCard

```tsx
// NUEVO: Tarjeta de estado del jugador
interface StatusCardProps {
  wallet: string | null;
  emberBalance: number;
  emissaryCount: number;
  activeMission: ActiveMicroMission | null;
  onViewMission?: () => void;
}

function StatusCard({ wallet, emberBalance, emissaryCount, activeMission, onViewMission }: StatusCardProps) {
  return (
    <div className="status-card">
      <div className="status-card-row">
        <div className="wallet-indicator">
          <div className="status-dot" />
          <span>{truncateWallet(wallet)}</span>
        </div>
        <div className="ember-balance">
          {emberBalance} 🔥 EMBER
        </div>
      </div>
      <div className="status-card-row secondary">
        <span>{emissaryCount} Emissaries</span>
        {activeMission && (
          <button onClick={onViewMission} className="active-mission-link">
            · 1 Active Mission →
          </button>
        )}
      </div>
    </div>
  );
}
```

### 2.3 Nuevo Componente: SectionHeader

```tsx
// NUEVO: Cabecera de seccion estilo terminal
function SectionHeader({ title }: { title: string }) {
  return (
    <div className="section-header">
      <span className="section-ornament">═══════</span>
      <span className="section-title">{title}</span>
      <span className="section-ornament">═══════</span>
    </div>
  );
}
```

---

## 3. NUEVOS ESTILOS CSS (globals.css)

```css
/* ═══════════════════════════════════════════════════════════
   DASHBOARD LAYOUT - Option 2 Redesign
   ═══════════════════════════════════════════════════════════ */

/* Status Card */
.status-card {
  border: 1px solid var(--amber-dark);
  background: var(--bg-card);
  padding: 12px 16px;
  margin: 12px 0;
}

.status-card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-card-row.secondary {
  margin-top: 8px;
  font-size: 12px;
  color: var(--amber-dim);
}

.wallet-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--green);
  animation: pulse-glow 2s ease-in-out infinite;
}

.ember-balance {
  color: var(--amber-bright);
  font-weight: 600;
  font-size: 16px;
}

.active-mission-link {
  background: none;
  border: none;
  color: var(--cyan);
  cursor: pointer;
  font-family: inherit;
  font-size: inherit;
}

.active-mission-link:hover {
  text-decoration: underline;
}

/* Section Headers */
.section-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 20px 0 12px;
  font-family: 'VT323', monospace;
}

.section-ornament {
  color: var(--amber-dark);
  font-size: 12px;
  letter-spacing: 2px;
}

.section-title {
  color: var(--amber-dim);
  font-size: 11px;
  letter-spacing: 3px;
  text-transform: uppercase;
}

/* Primary Button (PLAY) */
.menu-btn.primary {
  background: var(--amber);
  color: var(--bg-dark);
  border: 2px solid var(--amber);
  text-shadow: none;
}

.menu-btn.primary:hover {
  background: var(--amber-bright);
  border-color: var(--amber-bright);
}

/* Button with subtitle */
.menu-btn .btn-subtitle {
  font-size: 11px;
  color: var(--amber-dim);
  font-weight: 400;
  margin-top: 2px;
}

.menu-btn.primary .btn-subtitle {
  color: var(--bg-dark);
  opacity: 0.7;
}

/* Features Grid (3 columns) */
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.feature-card {
  border: 1px solid var(--amber-dark);
  background: var(--bg-card);
  padding: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.1s;
}

.feature-card:hover {
  border-color: var(--amber);
  background: rgba(255, 149, 0, 0.05);
}

.feature-card .icon {
  font-size: 20px;
  margin-bottom: 4px;
}

.feature-card .title {
  font-size: 12px;
  font-weight: 600;
  color: var(--amber-bright);
}

.feature-card .subtitle {
  font-size: 10px;
  color: var(--amber-dim);
  margin-top: 2px;
}

.feature-card .badge {
  display: inline-block;
  background: var(--red);
  color: white;
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 2px;
  margin-left: 4px;
}

/* World Section (horizontal row) */
.world-row {
  display: flex;
  border: 1px solid var(--amber-dark);
  background: var(--bg-card);
}

.world-item {
  flex: 1;
  padding: 10px;
  text-align: center;
  cursor: pointer;
  border-right: 1px solid var(--amber-dark);
  transition: all 0.1s;
  font-size: 12px;
}

.world-item:last-child {
  border-right: none;
}

.world-item:hover {
  background: rgba(255, 149, 0, 0.05);
}

.world-item .badge {
  background: var(--cyan);
  color: var(--bg-dark);
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 2px;
  margin-left: 4px;
}
```

---

## 4. LAYOUT JSX COMPLETO

```tsx
// MainMenu.tsx - Nueva estructura
export function MainMenu({
  wallet,
  emberBalance,
  emissaryCount,
  unreadMessages,
  activeMission,
  activeEventsCount,
  playerRank,
  onNavigate,
  onConnect,
  onDisconnect,
}: MainMenuProps) {

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">

      {/* ══════ HEADER ══════ */}
      <div className="text-center mb-2 relative">
        <button onClick={() => onNavigate('settings')} className="settings-btn">
          ⚙️
        </button>
        <Image src="/logo.png" alt="Emberholm" width={180} height={60} />
        <p className="subtitle">MINI APP</p>
      </div>

      {/* ══════ WALLET / STATUS CARD ══════ */}
      {wallet ? (
        <StatusCard
          wallet={wallet}
          emberBalance={emberBalance}
          emissaryCount={emissaryCount}
          activeMission={activeMission}
          onViewMission={() => onNavigate('timer')}
        />
      ) : (
        <button onClick={() => setShowWalletModal(true)} className="btn large">
          CONNECT WALLET
        </button>
      )}

      {/* ══════ GAMEPLAY SECTION ══════ */}
      <SectionHeader title="GAMEPLAY" />

      <div className="space-y-2">
        {/* PLAY - Primary CTA */}
        <button onClick={() => onNavigate('play')} className="menu-btn primary">
          <span className="icon">▶</span>
          <div className="flex-1 text-left">
            <div>PLAY</div>
            <div className="btn-subtitle">Start missions and earn $EMBER</div>
          </div>
        </button>

        {/* MINT */}
        <button onClick={() => onNavigate('mint')} className="menu-btn">
          <span className="icon">◈</span>
          <div className="flex-1 text-left">
            <div>MINT EMISSARY</div>
            <div className="btn-subtitle">Join the ranks of Emberholm</div>
          </div>
        </button>
      </div>

      {/* ══════ FEATURES SECTION ══════ */}
      <SectionHeader title="FEATURES" />

      <div className="features-grid">
        <button onClick={() => onNavigate('vault')} className="feature-card">
          <div className="icon">💰</div>
          <div className="title">VAULT</div>
          <div className="subtitle">Items & Tokens</div>
        </button>

        <button onClick={() => onNavigate('social-globe')} className="feature-card">
          <div className="icon">🔮</div>
          <div className="title">
            SOCIAL
            {unreadMessages > 0 && <span className="badge">{unreadMessages}</span>}
          </div>
          <div className="subtitle">messages</div>
        </button>

        <button onClick={() => onNavigate('leaderboard')} className="feature-card">
          <div className="icon">🏆</div>
          <div className="title">RANKS</div>
          <div className="subtitle">#{playerRank || '---'} global</div>
        </button>
      </div>

      {/* ══════ WORLD SECTION ══════ */}
      <SectionHeader title="WORLD" />

      <div className="world-row">
        <button onClick={() => onNavigate('events')} className="world-item">
          📜 EVENTS
          {activeEventsCount > 0 && <span className="badge">{activeEventsCount}</span>}
        </button>
        <button onClick={() => onNavigate('lore')} className="world-item">
          🔥 LORE
        </button>
        <button onClick={() => onNavigate('tutorial')} className="world-item">
          ? GUIDE
        </button>
      </div>

      {/* Wallet Modal (sin cambios) */}
      {/* ... */}
    </div>
  );
}
```

---

## 5. ARCHIVOS A MODIFICAR

| Archivo | Tipo de Cambio | Riesgo |
|---------|----------------|--------|
| `components/screens/MainMenu.tsx` | **Mayor** - Nueva estructura | Medio |
| `app/globals.css` | **Adicion** - Nuevos estilos | Bajo |
| `lib/store.tsx` | **Menor** - Agregar activeEventsCount, playerRank | Bajo |
| `app/page.tsx` | **Menor** - Pasar nuevas props a MainMenu | Bajo |

---

## 6. NUEVAS PROPS REQUERIDAS

```tsx
interface MainMenuProps {
  // Existentes
  wallet?: string | null;
  emberBalance?: number;
  emissaryCount?: number;
  unreadMessages?: number;
  onNavigate: (screen: AppScreen) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;

  // NUEVAS
  activeMission?: ActiveMicroMission | null;  // Para mostrar en status card
  activeEventsCount?: number;                  // Para badge en EVENTS
  playerRank?: number | null;                  // Para mostrar en RANKS
}
```

---

## 7. FLUJO DE NAVEGACION ACTUALIZADO

```
ANTES:
Menu → Play → [Missions | Micro-missions | Emissaries | Leaderboard]

DESPUES:
Menu → Play → [Missions | Micro-missions | Emissaries]  (Leaderboard movido a Menu)
Menu → Ranks → Leaderboard (acceso directo)
```

---

## 8. CONSIDERACIONES DE MOBILE

- **Touch targets**: Todos los botones >= 44px de altura
- **Features grid**: 3 columnas en mobile (cards compactas)
- **World row**: Horizontal scrollable si es necesario
- **Status card**: Responsive, stack vertical en <320px

---

## 9. PRESERVACION DE IDENTIDAD

### Elementos que NO cambian:
- ImmersionBar (intacta)
- Logo y branding
- Color scheme (amber)
- Fuentes (Pixelify Sans, VT323)
- CRT effects (scanlines, vignette)
- Portal-box style
- Animaciones de entrada

### Elementos que cambian:
- Layout de botones (de lista a secciones)
- Adicion de StatusCard
- Headers de seccion
- Grid de features
- Fila horizontal de WORLD

---

## 10. CHECKLIST PRE-IMPLEMENTACION

Antes de implementar, confirmar:

- [ ] Se mantiene la estetica retro-terminal
- [ ] PLAY sigue siendo el boton mas prominente
- [ ] Todos los elementos actuales son accesibles
- [ ] Mobile-first responsive
- [ ] No se pierde funcionalidad
- [ ] Lore y narrativa preservados

---

## 11. PROTOTIPO HTML STANDALONE

Cuando se confirme, creare:

```
/prototypes/
  └── option-2-dashboard.html
```

Este archivo sera:
- HTML completo standalone (no requiere servidor)
- CSS inline copiando estilos de globals.css
- JavaScript basico para interacciones (click feedback)
- Responsive design
- Comentarios explicativos

---

## CONFIRMACION REQUERIDA

Para proceder con la implementacion del prototipo, necesito confirmacion de:

1. **Estructura general** - ¿La division en 3 secciones (GAMEPLAY/FEATURES/WORLD) es correcta?
2. **StatusCard** - ¿Incluir el card de estado con balance y mision activa?
3. **RANKS extraido** - ¿Mover Leaderboard del submenu de PLAY al menu principal?
4. **Renombrar TUTORIAL → GUIDE** - ¿Aceptable el cambio de nombre?

**Esperando tu confirmacion para crear el prototipo HTML.**
