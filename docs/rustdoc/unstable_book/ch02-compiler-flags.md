# Compiler flags
allow-features

This feature is perma-unstable and has no tracking issue.

This flag allows limiting the features which can be enabled with #![feature(...)] attributes. By default, all features are allowed on nightly and no features are allowed on stable or beta (but see RUSTC_BOOTSTRAP).

Features are comma-separated, for example -Z allow-features=ffi_pure,f16. If the flag is present, any feature listed will be allowed and any feature not listed will be disallowed. Any unrecognized feature is ignored.

annotate-moves

The tracking issue for this feature is: #148197.

The -Z annotate-moves flag enables annotation of compiler-generated move and copy operations, making them visible in profilers and stack traces for performance debugging.

When enabled, the compiler manipulates debug info to make large move and copy operations appear as if they were inlined calls to core::profiling::compiler_move and core::profiling::compiler_copy. No actual function calls are generated - this is purely a debug info transformation that makes expensive memory operations visible in profilers and stack traces.

Syntax

rustc -Z annotate-moves[=<value>]
Where <value> can be:

A boolean: true, false, yes, no, on, off
A number: size threshold in bytes (e.g., 128)
Omitted: enables with default threshold (65 bytes)
Options

-Z annotate-moves or -Z annotate-moves=true: Enable with default size limit
-Z annotate-moves=false: Disable annotation
-Z annotate-moves=N: Enable with custom size limit of N bytes
Examples

# Enable annotation with default threshold (65 bytes)
rustc -Z annotate-moves main.rs

# Enable with custom 128-byte threshold
rustc -Z annotate-moves=128 main.rs

# Only annotate very large moves (1KB+)
rustc -Z annotate-moves=1024 main.rs

# Explicitly disable
rustc -Z annotate-moves=false main.rs
Behavior

The annotation only applies to:

Types equal or larger than the specified size threshold
Non-immediate types (those that would generate memcpy)
Operations that actually move/copy data (not ZST types)
Stack traces will show the operations:

0: memcpy
1: core::profiling::compiler_move::<MyLargeStruct, 148>
2: my_function
The compiler_move and compiler_copy functions have two generic parameters: the type being moved/copied and its size in bytes. The size is identical to size_of::<T>(), and is present just so that it's easy to immediately tell how large the copy is.

Note that this requires v0 mangling to be properly encoded; legacy mangling does not substitute these with a specific type and size.

Example

#[derive(Clone)]
struct LargeData {
    buffer: [u8; 1000],
}

fn example() {
    let data = LargeData { buffer: [0; 1000] };
    let copy = data.clone(); // Shows as compiler_copy in profiler
    let moved = data;        // Shows as compiler_move in profiler
}
Overhead

This has no effect on generated code; it only adds debuginfo. The overhead is typically very small; on rustc itself, the default limit of 65 bytes adds about 0.055% to the binary size.

## autodiff

The tracking issue for this feature is: #124509.

This feature allows you to differentiate functions using automatic differentiation. Set the -Zautodiff=<options> compiler flag to adjust the behaviour of the autodiff feature. Multiple options can be separated with a comma. Valid options are:

Enable - Required flag to enable autodiff PrintTA - print Type Analysis Information PrintTAFn - print Type Analysis Information for a specific function PrintAA - print Activity Analysis Information PrintPerf - print Performance Warnings from Enzyme PrintSteps - prints all intermediate transformations PrintModBefore - print the whole module, before running opts PrintModAfter - print the module after Enzyme differentiated everything LooseTypes - Enzyme's loose type debug helper (can cause incorrect gradients) Inline - runs Enzyme specific Inlining RuntimeActivity - allow specifying activity at runtime

branch-protection

The tracking issue for this feature is: #113369.

This option lets you enable branch authentication instructions on AArch64. This option is only accepted when targeting AArch64 architectures. It takes some combination of the following values, separated by a ,.

pac-ret - Enable pointer authentication for non-leaf functions.
pc - Use PC as a diversifier using PAuthLR instructions
leaf - Enable pointer authentication for all functions, including leaf functions.
b-key - Sign return addresses with key B, instead of the default key A.
bti - Enable branch target identification.
gcs - Enable guarded control stack support.
leaf, b-key and pc are only valid if pac-ret was previously specified. For example, -Z branch-protection=bti,pac-ret,leaf is valid, but -Z branch-protection=bti,leaf,pac-ret is not.

Rust's standard library does not ship with BTI or pointer authentication enabled by default. In Cargo projects the standard library can be recompiled with pointer authentication using the nightly build-std feature.

cf-protection

The tracking issue for this feature is: #93754.

This option enables control-flow enforcement technology (CET) on x86; a more detailed description of CET is available here. Similar to clang, this flag takes one of the following values:

none - Disable CET completely (this is the default).
branch - Enable indirect branch tracking (IBT).
return - Enable shadow stack (SHSTK).
full - Enable both branch and return.
This flag only applies to the LLVM backend: it sets the cf-protection-branch and cf-protection-return flags on LLVM modules. Note, however, that all compiled modules linked together must have the flags set for the compiled output to be CET-enabled. Currently, Rust's standard library does not ship with CET enabled by default, so you may need to rebuild all standard modules with a cargo command like:

$ RUSTFLAGS="-Z cf-protection=full" cargo +nightly build -Z build-std --target x86_64-unknown-linux-gnu
Detection

An ELF binary is CET-enabled if it has the IBT and SHSTK tags, e.g.:

$ readelf -a target/x86_64-unknown-linux-gnu/debug/example | grep feature:
      Properties: x86 feature: IBT, SHSTK
Troubleshooting

To display modules that are not CET enabled, examine the linker errors available when cet-report is enabled:

$ RUSTC_LOG=rustc_codegen_ssa::back::link=info rustc-custom -v -Z cf-protection=full -C link-arg="-Wl,-z,cet-report=warning" -o example example.rs
...
/usr/bin/ld: /.../build/x86_64-unknown-linux-gnu/stage1/lib/rustlib/x86_64-unknown-linux-gnu/lib/libstd-d73f7266be14cb8b.rlib(std-d73f7266be14cb8b.std.f7443020-cgu.12.rcgu.o): warning: missing IBT and SHSTK properties
codegen-backend

The tracking issue for this feature is: #77933.

This feature allows you to specify a path to a dynamic library to use as rustc's code generation backend at runtime.

## codegen_backend

Example

See also the codegen-backend/hotplug test for a working example.

use rustc_codegen_ssa::traits::CodegenBackend;

struct MyBackend;

impl CodegenBackend for MyBackend {
   // Implement codegen methods
}

#[no_mangle]
pub fn __rustc_codegen_backend() -> Box<dyn CodegenBackend> {
    Box::new(MyBackend)
}
Unstable codegen options

All of these options are passed to rustc via the -C flag, short for "codegen". The flags are stable but some of their values are individually unstable, and also require using -Z unstable-options to be accepted.

linker-flavor

In addition to the stable set of linker flavors, the following unstable values also exist:

ptx: use rust-ptx-linker for Nvidia NVPTX GPGPU support.
bpf: use bpf-linker for eBPF support.
llbc: for linking in llvm bitcode. Install the preview rustup componentsllvm-bitcode-linker and llvm-tools to use as a self-contained linker by passing -Zunstable-options -Clink-self-contained=+linker together with -Clinker-flavor=llbc. Can currently only be used for Nvidia NVPTX targets (nvptx64-nvidia-cuda).
Additionally, a set of more precise linker flavors also exists, for example allowing targets to declare that they use the LLD linker by default. The following values are currently unstable, and the goal is for them to become stable, and preferred in practice over the existing stable values:

gnu: unix-like linker with GNU extensions
gnu-lld: gnu using LLD
gnu-cc: gnu using a C/C++ compiler as the linker driver
gnu-lld-cc: gnu using LLD and a C/C++ compiler as the linker driver
darwin: unix-like linker for Apple targets
darwin-lld: darwin using LLD
darwin-cc: darwin using a C/C++ compiler as the linker driver
darwin-lld-cc: darwin using LLD and a C/C++ compiler as the linker driver
wasm-lld: unix-like linker for Wasm targets, with LLD
wasm-lld-cc: unix-like linker for Wasm targets, with LLD and a C/C++ compiler as the linker driver
unix: basic unix-like linker for "any other Unix" targets (Solaris/illumos, L4Re, MSP430, etc), not supported with LLD.
unix-cc: unix using a C/C++ compiler as the linker driver
msvc-lld: MSVC-style linker for Windows and UEFI, with LLD
em-cc: emscripten compiler frontend, similar to wasm-lld-cc with a different interface
link-self-contained

This flag generally controls whether the linker will use libraries and objects shipped with Rust instead of those in the system. The stable boolean values for this flag are coarse-grained (everything or nothing), but there exists a set of unstable values with finer-grained control, -Clink-self-contained can accept a comma-separated list of components, individually enabled (+component) or disabled (-component):

crto: CRT objects (e.g. on windows-gnu, musl, wasi targets)
libc: libc static library (e.g. on musl, wasi targets)
unwind: libgcc/libunwind (e.g. on windows-gnu, fuchsia, fortanix, gnullvm targets)
linker: linker, dlltool, and their necessary libraries (e.g. on windows-gnu and for rust-lld)
sanitizers: sanitizer runtime libraries
mingw: other MinGW libs and Windows import libs
Out of the above self-contained linking components, linker is the only one currently implemented (beyond parsing the CLI options) and stabilized.

It refers to the LLD linker, built from the same LLVM revision used by rustc (named rust-lld to avoid naming conflicts), that is distributed via rustup with the compiler (and is used by default for the wasm targets). One can also opt into using it by combining this flag with the appropriate linker feature: for example, -Clinker-features=+lld -Clink-self-contained=+linker will use the toolchain's rust-lld as the linker instead of the system's lld with -Clinker-features=+lld only.

codegen-source-order

This feature allows you to have a predictive and deterministic order for items after codegen, which is the same as in source code.

For every CodegenUnit, local MonoItems would be sorted by (Span, SymbolName), which makes codegen tests rely on the order of items in source files work.

control-flow-guard

The tracking issue for this feature is: #68793.

The rustc flag -Z control-flow-guard enables the Windows Control Flow Guard (CFG) platform security feature.

CFG is an exploit mitigation designed to enforce control-flow integrity for software running on supported Windows platforms (Windows 8.1 onwards). Specifically, CFG uses runtime checks to validate the target address of every indirect call/jump before allowing the call to complete.

During compilation, the compiler identifies all indirect calls/jumps and adds CFG checks. It also emits metadata containing the relative addresses of all address-taken functions. At runtime, if the binary is run on a CFG-aware operating system, the loader uses the CFG metadata to generate a bitmap of the address space and marks those addresses that contain valid targets. On each indirect call, the inserted check determines whether the target address is marked in this bitmap. If the target is not valid, the process is terminated.

In terms of interoperability:

Code compiled with CFG enabled can be linked with libraries and object files that are not compiled with CFG. In this case, a CFG-aware linker can identify address-taken functions in the non-CFG libraries.
Libraries compiled with CFG can linked into non-CFG programs. In this case, the CFG runtime checks in the libraries are not used (i.e. the mitigation is completely disabled).
CFG functionality is completely implemented in the LLVM backend and is supported for X86 (32-bit and 64-bit), ARM, and Aarch64 targets. The rustc flag adds the relevant LLVM module flags to enable the feature. This flag will be ignored for all non-Windows targets.

When to use Control Flow Guard

The primary motivation for enabling CFG in Rust is to enhance security when linking against non-Rust code, especially C/C++ code. To achieve full CFG protection, all indirect calls (including any from Rust code) must have the appropriate CFG checks, as added by this flag. CFG can also improve security for Rust code that uses the unsafe keyword.

Another motivation behind CFG is to harden programs against return-oriented programming (ROP) attacks. CFG disallows an attacker from taking advantage of the program's own instructions while redirecting control flow in unexpected ways.

Overhead of Control Flow Guard

The CFG checks and metadata can potentially increase binary size and runtime overhead. The magnitude of any increase depends on the number and frequency of indirect calls. For example, enabling CFG for the Rust standard library increases binary size by approximately 0.14%. Enabling CFG in the SPEC CPU 2017 Integer Speed benchmark suite (compiled with Clang/LLVM) incurs approximate runtime overheads of between 0% and 8%, with a geometric mean of 2.9%.

Testing Control Flow Guard

The rustc flag -Z control-flow-guard=nochecks instructs LLVM to emit the list of valid call targets without inserting runtime checks. This flag should only be used for testing purposes as it does not provide security enforcement.

Control Flow Guard in libraries

It is strongly recommended to also enable CFG checks for all linked libraries, including the standard library.

To enable CFG in the standard library, use the cargo -Z build-std functionality to recompile the standard library with the same configuration options as the main program.

For example:

rustup toolchain install --force nightly
rustup component add rust-src
SET RUSTFLAGS=-Z control-flow-guard
cargo +nightly build -Z build-std --target x86_64-pc-windows-msvc
rustup toolchain install --force nightly
rustup component add rust-src
$Env:RUSTFLAGS = "-Z control-flow-guard"
cargo +nightly build -Z build-std --target x86_64-pc-windows-msvc
Alternatively, if you are building the standard library from source, you can set control-flow-guard = true in the bootstrap.toml file.

coverage-options

This option controls details of the coverage instrumentation performed by -C instrument-coverage.

Multiple options can be passed, separated by commas. Valid options are:

block, branch, condition: Sets the level of coverage instrumentation. Setting the level will override any previously-specified level.
block (default): Blocks in the control-flow graph will be instrumented for coverage.
branch: In addition to block coverage, also enables branch coverage instrumentation.
condition: In addition to branch coverage, also instruments some boolean expressions as branches, even if they are not directly used as branch conditions.
crate-attr

The tracking issue for this feature is: #138287.

The -Z crate-attr flag allows you to inject attributes into the crate root. For example, -Z crate-attr=crate_name="test" acts as if #![crate_name="test"] were present before the first source line of the crate root.

To inject multiple attributes, pass -Z crate-attr multiple times.

Formally, the expansion behaves as follows:

The crate is parsed as if -Z crate-attr were not present.
The attributes in -Z crate-attr are parsed.
The attributes are injected at the top of the crate root.
Macro expansion is performed.
debug-info-for-profiling

Introduction

Automatic Feedback Directed Optimization (AFDO) is a method for using sampling based profiles to guide optimizations. This is contrasted with other methods of FDO or profile-guided optimization (PGO) which use instrumented profiling.

Unlike PGO (controlled by the rustc flags -Cprofile-generate and -Cprofile-use), a binary being profiled does not perform significantly worse, and thus it's possible to profile binaries used in real workflows and not necessary to construct artificial workflows.

Use

In order to use AFDO, the target platform must be Linux running on an x86_64 architecture with the performance profiler perf available. In addition, the external tool create_llvm_prof from this repository must be used.

Given a Rust file main.rs, we can produce an optimized binary as follows:

rustc -O -Zdebug-info-for-profiling main.rs -o main
perf record -b ./main
create_llvm_prof --binary=main --out=code.prof
rustc -O -Zprofile-sample-use=code.prof main.rs -o main2
The perf command produces a profile perf.data, which is then used by the create_llvm_prof command to create code.prof. This final profile is then used by rustc to guide optimizations in producing the binary main2.

debug-info-type-line-numbers

This option causes additional type and line information to be emitted in debug info to provide richer information to debuggers. This is currently off by default as it causes some compilation scenarios to be noticeably slower.

default-visibility

The tracking issue for this feature is: https://github.com/rust-lang/rust/issues/131090

## default_visibility

This option only affects building of shared objects and should have no effect on executables.

Visibility an be set to one of three options:

protected
hidden
interposable
Hidden visibility

Using -Zdefault-visibility=hidden is roughly equivalent to Clang's -fvisibility=hidden cmdline flag. Hidden symbols will not be exported from the created shared object, so cannot be referenced from other shared objects or from executables.

Protected visibility

Using -Zdefault-visibility=protected will cause rust-mangled symbols to be emitted with "protected" visibility. This signals the compiler, the linker and the runtime linker that these symbols cannot be overridden by the executable or by other shared objects earlier in the load order.

This will allow the compiler to emit direct references to symbols, which may improve performance. It also removes the need for these symbols to be resolved when a shared object built with this option is loaded.

Using protected visibility when linking with GNU ld prior to 2.40 will result in linker errors when building for Linux. Other linkers such as LLD are not affected.

Interposable

Using -Zdefault-visibility=interposable will cause symbols to be emitted with "default" visibility. On platforms that support it, this makes it so that symbols can be interposed, which means that they can be overridden by symbols with the same name from the executable or by other shared objects earier in the load order.

## direct_access_external_data

The tracking issue for this feature is: https://github.com/rust-lang/compiler-team/issues/707

Option -Z direct-access-external-data controls how to access symbols of external data.

Supported values for this option are:

yes - Don't use GOT indirection to reference external data symbols.
no - Use GOT indirection to reference external data symbols.
If the option is not explicitly specified, different targets have different default values.

dump-mono-stats

The -Z dump-mono-stats compiler flag generates a file with a list of the monomorphized items in the current crate. It is useful for investigating compile times.

It accepts an optional directory where the file will be located. If no directory is specified, the file will be placed in the current directory.

See also -Z dump-mono-stats-format and -Z print-mono-items. Unlike print-mono-items, dump-mono-stats aggregates monomorphized items by definition and includes a size estimate of how large the item is when codegened.

See https://rustc-dev-guide.rust-lang.org/backend/monomorph.html for an overview of monomorphized items.

dump-mono-stats-format

The -Z dump-mono-stats-format compiler flag controls what file format to use for -Z dump-mono-stats. The default is markdown; currently JSON is also supported. JSON can be useful for programmatically manipulating the results (e.g. to find the item that took the longest to compile).

dylib-lto

This option enables using LTO for the dylib crate type. This is currently only used for compiling rustc itself (more specifically, the librustc_driver dylib).

eagerly-emit-delayed-bugs

This feature is perma-unstable and has no tracking issue.

This flag converts all span_delayed_bug() calls to bug! calls, exiting the compiler immediately and allowing you to generate a backtrace of where the delayed bug occurred. For full documentation, see the rustc-dev-guide.

embed-metadata

This option instructs rustc to include the full metadata in rlib and dylib crate types. The default value is yes (enabled). If disabled (no), only stub metadata will be stored in these files, to reduce their size on disk. When using -Zembed-metadata=no, you will probably want to use --emit=metadata to produce the full metadata into a separate .rmeta file.

embed-source

This flag controls whether the compiler embeds the program source code text into the object debug information section. It takes one of the following values:

y, yes, on or true: put source code in debug info.
n, no, off, false or no value: omit source code from debug info (the default).
This flag is ignored in configurations that don't emit DWARF debug information and is ignored on non-LLVM backends. -Z embed-source requires DWARFv5. Use -Z dwarf-version=5 to control the compiler's DWARF target version and -g to enable debug info generation.

emit-stack-sizes

The tracking issue for this feature is: #54192

The rustc flag -Z emit-stack-sizes makes LLVM emit stack size metadata.

NOTE: This LLVM feature only supports the ELF object format as of LLVM 8.0. Using this flag with targets that use other object formats (e.g. macOS and Windows) will result in it being ignored.

Consider this crate:

#![crate_type = "lib"]

use std::ptr;

pub fn foo() {
    // this function doesn't use the stack
}

pub fn bar() {
    let xs = [0u32; 2];

    // force LLVM to allocate `xs` on the stack
    unsafe { ptr::read_volatile(&xs.as_ptr()); }
}
Using the -Z emit-stack-sizes flag produces extra linker sections in the output object file.

$ rustc -C opt-level=3 --emit=obj foo.rs

$ size -A foo.o
foo.o  :
section                                 size   addr
.text                                      0      0
.text._ZN3foo3foo17he211d7b4a3a0c16eE      1      0
.text._ZN3foo3bar17h1acb594305f70c2eE     22      0
.note.GNU-stack                            0      0
.eh_frame                                 72      0
Total                                     95

$ rustc -C opt-level=3 --emit=obj -Z emit-stack-sizes foo.rs

$ size -A foo.o
foo.o  :
section                                 size   addr
.text                                      0      0
.text._ZN3foo3foo17he211d7b4a3a0c16eE      1      0
.stack_sizes                               9      0
.text._ZN3foo3bar17h1acb594305f70c2eE     22      0
.stack_sizes                               9      0
.note.GNU-stack                            0      0
.eh_frame                                 72      0
Total                                    113
As of LLVM 7.0 the data will be written into a section named .stack_sizes and the format is "an array of pairs of function symbol values (pointer size) and stack sizes (unsigned LEB128)".

$ objdump -d foo.o

foo.o:     file format elf64-x86-64

Disassembly of section .text._ZN3foo3foo17he211d7b4a3a0c16eE:

0000000000000000 <_ZN3foo3foo17he211d7b4a3a0c16eE>:
   0:   c3                      retq

Disassembly of section .text._ZN3foo3bar17h1acb594305f70c2eE:

0000000000000000 <_ZN3foo3bar17h1acb594305f70c2eE>:
   0:   48 83 ec 10             sub    $0x10,%rsp
   4:   48 8d 44 24 08          lea    0x8(%rsp),%rax
   9:   48 89 04 24             mov    %rax,(%rsp)
   d:   48 8b 04 24             mov    (%rsp),%rax
  11:   48 83 c4 10             add    $0x10,%rsp
  15:   c3                      retq

$ objdump -s -j .stack_sizes foo.o

foo.o:     file format elf64-x86-64

Contents of section .stack_sizes:
 0000 00000000 00000000 00                 .........
Contents of section .stack_sizes:
 0000 00000000 00000000 10                 .........
It's important to note that linkers will discard this linker section by default. To preserve the section you can use a linker script like the one shown below.

/* file: keep-stack-sizes.x */
SECTIONS
{
  /* `INFO` makes the section not allocatable so it won't be loaded into memory */
  .stack_sizes (INFO) :
  {
    KEEP(*(.stack_sizes));
  }
}
The linker script must be passed to the linker using a rustc flag like -C link-arg.

// file: src/main.rs
use std::ptr;

#[inline(never)]
fn main() {
    let xs = [0u32; 2];

    // force LLVM to allocate `xs` on the stack
    unsafe { ptr::read_volatile(&xs.as_ptr()); }
}
$ RUSTFLAGS="-Z emit-stack-sizes" cargo build --release

$ size -A target/release/hello | grep stack_sizes || echo section was not found
section was not found

$ RUSTFLAGS="-Z emit-stack-sizes" cargo rustc --release -- \
    -C link-arg=-Wl,-Tkeep-stack-sizes.x \
    -C link-arg=-N

$ size -A target/release/hello | grep stack_sizes
.stack_sizes                               90   176272

$ # non-allocatable section (flags don't contain the "A" (alloc) flag)
$ readelf -S target/release/hello
Section Headers:
  [Nr]   Name              Type             Address           Offset
       Size              EntSize            Flags  Link  Info  Align
(..)
  [1031] .stack_sizes      PROGBITS         000000000002b090  0002b0f0
       000000000000005a  0000000000000000   L       5     0     1

$ objdump -s -j .stack_sizes target/release/hello

target/release/hello:     file format elf64-x86-64

Contents of section .stack_sizes:
 2b090 c0040000 00000000 08f00400 00000000  ................
 2b0a0 00080005 00000000 00000810 05000000  ................
 2b0b0 00000000 20050000 00000000 10400500  .... ........@..
 2b0c0 00000000 00087005 00000000 00000080  ......p.........
 2b0d0 05000000 00000000 90050000 00000000  ................
 2b0e0 00a00500 00000000 0000               ..........
Author note: I'm not entirely sure why, in this case, -N is required in addition to -Tkeep-stack-sizes.x. For example, it's not required when producing statically linked files for the ARM Cortex-M architecture.

emscripten-wasm-eh

Use the WebAssembly exception handling ABI to unwind for the wasm32-unknown-emscripten. If compiling with this setting, the emcc linker should be invoked with -fwasm-exceptions. If linking with C/C++ files, the C/C++ files should also be compiled with -fwasm-exceptions.

env-set

The tracking issue for this feature is: #118372.

This option flag allows to specify environment variables value at compile time to be used by env! and option_env! macros. It also impacts tracked_env::var function from the proc_macro crate.

This information will be stored in the dep-info files. For more information about dep-info files, take a look here.

When retrieving an environment variable value, the one specified by --env-set will take precedence. For example, if you want have PATH=a in your environment and pass:

rustc --env-set PATH=env
Then you will have:

assert_eq!(env!("PATH"), "env");
It will trigger a new compilation if any of the --env-set argument value is different. So if you first passed:

--env-set A=B --env X=12
and then on next compilation:

--env-set A=B
X value is different (not set) so the code will be re-compiled.

Please note that on Windows, environment variables are case insensitive but case preserving whereas rustc's environment variables are case sensitive. For example, having Path in your environment (case insensitive) is different than using rustc --env-set Path=... (case sensitive).

export-executable-symbols

The tracking issue for this feature is: #84161.

The -Zexport-executable-symbols compiler flag makes rustc export symbols from executables. The resulting binary is runnable, but can also be used as a dynamic library. This is useful for interoperating with programs written in other languages, in particular languages with a runtime like Java or Lua.

For example on windows:

#[no_mangle]
fn my_function() -> usize {
    return 42;
}

fn main() {
    println!("Hello, world!");
}
A standard cargo build will produce a .exe without an export directory. When the export-executable-symbols flag is added

export RUSTFLAGS="-Zexport-executable-symbols"
cargo build
the binary has an export directory with the functions:

The Export Tables (interpreted .edata section contents)

...

[Ordinal/Name Pointer] Table
    [   0] my_function
    [   1] main
(the output of objdump -x on the binary)

Please note that the #[no_mangle] attribute is required. Without it, the symbol is not exported.

The equivalent of this flag in C and C++ compilers is the __declspec(dllexport) annotation or the -rdynamic linker flag.

--extern Options

Tracking issue for --extern crate modifiers: #98405
Tracking issue for noprelude: #98398
Tracking issue for priv: #98399
Tracking issue for nounused: #98400
Tracking issue for force: #111302
The behavior of the --extern flag can be modified with noprelude, priv or nounused options.

This is unstable feature, so you have to provide -Zunstable-options to enable it.

Examples

Use your own build of the core crate.

rustc main.rs -Z unstable-options --extern noprelude:core=libcore.rlib

To use multiple options, separate them with a comma:

rustc main.rs -Z unstable-options --extern noprelude,priv,nounused:mydep=mydep.rlib

Options

noprelude: Do not add the crate to the external prelude. If used, it will need to be imported using extern crate. This is used by the build-std project to simulate compatibility with sysroot-only crates.
priv: Mark the crate as a private dependency for the exported_private_dependencies lint.
nounused: Suppress unused-crate-dependencies warnings for the crate.
force: Resolve the crate as if it is used, even if it is not used. This can be used to satisfy compilation session requirements like the presence of an allocator or panic handler.
external-clangrt

This option controls whether the compiler links in its own runtime library for sanitizers. Passing this flag makes the compiler not link its own library. For more information, see the section in the sanitizers doc on working with other languages.

fixed-x18

This option prevents the compiler from using the x18 register. It is only supported on aarch64.

From the ABI spec:

X18 is the platform register and is reserved for the use of platform ABIs. This is an additional temporary register on platforms that don't assign a special meaning to it.

This flag only has an effect when the x18 register would otherwise be considered a temporary register. When the flag is applied, x18 is always a reserved register.

This flag is intended for use with the shadow call stack sanitizer. Generally, when that sanitizer is enabled, the x18 register is used to store a pointer to the shadow stack. Enabling this flag prevents the compiler from overwriting the shadow stack pointer with temporary data, which is necessary for the sanitizer to work correctly.

Currently, the -Zsanitizer=shadow-call-stack flag is only supported on platforms that always treat x18 as a reserved register, and the -Zfixed-x18 flag is not required to use the sanitizer on such platforms. However, the sanitizer may be supported on targets where this is not the case in the future. One way to do so now on Nightly compilers is to explicitly supply this -Zfixed-x18 flag with aarch64 targets, so that the sanitizer is available for instrumentation on targets like aarch64-unknown-none, for instance. However, discretion is still required to make sure that the runtime support is in place for this sanitizer to be effective.

It is undefined behavior for -Zsanitizer=shadow-call-stack code to call into code where x18 is a temporary register. On the other hand, when you are not using the shadow call stack sanitizer, compilation units compiled with and without the -Zfixed-x18 flag are compatible with each other.

fmt-debug

The tracking issue for this feature is: #129709.

Option -Z fmt-debug=val controls verbosity of derived Debug implementations and debug formatting in format strings ({:?}).

full — #[derive(Debug)] prints types recursively. This is the default behavior.

shallow — #[derive(Debug)] prints only the type name, or name of a variant of a fieldless enums. Details of the Debug implementation are not stable and may change in the future. Behavior of custom fmt::Debug implementations is not affected.

none — #[derive(Debug)] does not print anything at all. {:?} in formatting strings has no effect. This option may reduce size of binaries, and remove occurrences of type names in the binary that are not removed by striping symbols. However, it may also cause panic! and assert! messages to be incomplete.

function-return

The tracking issue for this feature is: https://github.com/rust-lang/rust/issues/116853.

Option -Zfunction-return controls how function returns are converted.

It is equivalent to Clang's and GCC's -mfunction-return. The Linux kernel uses it for RETHUNK builds. For details, see LLVM commit 2240d72f15f3 ("[X86] initial -mfunction-return=thunk-extern support") which introduces the feature.

Supported values for this option are:

keep: do not convert function returns.
thunk-extern: convert function returns (ret) to jumps (jmp) to an external symbol called __x86_return_thunk.
Like in Clang, GCC's values thunk and thunk-inline are not supported.

Only x86 and non-large code models are supported.

hint-mostly-unused

This flag hints to the compiler that most of the crate will probably go unused. The compiler can optimize its operation based on this assumption, in order to compile faster. This is a hint, and does not guarantee any particular behavior.

This option can substantially speed up compilation if applied to a large dependency where the majority of the dependency does not get used. This flag may slow down compilation in other cases.

Currently, this option makes the compiler defer as much code generation as possible from functions in the crate, until later crates invoke those functions. Functions that never get invoked will never have code generated for them. For instance, if a crate provides thousands of functions, but only a few of them will get called, this flag will result in the compiler only doing code generation for the called functions. (This uses the same mechanisms as cross-crate inlining of functions.) This does not affect extern functions, or functions marked as #[inline(never)].

To try applying this flag to one dependency out of a dependency tree, use the profile-rustflags feature of nightly cargo:

cargo-features = ["profile-rustflags"]

# ...
[dependencies]
mostly-unused-dependency = "1.2.3"

[profile.release.package.mostly-unused-dependency]
rustflags = ["-Zhint-mostly-unused"]
indirect-branch-cs-prefix

The tracking issue for this feature is: https://github.com/rust-lang/rust/issues/116852.

Option -Zindirect-branch-cs-prefix controls whether a cs prefix is added to call and jmp to indirect thunks.

It is equivalent to Clang's and GCC's -mindirect-branch-cs-prefix. The Linux kernel uses it for RETPOLINE builds. For details, see LLVM commit 6f867f910283 ("[X86] Support -mindirect-branch-cs-prefix for call and jmp to indirect thunk") which introduces the feature.

Only x86 and x86_64 are supported.

instrument-xray

The tracking issue for this feature is: #102921.

Enable generation of NOP sleds for XRay function tracing instrumentation. For more information on XRay, read LLVM documentation, and/or the XRay whitepaper.

Set the -Z instrument-xray compiler flag in order to enable XRay instrumentation.

-Z instrument-xray – use the default settings
-Z instrument-xray=skip-exit – configure a custom setting
-Z instrument-xray=ignore-loops,instruction-threshold=300 – multiple settings separated by commas
Supported options:

always – force instrumentation of all functions
never – do no instrument any functions
ignore-loops – ignore presence of loops, instrument functions based only on instruction count
instruction-threshold=10 – set a different instruction threshold for instrumentation
skip-entry – do no instrument function entry
skip-exit – do no instrument function exit
The default settings are:

instrument both entry & exit from functions
instrument functions with at least 200 instructions, or containing a non-trivial loop
Note that -Z instrument-xray only enables generation of NOP sleds which on their own don't do anything useful. In order to actually trace the functions, you will need to link a separate runtime library of your choice, such as Clang's XRay Runtime Library.

link-native-libraries

This option allows ignoring libraries specified in #[link] attributes instead of passing them to the linker. This can be useful in build systems that manage native libraries themselves and pass them manually, e.g. with -Clink-arg.

yes - Pass native libraries to the linker. Default.
no - Don't pass native libraries to the linker.
lint-llvm-ir

This flag will add LintPass to the start of the pipeline. You can use it to check for common errors in the LLVM IR generated by rustc. You can add -Cllvm-args=-lint-abort-on-error to abort the process if errors were found.

llvm-module-flag

This flag allows adding a key/value to the !llvm.module.flags metadata in the LLVM-IR for a compiled Rust module. The syntax is

## llvm_module_flag

Currently only u32 values are supported but the type is required to be specified for forward compatibility. The behavior element must match one of the named LLVM metadata behaviors

location-detail

The tracking issue for this feature is: #70580.

Option -Z location-detail=val controls what location details are tracked when using caller_location. This allows users to control what location details are printed as part of panic messages, by allowing them to exclude any combination of filenames, line numbers, and column numbers. This option is intended to provide users with a way to mitigate the size impact of #[track_caller].

This option supports a comma separated list of location details to be included. Valid options within this list are:

file - the filename of the panic will be included in the panic output
line - the source line of the panic will be included in the panic output
column - the source column of the panic will be included in the panic output
Any combination of these three options are supported. Alternatively, you can pass none to this option, which results in no location details being tracked. If this option is not specified, all three are included by default.

An example of a panic output when using -Z location-detail=line:

panicked at 'Process blink had a fault', <redacted>:323:0
The code size savings from this option are two-fold. First, the &'static str values for each path to a file containing a panic are removed from the binary. For projects with deep directory structures and many files with panics, this can add up. This category of savings can only be realized by excluding filenames from the panic output. Second, savings can be realized by allowing multiple panics to be fused into a single panicking branch. It is often the case that within a single file, multiple panics with the same panic message exist -- e.g. two calls to Option::unwrap() in a single line, or two calls to Result::expect() on adjacent lines. If column and line information are included in the Location struct passed to the panic handler, these branches cannot be fused, as the output is different depending on which panic occurs. However if line and column information is identical for all panics, these branches can be fused, which can lead to substantial code size savings, especially for small embedded binaries with many panics.

The savings from this option are amplified when combined with the use of -Zbuild-std, as otherwise paths for panics within the standard library are still included in your binary.

macro-stats

This feature is perma-unstable and has no tracking issue.

Some macros, especially procedural macros, can generate a surprising amount of code, which can slow down compile times. This is hard to detect because the generated code is normally invisible to the programmer.

This flag helps identify such cases. When enabled, the compiler measures the effect on code size of all used macros and prints a table summarizing that effect. For each distinct macro, it counts how many times it is used, and how much code it produces when expanded (in lines of code, and bytes of code). The code size evaluation uses the compiler's internal pretty-printing, and so will be independent of the formatting in the original code.

Note that the output size of a macro may be zero. E.g. the cfg! and #[test] macros often strip out code.

If a macro is identified as causing a large increase in code size, it is worth using cargo expand to inspect the post-expansion code, which includes the code produced by all macros. It may be possible to optimize the macro to produce smaller code, or it may be possible to avoid using it altogether.

min-function-alignment

The tracking issue for this feature is: https://github.com/rust-lang/rust/issues/82232.

The -Zmin-function-alignment=<align> flag specifies the minimum alignment of functions for which code is generated. The align value must be a power of 2, other values are rejected.

Note that -Zbuild-std (or similar) is required to apply this minimum alignment to standard library functions. By default, these functions come precompiled and their alignments won't respect the min-function-alignment flag.

This flag is equivalent to:

-fmin-function-alignment for GCC
-falign-functions for Clang
The specified alignment is a minimum. A higher alignment can be specified for specific functions by using the align(...) feature and annotating the function with a #[align(<align>)] attribute. The attribute's value is ignored when it is lower than the value passed to min-function-alignment.

There are two additional edge cases for this flag:

targets have a minimum alignment for functions (e.g. on x86_64 the lowest that LLVM generates is 16 bytes). A min-function-alignment value lower than the target's minimum has no effect.
the maximum alignment supported by rust (and LLVM) is 2^29. Trying to set a higher value results in an error.
## move_size_limit

The -Zmove-size-limit=N compiler flag enables large_assignments lints which will warn when moving objects whose size exceeds N bytes.

Lint warns only about moves in functions that participate in code generation. Consequently it will be ineffective for compiler invocation that emit metadata only, i.e., cargo check like workflows.

no-parallel-llvm

This flag disables parallelization of codegen and linking, while otherwise preserving behavior with regard to codegen units and LTO.

This flag is not useful for regular users, but it can be useful for debugging the backend. Codegen issues commonly only manifest under specific circumstances, e.g. if multiple codegen units are used and ThinLTO is enabled. Serialization of these threaded configurations makes the use of LLVM debugging facilities easier, by avoiding the interleaving of output.

no-steal-thir

By default, to save on memory, the THIR body (obtained from the tcx.thir_body query) is stolen once no longer used. This is inconvenient for authors of rustc drivers who want to access the THIR.

This option disables the stealing. This has no observable effect on compiler behavior, only on memory usage.

no-unique-section-names

This flag currently applies only to ELF-based targets using the LLVM codegen backend. It prevents the generation of unique ELF section names for each separate code and data item when -Z function-sections is also in use, which is the default for most targets. This option can reduce the size of object files, and depending on the linker, the final ELF binary as well.

For example, a function func will by default generate a code section called .text.func. Normally this is fine because the linker will merge all those .text.* sections into a single one in the binary. However, starting with LLVM 12, the backend will also generate unique section names for exception handling, so you would see a section name of .gcc_except_table.func in the object file and potentially in the final ELF binary, which could add significant bloat to programs that contain many functions.

This flag instructs LLVM to use the same .text and .gcc_except_table section name for each function, and it is analogous to Clang's -fno-unique-section-names option.

## offload

The tracking issue for this feature is: #131513.

This feature will later allow you to run functions on GPUs. It is work in progress. Set the -Zoffload=Enable compiler flag to experiment with it.

on-broken-pipe

The tracking issue for this feature is: #97889

Note: The ui for this feature was previously an attribute named #[unix_sigpipe = "..."].

Overview

The -Zon-broken-pipe=... compiler flag can be used to specify how libstd shall setup SIGPIPE on Unix platforms before invoking fn main(). This flag is ignored on non-Unix targets. The flag can be used with three different values or be omitted entirely. It affects SIGPIPE before fn main() and before children get exec()'ed:

Compiler flag	SIGPIPE before fn main()	SIGPIPE before child exec()
not used	SIG_IGN	SIG_DFL
-Zon-broken-pipe=kill	SIG_DFL	not touched
-Zon-broken-pipe=error	SIG_IGN	not touched
-Zon-broken-pipe=inherit	not touched	not touched
-Zon-broken-pipe not used

If -Zon-broken-pipe is not used, libstd will behave in the manner it has since 2014, before Rust 1.0. SIGPIPE will be set to SIG_IGN before fn main() and result in EPIPE errors which are converted to std::io::ErrorKind::BrokenPipe.

When spawning child processes, SIGPIPE will be set to SIG_DFL before doing the underlying exec() syscall.

-Zon-broken-pipe=kill

Set the SIGPIPE handler to SIG_DFL before invoking fn main(). This will result in your program getting killed if it tries to write to a closed pipe. This is normally what you want if your program produces textual output.

When spawning child processes, SIGPIPE will not be touched. This normally means child processes inherit SIG_DFL for SIGPIPE.

Example

fn main() {
    loop {
        println!("hello world");
    }
}
$ rustc -Zon-broken-pipe=kill main.rs
$ ./main | head -n1
hello world
-Zon-broken-pipe=error

Set the SIGPIPE handler to SIG_IGN before invoking fn main(). This will result in ErrorKind::BrokenPipe errors if you program tries to write to a closed pipe. This is normally what you want if you for example write socket servers, socket clients, or pipe peers.

When spawning child processes, SIGPIPE will not be touched. This normally means child processes inherit SIG_IGN for SIGPIPE.

Example

fn main() {
    loop {
        println!("hello world");
    }
}
$ rustc -Zon-broken-pipe=error main.rs
$ ./main | head -n1
hello world
thread 'main' panicked at library/std/src/io/stdio.rs:1118:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
-Zon-broken-pipe=inherit

Leave SIGPIPE untouched before entering fn main(). Unless the parent process has changed the default SIGPIPE handler from SIG_DFL to something else, this will behave the same as -Zon-broken-pipe=kill.

When spawning child processes, SIGPIPE will not be touched. This normally means child processes inherit SIG_DFL for SIGPIPE.

patchable-function-entry

The -Z patchable-function-entry=total_nops,prefix_nops or -Z patchable-function-entry=total_nops compiler flag enables nop padding of function entries with 'total_nops' nops, with an offset for the entry of the function at 'prefix_nops' nops. In the second form, 'prefix_nops' defaults to 0.

As an illustrative example, -Z patchable-function-entry=3,2 would produce:

nop
nop
function_label:
nop
//Actual function code begins here
This flag is used for hotpatching, especially in the Linux kernel. The flag arguments are modeled after the -fpatchable-function-entry flag as defined for both Clang and gcc and is intended to provide the same effect.

print=check-cfg

The tracking issue for this feature is: #125704.

This option of the --print flag print the list of all the expected cfgs.

This is related to the --check-cfg flag which allows specifying arbitrary expected names and values.

This print option works similarly to --print=cfg (modulo check-cfg specifics).

--check-cfg	--print=check-cfg
cfg(foo)	foo
cfg(foo, values("bar"))	foo="bar"
cfg(foo, values(none(), "bar"))	foo & foo="bar"
check-cfg specific syntax
cfg(foo, values(any())	foo=any()
cfg(foo, values())	foo=
cfg(any())	any()
none	any()=any()
To be used like this:

rustc --print=check-cfg -Zunstable-options lib.rs
print=crate-root-lint-levels

The tracking issue for this feature is: #139180.

This option of the --print flag print the list of lints with print out all the lints and their associated levels (allow, warn, deny, forbid) based on the regular Rust rules at crate root, that is (roughly):

command line args (-W, -A, --force-warn, --cap-lints, ...)
crate root attributes (#![allow], #![warn], #[expect], ...)
the special warnings lint group
the default lint level
The output format is LINT_NAME=LINT_LEVEL, e.g.:

unknown_lint=warn
arithmetic_overflow=deny
To be used like this:

rustc --print=crate-root-lint-levels -Zunstable-options lib.rs
print=supported-crate-types

The tracking issue for this feature is: #138640.

This option of the --print flag produces a list of crate types (delimited by newlines) supported for the given target.

The crate type strings correspond to the values accepted by the --crate-type flag.

Intended to be used like this:

rustc --print=supported-crate-types -Zunstable-options --target=x86_64-unknown-linux-gnu
Example output for x86_64-unknown-linux-gnu:

bin
cdylib
dylib
lib
proc-macro
rlib
staticlib
profile-sample-use

-Zprofile-sample-use=code.prof directs rustc to use the profile code.prof as a source for Automatic Feedback Directed Optimization (AFDO). See the documentation of -Zdebug-info-for-profiling for more information on using AFDO.

randomize-layout

The tracking issue for this feature is: #106764.

The -Zrandomize-layout flag changes the layout algorithm for repr(Rust) types defined in the current crate from its normal optimization goals to pseudorandomly rearranging fields within the degrees of freedom provided by the largely unspecified default representation. This also affects type sizes and padding. Downstream instantiations of generic types defined in a crate with randomization enabled will also be randomized.

It can be used to find unsafe code that accidentally relies on unspecified behavior.

Randomization is not guaranteed to use a different permutation for each compilation session. -Zlayout-seed=<u64> can be used to supply additional entropy.

Randomization only approximates the intended freedom of repr(Rust). Sometimes two distinct types may still consistently result in the same layout due to limitations of the current implementation. Randomization may become more aggressive over time as our coverage of the available degrees of freedoms improves. Corollary: Randomization is not a safety oracle. Two struct layouts being observably the same under different layout seeds on the current compiler version does not guarantee that future compiler versions won't give them distinct layouts.

Randomization may also become less aggressive in the future if additional guarantees get added to the default layout.

reg-struct-return

The tracking issue for this feature is: https://github.com/rust-lang/rust/issues/116973.

Option -Zreg-struct-return causes the compiler to return small structs in registers instead of on the stack for extern "C"-like functions. It is UNSOUND to link together crates that use different values for this flag. It is only supported on x86.

It is equivalent to Clang's and GCC's -freg-struct-return.

## regparm

The tracking issue for this feature is: https://github.com/rust-lang/rust/issues/131749.

Option -Zregparm=N causes the compiler to pass N arguments in registers EAX, EDX, and ECX instead of on the stack for "C", "cdecl", and "stdcall" fn. It is UNSOUND to link together crates that use different values for this flag. It is only supported on x86.

It is equivalent to Clang's and GCC's -mregparm.

Supported values for this option are 0-3.

Implementation details: For eligible arguments, llvm inreg attribute is set.

remap-cwd-prefix

The tracking issue for this feature is: #87325.

This flag will rewrite absolute paths under the current working directory, replacing the current working directory prefix with a specified value.

The given value may be absolute or relative, or empty. This switch takes precedence over --remap-path-prefix in case they would both match a given path.

This flag helps to produce deterministic output, by removing the current working directory from build output, while allowing the command line to be universally reproducible, such that the same execution will work on all machines, regardless of build environment.

Example

# This would produce an absolute path to main.rs in build outputs of
# "./main.rs".
rustc -Z remap-cwd-prefix=. main.rs
remap-path-scope

The tracking issue for this feature is: #111540.

When the --remap-path-prefix option is passed to rustc, source path prefixes in all output will be affected by default. The --remap-path-scope argument can be used in conjunction with --remap-path-prefix to determine paths in which output context should be affected. This flag accepts a comma-separated list of values and may be specified multiple times, in which case the scopes are aggregated together. The valid scopes are:

macro - apply remappings to the expansion of std::file!() macro. This is where paths in embedded panic messages come from
diagnostics - apply remappings to printed compiler diagnostics
debuginfo - apply remappings to debug information
coverage - apply remappings to coverage information
object - apply remappings to all paths in compiled executables or libraries, but not elsewhere. Currently an alias for macro,debuginfo.
all - an alias for all of the above, also equivalent to supplying only --remap-path-prefix without --remap-path-scope.
Example

# This would produce an absolute path to main.rs in build outputs of
# "./main.rs".
rustc --remap-path-prefix=$(PWD)=/remapped -Zremap-path-scope=object main.rs
report-time

The tracking issue for this feature is: #64888

The report-time feature adds a possibility to report execution time of the tests generated via libtest.

This is unstable feature, so you have to provide -Zunstable-options to get this feature working.

Sample usage command:

./test_executable -Zunstable-options --report-time
Available options:

--report-time
                Show execution time of each test.
                Threshold values for colorized output can be
                configured via
                `RUST_TEST_TIME_UNIT`, `RUST_TEST_TIME_INTEGRATION`
                and
                `RUST_TEST_TIME_DOCTEST` environment variables.
                Expected format of environment variable is
                `VARIABLE=WARN_TIME,CRITICAL_TIME`.
                Not available for --format=terse
--ensure-time
                Treat excess of the test execution time limit as
                error.
                Threshold values for this option can be configured via
                `RUST_TEST_TIME_UNIT`, `RUST_TEST_TIME_INTEGRATION`
                and
                `RUST_TEST_TIME_DOCTEST` environment variables.
                Expected format of environment variable is
                `VARIABLE=WARN_TIME,CRITICAL_TIME`.
                `CRITICAL_TIME` here means the limit that should not be
                exceeded by test.
Example of the environment variable format:

RUST_TEST_TIME_UNIT=100,200
where 100 stands for warn time, and 200 stands for critical time.

Examples

cargo test --tests -- -Zunstable-options --report-time
    Finished dev [unoptimized + debuginfo] target(s) in 0.02s
     Running target/debug/deps/example-27fb188025bec02c

running 3 tests
test tests::unit_test_quick ... ok <0.000s>
test tests::unit_test_warn ... ok <0.055s>
test tests::unit_test_critical ... ok <0.110s>

test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out

     Running target/debug/deps/tests-cedb06f6526d15d9

running 3 tests
test unit_test_quick ... ok <0.000s>
test unit_test_warn ... ok <0.550s>
test unit_test_critical ... ok <1.100s>

test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
## sanitizer

Sanitizers are tools that help detect and prevent various types of bugs and vulnerabilities in software. They are available in compilers and work by instrumenting the code to add additional runtime checks. While they provide powerful tools for identifying bugs or security issues, it's important to note that using sanitizers can introduce runtime overhead and might not catch all possible issues. Therefore, they are typically used alongside other best practices in software development, such as testing and fuzzing, to ensure the highest level of software quality and security.

The tracking issues for this feature are:

#39699.
#89653.
This feature allows for use of one of following sanitizers:

Those intended for testing or fuzzing (but not production use):

AddressSanitizer a fast memory error detector.
HWAddressSanitizer a memory error detector similar to AddressSanitizer, but based on partial hardware assistance.
LeakSanitizer a run-time memory leak detector.
MemorySanitizer a detector of uninitialized reads.
RealtimeSanitizer a detector of calls to function with non-deterministic execution time in realtime contexts.
ThreadSanitizer a fast data race detector.
Those that apart from testing, may be used in production:

ControlFlowIntegrity LLVM Control Flow Integrity (CFI) provides forward-edge control flow protection.
DataFlowSanitizer a generic dynamic data flow analysis framework.
KernelControlFlowIntegrity LLVM Kernel Control Flow Integrity (KCFI) provides forward-edge control flow protection for operating systems kernels.
MemTagSanitizer fast memory error detector based on Armv8.5-A Memory Tagging Extension.
SafeStack provides backward-edge control flow protection by separating the stack into safe and unsafe regions.
ShadowCallStack provides backward-edge control flow protection (aarch64 only).
To enable a sanitizer compile with -Zsanitizer=address, -Zsanitizer=cfi, -Zsanitizer=dataflow,-Zsanitizer=hwaddress, -Zsanitizer=leak, -Zsanitizer=memory, -Zsanitizer=memtag, -Zsanitizer=realtime, -Zsanitizer=shadow-call-stack or -Zsanitizer=thread. You might also need the --target and build-std flags. If you're working with other languages that are also instrumented with sanitizers, you might need the external-clangrt flag. See the section on working with other languages.

Example:

$ RUSTFLAGS=-Zsanitizer=address cargo build -Zbuild-std --target x86_64-unknown-linux-gnu
Additional options for sanitizers can be passed to LLVM command line argument processor via LLVM arguments using llvm-args codegen option (e.g., -Cllvm-args=-dfsan-combine-pointer-labels-on-load=false). See the sanitizer documentation for more information about additional options.

AddressSanitizer

AddressSanitizer is a memory error detector. It can detect the following types of bugs:

Out of bound accesses to heap, stack and globals
Use after free
Use after return (runtime flag ASAN_OPTIONS=detect_stack_use_after_return=1)
Use after scope
Double-free, invalid free
Memory leaks
The memory leak detection is enabled by default on Linux, and can be enabled with runtime flag ASAN_OPTIONS=detect_leaks=1 on macOS.

AddressSanitizer is supported on the following targets:

aarch64-apple-darwin
aarch64-unknown-fuchsia
aarch64-unknown-linux-gnu
x86_64-apple-darwin
x86_64-unknown-fuchsia
x86_64-unknown-freebsd
x86_64-unknown-linux-gnu
AddressSanitizer works with non-instrumented code although it will impede its ability to detect some bugs. It is not expected to produce false positive reports.

See the Clang AddressSanitizer documentation for more details.

Examples

Stack buffer overflow:

fn main() {
    let xs = [0, 1, 2, 3];
    let _y = unsafe { *xs.as_ptr().offset(4) };
}
$ export RUSTFLAGS=-Zsanitizer=address RUSTDOCFLAGS=-Zsanitizer=address
$ cargo run -Zbuild-std --target x86_64-unknown-linux-gnu
==37882==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7ffe400e6250 at pc 0x5609a841fb20 bp 0x7ffe400e6210 sp 0x7ffe400e6208
READ of size 4 at 0x7ffe400e6250 thread T0
    #0 0x5609a841fb1f in example::main::h628ffc6626ed85b2 /.../src/main.rs:3:23
    ...

Address 0x7ffe400e6250 is located in stack of thread T0 at offset 48 in frame
    #0 0x5609a841f8af in example::main::h628ffc6626ed85b2 /.../src/main.rs:1

  This frame has 1 object(s):
    [32, 48) 'xs' (line 2) <== Memory access at offset 48 overflows this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow /.../src/main.rs:3:23 in example::main::h628ffc6626ed85b2
Shadow bytes around the buggy address:
  0x100048014bf0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x100048014c00: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x100048014c10: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x100048014c20: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x100048014c30: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
=>0x100048014c40: 00 00 00 00 f1 f1 f1 f1 00 00[f3]f3 00 00 00 00
  0x100048014c50: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x100048014c60: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x100048014c70: f1 f1 f1 f1 00 00 f3 f3 00 00 00 00 00 00 00 00
  0x100048014c80: 00 00 00 00 00 00 00 00 00 00 00 00 f1 f1 f1 f1
  0x100048014c90: 00 00 f3 f3 00 00 00 00 00 00 00 00 00 00 00 00
Shadow byte legend (one shadow byte represents 8 application bytes):
  Addressable:           00
  Partially addressable: 01 02 03 04 05 06 07
  Heap left redzone:       fa
  Freed heap region:       fd
  Stack left redzone:      f1
  Stack mid redzone:       f2
  Stack right redzone:     f3
  Stack after return:      f5
  Stack use after scope:   f8
  Global redzone:          f9
  Global init order:       f6
  Poisoned by user:        f7
  Container overflow:      fc
  Array cookie:            ac
  Intra object redzone:    bb
  ASan internal:           fe
  Left alloca redzone:     ca
  Right alloca redzone:    cb
  Shadow gap:              cc
==37882==ABORTING
Use of a stack object after its scope has already ended:

static mut P: *mut usize = std::ptr::null_mut();

fn main() {
    unsafe {
        {
            let mut x = 0;
            P = &mut x;
        }
        std::ptr::write_volatile(P, 123);
    }
}
$ export RUSTFLAGS=-Zsanitizer=address RUSTDOCFLAGS=-Zsanitizer=address
$ cargo run -Zbuild-std --target x86_64-unknown-linux-gnu
=================================================================
==39249==ERROR: AddressSanitizer: stack-use-after-scope on address 0x7ffc7ed3e1a0 at pc 0x55c98b262a8e bp 0x7ffc7ed3e050 sp 0x7ffc7ed3e048
WRITE of size 8 at 0x7ffc7ed3e1a0 thread T0
    #0 0x55c98b262a8d in core::ptr::write_volatile::he21f1df5a82f329a /.../src/rust/src/libcore/ptr/mod.rs:1048:5
    #1 0x55c98b262cd2 in example::main::h628ffc6626ed85b2 /.../src/main.rs:9:9
    ...

Address 0x7ffc7ed3e1a0 is located in stack of thread T0 at offset 32 in frame
    #0 0x55c98b262bdf in example::main::h628ffc6626ed85b2 /.../src/main.rs:3

  This frame has 1 object(s):
    [32, 40) 'x' (line 6) <== Memory access at offset 32 is inside this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-use-after-scope /.../src/rust/src/libcore/ptr/mod.rs:1048:5 in core::ptr::write_volatile::he21f1df5a82f329a
Shadow bytes around the buggy address:
  0x10000fd9fbe0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x10000fd9fbf0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x10000fd9fc00: 00 00 00 00 00 00 00 00 00 00 00 00 f1 f1 f1 f1
  0x10000fd9fc10: f8 f8 f3 f3 00 00 00 00 00 00 00 00 00 00 00 00
  0x10000fd9fc20: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
=>0x10000fd9fc30: f1 f1 f1 f1[f8]f3 f3 f3 00 00 00 00 00 00 00 00
  0x10000fd9fc40: 00 00 00 00 00 00 00 00 00 00 00 00 f1 f1 f1 f1
  0x10000fd9fc50: 00 00 f3 f3 00 00 00 00 00 00 00 00 00 00 00 00
  0x10000fd9fc60: 00 00 00 00 00 00 00 00 f1 f1 f1 f1 00 00 f3 f3
  0x10000fd9fc70: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x10000fd9fc80: 00 00 00 00 f1 f1 f1 f1 00 00 f3 f3 00 00 00 00
Shadow byte legend (one shadow byte represents 8 application bytes):
  Addressable:           00
  Partially addressable: 01 02 03 04 05 06 07
  Heap left redzone:       fa
  Freed heap region:       fd
  Stack left redzone:      f1
  Stack mid redzone:       f2
  Stack right redzone:     f3
  Stack after return:      f5
  Stack use after scope:   f8
  Global redzone:          f9
  Global init order:       f6
  Poisoned by user:        f7
  Container overflow:      fc
  Array cookie:            ac
  Intra object redzone:    bb
  ASan internal:           fe
  Left alloca redzone:     ca
  Right alloca redzone:    cb
  Shadow gap:              cc
==39249==ABORTING
ControlFlowIntegrity

The LLVM CFI support in the Rust compiler provides forward-edge control flow protection for both Rust-compiled code only and for C or C++ and Rust -compiled code mixed-language binaries, also known as “mixed binaries” (i.e., for when C or C++ and Rust -compiled code share the same virtual address space), by aggregating function pointers in groups identified by their return and parameter types.

LLVM CFI can be enabled with -Zsanitizer=cfi and requires LTO (i.e., -Clinker-plugin-lto or -Clto). Cross-language LLVM CFI can be enabled with -Zsanitizer=cfi, and requires the -Zsanitizer-cfi-normalize-integers option to be used with Clang -fsanitize-cfi-icall-experimental-normalize-integers option for cross-language LLVM CFI support, and proper (i.e., non-rustc) LTO (i.e., -Clinker-plugin-lto).

It is recommended to rebuild the standard library with CFI enabled by using the Cargo build-std feature (i.e., -Zbuild-std) when enabling CFI.

See the Clang ControlFlowIntegrity documentation for more details.

Example 1: Redirecting control flow using an indirect branch/call to an invalid destination

fn add_one(x: i32) -> i32 {
    x + 1
}

#[unsafe(naked)]
pub extern "sysv64" fn add_two(x: i32) {
    // x + 2 preceded by a landing pad/nop block
    std::arch::naked_asm!(
        "
         nop
         nop
         nop
         nop
         nop
         nop
         nop
         nop
         nop
         lea eax, [rdi+2]
         ret
        "
    );
}

fn do_twice(f: fn(i32) -> i32, arg: i32) -> i32 {
    f(arg) + f(arg)
}

fn main() {
    let answer = do_twice(add_one, 5);

    println!("The answer is: {}", answer);

        println!("With CFI enabled, you should not see the next answer");
        let f: fn(i32) -> i32 = unsafe {
            // Offset 0 is a valid branch/call destination (i.e., the function entry
            // point), but offsets 1-8 within the landing pad/nop block are invalid
            // branch/call destinations (i.e., within the body of the function).
            std::mem::transmute::<*const u8, fn(i32) -> i32>((add_two as *const u8).offset(5))
        };
        let next_answer = do_twice(f, 5);

        println!("The next answer is: {}", next_answer);
}
Fig. 1. Redirecting control flow using an indirect branch/call to an invalid destination (i.e., within the body of the function).

$ cargo run --release
   Compiling rust-cfi-1 v0.1.0 (/home/rcvalle/rust-cfi-1)
    Finished release [optimized] target(s) in 0.42s
     Running `target/release/rust-cfi-1`
The answer is: 12
With CFI enabled, you should not see the next answer
The next answer is: 14
$
Fig. 2. Build and execution of Fig. 1 with LLVM CFI disabled.

$ RUSTFLAGS="-Clinker-plugin-lto -Clinker=clang -Clink-arg=-fuse-ld=lld -Zsanitizer=cfi" cargo run -Zbuild-std -Zbuild-std-features --release --target x86_64-unknown-linux-gnu
   ...
   Compiling rust-cfi-1 v0.1.0 (/home/rcvalle/rust-cfi-1)
    Finished release [optimized] target(s) in 1m 08s
     Running `target/x86_64-unknown-linux-gnu/release/rust-cfi-1`
The answer is: 12
With CFI enabled, you should not see the next answer
Illegal instruction
$
Fig. 3. Build and execution of Fig. 1 with LLVM CFI enabled.

When LLVM CFI is enabled, if there are any attempts to change/hijack control flow using an indirect branch/call to an invalid destination, the execution is terminated (see Fig. 3).

Example 2: Redirecting control flow using an indirect branch/call to a function with a different number of parameters

use std::mem;

fn add_one(x: i32) -> i32 {
    x + 1
}

fn add_two(x: i32, _y: i32) -> i32 {
    x + 2
}

fn do_twice(f: fn(i32) -> i32, arg: i32) -> i32 {
    f(arg) + f(arg)
}

fn main() {
    let answer = do_twice(add_one, 5);

    println!("The answer is: {}", answer);

    println!("With CFI enabled, you should not see the next answer");
    let f: fn(i32) -> i32 =
        unsafe { mem::transmute::<*const u8, fn(i32) -> i32>(add_two as *const u8) };
    let next_answer = do_twice(f, 5);

    println!("The next answer is: {}", next_answer);
}
Fig. 4. Redirecting control flow using an indirect branch/call to a function with a different number of parameters than arguments intended/passed in the call/branch site.

$ cargo run --release
   Compiling rust-cfi-2 v0.1.0 (/home/rcvalle/rust-cfi-2)
    Finished release [optimized] target(s) in 0.43s
     Running `target/release/rust-cfi-2`
The answer is: 12
With CFI enabled, you should not see the next answer
The next answer is: 14
$
Fig. 5. Build and execution of Fig. 4 with LLVM CFI disabled.

$ RUSTFLAGS="-Clinker-plugin-lto -Clinker=clang -Clink-arg=-fuse-ld=lld -Zsanitizer=cfi" cargo run -Zbuild-std -Zbuild-std-features --release --target x86_64-unknown-linux-gnu
   ...
   Compiling rust-cfi-2 v0.1.0 (/home/rcvalle/rust-cfi-2)
    Finished release [optimized] target(s) in 1m 08s
     Running `target/x86_64-unknown-linux-gnu/release/rust-cfi-2`
The answer is: 12
With CFI enabled, you should not see the next answer
Illegal instruction
$
Fig. 6. Build and execution of Fig. 4 with LLVM CFI enabled.

When LLVM CFI is enabled, if there are any attempts to change/hijack control flow using an indirect branch/call to a function with different number of parameters than arguments intended/passed in the call/branch site, the execution is also terminated (see Fig. 6).

Example 3: Redirecting control flow using an indirect branch/call to a function with different return and parameter types

use std::mem;

fn add_one(x: i32) -> i32 {
    x + 1
}

fn add_two(x: i64) -> i64 {
    x + 2
}

fn do_twice(f: fn(i32) -> i32, arg: i32) -> i32 {
    f(arg) + f(arg)
}

fn main() {
    let answer = do_twice(add_one, 5);

    println!("The answer is: {}", answer);

    println!("With CFI enabled, you should not see the next answer");
    let f: fn(i32) -> i32 =
        unsafe { mem::transmute::<*const u8, fn(i32) -> i32>(add_two as *const u8) };
    let next_answer = do_twice(f, 5);

    println!("The next answer is: {}", next_answer);
}
Fig. 7. Redirecting control flow using an indirect branch/call to a function with different return and parameter types than the return type expected and arguments intended/passed at the call/branch site.

$ cargo run --release
   Compiling rust-cfi-3 v0.1.0 (/home/rcvalle/rust-cfi-3)
    Finished release [optimized] target(s) in 0.44s
     Running `target/release/rust-cfi-3`
The answer is: 12
With CFI enabled, you should not see the next answer
The next answer is: 14
$
Fig. 8. Build and execution of Fig. 7 with LLVM CFI disabled.

$ RUSTFLAGS="-Clinker-plugin-lto -Clinker=clang -Clink-arg=-fuse-ld=lld -Zsanitizer=cfi" cargo run -Zbuild-std -Zbuild-std-features --release --target x86_64-unknown-linux-gnu
   ...
   Compiling rust-cfi-3 v0.1.0 (/home/rcvalle/rust-cfi-3)
    Finished release [optimized] target(s) in 1m 07s
     Running `target/x86_64-unknown-linux-gnu/release/rust-cfi-3`
The answer is: 12
With CFI enabled, you should not see the next answer
Illegal instruction
$
Fig. 9. Build and execution of Fig. 7 with LLVM CFI enabled.

When LLVM CFI is enabled, if there are any attempts to change/hijack control flow using an indirect branch/call to a function with different return and parameter types than the return type expected and arguments intended/passed in the call/branch site, the execution is also terminated (see Fig. 9).

Example 4: Redirecting control flow using an indirect branch/call to a function with different return and parameter types across the FFI boundary

int
do_twice(int (*fn)(int), int arg)
{
    return fn(arg) + fn(arg);
}
Fig. 10. Example C library.

use std::mem;

#[link(name = "foo")]
extern "C" {
    fn do_twice(f: unsafe extern "C" fn(i32) -> i32, arg: i32) -> i32;
}

unsafe extern "C" fn add_one(x: i32) -> i32 {
    x + 1
}

unsafe extern "C" fn add_two(x: i64) -> i64 {
    x + 2
}

fn main() {
    let answer = unsafe { do_twice(add_one, 5) };

    println!("The answer is: {}", answer);

    println!("With CFI enabled, you should not see the next answer");
    let f: unsafe extern "C" fn(i32) -> i32 = unsafe {
        mem::transmute::<*const u8, unsafe extern "C" fn(i32) -> i32>(add_two as *const u8)
    };
    let next_answer = unsafe { do_twice(f, 5) };

    println!("The next answer is: {}", next_answer);
}
Fig. 11. Redirecting control flow using an indirect branch/call to a function with different return and parameter types than the return type expected and arguments intended/passed in the call/branch site, across the FFI boundary.

$ make
mkdir -p target/release
clang -I. -Isrc -Wall -c src/foo.c -o target/release/libfoo.o
llvm-ar rcs target/release/libfoo.a target/release/libfoo.o
RUSTFLAGS="-L./target/release -Clinker=clang -Clink-arg=-fuse-ld=lld" cargo build --release
   Compiling rust-cfi-4 v0.1.0 (/home/rcvalle/rust-cfi-4)
    Finished release [optimized] target(s) in 0.49s
$ ./target/release/rust-cfi-4
The answer is: 12
With CFI enabled, you should not see the next answer
The next answer is: 14
$
Fig. 12. Build and execution of Figs. 10–11 with LLVM CFI disabled.

$ make
mkdir -p target/release
clang -I. -Isrc -Wall -flto -fsanitize=cfi -fsanitize-cfi-icall-experimental-normalize-integers -fvisibility=hidden -c -emit-llvm src/foo.c -o target/release/libfoo.bc
llvm-ar rcs target/release/libfoo.a target/release/libfoo.bc
RUSTFLAGS="-L./target/release -Clinker-plugin-lto -Clinker=clang -Clink-arg=-fuse-ld=lld -Zsanitizer=cfi -Zsanitizer-cfi-normalize-integers" cargo build -Zbuild-std -Zbuild-std-features --release --target x86_64-unknown-linux-gnu
   ...
   Compiling rust-cfi-4 v0.1.0 (/home/rcvalle/rust-cfi-4)
    Finished release [optimized] target(s) in 1m 06s
$ ./target/x86_64-unknown-linux-gnu/release/rust-cfi-4
The answer is: 12
With CFI enabled, you should not see the next answer
Illegal instruction
$
Fig. 13. Build and execution of FIgs. 10–11 with LLVM CFI enabled.

When LLVM CFI is enabled, if there are any attempts to redirect control flow using an indirect branch/call to a function with different return and parameter types than the return type expected and arguments intended/passed in the call/branch site, even across the FFI boundary and for extern "C" function types indirectly called (i.e., callbacks/function pointers) across the FFI boundary, the execution is also terminated (see Fig. 13).

HWAddressSanitizer

HWAddressSanitizer is a newer variant of AddressSanitizer that consumes much less memory.

HWAddressSanitizer is supported on the following targets:

aarch64-linux-android
aarch64-unknown-linux-gnu
HWAddressSanitizer requires tagged-globals target feature to instrument globals. To enable this target feature compile with -C target-feature=+tagged-globals

See the Clang HWAddressSanitizer documentation for more details.

Example

Heap buffer overflow:

fn main() {
    let xs = vec![0, 1, 2, 3];
    let _y = unsafe { *xs.as_ptr().offset(4) };
}
$ rustc main.rs -Zsanitizer=hwaddress -C target-feature=+tagged-globals -C
linker=aarch64-linux-gnu-gcc -C link-arg=-fuse-ld=lld --target
aarch64-unknown-linux-gnu
$ ./main
==241==ERROR: HWAddressSanitizer: tag-mismatch on address 0xefdeffff0050 at pc 0xaaaae0ae4a98
READ of size 4 at 0xefdeffff0050 tags: 2c/00 (ptr/mem) in thread T0
    #0 0xaaaae0ae4a94  (/.../main+0x54a94)
    ...

[0xefdeffff0040,0xefdeffff0060) is a small allocated heap chunk; size: 32 offset: 16
0xefdeffff0050 is located 0 bytes to the right of 16-byte region [0xefdeffff0040,0xefdeffff0050)
allocated here:
    #0 0xaaaae0acb80c  (/.../main+0x3b80c)
    ...

Thread: T0 0xeffe00002000 stack: [0xffffc28ad000,0xffffc30ad000) sz: 8388608 tls: [0xffffaa10a020,0xffffaa10a7d0)
Memory tags around the buggy address (one tag corresponds to 16 bytes):
  0xfefcefffef80: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefcefffef90: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefcefffefa0: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefcefffefb0: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefcefffefc0: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefcefffefd0: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefcefffefe0: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefcefffeff0: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
=>0xfefceffff000: d7  d7  05  00  2c [00] 00  00  00  00  00  00  00  00  00  00
  0xfefceffff010: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefceffff020: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefceffff030: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefceffff040: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefceffff050: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefceffff060: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefceffff070: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
  0xfefceffff080: 00  00  00  00  00  00  00  00  00  00  00  00  00  00  00  00
Tags for short granules around the buggy address (one tag corresponds to 16 bytes):
  0xfefcefffeff0: ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..
=>0xfefceffff000: ..  ..  8c  ..  .. [..] ..  ..  ..  ..  ..  ..  ..  ..  ..  ..
  0xfefceffff010: ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..  ..
See https://clang.llvm.org/docs/HardwareAssistedAddressSanitizerDesign.html#short-granules for a description of short granule tags
Registers where the failure occurred (pc 0xaaaae0ae4a98):
    x0  2c00efdeffff0050  x1  0000000000000004  x2  0000000000000004  x3  0000000000000000
    x4  0000fffefc30ac37  x5  000000000000005d  x6  00000ffffc30ac37  x7  0000efff00000000
    x8  2c00efdeffff0050  x9  0200efff00000000  x10 0000000000000000  x11 0200efff00000000
    x12 0200effe00000310  x13 0200effe00000310  x14 0000000000000008  x15 5d00ffffc30ac360
    x16 0000aaaae0ad062c  x17 0000000000000003  x18 0000000000000001  x19 0000ffffc30ac658
    x20 4e00ffffc30ac6e0  x21 0000aaaae0ac5e10  x22 0000000000000000  x23 0000000000000000
    x24 0000000000000000  x25 0000000000000000  x26 0000000000000000  x27 0000000000000000
    x28 0000000000000000  x29 0000ffffc30ac5a0  x30 0000aaaae0ae4a98
SUMMARY: HWAddressSanitizer: tag-mismatch (/.../main+0x54a94)
KernelControlFlowIntegrity

The LLVM Kernel Control Flow Integrity (CFI) support to the Rust compiler initially provides forward-edge control flow protection for operating systems kernels for Rust-compiled code only by aggregating function pointers in groups identified by their return and parameter types. (See LLVM commit cff5bef "KCFI sanitizer".)

Forward-edge control flow protection for C or C++ and Rust -compiled code "mixed binaries" (i.e., for when C or C++ and Rust -compiled code share the same virtual address space) will be provided in later work by defining and using compatible type identifiers (see Type metadata in the design document in the tracking issue #89653).

LLVM KCFI can be enabled with -Zsanitizer=kcfi.

LLVM KCFI is supported on the following targets:

aarch64-linux-android
aarch64-unknown-linux-gnu
x86_64-linux-android
x86_64-unknown-linux-gnu
See the Clang KernelControlFlowIntegrity documentation for more details.

DataFlowSanitizer

DataFlowSanitizer is a generalised dynamic data flow analysis.

Unlike other Sanitizer tools, this tool is not designed to detect a specific class of bugs on its own. Instead, it provides a generic dynamic data flow analysis framework to be used by clients to help detect application-specific issues within their own code.

DataFlowSanitizer is supported on the following targets:

x86_64-unknown-linux-gnu
See the Clang DataFlowSanitizer documentation for more details.

KernelAddressSanitizer

KernelAddressSanitizer (KASAN) is a freestanding version of AddressSanitizer which is suitable for detecting memory errors in programs which do not have a runtime environment, such as operating system kernels. KernelAddressSanitizer requires manual implementation of the underlying functions used for tracking KernelAddressSanitizer state.

KernelAddressSanitizer is supported on the following targets:

aarch64-unknown-none
riscv64gc-unknown-none-elf
riscv64imac-unknown-none-elf
x86_64-unknown-none
See the Linux Kernel's KernelAddressSanitizer documentation for more details.

LeakSanitizer

LeakSanitizer is run-time memory leak detector.

LeakSanitizer is supported on the following targets:

aarch64-unknown-linux-gnu
x86_64-apple-darwin
x86_64-unknown-linux-gnu
See the Clang LeakSanitizer documentation for more details.

MemorySanitizer

MemorySanitizer is detector of uninitialized reads.

MemorySanitizer is supported on the following targets:

aarch64-unknown-linux-gnu
x86_64-unknown-freebsd
x86_64-unknown-linux-gnu
MemorySanitizer requires all program code to be instrumented. C/C++ dependencies need to be recompiled using Clang with -fsanitize=memory option. Failing to achieve that will result in false positive reports.

See the Clang MemorySanitizer documentation for more details.

Example

Detecting the use of uninitialized memory. The -Zbuild-std flag rebuilds and instruments the standard library, and is strictly necessary for the correct operation of the tool. The -Zsanitizer-memory-track-origins enables tracking of the origins of uninitialized memory:

use std::mem::MaybeUninit;

fn main() {
    unsafe {
        let a = MaybeUninit::<[usize; 4]>::uninit();
        let a = a.assume_init();
        println!("{}", a[2]);
    }
}
$ export \
  RUSTFLAGS='-Zsanitizer=memory -Zsanitizer-memory-track-origins' \
  RUSTDOCFLAGS='-Zsanitizer=memory -Zsanitizer-memory-track-origins'
$ cargo clean
$ cargo run -Zbuild-std --target x86_64-unknown-linux-gnu
==9416==WARNING: MemorySanitizer: use-of-uninitialized-value
    #0 0x560c04f7488a in core::fmt::num::imp::fmt_u64::haa293b0b098501ca $RUST/build/x86_64-unknown-linux-gnu/stage1/lib/rustlib/src/rust/src/libcore/fmt/num.rs:202:16
...
  Uninitialized value was stored to memory at
    #0 0x560c04ae898a in __msan_memcpy.part.0 $RUST/src/llvm-project/compiler-rt/lib/msan/msan_interceptors.cc:1558:3
    #1 0x560c04b2bf88 in memory::main::hd2333c1899d997f5 $CWD/src/main.rs:6:16

  Uninitialized value was created by an allocation of 'a' in the stack frame of function '_ZN6memory4main17hd2333c1899d997f5E'
    #0 0x560c04b2bc50 in memory::main::hd2333c1899d997f5 $CWD/src/main.rs:3
MemTagSanitizer

MemTagSanitizer detects a similar class of errors as AddressSanitizer and HardwareAddressSanitizer, but with lower overhead suitable for use as hardening for production binaries.

MemTagSanitizer is supported on the following targets:

aarch64-linux-android
aarch64-unknown-linux-gnu
MemTagSanitizer requires hardware support and the mte target feature. To enable this target feature compile with -C target-feature="+mte".

See the LLVM MemTagSanitizer documentation for more details.

SafeStack

SafeStack provides backward edge control flow protection by separating the stack into data which is only accessed safely (the safe stack) and all other data (the unsafe stack).

SafeStack can be enabled with the -Zsanitizer=safestack option and is supported on the following targets:

x86_64-unknown-linux-gnu
See the Clang SafeStack documentation for more details.

ShadowCallStack

ShadowCallStack provides backward edge control flow protection by storing a function's return address in a separately allocated 'shadow call stack' and loading the return address from that shadow call stack. AArch64 and RISC-V both have a platform register defined in their ABIs, which is x18 and x3/gp respectively, that can optionally be reserved for this purpose. Software support from the operating system and runtime may be required depending on the target platform which is detailed in the remaining section. See the Clang ShadowCallStack documentation for more details.

ShadowCallStack can be enabled with -Zsanitizer=shadow-call-stack option and is supported on the following targets:

AArch64 family

ShadowCallStack requires the use of the ABI defined platform register, x18, which is required for code generation purposes. When x18 is not reserved, and is instead used as a scratch register subsequently, enabling ShadowCallStack would lead to undefined behaviour due to corruption of return address or invalid memory access when the instrumentation restores return register to the link register lr from the already clobbered x18 register. In other words, code that is calling into or called by functions instrumented with ShadowCallStack must reserve the x18 register or preserve its value.

aarch64-linux-android and aarch64-unknown-fuchsia/aarch64-fuchsia

This target already reserves the x18 register. A runtime must be provided by the application or operating system. If bionic is used on this target, the software support is provided. Otherwise, a runtime needs to prepare a memory region and points x18 to the region which serves as the shadow call stack.

aarch64-unknown-none

In addition to support from a runtime by the application or operating system, the -Zfixed-x18 flag is also mandatory.

RISC-V 64 family

ShadowCallStack uses either the gp register for software shadow stack, also known as x3, or the ssp register if Zicfiss extension is available. gp/x3 is currently always reserved and available for ShadowCallStack instrumentation, and ssp in case of Zicfiss is only accessible through its dedicated shadow stack instructions.

Support from the runtime and operating system is required when gp/x3 is used for software shadow stack. A runtime must prepare a memory region and point gp/x3 to the region before executing the code.

The following targets support ShadowCallStack.

riscv64imac-unknown-none-elf
riscv64gc-unknown-none-elf
riscv64gc-unknown-fuchsia
ThreadSanitizer

ThreadSanitizer is a data race detection tool. It is supported on the following targets:

aarch64-apple-darwin
aarch64-unknown-linux-gnu
x86_64-apple-darwin
x86_64-unknown-freebsd
x86_64-unknown-linux-gnu
To work correctly ThreadSanitizer needs to be "aware" of all synchronization operations in a program. It generally achieves that through combination of library interception (for example synchronization performed through pthread_mutex_lock / pthread_mutex_unlock) and compile time instrumentation (e.g. atomic operations). Using it without instrumenting all the program code can lead to false positive reports.

ThreadSanitizer does not support atomic fences std::sync::atomic::fence, nor synchronization performed using inline assembly code.

See the Clang ThreadSanitizer documentation for more details.

Example

static mut A: usize = 0;

fn main() {
    let t = std::thread::spawn(|| {
        unsafe { A += 1 };
    });
    unsafe { A += 1 };

    t.join().unwrap();
}
$ export RUSTFLAGS=-Zsanitizer=thread RUSTDOCFLAGS=-Zsanitizer=thread
$ cargo run -Zbuild-std --target x86_64-unknown-linux-gnu
==================
WARNING: ThreadSanitizer: data race (pid=10574)
  Read of size 8 at 0x5632dfe3d030 by thread T1:
    #0 example::main::_$u7b$$u7b$closure$u7d$$u7d$::h23f64b0b2f8c9484 ../src/main.rs:5:18 (example+0x86cec)
    ...

  Previous write of size 8 at 0x5632dfe3d030 by main thread:
    #0 example::main::h628ffc6626ed85b2 /.../src/main.rs:7:14 (example+0x868c8)
    ...
    #11 main <null> (example+0x86a1a)

  Location is global 'example::A::h43ac149ddf992709' of size 8 at 0x5632dfe3d030 (example+0x000000bd9030)
RealtimeSanitizer

RealtimeSanitizer detects non-deterministic execution time calls in real-time contexts. Functions marked with the #[sanitize(realtime = "nonblocking")] attribute are considered real-time functions. When RTSan detects a call to a function with a non-deterministic execution time, like malloc or free while in a real-time context, it reports an error.

Besides "nonblocking" the attribute can also be used with "blocking" and "caller".

"blocking" allows the programmer to mark their own functions as having a non-deterministic execution time. When reaching such a function while in a real-time context a violation will be reported. A typical use case is a userland spinlock.
functions marked with "caller" will be sanitized if they were called from a real-time context. If no attribute is set, this is the default. Between entering a "nonblocking" function and exiting that function again the program will get sanitized.
The santizer checks can be disabled using the external functions __rtsan_disable() and __rtsan_enable(). Each call to __rtsan_disable() must be paired with one following call to __rtsan_enable(), otherwise the behaviour is undefined.

unsafe extern "C" {
  fn __rtsan_disable();
  fn __rtsan_enable();
}
// in a real-time context
#[cfg(debug_assertions)]
{
    unsafe { __rtsan_disable() };
    log!("logging xyz");
    unsafe { __rtsan_enable() };
}
See the Clang RealtimeSanitizer documentation for more details.

Example

#![feature(sanitize)]
#[sanitize(realtime = "nonblocking")]
fn real_time() {
  let vec = vec![0, 1, 2]; // call to malloc is detected and reported as an error
}
==8670==ERROR: RealtimeSanitizer: unsafe-library-call
Intercepted call to real-time unsafe function `malloc` in real-time context!
    #0 0x00010107b0d8 in malloc rtsan_interceptors_posix.cpp:792
    #1 0x000100d94e70 in alloc::alloc::Global::alloc_impl::h9e1fc3206c868eea+0xa0 (realtime_vec:arm64+0x100000e70)
    #2 0x000100d94d90 in alloc::alloc::exchange_malloc::hd45b5788339eb5c8+0x48 (realtime_vec:arm64+0x100000d90)
    #3 0x000100d95020 in realtime_vec::main::hea6bd69b03eb9ca1+0x24 (realtime_vec:arm64+0x100001020)
    #4 0x000100d94a28 in core::ops::function::FnOnce::call_once::h493b6cb9dd87d87c+0xc (realtime_vec:arm64+0x100000a28)
    #5 0x000100d949b8 in std::sys::backtrace::__rust_begin_short_backtrace::hfcddb06c73c19eea+0x8 (realtime_vec:arm64+0x1000009b8)
    #6 0x000100d9499c in std::rt::lang_start::_$u7b$$u7b$closure$u7d$$u7d$::h202288c05a2064f0+0xc (realtime_vec:arm64+0x10000099c)
    #7 0x000100d9fa34 in std::rt::lang_start_internal::h6c763158a05ac05f+0x6c (realtime_vec:arm64+0x10000ba34)
    #8 0x000100d94980 in std::rt::lang_start::h1c29cc56df0598b4+0x38 (realtime_vec:arm64+0x100000980)
    #9 0x000100d95118 in main+0x20 (realtime_vec:arm64+0x100001118)
    #10 0x000183a46b94 in start+0x17b8 (dyld:arm64+0xfffffffffff3ab94)

SUMMARY: RealtimeSanitizer: unsafe-library-call rtsan_interceptors_posix.cpp:792 in malloc
Instrumentation of external dependencies and std

The sanitizers to varying degrees work correctly with partially instrumented code. On the one extreme is LeakSanitizer that doesn't use any compile time instrumentation, on the other is MemorySanitizer that requires that all program code to be instrumented (failing to achieve that will inevitably result in false positives).

It is strongly recommended to combine sanitizers with recompiled and instrumented standard library, for example using cargo -Zbuild-std functionality.

Working with other languages

Sanitizers rely on compiler runtime libraries to function properly. Rust links in its own compiler runtime which might conflict with runtimes required by languages such as C++. Since Rust's runtime doesn't always contain the symbols required by C++ instrumented code, you might need to skip linking it so another runtime can be linked instead.

A separate unstable option -Zexternal-clangrt can be used to make rustc skip linking the compiler runtime for the sanitizer. This will require you to link in an external runtime, such as from clang instead.

Build scripts and procedural macros

Use of sanitizers together with build scripts and procedural macros is technically possible, but in almost all cases it would be best avoided. This is especially true for procedural macros which would require an instrumented version of rustc.

In more practical terms when using cargo always remember to pass --target flag, so that rustflags will not be applied to build scripts and procedural macros.

Symbolizing the Reports

Sanitizers produce symbolized stacktraces when llvm-symbolizer binary is in PATH.

Additional Information

Sanitizers project page
AddressSanitizer in Clang
ControlFlowIntegrity in Clang
DataFlowSanitizer in Clang
HWAddressSanitizer in Clang
Linux Kernel's KernelAddressSanitizer documentation
LeakSanitizer in Clang
MemorySanitizer in Clang
MemTagSanitizer in LLVM
ThreadSanitizer in Clang
RealtimeSanitizer in Clang
self-profile

The -Zself-profile compiler flag enables rustc's internal profiler. When enabled, the compiler will output three binary files in the specified directory (or the current working directory if no directory is specified). These files can be analyzed by using the tools in the measureme repository.

To control the data recorded in the trace files, use the -Zself-profile-events flag.

For example:

First, run a compilation session and provide the -Zself-profile flag:

$ rustc --crate-name foo -Zself-profile
This will generate three files in the working directory such as:

foo-1234.events
foo-1234.string_data
foo-1234.string_index
Where foo is the name of the crate and 1234 is the process id of the rustc process.

To get a summary of where the compiler is spending its time:

$ ../measureme/target/release/summarize summarize foo-1234
To generate a flamegraph of the same data:

$ ../measureme/target/release/inferno foo-1234
To dump the event data in a Chromium-profiler compatible format:

$ ../measureme/target/release/crox foo-1234
For more information, consult the measureme documentation.

self-profile-events

The -Zself-profile-events compiler flag controls what events are recorded by the self-profiler when it is enabled via the -Zself-profile flag.

This flag takes a comma delimited list of event types to record.

For example:

$ rustc -Zself-profile -Zself-profile-events=default,args
Event types

query-provider

Traces each query used internally by the compiler.
generic-activity

Traces other parts of the compiler not covered by the query system.
query-cache-hit

Adds tracing information that records when the in-memory query cache is "hit" and does not need to re-execute a query which has been cached.
Disabled by default because this significantly increases the trace file size.
query-blocked

Tracks time that a query tries to run but is blocked waiting on another thread executing the same query to finish executing.
Query blocking only occurs when the compiler is built with parallel mode support.
incr-cache-load

Tracks time that is spent loading and deserializing query results from the incremental compilation on-disk cache.
query-keys

Adds a serialized representation of each query's query key to the tracing data.
Disabled by default because this significantly increases the trace file size.
function-args

Adds additional tracing data to some generic-activity events.
Disabled by default for parity with query-keys.
llvm

Adds tracing information about LLVM passes and codegeneration.
Disabled by default because this significantly increases the trace file size.
Event synonyms

none

Disables all events. Equivalent to the self-profiler being disabled.
default

The default set of events which stikes a balance between providing detailed tracing data and adding additional overhead to the compilation.
args

Equivalent to query-keys and function-args.
all

Enables all events.
Examples

Enable the profiler and capture the default set of events (both invocations are equivalent):

$ rustc -Zself-profile
$ rustc -Zself-profile -Zself-profile-events=default
Enable the profiler and capture the default events and their arguments:

$ rustc -Zself-profile -Zself-profile-events=default,args
shell-argfiles

The -Zshell-argfiles compiler flag allows argfiles to be parsed using POSIX "shell-style" quoting. When enabled, the compiler will use shlex to parse the arguments from argfiles specified with @shell:<path>.

Because this feature controls the parsing of input arguments, the -Zshell-argfiles flag must be present before the argument specifying the shell-style argument file.

small-data-threshold

This flag controls the maximum static variable size that may be included in the "small data sections" (.sdata, .sbss) supported by some architectures (RISCV, MIPS, M68K, Hexagon). Can be set to 0 to disable the use of small data sections.

## small_data_threshold

none (SmallDataThresholdSupport::None) for no support
default-for-arch (SmallDataThresholdSupport::DefaultForArch) which is automatically translated into an appropriate value for the target.
llvm-module-flag=<flag_name> (SmallDataThresholdSupport::LlvmModuleFlag) for specifying the threshold via an LLVM module flag
llvm-arg=<arg_name> (SmallDataThresholdSupport::LlvmArg) for specifying the threshold via an LLVM argument.
split-dwarf-out-dir

On systems which use DWARF debug info this flag causes .dwo files produced by -C split-debuginfo to be written to the specified directory rather than placed next to the object files. This is mostly useful if you have a build system which needs to control where to find compile outputs without running the compiler and have to put your .dwo files in a separate directory.

src-hash-algorithm

The tracking issue for this feature is: #70401.

The -Z src-hash-algorithm compiler flag controls which algorithm is used when hashing each source file. The hash is stored in the debug info and can be used by a debugger to verify the source code matches the executable.

Supported hash algorithms are: md5, sha1, and sha256. Note that not all hash algorithms are supported by all debug info formats.

By default, the compiler chooses the hash algorithm based on the target specification.

temps-dir

The -Ztemps-dir compiler flag specifies the directory to write the intermediate files in. If not set, the output directory is used. This option is useful if you are running more than one instance of rustc (e.g. with different --crate-type settings), and you need to make sure they are not overwriting each other's intermediate files. No files are kept unless -C save-temps=yes is also set.

-Z terminal-urls

The tracking feature for this issue is #125586

This flag takes either a boolean or the string "auto".

When enabled, use the OSC 8 hyperlink terminal specification to print hyperlinks in the compiler output. Use "auto" to try and autodetect whether the terminal emulator supports hyperlinks. Currently, "auto" only enables hyperlinks if COLORTERM=truecolor and TERM=xterm-256color.

tiny-const-eval-limit

The -Ztiny-const-eval-limit compiler flag sets a tiny, non-configurable limit for const eval. This flag should only be used by const eval tests in the rustc test suite.

## tls_model

The tracking issue for this feature is: None.

Option -Z tls-model controls TLS model used to generate code for accessing #[thread_local] static items.

Supported values for this option are:

global-dynamic - General Dynamic TLS Model (alternatively called Global Dynamic) is the most general option usable in all circumstances, even if the TLS data is defined in a shared library loaded at runtime and is accessed from code outside of that library. This is the default for most targets.
local-dynamic - model usable if the TLS data is only accessed from the shared library or executable it is defined in. The TLS data may be in a library loaded after startup (via dlopen).
initial-exec - model usable if the TLS data is defined in the executable or in a shared library loaded at program startup. The TLS data must not be in a library loaded after startup (via dlopen).
local-exec - model usable only if the TLS data is defined directly in the executable, but not in a shared library, and is accessed only from that executable.
emulated - Uses thread-specific data keys to implement emulated TLS. It is like using a general-dynamic TLS model for all modes.
rustc and LLVM may use a more optimized model than specified if they know that we are producing an executable rather than a library, or that the static item is private enough.

track-diagnostics

This feature is perma-unstable and has no tracking issue.

This flag prints the source code span in the compiler where a diagnostic was generated, respecting #[track_caller]. Note that this may be different from the place it was emitted. For full documentation, see the rustc-dev-guide.

treat-err-as-bug

This feature is perma-unstable and has no tracking issue.

This flag converts the selected error to a bug! call, exiting the compiler immediately and allowing you to generate a backtrace of where the error occurred. For full documentation, see the rustc-dev-guide.

Note that the compiler automatically sets RUST_BACKTRACE=1 for itself, and so you do not need to set it yourself when using this flag.

ub-checks

The tracking issue for this feature is: #123499.

The -Zub-checks compiler flag enables additional runtime checks that detect some causes of Undefined Behavior at runtime. By default, -Zub-checks flag inherits the value of -Cdebug-assertions.

All checks are generated on a best-effort basis; even if we have a check implemented for some cause of Undefined Behavior, it may be possible for the check to not fire. If a dependency is compiled with -Zub-checks=no but the final binary or library is compiled with -Zub-checks=yes, UB checks reached by the dependency are likely to be optimized out.

When -Zub-checks detects UB, a non-unwinding panic is produced. That means that we will not unwind the stack and will not call any Drop impls, but we will execute the configured panic hook. We expect that unsafe code has been written which relies on code not unwinding which may have UB checks inserted. Ergo, an unwinding panic could easily turn works-as-intended UB into a much bigger problem. Calling the panic hook theoretically has the same implications, but we expect that the standard library panic hook will be stateless enough to be always called, and that if a user has configured a panic hook that the hook may be very helpful to debugging the detected UB.

unsound-mir-opts

The -Zunsound-mir-opts compiler flag enables MIR optimization passes which can cause unsound behavior. This flag should only be used by MIR optimization tests in the rustc test suite.

verbose-asm

The tracking issue for this feature is: #126802.

This enables passing -Zverbose-asm to get contextual comments added by LLVM.

Sample code:

#[no_mangle]
pub fn foo(a: i32, b: i32) -> i32 {
    a + b
}
Default output:

foo:
        push    rax
        add     edi, esi
        mov     dword ptr [rsp + 4], edi
        seto    al
        jo      .LBB0_2
        mov     eax, dword ptr [rsp + 4]
        pop     rcx
        ret
.LBB0_2:
        lea     rdi, [rip + .L__unnamed_1]
        mov     rax, qword ptr [rip + core::panicking::panic_const::panic_const_add_overflow::h9c85248fe0d735b2@GOTPCREL]
        call    rax

.L__unnamed_2:
        .ascii  "/app/example.rs"

.L__unnamed_1:
        .quad   .L__unnamed_2
        .asciz  "\017\000\000\000\000\000\000\000\004\000\000\000\005\000\000"
With -Zverbose-asm:

foo:                                    # @foo
# %bb.0:
        push    rax
        add     edi, esi
        mov     dword ptr [rsp + 4], edi        # 4-byte Spill
        seto    al
        jo      .LBB0_2
# %bb.1:
        mov     eax, dword ptr [rsp + 4]        # 4-byte Reload
        pop     rcx
        ret
.LBB0_2:
        lea     rdi, [rip + .L__unnamed_1]
        mov     rax, qword ptr [rip + core::panicking::panic_const::panic_const_add_overflow::h9c85248fe0d735b2@GOTPCREL]
        call    rax
                                        # -- End function
.L__unnamed_2:
        .ascii  "/app/example.rs"

.L__unnamed_1:
        .quad   .L__unnamed_2
        .asciz  "\017\000\000\000\000\000\000\000\004\000\000\000\005\000\000"

                                        # DW_AT_external
virtual-function-elimination

This option controls whether LLVM runs the Virtual Function Elimination (VFE) optimization. This optimization in only available with LTO, so this flag can only be passed if -Clto is also passed.

VFE makes it possible to remove functions from vtables that are never dynamically called by the rest of the code. Without this flag, LLVM makes the really conservative assumption, that if any function in a vtable is called, no function that is referenced by this vtable can be removed. With this flag additional information are given to LLVM, so that it can determine which functions are actually called and remove the unused functions.

Limitations

At the time of writing this flag may remove vtable functions too eagerly. One such example is in this code:

trait Foo { fn foo(&self) { println!("foo") } }

impl Foo for usize {}

pub struct FooBox(Box<dyn Foo>);

pub fn make_foo() -> FooBox { FooBox(Box::new(0)) }

#[inline]
pub fn f(a: FooBox) { a.0.foo() }
In the above code the Foo trait is private, so an assumption is made that its functions can only be seen/called from the current crate and can therefore get optimized out, if unused. However, with make_foo you can produce a wrapped dyn Foo type outside of the current crate, which can then be used in f. Due to inlining of f, Foo::foo can then be called from a foreign crate. This can lead to miscompilations.

wasm-c-abi

This option controls whether Rust uses the spec-compliant C ABI when compiling for the wasm32-unknown-unknown target.

This makes it possible to be ABI-compatible with all other spec-compliant Wasm targets like wasm32-wasip1.

This compiler flag is perma-unstable, as it will be enabled by default in the future with no option to fall back to the old non-spec-compliant ABI.
