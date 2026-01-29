"""
Job Tracker module for EmailAgent (Feature 2).

Provides job application tracking functionality:
- Email extraction (company, position, status)
- Pattern matching with keyword patterns
- Optional AI extraction via Ollama
- Excel storage with status hierarchy
- Status classification and confidence scoring
"""

from .job_patterns import (
    GENERIC_PROVIDERS,
    SUBJECT_COMPANY_PATTERNS,
    BODY_COMPANY_PATTERNS,
    POSITION_PATTERNS,
    POSITION_KEYWORDS,
    STATUS_HIERARCHY,
    STATUS_PATTERNS,
)

from .extractor import (
    ExtractionResult,
    extract_company,
    extract_company_from_domain,
    extract_company_from_subject,
    extract_company_from_body,
    extract_position,
    extract_position_from_subject,
    extract_position_from_body,
    pattern_match_extraction,
    extract_email_info,
    calculate_confidence,
    should_use_ai,
)

from .classifier import (
    StatusClassificationResult,
    StatusUpdateResult,
    classify_status,
    classify_email,
    can_update_status,
    get_status_level,
    create_conflict_note,
    is_deletable_status,
    is_protected_status,
    validate_status,
    normalize_status,
)

from .excel_storage import (
    ExcelStorage,
    JobApplication,
    ExcelUpdateResult,
    create_excel_storage,
    format_summary_table,
    COLUMNS,
    HEADERS,
)

from .ollama_client import (
    OllamaClient,
    OllamaConfig,
    OllamaError,
    OllamaConnectionError,
    OllamaTimeoutError,
    AIExtractionResult,
    create_ollama_client,
    ai_extract_email,
    check_ollama_status,
)

__all__ = [
    # Patterns
    'GENERIC_PROVIDERS',
    'SUBJECT_COMPANY_PATTERNS',
    'BODY_COMPANY_PATTERNS',
    'POSITION_PATTERNS',
    'POSITION_KEYWORDS',
    'STATUS_HIERARCHY',
    'STATUS_PATTERNS',

    # Extractor
    'ExtractionResult',
    'extract_company',
    'extract_company_from_domain',
    'extract_company_from_subject',
    'extract_company_from_body',
    'extract_position',
    'extract_position_from_subject',
    'extract_position_from_body',
    'pattern_match_extraction',
    'extract_email_info',
    'calculate_confidence',
    'should_use_ai',

    # Classifier
    'StatusClassificationResult',
    'StatusUpdateResult',
    'classify_status',
    'classify_email',
    'can_update_status',
    'get_status_level',
    'create_conflict_note',
    'is_deletable_status',
    'is_protected_status',
    'validate_status',
    'normalize_status',

    # Excel Storage
    'ExcelStorage',
    'JobApplication',
    'ExcelUpdateResult',
    'create_excel_storage',
    'format_summary_table',
    'COLUMNS',
    'HEADERS',

    # Ollama Client
    'OllamaClient',
    'OllamaConfig',
    'OllamaError',
    'OllamaConnectionError',
    'OllamaTimeoutError',
    'AIExtractionResult',
    'create_ollama_client',
    'ai_extract_email',
    'check_ollama_status',
]
