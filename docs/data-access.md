# Data access market (N5)

**Vision:** Software is free. Data buyers convert fiat → **$AXD** and pay for verified building data. Contributors who minted on input can hold or sell $AXD; demand for data supports the token.

## On-chain

`ArxPaymentRouter.payForAccess(buildingId, amount, nonce, maxPrice)`:

| Check | Rule |
| :--- | :--- |
| Building registered | `buildingId` = Building UUID |
| Amount | ≥ minimum for that building |
| maxPrice | Slippage guard (buyer max) |
| Nonce | One-time (replay protected) |

**Split of payment:** 70% building wallet · 10% maintainers · 20% treasury (remainder).

Contributor **mint** path remains separate (70/10/10/10 worker/building/maintainer/treasury).

## Off-chain CLI

```bash
# Free software: still use arx import/edit/export without paying

# Buyer prepares an access request
arx access quote --amount 1 --output access-request.json

# On-chain pay (requires blockchain build + deployed router/token)
cargo build --features blockchain
arx access pay --request access-request.json \
  --router $ARX_PAYMENT_ROUTER --token $ARX_TOKEN
```

## Foundry E2E

```bash
cd contracts
forge test --match-contract DataAccessPaymentE2E -vv
```

## Integration with contribute path

```text
Contributor: map building → contribute → mint $AXD (labor reward)
Buyer:       access quote → pay $AXD → host gates data on AccessPaid event
```

Hosts should only release sensitive exports after observing `AccessPaid` for the building UUID + valid nonce.
