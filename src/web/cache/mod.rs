//! Caching module for PWA / AR field client.
//!
//! Exposes three caching tiers (Hot, Warm, Binary Asset), Scoped working-set
//! retrievals, an offline mutation queue, and predictive warming triggers.

pub mod hot;
pub mod warm;
pub mod binary;
pub mod sync;
pub mod warming;

pub use hot::HotCache;
pub use warm::WarmCache;
pub use binary::BinaryAssetCache;
pub use sync::SyncQueue;
pub use warming::PredictiveWarming;
