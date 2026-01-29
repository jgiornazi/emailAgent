# Confidence Scoring

## Methodology

The extraction pipeline uses a **weighted scoring model** to assess how reliable each email extraction result is. A weighted scoring model assigns a predetermined weight to each evaluation criterion based on its relative importance, sums the individual scores, and maps the composite to a categorical confidence level.

This approach is used because the extraction draws from multiple independent signals (company, position, status), each with different reliability characteristics. The composite score reflects overall extraction quality rather than any single dimension.

## Score Components

The score is a float from 0.0 to 1.1, built from three weighted components:

### Company Extraction (up to 50%)

| Condition | Points |
|-----------|--------|
| Company name extracted (not "Unknown") | +0.40 |
| Extracted from email domain (most reliable source) | +0.10 bonus |

The domain bonus exists because domain-based extraction (`jobs@techcorp.com` -> "Techcorp") is the most reliable method. Other sources (subject line patterns, body patterns, sender local part) are more prone to false matches.

### Position Extraction (20%)

| Condition | Points |
|-----------|--------|
| Job title extracted (not "Not specified") | +0.20 |

Position carries less weight because many legitimate job emails don't include a specific title, and its absence doesn't indicate a bad extraction.

### Status Classification (up to 40%)

| Condition | Points |
|-----------|--------|
| 3+ status keyword patterns matched | +0.40 |
| 2 patterns matched | +0.30 |
| 1 pattern matched | +0.20 |
| No patterns matched | +0.00 |

More pattern matches indicate a clearer signal. A rejection email that matches "not moving forward", "unfortunately", and "wish you success" (3 patterns) is more confidently classified than one matching only a single phrase.

## Confidence Levels

The composite score maps to three categorical levels:

| Score Range | Level | Meaning |
|-------------|-------|---------|
| >= 0.70 | **high** | All key fields extracted with strong signals |
| 0.40 - 0.69 | **medium** | Partial extraction, reasonable confidence |
| < 0.40 | **low** | Missing fields or weak signals; AI fallback triggered if enabled |

## Examples

**High confidence (score: 1.1)**
- Company from domain: +0.50
- Position from subject: +0.20
- Status with 3+ matches: +0.40

**Medium confidence (score: 0.60)**
- Company from subject: +0.40
- No position found: +0.00
- Status with 1 match: +0.20

**Low confidence (score: 0.20)**
- Company unknown: +0.00
- No position found: +0.00
- Status with 1 match: +0.20

## AI Fallback Trigger

When Ollama is enabled, low-confidence results automatically trigger AI-powered extraction as a fallback. The AI fallback is triggered when any of the following conditions are met:

- Confidence level is `low`
- Company is "Unknown"
- Status is "Applied" with fewer than 2 pattern matches (uncertain default)

## Source Code

- Scoring logic: `job_tracker/extractor.py` — `calculate_confidence()`
- AI fallback decision: `job_tracker/extractor.py` — `should_use_ai()`
- Status patterns: `job_tracker/job_patterns.py` — `STATUS_PATTERNS`
