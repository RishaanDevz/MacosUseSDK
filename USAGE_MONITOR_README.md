# MacOS Usage Monitor Tool

A comprehensive real-time activity monitoring tool for macOS that tracks all user interactions including mouse movements, keyboard input, application events, file system changes, network activity, and system metrics.

## Features

The UsageMonitorTool tracks the following activities in real-time:

### 🖱️ Mouse Events
- **Mouse movements** (with position coordinates)
- **Mouse clicks** (left, right, middle button)
- **Scroll wheel events** (with delta values)
- **Drag operations**
- **Click pressure** (for supported devices)
- **Modifier keys** during mouse events

### ⌨️ Keyboard Events
- **Key presses and releases** (with key codes)
- **Character input** (when available)
- **Modifier key changes** (Shift, Control, Option, Command, etc.)
- **Key repeat detection**

### 🖥️ Application Events
- **App launches and terminations**
- **App activation/deactivation** (focus changes)
- **Process IDs and bundle identifiers**
- **Window title changes** (when available)

### 📂 File System Events
- **File creation, modification, deletion**
- **File and directory renames**
- **Real-time file system monitoring**
- **Path information for all changes**

### 🌐 Network Events
- **Network activity monitoring**
- **Connection tracking** (simplified)
- **Protocol identification**

### 💻 System Events
- **CPU usage monitoring**
- **Memory usage statistics**
- **Battery status** (for laptops)
- **Thermal state monitoring**
- **System performance metrics**

## Prerequisites

### Accessibility Permissions
The tool requires accessibility permissions to monitor system events. Grant permissions in:
**System Settings → Privacy & Security → Accessibility**

Add your terminal application or the built executable to the allowed applications.

### macOS Version
- Requires macOS 12.0 or later
- Compatible with Apple Silicon and Intel Macs

## Building

```bash
cd /path/to/MacosUseSDK
swift build
```

## Running

```bash
# Run the built executable
./.build/debug/UsageMonitorTool

# Or run in release mode for better performance
swift build -c release
./.build/release/UsageMonitorTool
```

## Output Format

All events are logged as JSON objects to stdout with the following format:

```
[CATEGORY] {JSON_EVENT_DATA}
```

### Categories:
- `[MOUSE]` - Mouse events
- `[KEYBOARD]` - Keyboard events
- `[APPLICATION]` - App events
- `[FILESYSTEM]` - File system events
- `[NETWORK]` - Network events
- `[SYSTEM]` - System events

### Example Output:

```json
[MOUSE] {"y":882.46,"x":1143.87,"timestamp":"2025-07-19T02:55:51Z","type":"move","modifierFlags":[]}
[KEYBOARD] {"timestamp":"2025-07-19T02:55:51Z","type":"key_down","keyCode":36,"character":"\\r","modifierFlags":[],"isRepeat":false}
[APPLICATION] {"timestamp":"2025-07-19T02:55:51Z","type":"activate","appName":"Safari","bundleId":"com.apple.Safari","processId":1234}
[FILESYSTEM] {"path":"/Users/user/Documents/file.txt","type":"file_system_change","eventFlags":["created","file"],"timestamp":"2025-07-19T02:55:51Z"}
[NETWORK] {"timestamp":"2025-07-19T02:55:51Z","type":"network_activity_check","networkProtocol":"tcp"}
[SYSTEM] {"timestamp":"2025-07-19T02:55:51Z","type":"system_status","details":"{\"cpu_usage\":23.5,\"memory_usage\":{\"physical_memory\":8589934592}}"}
```

## Integration with LLM

The JSON output format makes it easy to pipe the data to LLM processing systems:

```bash
# Stream to a file for analysis
./.build/debug/UsageMonitorTool > usage_log.jsonl

# Pipe to processing script
./.build/debug/UsageMonitorTool | python3 process_usage_data.py

# Filter specific event types
./.build/debug/UsageMonitorTool | grep "\\[KEYBOARD\\]"
```

## Use Cases

### 1. Productivity Analysis
Monitor application usage patterns, typing speed, and work habits.

### 2. Security Monitoring
Track file access patterns and system interactions for security analysis.

### 3. User Experience Research
Analyze user interaction patterns for UX improvements.

### 4. Automation Training Data
Generate training data for AI automation systems.

### 5. Digital Wellness
Monitor screen time and interaction patterns for health insights.

## Event Types Reference

### Mouse Events
```typescript
{
  timestamp: Date,
  type: "move" | "click_down" | "click_up" | "drag" | "scroll",
  x: number,
  y: number,
  button?: "left" | "right" | "middle",
  clickCount?: number,
  scrollDelta?: {x: number, y: number},
  pressure?: number,
  modifierFlags: string[]
}
```

### Keyboard Events
```typescript
{
  timestamp: Date,
  type: "key_down" | "key_up" | "modifier_changed",
  keyCode: number,
  character?: string,
  modifierFlags: string[],
  isRepeat: boolean
}
```

### Application Events
```typescript
{
  timestamp: Date,
  type: "launch" | "terminate" | "activate" | "deactivate",
  appName: string,
  bundleId?: string,
  processId: number,
  windowTitle?: string,
  windowBounds?: {x: number, y: number, width: number, height: number}
}
```

## Performance Considerations

- **Mouse movement filtering**: Only logs every 10th movement event to reduce spam
- **Efficient event handling**: Uses Core Graphics event taps for low-level access
- **Memory usage**: Streams events rather than storing in memory
- **CPU impact**: Minimal CPU overhead with optimized event processing

## Privacy and Security

⚠️ **Important Privacy Notes:**

1. This tool captures **all** user input including passwords and sensitive information
2. **Only use on systems you own** or have explicit permission to monitor
3. **Secure the output data** appropriately as it contains sensitive information
4. **Comply with local privacy laws** and regulations
5. Consider **filtering sensitive data** before storing or transmitting

## Stopping the Tool

- Press `Ctrl+C` to stop monitoring
- Or send a SIGTERM signal to the process

## Troubleshooting

### "Failed to create event tap"
- Ensure accessibility permissions are granted
- Try running with `sudo` (not recommended for security)
- Restart the terminal application after granting permissions

### High CPU Usage
- Mouse movement events can be frequent; consider increasing the filter interval
- Use release build for better performance
- Monitor specific event types only if needed

### Permission Denied
- Grant accessibility permissions in System Settings
- Ensure the terminal app is in the accessibility list
- May need to restart the terminal after granting permissions

## Advanced Usage

### Filtering Events
```bash
# Only keyboard events
./.build/debug/UsageMonitorTool | grep "\\[KEYBOARD\\]"

# Only application events
./.build/debug/UsageMonitorTool | grep "\\[APPLICATION\\]"

# Exclude mouse movements (reduce noise)
./.build/debug/UsageMonitorTool | grep -v '"type":"move"'
```

### Processing with jq
```bash
# Extract just the event types
./.build/debug/UsageMonitorTool | grep "\\[MOUSE\\]" | jq -r '.type'

# Get application launches only
./.build/debug/UsageMonitorTool | grep "\\[APPLICATION\\]" | jq 'select(.type == "launch")'
```

This tool is designed to provide comprehensive system monitoring for automation, analytics, and research purposes. Use responsibly and in compliance with applicable privacy laws.
