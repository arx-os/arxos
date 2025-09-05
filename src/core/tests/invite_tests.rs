use arxos_core::invites::invite::{create_invite, verify_invite, InviteRole};
use arxos_core::crypto::PacketAuthenticator;

#[test]
fn test_invite_create_and_verify() {
    let mac = PacketAuthenticator::new([0x55; 32]);
    let building_id = 0x2468;
    let role = InviteRole::Technician;
    let hours: u8 = 12;
    let seed: u32 = 0xDEADBEEF;

    let obj = create_invite(building_id, role, hours, &mac, seed);
    assert_eq!(obj.building_id, building_id);
    assert_eq!(obj.object_type, arxos_core::arxobject::object_types::ACCESS_INVITE);

    let verified = verify_invite(&obj, &mac, seed).expect("invite should verify");
    assert_eq!(verified.0 as u8, role as u8);
    assert_eq!(verified.1, hours);
}

#[test]
fn test_invite_tamper_detected() {
    let mac = PacketAuthenticator::new([0x55; 32]);
    let building_id = 0x1357;
    let role = InviteRole::Viewer;
    let hours: u8 = 2;
    let seed: u32 = 0x01020304;

    let mut obj = create_invite(building_id, role, hours, &mac, seed);
    // Tamper with hours
    obj.properties[1] ^= 0x01;
    assert!(verify_invite(&obj, &mac, seed).is_none());
}


