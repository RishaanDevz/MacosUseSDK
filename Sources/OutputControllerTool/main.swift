import Foundation
import MacosUseSDK

let startTime = Date()

func log(_ message: String) {
    fputs("OutputControllerTool: \(message)\n", stderr)
}

func finish(success: Bool, message: String? = nil) -> Never {
    if let msg = message {
        log(success ? "✅ Success: \(msg)" : "❌ Error: \(msg)")
    }
    let endTime = Date()
    let processingTime = endTime.timeIntervalSince(startTime)
    let formattedTime = String(format: "%.3f", processingTime)
    fputs("OutputControllerTool: total execution time: \(formattedTime) seconds\n", stderr)
    exit(success ? 0 : 1)
}

let arguments = CommandLine.arguments
let scriptName = arguments.first ?? "OutputControllerTool"

let usage = """
usage: \(scriptName) <action> [value]

actions:
  set-volume <value>      Set system output volume (0.0 - 1.0)
  get-volume              Get system output volume
  set-brightness <value>  Set main display brightness (0.0 - 1.0)
  get-brightness          Get main display brightness

Examples:
  \(scriptName) set-volume 0.5
  \(scriptName) get-volume
  \(scriptName) set-brightness 0.8
  \(scriptName) get-brightness
"""

guard arguments.count > 1 else {
    fputs(usage, stderr)
    finish(success: false, message: "No action specified.")
}

let action = arguments[1].lowercased()
log("Action: \(action)")

do {
    switch action {
    case "set-volume":
        guard arguments.count == 3, let value = Float(arguments[2]), value >= 0.0, value <= 1.0 else {
            throw OutputControllerError.volumeAdjustmentFailed
        }
        try OutputController.setSystemVolume(value)
        finish(success: true, message: "System volume set to \(value)")
    case "get-volume":
        let value = try OutputController.getSystemVolume()
        print(value)
        finish(success: true, message: "System volume is \(value)")
    case "set-brightness":
        guard arguments.count == 3, let value = Float(arguments[2]), value >= 0.0, value <= 1.0 else {
            throw OutputControllerError.brightnessAdjustmentFailed
        }
        try OutputController.setMainDisplayBrightness(value)
        finish(success: true, message: "Main display brightness set to \(value)")
    case "get-brightness":
        let value = try OutputController.getMainDisplayBrightness()
        print(value)
        finish(success: true, message: "Main display brightness is \(value)")
    default:
        fputs(usage, stderr)
        finish(success: false, message: "Unknown action '\(action)'")
    }
} catch let error as OutputControllerError {
    finish(success: false, message: error.localizedDescription)
} catch {
    finish(success: false, message: "An unexpected error occurred: \(error.localizedDescription)")
}

exit(0) 