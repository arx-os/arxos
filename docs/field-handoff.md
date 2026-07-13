# L1 field handoff packet (ordered)

**Audience:** Pilot owner (district IT / field tech with authority)  
**Engineering status:** Templates, pin tooling, and sample IFC smoke are ready.  
**What only you can close:** signatures, second-person walkthrough, real-site evidence.

Do these in order. Do **not** skip to chain/token work.

---

## B0 — Safety (R10)

1. Read and fill **`docs/pilot-charter.md`** (parties, site, pin blank, initials on §3).  
2. Leadership/pilot owner **signs** the charter before treating any export as official.  
3. Culture rule stays in force: human + licensed docs win; no unreviewed `proposed` as official.

## B1 — Transfer + pin (R5, R9)

1. Engineering has cut tag **`v2.0.0-pilot.1`** @ **`ba33e6ba7ebad55a61a54a9dae68d4508dbdd9d7`** (see `docs/pilot-release.md`).  
2. Record **that tag + SHA** in charter §2 and install from that pin only.  
3. Second person (not the doc author) runs **`docs/second-person-checklist.md`** on a district-like machine using only **`docs/l1-supported-workflow.md`**.  
4. File stuck points as backlog; do not invent parallel tools.

## B2 — Data class (R7)

1. Complete **`docs/data-classification.md`**.  
2. Tick charter §4 (internal remote, export who, no student PII).  
3. Put pilot Git on the **approved internal** remote — not public GitHub by default.

## B3 — Field truth (R1, R2, R6)

1. On **real** district IFC and/or scan hardware, fill **`docs/field-truth-log.md`** (interop matrix, false +/−, timing/OOM notes).  
2. Escalate only true blockers to engineering; eng does not invent field evidence.

## B4 — Chain stays optional (R3, R8)

L1 success = free software loop only. No mainnet $AXD. Anvil/testnet only if charter §5 names a requester.

---

## Eng-automated check (does not replace R5)

```bash
# From pinned checkout, after cargo build/install:
./scripts/l1_smoke.sh
# optional: ./scripts/l1_smoke.sh /path/to/real.ifc
```

## After evidence

Update **`arxos_manifest.md` §1.6** obligation statuses with paths to signed/completed artifacts (or private pilot folder paths if classification forbids commit).

**Related:** `arxos_manifest.md` §1.6 · §10.2 Horizon B
