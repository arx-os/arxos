// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/ArxOracleStaking.sol";
import "../src/ArxosToken.sol";

contract ArxOracleStakingTest is Test {
    ArxOracleStaking public staking;
    ArxosToken public arxo;
    
    address public admin = address(1);
    address public oracle1 = address(2);
    address public oracle2 = address(3);
    
    uint256 public minStake = 1000 * 1e18;
    
    function setUp() public {
        vm.startPrank(admin);
        arxo = new ArxosToken(admin);
        staking = new ArxOracleStaking(admin, address(arxo), minStake);
        
        // Grant admin the minter role to provide tokens for testing
        arxo.grantRole(arxo.MINTER_ROLE(), admin);
        
        // Distribute tokens to oracles
        arxo.mint(oracle1, 10000 * 1e18);
        arxo.mint(oracle2, 10000 * 1e18);
        vm.stopPrank();
    }
    
    function test_InitialStake() public {
        assertEq(staking.minStake(), minStake);
        assertEq(address(staking.arxoToken()), address(arxo));
    }
    
    function test_Stake() public {
        vm.startPrank(oracle1);
        arxo.approve(address(staking), 5000 * 1e18);
        staking.stake(5000 * 1e18);
        vm.stopPrank();
        
        assertEq(staking.stakes(oracle1), 5000 * 1e18);
        assertTrue(staking.hasMinStake(oracle1));
    }
    
    function test_WithdrawalWorkflow() public {
        vm.startPrank(oracle1);
        arxo.approve(address(staking), 5000 * 1e18);
        staking.stake(5000 * 1e18);
        
        staking.requestWithdrawal(2000 * 1e18);
        assertEq(staking.stakes(oracle1), 3000 * 1e18);
        assertEq(staking.pendingWithdrawals(oracle1), 2000 * 1e18);
        
        // Try to withdraw early
        vm.expectRevert("ArxOracleStaking: withdrawal delay not met");
        staking.withdraw();
        
        // Warp time
        vm.warp(block.timestamp + 7 days);
        staking.withdraw();
        vm.stopPrank();
        
        assertEq(arxo.balanceOf(oracle1), 10000 * 1e18 - 5000 * 1e18 + 2000 * 1e18);
        assertEq(staking.pendingWithdrawals(oracle1), 0);
    }
    
    function test_Slash() public {
        vm.startPrank(oracle1);
        arxo.approve(address(staking), 5000 * 1e18);
        staking.stake(5000 * 1e18);
        vm.stopPrank();
        
        vm.prank(admin);
        staking.slash(oracle1, 1000 * 1e18, "misconduct");
        
        assertEq(staking.stakes(oracle1), 4000 * 1e18);
    }
    
    function test_RevertWhen_InsufficientStakeForOracle() public {
        vm.startPrank(oracle1);
        arxo.approve(address(staking), 500 * 1e18);
        staking.stake(500 * 1e18);
        vm.stopPrank();
        
        assertFalse(staking.hasMinStake(oracle1));
    }
}
