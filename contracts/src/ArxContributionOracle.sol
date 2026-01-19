// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "./ArxosToken.sol";
import "./ArxRegistry.sol";
import "./ArxAddresses.sol";
import "./ArxOracleStaking.sol";

/**
 * @title ArxContributionOracle
 * @notice Verifies spatial data contributions and mints ARXO with 70/10/10/10 split
 * @dev Uses multi-oracle consensus (2-of-3) and EIP-712 typed signatures
 *      24-hour finalization delay allows for dispute resolution
 */
contract ArxContributionOracle is AccessControl, ReentrancyGuard, EIP712 {
    using ECDSA for bytes32;

    /// @notice Role identifier for oracle operators
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");

    /// @notice Minimum confirmations required to finalize contribution
    uint256 public constant MIN_CONFIRMATIONS = 2;

    /// @notice Finalization delay in seconds (24 hours)
    uint256 public constant FINALIZATION_DELAY = 24 hours;

    /// @notice Maximum proof age in seconds (1 hour)
    uint256 public constant MAX_PROOF_AGE = 1 hours;

    /// @notice ArxosToken contract
    ArxosToken public immutable arxoToken;

    /// @notice ArxRegistry contract
    ArxRegistry public immutable registry;

    /// @notice ArxAddresses contract
    ArxAddresses public immutable addresses;

    /// @notice ArxOracleStaking contract
    ArxOracleStaking public immutable staking;

    /// @notice ArxDisputeResolver contract
    address public disputeResolver;

    /// @notice EIP-712 typehash for ContributionProof (Updated for V2)
    bytes32 public constant CONTRIBUTION_PROOF_TYPEHASH =
        keccak256(
            "ContributionProof(bytes32 merkleRoot,bytes32 locationHash,bytes32 buildingHash,uint256 timestamp,uint256 dataSize,QualityMetrics quality)QualityMetrics(uint8 accuracy,uint8 completeness)"
        );

    /// @notice EIP-712 typehash for QualityMetrics
    bytes32 public constant QUALITY_METRICS_TYPEHASH =
        keccak256("QualityMetrics(uint8 accuracy,uint8 completeness)");

    /**
     * @notice Contribution proof structure
     * @param merkleRoot Root of spatial data Merkle tree
     * @param locationHash keccak256(abi.encodePacked(lat, lon, timestamp))
     * @param buildingHash keccak256(buildingId) for validation
     * @param timestamp Proof creation timestamp
     * @param dataSize Bytes of data contributed
     */
    /**
     * @notice Quality metrics for contribution
     * @param accuracy accuracy score 0-100
     * @param completeness completeness score 0-100
     */
    struct QualityMetrics {
        uint8 accuracy;
        uint8 completeness;
    }

    struct ContributionProof {
        bytes32 merkleRoot;
        bytes32 locationHash;
        bytes32 buildingHash;
        uint256 timestamp;
        uint256 dataSize;
        QualityMetrics quality;
    }

    struct WorkerStats {
        uint256 totalContributions;
        uint256 totalEarned;
        uint256 totalScore; // Cumulative quality score
    }

    mapping(address => WorkerStats) public workerStats;

    /**
     * @notice Pending contribution awaiting finalization
     * @param worker Worker wallet address
     * @param building Building wallet address
     * @param amount Total ARXO to mint
     * @param confirmations Number of oracle confirmations
     * @param proposedAt Timestamp when first proposed
     * @param finalized Whether contribution has been processed
     */
    struct PendingContribution {
        address worker;           // 20 bytes - SLOT 0
        uint8 confirmations;      // 1 byte   - SLOT 0 (packed)
        address building;         // 20 bytes - SLOT 1
        uint40 proposedAt;        // 5 bytes  - SLOT 1 (packed)
        string buildingId;        // dynamic  - SLOT 2+
        uint256 amount;           // 32 bytes - SLOT N
        uint8 accuracy;           // 1 byte   - SLOT N+1
        uint8 completeness;       // 1 byte   - SLOT N+1 (packed)
        bool finalized;           // 1 byte   - SLOT N+1 (packed)
        bool disputed;            // 1 byte   - SLOT N+1 (packed)
        mapping(address => bool) confirmed; // SLOT N+2
    }

    /// @notice Mapping from contribution ID to pending contribution
    mapping(bytes32 => PendingContribution) public pendingContributions;

    /// @notice Mapping from proof hash to usage status (prevents replay)
    mapping(bytes32 => bool) public usedProofs;

        /// @notice Mapping from contributionId to proof hash
        mapping(bytes32 => bytes32) public contributionProofHashes;

    // --- Phase 2: Revenue Splits ---
    enum SplitTier { STANDARD, PREMIUM, ENTERPRISE }
    
    struct RevenueConfig {
        uint256 workerBps;      // e.g. 7000 = 70%
        uint256 buildingBps;    // e.g. 1000 = 10%
        uint256 maintainerBps;  // e.g. 1000 = 10%
        uint256 treasuryBps;    // e.g. 1000 = 10%
    }
    
    mapping(SplitTier => RevenueConfig) public tierConfigs;
    mapping(string => SplitTier) public buildingTiers;
    
    event TierConfigUpdated(SplitTier indexed tier, uint256 workerBps, uint256 buildingBps, uint256 maintainerBps, uint256 treasuryBps);
    event BuildingTierUpdated(string indexed buildingId, SplitTier tier);

    /// @notice Emitted when contribution is proposed
    event ContributionProposed(
        bytes32 indexed contributionId,
        address indexed worker,
        string buildingId,
        uint256 amount,
        address oracle
    );

    /// @notice Emitted when oracle confirms contribution
    event ContributionConfirmed(bytes32 indexed contributionId, address indexed oracle, uint256 confirmations);

    /// @notice Emitted when contribution is finalized and minted
    event ContributionFinalized(
        bytes32 indexed contributionId,
        address indexed worker,
        uint256 amount
    );

    /// @notice Emitted when contribution is disputed
    event ContributionDisputed(bytes32 indexed contributionId, address indexed disputer, string reason);

    /**
     * @notice Contract constructor
     * @param admin Address with DEFAULT_ADMIN_ROLE
     * @param _arxoToken ArxosToken contract address
     * @param _registry ArxRegistry contract address
     * @param _addresses ArxAddresses contract address
     */
    constructor(
        address admin,
        address _arxoToken,
        address _registry,
        address _addresses,
        address _staking
    ) EIP712("ArxOS Contribution Oracle", "1") {
        require(admin != address(0), "ArxContributionOracle: zero admin");
        require(_arxoToken != address(0), "ArxContributionOracle: zero token");
        require(_registry != address(0), "ArxContributionOracle: zero registry");
        require(_addresses != address(0), "ArxContributionOracle: zero addresses");
        require(_staking != address(0), "ArxContributionOracle: zero staking");

        arxoToken = ArxosToken(_arxoToken);
        registry = ArxRegistry(_registry);
        addresses = ArxAddresses(_addresses);
        staking = ArxOracleStaking(_staking);

        // Initialize Default Tiers
        // Standard: 70/10/10/10
        tierConfigs[SplitTier.STANDARD] = RevenueConfig(7000, 1000, 1000, 1000);
        // Premium: 60/20/10/10 (Building gets more)
        tierConfigs[SplitTier.PREMIUM] = RevenueConfig(6000, 2000, 1000, 1000);
        // Enterprise: 50/30/10/10
        tierConfigs[SplitTier.ENTERPRISE] = RevenueConfig(5000, 3000, 1000, 1000);

        _grantRole(DEFAULT_ADMIN_ROLE, admin);
    }

    /**
     * @notice Returns the EIP-712 domain separator
     */
    function DOMAIN_SEPARATOR() external view returns (bytes32) {
        return _domainSeparatorV4();
    }

    /**
     * @notice Set the dispute resolver contract address
     * @param _resolver Address of the ArxDisputeResolver
     */
    function setResolver(address _resolver) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_resolver != address(0), "Zero resolver");
        disputeResolver = _resolver;
    }

    /**
     * @notice Propose a contribution (oracle 1 of 3)
     * @param buildingId Building identifier
     * @param worker Worker wallet address
     * @param amount Total ARXO to mint
     * @param proof Contribution proof with signature
     * @param signature Worker's EIP-712 signature
     * @dev Only callable by addresses with ORACLE_ROLE
     */
    function proposeContribution(
        string calldata buildingId,
        address worker,
        uint256 amount,
        ContributionProof calldata proof,
        bytes calldata signature
    ) external onlyRole(ORACLE_ROLE) nonReentrant {
        // Compute proof hash once
        bytes32 proofHash = keccak256(abi.encode(proof));
        require(worker != address(0), "ArxContributionOracle: zero worker");
        require(amount > 0, "ArxContributionOracle: zero amount");
        require(registry.isWorkerActive(worker), "ArxContributionOracle: worker not active");
        require(registry.isBuildingRegistered(buildingId), "Building not registered");

        // Verify proof
        _verifyProof(proof, worker, signature);

        // Generate unique contribution ID
        bytes32 contributionId = keccak256(abi.encodePacked(buildingId, worker, amount));

        // Store proof hash for replay protection at finalization
        contributionProofHashes[contributionId] = proofHash;

        PendingContribution storage pending = pendingContributions[contributionId];

        // First proposal initializes the contribution
        if (pending.confirmations == 0) {
            pending.worker = worker;
            pending.building = registry.getBuildingWallet(buildingId);
            pending.buildingId = buildingId;
            pending.amount = amount;
            pending.accuracy = proof.quality.accuracy;
            pending.completeness = proof.quality.completeness;
            pending.proposedAt = uint40(block.timestamp);

            emit ContributionProposed(contributionId, worker, buildingId, amount, msg.sender);
        }

        // Oracle confirms
        require(staking.hasMinStake(msg.sender), "ArxContributionOracle: insufficient stake");
        require(!pending.confirmed[msg.sender], "ArxContributionOracle: already confirmed");
        
        // Replay protection:
        // 1. If new contribution (confirms == 0), proof must be unused
        // 2. If existing, proof must match the one used to initialize it
        if (pending.confirmations == 0) {
            require(!usedProofs[proofHash], "ArxContributionOracle: proof already used");
            usedProofs[proofHash] = true;
        } else {
            require(contributionProofHashes[contributionId] == proofHash, "Proof mismatch");
        }

        pending.confirmed[msg.sender] = true;
        pending.confirmations++;

        emit ContributionConfirmed(contributionId, msg.sender, pending.confirmations);
    }

    /**
     * @notice Finalize contribution after delay and sufficient confirmations
     * @param contributionId Unique contribution identifier
     * @dev Can be called by anyone after finalization conditions are met
     */
    function finalizeContribution(bytes32 contributionId) external nonReentrant {
        PendingContribution storage pending = pendingContributions[contributionId];

        require(pending.confirmations > 0, "ArxContributionOracle: contribution not found");
        require(!pending.finalized, "Already finalized");
        require(!pending.disputed, "Contribution is disputed");

        require(
            pending.confirmations >= MIN_CONFIRMATIONS,
            "ArxContributionOracle: insufficient confirmations"
        );
        require(
            block.timestamp >= pending.proposedAt + FINALIZATION_DELAY,
            "ArxContributionOracle: finalization delay not met"
        );

        // Get system addresses
        (address maintainer, address treasury) = addresses.getAddresses();

        // Get Split Config
        SplitTier tier = buildingTiers[pending.buildingId];
        RevenueConfig memory config = tierConfigs[tier];
        
        // Calculate Shares (BPS = Basis Points, 10000 = 100%)
        // Calculate Reward Multiplier
        // Average of accuracy and completeness (0-100)
        uint256 qualityScore = (uint256(pending.accuracy) + uint256(pending.completeness)) / 2;
        // Scale amount: Base * Score / 100
        uint256 scaledAmount = (pending.amount * qualityScore) / 100;
        
        // Calculate Shares (BPS = Basis Points, 10000 = 100%)
        // Use scaledAmount for distribution
        uint256 workerAmount = (scaledAmount * config.workerBps) / 10000;
        uint256 buildingAmount = (scaledAmount * config.buildingBps) / 10000;
        uint256 maintainerAmount = (scaledAmount * config.maintainerBps) / 10000;
        uint256 treasuryAmount = (scaledAmount * config.treasuryBps) / 10000;
        
        // Enforce Caps via Token
        arxoToken.checkDailyCap(pending.worker, workerAmount, true); // true = worker
        arxoToken.checkDailyCap(pending.building, buildingAmount, false); // false = building
        
        // Prepare Batch Mint
        address[] memory recipients = new address[](4);
        recipients[0] = pending.worker;
        recipients[1] = pending.building;
        recipients[2] = maintainer;
        recipients[3] = treasury;
        
        uint256[] memory amounts = new uint256[](4);
        amounts[0] = workerAmount;
        amounts[1] = buildingAmount;
        amounts[2] = maintainerAmount;
        amounts[3] = treasuryAmount;
        
        // Mint Batch
        arxoToken.mintBatch(recipients, amounts);

        // Update Worker Stats
        WorkerStats storage stats = workerStats[pending.worker];
        stats.totalContributions++;
        stats.totalEarned += workerAmount;
        stats.totalScore += qualityScore;

        pending.finalized = true;
        emit ContributionFinalized(contributionId, pending.worker, scaledAmount);
    }

    /**
     * @notice Dispute a pending contribution (admin only)
     * @param contributionId Contribution to dispute
     * @param reason Reason for dispute
     * @dev Prevents finalization - used for fraud detection
     */
    function disputeContribution(
        bytes32 contributionId,
        string calldata reason
    ) external {
        require(hasRole(DEFAULT_ADMIN_ROLE, msg.sender) || hasRole(ORACLE_ROLE, msg.sender), "ArxContributionOracle: must be admin or oracle");
        PendingContribution storage pending = pendingContributions[contributionId];


        require(pending.confirmations > 0, "ArxContributionOracle: contribution not found");
        require(!pending.finalized, "Already finalized");

        // Mark as disputed (prevents minting) but do not finalize
        pending.disputed = true;
        emit ContributionDisputed(contributionId, msg.sender, reason);
    }

    /**
     * @notice Called by resolver to flag a contribution as disputed
     * @param contributionId Contribution ID
     * @param disputer Address of the disputer
     */
    function flagDisputed(bytes32 contributionId, address disputer) external {
        require(msg.sender == disputeResolver, "Only resolver");
        PendingContribution storage pending = pendingContributions[contributionId];
        require(pending.confirmations > 0, "Not found");
        require(!pending.finalized, "Finalized");
        require(!pending.disputed, "Already disputed");

        pending.disputed = true;
        emit ContributionDisputed(contributionId, disputer, "Dispute raised via Resolver");
    }

    /**
     * @notice Called by resolver to finalize dispute outcome
     * @param contributionId Contribution ID
     * @param valid True if contribution was ruled VALID, false if INVALID
     */
    function resolveDispute(bytes32 contributionId, bool valid) external {
        require(msg.sender == disputeResolver, "Only resolver");
        PendingContribution storage pending = pendingContributions[contributionId];
        
        require(pending.disputed, "Not disputed");
        require(!pending.finalized, "Already finalized");

        if (valid) {
            // Ruling: VALID. Lift dispute flag, allow finalizer to proceed (or auto-finalize?)
            // Auto-finalizing is simpler UX
            
            // Get system addresses
            (address maintainer, address treasury) = addresses.getAddresses();
    
            // Mint with 70/10/10/10 split
            arxoToken.mintContribution(
                pending.worker,
                pending.building,
                maintainer,
                treasury,
                pending.amount
            );
    
            pending.finalized = true;
            emit ContributionFinalized(contributionId, pending.worker, pending.amount);
        } else {
            // Ruling: INVALID. Mark finalized (dead) without minting
            pending.finalized = true;
            // No tokens minted.
        }
    }

    /**
     * @notice Verify contribution proof signature
     * @param proof Contribution proof data
     * @param worker Expected worker address
     * @param signature EIP-712 signature from worker
     * @dev Verifies timestamp, signature, and replay protection
     */
    function _verifyProof(
        ContributionProof calldata proof,
        address worker,
        bytes calldata signature
    ) internal {
        // Check proof age
        require(
            block.timestamp <= proof.timestamp + MAX_PROOF_AGE,
            "ArxContributionOracle: proof expired"
        );

        // Verify EIP-712 signature (V2 with QualityMetrics)
        bytes32 qualityHash = keccak256(abi.encode(
            QUALITY_METRICS_TYPEHASH,
            proof.quality.accuracy,
            proof.quality.completeness
        ));

        bytes32 structHash = keccak256(
            abi.encode(
                CONTRIBUTION_PROOF_TYPEHASH,
                proof.merkleRoot,
                proof.locationHash,
                proof.buildingHash,
                proof.timestamp,
                proof.dataSize,
                qualityHash
            )
        );

        bytes32 digest = _hashTypedDataV4(structHash);
        (address signer, ECDSA.RecoverError err, ) = ECDSA.tryRecoverCalldata(digest, signature);
        if (err != ECDSA.RecoverError.NoError) {
            revert("ArxContributionOracle: invalid signature");
        }
        require(signer == worker, "ArxContributionOracle: invalid signature");
        // No proof replay protection here; only checked at finalization
    }

    /**
     * @notice Get pending contribution details
     * @param contributionId Contribution identifier
     * @return worker Worker address
     * @return building Building address
     * @return amount Amount to mint
     * @return confirmations Number of confirmations
     * @return proposedAt Proposal timestamp
     * @return finalized Whether finalized
     */
    function getContribution(bytes32 contributionId)
        external
        view
        returns (
            address worker,
            address building,
            uint256 amount,
            uint256 confirmations,
            uint256 proposedAt,
            bool finalized
        )
    {
        PendingContribution storage pending = pendingContributions[contributionId];
        require(pending.proposedAt != 0, "Contribution does not exist");
        return (
            pending.worker,
            pending.building,
            pending.amount,
            uint256(pending.confirmations),
            uint256(pending.proposedAt),
            pending.finalized
        );
    }

    /**
     * @notice Check if oracle has confirmed a contribution
     * @param contributionId Contribution identifier
     * @param oracle Oracle address to check
     * @return True if oracle has confirmed
     */
    function hasConfirmed(bytes32 contributionId, address oracle) external view returns (bool) {
        return pendingContributions[contributionId].confirmed[oracle];
    }

    /**
     * @notice Update the revenue configuration for a specific tier
     * @param tier The tier to update
     * @param workerBps Basis points for worker (e.g. 7000 = 70%)
     * @param buildingBps Basis points for building
     * @param maintainerBps Basis points for maintainer vault
     * @param treasuryBps Basis points for treasury
     */
    function updateTierConfig(
        SplitTier tier,
        uint256 workerBps,
        uint256 buildingBps,
        uint256 maintainerBps,
        uint256 treasuryBps
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(workerBps + buildingBps + maintainerBps + treasuryBps == 10000, "Total must be 100%");
        
        tierConfigs[tier] = RevenueConfig(workerBps, buildingBps, maintainerBps, treasuryBps);
        emit TierConfigUpdated(tier, workerBps, buildingBps, maintainerBps, treasuryBps);
    }

    /**
     * @notice Assign a revenue tier to a building
     * @param buildingId The building identifier
     * @param tier The tier to assign
     */
    function setBuildingTier(string calldata buildingId, SplitTier tier) external onlyRole(DEFAULT_ADMIN_ROLE) {
        buildingTiers[buildingId] = tier;
        emit BuildingTierUpdated(buildingId, tier);
    }
}
