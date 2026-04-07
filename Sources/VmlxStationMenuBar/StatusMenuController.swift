import AppKit
import Foundation

@MainActor
final class StatusMenuController: NSObject {
    private let client: APIClient
    private let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    private let menu = NSMenu()
    private let headerItem = NSMenuItem(title: "vMLX Station", action: nil, keyEquivalent: "")
    private let stateItem = NSMenuItem(title: "Loading...", action: nil, keyEquivalent: "")
    private let scheduleItem = NSMenuItem(title: "Schedule: unknown", action: nil, keyEquivalent: "")
    private let loadMenuItem = NSMenuItem(title: "Load Model", action: nil, keyEquivalent: "")
    private let unloadItem = NSMenuItem(title: "Unload Current Model", action: #selector(unloadCurrentModel), keyEquivalent: "")
    private let refreshItem = NSMenuItem(title: "Refresh", action: #selector(refreshNow), keyEquivalent: "r")
    private let quitItem = NSMenuItem(title: "Quit vMLX Station", action: #selector(quitApp), keyEquivalent: "q")
    private var knownModels: [InstalledModel] = []
    private var refreshTimer: Timer?

    init(client: APIClient) {
        self.client = client
        super.init()
        setupMenu()
        startPolling()
        refresh()
    }

    private func setupMenu() {
        statusItem.button?.title = "vMLX"
        headerItem.isEnabled = false
        stateItem.isEnabled = false
        scheduleItem.isEnabled = false
        unloadItem.target = self
        refreshItem.target = self
        quitItem.target = self

        menu.addItem(headerItem)
        menu.addItem(.separator())
        menu.addItem(stateItem)
        menu.addItem(scheduleItem)
        menu.addItem(.separator())
        menu.addItem(loadMenuItem)
        menu.addItem(unloadItem)
        menu.addItem(.separator())
        menu.addItem(refreshItem)
        menu.addItem(quitItem)
        statusItem.menu = menu
        rebuildLoadSubmenu()
    }

    private func startPolling() {
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 10.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.refresh()
            }
        }
    }

    @objc private func refreshNow() {
        refresh()
    }

    @objc private func unloadCurrentModel() {
        let client = self.client
        Task {
            do {
                try await client.unload()
            } catch {
                self.applyError("Unload failed: \(error.localizedDescription)")
            }
            self.refreshFromTask()
        }
    }

    @objc private func loadModel(_ sender: NSMenuItem) {
        guard let modelID = sender.representedObject as? String else { return }
        let client = self.client
        Task {
            do {
                try await client.load(modelID: modelID)
            } catch {
                self.applyError("Load failed: \(error.localizedDescription)")
            }
            self.refreshFromTask()
        }
    }

    @objc private func quitApp() {
        NSApp.terminate(nil)
    }

    private func refresh() {
        let client = self.client
        Task {
            do {
                let status = try await client.fetchStatus()
                let models = try await client.fetchModels()
                self.applyRefresh(status: status, models: models.items)
            } catch {
                self.applyError("Daemon unreachable: \(error.localizedDescription)")
            }
        }
    }

    private func refreshFromTask() {
        refresh()
    }

    private func applyRefresh(status: StatusResponse, models: [InstalledModel]) {
        self.knownModels = models
        self.apply(status: status)
        self.rebuildLoadSubmenu()
    }

    private func applyError(_ message: String) {
        self.statusItem.button?.title = "vMLX?"
        self.stateItem.title = message
    }

    private func apply(status: StatusResponse) {
        let runningTitle = status.running ? (status.loadedModelName ?? "Running") : "Idle"
        statusItem.button?.title = status.running ? "vMLX: \(runningTitle)" : "vMLX"
        stateItem.title = status.message

        if let rule = status.activeScheduleRule {
            scheduleItem.title = status.scheduleEnabled
                ? "Schedule: \(rule.name) (\(rule.start)-\(rule.end))"
                : "Schedule: disabled"
        } else {
            scheduleItem.title = status.scheduleEnabled ? "Schedule: enabled" : "Schedule: disabled"
        }

        unloadItem.isEnabled = status.running
    }

    private func rebuildLoadSubmenu() {
        let submenu = NSMenu()
        if knownModels.isEmpty {
            let empty = NSMenuItem(title: "No models found", action: nil, keyEquivalent: "")
            empty.isEnabled = false
            submenu.addItem(empty)
        } else {
            for model in knownModels {
                let item = NSMenuItem(
                    title: "\(model.name) [\(model.engine)]",
                    action: #selector(loadModel(_:)),
                    keyEquivalent: ""
                )
                item.target = self
                item.representedObject = model.id
                submenu.addItem(item)
            }
        }
        loadMenuItem.submenu = submenu
    }
}
