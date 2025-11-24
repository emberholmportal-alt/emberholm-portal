// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

/**
 * @title PointsConverter - Phase 1 → Phase 2 Migration
 * @dev Converts off-chain EMBER Points to on-chain $EMBER tokens
 * @notice Allows users to claim $EMBER based on their historical EMBER Points
 *
 * How it works:
 * 1. Backend signs a message: "Convert {amount} EMBER Points for {wallet}"
 * 2. User calls convertPoints(amount, signature)
 * 3. Contract verifies signature is from authorized signer (backend)
 * 4. Contract mints {amount} $EMBER tokens to user
 * 5. Backend marks points as "claimed" in database
 *
 * Security:
 * - Signature-based (prevents unauthorized conversions)
 * - One-time use (prevents replay attacks via nonces)
 * - Rate limiting (prevents abuse)
 * - Pausable (emergency stop)
 *
 * Conversion Rate:
 * - Default: 1 EMBER Point = 1 $EMBER
 * - Adjustable by owner (can give bonuses, e.g., 1:1.5 for early adopters)
 *
 * Version: 1.0 (Phase 2)
 * Network: Base Mainnet
 * Deploy: After EmberToken
 */

interface IEmberToken {
    function mint(address to, uint256 amount) external;
}

contract PointsConverter is Ownable, Pausable, ReentrancyGuard {
    using ECDSA for bytes32;
    using MessageHashUtils for bytes32;

    // ========== STATE VARIABLES ==========

    IEmberToken public immutable emberToken;

    address public authorizedSigner;  // Backend wallet that signs conversion messages

    // Conversion rate (in basis points, 10000 = 1:1 ratio)
    // Example: 15000 = 1.5x bonus (1 point = 1.5 tokens)
    uint256 public conversionRate = 10000;

    // Nonces to prevent replay attacks
    mapping(address => uint256) public nonces;

    // Total converted per user (for analytics)
    mapping(address => uint256) public totalConverted;

    // Global stats
    uint256 public totalPointsConverted;
    uint256 public totalTokensMinted;

    // Rate limiting (max per transaction to prevent abuse)
    uint256 public maxConversionPerTx = 100000 * 10**18;  // 100k EMBER max

    // ========== EVENTS ==========

    event PointsConverted(
        address indexed user,
        uint256 pointsAmount,
        uint256 tokensAmount,
        uint256 nonce
    );
    event AuthorizedSignerSet(address indexed signer);
    event ConversionRateSet(uint256 newRate);
    event MaxConversionSet(uint256 newMax);

    // ========== CONSTRUCTOR ==========

    constructor(
        address _emberToken,
        address _authorizedSigner
    ) Ownable(msg.sender) {
        require(_emberToken != address(0), "Invalid token");
        require(_authorizedSigner != address(0), "Invalid signer");

        emberToken = IEmberToken(_emberToken);
        authorizedSigner = _authorizedSigner;
    }

    // ========== CONVERSION FUNCTIONS ==========

    /**
     * @dev Convert EMBER Points to $EMBER tokens
     * @param pointsAmount Amount of points to convert
     * @param signature Backend signature authorizing conversion
     *
     * Message format: "Convert {pointsAmount} EMBER Points for {wallet} nonce {nonce}"
     */
    function convertPoints(
        uint256 pointsAmount,
        bytes calldata signature
    ) external nonReentrant whenNotPaused {
        require(pointsAmount > 0, "Amount must be > 0");
        require(pointsAmount <= maxConversionPerTx, "Exceeds max per tx");

        // Get current nonce for user
        uint256 currentNonce = nonces[msg.sender];

        // Build message
        bytes32 messageHash = keccak256(abi.encodePacked(
            "Convert ",
            pointsAmount,
            " EMBER Points for ",
            msg.sender,
            " nonce ",
            currentNonce
        ));

        // Verify signature
        bytes32 ethSignedHash = messageHash.toEthSignedMessageHash();
        address signer = ethSignedHash.recover(signature);

        require(signer == authorizedSigner, "Invalid signature");

        // Increment nonce (prevents replay)
        nonces[msg.sender]++;

        // Calculate tokens to mint (apply conversion rate)
        uint256 tokensToMint = (pointsAmount * conversionRate) / 10000;

        // Update stats
        totalConverted[msg.sender] += pointsAmount;
        totalPointsConverted += pointsAmount;
        totalTokensMinted += tokensToMint;

        // Mint $EMBER tokens
        emberToken.mint(msg.sender, tokensToMint);

        emit PointsConverted(msg.sender, pointsAmount, tokensToMint, currentNonce);
    }

    /**
     * @dev Get expected tokens for points amount (preview)
     */
    function getExpectedTokens(uint256 pointsAmount) external view returns (uint256) {
        return (pointsAmount * conversionRate) / 10000;
    }

    /**
     * @dev Get conversion data for user
     */
    function getUserConversionData(address user) external view returns (
        uint256 converted,
        uint256 currentNonce
    ) {
        return (totalConverted[user], nonces[user]);
    }

    // ========== ADMIN FUNCTIONS ==========

    /**
     * @dev Set authorized signer (backend wallet)
     */
    function setAuthorizedSigner(address _signer) external onlyOwner {
        require(_signer != address(0), "Invalid address");
        authorizedSigner = _signer;
        emit AuthorizedSignerSet(_signer);
    }

    /**
     * @dev Set conversion rate (in basis points)
     * @param _rate New rate (10000 = 1:1, 15000 = 1.5:1, etc.)
     *
     * Examples:
     * - 10000 = 1 point → 1 token (1:1 ratio)
     * - 15000 = 1 point → 1.5 tokens (1.5x bonus)
     * - 20000 = 1 point → 2 tokens (2x bonus)
     * - 5000 = 1 point → 0.5 tokens (penalty)
     */
    function setConversionRate(uint256 _rate) external onlyOwner {
        require(_rate > 0, "Rate must be > 0");
        require(_rate <= 100000, "Rate too high");  // Max 10x
        conversionRate = _rate;
        emit ConversionRateSet(_rate);
    }

    /**
     * @dev Set max conversion per transaction (anti-abuse)
     */
    function setMaxConversionPerTx(uint256 _max) external onlyOwner {
        require(_max > 0, "Max must be > 0");
        maxConversionPerTx = _max;
        emit MaxConversionSet(_max);
    }

    /**
     * @dev Pause conversions (emergency)
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @dev Unpause conversions
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @dev Emergency function to adjust nonce (if user has issues)
     * USE WITH EXTREME CAUTION
     */
    function emergencySetNonce(address user, uint256 newNonce) external onlyOwner {
        nonces[user] = newNonce;
    }
}
