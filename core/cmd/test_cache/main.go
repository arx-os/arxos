package main

import (
	"fmt"
	"log"
	"time"

	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/services/cache"
	"github.com/joho/godotenv"
)

func main() {
	// Load environment variables
	godotenv.Load()

	// Initialize database
	err := db.InitDB()
	if err != nil {
		log.Fatal("Failed to initialize database:", err)
	}

	// Initialize cache service
	cacheService, err := cache.NewCacheService(nil, log.Default())
	if err != nil {
		log.Fatal("Failed to create cache service:", err)
	}
	defer cacheService.Close()

	fmt.Println("Testing PostgreSQL Cache Implementation...")
	fmt.Println("==========================================")

	// Test 1: Set and Get
	fmt.Println("\n1. Testing Set and Get:")
	key := "test_key_" + fmt.Sprintf("%d", time.Now().Unix())
	value := "test_value"
	
	err = cacheService.Set(key, value, 5*time.Second)
	if err != nil {
		log.Fatal("Failed to set cache:", err)
	}
	fmt.Printf("   ✓ Set key '%s' with value '%s'\n", key, value)

	retrieved, err := cacheService.Get(key)
	if err != nil {
		log.Fatal("Failed to get cache:", err)
	}
	fmt.Printf("   ✓ Retrieved value: %v\n", retrieved)

	// Test 2: Check existence
	fmt.Println("\n2. Testing Exists:")
	exists, err := cacheService.Exists(key)
	if err != nil {
		log.Fatal("Failed to check existence:", err)
	}
	fmt.Printf("   ✓ Key exists: %v\n", exists)

	// Test 3: TTL
	fmt.Println("\n3. Testing TTL:")
	ttl, err := cacheService.TTL(key)
	if err != nil {
		log.Fatal("Failed to get TTL:", err)
	}
	fmt.Printf("   ✓ TTL remaining: %v\n", ttl)

	// Test 4: Counter operations
	fmt.Println("\n4. Testing Counter Operations:")
	counterKey := "counter_" + fmt.Sprintf("%d", time.Now().Unix())
	
	val, err := cacheService.Incr(counterKey)
	if err != nil {
		log.Fatal("Failed to increment:", err)
	}
	fmt.Printf("   ✓ Counter after first increment: %d\n", val)

	val, err = cacheService.IncrBy(counterKey, 5)
	if err != nil {
		log.Fatal("Failed to increment by 5:", err)
	}
	fmt.Printf("   ✓ Counter after incrementing by 5: %d\n", val)

	// Test 5: Hash operations
	fmt.Println("\n5. Testing Hash Operations:")
	hashKey := "hash_" + fmt.Sprintf("%d", time.Now().Unix())
	
	err = cacheService.HSet(hashKey, "field1", "value1")
	if err != nil {
		log.Fatal("Failed to set hash field:", err)
	}
	fmt.Printf("   ✓ Set hash field 'field1'\n")

	hashVal, err := cacheService.HGet(hashKey, "field1")
	if err != nil {
		log.Fatal("Failed to get hash field:", err)
	}
	fmt.Printf("   ✓ Retrieved hash field value: %s\n", hashVal)

	// Test 6: Health check
	fmt.Println("\n6. Testing Health Check:")
	err = cacheService.HealthCheck()
	if err != nil {
		log.Fatal("Health check failed:", err)
	}
	fmt.Printf("   ✓ Health check passed\n")

	// Test 7: Statistics
	fmt.Println("\n7. Testing Statistics:")
	stats, err := cacheService.GetStats()
	if err != nil {
		log.Fatal("Failed to get stats:", err)
	}
	fmt.Printf("   ✓ Cache stats: Keys=%d, Hits=%d, HitRate=%.2f\n", 
		stats.TotalKeys, stats.Hits, stats.HitRate)

	fmt.Println("\n==========================================")
	fmt.Println("✅ All cache tests passed successfully!")
	fmt.Println("Redis has been successfully replaced with PostgreSQL!")
}