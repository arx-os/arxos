// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./ArxosToken.sol";
import "./ArxRegistry.sol";
import "./ArxAddresses.sol";

/**
 * @title ArxPaymentRouter
 * @notice Handles x402 micropayments for building data access
 * @dev Distributes payments with 70/10/10/10 split
 *      Integrates with x402 protocol for off-chain verification
 */
contract ArxPaymentRouter is Ownable, ReentrancyGuard {
    /// @notice ArxosToken contract
    ArxosToken public immutable arxoToken;

    /// @notice ArxRegistry contract
    ArxRegistry public immutable registry;

    /// @notice ArxAddresses contract
    ArxAddresses public immutable addresses;

    /// @notice Mapping from nonce to usage status (prevents replay)
    mapping(bytes32 => bool) public noncesUsed;

    /// @notice Mapping from building ID to minimum payment amount
    mapping(string => uint256) public minimumPayment;

    /// @notice Default minimum payment (0.01 ARXO)
    uint256 public constant DEFAULT_MINIMUM = 10**16;

    /// @notice Delay before a price increase becomes effective (7 days)
    uint256 public constant PRICE_UPDATE_DELAY = 7 days;

    struct ScheduledPrice {
        uint256 price;
        uint256 effectiveTimestamp;
    }

    /// @notice Mapping from building ID to pending price update
    mapping(string => ScheduledPrice) public pendingPriceUpdates;

    /// @notice Emitted when payment is made for data access
    event AccessPaid(
        string indexed buildingId,
        address indexed payer,
        uint256 amount,
        bytes32 indexed nonce,
        uint256 timestamp
    );

    /// @notice Emitted when payment is distributed
    event PaymentDistributed(
        address indexed building,
        address indexed maintainer,
        address indexed treasury,
        uint256 buildingAmount,
        uint256 maintainerAmount,
        uint256 treasuryAmount
    );

    /// @notice Emitted when minimum payment is updated
    event MinimumPaymentUpdated(string indexed buildingId, uint256 oldMinimum, uint256 newMinimum);

    /// @notice Emitted when a price update is scheduled
    event PriceUpdateScheduled(string indexed buildingId, uint256 newPrice, uint256 effectiveTimestamp);

    /**
     * @notice Contract constructor
     * @param _initialOwner Address that will own this contract
     * @param _arxoToken ArxosToken contract address
     * @param _registry ArxRegistry contract address
     * @param _addresses ArxAddresses contract address
     */
    constructor(
        address _initialOwner,
        address _arxoToken,
        address _registry,
        address _addresses
    ) Ownable(_initialOwner) {
        require(_arxoToken != address(0), "ArxPaymentRouter: zero token");
        require(_registry != address(0), "ArxPaymentRouter: zero registry");
        require(_addresses != address(0), "ArxPaymentRouter: zero addresses");

        arxoToken = ArxosToken(_arxoToken);
        registry = ArxRegistry(_registry);
        addresses = ArxAddresses(_addresses);
    }

    /**
     * @notice Pay for building data access
     * @param buildingId Building identifier
     * @param amount Amount of ARXO to pay
     * @param nonce Unique nonce from server (prevents replay)
     * @dev Transfers ARXO from user and distributes with 70/10/10/10 split
     *      Emits AccessPaid event for x402 protocol verification
     */
    function payForAccess(
        string calldata buildingId,
        uint256 amount,
        bytes32 nonce,
        uint256 maxPrice
    ) external nonReentrant {
        require(registry.isBuildingRegistered(buildingId), "ArxPaymentRouter: building not registered");
        uint256 currentPrice = getMinimumPayment(buildingId);
        require(currentPrice <= maxPrice, "ArxPaymentRouter: price exceeds max price");
        require(amount >= currentPrice, "ArxPaymentRouter: insufficient amount");
        require(!noncesUsed[nonce], "ArxPaymentRouter: nonce already used");

        // Mark nonce as used
        noncesUsed[nonce] = true;

        // Transfer ARXO from user to contract
        require(
            arxoToken.transferFrom(msg.sender, address(this), amount),
            "ArxPaymentRouter: transfer failed"
        );

        // Get building wallet
        address building = registry.getBuildingWallet(buildingId);

        // Distribute payment
        _distributePayment(building, amount);

        // Emit event for x402 verification
        emit AccessPaid(buildingId, msg.sender, amount, nonce, block.timestamp);
    }

    /**
     * @notice Batch payment for multiple buildings
     * @param buildingIds Array of building identifiers
     * @param amounts Array of payment amounts
     * @param nonces Array of unique nonces
     * @dev Gas-efficient for bulk access purchases
     */
    function batchPayForAccess(
        string[] calldata buildingIds,
        uint256[] calldata amounts,
        bytes32[] calldata nonces
    ) external nonReentrant {
        require(
            buildingIds.length == amounts.length && amounts.length == nonces.length,
            "ArxPaymentRouter: length mismatch"
        );
        require(buildingIds.length > 0, "ArxPaymentRouter: empty arrays");

        uint256 totalAmount = 0;

        for (uint256 i = 0; i < buildingIds.length; i++) {
            require(registry.isBuildingRegistered(buildingIds[i]), "ArxPaymentRouter: building not registered");
            require(amounts[i] >= getMinimumPayment(buildingIds[i]), "ArxPaymentRouter: insufficient amount");
            require(!noncesUsed[nonces[i]], "ArxPaymentRouter: nonce already used");

            noncesUsed[nonces[i]] = true;
            totalAmount += amounts[i];

            emit AccessPaid(buildingIds[i], msg.sender, amounts[i], nonces[i], block.timestamp);
        }

        // Transfer total amount once
        require(
            arxoToken.transferFrom(msg.sender, address(this), totalAmount),
            "ArxPaymentRouter: transfer failed"
        );

        // Distribute to each building
        for (uint256 i = 0; i < buildingIds.length; i++) {
            address building = registry.getBuildingWallet(buildingIds[i]);
            _distributePayment(building, amounts[i]);
        }
    }

    /**
     * @notice Distribute payment with 70/10/10/10 split
     * @param building Building wallet address (receives 70%)
     * @param totalAmount Total payment amount
     * @dev Internal function for payment distribution logic
     */
    function _distributePayment(address building, uint256 totalAmount) internal {
        (address maintainer, address treasury) = addresses.getAddresses();

        // Calculate 70/10/10/10 split
        uint256 buildingAmount = (totalAmount * 70) / 100;
        uint256 maintainerAmount = (totalAmount * 10) / 100;
        uint256 treasuryAmount = totalAmount - buildingAmount - maintainerAmount;

        // Distribute to all recipients
        require(arxoToken.transfer(building, buildingAmount), "ArxPaymentRouter: building transfer failed");
        require(arxoToken.transfer(maintainer, maintainerAmount), "ArxPaymentRouter: maintainer transfer failed");
        require(arxoToken.transfer(treasury, treasuryAmount), "ArxPaymentRouter: treasury transfer failed");

        emit PaymentDistributed(building, maintainer, treasury, buildingAmount, maintainerAmount, treasuryAmount);
    }

    /**
     * @notice Set minimum payment for a building
     * @param buildingId Building identifier
     * @param minimum Minimum payment amount in ARXO
     * @dev Only callable by owner (ArxOS LLC initially)
     */
    function setMinimumPayment(string calldata buildingId, uint256 minimum) external onlyOwner {
        require(registry.isBuildingRegistered(buildingId), "ArxPaymentRouter: building not registered");
        require(minimum > 0, "ArxPaymentRouter: zero minimum");

        uint256 effectiveTimestamp = block.timestamp + PRICE_UPDATE_DELAY;
        pendingPriceUpdates[buildingId] = ScheduledPrice(minimum, effectiveTimestamp);

        emit PriceUpdateScheduled(buildingId, minimum, effectiveTimestamp);
    }

    /**
     * @notice Get minimum payment for a building
     * @param buildingId Building identifier
     * @return Minimum payment amount (defaults to 0.01 ARXO if not set)
     */
    function getMinimumPayment(string calldata buildingId) public view returns (uint256) {
        // Check if there's a pending update that is now effective
        ScheduledPrice memory update = pendingPriceUpdates[buildingId];
        if (update.effectiveTimestamp != 0 && block.timestamp >= update.effectiveTimestamp) {
            return update.price;
        }

        uint256 minimum = minimumPayment[buildingId];
        return minimum > 0 ? minimum : DEFAULT_MINIMUM;
    }

    /**
     * @notice Apply a pending price update (public utility)
     * @param buildingId Building identifier
     */
    function applyPriceUpdate(string calldata buildingId) external {
        ScheduledPrice memory update = pendingPriceUpdates[buildingId];
        require(update.effectiveTimestamp != 0, "ArxPaymentRouter: no pending update");
        require(block.timestamp >= update.effectiveTimestamp, "ArxPaymentRouter: update not ready");

        uint256 oldMinimum = minimumPayment[buildingId];
        minimumPayment[buildingId] = update.price;
        delete pendingPriceUpdates[buildingId];

        emit MinimumPaymentUpdated(buildingId, oldMinimum, update.price);
    }

    /**
     * @notice Check if nonce has been used
     * @param nonce Nonce to check
     * @return True if nonce has been used
     */
    function isNonceUsed(bytes32 nonce) external view returns (bool) {
        return noncesUsed[nonce];
    }

    /**
     * @notice Emergency withdrawal (admin only)
     * @param amount Amount to withdraw
     * @dev Only for stuck funds, should never be needed in normal operation
     */
    function emergencyWithdraw(uint256 amount) external onlyOwner {
        require(arxoToken.transfer(msg.sender, amount), "ArxPaymentRouter: withdraw failed");
    }

    /**
     * @notice Get contract ARXO balance
     * @return Contract's ARXO token balance
     */
    function getBalance() external view returns (uint256) {
        return arxoToken.balanceOf(address(this));
    }
}
