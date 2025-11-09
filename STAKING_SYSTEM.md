# 🔒 Sistema de Staking On-Chain - Emberholm Portal

## 📋 Estado Actual

### ✅ **Contrato**: LISTO
El contrato `EmberholmPortal.sol` **YA TIENE** funciones de staking implementadas:

```solidity
// Línea 266-274
function stakeToken(uint256 tokenId) external {
    require(ownerOf(tokenId) == msg.sender, "Not owner");
    require(!stakedTokens[tokenId], "Already staked");
    stakedTokens[tokenId] = true;
    stakeTimestamp[tokenId] = block.timestamp;
    emit TokenStaked(tokenId, msg.sender, block.timestamp);
}

// Línea 279-290
function unstakeToken(uint256 tokenId) external {
    address owner = ownerOf(tokenId);
    require(msg.sender == owner || msg.sender == missionManager, "Not authorized");
    require(stakedTokens[tokenId], "Not staked");
    stakedTokens[tokenId] = false;
    emit TokenUnstaked(tokenId, owner, block.timestamp);
}

// Línea 295-302: CRÍTICO - Previene transferencias de NFTs stakeados
function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
    require(!stakedTokens[tokenId], "Token is staked");
    return super._update(to, tokenId, auth);
}
```

**Beneficio**: Mientras un NFT está en misión (staked), **NO PUEDE SER TRANSFERIDO O VENDIDO**. Esto previene exploits.

### ❌ **Backend**: NO IMPLEMENTADO
El backend (`app.py`) **NO** está llamando estas funciones. Solo actualiza estado en `players.json`.

### ❌ **Frontend**: NO IMPLEMENTADO
El frontend **NO** está llamando `stakeToken()` o `unstakeToken()`.

---

## 🎯 Opciones de Implementación

### **Opción A: Staking desde Frontend (Usuario paga gas)** ⭐ RECOMENDADA

#### Flujo:
1. Usuario presiona **[SEND]** en PROFILE
2. Frontend llama a `contract.stakeToken(tokenId)` - Usuario aprueba en MetaMask
3. Frontend espera confirmación de transacción
4. Frontend llama a `/api/mission/start` (backend verifica que esté staked)
5. Al completar misión:
   - Frontend llama a `/api/mission/complete`
   - Mostrar resultados
   - Frontend llama a `contract.unstakeToken(tokenId)` - Usuario aprueba
6. NFT desbloqueado

#### Ventajas:
- ✅ **Simple**: No requiere private key en backend
- ✅ **Seguro**: No hay fondos en el servidor
- ✅ **Testnet**: Gas es gratis (Base Sepolia)
- ✅ **Transparent**: Usuario ve exactamente qué sucede on-chain

#### Desventajas:
- ⚠️ Usuario debe aprobar 2 transacciones por misión (stake + unstake)
- ⚠️ Si usuario no hace unstake, NFT queda bloqueado (pero puede hacerlo manualmente)

#### Código Estimado:
```javascript
// En startMission()
async function startMissionWithStaking(heroId, missionId, missionName) {
    const tokenId = parseInt(heroId);

    // 1. Stake on-chain
    const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, signer);
    const stakeTx = await contract.stakeToken(tokenId);
    await stakeTx.wait(); // Esperar confirmación

    // 2. Iniciar misión en backend
    await fetch("/api/mission/start", {...});

    // Mostrar modal de éxito
}

// En completeMission()
async function completeMissionWithUnstaking(heroId) {
    // 1. Completar misión en backend
    const result = await fetch("/api/mission/complete", {...});

    // 2. Unstake on-chain
    const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, signer);
    const unstakeTx = await contract.unstakeToken(tokenId);
    await unstakeTx.wait();

    // Mostrar resultados
}
```

---

### **Opción B: Staking desde Backend (Backend paga gas)**

#### Flujo:
1. Usuario presiona **[SEND]**
2. Frontend llama a `/api/mission/start`
3. **Backend** llama a `contract.stakeToken(tokenId)` usando private key del `missionManager`
4. Backend responde con éxito
5. Al completar:
   - Frontend llama a `/api/mission/complete`
   - **Backend** llama a `contract.unstakeToken(tokenId)`
   - Responde con resultados

#### Ventajas:
- ✅ UX perfecta: Usuario solo ve 1 transacción (o ninguna si backend paga todo)
- ✅ Automático: No depende de que usuario haga unstake

#### Desventajas:
- ❌ **Requiere private key en backend** (riesgo de seguridad)
- ❌ **Requiere ETH en wallet backend** para gas
- ❌ Más complejo (Web3.py, manejo de nonces, etc.)
- ❌ Si backend falla, NFTs pueden quedar staked

#### Código Estimado:
```python
# app.py
from web3 import Web3

MISSION_MANAGER_PRIVATE_KEY = os.getenv("MISSION_MANAGER_PRIVATE_KEY")
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(MISSION_MANAGER_PRIVATE_KEY)

@app.route("/api/mission/start", methods=["POST"])
def api_mission_start():
    # ... validaciones ...

    # Stake on-chain
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
    tx = contract.functions.stakeToken(token_id).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 100000,
        'gasPrice': w3.eth.gas_price
    })
    signed_tx = w3.eth.account.sign_transaction(tx, MISSION_MANAGER_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)

    # ... resto de lógica ...
```

---

### **Opción C: Híbrido (Usuario stakea manualmente)**

#### Flujo:
- Usuario puede stakear NFTs manualmente cuando quiera
- Backend solo **verifica** que NFT esté staked antes de permitir misión
- Usuario puede unstakear cuando quiera (si no está en misión)

#### Ventajas:
- ✅ Usuario tiene control total
- ✅ Simple en backend (solo lectura)

#### Desventajas:
- ⚠️ Confuso para usuarios (¿cuándo stakear?)
- ⚠️ Puede olvidar stakear/unstakear

---

## 🚀 Recomendación: Opción A

Para **Base Sepolia (testnet)**, recomiendo **Opción A** porque:

1. ✅ Gas es gratis en testnet
2. ✅ No requiere fondos en backend
3. ✅ No requiere guardar private key
4. ✅ Usuarios pueden probar el flujo completo
5. ✅ Fácil de implementar y mantener

### Para Mainnet (futuro):
- Considerar **Opción B** para mejor UX
- Usar **Gelato Relay** o **Gasless Transactions** para que usuario no pague
- Configurar `missionManager` wallet con fondos limitados

---

## 📝 Implementación Paso a Paso (Opción A)

### 1. Actualizar ABI en `contract-config.js`

Agregar funciones de staking:
```javascript
"function stakeToken(uint256 tokenId) external",
"function unstakeToken(uint256 tokenId) external",
"function stakedTokens(uint256 tokenId) view returns (bool)",
"event TokenStaked(uint256 indexed tokenId, address indexed owner, uint256 timestamp)",
"event TokenUnstaked(uint256 indexed tokenId, address indexed owner, uint256 timestamp)"
```

### 2. Modificar `startMission()` en `index.html`

```javascript
async function startMission(heroId, missionId, missionName) {
    const tokenId = parseInt(heroId);

    try {
        // 1. Llamar stakeToken on-chain
        showInfoModal("STAKING NFT", "Confirma la transacción en MetaMask para bloquear tu NFT durante la misión...");

        const signer = await provider.getSigner();
        const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, signer);

        const stakeTx = await contract.stakeToken(tokenId);
        showInfoModal("TRANSACTION PENDING", "Esperando confirmación de staking...");
        await stakeTx.wait();

        // 2. Iniciar misión en backend
        const res = await fetch("/api/mission/start", {...});
        // ... resto del código ...

    } catch(error) {
        if (error.code === 4001) {
            showInfoModal("CANCELLED", "Transacción cancelada por el usuario.");
        } else {
            showInfoModal("ERROR", "Error al stakear NFT: " + error.message);
        }
    }
}
```

### 3. Modificar `completeMission()` en event listener

```javascript
const result = await res.json();

// Mostrar resultado primero
showInfoModal("MISSION SUCCESS", msg);

// Luego unstake
try {
    const signer = await provider.getSigner();
    const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, signer);
    const unstakeTx = await contract.unstakeToken(tokenId);
    await unstakeTx.wait();
} catch(error) {
    showInfoModal("UNSTAKE FAILED",
        "La misión se completó pero el unstake falló. Puedes desbloquear manualmente tu NFT.");
}
```

### 4. Agregar verificación en Backend (opcional pero recomendado)

```python
@app.route("/api/mission/start", methods=["POST"])
def api_mission_start():
    # ... código existente ...

    # Verificar que el NFT esté staked
    token_id_int = int(hero_id)
    if nft_contract:
        try:
            is_staked = nft_contract.functions.stakedTokens(token_id_int).call()
            if not is_staked:
                abort(400, "NFT must be staked before starting mission. Stake it on-chain first.")
        except Exception as e:
            print(f"⚠️ Could not verify staking status: {e}")

    # ... resto del código ...
```

---

## ⚠️ Notas Importantes

1. **Usuario olvida unstake**: Si el usuario no completa el unstake, puede hacerlo manualmente llamando a `contract.unstakeToken()` desde Etherscan o la UI.

2. **Misión cancelada**: Si usuario quiere cancelar misión, necesitarás agregar endpoint `/api/mission/cancel` que permita unstakear sin completar.

3. **Gas en Mainnet**: En mainnet, cada stake/unstake costará ~$0.10-0.50 USD dependiendo del gas. Considerar:
   - Patrocinar gas con Gelato Relay
   - Batch staking (stakear múltiples NFTs en 1 transacción)
   - Permitir misiones sin staking (menos seguro)

4. **Eventos**: Puedes escuchar eventos `TokenStaked` y `TokenUnstaked` para verificación adicional.

---

## 🔄 Alternativa: Staking Soft (Sin Blockchain)

Si quieres evitar complejidad inicial:

1. Backend guarda `is_locked` en `dynamic_state`
2. Frontend muestra advertencia: "NFT bloqueado durante misión, no transferir"
3. Usuario debe confiar y no transferir
4. **RIESGO**: Usuario puede transferir NFT y perder progreso

**No recomendado para mainnet**, pero aceptable para testnet inicial.

---

## 📊 Comparación Final

| Característica | Opción A (Frontend) | Opción B (Backend) | Sin Staking |
|---------------|---------------------|-------------------|-------------|
| Seguridad | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| UX | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Complejidad | ⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| Costo Gas Usuario | $ (testnet gratis) | - | - |
| Costo Gas Backend | - | $$ | - |
| Previene Exploits | ✅ | ✅ | ❌ |

**Recomendación**: Empezar con **Opción A** en testnet, migrar a **Opción B con Gelato Relay** en mainnet.
