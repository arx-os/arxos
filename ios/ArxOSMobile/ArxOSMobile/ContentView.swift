import SwiftUI

struct ContentView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            ARTerminalView()
                .tabItem {
                    Image(systemName: "square.split.diagonal")
                    Text("AR Terminal")
                }
                .tag(0)
            
            TerminalView()
                .tabItem {
                    Image(systemName: "terminal")
                    Text("Terminal")
                }
                .tag(1)
            
            ARScanView()
                .tabItem {
                    Image(systemName: "camera.viewfinder")
                    Text("AR Scan")
                }
                .tag(2)
            
            EquipmentListView()
                .tabItem {
                    Image(systemName: "list.bullet")
                    Text("Equipment")
                }
                .tag(3)
        }
        .accentColor(.blue)
    }
}

#Preview {
    ContentView()
}
