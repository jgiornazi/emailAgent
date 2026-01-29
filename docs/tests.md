# Tests

The `tests/` directory contains pytest test suites for the job tracker module. Tests are run with coverage reporting via `pytest-cov`.

## Running Tests

```bash
# Run all tests with verbose output
source .venv/bin/activate
pytest tests/ -v

# Run a specific test file
pytest tests/test_job_tracker/test_extractor.py -v

# Run a specific test class
pytest tests/test_job_tracker/test_classifier.py::TestClassifyStatusRejected -v

# Run with coverage report
pytest tests/ --cov=job_tracker --cov-report=html
```

Coverage HTML output is written to `htmlcov/`.

## Directory Structure

```
tests/
  __init__.py
  test_core/
    __init__.py
  test_job_tracker/
    __init__.py
    test_extractor.py     # 107 tests total (shared with classifier)
    test_classifier.py
```

## Test Suites

### `test_extractor.py` — Extraction Tests

Tests for company extraction, position extraction, confidence scoring, and the full extraction pipeline.

**Test classes:**

| Class | Tests | What it covers |
|-------|-------|----------------|
| `TestExtractCompanyFromDomain` | 12 | Domain parsing: simple domains, `.ai` TLDs, subdomains, hyphenated names, generic providers (greenhouse, lever, gmail), full name format (`John <john@co.com>`), empty/invalid input |
| `TestExtractCompanyFromSubject` | 7 | Subject patterns: "thank you for applying to X", "application to X", "update from X", "application received \| X", "your application at X", "application was sent to X", no-match case |
| `TestExtractCompanyFromBody` | 4 | Body patterns: "interest in X", "applied to X", "role at X", "here at X" |
| `TestExtractCompany` | 4 | Full extraction priority chain: domain > subject > body > "Unknown" |
| `TestExtractPosition` | 4 | Position from subject ("application for Software Engineer"), position with level ("Senior"), position from body, fallback to "Not specified" |
| `TestConfidenceScoring` | 3 | High confidence (all fields + domain), low confidence (nothing extracted), domain bonus (+0.1) |
| `TestShouldUseAI` | 3 | AI disabled returns false, low confidence triggers AI, high confidence skips AI |
| `TestRealEmailExamples` | 6 | Real-world emails: Perplexity, Plaid, Neuralink, Gem (rejection), Vercel, Robinhood (rejection) |
| `TestExtractEmailInfo` | 2 | Full pipeline integration, `ExtractionResult.to_dict()` serialization |

**Real email examples** are sourced from the PRD and test against actual sender addresses, subjects, and body snippets to validate end-to-end extraction.

---

### `test_classifier.py` — Classification Tests

Tests for status classification, hierarchy enforcement, conflict handling, and status validation.

**Test classes:**

| Class | Tests | What it covers |
|-------|-------|----------------|
| `TestClassifyStatusApplied` | 5 | "Thank you for applying", "received your application", "we will review", Perplexity real email, Plaid real email |
| `TestClassifyStatusRejected` | 6 | "Not moving forward", "won't be advancing", "wish you success", Gem real email, Robinhood real email, Attentive real email |
| `TestClassifyStatusInterviewing` | 5 | "Interview" keyword with scheduling context, "phone screen", "schedule a call", "technical assessment", "take-home assignment" |
| `TestClassifyStatusOffer` | 4 | "Pleased to offer", "job offer", "welcome to the team", "compensation package" |
| `TestStatusHierarchy` | 4 | Level values: Applied=0, Interviewing=1, Rejected=1, Offer=2 |
| `TestCanUpdateStatus` | 7 | Allowed transitions (Applied->Interviewing, Applied->Rejected, Interviewing->Offer, etc.) and blocked transitions (Offer->Rejected, Interviewing->Applied, etc.) |
| `TestConflictNote` | 2 | Conflict note formatting with and without date |
| `TestDeletionStatus` | 5 | Deletable statuses (Applied, Rejected), non-deletable (Interviewing, Offer), protected status checks |
| `TestStatusValidation` | 4 | Valid status strings, invalid status rejection |
| `TestStatusNormalization` | 4 | Mapping variations to canonical names: "submitted"/"application" -> Applied, "interview"/"screening" -> Interviewing, "rejection"/"declined" -> Rejected, "offered" -> Offer |
| `TestClassifyEmail` | 4 | Full classification pipeline for each status type |
| `TestEdgeCases` | 3 | Applied with incidental "interview" mention becomes Interviewing, empty email defaults to Applied, ambiguous email defaults to Applied |

## Test Coverage

The test suite currently covers the `job_tracker` module. The `test_core/` directory exists but does not yet contain test files — core module tests (auth, gmail_client, config, logger, deleter) are a future addition.

## Adding Tests

Tests follow standard pytest conventions:
- Test files are prefixed with `test_`.
- Test classes are prefixed with `Test`.
- Test methods are prefixed with `test_`.
- Real email examples from the PRD are preferred over synthetic data where possible.

When adding new patterns to `job_patterns.py`, add corresponding test cases in the relevant test file to prevent regressions.
