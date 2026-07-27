import SwiftUI

/// iOS application entry point (include this file in an Xcode app target).
@main
struct ArxosAppMain: App {
    var body: some Scene {
        WindowGroup {
            CaptureHomeView()
        }
    }
}
