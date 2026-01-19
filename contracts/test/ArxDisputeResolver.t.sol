// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {ArxDisputeResolver} from "../src/ArxDisputeResolver.sol";
import {ArxContributionOracle} from "../src/ArxContributionOracle.sol";
import {ArxOracleStaking} from "../src/ArxOracleStaking.sol";
import {ArxosToken} from "../src/ArxosToken.sol";
import {ArxRegistry} from "../src/ArxRegistry.sol";
import {ArxAddresses} from "../src/ArxAddresses.sol";

contract ArxDisputeResolverTest is Test {
    ArxDisputeResolver public resolver;
    ArxContributionOracle public oracle;
    ArxOracleStaking public staking;
    ArxosToken public token;
    ArxRegistry public registry;
    ArxAddresses public addresses;
    
    address public admin = address(this);
    address public worker = address(0x10);
    address public buildingWallet = address(0x20);
    address public disputer = address(0x30);
    address public oracle1 = address(0x40);
    address public oracle2 = address(0x41);
    
    uint256 public constant STAKE_AMOUNT = 1000 ether;
    uint256 public constant BOND_AMOUNT = 500 ether;
    uint256 public constant CONTRIBUTION_AMOUNT = 100 ether;
    string public constant BUILDING_ID = "test-building";
    
    // EIP-712 Helpers
    bytes32 public constant CONTRIBUTION_PROOF_TYPEHASH = keccak256("ContributionProof(bytes32 merkleRoot,bytes32 locationHash,bytes32 buildingHash,uint256 timestamp,uint256 dataSize)");
    uint256 public workerPk = 0xA11CE;
    
    function setUp() public {
        // 1. Deploy Core
        addresses = new ArxAddresses(admin, admin, admin);
        token = new ArxosToken(admin);
        token.grantRole(token.MINTER_ROLE(), admin);
        
        registry = new ArxRegistry(admin);
        registry.registerBuilding(BUILDING_ID, buildingWallet);
        // Setup worker with PK
        worker = vm.addr(workerPk);
        registry.registerWorker(worker, "metadata");
        
        staking = new ArxOracleStaking(admin, address(token), STAKE_AMOUNT);
        
        oracle = new ArxContributionOracle(
            admin, 
            address(token), 
            address(registry), 
            address(addresses), 
            address(staking)
        );
        
        // 2. Deploy Resolver
        resolver = new ArxDisputeResolver(
            admin,
            address(token),
            address(oracle),
            address(staking)
        );
        
        // 3. Configure Permissions
        oracle.setResolver(address(resolver));
        
        token.grantRole(token.MINTER_ROLE(), address(oracle));
        
        // 4. Setup Oracles
        _setupOracle(oracle1);
        _setupOracle(oracle2);
        
        // 5. Setup Disputer
        token.mint(disputer, BOND_AMOUNT);
        vm.prank(disputer);
        token.approve(address(resolver), BOND_AMOUNT);
    }
    
    function _setupOracle(address _oracle) internal {
        token.mint(_oracle, STAKE_AMOUNT);
        oracle.grantRole(oracle.ORACLE_ROLE(), _oracle);
        vm.startPrank(_oracle);
        token.approve(address(staking), STAKE_AMOUNT);
        staking.stake(STAKE_AMOUNT);
        vm.stopPrank();
    }
    
    function _createContribution() internal returns (bytes32) {
        // Create proof
        ArxContributionOracle.ContributionProof memory proof = ArxContributionOracle.ContributionProof({
            merkleRoot: keccak256("root"),
            locationHash: keccak256("loc"),
            buildingHash: keccak256(bytes(BUILDING_ID)),
            timestamp: block.timestamp,
            dataSize: 100
        });
        
        bytes32 structHash = keccak256(abi.encode(
            CONTRIBUTION_PROOF_TYPEHASH,
            proof.merkleRoot,
            proof.locationHash,
            proof.buildingHash,
            proof.timestamp,
            proof.dataSize
        ));
        
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", oracle.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(workerPk, digest);
        bytes memory signature = abi.encodePacked(r, s, v);
        
        // Propose
        vm.prank(oracle1);
        oracle.proposeContribution(BUILDING_ID, worker, CONTRIBUTION_AMOUNT, proof, signature);
        
        // Confirm (need 2)
        vm.prank(oracle2);
        // We need to pass valid params to propose/confirm again if we want to confirm, 
        // but proposeContribution handles confirmation for sender.
        // To verify confirm logic, we just re-call propose with same data
        oracle.proposeContribution(BUILDING_ID, worker, CONTRIBUTION_AMOUNT, proof, signature);
        
        return keccak256(abi.encodePacked(BUILDING_ID, worker, CONTRIBUTION_AMOUNT));
    }
    
    function test_RaiseDispute() public {
        bytes32 id = _createContribution();
        
        vm.prank(disputer);
        resolver.raiseDispute(id, "Fake GPS Data");
        
        (bytes32 cid, address d, string memory reason,,,,,,) = resolver.disputes(id);
        
        assertEq(cid, id);
        assertEq(d, disputer);
        assertEq(reason, "Fake GPS Data");
        assertEq(token.balanceOf(disputer), 0); // Bond taken
        assertEq(token.balanceOf(address(resolver)), BOND_AMOUNT);
    }
    
    function test_RevertWhen_FinalizingDisputed() public {
        bytes32 id = _createContribution();
        
        vm.prank(disputer);
        resolver.raiseDispute(id, "Bad data");
        
        vm.warp(block.timestamp + 2 days); // Wait for delay
        
        vm.expectRevert("Contribution is disputed");
        oracle.finalizeContribution(id);
    }
    
    function test_ResolveDispute_ValidWorkerWins() public {
        bytes32 id = _createContribution();
        
        vm.prank(disputer);
        resolver.raiseDispute(id, "Bad data");
        
        // Vote VALID (true)
        // Oracle1 votes
        uint256 salt1 = 123;
        bytes32 commit1 = keccak256(abi.encodePacked(true, salt1));
        vm.prank(oracle1);
        resolver.commitVote(id, commit1);
        
        // Oracle2 votes
        uint256 salt2 = 456;
        bytes32 commit2 = keccak256(abi.encodePacked(true, salt2));
        vm.prank(oracle2);
        resolver.commitVote(id, commit2);
        
        // Reveal
        vm.prank(oracle1);
        resolver.revealVote(id, true, salt1);
        
        vm.prank(oracle2);
        resolver.revealVote(id, true, salt2);
        
        // Resolve (after window)
        vm.warp(block.timestamp + 49 hours);
        
        resolver.resolveDispute(id);
        
        // Check state
        (,,,,,ArxDisputeResolver.Ruling ruling,,,) = resolver.disputes(id);
        assertEq(uint(ruling), 1); // 1 = VALID
        
        // Check contribution finalized & minted
        (,,,,, bool finalized) = oracle.getContribution(id);
        assertTrue(finalized);
        assertEq(token.balanceOf(worker), (CONTRIBUTION_AMOUNT * 70) / 100);
    }
    
    function test_ResolveDispute_InvalidDisputerWins() public {
        bytes32 id = _createContribution();
        
        vm.prank(disputer);
        resolver.raiseDispute(id, "Bad data");
        
        // Vote INVALID (false)
        uint256 salt = 123;
        bytes32 commit = keccak256(abi.encodePacked(false, salt));
        
        vm.prank(oracle1);
        resolver.commitVote(id, commit);
        vm.prank(oracle2);
        resolver.commitVote(id, commit);
        
        vm.prank(oracle1);
        resolver.revealVote(id, false, salt);
        vm.prank(oracle2);
        resolver.revealVote(id, false, salt);
        
        vm.warp(block.timestamp + 49 hours);
        resolver.resolveDispute(id);
        
        // Bond returned
        assertEq(token.balanceOf(disputer), BOND_AMOUNT);
        
        // Contribution cancelled (finalized but no mint)
        (,,,,, bool finalized) = oracle.getContribution(id);
        assertTrue(finalized);
        assertEq(token.balanceOf(worker), 0);
    }
}
