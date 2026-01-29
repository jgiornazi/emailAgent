# Job Tracker Module

The `job_tracker/` directory contains the email extraction and job application tracking pipeline. It processes Gmail messages, extracts structured data (company, position, status), and persists results to an Excel spreadsheet.

## Architecture

```
Email (from, subject, body)
        |
        v
  +--------------+
  | job_patterns  |  Regex patterns, keyword lists, provider lists
  +--------------+
        |
        v
  +--------------+
  |  extractor    |  Company + position extraction (domain -> subject -> body)
  +--------------+
        |
        v
  +--------------+
  |  classifier   |  Status classification (Applied/Interviewing/Rejected/Offer)
  +--------------+
        |
        v
  +--------------+        +-----------------+
  | excel_storage | <----> | ollama_client   |  (optional AI fallback)
  +--------------+        +-----------------+
```

## Modules

### `job_patterns.py` — Pattern Definitions

All regex patterns and keyword lists live here. Nothing else in the module contains raw patterns — everything references this file.

**Key data structures:**

| Name | Type | Purpose |
|------|------|---------|
| `GENERIC_PROVIDERS` | `List[str]` | Email domains to skip for company extraction (gmail, workday, greenhouse, etc.) |
| `ATS_PROVIDERS` | `set` | Subset of generic providers where the email local part (before `@`) may contain the company name (e.g. `disney@myworkday.com`) |
| `SUBJECT_COMPANY_PATTERNS` | `List[str]` | Regexes to extract company from subject lines |
| `BODY_COMPANY_PATTERNS` | `List[str]` | Regexes to extract company from email bodies |
| `POSITION_PATTERNS` | `List[str]` | Regexes to extract job titles (first 4 target subjects, rest target bodies) |
| `POSITION_KEYWORDS` | `List[str]` | Keywords that validate an extracted string is actually a job title |
| `STATUS_PATTERNS` | `Dict[str, List[str]]` | Regexes for each status category, ordered by distinctiveness |
| `STATUS_HIERARCHY` | `Dict[str, int]` | Level mapping: Applied=0, Interviewing/Rejected=1, Offer=2 |
| `COMPANY_CLEANUP_PATTERNS` | `List[tuple]` | Post-extraction cleanup (strip "Inc", "LLC", trailing punctuation, etc.) |
| `POSITION_CLEANUP_PATTERNS` | `List[tuple]` | Post-extraction cleanup for job titles |
| `JOB_EMAIL_SENDER_PREFIXES` | `List[str]` | Common sender prefixes that indicate job-related emails |

All patterns are pre-compiled at module load time into `COMPILED_*` variants for performance.

---

### `extractor.py` — Information Extraction

Extracts company name and job position from emails using a priority-based fallback chain.

**Company extraction order:**
1. **Domain** (`extract_company_from_domain`) — most reliable. Parses the sender's email domain. Skips known generic providers. For ATS domains, falls back to the email local part (e.g. `disney@myworkday.com` -> "Disney").
2. **Subject** (`extract_company_from_subject`) — pattern matches against subject line.
3. **Body** (`extract_company_from_body`) — pattern matches against first 500 chars of body.
4. Falls back to `"Unknown"`.

**Position extraction order:**
1. **Subject** (`extract_position_from_subject`) — first 4 compiled patterns.
2. **Body** (`extract_position_from_body`) — remaining compiled patterns, first 500 chars.
3. Falls back to `"Not specified"`.

Both extraction paths run cleanup patterns and validate results (length bounds, keyword presence for positions, filtering out generic phrases for companies).

**Key data class: `ExtractionResult`**
- `company`, `position`, `status` — the extracted fields
- `company_source`, `position_source` — where each was found (`domain`, `subject`, `body`, `sender`, `ai`)
- `confidence` / `confidence_score` — weighted scoring result (see `docs/confidence-scoring.md`)
- `extraction_method` — `pattern`, `ai`, `hybrid`, or `ai_failed`

**Special handling:**
- LinkedIn Easy Apply emails (`jobs-noreply@linkedin.com`) are handled separately with dedicated patterns before the general pipeline runs.

**Entry points:**
- `extract_email_info(email, config)` — full pipeline (pattern match + optional AI)
- `pattern_match_extraction(email)` — pattern-only extraction
- `should_use_ai(pattern_result, use_ai_enabled)` — decides whether to invoke Ollama

---

### `classifier.py` — Status Classification

Classifies emails into one of four statuses: **Applied**, **Interviewing**, **Rejected**, **Offer**.

**How classification works:**

1. Combines subject + body into a single lowercase text blob.
2. Checks every compiled pattern in `STATUS_PATTERNS` against the text, counting matches per status.
3. Applies override rules:
   - **Strong rejection phrases** (e.g. "not moving forward", "unfortunately") force `Rejected` when rejection patterns have any matches, regardless of other scores.
   - **Strong applied phrases** (e.g. "thank you for applying", "application received") force `Applied` over `Interviewing`, but not over `Offer` or `Rejected`.
4. If no override fires, the status with the highest match count wins. Ties break in favor of higher-priority statuses (`Rejected > Offer > Interviewing > Applied`).
5. Special case: if both `Offer` and `Rejected` match, `Offer` wins when its count >= `Rejected`'s count.

**Status hierarchy and transitions:**

```
Level 0: Applied
Level 1: Interviewing, Rejected  (sideways moves allowed between these)
Level 2: Offer
```

- Status can move **up** or **sideways**, never **down**.
- Downgrade attempts are blocked and recorded as conflicts in the Excel notes column.
- `can_update_status(current, new)` enforces these rules and returns a `StatusUpdateResult`.

**Other utilities:**
- `is_deletable_status(status)` — only `Applied` and `Rejected` emails are deletion candidates.
- `is_protected_status(status)` — `Interviewing` and `Offer` are always kept.
- `normalize_status(status)` — maps variations like "submitted", "screening", "declined" to canonical names.

---

### `excel_storage.py` — Excel Persistence

Manages the `job_applications.xlsx` file using `openpyxl`.

**Spreadsheet schema:**

| Column | Header | Content |
|--------|--------|---------|
| A | Company Name | Extracted company |
| B | Position | Job title |
| C | Status | Applied / Interviewing / Rejected / Offer |
| D | Confidence | high / medium / low |
| E | Date First Seen | When first email was processed |
| F | Date Last Updated | When latest email was processed |
| G | Email IDs | Comma-separated Gmail message IDs |
| H | Notes | Conflict flags, "NEEDS REVIEW" for low confidence |

**Key behaviors:**
- **Deduplication**: Companies are matched case-insensitively via an in-memory cache (`_company_cache`). If a company already has a row, the existing row is updated rather than creating a duplicate.
- **Status hierarchy enforcement**: `update_existing_row()` calls `can_update_status()` before changing status. Blocked transitions write a conflict note instead.
- **Conflict handling**: When a status downgrade is attempted, the notes column gets a `"Conflict: received X after Y on DATE"` entry and the cell is highlighted red.
- **Auto-backup**: On load, the current file is backed up to `~/.emailagent/backups/` with a timestamp. Old backups are cleaned up after a configurable retention period (default 7 days).
- **Conditional formatting**: Status cells are color-coded (blue=Applied, yellow=Interviewing, red=Rejected, green=Offer).
- **Export**: `export_to_csv()` and `export_to_json()` for external consumption.
- **Batch save**: `save_if_needed(threshold)` auto-saves after N unsaved changes to avoid data loss during large scans.

---

### `ollama_client.py` — AI Fallback (Optional)

Provides AI-powered extraction via a local Ollama instance as a fallback when pattern matching produces low-confidence results. Requires `--use-ai` flag.

**When AI is triggered** (via `should_use_ai()` in extractor):
- Confidence level is `low`
- Company is `"Unknown"`
- Status is `"Applied"` with fewer than 2 pattern matches (uncertain default)

**How it works:**
1. Sends a structured prompt to Ollama with the email's sender, subject, and body (truncated to 2000 chars).
2. Requests JSON output with `company_name`, `position`, and `status`.
3. Parses the response, handling clean JSON, embedded JSON, and code-block-wrapped JSON.
4. Validates the extracted status against the four valid values.

**Merge strategy** (`ai_extract_email()`):
- Company: domain extraction always wins over AI. AI fills in when pattern returned `"Unknown"`.
- Position: pattern result wins if it found something. AI fills in gaps.
- Status: pattern result wins if it had 2+ matches. Otherwise AI's classification is used.
- Confidence is recalculated after merging.

**Configuration:**
- `host`: Ollama server URL (default `http://localhost:11434`)
- `model`: Model name (default `llama3.2:3b`)
- `timeout`: Request timeout in seconds (default 30)
- `max_retries`: Retry count on timeout (default 2)
- `temperature`: Set to 0.1 for deterministic output

**Error handling:**
- `OllamaConnectionError` — server unreachable
- `OllamaTimeoutError` — request exceeded timeout (retried up to `max_retries` times)
- `OllamaResponseError` — non-200 response
- All errors result in graceful fallback to pattern-only results.
