import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "@typechain/hardhat";
import * as dotenv from "dotenv";

dotenv.config();

const {
  POLYGON_MUMBAI_RPC_URL,
  POLYGON_AMOY_RPC_URL,
  PRIVATE_KEY,
  ETHERSCAN_API_KEY,
} = process.env;

const sharedAccounts =
  PRIVATE_KEY !== undefined ? [PRIVATE_KEY] : { mnemonic: "test test test test test test test test test test test junk" };

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  defaultNetwork: "hardhat",
  networks: {
    hardhat: {
      chainId: 31337,
    },
    polygonMumbai: {
      url: POLYGON_MUMBAI_RPC_URL || "https://rpc.ankr.com/polygon_mumbai",
      accounts: sharedAccounts,
    },
    polygonAmoy: {
      url: POLYGON_AMOY_RPC_URL || "https://rpc-amoy.polygon.technology",
      accounts: sharedAccounts,
    },
  },
  etherscan: {
    apiKey: ETHERSCAN_API_KEY || "",
  },
  gasReporter: {
    enabled: process.env.REPORT_GAS === "true",
    currency: "USD",
    coinmarketcap: process.env.COINMARKETCAP_API_KEY,
    showTimeSpent: true,
  },
  typechain: {
    outDir: "typechain",
    target: "ethers-v6",
  },
};

export default config;

