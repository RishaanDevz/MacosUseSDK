# UsageMonitor API Guide

The `UsageMonitor` in MacosUseSDK provides a powerful way to monitor and capture user events on macOS, including mouse clicks, key presses, scrolling, and application focus changes. Unlike `InputController` which simulates input, `UsageMonitor` passively observes and captures real user interactions.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Basic Usage](#basic-usage)
- [Event Types](#event-types)
- [Data Structures](#data-structures)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The UsageMonitor provides:
- **Passive Event Monitoring**: Capture real user interactions without interfering
- **Smart Event Filtering**: Intelligent aggregation to avoid spam from rapid events
- **Rich Context**: Detailed information about UI elements and applications
- **Multiple Handler Types**: Specific handlers for different event types
- **Background Monitoring**: Continuous monitoring with minimal performance impact

### Comparison with InputController

| Feature | UsageMonitor | InputController |
|---------|--------------|-----------------|
| Purpose | Observe user events | Simulate user events |
| Direction | Input (capture) | Output (generate) |
| Usage Pattern | `monitor.onMouseClick { ... }` | `MacosUseSDK.clickMouse(at: point)` |
| Permissions | Accessibility permissions required | Accessibility permissions required |
| Performance | Passive monitoring | Active simulation |

## Prerequisites

### Accessibility Permissions

The UsageMonitor requires accessibility permissions to function. Your app must:

1. **Request permissions programmatically**:
```swift
// Check if permissions are granted
let hasPermissions = UsageMonitor.shared.startMonitoring()
if !hasPermissions {
    print("❌ Accessibility permissions required")
    // Guide user to System Preferences
}
```

2. **Add to Info.plist** (for full apps):
```xml
<key>NSAppleEventsUsageDescription</key>
<string>This app needs accessibility access to monitor user interactions.</string>
```

3. **Manual permission setup**:
   - System Preferences → Security & Privacy → Privacy → Accessibility
   - Add your application to the list

## Basic Usage

### Quick Start - Monitor All Events

```swift
import MacosUseSDK

// Start monitoring with a general handler
let success = startUsageMonitoring { event in
    print("📊 Event: \(event.type) at \(event.timestamp)")
    
    switch event.type {
    case "leftMouseDown":
        if let pos = event.position, let element = event.element {
            print("🖱️ Clicked at (\(pos.x), \(pos.y)) on \(element.role ?? "unknown")")
        }
    case "keyDown":
        if let key = event.key, let element = event.element {
            print("⌨️ Pressed '\(key)' in \(element.role ?? "unknown")")
        }
    case "appFocused":
        if let app = event.application {
            print("🎯 Focused: \(app.name)")
        }
    default:
        print("📝 Other event: \(event.type)")
    }
}

if success {
    print("✅ Monitoring started successfully")
    // Keep your app running to continue monitoring
    RunLoop.main.run()
} else {
    print("❌ Failed to start monitoring - check permissions")
}
```

### Specific Event Monitoring

```swift
import MacosUseSDK

let monitor = UsageMonitor.shared

// Monitor only mouse clicks
let success = monitorMouseClicks { position, element in
    print("🖱️ Click at (\(position.x), \(position.y))")
    print("   Element: \(element.role ?? "unknown") - '\(element.title ?? element.value ?? "no title")'")
    
    // Example: React to clicks on specific elements
    if element.role == "AXButton" {
        print("   → Button clicked!")
    }
}

// Monitor only key presses
monitorKeyPresses { key, element in
    print("⌨️ Key '\(key)' pressed in \(element.role ?? "unknown")")
    
    // Example: Log typing in text fields
    if element.role == "AXTextField" || element.role == "AXTextArea" {
        print("   → Typing in text field: \(element.value ?? "")")
    }
}

// Monitor app focus changes
monitorAppFocus { app in
    print("🎯 Switched to: \(app.name) (PID: \(app.processId))")
}
```

## Event Types

### Mouse Events

| Event Type | Description | Data Available |
|------------|-------------|----------------|
| `leftMouseDown` | Left mouse button clicked | `position`, `element` |
| `rightMouseDown` | Right mouse button clicked | `position`, `element` |
| `scrollWheel` | Mouse wheel scrolled | `position`, `element`, `scrollDelta` |

### Keyboard Events

| Event Type | Description | Data Available |
|------------|-------------|----------------|
| `keyDown` | Key pressed | `key`, `element` (focused element) |

### Application Events

| Event Type | Description | Data Available |
|------------|-------------|----------------|
| `appFocused` | Application gained focus | `application` |
| `appDefocused` | Application lost focus | `application` |
| `appLaunched` | Application started | `application` |
| `appTerminated` | Application quit | `application` |

## Data Structures

### UsageEvent

The main event structure containing all event information:

```swift
public struct UsageEvent: Codable, Sendable {
    public let type: String              // Event type (see above)
    public let timestamp: String         // ISO8601 formatted timestamp
    public let position: CGPoint?        // Screen coordinates (for mouse events)
    public let element: ElementInfo?     // UI element information
    public let key: String?              // Key pressed (for keyboard events)
    public let application: ApplicationInfo? // App information
    public let scrollDelta: ScrollDelta? // Scroll information
}
```

### ElementInfo

Detailed information about UI elements:

```swift
public struct ElementInfo: Codable, Sendable {
    public let role: String?         // AXRole (e.g., "AXButton", "AXTextField")
    public let title: String?        // Element title or label
    public let value: String?        // Current value (for text fields, etc.)
    public let placeholder: String?  // Placeholder text
    public let parentRole: String?   // Parent element role
    public let error: String?        // Error if element couldn't be read
}
```

### ApplicationInfo

Information about applications:

```swift
public struct ApplicationInfo: Codable, Sendable {
    public let name: String          // App name (e.g., "Safari")
    public let bundleId: String      // Bundle identifier
    public let processId: Int32      // Process ID
}
```

### ScrollDelta

Scroll wheel movement information:

```swift
public struct ScrollDelta: Codable, Sendable {
    public let dx: Double  // Horizontal scroll (-/+ for left/right)
    public let dy: Double  // Vertical scroll (-/+ for up/down)
}
```

## API Reference

### UsageMonitor Class

#### Core Methods

```swift
// Start/Stop monitoring
public func startMonitoring() -> Bool
public func stopMonitoring()
public var isRunning: Bool { get }

// General event registration
public func onEvent(_ eventType: String, handler: @escaping UsageEventHandler)

// Specific event handlers
public func onMouseClick(handler: @escaping MouseClickHandler)
public func onKeyPress(handler: @escaping KeyPressHandler)
public func onAppFocus(handler: @escaping AppFocusHandler)
public func onScroll(handler: @escaping ScrollHandler)

// Handler management
public func removeHandlers(for eventType: String)
public func removeAllHandlers()
```

#### Type Aliases

```swift
public typealias UsageEventHandler = (UsageEvent) -> Void
public typealias MouseClickHandler = (CGPoint, ElementInfo) -> Void
public typealias KeyPressHandler = (String, ElementInfo) -> Void
public typealias AppFocusHandler = (ApplicationInfo) -> Void
public typealias ScrollHandler = (CGPoint, ScrollDelta, ElementInfo) -> Void
```

### Convenience Functions

```swift
// Start monitoring with general handler
public func startUsageMonitoring(handler: @escaping UsageEventHandler) -> Bool

// Start monitoring specific event types
public func monitorMouseClicks(handler: @escaping MouseClickHandler) -> Bool
public func monitorKeyPresses(handler: @escaping KeyPressHandler) -> Bool
public func monitorAppFocus(handler: @escaping AppFocusHandler) -> Bool

// Stop all monitoring
public func stopUsageMonitoring()
```

## Examples

### Example 1: User Activity Logger

```swift
import MacosUseSDK
import Foundation

class ActivityLogger {
    private let monitor = UsageMonitor.shared
    private var logFile: FileHandle?
    
    func startLogging(to fileName: String) {
        // Create log file
        let url = URL(fileURLWithPath: fileName)
        FileManager.default.createFile(atPath: fileName, contents: nil)
        logFile = try? FileHandle(forWritingTo: url)
        
        // Register for all events
        let success = startUsageMonitoring { [weak self] event in
            self?.logEvent(event)
        }
        
        if success {
            print("✅ Activity logging started")
        } else {
            print("❌ Failed to start logging")
        }
    }
    
    private func logEvent(_ event: UsageEvent) {
        let logEntry = """
        [\(event.timestamp)] \(event.type)
        """
        
        var details: [String] = []
        
        if let pos = event.position {
            details.append("position: (\(pos.x), \(pos.y))")
        }
        
        if let element = event.element {
            let elementDesc = element.role ?? "unknown"
            let elementTitle = element.title ?? element.value ?? "no title"
            details.append("element: \(elementDesc) - '\(elementTitle)'")
        }
        
        if let key = event.key {
            details.append("key: '\(key)'")
        }
        
        if let app = event.application {
            details.append("app: \(app.name)")
        }
        
        if let scroll = event.scrollDelta {
            details.append("scroll: dx=\(scroll.dx), dy=\(scroll.dy)")
        }
        
        let fullLog = logEntry + (details.isEmpty ? "" : " | " + details.joined(separator: ", ")) + "\n"
        
        print(fullLog.trimmingCharacters(in: .whitespacesAndNewlines))
        logFile?.write(fullLog.data(using: .utf8) ?? Data())
    }
    
    func stopLogging() {
        stopUsageMonitoring()
        logFile?.closeFile()
        print("📝 Logging stopped")
    }
}

// Usage
let logger = ActivityLogger()
logger.startLogging(to: "user_activity.log")

// Keep running
signal(SIGINT) { _ in
    logger.stopLogging()
    exit(0)
}
RunLoop.main.run()
```

### Example 2: App Usage Tracker

```swift
import MacosUseSDK
import Foundation

class AppUsageTracker {
    private var appUsageTime: [String: TimeInterval] = [:]
    private var currentApp: String?
    private var lastFocusTime: Date?
    
    func startTracking() {
        let success = monitorAppFocus { [weak self] app in
            self?.handleAppFocus(app)
        }
        
        if success {
            print("📊 App usage tracking started")
        }
    }
    
    private func handleAppFocus(_ app: ApplicationInfo) {
        let now = Date()
        
        // Record time for previous app
        if let currentApp = currentApp,
           let lastTime = lastFocusTime {
            let timeSpent = now.timeIntervalSince(lastTime)
            appUsageTime[currentApp, default: 0] += timeSpent
        }
        
        // Update current app
        currentApp = app.name
        lastFocusTime = now
        
        print("🎯 Switched to: \(app.name)")
        printUsageStats()
    }
    
    private func printUsageStats() {
        print("\n📈 App Usage Statistics:")
        let sorted = appUsageTime.sorted { $0.value > $1.value }
        for (app, time) in sorted.prefix(5) {
            let minutes = Int(time / 60)
            let seconds = Int(time.truncatingRemainder(dividingBy: 60))
            print("   \(app): \(minutes)m \(seconds)s")
        }
        print("")
    }
}

// Usage
let tracker = AppUsageTracker()
tracker.startTracking()
RunLoop.main.run()
```

### Example 3: Form Interaction Monitor

```swift
import MacosUseSDK

class FormInteractionMonitor {
    private var formFields: Set<String> = []
    
    func startMonitoring() {
        let monitor = UsageMonitor.shared
        
        // Monitor clicks on form elements
        monitor.onMouseClick { [weak self] position, element in
            self?.handleFormClick(position, element)
        }
        
        // Monitor typing in form fields
        monitor.onKeyPress { [weak self] key, element in
            self?.handleFormTyping(key, element)
        }
        
        let success = monitor.startMonitoring()
        if success {
            print("📝 Form monitoring started")
        }
    }
    
    private func handleFormClick(_ position: CGPoint, _ element: ElementInfo) {
        if isFormElement(element) {
            let fieldId = getFieldIdentifier(element)
            formFields.insert(fieldId)
            print("👆 Clicked form field: \(fieldId)")
        }
    }
    
    private func handleFormTyping(_ key: String, _ element: ElementInfo) {
        if isFormElement(element) {
            let fieldId = getFieldIdentifier(element)
            print("⌨️ Typing in field: \(fieldId) - key: '\(key)'")
        }
    }
    
    private func isFormElement(_ element: ElementInfo) -> Bool {
        guard let role = element.role else { return false }
        return ["AXTextField", "AXTextArea", "AXSecureTextField", 
                "AXComboBox", "AXCheckBox", "AXRadioButton"].contains(role)
    }
    
    private func getFieldIdentifier(_ element: ElementInfo) -> String {
        return element.title ?? element.placeholder ?? element.value ?? "unknown_field"
    }
}

// Usage
let formMonitor = FormInteractionMonitor()
formMonitor.startMonitoring()
RunLoop.main.run()
```

### Example 4: Productivity Monitor

```swift
import MacosUseSDK
import Foundation

class ProductivityMonitor {
    private var keyPressCount = 0
    private var mouseClickCount = 0
    private var scrollCount = 0
    private var sessionStart = Date()
    
    func startMonitoring() {
        let monitor = UsageMonitor.shared
        
        // Count different types of interactions
        monitor.onEvent("keyDown") { [weak self] _ in
            self?.keyPressCount += 1
        }
        
        monitor.onEvent("leftMouseDown") { [weak self] _ in
            self?.mouseClickCount += 1
        }
        
        monitor.onEvent("scrollWheel") { [weak self] _ in
            self?.scrollCount += 1
        }
        
        let success = monitor.startMonitoring()
        if success {
            print("📊 Productivity monitoring started")
            
            // Print stats every 30 seconds
            Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
                self?.printStats()
            }
        }
    }
    
    private func printStats() {
        let elapsed = Date().timeIntervalSince(sessionStart)
        let minutes = Int(elapsed / 60)
        
        print("""
        
        📊 Productivity Stats (\(minutes) minutes):
           ⌨️  Key presses: \(keyPressCount)
           🖱️  Mouse clicks: \(mouseClickCount)
           📜 Scrolls: \(scrollCount)
           🚀 Actions per minute: \(Int(Double(keyPressCount + mouseClickCount) / elapsed * 60))
        
        """)
    }
}

// Usage
let productivityMonitor = ProductivityMonitor()
productivityMonitor.startMonitoring()
RunLoop.main.run()
```

## Best Practices

### Performance Optimization

1. **Use specific event handlers** when possible instead of general `onEvent`:
```swift
// ✅ Preferred - more efficient
monitor.onMouseClick { position, element in ... }

// ❌ Less efficient for specific needs
monitor.onEvent("leftMouseDown") { event in ... }
```

2. **Limit event processing**:
```swift
monitor.onKeyPress { key, element in
    // ✅ Quick processing
    if key == "\r" {  // Enter key
        handleEnterPress()
    }
    
    // ❌ Avoid heavy operations in handlers
    // processLargeDataSet()  // Don't do this!
}
```

3. **Use event aggregation** - the monitor already filters rapid events, but you can add your own:
```swift
private var lastProcessTime = Date.distantPast

monitor.onScroll { position, delta, element in
    let now = Date()
    guard now.timeIntervalSince(lastProcessTime) > 0.1 else { return }
    lastProcessTime = now
    
    // Process scroll event
}
```

### Memory Management

1. **Use weak references** in closures to avoid retain cycles:
```swift
class MyMonitor {
    func setupMonitoring() {
        monitor.onMouseClick { [weak self] position, element in
            self?.handleClick(position, element)
        }
    }
}
```

2. **Clean up handlers** when done:
```swift
// Remove specific event handlers
monitor.removeHandlers(for: "leftMouseDown")

// Or remove all handlers
monitor.removeAllHandlers()
```

### Error Handling

1. **Check permissions before starting**:
```swift
guard monitor.startMonitoring() else {
    print("❌ Accessibility permissions required")
    print("Go to System Preferences → Security & Privacy → Privacy → Accessibility")
    return
}
```

2. **Handle missing element information gracefully**:
```swift
monitor.onMouseClick { position, element in
    let elementDescription = element.role ?? "unknown element"
    let elementTitle = element.title ?? element.value ?? "no title"
    print("Clicked \(elementDescription): \(elementTitle)")
}
```

### Threading Considerations

1. **Event handlers run on background threads** - dispatch to main queue for UI updates:
```swift
monitor.onMouseClick { position, element in
    DispatchQueue.main.async {
        // Update UI here
        self.updateClickIndicator(at: position)
    }
}
```

2. **Keep the run loop active** for continuous monitoring:
```swift
// In command-line tools
RunLoop.main.run()

// In GUI apps, the run loop is already active
```

## Troubleshooting

### Common Issues

#### 1. "Accessibility permissions required"

**Problem**: `startMonitoring()` returns `false`

**Solution**:
- Go to System Preferences → Security & Privacy → Privacy → Accessibility
- Add your application to the list
- Restart your application

#### 2. Events not being captured

**Problem**: Event handlers not being called

**Possible causes**:
- Accessibility permissions not granted
- App not running with sufficient privileges
- Event handlers registered after `startMonitoring()`

**Solution**:
```swift
// ✅ Register handlers before starting
monitor.onMouseClick { ... }
monitor.onKeyPress { ... }
let success = monitor.startMonitoring()  // Start after registration
```

#### 3. App hangs or crashes

**Problem**: Application becomes unresponsive

**Possible causes**:
- Heavy processing in event handlers
- Retain cycles with closures
- Missing run loop

**Solution**:
```swift
// ✅ Keep handlers lightweight
monitor.onKeyPress { [weak self] key, element in
    DispatchQueue.global(qos: .background).async {
        // Heavy processing on background queue
        self?.processEvent(key: key)
    }
}

// ✅ Ensure run loop is active
RunLoop.main.run()
```

#### 4. Element information is incomplete

**Problem**: `ElementInfo` has `nil` values for most properties

**Possible causes**:
- Some applications don't expose full accessibility information
- Element is not accessible or hidden

**Solution**:
```swift
monitor.onMouseClick { position, element in
    // ✅ Handle missing information gracefully
    if let role = element.role {
        print("Element: \(role)")
    } else if let error = element.error {
        print("Element error: \(error)")
    } else {
        print("Unknown element at \(position)")
    }
}
```

### Debug Tips

1. **Enable verbose logging**:
```swift
monitor.onEvent("leftMouseDown") { event in
    print("🐛 Full event: \(event)")
}
```

2. **Test with simple applications** first (Calculator, TextEdit) before complex ones

3. **Check system console** for accessibility-related errors:
```bash
log stream --predicate 'subsystem == "com.apple.accessibility"'
```

4. **Verify your app's permissions**:
```bash
# Check if your app has accessibility permissions
sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db \
"SELECT service, client, allowed FROM access WHERE service='kTCCServiceAccessibility';"
```

## Integration with Other MacosUseSDK Components

The UsageMonitor works well with other MacosUseSDK components:

### With InputController

```swift
// Monitor clicks, then simulate response
monitor.onMouseClick { position, element in
    if element.role == "AXButton" && element.title == "Submit" {
        // Simulate additional action after user clicks Submit
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            try? MacosUseSDK.pressKey(keyCode: KEY_RETURN)
        }
    }
}
```

### With AppOpener

```swift
// Monitor app launches, then interact with them
monitor.onEvent("appLaunched") { event in
    if let app = event.application, app.name == "Calculator" {
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            // Open Calculator and perform operations
            let response = try? MacosUseSDK.traverseAccessibilityTree(pid: app.processId)
            // ... interact with Calculator
        }
    }
}
```

This comprehensive guide should help you effectively use the UsageMonitor to capture and respond to user events in your macOS applications. The monitor provides a powerful foundation for building user behavior analytics, automation tools, and accessibility enhancements.
