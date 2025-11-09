import SwiftUI
import ARKit
import RealityKit
import UIKit

struct ARScanView: View {
    @StateObject private var core = ArxOSCore()
    @State private var isScanning = false
    @State private var detectedEquipment: [DetectedEquipment] = []
    @State private var showEquipmentList = false
    @State private var currentRoom = "Room 301"
    @State private var buildingName = "Default Building"
    @State private var floorLevel: Int32 = 0
    @State private var scanStartTime: Date?
    @State private var isSavingScan = false
    @State private var showSaveSuccess = false
    @State private var saveErrorMessage: String?
    @State private var pendingEquipmentIds: [String] = []
    @State private var showEquipmentDialog = false
    @State private var showPendingConfirmation = false
    @State private var pendingEquipment: DetectedEquipment?
    @State private var equipmentName = ""
    @State private var equipmentType = "Unknown"
    
    var body: some View {
        NavigationView {
            ZStack {
                if isScanning {
                    ARViewContainer(
                        detectedEquipment: $detectedEquipment,
                        isScanning: $isScanning,
                        onEquipmentPlaced: { equipment in
                            // Show equipment placement dialog
                            showEquipmentPlacementDialog(for: equipment)
                        }
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
                                    if isSavingScan {
                                        ProgressView()
                                            .progressViewStyle(CircularProgressViewStyle(tint: .green))
                                    } else {
                                        Image(systemName: "checkmark.circle.fill")
                                            .font(.title2)
                                    }
                                    Text("Save")
                                        .font(.caption)
                                }
                                .foregroundColor(.green)
                                .disabled(isSavingScan)
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
                            TextField("Building Name", text: $buildingName)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .padding(.horizontal)
                            
                            TextField("Room Name", text: $currentRoom)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .padding(.horizontal)
                            
                            HStack {
                                Text("Floor Level:")
                                Stepper(value: $floorLevel, in: -5...50) {
                                    Text("\(floorLevel)")
                                        .frame(width: 50, alignment: .trailing)
                                }
                            }
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
            .sheet(isPresented: $showPendingConfirmation) {
                PendingEquipmentConfirmationView(
                    pendingIds: pendingEquipmentIds,
                    buildingName: buildingName,
                    core: core
                )
            }
            .onAppear {
                core.setActiveBuilding(buildingName)
            }
            .onChange(of: buildingName) { newValue in
                core.setActiveBuilding(newValue)
            }
            .sheet(isPresented: $showEquipmentDialog) {
                EquipmentPlacementDialog(
                    equipmentName: $equipmentName,
                    equipmentType: $equipmentType,
                    onSave: {
                        savePlacedEquipment()
                    },
                    onCancel: {
                        showEquipmentDialog = false
                        pendingEquipment = nil
                    }
                )
            }
            .alert("Scan Saved", isPresented: $showSaveSuccess) {
                Button("OK") {
                    // Reset scan state
                    detectedEquipment = []
                    isScanning = false
                }
            } message: {
                if !pendingEquipmentIds.isEmpty {
                    Text("Successfully saved scan. \(pendingEquipmentIds.count) pending equipment items created.")
                } else {
                    Text("Scan saved successfully.")
                }
            }
            .alert("Save Error", isPresented: .constant(saveErrorMessage != nil)) {
                Button("OK") {
                    saveErrorMessage = nil
                }
            } message: {
                if let error = saveErrorMessage {
                    Text(error)
                }
            }
        }
    }
    
    private func startScanning() {
        isScanning = true
        detectedEquipment = []
        scanStartTime = Date() // Track scan start time for duration
    }
    
    private func stopScanning() {
        isScanning = false
    }
    
    private func addEquipmentManually() {
        // Add manual equipment entry at origin (0,0,0)
        let newEquipment = DetectedEquipment(
            name: "Manual Equipment",
            type: "Manual",
            position: Position3D(x: 0, y: 0, z: 0),
            confidence: 1.0,
            detectionMethod: "Manual",
            status: "Detected",
            icon: "wrench"
        )
        detectedEquipment.append(newEquipment)
    }
    
    private func showEquipmentPlacementDialog(for equipment: DetectedEquipment) {
        // Store pending equipment
        pendingEquipment = equipment
        equipmentName = equipment.name
        equipmentType = equipment.type
        
        // Show dialog
        showEquipmentDialog = true
    }
    
    private func savePlacedEquipment() {
        guard let equipment = pendingEquipment else { return }
        
        // Create new equipment with user-provided details
        let newEquipment = DetectedEquipment(
            name: equipmentName.isEmpty ? "Equipment \(detectedEquipment.count + 1)" : equipmentName,
            type: equipmentType,
            position: equipment.position,
            confidence: equipment.confidence ?? 0.9,
            detectionMethod: equipment.detectionMethod ?? "Tap-to-Place",
            status: "Placed",
            icon: iconForEquipmentType(equipmentType)
        )
        
        // Add to detected equipment list
        detectedEquipment.append(newEquipment)
        
        // Reset dialog state
        showEquipmentDialog = false
        pendingEquipment = nil
        equipmentName = ""
        equipmentType = "Unknown"
        
        print("✅ Equipment placed: \(newEquipment.name) at (\(newEquipment.position.x), \(newEquipment.position.y), \(newEquipment.position.z))")
    }
    
    private func iconForEquipmentType(_ type: String) -> String {
        switch type.lowercased() {
        case "hvac", "air conditioning", "heating":
            return "fan"
        case "electrical", "electrical panel":
            return "bolt"
        case "plumbing", "water", "piping":
            return "drop"
        case "safety", "fire", "sprinkler":
            return "shield"
        case "lighting", "light":
            return "lightbulb"
        default:
            return "gear"
        }
    }
    
    private func saveScan() {
        guard !isSavingScan else { return }
        
        isSavingScan = true
        saveErrorMessage = nil
        
        // Convert detected equipment to ARScanData format
        // Swift DetectedEquipment has custom encoding that matches Rust expectations
        // Rust backend expects: name, type, position, confidence (required), detectionMethod
        // The custom encode() method ensures confidence is always provided
        let scanData = ARScanData(
            detectedEquipment: detectedEquipment,
            roomBoundaries: RoomBoundaries(walls: [], openings: []),
            deviceType: UIDevice.current.model,
            appVersion: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String,
            scanDurationMs: scanStartTime.map { Int64(Date().timeIntervalSince($0) * 1000) },
            pointCount: nil, // Could be enhanced with ARKit point cloud data
            accuracyEstimate: nil, // Could be enhanced with ARKit tracking quality
            lightingConditions: nil, // Could be enhanced with ARKit light estimation
            roomName: currentRoom,
            floorLevel: floorLevel
        )
        
        // Call FFI to save and process scan
        core.setActiveBuilding(buildingName)
        core.saveARScan(
            scanData: scanData,
            buildingName: buildingName,
            confidenceThreshold: 0.7
        ) { result in
            DispatchQueue.main.async {
                self.isSavingScan = false
                
                switch result {
                case .success(let saveResult):
                    print("✅ Scan saved successfully: \(saveResult.message)")
                    print("   Pending items: \(saveResult.pendingCount)")
                    print("   Pending IDs: \(saveResult.pendingIds)")
                    
                    self.pendingEquipmentIds = saveResult.pendingIds
                    
                    // Show pending confirmation if there are pending items
                    if !saveResult.pendingIds.isEmpty {
                        self.showPendingConfirmation = true
                    } else {
                        self.showSaveSuccess = true
                    }
                    
                case .failure(let error):
                    print("❌ Failed to save AR scan: \(error.localizedDescription)")
                    self.saveErrorMessage = "Failed to save scan: \(error.localizedDescription)"
                }
            }
        }
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
