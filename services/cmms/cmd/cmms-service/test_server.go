package main

import (
	"fmt"
	"log"
	"net/http"
	"time"
)

func testHTTPServer() {
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"status":"healthy","timestamp":"%s","service":"cmms"}`, time.Now().UTC().Format(time.RFC3339))
	})

	log.Println("🚀 Test HTTP Server starting on port 8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("Failed to start test HTTP server: %v", err)
	}
} 