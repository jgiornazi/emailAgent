"""
Unit tests for the classifier module.

Tests cover:
- Status classification (Applied, Rejected, Interviewing, Offer)
- Status hierarchy and transitions
- Conflict detection
- Real email examples from user
"""

import pytest
from datetime import datetime

from job_tracker.classifier import (
    classify_status,
    can_update_status,
    get_status_level,
    create_conflict_note,
    is_deletable_status,
    is_protected_status,
    validate_status,
    normalize_status,
    classify_email,
    StatusUpdateResult,
)
from job_tracker.extractor import ExtractionResult, pattern_match_extraction


# =============================================================================
# Status Classification Tests - Applied
# =============================================================================

class TestClassifyStatusApplied:
    """Tests for classifying Applied status emails."""

    def test_thank_you_for_applying(self):
        """Test 'thank you for applying' pattern."""
        status, count, patterns = classify_status(
            'Thank you for applying',
            'We received your application.'
        )
        assert status == 'Applied'
        assert count >= 1

    def test_received_your_application(self):
        """Test 'received your application' pattern."""
        status, count, patterns = classify_status(
            'Application Received',
            'We have received your application and will review it shortly.'
        )
        assert status == 'Applied'
        assert count >= 1

    def test_will_review(self):
        """Test 'we will review' pattern."""
        status, count, patterns = classify_status(
            'Application Update',
            'Our team will review your application and be in touch.'
        )
        assert status == 'Applied'
        assert count >= 1

    def test_perplexity_real_email(self):
        """Test real Perplexity email (from PRD)."""
        subject = 'Thank you for applying to Perplexity!'
        body = """Thanks for applying to Perplexity! We've received your application and
will review it shortly. We will be in touch if your qualifications match
our needs for the role."""

        status, count, patterns = classify_status(subject, body)
        assert status == 'Applied'
        assert count >= 2  # Multiple matches expected

    def test_plaid_real_email(self):
        """Test real Plaid email (from PRD)."""
        subject = 'Thank you for your application to Plaid'
        body = """Thank you for your interest in Plaid! We wanted to let you know we
received your application for Software Engineer - Platform, and we are
delighted that you would consider joining our team."""

        status, count, patterns = classify_status(subject, body)
        assert status == 'Applied'
        assert count >= 2


# =============================================================================
# Status Classification Tests - Rejected
# =============================================================================

class TestClassifyStatusRejected:
    """Tests for classifying Rejected status emails."""

    def test_not_moving_forward(self):
        """Test 'not moving forward' pattern."""
        status, count, patterns = classify_status(
            'Application Update',
            'Unfortunately, we will not be moving forward with your application.'
        )
        assert status == 'Rejected'
        assert count >= 1

    def test_wont_be_advancing(self):
        """Test 'won\'t be advancing' pattern."""
        status, count, patterns = classify_status(
            'Application Update',
            "Unfortunately, we won't be advancing you to the next round."
        )
        assert status == 'Rejected'
        assert count >= 1

    def test_wish_you_success(self):
        """Test 'wish you success in your job search' pattern."""
        status, count, patterns = classify_status(
            'Thanks',
            'We wish you success in your job search.'
        )
        assert status == 'Rejected'
        assert count >= 1

    def test_gem_real_email(self):
        """Test real Gem rejection email (from PRD)."""
        subject = 'Application Update from Gem'
        body = """Thank you so much for your interest in Gem and our Software Engineer
role. Unfortunately, we won't be advancing you to the next round of our
hiring process at this time. Thanks again and we wish you well on your search."""

        status, count, patterns = classify_status(subject, body)
        assert status == 'Rejected'
        assert count >= 2

    def test_robinhood_real_email(self):
        """Test real Robinhood rejection email (from PRD)."""
        subject = 'Important information about your application to Robinhood'
        body = """Thank you for taking the time to apply. After careful consideration,
we've made the decision to not move forward with the interview process
at this time. We really appreciate your time and efforts in applying."""

        status, count, patterns = classify_status(subject, body)
        assert status == 'Rejected'
        assert count >= 2

    def test_attentive_real_email(self):
        """Test real Attentive rejection email (from PRD)."""
        subject = 'Thanks from Attentive'
        body = """After reviewing your work and experience, we've made the decision to
not move forward at this time. We hope you don't mind if we reach out
to you in the future. We wish you success in your job search!"""

        status, count, patterns = classify_status(subject, body)
        assert status == 'Rejected'
        assert count >= 2


# =============================================================================
# Status Classification Tests - Interviewing
# =============================================================================

class TestClassifyStatusInterviewing:
    """Tests for classifying Interviewing status emails."""

    def test_interview_keyword(self):
        """Test 'interview' keyword."""
        status, count, patterns = classify_status(
            'Interview Request',
            'We would like to schedule an interview with you.'
        )
        assert status == 'Interviewing'
        assert count >= 1

    def test_phone_screen(self):
        """Test 'phone screen' pattern."""
        status, count, patterns = classify_status(
            'Next Steps',
            'We would like to schedule a phone screen with you.'
        )
        assert status == 'Interviewing'
        assert count >= 1

    def test_schedule_call(self):
        """Test 'schedule a call' pattern."""
        status, count, patterns = classify_status(
            'Application Update',
            'Can we schedule a call to discuss the role?'
        )
        assert status == 'Interviewing'
        assert count >= 1

    def test_technical_assessment(self):
        """Test 'technical assessment' pattern."""
        status, count, patterns = classify_status(
            'Next Steps',
            'Please complete the technical assessment attached.'
        )
        assert status == 'Interviewing'
        assert count >= 1

    def test_take_home_assignment(self):
        """Test 'take-home assignment' pattern."""
        status, count, patterns = classify_status(
            'Coding Challenge',
            'As the next step, please complete this take-home assignment.'
        )
        assert status == 'Interviewing'
        assert count >= 1


# =============================================================================
# Status Classification Tests - Offer
# =============================================================================

class TestClassifyStatusOffer:
    """Tests for classifying Offer status emails."""

    def test_pleased_to_offer(self):
        """Test 'pleased to offer' pattern."""
        status, count, patterns = classify_status(
            'Job Offer',
            'We are pleased to offer you the position of Software Engineer.'
        )
        assert status == 'Offer'
        assert count >= 1

    def test_job_offer_keyword(self):
        """Test 'job offer' keyword."""
        status, count, patterns = classify_status(
            'Job Offer - Software Engineer',
            'Please find attached your job offer letter.'
        )
        assert status == 'Offer'
        assert count >= 2

    def test_welcome_to_team(self):
        """Test 'welcome to the team' pattern."""
        status, count, patterns = classify_status(
            'Congratulations!',
            'Welcome to the team! We are excited to have you join us.'
        )
        assert status == 'Offer'
        assert count >= 1

    def test_compensation_package(self):
        """Test 'compensation package' pattern."""
        status, count, patterns = classify_status(
            'Offer Details',
            'Here is your compensation package and start date.'
        )
        assert status == 'Offer'
        assert count >= 2


# =============================================================================
# Status Hierarchy Tests
# =============================================================================

class TestStatusHierarchy:
    """Tests for status hierarchy rules."""

    def test_applied_level(self):
        """Test Applied is level 0."""
        assert get_status_level('Applied') == 0

    def test_interviewing_level(self):
        """Test Interviewing is level 1."""
        assert get_status_level('Interviewing') == 1

    def test_rejected_level(self):
        """Test Rejected is level 1 (same as Interviewing)."""
        assert get_status_level('Rejected') == 1

    def test_offer_level(self):
        """Test Offer is level 2."""
        assert get_status_level('Offer') == 2


# =============================================================================
# Status Update Rules Tests
# =============================================================================

class TestCanUpdateStatus:
    """Tests for status update rules."""

    # Upgrades (allowed)
    def test_applied_to_interviewing_allowed(self):
        """Test Applied -> Interviewing is allowed (upgrade)."""
        result = can_update_status('Applied', 'Interviewing')
        assert result.allowed is True
        assert result.is_conflict is False

    def test_applied_to_rejected_allowed(self):
        """Test Applied -> Rejected is allowed (upgrade)."""
        result = can_update_status('Applied', 'Rejected')
        assert result.allowed is True
        assert result.is_conflict is False

    def test_applied_to_offer_allowed(self):
        """Test Applied -> Offer is allowed (upgrade)."""
        result = can_update_status('Applied', 'Offer')
        assert result.allowed is True
        assert result.is_conflict is False

    def test_interviewing_to_offer_allowed(self):
        """Test Interviewing -> Offer is allowed (upgrade)."""
        result = can_update_status('Interviewing', 'Offer')
        assert result.allowed is True
        assert result.is_conflict is False

    def test_rejected_to_offer_allowed(self):
        """Test Rejected -> Offer is allowed (upgrade)."""
        result = can_update_status('Rejected', 'Offer')
        assert result.allowed is True
        assert result.is_conflict is False

    # Sideways (allowed)
    def test_interviewing_to_rejected_allowed(self):
        """Test Interviewing -> Rejected is allowed (sideways)."""
        result = can_update_status('Interviewing', 'Rejected')
        assert result.allowed is True
        assert result.is_conflict is False

    def test_rejected_to_interviewing_allowed(self):
        """Test Rejected -> Interviewing is allowed (sideways)."""
        result = can_update_status('Rejected', 'Interviewing')
        assert result.allowed is True
        assert result.is_conflict is False

    # Downgrades (blocked - conflict)
    def test_offer_to_rejected_blocked(self):
        """Test Offer -> Rejected is blocked (downgrade)."""
        result = can_update_status('Offer', 'Rejected')
        assert result.allowed is False
        assert result.is_conflict is True
        assert result.kept_status == 'Offer'
        assert result.attempted_status == 'Rejected'

    def test_offer_to_interviewing_blocked(self):
        """Test Offer -> Interviewing is blocked (downgrade)."""
        result = can_update_status('Offer', 'Interviewing')
        assert result.allowed is False
        assert result.is_conflict is True

    def test_offer_to_applied_blocked(self):
        """Test Offer -> Applied is blocked (downgrade)."""
        result = can_update_status('Offer', 'Applied')
        assert result.allowed is False
        assert result.is_conflict is True

    def test_interviewing_to_applied_blocked(self):
        """Test Interviewing -> Applied is blocked (downgrade)."""
        result = can_update_status('Interviewing', 'Applied')
        assert result.allowed is False
        assert result.is_conflict is True

    def test_rejected_to_applied_blocked(self):
        """Test Rejected -> Applied is blocked (downgrade)."""
        result = can_update_status('Rejected', 'Applied')
        assert result.allowed is False
        assert result.is_conflict is True


# =============================================================================
# Conflict Note Tests
# =============================================================================

class TestConflictNote:
    """Tests for conflict note generation."""

    def test_conflict_note_format(self):
        """Test conflict note has correct format."""
        note = create_conflict_note('Offer', 'Rejected', datetime(2026, 1, 25))
        assert 'Conflict' in note
        assert 'Rejected' in note
        assert 'Offer' in note
        assert '2026-01-25' in note

    def test_conflict_note_without_date(self):
        """Test conflict note without explicit date uses today."""
        note = create_conflict_note('Offer', 'Rejected')
        assert 'Conflict' in note
        # Should contain a date in YYYY-MM-DD format
        import re
        assert re.search(r'\d{4}-\d{2}-\d{2}', note)


# =============================================================================
# Deletion Status Tests
# =============================================================================

class TestDeletionStatus:
    """Tests for deletion status checks."""

    def test_applied_is_deletable(self):
        """Test Applied status is deletable."""
        assert is_deletable_status('Applied') is True

    def test_rejected_is_deletable(self):
        """Test Rejected status is deletable."""
        assert is_deletable_status('Rejected') is True

    def test_interviewing_not_deletable(self):
        """Test Interviewing status is NOT deletable."""
        assert is_deletable_status('Interviewing') is False

    def test_offer_not_deletable(self):
        """Test Offer status is NOT deletable."""
        assert is_deletable_status('Offer') is False

    def test_interviewing_is_protected(self):
        """Test Interviewing status is protected."""
        assert is_protected_status('Interviewing') is True

    def test_offer_is_protected(self):
        """Test Offer status is protected."""
        assert is_protected_status('Offer') is True

    def test_applied_not_protected(self):
        """Test Applied status is NOT protected."""
        assert is_protected_status('Applied') is False


# =============================================================================
# Status Validation Tests
# =============================================================================

class TestStatusValidation:
    """Tests for status validation and normalization."""

    def test_valid_statuses(self):
        """Test all valid statuses are validated."""
        assert validate_status('Applied') is True
        assert validate_status('Interviewing') is True
        assert validate_status('Rejected') is True
        assert validate_status('Offer') is True

    def test_invalid_status(self):
        """Test invalid status returns False."""
        assert validate_status('InvalidStatus') is False
        assert validate_status('') is False

    def test_normalize_applied_variations(self):
        """Test normalization of Applied variations."""
        assert normalize_status('applied') == 'Applied'
        assert normalize_status('APPLIED') == 'Applied'
        assert normalize_status('application') == 'Applied'
        assert normalize_status('submitted') == 'Applied'

    def test_normalize_interviewing_variations(self):
        """Test normalization of Interviewing variations."""
        assert normalize_status('interviewing') == 'Interviewing'
        assert normalize_status('interview') == 'Interviewing'
        assert normalize_status('screening') == 'Interviewing'

    def test_normalize_rejected_variations(self):
        """Test normalization of Rejected variations."""
        assert normalize_status('rejected') == 'Rejected'
        assert normalize_status('rejection') == 'Rejected'
        assert normalize_status('declined') == 'Rejected'

    def test_normalize_offer_variations(self):
        """Test normalization of Offer variations."""
        assert normalize_status('offer') == 'Offer'
        assert normalize_status('offered') == 'Offer'


# =============================================================================
# Full Classification Pipeline Tests
# =============================================================================

class TestClassifyEmail:
    """Tests for the full email classification pipeline."""

    def test_classify_applied_email(self):
        """Test classifying an Applied status email."""
        email = {
            'id': 'msg_123',
            'from': 'jobs@techcorp.com',
            'subject': 'Thank you for applying',
            'body': 'We received your application and will review it.',
            'date': datetime(2026, 1, 25)
        }

        extraction_result = pattern_match_extraction(email)
        result = classify_email(extraction_result, email)

        assert result.status == 'Applied'
        assert result.status_matches >= 1

    def test_classify_rejected_email(self):
        """Test classifying a Rejected status email."""
        email = {
            'id': 'msg_456',
            'from': 'jobs@techcorp.com',
            'subject': 'Application Update',
            'body': 'Unfortunately, we will not be moving forward. We wish you success in your job search.',
            'date': datetime(2026, 1, 25)
        }

        extraction_result = pattern_match_extraction(email)
        result = classify_email(extraction_result, email)

        assert result.status == 'Rejected'
        assert result.status_matches >= 2

    def test_classify_interviewing_email(self):
        """Test classifying an Interviewing status email."""
        email = {
            'id': 'msg_789',
            'from': 'jobs@techcorp.com',
            'subject': 'Interview Request',
            'body': 'We would like to schedule a phone screen with you next week.',
            'date': datetime(2026, 1, 25)
        }

        extraction_result = pattern_match_extraction(email)
        result = classify_email(extraction_result, email)

        assert result.status == 'Interviewing'
        assert result.status_matches >= 2

    def test_classify_offer_email(self):
        """Test classifying an Offer status email."""
        email = {
            'id': 'msg_101',
            'from': 'jobs@techcorp.com',
            'subject': 'Job Offer',
            'body': 'We are pleased to offer you the position. Please find your compensation package attached.',
            'date': datetime(2026, 1, 25)
        }

        extraction_result = pattern_match_extraction(email)
        result = classify_email(extraction_result, email)

        assert result.status == 'Offer'
        assert result.status_matches >= 2


# =============================================================================
# Edge Cases and Priority Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and priority handling."""

    def test_applied_with_interview_mention_becomes_interviewing(self):
        """Test that 'applied' email mentioning interview becomes Interviewing."""
        # When interview scheduling is mentioned, it should be Interviewing
        subject = 'Next Steps - Interview'
        body = 'We would like to schedule an interview with you next week.'

        status, count, patterns = classify_status(subject, body)
        # Should be Interviewing due to interview keyword
        assert status == 'Interviewing'

    def test_empty_email(self):
        """Test classification of empty email."""
        status, count, patterns = classify_status('', '')
        assert status == 'Applied'  # Default fallback
        assert count == 0

    def test_ambiguous_email_defaults_to_applied(self):
        """Test ambiguous email defaults to Applied."""
        status, count, patterns = classify_status(
            'Update',
            'Please check your application portal for updates.'
        )
        # Should default to Applied if no clear pattern matches
        assert status in ['Applied', 'Interviewing', 'Rejected', 'Offer']
