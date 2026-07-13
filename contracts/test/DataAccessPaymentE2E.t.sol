// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title DataAccessPaymentE2E
 * @notice Vision path: free software maps buildings; buyers pay $AXD for data access.
 *
 * Flow:
 *   1. Register building (UUID) + fund buyer with $AXD
 *   2. Buyer payForAccess(buildingId, amount, nonce, maxPrice)
 *   3. Split: 70% building owner / 10% maintainers / 20% treasury (remainder)
 *   4. Replay nonce fails; unregistered building fails
 */

import {Test} from "forge-std/Test.sol";
import {ArxPaymentRouter} from "../src/ArxPaymentRouter.sol";
import {ArxosToken} from "../src/ArxosToken.sol";
import {ArxRegistry} from "../src/ArxRegistry.sol";
import {ArxAddresses} from "../src/ArxAddresses.sol";

contract DataAccessPaymentE2E is Test {
    ArxPaymentRouter public router;
    ArxosToken public token;
    ArxRegistry public registry;
    ArxAddresses public addresses;

    address public owner = address(this);
    address public buyer = vm.addr(0xBEE1);
    address public buildingOwner = vm.addr(0xB002);
    address public maintainerVault = vm.addr(0xD002);
    address public treasury = vm.addr(0xE002);

    /// @dev Same UUID style as Building.id / contribution package building_id
    string constant BUILDING_UUID = "8ffa4c60-92a3-4e6e-b8e6-606ec923b3b5";

    function setUp() public {
        addresses = new ArxAddresses(owner, maintainerVault, treasury);
        token = new ArxosToken(owner);
        registry = new ArxRegistry(owner);
        router = new ArxPaymentRouter(
            owner, address(token), address(registry), address(addresses)
        );

        registry.registerBuilding(BUILDING_UUID, buildingOwner);

        token.grantRole(token.MINTER_ROLE(), owner);
        token.mint(buyer, 10_000 ether);

        vm.prank(buyer);
        token.approve(address(router), type(uint256).max);
    }

    function test_E2E_BuyerPaysAxdForBuildingDataAccess() public {
        uint256 price = 1 ether; // 1 $AXD
        bytes32 nonce = keccak256(abi.encodePacked("access-nonce-1", BUILDING_UUID, buyer));

        uint256 buyerBefore = token.balanceOf(buyer);
        uint256 b0 = token.balanceOf(buildingOwner);
        uint256 m0 = token.balanceOf(maintainerVault);
        uint256 t0 = token.balanceOf(treasury);

        vm.prank(buyer);
        router.payForAccess(BUILDING_UUID, price, nonce, price);

        // Buyer spent AXD
        assertEq(token.balanceOf(buyer), buyerBefore - price);

        // Building twin fund gets majority of access payment (70%)
        assertEq(token.balanceOf(buildingOwner), b0 + (price * 70) / 100);
        assertEq(token.balanceOf(maintainerVault), m0 + (price * 10) / 100);
        // Treasury gets remainder (20% when exact)
        assertEq(token.balanceOf(treasury), t0 + (price * 20) / 100);

        assertTrue(router.isNonceUsed(nonce));

        // Replay protection
        vm.prank(buyer);
        vm.expectRevert("ArxPaymentRouter: nonce already used");
        router.payForAccess(BUILDING_UUID, price, nonce, price);
    }

    function test_E2E_AccessRequiresRegisteredBuildingUuid() public {
        bytes32 nonce = keccak256("unregistered");
        vm.prank(buyer);
        vm.expectRevert("ArxPaymentRouter: building not registered");
        router.payForAccess("00000000-0000-0000-0000-000000000000", 1 ether, nonce, 1 ether);
    }

    function test_E2E_AccessRespectsMinimumPrice() public {
        // Price increases are timelocked (7 days) — schedule then warp
        router.setMinimumPayment(BUILDING_UUID, 5 ether);
        vm.warp(block.timestamp + 7 days + 1);
        router.applyPriceUpdate(BUILDING_UUID);
        assertEq(router.getMinimumPayment(BUILDING_UUID), 5 ether);

        bytes32 nonce = keccak256("too-low");
        vm.prank(buyer);
        vm.expectRevert("ArxPaymentRouter: insufficient amount");
        router.payForAccess(BUILDING_UUID, 1 ether, nonce, 10 ether);

        bytes32 nonce2 = keccak256("ok-price");
        vm.prank(buyer);
        router.payForAccess(BUILDING_UUID, 5 ether, nonce2, 5 ether);
        assertEq(token.balanceOf(buildingOwner), (5 ether * 70) / 100);
    }
}
