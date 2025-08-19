// Package config provides configuration management for the Arxos backend
package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/viper"
	"go.uber.org/zap"
)

// Config holds all configuration for the application
type Config struct {
	// Server configuration
	Server ServerConfig `mapstructure:"server"`
	
	// Database configuration
	Database DatabaseConfig `mapstructure:"database"`
	
	// Redis configuration
	Redis RedisConfig `mapstructure:"redis"`
	
	// JWT configuration
	JWT JWTConfig `mapstructure:"jwt"`
	
	// Logging configuration
	Logging LoggingConfig `mapstructure:"logging"`
	
	// ArxObject engine configuration
	Engine EngineConfig `mapstructure:"engine"`
	
	// Validation configuration
	Validation ValidationConfig `mapstructure:"validation"`
	
	// Performance configuration
	Performance PerformanceConfig `mapstructure:"performance"`
	
	// Security configuration
	Security SecurityConfig `mapstructure:"security"`
	
	// External services
	External ExternalConfig `mapstructure:"external"`
}

// ServerConfig contains HTTP server settings
type ServerConfig struct {
	Host         string        `mapstructure:"host"`
	Port         int           `mapstructure:"port"`
	ReadTimeout  time.Duration `mapstructure:"read_timeout"`
	WriteTimeout time.Duration `mapstructure:"write_timeout"`
	IdleTimeout  time.Duration `mapstructure:"idle_timeout"`
	TLSEnabled   bool          `mapstructure:"tls_enabled"`
	TLSCertFile  string        `mapstructure:"tls_cert_file"`
	TLSKeyFile   string        `mapstructure:"tls_key_file"`
}

// DatabaseConfig contains database connection settings
type DatabaseConfig struct {
	Host            string        `mapstructure:"host"`
	Port            int           `mapstructure:"port"`
	Username        string        `mapstructure:"username"`
	Password        string        `mapstructure:"password"`
	Database        string        `mapstructure:"database"`
	SSLMode         string        `mapstructure:"ssl_mode"`
	MaxOpenConns    int           `mapstructure:"max_open_conns"`
	MaxIdleConns    int           `mapstructure:"max_idle_conns"`
	ConnMaxLifetime time.Duration `mapstructure:"conn_max_lifetime"`
	ConnMaxIdleTime time.Duration `mapstructure:"conn_max_idle_time"`
	MigrationsPath  string        `mapstructure:"migrations_path"`
}

// RedisConfig contains Redis connection settings
type RedisConfig struct {
	Host               string        `mapstructure:"host"`
	Port               int           `mapstructure:"port"`
	Password           string        `mapstructure:"password"`
	Database           int           `mapstructure:"database"`
	MaxRetries         int           `mapstructure:"max_retries"`
	MinRetryBackoff    time.Duration `mapstructure:"min_retry_backoff"`
	MaxRetryBackoff    time.Duration `mapstructure:"max_retry_backoff"`
	DialTimeout        time.Duration `mapstructure:"dial_timeout"`
	ReadTimeout        time.Duration `mapstructure:"read_timeout"`
	WriteTimeout       time.Duration `mapstructure:"write_timeout"`
	PoolSize           int           `mapstructure:"pool_size"`
	MinIdleConns       int           `mapstructure:"min_idle_conns"`
	MaxConnAge         time.Duration `mapstructure:"max_conn_age"`
	PoolTimeout        time.Duration `mapstructure:"pool_timeout"`
	IdleTimeout        time.Duration `mapstructure:"idle_timeout"`
	IdleCheckFrequency time.Duration `mapstructure:"idle_check_frequency"`
}

// JWTConfig contains JWT authentication settings
type JWTConfig struct {
	AccessSecret     string        `mapstructure:"access_secret"`
	RefreshSecret    string        `mapstructure:"refresh_secret"`
	AccessExpiry     time.Duration `mapstructure:"access_expiry"`
	RefreshExpiry    time.Duration `mapstructure:"refresh_expiry"`
	Issuer          string        `mapstructure:"issuer"`
	AllowedOrigins  []string      `mapstructure:"allowed_origins"`
	EnableBlacklist bool          `mapstructure:"enable_blacklist"`
}

// LoggingConfig contains logging settings
type LoggingConfig struct {
	Level       string `mapstructure:"level"`
	Format      string `mapstructure:"format"`
	OutputPaths []string `mapstructure:"output_paths"`
	ErrorPaths  []string `mapstructure:"error_paths"`
	Development bool     `mapstructure:"development"`
	Sampling    bool     `mapstructure:"sampling"`
}

// EngineConfig contains ArxObject engine settings
type EngineConfig struct {
	InitialCapacity int     `mapstructure:"initial_capacity"`
	SpatialIndexing bool    `mapstructure:"spatial_indexing"`
	GridResolution  float32 `mapstructure:"grid_resolution"`
	MaxObjects      int     `mapstructure:"max_objects"`
	EnableMetrics   bool    `mapstructure:"enable_metrics"`
}

// ValidationConfig contains validation system settings
type ValidationConfig struct {
	MinConfidenceThreshold     float32       `mapstructure:"min_confidence_threshold"`
	CascadeValidationEnabled   bool          `mapstructure:"cascade_validation_enabled"`
	PatternLearningEnabled     bool          `mapstructure:"pattern_learning_enabled"`
	MinSimilarObjectsForPattern int          `mapstructure:"min_similar_objects_for_pattern"`
	ValidationCacheTimeout     time.Duration `mapstructure:"validation_cache_timeout"`
	MaxValidationTasks         int           `mapstructure:"max_validation_tasks"`
	PriorityCalculationWeights map[string]float32 `mapstructure:"priority_calculation_weights"`
}

// PerformanceConfig contains performance tuning settings
type PerformanceConfig struct {
	MaxConcurrentRequests    int           `mapstructure:"max_concurrent_requests"`
	RequestTimeout           time.Duration `mapstructure:"request_timeout"`
	CacheEnabled             bool          `mapstructure:"cache_enabled"`
	CacheTimeout             time.Duration `mapstructure:"cache_timeout"`
	EnableProfiling          bool          `mapstructure:"enable_profiling"`
	MetricsEnabled           bool          `mapstructure:"metrics_enabled"`
	TracingEnabled           bool          `mapstructure:"tracing_enabled"`
	CircuitBreakerEnabled    bool          `mapstructure:"circuit_breaker_enabled"`
	RateLimitEnabled         bool          `mapstructure:"rate_limit_enabled"`
	RateLimitRequestsPerMin  int           `mapstructure:"rate_limit_requests_per_min"`
}

// SecurityConfig contains security settings
type SecurityConfig struct {
	CORSEnabled        bool     `mapstructure:"cors_enabled"`
	CORSAllowedOrigins []string `mapstructure:"cors_allowed_origins"`
	CORSAllowedMethods []string `mapstructure:"cors_allowed_methods"`
	CORSAllowedHeaders []string `mapstructure:"cors_allowed_headers"`
	CSRFEnabled        bool     `mapstructure:"csrf_enabled"`
	CSRFSecret         string   `mapstructure:"csrf_secret"`
	InputValidation    bool     `mapstructure:"input_validation"`
	SQLInjectionProtection bool `mapstructure:"sql_injection_protection"`
	XSSProtection      bool     `mapstructure:"xss_protection"`
	ContentTypeValidation bool  `mapstructure:"content_type_validation"`
}

// ExternalConfig contains external service settings
type ExternalConfig struct {
	OpenAI  OpenAIConfig  `mapstructure:"openai"`
	AWS     AWSConfig     `mapstructure:"aws"`
	Metrics MetricsConfig `mapstructure:"metrics"`
}

// OpenAIConfig contains OpenAI API settings
type OpenAIConfig struct {
	APIKey      string        `mapstructure:"api_key"`
	Model       string        `mapstructure:"model"`
	MaxTokens   int           `mapstructure:"max_tokens"`
	Temperature float32       `mapstructure:"temperature"`
	Timeout     time.Duration `mapstructure:"timeout"`
	Enabled     bool          `mapstructure:"enabled"`
}

// AWSConfig contains AWS service settings
type AWSConfig struct {
	Region          string `mapstructure:"region"`
	AccessKeyID     string `mapstructure:"access_key_id"`
	SecretAccessKey string `mapstructure:"secret_access_key"`
	S3Bucket        string `mapstructure:"s3_bucket"`
	S3Enabled       bool   `mapstructure:"s3_enabled"`
}

// MetricsConfig contains metrics collection settings
type MetricsConfig struct {
	Enabled         bool          `mapstructure:"enabled"`
	PrometheusPort  int           `mapstructure:"prometheus_port"`
	CollectionInterval time.Duration `mapstructure:"collection_interval"`
	PushGateway     string        `mapstructure:"push_gateway"`
}

// Load loads configuration from files and environment variables
func Load() (*Config, error) {
	// Set default configuration
	viper.SetDefault("server.host", "0.0.0.0")
	viper.SetDefault("server.port", 8080)
	viper.SetDefault("server.read_timeout", "30s")
	viper.SetDefault("server.write_timeout", "30s")
	viper.SetDefault("server.idle_timeout", "120s")
	viper.SetDefault("server.tls_enabled", false)
	
	viper.SetDefault("database.host", "localhost")
	viper.SetDefault("database.port", 5432)
	viper.SetDefault("database.username", "arxos")
	viper.SetDefault("database.database", "arxos")
	viper.SetDefault("database.ssl_mode", "disable")
	viper.SetDefault("database.max_open_conns", 25)
	viper.SetDefault("database.max_idle_conns", 5)
	viper.SetDefault("database.conn_max_lifetime", "300s")
	viper.SetDefault("database.conn_max_idle_time", "60s")
	viper.SetDefault("database.migrations_path", "./migrations")
	
	viper.SetDefault("redis.host", "localhost")
	viper.SetDefault("redis.port", 6379)
	viper.SetDefault("redis.database", 0)
	viper.SetDefault("redis.max_retries", 3)
	viper.SetDefault("redis.min_retry_backoff", "8ms")
	viper.SetDefault("redis.max_retry_backoff", "512ms")
	viper.SetDefault("redis.dial_timeout", "5s")
	viper.SetDefault("redis.read_timeout", "3s")
	viper.SetDefault("redis.write_timeout", "3s")
	viper.SetDefault("redis.pool_size", 10)
	viper.SetDefault("redis.min_idle_conns", 2)
	viper.SetDefault("redis.max_conn_age", "600s")
	viper.SetDefault("redis.pool_timeout", "4s")
	viper.SetDefault("redis.idle_timeout", "300s")
	viper.SetDefault("redis.idle_check_frequency", "60s")
	
	viper.SetDefault("jwt.access_expiry", "15m")
	viper.SetDefault("jwt.refresh_expiry", "168h") // 7 days
	viper.SetDefault("jwt.issuer", "arxos")
	viper.SetDefault("jwt.enable_blacklist", true)
	
	viper.SetDefault("logging.level", "info")
	viper.SetDefault("logging.format", "json")
	viper.SetDefault("logging.output_paths", []string{"stdout"})
	viper.SetDefault("logging.error_paths", []string{"stderr"})
	viper.SetDefault("logging.development", false)
	viper.SetDefault("logging.sampling", true)
	
	viper.SetDefault("engine.initial_capacity", 10000)
	viper.SetDefault("engine.spatial_indexing", true)
	viper.SetDefault("engine.grid_resolution", 1.0)
	viper.SetDefault("engine.max_objects", 1000000)
	viper.SetDefault("engine.enable_metrics", true)
	
	viper.SetDefault("validation.min_confidence_threshold", 0.6)
	viper.SetDefault("validation.cascade_validation_enabled", true)
	viper.SetDefault("validation.pattern_learning_enabled", true)
	viper.SetDefault("validation.min_similar_objects_for_pattern", 3)
	viper.SetDefault("validation.validation_cache_timeout", "5m")
	viper.SetDefault("validation.max_validation_tasks", 1000)
	
	viper.SetDefault("performance.max_concurrent_requests", 1000)
	viper.SetDefault("performance.request_timeout", "30s")
	viper.SetDefault("performance.cache_enabled", true)
	viper.SetDefault("performance.cache_timeout", "5m")
	viper.SetDefault("performance.enable_profiling", false)
	viper.SetDefault("performance.metrics_enabled", true)
	viper.SetDefault("performance.tracing_enabled", false)
	viper.SetDefault("performance.circuit_breaker_enabled", true)
	viper.SetDefault("performance.rate_limit_enabled", true)
	viper.SetDefault("performance.rate_limit_requests_per_min", 1000)
	
	viper.SetDefault("security.cors_enabled", true)
	viper.SetDefault("security.cors_allowed_origins", []string{"*"})
	viper.SetDefault("security.cors_allowed_methods", []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"})
	viper.SetDefault("security.cors_allowed_headers", []string{"*"})
	viper.SetDefault("security.csrf_enabled", false)
	viper.SetDefault("security.input_validation", true)
	viper.SetDefault("security.sql_injection_protection", true)
	viper.SetDefault("security.xss_protection", true)
	viper.SetDefault("security.content_type_validation", true)
	
	viper.SetDefault("external.openai.model", "gpt-4-vision-preview")
	viper.SetDefault("external.openai.max_tokens", 4096)
	viper.SetDefault("external.openai.temperature", 0.1)
	viper.SetDefault("external.openai.timeout", "30s")
	viper.SetDefault("external.openai.enabled", false)
	
	viper.SetDefault("external.aws.region", "us-east-1")
	viper.SetDefault("external.aws.s3_enabled", false)
	
	viper.SetDefault("external.metrics.enabled", true)
	viper.SetDefault("external.metrics.prometheus_port", 9090)
	viper.SetDefault("external.metrics.collection_interval", "15s")
	
	// Configure viper
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")
	viper.AddConfigPath("./config")
	viper.AddConfigPath("/etc/arxos")
	
	// Enable environment variable binding
	viper.AutomaticEnv()
	viper.SetEnvPrefix("ARXOS")
	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	
	// Read configuration file
	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			// Config file not found; use defaults and environment variables
		} else {
			return nil, fmt.Errorf("error reading config file: %w", err)
		}
	}
	
	// Unmarshal configuration
	var config Config
	if err := viper.Unmarshal(&config); err != nil {
		return nil, fmt.Errorf("error unmarshaling config: %w", err)
	}
	
	// Override with environment variables
	if err := overrideWithEnv(&config); err != nil {
		return nil, fmt.Errorf("error overriding with environment variables: %w", err)
	}
	
	// Validate configuration
	if err := validate(&config); err != nil {
		return nil, fmt.Errorf("config validation failed: %w", err)
	}
	
	return &config, nil
}

// overrideWithEnv overrides configuration with environment variables
func overrideWithEnv(config *Config) error {
	// Database password from environment (sensitive)
	if dbPassword := os.Getenv("ARXOS_DATABASE_PASSWORD"); dbPassword != "" {
		config.Database.Password = dbPassword
	}
	
	// Redis password from environment (sensitive)
	if redisPassword := os.Getenv("ARXOS_REDIS_PASSWORD"); redisPassword != "" {
		config.Redis.Password = redisPassword
	}
	
	// JWT secrets from environment (sensitive)
	if jwtAccessSecret := os.Getenv("ARXOS_JWT_ACCESS_SECRET"); jwtAccessSecret != "" {
		config.JWT.AccessSecret = jwtAccessSecret
	}
	if jwtRefreshSecret := os.Getenv("ARXOS_JWT_REFRESH_SECRET"); jwtRefreshSecret != "" {
		config.JWT.RefreshSecret = jwtRefreshSecret
	}
	
	// OpenAI API key from environment (sensitive)
	if openaiKey := os.Getenv("ARXOS_EXTERNAL_OPENAI_API_KEY"); openaiKey != "" {
		config.External.OpenAI.APIKey = openaiKey
		config.External.OpenAI.Enabled = true
	}
	
	// AWS credentials from environment (sensitive)
	if awsKeyID := os.Getenv("ARXOS_EXTERNAL_AWS_ACCESS_KEY_ID"); awsKeyID != "" {
		config.External.AWS.AccessKeyID = awsKeyID
	}
	if awsSecretKey := os.Getenv("ARXOS_EXTERNAL_AWS_SECRET_ACCESS_KEY"); awsSecretKey != "" {
		config.External.AWS.SecretAccessKey = awsSecretKey
		config.External.AWS.S3Enabled = true
	}
	
	// Environment-specific overrides
	if env := os.Getenv("ARXOS_ENVIRONMENT"); env != "" {
		switch env {
		case "development":
			config.Logging.Development = true
			config.Logging.Level = "debug"
			config.Performance.EnableProfiling = true
			config.Security.CORSAllowedOrigins = []string{"*"}
		case "production":
			config.Logging.Development = false
			config.Logging.Level = "info"
			config.Performance.EnableProfiling = false
			config.Security.InputValidation = true
			config.Security.SQLInjectionProtection = true
		case "testing":
			config.Logging.Level = "warn"
			config.Performance.MetricsEnabled = false
		}
	}
	
	return nil
}

// validate validates the configuration
func validate(config *Config) error {
	// Server validation
	if config.Server.Port < 1 || config.Server.Port > 65535 {
		return fmt.Errorf("invalid server port: %d", config.Server.Port)
	}
	
	// Database validation
	if config.Database.Host == "" {
		return fmt.Errorf("database host is required")
	}
	if config.Database.Database == "" {
		return fmt.Errorf("database name is required")
	}
	if config.Database.MaxOpenConns < 1 {
		return fmt.Errorf("database max_open_conns must be at least 1")
	}
	
	// JWT validation
	if config.JWT.AccessSecret == "" {
		return fmt.Errorf("JWT access secret is required")
	}
	if len(config.JWT.AccessSecret) < 32 {
		return fmt.Errorf("JWT access secret must be at least 32 characters")
	}
	if config.JWT.RefreshSecret == "" {
		return fmt.Errorf("JWT refresh secret is required")
	}
	if len(config.JWT.RefreshSecret) < 32 {
		return fmt.Errorf("JWT refresh secret must be at least 32 characters")
	}
	
	// Validation configuration validation
	if config.Validation.MinConfidenceThreshold < 0 || config.Validation.MinConfidenceThreshold > 1 {
		return fmt.Errorf("validation min_confidence_threshold must be between 0 and 1")
	}
	if config.Validation.MinSimilarObjectsForPattern < 1 {
		return fmt.Errorf("validation min_similar_objects_for_pattern must be at least 1")
	}
	
	// Performance validation
	if config.Performance.MaxConcurrentRequests < 1 {
		return fmt.Errorf("performance max_concurrent_requests must be at least 1")
	}
	if config.Performance.RateLimitRequestsPerMin < 1 {
		return fmt.Errorf("performance rate_limit_requests_per_min must be at least 1")
	}
	
	return nil
}

// GetDatabaseDSN returns the database connection string
func (c *Config) GetDatabaseDSN() string {
	return fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		c.Database.Host,
		c.Database.Port,
		c.Database.Username,
		c.Database.Password,
		c.Database.Database,
		c.Database.SSLMode,
	)
}

// GetRedisAddress returns the Redis connection address
func (c *Config) GetRedisAddress() string {
	return fmt.Sprintf("%s:%d", c.Redis.Host, c.Redis.Port)
}

// GetServerAddress returns the server listen address
func (c *Config) GetServerAddress() string {
	return fmt.Sprintf("%s:%d", c.Server.Host, c.Server.Port)
}

// IsDevelopment returns true if running in development mode
func (c *Config) IsDevelopment() bool {
	return c.Logging.Development
}

// IsProduction returns true if running in production mode
func (c *Config) IsProduction() bool {
	return !c.Logging.Development && c.Security.InputValidation
}

// CreateLogger creates a zap logger with the configured settings
func (c *Config) CreateLogger() (*zap.Logger, error) {
	var config zap.Config
	
	if c.Logging.Development {
		config = zap.NewDevelopmentConfig()
	} else {
		config = zap.NewProductionConfig()
	}
	
	// Set log level
	level, err := zap.ParseAtomicLevel(c.Logging.Level)
	if err != nil {
		return nil, fmt.Errorf("invalid log level %s: %w", c.Logging.Level, err)
	}
	config.Level = level
	
	// Set output paths
	config.OutputPaths = c.Logging.OutputPaths
	config.ErrorOutputPaths = c.Logging.ErrorPaths
	
	// Set encoding
	if c.Logging.Format == "console" {
		config.Encoding = "console"
	} else {
		config.Encoding = "json"
	}
	
	// Disable sampling if configured
	if !c.Logging.Sampling {
		config.Sampling = nil
	}
	
	return config.Build()
}

// GetEnvAsString gets environment variable as string with default
func GetEnvAsString(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// GetEnvAsInt gets environment variable as int with default
func GetEnvAsInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

// GetEnvAsBool gets environment variable as bool with default
func GetEnvAsBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
	}
	return defaultValue
}

// GetEnvAsDuration gets environment variable as duration with default
func GetEnvAsDuration(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if duration, err := time.ParseDuration(value); err == nil {
			return duration
		}
	}
	return defaultValue
}