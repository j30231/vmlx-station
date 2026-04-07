import Foundation

struct InstalledModelsResponse: Decodable {
    let items: [InstalledModel]
    let count: Int
}

struct InstalledModel: Decodable {
    let id: String
    let name: String
    let path: String
    let engine: String
    let source: String
    let hasJang: Bool
    let hasVision: Bool
}

struct StatusResponse: Decodable {
    let running: Bool
    let loadedModelID: String?
    let loadedModelName: String?
    let servedModelName: String?
    let runtimePID: Int?
    let runtimePort: Int
    let openAIBaseURL: String
    let controlBaseURL: String
    let scheduleEnabled: Bool
    let activeScheduleRule: ScheduleRule?
    let message: String
}

struct ScheduleRule: Decodable {
    let name: String
    let start: String
    let end: String
    let modelID: String
}

