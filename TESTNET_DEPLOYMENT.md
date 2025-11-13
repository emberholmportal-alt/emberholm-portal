# 🧪 TESTNET DEPLOYMENT - Base Sepolia Testing Guide

## Purpose
Test the EmberholmPortal v3.0 (Professional - No Treasury) on Base Sepolia testnet to verify ALL functions work correctly before using the mainnet deployment.

**Mainnet Contract (Production):** `0xc145caD0cAd7ee0018C31baf4621FD87887F72c5`
**Testnet Contract (Testing):** Will be deployed in this guide

---

## ✅ Pre-requisitos

- [x] MetaMask instalado
- [ ] Base Sepolia testnet ETH (FREE - get from faucet)
- [x] Contract code ready: `/home/user/emberholm-portal/contracts/EmberholmPortal.sol`
- [x] Basescan API Key: `3T4CC9ASSG1FYDF9UK5MIRDAC45AIXYB78`

---

## 📋 PASO 1: Configurar Base Sepolia en MetaMask

### 1.1 Agregar red Base Sepolia

1. Abre MetaMask
2. Click en el selector de redes (arriba)
3. Click "Add Network" → "Add a network manually"
4. Ingresa estos datos:

```
Network Name: Base Sepolia
RPC URL: https://sepolia.base.org
Chain ID: 84532
Currency Symbol: ETH
Block Explorer URL: https://sepolia.basescan.org
```

5. Click "Save"
6. **Cambia a la red Base Sepolia**

---

## 📋 PASO 2: Obtener ETH de Testnet (GRATIS)

### 2.1 Método 1: Base Sepolia Faucet

1. Ve a: https://www.alchemy.com/faucets/base-sepolia
2. Ingresa tu wallet address
3. Click "Send Me ETH"
4. Espera 1-2 minutos
5. Verifica en MetaMask que recibiste ~0.05 ETH

### 2.2 Método 2: Sepolia Bridge (si tienes Sepolia ETH)

1. Ve a: https://bridge.base.org/
2. Conecta wallet
3. Selecciona: Sepolia → Base Sepolia
4. Bridge 0.01 ETH
5. Espera 5-10 minutos

### 2.3 Verificar balance

- Abre MetaMask
- Verifica: Base Sepolia network
- Balance: ~0.05 ETH (suficiente para todas las pruebas)

---

## 📋 PASO 3: Deploy Contrato en Base Sepolia

### 3.1 Abrir Remix

1. Ve a: **https://remix.ethereum.org**
2. Espera a que cargue completamente

### 3.2 Crear archivo del contrato

1. Click en "📁 File Explorer"
2. Click "📄 Create new file"
3. Nombre: `EmberholmPortal.sol`
4. Copia **TODO** el código desde: `/home/user/emberholm-portal/contracts/EmberholmPortal.sol`
5. Pega en Remix
6. Guarda (Ctrl/Cmd + S)

### 3.3 Compilar

1. Click en "🔨 Solidity Compiler"
2. Compiler: **0.8.20+commit.a1b79de6**
3. Click "Advanced Configurations"
4. Enable optimization: **Yes**
5. Optimization Runs: **200**
6. Click "Compile EmberholmPortal.sol"
7. Verifica ✅ verde (sin errores)

### 3.4 Deploy a Base Sepolia

1. Click en "🚀 Deploy & Run Transactions"
2. ENVIRONMENT: **Injected Provider - MetaMask**
3. Conecta MetaMask cuando aparezca popup
4. **VERIFICA que estés en Base Sepolia** (Chain ID: 84532)
5. CONTRACT: **EmberholmPortal - contracts/EmberholmPortal.sol**
6. **NO ingreses parámetros** (constructor vacío - no tiene treasury!)
7. Click botón naranja "transact"
8. MetaMask popup → Click "Confirm"
9. Espera 10-30 segundos

### 3.5 Guardar Contract Address

1. En "Deployed Contracts", verás: `EMBERHOLMPORTAL AT 0x...`
2. **COPIA ESTA DIRECCIÓN**
3. Guárdala aquí:

```
Testnet Contract Address: 0x___________________________________________
```

---

## 📋 PASO 4: Verificar Contrato en Basescan Sepolia

### 4.1 Método: Standard JSON Input

1. Ve a: https://sepolia.basescan.org/verifyContract
2. O busca tu contract address y click "Verify and Publish"

### 4.2 Datos necesarios

```
Contract Address: [TU_TESTNET_CONTRACT_ADDRESS]
Compiler Type: Solidity (Single file)
Compiler Version: v0.8.20+commit.a1b79de6
Open Source License Type: MIT License
```

### 4.3 Optimization

```
Optimization: Yes
Runs: 200
```

### 4.4 Pegar código

1. En "Enter the Solidity Contract Code"
2. Pega **TODO** el código del contrato (509 líneas)
3. Incluye imports de OpenZeppelin

### 4.5 Constructor Arguments

**IMPORTANTE:** El nuevo contrato NO tiene constructor arguments!

```
Constructor Arguments ABI-encoded: [DEJAR VACÍO]
```

### 4.6 Submit

1. Completa captcha
2. Click "Verify and Publish"
3. Espera 10-20 segundos
4. Verifica ✅ "Contract Source Code Verified!"

---

## 📋 PASO 5: TEST COMPLETO - Checklist de Funciones

### 5.1 Verificar Estado Inicial

En Basescan Sepolia → "Read Contract":

```
✓ maxSupply() = 35000
✓ mintPrice() = 1100000000000000 (0.0011 ETH)
✓ totalMinted() = 0
✓ mintOpen() = true
✓ treasury() = [NO DEBE EXISTIR ESTA FUNCIÓN!] ✅
```

**CRÍTICO:** Confirma que NO existe función `treasury()` - esto confirma la modificación.

---

### 5.2 TEST 1: Mint Function

**Objetivo:** Verificar que el mint funciona y los fondos quedan en el contrato.

1. Ve a "Write Contract"
2. Click "Connect to Web3" (conecta MetaMask)
3. Busca función `mint`
4. Ingresa:
   - `quantity`: `2`
   - `payableAmount`: `0.0022` (Ether, no Wei)
5. Click "Write"
6. Confirma en MetaMask
7. Espera confirmación

**Verificar:**
```
✓ Recibiste 2 NFTs (token IDs 1 y 2)
✓ totalMinted() = 2
✓ tokensOfOwner(tu_address) = [1, 2]
✓ ownerOf(1) = tu_address
✓ Contract balance = 0.0022 ETH (usa Basescan → balance)
```

---

### 5.3 TEST 2: Withdraw Function (Professional Standard)

**Objetivo:** Verificar que withdraw envía fondos al owner (NO a treasury).

1. Anota balance actual de tu wallet (en Basescan)
2. En "Write Contract", busca `withdraw()`
3. Click "Write"
4. Confirma en MetaMask
5. Espera confirmación

**Verificar:**
```
✓ Tu wallet recibió 0.0022 ETH (menos gas)
✓ Contract balance = 0 ETH
✓ NO hubo función treasury() llamada ✅
```

**CRÍTICO:** Esto confirma que el withdraw profesional funciona correctamente.

---

### 5.4 TEST 3: Staking System (Misiones)

**Objetivo:** Verificar que el sistema de staking funciona para misiones.

**3.1 Stake Token**
1. En "Write Contract", busca `stakeToken`
2. Ingresa `tokenId`: `1`
3. Click "Write" → Confirma

**Verificar:**
```
✓ stakedTokens(1) = true
✓ stakeTimestamp(1) = [timestamp actual]
```

**3.2 Intentar Transfer Staked Token (DEBE FALLAR)**
1. Intenta hacer `transferFrom` del token 1
2. **Debe revertir con "Token is staked"** ✅

**3.3 Unstake Token**
1. Busca `unstakeToken`
2. Ingresa `tokenId`: `1`
3. Click "Write" → Confirma

**Verificar:**
```
✓ stakedTokens(1) = false
✓ Ahora SÍ puedes transferir el token
```

---

### 5.5 TEST 4: Primary Token (TOP EMISSARY)

**Objetivo:** Verificar selección de emissary principal.

1. En "Write Contract", busca `setPrimaryToken`
2. Ingresa `tokenId`: `2`
3. Click "Write" → Confirma

**Verificar:**
```
✓ primaryToken(tu_address) = 2
✓ getPrimaryTokenInfo(tu_address) retorna info del token 2
```

---

### 5.6 TEST 5: Batch Operations

**Objetivo:** Verificar queries eficientes.

En "Read Contract":

**5.1 Get Wallet Profile**
```
✓ getWalletProfile(tu_address)
  → tokenIds: [1, 2]
  → tokens: [info token 1, info token 2]
  → stats: {totalTokens: 2, stakedCount: 0}
```

**5.2 Batch Get Token Info**
```
✓ batchGetTokenInfo([1, 2])
  → Array con info de ambos tokens
```

---

### 5.7 TEST 6: Metadata System

**Objetivo:** Verificar custom metadata.

**6.1 Set Token Attribute**
1. "Write Contract" → `setTokenAttribute`
2. Ingresa:
   - `tokenId`: `1`
   - `key`: `"test_attribute"`
   - `value`: `"test_value"`
3. Click "Write" → Confirma

**Verificar:**
```
✓ tokenAttributes(1, "test_attribute") = "test_value"
```

**6.2 Token URI**
```
✓ tokenURI(1) = "https://emberholm-portal.onrender.com/api/metadata/1"
```

---

### 5.8 TEST 7: Admin Functions

**Objetivo:** Verificar control del owner.

**7.1 Set Mission Manager**
1. "Write Contract" → `setMissionManager`
2. Ingresa tu address (para testing)
3. Click "Write" → Confirma

**Verificar:**
```
✓ missionManager() = tu_address
```

**7.2 Set Mint Price**
1. "Write Contract" → `setMintPrice`
2. Ingresa `2000000000000000` (0.002 ETH en Wei)
3. Click "Write" → Confirma

**Verificar:**
```
✓ mintPrice() = 2000000000000000
```

**7.3 Set Mint Open**
1. "Write Contract" → `setMintOpen`
2. Ingresa `false`
3. Click "Write" → Confirma

**Verificar:**
```
✓ mintOpen() = false
✓ Intentar mint ahora DEBE FALLAR con "Mint is closed" ✅
```

---

## 📋 PASO 6: Resultados del Testing

### ✅ Checklist Final

Marca cada función que probaste:

```
[✓] Mint function works
[✓] Contract receives ETH
[✓] Withdraw sends to owner (NOT treasury) - PROFESSIONAL ✅
[✓] Staking works (locks NFT)
[✓] Unstaking works
[✓] Transfer blocked when staked
[✓] Primary token selection works
[✓] Batch queries work (getWalletProfile)
[✓] Token attributes work
[✓] Token URI works
[✓] Mission manager can be set
[✓] Admin functions work (setMintPrice, setMintOpen)
[✓] NO treasury function exists ✅
```

---

## 📋 PASO 7: Conclusión y Siguiente Paso

### Si TODOS los tests pasaron ✅

**CONCLUSIÓN:** El contrato modificado funciona perfectamente. Los únicos cambios fueron:
1. ❌ Eliminada función `treasury` (no profesional)
2. ✅ Implementado `withdraw()` profesional (envía a owner)
3. ✅ TODAS las demás funciones intactas (missions, stats, staking, metadata, equipment)

**SIGUIENTE PASO:** Usa el contrato de mainnet con confianza.

```
🚀 PRODUCTION CONTRACT (Base Mainnet):
Address: 0xc145caD0cAd7ee0018C31baf4621FD87887F72c5
Network: Base Mainnet (Chain ID: 8453)
Basescan: https://basescan.org/address/0xc145caD0cAd7ee0018C31baf4621FD87887F72c5
```

### Próximos pasos para producción:

1. **Actualizar Frontend:**
   - Contract address → `0xc145caD0cAd7ee0018C31baf4621FD87887F72c5`
   - Chain ID → `8453` (Base Mainnet)

2. **Actualizar Backend:**
   - Contract address → `0xc145caD0cAd7ee0018C31baf4621FD87887F72c5`
   - Network → `base-mainnet`

3. **Configurar Mission Manager:**
   - Crear wallet para backend
   - Llamar `setMissionManager(backend_address)`
   - Fondear wallet con 0.01 ETH

4. **Test final en mainnet:**
   - Owner mint 1 NFT
   - Verificar aparece en frontend
   - Test 1 misión rápida
   - ✅ Launch!

---

## 🆘 Si algo falló en testnet...

**NO TE PREOCUPES:** Ese es el propósito del testing!

Si alguna función no funcionó:
1. Documenta QUÉ falló exactamente
2. Revisa el código del contrato
3. Identifica la causa
4. Modifica el contrato
5. Redeploy a testnet
6. Re-testea
7. Cuando TODO funcione → Deploy a mainnet

**VENTAJA DE TESTNET:** Puedes fallar infinitas veces sin costo. En mainnet, el contrato es inmutable.

---

## 📊 Comparación: Testnet vs Mainnet

| Aspecto | Base Sepolia (Testnet) | Base Mainnet (Production) |
|---------|------------------------|---------------------------|
| ETH | GRATIS (faucets) | REAL (comprar) |
| Gas costs | $0 USD | $3-10 USD por deploy |
| Errores | Sin consecuencias | Contrato inmutable |
| Testing | LIBRE para experimentar | Solo para producción |
| NFTs | Sin valor real | Valor real |
| Contract | `0x...` (testnet) | `0xc145caD0cAd7ee0018C31baf4621FD87887F72c5` |

---

## ✅ CONFIRMACIÓN FINAL

Después de completar TODOS los tests en testnet:

**El contrato EmberholmPortal v3.0 (Professional - No Treasury) está 100% funcional y listo para producción.**

Cambios vs v2.0:
- ❌ **REMOVIDO:** `treasury` function (no profesional)
- ✅ **IMPLEMENTADO:** Professional `withdraw()` (envía a owner)
- ✅ **MANTENIDO:** 100% de funciones de juego (missions, stats, staking, equipment, metadata)

**Mainnet contract es IDÉNTICO al que testeaste en testnet.**

🎉 **¡Listo para launch!**
