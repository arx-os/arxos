// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ArxOracleStaking
 * @notice Manages ARXO stakes for oracles in the ArxOS ecosystem
 * @dev Oracles must maintain a minimum stake to participate in consensus
 *      Includes a withdrawal delay and slashing mechanism
 */
contract ArxOracleStaking is Ownable, ReentrancyGuard {
    /// @notice The ARXO token contract
    IERC20 public immutable arxoToken;

    /// @notice Minimum amount of ARXO required to be an active oracle
    uint256 public minStake;

    /// @notice Delay required before stake can be withdrawn (7 days)
    uint256 public withdrawalDelay = 7 days;

    /// @notice Mapping from oracle address to current staked amount
    mapping(address => uint256) public stakes;

    /// @notice Mapping from oracle address to pending withdrawal timestamp
    mapping(address => uint256) public withdrawalRequestAt;

    /// @notice Mapping from oracle address to pending withdrawal amount
    mapping(address => uint256) public pendingWithdrawals;

    /// @notice Emitted when an oracle stakes tokens
    event Staked(address indexed oracle, uint256 amount);

    /// @notice Emitted when a withdrawal is requested
    event WithdrawalRequested(address indexed oracle, uint256 amount, uint256 unlockingAt);

    /// @notice Emitted when tokens are withdrawn
    event Withdrawn(address indexed oracle, uint256 amount);

    /// @notice Emitted when an oracle is slashed
    event Slashed(address indexed oracle, uint256 amount, string reason);

    /// @notice Emitted when configuration is updated
    event ConfigUpdated(uint256 minStake, uint256 withdrawalDelay);

    /**
     * @notice Contract constructor
     * @param _initialOwner Address that will own the contract
     * @param _arxoToken Address of the ARXO token contract
     * @param _minStake Initial minimum stake requirement
     */
    constructor(
        address _initialOwner,
        address _arxoToken,
        uint256 _minStake
    ) Ownable(_initialOwner) {
        require(_arxoToken != address(0), "ArxOracleStaking: zero token");
        arxoToken = IERC20(_arxoToken);
        minStake = _minStake;
    }

    /**
     * @notice Deposit ARXO to stake as an oracle
     * @param amount Amount of ARXO to stake
     */
    function stake(uint256 amount) external nonReentrant {
        require(amount > 0, "ArxOracleStaking: amount is zero");
        
        // Transfer tokens from sender to contract
        require(
            arxoToken.transferFrom(msg.sender, address(this), amount),
            "ArxOracleStaking: transfer failed"
        );

        stakes[msg.sender] += amount;
        emit Staked(msg.sender, amount);
    }

    /**
     * @notice Request to withdraw staked tokens
     * @param amount Amount to withdraw
     * @dev Initiates a countdown based on withdrawalDelay
     */
    function requestWithdrawal(uint256 amount) external {
        require(amount > 0, "ArxOracleStaking: amount is zero");
        require(stakes[msg.sender] >= amount, "ArxOracleStaking: insufficient stake");

        // Move from active stake to pending withdrawal
        stakes[msg.sender] -= amount;
        pendingWithdrawals[msg.sender] += amount;
        withdrawalRequestAt[msg.sender] = block.timestamp;

        emit WithdrawalRequested(msg.sender, amount, block.timestamp + withdrawalDelay);
    }

    /**
     * @notice Finalize a withdrawal after the delay has passed
     */
    function withdraw() external nonReentrant {
        require(pendingWithdrawals[msg.sender] > 0, "ArxOracleStaking: no pending withdrawal");
        require(
            block.timestamp >= withdrawalRequestAt[msg.sender] + withdrawalDelay,
            "ArxOracleStaking: withdrawal delay not met"
        );

        uint256 amount = pendingWithdrawals[msg.sender];
        pendingWithdrawals[msg.sender] = 0;
        
        require(
            arxoToken.transfer(msg.sender, amount),
            "ArxOracleStaking: transfer failed"
        );

        emit Withdrawn(msg.sender, amount);
    }

    /**
     * @notice Slash an oracle's stake for misconduct
     * @param oracle Address of the oracle to slash
     * @param amount Amount to slash
     * @param reason Description of the misconduct
     * @dev Slashed tokens are effectively burned (locked in this contract or sent to 0)
     */
    function slash(
        address oracle,
        uint256 amount,
        string calldata reason
    ) external onlyOwner {
        require(stakes[oracle] >= amount, "ArxOracleStaking: slash exceeds stake");
        
        stakes[oracle] -= amount;
        
        // For simplicity in V1, we lock them here. 
        // In V2, we might send them to a burn address or treasury.
        
        emit Slashed(oracle, amount, reason);
    }

    /**
     * @notice Check if an address is currently a valid oracle (has min stake)
     * @param oracle Address to check
     * @return True if oracle has >= minStake
     */
    function hasMinStake(address oracle) external view returns (bool) {
        return stakes[oracle] >= minStake;
    }

    /**
     * @notice Update minimum stake and withdrawal delay
     * @param _minStake New minimum stake amount
     * @param _delay New withdrawal delay in seconds
     */
    function updateConfig(uint256 _minStake, uint256 _delay) external onlyOwner {
        minStake = _minStake;
        withdrawalDelay = _delay;
        emit ConfigUpdated(_minStake, _delay);
    }
}
