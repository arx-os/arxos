# Introduction

Welcome to The Rust Edition Guide! "Editions" are Rust's way of introducing changes into the language that would not otherwise be backwards compatible.

In this guide, we'll discuss:

What editions are
Which changes are contained in each edition
How to migrate your code from one edition to another

## What are Editions?

In May 2015, the release of Rust 1.0 established "stability without stagnation" as a core Rust axiom. Since then, Rust has committed to a pivotal rule: once a feature is released through stable, contributors will continue to support that feature for all future releases.

However, there are times when it's useful to make backwards-incompatible changes to the language. A common example is the introduction of a new keyword. For instance, early versions of Rust didn't feature the async and await keywords.

If Rust had suddenly introduced these new keywords, some code would have broken: let async = 1; would no longer work.

Rust uses editions to solve this problem. When there are backwards-incompatible changes, they are pushed into the next edition. Since editions are opt-in, existing crates won't use the changes unless they explicitly migrate into the new edition. For example, the latest version of Rust doesn't treat async as a keyword unless edition 2018 or later is chosen.

Each crate chooses its edition within its Cargo.toml file. When creating a new crate with Cargo, it will automatically select the newest stable edition.

## Editions do not split the ecosystem

When creating editions, there is one most consequential rule: crates in one edition must seamlessly interoperate with those compiled with other editions.

In other words, each crate can decide when to migrate to a new edition independently. This decision is 'private' - it won't affect other crates in the ecosystem.

For Rust, this required compatibility implies some limits on the kinds of changes that can be featured in an edition. As a result, changes found in new Rust editions tend to be 'skin deep'. All Rust code - regardless of edition - will ultimately compile down to the same internal representation within the compiler.

## Edition migration is easy and largely automated

Rust aims to make upgrading to a new edition an easy process. When a new edition releases, crate authors may use automatic migration tooling within cargo to migrate. Cargo will then make minor changes to the code to make it compatible with the new version.

For example, when migrating to Rust 2018, anything named async will now use the equivalent raw identifier syntax: r#async.

Cargo's automatic migrations aren't perfect: there may still be corner cases where manual changes are required. It aims to avoid changes to semantics that could affect the correctness or performance of the code.

## What this guide covers

In addition to tooling, this Rust Edition Guide also covers the changes that are part of each edition. It describes each change and links to additional details, if available. It also covers corner cases or tricky details crate authors should be aware of.

Crate authors should find:

An overview of editions
A migration guide for specific editions
A quick troubleshooting reference when automated tooling isn't working.

## Creating a new project

A new project created with Cargo is configured to use the latest edition by default:

$ cargo new foo
    Creating binary (application) `foo` package
note: see more `Cargo.toml` keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html
$ cat foo/Cargo.toml
[package]
name = "foo"
version = "0.1.0"
edition = "2024"

[dependencies]
That edition = "2024" setting configures your package to be built using the Rust 2024 edition. No further configuration needed!

You can use the --edition <YEAR> option of cargo new to create the project using some specific edition. For example, creating a new project to use the Rust 2018 edition could be done like this:

$ cargo new --edition 2018 foo
    Creating binary (application) `foo` package
note: see more `Cargo.toml` keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html
$ cat foo/Cargo.toml
[package]
name = "foo"
version = "0.1.0"
edition = "2018"

[dependencies]
Don't worry about accidentally using an invalid year for the edition; the cargo new invocation will not accept an invalid edition year value:

$ cargo new --edition 2019 foo
error: invalid value '2019' for '--edition <YEAR>'
  [possible values: 2015, 2018, 2021, 2024]

  tip: a similar value exists: '2021'

For more information, try '--help'.
You can change the value of the edition key by simply editing the Cargo.toml file. For example, to cause your package to be built using the Rust 2015 edition, you would set the key as in the following example:

[package]
name = "foo"
version = "0.1.0"
edition = "2015"

## [dependencies]
