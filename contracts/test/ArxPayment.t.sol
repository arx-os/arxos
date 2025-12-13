// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {ArxPaymentRouter} from "../src/ArxPaymentRouter.sol";
import {ArxosToken} from "../src/ArxosToken.sol";
import {ArxRegistry} from "../src/ArxRegistry.sol";
import {ArxAddresses} from "../src/ArxAddresses.sol";

contract ArxPaymentTest is Test {
    ArxPaymentRouter public router;
    ArxosToken public token;
    ArxRegistry public registry;
    ArxAddresses public addresses;
    
    address public owner = address(this);
    address public payer = address(0x1001);
    address public buildingWallet = address(0x2001);
    address public maintainerVault = address(0x3001);
    address public treasury = address(0x4001);
    
    string constant BUILDING_ID = "ps-118";
    uint256 constant INITIAL_BALANCE = 10000 ether;
    
    event AccessPaid(
        string indexed buildingId,
        address indexed payer,
        uint256 amount,
        bytes32 indexed nonce,
        uint256 timestamp
    );
    
    event PaymentDistributed(
        address indexed building,
        address indexed maintainer,
        address indexed treasury,
        uint256 buildingAmount,
        uint256 maintainerAmount,
        uint256 treasuryAmount
    );
    
    event MinimumPaymentUpdated(string indexed buildingId, uint256 oldMinimum, uint256 newMinimum);

    function setUp() public {
        // Deploy contracts
        addresses = new ArxAddresses(owner, maintainerVault, treasury);
        token = new ArxosToken(owner);
        registry = new ArxRegistry(owner);
        router = new ArxPaymentRouter(
            owner,
            address(token),
            address(registry),
            address(addresses)
        );
        
        // Register building
        registry.registerBuilding(BUILDING_ID, buildingWallet);
        
        // Mint tokens to payer and approve router
        token.grantRole(token.MINTER_ROLE(), owner);
        token.mint(payer, INITIAL_BALANCE);
        
        // Payer approves router to spend tokens
        vm.prank(payer);
        token.approve(address(router), type(uint256).max);
    }

    // ============ Constructor Tests ============

    function test_Constructor() public view {
        assertEq(address(router.arxoToken()), address(token));
        assertEq(address(router.registry()), address(registry));
        assertEq(address(router.addresses()), address(addresses));
        assertEq(router.owner(), owner);
        assertEq(router.DEFAULT_MINIMUM(), 10**16);
    }

    // ============ Payment Tests ============

    function test_PayForAccess() public {
        uint256 amount = 1 ether;
        bytes32 nonce = keccak256("nonce1");
        
        vm.expectEmit(true, true, true, true);
        emit AccessPaid(BUILDING_ID, payer, amount, nonce, block.timestamp);
        
        vm.prank(payer);
        router.payForAccess(BUILDING_ID, amount, nonce);
        
        // Verify 70/10/10/10 distribution
        assertEq(token.balanceOf(buildingWallet), (amount * 70) / 100);
        assertEq(token.balanceOf(maintainerVault), (amount * 10) / 100);
        assertEq(token.balanceOf(treasury), (amount * 10) / 100 + (amount * 10) / 100); // Rounding
        
        // Verify nonce marked as used
        assertTrue(router.isNonceUsed(nonce));
        
        // Verify payer balance decreased
        assertEq(token.balanceOf(payer), INITIAL_BALANCE - amount);
    }

    function test_PayForAccess_ExactDistribution() public {
        uint256 amount = 1000 ether;
        bytes32 nonce = keccak256("nonce1");
        
        vm.prank(payer);
        router.payForAccess(BUILDING_ID, amount, nonce);
        
        // Verify exact 70/10/10/10 split
        uint256 expectedBuilding = 700 ether;
        uint256 expectedMaintainer = 100 ether;
        uint256 expectedTreasury = 200 ether; // Gets remainder
        
        assertEq(token.balanceOf(buildingWallet), expectedBuilding);
        assertEq(token.balanceOf(maintainerVault), expectedMaintainer);
        assertEq(token.balanceOf(treasury), expectedTreasury);
        
        // Verify total matches
        assertEq(
            token.balanceOf(buildingWallet) + token.balanceOf(maintainerVault) + token.balanceOf(treasury),
            amount
        );
    }

    function test_PaymentDistributedEvent() public {
        uint256 amount = 1000 ether;
        bytes32 nonce = keccak256("nonce1");
        
        uint256 buildingAmount = (amount * 70) / 100;
        uint256 maintainerAmount = (amount * 10) / 100;
        uint256 treasuryAmount = amount - buildingAmount - maintainerAmount;
        
        vm.expectEmit(true, true, true, true);
        emit PaymentDistributed(
            buildingWallet,
            maintainerVault,
            treasury,
            buildingAmount,
            maintainerAmount,
            treasuryAmount
        );
        
        vm.prank(payer);
        router.payForAccess(BUILDING_ID, amount, nonce);
    }

    // ============ Batch Payment Tests ============

    function test_BatchPayForAccess() public {
        // Register second building
        string memory buildingId2 = "building-2";
        address buildingWallet2 = address(0x2002);
        registry.registerBuilding(buildingId2, buildingWallet2);
        
        string[] memory buildingIds = new string[](2);
        buildingIds[0] = BUILDING_ID;
        buildingIds[1] = buildingId2;
        
        uint256[] memory amounts = new uint256[](2);
        amounts[0] = 100 ether;
        amounts[1] = 200 ether;
        
        bytes32[] memory nonces = new bytes32[](2);
        nonces[0] = keccak256("nonce1");
        nonces[1] = keccak256("nonce2");
        
        vm.prank(payer);
        router.batchPayForAccess(buildingIds, amounts, nonces);
        
        // Verify first building got 70% of 100
        assertEq(token.balanceOf(buildingWallet), 70 ether);
        
        // Verify second building got 70% of 200
        assertEq(token.balanceOf(buildingWallet2), 140 ether);
        
        // Verify maintainer got 10% of total (300)
        assertEq(token.balanceOf(maintainerVault), 30 ether);
        
        // Verify nonces used
        assertTrue(router.isNonceUsed(nonces[0]));
        assertTrue(router.isNonceUsed(nonces[1]));
    }

    function test_BatchPayForAccess_EmitsEvents() public {
        string[] memory buildingIds = new string[](1);
        buildingIds[0] = BUILDING_ID;
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = 100 ether;
        
        bytes32[] memory nonces = new bytes32[](1);
        nonces[0] = keccak256("nonce1");
        
        vm.expectEmit(true, true, true, true);
        emit AccessPaid(BUILDING_ID, payer, 100 ether, nonces[0], block.timestamp);
        
        vm.prank(payer);
        router.batchPayForAccess(buildingIds, amounts, nonces);
    }

    // ============ Minimum Payment Tests ============

    function test_GetMinimumPayment_DefaultValue() public view {
        assertEq(router.getMinimumPayment(BUILDING_ID), router.DEFAULT_MINIMUM());
    }

    function test_SetMinimumPayment() public {
        uint256 newMinimum = 1 ether;
        
        vm.expectEmit(true, false, false, true);
        emit MinimumPaymentUpdated(BUILDING_ID, 0, newMinimum);
        
        router.setMinimumPayment(BUILDING_ID, newMinimum);
        
        assertEq(router.getMinimumPayment(BUILDING_ID), newMinimum);
    }

    function test_PayForAccess_WithCustomMinimum() public {
        uint256 customMinimum = 5 ether;
        router.setMinimumPayment(BUILDING_ID, customMinimum);
        
        bytes32 nonce = keccak256("nonce1");
        
        vm.prank(payer);
        router.payForAccess(BUILDING_ID, customMinimum, nonce);
        
        assertEq(token.balanceOf(buildingWallet), (customMinimum * 70) / 100);
    }

    // ============ Nonce Replay Protection Tests ============

    function test_RevertWhen_NonceReused() public {
        bytes32 nonce = keccak256("nonce1");
        
        // First payment succeeds
        vm.prank(payer);
        router.payForAccess(BUILDING_ID, 1 ether, nonce);
        
        // Second payment with same nonce fails
        vm.expectRevert("ArxPaymentRouter: nonce already used");
        vm.prank(payer);
        router.payForAccess(BUILDING_ID, 1 ether, nonce);
    }

    function test_IsNonceUsed() public {
        bytes32 nonce = keccak256("nonce1");
        assertFalse(router.isNonceUsed(nonce));
        
        vm.prank(payer);
        router.payForAccess(BUILDING_ID, 1 ether, nonce);
        
        assertTrue(router.isNonceUsed(nonce));
    }

    // ============ Validation Tests ============

    function test_RevertWhen_BuildingNotRegistered() public {
        bytes32 nonce = keccak256("nonce1");
        
        vm.expectRevert("ArxPaymentRouter: building not registered");
        vm.prank(payer);
        router.payForAccess("nonexistent-building", 1 ether, nonce);
    }

    function test_RevertWhen_InsufficientAmount() public {
        bytes32 nonce = keccak256("nonce1");
        uint256 tooSmall = router.DEFAULT_MINIMUM() - 1;
        
        vm.expectRevert("ArxPaymentRouter: insufficient amount");
        vm.prank(payer);
        router.payForAccess(BUILDING_ID, tooSmall, nonce);
    }

    function test_RevertWhen_InsufficientAllowance() public {
        bytes32 nonce = keccak256("nonce1");
        address newPayer = address(0x9999);
        
        // Mint tokens but don't approve
        token.mint(newPayer, 100 ether);
        
        vm.expectRevert(); // ERC20InsufficientAllowance custom error
        vm.prank(newPayer);
        router.payForAccess(BUILDING_ID, 1 ether, nonce);
    }

    function test_RevertWhen_InsufficientBalance() public {
        bytes32 nonce = keccak256("nonce1");
        address poorPayer = address(0x8888);
        
        // Approve but no tokens
        vm.prank(poorPayer);
        token.approve(address(router), type(uint256).max);
        
        vm.expectRevert(); // ERC20InsufficientBalance custom error
        vm.prank(poorPayer);
        router.payForAccess(BUILDING_ID, 1 ether, nonce);
    }

    function test_RevertWhen_SetMinimumNotOwner() public {
        vm.expectRevert();
        vm.prank(payer);
        router.setMinimumPayment(BUILDING_ID, 1 ether);
    }

    function test_RevertWhen_SetMinimumZero() public {
        vm.expectRevert("ArxPaymentRouter: zero minimum");
        router.setMinimumPayment(BUILDING_ID, 0);
    }

    function test_RevertWhen_SetMinimumBuildingNotRegistered() public {
        vm.expectRevert("ArxPaymentRouter: building not registered");
        router.setMinimumPayment("nonexistent", 1 ether);
    }

    // ============ Batch Payment Validation Tests ============

    function test_RevertWhen_BatchEmptyArrays() public {
        string[] memory buildingIds = new string[](0);
        uint256[] memory amounts = new uint256[](0);
        bytes32[] memory nonces = new bytes32[](0);
        
        vm.expectRevert("ArxPaymentRouter: empty arrays");
        vm.prank(payer);
        router.batchPayForAccess(buildingIds, amounts, nonces);
    }

    function test_RevertWhen_BatchLengthMismatch() public {
        string[] memory buildingIds = new string[](2);
        uint256[] memory amounts = new uint256[](1);
        bytes32[] memory nonces = new bytes32[](2);
        
        vm.expectRevert("ArxPaymentRouter: length mismatch");
        vm.prank(payer);
        router.batchPayForAccess(buildingIds, amounts, nonces);
    }

    function test_RevertWhen_BatchBuildingNotRegistered() public {
        string[] memory buildingIds = new string[](1);
        buildingIds[0] = "nonexistent";
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = 1 ether;
        
        bytes32[] memory nonces = new bytes32[](1);
        nonces[0] = keccak256("nonce1");
        
        vm.expectRevert("ArxPaymentRouter: building not registered");
        vm.prank(payer);
        router.batchPayForAccess(buildingIds, amounts, nonces);
    }

    function test_RevertWhen_BatchInsufficientAmount() public {
        string[] memory buildingIds = new string[](1);
        buildingIds[0] = BUILDING_ID;
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = router.DEFAULT_MINIMUM() - 1;
        
        bytes32[] memory nonces = new bytes32[](1);
        nonces[0] = keccak256("nonce1");
        
        vm.expectRevert("ArxPaymentRouter: insufficient amount");
        vm.prank(payer);
        router.batchPayForAccess(buildingIds, amounts, nonces);
    }

    function test_RevertWhen_BatchNonceReused() public {
        bytes32 sharedNonce = keccak256("shared");
        
        string[] memory buildingIds = new string[](2);
        buildingIds[0] = BUILDING_ID;
        buildingIds[1] = BUILDING_ID;
        
        uint256[] memory amounts = new uint256[](2);
        amounts[0] = 1 ether;
        amounts[1] = 1 ether;
        
        bytes32[] memory nonces = new bytes32[](2);
        nonces[0] = sharedNonce;
        nonces[1] = sharedNonce;
        
        vm.expectRevert("ArxPaymentRouter: nonce already used");
        vm.prank(payer);
        router.batchPayForAccess(buildingIds, amounts, nonces);
    }

    // ============ Emergency Functions Tests ============

    function test_EmergencyWithdraw() public {
        // Send some tokens to router (simulating stuck funds)
        token.mint(address(router), 100 ether);
        
        uint256 ownerBalanceBefore = token.balanceOf(owner);
        uint256 routerBalance = token.balanceOf(address(router));
        
        router.emergencyWithdraw(routerBalance);
        
        assertEq(token.balanceOf(owner), ownerBalanceBefore + routerBalance);
        assertEq(token.balanceOf(address(router)), 0);
    }

    function test_GetBalance() public {
        assertEq(router.getBalance(), 0);
        
        token.mint(address(router), 50 ether);
        assertEq(router.getBalance(), 50 ether);
    }

    function test_RevertWhen_EmergencyWithdrawNotOwner() public {
        token.mint(address(router), 100 ether);
        
        vm.expectRevert();
        vm.prank(payer);
        router.emergencyWithdraw(100 ether);
    }

    // ============ Fuzz Tests ============

    function testFuzz_PayForAccess(uint256 amount) public {
        // Bound amount to reasonable range
        amount = bound(amount, router.DEFAULT_MINIMUM(), INITIAL_BALANCE);
        
        bytes32 nonce = keccak256(abi.encodePacked("fuzz", amount));
        
        vm.prank(payer);
        router.payForAccess(BUILDING_ID, amount, nonce);
        
        // Verify distribution sums to total
        uint256 total = token.balanceOf(buildingWallet) + 
                        token.balanceOf(maintainerVault) + 
                        token.balanceOf(treasury);
        assertEq(total, amount);
    }

    function testFuzz_BatchPayment(uint8 count) public {
        // Bound to reasonable batch size
        count = uint8(bound(count, 1, 10));
        
        string[] memory buildingIds = new string[](count);
        uint256[] memory amounts = new uint256[](count);
        bytes32[] memory nonces = new bytes32[](count);
        
        for (uint256 i = 0; i < count; i++) {
            buildingIds[i] = BUILDING_ID;
            amounts[i] = 1 ether;
            nonces[i] = keccak256(abi.encodePacked("fuzz", i));
        }
        
        vm.prank(payer);
        router.batchPayForAccess(buildingIds, amounts, nonces);
        
        // Verify all nonces used
        for (uint256 i = 0; i < count; i++) {
            assertTrue(router.isNonceUsed(nonces[i]));
        }
    }
}
