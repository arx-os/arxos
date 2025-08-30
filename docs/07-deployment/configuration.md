# Network Configuration

## Setting Up the Mesh

### Quick Config

```bash
# Basic setup
$ arxos config --building="Main" --channel=20 --sf=7

# Advanced setup
$ arxos config advanced
- Region: US915
- Bandwidth: 125 kHz
- Spreading Factor: 7 (balanced)
- Coding Rate: 4/5
- Hop Limit: 3
- Encryption: AES-128
```

### Channel Planning

```
Building A: Channel 20
Building B: Channel 21
Building C: Channel 22
Emergency: Channel 0 (all buildings)
```

### Performance Tuning

| Environment | SF | Power | Bandwidth |
|-------------|-----|-------|-----------|
| Dense urban | 7 | 10 dBm | 250 kHz |
| Suburban | 9 | 15 dBm | 125 kHz |
| Rural | 12 | 20 dBm | 125 kHz |

---

→ Next: [Troubleshooting](troubleshooting.md)