# Design: Controller Rotation (Phase 4 minimal)

## Problem

`Building.controller_keys` is set at init. Without a rotation path, adding a
second device requires re-init (losing identity) or seed sharing.

## Minimal viable path

`BuildingRepository::add_controller_key(PublicKey)`:

1. Locate the unique Building object in the active set.
2. Build a **new** Building object (new CID) with the same `building_id`,
   same name/properties, and `controller_keys` extended by the new key
   (deduped, stable order).
3. Stage the new object; stage removal of the old Building object CID.
4. Caller commits. New roots may be signed by any key in the expanded set.

Authorization remains fail-closed: only keys present on the Building object
in the **new** active set may sign the commit that introduces them — so the
**current** controller must perform the add + commit.

## Recovery story (ops, not automated)

- **Lost device, seed available from backup**: restore seed, continue.
- **Lost device, no seed, second controller already added**: remaining
  controller can continue; optionally remove the lost key later
  (`remove_controller_key` is future work).
- **Lost sole controller**: no recovery without `allow_untrusted` adopt of a
  rebuilt Building object (escape hatch for offline disaster recovery only).

## Not in this phase

- Multi-sig threshold for controller set changes
- Time-delayed rotation / social recovery
- Binding transport (Iroh) keys to author keys
