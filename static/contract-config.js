// EmberholmPortal V2 Contract Configuration
// Update these values after deploying to Base Sepolia

const CONTRACT_CONFIG = {
    // ✅ EmberholmPortal V2 deployed on Base Sepolia
    ADDRESS: "0xA93C701F0dD91DE0E82f6796d56c4c7aeE053749",

    // Base Sepolia Testnet
    CHAIN_ID: 84532,
    CHAIN_ID_HEX: "0x14a34",
    NETWORK_NAME: "Base Sepolia",
    RPC_URL: "https://sepolia.base.org",
    BLOCK_EXPLORER: "https://sepolia.basescan.org",

    // ABI simplificado - solo funciones que usamos
    ABI: [
        // ========== QUERIES ==========
        "function totalMinted() view returns (uint256)",
        "function maxSupply() pure returns (uint256)",
        "function tokensOfOwner(address owner) view returns (uint256[])",
        "function getTokenInfo(uint256 tokenId) view returns (tuple(uint256 tokenId, address owner, bool isStaked))",
        "function batchGetTokenInfo(uint256[] tokenIds) view returns (tuple(uint256 tokenId, address owner, bool isStaked)[])",
        "function getWalletProfile(address owner) view returns (uint256[] tokenIds, tuple(uint256 tokenId, address owner, bool isStaked)[] tokens, tuple(uint256 totalTokens, uint256 stakedCount) stats)",
        "function getPrimaryTokenInfo(address owner) view returns (tuple(uint256 tokenId, address owner, bool isStaked))",
        "function tokenURI(uint256 tokenId) view returns (string)",
        "function balanceOf(address owner) view returns (uint256)",

        // ========== STAKING ==========
        "function stakeToken(uint256 tokenId)",
        "function unstakeToken(uint256 tokenId)",
        "function stakedTokens(uint256 tokenId) view returns (bool)",
        "function stakeTimestamp(uint256 tokenId) view returns (uint256)",

        // ========== PRIMARY TOKEN ==========
        "function setPrimaryToken(uint256 tokenId)",
        "function primaryToken(address owner) view returns (uint256)",

        // ========== EQUIPMENT (Future) ==========
        "function equipItem(uint256 tokenId, string slot, uint256 itemId)",
        "function unequipItem(uint256 tokenId, string slot)",
        "function getEquippedItems(uint256 tokenId) view returns (uint256 weapon, uint256 armor, uint256 boots, uint256 accessory)",

        // ========== MINT ==========
        "function mint(uint256 quantity) payable",
        "function mintPrice() view returns (uint256)",
        "function mintOpen() view returns (bool)",

        // ========== EVENTS ==========
        "event TokenStaked(uint256 indexed tokenId, address indexed owner, uint256 timestamp)",
        "event TokenUnstaked(uint256 indexed tokenId, address indexed owner, uint256 timestamp)",
        "event PrimaryTokenSet(address indexed owner, uint256 indexed tokenId)",
        "event Transfer(address indexed from, address indexed to, uint256 indexed tokenId)"
    ]
};

// Para producción (Base Mainnet), cambia a:
// CHAIN_ID: 8453
// CHAIN_ID_HEX: "0x2105"
// RPC_URL: "https://mainnet.base.org"
// BLOCK_EXPLORER: "https://basescan.org"
