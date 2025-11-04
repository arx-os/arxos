//! User Identity and Attribution module for ArxOS
//!
//! This module provides user registry management, verification, and attribution
//! for Git commits. All identity data is stored in Git (Git-native architecture).

mod user;
mod registry;
mod pending;
mod gpg;

pub use user::{User, UserStatus, UserRegistryData};
pub use registry::{UserRegistry, RegistryError};
pub use pending::{PendingUserRequest, PendingUserRegistry, PendingRequestStatus, PendingRegistryError};
pub use gpg::{GpgError, GpgResult, get_key_fingerprint_for_email, get_key_id_for_email, is_gpg_available, get_git_signing_key, is_git_signing_enabled, store_gpg_fingerprint_for_user};

