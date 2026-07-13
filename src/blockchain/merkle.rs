//! Merkle Tree implementation for batch verification matching Solidity's schema.
//!
//! This module uses the `rs_merkle` crate to build a binary Merkle Tree where
//! nodes are hashed using Keccak256, and parent nodes are sorted before hashing
//! to ensure compatibility with OpenZeppelin's `MerkleProof.sol` contract helper.

use ethers::utils::keccak256;
use rs_merkle::{Hasher, MerkleProof, MerkleTree};

/// Custom Hasher wrapper implementing Keccak256 for `rs_merkle`.
/// Automatically sorts pair hashes before concatenating and hashing
/// to guarantee compatibility with OpenZeppelin on-chain verifiers.
#[derive(Clone)]
pub struct Keccak256Algorithm;

impl Hasher for Keccak256Algorithm {
    type Hash = [u8; 32];

    fn hash(data: &[u8]) -> [u8; 32] {
        keccak256(data)
    }

    fn concat_and_hash(left: &Self::Hash, right: Option<&Self::Hash>) -> Self::Hash {
        match right {
            Some(right_val) => {
                let mut a = *left;
                let mut b = *right_val;
                // Sort hashes to match OpenZeppelin's sorted pairs logic
                if a > b {
                    std::mem::swap(&mut a, &mut b);
                }
                let mut concat = [0u8; 64];
                concat[..32].copy_from_slice(&a);
                concat[32..].copy_from_slice(&b);
                keccak256(concat)
            }
            None => *left,
        }
    }
}

pub struct ArxMerkleTree {
    tree: MerkleTree<Keccak256Algorithm>,
}

impl ArxMerkleTree {
    /// Build a binary Merkle Tree from a list of leaves raw bytes
    pub fn build_tree(leaves_data: &[Vec<u8>]) -> Self {
        let leaves: Vec<[u8; 32]> = leaves_data
            .iter()
            .map(|data| Keccak256Algorithm::hash(data))
            .collect();
        let tree = MerkleTree::<Keccak256Algorithm>::from_leaves(&leaves);
        Self { tree }
    }

    /// Get the root of the Merkle Tree
    pub fn get_root(&self) -> Option<[u8; 32]> {
        self.tree.root()
    }

    /// Generate an inclusion proof for a list of indices
    pub fn generate_proof(&self, indices: &[usize]) -> Vec<u8> {
        self.tree.proof(indices).to_bytes()
    }

    /// Verify an inclusion proof against a root and leaf hashes
    pub fn verify_proof(
        root: [u8; 32],
        proof_bytes: &[u8],
        indices: &[usize],
        leaves: &[[u8; 32]],
        total_leaves_count: usize,
    ) -> bool {
        if let Ok(proof) = MerkleProof::<Keccak256Algorithm>::from_bytes(proof_bytes) {
            proof.verify(root, indices, leaves, total_leaves_count)
        } else {
            false
        }
    }
}
