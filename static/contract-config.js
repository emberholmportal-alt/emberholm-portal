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
        // ========== SUPPLY ==========
        "function totalSupply() view returns (uint256)",
        "function MAX_SUPPLY() view returns (uint256)",

        // ========== QUERIES ==========
        "function tokensOfOwner(address owner) view returns (uint256[])",
        "function tokenURI(uint256 tokenId) view returns (string)",
        "function balanceOf(address owner) view returns (uint256)",
        "function ownerOf(uint256 tokenId) view returns (address)",

        // ========== MINT ==========
        "function mint(uint256 quantity) payable",
        "function MINT_PRICE() view returns (uint256)",
        "function mintOpen() view returns (bool)",
        "function MAX_PER_TX() view returns (uint256)",

        // ========== EVENTS ==========
        "event Transfer(address indexed from, address indexed to, uint256 indexed tokenId)"
    ]
};

// Para producción (Base Mainnet), cambia a:
// CHAIN_ID: 8453
// CHAIN_ID_HEX: "0x2105"
// RPC_URL: "https://mainnet.base.org"
// BLOCK_EXPLORER: "https://basescan.org"
