"""
Logging configuration for the ADC CLI package.
"""

import logging
import sys


def configure_logging(verbose=False):
    """
    Configure logging for the ADC CLI package.

    Args:
        verbose (bool): Whether to enable debug logging

    Returns:
        logging.Logger: The configured logger
    """
    logger = logging.getLogger("adc_cli")

    # Clear any existing handlers to avoid duplicate logs
    if logger.handlers:
        logger.handlers = []

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    # Set format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    # Set log level based on verbosity
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger


# Create a default logger instance
logger = configure_logging()
