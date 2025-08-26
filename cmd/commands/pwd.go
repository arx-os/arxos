package commands

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var PwdCmd = &cobra.Command{
	Use:   "pwd",
	Short: "Print the current virtual path in the building workspace",
	RunE: func(cmd *cobra.Command, args []string) error {
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("getwd: %w", err)
		}
		root, err := findBuildingRoot(cwd)
		if err != nil {
			return err
		}
		s, err := loadSession(root)
		if err != nil {
			return err
		}
		fmt.Printf("building:%s%s\n", s.BuildingID, s.CWD)
		return nil
	},
}
