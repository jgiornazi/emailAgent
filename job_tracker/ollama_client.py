"""
Ollama AI Client for Email Extraction

This module provides AI-powered extraction for job emails using Ollama.
It serves as a fallback when pattern matching produces low confidence results.

Features:
- Local AI inference via Ollama API
- Structured JSON output for extraction
- Timeout handling and retries
- Graceful degradation on failure

Requirements:
- Ollama running locally (default: http://localhost:11434)
- llama3.2:3b model downloaded: `ollama pull llama3.2:3b`
"""

import json
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any

import requests

from .extractor import ExtractionResult


# =============================================================================
# Constants
# =============================================================================

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 2
RETRY_DELAY = 5  # seconds


# =============================================================================
# Prompt Templates
# =============================================================================

EXTRACTION_PROMPT = """You are an expert at analyzing job application emails.

Analyze the following email and extract the information in JSON format.

EMAIL:
From: {sender}
Subject: {subject}
Body:
{body}

TASK:
Extract the following information from the email:
1. company_name: The name of the company (from domain, subject, or body)
2. position: The job title or position applied for (if mentioned)
3. status: One of: "Applied", "Interviewing", "Rejected", "Offer"

STATUS DEFINITIONS:
- Applied: Confirmation that application was received
- Interviewing: Request for interview, phone screen, or next steps
- Rejected: Application was unsuccessful, not moving forward
- Offer: Job offer extended

OUTPUT FORMAT (JSON only, no other text):
{{"company_name": "Company Name", "position": "Job Title", "status": "Status"}}

If you cannot determine a value, use:
- company_name: "Unknown"
- position: "Not specified"
- status: "Applied" (default)

JSON OUTPUT:"""


# =============================================================================
# Exceptions
# =============================================================================

class OllamaError(Exception):
    """Base exception for Ollama errors."""
    pass


class OllamaConnectionError(OllamaError):
    """Raised when cannot connect to Ollama server."""
    pass


class OllamaTimeoutError(OllamaError):
    """Raised when Ollama request times out."""
    pass


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns an invalid response."""
    pass


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class OllamaConfig:
    """Ollama configuration."""

    host: str = DEFAULT_OLLAMA_HOST
    model: str = DEFAULT_MODEL
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = MAX_RETRIES
    retry_delay: int = RETRY_DELAY


@dataclass
class AIExtractionResult:
    """Result from AI extraction."""

    success: bool
    company: str = "Unknown"
    position: str = "Not specified"
    status: str = "Applied"
    raw_response: str = ""
    error: Optional[str] = None


# =============================================================================
# Ollama Client
# =============================================================================

class OllamaClient:
    """
    Client for interacting with Ollama API.

    Usage:
        client = OllamaClient()
        if client.is_available():
            result = client.extract_email_info(email_dict)
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        """
        Initialize Ollama client.

        Args:
            config: Ollama configuration (uses defaults if None)
        """
        self.config = config or OllamaConfig()
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        """
        Check if Ollama server is available.

        Returns:
            True if Ollama is running and reachable
        """
        if self._available is not None:
            return self._available

        try:
            response = requests.get(
                f"{self.config.host}/api/tags",
                timeout=5
            )
            self._available = response.status_code == 200
        except requests.exceptions.RequestException:
            self._available = False

        return self._available

    def check_model_available(self) -> bool:
        """
        Check if the configured model is available.

        Returns:
            True if model is downloaded and ready
        """
        try:
            response = requests.get(
                f"{self.config.host}/api/tags",
                timeout=5
            )
            if response.status_code != 200:
                return False

            data = response.json()
            models = [m.get('name', '') for m in data.get('models', [])]

            # Check for exact match or model without tag
            model_name = self.config.model.split(':')[0]
            return any(
                self.config.model in m or model_name in m
                for m in models
            )
        except Exception:
            return False

    def generate(self, prompt: str) -> str:
        """
        Generate text using Ollama.

        Args:
            prompt: The prompt to send to Ollama

        Returns:
            Generated text response

        Raises:
            OllamaConnectionError: Cannot connect to server
            OllamaTimeoutError: Request timed out
            OllamaResponseError: Invalid response
        """
        if not self.is_available():
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.config.host}"
            )

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temp for deterministic output
                "num_predict": 256,  # Limit response length
            }
        }

        for attempt in range(self.config.max_retries + 1):
            try:
                response = requests.post(
                    f"{self.config.host}/api/generate",
                    json=payload,
                    timeout=self.config.timeout
                )

                if response.status_code != 200:
                    raise OllamaResponseError(
                        f"Ollama returned status {response.status_code}"
                    )

                data = response.json()
                return data.get('response', '')

            except requests.exceptions.Timeout:
                if attempt == self.config.max_retries:
                    raise OllamaTimeoutError(
                        f"Ollama request timed out after {self.config.timeout}s"
                    )
                import time
                time.sleep(self.config.retry_delay)

            except requests.exceptions.ConnectionError:
                raise OllamaConnectionError(
                    f"Cannot connect to Ollama at {self.config.host}"
                )

        return ""

    def extract_email_info(self, email: Dict[str, Any]) -> AIExtractionResult:
        """
        Extract job application info from email using AI.

        Args:
            email: Email dictionary with 'subject', 'from', 'body' keys

        Returns:
            AIExtractionResult with extracted information
        """
        # Build prompt
        prompt = EXTRACTION_PROMPT.format(
            sender=email.get('from', 'Unknown'),
            subject=email.get('subject', 'No subject'),
            body=email.get('body', email.get('snippet', ''))[:2000],  # Limit body length
        )

        try:
            # Generate response
            response = self.generate(prompt)

            # Parse JSON from response
            result = self._parse_json_response(response)
            result.raw_response = response

            return result

        except OllamaConnectionError as e:
            return AIExtractionResult(
                success=False,
                error=f"Connection error: {e}"
            )
        except OllamaTimeoutError as e:
            return AIExtractionResult(
                success=False,
                error=f"Timeout: {e}"
            )
        except OllamaResponseError as e:
            return AIExtractionResult(
                success=False,
                error=f"Response error: {e}"
            )
        except Exception as e:
            return AIExtractionResult(
                success=False,
                error=f"Unexpected error: {e}"
            )

    def _parse_json_response(self, response: str) -> AIExtractionResult:
        """
        Parse JSON from Ollama response.

        Handles various response formats including:
        - Clean JSON
        - JSON embedded in text
        - JSON in code blocks

        Args:
            response: Raw response text from Ollama

        Returns:
            AIExtractionResult with parsed data
        """
        # Try to find JSON in response
        json_match = None

        # Pattern 1: Look for JSON object
        patterns = [
            r'\{[^{}]*"company_name"[^{}]*\}',
            r'\{[^{}]*"company"[^{}]*\}',
            r'```json?\s*(\{.*?\})\s*```',
            r'\{.*?\}',
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                json_str = match.group(1) if match.lastindex else match.group(0)
                try:
                    data = json.loads(json_str)
                    if isinstance(data, dict):
                        json_match = data
                        break
                except json.JSONDecodeError:
                    continue

        if not json_match:
            # Fallback: try parsing entire response
            try:
                json_match = json.loads(response.strip())
            except json.JSONDecodeError:
                return AIExtractionResult(
                    success=False,
                    error="Could not parse JSON from response"
                )

        # Extract fields with fallbacks
        company = json_match.get('company_name') or json_match.get('company') or "Unknown"
        position = json_match.get('position') or json_match.get('job_title') or "Not specified"
        status = json_match.get('status') or "Applied"

        # Validate status
        valid_statuses = ["Applied", "Interviewing", "Rejected", "Offer"]
        if status not in valid_statuses:
            # Try to normalize
            status_lower = status.lower()
            if 'interview' in status_lower:
                status = "Interviewing"
            elif 'reject' in status_lower or 'denied' in status_lower:
                status = "Rejected"
            elif 'offer' in status_lower:
                status = "Offer"
            else:
                status = "Applied"

        return AIExtractionResult(
            success=True,
            company=company,
            position=position,
            status=status,
        )


# =============================================================================
# Helper Functions
# =============================================================================

def create_ollama_client(config: Dict[str, Any]) -> OllamaClient:
    """
    Create OllamaClient from configuration dictionary.

    Args:
        config: Configuration dictionary with 'ollama' section

    Returns:
        Configured OllamaClient
    """
    ollama_config = config.get('ollama', {})

    return OllamaClient(OllamaConfig(
        host=ollama_config.get('host', DEFAULT_OLLAMA_HOST),
        model=ollama_config.get('model', DEFAULT_MODEL),
        timeout=ollama_config.get('timeout', DEFAULT_TIMEOUT),
        max_retries=ollama_config.get('max_retries', MAX_RETRIES),
        retry_delay=ollama_config.get('retry_delay', RETRY_DELAY),
    ))


def ai_extract_email(
    email: Dict[str, Any],
    pattern_result: ExtractionResult,
    client: Optional[OllamaClient] = None,
) -> ExtractionResult:
    """
    Enhance extraction result with AI.

    Uses AI to fill in missing or low-confidence fields from pattern extraction.

    Args:
        email: Email dictionary
        pattern_result: Result from pattern matching
        client: Optional OllamaClient (creates new one if None)

    Returns:
        Enhanced ExtractionResult
    """
    if client is None:
        client = OllamaClient()

    if not client.is_available():
        # Return original result if Ollama not available
        pattern_result.extraction_method = "pattern_only"
        return pattern_result

    # Get AI extraction
    ai_result = client.extract_email_info(email)

    if not ai_result.success:
        # AI failed, use pattern result
        pattern_result.extraction_method = "ai_failed"
        return pattern_result

    # Merge results - AI fills in missing fields
    merged = ExtractionResult(
        email_id=pattern_result.email_id,
        email_date=pattern_result.email_date,
        extraction_method="hybrid",
    )

    # Company: prefer domain extraction, then AI
    if pattern_result.company != "Unknown" and pattern_result.company_source == "domain":
        merged.company = pattern_result.company
        merged.company_source = pattern_result.company_source
    elif ai_result.company != "Unknown":
        merged.company = ai_result.company
        merged.company_source = "ai"
    else:
        merged.company = pattern_result.company
        merged.company_source = pattern_result.company_source

    # Position: prefer AI if pattern didn't find one
    if pattern_result.position != "Not specified":
        merged.position = pattern_result.position
        merged.position_source = pattern_result.position_source
    elif ai_result.position != "Not specified":
        merged.position = ai_result.position
        merged.position_source = "ai"
    else:
        merged.position = pattern_result.position
        merged.position_source = pattern_result.position_source

    # Status: use AI if pattern confidence was low
    if pattern_result.status_matches >= 2:
        merged.status = pattern_result.status
        merged.status_matches = pattern_result.status_matches
    else:
        merged.status = ai_result.status
        merged.status_matches = 1  # AI counts as 1 match

    # Recalculate confidence
    from .extractor import calculate_confidence
    merged.confidence, merged.confidence_score = calculate_confidence(merged)

    return merged


def check_ollama_status(host: str = DEFAULT_OLLAMA_HOST) -> Dict[str, Any]:
    """
    Check Ollama server status.

    Args:
        host: Ollama server URL

    Returns:
        Status dictionary with 'available', 'models', 'error' keys
    """
    result = {
        "available": False,
        "host": host,
        "models": [],
        "error": None,
    }

    try:
        response = requests.get(f"{host}/api/tags", timeout=5)
        if response.status_code == 200:
            result["available"] = True
            data = response.json()
            result["models"] = [m.get('name') for m in data.get('models', [])]
        else:
            result["error"] = f"Server returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        result["error"] = f"Cannot connect to {host}"
    except requests.exceptions.Timeout:
        result["error"] = "Connection timed out"
    except Exception as e:
        result["error"] = str(e)

    return result
