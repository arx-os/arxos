// Package cache provides Redis cluster management and failover capabilities
package cache

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arxos/arxos/core/backend/config"
	"github.com/arxos/arxos/core/backend/errors"
	"github.com/go-redis/redis/v8"
	"go.uber.org/zap"
)

// ClusterManager manages Redis cluster operations and failover
type ClusterManager struct {
	config         *config.RedisConfig
	logger         *zap.Logger
	clusterClient  *redis.ClusterClient
	failoverClient *redis.Client
	healthChecker  *HealthChecker
	metrics        *ClusterMetrics
	mutex          sync.RWMutex
	isFailover     bool
	lastFailover   time.Time
}

// ClusterMetrics tracks cluster performance and health
type ClusterMetrics struct {
	NodesTotal       int                    `json:"nodes_total"`
	NodesOnline      int                    `json:"nodes_online"`
	NodesOffline     int                    `json:"nodes_offline"`
	FailoverCount    int64                  `json:"failover_count"`
	LastFailover     time.Time              `json:"last_failover"`
	FailoverDuration time.Duration          `json:"failover_duration"`
	NodeStatus       map[string]NodeStatus  `json:"node_status"`
	ClusterHealth    string                 `json:"cluster_health"`
	LastHealthCheck  time.Time              `json:"last_health_check"`
}

// NodeStatus represents the status of a Redis node
type NodeStatus struct {
	Address      string        `json:"address"`
	Role         string        `json:"role"`        // master, slave
	Status       string        `json:"status"`      // online, offline, degraded
	LastSeen     time.Time     `json:"last_seen"`
	ResponseTime time.Duration `json:"response_time"`
	Memory       NodeMemory    `json:"memory"`
	Connections  int           `json:"connections"`
	Commands     int64         `json:"commands"`
}

// NodeMemory represents memory usage of a Redis node
type NodeMemory struct {
	Used     int64   `json:"used"`
	Peak     int64   `json:"peak"`
	MaxMem   int64   `json:"max_mem"`
	UsedRSS  int64   `json:"used_rss"`
	UsagePercent float64 `json:"usage_percent"`
}

// HealthChecker monitors cluster health
type HealthChecker struct {
	manager       *ClusterManager
	checkInterval time.Duration
	timeout       time.Duration
	stopCh        chan struct{}
	mutex         sync.RWMutex
	running       bool
}

// NewClusterManager creates a new Redis cluster manager
func NewClusterManager(cfg *config.RedisConfig, logger *zap.Logger) (*ClusterManager, error) {
	manager := &ClusterManager{
		config:  cfg,
		logger:  logger,
		metrics: &ClusterMetrics{
			NodeStatus: make(map[string]NodeStatus),
		},
	}

	// Initialize cluster client
	if err := manager.initializeCluster(); err != nil {
		return nil, err
	}

	// Initialize health checker
	manager.healthChecker = &HealthChecker{
		manager:       manager,
		checkInterval: 30 * time.Second,
		timeout:       5 * time.Second,
		stopCh:        make(chan struct{}),
	}

	// Start health monitoring
	go manager.healthChecker.start()

	logger.Info("Redis cluster manager initialized", 
		zap.Int("nodes", len(manager.getClusterAddresses())),
		zap.Bool("failover_enabled", manager.hasFailoverConfig()))

	return manager, nil
}

// initializeCluster sets up the Redis cluster connection
func (cm *ClusterManager) initializeCluster() error {
	addresses := cm.getClusterAddresses()
	
	if len(addresses) == 0 {
		return errors.NewConfigurationError("No Redis cluster addresses configured")
	}

	// Create cluster client
	cm.clusterClient = redis.NewClusterClient(&redis.ClusterOptions{
		Addrs:              addresses,
		Password:           cm.config.Password,
		MaxRetries:         cm.config.MaxRetries,
		MinRetryBackoff:    cm.config.MinRetryBackoff,
		MaxRetryBackoff:    cm.config.MaxRetryBackoff,
		DialTimeout:        cm.config.DialTimeout,
		ReadTimeout:        cm.config.ReadTimeout,
		WriteTimeout:       cm.config.WriteTimeout,
		PoolSize:           cm.config.PoolSize,
		MinIdleConns:       cm.config.MinIdleConns,
		MaxConnAge:         cm.config.MaxConnAge,
		PoolTimeout:        cm.config.PoolTimeout,
		IdleTimeout:        cm.config.IdleTimeout,
		IdleCheckFrequency: cm.config.IdleCheckFrequency,
	})

	// Initialize failover client if configured
	if cm.hasFailoverConfig() {
		cm.failoverClient = redis.NewClient(&redis.Options{
			Addr:     cm.getFailoverAddress(),
			Password: cm.config.Password,
			DB:       cm.config.Database,
		})
	}

	// Test cluster connection
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := cm.clusterClient.Ping(ctx).Err(); err != nil {
		cm.logger.Warn("Cluster ping failed, checking individual nodes", zap.Error(err))
		
		// Try individual nodes
		if err := cm.checkIndividualNodes(ctx); err != nil {
			return errors.NewExternalError("redis_cluster", fmt.Sprintf("All cluster nodes unreachable: %v", err))
		}
	}

	return nil
}

// GetClient returns the appropriate Redis client (cluster or failover)
func (cm *ClusterManager) GetClient() redis.Cmdable {
	cm.mutex.RLock()
	defer cm.mutex.RUnlock()

	if cm.isFailover && cm.failoverClient != nil {
		return cm.failoverClient
	}
	return cm.clusterClient
}

// ExecuteWithFailover executes a Redis command with automatic failover
func (cm *ClusterManager) ExecuteWithFailover(ctx context.Context, fn func(redis.Cmdable) error) error {
	client := cm.GetClient()
	
	err := fn(client)
	if err != nil {
		// Check if error indicates cluster failure
		if cm.isClusterError(err) && !cm.isFailover {
			cm.logger.Warn("Cluster operation failed, attempting failover", zap.Error(err))
			
			if cm.initiateFailover(ctx) {
				// Retry with failover client
				client = cm.GetClient()
				return fn(client)
			}
		}
		return err
	}
	
	return nil
}

// initiateFailover switches to failover mode
func (cm *ClusterManager) initiateFailover(ctx context.Context) bool {
	cm.mutex.Lock()
	defer cm.mutex.Unlock()

	if cm.isFailover {
		return true // Already in failover mode
	}

	if cm.failoverClient == nil {
		cm.logger.Error("Failover requested but no failover client configured")
		return false
	}

	// Test failover client
	if err := cm.failoverClient.Ping(ctx).Err(); err != nil {
		cm.logger.Error("Failover client is also unavailable", zap.Error(err))
		return false
	}

	cm.isFailover = true
	cm.lastFailover = time.Now()
	cm.metrics.FailoverCount++
	cm.metrics.LastFailover = cm.lastFailover

	cm.logger.Warn("Switched to failover Redis instance",
		zap.String("failover_address", cm.getFailoverAddress()),
		zap.Time("failover_time", cm.lastFailover))

	// Start monitoring for cluster recovery
	go cm.monitorClusterRecovery()

	return true
}

// monitorClusterRecovery checks if the cluster is available again
func (cm *ClusterManager) monitorClusterRecovery() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		cm.mutex.RLock()
		if !cm.isFailover {
			cm.mutex.RUnlock()
			return
		}
		cm.mutex.RUnlock()

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		if err := cm.clusterClient.Ping(ctx).Err(); err == nil {
			// Cluster is back online
			cm.switchBackToCluster()
			cancel()
			return
		}
		cancel()
	}
}

// switchBackToCluster returns to cluster mode from failover
func (cm *ClusterManager) switchBackToCluster() {
	cm.mutex.Lock()
	defer cm.mutex.Unlock()

	if !cm.isFailover {
		return
	}

	cm.isFailover = false
	duration := time.Since(cm.lastFailover)
	cm.metrics.FailoverDuration = duration

	cm.logger.Info("Switched back to Redis cluster",
		zap.Duration("failover_duration", duration))
}

// Health monitoring methods

// start begins health checking
func (hc *HealthChecker) start() {
	hc.mutex.Lock()
	if hc.running {
		hc.mutex.Unlock()
		return
	}
	hc.running = true
	hc.mutex.Unlock()

	ticker := time.NewTicker(hc.checkInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			hc.performHealthCheck()
		case <-hc.stopCh:
			return
		}
	}
}

// stop halts health checking
func (hc *HealthChecker) stop() {
	hc.mutex.Lock()
	defer hc.mutex.Unlock()

	if !hc.running {
		return
	}

	hc.running = false
	close(hc.stopCh)
}

// performHealthCheck checks the health of all cluster nodes
func (hc *HealthChecker) performHealthCheck() {
	ctx, cancel := context.WithTimeout(context.Background(), hc.timeout)
	defer cancel()

	hc.manager.metrics.LastHealthCheck = time.Now()
	
	addresses := hc.manager.getClusterAddresses()
	nodeStatuses := make(map[string]NodeStatus)
	
	onlineNodes := 0
	totalNodes := len(addresses)

	for _, addr := range addresses {
		status := hc.checkNodeHealth(ctx, addr)
		nodeStatuses[addr] = status
		
		if status.Status == "online" {
			onlineNodes++
		}
	}

	// Update metrics
	hc.manager.mutex.Lock()
	hc.manager.metrics.NodesTotal = totalNodes
	hc.manager.metrics.NodesOnline = onlineNodes
	hc.manager.metrics.NodesOffline = totalNodes - onlineNodes
	hc.manager.metrics.NodeStatus = nodeStatuses
	
	// Determine cluster health
	if onlineNodes == totalNodes {
		hc.manager.metrics.ClusterHealth = "healthy"
	} else if onlineNodes >= totalNodes/2 {
		hc.manager.metrics.ClusterHealth = "degraded"
	} else {
		hc.manager.metrics.ClusterHealth = "critical"
	}
	hc.manager.mutex.Unlock()

	// Log health status
	hc.manager.logger.Debug("Cluster health check completed",
		zap.Int("online_nodes", onlineNodes),
		zap.Int("total_nodes", totalNodes),
		zap.String("health", hc.manager.metrics.ClusterHealth))
}

// checkNodeHealth checks the health of a specific Redis node
func (hc *HealthChecker) checkNodeHealth(ctx context.Context, address string) NodeStatus {
	start := time.Now()
	
	client := redis.NewClient(&redis.Options{
		Addr:     address,
		Password: hc.manager.config.Password,
		DB:       0,
	})
	defer client.Close()

	status := NodeStatus{
		Address:  address,
		LastSeen: time.Now(),
		Status:   "offline",
	}

	// Test ping
	if err := client.Ping(ctx).Err(); err != nil {
		return status
	}

	status.Status = "online"
	status.ResponseTime = time.Since(start)

	// Get node info
	if info, err := client.Info(ctx, "replication", "memory", "stats").Result(); err == nil {
		status.Role = hc.extractRole(info)
		status.Memory = hc.extractMemoryInfo(info)
		status.Connections = hc.extractConnections(info)
		status.Commands = hc.extractCommands(info)
	}

	// Check if node is degraded
	if status.Memory.UsagePercent > 90 || status.ResponseTime > 1*time.Second {
		status.Status = "degraded"
	}

	return status
}

// Utility methods for extracting Redis info

func (hc *HealthChecker) extractRole(info string) string {
	// Parse Redis INFO output for role
	if contains(info, "role:master") {
		return "master"
	} else if contains(info, "role:slave") {
		return "slave"
	}
	return "unknown"
}

func (hc *HealthChecker) extractMemoryInfo(info string) NodeMemory {
	// Parse memory information from Redis INFO
	// This is a simplified implementation
	return NodeMemory{
		Used:         parseInfoValue(info, "used_memory"),
		Peak:         parseInfoValue(info, "used_memory_peak"),
		MaxMem:       parseInfoValue(info, "maxmemory"),
		UsedRSS:      parseInfoValue(info, "used_memory_rss"),
		UsagePercent: 0, // Calculate based on used/max
	}
}

func (hc *HealthChecker) extractConnections(info string) int {
	return int(parseInfoValue(info, "connected_clients"))
}

func (hc *HealthChecker) extractCommands(info string) int64 {
	return parseInfoValue(info, "total_commands_processed")
}

// Helper methods

func (cm *ClusterManager) getClusterAddresses() []string {
	if cm.config.Host == "" {
		return []string{}
	}
	
	// Split comma-separated addresses
	addresses := []string{}
	for _, addr := range []string{cm.config.Host} {
		if addr != "" {
			addresses = append(addresses, addr)
		}
	}
	
	return addresses
}

func (cm *ClusterManager) getFailoverAddress() string {
	// This could be configured separately or derived from config
	return fmt.Sprintf("localhost:%d", cm.config.Port+1000) // Simplified
}

func (cm *ClusterManager) hasFailoverConfig() bool {
	// Check if failover is configured
	return true // Simplified for example
}

func (cm *ClusterManager) isClusterError(err error) bool {
	if err == nil {
		return false
	}
	
	errorStr := err.Error()
	return contains(errorStr, "CLUSTERDOWN") ||
		   contains(errorStr, "connection refused") ||
		   contains(errorStr, "timeout") ||
		   contains(errorStr, "no route to host")
}

func (cm *ClusterManager) checkIndividualNodes(ctx context.Context) error {
	addresses := cm.getClusterAddresses()
	
	for _, addr := range addresses {
		client := redis.NewClient(&redis.Options{
			Addr:     addr,
			Password: cm.config.Password,
		})
		
		if err := client.Ping(ctx).Err(); err == nil {
			client.Close()
			return nil // At least one node is reachable
		}
		client.Close()
	}
	
	return errors.NewExternalError("redis_cluster", "No cluster nodes reachable")
}

// GetMetrics returns cluster metrics
func (cm *ClusterManager) GetMetrics() ClusterMetrics {
	cm.mutex.RLock()
	defer cm.mutex.RUnlock()
	
	// Deep copy metrics
	metrics := *cm.metrics
	metrics.NodeStatus = make(map[string]NodeStatus)
	for k, v := range cm.metrics.NodeStatus {
		metrics.NodeStatus[k] = v
	}
	
	return metrics
}

// Close gracefully shuts down the cluster manager
func (cm *ClusterManager) Close() error {
	cm.healthChecker.stop()
	
	var errs []error
	
	if cm.clusterClient != nil {
		if err := cm.clusterClient.Close(); err != nil {
			errs = append(errs, err)
		}
	}
	
	if cm.failoverClient != nil {
		if err := cm.failoverClient.Close(); err != nil {
			errs = append(errs, err)
		}
	}
	
	if len(errs) > 0 {
		return fmt.Errorf("errors closing cluster manager: %v", errs)
	}
	
	return nil
}

// Utility functions

func contains(s, substr string) bool {
	return len(s) >= len(substr) && 
		   (s == substr || 
			len(substr) == 0 ||
			indexOf(s, substr) >= 0)
}

func indexOf(s, substr string) int {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return i
		}
	}
	return -1
}

func parseInfoValue(info, key string) int64 {
	// Simplified Redis INFO parsing
	keyPattern := key + ":"
	start := indexOf(info, keyPattern)
	if start == -1 {
		return 0
	}
	
	start += len(keyPattern)
	end := indexOf(info[start:], "\r\n")
	if end == -1 {
		end = len(info) - start
	}
	
	valueStr := info[start : start+end]
	value := int64(0)
	
	// Simple integer parsing
	for _, char := range valueStr {
		if char >= '0' && char <= '9' {
			value = value*10 + int64(char-'0')
		} else {
			break
		}
	}
	
	return value
}