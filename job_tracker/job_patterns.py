"""
Job Email Pattern Definitions

This module contains all regex patterns and keyword lists for extracting
job application information from emails. Patterns are derived from real
user email examples as documented in the PRD.

Categories:
- Company extraction patterns (domain, subject, body)
- Position extraction patterns
- Status classification patterns (Applied, Rejected, Interviewing, Offer)
- Generic email providers to skip
- Position keywords for validation
"""

import re
from typing import List, Dict, Pattern

# =============================================================================
# GENERIC EMAIL PROVIDERS (Skip for company extraction)
# =============================================================================

GENERIC_PROVIDERS: List[str] = [
    # Personal email providers
    'gmail',
    'yahoo',
    'outlook',
    'hotmail',
    'icloud',
    'aol',
    'protonmail',
    'zoho',
    'mail',
    'live',
    'msn',

    # ATS/Recruiting platforms (company name won't be in domain)
    'greenhouse',
    'lever',
    'workday',
    'myworkdayjobs',
    'icims',
    'taleo',
    'jobvite',
    'smartrecruiters',
    'applicantstack',
    'bamboohr',
    'workable',
    'ashbyhq',
    'breezy',
    'jazz',
    'recruiterbox',
    'resumator',
    'newton',
    'pinpointhq',
    'recruitee',
    'comeet',
    'fountain',
    'rippling',
    'gusto',
    'deel',
    'namely',
    'paychex',
    'adp',
    'paylocity',
    'paycom',
    'ultipro',
    'successfactors',
    'cornerstone',
    'ceridian',
    'kronos',

    # Generic sending domains
    'noreply',
    'no-reply',
    'donotreply',
    'notifications',
    'mailer',
    'sendgrid',
    'mailchimp',
    'mailgun',
    'amazonses',
    'postmark',
    'sparkpost',
]

# =============================================================================
# COMPANY EXTRACTION PATTERNS
# =============================================================================

# Patterns for extracting company from email subject
SUBJECT_COMPANY_PATTERNS: List[str] = [
    # "Application to [Company]"
    r'application to ([^-|\n]+?)(?:\s*[-|]|$)',

    # "Your application at [Company]"
    r'your application at ([^-|\n]+?)(?:\s*[-|]|$)',

    # "[Company] - Application Received"
    r'^([^-|]+?)\s*[-|]\s*application',

    # "Thank you for applying to [Company]"
    r'applying to ([^-|!\n]+?)(?:\s*[-|!]|$)',

    # "Thank you for your application to [Company]"
    r'your application to ([^-|!\n]+?)(?:\s*[-|!]|$)',

    # "[Company]: Job Title"
    r'^([^:]+?):\s*\w',

    # "Application Update from [Company]"
    r'(?:update|thanks) from ([^-|\n]+?)(?:\s*[-|]|$)',

    # "...application was sent to [Company]"
    r'was sent to ([^-|\n]+?)(?:\s*[-|]|$)',

    # "Follow up from your...application at [Company]"
    r'application at ([^-|\n]+?)(?:\s*[-|]|$)',

    # "Important information about your application to [Company]"
    r'application to ([^-|\n]+?)(?:\s*[-|]|$)',

    # "Application Received | [Company]"
    r'\|\s*([^|\n]+?)$',

    # "[Company] Application"
    r'^([^-|]+?)\s+application\b',
]

# Patterns for extracting company from email body
BODY_COMPANY_PATTERNS: List[str] = [
    # "Thank you for your interest in [Company]"
    r'interest in ([^.\n,]+?)(?:[.,]|$)',

    # "Welcome to [Company]'s application"
    r'welcome to ([^\']+?)\'s',

    # "You applied to [Company]"
    r'applied to ([^.\n,]+?)(?:\s+for|[.,]|$)',

    # "[Company] Recruiting Team"
    r'([^.\n,]+?)\s+recruiting team',

    # "Your application for [position] at [Company]"
    r'\bat ([^.\n,]+?)(?:[.,]|$)',

    # "Thank you for applying to [Company]"
    r'applying to ([^.\n,!]+?)(?:[.,!]|$)',

    # "...role at [Company]"
    r'role at ([^.\n,]+?)(?:[.,]|$)',

    # "...position at [Company]"
    r'position at ([^.\n,]+?)(?:[.,]|$)',

    # "...job at [Company]"
    r'job at ([^.\n,]+?)(?:[.,]|$)',

    # "on behalf of [Company]"
    r'on behalf of ([^.\n,]+?)(?:[.,]|$)',

    # "here at [Company]"
    r'here at ([^.\n,]+?)(?:[.,]|$)',

    # "team at [Company]"
    r'team at ([^.\n,]+?)(?:[.,]|$)',
]

# =============================================================================
# POSITION EXTRACTION PATTERNS
# =============================================================================

POSITION_PATTERNS: List[str] = [
    # From subject: "Application for [Position]"
    r'application for\s+(?:the\s+)?([^-|\n]+?)(?:\s*[-|]|\s+at\s+|$)',

    # From subject: "Applied for [Position] at"
    r'applied for\s+(?:the\s+)?([^-|\n]+?)\s+at',

    # From subject: "[Position] - Application"
    r'^([^-]+?)\s*-\s*application',

    # From subject: "...your [Position] application"
    r'your\s+([^-|\n]+?)\s+application',

    # From body: "for the [Position] position"
    r'for the ([^.\n]+?) (?:position|role)',

    # From body: "applied to our [Position] position"
    r'applied to our ([^.\n]+?) (?:position|role)',

    # From body: "interest in the [Position]"
    r'interest in (?:the )?([^.\n]+?)(?:\s+position|\s+role|[.,])',

    # From body: "application for [Position]"
    r'application for (?:the )?([^.\n]+?)(?:\s+position|\s+role|[.,])',

    # From body: "received your application for [Position]"
    r'application for (?:the )?([^.\n]+?)(?:\s+and|\s+at|[.,])',

    # Generic position pattern with keywords
    r'((?:senior|junior|staff|principal|lead|sr\.?|jr\.?)?\s*'
    r'(?:software|backend|frontend|full[-\s]?stack|devops|data|ml|ai|cloud|platform|infrastructure|site reliability|sre|mobile|ios|android|web|qa|test|security)?\s*'
    r'(?:engineer|developer|scientist|analyst|manager|designer|architect|specialist|consultant|administrator|admin|lead|director))',
]

# Keywords that must be present to validate position extraction
POSITION_KEYWORDS: List[str] = [
    'engineer',
    'developer',
    'manager',
    'designer',
    'analyst',
    'scientist',
    'architect',
    'specialist',
    'consultant',
    'administrator',
    'admin',
    'lead',
    'director',
    'coordinator',
    'associate',
    'intern',
    'backend',
    'frontend',
    'full stack',
    'fullstack',
    'full-stack',
    'senior',
    'junior',
    'staff',
    'principal',
    'devops',
    'sre',
    'data',
    'product',
    'software',
    'qa',
    'test',
    'security',
    'cloud',
    'platform',
    'infrastructure',
    'mobile',
    'ios',
    'android',
    'web',
    'ml',
    'machine learning',
    'ai',
    'artificial intelligence',
]

# =============================================================================
# STATUS CLASSIFICATION PATTERNS
# =============================================================================

# Status hierarchy levels
STATUS_HIERARCHY: Dict[str, int] = {
    'Applied': 0,
    'Interviewing': 1,
    'Rejected': 1,  # Same level as Interviewing (sideways moves allowed)
    'Offer': 2,
}

# Patterns for each status, ordered by priority (most distinctive first)
STATUS_PATTERNS: Dict[str, List[str]] = {
    'Rejected': [
        # Direct rejection phrases (strongest indicators)
        r'not moving forward',
        r"won'?t be advancing",
        r'will not be moving forward',
        r'not move forward',
        r'made the decision to not move forward',
        r'we are not moving forward',
        r'decided to move forward with other candidates',
        r'decided to pursue (?:other|different) candidates',
        r'position has been filled',
        r'role has been filled',
        r'no longer considering',
        r'not selected',
        r'not been selected',
        r'not a fit',
        r'not the right fit',

        # Soft rejection phrases
        r'after (?:careful )?consideration.*not',
        r'unfortunately.*(?:not|won\'t|will not)',
        r'unfortunately, we will not',
        r'unfortunately, we are not',
        r'regret to inform',
        r'sorry to inform',

        # Polite closings (still rejection)
        r'wish you (?:well|success|the best) (?:in|on|with) your (?:search|job search|future)',
        r'best of luck (?:in|on|with) your (?:search|job search|future)',
        r'success in your job search',
        r'good luck (?:in|on|with) your (?:search|job search)',
        r'we appreciate your (?:time|interest|application)',

        # Future consideration (but still rejected now)
        r'(?:keep|stay) in touch',
        r'reach out.*in the future',
        r'future opportunities',
        r'watch our (?:career|careers) page',
        r'encourage you to (?:watch|check|apply)',
        r'when a position opens up',
        r'consider you for future',

        # Other indicators
        r'overwhelming response',
        r'high volume of applications',
        r'many (?:exceptional|qualified|strong) (?:applications|candidates)',
        r'other candidates',
        r'moved forward with other',
        r'pursuing other candidates',
    ],

    'Offer': [
        # Direct offer phrases (strongest indicators)
        r'pleased to offer',
        r'(?:we are |we\'re )?excited to offer',
        r'(?:we would |we\'d )?like to offer',
        r'delighted to offer',
        r'happy to offer',
        r'thrilled to offer',
        r'job offer',
        r'offer letter',
        r'offer of employment',
        r'extend(?:ing)? (?:an |a )?offer',
        r'formal offer',
        r'official offer',

        # Acceptance phrases
        r'congratulations.*(?:position|role|job|offer)',
        r'welcome to (?:the )?team',
        r'welcome aboard',
        r'accept (?:your|this|the) offer',
        r'(?:please )?sign (?:the|this|your) offer',

        # Compensation/terms
        r'compensation package',
        r'salary of',
        r'annual salary',
        r'base salary',
        r'starting salary',
        r'start date',
        r'your start date',
        r'onboarding',
        r'first day',
        r'benefits package',
        r'equity grant',
        r'stock options',
        r'signing bonus',
        r'sign-on bonus',
        r'relocation (?:package|assistance|bonus)',
    ],

    'Interviewing': [
        # Interview scheduling (strongest indicators)
        r'\binterview\b',
        r'phone screen',
        r'video (?:call|interview|chat)',
        r'zoom (?:call|meeting|interview)',
        r'teams (?:call|meeting|interview)',
        r'google meet',
        r'virtual interview',
        r'in-person interview',
        r'on-?site (?:interview|visit)',
        r'final round',
        r'next round',
        r'second round',
        r'technical round',

        # Meeting/scheduling
        r'next steps',
        r'schedule (?:a )?(?:call|meeting|time|interview)',
        r'speak with',
        r'meet with(?: our| the)? team',
        r'meeting with',
        r'chat with',
        r'connect with',
        r'would like to (?:meet|speak|talk|chat)',
        r'invite you to',
        r'like to invite',

        # Assessment/challenge
        r'(?:technical|coding) (?:assessment|challenge|test|exercise)',
        r'take-?home (?:assignment|project|exercise|test)',
        r'homework assignment',
        r'coding (?:exercise|project|challenge)',
        r'skills assessment',
        r'assessment test',

        # People involved
        r'hiring manager',
        r'recruiter',
        r'talent (?:team|acquisition)',
        r'engineering (?:team|manager|lead)',

        # Availability
        r'your availability',
        r'available (?:to|for)',
        r'please (?:provide|share|send) your availability',
        r'book (?:a )?time',
        r'pick a time',
        r'calendly',
    ],

    'Applied': [
        # Direct confirmation phrases
        r'thank you for (?:your )?(?:applying|application|interest)',
        r'thanks for applying',
        r'we.*received your application',
        r'(?:we )?received your application',
        r'application (?:has been )?(?:received|was sent|submitted)',
        r'confirm(?:ing)? (?:receipt of )?(?:your )?application',
        r'your application was sent',
        r'successfully (?:submitted|applied|received)',

        # Review/next steps (but not interview)
        r'we will (?:review|be in touch)',
        r'our team will review',
        r'we are committed to reviewing',
        r'excited to review your application',
        r'application is (?:being|under) review',
        r'currently reviewing',
        r'reviewing (?:all |your )?application',
        r'review your (?:application|background|qualifications)',

        # General appreciation (without next steps)
        r'delighted that you would consider',
        r'thank you for taking the time',
        r'appreciate your interest',
        r'glad you(?:\'re| are) interested',

        # Status update generic
        r'application (?:status|update)',
        r'status of your application',
        r'keep you (?:updated|informed|posted)',
        r'you will hear from us',
        r'we\'ll be in touch',
        r'if.*qualifications match',
        r'if.*good (?:fit|match)',
    ],
}

# =============================================================================
# COMPILED PATTERNS (for performance)
# =============================================================================

def compile_patterns(patterns: List[str], flags: int = re.IGNORECASE) -> List[Pattern]:
    """Compile a list of regex pattern strings."""
    compiled = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern, flags))
        except re.error as e:
            # Log but don't fail - skip invalid patterns
            print(f"Warning: Invalid regex pattern '{pattern}': {e}")
    return compiled


# Pre-compile patterns for performance
COMPILED_SUBJECT_COMPANY_PATTERNS = compile_patterns(SUBJECT_COMPANY_PATTERNS)
COMPILED_BODY_COMPANY_PATTERNS = compile_patterns(BODY_COMPANY_PATTERNS)
COMPILED_POSITION_PATTERNS = compile_patterns(POSITION_PATTERNS)
COMPILED_STATUS_PATTERNS: Dict[str, List[Pattern]] = {
    status: compile_patterns(patterns)
    for status, patterns in STATUS_PATTERNS.items()
}

# =============================================================================
# SENDER PATTERNS (for identifying job-related emails)
# =============================================================================

# Common sender prefixes for job-related emails
JOB_EMAIL_SENDER_PREFIXES: List[str] = [
    'recruiting',
    'recruitment',
    'recruiter',
    'talent',
    'careers',
    'career',
    'jobs',
    'job',
    'hr',
    'hiring',
    'apply',
    'applications',
    'people',
    'team',
    'noreply',
    'no-reply',
    'notifications',
]

# =============================================================================
# CLEANUP PATTERNS
# =============================================================================

# Patterns for cleaning up extracted company names
COMPANY_CLEANUP_PATTERNS: List[tuple] = [
    # Remove common suffixes
    (r'\b(?:corp|inc|llc|ltd|co|company|corporation|incorporated)\.?\s*$', ''),
    # Remove "the" prefix
    (r'^the\s+', ''),
    # Remove trailing punctuation
    (r'[.,!?;:]+$', ''),
    # Remove quotes
    (r'^["\']|["\']$', ''),
    # Normalize whitespace
    (r'\s+', ' '),
]

# Patterns for cleaning up extracted position titles
POSITION_CLEANUP_PATTERNS: List[tuple] = [
    # Remove common prefixes like "a" or "the"
    (r'^(?:a|an|the)\s+', ''),
    # Remove trailing punctuation
    (r'[.,!?;:]+$', ''),
    # Normalize whitespace
    (r'\s+', ' '),
    # Remove parenthetical content at end (often location or team)
    (r'\s*\([^)]*\)\s*$', ''),
]
