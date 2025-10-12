# Simple Guide: What Are Database Columns & Migrations?

**For:** Joel (non-database expert)
**Created:** October 12, 2025

---

## 🏢 Think of a Database Like a Filing Cabinet

### Your Filing Cabinet (Database):
```
┌─────────────────────────────────┐
│  Equipment Files (Table)        │
│  ─────────────────────────      │
│  Each drawer = One piece of     │
│  equipment (like a row)         │
│                                 │
│  Each folder section = Type of  │
│  info you track (like columns)  │
└─────────────────────────────────┘
```

**Columns** = The dividers in your filing system (Name, Type, Location, Status)
**Rows** = Individual files (VAV Box 301, Panel 1A, Outlet 12)

---

## 📋 What We Currently Have

### Equipment Filing System (Current):
```
Equipment File for "VAV Box 301":
┌────────────────────────────────┐
│ ID:       eq-12345             │ ← Column: ID
│ Name:     VAV Box 301          │ ← Column: Name
│ Type:     HVAC                 │ ← Column: Type
│ Building: Building 1           │ ← Column: Building
│ Status:   Active               │ ← Column: Status
│                                │
│ [Missing: Address/Path]        │ ← We need to ADD this!
└────────────────────────────────┘
```

---

## 🔧 What We Need to Add

### Equipment File After Migration:
```
Equipment File for "VAV Box 301":
┌────────────────────────────────┐
│ ID:       eq-12345             │
│ Name:     VAV Box 301          │
│ Type:     HVAC                 │
│ Building: Building 1           │
│ Status:   Active               │
│ Path:     /B1/3/301/HVAC/VAV-301│ ← NEW! This is what we're adding
└────────────────────────────────┘
```

**The "Path" is like adding a street address to each equipment file!**

---

## 🔨 What Is a Migration?

A **migration** is like a work order that says:

> "Add a new section to all equipment files called 'Path' where we can write the address."

### Real-World Analogy:

**Electrical Panel Comparison:**
```
BEFORE:  Panel has 20 circuits
         ↓
WORK ORDER: "Add 4 new breaker spaces"
         ↓
AFTER:   Panel now has 24 circuits
```

**Database Comparison:**
```
BEFORE:  Equipment table has 5 columns
         ↓
MIGRATION: "Add path column"
         ↓
AFTER:   Equipment table has 6 columns
```

---

## 📁 Files I Created For You

### 1. The Migration Files (The Work Orders)
```
internal/migrations/
├── 023_add_equipment_paths.up.sql    ← Adds the column
└── 023_add_equipment_paths.down.sql  ← Removes it (if needed)
```

### 2. The Instructions
```
MIGRATION_INSTRUCTIONS.md              ← Quick start (read this first!)
docs/DATABASE_MIGRATIONS_GUIDE.md     ← Detailed guide (12KB of info)
```

---

## 🚀 How to Run It (Simple Steps)

### Step 1: Open Terminal
```bash
cd /Users/joelpate/repos/arxos
```

### Step 2: Make Sure Database is Running
```bash
pg_isready
```
Should say "accepting connections"

### Step 3: Run the Migration
```bash
arx migrate up
```

That's it! The column is added.

### Step 4: Verify It Worked
```bash
psql -U your_username -d arxos_db -c "\d equipment"
```

Look for a line that says:
```
path | text |
```

**If you see that → Success! ✅**

---

## 🎯 What Happens During Migration

### Visual Flow:

**BEFORE MIGRATION:**
```
equipment table:
┌─────┬─────────┬──────┬──────────┬────────┐
│ ID  │  Name   │ Type │ Building │ Status │
├─────┼─────────┼──────┼──────────┼────────┤
│ 001 │ VAV Box │ HVAC │ B1       │ Active │
└─────┴─────────┴──────┴──────────┴────────┘
         5 columns total
```

↓ **RUN MIGRATION** ↓

**AFTER MIGRATION:**
```
equipment table:
┌─────┬─────────┬──────┬──────────┬────────┬──────────┐
│ ID  │  Name   │ Type │ Building │ Status │   Path   │ ← NEW!
├─────┼─────────┼──────┼──────────┼────────┼──────────┤
│ 001 │ VAV Box │ HVAC │ B1       │ Active │   NULL   │
└─────┴─────────┴──────┴──────────┴────────┴──────────┘
         6 columns total
```

**NULL means empty (for now). New equipment will get paths automatically!**

---

## 🧪 Testing After Migration

### Import Some Equipment:
```bash
# Import a building
arx import test_data/inputs/sample_building.ifc
```

### Check If Paths Were Generated:
```bash
psql -U your_username -d arxos_db -c \
"SELECT name, path FROM equipment WHERE path IS NOT NULL LIMIT 5;"
```

### You Should See:
```
       name       |          path
------------------+------------------------
 VAV Box 301      | /B1/3/301/HVAC/VAV-301
 Thermostat 301   | /B1/3/301/HVAC/STAT-01
 Outlet A         | /B1/2/205/ELEC/OUTLET-A
 Core Switch 1    | /B1/1/MDF/NETWORK/CORE-SW-1
 Fire Panel       | /B1/1/SAFETY/FIRE-PANEL-1
```

**If you see paths like these → Everything works! 🎉**

---

## ❓ Common Questions

### Q: Will this break existing equipment?
**A:** No! Existing equipment will have NULL (empty) paths. Only new imports will get paths. Everything still works.

### Q: What if I run the migration twice?
**A:** It's safe! The migration has `IF NOT EXISTS` which means it skips if the column already exists.

### Q: Can I undo it?
**A:** Yes! Run `arx migrate down` to remove the column. (But you probably won't need to.)

### Q: Do I need to update my code?
**A:** Nope! I already updated the code. It will automatically generate paths when you import equipment.

### Q: What if it fails?
**A:** Read the error message. Most common issues:
- Database not running → Start PostgreSQL
- Wrong username → Check your database config
- Already exists → That's fine! Column was already added

---

## 📊 Summary

### What We Had:
- Equipment in database with NO universal address
- Can't query by location consistently
- No standard way to reference equipment

### What We're Adding:
- New `path` column in equipment table
- New `path` column in bas_points table
- Indexes to make searches fast

### What You Get:
- Every equipment has unique address like `/B1/3/301/HVAC/VAV-301`
- Can search by path patterns like `/B1/3/*/HVAC/*`
- Work orders can reference exact equipment
- No more "that thermostat in room 301"

---

## 🎓 Key Concepts

| Concept | What It Is | Like... |
|---------|------------|---------|
| **Column** | Type of data to store | Folder divider in filing cabinet |
| **Row** | One record | One file in the cabinet |
| **Table** | Collection of data | The whole filing drawer |
| **Migration** | Change to structure | Work order to modify the cabinet |
| **Index** | Fast lookup | Index in back of a book |
| **NULL** | Empty/no value | Blank space on a form |

---

## 📚 Where to Learn More

1. **Quick Start:** Read `MIGRATION_INSTRUCTIONS.md` (2 pages)
2. **Detailed Guide:** Read `docs/DATABASE_MIGRATIONS_GUIDE.md` (12KB)
3. **Try It:** Run the migration and test it!

---

## ✅ Checklist

- [ ] Understand what columns are (sections in filing system)
- [ ] Understand what migrations are (work orders for database)
- [ ] Run `arx migrate up` to add the columns
- [ ] Verify with `\d equipment` in psql
- [ ] Import test data to see paths generated
- [ ] Celebrate! You just modified a database! 🎉

---

**Bottom Line:** You're adding a "street address" field to your equipment records. The migration is the instruction that tells the database to add that field. Once you run it, every piece of equipment can have a path like `/B1/3/301/HVAC/VAV-301`!

**It's that simple!** 😊

