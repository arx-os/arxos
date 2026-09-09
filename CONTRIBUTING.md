# Contributing

## Test

```bash
cargo test --workspace
cargo clippy -p arxos-core -- -D warnings
```

Store contract: [core/README.md](core/README.md). Threat model: [SECURITY.md](SECURITY.md).

## Module size

New production `*.rs` files should stay around 400–600 source lines unless they are:

- a single serde schema (`core/src/object/mod.rs` — **exception: one canonical schema**)
- generated bindings (UniFFI `Generated/` is gitignored)
- a table-driven test file of cases

If a file must exceed **800** production lines, add it to the exception list below with a reason.

### Exceptions (>800 production LOC)

| File | Reason |
|---|---|
| `core/src/object/mod.rs` | Single canonical CBOR schema (`Object` / `ObjectBody` / `Pose`). Splitting bodies is optional; field names must not change. |

## Do not commit

- `REVIEW.md` or other machine-local audits
- Graphify output (`graphify-out/`)
- `/docs/_scratch/` or `*.local.md` under `docs/`
- Generated iOS UniFFI (`ios/Arxos/Sources/ArxosCore/Generated/`) or `libarxos_core.a`
