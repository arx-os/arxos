//! Shared builders for field/label text DSL scripts.
//!
//! Used by CLI helpers and agent `field.*` RPCs so clients do not invent quoting.
//! Mirrors iOS `EditScript` rules and core `text.rs` tokenizer (double quotes).

use anyhow::{bail, Result};

/// Max length for room / equipment names in field RPCs.
pub const MAX_NAME_LEN: usize = 128;

/// Validate a human-facing room or equipment name before interpolation.
pub fn validate_name(raw: &str, kind: &str) -> Result<String> {
    let name = raw.trim();
    if name.is_empty() {
        bail!("{kind} name is empty");
    }
    if name.chars().count() > MAX_NAME_LEN {
        bail!("{kind} name is too long (max {MAX_NAME_LEN} characters)");
    }
    // Core tokenizer has no escape for embedded `"`. Reject injection / parse breaks.
    if name.contains('"') || name.contains('\n') || name.contains('\r') {
        bail!("{kind} name may not contain quotes or newlines");
    }
    if name.chars().any(|c| c.is_control()) {
        bail!("{kind} name may not contain control characters");
    }
    Ok(name.to_string())
}

/// Quote a token if it contains whitespace or `=` (key=value ambiguity).
pub fn quote_token(value: &str) -> String {
    if value.chars().any(|c| c.is_whitespace() || c == '=') {
        format!("\"{value}\"")
    } else {
        value.to_string()
    }
}

/// Ensure equipment exists as proposed (room must already exist).
pub fn label_equipment_script(room: &str, equipment: &str) -> Result<String> {
    let room = validate_name(room, "Room")?;
    let equip = validate_name(equipment, "Equipment")?;
    let rq = quote_token(&room);
    let eq = quote_token(&equip);
    Ok(format!(
        "add equipment {eq} room={rq} type=electrical\nset equipment {eq} review_status=proposed\n"
    ))
}

/// Create proposed room + equipment when the room is missing.
pub fn create_room_and_label_script(room: &str, equipment: &str) -> Result<String> {
    let room = validate_name(room, "Room")?;
    let equip = validate_name(equipment, "Equipment")?;
    let rq = quote_token(&room);
    let eq = quote_token(&equip);
    Ok(format!(
        "add room {rq} floor=0 type=other\n\
         set room {rq} review_status=proposed\n\
         add equipment {eq} room={rq} type=electrical\n\
         set equipment {eq} review_status=proposed\n"
    ))
}

/// Stamp existing equipment as proposed (idempotent label).
pub fn mark_equipment_proposed_script(equipment: &str) -> Result<String> {
    let equip = validate_name(equipment, "Equipment")?;
    let eq = quote_token(&equip);
    Ok(format!("set equipment {eq} review_status=proposed\n"))
}

/// Accept a room (`review_status=accepted`).
pub fn accept_room_script(room: &str) -> Result<String> {
    let room = validate_name(room, "Room")?;
    let rq = quote_token(&room);
    Ok(format!("set room {rq} review_status=accepted\n"))
}

/// Human grammar cheat-sheet (CLI / docs).
pub fn grammar_help() -> &'static str {
    r#"Text / AR edit DSL (one command per line; # comments ok)

  add room <name> floor=<n|name> [wing=<name>] [type=<room_type>] [pos=x,y,z] [dims=WxDxH]
  add equipment <name> room=<room_name> [type=<eq_type>] [pos=x,y,z]
  set room <name> <key>=<value> [...]
  set equipment <name> status=<status> | <key>=<value>
  rename room <old> <new>

Review (Decision 10):
  set room <name> review_status=proposed|accepted|rejected
  set equipment <name> review_status=proposed|accepted|rejected

Quoting: multi-word names use double quotes, e.g. add room "Studio A" floor=0
  Names may not contain " or newlines.

Field clients should prefer structured agent RPCs (field.label, field.accept_room)
instead of free-form scripts when possible. See docs/field-language.md."#
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quotes_multi_word() {
        let s = label_equipment_script("Room 1", "Light Switch").unwrap();
        assert!(s.contains("room=\"Room 1\""));
        assert!(s.contains("\"Light Switch\""));
    }

    #[test]
    fn rejects_quote_injection() {
        assert!(validate_name("evil\"x", "Room").is_err());
        assert!(validate_name("a\nb", "Room").is_err());
    }

    #[test]
    fn simple_tokens_unquoted() {
        let s = label_equipment_script("Lab", "panel-1").unwrap();
        assert!(s.contains("room=Lab"));
        assert!(s.contains("add equipment panel-1"));
    }
}
