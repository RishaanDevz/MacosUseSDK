"""
MacosUseSDK Python Wrapper

A Python library for automating macOS applications using accessibility APIs.
Provides functionality for:
- Opening applications
- Traversing accessibility trees
- Simulating user input (mouse, keyboard)
- File searching
- System control (volume, brightness)
- Visual feedback and highlighting
"""

from .core import MacosSDK
from .types import (
    # Data structures
    ElementData,
    ResponseData,
    Statistics,
    AppOpenerResult,
    FileSearchOptions,
    FileSearchResult,
    FileInfo,
    OutputControllerResult,
    ActionResult,
    TraversalDiff,
    
    # Enums
    InputAction,
    PrimaryAction,
    ActionOptions,
    OutputControllerAction,
    
    # Exceptions
    MacosUseSDKError,
    AccessibilityError,
    AppNotFoundError,
    InputSimulationError,
    FileSearchError,
    OutputControllerError,
)

# Version info
__version__ = "1.0.0"
__author__ = "MacosUseSDK Team"

# Main exports
__all__ = [
    # Main class
    "MacosSDK",
    
    # Data structures
    "ElementData",
    "ResponseData", 
    "Statistics",
    "AppOpenerResult",
    "FileSearchOptions",
    "FileSearchResult",
    "FileInfo",
    "OutputControllerResult",
    "ActionResult",
    "TraversalDiff",
    
    # Enums
    "InputAction",
    "PrimaryAction", 
    "ActionOptions",
    "OutputControllerAction",
    
    # Exceptions
    "MacosUseSDKError",
    "AccessibilityError",
    "AppNotFoundError",
    "InputSimulationError",
    "FileSearchError",
    "OutputControllerError",
    
    # Version
    "__version__",
    "__author__",
] 