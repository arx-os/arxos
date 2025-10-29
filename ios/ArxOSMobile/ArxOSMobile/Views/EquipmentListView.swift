import SwiftUI

struct EquipmentListView: View {
    @State private var equipmentList: [Equipment] = []
    @State private var isLoading = false
    @State private var searchText = ""
    @State private var selectedFilter: EquipmentFilter = .all
    
    enum EquipmentFilter: String, CaseIterable {
        case all = "All"
        case hvac = "HVAC"
        case electrical = "Electrical"
        case plumbing = "Plumbing"
        case safety = "Safety"
    }
    
    var filteredEquipment: [Equipment] {
        let filtered = equipmentList.filter { equipment in
            if !searchText.isEmpty {
                return equipment.name.localizedCaseInsensitiveContains(searchText)
            }
            return true
        }
        
        if selectedFilter != .all {
            return filtered.filter { $0.type.lowercased() == selectedFilter.rawValue.lowercased() }
        }
        
        return filtered
    }
    
    var body: some View {
        NavigationView {
            VStack {
                // Search and Filter Bar
                VStack {
                    SearchBar(text: $searchText)
                    
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack {
                            ForEach(EquipmentFilter.allCases, id: \.self) { filter in
                                FilterButton(
                                    title: filter.rawValue,
                                    isSelected: selectedFilter == filter
                                ) {
                                    selectedFilter = filter
                                }
                            }
                        }
                        .padding(.horizontal)
                    }
                }
                .padding(.vertical, 8)
                
                // Equipment List
                if isLoading {
                    ProgressView("Loading equipment...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if filteredEquipment.isEmpty {
                    EmptyStateView()
                } else {
                    List(filteredEquipment) { equipment in
                        EquipmentRowView(equipment: equipment)
                    }
                    .listStyle(PlainListStyle())
                }
            }
            .navigationTitle("Equipment")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: refreshEquipment) {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .onAppear {
                loadEquipment()
            }
        }
    }
    
    private func loadEquipment() {
        isLoading = true
        
        // FFI calls enabled - ready for testing
        let ffi = ArxOSCoreFFI()
        ffi.listEquipment(buildingName: "Default Building") { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let equipment):
                    // Convert EquipmentInfo to Equipment
                    self.equipmentList = equipment.map { eq in
                        Equipment(
                            id: eq.id,
                            name: eq.name,
                            type: eq.equipmentType,
                            status: eq.status,
                            location: "Room \(eq.position.x), \(eq.position.y)",
                            lastMaintenance: "Unknown"
                        )
                    }
                case .failure(let error):
                    print("Error loading equipment: \(error.localizedDescription)")
                    self.equipmentList = []
                }
                self.isLoading = false
            }
        }
    }
    
    private func refreshEquipment() {
        loadEquipment()
    }
}

struct EquipmentRowView: View {
    let equipment: Equipment
    
    var statusColor: Color {
        switch equipment.status.lowercased() {
        case "active":
            return .green
        case "maintenance":
            return .orange
        case "inactive":
            return .red
        default:
            return .gray
        }
    }
    
    var typeIcon: String {
        switch equipment.type.lowercased() {
        case "hvac":
            return "fan"
        case "electrical":
            return "bolt"
        case "plumbing":
            return "drop"
        case "safety":
            return "shield"
        default:
            return "gear"
        }
    }
    
    var body: some View {
        HStack {
            Image(systemName: typeIcon)
                .font(.title2)
                .foregroundColor(.blue)
                .frame(width: 30)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(equipment.name)
                    .font(.headline)
                
                Text(equipment.location)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text(equipment.status)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(statusColor.opacity(0.2))
                    .foregroundColor(statusColor)
                    .cornerRadius(8)
                
                Text("Last: \(equipment.lastMaintenance)")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

struct SearchBar: View {
    @Binding var text: String
    
    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            
            TextField("Search equipment...", text: $text)
                .textFieldStyle(PlainTextFieldStyle())
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color(.systemGray6))
        .cornerRadius(10)
        .padding(.horizontal)
    }
}

struct FilterButton: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isSelected ? Color.blue : Color(.systemGray5))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(16)
        }
    }
}

struct EmptyStateView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "list.bullet")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            
            Text("No Equipment Found")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Start scanning rooms to detect equipment")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#Preview {
    EquipmentListView()
}
