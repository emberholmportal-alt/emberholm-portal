// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * @title EmberholmPortal
 * @dev Ultra-lightweight NFT contract for Emberholm Portal game
 * @notice MINIMAL on-chain design: Only ownership, staking, and equipment. Everything else in backend/metadata.
 *
 * Features:
 * - TIER 1: Basic queries (totalMinted, tokensOfOwner, getTokenInfo)
 * - TIER 2: Batch operations, staking system, primary token selection
 * - TIER 3: Equipment slots (prepared for future Items contract)
 *
 * Design Philosophy (Backend-First):
 * - Guild membership: Backend + Metadata (FREE, flexible)
 * - Names: Backend + Metadata (FREE, fixed)
 * - Achievements: Backend + Metadata (FREE, appears in OpenSea)
 * - Guild leadership: Backend database (FREE, no gas)
 * - Staking: On-chain (CRITICAL - prevents transfers during missions)
 * - Equipment: On-chain (future Items contract integration)
 *
 * Version: 2.0 (Ultra-Optimized - Backend First)
 * Network: Base Sepolia (testnet) → Base (mainnet ready)
 */

// Interface for future Items contract
interface IEmberholmItems {
    function balanceOf(address account, uint256 id) external view returns (uint256);

    struct ItemStats {
        uint16 attackBonus;
        uint16 defenseBonus;
        uint16 speedBonus;
        uint16 auraBonus;
        uint8 rarity;
    }

    function itemStats(uint256 itemId) external view returns (ItemStats memory);
}

contract EmberholmPortal is ERC721, ERC2981, Ownable {
    using Strings for uint256;

    // ========== STATE VARIABLES ==========

    uint256 private _nextTokenId;

    uint256 public constant MAX_SUPPLY = 35000;
    uint256 public mintPrice = 0.0011 ether;

    string private baseTokenURI = "https://emberholm-portal.onrender.com/api/metadata/";
    bool public mintOpen = true;

    address public treasury;
    address public missionManager; // Backend wallet for game operations

    // Items contract (connected later)
    IEmberholmItems public itemsContract;

    // ========== STRUCTS ==========

    struct TokenInfo {
        uint256 tokenId;
        address owner;
        bool isStaked;
        // Note: guild, name, and achievements are in metadata (backend manages)
    }

    struct WalletStats {
        uint256 totalTokens;
        uint256 stakedCount;
        // Note: guildsRepresented removed - calculated from metadata by backend
    }

    // ========== STORAGE MAPPINGS ==========

    // Staking system (CRITICAL on-chain - prevents transfers during missions)
    mapping(uint256 => bool) public stakedTokens;
    mapping(uint256 => uint256) public stakeTimestamp;

    // Primary token selection (user preference for TOP EMISSARY)
    mapping(address => uint256) public primaryToken;

    // Custom metadata
    mapping(uint256 => string) public tokenImageOverride;
    mapping(uint256 => mapping(string => string)) public tokenAttributes;

    // Equipment system (prepared for items)
    mapping(uint256 => mapping(string => uint256)) public equippedItems;
    string[4] public equipmentSlots = ["weapon", "armor", "boots", "accessory"];

    // ========== EVENTS ==========

    event TokenStaked(uint256 indexed tokenId, address indexed owner, uint256 timestamp);
    event TokenUnstaked(uint256 indexed tokenId, address indexed owner, uint256 timestamp);
    event PrimaryTokenSet(address indexed owner, uint256 indexed tokenId);
    event TokenImageUpdated(uint256 indexed tokenId, string imageURI);
    event TokenAttributeSet(uint256 indexed tokenId, string key, string value);
    event ItemEquipped(uint256 indexed tokenId, string slot, uint256 itemId);
    event ItemUnequipped(uint256 indexed tokenId, string slot, uint256 itemId);
    event ItemsContractSet(address indexed itemsContract);
    event MissionManagerSet(address indexed missionManager);

    // ========== CONSTRUCTOR ==========

    constructor(address _treasury) ERC721("Emberholm Portal", "EMBERHOLM") Ownable(msg.sender) {
        require(_treasury != address(0), "Invalid treasury");
        treasury = _treasury;
        _setDefaultRoyalty(_treasury, 500); // 5% royalty
        _nextTokenId = 1; // Start from token ID 1
    }

    // ========== MINT FUNCTIONS ==========

    /**
     * @dev Public mint function
     */
    function mint(uint256 quantity) external payable {
        require(mintOpen, "Mint is closed");
        require(quantity > 0 && quantity <= 10, "Invalid quantity");
        require(_nextTokenId + quantity <= MAX_SUPPLY + 1, "Max supply reached");

        uint256 totalCost = mintPrice * quantity;
        require(msg.value >= totalCost, "Not enough ETH");

        for (uint256 i = 0; i < quantity; i++) {
            _safeMint(msg.sender, _nextTokenId);
            _nextTokenId++;
        }

        // Refund excess payment
        if (msg.value > totalCost) {
            payable(msg.sender).transfer(msg.value - totalCost);
        }
    }

    /**
     * @dev Owner mint (for airdrops, team, etc)
     */
    function ownerMint(address to, uint256 quantity) external onlyOwner {
        require(to != address(0), "Invalid address");
        require(_nextTokenId + quantity <= MAX_SUPPLY + 1, "Max supply reached");

        for (uint256 i = 0; i < quantity; i++) {
            _safeMint(to, _nextTokenId);
            _nextTokenId++;
        }
    }

    // ========== TIER 1: BASIC QUERY FUNCTIONS ==========

    /**
     * @dev Returns total number of tokens minted
     */
    function totalMinted() public view returns (uint256) {
        return _nextTokenId - 1;
    }

    /**
     * @dev Alias for compatibility
     */
    function totalSupply() external view returns (uint256) {
        return totalMinted();
    }

    /**
     * @dev Returns max supply constant
     */
    function maxSupply() external pure returns (uint256) {
        return MAX_SUPPLY;
    }

    /**
     * @dev Returns all token IDs owned by an address
     */
    function tokensOfOwner(address owner) public view returns (uint256[] memory) {
        uint256 balance = balanceOf(owner);
        if (balance == 0) {
            return new uint256[](0);
        }

        uint256[] memory tokens = new uint256[](balance);
        uint256 index = 0;
        uint256 supply = totalMinted();

        for (uint256 tokenId = 1; tokenId <= supply && index < balance; tokenId++) {
            if (_ownerOf(tokenId) == owner) {
                tokens[index] = tokenId;
                index++;
            }
        }

        return tokens;
    }

    /**
     * @dev Get on-chain info for a token
     * Note: Guild, name, and achievements are in metadata (backend manages)
     */
    function getTokenInfo(uint256 tokenId) public view returns (TokenInfo memory) {
        require(_ownerOf(tokenId) != address(0), "Token doesn't exist");

        address owner = ownerOf(tokenId);

        return TokenInfo({
            tokenId: tokenId,
            owner: owner,
            isStaked: stakedTokens[tokenId]
        });
    }

    // ========== TIER 2: BATCH OPERATIONS ==========

    /**
     * @dev Get info for multiple tokens at once (gas efficient)
     */
    function batchGetTokenInfo(uint256[] calldata tokenIds) external view returns (TokenInfo[] memory) {
        TokenInfo[] memory infos = new TokenInfo[](tokenIds.length);

        for (uint256 i = 0; i < tokenIds.length; i++) {
            if (_ownerOf(tokenIds[i]) != address(0)) {
                infos[i] = getTokenInfo(tokenIds[i]);
            }
            // If token doesn't exist, struct will be empty (default values)
        }

        return infos;
    }

    /**
     * @dev Get complete wallet profile in ONE call
     */
    function getWalletProfile(address owner) external view returns (
        uint256[] memory tokenIds,
        TokenInfo[] memory tokens,
        WalletStats memory stats
    ) {
        tokenIds = tokensOfOwner(owner);

        tokens = new TokenInfo[](tokenIds.length);
        for (uint256 i = 0; i < tokenIds.length; i++) {
            tokens[i] = getTokenInfo(tokenIds[i]);
        }

        uint256 stakedCount = 0;
        for (uint256 i = 0; i < tokens.length; i++) {
            if (tokens[i].isStaked) stakedCount++;
        }

        stats = WalletStats({
            totalTokens: tokenIds.length,
            stakedCount: stakedCount
        });
    }

    // ========== TIER 2: STAKING SYSTEM ==========

    /**
     * @dev Stake token (locks it during missions)
     */
    function stakeToken(uint256 tokenId) external {
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        require(!stakedTokens[tokenId], "Already staked");

        stakedTokens[tokenId] = true;
        stakeTimestamp[tokenId] = block.timestamp;

        emit TokenStaked(tokenId, msg.sender, block.timestamp);
    }

    /**
     * @dev Unstake token (only owner or mission manager)
     */
    function unstakeToken(uint256 tokenId) external {
        address owner = ownerOf(tokenId);
        require(
            msg.sender == owner || msg.sender == missionManager,
            "Not authorized"
        );
        require(stakedTokens[tokenId], "Not staked");

        stakedTokens[tokenId] = false;

        emit TokenUnstaked(tokenId, owner, block.timestamp);
    }

    /**
     * @dev Override _update to prevent transfer of staked tokens
     */
    function _update(address to, uint256 tokenId, address auth)
        internal
        override
        returns (address)
    {
        require(!stakedTokens[tokenId], "Token is staked");
        return super._update(to, tokenId, auth);
    }

    // ========== TIER 2: PRIMARY TOKEN ==========

    /**
     * @dev Set primary token (for TOP EMISSARY display)
     */
    function setPrimaryToken(uint256 tokenId) external {
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        primaryToken[msg.sender] = tokenId;

        emit PrimaryTokenSet(msg.sender, tokenId);
    }

    /**
     * @dev Get primary token info (auto-selects first token if not set)
     */
    function getPrimaryTokenInfo(address owner) external view returns (TokenInfo memory) {
        uint256 tokenId = primaryToken[owner];

        // If no primary token set or user doesn't own it anymore
        if (tokenId == 0 || _ownerOf(tokenId) != owner) {
            uint256[] memory tokens = tokensOfOwner(owner);
            require(tokens.length > 0, "No tokens owned");
            tokenId = tokens[0];
        }

        return getTokenInfo(tokenId);
    }

    // ========== TIER 3: CUSTOM METADATA ==========
    // Note: Achievements and guild leadership moved to backend (FREE, appears in OpenSea metadata)

    /**
     * @dev Set custom image for token
     */
    function setTokenImage(uint256 tokenId, string calldata imageURI) external {
        require(
            ownerOf(tokenId) == msg.sender || msg.sender == owner(),
            "Not authorized"
        );
        tokenImageOverride[tokenId] = imageURI;
        emit TokenImageUpdated(tokenId, imageURI);
    }

    /**
     * @dev Set custom attribute (flexible key-value storage)
     */
    function setTokenAttribute(uint256 tokenId, string calldata key, string calldata value) external {
        require(
            ownerOf(tokenId) == msg.sender || msg.sender == missionManager,
            "Not authorized"
        );
        tokenAttributes[tokenId][key] = value;
        emit TokenAttributeSet(tokenId, key, value);
    }

    /**
     * @dev Override tokenURI to support custom images
     */
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        _requireOwned(tokenId);

        // If custom image set, use it
        if (bytes(tokenImageOverride[tokenId]).length > 0) {
            return tokenImageOverride[tokenId];
        }

        // Otherwise use baseURI + tokenId
        return string(abi.encodePacked(_baseURI(), tokenId.toString()));
    }

    // ========== EQUIPMENT SYSTEM (PREPARED FOR ITEMS) ==========

    /**
     * @dev Connect Items contract (can only be set once)
     */
    function setItemsContract(address _itemsContract) external onlyOwner {
        require(address(itemsContract) == address(0), "Already set");
        require(_itemsContract != address(0), "Invalid address");
        itemsContract = IEmberholmItems(_itemsContract);
        emit ItemsContractSet(_itemsContract);
    }

    /**
     * @dev Equip item to a slot
     */
    function equipItem(uint256 tokenId, string calldata slot, uint256 itemId) external {
        require(address(itemsContract) != address(0), "Items contract not set");
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        require(itemsContract.balanceOf(msg.sender, itemId) > 0, "Don't own item");

        // Validate slot
        bool validSlot = false;
        for (uint i = 0; i < equipmentSlots.length; i++) {
            if (keccak256(bytes(equipmentSlots[i])) == keccak256(bytes(slot))) {
                validSlot = true;
                break;
            }
        }
        require(validSlot, "Invalid slot");

        equippedItems[tokenId][slot] = itemId;
        emit ItemEquipped(tokenId, slot, itemId);
    }

    /**
     * @dev Unequip item from slot
     */
    function unequipItem(uint256 tokenId, string calldata slot) external {
        require(ownerOf(tokenId) == msg.sender, "Not owner");

        uint256 itemId = equippedItems[tokenId][slot];
        require(itemId != 0, "No item equipped");

        equippedItems[tokenId][slot] = 0;
        emit ItemUnequipped(tokenId, slot, itemId);
    }

    /**
     * @dev Get item equipped in specific slot
     */
    function getEquippedItem(uint256 tokenId, string calldata slot) external view returns (uint256) {
        return equippedItems[tokenId][slot];
    }

    /**
     * @dev Get all equipped items
     */
    function getEquippedItems(uint256 tokenId) external view returns (
        uint256 weapon,
        uint256 armor,
        uint256 boots,
        uint256 accessory
    ) {
        weapon = equippedItems[tokenId]["weapon"];
        armor = equippedItems[tokenId]["armor"];
        boots = equippedItems[tokenId]["boots"];
        accessory = equippedItems[tokenId]["accessory"];
    }

    /**
     * @dev Calculate total stats with item bonuses
     */
    function getTotalStats(uint256 tokenId) external view returns (
        uint16 totalAttack,
        uint16 totalDefense,
        uint16 totalSpeed,
        uint16 totalAura
    ) {
        // If no items contract, return 0
        if (address(itemsContract) == address(0)) {
            return (0, 0, 0, 0);
        }

        // Sum bonuses from equipped items
        for (uint i = 0; i < equipmentSlots.length; i++) {
            uint256 itemId = equippedItems[tokenId][equipmentSlots[i]];
            if (itemId != 0) {
                IEmberholmItems.ItemStats memory stats = itemsContract.itemStats(itemId);
                totalAttack += stats.attackBonus;
                totalDefense += stats.defenseBonus;
                totalSpeed += stats.speedBonus;
                totalAura += stats.auraBonus;
            }
        }
    }

    // ========== ADMIN FUNCTIONS ==========

    function setMintOpen(bool _open) external onlyOwner {
        mintOpen = _open;
    }

    function setMintPrice(uint256 _newPriceWei) external onlyOwner {
        mintPrice = _newPriceWei;
    }

    function setBaseURI(string calldata _newBase) external onlyOwner {
        baseTokenURI = _newBase;
    }

    function setTreasury(address _newTreasury) external onlyOwner {
        require(_newTreasury != address(0), "Invalid address");
        treasury = _newTreasury;
        _setDefaultRoyalty(_newTreasury, 500);
    }

    function setMissionManager(address _missionManager) external onlyOwner {
        missionManager = _missionManager;
        emit MissionManagerSet(_missionManager);
    }

    function withdraw() external onlyOwner {
        payable(treasury).transfer(address(this).balance);
    }

    function _baseURI() internal view override returns (string memory) {
        return baseTokenURI;
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
