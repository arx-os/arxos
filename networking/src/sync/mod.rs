//! High-level sync: pull root closures into a local building repository.

mod ads;
mod pull;
mod push;

pub use ads::{
    building_ads_from_store, cid_in_advertised_closures, serve_get_object, serve_root_closure,
    serve_root_closure_with_options,
};
pub use pull::{
    pull_building_head, pull_building_head_with_options, pull_root, pull_root_with_options,
    PullResult,
};
pub use push::{push_facts, serve_push_facts, serve_put_object, PushResult};

#[cfg(test)]
mod tests;
