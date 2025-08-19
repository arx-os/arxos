package config

import (
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/joho/godotenv"
)

// Config holds all application configuration
type Config struct {
	Server   ServerConfig
	Database DatabaseConfig
	Redis    RedisConfig
	Logging  LoggingConfig
	Security SecurityConfig
	Tile     TileConfig
	PDF      PDFConfig
}

// ServerConfig contains HTTP server settings
type ServerConfig struct {
	Port              string
	Host              string
	ReadTimeout       time.Duration
	WriteTimeout      time.Duration
	IdleTimeout       time.Duration
	MaxHeaderBytes    int
	EnableCORS        bool
	AllowedOrigins    []string
	EnableCompression bool
}

// DatabaseConfig contains database connection settings
type DatabaseConfig struct {
	Host            string
	Port            int
	User            string
	Password        string
	DBName          string
	SSLMode         string
	MaxOpenConns    int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration
	ConnMaxIdleTime time.Duration
	EnableLogging   bool
}

// RedisConfig contains Redis cache settings
type RedisConfig struct {
	Host        string
	Port        int
	Password    string
	DB          int
	MaxRetries  int
	PoolSize    int
	MinIdleConns int
	MaxConnAge  time.Duration
	Enabled     bool
}

// LoggingConfig contains logging settings
type LoggingConfig struct {
	Level      string // debug, info, warn, error
	Format     string // json, text
	Output     string // stdout, file
	FilePath   string
	MaxSize    int  // megabytes
	MaxBackups int
	MaxAge     int  // days
	Compress   bool
}

// SecurityConfig contains security settings
type SecurityConfig struct {
	JWTSecret           string
	JWTExpiration       time.Duration
	BCryptCost          int
	RateLimitRequests   int
	RateLimitWindow     time.Duration
	EnableHTTPS         bool
	TLSCertPath         string
	TLSKeyPath          string
	CSRFToken           string
	SessionTimeout      time.Duration
}

// TileConfig contains tile service settings
type TileConfig struct {
	CacheEnabled   bool
	CacheTTL       time.Duration
	CacheMaxSize   int
	MaxTilesPerReq int
	TileTimeout    time.Duration
}

// PDFConfig contains PDF processing settings
type PDFConfig struct {
	UploadDir       string
	MaxFileSize     int64 // bytes
	AllowedTypes    []string
	ProcessTimeout  time.Duration
	EnableOCR       bool
	ConfidenceThreshold float32
}

// Load loads configuration from environment variables
func Load() (*Config, error) {
	// Load .env file if it exists
	godotenv.Load()

	cfg := &Config{
		Server: ServerConfig{
			Port:              getEnv("SERVER_PORT", "8080"),
			Host:              getEnv("SERVER_HOST", "localhost"),
			ReadTimeout:       getDurationEnv("SERVER_READ_TIMEOUT", 15*time.Second),
			WriteTimeout:      getDurationEnv("SERVER_WRITE_TIMEOUT", 15*time.Second),
			IdleTimeout:       getDurationEnv("SERVER_IDLE_TIMEOUT", 60*time.Second),
			MaxHeaderBytes:    getIntEnv("SERVER_MAX_HEADER_BYTES", 1<<20), // 1MB
			EnableCORS:        getBoolEnv("SERVER_ENABLE_CORS", true),
			AllowedOrigins:    []string{"*"}, // In production, specify actual origins
			EnableCompression: getBoolEnv("SERVER_ENABLE_COMPRESSION", true),
		},
		Database: DatabaseConfig{
			Host:            getEnv("DB_HOST", "localhost"),
			Port:            getIntEnv("DB_PORT", 5432),
			User:            getEnv("DB_USER", "joelpate"),
			Password:        getEnv("DB_PASSWORD", ""),
			DBName:          getEnv("DB_NAME", "arxos_db_pg17"),
			SSLMode:         getEnv("DB_SSLMODE", "disable"),
			MaxOpenConns:    getIntEnv("DB_MAX_OPEN_CONNS", 25),
			MaxIdleConns:    getIntEnv("DB_MAX_IDLE_CONNS", 10),
			ConnMaxLifetime: getDurationEnv("DB_CONN_MAX_LIFETIME", 5*time.Minute),
			ConnMaxIdleTime: getDurationEnv("DB_CONN_MAX_IDLE_TIME", 5*time.Minute),
			EnableLogging:   getBoolEnv("DB_ENABLE_LOGGING", false),
		},
		Redis: RedisConfig{
			Host:         getEnv("REDIS_HOST", "localhost"),
			Port:         getIntEnv("REDIS_PORT", 6379),
			Password:     getEnv("REDIS_PASSWORD", ""),
			DB:           getIntEnv("REDIS_DB", 0),
			MaxRetries:   getIntEnv("REDIS_MAX_RETRIES", 3),
			PoolSize:     getIntEnv("REDIS_POOL_SIZE", 10),
			MinIdleConns: getIntEnv("REDIS_MIN_IDLE_CONNS", 5),
			MaxConnAge:   getDurationEnv("REDIS_MAX_CONN_AGE", 0),
			Enabled:      getBoolEnv("REDIS_ENABLED", false),
		},
		Logging: LoggingConfig{
			Level:      getEnv("LOG_LEVEL", "info"),
			Format:     getEnv("LOG_FORMAT", "json"),
			Output:     getEnv("LOG_OUTPUT", "stdout"),
			FilePath:   getEnv("LOG_FILE_PATH", "logs/arxos.log"),
			MaxSize:    getIntEnv("LOG_MAX_SIZE", 100),      // 100MB
			MaxBackups: getIntEnv("LOG_MAX_BACKUPS", 5),
			MaxAge:     getIntEnv("LOG_MAX_AGE", 30),        // 30 days
			Compress:   getBoolEnv("LOG_COMPRESS", true),
		},
		Security: SecurityConfig{
			JWTSecret:           getEnv("JWT_SECRET", generateDefaultSecret()),
			JWTExpiration:       getDurationEnv("JWT_EXPIRATION", 24*time.Hour),
			BCryptCost:          getIntEnv("BCRYPT_COST", 10),
			RateLimitRequests:   getIntEnv("RATE_LIMIT_REQUESTS", 100),
			RateLimitWindow:     getDurationEnv("RATE_LIMIT_WINDOW", 1*time.Minute),
			EnableHTTPS:         getBoolEnv("ENABLE_HTTPS", false),
			TLSCertPath:         getEnv("TLS_CERT_PATH", ""),
			TLSKeyPath:          getEnv("TLS_KEY_PATH", ""),
			CSRFToken:           getEnv("CSRF_TOKEN", generateDefaultSecret()),
			SessionTimeout:      getDurationEnv("SESSION_TIMEOUT", 24*time.Hour),
		},
		Tile: TileConfig{
			CacheEnabled:   getBoolEnv("TILE_CACHE_ENABLED", true),
			CacheTTL:       getDurationEnv("TILE_CACHE_TTL", 5*time.Minute),
			CacheMaxSize:   getIntEnv("TILE_CACHE_MAX_SIZE", 1000),
			MaxTilesPerReq: getIntEnv("TILE_MAX_PER_REQUEST", 100),
			TileTimeout:    getDurationEnv("TILE_TIMEOUT", 10*time.Second),
		},
		PDF: PDFConfig{
			UploadDir:           getEnv("PDF_UPLOAD_DIR", "./uploads"),
			MaxFileSize:         getInt64Env("PDF_MAX_FILE_SIZE", 100<<20), // 100MB
			AllowedTypes:        []string{"application/pdf"},
			ProcessTimeout:      getDurationEnv("PDF_PROCESS_TIMEOUT", 5*time.Minute),
			EnableOCR:           getBoolEnv("PDF_ENABLE_OCR", false),
			ConfidenceThreshold: getFloat32Env("PDF_CONFIDENCE_THRESHOLD", 0.5),
		},
	}

	return cfg, nil
}

// GetDatabaseURL returns the formatted database connection string
func (c *Config) GetDatabaseURL() string {
	if c.Database.Password == "" {
		return fmt.Sprintf("postgres://%s@%s:%d/%s?sslmode=%s",
			c.Database.User,
			c.Database.Host,
			c.Database.Port,
			c.Database.DBName,
			c.Database.SSLMode,
		)
	}
	return fmt.Sprintf("postgres://%s:%s@%s:%d/%s?sslmode=%s",
		c.Database.User,
		c.Database.Password,
		c.Database.Host,
		c.Database.Port,
		c.Database.DBName,
		c.Database.SSLMode,
	)
}

// Helper functions

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getIntEnv(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intVal, err := strconv.Atoi(value); err == nil {
			return intVal
		}
	}
	return defaultValue
}

func getInt64Env(key string, defaultValue int64) int64 {
	if value := os.Getenv(key); value != "" {
		if intVal, err := strconv.ParseInt(value, 10, 64); err == nil {
			return intVal
		}
	}
	return defaultValue
}

func getFloat32Env(key string, defaultValue float32) float32 {
	if value := os.Getenv(key); value != "" {
		if floatVal, err := strconv.ParseFloat(value, 32); err == nil {
			return float32(floatVal)
		}
	}
	return defaultValue
}

func getBoolEnv(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolVal, err := strconv.ParseBool(value); err == nil {
			return boolVal
		}
	}
	return defaultValue
}

func getDurationEnv(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if duration, err := time.ParseDuration(value); err == nil {
			return duration
		}
	}
	return defaultValue
}

func generateDefaultSecret() string {
	// In production, this should be a secure random string
	return "arxos-default-secret-change-in-production"
}

// Validate checks if the configuration is valid
func (c *Config) Validate() error {
	if c.Server.Port == "" {
		return fmt.Errorf("server port is required")
	}

	if c.Database.Host == "" || c.Database.DBName == "" {
		return fmt.Errorf("database host and name are required")
	}

	if c.Security.EnableHTTPS && (c.Security.TLSCertPath == "" || c.Security.TLSKeyPath == "") {
		return fmt.Errorf("TLS cert and key paths are required when HTTPS is enabled")
	}

	if c.PDF.MaxFileSize <= 0 {
		return fmt.Errorf("PDF max file size must be positive")
	}

	return nil
}