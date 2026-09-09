# Controller removal (Phase: dual-control basics)

## Policy (fail-closed)

- `remove_controller_key(pk)` stages a new Building object with `pk` removed.
- **Cannot remove the last remaining controller** — returns `Authorization`.
- **Unknown key** — returns `Validation`.
- The **current** device key (seed) must still be a remaining controller to
  commit the removal (same as any other root).

## Recovery implications

| Scenario | Outcome |
|----------|---------|
| Second controller removed intentionally | Remaining controller continues |
| Sole controller lost (seed gone) | No in-protocol recovery; offline `allow_untrusted` rebuild only |
| Removed key tries to commit | Authorization failure on commit |

## CLI

```text
arx building remove-controller <building_id> <pubkey>
arx building controllers <building_id>
```
