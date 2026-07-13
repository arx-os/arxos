# Full ArxOS lab closed loop (engineering)

**Purpose:** One command that proves the product spine in the lab.  
**Not:** District L1 exit (see `docs/field-handoff.md` and §1.6 obligations).

## What “full loop” means here

```text
Compiler:  init → import → validate → export → git stage/commit
Labor:     contribute package (off-chain commitment)
Host:      commercial export refuse → grant/receipt → allow
Chain:     Foundry mint E2E (2-of-3 → finalize → $AXD split)
Buyer:     Foundry payForAccess E2E
Optional:  Anvil deploy → .env.arx (N8 helpers)
```

## Run

```bash
# From repo root (default: Rust + l1_smoke + forge E2Es)
./scripts/full_lab_loop.sh

# Faster local (fewer integration tests)
QUICK=1 ./scripts/full_lab_loop.sh

# Also start/deploy Anvil stack
RUN_ANVIL=1 ./scripts/full_lab_loop.sh

# Compiler only (no Foundry)
SKIP_FORGE=1 ./scripts/full_lab_loop.sh
```

CI: `.github/workflows/full-lab-loop.yml` runs `QUICK=1 ./scripts/full_lab_loop.sh` on `main` / PRs.

## Related

| Path | Role |
| :--- | :--- |
| `./scripts/l1_smoke.sh` | Free-software + commercial gate only |
| `./scripts/horizon_a_deploy_env.sh` | Anvil deploy → `.env.arx` |
| `./scripts/pin_pilot_release.sh` | R9 pilot pin |
| `docs/horizon-a-ops.md` | Manual mint/pay ops |
| `docs/field-handoff.md` | District B0–B3 (field) |
| `arxos_manifest.md` §1.6 / §10 | Obligations + horizons |
