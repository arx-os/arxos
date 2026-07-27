# arxos-usd

OpenUSD **projection** of the Arxos object graph (Phase 4).

## Scope

- **Wire format:** USDA 1.0 (ASCII) — loadable by OpenUSD tools (`usdview`, etc.)
- **Hierarchy:** Building → Floor → Space → Annotation / Points / Equipment
- **Identity:** `arxos:cid`, `arxos:type`, `arxos:buildingId`, layer `customLayerData`
- Geometry is **data only** (points, extents, xforms). Arxos never owns general 3D rendering.

## Usage

```bash
arxos export usd $BUILDING_ID -o building.usda
arxos import usd building.usda
```

## Expanding coverage

Prefer growing the projection map deliberately (more IFC/USD schema classes)
rather than pulling full OpenUSD C++ until a host app needs USDC/crate I/O.
