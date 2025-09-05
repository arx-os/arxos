//! RF Invite tokens encoded as 13B ArxObjects (object_type = ACCESS_INVITE)
//! Encodes role, duration, and a MAC’d short code inside properties.

use crate::arxobject::{ArxObject, object_types};
use crate::crypto::PacketAuthenticator;

/// Compact role codes
#[derive(Debug, Clone, Copy)]
pub enum InviteRole { Viewer = 0x01, Technician = 0x02, Admin = 0x03 }

/// Create an invite token as an ArxObject
pub fn create_invite(
    building_id: u16,
    role: InviteRole,
    hours: u8,
    mac: &PacketAuthenticator,
    seed: u32,
) -> ArxObject {
    // Encode: props[0] = role, props[1] = hours; props[2..4] = first 2 bytes of MAC
    let mut temp = [0u8; 9];
    temp[0] = role as u8; temp[1] = hours;
    temp[2] = (seed & 0xFF) as u8; temp[3] = ((seed >> 8) & 0xFF) as u8; temp[4] = ((seed >> 16) & 0xFF) as u8; temp[5] = ((seed >> 24) & 0xFF) as u8;
    // MAC over role|hours|seed
    let tag = mac.generate_mac(&temp);

    let mut props = [0u8; 4];
    props[0] = role as u8;
    props[1] = hours;
    props[2] = tag[0];
    props[3] = tag[1];

    // Coordinates zero; broadcast building for invites or specific building
    ArxObject::with_properties(building_id, object_types::ACCESS_INVITE, 0, 0, 0, props)
}

/// Verify an invite object and extract (role, hours)
pub fn verify_invite(obj: &ArxObject, mac: &PacketAuthenticator, seed: u32) -> Option<(InviteRole, u8)> {
    if obj.object_type != object_types::ACCESS_INVITE { return None; }
    let role = match obj.properties[0] { 0x01 => InviteRole::Viewer, 0x02 => InviteRole::Technician, 0x03 => InviteRole::Admin, _ => return None };
    let hours = obj.properties[1];

    let mut temp = [0u8; 9];
    temp[0] = role as u8; temp[1] = hours;
    temp[2] = (seed & 0xFF) as u8; temp[3] = ((seed >> 8) & 0xFF) as u8; temp[4] = ((seed >> 16) & 0xFF) as u8; temp[5] = ((seed >> 24) & 0xFF) as u8;
    let tag = mac.generate_mac(&temp);
    if tag[0] != obj.properties[2] || tag[1] != obj.properties[3] { return None; }
    Some((role, hours))
}


