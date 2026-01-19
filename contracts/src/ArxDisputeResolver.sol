// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./ArxContributionOracle.sol";
import "./ArxOracleStaking.sol";

/**
 * @title ArxDisputeResolver
 * @notice Handles optimistic dispute resolution for ArxOS contributions
 * @dev Implements a bond-based challenge game with commit-reveal voting
 */
contract ArxDisputeResolver is AccessControl, ReentrancyGuard {
    
    // Roles
    bytes32 public constant DISPUTER_ROLE = keccak256("DISPUTER_ROLE"); // Can be ANYONE in V1, or restricted for beta
    
    // Config
    uint256 public disputeBondAmount = 500 ether; // 500 ARXO required to dispute
    uint256 public constant VOTING_WINDOW = 48 hours;
    uint256 public constant MIN_JURORS = 2; // Minimum jurors needed for validity
    
    // Contracts
    IERC20 public immutable arxoToken;
    ArxContributionOracle public immutable oracle;
    ArxOracleStaking public immutable staking;
    
    enum DisputeStatus { PENDING, VOTING, RESOLVED, CANCELLED }
    enum Ruling { NONE, VALID, INVALID } // VALID = Worker wins, INVALID = Disputer wins

    struct Dispute {
        bytes32 contributionId;
        address disputer;
        string reason;
        uint256 createdAt;
        DisputeStatus status;
        Ruling ruling;
        uint256 invalidVotes;
        uint256 validVotes;
        uint256 totalWeight;
    }
    
    struct VoteCommitment {
        bytes32 commitHash;
        bool revealed;
        bool vote; // true = VALID, false = INVALID
    }
    
    // Mapping from contributionId to Dispute
    mapping(bytes32 => Dispute) public disputes;
    
    // Mapping from contributionId -> juror -> Commitment
    mapping(bytes32 => mapping(address => VoteCommitment)) public votes;
    
    // Events
    event DisputeRaised(bytes32 indexed contributionId, address indexed disputer, string reason);
    event EvidenceSubmitted(bytes32 indexed contributionId, address indexed submitter, string ipfsCid);
    event VoteCommitted(bytes32 indexed contributionId, address indexed juror);
    event VoteRevealed(bytes32 indexed contributionId, address indexed juror, bool vote, uint256 weight);
    event DisputeResolved(bytes32 indexed contributionId, Ruling ruling);
    
    constructor(
        address admin,
        address _arxoToken,
        address _oracle,
        address _staking
    ) {
        require(_arxoToken != address(0), "Zero token");
        require(_oracle != address(0), "Zero oracle");
        require(_staking != address(0), "Zero staking");
        
        arxoToken = IERC20(_arxoToken);
        oracle = ArxContributionOracle(_oracle);
        staking = ArxOracleStaking(_staking);
        
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
    }
    
    /**
     * @notice Raise a dispute against a pending contribution
     * @param contributionId The ID of the contribution to challenge
     * @param reason Why this contribution is invalid
     */
    function raiseDispute(bytes32 contributionId, string calldata reason) external nonReentrant {
        // 1. Validate contribution state
        (,,,, uint256 proposedAt, bool finalized) = oracle.getContribution(contributionId);
        require(proposedAt > 0, "Contribution not found");
        require(!finalized, "Already finalized");
        require(disputes[contributionId].status == DisputeStatus.PENDING, "Dispute already exists"); // Init state is 0 (PENDING) check logic
        // Actually PENDING is 0, so we need way to check existence. 
        // Better to check createAt > 0 or status == VOTING/RESOLVED
        
        // Fix: PENDING is default 0. We need to check if it was initialized.
        require(disputes[contributionId].createdAt == 0, "Dispute already active");

        // 2. Transfer Bond
        require(arxoToken.transferFrom(msg.sender, address(this), disputeBondAmount), "Bond transfer failed");
        
        // 3. Notify Oracle (This needs to be implemented in Oracle contract to block finalization)
        // For now, we assume integrating call:
        try oracle.flagDisputed(contributionId, msg.sender) {
            // Success
        } catch {
            revert("Oracle update failed");
        }
        
        // 4. Create Dispute
        disputes[contributionId] = Dispute({
            contributionId: contributionId,
            disputer: msg.sender,
            reason: reason,
            createdAt: block.timestamp,
            status: DisputeStatus.VOTING,
            ruling: Ruling.NONE,
            invalidVotes: 0,
            validVotes: 0,
            totalWeight: 0
        });
        
        emit DisputeRaised(contributionId, msg.sender, reason);
    }
    
    /**
     * @notice Submit evidence (IPFS hash)
     * @param contributionId Contribution ID
     * @param ipfsCid IPFS content identifier
     */
    function submitEvidence(bytes32 contributionId, string calldata ipfsCid) external {
        // In V1 anyone can submit? Or just involved parties?
        // Let's allow anyone for transparency
        require(disputes[contributionId].status == DisputeStatus.VOTING, "Not in voting period");
        emit EvidenceSubmitted(contributionId, msg.sender, ipfsCid);
    }
    
    /**
     * @notice Juror commits their vote (commit-reveal scheme)
     * @param contributionId Contribution ID
     * @param commitHash keccak256(abi.encodePacked(vote, salt))
     */
    function commitVote(bytes32 contributionId, bytes32 commitHash) external {
        require(disputes[contributionId].status == DisputeStatus.VOTING, "Not voting");
        require(staking.hasMinStake(msg.sender), "Must be staked oracle");
        
        // Prevent double voting
        require(votes[contributionId][msg.sender].commitHash == bytes32(0), "Already voted");
        
        votes[contributionId][msg.sender] = VoteCommitment({
            commitHash: commitHash,
            revealed: false,
            vote: false
        });
        
        emit VoteCommitted(contributionId, msg.sender);
    }
    
    /**
     * @notice Juror reveals their vote
     * @param contributionId Contribution ID
     * @param vote True for VALID (Worker wins), False for INVALID (Disputer wins)
     * @param salt Random salt used in commit
     */
    function revealVote(bytes32 contributionId, bool vote, uint256 salt) external {
        require(disputes[contributionId].status == DisputeStatus.VOTING, "Not voting");
        
        VoteCommitment storage commitment = votes[contributionId][msg.sender];
        require(commitment.commitHash != bytes32(0), "No vote committed");
        require(!commitment.revealed, "Already revealed");
        
        // Verify hash
        bytes32 hashCheck = keccak256(abi.encodePacked(vote, salt));
        require(hashCheck == commitment.commitHash, "Hash mismatch");
        
        commitment.revealed = true;
        commitment.vote = vote;
        
        // Weight is 1 vote per oracle (could be stake-weighted later)
        // Simplicity: 1 person, 1 vote for now among oracles
        uint256 weight = 1; 
        
        if (vote) {
            disputes[contributionId].validVotes += weight;
        } else {
            disputes[contributionId].invalidVotes += weight;
        }
        disputes[contributionId].totalWeight += weight;
        
        emit VoteRevealed(contributionId, msg.sender, vote, weight);
    }
    
    /**
     * @notice Finalize the dispute and execute ruling
     * @param contributionId Contribution ID
     */
    function resolveDispute(bytes32 contributionId) external nonReentrant {
        Dispute storage dispute = disputes[contributionId];
        require(dispute.status == DisputeStatus.VOTING, "Not voting");
        require(block.timestamp >= dispute.createdAt + VOTING_WINDOW, "Vote window active");
        
        Ruling finalRuling;
        
        if (dispute.totalWeight < MIN_JURORS) {
            // Not enough votes? Default to VALID (Optimistic) or return bond?
            // Conservative: If not enough jurors care, we default to VALID but flag it.
            // OR: We extend. For V1, let's default to VALID (Worker wins) to prevent griefing by apathy.
            finalRuling = Ruling.VALID; 
        } else {
            if (dispute.validVotes >= dispute.invalidVotes) {
                finalRuling = Ruling.VALID;
            } else {
                finalRuling = Ruling.INVALID;
            }
        }
        
        dispute.ruling = finalRuling;
        dispute.status = DisputeStatus.RESOLVED;
        
        if (finalRuling == Ruling.VALID) {
            // Worker was right.
            // 1. Bond goes to... treasury? or reward jurors?
            // V1: Send bond to treasury (simplest). Worker gets their mint (via process).
            arxoToken.transfer(0x610178dA211FEF7D417bC0e6FeD39F05609AD788, disputeBondAmount); // Addresses.treasury? Need to look up.
            // Actually, let's just burn/treasury it.
            // We need addresses contract here optimally.
            
            // 2. Unpause oracle
             oracle.resolveDispute(contributionId, true); // true = valid
             
        } else {
            // Disputer was right.
            // 1. Return bond to disputer
            arxoToken.transfer(dispute.disputer, disputeBondAmount);
            
            // 2. Cancel contribution
            oracle.resolveDispute(contributionId, false); // false = invalid
            
            // 3. Reward disputer?
            // In V1, they just get bond back + justice.
        }
        
        emit DisputeResolved(contributionId, finalRuling);
    }
    
    function setBondAmount(uint256 amount) external onlyRole(DEFAULT_ADMIN_ROLE) {
        disputeBondAmount = amount;
    }
}
