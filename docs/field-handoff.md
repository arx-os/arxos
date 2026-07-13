# L1 field handoff packet (ordered)

**Audience:** Pilot owner (district IT / field tech with authority)  
**Engineering status:** Templates, pin tooling, and sample IFC smoke are ready.  
**What only you can close:** signatures, second-person walkthrough, real-site evidence.

Do these in order. Do **not** skip to chain/token work or CAD plugins.

**Map:** [INDEX.md](./INDEX.md) · **Authority:** [`arxos_manifest.md`](../arxos_manifest.md) §1.1a · §1.5–1.6  
**Living roadmap (phases HB0–HB7):** [horizon-b-roadmap.md](./horizon-b-roadmap.md)

---

## B0 — Safety (R10)

1. Read and fill **[pilot-charter.md](./pilot-charter.md)** (parties, site, pin blank, initials on §3).  
2. Leadership/pilot owner **signs** the charter before treating any export as official.  
3. Culture rule stays in force: human + licensed docs win; no unreviewed `proposed` as official.

## B1 — Transfer + pin (R5, R9)

1. Use the **preferred pin** in [pilot-release.md](./pilot-release.md): **`v2.0.0-pilot.4`** @ `659bbd9f369c0b942f150983b204ea054fc595a0`.  
2. Record **that tag + full SHA** in charter §2 and install from that pin only (`cargo install --path .` = default: compiler + TUI).  
3. Second person (not the doc author) runs **[second-person-checklist.md](./second-person-checklist.md)** on a district-like machine using only **[l1-supported-workflow.md](./l1-supported-workflow.md)**.  
4. File stuck points as backlog; do not invent parallel tools or CAD plugins.

## B2 — Data class (R7)

1. Complete **[data-classification.md](./data-classification.md)**.  
2. Tick charter §4 (internal remote, export who, no student PII).  
3. Put pilot Git on the **approved internal** remote — not public GitHub by default.

## B3 — Field truth (R1, R2, R6)

1. On **real** district IFC (clean export from vendor BIM — **no plugins**) and/or scan hardware, fill **[field-truth-log.md](./field-truth-log.md)** (interop matrix, false +/−, timing/OOM notes).  
2. Escalate only true blockers to engineering; eng does not invent field evidence.

## B4 — Chain stays optional (R3, R8)

L1 success = free software loop only. No mainnet $AXD. Anvil/testnet only if charter §5 names a requester.  
Lab loops: [lab/](./lab/) (not required for L1 exit).

---

## L1 exit snapshot

```text
pinned install → real IFC (and/or LiDAR) → human review → validate
  → git on private remote → arx export --format ifc
  + signed charter + classification + second-person + field-truth-log
```

**Related:** [INDEX.md](./INDEX.md) · [identity.md](./identity.md) · [ifc-limitations.md](./ifc-limitations.md)
