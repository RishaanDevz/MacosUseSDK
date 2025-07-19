import AppKit
import Foundation
@preconcurrency import ApplicationServices

// MARK: - Smart Filtering and Aggregation
struct EventAggregator {
    private var lastKeySequence: [String] = []
    private var lastScrollTime: Date = Date.distantPast
    private var lastMouseLocation: CGPoint = CGPoint.zero
    private var lastAppContext: String = ""
    private var sessionStartTime = Date()
    
    mutating func shouldLog(_ eventType: String, location: CGPoint = CGPoint.zero, key: String = "") -> Bool {
        let now = Date()
        
        // Always log important events
        if ["appFocused", "appDefocused", "appLaunched", "appTerminated"].contains(eventType) {
            return true
        }
        
        // Aggregate rapid scrolling (only log every 0.5 seconds)
        if eventType == "scrollWheel" {
            if now.timeIntervalSince(lastScrollTime) < 0.5 {
                return false
            }
            lastScrollTime = now
        }
        
        // Filter out repetitive mouse movements in same area
        if ["leftMouseDown", "rightMouseDown"].contains(eventType) {
            let distance = sqrt(pow(location.x - lastMouseLocation.x, 2) + pow(location.y - lastMouseLocation.y, 2))
            if distance < 50 && now.timeIntervalSince(lastScrollTime) < 1.0 {
                return false // Skip clicks very close to recent activity
            }
            lastMouseLocation = location
        }
        
        // Aggregate typing into sequences
        if eventType == "keyDown" {
            lastKeySequence.append(key)
            if lastKeySequence.count > 10 {
                lastKeySequence.removeFirst()
            }
            // Only log every 5th keystroke or special keys
            return key.count != 1 || lastKeySequence.count % 5 == 0
        }
        
        return true
    }
    
    mutating func getTypingSequence() -> String {
        let sequence = lastKeySequence.joined()
        lastKeySequence.removeAll()
        return sequence
    }
}

// Helper to describe an AXUIElement concisely
func describeElementConcisely(_ element: AXUIElement?) -> [String: Any] {
    guard let el = element else { return ["error": "unknown"] }
    
    // Only get essential attributes
    func getStringAttribute(_ attr: String) -> String? {
        var ref: CFTypeRef?
        AXUIElementCopyAttributeValue(el, attr as CFString, &ref)
        return ref as? String
    }
    
    var result: [String: Any] = [:]
    
    // Core attributes only
    if let role = getStringAttribute(kAXRoleAttribute) {
        result["role"] = role
    }
    if let title = getStringAttribute(kAXTitleAttribute) {
        result["title"] = title
    }
    if let value = getStringAttribute(kAXValueAttribute), !value.isEmpty {
        // Truncate long values
        result["value"] = value.count > 50 ? String(value.prefix(50)) + "..." : value
    }
    if let placeholder = getStringAttribute(kAXPlaceholderValueAttribute) {
        result["placeholder"] = placeholder
    }
    
    // Get one parent for context
    var parentRef: CFTypeRef?
    AXUIElementCopyAttributeValue(el, kAXParentAttribute as CFString, &parentRef)
    if let parent = parentRef, CFGetTypeID(parent) == AXUIElementGetTypeID() {
        let _ = parent as! AXUIElement
        var parentRole: CFTypeRef?
        AXUIElementCopyAttributeValue(parent as! AXUIElement, kAXRoleAttribute as CFString, &parentRole)
        if let role = parentRole as? String {
            result["parentRole"] = role
        }
    }
    
    return result
}

// Get element at a screen position
func elementDescription(at pos: CGPoint) -> [String: Any] {
    let system = AXUIElementCreateSystemWide()
    var el: AXUIElement?
    let err = AXUIElementCopyElementAtPosition(system, Float(pos.x), Float(pos.y), &el)
    if err != .success || el == nil {
        return ["error": "unknown element"]
    }
    return describeElementConcisely(el)
}

// Get element at a screen position (concise version)
func describeElementConcisely(at pos: CGPoint) -> [String: Any] {
    let system = AXUIElementCreateSystemWide()
    var el: AXUIElement?
    let err = AXUIElementCopyElementAtPosition(system, Float(pos.x), Float(pos.y), &el)
    if err != .success || el == nil {
        return ["error": "unknown element"]
    }
    return describeElementConcisely(el)
}

// Get focused element description
func focusedElementDescription() -> [String: Any] {
    let system = AXUIElementCreateSystemWide()
    var cfEl: CFTypeRef?
    let err = AXUIElementCopyAttributeValue(system, kAXFocusedUIElementAttribute as CFString, &cfEl)
    if err != .success {
        return ["error": "unknown element"]
    }
    let el = cfEl as! AXUIElement
    return describeElementConcisely(el)
}

// Tool-specific JSON logging with smart filtering
var eventAggregator = EventAggregator()

func logEvent(data: [String: Any]) {
    var eventData = data
    let timestamp = ISO8601DateFormatter().string(from: Date())
    eventData["timestamp"] = timestamp
    
    // Only add app context occasionally to reduce redundancy
    if ["appFocused", "startup", "leftMouseDown"].contains(eventData["type"] as? String) {
        if let frontmostApp = NSWorkspace.shared.frontmostApplication {
            eventData["app"] = [
                "name": frontmostApp.localizedName ?? "Unknown",
                "bundleId": frontmostApp.bundleIdentifier ?? "Unknown"
            ]
        }
    }

    do {
        let jsonData = try JSONSerialization.data(withJSONObject: eventData, options: [])
        if let jsonString = String(data: jsonData, encoding: .utf8) {
            print(jsonString)
            fflush(stdout)
        }
    } catch {
        print("{\"error\": \"Failed to serialize event to JSON\", \"timestamp\": \"\(timestamp)\"}")
    }
}

func checkAccessibilityPermissions() -> Bool {
    let isTrusted = AXIsProcessTrusted()
    if !isTrusted {
        logEvent(data: ["type": "permissionRequest", "message": "Accessibility permissions not granted. Requesting permissions..."])
        let options: NSDictionary = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true]
        let requestResult = AXIsProcessTrustedWithOptions(options)
        logEvent(data: ["type": "permissionResult", "result": requestResult])
        return requestResult
    }
    logEvent(data: ["type": "permissionCheck", "message": "Accessibility permissions already granted."])
    return true
}

// MARK: - Event Tap Based Monitoring
// Callback for CGEventTap
func eventTapCallback(proxy: CGEventTapProxy, type: CGEventType, event: CGEvent, refcon: UnsafeMutableRawPointer?) -> Unmanaged<CGEvent>? {
    guard let aggregatorPtr = refcon?.assumingMemoryBound(to: EventAggregator.self) else {
        return Unmanaged.passUnretained(event)
    }
    
    let loc = event.location
    
    switch type {
    case .leftMouseDown:
        if aggregatorPtr.pointee.shouldLog("leftMouseDown", location: loc) {
            let eventData: [String: Any] = [
                "type": "leftMouseDown",
                "position": ["x": loc.x, "y": loc.y],
                "element": describeElementConcisely(at: loc)
            ]
            logEvent(data: eventData)
        }
        
    case .keyDown:
        var chars = [UniChar](repeating: 0, count: 4)
        var length: Int = 0
        event.keyboardGetUnicodeString(maxStringLength: 4, actualStringLength: &length, unicodeString: &chars)
        let keyChar = String(utf16CodeUnits: chars, count: length)
        
        if aggregatorPtr.pointee.shouldLog("keyDown", key: keyChar) {
            let eventData: [String: Any] = [
                "type": "keyDown",
                "key": keyChar,
                "element": focusedElementDescription()
            ]
            logEvent(data: eventData)
        }
        
    case .scrollWheel:
        if aggregatorPtr.pointee.shouldLog("scrollWheel", location: loc) {
            let dy = event.getDoubleValueField(.scrollWheelEventDeltaAxis1)
            let dx = event.getDoubleValueField(.scrollWheelEventDeltaAxis2)
            let eventData: [String: Any] = [
                "type": "scrollWheel",
                "position": ["x": loc.x, "y": loc.y],
                "delta": ["dx": dx, "dy": dy],
                "element": describeElementConcisely(at: loc)
            ]
            logEvent(data: eventData)
        }
        
    default:
        break
    }
    return Unmanaged.passUnretained(event)
}

func monitorEvents() {
    logEvent(data: ["type": "monitoring", "message": "Setting up CG event taps..."])
    
    // Create and allocate EventAggregator
    let aggregator = UnsafeMutablePointer<EventAggregator>.allocate(capacity: 1)
    aggregator.initialize(to: EventAggregator())
    
    let leftMouseDown = CGEventMask(1 << CGEventType.leftMouseDown.rawValue)
    let scrollWheel = CGEventMask(1 << CGEventType.scrollWheel.rawValue)
    let keyDown = CGEventMask(1 << CGEventType.keyDown.rawValue)
    
    let mask = leftMouseDown | scrollWheel | keyDown
    
    guard let eventTap = CGEvent.tapCreate(
        tap: .cgSessionEventTap,
        place: .headInsertEventTap,
        options: .defaultTap,
        eventsOfInterest: mask,
        callback: eventTapCallback,
        userInfo: UnsafeMutableRawPointer(aggregator)
    ) else {
        logEvent(data: ["type": "error", "message": "Failed to create event tap. Ensure permissions are granted."])
        aggregator.deallocate()
        exit(1)
    }
    let runLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, eventTap, 0)
    CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, .commonModes)
    CGEvent.tapEnable(tap: eventTap, enable: true)
    logEvent(data: ["type": "monitoring", "message": "CG event taps set up. Monitoring started..."])
}

// Set up signal handler for graceful shutdown
signal(SIGINT) { _ in
    logEvent(data: ["type": "shutdown", "reason": "Received SIGINT"])
    exit(0)
}

// Monitor app focus changes
let workspace = NSWorkspace.shared
workspace.notificationCenter.addObserver(forName: NSWorkspace.didActivateApplicationNotification, object: nil, queue: nil) { note in
    if let app = note.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication {
        let name = app.localizedName ?? app.bundleIdentifier ?? "UnknownApp"
        logEvent(data: [
            "type": "appFocused",
            "application": [
                "name": name,
                "bundleId": app.bundleIdentifier ?? "",
                "processId": app.processIdentifier
            ]
        ])
    }
}
workspace.notificationCenter.addObserver(forName: NSWorkspace.didDeactivateApplicationNotification, object: nil, queue: nil) { note in
    if let app = note.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication {
        let name = app.localizedName ?? app.bundleIdentifier ?? "UnknownApp"
        logEvent(data: [
            "type": "appDefocused",
            "application": [
                "name": name,
                "bundleId": app.bundleIdentifier ?? "",
                "processId": app.processIdentifier
            ]
        ])
    }
}

// Monitor app launches and quits
workspace.notificationCenter.addObserver(forName: NSWorkspace.didLaunchApplicationNotification, object: nil, queue: nil) { note in
    if let app = note.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication {
        let name = app.localizedName ?? app.bundleIdentifier ?? "UnknownApp"
        logEvent(data: [
            "type": "appLaunched",
            "application": [
                "name": name,
                "bundleId": app.bundleIdentifier ?? "",
                "processId": app.processIdentifier
            ]
        ])
    }
}
workspace.notificationCenter.addObserver(forName: NSWorkspace.didTerminateApplicationNotification, object: nil, queue: nil) { note in
    if let app = note.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication {
        let name = app.localizedName ?? app.bundleIdentifier ?? "UnknownApp"
        logEvent(data: [
            "type": "appTerminated",
            "application": [
                "name": name,
                "bundleId": app.bundleIdentifier ?? "",
                "processId": app.processIdentifier
            ]
        ])
    }
}

if checkAccessibilityPermissions() {
    logEvent(data: ["type": "startup", "message": "Starting usage monitoring. Press Ctrl+C to stop."])
    monitorEvents()
    
    // Keep the run loop alive
    logEvent(data: ["type": "startup", "message": "Starting run loop..."])
    RunLoop.main.run()
} else {
    logEvent(data: ["type": "error", "message": "Accessibility permissions are required."])
    logEvent(data: ["type": "error", "message": "Please grant permissions in System Settings > Privacy & Security > Accessibility."])
    logEvent(data: ["type": "error", "message": "After granting permissions, please restart the tool."])
    exit(1)
}
