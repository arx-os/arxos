# Field trial one-pager (Horizon B)

**Purpose:** Prove ArxOS on one real building with messy data.  
**Not:** Mainnet launch, multi-oracle market, or PWA polish.

## People

| Role | Who | Job |
| :--- | :--- | :--- |
| Capture node | | Laptop with `arx`, storage for LiDAR/IFC |
| Reviewer | | Accept/reject auto LiDAR rooms before export |
| Worker wallet | | Receives mint share (can be same person) |
| Buyer (optional) | | Pays $AXD for commercial access |

## Site

- Building name / address: ________________  
- Pain (safety / quote unknowns): ________________  
- Inputs: [ ] IFC  [ ] LiDAR  [ ] text corrections  

## Loop (do in order)

1. **Install** — `cargo install --path .` (see `docs/install.md`)  
2. **Init** — `arx init --name "…"`  
3. **Import** — `arx import …` IFC and/or LiDAR  
4. **Review** — `arx edit` with `review_status=accepted|rejected` on autos  
5. **Validate** — `arx validate` must be clean for contribute  
6. **Git** — `arx stage && arx commit -m "…"`  
7. **Export internal** — `arx export --format ifc` (or `--approved-only`)  
8. **Contribute** — `arx contribute` → package; chain steps if testnet/Anvil ready (`docs/horizon-a-ops.md`)  
9. **Buyer** — `arx access quote` → `pay` → `export --commercial` only with receipt  

## Success (yes/no)

| Question | Y/N |
| :--- | :---: |
| Did the model reduce unknowns vs walking in blind? | |
| Could a second person re-run steps 2–7 from the runbook? | |
| Was mint/pay understandable (if used)? | |
| What broke first? ________________ | |

## Rules

- Fix **only** blockers from this trial.  
- No new peripherals mid-trial.  
- Update `arxos_manifest.md` scorecard after (G4/G7/N9).

## After trial

Return notes to engineering. Horizon C (public chain, external oracles) only after **≥1** successful closed loop.
