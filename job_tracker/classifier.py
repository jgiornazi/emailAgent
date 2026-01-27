"""
Status Classifier Module

This module handles classification of email status and enforces
the status hierarchy rules:

Status Hierarchy:
    Applied (Level 0) -> Interviewing/Rejected (Level 1) -> Offer (Level 2)

Rules:
- Status can move UP or SIDEWAYS, never DOWN
- Conflicts are flagged when downgrade would occur
- All status transitions are logged

Statuses:
- Applied: Confirmation emails after submitting application
- Interviewing: Interview requests, phone screens, assessments
- Rejected: Application was not successful
- Offer: Job offer extended
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, List, Dict, Optional, Any

from .job_patterns import (
    STATUS_HIERARCHY,
    COMPILED_STATUS_PATTERNS,
)
from .extractor import ExtractionResult, calculate_confidence


@dataclass
class StatusClassificationResult:
    """Result of classifying an email's status."""

    status: str
    match_count: int
    matched_patterns: List[str]
    confidence: str


@dataclass
class StatusUpdateResult:
    """Result of attempting to update a status."""

    allowed: bool
    reason: str
    is_conflict: bool = False
    kept_status: Optional[str] = None
    attempted_status: Optional[str] = None


def classify_status(subject: str, body: str) -> Tuple[str, int, List[str]]:
    """
    Classify email status using pattern matching.

    Checks patterns in priority order:
    1. Rejected (most distinctive patterns)
    2. Offer (strong positive indicators)
    3. Interviewing (action-oriented patterns)
    4. Applied (generic confirmation patterns)

    Special handling:
    - Rejection phrases like "not move forward" take precedence over "interview" keyword
    - When rejection patterns match strongly, ignore incidental "interview" mentions

    Args:
        subject: Email subject line
        body: Email body text

    Returns:
        Tuple of (status, match_count, matched_patterns)
    """
    import re

    # Combine text for analysis
    text = f"{subject} {body}".lower()

    # Track matches for each status
    status_scores: Dict[str, int] = {status: 0 for status in STATUS_HIERARCHY}
    matched_patterns: Dict[str, List[str]] = {status: [] for status in STATUS_HIERARCHY}

    # Check patterns in priority order
    # Priority: Rejected > Offer > Interviewing > Applied
    # (Rejected first because it's most distinctive, Applied last because it's most generic)
    check_order = ['Rejected', 'Offer', 'Interviewing', 'Applied']

    for status in check_order:
        patterns = COMPILED_STATUS_PATTERNS.get(status, [])
        for pattern in patterns:
            if pattern.search(text):
                status_scores[status] += 1
                matched_patterns[status].append(pattern.pattern)

    # Special handling: Check for strong rejection indicators
    # These phrases definitively indicate rejection even if "interview" appears
    strong_rejection_phrases = [
        r'not moving forward',
        r"won'?t be advancing",
        r'will not be moving forward',
        r'not move forward',
        r'unfortunately.*not',
        r'decided to not move forward',
        r'we are not moving forward',
        r'wish you.*success.*job search',
        r'best of luck.*job search',
    ]

    has_strong_rejection = False
    for phrase in strong_rejection_phrases:
        if re.search(phrase, text, re.IGNORECASE):
            has_strong_rejection = True
            break

    # If strong rejection phrase found and Rejected has matches,
    # prioritize Rejected over Interviewing
    if has_strong_rejection and status_scores['Rejected'] >= 1:
        return 'Rejected', status_scores['Rejected'], matched_patterns['Rejected']

    # Determine best status
    # If multiple statuses have matches, use priority order with tie-breaking
    best_status = 'Applied'  # Default fallback
    best_score = 0

    # Check in reverse priority (so higher priority wins ties)
    for status in reversed(check_order):
        score = status_scores[status]
        if score > best_score:
            best_score = score
            best_status = status
        elif score == best_score and score > 0:
            # Tie: prefer higher priority status
            # Priority order: Rejected > Offer > Interviewing > Applied
            priority_order = ['Applied', 'Interviewing', 'Offer', 'Rejected']
            if priority_order.index(status) > priority_order.index(best_status):
                best_status = status

    # Special case: if Offer patterns match AND Rejected patterns match,
    # it's likely a conflict or confusing email - prefer Offer (higher level)
    if status_scores['Offer'] > 0 and status_scores['Rejected'] > 0:
        if status_scores['Offer'] >= status_scores['Rejected']:
            best_status = 'Offer'

    # Special case: if Interviewing AND Applied both match,
    # prefer Interviewing (more actionable)
    if status_scores['Interviewing'] > 0 and status_scores['Applied'] > 0:
        if status_scores['Interviewing'] >= status_scores['Applied']:
            best_status = 'Interviewing'

    return best_status, best_score, matched_patterns.get(best_status, [])


def get_status_level(status: str) -> int:
    """
    Get the hierarchy level for a status.

    Args:
        status: Status string

    Returns:
        Level number (0 = Applied, 1 = Interviewing/Rejected, 2 = Offer)
    """
    return STATUS_HIERARCHY.get(status, 0)


def can_update_status(current_status: str, new_status: str) -> StatusUpdateResult:
    """
    Determine if a status update is allowed based on hierarchy rules.

    Rules:
    - Status can move UP (higher level)
    - Status can move SIDEWAYS (same level, e.g., Interviewing <-> Rejected)
    - Status CANNOT move DOWN (lower level)

    Args:
        current_status: Current status in Excel
        new_status: New status from incoming email

    Returns:
        StatusUpdateResult with allowed flag and reason
    """
    current_level = get_status_level(current_status)
    new_level = get_status_level(new_status)

    if new_level > current_level:
        # Moving UP - allowed
        return StatusUpdateResult(
            allowed=True,
            reason=f"Status upgrade: {current_status} -> {new_status}",
            is_conflict=False
        )
    elif new_level == current_level:
        # Moving SIDEWAYS - allowed
        # (e.g., Interviewing -> Rejected or Rejected -> Interviewing)
        return StatusUpdateResult(
            allowed=True,
            reason=f"Status sideways move: {current_status} -> {new_status}",
            is_conflict=False
        )
    else:
        # Moving DOWN - not allowed, flag as conflict
        return StatusUpdateResult(
            allowed=False,
            reason=f"Cannot downgrade status: {current_status} -> {new_status}",
            is_conflict=True,
            kept_status=current_status,
            attempted_status=new_status
        )


def create_conflict_note(
    current_status: str,
    new_status: str,
    conflict_date: Optional[datetime] = None
) -> str:
    """
    Create a conflict note for Excel.

    Args:
        current_status: The status that was kept
        new_status: The status that was rejected
        conflict_date: When the conflict occurred

    Returns:
        Formatted conflict note string
    """
    date_str = conflict_date.strftime('%Y-%m-%d') if conflict_date else datetime.now().strftime('%Y-%m-%d')
    return f"Conflict: received {new_status} after {current_status} on {date_str}"


def classify_email(extraction_result: ExtractionResult, email: Dict[str, Any]) -> ExtractionResult:
    """
    Classify the status of an email and update the extraction result.

    This function takes an ExtractionResult (from the extractor module)
    and adds status classification to it.

    Args:
        extraction_result: Result from pattern_match_extraction
        email: Original email dict with 'subject' and 'body'

    Returns:
        Updated ExtractionResult with status classification
    """
    subject = email.get('subject', '')
    body = email.get('body', email.get('snippet', ''))

    # Classify status
    status, match_count, matched_patterns = classify_status(subject, body)

    # Update extraction result
    extraction_result.status = status
    extraction_result.status_matches = match_count
    extraction_result.matched_patterns = matched_patterns

    # Recalculate confidence with status information
    confidence, score = calculate_confidence(extraction_result)
    extraction_result.confidence = confidence
    extraction_result.confidence_score = score

    return extraction_result


def get_status_display(status: str) -> str:
    """
    Get display string for a status.

    Args:
        status: Status string

    Returns:
        Formatted display string
    """
    display_map = {
        'Applied': 'Applied',
        'Interviewing': 'Interviewing',
        'Rejected': 'Rejected',
        'Offer': 'Offer',
    }
    return display_map.get(status, status)


def get_status_color(status: str) -> str:
    """
    Get display color for a status (for CLI/Excel formatting).

    Args:
        status: Status string

    Returns:
        Color name
    """
    color_map = {
        'Applied': 'blue',
        'Interviewing': 'yellow',
        'Rejected': 'red',
        'Offer': 'green',
    }
    return color_map.get(status, 'white')


def is_deletable_status(status: str) -> bool:
    """
    Check if a status indicates the email can be deleted.

    Only Applied and Rejected emails are candidates for deletion.
    Interviewing and Offer emails are always kept.

    Args:
        status: Status string

    Returns:
        True if the email can potentially be deleted
    """
    return status in ['Applied', 'Rejected']


def is_protected_status(status: str) -> bool:
    """
    Check if a status indicates the email should always be kept.

    Interviewing and Offer emails are always protected.

    Args:
        status: Status string

    Returns:
        True if the email should never be deleted
    """
    return status in ['Interviewing', 'Offer']


def validate_status(status: str) -> bool:
    """
    Validate that a status string is valid.

    Args:
        status: Status string to validate

    Returns:
        True if valid status
    """
    return status in STATUS_HIERARCHY


def normalize_status(status: str) -> str:
    """
    Normalize a status string to standard format.

    Handles common variations and typos.

    Args:
        status: Status string to normalize

    Returns:
        Normalized status string
    """
    status_lower = status.lower().strip()

    normalization_map = {
        'applied': 'Applied',
        'application': 'Applied',
        'submitted': 'Applied',
        'interviewing': 'Interviewing',
        'interview': 'Interviewing',
        'screening': 'Interviewing',
        'rejected': 'Rejected',
        'rejection': 'Rejected',
        'declined': 'Rejected',
        'offer': 'Offer',
        'offered': 'Offer',
    }

    return normalization_map.get(status_lower, 'Applied')


# =============================================================================
# Status Transition Table (for reference/documentation)
# =============================================================================

STATUS_TRANSITIONS = """
Valid Status Transitions:
=========================

From Applied (Level 0):
  -> Interviewing (Level 1) : ALLOWED (upgrade)
  -> Rejected (Level 1)     : ALLOWED (upgrade)
  -> Offer (Level 2)        : ALLOWED (upgrade)

From Interviewing (Level 1):
  -> Applied (Level 0)      : BLOCKED (downgrade) - FLAG CONFLICT
  -> Rejected (Level 1)     : ALLOWED (sideways)
  -> Offer (Level 2)        : ALLOWED (upgrade)

From Rejected (Level 1):
  -> Applied (Level 0)      : BLOCKED (downgrade) - FLAG CONFLICT
  -> Interviewing (Level 1) : ALLOWED (sideways - company reconsidered)
  -> Offer (Level 2)        : ALLOWED (upgrade)

From Offer (Level 2):
  -> Applied (Level 0)      : BLOCKED (downgrade) - FLAG CONFLICT
  -> Interviewing (Level 1) : BLOCKED (downgrade) - FLAG CONFLICT
  -> Rejected (Level 1)     : BLOCKED (downgrade) - FLAG CONFLICT
"""
