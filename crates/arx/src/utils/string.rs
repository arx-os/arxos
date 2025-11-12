//! String utility helpers used across ArxOS.
//!
//! Provides canonicalisation helpers for labels and slugs so that the same
//! normalization logic is shared between the IFC import pipeline, YAML export,
//! and CLI surfaces that rely on deterministic identifiers.

/// Normalise a human readable label by trimming quotes and surrounding
/// whitespace.
///
/// IFC entities frequently wrap names in single quotes. This helper removes the
/// quotes and leading/trailing whitespace while leaving the interior intact.
///
/// Returns an empty string if the input contains no meaningful characters.
pub fn normalize_label(raw: &str) -> String {
    let trimmed = raw.trim().trim_matches('\'').trim_matches('"').trim();
    if trimmed.is_empty() {
        String::new()
    } else {
        trimmed.to_string()
    }
}

/// Convert arbitrary text into a lowercase slug suitable for filenames and path
/// segments.
///
/// * Non alphanumeric characters are replaced with single hyphens.
/// * Consecutive separators are collapsed.
/// * Leading/trailing separators are removed.
pub fn slugify(input: &str) -> String {
    let mut slug = String::with_capacity(input.len());
    let mut last_was_separator = false;

    for ch in input.chars() {
        let lower = ch.to_ascii_lowercase();
        if lower.is_ascii_alphanumeric() {
            slug.push(lower);
            last_was_separator = false;
        } else if !slug.is_empty() {
            if !last_was_separator {
                slug.push('-');
                last_was_separator = true;
            }
        }
    }

    // Trim any trailing separator that may have been appended.
    while slug.ends_with('-') {
        slug.pop();
    }

    slug
}

#[cfg(test)]
mod tests {
    use super::{normalize_label, slugify};

    #[test]
    fn normalize_label_strips_quotes_and_whitespace() {
        assert_eq!(normalize_label("' Building 01 '"), "Building 01");
        assert_eq!(normalize_label("\"Main Tower\""), "Main Tower");
        assert_eq!(normalize_label("   "), "");
    }

    #[test]
    fn slugify_replaces_non_alphanumeric() {
        assert_eq!(slugify("Main Tower West"), "main-tower-west");
        assert_eq!(slugify("Building #42"), "building-42");
        assert_eq!(slugify("__Already--Slug__"), "already-slug");
    }

    #[test]
    fn slugify_handles_empty_string() {
        assert_eq!(slugify(""), "");
        assert_eq!(slugify("!!!"), "");
    }
}

