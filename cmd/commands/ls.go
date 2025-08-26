package commands

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
)

var LsCmd = &cobra.Command{
	Use:   "ls [path]",
	Short: "List contents of a virtual directory in the building workspace",
	Long: `List the contents of a virtual directory within the building filesystem.

Examples:
  arx ls                    # List current directory contents
  arx ls /                 # List building root contents
  arx ls systems           # List systems directory contents
  arx ls -l                # Long format with details
  arx ls -t                # Show by type (floors, systems, etc.)
  arx ls --tree            # Tree view of current directory`,
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

		idx, err := GetOrBuildIndex(root, session.BuildingID)
		if err != nil {
			return fmt.Errorf("index error: %w", err)
		}
		if !idx.Exists(targetPath) {
			return fmt.Errorf("path does not exist: %s", targetPath)
		}

		entries := idx.List(targetPath)

		// Apply display options
		longFormat, _ := cmd.Flags().GetBool("long")
		showTypes, _ := cmd.Flags().GetBool("types")
		treeView, _ := cmd.Flags().GetBool("tree")

		if treeView {
			// Build a shallow tree (depth 2) for ls --tree
			tree := idx.BuildTree(targetPath, 2)
			displayTreeViewFromIndex(tree)
			return nil
		}

		if longFormat {
			displayLongFormatFromIndex(targetPath, entries)
			return nil
		}

		if showTypes {
			displayByTypeFromIndex(targetPath, entries)
			return nil
		}

		displaySimpleFromIndex(targetPath, entries)
		return nil
	},
}

func init() {
	LsCmd.Flags().BoolP("long", "l", false, "Use long listing format")
	LsCmd.Flags().BoolP("types", "t", false, "Group by type")
	LsCmd.Flags().Bool("tree", false, "Display in tree format")
}

func displaySimpleFromIndex(virtualPath string, contents []DirectoryEntry) {
	if virtualPath != "/" {
		fmt.Printf("Contents of %s:\n", virtualPath)
	}
	for _, entry := range contents {
		if entry.IsDir {
			fmt.Printf("%s/\n", entry.Name)
		} else {
			fmt.Printf("%s\n", entry.Name)
		}
	}
}

func displayLongFormatFromIndex(virtualPath string, contents []DirectoryEntry) {
	if virtualPath != "/" {
		fmt.Printf("Contents of %s:\n", virtualPath)
	}
	fmt.Printf("%-20s %-15s %-30s\n", "NAME", "TYPE", "PATH")
	fmt.Println(strings.Repeat("-", 65))
	for _, entry := range contents {
		entryType := entry.Type
		if entry.IsDir {
			entryType += "/"
		}
		fmt.Printf("%-20s %-15s %-30s\n", entry.Name, entryType, entry.Path)
	}
}

func displayByTypeFromIndex(virtualPath string, contents []DirectoryEntry) {
	if virtualPath != "/" {
		fmt.Printf("Contents of %s:\n", virtualPath)
	}
	typeGroups := make(map[string][]DirectoryEntry)
	for _, entry := range contents {
		typeGroups[entry.Type] = append(typeGroups[entry.Type], entry)
	}
	for entryType, entries := range typeGroups {
		fmt.Printf("\n%s:\n", strings.ToUpper(entryType))
		for _, entry := range entries {
			if entry.IsDir {
				fmt.Printf("  %s/\n", entry.Name)
			} else {
				fmt.Printf("  %s\n", entry.Name)
			}
		}
	}
}

func displayTreeViewFromIndex(root TreeEntry) {
	// Print only one level deep for ls --tree
	if root.IsDir {
		fmt.Printf("%s/\n", root.Name)
	} else {
		fmt.Println(root.Name)
	}
	for i, child := range root.Children {
		isLast := i == len(root.Children)-1
		prefix := "├── "
		if isLast {
			prefix = "└── "
		}
		if child.IsDir {
			fmt.Printf("%s%s/\n", prefix, child.Name)
		} else {
			fmt.Printf("%s%s\n", prefix, child.Name)
		}
	}
}
