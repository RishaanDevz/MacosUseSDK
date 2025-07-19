"""
Core MacosSDK class that provides the main interface for the Python wrapper.

This class coordinates calls to the Swift command-line tools and provides
a Pythonic interface for all SDK functionality.
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from .types import (
    ActionOptions,
    ActionResult,
    AppOpenerResult,
    ElementData,
    FileSearchOptions,
    FileSearchResult,
    InputAction,
    OutputControllerAction,
    OutputControllerResult,
    PrimaryAction,
    ResponseData,
    Statistics,
    TraversalDiff,
    BrowserElementData,
    BrowserPageData,
    FileInfo,
    AttributeChangeDetail,
    ElementChange,
    
    # Exceptions
    MacosUseSDKError,
    AccessibilityError,
    AppNotFoundError,
    InputSimulationError,
    FileSearchError,
    OutputControllerError,
)


class MacosSDK:
    """
    Main interface for the MacosUseSDK Python wrapper.
    
    This class provides methods for:
    - Opening applications
    - Traversing accessibility trees  
    - Simulating user input
    - Searching files
    - Controlling system output
    - Performing coordinated actions with visual feedback
    """
    
    def __init__(self, swift_build_path: Optional[str] = None):
        """
        Initialize the MacosSDK wrapper.
        
        Args:
            swift_build_path: Path to the Swift build directory. If None, will try to
                            locate it relative to this package or in common locations.
        """
        self.swift_build_path = self._find_swift_build_path(swift_build_path)
        
    def _find_swift_build_path(self, provided_path: Optional[str]) -> str:
        """Find the Swift build directory containing the compiled tools."""
        if provided_path and os.path.exists(provided_path):
            return provided_path
            
        # Try to find relative to the Python package
        package_dir = Path(__file__).parent.parent.parent
        candidates = [
            package_dir / ".build" / "debug",
            package_dir / ".build" / "release", 
            package_dir.parent / ".build" / "debug",
            package_dir.parent / ".build" / "release",
            Path.cwd() / ".build" / "debug",
            Path.cwd() / ".build" / "release",
        ]
        
        for candidate in candidates:
            if candidate.exists() and (candidate / "AppOpenerTool").exists():
                return str(candidate)
                
        raise MacosUseSDKError(
            f"Could not find Swift build directory. Please build the project with "
            f"'swift build' or provide the path explicitly."
        )
    
    def _run_tool(self, tool_name: str, args: List[str], check_returncode: bool = True) -> subprocess.CompletedProcess:
        """Run a Swift tool with the given arguments."""
        tool_path = os.path.join(self.swift_build_path, tool_name)
        if not os.path.exists(tool_path):
            raise MacosUseSDKError(f"Tool {tool_name} not found at {tool_path}")
        
        cmd = [tool_path] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # We'll check manually to provide better error messages
            )
            
            if check_returncode and result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise MacosUseSDKError(f"{tool_name} failed: {error_msg}")
                
            return result
        except subprocess.SubprocessError as e:
            raise MacosUseSDKError(f"Failed to run {tool_name}: {e}")
    
    async def _run_tool_async(self, tool_name: str, args: List[str], check_returncode: bool = True) -> subprocess.CompletedProcess:
        """Run a Swift tool asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run_tool, tool_name, args, check_returncode)
    
    def _parse_json_response(self, json_str: str, response_type: str) -> Dict:
        """Parse JSON response from Swift tools."""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise MacosUseSDKError(f"Failed to parse {response_type} JSON response: {e}")
    
    # === Application Operations ===
    
    async def open_application(self, identifier: str) -> AppOpenerResult:
        """
        Open or activate a macOS application.
        
        Args:
            identifier: Application name, bundle ID, or path
            
        Returns:
            AppOpenerResult containing PID and timing information
            
        Raises:
            AppNotFoundError: If the application cannot be found or opened
        """
        try:
            result = await self._run_tool_async("AppOpenerTool", [identifier])
            pid = int(result.stdout.strip())
            
            # Parse app name and timing from stderr
            stderr_lines = result.stderr.strip().split('\n')
            app_name = identifier  # Default fallback
            processing_time = "0.000"
            
            for line in stderr_lines:
                if "total execution time:" in line:
                    processing_time = line.split(":")[-1].strip().replace(" seconds", "")
                
            return AppOpenerResult(
                pid=pid,
                app_name=app_name,
                processing_time_seconds=processing_time
            )
        except MacosUseSDKError as e:
            if "not found" in str(e).lower():
                raise AppNotFoundError(f"Application not found: {identifier}")
            raise
    
    async def get_pid_by_bundle_id(self, bundle_id: str) -> Optional[int]:
        """
        Get the PID of a running application by its bundle ID.
        
        Args:
            bundle_id: Bundle ID of the application (e.g., "com.apple.Calculator")
            
        Returns:
            PID if the application is running, None otherwise
        """
        try:
            # Use our improved app listing to find by bundle ID
            apps = await self.list_running_applications()
            for app in apps:
                if app['bundle_id'] == bundle_id:
                    return app['pid']
            return None
        except Exception:
            return None
    
    async def find_running_app_pid(self, identifier: str) -> Optional[int]:
        """
        Find the PID of a running application by name or bundle ID.
        
        Args:
            identifier: Application name or bundle ID
            
        Returns:
            PID if found, None otherwise
        """
        try:
            # Get list of running applications
            apps = await self.list_running_applications()
            
            # First try exact bundle ID match
            for app in apps:
                if app['bundle_id'] == identifier:
                    return app['pid']
            
            # Then try exact name match (case insensitive)
            for app in apps:
                if app['name'].lower() == identifier.lower():
                    return app['pid']
            
            # Finally try partial name match (case insensitive)
            for app in apps:
                if identifier.lower() in app['name'].lower():
                    return app['pid']
            
            return None
        except Exception:
            return None

    async def list_running_applications(self) -> List[Dict[str, Union[str, int]]]:
        """
        List all currently running applications with their PIDs and bundle IDs.
        
        Returns:
            List of dictionaries containing app information
        """
        apps = []
        try:
            import subprocess
            
            # Use osascript to get app information from System Events
            try:
                script = '''tell application "System Events"
    set appInfo to {}
    repeat with proc in (every process whose background only is false)
        try
            set procName to name of proc
            set procPID to unix id of proc
            set bundleID to bundle identifier of proc
            set end of appInfo to (procName & "," & procPID & "," & bundleID)
        on error
            -- Skip processes without bundle IDs
        end try
    end repeat
    return appInfo
end tell'''
                
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    # Parse the comma-separated output
                    output = result.stdout.strip()
                    # Split by comma, but handle app names that might contain commas
                    app_entries = output.split(', ')
                    
                    for entry in app_entries:
                        # Each entry format: "AppName,PID,BundleID"
                        parts = entry.split(',')
                        if len(parts) >= 3:
                            # Handle case where app name might contain commas
                            name = ','.join(parts[:-2]) if len(parts) > 3 else parts[0]
                            pid_str = parts[-2]
                            bundle_id = parts[-1]
                            
                            try:
                                apps.append({
                                    'pid': int(pid_str),
                                    'bundle_id': bundle_id,
                                    'name': name,
                                })
                            except ValueError:
                                continue
                            
            except Exception:
                # Fallback to simpler ps approach
                result = subprocess.run(
                    ["ps", "-eo", "pid,comm"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    parts = line.strip().split(None, 1)
                    if len(parts) >= 2:
                        pid_str, comm = parts[0], parts[1]
                        try:
                            pid = int(pid_str)
                            # Filter for likely app processes
                            if '.app/Contents/MacOS/' in comm:
                                app_name = comm.split('.app/Contents/MacOS/')[0].split('/')[-1]
                                apps.append({
                                    'pid': pid,
                                    'bundle_id': f'unknown.{app_name.lower()}',
                                    'name': app_name,
                                })
                        except ValueError:
                            continue
        except Exception:
            pass
        
        return apps

    async def traverse_accessibility_tree(
        self,
        pid_or_identifier: Union[int, str],
        only_visible_elements: bool = False
    ) -> ResponseData:
        """
        Traverse the accessibility tree of an application.
        
        Args:
            pid_or_identifier: Process ID (int), application name (str), or bundle ID (str)
            only_visible_elements: If True, only include visible elements
            
        Returns:
            ResponseData containing the accessibility tree and statistics
            
        Raises:
            AccessibilityError: If accessibility permissions are denied
            AppNotFoundError: If the application cannot be found
        """
        # Resolve identifier to PID if needed
        if isinstance(pid_or_identifier, str):
            pid = await self.find_running_app_pid(pid_or_identifier)
            if pid is None:
                raise AppNotFoundError(f"No running application found for identifier: {pid_or_identifier}")
        else:
            pid = pid_or_identifier
        
        args = []
        if only_visible_elements:
            args.append("--visible-only")
        args.append(str(pid))
        
        try:
            result = await self._run_tool_async("TraversalTool", args)
            json_data = self._parse_json_response(result.stdout, "traversal")
            
            return self._parse_response_data(json_data)
        except MacosUseSDKError as e:
            if "accessibility" in str(e).lower():
                raise AccessibilityError(str(e))
            elif "not found" in str(e).lower():
                raise AppNotFoundError(f"No application found for identifier {pid_or_identifier}")
            raise
    
    def _parse_response_data(self, json_data: Dict) -> ResponseData:
        """Parse JSON data into ResponseData object."""
        # Parse statistics
        stats_data = json_data.get("stats", {})
        stats = Statistics(
            count=stats_data.get("count", 0),
            excluded_count=stats_data.get("excluded_count", 0),
            excluded_non_interactable=stats_data.get("excluded_non_interactable", 0),
            excluded_no_text=stats_data.get("excluded_no_text", 0),
            with_text_count=stats_data.get("with_text_count", 0),
            without_text_count=stats_data.get("without_text_count", 0),
            visible_elements_count=stats_data.get("visible_elements_count", 0),
            role_counts=stats_data.get("role_counts", {}),
            browser_elements_count=stats_data.get("browser_elements_count", 0)
        )
        
        # Parse elements
        elements = []
        for elem_data in json_data.get("elements", []):
            elements.append(ElementData(
                role=elem_data.get("role", ""),
                text=elem_data.get("text"),
                x=elem_data.get("x"),
                y=elem_data.get("y"),
                width=elem_data.get("width"),
                height=elem_data.get("height")
            ))
        
        # Parse browser data if present
        browser_data = None
        if json_data.get("browser_data"):
            browser_json = json_data["browser_data"]
            browser_elements = []
            for elem in browser_json.get("elements", []):
                browser_elements.append(BrowserElementData(
                    tag_name=elem.get("tagName", ""),
                    id=elem.get("id"),
                    class_name=elem.get("className"),
                    text=elem.get("text"),
                    value=elem.get("value"),
                    placeholder=elem.get("placeholder"),
                    aria_label=elem.get("ariaLabel"),
                    role=elem.get("role"),
                    href=elem.get("href"),
                    src=elem.get("src"),
                    x=elem.get("x"),
                    y=elem.get("y"),
                    width=elem.get("width"),
                    height=elem.get("height")
                ))
            
            browser_data = BrowserPageData(
                url=browser_json.get("url"),
                title=browser_json.get("title"),
                elements=browser_elements
            )
        
        return ResponseData(
            app_name=json_data.get("app_name", ""),
            elements=elements,
            stats=stats,
            processing_time_seconds=json_data.get("processing_time_seconds", "0.000"),
            is_browser=json_data.get("is_browser", False),
            browser_data=browser_data
        )
    
    async def highlight_elements(self, pid_or_identifier: Union[int, str], duration: float = 3.0) -> ResponseData:
        """
        Highlight all visible elements of an application with red boxes.
        
        Args:
            pid_or_identifier: Process ID (int), application name (str), or bundle ID (str)
            duration: How long to show highlights (seconds)
            
        Returns:
            ResponseData containing the highlighted elements
        """
        # Resolve identifier to PID if needed
        if isinstance(pid_or_identifier, str):
            pid = await self.find_running_app_pid(pid_or_identifier)
            if pid is None:
                raise AppNotFoundError(f"No running application found for identifier: {pid_or_identifier}")
        else:
            pid = pid_or_identifier
            
        args = [str(pid), "--duration", str(duration)]
        
        try:
            result = await self._run_tool_async("HighlightTraversalTool", args)
            json_data = self._parse_json_response(result.stdout, "highlight traversal")
            return self._parse_response_data(json_data)
        except MacosUseSDKError as e:
            if "accessibility" in str(e).lower():
                raise AccessibilityError(str(e))
            elif "not found" in str(e).lower():
                raise AppNotFoundError(f"No application found for identifier {pid_or_identifier}")
            raise
    
    # === Input Simulation ===
    
    async def click(self, x: float, y: float) -> None:
        """Simulate a left mouse click at the specified coordinates."""
        await self._run_input_action("click", [str(x), str(y)])
    
    async def double_click(self, x: float, y: float) -> None:
        """Simulate a left mouse double-click at the specified coordinates.""" 
        await self._run_input_action("doubleclick", [str(x), str(y)])
    
    async def right_click(self, x: float, y: float) -> None:
        """Simulate a right mouse click at the specified coordinates."""
        await self._run_input_action("rightclick", [str(x), str(y)])
    
    async def move_mouse(self, x: float, y: float) -> None:
        """Move the mouse cursor to the specified coordinates."""
        await self._run_input_action("mousemove", [str(x), str(y)])
    
    async def type_text(self, text: str) -> None:
        """Type the specified text."""
        await self._run_input_action("writetext", [text])
    
    async def press_key(self, key: str) -> None:
        """Press a key (e.g., 'return', 'cmd+c', 'shift+tab')."""
        await self._run_input_action("keypress", [key])
    
    async def scroll(self, x: float, y: float, delta_y: int, delta_x: int = 0) -> None:
        """Simulate a scroll action at the specified coordinates."""
        await self._run_input_action("scroll", [str(x), str(y), str(delta_y), str(delta_x)])
    
    async def _run_input_action(self, action: str, args: List[str]) -> None:
        """Run an input action using InputControllerTool."""
        try:
            await self._run_tool_async("InputControllerTool", [action] + args)
        except MacosUseSDKError as e:
            raise InputSimulationError(f"Input simulation failed: {e}")
    
    # === Visual Input (with feedback) ===
    
    async def click_visual(self, x: float, y: float, duration: float = 0.5) -> None:
        """Simulate a left mouse click with visual feedback."""
        await self._run_visual_input_action("click", [str(x), str(y)], duration)
    
    async def double_click_visual(self, x: float, y: float, duration: float = 0.5) -> None:
        """Simulate a double-click with visual feedback."""
        await self._run_visual_input_action("doubleclick", [str(x), str(y)], duration)
    
    async def right_click_visual(self, x: float, y: float, duration: float = 0.5) -> None:
        """Simulate a right-click with visual feedback."""
        await self._run_visual_input_action("rightclick", [str(x), str(y)], duration)
    
    async def move_mouse_visual(self, x: float, y: float, duration: float = 0.5) -> None:
        """Move mouse with visual feedback."""
        await self._run_visual_input_action("mousemove", [str(x), str(y)], duration)
    
    async def _run_visual_input_action(self, action: str, args: List[str], duration: float) -> None:
        """Run a visual input action using VisualInputTool."""
        try:
            full_args = [action] + args + ["--duration", str(duration)]
            await self._run_tool_async("VisualInputTool", full_args)
        except MacosUseSDKError as e:
            raise InputSimulationError(f"Visual input simulation failed: {e}")
    
    # === File Search ===
    
    async def search_files(self, options: FileSearchOptions) -> FileSearchResult:
        """
        Search for files based on the given criteria.
        
        Args:
            options: FileSearchOptions containing search parameters
            
        Returns:
            FileSearchResult containing matched files
            
        Raises:
            FileSearchError: If the search fails
        """
        args = []
        
        if options.file_name:
            args.extend(["--name", options.file_name])
        if options.file_type:
            args.extend(["--type", options.file_type])
        if options.start_date:
            args.extend(["--start-date", options.start_date.strftime("%Y-%m-%d")])
        if options.end_date:
            args.extend(["--end-date", options.end_date.strftime("%Y-%m-%d")])
        if options.max_results != 100:
            args.extend(["--max", str(options.max_results)])
        
        for location in options.search_locations:
            args.extend(["--location", location])
        
        try:
            result = await self._run_tool_async("FileSearchTool", args)
            json_data = self._parse_json_response(result.stdout, "file search")
            
            # Parse file info
            files = []
            for file_data in json_data.get("files", []):
                creation_date = None
                modification_date = None
                
                if file_data.get("creationDate"):
                    creation_date = datetime.fromisoformat(file_data["creationDate"].replace("Z", "+00:00"))
                if file_data.get("modificationDate"):
                    modification_date = datetime.fromisoformat(file_data["modificationDate"].replace("Z", "+00:00"))
                
                files.append(FileInfo(
                    path=file_data.get("path", ""),
                    name=file_data.get("name", ""),
                    size=file_data.get("size", 0),
                    creation_date=creation_date,
                    modification_date=modification_date,
                    file_type=file_data.get("fileType", "")
                ))
            
            return FileSearchResult(
                files=files,
                total_count=json_data.get("totalCount", len(files)),
                execution_time=json_data.get("executionTime", "0.000")
            )
        except MacosUseSDKError as e:
            raise FileSearchError(f"File search failed: {e}")
    
    # === System Output Control ===
    
    async def set_volume(self, volume: float) -> OutputControllerResult:
        """Set system volume (0.0 - 1.0)."""
        return await self._run_output_controller_action(OutputControllerAction.SET_VOLUME, volume)
    
    async def get_volume(self) -> OutputControllerResult:
        """Get current system volume."""
        return await self._run_output_controller_action(OutputControllerAction.GET_VOLUME)
    
    async def set_brightness(self, brightness: float) -> OutputControllerResult:
        """Set display brightness (0.0 - 1.0)."""
        return await self._run_output_controller_action(OutputControllerAction.SET_BRIGHTNESS, brightness)
    
    async def get_brightness(self) -> OutputControllerResult:
        """Get current display brightness."""
        return await self._run_output_controller_action(OutputControllerAction.GET_BRIGHTNESS)
    
    async def _run_output_controller_action(
        self,
        action: OutputControllerAction,
        value: Optional[float] = None
    ) -> OutputControllerResult:
        """Run an output controller action."""
        args = [action.value]
        if value is not None:
            args.append(str(value))
        
        try:
            result = await self._run_tool_async("OutputControllerTool", args)
            value_output = result.stdout.strip()
            
            # Parse value from stdout
            parsed_value = None
            if value_output:
                try:
                    parsed_value = float(value_output)
                except ValueError:
                    pass
            
            # Parse message from stderr
            stderr_lines = result.stderr.strip().split('\n')
            message = ""
            for line in stderr_lines:
                if "Success:" in line:
                    message = line.split("Success:", 1)[1].strip()
                    break
            
            return OutputControllerResult(value=parsed_value, message=message)
        except MacosUseSDKError as e:
            raise OutputControllerError(f"Output controller operation failed: {e}")
    
    # === Coordinated Actions ===
    
    async def perform_action(
        self,
        action: Union[PrimaryAction.Open, PrimaryAction.Input, PrimaryAction.TraverseOnly],
        options: Optional[ActionOptions] = None
    ) -> ActionResult:
        """
        Perform a coordinated action with optional traversal and visual feedback.
        
        This is the high-level interface that combines multiple operations
        like opening apps, performing input, and capturing UI state changes.
        
        Args:
            action: The primary action to perform
            options: Configuration options for the action
            
        Returns:
            ActionResult containing all the results and data from the operation
        """
        if options is None:
            options = ActionOptions()
        
        options = options.validated()
        
        # Convert Python action to command line arguments for ActionTool
        # For now, we'll implement basic actions directly rather than using ActionTool
        # since ActionTool appears to be more of an example/test tool
        
        result = ActionResult()
        
        # Handle open action
        if isinstance(action, PrimaryAction.Open):
            try:
                open_result = await self.open_application(action.identifier)
                result.open_result = open_result
                result.traversal_pid = open_result.pid
            except Exception as e:
                result.primary_action_error = str(e)
                return result
        
        # Handle traversal before
        if options.traverse_before and result.traversal_pid:
            try:
                result.traversal_before = await self.traverse_accessibility_tree(
                    result.traversal_pid, 
                    options.only_visible_elements
                )
            except Exception as e:
                result.traversal_before_error = str(e)
        
        # Handle input action  
        if isinstance(action, PrimaryAction.Input):
            try:
                await self._execute_input_action(action.action, options)
            except Exception as e:
                result.primary_action_error = str(e)
        
        # Delay after action
        if options.delay_after_action > 0:
            await asyncio.sleep(options.delay_after_action)
        
        # Handle traversal after
        if options.traverse_after and result.traversal_pid:
            try:
                result.traversal_after = await self.traverse_accessibility_tree(
                    result.traversal_pid,
                    options.only_visible_elements
                )
            except Exception as e:
                result.traversal_after_error = str(e)
        
        # Generate diff if requested
        if options.show_diff and result.traversal_before and result.traversal_after:
            result.traversal_diff = self._generate_traversal_diff(
                result.traversal_before,
                result.traversal_after
            )
        
        return result
    
    async def _execute_input_action(self, action: InputAction, options: ActionOptions) -> None:
        """Execute an input action with optional visual feedback."""
        if isinstance(action, InputAction.Click):
            point = action.point
            if options.show_animation:
                await self.click_visual(point["x"], point["y"], options.animation_duration)
            else:
                await self.click(point["x"], point["y"])
        
        elif isinstance(action, InputAction.DoubleClick):
            point = action.point
            if options.show_animation:
                await self.double_click_visual(point["x"], point["y"], options.animation_duration)
            else:
                await self.double_click(point["x"], point["y"])
        
        elif isinstance(action, InputAction.RightClick):
            point = action.point
            if options.show_animation:
                await self.right_click_visual(point["x"], point["y"], options.animation_duration)
            else:
                await self.right_click(point["x"], point["y"])
        
        elif isinstance(action, InputAction.Type):
            await self.type_text(action.text)
        
        elif isinstance(action, InputAction.Press):
            await self.press_key(action.key_name)
        
        elif isinstance(action, InputAction.Move):
            point = action.to
            if options.show_animation:
                await self.move_mouse_visual(point["x"], point["y"], options.animation_duration)
            else:
                await self.move_mouse(point["x"], point["y"])
        
        elif isinstance(action, InputAction.Scroll):
            point = action.point
            await self.scroll(point["x"], point["y"], action.delta_y, action.delta_x)
    
    def _generate_traversal_diff(self, before: ResponseData, after: ResponseData) -> TraversalDiff:
        """Generate a diff between two traversal results."""
        # This is a simplified diff implementation
        # The full Swift implementation is much more sophisticated
        
        before_elements = {elem.ax_element: elem for elem in before.elements}
        after_elements = {elem.ax_element: elem for elem in after.elements}
        
        added = [elem for ax_el, elem in after_elements.items() if ax_el not in before_elements]
        removed = [elem for ax_el, elem in before_elements.items() if ax_el not in after_elements]
        
        # For now, we'll skip the detailed attribute change detection
        # which would require comparing all attributes of each element
        
        return TraversalDiff(
            added_elements=added,
            removed_elements=removed,
            modified_elements=[],  # TODO: Implement detailed change detection
            stats_before=before.stats,
            stats_after=after.stats
        ) 