# EMBERHOLM PORTAL - Análisis para Mini App Base/Farcaster

## Resumen Ejecutivo

**Proyecto**: Emberholm Portal - RPG On-Chain
**Blockchain**: Base Mainnet (Chain ID: 8453)
**NFTs**: 35,000 Genesis Emissaries
**Stack**: Flask (Python) + Vanilla JS + PostgreSQL
**Tokens**: $EMBER (ERC20 recompensas) + $ASH (governance)

---

## 1. ENDPOINTS API

### 1.1 Endpoints Públicos (Sin Autenticación)

| Endpoint | Método | Descripción | Rate Limit |
|----------|--------|-------------|------------|
| `/api/stats` | GET | Stats globales del realm (minted, XP total, misiones) | - |
| `/api/guilds` | GET | Rankings de los 6 gremios | - |
| `/api/missions` | GET | Lista de 9 misiones disponibles | - |
| `/api/events` | GET | Eventos activos con multiplicadores de drop | - |
| `/api/realm-feed` | GET | Feed en vivo de actividad del realm | - |
| `/api/events/active` | GET | Evento activo con progreso y premios | 60/min |
| `/api/events/leaderboard` | GET | Top 10 jugadores por XP | 30/min |
| `/api/metadata/<token_id>` | GET | Metadata de un Emissary específico | - |
| `/api/achievements` | GET | Lista de achievements disponibles | - |
| `/api/achievements/<token_id>` | GET | Achievements de un emissary | - |

### 1.2 Endpoints de Jugador (Requieren Wallet)

| Endpoint | Método | Parámetros | Descripción | Rate Limit |
|----------|--------|------------|-------------|------------|
| `/api/player/<wallet>` | GET | wallet | Datos completos del jugador + héroes | 20/min |
| `/api/player/<wallet>` | POST | wallet, token_ids[], total_supply | Sincronizar NFTs del wallet | 20/min |
| `/api/claims/<wallet>` | GET | wallet | Claims pendientes (items/runes) | 10/min |
| `/api/trophies/<wallet>` | GET | wallet | Trofeos del jugador | 30/min |

**Formato de Respuesta `/api/player/<wallet>`**:
```json
{
  "wallet": "0x...",
  "heroes": [
    {
      "token_id": "00001",
      "name": "Emissary #1",
      "guild": "Circle of Mist",
      "race_class": "Human Wizard",
      "image_url": "ipfs://...",
      "dynamic_state": {
        "state": "READY|ON_MISSION|FALLEN",
        "xp_total": 1500,
        "aura_level": 25,
        "energy_current": 80,
        "energy_max": 100,
        "death_count": 0,
        "current_mission_id": null,
        "mission_start_time": null
      },
      "weapon_id": "item-1",
      "armor_id": null,
      "rune_ids": ["rune-3", "rune-5"]
    }
  ]
}
```

### 1.3 Endpoints de Misiones

| Endpoint | Método | Parámetros | Descripción | Rate Limit |
|----------|--------|------------|-------------|------------|
| `/api/mission/start` | POST | wallet, hero_id, mission_id | Iniciar misión (solo) | 10/min |
| `/api/mission/start` | POST | wallet, hero_ids[], mission_id | Iniciar misión (party 5) | 10/min |
| `/api/mission/complete` | POST | wallet, hero_id | Completar misión y recibir rewards | 10/min |
| `/api/mission/preview` | POST | wallet, hero_id, mission_id | Preview con bonuses de equipo | - |
| `/api/mission/push` | POST | wallet, hero_id, cost | Acelerar misión gastando XP | - |

**Request `/api/mission/start`**:
```json
{
  "wallet": "0x...",
  "hero_id": "00001",
  "mission_id": "001"
}
```

**Response `/api/mission/start`**:
```json
{
  "success": true,
  "hero_id": "00001",
  "mission_id": "001",
  "mission_name": "The Lost Forge",
  "difficulty": "EASY",
  "estimated_success_rate": 95.5,
  "completion_time": "2025-01-25T18:00:00Z",
  "duration": {
    "base_hours": 3,
    "actual_hours": 2.7,
    "actual_minutes": 162
  },
  "energy": {
    "base": 10,
    "actual": 8
  },
  "bonuses_applied": {
    "ember": 15,
    "xp": 10,
    "energy": 20,
    "death": 5,
    "speed": 10
  }
}
```

### 1.4 Endpoints de Economía ($EMBER)

| Endpoint | Método | Parámetros | Descripción | Rate Limit |
|----------|--------|------------|-------------|------------|
| `/api/ember/balance/<wallet>` | GET | wallet | Balance pending + on-chain + total claimed | 30/min |
| `/api/ember/claim` | POST | wallet | Claim gasless de $EMBER pendientes | 5/min |
| `/api/ember/rewards-pool` | GET | - | $EMBER restante en rewards pool | 30/min |
| `/api/ember/register-burn` | POST | wallet, amount, tx_hash | Registrar conversión a $ASH | 10/min |

**Response `/api/ember/balance/<wallet>`**:
```json
{
  "pending": 250.5,
  "onchain": 1000.0,
  "total_claimed": 5000.0,
  "total_burned": 500.0,
  "total_earned": 5750.5,
  "last_claim": "2025-01-20T15:30:00Z"
}
```

### 1.5 Endpoints de Equipamiento

| Endpoint | Método | Parámetros | Descripción | Rate Limit |
|----------|--------|------------|-------------|------------|
| `/api/vault` | GET | wallet | Items del vault (deprecated - usa blockchain) | 20/min |
| `/api/equipment/<emissary_id>` | GET | emissary_id | Equipamiento de un emissary | - |
| `/api/equipment/equipped-items` | GET | wallet | Mapa de items equipados | - |
| `/api/equipment/equip` | POST | wallet, emissary_id, item_id, item_type | Equipar item | 20/min |
| `/api/equipment/unequip` | POST | wallet, emissary_id, item_type | Desequipar item | 20/min |
| `/api/equipment/unequip-all` | POST | wallet, emissary_id | Desequipar todo | 10/min |

**Slots de Equipamiento**:
- `weapon` - Arma
- `armor` - Armadura
- `helmet` - Casco
- `accessory` - Accesorio
- `amulet` - Amuleto
- `rune` - Runa (max 2 por emissary)

### 1.6 Endpoints Especiales

| Endpoint | Método | Parámetros | Descripción |
|----------|--------|------------|-------------|
| `/api/revive` | POST | wallet, emissary_id, tx_hash, amount | Revivir emissary caído (requiere tx on-chain) |
| `/api/energy/recover` | POST | emissary_id, amount, wallet | Recuperar energía con $EMBER |
| `/api/ember-roll/status` | GET | wallet | Status de Ember Roll (gambit) |
| `/api/ember-roll/perform` | POST | wallet, emissary_id, cost | Ejecutar Ember Roll |
| `/api/claims/confirm` | POST | claim_id, token_id, tx_hash | Confirmar claim de item/rune |
| `/api/mint/register` | POST | token_id, wallet_address | Registrar nuevo mint |

---

## 2. CONTRATOS INTEGRADOS

### 2.1 Direcciones Base Mainnet

| Contrato | Dirección | Tipo |
|----------|-----------|------|
| **EmberholmPortal** | `0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3` | ERC721 (NFTs) |
| **EmberRunes** | `0xDa2D1085053c3700645a13498293D17c1cc3f595` | ERC721 (Drop NFT) |
| **EmberItems** | `0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA` | ERC721 (Drop NFT) |
| **EmberToken** | `0xbA7723fBfb44C7712C0B78108ad873DcFd5Dd73b` | ERC20 ($EMBER) |
| **AshToken** | `0xD4eef3eadb1Cf1B2905AA4Cd1022b8cCCC739DAb` | ERC20 ($ASH) |
| **EmberTrophies** | `0x99bB074468DF7acED00a7a4960c52c4e22543ab8` | ERC1155 (Trofeos) |

### 2.2 ABIs - EmberholmPortal (NFT Principal)

```javascript
const ABI = [
  // Supply
  "function totalSupply() view returns (uint256)",
  "function maxSupply() pure returns (uint256)",
  "function totalMinted() view returns (uint256)",

  // Queries
  "function tokensOfOwner(address owner) view returns (uint256[])",
  "function tokenURI(uint256 tokenId) view returns (string)",
  "function balanceOf(address owner) view returns (uint256)",
  "function ownerOf(uint256 tokenId) view returns (address)",

  // Mint
  "function mint(uint256 quantity) payable",
  "function mintPrice() view returns (uint256)",
  "function mintOpen() view returns (bool)",
  "function getFreeMints(address wallet) view returns (uint256)",

  // Events
  "event Transfer(address indexed from, address indexed to, uint256 indexed tokenId)"
];
```

### 2.3 ABIs - Tokens y Drops

```javascript
// EmberRunes / EmberItems (Drop NFTs)
const DROP_ABI = [
  "function claimRune(bytes32 claimId, bytes signature) external",  // o claimItem
  "function balanceOf(address owner) view returns (uint256)",
  "function tokensOfOwner(address owner) view returns (uint256[])",
  "function tokenURI(uint256 tokenId) view returns (string)",
  "event RuneClaimed(address indexed player, uint256 indexed tokenId, bytes32 claimId)"
];

// EmberToken (ERC20)
const EMBER_ABI = [
  "function balanceOf(address account) view returns (uint256)",
  "function approve(address spender, uint256 amount) returns (bool)",
  "function transfer(address to, uint256 amount) returns (bool)",
  "function convertToAsh(uint256 emberAmount) external"
];

// AshToken (ERC20)
const ASH_ABI = [
  "function balanceOf(address account) view returns (uint256)"
];
```

### 2.4 Ubicación del ABI

**Archivo**: `/static/contract-config.js`

Contiene `CONTRACT_CONFIG` con:
- Direcciones de todos los contratos
- ABIs en formato human-readable (ethers.js)
- URLs de IPFS para metadata e imágenes
- Probabilidades de drop por dificultad

### 2.5 IPFS CIDs

| Tipo | CID |
|------|-----|
| **NFT Metadata** | `bafybeidd7wtx7izjgsociwe6ynjz6c3xslqmcedr7z4wojcxs4yd5u7pim` |
| **NFT Images** | `bafybeicnvc3zagcncablcovpxgt5mtuotowvuqom6kby754ve2gwbzdvkm` |
| **Items Metadata** | `bafybeibs6mm5rghbpld7twbj35dbpryrfimmqkbnkev6ufs4kpbp343wfm` |
| **Runes Metadata** | `bafybeiajq22kxgm764srr55wsiz4t65so5laxe2nmrryzgailzpmfes3nq` |

---

## 3. FRONTEND - SECCIONES Y PANTALLAS

### 3.1 Estructura de Archivos

| Archivo | Tamaño | Función |
|---------|--------|---------|
| `/static/index.html` | 12,570 líneas | SPA principal (todas las secciones) |
| `/static/js/inventory.js` | 2,851 líneas | Sistema de vault/equipamiento |
| `/static/js/hacknet-ui.js` | ~200 líneas | UI interactions/animaciones |
| `/static/contract-config.js` | 96 líneas | Config contratos + ABIs |
| `/static/css/hacknet-clean.css` | ~3,000 líneas | Estilo terminal retro |

### 3.2 Pantallas Principales

#### HOME (`data-screen="home"`)
- **Archivo**: `index.html` línea 1474-1610
- **Endpoints**: `/api/stats`, `/api/realm-feed`
- **Funcionalidad**:
  - Warning node (alertas del sistema)
  - Realm Map interactivo
  - Core stability indicator
  - Live Feed de actividad

#### GUILDS (`data-screen="guilds"`)
- **Archivo**: `index.html` línea 1613-1644
- **Endpoints**: `/api/guilds`, `/api/events/leaderboard`
- **Funcionalidad**:
  - Rankings de los 6 gremios
  - Leaderboard de jugadores (Top 10 + posición del usuario)
  - Stats por gremio (XP total, miembros, misiones)

#### MISSIONS (`data-screen="missions"`)
- **Archivo**: `index.html` línea 1647-1656
- **Endpoints**: `/api/missions`, `/api/events`
- **Funcionalidad**:
  - Lista de 9 misiones (3 EASY, 3 MEDIUM, 3 HARD)
  - Eventos temporales
  - Party missions (5 héroes)
  - Selector de emissary para misión

#### PROFILE (`data-screen="profile"`)
- **Archivo**: `index.html` línea 1659-1755
- **Endpoints**: `/api/player/<wallet>`, `/api/ember/balance/<wallet>`
- **Contratos**: EmberholmPortal (tokensOfOwner)
- **Funcionalidad**:
  - Lista de emissaries del wallet
  - Estado de cada emissary (READY, ON_MISSION, FALLEN)
  - Botones contextuales (Start Mission, Complete, Revive)
  - Pending claims
  - Balance de $EMBER

#### VAULT (`data-screen="vault"`)
- **Archivo**: `index.html` línea 1758-1882 + `inventory.js`
- **Endpoints**: `/api/vault`, `/api/equipment/*`, `/api/ember/balance/<wallet>`
- **Contratos**: EmberItems, EmberRunes, EmberToken, AshToken
- **Funcionalidad**:
  - Inventario de items y runas (desde blockchain)
  - Sistema de equipamiento
  - Balance $EMBER (pending + on-chain)
  - Claim de $EMBER (gasless)
  - Conversión $EMBER → $ASH
  - Balance $ASH

#### TUTORIAL (`data-screen="tutorial"`)
- **Archivo**: `index.html` línea 1887-2700+
- **Endpoints**: Ninguno
- **Funcionalidad**: Guía completa del juego

### 3.3 Modales Importantes

| Modal | Función | Endpoints |
|-------|---------|-----------|
| **Mission Start** | Confirmar inicio de misión | `/api/mission/start` |
| **Mission Complete** | Mostrar resultados + drops | `/api/mission/complete` |
| **Revive** | Revivir emissary caído | `/api/revive` |
| **Inventory** | Equipar/desequipar items | `/api/equipment/*` |
| **Ember Roll** | Sistema de gambit | `/api/ember-roll/*` |
| **Push** | Acelerar misión | `/api/mission/push` |
| **Recover** | Recuperar energía | `/api/energy/recover` |

---

## 4. FLUJOS CRÍTICOS

### 4.1 Conexión de Wallet

```
1. Usuario hace clic en [CONNECT WALLET]
2. connectWallet() en index.html:5114
3. Verificar window.ethereum existe (MetaMask/Coinbase)
4. Obtener chainId actual
5. Si no es Base (8453):
   - wallet_switchEthereumChain → Base
   - Si falla con 4902: wallet_addEthereumChain
   - Esperar 3s + verificar
6. eth_requestAccounts para obtener address
7. new ethers.providers.Web3Provider(window.ethereum)
8. Llamar contrato.tokensOfOwner(address)
9. Para cada tokenId: fetch IPFS metadata
10. POST /api/player/<wallet> con token_ids[]
11. Renderizar héroes en PROFILE
```

**Código clave** (`index.html:5114-5380`):
```javascript
async function connectWallet() {
  const provider = new ethers.providers.Web3Provider(window.ethereum);
  await provider.send("eth_requestAccounts", []);
  const address = await signer.getAddress();

  const contract = new ethers.Contract(CONTRACT_CONFIG.ADDRESS, CONTRACT_CONFIG.ABI, provider);
  const ownedTokens = await contract.tokensOfOwner(address);

  // Sync to backend
  await fetch(`/api/player/${address}`, {
    method: "POST",
    body: JSON.stringify({ token_ids: tokenIds, total_supply })
  });
}
```

### 4.2 Cargar Emissaries del Usuario

```
1. GET /api/player/<wallet> (backend)
2. Backend: ensure_player(wallet)
3. Backend: Consulta tabla nfts WHERE last_known_owner = wallet
4. Backend: Para cada NFT, obtener dynamic_state (XP, energy, state)
5. Backend: Obtener misiones activas del wallet
6. Backend: Aplicar ganancia pasiva (XP/aura por día)
7. Backend: Retornar lista de heroes con estado completo
8. Frontend: Renderizar cards de emissaries
9. Frontend: Mostrar botones según estado (START/COMPLETE/REVIVE)
```

### 4.3 Iniciar Misión

```
1. Usuario selecciona emissary + misión
2. startMission(heroId, missionId) en index.html:7029
3. Mostrar modal de confirmación
4. POST /api/mission/start:
   - Verificar state != FALLEN && state != ON_MISSION
   - Verificar energy_current >= mission.energy_cost
   - Verificar cooldown (72h por misión)
   - Aplicar bonuses de equipo (energy reduction, speed)
   - Deducir energía
   - Cambiar state a ON_MISSION
   - Guardar en active_missions
   - Guardar en nfts.dynamic_state
5. Respuesta con duration, bonuses aplicados
6. Frontend: Actualizar UI, mostrar timer
```

### 4.4 Completar Misión

```
1. Timer llega a 0 o usuario hace clic en [COMPLETE]
2. POST /api/mission/complete:
   - Verificar misión existe en active_missions
   - Verificar tiempo transcurrido >= duration
   - roll_mission_outcome() → SUCCESS/FAILURE/DEATH
   - Si SUCCESS:
     - Sumar XP + Aura (con bonuses de equipo)
     - calculate_drops() → item/rune drops
     - generate_claim_signature() (firma del backend)
     - Guardar pending_claims
   - Si FAILURE:
     - Restar XP (xp_loss_on_fail)
   - Si DEATH:
     - state = FALLEN
     - Reset XP, Aura, Energy a 0
     - death_count++
   - Eliminar de active_missions
   - Actualizar nfts.dynamic_state
3. Respuesta con outcome, rewards, drops
4. Frontend: Mostrar modal con resultados
5. Si hay drops: Mostrar botón [CLAIM ON-CHAIN]
```

### 4.5 Claim de $EMBER

```
1. Usuario hace clic en [CLAIM EMBER] en Vault
2. claimEmber() en inventory.js:2619
3. POST /api/ember/claim:
   - FOR UPDATE NOWAIT (lock de DB)
   - Obtener pending balance
   - Setear balance a 0 (prevenir doble-claim)
   - Verificar rewards pool tiene suficiente
   - Build transaction: claimTransfer(wallet, amount)
   - Sign con CLAIMER_PRIVATE_KEY (gasless)
   - Send transaction
   - Wait for confirmation
   - Si status == 1: Actualizar total_claimed
   - Si falla: Restaurar balance
4. Respuesta con tx_hash, amount
5. Frontend: Mostrar éxito + link a BaseScan
```

### 4.6 Mint de Nuevo Emissary

```
1. Usuario va a /mint
2. Conectar wallet (mismo flujo)
3. Verificar mintOpen == true
4. Obtener mintPrice (0.0011 ETH)
5. Verificar getFreeMints(wallet) para free mints
6. contract.mint(quantity, { value: mintPrice * quantity })
7. Wait for transaction
8. POST /api/mint/register:
   - Actualizar emissaries_state.minted = true
   - Actualizar wallet_address
   - Incrementar guild member count
9. Redirect a /profile
```

---

## 5. BASE DE DATOS

### 5.1 Tablas Principales

| Tabla | Propósito | Campos Clave |
|-------|-----------|--------------|
| `nfts` | 35,000 emissaries | token_id, name, guild, dynamic_state (JSONB), last_known_owner |
| `active_missions` | Misiones en progreso | mission_key, wallet, hero_id, mission_id, start_time, duration_hours |
| `user_balances` | Balances de $EMBER | wallet, ember_balance, total_claimed, total_burned |
| `items` | Items en vault | id, name, type, rarity, stats (JSONB), owner_wallet |
| `lands` | Sistema de lands | id, name, bound_emissaries[], owner_wallet |
| `players` | Cache de sesión | wallet, player_data (JSONB) |
| `achievements` | Logros por NFT | token_id, achievement_id |
| `pending_claims` | Drops no reclamados | wallet, claim_type, claim_id, signature |
| `revive_log` | Historial de revives | wallet, emissary_id, tx_hash, amount |
| `events` | Eventos del juego | id, name, status, multipliers |
| `event_prizes` | Premios de eventos | event_id, prize_name, winner_wallet |

### 5.2 Dynamic State (JSONB)

```json
{
  "state": "READY",
  "xp_total": 1500,
  "aura_level": 25,
  "energy_current": 80,
  "energy_max": 100,
  "death_count": 0,
  "current_mission_id": null,
  "mission_start_time": null,
  "last_update": "2025-01-25T12:00:00Z",
  "last_energy_refresh": "2025-01-24T00:00:00Z",
  "mission_history": {
    "001": "2025-01-20T15:00:00Z",
    "004": "2025-01-22T10:00:00Z"
  }
}
```

### 5.3 Datos Off-chain vs On-chain

| Dato | Off-chain (PostgreSQL) | On-chain |
|------|------------------------|----------|
| Ownership | `last_known_owner` (cache) | `ownerOf(tokenId)` |
| XP/Aura/Energy | `dynamic_state` | - |
| Estado misión | `active_missions` | - |
| Items/Runas | `items` table | EmberItems/EmberRunes NFTs |
| $EMBER pending | `ember_balance` | - |
| $EMBER claimed | - | `balanceOf(wallet)` |
| Trofeos | `event_prizes` (cache) | EmberTrophies ERC1155 |

### 5.4 Sincronización

1. **POST /api/player/<wallet>**: Frontend envía tokenIds de blockchain → Backend sincroniza owners
2. **Background updater**: Cada 2 min actualiza rewards_remaining de contrato
3. **Claim confirm**: Cuando user claimea item on-chain, confirma en DB
4. **Revive**: Requiere tx_hash válido de transferencia on-chain

---

## 6. SISTEMA DE FIRMAS (Backend Signer)

### 6.1 Drop Claims

El backend genera firmas para claims de items/runes:

```python
# app.py - generate_claim_signature()
def generate_claim_signature(wallet, claim_type, mission_id):
    claim_id = Web3Lib.keccak(text=f"{wallet}_{claim_type}_{mission_id}_{timestamp}")
    message = encode_defunct(claim_id)
    signed = Account.sign_message(message, BACKEND_SIGNER_PRIVATE_KEY)
    return {
        "claim_id": claim_id.hex(),
        "signature": signed.signature.hex()
    }
```

El frontend luego llama al contrato:
```javascript
contract.claimRune(claimId, signature);  // o claimItem
```

### 6.2 Variables de Entorno Requeridas

```bash
BACKEND_SIGNER_PRIVATE_KEY  # Para firmar claims
CLAIMER_PRIVATE_KEY         # Para gasless EMBER claims
CLAIMER_WALLET_ADDRESS      # Wallet que paga gas de claims
DATABASE_URL                # PostgreSQL connection string
```

---

## 7. ASSETS Y CONFIGURACIÓN

### 7.1 Configuración de Misiones (`data/missions_config.json`)

9 misiones con estructura:
```json
{
  "id": "001",
  "name": "The Lost Forge",
  "difficulty": "EASY",
  "duration_hours": 3,
  "energy_cost": 10,
  "reward_xp": 60,
  "reward_aura": 4,
  "success_rate": 92,
  "xp_loss_on_fail": 25,
  "death_chance": 0,
  "favored_guild": "Forge Legion",
  "favored_class": "Warrior",
  "favored_race": "Orc",
  "party_size": null  // 5 para party missions
}
```

### 7.2 Gremios (`data/guilds.json`)

6 gremios:
- Circle of Mist (10,599 miembros)
- Order of Dawn (6,341)
- Shadow Guild (6,234)
- Forge Legion (4,538)
- Void Echoes (4,302)
- Horizon Watch (2,986)

### 7.3 Drop Rates

```javascript
DROP_RATES = {
  EASY:   { item: 5%,  rune: 1% },
  MEDIUM: { item: 10%, rune: 3% },
  HARD:   { item: 20%, rune: 8% },
  PARTY:  { item: 25%, rune: 12% }
}
```

### 7.4 Equipment Bonuses por Rareza

**Items**:
| Rareza | Ember | XP | Energy | Death | Speed |
|--------|-------|----|---------| ------|-------|
| Common | 3% | 2% | 0% | 0% | 0% |
| Uncommon | 5% | 4% | 2% | 0% | 0% |
| Rare | 8% | 6% | 3% | 2% | 0% |
| Epic | 12% | 10% | 5% | 4% | 3% |
| Legendary | 18% | 15% | 8% | 6% | 5% |

**Runes** (todos los stats iguales):
| Rareza | All Bonuses |
|--------|-------------|
| Common | 3% |
| Uncommon | 5% |
| Rare | 8% |
| Epic | 12% |
| Legendary | 18% |

---

## 8. REUTILIZACIÓN PARA MINI APP

### 8.1 Endpoints Reutilizables Directamente

| Endpoint | Uso en Mini App |
|----------|-----------------|
| `/api/stats` | Dashboard principal |
| `/api/guilds` | Leaderboard |
| `/api/missions` | Lista de misiones |
| `/api/player/<wallet>` | Profile del usuario |
| `/api/mission/start` | Iniciar misión |
| `/api/mission/complete` | Completar misión |
| `/api/ember/balance/<wallet>` | Balance de tokens |
| `/api/ember/claim` | Claim gasless |

### 8.2 Consideraciones para Farcaster Frame

1. **Autenticación**: Los endpoints ya aceptan `wallet` como parámetro, compatible con Farcaster verified address
2. **Sin firmas requeridas**: Mission start/complete no requieren firma on-chain
3. **Claim gasless**: `/api/ember/claim` maneja todo server-side
4. **Rate limiting**: Ya implementado por wallet/IP

### 8.3 Funcionalidades Prioritarias para Mini App

1. **Ver mis Emissaries** → `/api/player/<wallet>`
2. **Ver misiones disponibles** → `/api/missions`
3. **Iniciar misión** → `/api/mission/start`
4. **Completar misión** → `/api/mission/complete`
5. **Ver balance $EMBER** → `/api/ember/balance/<wallet>`
6. **Claim $EMBER** → `/api/ember/claim`
7. **Leaderboard** → `/api/events/leaderboard`

### 8.4 Qué NO se puede reutilizar directamente

1. **Equipamiento**: Requiere transacciones on-chain para items NFT
2. **Revive**: Requiere tx on-chain de $EMBER
3. **Mint**: Requiere tx on-chain con payment
4. **Conversión $EMBER→$ASH**: Requiere tx on-chain

---

## 9. ARQUITECTURA RECOMENDADA PARA MINI APP

```
┌─────────────────────────────────────────────────────────────┐
│                    FARCASTER FRAME                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Frame Actions (buttons + state)                      │  │
│  │  • Select Emissary                                    │  │
│  │  • Select Mission                                     │  │
│  │  • Start/Complete                                     │  │
│  │  • View Rewards                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               MINI APP BACKEND (opcional)                    │
│  • Frame state management                                    │
│  • Session caching                                          │
│  • Farcaster Hub integration                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                EMBERHOLM PORTAL API                          │
│  https://www.emberholmportal.xyz/api/*                      │
│  • Player data                                              │
│  • Mission management                                       │
│  • Token economy                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     BASE MAINNET                            │
│  • EmberholmPortal (NFTs)                                   │
│  • EmberToken ($EMBER)                                      │
│  • Items/Runes (opcional)                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. PRÓXIMOS PASOS

1. **Fase 2**: Diseñar estructura de Frames para flujo básico
2. **Fase 3**: Implementar Mini App server con estado
3. **Fase 4**: Integrar con Farcaster Hub para verified addresses
4. **Fase 5**: Testing en testnet/producción
5. **Fase 6**: Launch y monitoreo

---

*Documento generado el 2025-01-25*
*Para uso interno del equipo de desarrollo*
