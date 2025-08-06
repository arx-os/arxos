"""
OAuth Manager for Authentication

Handles OAuth authentication with multiple providers including Google,
Microsoft, GitHub, and custom providers with proper security practices.
"""

import secrets
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import httpx
from urllib.parse import urlencode, parse_qs, urlparse

from .models import (
    OAuthConfig,
    OAuthToken,
    OAuthUserInfo,
    OAuthProvider,
    OAuthRequest,
    OAuthCallback,
)


logger = logging.getLogger(__name__)


class OAuthManager:
    """OAuth authentication manager"""

    def __init__(self, redis_manager=None):
        """
        Initialize the OAuth manager

        Args:
            redis_manager: Redis manager for token storage
        """
        self.redis_manager = redis_manager
        self.oauth_configs: Dict[OAuthProvider, OAuthConfig] = {}
        self.oauth_tokens: Dict[str, OAuthToken] = {}
        self.user_info_cache: Dict[str, OAuthUserInfo] = {}

        # Initialize default OAuth configurations
        self._initialize_default_configs()

        logger.info("OAuth Manager initialized")

    def _initialize_default_configs(self) -> None:
        """Initialize default OAuth configurations"""
        # Google OAuth
        google_config = OAuthConfig(
            provider=OAuthProvider.GOOGLE,
            client_id="your_google_client_id",
            client_secret="your_google_client_secret",
            redirect_uri="http://localhost:8001/api/v1/auth/oauth/callback/google",
            scopes=["openid", "email", "profile"],
            is_enabled=False,  # Disabled by default
        )
        self.oauth_configs[OAuthProvider.GOOGLE] = google_config

        # Microsoft OAuth
        microsoft_config = OAuthConfig(
            provider=OAuthProvider.MICROSOFT,
            client_id="your_microsoft_client_id",
            client_secret="your_microsoft_client_secret",
            redirect_uri="http://localhost:8001/api/v1/auth/oauth/callback/microsoft",
            scopes=["openid", "email", "profile"],
            is_enabled=False,
        )
        self.oauth_configs[OAuthProvider.MICROSOFT] = microsoft_config

        # GitHub OAuth
        github_config = OAuthConfig(
            provider=OAuthProvider.GITHUB,
            client_id="your_github_client_id",
            client_secret="your_github_client_secret",
            redirect_uri="http://localhost:8001/api/v1/auth/oauth/callback/github",
            scopes=["read:user", "user:email"],
            is_enabled=False,
        )
        self.oauth_configs[OAuthProvider.GITHUB] = github_config

        logger.info("Default OAuth configurations initialized")

    def _get_oauth_urls(self, provider: OAuthProvider) -> Dict[str, str]:
        """
        Get OAuth URLs for a provider

        Args:
            provider: OAuth provider

        Returns:
            Dictionary with OAuth URLs
        """
        urls = {
            OAuthProvider.GOOGLE: {
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            },
            OAuthProvider.MICROSOFT: {
                "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "userinfo_url": "https://graph.microsoft.com/v1.0/me",
            },
            OAuthProvider.GITHUB: {
                "authorization_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "userinfo_url": "https://api.github.com/user",
            },
            OAuthProvider.FACEBOOK: {
                "authorization_url": "https://www.facebook.com/v12.0/dialog/oauth",
                "token_url": "https://graph.facebook.com/v12.0/oauth/access_token",
                "userinfo_url": "https://graph.facebook.com/v12.0/me",
            },
            OAuthProvider.LINKEDIN: {
                "authorization_url": "https://www.linkedin.com/oauth/v2/authorization",
                "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
                "userinfo_url": "https://api.linkedin.com/v2/me",
            },
        }

        return urls.get(provider, {})

    def _generate_state(self) -> str:
        """
        Generate a secure state parameter for OAuth

        Returns:
            Secure state string
        """
        return secrets.token_urlsafe(32)

    def _store_state(self, state: str, provider: OAuthProvider) -> None:
        """
        Store OAuth state for verification

        Args:
            state: State parameter
            provider: OAuth provider
        """
        if self.redis_manager:
            # Store state with 10-minute expiration
            self.redis_manager.set(f"oauth_state_{state}", provider.value, ex=600)

    def _verify_state(self, state: str) -> Optional[str]:
        """
        Verify OAuth state parameter

        Args:
            state: State parameter to verify

        Returns:
            Provider value if valid, None otherwise
        """
        if not self.redis_manager:
            return None

        provider = self.redis_manager.get(f"oauth_state_{state}")
        if provider:
            # Remove state after verification
            self.redis_manager.delete(f"oauth_state_{state}")
            return provider

        return None

    def get_authorization_url(self, request: OAuthRequest) -> str:
        """
        Get OAuth authorization URL

        Args:
            request: OAuth request

        Returns:
            Authorization URL
        """
        if request.provider not in self.oauth_configs:
            raise ValueError(f"OAuth provider {request.provider} not configured")

        config = self.oauth_configs[request.provider]
        if not config.is_enabled:
            raise ValueError(f"OAuth provider {request.provider} is disabled")

        urls = self._get_oauth_urls(request.provider)
        if not urls:
            raise ValueError(
                f"OAuth URLs not available for provider {request.provider}"
            )

        # Generate state parameter
        state = request.state or self._generate_state()
        self._store_state(state, request.provider)

        # Build authorization URL
        params = {
            "client_id": config.client_id,
            "redirect_uri": request.redirect_uri,
            "response_type": "code",
            "scope": " ".join(request.scopes or config.scopes),
            "state": state,
        }

        # Add provider-specific parameters
        if request.provider == OAuthProvider.GOOGLE:
            params["access_type"] = "offline"
            params["prompt"] = "consent"
        elif request.provider == OAuthProvider.MICROSOFT:
            params["response_mode"] = "query"

        authorization_url = urls["authorization_url"]
        return f"{authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, callback: OAuthCallback) -> OAuthToken:
        """
        Exchange authorization code for access token

        Args:
            callback: OAuth callback data

        Returns:
            OAuth token information
        """
        if callback.error:
            raise ValueError(
                f"OAuth error: {callback.error} - {callback.error_description}"
            )

        # Verify state parameter
        provider_value = self._verify_state(callback.state)
        if not provider_value or provider_value != callback.provider.value:
            raise ValueError("Invalid OAuth state parameter")

        if callback.provider not in self.oauth_configs:
            raise ValueError(f"OAuth provider {callback.provider} not configured")

        config = self.oauth_configs[callback.provider]
        urls = self._get_oauth_urls(callback.provider)

        # Exchange code for token
        token_data = await self._exchange_token(
            callback.provider, callback.code, config, urls
        )

        # Get user information
        user_info = await self._get_user_info(
            callback.provider, token_data["access_token"], urls
        )

        # Create OAuth token
        oauth_token = OAuthToken(
            user_id=user_info.user_id,
            provider=callback.provider,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_type=token_data.get("token_type", "Bearer"),
            expires_at=datetime.utcnow()
            + timedelta(seconds=token_data.get("expires_in", 3600)),
            scopes=token_data.get("scope", "").split(),
            created_at=datetime.utcnow(),
        )

        # Store token
        token_key = f"oauth_token_{user_info.user_id}_{callback.provider.value}"
        self.oauth_tokens[token_key] = oauth_token

        # Cache user info
        self.user_info_cache[user_info.user_id] = user_info

        logger.info(
            f"OAuth token obtained for user {user_info.user_id} via {callback.provider}"
        )
        return oauth_token

    async def _exchange_token(
        self,
        provider: OAuthProvider,
        code: str,
        config: OAuthConfig,
        urls: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            provider: OAuth provider
            code: Authorization code
            config: OAuth configuration
            urls: OAuth URLs

        Returns:
            Token response data
        """
        token_data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": config.redirect_uri,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # GitHub requires Accept header
        if provider == OAuthProvider.GITHUB:
            headers["Accept"] = "application/json"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                urls["token_url"], data=token_data, headers=headers
            )

            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.text}")

            return response.json()

    async def _get_user_info(
        self, provider: OAuthProvider, access_token: str, urls: Dict[str, str]
    ) -> OAuthUserInfo:
        """
        Get user information from OAuth provider

        Args:
            provider: OAuth provider
            access_token: Access token
            urls: OAuth URLs

        Returns:
            User information
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        # Provider-specific headers
        if provider == OAuthProvider.GITHUB:
            headers["Accept"] = "application/vnd.github.v3+json"
        elif provider == OAuthProvider.LINKEDIN:
            headers["X-Restli-Protocol-Version"] = "2.0.0"

        async with httpx.AsyncClient() as client:
            response = await client.get(urls["userinfo_url"], headers=headers)

            if response.status_code != 200:
                raise ValueError(f"Failed to get user info: {response.text}")

            user_data = response.json()

            # Map provider-specific user data to our format
            if provider == OAuthProvider.GOOGLE:
                user_info = OAuthUserInfo(
                    user_id=user_data["id"],
                    provider=provider,
                    provider_user_id=user_data["id"],
                    email=user_data["email"],
                    name=user_data.get("name"),
                    picture=user_data.get("picture"),
                    locale=user_data.get("locale"),
                )
            elif provider == OAuthProvider.MICROSOFT:
                user_info = OAuthUserInfo(
                    user_id=user_data["id"],
                    provider=provider,
                    provider_user_id=user_data["id"],
                    email=user_data.get("mail") or user_data.get("userPrincipalName"),
                    name=user_data.get("displayName"),
                    picture=None,  # Microsoft Graph doesn't provide picture in basic profile
                    locale=user_data.get("preferredLanguage"),
                )
            elif provider == OAuthProvider.GITHUB:
                user_info = OAuthUserInfo(
                    user_id=str(user_data["id"]),
                    provider=provider,
                    provider_user_id=str(user_data["id"]),
                    email=user_data.get("email"),
                    name=user_data.get("name"),
                    picture=user_data.get("avatar_url"),
                    locale=user_data.get("location"),
                )
            else:
                # Generic mapping for other providers
                user_info = OAuthUserInfo(
                    user_id=user_data.get("id", user_data.get("sub")),
                    provider=provider,
                    provider_user_id=user_data.get("id", user_data.get("sub")),
                    email=user_data.get("email"),
                    name=user_data.get("name"),
                    picture=user_data.get("picture"),
                    locale=user_data.get("locale"),
                )

            return user_info

    def get_oauth_token(
        self, user_id: str, provider: OAuthProvider
    ) -> Optional[OAuthToken]:
        """
        Get OAuth token for a user

        Args:
            user_id: User ID
            provider: OAuth provider

        Returns:
            OAuth token or None if not found
        """
        token_key = f"oauth_token_{user_id}_{provider.value}"
        return self.oauth_tokens.get(token_key)

    def get_user_info(self, user_id: str) -> Optional[OAuthUserInfo]:
        """
        Get OAuth user information

        Args:
            user_id: User ID

        Returns:
            User information or None if not found
        """
        return self.user_info_cache.get(user_id)

    def revoke_token(self, user_id: str, provider: OAuthProvider) -> bool:
        """
        Revoke OAuth token

        Args:
            user_id: User ID
            provider: OAuth provider

        Returns:
            True if token was revoked
        """
        token_key = f"oauth_token_{user_id}_{provider.value}"

        if token_key in self.oauth_tokens:
            del self.oauth_tokens[token_key]

        if user_id in self.user_info_cache:
            del self.user_info_cache[user_id]

        logger.info(f"OAuth token revoked for user {user_id} via {provider}")
        return True

    def update_oauth_config(self, provider: OAuthProvider, config: OAuthConfig) -> None:
        """
        Update OAuth configuration

        Args:
            provider: OAuth provider
            config: New OAuth configuration
        """
        self.oauth_configs[provider] = config
        logger.info(f"OAuth configuration updated for {provider}")

    def get_oauth_config(self, provider: OAuthProvider) -> Optional[OAuthConfig]:
        """
        Get OAuth configuration

        Args:
            provider: OAuth provider

        Returns:
            OAuth configuration or None if not found
        """
        return self.oauth_configs.get(provider)

    def get_enabled_providers(self) -> List[OAuthProvider]:
        """
        Get list of enabled OAuth providers

        Returns:
            List of enabled providers
        """
        return [
            provider
            for provider, config in self.oauth_configs.items()
            if config.is_enabled
        ]

    def get_oauth_statistics(self) -> Dict[str, Any]:
        """Get OAuth statistics"""
        total_tokens = len(self.oauth_tokens)
        total_users = len(self.user_info_cache)
        enabled_providers = len(self.get_enabled_providers())

        provider_counts = {}
        for token_key in self.oauth_tokens.keys():
            provider = token_key.split("_")[-1]
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        return {
            "total_tokens": total_tokens,
            "total_users": total_users,
            "enabled_providers": enabled_providers,
            "provider_distribution": provider_counts,
        }
