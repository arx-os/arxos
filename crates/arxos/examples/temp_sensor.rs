use arx::depin::{EquipmentSensorMapping, SensorReadingValidator, SensorType};

fn main() {
    let mapping = EquipmentSensorMapping {
        equipment_id: "AHU-001".to_string(),
        sensor_id: "TEMP-001".to_string(),
        sensor_type: SensorType::Temperature,
        threshold_min: Some(18.0),
        threshold_max: Some(26.0),
        alert_on_out_of_range: true,
    };

    let validator = SensorReadingValidator::new(&mapping);

    for reading in [22.0, 27.5] {
        let outcome = validator.evaluate(reading);
        println!("Reading {reading:.1}°C -> {:?}", outcome);

        if validator.should_alert(&outcome) {
            println!("  ⚠️  Alert: reading outside configured thresholds");
        }
    }
}
