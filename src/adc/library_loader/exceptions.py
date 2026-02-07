"""
Exception classes for Universal Library Loader.

This module defines custom exceptions used throughout the library loader
to provide clear, actionable error messages.
"""

# ADC-IMPLEMENTS: <ull-impl-02>


class LibraryLoadError(Exception):
    """Raised when library cannot be loaded."""
    pass


class InterfaceConformanceError(Exception):
    """Raised when library doesn't match expected interface."""
    pass
