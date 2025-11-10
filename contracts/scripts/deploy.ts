import { ethers, network } from "hardhat";

async function main() {
  console.log(`Deploying ARXO contracts to ${network.name}...`);

  const [deployer] = await ethers.getSigners();
  console.log("Deployer:", deployer.address);

  const link = process.env.LINK_TOKEN ?? ethers.ZeroAddress;
  const chainlinkOracle = process.env.CHAINLINK_ORACLE ?? ethers.ZeroAddress;
  const chainlinkJobId = process.env.CHAINLINK_JOB_ID ?? "0x00";
  const chainlinkFee = process.env.CHAINLINK_FEE ?? "10000000000000000"; // 0.01 LINK
  const usdcAddress = process.env.USDC_TOKEN ?? ethers.ZeroAddress;
  const uniswapRouter = process.env.UNISWAP_ROUTER ?? ethers.ZeroAddress;
  const uniswapPoolFee = Number(process.env.UNISWAP_POOL_FEE ?? 500); // 0.05%
  const treasury = process.env.ARXOS_TREASURY ?? deployer.address;

  const ArxosToken = await ethers.getContractFactory("ArxosToken");
  const token = await ArxosToken.deploy(chainlinkOracle);
  await token.waitForDeployment();
  console.log("ArxosToken:", await token.getAddress());

  const ArxStaking = await ethers.getContractFactory("ArxStaking");
  const staking = await ArxStaking.deploy(await token.getAddress());
  await staking.waitForDeployment();
  console.log("ArxStaking:", await staking.getAddress());

  const RevenueSplitter = await ethers.getContractFactory("RevenueSplitter");
  const splitter = await RevenueSplitter.deploy(
    usdcAddress,
    await token.getAddress(),
    await staking.getAddress(),
    treasury,
    uniswapRouter,
    uniswapPoolFee
  );
  await splitter.waitForDeployment();
  console.log("RevenueSplitter:", await splitter.getAddress());

  const TaxOracle = await ethers.getContractFactory("TaxOracle");
  const oracle = await TaxOracle.deploy(
    link,
    chainlinkOracle,
    chainlinkJobId as `0x${string}`,
    chainlinkFee,
    await token.getAddress()
  );
  await oracle.waitForDeployment();
  console.log("TaxOracle:", await oracle.getAddress());

  const tx = await token.setOracle(await oracle.getAddress());
  await tx.wait();
  console.log("Oracle set on ArxosToken");

  console.log("Deployment complete.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

