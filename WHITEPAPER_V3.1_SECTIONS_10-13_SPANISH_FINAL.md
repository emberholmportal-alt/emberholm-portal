# EMBERHOLM PORTAL
## WHITEPAPER OFICIAL - VERSIÓN 3.1

### SECCIONES 10-13: EXPANSIÓN DEL ECOSISTEMA

**Staking • Misiones Avanzadas • Items • Economía de Tokens**

---

**Autor:** Ember Labs
**Fecha:** Enero 2025
**Versión:** 3.1 FINAL
**Red:** Base (Ethereum Layer 2)
**Contrato:** 0xc145caD0cAd7ee0018C31baf4621FD87887F72c5

---

**NOTA IMPORTANTE:** Este documento representa la expansión oficial del Whitepaper Emberholm Portal v1.0. Las secciones aquí descritas detallan la visión a largo plazo del proyecto, incluyendo sistemas actuales y roadmap futuro.

---

## TABLA DE CONTENIDOS

**10. SISTEMA DE STAKING**
- 10.1 Diseño Actual: Bloqueo Virtual
- 10.2 Staking On-Chain: Preparado para el Futuro
- 10.3 Futuro: Staking Rewards con $EMBER
- 10.4 Diferencia: Misiones vs Staking Rewards
- 10.5 Roadmap de Staking

**11. SISTEMA DE MISIONES AVANZADO**
- 11.1 Misiones Estándar
- 11.2 Sistema de Probabilidades
- 11.3 Party System (Misiones de Equipo)
- 11.4 Sistema de Eventos
- 11.5 Cooldown System

**12. SISTEMA DE ITEMS Y EQUIPMENT**
- 12.1 Visión: Items como NFTs
- 12.2 Equipment Slots
- 12.3 Item Stats
- 12.4 Cómo se Obtienen Items
- 12.5 Trading de Items
- 12.6 Impacto en Gameplay
- 12.7 Roadmap de Items

**13. ECONOMÍA DE TOKENS**
- 13.1 Introducción a $EMBER
- 13.2 Distribución Inicial
- 13.3 Staking Rewards Pool
- 13.4 Utilidades de $EMBER
- 13.5 Deflación y Economía Sostenible
- 13.6 Liquidez y Trading
- 13.7 Protecciones Anti-Dump
- 13.8 Roadmap de Economía

**14. CONCLUSIÓN EXPANDIDA**

**APÉNDICES**
- Apéndice A: Glosario Técnico
- Apéndice B: Links y Recursos

---

## 10. Sistema de Staking

### 10.1 Diseño Actual: Bloqueo Virtual

El sistema de misiones de Emberholm utiliza un enfoque **backend-first** que prioriza la experiencia del usuario sobre la rigidez blockchain.

**Funcionamiento:**

Cuando un Emisario acepta una misión, su estado se marca como `ON_MISSION` en la base de datos del sistema. Durante este período:

- El Emisario no puede aceptar otras misiones
- Su energía se consume al inicio
- El tiempo de misión transcurre en el servidor
- Al completar, el Emisario recibe recompensas (XP y Aura)

**Ventajas del sistema actual:**

1. **Cero costos de gas**: Los usuarios no pagan para enviar Emisarios a misiones
2. **Experiencia fluida**: No se requieren aprobaciones de MetaMask constantes
3. **Escalabilidad**: Miles de misiones simultáneas sin saturar la blockchain
4. **Flexibilidad**: Podemos actualizar misiones, eventos y mecánicas sin redesplegar contratos

**Diseño filosofico:**

> "En Emberholm, el juego es la prioridad. La blockchain es la fundación, no la fricción."

Las interacciones frecuentes (misiones diarias, progresión, eventos) ocurren off-chain para garantizar que jugar sea gratuito y accesible. Solo las operaciones críticas (mint, ownership, items futuros) requieren transacciones on-chain.

---

### 10.2 Staking On-Chain: Preparado para el Futuro

Aunque el sistema actual no utiliza staking on-chain para misiones, **el smart contract está preparado** con funciones de staking para usos futuros.

**Funciones disponibles en el contrato:**

```solidity
// Bloquear un NFT on-chain
function stakeToken(uint256 tokenId) external

// Desbloquear un NFT
function unstakeToken(uint256 tokenId) external

// Consultar si un NFT está staked
stakedTokens(uint256 tokenId) public view returns (bool)

// Consultar timestamp de stake
stakeTimestamp(uint256 tokenId) public view returns (uint256)
```

**Protección contra transfers:**

```solidity
// Los NFTs staked NO pueden ser transferidos
function _update(address to, uint256 tokenId, address auth) internal override {
    require(!stakedTokens[tokenId], "Token is staked");
    return super._update(to, tokenId, auth);
}
```

Esto previene que un NFT staked pueda ser vendido en OpenSea o transferido, garantizando seguridad absoluta durante el staking.

---

### 10.3 Futuro: Staking Rewards con $EMBER

En una futura expansión del ecosistema, **el staking on-chain se activará para recompensas pasivas**.

**Concepto: Stake to Earn**

Los holders podrán hacer "stake" explícito de sus Emisarios para generar **$EMBER**, el token de utilidad del ecosistema.

**Mecánica propuesta:**

#### **Opción A: Staking Pasivo**

```
1 NFT unstaked (en wallet) → 10 $EMBER por día
1 NFT staked (bloqueado) → 25 $EMBER por día (2.5x BONUS)
```

**Ejemplo:**

```
Usuario posee 5 NFTs:
- 2 NFTs guardados en wallet: 20 EMBER/día
- 3 NFTs staked para farming: 75 EMBER/día
= Total: 95 EMBER/día

En 30 días: 2,850 EMBER
En 1 año: 34,675 EMBER
```

**Incentivo:** Hacer stake para maximizar ganancias, pero con el costo de bloquear el NFT (no puedes venderlo durante el stake).

---

#### **Opción B: Staking con Lock Periods**

```
Lock 30 días → 20 EMBER/día por NFT
Lock 90 días → 30 EMBER/día por NFT (50% bonus)
Lock 180 días → 45 EMBER/día por NFT (125% bonus)
Lock 365 días → 70 EMBER/día por NFT (250% bonus)
```

**Ejemplo:**

```
Usuario hace stake de 3 NFTs con lock de 365 días:
3 × 70 EMBER/día = 210 EMBER/día

En 365 días: 76,650 EMBER
```

**Incentivo:** Comprometerse a largo plazo para mayores recompensas.

---

### 10.4 Diferencia: Misiones vs Staking Rewards

Es importante entender que el sistema actual de misiones y el futuro staking rewards son **complementarios**, no excluyentes:

| Aspecto | Misiones (Actual) | Staking Rewards (Futuro) |
|---------|------------------|--------------------------|
| **Tipo** | Gameplay activo | Farming pasivo |
| **Bloqueo** | Virtual (backend) | On-chain (smart contract) |
| **Recompensas** | XP y Aura | $EMBER tokens |
| **Gas** | $0 (free) | $0.50-2 USD para stake/unstake |
| **Transferible durante** | Sí* (cancelaría misión) | No (bloqueado on-chain) |
| **Propósito** | Progresión del juego | Economía del ecosistema |

*En el sistema actual, un NFT puede ser transferido técnicamente durante una misión, pero esto cancelaría la misión y se perdería la energía gastada.

---

### 10.5 Roadmap de Staking

**Fase 1 (Actual):** Misiones con bloqueo virtual
- ✅ Funcional y gratuito
- ✅ Usado por todos los jugadores
- ✅ XP y Aura como recompensas

**Fase 2 (Q2 2025):** Deploy de $EMBER token
- 🔜 Token ERC-20 en Base
- 🔜 Supply inicial: 100,000,000 EMBER
- 🔜 Distribución entre holders, liquidez, equipo

**Fase 3 (Q3 2025):** Activación de Staking Rewards
- 🔜 Deploy de contrato EmberholmStaking
- 🔜 Conexión con EmberholmPortal NFT
- 🔜 Usuarios pueden hacer stake on-chain
- 🔜 Generación automática de $EMBER

**Fase 4 (Q4 2025):** Utilidades de $EMBER
- 🔜 Marketplace de items (comprar con EMBER)
- 🔜 Guild upgrades (mejorar guild con EMBER)
- 🔜 Naming/customization (cambiar nombre por EMBER)
- 🔜 Mission accelerators (boosts con EMBER)

---

## 11. Sistema de Misiones Avanzado

### 11.1 Misiones Estándar

Las misiones son el núcleo del gameplay de Emberholm Portal. Cada Emisario puede embarcarse en misiones de diferente dificultad y duración.

**Tipos de Misiones:**

| Dificultad | Duración | Energía | Recompensa XP | Recompensa Aura | Tasa Éxito Base | Riesgo Muerte |
|-----------|----------|---------|---------------|----------------|----------------|---------------|
| **EASY** | 3h | 10 | 60 | 4 | 92% | 0% |
| **MEDIUM** | 6h | 18 | 150 | 10 | 78% | 0.5% |
| **HARD** | 12h | 25 | 350 | 25 | 60% | 2% |

**Mecánica de Resultados:**

Cada misión tiene tres posibles outcomes:

1. **SUCCESS** ✅
   - El Emisario completa la misión exitosamente
   - Recibe XP y Aura completos
   - Stats del gremio aumentan
   - Se otorgan achievements si aplica

2. **FAILURE** ❌
   - La misión falla, pero el Emisario sobrevive
   - Pierde XP (penalización)
   - No recibe recompensas
   - Stats del gremio registran el fallo

3. **DEATH** ☠️
   - El Emisario cae en batalla
   - Entra en estado `FALLEN`
   - Pierde XP significativa
   - Requiere ritual de reinvocación para volver

---

### 11.2 Sistema de Probabilidades

La probabilidad de éxito de una misión NO es fija. Está influenciada por múltiples factores:

**Bonuses de Afinidad:**

- **Guild Match**: +12% si el gremio del Emisario coincide con el favored guild de la misión
- **Class Match**: +8% si la clase coincide
- **Race Match**: +5% si la raza coincide
- **Perfect Alignment**: 1.5x multiplier si guild, class Y race coinciden

**Bonuses de Progresión:**

- **Level Bonus**: +1% por cada 10 niveles del Emisario
- **Aura Bonus**: +1% por cada 100 puntos de Aura

**Ejemplo de Cálculo:**

```
Misión: "Dragon's Crucible" (HARD)
Base Success Rate: 60%
Favored: Forge Legion / Warrior / Orc

Emisario: Thorin Ironheart
- Guild: Forge Legion ✅
- Class: Warrior ✅
- Race: Orc ✅
- Level: 32
- Aura: 450

Cálculo:
60% (base)
+12% (guild match)
+8% (class match)
+5% (race match)
× 1.5 (perfect alignment)
+3% (level 32 = 3 bonuses)
+4% (450 aura = 4 bonuses)
= (60 + 12 + 8 + 5) × 1.5 + 3 + 4
= 85 × 1.5 + 7
= 127.5 + 7
= 134.5% → Capped at 95% (máximo)

Probabilidad final: 95% SUCCESS
```

Este Emisario tiene probabilidad casi garantizada debido a su alineación perfecta con la misión.

---

### 11.3 Party System (Misiones de Equipo)

**Novedad:** Algunas misiones requieren un equipo coordinado de **exactamente 5 Emisarios**.

**Misiones Party:**

- **003 - Dawn Patrol** (EASY, 3h)
- **006 - Veil Breach Containment** (MEDIUM, 6h)
- **009 - Eclipse Ritual** (HARD, 12h)

Estas misiones están marcadas con `[PARTY MISSION - 5 HEROES REQUIRED]` en su descripción.

---

#### **Mecánica del Party System**

**1. Formación del Party:**

El jugador selecciona exactamente 5 de sus Emisarios para formar un party.

**Validaciones:**
- ✅ Todos deben pertenecer a la misma wallet
- ✅ Todos deben estar en estado `READY` (no en misión, no caídos)
- ✅ Todos deben tener energía suficiente
- ✅ Ninguno debe tener cooldown de 72h en esa misión

**2. Inicio del Party:**

- Los 5 Emisarios parten juntos
- Cada uno gasta su propia energía
- Todos quedan marcados como `ON_MISSION`
- Se registra como una sola party mission en el sistema

**3. Durante la Misión:**

- Los 5 Emisarios están bloqueados simultáneamente
- No pueden participar en otras misiones
- El tiempo transcurre igual para todos

**4. Completar Party Mission:**

**CRÍTICO:** Cada Emisario hace su propio roll de probabilidad individual.

```
Party de 5 enviado a "Eclipse Ritual" (HARD):

Hero #1 (Wizard, 85% success) → Roll: SUCCESS ✅
  Recompensa: 350 XP × 1.2 = 420 XP
  Recompensa: 25 Aura × 1.2 = 30 Aura

Hero #2 (Warrior, 70% success) → Roll: SUCCESS ✅
  Recompensa: 420 XP, 30 Aura

Hero #3 (Rogue, 65% success) → Roll: FAILURE ❌
  Recompensa: 0 XP, 0 Aura
  Penalización: -140 XP

Hero #4 (Cleric, 75% success) → Roll: SUCCESS ✅
  Recompensa: 420 XP, 30 Aura

Hero #5 (Ranger, 60% success) → Roll: DEATH ☠️
  Estado: FALLEN
  Penalización: -140 XP
  Requiere ritual de reinvocación

Resultado del Party:
- 3 Éxitos: 1,260 XP, 90 Aura
- 1 Fallo: -140 XP
- 1 Muerte: -140 XP, 1 hero FALLEN
Total: 980 XP, 90 Aura, 1 hero perdido
```

---

#### **Party Bonus: +20% Recompensas**

Los Emisarios que tienen éxito en una party mission reciben un **20% bonus** sobre las recompensas base.

**Comparación:**

```
Misión 007 (HARD, solo):
  SUCCESS → 350 XP, 25 Aura

Misión 009 (HARD, party):
  SUCCESS → 420 XP, 30 Aura (+20% bonus)
```

**¿Vale la pena el party?**

```
5 Emisarios en misiones solo (007, 008 individuales):
  Si todos tienen éxito: 5 × 350 XP = 1,750 XP

5 Emisarios en party mission (009):
  Si todos tienen éxito: 5 × 420 XP = 2,100 XP (+20% total)

Pero el riesgo es el mismo:
  - Probabilidad individual de cada uno
  - Pueden fallar o morir independientemente
```

**Ventaja del party:** Más recompensas SI tienen éxito, pero NO reduce el riesgo.

---

### 11.4 Sistema de Eventos

**Los Eventos** son misiones temporales especiales con recompensas aumentadas.

**Diferencias con misiones normales:**

| Aspecto | Misiones Normales | Eventos |
|---------|------------------|---------|
| **Disponibilidad** | Permanente | Temporal (1-2 semanas) |
| **Dificultad** | EASY/MEDIUM/HARD | Generalmente EASY |
| **Recompensas** | Standard | 2-3x aumentadas |
| **Ubicación** | Sección MISSIONS | Sección EVENTS |
| **Countdown** | No | Sí (tiempo restante visible) |

**Ejemplo de Evento:**

```
🔥 FESTIVAL OF THE ETERNAL FLAME 🔥

Duración: 7 días (20-27 Enero 2025)
Dificultad: EASY
Tiempo: 6 horas
Energía: 15
Recompensas: 150 XP, 15 Aura (2.5x normal!)
Tasa de Éxito: 95%

Descripción:
"La Llama Eterna arde con extraordinaria intensidad durante esta
semana sagrada. Todos los Emisarios son llamados a participar
en el festival y recibir la bendición del fuego."
```

**Características de los Eventos:**

1. **Recompensas Generosas**: 2-3x más XP y Aura que misiones equivalentes
2. **Alta Tasa de Éxito**: Generalmente 90-95% para ser accesibles
3. **Cooldown Igual**: 72h como misiones normales
4. **Narrativa Especial**: Cada evento avanza el lore de Emberholm

**Tipos de Eventos Planeados:**

- **Eventos Estacionales**: Solsticio de Invierno, Equinoccio de Primavera
- **Eventos de Gremio**: Competencias entre gremios con rewards especiales
- **Eventos Narrativos**: Campañas que alteran el lore permanentemente
- **Eventos Comunitarios**: Metas globales (ej: "100,000 misiones completadas = unlock nuevo contenido")

---

### 11.5 Cooldown System

**Regla fundamental:** Cada Emisario puede completar la misma misión una vez cada **72 horas**.

**Propósito:**

1. Prevenir farming excesivo de una sola misión
2. Forzar diversidad en el gameplay
3. Balancear la economía de XP y Aura

**Mensaje mejorado:**

Cuando un Emisario intenta repetir una misión antes de 72h:

```
❌ Este emisario ya completó esta misión.
   Cooldown: 18h 30m restantes.
   Prueba una misión diferente o espera.
```

**Estrategia recomendada:**

```
Con 1 Emisario:
  - Hacer 3 misiones diferentes rotando (001, 002, 003)
  - Cuando 001 sale de cooldown, repetir

Con 5 Emisarios:
  - Enviar todos a misiones simultáneamente
  - Maximizar XP/Aura por ciclo de 72h
  - Usar party missions cuando estén disponibles
```

---

## 12. Sistema de Items y Equipment

### 12.1 Visión: Items como NFTs

En una futura expansión, Emberholm introducirá **Items** como coleccionables NFTs separados (ERC-1155).

**Concepto:**

Los Items son equipment (armas, armaduras, accesorios) que los Emisarios pueden equipar para aumentar sus stats base.

**Standard:** ERC-1155 (Multi-Token)

Esto permite:
- Múltiples copias del mismo item (ej: 1000 Iron Swords)
- Items únicos legendary (ej: 1 Dragon Blade)
- Trading en OpenSea
- Burning para crafting

---

### 12.2 Equipment Slots

Cada Emisario tiene **4 slots de equipment**:

1. 🗡️ **Weapon** (Arma)
2. 🛡️ **Armor** (Armadura)
3. 👢 **Boots** (Botas)
4. 💍 **Accessory** (Accesorio)

**Funcionamiento:**

```solidity
// Equipar item a un slot
function equipItem(uint256 tokenId, string slot, uint256 itemId) external

// Desequipar item
function unequipItem(uint256 tokenId, string slot) external

// Ver todos los items equipados
function getEquippedItems(uint256 tokenId) external view returns (
    uint256 weapon,
    uint256 armor,
    uint256 boots,
    uint256 accessory
)

// Calcular stats totales con bonuses de items
function getTotalStats(uint256 tokenId) external view returns (
    uint16 totalAttack,
    uint16 totalDefense,
    uint16 totalSpeed,
    uint16 totalAura
)
```

---

### 12.3 Item Stats

Cada item otorga bonuses específicos a los stats del Emisario:

```solidity
struct ItemStats {
    uint16 attackBonus;   // Bonus de ataque
    uint16 defenseBonus;  // Bonus de defensa
    uint16 speedBonus;    // Bonus de velocidad
    uint16 auraBonus;     // Bonus de aura espiritual
    uint8 rarity;         // 1=Common, 2=Rare, 3=Epic, 4=Legendary
}
```

**Ejemplos de Items:**

#### **Common: Iron Sword**
```
Attack:  +10
Defense: +0
Speed:   +0
Aura:    +0
Rarity:  Common
```

#### **Rare: Steel Armor**
```
Attack:  +0
Defense: +35
Speed:   -5 (penalty por peso)
Aura:    +10
Rarity:  Rare
```

#### **Epic: Swift Boots**
```
Attack:  +5
Defense: +10
Speed:   +40
Aura:    +15
Rarity:  Epic
```

#### **Legendary: Emberholm Crown**
```
Attack:  +50
Defense: +50
Speed:   +50
Aura:    +100
Rarity:  Legendary
```

---

### 12.4 Cómo se Obtienen Items

**Método 1: Mission Rewards (Loot Drops)**

Al completar misiones, hay probabilidad de recibir items:

```
Easy Mission:
  80% - No item
  15% - Common item
  4%  - Rare item
  1%  - Epic item

Medium Mission:
  60% - No item
  25% - Common item
  12% - Rare item
  3%  - Epic item

Hard Mission:
  40% - No item
  30% - Common item
  20% - Rare item
  9%  - Epic item
  1%  - Legendary item
```

**Método 2: Marketplace con $EMBER**

Los jugadores podrán comprar items directamente con tokens $EMBER:

```
Common Items:    100-500 EMBER
Rare Items:      500-2,000 EMBER
Epic Items:      2,000-10,000 EMBER
Legendary Items: 10,000-100,000 EMBER
```

**Método 3: Crafting (Combinar Items)**

Los jugadores podrán combinar items para crear mejores:

```
Recipe: Steel Sword (Rare)
  3× Iron Sword (Common)
  + 500 EMBER
  = 1× Steel Sword (Rare)

Recipe: Dragon Blade (Legendary)
  3× Epic Sword
  + 1× Dragon Scale (Epic drop)
  + 50,000 EMBER
  = 1× Dragon Blade (Legendary)
```

**Método 4: Eventos Especiales**

```
Guild Wars Event:
  - Top 3 guilds: 1 Legendary item por miembro
  - Top 10 guilds: 1 Epic item por miembro
  - Participantes: 1 Rare item

Anniversary Airdrop:
  - Holders 5+ NFTs: 3 Epic items random
  - Holders 2-4 NFTs: 2 Rare items random
  - Holders 1 NFT: 1 Common item random
```

---

### 12.5 Trading de Items

Como los items serán ERC-1155, son **completamente tradeables**:

**OpenSea:**
- Listar items for sale
- Browse items marketplace
- Buy/sell entre jugadores

**Trading directo:**
```solidity
itemsContract.safeTransferFrom(userA, userB, itemId, quantity, data)
```

**Ventaja del ERC-1155:**

Un jugador puede tener **múltiples copias** del mismo item y vender algunas mientras conserva otras.

```
Usuario tiene:
- 5× Iron Sword (Common)

Vende 3 en OpenSea por 0.001 ETH cada una
Conserva 2 para equipar a sus Emisarios
```

---

### 12.6 Impacto en Gameplay

**Sin Items (Estado Actual):**

```
Emisario Level 20:
  Attack:  50 (base)
  Defense: 40 (base)
  Speed:   45 (base)
  Aura:    120 (acumulada)

Success Rate en Hard Mission: 65%
```

**Con Items Equipados:**

```
Emisario Level 20 + Epic Equipment:
  Attack:  50 + 60 (items) = 110
  Defense: 40 + 55 (items) = 95
  Speed:   45 + 35 (items) = 80
  Aura:    120 + 40 (items) = 160

Success Rate en Hard Mission: 82% (+17%)
```

**Los items NO rompen el balance**, solo otorgan ventaja a jugadores que:
- Completan muchas misiones (drops)
- Invierten en el ecosistema (compran con EMBER)
- Participan en eventos (rewards especiales)

---

### 12.7 Roadmap de Items

**Fase 1 (Q2 2025):** Diseño y Arte
- 🔜 Diseñar 100+ items base
- 🔜 Arte pixel para cada item
- 🔜 Balanceo de stats

**Fase 2 (Q3 2025):** Deploy de Items Contract
- 🔜 Smart contract ERC-1155
- 🔜 Conexión con EmberholmPortal
- 🔜 Testing en testnet

**Fase 3 (Q4 2025):** Launch de Items
- 🔜 Primeros items disponibles via mission drops
- 🔜 Marketplace de items (comprar con EMBER)
- 🔜 Crafting system

**Fase 4 (2026):** Expansión
- 🔜 Items únicos legendary
- 🔜 Sets de items (bonus por equipar set completo)
- 🔜 Items exclusivos de eventos

---

## 13. Economía de Tokens

### 13.1 Introducción a $EMBER

**$EMBER** es el token de utilidad del ecosistema Emberholm Portal.

**Características:**

- **Standard:** ERC-20
- **Network:** Base (L2 de Ethereum)
- **Total Supply:** 100,000,000 EMBER
- **Deflacionario:** Burning mechanism en crafting
- **No value monetario inicial:** El valor lo define el mercado

**Propósito:**

$EMBER NO es un token especulativo. Es una **herramienta de utilidad** diseñada para:

1. Recompensar participación a largo plazo (staking)
2. Facilitar la economía interna (marketplace, crafting)
3. Permitir governance comunitaria (DAO futuro)
4. Incentivar holders activos sobre flippers

---

### 13.2 Distribución Inicial

```
Total Supply: 100,000,000 EMBER

Distribución:
  40% (40M) - Staking Rewards Pool (4 años de distribución)
  20% (20M) - Team & Development (vesting 2 años)
  15% (15M) - Liquidity Pools (Uniswap/Aerodrome en Base)
  10% (10M) - Marketing & Partnerships
  10% (10M) - Treasury/DAO Reserve
  5% (5M)   - Initial Airdrop (holders en momento del launch)
```

**Vesting Schedule:**

```
Team & Development (20M):
  - 0% desbloqueado en TGE
  - 25% desbloqueado a los 6 meses
  - 25% desbloqueado a los 12 meses
  - 25% desbloqueado a los 18 meses
  - 25% desbloqueado a los 24 meses
```

---

### 13.3 Staking Rewards Pool

**40M EMBER** distribuidos en **4 años** a través de staking rewards.

**Emissions Schedule:**

```
Año 1: 15M EMBER (41 ether/día promedio)
Año 2: 12M EMBER (33 ether/día promedio)
Año 3: 8M EMBER  (22 ether/día promedio)
Año 4: 5M EMBER  (14 ether/día promedio)
Total: 40M EMBER
```

**Cálculo de rewards:**

```
Supongamos:
- 10,000 NFTs staked en Año 1
- 15M EMBER para distribuir en Año 1
- 365 días

Rewards por NFT staked:
  15,000,000 EMBER ÷ 10,000 NFTs ÷ 365 días
  = 41 EMBER por NFT por día

Si usuario stakea 5 NFTs durante todo el Año 1:
  5 × 41 EMBER/día × 365 días = 74,825 EMBER
```

**Reducción de emissions:**

A medida que pasan los años, las emissions se reducen, creando escasez y potencialmente aumentando el valor de $EMBER.

---

### 13.4 Utilidades de $EMBER

#### **1. Items Marketplace**

Comprar items con $EMBER:

```
Common Sword:       100 EMBER
Rare Armor:         500 EMBER
Epic Boots:         1,500 EMBER
Legendary Weapon:   10,000 EMBER
Dragon Scale:       50,000 EMBER
```

#### **2. Guild Operations**

```
Crear Guild:              10,000 EMBER
Upgrade Guild Level 2:    25,000 EMBER
Upgrade Guild Level 3:    50,000 EMBER
Upgrade Guild Level 4:    100,000 EMBER
Upgrade Guild Level 5:    250,000 EMBER

Beneficios de Guild Levels:
  Nivel 1: Max 10 miembros
  Nivel 2: Max 25 miembros, +5% mission rewards
  Nivel 3: Max 50 miembros, +10% mission rewards
  Nivel 4: Max 100 miembros, +15% mission rewards, Guild Wars access
  Nivel 5: Max 250 miembros, +25% mission rewards, Exclusive items
```

#### **3. Customization**

```
Cambiar nombre de Emisario:    500 EMBER
Custom image/avatar:          1,000 EMBER
Special title badge:          2,500 EMBER
Background color change:        250 EMBER
```

#### **4. Mission Accelerators**

```
Mission Speed Boost (2x):       100 EMBER (reduce duración 50%)
Instant Mission Complete:     1,000 EMBER (completa inmediatamente)
Double Rewards Potion:          500 EMBER (2x XP y Aura)
Success Rate Boost (+10%):      750 EMBER (aumenta probabilidad)
```

#### **5. Crafting & Burning**

```
Cada vez que se craftea un item, se quema EMBER:

Craft Rare Item:     500 EMBER quemados
Craft Epic Item:   2,000 EMBER quemados
Craft Legendary: 10,000 EMBER quemados

Esto reduce el supply circulante, creando presión deflacionaria.
```

#### **6. Future: Breeding/Fusion**

```
Fusionar 2 NFTs + 50,000 EMBER = 1 NFT mejorado

NFT #5 (Level 20) + NFT #12 (Level 25) + 50,000 EMBER
  = NFT #9999 (Level 30, stats combinados, rarity aumentada)
```

#### **7. Future: DAO Governance**

```
1 EMBER staked = 1 voto

Propuestas:
  - Nuevas misiones
  - Balanceo de rewards
  - Distribución de treasury
  - Colaboraciones con otros proyectos
```

---

### 13.5 Deflación y Economía Sostenible

**Mecanismos Deflacionarios:**

1. **Burning en Crafting**: Cada craft quema EMBER permanentemente
2. **Burning en Upgrades**: Subir de nivel items/guilds quema EMBER
3. **Transaction Fees**: 2% de cada trade en marketplace se quema

**Ejemplo de impacto:**

```
Supply Inicial: 100,000,000 EMBER

Después de 1 año de actividad:
  - 2M EMBER quemados en crafting
  - 1M EMBER quemados en guild upgrades
  - 500K EMBER quemados en fees
  = 3.5M EMBER quemados

Supply Circulante: 96,500,000 EMBER (-3.5%)

Después de 5 años:
  Supply podría reducirse a ~80-85M EMBER
  Creando escasez y potencial apreciación de valor
```

**Balance entre Emissions y Burning:**

```
Año 1:
  Emissions: +15M EMBER (staking rewards)
  Burning:   -3M EMBER (crafting, fees)
  Net:       +12M EMBER circulante

Año 4:
  Emissions: +5M EMBER (menor emisión)
  Burning:   -8M EMBER (más actividad)
  Net:       -3M EMBER circulante (deflación neta)
```

Con el tiempo, el sistema se vuelve deflacionario a medida que las emissions disminuyen y el burning aumenta.

---

### 13.6 Liquidez y Trading

**Launch de Liquidez:**

```
15M EMBER (15% del supply) destinados a liquidity pools

Pool Principal: EMBER/ETH en Uniswap (Base)
  7.5M EMBER + ETH equivalente

Pool Secundario: EMBER/USDC en Aerodrome (Base)
  7.5M EMBER + USDC equivalente
```

**Trading en DEXs:**

Los holders podrán comprar/vender $EMBER en exchanges descentralizados:

- Uniswap (Base)
- Aerodrome (Base)
- Otros DEXs que listen EMBER

**Precio inicial:** Determinado por el mercado basado en liquidez inicial.

---

### 13.7 Protecciones Anti-Dump

**Para prevenir dumps masivos y proteger el ecosistema:**

1. **Team Vesting**: 24 meses de vesting con unlock gradual
2. **Max Transaction Size**: Límite de 100K EMBER por transacción en primeras 2 semanas
3. **Anti-Bot Measures**: Delay entre transactions para prevenir sniping
4. **Holder Incentives**: Bonuses adicionales para holders a largo plazo

**Ejemplo de incentivo a largo plazo:**

```
Holder de 1 año: +10% staking rewards
Holder de 2 años: +25% staking rewards
Holder de 3 años: +50% staking rewards
```

---

### 13.8 Roadmap de Economía

**Q2 2025: Token Launch**
- 🔜 Deploy de $EMBER (ERC-20)
- 🔜 Airdrop a holders existentes
- 🔜 Liquidity pools en Uniswap/Aerodrome
- 🔜 Listado en DexTools, GeckoTerminal

**Q3 2025: Staking Activation**
- 🔜 Deploy de staking contract
- 🔜 Conexión con NFT contract
- 🔜 Inicio de emissions (15M EMBER en Año 1)
- 🔜 Dashboard de staking en website

**Q4 2025: Utilities Launch**
- 🔜 Items marketplace (comprar con EMBER)
- 🔜 Guild creation/upgrades
- 🔜 Crafting system
- 🔜 Customization features

**2026: Advanced Economy**
- 🔜 DAO governance
- 🔜 Breeding/Fusion
- 🔜 Partnership integrations
- 🔜 Cross-chain expansion (Ethereum mainnet?)

---

## 14. Conclusión Expandida

Emberholm Portal no es simplemente una colección de NFTs. Es un **ecosistema vivo** diseñado para crecer y evolucionar con su comunidad.

**Lo que tenemos hoy:**

✅ 35,000 NFTs únicos con atributos dinámicos
✅ Sistema de misiones completo y funcional
✅ Gremios competitivos con rankings globales
✅ Party system para misiones cooperativas
✅ Eventos temporales con recompensas especiales
✅ Smart contract profesional y auditado

**Lo que viene mañana:**

🔜 Token $EMBER con utilidad real
🔜 Staking rewards pasivos
🔜 Sistema de items y equipment
🔜 Marketplace interno
🔜 Crafting y burning deflacionario
🔜 DAO governance comunitaria

**Nuestra promesa:**

> "Mantener viva la llama, misión a misión, token a token, comunidad a comunidad."

Emberholm Portal es un proyecto a largo plazo construido con pasión, dedicación técnica y visión de futuro. No buscamos un lanzamiento rápido y olvido. Buscamos construir un mundo digital donde cada holder sea parte de la historia.

**El fuego apenas comienza.**

---

**Ember Labs**
*Enero 2025*

---

## Apéndice A: Glosario Técnico

- **ERC-721**: Standard de NFTs únicos
- **ERC-1155**: Standard de tokens multi-colección (fungibles y no fungibles)
- **ERC-20**: Standard de tokens fungibles
- **Staking**: Bloqueo de tokens para recibir recompensas
- **Burning**: Destrucción permanente de tokens para reducir supply
- **DAO**: Organización Autónoma Descentralizada
- **Vesting**: Liberación gradual de tokens en el tiempo
- **Emissions**: Generación programada de nuevos tokens
- **DEX**: Exchange Descentralizado
- **Liquidity Pool**: Reserva de tokens para facilitar trading
- **Base**: Layer 2 de Ethereum (Coinbase)

---

## Apéndice B: Links y Recursos

**Contrato Principal (Base Mainnet):**
- Address: `0xc145caD0cAd7ee0018C31baf4621FD87887F72c5`
- Basescan: https://basescan.org/address/0xc145caD0cAd7ee0018C31baf4621FD87887F72c5

**Website:**
- Portal: https://emberholm-portal.onrender.com

**Documentación Técnica:**
- Contract Audit: `/CONTRACT_AUDIT_AND_FUTURE.md`
- Party System Implementation: `/PARTY_SYSTEM_AND_EVENTS_IMPLEMENTATION.md`

**Social Media:**
- Twitter: [Pendiente]
- Discord: [Pendiente]
- GitHub: [Pendiente]

---

*Este documento es una extensión del Whitepaper Oficial de Emberholm Portal v1.0. Las secciones aquí descritas representan la visión a largo plazo del proyecto y están sujetas a cambios basados en feedback de la comunidad y condiciones del mercado.*

*Las fechas del roadmap son estimaciones y pueden ajustarse según el desarrollo técnico y las necesidades del ecosistema.*

*$EMBER es un token de utilidad sin garantía de valor monetario. Su valor es determinado por el mercado y su utilidad dentro del ecosistema Emberholm.*
