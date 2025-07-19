#!/usr/bin/env python3
"""
Basic usage examples for MacosUseSDK Python wrapper.

This script demonstrates the main functionality of the library:
- Opening applications
- Traversing accessibility trees
- Simulating input
- File searching
- System control
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import macos_use_sdk
sys.path.insert(0, str(Path(__file__).parent.parent))

from macos_use_sdk import (
    MacosSDK,
    FileSearchOptions,
    InputAction,
    PrimaryAction,
    ActionOptions,
    OutputControllerAction,
    MacosUseSDKError,
)


async def main():
    """Run basic usage examples."""
    try:
        # Initialize the SDK
        print("🚀 Initializing MacosUseSDK...")
        sdk = MacosSDK()
        print("✅ SDK initialized successfully!")
        
        # Example 1: Open Calculator app
        print("\n📱 Example 1: Opening Calculator app...")
        try:
            app_result = await sdk.open_application("Calculator")
            print(f"✅ Calculator opened with PID: {app_result.pid}")
            calculator_pid = app_result.pid
        except Exception as e:
            print(f"❌ Failed to open Calculator: {e}")
            return
        
        # Small delay to let app fully load
        await asyncio.sleep(1.0)
        
        # Example 2: Traverse accessibility tree
        print("\n🌳 Example 2: Traversing Calculator's accessibility tree...")
        try:
            traversal_result = await sdk.traverse_accessibility_tree(
                calculator_pid, 
                only_visible_elements=True
            )
            print(f"✅ Found {len(traversal_result.elements)} visible elements")
            print(f"   App: {traversal_result.app_name}")
            print(f"   Processing time: {traversal_result.processing_time_seconds}s")
            
            # Show some sample elements
            print("   Sample elements:")
            for i, element in enumerate(traversal_result.elements[:3]):
                print(f"     {i+1}. {element.role}: {element.text or 'No title'}")
                
        except Exception as e:
            print(f"❌ Failed to traverse accessibility tree: {e}")
        
        # Example 3: Simulate input (type calculation)
        print("\n⌨️  Example 3: Simulating input (typing '2+2=')...")
        try:
            await sdk.type_text("2+2=")
            print("✅ Text input simulated successfully")
            await asyncio.sleep(1.0)  # Let calculation complete
        except Exception as e:
            print(f"❌ Failed to simulate input: {e}")
        
        # Example 4: Visual input with feedback
        print("\n✨ Example 4: Visual click with feedback...")
        try:
            # Click the clear button (approximate position)
            await sdk.click_visual(300, 200, duration=1.0)
            print("✅ Visual click performed with feedback")
        except Exception as e:
            print(f"❌ Failed to perform visual click: {e}")
        
        # Example 5: Highlight elements 
        print("\n🔆 Example 5: Highlighting Calculator elements...")
        try:
            highlighted_result = await sdk.highlight_elements(calculator_pid, duration=2.0)
            print(f"✅ Highlighted {len(highlighted_result.elements)} elements for 2 seconds")
        except Exception as e:
            print(f"❌ Failed to highlight elements: {e}")
        
        # Example 6: File search
        print("\n🔍 Example 6: Searching for PDF files...")
        try:
            search_options = FileSearchOptions(
                file_type="public.pdf",
                max_results=5
            )
            search_result = await sdk.search_files(search_options)
            print(f"✅ Found {len(search_result.files)} PDF files in {search_result.execution_time}s")
            
            for i, file_info in enumerate(search_result.files[:3]):
                print(f"     {i+1}. {file_info.name} ({file_info.size} bytes)")
                
        except Exception as e:
            print(f"❌ Failed to search files: {e}")
        
        # Example 7: System control (get volume)
        print("\n🔊 Example 7: Getting system volume...")
        try:
            volume_result = await sdk.get_volume()
            print(f"✅ Current volume: {volume_result.value:.2f}")
        except Exception as e:
            print(f"❌ Failed to get volume: {e}")
        
        # Example 8: Coordinated action with traversal
        print("\n🎭 Example 8: Coordinated action with before/after traversal...")
        try:
            # Perform a click action with traversal before and after
            action = PrimaryAction.Input(
                InputAction.Click({"x": 250, "y": 300})
            )
            options = ActionOptions(
                traverse_before=True,
                traverse_after=True,
                show_diff=True,
                only_visible_elements=True,
                show_animation=True,
                animation_duration=0.5,
                pid_for_traversal=calculator_pid
            )
            
            action_result = await sdk.perform_action(action, options)
            
            if action_result.traversal_before:
                print(f"✅ Before: {len(action_result.traversal_before.elements)} elements")
            if action_result.traversal_after:
                print(f"✅ After: {len(action_result.traversal_after.elements)} elements")
            if action_result.traversal_diff:
                diff = action_result.traversal_diff
                print(f"✅ Diff: +{len(diff.added_elements)} -{len(diff.removed_elements)} elements")
                
        except Exception as e:
            print(f"❌ Failed coordinated action: {e}")
        
        print("\n🎉 All examples completed!")
        
    except MacosUseSDKError as e:
        print(f"❌ SDK Error: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Built the Swift project with 'swift build'")
        print("   2. Granted accessibility permissions to Terminal/Python")
        print("   3. The Swift tools are in the .build/debug directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 