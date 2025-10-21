package versioncontrol

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/fatih/color"
	"github.com/spf13/cobra"
)

// VersionServiceProvider provides access to version control services
type VersionServiceProvider interface {
	GetSnapshotService() SnapshotService
	GetDiffService() DiffService
	GetRollbackService() RollbackService
	GetVersionService() VersionService
	GetBuildingID() string // Current building context
}

// Service interfaces (to avoid circular dependencies)
type SnapshotService interface {
	CaptureSnapshot(ctx context.Context, repoID string) (*building.Snapshot, error)
	ListSnapshots(ctx context.Context, repoID string) ([]*building.Snapshot, error)
	GetLatestSnapshot(ctx context.Context, repoID string) (*building.Snapshot, error)
}

type DiffService interface {
	DiffVersions(ctx context.Context, fromVersion, toVersion *building.Version) (*building.DiffResult, error)
}

type RollbackService interface {
	Rollback(ctx context.Context, buildingID string, targetVersion *building.Version, opts *RollbackOptions) (*RollbackResult, error)
}

type VersionService interface {
	CreateVersion(ctx context.Context, repoID string, message string) (*building.Version, error)
	GetVersion(ctx context.Context, repoID string, versionTag string) (*building.Version, error)
	ListVersions(ctx context.Context, repoID string) ([]building.Version, error)
}

// Rollback types (re-declare to avoid import cycles)
type RollbackOptions struct {
	CreateVersion bool
	Message       string
	ValidateAfter bool
	DryRun        bool
}

type RollbackResult struct {
	Success          bool
	TargetVersion    string
	PreviousVersion  string
	Changes          *RollbackChanges
	ValidationResult *ValidationResult
	Duration         time.Duration
	Error            string
}

type RollbackChanges struct {
	BuildingRestored  bool
	FloorsRestored    int
	RoomsRestored     int
	EquipmentRestored int
	FilesRestored     int
}

type ValidationResult struct {
	Valid    bool
	Checks   []string
	Warnings []string
	Errors   []string
}

// Color output helpers
var (
	success   = color.New(color.FgGreen, color.Bold).SprintFunc()
	info      = color.New(color.FgCyan).SprintFunc()
	warning   = color.New(color.FgYellow).SprintFunc()
	errorMsg  = color.New(color.FgRed, color.Bold).SprintFunc()
	bold      = color.New(color.Bold).SprintFunc()
	dim       = color.New(color.Faint).SprintFunc()
	highlight = color.New(color.FgMagenta, color.Bold).SprintFunc()
)

// CreateRepoVersionCommands adds version control subcommands to repo
func CreateRepoVersionCommands(repoCmd *cobra.Command, serviceContext any) {
	repoCmd.AddCommand(createRepoCommitCommand2(serviceContext))
	repoCmd.AddCommand(createRepoStatusCommand2(serviceContext))
	repoCmd.AddCommand(createRepoLogCommand(serviceContext))
	repoCmd.AddCommand(createRepoDiffCommand(serviceContext))
	repoCmd.AddCommand(createRepoCheckoutCommand(serviceContext))
}

// createRepoCommitCommand2 creates a real commit command
func createRepoCommitCommand2(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "commit",
		Short: "Create a new version snapshot",
		Long:  "Capture the current building state and create a new version with a commit message",
		RunE: func(cmd *cobra.Command, args []string) error {
			message, _ := cmd.Flags().GetString("message")
			if message == "" {
				return fmt.Errorf("commit message is required (-m flag)")
			}

			// Get service context
			sc, ok := serviceContext.(VersionServiceProvider)
			if !ok {
				return fmt.Errorf("version control services not available")
			}

			ctx := context.Background()
			buildingID := sc.GetBuildingID()

			if buildingID == "" {
				return fmt.Errorf("no building context set. Use 'arx building create' first")
			}

			fmt.Println(info("Creating version snapshot..."))

			// Capture snapshot first
			snapshot, err := sc.GetSnapshotService().CaptureSnapshot(ctx, buildingID)
			if err != nil {
				return fmt.Errorf("failed to capture snapshot: %w", err)
			}

			fmt.Printf(dim("  Snapshot: %s\n"), shortHash(snapshot.Hash))
			fmt.Printf(dim("  Building: %d floors, %d equipment items\n"),
				snapshot.Metadata.SpaceCount,
				snapshot.Metadata.ItemCount)

			// Create version
			version, err := sc.GetVersionService().CreateVersion(ctx, buildingID, message)
			if err != nil {
				return fmt.Errorf("failed to create version: %w", err)
			}

			// Success output
			fmt.Println()
			fmt.Printf("%s Version %s created\n", success("✓"), highlight(version.Tag))
			fmt.Printf("  %s\n", bold(message))
			fmt.Printf("  Author: %s\n", version.Author.Name)
			fmt.Printf("  Hash: %s\n", shortHash(version.Hash))
			fmt.Printf("  Time: %s\n", version.Timestamp.Format("2006-01-02 15:04:05"))

			return nil
		},
	}

	cmd.Flags().StringP("message", "m", "", "Commit message (required)")
	cmd.MarkFlagRequired("message")

	return cmd
}

// createRepoStatusCommand2 creates a real status command
func createRepoStatusCommand2(serviceContext any) *cobra.Command {
	return &cobra.Command{
		Use:   "status",
		Short: "Show repository status and current version",
		Long:  "Display the current version, recent history, and repository statistics",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Get service context
			sc, ok := serviceContext.(VersionServiceProvider)
			if !ok {
				return fmt.Errorf("version control services not available")
			}

			ctx := context.Background()
			buildingID := sc.GetBuildingID()

			if buildingID == "" {
				return fmt.Errorf("no building context set")
			}

			// Get versions
			versions, err := sc.GetVersionService().ListVersions(ctx, buildingID)
			if err != nil {
				return fmt.Errorf("failed to list versions: %w", err)
			}

			if len(versions) == 0 {
				fmt.Println(warning("⚠ No versions yet. Use 'arx repo commit -m \"Initial version\"'"))
				return nil
			}

			// Get latest version
			current := versions[len(versions)-1]

			// Get latest snapshot
			snapshot, err := sc.GetSnapshotService().GetLatestSnapshot(ctx, buildingID)
			if err != nil {
				return fmt.Errorf("failed to get snapshot: %w", err)
			}

			// Display status
			fmt.Println(bold("Repository Status"))
			fmt.Println(strings.Repeat("─", 50))
			fmt.Printf("Building: %s\n", info(buildingID))
			fmt.Printf("Current:  %s\n", highlight(current.Tag))
			fmt.Printf("Branch:   %s\n", success("main"))
			fmt.Printf("Hash:     %s\n", dim(shortHash(current.Hash)))
			fmt.Println()

			fmt.Println(bold("Latest Snapshot"))
			fmt.Println(strings.Repeat("─", 50))
			fmt.Printf("Floors:    %d\n", snapshot.Metadata.SpaceCount)
			fmt.Printf("Rooms:     %d\n", snapshot.Metadata.SpaceCount)
			fmt.Printf("Equipment: %d\n", snapshot.Metadata.ItemCount)
			fmt.Printf("Files:     %d\n", snapshot.Metadata.FileCount)
			fmt.Printf("Size:      %.2f MB\n", float64(snapshot.Metadata.TotalSize)/(1024*1024))
			fmt.Println()

			fmt.Println(bold("Recent History"))
			fmt.Println(strings.Repeat("─", 50))

			// Show last 5 versions
			start := len(versions) - 5
			if start < 0 {
				start = 0
			}

			for i := len(versions) - 1; i >= start; i-- {
				v := versions[i]
				marker := " "
				if i == len(versions)-1 {
					marker = success("●")
				} else {
					marker = dim("○")
				}

				fmt.Printf("%s %s %s\n",
					marker,
					highlight(v.Tag),
					dim(v.Timestamp.Format("2006-01-02 15:04")))
				fmt.Printf("  %s\n", v.Message)
				if i > start {
					fmt.Println()
				}
			}

			fmt.Println()
			fmt.Print(dim("Use 'arx repo log' for full history\n"))

			return nil
		},
	}
}

// createRepoLogCommand creates the log command
func createRepoLogCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "log",
		Short: "Show version history",
		Long:  "Display the complete version history with commit messages and authors",
		RunE: func(cmd *cobra.Command, args []string) error {
			// Get service context
			sc, ok := serviceContext.(VersionServiceProvider)
			if !ok {
				return fmt.Errorf("version control services not available")
			}

			ctx := context.Background()
			buildingID := sc.GetBuildingID()

			if buildingID == "" {
				return fmt.Errorf("no building context set")
			}

			// Get flag for oneline format
			oneline, _ := cmd.Flags().GetBool("oneline")
			limit, _ := cmd.Flags().GetInt("limit")

			// Get versions
			versions, err := sc.GetVersionService().ListVersions(ctx, buildingID)
			if err != nil {
				return fmt.Errorf("failed to list versions: %w", err)
			}

			if len(versions) == 0 {
				fmt.Println(warning("⚠ No versions yet"))
				return nil
			}

			// Apply limit
			if limit > 0 && len(versions) > limit {
				versions = versions[len(versions)-limit:]
			}

			// Display log
			for i := len(versions) - 1; i >= 0; i-- {
				v := versions[i]

				if oneline {
					// Compact format
					marker := dim("○")
					if i == len(versions)-1 {
						marker = success("●")
					}
					hashShort := v.Hash
					if len(hashShort) > 8 {
						hashShort = hashShort[:8]
					}
					fmt.Printf("%s %s %s %s\n",
						marker,
						highlight(v.Tag),
						dim(hashShort),
						v.Message)
				} else {
					// Full format
					marker := dim("commit")
					if i == len(versions)-1 {
						marker = success("commit")
					}

					fmt.Printf("%s %s\n", marker, highlight(v.Tag))
					fmt.Printf("Hash:      %s\n", shortHash(v.Hash))
					if v.Parent != "" {
						fmt.Printf("Parent:    %s\n", dim(shortHash(v.Parent)))
					}
					fmt.Printf("Author:    %s <%s>\n", v.Author.Name, v.Author.Email)
					fmt.Printf("Date:      %s\n", v.Timestamp.Format("Mon Jan 2 15:04:05 2006"))
					fmt.Printf("Source:    %s\n", v.Metadata.Source)
					if v.Metadata.ChangeCount > 0 {
						fmt.Printf("Changes:   %d\n", v.Metadata.ChangeCount)
					}
					fmt.Println()
					fmt.Printf("    %s\n", bold(v.Message))

					if i > 0 {
						fmt.Println()
					}
				}
			}

			return nil
		},
	}

	cmd.Flags().BoolP("oneline", "1", false, "Show compact one-line format")
	cmd.Flags().IntP("limit", "n", 0, "Limit number of versions shown (0 = all)")

	return cmd
}

// createRepoDiffCommand creates the diff command
func createRepoDiffCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "diff <version1> <version2>",
		Short: "Show differences between versions",
		Long:  "Compare two versions and display the differences in building state",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			fromTag := args[0]
			toTag := args[1]

			// Get service context
			sc, ok := serviceContext.(VersionServiceProvider)
			if !ok {
				return fmt.Errorf("version control services not available")
			}

			ctx := context.Background()
			buildingID := sc.GetBuildingID()

			if buildingID == "" {
				return fmt.Errorf("no building context set")
			}

			// Get format flag
			format, _ := cmd.Flags().GetString("format")

			fmt.Printf(info("Comparing %s...%s\n"), highlight(fromTag), highlight(toTag))

			// Get versions
			fromVersion, err := sc.GetVersionService().GetVersion(ctx, buildingID, fromTag)
			if err != nil {
				return fmt.Errorf("failed to get version %s: %w", fromTag, err)
			}

			toVersion, err := sc.GetVersionService().GetVersion(ctx, buildingID, toTag)
			if err != nil {
				return fmt.Errorf("failed to get version %s: %w", toTag, err)
			}

			// Calculate diff
			diff, err := sc.GetDiffService().DiffVersions(ctx, fromVersion, toVersion)
			if err != nil {
				return fmt.Errorf("failed to calculate diff: %w", err)
			}

			// Format and display
			output, err := building.FormatDiff(diff, building.DiffOutputFormat(format))
			if err != nil {
				return fmt.Errorf("failed to format diff: %w", err)
			}

			fmt.Println()
			fmt.Println(output)

			return nil
		},
	}

	cmd.Flags().StringP("format", "f", "semantic", "Output format (unified, json, semantic, summary)")

	return cmd
}

// createRepoCheckoutCommand creates the checkout command
func createRepoCheckoutCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "checkout <version>",
		Short: "Rollback to a previous version",
		Long:  "Restore the building state to a previous version",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			versionTag := args[0]

			// Get service context
			sc, ok := serviceContext.(VersionServiceProvider)
			if !ok {
				return fmt.Errorf("version control services not available")
			}

			ctx := context.Background()
			buildingID := sc.GetBuildingID()

			if buildingID == "" {
				return fmt.Errorf("no building context set")
			}

			// Get flags
			force, _ := cmd.Flags().GetBool("force")
			dryRun, _ := cmd.Flags().GetBool("dry-run")

			if !force && !dryRun {
				fmt.Println(warning("⚠ This will restore your building to a previous state."))
				fmt.Println(dim("  Use --dry-run to preview changes"))
				fmt.Println(dim("  Use --force to proceed without confirmation"))
				return fmt.Errorf("rollback cancelled")
			}

			// Get target version
			targetVersion, err := sc.GetVersionService().GetVersion(ctx, buildingID, versionTag)
			if err != nil {
				return fmt.Errorf("failed to get version %s: %w", versionTag, err)
			}

			// Configure rollback
			opts := &RollbackOptions{
				CreateVersion: true,
				Message:       fmt.Sprintf("Rollback to %s", versionTag),
				ValidateAfter: true,
				DryRun:        dryRun,
			}

			if dryRun {
				fmt.Println(info("Preview Mode (dry-run)"))
				fmt.Println(strings.Repeat("─", 50))
			} else {
				fmt.Printf(info("Rolling back to %s...\n"), highlight(versionTag))
			}

			// Perform rollback
			result, err := sc.GetRollbackService().Rollback(ctx, buildingID, targetVersion, opts)
			if err != nil {
				return fmt.Errorf("rollback failed: %w", err)
			}

			if !result.Success {
				return fmt.Errorf("rollback failed: %s", result.Error)
			}

			// Display results
			fmt.Println()
			if dryRun {
				fmt.Println(info("Would restore:"))
			} else {
				fmt.Println(success("✓ Rollback completed successfully"))
				fmt.Println()
				fmt.Println(bold("Restored:"))
			}

			fmt.Printf("  Building:  %s\n", formatBool(result.Changes.BuildingRestored))
			fmt.Printf("  Floors:    %d\n", result.Changes.FloorsRestored)
			fmt.Printf("  Equipment: %d\n", result.Changes.EquipmentRestored)
			fmt.Println()
			fmt.Printf("Duration: %v\n", result.Duration)

			// Show validation results if available
			if result.ValidationResult != nil {
				fmt.Println()
				if result.ValidationResult.Valid {
					fmt.Println(success("✓ Validation passed"))
					for _, check := range result.ValidationResult.Checks {
						fmt.Printf("  %s %s\n", success("✓"), check)
					}
				} else {
					fmt.Println(errorMsg("✗ Validation failed"))
					for _, err := range result.ValidationResult.Errors {
						fmt.Printf("  %s %s\n", errorMsg("✗"), err)
					}
				}

				if len(result.ValidationResult.Warnings) > 0 {
					fmt.Println()
					fmt.Println(warning("⚠ Warnings:"))
					for _, warn := range result.ValidationResult.Warnings {
						fmt.Printf("  %s %s\n", warning("⚠"), warn)
					}
				}
			}

			if dryRun {
				fmt.Println()
				fmt.Println(dim("Run without --dry-run and with --force to apply changes"))
			}

			return nil
		},
	}

	cmd.Flags().Bool("force", false, "Force rollback without confirmation")
	cmd.Flags().Bool("dry-run", false, "Preview changes without applying")

	return cmd
}

// formatBool formats a boolean with color
func formatBool(b bool) string {
	if b {
		return success("restored")
	}
	return dim("unchanged")
}

// shortHash safely truncates a hash to the first 12 characters (or less if shorter)
func shortHash(hash string) string {
	if len(hash) <= 12 {
		return hash
	}
	return hash[:12]
}
