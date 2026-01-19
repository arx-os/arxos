// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {ArxContributionOracle} from "../src/ArxContributionOracle.sol";
import {ArxosToken} from "../src/ArxosToken.sol";
import {ArxRegistry} from "../src/ArxRegistry.sol";
import {ArxAddresses} from "../src/ArxAddresses.sol";
import {ArxOracleStaking} from "../src/ArxOracleStaking.sol";

contract ArxContributionTest is Test {
    ArxContributionOracle public oracle;
    ArxosToken public token;
    ArxRegistry public registry;
    ArxAddresses public addresses;
    ArxOracleStaking public staking;
    
    address public owner = address(this);
    address public oracle1 = vm.addr(0x101);
    address public oracle2 = vm.addr(0x102);
    address public oracle3 = vm.addr(0x103);
    address public worker1 = vm.addr(0x201);  // Derive from private key
    address public buildingWallet = address(0x301);
    address public maintainerVault = address(0x401);
    address public treasury = address(0x501);
    
    uint256 constant ORACLE1_KEY = 0x101;
    uint256 constant ORACLE2_KEY = 0x102;
    uint256 constant ORACLE3_KEY = 0x103;
    uint256 constant WORKER1_KEY = 0x201;  // Private key for worker1
    
    string constant BUILDING_ID = "ps-118";
    string constant WORKER_METADATA = "ipfs://QmWorker1";
    
    bytes32 constant MERKLE_ROOT = keccak256("merkle_root");
    bytes32 constant LOCATION_HASH = keccak256("location_hash");
    bytes32 constant BUILDING_HASH = keccak256("building_hash");
    uint256 constant DATA_SIZE = 1000000;
    
    event ContributionProposed(
        bytes32 indexed contributionId,
        address indexed worker,
        string buildingId,
        uint256 amount,
        address oracle
    );
    
    event ContributionConfirmed(
        bytes32 indexed contributionId,
        address indexed oracle,
        uint256 confirmations
    );
    
    event ContributionFinalized(
        bytes32 indexed contributionId,
        address indexed worker,
        uint256 amount
    );
    
    event ContributionDisputed(
        bytes32 indexed contributionId,
        address indexed oracle,
        string reason
    );

    function setUp() public {
        // Deploy core contracts
        addresses = new ArxAddresses(owner, maintainerVault, treasury);
        registry = new ArxRegistry(owner);
        token = new ArxosToken(owner);  // owner is the admin
        staking = new ArxOracleStaking(owner, address(token), 1000 ether);
        oracle = new ArxContributionOracle(
            owner,
            address(token),
            address(registry),
            address(addresses),
            address(staking)
        );
        
        // Grant MINTER_ROLE to oracle (as token owner)
        vm.startPrank(owner);
        token.grantRole(token.MINTER_ROLE(), address(oracle));
        
        // Grant ORACLE_ROLE and stake for three oracles
        oracle.grantRole(oracle.ORACLE_ROLE(), oracle1);
        oracle.grantRole(oracle.ORACLE_ROLE(), oracle2);
        oracle.grantRole(oracle.ORACLE_ROLE(), oracle3);
        
        token.grantRole(token.MINTER_ROLE(), owner);
        token.mint(oracle1, 2000 ether);
        token.mint(oracle2, 2000 ether);
        token.mint(oracle3, 2000 ether);
        
        vm.stopPrank();
        
        vm.prank(oracle1);
        token.approve(address(staking), 1000 ether);
        vm.prank(oracle1);
        staking.stake(1000 ether);
        
        vm.prank(oracle2);
        token.approve(address(staking), 1000 ether);
        vm.prank(oracle2);
        staking.stake(1000 ether);
        
        vm.prank(oracle3);
        token.approve(address(staking), 1000 ether);
        vm.prank(oracle3);
        staking.stake(1000 ether);
        
        vm.startPrank(owner);
        
        // Register worker and building
        registry.registerWorker(worker1, WORKER_METADATA);
        registry.registerBuilding(BUILDING_ID, buildingWallet);
        vm.stopPrank();
    }

    // ============ Helper Functions ============

    function createProof(uint256 timestamp) internal pure returns (ArxContributionOracle.ContributionProof memory) {
        return ArxContributionOracle.ContributionProof({
            merkleRoot: MERKLE_ROOT,
            locationHash: LOCATION_HASH,
            buildingHash: BUILDING_HASH,
            timestamp: timestamp,
            dataSize: DATA_SIZE
        });
    }

    function signProof(
        ArxContributionOracle.ContributionProof memory proof,
        uint256 privateKey
    ) internal view returns (bytes memory) {
        // Build EIP-712 struct hash
        bytes32 structHash = keccak256(abi.encode(
            oracle.CONTRIBUTION_PROOF_TYPEHASH(),
            proof.merkleRoot,
            proof.locationHash,
            proof.buildingHash,
            proof.timestamp,
            proof.dataSize
        ));
        
        // Build EIP-712 domain separator manually
        bytes32 domainSeparator = keccak256(abi.encode(
            keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
            keccak256("ArxOS Contribution Oracle"),
            keccak256("1"),
            block.chainid,
            address(oracle)
        ));
        
        // Build final digest
        bytes32 digest = keccak256(abi.encodePacked(
            "\x19\x01",
            domainSeparator,
            structHash
        ));
        
        // Sign with vm.sign
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(privateKey, digest);
        return abi.encodePacked(r, s, v);
    }

    function calculateContributionId(
        string memory buildingId,
        address worker,
        uint256 amount,
        ArxContributionOracle.ContributionProof memory proof
    ) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(buildingId, worker, amount));
    }

    // ============ Constructor Tests ============

    function test_Constructor() public view {
        assertEq(address(oracle.arxoToken()), address(token));
        assertEq(address(oracle.registry()), address(registry));
        assertEq(address(oracle.addresses()), address(addresses));
        assertEq(oracle.MIN_CONFIRMATIONS(), 2);
        assertEq(oracle.FINALIZATION_DELAY(), 24 hours);
        assertEq(oracle.MAX_PROOF_AGE(), 1 hours);
    }

    function test_RoleConfiguration() public view {
        // Verify oracle roles are set up correctly
        assertTrue(oracle.hasRole(oracle.ORACLE_ROLE(), oracle1));
        assertTrue(oracle.hasRole(oracle.ORACLE_ROLE(), oracle2));
        assertTrue(oracle.hasRole(oracle.ORACLE_ROLE(), oracle3));
        assertTrue(oracle.hasRole(oracle.DEFAULT_ADMIN_ROLE(), owner));
    }

    // ============ Propose Contribution Tests ============

    function test_ProposeContribution() public {
        uint256 amount = 1000 ether;
        uint256 timestamp = block.timestamp;
        ArxContributionOracle.ContributionProof memory proof = createProof(timestamp);
        bytes memory signature = signProof(proof, WORKER1_KEY);
        
        bytes32 contributionId = calculateContributionId(BUILDING_ID, worker1, amount, proof);
        
        vm.expectEmit(true, true, false, true);
        emit ContributionProposed(contributionId, worker1, BUILDING_ID, amount, oracle1);
        
        vm.prank(oracle1);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            amount,
            proof,
            signature
        );
        
        // Verify contribution state
        (
            address storedWorker,
            address storedBuilding,
            uint256 storedAmount,
            uint256 confirmations,
            uint256 proposedAt,
            bool finalized
        ) = oracle.getContribution(contributionId);
        
        assertEq(storedWorker, worker1);
        assertEq(storedBuilding, buildingWallet);
        assertEq(storedAmount, amount);
        assertEq(confirmations, 1);
        assertEq(proposedAt, timestamp);
        assertFalse(finalized);
    }

    function test_ConfirmContribution() public {
        uint256 amount = 1000 ether;
        uint256 timestamp = block.timestamp;
        ArxContributionOracle.ContributionProof memory proof1 = createProof(timestamp);
        ArxContributionOracle.ContributionProof memory proof2 = createProof(timestamp + 1);
        
        // Oracle 1 proposes
        bytes memory sig1 = signProof(proof1, WORKER1_KEY); 
        bytes32 contributionId = calculateContributionId(BUILDING_ID, worker1, amount, proof1);

        vm.prank(oracle1);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            amount,
            proof1,
            sig1
        );
        
        // Oracle 2 confirms with different proof
        bytes memory sig2 = signProof(proof2, WORKER1_KEY);
        
        vm.expectEmit(true, true, false, true);
        emit ContributionConfirmed(contributionId, oracle2, 2);
        
        vm.prank(oracle2);
        oracle.proposeContribution(BUILDING_ID, worker1, amount, proof2, sig2);
        
        // Verify confirmations increased
        (, , , uint256 confirmations, ,) = oracle.getContribution(contributionId);
        assertEq(confirmations, 2);
    }

    function test_RevertWhen_NonOracleProposes() public {
        ArxContributionOracle.ContributionProof memory proof = createProof(block.timestamp);
        bytes memory signature = signProof(proof, WORKER1_KEY);
        
        vm.prank(worker1);
        vm.expectRevert();
        oracle.proposeContribution(BUILDING_ID, worker1, 1000 ether, proof, signature);
    }

    function test_RevertWhen_InvalidSignature() public {
        ArxContributionOracle.ContributionProof memory proof = createProof(block.timestamp);
        bytes memory badSignature = new bytes(65);
        
        vm.prank(oracle1);
        vm.expectRevert("ArxContributionOracle: invalid signature");
        oracle.proposeContribution(BUILDING_ID, worker1, 1000 ether, proof, badSignature);
    }

    function test_RevertWhen_WorkerNotActive() public {
        address inactiveWorker = address(0x999);
        ArxContributionOracle.ContributionProof memory proof = createProof(block.timestamp);
        bytes memory signature = signProof(proof, WORKER1_KEY);
        
        vm.prank(oracle1);
        vm.expectRevert("ArxContributionOracle: worker not active");
        oracle.proposeContribution(BUILDING_ID, inactiveWorker, 1000 ether, proof, signature);
    }

    function test_RevertWhen_BuildingNotRegistered() public {
        ArxContributionOracle.ContributionProof memory proof = createProof(block.timestamp);
        bytes memory signature = signProof(proof, WORKER1_KEY);
        
        vm.prank(oracle1);
        vm.expectRevert("Building not registered");
        oracle.proposeContribution("unknown-building", worker1, 1000 ether, proof, signature);
    }

    function test_RevertWhen_ProofAlreadyUsed() public {
        ArxContributionOracle.ContributionProof memory proof = createProof(block.timestamp);
        bytes memory signature = signProof(proof, WORKER1_KEY);
        
        vm.prank(oracle1);
        oracle.proposeContribution(BUILDING_ID, worker1, 1000 ether, proof, signature);
        
        // Try to use same proof again with different oracle
        bytes memory sig2 = signProof(proof, WORKER1_KEY);
        vm.prank(oracle2);
        vm.expectRevert("ArxContributionOracle: proof already used");
        oracle.proposeContribution(BUILDING_ID, worker1, 1000 ether, proof, sig2);
    }

    function test_RevertWhen_OracleConfirmsTwice() public {
        ArxContributionOracle.ContributionProof memory proof = createProof(block.timestamp);
        bytes memory signature = signProof(proof, WORKER1_KEY);
        
        vm.prank(oracle1);
        oracle.proposeContribution(BUILDING_ID, worker1, 1000 ether, proof, signature);
        
        // Same oracle tries to confirm again
        vm.prank(oracle1);
        vm.expectRevert("ArxContributionOracle: already confirmed");
        oracle.proposeContribution(BUILDING_ID, worker1, 1000 ether, proof, signature);
    }

    // ============ Finalization Tests ============

    function test_FinalizeContribution() public {
        uint256 amount = 1000 ether;
        uint256 timestamp = block.timestamp;
        
        // Oracle 1 proposes with first proof
        ArxContributionOracle.ContributionProof memory proof1 = createProof(timestamp);
        bytes memory sig1 = signProof(proof1, WORKER1_KEY);
        bytes32 contributionId = calculateContributionId(BUILDING_ID, worker1, amount, proof1);
        
        vm.prank(oracle1);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            amount,
            proof1,
            sig1
        );
        
        // Oracle 2 confirms with different proof (different timestamp to avoid replay)
        ArxContributionOracle.ContributionProof memory proof2 = createProof(timestamp + 1);
        bytes memory sig2 = signProof(proof2, WORKER1_KEY);
        
        vm.prank(oracle2);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            amount,
            proof2,
            sig2
        );
        
        // Fast forward past delay
        vm.warp(timestamp + 24 hours + 1);
        
        uint256 workerBalanceBefore = token.balanceOf(worker1);
        uint256 buildingBalanceBefore = token.balanceOf(buildingWallet);
        uint256 maintainerBalanceBefore = token.balanceOf(maintainerVault);
        uint256 treasuryBalanceBefore = token.balanceOf(treasury);
        
        vm.expectEmit(true, true, false, true);
        emit ContributionFinalized(contributionId, worker1, amount);
        
        oracle.finalizeContribution(contributionId);
        
        // Verify 70/10/10/10 distribution
        assertEq(token.balanceOf(worker1), workerBalanceBefore + (amount * 70 / 100));
        assertEq(token.balanceOf(buildingWallet), buildingBalanceBefore + (amount * 10 / 100));
        assertEq(token.balanceOf(maintainerVault), maintainerBalanceBefore + (amount * 10 / 100));
        assertEq(token.balanceOf(treasury), treasuryBalanceBefore + (amount * 10 / 100));
        
        // Verify finalized state
        (, , , , , bool finalized) = oracle.getContribution(contributionId);
        assertTrue(finalized);
    }

    function test_RevertWhen_FinalizeBeforeDelay() public {
        ArxContributionOracle.ContributionProof memory proof1 = createProof(block.timestamp);
        ArxContributionOracle.ContributionProof memory proof2 = createProof(block.timestamp + 1);
        bytes memory signature1 = signProof(proof1, WORKER1_KEY);
        bytes memory signature2 = signProof(proof2, WORKER1_KEY);
        bytes32 contributionId = calculateContributionId(BUILDING_ID, worker1, 1000 ether, proof1);
        
        vm.prank(oracle1);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            1000 ether,
            proof1,
            signature1
        );
        
        vm.prank(oracle2);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            1000 ether,
            proof2,
            signature2
        );
        
        // Try to finalize before delay
        vm.warp(block.timestamp + 12 hours);
        
        vm.expectRevert("ArxContributionOracle: finalization delay not met");
        oracle.finalizeContribution(contributionId);
    }

    function test_RevertWhen_FinalizeWithoutConsensus() public {
        ArxContributionOracle.ContributionProof memory proof = createProof(block.timestamp);
        bytes memory signature = signProof(proof, WORKER1_KEY);
        bytes32 contributionId = calculateContributionId(BUILDING_ID, worker1, 1000 ether, proof);
        
        vm.prank(oracle1);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            1000 ether,
            proof,
            signature
        );
        
        vm.warp(block.timestamp + 24 hours + 1);
        
        vm.expectRevert("ArxContributionOracle: insufficient confirmations");
        oracle.finalizeContribution(contributionId);
    }

    function test_RevertWhen_FinalizeAlreadyFinalized() public {
        ArxContributionOracle.ContributionProof memory proof1 = createProof(block.timestamp);
        ArxContributionOracle.ContributionProof memory proof2 = createProof(block.timestamp + 1);
        bytes memory signature1 = signProof(proof1, WORKER1_KEY);
        bytes memory signature2 = signProof(proof2, WORKER1_KEY);
        bytes32 contributionId = calculateContributionId(BUILDING_ID, worker1, 1000 ether, proof1);
        
        vm.prank(oracle1);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            1000 ether,
            proof1,
            signature1
        );
        
        vm.prank(oracle2);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            1000 ether,
            proof2,
            signature2
        );
        
        vm.warp(block.timestamp + 24 hours + 1);
        oracle.finalizeContribution(contributionId);
        
        vm.expectRevert("Already finalized");
        oracle.finalizeContribution(contributionId);
    }

    // ============ Dispute Tests ============

    function test_DisputeContribution() public {
        ArxContributionOracle.ContributionProof memory proof = createProof(block.timestamp);
        bytes memory signature = signProof(proof, WORKER1_KEY);
        bytes32 contributionId = calculateContributionId(BUILDING_ID, worker1, 1000 ether, proof);
        
        vm.prank(oracle1);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            1000 ether,
            proof,
            signature
        );
        
        string memory reason = "Invalid data";
        
        vm.expectEmit(true, true, false, true);
        emit ContributionDisputed(contributionId, oracle2, reason);
        
        vm.prank(oracle2);
        oracle.disputeContribution(contributionId, reason);
        
        // Verify contribution is marked as disputed
        (, , , , , bool finalized) = oracle.getContribution(contributionId);
        assertFalse(finalized);
    }

    function test_RevertWhen_NonOracleDisputes() public {
        ArxContributionOracle.ContributionProof memory proof = createProof(block.timestamp);
        bytes memory signature = signProof(proof, WORKER1_KEY);
        bytes32 contributionId = calculateContributionId(BUILDING_ID, worker1, 1000 ether, proof);
        
        vm.prank(oracle1);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            1000 ether,
            proof,
            signature
        );
        
        vm.prank(worker1);
        vm.expectRevert();
        oracle.disputeContribution(contributionId, "reason");
    }

    function test_RevertWhen_DisputeAfterFinalization() public {
        ArxContributionOracle.ContributionProof memory proof1 = createProof(block.timestamp);
        ArxContributionOracle.ContributionProof memory proof2 = createProof(block.timestamp + 1);
        bytes memory signature1 = signProof(proof1, WORKER1_KEY);
        bytes memory signature2 = signProof(proof2, WORKER1_KEY);
        bytes32 contributionId = calculateContributionId(BUILDING_ID, worker1, 1000 ether, proof1);
        
        vm.prank(oracle1);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            1000 ether,
            proof1,
            signature1
        );
        
        vm.prank(oracle2);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            1000 ether,
            proof2,
            signature2
        );
        
        vm.warp(block.timestamp + 24 hours + 1);
        oracle.finalizeContribution(contributionId);
        
        vm.prank(oracle3);
        vm.expectRevert("Already finalized");
        oracle.disputeContribution(contributionId, "too late");
    }

    // ============ Three Oracle Consensus Tests ============

    function test_ThreeOracleConsensus() public {
        uint256 amount = 5000 ether;
        ArxContributionOracle.ContributionProof memory proof1 = createProof(block.timestamp);
        ArxContributionOracle.ContributionProof memory proof2 = createProof(block.timestamp + 1);
        ArxContributionOracle.ContributionProof memory proof3 = createProof(block.timestamp + 2);
        
        bytes memory signature1 = signProof(proof1, WORKER1_KEY);
        bytes memory signature2 = signProof(proof2, WORKER1_KEY);
        bytes memory signature3 = signProof(proof3, WORKER1_KEY);
        
        bytes32 contributionId = calculateContributionId(BUILDING_ID, worker1, amount, proof1);
        
        // All three oracles confirm with distinct proofs
        vm.prank(oracle1);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            amount,
            proof1,
            signature1
        );
        
        vm.prank(oracle2);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            amount,
            proof2,
            signature2
        );
        
        vm.prank(oracle3);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            amount,
            proof3,
            signature3
        );
        
        // Verify 3 confirmations
        (, , , uint256 confirmations, ,) = oracle.getContribution(contributionId);
        assertEq(confirmations, 3);
        
        // Should still be able to finalize
        vm.warp(block.timestamp + 24 hours + 1);
        oracle.finalizeContribution(contributionId);
        
        (, , , , , bool finalized) = oracle.getContribution(contributionId);
        assertTrue(finalized);
    }

    // ============ Edge Case Tests ============

    function test_MultipleContributionsSameBuilding() public {
        uint256 timestamp = block.timestamp;

        // Ensure role is set (defensive)
        vm.startPrank(owner);
        oracle.grantRole(oracle.ORACLE_ROLE(), owner);
        token.grantRole(token.MINTER_ROLE(), owner);
        token.mint(owner, 1000 ether);
        token.approve(address(staking), 1000 ether);
        staking.stake(1000 ether);
        vm.stopPrank();

        // First contribution
        ArxContributionOracle.ContributionProof memory proof1 = createProof(timestamp);
        bytes32 id1 = calculateContributionId(BUILDING_ID, worker1, 1000 ether, proof1);

        vm.prank(owner);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            1000 ether,
            proof1,
            signProof(proof1, WORKER1_KEY)
        );

        // Second contribution with different proof
        ArxContributionOracle.ContributionProof memory proof2 = createProof(timestamp + 1);
        bytes32 id2 = calculateContributionId(BUILDING_ID, worker1, 2000 ether, proof2);

        vm.prank(owner);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            2000 ether,
            proof2,
            signProof(proof2, WORKER1_KEY)
        );

        assertTrue(id1 != id2);
    }

    function test_ZeroAmountContribution() public {
        ArxContributionOracle.ContributionProof memory proof = createProof(block.timestamp);
        bytes memory signature = signProof(proof, WORKER1_KEY);
        
        vm.prank(oracle1);
        vm.expectRevert("ArxContributionOracle: zero amount");
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            0,
            proof,
            signature
        );
    }

    // ============ Getter Tests ============

    function test_GetContributionStatus() public {
        ArxContributionOracle.ContributionProof memory proof = createProof(block.timestamp);
        bytes memory signature = signProof(proof, WORKER1_KEY);
        bytes32 contributionId = calculateContributionId(BUILDING_ID, worker1, 1000 ether, proof);
        
        vm.prank(oracle1);
        oracle.proposeContribution(
            BUILDING_ID,
            worker1,
            1000 ether,
            proof,
            signature
        );
        
        (
            address worker,
            address building,
            uint256 amount,
            uint256 confirmations,
            uint256 proposedAt,
            bool finalized
        ) = oracle.getContribution(contributionId);
        
        assertEq(worker, worker1);
        assertEq(building, buildingWallet);
        assertEq(amount, 1000 ether);
        assertEq(confirmations, 1);
        assertEq(proposedAt, block.timestamp);
        assertFalse(finalized);
    }

    function test_RevertWhen_GetNonexistentContribution() public {
        bytes32 fakeId = keccak256("fake");
        
        vm.expectRevert("Contribution does not exist");
        oracle.getContribution(fakeId);
    }
}
