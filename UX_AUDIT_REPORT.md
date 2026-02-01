# Auditoria UX/Legibilidad - Emberholm Portal

**Fecha:** 2026-02-01
**Version analizada:** mini-app (Tailwind CSS + CSS Custom Properties)

---

## RESUMEN EJECUTIVO

| Metrica | Puntuacion | Notas |
|---------|------------|-------|
| **Legibilidad General** | 6.5/10 | Colores principales buenos, pero textos secundarios con bajo contraste |
| **Contraste WCAG** | 5/10 | 3 de 5 variantes de color fallan WCAG AA |
| **Tipografia** | 7/10 | Fuentes apropiadas pero tamanios muy pequenios en algunos lugares |
| **Espaciado** | 7.5/10 | Buena estructura pero densidad alta en algunas pantallas |
| **Interactividad** | 6/10 | Faltan focus states visibles y algunos touch targets son pequenios |
| **Accesibilidad** | 4/10 | Faltan aria-labels, skip links y soporte para reduced motion |
| **Responsive** | 8/10 | Buen enfoque mobile-first, bien implementado |

### Top 3 Problemas Criticos

1. **Contraste insuficiente** en `--amber-dark` (#804d00) y `--amber-darker` (#4d2e00) - ratio ~2.6:1 y ~1.5:1 respectivamente (WCAG requiere minimo 4.5:1)
2. **Tamanios de fuente muy pequenios** - Uso de 9px, 10px en textos importantes (.slot-name, .stat-label, .notif-badge)
3. **Focus states invisibles** - La navegacion por teclado es practicamente inutilizable

### Impacto Estimado de Mejoras

- **Alto impacto, bajo esfuerzo:** Ajustar colores de bajo contraste (+30% legibilidad)
- **Alto impacto, medio esfuerzo:** Mejorar focus states (+50% accesibilidad)
- **Medio impacto, bajo esfuerzo:** Aumentar tamanios minimos de texto (+20% legibilidad)

---

## ANALISIS DE CONTRASTE

### Problemas Encontrados

| Combinacion | Ratio Actual | Requerido WCAG AA | Estado |
|-------------|--------------|-------------------|--------|
| `--amber` (#ff9500) sobre `--bg-dark` (#0a0705) | ~9:1 | 4.5:1 | PASA |
| `--amber-bright` (#ffb340) sobre `--bg-dark` | ~11:1 | 4.5:1 | PASA |
| `--amber-dim` (#cc7700) sobre `--bg-dark` | ~5.8:1 | 4.5:1 | PASA (justo) |
| `--amber-dark` (#804d00) sobre `--bg-dark` | ~2.6:1 | 4.5:1 | **FALLA** |
| `--amber-darker` (#4d2e00) sobre `--bg-dark` | ~1.5:1 | 4.5:1 | **FALLA** |
| `--red` (#ff4444) sobre `--bg-dark` | ~4.9:1 | 4.5:1 | PASA (limite) |

#### Ubicaciones del Problema

- `.section-title` - Usa `--amber-dim` (aceptable pero limite)
- `.data-row` border - Usa `--amber-darker` (invisible)
- `.slot .slot-name` - Usa `--amber-dim` con texto de 9px (ilegible)
- `.stat-label` - Usa `--amber-dim` a 10px (dificil de leer)
- Placeholders de inputs - Usa `--amber-darker` (casi invisible)
- Borders decorativos - Usa `--amber-dark` y `--amber-darker`

### Propuestas de Mejora

```css
/* ANTES: Variables problematicas */
--amber-dark: #804d00;    /* ratio 2.6:1 - FALLA */
--amber-darker: #4d2e00;  /* ratio 1.5:1 - FALLA */

/* DESPUES: Colores mejorados manteniendo estetica */
--amber-dark: #b36b00;    /* ratio ~4.5:1 - PASA AA */
--amber-darker: #8a5200;  /* ratio ~3.5:1 - Para decorativos */
--amber-muted: #996600;   /* ratio ~4.0:1 - Nueva variante para texto secundario */
```

**Propuesta de paleta extendida:**

```css
:root {
  /* Amber Palette - MEJORADO */
  --amber: #ff9500;           /* Principal - ratio 9:1 */
  --amber-bright: #ffb340;    /* Destacados - ratio 11:1 */
  --amber-dim: #d98c00;       /* Secundario - ratio 6.5:1 (MEJORADO de #cc7700) */
  --amber-dark: #b36b00;      /* Terciario - ratio 4.5:1 (MEJORADO de #804d00) */
  --amber-darker: #8a5200;    /* Decorativo - ratio 3.5:1 */

  /* Nuevo: Para bordes/decoracion que no necesitan ser legibles */
  --amber-border: #5a3800;    /* Solo para bordes, no texto */
}
```

---

## ANALISIS TIPOGRAFICO

### Configuracion Actual

| Elemento | Fuente | Tamanio | Line-Height | Peso |
|----------|--------|---------|-------------|------|
| Body default | Pixelify Sans | 16px | 1.4 | 400 |
| `.title` | Pixelify Sans | 32px | 1.4 | 700 |
| `.title-large` | Pixelify Sans | 42px | 1.4 | 700 |
| `.subtitle` | Pixelify Sans | 14px | 1.4 | 500 |
| `.section-title` | Pixelify Sans | 12px | 1.4 | 600 |
| `.top-bar` | VT323 | 13px | 1.4 | 400 |
| `.slot-name` | Pixelify Sans | **9px** | - | 400 |
| `.stat-label` | Pixelify Sans | **10px** | - | 400 |
| `.notif-badge` | Pixelify Sans | **11px** | - | 400 |
| `.btn.tiny` | Pixelify Sans | **10px** | - | 600 |

### Problemas Encontrados

1. **Tamanios criticos demasiado pequenios:**
   - 9px en `.slot-name` - Ilegible en la mayoria de dispositivos
   - 10px en `.stat-label`, `.btn.tiny`, `[10px]` en ImmersionBar
   - 11px en badges y estados

2. **Line-height global de 1.4:**
   - Aceptable para titulos pero muy ajustado para parrafos largos (lore, descripciones)
   - Los bloques de texto en `.lore-card-content` usan 1.6 (bien), pero no es consistente

3. **Text-shadow en todo el body:**
   ```css
   body {
     text-shadow: 0 0 5px var(--amber), 0 0 10px var(--amber-glow);
   }
   ```
   - Reduce legibilidad en textos pequenios
   - Dificulta la lectura de parrafos largos
   - El efecto "glow" es bueno para titulos, no para cuerpo de texto

4. **Letter-spacing excesivo en subtitulos:**
   - `.subtitle` tiene `letter-spacing: 3px` - Demasiado para 14px

### Propuestas de Mejora

```css
/* TAMANIOS MINIMOS - Subir a 12px minimo */
.slot-name {
  font-size: 11px; /* Era 9px */
}

.stat-label {
  font-size: 12px; /* Era 10px */
}

.btn.tiny {
  font-size: 11px; /* Era 10px */
  padding: 5px 12px; /* Aumentar padding */
}

.notif-badge {
  font-size: 11px; /* Mantener, pero aumentar padding */
  padding: 3px 10px;
}

/* LINE-HEIGHT mejorado */
body {
  line-height: 1.5; /* Era 1.4 */
}

.lore-card-content p,
.chat-bubble,
.data-box-content {
  line-height: 1.6; /* Para textos largos */
}

/* TEXT-SHADOW selectivo */
body {
  text-shadow: none; /* Quitar del body */
}

.title,
.title-large,
.emissary-name,
.menu-btn,
.btn {
  text-shadow: 0 0 5px var(--amber), 0 0 10px var(--amber-glow);
}

/* LETTER-SPACING ajustado */
.subtitle {
  letter-spacing: 2px; /* Era 3px */
}

.section-title {
  letter-spacing: 1.5px; /* Era 2px */
}
```

---

## ANALISIS DE ESPACIADO Y LAYOUT

### Estructura Actual

- **Container principal:** `max-width: 420px` (mobile-first)
- **Screen padding:** `15px`
- **Gap entre elementos:** `8px` (menu), `12px` (cards)
- **Top bar padding:** `10px 15px`

### Problemas Encontrados

1. **Densidad de informacion alta en EmissaryCard:**
   - Stats, estado, nivel, guild, energia, todo en un espacio reducido
   - Font sizes muy pequenios (xs = 12px, pero algunos son 10px)

2. **Slots de inventario muy compactos:**
   - 60x60px con texto de 9px
   - Dificil tocar en mobile

3. **Menu buttons adecuados** (16px padding, buen tamanio)

4. **Scroll areas sin padding inferior:**
   - `.scroll-area` termina abruptamente en mobile

### Propuestas de Mejora

```css
/* Slots de inventario mas grandes */
.slot {
  width: 70px;  /* Era 60px */
  height: 70px; /* Era 60px */
}

.slot .slot-name {
  font-size: 11px; /* Era 9px */
  margin-top: 4px; /* Era 2px */
}

/* Mejor breathing room en scroll areas */
.scroll-area {
  padding-bottom: 20px;
}

/* Cards con mejor espaciado interno */
.emissary-card {
  padding: 14px; /* Era 12px */
}

.data-box {
  padding: 14px; /* Era 12px */
  margin: 10px 0; /* Era 8px */
}
```

---

## ANALISIS DE ELEMENTOS INTERACTIVOS

### Botones

| Clase | Padding | Touch Target | Estado |
|-------|---------|--------------|--------|
| `.btn` | 14px 20px | ~48px height | Bueno |
| `.btn-small` | 8px 12px | ~32px height | **Pequenio** |
| `.btn.tiny` | 4px 10px | ~22px height | **Muy pequenio** |
| `.menu-btn` | 16px 20px | ~52px height | Bueno |
| `.back-btn` | 12px 20px | ~40px height | Aceptable |

### Problemas Encontrados

1. **Focus states invisibles:**
   ```css
   /* No hay definicion de :focus-visible en la mayoria de elementos */
   .search-input:focus {
     outline: none; /* MALO - elimina el focus */
     border-color: var(--amber);
   }
   ```

2. **Botones pequenios no cumplen 44x44px minimo:**
   - `.btn.tiny` - Solo 22px de altura
   - `.btn-small` - Solo 32px de altura
   - Toggle switches en settings - 44x24px (bien en ancho, corto en altura)

3. **Estados hover buenos pero inconsistentes:**
   - Algunos usan `scale(1.02)` (framer-motion)
   - Otros solo cambian color de borde
   - No hay patron unificado

4. **Estados disabled:**
   ```css
   .btn:disabled {
     opacity: 0.5; /* Poco contraste con fondo oscuro */
     cursor: not-allowed;
   }
   ```

### Propuestas de Mejora

```css
/* FOCUS STATES visibles manteniendo estetica */
:focus-visible {
  outline: 2px solid var(--amber);
  outline-offset: 2px;
  /* Alternativa retro: */
  /* box-shadow: 0 0 0 2px var(--amber), 0 0 10px var(--amber-glow); */
}

/* Quitar outline:none y reemplazar */
.search-input:focus,
.chat-input:focus {
  outline: none;
  border-color: var(--amber);
  box-shadow: 0 0 5px var(--amber-glow);
}

/* Touch targets minimos */
.btn-small {
  padding: 10px 14px; /* Era 8px 12px */
  min-height: 44px;
}

.btn.tiny {
  padding: 8px 14px; /* Era 4px 10px */
  min-height: 36px; /* Compromiso entre estetica y usabilidad */
}

/* Estados disabled mas claros */
.btn:disabled {
  opacity: 0.4;
  background: var(--amber-dark);
  color: var(--amber-dim);
  cursor: not-allowed;
}
```

---

## ANALISIS DE ACCESIBILIDAD

### Problemas Criticos

1. **ARIA labels faltantes:**
   ```tsx
   // MainMenu.tsx - Boton sin label
   <button onClick={() => onNavigate('settings')} title="Settings">
     <span className="text-xl">?</span>
   </button>
   // Deberia tener: aria-label="Settings"
   ```

2. **Informacion solo por color:**
   - Estados de emissary (READY=verde, MISSION=cyan, FALLEN=rojo)
   - No hay texto alternativo para usuarios con daltonismo

3. **Sin skip links:**
   - No hay manera de saltar al contenido principal

4. **Sin soporte para reduced-motion:**
   ```css
   /* Falta: */
   @media (prefers-reduced-motion: reduce) {
     *, *::before, *::after {
       animation-duration: 0.01ms !important;
       transition-duration: 0.01ms !important;
     }
   }
   ```

5. **Modales sin focus trap:**
   - `Modal.tsx` maneja Escape pero no atrapa el foco dentro del modal

6. **Imagenes sin alt descriptivo:**
   ```tsx
   // Varios lugares usan alt="" en iconos decorativos (correcto)
   // Pero algunas imagenes importantes carecen de alt util
   <img src={emissary.image_url} alt={emissary.name} /> // OK
   <Image src="/icons/fire.png" alt="" /> // Deberia describir el estado
   ```

### Propuestas de Mejora

```tsx
// 1. ARIA labels en botones de iconos
<button
  onClick={() => onNavigate('settings')}
  aria-label="Open settings menu"
  title="Settings"
>

// 2. Estados con texto, no solo color
<span className={`${stateStyle.color}`}>
  <span aria-hidden="true">{stateStyle.icon}</span>
  <span className="sr-only">{stateStyle.label}</span>
  <span className="hidden sm:inline">{stateStyle.label}</span>
</span>

// 3. Skip link (agregar al layout)
<a href="#main-content" className="sr-only focus:not-sr-only focus:absolute ...">
  Skip to main content
</a>
```

```css
/* 4. Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  .crt-moving-line,
  .animate-pulse,
  .animate-blink {
    animation: none !important;
  }
}

/* 5. Screen reader only class */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

---

## ANALISIS RESPONSIVE

### Configuracion Actual

- **Breakpoint principal:** max-width 420px (frame de mobile)
- **Safe areas:** Implementadas con `env(safe-area-inset-*)`
- **Touch scrolling:** `-webkit-overflow-scrolling: touch`

### Puntos Positivos

- Buen enfoque mobile-first
- Uso correcto de `100dvh` para altura dinamica
- Grid de 2 columnas para paises
- Scroll areas con estilos personalizados

### Problemas Encontrados

1. **Breakpoints limitados:**
   - Solo hay `sm:inline` en algunos lugares
   - No hay ajustes para tablets (768px)

2. **Texto oculto en mobile:**
   ```tsx
   // ImmersionBar.tsx
   <span className="hidden sm:inline ml-1">{realm.weather.name}</span>
   // Estado del emissary
   <span className="hidden sm:inline">{stateStyle.label}</span>
   ```
   - Pierde informacion importante en mobile

3. **Truncado agresivo:**
   - Nombres de emissary con `truncate` pueden cortar nombres importantes

### Propuestas de Mejora

```css
/* Breakpoints adicionales para tablets */
@media (min-width: 768px) {
  .crt-screen {
    max-width: 520px; /* Un poco mas ancho en tablets */
  }

  .menu-btn {
    padding: 18px 24px;
    font-size: 18px;
  }

  .slot {
    width: 80px;
    height: 80px;
  }
}

/* Mejor manejo de texto truncado */
.emissary-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px; /* Limitar pero no truncar muy pronto */
}
```

---

## RECOMENDACIONES PRIORIZADAS

### CRITICO (Implementar inmediatamente)

| # | Problema | Solucion | Archivo | Esfuerzo |
|---|----------|----------|---------|----------|
| 1 | Colores de bajo contraste | Actualizar `--amber-dark` y `--amber-darker` | `globals.css:58-65` | Bajo |
| 2 | Focus states invisibles | Agregar `:focus-visible` global | `globals.css` (nuevo) | Bajo |
| 3 | Texto de 9-10px ilegible | Aumentar minimos a 11-12px | `globals.css:600-604, 1006-1011` | Bajo |
| 4 | Text-shadow en body | Mover a elementos especificos | `globals.css:110` | Bajo |

### IMPORTANTE (Implementar pronto)

| # | Problema | Solucion | Archivo | Esfuerzo |
|---|----------|----------|---------|----------|
| 5 | Touch targets pequenios | Aumentar padding de `.btn.tiny` y `.btn-small` | `globals.css:357-366` | Bajo |
| 6 | ARIA labels faltantes | Agregar a botones de iconos | Componentes varios | Medio |
| 7 | Sin reduced-motion | Agregar media query | `globals.css` (nuevo) | Bajo |
| 8 | Estados solo por color | Agregar texto/iconos descriptivos | `EmissaryCard.tsx` | Medio |

### MEJORA (Nice to have)

| # | Problema | Solucion | Archivo | Esfuerzo |
|---|----------|----------|---------|----------|
| 9 | Line-height ajustado | Aumentar a 1.5 en body, 1.6 en textos largos | `globals.css:108` | Bajo |
| 10 | Skip link | Agregar al layout principal | Layout component | Bajo |
| 11 | Slots pequenios | Aumentar de 60px a 70px | `globals.css:563-575` | Bajo |
| 12 | Focus trap en modales | Usar `focus-trap-react` | `Modal.tsx` | Medio |

---

## PROPUESTA DE PALETA MEJORADA

Manteniendo la estetica retro-terminal pero con mejor contraste:

```css
:root {
  /* ═══════════════════════════════════════════════════════════
     PALETA MEJORADA - Mantiene estetica, mejora contraste
     ═══════════════════════════════════════════════════════════ */

  /* Amber Palette - ACTUALIZADA */
  --amber: #ff9500;           /* Principal - ratio 9:1 - SIN CAMBIO */
  --amber-bright: #ffb340;    /* Destacados - ratio 11:1 - SIN CAMBIO */
  --amber-dim: #d98c00;       /* Secundario - ratio 6.5:1 (era #cc7700 ~5.8:1) */
  --amber-dark: #b36b00;      /* Terciario legible - ratio 4.5:1 (era #804d00 ~2.6:1) */
  --amber-darker: #8a5200;    /* Decorativo - ratio 3.5:1 (era #4d2e00 ~1.5:1) */
  --amber-glow: rgba(255, 149, 0, 0.5); /* SIN CAMBIO */

  /* NUEVO: Variante para bordes (no necesita contraste) */
  --amber-border: #5a3800;

  /* Accent Colors - SIN CAMBIO (todos pasan WCAG) */
  --cyan: #00d4ff;
  --cyan-glow: rgba(0, 212, 255, 0.5);
  --red: #ff4444;
  --green: #44ff44;
  --purple: #aa66ff;

  /* Background Colors - SIN CAMBIO */
  --bg-dark: #0a0705;
  --bg-screen: #0f0a05;
  --bg-panel: rgba(0, 0, 0, 0.3);
  --bg-card: rgba(0, 0, 0, 0.2);
}
```

### Comparacion Visual

| Variable | Antes | Despues | Mejora |
|----------|-------|---------|--------|
| `--amber-dim` | #cc7700 (5.8:1) | #d98c00 (6.5:1) | +12% contraste |
| `--amber-dark` | #804d00 (2.6:1) | #b36b00 (4.5:1) | +73% contraste |
| `--amber-darker` | #4d2e00 (1.5:1) | #8a5200 (3.5:1) | +133% contraste |

---

## ARCHIVOS A MODIFICAR

### Prioridad Alta

| Archivo | Cambios | Lineas aproximadas |
|---------|---------|-------------------|
| `mini-app/app/globals.css` | Variables de color, focus states, font sizes, reduced-motion | ~50 lineas |
| `mini-app/tailwind.config.ts` | Actualizar colores de ember si se usan ahi | ~10 lineas |

### Prioridad Media

| Archivo | Cambios |
|---------|---------|
| `mini-app/components/ui/EmissaryCard.tsx` | ARIA labels, texto en estados |
| `mini-app/components/ui/Modal.tsx` | Focus trap, ARIA attributes |
| `mini-app/components/screens/MainMenu.tsx` | ARIA labels en botones |
| `mini-app/components/ImmersionBar.tsx` | Mejores alt texts |

### Prioridad Baja

| Archivo | Cambios |
|---------|---------|
| `mini-app/components/screens/SettingsScreen.tsx` | Labels para sliders |
| `mini-app/components/ui/DataBox.tsx` | Roles ARIA |
| Layout principal | Skip link |

---

## NOTAS FINALES

### Que se MANTIENE (estetica retro-terminal)

- Fuentes pixeladas (Pixelify Sans, VT323)
- Color scheme amber/void
- Efecto de scanlines y CRT
- Animaciones de glitch y flicker
- Bordes rectangulares sin border-radius excesivo
- Efectos de glow en elementos destacados

### Que se MEJORA (UX sin romper identidad)

- Contraste de colores secundarios
- Tamanios de texto minimos
- Focus states visibles
- Touch targets adecuados
- Soporte para accesibilidad basica

---

*Auditoria generada por Claude Code - Lista para revision del equipo*
