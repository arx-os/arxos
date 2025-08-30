# Troubleshooting Guide

## Common Issues and Solutions

### Node Not Joining Mesh

```bash
$ arxos diagnose node:0x4A7B

Diagnostics:
✗ Radio: No signal
✓ Power: OK
✓ Firmware: v1.2.0

Solution: Check antenna connection
```

### Poor Coverage

```bash
$ arxos coverage --map

Heat map shows dead zones
Solution: Add repeater nodes at:
- Stairwells
- Elevator shafts
- Metal-heavy areas
```

### High Packet Loss

Causes:
1. Interference (change channel)
2. Too many hops (add nodes)
3. Weak signal (external antenna)
4. Congestion (increase SF)

### Quick Fixes

| Symptom | Try This |
|---------|----------|
| No communication | Check antenna |
| Intermittent | Reduce TX rate |
| Slow updates | Decrease hop limit |
| Node offline | Power cycle |

---

→ Next: [Case Studies](case-studies.md)