# arxos-ifc

IFC4 **bidirectional** projection of the Arxos object graph (Phase 4).

## Scope

- STEP physical file (`ISO-10303-21`), schema `IFC4`
- Hierarchy: Project → Site → Building → BuildingStorey → Space
- Annotations as `IfcAnnotation` + `Pset_ArxosAnnotation`
- **Identity-preserving** property set `Pset_ArxosIdentity`:
  - `Cid`, `BuildingId`, `ObjectType`
- GlobalId derived deterministically from CID (stable re-exports)

## Usage

```bash
arx export ifc $BUILDING_ID -o building.ifc
arx import ifc building.ifc
```

## Fidelity

This is a **narrow correct subset**. Full BREP/mesh and vendor property coverage
is intentionally deferred — use USD for modern geometry interchange.
