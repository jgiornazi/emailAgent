"""
OAuth 2.0 authentication for Gmail API.

Handles:
- Initial authentication flow (browser-based)
- Token storage and refresh
- Credential management
"""

import json
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from .logger import get_logger

# Gmail API scopes required for the application
# readonly: Read emails and search
# modify: Move emails to trash
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class CredentialsNotFoundError(AuthenticationError):
    """Raised when credentials.json is not found."""

    pass


class TokenExpiredError(AuthenticationError):
    """Raised when token is expired and cannot be refreshed."""

    pass


def get_credentials(
    credentials_path: Path,
    token_path: Path,
    force_refresh: bool = False,
) -> Credentials:
    """
    Get valid credentials for Gmail API.

    Attempts to load existing token. If not found or invalid,
    initiates OAuth flow.

    Args:
        credentials_path: Path to credentials.json from Google Cloud Console.
        token_path: Path to store/load OAuth token.
        force_refresh: Force re-authentication even if token exists.

    Returns:
        Valid Credentials object.

    Raises:
        CredentialsNotFoundError: If credentials.json doesn't exist.
        AuthenticationError: If authentication fails.
    """
    logger = get_logger("auth")
    creds: Optional[Credentials] = None

    credentials_path = Path(credentials_path).expanduser()
    token_path = Path(token_path).expanduser()

    # Check credentials exist
    if not credentials_path.exists():
        raise CredentialsNotFoundError(
            f"Gmail credentials not found at: {credentials_path}\n"
            "Please download credentials.json from Google Cloud Console.\n"
            "See SETUP.md for instructions."
        )

    # Try to load existing token
    if not force_refresh and token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            logger.debug(f"Loaded token from {token_path}")
        except Exception as e:
            logger.warning(f"Failed to load token: {e}")
            creds = None

    # Check if token needs refresh
    if creds and creds.expired and creds.refresh_token:
        try:
            logger.info("Refreshing expired token...")
            creds.refresh(Request())
            _save_token(creds, token_path)
            logger.info("Token refreshed successfully")
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            creds = None

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        logger.info("Starting OAuth authentication flow...")
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
            _save_token(creds, token_path)
            logger.info("Authentication successful")
        except Exception as e:
            raise AuthenticationError(f"OAuth authentication failed: {e}") from e

    return creds


def _save_token(creds: Credentials, token_path: Path) -> None:
    """Save credentials to token file."""
    logger = get_logger("auth")
    token_path = Path(token_path)
    token_path.parent.mkdir(parents=True, exist_ok=True)

    with open(token_path, "w") as f:
        f.write(creds.to_json())

    logger.debug(f"Token saved to {token_path}")


def get_gmail_service(
    credentials_path: Path,
    token_path: Path,
    force_refresh: bool = False,
) -> Resource:
    """
    Get authenticated Gmail API service.

    Args:
        credentials_path: Path to credentials.json.
        token_path: Path to token.json.
        force_refresh: Force re-authentication.

    Returns:
        Gmail API service resource.
    """
    creds = get_credentials(credentials_path, token_path, force_refresh)
    service = build("gmail", "v1", credentials=creds)
    return service


def check_auth_status(token_path: Path) -> dict:
    """
    Check current authentication status.

    Args:
        token_path: Path to token.json.

    Returns:
        Dict with status information.
    """
    token_path = Path(token_path).expanduser()

    result = {
        "authenticated": False,
        "email": None,
        "token_path": str(token_path),
        "token_exists": token_path.exists(),
        "token_valid": False,
        "token_expired": False,
    }

    if not token_path.exists():
        return result

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        result["token_valid"] = creds.valid
        result["token_expired"] = creds.expired

        if creds.valid or (creds.expired and creds.refresh_token):
            result["authenticated"] = True

            # Try to get email address
            if creds.expired:
                creds.refresh(Request())

            service = build("gmail", "v1", credentials=creds)
            profile = service.users().getProfile(userId="me").execute()
            result["email"] = profile.get("emailAddress")

    except Exception:
        result["authenticated"] = False

    return result


def logout(token_path: Path, revoke: bool = False) -> bool:
    """
    Logout by deleting token.

    Args:
        token_path: Path to token.json.
        revoke: Whether to revoke the token with Google (optional).

    Returns:
        True if logout successful.
    """
    logger = get_logger("auth")
    token_path = Path(token_path).expanduser()

    if not token_path.exists():
        logger.info("No token found, already logged out")
        return True

    # Optionally revoke token with Google
    if revoke:
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            import requests

            requests.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": creds.token},
                headers={"content-type": "application/x-www-form-urlencoded"},
            )
            logger.info("Token revoked with Google")
        except Exception as e:
            logger.warning(f"Failed to revoke token: {e}")

    # Delete token file
    try:
        token_path.unlink()
        logger.info(f"Deleted token: {token_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete token: {e}")
        return False


def verify_scopes(token_path: Path) -> bool:
    """
    Verify that the token has the required scopes.

    Args:
        token_path: Path to token.json.

    Returns:
        True if all required scopes are present.
    """
    token_path = Path(token_path).expanduser()

    if not token_path.exists():
        return False

    try:
        with open(token_path, "r") as f:
            token_data = json.load(f)

        token_scopes = set(token_data.get("scopes", []))
        required_scopes = set(SCOPES)

        return required_scopes.issubset(token_scopes)
    except Exception:
        return False
