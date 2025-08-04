// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./BILTToken.sol";

/**
 * @title RevenueRouter
 * @dev Handles revenue attribution and dividend distribution for BILT token holders
 * 
 * Features:
 * - Revenue attribution from platform activities
 * - Equal dividend distribution to all BILT holders
 * - Revenue tracking and transparency
 * - Integration with BILT token contract
 */
contract RevenueRouter is Ownable, ReentrancyGuard {
    
    // ============ STATE VARIABLES ============
    
    BILTToken public biltToken;
    
    // Revenue tracking
    uint256 public totalRevenue;
    uint256 public totalDividendsDistributed;
    uint256 public currentDividendPool;
    
    // Revenue sources
    mapping(string => uint256) public revenueBySource;
    mapping(uint256 => RevenueEntry) public revenueHistory;
    uint256 public revenueEntryCounter;
    
    // Dividend tracking
    mapping(uint256 => DividendDistribution) public dividendHistory;
    uint256 public dividendDistributionCounter;
    
    // Events
    event RevenueAttributed(string source, uint256 amount, uint256 timestamp);
    event DividendDistributed(uint256 totalAmount, uint256 dividendIndex, uint256 timestamp);
    event RevenuePoolUpdated(uint256 newPool, uint256 timestamp);
    
    // Structs
    struct RevenueEntry {
        string source;
        uint256 amount;
        uint256 timestamp;
        bool processed;
    }
    
    struct DividendDistribution {
        uint256 totalAmount;
        uint256 dividendIndex;
        uint256 timestamp;
        uint256 totalSupply;
    }
    
    // ============ CONSTRUCTOR ============
    
    constructor(address _biltTokenAddress) {
        require(_biltTokenAddress != address(0), "Invalid BILT token address");
        biltToken = BILTToken(_biltTokenAddress);
    }
    
    // ============ REVENUE FUNCTIONS ============
    
    /**
     * @dev Attribute revenue from platform activities
     * @param source Source of revenue (e.g., "data_sales", "service_transactions")
     * @param amount Amount of revenue in wei
     */
    function attributeRevenue(string memory source, uint256 amount) external onlyOwner {
        require(amount > 0, "Amount must be greater than 0");
        require(bytes(source).length > 0, "Source cannot be empty");
        
        // Update revenue tracking
        totalRevenue += amount;
        revenueBySource[source] += amount;
        currentDividendPool += amount;
        
        // Record revenue entry
        revenueEntryCounter++;
        revenueHistory[revenueEntryCounter] = RevenueEntry({
            source: source,
            amount: amount,
            timestamp: block.timestamp,
            processed: false
        });
        
        emit RevenueAttributed(source, amount, block.timestamp);
        emit RevenuePoolUpdated(currentDividendPool, block.timestamp);
    }
    
    /**
     * @dev Distribute dividends to all BILT token holders
     * @param amount Amount to distribute (must be <= currentDividendPool)
     */
    function distributeDividends(uint256 amount) external onlyOwner nonReentrant {
        require(amount > 0, "Amount must be greater than 0");
        require(amount <= currentDividendPool, "Amount exceeds dividend pool");
        require(biltToken.totalSupply() > 0, "No tokens in circulation");
        
        // Distribute dividends through BILT token contract
        biltToken.distributeDividend(amount);
        
        // Update tracking
        currentDividendPool -= amount;
        totalDividendsDistributed += amount;
        
        // Record dividend distribution
        dividendDistributionCounter++;
        dividendHistory[dividendDistributionCounter] = DividendDistribution({
            totalAmount: amount,
            dividendIndex: biltToken.currentDividendIndex(),
            timestamp: block.timestamp,
            totalSupply: biltToken.totalSupply()
        });
        
        emit DividendDistributed(amount, biltToken.currentDividendIndex(), block.timestamp);
        emit RevenuePoolUpdated(currentDividendPool, block.timestamp);
    }
    
    /**
     * @dev Distribute entire dividend pool
     */
    function distributeAllDividends() external onlyOwner {
        uint256 poolAmount = currentDividendPool;
        if (poolAmount > 0) {
            distributeDividends(poolAmount);
        }
    }
    
    // ============ VIEW FUNCTIONS ============
    
    /**
     * @dev Get total revenue by source
     * @param source Revenue source to query
     * @return Total revenue from the specified source
     */
    function getRevenueBySource(string memory source) external view returns (uint256) {
        return revenueBySource[source];
    }
    
    /**
     * @dev Get revenue entry details
     * @param entryId ID of the revenue entry
     * @return Revenue entry details
     */
    function getRevenueEntry(uint256 entryId) external view returns (
        string memory source,
        uint256 amount,
        uint256 timestamp,
        bool processed
    ) {
        RevenueEntry memory entry = revenueHistory[entryId];
        return (entry.source, entry.amount, entry.timestamp, entry.processed);
    }
    
    /**
     * @dev Get dividend distribution details
     * @param distributionId ID of the dividend distribution
     * @return Dividend distribution details
     */
    function getDividendDistribution(uint256 distributionId) external view returns (
        uint256 totalAmount,
        uint256 dividendIndex,
        uint256 timestamp,
        uint256 totalSupply
    ) {
        DividendDistribution memory distribution = dividendHistory[distributionId];
        return (
            distribution.totalAmount,
            distribution.dividendIndex,
            distribution.timestamp,
            distribution.totalSupply
        );
    }
    
    /**
     * @dev Get current dividend pool and statistics
     * @return pool Current dividend pool amount
     * @return totalRevenue Total revenue attributed
     * @return totalDistributed Total dividends distributed
     * @return totalSupply Current BILT token supply
     */
    function getDividendPoolStats() external view returns (
        uint256 pool,
        uint256 totalRevenue,
        uint256 totalDistributed,
        uint256 totalSupply
    ) {
        return (
            currentDividendPool,
            totalRevenue,
            totalDividendsDistributed,
            biltToken.totalSupply()
        );
    }
    
    /**
     * @dev Calculate dividend per token for a given amount
     * @param amount Amount to distribute
     * @return Dividend per token (with 18 decimals)
     */
    function calculateDividendPerToken(uint256 amount) external view returns (uint256) {
        uint256 totalSupply = biltToken.totalSupply();
        if (totalSupply == 0) return 0;
        return (amount * 1e18) / totalSupply();
    }
    
    /**
     * @dev Get all revenue sources and their amounts
     * @return sources Array of revenue source names
     * @return amounts Array of corresponding amounts
     */
    function getAllRevenueSources() external view returns (
        string[] memory sources,
        uint256[] memory amounts
    ) {
        // This is a simplified implementation
        // In practice, you'd maintain a list of sources
        string[] memory defaultSources = new string[](3);
        defaultSources[0] = "data_sales";
        defaultSources[1] = "service_transactions";
        defaultSources[2] = "api_usage";
        
        uint256[] memory defaultAmounts = new uint256[](3);
        defaultAmounts[0] = revenueBySource["data_sales"];
        defaultAmounts[1] = revenueBySource["service_transactions"];
        defaultAmounts[2] = revenueBySource["api_usage"];
        
        return (defaultSources, defaultAmounts);
    }
    
    // ============ ADMIN FUNCTIONS ============
    
    /**
     * @dev Update BILT token contract address
     * @param newBiltTokenAddress New BILT token contract address
     */
    function updateBiltTokenAddress(address newBiltTokenAddress) external onlyOwner {
        require(newBiltTokenAddress != address(0), "Invalid address");
        biltToken = BILTToken(newBiltTokenAddress);
    }
    
    /**
     * @dev Emergency function to withdraw stuck funds
     * @param amount Amount to withdraw
     * @param recipient Address to send funds to
     */
    function emergencyWithdraw(uint256 amount, address recipient) external onlyOwner {
        require(recipient != address(0), "Invalid recipient");
        require(amount <= address(this).balance, "Insufficient balance");
        
        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Transfer failed");
    }
    
    // ============ RECEIVE FUNCTION ============
    
    /**
     * @dev Allow contract to receive ETH
     */
    receive() external payable {
        // Automatically attribute received ETH as revenue
        if (msg.value > 0) {
            attributeRevenue("direct_deposit", msg.value);
        }
    }
} 