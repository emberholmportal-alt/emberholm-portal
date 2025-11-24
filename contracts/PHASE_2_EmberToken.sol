// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title EmberToken - $EMBER
 * @dev ERC20 token for Emberholm Portal game economy
 * @notice PHASE 2 contract - Deploy when ready for tokenomics
 *
 * Features:
 * - Standard ERC20 functionality
 * - Burnable (users can burn their tokens)
 * - Mintable by authorized contracts only
 * - Pausable for emergency stops
 *
 * Minters:
 * - StakingRewards contract (mints rewards for completed missions)
 * - PointsConverter contract (mints when converting EMBER Points)
 * - Owner (for initial liquidity, airdrops, etc.)
 *
 * Tokenomics:
 * - Max Supply: TBD (set at deployment or leave uncapped)
 * - Initial Distribution: TBD
 * - Mission Rewards: 50-500 $EMBER per mission (depends on difficulty)
 * - Staking Requirements: TBD
 *
 * Version: 1.0 (Phase 2)
 * Network: Base Mainnet
 * Deploy: When launching tokenomics
 */

contract EmberToken is ERC20, ERC20Burnable, Ownable, Pausable {

    // Max supply (0 = uncapped, set value to cap)
    uint256 public maxSupply;

    // Authorized minters (StakingRewards, PointsConverter contracts)
    mapping(address => bool) public minters;

    // ========== EVENTS ==========

    event MinterAdded(address indexed minter);
    event MinterRemoved(address indexed minter);
    event MaxSupplySet(uint256 maxSupply);

    // ========== CONSTRUCTOR ==========

    /**
     * @dev Initialize token
     * @param _maxSupply Max supply (0 for uncapped)
     * @param initialMint Amount to mint to deployer for initial liquidity
     */
    constructor(
        uint256 _maxSupply,
        uint256 initialMint
    ) ERC20("Ember", "EMBER") Ownable(msg.sender) {
        maxSupply = _maxSupply;

        if (initialMint > 0) {
            if (maxSupply > 0) {
                require(initialMint <= maxSupply, "Initial mint exceeds max supply");
            }
            _mint(msg.sender, initialMint);
        }

        emit MaxSupplySet(_maxSupply);
    }

    // ========== MINTING ==========

    /**
     * @dev Mint tokens (only authorized minters)
     * @param to Recipient address
     * @param amount Amount to mint
     */
    function mint(address to, uint256 amount) external whenNotPaused {
        require(minters[msg.sender] || msg.sender == owner(), "Not authorized to mint");

        // Check max supply if capped
        if (maxSupply > 0) {
            require(totalSupply() + amount <= maxSupply, "Max supply exceeded");
        }

        _mint(to, amount);
    }

    // ========== ADMIN FUNCTIONS ==========

    /**
     * @dev Add authorized minter (StakingRewards, PointsConverter contracts)
     */
    function addMinter(address minter) external onlyOwner {
        require(minter != address(0), "Invalid address");
        require(!minters[minter], "Already minter");

        minters[minter] = true;
        emit MinterAdded(minter);
    }

    /**
     * @dev Remove minter
     */
    function removeMinter(address minter) external onlyOwner {
        require(minters[minter], "Not a minter");

        minters[minter] = false;
        emit MinterRemoved(minter);
    }

    /**
     * @dev Set max supply (can only decrease, not increase)
     */
    function setMaxSupply(uint256 _maxSupply) external onlyOwner {
        require(_maxSupply == 0 || _maxSupply >= totalSupply(), "Cannot set below current supply");
        if (maxSupply > 0) {
            require(_maxSupply <= maxSupply, "Cannot increase max supply");
        }

        maxSupply = _maxSupply;
        emit MaxSupplySet(_maxSupply);
    }

    /**
     * @dev Pause transfers (emergency)
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @dev Unpause transfers
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    // ========== OVERRIDES ==========

    /**
     * @dev Override transfer to support pausable
     */
    function _update(address from, address to, uint256 value)
        internal
        override
        whenNotPaused
    {
        super._update(from, to, value);
    }
}
