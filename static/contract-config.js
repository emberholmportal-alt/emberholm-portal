// EmberholmPortal Contract Configuration
// Base Mainnet Deployment

const CONTRACT_CONFIG = {
    // ========== CONTRACT ADDRESSES ==========
    // EmberholmPortal - Main NFT Contract on Base Mainnet
    ADDRESS: "0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3",

    // All Emberholm Contracts (Base Mainnet)
    CONTRACTS: {
        EmberholmPortal: "0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3",
        EmberRunes: "0xDa2D1085053c3700645a13498293D17c1cc3f595",
        EmberItems: "0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA"
    },

    // ========== NETWORK CONFIGURATION ==========
    // Base Mainnet
    CHAIN_ID: 8453,
    CHAIN_ID_HEX: "0x2105",
    NETWORK_NAME: "Base",
    RPC_URL: "https://mainnet.base.org",
    BLOCK_EXPLORER: "https://basescan.org",

    // ========== IPFS METADATA ==========
    // Metadata JSON CID
    IPFS_METADATA_BASE: "https://ipfs.io/ipfs/bafybeidd7wtx7izjgsociwe6ynjz6c3xslqmcedr7z4wojcxs4yd5u7pim/",
    // Images PNG CID (different from metadata!)
    IPFS_IMAGES_BASE: "https://ipfs.io/ipfs/bafybeicnvc3zagcncablcovpxgt5mtuotowvuqom6kby754ve2gwbzdvkm/",

    // ========== ABI - EmberholmPortal ==========
    ABI: [
        // ========== SUPPLY ==========
        "function totalSupply() view returns (uint256)",
        "function maxSupply() pure returns (uint256)",
        "function totalMinted() view returns (uint256)",

        // ========== QUERIES ==========
        "function tokensOfOwner(address owner) view returns (uint256[])",
        "function tokenURI(uint256 tokenId) view returns (string)",
        "function balanceOf(address owner) view returns (uint256)",
        "function ownerOf(uint256 tokenId) view returns (address)",

        // ========== MINT ==========
        "function mint(uint256 quantity) payable",
        "function mintPrice() view returns (uint256)",
        "function mintOpen() view returns (bool)",
        "function getFreeMints(address wallet) view returns (uint256)",

        // ========== EVENTS ==========
        "event Transfer(address indexed from, address indexed to, uint256 indexed tokenId)"
    ],

    // ========== ABI - EmberRunes (Drop NFT) ==========
    RUNES_ABI: [
        "function claimRune(bytes32 claimId, bytes signature) external",
        "function balanceOf(address owner) view returns (uint256)",
        "function tokensOfOwner(address owner) view returns (uint256[])",
        "function tokenURI(uint256 tokenId) view returns (string)",
        "event RuneClaimed(address indexed player, uint256 indexed tokenId, bytes32 claimId)"
    ],

    // ========== ABI - EmberItems (Drop NFT) ==========
    ITEMS_ABI: [
        "function claimItem(bytes32 claimId, bytes signature) external",
        "function balanceOf(address owner) view returns (uint256)",
        "function tokensOfOwner(address owner) view returns (uint256[])",
        "function tokenURI(uint256 tokenId) view returns (string)",
        "event ItemClaimed(address indexed player, uint256 indexed tokenId, bytes32 claimId)"
    ],

    // ========== DROP PROBABILITIES BY DIFFICULTY ==========
    DROP_RATES: {
        EASY:   { item: 5,  rune: 1 },
        MEDIUM: { item: 10, rune: 3 },
        HARD:   { item: 20, rune: 8 },
        PARTY:  { item: 25, rune: 12 }
    }
};
