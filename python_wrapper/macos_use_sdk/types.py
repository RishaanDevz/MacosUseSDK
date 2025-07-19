"""
Type definitions for MacosUseSDK Python wrapper

This module contains all the data structures, enums, and exceptions
that mirror the Swift SDK's public API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


# === Exceptions ===

class MacosUseSDKError(Exception):
    """Base exception for all MacosUseSDK errors."""
    pass


class AccessibilityError(MacosUseSDKError):
    """Raised when accessibility permissions are denied or unavailable."""
    pass


class AppNotFoundError(MacosUseSDKError):
    """Raised when a requested application cannot be found or opened."""
    pass


class InputSimulationError(MacosUseSDKError):
    """Raised when input simulation (mouse, keyboard) fails."""
    pass


class FileSearchError(MacosUseSDKError):
    """Raised when file search operations fail."""
    pass


class OutputControllerError(MacosUseSDKError):
    """Raised when system output control operations fail."""
    pass


# === Data Structures ===

@dataclass
class ElementData:
    """Represents an accessibility element from the UI tree."""
    role: str
    text: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None


@dataclass 
class BrowserElementData:
    """Represents a browser-specific element extracted from HTML."""
    tag_name: str
    id: Optional[str] = None
    class_name: Optional[str] = None
    text: Optional[str] = None
    value: Optional[str] = None
    placeholder: Optional[str] = None
    aria_label: Optional[str] = None
    role: Optional[str] = None
    href: Optional[str] = None
    src: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None


@dataclass
class BrowserPageData:
    """Contains browser page information and extracted elements."""
    url: Optional[str] = None
    title: Optional[str] = None
    elements: List[BrowserElementData] = field(default_factory=list)


@dataclass
class Statistics:
    """Statistics about the accessibility tree traversal."""
    count: int = 0
    excluded_count: int = 0
    excluded_non_interactable: int = 0
    excluded_no_text: int = 0
    with_text_count: int = 0
    without_text_count: int = 0
    visible_elements_count: int = 0
    role_counts: Dict[str, int] = field(default_factory=dict)
    browser_elements_count: int = 0


@dataclass
class ResponseData:
    """Response from accessibility tree traversal."""
    app_name: str
    elements: List[ElementData]
    stats: Statistics
    processing_time_seconds: str
    is_browser: bool = False
    browser_data: Optional[BrowserPageData] = None


@dataclass
class AppOpenerResult:
    """Result from opening an application."""
    pid: int
    app_name: str
    processing_time_seconds: str


@dataclass
class FileInfo:
    """Information about a file found in search."""
    path: str
    name: str
    size: int
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    file_type: str = ""


@dataclass
class FileSearchOptions:
    """Options for file search operations."""
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search_locations: List[str] = field(default_factory=list)
    max_results: int = 100

    def __post_init__(self):
        if not self.search_locations:
            import os
            self.search_locations = [os.path.expanduser("~")]


@dataclass
class FileSearchResult:
    """Result from file search operation."""
    files: List[FileInfo]
    total_count: int
    execution_time: str


@dataclass
class OutputControllerResult:
    """Result from system output control operations."""
    value: Optional[float]
    message: str


@dataclass
class AttributeChangeDetail:
    """Details about a change in an accessibility element attribute."""
    attribute_name: str
    added_text: Optional[str] = None
    removed_text: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None


@dataclass
class ElementChange:
    """Represents a change to an accessibility element."""
    ax_element: str
    change_type: str  # "added", "removed", "modified"
    changes: List[AttributeChangeDetail] = field(default_factory=list)


@dataclass
class TraversalDiff:
    """Difference between two accessibility tree traversals."""
    added_elements: List[ElementData] = field(default_factory=list)
    removed_elements: List[ElementData] = field(default_factory=list)
    modified_elements: List[ElementChange] = field(default_factory=list)
    stats_before: Optional[Statistics] = None
    stats_after: Optional[Statistics] = None


@dataclass
class ActionResult:
    """Result from performing a coordinated action."""
    open_result: Optional[AppOpenerResult] = None
    traversal_pid: Optional[int] = None
    traversal_before: Optional[ResponseData] = None
    traversal_after: Optional[ResponseData] = None
    traversal_diff: Optional[TraversalDiff] = None
    primary_action_error: Optional[str] = None
    traversal_before_error: Optional[str] = None
    traversal_after_error: Optional[str] = None


# === Enums ===

class OutputControllerAction(Enum):
    """Actions for system output control."""
    SET_VOLUME = "set-volume"
    GET_VOLUME = "get-volume"
    SET_BRIGHTNESS = "set-brightness"
    GET_BRIGHTNESS = "get-brightness"


class InputAction:
    """Represents different types of input actions."""
    
    @dataclass
    class Click:
        point: Dict[str, float]  # {"x": float, "y": float}
    
    @dataclass
    class DoubleClick:
        point: Dict[str, float]
    
    @dataclass
    class RightClick:
        point: Dict[str, float]
    
    @dataclass
    class Type:
        text: str
    
    @dataclass
    class Press:
        key_name: str
        flags: int = 0
    
    @dataclass
    class Move:
        to: Dict[str, float]
    
    @dataclass
    class Scroll:
        point: Dict[str, float]
        delta_y: int = 0
        delta_x: int = 0


class PrimaryAction:
    """Represents the main action to be performed."""
    
    @dataclass
    class Open:
        identifier: str
    
    @dataclass 
    class Input:
        action: Union[
            InputAction.Click,
            InputAction.DoubleClick,
            InputAction.RightClick,
            InputAction.Type,
            InputAction.Press,
            InputAction.Move,
            InputAction.Scroll
        ]
    
    @dataclass
    class TraverseOnly:
        pass


@dataclass
class ActionOptions:
    """Configuration options for orchestrated actions."""
    traverse_before: bool = False
    traverse_after: bool = False
    show_diff: bool = False
    only_visible_elements: bool = False
    show_animation: bool = True
    animation_duration: float = 0.8
    pid_for_traversal: Optional[int] = None
    delay_after_action: float = 0.2

    def validated(self) -> Self:
        """Return validated options with consistent settings."""
        options = ActionOptions(
            traverse_before=self.traverse_before,
            traverse_after=self.traverse_after,
            show_diff=self.show_diff,
            only_visible_elements=self.only_visible_elements,
            show_animation=self.show_animation,
            animation_duration=self.animation_duration,
            pid_for_traversal=self.pid_for_traversal,
            delay_after_action=self.delay_after_action
        )
        
        # If diff is requested, ensure both traversals are enabled
        if options.show_diff:
            options.traverse_before = True
            options.traverse_after = True
        
        return options 