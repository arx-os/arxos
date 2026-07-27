//! Device attestation hooks (Apple App Attest and mocks).
//!
//! Phase 5: Arxos records attestation *statements* as content-addressed
//! provenance. Verification of Apple's CBOR attestation objects happens on
//! a trusted verifier path; mobile clients supply the raw statement bytes.
//!
//! Offline / CI uses [`MockAttestationVerifier`].

use std::collections::BTreeMap;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::canonical::{cid_of, to_canonical_cbor};
use crate::cid::Cid;
use crate::crypto::{AuthorSignature, Keypair, PublicKey};
use crate::error::Result;
use crate::object::{Object, ObjectBody, ObjectHeader, ProvenanceBody, SCHEMA_VERSION};

/// Attestation provider identifier.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AttestationKind {
    /// Apple App Attest (iOS).
    AppAttest,
    /// Development / CI mock.
    Mock,
    /// Unspecified / future (Play Integrity, etc.).
    Other,
}

impl AttestationKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::AppAttest => "app_attest",
            Self::Mock => "mock",
            Self::Other => "other",
        }
    }
}

/// Portable attestation statement bound to a subject CID (usually a Root).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AttestationStatement {
    pub kind: AttestationKind,
    /// Subject object CID (root or contribution package).
    pub subject: Cid,
    /// Device / key identifier (App Attest keyId hex, mock id, …).
    pub device_id: String,
    /// Opaque provider payload (App Attest CBOR, mock token, …).
    pub statement: Vec<u8>,
    /// Optional environment: production | sandbox | development.
    pub environment: Option<String>,
    /// Unix seconds when the client produced the statement.
    pub created: u64,
    /// Optional client app identity (bundle id).
    pub app_id: Option<String>,
    pub properties: BTreeMap<String, String>,
}

impl AttestationStatement {
    pub fn mock(subject: Cid, device_id: impl Into<String>) -> Self {
        let device_id = device_id.into();
        Self {
            kind: AttestationKind::Mock,
            subject,
            statement: format!("mock-attest:{device_id}:{subject}").into_bytes(),
            device_id,
            environment: Some("development".into()),
            created: now_secs(),
            app_id: Some("dev.arxos.capture".into()),
            properties: BTreeMap::new(),
        }
    }

    pub fn app_attest(
        subject: Cid,
        key_id_hex: impl Into<String>,
        statement: Vec<u8>,
        environment: impl Into<String>,
        app_id: impl Into<String>,
    ) -> Self {
        Self {
            kind: AttestationKind::AppAttest,
            subject,
            device_id: key_id_hex.into(),
            statement,
            environment: Some(environment.into()),
            created: now_secs(),
            app_id: Some(app_id.into()),
            properties: BTreeMap::new(),
        }
    }

    pub fn cid(&self) -> Result<Cid> {
        cid_of(self)
    }

    /// Wrap as a Provenance object (optional author signature).
    pub fn into_provenance_object(self, keypair: Option<&Keypair>) -> Result<Object> {
        let mut props = self.properties.clone();
        props.insert("attest_kind".into(), self.kind.as_str().into());
        props.insert("device_id".into(), self.device_id.clone());
        if let Some(env) = &self.environment {
            props.insert("environment".into(), env.clone());
        }
        if let Some(app) = &self.app_id {
            props.insert("app_id".into(), app.clone());
        }
        // Embed raw statement as hex for CAS-friendly text properties + binary in evidence blob path.
        props.insert("statement_hex".into(), hex::encode(&self.statement));
        props.insert("statement_len".into(), self.statement.len().to_string());

        let body = ObjectBody::Provenance(ProvenanceBody {
            subject: self.subject,
            statement: format!(
                "device attestation kind={} device={}",
                self.kind.as_str(),
                self.device_id
            ),
            evidence: Vec::new(),
            properties: props,
        });
        let mut obj = Object {
            header: ObjectHeader {
                object_type: body.object_type(),
                schema_version: SCHEMA_VERSION,
                created: self.created,
                author: None,
                signature: None,
            },
            body,
        };
        if let Some(kp) = keypair {
            obj.sign(kp)?;
        }
        Ok(obj)
    }
}

/// Verification outcome for an attestation statement.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AttestationVerdict {
    pub valid: bool,
    pub kind: AttestationKind,
    pub device_id: String,
    pub detail: String,
}

/// Trait for provider-specific verification (Apple servers, mock, …).
pub trait AttestationVerifier: Send + Sync {
    fn verify(&self, statement: &AttestationStatement) -> Result<AttestationVerdict>;
}

/// Accepts only well-formed mock statements.
#[derive(Debug, Default, Clone)]
pub struct MockAttestationVerifier;

impl AttestationVerifier for MockAttestationVerifier {
    fn verify(&self, statement: &AttestationStatement) -> Result<AttestationVerdict> {
        if statement.kind != AttestationKind::Mock {
            return Ok(AttestationVerdict {
                valid: false,
                kind: statement.kind,
                device_id: statement.device_id.clone(),
                detail: "mock verifier rejects non-mock statements".into(),
            });
        }
        let expected = format!("mock-attest:{}:{}", statement.device_id, statement.subject);
        let ok = statement.statement == expected.as_bytes();
        Ok(AttestationVerdict {
            valid: ok,
            kind: statement.kind,
            device_id: statement.device_id.clone(),
            detail: if ok {
                "mock attestation ok".into()
            } else {
                "mock statement mismatch".into()
            },
        })
    }
}

/// App Attest verifier placeholder.
///
/// Production must validate the CBOR attestation object against Apple's App
/// Attest root certs and the expected `app_id` / challenge. Phase 5 ships
/// structural checks only so the pipeline is wired; do not treat as secure
/// production verification.
#[derive(Debug, Clone)]
pub struct AppAttestVerifier {
    pub expected_app_id: Option<String>,
    pub allow_empty_statement: bool,
}

impl Default for AppAttestVerifier {
    fn default() -> Self {
        Self {
            expected_app_id: None,
            allow_empty_statement: false,
        }
    }
}

impl AttestationVerifier for AppAttestVerifier {
    fn verify(&self, statement: &AttestationStatement) -> Result<AttestationVerdict> {
        if statement.kind != AttestationKind::AppAttest {
            return Ok(AttestationVerdict {
                valid: false,
                kind: statement.kind,
                device_id: statement.device_id.clone(),
                detail: "not an app_attest statement".into(),
            });
        }
        if statement.device_id.is_empty() {
            return Ok(AttestationVerdict {
                valid: false,
                kind: statement.kind,
                device_id: statement.device_id.clone(),
                detail: "missing App Attest keyId".into(),
            });
        }
        if statement.statement.is_empty() && !self.allow_empty_statement {
            return Ok(AttestationVerdict {
                valid: false,
                kind: statement.kind,
                device_id: statement.device_id.clone(),
                detail: "empty attestation object".into(),
            });
        }
        if let (Some(expected), Some(got)) = (&self.expected_app_id, &statement.app_id) {
            if expected != got {
                return Ok(AttestationVerdict {
                    valid: false,
                    kind: statement.kind,
                    device_id: statement.device_id.clone(),
                    detail: format!("app_id mismatch: expected {expected}, got {got}"),
                });
            }
        }
        // Structural pass only — full Apple chain verification is host-specific.
        Ok(AttestationVerdict {
            valid: true,
            kind: statement.kind,
            device_id: statement.device_id.clone(),
            detail: "structural app_attest checks passed (full chain verify not run)".into(),
        })
    }
}

/// Composite verifier: mock + app attest structural.
#[derive(Debug, Default, Clone)]
pub struct DefaultAttestationVerifier {
    pub mock: MockAttestationVerifier,
    pub app_attest: AppAttestVerifier,
}

impl AttestationVerifier for DefaultAttestationVerifier {
    fn verify(&self, statement: &AttestationStatement) -> Result<AttestationVerdict> {
        match statement.kind {
            AttestationKind::Mock => self.mock.verify(statement),
            AttestationKind::AppAttest => self.app_attest.verify(statement),
            AttestationKind::Other => Ok(AttestationVerdict {
                valid: false,
                kind: statement.kind,
                device_id: statement.device_id.clone(),
                detail: "unsupported attestation kind".into(),
            }),
        }
    }
}

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

/// Sign an attestation envelope for transport (not the Apple payload itself).
pub fn sign_statement(
    statement: &AttestationStatement,
    keypair: &Keypair,
) -> Result<(Vec<u8>, AuthorSignature)> {
    let bytes = to_canonical_cbor(statement)?;
    let sig = AuthorSignature::create(keypair, &bytes);
    Ok((bytes, sig))
}

pub fn verify_statement_signature(
    statement_bytes: &[u8],
    author: &PublicKey,
    signature: &crate::crypto::Signature,
) -> Result<()> {
    author.verify(statement_bytes, signature)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Cid;

    #[test]
    fn mock_attest_roundtrip() {
        let subject = Cid::from_canonical_bytes(b"root-subject");
        let stmt = AttestationStatement::mock(subject, "device-1");
        let v = MockAttestationVerifier.verify(&stmt).unwrap();
        assert!(v.valid);
        let obj = stmt.into_provenance_object(None).unwrap();
        assert_eq!(obj.header.object_type.as_str(), "provenance");
    }

    #[test]
    fn app_attest_structural() {
        let subject = Cid::from_canonical_bytes(b"root-2");
        let stmt = AttestationStatement::app_attest(
            subject,
            "aabbccdd",
            vec![1, 2, 3],
            "production",
            "dev.arxos.capture",
        );
        let v = AppAttestVerifier {
            expected_app_id: Some("dev.arxos.capture".into()),
            allow_empty_statement: false,
        }
        .verify(&stmt)
        .unwrap();
        assert!(v.valid);
    }
}
