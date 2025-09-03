//! Example API Client for ArxOS REST API
//! 
//! Demonstrates how to query building intelligence via HTTP

use reqwest;
use serde_json::Value;
use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    
    let base_url = if args.len() > 1 {
        args[1].clone()
    } else {
        "http://localhost:3000".to_string()
    };
    
    println!("ArxOS API Client Demo");
    println!("====================");
    println!("Server: {}", base_url);
    println!();
    
    let client = reqwest::Client::new();
    
    // 1. Health check
    println!("1. Health Check:");
    let resp = client.get(format!("{}/health", base_url))
        .send()
        .await?
        .json::<Value>()
        .await?;
    println!("   Status: {}", resp["status"]);
    println!("   Version: {}", resp["version"]);
    println!();
    
    // 2. Get statistics
    println!("2. Database Statistics:");
    let resp = client.get(format!("{}/api/stats", base_url))
        .send()
        .await?
        .json::<Value>()
        .await?;
    
    if let Some(total) = resp["total_objects"].as_u64() {
        println!("   Total objects: {}", total);
        println!("   Buildings: {}", resp["building_count"]);
        
        if let Some(types) = resp["type_distribution"].as_array() {
            println!("   Object types:");
            for t in types.iter().take(5) {
                println!("      - {}: {} ({})", 
                    t["object_type"], 
                    t["count"],
                    t["category"]);
            }
        }
    } else {
        println!("   No data in database");
    }
    println!();
    
    // 3. Find objects near a point
    println!("3. Finding objects within 2 meters of (5, 5, 1):");
    let resp = client.get(format!("{}/api/objects/radius", base_url))
        .query(&[
            ("x", "5"),
            ("y", "5"),
            ("z", "1"),
            ("radius", "2"),
        ])
        .send()
        .await?
        .json::<Value>()
        .await?;
    
    if let Some(objects) = resp["objects"].as_array() {
        println!("   Found {} objects", objects.len());
        for (i, obj) in objects.iter().take(3).enumerate() {
            println!("   {}. {} at ({:.2}m, {:.2}m, {:.2}m)",
                i + 1,
                obj["object_type"],
                obj["position"]["x_m"],
                obj["position"]["y_m"],
                obj["position"]["z_m"]);
        }
    }
    println!();
    
    // 4. Find nearest objects
    println!("4. Finding 5 nearest objects to maintenance point (10, 10, 1):");
    let resp = client.get(format!("{}/api/objects/nearest", base_url))
        .query(&[
            ("x", "10"),
            ("y", "10"),
            ("z", "1"),
            ("limit", "5"),
        ])
        .send()
        .await?
        .json::<Value>()
        .await?;
    
    if let Some(objects) = resp["objects"].as_array() {
        println!("   Found {} nearest objects", objects.len());
        for (i, item) in objects.iter().enumerate() {
            let obj = &item["object"];
            println!("   {}. {} at {:.2}m distance",
                i + 1,
                obj["object_type"],
                item["distance_m"]);
        }
    }
    println!();
    
    // 5. Get objects on a specific floor
    println!("5. Getting objects on ground floor (building 1):");
    let resp = client.get(format!("{}/api/objects/floor/1/0", base_url))
        .send()
        .await?
        .json::<Value>()
        .await?;
    
    if let Some(count) = resp["count"].as_u64() {
        println!("   Found {} objects on ground floor", count);
        
        // Count by category
        let mut categories = std::collections::HashMap::new();
        if let Some(objects) = resp["objects"].as_array() {
            for obj in objects {
                let cat = obj["category"].as_str().unwrap_or("Unknown");
                *categories.entry(cat).or_insert(0) += 1;
            }
            
            println!("   By category:");
            for (cat, count) in categories {
                println!("      - {}: {}", cat, count);
            }
        }
    }
    println!();
    
    // 6. Get all objects in building
    println!("6. Getting building 1 summary:");
    let resp = client.get(format!("{}/api/objects/building/1", base_url))
        .send()
        .await?
        .json::<Value>()
        .await?;
    
    if let Some(count) = resp["count"].as_u64() {
        println!("   Total objects in building: {}", count);
        
        if let Some(objects) = resp["objects"].as_array() {
            // Find bounds
            let mut min_z = f64::MAX;
            let mut max_z = f64::MIN;
            
            for obj in objects {
                if let Some(z) = obj["position"]["z_m"].as_f64() {
                    min_z = min_z.min(z);
                    max_z = max_z.max(z);
                }
            }
            
            if min_z != f64::MAX {
                let floors = ((max_z / 3.0).ceil() as i32).max(1);
                println!("   Height range: {:.1}m to {:.1}m", min_z, max_z);
                println!("   Estimated floors: {}", floors);
            }
        }
    }
    
    println!();
    println!("✅ API client demo complete!");
    
    Ok(())
}