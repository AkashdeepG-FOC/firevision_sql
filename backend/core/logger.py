"""
FireVision Backend – Centralized Logging Configuration
Uses loguru for structured, levelled, rotating file logs.
"""
import sys
import os
from loguru import logger

# ─── Log directory ────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ─── Remove default handler ───────────────────────────────────────────────────
logger.remove()

# ─── Console handler (coloured, human-readable) ───────────────────────────────
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> – "
        "<level>{message}</level>"
    ),
)

# ─── Rotating file handler – general application log ─────────────────────────
logger.add(
    os.path.join(LOG_DIR, "firevision_{time:YYYY-MM-DD}.log"),
    level="DEBUG",
    rotation="00:00",          # New file every midnight
    retention="30 days",       # Keep 30 days of logs
    compression="zip",
    enqueue=True,              # Non-blocking (thread-safe)
    format=(
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
        "{name}:{function}:{line} – {message}"
    ),
)

# ─── Separate file handler – ERROR / CRITICAL only ───────────────────────────
logger.add(
    os.path.join(LOG_DIR, "errors_{time:YYYY-MM-DD}.log"),
    level="ERROR",
    rotation="50 MB",
    retention="90 days",
    compression="zip",
    enqueue=True,
    backtrace=True,            # Full stack trace on errors
    diagnose=True,             # Variable values in tracebacks
    format=(
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
        "{name}:{function}:{line} – {message}\n{exception}"
    ),
)

# ─── Security-specific audit log ─────────────────────────────────────────────
logger.add(
    os.path.join(LOG_DIR, "security_audit_{time:YYYY-MM-DD}.log"),
    level="WARNING",
    rotation="10 MB",
    retention="365 days",      # Audit logs kept for a year
    compression="zip",
    enqueue=True,
    filter=lambda record: "SECURITY" in record["extra"],
    format=(
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | AUDIT | "
        "{extra[SECURITY]} | {message}"
    ),
)


def get_logger(name: str):
    """Return a bound logger for a specific module."""
    return logger.bind(module=name)


def log_security_event(event_type: str, message: str):
    """Emit a structured security-audit log entry."""
    logger.bind(SECURITY=event_type).warning(message)
