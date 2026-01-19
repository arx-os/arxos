// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/ArxAddresses.sol";
import "../src/ArxRegistry.sol";
import "../src/ArxosToken.sol";
import "../src/ArxContributionOracle.sol";
import "../src/ArxContributionOracle.sol";
import "../src/ArxPaymentRouter.sol";
import "../src/ArxOracleStaking.sol";
import "../src/ArxDisputeResolver.sol";

/**
 * @title DeployArxos
 * @notice Deployment script for ArxOS tokenomics contracts
 * @dev Deploy order:
 *      1. ArxAddresses (configuration)
 *      2. ArxRegistry (identity management)
 *      3. ArxosToken (ERC20 token)
 *      4. ArxOracleStaking (security)
 *      5. ArxContributionOracle (minting logic)
 *      6. ArxPaymentRouter (x402 payments)
 *      7. ArxDisputeResolver (dispute handling)
 */
contract DeployArxos is Script {
    function run() external {
        // Load deployment account from private key
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);

        console.log("Deploying from:", deployer);
        console.log("Balance:", deployer.balance);

        // Load configuration from environment
        address maintainerVault = vm.envAddress("MAINTAINER_VAULT");
        address treasury = vm.envAddress("TREASURY");

        console.log("Maintainer Vault:", maintainerVault);
        console.log("Treasury:", treasury);

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy ArxAddresses
        console.log("\n1. Deploying ArxAddresses...");
        ArxAddresses addresses = new ArxAddresses(deployer, maintainerVault, treasury);
        console.log("ArxAddresses deployed at:", address(addresses));

        // 2. Deploy ArxRegistry
        console.log("\n2. Deploying ArxRegistry...");
        ArxRegistry registry = new ArxRegistry(deployer);
        console.log("ArxRegistry deployed at:", address(registry));
        console.log("ArxWorkerID NFT deployed at:", address(registry.workerNFT()));

        // 3. Deploy ArxosToken
        console.log("\n3. Deploying ArxosToken...");
        ArxosToken token = new ArxosToken(deployer);
        console.log("ArxosToken deployed at:", address(token));

        // 4. Deploy ArxContributionOracle
        // 4. Deploy ArxOracleStaking
        console.log("\n4. Deploying ArxOracleStaking...");
        uint256 minStake = 10_000 * 10**18;
        ArxOracleStaking staking = new ArxOracleStaking(deployer, address(token), minStake); // owner first
        console.log("ArxOracleStaking deployed at:", address(staking));

        // 5. Deploy ArxContributionOracle
        console.log("\n5. Deploying ArxContributionOracle...");
        ArxContributionOracle oracle = new ArxContributionOracle(
            deployer,
            address(token),
            address(registry),
            address(addresses),
            address(staking)
        );
        console.log("ArxContributionOracle deployed at:", address(oracle));

        // 6. Deploy ArxPaymentRouter
        console.log("\n6. Deploying ArxPaymentRouter...");
        ArxPaymentRouter router = new ArxPaymentRouter(
            deployer,
            address(token),
            address(registry),
            address(addresses)
        );
        console.log("ArxPaymentRouter deployed at:", address(router));

        // 7. Deploy ArxDisputeResolver
        console.log("\n7. Deploying ArxDisputeResolver...");
        ArxDisputeResolver resolver = new ArxDisputeResolver(
            deployer,
            address(token),
            address(oracle),
            address(staking)
        );
        console.log("ArxDisputeResolver deployed at:", address(resolver));
        
        // Connect Oracle to Resolver
        oracle.setResolver(address(resolver));

        // Grant MINTER_ROLE to oracle
        console.log("\n6. Granting MINTER_ROLE to oracle...");
        bytes32 MINTER_ROLE = token.MINTER_ROLE();
        token.grantRole(MINTER_ROLE, address(oracle));
        console.log("MINTER_ROLE granted to:", address(oracle));

        // Grant ORACLE_ROLE to deployer (first oracle)
        console.log("\n7. Granting ORACLE_ROLE to deployer...");
        bytes32 ORACLE_ROLE = oracle.ORACLE_ROLE();
        oracle.grantRole(ORACLE_ROLE, deployer);
        console.log("ORACLE_ROLE granted to:", deployer);

        vm.stopBroadcast();

        // Print deployment summary
        console.log("\n========================================");
        console.log("DEPLOYMENT SUMMARY");
        console.log("========================================");
        console.log("ArxAddresses:", address(addresses));
        console.log("ArxRegistry:", address(registry));
        console.log("ArxWorkerID:", address(registry.workerNFT()));
        console.log("ArxosToken:", address(token));
        console.log("ArxContributionOracle:", address(oracle));
        console.log("ArxPaymentRouter:", address(router));
        console.log("========================================");
        console.log("\nNext steps:");
        console.log("1. Verify contracts on Basescan");
        console.log("2. Add additional oracle operators");
        console.log("3. Register first building and worker");
        console.log("4. Transfer ownership to multisig");
    }
}
