"""
Unit tests for the extractor module.

Tests cover:
- Company extraction from domain, subject, body
- Position extraction from subject and body
- Confidence scoring
- Full extraction pipeline
- Real email examples from user (Perplexity, Plaid, Gem, etc.)
"""

import pytest
from datetime import datetime

from job_tracker.extractor import (
    ExtractionResult,
    extract_company_from_domain,
    extract_company_from_subject,
    extract_company_from_body,
    extract_company,
    extract_position_from_subject,
    extract_position_from_body,
    extract_position,
    pattern_match_extraction,
    extract_email_info,
    calculate_confidence,
    should_use_ai,
)


# =============================================================================
# Company Extraction Tests - Domain
# =============================================================================

class TestExtractCompanyFromDomain:
    """Tests for company extraction from email domain."""

    def test_simple_domain(self):
        """Test extraction from simple company domain."""
        company, source = extract_company_from_domain('jobs@techcorp.com')
        assert company == 'Techcorp'
        assert source == 'domain'

    def test_perplexity_domain(self):
        """Test extraction from Perplexity (real user example)."""
        company, source = extract_company_from_domain('recruiting@perplexity.ai')
        assert company == 'Perplexity'
        assert source == 'domain'

    def test_plaid_domain(self):
        """Test extraction from Plaid (real user example)."""
        company, source = extract_company_from_domain('jobs@plaid.com')
        assert company == 'Plaid'
        assert source == 'domain'

    def test_neuralink_domain(self):
        """Test extraction from Neuralink (real user example)."""
        company, source = extract_company_from_domain('apply@neuralink.com')
        assert company == 'Neuralink'
        assert source == 'domain'

    def test_gem_domain(self):
        """Test extraction from Gem (real user example)."""
        company, source = extract_company_from_domain('recruiting@gem.com')
        assert company == 'Gem'
        assert source == 'domain'

    def test_vercel_domain(self):
        """Test extraction from Vercel (real user example)."""
        company, source = extract_company_from_domain('talent@vercel.com')
        assert company == 'Vercel'
        assert source == 'domain'

    def test_generic_provider_greenhouse(self):
        """Test that greenhouse.io returns None (generic ATS)."""
        company, source = extract_company_from_domain('noreply@greenhouse.io')
        assert company is None
        assert source is None

    def test_generic_provider_lever(self):
        """Test that lever.co returns None (generic ATS)."""
        company, source = extract_company_from_domain('no-reply@lever.co')
        assert company is None
        assert source is None

    def test_gmail_returns_none(self):
        """Test that gmail.com returns None (personal email)."""
        company, source = extract_company_from_domain('someone@gmail.com')
        assert company is None
        assert source is None

    def test_full_name_format(self):
        """Test extraction from 'Name <email>' format."""
        company, source = extract_company_from_domain('TechCorp Recruiting <jobs@techcorp.com>')
        assert company == 'Techcorp'
        assert source == 'domain'

    def test_subdomain(self):
        """Test extraction with subdomain."""
        company, source = extract_company_from_domain('noreply@jobs.techcorp.com')
        assert company == 'Techcorp'
        assert source == 'domain'

    def test_hyphenated_domain(self):
        """Test extraction with hyphenated domain."""
        company, source = extract_company_from_domain('careers@tech-corp.com')
        # Extracts first part of hyphenated domain
        assert company == 'Tech'
        assert source == 'domain'

    def test_empty_string(self):
        """Test empty string returns None."""
        company, source = extract_company_from_domain('')
        assert company is None
        assert source is None

    def test_invalid_email(self):
        """Test invalid email format returns None."""
        company, source = extract_company_from_domain('not-an-email')
        assert company is None
        assert source is None


# =============================================================================
# Company Extraction Tests - Subject
# =============================================================================

class TestExtractCompanyFromSubject:
    """Tests for company extraction from email subject."""

    def test_thank_you_for_applying(self):
        """Test 'Thank you for applying to [Company]' pattern."""
        company, source = extract_company_from_subject('Thank you for applying to Perplexity!')
        assert company == 'Perplexity'
        assert source == 'subject'

    def test_application_to(self):
        """Test 'Application to [Company]' pattern."""
        company, source = extract_company_from_subject('Application to TechCorp')
        assert company == 'Techcorp'
        assert source == 'subject'

    def test_application_update_from(self):
        """Test 'Application Update from [Company]' pattern."""
        company, source = extract_company_from_subject('Application Update from Gem')
        assert company == 'Gem'
        assert source == 'subject'

    def test_application_received_pipe(self):
        """Test 'Application Received | [Company]' pattern."""
        company, source = extract_company_from_subject('Application Received | Spire')
        assert company == 'Spire'
        assert source == 'subject'

    def test_your_application_at(self):
        """Test 'Your application at [Company]' pattern."""
        company, source = extract_company_from_subject('Your application at Robinhood')
        assert company == 'Robinhood'
        assert source == 'subject'

    def test_application_was_sent(self):
        """Test '...application was sent to [Company]' pattern."""
        company, source = extract_company_from_subject('Jamal, your application was sent to Neuralink')
        assert company == 'Neuralink'
        assert source == 'subject'

    def test_no_company_in_subject(self):
        """Test subject without company returns None."""
        company, source = extract_company_from_subject('Important Update')
        assert company is None
        assert source is None


# =============================================================================
# Company Extraction Tests - Body
# =============================================================================

class TestExtractCompanyFromBody:
    """Tests for company extraction from email body."""

    def test_interest_in(self):
        """Test 'Thank you for your interest in [Company]' pattern."""
        body = "Thank you for your interest in TechCorp. We will review your application."
        company, source = extract_company_from_body(body)
        assert company == 'Techcorp'
        assert source == 'body'

    def test_applied_to(self):
        """Test 'You applied to [Company]' pattern."""
        body = "You applied to Stripe for the Software Engineer position."
        company, source = extract_company_from_body(body)
        assert company == 'Stripe'
        assert source == 'body'

    def test_role_at(self):
        """Test '...role at [Company]' pattern."""
        body = "Thank you for applying to the Senior Engineer role at Netflix."
        company, source = extract_company_from_body(body)
        assert company == 'Netflix'
        assert source == 'body'

    def test_here_at(self):
        """Test 'here at [Company]' pattern."""
        body = "We're excited about your application here at Airbnb."
        company, source = extract_company_from_body(body)
        assert company == 'Airbnb'
        assert source == 'body'


# =============================================================================
# Full Company Extraction Tests
# =============================================================================

class TestExtractCompany:
    """Tests for the full company extraction pipeline."""

    def test_domain_priority(self):
        """Test that domain extraction takes priority."""
        email = {
            'from': 'jobs@techcorp.com',
            'subject': 'Application to OtherCompany',
            'body': 'Thank you for your interest in YetAnother.'
        }
        company, source = extract_company(email)
        assert company == 'Techcorp'
        assert source == 'domain'

    def test_fallback_to_subject(self):
        """Test fallback to subject when domain is generic."""
        email = {
            'from': 'noreply@greenhouse.io',
            'subject': 'Thank you for applying to Stripe!',
            'body': 'We received your application.'
        }
        company, source = extract_company(email)
        assert company == 'Stripe'
        assert source == 'subject'

    def test_fallback_to_body(self):
        """Test fallback to body when domain and subject fail."""
        email = {
            'from': 'noreply@greenhouse.io',
            'subject': 'Application Received',
            'body': 'Thank you for your interest in Dropbox. We will review.'
        }
        company, source = extract_company(email)
        assert company == 'Dropbox'
        assert source == 'body'

    def test_returns_unknown(self):
        """Test returns 'Unknown' when all methods fail."""
        email = {
            'from': 'noreply@greenhouse.io',
            'subject': 'Update',
            'body': 'Please check your status online.'
        }
        company, source = extract_company(email)
        assert company == 'Unknown'
        assert source is None


# =============================================================================
# Position Extraction Tests
# =============================================================================

class TestExtractPosition:
    """Tests for position extraction."""

    def test_application_for_position(self):
        """Test 'Application for [Position]' pattern."""
        position, source = extract_position_from_subject('Application for Software Engineer')
        assert 'Software Engineer' in position
        assert source == 'subject'

    def test_position_with_level(self):
        """Test position with seniority level."""
        position, source = extract_position_from_subject('Application for Senior Software Engineer')
        assert 'Senior' in position
        assert 'Engineer' in position
        assert source == 'subject'

    def test_position_in_body(self):
        """Test position extraction from body."""
        body = "Thank you for applying to our Senior Data Scientist position at TechCorp."
        position, source = extract_position_from_body(body)
        assert 'Data Scientist' in position or 'Scientist' in position
        assert source == 'body'

    def test_no_position_returns_not_specified(self):
        """Test returns 'Not specified' when no position found."""
        position, source = extract_position('Application Update', 'Thank you for your application.')
        assert position == 'Not specified'
        assert source is None


# =============================================================================
# Confidence Scoring Tests
# =============================================================================

class TestConfidenceScoring:
    """Tests for confidence scoring algorithm."""

    def test_high_confidence(self):
        """Test high confidence when all fields extracted."""
        result = ExtractionResult(
            company='TechCorp',
            company_source='domain',
            position='Software Engineer',
            position_source='subject',
            status='Applied',
            status_matches=3
        )
        confidence, score = calculate_confidence(result)
        assert confidence == 'high'
        assert score >= 0.7

    def test_medium_confidence(self):
        """Test medium confidence with partial extraction."""
        result = ExtractionResult(
            company='TechCorp',
            company_source='subject',
            position='Not specified',
            status='Applied',
            status_matches=1
        )
        confidence, score = calculate_confidence(result)
        assert confidence == 'medium'
        assert 0.4 <= score < 0.7

    def test_low_confidence(self):
        """Test low confidence when extraction fails."""
        result = ExtractionResult(
            company='Unknown',
            position='Not specified',
            status='Applied',
            status_matches=0
        )
        confidence, score = calculate_confidence(result)
        assert confidence == 'low'
        assert score < 0.4

    def test_domain_bonus(self):
        """Test domain extraction gives confidence bonus."""
        result_domain = ExtractionResult(
            company='TechCorp',
            company_source='domain',
            status_matches=1
        )
        result_subject = ExtractionResult(
            company='TechCorp',
            company_source='subject',
            status_matches=1
        )
        _, score_domain = calculate_confidence(result_domain)
        _, score_subject = calculate_confidence(result_subject)
        assert score_domain > score_subject


# =============================================================================
# AI Fallback Decision Tests
# =============================================================================

class TestShouldUseAI:
    """Tests for AI fallback decision logic."""

    def test_ai_disabled_returns_false(self):
        """Test returns False when AI is disabled."""
        result = ExtractionResult(confidence='low', company='Unknown')
        assert should_use_ai(result, use_ai_enabled=False) is False

    def test_low_confidence_triggers_ai(self):
        """Test low confidence triggers AI when enabled."""
        result = ExtractionResult(confidence='low', company='TechCorp')
        assert should_use_ai(result, use_ai_enabled=True) is True

    def test_unknown_company_triggers_ai(self):
        """Test unknown company triggers AI when enabled."""
        result = ExtractionResult(confidence='medium', company='Unknown')
        assert should_use_ai(result, use_ai_enabled=True) is True

    def test_high_confidence_no_ai(self):
        """Test high confidence doesn't trigger AI."""
        result = ExtractionResult(
            confidence='high',
            company='TechCorp',
            status='Rejected',
            status_matches=3
        )
        assert should_use_ai(result, use_ai_enabled=True) is False


# =============================================================================
# Real Email Examples from PRD
# =============================================================================

class TestRealEmailExamples:
    """Tests using real email examples from the user's inbox (from PRD)."""

    def test_perplexity_email(self):
        """Test Perplexity email extraction (real user example)."""
        email = {
            'id': 'msg_perplexity_123',
            'from': 'recruiting@perplexity.ai',
            'subject': 'Thank you for applying to Perplexity!',
            'body': """Hi Jamal,

Thanks for applying to Perplexity! We've received your application and
will review it shortly.

We will be in touch if your qualifications match our needs for the role.
Thank you for taking the time to apply and we look forward to getting to
know you better.

Thank you,
Perplexity Recruiting""",
            'date': datetime(2026, 1, 15)
        }

        result = pattern_match_extraction(email)
        assert result.company == 'Perplexity'
        assert result.company_source == 'domain'
        assert result.email_id == 'msg_perplexity_123'

    def test_plaid_email(self):
        """Test Plaid email extraction (real user example)."""
        email = {
            'id': 'msg_plaid_456',
            'from': 'jobs@plaid.com',
            'subject': 'Thank you for your application to Plaid',
            'body': """Thank you for your interest in Plaid! We wanted to let you know we
received your application for Software Engineer - Platform, and we are
delighted that you would consider joining our team.

Our team will review your application and will be in touch if your
qualifications match our needs for the role.""",
            'date': datetime(2026, 1, 10)
        }

        result = pattern_match_extraction(email)
        assert result.company == 'Plaid'
        assert result.company_source == 'domain'
        # Position should be extracted
        assert 'Software Engineer' in result.position or 'Engineer' in result.position or result.position != 'Not specified'

    def test_neuralink_email(self):
        """Test Neuralink email extraction (real user example)."""
        email = {
            'id': 'msg_neuralink_789',
            'from': 'apply@neuralink.com',
            'subject': 'Jamal, your application was sent to Neuralink',
            'body': 'Your application was sent to Neuralink',
            'date': datetime(2026, 1, 12)
        }

        result = pattern_match_extraction(email)
        assert result.company == 'Neuralink'
        assert result.company_source == 'domain'

    def test_gem_email(self):
        """Test Gem rejection email extraction (real user example)."""
        email = {
            'id': 'msg_gem_101',
            'from': 'recruiting@gem.com',
            'subject': 'Application Update from Gem',
            'body': """Thank you so much for your interest in Gem and our Software Engineer
role. We know a lot of consideration went into your application.

Unfortunately, we won't be advancing you to the next round of our
hiring process at this time.

Thanks again for your interest in Gem and we wish you well on your
search.""",
            'date': datetime(2026, 1, 18)
        }

        result = pattern_match_extraction(email)
        assert result.company == 'Gem'
        assert result.company_source == 'domain'

    def test_vercel_email(self):
        """Test Vercel email extraction (real user example)."""
        email = {
            'id': 'msg_vercel_202',
            'from': 'talent@vercel.com',
            'subject': 'Thank you for applying to Vercel!',
            'body': """We wanted to confirm that we received your application for the Software
Engineer, CI/CD role at Vercel.

Thank you for applying! While we do receive a large number of
applications daily, rest assured that we are committed to reviewing and
responding to each application.""",
            'date': datetime(2026, 1, 14)
        }

        result = pattern_match_extraction(email)
        assert result.company == 'Vercel'
        assert result.company_source == 'domain'

    def test_robinhood_rejection_email(self):
        """Test Robinhood rejection email (real user example)."""
        email = {
            'id': 'msg_robinhood_303',
            'from': 'recruiting@robinhood.com',
            'subject': 'Important information about your application to Robinhood',
            'body': """Thank you for taking the time to apply for the [PIPELINE] Software
Engineer, IC3 (US) position. We've been extremely fortunate to have a
fantastic response from accomplished candidates such as yourself for
this role. However, after careful consideration, we've made the
decision to not move forward with the interview process at this time.

We really appreciate your time and efforts in applying. We'd love to stay
in touch as our team continues to grow and reconnect down the line.""",
            'date': datetime(2026, 1, 20)
        }

        result = pattern_match_extraction(email)
        assert result.company == 'Robinhood'
        assert result.company_source == 'domain'


# =============================================================================
# Full Pipeline Tests
# =============================================================================

class TestExtractEmailInfo:
    """Tests for the complete extraction pipeline."""

    def test_full_extraction(self):
        """Test complete extraction with all fields."""
        email = {
            'id': 'msg_test_001',
            'from': 'recruiting@techcorp.com',
            'subject': 'Application for Senior Software Engineer at TechCorp',
            'body': 'Thank you for applying to TechCorp! We received your application.',
            'date': datetime(2026, 1, 25)
        }

        result = extract_email_info(email)

        assert result.company == 'Techcorp'
        assert result.email_id == 'msg_test_001'
        assert result.extraction_method == 'pattern'
        assert result.confidence in ['high', 'medium', 'low']

    def test_extraction_result_to_dict(self):
        """Test ExtractionResult serialization."""
        result = ExtractionResult(
            company='TechCorp',
            position='Software Engineer',
            status='Applied',
            confidence='high',
            email_id='msg_123',
            email_date=datetime(2026, 1, 25)
        )

        data = result.to_dict()

        assert data['company'] == 'TechCorp'
        assert data['position'] == 'Software Engineer'
        assert data['status'] == 'Applied'
        assert data['confidence'] == 'high'
        assert data['email_id'] == 'msg_123'
        assert data['email_date'] == '2026-01-25T00:00:00'
