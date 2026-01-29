/**
 * EMBERHOLM MINI APP - Contract Configuration
 * Base Mainnet Deployment - Same contracts as portal web
 */

export const CONTRACT_CONFIG = {
  // ========== CONTRACT ADDRESSES ==========
  CONTRACTS: {
    EmberholmPortal: '0x7AB2cf80FbfB8c89868b3dFa053729ecC86E39b3',
    EmberToken: '0xbA7723fBfb44C7712C0B78108ad873DcFd5Dd73b',
    AshToken: '0xD4eef3eadb1Cf1B2905AA4Cd1022b8cCCC739DAb',
    EmberItems: '0xCE71702CE99Bc927216e64d57e4BD19254Ac28bA',
    EmberRunes: '0xDa2D1085053c3700645a13498293D17c1cc3f595',
    EmberLands: '0x75837A89359654A3c17b92704cF2255Dd42b985b',
    EmberTrophies: '0x99bB074468DF7acED00a7a4960c52c4e22543ab8',
  },

  // ========== NETWORK CONFIGURATION ==========
  CHAIN_ID: 8453,
  CHAIN_ID_HEX: '0x2105',
  NETWORK_NAME: 'Base',
  RPC_URL: 'https://mainnet.base.org',
  BLOCK_EXPLORER: 'https://basescan.org',

  // ========== IPFS METADATA ==========
  IPFS_METADATA_BASE: 'https://ipfs.io/ipfs/bafybeidd7wtx7izjgsociwe6ynjz6c3xslqmcedr7z4wojcxs4yd5u7pim/',
  IPFS_IMAGES_BASE: 'https://ipfs.io/ipfs/bafybeicnvc3zagcncablcovpxgt5mtuotowvuqom6kby754ve2gwbzdvkm/',

  // ========== MINT CONFIGURATION ==========
  MINT_PRICE_ETH: 0.0011,
  MAX_SUPPLY: 35000,

  // ========== ABIs ==========
  ABI: {
    EmberholmPortal: [
      'function totalSupply() view returns (uint256)',
      'function maxSupply() pure returns (uint256)',
      'function totalMinted() view returns (uint256)',
      'function tokensOfOwner(address owner) view returns (uint256[])',
      'function tokenURI(uint256 tokenId) view returns (string)',
      'function balanceOf(address owner) view returns (uint256)',
      'function ownerOf(uint256 tokenId) view returns (address)',
      'function mint(uint256 quantity) payable',
      'function mintPrice() view returns (uint256)',
      'function mintOpen() view returns (bool)',
      'function getFreeMints(address wallet) view returns (uint256)',
      'event Transfer(address indexed from, address indexed to, uint256 indexed tokenId)',
    ],
    EmberToken: [
      'function balanceOf(address account) view returns (uint256)',
      'function approve(address spender, uint256 amount) returns (bool)',
      'function allowance(address owner, address spender) view returns (uint256)',
      'function convertToAsh(uint256 emberAmount) external',
    ],
    AshToken: [
      'function balanceOf(address account) view returns (uint256)',
    ],
    EmberItems: [
      'function claimItem(bytes32 claimId, bytes signature) external',
      'function balanceOf(address owner) view returns (uint256)',
      'function ownerOf(uint256 tokenId) view returns (address)',
      'function tokensOfOwner(address owner) view returns (uint256[])',
      'function tokenURI(uint256 tokenId) view returns (string)',
    ],
    EmberRunes: [
      'function claimRune(bytes32 claimId, bytes signature) external',
      'function balanceOf(address owner) view returns (uint256)',
      'function ownerOf(uint256 tokenId) view returns (address)',
      'function tokensOfOwner(address owner) view returns (uint256[])',
      'function tokenURI(uint256 tokenId) view returns (string)',
    ],
  },

  // ========== DROP RATES ==========
  DROP_RATES: {
    EASY: { item: 5, rune: 1 },
    MEDIUM: { item: 10, rune: 3 },
    HARD: { item: 20, rune: 8 },
    PARTY: { item: 25, rune: 12 },
  },
} as const;

export default CONTRACT_CONFIG;
