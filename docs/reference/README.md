# Reference (engineers)

Stable design and **implementation maps**. On conflict with an accepted ADR, the ADR wins.

| Doc | Topic |
| :--- | :--- |
| [identity.md](identity.md) | **Code map** — roots, `/elec`, `show`/`ls`/`tree`/`add`, GlobalId export |
| [identity-and-addressing.md](identity-and-addressing.md) | Full address-tree design + CLI language |
| [ifc-limitations.md](ifc-limitations.md) | IFC-only policy, fidelity L0–L2, LossReport honesty |
| [lidar-confidence.md](lidar-confidence.md) | Non-probabilistic confidence honesty |
| [resource-limits.md](resource-limits.md) | R6 pilot import ceilings |
| [field-language.md](field-language.md) | Shared CLI / agent / iOS vocabulary |
| [agent-client-interface.md](agent-client-interface.md) | Versioned agent JSON-RPC for peripheral clients |
| [native-file-handoff.md](native-file-handoff.md) | Scan file → CLI or agent `lidar.import` |
| [ios-lab-loop.md](ios-lab-loop.md) | Companion ↔ agent ↔ commit ↔ IFC lab status |

**Binding identity decisions:** [`../adr/0001-identity-and-addressing.md`](../adr/0001-identity-and-addressing.md)
