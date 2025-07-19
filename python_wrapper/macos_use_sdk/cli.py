#!/usr/bin/env python3
"""
Command-line interface for MacosUseSDK Python wrapper.

Provides a CLI for common automation tasks without needing to write Python code.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from .core import MacosSDK
from .types import (
    FileSearchOptions,
    InputAction,
    PrimaryAction,
    ActionOptions,
    OutputControllerAction,
    MacosUseSDKError,
)


class CLIHandler:
    """Handles CLI commands for MacosUseSDK."""
    
    def __init__(self):
        self.sdk = MacosSDK()
    
    async def open_app(self, identifier: str) -> None:
        """Open an application and print the PID."""
        try:
            result = await self.sdk.open_application(identifier)
            print(f"Application opened with PID: {result.pid}")
            print(f"App name: {result.app_name}")
            print(f"Processing time: {result.processing_time_seconds}s")
        except Exception as e:
            print(f"Error opening application: {e}", file=sys.stderr)
            sys.exit(1)
    
    async def traverse(self, pid_or_identifier: Union[int, str], visible_only: bool = False, output_file: Optional[str] = None) -> None:
        """Traverse accessibility tree and output JSON."""
        try:
            # Convert to int if it's a numeric string (PID), otherwise keep as string (bundle ID/name)
            if isinstance(pid_or_identifier, str) and pid_or_identifier.isdigit():
                identifier = int(pid_or_identifier)
            else:
                identifier = pid_or_identifier
                
            result = await self.sdk.traverse_accessibility_tree(identifier, visible_only)
            
            # Convert to dict for JSON serialization
            data = {
                "app_name": result.app_name,
                "processing_time_seconds": result.processing_time_seconds,
                "is_browser": result.is_browser,
                "stats": {
                    "count": result.stats.count,
                    "excluded_count": result.stats.excluded_count,
                    "visible_elements_count": result.stats.visible_elements_count,
                    "role_counts": result.stats.role_counts,
                },
                "elements": [
                    {
                        "role": elem.role,
                        "text": elem.text,
                        "x": elem.x,
                        "y": elem.y,
                        "width": elem.width,
                        "height": elem.height,
                    }
                    for elem in result.elements
                ]
            }
            
            json_output = json.dumps(data, indent=2, ensure_ascii=False)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(json_output)
                print(f"Traversal data saved to {output_file}")
            else:
                print(json_output)
                
        except Exception as e:
            print(f"Error traversing accessibility tree: {e}", file=sys.stderr)
            sys.exit(1)
    
    async def click(self, x: float, y: float, visual: bool = False, duration: float = 0.5) -> None:
        """Simulate a mouse click."""
        try:
            if visual:
                await self.sdk.click_visual(x, y, duration)
                print(f"Visual click at ({x}, {y}) with {duration}s feedback")
            else:
                await self.sdk.click(x, y)
                print(f"Click at ({x}, {y})")
        except Exception as e:
            print(f"Error clicking: {e}", file=sys.stderr)
            sys.exit(1)
    
    async def type_text(self, text: str) -> None:
        """Type text."""
        try:
            await self.sdk.type_text(text)
            print(f"Typed: {text}")
        except Exception as e:
            print(f"Error typing text: {e}", file=sys.stderr)
            sys.exit(1)
    
    async def press_key(self, key: str) -> None:
        """Press a key."""
        try:
            await self.sdk.press_key(key)
            print(f"Pressed key: {key}")
        except Exception as e:
            print(f"Error pressing key: {e}", file=sys.stderr)
            sys.exit(1)
    
    async def search_files(
        self,
        name: Optional[str] = None,
        file_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        locations: Optional[List[str]] = None,
        max_results: int = 100,
        output_file: Optional[str] = None
    ) -> None:
        """Search for files."""
        try:
            # Parse dates if provided
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
            
            options = FileSearchOptions(
                file_name=name,
                file_type=file_type,
                start_date=start_dt,
                end_date=end_dt,
                search_locations=locations or [],
                max_results=max_results
            )
            
            result = await self.sdk.search_files(options)
            
            # Convert to dict for JSON serialization
            data = {
                "total_count": result.total_count,
                "execution_time": result.execution_time,
                "files": [
                    {
                        "path": file_info.path,
                        "name": file_info.name,
                        "size": file_info.size,
                        "creation_date": file_info.creation_date.isoformat() if file_info.creation_date else None,
                        "modification_date": file_info.modification_date.isoformat() if file_info.modification_date else None,
                        "file_type": file_info.file_type,
                    }
                    for file_info in result.files
                ]
            }
            
            json_output = json.dumps(data, indent=2, ensure_ascii=False)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(json_output)
                print(f"Search results saved to {output_file}")
            else:
                print(json_output)
                
        except Exception as e:
            print(f"Error searching files: {e}", file=sys.stderr)
            sys.exit(1)
    
    async def set_volume(self, volume: float) -> None:
        """Set system volume."""
        try:
            result = await self.sdk.set_volume(volume)
            print(f"Volume set to: {result.value:.2f}")
        except Exception as e:
            print(f"Error setting volume: {e}", file=sys.stderr)
            sys.exit(1)
    
    async def get_volume(self) -> None:
        """Get system volume."""
        try:
            result = await self.sdk.get_volume()
            print(f"Current volume: {result.value:.2f}")
        except Exception as e:
            print(f"Error getting volume: {e}", file=sys.stderr)
            sys.exit(1)
    
    async def set_brightness(self, brightness: float) -> None:
        """Set display brightness."""
        try:
            result = await self.sdk.set_brightness(brightness)
            print(f"Brightness set to: {result.value:.2f}")
        except Exception as e:
            print(f"Error setting brightness: {e}", file=sys.stderr)
            sys.exit(1)
    
    async def get_brightness(self) -> None:
        """Get display brightness."""
        try:
            result = await self.sdk.get_brightness()
            print(f"Current brightness: {result.value:.2f}")
        except Exception as e:
            print(f"Error getting brightness: {e}", file=sys.stderr)
            sys.exit(1)
    
    async def list_apps(self, output_file: Optional[str] = None) -> None:
        """List running applications."""
        try:
            apps = await self.sdk.list_running_applications()
            
            # Convert to dict for JSON serialization
            data = {
                "running_applications": apps,
                "count": len(apps)
            }
            
            json_output = json.dumps(data, indent=2, ensure_ascii=False)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(json_output)
                print(f"Application list saved to {output_file}")
            else:
                print(json_output)
                
        except Exception as e:
            print(f"Error listing applications: {e}", file=sys.stderr)
            sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="MacosUseSDK Python CLI - Automate macOS applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
 Examples:
   # List running applications
   macos-use-sdk list
   
   # Open Calculator
   macos-use-sdk open Calculator
  
     # Traverse accessibility tree (by PID, name, or bundle ID)
   macos-use-sdk traverse 12345 --visible-only
   macos-use-sdk traverse Calculator --visible-only  
   macos-use-sdk traverse com.apple.Calculator --visible-only
  
  # Click at coordinates
  macos-use-sdk click 100 200 --visual
  
  # Type text
  macos-use-sdk type "Hello World"
  
  # Press key combination
  macos-use-sdk key "cmd+c"
  
  # Search for PDF files
  macos-use-sdk search --type public.pdf --max 10
  
  # Set volume to 50%
  macos-use-sdk volume set 0.5
  
  # Get current brightness
  macos-use-sdk brightness get
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List running applications")
    list_parser.add_argument("--output", "-o", help="Output file for JSON data")
    
    # Open command
    open_parser = subparsers.add_parser("open", help="Open an application")
    open_parser.add_argument("identifier", help="Application name, bundle ID, or path")
    
    # Traverse command
    traverse_parser = subparsers.add_parser("traverse", help="Traverse accessibility tree")
    traverse_parser.add_argument("identifier", help="Process ID, application name, or bundle ID (e.g., 12345, Calculator, com.apple.Calculator)")
    traverse_parser.add_argument("--visible-only", action="store_true", help="Only include visible elements")
    traverse_parser.add_argument("--output", "-o", help="Output file for JSON data")
    
    # Click command
    click_parser = subparsers.add_parser("click", help="Simulate mouse click")
    click_parser.add_argument("x", type=float, help="X coordinate")
    click_parser.add_argument("y", type=float, help="Y coordinate")
    click_parser.add_argument("--visual", action="store_true", help="Show visual feedback")
    click_parser.add_argument("--duration", type=float, default=0.5, help="Visual feedback duration")
    
    # Type command
    type_parser = subparsers.add_parser("type", help="Type text")
    type_parser.add_argument("text", help="Text to type")
    
    # Key command
    key_parser = subparsers.add_parser("key", help="Press key or key combination")
    key_parser.add_argument("key", help="Key to press (e.g., 'return', 'cmd+c')")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for files")
    search_parser.add_argument("--name", help="File name pattern")
    search_parser.add_argument("--type", help="File type (UTI)")
    search_parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    search_parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    search_parser.add_argument("--location", action="append", help="Search location (can be used multiple times)")
    search_parser.add_argument("--max", type=int, default=100, help="Maximum results")
    search_parser.add_argument("--output", "-o", help="Output file for JSON data")
    
    # Volume command
    volume_parser = subparsers.add_parser("volume", help="Control system volume")
    volume_subparsers = volume_parser.add_subparsers(dest="volume_action")
    volume_set = volume_subparsers.add_parser("set", help="Set volume")
    volume_set.add_argument("value", type=float, help="Volume level (0.0 - 1.0)")
    volume_subparsers.add_parser("get", help="Get current volume")
    
    # Brightness command
    brightness_parser = subparsers.add_parser("brightness", help="Control display brightness")
    brightness_subparsers = brightness_parser.add_subparsers(dest="brightness_action")
    brightness_set = brightness_subparsers.add_parser("set", help="Set brightness")
    brightness_set.add_argument("value", type=float, help="Brightness level (0.0 - 1.0)")
    brightness_subparsers.add_parser("get", help="Get current brightness")
    
    return parser


async def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    handler = CLIHandler()
    
    try:
        if args.command == "list":
            await handler.list_apps(args.output)
        
        elif args.command == "open":
            await handler.open_app(args.identifier)
        
        elif args.command == "traverse":
            await handler.traverse(args.identifier, args.visible_only, args.output)
        
        elif args.command == "click":
            await handler.click(args.x, args.y, args.visual, args.duration)
        
        elif args.command == "type":
            await handler.type_text(args.text)
        
        elif args.command == "key":
            await handler.press_key(args.key)
        
        elif args.command == "search":
            await handler.search_files(
                name=args.name,
                file_type=args.type,
                start_date=args.start_date,
                end_date=args.end_date,
                locations=args.location,
                max_results=args.max,
                output_file=args.output
            )
        
        elif args.command == "volume":
            if args.volume_action == "set":
                await handler.set_volume(args.value)
            elif args.volume_action == "get":
                await handler.get_volume()
            else:
                parser.print_help()
        
        elif args.command == "brightness":
            if args.brightness_action == "set":
                await handler.set_brightness(args.value)
            elif args.brightness_action == "get":
                await handler.get_brightness()
            else:
                parser.print_help()
        
        else:
            parser.print_help()
    
    except MacosUseSDKError as e:
        print(f"SDK Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def cli_main() -> None:
    """CLI entry point that properly handles async execution."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main() 