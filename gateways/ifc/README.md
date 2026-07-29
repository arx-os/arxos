# arxos-ifc

IFC4 gateway for the Arxos spatial object graph.

## Scope

- **Format**: STEP physical file (`ISO-10303-21`), conforming to the `IFC4` schema.
- **Hierarchy Mapping**: Project → Site → Building → BuildingStorey → Space.
- **Identity Preservation**: Attaches custom property sets (`Pset_ArxosIdentity`) containing `Cid`, `BuildingId`, and `ObjectType`. Derives stable IFC GlobalIds deterministically from object CIDs.
- **Fidelity**: Focuses on a narrow, correct structural schema subset (Project / Site / Storey / Space). Use OpenUSD for rich boundary representation / geometry.

## Usage

```bash
arx export ifc $BUILDING_ID -o building.ifc
arx import ifc building.ifc
```
