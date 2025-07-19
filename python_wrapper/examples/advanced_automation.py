#!/usr/bin/env python3
"""
Advanced automation examples for MacosUseSDK Python wrapper.

This script demonstrates more complex automation workflows:
- Multi-step application workflows
- Element finding and interaction
- Browser automation
- Complex file operations
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory to the path so we can import macos_use_sdk
sys.path.insert(0, str(Path(__file__).parent.parent))

from macos_use_sdk import (
    MacosSDK,
    ElementData,
    ResponseData,
    FileSearchOptions,
    InputAction,
    PrimaryAction,
    ActionOptions,
    MacosUseSDKError,
)


class MacosAutomationHelper:
    """Helper class for common automation tasks."""
    
    def __init__(self, sdk: MacosSDK):
        self.sdk = sdk
    
    async def find_element_by_text(self, response: ResponseData, text: str) -> Optional[ElementData]:
        """Find an element containing specific text."""
        for element in response.elements:
            if element.text and text.lower() in element.text.lower():
                return element
        return None
    
    async def find_button_by_text(self, response: ResponseData, text: str) -> Optional[ElementData]:
        """Find a button with specific text."""
        for element in response.elements:
            if element.role == "AXButton":
                if element.text and text.lower() in element.text.lower():
                    return element
        return None
    
    async def click_element(self, element: ElementData, visual: bool = True) -> None:
        """Click on an element using its position."""
        if element.x is None or element.y is None or element.width is None or element.height is None:
            raise ValueError("Element has no position or size information")
        
        # Calculate center of element
        x = element.x + element.width / 2
        y = element.y + element.height / 2
        
        if visual:
            await self.sdk.click_visual(x, y, duration=0.5)
        else:
            await self.sdk.click(x, y)


async def calculator_workflow():
    """Demonstrate a complete Calculator workflow."""
    print("🧮 Calculator Workflow Example")
    print("=" * 40)
    
    sdk = MacosSDK()
    helper = MacosAutomationHelper(sdk)
    
    try:
        # Open Calculator
        print("1. Opening Calculator...")
        app_result = await sdk.open_application("Calculator")
        pid = app_result.pid
        print(f"   ✅ Calculator opened (PID: {pid})")
        
        await asyncio.sleep(1.0)  # Let app load
        
        # Get initial state
        print("2. Getting initial accessibility tree...")
        initial_state = await sdk.traverse_accessibility_tree(pid, only_visible_elements=True)
        print(f"   ✅ Found {len(initial_state.elements)} elements")
        
        # Find and click number buttons to enter "123"
        print("3. Entering calculation: 123 + 456 = ")
        
        # Method 1: Use direct text input (simpler)
        await sdk.type_text("123+456=")
        await asyncio.sleep(0.5)
        
        # Get final state to see the result
        print("4. Getting result...")
        final_state = await sdk.traverse_accessibility_tree(pid, only_visible_elements=True)
        
        # Find the result display
        result_element = await helper.find_element_by_text(final_state, "579")
        if result_element:
                            print(f"   ✅ Calculation result: {result_element.text or 'No result'}")
        else:
            print("   ⚠️  Could not find result element")
        
        # Clear the calculator
        print("5. Clearing calculator...")
        await sdk.press_key("escape")  # Clear key
        
        print("   ✅ Calculator workflow completed!")
        
    except Exception as e:
        print(f"   ❌ Calculator workflow failed: {e}")


async def text_editor_workflow():
    """Demonstrate TextEdit automation."""
    print("\n📝 TextEdit Workflow Example")
    print("=" * 40)
    
    sdk = MacosSDK()
    helper = MacosAutomationHelper(sdk)
    
    try:
        # Open TextEdit
        print("1. Opening TextEdit...")
        app_result = await sdk.open_application("TextEdit")
        pid = app_result.pid
        print(f"   ✅ TextEdit opened (PID: {pid})")
        
        await asyncio.sleep(2.0)  # Let app load and create new document
        
        # Type some content
        print("2. Typing content...")
        content = """Hello from MacosUseSDK Python Wrapper!

This text was automatically typed using the automation library.

Features demonstrated:
- Application opening
- Text input simulation
- Accessibility tree traversal
- Element interaction

Date: """ + str(asyncio.get_event_loop().time())
        
        await sdk.type_text(content)
        print("   ✅ Content typed successfully")
        
        # Try to save the document
        print("3. Attempting to save document...")
        await sdk.press_key("cmd+s")  # Save shortcut
        await asyncio.sleep(1.0)
        
        # Check if save dialog appeared
        save_state = await sdk.traverse_accessibility_tree(pid, only_visible_elements=True)
        save_dialog = await helper.find_element_by_text(save_state, "Save")
        
        if save_dialog:
            print("   ✅ Save dialog appeared")
            # Cancel the save dialog for this demo
            await sdk.press_key("escape")
            print("   ℹ️  Save dialog cancelled (demo purposes)")
        else:
            print("   ⚠️  Save dialog not detected")
        
        print("   ✅ TextEdit workflow completed!")
        
    except Exception as e:
        print(f"   ❌ TextEdit workflow failed: {e}")


async def file_management_workflow():
    """Demonstrate advanced file search and organization."""
    print("\n📁 File Management Workflow Example")
    print("=" * 40)
    
    sdk = MacosSDK()
    
    try:
        # Search for different types of files
        print("1. Searching for various file types...")
        
        # Search for images
        image_options = FileSearchOptions(
            file_type="public.image",
            max_results=5,
            search_locations=[str(Path.home() / "Pictures")]
        )
        image_results = await sdk.search_files(image_options)
        print(f"   📸 Found {len(image_results.files)} images")
        
        # Search for documents
        doc_options = FileSearchOptions(
            file_type="public.text",
            max_results=5,
            search_locations=[str(Path.home() / "Documents")]
        )
        doc_results = await sdk.search_files(doc_options)
        print(f"   📄 Found {len(doc_results.files)} text documents")
        
        # Search for recent files (last 7 days)
        from datetime import datetime, timedelta
        recent_date = datetime.now() - timedelta(days=7)
        
        recent_options = FileSearchOptions(
            start_date=recent_date,
            max_results=10
        )
        recent_results = await sdk.search_files(recent_options)
        print(f"   🕐 Found {len(recent_results.files)} files modified in last 7 days")
        
        # Display some file details
        print("2. Recent file details:")
        for i, file_info in enumerate(recent_results.files[:3]):
            size_mb = file_info.size / (1024 * 1024)
            mod_date = file_info.modification_date.strftime("%Y-%m-%d %H:%M") if file_info.modification_date else "Unknown"
            print(f"   {i+1}. {file_info.name}")
            print(f"      Size: {size_mb:.2f} MB, Modified: {mod_date}")
        
        print("   ✅ File management workflow completed!")
        
    except Exception as e:
        print(f"   ❌ File management workflow failed: {e}")


async def system_control_workflow():
    """Demonstrate system control features."""
    print("\n🎛️  System Control Workflow Example")
    print("=" * 40)
    
    sdk = MacosSDK()
    
    try:
        # Get current system state
        print("1. Getting current system state...")
        volume_result = await sdk.get_volume()
        brightness_result = await sdk.get_brightness()
        
        print(f"   🔊 Current volume: {volume_result.value:.1%}")
        print(f"   🔆 Current brightness: {brightness_result.value:.1%}")
        
        # Store original values
        original_volume = volume_result.value
        original_brightness = brightness_result.value
        
        # Demonstrate volume control
        print("2. Demonstrating volume control...")
        await sdk.set_volume(0.5)  # Set to 50%
        await asyncio.sleep(0.5)
        
        new_volume = await sdk.get_volume()
        print(f"   🔊 Volume set to: {new_volume.value:.1%}")
        
        # Restore original volume
        await sdk.set_volume(original_volume)
        print(f"   🔊 Volume restored to: {original_volume:.1%}")
        
        # Demonstrate brightness control (be careful with this)
        print("3. Demonstrating brightness control...")
        if original_brightness > 0.3:  # Only demo if brightness is reasonable
            demo_brightness = max(0.3, original_brightness - 0.2)  # Slightly dimmer
            await sdk.set_brightness(demo_brightness)
            await asyncio.sleep(1.0)
            
            new_brightness = await sdk.get_brightness()
            print(f"   🔆 Brightness set to: {new_brightness.value:.1%}")
            
            # Restore original brightness
            await sdk.set_brightness(original_brightness)
            print(f"   🔆 Brightness restored to: {original_brightness:.1%}")
        else:
            print("   ⚠️  Skipping brightness demo (current brightness too low)")
        
        print("   ✅ System control workflow completed!")
        
    except Exception as e:
        print(f"   ❌ System control workflow failed: {e}")


async def coordinated_action_workflow():
    """Demonstrate coordinated actions with before/after analysis."""
    print("\n🎭 Coordinated Action Workflow Example")
    print("=" * 40)
    
    sdk = MacosSDK()
    
    try:
        # Open Calculator for this demo
        print("1. Opening Calculator for coordinated action demo...")
        app_result = await sdk.open_application("Calculator")
        pid = app_result.pid
        await asyncio.sleep(1.0)
        
        # Perform a coordinated action with full analysis
        print("2. Performing coordinated action with analysis...")
        
        # Create an input action
        action = PrimaryAction.Input(
            InputAction.Type("42")
        )
        
        # Configure options for full analysis
        options = ActionOptions(
            traverse_before=True,
            traverse_after=True,
            show_diff=True,
            only_visible_elements=True,
            show_animation=False,  # Faster for this demo
            pid_for_traversal=pid,
            delay_after_action=0.5
        )
        
        # Execute the coordinated action
        result = await sdk.perform_action(action, options)
        
        # Analyze the results
        print("3. Analyzing results...")
        if result.traversal_before:
            print(f"   📊 Elements before action: {len(result.traversal_before.elements)}")
        
        if result.traversal_after:
            print(f"   📊 Elements after action: {len(result.traversal_after.elements)}")
        
        if result.traversal_diff:
            diff = result.traversal_diff
            print(f"   📊 Elements added: {len(diff.added_elements)}")
            print(f"   📊 Elements removed: {len(diff.removed_elements)}")
            print(f"   📊 Elements modified: {len(diff.modified_elements)}")
        
        if result.primary_action_error:
            print(f"   ❌ Action error: {result.primary_action_error}")
        else:
            print("   ✅ Action completed successfully")
        
        print("   ✅ Coordinated action workflow completed!")
        
    except Exception as e:
        print(f"   ❌ Coordinated action workflow failed: {e}")


async def main():
    """Run all advanced automation examples."""
    print("🚀 MacosUseSDK Advanced Automation Examples")
    print("=" * 50)
    
    try:
        # Run all workflow examples
        await calculator_workflow()
        await text_editor_workflow()
        await file_management_workflow()
        await system_control_workflow()
        await coordinated_action_workflow()
        
        print("\n🎉 All advanced workflows completed successfully!")
        print("\n💡 Tips for building your own automation:")
        print("   • Always add delays between actions for reliability")
        print("   • Use traverse_accessibility_tree() to find elements")
        print("   • Test with only_visible_elements=True for faster traversal")
        print("   • Use visual feedback during development")
        print("   • Handle errors gracefully with try/except blocks")
        
    except MacosUseSDKError as e:
        print(f"\n❌ SDK Error: {e}")
        print("Make sure the Swift project is built and accessibility permissions are granted.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 