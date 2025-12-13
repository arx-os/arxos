// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ArxAddresses
 * @notice Registry of system addresses for ArxOS tokenomics
 * @dev Centralized configuration for maintainer vault and treasury addresses
 *      Used by ArxContributionOracle and ArxPaymentRouter for 70/10/10/10 splits
 */
contract ArxAddresses is Ownable {
    /// @notice Address of the maintainer vault (10% of all mints/payments)
    address public maintainerVault;

    /// @notice Address of the treasury (10% of all mints/payments)
    address public treasury;

    /// @notice Emitted when maintainer vault address is updated
    event MaintainerVaultUpdated(address indexed oldVault, address indexed newVault);

    /// @notice Emitted when treasury address is updated
    event TreasuryUpdated(address indexed oldTreasury, address indexed newTreasury);

    /**
     * @notice Contract constructor
     * @param _initialOwner Address that will own this contract
     * @param _maintainerVault Initial maintainer vault address
     * @param _treasury Initial treasury address
     */
    constructor(
        address _initialOwner,
        address _maintainerVault,
        address _treasury
    ) Ownable(_initialOwner) {
        require(_maintainerVault != address(0), "ArxAddresses: zero maintainer vault");
        require(_treasury != address(0), "ArxAddresses: zero treasury");

        maintainerVault = _maintainerVault;
        treasury = _treasury;
    }

    /**
     * @notice Update maintainer vault address
     * @param _newVault New maintainer vault address
     * @dev Only callable by owner (ArxOS LLC initially, DAO later)
     */
    function setMaintainerVault(address _newVault) external onlyOwner {
        require(_newVault != address(0), "ArxAddresses: zero address");
        emit MaintainerVaultUpdated(maintainerVault, _newVault);
        maintainerVault = _newVault;
    }

    /**
     * @notice Update treasury address
     * @param _newTreasury New treasury address
     * @dev Only callable by owner (ArxOS LLC initially, DAO later)
     */
    function setTreasury(address _newTreasury) external onlyOwner {
        require(_newTreasury != address(0), "ArxAddresses: zero address");
        emit TreasuryUpdated(treasury, _newTreasury);
        treasury = _newTreasury;
    }

    /**
     * @notice Get all system addresses in one call
     * @return _maintainerVault Address of maintainer vault
     * @return _treasury Address of treasury
     * @dev Useful for contracts that need both addresses
     */
    function getAddresses() external view returns (address _maintainerVault, address _treasury) {
        return (maintainerVault, treasury);
    }
}
