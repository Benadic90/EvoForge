import re

import structlog

logger = structlog.get_logger(__name__)

class SecretDetector:
    def __init__(self):
        # Basic patterns for common secrets
        self.patterns = {
            "aws_access_key": re.compile(r"(?i)aws_access_key_id\s*=?\s*['\"]?(AKIA[0-9A-Z]{16})['\"]?"),
            "aws_secret_key": re.compile(r"(?i)aws_secret_access_key\s*=?\s*['\"]?([0-9a-zA-Z/+]{40})['\"]?"),
            "github_token": re.compile(r"(?i)gh[p|o|u|s|r]_[0-9a-zA-Z]{36}"),
            "generic_api_key": re.compile(r"(?i)(?:api_key|apikey|secret|token|password|pwd)\s*[:=]\s*['\"]?([a-zA-Z0-9\-_]{16,})['\"]?"),
            "private_key": re.compile(r"-----BEGIN [A-Z]+ PRIVATE KEY-----")
        }

    def scan_text(self, text: str) -> list[tuple[str, str]]:
        """
        Scans text for secrets and returns a list of (secret_type, matched_string).
        """
        findings = []
        for secret_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                # If the regex has groups, match is the string. Otherwise it's the whole match.
                matched_str = match if isinstance(match, str) else match[0]
                findings.append((secret_type, matched_str))
                
        if findings:
            logger.warning("secrets_detected", count=len(findings), types=[f[0] for f in findings])
            
        return findings

    def redact(self, text: str) -> str:
        """Redacts detected secrets from text."""
        redacted_text = text
        for secret_type, pattern in self.patterns.items():
            redacted_text = pattern.sub(f"[{secret_type.upper()}_REDACTED]", redacted_text)
        return redacted_text
