import AppKit
import Foundation
import OSLog

@MainActor
final class StatusMenuController: NSObject {
    private let client: APIClient
    private let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    private let menu = NSMenu()
    private let headerItem = NSMenuItem(title: "vMLX Station", action: nil, keyEquivalent: "")
    private let stateItem = NSMenuItem(title: "Loading...", action: nil, keyEquivalent: "")
    private let loadedItem = NSMenuItem(title: "Loaded: unknown", action: nil, keyEquivalent: "")
    private let servedItem = NSMenuItem(title: "Served as: unknown", action: nil, keyEquivalent: "")
    private let runtimeItem = NSMenuItem(title: "Runtime: unknown", action: nil, keyEquivalent: "")
    private let scheduleItem = NSMenuItem(title: "Schedule: unknown", action: nil, keyEquivalent: "")
    private let webUIItem = NSMenuItem(title: "Open WebUI: unknown", action: nil, keyEquivalent: "")
    private let modelsHeaderItem = NSMenuItem(title: "Models", action: nil, keyEquivalent: "")
    private let unloadItem = NSMenuItem(title: "Unload Current Model", action: #selector(unloadCurrentModel), keyEquivalent: "")
    private let rescanItem = NSMenuItem(title: "Rescan Models", action: #selector(rescanModels), keyEquivalent: "")
    private let openAPIItem = NSMenuItem(title: "Open Model API in Browser", action: #selector(openModelAPI), keyEquivalent: "")
    private let openControlItem = NSMenuItem(title: "Open Control API", action: #selector(openControlAPI), keyEquivalent: "")
    private let openWebUIItem = NSMenuItem(title: "Open WebUI", action: #selector(openWebUI), keyEquivalent: "")
    private let openConfigItem = NSMenuItem(title: "Open Config", action: #selector(openConfig), keyEquivalent: "")
    private let openLogsItem = NSMenuItem(title: "Open Logs", action: #selector(openLogs), keyEquivalent: "")
    private let refreshItem = NSMenuItem(title: "Refresh", action: #selector(refreshNow), keyEquivalent: "r")
    private let quitItem = NSMenuItem(title: "Quit vMLX Station", action: #selector(quitApp), keyEquivalent: "q")
    private var knownModels: [InstalledModel] = []
    private var currentStatus: StatusResponse?
    private var refreshTimer: Timer?
    private var modelItems: [NSMenuItem] = []
    private let logger = Logger(subsystem: "com.vmlxstation.menu-bar", category: "StatusMenu")

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
        loadedItem.isEnabled = false
        servedItem.isEnabled = false
        runtimeItem.isEnabled = false
        scheduleItem.isEnabled = false
        webUIItem.isEnabled = false
        modelsHeaderItem.isEnabled = false
        unloadItem.target = self
        rescanItem.target = self
        openAPIItem.target = self
        openControlItem.target = self
        openWebUIItem.target = self
        openConfigItem.target = self
        openLogsItem.target = self
        refreshItem.target = self
        quitItem.target = self

        menu.addItem(headerItem)
        menu.addItem(.separator())
        menu.addItem(stateItem)
        menu.addItem(loadedItem)
        menu.addItem(servedItem)
        menu.addItem(runtimeItem)
        menu.addItem(scheduleItem)
        menu.addItem(webUIItem)
        menu.addItem(.separator())
        menu.addItem(modelsHeaderItem)
        menu.addItem(unloadItem)
        menu.addItem(rescanItem)
        menu.addItem(.separator())
        menu.addItem(openAPIItem)
        menu.addItem(openControlItem)
        menu.addItem(openWebUIItem)
        menu.addItem(openConfigItem)
        menu.addItem(openLogsItem)
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

    @objc private func rescanModels() {
        let client = self.client
        Task {
            do {
                let count = try await client.rescan()
                self.stateItem.title = "Rescanned \(count) models"
            } catch {
                self.applyError("Rescan failed: \(error.localizedDescription)")
            }
            self.refreshFromTask()
        }
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

    @objc private func openModelAPI() {
        guard let urlString = currentStatus?.openAIBaseURL, let url = URL(string: urlString) else { return }
        NSWorkspace.shared.open(url)
    }

    @objc private func openControlAPI() {
        guard let urlString = currentStatus?.controlBaseURL,
              let baseURL = URL(string: urlString) else { return }
        let url = baseURL.appendingPathComponent("admin")
        NSWorkspace.shared.open(url)
    }

    @objc private func openWebUI() {
        guard let urlString = currentStatus?.openWebUIURL, let url = URL(string: urlString) else { return }
        NSWorkspace.shared.open(url)
    }

    @objc private func openConfig() {
        NSWorkspace.shared.open(Self.configURL)
    }

    @objc private func openLogs() {
        NSWorkspace.shared.open(Self.logsURL)
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
        self.currentStatus = status
        self.knownModels = models
        self.apply(status: status)
        self.rebuildLoadSubmenu()
        logger.notice("applyRefresh models=\(models.count) running=\(status.running)")
    }

    private func applyError(_ message: String) {
        self.statusItem.button?.title = "vMLX?"
        self.stateItem.title = message
        self.loadedItem.title = "Loaded: unavailable"
        self.servedItem.title = "Served as: unavailable"
        self.runtimeItem.title = "Runtime: unavailable"
        self.webUIItem.title = "Open WebUI: unavailable"
        self.modelsHeaderItem.title = "Models: unavailable"
        logger.error("menu error: \(message)")
    }

    private func apply(status: StatusResponse) {
        let runningTitle = status.running ? Self.compactName(status.loadedModelName ?? status.loadedModelID ?? "Running") : "Idle"
        statusItem.button?.title = status.running ? "vMLX • \(runningTitle)" : "vMLX"
        stateItem.title = status.message
        loadedItem.title = "Loaded: \(status.loadedModelName ?? status.loadedModelID ?? "None")"
        servedItem.title = "Served as: \(status.servedModelName ?? "unknown")"
        runtimeItem.title = "Runtime: \(status.runtimePID.map { "PID \($0)" } ?? "stopped") · Port \(status.runtimePort)"
        if let webUIURL = status.openWebUIURL {
            webUIItem.title = "Open WebUI: \(status.openWebUIRunning ? "running" : "configured")"
            openWebUIItem.title = status.openWebUIRunning ? "Open WebUI" : "Open WebUI (start if needed)"
            openWebUIItem.isEnabled = true
            webUIItem.toolTip = webUIURL
        } else {
            webUIItem.title = "Open WebUI: disabled"
            openWebUIItem.title = "Open WebUI"
            openWebUIItem.isEnabled = false
            webUIItem.toolTip = nil
        }
        modelsHeaderItem.title = "Models (\(knownModels.count))"

        if let rule = status.activeScheduleRule {
            scheduleItem.title = status.scheduleEnabled
                ? "Schedule: \(rule.name) (\(rule.start)-\(rule.end))"
                : "Schedule: disabled"
        } else {
            scheduleItem.title = status.scheduleEnabled ? "Schedule: enabled" : "Schedule: disabled"
        }

        unloadItem.isEnabled = status.running
        openAPIItem.isEnabled = URL(string: status.openAIBaseURL) != nil
        openControlItem.isEnabled = URL(string: status.controlBaseURL) != nil
        openWebUIItem.isEnabled = status.openWebUIURL.flatMap(URL.init(string:)) != nil
        openConfigItem.isEnabled = FileManager.default.fileExists(atPath: Self.configURL.path)
        openLogsItem.isEnabled = FileManager.default.fileExists(atPath: Self.logsURL.path)
    }

    private func rebuildLoadSubmenu() {
        for item in modelItems {
            menu.removeItem(item)
        }
        modelItems.removeAll()

        let insertionIndex = menu.index(of: unloadItem)
        guard insertionIndex != -1 else { return }

        if knownModels.isEmpty {
            let empty = NSMenuItem(title: "No models found", action: nil, keyEquivalent: "")
            empty.isEnabled = false
            modelItems = [empty]
        } else {
            modelItems = knownModels.map { model in
                let item = NSMenuItem(
                    title: "Load \(model.id) [\(model.engine)]",
                    action: #selector(loadModel(_:)),
                    keyEquivalent: ""
                )
                item.target = self
                item.representedObject = model.id
                return item
            }
        }

        for (offset, item) in modelItems.enumerated() {
            menu.insertItem(item, at: insertionIndex + offset)
        }

        let titles = modelItems.map(\.title).joined(separator: " | ")
        logger.notice("rebuilt model items count=\(self.modelItems.count) titles=\(titles, privacy: .public)")
    }

    private static var appSupportURL: URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/vmlx-station", isDirectory: true)
    }

    private static var configURL: URL {
        appSupportURL.appendingPathComponent("config.yaml", isDirectory: false)
    }

    private static var logsURL: URL {
        appSupportURL.appendingPathComponent("logs", isDirectory: true)
    }

    private static func compactName(_ name: String) -> String {
        let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.count > 24 else { return trimmed }
        return "\(trimmed.prefix(21))..."
    }
}
