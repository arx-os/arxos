package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	// Serve static files
	fs := http.FileServer(http.Dir("."))
	http.Handle("/", fs)

	// Simple API endpoint for testing
	http.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"ok","message":"Arxos test server running"}`))
	})

	fmt.Printf("Arxos test server running on http://localhost:%s\n", port)
	fmt.Println("Available demos:")
	fmt.Printf("  - PDF Wall Extractor: http://localhost:%s/pdf_wall_extractor.html\n", port)
	fmt.Printf("  - PDF Wall Extractor V2: http://localhost:%s/pdf_wall_extractor_v2.html\n", port)
	fmt.Printf("  - BIM Viewer: http://localhost:%s/bim_viewer.html\n", port)
	fmt.Printf("  - BIM 3D Viewer: http://localhost:%s/bim_3d_viewer.html\n", port)
	fmt.Printf("  - Arxos 14KB: http://localhost:%s/arxos_14kb.html\n", port)
	fmt.Printf("  - Arxos 10KB: http://localhost:%s/arxos_10kb.html\n", port)
	fmt.Printf("  - Arxos 14KB Pro: http://localhost:%s/arxos_14kb_pro.html\n", port)
	fmt.Printf("  - Test PDF Batch: http://localhost:%s/test_pdf_batch.html\n", port)

	log.Fatal(http.ListenAndServe(":"+port, nil))
}