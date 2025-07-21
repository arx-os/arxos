"""
Encryption Services for Arxos.

This module provides comprehensive encryption capabilities including:
- AES-256 encryption for data at rest
- TLS 1.3 support for data in transit
- Key management and rotation
- Certificate management
"""

import base64
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union, List
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography import x509
from cryptography.x509.oid import NameOID
import os


class EncryptionService:
    """AES-256 encryption service for data protection."""
    
    def __init__(self, key_size: int = 32):
        self.key_size = key_size  # 32 bytes = 256 bits
        self.algorithm = algorithms.AES
        self.mode = modes.GCM
        
    def generate_key(self) -> bytes:
        """Generate a random AES-256 key."""
        return secrets.token_bytes(self.key_size)
    
    def derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_size,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())
    
    def encrypt_data(self, data: Union[str, bytes], key: bytes) -> Dict[str, bytes]:
        """Encrypt data using AES-256-GCM."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Generate random IV
        iv = secrets.token_bytes(12)  # 96 bits for GCM
        
        # Create cipher
        cipher = Cipher(self.algorithm(key), self.mode(iv))
        encryptor = cipher.encryptor()
        
        # Encrypt data
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return {
            'ciphertext': ciphertext,
            'iv': iv,
            'tag': encryptor.tag
        }
    
    def decrypt_data(self, encrypted_data: Dict[str, bytes], key: bytes) -> bytes:
        """Decrypt data using AES-256-GCM."""
        ciphertext = encrypted_data['ciphertext']
        iv = encrypted_data['iv']
        tag = encrypted_data['tag']
        
        # Create cipher
        cipher = Cipher(self.algorithm(key), self.mode(iv, tag))
        decryptor = cipher.decryptor()
        
        # Decrypt data
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext
    
    def encrypt_file(self, file_path: str, key: bytes) -> str:
        """Encrypt a file and return the encrypted file path."""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = self.encrypt_data(data, key)
        
        # Save encrypted data
        encrypted_file_path = f"{file_path}.encrypted"
        with open(encrypted_file_path, 'wb') as f:
            f.write(encrypted_data['ciphertext'])
            f.write(encrypted_data['iv'])
            f.write(encrypted_data['tag'])
        
        return encrypted_file_path
    
    def decrypt_file(self, encrypted_file_path: str, key: bytes) -> bytes:
        """Decrypt a file and return the plaintext data."""
        with open(encrypted_file_path, 'rb') as f:
            data = f.read()
        
        # Extract components
        tag_size = 16  # GCM tag size
        iv_size = 12   # GCM IV size
        
        ciphertext = data[:-tag_size-iv_size]
        iv = data[-tag_size-iv_size:-tag_size]
        tag = data[-tag_size:]
        
        encrypted_data = {
            'ciphertext': ciphertext,
            'iv': iv,
            'tag': tag
        }
        
        return self.decrypt_data(encrypted_data, key)


class KeyManagementService:
    """Key management service with rotation and storage."""
    
    def __init__(self, storage_path: str = "keys/"):
        self.storage_path = storage_path
        self.keys = {}
        self.key_metadata = {}
        os.makedirs(storage_path, exist_ok=True)
    
    def generate_key_pair(self, key_id: str) -> Dict[str, bytes]:
        """Generate RSA key pair for asymmetric encryption."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Store keys
        self.keys[key_id] = {
            'private_key': private_pem,
            'public_key': public_pem,
            'created_at': datetime.utcnow()
        }
        
        return {
            'private_key': private_pem,
            'public_key': public_pem
        }
    
    def store_key(self, key_id: str, key_data: bytes, key_type: str = "aes"):
        """Store a key with metadata."""
        key_file = os.path.join(self.storage_path, f"{key_id}.key")
        
        # Encrypt key data before storage
        master_key = self._get_master_key()
        encryption_service = EncryptionService()
        encrypted_key = encryption_service.encrypt_data(key_data, master_key)
        
        # Store encrypted key
        with open(key_file, 'wb') as f:
            f.write(encrypted_key['ciphertext'])
            f.write(encrypted_key['iv'])
            f.write(encrypted_key['tag'])
        
        # Store metadata
        self.key_metadata[key_id] = {
            'type': key_type,
            'created_at': datetime.utcnow(),
            'last_used': None,
            'rotation_date': datetime.utcnow() + timedelta(days=90)
        }
    
    def retrieve_key(self, key_id: str) -> Optional[bytes]:
        """Retrieve a key from storage."""
        key_file = os.path.join(self.storage_path, f"{key_id}.key")
        
        if not os.path.exists(key_file):
            return None
        
        # Read encrypted key
        with open(key_file, 'rb') as f:
            data = f.read()
        
        # Extract components
        tag_size = 16
        iv_size = 12
        
        ciphertext = data[:-tag_size-iv_size]
        iv = data[-tag_size-iv_size:-tag_size]
        tag = data[-tag_size:]
        
        encrypted_key = {
            'ciphertext': ciphertext,
            'iv': iv,
            'tag': tag
        }
        
        # Decrypt key
        master_key = self._get_master_key()
        encryption_service = EncryptionService()
        key_data = encryption_service.decrypt_data(encrypted_key, master_key)
        
        # Update metadata
        if key_id in self.key_metadata:
            self.key_metadata[key_id]['last_used'] = datetime.utcnow()
        
        return key_data
    
    def rotate_key(self, key_id: str) -> str:
        """Rotate a key and return the new key ID."""
        # Generate new key
        encryption_service = EncryptionService()
        new_key = encryption_service.generate_key()
        
        # Create new key ID
        new_key_id = f"{key_id}_v{int(datetime.utcnow().timestamp())}"
        
        # Store new key
        self.store_key(new_key_id, new_key)
        
        # Mark old key for deletion
        if key_id in self.key_metadata:
            self.key_metadata[key_id]['scheduled_for_deletion'] = datetime.utcnow() + timedelta(days=30)
        
        return new_key_id
    
    def _get_master_key(self) -> bytes:
        """Get or generate master key for key encryption."""
        master_key_file = os.path.join(self.storage_path, "master.key")
        
        if os.path.exists(master_key_file):
            with open(master_key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new master key
            master_key = secrets.token_bytes(32)
            with open(master_key_file, 'wb') as f:
                f.write(master_key)
            return master_key


class CertificateService:
    """Certificate management for TLS and digital signatures."""
    
    def __init__(self):
        self.certificates = {}
    
    def generate_self_signed_certificate(self, common_name: str, days_valid: int = 365) -> x509.Certificate:
        """Generate a self-signed certificate."""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=days_valid)
        ).sign(private_key, hashes.SHA256())
        
        return cert
    
    def verify_certificate(self, cert: x509.Certificate, ca_cert: x509.Certificate) -> bool:
        """Verify a certificate against a CA certificate."""
        try:
            ca_cert.public_key().verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                cert.signature_hash_algorithm
            )
            return True
        except Exception:
            return False
    
    def create_certificate_signing_request(self, common_name: str) -> x509.CertificateSigningRequest:
        """Create a certificate signing request."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])
        
        csr = x509.CertificateSigningRequestBuilder().subject_name(
            subject
        ).sign(private_key, hashes.SHA256())
        
        return csr


class TLSService:
    """TLS 1.3 service for secure communications."""
    
    def __init__(self):
        self.supported_ciphers = [
            'TLS_AES_256_GCM_SHA384',
            'TLS_CHACHA20_POLY1305_SHA256',
            'TLS_AES_128_GCM_SHA256'
        ]
    
    def create_tls_context(self, cert_file: str, key_file: str) -> Dict[str, Any]:
        """Create TLS context for secure connections."""
        return {
            'cert_file': cert_file,
            'key_file': key_file,
            'min_version': 'TLSv1.3',
            'cipher_suites': self.supported_ciphers,
            'verify_mode': 'CERT_REQUIRED'
        }
    
    def verify_certificate_chain(self, cert_chain: List[x509.Certificate]) -> bool:
        """Verify certificate chain."""
        for i in range(len(cert_chain) - 1):
            if not self.verify_certificate(cert_chain[i], cert_chain[i + 1]):
                return False
        return True


class HashService:
    """Hash service for data integrity and verification."""
    
    @staticmethod
    def sha256_hash(data: Union[str, bytes]) -> str:
        """Generate SHA-256 hash of data."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def sha512_hash(data: Union[str, bytes]) -> str:
        """Generate SHA-512 hash of data."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha512(data).hexdigest()
    
    @staticmethod
    def verify_hash(data: Union[str, bytes], expected_hash: str, algorithm: str = "sha256") -> bool:
        """Verify hash of data."""
        if algorithm == "sha256":
            actual_hash = HashService.sha256_hash(data)
        elif algorithm == "sha512":
            actual_hash = HashService.sha512_hash(data)
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
        return actual_hash == expected_hash 