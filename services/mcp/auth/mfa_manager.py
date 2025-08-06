"""
Multi-Factor Authentication Manager

Handles TOTP, SMS, email, and hardware token authentication
with proper security practices and audit logging.
"""

import time
import secrets
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pyotp
import qrcode
from io import BytesIO
import base64

from .models import MFAConfig, MFAMethod, MFAToken, MFAStatus, MFAAuditLog


logger = logging.getLogger(__name__)


class MFAManager:
    """Multi-factor authentication manager"""

    def __init__(self, redis_manager=None):
        """
        Initialize the MFA manager

        Args:
            redis_manager: Redis manager for token storage
        """
        self.redis_manager = redis_manager
        self.totp_issuer = "MCP Service"
        self.totp_algorithm = "sha1"
        self.totp_digits = 6
        self.totp_period = 30

        # MFA configuration cache
        self.mfa_configs: Dict[str, MFAConfig] = {}

        logger.info("MFA Manager initialized")

    def _generate_secret(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure secret

        Args:
            length: Length of the secret

        Returns:
            Base32 encoded secret
        """
        return pyotp.random_base32(length)

    def _generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for account recovery

        Args:
            count: Number of backup codes to generate

        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = secrets.token_urlsafe(6).upper()[:8]
            codes.append(code)
        return codes

    def _hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for secure storage

        Args:
            code: Backup code to hash

        Returns:
            Hashed backup code
        """
        return hashlib.sha256(code.encode()).hexdigest()

    def _verify_backup_code(self, code: str, hashed_code: str) -> bool:
        """
        Verify a backup code against its hash

        Args:
            code: Backup code to verify
            hashed_code: Hashed backup code

        Returns:
            True if code matches hash
        """
        return hashlib.sha256(code.encode()).hexdigest() == hashed_code

    def _generate_qr_code(self, secret: str, username: str) -> str:
        """
        Generate QR code for TOTP setup

        Args:
            secret: TOTP secret
            username: Username for the account

        Returns:
            Base64 encoded QR code image
        """
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=username, issuer_name=self.totp_issuer
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    def setup_mfa(
        self, user_id: str, username: str, method: MFAMethod
    ) -> Dict[str, Any]:
        """
        Set up MFA for a user

        Args:
            user_id: User ID
            username: Username
            method: MFA method to set up

        Returns:
            Setup information including secrets and QR codes
        """
        try:
            if method == MFAMethod.TOTP:
                return self._setup_totp(user_id, username)
            elif method == MFAMethod.SMS:
                return self._setup_sms(user_id, username)
            elif method == MFAMethod.EMAIL:
                return self._setup_email(user_id, username)
            elif method == MFAMethod.HARDWARE_TOKEN:
                return self._setup_hardware_token(user_id, username)
            else:
                raise ValueError(f"Unsupported MFA method: {method}")

        except Exception as e:
            logger.error(f"Failed to setup MFA for user {user_id}: {e}")
            raise

    def _setup_totp(self, user_id: str, username: str) -> Dict[str, Any]:
        """Set up TOTP authentication"""
        # Generate secret
        secret = self._generate_secret()

        # Generate backup codes
        backup_codes = self._generate_backup_codes()
        hashed_backup_codes = [self._hash_backup_code(code) for code in backup_codes]

        # Generate QR code
        qr_code = self._generate_qr_code(secret, username)

        # Create MFA config
        mfa_config = MFAConfig(
            user_id=user_id,
            method=MFAMethod.TOTP,
            secret=secret,
            backup_codes=hashed_backup_codes,
            is_enabled=False,
            created_at=datetime.utcnow(),
        )

        # Store config
        self.mfa_configs[user_id] = mfa_config

        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes,
            "setup_instructions": [
                "1. Scan the QR code with your authenticator app",
                "2. Enter the 6-digit code to verify setup",
                "3. Save your backup codes in a secure location",
            ],
        }

    def _setup_sms(self, user_id: str, username: str) -> Dict[str, Any]:
        """Set up SMS authentication"""
        # Generate verification code
        verification_code = secrets.token_hex(3).upper()[:6]

        # Store verification code (in production, send via SMS)
        if self.redis_manager:
            self.redis_manager.set(f"mfa_sms_{user_id}", verification_code, ex=300)

        return {
            "verification_code": verification_code,  # In production, this would be sent via SMS
            "phone_number": "***-***-****",  # Placeholder
            "setup_instructions": [
                "1. Enter the verification code sent to your phone",
                "2. Verify the code to complete setup",
            ],
        }

    def _setup_email(self, user_id: str, username: str) -> Dict[str, Any]:
        """Set up email authentication"""
        # Generate verification code
        verification_code = secrets.token_hex(3).upper()[:6]

        # Store verification code (in production, send via email)
        if self.redis_manager:
            self.redis_manager.set(f"mfa_email_{user_id}", verification_code, ex=300)

        return {
            "verification_code": verification_code,  # In production, this would be sent via email
            "email": "user@example.com",  # Placeholder
            "setup_instructions": [
                "1. Enter the verification code sent to your email",
                "2. Verify the code to complete setup",
            ],
        }

    def _setup_hardware_token(self, user_id: str, username: str) -> Dict[str, Any]:
        """Set up hardware token authentication"""
        return {
            "setup_instructions": [
                "1. Insert your hardware token",
                "2. Enter the code displayed on the token",
                "3. Verify the code to complete setup",
            ]
        }

    def verify_mfa(self, user_id: str, method: MFAMethod, token: str) -> bool:
        """
        Verify MFA token

        Args:
            user_id: User ID
            method: MFA method
            token: Token to verify

        Returns:
            True if token is valid
        """
        try:
            if method == MFAMethod.TOTP:
                return self._verify_totp(user_id, token)
            elif method == MFAMethod.SMS:
                return self._verify_sms(user_id, token)
            elif method == MFAMethod.EMAIL:
                return self._verify_email(user_id, token)
            elif method == MFAMethod.HARDWARE_TOKEN:
                return self._verify_hardware_token(user_id, token)
            elif method == MFAMethod.BACKUP_CODE:
                return self._verify_backup_code(user_id, token)
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to verify MFA for user {user_id}: {e}")
            return False

    def _verify_totp(self, user_id: str, token: str) -> bool:
        """Verify TOTP token"""
        if user_id not in self.mfa_configs:
            return False

        config = self.mfa_configs[user_id]
        if config.method != MFAMethod.TOTP or not config.is_enabled:
            return False

        totp = pyotp.TOTP(config.secret)
        return totp.verify(token, valid_window=1)  # Allow 1 period window

    def _verify_sms(self, user_id: str, token: str) -> bool:
        """Verify SMS token"""
        if not self.redis_manager:
            return False

        stored_token = self.redis_manager.get(f"mfa_sms_{user_id}")
        if not stored_token:
            return False

        # Remove token after use
        self.redis_manager.delete(f"mfa_sms_{user_id}")

        return stored_token == token

    def _verify_email(self, user_id: str, token: str) -> bool:
        """Verify email token"""
        if not self.redis_manager:
            return False

        stored_token = self.redis_manager.get(f"mfa_email_{user_id}")
        if not stored_token:
            return False

        # Remove token after use
        self.redis_manager.delete(f"mfa_email_{user_id}")

        return stored_token == token

    def _verify_hardware_token(self, user_id: str, token: str) -> bool:
        """Verify hardware token"""
        # In a real implementation, this would verify against hardware token
        # For demo purposes, accept any 6-digit code
        return len(token) == 6 and token.isdigit()

    def _verify_backup_code(self, user_id: str, token: str) -> bool:
        """Verify backup code"""
        if user_id not in self.mfa_configs:
            return False

        config = self.mfa_configs[user_id]
        if not config.is_enabled:
            return False

        hashed_token = self._hash_backup_code(token)

        # Check if backup code exists and remove it after use
        if hashed_token in config.backup_codes:
            config.backup_codes.remove(hashed_token)
            return True

        return False

    def enable_mfa(self, user_id: str) -> bool:
        """
        Enable MFA for a user

        Args:
            user_id: User ID

        Returns:
            True if enabled successfully
        """
        try:
            if user_id not in self.mfa_configs:
                return False

            config = self.mfa_configs[user_id]
            config.is_enabled = True
            config.enabled_at = datetime.utcnow()

            logger.info(f"MFA enabled for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to enable MFA for user {user_id}: {e}")
            return False

    def disable_mfa(self, user_id: str) -> bool:
        """
        Disable MFA for a user

        Args:
            user_id: User ID

        Returns:
            True if disabled successfully
        """
        try:
            if user_id in self.mfa_configs:
                del self.mfa_configs[user_id]

            logger.info(f"MFA disabled for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to disable MFA for user {user_id}: {e}")
            return False

    def get_mfa_status(self, user_id: str) -> Optional[MFAStatus]:
        """
        Get MFA status for a user

        Args:
            user_id: User ID

        Returns:
            MFA status or None if not configured
        """
        if user_id not in self.mfa_configs:
            return None

        config = self.mfa_configs[user_id]

        return MFAStatus(
            user_id=user_id,
            method=config.method,
            is_enabled=config.is_enabled,
            is_configured=True,
            backup_codes_remaining=len(config.backup_codes),
            created_at=config.created_at,
            enabled_at=config.enabled_at,
        )

    def generate_new_backup_codes(self, user_id: str) -> List[str]:
        """
        Generate new backup codes for a user

        Args:
            user_id: User ID

        Returns:
            List of new backup codes
        """
        if user_id not in self.mfa_configs:
            raise ValueError("MFA not configured for user")

        config = self.mfa_configs[user_id]
        new_backup_codes = self._generate_backup_codes()
        config.backup_codes = [
            self._hash_backup_code(code) for code in new_backup_codes
        ]

        logger.info(f"Generated new backup codes for user {user_id}")
        return new_backup_codes

    def log_mfa_attempt(
        self,
        user_id: str,
        method: MFAMethod,
        success: bool,
        ip_address: str = None,
        user_agent: str = None,
    ) -> None:
        """
        Log MFA attempt for audit purposes

        Args:
            user_id: User ID
            method: MFA method used
            success: Whether the attempt was successful
            ip_address: IP address of the attempt
            user_agent: User agent string
        """
        audit_log = MFAAuditLog(
            user_id=user_id,
            method=method,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
        )

        # In a real implementation, this would be stored in a database
        logger.info(f"MFA attempt: user={user_id}, method={method}, success={success}")

    def get_mfa_statistics(self) -> Dict[str, Any]:
        """Get MFA statistics"""
        total_users = len(self.mfa_configs)
        enabled_users = len([c for c in self.mfa_configs.values() if c.is_enabled])

        method_counts = {}
        for config in self.mfa_configs.values():
            method = config.method.value
            method_counts[method] = method_counts.get(method, 0) + 1

        return {
            "total_users": total_users,
            "enabled_users": enabled_users,
            "enabled_percentage": (
                (enabled_users / total_users * 100) if total_users > 0 else 0
            ),
            "method_distribution": method_counts,
        }
