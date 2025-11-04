//
//  EquipmentPlacementDialog.swift
//  ArxOSMobile
//
//  Dialog for placing equipment via tap-to-place in AR
//

import SwiftUI

struct EquipmentPlacementDialog: View {
    @Binding var equipmentName: String
    @Binding var equipmentType: String
    let onSave: () -> Void
    let onCancel: () -> Void
    
    @Environment(\.dismiss) var dismiss
    
    let equipmentTypes = [
        "Unknown",
        "HVAC",
        "Electrical",
        "Plumbing",
        "Lighting",
        "Safety",
        "Fire Safety",
        "Other"
    ]
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Equipment Details")) {
                    TextField("Equipment Name", text: $equipmentName)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                    
                    Picker("Equipment Type", selection: $equipmentType) {
                        ForEach(equipmentTypes, id: \.self) { type in
                            Text(type).tag(type)
                        }
                    }
                    .pickerStyle(MenuPickerStyle())
                }
                
                Section(header: Text("Instructions")) {
                    Text("Tap on a surface in AR to place equipment. Then fill in the details above.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .navigationTitle("Place Equipment")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        onCancel()
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        onSave()
                        dismiss()
                    }
                    .disabled(equipmentName.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }
}

#Preview {
    EquipmentPlacementDialog(
        equipmentName: .constant("VAV-301"),
        equipmentType: .constant("HVAC"),
        onSave: {},
        onCancel: {}
    )
}

