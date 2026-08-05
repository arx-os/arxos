// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Arxos Building Registry (minimal)
/// @notice Maps a stable BuildingId to an official Root CID and controller set.
/// @dev Deploy on Base L2 (or compatible EVM). CIDs are stored as bytes32 BLAKE3 digests
///      (raw 32 bytes without the `b3:` prefix). Full `b3:hex` form is reconstructed off-chain.
///
/// Phase 5 scope: controllers, official root tip, events for indexers.
/// Rewards / staking intentionally deferred.

contract BuildingRegistry {
    struct Building {
        bytes32 officialRoot;
        address[] controllers;
        uint64 updatedAt;
        bool exists;
    }

    /// buildingId (bytes32 ULID/hash) => Building
    mapping(bytes32 => Building) private buildings;

    event BuildingRegistered(bytes32 indexed buildingId, address indexed registrar, bytes32 root);
    event RootUpdated(bytes32 indexed buildingId, bytes32 indexed previousRoot, bytes32 newRoot, address indexed updater);
    event ControllerAdded(bytes32 indexed buildingId, address indexed controller);
    event ControllerRemoved(bytes32 indexed buildingId, address indexed controller);

    error BuildingAlreadyExists();
    error BuildingNotFound();
    error NotController();
    error ZeroAddress();
    error ZeroId();
    error ControllerExists();
    error ControllerMissing();
    error NeedOneController();

    modifier onlyController(bytes32 buildingId) {
        if (!_isController(buildingId, msg.sender)) revert NotController();
        _;
    }

    /// @notice Register a new building with an initial official root and the caller as controller.
    function register(bytes32 buildingId, bytes32 initialRoot) external {
        if (buildingId == bytes32(0)) revert ZeroId();
        if (buildings[buildingId].exists) revert BuildingAlreadyExists();

        Building storage b = buildings[buildingId];
        b.exists = true;
        b.officialRoot = initialRoot;
        b.updatedAt = uint64(block.timestamp);
        b.controllers.push(msg.sender);

        emit BuildingRegistered(buildingId, msg.sender, initialRoot);
        emit ControllerAdded(buildingId, msg.sender);
    }

    /// @notice Update the official root tip (must be a controller).
    function setOfficialRoot(bytes32 buildingId, bytes32 newRoot) external onlyController(buildingId) {
        Building storage b = buildings[buildingId];
        if (!b.exists) revert BuildingNotFound();
        bytes32 prev = b.officialRoot;
        b.officialRoot = newRoot;
        b.updatedAt = uint64(block.timestamp);
        emit RootUpdated(buildingId, prev, newRoot, msg.sender);
    }

    /// @notice Add a controller address.
    function addController(bytes32 buildingId, address controller) external onlyController(buildingId) {
        if (controller == address(0)) revert ZeroAddress();
        Building storage b = buildings[buildingId];
        if (!b.exists) revert BuildingNotFound();
        if (_isController(buildingId, controller)) revert ControllerExists();
        b.controllers.push(controller);
        emit ControllerAdded(buildingId, controller);
    }

    /// @notice Remove a controller (cannot remove the last one).
    function removeController(bytes32 buildingId, address controller) external onlyController(buildingId) {
        Building storage b = buildings[buildingId];
        if (!b.exists) revert BuildingNotFound();
        if (b.controllers.length <= 1) revert NeedOneController();
        uint256 idx = type(uint256).max;
        for (uint256 i = 0; i < b.controllers.length; i++) {
            if (b.controllers[i] == controller) {
                idx = i;
                break;
            }
        }
        if (idx == type(uint256).max) revert ControllerMissing();
        b.controllers[idx] = b.controllers[b.controllers.length - 1];
        b.controllers.pop();
        emit ControllerRemoved(buildingId, controller);
    }

    function getOfficialRoot(bytes32 buildingId) external view returns (bytes32) {
        if (!buildings[buildingId].exists) revert BuildingNotFound();
        return buildings[buildingId].officialRoot;
    }

    function getControllers(bytes32 buildingId) external view returns (address[] memory) {
        if (!buildings[buildingId].exists) revert BuildingNotFound();
        return buildings[buildingId].controllers;
    }

    function getBuilding(bytes32 buildingId)
        external
        view
        returns (bytes32 officialRoot, address[] memory controllers, uint64 updatedAt, bool exists)
    {
        Building storage b = buildings[buildingId];
        return (b.officialRoot, b.controllers, b.updatedAt, b.exists);
    }

    function isController(bytes32 buildingId, address account) external view returns (bool) {
        return _isController(buildingId, account);
    }

    function _isController(bytes32 buildingId, address account) internal view returns (bool) {
        Building storage b = buildings[buildingId];
        if (!b.exists) return false;
        for (uint256 i = 0; i < b.controllers.length; i++) {
            if (b.controllers[i] == account) return true;
        }
        return false;
    }
}
