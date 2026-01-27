"""
Gmail API client wrapper.

Provides high-level operations for:
- Searching emails with queries
- Fetching email details
- Moving emails to trash
- Restoring emails from trash
"""

import base64
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generator, Optional

from dateutil import parser as date_parser
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from .logger import get_logger, log_api_call


class GmailAPIError(Exception):
    """Raised when Gmail API call fails."""

    pass


class RateLimitError(GmailAPIError):
    """Raised when rate limit is hit."""

    pass


@dataclass
class Email:
    """Email data container."""

    id: str
    subject: str
    sender: str
    body: str
    snippet: str
    date: Optional[datetime]
    labels: list[str]
    is_starred: bool = False
    has_attachments: bool = False

    @property
    def text(self) -> str:
        """Get combined subject and body for analysis."""
        return f"{self.subject} {self.body}"


class GmailClient:
    """Gmail API client wrapper."""

    # Job email search queries
    JOB_SEARCH_QUERIES = [
        'subject:(application OR applied OR "thank you for applying")',
        'subject:(interview OR "phone screen" OR "next steps")',
        'subject:(offer OR "job offer" OR "offer letter")',
        'subject:(rejection OR "not moving forward")',
        '"your application" OR "application status"',
    ]

    def __init__(
        self,
        service: Resource,
        batch_size: int = 100,
        requests_per_second: int = 10,
    ):
        """
        Initialize Gmail client.

        Args:
            service: Gmail API service resource.
            batch_size: Number of emails per API request.
            requests_per_second: Rate limit for API calls.
        """
        self.service = service
        self.batch_size = batch_size
        self.requests_per_second = requests_per_second
        self.logger = get_logger("gmail")

    def search_job_emails(
        self,
        max_results: int = 10000,
        since_date: Optional[datetime] = None,
    ) -> list[str]:
        """
        Search for job-related emails using predefined queries.

        Args:
            max_results: Maximum number of emails to return.
            since_date: Only return emails after this date.

        Returns:
            List of unique email IDs.
        """
        all_email_ids: set[str] = set()

        for query in self.JOB_SEARCH_QUERIES:
            # Add date filter if specified
            if since_date:
                date_str = since_date.strftime("%Y/%m/%d")
                query = f"{query} after:{date_str}"

            self.logger.debug(f"Searching: {query[:60]}...")

            try:
                ids = self._search_emails(query, max_results - len(all_email_ids))
                all_email_ids.update(ids)

                if len(all_email_ids) >= max_results:
                    break

            except GmailAPIError as e:
                self.logger.error(f"Search failed for query: {e}")
                continue

        self.logger.info(f"Found {len(all_email_ids)} unique job emails")
        return list(all_email_ids)

    def _search_emails(
        self,
        query: str,
        max_results: int,
    ) -> list[str]:
        """
        Execute a single search query.

        Args:
            query: Gmail search query.
            max_results: Maximum results to return.

        Returns:
            List of email IDs matching the query.
        """
        email_ids: list[str] = []
        page_token: Optional[str] = None

        while len(email_ids) < max_results:
            try:
                results = (
                    self.service.users()
                    .messages()
                    .list(
                        userId="me",
                        q=query,
                        maxResults=min(self.batch_size, max_results - len(email_ids)),
                        pageToken=page_token,
                    )
                    .execute()
                )

                log_api_call("messages.list", "GET", 200)

                if "messages" in results:
                    for msg in results["messages"]:
                        email_ids.append(msg["id"])

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

                # Rate limiting
                time.sleep(1.0 / self.requests_per_second)

            except HttpError as error:
                log_api_call("messages.list", "GET", error=str(error))

                if error.resp.status == 429:
                    self.logger.warning("Rate limit hit, waiting 10 seconds...")
                    time.sleep(10)
                    continue
                else:
                    raise GmailAPIError(f"Search failed: {error}") from error

        return email_ids

    def fetch_emails(
        self,
        email_ids: list[str],
        progress_callback: Optional[callable] = None,
    ) -> Generator[Email, None, None]:
        """
        Fetch full details for list of emails.

        Args:
            email_ids: List of email IDs to fetch.
            progress_callback: Optional callback for progress updates.

        Yields:
            Email objects with full details.
        """
        total = len(email_ids)

        for i, email_id in enumerate(email_ids):
            try:
                email = self._fetch_email(email_id)
                if email:
                    yield email

                # Progress callback
                if progress_callback and (i + 1) % 100 == 0:
                    progress_callback(i + 1, total)

                # Rate limiting
                if (i + 1) % self.batch_size == 0:
                    time.sleep(1.0 / self.requests_per_second)

            except GmailAPIError as e:
                self.logger.warning(f"Failed to fetch email {email_id}: {e}")
                continue

    def _fetch_email(self, email_id: str) -> Optional[Email]:
        """
        Fetch a single email by ID.

        Args:
            email_id: Gmail message ID.

        Returns:
            Email object or None if failed.
        """
        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=email_id, format="full")
                .execute()
            )

            log_api_call("messages.get", "GET", 200)

            return self._parse_email(msg)

        except HttpError as error:
            log_api_call("messages.get", "GET", error=str(error))

            if error.resp.status == 429:
                self.logger.warning("Rate limit hit, waiting...")
                time.sleep(10)
                return self._fetch_email(email_id)

            raise GmailAPIError(f"Fetch failed: {error}") from error

    def _parse_email(self, msg: dict[str, Any]) -> Email:
        """Parse Gmail API message into Email object."""
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

        subject = headers.get("Subject", "")
        sender = headers.get("From", "")
        date_str = headers.get("Date", "")

        # Parse date
        email_date = None
        if date_str:
            try:
                email_date = date_parser.parse(date_str)
            except Exception:
                pass

        # Extract body
        body = self._extract_body(msg["payload"])

        # Check for attachments
        has_attachments = self._has_attachments(msg["payload"])

        # Check labels
        labels = msg.get("labelIds", [])
        is_starred = "STARRED" in labels

        return Email(
            id=msg["id"],
            subject=subject,
            sender=sender,
            body=body,
            snippet=msg.get("snippet", ""),
            date=email_date,
            labels=labels,
            is_starred=is_starred,
            has_attachments=has_attachments,
        )

    def _extract_body(self, payload: dict[str, Any]) -> str:
        """Extract email body from payload."""
        # Direct body data
        if "body" in payload and "data" in payload["body"]:
            data = payload["body"]["data"]
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        # Multi-part message
        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")

                # Prefer plain text
                if mime_type == "text/plain":
                    if "data" in part.get("body", {}):
                        data = part["body"]["data"]
                        return base64.urlsafe_b64decode(data).decode(
                            "utf-8", errors="ignore"
                        )

                # Recurse into nested parts
                if "parts" in part:
                    body = self._extract_body(part)
                    if body:
                        return body

            # Fall back to HTML if no plain text
            for part in payload["parts"]:
                if part.get("mimeType") == "text/html":
                    if "data" in part.get("body", {}):
                        data = part["body"]["data"]
                        html = base64.urlsafe_b64decode(data).decode(
                            "utf-8", errors="ignore"
                        )
                        # Strip HTML tags (simple approach)
                        import re

                        return re.sub(r"<[^>]+>", " ", html)

        return ""

    def _has_attachments(self, payload: dict[str, Any]) -> bool:
        """Check if email has attachments."""
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("filename"):
                    return True
                if "parts" in part:
                    if self._has_attachments(part):
                        return True
        return False

    def trash_email(self, email_id: str) -> bool:
        """
        Move email to trash.

        Args:
            email_id: Gmail message ID.

        Returns:
            True if successful.
        """
        try:
            self.service.users().messages().trash(userId="me", id=email_id).execute()

            log_api_call("messages.trash", "POST", 200)
            return True

        except HttpError as error:
            log_api_call("messages.trash", "POST", error=str(error))

            if error.resp.status == 429:
                self.logger.warning("Rate limit hit, waiting...")
                time.sleep(10)
                return self.trash_email(email_id)

            self.logger.error(f"Failed to trash email {email_id}: {error}")
            return False

    def trash_emails_batch(
        self,
        email_ids: list[str],
        delay: float = 0.1,
        progress_callback: Optional[callable] = None,
    ) -> tuple[int, list[str]]:
        """
        Move multiple emails to trash.

        Args:
            email_ids: List of email IDs to trash.
            delay: Delay between deletions (rate limiting).
            progress_callback: Optional callback for progress.

        Returns:
            Tuple of (success_count, failed_ids).
        """
        success = 0
        failed: list[str] = []

        for i, email_id in enumerate(email_ids):
            if self.trash_email(email_id):
                success += 1
            else:
                failed.append(email_id)

            # Progress callback
            if progress_callback:
                progress_callback(i + 1, len(email_ids))

            # Rate limiting
            time.sleep(delay)

        return success, failed

    def untrash_email(self, email_id: str) -> bool:
        """
        Restore email from trash.

        Args:
            email_id: Gmail message ID.

        Returns:
            True if successful.
        """
        try:
            self.service.users().messages().untrash(userId="me", id=email_id).execute()

            log_api_call("messages.untrash", "POST", 200)
            return True

        except HttpError as error:
            log_api_call("messages.untrash", "POST", error=str(error))
            self.logger.error(f"Failed to untrash email {email_id}: {error}")
            return False

    def untrash_emails_batch(
        self,
        email_ids: list[str],
        progress_callback: Optional[callable] = None,
    ) -> tuple[int, list[str]]:
        """
        Restore multiple emails from trash.

        Args:
            email_ids: List of email IDs to restore.
            progress_callback: Optional callback for progress.

        Returns:
            Tuple of (success_count, failed_ids).
        """
        success = 0
        failed: list[str] = []

        for i, email_id in enumerate(email_ids):
            if self.untrash_email(email_id):
                success += 1
            else:
                failed.append(email_id)

            if progress_callback:
                progress_callback(i + 1, len(email_ids))

            time.sleep(0.1)

        return success, failed

    def get_user_email(self) -> str:
        """Get the authenticated user's email address."""
        try:
            profile = self.service.users().getProfile(userId="me").execute()
            return profile.get("emailAddress", "")
        except HttpError as error:
            self.logger.error(f"Failed to get user profile: {error}")
            return ""
