package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"time"
)

func main() {
	baseURL := "http://localhost:8080"
	
	// Test 1: Check health
	fmt.Println("=== Testing Arxos System ===\n")
	fmt.Println("1. Health Check:")
	resp, err := http.Get(baseURL + "/health")
	if err != nil {
		log.Fatalf("Health check failed: %v", err)
	}
	body, _ := io.ReadAll(resp.Body)
	fmt.Printf("   Status: %s\n", resp.Status)
	fmt.Printf("   Response: %s\n", string(body))
	resp.Body.Close()
	
	// Test 2: Get current ArxObjects
	fmt.Println("\n2. Current ArxObjects:")
	resp, err = http.Get(baseURL + "/api/arxobjects")
	if err != nil {
		log.Printf("Failed to get ArxObjects: %v", err)
	} else {
		var objects []map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&objects)
		fmt.Printf("   Total objects: %d\n", len(objects))
		if len(objects) > 0 {
			fmt.Printf("   Sample object: Type=%v, System=%v, X=%v\n", 
				objects[0]["type"], objects[0]["system"], objects[0]["x"])
		}
		resp.Body.Close()
	}
	
	// Test 3: Test tile service
	fmt.Println("\n3. Tile Service:")
	tileURL := fmt.Sprintf("%s/api/tiles/5/0/0", baseURL) // Floor level, tile 0,0
	resp, err = http.Get(tileURL)
	if err != nil {
		log.Printf("Tile request failed: %v", err)
	} else {
		var tileData []map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&tileData)
		fmt.Printf("   Tile [5/0/0] contains %d objects\n", len(tileData))
		resp.Body.Close()
	}
	
	// Test 4: Create a new ArxObject
	fmt.Println("\n4. Creating New ArxObject:")
	newObject := map[string]interface{}{
		"type":   "sensor",
		"system": "hvac",
		"x":      5000,
		"y":      3000,
		"z":      0,
		"width":  100,
		"height": 100,
		"properties": map[string]interface{}{
			"sensor_type": "temperature",
			"location":    "Test Room",
			"unit":        "celsius",
		},
	}
	
	objectJSON, _ := json.Marshal(newObject)
	resp, err = http.Post(baseURL+"/api/arxobjects", "application/json", bytes.NewBuffer(objectJSON))
	if err != nil {
		log.Printf("Failed to create ArxObject: %v", err)
	} else {
		body, _ := io.ReadAll(resp.Body)
		fmt.Printf("   Status: %s\n", resp.Status)
		
		var created map[string]interface{}
		if err := json.Unmarshal(body, &created); err == nil {
			fmt.Printf("   Created object ID: %v\n", created["id"])
		} else {
			fmt.Printf("   Response: %s\n", string(body))
		}
		resp.Body.Close()
	}
	
	// Test 5: Test PDF upload with a simple test file
	fmt.Println("\n5. PDF Upload Test:")
	
	// Check if we have a PDF to test with
	pdfPath := "uploads/1755622664_Alafia_ES_IDF_CallOut.pdf"
	if _, err := os.Stat(pdfPath); os.IsNotExist(err) {
		fmt.Println("   No PDF file found to test upload")
	} else {
		// Create multipart form
		var requestBody bytes.Buffer
		writer := multipart.NewWriter(&requestBody)
		
		// Add PDF file
		file, err := os.Open(pdfPath)
		if err != nil {
			log.Printf("Failed to open PDF: %v", err)
		} else {
			defer file.Close()
			
			part, err := writer.CreateFormFile("pdf", "test_floor_plan.pdf")
			if err != nil {
				log.Printf("Failed to create form file: %v", err)
			} else {
				io.Copy(part, file)
			}
			
			// Add form fields
			writer.WriteField("building_name", "Test Building From Go")
			writer.WriteField("floor_number", "1")
			writer.Close()
			
			// Send request
			req, _ := http.NewRequest("POST", baseURL+"/api/upload/pdf", &requestBody)
			req.Header.Set("Content-Type", writer.FormDataContentType())
			
			client := &http.Client{Timeout: 30 * time.Second}
			resp, err := client.Do(req)
			if err != nil {
				log.Printf("PDF upload failed: %v", err)
			} else {
				body, _ := io.ReadAll(resp.Body)
				fmt.Printf("   Status: %s\n", resp.Status)
				
				var result map[string]interface{}
				if err := json.Unmarshal(body, &result); err == nil {
					fmt.Printf("   Building: %v\n", result["building_name"])
					fmt.Printf("   Objects created: %v\n", result["object_count"])
					fmt.Printf("   Process time: %v seconds\n", result["process_time_seconds"])
				} else {
					fmt.Printf("   Response: %s\n", string(body))
				}
				resp.Body.Close()
			}
		}
	}
	
	// Test 6: Check WebSocket connectivity
	fmt.Println("\n6. WebSocket Status:")
	fmt.Println("   WebSocket endpoint available at: ws://localhost:8080/ws")
	fmt.Println("   (Would need gorilla/websocket to test actual connection)")
	
	// Test 7: Check confidence levels
	fmt.Println("\n7. Object Confidence Distribution:")
	resp, err = http.Get(baseURL + "/api/arxobjects")
	if err == nil {
		var objects []map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&objects)
		
		highConf, medConf, lowConf := 0, 0, 0
		for _, obj := range objects {
			if conf, ok := obj["confidence"].(map[string]interface{}); ok {
				if overall, ok := conf["overall"].(float64); ok {
					if overall > 0.85 {
						highConf++
					} else if overall >= 0.60 {
						medConf++
					} else {
						lowConf++
					}
				}
			}
		}
		
		fmt.Printf("   High confidence (>0.85): %d objects\n", highConf)
		fmt.Printf("   Medium confidence (0.60-0.85): %d objects\n", medConf)  
		fmt.Printf("   Low confidence (<0.60): %d objects\n", lowConf)
		resp.Body.Close()
	}
	
	fmt.Println("\n=== Test Complete ===")
}