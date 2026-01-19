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

    /// @notice EIP-712 typehash for ContributionProof
    bytes32 public constant CONTRIBUTION_PROOF_TYPEHASH =
        keccak256(
            "ContributionProof(bytes32 merkleRoot,bytes32 locationHash,bytes32 buildingHash,uint256 timestamp,uint256 dataSize)"
        );

    /**
     * @notice Contribution proof structure
     * @param merkleRoot Root of spatial data Merkle tree
     * @param locationHash keccak256(abi.encodePacked(lat, lon, timestamp))
     * @param buildingHash keccak256(buildingId) for validation
     * @param timestamp Proof creation timestamp
     * @param dataSize Bytes of data contributed
     */
    struct ContributionProof {
        bytes32 merkleRoot;
        bytes32 locationHash;
        bytes32 buildingHash;
        uint256 timestamp;
        uint256 dataSize;
    }

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
        address worker;
        address building;
        uint256 amount;
        uint256 confirmations;
        uint256 proposedAt;
        bool finalized;
        mapping(address => bool) confirmed;
        bool disputed;
    }

    /// @notice Mapping from contribution ID to pending contribution
    mapping(bytes32 => PendingContribution) public pendingContributions;

    /// @notice Mapping from proof hash to usage status (prevents replay)
    mapping(bytes32 => bool) public usedProofs;

        /// @notice Mapping from contributionId to proof hash
        mapping(bytes32 => bytes32) public contributionProofHashes;

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
            pending.amount = amount;
            pending.proposedAt = block.timestamp;

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

        // Verify EIP-712 signature
        bytes32 structHash = keccak256(
            abi.encode(
                CONTRIBUTION_PROOF_TYPEHASH,
                proof.merkleRoot,
                proof.locationHash,
                proof.buildingHash,
                proof.timestamp,
                proof.dataSize
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
            pending.confirmations,
            pending.proposedAt,
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
}
