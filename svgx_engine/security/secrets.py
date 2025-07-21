"""
Secrets Management for Arxos.

This module provides comprehensive secrets management including:
- HashiCorp Vault integration
- Automated secret rotation
- Secure secret distribution
- Key management and encryption
"""

import os
import json
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import logging
from .encryption import EncryptionService


@dataclass
class SecretMetadata:
    """Metadata for stored secrets."""
    secret_id: str
    secret_type: str
    created_at: datetime
    last_rotated: datetime
    next_rotation: datetime
    version: int
    tags: Dict[str, str] = None


class VaultClient:
    """HashiCorp Vault client for secrets management."""
    
    def __init__(self, vault_url: str, token: str, namespace: str = None):
        self.vault_url = vault_url.rstrip('/')
        self.token = token
        self.namespace = namespace
        self.session = requests.Session()
        self.session.headers.update({
            'X-Vault-Token': token,
            'Content-Type': 'application/json'
        })
        
        if namespace:
            self.session.headers['X-Vault-Namespace'] = namespace
    
    def read_secret(self, path: str, version: Optional[int] = None) -> Dict[str, Any]:
        """Read secret from Vault."""
        url = f"{self.vault_url}/v1/secret/data/{path}"
        
        if version:
            url += f"?version={version}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()['data']['data']
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to read secret from Vault: {e}")
            raise
    
    def write_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """Write secret to Vault."""
        url = f"{self.vault_url}/v1/secret/data/{path}"
        payload = {'data': data}
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to write secret to Vault: {e}")
            return False
    
    def delete_secret(self, path: str) -> bool:
        """Delete secret from Vault."""
        url = f"{self.vault_url}/v1/secret/metadata/{path}"
        
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to delete secret from Vault: {e}")
            return False
    
    def list_secrets(self, path: str = "") -> List[str]:
        """List secrets in Vault."""
        url = f"{self.vault_url}/v1/secret/metadata/{path}"
        
        try:
            response = self.session.list(url)
            response.raise_for_status()
            return response.json()['data']['keys']
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to list secrets from Vault: {e}")
            return []
    
    def get_secret_metadata(self, path: str) -> Optional[Dict[str, Any]]:
        """Get secret metadata from Vault."""
        url = f"{self.vault_url}/v1/secret/metadata/{path}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()['data']
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get secret metadata from Vault: {e}")
            return None
    
    def rotate_secret(self, path: str) -> bool:
        """Rotate secret in Vault."""
        # Read current secret
        current_secret = self.read_secret(path)
        
        # Generate new secret value
        new_secret = self._generate_new_secret(current_secret)
        
        # Write new secret
        success = self.write_secret(path, new_secret)
        
        if success:
            logging.info(f"Successfully rotated secret: {path}")
        
        return success
    
    def _generate_new_secret(self, current_secret: Dict[str, Any]) -> Dict[str, Any]:
        """Generate new secret value based on current secret."""
        new_secret = {}
        
        for key, value in current_secret.items():
            if isinstance(value, str):
                # Generate new random value for string secrets
                new_secret[key] = self._generate_random_string(len(value))
            elif isinstance(value, dict):
                # Recursively generate new values for nested secrets
                new_secret[key] = self._generate_new_secret(value)
            else:
                # Keep non-string values as-is
                new_secret[key] = value
        
        return new_secret
    
    def _generate_random_string(self, length: int) -> str:
        """Generate random string of specified length."""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class SecretsManager:
    """Comprehensive secrets management service."""
    
    def __init__(self, vault_client: VaultClient = None, local_storage_path: str = "secrets/"):
        self.vault_client = vault_client
        self.local_storage_path = local_storage_path
        self.encryption_service = EncryptionService()
        self.secret_metadata = {}
        
        # Create local storage directory
        os.makedirs(local_storage_path, exist_ok=True)
        
        # Load existing metadata
        self._load_metadata()
    
    def store_secret(self, secret_id: str, secret_data: Dict[str, Any], 
                    secret_type: str = "application", rotation_days: int = 90) -> bool:
        """Store secret with metadata."""
        try:
            # Encrypt secret data
            master_key = self._get_master_key()
            encrypted_data = self.encryption_service.encrypt_data(
                json.dumps(secret_data), master_key
            )
            
            # Store in Vault if available
            if self.vault_client:
                success = self.vault_client.write_secret(secret_id, secret_data)
                if not success:
                    return False
            
            # Store locally as backup
            local_file = os.path.join(self.local_storage_path, f"{secret_id}.encrypted")
            with open(local_file, 'wb') as f:
                f.write(encrypted_data['ciphertext'])
                f.write(encrypted_data['iv'])
                f.write(encrypted_data['tag'])
            
            # Store metadata
            metadata = SecretMetadata(
                secret_id=secret_id,
                secret_type=secret_type,
                created_at=datetime.utcnow(),
                last_rotated=datetime.utcnow(),
                next_rotation=datetime.utcnow() + timedelta(days=rotation_days),
                version=1,
                tags={}
            )
            
            self.secret_metadata[secret_id] = metadata
            self._save_metadata()
            
            logging.info(f"Successfully stored secret: {secret_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to store secret {secret_id}: {e}")
            return False
    
    def retrieve_secret(self, secret_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve secret by ID."""
        try:
            # Try Vault first
            if self.vault_client:
                try:
                    secret_data = self.vault_client.read_secret(secret_id)
                    return secret_data
                except Exception as e:
                    logging.warning(f"Failed to retrieve from Vault, trying local storage: {e}")
            
            # Fallback to local storage
            local_file = os.path.join(self.local_storage_path, f"{secret_id}.encrypted")
            if not os.path.exists(local_file):
                return None
            
            # Read encrypted data
            with open(local_file, 'rb') as f:
                data = f.read()
            
            # Extract components
            tag_size = 16
            iv_size = 12
            
            ciphertext = data[:-tag_size-iv_size]
            iv = data[-tag_size-iv_size:-tag_size]
            tag = data[-tag_size:]
            
            encrypted_data = {
                'ciphertext': ciphertext,
                'iv': iv,
                'tag': tag
            }
            
            # Decrypt data
            master_key = self._get_master_key()
            decrypted_data = self.encryption_service.decrypt_data(encrypted_data, master_key)
            
            # Parse JSON
            secret_data = json.loads(decrypted_data.decode('utf-8'))
            
            # Update metadata
            if secret_id in self.secret_metadata:
                self.secret_metadata[secret_id].last_rotated = datetime.utcnow()
                self._save_metadata()
            
            return secret_data
            
        except Exception as e:
            logging.error(f"Failed to retrieve secret {secret_id}: {e}")
            return None
    
    def rotate_secret(self, secret_id: str) -> bool:
        """Rotate secret and update all references."""
        try:
            # Retrieve current secret
            current_secret = self.retrieve_secret(secret_id)
            if not current_secret:
                return False
            
            # Generate new secret values
            new_secret = self._generate_new_secret_values(current_secret)
            
            # Store new secret
            success = self.store_secret(secret_id, new_secret)
            
            if success:
                # Update metadata
                if secret_id in self.secret_metadata:
                    metadata = self.secret_metadata[secret_id]
                    metadata.last_rotated = datetime.utcnow()
                    metadata.next_rotation = datetime.utcnow() + timedelta(days=90)
                    metadata.version += 1
                    self._save_metadata()
                
                logging.info(f"Successfully rotated secret: {secret_id}")
            
            return success
            
        except Exception as e:
            logging.error(f"Failed to rotate secret {secret_id}: {e}")
            return False
    
    def _generate_new_secret_values(self, current_secret: Dict[str, Any]) -> Dict[str, Any]:
        """Generate new secret values while preserving structure."""
        new_secret = {}
        
        for key, value in current_secret.items():
            if isinstance(value, str):
                # Generate new random string
                new_secret[key] = self._generate_random_string(len(value))
            elif isinstance(value, dict):
                # Recursively generate new values
                new_secret[key] = self._generate_new_secret_values(value)
            else:
                # Keep non-string values as-is
                new_secret[key] = value
        
        return new_secret
    
    def _generate_random_string(self, length: int) -> str:
        """Generate cryptographically secure random string."""
        import secrets
        import string
        
        # Use alphanumeric characters for most secrets
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def list_secrets(self) -> List[Dict[str, Any]]:
        """List all secrets with metadata."""
        secrets_list = []
        
        for secret_id, metadata in self.secret_metadata.items():
            secrets_list.append({
                'secret_id': secret_id,
                'secret_type': metadata.secret_type,
                'created_at': metadata.created_at.isoformat(),
                'last_rotated': metadata.last_rotated.isoformat(),
                'next_rotation': metadata.next_rotation.isoformat(),
                'version': metadata.version,
                'tags': metadata.tags or {}
            })
        
        return secrets_list
    
    def get_secrets_due_for_rotation(self) -> List[str]:
        """Get list of secrets due for rotation."""
        due_secrets = []
        current_time = datetime.utcnow()
        
        for secret_id, metadata in self.secret_metadata.items():
            if current_time >= metadata.next_rotation:
                due_secrets.append(secret_id)
        
        return due_secrets
    
    def auto_rotate_secrets(self) -> Dict[str, bool]:
        """Automatically rotate all secrets due for rotation."""
        results = {}
        due_secrets = self.get_secrets_due_for_rotation()
        
        for secret_id in due_secrets:
            success = self.rotate_secret(secret_id)
            results[secret_id] = success
        
        return results
    
    def delete_secret(self, secret_id: str) -> bool:
        """Delete secret and its metadata."""
        try:
            # Delete from Vault
            if self.vault_client:
                self.vault_client.delete_secret(secret_id)
            
            # Delete local file
            local_file = os.path.join(self.local_storage_path, f"{secret_id}.encrypted")
            if os.path.exists(local_file):
                os.remove(local_file)
            
            # Remove metadata
            if secret_id in self.secret_metadata:
                del self.secret_metadata[secret_id]
                self._save_metadata()
            
            logging.info(f"Successfully deleted secret: {secret_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to delete secret {secret_id}: {e}")
            return False
    
    def _get_master_key(self) -> bytes:
        """Get or generate master key for secret encryption."""
        master_key_file = os.path.join(self.local_storage_path, "master.key")
        
        if os.path.exists(master_key_file):
            with open(master_key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new master key
            master_key = self.encryption_service.generate_key()
            with open(master_key_file, 'wb') as f:
                f.write(master_key)
            return master_key
    
    def _load_metadata(self):
        """Load secret metadata from file."""
        metadata_file = os.path.join(self.local_storage_path, "metadata.json")
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    
                for secret_id, metadata_data in data.items():
                    metadata = SecretMetadata(
                        secret_id=metadata_data['secret_id'],
                        secret_type=metadata_data['secret_type'],
                        created_at=datetime.fromisoformat(metadata_data['created_at']),
                        last_rotated=datetime.fromisoformat(metadata_data['last_rotated']),
                        next_rotation=datetime.fromisoformat(metadata_data['next_rotation']),
                        version=metadata_data['version'],
                        tags=metadata_data.get('tags', {})
                    )
                    self.secret_metadata[secret_id] = metadata
            except Exception as e:
                logging.error(f"Failed to load metadata: {e}")
    
    def _save_metadata(self):
        """Save secret metadata to file."""
        metadata_file = os.path.join(self.local_storage_path, "metadata.json")
        
        try:
            data = {}
            for secret_id, metadata in self.secret_metadata.items():
                data[secret_id] = {
                    'secret_id': metadata.secret_id,
                    'secret_type': metadata.secret_type,
                    'created_at': metadata.created_at.isoformat(),
                    'last_rotated': metadata.last_rotated.isoformat(),
                    'next_rotation': metadata.next_rotation.isoformat(),
                    'version': metadata.version,
                    'tags': metadata.tags or {}
                }
            
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Failed to save metadata: {e}")


class SecretRotator:
    """Automated secret rotation service."""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.secrets_manager = secrets_manager
        self.rotation_schedule = {}
        self.rotation_handlers = {}
    
    def schedule_rotation(self, secret_id: str, rotation_interval_days: int = 90):
        """Schedule secret for rotation."""
        self.rotation_schedule[secret_id] = rotation_interval_days
    
    def add_rotation_handler(self, secret_id: str, handler: callable):
        """Add custom rotation handler for a secret."""
        self.rotation_handlers[secret_id] = handler
    
    def rotate_scheduled_secrets(self) -> Dict[str, bool]:
        """Rotate all scheduled secrets that are due."""
        results = {}
        due_secrets = self.secrets_manager.get_secrets_due_for_rotation()
        
        for secret_id in due_secrets:
            success = self._rotate_secret_with_handler(secret_id)
            results[secret_id] = success
        
        return results
    
    def _rotate_secret_with_handler(self, secret_id: str) -> bool:
        """Rotate secret using custom handler if available."""
        try:
            # Check if custom handler exists
            if secret_id in self.rotation_handlers:
                handler = self.rotation_handlers[secret_id]
                success = handler(secret_id)
            else:
                # Use default rotation
                success = self.secrets_manager.rotate_secret(secret_id)
            
            if success:
                logging.info(f"Successfully rotated secret with handler: {secret_id}")
            
            return success
            
        except Exception as e:
            logging.error(f"Failed to rotate secret with handler {secret_id}: {e}")
            return False 