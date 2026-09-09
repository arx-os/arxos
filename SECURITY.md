# Security

Arxos is a **local-first, content-addressed** record of the built world. This page is the public threat model, not an audit novel.

## Threat model (one page)

| Surface | What is true |
|---|---|
| **CAS** | Objects are BLAKE3 of canonical CBOR. The store is **not confidential**. Anyone who can read the bytes can read Facts, blobs, and notes. |
| **Head authority** | Official history is whoever `Building.controller_keys` will sign. `head_root` moves on `commit`, `adopt` (self-consistency + replica continuity), or explicit `allow_untrusted`. |
| **Tickets** | An Iroh dial ticket is a **capability** to talk to that replica. It is not an account. Treat stdout / journals as secret. Default serve uses `N0DisableRelay` (no public relays). |
| **Push ≠ adopt** | `PutObject` / `PushFacts` put bytes in the CAS and append inbox meta. They never set `head_root`. |
| **Apply** | `inbox apply` is a controller commit (same fuse-on-commit path). While `net serve` holds `store.lock`, apply goes through `$STORE/meta/serve.sock` (mode `0600`, same user). The socket is **not** on Iroh. |
| **First contact** | Empty replica + `adopt` is TOFU unless `--trust-controllers` / `AdoptOptions.expected_controllers` pins keys. `arx://` `controllers=` is that pin on the client. |

Report vulnerabilities via GitHub private vulnerability reporting on this repository, or email `security@arxos.dev` (placeholder until a public contact is published).

## Still true (checklist)

Verified against current `main`. Fixed items from older reviews are **not** relisted.

- [ ] **Ticket ACL.** `GetObject` / `GetRootClosure` are scoped to advertised head closures, but anyone who can dial the ticket can fetch those closures. Keep tickets out of public logs.
- [ ] **App Attest is not on the commit path.** Capture/commit go through `BuildingRepository`. Attestation objects are diagnostic.
- [ ] **`allow_untrusted` still exists** as an explicit disaster hatch (CLI flag; iOS FFI pull with the flag hard-fails). It will set head. Do not use it as import.
- [ ] **CAS is not encrypted.** Physical access to `objects/` is full read of the record.

`AnnounceRoot` does not mutate Hello ads (ads are read from disk). IFC export is `ArxosAsBuiltView`, not CoordinationView.

## What this repo is not

No accounts, no HTTP directory, no public Iroh relays by default, no token in CIDs.
