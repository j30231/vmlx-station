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

    private enum CodingKeys: String, CodingKey {
        case id
        case name
        case path
        case engine
        case source
        case hasJang = "has_jang"
        case hasVision = "has_vision"
    }
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

    private enum CodingKeys: String, CodingKey {
        case running
        case loadedModelID = "loaded_model_id"
        case loadedModelName = "loaded_model_name"
        case servedModelName = "served_model_name"
        case runtimePID = "runtime_pid"
        case runtimePort = "runtime_port"
        case openAIBaseURL = "openai_base_url"
        case controlBaseURL = "control_base_url"
        case scheduleEnabled = "schedule_enabled"
        case activeScheduleRule = "active_schedule_rule"
        case message
    }
}

struct ScheduleRule: Decodable {
    let name: String
    let start: String
    let end: String
    let modelID: String

    private enum CodingKeys: String, CodingKey {
        case name
        case start
        case end
        case modelID = "model_id"
    }
}
