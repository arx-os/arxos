import Foundation

#if canImport(DeviceCheck)
import DeviceCheck
#endif

/// Phase 5 App Attest client hooks.
///
/// Production path uses `DCAppAttestService` on device. The mock path produces
/// statements consumable by `arxos-core` `MockAttestationVerifier` / CLI.
public enum AppAttestClient {
    public enum Environment: String, Sendable {
        case development
        case sandbox
        case production
    }

    /// Mock attestation statement bytes (UTF-8) matching Rust mock format.
    public static func mockStatement(subjectCid: String, deviceId: String) -> Data {
        Data("mock-attest:\(deviceId):\(subjectCid)".utf8)
    }

    /// Generate a mock key id for development.
    public static func mockDeviceId() -> String {
        UUID().uuidString.replacingOccurrences(of: "-", with: "").lowercased()
    }

    #if canImport(DeviceCheck)
    /// Whether App Attest is supported on this device.
    @available(iOS 14.0, *)
    public static var isSupported: Bool {
        DCAppAttestService.shared.isSupported
    }

    /// Generate a new App Attest key (returns keyId).
    @available(iOS 14.0, *)
    public static func generateKey() async throws -> String {
        try await DCAppAttestService.shared.generateKey()
    }

    /// Attest the key for `clientDataHash` (usually SHA256 of challenge / root CID).
    @available(iOS 14.0, *)
    public static func attestKey(keyId: String, clientDataHash: Data) async throws -> Data {
        try await DCAppAttestService.shared.attestKey(keyId, clientDataHash: clientDataHash)
    }
    #endif
}
