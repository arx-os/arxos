# Arxos on-chain contracts (Phase 5)

Minimal **Building registry** for Base L2 (or any EVM):

`BuildingId (bytes32) → official Root CID (bytes32) + controllers`

## BuildingRegistry.sol

| Function | Description |
|----------|-------------|
| `register(buildingId, initialRoot)` | Create building; caller becomes first controller |
| `setOfficialRoot(buildingId, newRoot)` | Controllers update official tip |
| `addController` / `removeController` | Multisig-style controller set |
| `getOfficialRoot` / `getBuilding` | Read API for indexers / clients |

**CID encoding:** store the raw 32-byte BLAKE3 digest (strip `b3:` + hex-decode).  
Off-chain tools reconstruct `b3:` + hex for CAS lookups.

## Deploy (Foundry)

```bash
# optional
forge build
forge create BuildingRegistry --rpc-url $BASE_SEPOLIA_RPC --private-key $PK
```

If Foundry is not installed, the Solidity source remains the contract source of truth;
CI can compile when `forge` is available.

## Design notes

- No token / rewards logic in v0 — scoring stays off-chain (`arxos-core` DePIN module).
- Controllers are EVM addresses; ed25519 authors map via an off-chain allowlist or future linking contract.
