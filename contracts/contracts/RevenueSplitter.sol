// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol";

interface IArxosToken is IERC20 {
    function burn(uint256 amount) external;
}

interface IArxStaking {
    function fundRewards(uint256 amount) external;
}

/**
 * @title RevenueSplitter
 * @notice Splits USDC inflows according to the ARXO economy design:
 *         60% swapped to ARXO and sent to stakers, 20% swapped and burned, 20% to the LLC treasury.
 */
contract RevenueSplitter is Ownable {
    IERC20 public immutable usdc;
    IArxosToken public immutable arxo;
    IArxStaking public staking;
    address public treasury;
    ISwapRouter public immutable uniswapRouter;
    uint24 public immutable poolFee;

    event RevenueDistributed(uint256 usdcAmount, uint256 toStakers, uint256 burned, uint256 toTreasury);
    event StakingUpdated(address indexed previous, address indexed current);
    event TreasuryUpdated(address indexed previous, address indexed current);

    constructor(
        address usdcToken,
        address arxoToken,
        address stakingAddress,
        address treasuryAddress,
        address router,
        uint24 fee
    ) Ownable(msg.sender) {
        require(usdcToken != address(0), "RevenueSplitter: USDC required");
        require(arxoToken != address(0), "RevenueSplitter: ARXO required");
        require(stakingAddress != address(0), "RevenueSplitter: staking required");
        require(treasuryAddress != address(0), "RevenueSplitter: treasury required");
        require(router != address(0), "RevenueSplitter: router required");
        require(fee > 0, "RevenueSplitter: pool fee required");

        usdc = IERC20(usdcToken);
        arxo = IArxosToken(arxoToken);
        staking = IArxStaking(stakingAddress);
        treasury = treasuryAddress;
        uniswapRouter = ISwapRouter(router);
        poolFee = fee;
    }

    function setStaking(address newStaking) external onlyOwner {
        require(newStaking != address(0), "RevenueSplitter: zero staking");
        emit StakingUpdated(address(staking), newStaking);
        staking = IArxStaking(newStaking);
    }

    function setTreasury(address newTreasury) external onlyOwner {
        require(newTreasury != address(0), "RevenueSplitter: zero treasury");
        emit TreasuryUpdated(treasury, newTreasury);
        treasury = newTreasury;
    }

    function distribute(uint256 usdcAmount) external onlyOwner {
        require(usdcAmount > 0, "RevenueSplitter: amount zero");
        require(usdc.balanceOf(address(this)) >= usdcAmount, "RevenueSplitter: insufficient USDC");

        uint256 toStakers = (usdcAmount * 60) / 100;
        uint256 toBurn = (usdcAmount * 20) / 100;
        uint256 toTreasury = usdcAmount - toStakers - toBurn;

        uint256 arxoForStakers = _swapUSDCForARXO(toStakers);
        uint256 arxoForBurn = _swapUSDCForARXO(toBurn);

        arxo.approve(address(staking), arxoForStakers);
        staking.fundRewards(arxoForStakers);

        arxo.burn(arxoForBurn);

        require(usdc.transfer(treasury, toTreasury), "RevenueSplitter: treasury transfer failed");

        emit RevenueDistributed(usdcAmount, arxoForStakers, arxoForBurn, toTreasury);
    }

    function _swapUSDCForARXO(uint256 amountIn) internal returns (uint256) {
        if (amountIn == 0) {
            return 0;
        }

        usdc.approve(address(uniswapRouter), amountIn);

        ISwapRouter.ExactInputSingleParams memory params = ISwapRouter.ExactInputSingleParams({
            tokenIn: address(usdc),
            tokenOut: address(arxo),
            fee: poolFee,
            recipient: address(this),
            deadline: block.timestamp + 300,
            amountIn: amountIn,
            amountOutMinimum: 0,
            sqrtPriceLimitX96: 0
        });

        return uniswapRouter.exactInputSingle(params);
    }
}

