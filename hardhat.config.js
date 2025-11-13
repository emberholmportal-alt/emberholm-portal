require("@nomicfoundation/hardhat-toolbox");
require("@nomicfoundation/hardhat-verify");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
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
    // Base Mainnet (Production)
    base: {
      url: "https://mainnet.base.org",
      chainId: 8453,
      accounts: (process.env.PRIVATE_KEY && process.env.PRIVATE_KEY !== "YOUR_PRIVATE_KEY_HERE")
        ? [process.env.PRIVATE_KEY]
        : [],
      gasPrice: "auto"
    },
    // Base Sepolia (Testnet - for reference)
    baseSepolia: {
      url: "https://sepolia.base.org",
      chainId: 84532,
      accounts: (process.env.PRIVATE_KEY && process.env.PRIVATE_KEY !== "YOUR_PRIVATE_KEY_HERE")
        ? [process.env.PRIVATE_KEY]
        : []
    }
  },
  etherscan: {
    apiKey: {
      base: process.env.ETHERSCAN_API_KEY || "",
      baseSepolia: process.env.ETHERSCAN_API_KEY || ""
    },
    customChains: [
      {
        network: "base",
        chainId: 8453,
        urls: {
          apiURL: "https://api.basescan.org/api",
          browserURL: "https://basescan.org"
        }
      },
      {
        network: "baseSepolia",
        chainId: 84532,
        urls: {
          apiURL: "https://api-sepolia.basescan.org/api",
          browserURL: "https://sepolia.basescan.org"
        }
      }
    ]
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};
