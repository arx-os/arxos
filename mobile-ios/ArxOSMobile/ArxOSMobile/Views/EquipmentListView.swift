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
        
        // Simulate loading equipment from ArxOS core
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            equipmentList = [
                Equipment(
                    id: "1",
                    name: "VAV-301",
                    type: "HVAC",
                    status: "Active",
                    location: "Room 301",
                    lastMaintenance: "2024-01-15"
                ),
                Equipment(
                    id: "2",
                    name: "Panel-301",
                    type: "Electrical",
                    status: "Active",
                    location: "Room 301",
                    lastMaintenance: "2024-01-10"
                ),
                Equipment(
                    id: "3",
                    name: "Sink-301",
                    type: "Plumbing",
                    status: "Maintenance",
                    location: "Room 301",
                    lastMaintenance: "2024-01-20"
                ),
                Equipment(
                    id: "4",
                    name: "Fire Alarm-301",
                    type: "Safety",
                    status: "Active",
                    location: "Room 301",
                    lastMaintenance: "2024-01-05"
                )
            ]
            isLoading = false
        }
    }
    
    private func refreshEquipment() {
        loadEquipment()
    }
}

struct Equipment: Identifiable {
    let id: String
    let name: String
    let type: String
    let status: String
    let location: String
    let lastMaintenance: String
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
