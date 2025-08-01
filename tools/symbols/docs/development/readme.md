# Arxos Symbol Library (`arx-symbol-library`)

**`arx-symbol-library`** is the centralized repository of graphical symbols (inlined SVG) used throughout the Arxos platform for building system markup and logic modeling. Each symbol represents a physical or logical component within a building's infrastructure.

---

## 📦 Overview

This library provides:

- 🔹 Standardized SVG symbols for all major building systems  
- 🔹 Categorization by discipline (e.g., electrical, mechanical, AV, plumbing)  
- 🔹 Structured metadata for integration with `svgx-engine`, `arx_symbol`, and `object_type` schemas  
- 🔹 Future support for AI-based search, filtering, and behavior simulation

---

## 📁 Structure

```
/arx-symbol-library/
├── symbols/
│   ├── mechanical/          # HVAC, air handling, etc.
│   ├── electrical/          # Power, lighting, etc.
│   ├── plumbing/            # Water, drainage, etc.
│   ├── fire_alarm/          # Fire detection and alarm
│   ├── security/            # Access control, CCTV, etc.
│   ├── network/             # Data, telecommunications
│   ├── building_controls/   # Building automation
│   ├── telecommunications/  # Phone, intercom systems
│   └── av/                  # Audio/visual systems
├── schemas/                 # JSON schemas for validation
├── index.json               # Symbol library index
├── categories.json          # Category definitions
└── systems.json            # System definitions
```

Symbols are organized by system category, with each symbol file containing:

```json
{
  "system": "mechanical",
  "display_name": "Air Handling Unit (AHU)",
  "description": "Central air handling unit for HVAC system",
  "svg": "<g id=\"ahu\"><rect x=\"0\" y=\"0\" width=\"40\" height=\"20\" fill=\"#ccc\" stroke=\"#000\"/><text x=\"20\" y=\"15\" font-size=\"10\" text-anchor=\"middle\">AHU</text></g>",
  "properties": {
    "height": 20,
    "width": 40
  },
  "connections": [
    {
      "type": "ductwork",
      "description": "Connection to duct system"
    },
    {
      "type": "power",
      "description": "Electrical power connection"
    }
  ],
  "tags": ["mechanical", "hvac", "air_handling"]
}
```

---

## 🔌 Integration

This library is used by the following Arxos components:

| Component            | Purpose |
|---------------------|---------|
| `svgx-engine`        | Renders symbols on SVG floor plans |

| `arxfile.json`       | References `arx_symbol` ID in object metadata |
| `ascii-bim`          | CLI/text-based visual mapping |
| `behavior_profiles`  | (Future) Logic simulation profiles linked to symbols |

---

## 📜 Symbol Metadata Fields

| Field         | Description |
|---------------|-------------|
| `system`      | Building system (e.g. electrical, plumbing) |
| `display_name`| Human-readable name |
| `svg`         | Inline SVG markup |
| *(optional)* `tags` | Keywords for search and AI |
| *(optional)* `symbol_type` | Type classification (`device`, `conduit`, `sensor`) |
| *(optional)* `interactive_fields` | For object editing (e.g. voltage, name) |
| *(optional)* `funding_source` | Source of funding for this asset/component (string, e.g. 'Capital Budget', 'Operating Budget') |

---

## 🛠 Contributing

We welcome symbol contributions for new systems or components!

1. Fork the repo and add your symbol to the correct `.json` file
2. Follow existing formatting and ID conventions
3. Ensure all `svg` markup is enclosed in a `<g id="...">` wrapper
4. Submit a pull request with a clear description

---

## 📅 Roadmap

- [x] Organize symbols by system category in structured directories
- [x] Convert current Python symbol dictionary to modular JSON format
- [ ] Add searchable manifest
- [ ] Add symbol versioning and visual previews
- [ ] Create interactive web interface for viewing and testing symbols
- [ ] Link symbols to `behavior_profiles` and system logic

---

## 🔗 Related Repositories


- [`arx-backend`](https://github.com/capstanistan/arx-backend)
- [`arx-docs`](https://github.com/capstanistan/arx-docs)
- [`arx-infra`](https://github.com/capstanistan/arx-infra)

---

## 🔤 Example Symbols

```json
{
  "system": "mechanical",
  "display_name": "Air Handling Unit (AHU)",
  "funding_source": "Capital Budget",
  "svg": "<g id=\"ahu\"><rect x=\"0\" y=\"0\" width=\"40\" height=\"20\" fill=\"#ccc\" stroke=\"#000\"/><text x=\"20\" y=\"15\" font-size=\"10\" text-anchor=\"middle\">AHU</text></g>"
}
```

```json
{
  "system": "electrical",
  "display_name": "Receptacle",
  "funding_source": "Operating Budget",
  "svg": "<g id=\"receptacle\"><circle cx=\"10\" cy=\"10\" r=\"7\" fill=\"#fff\" stroke=\"#000\"/><text x=\"10\" y=\"14\" font-size=\"8\" text-anchor=\"middle\">R</text></g>"
}
```

---

## License

MIT License © 2025 Arxos / Capstanistan
