import SwiftUI

@main
struct ArxOSMobileApp: App {
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false
    
    var body: some Scene {
        WindowGroup {
            if hasCompletedOnboarding || !UserProfile.needsOnboarding() {
                ContentView()
            } else {
                OnboardingView()
                    .onDisappear {
                        hasCompletedOnboarding = true
                    }
            }
        }
    }
}
