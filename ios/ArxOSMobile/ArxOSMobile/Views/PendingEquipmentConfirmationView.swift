//
//  PendingEquipmentConfirmationView.swift
//  ArxOSMobile
//
//  View for reviewing and confirming/rejecting pending equipment from AR scans
//

import SwiftUI

struct PendingEquipmentConfirmationView: View {
    let pendingIds: [String]
    let buildingName: String
    @ObservedObject var core: ArxOSCore
    
    @State private var pendingEquipment: [PendingEquipmentItem] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showSuccessAlert = false
    @State private var successMessage = ""
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationView {
            ZStack {
                if isLoading {
                    ProgressView("Loading pending equipment...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if pendingEquipment.isEmpty {
                    EmptyPendingEquipmentView()
                } else {
                    List {
                        ForEach(pendingEquipment) { equipment in
                            PendingEquipmentRow(
                                equipment: equipment,
                                onConfirm: {
                                    confirmEquipment(equipment.id)
                                },
                                onReject: {
                                    rejectEquipment(equipment.id)
                                }
                            )
                        }
                    }
                    .listStyle(PlainListStyle())
                }
            }
            .navigationTitle("Pending Equipment")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
            .alert("Success", isPresented: $showSuccessAlert) {
                Button("OK") {
                    // Reload pending equipment after action
                    loadPendingEquipment()
                }
            } message: {
                Text(successMessage)
            }
            .alert("Error", isPresented: .constant(errorMessage != nil)) {
                Button("OK") {
                    errorMessage = nil
                }
            } message: {
                if let error = errorMessage {
                    Text(error)
                }
            }
            .onAppear {
                loadPendingEquipment()
            }
        }
    }
    
    private func loadPendingEquipment() {
        isLoading = true
        errorMessage = nil
        core.setActiveBuilding(buildingName)
        
        core.listPendingEquipment(buildingName: buildingName) { result in
            DispatchQueue.main.async {
                self.isLoading = false
                
                switch result {
                case .success(let listResult):
                    if pendingIds.isEmpty {
                        self.pendingEquipment = listResult.pendingItems
                    } else {
                        self.pendingEquipment = listResult.pendingItems.filter { pendingIds.contains($0.id) }
                    }
                    print("✅ Loaded \(listResult.pendingCount) pending equipment items")
                    
                case .failure(let error):
                    self.errorMessage = "Failed to load pending equipment: \(error.localizedDescription)"
                    print("❌ Failed to load pending equipment: \(error.localizedDescription)")
                }
            }
        }
    }
    
    private func confirmEquipment(_ id: String) {
        isLoading = true
        core.setActiveBuilding(buildingName)
        
        core.confirmPendingEquipment(
            buildingName: buildingName,
            pendingId: id,
            commitToGit: true,
            completion: { result in
            DispatchQueue.main.async {
                self.isLoading = false
                
                switch result {
                case .success(let confirmResult):
                    if confirmResult.committed {
                        self.successMessage = "Equipment '\(confirmResult.equipmentId)' confirmed and committed to Git (commit: \(confirmResult.commitId?.prefix(8) ?? "unknown"))"
                    } else {
                        self.successMessage = "Equipment '\(confirmResult.equipmentId)' confirmed and saved"
                    }
                    self.showSuccessAlert = true
                    
                    // Remove from list
                    self.pendingEquipment.removeAll { $0.id == id }
                    
                case .failure(let error):
                    self.errorMessage = "Failed to confirm equipment: \(error.localizedDescription)"
                    print("❌ Failed to confirm equipment: \(error.localizedDescription)")
                }
            }
        })
    }
    
    private func rejectEquipment(_ id: String) {
        isLoading = true
        core.setActiveBuilding(buildingName)
        
        core.rejectPendingEquipment(
            buildingName: buildingName,
            pendingId: id,
            completion: { result in
            DispatchQueue.main.async {
                self.isLoading = false
                
                switch result {
                case .success(let rejectResult):
                    self.successMessage = "Equipment '\(rejectResult.pendingId)' rejected"
                    self.showSuccessAlert = true
                    
                    // Remove from list
                    self.pendingEquipment.removeAll { $0.id == id }
                    
                case .failure(let error):
                    self.errorMessage = "Failed to reject equipment: \(error.localizedDescription)"
                    print("❌ Failed to reject equipment: \(error.localizedDescription)")
                }
            }
        })
    }
}

struct PendingEquipmentRow: View {
    let equipment: PendingEquipmentItem
    let onConfirm: () -> Void
    let onReject: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(equipment.name)
                        .font(.headline)
                    
                    Text(equipment.equipmentType)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    HStack {
                        Label("Confidence: \(Int(equipment.confidence * 100))%", systemImage: "checkmark.circle")
                            .font(.caption)
                            .foregroundColor(confidenceColor(equipment.confidence))
                        
                        Spacer()
                        
                        if let roomName = equipment.roomName {
                            Label(roomName, systemImage: "door.left.hand.open")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                
                Spacer()
            }
            
            // Position info
            HStack {
                Label("X: \(equipment.position.x, specifier: "%.2f")", systemImage: "xmark")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                
                Label("Y: \(equipment.position.y, specifier: "%.2f")", systemImage: "y.circle")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                
                Label("Z: \(equipment.position.z, specifier: "%.2f")", systemImage: "z.circle")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            // Action buttons
            HStack(spacing: 12) {
                Button(action: onReject) {
                    HStack {
                        Image(systemName: "xmark.circle.fill")
                        Text("Reject")
                    }
                    .font(.subheadline)
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.red)
                    .cornerRadius(8)
                }
                
                Spacer()
                
                Button(action: onConfirm) {
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                        Text("Confirm")
                    }
                    .font(.subheadline)
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(Color.green)
                    .cornerRadius(8)
                }
            }
        }
        .padding(.vertical, 8)
    }
    
    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.8 {
            return .green
        } else if confidence >= 0.6 {
            return .orange
        } else {
            return .red
        }
    }
}

struct EmptyPendingEquipmentView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "checkmark.circle")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            
            Text("No Pending Equipment")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("All pending equipment has been reviewed")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#Preview {
    PendingEquipmentConfirmationView(
        pendingIds: ["pending-1", "pending-2"],
        buildingName: "Test Building",
        core: ArxOSCore() // Provide a mock or dummy core for preview
    )
}

