# ArxOS SMS Onboarding & Access Management

## The Problem
Contractors show up unexpectedly. They need building access NOW. Traditional IAM systems require:
- Pre-enrollment
- IT staff on-site  
- Internet connectivity
- App installation
- Complex authentication

## The ArxOS Solution
**Grant access in 30 seconds using SMS.**

## How It Works

### 1. Contractor Arrives
```bash
Contractor: "I'm here to fix the AC"
Manager: "What's your phone number?"
Contractor: "555-0100"
```

### 2. Manager Grants Access (One Command)
```bash
$ arx -newuser 555-0100 @west-high --temp
✅ Access SMS sent to 555-0100
```

Or even simpler:
```bash
$ grant 555-0100 hvac 4h
✅ Access granted for 4 hours
```

### 3. Contractor Gets SMS
```
🏢 West High Building Access

You've been granted 12 hour access.

Code: K7M3X9

Install ArxOS:
📱 arxos.app/ios

Or reply with code to activate
```

### 4. Two Paths

#### Path A: No App (Reply to SMS)
```
Contractor texts back: K7M3X9

Receives:
✅ Access activated!
Building: West High
Role: HVAC Tech
Valid: 12 hours

WiFi: west-high_mesh
Pass: K7M3
```

#### Path B: Has App (Deep Link)
- Taps link in SMS
- App opens with access already configured
- Immediately connected to building mesh

### 5. Access Token Over Mesh

The SMS code becomes a 13-byte ArxObject:
```rust
SMS Code: "K7M3X9"
Phone: 555-0100
     ↓
ArxObject {
    building_id: 0x0042,
    object_type: 0xFE, // Access token
    x: 0100,           // Phone suffix
    y: [role|company],
    z: [hours|trust],
    properties: [token_bytes]
}
     ↓
Mesh Packet: [13 bytes]
```

## CLI Commands

### Basic Commands
```bash
# Quick grant
grant PHONE ROLE HOURS
grant 555-0100 hvac 4h

# List active
list

# Revoke
revoke 555-0100
revoke all
```

### Full ArxOS Commands
```bash
# Grant with options
arx -newuser PHONE [@building] [--temp] [--role ROLE] [--hours N]

# Share with team
arx -share PHONE PHONE... [--role ROLE]

# Status
arx -status
```

## Real-World Scenarios

### Scenario 1: HVAC Emergency
```bash
$ grant 555-0100 hvac 2h
→ SMS sent
→ Tech replies with code
→ Access granted
→ Can see: HVAC + Electrical (read-only)
→ Can modify: HVAC only
→ Expires: 2 hours
```

### Scenario 2: Team Arrives
```bash
$ arx -share 555-0101 555-0102 555-0103 --role=electrical
→ 3 SMS sent
→ Lead tech's access shared
→ Same restrictions apply
→ Revoked if lead loses access
```

### Scenario 3: Inspector Visit
```bash
$ grant 555-9999 inspector 8h
→ SMS sent
→ Inspector gets wide read access
→ Cannot modify anything
→ Full audit trail
```

## Security Features

### Progressive Trust
- New contractors: Basic access
- After 10 visits: Standard access  
- After 6 months: Extended access
- Trust score: 0-255

### Access Control (13 bytes)
```
[Building:2][Company:1][Role:1][Expires:2][Mask:4][Trust:1][Check:2]
```

### Permission Check (3 operations)
```rust
1. building_id == object.building_id?  // 2-byte compare
2. expires > now?                       // 2-byte compare  
3. (mask & (1 << type)) != 0?          // bit shift + AND
```

## Why This Works

### Universal
- **Every contractor has a phone**
- Works with flip phones
- No smartphone required
- No app required initially

### Fast
- 30 seconds to grant access
- No pre-enrollment
- No certificates
- No complex setup

### Reliable
- Works without internet (SMS only)
- Mesh network for actual access
- No cloud dependency
- No vendor lock-in

### Practical
- Facility managers aren't IT experts
- Simple commands they can remember
- Visual feedback (SMS confirmation)
- Automatic expiration

## Implementation Requirements

### Building Side
- Raspberry Pi with cellular modem
- Or integration with existing SMS gateway
- SQLite database for tokens
- Mesh network nodes

### Phone Side
- Any phone that can receive SMS
- Optional: ArxOS app for better UX
- Optional: QR scanner for sharing

### Cost
- SMS: ~$0.01 per access grant
- No monthly fees
- No cloud costs
- Uses existing phones

## The Magic

**Complex IAM Problem → Simple SMS Solution**

Instead of:
- SAML, OAuth, LDAP, Active Directory
- Certificates, tokens, sessions
- Pre-enrollment, provisioning
- IT staff, help desk

Just:
- Phone number
- SMS code
- 13 bytes over mesh

## Example Integration

```rust
// In terminal interface
match input {
    "grant" => {
        let phone = get_phone();
        let role = get_role();
        let hours = get_hours();
        
        let token = generate_token();
        send_sms(phone, token);
        store_pending(token, phone, role, hours);
        
        println!("✅ Access SMS sent");
    }
}

// When SMS reply received
match sms_reply {
    token if valid(token) => {
        let access = create_access(token);
        broadcast_to_mesh(access.to_arxobject());
        send_confirmation_sms();
    }
}
```

## Future Enhancements

### WhatsApp/Signal Integration
Same flow but with:
- End-to-end encryption
- Read receipts
- Rich media (QR codes)

### Voice Activation
```
"Hey Siri, grant HVAC access to 555-0100"
→ Triggers ArxOS CLI
→ SMS sent automatically
```

### Geofencing
- Auto-grant when contractor arrives
- Auto-revoke when they leave
- Based on phone location

### Contractor Profiles
- Remember frequent contractors
- Auto-fill their usual role/hours
- Track performance over time

## Summary

ArxOS SMS onboarding solves the "unexpected contractor" problem with:
- **30-second setup**
- **No app required**
- **Works offline**
- **Universal compatibility**
- **13-byte access tokens**

Perfect for K-12 schools where:
- Contractors arrive unscheduled
- IT staff is limited
- Simplicity is critical
- Budget is tight
- Reliability matters

**The building texts you access. It's that simple.**