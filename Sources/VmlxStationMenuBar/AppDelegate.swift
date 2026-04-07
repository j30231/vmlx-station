import AppKit
import Foundation

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var controller: StatusMenuController?

    func applicationDidFinishLaunching(_ notification: Notification) {
        let apiURL = ProcessInfo.processInfo.environment["VMLX_STATION_API"] ?? "http://127.0.0.1:18100"
        controller = StatusMenuController(client: APIClient(baseURL: URL(string: apiURL)!))
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        false
    }
}

