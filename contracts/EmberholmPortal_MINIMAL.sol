// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * @title EmberholmPortal - Phase 1 (Minimal)
 * @dev Ultra-lightweight NFT contract for Emberholm Portal game
 * @notice PHASE 1: Everything off-chain (guilds, missions, EMBER Points in backend)
 *         PHASE 2: Staking + $EMBER token integration (future upgrade)
 *
 * Current Features (Phase 1):
 * - NFT minting (owner and public)
 * - Basic queries (totalSupply, tokensOfOwner, etc.)
 * - Equipment slots (prepared for Phase 2 Items contract)
 * - Pausable for emergency stops
 * - ERC2981 royalties
 *
 * Future Upgrade (Phase 2):
 * - StakingRewards contract (separate - users pay minimal gas)
 * - EmberToken contract (ERC20 - $EMBER)
 * - PointsConverter contract (EMBER Points → $EMBER)
 *
 * Design Philosophy:
 * - Phase 1: ZERO gas for users (everything in backend)
 * - Phase 2: MINIMAL gas for users (stake/unstake/claim)
 * - Backend-first: Guilds, names, achievements, EMBER Points all off-chain
 *
 * Version: 4.0 (Minimal - Phase 1)
 * Network: Base Mainnet
 * Deployed: TBD
 */

// Interface for future Items contract (Phase 2)
interface IEmberholmItems {
    function balanceOf(address account, uint256 id) external view returns (uint256);
}

contract EmberholmPortal is ERC721, ERC2981, Ownable, Pausable {
    using Strings for uint256;

    // ========== STATE VARIABLES ==========

    uint256 private _nextTokenId;

    uint256 public constant MAX_SUPPLY = 35000;
    uint256 public mintPrice = 0.0011 ether;

    string private baseTokenURI = "https://emberholm-portal.onrender.com/api/metadata/";
    bool public mintOpen = true;

    // Items contract (Phase 2 - connected later)
    IEmberholmItems public itemsContract;

    // Equipment system (prepared for Phase 2 Items)
    mapping(uint256 => mapping(string => uint256)) public equippedItems;
    string[4] public equipmentSlots = ["weapon", "armor", "accessory", "trinket"];

    // ========== EVENTS ==========

    event MintPriceUpdated(uint256 newPrice);
    event BaseURIUpdated(string newBaseURI);
    event ItemsContractSet(address indexed itemsContract);
    event ItemEquipped(uint256 indexed tokenId, string slot, uint256 itemId);
    event ItemUnequipped(uint256 indexed tokenId, string slot, uint256 itemId);

    // ========== CONSTRUCTOR ==========

    constructor() ERC721("Emberholm Portal", "EMBERHOLM") Ownable(msg.sender) {
        _setDefaultRoyalty(msg.sender, 500); // 5% royalty
        _nextTokenId = 1;
    }

    // ========== MINT FUNCTIONS ==========

    /**
     * @dev Public mint function
     */
    function mint(uint256 quantity) external payable whenNotPaused {
        require(mintOpen, "Mint is closed");
        require(quantity > 0 && quantity <= 10, "Invalid quantity");
        require(_nextTokenId + quantity <= MAX_SUPPLY + 1, "Max supply reached");

        uint256 totalCost = mintPrice * quantity;
        require(msg.value >= totalCost, "Not enough ETH");

        for (uint256 i = 0; i < quantity; i++) {
            _safeMint(msg.sender, _nextTokenId);
            _nextTokenId++;
        }

        // Refund excess
        if (msg.value > totalCost) {
            payable(msg.sender).transfer(msg.value - totalCost);
        }
    }

    /**
     * @dev Owner mint (airdrops, team, etc)
     */
    function ownerMint(address to, uint256 quantity) external onlyOwner {
        require(to != address(0), "Invalid address");
        require(_nextTokenId + quantity <= MAX_SUPPLY + 1, "Max supply reached");

        for (uint256 i = 0; i < quantity; i++) {
            _safeMint(to, _nextTokenId);
            _nextTokenId++;
        }
    }

    // ========== QUERY FUNCTIONS ==========

    /**
     * @dev Total minted
     */
    function totalMinted() public view returns (uint256) {
        return _nextTokenId - 1;
    }

    /**
     * @dev Total supply (alias)
     */
    function totalSupply() external view returns (uint256) {
        return totalMinted();
    }

    /**
     * @dev Max supply
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
     * @dev Check if token exists
     */
    function exists(uint256 tokenId) external view returns (bool) {
        return _ownerOf(tokenId) != address(0);
    }

    // ========== EQUIPMENT SYSTEM (Phase 2) ==========

    /**
     * @dev Set Items contract (Phase 2 - can only be set once)
     */
    function setItemsContract(address _itemsContract) external onlyOwner {
        require(address(itemsContract) == address(0), "Already set");
        require(_itemsContract != address(0), "Invalid address");
        itemsContract = IEmberholmItems(_itemsContract);
        emit ItemsContractSet(_itemsContract);
    }

    /**
     * @dev Equip item (Phase 2 - requires Items contract)
     */
    function equipItem(uint256 tokenId, string calldata slot, uint256 itemId) external whenNotPaused {
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
     * @dev Unequip item (Phase 2)
     */
    function unequipItem(uint256 tokenId, string calldata slot) external whenNotPaused {
        require(ownerOf(tokenId) == msg.sender, "Not owner");

        uint256 itemId = equippedItems[tokenId][slot];
        require(itemId != 0, "No item equipped");

        equippedItems[tokenId][slot] = 0;
        emit ItemUnequipped(tokenId, slot, itemId);
    }

    /**
     * @dev Get equipped item in slot
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
        uint256 accessory,
        uint256 trinket
    ) {
        weapon = equippedItems[tokenId]["weapon"];
        armor = equippedItems[tokenId]["armor"];
        accessory = equippedItems[tokenId]["accessory"];
        trinket = equippedItems[tokenId]["trinket"];
    }

    // ========== ADMIN FUNCTIONS ==========

    function setMintOpen(bool _open) external onlyOwner {
        mintOpen = _open;
    }

    function setMintPrice(uint256 _newPriceWei) external onlyOwner {
        mintPrice = _newPriceWei;
        emit MintPriceUpdated(_newPriceWei);
    }

    function setBaseURI(string calldata _newBase) external onlyOwner {
        baseTokenURI = _newBase;
        emit BaseURIUpdated(_newBase);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function withdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds");

        (bool success, ) = payable(msg.sender).call{value: balance}("");
        require(success, "Transfer failed");
    }

    function _baseURI() internal view override returns (string memory) {
        return baseTokenURI;
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        _requireOwned(tokenId);
        return string(abi.encodePacked(_baseURI(), tokenId.toString()));
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    /**
     * @dev Override _update to support pausable
     */
    function _update(address to, uint256 tokenId, address auth)
        internal
        override
        whenNotPaused
        returns (address)
    {
        return super._update(to, tokenId, auth);
    }
}
