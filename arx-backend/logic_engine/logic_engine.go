package logic_engine

// ObjectTypesRegistry contains the registry of all available object types
var ObjectTypesRegistry = map[string]interface{}{
	"wall": map[string]interface{}{
		"name":        "Wall",
		"category":    "structural",
		"properties":  []string{"type", "material", "thickness", "height", "fire_rating", "insulation"},
		"connections": []string{"room_id_1", "room_id_2"},
	},
	"room": map[string]interface{}{
		"name":        "Room",
		"category":    "spatial",
		"properties":  []string{"name", "type", "area", "height"},
		"connections": []string{"walls", "devices", "labels"},
	},
	"device": map[string]interface{}{
		"name":        "Device",
		"category":    "equipment",
		"properties":  []string{"type", "system", "subtype", "manufacturer", "model"},
		"connections": []string{"room_id", "panel_id", "circuit_id", "upstream_id", "downstream_id"},
	},
	"label": map[string]interface{}{
		"name":        "Label",
		"category":    "annotation",
		"properties":  []string{"text", "font_size", "color"},
		"connections": []string{"room_id", "upstream_id", "downstream_id"},
	},
	"zone": map[string]interface{}{
		"name":        "Zone",
		"category":    "spatial",
		"properties":  []string{"name", "type", "area"},
		"connections": []string{"rooms", "devices"},
	},
}

// BehaviorProfilesRegistry contains the registry of all available behavior profiles
var BehaviorProfilesRegistry = map[string]interface{}{
	"wall": map[string]interface{}{
		"validation": map[string]interface{}{
			"thickness": map[string]interface{}{
				"min":  0.1,
				"max":  2.0,
				"unit": "meters",
			},
			"height": map[string]interface{}{
				"min":  2.0,
				"max":  10.0,
				"unit": "meters",
			},
		},
		"simulation": map[string]interface{}{
			"thermal_resistance": "R = thickness / thermal_conductivity",
			"structural_load":    "load = height * thickness * density * gravity",
		},
	},
	"device": map[string]interface{}{
		"validation": map[string]interface{}{
			"power_rating": map[string]interface{}{
				"min":  0.0,
				"max":  1000000.0,
				"unit": "watts",
			},
		},
		"simulation": map[string]interface{}{
			"power_consumption": "P = voltage * current",
			"heat_generation":   "Q = power_consumption * efficiency_factor",
		},
	},
}
