# ArxOS Desktop Agent

The desktop companion bridges the browser PWA and the local filesystem/Git repository. It runs on
loopback, authenticates requests with a DID:key token, and exposes a WebSocket API for high-trust
operations that cannot run inside the browser sandbox.

## Features (MVP)

- Health endpoint (`/health`)
- Capability discovery (`/capabilities`)
- WebSocket interface (`/ws`) with `ping`, `version`, and `capabilities` actions
- Authentication via DID:key token (`--token` or `ARXOS_AGENT_TOKEN`)
- Graceful shutdown on SIGINT / SIGTERM

## Running

```bash
cargo run -p arxos-agent -- --host 127.0.0.1 --port 8787 --token did:key:zexample
```

If no token is provided, the agent generates an ephemeral DID and prints it to the console. The PWA
must present the same token as a `token` query parameter when opening the WebSocket.

## TODO

- Implement Git status/commit actions
- Secure DID:key verification and rotation
- File read/write APIs with sandbox policies
- Structured logging and metrics forwarding

