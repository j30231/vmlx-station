import Foundation

actor APIClient {
    private let baseURL: URL
    private let session: URLSession

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    func fetchStatus() async throws -> StatusResponse {
        try await get("api/status", as: StatusResponse.self)
    }

    func fetchModels() async throws -> InstalledModelsResponse {
        try await get("api/models", as: InstalledModelsResponse.self)
    }

    func load(modelID: String) async throws {
        try await post("api/load", body: ["model_id": modelID])
    }

    func unload() async throws {
        try await post("api/unload", body: [:])
    }

    func rescan() async throws -> Int {
        let response = try await post("api/rescan", body: [:], as: RescanResponse.self)
        return response.count
    }

    private func get<T: Decodable>(_ path: String, as type: T.Type) async throws -> T {
        let (data, response) = try await session.data(from: baseURL.appendingPathComponent(path))
        try validate(response: response, data: data)
        return try JSONDecoder.vmlxStation.decode(T.self, from: data)
    }

    private func post(_ path: String, body: [String: Any]) async throws {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, response) = try await session.data(for: request)
        try validate(response: response, data: data)
    }

    private func post<T: Decodable>(_ path: String, body: [String: Any], as type: T.Type) async throws -> T {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, response) = try await session.data(for: request)
        try validate(response: response, data: data)
        return try JSONDecoder.vmlxStation.decode(T.self, from: data)
    }

    private func validate(response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        guard (200..<300).contains(http.statusCode) else {
            let message = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw NSError(domain: "VmlxStation", code: http.statusCode, userInfo: [
                NSLocalizedDescriptionKey: message
            ])
        }
    }
}

private struct RescanResponse: Decodable {
    let status: String
    let count: Int
}

private extension JSONDecoder {
    static var vmlxStation: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }
}
