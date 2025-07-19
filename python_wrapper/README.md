# MacosUseSDK Python Wrapper

A Python library for automating macOS applications using accessibility APIs. This package provides a Pythonic interface to the Swift-based MacosUseSDK, enabling you to:

- 🚀 **Open and control applications**
- 🌳 **Traverse accessibility trees** to understand UI structure  
- 🖱️ **Simulate user input** (mouse clicks, keyboard input, scrolling)
- 📁 **Search files** with advanced criteria
- 🎛️ **Control system settings** (volume, brightness)
- ✨ **Visual feedback** and element highlighting
- 🎭 **Coordinated actions** with before/after analysis

## Features

### Core Functionality

- **Application Management**: Open apps by name, bundle ID, or path
- **Accessibility Tree Traversal**: Extract complete UI element hierarchies
- **Input Simulation**: Mouse clicks, keyboard input, key combinations
- **Visual Feedback**: Highlight elements and show action feedback
- **File Operations**: Advanced file searching with multiple criteria
- **System Control**: Volume and brightness adjustment
- **Browser Support**: Enhanced support for web browsers with HTML element extraction

### Advanced Features

- **Coordinated Actions**: Combine multiple operations with automatic UI state capture
- **Differential Analysis**: Compare UI states before and after actions
- **Async Support**: All operations are async for better performance
- **Type Safety**: Full type annotations for better development experience
- **CLI Interface**: Command-line tools for scripting and automation
- **Error Handling**: Comprehensive error types for different failure modes

## Installation

### Prerequisites

1. **macOS 12.0+** - Required for the underlying Swift SDK
2. **Python 3.8+** - For the Python wrapper
3. **Swift toolchain** - To build the native components
4. **Accessibility permissions** - Required for UI automation

### Setup Steps

1. **Clone and build the Swift project:**
   ```bash
   git clone <repository-url>
   cd MacosUseSDK
   swift build
   ```

2. **Install the Python wrapper:**
   ```bash
   cd python_wrapper
   pip install -e .
   ```

3. **Grant accessibility permissions:**
   - Go to System Settings → Privacy & Security → Accessibility
   - Add Terminal (or your Python environment) to the allowed applications
   - Enable the permission

## Quick Start

### Basic Usage

```python
import asyncio
from macos_use_sdk import MacosSDK

async def main():
    # Initialize the SDK
    sdk = MacosSDK()
    
    # Open Calculator
    result = await sdk.open_application("Calculator")
    print(f"Calculator PID: {result.pid}")
    
    # Type a calculation
    await sdk.type_text("2+2=")
    
    # Get the UI structure
    tree = await sdk.traverse_accessibility_tree(result.pid, only_visible_elements=True)
    print(f"Found {len(tree.elements)} elements")
    
    # Click with visual feedback
    await sdk.click_visual(300, 200, duration=1.0)

asyncio.run(main())
```

### Command Line Interface

```bash
# Open an application
macos-use-sdk open Calculator

# Traverse accessibility tree
macos-use-sdk traverse 12345 --visible-only --output tree.json

# Simulate input
macos-use-sdk click 100 200 --visual
macos-use-sdk type "Hello World"
macos-use-sdk key "cmd+c"

# File operations
macos-use-sdk search --type public.pdf --max 10 --output results.json

# System control
macos-use-sdk volume set 0.5
macos-use-sdk brightness get
```

## API Reference

### MacosSDK Class

The main interface for all automation functionality.

#### Application Operations

```python
# Open applications
result = await sdk.open_application("Calculator")
result = await sdk.open_application("com.apple.Safari")
result = await sdk.open_application("/Applications/TextEdit.app")

# Traverse UI trees
tree = await sdk.traverse_accessibility_tree(pid, only_visible_elements=True)

# Highlight elements
highlighted = await sdk.highlight_elements(pid, duration=3.0)
```

#### Input Simulation

```python
# Mouse operations
await sdk.click(x, y)
await sdk.double_click(x, y)
await sdk.right_click(x, y)
await sdk.move_mouse(x, y)
await sdk.scroll(x, y, delta_y=-10, delta_x=0)

# Visual feedback versions
await sdk.click_visual(x, y, duration=0.5)
await sdk.double_click_visual(x, y, duration=0.5)
await sdk.right_click_visual(x, y, duration=0.5)
await sdk.move_mouse_visual(x, y, duration=0.5)

# Keyboard operations
await sdk.type_text("Hello World")
await sdk.press_key("return")
await sdk.press_key("cmd+c")
await sdk.press_key("shift+tab")
```

#### File Operations

```python
from macos_use_sdk import FileSearchOptions
from datetime import datetime, timedelta

# Search options
options = FileSearchOptions(
    file_name="report",
    file_type="public.pdf",
    start_date=datetime.now() - timedelta(days=7),
    search_locations=["/Users/username/Documents"],
    max_results=50
)

result = await sdk.search_files(options)
for file_info in result.files:
    print(f"{file_info.name}: {file_info.size} bytes")
```

#### System Control

```python
# Volume control
await sdk.set_volume(0.5)  # 50%
volume = await sdk.get_volume()

# Brightness control
await sdk.set_brightness(0.8)  # 80%
brightness = await sdk.get_brightness()
```

#### Coordinated Actions

```python
from macos_use_sdk import PrimaryAction, InputAction, ActionOptions

# Define an action
action = PrimaryAction.Input(
    InputAction.Click({"x": 100, "y": 200})
)

# Configure options
options = ActionOptions(
    traverse_before=True,
    traverse_after=True,
    show_diff=True,
    show_animation=True,
    pid_for_traversal=calculator_pid
)

# Execute coordinated action
result = await sdk.perform_action(action, options)

# Analyze results
if result.traversal_diff:
    print(f"Added: {len(result.traversal_diff.added_elements)}")
    print(f"Removed: {len(result.traversal_diff.removed_elements)}")
```

### Data Types

#### ElementData
Represents a UI element from the accessibility tree:

```python
@dataclass
class ElementData:
    ax_element: str          # Unique identifier
    role: str               # Element role (button, text field, etc.)
    title: Optional[str]    # Element title
    text: Optional[str]     # Element text content
    position: Optional[Dict[str, float]]  # {"x": float, "y": float}
    size: Optional[Dict[str, float]]      # {"width": float, "height": float}
    enabled: Optional[bool]  # Whether element is enabled
    focused: Optional[bool]  # Whether element has focus
    # ... additional properties
```

#### ResponseData
Contains the full accessibility tree and metadata:

```python
@dataclass
class ResponseData:
    app_name: str
    elements: List[ElementData]
    stats: Statistics
    processing_time_seconds: str
    is_browser: bool
    browser_data: Optional[BrowserPageData]
```

## Examples

### Calculator Automation

```python
async def calculator_demo():
    sdk = MacosSDK()
    
    # Open Calculator
    app = await sdk.open_application("Calculator")
    await asyncio.sleep(1.0)  # Let app load
    
    # Perform calculation
    await sdk.type_text("123+456=")
    
    # Get result
    tree = await sdk.traverse_accessibility_tree(app.pid, only_visible_elements=True)
    
    # Find result element
    for element in tree.elements:
        if element.text and "579" in element.text:
            print(f"Result found: {element.text}")
            break
```

### File Management

```python
async def file_management_demo():
    sdk = MacosSDK()
    
    # Search for recent images
    options = FileSearchOptions(
        file_type="public.image",
        start_date=datetime.now() - timedelta(days=7),
        search_locations=[str(Path.home() / "Pictures")],
        max_results=10
    )
    
    results = await sdk.search_files(options)
    print(f"Found {len(results.files)} recent images")
    
    for file_info in results.files:
        size_mb = file_info.size / (1024 * 1024)
        print(f"- {file_info.name} ({size_mb:.1f} MB)")
```

### Browser Automation

```python
async def browser_demo():
    sdk = MacosSDK()
    
    # Open Safari
    app = await sdk.open_application("Safari")
    await asyncio.sleep(2.0)
    
    # Get page structure (includes HTML elements for browsers)
    tree = await sdk.traverse_accessibility_tree(app.pid)
    
    if tree.is_browser and tree.browser_data:
        print(f"Page title: {tree.browser_data.title}")
        print(f"URL: {tree.browser_data.url}")
        print(f"HTML elements: {len(tree.browser_data.elements)}")
        
        # Find specific elements
        for element in tree.browser_data.elements:
            if element.tag_name == "button" and element.text:
                print(f"Button found: {element.text}")
```

### System Integration

```python
async def system_demo():
    sdk = MacosSDK()
    
    # Get current state
    volume = await sdk.get_volume()
    brightness = await sdk.get_brightness()
    
    print(f"Volume: {volume.value:.0%}")
    print(f"Brightness: {brightness.value:.0%}")
    
    # Temporarily adjust settings
    original_volume = volume.value
    await sdk.set_volume(0.3)  # 30%
    
    # Do something...
    await asyncio.sleep(1.0)
    
    # Restore settings
    await sdk.set_volume(original_volume)
```

## Error Handling

The library provides specific exception types for different error conditions:

```python
from macos_use_sdk import (
    MacosUseSDKError,
    AccessibilityError,
    AppNotFoundError,
    InputSimulationError,
    FileSearchError,
    OutputControllerError,
)

try:
    result = await sdk.open_application("NonExistentApp")
except AppNotFoundError as e:
    print(f"App not found: {e}")
except AccessibilityError as e:
    print(f"Accessibility denied: {e}")
except MacosUseSDKError as e:
    print(f"General SDK error: {e}")
```

## Best Practices

### Timing and Reliability

```python
# Always add delays after opening applications
await sdk.open_application("TextEdit")
await asyncio.sleep(1.0)  # Let app fully load

# Add delays between related actions
await sdk.click(100, 200)
await asyncio.sleep(0.1)  # Brief pause
await sdk.type_text("Hello")
```

### Element Discovery

```python
# Use only_visible_elements for faster traversal
tree = await sdk.traverse_accessibility_tree(pid, only_visible_elements=True)

# Search for elements by text/role
def find_button(elements, text):
    for elem in elements:
        if elem.role == "AXButton" and elem.text and text.lower() in elem.text.lower():
            return elem
    return None

button = find_button(tree.elements, "Save")
if button and button.position:
    x = button.position["x"] + button.size["width"] / 2
    y = button.position["y"] + button.size["height"] / 2
    await sdk.click(x, y)
```

### Development and Debugging

```python
# Use visual feedback during development
await sdk.click_visual(x, y, duration=1.0)  # Easier to see what's happening

# Highlight elements to understand structure
await sdk.highlight_elements(pid, duration=3.0)

# Use coordinated actions for complex workflows
options = ActionOptions(
    traverse_before=True,
    traverse_after=True,
    show_diff=True,
    show_animation=True
)
result = await sdk.perform_action(action, options)
```

## Troubleshooting

### Common Issues

1. **"SDK Error: Could not find Swift build directory"**
   - Run `swift build` in the project root
   - Check that `.build/debug/` contains the tool executables

2. **"Accessibility access is denied"**
   - Go to System Settings → Privacy & Security → Accessibility
   - Add Terminal or your Python environment
   - Enable the permission and restart your script

3. **"Application not found"**
   - Check the application name spelling
   - Try using the bundle ID instead (e.g., "com.apple.Calculator")
   - Use the full path to the application

4. **Input simulation not working**
   - Ensure the target application is active/focused
   - Add delays between actions
   - Check if the application requires special handling

### Performance Tips

- Use `only_visible_elements=True` for faster traversal
- Cache PIDs instead of repeatedly opening applications
- Use non-visual input methods for better performance
- Batch operations when possible

### Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable verbose output
sdk = MacosSDK()

# Check tool availability
try:
    result = await sdk.open_application("Calculator")
    print("SDK working correctly")
except Exception as e:
    print(f"SDK issue: {e}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on top of the Swift MacosUseSDK
- Uses macOS Accessibility APIs
- Inspired by automation needs in the macOS ecosystem 