"""
Configuration management for EmailAgent.

Handles loading configuration from:
1. Default values
2. config.yaml file
3. Environment variables

Priority: CLI flags > Environment Variables > config.yaml > defaults
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv


# Load .env file if present
load_dotenv()


def get_default_config_dir() -> Path:
    """Get the default configuration directory."""
    return Path.home() / ".emailagent"


def get_default_config_path() -> Path:
    """Get the default configuration file path."""
    return get_default_config_dir() / "config.yaml"


@dataclass
class GmailConfig:
    """Gmail API configuration."""

    credentials_path: Path = field(
        default_factory=lambda: get_default_config_dir() / "credentials.json"
    )
    token_path: Path = field(
        default_factory=lambda: get_default_config_dir() / "token.json"
    )
    max_results_per_query: int = 10000
    batch_size: int = 100
    requests_per_second: int = 10


@dataclass
class ExtractionConfig:
    """Extraction configuration."""

    use_ai: bool = False
    confidence_threshold: float = 0.7
    ai_triggers_low_confidence: bool = True
    ai_triggers_unknown_company: bool = True
    ai_triggers_unclear_status: bool = True


@dataclass
class OllamaConfig:
    """Ollama AI configuration."""

    host: str = "http://localhost:11434"
    model: str = "llama3.2:3b"
    timeout: int = 30
    max_retries: int = 2
    retry_delay: int = 5


@dataclass
class ExcelConfig:
    """Excel storage configuration."""

    file_path: Path = field(default_factory=lambda: Path.home() / "job_applications.xlsx")
    sheet_name: str = "Applications"
    auto_backup: bool = True
    backup_directory: Path = field(
        default_factory=lambda: get_default_config_dir() / "backups"
    )
    backup_retention_days: int = 7
    save_after_n_emails: int = 100
    use_conditional_formatting: bool = True
    freeze_header: bool = True


@dataclass
class DeletionConfig:
    """Deletion configuration."""

    delete_applied: bool = True
    delete_rejected: bool = True
    delete_interviewing: bool = False
    delete_offer: bool = False
    safety_keywords: list[str] = field(default_factory=lambda: [
        "interview", "phone screen", "video call", "next steps", "schedule",
        "meet with", "assessment", "take-home", "offer", "compensation",
        "urgent", "deadline", "password", "account", "verify"
    ])
    never_delete_starred: bool = True
    never_delete_with_attachments: bool = False
    never_delete_conflicts: bool = True
    minimum_age_days: int = 0
    batch_size: int = 50
    delay_between_deletes: float = 0.1
    require_confirmation: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    log_directory: Path = field(
        default_factory=lambda: get_default_config_dir() / "logs"
    )
    log_file_pattern: str = "emailagent_{date}.log"
    max_log_size_mb: int = 10
    retention_days: int = 30
    log_extractions: bool = True
    log_classifications: bool = True
    log_deletions: bool = True
    log_api_calls: bool = False


@dataclass
class CLIConfig:
    """CLI display configuration."""

    use_colors: bool = True
    show_progress: bool = True
    verbose: bool = False
    table_style: str = "simple"
    paginate: bool = True
    items_per_page: int = 50


@dataclass
class AdvancedConfig:
    """Advanced configuration."""

    parallel_extraction: bool = False
    max_workers: int = 4
    cache_enabled: bool = True
    cache_directory: Path = field(
        default_factory=lambda: get_default_config_dir() / "cache"
    )
    cache_ttl_hours: int = 24
    max_body_length: int = 5000


@dataclass
class Config:
    """Main configuration container."""

    gmail: GmailConfig = field(default_factory=GmailConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    excel: ExcelConfig = field(default_factory=ExcelConfig)
    deletion: DeletionConfig = field(default_factory=DeletionConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    cli: CLIConfig = field(default_factory=CLIConfig)
    advanced: AdvancedConfig = field(default_factory=AdvancedConfig)


def _expand_path(value: Any) -> Any:
    """Expand ~ in paths."""
    if isinstance(value, str) and value.startswith("~"):
        return Path(value).expanduser()
    return value


def _get_env_value(key: str, default: Any = None) -> Optional[str]:
    """Get value from environment variable."""
    env_key = f"EMAILAGENT_{key.upper()}"
    return os.environ.get(env_key, default)


def _apply_env_overrides(config: Config) -> None:
    """Apply environment variable overrides to config."""
    # Gmail
    if val := _get_env_value("GMAIL_CREDENTIALS"):
        config.gmail.credentials_path = Path(val).expanduser()
    if val := _get_env_value("GMAIL_TOKEN"):
        config.gmail.token_path = Path(val).expanduser()

    # Extraction
    if val := _get_env_value("USE_AI"):
        config.extraction.use_ai = val.lower() in ("true", "1", "yes")
    if val := _get_env_value("CONFIDENCE_THRESHOLD"):
        config.extraction.confidence_threshold = float(val)

    # Ollama
    if val := _get_env_value("OLLAMA_HOST"):
        config.ollama.host = val
    if val := _get_env_value("OLLAMA_MODEL"):
        config.ollama.model = val

    # Excel
    if val := _get_env_value("EXCEL_PATH"):
        config.excel.file_path = Path(val).expanduser()

    # Logging
    if val := _get_env_value("LOG_LEVEL"):
        config.logging.level = val.upper()
    if val := _get_env_value("LOG_DIR"):
        config.logging.log_directory = Path(val).expanduser()


def _parse_gmail_config(data: dict) -> GmailConfig:
    """Parse Gmail configuration from dict."""
    config = GmailConfig()
    if "credentials_path" in data:
        config.credentials_path = Path(data["credentials_path"]).expanduser()
    if "token_path" in data:
        config.token_path = Path(data["token_path"]).expanduser()
    if "max_results_per_query" in data:
        config.max_results_per_query = int(data["max_results_per_query"])
    if "batch_size" in data:
        config.batch_size = int(data["batch_size"])
    if "requests_per_second" in data:
        config.requests_per_second = int(data["requests_per_second"])
    return config


def _parse_extraction_config(data: dict) -> ExtractionConfig:
    """Parse extraction configuration from dict."""
    config = ExtractionConfig()
    if "use_ai" in data:
        config.use_ai = bool(data["use_ai"])
    if "confidence_threshold" in data:
        config.confidence_threshold = float(data["confidence_threshold"])
    if "ai_triggers" in data:
        triggers = data["ai_triggers"]
        if "low_confidence" in triggers:
            config.ai_triggers_low_confidence = bool(triggers["low_confidence"])
        if "unknown_company" in triggers:
            config.ai_triggers_unknown_company = bool(triggers["unknown_company"])
        if "unclear_status" in triggers:
            config.ai_triggers_unclear_status = bool(triggers["unclear_status"])
    return config


def _parse_ollama_config(data: dict) -> OllamaConfig:
    """Parse Ollama configuration from dict."""
    config = OllamaConfig()
    if "host" in data:
        config.host = str(data["host"])
    if "model" in data:
        config.model = str(data["model"])
    if "timeout" in data:
        config.timeout = int(data["timeout"])
    if "max_retries" in data:
        config.max_retries = int(data["max_retries"])
    if "retry_delay" in data:
        config.retry_delay = int(data["retry_delay"])
    return config


def _parse_excel_config(data: dict) -> ExcelConfig:
    """Parse Excel configuration from dict."""
    config = ExcelConfig()
    if "file_path" in data:
        config.file_path = Path(data["file_path"]).expanduser()
    if "sheet_name" in data:
        config.sheet_name = str(data["sheet_name"])
    if "auto_backup" in data:
        config.auto_backup = bool(data["auto_backup"])
    if "backup_directory" in data:
        config.backup_directory = Path(data["backup_directory"]).expanduser()
    if "backup_retention_days" in data:
        config.backup_retention_days = int(data["backup_retention_days"])
    if "save_after_n_emails" in data:
        config.save_after_n_emails = int(data["save_after_n_emails"])
    if "use_conditional_formatting" in data:
        config.use_conditional_formatting = bool(data["use_conditional_formatting"])
    if "freeze_header" in data:
        config.freeze_header = bool(data["freeze_header"])
    return config


def _parse_deletion_config(data: dict) -> DeletionConfig:
    """Parse deletion configuration from dict."""
    config = DeletionConfig()
    if "delete_applied" in data:
        config.delete_applied = bool(data["delete_applied"])
    if "delete_rejected" in data:
        config.delete_rejected = bool(data["delete_rejected"])
    if "delete_interviewing" in data:
        config.delete_interviewing = bool(data["delete_interviewing"])
    if "delete_offer" in data:
        config.delete_offer = bool(data["delete_offer"])
    if "safety_keywords" in data:
        config.safety_keywords = list(data["safety_keywords"])
    if "never_delete_starred" in data:
        config.never_delete_starred = bool(data["never_delete_starred"])
    if "never_delete_with_attachments" in data:
        config.never_delete_with_attachments = bool(data["never_delete_with_attachments"])
    if "never_delete_conflicts" in data:
        config.never_delete_conflicts = bool(data["never_delete_conflicts"])
    if "minimum_age_days" in data:
        config.minimum_age_days = int(data["minimum_age_days"])
    if "batch_size" in data:
        config.batch_size = int(data["batch_size"])
    if "delay_between_deletes" in data:
        config.delay_between_deletes = float(data["delay_between_deletes"])
    if "require_confirmation" in data:
        config.require_confirmation = bool(data["require_confirmation"])
    return config


def _parse_logging_config(data: dict) -> LoggingConfig:
    """Parse logging configuration from dict."""
    config = LoggingConfig()
    if "level" in data:
        config.level = str(data["level"]).upper()
    if "log_directory" in data:
        config.log_directory = Path(data["log_directory"]).expanduser()
    if "log_file_pattern" in data:
        config.log_file_pattern = str(data["log_file_pattern"])
    if "max_log_size_mb" in data:
        config.max_log_size_mb = int(data["max_log_size_mb"])
    if "retention_days" in data:
        config.retention_days = int(data["retention_days"])
    if "log_extractions" in data:
        config.log_extractions = bool(data["log_extractions"])
    if "log_classifications" in data:
        config.log_classifications = bool(data["log_classifications"])
    if "log_deletions" in data:
        config.log_deletions = bool(data["log_deletions"])
    if "log_api_calls" in data:
        config.log_api_calls = bool(data["log_api_calls"])
    return config


def _parse_cli_config(data: dict) -> CLIConfig:
    """Parse CLI configuration from dict."""
    config = CLIConfig()
    if "use_colors" in data:
        config.use_colors = bool(data["use_colors"])
    if "show_progress" in data:
        config.show_progress = bool(data["show_progress"])
    if "verbose" in data:
        config.verbose = bool(data["verbose"])
    if "table_style" in data:
        config.table_style = str(data["table_style"])
    if "paginate" in data:
        config.paginate = bool(data["paginate"])
    if "items_per_page" in data:
        config.items_per_page = int(data["items_per_page"])
    return config


def _parse_advanced_config(data: dict) -> AdvancedConfig:
    """Parse advanced configuration from dict."""
    config = AdvancedConfig()
    if "parallel_extraction" in data:
        config.parallel_extraction = bool(data["parallel_extraction"])
    if "max_workers" in data:
        config.max_workers = int(data["max_workers"])
    if "cache_enabled" in data:
        config.cache_enabled = bool(data["cache_enabled"])
    if "cache_directory" in data:
        config.cache_directory = Path(data["cache_directory"]).expanduser()
    if "cache_ttl_hours" in data:
        config.cache_ttl_hours = int(data["cache_ttl_hours"])
    if "max_body_length" in data:
        config.max_body_length = int(data["max_body_length"])
    return config


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from file and environment variables.

    Args:
        config_path: Path to config file. If None, uses default location.

    Returns:
        Config object with all settings.
    """
    config = Config()

    # Determine config path
    if config_path is None:
        config_path = get_default_config_path()
    else:
        config_path = Path(config_path).expanduser()

    # Load from YAML if exists
    if config_path.exists():
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}

        if "gmail" in data:
            config.gmail = _parse_gmail_config(data["gmail"])
        if "extraction" in data:
            config.extraction = _parse_extraction_config(data["extraction"])
        if "ollama" in data:
            config.ollama = _parse_ollama_config(data["ollama"])
        if "excel" in data:
            config.excel = _parse_excel_config(data["excel"])
        if "deletion" in data:
            config.deletion = _parse_deletion_config(data["deletion"])
        if "logging" in data:
            config.logging = _parse_logging_config(data["logging"])
        if "cli" in data:
            config.cli = _parse_cli_config(data["cli"])
        if "advanced" in data:
            config.advanced = _parse_advanced_config(data["advanced"])

    # Apply environment variable overrides
    _apply_env_overrides(config)

    return config


def ensure_directories(config: Config) -> None:
    """Ensure all required directories exist."""
    directories = [
        get_default_config_dir(),
        config.logging.log_directory,
        config.excel.backup_directory,
        config.advanced.cache_directory,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def validate_config(config: Config) -> tuple[bool, list[str], list[str]]:
    """
    Validate configuration.

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Check credentials path
    if not config.gmail.credentials_path.exists():
        errors.append(f"Gmail credentials not found: {config.gmail.credentials_path}")

    # Check Excel directory writable
    excel_dir = config.excel.file_path.parent
    if not excel_dir.exists():
        try:
            excel_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            errors.append(f"Cannot create Excel directory: {excel_dir}")

    # Check log directory
    try:
        config.logging.log_directory.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        errors.append(f"Cannot create log directory: {config.logging.log_directory}")

    # Check Ollama if AI enabled
    if config.extraction.use_ai:
        import requests
        try:
            response = requests.get(f"{config.ollama.host}/api/tags", timeout=5)
            if response.status_code != 200:
                warnings.append(f"Ollama not reachable at {config.ollama.host}")
        except Exception:
            warnings.append(f"Cannot connect to Ollama at {config.ollama.host}")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def save_default_config(config_path: Optional[Path] = None) -> Path:
    """
    Save default configuration to file.

    Args:
        config_path: Path to save config. If None, uses default location.

    Returns:
        Path where config was saved.
    """
    if config_path is None:
        config_path = get_default_config_path()
    else:
        config_path = Path(config_path).expanduser()

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate default config YAML content
    default_yaml = """# ============================================================================
# EmailAgent Configuration File
# ============================================================================
# This file controls all aspects of the job email tracker.
# Edit values below to customize behavior.

# ----------------------------------------------------------------------------
# Gmail Configuration
# ----------------------------------------------------------------------------
gmail:
  credentials_path: ~/.emailagent/credentials.json
  token_path: ~/.emailagent/token.json
  max_results_per_query: 10000
  batch_size: 100
  requests_per_second: 10

# ----------------------------------------------------------------------------
# Extraction Configuration
# ----------------------------------------------------------------------------
extraction:
  use_ai: false
  confidence_threshold: 0.7
  ai_triggers:
    low_confidence: true
    unknown_company: true
    unclear_status: true

# ----------------------------------------------------------------------------
# Ollama Configuration (only used if extraction.use_ai = true)
# ----------------------------------------------------------------------------
ollama:
  host: http://localhost:11434
  model: llama3.2:3b
  timeout: 30
  max_retries: 2
  retry_delay: 5

# ----------------------------------------------------------------------------
# Excel Configuration
# ----------------------------------------------------------------------------
excel:
  file_path: ~/job_applications.xlsx
  sheet_name: Applications
  auto_backup: true
  backup_directory: ~/.emailagent/backups/
  backup_retention_days: 7
  save_after_n_emails: 100
  use_conditional_formatting: true
  freeze_header: true

# ----------------------------------------------------------------------------
# Deletion Configuration
# ----------------------------------------------------------------------------
deletion:
  delete_applied: true
  delete_rejected: true
  delete_interviewing: false
  delete_offer: false
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
  never_delete_starred: true
  never_delete_with_attachments: false
  never_delete_conflicts: true
  minimum_age_days: 0
  batch_size: 50
  delay_between_deletes: 0.1
  require_confirmation: true

# ----------------------------------------------------------------------------
# Logging Configuration
# ----------------------------------------------------------------------------
logging:
  level: INFO
  log_directory: ~/.emailagent/logs/
  log_file_pattern: emailagent_{date}.log
  max_log_size_mb: 10
  retention_days: 30
  log_extractions: true
  log_classifications: true
  log_deletions: true
  log_api_calls: false

# ----------------------------------------------------------------------------
# CLI Display Settings
# ----------------------------------------------------------------------------
cli:
  use_colors: true
  show_progress: true
  verbose: false
  table_style: simple
  paginate: true
  items_per_page: 50

# ----------------------------------------------------------------------------
# Advanced Settings
# ----------------------------------------------------------------------------
advanced:
  parallel_extraction: false
  max_workers: 4
  cache_enabled: true
  cache_directory: ~/.emailagent/cache/
  cache_ttl_hours: 24
  max_body_length: 5000
"""

    with open(config_path, "w") as f:
        f.write(default_yaml)

    return config_path
