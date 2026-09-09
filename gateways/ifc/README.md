# arxos-ifc

IFC4 gateway for the Arxos spatial object graph.

## Scope

- **Format**: STEP physical file (`ISO-10303-21`), conforming to the `IFC4` schema.
- **Hierarchy Mapping**: Project → Site → Building → BuildingStorey → Space.
- **Identity Preservation**: Attaches custom property sets (`Pset_ArxosIdentity`) containing `Cid`, `BuildingId`, and `ObjectType`. Derives stable IFC GlobalIds deterministically from object CIDs.
- **Fidelity**: Structure (Project / Site / Storey / Space) plus **realized solids** (`IfcWall` / `IfcSlab` / `IfcDoor` / `IfcWindow` / `IfcOpeningElement` + `IfcRelVoidsElement` / proxy / flow segment) from \(R(S)\). Identity pset `Pset_ArxosIdentity` (`Cid`, `BuildingId`, `ObjectType`, `EntityId`) and measure pset `Pset_ArxosMeasure` (`SigmaMm`, `SupportCount`, `ExtentX/Y/Z`). Still **not** IFC CoordinationView certified.

## Usage

```bash
arx export ifc $BUILDING_ID -o building.ifc
arx import ifc building.ifc
```
