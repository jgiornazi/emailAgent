"""
Email deletion operations for EmailAgent.

Provides safe deletion logic with:
- Safety keyword checking
- Status-based deletion rules
- Batch operations with progress
- Audit logging
- Undo functionality
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .gmail_client import Email, GmailClient
from .logger import (
    get_logger,
    log_deletion,
    log_deletion_batch_complete,
    log_deletion_batch_start,
)


# Safety keywords that prevent deletion
DEFAULT_SAFETY_KEYWORDS = [
    # Interview-related
    "interview",
    "phone screen",
    "video call",
    "video interview",
    "zoom call",
    "teams meeting",
    "google meet",
    "next steps",
    "schedule a call",
    "schedule call",
    "schedule a meeting",
    "schedule meeting",
    "speak with",
    "meet with",
    "meeting",
    "call with",
    "chat with",
    # Assessment-related
    "assessment",
    "technical challenge",
    "coding challenge",
    "programming challenge",
    "take-home",
    "take home",
    "homework",
    "project",
    "assignment",
    "test",
    "exercise",
    # Offer-related
    "offer",
    "job offer",
    "offer letter",
    "compensation",
    "salary",
    "benefits",
    "stock options",
    "equity",
    "sign-on bonus",
    "signing bonus",
    "relocation",
    "start date",
    # Time-sensitive
    "urgent",
    "asap",
    "immediately",
    "deadline",
    "respond by",
    "reply by",
    "due date",
    "time-sensitive",
    # Account/security
    "password",
    "account",
    "verify",
    "verification",
    "security",
    "two-factor",
    "2fa",
    "authenticate",
    "reset",
    # Document requests
    "references",
    "background check",
    "documents",
    "upload",
    "submit",
    "provide",
    "send us",
]


@dataclass
class DeletionResult:
    """Result of deletion decision."""

    should_delete: bool
    reason: str
    safety_keyword: Optional[str] = None


@dataclass
class DeletionBatchResult:
    """Result of a batch deletion operation."""

    total_requested: int
    deleted_count: int
    failed_count: int
    kept_count: int
    failed_ids: list[str]
    batch_id: str
    timestamp: datetime


def contains_safety_keyword(
    text: str,
    safety_keywords: Optional[list[str]] = None,
) -> tuple[bool, Optional[str]]:
    """
    Check if text contains any safety keywords.

    Args:
        text: Combined subject + body text.
        safety_keywords: List of keywords to check. Uses defaults if None.

    Returns:
        Tuple of (has_keyword, keyword_found).
    """
    if safety_keywords is None:
        safety_keywords = DEFAULT_SAFETY_KEYWORDS

    text_lower = text.lower()

    for keyword in safety_keywords:
        if keyword.lower() in text_lower:
            return True, keyword

    return False, None


def should_delete_email(
    status: str,
    email_text: str,
    is_conflict: bool = False,
    is_starred: bool = False,
    has_attachments: bool = False,
    safety_keywords: Optional[list[str]] = None,
    delete_applied: bool = True,
    delete_rejected: bool = True,
    delete_interviewing: bool = False,
    delete_offer: bool = False,
    never_delete_starred: bool = True,
    never_delete_with_attachments: bool = False,
    never_delete_conflicts: bool = True,
) -> DeletionResult:
    """
    Determine if an email should be deleted.

    Args:
        status: Email status (Applied, Interviewing, Rejected, Offer).
        email_text: Combined subject + body text.
        is_conflict: Whether this email created a status conflict.
        is_starred: Whether the email is starred.
        has_attachments: Whether the email has attachments.
        safety_keywords: List of safety keywords.
        delete_applied: Whether to delete Applied emails.
        delete_rejected: Whether to delete Rejected emails.
        delete_interviewing: Whether to delete Interviewing emails.
        delete_offer: Whether to delete Offer emails.
        never_delete_starred: Never delete starred emails.
        never_delete_with_attachments: Never delete emails with attachments.
        never_delete_conflicts: Never delete conflict emails.

    Returns:
        DeletionResult with decision and reason.
    """
    # Rule 1: Never delete Interviewing (by default)
    if status == "Interviewing" and not delete_interviewing:
        return DeletionResult(False, "Status is Interviewing (always kept)")

    # Rule 2: Never delete Offer (by default)
    if status == "Offer" and not delete_offer:
        return DeletionResult(False, "Status is Offer (always kept)")

    # Rule 3: Never delete conflicts
    if is_conflict and never_delete_conflicts:
        return DeletionResult(False, "Email created status conflict (requires review)")

    # Rule 4: Never delete starred
    if is_starred and never_delete_starred:
        return DeletionResult(False, "Email is starred (protected)")

    # Rule 5: Never delete with attachments (optional)
    if has_attachments and never_delete_with_attachments:
        return DeletionResult(False, "Email has attachments (protected)")

    # Rule 6: Check safety keywords
    has_keyword, keyword = contains_safety_keyword(email_text, safety_keywords)
    if has_keyword:
        return DeletionResult(
            False, f"Contains safety keyword: '{keyword}'", keyword
        )

    # Rule 7: Delete Applied if allowed
    if status == "Applied" and delete_applied:
        return DeletionResult(True, "Status is Applied (safe to delete)")

    # Rule 8: Delete Rejected if allowed
    if status == "Rejected" and delete_rejected:
        return DeletionResult(True, "Status is Rejected (safe to delete)")

    # Default: don't delete
    return DeletionResult(False, f"Status is {status} (not configured for deletion)")


class EmailDeleter:
    """Handles email deletion operations."""

    def __init__(
        self,
        gmail_client: GmailClient,
        log_directory: Optional[Path] = None,
        safety_keywords: Optional[list[str]] = None,
    ):
        """
        Initialize email deleter.

        Args:
            gmail_client: Gmail client for API operations.
            log_directory: Directory for deletion logs.
            safety_keywords: Custom safety keywords (uses defaults if None).
        """
        self.gmail_client = gmail_client
        self.logger = get_logger("deleter")
        self.safety_keywords = safety_keywords or DEFAULT_SAFETY_KEYWORDS

        if log_directory:
            self.log_directory = Path(log_directory)
            self.log_directory.mkdir(parents=True, exist_ok=True)
        else:
            from .config import get_default_config_dir

            self.log_directory = get_default_config_dir() / "logs"
            self.log_directory.mkdir(parents=True, exist_ok=True)

    def delete_emails(
        self,
        emails_to_delete: list[tuple[str, str, str, str]],
        delay: float = 0.1,
        progress_callback: Optional[callable] = None,
    ) -> DeletionBatchResult:
        """
        Delete a batch of emails.

        Args:
            emails_to_delete: List of (email_id, company, status, subject) tuples.
            delay: Delay between deletions.
            progress_callback: Optional progress callback.

        Returns:
            DeletionBatchResult with operation results.
        """
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        total = len(emails_to_delete)

        # Log batch start
        log_deletion_batch_start(total)
        self.logger.info(f"Starting deletion batch {batch_id}: {total} emails")

        deleted = 0
        failed: list[str] = []

        for i, (email_id, company, status, subject) in enumerate(emails_to_delete):
            success = self.gmail_client.trash_email(email_id)

            if success:
                deleted += 1
                log_deletion(email_id, company, status, subject)
            else:
                failed.append(email_id)

            if progress_callback:
                progress_callback(i + 1, total)

        # Log batch complete
        log_deletion_batch_complete(deleted, len(failed))
        self.logger.info(
            f"Batch {batch_id} complete: {deleted} deleted, {len(failed)} failed"
        )

        # Save batch info for undo
        self._save_batch_info(batch_id, emails_to_delete, deleted, failed)

        return DeletionBatchResult(
            total_requested=total,
            deleted_count=deleted,
            failed_count=len(failed),
            kept_count=0,
            failed_ids=failed,
            batch_id=batch_id,
            timestamp=datetime.now(),
        )

    def _save_batch_info(
        self,
        batch_id: str,
        emails: list[tuple[str, str, str, str]],
        deleted: int,
        failed: list[str],
    ) -> None:
        """Save batch info for potential undo."""
        batch_file = self.log_directory / f"batch_{batch_id}.json"

        batch_data = {
            "batch_id": batch_id,
            "timestamp": datetime.now().isoformat(),
            "total_emails": len(emails),
            "deleted_count": deleted,
            "failed_count": len(failed),
            "email_ids": [e[0] for e in emails],
            "emails": [
                {"id": e[0], "company": e[1], "status": e[2], "subject": e[3]}
                for e in emails
            ],
            "failed_ids": failed,
        }

        with open(batch_file, "w") as f:
            json.dump(batch_data, f, indent=2)

        self.logger.debug(f"Saved batch info to {batch_file}")

    def get_last_batch(self) -> Optional[dict]:
        """
        Get information about the last deletion batch.

        Returns:
            Dict with batch info or None if no batches found.
        """
        batch_files = sorted(
            self.log_directory.glob("batch_*.json"), reverse=True
        )

        if not batch_files:
            return None

        with open(batch_files[0], "r") as f:
            return json.load(f)

    def undo_last_batch(
        self,
        progress_callback: Optional[callable] = None,
    ) -> Optional[tuple[int, list[str]]]:
        """
        Undo the last deletion batch.

        Args:
            progress_callback: Optional progress callback.

        Returns:
            Tuple of (restored_count, failed_ids) or None if no batch.
        """
        batch_info = self.get_last_batch()

        if not batch_info:
            self.logger.warning("No deletion batch found to undo")
            return None

        email_ids = batch_info.get("email_ids", [])
        self.logger.info(f"Restoring {len(email_ids)} emails from batch {batch_info['batch_id']}")

        restored, failed = self.gmail_client.untrash_emails_batch(
            email_ids, progress_callback
        )

        self.logger.info(f"Restored {restored} emails, {len(failed)} failed")

        return restored, failed

    def cleanup_old_batch_files(self, retention_days: int = 30) -> int:
        """
        Clean up old batch files.

        Args:
            retention_days: Days to keep batch files.

        Returns:
            Number of files deleted.
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=retention_days)
        deleted = 0

        for batch_file in self.log_directory.glob("batch_*.json"):
            try:
                mtime = datetime.fromtimestamp(batch_file.stat().st_mtime)
                if mtime < cutoff:
                    batch_file.unlink()
                    deleted += 1
            except (OSError, PermissionError):
                continue

        if deleted > 0:
            self.logger.info(f"Cleaned up {deleted} old batch files")

        return deleted
