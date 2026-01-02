// EmberholmPortal Contract Configuration
// Base Mainnet Deployment - Updated January 2, 2026

const CONTRACT_CONFIG = {
    // ========== CONTRACT ADDRESSES (BASE MAINNET) ==========
    // EmberholmPortal - Main NFT Contract (35,000 Emissaries)
    ADDRESS: "0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3",

    // All Emberholm Contracts
    CONTRACTS: {
        // NFT Collections (ERC721)
        EmberholmPortal: "0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3",  // 35,000 Emissaries
        EmberLands: "0x759012afba17629Cf7Eeb6a3b4a8bB4EA83762B0",       // 10,000 Lands

        // NFT Collections (ERC1155) - Con sistema de CLAIM
        EmberRunes: "0xDa2D1085053c3700645a13498293D17c1cc3f595",       // 5,000 Runes
        EmberItems: "0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA",       // 50,000 Items

        // ERC20 Tokens
        EmberToken: "0x2f2Cc49faDd8Ff1A8FC3c3844F5FaA7293538B01",
        AshToken: "0x32da1Df31D66D05cA3738925DB010A9372640590",

        // Utility
        AshProtocol: "0xbC26c4a0063E2D61862a25c5300f0A942507F437"
    },

    // Wallets
    WALLETS: {
        BACKEND_SIGNER: "0x05C169A288b509237c5983BA0D8463A821a45BE1",
        TREASURY: "0x31d6E19aAE43B5E2fbeDb01b6FF82AD1e8B576DC",
        OWNER: "0xaE882a8933b33429F53B7Cee102Ef3Dbf9C9E88B"
    },

    // ========== NETWORK CONFIGURATION ==========
    // Base Mainnet
    CHAIN_ID: 8453,
    CHAIN_ID_HEX: "0x2105",
    NETWORK_NAME: "Base",
    RPC_URL: "https://mainnet.base.org",
    BLOCK_EXPLORER: "https://basescan.org",

    // ========== IPFS CONFIGURATION ==========
    METADATA_CID: "bafybeicnvc3zagcncablcovpxgt5mtuotowvuqom6kby754ve2gwbzdvkm",
    IPFS_GATEWAY: "https://ipfs.io/ipfs/",

    // ========== ABI - EmberholmPortal (ERC721) ==========
    ABI: [
        // Mint function
        {"inputs":[{"name":"quantity","type":"uint256"}],"name":"mint","outputs":[],"stateMutability":"payable","type":"function"},

        // Variables públicas (camelCase)
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
        {"inputs":[{"name":"tokenId","type":"uint256"}],"name":"tokenURI","outputs":[{"name":"","type":"string"}],"stateMutability":"view","type":"function"},

        // Supply info helper
        {"inputs":[],"name":"supplyInfo","outputs":[{"name":"total","type":"uint256"},{"name":"minted","type":"uint256"},{"name":"remaining","type":"uint256"}],"stateMutability":"view","type":"function"},

        // Events
        {"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},{"indexed":true,"name":"to","type":"address"},{"indexed":true,"name":"tokenId","type":"uint256"}],"name":"Transfer","type":"event"},
        {"anonymous":false,"inputs":[{"indexed":true,"name":"to","type":"address"},{"indexed":true,"name":"tokenId","type":"uint256"}],"name":"Minted","type":"event"}
    ],

    // ========== ABI - EmberRunes (ERC1155 con Claim) ==========
    RUNES_ABI: [
        {"inputs":[{"name":"claimId","type":"bytes32"},{"name":"signature","type":"bytes"}],"name":"claimRune","outputs":[{"name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
        {"inputs":[{"name":"player","type":"address"},{"name":"claimId","type":"bytes32"},{"name":"signature","type":"bytes"}],"name":"verifyClaimSignature","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
        {"inputs":[{"name":"claimId","type":"bytes32"}],"name":"isClaimUsed","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
        {"inputs":[],"name":"supplyInfo","outputs":[{"name":"total","type":"uint256"},{"name":"minted","type":"uint256"},{"name":"remaining","type":"uint256"}],"stateMutability":"view","type":"function"},
        {"inputs":[{"name":"tokenId","type":"uint256"}],"name":"uri","outputs":[{"name":"","type":"string"}],"stateMutability":"view","type":"function"},
        {"inputs":[{"name":"account","type":"address"},{"name":"id","type":"uint256"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
        {"anonymous":false,"inputs":[{"indexed":true,"name":"player","type":"address"},{"indexed":true,"name":"runeId","type":"uint256"},{"indexed":false,"name":"claimId","type":"bytes32"}],"name":"RuneClaimed","type":"event"}
    ],

    // ========== ABI - EmberItems (ERC1155 con Claim) ==========
    ITEMS_ABI: [
        {"inputs":[{"name":"claimId","type":"bytes32"},{"name":"signature","type":"bytes"}],"name":"claimItem","outputs":[{"name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
        {"inputs":[{"name":"player","type":"address"},{"name":"claimId","type":"bytes32"},{"name":"signature","type":"bytes"}],"name":"verifyClaimSignature","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
        {"inputs":[{"name":"claimId","type":"bytes32"}],"name":"isClaimUsed","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
        {"inputs":[],"name":"supplyInfo","outputs":[{"name":"total","type":"uint256"},{"name":"minted","type":"uint256"},{"name":"remaining","type":"uint256"}],"stateMutability":"view","type":"function"},
        {"inputs":[{"name":"tokenId","type":"uint256"}],"name":"uri","outputs":[{"name":"","type":"string"}],"stateMutability":"view","type":"function"},
        {"inputs":[{"name":"account","type":"address"},{"name":"id","type":"uint256"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
        {"anonymous":false,"inputs":[{"indexed":true,"name":"player","type":"address"},{"indexed":true,"name":"itemId","type":"uint256"},{"indexed":false,"name":"claimId","type":"bytes32"}],"name":"ItemClaimed","type":"event"}
    ]
};
