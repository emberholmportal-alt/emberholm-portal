// EmberholmPortal Contract Configuration
// Base Sepolia Testnet Deployment

const CONTRACT_CONFIG = {
    // ========== CONTRACT ADDRESSES ==========
    // EmberholmPortal V2 - Main NFT Contract
    ADDRESS: "0x1db270b8a9725962f1B808a46b919F9a50312659",

    // All Emberholm Contracts
    CONTRACTS: {
        EmberholmPortal: "0x1db270b8a9725962f1B808a46b919F9a50312659",
        EmberToken: "0xa35bcc45F1b216Ed83D14B37625789ec2EEeE082",
        AshToken: "0xDc211Dc3bBe0D8b9Cd38c12863fcCeD46C1162d2",
        AshProtocol: "0xE5F683963180D53051FaB2D2C6B63DA5413fBea8",
        EmberLands: "0x9Ab5465C2978005751E5a435CE8f34242b7EE298",
        EmberRunes: "0x83061983a3E360ef9A5570FF513f8a67fad92CdC",
        ItemShop: "0xCE140A9771DA3A5a9D443b3f7FBF6B900340C161"
    },

    // ========== NETWORK CONFIGURATION ==========
    // Base Sepolia Testnet
    CHAIN_ID: 84532,
    CHAIN_ID_HEX: "0x14a34",
    NETWORK_NAME: "Base Sepolia",
    RPC_URL: "https://sepolia.base.org",
    BLOCK_EXPLORER: "https://sepolia.basescan.org",

    // ========== ABI - EmberholmPortal V2 ==========
    ABI: [
        // Mint function
        {"inputs":[{"name":"quantity","type":"uint256"}],"name":"mint","outputs":[],"stateMutability":"payable","type":"function"},

        // Variables públicas (se acceden como funciones)
        {"inputs":[],"name":"mintPrice","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
        {"inputs":[],"name":"mintOpen","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},

        // Constantes
        {"inputs":[],"name":"MAX_SUPPLY","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
        {"inputs":[],"name":"MAX_PER_TX","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},

        // ERC721 Enumerable
        {"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
        {"inputs":[{"name":"owner","type":"address"}],"name":"tokensOfOwner","outputs":[{"name":"","type":"uint256[]"}],"stateMutability":"view","type":"function"},
        {"inputs":[{"name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
        {"inputs":[{"name":"tokenId","type":"uint256"}],"name":"ownerOf","outputs":[{"name":"","type":"address"}],"stateMutability":"view","type":"function"},

        // Supply info helper
        {"inputs":[],"name":"supplyInfo","outputs":[{"name":"total","type":"uint256"},{"name":"minted","type":"uint256"},{"name":"remaining","type":"uint256"}],"stateMutability":"view","type":"function"},

        // Events
        {"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},{"indexed":true,"name":"to","type":"address"},{"indexed":true,"name":"tokenId","type":"uint256"}],"name":"Transfer","type":"event"},
        {"anonymous":false,"inputs":[{"indexed":true,"name":"to","type":"address"},{"indexed":true,"name":"tokenId","type":"uint256"}],"name":"Minted","type":"event"}
    ]
};

// Para producción (Base Mainnet), cambia a:
// CHAIN_ID: 8453
// CHAIN_ID_HEX: "0x2105"
// RPC_URL: "https://mainnet.base.org"
// BLOCK_EXPLORER: "https://basescan.org"
