//
//  ARTerminalViewModel.swift
//  ArxOSMobile
//
//  View Model for AR + Terminal hybrid view state management
//

import Foundation
import Combine

@MainActor
class ARTerminalViewModel: ObservableObject {
    @Published var outputLines: [String] = [
        "ArxOS AR Terminal - Git for Buildings",
        "Type 'help' for available commands",
        "AR scanning is active in background..."
    ]
    @Published var detectedEquipment: [DetectedEquipment] = []
    @Published var isScanning: Bool = false
    @Published var isExecuting: Bool = false
    
    private let terminalService = TerminalService()
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        setupInitialOutput()
    }
    
    func executeCommand(_ command: String) {
        guard !command.isEmpty else { return }
        
        isExecuting = true
        outputLines.append("arx$ \(command)")
        
        terminalService.executeCommand(command) { [weak self] result in
            Task { @MainActor in
                guard let self = self else { return }
                
                switch result {
                case .success(let output):
                    let lines = output.split(separator: "\n").map(String.init)
                    self.outputLines.append(contentsOf: lines)
                case .failure(let error):
                    self.outputLines.append("❌ Error: \(error.localizedDescription)")
                }
                
                self.isExecuting = false
            }
        }
    }
    
    func addOutput(_ text: String) {
        outputLines.append(text)
        // Keep output size manageable
        if outputLines.count > 100 {
            outputLines.removeFirst(20)
        }
    }
    
    private func setupInitialOutput() {
        // Add helpful commands
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.outputLines.append("")
            self.outputLines.append("Available commands:")
            self.outputLines.append("  help                 - Show this help message")
            self.outputLines.append("  list                 - List detected equipment")
            self.outputLines.append("  equipment            - Show equipment details")
            self.outputLines.append("  ar-pending           - Show pending AR detections")
            self.outputLines.append("  ar-confirm <id>      - Confirm AR detection")
            self.outputLines.append("")
        }
    }
}

