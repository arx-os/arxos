# Command-line Arguments
-h/--help: get help
--cfg: configure the compilation environment
--check-cfg: configure compile-time checking of conditional compilation
-L: add a directory to the library search path
-l: link the generated crate to a native library
Linking modifiers: whole-archive
Linking modifiers: bundle
Linking modifiers: verbatim
--crate-type: a list of types of crates for the compiler to emit
--crate-name: specify the name of the crate being built
--edition: specify the edition to use
--emit: specifies the types of output files to generate
Custom paths for individual emit kinds
Emitting to stdout
--print: print compiler information
-g: include debug information
-O: optimize your code
-o: filename of the output
--out-dir: directory to write the output in
--explain: provide a detailed explanation of an error message
--test: build a test harness
--target: select a target triple to build
-W: set lint warnings
--force-warn: force a lint to warn
-A: set lint allowed
-D: set lint denied
-F: set lint forbidden
-Z: set unstable options
--cap-lints: set the most restrictive lint level
-C/--codegen: code generation options
-V/--version: print a version
-v/--verbose: use verbose output
--extern: specify where an external library is located
--sysroot: Override the system root
--error-format: control how errors are produced
--color: configure coloring of output
--diagnostic-width: specify the terminal width for diagnostics
--remap-path-prefix: remap source paths in output
--json: configure json messages printed by the compiler
@path: load command-line flags from a path
## Print Options
crate-name
file-names
sysroot
target-libdir
host-tuple
cfg
target-list
target-cpus
target-features
relocation-models
code-models
tls-models
native-static-libs
link-args
deployment-target
## Codegen Options
ar
code-model
codegen-units
collapse-macro-debuginfo
control-flow-guard
debug-assertions
debuginfo
default-linker-libraries
dlltool
dwarf-version
embed-bitcode
extra-filename
force-frame-pointers
force-unwind-tables
incremental
inline-threshold
instrument-coverage
link-arg
link-args
link-dead-code
link-self-contained
Implementation notes
linker
linker-features
Implementation notes
linker-flavor
linker-plugin-lto
llvm-args
lto
metadata
no-prepopulate-passes
no-redzone
no-stack-check
no-vectorize-loops
no-vectorize-slp
opt-level
overflow-checks
panic
passes
prefer-dynamic
profile-generate
profile-use
relocation-model
Primary relocation models
Special relocation models
Linking effects
relro-level
remark
rpath
save-temps
soft-float
split-debuginfo
strip
symbol-mangling-version
target-cpu
target-feature
tune-cpu
