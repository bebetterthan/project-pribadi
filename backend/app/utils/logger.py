from loguru import logger
import sys
import os

# Remove default handler
logger.remove()

# Determine log level from environment (default: DEBUG for comprehensive logging)
log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()

# CRITICAL: Console output - BOTH stdout AND stderr for maximum visibility
# This ensures ALL logs appear in console regardless of stream
logger.add(
    sys.stdout,  # Standard output
    level="DEBUG",  # Show EVERYTHING
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
    backtrace=True,  # Show full traceback on errors
    diagnose=True,   # Show variable values in traceback
    enqueue=False,   # Disable queue for immediate output
    catch=True       # Catch errors in logging itself
)

logger.add(
    sys.stderr,  # Error output
    level="WARNING",  # Warnings and above to stderr
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
    backtrace=True,
    diagnose=True,
    enqueue=False,
    catch=True
)

# File output (production) - always at DEBUG level for post-mortem analysis
logger.add(
    "logs/app.log",
    rotation="100 MB",
    retention="30 days",
    compression="zip",
    level="DEBUG",  # Capture everything in file
    backtrace=True,
    diagnose=True,
    enqueue=False  # Immediate write
)

# Additional file for errors only (easier to review)
logger.add(
    "logs/error_debug.log",
    rotation="50 MB",
    retention="14 days",
    level="ERROR",  # Only errors and above
    backtrace=True,
    diagnose=True,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
    enqueue=False
)

# Test logging on import
logger.info("="*60)
logger.info("[LOGGER] Loguru initialized with DEBUG level")
logger.info("[LOGGER] Console output: ENABLED (stdout + stderr)")
logger.info("[LOGGER] File output: logs/app.log + logs/error_debug.log")
logger.info("="*60)


def mask_api_key(key: str) -> str:
    """Mask API key for logging"""
    if not key or len(key) < 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"
