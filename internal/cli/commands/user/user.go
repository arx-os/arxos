package user

import (
	"context"
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase/auth"
	"github.com/spf13/cobra"
)

// UserServiceProvider provides access to user services
type UserServiceProvider interface {
	GetUserUseCase() *auth.UserUseCase
}

// CreateUserCommands creates user management commands
func CreateUserCommands(serviceContext any) *cobra.Command {
	userCmd := &cobra.Command{
		Use:   "user",
		Short: "Manage users",
		Long:  `Create, list, get, update, and delete users in the ArxOS system`,
	}

	userCmd.AddCommand(createUserRegisterCommand(serviceContext))
	userCmd.AddCommand(createUserListCommand(serviceContext))
	userCmd.AddCommand(createUserGetCommand(serviceContext))
	userCmd.AddCommand(createUserUpdateCommand(serviceContext))
	userCmd.AddCommand(createUserDeleteCommand(serviceContext))

	return userCmd
}

// createUserRegisterCommand creates the user register command
func createUserRegisterCommand(serviceContext any) *cobra.Command {
	var (
		email    string
		name     string
		password string
		role     string
	)

	cmd := &cobra.Command{
		Use:   "register",
		Short: "Register a new user",
		Long:  "Register a new user account with email, name, and password",
		Example: `  # Register a user
  arx user register --email user@example.com --name "John Doe" --password "SecurePass123!"

  # Register an admin user
  arx user register --email admin@example.com --name "Admin" --password "AdminPass123!" --role admin`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Get service from context
			sc, ok := serviceContext.(UserServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			userUC := sc.GetUserUseCase()

			// Validate required fields
			if email == "" {
				return fmt.Errorf("email is required (--email)")
			}
			if name == "" {
				return fmt.Errorf("name is required (--name)")
			}
			if password == "" {
				return fmt.Errorf("password is required (--password)")
			}
			if role == "" {
				role = "user" // Default role
			}

			// Register user
			user, err := userUC.RegisterUser(ctx, email, name, password, role)
			if err != nil {
				return fmt.Errorf("failed to register user: %w", err)
			}

			// Print success
			fmt.Printf("✅ User registered successfully!\n\n")
			fmt.Printf("   ID:     %s\n", user.ID.String())
			fmt.Printf("   Email:  %s\n", user.Email)
			fmt.Printf("   Name:   %s\n", user.Name)
			fmt.Printf("   Role:   %s\n", user.Role)
			fmt.Printf("   Status: %s\n", func() string {
				if user.Active {
					return "active"
				}
				return "inactive"
			}())
			fmt.Printf("\n")
			fmt.Printf("💡 Use 'arx user login' to authenticate\n")
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringVarP(&email, "email", "e", "", "User email (required)")
	cmd.Flags().StringVarP(&name, "name", "n", "", "User full name (required)")
	cmd.Flags().StringVarP(&password, "password", "p", "", "User password (required)")
	cmd.Flags().StringVarP(&role, "role", "r", "user", "User role (user, admin, viewer)")

	cmd.MarkFlagRequired("email")
	cmd.MarkFlagRequired("name")
	cmd.MarkFlagRequired("password")

	return cmd
}

// createUserListCommand creates the user list command
func createUserListCommand(serviceContext any) *cobra.Command {
	var (
		limit      int
		offset     int
		roleFilter string
		activeOnly bool
	)

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List all users",
		Long:  "List all users in the system with optional filtering and pagination",
		Example: `  # List all users
  arx user list

  # List with pagination
  arx user list --limit 10 --offset 20

  # Filter by role
  arx user list --role admin

  # Show only active users
  arx user list --active`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Get service from context
			sc, ok := serviceContext.(UserServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			userUC := sc.GetUserUseCase()

			// Create filter
			filter := &domain.UserFilter{
				Limit:  limit,
				Offset: offset,
			}
			if roleFilter != "" {
				filter.Role = &roleFilter
			}
			if activeOnly {
				active := true
				filter.Active = &active
			}

			// List users
			users, err := userUC.ListUsers(ctx, filter)
			if err != nil {
				return fmt.Errorf("failed to list users: %w", err)
			}

			if len(users) == 0 {
				fmt.Println("No users found.")
				return nil
			}

			// Print results in table format
			w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
			fmt.Fprintf(w, "ID\tEMAIL\tNAME\tROLE\tSTATUS\tCREATED\n")
			fmt.Fprintf(w, "--\t-----\t----\t----\t------\t-------\n")

			for _, user := range users {
				status := "active"
				if !user.Active {
					status = "inactive"
				}
				fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\n",
					user.ID.String()[:8]+"...",
					user.Email,
					user.Name,
					user.Role,
					status,
					user.CreatedAt.Format("2006-01-02"),
				)
			}
			w.Flush()

			fmt.Printf("\n%d user(s) found (showing %d-%d)\n", len(users), offset+1, offset+len(users))

			return nil
		},
	}

	// Add flags
	cmd.Flags().IntVarP(&limit, "limit", "l", 100, "Maximum number of results")
	cmd.Flags().IntVarP(&offset, "offset", "o", 0, "Offset for pagination")
	cmd.Flags().StringVar(&roleFilter, "role", "", "Filter by role (user, admin, viewer)")
	cmd.Flags().BoolVar(&activeOnly, "active", false, "Show only active users")

	return cmd
}

// createUserGetCommand creates the user get command
func createUserGetCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "get <user-id>",
		Short: "Get user details",
		Long:  "Get detailed information about a specific user by ID",
		Example: `  # Get user details
  arx user get abc123def456`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			userID := args[0]

			// Get service from context
			sc, ok := serviceContext.(UserServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			userUC := sc.GetUserUseCase()

			// Get user
			user, err := userUC.GetUser(ctx, userID)
			if err != nil {
				return fmt.Errorf("failed to get user: %w", err)
			}

			// Print user details
			fmt.Printf("User Details:\n\n")
			fmt.Printf("   ID:      %s\n", user.ID.String())
			fmt.Printf("   Email:   %s\n", user.Email)
			fmt.Printf("   Name:    %s\n", user.Name)
			fmt.Printf("   Role:    %s\n", user.Role)
			fmt.Printf("   Status:  %s\n", func() string {
				if user.Active {
					return "active"
				}
				return "inactive"
			}())
			fmt.Printf("   Created: %s\n", user.CreatedAt.Format("2006-01-02 15:04:05"))
			fmt.Printf("   Updated: %s\n", user.UpdatedAt.Format("2006-01-02 15:04:05"))
			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}

// createUserUpdateCommand creates the user update command
func createUserUpdateCommand(serviceContext any) *cobra.Command {
	var (
		name       string
		role       string
		activate   bool
		deactivate bool
	)

	cmd := &cobra.Command{
		Use:   "update <user-id>",
		Short: "Update user information",
		Long:  "Update user name, role, or activation status",
		Example: `  # Update user name
  arx user update abc123 --name "New Name"

  # Update role
  arx user update abc123 --role admin

  # Deactivate user
  arx user update abc123 --deactivate

  # Activate user
  arx user update abc123 --activate`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			userID := args[0]

			// Validate at least one field is provided
			if name == "" && role == "" && !activate && !deactivate {
				return fmt.Errorf("at least one field to update is required")
			}

			// Validate conflicting flags
			if activate && deactivate {
				return fmt.Errorf("cannot use --activate and --deactivate together")
			}

			// Get service from context
			sc, ok := serviceContext.(UserServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			userUC := sc.GetUserUseCase()

			// Create update request
			req := &domain.UpdateUserRequest{
				ID: types.FromString(userID),
			}
			if name != "" {
				req.Name = &name
			}
			if role != "" {
				req.Role = &role
			}
			if activate {
				active := true
				req.Active = &active
			}
			if deactivate {
				active := false
				req.Active = &active
			}

			// Update user
			user, err := userUC.UpdateUser(ctx, req)
			if err != nil {
				return fmt.Errorf("failed to update user: %w", err)
			}

			// Print success
			fmt.Printf("✅ User updated successfully!\n\n")
			fmt.Printf("   ID:     %s\n", user.ID.String())
			fmt.Printf("   Email:  %s\n", user.Email)
			fmt.Printf("   Name:   %s\n", user.Name)
			fmt.Printf("   Role:   %s\n", user.Role)
			fmt.Printf("   Status: %s\n", func() string {
				if user.Active {
					return "active"
				}
				return "inactive"
			}())
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringVarP(&name, "name", "n", "", "New user name")
	cmd.Flags().StringVarP(&role, "role", "r", "", "New user role (user, admin, viewer)")
	cmd.Flags().BoolVar(&activate, "activate", false, "Activate user account")
	cmd.Flags().BoolVar(&deactivate, "deactivate", false, "Deactivate user account")

	return cmd
}

// createUserDeleteCommand creates the user delete command
func createUserDeleteCommand(serviceContext any) *cobra.Command {
	var force bool

	cmd := &cobra.Command{
		Use:   "delete <user-id>",
		Short: "Delete a user",
		Long:  "Delete a user from the system (requires confirmation unless --force is used)",
		Example: `  # Delete with confirmation
  arx user delete abc123

  # Delete without confirmation
  arx user delete abc123 --force`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			userID := args[0]

			// Get service from context
			sc, ok := serviceContext.(UserServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			userUC := sc.GetUserUseCase()

			// Confirmation prompt unless --force
			if !force {
				fmt.Printf("⚠️  Are you sure you want to delete user %s? (yes/no): ", userID)
				var response string
				fmt.Scanln(&response)
				if response != "yes" && response != "y" {
					fmt.Println("Deletion cancelled.")
					return nil
				}
			}

			// Delete user
			err := userUC.DeleteUser(ctx, userID)
			if err != nil {
				return fmt.Errorf("failed to delete user: %w", err)
			}

			// Print success
			fmt.Printf("✅ User deleted successfully!\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().BoolVarP(&force, "force", "f", false, "Skip confirmation prompt")

	return cmd
}
