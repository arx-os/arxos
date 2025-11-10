import { expect } from "chai";
import { ethers } from "hardhat";

describe("ARXO Economy Contracts", () => {
  it("mints ARXO through the oracle flow", async () => {
    const [deployer, recipient] = await ethers.getSigners();

    const Token = await ethers.getContractFactory("ArxosToken");
    const token = await Token.deploy(deployer.address);
    await token.waitForDeployment();

    await expect(token.mintForBuilding(ethers.parseUnits("1000", 0), recipient.address))
      .to.emit(token, "MintedForBuilding")
      .withArgs(recipient.address, ethers.parseUnits("1000", 0), ethers.parseUnits("1000", 18));

    const balance = await token.balanceOf(recipient.address);
    expect(balance).to.equal(ethers.parseUnits("1000", 18));
  });

  it("distributes rewards to stakers through RevenueSplitter", async () => {
    const [oracle, staker, treasury] = await ethers.getSigners();

    const Token = await ethers.getContractFactory("ArxosToken");
    const token = await Token.deploy(oracle.address);
    await token.waitForDeployment();

    const Staking = await ethers.getContractFactory("ArxStaking");
    const staking = await Staking.deploy(await token.getAddress());
    await staking.waitForDeployment();

    const MockUSDC = await ethers.getContractFactory("MockERC20");
    const usdc = await MockUSDC.deploy("Mock USDC", "USDC", 6);
    await usdc.waitForDeployment();

    const MockRouter = await ethers.getContractFactory("MockSwapRouter");
    const router = await MockRouter.deploy(await usdc.getAddress(), await token.getAddress());
    await router.waitForDeployment();

    const Splitter = await ethers.getContractFactory("RevenueSplitter");
    const splitter = await Splitter.deploy(
      await usdc.getAddress(),
      await token.getAddress(),
      await staking.getAddress(),
      treasury.address,
      await router.getAddress(),
      500
    );
    await splitter.waitForDeployment();

    // Mint ARXO to router so swaps can succeed
    await token.connect(oracle).mintForBuilding(ethers.parseUnits("10000", 0), await router.getAddress());

    // Stake some ARXO
    await token.connect(oracle).mintForBuilding(ethers.parseUnits("1000", 0), staker.address);
    await token.connect(staker).approve(await staking.getAddress(), ethers.parseUnits("1000", 18));
    await staking.connect(staker).stake(ethers.parseUnits("1000", 18));

    // Provide USDC revenue
    await usdc.mint(await splitter.getAddress(), ethers.parseUnits("600", 6));

    await expect(splitter.connect(oracle).distribute(ethers.parseUnits("600", 6))).to.emit(splitter, "RevenueDistributed");

    const pending = await staking.pendingRewards(staker.address);
    expect(pending).to.be.gt(0);
  });
});

