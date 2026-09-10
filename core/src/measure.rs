//! Fact-layer measure constants shared by scoring and realize.
//!
//! Scoring reads Facts (\(S\)), not solids (\(B = R(S)\)). The high-\(\sigma\)
//! law lives here so the diagnostic layer does not import `realize`.

/// Skip solids / penalize Facts looser than this 1σ (millimetres).
///
/// Facts with `sigma_mm > SIGMA_EXCLUDE_MM` stay in \(S\). Realize omits
/// them from \(B\). Scoring applies the high-\(\sigma\) penalty. The
/// threshold is the same in both places; do not fork it.
pub const SIGMA_EXCLUDE_MM: f64 = 500.0;
