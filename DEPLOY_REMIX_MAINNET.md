# 🚀 DEPLOYMENT GUIDE - Base Mainnet con Remix IDE

## ✅ Pre-requisitos

- [ ] MetaMask instalado
- [ ] ETH en Base Mainnet (~0.01-0.02 ETH para gas)
- [ ] Treasury wallet: `0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B`
- [ ] Etherscan API Key: `NJGKD47X897KTY87ZDHU9SGADFZSQY3YPW`

---

## 📋 PASO 1: Configurar MetaMask para Base Mainnet

### Agregar red Base (si no la tienes):

1. Abre MetaMask
2. Click en el selector de redes (arriba)
3. Click "Add Network" → "Add a network manually"
4. Ingresa estos datos:

```
Network Name: Base
RPC URL: https://mainnet.base.org
Chain ID: 8453
Currency Symbol: ETH
Block Explorer URL: https://basescan.org
```

5. Click "Save"
6. **Cambia a la red Base**
7. Verifica que tienes ETH suficiente (~0.01-0.02 ETH)

---

## 📋 PASO 2: Abrir Remix y Preparar Contrato

### 2.1 Abrir Remix

1. Ve a: **https://remix.ethereum.org**
2. Espera a que cargue completamente

### 2.2 Crear archivo del contrato

1. En el panel izquierdo, click en "📁 File Explorer"
2. Click en el ícono "📄" (Create new file)
3. Nombre del archivo: `EmberholmPortal.sol`
4. Click OK

### 2.3 Copiar código del contrato

1. Abre el archivo que acabas de crear
2. Copia **TODO** el código del contrato desde: `/home/user/emberholm-portal/contracts/EmberholmPortal.sol`
3. Pega el código completo en Remix
4. Guarda (Ctrl/Cmd + S)

**IMPORTANTE**: El contrato completo tiene 512 líneas. Asegúrate de copiar TODO desde:
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
...
hasta el final:
...
    }
}
```

---

## 📋 PASO 3: Compilar el Contrato

### 3.1 Ir al compilador

1. Click en el ícono "🔨 Solidity Compiler" (panel izquierdo)

### 3.2 Configurar compilador

```
Compiler: 0.8.20+commit.a1b79de6
Language: Solidity
EVM Version: default
```

### 3.3 Habilitar optimización (IMPORTANTE)

1. Click en "Advanced Configurations"
2. Activa "Enable optimization"
3. Optimization Runs: **200**

### 3.4 Compilar

1. Click en el botón grande "Compile EmberholmPortal.sol"
2. Espera unos segundos
3. **Verifica que no haya errores** (debe aparecer un ✅ verde)

---

## 📋 PASO 4: Deploy del Contrato (¡PRODUCCIÓN!)

### 4.1 Ir al panel de deployment

1. Click en "🚀 Deploy & Run Transactions" (panel izquierdo)

### 4.2 Configurar environment

```
ENVIRONMENT: Injected Provider - MetaMask
```

### 4.3 Conectar MetaMask

1. Cuando aparezca el popup de MetaMask, click "Connect"
2. Selecciona tu cuenta
3. **VERIFICA que estés en la red BASE** (no Ethereum, no Base Sepolia)
4. Verifica que tu balance sea suficiente

### 4.4 Configurar deployment

```
CONTRACT: EmberholmPortal - contracts/EmberholmPortal.sol
```

### 4.5 Ingresar parámetro del constructor

En el campo "DEPLOY" verás un input para el constructor:

```
_TREASURY (address): 0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B
```

**IMPORTANTE**: Copia exactamente esta dirección (sin espacios, con 0x al inicio)

### 4.6 Deploy!

1. Click en el botón naranja "transact"
2. **MetaMask popup aparecerá**
3. **REVISA CUIDADOSAMENTE**:
   - Red: Base (Chain ID 8453) ✅
   - Gas fee: ~$3-10 USD ✅
   - Destination: Contract Creation ✅
4. Click "Confirm"

### 4.7 Esperar confirmación

1. Verás "creation of EmberholmPortal pending..."
2. Espera 10-30 segundos
3. Cuando termine, verás el contrato desplegado en "Deployed Contracts"

### 4.8 Guardar Contract Address

1. En "Deployed Contracts", verás: `EMBERHOLMPORTAL AT 0x...`
2. **COPIA ESTA DIRECCIÓN** (click en el ícono de copiar)
3. **GUÁRDALA EN UN LUGAR SEGURO**

Ejemplo:
```
Contract Address: 0x1234567890abcdef1234567890abcdef12345678
```

---

## 📋 PASO 5: Verificar Contrato en Basescan

### 5.1 Ir a Basescan

1. Ve a: https://basescan.org/verifyContract
2. O busca tu contract address en Basescan y click "Verify and Publish"

### 5.2 Método de verificación

Selecciona:
```
Via Standard Input JSON
```

### 5.3 Datos necesarios

```
Contract Address: [TU_CONTRACT_ADDRESS]
Compiler Type: Solidity (Single file)
Compiler Version: v0.8.20+commit.a1b79de6
Open Source License Type: MIT License
```

### 5.4 Optimization

```
Optimization: Yes
Runs: 200
```

### 5.5 Pegar código

1. En "Enter the Solidity Contract Code"
2. Pega **TODO** el código del contrato (las 512 líneas)
3. **IMPORTANTE**: Incluye los imports de OpenZeppelin

### 5.6 Constructor Arguments (ABI-encoded)

Basescan te pedirá los constructor arguments en formato ABI. Usa esta herramienta:

1. Ve a: https://abi.hashex.org/
2. En "Function": Pon `constructor(address)`
3. En "Argument": Pon `0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B`
4. Click "Encode"
5. Copia el resultado (sin el 0x inicial)

O simplemente usa este valor ya codificado:
```
000000000000000000000000ae882a8933b33429f53b7cee102ef3dbf9c9e88b
```

### 5.7 Submit

1. Completa el captcha
2. Click "Verify and Publish"
3. Espera 10-20 segundos

### 5.8 Verificación exitosa

Deberías ver:
```
✅ Contract Source Code Verified!
```

---

## 📋 PASO 6: Verificar Deployment

### 6.1 Check en Basescan

1. Ve a: `https://basescan.org/address/[TU_CONTRACT_ADDRESS]`
2. Verifica que veas:
   - ✅ Contract ícono (no wallet)
   - ✅ Tab "Contract" disponible
   - ✅ Tab "Read Contract" disponible
   - ✅ Tab "Write Contract" disponible

### 6.2 Leer información del contrato

En la tab "Read Contract":

```
1. maxSupply() = 35000
2. mintPrice() = 1100000000000000 (0.0011 ETH)
3. treasury() = 0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B
4. totalMinted() = 0
5. mintOpen() = true
```

**Si todo coincide, ¡deployment exitoso!** ✅

---

## 📋 PASO 7: Configurar Mission Manager (Opcional)

Si quieres que el backend pueda unstakear NFTs automáticamente:

### 7.1 Crear wallet para backend

En Node.js o Python:
```javascript
const ethers = require('ethers');
const wallet = ethers.Wallet.createRandom();
console.log('Address:', wallet.address);
console.log('Private Key:', wallet.privateKey);
```

### 7.2 Configurar en el contrato

1. En Basescan, ve a "Write Contract"
2. Click "Connect to Web3" (conecta MetaMask)
3. Busca función `setMissionManager`
4. Ingresa la address del backend wallet
5. Click "Write"
6. Confirma en MetaMask

### 7.3 Fondear wallet del backend

Envía 0.01 ETH a la wallet del backend (para gas de unstaking)

---

## 📋 PASO 8: Test Mint (Opcional)

### 8.1 Mint tu primer NFT

1. En Basescan, "Write Contract"
2. Busca función `mint`
3. quantity: `1`
4. payableAmount: `0.0011` (Ether, no Wei)
5. Click "Write"
6. Confirma en MetaMask (pagarás 0.0011 ETH + gas)

### 8.2 Verificar

1. Ve a "Read Contract"
2. Llama `totalMinted()` → Debe retornar `1`
3. Llama `tokensOfOwner` con tu address → Debe retornar `[1]`

**Si funciona, ¡tu contrato está 100% operativo!** 🎉

---

## 📋 PASO 9: Actualizar Frontend y Backend

### Frontend (`static/index.html`)

Busca y reemplaza:
```javascript
// ANTES
const contractAddress = "0x2F55e14F0b2B2118d2026d20Ad2C39EAcBdCAc47";
const CHAIN_ID = 84532; // Base Sepolia

// DESPUÉS
const contractAddress = "0xTU_NUEVO_CONTRACT_ADDRESS";
const CHAIN_ID = 8453; // Base Mainnet
```

### Backend (`.env` o `app.py`)

```python
CONTRACT_ADDRESS = "0xTU_NUEVO_CONTRACT_ADDRESS"
NETWORK = "base-mainnet"
CHAIN_ID = 8453
```

---

## ✅ Checklist Final

- [ ] Contrato deployado en Base Mainnet
- [ ] Contract address guardada
- [ ] Contrato verificado en Basescan
- [ ] `totalMinted()` retorna 0
- [ ] `maxSupply()` retorna 35000
- [ ] `mintPrice()` retorna 0.0011 ETH
- [ ] `treasury()` retorna tu wallet
- [ ] Test mint funciona (opcional)
- [ ] Mission Manager configurado (opcional)
- [ ] Frontend actualizado con nueva address
- [ ] Backend actualizado con nueva address

---

## 🎉 ¡Deployment Completo!

Tu contrato **EmberholmPortal** está ahora **LIVE en Base Mainnet**!

**Contract Info:**
- 📍 Address: [Tu contract address]
- 🌐 Network: Base Mainnet (Chain ID: 8453)
- 🔍 Basescan: https://basescan.org/address/[tu_address]
- 💰 Treasury: 0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B

**Próximos pasos:**
1. Testea el mint
2. Verifica metadata endpoint funciona
3. Promociona la colección
4. ¡Deja que los usuarios minteen! 🚀

---

## 🆘 Troubleshooting

### "Transaction reverted"
- Verifica que estés en Base Mainnet
- Verifica que tengas ETH suficiente
- Revisa que el constructor argument sea correcto

### "Contract verification failed"
- Verifica compiler version exacta
- Verifica optimization settings (200 runs)
- Verifica constructor arguments encoding

### "Insufficient funds"
- Necesitas más ETH en Base Mainnet
- Usa un bridge o exchange para obtener ETH en Base

---

**¿Preguntas? Revisa la documentación en /contracts/DEPLOY_GUIDE.md**
