package commands

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var CdCmd = &cobra.Command{
	Use:   "cd [path]",
	Short: "Change the virtual working directory in the building workspace",
	Long: `Change the current working directory within the virtual building filesystem.

Examples:
  arx cd                    # Show current directory
  arx cd /                 # Go to building root
  arx cd systems           # Go to systems directory
  arx cd ../floors/2       # Go up one level, then to floors/2
  arx cd ~                 # Go to building root (same as /)
  arx cd -                 # Go to previous directory (not yet implemented)`,
	Args: cobra.MaximumNArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("getwd: %w", err)
		}

		root, err := findBuildingRoot(cwd)
		if err != nil {
			return err
		}

		session, err := loadSession(root)
		if err != nil {
			return err
		}

		// If no path provided, just show current directory
		if len(args) == 0 {
			fmt.Printf("building:%s%s\n", session.BuildingID, session.CWD)
			return nil
		}

		// Resolve the target path
		resolver := NewPathResolver(root)
		targetPath, err := resolver.ResolvePath(session.CWD, args[0])
		if err != nil {
			return fmt.Errorf("invalid path: %w", err)
		}

		// Validate the resolved path format
		if err := resolver.ValidatePath(targetPath); err != nil {
			return fmt.Errorf("invalid path: %w", err)
		}

		// Ensure the target exists according to the index
		idx, err := GetOrBuildIndex(root, session.BuildingID)
		if err != nil {
			return fmt.Errorf("index error: %w", err)
		}
		if !idx.Exists(targetPath) {
			return fmt.Errorf("path does not exist: %s", targetPath)
		}

		// Update session with new CWD
		session.PreviousCWD = session.CWD
		session.CWD = targetPath

		// Save the updated session
		if err := saveSession(root, session); err != nil {
			return fmt.Errorf("failed to save session: %w", err)
		}

		fmt.Printf("Changed directory to: building:%s%s\n", session.BuildingID, session.CWD)
		return nil
	},
}
