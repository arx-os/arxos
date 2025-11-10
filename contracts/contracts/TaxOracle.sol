// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@chainlink/contracts/src/v0.8/operatorforwarder/Chainlink.sol";
import "@chainlink/contracts/src/v0.8/operatorforwarder/ChainlinkClient.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./ArxosToken.sol";

/**
 * @title TaxOracle
 * @notice Minimal Chainlink oracle client that requests assessed value data and mints ARXO when fulfilled.
 *         In production this contract would be operated by a Chainlink node. Here we provide a simplified
 *         pattern that can be extended with DON integration.
 */
contract TaxOracle is ChainlinkClient, Ownable {
    using Chainlink for Chainlink.Request;
    using Chainlink for Chainlink.Request;

    bytes32 public jobId;
    uint256 public fee;
    ArxosToken public immutable arxo;

    struct PendingMint {
        address recipient;
        uint256 taxValueUSD;
    }

    mapping(bytes32 => PendingMint) public pendingMints;

    event OracleRequest(bytes32 indexed requestId, address indexed recipient, uint256 taxValueUSD);
    event OracleFulfilled(bytes32 indexed requestId, uint256 assessedValue);
    event JobUpdated(bytes32 indexed jobId, uint256 fee);

    constructor(
        address link,
        address oracle,
        bytes32 job,
        uint256 oracleFee,
        address arxoToken
    ) Ownable(msg.sender) {
        require(link != address(0) && oracle != address(0), "TaxOracle: LINK/oracle required");
        require(arxoToken != address(0), "TaxOracle: ARXO required");

        _setChainlinkToken(link);
        _setChainlinkOracle(oracle);

        jobId = job;
        fee = oracleFee;
        arxo = ArxosToken(arxoToken);
    }

    function updateJob(bytes32 newJobId, uint256 newFee) external onlyOwner {
        require(newJobId != bytes32(0), "TaxOracle: jobId required");
        require(newFee > 0, "TaxOracle: fee required");
        jobId = newJobId;
        fee = newFee;
        emit JobUpdated(newJobId, newFee);
    }

    function requestAssessment(string calldata propertyId, address recipient, uint256 expectedTaxValue) external onlyOwner returns (bytes32 requestId) {
        require(bytes(propertyId).length > 0, "TaxOracle: property id required");
        require(recipient != address(0), "TaxOracle: recipient required");
        require(expectedTaxValue > 0, "TaxOracle: expected value required");

        Chainlink.Request memory request = _buildChainlinkRequest(jobId, address(this), this.fulfill.selector);
        request._add("property_id", propertyId);

        requestId = _sendChainlinkRequest(request, fee);
        pendingMints[requestId] = PendingMint({recipient: recipient, taxValueUSD: expectedTaxValue});

        emit OracleRequest(requestId, recipient, expectedTaxValue);
    }

    function fulfill(bytes32 requestId, uint256 assessedValueUSD) public recordChainlinkFulfillment(requestId) {
        PendingMint memory mint = pendingMints[requestId];
        require(mint.recipient != address(0), "TaxOracle: unknown request");

        delete pendingMints[requestId];

        uint256 valueToMint = assessedValueUSD == 0 ? mint.taxValueUSD : assessedValueUSD;
        arxo.mintForBuilding(valueToMint, mint.recipient);
        emit OracleFulfilled(requestId, valueToMint);
    }
}

