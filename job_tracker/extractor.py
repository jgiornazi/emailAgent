"""
Email Information Extractor

This module handles extraction of job application information from emails:
- Company name extraction (from domain, subject, body)
- Position/job title extraction
- Integration with optional AI fallback (Ollama)

The extraction follows a priority order:
1. Domain extraction (most reliable)
2. Subject line patterns
3. Body text patterns
4. AI fallback (if enabled and low confidence)
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List

from .job_patterns import (
    GENERIC_PROVIDERS,
    COMPILED_SUBJECT_COMPANY_PATTERNS,
    COMPILED_BODY_COMPANY_PATTERNS,
    COMPILED_POSITION_PATTERNS,
    POSITION_KEYWORDS,
    COMPANY_CLEANUP_PATTERNS,
    POSITION_CLEANUP_PATTERNS,
)


@dataclass
class ExtractionResult:
    """Result of extracting information from an email."""

    # Core extracted fields
    company: str = "Unknown"
    position: str = "Not specified"
    status: str = "Applied"

    # Extraction metadata
    company_source: Optional[str] = None  # 'domain', 'subject', 'body', 'ai'
    position_source: Optional[str] = None  # 'subject', 'body', 'ai'
    status_matches: int = 0

    # Confidence scoring
    confidence: str = "low"  # 'high', 'medium', 'low'
    confidence_score: float = 0.0

    # Extraction method tracking
    extraction_method: str = "pattern"  # 'pattern', 'ai', 'ai_failed'

    # Email reference
    email_id: str = ""
    email_date: Optional[datetime] = None

    # Additional metadata
    matched_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'company': self.company,
            'position': self.position,
            'status': self.status,
            'company_source': self.company_source,
            'position_source': self.position_source,
            'status_matches': self.status_matches,
            'confidence': self.confidence,
            'confidence_score': self.confidence_score,
            'extraction_method': self.extraction_method,
            'email_id': self.email_id,
            'email_date': self.email_date.isoformat() if self.email_date else None,
            'matched_patterns': self.matched_patterns,
        }


def clean_text(text: str, cleanup_patterns: List[tuple]) -> str:
    """Apply cleanup patterns to text."""
    result = text.strip()
    for pattern, replacement in cleanup_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result.strip()


def extract_company_from_domain(email_address: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract company name from email domain.

    This is the most reliable method as companies typically use their
    own domain for recruiting emails.

    Args:
        email_address: The sender's email address (From field)

    Returns:
        Tuple of (company_name, source) or (None, None) if not extractable

    Examples:
        jobs@techcorp.com -> ("Techcorp", "domain")
        recruiting@perplexity.ai -> ("Perplexity", "domain")
        noreply@greenhouse.io -> (None, None)  # Generic provider
    """
    if not email_address:
        return None, None

    # Extract domain from email address
    # Handle formats like "John Doe <john@company.com>" or "john@company.com"
    email_match = re.search(r'[\w.-]+@([\w.-]+)', email_address)
    if not email_match:
        return None, None

    full_domain = email_match.group(1).lower()

    # Get the main domain part (before TLD)
    # e.g., "jobs.techcorp.com" -> "techcorp"
    # e.g., "perplexity.ai" -> "perplexity"
    domain_parts = full_domain.split('.')

    # Try to find the company name in domain parts
    company_domain = None

    # Check each part (skip TLDs like .com, .io, .ai, .org)
    for part in domain_parts[:-1]:  # Skip last part (TLD)
        # Skip generic subdomains
        if part in ['www', 'mail', 'email', 'jobs', 'careers', 'recruiting', 'apply', 'hr']:
            continue
        # Skip if it's a generic provider
        if part.lower() in GENERIC_PROVIDERS:
            return None, None
        # Found a potential company name
        company_domain = part
        break

    # If we only found a generic provider, return None
    if not company_domain:
        # Last check: the second-to-last part might be the company
        if len(domain_parts) >= 2:
            potential = domain_parts[-2]
            if potential.lower() not in GENERIC_PROVIDERS:
                company_domain = potential

    if not company_domain:
        return None, None

    # Clean and format company name
    company = company_domain.replace('-', ' ').replace('_', ' ')
    company = re.sub(r'\b(corp|inc|llc|ltd|co)\b', '', company, flags=re.IGNORECASE)
    company = company.strip().title()

    if company and len(company) >= 2:
        return company, 'domain'

    return None, None


def extract_company_from_subject(subject: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract company name from email subject line.

    Uses predefined patterns to match common subject formats.

    Args:
        subject: The email subject line

    Returns:
        Tuple of (company_name, source) or (None, None) if not found
    """
    if not subject:
        return None, None

    for pattern in COMPILED_SUBJECT_COMPANY_PATTERNS:
        match = pattern.search(subject)
        if match:
            company = match.group(1).strip()

            # Clean up the company name
            company = clean_text(company, COMPANY_CLEANUP_PATTERNS)

            # Validate: reasonable length and not just generic words
            if company and 2 <= len(company) <= 50:
                # Check it's not a generic phrase
                generic_phrases = [
                    'your application', 'application received', 'thank you',
                    'application update', 'important information', 'follow up'
                ]
                if company.lower() not in generic_phrases:
                    return company.title(), 'subject'

    return None, None


def extract_company_from_body(body: str, max_length: int = 500) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract company name from email body.

    Only searches the first portion of the body for efficiency.

    Args:
        body: The email body text
        max_length: Maximum characters to search (default 500)

    Returns:
        Tuple of (company_name, source) or (None, None) if not found
    """
    if not body:
        return None, None

    snippet = body[:max_length]

    for pattern in COMPILED_BODY_COMPANY_PATTERNS:
        match = pattern.search(snippet)
        if match:
            company = match.group(1).strip()

            # Clean up the company name
            company = clean_text(company, COMPANY_CLEANUP_PATTERNS)

            # Validate: reasonable length
            if company and 2 <= len(company) <= 50:
                # Check it's not a generic phrase
                generic_phrases = [
                    'us', 'our team', 'the team', 'our company',
                    'this position', 'the role', 'your application'
                ]
                if company.lower() not in generic_phrases:
                    return company.title(), 'body'

    return None, None


def extract_company(email: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    Extract company name from email using all available methods.

    Tries extraction in priority order:
    1. Email domain (most reliable)
    2. Subject line patterns
    3. Body text patterns

    Args:
        email: Email dictionary with 'from', 'subject', 'body' keys

    Returns:
        Tuple of (company_name, source) where source is the extraction method used
    """
    # Try domain first (most reliable)
    company, source = extract_company_from_domain(email.get('from', ''))
    if company:
        return company, source

    # Try subject
    company, source = extract_company_from_subject(email.get('subject', ''))
    if company:
        return company, source

    # Try body
    company, source = extract_company_from_body(email.get('body', ''))
    if company:
        return company, source

    # Failed to extract
    return 'Unknown', None


def extract_position_from_subject(subject: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract job position/title from email subject.

    Args:
        subject: The email subject line

    Returns:
        Tuple of (position, source) or (None, None) if not found
    """
    if not subject:
        return None, None

    # Try each pattern
    for pattern in COMPILED_POSITION_PATTERNS[:4]:  # First 4 are subject patterns
        match = pattern.search(subject)
        if match:
            position = match.group(1).strip()

            # Clean up
            position = clean_text(position, POSITION_CLEANUP_PATTERNS)

            # Validate: must contain a position keyword and reasonable length
            if position and 5 <= len(position) <= 60:
                if any(keyword in position.lower() for keyword in POSITION_KEYWORDS):
                    # Remove any trailing company name indicators
                    if ' at ' in position.lower():
                        position = position.split(' at ')[0].strip()
                    return position.title(), 'subject'

    return None, None


def extract_position_from_body(body: str, max_length: int = 500) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract job position/title from email body.

    Args:
        body: The email body text
        max_length: Maximum characters to search

    Returns:
        Tuple of (position, source) or (None, None) if not found
    """
    if not body:
        return None, None

    snippet = body[:max_length]

    # Try body-specific patterns
    for pattern in COMPILED_POSITION_PATTERNS[4:]:  # Patterns 4+ are for body
        match = pattern.search(snippet)
        if match:
            position = match.group(1).strip()

            # Clean up
            position = clean_text(position, POSITION_CLEANUP_PATTERNS)

            # Validate
            if position and 5 <= len(position) <= 60:
                if any(keyword in position.lower() for keyword in POSITION_KEYWORDS):
                    return position.title(), 'body'

    return None, None


def extract_position(subject: str, body: str) -> Tuple[str, Optional[str]]:
    """
    Extract job position/title from email.

    Tries subject first (more reliable), then body.

    Args:
        subject: Email subject line
        body: Email body text

    Returns:
        Tuple of (position, source)
    """
    # Try subject first (most reliable)
    position, source = extract_position_from_subject(subject)
    if position:
        return position, source

    # Try body
    position, source = extract_position_from_body(body)
    if position:
        return position, source

    return "Not specified", None


def calculate_confidence(extraction_result: ExtractionResult) -> Tuple[str, float]:
    """
    Calculate confidence score for extraction result.

    Scoring breakdown:
    - Company extraction: 40% of score
      - From domain: +10% bonus (most reliable)
    - Position extraction: 20% of score
    - Status classification: 40% of score
      - Multiple keyword matches: higher confidence

    Args:
        extraction_result: The extraction result to score

    Returns:
        Tuple of (confidence_level, score) where level is 'high', 'medium', or 'low'
    """
    score = 0.0

    # Company extraction (40% of score)
    if extraction_result.company != 'Unknown':
        score += 0.4
        # Bonus for domain extraction (most reliable)
        if extraction_result.company_source == 'domain':
            score += 0.1

    # Position extraction (20% of score)
    if extraction_result.position != 'Not specified':
        score += 0.2

    # Status classification (40% of score)
    status_matches = extraction_result.status_matches
    if status_matches >= 3:
        score += 0.4  # Multiple strong matches
    elif status_matches >= 2:
        score += 0.3  # Good match
    elif status_matches == 1:
        score += 0.2  # Single match

    # Determine confidence level
    if score >= 0.7:
        confidence = 'high'
    elif score >= 0.4:
        confidence = 'medium'
    else:
        confidence = 'low'

    return confidence, round(score, 2)


def pattern_match_extraction(email: Dict[str, Any]) -> ExtractionResult:
    """
    Perform pattern-based extraction on an email.

    This is the primary extraction method, using regex patterns
    to extract company, position, and classify status.

    Args:
        email: Email dictionary with keys:
            - 'id': Gmail message ID
            - 'subject': Email subject
            - 'from': Sender email address
            - 'body': Email body text
            - 'snippet': Short preview (optional)
            - 'date': Email date (optional)

    Returns:
        ExtractionResult with all extracted information
    """
    result = ExtractionResult()
    result.email_id = email.get('id', '')
    result.email_date = email.get('date')
    result.extraction_method = 'pattern'

    # Extract company
    company, company_source = extract_company(email)
    result.company = company
    result.company_source = company_source

    # Extract position
    position, position_source = extract_position(
        email.get('subject', ''),
        email.get('body', email.get('snippet', ''))
    )
    result.position = position
    result.position_source = position_source

    # Status classification will be done by classifier module
    # For now, set defaults that will be updated
    result.status = 'Applied'
    result.status_matches = 0

    return result


def should_use_ai(pattern_result: ExtractionResult, use_ai_enabled: bool) -> bool:
    """
    Determine if AI extraction should be attempted.

    AI fallback is triggered when:
    - use_ai is enabled in config
    - Pattern confidence is low
    - Company could not be extracted
    - Status is uncertain

    Args:
        pattern_result: Result from pattern matching
        use_ai_enabled: Whether AI is enabled in config

    Returns:
        True if AI should be attempted
    """
    if not use_ai_enabled:
        return False

    # Trigger AI for low confidence results
    if pattern_result.confidence == 'low':
        return True

    # Trigger AI for unknown companies
    if pattern_result.company == 'Unknown':
        return True

    # Trigger AI for uncertain status (few matches)
    if pattern_result.status == 'Applied' and pattern_result.status_matches < 2:
        return True

    return False


def extract_email_info(email: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> ExtractionResult:
    """
    Complete extraction pipeline for an email.

    This is the main entry point for email extraction. It:
    1. Always tries pattern matching first (fast, free)
    2. Optionally uses AI fallback if enabled and needed
    3. Returns complete extraction result with confidence scoring

    Args:
        email: Email dictionary with 'id', 'subject', 'from', 'body', 'date'
        config: Configuration dictionary with 'use_ai' flag

    Returns:
        ExtractionResult with all extracted information

    Note:
        Status classification is handled by the classifier module.
        This function should be called first, then pass the result
        to the classifier for status determination.
    """
    config = config or {}

    # Step 1: Always try pattern matching first
    result = pattern_match_extraction(email)

    # Step 2: Calculate initial confidence
    confidence, score = calculate_confidence(result)
    result.confidence = confidence
    result.confidence_score = score

    # Step 3: Check if we should use AI (implemented in ollama_client module)
    # AI integration will be added in Phase 6
    # For now, just return pattern result

    return result
