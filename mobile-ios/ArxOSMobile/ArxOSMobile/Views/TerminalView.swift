import SwiftUI

struct TerminalView: View {
    @State private var commandText = ""
    @State private var outputLines: [String] = ["ArxOS Mobile Terminal - Git for Buildings", "Type 'help' for available commands"]
    @State private var isExecuting = false
    @ObservedObject private var terminalService = TerminalService()
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Terminal Output Area
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 2) {
                            ForEach(Array(outputLines.enumerated()), id: \.offset) { index, line in
                                Text(line)
                                    .font(.system(.body, design: .monospaced))
                                    .foregroundColor(.primary)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .id(index)
                            }
                        }
                        .padding()
                    }
                    .background(Color.black)
                    .onChange(of: outputLines.count) { _ in
                        withAnimation {
                            proxy.scrollTo(outputLines.count - 1, anchor: .bottom)
                        }
                    }
                }
                
                Divider()
                
                // Command Input Area
                HStack {
                    Text("arx$")
                        .font(.system(.body, design: .monospaced))
                        .foregroundColor(.green)
                    
                    TextField("Enter command...", text: $commandText)
                        .font(.system(.body, design: .monospaced))
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .onSubmit {
                            executeCommand()
                        }
                        .disabled(isExecuting)
                    
                    Button(action: executeCommand) {
                        Image(systemName: "play.fill")
                            .foregroundColor(.blue)
                    }
                    .disabled(commandText.isEmpty || isExecuting)
                }
                .padding()
                .background(Color(.systemGray6))
            }
            .navigationTitle("ArxOS Terminal")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
    
    private func executeCommand() {
        guard !commandText.isEmpty else { return }
        
        let command = commandText.trimmingCharacters(in: .whitespacesAndNewlines)
        commandText = ""
        
        // Add command to output
        outputLines.append("arx$ \(command)")
        
        isExecuting = true
        
        // Execute command through terminal service
        terminalService.executeCommand(command) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let output):
                    if !output.isEmpty {
                        outputLines.append(output)
                    }
                case .failure(let error):
                    outputLines.append("Error: \(error.localizedDescription)")
                }
                
                isExecuting = false
            }
        }
    }
}

#Preview {
    TerminalView()
}
