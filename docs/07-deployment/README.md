# Real-World Deployment Guide

## From Prototype to Production Building

### Deployment Phases

```
Phase 1: Pilot (1 room)
  ↓ Learn & iterate
Phase 2: Floor (20 rooms)
  ↓ Prove value
Phase 3: Building (100+ rooms)
  ↓ Full deployment
Phase 4: Campus (Multiple buildings)
  ↓ Mesh network
Phase 5: City (Community mesh)
```

### Pre-Deployment Checklist

```bash
☐ Building survey completed
☐ Electrical panels mapped
☐ Network coverage tested
☐ Stakeholders trained
☐ Safety protocols established
☐ BILT rewards configured
```

### Installation Workflow

#### 1. Site Survey
```bash
$ arxos survey --building="Alafia Elementary"

Scanning building...
- Floors: 3
- Rooms: 47
- Electrical panels: 3
- Approximate nodes needed: 75
- Estimated BILT rewards: 5,000
```

#### 2. Node Placement
```
Priority locations:
1. Electrical panels (100 BILT each)
2. Server/network rooms (75 BILT)
3. HVAC equipment (50 BILT)
4. Main corridors (25 BILT)
5. Individual rooms (10 BILT)
```

#### 3. Physical Installation
```
Per node: 10 minutes
- Mount: 3 minutes
- Wire: 4 minutes
- Power: 2 minutes
- Test: 1 minute
```

### Team Roles (RPG Classes)

#### Electrical Team (Electrician Class)
- Install outlet nodes
- Wire power connections
- Map circuits
- Verify safety

#### Network Team (IT Class)
- Deploy mesh nodes
- Configure channels
- Test coverage
- Monitor traffic

#### Facilities Team (Admin Class)
- Coordinate access
- Update documentation
- Train staff
- Manage BILT

### Progressive Deployment

```yaml
Week 1: Core Infrastructure
- Install gateway node
- Deploy panel monitors
- Establish mesh backbone
- Reward: 500 BILT

Week 2: Common Areas
- Hallway sensors
- Conference rooms
- Break areas
- Reward: 300 BILT

Week 3: Individual Spaces
- Offices
- Classrooms
- Storage
- Reward: 200 BILT

Week 4: Optimization
- Fill coverage gaps
- Tune parameters
- Document everything
- Reward: 100 BILT bonus
```

### Deployment Tools

```bash
# Arxos deployment toolkit
$ arxos deploy --help

Commands:
  survey    - Analyze building
  plan      - Generate deployment plan
  test      - Verify mesh coverage
  monitor   - Track installation progress
  validate  - Confirm proper operation
```

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Coverage | 95% | Signal strength map |
| Latency | <500ms | Packet round trip |
| Reliability | 99% | Delivery success rate |
| Redundancy | 2+ paths | Mesh topology |

### Common Challenges

#### Challenge: Dead Zones
```
Solution: Add repeater nodes
Cost: $25 per node
BILT Reward: 50 tokens
```

#### Challenge: Interference
```
Solution: Change channel/SF
Cost: Configuration time
BILT Reward: 25 tokens
```

#### Challenge: Power Access
```
Solution: Battery nodes
Cost: $10 per battery
BILT Reward: 30 tokens
```

### Deployment Configurations

#### Small Office (< 10,000 sq ft)
```yaml
Nodes: 10-20
Gateway: 1
Investment: $500
Install time: 1 day
BILT potential: 1,000
```

#### School Building (50,000 sq ft)
```yaml
Nodes: 50-75
Gateways: 2-3
Investment: $2,500
Install time: 1 week
BILT potential: 5,000
```

#### Office Complex (200,000 sq ft)
```yaml
Nodes: 200-300
Gateways: 5-10
Investment: $10,000
Install time: 2 weeks
BILT potential: 20,000
```

### Post-Deployment

#### Verification
```bash
$ arxos verify --building="Alafia Elementary"

Verification Report:
✓ 75 nodes online
✓ 95% coverage achieved
✓ All critical systems mapped
✓ 3 players active
✓ 847 BILT earned today
```

#### Training
- Terminal basics (1 hour)
- Navigation (30 minutes)
- Troubleshooting (30 minutes)
- BILT rewards (15 minutes)

#### Maintenance
- Weekly: Check node status
- Monthly: Review coverage
- Quarterly: Update firmware
- Yearly: Hardware inspection

### Success Metrics

```
Day 1: System online
Week 1: 90% coverage
Month 1: Full deployment
Month 3: ROI positive
Year 1: 30% energy savings
```

### Next Steps

- [Installation Guide](installation.md) - Physical setup
- [Configuration](configuration.md) - Network settings
- [Troubleshooting](troubleshooting.md) - Common issues
- [Case Studies](case-studies.md) - Real deployments

---

*"Every building deployed is a victory for open infrastructure"*