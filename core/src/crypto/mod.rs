//! Cryptographic primitives: ed25519 keys and signatures.

use std::fmt;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::Path;
use std::str::FromStr;

use ed25519_dalek::{Signature as DalekSignature, Signer, SigningKey, Verifier, VerifyingKey};
use rand::rngs::OsRng;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use zeroize::{Zeroize, ZeroizeOnDrop, Zeroizing};

use crate::error::{Error, Result};

/// ed25519 public key (32 bytes).
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct PublicKey([u8; 32]);

/// ed25519 private/signing key (32-byte seed).
///
/// Not `Clone`. Memory is wiped on drop (`ZeroizeOnDrop`).
pub struct SecretKey(SigningKey);

impl Zeroize for SecretKey {
    fn zeroize(&mut self) {
        // ed25519-dalek 2's SigningKey is ZeroizeOnDrop but does not impl Zeroize.
        // Replace so the previous key is dropped (and wiped) immediately.
        self.0 = SigningKey::from_bytes(&[0u8; 32]);
    }
}

impl Drop for SecretKey {
    fn drop(&mut self) {
        self.zeroize();
    }
}

impl ZeroizeOnDrop for SecretKey {}

/// ed25519 signature (64 bytes).
#[derive(Clone, Copy, PartialEq, Eq, Hash)]
pub struct Signature([u8; 64]);

/// A signing identity: secret + derived public key.
///
/// Not `Clone` — sign with `&Keypair`. Reconstruct from a seed only when an
/// owned copy is required (tests / seed-file install). The secret is wiped on drop.
pub struct Keypair {
    secret: SecretKey,
    public: PublicKey,
}

impl Zeroize for Keypair {
    fn zeroize(&mut self) {
        self.secret.zeroize();
    }
}

impl Drop for Keypair {
    fn drop(&mut self) {
        self.zeroize();
    }
}

impl ZeroizeOnDrop for Keypair {}

impl PublicKey {
    pub fn from_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }

    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }

    pub fn to_hex(&self) -> String {
        hex::encode(self.0)
    }

    fn verifying_key(&self) -> Result<VerifyingKey> {
        VerifyingKey::from_bytes(&self.0)
            .map_err(|e| Error::Crypto(format!("invalid public key: {e}")))
    }

    /// Verify a signature over `message`.
    pub fn verify(&self, message: &[u8], signature: &Signature) -> Result<()> {
        let vk = self.verifying_key()?;
        let sig = DalekSignature::from_bytes(&signature.0);
        vk.verify(message, &sig)
            .map_err(|e| Error::Signature(format!("verification failed: {e}")))
    }
}

impl fmt::Display for PublicKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "ed25519:{}", self.to_hex())
    }
}

impl fmt::Debug for PublicKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "PublicKey({})", self)
    }
}

impl FromStr for PublicKey {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self> {
        let hex_part = s
            .strip_prefix("ed25519:")
            .unwrap_or(s);
        let bytes = hex::decode(hex_part)
            .map_err(|e| Error::Crypto(format!("invalid public key hex: {e}")))?;
        if bytes.len() != 32 {
            return Err(Error::Crypto(format!(
                "public key must be 32 bytes, got {}",
                bytes.len()
            )));
        }
        let mut arr = [0u8; 32];
        arr.copy_from_slice(&bytes);
        Ok(PublicKey(arr))
    }
}

impl Serialize for PublicKey {
    fn serialize<S: Serializer>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error> {
        if serializer.is_human_readable() {
            serializer.serialize_str(&self.to_string())
        } else {
            serializer.serialize_bytes(&self.0)
        }
    }
}

impl<'de> Deserialize<'de> for PublicKey {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> std::result::Result<Self, D::Error> {
        use serde::de::{self, Visitor};

        struct PkVisitor;

        impl<'de> Visitor<'de> for PkVisitor {
            type Value = PublicKey;

            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("ed25519 public key bytes or string")
            }

            fn visit_bytes<E: de::Error>(self, v: &[u8]) -> std::result::Result<PublicKey, E> {
                if v.len() != 32 {
                    return Err(E::custom("public key must be 32 bytes"));
                }
                let mut arr = [0u8; 32];
                arr.copy_from_slice(v);
                Ok(PublicKey(arr))
            }

            fn visit_str<E: de::Error>(self, v: &str) -> std::result::Result<PublicKey, E> {
                PublicKey::from_str(v).map_err(E::custom)
            }
        }

        if deserializer.is_human_readable() {
            deserializer.deserialize_str(PkVisitor)
        } else {
            deserializer.deserialize_bytes(PkVisitor)
        }
    }
}

impl Signature {
    pub fn from_bytes(bytes: [u8; 64]) -> Self {
        Self(bytes)
    }

    pub fn as_bytes(&self) -> &[u8; 64] {
        &self.0
    }

    pub fn to_hex(&self) -> String {
        hex::encode(self.0)
    }
}

impl fmt::Display for Signature {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "sig:{}", self.to_hex())
    }
}

impl fmt::Debug for Signature {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Signature({})", self)
    }
}

impl Serialize for Signature {
    fn serialize<S: Serializer>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error> {
        if serializer.is_human_readable() {
            serializer.serialize_str(&self.to_hex())
        } else {
            serializer.serialize_bytes(&self.0)
        }
    }
}

impl<'de> Deserialize<'de> for Signature {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> std::result::Result<Self, D::Error> {
        use serde::de::{self, Visitor};

        struct SigVisitor;

        impl<'de> Visitor<'de> for SigVisitor {
            type Value = Signature;

            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("ed25519 signature bytes or hex")
            }

            fn visit_bytes<E: de::Error>(self, v: &[u8]) -> std::result::Result<Signature, E> {
                if v.len() != 64 {
                    return Err(E::custom("signature must be 64 bytes"));
                }
                let mut arr = [0u8; 64];
                arr.copy_from_slice(v);
                Ok(Signature(arr))
            }

            fn visit_str<E: de::Error>(self, v: &str) -> std::result::Result<Signature, E> {
                let hex_part = v.strip_prefix("sig:").unwrap_or(v);
                let bytes = hex::decode(hex_part).map_err(E::custom)?;
                if bytes.len() != 64 {
                    return Err(E::custom("signature must be 64 bytes"));
                }
                let mut arr = [0u8; 64];
                arr.copy_from_slice(&bytes);
                Ok(Signature(arr))
            }
        }

        if deserializer.is_human_readable() {
            deserializer.deserialize_str(SigVisitor)
        } else {
            deserializer.deserialize_bytes(SigVisitor)
        }
    }
}

impl Keypair {
    /// Generate a new random keypair.
    pub fn generate() -> Self {
        let secret = SigningKey::generate(&mut OsRng);
        let public = PublicKey(*secret.verifying_key().as_bytes());
        Self {
            secret: SecretKey(secret),
            public,
        }
    }

    /// Reconstruct from a 32-byte seed.
    ///
    /// The input array is zeroized before this function returns. Callers that
    /// still hold another copy should wrap it in [`Zeroizing`].
    pub fn from_seed(mut seed: [u8; 32]) -> Self {
        let secret = SigningKey::from_bytes(&seed);
        let public = PublicKey(*secret.verifying_key().as_bytes());
        seed.zeroize();
        Self {
            secret: SecretKey(secret),
            public,
        }
    }

    pub fn public_key(&self) -> PublicKey {
        self.public
    }

    /// Export the 32-byte seed into a zeroizing buffer (wiped on drop).
    ///
    /// This is an explicit export. Prefer signing with `&Keypair` instead of
    /// copying the seed.
    pub fn seed(&self) -> Zeroizing<[u8; 32]> {
        Zeroizing::new(self.secret.0.to_bytes())
    }

    /// Sign an arbitrary message.
    pub fn sign(&self, message: &[u8]) -> Signature {
        let sig = self.secret.0.sign(message);
        Signature(sig.to_bytes())
    }
}

/// An author signature: who signed + the signature bytes.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuthorSignature {
    pub public_key: PublicKey,
    pub signature: Signature,
}

/// Write `bytes` to `path`, creating the file with mode `0o600` on Unix so
/// there is no world-readable window before chmod.
pub fn write_secret_bytes(path: &Path, bytes: &[u8]) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let mut opts = OpenOptions::new();
    opts.write(true).create(true).truncate(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        opts.mode(0o600);
    }
    let mut file = opts
        .open(path)
        .map_err(|e| Error::Crypto(format!("open secret file {}: {e}", path.display())))?;
    file.write_all(bytes)
        .map_err(|e| Error::Crypto(format!("write secret file {}: {e}", path.display())))?;
    file.sync_all()
        .map_err(|e| Error::Crypto(format!("sync secret file {}: {e}", path.display())))?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = fs::set_permissions(path, fs::Permissions::from_mode(0o600));
    }
    Ok(())
}

/// Read a 32-byte seed file into a zeroizing buffer.
pub fn read_secret_32(path: &Path) -> Result<Zeroizing<[u8; 32]>> {
    let bytes = Zeroizing::new(
        fs::read(path).map_err(|e| Error::Crypto(format!("read secret file {}: {e}", path.display())))?,
    );
    if bytes.len() != 32 {
        return Err(Error::Crypto(format!(
            "seed must be 32 bytes, got {}",
            bytes.len()
        )));
    }
    let mut seed = Zeroizing::new([0u8; 32]);
    seed.copy_from_slice(&bytes);
    Ok(seed)
}

impl AuthorSignature {
    pub fn create(keypair: &Keypair, message: &[u8]) -> Self {
        Self {
            public_key: keypair.public_key(),
            signature: keypair.sign(message),
        }
    }

    pub fn verify(&self, message: &[u8]) -> Result<()> {
        self.public_key.verify(message, &self.signature)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sign_verify_roundtrip() {
        let kp = Keypair::generate();
        let msg = b"arxos phase 0";
        let sig = kp.sign(msg);
        kp.public_key().verify(msg, &sig).unwrap();
        assert!(kp.public_key().verify(b"tampered", &sig).is_err());
    }

    #[test]
    fn seed_roundtrip() {
        let kp = Keypair::generate();
        let seed = kp.seed();
        let kp2 = Keypair::from_seed(*seed);
        assert_eq!(kp.public_key(), kp2.public_key());
    }

    #[test]
    fn secret_types_are_zeroize_on_drop() {
        fn assert_zod<T: ZeroizeOnDrop>() {}
        assert_zod::<SecretKey>();
        assert_zod::<Keypair>();
        assert_zod::<Zeroizing<[u8; 32]>>();
    }

    #[test]
    fn write_secret_file_is_owner_rw_only() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("device.seed");
        let kp = Keypair::generate();
        let seed = kp.seed();
        write_secret_bytes(&path, seed.as_ref()).unwrap();
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let mode = std::fs::metadata(&path).unwrap().permissions().mode() & 0o777;
            assert_eq!(mode, 0o600, "seed file must be 0o600, got {mode:#o}");
        }
        let loaded = read_secret_32(&path).unwrap();
        assert_eq!(&*loaded, seed.as_ref());
    }
}
