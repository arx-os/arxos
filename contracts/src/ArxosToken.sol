// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title ArxosToken
 * @notice ERC-20 token for ArxOS ecosystem with role-based minting
 * @dev Supports batch minting for 70/10/10/10 distribution splits
 *      Minting controlled by MINTER_ROLE (assigned to ArxContributionOracle)
 */
contract ArxosToken is ERC20, AccessControl {
    /// @notice Role identifier for addresses that can mint tokens
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    /// @notice Total value contributed (in USD equivalent)
    uint256 public totalContributedValue;

    /// @notice Emitted when tokens are minted for a contribution
    event ContributionMinted(
        address indexed worker,
        address indexed building,
        address indexed maintainer,
        address treasury,
        uint256 totalAmount
    );

    /// @notice Emitted when tokens are minted in batch
    event BatchMinted(address indexed minter, uint256 totalAmount, uint256 recipientCount);

    /// @notice Emitted when tokens are burned
    event TokensBurned(address indexed burner, uint256 amount);

    /**
     * @notice Contract constructor
     * @param admin Address that will have DEFAULT_ADMIN_ROLE
     */
    constructor(address admin) ERC20("ArxOS Token", "ARXO") {
        require(admin != address(0), "ArxosToken: zero admin");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
    }

    /**
     * @notice Mint tokens to a single recipient
     * @param to Recipient address
     * @param amount Amount of tokens to mint
     * @dev Only callable by addresses with MINTER_ROLE
     */
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        require(to != address(0), "ArxosToken: zero address");
        require(amount > 0, "ArxosToken: zero amount");

        _mint(to, amount);
    }

    /**
     * @notice Mint tokens to multiple recipients in one transaction
     * @param recipients Array of recipient addresses
     * @param amounts Array of amounts (must match recipients length)
     * @dev Only callable by addresses with MINTER_ROLE
     *      Gas-efficient for 70/10/10/10 splits (4 recipients per contribution)
     */
    function mintBatch(
        address[] calldata recipients,
        uint256[] calldata amounts
    ) external onlyRole(MINTER_ROLE) {
        require(recipients.length == amounts.length, "ArxosToken: length mismatch");
        require(recipients.length > 0, "ArxosToken: empty arrays");

        uint256 totalAmount = 0;

        for (uint256 i = 0; i < recipients.length; i++) {
            require(recipients[i] != address(0), "ArxosToken: zero address");
            require(amounts[i] > 0, "ArxosToken: zero amount");

            _mint(recipients[i], amounts[i]);
            totalAmount += amounts[i];
        }

        emit BatchMinted(msg.sender, totalAmount, recipients.length);
    }

    /**
     * @notice Mint for contribution with automatic 70/10/10/10 split
     * @param worker Worker address (receives 70%)
     * @param building Building wallet address (receives 10%)
     * @param maintainer Maintainer vault address (receives 10%)
     * @param treasury Treasury address (receives 10%)
     * @param totalAmount Total amount to mint and split
     * @dev Only callable by addresses with MINTER_ROLE
     *      Convenience function for ArxContributionOracle
     */
    function mintContribution(
        address worker,
        address building,
        address maintainer,
        address treasury,
        uint256 totalAmount
    ) external onlyRole(MINTER_ROLE) {
        require(worker != address(0), "ArxosToken: zero worker");
        require(building != address(0), "ArxosToken: zero building");
        require(maintainer != address(0), "ArxosToken: zero maintainer");
        require(treasury != address(0), "ArxosToken: zero treasury");
        require(totalAmount > 0, "ArxosToken: zero amount");

        // Calculate 70/10/10/10 split
        uint256 workerAmount = (totalAmount * 70) / 100;
        uint256 buildingAmount = (totalAmount * 10) / 100;
        uint256 maintainerAmount = (totalAmount * 10) / 100;
        uint256 treasuryAmount = totalAmount - workerAmount - buildingAmount - maintainerAmount;

        // Mint to all recipients
        _mint(worker, workerAmount);
        _mint(building, buildingAmount);
        _mint(maintainer, maintainerAmount);
        _mint(treasury, treasuryAmount);

        totalContributedValue += totalAmount;

        emit ContributionMinted(worker, building, maintainer, treasury, totalAmount);
    }

    /**
     * @notice Burn tokens from caller's balance
     * @param amount Amount of tokens to burn
     * @dev Public function for deflationary mechanics (RevenueSplitter)
     */
    function burn(uint256 amount) external {
        require(amount > 0, "ArxosToken: zero amount");
        _burn(msg.sender, amount);
        emit TokensBurned(msg.sender, amount);
    }

    /**
     * @notice Burn tokens from specified address (requires allowance)
     * @param from Address to burn from
     * @param amount Amount of tokens to burn
     * @dev Used by contracts with burn approval
     */
    function burnFrom(address from, uint256 amount) external {
        require(amount > 0, "ArxosToken: zero amount");
        _spendAllowance(from, msg.sender, amount);
        _burn(from, amount);
        emit TokensBurned(from, amount);
    }

    /**
     * @notice Get token decimals
     * @return Number of decimals (18)
     */
    function decimals() public pure override returns (uint8) {
        return 18;
    }
}
