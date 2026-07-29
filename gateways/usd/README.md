# arxos-usd

OpenUSD ASCII (USDA) gateway for the Arxos spatial object graph.

## Scope

- **Format**: USDA 1.0 (ASCII) — compatible with standard OpenUSD tools (e.g., `usdview`).
- **Hierarchy Mapping**: Building → Floor → Space → Annotation / Surface / Equipment.
- **Identity Preservation**: Embeds custom metadata attributes (`arxos:cid`, `arxos:type`, `arxos:buildingId`, and layer `customLayerData`) to allow reconstruction and round-trip verification.
- **Fidelity**: Focuses on spatial geometry as data (transforms, point lists, bounds). Arxos does not own 3D rendering.

## Usage

```bash
arx export usd $BUILDING_ID -o building.usda
arx import usd building.usda
```
