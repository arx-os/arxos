package commands

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var TreeCmd = &cobra.Command{
	Use:   "tree [path]",
	Short: "Display a tree view of the building structure",
	Long: `Display a hierarchical tree view of the building structure using ASCII art.

Examples:
  arx tree                    # Show tree from current directory
  arx tree /                 # Show complete building tree
  arx tree systems           # Show tree from systems directory
  arx tree --depth 2         # Limit tree depth to 2 levels
  arx tree --compact         # Use compact tree symbols`,
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

		// Determine target path (default to current directory)
		targetPath := session.CWD
		if len(args) > 0 {
			resolver := NewPathResolver(root)
			resolvedPath, err := resolver.ResolvePath(session.CWD, args[0])
			if err != nil {
				return fmt.Errorf("invalid path: %w", err)
			}
			if err := resolver.ValidatePath(resolvedPath); err != nil {
				return fmt.Errorf("invalid path: %w", err)
			}
			targetPath = resolvedPath
		}

		// Get display options
		maxDepth, _ := cmd.Flags().GetInt("depth")
		compact, _ := cmd.Flags().GetBool("compact")

		idx, err := GetOrBuildIndex(root, session.BuildingID)
		if err != nil {
			return fmt.Errorf("index error: %w", err)
		}
		if !idx.Exists(targetPath) {
			return fmt.Errorf("path does not exist: %s", targetPath)
		}

		// Build the tree from the index
		depth := maxDepth
		if depth < 0 {
			depth = 0
		}
		treeData := idx.BuildTree(targetPath, depth)

		displayTreeFromIndex(treeData, compact, "")
		return nil
	},
}

func init() {
	TreeCmd.Flags().IntP("depth", "d", 0, "Maximum depth to display (0 = unlimited)")
	TreeCmd.Flags().BoolP("compact", "c", false, "Use compact tree symbols")
}

func displayTreeFromIndex(entry TreeEntry, compact bool, prefix string) {
	// Determine symbols
	line := "├── "
	space := "    "
	if compact {
		line = "├─"
		space = "  "
	}

	// Print current
	if prefix == "" {
		if entry.IsDir {
			fmt.Printf("%s/\n", entry.Name)
		} else {
			fmt.Printf("%s\n", entry.Name)
		}
	}

	// Print children
	for i, child := range entry.Children {
		isLast := i == len(entry.Children)-1
		branch := line
		if compact {
			branch = "├─"
		}
		if isLast {
			if compact {
				branch = "└─"
			} else {
				branch = "└── "
			}
		}
		if child.IsDir {
			fmt.Printf("%s%s%s/\n", prefix, branch, child.Name)
		} else {
			fmt.Printf("%s%s%s\n", prefix, branch, child.Name)
		}
		nextPrefix := prefix + space
		if !isLast && !compact {
			nextPrefix = prefix + "│   "
		}
		displayTreeFromIndex(child, compact, nextPrefix)
	}
}
