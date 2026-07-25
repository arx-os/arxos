# Security policy

## Reporting

If you believe you have found a vulnerability in ArxOS, **do not open a public issue**.  
Email the maintainers privately (see GitHub org / repo security contacts) with:

- Description and impact
- Reproduction steps
- Affected version / commit SHA

## What this project handles

| Surface | Risk class | Notes |
| :--- | :--- | :--- |
| **CLI + `building.yaml`** | Local data integrity | Facility models may be sensitive; keep remotes private (R7) |
| **`arx agent` (optional)** | Network-facing capture node | Token auth; default bind `0.0.0.0` for LAN — restrict network |
| **Blockchain feature** | Signing / funds | Keys via env only; no silent mainnet defaults |
| **Contracts / Foundry** | On-chain | Lab Anvil keys are public test keys |

## Hard rules (operators)

1. **Never commit** `.env`, `.env.arx`, `contracts/deployed.env`, private keys, or facility models to public remotes.
2. **Pilot data** stays on private Git remotes and classified storage (see `docs/pilot/data-classification.md`).
3. **Agent ROOT TOKEN** is printed once at start — treat like a password. Prefer `Authorization: Bearer` over `?token=` (query strings land in logs/history).
4. **Do not fund Anvil account #0** (or any key checked into lab scripts) on public networks. That key is public knowledge for local Foundry only.
5. **Blockchain signing:** set `ARX_PRIVATE_KEY` (or pass a key flag). Silent Anvil fallback requires `ARX_ALLOW_ANVIL_DEFAULT_KEY=1`.

## Agent hardening (current)

| Control | Default |
| :--- | :--- |
| Auth | Shared root token (capability-scoped); constant-time compare |
| Bind | `0.0.0.0:8787` (LAN) — override with `ARX_AGENT_BIND` / `ARX_AGENT_PORT` |
| UDP discovery | **Off** unless `ARX_AGENT_DISCOVERY=1` |
| Discovery payload | Non-secret peer id only — **never** the root token |
| File reads | Path confined under repo root |
| Transport | Cleartext HTTP/WS on LAN (no TLS yet) — trusted network only |

## Dependency advisories

Run periodically:

```bash
cargo audit
cargo audit --features full
```

Known residual issues (as of 2026-07-25) often come from **optional** stacks:

| Area | Example | Status |
| :--- | :--- | :--- |
| `russh` 0.40 (agent SSH optional code) | High severity allocation CVEs; upgrade path ≥0.60 | SSH server not started by default agent HTTP path; plan upgrade or `agent-ssh` feature split |
| `ethers` / old `ring` 0.16 / `rustls-webpki` 0.101 | Via `blockchain` + ethers 2.x | Residual until ethers/alloy migration |
| `rsa` (Marvin) via `jsonwebtoken`/`octocrab` | Medium; no upstream fix in some graphs | Agent GitHub collab only |

Default **compiler + TUI** builds avoid most of the network crypto surface.  
**L1 pilot success does not require** agent SSH, blockchain, or collab.

## Secret scanning

- `.gitignore` excludes env files, keys, PEM/P12, local deploy env.
- `.secrets.baseline` supports detect-secrets workflows when configured.
- CI / pre-push: prefer `cargo audit` + a secrets scanner on changed files.

## What we do **not** claim

- Hardened multi-tenant SaaS isolation
- Production HSM key management
- Browser TLS termination for the agent
- Formal verification of contracts for mainnet

Security posture is **local-first / edge capture node** honesty — not “bank-grade cloud.”
