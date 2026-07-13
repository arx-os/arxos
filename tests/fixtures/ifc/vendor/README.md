# Vendor IFC fixtures (slot for anonymized real files)

Drop anonymized Revit / ArchiCAD / FreeCAD exports here for Track B1.

## Requirements

- Strip personal names, project GUIDs if sensitive, proprietary macros
- Note original tool + version in a one-line `*.notes.md` beside the file
- License must allow repo distribution (or private CI only — document which)

## Until then

CI uses:

- `test_data/Building-Architecture.ifc` (SketchUp IFC-manager)
- `test_data/Building-Hvac.ifc`
- `test_data/sample_building.ifc` (Arx-authored)

See `docs/ifc-limitations.md`.
