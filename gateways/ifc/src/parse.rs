//! Minimal IFC STEP parser for the Arxos subset.

use std::collections::BTreeMap;

/// One parsed entity instance.
#[derive(Debug, Clone)]
pub struct IfcEntity {
    #[allow(dead_code)]
    pub id: u64,
    pub type_name: String,
    /// Raw argument string inside parentheses (not fully tokenized).
    pub args_raw: String,
}

/// Parsed IFC file (DATA section only).
#[derive(Debug, Clone, Default)]
pub struct IfcFile {
    pub entities: BTreeMap<u64, IfcEntity>,
    pub comments: Vec<String>,
}

/// Parse a STEP physical file into entities.
pub fn parse_ifc(text: &str) -> Result<IfcFile, String> {
    let mut file = IfcFile::default();
    let mut in_data = false;
    for line in text.lines() {
        let t = line.trim();
        if t.starts_with("/*") && t.ends_with("*/") {
            file.comments
                .push(t.trim_start_matches("/*").trim_end_matches("*/").trim().into());
        }
        if t == "DATA;" {
            in_data = true;
            continue;
        }
        if t == "ENDSEC;" && in_data {
            break;
        }
        if !in_data {
            continue;
        }
        if !t.starts_with('#') {
            continue;
        }
        // #12=IFCSPACE(...);
        let t = t.trim_end_matches(';');
        let (id_part, rest) = t
            .split_once('=')
            .ok_or_else(|| format!("bad entity: {t}"))?;
        let id: u64 = id_part
            .trim()
            .trim_start_matches('#')
            .parse()
            .map_err(|e| format!("bad id: {e}"))?;
        let rest = rest.trim();
        let paren = rest
            .find('(')
            .ok_or_else(|| format!("no args: {rest}"))?;
        let type_name = rest[..paren].trim().to_ascii_uppercase();
        let args_raw = rest[paren + 1..].trim().trim_end_matches(')').to_string();
        file.entities.insert(
            id,
            IfcEntity {
                id,
                type_name,
                args_raw,
            },
        );
    }
    Ok(file)
}

/// Split top-level STEP arguments (comma-separated, respecting quotes/parens).
pub fn split_args(s: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    let mut depth = 0i32;
    let mut in_str = false;
    let mut chars = s.chars().peekable();
    while let Some(c) = chars.next() {
        if in_str {
            cur.push(c);
            if c == '\'' {
                if chars.peek() == Some(&'\'') {
                    cur.push(chars.next().unwrap());
                } else {
                    in_str = false;
                }
            }
            continue;
        }
        match c {
            '\'' => {
                in_str = true;
                cur.push(c);
            }
            '(' => {
                depth += 1;
                cur.push(c);
            }
            ')' => {
                depth -= 1;
                cur.push(c);
            }
            ',' if depth == 0 => {
                out.push(cur.trim().to_string());
                cur.clear();
            }
            _ => cur.push(c),
        }
    }
    if !cur.trim().is_empty() {
        out.push(cur.trim().to_string());
    }
    out
}

pub fn unquote(s: &str) -> Option<String> {
    let s = s.trim();
    if s == "$" || s == "*" {
        return None;
    }
    if s.starts_with('\'') && s.ends_with('\'') && s.len() >= 2 {
        return Some(s[1..s.len() - 1].replace("''", "'"));
    }
    Some(s.to_string())
}

pub fn parse_ref(s: &str) -> Option<u64> {
    let s = s.trim();
    s.strip_prefix('#')?.parse().ok()
}

/// Extract IFCTEXT('...') or plain quoted from property value arg.
pub fn parse_typed_text(s: &str) -> Option<String> {
    let s = s.trim();
    if let Some(inner) = s.strip_prefix("IFCTEXT(").and_then(|x| x.strip_suffix(')')) {
        return unquote(inner);
    }
    unquote(s)
}
