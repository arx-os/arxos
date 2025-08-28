package store

import (
	"github.com/spf13/cobra"
)

// StoreCmd provides store operations
var StoreCmd = &cobra.Command{
	Use:   "store",
	Short: "Store operations (temporarily disabled)",
	Long:  "Store operations are temporarily disabled during module refactoring",
	RunE: func(cmd *cobra.Command, args []string) error {
		return nil
	},
}