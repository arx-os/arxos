package main

import (
	"github.com/arxos/arxos/cmd/commands"
)

var (
	Version   = "1.0.0"
	BuildDate = "2024-08-23"
	GitCommit = "unknown"
)

func main() {
	// Set version info
	commands.SetVersion(Version, BuildDate, GitCommit)
	
	// Execute root command
	commands.Execute()
}