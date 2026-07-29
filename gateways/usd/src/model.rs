//! Minimal in-memory USD stage model for USDA emit/parse.

use std::collections::BTreeMap;

/// Typed attribute value (subset).
#[derive(Debug, Clone, PartialEq)]
pub enum UsdValue {
    String(String),
    Float(f64),
    Float3([f64; 3]),
    Float3Array(Vec<[f64; 3]>),
    Token(String),
    Asset(String),
}

/// One prim in the stage.
#[derive(Debug, Clone)]
pub struct UsdPrim {
    pub path: String,
    pub type_name: String,
    pub specifier: String, // def | over | class
    pub attrs: BTreeMap<String, UsdValue>,
    pub metadata: BTreeMap<String, String>,
}

/// In-memory stage.
#[derive(Debug, Clone, Default)]
pub struct UsdStage {
    pub up_axis: String,
    pub meters_per_unit: f64,
    pub default_prim: Option<String>,
    pub custom_layer_data: BTreeMap<String, String>,
    pub prims: Vec<UsdPrim>,
}

impl UsdStage {
    pub fn new() -> Self {
        Self {
            up_axis: "Y".into(),
            meters_per_unit: 1.0,
            default_prim: None,
            custom_layer_data: BTreeMap::new(),
            prims: Vec::new(),
        }
    }

    /// Serialize to USDA text (OpenUSD-compatible ASCII).
    pub fn to_usda(&self) -> String {
        let mut out = String::new();
        out.push_str("#usda 1.0\n");
        out.push_str("(\n");
        out.push_str(&format!("    upAxis = \"{}\"\n", self.up_axis));
        out.push_str(&format!("    metersPerUnit = {}\n", self.meters_per_unit));
        if let Some(dp) = &self.default_prim {
            out.push_str(&format!("    defaultPrim = \"{}\"\n", sanitize_name(dp.trim_start_matches('/'))));
        }
        if !self.custom_layer_data.is_empty() {
            out.push_str("    customLayerData = {\n");
            for (k, v) in &self.custom_layer_data {
                out.push_str(&format!(
                    "        string {} = \"{}\"\n",
                    sanitize_ident(k),
                    escape_str(v)
                ));
            }
            out.push_str("    }\n");
        }
        out.push_str(")\n\n");

        for prim in &self.prims {
            let name = prim
                .path
                .rsplit('/')
                .next()
                .unwrap_or("Prim");
            let parent_indent = prim.path.matches('/').count().saturating_sub(1);
            // Flat emit with full path in comment for readability; structure as nested only one level
            // Phase 4: emit each prim with absolute path using over-style absolute defs.
            out.push_str(&format!(
                "def {} \"{}\" (\n",
                prim.type_name,
                sanitize_name(name)
            ));
            // USD requires nested hierarchy for parent paths — we emit a flat list of
            // absolute prims via `def` under synthetic parents created earlier.
            if !prim.metadata.is_empty() {
                for (k, v) in &prim.metadata {
                    out.push_str(&format!("    {} = \"{}\"\n", k, escape_str(v)));
                }
            }
            out.push_str(")\n{\n");
            for (k, v) in &prim.attrs {
                out.push_str("    ");
                out.push_str(&format_attr(k, v));
                out.push('\n');
            }
            // Record full path for importers
            out.push_str(&format!(
                "    custom string arxos:path = \"{}\"\n",
                escape_str(&prim.path)
            ));
            let _ = parent_indent;
            out.push_str("}\n\n");
        }
        out
    }
}

fn format_attr(name: &str, v: &UsdValue) -> String {
    match v {
        UsdValue::String(s) => format!("custom string {} = \"{}\"", name, escape_str(s)),
        UsdValue::Token(s) => format!("uniform token {} = \"{}\"", name, escape_str(s)),
        UsdValue::Float(f) => format!("float {} = {}", name, f),
        UsdValue::Float3(a) => format!(
            "float3 {} = ({}, {}, {})",
            name, a[0], a[1], a[2]
        ),
        UsdValue::Float3Array(pts) => {
            let body: Vec<String> = pts
                .iter()
                .map(|p| format!("({}, {}, {})", p[0], p[1], p[2]))
                .collect();
            format!("point3f[] {} = [{}]", name, body.join(", "))
        }
        UsdValue::Asset(s) => format!("asset {} = @{}@", name, s),
    }
}

pub fn escape_str(s: &str) -> String {
    s.replace('\\', "\\\\").replace('"', "\\\"")
}

pub fn sanitize_name(s: &str) -> String {
    let mut out = String::new();
    for (i, c) in s.chars().enumerate() {
        if c.is_ascii_alphanumeric() || c == '_' {
            out.push(c);
        } else {
            out.push('_');
        }
        if i == 0 && out.starts_with(|c: char| c.is_ascii_digit()) {
            out.insert(0, '_');
        }
    }
    if out.is_empty() {
        "Prim".into()
    } else {
        out
    }
}

pub fn sanitize_ident(s: &str) -> String {
    sanitize_name(s)
}

/// Parse a minimal USDA subset produced by this crate (and similar exporters).
pub fn parse_usda(text: &str) -> Result<UsdStage, String> {
    let mut stage = UsdStage::new();
    let mut current: Option<UsdPrim> = None;
    let mut in_prim = false;

    for raw in text.lines() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if line.starts_with("def ") && line.contains('"') {
            if let Some(p) = current.take() {
                stage.prims.push(p);
            }
            // def Xform "Name"
            let type_name = line
                .strip_prefix("def ")
                .and_then(|s| s.split_whitespace().next())
                .unwrap_or("Xform")
                .to_string();
            let name = extract_quoted(line).unwrap_or_else(|| "Prim".into());
            current = Some(UsdPrim {
                path: format!("/{name}"),
                type_name,
                specifier: "def".into(),
                attrs: BTreeMap::new(),
                metadata: BTreeMap::new(),
            });
            in_prim = false;
            continue;
        }
        if line == "{" {
            in_prim = true;
            continue;
        }
        if line == "}" {
            if let Some(p) = current.take() {
                stage.prims.push(p);
            }
            in_prim = false;
            continue;
        }
        if !in_prim {
            if line.starts_with("upAxis") {
                if let Some(v) = extract_quoted(line) {
                    stage.up_axis = v;
                }
            } else if line.starts_with("metersPerUnit") {
                if let Some(num) = line.split('=').nth(1) {
                    if let Ok(f) = num.trim().trim_end_matches(',').parse() {
                        stage.meters_per_unit = f;
                    }
                }
            } else if line.starts_with("defaultPrim") {
                if let Some(v) = extract_quoted(line) {
                    stage.default_prim = Some(format!("/{v}"));
                }
            } else if line.starts_with("string ") && line.contains('=') {
                // customLayerData entries: string arxosRootCid = "..."
                if let Some(rest) = line.strip_prefix("string ") {
                    if let Some((name, val)) = rest.split_once('=') {
                        if let Some(v) = extract_quoted(val) {
                            stage
                                .custom_layer_data
                                .insert(name.trim().to_string(), v);
                        }
                    }
                }
            }
            continue;
        }
        if let Some(prim) = current.as_mut() {
            if let Some((key, val)) = parse_attr_line(line) {
                if key == "arxos:path" {
                    if let UsdValue::String(p) = &val {
                        prim.path = p.clone();
                    }
                }
                prim.attrs.insert(key, val);
            }
        }
    }
    if let Some(p) = current.take() {
        stage.prims.push(p);
    }
    Ok(stage)
}

fn extract_quoted(s: &str) -> Option<String> {
    let start = s.find('"')? + 1;
    let end = s[start..].find('"')? + start;
    Some(s[start..end].replace("\\\"", "\"").replace("\\\\", "\\"))
}

fn parse_attr_line(line: &str) -> Option<(String, UsdValue)> {
    // custom string arxos:cid = "b3:..."
    // float3 xformOp:translate = (1, 2, 3)
    // point3f[] points = [(0,0,0), (1,0,0)]
    let line = line.trim().trim_end_matches(';');
    if let Some(rest) = line.strip_prefix("custom string ") {
        let (name, val) = split_eq(rest)?;
        return Some((name, UsdValue::String(extract_quoted(val).unwrap_or_default())));
    }
    if let Some(rest) = line.strip_prefix("uniform token ") {
        let (name, val) = split_eq(rest)?;
        return Some((name, UsdValue::Token(extract_quoted(val).unwrap_or_default())));
    }
    if let Some(rest) = line.strip_prefix("float3 ") {
        let (name, val) = split_eq(rest)?;
        return Some((name, UsdValue::Float3(parse_float3(val)?)));
    }
    if let Some(rest) = line.strip_prefix("float ") {
        let (name, val) = split_eq(rest)?;
        let f: f64 = val.trim().parse().ok()?;
        return Some((name, UsdValue::Float(f)));
    }
    if let Some(rest) = line.strip_prefix("point3f[] ") {
        let (name, val) = split_eq(rest)?;
        return Some((name, UsdValue::Float3Array(parse_float3_array(val)?)));
    }
    None
}

fn split_eq(s: &str) -> Option<(String, &str)> {
    let (a, b) = s.split_once('=')?;
    Some((a.trim().to_string(), b.trim()))
}

fn parse_float3(s: &str) -> Option<[f64; 3]> {
    let s = s.trim().trim_start_matches('(').trim_end_matches(')');
    let parts: Vec<_> = s.split(',').map(|p| p.trim().parse::<f64>().ok()).collect();
    if parts.len() != 3 {
        return None;
    }
    Some([parts[0]?, parts[1]?, parts[2]?])
}

fn parse_float3_array(s: &str) -> Option<Vec<[f64; 3]>> {
    let s = s.trim().trim_start_matches('[').trim_end_matches(']');
    if s.is_empty() {
        return Some(Vec::new());
    }
    let mut out = Vec::new();
    for chunk in s.split("),") {
        let c = chunk.trim().trim_start_matches('(').trim_end_matches(')');
        let parts: Vec<_> = c.split(',').map(|p| p.trim().parse::<f64>().ok()).collect();
        if parts.len() == 3 {
            out.push([parts[0]?, parts[1]?, parts[2]?]);
        }
    }
    Some(out)
}
