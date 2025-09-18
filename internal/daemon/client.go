package daemon

import (
	"bufio"
	"encoding/json"
	"fmt"
	"net"
	"time"
)

// Client communicates with the daemon
type Client struct {
	socketPath string
	timeout    time.Duration
}

// NewClient creates a new daemon client
func NewClient(socketPath string) *Client {
	if socketPath == "" {
		socketPath = "/tmp/arxos.sock"
	}

	return &Client{
		socketPath: socketPath,
		timeout:    5 * time.Second,
	}
}

// IsRunning checks if the daemon is running
func (c *Client) IsRunning() bool {
	conn, err := net.DialTimeout("unix", c.socketPath, c.timeout)
	if err != nil {
		return false
	}
	conn.Close()
	return true
}

// SendCommand sends a command to the daemon
func (c *Client) SendCommand(command string, args map[string]interface{}) (*Response, error) {
	// Connect to daemon
	conn, err := net.DialTimeout("unix", c.socketPath, c.timeout)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to daemon: %w", err)
	}
	defer conn.Close()

	// Send request
	req := Request{
		Command: command,
		Args:    args,
	}

	encoder := json.NewEncoder(conn)
	if err := encoder.Encode(req); err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}

	// Read response
	conn.SetReadDeadline(time.Now().Add(c.timeout))
	scanner := bufio.NewScanner(conn)
	if !scanner.Scan() {
		if err := scanner.Err(); err != nil {
			return nil, fmt.Errorf("failed to read response: %w", err)
		}
		return nil, fmt.Errorf("no response from daemon")
	}

	var resp Response
	if err := json.Unmarshal(scanner.Bytes(), &resp); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &resp, nil
}

// Status gets daemon status
func (c *Client) Status() (*Response, error) {
	return c.SendCommand("status", nil)
}

// Stats gets daemon statistics
func (c *Client) Stats() (*Response, error) {
	return c.SendCommand("stats", nil)
}

// Reload reloads daemon configuration
func (c *Client) Reload() (*Response, error) {
	return c.SendCommand("reload", nil)
}

// AddWatch adds a directory to watch
func (c *Client) AddWatch(directory string) (*Response, error) {
	return c.SendCommand("add-watch", map[string]interface{}{
		"directory": directory,
	})
}

// RemoveWatch removes a directory from watch
func (c *Client) RemoveWatch(directory string) (*Response, error) {
	return c.SendCommand("remove-watch", map[string]interface{}{
		"directory": directory,
	})
}

// Import imports a file
func (c *Client) Import(file string) (*Response, error) {
	return c.SendCommand("import", map[string]interface{}{
		"file": file,
	})
}

// Sync triggers a sync operation
func (c *Client) Sync() (*Response, error) {
	return c.SendCommand("sync", nil)
}

// QueueStatus gets queue status
func (c *Client) QueueStatus() (*Response, error) {
	return c.SendCommand("queue-status", nil)
}

// Ping checks if daemon is responsive
func (c *Client) Ping() (*Response, error) {
	return c.SendCommand("ping", nil)
}

// Shutdown shuts down the daemon
func (c *Client) Shutdown() (*Response, error) {
	return c.SendCommand("shutdown", nil)
}
