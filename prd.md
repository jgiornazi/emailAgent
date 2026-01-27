# Product Requirements Document
# Job Email Tracker - Part 1

**Version:** 1.0  
**Date:** January 26, 2026  
**Product:** EmailAgent - Job Application Tracker (Feature 2)  
**Status:** Draft - Ready for Implementation  
**Tech Stack:** Python 3.11+, Gmail API, Ollama (optional), openpyxl  
**Coverage:** Sections 1-3

---

## Table of Contents - Part 1

1. Executive Summary
2. Product Scope
3. System Architecture

---

## 1. Executive Summary

### 1.1 Problem Statement

Managing job applications across multiple companies is time-consuming and error-prone. Job seekers receive confirmation emails, interview requests, rejections, and offers scattered across thousands of emails. Without a structured system, it's easy to miss opportunities, lose track of application status, and waste time manually sorting through emails.

**User Context:** The user has **100,000+ emails** in their Gmail inbox and needs an efficient, **free** solution to:
- Track job applications across multiple companies
- Know current status of each application (Applied, Interviewing, Rejected, Offer)
- Delete useless confirmation/rejection emails to clean up inbox
- Never miss interview requests or offers

### 1.2 Solution

An automated job application tracker that:

- **Scans Gmail inbox** for job-related emails using Gmail API search queries
- **Extracts information:** company name, position (optional), and application status
- **Uses HYBRID approach:** Pattern matching (fast, free, 70-80% accurate) + Optional Ollama AI (accurate, free, 90%+ accurate)
- **Stores data in Excel** (`job_applications.xlsx`) with automatic status updates
- **Implements status hierarchy:** Applied → Interviewing/Rejected → Offer (status can move UP or SIDEWAYS, never DOWN)
- **Deletes strategically:** "Applied" confirmation and "Rejected" emails ONLY (after extracting data)
- **Keeps important emails:** "Interviewing" and "Offer" emails are NEVER auto-deleted
- **Batch processing:** Process all emails, show summary, single Y/n confirmation before deletion
- **Safety mechanisms:** Keywords prevent deletion, conflicts flagged, trash (not permanent delete), 30-day recovery

### 1.3 Target User

Job seekers managing high-volume inboxes (10,000-100,000+ emails) who need automated tracking of job applications without:
- Manual email sorting
- Expensive paid services
- Complex setup

**Target User Profile:**
- Actively applying to jobs (10-100+ companies)
- Receives 50-200+ job-related emails per month
- Uses Gmail as primary email
- Wants simple Excel output (not a complex database)
- Technically comfortable with command-line tools
- Budget-conscious (needs free solution)

### 1.4 Cost

**$0 - Completely Free**

| Component | Cost | Notes |
|-----------|------|-------|
| **Pattern matching** | Free | Primary method, 70-80% accuracy, instant |
| **Gmail API** | Free | Free tier: 10,000 requests/day (sufficient) |
| **Ollama local LLM** | Free | Optional, runs on user's machine, ~8GB RAM |
| **openpyxl** | Free | Open-source Python library |
| **Total** | **$0** | No paid APIs, no subscriptions |

**Why Free Matters:**
- User explicitly wants to avoid paid APIs (Claude, OpenAI cost $100s for 100K emails)
- Pattern matching handles 70-80% of emails instantly
- Ollama is optional and runs locally (no API costs)
- Gmail API free tier is more than sufficient

### 1.5 Key Design Decisions

These decisions were made through detailed discussion with the user:

#### Decision 1: Extraction Method - Hybrid with Flag (Option C)

**Chosen Approach:**
- Pattern matching runs FIRST for ALL emails (fast, free)
- `use_ai` configuration flag enables Ollama for ambiguous cases
- Default: `use_ai = false` (pattern-only mode)

**Rationale:**
- 70-80% of emails can be classified instantly with patterns
- User doesn't want to wait 8+ hours for AI to process 100K emails
- AI available as opt-in for users who want higher accuracy
- Graceful degradation: AI fails → continue with patterns

**User Quote:** "I want it fast by default, but I should be able to enable AI if I want better accuracy."

#### Decision 2: Deletion Strategy - Batch with Summary (Option B Modified)

**Chosen Approach:**
- Process ALL emails first
- Show comprehensive summary report
- Single Y/n confirmation for entire batch
- Delete Applied + Rejected ONLY
- Safety keywords prevent deletion even if classified as Applied/Rejected
- Can delete same-day (no minimum age requirement)

**Rationale:**
- User doesn't want to review 1000+ emails individually
- Summary gives overview of what will happen
- Single confirmation is efficient for bulk operations
- Safety keywords catch edge cases (e.g., "applied" email that mentions "interview")

**Alternative Considered (Rejected):** Per-email confirmation - too tedious for 1000+ emails

#### Decision 3: Excel Format - Track Multiple Emails Per Company (Option B)

**Chosen Approach:**
- One row per company (no duplicates)
- Update existing row when new email from same company arrives
- Track all email IDs in comma-separated list
- "Last Updated" date reflects most recent email

**Rationale:**
- User wants overview of companies, not individual emails
- Excel stays manageable (156 companies vs 1000+ emails)
- Can still trace back to original emails via IDs
- Position field shows most recent position applied for

**Alternative Considered (Rejected):** One row per email - Excel becomes unwieldy with 1000+ rows

#### Decision 4: Status Updates - Update Existing Row (Option B)

**Chosen Approach:**
- Status can move UP or SIDEWAYS, never DOWN
- Applied (Level 0) → Interviewing/Rejected (Level 1) → Offer (Level 2)
- Conflicts flagged with ⚠️ symbol and note
- Conflicting emails never auto-deleted

**Rationale:**
- Once you get an offer, receiving rejection is likely an error
- User should manually review conflicts
- Better to flag than silently downgrade

**Example Conflict:**
```
Current: Offer
New Email: Rejection
Action: Keep status as "Offer", add note "⚠️ Conflict: received Rejected after Offer on 2026-01-25"
```

#### Decision 5: AI Integration - Optional via Flag

**Chosen Approach:**
- Ollama local LLM (llama3.2:3b model)
- Enabled via `use_ai: true` in config.yaml
- Graceful degradation if Ollama unavailable
- No dependency on paid APIs

**Rationale:**
- Keeps system free (no API costs)
- User has control over speed vs accuracy tradeoff
- Works offline (privacy benefit)
- ~8GB RAM requirement is reasonable for modern computers

**Processing Time Comparison:**
- Pattern-only: 1000 emails in 5 seconds
- With AI (20% need it): 1000 emails in ~8-10 minutes

---

## 2. Product Scope

### 2.1 In Scope (MVP)

✅ **Email discovery** using Gmail API search queries  
✅ **Information extraction** (company, position, status) via pattern matching  
✅ **Optional AI extraction** via Ollama for ambiguous cases (flag-controlled)  
✅ **Excel storage** with status hierarchy and conflict detection  
✅ **Selective email deletion** (Applied and Rejected only)  
✅ **Batch processing** with summary confirmation  
✅ **Safety rules** and conflict handling  
✅ **Keyword patterns** derived from real user email examples (Perplexity, Plaid, Gem, etc.)  
✅ **Monorepo structure** for future extensibility (Feature 1)  
✅ **CLI interface** with commands for scan, list, export, stats  
✅ **Configuration system** (YAML file + environment variables)  
✅ **Logging and audit trail** (deletion logs, extraction logs)  
✅ **Backup system** (auto-backup before each scan, 7-day retention)  
✅ **Export functionality** (CSV, JSON formats)  

### 2.2 Out of Scope (MVP)

❌ **General email cleanup** (promotional, newsletters, spam) - **Deferred to Feature 1**  
❌ **Automatic scheduling/cron jobs** (manual execution only)  
❌ **Email response templates** or auto-replies  
❌ **Multi-account support** (single Gmail account only)  
❌ **Web dashboard or GUI** (CLI only for MVP)  
❌ **Calendar integration** for interview scheduling  
❌ **Mobile app**  
❌ **Browser extension**  
❌ **Real-time monitoring** (batch mode only)  
❌ **Email sending** (read-only except for deletion)  
❌ **Attachment handling** (text-based emails only)  

### 2.3 Future Enhancements

**After Feature 2 (Job Tracker) is tested and working:**

#### Priority 1: Feature 1 - General Email Cleanup Agent

**Scope:**
- Will reuse core components from Feature 2:
  - Gmail client
  - Auth flow
  - Deletion logic
  - Safety mechanisms
  - Configuration system
- Pattern-based deletion for promotional, newsletters, spam
- Deletion count logging by category (no per-email tracking needed)
- **Separate PRD to be created** after Feature 2 validation

**Why Separate:**
- Feature 2 is priority (job tracking is critical need)
- Want to validate core architecture before extending
- Different patterns/rules needed for general cleanup
- User wants to test Feature 2 thoroughly first

#### Priority 2: Other Enhancements

**User Experience:**
- Web dashboard for visual job application tracking
- GUI for non-technical users
- Mobile app (iOS/Android)
- Browser extension for quick access

**Email Management:**
- Email response templates (thank you, follow-up)
- Auto-reply for certain scenarios
- Email sending capabilities

**Integrations:**
- Calendar integration (schedule interviews automatically)
- Job board integration (LinkedIn, Indeed)
- ATS system integration (if user is hiring manager)
- Slack/Discord notifications

**Advanced Features:**
- Multi-account Gmail support
- Real-time monitoring (webhook-based)
- AI-powered insights ("You haven't heard back from Company X in 2 weeks")
- Automated follow-up email generation
- Statistics dashboard (application funnel, response rates)
- Company research (auto-fetch company info from web)

### 2.4 Why Monorepo?

**Decision:** Build Feature 2 in a monorepo structure even though Feature 1 is future work.

**Structure:**
```
emailagent/
├── core/           # Shared (used by both features)
├── job_tracker/    # Feature 2 (this PRD)
├── bulk_cleaner/   # Feature 1 (future, stub for now)
└── cli.py          # Unified CLI
```

**Benefits:**

1. **Code Reuse**
   - Gmail client written once, used by both features
   - Auth flow shared
   - Deletion logic shared (with different rules per feature)
   - Safety mechanisms shared
   - Configuration system shared

2. **Consistency**
   - Same patterns across features
   - Same error handling
   - Same logging approach
   - Same CLI style

3. **Single Source of Truth**
   - One config.yaml file
   - One auth flow
   - One set of credentials
   - One logging directory

4. **Progressive Enhancement**
   - Build core solid for Feature 2
   - Extend easily for Feature 1
   - No refactoring needed when adding Feature 1

5. **Maintenance**
   - Fix a bug in core → both features benefit
   - Update Gmail API → change in one place
   - Improve safety rules → applies everywhere

**Cost of Monorepo:**
- Slightly more upfront structure (but pays off quickly)
- Need to think about abstraction (but makes code better)

**Alternative (Rejected):**
- Build Feature 2 standalone, refactor later for Feature 1
- Would require significant refactoring
- Risk of inconsistency between features

---

## 3. System Architecture

### 3.1 Repository Structure (Monorepo)

```
emailagent/
├── core/                       # Shared components (reusable for Feature 1)
│   ├── __init__.py
│   ├── gmail_client.py        # Gmail API wrapper
│   ├── auth.py                # OAuth 2.0 authentication
│   ├── deleter.py             # Email deletion operations
│   ├── logger.py              # Logging and audit trail
│   └── config.py              # Configuration management
│
├── job_tracker/                # Feature 2 (this PRD)
│   ├── __init__.py
│   ├── extractor.py           # Company/position/status extraction
│   ├── excel_storage.py       # Excel read/write operations
│   ├── job_patterns.py        # Job email keyword patterns
│   ├── classifier.py          # Status classification logic
│   └── ollama_client.py       # Optional: Ollama AI wrapper
│
├── bulk_cleaner/               # Feature 1 (future)
│   ├── __init__.py            # Placeholder for now
│   └── README.md              # "Coming soon" note
│
├── cli.py                      # Unified CLI entry point
├── config.yaml                 # Configuration file (default)
├── requirements.txt            # Python dependencies
├── README.md                   # Main documentation
├── SETUP.md                    # Gmail API setup guide
├── .gitignore
└── tests/
    ├── __init__.py
    ├── test_core/             # Tests for core modules
    │   ├── test_gmail_client.py
    │   ├── test_auth.py
    │   └── test_deleter.py
    ├── test_job_tracker/      # Tests for job tracker
    │   ├── test_extractor.py
    │   ├── test_classifier.py
    │   └── test_excel_storage.py
    └── fixtures/              # Test data (mock emails)
        ├── applied_emails.json
        ├── rejected_emails.json
        └── interviewing_emails.json
```

**Key Files Explained:**

**Core Module:**
- `gmail_client.py`: Wrapper around Gmail API (search, fetch, trash emails)
- `auth.py`: OAuth 2.0 flow, token management, credential refresh
- `deleter.py`: Safe deletion logic, batch operations, undo functionality
- `logger.py`: Structured logging (app logs, deletion logs, audit trail)
- `config.py`: Load config from YAML/env vars, validation

**Job Tracker Module:**
- `extractor.py`: Pattern matching + optional AI extraction
- `excel_storage.py`: Create/update/export Excel file
- `job_patterns.py`: Regex patterns for company, position, status
- `classifier.py`: Status hierarchy, conflict detection
- `ollama_client.py`: Wrapper around Ollama API (if use_ai enabled)

**CLI:**
- `cli.py`: Command-line interface (auth, job scan, job list, job export, etc.)

**Config:**
- `config.yaml`: User-editable configuration (Gmail paths, AI settings, deletion rules)

### 3.2 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  Gmail Inbox (100,000 emails)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         Gmail API Search (job-specific search queries)          │
│                                                                  │
│   Query 1: subject:(application OR applied OR "thank you...")   │
│   Query 2: subject:(interview OR "phone screen"...)             │
│   Query 3: subject:(offer OR "job offer"...)                    │
│   Query 4: subject:(rejection OR "not moving forward"...)       │
│   Query 5: "your application" OR "application status"           │
│                                                                  │
│   → Returns ~1,000-2,000 job-related emails                     │
│   → De-duplicates by message ID                                 │
│   → Sorts chronologically (oldest first)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Extraction Module (Hybrid Approach)                │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │ Step 1: Pattern Matching (ALWAYS runs first)    │           │
│  │                                                   │           │
│  │  • Extract company from email domain             │           │
│  │    jobs@techcorp.com → "TechCorp"               │           │
│  │  • Extract position from subject/body            │           │
│  │    "Application for Backend Engineer"            │           │
│  │  • Classify status with keyword patterns         │           │
│  │    "thank you for applying" → Applied            │           │
│  │  • Assign confidence score (high/medium/low)     │           │
│  │                                                   │           │
│  │  Speed: ~1000 emails in 5 seconds                │           │
│  │  Accuracy: 70-80%                                 │           │
│  │  Cost: Free                                       │           │
│  └──────────────────────────────────────────────────┘           │
│                         │                                        │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────┐           │
│  │ Step 2: AI Fallback (ONLY if use_ai=true)       │           │
│  │                                                   │           │
│  │  Triggered when:                                  │           │
│  │  • Pattern confidence < 0.7                       │           │
│  │  • Company == "Unknown"                           │           │
│  │  • Status unclear                                 │           │
│  │                                                   │           │
│  │  Process:                                         │           │
│  │  • Invoke Ollama llama3.2:3b                     │           │
│  │  • Send prompt with email data                    │           │
│  │  • Parse JSON response                            │           │
│  │  • Handle timeout (30s limit)                     │           │
│  │                                                   │           │
│  │  Speed: ~2-3 seconds per email                   │           │
│  │  Accuracy: 90-95%                                 │           │
│  │  Cost: Free (local)                               │           │
│  └──────────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         Classification Module (Status + Confidence)             │
│                                                                  │
│  • Status: Applied, Interviewing, Rejected, Offer               │
│  • Confidence: High, Medium, Low                                │
│  • Mark low confidence as "Needs Review" in Excel               │
│  • Track extraction method (pattern vs ai)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           Excel Storage (job_applications.xlsx)                 │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │ Check if company exists in Excel:                │           │
│  │                                                   │           │
│  │ IF company NOT found:                             │           │
│  │   → Create new row with all details               │           │
│  │   → Company, Position, Status, Confidence, Dates  │           │
│  │                                                   │           │
│  │ IF company found:                                 │           │
│  │   → Check status hierarchy                        │           │
│  │   → IF new_status_level >= current_status_level: │           │
│  │       → Update status, date, append email ID      │           │
│  │   → ELSE (status would downgrade):                │           │
│  │       → FLAG CONFLICT with ⚠️ symbol              │           │
│  │       → Keep current (higher) status              │           │
│  │       → Add note with conflict details            │           │
│  │       → Append email ID (track conflict)          │           │
│  │                                                   │           │
│  │ Save after every 100 emails processed             │           │
│  └──────────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Deletion Module (Selective)                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │ Mark for deletion IF ALL of:                     │           │
│  │  1. Status = "Applied" OR "Rejected"             │           │
│  │  2. Email does NOT contain safety keywords       │           │
│  │     (interview, offer, assessment, etc.)         │           │
│  │  3. Email is NOT a conflict case (no ⚠️)         │           │
│  │                                                   │           │
│  │ Safety Keywords (Prevent Deletion):               │           │
│  │  • interview, phone screen, next steps           │           │
│  │  • offer, job offer, compensation                │           │
│  │  • assessment, take-home, challenge              │           │
│  │  • schedule, meeting, call with                  │           │
│  │  • urgent, deadline, respond by                  │           │
│  │                                                   │           │
│  │ ALWAYS KEEP:                                      │           │
│  │  • Interviewing emails                            │           │
│  │  • Offer emails                                   │           │
│  │  • Emails with safety keywords                    │           │
│  │  • Conflict emails                                │           │
│  └──────────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           Summary Report + User Confirmation                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │ Processing complete!                              │           │
│  │                                                   │           │
│  │ Summary:                                          │           │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│           │
│  │ • Total job emails found: 1,247                   │           │
│  │ • Companies identified: 156 unique                │           │
│  │                                                   │           │
│  │ Status Breakdown:                                 │           │
│  │   • Applied: 892 emails (will be deleted)        │           │
│  │   • Interviewing: 45 emails (KEPT)               │           │
│  │   • Rejected: 287 emails (will be deleted)       │           │
│  │   • Offer: 23 emails (KEPT)                      │           │
│  │                                                   │           │
│  │ Safety Checks:                                    │           │
│  │   ✓ 15 emails protected by safety keywords       │           │
│  │   ✓ 3 conflicts flagged                          │           │
│  │   ⚠ 42 emails need manual review                 │           │
│  │                                                   │           │
│  │ Ready to delete 1,179 emails? [Y/n]:             │           │
│  └──────────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            Gmail API: Move to Trash (Not Permanent)             │
│                                                                  │
│  • Move emails to Gmail trash folder (not permanent delete)     │
│  • 30-day recovery window (Google automatic deletion)           │
│  • Process in batches of 50 (rate limit compliance)             │
│  • Log all deletions with timestamp to audit file               │
│  • Show progress: "Deleting 523/1179 emails..."                 │
│  • Display recovery instructions after completion               │
│  • Undo command available: emailagent job undo-last             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Technology Stack

| Component | Technology | Version | Purpose | Cost |
|-----------|------------|---------|---------|------|
| **Language** | Python | 3.11+ | Main programming language | Free |
| **Email API** | Gmail API v1 | Latest | Email access (read, search, trash) | Free |
| **Authentication** | google-auth, google-auth-oauthlib | 2.16+ | OAuth 2.0 flow | Free |
| **AI (Optional)** | Ollama | Latest | Local LLM for extraction | Free |
| **AI Model** | llama3.2:3b | - | Small, fast, accurate | Free |
| **Excel** | openpyxl | 3.1+ | Create/edit .xlsx files | Free |
| **CLI Framework** | Click or Typer | 8.1+ | Command-line interface | Free |
| **CLI UI** | Rich | 13.0+ | Progress bars, tables, colors | Free |
| **Config** | PyYAML | 6.0+ | YAML parsing | Free |
| **HTTP** | requests | 2.31+ | Ollama API calls | Free |
| **Date/Time** | python-dateutil | 2.8+ | Date parsing | Free |
| **Logging** | Python logging | Built-in | Structured logging | Free |
| **Testing** | pytest | 7.4+ | Unit/integration tests | Free |
| **Type Checking** | mypy | 1.7+ | Static type checking | Free |
| **Formatting** | black | 23.0+ | Code formatting | Free |

**System Requirements:**

**Minimum (Pattern-only mode):**
- OS: Linux, macOS, Windows 10+
- Python: 3.11+
- RAM: 2GB
- Disk: 500MB free
- Internet: Required for Gmail API

**Recommended (With AI):**
- OS: Linux, macOS, Windows 10+
- Python: 3.11+
- RAM: 8GB (for Ollama)
- Disk: 10GB (for Ollama model)
- Internet: Required for Gmail API + Ollama model download

### 3.4 Key Architectural Decisions

#### Decision 1: Monorepo vs. Separate Repos
- **Chosen:** Monorepo
- **Rationale:** Feature 1 (future) will reuse 80% of core code. Single auth, single config, consistent patterns.
- **Tradeoff:** Slightly more upfront structure, but easier to maintain long-term.

#### Decision 2: Pattern Matching First, AI Optional
- **Chosen:** Hybrid with flag (`use_ai` configuration)
- **Rationale:** 70-80% of emails can be classified instantly for free. AI for remaining 20-30% if user enables it.
- **Tradeoff:** Some inaccuracy in pattern-only mode, but vastly faster and free.

#### Decision 3: Excel vs. Database
- **Chosen:** Excel (openpyxl)
- **Rationale:** 
  - User wants simple, portable file
  - Easy to open in Excel, Google Sheets, LibreOffice
  - No database setup required
  - Export to CSV/JSON still available
- **Tradeoff:** Less scalable for 10,000+ companies (but user has ~150 companies).

#### Decision 4: Trash vs. Permanent Delete
- **Chosen:** Trash (Gmail API `trash` operation)
- **Rationale:** 
  - 30-day recovery window
  - Accidental deletion protection
  - User can manually empty trash later
  - Undo functionality possible
- **Tradeoff:** Emails still count toward Gmail storage quota until permanently deleted after 30 days.

#### Decision 5: Batch Confirmation vs. Per-Email Confirmation
- **Chosen:** Batch with summary
- **Rationale:** 
  - User doesn't want to review 1000+ emails individually
  - Summary gives overview of what will happen
  - Single Y/n confirmation is efficient
  - Clear counts prevent accidental deletion
- **Tradeoff:** Less granular control, but vastly more efficient.

#### Decision 6: Status Can't Downgrade
- **Chosen:** Strict hierarchy enforcement (up/sideways only, never down)
- **Rationale:** 
  - Once you get an offer, receiving rejection is likely error/confusion
  - Better to flag for manual review than silently downgrade
  - Prevents data loss (offer → rejection would lose important info)
- **Tradeoff:** Requires manual conflict resolution, but safer.

#### Decision 7: Python vs. Go
- **Chosen:** Python
- **Rationale:**
  - Better Gmail API support (official Google library)
  - Rich ecosystem (openpyxl, Click, Rich)
  - Easier for users to modify/extend
  - Ollama has Python client
- **Tradeoff:** Slightly slower than Go, but negligible for this use case.

#### Decision 8: CLI vs. GUI
- **Chosen:** CLI for MVP
- **Rationale:**
  - Faster to build and test
  - User is technically comfortable
  - Easier to run on any system
  - Can add GUI later as enhancement
- **Tradeoff:** Less accessible to non-technical users, but acceptable for MVP.

---

**End of Part 1**

**Next:** Part 2 will cover Sections 4-6 (Functional Requirements, Extraction Patterns, CLI Specification)

# Product Requirements Document
# Job Email Tracker - Part 2

**Version:** 1.0  
**Date:** January 26, 2026  
**Product:** EmailAgent - Job Application Tracker (Feature 2)  
**Status:** Draft - Ready for Implementation  
**Coverage:** Sections 4-6 (Functional Requirements - Parts 1-3)

---

## Table of Contents - Part 2

4. Functional Requirements (Part 1)
   - 4.1 Email Discovery
   - 4.2 Information Extraction
5. Functional Requirements (Part 2)
   - 4.3 Status Hierarchy & Updates
   - 4.4 Excel Storage
6. Functional Requirements (Part 3)
   - 4.5 Deletion Logic

---

## 4. Functional Requirements

### 4.1 Email Discovery

#### 4.1.1 Gmail Search Queries

The system shall fetch job-related emails using the following Gmail API search queries:

```
Query 1: subject:(application OR applied OR "thank you for applying")
Query 2: subject:(interview OR "phone screen" OR "next steps")
Query 3: subject:(offer OR "job offer" OR "offer letter")
Query 4: subject:(rejection OR "not moving forward")
Query 5: "your application" OR "application status" OR "application for"
```

**Implementation Strategy:**
- Execute each query separately using Gmail API `users().messages().list()`
- Combine all results into a single list
- De-duplicate by Gmail message ID (emails matching multiple queries counted once)
- Sort by internal date (oldest first) for chronological processing

**Why These Queries?**
- Derived from analysis of user's real email examples
- Cover all four statuses: Applied, Interviewing, Rejected, Offer
- Balance between recall (finding all job emails) and precision (avoiding non-job emails)
- Subject-based queries are fastest (indexed by Gmail)

#### 4.1.2 Email Fetch Limits

**Per-Scan Limits:**
- **Maximum emails to process:** 10,000 per scan
- **Batch size for API calls:** 100 emails per `list()` request
- **Rate limiting:** Respect Gmail API quotas (250 quota units per user per second)
- **Timeout:** 60 minutes maximum per scan (safety limit)

**Gmail API Quotas:**
- 10,000 requests per day (free tier)
- 250 quota units per user per second
- Each `list()` call = 1 quota unit
- Each `get()` call = 5 quota units
- Each `trash()` call = 1 quota unit

**Expected Usage:**
- Scanning 1,000 emails: ~1,000 quota units (well within limits)
- First-time scan of 10,000 emails: ~10,000 quota units (max usage)
- Typical usage after initial scan: 50-200 emails per week

#### 4.1.3 Gmail API Request Implementation

```python
def fetch_job_emails(service, max_emails=10000):
    """
    Fetch job-related emails from Gmail
    
    Args:
        service: Gmail API service object
        max_emails: Maximum number of emails to fetch
    
    Returns:
        List of email message IDs
    """
    all_email_ids = set()  # Use set for automatic deduplication
    
    queries = [
        'subject:(application OR applied OR "thank you for applying")',
        'subject:(interview OR "phone screen" OR "next steps")',
        'subject:(offer OR "job offer" OR "offer letter")',
        'subject:(rejection OR "not moving forward")',
        '"your application" OR "application status"'
    ]
    
    for query in queries:
        print(f"Searching: {query[:50]}...")
        page_token = None
        
        while len(all_email_ids) < max_emails:
            try:
                # Fetch batch
                results = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=min(100, max_emails - len(all_email_ids)),
                    pageToken=page_token
                ).execute()
                
                # Add message IDs to set (automatic deduplication)
                if 'messages' in results:
                    for msg in results['messages']:
                        all_email_ids.add(msg['id'])
                
                # Check for more pages
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
            except HttpError as error:
                if error.resp.status == 429:  # Rate limit
                    print("Rate limit hit, waiting 10 seconds...")
                    time.sleep(10)
                    continue
                else:
                    raise
    
    print(f"Found {len(all_email_ids)} unique job emails")
    return list(all_email_ids)


def fetch_email_details(service, email_ids, batch_size=100):
    """
    Fetch full details for list of email IDs
    
    Args:
        service: Gmail API service object
        email_ids: List of message IDs
        batch_size: Number of emails to fetch per batch
    
    Returns:
        List of email objects with subject, from, body, date
    """
    emails = []
    total = len(email_ids)
    
    for i in range(0, total, batch_size):
        batch = email_ids[i:i+batch_size]
        
        for email_id in batch:
            try:
                msg = service.users().messages().get(
                    userId='me',
                    id=email_id,
                    format='full'
                ).execute()
                
                # Parse email
                email_obj = parse_gmail_message(msg)
                emails.append(email_obj)
                
            except HttpError as error:
                logger.error(f"Failed to fetch {email_id}: {error}")
                continue
        
        # Show progress
        progress = min(i + len(batch), total)
        print(f"Fetched: {progress}/{total} emails", end='\r')
    
    print(f"\nFetched {len(emails)} emails successfully")
    return emails


def parse_gmail_message(msg):
    """
    Parse Gmail API message object
    
    Returns:
        dict with id, subject, from, body, date, snippet
    """
    headers = msg['payload']['headers']
    
    # Extract headers
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
    date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
    
    # Parse date
    date = parse_date(date_str) if date_str else None
    
    # Extract body
    body = extract_body(msg['payload'])
    
    return {
        'id': msg['id'],
        'subject': subject,
        'from': from_email,
        'body': body,
        'snippet': msg.get('snippet', ''),
        'date': date
    }


def extract_body(payload):
    """Extract email body from Gmail payload"""
    if 'body' in payload and 'data' in payload['body']:
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
    
    return ''
```

#### 4.1.4 Acceptance Criteria

- [ ] Fetch up to 10,000 emails per scan
- [ ] De-duplicate emails by Gmail message ID
- [ ] Process emails in chronological order (oldest first)
- [ ] Handle API rate limits gracefully (exponential backoff on 429 errors)
- [ ] Log total emails found before processing begins
- [ ] Handle network errors with retry (up to 3 attempts)
- [ ] Show progress: "Fetching emails: 523/1000..."
- [ ] Complete scan within 5 minutes for 1000 emails

---

### 4.2 Information Extraction

#### 4.2.1 Extraction Methods Overview

**Two-Stage Extraction:**

**Stage 1: Pattern Matching (ALWAYS runs, runs FIRST)**
- Free, fast (~1000 emails in 5 seconds)
- Accuracy: 70-80%
- Uses regex and keyword matching
- Assigns confidence score

**Stage 2: AI Fallback (ONLY if use_ai=true AND low confidence)**
- Uses Ollama local LLM
- Accuracy: 90-95%
- Slower (~2-3 seconds per email)
- Triggered by: confidence < 0.7, company == "Unknown", status == "Needs_Review"

#### 4.2.2 Pattern Matching - Company Name Extraction

**Priority Order (try in sequence until success):**

**1. Email Domain (Highest Priority)**

```python
def extract_company_from_domain(email_address):
    """
    Extract company from email domain
    Example: jobs@techcorp.com → "TechCorp"
    """
    # Generic providers to skip
    GENERIC_PROVIDERS = [
        'gmail', 'yahoo', 'outlook', 'hotmail', 'icloud',
        'greenhouse', 'lever', 'workday', 'myworkdayjobs',
        'icims', 'taleo', 'jobvite', 'smartrecruiters',
        'applicantstack', 'bamboohr', 'workable'
    ]
    
    # Extract domain
    match = re.search(r'@([^.]+)', email_address)
    if not match:
        return None, None
    
    domain = match.group(1).lower()
    
    # Skip generic providers
    if domain in GENERIC_PROVIDERS:
        return None, None
    
    # Clean and format company name
    company = domain.replace('-', ' ').replace('_', ' ')
    company = re.sub(r'\b(corp|inc|llc|ltd|co)\b', '', company, flags=re.IGNORECASE)
    company = company.strip().title()
    
    return company if company else None, 'domain'

# Examples:
# jobs@techcorp.com → "Techcorp", 'domain'
# recruiting@perplexity.ai → "Perplexity", 'domain'
# noreply@greenhouse.io → None, None (generic provider)
```

**2. Subject Line Patterns**

```python
SUBJECT_COMPANY_PATTERNS = [
    # "Application to [Company]"
    r'application to ([^-|\n]+?)(?:\s*[-|]|$)',
    
    # "Your application at [Company]"
    r'your application at ([^-|\n]+?)(?:\s*[-|]|$)',
    
    # "[Company] - Application Received"
    r'^([^-|]+?)\s*[-|]\s*application',
    
    # "Thank you for applying to [Company]"
    r'applying to ([^-|!\n]+?)(?:\s*[-|!]|$)',
    
    # "[Company]: Job Title"
    r'^([^:]+?):\s*\w',
    
    # "Application Update from [Company]"
    r'(?:update|thanks) from ([^-|\n]+?)(?:\s*[-|]|$)',
]

def extract_company_from_subject(subject):
    """Extract company name from email subject"""
    for pattern in SUBJECT_COMPANY_PATTERNS:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            # Validate length (reasonable company name)
            if 2 <= len(company) <= 50:
                return company.title(), 'subject'
    return None, None
```

**3. Email Body Patterns**

```python
BODY_COMPANY_PATTERNS = [
    # "Thank you for your interest in [Company]"
    r'interest in ([^.\n]+?)(?:\.|$)',
    
    # "Welcome to [Company]'s application"
    r'welcome to ([^\']+?)\'s',
    
    # "You applied to [Company]"
    r'applied to ([^.\n]+?)(?:\s+for|\.|$)',
    
    # "[Company] Recruiting Team"
    r'([^.\n]+?) recruiting team',
    
    # "Your application for [position] at [Company]"
    r'at ([^.\n]+?)(?:\.|$)',
]

def extract_company_from_body(body):
    """Extract company from first 500 characters of body"""
    snippet = body[:500]
    for pattern in BODY_COMPANY_PATTERNS:
        match = re.search(pattern, snippet, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if 2 <= len(company) <= 50:
                return company.title(), 'body'
    return None, None
```

**Complete Company Extraction:**

```python
def extract_company(email):
    """
    Extract company name from email (tries all methods)
    
    Returns: (company_name, source)
    """
    # Try domain first (most reliable)
    company, source = extract_company_from_domain(email['from'])
    if company:
        return company, source
    
    # Try subject
    company, source = extract_company_from_subject(email['subject'])
    if company:
        return company, source
    
    # Try body
    company, source = extract_company_from_body(email.get('body', ''))
    if company:
        return company, source
    
    # Failed to extract
    return 'Unknown', None
```

#### 4.2.3 Pattern Matching - Position Extraction

```python
POSITION_PATTERNS = [
    # From subject: "Application for [Position]"
    r'application for\s+([^-|\n]+?)(?:\s*[-|]|$)',
    
    # From subject: "Applied for [Position] at"
    r'applied for\s+([^-|\n]+?)\s+at',
    
    # From subject: "[Position] - Application"
    r'^([^-]+?)\s*-\s*application',
    
    # From body: "for the [Position] position"
    r'for the ([^.\n]+?) (?:position|role)',
    
    # Position keywords with context
    r'((?:senior|junior|staff|principal|lead)?\s*'
    r'(?:software|backend|frontend|full.?stack|devops|data)?\s*'
    r'(?:engineer|developer|scientist|analyst|manager|designer|architect))',
]

POSITION_KEYWORDS = [
    'engineer', 'developer', 'manager', 'designer', 'analyst', 'scientist',
    'backend', 'frontend', 'full stack', 'fullstack', 'senior', 'junior',
    'lead', 'staff', 'principal', 'architect', 'devops', 'data', 'product',
    'software', 'qa', 'test', 'security', 'cloud', 'platform', 'infrastructure'
]

def extract_position(subject, body):
    """
    Extract job position/title
    
    Returns: position string or "Not specified"
    """
    # Try subject first (most reliable)
    for pattern in POSITION_PATTERNS[:3]:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            position = match.group(1).strip()
            # Validate: should contain a position keyword
            if any(keyword in position.lower() for keyword in POSITION_KEYWORDS):
                # Validate length
                if 5 <= len(position) <= 60 and '.' not in position:
                    return position.title()
    
    # Try body (first 300 chars)
    for pattern in POSITION_PATTERNS[3:]:
        match = re.search(pattern, body[:300], re.IGNORECASE)
        if match:
            position = match.group(1).strip()
            if any(keyword in position.lower() for keyword in POSITION_KEYWORDS):
                if 5 <= len(position) <= 60:
                    return position.title()
    
    return "Not specified"
```

#### 4.2.4 Pattern Matching - Status Classification

**Status Keywords (derived from real user emails):**

```python
STATUS_PATTERNS = {
    'Rejected': [
        r'not moving forward',
        r'won\'?t be advancing',
        r'will not be moving forward',
        r'not move forward',
        r'made the decision to not move forward',
        r'we are not moving forward',
        r'after (careful )?consideration.*not',
        r'unfortunately.*not',
        r'unfortunately, we will not',
        r'wish you (well|success) (in|on) your (search|job search)',
        r'best of luck in your (search|job search)',
        r'we appreciate your (time|interest)',
        r'(keep|stay) in touch',
        r'reach out.*in the future',
        r'future opportunities',
        r'watch our career page',
        r'decided to pursue (other|different) candidates',
        r'position has been filled',
        r'other candidates',
        r'moved forward with other',
    ],
    
    'Offer': [
        r'pleased to offer',
        r'(we are )?excited to offer',
        r'(we would )?like to offer',
        r'job offer',
        r'offer letter',
        r'extend(ing)? (an|a) offer',
        r'congratulations.*position',
        r'welcome to (the )?team',
        r'accept (your|this) offer',
        r'offer of employment',
        r'compensation package',
        r'start date',
    ],
    
    'Interviewing': [
        r'\binterview\b',
        r'phone screen',
        r'video call',
        r'next steps',
        r'schedule (a )?call',
        r'schedule (a )?meeting',
        r'speak with',
        r'meet with (our|the )?team',
        r'meeting with',
        r'(technical|coding) (assessment|challenge)',
        r'take.?home (assignment|project)',
        r'on.?site (interview|visit)',
        r'final round',
        r'hiring manager',
        r'chat with',
        r'connect with',
    ],
    
    'Applied': [
        r'thank you for (your )?(applying|application|interest)',
        r'we.*received your application',
        r'(we )?received your application',
        r'application (has been )?(received|was sent)',
        r'confirm(ing)? (receipt of )?(your )?application',
        r'we will (review|be in touch)',
        r'our team will review',
        r'we are committed to reviewing',
        r'excited to review your application',
        r'application is (being|under) review',
        r'delighted that you would consider',
        r'thanks for applying',
    ],
}

def classify_status(subject, body):
    """
    Classify email status using pattern matching
    
    Returns: (status, match_count)
    """
    # Combine text for analysis
    text = f"{subject} {body}".lower()
    
    # Count matches for each status
    status_scores = {status: 0 for status in STATUS_PATTERNS}
    
    # Check in priority order: Rejected, Offer, Interviewing, Applied
    # (Rejection most distinctive, Applied most generic)
    for status in ['Rejected', 'Offer', 'Interviewing', 'Applied']:
        for pattern in STATUS_PATTERNS[status]:
            if re.search(pattern, text, re.IGNORECASE):
                status_scores[status] += 1
    
    # Return status with highest score
    best_status = max(status_scores, key=status_scores.get)
    match_count = status_scores[best_status]
    
    # If no matches, return None
    if match_count == 0:
        return None, 0
    
    return best_status, match_count
```

#### 4.2.5 Confidence Scoring

```python
def calculate_confidence(extraction_result):
    """
    Calculate confidence score for extraction
    
    Args:
        extraction_result: dict with keys:
            - company: str
            - company_source: 'domain' | 'subject' | 'body' | None
            - position: str
            - status: str
            - status_matches: int (number of keyword matches)
    
    Returns:
        'high' | 'medium' | 'low'
    """
    score = 0.0
    
    # Company extraction (40% of score)
    if extraction_result['company'] != 'Unknown':
        score += 0.4
        # Bonus for domain extraction (most reliable)
        if extraction_result.get('company_source') == 'domain':
            score += 0.1
    
    # Position extraction (20% of score)
    if extraction_result['position'] != 'Not specified':
        score += 0.2
    
    # Status classification (40% of score)
    status_matches = extraction_result.get('status_matches', 0)
    if status_matches >= 2:
        score += 0.4  # Multiple keyword matches = high confidence
    elif status_matches == 1:
        score += 0.2  # Single match = moderate confidence
    
    # Determine confidence level
    if score >= 0.7:
        return 'high'
    elif score >= 0.4:
        return 'medium'
    else:
        return 'low'

# Examples:
# Company from domain + position + 2 status keywords = 1.0 → high
# Company from subject + 1 status keyword = 0.6 → medium
# Company unknown + no position = 0.2 → low
```

#### 4.2.6 AI Extraction (Optional, Ollama)

**When to Use AI:**

```python
def should_use_ai(pattern_result, use_ai_enabled):
    """Determine if AI extraction should be attempted"""
    if not use_ai_enabled:
        return False
    
    # Trigger AI for low confidence results
    if pattern_result['confidence'] == 'low':
        return True
    
    # Trigger AI for unknown companies
    if pattern_result['company'] == 'Unknown':
        return True
    
    # Trigger AI for unclear status
    if pattern_result['status'] == 'Applied' and pattern_result['status_matches'] < 2:
        return True
    
    return False
```

**AI Prompt Template:**

```python
def generate_ollama_prompt(email):
    """Generate prompt for Ollama"""
    return f"""Extract job application information from this email.

Email:
Subject: {email['subject']}
From: {email['from']}
Body: {email.get('body', '')[:800]}

Return a JSON object with these fields:
- company: company name (string, or "Unknown" if not found)
- position: job position/title (string, or "Not specified" if not found)
- status: exactly one of "Applied", "Interviewing", "Rejected", or "Offer"

Rules:
- Be concise with company name (e.g., "TechCorp" not "TechCorp Inc.")
- If company is in email domain, use that
- Status should match the email's tone and purpose
- Return ONLY valid JSON, no markdown, no other text

Example valid response:
{{"company": "TechCorp", "position": "Software Engineer", "status": "Applied"}}
"""
```

**AI Response Parsing:**

```python
import json
import re

def parse_ollama_response(response_text):
    """
    Parse AI response, handling markdown fences or plain JSON
    
    Returns: dict with company, position, status, confidence
    """
    # Remove markdown code fences if present
    cleaned = re.sub(r'```json\s*', '', response_text)
    cleaned = re.sub(r'```\s*', '', cleaned)
    cleaned = cleaned.strip()
    
    try:
        data = json.loads(cleaned)
        
        # Validate status
        valid_statuses = ['Applied', 'Interviewing', 'Rejected', 'Offer']
        status = data.get('status', 'Applied')
        if status not in valid_statuses:
            status = 'Applied'  # Default fallback
        
        return {
            'company': data.get('company', 'Unknown'),
            'position': data.get('position', 'Not specified'),
            'status': status,
            'confidence': 'medium',  # AI results get medium confidence
            'extraction_method': 'ai'
        }
        
    except json.JSONDecodeError as e:
        # AI failed to return valid JSON
        logger.warning(f"Failed to parse AI response: {e}")
        return {
            'company': 'Unknown',
            'position': 'Not specified',
            'status': 'Applied',
            'confidence': 'low',
            'extraction_method': 'ai_failed'
        }
```

**Ollama API Call:**

```python
import requests

def extract_with_ollama(email, model='llama3.2:3b', timeout=30):
    """
    Use Ollama to extract information from email
    
    Returns: dict with company, position, status or None if failed
    """
    prompt = generate_ollama_prompt(email)
    
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.1,  # Low temperature for consistency
                    'top_p': 0.9,
                }
            },
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return parse_ollama_response(result['response'])
        else:
            logger.error(f"Ollama API error: {response.status_code}")
            return None
            
    except requests.Timeout:
        logger.warning(f"Ollama timeout after {timeout}s")
        return None
    except requests.ConnectionError:
        logger.error("Cannot connect to Ollama (is it running?)")
        return None
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return None
```

#### 4.2.7 Complete Extraction Flow

```python
def extract_email_info(email, config):
    """
    Complete extraction pipeline
    
    Args:
        email: dict with 'subject', 'from', 'body', 'snippet', 'date', 'id'
        config: configuration dict with 'use_ai' flag
    
    Returns:
        dict with company, position, status, confidence, extraction_method
    """
    # Step 1: Always try pattern matching first
    pattern_result = pattern_match_extraction(email)
    
    # Step 2: Check if we should use AI
    if should_use_ai(pattern_result, config.get('use_ai', False)):
        logger.info(f"Low confidence, trying AI: {email['subject'][:50]}...")
        
        ai_result = extract_with_ollama(email)
        
        # Use AI result if it succeeded and found company
        if ai_result and ai_result['company'] != 'Unknown':
            logger.info(f"AI extraction successful: {ai_result['company']}")
            return ai_result
        else:
            logger.warning("AI extraction failed, using pattern result")
    
    # Step 3: Return pattern matching result (original or AI failed)
    return pattern_result


def pattern_match_extraction(email):
    """Pattern matching extraction (no AI)"""
    # Extract company
    company, company_source = extract_company(email)
    
    # Extract position
    position = extract_position(email['subject'], email.get('body', ''))
    
    # Classify status
    status, match_count = classify_status(
        email['subject'],
        email.get('body', email.get('snippet', ''))
    )
    
    if not status:
        status = 'Applied'  # Default fallback
        match_count = 0
    
    # Build result
    result = {
        'company': company,
        'company_source': company_source,
        'position': position,
        'status': status,
        'status_matches': match_count,
        'extraction_method': 'pattern',
        'email_id': email['id'],
        'email_date': email.get('date')
    }
    
    # Calculate confidence
    result['confidence'] = calculate_confidence(result)
    
    return result
```

#### 4.2.8 Acceptance Criteria

- [ ] Pattern matching attempts extraction for 100% of emails
- [ ] If use_ai=true AND confidence < 0.7, invoke Ollama
- [ ] If use_ai=false AND confidence < 0.7, mark as "Needs_Review" in Excel
- [ ] Pattern-only mode: Process 1000 emails in ≤5 seconds
- [ ] Hybrid mode (with AI): Process 1000 emails in ≤10 minutes
- [ ] All extractions include confidence score (high/medium/low)
- [ ] AI timeout after 30 seconds (mark as failed, continue with pattern result)
- [ ] Graceful degradation: AI unavailable → continue with pattern-only
- [ ] Log extraction method used (pattern vs. ai) for analysis
- [ ] Company extracted correctly from user's real email examples (Perplexity, Plaid, Gem, etc.)

---

## 5. Functional Requirements (Part 2)

### 4.3 Status Hierarchy & Updates

#### 4.3.1 Status Hierarchy Definition

```
Applied (Level 0) ─────────── Lowest Priority
    ↓ (can move up)
Interviewing (Level 1) ─────┐
                            ├── Middle Priority (Equal Level)
Rejected (Level 1) ─────────┘
    ↓ (can move up)
Offer (Level 2) ───────────── Highest Priority
```

**Level Values:**
```python
STATUS_HIERARCHY = {
    'Applied': 0,
    'Interviewing': 1,
    'Rejected': 1,  # Same level as Interviewing
    'Offer': 2
}
```

**Core Rule:** Status can move **UP or SIDEWAYS**, never **DOWN**

**Rationale:**
- Once you get an offer, you won't suddenly be "applied" or "rejected"
- Interviewing ↔ Rejected is sideways (same level) - company can change their mind
- Prevents accidental data loss (offer → rejection would lose critical info)
- Forces manual review of unusual situations (conflicts)

#### 4.3.2 Status Update Rules

```python
def can_update_status(current_status, new_status):
    """
    Determine if status update is allowed
    
    Returns: (allowed: bool, reason: str)
    """
    current_level = STATUS_HIERARCHY.get(current_status, 0)
    new_level = STATUS_HIERARCHY.get(new_status, 0)
    
    if new_level >= current_level:
        return (True, f"Status update allowed: {current_status} → {new_status}")
    else:
        return (False, f"Cannot downgrade status: {current_status} → {new_status}")
```

**Valid Transitions Table:**

| Current Status | New Status | Level Change | Action | Reasoning |
|---------------|------------|--------------|--------|-----------|
| Applied | Interviewing | 0 → 1 (UP) | ✅ Update | Company moving forward with you |
| Applied | Rejected | 0 → 1 (UP) | ✅ Update | Application rejected |
| Applied | Offer | 0 → 2 (UP) | ✅ Update | Fast track to offer (rare but possible) |
| Interviewing | Rejected | 1 → 1 (SIDEWAYS) | ✅ Update | Interview didn't work out |
| Rejected | Interviewing | 1 → 1 (SIDEWAYS) | ✅ Update | Company reconsidered (rare) |
| Interviewing | Offer | 1 → 2 (UP) | ✅ Update | Interview successful! |
| Rejected | Offer | 1 → 2 (UP) | ✅ Update | Rare but possible (company error?) |
| **Offer** | **Rejected** | **2 → 1 (DOWN)** | **❌ FLAG** | **Cannot downgrade - conflict** |
| **Offer** | **Interviewing** | **2 → 1 (DOWN)** | **❌ FLAG** | **Cannot downgrade - conflict** |
| Interviewing | Applied | 1 → 0 (DOWN) | ❌ FLAG | Cannot downgrade |
| Rejected | Applied | 1 → 0 (DOWN) | ❌ FLAG | Cannot downgrade |

#### 4.3.3 Conflict Detection & Handling

**When Conflict Occurs:**

A conflict occurs when a new email would cause a status downgrade.

**Actions When Conflict Detected:**

1. **Do NOT update status** - Keep current (higher) status
2. **Add ⚠️ flag** to Notes column in Excel
3. **Add conflict note** with details: new status, old status, date
4. **Append email ID** to Email IDs list (track the conflicting email)
5. **Update "Last Updated" date** to reflect when conflict was detected
6. **Do NOT auto-delete** the conflicting email (user should review)
7. **Log conflict** to audit log for investigation

```python
def handle_status_conflict(excel_row, current_status, new_status, new_date, new_email_id):
    """
    Handle status conflict by flagging in Excel
    
    Does NOT update status, only adds warning
    
    Args:
        excel_row: Row index in Excel
        current_status: Current status in Excel
        new_status: New status from email (would be downgrade)
        new_date: Date of conflicting email
        new_email_id: Gmail message ID of conflicting email
    """
    # Build conflict note
    conflict_note = (
        f"⚠️ Conflict: received {new_status} after {current_status} "
        f"on {new_date.strftime('%Y-%m-%d')}"
    )
    
    # Get current notes from Excel
    current_notes = get_cell_value(excel_row, 'Notes')
    
    # Append conflict note
    if current_notes:
        updated_notes = f"{current_notes}; {conflict_note}"
    else:
        updated_notes = conflict_note
    
    # Update Excel (status unchanged, add note)
    set_cell_value(excel_row, 'Notes', updated_notes)
    
    # Append email ID (track conflicting email)
    current_ids = get_cell_value(excel_row, 'Email IDs')
    if current_ids:
        updated_ids = f"{current_ids}, {new_email_id}"
    else:
        updated_ids = new_email_id
    set_cell_value(excel_row, 'Email IDs', updated_ids)
    
    # Update Last Updated date (when conflict occurred)
    set_cell_value(excel_row, 'Date Last Updated', new_date.strftime('%Y-%m-%d'))
    
    # Log conflict for review
    logger.warning(
        f"CONFLICT: Company row {excel_row}, "
        f"kept {current_status}, received {new_status}, "
        f"email {new_email_id}"
    )
    
    return {
        'is_conflict': True,
        'kept_status': current_status,
        'conflicting_status': new_status,
        'conflicting_email_id': new_email_id
    }
```

**Example Conflict Scenario:**

```
Excel Row BEFORE new email:
┌──────────┬──────────┬────────┬────────────┬──────────────────────┬────────────┬───────┐
│ Company  │ Position │ Status │ Date First │ Date Last Updated    │ Email IDs  │ Notes │
├──────────┼──────────┼────────┼────────────┼──────────────────────┼────────────┼───────┤
│ TechCorp │ SWE      │ Offer  │ 2026-01-15 │ 2026-01-20           │ msg_123,   │       │
│          │          │        │            │                      │ msg_456    │       │
└──────────┴──────────┴────────┴────────────┴──────────────────────┴────────────┴───────┘

New Email Received (2026-01-25):
Subject: "Application Update from TechCorp"
From: recruiting@techcorp.com
Body: "Unfortunately, we will not be moving forward with your application..."
Extracted Status: Rejected

Processing Logic:
- Current status: Offer (Level 2)
- New status: Rejected (Level 1)
- Level 1 < Level 2 → DOWNGRADE ATTEMPT → CONFLICT!

Excel Row AFTER conflict handling:
┌──────────┬──────────┬────────┬────────────┬──────────────────────┬─────────────────┬────────────────────────────────────────┐
│ Company  │ Position │ Status │ Date First │ Date Last Updated    │ Email IDs       │ Notes                                  │
├──────────┼──────────┼────────┼────────────┼──────────────────────┼─────────────────┼────────────────────────────────────────┤
│ TechCorp │ SWE      │ Offer  │ 2026-01-15 │ 2026-01-25           │ msg_123,        │ ⚠️ Conflict: received Rejected after  │
│          │          │ (kept!)│            │ (updated!)           │ msg_456,        │ Offer on 2026-01-25                    │
│          │          │        │            │                      │ msg_789 (added!)│                                        │
└──────────┴──────────┴────────┴────────────┴──────────────────────┴─────────────────┴────────────────────────────────────────┘

Result:
- Status remains: Offer (NOT changed to Rejected)
- Conflicting email ID added: msg_789
- Date updated: 2026-01-25 (when conflict detected)
- Note added: Clear explanation of what happened
- Email NOT deleted: User can investigate manually
- Logged to audit: System administrators can review
```

**Why This Matters:**

- Sometimes companies send rejection emails to wrong candidate
- Sometimes rejection is for different position at same company
- Sometimes there's email threading confusion
- User should manually review to understand what really happened
- Better to flag and preserve data than to silently corrupt it

#### 4.3.4 Multiple Emails from Same Company

**Scenario:** User applies to same company multiple times for different positions

**Current Behavior (MVP):**
- System treats as ONE company (single row in Excel)
- Most recent position shown in Position field
- Status reflects highest level achieved across all positions
- All email IDs tracked in comma-separated list

**Example Flow:**

```
Email 1 (2026-01-15):
Subject: "Thank you for applying - Backend Engineer at TechCorp"
Extracted: Company=TechCorp, Position="Backend Engineer", Status=Applied

Excel after Email 1:
Company: TechCorp | Position: Backend Engineer | Status: Applied

---

Email 2 (2026-02-10):
Subject: "Thank you for applying - Frontend Engineer at TechCorp"
Extracted: Company=TechCorp, Position="Frontend Engineer", Status=Applied

Excel after Email 2:
Company: TechCorp | Position: Frontend Engineer | Status: Applied (position updated)

---

Email 3 (2026-02-20):
Subject: "Interview Request - Frontend Engineer"
Extracted: Company=TechCorp, Position="Frontend Engineer", Status=Interviewing

Excel after Email 3:
Company: TechCorp | Position: Frontend Engineer | Status: Interviewing (status upgraded)

Email IDs: msg_123, msg_456, msg_789
```

**Limitation:**
- Can't track status per position (only per company)
- Backend and Frontend applications merged into one row

**Workaround (Manual):**
- User can add note: "Multiple applications: BE (Applied), FE (Interviewing)"

**Future Enhancement:**
- Track multiple positions per company
- Separate rows for each position, grouped by company
- Position-specific status tracking

#### 4.3.5 Acceptance Criteria

- [ ] One row per company in Excel (no duplicate company names)
- [ ] Status updates follow hierarchy rules strictly (no downgrades without flagging)
- [ ] All conflicts flagged with ⚠️ symbol in Notes column
- [ ] Conflict notes include: new status, old status, date received
- [ ] Conflicting emails never auto-deleted (always kept for manual review)
- [ ] "Last Updated" date always reflects most recent email received
- [ ] All email IDs stored (comma-separated, no duplicates)
- [ ] Status hierarchy levels documented in code constants
- [ ] Every conflict logged to audit file with full details
- [ ] Conflict handling tested with real scenarios (Offer → Rejected)

---

### 4.4 Excel Storage

#### 4.4.1 File Structure

**File:** `job_applications.xlsx`  
**Default Location:** `~/job_applications.xlsx` (user's home directory)  
**Sheet Name:** "Applications"  
**Format:** Microsoft Excel 2007+ (.xlsx format)

**Column Structure:**

| Column | Width | Data Type | Format | Description |
|--------|-------|-----------|--------|-------------|
| **A: Company Name** | 20 chars | Text | - | Company name (or "Unknown" if not extracted) |
| **B: Position** | 25 chars | Text | - | Job title (or "Not specified") |
| **C: Status** | 15 chars | Text | - | Applied, Interviewing, Rejected, Offer |
| **D: Confidence** | 12 chars | Text | - | high, medium, low |
| **E: Date First Seen** | 15 chars | Date | YYYY-MM-DD | Date of first email from company |
| **F: Date Last Updated** | 18 chars | Date | YYYY-MM-DD | Date of most recent email |
| **G: Email IDs** | 35 chars | Text | - | Comma-separated Gmail message IDs |
| **H: Notes** | 50 chars | Text | - | User notes, conflict flags, system messages |

**Example Data:**

```
| A            | B                    | C            | D          | E          | F          | G                        | H                           |
|--------------|----------------------|--------------|------------|------------|------------|--------------------------|----------------------------|
| Company Name | Position             | Status       | Confidence | Date First | Date Last  | Email IDs                | Notes                      |
| Perplexity   | SWE                  | Applied      | high       | 2026-01-15 | 2026-01-15 | msg_abc123               |                            |
| Plaid        | Platform Engineer    | Interviewing | high       | 2026-01-10 | 2026-01-22 | msg_def456, msg_ghi789   |                            |
| Gem          | Software Engineer    | Rejected     | high       | 2026-01-05 | 2026-01-18 | msg_jkl012               |                            |
| Neuralink    | Backend Developer    | Offer        | high       | 2026-01-01 | 2026-01-25 | msg_mno345, msg_pqr678   |                            |
| Unknown      | Not specified        | Applied      | low        | 2026-01-12 | 2026-01-12 | msg_stu901               | NEEDS REVIEW               |
| TechCorp     | Staff Engineer       | Offer        | high       | 2026-01-03 | 2026-01-23 | msg_vwx234, msg_yz567    | ⚠️ Conflict: received      |
|              |                      |              |            |            |            |                          | Rejected after Offer       |
|              |                      |              |            |            |            |                          | on 2026-01-23              |
```

#### 4.4.2 Excel Operations

**Operation 1: Create New Row**

```python
from openpyxl import Workbook, load_workbook
from pathlib import Path

def create_new_row(workbook, company, position, status, confidence, date, email_id):
    """
    Add new company row to Excel
    
    Args:
        workbook: openpyxl Workbook object
        company: Company name
        position: Job position
        status: Applied/Interviewing/Rejected/Offer
        confidence: high/medium/low
        date: datetime object or string (YYYY-MM-DD)
        email_id: Gmail message ID
    """
    ws = workbook['Applications']
    
    # Format date
    date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else date
    
    # Create new row
    new_row = [
        company,               # A: Company Name
        position,              # B: Position
        status,                # C: Status
        confidence,            # D: Confidence
        date_str,              # E: Date First Seen
        date_str,              # F: Date Last Updated (same initially)
        email_id,              # G: Email IDs
        ''                     # H: Notes (empty initially)
    ]
    
    # Append to worksheet
    ws.append(new_row)
    
    logger.info(f"Created new row: {company} - {status}")
```

**Operation 2: Update Existing Row**

```python
def update_existing_row(workbook, company_row_idx, new_status, new_date, new_email_id):
    """
    Update existing company row with new information
    
    Handles:
    - Status hierarchy validation
    - Conflict detection
    - Email ID appending
    - Date updates
    
    Args:
        workbook: openpyxl Workbook object
        company_row_idx: Row index in Excel (1-based, row 1 is header)
        new_status: New status from email
        new_date: Date of new email
        new_email_id: Gmail message ID
    
    Returns:
        dict with 'updated': bool, 'is_conflict': bool
    """
    ws = workbook['Applications']
    
    # Get current status (Column C)
    current_status = ws.cell(company_row_idx, 3).value
    
    # Check if update allowed
    allowed, reason = can_update_status(current_status, new_status)
    
    date_str = new_date.strftime('%Y-%m-%d') if hasattr(new_date, 'strftime') else new_date
    
    if allowed:
        # Update status (Column C)
        ws.cell(company_row_idx, 3, new_status)
        
        # Update last updated date (Column F)
        ws.cell(company_row_idx, 6, date_str)
        
        # Append email ID (Column G)
        current_ids = ws.cell(company_row_idx, 7).value or ''
        if current_ids:
            updated_ids = f"{current_ids}, {new_email_id}"
        else:
            updated_ids = new_email_id
        ws.cell(company_row_idx, 7, updated_ids)
        
        logger.info(f"Updated row {company_row_idx}: {current_status} → {new_status}")
        
        return {'updated': True, 'is_conflict': False}
    
    else:
        # Handle conflict (status NOT updated)
        handle_status_conflict_excel(
            ws, company_row_idx, current_status, new_status, date_str, new_email_id
        )
        
        logger.warning(f"Conflict at row {company_row_idx}: {reason}")
        
        return {'updated': False, 'is_conflict': True}
```

**Operation 3: Flag Conflict (Excel)**

```python
def handle_status_conflict_excel(ws, row_idx, current_status, new_status, new_date_str, new_email_id):
    """
    Add conflict flag to Excel row without changing status
    
    Args:
        ws: openpyxl Worksheet object
        row_idx: Row index (1-based)
        current_status: Current status in Excel (kept)
        new_status: New status from email (rejected)
        new_date_str: Date string (YYYY-MM-DD)
        new_email_id: Gmail message ID
    """
    # Create conflict note
    conflict_note = f"⚠️ Conflict: received {new_status} after {current_status} on {new_date_str}"
    
    # Get current notes (Column H)
    current_notes = ws.cell(row_idx, 8).value or ''
    
    # Append conflict note
    if current_notes:
        updated_notes = f"{current_notes}; {conflict_note}"
    else:
        updated_notes = conflict_note
    
    ws.cell(row_idx, 8, updated_notes)
    
    # Still append email ID (Column G) - track conflicting email
    current_ids = ws.cell(row_idx, 7).value or ''
    if current_ids:
        updated_ids = f"{current_ids}, {new_email_id}"
    else:
        updated_ids = new_email_id
    ws.cell(row_idx, 7, updated_ids)
    
    # Update last updated date (Column F) - when conflict occurred
    ws.cell(row_idx, 6, new_date_str)
```

**Operation 4: Find Company Row**

```python
def find_company_row(workbook, company_name):
    """
    Find Excel row index for given company
    
    Args:
        workbook: openpyxl Workbook object
        company_name: Company name to search for
    
    Returns:
        int: Row index (1-based) or None if not found
    """
    ws = workbook['Applications']
    
    # Start from row 2 (row 1 is header)
    for row_idx in range(2, ws.max_row + 1):
        cell_value = ws.cell(row_idx, 1).value  # Column A (Company Name)
        
        if cell_value and cell_value.lower() == company_name.lower():
            return row_idx
    
    return None
```

**Operation 5: Save with Auto-Backup**

```python
def save_excel_with_backup(workbook, file_path):
    """
    Save Excel file and create backup
    
    Args:
        workbook: openpyxl Workbook object
        file_path: Path to Excel file
    """
    file_path = Path(file_path).expanduser()
    
    # Create backup if file exists
    if file_path.exists():
        create_backup(file_path)
    
    # Save workbook
    workbook.save(file_path)
    logger.info(f"Saved Excel: {file_path}")
```

#### 4.4.3 Acceptance Criteria

- [ ] Excel file created with headers if doesn't exist
- [ ] Header row: bold font, light blue background (#D5E8F0)
- [ ] One row per unique company (case-insensitive matching)
- [ ] All fields populated (use "Unknown"/"Not specified" for missing)
- [ ] Email IDs stored as comma-separated list, no duplicates
- [ ] File saved after processing every 100 emails
- [ ] Backup created before each scan (timestamped)
- [ ] Old backups auto-deleted (7-day retention)
- [ ] Conditional formatting: Status colors, conflict warnings
- [ ] Columns auto-sized to content
- [ ] Header row frozen (stays visible when scrolling)
- [ ] Compatible with Excel, Google Sheets, LibreOffice

---

## 6. Functional Requirements (Part 3)

### 4.5 Deletion Logic

#### 4.5.1 Deletion Rules (Core Logic)

**Delete email if ALL of the following are true:**

1. **Status = "Applied" OR Status = "Rejected"**
2. **Email does NOT contain ANY safety keywords**
3. **Email is NOT a conflict case** (no ⚠️ flag in Excel)

**Keep email if ANY of the following are true:**

1. **Status = "Interviewing" OR Status = "Offer"**
2. **Email contains ANY safety keyword**
3. **Email is a conflict case**

**Deletion Decision Table:**

| Status | Safety Keywords? | Conflict? | Action | Reasoning |
|--------|-----------------|-----------|--------|-----------|
| Applied | No | No | ✅ **DELETE** | Just confirmation, no value after extraction |
| Applied | Yes | No | ❌ **KEEP** | Contains interview/offer/assessment keyword |
| Applied | No | Yes | ❌ **KEEP** | Conflict requires manual review |
| Rejected | No | No | ✅ **DELETE** | No need to keep rejection emails |
| Rejected | Yes | No | ❌ **KEEP** | Contains important keyword (rare but possible) |
| Rejected | No | Yes | ❌ **KEEP** | Conflict requires review |
| Interviewing | Any | Any | ❌ **KEEP** | Always keep interview emails |
| Offer | Any | Any | ❌ **KEEP** | Always keep offer emails |

```python
def should_delete_email(extraction_result, email_text, is_conflict):
    """
    Determine if email should be deleted
    
    Args:
        extraction_result: dict with 'status', 'company', etc.
        email_text: Full email text (subject + body combined)
        is_conflict: bool, whether this email created a conflict
    
    Returns:
        tuple: (should_delete: bool, reason: str)
    """
    status = extraction_result['status']
    
    # Rule 1: Never delete Interviewing or Offer
    if status in ['Interviewing', 'Offer']:
        return False, f"Status is {status} (always kept)"
    
    # Rule 2: Never delete conflicts
    if is_conflict:
        return False, "Email created status conflict (requires review)"
    
    # Rule 3: Check safety keywords
    has_safety_keyword, keyword = contains_safety_keyword(email_text)
    if has_safety_keyword:
        return False, f"Contains safety keyword: '{keyword}'"
    
    # Rule 4: Delete Applied and Rejected (if passed all checks above)
    if status in ['Applied', 'Rejected']:
        return True, f"Status is {status} (safe to delete)"
    
    # Default: don't delete
    return False, "Unknown status or edge case"
```

#### 4.5.2 Safety Keywords (Deletion Prevention)

**Even if email is classified as "Applied" or "Rejected", do NOT delete if it contains ANY of these keywords:**

```python
SAFETY_KEYWORDS = [
    # Interview-related
    'interview',
    'phone screen',
    'video call',
    'video interview',
    'zoom call',
    'teams meeting',
    'google meet',
    'next steps',
    'schedule a call',
    'schedule call',
    'schedule a meeting',
    'schedule meeting',
    'speak with',
    'meet with',
    'meeting',
    'call with',
    'chat with',
    
    # Assessment-related
    'assessment',
    'technical challenge',
    'coding challenge',
    'programming challenge',
    'take-home',
    'take home',
    'homework',
    'project',
    'assignment',
    'test',
    'exercise',
    
    # Offer-related
    'offer',
    'job offer',
    'offer letter',
    'compensation',
    'salary',
    'benefits',
    'stock options',
    'equity',
    'sign-on bonus',
    'signing bonus',
    'relocation',
    'start date',
    
    # Time-sensitive
    'urgent',
    'asap',
    'immediately',
    'deadline',
    'respond by',
    'reply by',
    'due date',
    'time-sensitive',
    
    # Account/security (avoid deleting account emails)
    'password',
    'account',
    'verify',
    'verification',
    'security',
    'two-factor',
    '2fa',
    'authenticate',
    'reset',
    
    # Document requests
    'references',
    'background check',
    'documents',
    'upload',
    'submit',
    'provide',
    'send us',
]

def contains_safety_keyword(email_text):
    """
    Check if email contains any safety keywords
    
    Args:
        email_text: Combined subject + body text
    
    Returns:
        tuple: (has_keyword: bool, keyword: str or None)
    """
    text_lower = email_text.lower()
    
    for keyword in SAFETY_KEYWORDS:
        if keyword in text_lower:
            return True, keyword
    
    return False, None
```

**Example - Safety Keyword Protection:**

```
Email:
Subject: "Thank you for applying to TechCorp"
Body: "We received your application for Software Engineer. 
       We would like to schedule a phone screen with you next week.
       Please reply with your availability..."

Initial Classification:
- Subject matches: "thank you for applying"
- Status: Applied
- Without safety check: Would be DELETED

Safety Keyword Check:
- Text contains: "schedule a phone screen"
- Safety keyword found: "schedule"
- Action: DO NOT DELETE

Corrected Action:
- Status should be updated to: Interviewing
- Email: KEPT in inbox
- User can respond to schedule interview
```

#### 4.5.3 Batch Processing Flow

```python
def process_and_delete_emails(service, emails, config):
    """
    Complete processing pipeline with selective deletion
    
    Args:
        service: Gmail API service object
        emails: List of email objects from Gmail
        config: Configuration dict with 'use_ai', 'confirm_delete', etc.
    
    Returns:
        dict with processing results and statistics
    """
    # Initialize results tracking
    results = {
        'total_emails': len(emails),
        'companies_found': set(),
        'status_counts': {'Applied': 0, 'Interviewing': 0, 'Rejected': 0, 'Offer': 0},
        'to_delete': [],
        'to_keep': [],
        'deletion_reasons': {},
        'keep_reasons': {},
        'conflicts': [],
        'low_confidence': [],
        'safety_protected': []
    }
    
    # Load or create Excel workbook
    excel_path = Path(config.get('excel_path', '~/job_applications.xlsx')).expanduser()
    workbook = initialize_excel_file(excel_path)
    
    print(f"\nProcessing {len(emails)} emails...")
    
    # Step 1: Process all emails (extract, classify, update Excel)
    for i, email in enumerate(emails):
        # Show progress every 100 emails
        if i % 100 == 0:
            print(f"Progress: {i}/{len(emails)} emails processed...")
            # Save Excel every 100 emails
            if i > 0:
                save_excel_with_backup(workbook, excel_path)
        
        # Extract information
        extraction = extract_email_info(email, config)
        
        # Update or create Excel row
        company = extraction['company']
        excel_row = find_company_row(workbook, company)
        
        if excel_row:
            # Update existing company
            update_result = update_existing_row(
                workbook, excel_row, 
                extraction['status'], 
                extraction['email_date'],
                extraction['email_id']
            )
            is_conflict = update_result['is_conflict']
        else:
            # Create new company row
            create_new_row(
                workbook, company, extraction['position'], extraction['status'],
                extraction['confidence'], extraction['email_date'], extraction['email_id']
            )
            is_conflict = False
        
        # Track statistics
        results['companies_found'].add(company)
        results['status_counts'][extraction['status']] += 1
        
        # Determine if should delete this email
        email_text = f"{email['subject']} {email.get('body', '')}"
        should_del, reason = should_delete_email(extraction, email_text, is_conflict)
        
        if should_del:
            results['to_delete'].append(email['id'])
            results['deletion_reasons'][email['id']] = reason
        else:
            results['to_keep'].append(email['id'])
            results['keep_reasons'][email['id']] = reason
            
            # Track specific keep reasons
            if is_conflict:
                results['conflicts'].append((company, email['id']))
            if contains_safety_keyword(email_text)[0]:
                results['safety_protected'].append((company, email['id']))
        
        # Track low confidence for user review
        if extraction['confidence'] == 'low':
            results['low_confidence'].append((company, email['id']))
    
    # Final save
    save_excel_with_backup(workbook, excel_path)
    print(f"\n✓ Processed all {len(emails)} emails")
    print(f"✓ Excel saved: {excel_path}")
    
    # Step 2: Generate and display summary
    summary = generate_summary_report(results)
    print("\n" + summary)
    
    # Step 3: Get user confirmation (if required)
    if config.get('confirm_delete', True) and len(results['to_delete']) > 0:
        response = input("\nReady to delete emails? They will be moved to Trash (30-day recovery). [Y/n]: ")
        if response.lower() not in ['y', 'yes', '']:
            print("❌ Deletion cancelled by user.")
            return {
                'success': False,
                'deleted_count': 0,
                'kept_count': len(results['to_keep']),
                'cancelled': True
            }
    
    # Step 4: Delete emails (move to trash)
    if len(results['to_delete']) > 0:
        deleted_count = delete_emails_batch(service, results['to_delete'])
    else:
        print("\n✓ No emails to delete")
        deleted_count = 0
    
    return {
        'success': True,
        'deleted_count': deleted_count,
        'kept_count': len(results['to_keep']),
        'cancelled': False,
        'results': results
    }
```

#### 4.5.4 Summary Report (Before Deletion)

```python
def generate_summary_report(results):
    """
    Generate comprehensive summary report
    
    Returns: string with formatted summary
    """
    total = results['total_emails']
    companies = len(results['companies_found'])
    status_counts = results['status_counts']
    to_delete = len(results['to_delete'])
    to_keep = len(results['to_keep'])
    conflicts = len(results['conflicts'])
    safety_protected = len(results['safety_protected'])
    low_conf = len(results['low_confidence'])
    
    # Calculate delete breakdown
    applied_count = status_counts['Applied']
    rejected_count = status_counts['Rejected']
    interviewing_count = status_counts['Interviewing']
    offer_count = status_counts['Offer']
    
    report = f"""
{'='*70}
PROCESSING COMPLETE
{'='*70}

Summary:
  • Total job emails found: {total:,}
  • Companies identified: {companies} unique companies

Status Breakdown:
  • Applied:      {applied_count:>5} emails (will be deleted)
  • Interviewing: {interviewing_count:>5} emails (KEPT)
  • Rejected:     {rejected_count:>5} emails (will be deleted)
  • Offer:        {offer_count:>5} emails (KEPT)

Deletion Summary:
  → {to_delete:,} emails will be deleted
  → {to_keep:,} emails will be kept

Safety Checks Performed:
  ✓ {safety_protected} emails protected by safety keywords
    (contains: interview, offer, assessment, schedule, etc.)
  ✓ {conflicts} conflicts flagged (status downgrades prevented)
  ✓ All Interviewing and Offer emails protected
  ⚠ {low_conf} emails marked "Needs Review" (low confidence extraction)

Data Saved:
  → Excel file: ~/job_applications.xlsx
  → Backup created with timestamp

{'='*70}
    """
    return report.strip()
```

#### 4.5.5 Gmail API Deletion (Trash, Not Permanent)

```python
from googleapiclient.errors import HttpError
import time

def delete_email(service, email_id):
    """
    Move single email to trash (not permanent delete)
    
    Args:
        service: Gmail API service object
        email_id: Gmail message ID
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        service.users().messages().trash(
            userId='me',
            id=email_id
        ).execute()
        
        # Log deletion to audit file
        log_deletion(email_id, datetime.now())
        
        return True
        
    except HttpError as error:
        logger.error(f"Failed to delete {email_id}: {error}")
        return False


def delete_emails_batch(service, email_ids, batch_size=50):
    """
    Delete emails in batches with progress indicator
    
    Args:
        service: Gmail API service object
        email_ids: List of Gmail message IDs to delete
        batch_size: Emails per batch (default: 50 for rate limit compliance)
    
    Returns:
        int: Number of emails successfully deleted
    """
    total = len(email_ids)
    deleted = 0
    failed = []
    
    print(f"\nDeleting {total:,} emails (moving to Trash)...")
    
    # Log batch start
    log_deletion_batch_start(total)
    
    for i in range(0, total, batch_size):
        batch = email_ids[i:i+batch_size]
        
        for email_id in batch:
            if delete_email(service, email_id):
                deleted += 1
            else:
                failed.append(email_id)
            
            # Small delay to avoid rate limits (10 emails per second max)
            time.sleep(0.1)
        
        # Show progress
        progress = min(i + len(batch), total)
        percent = (progress / total) * 100
        bar_length = 40
        filled = int(bar_length * progress / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"Progress: [{bar}] {percent:.0f}% ({progress:,}/{total:,})", end='\r')
    
    print()  # New line after progress bar
    
    # Log batch completion
    log_deletion_batch_complete(deleted)
    
    # Summary
    print(f"\n✓ {deleted:,}/{total:,} emails moved to trash")
    if failed:
        print(f"⚠ {len(failed)} emails failed to delete (see logs)")
    
    print(f"\nRecovery Options:")
    print(f"  1. Gmail web: Trash folder → Select → Move to Inbox")
    print(f"  2. Undo command: emailagent job undo-last")
    print(f"  3. Auto-delete: Gmail permanently deletes after 30 days")
    print(f"\nDeletion log: ~/.emailagent/logs/deletions_{datetime.now().strftime('%Y%m%d')}.log")
    
    return deleted
```

#### 4.5.6 Acceptance Criteria

- [ ] Only "Applied" and "Rejected" status emails deleted
- [ ] Safety keywords prevent deletion (tested with all keywords)
- [ ] Conflicting emails never auto-deleted
- [ ] Summary report shows exact counts before deletion
- [ ] Single Y/n confirmation (not per-email)
- [ ] Progress bar displayed during deletion
- [ ] All deletions logged with timestamp, email ID, status, company
- [ ] Emails moved to trash (not permanent delete)
- [ ] 30-day recovery window (Gmail automatic)
- [ ] Recovery instructions displayed after deletion
- [ ] Batch size: 50 emails per API call (rate limit compliance)
- [ ] 0.1 second delay between deletions (10/second max)
- [ ] Failed deletions tracked and reported
- [ ] Undo command available for last batch

---

**End of Part 2**

**Next:** Part 3 will cover remaining sections (Extraction Patterns from Real Emails, CLI Specification, Configuration, Dependencies, etc.)

# Product Requirements Document
# Job Email Tracker - Part 3

**Version:** 1.0  
**Date:** January 26, 2026  
**Product:** EmailAgent - Job Application Tracker (Feature 2)  
**Status:** Draft - Ready for Implementation  
**Coverage:** Sections 7-9 (Real Email Patterns, CLI, Configuration)

---

## Table of Contents - Part 3

7. Extraction Patterns (From Real Emails)
   - 7.1 Real Email Analysis
   - 7.2 "Applied" Status Examples
   - 7.3 "Rejected" Status Examples
   - 7.4 Pattern Summary
8. CLI Specification
   - 8.1 Command Structure
   - 8.2 Authentication Commands
   - 8.3 Job Tracking Commands
   - 8.4 Example Workflows
9. Configuration
   - 9.1 Configuration File (config.yaml)
   - 9.2 Environment Variables
   - 9.3 Configuration Validation

---

## 7. Extraction Patterns (From Real Emails)

### 7.1 Real Email Analysis Context

**User provided actual email samples from their Gmail inbox during job search.**

These patterns are derived from REAL emails the user received, ensuring the system works with authentic data. This is not theoretical - these are actual patterns from companies like:
- Perplexity
- Plaid
- Spire
- Neuralink
- Vercel
- Gem
- Robinhood
- Attentive
- Vorto
- Bestow

### 7.2 "Applied" Status Emails (Examples - TO BE DELETED)

User received these confirmation emails after submitting applications:

#### Example 1 - Perplexity

```
Subject: Thank you for applying to Perplexity!
From: recruiting@perplexity.ai

Hi Jamal,

Thanks for applying to Perplexity! We've received your application and
will review it shortly.

We will be in touch if your qualifications match our needs for the role.
Thank you for taking the time to apply and we look forward to getting to
know you better.

Thank you,
Perplexity Recruiting
```

**Extracted Information:**
- **Company:** "Perplexity" (from domain: perplexity.ai)
- **Position:** Not specified in email
- **Status:** "Applied"
- **Matched Keywords:** "thank you for applying", "we've received your application", "we will review"
- **Action:** DELETE (after extracting company)

#### Example 2 - Plaid

```
Subject: Thank you for your application to Plaid
From: jobs@plaid.com

Thank you for your interest in Plaid! We wanted to let you know we
received your application for Software Engineer - Platform, and we are
delighted that you would consider joining our team.

Our team will review your application and will be in touch if your
qualifications match our needs for the role.
```

**Extracted Information:**
- **Company:** "Plaid" (from domain: plaid.com)
- **Position:** "Software Engineer - Platform" (from body)
- **Status:** "Applied"
- **Matched Keywords:** "thank you for your application", "received your application", "our team will review"
- **Action:** DELETE (after extracting)

#### Example 3 - Spire

```
Subject: Application Received | Spire
From: talent@spire.com

Thanks for applying to our Senior Software Engineer (Constellation
Operations) position here at Spire, and certainly for your interest -
We're excited to review your application and get to know you!

If it looks like there is a good match, one of our Talent Team members
will reach out to you.
```

**Extracted Information:**
- **Company:** "Spire" (from domain: spire.com AND subject)
- **Position:** "Senior Software Engineer" (from body)
- **Status:** "Applied"
- **Matched Keywords:** "thanks for applying", "excited to review your application"
- **Action:** DELETE (after extracting)

#### Example 4 - Neuralink

```
Subject: Jamal, your application was sent to Neuralink
From: apply@neuralink.com

Your application was sent to Neuralink
```

**Extracted Information:**
- **Company:** "Neuralink" (from domain: neuralink.com AND subject)
- **Position:** Not specified
- **Status:** "Applied"
- **Matched Keywords:** "application was sent"
- **Action:** DELETE (minimal content email)

#### Example 5 - Vercel

```
Subject: Thank you for applying to Vercel!
From: talent@vercel.com

We wanted to confirm that we received your application for the Software
Engineer, CI/CD role at Vercel.

Thank you for applying! While we do receive a large number of
applications daily, rest assured that we are committed to reviewing and
responding to each application.
```

**Extracted Information:**
- **Company:** "Vercel" (from domain: vercel.com AND subject)
- **Position:** "Software Engineer, CI/CD" (from body)
- **Status:** "Applied"
- **Matched Keywords:** "thank you for applying", "received your application", "committed to reviewing"
- **Action:** DELETE (after extracting)

#### Common "Applied" Patterns Summary

**From Real Emails:**

```python
# Patterns that appear in REAL confirmation emails
APPLIED_PATTERNS_REAL = [
    # Direct confirmation phrases
    r'thank you for (your )?(applying|application|interest)',
    r'thanks for applying',
    r'we.*received your application',
    r'(we )?received your application',
    r'application (has been )?(received|was sent)',
    r'confirm(ing)? (receipt of )?(your )?application',
    r'your application was sent',
    
    # Review/next steps (but not interview)
    r'we will (review|be in touch)',
    r'our team will review',
    r'we are committed to reviewing',
    r'excited to review your application',
    r'delighted that you would consider',
    r'if.*(good match|qualifications match)',
    
    # General appreciation
    r'thank you for taking the time',
    r'we appreciate your interest',
]

# Common sender domains in REAL applied emails
APPLIED_SENDER_DOMAINS_REAL = [
    'recruiting@',
    'jobs@',
    'talent@',
    'apply@',
    'careers@',
    'noreply@',
]
```

**Key Distinguisher:** Applied emails say "we will review" (future tense, passive). They do NOT contain interview/offer keywords.

---

### 7.3 "Rejected" Status Emails (Examples - TO BE DELETED)

User received these rejection emails:

#### Example 1 - Gem

```
Subject: Application Update from Gem
From: recruiting@gem.com

Thank you so much for your interest in Gem and our Software Engineer
role. We know a lot of consideration went into your application.

Unfortunately, we won't be advancing you to the next round of our
hiring process at this time.

Thanks again for your interest in Gem and we wish you well on your
search.
```

**Extracted Information:**
- **Company:** "Gem" (from domain: gem.com AND subject)
- **Position:** "Software Engineer" (from body)
- **Status:** "Rejected"
- **Matched Keywords:** "unfortunately, we won't be advancing"
- **Action:** DELETE (after extracting)

#### Example 2 - Robinhood

```
Subject: Important information about your application to Robinhood
From: recruiting@robinhood.com

Thank you for taking the time to apply for the [PIPELINE] Software
Engineer, IC3 (US) position. We've been extremely fortunate to have a
fantastic response from accomplished candidates such as yourself for
this role. However, after careful consideration, we've made the
decision to not move forward with the interview process at this time.

We really appreciate your time and efforts in applying. We'd love to stay
in touch as our team continues to grow and reconnect down the line.
```

**Extracted Information:**
- **Company:** "Robinhood" (from domain: robinhood.com AND subject)
- **Position:** "Software Engineer, IC3" (from body)
- **Status:** "Rejected"
- **Matched Keywords:** "after careful consideration", "decision to not move forward"
- **Action:** DELETE (after extracting)

#### Example 3 - Attentive

```
Subject: Thanks from Attentive
From: recruiting@attentive.com

Thanks for applying to our Senior Software Engineer, Infrastructure role
at Attentive. You've done some really impressive work!

After reviewing your work and experience, we've made the decision to
not move forward at this time. We hope you don't mind if we reach out
to you in the future when a position opens up that may be a better fit.

We appreciate your interest in Attentive and wish you success in your
job search!
```

**Extracted Information:**
- **Company:** "Attentive" (from domain: attentive.com AND subject)
- **Position:** "Senior Software Engineer, Infrastructure" (from body)
- **Status:** "Rejected"
- **Matched Keywords:** "decision to not move forward", "wish you success in your job search"
- **Action:** DELETE (after extracting)

#### Example 4 - Vorto

```
Subject: Vorto Application
From: hr@vorto.com

Thank you for your interest in the Backend Engineer position at Vorto.
Unfortunately, we will not be moving forward with your application, but
we appreciate your time and interest in Vorto.
```

**Extracted Information:**
- **Company:** "Vorto" (from domain: vorto.com AND subject)
- **Position:** "Backend Engineer" (from body)
- **Status:** "Rejected"
- **Matched Keywords:** "unfortunately, we will not be moving forward"
- **Action:** DELETE (after extracting)

#### Example 5 - Bestow

```
Subject: Follow up from your Backend Software Engineer II (Python)
application at Bestow
From: recruiting@bestow.com

Thanks again for applying to Bestow and our Backend Software Engineer II
(Python) role.

We have received an overwhelming response to our job posting, resulting
in a high volume of applications. While we genuinely value your
qualifications and experience, unfortunately, we are not moving forward
with your application at this time.

Our decision was challenging, as we received many exceptional
applications. We appreciate your interest in joining our team and
encourage you to watch our career page for future opportunities that
align with your skills and experience.
```

**Extracted Information:**
- **Company:** "Bestow" (from domain: bestow.com AND subject)
- **Position:** "Backend Software Engineer II (Python)" (from subject/body)
- **Status:** "Rejected"
- **Matched Keywords:** "unfortunately, we are not moving forward", "watch our career page"
- **Action:** DELETE (after extracting)

#### Common "Rejected" Patterns Summary

**From Real Emails:**

```python
# Patterns that appear in REAL rejection emails
REJECTED_PATTERNS_REAL = [
    # Direct rejection phrases (strongest indicators)
    r'not moving forward',
    r'won\'?t be advancing',
    r'will not be moving forward',
    r'not move forward',
    r'made the decision to not move forward',
    r'we are not moving forward',
    r'decided to move forward with other candidates',
    r'decided to pursue (other|different) candidates',
    
    # Soft rejection phrases
    r'after (careful )?consideration.*not',
    r'unfortunately.*not',
    r'unfortunately, we will not',
    r'unfortunately, we are not',
    
    # Polite closings (still rejection)
    r'wish you (well|success) (in|on) your (search|job search)',
    r'best of luck in your (search|job search)',
    r'success in your job search',
    r'we appreciate your (time|interest)',
    
    # Future consideration (but still rejected now)
    r'(keep|stay) in touch',
    r'reach out.*in the future',
    r'future opportunities',
    r'watch our career page',
    r'encourage you to watch',
    r'when a position opens up',
    
    # Other indicators
    r'overwhelming response',
    r'high volume of applications',
    r'many exceptional applications',
    r'other candidates',
    r'moved forward with other',
]
```

**Key Distinguisher:** Rejection emails contain "unfortunately" or "not moving forward" (definite negative). They often thank you but clearly state no next steps.

---

### 7.4 Pattern Implementation Summary

#### Company Extraction Priority (From Real Emails)

Based on user's actual emails, the most reliable extraction method is:

**1. Email Domain (90% success rate in real emails)**

```
recruiting@perplexity.ai → "Perplexity"
jobs@plaid.com → "Plaid"
talent@spire.com → "Spire"
apply@neuralink.com → "Neuralink"
hr@vorto.com → "Vorto"
recruiting@gem.com → "Gem"
```

**Skip generic domains:**
- greenhouse.io, lever.co, workday, myworkdayjobs
- gmail.com, yahoo.com, outlook.com

**2. Subject Line (when domain is generic)**

```
"Thank you for applying to Perplexity!" → "Perplexity"
"Application Update from Gem" → "Gem"
"Application Received | Spire" → "Spire"
```

**3. Body Text (fallback)**

```
"...your interest in Plaid!" → "Plaid"
"...at Vercel." → "Vercel"
```

#### Status Classification Logic (From Real Emails)

**Applied = Confirmation without next steps**
- "thank you for applying"
- "received your application"
- "we will review" (future, passive)
- NO interview keywords

**Rejected = Clear negative with closure**
- "not moving forward"
- "unfortunately"
- "wish you success in your job search"

**Interviewing = Action requested**
- "interview"
- "phone screen"
- "schedule"
- "next steps" (with specific action)

**Offer = Explicit offer language**
- "pleased to offer"
- "job offer"
- "offer letter"

#### Validation Against Real Data

**Test Cases (From User's Emails):**

| Company | Subject | Expected Status | Expected Action |
|---------|---------|----------------|-----------------|
| Perplexity | "Thank you for applying..." | Applied | DELETE |
| Plaid | "Thank you for your application..." | Applied | DELETE |
| Spire | "Application Received..." | Applied | DELETE |
| Neuralink | "...application was sent..." | Applied | DELETE |
| Vercel | "Thank you for applying..." | Applied | DELETE |
| Gem | "Application Update from Gem" | Rejected | DELETE |
| Robinhood | "Important information..." | Rejected | DELETE |
| Attentive | "Thanks from Attentive" | Rejected | DELETE |
| Vorto | "Vorto Application" | Rejected | DELETE |
| Bestow | "Follow up from your...application" | Rejected | DELETE |

**Acceptance Criteria:**
- [ ] All 10 real email examples correctly classified
- [ ] Company names extracted correctly from all examples
- [ ] Positions extracted where present in email
- [ ] No false positives (interview emails classified as Applied)
- [ ] No false negatives (rejection emails classified as Applied)

---

## 8. CLI Specification

### 8.1 Command Structure

```bash
emailagent <command> [subcommand] [options]
```

**Design Principles:**
- Clear command hierarchy (auth, job, config)
- Intuitive subcommands (scan, list, export)
- Sensible defaults (--no-ai default, no confirmation for previews)
- Progress indicators for long operations
- Colored output for better readability

### 8.2 Authentication Commands

```bash
# ============================================================================
# Authentication Commands
# ============================================================================

# Login with Gmail (OAuth 2.0 flow)
emailagent auth login

  Description:
    Opens browser for Google OAuth authentication.
    User grants permissions for Gmail API access.
    Saves credentials to ~/.emailagent/credentials.json
    Saves refresh token to ~/.emailagent/token.json
  
  Example Output:
    Opening browser for Google authentication...
    ✓ Successfully authenticated as jamal@gmail.com
    ✓ Credentials saved to ~/.emailagent/credentials.json
    ✓ Token saved to ~/.emailagent/token.json


# Logout (revoke credentials)
emailagent auth logout

  Description:
    Deletes token.json (user must re-authenticate next time)
    Optionally revokes OAuth token with Google
  
  Options:
    --revoke    Revoke token with Google (more thorough)
  
  Example Output:
    ✓ Token deleted: ~/.emailagent/token.json
    ✓ You must run 'emailagent auth login' to use the app again


# Check authentication status
emailagent auth status

  Description:
    Shows current authentication status
    Displays authenticated email address
    Shows token expiry (if available)
  
  Example Output:
    ✓ Authenticated as jamal@gmail.com
    ✓ Token valid until: 2026-02-01 10:30:00
    ✓ Credentials: ~/.emailagent/credentials.json
```

### 8.3 Job Tracking Commands

```bash
# ============================================================================
# Job Tracking Commands
# ============================================================================

# Scan for job emails
emailagent job scan [OPTIONS]

  Description:
    Scans Gmail for job-related emails, extracts information,
    updates Excel file, and optionally deletes emails.
  
  Options:
    --use-ai                  Enable Ollama for ambiguous cases (default: false)
    --no-ai                   Pattern-only mode (explicit, default)
    --preview                 Show results without deleting (dry-run)
    --confirm-delete          Delete after confirmation (default behavior)
    --max-emails <number>     Limit emails to process (default: 10000)
    --since <date>            Only process emails after date (YYYY-MM-DD)
    --batch-size <number>     Emails per batch (default: 100)
  
  Examples:
    # Quick scan with pattern matching only (fast)
    $ emailagent job scan --no-ai
    
    # Scan with AI for better accuracy (slower)
    $ emailagent job scan --use-ai
    
    # Preview without deleting (dry-run)
    $ emailagent job scan --preview
    
    # Scan recent emails only
    $ emailagent job scan --since 2026-01-01
    
    # Scan and delete with single confirmation
    $ emailagent job scan --confirm-delete
  
  Example Output:
    Scanning Gmail for job emails...
    Found 1,247 job-related emails
    
    Processing with pattern matching...
    Progress: [████████████████████] 100% (1247/1247)
    
    Results:
      ✓ 1,000 emails processed successfully (high confidence)
      ⚠ 247 emails marked "Needs Review" (low confidence)
    
    Data saved to: ~/job_applications.xlsx
    Backup created: ~/.emailagent/backups/job_applications_backup_20260126_103045.xlsx
    
    Summary:
      • Applied: 892 emails (will be deleted)
      • Interviewing: 45 emails (KEPT)
      • Rejected: 287 emails (will be deleted)
      • Offer: 23 emails (KEPT)
    
    Ready to delete 1,179 emails? [Y/n]: 


# List all applications
emailagent job list [OPTIONS]

  Description:
    Display job applications from Excel in table format.
  
  Options:
    --status <status>         Filter by status (Applied, Interviewing, Rejected, Offer)
    --company <name>          Filter by company name (partial match, case-insensitive)
    --sort <field>            Sort by: date, company, status (default: date-desc)
    --limit <number>          Show only N most recent (default: all)
    --action-required         Show only Interviewing/Offer (items needing action)
    --conflicts               Show only rows with conflicts (⚠️)
    --format <format>         Output format: table, csv, json (default: table)
  
  Examples:
    # List all applications
    $ emailagent job list
    
    # List only interview requests
    $ emailagent job list --status Interviewing
    
    # List applications from "Tech" companies
    $ emailagent job list --company "Tech"
    
    # Show only actionable items
    $ emailagent job list --action-required
    
    # Show conflicts that need review
    $ emailagent job list --conflicts
    
    # Export to CSV
    $ emailagent job list --format csv > applications.csv
  
  Example Output:
    JOB APPLICATIONS (156 companies)
    
    ┌─────────────────────┬──────────────────────┬──────────────┬────────────┬────────────────┐
    │ Company             │ Position             │ Status       │ Last Update│ Notes          │
    ├─────────────────────┼──────────────────────┼──────────────┼────────────┼────────────────┤
    │ Neuralink           │ Backend Developer    │ Offer        │ 2026-01-25 │                │
    │ Plaid               │ Platform Engineer    │ Interviewing │ 2026-01-22 │                │
    │ TechCorp            │ Staff Engineer       │ Offer        │ 2026-01-23 │ ⚠️ Conflict    │
    │ Gem                 │ Software Engineer    │ Rejected     │ 2026-01-18 │                │
    │ Perplexity          │ SWE                  │ Applied      │ 2026-01-15 │                │
    └─────────────────────┴──────────────────────┴──────────────┴────────────┴────────────────┘
    
    Status Summary:
      Applied: 78 | Interviewing: 12 | Rejected: 60 | Offers: 6


# Show detailed application info
emailagent job show <company_name>

  Description:
    Display full details for a specific company application.
  
  Arguments:
    company_name          Company name (case-insensitive, partial match)
  
  Example:
    $ emailagent job show "TechCorp"
  
  Example Output:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    TECHCORP - Staff Engineer
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    Status:          Offer
    Confidence:      high
    Date First Seen: 2026-01-03
    Date Last Update: 2026-01-23
    
    Email Timeline (3 emails):
      1. 2026-01-03: msg_abc123 - Applied
      2. 2026-01-15: msg_def456 - Interviewing
      3. 2026-01-20: msg_ghi789 - Offer
    
    Notes:
      ⚠️ Conflict: received Rejected after Offer on 2026-01-23
    
    Actions:
      • Review conflict email: gmail.com/mail/u/0/#inbox/msg_jkl012
      • Update notes: emailagent job update "TechCorp" --notes "..."


# Update application manually
emailagent job update <company_name> [OPTIONS]

  Description:
    Manually update application details in Excel.
  
  Arguments:
    company_name          Company name
  
  Options:
    --status <status>     Update status (Applied, Interviewing, Rejected, Offer)
    --notes "<text>"      Add/update notes
    --position "<title>"  Update position title
    --clear-conflict      Remove conflict flag
  
  Examples:
    # Add notes
    $ emailagent job update "TechCorp" --notes "Phone screen scheduled for 2/1"
    
    # Update status manually
    $ emailagent job update "StartupXYZ" --status Offer
    
    # Clear conflict after review
    $ emailagent job update "TechCorp" --clear-conflict


# Export data
emailagent job export [OPTIONS]

  Description:
    Export job applications to various formats.
  
  Options:
    --format <format>     csv, json, xlsx (default: csv)
    --output <file>       Output file path (default: stdout or auto-named)
    --status <status>     Export only specific status
    --include-ids         Include email IDs in export
  
  Examples:
    # Export to CSV
    $ emailagent job export --format csv --output my_applications.csv
    
    # Export only offers to JSON
    $ emailagent job export --format json --status Offer --output offers.json
    
    # Export to stdout (pipe to other commands)
    $ emailagent job export --format csv | grep "Interviewing"


# Show statistics
emailagent job stats

  Description:
    Display application statistics and insights.
  
  Example Output:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    JOB APPLICATION STATISTICS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    Total Companies:          156
    
    Status Breakdown:
      Applied:      78 (50.0%)
      Interviewing: 12 (7.7%)
      Rejected:     60 (38.5%)
      Offers:       6 (3.8%)
    
    Response Rate:            50% (78 responses out of 156 applications)
    Offer Rate:               3.8% (6 offers out of 156 applications)
    Interview Rate:           7.7% (12 interviews out of 156 applications)
    
    Average Days to Response: 8.5 days
    
    Companies with no response >30 days: 15
      • CompanyA (45 days since application)
      • CompanyB (38 days since application)
      ...
    
    Recent Activity (last 7 days):
      • 3 new applications
      • 2 interview requests
      • 1 offer received
      • 4 rejections


# Undo last deletion
emailagent job undo-last

  Description:
    Restore emails from last deletion batch.
    Moves emails back from Trash to Inbox.
  
  Example Output:
    Reading deletion log...
    Found last batch: 1,179 emails deleted on 2026-01-26 10:32:15
    
    Restoring from Trash...
    Progress: [████████████████████] 100% (1179/1179)
    
    ✓ Restored 1,179 emails from Trash to Inbox
```

### 8.4 Configuration Commands

```bash
# ============================================================================
# Configuration Commands
# ============================================================================

# Edit configuration file
emailagent config

  Description:
    Opens config.yaml in default text editor.
    Creates default config if doesn't exist.
  
  Example Output:
    Opening ~/.emailagent/config.yaml in editor...


# Show current configuration
emailagent config show

  Description:
    Prints current configuration to terminal.
  
  Example Output:
    Configuration:
      Gmail:
        credentials: ~/.emailagent/credentials.json
        token: ~/.emailagent/token.json
      
      Extraction:
        use_ai: false
        confidence_threshold: 0.7
      
      Excel:
        file_path: ~/job_applications.xlsx
      
      Deletion:
        delete_applied: true
        delete_rejected: true


# Validate configuration
emailagent config validate

  Description:
    Checks configuration for errors.
    Verifies paths, settings, and required fields.
  
  Example Output:
    Validating configuration...
    ✓ Gmail credentials path exists
    ✓ Excel file path writable
    ✓ Logging directory exists
    ✗ Ollama host not reachable (use_ai is enabled)
    
    Configuration status: WARNING
      - 3/4 checks passed
      - Ollama unavailable (disable use_ai or start Ollama)
```

### 8.5 General Commands

```bash
# ============================================================================
# General Commands
# ============================================================================

# Show help
emailagent --help
emailagent <command> --help
emailagent <command> <subcommand> --help

# Show version
emailagent --version

  Example Output:
    EmailAgent v1.0.0
    Job Email Tracker
    Python 3.11+


# Enable verbose logging
emailagent --verbose <command>

  Description:
    Enable DEBUG level logging for detailed output.


# Dry-run mode (no changes made)
emailagent --dry-run <command>

  Description:
    Simulate command without making any changes.
    Shows what would happen.
```

### 8.6 Example Workflows

#### Workflow 1: First-Time Setup and Scan

```bash
# Step 1: Authenticate with Gmail
$ emailagent auth login
Opening browser for Google authentication...
✓ Successfully authenticated as jamal@gmail.com

# Step 2: Run initial scan (preview mode first)
$ emailagent job scan --preview
Scanning Gmail for job emails...
Found 1,247 job-related emails

Processing with pattern matching...
[████████████████████] 100% (5 seconds)

Summary (PREVIEW - no emails deleted):
  - Applied: 892 emails
  - Interviewing: 45 emails
  - Rejected: 287 emails
  - Offer: 23 emails

Would delete: 1,179 emails (Applied + Rejected)
Run without --preview to actually delete.

# Step 3: Review Excel file
$ open ~/job_applications.xlsx
(User reviews companies, positions, statuses)

# Step 4: Run actual deletion
$ emailagent job scan --confirm-delete
... (same processing) ...
Ready to delete 1,179 emails? [Y/n]: Y
✓ 1,179 emails moved to trash

# Step 5: Check results
$ emailagent job list --action-required

ACTIONABLE APPLICATIONS (18):
  • TechCorp - Interviewing (phone screen next week)
  • StartupXYZ - Offer (review offer letter)
  ...
```

#### Workflow 2: Weekly Update (Pattern-Only, Fast)

```bash
# Quick weekly scan for new emails
$ emailagent job scan --no-ai --since 2026-01-20

Found 47 new job emails since 2026-01-20

Processing...
✓ Processed 47 emails in 0.5 seconds
✓ 32 emails deleted
✓ Data updated in ~/job_applications.xlsx

# Check for action items
$ emailagent job list --action-required

New Action Items:
  • CloudCo - Interviewing (schedule on-site)
  • DataCorp - Offer (expires 2026-02-05)
```

#### Workflow 3: Deep Scan with AI (Accurate)

```bash
# Use AI for maximum accuracy (slower)
$ emailagent job scan --use-ai --max-emails 500

Scanning Gmail...
Found 500 emails

Pattern matching (80% complete instantly)...
AI processing remaining 20%...
[████████████████████] 100% (2 minutes)

Results:
  ✓ 485 emails processed successfully
  ⚠ 15 emails still need manual review

Ready to delete 350 emails? [Y/n]: Y
✓ 350 emails deleted
```

### 8.7 Output Formatting

**Success Messages:**
```
✓ Operation completed successfully
```

**Error Messages:**
```
✗ Error: Gmail API authentication failed
  → Run 'emailagent auth login' to authenticate
```

**Progress Indicators:**
```
Processing: [████████████░░░░░░░░] 65% (650/1000)
```

**Summary Tables:**
```
┌─────────────────────┬────────┐
│ Status              │ Count  │
├─────────────────────┼────────┤
│ Applied             │    892 │
│ Interviewing        │     45 │
│ Rejected            │    287 │
│ Offer               │     23 │
├─────────────────────┼────────┤
│ Total               │  1,247 │
└─────────────────────┴────────┘
```

### 8.8 Exit Codes

```
0   - Success
1   - General error
2   - Authentication error
3   - Gmail API error
4   - File I/O error
5   - User cancelled operation
10  - Ollama not available (when --use-ai specified)
11  - Configuration error
12  - Invalid arguments
```

### 8.9 Acceptance Criteria

- [ ] All commands execute without errors
- [ ] Help text displayed for --help on all commands
- [ ] Version displayed for --version
- [ ] Authentication persists between sessions (token refresh works)
- [ ] Progress indicators show during long operations (>5 seconds)
- [ ] Clear error messages for common failures
- [ ] User confirmation required before deletion (unless --preview)
- [ ] Preview mode works without modifying any data
- [ ] Exit codes match specification
- [ ] Colored output works on Linux, macOS, Windows
- [ ] CLI responds within 1 second for non-processing commands

---

## 9. Configuration

### 9.1 Configuration File: config.yaml

**Location:** `~/.emailagent/config.yaml`

**Full Configuration Example:**

```yaml
# ============================================================================
# EmailAgent Configuration File
# ============================================================================
# This file controls all aspects of the job email tracker.
# Edit values below to customize behavior.

# ----------------------------------------------------------------------------
# Gmail Configuration
# ----------------------------------------------------------------------------
gmail:
  # Path to OAuth credentials (downloaded from Google Cloud Console)
  credentials_path: ~/.emailagent/credentials.json
  
  # Path to store OAuth token (auto-generated after first login)
  token_path: ~/.emailagent/token.json
  
  # API request limits
  max_results_per_query: 10000  # Max emails to fetch per scan
  batch_size: 100               # Emails per API request
  
  # Rate limiting (respect Gmail API quotas)
  requests_per_second: 10       # Max 10 requests/second


# ----------------------------------------------------------------------------
# Extraction Configuration
# ----------------------------------------------------------------------------
extraction:
  # Enable/disable AI fallback for ambiguous cases
  # false = Pattern-only (fast, free, 70-80% accurate)
  # true = Hybrid (slower, free, 90-95% accurate)
  use_ai: false  # Default: pattern-only mode
  
  # Confidence threshold for "Needs Review" flagging
  confidence_threshold: 0.7  # Below this = low confidence
  
  # AI triggers (only if use_ai = true)
  ai_triggers:
    low_confidence: true      # Use AI when pattern confidence < 0.7
    unknown_company: true     # Use AI when company = "Unknown"
    unclear_status: true      # Use AI when status unclear


# ----------------------------------------------------------------------------
# Ollama Configuration (only used if extraction.use_ai = true)
# ----------------------------------------------------------------------------
ollama:
  # Ollama server URL
  host: http://localhost:11434
  
  # Model to use
  model: llama3.2:3b
  
  # Request timeout (seconds per email)
  timeout: 30
  
  # Retry settings
  max_retries: 2
  retry_delay: 5  # seconds


# ----------------------------------------------------------------------------
# Excel Configuration
# ----------------------------------------------------------------------------
excel:
  # Path to Excel file
  file_path: ~/job_applications.xlsx
  
  # Sheet name
  sheet_name: Applications
  
  # Backup settings
  auto_backup: true
  backup_directory: ~/.emailagent/backups/
  backup_retention_days: 7  # Delete backups older than this
  
  # Auto-save frequency
  save_after_n_emails: 100  # Save after processing N emails
  
  # Formatting
  use_conditional_formatting: true  # Status colors, conflict warnings
  freeze_header: true               # Keep header visible when scrolling


# ----------------------------------------------------------------------------
# Deletion Configuration
# ----------------------------------------------------------------------------
deletion:
  # Which statuses to delete
  delete_applied: true
  delete_rejected: true
  delete_interviewing: false
  delete_offer: false
  
  # Safety keywords that prevent deletion
  # (Even if status = Applied/Rejected, don't delete if contains these)
  safety_keywords:
    - interview
    - phone screen
    - video call
    - next steps
    - schedule
    - meet with
    - assessment
    - take-home
    - offer
    - compensation
    - urgent
    - deadline
    - password
    - account
    - verify
  
  # Additional safety checks
  never_delete_starred: true          # Keep starred emails
  never_delete_with_attachments: false # Keep emails with attachments
  never_delete_conflicts: true        # Keep conflict emails (⚠️)
  
  # Minimum email age before deletion (days)
  # 0 = allow same-day deletion
  minimum_age_days: 0
  
  # Batch deletion settings
  batch_size: 50              # Emails per API call
  delay_between_deletes: 0.1  # Seconds (rate limit compliance)
  require_confirmation: true  # Ask user before deleting


# ----------------------------------------------------------------------------
# Logging Configuration
# ----------------------------------------------------------------------------
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: INFO
  
  # Log file settings
  log_directory: ~/.emailagent/logs/
  log_file_pattern: emailagent_{date}.log
  max_log_size_mb: 10
  retention_days: 30
  
  # What to log
  log_extractions: true   # Log company/position/status extracted
  log_classifications: true  # Log status classifications
  log_deletions: true     # Log all deletions (ALWAYS true for audit)
  log_api_calls: false    # Log Gmail API calls (verbose, for debugging)


# ----------------------------------------------------------------------------
# CLI Display Settings
# ----------------------------------------------------------------------------
cli:
  # Use colors in terminal output
  use_colors: true
  
  # Show progress bars
  show_progress: true
  
  # Verbose output by default
  verbose: false
  
  # Table formatting style
  # Options: simple, grid, fancy, markdown
  table_style: simple
  
  # Pagination for long lists
  paginate: true
  items_per_page: 50


# ----------------------------------------------------------------------------
# Advanced Settings (rarely need to change)
# ----------------------------------------------------------------------------
advanced:
  # Parallel processing (experimental)
  parallel_extraction: false
  max_workers: 4
  
  # Caching
  cache_enabled: true
  cache_directory: ~/.emailagent/cache/
  cache_ttl_hours: 24
  
  # Performance tuning
  max_body_length: 5000  # Max characters of email body to analyze
```

### 9.2 Environment Variables

**Environment variables override config.yaml settings.**

```bash
# Gmail Configuration
export EMAILAGENT_GMAIL_CREDENTIALS=~/.emailagent/credentials.json
export EMAILAGENT_GMAIL_TOKEN=~/.emailagent/token.json

# Extraction Settings
export EMAILAGENT_USE_AI=false
export EMAILAGENT_CONFIDENCE_THRESHOLD=0.7

# Ollama Settings
export EMAILAGENT_OLLAMA_HOST=http://localhost:11434
export EMAILAGENT_OLLAMA_MODEL=llama3.2:3b

# Excel Settings
export EMAILAGENT_EXCEL_PATH=~/custom_path/applications.xlsx

# Logging
export EMAILAGENT_LOG_LEVEL=DEBUG
export EMAILAGENT_LOG_DIR=~/custom_logs/

# Priority: CLI flags > Environment Variables > config.yaml > defaults
```

### 9.3 Configuration Validation

```python
def validate_config(config):
    """
    Validate configuration file
    
    Returns: (is_valid: bool, errors: list, warnings: list)
    """
    errors = []
    warnings = []
    
    # Required fields
    if 'gmail' not in config:
        errors.append("Missing 'gmail' section")
    else:
        # Check credentials path
        creds_path = Path(config['gmail']['credentials_path']).expanduser()
        if not creds_path.exists():
            errors.append(f"Gmail credentials not found: {creds_path}")
    
    # Excel path writable
    if 'excel' in config:
        excel_path = Path(config['excel']['file_path']).expanduser()
        if not excel_path.parent.exists():
            errors.append(f"Excel directory doesn't exist: {excel_path.parent}")
    
    # Ollama check (if AI enabled)
    if config.get('extraction', {}).get('use_ai', False):
        ollama_host = config.get('ollama', {}).get('host', 'http://localhost:11434')
        try:
            response = requests.get(f"{ollama_host}/api/tags", timeout=5)
            if response.status_code != 200:
                warnings.append(f"Ollama not reachable at {ollama_host}")
        except:
            warnings.append(f"Cannot connect to Ollama at {ollama_host}")
    
    # Log directory exists
    log_dir = Path(config.get('logging', {}).get('log_directory', '~/.emailagent/logs')).expanduser()
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except:
            errors.append(f"Cannot create log directory: {log_dir}")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings
```

**Validation Command:**

```bash
$ emailagent config validate

Validating configuration...

Checking required settings:
  ✓ Gmail credentials path exists
  ✓ Excel file path writable
  ✓ Logging directory exists
  ✗ Ollama host not reachable (use_ai is enabled)

Configuration status: WARNING
  - 3/4 checks passed
  - 1 warning:
    • Ollama unavailable at http://localhost:11434
    • Disable use_ai or start Ollama: `ollama serve`

Warnings do not prevent the app from running.
```

### 9.4 Acceptance Criteria

- [ ] Configuration file created with defaults on first run
- [ ] All paths support ~/ expansion (home directory)
- [ ] Environment variables override config file values
- [ ] CLI flags override both environment and config
- [ ] Invalid config shows clear error messages
- [ ] Config validation command works
- [ ] YAML file is human-readable with comments
- [ ] Config changes take effect immediately (no restart needed for most settings)
- [ ] Backup created before editing config file

---

**End of Part 3**

**Next:** Part 4 will cover remaining sections (Dependencies, Success Metrics, Testing Strategy, Development Phases, Risk Mitigation, etc.)

# Product Requirements Document
# Job Email Tracker - Part 4 (FINAL)

**Version:** 1.0  
**Date:** January 26, 2026  
**Product:** EmailAgent - Job Application Tracker (Feature 2)  
**Status:** Draft - Ready for Implementation  
**Coverage:** Sections 10-14 (Dependencies, Testing, Development, Risk, Future)

---

## Table of Contents - Part 4 (FINAL)

10. Dependencies
11. Success Metrics
12. Testing Strategy
13. Development Phases
14. Risk Mitigation & Future Enhancements

---

## 10. Dependencies

### 10.1 Python Packages (requirements.txt)

```txt
# ============================================================================
# EmailAgent Dependencies
# Version: 1.0.0
# Python: 3.11+
# ============================================================================

# ----------------------------------------------------------------------------
# Core - Gmail API
# ----------------------------------------------------------------------------
google-auth>=2.16.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
google-api-python-client>=2.70.0

# ----------------------------------------------------------------------------
# Excel Operations
# ----------------------------------------------------------------------------
openpyxl>=3.1.0

# ----------------------------------------------------------------------------
# CLI Framework
# ----------------------------------------------------------------------------
click>=8.1.0
# Alternative: typer>=0.9.0 (choose one)

# CLI UI Enhancements
rich>=13.0.0              # Progress bars, tables, colors
colorama>=0.4.6           # Cross-platform colored output

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
pyyaml>=6.0
python-dotenv>=1.0.0

# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------
python-dateutil>=2.8.0    # Date parsing
requests>=2.31.0          # HTTP requests (for Ollama)

# ----------------------------------------------------------------------------
# Optional: AI (only if use_ai = true)
# ----------------------------------------------------------------------------
# Uncomment if using Ollama:
# ollama>=0.1.0

# ----------------------------------------------------------------------------
# Development Dependencies (optional, for contributors)
# ----------------------------------------------------------------------------
# Uncomment for development:
# pytest>=7.4.0
# pytest-cov>=4.1.0
# black>=23.0.0
# mypy>=1.7.0
# flake8>=6.1.0
# pre-commit>=3.5.0
```

### 10.2 External Dependencies

**Required:**
- **Python 3.11+** - Main programming language
- **Gmail account** - For email access
- **Google Cloud project** - For Gmail API credentials
- **Internet connection** - For Gmail API calls

**Optional:**
- **Ollama** - For AI extraction (only if use_ai = true)
  - Download: https://ollama.com
  - Model: llama3.2:3b (~4GB download)
  - Requires: ~8GB RAM minimum

### 10.3 System Requirements

**Minimum (Pattern-only mode):**
- **OS:** Linux, macOS, Windows 10+
- **Python:** 3.11+
- **RAM:** 2GB
- **Disk:** 500MB free space
- **Internet:** Required for Gmail API

**Recommended (With AI):**
- **OS:** Linux, macOS, Windows 10+
- **Python:** 3.11+
- **RAM:** 8GB (for Ollama)
- **Disk:** 10GB free (for Ollama model)
- **Internet:** Required for Gmail API + initial Ollama model download

### 10.4 Installation Guide

```bash
# ============================================================================
# Installation Steps
# ============================================================================

# Step 1: Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Step 2: Install dependencies
pip install -r requirements.txt

# Step 3: Install the package (if packaged)
pip install -e .  # Development mode
# OR
pip install emailagent  # From PyPI (future)

# Step 4: Verify installation
emailagent --version

# Step 5 (Optional): Install and setup Ollama
# Only if you plan to use --use-ai flag
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b

# Step 6: Setup Gmail API credentials
# See SETUP.md for detailed Gmail API setup instructions
```

### 10.5 Gmail API Setup

**Step 1: Create Google Cloud Project**
1. Go to https://console.cloud.google.com
2. Click "Create Project"
3. Name: "EmailAgent" (or your choice)
4. Click "Create"

**Step 2: Enable Gmail API**
1. In your project, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click "Enable"

**Step 3: Create OAuth Credentials**
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Configure consent screen first (if prompted):
   - User Type: External
   - App name: EmailAgent
   - User support email: your-email@gmail.com
   - Developer contact: your-email@gmail.com
4. Application type: "Desktop app"
5. Name: "EmailAgent Desktop"
6. Click "Create"

**Step 4: Download Credentials**
1. Click download icon next to your OAuth client
2. Save as `credentials.json`
3. Move to: `~/.emailagent/credentials.json`

**Step 5: Configure OAuth Scopes**

Required scopes (automatically requested on first login):
```
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.modify
```

**Step 6: First Authentication**
```bash
emailagent auth login
# Opens browser, user grants permissions
# Token saved to ~/.emailagent/token.json
```

### 10.6 Acceptance Criteria

- [ ] All required packages install without errors
- [ ] Gmail API authentication works end-to-end
- [ ] Ollama is optional (app works without it in pattern-only mode)
- [ ] Installation guide tested on Linux, macOS, Windows
- [ ] Version compatibility verified (Python 3.11, 3.12)
- [ ] Dependencies documented with minimum versions

---

## 11. Success Metrics

### 11.1 Extraction Accuracy

**Pattern Matching (use_ai = false):**
- **Company name extraction:** ≥70% accuracy
- **Position extraction:** ≥60% accuracy
- **Status classification:** ≥85% accuracy
- **Overall confidence:** ≥70% emails marked high/medium confidence

**Hybrid Mode (use_ai = true):**
- **Company name extraction:** ≥90% accuracy
- **Position extraction:** ≥75% accuracy
- **Status classification:** ≥95% accuracy
- **Overall confidence:** ≥85% emails marked high/medium confidence

**Measurement Method:**
- Manual review of 100 random emails from real dataset
- Compare extracted data vs. actual email content
- Track false positives/negatives
- Calculate precision, recall, F1 score per field

**Acceptance Criteria:**
- [ ] All 10 user-provided real email examples correctly classified
- [ ] Company names extracted correctly from email domains
- [ ] No false positives (interview emails classified as Applied)
- [ ] No false negatives (rejection emails classified as Applied)

### 11.2 Processing Performance

**Speed Targets:**
- **Pattern-only:** Process 1000 emails in ≤5 seconds
- **With AI (20% ambiguous):** Process 1000 emails in ≤10 minutes
- **Excel save operations:** ≤1 second per 100 emails
- **Gmail API calls:** No throttling errors, respect rate limits

**Measurement Method:**
- Time processing of 1000-email batch
- Profile with Python's cProfile
- Monitor API quota usage
- Test on multiple machines (vary RAM/CPU)

**Acceptance Criteria:**
- [ ] Pattern-only mode completes 1000 emails in ≤5 seconds
- [ ] Hybrid mode completes 1000 emails in ≤10 minutes
- [ ] No Gmail API rate limit errors (429 responses)
- [ ] Memory usage stays under 500MB (pattern-only)
- [ ] Memory usage stays under 2GB (with Ollama)

### 11.3 Deletion Safety

**Zero Tolerance Metrics:**
- **Accidental deletion of Interviewing/Offer emails:** 0
- **Deletion of emails with safety keywords:** 0
- **Unlogged deletions:** 0
- **Silently ignored conflicts:** 0

**Acceptable Metrics:**
- **False positive deletion rate:** <1% (incorrectly marked for deletion)
- **Emails moved to trash (recoverable):** 100%

**Measurement Method:**
- Manual audit of 50 randomly selected deleted emails
- Verify all deletions logged to audit file
- Check trash recovery capability
- Verify safety keyword protection

**Acceptance Criteria:**
- [ ] Zero Interviewing emails deleted in test dataset
- [ ] Zero Offer emails deleted in test dataset
- [ ] All safety keywords tested and working
- [ ] All deletions appear in deletion log
- [ ] Trash recovery tested and working (undo-last command)

### 11.4 User Experience

**Usability Metrics:**
- **Single confirmation prompt:** Yes (no per-email review)
- **Clear summary report:** Yes (shows counts before deletion)
- **Excel compatibility:** Opens in Excel, Sheets, LibreOffice
- **Error messages actionable:** User knows what to do

**Measurement Method:**
- User testing with 3-5 job seekers
- Feedback survey (1-5 scale)
- Time to complete first scan
- Number of support questions

**Acceptance Criteria:**
- [ ] User can complete first scan in ≤10 minutes
- [ ] Excel file opens successfully in 3 different spreadsheet apps
- [ ] Error messages tested for clarity
- [ ] Average user satisfaction score ≥4/5

### 11.5 Key Performance Indicators (KPIs)

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| **Company extraction accuracy** | ≥70% | <50% |
| **Status classification accuracy** | ≥85% | <70% |
| **Processing speed (1000 emails)** | ≤5 seconds | >30 seconds |
| **False positive deletions** | <1% | >5% |
| **User satisfaction** | ≥4/5 | <3/5 |
| **Excel file size (1000 companies)** | <1MB | >10MB |
| **Gmail API quota usage** | <5000/day | >9000/day |

---

## 12. Testing Strategy

### 12.1 Unit Tests

**Coverage Target:** ≥80% code coverage

**Test Modules:**

**1. Extraction Module (`test_extractor.py`)**
```python
def test_extract_company_from_domain():
    """Test company extraction from email domain"""
    assert extract_company_from_domain('jobs@techcorp.com') == ('Techcorp', 'domain')
    assert extract_company_from_domain('jobs@greenhouse.io') == (None, None)

def test_extract_company_from_subject():
    """Test company extraction from subject line"""
    assert extract_company_from_subject('Application to TechCorp') == ('Techcorp', 'subject')

def test_classify_status_applied():
    """Test Applied status classification"""
    email = {'subject': 'Thank you for applying', 'body': 'We received your application'}
    status, count = classify_status(email['subject'], email['body'])
    assert status == 'Applied'
    assert count >= 2

def test_classify_status_rejected():
    """Test Rejected status classification"""
    email = {'subject': 'Application Update', 'body': 'Unfortunately, we will not be moving forward'}
    status, count = classify_status(email['subject'], email['body'])
    assert status == 'Rejected'
    assert count >= 1

def test_confidence_scoring_high():
    """Test high confidence scoring"""
    result = {
        'company': 'TechCorp',
        'company_source': 'domain',
        'position': 'Software Engineer',
        'status_matches': 2
    }
    confidence = calculate_confidence(result)
    assert confidence == 'high'

def test_confidence_scoring_low():
    """Test low confidence scoring"""
    result = {
        'company': 'Unknown',
        'company_source': None,
        'position': 'Not specified',
        'status_matches': 0
    }
    confidence = calculate_confidence(result)
    assert confidence == 'low'
```

**2. Status Hierarchy (`test_classifier.py`)**
```python
def test_status_hierarchy_upgrade_allowed():
    """Test status can move up"""
    allowed, _ = can_update_status('Applied', 'Interviewing')
    assert allowed == True

def test_status_hierarchy_downgrade_blocked():
    """Test status cannot move down"""
    allowed, _ = can_update_status('Offer', 'Rejected')
    assert allowed == False

def test_status_hierarchy_sideways_allowed():
    """Test status can move sideways (same level)"""
    allowed, _ = can_update_status('Interviewing', 'Rejected')
    assert allowed == True
    allowed, _ = can_update_status('Rejected', 'Interviewing')
    assert allowed == True
```

**3. Safety Keywords (`test_deleter.py`)**
```python
def test_safety_keyword_prevents_deletion():
    """Test safety keyword prevents deletion"""
    email = {
        'status': 'Applied',
        'subject': 'Application received',
        'body': 'We would like to schedule an interview with you'
    }
    email_text = f"{email['subject']} {email['body']}"
    should_del, reason = should_delete_email({'status': 'Applied'}, email_text, False)
    assert should_del == False
    assert 'interview' in reason.lower()

def test_applied_without_safety_keywords():
    """Test Applied email without safety keywords is deleted"""
    email = {
        'status': 'Applied',
        'subject': 'Thank you for applying',
        'body': 'We received your application and will review it'
    }
    email_text = f"{email['subject']} {email['body']}"
    should_del, reason = should_delete_email({'status': 'Applied'}, email_text, False)
    assert should_del == True
```

**4. Excel Operations (`test_excel_storage.py`)**
```python
def test_excel_create_new_row():
    """Test creating new company row"""
    # Implementation test

def test_excel_update_existing_row():
    """Test updating status for existing company"""
    # Implementation test

def test_excel_conflict_flagging():
    """Test conflict flagging when status downgrades"""
    # Implementation test

def test_excel_find_company():
    """Test finding company row (case-insensitive)"""
    # Implementation test
```

### 12.2 Integration Tests

**1. Gmail API Integration**
```python
def test_gmail_authentication(mock_service):
    """Test OAuth authentication flow"""
    # Test with mock Gmail service

def test_gmail_email_fetching(mock_service):
    """Test fetching emails with search queries"""
    # Test with mock responses

def test_gmail_email_deletion(mock_service):
    """Test moving emails to trash"""
    # Test with test Gmail account
```

**2. End-to-End Workflow**
```python
def test_full_workflow_pattern_only():
    """Test complete workflow: fetch → extract → save → delete"""
    # Use mock Gmail responses
    # Verify Excel output
    # Verify deletion calls made

def test_full_workflow_with_ai(mock_ollama):
    """Test workflow with Ollama enabled"""
    # Mock Ollama responses
    # Verify AI called for low confidence emails
```

**3. Ollama Integration (if enabled)**
```python
def test_ollama_connection():
    """Test Ollama server reachable"""
    # Skip if Ollama not running

def test_ollama_extraction(mock_ollama):
    """Test AI extraction returns valid JSON"""
    # Mock Ollama API response

def test_ollama_timeout_handling():
    """Test timeout handling (30 second limit)"""
    # Simulate slow response
```

### 12.3 Manual Testing Scenarios

**Scenario 1: First-Time User (30 minutes)**
1. User installs package
2. Runs `emailagent auth login`
3. Grants Gmail permissions
4. Runs `emailagent job scan --preview`
5. Reviews Excel file
6. Runs `emailagent job scan --confirm-delete`
7. Verifies emails deleted and Excel accurate

**Expected Result:**
- No errors during installation
- Authentication completes successfully
- Preview shows accurate summary
- Excel file opens and is readable
- Deletion confirmation clear
- Correct emails deleted

**Scenario 2: Pattern Matching Accuracy (1 hour)**
1. Use real user email samples (10 Applied, 10 Rejected)
2. Run extraction on each email
3. Manually verify:
   - Company name extracted correctly
   - Position extracted (if present)
   - Status classified correctly
   - Confidence score reasonable
4. Document false positives/negatives

**Expected Result:**
- ≥8/10 Applied emails correctly classified
- ≥8/10 Rejected emails correctly classified
- ≥15/20 company names extracted correctly

**Scenario 3: Safety Keyword Protection (30 minutes)**
1. Create test emails with safety keywords
2. Classify as "Applied"
3. Verify NOT marked for deletion
4. Test all safety keywords:
   - interview, offer, assessment, schedule, etc.

**Expected Result:**
- All safety keywords tested
- No emails with safety keywords marked for deletion
- Emails correctly kept in inbox

**Scenario 4: Conflict Handling (30 minutes)**
1. Create company with status = "Offer"
2. Receive rejection email for same company
3. Process email
4. Verify:
   - Status NOT downgraded to Rejected
   - Conflict flag (⚠️) added to Notes
   - Conflict note explains what happened
   - Email NOT deleted

**Expected Result:**
- Status remains "Offer"
- Notes contain "⚠️ Conflict: received Rejected after Offer..."
- Email kept for manual review
- Conflict logged to audit file

**Scenario 5: Undo Functionality (15 minutes)**
1. Delete batch of emails
2. Run `emailagent job undo-last`
3. Verify emails restored from trash
4. Check Gmail inbox for restored emails

**Expected Result:**
- Undo command successfully restores emails
- All emails back in inbox
- Deletion log shows undo action

### 12.4 Performance Testing

**Load Test: 10,000 Emails**
1. Create mock dataset of 10,000 emails
2. Run full processing pipeline
3. Measure:
   - Total processing time
   - Peak memory usage
   - API quota usage
   - Excel file size
4. Verify no memory leaks

**Expected Result:**
- Pattern-only: Complete in ≤60 seconds
- Hybrid (20% AI): Complete in ≤120 minutes
- Memory: <500MB (pattern), <2GB (AI)
- Excel file: <2MB

**Stress Test: Concurrent Operations**
1. Run 5 scans back-to-back
2. Verify token refresh works
3. Check file locking (Excel concurrent access)
4. Monitor for errors

**Expected Result:**
- All scans complete successfully
- Token auto-refreshes when needed
- No file corruption
- No race conditions

### 12.5 User Acceptance Testing (UAT)

**Test Users:** 3-5 job seekers with real Gmail accounts

**UAT Checklist:**
- [ ] Installation process clear and works
- [ ] Gmail authentication understandable
- [ ] First scan completes successfully
- [ ] Excel file is readable and accurate
- [ ] Deletion summary is clear
- [ ] No important emails accidentally deleted
- [ ] Error messages are helpful
- [ ] Documentation is sufficient

**UAT Survey Questions:**
1. How easy was installation? (1-5 scale)
2. Did you understand what the tool was doing? (Yes/No)
3. Do you trust the deletion decisions? (Yes/No)
4. Would you use this regularly? (Yes/No)
5. What features are missing?
6. What was confusing or unclear?

**Success Criteria:**
- ≥80% of users complete first scan successfully
- Average satisfaction score ≥4/5
- <2 critical bugs reported
- <5 documentation clarifications needed

### 12.6 Regression Testing

**Before Each Release:**
- [ ] Run full test suite (unit + integration)
- [ ] Test with real Gmail account
- [ ] Verify no existing functionality broken
- [ ] Check backward compatibility (config file format)
- [ ] Test on all supported OS (Linux, macOS, Windows)

### 12.7 Acceptance Criteria

- [ ] 80%+ unit test coverage achieved
- [ ] All integration tests pass
- [ ] Manual testing completed with real emails
- [ ] UAT completed with ≥3 users
- [ ] Performance benchmarks met
- [ ] Zero critical bugs in UAT
- [ ] Regression tests pass
- [ ] All user-provided email examples correctly processed

---

## 13. Development Phases

### Phase 1: Foundation & Setup (Week 1)

**Goals:**
- Project structure created
- Gmail API authentication working
- Basic email fetching operational
- Configuration system in place

**Tasks:**
- [ ] Create monorepo structure (`core/`, `job_tracker/`, `tests/`)
- [ ] Set up virtual environment and install dependencies
- [ ] Implement Gmail OAuth 2.0 authentication flow
- [ ] Create `core/gmail_client.py` with basic fetch operations
- [ ] Implement configuration loading (YAML + environment variables)
- [ ] Write authentication unit tests
- [ ] Create README with setup instructions
- [ ] Create SETUP.md with Gmail API setup guide

**Deliverables:**
- Working `emailagent auth login` command
- Able to fetch emails from Gmail using search queries
- `config.yaml` with defaults
- Unit tests for auth module (≥80% coverage)

**Estimated Time:** 5-7 days

---

### Phase 2: Pattern-Based Extraction (Week 2)

**Goals:**
- Pattern matching extraction fully functional
- Confidence scoring implemented
- All patterns from real user emails coded

**Tasks:**
- [ ] Implement company name extraction (domain → subject → body)
- [ ] Implement position extraction from subject/body
- [ ] Implement status classification with keyword patterns
- [ ] Code all patterns from user's real email examples
- [ ] Implement confidence scoring algorithm
- [ ] Create `job_tracker/job_patterns.py` with all regex patterns
- [ ] Write extraction unit tests (test with real email examples)
- [ ] Optimize performance (target: 1000 emails in 5 seconds)

**Deliverables:**
- `job_tracker/extractor.py` with pattern matching
- `job_tracker/job_patterns.py` with categorized patterns
- `job_tracker/classifier.py` with status classification
- Unit tests achieving ≥70% accuracy on test dataset

**Estimated Time:** 5-7 days

---

### Phase 3: Excel Storage & Status Hierarchy (Week 2-3)

**Goals:**
- Excel operations working
- Status hierarchy enforced
- Conflict detection functional

**Tasks:**
- [ ] Implement Excel file creation/loading with `openpyxl`
- [ ] Implement row creation (new company)
- [ ] Implement row updates (existing company)
- [ ] Implement status hierarchy rules (up/sideways only)
- [ ] Implement conflict detection and flagging
- [ ] Add Excel formatting (headers, colors, conditional formatting)
- [ ] Implement export functionality (CSV, JSON)
- [ ] Implement auto-backup system
- [ ] Write Excel storage unit tests

**Deliverables:**
- `job_tracker/excel_storage.py` with all operations
- Excel file with proper formatting
- Export to CSV/JSON working
- Backup system functional

**Estimated Time:** 7-10 days

---

### Phase 4: Deletion Logic (Week 3-4)

**Goals:**
- Safe deletion rules implemented
- Safety keywords working
- Batch processing with confirmation

**Tasks:**
- [ ] Implement deletion rules (Applied, Rejected only)
- [ ] Implement safety keyword checking (all keywords tested)
- [ ] Implement batch deletion with progress indicator
- [ ] Implement summary report generation
- [ ] Implement user confirmation prompt
- [ ] Implement deletion logging to audit file
- [ ] Implement undo functionality (restore from trash)
- [ ] Write deletion unit tests

**Deliverables:**
- `core/deleter.py` with safe deletion logic
- Summary report formatter
- Deletion log files with timestamps
- `undo-last` command functional

**Estimated Time:** 5-7 days

---

### Phase 5: CLI & Integration (Week 4-5)

**Goals:**
- All CLI commands working
- End-to-end workflow functional
- Error handling comprehensive

**Tasks:**
- [ ] Implement CLI structure with Click or Typer
- [ ] Implement `emailagent auth` commands (login, logout, status)
- [ ] Implement `emailagent job scan` with all options
- [ ] Implement `emailagent job list/show/update`
- [ ] Implement `emailagent job export/stats/undo-last`
- [ ] Implement progress indicators using Rich library
- [ ] Implement comprehensive error handling for all failure modes
- [ ] Add logging throughout application
- [ ] Write integration tests (end-to-end workflow)

**Deliverables:**
- `cli.py` with all commands
- Comprehensive error messages
- Progress indicators (progress bars, spinners)
- Integration test suite passing

**Estimated Time:** 7-10 days

---

### Phase 6: Optional AI Integration (Week 5-6)

**Goals:**
- Ollama integration working
- Hybrid workflow (pattern → AI fallback) functional
- AI response parsing robust

**Tasks:**
- [ ] Implement Ollama client wrapper
- [ ] Implement AI prompt templates
- [ ] Implement JSON response parsing (handle errors)
- [ ] Implement AI fallback logic (triggered by low confidence)
- [ ] Handle AI timeouts and connection errors gracefully
- [ ] Add `--use-ai` flag to CLI
- [ ] Test with Ollama locally
- [ ] Write AI integration tests (mock Ollama responses)
- [ ] Document Ollama setup for users

**Deliverables:**
- `job_tracker/ollama_client.py` with AI wrapper
- Hybrid extraction workflow (pattern + AI)
- AI timeout handling (30s limit)
- Optional dependency documentation

**Estimated Time:** 5-7 days

---

### Phase 7: Polish & Documentation (Week 6-7)

**Goals:**
- Production-ready quality
- Comprehensive documentation
- Ready for user testing

**Tasks:**
- [ ] Comprehensive error handling review
- [ ] Add user-friendly error messages
- [ ] Write installation guide (INSTALL.md)
- [ ] Write Gmail API setup guide (SETUP.md)
- [ ] Create example configuration files
- [ ] Write user guide with screenshots (USER_GUIDE.md)
- [ ] Create troubleshooting guide (TROUBLESHOOTING.md)
- [ ] Code cleanup and formatting (black, mypy)
- [ ] Final testing with real Gmail account (1000+ emails)
- [ ] Create demo video (optional)

**Deliverables:**
- README.md (comprehensive)
- SETUP.md (Gmail API setup)
- USER_GUIDE.md (CLI usage)
- TROUBLESHOOTING.md (common issues)
- Example config files
- All code formatted and type-checked

**Estimated Time:** 7-10 days

---

### Phase 8: User Acceptance Testing (Week 7-8)

**Goals:**
- Real users test the system
- Bugs identified and fixed
- User feedback incorporated

**Tasks:**
- [ ] Recruit 3-5 test users (job seekers with Gmail)
- [ ] Guide users through installation
- [ ] Observe first scan process
- [ ] Collect feedback via survey
- [ ] Fix critical bugs discovered
- [ ] Iterate on UI/UX issues
- [ ] Update documentation based on feedback
- [ ] Perform final regression testing

**Deliverables:**
- UAT report with user feedback
- Critical bugs fixed
- Updated documentation
- Release candidate ready

**Estimated Time:** 7-10 days

---

**Total Estimated Development Time:** 6-8 weeks

---

## 14. Risk Mitigation & Future Enhancements

### 14.1 Technical Risks

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|---------------------|
| **Gmail API rate limits exceeded** | High | Medium | • Batch operations (100 emails/request)<br>• Exponential backoff on 429 errors<br>• Respect 250 quota units/sec limit<br>• Cache results where possible<br>• Show quota usage to user |
| **OAuth token expiration** | High | Low | • Implement automatic token refresh<br>• Clear error messages when token expires<br>• Graceful re-authentication flow<br>• Store refresh token securely |
| **Pattern matching misclassification** | Medium | Medium | • Optional AI fallback (Ollama)<br>• Confidence scoring<br>• "Needs Review" flagging<br>• Safety keywords prevent worst cases<br>• User can manually correct in Excel |
| **Excel file corruption** | High | Low | • Auto-backup before each scan<br>• Validate writes with openpyxl<br>• Save incrementally (every 100 emails)<br>• Keep 7 days of backups<br>• Use robust library (openpyxl) |
| **Ollama unavailable/crashes** | Low | Medium | • Make AI optional (graceful degradation)<br>• Timeout after 30 seconds<br>• Continue with pattern-only if AI fails<br>• Clear error messages<br>• Test without Ollama |
| **Large dataset performance** | Medium | Medium | • Process in batches of 100<br>• Save Excel incrementally<br>• Profile and optimize hotspots<br>• Test with 10K+ emails<br>• Streaming where possible |

### 14.2 User Experience Risks

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|---------------------|
| **User accidentally confirms deletion** | High | Medium | • Clear summary before confirmation<br>• Trash (not permanent delete)<br>• 30-day recovery window<br>• Undo command available<br>• Deletion log for reference<br>• Preview mode option |
| **User doesn't understand hierarchy** | Low | High | • Clear documentation with examples<br>• Example scenarios in user guide<br>• Conflict flags with explanations<br>• Status transition diagram<br>• Help command with examples |
| **User confused by "Needs Review"** | Low | Medium | • Clear note in Excel<br>• Guidance in USER_GUIDE.md<br>• Option to re-run with AI<br>• Suggest manual review workflow |
| **Installation too complex** | Medium | High | • Detailed SETUP.md with screenshots<br>• Pre-check script for dependencies<br>• Common error messages documented<br>• Video tutorial (optional)<br>• One-line install script (future) |

### 14.3 Data Safety Risks

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|---------------------|
| **Accidental deletion of important emails** | Critical | Low | • Safety keywords prevent deletion<br>• Interviewing/Offer never deleted<br>• Conflict emails never deleted<br>• Trash (30-day recovery)<br>• Undo command<br>• Deletion log audit trail |
| **Status conflict not detected** | Medium | Low | • Strict hierarchy enforcement<br>• All conflicts flagged with ⚠️<br>• Conflict detection tested thoroughly<br>• Never silently downgrade<br>• Log all conflicts |
| **Excel data loss** | High | Low | • Auto-backup before each scan<br>• Save after every 100 emails<br>• 7-day backup retention<br>• Validate writes<br>• Test file integrity |
| **Privacy concerns (email content)** | Medium | Low | • All processing local (no cloud)<br>• Ollama runs locally (not API)<br>• No data sent to third parties<br>• OAuth scopes minimal (read + trash)<br>• Clear privacy policy in docs |

### 14.4 Future Enhancements (Post-MVP)

#### Priority 1: Feature 1 - General Email Cleanup Agent

**Scope:**
- Pattern-based deletion for promotional, newsletters, spam
- Category-based deletion rules
- Deletion count logging (no per-email tracking)
- **Separate PRD** to be created after Feature 2 validation

**Timeline:** 4-6 weeks after Feature 2 launch

**Why Separate:**
- Different patterns/rules than job emails
- Want to validate core architecture first
- User wants to test Feature 2 thoroughly first

#### Priority 2: Web Dashboard

**Features:**
- Visual job application tracking
- Charts (funnel, response rates over time)
- Calendar view for interview dates
- Quick filters and search
- Export functionality

**Tech Stack:** React + Flask/FastAPI backend

**Timeline:** 3-4 months after Feature 2

#### Priority 3: Enhanced Features

**Email Management:**
- Email response templates (thank you, follow-up)
- Auto-reply for certain scenarios
- Email sending capabilities
- Attachment handling

**Integrations:**
- Calendar integration (Google Calendar, Outlook)
- Job board sync (LinkedIn, Indeed API)
- Slack/Discord notifications
- Mobile app notifications

**AI Enhancements:**
- Company research (auto-fetch company info)
- Salary estimation
- AI-powered insights ("Company X typically responds in 5 days")
- Automated follow-up suggestions

**Multi-Account:**
- Support multiple Gmail accounts
- Switch between accounts
- Consolidated view

**Real-Time:**
- Gmail webhook integration
- Real-time monitoring (no manual scans)
- Instant notifications

#### Priority 4: Advanced Analytics

**Statistics Dashboard:**
- Application funnel (Applied → Interview → Offer)
- Response rates by company
- Time-to-response analysis
- Success factors analysis
- Industry/role comparisons

**Predictive Analytics:**
- Likelihood of getting interview
- Best time to follow up
- Salary negotiation insights

### 14.5 Known Limitations (MVP)

**Accepted Limitations:**
1. **One position per company** - Can't track multiple positions at same company separately
2. **Pattern-only 70-80% accurate** - User must enable AI for higher accuracy
3. **English only** - Patterns designed for English emails
4. **CLI only** - No GUI for MVP
5. **Single account** - Can't switch between Gmail accounts
6. **Manual execution** - No automatic scheduling/cron

**Future Improvements:**
- Track multiple positions per company
- Multi-language support
- GUI interface
- Multi-account support
- Automatic scheduled scans

### 14.6 Success Criteria (Launch Decision)

**Must Have (Launch Blockers):**
- [ ] All 10 user-provided emails correctly processed
- [ ] Zero accidental deletion of Interviewing/Offer emails in testing
- [ ] Excel file opens in Excel, Sheets, LibreOffice
- [ ] Undo command successfully restores emails
- [ ] ≥3 UAT users complete first scan successfully
- [ ] Zero critical bugs in UAT

**Should Have (Launch Goals):**
- [ ] Pattern-only ≥70% company extraction accuracy
- [ ] ≥85% status classification accuracy
- [ ] Process 1000 emails in ≤5 seconds
- [ ] User satisfaction ≥4/5
- [ ] Comprehensive documentation

**Nice to Have (Post-Launch):**
- [ ] AI integration fully tested and documented
- [ ] Video tutorial created
- [ ] Published to PyPI
- [ ] Community feedback gathered

---

## 15. Appendix

### 15.1 Glossary

**Applied** - Status for confirmation emails received immediately after submitting application

**Rejected** - Status for emails explicitly stating application was not successful

**Interviewing** - Status for emails requesting interview, phone screen, or assessment

**Offer** - Status for emails extending job offer

**Conflict** - Situation where new email would downgrade status (e.g., Offer → Rejected)

**Safety Keywords** - Keywords that prevent email deletion (interview, offer, schedule, etc.)

**Pattern Matching** - Regex-based extraction method (fast, free, 70-80% accurate)

**Hybrid Mode** - Pattern matching + AI fallback (slower, free, 90%+ accurate)

**Confidence Score** - Measure of extraction accuracy (high, medium, low)

**Status Hierarchy** - Rule that status can move up or sideways, never down

**Trash** - Gmail folder where deleted emails go (30-day recovery before permanent deletion)

### 15.2 References

**Gmail API Documentation:**
- https://developers.google.com/gmail/api
- https://developers.google.com/gmail/api/quickstart/python

**Ollama Documentation:**
- https://ollama.com
- https://github.com/ollama/ollama

**Python Libraries:**
- openpyxl: https://openpyxl.readthedocs.io
- Click: https://click.palletsprojects.com
- Rich: https://rich.readthedocs.io

### 15.3 Contact & Support

**For Users:**
- Documentation: README.md, USER_GUIDE.md, TROUBLESHOOTING.md
- Issues: GitHub Issues (future)
- Discussions: GitHub Discussions (future)

**For Developers:**
- Contributing: CONTRIBUTING.md (future)
- Code Style: black + mypy
- Testing: pytest

### 15.4 License

**Recommendation:** MIT License (permissive, allows commercial use)

### 15.5 Changelog

**v1.0.0 (Target: March 2026)**
- Initial release
- Pattern-based extraction
- Optional AI extraction (Ollama)
- Excel storage with status hierarchy
- Selective deletion (Applied/Rejected only)
- CLI interface
- Comprehensive documentation

**v1.1.0 (Target: April 2026)**
- Bug fixes from user feedback
- Performance improvements
- Additional safety keywords
- Enhanced error messages

**v2.0.0 (Target: Q2 2026)**
- Feature 1: General email cleanup
- Web dashboard (optional)
- Multi-account support (optional)

---

## Document Complete

This concludes the comprehensive Product Requirements Document for the Job Email Tracker (Feature 2).

**Total Document Pages:** ~150+ pages across 4 parts

**Key Sections:**
1. Executive Summary & Scope
2. System Architecture
3. Functional Requirements (detailed)
4. Real Email Patterns (from user examples)
5. CLI Specification (complete)
6. Configuration (full YAML)
7. Dependencies & Installation
8. Success Metrics
9. Testing Strategy (comprehensive)
10. Development Phases (8-week timeline)
11. Risk Mitigation
12. Future Enhancements

**Ready for:**
- Development team to start implementation
- Claude Code to build the system
- Stakeholder review
- User validation

**Next Steps:**
1. Review PRD with stakeholders
2. Set up development environment
3. Begin Phase 1: Foundation & Setup
4. Create GitHub repository (if open source)
5. Start building according to development phases

---

**END OF PRODUCT REQUIREMENTS DOCUMENT**