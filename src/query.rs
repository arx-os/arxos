//! Query engine for ArxOS

use crate::models::{Building, BuildingObject};
use anyhow::Result;

pub struct QueryEngine<'a> {
    building: &'a Building,
}

impl<'a> QueryEngine<'a> {
    pub fn new(building: &'a Building) -> Self {
        Self { building }
    }
    
    pub fn execute(&self, query: &str) -> Result<Vec<&BuildingObject>> {
        let query_upper = query.to_uppercase();
        
        // Simple query parser
        if query_upper.contains("WHERE") {
            let parts: Vec<&str> = query.split_whitespace().collect();
            
            if let Some(where_idx) = parts.iter().position(|&s| s.eq_ignore_ascii_case("WHERE")) {
                if where_idx + 2 < parts.len() {
                    let field = parts[where_idx + 1];
                    let operator = parts.get(where_idx + 2).copied().unwrap_or("=");
                    let value = parts[where_idx + 3..].join(" ")
                        .replace("'", "")
                        .replace("\"", "");
                    
                    return self.filter_objects(field, operator, &value);
                }
            }
        }
        
        // Default: return all objects
        Ok(self.building.objects.values().collect())
    }
    
    fn filter_objects(&self, field: &str, operator: &str, value: &str) -> Result<Vec<&BuildingObject>> {
        let mut results = Vec::new();
        
        for obj in self.building.objects.values() {
            let matches = match field.to_lowercase().as_str() {
                "type" | "object_type" => {
                    self.compare_values(&obj.object_type, operator, value)
                }
                "status" => {
                    self.compare_values(&obj.state.status, operator, value)
                }
                "health" => {
                    self.compare_values(&obj.state.health, operator, value)
                }
                "needs_repair" => {
                    let needs = obj.state.needs_repair;
                    (value.eq_ignore_ascii_case("true") && needs) ||
                    (value.eq_ignore_ascii_case("false") && !needs)
                }
                "path" => {
                    if operator == "LIKE" || operator == "like" {
                        obj.path.contains(value)
                    } else {
                        self.compare_values(&obj.path, operator, value)
                    }
                }
                _ => {
                    // Check properties
                    if let Some(prop_value) = obj.properties.get(field) {
                        self.compare_json_value(prop_value, operator, value)
                    } else {
                        false
                    }
                }
            };
            
            if matches {
                results.push(obj);
            }
        }
        
        Ok(results)
    }
    
    fn compare_values(&self, field_value: &str, operator: &str, compare_value: &str) -> bool {
        match operator {
            "=" | "==" => field_value.eq_ignore_ascii_case(compare_value),
            "!=" | "<>" => !field_value.eq_ignore_ascii_case(compare_value),
            "LIKE" | "like" => field_value.to_lowercase().contains(&compare_value.to_lowercase()),
            _ => false,
        }
    }
    
    fn compare_json_value(&self, json_value: &serde_json::Value, operator: &str, compare_value: &str) -> bool {
        match json_value {
            serde_json::Value::String(s) => self.compare_values(s, operator, compare_value),
            serde_json::Value::Number(n) => {
                if let Ok(compare_num) = compare_value.parse::<f64>() {
                    if let Some(num) = n.as_f64() {
                        match operator {
                            "=" | "==" => (num - compare_num).abs() < 0.0001,
                            "!=" | "<>" => (num - compare_num).abs() >= 0.0001,
                            ">" => num > compare_num,
                            "<" => num < compare_num,
                            ">=" => num >= compare_num,
                            "<=" => num <= compare_num,
                            _ => false,
                        }
                    } else {
                        false
                    }
                } else {
                    false
                }
            }
            serde_json::Value::Bool(b) => {
                let compare_bool = compare_value.eq_ignore_ascii_case("true");
                match operator {
                    "=" | "==" => *b == compare_bool,
                    "!=" | "<>" => *b != compare_bool,
                    _ => false,
                }
            }
            _ => false,
        }
    }
}