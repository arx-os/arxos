# Cargo Commands
The commands will let you interact with Cargo using its command-line interface.

Frequently Asked Questions

Appendices:

Glossary
Git Authentication
Other Documentation:

Changelog — Detailed notes about changes in Cargo in each release.
Rust documentation website — Links to official Rust documentation and tools.
Getting Started

### cargo install

Installation
First steps with Cargo
Installation

Install Rust and Cargo

The easiest way to get Cargo is to install the current stable release of Rust by using rustup. Installing Rust using rustup will also install cargo.

On Linux and macOS systems, this is done as follows:

curl https://sh.rustup.rs -sSf | sh
It will download a script, and start the installation. If everything goes well, you’ll see this appear:

Rust is installed now. Great!
On Windows, download and run rustup-init.exe. It will start the installation in a console and present the above message on success.

After this, you can use the rustup command to also install beta or nightly channels for Rust and Cargo.

For other installation options and information, visit the install page of the Rust website.

Build and Install Cargo from Source

Alternatively, you can build Cargo from source.

First Steps with Cargo

This section provides a quick sense for the cargo command line tool. We demonstrate its ability to generate a new package for us, its ability to compile the crate within the package, and its ability to run the resulting program.

### cargo new

$ cargo new hello_world
Cargo defaults to --bin to make a binary program. To make a library, we would pass --lib, instead.

### cargo check

$ cd hello_world
$ tree .
.
├── Cargo.toml
└── src
    └── main.rs

1 directory, 2 files
This is all we need to get started. First, let’s check out Cargo.toml:

[package]
name = "hello_world"
version = "0.1.0"
edition = "2024"

[dependencies]
### cargo metadata

Here’s what’s in src/main.rs:

fn main() {
    println!("Hello, world!");
}
Cargo generated a “hello world” program for us, otherwise known as a binary crate. Let’s compile it:

### cargo build
   Compiling hello_world v0.1.0 (file:///path/to/package/hello_world)
And then run it:

$ ./target/debug/hello_world
Hello, world!
### cargo run

$ cargo run
     Fresh hello_world v0.1.0 (file:///path/to/package/hello_world)
   Running `target/hello_world`
Hello, world!
Going further

For more details on using Cargo, check out the Cargo Guide

Cargo Guide

This guide will give you all that you need to know about how to use Cargo to develop Rust packages.

Why Cargo Exists
Creating a New Package
### cargo package
Dependencies
Package Layout
Cargo.toml vs Cargo.lock
Tests
Continuous Integration
Publishing on crates.io
Cargo Home
Why Cargo Exists

Preliminaries

In Rust, as you may know, a library or executable program is called a crate. Crates are compiled using the Rust compiler, rustc. When starting with Rust, the first source code most people encounter is that of the classic “hello world” program, which they compile by invoking rustc directly:

$ rustc hello.rs
$ ./hello
Hello, world!
Note that the above command required that you specify the file name explicitly. If you were to directly use rustc to compile a different program, a different command line invocation would be required. If you needed to specify any specific compiler flags or include external dependencies, then the needed command would be even more specific (and complex).

Furthermore, most non-trivial programs will likely have dependencies on external libraries, and will therefore also depend transitively on their dependencies. Obtaining the correct versions of all the necessary dependencies and keeping them up to date would be hard and error-prone if done by hand.

Rather than work only with crates and rustc, you can avoid the difficulties involved with performing the above tasks by introducing a higher-level “package” abstraction and by using a package manager.

Enter: Cargo

Cargo is the Rust package manager. It is a tool that allows Rust packages to declare their various dependencies and ensure that you’ll always get a repeatable build.

To accomplish this goal, Cargo does four things:

Introduces two metadata files with various bits of package information.
Fetches and builds your package’s dependencies.
Invokes rustc or another build tool with the correct parameters to build your package.
Introduces conventions to make working with Rust packages easier.
### cargo add

It is only a slight exaggeration to say that once you know how to build one Cargo-based project, you know how to build all of them.

Creating a New Package

To start a new package with Cargo, use cargo new:

$ cargo new hello_world --bin
We’re passing --bin because we’re making a binary program: if we were making a library, we’d pass --lib. This also initializes a new git repository by default. If you don’t want it to do that, pass --vcs none.

Let’s check out what Cargo has generated for us:

$ cd hello_world
$ tree .
.
├── Cargo.toml
└── src
    └── main.rs

1 directory, 2 files
Let’s take a closer look at Cargo.toml:

[package]
name = "hello_world"
version = "0.1.0"
edition = "2024"

[dependencies]

This is called a manifest, and it contains all of the metadata that Cargo needs to compile your package. This file is written in the TOML format (pronounced /tɑməl/).

Here’s what’s in src/main.rs:

fn main() {
    println!("Hello, world!");
}
Cargo generated a “hello world” program for you, otherwise known as a binary crate. Let’s compile it:

$ cargo build
   Compiling hello_world v0.1.0 (file:///path/to/package/hello_world)
And then run it:

$ ./target/debug/hello_world
Hello, world!
You can also use cargo run to compile and then run it, all in one step (You won’t see the Compiling line if you have not made any changes since you last compiled):

$ cargo run
   Compiling hello_world v0.1.0 (file:///path/to/package/hello_world)
     Running `target/debug/hello_world`
Hello, world!
### cargo info

Once you’re ready for release, you can use cargo build --release to compile your files with optimizations turned on:

$ cargo build --release
   Compiling hello_world v0.1.0 (file:///path/to/package/hello_world)
cargo build --release puts the resulting binary in target/release instead of target/debug.

Compiling in debug mode is the default for development. Compilation time is shorter since the compiler doesn’t do optimizations, but the code will run slower. Release mode takes longer to compile, but the code will run faster.

Working on an Existing Cargo Package

If you download an existing package that uses Cargo, it’s really easy to get going.

First, get the package from somewhere. In this example, we’ll use regex cloned from its repository on GitHub:

$ git clone https://github.com/rust-lang/regex.git
$ cd regex
To build, use cargo build:

$ cargo build
   Compiling regex v1.5.0 (file:///path/to/package/regex)
This will fetch all of the dependencies and then build them, along with the package.

Dependencies

crates.io is the Rust community’s central package registry that serves as a location to discover and download packages. cargo is configured to use it by default to find requested packages.

To depend on a library hosted on crates.io, add it to your Cargo.toml.

Adding a dependency

### cargo version

[dependencies]
time = "0.1.12"
The version string is a SemVer version requirement. The specifying dependencies docs have more information about the options you have here.

If you also wanted to add a dependency on the regex crate, you would not need to add [dependencies] for each crate listed. Here’s what your whole Cargo.toml file would look like with dependencies on the time and regex crates:

[package]
name = "hello_world"
version = "0.1.0"
edition = "2024"

[dependencies]
time = "0.1.12"
regex = "0.1.41"
Re-run cargo build, and Cargo will fetch the new dependencies and all of their dependencies, compile them all, and update the Cargo.lock:

$ cargo build
      Updating crates.io index
   Downloading memchr v0.1.5
   Downloading libc v0.1.10
   Downloading regex-syntax v0.2.1
   Downloading memchr v0.1.5
   Downloading aho-corasick v0.3.0
   Downloading regex v0.1.41
     Compiling memchr v0.1.5
     Compiling libc v0.1.10
     Compiling regex-syntax v0.2.1
     Compiling memchr v0.1.5
     Compiling aho-corasick v0.3.0
     Compiling regex v0.1.41
     Compiling hello_world v0.1.0 (file:///path/to/package/hello_world)
Cargo.lock contains the exact information about which revision was used for all of these dependencies.

### cargo update

You can now use the regex library in main.rs.

use regex::Regex;

fn main() {
    let re = Regex::new(r"^\d{4}-\d{2}-\d{2}$").unwrap();
    println!("Did our date match? {}", re.is_match("2014-01-01"));
}
Running it will show:

$ cargo run
   Running `target/hello_world`
Did our date match? true
Package Layout

Cargo uses conventions for file placement to make it easy to dive into a new Cargo package:

.
├── Cargo.lock
├── Cargo.toml
├── src/
│   ├── lib.rs
│   ├── main.rs
│   └── bin/
│       ├── named-executable.rs
│       ├── another-executable.rs
│       └── multi-file-executable/
│           ├── main.rs
│           └── some_module.rs
├── benches/
│   ├── large-input.rs
│   └── multi-file-bench/
│       ├── main.rs
│       └── bench_module.rs
├── examples/
│   ├── simple.rs
│   └── multi-file-example/
│       ├── main.rs
│       └── ex_module.rs
└── tests/
    ├── some-integration-tests.rs
    └── multi-file-test/
        ├── main.rs
        └── test_module.rs
Cargo.toml and Cargo.lock are stored in the root of your package (package root).
Source code goes in the src directory.
The default library file is src/lib.rs.
The default executable file is src/main.rs.
Other executables can be placed in src/bin/.
Benchmarks go in the benches directory.
Examples go in the examples directory.
Integration tests go in the tests directory.
If a binary, example, bench, or integration test consists of multiple source files, place a main.rs file along with the extra modules within a subdirectory of the src/bin, examples, benches, or tests directory. The name of the executable will be the directory name.

Note: By convention, binaries, examples, benches and integration tests follow kebab-case naming style, unless there are compatibility reasons to do otherwise (e.g. compatibility with a pre-existing binary name). Modules within those targets are snake_case following the Rust standard.

You can learn more about Rust’s module system in the book.

See Configuring a target for more details on manually configuring targets. See Target auto-discovery for more information on controlling how Cargo automatically infers target names.

Cargo.toml vs Cargo.lock

Cargo.toml and Cargo.lock serve two different purposes. Before we talk about them, here’s a summary:

Cargo.toml is about describing your dependencies in a broad sense, and is written by you.
Cargo.lock contains exact information about your dependencies. It is maintained by Cargo and should not be manually edited.
