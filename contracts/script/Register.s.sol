// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/ArxRegistry.sol";
import "../src/ArxContributionOracle.sol";
import "../src/ArxosToken.sol";
import "../src/ArxOracleStaking.sol";

/**
 * @title RegisterArxos
 * @notice Post-deploy: register worker + building UUID; ensure deployer oracle role + stake.
 *
 * Required env: PRIVATE_KEY, ARX_REGISTRY, ARX_ORACLE, ARX_TOKEN,
 *               WORKER_ADDRESS, BUILDING_ID, BUILDING_WALLET
 * Optional: ARX_STAKING, ORACLE2_ADDRESS
 */
contract RegisterArxos is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(pk);

        ArxRegistry registry = ArxRegistry(vm.envAddress("ARX_REGISTRY"));
        ArxContributionOracle oracle = ArxContributionOracle(vm.envAddress("ARX_ORACLE"));
        ArxosToken token = ArxosToken(vm.envAddress("ARX_TOKEN"));

        address worker = vm.envAddress("WORKER_ADDRESS");
        string memory buildingId = vm.envString("BUILDING_ID");
        address buildingWallet = vm.envAddress("BUILDING_WALLET");

        console.log("Register from:", deployer);
        console.log("Worker:", worker);
        console.log("Building wallet:", buildingWallet);

        vm.startBroadcast(pk);

        if (!registry.isWorkerActive(worker)) {
            registry.registerWorker(worker, "arxos-horizon-a");
            console.log("Registered worker");
        } else {
            console.log("Worker already active");
        }

        if (!registry.isBuildingRegistered(buildingId)) {
            registry.registerBuilding(buildingId, buildingWallet);
            console.log("Registered building");
        } else {
            console.log("Building already registered");
        }

        bytes32 ORACLE_ROLE = oracle.ORACLE_ROLE();
        if (!oracle.hasRole(ORACLE_ROLE, deployer)) {
            oracle.grantRole(ORACLE_ROLE, deployer);
            console.log("Granted ORACLE_ROLE to deployer");
        }

        // Optional second oracle role (no stake here — stake via cast if needed)
        // Set ORACLE2_ADDRESS in env when used from shell.

        if (vm.envExists("ARX_STAKING")) {
            address stakingAddr = vm.envAddress("ARX_STAKING");
            ArxOracleStaking staking = ArxOracleStaking(stakingAddr);
            uint256 minStake = staking.minStake();
            if (!staking.hasMinStake(deployer)) {
                if (!token.hasRole(token.MINTER_ROLE(), deployer)) {
                    token.grantRole(token.MINTER_ROLE(), deployer);
                }
                token.mint(deployer, minStake * 2);
                token.approve(stakingAddr, minStake);
                staking.stake(minStake);
                console.log("Staked min stake for deployer oracle");
            } else {
                console.log("Deployer already staked");
            }
        } else {
            console.log("ARX_STAKING not set - stake manually if proposing");
        }

        vm.stopBroadcast();
        console.log("Register complete.");
    }
}
