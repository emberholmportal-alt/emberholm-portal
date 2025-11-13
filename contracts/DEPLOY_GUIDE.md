# 🚀 Guía de Deployment - EmberholmPortal V2

## Paso 1: Deploy a Base Sepolia (Testnet)

### Opción A: Remix IDE (MÁS FÁCIL) ⭐ RECOMENDADO

#### 1.1 Preparar Remix

1. Ve a: **https://remix.ethereum.org/**
2. Crea nuevo archivo: `EmberholmPortal.sol`
3. Copia y pega el contrato completo desde `/home/user/emberholm-portal/contracts/EmberholmPortal.sol`

#### 1.2 Instalar Dependencias OpenZeppelin

En Remix, las dependencias se importan automáticamente. El compilador las descargará.

#### 1.3 Compilar

1. Click en "Solidity Compiler" (icono de Solidity)
2. Configurar:
   - **Compiler:** 0.8.20
   - **EVM Version:** default
   - **Optimization:** 200 runs (recomendado)
3. Click "Compile EmberholmPortal.sol"
4. Verificar: ✅ Sin errores

#### 1.4 Configurar MetaMask para Base Sepolia

**Network Details:**
```
Network Name: Base Sepolia
RPC URL: https://sepolia.base.org
Chain ID: 84532
Currency Symbol: ETH
Block Explorer: https://sepolia.basescan.org
```

**Agregar a MetaMask:**
1. MetaMask → Networks → Add Network
2. Ingresa los datos arriba
3. Save

**Obtener ETH testnet:**
1. Ve a: https://www.alchemy.com/faucets/base-sepolia
2. O: https://sepolia.basescan.org/faucet
3. Solicita 0.1 ETH para deploy (suficiente)

#### 1.5 Deploy

1. Click "Deploy & Run Transactions" (icono de Ethereum)
2. Configurar:
   - **Environment:** "Injected Provider - MetaMask"
   - **Account:** Tu wallet en MetaMask
   - **Contract:** EmberholmPortal
3. Constructor Parameter:
   - `_TREASURY`: `0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B`

4. **Gas Limit:** 5,000,000 (auto-detect)
5. Click "Deploy"
6. MetaMask popup → Confirmar transacción

**Esperar confirmación (~5 segundos)**

#### 1.6 Guardar Contract Address

Cuando termine:
```
✅ Contract deployed at: 0x1234567890abcdef...

GUARDA ESTA DIRECCIÓN! La necesitarás para frontend/backend.
```

#### 1.7 Verificar en Basescan

1. Ve a: https://sepolia.basescan.org/address/0xTU_CONTRACT_ADDRESS
2. Verifica que aparece el contrato
3. Click "Contract" → "Verify and Publish"

**Verification:**
- Compiler: 0.8.20
- Optimization: Yes (200 runs)
- License: MIT
- Constructor Arguments: (auto-detect)
- Pega el código fuente

**Resultado:** ✅ Código verificado, usuarios pueden ver las funciones

---

### Opción B: Hardhat (Para Desarrolladores)

#### 2.1 Instalar Hardhat

```bash
cd /home/user/emberholm-portal/contracts
npm init -y
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
npx hardhat
```

Selecciona: "Create a JavaScript project"

#### 2.2 Instalar OpenZeppelin

```bash
npm install @openzeppelin/contracts
```

#### 2.3 Configurar hardhat.config.js

```javascript
require("@nomicfoundation/hardhat-toolbox");
require('dotenv').config();

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    baseSepolia: {
      url: "https://sepolia.base.org",
      accounts: [process.env.PRIVATE_KEY], // Tu private key
      chainId: 84532
    }
  },
  etherscan: {
    apiKey: {
      baseSepolia: process.env.BASESCAN_API_KEY
    },
    customChains: [
      {
        network: "baseSepolia",
        chainId: 84532,
        urls: {
          apiURL: "https://api-sepolia.basescan.org/api",
          browserURL: "https://sepolia.basescan.org"
        }
      }
    ]
  }
};
```

#### 2.4 Crear .env

```bash
PRIVATE_KEY=tu_private_key_aqui
BASESCAN_API_KEY=tu_basescan_api_key_aqui
TREASURY_ADDRESS=0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B
```

#### 2.5 Crear Script de Deploy

`scripts/deploy.js`:
```javascript
const hre = require("hardhat");

async function main() {
  const treasury = process.env.TREASURY_ADDRESS;

  console.log("Deploying EmberholmPortal...");
  console.log("Treasury:", treasury);

  const EmberholmPortal = await hre.ethers.getContractFactory("EmberholmPortal");
  const portal = await EmberholmPortal.deploy(treasury);

  await portal.deployed();

  console.log("✅ EmberholmPortal deployed to:", portal.address);
  console.log("🔍 Verify on Basescan:");
  console.log(`https://sepolia.basescan.org/address/${portal.address}`);

  // Wait for block confirmations
  console.log("Waiting for confirmations...");
  await portal.deployTransaction.wait(5);

  // Verify on Basescan
  console.log("Verifying contract...");
  await hre.run("verify:verify", {
    address: portal.address,
    constructorArguments: [treasury],
  });

  console.log("✅ Contract verified!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

#### 2.6 Deploy

```bash
npx hardhat run scripts/deploy.js --network baseSepolia
```

**Output:**
```
Deploying EmberholmPortal...
Treasury: 0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B
✅ EmberholmPortal deployed to: 0x1234567890abcdef...
🔍 Verify on Basescan: https://sepolia.basescan.org/address/0x1234567890abcdef...
Waiting for confirmations...
Verifying contract...
✅ Contract verified!
```

---

## Paso 2: Configuración Inicial

### 2.1 Configurar Mission Manager

El backend necesita una wallet para unstakear NFTs después de misiones.

**Crear wallet para backend:**
```javascript
// En Node.js o en tu backend
const ethers = require('ethers');
const wallet = ethers.Wallet.createRandom();

console.log('Mission Manager Address:', wallet.address);
console.log('Private Key:', wallet.privateKey);
// GUARDA ESTO EN .env DEL BACKEND
```

**Configurar en el contrato:**
```javascript
// En Remix o Hardhat
await contract.setMissionManager("0xMissionManagerAddress");
```

**Fondear la wallet:**
- Envía 0.01 ETH a esta wallet (para gas de unstaking)
- Backend usará esta wallet para llamar `unstakeToken()`

### 2.2 Verificar Configuración

```javascript
// Verificar todo está correcto
const mintPrice = await contract.mintPrice();
console.log('Mint Price:', ethers.utils.formatEther(mintPrice), 'ETH');

const treasury = await contract.treasury();
console.log('Treasury:', treasury);

const missionManager = await contract.missionManager();
console.log('Mission Manager:', missionManager);

const maxSupply = await contract.maxSupply();
console.log('Max Supply:', maxSupply.toString());
```

---

## Paso 3: Testing en Base Sepolia

### 3.1 Test Mint

```javascript
// Mintear 1 NFT
const tx = await contract.mint(1, {
  value: ethers.utils.parseEther("0.0011")
});
await tx.wait();

console.log('✅ Minted token #1');
```

### 3.2 Test Queries

```javascript
const totalMinted = await contract.totalMinted();
console.log('Total Minted:', totalMinted.toString());

const myTokens = await contract.tokensOfOwner(myAddress);
console.log('My Tokens:', myTokens.map(t => t.toString()));

const tokenInfo = await contract.getTokenInfo(1);
console.log('Token 1 Info:', tokenInfo);
```

### 3.3 Test Staking

```javascript
// Stakear NFT
await contract.stakeToken(1);
console.log('✅ Token #1 staked');

// Intentar transferir (debe fallar)
try {
  await contract.transferFrom(myAddress, otherAddress, 1);
  console.log('❌ ERROR: Transfer should have failed!');
} catch (error) {
  console.log('✅ Correctly blocked transfer of staked token');
}

// Unstakear
await contract.unstakeToken(1);
console.log('✅ Token #1 unstaked');

// Ahora sí se puede transferir
await contract.transferFrom(myAddress, otherAddress, 1);
console.log('✅ Transfer successful after unstake');
```

### 3.4 Test Metadata

```javascript
const uri = await contract.tokenURI(1);
console.log('Token URI:', uri);
// Debe ser: https://emberholm-portal.onrender.com/api/metadata/1

// Fetch metadata
const response = await fetch(uri);
const metadata = await response.json();
console.log('Metadata:', metadata);
```

---

## Paso 4: Deploy a Base Mainnet (Producción)

**⚠️ SOLO después de testear todo en Sepolia**

### 4.1 Cambiar Network

**Base Mainnet:**
```
Network Name: Base
RPC URL: https://mainnet.base.org
Chain ID: 8453
Currency Symbol: ETH
Block Explorer: https://basescan.org
```

### 4.2 Preparar Real ETH

- Necesitas ~0.01-0.02 ETH real para deploy
- Bridge ETH desde Ethereum mainnet a Base
- O compra ETH directamente en Base

### 4.3 Deploy Proceso Idéntico

1. Usa el mismo contrato (sin cambios)
2. Deploy con Remix o Hardhat a Base mainnet
3. Guarda contract address
4. Verifica en Basescan

### 4.4 Actualizar Frontend/Backend

```javascript
// Frontend: static/index.html
const CONTRACT_ADDRESS = "0xNEW_MAINNET_ADDRESS";
const CHAIN_ID = 8453; // Base mainnet

// Backend: .env
CONTRACT_ADDRESS=0xNEW_MAINNET_ADDRESS
NETWORK=base-mainnet
```

---

## Checklist Final

### Deploy Completado ✅
- [ ] Contrato deployado a Base Sepolia
- [ ] Contract address guardada
- [ ] Código verificado en Basescan
- [ ] Treasury configurada correctamente
- [ ] Mission Manager wallet creada
- [ ] Mission Manager configurado en contrato
- [ ] Mission Manager wallet fondeada (0.01 ETH)

### Testing Completado ✅
- [ ] Mint funciona
- [ ] totalMinted() retorna valor correcto
- [ ] tokensOfOwner() retorna array correcto
- [ ] getTokenInfo() retorna data correcta
- [ ] Staking bloquea transfers
- [ ] Unstaking permite transfers
- [ ] tokenURI() retorna URL correcta
- [ ] Metadata endpoint responde correctamente

### Configuración Backend ✅
- [ ] .env con CONTRACT_ADDRESS
- [ ] .env con MISSION_MANAGER_PRIVATE_KEY
- [ ] Backend puede llamar unstakeToken()
- [ ] Backend genera metadata correctamente

### Configuración Frontend ✅
- [ ] CONTRACT_ADDRESS actualizado
- [ ] CHAIN_ID = 84532 (Sepolia) o 8453 (Mainnet)
- [ ] ABI actualizado
- [ ] Network switch forzado a Base Sepolia
- [ ] Queries funcionan correctamente

### OpenSea Integration ✅
- [ ] NFTs aparecen en OpenSea testnet
- [ ] Metadata se muestra correctamente
- [ ] Attributes (guild, achievements) visibles
- [ ] Refresh metadata funciona

---

## Comandos Útiles

### Remix
```
Compile: Ctrl/Cmd + S
Deploy: Click "Deploy" button
Interact: Use deployed contract UI
```

### Hardhat
```bash
# Compile
npx hardhat compile

# Deploy to Sepolia
npx hardhat run scripts/deploy.js --network baseSepolia

# Verify contract
npx hardhat verify --network baseSepolia CONTRACT_ADDRESS "TREASURY_ADDRESS"

# Run tests
npx hardhat test

# Get contract size
npx hardhat size-contracts
```

### Cast (Foundry)
```bash
# Check totalMinted
cast call CONTRACT_ADDRESS "totalMinted()(uint256)" --rpc-url https://sepolia.base.org

# Check balance
cast call CONTRACT_ADDRESS "balanceOf(address)(uint256)" WALLET_ADDRESS --rpc-url https://sepolia.base.org

# Send transaction (stake)
cast send CONTRACT_ADDRESS "stakeToken(uint256)" TOKEN_ID --rpc-url https://sepolia.base.org --private-key PRIVATE_KEY
```

---

## Troubleshooting

### Error: "Insufficient funds"
- **Causa:** No tienes ETH en tu wallet
- **Solución:** Obtén ETH del faucet o bridge

### Error: "Invalid treasury address"
- **Causa:** Treasury address es 0x0 o inválida
- **Solución:** Verifica que la address sea correcta

### Error: "Contract verification failed"
- **Causa:** Código no coincide o parámetros incorrectos
- **Solución:** Verifica compiler version, optimization, y constructor args

### Metadata no se muestra en OpenSea
- **Causa:** Backend no responde en /api/metadata/
- **Solución:** Verifica que backend esté corriendo y accesible

### NFT no se puede transferir
- **Causa:** Probablemente está staked
- **Solución:** Llama unstakeToken() primero

---

## Próximos Pasos

Después del deploy:
1. ✅ Actualizar backend (Paso 2)
2. ✅ Actualizar frontend (Paso 3)
3. ✅ Test completo end-to-end
4. ✅ Deploy a Base Mainnet (cuando estés listo)

---

**¿Listo para deployar? Sigue la Opción A (Remix) para la forma más fácil!**
