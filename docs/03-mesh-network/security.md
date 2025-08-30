# Mesh Network Security

## Air-Gapped by Design

### Security Layers

#### Physical Layer
- Limited radio range (1-10 km)
- Physical proximity required
- No internet = no remote attacks

#### Encryption Layer
- AES-128/256 standard
- Per-channel PSK
- Rolling codes for commands

#### Application Layer
- Node whitelisting
- Player authentication
- BILT token verification

### Threat Model

| Attack | Protection |
|--------|------------|
| Eavesdropping | AES encryption |
| Replay | Rolling codes |
| Jamming | Channel hopping |
| Spoofing | Node authentication |
| Remote hack | Air-gapped |

### Best Practices

1. **Unique channel keys** per building
2. **Rotate keys** quarterly
3. **Monitor signal** for anomalies
4. **Physical security** for nodes
5. **Audit logs** for all changes

---

→ Next: [Hardware Documentation](../04-hardware/)