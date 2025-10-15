# Universal Naming Convention - Quick Start Guide

**5-Minute Guide for Busy Technicians**

---

## The Basics

Every piece of equipment gets an address like this:

```
/B1/3/301/HVAC/VAV-301
 │   │  │   │     │
 │   │  │   │     └─ Equipment name
 │   │  │   └─────── System (HVAC, ELEC, NETWORK, etc.)
 │   │  └─────────── Room number
 │   └────────────── Floor number
 └────────────────── Building code
```

**That's it.** Now you can find any equipment instantly.

---

## The 5 Essential Commands

### 1. Find Specific Equipment
```bash
arx get /B1/3/301/HVAC/VAV-301
```
Returns: Details about VAV-301 in Room 301

### 2. Find Multiple Items (Wildcards)
```bash
arx get /B1/3/*/HVAC/*
```
Returns: All HVAC equipment on floor 3

### 3. Check Status
```bash
arx status /B1/3/301/HVAC/VAV-301
```
Returns: Current status and recent alerts

### 4. Trace Connections
```bash
arx trace /B1/2/205/ELEC/OUTLET-1 --upstream
```
Returns: Which panel feeds this outlet

### 5. List by System
```bash
arx list /B1/*/HVAC/*
```
Returns: All HVAC equipment in building

---

## Real-World Examples

### "AC not working in Room 301"
```bash
# Check thermostat
arx status /B1/3/301/HVAC/STAT-01

# Check VAV box
arx status /B1/3/301/HVAC/VAV-301

# Find air handler
arx trace /B1/3/301/HVAC/VAV-301 --upstream
```

### "No network in Room 205"
```bash
# Check wall jack
arx status /B1/2/205/NETWORK/JACK-A

# Find the switch
arx trace /B1/2/205/NETWORK/JACK-A --upstream

# Check wireless as backup
arx get /B1/2/*/NETWORK/WAP-*
```

### "Monthly fire extinguisher check"
```bash
# List all fire extinguishers
arx get /*/*/SAFETY/EXTING-*

# Just floor 2
arx get /B1/2/*/SAFETY/EXTING-*
```

---

## System Codes Cheat Sheet

| Code | System | Examples |
|------|--------|----------|
| `ELEC` | Electrical | Panels, outlets, lights |
| `HVAC` | Heating/Cooling | VAVs, thermostats, air handlers |
| `NETWORK` | IT/Network | Switches, WAPs, network jacks |
| `PLUMB` | Plumbing | Sinks, toilets, water heaters |
| `SAFETY` | Fire/Safety | Fire panels, detectors, sprinklers |
| `BAS` | Building Automation | Control points, sensors |
| `AV` | Audio/Visual | Projectors, displays |

---

## Common Patterns

### All equipment in a room:
```bash
arx get /B1/3/301/*/*
```

### All panels in the building:
```bash
arx get /*/*/ELEC-RM/ELEC/PANEL-*
```

### All WAPs on floor 2:
```bash
arx get /B1/2/*/NETWORK/WAP-*
```

### All smoke detectors:
```bash
arx get /*/*/SAFETY/DETECTOR-*
```

---

## Quick Troubleshooting

**Path doesn't work?**
- Must start with `/`
- Must be UPPERCASE
- No spaces

**Can't find equipment?**
```bash
# Search by name instead
arx search "VAV 301"

# Or list everything in the room
arx get /B1/3/301/*/*
```

**Too many results?**
- Add more specifics to your path
- Use `--status` filters
- Narrow down to specific system

---

## Tips for Work Orders

**Instead of:**
> "Outlet not working in conference room on 3rd floor"

**Write:**
> `Check /B1/3/CONF-301/ELEC/OUTLET-2 - no power`

Now the next tech knows EXACTLY which outlet without searching.

---

## Next Steps

**Read the full guide:** `docs/USER_GUIDE_NAMING_CONVENTION.md`

**Try it yourself:**
```bash
# See all equipment in your area
arx get /B1/[YOUR-FLOOR]/*/*

# Find something specific
arx search "conference"
```

**Questions?**
```bash
arx help
arx examples
```

---

**Remember:** Every equipment address follows the same pattern. Once you know one, you know them all.

