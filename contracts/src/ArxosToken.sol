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

    /// @notice Global emergency pause flag for minting flows
    bool public emergencyPause;

    /// @notice Per-building and per-worker daily caps (in token units)
    uint256 public buildingDailyCap = type(uint256).max;
    uint256 public workerDailyCap = type(uint256).max;

    struct DailyLimit {
        uint256 amount; // minted so far today
        uint64 lastUpdatedDay; // day index to roll over usage
    }

    mapping(address => DailyLimit) private buildingDailyUsage;
    mapping(address => DailyLimit) private workerDailyUsage;

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

    /// @notice Emitted when daily caps are updated (0 treated as unlimited)
    event DailyCapsUpdated(uint256 buildingCap, uint256 workerCap);

    /// @notice Emitted when the emergency pause flag changes
    event EmergencyPauseSet(address indexed caller, bool paused);

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
        require(!emergencyPause, "ArxosToken: paused");
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
        require(!emergencyPause, "ArxosToken: paused");
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
        require(!emergencyPause, "ArxosToken: paused");
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

        _enforceDailyCap(workerDailyUsage[worker], workerDailyCap, workerAmount, "worker");
        _enforceDailyCap(buildingDailyUsage[building], buildingDailyCap, buildingAmount, "building");

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
     * @notice Set the emergency pause flag for all minting entrypoints
     * @param paused Whether minting should be paused
     * @dev Only callable by DEFAULT_ADMIN_ROLE
     */
    function setEmergencyPause(bool paused) external onlyRole(DEFAULT_ADMIN_ROLE) {
        emergencyPause = paused;
        emit EmergencyPauseSet(msg.sender, paused);
    }

    /**
     * @notice Update daily mint caps for buildings and workers
     * @param newBuildingCap Cap applied to each building's 10% share per day (0 means unlimited)
     * @param newWorkerCap Cap applied to each worker's 70% share per day (0 means unlimited)
     * @dev Only callable by DEFAULT_ADMIN_ROLE. Caps are evaluated on the minted share amounts.
     */
    function setDailyCaps(uint256 newBuildingCap, uint256 newWorkerCap) external onlyRole(DEFAULT_ADMIN_ROLE) {
        buildingDailyCap = newBuildingCap == 0 ? type(uint256).max : newBuildingCap;
        workerDailyCap = newWorkerCap == 0 ? type(uint256).max : newWorkerCap;
        emit DailyCapsUpdated(buildingDailyCap, workerDailyCap);
    }

    /**
     * @notice Get token decimals
     * @return Number of decimals (18)
     */
    function decimals() public pure override returns (uint8) {
        return 18;
    }

    function _enforceDailyCap(
        DailyLimit storage limit,
        uint256 cap,
        uint256 amount,
        string memory domain
    ) internal {
        if (cap == type(uint256).max) {
            return; // unlimited
        }

        uint64 currentDay = uint64(block.timestamp / 1 days);
        if (limit.lastUpdatedDay < currentDay) {
            limit.amount = 0;
            limit.lastUpdatedDay = currentDay;
        }

        uint256 newTotal = limit.amount + amount;
        require(newTotal <= cap, string.concat("ArxosToken: ", domain, " daily cap"));
        limit.amount = newTotal;
    }
}
