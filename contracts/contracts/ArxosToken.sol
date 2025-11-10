// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ArxosToken
 * @notice ERC-20 token representing verified Total Assessed Value (TAV) for buildings.
 *         Minting is restricted to an authorized oracle that validates TAV proofs off-chain.
 */
contract ArxosToken is ERC20, Ownable {
    address public oracle;
    uint256 public totalAssessedValue;

    event OracleUpdated(address indexed previousOracle, address indexed newOracle);
    event MintedForBuilding(address indexed to, uint256 taxValue, uint256 amountMinted);

    constructor(address oracleAddress) ERC20("ArxOS Token", "ARXO") Ownable(msg.sender) {
        require(oracleAddress != address(0), "oracle address required");
        oracle = oracleAddress;
    }

    modifier onlyOracle() {
        require(msg.sender == oracle, "ArxosToken: caller is not oracle");
        _;
    }

    function setOracle(address newOracle) external onlyOwner {
        require(newOracle != address(0), "ArxosToken: zero address");
        emit OracleUpdated(oracle, newOracle);
        oracle = newOracle;
    }

    /**
     * @notice Mints ARXO proportional to verified TAV. 1 $ARXO == 1 USD TAV.
     * @param taxValueUSD Value confirmed by the oracle (USD with 2 decimals precision handled off-chain).
     * @param recipient Address receiving the minted tokens.
     */
    function mintForBuilding(uint256 taxValueUSD, address recipient) external onlyOracle {
        require(recipient != address(0), "ArxosToken: zero recipient");
        require(taxValueUSD > 0, "ArxosToken: zero tax value");

        totalAssessedValue += taxValueUSD;
        uint256 amount = taxValueUSD * (10 ** decimals());
        _mint(recipient, amount);
        emit MintedForBuilding(recipient, taxValueUSD, amount);
    }

    /**
     * @notice Burning is exposed for deflationary revenue mechanics.
     */
    function burn(uint256 amount) external {
        _burn(msg.sender, amount);
    }
}

