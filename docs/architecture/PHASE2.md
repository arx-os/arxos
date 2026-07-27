# Phase 2 — Multi-device & Networking

**Status:** Implemented (2026-07-27)

## Goals

* Iroh integration (QUIC P2P)
* Publish Root + objects
* Second device pulls Root and required objects by CID
* Basic spatial query (“objects near me”) — via core `annotations_near` after pull
* mDNS local discovery for site use

## Design principles

1. **Networking moves bytes; CAS remains source of truth.**  
   Peers never invent CIDs. Fetched bytes are verified by re-hashing (BLAKE3) before store.

2. **Transport is swappable.**  
   `ObjectTransport` trait → `MemoryMesh` (tests) and `IrohNode` (production).

3. **Application protocol is ours (`arxos/sync/1`).**  
   Length-prefixed CBOR messages over bi-directional QUIC streams. We keep Arxos CIDs native instead of dual-hashing through a third-party blob store.

4. **Partial by default.**  
   `GetRootClosure` returns root + members the peer holds; missing members can be requested later with `GetObject`.

5. **Follow without authoring keys.**  
   `BuildingRepository::open_or_follow` + `adopt_root` let a device track a remote head without signing.

6. **Local-first.**  
   Capture never blocks on network. Sync is explicit (`net fetch` / future auto-pull).

## Protocol sketch

```
Hello { protocol_version, peer_id, buildings[] }
GetObject { cid } → GetObjectOk | GetObjectMissing
GetRootClosure { root_cid } → RootClosure { objects: [{cid, bytes}] }
AnnounceRoot { building_id, root_cid, object_count, message? } → Ok
```

ALPN: `arxos/sync/1`

## CLI

```bash
# Device A
export ARXOS_STORE=/tmp/a
arxos building init --name Site
arxos capture simulate "$BID" --commit
arxos net serve                  # prints ticket=… ; mDNS on by default
# arxos net serve --no-mdns

# Device B
export ARXOS_STORE=/tmp/b
arxos net fetch --peer "$TICKET" --root "$ROOT" --building-id "$BID" --set-head
arxos building near "$BID" --x … --y … --z …

arxos net peers --timeout 3      # mDNS browse
arxos net publish                # list local heads
arxos net status
```

## Layout

```
networking/
  src/
    protocol.rs    # messages + framing
    transport.rs   # ObjectTransport trait
    memory.rs      # in-process mesh
    iroh_node.rs   # Iroh QUIC node
    discovery.rs   # mDNS
    sync.rs        # pull_root / serve helpers
```

## Tests

* `protocol` encode/decode
* `sync::two_device_pull_root` (MemoryMesh)
* `iroh_two_node` integration (real Iroh endpoints)
* CLI serve → fetch vertical slice (manual / CI)

## Out of scope (later)

* Continuous gossip of every object (Iroh Gossip / iroh-blobs)
* Authentication / capability tokens beyond endpoint identity
* Conflict merge of concurrent roots (Phase 3)
