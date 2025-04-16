// The Swift Programming Language
// https://docs.swift.org/swift-book

import AppKit // For NSWorkspace, NSRunningApplication, NSApplication
import Foundation // For basic types, JSONEncoder, Date
import ApplicationServices // For Accessibility API (AXUIElement, etc.)
import WebKit // For WKWebView interactions

// --- Error Enum ---
public enum MacosUseSDKError: Error, LocalizedError {
    case accessibilityDenied
    case appNotFound(pid: Int32)
    case jsonEncodingFailed(Error)
    case internalError(String) // For unexpected issues
    case browserScriptError(String) // For browser script injection errors

    public var errorDescription: String? {
        switch self {
        case .accessibilityDenied:
            return "Accessibility access is denied. Please grant permissions in System Settings > Privacy & Security > Accessibility."
        case .appNotFound(let pid):
            return "No running application found with PID \(pid)."
        case .jsonEncodingFailed(let underlyingError):
            return "Failed to encode response to JSON: \(underlyingError.localizedDescription)"
        case .internalError(let message):
            return "Internal SDK error: \(message)"
        case .browserScriptError(let message):
            return "Browser script injection error: \(message)"
        }
    }
}


// --- Public Data Structures for API Response ---

public struct ElementData: Codable, Hashable, Sendable {
    public var role: String
    public var text: String?
    public var x: Double?
    public var y: Double?
    public var width: Double?
    public var height: Double?

    // Implement Hashable for use in Set
    public func hash(into hasher: inout Hasher) {
        hasher.combine(role)
        hasher.combine(text)
        hasher.combine(x)
        hasher.combine(y)
        hasher.combine(width)
        hasher.combine(height)
    }
    public static func == (lhs: ElementData, rhs: ElementData) -> Bool {
        lhs.role == rhs.role &&
        lhs.text == rhs.text &&
        lhs.x == rhs.x &&
        lhs.y == rhs.y &&
        lhs.width == rhs.width &&
        lhs.height == rhs.height
    }
}

// New structure for browser HTML content
public struct BrowserPageData: Codable, Sendable {
    public var url: String
    public var title: String
    public var html: String
    public var extractedText: String
    public var elements: [BrowserElementData]
}

public struct BrowserElementData: Codable, Hashable, Sendable {
    public var tagName: String
    public var id: String?
    public var className: String?
    public var text: String?
    public var href: String?
    public var src: String?
    public var x: Double?
    public var y: Double?
    public var width: Double?
    public var height: Double?
    
    // Implement Hashable for use in Set
    public func hash(into hasher: inout Hasher) {
        hasher.combine(tagName)
        hasher.combine(id)
        hasher.combine(className)
        hasher.combine(text)
        hasher.combine(href)
        hasher.combine(src)
        hasher.combine(x)
        hasher.combine(y)
        hasher.combine(width)
        hasher.combine(height)
    }
    
    public static func == (lhs: BrowserElementData, rhs: BrowserElementData) -> Bool {
        lhs.tagName == rhs.tagName &&
        lhs.id == rhs.id &&
        lhs.className == rhs.className &&
        lhs.text == rhs.text &&
        lhs.href == rhs.href &&
        lhs.src == rhs.src &&
        lhs.x == rhs.x &&
        lhs.y == rhs.y &&
        lhs.width == rhs.width &&
        lhs.height == rhs.height
    }
}

public struct Statistics: Codable, Sendable {
    public var count: Int = 0
    public var excluded_count: Int = 0
    public var excluded_non_interactable: Int = 0
    public var excluded_no_text: Int = 0
    public var with_text_count: Int = 0
    public var without_text_count: Int = 0
    public var visible_elements_count: Int = 0
    public var role_counts: [String: Int] = [:]
    public var browser_elements_count: Int = 0 // New stat for browser elements
}

public struct ResponseData: Codable, Sendable {
    public let app_name: String
    public var elements: [ElementData]
    public var stats: Statistics
    public let processing_time_seconds: String
    public var is_browser: Bool = false
    public var browser_data: BrowserPageData?
}


// --- Main Public Function ---

/// Traverses the accessibility tree of an application specified by its PID.
/// For browser applications, also extracts HTML content.
///
/// - Parameter pid: The Process ID (PID) of the target application.
/// - Parameter onlyVisibleElements: If true, only collects elements with valid position and size. Defaults to false.
/// - Parameter scrapeBrowserContent: If true, attempts to extract HTML from browsers. Defaults to true.
/// - Returns: A `ResponseData` struct containing the collected elements, statistics, and timing information.
/// - Throws: `MacosUseSDKError` if accessibility is denied, the app is not found, or an internal error occurs.
public func traverseAccessibilityTree(pid: Int32, onlyVisibleElements: Bool = false, scrapeBrowserContent: Bool = true) throws -> ResponseData {
    let operation = AccessibilityTraversalOperation(pid: pid, onlyVisibleElements: onlyVisibleElements, scrapeBrowserContent: scrapeBrowserContent)
    return try operation.executeTraversal()
}


// --- Internal Implementation Detail ---

// Class to encapsulate the state and logic of a single traversal operation
fileprivate class AccessibilityTraversalOperation {
    let pid: Int32
    let onlyVisibleElements: Bool
    let scrapeBrowserContent: Bool
    var visitedElements: Set<AXUIElement> = []
    var collectedElements: Set<ElementData> = []
    var statistics: Statistics = Statistics()
    var stepStartTime: Date = Date()
    let maxDepth = 100
    
    // Known browser bundle identifiers
    let browserBundleIDs: Set<String> = [
        "com.apple.Safari",
        "com.google.Chrome",
        "org.mozilla.firefox",
        "com.brave.Browser",
        "com.microsoft.edgemac",
        "com.operasoftware.Opera"
    ]
    
    var isBrowser: Bool = false
    var browserData: BrowserPageData?

    // Define roles considered non-interactable by default
    let nonInteractableRoles: Set<String> = [
        "AXGroup", "AXStaticText", "AXUnknown", "AXSeparator",
        "AXHeading", "AXLayoutArea", "AXHelpTag", "AXGrowArea",
        "AXOutline", "AXScrollArea", "AXSplitGroup", "AXSplitter",
        "AXToolbar", "AXDisclosureTriangle",
    ]

    init(pid: Int32, onlyVisibleElements: Bool, scrapeBrowserContent: Bool) {
        self.pid = pid
        self.onlyVisibleElements = onlyVisibleElements
        self.scrapeBrowserContent = scrapeBrowserContent
    }

    // --- Main Execution Method ---
    func executeTraversal() throws -> ResponseData {
        let overallStartTime = Date()
        fputs("info: starting traversal for pid: \(pid) (Visible Only: \(onlyVisibleElements))\n", stderr)
        stepStartTime = Date() // Initialize step timer

        // 1. Accessibility Check
        fputs("info: checking accessibility permissions...\n", stderr)
        let checkOptions = ["AXTrustedCheckOptionPrompt": kCFBooleanTrue] as CFDictionary
        let isTrusted = AXIsProcessTrustedWithOptions(checkOptions)

        if !isTrusted {
            fputs("❌ error: accessibility access is denied.\n", stderr)
            fputs("       please grant permissions in system settings > privacy & security > accessibility.\n", stderr)
            throw MacosUseSDKError.accessibilityDenied
        }
        logStepCompletion("checking accessibility permissions (granted)")

        // 2. Find Application by PID and Create AXUIElement
        guard let runningApp = NSRunningApplication(processIdentifier: pid) else {
            fputs("error: no running application found with pid \(pid).\n", stderr)
            throw MacosUseSDKError.appNotFound(pid: pid)
        }
        let targetAppName = runningApp.localizedName ?? "App (PID: \(pid))"
        let appElement = AXUIElementCreateApplication(pid)
        
        // Check if this is a browser
        if let bundleID = runningApp.bundleIdentifier, browserBundleIDs.contains(bundleID) {
            isBrowser = true
            fputs("info: detected browser application: \(bundleID)\n", stderr)
        }

        // 3. Activate App if needed
        var didActivate = false
        if runningApp.activationPolicy == NSApplication.ActivationPolicy.regular {
            if !runningApp.isActive {
                runningApp.activate()
                didActivate = true
            }
        }
        if didActivate {
            logStepCompletion("activating application '\(targetAppName)'")
        }

        // 4. For browsers, try to extract HTML content
        if isBrowser && scrapeBrowserContent {
            fputs("info: attempting to extract browser content...\n", stderr)
            try extractBrowserContent(app: runningApp, appElement: appElement)
            logStepCompletion("extracting browser content")
        }

        // 5. Start Accessibility Traversal
        walkElementTree(element: appElement, depth: 0)
        logStepCompletion("traversing accessibility tree (\(collectedElements.count) elements collected)")

        // 6. Process Results
        let sortedElements = collectedElements.sorted {
            let y0 = $0.y ?? Double.greatestFiniteMagnitude
            let y1 = $1.y ?? Double.greatestFiniteMagnitude
            if y0 != y1 { return y0 < y1 }
            let x0 = $0.x ?? Double.greatestFiniteMagnitude
            let x1 = $1.x ?? Double.greatestFiniteMagnitude
            return x0 < x1
        }

        // Set the final count statistic
        statistics.count = sortedElements.count

        // --- Calculate Total Time ---
        let overallEndTime = Date()
        let totalProcessingTime = overallEndTime.timeIntervalSince(overallStartTime)
        let formattedTime = String(format: "%.2f", totalProcessingTime)
        fputs("info: total execution time: \(formattedTime) seconds\n", stderr)

        // 7. Prepare Response
        let response = ResponseData(
            app_name: targetAppName,
            elements: sortedElements,
            stats: statistics,
            processing_time_seconds: formattedTime,
            is_browser: isBrowser,
            browser_data: browserData
        )

        return response
    }
    
    // --- Browser Content Extraction ---
    
    func extractBrowserContent(app: NSRunningApplication, appElement: AXUIElement) throws {
        // Get the browser's current URL and document
        var browserURL = "unknown"
        var browserTitle = "unknown"
        var html = ""
        var extractedText = ""
        var browserElements: [BrowserElementData] = []
        
        // First, try to get the URL and title using accessibility API
        if let urlValue = getURLFromBrowser(appElement: appElement) {
            browserURL = urlValue
        }
        
        if let titleValue = getTitleFromBrowser(appElement: appElement) {
            browserTitle = titleValue
        }
        
        // Use AppleScript to extract HTML content
        let script = """
        tell application "\(app.localizedName ?? "")"
            set currentURL to URL of active tab of front window
            set pageTitle to name of front window
            set pageContent to execute front window's active tab javascript "
                (function() {
                    // Extract full HTML
                    var htmlContent = document.documentElement.outerHTML;
                    
                    // Extract visible text
                    var textContent = Array.from(document.querySelectorAll('body, body *'))
                        .filter(el => {
                            var style = window.getComputedStyle(el);
                            return style.display !== 'none' && 
                                   style.visibility !== 'hidden' && 
                                   style.opacity !== '0' &&
                                   el.offsetWidth > 0 &&
                                   el.offsetHeight > 0;
                        })
                        .map(el => el.textContent)
                        .filter(text => text.trim().length > 0)
                        .join('\\n');
                    
                    // Extract important elements with positions
                    var elements = [];
                    var interactiveElements = document.querySelectorAll('a, button, input, select, textarea, [role=button], [role=link], [role=checkbox], [role=radio], [role=tab]');
                    
                    interactiveElements.forEach(function(el) {
                        if (el.offsetWidth > 0 && el.offsetHeight > 0) {
                            var rect = el.getBoundingClientRect();
                            elements.push({
                                tagName: el.tagName.toLowerCase(),
                                id: el.id || null,
                                className: el.className || null,
                                text: el.textContent.trim() || null,
                                href: el.href || null,
                                src: el.src || null,
                                x: rect.left,
                                y: rect.top,
                                width: rect.width,
                                height: rect.height
                            });
                        }
                    });
                    
                    return JSON.stringify({
                        html: htmlContent,
                        text: textContent,
                        elements: elements
                    });
                })();
            "
            return pageContent
        end tell
        """
        
        do {
            let appleScriptResult = try runAppleScript(script)
            if let data = appleScriptResult.data(using: .utf8) {
                if let json = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] {
                    html = json["html"] as? String ?? ""
                    extractedText = json["text"] as? String ?? ""
                    
                    // Process browser elements
                    if let elements = json["elements"] as? [[String: Any]] {
                        for element in elements {
                            let browserElement = BrowserElementData(
                                tagName: element["tagName"] as? String ?? "unknown",
                                id: element["id"] as? String,
                                className: element["className"] as? String,
                                text: element["text"] as? String,
                                href: element["href"] as? String,
                                src: element["src"] as? String,
                                x: element["x"] as? Double,
                                y: element["y"] as? Double,
                                width: element["width"] as? Double,
                                height: element["height"] as? Double
                            )
                            browserElements.append(browserElement)
                        }
                        statistics.browser_elements_count = browserElements.count
                    }
                }
            }
        } catch {
            fputs("warning: failed to extract HTML using AppleScript: \(error.localizedDescription)\n", stderr)
        }
        
        // Create browser data
        browserData = BrowserPageData(
            url: browserURL,
            title: browserTitle,
            html: html,
            extractedText: extractedText,
            elements: browserElements
        )
    }
    
    func getURLFromBrowser(appElement: AXUIElement) -> String? {
        // Try to get URL from various accessibility attributes that browsers might use
        guard let windowsValue = copyAttributeValue(element: appElement, attribute: kAXWindowsAttribute as String),
              let windowsArray = windowsValue as? [AXUIElement],
              let mainWindow = windowsArray.first else {
            return nil
        }
        
        // Different browsers store URL in different places, try several common patterns
        // 1. Check for AXDocument attribute
        if let docValue = copyAttributeValue(element: mainWindow, attribute: kAXDocumentAttribute as String) {
            if let url = getStringValue(docValue) {
                return url
            }
        }
        
        // 2. Try to find URL in the toolbar
        if let toolbarValue = findElementByRole(element: mainWindow, role: "AXToolbar") {
            if let textFieldValue = findElementByRole(element: toolbarValue, role: "AXTextField") {
                if let urlValue = copyAttributeValue(element: textFieldValue, attribute: kAXValueAttribute as String) {
                    if let url = getStringValue(urlValue) {
                        return url
                    }
                }
            }
        }
        
        return nil
    }
    
    func getTitleFromBrowser(appElement: AXUIElement) -> String? {
        // Try to get title from the main window
        guard let windowsValue = copyAttributeValue(element: appElement, attribute: kAXWindowsAttribute as String),
              let windowsArray = windowsValue as? [AXUIElement],
              let mainWindow = windowsArray.first else {
            return nil
        }
        
        // Get title from window title
        if let titleValue = copyAttributeValue(element: mainWindow, attribute: kAXTitleAttribute as String) {
            return getStringValue(titleValue)
        }
        
        return nil
    }
    
    func findElementByRole(element: AXUIElement, role: String) -> AXUIElement? {
        // Check if this element has the requested role
        if let roleValue = copyAttributeValue(element: element, attribute: kAXRoleAttribute as String),
           let elementRole = getStringValue(roleValue),
           elementRole == role {
            return element
        }
        
        // Check children
        if let childrenValue = copyAttributeValue(element: element, attribute: kAXChildrenAttribute as String),
           let childrenArray = childrenValue as? [AXUIElement] {
            for child in childrenArray {
                if let foundElement = findElementByRole(element: child, role: role) {
                    return foundElement
                }
            }
        }
        
        return nil
    }
    
    func runAppleScript(_ script: String) throws -> String {
        let appleScript = NSAppleScript(source: script)
        var error: NSDictionary?
        guard let result = appleScript?.executeAndReturnError(&error) else {
            if let error = error {
                throw MacosUseSDKError.browserScriptError(error.description)
            }
            throw MacosUseSDKError.browserScriptError("Unknown AppleScript error")
        }
        return result.stringValue ?? ""
    }

    // --- Helper Functions (now methods of the class) ---

    // Safely copy an attribute value
    func copyAttributeValue(element: AXUIElement, attribute: String) -> CFTypeRef? {
        var value: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(element, attribute as CFString, &value)
        if result == .success {
            return value
        } else if result != .attributeUnsupported && result != .noValue {
            // fputs("warning: could not get attribute '\(attribute)' for element: error \(result.rawValue)\n", stderr)
        }
        return nil
    }

    // Extract string value
    func getStringValue(_ value: CFTypeRef?) -> String? {
        guard let value = value else { return nil }
        let typeID = CFGetTypeID(value)
        if typeID == CFStringGetTypeID() {
            let cfString = value as! CFString
            return cfString as String
        } else if typeID == AXValueGetTypeID() {
            // AXValue conversion is complex, return nil for generic string conversion
            return nil
        }
        return nil
    }

    // Extract CGPoint
    func getCGPointValue(_ value: CFTypeRef?) -> CGPoint? {
        guard let value = value, CFGetTypeID(value) == AXValueGetTypeID() else { return nil }
        let axValue = value as! AXValue
        var pointValue = CGPoint.zero
        if AXValueGetValue(axValue, .cgPoint, &pointValue) {
            return pointValue
        }
        return nil
    }

    // Extract CGSize
    func getCGSizeValue(_ value: CFTypeRef?) -> CGSize? {
        guard let value = value, CFGetTypeID(value) == AXValueGetTypeID() else { return nil }
        let axValue = value as! AXValue
        var sizeValue = CGSize.zero
        if AXValueGetValue(axValue, .cgSize, &sizeValue) {
            return sizeValue
        }
        return nil
    }

    // Extract attributes, text, and geometry
    func extractElementAttributes(element: AXUIElement) -> (role: String, roleDesc: String?, text: String?, allTextParts: [String], position: CGPoint?, size: CGSize?) {
        var role = "AXUnknown"
        var roleDesc: String? = nil
        var textParts: [String] = []
        var position: CGPoint? = nil
        var size: CGSize? = nil

        if let roleValue = copyAttributeValue(element: element, attribute: kAXRoleAttribute as String) {
            role = getStringValue(roleValue) ?? "AXUnknown"
        }
        if let roleDescValue = copyAttributeValue(element: element, attribute: kAXRoleDescriptionAttribute as String) {
            roleDesc = getStringValue(roleDescValue)
        }

        let textAttributes = [
            kAXValueAttribute as String, kAXTitleAttribute as String, kAXDescriptionAttribute as String,
            "AXLabel", "AXHelp",
        ]
        for attr in textAttributes {
            if let attrValue = copyAttributeValue(element: element, attribute: attr),
               let text = getStringValue(attrValue),
               !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                textParts.append(text)
            }
        }
        let combinedText = textParts.isEmpty ? nil : textParts.joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)

        if let posValue = copyAttributeValue(element: element, attribute: kAXPositionAttribute as String) {
            position = getCGPointValue(posValue)
        }

        if let sizeValue = copyAttributeValue(element: element, attribute: kAXSizeAttribute as String) {
            size = getCGSizeValue(sizeValue)
        }

        return (role, roleDesc, combinedText, textParts, position, size)
    }

    // Recursive traversal function (now a method)
    func walkElementTree(element: AXUIElement, depth: Int) {
        // 1. Check for cycles and depth limit
        if visitedElements.contains(element) || depth > maxDepth {
            return
        }
        visitedElements.insert(element)

        // 2. Process the current element
        let (role, roleDesc, combinedText, _, position, size) = extractElementAttributes(element: element)
        let hasText = combinedText != nil && !combinedText!.isEmpty
        let isNonInteractable = nonInteractableRoles.contains(role)
        let roleWithoutAX = role.starts(with: "AX") ? String(role.dropFirst(2)) : role

        statistics.role_counts[role, default: 0] += 1

        // 3. Determine Geometry and Visibility
        var finalX: Double? = nil
        var finalY: Double? = nil
        var finalWidth: Double? = nil
        var finalHeight: Double? = nil
        if let p = position, let s = size, s.width > 0 || s.height > 0 {
            finalX = Double(p.x)
            finalY = Double(p.y)
            finalWidth = s.width > 0 ? Double(s.width) : nil
            finalHeight = s.height > 0 ? Double(s.height) : nil
        }
        let isGeometricallyVisible = finalX != nil && finalY != nil && finalWidth != nil && finalHeight != nil

        // Always update the visible_elements_count stat based on geometry, regardless of collection
        if isGeometricallyVisible {
            statistics.visible_elements_count += 1
        }

        // 4. Apply Filtering Logic
        var displayRole = role
        if let desc = roleDesc, !desc.isEmpty, !desc.elementsEqual(roleWithoutAX) {
            displayRole = "\(role) (\(desc))"
        }

        // Determine if the element passes the original filter criteria
        let passesOriginalFilter = !isNonInteractable || hasText

        // Determine if the element should be collected based on the new flag
        let shouldCollectElement = passesOriginalFilter && (!onlyVisibleElements || isGeometricallyVisible)

        if shouldCollectElement {
            let elementData = ElementData(
                role: displayRole, text: combinedText,
                x: finalX, y: finalY, width: finalWidth, height: finalHeight
            )

            if collectedElements.insert(elementData).inserted {
                // Update text counts only for collected elements
                if hasText { statistics.with_text_count += 1 }
                else { statistics.without_text_count += 1 }
            }
        } else {
            // Log exclusion (MODIFIED logic)
            var reasons: [String] = []
            if !passesOriginalFilter {
                 if isNonInteractable { reasons.append("non-interactable role '\(role)'") }
                 if !hasText { reasons.append("no text") }
            }
            // Add visibility reason only if it was the deciding factor
            if passesOriginalFilter && onlyVisibleElements && !isGeometricallyVisible {
                reasons.append("not visible")
            }

            // Update exclusion counts
            statistics.excluded_count += 1
            if isNonInteractable { statistics.excluded_non_interactable += 1 }
            if !hasText { statistics.excluded_no_text += 1 }
        }

        // 5. Recursively traverse children, windows, main window
        // a) Windows
        if let windowsValue = copyAttributeValue(element: element, attribute: kAXWindowsAttribute as String) {
            if let windowsArray = windowsValue as? [AXUIElement] {
                for windowElement in windowsArray where !visitedElements.contains(windowElement) {
                    walkElementTree(element: windowElement, depth: depth + 1)
                }
            }
        }

        // b) Main Window
        if let mainWindowValue = copyAttributeValue(element: element, attribute: kAXMainWindowAttribute as String) {
            if CFGetTypeID(mainWindowValue) == AXUIElementGetTypeID() {
                 let mainWindowElement = mainWindowValue as! AXUIElement
                 if !visitedElements.contains(mainWindowElement) {
                     walkElementTree(element: mainWindowElement, depth: depth + 1)
                 }
            }
        }

        // c) Regular Children
        if let childrenValue = copyAttributeValue(element: element, attribute: kAXChildrenAttribute as String) {
            if let childrenArray = childrenValue as? [AXUIElement] {
                for childElement in childrenArray where !visitedElements.contains(childElement) {
                    walkElementTree(element: childElement, depth: depth + 1)
                }
            }
        }
    }

    // Helper function logs duration of the step just completed
    func logStepCompletion(_ stepDescription: String) {
        let endTime = Date()
        let duration = endTime.timeIntervalSince(stepStartTime)
        let durationStr = String(format: "%.3f", duration)
        fputs("info: [\(durationStr)s] finished '\(stepDescription)'\n", stderr)
        stepStartTime = endTime // Reset start time for the next step
    }
} // End of AccessibilityTraversalOperation class
