//! Deterministic commitment over canonical Building state.

use sha2::{Digest, Sha256};

use crate::core::Building;
use crate::yaml::BuildingYamlSerializer;

/// Label written into contribution packages (off-chain / default features).
/// On-chain submission with `--features blockchain` re-hashes with keccak where required.
pub const HASH_ALG_LABEL: &str = "sha256-v1";

/// Content + structure commitment for a building model.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BuildingCommitment {
    /// Hash algorithm label (`sha256-v1` for default builds).
    pub algorithm: &'static str,
    /// Hash of deterministic `building.yaml` bytes (primary commitment).
    pub content_hash: [u8; 32],
    /// Merkle-style root over entity identity leaves (structure commitment).
    pub entity_root: [u8; 32],
    /// Combined root: hash(content_hash || entity_root) — oracle `merkleRoot` field.
    pub merkle_root: [u8; 32],
    /// Serialized YAML size in bytes.
    pub data_size: u64,
    /// Canonical building id (UUID string).
    pub building_id: String,
}

impl BuildingCommitment {
    /// Hex-encoded merkle root (no 0x prefix).
    pub fn merkle_root_hex(&self) -> String {
        hex_encode(&self.merkle_root)
    }

    pub fn content_hash_hex(&self) -> String {
        hex_encode(&self.content_hash)
    }
}

/// Hash deterministic YAML serialization of `building` (primary labor unit).
pub fn building_content_hash(building: &Building) -> Result<([u8; 32], u64, String), String> {
    let yaml = BuildingYamlSerializer::serialize_building(building)
        .map_err(|e| format!("serialize building for commitment: {}", e))?;
    let bytes = yaml.as_bytes();
    let hash = sha256(bytes);
    Ok((hash, bytes.len() as u64, yaml))
}

/// Sorted entity leaves → binary-style rolling hash root (no external merkle dep).
///
/// Leaf format (UTF-8):
/// `floor:{id}|room:{id}|equip:{id}|addr:{path_or_empty}`
pub fn building_entity_merkle_root(building: &Building) -> [u8; 32] {
    let mut leaves: Vec<[u8; 32]> = Vec::new();

    for floor in &building.floors {
        leaves.push(sha256(
            format!("floor:{}:{}:{}", floor.id, floor.level, floor.name).as_bytes(),
        ));
        for eq in &floor.equipment {
            leaves.push(equipment_leaf(eq));
        }
        for wing in &floor.wings {
            leaves.push(sha256(format!("wing:{}:{}", wing.name, floor.id).as_bytes()));
            for room in &wing.rooms {
                leaves.push(sha256(
                    format!("room:{}:{}:{}", room.id, room.name, floor.id).as_bytes(),
                ));
                for eq in &room.equipment {
                    leaves.push(equipment_leaf(eq));
                }
            }
            for eq in &wing.equipment {
                leaves.push(equipment_leaf(eq));
            }
        }
    }

    leaves.sort(); // deterministic independent of hierarchy walk quirks
    fold_merkle(&leaves)
}

fn equipment_leaf(eq: &crate::core::Equipment) -> [u8; 32] {
    let addr = eq
        .address
        .as_ref()
        .map(|a| a.path.as_str())
        .unwrap_or("");
    sha256(format!("equip:{}:{}:{}", eq.id, eq.name, addr).as_bytes())
}

/// Build full commitment for oracle / package.
pub fn commit_building(building: &Building) -> Result<BuildingCommitment, String> {
    let (content_hash, data_size, _yaml) = building_content_hash(building)?;
    let entity_root = building_entity_merkle_root(building);
    let mut combined = [0u8; 64];
    combined[..32].copy_from_slice(&content_hash);
    combined[32..].copy_from_slice(&entity_root);
    let merkle_root = sha256(&combined);

    Ok(BuildingCommitment {
        algorithm: HASH_ALG_LABEL,
        content_hash,
        entity_root,
        merkle_root,
        data_size,
        building_id: building.id.clone(),
    })
}

fn fold_merkle(leaves: &[[u8; 32]]) -> [u8; 32] {
    if leaves.is_empty() {
        return sha256(b"arxos-empty-building");
    }
    let mut layer: Vec<[u8; 32]> = leaves.to_vec();
    while layer.len() > 1 {
        let mut next = Vec::with_capacity(layer.len().div_ceil(2));
        let mut i = 0;
        while i < layer.len() {
            if i + 1 < layer.len() {
                let mut a = layer[i];
                let mut b = layer[i + 1];
                if a > b {
                    std::mem::swap(&mut a, &mut b);
                }
                let mut concat = [0u8; 64];
                concat[..32].copy_from_slice(&a);
                concat[32..].copy_from_slice(&b);
                next.push(sha256(&concat));
            } else {
                next.push(layer[i]);
            }
            i += 2;
        }
        layer = next;
    }
    layer[0]
}

fn sha256(data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize().into()
}

fn hex_encode(bytes: &[u8; 32]) -> String {
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Floor, Room, RoomType, Wing};

    fn sample() -> Building {
        let mut b = Building::new("Commit HQ".into(), "/commit-hq".into());
        let mut floor = Floor::new("G".into(), 0);
        let mut wing = Wing::new("Main".into());
        wing.add_room(Room::new("Lobby".into(), RoomType::Hallway));
        floor.add_wing(wing);
        b.add_floor(floor);
        b
    }

    #[test]
    fn commitment_is_stable() {
        let b = sample();
        let c1 = commit_building(&b).unwrap();
        let c2 = commit_building(&b).unwrap();
        assert_eq!(c1.merkle_root, c2.merkle_root);
        assert_eq!(c1.content_hash, c2.content_hash);
        assert_eq!(c1.building_id, b.id);
        assert!(c1.data_size > 0);
    }

    #[test]
    fn commitment_changes_when_model_changes() {
        let mut b = sample();
        let before = commit_building(&b).unwrap();
        b.floors[0].wings[0]
            .rooms
            .push(Room::new("Office".into(), RoomType::Office));
        let after = commit_building(&b).unwrap();
        assert_ne!(before.merkle_root, after.merkle_root);
    }
}
