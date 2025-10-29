//
//  OnboardingView.swift
//  ArxOSMobile
//
//  One-time onboarding view for user setup
//

import SwiftUI

struct OnboardingView: View {
    @State private var name: String = ""
    @State private var email: String = ""
    @State private var company: String = ""
    @State private var showingValidationError = false
    @Environment(\.dismiss) var dismiss
    
    var isFormValid: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty &&
        !email.trimmingCharacters(in: .whitespaces).isEmpty &&
        email.contains("@") && email.contains(".")
    }
    
    var body: some View {
        VStack(spacing: 24) {
            // Header
            VStack(spacing: 8) {
                Image(systemName: "building.2")
                    .font(.system(size: 60))
                    .foregroundColor(.blue)
                
                Text("Welcome to ArxOS")
                    .font(.title)
                    .bold()
                
                Text("Let's get you set up")
                    .foregroundColor(.secondary)
                    .font(.subheadline)
            }
            .padding(.top, 40)
            
            // Form
            VStack(spacing: 16) {
                TextField("Your Name", text: $name)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .autocapitalization(.words)
                
                TextField("Your Email", text: $email)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .keyboardType(.emailAddress)
                    .autocapitalization(.none)
                
                TextField("Company (Optional)", text: $company)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .autocapitalization(.words)
            }
            .padding(.horizontal)
            
            if showingValidationError {
                Text("Please enter a valid name and email")
                    .foregroundColor(.red)
                    .font(.caption)
            }
            
            // Continue Button
            Button(action: handleSignup) {
                Text("Continue")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(isFormValid ? Color.blue : Color.gray)
                    .cornerRadius(8)
            }
            .disabled(!isFormValid)
            .padding(.horizontal)
            
            Spacer()
        }
        .padding()
    }
    
    private func handleSignup() {
        guard isFormValid else {
            showingValidationError = true
            return
        }
        
        // Save profile
        let profile = UserProfile(
            name: name.trimmingCharacters(in: .whitespaces),
            email: email.trimmingCharacters(in: .whitespaces),
            company: company.isEmpty ? nil : company.trimmingCharacters(in: .whitespaces)
        )
        profile.save()
        
        // Configure Git via FFI
        configureGitCredentials(name: profile.name, email: profile.email)
        
        // Dismiss onboarding
        dismiss()
    }
    
    private func configureGitCredentials(name: String, email: String) {
        // Configure Git credentials via FFI
        let ffi = ArxOSCoreFFI()
        ffi.configureGitCredentials(name: name, email: email) { result in
            switch result {
            case .success:
                print("Git credentials configured successfully")
            case .failure(let error):
                print("Error configuring Git credentials: \(error.localizedDescription)")
            }
        }
    }
}

