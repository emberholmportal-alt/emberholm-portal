# EmberholmPortal V2 - Deployment Guide

## 🎯 Overview

This is the **complete, production-ready** EmberholmPortal contract with all features:
- ✅ TIER 1: Basic queries (totalMinted, tokensOfOwner, etc)
- ✅ TIER 2: Batch operations, staking, primary token
- ✅ TIER 3: Achievements, guild leadership, custom metadata, equipment slots

**Ready for:** Base Sepolia (testnet) → Base Mainnet (production)

---

## 📋 Pre-Deployment Checklist

### 1. Prepare Treasury Wallet
```javascript
// Base Sepolia (testnet)
TREASURY_ADDRESS = "0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B"

// Base Mainnet (production) - CHANGE THIS!
TREASURY_ADDRESS = "0xYOUR_MAINNET_TREASURY_WALLET"
```

### 2. Prepare Deployment Wallet
- Need ETH for gas on Base Sepolia or Base Mainnet
- Base Sepolia: Get testnet ETH from faucet
- Base Mainnet: Need real ETH (~$50-100 for deployment)

### 3. Verify Contract Code
- Review EmberholmPortal.sol
- Confirm all functions are correct
- Test locally if possible

---

## 🚀 Deployment Steps

### Option A: Using Hardhat

#### 1. Install Dependencies
```bash
cd /home/user/emberholm-portal
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
npm install @openzeppelin/contracts
```

#### 2. Create hardhat.config.js
```javascript
require("@nomicfoundation/hardhat-toolbox");

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
      chainId: 84532,
      accounts: [process.env.PRIVATE_KEY] // Your deployer wallet private key
    },
    base: {
      url: "https://mainnet.base.org",
      chainId: 8453,
      accounts: [process.env.PRIVATE_KEY]
    }
  },
  etherscan: {
    apiKey: {
      baseSepolia: process.env.BASESCAN_API_KEY,
      base: process.env.BASESCAN_API_KEY
    },
    customChains: [
      {
        network: "baseSepolia",
        chainId: 84532,
        urls: {
          apiURL: "https://api-sepolia.basescan.org/api",
          browserURL: "https://sepolia.basescan.org"
        }
      },
      {
        network: "base",
        chainId: 8453,
        urls: {
          apiURL: "https://api.basescan.org/api",
          browserURL: "https://basescan.org"
        }
      }
    ]
  }
};
```

#### 3. Create .env File
```bash
# .env
PRIVATE_KEY=your_deployer_wallet_private_key_here
BASESCAN_API_KEY=your_basescan_api_key_here
TREASURY_ADDRESS=0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B
```

#### 4. Create Deploy Script
```javascript
// scripts/deploy.js
const hre = require("hardhat");

async function main() {
  const treasuryAddress = process.env.TREASURY_ADDRESS;

  console.log("Deploying EmberholmPortal...");
  console.log("Treasury:", treasuryAddress);

  const EmberholmPortal = await hre.ethers.getContractFactory("EmberholmPortal");
  const portal = await EmberholmPortal.deploy(treasuryAddress);

  await portal.waitForDeployment();
  const address = await portal.getAddress();

  console.log("✅ EmberholmPortal deployed to:", address);
  console.log("");
  console.log("Next steps:");
  console.log("1. Verify contract on Basescan");
  console.log("2. Update frontend with new address");
  console.log("3. Update backend with new address");
  console.log("");
  console.log("Verify command:");
  console.log(`npx hardhat verify --network baseSepolia ${address} ${treasuryAddress}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

#### 5. Deploy to Base Sepolia
```bash
npx hardhat run scripts/deploy.js --network baseSepolia
```

#### 6. Verify on Basescan
```bash
npx hardhat verify --network baseSepolia <CONTRACT_ADDRESS> <TREASURY_ADDRESS>
```

---

### Option B: Using Remix IDE (Easier)

#### 1. Open Remix
Go to: https://remix.ethereum.org

#### 2. Create Contract File
- Create new file: `EmberholmPortal.sol`
- Copy paste the contract code from `contracts/EmberholmPortal.sol`

#### 3. Compile
- Compiler version: 0.8.20
- Optimization: Enabled (200 runs)
- Click "Compile EmberholmPortal.sol"

#### 4. Deploy
- Environment: "Injected Provider - MetaMask"
- Switch MetaMask to Base Sepolia network
- Contract: EmberholmPortal
- Constructor args:
  - `_treasury`: `0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B`
- Click "Deploy"
- Confirm in MetaMask

#### 5. Copy Contract Address
- Copy the deployed contract address
- Save it for next steps

---

## 📝 Post-Deployment Tasks

### 1. Verify Contract on Basescan

Visit: https://sepolia.basescan.org/verifyContract

- Contract Address: `<YOUR_DEPLOYED_ADDRESS>`
- Compiler Type: Solidity (Single file)
- Compiler Version: v0.8.20
- License: MIT
- Optimization: Yes (200 runs)
- Constructor Arguments ABI-encoded: Use Basescan's tool

### 2. Set Mission Manager (Optional)

```javascript
// If you want backend to control staking/achievements
await contract.setMissionManager("0xYOUR_BACKEND_WALLET");
```

### 3. Test Basic Functions

```javascript
// Test minting
await contract.mint(1, { value: ethers.parseEther("0.0011") });

// Test totalMinted
const total = await contract.totalMinted();
console.log("Total minted:", total);

// Test tokensOfOwner
const tokens = await contract.tokensOfOwner(userAddress);
console.log("User tokens:", tokens);
```

---

## 🔄 Update Frontend & Backend

### Frontend Updates

File: `/home/user/emberholm-portal/static/index.html`

**Find and replace:**
```javascript
// OLD
const contractAddress = "0x2F55e14F0b2B2118d2026d20Ad2C39EAcBdCAc47";

// NEW
const contractAddress = "0xNEW_CONTRACT_ADDRESS_HERE";
```

**Update ABI:**
```javascript
// OLD (minimal ABI)
const abi = [
    "function balanceOf(address owner) view returns (uint256)",
    "function ownerOf(uint256 tokenId) view returns (address)",
    "function totalMinted() view returns (uint256)",
    // ...
];

// NEW (use complete ABI from compiled contract)
// Get from Basescan after verification, or from Hardhat/Remix
```

### Backend Updates

File: `/home/user/emberholm-portal/app.py`

**Update contract address (if used):**
```python
# If you store contract address in backend
CONTRACT_ADDRESS = "0xNEW_CONTRACT_ADDRESS_HERE"
```

---

## ✅ Testing Checklist

After deployment, test these features:

### TIER 1 - Basic Functions
- [ ] Mint NFT
- [ ] Check totalMinted()
- [ ] Check tokensOfOwner()
- [ ] Set guild
- [ ] Set name
- [ ] View PROFILE with NFT data

### TIER 2 - Advanced Functions
- [ ] Batch get token info (multiple NFTs)
- [ ] Get wallet profile (all data in 1 call)
- [ ] Stake token
- [ ] Try to transfer staked token (should fail)
- [ ] Unstake token
- [ ] Set primary token
- [ ] View TOP EMISSARY

### TIER 3 - Future Features
- [ ] Grant achievement (as mission manager)
- [ ] Set guild leader (as owner)
- [ ] Set token image
- [ ] Set token attribute

---

## 🌐 Migrate to Mainnet

When ready for production:

### 1. Same Contract, Different Network
```bash
# Deploy to Base Mainnet instead
npx hardhat run scripts/deploy.js --network base
```

### 2. Update Treasury
Make sure to use production treasury wallet!

### 3. Update Frontend/Backend
Change:
- Contract address
- Chain ID (84532 → 8453)
- Network name ("Base Sepolia" → "Base")

### 4. Verify on Mainnet Basescan
https://basescan.org/verifyContract

---

## 📊 Contract Info Summary

**Name:** Emberholm Portal
**Symbol:** EMBERHOLM
**Max Supply:** 35,000
**Mint Price:** 0.0011 ETH
**Royalty:** 5% to treasury

**Features:**
- ERC721 with ERC2981 royalties
- Guild system (6 guilds)
- Staking mechanism
- Achievement system
- Equipment slots (prepared for items)
- Guild leadership
- Custom metadata

**Networks:**
- Base Sepolia (testnet): Chain ID 84532
- Base (mainnet): Chain ID 8453

---

## 🆘 Troubleshooting

### "Transaction reverted" during deployment
- Check you have enough ETH for gas
- Verify constructor args are correct
- Check compiler version matches

### "Contract verification failed"
- Ensure same compiler version
- Ensure same optimization settings
- Check constructor arguments encoding

### Frontend not showing NFTs
- Clear browser cache
- Verify contract address is updated
- Check console for errors
- Verify network is Base Sepolia

---

## 📞 Next Steps

After successful deployment:

1. ✅ Update contract address in frontend
2. ✅ Update contract address in backend (if needed)
3. ✅ Test all PROFILE features
4. ✅ Mint test NFTs
5. ✅ Deploy to production (Base Mainnet) when ready

**Contract is ready for:**
- ✅ Full gameplay
- ✅ Guild system
- ✅ Achievements
- ✅ Future items integration (just deploy Items contract and connect)
