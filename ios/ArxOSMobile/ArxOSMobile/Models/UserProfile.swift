//
//  UserProfile.swift
//  ArxOSMobile
//
//  User profile model for storing user credentials and preferences
//

import Foundation

/// User profile for storing local credentials and preferences
struct UserProfile: Codable {
    var name: String
    var email: String
    var company: String?
    
    init(name: String, email: String, company: String? = nil) {
        self.name = name
        self.email = email
        self.company = company
    }
    
    /// Load profile from UserDefaults
    static func load() -> UserProfile? {
        guard let data = UserDefaults.standard.data(forKey: "arxos_user_profile"),
              let profile = try? JSONDecoder().decode(UserProfile.self, from: data) else {
            return nil
        }
        return profile
    }
    
    /// Save profile to UserDefaults
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: "arxos_user_profile")
        }
    }
    
    /// Check if onboarding is needed
    static func needsOnboarding() -> Bool {
        return UserProfile.load() == nil
    }
    
    /// Clear stored profile (for logout/reset)
    static func clear() {
        UserDefaults.standard.removeObject(forKey: "arxos_user_profile")
    }
}

