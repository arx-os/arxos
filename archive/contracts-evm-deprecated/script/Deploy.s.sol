// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console2} from "forge-std/Script.sol";
import {BuildingRegistry} from "../BuildingRegistry.sol";

/// @dev forge script script/Deploy.s.sol:Deploy --rpc-url $RPC --broadcast
contract Deploy is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(pk);
        BuildingRegistry reg = new BuildingRegistry();
        console2.log("BuildingRegistry", address(reg));
        vm.stopBroadcast();
    }
}
