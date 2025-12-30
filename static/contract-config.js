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

    // ========== ABI - EmberholmPortal ==========
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
        "function ownerOf(uint256 tokenId) view returns (address)",

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
