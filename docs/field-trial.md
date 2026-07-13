# Field trial one-pager (Horizon B / L1)

**Purpose:** Prove ArxOS on one real building with messy data.  
**Not:** Mainnet launch, multi-oracle market, or PWA polish.

**Before start:** complete and sign **`docs/pilot-charter.md`**.  
**Install:** pinned release per **`docs/pilot-release.md`**.  
**Workflow:** **`docs/l1-supported-workflow.md`** only for L1 success.  
**Transfer:** **`docs/second-person-checklist.md`** (R5).

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

Follow **`docs/l1-supported-workflow.md`** in full. Summary:

1. **Install** — pinned tag only (`docs/pilot-release.md`)  
2. **Init** — `arx init --name "…"`  
3. **Import** — IFC and/or LiDAR  
4. **Review** — accept/reject autos; no official use of unreviewed `proposed`  
5. **Validate** — clean errors  
6. **Git** — stage/commit; push only to internal remote  
7. **Export internal** — free export; use `--approved-only` for reviewed LiDAR handoff  

**Optional demo only (not L1 success):** contribute / access / commercial (`docs/horizon-a-ops.md`).

## Success (yes/no)

| Question | Y/N |
| :--- | :---: |
| Charter signed (`docs/pilot-charter.md`)? | |
| Second-person checklist pass/conditional? | |
| Did the model reduce unknowns vs walking in blind? | |
| Site IFC/LiDAR limits written (R1/R2)? | |
| What broke first? ________________ | |

## Rules

- Fix **only** blockers from this trial.  
- No new peripherals mid-trial.  
- Update `arxos_manifest.md` scorecard after (G4/G7/N9).

## After trial

Return notes to engineering. Horizon C (public chain, external oracles) only after **≥1** successful closed loop.
