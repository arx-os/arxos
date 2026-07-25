//! Postal address → ADR 0001 fully-qualified building root derivation.
//!
//! Target form (single path segment, no leading slash in the core string):
//! `bldg.<country>.<region>.<city>.<street>-<number>[.<unit>]`
//!
//! Example:
//! `143677 N. Dale Mabry Hwy, Suite 2, Tampa, FL, 33622`
//! → `bldg.us.fl.tampa.dale-mabry.143677.s2`

use super::address::ArxAddress;
use anyhow::{anyhow, Result};

/// Structured postal fields used for deterministic root derivation.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct PostalAddress {
    pub country: String,
    pub region: String,
    pub city: String,
    pub street: String,
    pub number: String,
    pub unit: Option<String>,
}

impl PostalAddress {
    pub fn new(
        country: impl Into<String>,
        region: impl Into<String>,
        city: impl Into<String>,
        street: impl Into<String>,
        number: impl Into<String>,
        unit: Option<String>,
    ) -> Self {
        Self {
            country: country.into(),
            region: region.into(),
            city: city.into(),
            street: street.into(),
            number: number.into(),
            unit,
        }
    }

    /// True when enough fields exist to form a root.
    pub fn is_complete(&self) -> bool {
        !self.country.trim().is_empty()
            && !self.region.trim().is_empty()
            && !self.city.trim().is_empty()
            && !self.street.trim().is_empty()
            && !self.number.trim().is_empty()
    }
}

/// Directional prefixes dropped from street names.
const DIRECTIONALS: &[&str] = &[
    "n", "s", "e", "w", "ne", "nw", "se", "sw", "north", "south", "east", "west",
    "northeast", "northwest", "southeast", "southwest",
];

/// Street type suffixes dropped from street names.
const STREET_SUFFIXES: &[&str] = &[
    "hwy",
    "highway",
    "st",
    "street",
    "ave",
    "avenue",
    "blvd",
    "boulevard",
    "rd",
    "road",
    "dr",
    "drive",
    "ln",
    "lane",
    "ct",
    "court",
    "pl",
    "place",
    "pkwy",
    "parkway",
    "cir",
    "circle",
    "way",
    "ter",
    "terrace",
    "trl",
    "trail",
    "aly",
    "alley",
    "expy",
    "expressway",
    "fwy",
    "freeway",
];

/// US state/territory → 2-letter codes (lowercase).
fn normalize_region(raw: &str) -> String {
    let t = raw.trim().to_lowercase().replace('.', "");
    if t.len() == 2 && t.chars().all(|c| c.is_ascii_alphabetic()) {
        return t;
    }
    match t.as_str() {
        "florida" => "fl".into(),
        "california" => "ca".into(),
        "new york" => "ny".into(),
        "texas" => "tx".into(),
        "georgia" => "ga".into(),
        "washington" => "wa".into(),
        "massachusetts" => "ma".into(),
        "pennsylvania" => "pa".into(),
        "illinois" => "il".into(),
        "ohio" => "oh".into(),
        "arizona" => "az".into(),
        "colorado" => "co".into(),
        "nevada" => "nv".into(),
        "oregon" => "or".into(),
        "michigan" => "mi".into(),
        "north carolina" => "nc".into(),
        "south carolina" => "sc".into(),
        "virginia" => "va".into(),
        "maryland" => "md".into(),
        "new jersey" => "nj".into(),
        "connecticut" => "ct".into(),
        "minnesota" => "mn".into(),
        "wisconsin" => "wi".into(),
        "tennessee" => "tn".into(),
        "missouri" => "mo".into(),
        "indiana" => "in".into(),
        "alabama" => "al".into(),
        "louisiana" => "la".into(),
        "kentucky" => "ky".into(),
        "oklahoma" => "ok".into(),
        "utah" => "ut".into(),
        "iowa" => "ia".into(),
        "arkansas" => "ar".into(),
        "mississippi" => "ms".into(),
        "kansas" => "ks".into(),
        "new mexico" => "nm".into(),
        "nebraska" => "ne".into(),
        "idaho" => "id".into(),
        "hawaii" => "hi".into(),
        "maine" => "me".into(),
        "new hampshire" => "nh".into(),
        "rhode island" => "ri".into(),
        "montana" => "mt".into(),
        "delaware" => "de".into(),
        "south dakota" => "sd".into(),
        "north dakota" => "nd".into(),
        "alaska" => "ak".into(),
        "vermont" => "vt".into(),
        "wyoming" => "wy".into(),
        "west virginia" => "wv".into(),
        "district of columbia" | "washington dc" | "washington d c" => "dc".into(),
        _ => ArxAddress::sanitize_part(&t),
    }
}

fn normalize_country(raw: &str) -> String {
    let t = raw.trim().to_lowercase().replace('.', "");
    match t.as_str() {
        "" => "us".into(),
        "usa" | "united states" | "united states of america" | "u s" | "u s a" | "us" => {
            "us".into()
        }
        "uk" | "united kingdom" | "great britain" | "gb" => "gb".into(),
        "canada" | "ca" if t == "canada" => "ca".into(),
        other if other.len() == 2 => other.to_string(),
        other => ArxAddress::sanitize_part(other),
    }
}

/// Simplify street name: drop directionals and type suffixes; kebab-case.
pub fn simplify_street(street: &str) -> String {
    let cleaned = street
        .to_lowercase()
        .replace(['.', ',', '#'], " ");
    let tokens: Vec<&str> = cleaned
        .split_whitespace()
        .filter(|t| !t.is_empty())
        .collect();
    if tokens.is_empty() {
        return String::new();
    }

    let mut start = 0usize;
    let mut end = tokens.len();

    // Drop leading directionals
    while start < end && DIRECTIONALS.contains(&tokens[start]) {
        start += 1;
    }
    // Drop trailing street suffixes (may stack rarely)
    while end > start && STREET_SUFFIXES.contains(&tokens[end - 1]) {
        end -= 1;
    }
    // If everything stripped, fall back to original tokens without only-directionals
    let slice = if start >= end {
        &tokens[..]
    } else {
        &tokens[start..end]
    };

    ArxAddress::sanitize_part(&slice.join(" "))
}

/// Normalize unit/suite: `Suite 2` → `s2`, `Unit 4` → `u4`, `#12` → `u12`, bare `2` → `u2`.
pub fn normalize_unit(unit: &str) -> Option<String> {
    let owned = unit.trim().to_lowercase();
    if owned.is_empty() {
        return None;
    }
    let t: &str = owned.trim_start_matches('#').trim();

    // Already canonical (s2, u4, a3b)
    if t.len() >= 2
        && matches!(t.as_bytes()[0], b's' | b'u' | b'a' | b'f')
        && t[1..].chars().all(|c| c.is_ascii_alphanumeric())
        && t[1..].chars().any(|c| c.is_ascii_digit())
    {
        return Some(t.to_string());
    }

    let (prefix, rest): (&str, &str) = if let Some(r) = t.strip_prefix("suite") {
        ("s", r)
    } else if let Some(r) = t.strip_prefix("ste") {
        ("s", r)
    } else if let Some(r) = t.strip_prefix("unit") {
        ("u", r)
    } else if let Some(r) = t.strip_prefix("apt") {
        ("a", r)
    } else if let Some(r) = t.strip_prefix("apartment") {
        ("a", r)
    } else if let Some(r) = t.strip_prefix("floor") {
        ("f", r)
    } else if let Some(r) = t.strip_prefix("fl") {
        // avoid matching "florida" — only "fl " or "fl." or "fl2"
        if r.is_empty()
            || r.starts_with(|c: char| c.is_ascii_whitespace() || c == '.' || c.is_ascii_digit())
        {
            ("f", r)
        } else {
            ("", t)
        }
    } else {
        ("", t)
    };

    let digits: String = rest.chars().filter(|c| c.is_ascii_alphanumeric()).collect();
    if digits.is_empty() {
        let slug = ArxAddress::sanitize_part(t);
        return if slug.is_empty() { None } else { Some(slug) };
    }
    if prefix.is_empty() {
        // bare number → uN
        Some(format!("u{}", digits.to_lowercase()))
    } else {
        Some(format!("{}{}", prefix, digits.to_lowercase()))
    }
}

/// Derive the canonical building root string (**no** leading slash).
///
/// Form (ADR concrete example): `bldg.<country>.<region>.<city>.<street>.<number>[.<unit>]`
///
/// All components are joined with `.` into **one** path segment.
pub fn derive_building_root_string(postal: &PostalAddress) -> Result<String> {
    if !postal.is_complete() {
        return Err(anyhow!(
            "postal address incomplete: need country, region, city, street, and number"
        ));
    }
    let country = normalize_country(&postal.country);
    let region = normalize_region(&postal.region);
    let city = ArxAddress::sanitize_part(&postal.city);
    let street = simplify_street(&postal.street);
    let number = ArxAddress::sanitize_part(&postal.number);
    if country.is_empty()
        || region.is_empty()
        || city.is_empty()
        || street.is_empty()
        || number.is_empty()
    {
        return Err(anyhow!(
            "postal address produced empty component after normalization"
        ));
    }
    let mut core = format!(
        "bldg.{}.{}.{}.{}.{}",
        country, region, city, street, number
    );
    if let Some(ref u) = postal.unit {
        if let Some(nu) = normalize_unit(u) {
            core.push('.');
            core.push_str(&nu);
        }
    }
    // Ensure the whole root is a valid single address segment
    if !ArxAddress::is_valid_segment(&core) {
        return Err(anyhow!(
            "derived root is not a valid address segment: {}",
            core
        ));
    }
    Ok(core)
}

/// Derive `ArxAddress` building root (leading `/` for storage).
pub fn postal_building_root(postal: &PostalAddress) -> Result<ArxAddress> {
    let core = derive_building_root_string(postal)?;
    ArxAddress::from_path(&core)
}

/// Convenience from structured string slices (same as ADR helper shape).
pub fn postal_building_root_fields(
    country: &str,
    region: &str,
    city: &str,
    street: &str,
    number: &str,
    unit: Option<&str>,
) -> Result<ArxAddress> {
    postal_building_root(&PostalAddress {
        country: country.into(),
        region: region.into(),
        city: city.into(),
        street: street.into(),
        number: number.into(),
        unit: unit.map(|s| s.to_string()),
    })
}

/// Parse a free-form US-style postal string into structured fields.
///
/// Handles patterns like:
/// `143677 N. Dale Mabry Hwy, Suite 2, Tampa, FL, 33622`
pub fn parse_postal_string(input: &str) -> Result<PostalAddress> {
    let input = input.trim();
    if input.is_empty() {
        return Err(anyhow!("empty postal address"));
    }

    let mut parts: Vec<String> = input
        .split(',')
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();
    if parts.is_empty() {
        return Err(anyhow!("could not parse postal address"));
    }

    let mut country = String::from("us");
    let mut zip: Option<String> = None;

    // Trailing country
    if let Some(last) = parts.last() {
        let l = last.to_lowercase();
        if matches!(
            l.as_str(),
            "usa" | "us" | "united states" | "united states of america"
        ) {
            country = "us".into();
            parts.pop();
        }
    }

    // Trailing ZIP and/or "ST ZIP" combined field
    let mut region = String::new();
    if let Some(last) = parts.last().cloned() {
        let tokens: Vec<&str> = last.split_whitespace().collect();
        // "FL 33622" or "CA 94105"
        if tokens.len() == 2 {
            let digs: String = tokens[1].chars().filter(|c| c.is_ascii_digit()).collect();
            if digs.len() == 5 || digs.len() == 9 {
                region = normalize_region(tokens[0]);
                zip = Some(digs);
                parts.pop();
            }
        }
        if zip.is_none() {
            let digits: String = last.chars().filter(|c| c.is_ascii_digit()).collect();
            if (digits.len() == 5 || digits.len() == 9)
                && last.chars().all(|c| c.is_ascii_digit() || c == '-')
            {
                zip = Some(digits);
                parts.pop();
            }
        }
    }
    let _ = zip;

    // Trailing state/region (if not already taken from ST ZIP)
    if region.is_empty() {
        if let Some(last) = parts.last() {
            let cand = normalize_region(last);
            if cand.len() == 2 || last.split_whitespace().count() <= 2 {
                region = cand;
                parts.pop();
            }
        }
    }
    if region.is_empty() {
        return Err(anyhow!(
            "could not find state/region in postal address: {}",
            input
        ));
    }

    // City
    let city = parts
        .pop()
        .ok_or_else(|| anyhow!("could not find city in postal address: {}", input))?;

    // Unit may be last remaining non-street part
    let mut unit: Option<String> = None;
    let street_line = if parts.len() >= 2 {
        // Heuristic: if last part looks like unit, peel it
        if let Some(last) = parts.last() {
            let low = last.to_lowercase();
            if low.starts_with("suite")
                || low.starts_with("ste")
                || low.starts_with("unit")
                || low.starts_with("apt")
                || low.starts_with('#')
                || low.starts_with("apartment")
            {
                unit = Some(parts.pop().unwrap());
            }
        }
        parts.join(" ")
    } else if parts.len() == 1 {
        let mut line = parts.pop().unwrap();
        // Unit embedded: "143677 N. Dale Mabry Hwy Suite 2"
        if let Some((street_part, unit_part)) = split_trailing_unit(&line) {
            line = street_part;
            unit = Some(unit_part);
        }
        line
    } else {
        return Err(anyhow!(
            "could not find street line in postal address: {}",
            input
        ));
    };

    let (number, street) = split_number_and_street(&street_line)
        .ok_or_else(|| anyhow!("could not parse street number from: {}", street_line))?;

    Ok(PostalAddress {
        country,
        region,
        city,
        street,
        number,
        unit,
    })
}

/// Parse free-form postal text and return the building root `ArxAddress`.
pub fn postal_building_root_from_str(input: &str) -> Result<ArxAddress> {
    let postal = parse_postal_string(input)?;
    postal_building_root(&postal)
}

/// Resolve an optional building root from free-form and/or structured CLI flags.
///
/// Precedence: free-form `--postal` wins when present; otherwise all structured
/// fields must be provided together. Returns `Ok(None)` when nothing is supplied.
pub fn resolve_building_root_from_options(
    postal: Option<&str>,
    country: Option<&str>,
    region: Option<&str>,
    city: Option<&str>,
    street: Option<&str>,
    number: Option<&str>,
    unit: Option<&str>,
) -> Result<Option<ArxAddress>> {
    if let Some(p) = postal.map(str::trim).filter(|s| !s.is_empty()) {
        return Ok(Some(postal_building_root_from_str(p)?));
    }
    let any_structured = country.is_some()
        || region.is_some()
        || city.is_some()
        || street.is_some()
        || number.is_some()
        || unit.is_some();
    if !any_structured {
        return Ok(None);
    }
    let country = country
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .ok_or_else(|| anyhow!("--country required when using structured postal flags"))?;
    let region = region
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .ok_or_else(|| anyhow!("--region required when using structured postal flags"))?;
    let city = city
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .ok_or_else(|| anyhow!("--city required when using structured postal flags"))?;
    let street = street
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .ok_or_else(|| anyhow!("--street required when using structured postal flags"))?;
    let number = number
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .ok_or_else(|| anyhow!("--number required when using structured postal flags"))?;
    Ok(Some(postal_building_root_fields(
        country,
        region,
        city,
        street,
        number,
        unit.map(str::trim).filter(|s| !s.is_empty()),
    )?))
}

/// Core string only (no leading `/`).
pub fn derive_building_root_from_str(input: &str) -> Result<String> {
    let postal = parse_postal_string(input)?;
    derive_building_root_string(&postal)
}

fn split_number_and_street(line: &str) -> Option<(String, String)> {
    let line = line.trim();
    let mut parts = line.split_whitespace();
    let first = parts.next()?;
    // number may be "143677" or "123-A"
    let number: String = first
        .chars()
        .filter(|c| c.is_ascii_alphanumeric() || *c == '-')
        .collect();
    if number.is_empty() || !number.chars().any(|c| c.is_ascii_digit()) {
        return None;
    }
    let rest: Vec<&str> = parts.collect();
    if rest.is_empty() {
        return None;
    }
    Some((number, rest.join(" ")))
}

fn split_trailing_unit(line: &str) -> Option<(String, String)> {
    let low = line.to_lowercase();
    for key in [" suite ", " ste ", " unit ", " apt ", " apartment "] {
        if let Some(idx) = low.rfind(key) {
            let street = line[..idx].trim().to_string();
            let unit = line[idx..].trim().to_string();
            if !street.is_empty() {
                return Some((street, unit));
            }
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dale_mabry_example() {
        let input = "143677 N. Dale Mabry Hwy, Suite 2, Tampa, FL, 33622";
        let root = derive_building_root_from_str(input).unwrap();
        assert_eq!(root, "bldg.us.fl.tampa.dale-mabry.143677.s2");
        let addr = postal_building_root_from_str(input).unwrap();
        assert_eq!(addr.path, "/bldg.us.fl.tampa.dale-mabry.143677.s2");
    }

    #[test]
    fn without_suite() {
        let input = "100 Main Street, Springfield, IL, 62701";
        let root = derive_building_root_from_str(input).unwrap();
        assert_eq!(root, "bldg.us.il.springfield.main.100");
    }

    #[test]
    fn unit_form() {
        let input = "500 Market Ave, Unit 4, San Francisco, CA 94105";
        // CA 94105 may be one part if no comma before zip
        let postal = parse_postal_string(input).unwrap();
        assert_eq!(normalize_region(&postal.region), "ca");
        let root = derive_building_root_string(&postal).unwrap();
        assert!(root.starts_with("bldg.us.ca.san-francisco.market.500"));
        assert!(root.ends_with(".u4"), "got {}", root);
    }

    #[test]
    fn multi_word_city_and_street() {
        let input = "12 East 42nd Street, New York, NY, 10017";
        let root = derive_building_root_from_str(input).unwrap();
        // drop East directional, drop Street suffix → 42nd
        assert_eq!(root, "bldg.us.ny.new-york.42nd.12");
    }

    #[test]
    fn determinism() {
        let input = "143677 N. Dale Mabry Hwy, Suite 2, Tampa, FL, 33622";
        let a = derive_building_root_from_str(input).unwrap();
        let b = derive_building_root_from_str(input).unwrap();
        assert_eq!(a, b);
        let structured = PostalAddress::new("US", "FL", "Tampa", "N. Dale Mabry Hwy", "143677", Some("Suite 2".into()));
        assert_eq!(derive_building_root_string(&structured).unwrap(), a);
    }

    #[test]
    fn structured_fields_helper() {
        let addr = postal_building_root_fields(
            "us",
            "fl",
            "tampa",
            "Dale Mabry",
            "143677",
            Some("s2"),
        )
        .unwrap();
        assert_eq!(addr.path, "/bldg.us.fl.tampa.dale-mabry.143677.s2");
    }

    #[test]
    fn simplify_street_drops_direction_and_suffix() {
        assert_eq!(simplify_street("N. Dale Mabry Hwy"), "dale-mabry");
        assert_eq!(simplify_street("South Congress Avenue"), "congress");
        assert_eq!(simplify_street("W. Elm Blvd"), "elm");
    }

    #[test]
    fn normalize_unit_forms() {
        assert_eq!(normalize_unit("Suite 2").as_deref(), Some("s2"));
        assert_eq!(normalize_unit("Unit 4").as_deref(), Some("u4"));
        assert_eq!(normalize_unit("#12").as_deref(), Some("u12"));
        assert_eq!(normalize_unit("Apt 3B").as_deref(), Some("a3b"));
    }

    #[test]
    fn incomplete_structured_errors() {
        let p = PostalAddress::new("us", "fl", "tampa", "", "1", None);
        assert!(derive_building_root_string(&p).is_err());
    }
}
