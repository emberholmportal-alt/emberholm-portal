// EmberholmPortal Contract Configuration
// Base Mainnet Deployment

const CONTRACT_CONFIG = {
    // ========== CONTRACT ADDRESSES ==========
    // EmberholmPortal - Main NFT Contract on Base Mainnet
    ADDRESS: "0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3",

    // All Emberholm Contracts (Base Mainnet)
    CONTRACTS: {
        EmberholmPortal: "0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3"
    },

    // ========== NETWORK CONFIGURATION ==========
    // Base Mainnet
    CHAIN_ID: 8453,
    CHAIN_ID_HEX: "0x2105",
    NETWORK_NAME: "Base",
    RPC_URL: "https://mainnet.base.org",
    BLOCK_EXPLORER: "https://basescan.org",

    // ========== IPFS METADATA ==========
    IPFS_METADATA_BASE: "https://ipfs.io/ipfs/bafybeidd7wtx7izjgsociwe6ynjz6c3xslqmcedr7z4wojcxs4yd5u7pim/",

    // ========== ABI - EmberholmPortal ==========
    ABI: [
        // ========== SUPPLY ==========
        "function totalSupply() view returns (uint256)",
        "function MAX_SUPPLY() view returns (uint256)",

        // ========== QUERIES ==========
        "function tokensOfOwner(address owner_) view returns (uint256[])",
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
