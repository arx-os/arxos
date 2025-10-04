package types

import (
	"context"
	"time"
)

// Server represents the HTTP server configuration
type Server struct {
	Port         string
	Host         string
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
	IdleTimeout  time.Duration
	Context      context.Context
}

// NewServer creates a new server configuration
func NewServer(port, host string) *Server {
	return &Server{
		Port:         port,
		Host:         host,
		ReadTimeout:  time.Second * 30,
		WriteTimeout: time.Second * 30,
		IdleTimeout:  time.Second * 60,
		Context:      context.Background(),
	}
}

// Note: BaseHandler moved to internal/interfaces/http/handlers/base.go for Clean Architecture compliance
