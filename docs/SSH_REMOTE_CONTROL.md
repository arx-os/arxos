# SSH Remote Control Layer

ArxOS includes a secure, SSH-based remote control layer that allows administrators and authorized users to manage building systems remotely using standard SSH clients or the `arx remote` CLI tool.

## Overview

The Agent runs an embedded SSH server (default port 2222) that provides:
1.  **Secure Authentication**: Standard SSH public key authentication (ED25519/RSA).
2.  **Role-Based Access Control (RBAC)**: Fine-grained permissions defined in `.arxos/permissions.yaml`.
3.  **Command Execution**: Execute `get`, `set`, and other agent commands remotely.
4.  **Hardware Abstraction**: Unified interface for BACnet, Modbus, and MQTT devices.

## Setup

### 1. Server Configuration
The SSH server is enabled by default when running the agent.
Configuration is loaded from generic agent config or defaults:
- **Port**: 2222
- **Host Key**: `.arxos/ssh_host_key`
- **Authorized Keys**: `.arxos/authorized_keys`

### 2. User Access
To grant access to a user:
1.  Obtain their public SSH key (e.g., `id_ed25519.pub`).
2.  Append it to the `.arxos/authorized_keys` file on the agent machine.
    ```text
    ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... user@laptop
    ```
3.  Assign permissions in `.arxos/permissions.yaml`.

### 3. Client Configuration
Use the `arx` CLI to manage connections.

```bash
# Add a building
arx remote add --name hq --host 192.168.1.50 --user admin

# List buildings
arx remote list

# Execute command
arx remote exec hq "get temp --room 'Server Room'"

# Interactive Shell
arx remote connect hq
```

You can also use standard SSH clients:
```bash
ssh -p 2222 admin@192.168.1.50 "list sensors"
```

## RBAC & Permissions

Permissions are defined in `.arxos/permissions.yaml`.

### Roles
- `admin`: Full access to all commands.
- `operator`: Can read/write sensors but cannot change system config.
- `viewer`: Read-only access to sensors.

### Example Configuration
```yaml
roles:
  viewer:
    - "sensor:read"
  operator:
    - "sensor:read"
    - "sensor:write"
  admin:
    - "*"

users:
  - name: "alice"
    role: "admin"
    keys: 
      - "SHA256:..."
  - name: "bob"
    role: "viewer"
```

## Architecture

The SSH layer sits on top of the **Agent Dispatcher**.

```text
[ Remote Client ] --(SSH)--> [ SSH Server (russh) ]
                                     |
                             [ Authenticator ]
                                     |
                                     v
                             [ Command Dispatcher ]
                                     |
                        +------------+------------+
                        |            |            |
                    [ Sensors ]  [ Hardware ]  [ IFC ]
```
