//! Shared private-key resolution for blockchain CLI paths.
//!
//! Lab scripts may use the public Anvil account #0 key **only** when explicitly
//! opted in. Silent fallback is forbidden — it is a footgun on any non-local chain.

/// Foundry / Anvil default account #0 private key (public knowledge — lab only).
pub const ANVIL_ACCOUNT0_KEY: &str =
    "ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";

/// Resolve the Anvil lab default only when `ARX_ALLOW_ANVIL_DEFAULT_KEY=1`.
///
/// Callers must already have checked CLI args and `ARX_PRIVATE_KEY`.
pub fn resolve_anvil_lab_default() -> Result<String, Box<dyn std::error::Error>> {
    let allow = std::env::var("ARX_ALLOW_ANVIL_DEFAULT_KEY")
        .map(|v| v == "1" || v.eq_ignore_ascii_case("true"))
        .unwrap_or(false);
    if allow {
        eprintln!(
            "⚠️  Using Anvil account #0 private key (ARX_ALLOW_ANVIL_DEFAULT_KEY). \
             Lab/local only — never fund this key on a public network."
        );
        return Ok(ANVIL_ACCOUNT0_KEY.into());
    }
    Err(
        "No signing key: set ARX_PRIVATE_KEY, pass --private-key / key flag, \
         or for local Anvil only set ARX_ALLOW_ANVIL_DEFAULT_KEY=1 \
         (public Anvil account #0 — never use on mainnet/testnet with real funds)."
            .into(),
    )
}


#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    static ENV_LOCK: Mutex<()> = Mutex::new(());

    #[test]
    fn anvil_default_requires_explicit_opt_in() {
        let _g = ENV_LOCK.lock().unwrap();
        std::env::remove_var("ARX_ALLOW_ANVIL_DEFAULT_KEY");
        let err = resolve_anvil_lab_default().unwrap_err().to_string();
        assert!(
            err.contains("ARX_PRIVATE_KEY") || err.contains("ARX_ALLOW_ANVIL"),
            "unexpected err: {err}"
        );

        std::env::set_var("ARX_ALLOW_ANVIL_DEFAULT_KEY", "1");
        let key = resolve_anvil_lab_default().expect("opt-in should allow anvil default");
        assert_eq!(key, ANVIL_ACCOUNT0_KEY);
        std::env::remove_var("ARX_ALLOW_ANVIL_DEFAULT_KEY");
    }
}
