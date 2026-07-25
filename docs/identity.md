# Identity model (code map + GlobalId mechanics)

> **Binding decisions:** [`adr-0001-identity-and-addressing.md`](./adr-0001-identity-and-addressing.md)  
> **Detailed design:** [`identity-and-addressing.md`](./identity-and-addressing.md)  
>
> This page is the **implementation map** for engineers. On conflict, ADR 0001 wins.

**Code:** `src/core/domain/address.rs`, `postal.rs`, `elec.rs` · `src/core/operations/address_nav.rs`, `address_mutate.rs` · `src/ifc/mapping/identity.rs` · `src/export/ifc.rs` · `src/cli/commands/{browse,add,export,init,import,migrate}.rs`  
**Field YAML name:** `address` (not yet renamed to `arx_address`)

---

## Three layers (ADR 0001)

| Layer | Storage | Role |
| :--- | :--- | :--- |
| **Operational** | `address: Option<ArxAddress>` | Primary human/CLI identity — hierarchical path |
| **Provenance** | `ifc_global_id: Option<String>` | IFC GlobalId; preserved on import; assigned on first export for native entities |
| **Internal** | `id: String` (UUID) | Merge stability / implementation only — not CLI primary |

**Never** treat STEP express ids (`#42`) as durable identity.

---

## Implemented behavior (2026-07)

### Building roots
| Source | Root form |
| :--- | :--- |
| `arx init --postal "…"` / `import ifc --postal "…"` | `bldg.<country>.<region>.<city>.<street>.<number>[.<unit>]` |
| No postal data | `bldg.lab.local.sample.<slug>` (lab default) |

Example postal derivation:

```text
143677 N. Dale Mabry Hwy, Suite 2, Tampa, FL, 33622
→ bldg.us.fl.tampa.dale-mabry.143677.s2
```

### Spatial paths
```text
ROOT/fl.<n>/rm.<slug>/…
```

### Electrical system tree (first system)
```text
ROOT/elec
ROOT/elec/panel.<id>
ROOT/elec/panel.<id>/ckt.<n>
ROOT/elec/panel.<id>/ckt.<n>/rec.<id>   # outlet
ROOT/elec/…/ltg.<id> | sw.<id> | jbox.<id>
```

Import assigns `/elec/...` only when IFC class/signal is clear; does not invent panel/circuit topology without properties.

### CLI (address-native)

```bash
arx show  <address>
arx ls    <address>
arx tree  <address> [--depth N]
arx add   <parent-address> <kind> [--name NAME]
# kinds: outlet|rec, light|ltg, switch|sw, jbox, ckt|circuit, panel

arx init  --name SITE [--postal "…"] [--country us --region fl …]
arx import ifc model.ifc [--postal "…"]
arx migrate [--postal "…"]   # backfill + optional postal re-root
arx query  "/bldg…/elec/panel.*/ckt.*"   # equipment glob (legacy helper)
arx validate [--strict-addresses]        # whole building; missing address = warn (error if strict)
arx export --format ifc --output out.ifc
```

### GlobalId rules (must not regress)

| Situation | Behavior |
| :--- | :--- |
| Import product with GlobalId | Store in `ifc_global_id`; never use as operational address |
| `arx add` (Arxos-native) | **No** GlobalId at creation |
| First `arx export` | Assign missing GlobalIds (deterministic from entity UUID when possible); **write back** to `building.yaml` |
| Re-export | Preserve existing GlobalIds (no churn) |
| Export product type | `rec.*`→`IFCOUTLET`, `ltg.*`→`IFCLIGHTFIXTURE`, `sw.*`→`IFCSWITCHINGDEVICE`, `panel.*`→`IFCELECTRICDISTRIBUTIONBOARD` |

```text
FIELD / CLI
  address  = operational identity (humans, show/ls/tree/add)
  id       = internal UUID (invisible in browse output)

IMPORT
  IFC GlobalId → ifc_global_id
  Pset_ArxIdentity:ArxId → restore internal id when present

EXPORT
  ifc_global_id present → re-emit same GlobalId
  ifc_global_id absent  → mint from UUID, persist, emit as new IFC product
```

### Validation
- Syntax: lowercase segments; alnum, `-`, `_`, `.` allowed; leading `/` optional on parse
- Missing `address` on Building/Floor/Room/Equipment → **warning** (error under `--strict-addresses`)
- Reserved-system prefix mismatches → warning by default, error if strict

### Not yet implemented
- Other system trees (`hvac`, `plumb`, `fire`, `vert`, …)
- `arx link` / relationship graph
- Scoped `arx validate <address>`
- YAML field rename `address` → `arx_address`
- Full IFC electrical topology extraction from `IfcRel*` networks

---

## Tests that guard this

| Area | What |
| :--- | :--- |
| `src/core/domain/{address,postal,elec}.rs` | Parser, postal root, elec segments |
| `src/core/operations/{address_nav,address_mutate}.rs` | show/ls/tree/add |
| `src/ifc/mapping/identity.rs` | GlobalId assign/preserve |
| `tests/postal_root_test.rs` | Postal import root |
| `tests/address_add_test.rs` | Add + persist |
| `tests/export_identity_test.rs` | Native assign + imported preserve |
| `tests/bidirectional_tests.rs` | Compiler identity round-trip |

---

## Related

- [ADR 0001](./adr-0001-identity-and-addressing.md) — binding decisions  
- [identity-and-addressing.md](./identity-and-addressing.md) — full hierarchy design  
- [ifc-limitations.md](./ifc-limitations.md) — IFC fidelity contract  
- [l1-supported-workflow.md](./l1-supported-workflow.md) — pilot loop  
