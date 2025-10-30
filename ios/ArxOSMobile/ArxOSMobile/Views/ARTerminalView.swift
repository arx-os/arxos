//
//  ARTerminalView.swift
//  ArxOSMobile
//
//  AR + Terminal hybrid view combining AR scanning with terminal interaction
//

import SwiftUI
import ARKit

struct ARTerminalView: View {
    // MARK: - State
    @StateObject private var viewModel = ARTerminalViewModel()
    @State private var terminalOpacity: Double = 0.75
    @State private var showTerminal: Bool = true
    @State private var commandText: String = ""
    
    // MARK: - Body
    var body: some View {
        ZStack {
            // Background: AR Camera View
            ARViewContainer(
                detectedEquipment: $viewModel.detectedEquipment,
                isScanning: $viewModel.isScanning
            )
            .ignoresSafeArea()
            
            // Foreground: Terminal Overlay (conditionally visible)
            if showTerminal {
                VStack(spacing: 0) {
                    // Terminal Output Area
                    TerminalOutputArea(
                        outputLines: $viewModel.outputLines,
                        opacity: terminalOpacity
                    )
                    
                    Spacer()
                    
                    // Command Input Area
                    TerminalInputArea(
                        commandText: $commandText,
                        onExecute: { command in
                            viewModel.executeCommand(command)
                            commandText = ""
                        },
                        opacity: min(terminalOpacity + 0.1, 0.95)
                    )
                }
                .transition(.opacity)
            }
            
            // Control Panel Overlay
            VStack {
                HStack {
                    Spacer()
                    ControlPanelView(
                        terminalOpacity: $terminalOpacity,
                        showTerminal: $showTerminal
                    )
                }
                Spacer()
            }
            .padding()
        }
        .onChange(of: viewModel.detectedEquipment) { equipment in
            handleNewEquipmentDetected(equipment)
        }
    }
    
    // MARK: - Helpers
    private func handleNewEquipmentDetected(_ equipment: [DetectedEquipment]) {
        if let latest = equipment.last {
            viewModel.addOutput("🔍 AR Detected: \(latest.name) (\(latest.equipmentType))")
        }
    }
}

// MARK: - Terminal Output Area
struct TerminalOutputArea: View {
    @Binding var outputLines: [String]
    let opacity: Double
    
    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 2) {
                    ForEach(Array(outputLines.enumerated()), id: \.offset) { index, line in
                        Text(line)
                            .font(.system(.body, design: .monospaced))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .id(index)
                    }
                }
                .padding(8)
            }
            .background(Color.black.opacity(opacity))
            .cornerRadius(12)
            .padding(.horizontal)
            .frame(maxHeight: 200)
            .onChange(of: outputLines.count) { _ in
                withAnimation {
                    proxy.scrollTo(outputLines.count - 1, anchor: .bottom)
                }
            }
        }
    }
}

// MARK: - Terminal Input Area
struct TerminalInputArea: View {
    @Binding var commandText: String
    let onExecute: (String) -> Void
    let opacity: Double
    
    var body: some View {
        HStack {
            Text("arx$")
                .font(.system(.body, design: .monospaced))
                .foregroundColor(.green)
            
            TextField("Enter command...", text: $commandText)
                .font(.system(.body, design: .monospaced))
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .onSubmit {
                    if !commandText.isEmpty {
                        onExecute(commandText)
                    }
                }
            
            Button(action: {
                if !commandText.isEmpty {
                    onExecute(commandText)
                }
            }) {
                Image(systemName: "play.fill")
                    .foregroundColor(.blue)
            }
            .disabled(commandText.isEmpty)
        }
        .padding(8)
        .background(Color.black.opacity(opacity))
        .cornerRadius(12)
        .padding()
    }
}

// MARK: - Control Panel
struct ControlPanelView: View {
    @Binding var terminalOpacity: Double
    @Binding var showTerminal: Bool
    
    var body: some View {
        VStack(spacing: 12) {
            // Toggle Terminal Visibility
            Button(action: {
                withAnimation {
                    showTerminal.toggle()
                }
            }) {
                Image(systemName: showTerminal ? "eye.slash" : "eye")
                    .foregroundColor(.white)
                    .padding(8)
                    .background(Color.black.opacity(0.6))
                    .clipShape(Circle())
            }
            
            if showTerminal {
                // Opacity Control
                VStack(spacing: 4) {
                    Text("Opacity")
                        .font(.caption)
                        .foregroundColor(.white)
                    
                    Slider(
                        value: $terminalOpacity,
                        in: 0.3...0.9,
                        step: 0.05
                    )
                    .frame(width: 100)
                    .accentColor(.blue)
                    
                    Text("\(Int(terminalOpacity * 100))%")
                        .font(.caption2)
                        .foregroundColor(.white)
                }
                .padding(8)
                .background(Color.black.opacity(0.6))
                .cornerRadius(8)
                .transition(.opacity)
            }
        }
    }
}

