# EmailAgent - Job Application Tracker

Automated job application tracker that scans Gmail for job-related emails, extracts company and status information, and helps you manage your job search.

## Features

- **Gmail Integration**: Scans your inbox for job-related emails
- **Smart Extraction**: Extracts company name, position, and application status
- **Pattern Matching**: Fast, free extraction (70-80% accuracy)
- **Optional AI**: Ollama integration for higher accuracy (90%+)
- **Excel Export**: Stores all data in `job_applications.xlsx`
- **Safe Deletion**: Removes Applied/Rejected emails after extraction
- **Status Tracking**: Applied → Interviewing → Offer progression
- **Conflict Detection**: Flags unusual status changes

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/your-username/emailagent.git
cd emailagent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Set up Gmail API (see SETUP.md)

# 3. Authenticate
emailagent auth login

# 4. Scan your inbox
emailagent job scan --preview  # Preview first
emailagent job scan            # Run with deletion
```

## Installation

### Prerequisites

- Python 3.11+
- Gmail account
- Google Cloud project with Gmail API enabled

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Gmail API Setup

See [SETUP.md](SETUP.md) for detailed Gmail API configuration instructions.

## Usage

### Authentication

```bash
# Login with Gmail
emailagent auth login

# Check status
emailagent auth status

# Logout
emailagent auth logout
```

### Job Tracking

```bash
# Scan for job emails (preview mode)
emailagent job scan --preview

# Scan and delete
emailagent job scan

# Scan with AI for better accuracy
emailagent job scan --use-ai

# Scan recent emails only
emailagent job scan --since 2026-01-01

# List all applications
emailagent job list

# Filter by status
emailagent job list --status Interviewing

# Show detailed info
emailagent job show "TechCorp"

# Export to CSV
emailagent job export --format csv --output applications.csv

# View statistics
emailagent job stats

# Undo last deletion
emailagent job undo-last
```

### Configuration

```bash
# Edit config
emailagent config

# Show current config
emailagent config show

# Validate config
emailagent config validate
```

## How It Works

### Email Detection

Searches Gmail using queries like:
- `subject:(application OR applied OR "thank you for applying")`
- `subject:(interview OR "phone screen" OR "next steps")`
- `subject:(offer OR "job offer")`
- `subject:(rejection OR "not moving forward")`

### Status Classification

| Status | Description | Action |
|--------|-------------|--------|
| **Applied** | Confirmation emails | Deleted after extraction |
| **Interviewing** | Interview requests | Always kept |
| **Rejected** | Rejection emails | Deleted after extraction |
| **Offer** | Job offers | Always kept |

### Status Hierarchy

```
Applied (Level 0)
    ↓
Interviewing (Level 1) ↔ Rejected (Level 1)
    ↓
Offer (Level 2)
```

Status can move UP or SIDEWAYS, never DOWN. Conflicts are flagged.

### Safety Features

- **Safety Keywords**: Emails containing "interview", "offer", "schedule", etc. are never deleted
- **Conflict Detection**: Unusual status changes are flagged for review
- **Trash Only**: Emails go to Trash (30-day recovery), not permanent delete
- **Undo Command**: Restore last batch of deletions

## Configuration

Configuration file: `~/.emailagent/config.yaml`

Key settings:

```yaml
extraction:
  use_ai: false  # Enable for higher accuracy

deletion:
  delete_applied: true
  delete_rejected: true
  delete_interviewing: false  # Always false
  delete_offer: false         # Always false

excel:
  file_path: ~/job_applications.xlsx
```

See [config.yaml](config.yaml) for full options.

## Optional: AI Extraction

For higher accuracy, enable Ollama integration:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download model
ollama pull llama3.2:3b

# Enable in config
# extraction:
#   use_ai: true

# Or use flag
emailagent job scan --use-ai
```

## Project Structure

```
emailagent/
├── core/               # Shared components
│   ├── gmail_client.py # Gmail API wrapper
│   ├── auth.py         # OAuth authentication
│   ├── deleter.py      # Deletion operations
│   ├── logger.py       # Logging
│   └── config.py       # Configuration
├── job_tracker/        # Job tracking (Feature 2)
│   ├── extractor.py    # Company/status extraction
│   ├── excel_storage.py# Excel operations
│   ├── job_patterns.py # Regex patterns
│   └── classifier.py   # Status classification
├── bulk_cleaner/       # General cleanup (Future)
├── cli.py              # CLI entry point
└── tests/              # Test suite
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Issues: [GitHub Issues](https://github.com/your-username/emailagent/issues)
- Documentation: [docs/](docs/)
