# MacOS Smart Usage Monitor Tool

An intelligent real-time activity monitoring tool for macOS that captures meaningful user interactions with UI content extraction and automatic screenshots. Designed specifically for LLM integration and automation training.

## 🎯 Smart Features

### 📱 UI Content Capture
- **Automatic screenshots** on user interactions
- **Text extraction** from active windows and UI elements
- **Element identification** - knows what you clicked on
- **App context tracking** - understands which app and window you're using
- **Periodic UI snapshots** - captures content every 30 seconds

### 🖱️ Meaningful Mouse Events
- **Click capture with context** - screenshots and UI content when you click
- **Smart scroll detection** - only logs significant scrolling actions
- **Reduced noise** - no constant mouse movement spam

### ⌨️ Intelligent Keyboard Monitoring
- **Text accumulation** - batches typed content into meaningful chunks
- **Smart logging** - captures text every 50 characters or 10 seconds
- **Context awareness** - knows which app you're typing in

### 🖥️ Application Context
- **App switching detection** - captures UI when you change applications
- **Window title tracking** - knows what document/page you're viewing
- **Bundle identification** - tracks specific applications

## 🗂️ Data Organization

The tool creates a structured data folder in your home directory:

```
~/usage_monitor_data/
├── screenshots/           # Automatic screenshots
│   ├── screenshot_1_2025-07-19T02-55-51.png
│   └── screenshot_2_2025-07-19T02-56-21.png
└── logs/                 # JSON event logs (if redirected)
```

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

Events are logged as structured JSON with three main categories:

### Categories:
- `[USER_ACTION]` - User clicks, typing, scrolling with UI context
- `[UI_CAPTURE]` - Periodic UI content and screenshots
- `[APP_SWITCH]` - Application focus changes

### Example Output:

```json
[USER_ACTION] {
  "timestamp": "2025-07-19T02:55:51Z",
  "type": "click",
  "target": "AXButton",
  "content": "Send Message",
  "position": {"x": 150.5, "y": 200.3},
  "appContext": "Messages - Chat with John",
  "screenshot": "/Users/user/usage_monitor_data/screenshots/screenshot_1_2025-07-19T02-55-51.png"
}

[USER_ACTION] {
  "timestamp": "2025-07-19T02:55:52Z",
  "type": "type",
  "content": "Hey, how's the project going?",
  "appContext": "Messages - Chat with John"
}

[UI_CAPTURE] {
  "timestamp": "2025-07-19T02:56:21Z",
  "type": "periodic_capture",
  "appName": "Messages",
  "windowTitle": "Chat with John",
  "textContent": "Hey, how's the project going? Great! Almost done with the API integration...",
  "screenshotPath": "/Users/user/usage_monitor_data/screenshots/screenshot_2_2025-07-19T02-56-21.png"
}
```

## Perfect for LLM Integration

The smart monitoring approach makes it ideal for:

### 🤖 AI Training Data
- **Context-rich interactions** - knows what you clicked and why
- **Visual + text data** - screenshots paired with extracted text
- **Conversation capture** - can see both sides of messaging apps
- **Workflow understanding** - tracks app usage patterns

### 📊 Productivity Analysis
- **Task switching patterns** - see how you move between applications
- **Content consumption** - what you read and interact with
- **Work patterns** - understand focus time and distractions

## Usage

```bash
# Build and run
swift build
./.build/debug/UsageMonitorTool

# Or run in release mode for better performance
swift build -c release
./.build/release/UsageMonitorTool
```

## LLM Integration Examples

```bash
# Stream meaningful events to a file
./.build/debug/UsageMonitorTool > ~/usage_data.jsonl

# Process with Python script
./.build/debug/UsageMonitorTool | python3 analyze_usage.py

# Filter only user actions
./.build/debug/UsageMonitorTool | grep "\\[USER_ACTION\\]"

# Extract UI captures only
./.build/debug/UsageMonitorTool | grep "\\[UI_CAPTURE\\]"
```

## Smart Filtering Features

- **Batched text input** - No keystroke spam, just meaningful content
- **Context-aware screenshots** - Only captures when something interesting happens
- **Reduced event volume** - ~90% fewer events compared to raw monitoring
- **Rich metadata** - Every event includes application context and UI information

## Privacy & Security

⚠️ **Enhanced Privacy Awareness:**

1. **Screenshot storage** - Images are saved locally in `~/usage_monitor_data/`
2. **UI text extraction** - Can capture sensitive information from applications
3. **Message content** - Will capture conversations, passwords, and private data
4. **Automatic capture** - Takes screenshots every 30 seconds
5. **Local storage only** - No data transmitted, but files contain sensitive information

**Recommendations:**
- Regularly clean the `~/usage_monitor_data/` directory
- Exclude sensitive applications from monitoring if possible
- Encrypt the data directory for additional security
- Review captured screenshots before sharing or analyzing

## Performance Impact

- **Minimal CPU usage** - Smart event filtering reduces processing
- **Storage efficient** - PNG screenshots and JSON logs
- **Memory friendly** - Streams data instead of accumulating
- **Battery conscious** - Reduced monitoring frequency

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
