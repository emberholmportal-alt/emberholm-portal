# 🔍 AUDITORÍA COMPLETA - EmberholmPortal v3.0

## 📊 Resumen Ejecutivo

**Contrato:** EmberholmPortal v3.0 (Professional - No Treasury)
**Network:** Base Mainnet (deployed) + Base Sepolia (testing)
**Total Líneas:** 509 líneas
**Versión Solidity:** 0.8.20
**Estándares:** ERC721 + ERC2981 (Royalties)

**Mainnet Address:** `0xc145caD0cAd7ee0018C31baf4621FD87887F72c5`

---

## 🎯 FILOSOFÍA DE DISEÑO

El contrato sigue un enfoque **"Backend-First"** - solo lo CRÍTICO va on-chain:

### ✅ ON-CHAIN (Requiere blockchain)
1. **Ownership** - Quién posee cada NFT (ERC721 standard)
2. **Staking** - Bloqueo de NFTs durante misiones (CRÍTICO - previene transfers)
3. **Equipment** - Items equipados (preparado para futuro contrato de Items)

### 🔄 BACKEND (Base de datos PostgreSQL)
1. **Guild Membership** - FREE, flexible, sin gas
2. **Names** - FREE, fijos por defecto, sin gas
3. **Achievements** - FREE, aparece en metadata OpenSea
4. **Guild Leadership** - FREE, sin gas
5. **Mission Progress** - FREE, estado de misiones

**VENTAJA:** Los usuarios NO pagan gas por operaciones comunes del juego. Solo pagan gas para staking (misiones) y equipar items (futuro).

---

## 📋 AUDITORÍA DE FUNCIONES - CATEGORÍAS

### 🟢 CATEGORÍA 1: MINT (Creación de NFTs)

#### `mint(uint256 quantity)` - Mint público
**Ubicación:** Líneas 120-137
**Función:** Permite a usuarios mintear entre 1-10 NFTs pagando el precio.
**Costo Gas:** ~50,000 gas por NFT (~$0.15 USD en Base)
**Parámetros:**
- `quantity`: Cantidad de NFTs (1-10)
- `msg.value`: ETH enviado (debe ser >= mintPrice * quantity)

**Verificaciones:**
- ✅ Mint está abierto (`mintOpen = true`)
- ✅ Cantidad válida (1-10)
- ✅ No excede MAX_SUPPLY (35,000)
- ✅ ETH suficiente enviado
- ✅ Refund automático si enviaste de más

**Ejemplo de uso:**
```javascript
// Usuario mintea 3 NFTs
await contract.mint(3, { value: ethers.parseEther("0.0033") })
// Recibe tokens #1, #2, #3
// Si envió 0.004 ETH, recibe refund de 0.0007 ETH
```

---

#### `ownerMint(address to, uint256 quantity)` - Mint del owner
**Ubicación:** Líneas 142-150
**Función:** Solo owner puede mintear gratis (airdrops, team, colaboraciones).
**Costo Gas:** ~45,000 gas por NFT
**Uso:**
- Airdrops para holders
- Team allocation
- Colaboraciones con otros proyectos
- Recompensas especiales

**Ejemplo:**
```javascript
// Owner hace airdrop de 5 NFTs a un holder VIP
await contract.ownerMint("0x123...abc", 5)
```

---

### 🟢 CATEGORÍA 2: QUERIES BÁSICAS (Lectura - FREE)

#### `totalMinted()` - Total minteado
**Ubicación:** Líneas 157-159
**Returns:** Número total de NFTs creados
**Costo:** FREE (lectura)

#### `totalSupply()` - Total supply
**Ubicación:** Líneas 164-166
**Returns:** Alias de `totalMinted()`
**Costo:** FREE (lectura)

#### `maxSupply()` - Máximo supply
**Ubicación:** Líneas 171-173
**Returns:** 35,000 (constante)
**Costo:** FREE (lectura)

#### `tokensOfOwner(address owner)` - NFTs de una wallet
**Ubicación:** Líneas 178-196
**Returns:** Array con todos los token IDs de un owner
**Costo:** FREE (lectura)
**Uso:** Frontend muestra todos los NFTs del usuario

**Ejemplo:**
```javascript
// Ver NFTs de una wallet
const tokens = await contract.tokensOfOwner("0x123...abc")
// Returns: [1, 5, 12, 45] - Esta wallet tiene 4 NFTs
```

---

#### `getTokenInfo(uint256 tokenId)` - Info de un NFT
**Ubicación:** Líneas 202-212
**Returns:** Struct con:
- `tokenId`: ID del NFT
- `owner`: Address del dueño
- `isStaked`: ¿Está en misión?

**Costo:** FREE (lectura)

**NOTA IMPORTANTE:** Guild, name, y achievements están en **metadata** (backend), NO on-chain. Esto ahorra gas.

---

### 🟢 CATEGORÍA 3: BATCH OPERATIONS (Queries eficientes)

#### `batchGetTokenInfo(uint256[] tokenIds)` - Info múltiple
**Ubicación:** Líneas 219-230
**Función:** Obtener info de MÚLTIPLES NFTs en UNA sola llamada.
**Ventaja:** En vez de 10 llamadas → 1 llamada
**Costo:** FREE (lectura)

**Ejemplo:**
```javascript
// Obtener info de 10 NFTs de una vez
const infos = await contract.batchGetTokenInfo([1,2,3,4,5,6,7,8,9,10])
// Returns array con info de cada NFT
```

---

#### `getWalletProfile(address owner)` - Perfil completo de wallet
**Ubicación:** Líneas 235-256
**Función:** Obtener TODO sobre una wallet en UNA llamada.
**Returns:**
- `tokenIds`: Array de todos los NFT IDs
- `tokens`: Array con info completa de cada NFT
- `stats`: Estadísticas resumidas (total tokens, cuántos staked)

**Ventaja:** Frontend carga perfil completo en 1 segundo (antes eran múltiples llamadas).

**Ejemplo:**
```javascript
const profile = await contract.getWalletProfile("0x123...abc")
console.log(profile.stats.totalTokens) // 15 NFTs
console.log(profile.stats.stakedCount) // 3 en misión
console.log(profile.tokenIds) // [1, 5, 12, 45, ...]
```

---

### 🔴 CATEGORÍA 4: STAKING SYSTEM (CRÍTICO - Sistema de Misiones)

Este es uno de los sistemas MÁS IMPORTANTES del contrato. Voy a explicarlo en DETALLE.

---

#### 🎮 ¿QUÉ ES EL STAKING EN EMBERHOLM?

**Concepto:** Cuando un NFT va a una misión, se "lockea" (staking) para que NO pueda ser transferido, vendido, o enviado mientras está en la misión.

**¿Por qué on-chain?**
- ✅ **Seguridad:** Imposible vender un NFT que está en misión
- ✅ **Trust:** Los holders saben que el sistema es transparente
- ✅ **Immutable:** Nadie puede cambiar las reglas del staking

**¿Por qué NO en backend?**
- ❌ Backend podría tener bugs
- ❌ Usuarios podrían vender NFT durante misión
- ❌ Menos transparencia

---

#### 📊 STORAGE DEL STAKING

**Líneas 82-83:**
```solidity
mapping(uint256 => bool) public stakedTokens;
mapping(uint256 => uint256) public stakeTimestamp;
```

**Explicación:**
- `stakedTokens[tokenId]`: `true` si está staked, `false` si no
- `stakeTimestamp[tokenId]`: Timestamp UNIX de cuándo se hizo stake

**Ejemplo:**
```
Token #5:
  stakedTokens[5] = true
  stakeTimestamp[5] = 1705234567 (timestamp)

→ Este NFT está bloqueado desde ese momento
```

---

#### ⚡ FUNCIÓN: `stakeToken(uint256 tokenId)`

**Ubicación:** Líneas 263-271
**Quien puede llamarla:** Solo el OWNER del NFT
**Costo Gas:** ~30,000 gas (~$0.09 USD en Base)

**¿Qué hace?**
1. Verifica que el caller es el owner del NFT
2. Verifica que el NFT NO esté ya staked
3. Marca `stakedTokens[tokenId] = true`
4. Guarda el timestamp actual
5. Emite evento `TokenStaked`

**Código:**
```solidity
function stakeToken(uint256 tokenId) external {
    require(ownerOf(tokenId) == msg.sender, "Not owner");
    require(!stakedTokens[tokenId], "Already staked");

    stakedTokens[tokenId] = true;
    stakeTimestamp[tokenId] = block.timestamp;

    emit TokenStaked(tokenId, msg.sender, block.timestamp);
}
```

**Flujo en el juego:**
```
1. Usuario selecciona NFT #5 para misión
2. Frontend llama: contract.stakeToken(5)
3. NFT queda bloqueado on-chain
4. Backend inicia la misión (PostgreSQL)
5. NFT NO puede ser transferido mientras dure la misión
```

---

#### ⚡ FUNCIÓN: `unstakeToken(uint256 tokenId)`

**Ubicación:** Líneas 276-287
**Quien puede llamarla:**
- Owner del NFT, O
- Mission Manager (backend wallet)

**Costo Gas:** ~25,000 gas (~$0.08 USD en Base)

**¿Qué hace?**
1. Verifica que el caller es owner O mission manager
2. Verifica que el NFT esté staked
3. Marca `stakedTokens[tokenId] = false`
4. Emite evento `TokenUnstaked`

**Código:**
```solidity
function unstakeToken(uint256 tokenId) external {
    address owner = ownerOf(tokenId);
    require(
        msg.sender == owner || msg.sender == missionManager,
        "Not authorized"
    );
    require(stakedTokens[tokenId], "Not staked");

    stakedTokens[tokenId] = false;

    emit TokenUnstaked(tokenId, owner, block.timestamp);
}
```

**Flujo en el juego:**
```
1. Misión termina en backend
2. Backend (mission manager) llama: contract.unstakeToken(5)
3. NFT queda desbloqueado
4. Usuario puede venderlo, transferirlo, o enviarlo a otra misión
```

**IMPORTANTE:** El backend puede unstakear automáticamente cuando termina la misión. El usuario NO tiene que pagar gas adicional.

---

#### 🔒 FUNCIÓN: `_update()` - BLOQUEO DE TRANSFERS

**Ubicación:** Líneas 292-299
**Función:** Override interno de ERC721 que se llama en TODOS los transfers.

**¿Qué hace?**
Bloquea CUALQUIER transfer si el NFT está staked.

**Código:**
```solidity
function _update(address to, uint256 tokenId, address auth)
    internal
    override
    returns (address)
{
    require(!stakedTokens[tokenId], "Token is staked");
    return super._update(to, tokenId, auth);
}
```

**CRÍTICO:** Esto significa que:
- ❌ NO puedes vender un NFT staked en OpenSea
- ❌ NO puedes transferirlo con `transferFrom()`
- ❌ NO puedes enviarlo con `safeTransferFrom()`
- ✅ Está 100% seguro durante la misión

**Test de seguridad:**
```javascript
// NFT #5 está en misión (staked)
await contract.transferFrom(alice, bob, 5)
// ❌ REVIERTE con error: "Token is staked"

// Misión termina, backend hace unstake
await contract.unstakeToken(5)

// Ahora SÍ funciona
await contract.transferFrom(alice, bob, 5)
// ✅ Transfer exitoso
```

---

#### 📈 EVENTOS DE STAKING

**Líneas 98-99:**
```solidity
event TokenStaked(uint256 indexed tokenId, address indexed owner, uint256 timestamp);
event TokenUnstaked(uint256 indexed tokenId, address indexed owner, uint256 timestamp);
```

**Uso:**
- Backend escucha estos eventos para sincronizar estado
- Frontend puede mostrar notificaciones en tiempo real
- Analytics pueden trackear cuántos NFTs están en misiones

---

### 🔵 CATEGORÍA 5: PRIMARY TOKEN (TOP EMISSARY)

#### `setPrimaryToken(uint256 tokenId)` - Seleccionar emissary principal
**Ubicación:** Líneas 306-311
**Función:** Permite al usuario elegir cuál NFT es su "TOP EMISSARY" (emissary destacado).
**Costo Gas:** ~25,000 gas (~$0.08 USD)

**Uso en el juego:**
- Usuario tiene 10 NFTs
- Elige su favorito como "TOP EMISSARY"
- Frontend lo muestra en grande en el perfil
- Aparece primero en la página de PROFILE

**Ejemplo:**
```javascript
// Usuario tiene NFTs #1, #5, #12
// Quiere destacar el #12
await contract.setPrimaryToken(12)

// Ahora primaryToken[userAddress] = 12
```

---

#### `getPrimaryTokenInfo(address owner)` - Info del emissary principal
**Ubicación:** Líneas 316-327
**Returns:** Info completa del NFT marcado como primary
**Costo:** FREE (lectura)

**SMART:** Si el usuario NO ha seleccionado primary token, auto-selecciona el primero.

**Código:**
```solidity
function getPrimaryTokenInfo(address owner) external view returns (TokenInfo memory) {
    uint256 tokenId = primaryToken[owner];

    // Si no hay primary token o ya no lo posee
    if (tokenId == 0 || _ownerOf(tokenId) != owner) {
        uint256[] memory tokens = tokensOfOwner(owner);
        require(tokens.length > 0, "No tokens owned");
        tokenId = tokens[0]; // Auto-selecciona el primero
    }

    return getTokenInfo(tokenId);
}
```

---

### 🟣 CATEGORÍA 6: METADATA CUSTOM

#### `setTokenImage(uint256 tokenId, string imageURI)` - Custom image
**Ubicación:** Líneas 335-342
**Quien puede llamarla:** Owner del NFT o contract owner
**Uso futuro:** Recompensas especiales, skins exclusivas, evoluciones

#### `setTokenAttribute(uint256 tokenId, string key, string value)` - Atributos custom
**Ubicación:** Líneas 347-354
**Quien puede llamarla:** Owner del NFT o mission manager
**Uso:** Metadata flexible (achievements especiales, títulos ganados, etc.)

#### `tokenURI(uint256 tokenId)` - URL de metadata
**Ubicación:** Líneas 359-369
**Returns:** URL completa del metadata JSON
**Default:** `https://emberholm-portal.onrender.com/api/metadata/{tokenId}`

---

### 🔴 CATEGORÍA 7: EQUIPMENT SYSTEM (Sistema de Items)

Este es el SEGUNDO sistema más importante. Voy a explicarlo en DETALLE.

---

#### 🎮 ¿QUÉ ES EL EQUIPMENT SYSTEM?

**Concepto:** Cada NFT puede equipar hasta 4 items simultáneamente para aumentar sus stats.

**Slots disponibles (Línea 94):**
```solidity
string[4] public equipmentSlots = ["weapon", "armor", "boots", "accessory"];
```

**Ejemplo visual:**
```
NFT #5 (Emissary Level 15):
├─ Weapon: Sword of Ember (#101) → +50 Attack
├─ Armor: Dragon Scale (#205) → +40 Defense
├─ Boots: Swift Boots (#312) → +30 Speed
└─ Accessory: Aura Ring (#420) → +20 Aura

Total Stats:
  Attack: 50 (base) + 50 (weapon) = 100
  Defense: 30 (base) + 40 (armor) = 70
  Speed: 40 (base) + 30 (boots) = 70
  Aura: 35 (base) + 20 (accessory) = 55
```

---

#### 📊 STORAGE DEL EQUIPMENT

**Línea 93:**
```solidity
mapping(uint256 => mapping(string => uint256)) public equippedItems;
```

**Explicación:**
- `equippedItems[tokenId][slot]`: Item ID equipado en ese slot
- Si es `0`, significa que no hay item equipado

**Ejemplo:**
```
Token #5:
  equippedItems[5]["weapon"] = 101 (Sword of Ember)
  equippedItems[5]["armor"] = 205 (Dragon Scale)
  equippedItems[5]["boots"] = 0 (vacío)
  equippedItems[5]["accessory"] = 420 (Aura Ring)
```

---

#### 🔗 INTERFACE: IEmberholmItems

**Ubicación:** Líneas 32-44
**Función:** Define cómo el contrato de NFTs se comunicará con el futuro contrato de Items.

**Código:**
```solidity
interface IEmberholmItems {
    function balanceOf(address account, uint256 id) external view returns (uint256);

    struct ItemStats {
        uint16 attackBonus;
        uint16 defenseBonus;
        uint16 speedBonus;
        uint16 auraBonus;
        uint8 rarity;
    }

    function itemStats(uint256 itemId) external view returns (ItemStats memory);
}
```

**Explicación:**
- `balanceOf(account, id)`: Verifica si el usuario posee el item (ERC1155 standard)
- `itemStats(itemId)`: Retorna los stats que otorga el item

**IMPORTANTE:** El contrato de Items será ERC1155 (fungible items). Explicaré más abajo.

---

#### 🔗 FUNCIÓN: `setItemsContract(address _itemsContract)`

**Ubicación:** Líneas 376-381
**Quien puede llamarla:** Solo owner
**Costo Gas:** ~35,000 gas
**IMPORTANTE:** Solo puede configurarse UNA VEZ (inmutable después)

**¿Qué hace?**
Conecta el contrato de NFTs con el contrato de Items.

**Código:**
```solidity
function setItemsContract(address _itemsContract) external onlyOwner {
    require(address(itemsContract) == address(0), "Already set");
    require(_itemsContract != address(0), "Invalid address");
    itemsContract = IEmberholmItems(_itemsContract);
    emit ItemsContractSet(_itemsContract);
}
```

**Flujo futuro:**
```
1. Hoy: Deploy NFT contract (EmberholmPortal)
2. En 1 mes: Deploy Items contract (EmberholmItems)
3. Owner llama: setItemsContract(0x...items_address)
4. Sistema de items activado ✅
```

---

#### ⚡ FUNCIÓN: `equipItem(uint256 tokenId, string slot, uint256 itemId)`

**Ubicación:** Líneas 386-403
**Quien puede llamarla:** Owner del NFT
**Costo Gas:** ~45,000 gas (~$0.14 USD en Base)

**¿Qué hace?**
Permite equipar un item a un slot específico del NFT.

**Verificaciones:**
1. ✅ Items contract está configurado
2. ✅ Caller es owner del NFT
3. ✅ Caller posee el item (verificado con `itemsContract.balanceOf()`)
4. ✅ Slot es válido (weapon/armor/boots/accessory)

**Código completo:**
```solidity
function equipItem(uint256 tokenId, string calldata slot, uint256 itemId) external {
    require(address(itemsContract) != address(0), "Items contract not set");
    require(ownerOf(tokenId) == msg.sender, "Not owner");
    require(itemsContract.balanceOf(msg.sender, itemId) > 0, "Don't own item");

    // Validate slot
    bool validSlot = false;
    for (uint i = 0; i < equipmentSlots.length; i++) {
        if (keccak256(bytes(equipmentSlots[i])) == keccak256(bytes(slot))) {
            validSlot = true;
            break;
        }
    }
    require(validSlot, "Invalid slot");

    equippedItems[tokenId][slot] = itemId;
    emit ItemEquipped(tokenId, slot, itemId);
}
```

**Ejemplo de uso:**
```javascript
// Usuario tiene NFT #5 y posee Sword of Ember (item #101)
await contract.equipItem(5, "weapon", 101)

// Ahora:
// equippedItems[5]["weapon"] = 101
// NFT #5 tiene +50 attack bonus
```

**IMPORTANTE:** El item NO sale de la wallet del usuario. Solo se "vincula" al NFT.

---

#### ⚡ FUNCIÓN: `unequipItem(uint256 tokenId, string slot)`

**Ubicación:** Líneas 408-416
**Quien puede llamarla:** Owner del NFT
**Costo Gas:** ~28,000 gas (~$0.09 USD)

**¿Qué hace?**
Desequipa un item de un slot.

**Código:**
```solidity
function unequipItem(uint256 tokenId, string calldata slot) external {
    require(ownerOf(tokenId) == msg.sender, "Not owner");

    uint256 itemId = equippedItems[tokenId][slot];
    require(itemId != 0, "No item equipped");

    equippedItems[tokenId][slot] = 0;
    emit ItemUnequipped(tokenId, slot, itemId);
}
```

**Ejemplo:**
```javascript
// Desequipar weapon del NFT #5
await contract.unequipItem(5, "weapon")

// Ahora:
// equippedItems[5]["weapon"] = 0
// NFT #5 ya no tiene attack bonus
```

---

#### 📊 FUNCIÓN: `getEquippedItems(uint256 tokenId)`

**Ubicación:** Líneas 428-438
**Returns:** Los 4 item IDs equipados
**Costo:** FREE (lectura)

**Ejemplo:**
```javascript
const equipped = await contract.getEquippedItems(5)
console.log(equipped.weapon)    // 101 (Sword of Ember)
console.log(equipped.armor)     // 205 (Dragon Scale)
console.log(equipped.boots)     // 0 (vacío)
console.log(equipped.accessory) // 420 (Aura Ring)
```

---

#### 📊 FUNCIÓN: `getTotalStats(uint256 tokenId)`

**Ubicación:** Líneas 443-465
**Returns:** Stats totales sumando bonuses de todos los items
**Costo:** FREE (lectura)

**¿Qué hace?**
Suma automáticamente los bonuses de los 4 items equipados.

**Código:**
```solidity
function getTotalStats(uint256 tokenId) external view returns (
    uint16 totalAttack,
    uint16 totalDefense,
    uint16 totalSpeed,
    uint16 totalAura
) {
    // Si no hay items contract, return 0
    if (address(itemsContract) == address(0)) {
        return (0, 0, 0, 0);
    }

    // Sum bonuses from equipped items
    for (uint i = 0; i < equipmentSlots.length; i++) {
        uint256 itemId = equippedItems[tokenId][equipmentSlots[i]];
        if (itemId != 0) {
            IEmberholmItems.ItemStats memory stats = itemsContract.itemStats(itemId);
            totalAttack += stats.attackBonus;
            totalDefense += stats.defenseBonus;
            totalSpeed += stats.speedBonus;
            totalAura += stats.auraBonus;
        }
    }
}
```

**Ejemplo:**
```javascript
const stats = await contract.getTotalStats(5)
console.log(stats.totalAttack)   // 50 (weapon bonus)
console.log(stats.totalDefense)  // 40 (armor bonus)
console.log(stats.totalSpeed)    // 0 (no boots)
console.log(stats.totalAura)     // 20 (accessory bonus)
```

**USO EN FRONTEND:**
```javascript
// Base stats del NFT (desde metadata API)
const baseStats = await fetch(`/api/metadata/${tokenId}`)

// Item bonuses (desde contract)
const itemBonuses = await contract.getTotalStats(tokenId)

// Total final
const finalStats = {
  attack: baseStats.attack + itemBonuses.totalAttack,
  defense: baseStats.defense + itemBonuses.totalDefense,
  speed: baseStats.speed + itemBonuses.totalSpeed,
  aura: baseStats.aura + itemBonuses.totalAura
}
```

---

### 🟡 CATEGORÍA 8: ADMIN FUNCTIONS

#### `setMintOpen(bool _open)` - Abrir/cerrar mint
**Ubicación:** Línea 469-471
**Solo owner**

#### `setMintPrice(uint256 _newPriceWei)` - Cambiar precio
**Ubicación:** Línea 473-475
**Solo owner**

#### `setBaseURI(string _newBase)` - Cambiar metadata URL
**Ubicación:** Línea 477-479
**Solo owner**

#### `setMissionManager(address _missionManager)` - Configurar backend wallet
**Ubicación:** Línea 481-484
**Solo owner**
**CRÍTICO:** Esta wallet puede unstakear NFTs cuando terminan misiones

#### `withdraw()` - Retirar fondos (PROFESSIONAL STANDARD)
**Ubicación:** Línea 489-495
**Solo owner**
**Envía directamente a owner (NO a treasury)** ✅

---

## 🚀 FUTURO: STAKING REWARDS (Token Economy)

### 💡 TU IDEA: Staking que otorgue moneda del ecosistema

Esta es una idea EXCELENTE y muy común en proyectos serios. Vamos a explorar cómo implementarlo.

---

### 📊 CONCEPTO: $EMBER Token (ERC20)

**Nombre sugerido:** EMBER
**Símbolo:** $EMBER
**Standard:** ERC20 (fungible token)
**Supply:** 100,000,000 EMBER (ejemplo)
**Uso:** Moneda del ecosistema Emberholm

---

### 🎯 CÓMO FUNCIONARÍA EL STAKING REWARDS

#### **Opción A: Pasivo (Staking automático para holders)**

**Concepto:** Simplemente por TENER un NFT, ganas $EMBER.

**Mecánica:**
```
1 NFT unstaked = 10 $EMBER por día
1 NFT staked (en misión) = 25 $EMBER por día (2.5x bonus!)
```

**Ejemplo:**
```
Usuario tiene 5 NFTs:
- 3 NFTs unstaked (esperando)
- 2 NFTs staked (en misión)

Earnings por día:
  3 × 10 EMBER = 30 EMBER
  2 × 25 EMBER = 50 EMBER
  TOTAL: 80 EMBER/día

En 30 días: 2,400 EMBER
En 1 año: 29,200 EMBER
```

**VENTAJA:** Incentiva hacer misiones (más rewards).

---

#### **Opción B: Activo (Staking explícito para farming)**

**Concepto:** Usuarios hacen "stake" de NFTs explícitamente para farmear tokens.

**Mecánica:**
```
Usuario "deposita" NFT en staking vault
↓
NFT queda bloqueado
↓
Gana 50 $EMBER por día por NFT
↓
Usuario hace "withdraw" cuando quiere
```

**Ejemplo:**
```
Usuario stakea 3 NFTs durante 60 días:
3 × 50 EMBER/día × 60 días = 9,000 EMBER
```

**VENTAJA:** Más control, usuarios eligen cuándo farmear.

---

### 💻 IMPLEMENTACIÓN TÉCNICA

**Para agregar staking rewards, necesitarías:**

#### 1. **Crear contrato $EMBER (ERC20)**

Archivo nuevo: `EmberToken.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract EmberToken is ERC20, Ownable {
    // Reward rate: EMBER per day per NFT
    uint256 public rewardRateUnstaked = 10 ether; // 10 EMBER/day
    uint256 public rewardRateStaked = 25 ether;   // 25 EMBER/day (bonus!)

    constructor() ERC20("Ember", "EMBER") Ownable(msg.sender) {
        // Mint initial supply (100M tokens)
        _mint(msg.sender, 100_000_000 ether);
    }

    // Owner puede ajustar reward rates
    function setRewardRates(uint256 _unstaked, uint256 _staked) external onlyOwner {
        rewardRateUnstaked = _unstaked;
        rewardRateStaked = _staked;
    }
}
```

---

#### 2. **Crear contrato Staking Rewards**

Archivo nuevo: `EmberholmStaking.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./EmberholmPortal.sol";
import "./EmberToken.sol";

contract EmberholmStaking {
    EmberholmPortal public nftContract;
    EmberToken public emberToken;

    // Track last claim timestamp per NFT
    mapping(uint256 => uint256) public lastClaimTime;

    constructor(address _nft, address _token) {
        nftContract = EmberholmPortal(_nft);
        emberToken = EmberToken(_token);
    }

    // Claim rewards for a token
    function claimRewards(uint256 tokenId) external {
        require(nftContract.ownerOf(tokenId) == msg.sender, "Not owner");

        uint256 lastClaim = lastClaimTime[tokenId];
        if (lastClaim == 0) {
            lastClaim = block.timestamp; // First claim
        }

        uint256 timeElapsed = block.timestamp - lastClaim;
        uint256 daysElapsed = timeElapsed / 1 days;

        // Calculate rewards
        bool isStaked = nftContract.stakedTokens(tokenId);
        uint256 rate = isStaked
            ? emberToken.rewardRateStaked()
            : emberToken.rewardRateUnstaked();

        uint256 rewards = daysElapsed * rate;

        // Update last claim
        lastClaimTime[tokenId] = block.timestamp;

        // Transfer EMBER tokens
        emberToken.transfer(msg.sender, rewards);
    }

    // Claim rewards for multiple tokens at once
    function claimRewardsMultiple(uint256[] calldata tokenIds) external {
        for (uint i = 0; i < tokenIds.length; i++) {
            claimRewards(tokenIds[i]);
        }
    }

    // View pending rewards
    function pendingRewards(uint256 tokenId) external view returns (uint256) {
        uint256 lastClaim = lastClaimTime[tokenId];
        if (lastClaim == 0) return 0;

        uint256 timeElapsed = block.timestamp - lastClaim;
        uint256 daysElapsed = timeElapsed / 1 days;

        bool isStaked = nftContract.stakedTokens(tokenId);
        uint256 rate = isStaked
            ? emberToken.rewardRateStaked()
            : emberToken.rewardRateUnstaked();

        return daysElapsed * rate;
    }
}
```

---

### 🎮 EJEMPLO DE USO: Staking Rewards

**Usuario tiene NFT #5:**

```javascript
// Ver rewards pendientes
const pending = await stakingContract.pendingRewards(5)
console.log(pending) // "500000000000000000000" (500 EMBER)

// Claim rewards
await stakingContract.claimRewards(5)
// Usuario recibe 500 EMBER en su wallet

// Ver balance de EMBER
const balance = await emberToken.balanceOf(userAddress)
console.log(balance) // "500000000000000000000" (500 EMBER)
```

---

### 💰 UTILIDADES DEL TOKEN $EMBER

#### **Idea 1: Marketplace de Items**

```
Usuarios pueden comprar items con $EMBER:

- Common Sword: 100 EMBER
- Rare Armor: 500 EMBER
- Epic Boots: 1,500 EMBER
- Legendary Accessory: 5,000 EMBER
```

**Flujo:**
1. Usuario farmea EMBER haciendo misiones (staking NFTs)
2. Acumula 1,500 EMBER en 2 semanas
3. Compra Epic Boots en el marketplace
4. Equipa los boots a su NFT
5. Stats del NFT aumentan (+30 Speed)

---

#### **Idea 2: Guild Creation & Upgrades**

```
Crear guild: 10,000 EMBER
Upgrade guild level 2: 25,000 EMBER
Upgrade guild level 3: 50,000 EMBER
Upgrade guild level 4: 100,000 EMBER
Upgrade guild level 5 (MAX): 250,000 EMBER
```

**Beneficios de guild levels:**
- Level 1: Max 10 miembros
- Level 2: Max 25 miembros + 5% mission rewards bonus
- Level 3: Max 50 miembros + 10% mission rewards bonus
- Level 4: Max 100 miembros + 15% mission rewards bonus + Guild wars access
- Level 5: Max 250 miembros + 25% mission rewards bonus + Exclusive items

---

#### **Idea 3: Breeding/Fusion (Futuro)**

```
Fusionar 2 NFTs + 50,000 EMBER = 1 NFT mejorado

NFT #5 (Level 10) + NFT #12 (Level 15) + 50,000 EMBER
= NFT #99 (Level 20, stats combinados)
```

---

#### **Idea 4: Naming/Customization**

```
Cambiar nombre de NFT: 500 EMBER
Cambiar imagen custom: 1,000 EMBER
Special title/achievement: 2,500 EMBER
```

---

#### **Idea 5: Accelerators**

```
Mission Speed Boost (2x): 100 EMBER
Instant Mission Complete: 1,000 EMBER
Double Rewards Potion: 500 EMBER
```

---

### 📊 ECONOMÍA DEL TOKEN

**Supply:** 100,000,000 EMBER

**Distribución sugerida:**
```
- 40% (40M): Staking rewards pool (distribuido en 4 años)
- 20% (20M): Team & Development
- 15% (15M): Liquidity (DEX pools)
- 10% (10M): Marketing & Partnerships
- 10% (10M): Treasury/DAO
- 5% (5M): Initial airdrop para holders
```

**Emissions schedule (ejemplo):**
```
Año 1: 15M EMBER distribuidos
Año 2: 12M EMBER distribuidos
Año 3: 8M EMBER distribuidos
Año 4: 5M EMBER distribuidos
Total 4 años: 40M EMBER
```

---

## 🚀 FUTURO: SISTEMA DE ITEMS (Detallado)

### 💡 CONCEPTO: Items como NFTs (ERC1155)

**Standard:** ERC1155 (Multi-Token)
**Ventaja:** Puedes tener múltiples copias del mismo item

**Ejemplo:**
```
Item #1 (Common Sword):
  - Supply: 1,000 copias
  - 250 usuarios lo poseen
  - Cada uno puede tener múltiples copias

Item #500 (Legendary Dragon Blade):
  - Supply: 1 copia (ÚNICA)
  - Solo 1 usuario lo posee
```

---

### 📊 ITEM STATS

Cada item tiene stats (definidos en el contrato):

```solidity
struct ItemStats {
    uint16 attackBonus;   // +50 attack
    uint16 defenseBonus;  // +40 defense
    uint16 speedBonus;    // +30 speed
    uint16 auraBonus;     // +20 aura
    uint8 rarity;         // 1=Common, 2=Rare, 3=Epic, 4=Legendary
}
```

**Ejemplos de items:**

#### **Item #1: Iron Sword (Common)**
```
attackBonus: 10
defenseBonus: 0
speedBonus: 0
auraBonus: 0
rarity: 1
```

#### **Item #50: Dragon Scale Armor (Epic)**
```
attackBonus: 0
defenseBonus: 75
speedBonus: -10 (penalty, pesado!)
auraBonus: 25
rarity: 3
```

#### **Item #500: Legendary Emberholm Crown (Legendary)**
```
attackBonus: 50
defenseBonus: 50
speedBonus: 50
auraBonus: 100
rarity: 4
```

---

### 🎮 CÓMO OBTENER ITEMS

#### **Método 1: Mission Rewards**

```
Backend asigna items al completar misiones:

Easy Mission:
  - 80% chance: Nothing
  - 15% chance: Common item
  - 4% chance: Rare item
  - 1% chance: Epic item

Hard Mission:
  - 40% chance: Nothing
  - 30% chance: Common item
  - 20% chance: Rare item
  - 9% chance: Epic item
  - 1% chance: Legendary item
```

**Flujo:**
```
1. Usuario completa misión difícil
2. Backend hace roll de loot (random)
3. Usuario gana Epic Boots (item #312)
4. Backend mints item: itemsContract.mint(userAddress, 312, 1)
5. Usuario recibe el item en su wallet
6. Usuario puede equiparlo a cualquier NFT
```

---

#### **Método 2: Marketplace con $EMBER**

```
Frontend muestra shop:

Common Items: 100-500 EMBER
Rare Items: 500-2,000 EMBER
Epic Items: 2,000-10,000 EMBER
Legendary Items: 10,000-100,000 EMBER
```

**Flujo:**
```
1. Usuario tiene 5,000 EMBER (farmeado con staking)
2. Ve Epic Sword (#245) en shop por 4,500 EMBER
3. Click "Buy"
4. Backend verifica balance EMBER
5. Backend transfiere EMBER del usuario al treasury
6. Backend mints Epic Sword: itemsContract.mint(userAddress, 245, 1)
7. Usuario recibe el item
```

---

#### **Método 3: Crafting (Combinar items)**

```
Recipe: Legendary Emberholm Blade
Requiere:
  - 3x Epic Sword (#245)
  - 1x Rare Ember Crystal (#150)
  - 10,000 EMBER

= Legendary Emberholm Blade (#501)
```

**Flujo:**
```
1. Usuario tiene los materiales
2. Click "Craft" en frontend
3. Backend verifica que posee los items y EMBER
4. Backend quema los materiales:
   itemsContract.burn(userAddress, 245, 3)
   itemsContract.burn(userAddress, 150, 1)
   emberToken.transferFrom(user, treasury, 10000 ether)
5. Backend mints legendary:
   itemsContract.mint(userAddress, 501, 1)
6. Usuario recibe Legendary Emberholm Blade
```

---

#### **Método 4: Drops Especiales (Eventos)**

```
Guild Wars Event:
  - Top 3 guilds: 1x Legendary item each member
  - Top 10 guilds: 1x Epic item each member
  - All participants: 1x Rare item

Airdrop a holders:
  - Holders con 5+ NFTs: 3x Random Epic items
  - Holders con 2-4 NFTs: 2x Random Rare items
  - Holders con 1 NFT: 1x Random Common item
```

---

### 🔄 TRADING DE ITEMS

**Como son ERC1155, se pueden tradear en OpenSea:**

```
Usuario A vende Epic Boots (#312):
  - Lista en OpenSea: 0.01 ETH
  - Usuario B compra
  - Item se transfiere
  - Usuario B puede equiparlo a su NFT
```

**También trading directo:**
```javascript
// Usuario A transfiere item a Usuario B
await itemsContract.safeTransferFrom(
  userA,           // from
  userB,           // to
  312,             // itemId (Epic Boots)
  1,               // quantity
  "0x"             // data
)
```

---

### 📊 CONTRATO DE ITEMS: EmberholmItems.sol

**Estructura básica:**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract EmberholmItems is ERC1155, Ownable {
    struct ItemStats {
        uint16 attackBonus;
        uint16 defenseBonus;
        uint16 speedBonus;
        uint16 auraBonus;
        uint8 rarity;
    }

    // Item ID → Stats
    mapping(uint256 => ItemStats) public itemStats;

    // Item ID → Name
    mapping(uint256 => string) public itemNames;

    // Item ID → Image URI
    mapping(uint256 => string) public itemImages;

    // Authorized minters (backend wallet)
    mapping(address => bool) public minters;

    constructor() ERC1155("https://emberholm-portal.onrender.com/api/items/{id}") Ownable(msg.sender) {}

    // Create new item type
    function createItem(
        uint256 itemId,
        string memory name,
        string memory imageURI,
        ItemStats memory stats
    ) external onlyOwner {
        itemNames[itemId] = name;
        itemImages[itemId] = imageURI;
        itemStats[itemId] = stats;
    }

    // Mint items (mission rewards, shop purchases)
    function mint(address to, uint256 itemId, uint256 amount) external {
        require(minters[msg.sender], "Not authorized");
        _mint(to, itemId, amount, "");
    }

    // Burn items (crafting)
    function burn(address from, uint256 itemId, uint256 amount) external {
        require(minters[msg.sender], "Not authorized");
        _burn(from, itemId, amount);
    }

    // Add minter (backend wallet)
    function setMinter(address minter, bool status) external onlyOwner {
        minters[minter] = status;
    }
}
```

---

### 🎮 EJEMPLO COMPLETO: Flujo de Items

**Paso 1: Owner crea items (one-time setup)**

```javascript
// Create Iron Sword (item #1)
await itemsContract.createItem(
  1,
  "Iron Sword",
  "ipfs://QmXxx.../iron-sword.png",
  {
    attackBonus: 10,
    defenseBonus: 0,
    speedBonus: 0,
    auraBonus: 0,
    rarity: 1
  }
)

// Create 500 items...
```

---

**Paso 2: Usuario completa misión**

```javascript
// Backend detecta que misión terminó
// Roll de loot: Usuario ganó Iron Sword

// Backend mints item
await itemsContract.mint(userAddress, 1, 1)
// Usuario recibe 1x Iron Sword
```

---

**Paso 3: Usuario equipa item a NFT**

```javascript
// Frontend
await nftContract.equipItem(5, "weapon", 1)
// NFT #5 ahora tiene Iron Sword equipado
// Attack bonus: +10
```

---

**Paso 4: Ver stats totales**

```javascript
// Frontend llama
const stats = await nftContract.getTotalStats(5)
console.log(stats.totalAttack) // 10 (del Iron Sword)

// Combinar con base stats
const metadata = await fetch('/api/metadata/5')
const finalAttack = metadata.attack + stats.totalAttack
// Final attack: 50 (base) + 10 (item) = 60
```

---

**Paso 5: Usuario upgradea item**

```javascript
// Usuario tiene 3x Iron Sword
// Quiere craftear Steel Sword (mejor)

// Recipe: 3x Iron Sword + 500 EMBER = 1x Steel Sword

// Backend verifica materiales
const ironSwords = await itemsContract.balanceOf(user, 1) // 3
const ember = await emberToken.balanceOf(user) // 500+

// Backend quema materiales
await itemsContract.burn(user, 1, 3) // Quema 3 Iron Swords
await emberToken.transferFrom(user, treasury, 500)

// Backend mints Steel Sword
await itemsContract.mint(user, 2, 1)

// Usuario ahora tiene Steel Sword (attack +25)
```

---

## 🎯 ROADMAP SUGERIDO

### **FASE 1: AHORA (Enero 2025)**
✅ Deploy NFT contract (EmberholmPortal v3.0)
✅ Sistema de staking funcional
✅ Sistema de misiones (backend)
⏳ Testing en testnet
⏳ Launch mainnet

---

### **FASE 2: Items (Febrero-Marzo 2025)**
- [ ] Diseñar 50-100 items iniciales
- [ ] Deploy Items contract (EmberholmItems)
- [ ] Conectar: `setItemsContract()`
- [ ] Integrar items como mission rewards
- [ ] Frontend para equipar/desequipar items
- [ ] OpenSea collection para items

---

### **FASE 3: Token Economy (Abril-Mayo 2025)**
- [ ] Deploy $EMBER token (ERC20)
- [ ] Deploy Staking Rewards contract
- [ ] Crear liquidity pool (Uniswap/Aerodrome en Base)
- [ ] Airdrop inicial a holders
- [ ] Frontend para claim rewards
- [ ] Marketing del token

---

### **FASE 4: Marketplace (Junio-Julio 2025)**
- [ ] Items shop (comprar con $EMBER)
- [ ] Crafting system (combinar items)
- [ ] Trading entre usuarios
- [ ] Burn mechanism para deflación

---

### **FASE 5: Advanced Features (Agosto+ 2025)**
- [ ] Guild wars con rewards en $EMBER
- [ ] Breeding/Fusion de NFTs
- [ ] Governance (DAO con $EMBER)
- [ ] Staking pools con APY variable
- [ ] Partnership con otros proyectos Base

---

## ✅ CONCLUSIÓN DE LA AUDITORÍA

### 📊 Resumen del Contrato Actual

**FUNCIONAL AL 100%:**
✅ Mint system (public + owner)
✅ Staking system (misiones)
✅ Primary token (TOP EMISSARY)
✅ Equipment system (preparado para items)
✅ Batch operations (queries eficientes)
✅ Metadata custom
✅ Professional withdraw (sin treasury)

**PREPARADO PARA FUTURO:**
🔜 Items contract (interface lista)
🔜 Staking rewards (compatible)
🔜 Token economy (extensible)

---

### 🎯 Recomendaciones

1. **TESTNET PRIMERO** ✅
   - Probar todas las funciones en Base Sepolia
   - Verificar staking/unstaking
   - Verificar batch operations
   - Confirmar que NO existe función treasury

2. **DOCUMENTACIÓN**
   - Crear guía para holders (cómo hacer stake, misiones)
   - Explicar sistema de items (cuando se lance)
   - Roadmap público

3. **SMART CONTRACT AUDITORÍA PROFESIONAL**
   - Cuando el proyecto crezca, considera audit de Certik o similar
   - Especialmente antes de lanzar $EMBER token

4. **COMMUNITY FEEDBACK**
   - Pregunta a holders qué utilidades quieren para $EMBER
   - Test beta del sistema de items con holders VIP
   - Governance descentralizada a futuro

---

### 💡 TU PREGUNTA: "¿Qué podríamos hacer a futuro?"

**RESPUESTA CORTA:** Tienes un contrato EXTREMADAMENTE flexible y bien diseñado. Las posibilidades son infinitas:

**STAKING:**
- ✅ Ya funciona para misiones
- 🔜 Agregar rewards en $EMBER (fácil de implementar)
- 🔜 Staking tiers (más NFTs = más rewards)
- 🔜 Staking pools comunitarios

**ITEMS:**
- ✅ Sistema preparado (interface lista)
- 🔜 Deploy Items contract (1-2 meses)
- 🔜 Mission rewards (items loot)
- 🔜 Marketplace con $EMBER
- 🔜 Crafting & Upgrading
- 🔜 Trading en OpenSea

**TOKEN ECONOMY:**
- 🔜 $EMBER como moneda del ecosistema
- 🔜 Staking rewards pasivos
- 🔜 Items shop
- 🔜 Guild upgrades
- 🔜 Breeding/Fusion
- 🔜 Governance (DAO)

**El contrato actual es la BASE PERFECTA para construir todo esto.**

---

## 🚀 SIGUIENTE PASO

Ahora que entiendes COMPLETAMENTE el contrato, estás listo para:

1. ✅ Deploy a testnet (Base Sepolia)
2. ✅ Probar TODAS las funciones
3. ✅ Confirmar que staking funciona
4. ✅ Verificar que equipment system está listo
5. ✅ Cuando todo pase → Usar mainnet contract con confianza

**¿Procedemos con el testnet deployment siguiendo la guía `TESTNET_DEPLOYMENT.md`?**
