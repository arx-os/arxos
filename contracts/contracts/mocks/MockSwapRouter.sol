// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract MockSwapRouter is ISwapRouter {
    IERC20 public immutable usdc;
    IERC20 public immutable arxo;

    constructor(address usdcToken, address arxoToken) {
        usdc = IERC20(usdcToken);
        arxo = IERC20(arxoToken);
    }

    function exactInputSingle(ExactInputSingleParams calldata params) external payable override returns (uint256 amountOut) {
        require(params.tokenIn == address(usdc), "MockSwapRouter: unexpected tokenIn");
        require(params.tokenOut == address(arxo), "MockSwapRouter: unexpected tokenOut");

        usdc.transferFrom(msg.sender, address(this), params.amountIn);
        uint256 balance = arxo.balanceOf(address(this));
        require(balance >= params.amountIn, "MockSwapRouter: insufficient ARXO");

        arxo.transfer(msg.sender, params.amountIn);
        return params.amountIn;
    }

    // Unused methods in tests
    function exactInput(ExactInputParams calldata) external payable override returns (uint256) {
        revert("MockSwapRouter: not implemented");
    }

    function exactOutputSingle(ExactOutputSingleParams calldata) external payable override returns (uint256) {
        revert("MockSwapRouter: not implemented");
    }

    function exactOutput(ExactOutputParams calldata) external payable override returns (uint256) {
        revert("MockSwapRouter: not implemented");
    }

    function uniswapV3SwapCallback(int256, int256, bytes calldata) external override {
        revert("MockSwapRouter: callback not implemented");
    }
}

