import SwiftUI
import ArxosCore

/// Blank Phase 0 SwiftUI app — lived-experience shell.
/// ARKit / RoomPlan / LiDAR capture arrive in Phase 1.
@main
struct ArxosApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    @State private var greeting: String = ""
    @State private var buildingId: String = ""

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Text("Arxos")
                    .font(.largeTitle.bold())

                Text("Phase 0 — Foundation")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                Divider()

                VStack(alignment: .leading, spacing: 12) {
                    labeled("Core version", ArxosCore.version())
                    labeled("Hello", greeting.isEmpty ? "—" : greeting)
                    labeled("BuildingId", buildingId.isEmpty ? "—" : buildingId)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))

                Button("Call Rust hello()") {
                    greeting = ArxosCore.hello(name: "iOS")
                    buildingId = ArxosCore.generateBuildingId()
                }
                .buttonStyle(.borderedProminent)

                Text("No general 3D rendering. Geometry is data only.\nCapture loop lands in Phase 1.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.top, 8)

                Spacer()
            }
            .padding()
            .navigationTitle("Arxos")
            .onAppear {
                greeting = ArxosCore.hello(name: "iOS")
                buildingId = ArxosCore.generateBuildingId()
            }
        }
    }

    @ViewBuilder
    private func labeled(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title.uppercased())
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.body.monospaced())
                .textSelection(.enabled)
        }
    }
}

#Preview {
    ContentView()
}
