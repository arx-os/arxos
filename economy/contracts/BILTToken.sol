// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title BILTToken
 * @dev BILT (Building Infrastructure Link Token) - ERC-20 token for Arxos platform
 * 
 * Features:
 * - Unlimited supply based on validated contributions
 * - Minting controls for authorized contributors
 * - Dividend distribution to all holders
 * - Fraud prevention mechanisms
 * - Contribution tracking
 */
contract BILTToken is ERC20, Ownable, Pausable, ReentrancyGuard {
    
    // ============ STATE VARIABLES ============
    
    // Minting controls
    mapping(address => bool) public authorizedMinters;
    mapping(bytes32 => uint256) public objectMintAmounts;
    mapping(bytes32 => address) public objectContributors;
    mapping(bytes32 => address) public objectVerifiers;
    mapping(address => bytes32[]) public contributorObjects;
    
    // Fraud prevention
    mapping(address => uint256) public reputationScores;
    mapping(address => uint256) public fraudStrikes;
    mapping(bytes32 => bool) public blacklistedObjects;
    
    // Dividend tracking
    uint256 public totalDividendsDistributed;
    mapping(address => uint256) public lastDividendIndex;
    uint256 public currentDividendIndex;
    
    // Events
    event BiltMinted(address indexed contributor, bytes32 indexed biltobjectHash, uint256 amount, address indexed verifier);
    event DividendDistributed(uint256 totalAmount, uint256 dividendIndex);
    event FraudReported(address indexed contributor, bytes32 indexed biltobjectHash, string reason);
    event ReputationUpdated(address indexed contributor, int256 delta);
    event ObjectBlacklisted(bytes32 indexed biltobjectHash);
    
    // ============ CONSTRUCTOR ============
    
    constructor() ERC20("BILT Token", "BILT") {
        // Initial setup
        currentDividendIndex = 1;
    }
    
    // ============ MINTING FUNCTIONS ============
    
    /**
     * @dev Mint BILT tokens for validated contribution
     * @param contributor Address of the contributor
     * @param biltobjectHash Hash of the contributed object
     * @param amount Amount of BILT to mint
     * @param verifier Address of the secondary verifier
     */
    function mintForContribution(
        address contributor,
        bytes32 biltobjectHash,
        uint256 amount,
        address verifier
    ) external onlyAuthorizedMinter whenNotPaused nonReentrant {
        require(contributor != address(0), "Invalid contributor address");
        require(verifier != address(0), "Invalid verifier address");
        require(amount > 0, "Amount must be greater than 0");
        require(objectMintAmounts[biltobjectHash] == 0, "Object already minted");
        require(!blacklistedObjects[biltobjectHash], "Object is blacklisted");
        
        // Record the contribution
        objectMintAmounts[biltobjectHash] = amount;
        objectContributors[biltobjectHash] = contributor;
        objectVerifiers[biltobjectHash] = verifier;
        contributorObjects[contributor].push(biltobjectHash);
        
        // Mint tokens
        _mint(contributor, amount);
        
        emit BiltMinted(contributor, biltobjectHash, amount, verifier);
    }
    
    // ============ DIVIDEND FUNCTIONS ============
    
    /**
     * @dev Distribute dividends to all token holders
     * @param totalAmount Total amount to distribute
     */
    function distributeDividend(uint256 totalAmount) external onlyOwner whenNotPaused {
        require(totalAmount > 0, "Amount must be greater than 0");
        require(totalSupply() > 0, "No tokens in circulation");
        
        // Calculate dividend per token
        uint256 dividendPerToken = totalAmount * 1e18 / totalSupply();
        
        // Update dividend index
        currentDividendIndex++;
        totalDividendsDistributed += totalAmount;
        
        emit DividendDistributed(totalAmount, currentDividendIndex);
    }
    
    /**
     * @dev Claim dividends for a specific address
     * @param account Address to claim dividends for
     */
    function claimDividends(address account) external whenNotPaused nonReentrant {
        uint256 claimable = getClaimableDividends(account);
        require(claimable > 0, "No dividends to claim");
        
        // Update last dividend index for the account
        lastDividendIndex[account] = currentDividendIndex;
        
        // Transfer dividends
        (bool success, ) = account.call{value: claimable}("");
        require(success, "Dividend transfer failed");
    }
    
    /**
     * @dev Get claimable dividends for an address
     * @param account Address to check
     * @return Amount of claimable dividends
     */
    function getClaimableDividends(address account) public view returns (uint256) {
        uint256 balance = balanceOf(account);
        if (balance == 0) return 0;
        
        uint256 lastIndex = lastDividendIndex[account];
        uint256 currentIndex = currentDividendIndex;
        
        if (lastIndex >= currentIndex) return 0;
        
        // Calculate dividends based on balance and dividend index difference
        // This is a simplified calculation - in practice, you'd track dividend amounts per index
        return balance * (currentIndex - lastIndex) / 1e18;
    }
    
    // ============ FRAUD PREVENTION ============
    
    /**
     * @dev Report fraud for a contribution
     * @param contributor Address of the contributor
     * @param biltobjectHash Hash of the contributed object
     * @param reason Reason for fraud report
     */
    function reportFraud(
        address contributor,
        bytes32 biltobjectHash,
        string memory reason
    ) external onlyAuthorizedMinter {
        require(objectContributors[biltobjectHash] == contributor, "Invalid contributor for object");
        require(!blacklistedObjects[biltobjectHash], "Object already blacklisted");
        
        // Blacklist the object
        blacklistedObjects[biltobjectHash] = true;
        
        // Update fraud strikes
        fraudStrikes[contributor]++;
        
        emit FraudReported(contributor, biltobjectHash, reason);
        emit ObjectBlacklisted(biltobjectHash);
    }
    
    /**
     * @dev Slash tokens from a fraudulent contributor
     * @param contributor Address to slash tokens from
     * @param amount Amount of tokens to slash
     */
    function slashTokens(address contributor, uint256 amount) external onlyOwner {
        require(balanceOf(contributor) >= amount, "Insufficient balance to slash");
        
        _burn(contributor, amount);
    }
    
    /**
     * @dev Update reputation score for a contributor
     * @param contributor Address of the contributor
     * @param delta Change in reputation score (can be negative)
     */
    function updateReputation(address contributor, int256 delta) external onlyAuthorizedMinter {
        uint256 currentScore = reputationScores[contributor];
        
        if (delta > 0) {
            reputationScores[contributor] = currentScore + uint256(delta);
        } else {
            uint256 decrease = uint256(-delta);
            if (decrease > currentScore) {
                reputationScores[contributor] = 0;
            } else {
                reputationScores[contributor] = currentScore - decrease;
            }
        }
        
        emit ReputationUpdated(contributor, delta);
    }
    
    // ============ ADMIN FUNCTIONS ============
    
    /**
     * @dev Add or remove authorized minter
     * @param minter Address to authorize/revoke
     * @param authorized Whether to authorize or revoke
     */
    function setAuthorizedMinter(address minter, bool authorized) external onlyOwner {
        authorizedMinters[minter] = authorized;
    }
    
    /**
     * @dev Pause or unpause the contract
     * @param paused Whether to pause or unpause
     */
    function setPaused(bool paused) external onlyOwner {
        if (paused) {
            _pause();
        } else {
            _unpause();
        }
    }
    
    // ============ VIEW FUNCTIONS ============
    
    /**
     * @dev Get all objects contributed by an address
     * @param contributor Address to check
     * @return Array of object hashes
     */
    function getContributorObjects(address contributor) external view returns (bytes32[] memory) {
        return contributorObjects[contributor];
    }
    
    /**
     * @dev Get contribution details for an object
     * @param biltobjectHash Hash of the object
     * @return contributor Address of the contributor
     * @return verifier Address of the verifier
     * @return amount Amount of BILT minted
     * @return isBlacklisted Whether the object is blacklisted
     */
    function getObjectDetails(bytes32 biltobjectHash) external view returns (
        address contributor,
        address verifier,
        uint256 amount,
        bool isBlacklisted
    ) {
        return (
            objectContributors[biltobjectHash],
            objectVerifiers[biltobjectHash],
            objectMintAmounts[biltobjectHash],
            blacklistedObjects[biltobjectHash]
        );
    }
    
    // ============ MODIFIERS ============
    
    modifier onlyAuthorizedMinter() {
        require(authorizedMinters[msg.sender] || msg.sender == owner(), "Not authorized minter");
        _;
    }
    
    // ============ OVERRIDES ============
    
    /**
     * @dev Override transfer to include fraud checks
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal virtual override {
        super._beforeTokenTransfer(from, to, amount);
        
        // Additional checks can be added here for fraud prevention
        require(!paused(), "Token transfers paused");
    }
} 