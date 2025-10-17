# IFC Import Guide

**Last Updated:** October 17, 2025  
**For Users:** Architects, BIM Managers, Facility Managers  
**Skill Level:** Beginner to Intermediate

---

## Table of Contents

- [What is IFC?](#what-is-ifc)
- [Quick Start](#quick-start)
- [Supported IFC Versions](#supported-versions)
- [Preparing IFC Files](#preparing-files)
- [Importing to ArxOS](#importing)
- [What Gets Extracted](#what-gets-extracted)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## What is IFC? {#what-is-ifc}

**IFC (Industry Foundation Classes)** is an open standard file format for Building Information Modeling (BIM) data. Think of it as a universal language that lets different CAD/BIM software communicate.

**Common Uses:**
- Architectural models from Revit, ArchiCAD, Vectorworks
- Structural models from Tekla, RISA
- MEP (Mechanical, Electrical, Plumbing) systems
- Facility management data

**In ArxOS:**
- IFC files are the primary way to bulk-import building data
- One IFC import can create an entire building with floors, rooms, and equipment
- Alternative to manual data entry or CSV imports

---

## Quick Start {#quick-start}

### 5-Minute Import

```bash
# 1. Get an IFC file (from your architect or BIM manager)
# Example: building.ifc

# 2. Import to ArxOS
arx import building.ifc

# 3. Verify import
arx building list

# 4. Explore the data
arx get /MAIN/1/101/HVAC/*
```

**That's it!** ArxOS automatically extracts:
- Buildings
- Floors
- Rooms
- Equipment (HVAC, electrical, plumbing, etc.)
- Spatial hierarchy

---

## Supported IFC Versions {#supported-versions}

### Fully Supported ✅

- **IFC4** (Recommended)
  - Latest standard
  - Best support for MEP systems
  - Enhanced spatial features

- **IFC2x3** (Legacy)
  - Widely used
  - Good compatibility
  - May have limited MEP details

### Partially Supported ⚠️

- **IFC4x1, IFC4x2, IFC4x3** (Preview versions)
  - Import works
  - Some advanced features may not extract

### Not Supported ❌

- **IFC1.0, IFC2.0** (Very old)
  - Too limited for modern use
  - Consider updating IFC file

**How to Check Your IFC Version:**
- Open IFC file in text editor
- Look for `FILE_SCHEMA(('IFC4'))` in the header
- Or check in your CAD software's export settings

---

## Preparing IFC Files {#preparing-files}

### Export Settings in CAD Software

#### Autodesk Revit

1. **File → Export → IFC**
2. **Setup:**
   - IFC Version: IFC4
   - File Type: IFC4 Design Transfer View
   - Space Boundaries: 1st Level
   - Export Base Quantities: ✅ Enabled
   - Split Walls and Columns by Level: ✅ Enabled
3. **Property Sets:**
   - Include property sets: ✅ Enabled
   - Include IFC common property sets: ✅ Enabled
4. **Export**

#### Graphisoft ArchiCAD

1. **File → Save As → IFC 4.0**
2. **Translator Settings:**
   - Use IFC4 Reference View or Design Transfer View
   - Include property definitions
   - Export zones as spaces
3. **Geometry:**
   - Export model with full geometry
   - Include structural elements
4. **Export**

#### Vectorworks

1. **File → Export → Export IFC**
2. **Settings:**
   - IFC Version: IFC4
   - Data mapping: Full
   - Include properties
3. **Export**

### What to Include in Your IFC Export

**Essential (Required for Good Results):**
- ✅ Buildings (IfcBuilding)
- ✅ Floors/Stories (IfcBuildingStorey)
- ✅ Spaces/Rooms (IfcSpace)
- ✅ Spatial hierarchy (Building → Floor → Space)

**Important (Highly Recommended):**
- ✅ Equipment (IfcFlowTerminal, IfcDistributionElement)
- ✅ HVAC components (AHUs, VAVs, ducts, etc.)
- ✅ Electrical components (panels, fixtures, etc.)
- ✅ Property sets (Psets) with equipment specifications
- ✅ 3D coordinates (placement data)

**Optional (Nice to Have):**
- Walls, doors, windows (for spatial context)
- Structural elements (beams, columns)
- Site information (IfcSite)
- Classifications (Uniclass, OmniClass)

### File Size Considerations

**Limits:**
- Maximum file size: 200MB (configurable)
- Typical files: 1-50MB

**If Your File is Too Large:**
1. Split by building (export each building separately)
2. Simplify geometry (use simplified representations)
3. Remove unnecessary detail elements
4. Export by floor/zone

---

## Importing to ArxOS {#importing}

### Command Line Import

```bash
# Basic import
arx import /path/to/building.ifc

# Import with options
arx import building.ifc --building-name "Main Campus" --validate

# Import and create version commit
arx import building.ifc --commit --message "Initial building import from IFC"

# Verbose output
arx import building.ifc --verbose
```

### What Happens During Import

1. **Upload**: IFC file sent to IfcOpenShell service
2. **Parse**: Service extracts entities (buildings, floors, rooms, equipment)
3. **Validate**: Checks for buildingSMART compliance
4. **Create**: ArxOS creates database records
5. **Link**: Establishes parent-child relationships
6. **Generate Paths**: Creates universal naming paths (e.g., `/MAIN/1/101/HVAC/VAV-101`)
7. **Commit**: Optionally creates version control commit

**Typical Import Time:**
- Small building (< 1MB): 5-15 seconds
- Medium building (1-10MB): 15-60 seconds
- Large building (10-50MB): 1-5 minutes

---

## What Gets Extracted {#what-gets-extracted}

### Buildings

**From IFC:**
- IfcBuilding → ArxOS Building

**Extracted Data:**
- Building name
- Address (if provided in IfcBuilding.BuildingAddress)
- Elevation
- Description

**Example:**
```
IFC: IfcBuilding("Main Campus HQ")
  → ArxOS: Building{Name: "Main Campus HQ", Address: "123 Main St, San Francisco, CA"}
```

### Floors

**From IFC:**
- IfcBuildingStorey → ArxOS Floor

**Extracted Data:**
- Floor name (e.g., "Level 1")
- Floor level (inferred from elevation or name)
- Elevation in meters
- Floor height

**Example:**
```
IFC: IfcBuildingStorey("Level 1", Elevation: 0.0)
  → ArxOS: Floor{Name: "Level 1", Level: 1, Elevation: 0.0}
```

### Rooms/Spaces

**From IFC:**
- IfcSpace → ArxOS Room

**Extracted Data:**
- Room name/number
- Parent floor reference
- 3D coordinates (center point)
- Room description

**Example:**
```
IFC: IfcSpace("101", LongName: "Conference Room A")
  → ArxOS: Room{Name: "101", Number: "101", Location: {X: 10.5, Y: 5.2, Z: 0.0}}
```

### Equipment

**From IFC:**
- IfcFlowTerminal, IfcAirTerminalBox, IfcElectricDistributionBoard, etc. → ArxOS Equipment

**Extracted Data:**
- Equipment name
- IFC object type
- Category (hvac, electrical, plumbing, etc.)
- Parent room reference
- 3D coordinates
- Property sets (manufacturer, model, specifications)
- Equipment tag

**Example:**
```
IFC: IfcAirTerminalBox("VAV-101", Tag: "VAV-101")
  Pset: {NominalAirFlowRate: 500, NominalPower: 1200}
  → ArxOS: Equipment{
       Name: "VAV-101",
       Type: "IfcAirTerminalBox",
       Category: "hvac",
       Path: "/MAIN/1/101/HVAC/VAV-101",
       Metadata: {"Pset_AirTerminalBoxTypeCommon.NominalAirFlowRate": 500}
     }
```

### Equipment Category Mapping

ArxOS automatically categorizes IFC equipment:

| IFC Types | ArxOS Category | Examples |
|-----------|---------------|----------|
| IfcElectricDistributionBoard, IfcElectricGenerator | `electrical` | Electrical panels, generators |
| IfcAirTerminal, IfcBoiler, IfcChiller, IfcFan | `hvac` | HVAC equipment |
| IfcSanitaryTerminal, IfcWasteTerminal | `plumbing` | Sinks, toilets |
| IfcFireSuppressionTerminal, IfcAlarm | `safety` | Fire suppression, alarms |
| IfcLightFixture | `lighting` | Light fixtures |
| IfcCommunicationsAppliance | `network` | Network/AV equipment |

---

## Troubleshooting {#troubleshooting}

### Import Fails Completely

**Error: "File size exceeds maximum"**
- File is > 200MB
- **Solution**: Split file by building or floor, or simplify geometry

**Error: "Invalid IFC format"**
- File may be corrupted or not actually IFC
- **Solution**: Re-export from CAD software, ensure .ifc extension

**Error: "No IFC data provided"**
- File path incorrect or empty file
- **Solution**: Verify file exists and has content

### Import Succeeds But No Data Created

**Building count shows 0 after import**
- IFC file missing IfcBuilding entity
- **Solution**: Ensure CAD export includes building structure

**Rooms not created**
- IFC file missing IfcSpace entities
- **Solution**: In CAD software, export spaces/zones

**Equipment not extracted**
- IFC file missing MEP equipment
- **Solution**: Export with MEP systems included

### Partial Import (Some Data Missing)

**Floors created but rooms missing**
- Check if IFC has IfcSpace entities
- Some CAD software doesn't export spaces by default

**Equipment missing parent room**
- IFC may not have proper spatial containment relationships
- Equipment will still be created but at floor/building level

**Property sets empty**
- CAD export may not include Psets
- Re-export with "Include property sets" enabled

### Performance Issues

**Import taking very long**
- Large file (>50MB) or complex geometry
- **Solution**: Be patient, or split into smaller files

**Service unavailable**
- IfcOpenShell service not running
- **Check**: `docker ps | grep ifcopenshell`
- **Solution**: Start service with `docker-compose up ifcopenshell-service`

---

## Best Practices {#best-practices}

### Before Export

1. **Clean your model**
   - Remove unused elements
   - Fix modeling errors
   - Validate in your CAD software

2. **Organize spatially**
   - Ensure proper Building → Floor → Space hierarchy
   - Place equipment in correct rooms
   - Verify spatial containment

3. **Add property data**
   - Fill in equipment specifications
   - Add manufacturer/model information
   - Include maintenance data if available

### During Export

1. **Choose IFC4** for best results
2. **Enable property sets** in export settings
3. **Include spaces** (rooms) in export
4. **Export 3D geometry** not just 2D
5. **Use Design Transfer View** for comprehensive data

### After Import

1. **Verify import results**
   ```bash
   arx building list
   arx query /MAIN/1/*/HVAC/* --count
   ```

2. **Check data quality**
   - Spot-check room names
   - Verify equipment categorization
   - Review universal naming paths

3. **Create version commit**
   ```bash
   arx commit -m "Imported Main Building from IFC"
   ```

4. **Supplement as needed**
   - Add missing equipment manually
   - Map BAS points to equipment
   - Add photos/documentation

---

## FAQ {#faq}

**Q: Do I need an IFC file to use ArxOS?**  
A: No. IFC is one import method. You can also add buildings manually or import from CSV.

**Q: Will importing IFC replace my CAD software?**  
A: No. ArxOS is for facility management, not design. Keep using CAD for design work.

**Q: Can I export back to IFC?**  
A: Planned feature. Currently, export to JSON/CSV is supported.

**Q: What if my IFC file is from Revit 2015?**  
A: Older IFC exports (IFC2x3) work fine. Export quality depends on Revit version.

**Q: How accurate is the spatial data?**  
A: As accurate as your IFC export. Coordinates are preserved exactly from the IFC file.

**Q: Can I import multiple IFC files?**  
A: Yes. Each import creates a building. Import multiple times for multiple buildings.

**Q: What if equipment ends up in the wrong room?**  
A: This happens if IFC spatial containment is wrong. You can manually reassign in ArxOS.

**Q: Does import preserve materials/finishes?**  
A: Property sets are imported. Visual materials are not (ArxOS focuses on data, not rendering).

**Q: Can I import IFC files automatically?**  
A: Yes. Use the daemon to watch a folder and auto-import new IFC files.

**Q: What if import fails halfway through?**  
A: Imports are transactional. If it fails, nothing is created (no partial data).

---

## Common IFC Export Issues

### Issue: "No rooms created despite IfcSpace entities"

**Cause:** CAD software may export IfcSpace but not link them to floors properly.

**Solution:**
1. In your CAD software, ensure spaces are assigned to floors/stories
2. Check spatial containment relationships
3. Re-export with "Include spatial structure" enabled

### Issue: "Equipment has no location"

**Cause:** Equipment exported without placement data.

**Solution:**
1. In CAD, ensure equipment has 3D coordinates
2. Don't use 2D-only exports
3. Place equipment properly in the model before export

### Issue: "HVAC equipment not categorized correctly"

**Cause:** IFC type not recognized or generic IfcDistributionElement used.

**Solution:**
1. Use specific IFC types (IfcAirTerminalBox, not generic IfcDistributionElement)
2. Add equipment type in CAD metadata
3. Manually recategorize in ArxOS if needed

---

## Sample Workflow: School District

**Scenario:** District facilities manager wants to import 10 schools from IFC files.

**Workflow:**

1. **Get IFC files from architect**
   - Request IFC4 format
   - Request property sets included
   - Request one file per building

2. **Validate files before import**
   ```bash
   arx validate lincoln-hs.ifc
   ```

3. **Import each building**
   ```bash
   arx import lincoln-hs.ifc --name "Lincoln High School"
   arx import washington-es.ifc --name "Washington Elementary"
   # ... repeat for all 10 schools
   ```

4. **Verify imports**
   ```bash
   arx building list
   # Should show 10 buildings
   
   arx get /LINCOLN-HS/1/*/HVAC/* --count
   # Verify HVAC equipment extracted
   ```

5. **Supplement with BAS data**
   ```bash
   arx bas import metasys_points.csv --building lincoln-hs
   ```

6. **Create baseline version**
   ```bash
   arx commit -m "Initial import of all 10 schools from IFC"
   ```

**Result:** Complete building repository for all 10 schools with equipment, ready for facility management workflows.

---

## Integration with Other ArxOS Features

### After IFC Import, You Can:

**1. Add BAS Control Points**
```bash
arx bas import metasys_export.csv --building <building-id> --auto-map
```
BAS points will automatically map to rooms created from IFC.

**2. Query Equipment by Path**
```bash
arx get /MAIN/3/*/HVAC/*
```
Universal naming paths are auto-generated from IFC data.

**3. Scan with Mobile App**
- IFC provides baseline building structure
- Mobile AR adds real-world positioning
- Links IFC equipment to physical locations

**4. Track Changes Over Time**
```bash
arx commit -m "Initial IFC import"
# Later, re-import updated IFC
arx import building-updated.ifc
arx diff
```
See what changed between IFC versions.

---

## Advanced Topics

### Incremental IFC Updates

**Scenario:** Architect sends updated IFC after design changes.

**Approach:**
1. Create a branch for the update
   ```bash
   arx branch create update/architect-rev-b
   ```

2. Import updated IFC to the branch
   ```bash
   arx import building-rev-b.ifc --branch update/architect-rev-b
   ```

3. Review changes
   ```bash
   arx diff main update/architect-rev-b
   ```

4. Merge if acceptable
   ```bash
   arx merge update/architect-rev-b -m "Applied architect updates from Rev B"
   ```

### Custom Property Mapping

**Scenario:** You want to map specific IFC properties to custom fields.

Currently, all property sets are stored in `Equipment.Metadata` as JSON. You can:
1. Query metadata fields via API
2. Extract specific properties programmatically
3. Create custom views in database

**Future:** Template-based property mapping.

### Combining Multiple IFC Sources

**Scenario:** Architectural IFC + MEP IFC from different consultants.

**Approach:**
1. Import architectural IFC first (creates building structure)
2. Import MEP IFC to same building (adds equipment)
3. ArxOS merges based on spatial containment

**Note:** Duplicate detection is basic. Review carefully.

---

## Related Documentation

- [IfcOpenShell Service API](../integration/IFCOPENSHELL_SERVICE_API.md) - Technical API reference
- [IfcOpenShell Integration Architecture](../integration/IFCOPENSHELL_INTEGRATION.md) - System architecture
- [Universal Naming Convention](naming-convention.md) - How paths are generated
- [Database Setup](database-setup.md) - Database requirements

---

## External Resources

- [buildingSMART IFC Specification](https://www.buildingsmart.org/standards/bsi-standards/industry-foundation-classes/)
- [IfcOpenShell Documentation](http://ifcopenshell.org/)
- [IFC File Viewer (Online)](https://www.ifcviewer.com/)
- [BIM Collab ZOOM (Free IFC Viewer)](https://www.bimcollab.com/en/products/bimcollab-zoom)

---

## Getting Help

**IFC Import Not Working?**
1. Check service status: `docker ps | grep ifcopenshell`
2. View service logs: `docker logs arxos-ifcopenshell-service-1`
3. Validate IFC file: `arx validate building.ifc`
4. Check file format: Open in text editor, verify `ISO-10303-21` header

**Questions?**
- See [Troubleshooting](#troubleshooting) section above
- Check GitHub Issues
- Review [Integration Architecture](../integration/IFCOPENSHELL_INTEGRATION.md)

---

**Quick Reference Card:**

```
┌─────────────────────────────────────────────┐
│  IFC IMPORT QUICK REFERENCE                 │
├─────────────────────────────────────────────┤
│  arx import building.ifc                    │
│    → Import IFC file                        │
│                                             │
│  arx validate building.ifc                  │
│    → Check IFC before import                │
│                                             │
│  arx building list                          │
│    → Verify import success                  │
│                                             │
│  arx get /BUILDING/FLOOR/ROOM/SYSTEM/*     │
│    → Query imported equipment               │
│                                             │
│  Supported: IFC4, IFC2x3                    │
│  Max Size: 200MB                            │
│  Extracts: Buildings, Floors, Rooms, Equip  │
└─────────────────────────────────────────────┘
```

---

*This guide focuses on practical IFC import for facility management. For BIM authoring and design, continue using your CAD software.*

