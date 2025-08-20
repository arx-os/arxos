package main

import (
	"fmt"
)

func main() {
	fmt.Println("🏗️ Testing Arxos Ingestion Pipeline")
	fmt.Println("Note: Since ingestion package imports aren't working in this test,")
	fmt.Println("run: go run ingestion/*.go to test the pipeline directly.")
	fmt.Println("Or check the test function in ingestion/test_pipeline.go")
}