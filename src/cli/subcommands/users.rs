//! User management commands

use clap::Subcommand;

#[derive(Subcommand)]
pub enum UsersCommands {
    /// Add user to registry
    ///
    /// If --verify is used, requires 'verify_users' permission (admin only).
    /// The first user added automatically becomes an admin with all permissions.
    Add {
        /// User's full name
        #[arg(long)]
        name: String,
        /// User's email address
        #[arg(long)]
        email: String,
        /// Organization (optional)
        #[arg(long)]
        organization: Option<String>,
        /// Role (optional)
        #[arg(long)]
        role: Option<String>,
        /// Phone number (optional, for privacy)
        #[arg(long)]
        phone: Option<String>,
        /// Verify user immediately (requires 'verify_users' permission)
        #[arg(long)]
        verify: bool,
    },
    /// List all registered users
    List,
    /// Interactive user browser (TUI)
    Browse,
    /// Show user details
    Show {
        /// User email
        email: String,
    },
    /// Verify a user (admin only - requires 'verify_users' permission)
    ///
    /// Only users with the 'verify_users' permission can verify other users.
    /// The first user in the registry automatically receives admin permissions.
    Verify {
        /// User email to verify
        email: String,
    },
    /// Revoke user access (admin only - requires 'revoke_users' permission)
    ///
    /// Only users with the 'revoke_users' permission can revoke user access.
    /// The first user in the registry automatically receives admin permissions.
    Revoke {
        /// User email to revoke
        email: String,
    },
    /// Approve a pending user registration request (admin only)
    ///
    /// Approves a pending request from a mobile user and adds them to the user registry.
    /// Requires 'verify_users' permission.
    Approve {
        /// User email from pending request
        email: String,
    },
    /// Deny a pending user registration request (admin only)
    ///
    /// Denies a pending request from a mobile user.
    /// Requires 'verify_users' permission.
    Deny {
        /// User email from pending request
        email: String,
        /// Reason for denial (optional)
        #[arg(long)]
        reason: Option<String>,
    },
    /// List all pending user registration requests
    Pending,
}
