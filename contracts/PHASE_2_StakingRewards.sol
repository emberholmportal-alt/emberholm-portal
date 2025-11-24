// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title StakingRewards - Phase 2
 * @dev Staking contract for Emberholm Portal NFTs with $EMBER rewards
 * @notice Users stake NFTs to participate in missions and earn $EMBER tokens
 *
 * Flow:
 * 1. User calls stakeNFT(tokenId) - Pays minimal gas (~$0.01)
 * 2. NFT locked in this contract (cannot transfer while staked)
 * 3. Backend tracks mission completion off-chain
 * 4. Backend calls completeMission(tokenId, reward) - Backend pays gas
 * 5. User calls claimRewards() - Pays minimal gas (~$0.005) - Receives $EMBER
 *
 * Security:
 * - Only NFT owner can stake/unstake
 * - Backend (missionOperator) can complete missions
 * - 2-hour cooldown between unstakes (prevents abuse)
 * - ReentrancyGuard on all external functions
 *
 * Version: 1.0 (Phase 2)
 * Network: Base Mainnet
 * Deploy: After EmberToken and EmberholmPortal
 */

interface IEmberholmPortal {
    function ownerOf(uint256 tokenId) external view returns (address);
    function transferFrom(address from, address to, uint256 tokenId) external;
}

interface IEmberToken {
    function mint(address to, uint256 amount) external;
}

contract StakingRewards is Ownable, Pausable, ReentrancyGuard {

    // ========== STATE VARIABLES ==========

    IEmberholmPortal public immutable nftContract;
    IEmberToken public immutable emberToken;

    address public missionOperator;  // Backend wallet that completes missions

    uint256 public constant UNSTAKE_COOLDOWN = 2 hours;

    // Staking data
    struct StakeInfo {
        address owner;
        uint256 stakedAt;
        uint256 lastUnstakeTime;
        uint256 pendingRewards;  // Accumulated $EMBER from missions
    }

    mapping(uint256 => StakeInfo) public stakes;

    // ========== EVENTS ==========

    event NFTStaked(uint256 indexed tokenId, address indexed owner, uint256 timestamp);
    event NFTUnstaked(uint256 indexed tokenId, address indexed owner, uint256 timestamp);
    event MissionCompleted(uint256 indexed tokenId, uint256 reward, bool success);
    event RewardsClaimed(uint256 indexed tokenId, address indexed owner, uint256 amount);
    event MissionOperatorSet(address indexed operator);

    // ========== CONSTRUCTOR ==========

    constructor(
        address _nftContract,
        address _emberToken,
        address _missionOperator
    ) Ownable(msg.sender) {
        require(_nftContract != address(0), "Invalid NFT contract");
        require(_emberToken != address(0), "Invalid token contract");
        require(_missionOperator != address(0), "Invalid operator");

        nftContract = IEmberholmPortal(_nftContract);
        emberToken = IEmberToken(_emberToken);
        missionOperator = _missionOperator;
    }

    // ========== STAKING FUNCTIONS ==========

    /**
     * @dev Stake NFT (user pays minimal gas ~$0.01)
     * @param tokenId NFT to stake
     */
    function stakeNFT(uint256 tokenId) external nonReentrant whenNotPaused {
        address owner = nftContract.ownerOf(tokenId);
        require(owner == msg.sender, "Not NFT owner");
        require(stakes[tokenId].owner == address(0), "Already staked");

        // Transfer NFT to this contract
        nftContract.transferFrom(msg.sender, address(this), tokenId);

        // Record stake
        stakes[tokenId] = StakeInfo({
            owner: msg.sender,
            stakedAt: block.timestamp,
            lastUnstakeTime: 0,
            pendingRewards: 0
        });

        emit NFTStaked(tokenId, msg.sender, block.timestamp);
    }

    /**
     * @dev Unstake NFT (user pays minimal gas ~$0.007)
     * @param tokenId NFT to unstake
     */
    function unstakeNFT(uint256 tokenId) external nonReentrant whenNotPaused {
        StakeInfo storage stake = stakes[tokenId];
        require(stake.owner == msg.sender, "Not stake owner");

        // Enforce cooldown (prevents rapid stake/unstake abuse)
        require(
            block.timestamp >= stake.lastUnstakeTime + UNSTAKE_COOLDOWN,
            "Cooldown not elapsed"
        );

        // Transfer NFT back to owner
        nftContract.transferFrom(address(this), msg.sender, tokenId);

        // Update last unstake time
        stake.lastUnstakeTime = block.timestamp;

        // Clear stake (but keep pending rewards)
        uint256 pendingRewards = stake.pendingRewards;
        delete stakes[tokenId];

        // Restore pending rewards if any
        if (pendingRewards > 0) {
            stakes[tokenId].pendingRewards = pendingRewards;
            stakes[tokenId].owner = msg.sender;  // Keep owner for claiming
        }

        emit NFTUnstaked(tokenId, msg.sender, block.timestamp);
    }

    // ========== MISSION FUNCTIONS (Backend) ==========

    /**
     * @dev Complete mission and assign rewards (backend pays gas)
     * @param tokenId NFT that completed mission
     * @param rewardAmount $EMBER reward (in wei, e.g., 50 * 10**18 for 50 EMBER)
     * @param success True if mission succeeded, false if failed
     */
    function completeMission(
        uint256 tokenId,
        uint256 rewardAmount,
        bool success
    ) external nonReentrant {
        require(msg.sender == missionOperator, "Not authorized");

        StakeInfo storage stake = stakes[tokenId];
        require(stake.owner != address(0), "NFT not staked");

        if (success && rewardAmount > 0) {
            stake.pendingRewards += rewardAmount;
        }

        emit MissionCompleted(tokenId, rewardAmount, success);
    }

    // ========== REWARDS FUNCTIONS (User) ==========

    /**
     * @dev Claim accumulated rewards (user pays minimal gas ~$0.005)
     * @param tokenId NFT to claim rewards for
     */
    function claimRewards(uint256 tokenId) external nonReentrant whenNotPaused {
        StakeInfo storage stake = stakes[tokenId];
        require(stake.owner == msg.sender, "Not stake owner");
        require(stake.pendingRewards > 0, "No rewards to claim");

        uint256 rewards = stake.pendingRewards;
        stake.pendingRewards = 0;

        // Mint $EMBER tokens to user
        emberToken.mint(msg.sender, rewards);

        emit RewardsClaimed(tokenId, msg.sender, rewards);
    }

    /**
     * @dev Claim rewards for multiple NFTs at once (batch claim)
     * @param tokenIds Array of NFT IDs
     */
    function claimRewardsBatch(uint256[] calldata tokenIds) external nonReentrant whenNotPaused {
        uint256 totalRewards = 0;

        for (uint256 i = 0; i < tokenIds.length; i++) {
            uint256 tokenId = tokenIds[i];
            StakeInfo storage stake = stakes[tokenId];

            require(stake.owner == msg.sender, "Not stake owner");

            if (stake.pendingRewards > 0) {
                totalRewards += stake.pendingRewards;
                stake.pendingRewards = 0;

                emit RewardsClaimed(tokenId, msg.sender, stake.pendingRewards);
            }
        }

        require(totalRewards > 0, "No rewards to claim");

        // Mint total $EMBER tokens to user
        emberToken.mint(msg.sender, totalRewards);
    }

    // ========== VIEW FUNCTIONS ==========

    /**
     * @dev Get stake info for NFT
     */
    function getStakeInfo(uint256 tokenId) external view returns (StakeInfo memory) {
        return stakes[tokenId];
    }

    /**
     * @dev Check if NFT is staked
     */
    function isStaked(uint256 tokenId) external view returns (bool) {
        return stakes[tokenId].owner != address(0);
    }

    /**
     * @dev Get pending rewards for NFT
     */
    function getPendingRewards(uint256 tokenId) external view returns (uint256) {
        return stakes[tokenId].pendingRewards;
    }

    // ========== ADMIN FUNCTIONS ==========

    /**
     * @dev Set mission operator (backend wallet)
     */
    function setMissionOperator(address _operator) external onlyOwner {
        require(_operator != address(0), "Invalid address");
        missionOperator = _operator;
        emit MissionOperatorSet(_operator);
    }

    /**
     * @dev Pause staking/unstaking (emergency)
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @dev Unpause
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @dev Emergency unstake (only owner, for stuck NFTs)
     */
    function emergencyUnstake(uint256 tokenId) external onlyOwner {
        StakeInfo storage stake = stakes[tokenId];
        require(stake.owner != address(0), "Not staked");

        address owner = stake.owner;
        delete stakes[tokenId];

        nftContract.transferFrom(address(this), owner, tokenId);

        emit NFTUnstaked(tokenId, owner, block.timestamp);
    }
}
