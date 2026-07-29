# Arxos Smart Contracts

Minimal EVM-compatible Building registry contract.

## Contract Architecture

The `BuildingRegistry.sol` contract maps a stable `BuildingId` to an official Root CID and a set of designated controller addresses:
`BuildingId (bytes32) → official Root CID (bytes32) + controllers`

### Interface Summary

| Function | Access | Description |
|----------|--------|-------------|
| `register(buildingId, initialRoot)` | Public | Registers a new building ID; caller becomes the first controller. |
| `setOfficialRoot(buildingId, newRoot)` | Controller | Updates the official Root CID tip. |
| `addController` / `removeController` | Controller | Manages the controller address set. |
| `getOfficialRoot` / `getBuilding` | View | Read API for clients and indexers. |

- **CID Encoding**: The registry stores the raw 32-byte BLAKE3 digest (obtained by decoding the hex representation and stripping the `b3:` prefix). Off-chain tools reconstruct the `b3:` prefix for CAS lookups.

## Build and Deployment (Foundry)

```bash
forge build
forge create BuildingRegistry --rpc-url $RPC_URL --private-key $PK
```

## Limitations & Scope

- **Off-chain scoring**: Token incentives and contributor scoring are evaluated off-chain via the core DePIN module.
- **Identity mapping**: Repository controller addresses are EVM accounts; ed25519 author keys map to these accounts via off-chain controller designations.
