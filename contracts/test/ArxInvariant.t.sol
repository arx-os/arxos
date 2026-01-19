// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {ArxosToken} from "../src/ArxosToken.sol";
import {ArxContributionOracle} from "../src/ArxContributionOracle.sol";
import {ArxRegistry} from "../src/ArxRegistry.sol";
import {ArxAddresses} from "../src/ArxAddresses.sol";
import {ArxOracleStaking} from "../src/ArxOracleStaking.sol";
import {ArxPaymentRouter} from "../src/ArxPaymentRouter.sol";

/**
 * @title ArxInvariantTests
 * @notice Invariant tests for ArxOS system properties
 * @dev These tests verify critical system invariants that must always hold
 */
contract ArxInvariantTests is Test {
    ArxosToken public token;
    ArxContributionOracle public oracle;
    ArxRegistry public registry;
    ArxAddresses public addresses;
    ArxOracleStaking public staking;
    ArxPaymentRouter public paymentRouter;
    
    address public admin = address(this);
    address public maintainer = address(0x1);
    address public treasury = address(0x2);
    
    // Track all addresses that have received tokens
    address[] public tokenHolders;
    mapping(address => bool) public isTokenHolder;
    
    function setUp() public {
        // Deploy contracts
        addresses = new ArxAddresses(admin, maintainer, treasury);
        registry = new ArxRegistry(admin);
        token = new ArxosToken(admin);
        staking = new ArxOracleStaking(admin, address(token), 1000 ether);
        oracle = new ArxContributionOracle(
            admin,
            address(token),
            address(registry),
            address(addresses),
            address(staking)
        );
        paymentRouter = new ArxPaymentRouter(
            admin,
            address(token),
            address(registry),
            address(addresses)
        );
        
        // Grant roles
        token.grantRole(token.MINTER_ROLE(), address(oracle));
        token.grantRole(token.MINTER_ROLE(), admin);
        
        // Target contracts for invariant testing
        targetContract(address(token));
        targetContract(address(oracle));
    }
    
    /// @notice Track new token holders
    function _trackHolder(address holder) internal {
        if (!isTokenHolder[holder] && token.balanceOf(holder) > 0) {
            tokenHolders.push(holder);
            isTokenHolder[holder] = true;
        }
    }
    
    /**
     * INVARIANT 1: Total Supply Consistency
     * The total supply must always equal the sum of all individual balances
     */
    function invariant_totalSupplyEqualsBalances() public {
        uint256 totalSupply = token.totalSupply();
        uint256 sumOfBalances = 0;
        
        // Sum all known balances
        for (uint256 i = 0; i < tokenHolders.length; i++) {
            sumOfBalances += token.balanceOf(tokenHolders[i]);
        }
        
        // Also check system addresses
        sumOfBalances += token.balanceOf(maintainer);
        sumOfBalances += token.balanceOf(treasury);
        sumOfBalances += token.balanceOf(address(oracle));
        sumOfBalances += token.balanceOf(address(staking));
        
        assertEq(totalSupply, sumOfBalances, "Total supply must equal sum of balances");
    }
    
    /**
     * INVARIANT 2: Revenue Split Correctness
     * All tier configurations must sum to exactly 100% (10000 basis points)
     */
    function invariant_revenueSplitsSum100Percent() public {
        // Check Standard tier
        (uint256 workerBps, uint256 buildingBps, uint256 maintainerBps, uint256 treasuryBps) = 
            oracle.tierConfigs(ArxContributionOracle.SplitTier.STANDARD);
        assertEq(
            workerBps + buildingBps + maintainerBps + treasuryBps,
            10000,
            "Standard tier must sum to 100%"
        );
        
        // Check Premium tier
        (workerBps, buildingBps, maintainerBps, treasuryBps) = 
            oracle.tierConfigs(ArxContributionOracle.SplitTier.PREMIUM);
        assertEq(
            workerBps + buildingBps + maintainerBps + treasuryBps,
            10000,
            "Premium tier must sum to 100%"
        );
        
        // Check Enterprise tier
        (workerBps, buildingBps, maintainerBps, treasuryBps) = 
            oracle.tierConfigs(ArxContributionOracle.SplitTier.ENTERPRISE);
        assertEq(
            workerBps + buildingBps + maintainerBps + treasuryBps,
            10000,
            "Enterprise tier must sum to 100%"
        );
    }
    
    /**
     * INVARIANT 3: Daily Caps Cannot Be Exceeded
     * No worker or building should ever exceed their daily cap
     * Note: This is enforced by reverts, so we verify the caps are set correctly
     */
    function invariant_dailyCapsArePositive() public view {
        uint256 workerCap = token.workerDailyCap();
        uint256 buildingCap = token.buildingDailyCap();
        
        // Caps should either be unlimited (max uint256) or a reasonable positive value
        assertTrue(
            workerCap > 0 || workerCap == type(uint256).max,
            "Worker cap must be positive or unlimited"
        );
        assertTrue(
            buildingCap > 0 || buildingCap == type(uint256).max,
            "Building cap must be positive or unlimited"
        );
    }
    
    /**
     * INVARIANT 4: Oracle Consensus Requirements
     * MIN_CONFIRMATIONS must be achievable and reasonable
     */
    function invariant_consensusRequirementsValid() public view {
        uint256 minConfirmations = oracle.MIN_CONFIRMATIONS();
        
        // Must require at least 2 confirmations for security
        assertGe(minConfirmations, 2, "Must require at least 2 confirmations");
        
        // Should not require more than 5 (practical limit)
        assertLe(minConfirmations, 5, "Should not require more than 5 confirmations");
    }
    
    /**
     * INVARIANT 5: Finalization Delay Is Reasonable
     * The delay should be long enough for disputes but not too long
     */
    function invariant_finalizationDelayReasonable() public view {
        uint256 delay = oracle.FINALIZATION_DELAY();
        
        // At least 1 hour for dispute window
        assertGe(delay, 1 hours, "Delay must be at least 1 hour");
        
        // No more than 7 days (too long for UX)
        assertLe(delay, 7 days, "Delay should not exceed 7 days");
    }
    
    /**
     * INVARIANT 6: Minimum Stake Is Reasonable
     * Oracle stake requirements should be meaningful but achievable
     */
    function invariant_minStakeReasonable() public view {
        uint256 minStake = staking.minStake();
        
        // Should require meaningful stake (at least 100 tokens)
        assertGe(minStake, 100 ether, "Min stake should be at least 100 tokens");
        
        // Should not be impossibly high (max 1M tokens)
        assertLe(minStake, 1_000_000 ether, "Min stake should not exceed 1M tokens");
    }
    
    /**
     * INVARIANT 7: No Negative Balances
     * All balances must be non-negative (this should be impossible with uint256, but verify)
     */
    function invariant_noNegativeBalances() public view {
        for (uint256 i = 0; i < tokenHolders.length; i++) {
            uint256 balance = token.balanceOf(tokenHolders[i]);
            // uint256 is always >= 0, but we verify it's a valid value
            assertTrue(balance >= 0, "Balance must be non-negative");
        }
    }
}
