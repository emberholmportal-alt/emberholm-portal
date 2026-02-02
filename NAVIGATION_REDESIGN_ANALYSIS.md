# Analisis de Rediseno - Emberholm Portal

## 1. ESTRUCTURA ACTUAL DOCUMENTADA

### 1.1 Componentes de Layout

| Componente | Existe | Ubicacion |
|------------|--------|-----------|
| **ImmersionBar** (Top Bar) | SI | `/mini-app/components/ImmersionBar.tsx` |
| **MainMenu** | SI | `/mini-app/components/screens/MainMenu.tsx` |
| **CRTOverlay** | SI | `/mini-app/components/CRTOverlay.tsx` |
| **LivingWallpaper** | SI | `/mini-app/components/LivingWallpaper.tsx` |
| **Footer** | NO | No existe como componente separado |

### 1.2 MainMenu.tsx Actual

**Archivo:** `/mini-app/components/screens/MainMenu.tsx`

**Elementos identificados:**
- **Linea 113-137:** Header con Logo y Settings (NO TOCAR)
- **Linea 119-126:** Settings Button - Top Right (NO TOCAR)
- **Linea 128-136:** Logo Image + Subtitle "MINI APP" (NO TOCAR)
- **Linea 139-169:** Connect Wallet Button (NO TOCAR)
- **Linea 171-201:** BOTONES DEL MENU (ESTO CAMBIA)
- **Linea 203-265:** Wallet Connection Modal (NO TOCAR)

**Botones actuales (7):**
```typescript
const menuItems: MenuItem[] = [
  { id: 'play', title: 'PLAY', icon: '▶' },
  { id: 'mint', title: 'MINT EMISSARY', icon: '◈' },
  { id: 'social-globe', title: 'SOCIAL', icon: '', iconSrc: '/icons/crystalball.png', badge: unreadMessages },
  { id: 'vault', title: 'VAULT', icon: '', iconSrc: '/icons/moneybag.png' },
  { id: 'events', title: 'EVENTS', icon: '', iconSrc: '/icons/scroll.png' },
  { id: 'lore', title: 'LORE', icon: '', iconSrc: '/icons/EternalTorch.png' },
  { id: 'tutorial', title: 'TUTORIAL', icon: '?' },
];
```

### 1.3 CSS Actual

**Archivo:** `/mini-app/app/globals.css`

**Estilos relevantes:**
- **Linea 412-456:** `.menu-btn` - Estilos de botones del menu
- **Linea 1096-1102:** `.menu-container` - Container de botones
- **Linea 1049-1056:** `.notif-badge` - Badge de notificaciones

---

## 2. CAMBIOS PROPUESTOS

### 2.1 Nuevos 6 Botones (segun boceto)

| # | Label | Screen ID | Estilo | Badge |
|---|-------|-----------|--------|-------|
| 1 | MINT / INVOKE | `mint` | ROJO | No |
| 2 | [ PLAY ] | `play` | Naranja | SI (misiones activas) |
| 3 | [ COMO JUGAR ] | `tutorial` | Naranja | No |
| 4 | [ VAULT ] | `vault` | Naranja | No |
| 5 | [ WORLD CHAT ] | `global-chat` | Naranja | No |
| 6 | [ INFO ] | `info` | Naranja | No |

### 2.2 Mapeo de funcionalidades antiguas

**Se mantienen directamente:**
- MINT/INVOKE -> `mint` screen
- PLAY -> `play` screen (submenu con misiones)
- VAULT -> `vault` screen
- TUTORIAL -> Renombrado a "COMO JUGAR"

**Se consolidan en INFO:**
- LORE -> Dentro de INFO
- EVENTS -> Dentro de INFO
- SOCIAL (globe) -> Reemplazado por WORLD CHAT directo

**Nuevo:**
- WORLD CHAT -> Acceso directo a `global-chat`
- INFO -> Nueva pantalla con submenu (Lore, Events, etc.)

### 2.3 MainMenu.tsx - CAMBIOS ESPECIFICOS

**ANTES (lineas 52-93):**
```typescript
const menuItems: MenuItem[] = [
  { id: 'play', title: 'PLAY', icon: '▶' },
  { id: 'mint', title: 'MINT EMISSARY', icon: '◈' },
  { id: 'social-globe', title: 'SOCIAL', iconSrc: '/icons/crystalball.png', badge: unreadMessages },
  { id: 'vault', title: 'VAULT', iconSrc: '/icons/moneybag.png' },
  { id: 'events', title: 'EVENTS', iconSrc: '/icons/scroll.png' },
  { id: 'lore', title: 'LORE', iconSrc: '/icons/EternalTorch.png' },
  { id: 'tutorial', title: 'TUTORIAL', icon: '?' },
];
```

**DESPUES:**
```typescript
// Nueva interfaz para soportar estilo especial
interface MenuItem {
  id: AppScreen;
  title: string;
  icon?: string;
  iconSrc?: string;
  badge?: number;
  variant?: 'primary' | 'default'; // Para boton rojo
}

const menuItems: MenuItem[] = [
  { id: 'mint', title: 'MINT / INVOKE', variant: 'primary' },
  { id: 'play', title: '[ PLAY ]', badge: playNotifications },
  { id: 'tutorial', title: '[ COMO JUGAR ]' },
  { id: 'vault', title: '[ VAULT ]' },
  { id: 'global-chat', title: '[ WORLD CHAT ]' },
  { id: 'info', title: '[ INFO ]' },
];
```

### 2.4 CSS - AGREGAR (no reemplazar)

```css
/* Boton primario (MINT) - Rojo */
.menu-btn.primary {
  background: #ff4444;
  color: #000000;
  border-color: #ff4444;
  font-weight: bold;
  box-shadow: 0 0 20px rgba(255, 68, 68, 0.3);
}

.menu-btn.primary:hover {
  background: #ff6666;
  box-shadow: 0 0 30px rgba(255, 68, 68, 0.5);
}
```

---

## 3. COMPONENTES NUEVOS A CREAR

### 3.1 InfoScreen.tsx

Nueva pantalla que agrupa:
- LORE (acceso a LoreScreen)
- EVENTS (acceso a EventsScreen)
- ANNOUNCEMENTS (futuro)
- WHITEPAPER (link externo)
- TOKENOMICS (link externo)
- SOCIAL/CREDITS (futuro)

### 3.2 Actualizacion de store.tsx

Agregar nuevo screen type:
```typescript
export type AppScreen =
  // ... existentes ...
  | 'info';  // NUEVO - Info submenu
```

---

## 4. ELEMENTOS QUE NO SE TOCAN

### 4.1 ImmersionBar (Top Bar)
- Ubicacion: `/mini-app/components/ImmersionBar.tsx`
- Contenido: Sound toggle, Music toggle, Flame indicator, Time/Date, Weather
- Estado: INTACTO

### 4.2 Logo y Header
- Ubicacion: MainMenu.tsx lineas 113-137
- Contenido: Logo image, subtitle "MINI APP", settings button
- Estado: INTACTO

### 4.3 Connect Wallet
- Ubicacion: MainMenu.tsx lineas 139-169
- Contenido: Wallet connection flow
- Estado: INTACTO

### 4.4 Wallet Modal
- Ubicacion: MainMenu.tsx lineas 203-265
- Contenido: Wallet options modal
- Estado: INTACTO

### 4.5 Estilos globales
- Ubicacion: `/mini-app/app/globals.css`
- Variables CSS, fuentes, efectos CRT
- Estado: INTACTO (solo se agregan nuevos estilos)

---

## 5. RIESGO: BAJO

**Por que es seguro:**
- Solo cambiamos el array de menuItems (6 lineas)
- Solo agregamos una clase CSS nueva (.menu-btn.primary)
- Creamos un componente nuevo (InfoScreen) sin modificar existentes
- Todos los screens existentes siguen funcionando igual
- Facil rollback si algo falla

---

## 6. PLAN DE IMPLEMENTACION

### Paso 1: Actualizar store.tsx
- Agregar `'info'` al type AppScreen

### Paso 2: Crear InfoScreen.tsx
- Nueva pantalla con submenu de informacion

### Paso 3: Actualizar MainMenu.tsx
- Cambiar array menuItems de 7 a 6 botones
- Agregar logica para variant='primary'
- Calcular playNotifications badge

### Paso 4: Actualizar globals.css
- Agregar estilos para .menu-btn.primary

### Paso 5: Actualizar page.tsx
- Agregar routing para InfoScreen

### Paso 6: Test y commit

---

## 7. ARCHIVOS AFECTADOS

| Archivo | Tipo de cambio |
|---------|---------------|
| `/mini-app/lib/store.tsx` | Agregar tipo 'info' |
| `/mini-app/components/screens/MainMenu.tsx` | Modificar menuItems |
| `/mini-app/components/screens/InfoScreen.tsx` | NUEVO |
| `/mini-app/app/globals.css` | Agregar estilos |
| `/mini-app/app/page.tsx` | Agregar routing |
