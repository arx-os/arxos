# Field trial one-pager (Horizon B / L1)

**Purpose:** Prove ArxOS on one real building with messy data.  
**Not:** Mainnet launch, multi-oracle market, or PWA polish.

**Start here:** **`docs/field-handoff.md`** (ordered B0–B3).  
**Before work:** sign **`docs/pilot-charter.md`**.  
**Install:** pin **`v2.0.0-pilot.3`** per **`docs/pilot-release.md`**.  
**Workflow:** **`docs/l1-supported-workflow.md`** only for L1 success.  
**Transfer:** **`docs/second-person-checklist.md`** (R5).  
**Site evidence:** **`docs/field-truth-log.md`**.

## People (L1)

| Role | Who | Job |
| :--- | :--- | :--- |
| Pilot owner | | Signs charter; authority for the site |
| Capture / ops tech | | Laptop with pinned `arx`, storage for IFC/LiDAR |
| Reviewer | | Accept/reject auto LiDAR rooms before official export |
| Second person | | Cold-start walkthrough (not the doc author) |

Economy roles (worker wallet, buyer) are **out of L1 success** — optional demo only (`docs/horizon-a-ops.md`).

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
6. **Git** — `arx stage` + `arx commit -m "…"`; push only to internal remote  
7. **Export internal** — free export; use `--approved-only` for reviewed LiDAR handoff  

**Optional demo only (not L1 success):** contribute / access / commercial (`docs/horizon-a-ops.md`).

## Success (yes/no)

| Question | Y/N |
| :--- | :---: |
| Charter signed (`docs/pilot-charter.md`)? | |
| Second-person checklist pass/conditional? | |
| Data classification completed? | |
| Did the model reduce unknowns vs walking in blind? | |
| Site IFC/LiDAR limits written (`docs/field-truth-log.md`)? | |
| What broke first? ________________ | |

## Rules

- Fix **only** blockers from this trial.  
- No new peripherals mid-trial.  
- No mainnet token dependency.  
- Update `arxos_manifest.md` §1.6 after evidence lands.

## After trial

Return notes to engineering. Horizon C (public chain, external oracles) only after **L1 exit** criteria in the manifest.
