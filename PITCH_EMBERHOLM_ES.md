# EMBERHOLM PORTAL

### Un RPG Medieval de Fantasía con NFTs Dinámicos en Base

---

<div align="center">

**35,000 Emissaries** | **Dual Economy** | **Zero Gas Missions** | **Dynamic Metadata**

*El reino está muriendo. Los Emissaries son su última esperanza.*

</div>

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [El Mundo de Emberholm](#2-el-mundo-de-emberholm)
3. [Cómo Funciona el Juego](#3-cómo-funciona-el-juego)
4. [Lo Que Nos Hace Diferentes](#4-lo-que-nos-hace-diferentes)
5. [Arquitectura Técnica](#5-arquitectura-técnica)
6. [Economía Dual: $EMBER y $ASH](#6-economía-dual-ember-y-ash)
7. [5 Smart Contracts en Base](#7-5-smart-contracts-en-base)
8. [Roadmap](#8-roadmap)
9. [Sobre el Desarrollo](#9-sobre-el-desarrollo)
10. [Preguntas Frecuentes](#10-preguntas-frecuentes)

---

## 1. RESUMEN EJECUTIVO

### ¿Qué es Emberholm Portal?

**Emberholm Portal** es un RPG medieval de fantasía donde controlas **Emissaries** — guerreros NFT únicos que completan misiones, ganan tokens, y determinan el destino de un reino al borde de la extinción.

### En 30 Segundos

> *Mintea un Emissary. Envíalo a misiones. Gana $EMBER. Sube de rango. Equípalo con items legendarios. Conquista tierras. Pero cuidado — la muerte puede ser permanente.*

### Características Clave

| Característica | Descripción |
|----------------|-------------|
| **35,000 NFTs Únicos** | Cada Emissary tiene raza, clase, guild y stats únicos |
| **Metadata Dinámica** | Tu NFT evoluciona — XP, nivel, logros visibles en OpenSea |
| **Cero Gas en Misiones** | Juega sin pagar transacciones constantes |
| **Economía Dual** | $EMBER (utility) + $ASH (gobernanza) |
| **Items On-Chain** | Armas, armaduras y runas como NFTs equipables |
| **11 Rangos de Progresión** | De Novice a Legendary — cada rango da más poder |
| **Muerte Permanente** | Riesgo real, decisiones que importan |

---

## 2. EL MUNDO DE EMBERHOLM

### La Historia

En el corazón del reino arde **La Llama Eterna** — fuego sagrado que mantiene la realidad estable. Pero la llama se está apagando.

**El Velo** — la barrera que separa nuestro mundo del **Vacío** — se desgarra. Entidades que no deberían existir comienzan a filtrarse.

Los **Emissaries** son la última línea de defensa. Guerreros, magos, pícaros y exploradores que arriesgan sus vidas en misiones peligrosas para reunir recursos, defender fronteras y buscar la manera de reavivar la llama.

### Las Seis Facciones

```
┌─────────────────────────────────────────────────────────────────┐
│                     LAS SEIS GUILDS DE EMBERHOLM                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ⚗️  CIRCLE OF MIST     │  Alquimistas y magos del conocimiento│
│      10,599 miembros    │  prohibido. Controlan el flujo mágico│
│                                                                 │
│  ☀️  ORDER OF DAWN      │  Paladines y clérigos de la luz.     │
│      6,341 miembros     │  Protectores de la civilización      │
│                                                                 │
│  🗡️  SHADOW GUILD       │  Espías y asesinos. Información      │
│      6,234 miembros     │  es poder, silencio es supervivencia │
│                                                                 │
│  ⚒️  FORGE LEGION       │  Guerreros y herreros. Acero,        │
│      4,538 miembros     │  fuerza y honor en batalla           │
│                                                                 │
│  🌀  VOID ECHOES        │  Nigromantes y espectrales.          │
│      4,302 miembros     │  Especialistas en sellar el Vacío    │
│                                                                 │
│  🔭  HORIZON WATCH      │  Exploradores y vigías del confín.   │
│      2,986 miembros     │  Cartógrafos de lo desconocido       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Razas y Clases

**8 Razas**: Human, Elf, Dwarf, Tiefling, Draconid, Gith, Triton, Goliath

**7 Clases**: Paladin, Cleric, Druid, Hunter, Rogue, Bard, Explorer

> Cada combinación de raza + clase + guild crea un Emissary único con fortalezas específicas para ciertas misiones.

---

## 3. CÓMO FUNCIONA EL JUEGO

### El Loop Principal

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   MINTEA     │────▶│   MISIONES   │────▶│  PROGRESA    │
│  Emissary    │     │  3h / 6h /12h│     │  XP + Aura   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │   GANA       │     │   EQUIPA     │
                     │   $EMBER     │     │   Items      │
                     └──────────────┘     └──────────────┘
                            │                    │
                            └────────┬───────────┘
                                     ▼
                            ┌──────────────┐
                            │  SUBE DE     │
                            │   RANGO      │
                            └──────────────┘
```

### Sistema de Misiones

| Dificultad | Duración | XP | $EMBER | Riesgo de Muerte |
|------------|----------|-----|--------|------------------|
| **EASY** | 3 horas | 60 | 10-25 | 0% |
| **MEDIUM** | 6 horas | 150 | 30-75 | 0.5% |
| **HARD** | 12 horas | 350 | 80-200 | 2% |
| **PARTY** | Variable | +20% | +20% | Variable |

> **Party Missions**: Requieren 5 Emissaries y dan bonus de 20% en todas las recompensas.

### Sistema de Rangos (Emissary Rank)

Tu Emissary sube de rango según su progreso. Cada rango desbloquea bonificaciones:

| Rango | Tier | Requisitos | Bonus $EMBER |
|-------|------|------------|--------------|
| Novice | 1 | Inicial | +2% |
| Apprentice | 2 | 1,000 XP, 50 Aura | +5% |
| Journeyman | 3 | 5,000 XP, 150 Aura | +10% |
| Adept | 4 | 15,000 XP, 400 Aura | +15% |
| Expert | 5 | 35,000 XP, 800 Aura | +22% |
| Master | 6 | 70,000 XP, 1,500 Aura | +30% |
| Grandmaster | 7 | 120,000 XP, 3,000 Aura | +40% |
| **Legendary** | 8 | 200,000 XP, 5,000 Aura | **+50%** |

### Sistema de Muerte

La muerte en Emberholm tiene consecuencias reales:

- **Misiones EASY**: 0% riesgo de muerte
- **Misiones MEDIUM**: 0.5% riesgo
- **Misiones HARD**: 2% riesgo

Cuando un Emissary muere, entra en estado **FALLEN**. Puedes resucitarlo pagando $EMBER:

| Muerte # | Costo |
|----------|-------|
| 1ra | 200 EMBER |
| 2da | 500 EMBER |
| 3ra | 1,000 EMBER |
| 4ta | 2,500 EMBER |
| 5ta | 5,000 EMBER |
| 6ta+ | 10,000 EMBER |

> La protección contra muerte aumenta con nivel, aura y equipo (máximo 80% protección).

---

## 4. LO QUE NOS HACE DIFERENTES

### Comparativa con Otros Proyectos NFT

| Característica | Emberholm Portal | Proyectos Típicos |
|----------------|------------------|-------------------|
| **Metadata** | Dinámica (cambia en tiempo real) | Estática (nunca cambia) |
| **Costo por jugar** | **$0 en misiones** | Gas en cada acción |
| **Progresión** | 11 rangos + achievements | Niveles básicos o ninguno |
| **Economía** | Dual token (utility + governance) | Single token |
| **Consecuencias** | Muerte permanente | Sin riesgo real |
| **Items** | NFTs on-chain equipables | Off-chain o inexistentes |
| **Visualización** | Stats visibles en marketplaces | Solo imagen |

### Los 3 Diferenciadores Clave

#### 1. METADATA DINÁMICA EN TIEMPO REAL

Tu NFT no es solo una imagen — es un personaje vivo que evoluciona.

```
Cuando completas una misión:
  ├── Tu XP aumenta
  ├── Tu nivel sube
  ├── Tus logros se actualizan
  ├── Tu rango puede cambiar
  └── TODO esto es visible en OpenSea instantáneamente
```

Cualquiera puede ver el progreso de tu Emissary directamente en los marketplaces. Un Emissary nivel 50 con equipo Legendary vale más que uno nivel 1.

#### 2. CERO GAS EN MISIONES

La blockchain es la fundación, no la fricción.

```
┌─────────────────────────────────────────────────────────────┐
│                         ON-CHAIN                             │
│  • Propiedad de NFTs (indisputable)                         │
│  • Tokens $EMBER y $ASH                                     │
│  • Items y Runas como NFTs                                  │
│  • Reclamación de rewards                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        OFF-CHAIN                             │
│  • Iniciar/completar misiones (SIN GAS)                     │
│  • Progresión (XP, Aura, rankings)                          │
│  • Eventos temporales                                       │
│  • Sistema de energía                                       │
└─────────────────────────────────────────────────────────────┘
```

Puedes jugar horas sin gastar un centavo en gas. Solo pagas cuando reclamas rewards o minteas items.

#### 3. SISTEMA DE PERSISTENCIA ROBUSTO

Tus datos están seguros y son portables:

- **Base de datos PostgreSQL** para progreso en tiempo real
- **Metadata servida via API** para marketplaces
- **Backups redundantes** de toda la información
- **Sin pérdida de datos** si el servidor se reinicia

---

## 5. ARQUITECTURA TÉCNICA

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUARIO                                  │
│                    (Browser + MetaMask)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  HTML/CSS   │  │  Vanilla JS │  │  ethers.js (Web3)       │  │
│  │  Terminal   │  │  Zero deps  │  │  Wallet connection      │  │
│  │  Aesthetic  │  │             │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────┐        ┌──────────────────────────────┐
│      BACKEND         │        │        BLOCKCHAIN            │
│  ┌────────────────┐  │        │  ┌────────────────────────┐  │
│  │  Flask/Python  │  │        │  │     BASE MAINNET       │  │
│  │  REST API      │  │        │  │     (Ethereum L2)      │  │
│  └────────────────┘  │        │  └────────────────────────┘  │
│  ┌────────────────┐  │        │  ┌────────────────────────┐  │
│  │  PostgreSQL    │  │        │  │   5 Smart Contracts    │  │
│  │  Persistencia  │  │        │  │   ERC721 + ERC20       │  │
│  └────────────────┘  │        │  └────────────────────────┘  │
└──────────────────────┘        └──────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          IPFS                                    │
│            Imágenes y metadata descentralizada                   │
└─────────────────────────────────────────────────────────────────┘
```

### Stack Tecnológico

| Capa | Tecnología | Propósito |
|------|------------|-----------|
| Frontend | HTML5 + CSS3 + Vanilla JS | UI Terminal retro |
| Web3 | ethers.js | Conexión a blockchain |
| Backend | Python Flask | API REST |
| Database | PostgreSQL | Persistencia de estado |
| Blockchain | Base Mainnet | L2 de bajo costo |
| Contracts | Solidity 0.8.20 | NFTs y tokens |
| Storage | IPFS | Imágenes descentralizadas |
| Hosting | Render.com | Deploy automático |

### ¿Por Qué Base?

| Razón | Detalle |
|-------|---------|
| **Costos ~100x menores** | Gas de $0.01-0.05 vs $5-50 en Ethereum |
| **Respaldado por Coinbase** | Seguridad y adopción institucional |
| **Compatibilidad EVM** | Mismo código que Ethereum |
| **Ideal para Gaming** | Microtransacciones frecuentes viables |
| **Ecosistema creciente** | Cada vez más proyectos y usuarios |

---

## 6. ECONOMÍA DUAL: $EMBER Y $ASH

### $EMBER — Token de Utilidad

**Supply Total: 100,000,000 EMBER**

#### Formas de Obtener

| Método | Cantidad |
|--------|----------|
| Misiones EASY | 10-25 EMBER |
| Misiones MEDIUM | 30-75 EMBER |
| Misiones HARD | 80-200 EMBER |
| Ember Roll (D20) | -100 a +1,000 EMBER |
| Staking (futuro) | 10-70 EMBER/día |

#### Formas de Gastar

| Uso | Costo |
|-----|-------|
| Recarga de energía | 30-150 EMBER |
| Ember Roll adicional | 75 EMBER |
| Resurrección | 200-10,000 EMBER |
| Conversión a $ASH | 1,000 EMBER = 1 ASH |

#### Distribución

```
┌─────────────────────────────────────────────────────────────┐
│                    DISTRIBUCIÓN $EMBER                       │
├─────────────────────────────────────────────────────────────┤
│  ████████████████████░░░░░░░░░░░░░░░  40% Staking Rewards   │
│  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░  20% Team (2yr vest)   │
│  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  15% Liquidity         │
│  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  10% Marketing         │
│  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  10% Treasury/DAO      │
│  ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   5% Airdrop           │
└─────────────────────────────────────────────────────────────┘
```

### $ASH — Token de Gobernanza

**Obtención**: Quemar 1,000 $EMBER = 1 $ASH

| Utilidad | Descripción |
|----------|-------------|
| Votación DAO | 1 ASH = 1 voto |
| Propuestas | Crear cambios al juego |
| Treasury | Decidir uso de fondos |
| Features Premium | Acceso anticipado (futuro) |

---

## 7. 5 SMART CONTRACTS EN BASE

Emberholm no es un contrato — es un **ecosistema de 5 contratos** interconectados:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMBERHOLM ECOSYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              EMBERHOLM PORTAL (ERC721)                   │   │
│   │              35,000 Emissary NFTs                        │   │
│   │              0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│              ┌───────────────┼───────────────┐                   │
│              ▼               ▼               ▼                   │
│   ┌─────────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│   │  EMBER TOKEN    │ │  ASH TOKEN  │ │                     │   │
│   │  (ERC20)        │ │  (ERC20)    │ │   EQUIPABLES        │   │
│   │  Utility        │ │  Governance │ │                     │   │
│   │  0xbA77...      │ │  0xD4ee...  │ │  ┌───────────────┐  │   │
│   └─────────────────┘ └─────────────┘ │  │ EMBER ITEMS   │  │   │
│                                       │  │ 0xCE71...     │  │   │
│                                       │  └───────────────┘  │   │
│                                       │  ┌───────────────┐  │   │
│                                       │  │ EMBER RUNES   │  │   │
│                                       │  │ 0xDa2D...     │  │   │
│                                       │  └───────────────┘  │   │
│                                       └─────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| Contrato | Tipo | Función |
|----------|------|---------|
| **EmberholmPortal** | ERC721 | 35,000 NFTs de Emissaries |
| **EmberToken** | ERC20 | Token de utilidad $EMBER |
| **AshToken** | ERC20 | Token de gobernanza $ASH |
| **EmberItems** | ERC721 | Armas, armaduras, accesorios |
| **EmberRunes** | ERC721 | Runas mágicas equipables |

---

## 8. ROADMAP

```
════════════════════════════════════════════════════════════════════

  2026 Q1                        ✅ COMPLETADO
  ─────────────────────────────────────────────────────────────────
  ✅ Launch en Base Mainnet
  ✅ Sistema de misiones completo (Solo, Party)
  ✅ 11 rangos de progresión
  ✅ Items y Runas on-chain
  ✅ Economía dual ($EMBER + $ASH)
  ✅ Tutorial interactivo
  ✅ Metadata dinámica

════════════════════════════════════════════════════════════════════

  2026 Q2                        🔲 EN DESARROLLO
  ─────────────────────────────────────────────────────────────────
  🔲 Staking rewards para holders
  🔲 Marketplace de Items P2P
  🔲 Guild Wars (competencia entre facciones)
  🔲 Eventos temporales con rewards exclusivos

════════════════════════════════════════════════════════════════════

  2026 Q3                        📋 PLANIFICADO
  ─────────────────────────────────────────────────────────────────
  📋 Sistema de Lands (territorios conquistables)
  📋 Income pasivo por ownership de lands
  📋 DAO governance activo con $ASH
  📋 Mobile companion app

════════════════════════════════════════════════════════════════════

  2026 Q4                        🔮 VISIÓN
  ─────────────────────────────────────────────────────────────────
  🔮 Expansión de lore y nuevas misiones
  🔮 Cross-chain bridge
  🔮 Partnerships estratégicos
  🔮 Segunda colección de NFTs

════════════════════════════════════════════════════════════════════
```

---

## 9. SOBRE EL DESARROLLO

### Un Proyecto, Un Desarrollador

Emberholm Portal fue diseñado, desarrollado e implementado **100% por una sola persona**.

Esto incluye:

- **Lore y diseño del mundo** — Historia, facciones, personajes
- **Smart contracts** — 5 contratos en Solidity
- **Backend completo** — API en Python/Flask + PostgreSQL
- **Frontend** — UI estilo terminal desde cero
- **Sistema de juego** — Misiones, rangos, items, economía
- **Arte direccional** — Estética visual del proyecto
- **Deployment** — Infraestructura en Base + Render + IPFS

> *"Quise demostrar que una sola persona con visión clara puede crear un ecosistema completo de gaming on-chain."*

---

## 10. PREGUNTAS FRECUENTES

### GENERALES

**P: ¿Qué es Emberholm Portal?**
> Un RPG medieval de fantasía donde 35,000 NFTs únicos (Emissaries) completan misiones, ganan tokens $EMBER, y progresan a través de 11 rangos mientras determinan el destino de un reino moribundo.

**P: ¿Cuánto cuesta empezar a jugar?**
> Mintear un Emissary cuesta 0.0011 ETH (~$2-3 USD) + gas mínimo en Base (~$0.02-0.05). Una vez que tienes tu NFT, las misiones son GRATIS.

**P: ¿Necesito experiencia con crypto/NFTs?**
> Solo necesitas MetaMask y ETH en Base. El juego tiene un tutorial interactivo que te guía paso a paso.

**P: ¿Puedo jugar en móvil?**
> Actualmente es web-only, pero funciona en browsers móviles con MetaMask mobile. Una app nativa está en el roadmap.

---

### GAMEPLAY

**P: ¿Cómo funcionan las misiones?**
> Seleccionas un Emissary, eliges una misión (3h/6h/12h), y esperas. Al completarse, recibes XP, Aura, $EMBER, y posible drop de items.

**P: ¿Qué pasa si mi Emissary muere?**
> Entra en estado FALLEN. Puedes resucitarlo pagando $EMBER (200-10,000 según cantidad de muertes previas). El XP y Aura se reinician.

**P: ¿Puedo perder mi NFT permanentemente?**
> No. El NFT siempre es tuyo. La "muerte" solo afecta el estado del personaje en el juego, no la propiedad del token.

**P: ¿Qué es el Ember Roll?**
> Un sistema de dados D20 donde puedes ganar $EMBER. Primera tirada gratis, luego 75 EMBER cada una. Puedes ganar hasta 1,000 EMBER con un Natural 20.

**P: ¿Cómo maximizo mis ganancias?**
> 1) Alinea guild/clase/raza con la misión (1.5x rewards), 2) Equipa items Legendary (+18% EMBER), 3) Haz Party missions (+20%), 4) Sube de rango (hasta +50% EMBER).

---

### TÉCNICAS

**P: ¿Por qué las misiones no cuestan gas?**
> Las misiones se procesan off-chain en nuestro backend. Solo pagas gas cuando minteas, reclamas items, o transfieres tokens — acciones que realmente requieren blockchain.

**P: ¿Mis datos están seguros?**
> Sí. Tu NFT está en blockchain (imposible de perder). Tu progreso está en PostgreSQL con backups. La metadata se sincroniza constantemente.

**P: ¿Qué pasa si el servidor cae?**
> Tu NFT sigue siendo tuyo en blockchain. Cuando el servidor vuelve, tu progreso se restaura automáticamente desde la base de datos.

**P: ¿Por qué Base y no Ethereum/Solana/Polygon?**
> Base ofrece: 1) Costos ~100x menores que Ethereum, 2) Respaldo de Coinbase, 3) Compatibilidad EVM total, 4) Ecosistema en crecimiento. Ideal para gaming.

**P: ¿Los NFTs son realmente dinámicos?**
> Sí. Cada vez que completas una misión, tu metadata se actualiza. Puedes ver XP, nivel, rango, logros y equipo directamente en OpenSea.

---

### ECONÓMICAS

**P: ¿Cómo gano dinero real?**
> Ganas $EMBER completando misiones. $EMBER es un token ERC20 que puedes tradear. También puedes vender tu NFT — uno con alto nivel/rango vale más.

**P: ¿Hay inflación de tokens?**
> Controlada. Supply fijo de 100M con emisiones decrecientes. Mecanismos de quema en resurrecciones, crafting futuro, y fees de marketplace.

**P: ¿Qué es $ASH?**
> Token de gobernanza obtenido quemando $EMBER (1,000:1). Permite votar en decisiones del proyecto y acceder a features premium futuros.

**P: ¿Puedo vivir de jugar Emberholm?**
> Depende del mercado y tu dedicación. El juego está diseñado para ser sostenible a largo plazo, no un esquema de ganancias rápidas.

---

### ITEMS Y RUNAS

**P: ¿Cómo obtengo items?**
> Drops aleatorios al completar misiones. Mayor dificultad = mayor probabilidad. Party missions tienen el mejor drop rate (25% items, 12% runas).

**P: ¿Qué tan raro es un Legendary?**
> En misiones EASY: 0.05%. En PARTY: 2.5%. Son difíciles de obtener pero dan +18% a todos los stats.

**P: ¿Los items son NFTs?**
> Sí. Contratos separados (EmberItems, EmberRunes). Puedes tradearlos o transferirlos independientemente de tu Emissary.

**P: ¿Puedo equipar múltiples items?**
> Sí. Slots: Weapon, Armor, Helmet, Accessory, Amulet, y 2 Runas. Los bonuses se acumulan.

---

### COMUNIDAD Y FUTURO

**P: ¿Hay Discord/comunidad?**
> El proyecto está en fase de crecimiento. Comunidad se construirá orgánicamente.

**P: ¿Qué viene después?**
> Próximamente: Staking rewards, Guild Wars, Sistema de Lands, y DAO governance. Ver roadmap completo arriba.

**P: ¿Puedo sugerir features?**
> Cuando el DAO esté activo, podrás crear propuestas con $ASH. Por ahora, feedback es bienvenido.

**P: ¿El proyecto seguirá desarrollándose?**
> Sí. El roadmap tiene visión a largo plazo. El desarrollo es continuo.

---

## ENLACES

| Recurso | URL |
|---------|-----|
| **Juego** | [emberholm.com](https://emberholm.com) |
| **Mint** | [emberholm.com/mint](https://emberholm.com/mint) |
| **OpenSea** | [opensea.io/collection/emberholm-portal](https://opensea.io/collection/emberholm-portal) |
| **Contrato NFT** | [basescan.org/address/0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3](https://basescan.org/address/0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3) |

---

<div align="center">

### EL REINO ESTÁ MURIENDO. LOS EMISSARIES SON SU ÚLTIMA ESPERANZA.

**¿Te unirás a la causa?**

*[MINT YOUR EMISSARY]*

</div>

---

*Documento de Presentación — Emberholm Portal*
*Versión 1.0 | Enero 2026*
