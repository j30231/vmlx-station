// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "vmlx-station",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "VmlxStationMenuBar", targets: ["VmlxStationMenuBar"])
    ],
    targets: [
        .executableTarget(
            name: "VmlxStationMenuBar",
            path: "Sources/VmlxStationMenuBar"
        )
    ]
)

