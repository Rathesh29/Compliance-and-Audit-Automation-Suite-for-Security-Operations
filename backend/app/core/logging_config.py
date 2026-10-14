import logging
import sys
import json
from datetime import datetime, timezone


class SanitizedFormatter(logging.Formatter):
    """Structured JSON & Sanitized Formatter that never leaks credentials."""
    SENSITIVE_KEYS = {"password", "token", "jwt", "secret", "mfa_secret", "password_hash"}

    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "props"):
            props = getattr(record, "props")
            if isinstance(props, dict):
                sanitized_props = {}
                for k, v in props.items():
                    if any(s in k.lower() for s in self.SENSITIVE_KEYS):
                        sanitized_props[k] = "[REDACTED]"
                    else:
                        sanitized_props[k] = v
                log_obj["data"] = sanitized_props
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging():
    logger = logging.getLogger("compliance_suite")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(SanitizedFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


logger = setup_logging()
