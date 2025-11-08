//! User Identity and Attribution module for ArxOS
//!
//! This module provides user registry management, verification, and attribution
//! for Git commits. All identity data is stored in Git (Git-native architecture).

mod gpg;
mod pending;
mod registry;
mod user;

pub use gpg::{
    get_git_signing_key, get_key_fingerprint_for_email, get_key_id_for_email,
    is_git_signing_enabled, is_gpg_available, store_gpg_fingerprint_for_user, GpgError, GpgResult,
};
pub use pending::{
    PendingRegistryError, PendingRequestStatus, PendingUserRegistry, PendingUserRequest,
};
pub use registry::{RegistryError, UserRegistry};
pub use user::{User, UserRegistryData, UserStatus};
