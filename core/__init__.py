"""
Core module for EmailAgent.

Contains shared components used across features:
- Gmail client (API wrapper)
- Authentication (OAuth 2.0)
- Deletion operations
- Logging and audit trail
- Configuration management
"""

from .config import (
    Config,
    load_config,
    save_default_config,
    ensure_directories,
    validate_config,
    get_default_config_dir,
    get_default_config_path,
)
from .logger import (
    setup_logger,
    get_logger,
    setup_deletion_logger,
    log_deletion,
    log_conflict,
    log_extraction,
)
from .auth import (
    get_credentials,
    get_gmail_service,
    check_auth_status,
    logout,
    AuthenticationError,
    CredentialsNotFoundError,
)
from .gmail_client import (
    GmailClient,
    Email,
    GmailAPIError,
)
from .deleter import (
    EmailDeleter,
    should_delete_email,
    contains_safety_keyword,
    DeletionResult,
    DeletionBatchResult,
)

__all__ = [
    # Config
    "Config",
    "load_config",
    "save_default_config",
    "ensure_directories",
    "validate_config",
    "get_default_config_dir",
    "get_default_config_path",
    # Logger
    "setup_logger",
    "get_logger",
    "setup_deletion_logger",
    "log_deletion",
    "log_conflict",
    "log_extraction",
    # Auth
    "get_credentials",
    "get_gmail_service",
    "check_auth_status",
    "logout",
    "AuthenticationError",
    "CredentialsNotFoundError",
    # Gmail Client
    "GmailClient",
    "Email",
    "GmailAPIError",
    # Deleter
    "EmailDeleter",
    "should_delete_email",
    "contains_safety_keyword",
    "DeletionResult",
    "DeletionBatchResult",
]
