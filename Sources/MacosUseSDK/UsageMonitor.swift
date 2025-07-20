import AppKit
import Foundation
@preconcurrency import ApplicationServices

// MARK: - Public Data Structures

public struct ElementInfo: Codable, Sendable {
    public let role: String?
    public let title: String?
    public let value: String?
    public let placeholder: String?
    public let parentRole: String?
    public let error: String?
    
    public init(role: String? = nil, title: String? = nil, value: String? = nil, placeholder: String? = nil, parentRole: String? = nil, error: String? = nil) {
        self.role = role
        self.title = title
        self.value = value
        self.placeholder = placeholder
        self.parentRole = parentRole
        self.error = error
    }
}

public struct UsageEvent: Codable, Sendable {
    public let type: String
    public let timestamp: String
    public let position: CGPoint?
    public let element: ElementInfo?
    public let key: String?
    public let application: ApplicationInfo?
    public let scrollDelta: ScrollDelta?
    
    public init(type: String, timestamp: String, position: CGPoint? = nil, element: ElementInfo? = nil, key: String? = nil, application: ApplicationInfo? = nil, scrollDelta: ScrollDelta? = nil) {
        self.type = type
        self.timestamp = timestamp
        self.position = position
        self.element = element
        self.key = key
        self.application = application
        self.scrollDelta = scrollDelta
    }
}

public struct ApplicationInfo: Codable, Sendable {
    public let name: String
    public let bundleId: String
    public let processId: Int32
    
    public init(name: String, bundleId: String, processId: Int32) {
        self.name = name
        self.bundleId = bundleId
        self.processId = processId
    }
}

public struct ScrollDelta: Codable, Sendable {
    public let dx: Double
    public let dy: Double
    
    public init(dx: Double, dy: Double) {
        self.dx = dx
        self.dy = dy
    }
}

// MARK: - Event Handler Types

public typealias UsageEventHandler = (UsageEvent) -> Void
public typealias MouseClickHandler = (CGPoint, ElementInfo) -> Void
public typealias KeyPressHandler = (String, ElementInfo) -> Void
public typealias AppFocusHandler = (ApplicationInfo) -> Void
public typealias ScrollHandler = (CGPoint, ScrollDelta, ElementInfo) -> Void

// MARK: - Usage Monitor Class

public class UsageMonitor {
    nonisolated(unsafe) public static let shared = UsageMonitor()
    
    private var eventTap: CFMachPort?
    private var eventAggregator = EventAggregator()
    private var eventHandlers: [String: [UsageEventHandler]] = [:]
    private var workspaceObservers: [NSObjectProtocol] = []
    private var isMonitoring = false
    
    private init() {}
    
    // MARK: - Public API
    
    /// Starts monitoring user events. Requires accessibility permissions.
    /// - Returns: True if monitoring started successfully, false otherwise
    public func startMonitoring() -> Bool {
        guard !isMonitoring else { return true }
        guard checkAccessibilityPermissions() else { return false }
        
        setupEventTap()
        setupApplicationNotifications()
        isMonitoring = true
        
        return eventTap != nil
    }
    
    /// Stops monitoring user events
    public func stopMonitoring() {
        guard isMonitoring else { return }
        
        if let eventTap = eventTap {
            CGEvent.tapEnable(tap: eventTap, enable: false)
            self.eventTap = nil
        }
        
        removeApplicationNotifications()
        isMonitoring = false
    }
    
    /// Registers a general event handler for any event type
    /// - Parameters:
    ///   - eventType: The type of event to listen for (e.g., "leftMouseDown", "keyDown", "appFocused")
    ///   - handler: The handler to call when the event occurs
    public func onEvent(_ eventType: String, handler: @escaping UsageEventHandler) {
        if eventHandlers[eventType] == nil {
            eventHandlers[eventType] = []
        }
        eventHandlers[eventType]?.append(handler)
    }
    
    /// Registers a handler for mouse click events
    /// - Parameter handler: Called with click position and element information
    public func onMouseClick(handler: @escaping MouseClickHandler) {
        onEvent("leftMouseDown") { event in
            if let position = event.position,
               let element = event.element {
                handler(position, element)
            }
        }
    }
    
    /// Registers a handler for key press events
    /// - Parameter handler: Called with the pressed key and focused element information
    public func onKeyPress(handler: @escaping KeyPressHandler) {
        onEvent("keyDown") { event in
            if let key = event.key,
               let element = event.element {
                handler(key, element)
            }
        }
    }
    
    /// Registers a handler for application focus events
    /// - Parameter handler: Called when an application gains focus
    public func onAppFocus(handler: @escaping AppFocusHandler) {
        onEvent("appFocused") { event in
            if let app = event.application {
                handler(app)
            }
        }
    }
    
    /// Registers a handler for scroll events
    /// - Parameter handler: Called with scroll position, delta, and element information
    public func onScroll(handler: @escaping ScrollHandler) {
        onEvent("scrollWheel") { event in
            if let position = event.position,
               let delta = event.scrollDelta,
               let element = event.element {
                handler(position, delta, element)
            }
        }
    }
    
    /// Removes all event handlers for a specific event type
    /// - Parameter eventType: The event type to clear handlers for
    public func removeHandlers(for eventType: String) {
        eventHandlers[eventType] = nil
    }
    
    /// Removes all event handlers
    public func removeAllHandlers() {
        eventHandlers.removeAll()
    }
    
    /// Checks if the monitor is currently running
    public var isRunning: Bool {
        return isMonitoring
    }
}

// MARK: - Convenience Functions

/// Starts usage monitoring with a general event handler
/// - Parameter handler: Called for every monitored event
/// - Returns: True if monitoring started successfully
public func startUsageMonitoring(handler: @escaping UsageEventHandler) -> Bool {
    let monitor = UsageMonitor.shared
    monitor.onEvent("leftMouseDown", handler: handler)
    monitor.onEvent("keyDown", handler: handler)
    monitor.onEvent("scrollWheel", handler: handler)
    monitor.onEvent("appFocused", handler: handler)
    monitor.onEvent("appDefocused", handler: handler)
    monitor.onEvent("appLaunched", handler: handler)
    monitor.onEvent("appTerminated", handler: handler)
    return monitor.startMonitoring()
}

/// Starts monitoring just mouse clicks
/// - Parameter handler: Called for each mouse click with position and element info
/// - Returns: True if monitoring started successfully
public func monitorMouseClicks(handler: @escaping MouseClickHandler) -> Bool {
    let monitor = UsageMonitor.shared
    monitor.onMouseClick(handler: handler)
    return monitor.startMonitoring()
}

/// Starts monitoring just key presses
/// - Parameter handler: Called for each key press with key and element info
/// - Returns: True if monitoring started successfully
public func monitorKeyPresses(handler: @escaping KeyPressHandler) -> Bool {
    let monitor = UsageMonitor.shared
    monitor.onKeyPress(handler: handler)
    return monitor.startMonitoring()
}

/// Starts monitoring application focus changes
/// - Parameter handler: Called when applications gain focus
/// - Returns: True if monitoring started successfully
public func monitorAppFocus(handler: @escaping AppFocusHandler) -> Bool {
    let monitor = UsageMonitor.shared
    monitor.onAppFocus(handler: handler)
    return monitor.startMonitoring()
}

/// Stops all usage monitoring
public func stopUsageMonitoring() {
    UsageMonitor.shared.stopMonitoring()
}

// MARK: - Internal Implementation

// Reusing the EventAggregator from the original code
internal struct EventAggregator {
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

// MARK: - Private Implementation

private extension UsageMonitor {
    func checkAccessibilityPermissions() -> Bool {
        return AXIsProcessTrusted()
    }
    
    func setupEventTap() {
        let aggregatorPtr = UnsafeMutablePointer<EventAggregator>.allocate(capacity: 1)
        aggregatorPtr.initialize(to: eventAggregator)
        
        let mask = CGEventMask(1 << CGEventType.leftMouseDown.rawValue) |
                   CGEventMask(1 << CGEventType.scrollWheel.rawValue) |
                   CGEventMask(1 << CGEventType.keyDown.rawValue)
        
        eventTap = CGEvent.tapCreate(
            tap: .cgSessionEventTap,
            place: .headInsertEventTap,
            options: .defaultTap,
            eventsOfInterest: mask,
            callback: { proxy, type, event, refcon in
                return UsageMonitor.eventTapCallback(proxy: proxy, type: type, event: event, refcon: refcon)
            },
            userInfo: UnsafeMutableRawPointer(aggregatorPtr)
        )
        
        guard let eventTap = eventTap else { return }
        
        let runLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, eventTap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, .commonModes)
        CGEvent.tapEnable(tap: eventTap, enable: true)
    }
    
    static func eventTapCallback(proxy: CGEventTapProxy, type: CGEventType, event: CGEvent, refcon: UnsafeMutableRawPointer?) -> Unmanaged<CGEvent>? {
        guard let aggregatorPtr = refcon?.assumingMemoryBound(to: EventAggregator.self) else {
            return Unmanaged.passUnretained(event)
        }
        
        let loc = event.location
        let monitor = UsageMonitor.shared
        
        switch type {
        case .leftMouseDown:
            if aggregatorPtr.pointee.shouldLog("leftMouseDown", location: loc) {
                let element = describeElementConcisely(at: loc)
                let usageEvent = UsageEvent(
                    type: "leftMouseDown",
                    timestamp: ISO8601DateFormatter().string(from: Date()),
                    position: loc,
                    element: element
                )
                monitor.notifyHandlers(event: usageEvent)
            }
            
        case .keyDown:
            var chars = [UniChar](repeating: 0, count: 4)
            var length: Int = 0
            event.keyboardGetUnicodeString(maxStringLength: 4, actualStringLength: &length, unicodeString: &chars)
            let keyChar = String(utf16CodeUnits: chars, count: length)
            
            if aggregatorPtr.pointee.shouldLog("keyDown", key: keyChar) {
                let element = focusedElementDescription()
                let usageEvent = UsageEvent(
                    type: "keyDown",
                    timestamp: ISO8601DateFormatter().string(from: Date()),
                    element: element,
                    key: keyChar
                )
                monitor.notifyHandlers(event: usageEvent)
            }
            
        case .scrollWheel:
            if aggregatorPtr.pointee.shouldLog("scrollWheel", location: loc) {
                let dy = event.getDoubleValueField(.scrollWheelEventDeltaAxis1)
                let dx = event.getDoubleValueField(.scrollWheelEventDeltaAxis2)
                let element = describeElementConcisely(at: loc)
                let usageEvent = UsageEvent(
                    type: "scrollWheel",
                    timestamp: ISO8601DateFormatter().string(from: Date()),
                    position: loc,
                    element: element,
                    scrollDelta: ScrollDelta(dx: dx, dy: dy)
                )
                monitor.notifyHandlers(event: usageEvent)
            }
            
        default:
            break
        }
        
        return Unmanaged.passUnretained(event)
    }
    
    func setupApplicationNotifications() {
        let workspace = NSWorkspace.shared
        
        let focusObserver = workspace.notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification,
            object: nil,
            queue: nil
        ) { [weak self] note in
            self?.handleAppNotification(note: note, type: "appFocused")
        }
        
        let defocusObserver = workspace.notificationCenter.addObserver(
            forName: NSWorkspace.didDeactivateApplicationNotification,
            object: nil,
            queue: nil
        ) { [weak self] note in
            self?.handleAppNotification(note: note, type: "appDefocused")
        }
        
        let launchObserver = workspace.notificationCenter.addObserver(
            forName: NSWorkspace.didLaunchApplicationNotification,
            object: nil,
            queue: nil
        ) { [weak self] note in
            self?.handleAppNotification(note: note, type: "appLaunched")
        }
        
        let terminateObserver = workspace.notificationCenter.addObserver(
            forName: NSWorkspace.didTerminateApplicationNotification,
            object: nil,
            queue: nil
        ) { [weak self] note in
            self?.handleAppNotification(note: note, type: "appTerminated")
        }
        
        workspaceObservers = [focusObserver, defocusObserver, launchObserver, terminateObserver]
    }
    
    func removeApplicationNotifications() {
        let workspace = NSWorkspace.shared
        for observer in workspaceObservers {
            workspace.notificationCenter.removeObserver(observer)
        }
        workspaceObservers.removeAll()
    }
    
    func handleAppNotification(note: Notification, type: String) {
        guard let app = note.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication else { return }
        
        let appInfo = ApplicationInfo(
            name: app.localizedName ?? app.bundleIdentifier ?? "UnknownApp",
            bundleId: app.bundleIdentifier ?? "",
            processId: app.processIdentifier
        )
        
        let usageEvent = UsageEvent(
            type: type,
            timestamp: ISO8601DateFormatter().string(from: Date()),
            application: appInfo
        )
        
        notifyHandlers(event: usageEvent)
    }
    
    func notifyHandlers(event: UsageEvent) {
        if let handlers = eventHandlers[event.type] {
            for handler in handlers {
                handler(event)
            }
        }
    }
}

// MARK: - Utility Functions (Reused from original code)

private func describeElementConcisely(_ element: AXUIElement?) -> ElementInfo {
    guard let el = element else { return ElementInfo(error: "unknown") }
    
    func getStringAttribute(_ attr: String) -> String? {
        var ref: CFTypeRef?
        AXUIElementCopyAttributeValue(el, attr as CFString, &ref)
        return ref as? String
    }
    
    let role = getStringAttribute(kAXRoleAttribute)
    let title = getStringAttribute(kAXTitleAttribute)
    let rawValue = getStringAttribute(kAXValueAttribute)
    let value = rawValue?.isEmpty == false ? (rawValue!.count > 50 ? String(rawValue!.prefix(50)) + "..." : rawValue!) : nil
    let placeholder = getStringAttribute(kAXPlaceholderValueAttribute)
    
    var parentRole: String?
    var parentRef: CFTypeRef?
    AXUIElementCopyAttributeValue(el, kAXParentAttribute as CFString, &parentRef)
    if let parent = parentRef, CFGetTypeID(parent) == AXUIElementGetTypeID() {
        let parentElement = parent as! AXUIElement
        var parentRoleRef: CFTypeRef?
        AXUIElementCopyAttributeValue(parentElement, kAXRoleAttribute as CFString, &parentRoleRef)
        parentRole = parentRoleRef as? String
    }
    
    return ElementInfo(role: role, title: title, value: value, placeholder: placeholder, parentRole: parentRole)
}

private func describeElementConcisely(at pos: CGPoint) -> ElementInfo {
    let system = AXUIElementCreateSystemWide()
    var el: AXUIElement?
    let err = AXUIElementCopyElementAtPosition(system, Float(pos.x), Float(pos.y), &el)
    if err != .success || el == nil {
        return ElementInfo(error: "unknown element")
    }
    return describeElementConcisely(el)
}

private func focusedElementDescription() -> ElementInfo {
    let system = AXUIElementCreateSystemWide()
    var cfEl: CFTypeRef?
    let err = AXUIElementCopyAttributeValue(system, kAXFocusedUIElementAttribute as CFString, &cfEl)
    if err != .success {
        return ElementInfo(error: "unknown element")
    }
    let el = cfEl as! AXUIElement
    return describeElementConcisely(el)
}
