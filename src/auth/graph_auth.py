"""Microsoft Graph API authentication using MSAL."""

import json
import logging
from pathlib import Path
from typing import Optional

import msal

from src.config import Config

logger = logging.getLogger(__name__)


class GraphAuthenticator:
    """Handles authentication with Microsoft Graph API."""

    TOKEN_CACHE_FILE = Path("token_cache.json")

    def __init__(self):
        """Initialize the authenticator."""
        self.client_id = Config.CLIENT_ID
        self.tenant_id = Config.TENANT_ID
        self.client_secret = Config.CLIENT_SECRET
        self.scopes = Config.GRAPH_SCOPES

        # Create MSAL app
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"

        # Load token cache if exists
        cache = msal.SerializableTokenCache()
        if self.TOKEN_CACHE_FILE.exists():
            cache.deserialize(self.TOKEN_CACHE_FILE.read_text())

        # Create confidential client app (for service/daemon apps)
        if self.client_secret:
            self.app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret,
                token_cache=cache
            )
        else:
            # Public client app (for interactive/device code flow)
            self.app = msal.PublicClientApplication(
                self.client_id,
                authority=self.authority,
                token_cache=cache
            )

        self.cache = cache

    def get_access_token(self) -> Optional[str]:
        """
        Get an access token for Microsoft Graph API.

        Returns:
            Access token string or None if authentication fails.
        """
        # Try to get token from cache first
        accounts = self.app.get_accounts()
        if accounts:
            logger.info("Found cached account, attempting silent authentication")
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            if result and "access_token" in result:
                logger.info("Successfully acquired token from cache")
                self._save_cache()
                return result["access_token"]

        # If client secret is available, use client credentials flow
        if self.client_secret:
            logger.info("Using client credentials flow")
            # Client credentials flow requires /.default scope
            client_scopes = ["https://graph.microsoft.com/.default"]
            result = self.app.acquire_token_for_client(scopes=client_scopes)
        else:
            # Use device code flow for interactive authentication
            logger.info("Using device code flow for interactive authentication")
            flow = self.app.initiate_device_flow(scopes=self.scopes)

            if "user_code" not in flow:
                raise ValueError(f"Failed to create device flow: {flow.get('error_description')}")

            print(flow["message"])

            # Wait for user to authenticate
            result = self.app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            logger.info("Successfully acquired access token")
            self._save_cache()
            return result["access_token"]
        else:
            logger.error(f"Failed to acquire token: {result.get('error_description', result)}")
            return None

    def _save_cache(self):
        """Save token cache to file."""
        if self.cache.has_state_changed:
            self.TOKEN_CACHE_FILE.write_text(self.cache.serialize())
            logger.debug("Token cache saved")

    def clear_cache(self):
        """Clear the token cache."""
        if self.TOKEN_CACHE_FILE.exists():
            self.TOKEN_CACHE_FILE.unlink()
            logger.info("Token cache cleared")


def get_authenticated_session():
    """
    Get an authenticated session for Microsoft Graph API.

    Returns:
        Access token string.

    Raises:
        RuntimeError: If authentication fails.
    """
    authenticator = GraphAuthenticator()
    token = authenticator.get_access_token()

    if not token:
        raise RuntimeError("Failed to obtain access token")

    return token
