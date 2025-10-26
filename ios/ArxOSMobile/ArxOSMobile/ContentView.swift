import SwiftUI

struct ContentView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            TerminalView()
                .tabItem {
                    Image(systemName: "terminal")
                    Text("Terminal")
                }
                .tag(0)
            
            ARScanView()
                .tabItem {
                    Image(systemName: "camera.viewfinder")
                    Text("AR Scan")
                }
                .tag(1)
            
            EquipmentListView()
                .tabItem {
                    Image(systemName: "list.bullet")
                    Text("Equipment")
                }
                .tag(2)
        }
        .accentColor(.blue)
    }
}

#Preview {
    ContentView()
}
