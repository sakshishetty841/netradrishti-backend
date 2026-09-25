import logging
import sys

def setup_logging():
    logger = logging.getLogger("netradrishti")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

logger = setup_logging()

def sanitize_log_data(data: dict) -> dict:
    """Strip sensitive fields before logging"""
    sensitive_keys = {"password", "token", "access_token", "refresh_token", "otp", "secret"}
    sanitized = {}
    for k, v in data.items():
        if any(sk in k.lower() for sk in sensitive_keys):
            sanitized[k] = "******"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_log_data(v)
        else:
            sanitized[k] = v
    return sanitized
