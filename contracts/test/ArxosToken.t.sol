// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {ArxosToken} from "../src/ArxosToken.sol";

contract ArxosTokenTest is Test {
    ArxosToken public token;
    
    address public admin = address(this);
    address public minter = address(0x1);
    address public worker = address(0x2);
    address public building = address(0x3);
    address public maintainer = address(0x4);
    address public treasury = address(0x5);
    address public user1 = address(0x6);
    address public user2 = address(0x7);
    
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    
    event ContributionMinted(
        address indexed worker,
        address indexed building,
        address indexed maintainer,
        address treasury,
        uint256 totalAmount
    );
    event BatchMinted(address indexed minter, uint256 totalAmount, uint256 recipientCount);
    event TokensBurned(address indexed burner, uint256 amount);

    function setUp() public {
        token = new ArxosToken(admin);
        // Grant minter role to minter address
        token.grantRole(MINTER_ROLE, minter);
    }

    // ============ Constructor Tests ============

    function test_Constructor() public view {
        assertEq(token.name(), "ArxOS Token");
        assertEq(token.symbol(), "ARXO");
        assertEq(token.decimals(), 18);
        assertTrue(token.hasRole(token.DEFAULT_ADMIN_ROLE(), admin));
    }

    function test_RevertWhen_ConstructorWithZeroAdmin() public {
        vm.expectRevert("ArxosToken: zero admin");
        new ArxosToken(address(0));
    }

    // ============ Role Management Tests ============

    function test_GrantMinterRole() public {
        address newMinter = address(0x8);
        
        token.grantRole(MINTER_ROLE, newMinter);
        
        assertTrue(token.hasRole(MINTER_ROLE, newMinter));
    }

    function test_RevokeMinterRole() public {
        assertTrue(token.hasRole(MINTER_ROLE, minter));
        
        token.revokeRole(MINTER_ROLE, minter);
        
        assertFalse(token.hasRole(MINTER_ROLE, minter));
    }

    function test_RevertWhen_NonAdminGrantsRole() public {
        vm.prank(user1);
        vm.expectRevert();
        token.grantRole(MINTER_ROLE, user2);
    }

    // ============ Mint Tests ============

    function test_Mint() public {
        uint256 amount = 1000 ether;
        
        vm.prank(minter);
        token.mint(worker, amount);
        
        assertEq(token.balanceOf(worker), amount);
        assertEq(token.totalSupply(), amount);
    }

    function test_MintMultipleTimes() public {
        vm.startPrank(minter);
        
        token.mint(worker, 1000 ether);
        token.mint(worker, 500 ether);
        token.mint(building, 250 ether);
        
        vm.stopPrank();
        
        assertEq(token.balanceOf(worker), 1500 ether);
        assertEq(token.balanceOf(building), 250 ether);
        assertEq(token.totalSupply(), 1750 ether);
    }

    function test_RevertWhen_NonMinterMints() public {
        vm.prank(user1);
        vm.expectRevert();
        token.mint(worker, 1000 ether);
    }

    function test_RevertWhen_MintToZeroAddress() public {
        vm.prank(minter);
        vm.expectRevert("ArxosToken: zero address");
        token.mint(address(0), 1000 ether);
    }

    function test_RevertWhen_MintZeroAmount() public {
        vm.prank(minter);
        vm.expectRevert("ArxosToken: zero amount");
        token.mint(worker, 0);
    }

    // ============ Batch Mint Tests ============

    function test_MintBatch() public {
        address[] memory recipients = new address[](4);
        recipients[0] = worker;
        recipients[1] = building;
        recipients[2] = maintainer;
        recipients[3] = treasury;
        
        uint256[] memory amounts = new uint256[](4);
        amounts[0] = 700 ether;
        amounts[1] = 100 ether;
        amounts[2] = 100 ether;
        amounts[3] = 100 ether;
        
        vm.expectEmit(true, false, false, true);
        emit BatchMinted(minter, 1000 ether, 4);
        
        vm.prank(minter);
        token.mintBatch(recipients, amounts);
        
        assertEq(token.balanceOf(worker), 700 ether);
        assertEq(token.balanceOf(building), 100 ether);
        assertEq(token.balanceOf(maintainer), 100 ether);
        assertEq(token.balanceOf(treasury), 100 ether);
        assertEq(token.totalSupply(), 1000 ether);
    }

    function test_RevertWhen_BatchMintLengthMismatch() public {
        address[] memory recipients = new address[](3);
        uint256[] memory amounts = new uint256[](4);
        
        vm.prank(minter);
        vm.expectRevert("ArxosToken: length mismatch");
        token.mintBatch(recipients, amounts);
    }

    function test_RevertWhen_BatchMintEmptyArrays() public {
        address[] memory recipients = new address[](0);
        uint256[] memory amounts = new uint256[](0);
        
        vm.prank(minter);
        vm.expectRevert("ArxosToken: empty arrays");
        token.mintBatch(recipients, amounts);
    }

    function test_RevertWhen_BatchMintContainsZeroAddress() public {
        address[] memory recipients = new address[](2);
        recipients[0] = worker;
        recipients[1] = address(0);
        
        uint256[] memory amounts = new uint256[](2);
        amounts[0] = 500 ether;
        amounts[1] = 500 ether;
        
        vm.prank(minter);
        vm.expectRevert("ArxosToken: zero address");
        token.mintBatch(recipients, amounts);
    }

    function test_RevertWhen_BatchMintContainsZeroAmount() public {
        address[] memory recipients = new address[](2);
        recipients[0] = worker;
        recipients[1] = building;
        
        uint256[] memory amounts = new uint256[](2);
        amounts[0] = 500 ether;
        amounts[1] = 0;
        
        vm.prank(minter);
        vm.expectRevert("ArxosToken: zero amount");
        token.mintBatch(recipients, amounts);
    }

    // ============ Contribution Mint Tests (70/10/10/10) ============

    function test_MintContribution() public {
        uint256 totalAmount = 1000 ether;
        
        vm.expectEmit(true, true, true, true);
        emit ContributionMinted(worker, building, maintainer, treasury, totalAmount);
        
        vm.prank(minter);
        token.mintContribution(worker, building, maintainer, treasury, totalAmount);
        
        // Verify 70/10/10/10 split
        assertEq(token.balanceOf(worker), 700 ether);
        assertEq(token.balanceOf(building), 100 ether);
        assertEq(token.balanceOf(maintainer), 100 ether);
        assertEq(token.balanceOf(treasury), 100 ether);
        assertEq(token.totalSupply(), 1000 ether);
        assertEq(token.totalContributedValue(), 1000 ether);
    }

    function test_MintContributionMultipleTimes() public {
        vm.startPrank(minter);
        
        token.mintContribution(worker, building, maintainer, treasury, 1000 ether);
        token.mintContribution(worker, building, maintainer, treasury, 500 ether);
        
        vm.stopPrank();
        
        // Worker gets 70% of 1500 = 1050
        assertEq(token.balanceOf(worker), 1050 ether);
        // Building gets 10% of 1500 = 150
        assertEq(token.balanceOf(building), 150 ether);
        assertEq(token.totalSupply(), 1500 ether);
        assertEq(token.totalContributedValue(), 1500 ether);
    }

    function test_MintContribution_RoundingHandling() public {
        // Test with amount that doesn't divide evenly by 100
        uint256 totalAmount = 1001 ether;
        
        vm.prank(minter);
        token.mintContribution(worker, building, maintainer, treasury, totalAmount);
        
        uint256 workerAmount = (totalAmount * 70) / 100; // 700.7 -> 700 ether
        uint256 buildingAmount = (totalAmount * 10) / 100; // 100.1 -> 100 ether
        uint256 maintainerAmount = (totalAmount * 10) / 100; // 100.1 -> 100 ether
        
        assertEq(token.balanceOf(worker), workerAmount);
        assertEq(token.balanceOf(building), buildingAmount);
        assertEq(token.balanceOf(maintainer), maintainerAmount);
        
        // Treasury gets remainder to ensure total is exact
        uint256 treasuryAmount = totalAmount - workerAmount - buildingAmount - maintainerAmount;
        assertEq(token.balanceOf(treasury), treasuryAmount);
        assertEq(token.totalSupply(), totalAmount);
    }

    function test_RevertWhen_MintContributionZeroWorker() public {
        vm.prank(minter);
        vm.expectRevert("ArxosToken: zero worker");
        token.mintContribution(address(0), building, maintainer, treasury, 1000 ether);
    }

    function test_RevertWhen_MintContributionZeroBuilding() public {
        vm.prank(minter);
        vm.expectRevert("ArxosToken: zero building");
        token.mintContribution(worker, address(0), maintainer, treasury, 1000 ether);
    }

    function test_RevertWhen_MintContributionZeroMaintainer() public {
        vm.prank(minter);
        vm.expectRevert("ArxosToken: zero maintainer");
        token.mintContribution(worker, building, address(0), treasury, 1000 ether);
    }

    function test_RevertWhen_MintContributionZeroTreasury() public {
        vm.prank(minter);
        vm.expectRevert("ArxosToken: zero treasury");
        token.mintContribution(worker, building, maintainer, address(0), 1000 ether);
    }

    function test_RevertWhen_MintContributionZeroAmount() public {
        vm.prank(minter);
        vm.expectRevert("ArxosToken: zero amount");
        token.mintContribution(worker, building, maintainer, treasury, 0);
    }

    // ============ Burn Tests ============

    function test_Burn() public {
        // Mint tokens first
        vm.prank(minter);
        token.mint(worker, 1000 ether);
        
        // Burn tokens
        vm.expectEmit(true, false, false, true);
        emit TokensBurned(worker, 500 ether);
        
        vm.prank(worker);
        token.burn(500 ether);
        
        assertEq(token.balanceOf(worker), 500 ether);
        assertEq(token.totalSupply(), 500 ether);
    }

    function test_BurnAll() public {
        vm.prank(minter);
        token.mint(worker, 1000 ether);
        
        vm.prank(worker);
        token.burn(1000 ether);
        
        assertEq(token.balanceOf(worker), 0);
        assertEq(token.totalSupply(), 0);
    }

    function test_RevertWhen_BurnMoreThanBalance() public {
        vm.prank(minter);
        token.mint(worker, 1000 ether);
        
        vm.prank(worker);
        vm.expectRevert();
        token.burn(1001 ether);
    }

    function test_RevertWhen_BurnZeroAmount() public {
        vm.prank(worker);
        vm.expectRevert("ArxosToken: zero amount");
        token.burn(0);
    }

    // ============ BurnFrom Tests ============

    function test_BurnFrom() public {
        // Mint and approve
        vm.prank(minter);
        token.mint(worker, 1000 ether);
        
        vm.prank(worker);
        token.approve(user1, 500 ether);
        
        // Burn from
        vm.expectEmit(true, false, false, true);
        emit TokensBurned(worker, 500 ether);
        
        vm.prank(user1);
        token.burnFrom(worker, 500 ether);
        
        assertEq(token.balanceOf(worker), 500 ether);
        assertEq(token.totalSupply(), 500 ether);
        assertEq(token.allowance(worker, user1), 0);
    }

    function test_RevertWhen_BurnFromWithoutAllowance() public {
        vm.prank(minter);
        token.mint(worker, 1000 ether);
        
        vm.prank(user1);
        vm.expectRevert();
        token.burnFrom(worker, 500 ether);
    }

    function test_RevertWhen_BurnFromExceedsAllowance() public {
        vm.prank(minter);
        token.mint(worker, 1000 ether);
        
        vm.prank(worker);
        token.approve(user1, 400 ether);
        
        vm.prank(user1);
        vm.expectRevert();
        token.burnFrom(worker, 500 ether);
    }

    function test_RevertWhen_BurnFromZeroAmount() public {
        vm.prank(user1);
        vm.expectRevert("ArxosToken: zero amount");
        token.burnFrom(worker, 0);
    }

    // ============ ERC20 Compliance Tests ============

    function test_Transfer() public {
        vm.prank(minter);
        token.mint(worker, 1000 ether);
        
        vm.prank(worker);
        token.transfer(user1, 300 ether);
        
        assertEq(token.balanceOf(worker), 700 ether);
        assertEq(token.balanceOf(user1), 300 ether);
    }

    function test_Approve() public {
        vm.prank(worker);
        token.approve(user1, 500 ether);
        
        assertEq(token.allowance(worker, user1), 500 ether);
    }

    function test_TransferFrom() public {
        vm.prank(minter);
        token.mint(worker, 1000 ether);
        
        vm.prank(worker);
        token.approve(user1, 500 ether);
        
        vm.prank(user1);
        token.transferFrom(worker, user2, 300 ether);
        
        assertEq(token.balanceOf(worker), 700 ether);
        assertEq(token.balanceOf(user2), 300 ether);
        assertEq(token.allowance(worker, user1), 200 ether);
    }

    // ============ Fuzz Tests ============

    function testFuzz_Mint(address recipient, uint256 amount) public {
        vm.assume(recipient != address(0));
        vm.assume(amount > 0 && amount < type(uint128).max); // Prevent overflow
        
        vm.prank(minter);
        token.mint(recipient, amount);
        
        assertEq(token.balanceOf(recipient), amount);
        assertEq(token.totalSupply(), amount);
    }

    function testFuzz_MintContribution(uint256 amount) public {
        vm.assume(amount > 0 && amount < type(uint128).max);
        
        vm.prank(minter);
        token.mintContribution(worker, building, maintainer, treasury, amount);
        
        uint256 workerAmount = (amount * 70) / 100;
        uint256 buildingAmount = (amount * 10) / 100;
        uint256 maintainerAmount = (amount * 10) / 100;
        uint256 treasuryAmount = amount - workerAmount - buildingAmount - maintainerAmount;
        
        assertEq(token.balanceOf(worker), workerAmount);
        assertEq(token.balanceOf(building), buildingAmount);
        assertEq(token.balanceOf(maintainer), maintainerAmount);
        assertEq(token.balanceOf(treasury), treasuryAmount);
        assertEq(token.totalSupply(), amount);
    }

    function testFuzz_Burn(uint256 mintAmount, uint256 burnAmount) public {
        vm.assume(mintAmount > 0 && mintAmount < type(uint128).max);
        vm.assume(burnAmount > 0 && burnAmount <= mintAmount);
        
        vm.prank(minter);
        token.mint(worker, mintAmount);
        
        vm.prank(worker);
        token.burn(burnAmount);
        
        assertEq(token.balanceOf(worker), mintAmount - burnAmount);
        assertEq(token.totalSupply(), mintAmount - burnAmount);
    }
}
