//! Clap argument definitions for the `arx` CLI.

use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(
    name = "arx",
    version,
    about = "Arxos content-addressed building repository tools"
)]
pub struct Cli {
    /// Path to the local object store directory.
    #[arg(
        long,
        global = true,
        default_value = ".arxos/store",
        env = "ARXOS_STORE"
    )]
    pub store: PathBuf,

    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand, Debug)]
pub enum Commands {
    /// Low-level object CAS (debug)
    ///
    /// `object put` is a debug CAS operation and does not stage or update a
    /// building head. Prefer `capture` + `building commit`.
    Object {
        #[command(subcommand)]
        command: ObjectCommands,
    },
    /// Low-level root CAS (debug)
    ///
    /// `root create` writes a signed root but does not update the building head.
    /// Prefer `building commit`.
    Root {
        #[command(subcommand)]
        command: RootCommands,
    },
    /// Key management
    Key {
        #[command(subcommand)]
        command: KeyCommands,
    },
    /// Building repository (Phase 1)
    Building {
        #[command(subcommand)]
        command: BuildingCommands,
    },
    /// Capture into a building working set (Phase 1)
    Capture {
        #[command(subcommand)]
        command: CaptureCommands,
    },
    /// Multi-device networking (Phase 2)
    Net {
        #[command(subcommand)]
        command: NetCommands,
    },
    /// Spatial index & partial load (Phase 3)
    Spatial {
        #[command(subcommand)]
        command: SpatialCommands,
    },
    /// Merge concurrent roots (Phase 3)
    Merge {
        #[command(subcommand)]
        command: MergeCommands,
    },
    /// Interop projections: USD / IFC (Phase 4)
    Export {
        #[command(subcommand)]
        command: ExportCommands,
    },
    /// Import projections into the object store (Phase 4)
    Import {
        #[command(subcommand)]
        command: ImportCommands,
    },
    /// Entity operations (remove / list heads)
    Entity {
        #[command(subcommand)]
        command: EntityCommands,
    },
    /// Score contributions under a building head (diagnostic points; not payment-grade)
    Score {
        building_id: String,
        /// Root CID (default: building head)
        #[arg(long)]
        root: Option<String>,
        #[arg(long)]
        json: bool,
    },
    /// Verify root transition + signatures + canonicalization
    Verify {
        /// Root CID to verify
        root: String,
        #[arg(long)]
        json: bool,
    },
    /// Debug CAS operation: write a mock attestation provenance object
    ///
    /// Does not stage objects or update the building head. Prefer
    /// `BuildingRepository` / capture + commit for building data.
    Attest {
        /// Subject root CID
        root: String,
        #[arg(long, default_value = "mock-device")]
        device_id: String,
        /// Sign provenance with store device key when present
        #[arg(long, default_value_t = true)]
        sign: bool,
    },
    /// Print core version / hello
    Version,
}

#[derive(Subcommand, Debug)]
pub enum ExportCommands {
    /// Export building head as OpenUSD ASCII (USDA)
    Usd {
        building_id: String,
        /// Output path (default: stdout)
        #[arg(long, short)]
        out: Option<PathBuf>,
        /// Omit point-cloud points
        #[arg(long)]
        no_points: bool,
    },
    /// Export building head as IFC4 STEP
    Ifc {
        building_id: String,
        #[arg(long, short)]
        out: Option<PathBuf>,
        #[arg(long)]
        project_name: Option<String>,
    },
}

#[derive(Subcommand, Debug)]
pub enum ImportCommands {
    /// Import USDA into a local store (new/follow building + commit)
    Usd {
        /// Path to .usda file
        file: PathBuf,
        /// Sign imported objects with device seed if present
        #[arg(long, default_value_t = true)]
        sign: bool,
    },
    /// Import IFC STEP into a local store
    Ifc {
        file: PathBuf,
        #[arg(long, default_value_t = true)]
        sign: bool,
    },
}

#[derive(Subcommand, Debug)]
pub enum SpatialCommands {
    /// Rebuild spatial index for a building head (reports CID; commit to attach)
    Build {
        building_id: String,
        /// Create a new root that attaches the index
        #[arg(long)]
        commit: bool,
        #[arg(long)]
        message: Option<String>,
    },
    /// Query objects intersecting a volume
    Query {
        building_id: String,
        #[arg(long)]
        min_x: f64,
        #[arg(long)]
        min_y: f64,
        #[arg(long)]
        min_z: f64,
        #[arg(long)]
        max_x: f64,
        #[arg(long)]
        max_y: f64,
        #[arg(long)]
        max_z: f64,
        #[arg(long)]
        json: bool,
    },
    /// Partially materialize objects in a volume into the working set
    Load {
        building_id: String,
        #[arg(long)]
        min_x: f64,
        #[arg(long)]
        min_y: f64,
        #[arg(long)]
        min_z: f64,
        #[arg(long)]
        max_x: f64,
        #[arg(long)]
        max_y: f64,
        #[arg(long)]
        max_z: f64,
        /// Max objects to load (0 = unlimited)
        #[arg(long, default_value_t = 0)]
        limit: usize,
    },
    /// Load objects for a floor (by floor object CID)
    LoadFloor {
        building_id: String,
        floor_cid: String,
        #[arg(long, default_value_t = 0)]
        limit: usize,
    },
}

#[derive(Subcommand, Debug)]
pub enum MergeCommands {
    /// Dry-run merge plan for two root CIDs
    Plan { root_a: String, root_b: String },
    /// Merge other_root into the building's current head
    Apply {
        building_id: String,
        other_root: String,
        #[arg(long)]
        message: Option<String>,
    },
}

#[derive(Subcommand, Debug)]
pub enum NetCommands {
    /// Serve the local CAS over Iroh QUIC (and optionally mDNS)
    Serve {
        /// Disable mDNS advertising (on by default)
        #[arg(long, default_value_t = false)]
        no_mdns: bool,
        /// Print ticket and exit accept-loop setup info only (for scripting)
        #[arg(long)]
        ticket_only: bool,
    },
    Fetch {
        /// Peer dial ticket (JSON EndpointAddr from `net serve`)
        #[arg(long)]
        peer: String,
        /// Root CID to pull
        #[arg(long)]
        root: String,
        /// Building id (optional; inferred from root when omitted)
        #[arg(long)]
        building_id: Option<String>,
        /// Adopt pulled root as local head [default: true].
        #[arg(
            long = "no-set-head",
            action = clap::ArgAction::SetFalse,
            default_value_t = true,
            help = "Ingest without adopting as local head (then merge apply with printed root_cid)"
        )]
        set_head: bool,
        /// Allow adopting untrusted roots (verification failure becomes warning)
        #[arg(long, default_value_t = false)]
        allow_untrusted: bool,
        /// Pull domain objects without Blob payloads (metadata-first)
        #[arg(long, default_value_t = false)]
        metadata_only: bool,
    },
    /// Refresh advertisements / print current building heads for publish
    Publish {
        /// Optional peer ticket to announce to (best-effort)
        #[arg(long)]
        peer: Option<String>,
        /// Building to announce (all if omitted)
        #[arg(long)]
        building_id: Option<String>,
    },
    /// Browse mDNS for local Arxos peers
    Peers {
        /// How long to wait for discoveries (seconds)
        #[arg(long, default_value_t = 3)]
        timeout: u64,
        #[arg(long)]
        json: bool,
    },
    /// Networking stack status
    Status,
}

#[derive(Subcommand, Debug)]
pub enum BuildingCommands {
    /// Create a new building repository (CAS + head + device key)
    Init {
        #[arg(long)]
        name: Option<String>,
        #[arg(long)]
        quiet: bool,
    },
    /// Open / show a building by ID
    Show {
        building_id: String,
        #[arg(long)]
        json: bool,
    },
    /// List buildings in the store
    List {
        #[arg(long)]
        json: bool,
    },
    /// Commit pending captures to a new signed root
    Commit {
        building_id: String,
        #[arg(long)]
        message: Option<String>,
        #[arg(long)]
        quiet: bool,
    },
    /// Query annotations near a pose
    Near {
        building_id: String,
        #[arg(long, default_value = "0")]
        x: f64,
        #[arg(long, default_value = "0")]
        y: f64,
        #[arg(long, default_value = "0")]
        z: f64,
        #[arg(long, default_value = "10")]
        radius: f64,
    },
    /// Add a controller public key (commits by default)
    AddController {
        building_id: String,
        /// ed25519 public key (`ed25519:<hex>` or raw 64-char hex)
        pubkey: String,
        /// Skip automatic commit (stage only)
        #[arg(long)]
        no_commit: bool,
        #[arg(long)]
        message: Option<String>,
        #[arg(long)]
        quiet: bool,
    },
    /// Remove a controller public key (commits by default; cannot remove last)
    RemoveController {
        building_id: String,
        pubkey: String,
        #[arg(long)]
        no_commit: bool,
        #[arg(long)]
        message: Option<String>,
        #[arg(long)]
        quiet: bool,
    },
    /// List controller public keys for a building
    Controllers {
        building_id: String,
        #[arg(long)]
        json: bool,
    },
    /// Compact head status: root, controllers, entity counts, lock probe
    Status {
        building_id: String,
        #[arg(long)]
        json: bool,
    },
}

#[derive(Subcommand, Debug)]
pub enum EntityCommands {
    /// Stage removal of all versions of an entity and commit (by default)
    Remove {
        building_id: String,
        entity_id: String,
        /// Skip automatic commit (stage only)
        #[arg(long)]
        no_commit: bool,
        #[arg(long)]
        message: Option<String>,
        #[arg(long)]
        quiet: bool,
    },
    /// List entity heads in the building active set
    List {
        building_id: String,
        #[arg(long)]
        json: bool,
    },
    /// Show the current head version of one entity
    Show {
        building_id: String,
        entity_id: String,
        #[arg(long)]
        json: bool,
    },
}

#[derive(Subcommand, Debug)]
pub enum CaptureCommands {
    /// Capture a Space object at a pose
    Space {
        building_id: String,
        #[arg(long)]
        name: Option<String>,
        #[arg(long, default_value = "0")]
        x: f64,
        #[arg(long, default_value = "0")]
        y: f64,
        #[arg(long, default_value = "0")]
        z: f64,
        #[arg(long)]
        quiet: bool,
    },
    /// Capture a text Annotation at a pose
    Annotation {
        building_id: String,
        #[arg(long)]
        text: String,
        #[arg(long, default_value = "0")]
        x: f64,
        #[arg(long, default_value = "0")]
        y: f64,
        #[arg(long, default_value = "0")]
        z: f64,
        #[arg(long)]
        quiet: bool,
    },
    /// Capture a synthetic / file-based point cloud (xyz f32 LE)
    PointCloud {
        building_id: String,
        /// Path to raw xyz f32 LE bytes; if omitted, generates a small synthetic room sample
        #[arg(long)]
        file: Option<PathBuf>,
        #[arg(long, default_value = "0")]
        x: f64,
        #[arg(long, default_value = "0")]
        y: f64,
        #[arg(long, default_value = "0")]
        z: f64,
        #[arg(long)]
        quiet: bool,
    },
    /// Simulate a full RoomPlan-like capture: space + point cloud + annotation
    Simulate {
        building_id: String,
        #[arg(long, default_value = "Simulated Room")]
        name: String,
        #[arg(long, default_value = "simulated note")]
        text: String,
        #[arg(long)]
        commit: bool,
        #[arg(long)]
        message: Option<String>,
    },
}

#[derive(Subcommand, Debug)]
pub enum ObjectCommands {
    /// Debug CAS operation: write an object into the store
    ///
    /// Does not stage objects or update the building head. Prefer `capture` +
    /// `building commit`. Without `--building-id` this is a bare CAS put (no
    /// building attached).
    Put {
        /// Object type (blob, annotation, building, …)
        #[arg(long, default_value = "blob")]
        r#type: String,

        /// Path to file payload (for blob) or text for annotation
        #[arg(long)]
        file: Option<PathBuf>,

        /// Inline text (annotation or blob utf-8)
        #[arg(long)]
        text: Option<String>,

        /// Building name (when type=building)
        #[arg(long)]
        name: Option<String>,

        /// Building id (when type=building); generated if omitted
        #[arg(long)]
        building_id: Option<String>,

        /// Optional content-type for blob
        #[arg(long)]
        content_type: Option<String>,

        /// Sign with seed hex (32-byte ed25519 seed)
        #[arg(long)]
        sign_seed: Option<String>,

        /// Print only the CID
        #[arg(long)]
        quiet: bool,
    },
    /// Read an object by CID
    Get {
        /// Object CID (b3:… or hex)
        cid: String,

        /// Write raw canonical CBOR to this path
        #[arg(long)]
        out: Option<PathBuf>,

        /// Print JSON summary
        #[arg(long)]
        json: bool,
    },
    /// List CIDs in the store
    List,
}

#[derive(Subcommand, Debug)]
pub enum RootCommands {
    /// Debug CAS operation: write a signed root object
    ///
    /// Does not stage objects or update the building head. Prefer
    /// `building commit`.
    Create {
        /// Building ID
        #[arg(long)]
        building_id: String,

        /// Object CIDs to include (repeatable)
        #[arg(long = "object")]
        objects: Vec<String>,

        /// Include every object currently in the store
        #[arg(long)]
        all: bool,

        /// Previous root CID
        #[arg(long)]
        previous: Option<String>,

        /// Commit message
        #[arg(long)]
        message: Option<String>,

        /// ed25519 seed hex (32 bytes) used to sign the root
        #[arg(long)]
        seed: String,

        /// Print only the root CID
        #[arg(long)]
        quiet: bool,
    },
    /// Show a root by CID
    Show {
        /// Root object CID
        cid: String,

        /// JSON output
        #[arg(long)]
        json: bool,
    },
}

#[derive(Subcommand, Debug)]
pub enum KeyCommands {
    /// Explicitly export a new ed25519 seed + public key (prints secret material)
    Generate,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn parse_fetch(extra: &[&str]) -> bool {
        let mut args = vec!["arx", "net", "fetch", "--peer", "{}", "--root", "b3:00"];
        args.extend(extra);
        match Cli::try_parse_from(args) {
            Ok(Cli {
                command:
                    Commands::Net {
                        command: NetCommands::Fetch { set_head, .. },
                    },
                ..
            }) => set_head,
            Ok(other) => panic!("expected net fetch, got {other:?}"),
            Err(e) => panic!("{e}"),
        }
    }

    #[test]
    fn fetch_set_head_default_true() {
        assert!(parse_fetch(&[]));
    }

    #[test]
    fn fetch_no_set_head_sets_false() {
        assert!(!parse_fetch(&["--no-set-head"]));
    }
}
