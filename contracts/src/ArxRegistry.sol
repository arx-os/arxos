// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ArxRegistry
 * @notice Manages soulbound identities for Workers and Buildings in ArxOS
 * @dev Workers receive ERC721 NFTs that cannot be transferred (soulbound)
 *      Buildings are registered with wallet addresses for payment distribution
 */
contract ArxRegistry is Ownable, ReentrancyGuard {
    /// @notice Worker identity NFT contract
    ArxWorkerID public immutable workerNFT;

    /// @notice Mapping from building ID to registered wallet address
    mapping(string => address) private buildingWallets;

    /// @notice Mapping from building ID to registration status
    mapping(string => bool) private buildingRegistered;

    /// @notice Mapping from worker address to registration status
    mapping(address => bool) private workerRegistered;

    /// @notice Counter for worker NFT token IDs
    uint256 private workerTokenIdCounter;

    /// @notice Emitted when a new worker is registered
    event WorkerRegistered(address indexed wallet, uint256 indexed tokenId, string metadata);

    /// @notice Emitted when a new building is registered
    event BuildingRegistered(string indexed buildingId, address indexed wallet);

    /// @notice Emitted when a building wallet is updated
    event BuildingWalletUpdated(string indexed buildingId, address indexed oldWallet, address indexed newWallet);

    /// @notice Emitted when a worker is deactivated
    event WorkerDeactivated(address indexed wallet, uint256 indexed tokenId);

    /**
     * @notice Contract constructor
     * @param _initialOwner Address that will own this contract
     */
    constructor(address _initialOwner) Ownable(_initialOwner) {
        workerNFT = new ArxWorkerID(address(this));
    }

    /**
     * @notice Register a new field worker with soulbound NFT
     * @param wallet Worker's wallet address
     * @param metadata IPFS CID or JSON metadata for worker profile
     * @dev Only callable by owner (ArxOS LLC initially)
     */
    function registerWorker(address wallet, string calldata metadata) external onlyOwner nonReentrant {
        require(wallet != address(0), "ArxRegistry: zero address");
        require(!workerRegistered[wallet], "ArxRegistry: worker already registered");

        uint256 tokenId = workerTokenIdCounter++;
        workerNFT.mint(wallet, tokenId, metadata);
        workerRegistered[wallet] = true;

        emit WorkerRegistered(wallet, tokenId, metadata);
    }

    /**
     * @notice Register a new building with wallet address
     * @param buildingId Unique building identifier (e.g., "ps-118")
     * @param wallet Building owner's wallet address
     * @dev Only callable by owner (ArxOS LLC initially)
     */
    function registerBuilding(string calldata buildingId, address wallet) external onlyOwner {
        require(wallet != address(0), "ArxRegistry: zero address");
        require(bytes(buildingId).length > 0, "ArxRegistry: empty building ID");
        require(!buildingRegistered[buildingId], "ArxRegistry: building already registered");

        buildingWallets[buildingId] = wallet;
        buildingRegistered[buildingId] = true;

        emit BuildingRegistered(buildingId, wallet);
    }

    /**
     * @notice Update building wallet address
     * @param buildingId Building identifier
     * @param newWallet New wallet address
     * @dev Only callable by owner - for handling lost keys or ownership transfers
     */
    function updateBuildingWallet(string calldata buildingId, address newWallet) external onlyOwner {
        require(newWallet != address(0), "ArxRegistry: zero address");
        require(buildingRegistered[buildingId], "ArxRegistry: building not registered");

        address oldWallet = buildingWallets[buildingId];
        buildingWallets[buildingId] = newWallet;

        emit BuildingWalletUpdated(buildingId, oldWallet, newWallet);
    }

    /**
     * @notice Deactivate a worker (emergency only)
     * @param wallet Worker's wallet address
     * @dev Does not burn NFT, just marks as deactivated
     *      Only callable by owner in case of fraud/abuse
     */
    function deactivateWorker(address wallet) external onlyOwner {
        require(workerRegistered[wallet], "ArxRegistry: worker not registered");
        workerRegistered[wallet] = false;

        uint256 tokenId = workerNFT.getTokenId(wallet);
        emit WorkerDeactivated(wallet, tokenId);
    }

    /**
     * @notice Get building wallet address
     * @param buildingId Building identifier
     * @return Wallet address for the building
     */
    function getBuildingWallet(string calldata buildingId) external view returns (address) {
        require(buildingRegistered[buildingId], "ArxRegistry: building not registered");
        return buildingWallets[buildingId];
    }

    /**
     * @notice Get worker wallet from NFT token ID
     * @param tokenId Worker NFT token ID
     * @return Worker wallet address
     */
    function getWorkerWallet(uint256 tokenId) external view returns (address) {
        return workerNFT.ownerOf(tokenId);
    }

    /**
     * @notice Check if worker is registered and active
     * @param wallet Worker's wallet address
     * @return True if worker is registered and active
     */
    function isWorkerActive(address wallet) external view returns (bool) {
        return workerRegistered[wallet];
    }

    /**
     * @notice Check if building is registered
     * @param buildingId Building identifier
     * @return True if building is registered
     */
    function isBuildingRegistered(string calldata buildingId) external view returns (bool) {
        return buildingRegistered[buildingId];
    }
}

/**
 * @title ArxWorkerID
 * @notice Soulbound NFT for worker identities
 * @dev Non-transferable ERC721 tokens representing field worker identities
 */
contract ArxWorkerID is ERC721 {
    /// @notice Registry contract that controls minting
    address public immutable registry;

    /// @notice Mapping from token ID to transfer lock status
    mapping(uint256 => bool) private transferLocked;

    /// @notice Mapping from token ID to metadata URI
    mapping(uint256 => string) private tokenMetadata;

    /// @notice Mapping from wallet to token ID (reverse lookup)
    mapping(address => uint256) private walletToTokenId;

    /// @notice Emitted when a new worker NFT is minted
    event WorkerNFTMinted(address indexed to, uint256 indexed tokenId, string metadata);

    /**
     * @notice Contract constructor
     * @param _registry Address of the ArxRegistry contract
     */
    constructor(address _registry) ERC721("ArxOS Worker ID", "ARXWORKER") {
        registry = _registry;
    }

    /**
     * @notice Mint a new soulbound worker NFT
     * @param to Worker wallet address
     * @param tokenId Token ID for this NFT
     * @param metadata IPFS CID or JSON metadata
     * @dev Only callable by registry contract
     */
    function mint(address to, uint256 tokenId, string calldata metadata) external {
        require(msg.sender == registry, "ArxWorkerID: only registry");
        require(to != address(0), "ArxWorkerID: zero address");

        _mint(to, tokenId);
        transferLocked[tokenId] = true; // Soulbound - cannot transfer
        tokenMetadata[tokenId] = metadata;
        walletToTokenId[to] = tokenId;

        emit WorkerNFTMinted(to, tokenId, metadata);
    }

    /**
     * @notice Get token ID for a worker wallet
     * @param wallet Worker wallet address
     * @return Token ID owned by wallet
     */
    function getTokenId(address wallet) external view returns (uint256) {
        return walletToTokenId[wallet];
    }

    /**
     * @notice Get metadata for a token ID
     * @param tokenId Token ID to query
     * @return Metadata string (IPFS CID or JSON)
     */
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        _requireOwned(tokenId);
        return tokenMetadata[tokenId];
    }

    /**
     * @notice Override transfer to enforce soulbound behavior
     * @dev Reverts all transfers for soulbound tokens
     */
    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        address from = _ownerOf(tokenId);

        // Allow minting (from == address(0))
        // Block all transfers (from != address(0))
        if (from != address(0)) {
            require(!transferLocked[tokenId], "ArxWorkerID: soulbound token");
        }

        return super._update(to, tokenId, auth);
    }
}
