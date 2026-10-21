"""Logging configuration for the P2P file sharing application."""

import logging
import sys


def setup_logging(level: str = "INFO", name: str = "p2p") -> logging.Logger:
    """Configure and return a structured logger.

    Format: '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'

    Args:
        level: Logging level name (e.g. 'DEBUG', 'INFO', 'WARNING', 'ERROR').
        name: Name of the logger instance.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
