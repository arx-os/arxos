// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title BuildingContributionE2E
 * @notice Vision-aligned end-to-end: registered building (UUID) + worker →
 *         multi-oracle consensus on one building-data proof → finalize → mint $AXD 70/10/10/10.
 *
 * Mirrors the off-chain path:
 *   arx contribute → contribution.json (merkle root + quality + building_id UUID)
 *   → EIP-712 worker signature → oracle propose (2-of-3) → warp → finalize mint
 */

import {Test} from "forge-std/Test.sol";
import {ArxContributionOracle} from "../src/ArxContributionOracle.sol";
import {ArxosToken} from "../src/ArxosToken.sol";
import {ArxRegistry} from "../src/ArxRegistry.sol";
import {ArxAddresses} from "../src/ArxAddresses.sol";
import {ArxOracleStaking} from "../src/ArxOracleStaking.sol";

contract BuildingContributionE2E is Test {
    ArxContributionOracle public oracle;
    ArxosToken public token;
    ArxRegistry public registry;
    ArxAddresses public addresses;
    ArxOracleStaking public staking;

    address public owner = address(this);
    address public oracleA = vm.addr(0xA11);
    address public oracleB = vm.addr(0xB22);
    address public oracleC = vm.addr(0xC33);
    address public worker = vm.addr(0x701);
    address public buildingOwner = vm.addr(0xB01);
    address public maintainerVault = vm.addr(0xD01);
    address public treasury = vm.addr(0xE01);

    uint256 constant WORKER_KEY = 0x701;
    uint256 constant ORACLE_A_KEY = 0xA11;
    uint256 constant ORACLE_B_KEY = 0xB22;

    /// @dev UUID-shaped building id as produced by Rust `Building.id` / contribution package
    string constant BUILDING_UUID = "8ffa4c60-92a3-4e6e-b8e6-606ec923b3b5";

    /// @dev Stands in for package.merkle_root_hex decoded (building.yaml commitment)
    bytes32 constant BUILDING_MERKLE =
        hex"842222818c2acd4bc9f66f71426377d0afb278b657c1111b13ddf5911e5b43d7";

    function setUp() public {
        addresses = new ArxAddresses(owner, maintainerVault, treasury);
        registry = new ArxRegistry(owner);
        token = new ArxosToken(owner);
        staking = new ArxOracleStaking(owner, address(token), 1000 ether);
        oracle = new ArxContributionOracle(
            owner, address(token), address(registry), address(addresses), address(staking)
        );

        token.grantRole(token.MINTER_ROLE(), address(oracle));
        token.grantRole(token.MINTER_ROLE(), owner);

        oracle.grantRole(oracle.ORACLE_ROLE(), oracleA);
        oracle.grantRole(oracle.ORACLE_ROLE(), oracleB);
        oracle.grantRole(oracle.ORACLE_ROLE(), oracleC);

        _fundAndStake(oracleA);
        _fundAndStake(oracleB);
        _fundAndStake(oracleC);

        registry.registerWorker(worker, "ipfs://field-worker-meta");
        // N4: buildingId on-chain == building UUID from contribution package
        registry.registerBuilding(BUILDING_UUID, buildingOwner);
    }

    function _fundAndStake(address who) internal {
        token.mint(who, 2000 ether);
        vm.startPrank(who);
        token.approve(address(staking), 1000 ether);
        staking.stake(1000 ether);
        vm.stopPrank();
    }

    function _proof(uint256 ts, uint8 accuracy, uint8 completeness)
        internal
        pure
        returns (ArxContributionOracle.ContributionProof memory)
    {
        return ArxContributionOracle.ContributionProof({
            merkleRoot: BUILDING_MERKLE,
            locationHash: keccak256("site"),
            buildingHash: keccak256(bytes(BUILDING_UUID)),
            timestamp: ts,
            dataSize: 448, // sample package data_size
            quality: ArxContributionOracle.QualityMetrics({
                accuracy: accuracy, completeness: completeness
            })
        });
    }

    function _sign(ArxContributionOracle.ContributionProof memory proof, uint256 key)
        internal
        view
        returns (bytes memory)
    {
        bytes32 qualityHash = keccak256(
            abi.encode(
                oracle.QUALITY_METRICS_TYPEHASH(),
                proof.quality.accuracy,
                proof.quality.completeness
            )
        );
        bytes32 structHash = keccak256(
            abi.encode(
                oracle.CONTRIBUTION_PROOF_TYPEHASH(),
                proof.merkleRoot,
                proof.locationHash,
                proof.buildingHash,
                proof.timestamp,
                proof.dataSize,
                qualityHash
            )
        );
        bytes32 domainSeparator = keccak256(
            abi.encode(
                keccak256(
                    "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
                ),
                keccak256("ArxOS Contribution Oracle"),
                keccak256("1"),
                block.chainid,
                address(oracle)
            )
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", domainSeparator, structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(key, digest);
        return abi.encodePacked(r, s, v);
    }

    /// @notice Full reward path: free software labor (package) → peer oracles → mint to worker/building
    function test_E2E_BuildingUuid_PackageToMint() public {
        uint256 amount = 100 ether; // base reward before quality scale
        uint256 ts = block.timestamp;
        // Quality from package path (validation clean + structure)
        ArxContributionOracle.ContributionProof memory proof = _proof(ts, 100, 70);
        bytes memory sig = _sign(proof, WORKER_KEY);
        bytes32 contributionId =
            keccak256(abi.encodePacked(BUILDING_UUID, worker, amount));

        // Two oracles confirm the *same* building-data proof (consensus)
        vm.prank(oracleA);
        oracle.proposeContribution(BUILDING_UUID, worker, amount, proof, sig);
        vm.prank(oracleB);
        oracle.proposeContribution(BUILDING_UUID, worker, amount, proof, sig);

        (, , , uint256 conf, , bool fin) = oracle.getContribution(contributionId);
        assertEq(conf, 2);
        assertFalse(fin);

        // Contractual delay (24h) — field product does not wait in Foundry
        vm.warp(ts + 24 hours + 1);

        uint256 w0 = token.balanceOf(worker);
        uint256 b0 = token.balanceOf(buildingOwner);
        uint256 m0 = token.balanceOf(maintainerVault);
        uint256 t0 = token.balanceOf(treasury);

        oracle.finalizeContribution(contributionId);

        // qualityScore = (100+70)/2 = 85 → scaledAmount = amount * 85 / 100
        uint256 scaled = (amount * 85) / 100;
        assertEq(token.balanceOf(worker), w0 + (scaled * 70) / 100);
        assertEq(token.balanceOf(buildingOwner), b0 + (scaled * 10) / 100);
        assertEq(token.balanceOf(maintainerVault), m0 + (scaled * 10) / 100);
        assertEq(token.balanceOf(treasury), t0 + (scaled * 10) / 100);

        (, , , , , bool finalized) = oracle.getContribution(contributionId);
        assertTrue(finalized);

        // Unregistered building UUID must fail (identity binding)
        ArxContributionOracle.ContributionProof memory p2 = _proof(ts + 10, 100, 100);
        bytes memory s2 = _sign(p2, WORKER_KEY);
        vm.prank(oracleA);
        vm.expectRevert("Building not registered");
        oracle.proposeContribution("00000000-0000-0000-0000-000000000000", worker, amount, p2, s2);
    }

    function test_E2E_SameProofRequiredForSecondOracle() public {
        uint256 amount = 50 ether;
        uint256 ts = block.timestamp;
        ArxContributionOracle.ContributionProof memory proof = _proof(ts, 90, 90);
        bytes memory sig = _sign(proof, WORKER_KEY);

        vm.prank(oracleA);
        oracle.proposeContribution(BUILDING_UUID, worker, amount, proof, sig);

        // Different merkle (different building package) must not confirm same claim
        ArxContributionOracle.ContributionProof memory other = _proof(ts, 90, 90);
        other.merkleRoot = keccak256("other-building-yaml");
        bytes memory otherSig = _sign(other, WORKER_KEY);

        vm.prank(oracleB);
        vm.expectRevert("ArxContributionOracle: proof mismatch");
        oracle.proposeContribution(BUILDING_UUID, worker, amount, other, otherSig);
    }
}
