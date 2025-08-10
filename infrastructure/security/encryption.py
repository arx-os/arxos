"""
Enterprise Data Encryption and Security Utilities.

Provides encryption/decryption services, secure key management,
and data protection utilities following cryptographic best practices.
"""

import os
import base64
import secrets
import hashlib
from typing import Dict, Any, Optional, Union, Tuple, List
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timezone
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization, padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

from infrastructure.logging.structured_logging import get_logger, security_logger
from infrastructure.error_handling import SecurityError


logger = get_logger(__name__)


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms."""
    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"
    CHACHA20_POLY1305 = "chacha20-poly1305"
    FERNET = "fernet"  # Symmetric encryption with built-in authentication


class KeyDerivationFunction(Enum):
    """Key derivation functions."""
    PBKDF2 = "pbkdf2"
    SCRYPT = "scrypt"
    ARGON2 = "argon2"


@dataclass
class EncryptionMetadata:
    """Metadata for encrypted data."""
    algorithm: EncryptionAlgorithm
    key_id: str
    iv: Optional[bytes]
    salt: Optional[bytes]
    created_at: datetime
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "algorithm": self.algorithm.value,
            "key_id": self.key_id,
            "iv": base64.b64encode(self.iv).decode('utf-8') if self.iv else None,
            "salt": base64.b64encode(self.salt).decode('utf-8') if self.salt else None,
            "created_at": self.created_at.isoformat(),
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EncryptionMetadata':
        """Create from dictionary."""
        return cls(
            algorithm=EncryptionAlgorithm(data["algorithm"]),
            key_id=data["key_id"],
            iv=base64.b64decode(data["iv"]) if data.get("iv") else None,
            salt=base64.b64decode(data["salt"]) if data.get("salt") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            version=data.get("version", "1.0")
        )


class SecureKeyManager:
    """Secure key management system."""
    
    def __init__(self, master_key: Optional[bytes] = None):
        """Initialize key manager with optional master key."""
        self.master_key = master_key or self._generate_master_key()
        self.keys = {}  # In production, use secure key store (HSM, AWS KMS, etc.)
        self.key_rotation_interval = 86400 * 90  # 90 days
    
    def _generate_master_key(self) -> bytes:
        """Generate cryptographically secure master key."""
        return secrets.token_bytes(32)  # 256 bits
    
    def generate_key(self, key_id: str, algorithm: EncryptionAlgorithm) -> bytes:
        """Generate and store encryption key."""
        if algorithm in [EncryptionAlgorithm.AES_256_GCM, EncryptionAlgorithm.AES_256_CBC]:
            key = secrets.token_bytes(32)  # 256 bits
        elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
            key = secrets.token_bytes(32)  # 256 bits
        elif algorithm == EncryptionAlgorithm.FERNET:
            key = Fernet.generate_key()
        else:
            raise SecurityError(f"Unsupported algorithm: {algorithm}")
        
        # Encrypt key with master key before storage
        encrypted_key = self._encrypt_key_with_master(key)
        
        self.keys[key_id] = {
            "encrypted_key": encrypted_key,
            "algorithm": algorithm,
            "created_at": datetime.now(timezone.utc),
            "version": 1,
            "is_active": True
        }
        
        security_logger.log_security_event(
            event_type="encryption_key_generated",
            details={
                "key_id": key_id,
                "algorithm": algorithm.value,
                "key_length_bits": len(key) * 8
            }
        )
        
        return key
    
    def get_key(self, key_id: str) -> Optional[bytes]:
        """Retrieve and decrypt key."""
        if key_id not in self.keys:
            return None
        
        key_data = self.keys[key_id]
        if not key_data["is_active"]:
            return None
        
        # Decrypt key with master key
        return self._decrypt_key_with_master(key_data["encrypted_key"])
    
    def rotate_key(self, key_id: str) -> bytes:
        """Rotate encryption key."""
        if key_id not in self.keys:
            raise SecurityError(f"Key {key_id} not found")
        
        old_key_data = self.keys[key_id]
        algorithm = old_key_data["algorithm"]
        
        # Generate new key
        new_key = self.generate_key(f"{key_id}_v{old_key_data['version'] + 1}", algorithm)
        
        # Deactivate old key
        old_key_data["is_active"] = False
        old_key_data["rotated_at"] = datetime.now(timezone.utc)
        
        security_logger.log_security_event(
            event_type="encryption_key_rotated",
            details={"key_id": key_id, "old_version": old_key_data["version"]}
        )
        
        return new_key
    
    def _encrypt_key_with_master(self, key: bytes) -> bytes:
        """Encrypt key with master key."""
        f = Fernet(base64.urlsafe_b64encode(self.master_key))
        return f.encrypt(key)
    
    def _decrypt_key_with_master(self, encrypted_key: bytes) -> bytes:
        """Decrypt key with master key."""
        f = Fernet(base64.urlsafe_b64encode(self.master_key))
        return f.decrypt(encrypted_key)


class DataEncryption:
    """High-level data encryption service."""
    
    def __init__(self, key_manager: SecureKeyManager):
        self.key_manager = key_manager
        self.default_algorithm = EncryptionAlgorithm.AES_256_GCM
    
    def encrypt(self, data: Union[str, bytes], key_id: str, 
               algorithm: Optional[EncryptionAlgorithm] = None) -> Tuple[bytes, EncryptionMetadata]:
        """Encrypt data with specified algorithm."""
        algorithm = algorithm or self.default_algorithm
        
        # Convert string to bytes
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Get encryption key
        key = self.key_manager.get_key(key_id)
        if not key:
            # Generate new key if it doesn't exist
            key = self.key_manager.generate_key(key_id, algorithm)
        
        # Encrypt based on algorithm
        if algorithm == EncryptionAlgorithm.AES_256_GCM:
            encrypted_data, iv = self._encrypt_aes_gcm(data, key)
            metadata = EncryptionMetadata(
                algorithm=algorithm,
                key_id=key_id,
                iv=iv,
                salt=None,
                created_at=datetime.now(timezone.utc)
            )
        elif algorithm == EncryptionAlgorithm.AES_256_CBC:
            encrypted_data, iv = self._encrypt_aes_cbc(data, key)
            metadata = EncryptionMetadata(
                algorithm=algorithm,
                key_id=key_id,
                iv=iv,
                salt=None,
                created_at=datetime.now(timezone.utc)
            )
        elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
            encrypted_data, nonce = self._encrypt_chacha20_poly1305(data, key)
            metadata = EncryptionMetadata(
                algorithm=algorithm,
                key_id=key_id,
                iv=nonce,
                salt=None,
                created_at=datetime.now(timezone.utc)
            )
        elif algorithm == EncryptionAlgorithm.FERNET:
            encrypted_data = self._encrypt_fernet(data, key)
            metadata = EncryptionMetadata(
                algorithm=algorithm,
                key_id=key_id,
                iv=None,
                salt=None,
                created_at=datetime.now(timezone.utc)
            )
        else:
            raise SecurityError(f"Unsupported encryption algorithm: {algorithm}")
        
        security_logger.log_security_event(
            event_type="data_encrypted",
            details={
                "algorithm": algorithm.value,
                "key_id": key_id,
                "data_size_bytes": len(data)
            }
        )
        
        return encrypted_data, metadata
    
    def decrypt(self, encrypted_data: bytes, metadata: EncryptionMetadata) -> bytes:
        """Decrypt data using metadata."""
        # Get decryption key
        key = self.key_manager.get_key(metadata.key_id)
        if not key:
            raise SecurityError(f"Encryption key {metadata.key_id} not found")
        
        # Decrypt based on algorithm
        try:
            if metadata.algorithm == EncryptionAlgorithm.AES_256_GCM:
                decrypted_data = self._decrypt_aes_gcm(encrypted_data, key, metadata.iv)
            elif metadata.algorithm == EncryptionAlgorithm.AES_256_CBC:
                decrypted_data = self._decrypt_aes_cbc(encrypted_data, key, metadata.iv)
            elif metadata.algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
                decrypted_data = self._decrypt_chacha20_poly1305(encrypted_data, key, metadata.iv)
            elif metadata.algorithm == EncryptionAlgorithm.FERNET:
                decrypted_data = self._decrypt_fernet(encrypted_data, key)
            else:
                raise SecurityError(f"Unsupported decryption algorithm: {metadata.algorithm}")
            
            security_logger.log_security_event(
                event_type="data_decrypted",
                details={
                    "algorithm": metadata.algorithm.value,
                    "key_id": metadata.key_id,
                    "data_size_bytes": len(decrypted_data)
                }
            )
            
            return decrypted_data
            
        except Exception as e:
            security_logger.log_security_event(
                event_type="decryption_failed",
                details={
                    "algorithm": metadata.algorithm.value,
                    "key_id": metadata.key_id,
                    "error": str(e)
                }
            )
            raise SecurityError(f"Decryption failed: {str(e)}")
    
    def _encrypt_aes_gcm(self, data: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """Encrypt with AES-256-GCM."""
        iv = secrets.token_bytes(12)  # 96-bit IV for GCM
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return ciphertext + encryptor.tag, iv
    
    def _decrypt_aes_gcm(self, encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
        """Decrypt with AES-256-GCM."""
        ciphertext = encrypted_data[:-16]  # Remove tag
        tag = encrypted_data[-16:]  # Last 16 bytes are tag
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    def _encrypt_aes_cbc(self, data: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """Encrypt with AES-256-CBC."""
        iv = secrets.token_bytes(16)  # 128-bit IV
        
        # Apply PKCS7 padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return ciphertext, iv
    
    def _decrypt_aes_cbc(self, encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
        """Decrypt with AES-256-CBC."""
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Remove PKCS7 padding
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(padded_data) + unpadder.finalize()
    
    def _encrypt_chacha20_poly1305(self, data: bytes, key: bytes) -> Tuple[bytes, bytes]:
        """Encrypt with ChaCha20-Poly1305."""
        nonce = secrets.token_bytes(12)  # 96-bit nonce
        cipher = Cipher(algorithms.ChaCha20(key, nonce), None, backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return ciphertext, nonce
    
    def _decrypt_chacha20_poly1305(self, encrypted_data: bytes, key: bytes, nonce: bytes) -> bytes:
        """Decrypt with ChaCha20-Poly1305."""
        cipher = Cipher(algorithms.ChaCha20(key, nonce), None, backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(encrypted_data) + decryptor.finalize()
    
    def _encrypt_fernet(self, data: bytes, key: bytes) -> bytes:
        """Encrypt with Fernet (includes authentication)."""
        f = Fernet(key)
        return f.encrypt(data)
    
    def _decrypt_fernet(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Decrypt with Fernet."""
        f = Fernet(key)
        return f.decrypt(encrypted_data)


class AsymmetricEncryption:
    """RSA asymmetric encryption for key exchange and secure communication."""
    
    @staticmethod
    def generate_key_pair(key_size: int = 2048) -> Tuple[bytes, bytes]:
        """Generate RSA key pair."""
        if key_size < 2048:
            raise SecurityError("RSA key size must be at least 2048 bits")
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        security_logger.log_security_event(
            event_type="rsa_key_pair_generated",
            details={"key_size_bits": key_size}
        )
        
        return private_pem, public_pem
    
    @staticmethod
    def encrypt_with_public_key(data: bytes, public_key_pem: bytes) -> bytes:
        """Encrypt data with RSA public key."""
        public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
        
        # RSA encryption with OAEP padding
        encrypted = public_key.encrypt(
            data,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return encrypted
    
    @staticmethod
    def decrypt_with_private_key(encrypted_data: bytes, private_key_pem: bytes) -> bytes:
        """Decrypt data with RSA private key."""
        private_key = serialization.load_pem_private_key(
            private_key_pem, 
            password=None, 
            backend=default_backend()
        )
        
        # RSA decryption with OAEP padding
        decrypted = private_key.decrypt(
            encrypted_data,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted


class SecureHasher:
    """Secure hashing utilities."""
    
    @staticmethod
    def hash_sha256(data: Union[str, bytes], salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Hash data with SHA-256."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if salt is None:
            salt = secrets.token_bytes(32)
        
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(salt)
        digest.update(data)
        hash_value = digest.finalize()
        
        return hash_value, salt
    
    @staticmethod
    def derive_key_pbkdf2(password: str, salt: Optional[bytes] = None, 
                         iterations: int = 100000, key_length: int = 32) -> Tuple[bytes, bytes]:
        """Derive key using PBKDF2."""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
    
    @staticmethod
    def derive_key_scrypt(password: str, salt: Optional[bytes] = None,
                         n: int = 2**14, r: int = 8, p: int = 1, 
                         key_length: int = 32) -> Tuple[bytes, bytes]:
        """Derive key using Scrypt."""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = Scrypt(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            n=n, r=r, p=p,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode('utf-8'))
        return key, salt


class FieldLevelEncryption:
    """Field-level encryption for database columns."""
    
    def __init__(self, data_encryption: DataEncryption):
        self.data_encryption = data_encryption
        self.field_key_prefix = "field_"
    
    def encrypt_field(self, field_name: str, value: Any, 
                     context_id: str = "default") -> Tuple[str, Dict[str, Any]]:
        """Encrypt a specific field value."""
        if value is None:
            return None, None
        
        # Serialize value
        if isinstance(value, (dict, list)):
            serialized_value = json.dumps(value, default=str)
        else:
            serialized_value = str(value)
        
        # Generate field-specific key ID
        key_id = f"{self.field_key_prefix}{field_name}_{context_id}"
        
        # Encrypt value
        encrypted_data, metadata = self.data_encryption.encrypt(
            serialized_value, 
            key_id,
            EncryptionAlgorithm.AES_256_GCM
        )
        
        # Encode encrypted data for storage
        encoded_data = base64.b64encode(encrypted_data).decode('utf-8')
        
        return encoded_data, metadata.to_dict()
    
    def decrypt_field(self, encrypted_value: str, metadata_dict: Dict[str, Any]) -> Any:
        """Decrypt a field value."""
        if encrypted_value is None or metadata_dict is None:
            return None
        
        # Decode encrypted data
        encrypted_data = base64.b64decode(encrypted_value.encode('utf-8'))
        
        # Recreate metadata
        metadata = EncryptionMetadata.from_dict(metadata_dict)
        
        # Decrypt value
        decrypted_data = self.data_encryption.decrypt(encrypted_data, metadata)
        
        # Deserialize value
        decrypted_str = decrypted_data.decode('utf-8')
        
        # Try to parse as JSON first
        try:
            return json.loads(decrypted_str)
        except json.JSONDecodeError:
            return decrypted_str


class EncryptionService:
    """Main encryption service facade."""
    
    def __init__(self, master_key: Optional[bytes] = None):
        self.key_manager = SecureKeyManager(master_key)
        self.data_encryption = DataEncryption(self.key_manager)
        self.field_encryption = FieldLevelEncryption(self.data_encryption)
        self.asymmetric = AsymmetricEncryption()
        self.hasher = SecureHasher()
    
    def encrypt_sensitive_data(self, data: Dict[str, Any], 
                             sensitive_fields: List[str]) -> Dict[str, Any]:
        """Encrypt sensitive fields in a data dictionary."""
        encrypted_data = data.copy()
        encryption_metadata = {}
        
        for field_name in sensitive_fields:
            if field_name in data:
                encrypted_value, metadata = self.field_encryption.encrypt_field(
                    field_name, 
                    data[field_name]
                )
                
                encrypted_data[field_name] = encrypted_value
                encryption_metadata[f"{field_name}_metadata"] = metadata
        
        encrypted_data["_encryption_metadata"] = encryption_metadata
        return encrypted_data
    
    def decrypt_sensitive_data(self, encrypted_data: Dict[str, Any], 
                             sensitive_fields: List[str]) -> Dict[str, Any]:
        """Decrypt sensitive fields in a data dictionary."""
        decrypted_data = encrypted_data.copy()
        encryption_metadata = encrypted_data.get("_encryption_metadata", {})
        
        for field_name in sensitive_fields:
            if field_name in encrypted_data:
                metadata_key = f"{field_name}_metadata"
                if metadata_key in encryption_metadata:
                    decrypted_value = self.field_encryption.decrypt_field(
                        encrypted_data[field_name],
                        encryption_metadata[metadata_key]
                    )
                    decrypted_data[field_name] = decrypted_value
        
        # Remove metadata from final result
        if "_encryption_metadata" in decrypted_data:
            del decrypted_data["_encryption_metadata"]
        
        return decrypted_data
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token."""
        return secrets.token_urlsafe(length)
    
    def constant_time_compare(self, a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks."""
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0