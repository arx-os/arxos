import SwiftUI
import ARKit
import RealityKit

struct ARScanView: View {
    @State private var isScanning = false
    @State private var detectedEquipment: [DetectedEquipment] = []
    @State private var showEquipmentList = false
    @State private var currentRoom = "Room 301"
    
    var body: some View {
        NavigationView {
            ZStack {
                if isScanning {
                    ARViewContainer(
                        detectedEquipment: $detectedEquipment,
                        isScanning: $isScanning
                    )
                    .ignoresSafeArea()
                    
                    // AR Overlay UI
                    VStack {
                        HStack {
                            Text("Scanning: \(currentRoom)")
                                .padding()
                                .background(Color.black.opacity(0.7))
                                .foregroundColor(.white)
                                .cornerRadius(8)
                            
                            Spacer()
                            
                            Button(action: stopScanning) {
                                Image(systemName: "stop.circle.fill")
                                    .font(.title)
                                    .foregroundColor(.red)
                            }
                        }
                        .padding()
                        
                        Spacer()
                        
                        // Equipment Detection Indicators
                        if !detectedEquipment.isEmpty {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 12) {
                                    ForEach(detectedEquipment) { equipment in
                                        EquipmentTagView(equipment: equipment)
                                    }
                                }
                                .padding()
                            }
                        }
                        
                        // Control Panel
                        HStack(spacing: 20) {
                            Button(action: addEquipmentManually) {
                                VStack {
                                    Image(systemName: "plus.circle.fill")
                                        .font(.title2)
                                    Text("Add")
                                        .font(.caption)
                                }
                                .foregroundColor(.blue)
                            }
                            
                            Button(action: { showEquipmentList = true }) {
                                VStack {
                                    Image(systemName: "list.bullet")
                                        .font(.title2)
                                    Text("List")
                                        .font(.caption)
                                }
                                .foregroundColor(.green)
                            }
                            
                            Button(action: saveScan) {
                                VStack {
                                    Image(systemName: "checkmark.circle.fill")
                                        .font(.title2)
                                    Text("Save")
                                        .font(.caption)
                                }
                                .foregroundColor(.green)
                            }
                        }
                        .padding()
                        .background(Color.black.opacity(0.7))
                        .cornerRadius(12)
                        .padding()
                    }
                } else {
                    // Start Screen
                    VStack(spacing: 30) {
                        Image(systemName: "camera.viewfinder")
                            .font(.system(size: 80))
                            .foregroundColor(.blue)
                        
                        Text("AR Equipment Scanner")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Text("Scan rooms and tag equipment using AR")
                            .font(.body)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                        
                        VStack(spacing: 16) {
                            TextField("Room Name", text: $currentRoom)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .padding(.horizontal)
                            
                            Button(action: startScanning) {
                                HStack {
                                    Image(systemName: "play.fill")
                                    Text("Start AR Scan")
                                }
                                .font(.headline)
                                .foregroundColor(.white)
                                .padding()
                                .background(Color.blue)
                                .cornerRadius(12)
                            }
                        }
                        
                        if !detectedEquipment.isEmpty {
                            VStack {
                                Text("Last Scan Results")
                                    .font(.headline)
                                
                                ForEach(detectedEquipment.prefix(3)) { equipment in
                                    HStack {
                                        Image(systemName: equipment.icon)
                                        Text(equipment.name)
                                        Spacer()
                                        Text(equipment.status)
                                            .foregroundColor(.secondary)
                                    }
                                    .padding(.horizontal)
                                }
                            }
                            .padding()
                            .background(Color(.systemGray6))
                            .cornerRadius(12)
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("AR Scanner")
            .navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented: $showEquipmentList) {
                EquipmentListView()
            }
        }
    }
    
    private func startScanning() {
        isScanning = true
        detectedEquipment = []
    }
    
    private func stopScanning() {
        isScanning = false
    }
    
    private func addEquipmentManually() {
        // Add manual equipment entry
        let newEquipment = DetectedEquipment(
            name: "Manual Equipment",
            type: "Manual",
            position: Position3D(x: 0, y: 0, z: 0),
            status: "Detected",
            icon: "wrench"
        )
        detectedEquipment.append(newEquipment)
    }
    
    private func saveScan() {
        // Save scan results to ArxOS
        // This would integrate with the Rust core
        isScanning = false
    }
}

struct EquipmentTagView: View {
    let equipment: DetectedEquipment
    
    var body: some View {
        HStack {
            Image(systemName: equipment.icon)
            Text(equipment.name)
                .font(.caption)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.blue.opacity(0.8))
        .foregroundColor(.white)
        .cornerRadius(16)
    }
}

#Preview {
    ARScanView()
}
