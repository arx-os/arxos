# Compiler environment variables
## COLORTERM

This environment variable is used by -Zterminal-urls to detect if URLs are supported by the terminal emulator.

## QNX_TARGET

This environment variable is mandatory when linking on nto-qnx*_iosock platforms. It is used to determine an -L path to pass to the QNX linker.

You should set this variable by running source qnxsdp-env.sh. See the QNX docs for more background information.

## RUSTC_BLESS

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUSTC_BOOTSTRAP

This feature is perma-unstable and has no tracking issue.

The RUSTC_BOOTSTRAP environment variable tells rustc to act as if it is a nightly compiler; in particular, it allows #![feature(...)] attributes and -Z flags even on the stable release channel.

Setting RUSTC_BOOTSTRAP=1 instructs rustc to enable this for all crates. Setting RUSTC_BOOTSTRAP=crate_name instructs rustc to only apply this to crates named crate_name. Setting RUSTC_BOOTSTRAP=-1 instructs rustc to act as if it is a stable compiler, even on the nightly release channel. Cargo disallows setting cargo::rustc-env=RUSTC_BOOTSTRAP in build scripts. Build systems can limit the features they enable with -Z allow-features=feature1,feature2. Crates can fully opt out of unstable features by using #![forbid(unstable_features)] at the crate root (or any other way of enabling lints, such as -F unstable-features).

Why does this environment variable exist?

RUSTC_BOOTSTRAP, as the name suggests, is used for bootstrapping the compiler from an earlier version. In particular, nightly is built with beta, and beta is built with stable. Since the standard library and compiler both use unstable features, RUSTC_BOOTSTRAP is required so that we can use the previous version to build them.

Why is this environment variable so easy to use for people not in the Rust project?

Originally, RUSTC_BOOTSTRAP required passing in a hash of the previous compiler version, to discourage using it for any purpose other than bootstrapping. That constraint was later relaxed; see https://github.com/rust-lang/rust/issues/36548 for the discussion that happened at that time.

People have at various times proposed re-adding the technical constraints. However, doing so is extremely disruptive for several major projects that we very much want to keep using the latest stable toolchain version, such as Firefox, Rust for Linux, and Chromium. We continue to allow RUSTC_BOOTSTRAP until we can come up with an alternative that does not disrupt our largest constituents.

Stability policy

Despite being usable on stable, this is an unstable feature. Like any other unstable feature, we reserve the right to change or remove this feature in the future, as well as any other unstable feature that it enables. Using this feature opts you out of the normal stability/backwards compatibility guarantee of stable.

Although we do not take technical measures to prevent it from being used, we strongly discourage using this feature. If at all possible, please contribute to stabilizing the features you care about instead of bypassing the Rust project's stability policy.

For library crates, we especially discourage the use of this feature. The crates depending on you do not know that you use this feature, have little recourse if it breaks, and can be used in contexts that are hard to predict.

For libraries that do use this feature, please document the versions you support (including a maximum as well as minimum version), and a mechanism to disable it. If you do not have a mechanism to disable the use of RUSTC_BOOTSTRAP, consider removing its use altogether, such that people can only use your library if they are already using a nightly toolchain. This leaves the choice of whether to opt-out of Rust's stability guarantees up to the end user building their code.

History

Allowed without a hash (discussion)
Extended to crate names (discussion)
Disallowed for build scripts (discussion)
Extended to emulate stable (discussion)
## RUSTC_BREAK_ON_ICE

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUSTC_CTFE_BACKTRACE

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUSTC_FORCE_RUSTC_VERSION

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUSTC_GRAPHVIZ_FONT

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUSTC_ICE

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUSTC_LOG

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUSTC_OVERRIDE_VERSION_STRING

This feature is perma-unstable and has no tracking issue.

The RUSTC_OVERRIDE_VERSION_STRING environment variable overrides the version reported by rustc --version. For example:

$ rustc --version
rustc 1.87.0-nightly (43f0014ef 2025-03-25)
$ env RUSTC_OVERRIDE_VERSION_STRING=1.81.0-nightly rustc --version
rustc 1.81.0-nightly
Note that the version string is completely overwritten; i.e. rustc discards commit hash and commit date information unless it is explicitly included in the environment variable. The string only applies to the "release" part of the version; for example:

$ RUSTC_OVERRIDE_VERSION_STRING="1.81.0-nightly (aaaaaaaaa 2025-03-22)" rustc -vV
rustc 1.81.0-nightly (aaaaaaaaa 2025-03-22)
binary: rustc
commit-hash: 43f0014ef0f242418674f49052ed39b70f73bc1c
commit-date: 2025-03-25
host: x86_64-unknown-linux-gnu
release: 1.81.0-nightly (aaaaaaaaa 2025-03-22)
LLVM version: 20.1.1
Note here that commit-hash and commit-date do not match the values in the string, and release includes the fake hash and date.

This variable has no effect on whether or not unstable features are allowed to be used. It only affects the output of --version.

Why does this environment variable exist?

Various library crates have incomplete or incorrect feature detection. This environment variable allows bisecting crates that do incorrect detection with version_check::supports_feature.

This is not intended to be used for any other case (and, except for bisection, is not particularly useful).

See https://github.com/rust-lang/rust/pull/124339 for further discussion.

## RUSTC_TRANSLATION_NO_DEBUG_ASSERT

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUSTC_WINDOWS_RC

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUST_BACKTRACE

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUST_DEP_GRAPH

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUST_DEP_GRAPH_FILTER

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUST_FORBID_DEP_GRAPH_EDGE

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUST_MIN_STACK

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## RUST_TARGET_PATH

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## SDKROOT

This environment variable is used on Apple targets. It is passed through to the linker (currently either directly or via the -syslibroot flag).

Note that this variable is not always respected. When the SDKROOT is clearly wrong (e.g. when the platform of the SDK does not match the --target used by rustc), this is ignored and rustc does its own detection.

## TERM

This environment variable is used by -Zterminal-urls to detect if URLs are supported by the terminal emulator.

## UNSTABLE_RUSTDOC_TEST_LINE

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.

## UNSTABLE_RUSTDOC_TEST_PATH

Environment variables have no tracking issue. This environment variable has no documentation, and therefore is likely internal to the compiler and not meant for general use.

See the code for more information.
