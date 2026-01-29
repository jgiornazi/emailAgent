# Core Module

The `core/` directory contains the foundational infrastructure that the rest of the application depends on: authentication, Gmail API interaction, configuration management, logging, and email deletion.

## Modules

### `auth.py` — OAuth 2.0 Authentication

Handles the Google OAuth 2.0 flow for Gmail API access.

**Scopes requested:**
- `gmail.readonly` — read email content
- `gmail.modify` — trash/untrash emails

**Credential flow:**
1. On first run (`get_credentials()`), opens a browser for Google sign-in.
2. The returned token is saved to `~/.emailagent/token.json` (600 permissions).
3. On subsequent runs, the saved token is loaded and refreshed if expired.
4. If the refresh token is also expired, re-authentication is triggered.

**Key functions:**

| Function | Purpose |
|----------|---------|
| `get_credentials(config)` | Load or create OAuth credentials. Triggers browser auth if needed. |
| `get_gmail_service(credentials)` | Build an authenticated Gmail API service object. |
| `check_auth_status(config)` | Check if valid credentials exist without triggering auth. |
| `logout(config, revoke)` | Delete local token. Optionally revoke the token with Google. |
| `verify_scopes(credentials)` | Confirm the token has the required scopes. |

**Exceptions:**
- `AuthenticationError` — base auth error
- `CredentialsNotFoundError` — `credentials.json` not found at configured path
- `TokenExpiredError` — token refresh failed

---

### `gmail_client.py` — Gmail API Wrapper

Provides a high-level interface to the Gmail API with rate limiting and batch operations.

**`Email` dataclass:**
- `id`, `subject`, `sender`, `body`, `snippet`, `date`, `labels`, `starred`, `attachments`

**`GmailClient` class:**

| Method | Purpose |
|--------|---------|
| `search_job_emails(max_results, since)` | Searches Gmail using 7 predefined job-related queries |
| `fetch_emails(message_ids)` | Generator that yields full `Email` objects with decoded bodies |
| `trash_email(email_id)` | Move a single email to trash |
| `untrash_email(email_id)` | Restore a single email from trash |
| `trash_emails_batch(email_ids)` | Batch trash with progress tracking |
| `untrash_emails_batch(email_ids)` | Batch untrash |
| `get_user_email()` | Get the authenticated user's email address |

**Job search queries** (`JOB_SEARCH_QUERIES`):
The client uses 7 Gmail search queries to find job-related emails, covering application confirmations, interview requests, rejection notifications, offer letters, and messages from known ATS platforms (Greenhouse, Lever, Workday, etc.).

**Rate limiting:**
Requests are throttled to a configurable rate (default 10/second) to stay within Gmail API quotas.

**Exceptions:**
- `GmailAPIError` — general API errors
- `RateLimitError` — quota exceeded

---

### `config.py` — Configuration Management

YAML-based configuration with dataclass validation and environment variable overrides.

**Configuration hierarchy:**
1. Default values (hardcoded in dataclasses)
2. Config file (`~/.emailagent/config.yaml`)
3. Environment variables (override specific settings)

**Config sections:**

| Section | Dataclass | Key settings |
|---------|-----------|--------------|
| Gmail | `GmailConfig` | `credentials_path`, `token_path`, `batch_size`, `requests_per_second` |
| Extraction | `ExtractionConfig` | `use_ai`, `confidence_threshold` |
| Ollama | `OllamaConfig` | `host`, `model`, `timeout`, `max_retries` |
| Excel | `ExcelConfig` | `file_path`, `sheet_name`, `auto_backup`, `backup_retention_days` |
| Deletion | `DeletionConfig` | Deletion rules, safety keywords, batch settings |
| Logging | `LoggingConfig` | Log levels, directories, retention |
| CLI | `CLIConfig` | Display settings (colors, progress bars, pagination) |
| Advanced | `AdvancedConfig` | Parallel extraction, caching, performance tuning |

**Key functions:**

| Function | Purpose |
|----------|---------|
| `load_config(path)` | Load and validate config from YAML file |
| `validate_config(config)` | Check for invalid or missing values |
| `save_default_config(path)` | Write `config.yaml.example` to disk |
| `ensure_directories(config)` | Create `~/.emailagent/`, `backups/`, `logs/`, `cache/` |

---

### `logger.py` — Structured Logging

Logging system with rotating file handlers and colored console output via Rich.

**Logger setup:**
- Console output uses `RichHandler` for colored, formatted output.
- File output uses `RotatingFileHandler` (10MB max, 5 backups).
- Log files are written to `~/.emailagent/logs/`.

**Specialized loggers:**

| Function | Purpose |
|----------|---------|
| `setup_logger(name, config)` | Create a logger with console + file handlers |
| `setup_deletion_logger(config)` | Separate audit trail logger for deletion operations |

**Structured log functions:**

| Function | What it logs |
|----------|-------------|
| `log_deletion(logger, email_id, company, reason)` | Email deletion events |
| `log_conflict(logger, company, old_status, new_status)` | Status hierarchy conflicts |
| `log_extraction(logger, email_id, company, position, status)` | Extraction results |
| `log_api_call(logger, endpoint, status_code)` | Gmail API calls |

**Maintenance:**
- `cleanup_old_logs(log_dir, retention_days)` — removes logs older than retention period.

---

### `deleter.py` — Email Deletion with Safety Checks

Handles email deletion decisions and batch operations with multiple safety layers.

**Safety keyword system:**
`DEFAULT_SAFETY_KEYWORDS` contains 99 keywords that prevent deletion when found in an email's subject or body. Categories include:
- Interview signals: "interview", "phone screen", "video call", "on-site"
- Offer signals: "offer letter", "compensation", "start date", "onboarding"
- Action required: "assessment", "take-home", "coding challenge", "background check"
- Scheduling: "calendar invite", "availability", "schedule"

**Deletion rules** (`should_delete_email()`):
1. Never delete emails with protected statuses (`Interviewing`, `Offer`) unless overridden.
2. Never delete starred emails (configurable).
3. Never delete emails with conflicts (configurable).
4. Never delete emails with attachments (configurable).
5. Check for safety keywords — if any match, block deletion.
6. Only delete `Applied` and `Rejected` status emails by default.

Returns a `DeletionResult` with `should_delete`, `reason`, and the matched `safety_keyword` if blocked.

**`EmailDeleter` class:**

| Method | Purpose |
|--------|---------|
| `delete_emails(emails, gmail_client)` | Batch delete with progress, returns `DeletionBatchResult` |
| `undo_last_batch()` | Restore all emails from the last deletion batch |
| `get_last_batch()` | Retrieve last batch metadata |
| `cleanup_old_batch_files(retention_days)` | Remove old batch records |

Batch metadata is saved to disk so `undo_last_batch()` can restore emails even across sessions.
