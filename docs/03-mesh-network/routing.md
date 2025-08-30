# Mesh Routing Algorithms

## How Packets Find Their Way

### Routing Strategies

#### Flooding (Simple but Works)
```
Node A broadcasts packet
All neighbors rebroadcast once
Hop limit prevents infinite loops
Guaranteed delivery if path exists
```

#### Directed Routing (Smarter)
```
Nodes learn network topology
Packets follow best path
Falls back to flooding if needed
Reduces unnecessary transmissions
```

### Building-Aware Routing

```python
# Buildings have routing preferences
class BuildingRouter:
    def route_packet(self, packet):
        if packet.is_emergency():
            return self.broadcast_immediate()
        elif packet.is_local():
            return self.route_internal()
        elif packet.is_discovery():
            return self.flood_with_ttl(3)
        else:
            return self.route_optimal()
```

### Hop Optimization

```
Direct:     A → B           (1 hop, 100ms)
Indirect:   A → C → B       (2 hops, 200ms)
Mesh:       A → C → D → B   (3 hops, 300ms)

Maximum recommended: 7 hops (city-wide)
```

---

→ Next: [Bandwidth Optimization](bandwidth.md)