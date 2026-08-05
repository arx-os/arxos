import SwiftUI
#if canImport(ArxosCore)
import ArxosCore
#endif

/// iOS application entry point (Xcode target: ios/ArxosApp).
@main
struct ArxosAppMain: App {
    var body: some Scene {
        WindowGroup {
            CaptureHomeView()
        }
    }
}
