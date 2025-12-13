// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/ArxAddresses.sol";

contract ArxAddressesTest is Test {
    ArxAddresses public addresses;
    address public owner;
    address public maintainerVault;
    address public treasury;

    event MaintainerVaultUpdated(address indexed oldVault, address indexed newVault);
    event TreasuryUpdated(address indexed oldTreasury, address indexed newTreasury);

    function setUp() public {
        owner = address(this);
        maintainerVault = makeAddr("maintainerVault");
        treasury = makeAddr("treasury");

        addresses = new ArxAddresses(owner, maintainerVault, treasury);
    }

    function test_Constructor() public {
        assertEq(addresses.owner(), owner);
        assertEq(addresses.maintainerVault(), maintainerVault);
        assertEq(addresses.treasury(), treasury);
    }

    function test_ConstructorRevertsOnZeroMaintainerVault() public {
        vm.expectRevert("ArxAddresses: zero maintainer vault");
        new ArxAddresses(owner, address(0), treasury);
    }

    function test_ConstructorRevertsOnZeroTreasury() public {
        vm.expectRevert("ArxAddresses: zero treasury");
        new ArxAddresses(owner, maintainerVault, address(0));
    }

    function test_SetMaintainerVault() public {
        address newVault = makeAddr("newVault");

        vm.expectEmit(true, true, false, false);
        emit MaintainerVaultUpdated(maintainerVault, newVault);

        addresses.setMaintainerVault(newVault);

        assertEq(addresses.maintainerVault(), newVault);
    }

    function test_SetMaintainerVaultRevertsOnZeroAddress() public {
        vm.expectRevert("ArxAddresses: zero address");
        addresses.setMaintainerVault(address(0));
    }

    function test_SetMaintainerVaultRevertsWhenNotOwner() public {
        address attacker = makeAddr("attacker");
        address newVault = makeAddr("newVault");

        vm.prank(attacker);
        vm.expectRevert(abi.encodeWithSignature("OwnableUnauthorizedAccount(address)", attacker));
        addresses.setMaintainerVault(newVault);
    }

    function test_SetTreasury() public {
        address newTreasury = makeAddr("newTreasury");

        vm.expectEmit(true, true, false, false);
        emit TreasuryUpdated(treasury, newTreasury);

        addresses.setTreasury(newTreasury);

        assertEq(addresses.treasury(), newTreasury);
    }

    function test_SetTreasuryRevertsOnZeroAddress() public {
        vm.expectRevert("ArxAddresses: zero address");
        addresses.setTreasury(address(0));
    }

    function test_SetTreasuryRevertsWhenNotOwner() public {
        address attacker = makeAddr("attacker");
        address newTreasury = makeAddr("newTreasury");

        vm.prank(attacker);
        vm.expectRevert(abi.encodeWithSignature("OwnableUnauthorizedAccount(address)", attacker));
        addresses.setTreasury(newTreasury);
    }

    function test_GetAddresses() public {
        (address _maintainer, address _treasury) = addresses.getAddresses();

        assertEq(_maintainer, maintainerVault);
        assertEq(_treasury, treasury);
    }

    function testFuzz_SetMaintainerVault(address newVault) public {
        vm.assume(newVault != address(0));

        addresses.setMaintainerVault(newVault);

        assertEq(addresses.maintainerVault(), newVault);
    }

    function testFuzz_SetTreasury(address newTreasury) public {
        vm.assume(newTreasury != address(0));

        addresses.setTreasury(newTreasury);

        assertEq(addresses.treasury(), newTreasury);
    }
}
