// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ArxStaking
 * @notice Minimal staking pool distributing ARXO rewards pro-rata.
 *         Designed to be funded by the RevenueSplitter contract.
 */
contract ArxStaking is ReentrancyGuard {
    IERC20 public immutable arxo;

    uint256 public totalStaked;
    uint256 public accRewardPerShare; // scaled by 1e18

    struct StakeInfo {
        uint256 amount;
        uint256 rewardDebt;
    }

    mapping(address => StakeInfo) private stakes;

    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event RewardsFunded(address indexed funder, uint256 amount);
    event RewardsClaimed(address indexed user, uint256 amount);

    constructor(address arxoToken) {
        require(arxoToken != address(0), "ArxStaking: zero token");
        arxo = IERC20(arxoToken);
    }

    function stake(uint256 amount) external nonReentrant {
        require(amount > 0, "ArxStaking: amount zero");

        StakeInfo storage user = stakes[msg.sender];
        _harvest(msg.sender, user);

        arxo.transferFrom(msg.sender, address(this), amount);
        user.amount += amount;
        totalStaked += amount;

        user.rewardDebt = (user.amount * accRewardPerShare) / 1e18;
        emit Staked(msg.sender, amount);
    }

    function unstake(uint256 amount) external nonReentrant {
        StakeInfo storage user = stakes[msg.sender];
        require(amount > 0, "ArxStaking: amount zero");
        require(user.amount >= amount, "ArxStaking: insufficient stake");

        _harvest(msg.sender, user);

        user.amount -= amount;
        totalStaked -= amount;
        user.rewardDebt = (user.amount * accRewardPerShare) / 1e18;

        arxo.transfer(msg.sender, amount);
        emit Unstaked(msg.sender, amount);
    }

    function fundRewards(uint256 amount) external nonReentrant {
        require(amount > 0, "ArxStaking: amount zero");
        require(totalStaked > 0, "ArxStaking: no stakes");

        arxo.transferFrom(msg.sender, address(this), amount);
        accRewardPerShare += (amount * 1e18) / totalStaked;

        emit RewardsFunded(msg.sender, amount);
    }

    function claim() external nonReentrant {
        StakeInfo storage user = stakes[msg.sender];
        _harvest(msg.sender, user);
    }

    function pendingRewards(address account) external view returns (uint256) {
        StakeInfo storage user = stakes[account];
        uint256 accumulated = (user.amount * accRewardPerShare) / 1e18;
        if (accumulated < user.rewardDebt) {
            return 0;
        }
        return accumulated - user.rewardDebt;
    }

    function stakeInfo(address account) external view returns (StakeInfo memory) {
        return stakes[account];
    }

    function _harvest(address account, StakeInfo storage user) internal {
        if (user.amount == 0) {
            user.rewardDebt = 0;
            return;
        }

        uint256 accumulated = (user.amount * accRewardPerShare) / 1e18;
        uint256 pending;

        if (accumulated > user.rewardDebt) {
            pending = accumulated - user.rewardDebt;
        }

        user.rewardDebt = accumulated;

        if (pending > 0) {
            arxo.transfer(account, pending);
            emit RewardsClaimed(account, pending);
        }
    }
}

