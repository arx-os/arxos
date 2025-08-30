# Bandwidth Optimization

## Making 1 kbps Feel Like Broadband

### The Constraint

LoRa gives us 0.3-5.4 kbps. We make it work through:
- 13-byte packets (30x smaller than JSON)
- Aggressive caching (95% hit rate)
- Delta updates (only changes)
- Progressive disclosure (overview first)

### Optimization Techniques

#### Multi-Level Cache
```python
cache_hierarchy = {
    "L1": "Current room (100ms)",
    "L2": "Current floor (500ms)",
    "L3": "Building (1s)",
    "L4": "Mesh network (2-5s)"
}
```

#### Delta Compression
```c
// Full update: 13 bytes
{0x0F17, 0x10, 0x1472, 0x0866, 0x04B0, {15, 20, 1, 75}}

// Delta update: 5 bytes (only load changed)
{0x84, 0x0F17, 0x03, 80}  // Delta cmd, ID, property 3, new value
```

#### Batch Operations
```c
// Send multiple updates as one transmission
{0x82}  // Batch start
{...}   // Object 1
{...}   // Object 2
{...}   // Object 3
{0x83}  // Batch end
```

### Real-World Performance

| Operation | Size | Time @ 1kbps |
|-----------|------|--------------|
| Single object | 13 bytes | 104 ms |
| Floor query | 130 bytes | 1.04 s |
| Building sync | 1.3 KB | 10.4 s |
| Full campus | 13 KB | 104 s |

---

→ Next: [Security](security.md)