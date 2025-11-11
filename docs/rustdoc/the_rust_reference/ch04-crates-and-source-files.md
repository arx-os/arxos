# Crates and source files
[crate.syntax]
Syntax
Crate →
    InnerAttribute*
    Item*

Show syntax diagrams

Note

Although Rust, like any other language, can be implemented by an interpreter as well as a compiler, the only existing implementation is a compiler, and the language has always been designed to be compiled. For these reasons, this section assumes a compiler.
[crate.compile-time]
Rust’s semantics obey a phase distinction between compile-time and run-time.1 Semantic rules that have a static interpretation govern the success or failure of compilation, while semantic rules that have a dynamic interpretation govern the behavior of the program at run-time.
[crate.unit]
The compilation model centers on artifacts called crates. Each compilation processes a single crate in source form, and if successful, produces a single crate in binary form: either an executable or some sort of library.2
[crate.module]
A crate is a unit of compilation and linking, as well as versioning, distribution, and runtime loading. A crate contains a tree of nested module scopes. The top level of this tree is a module that is anonymous (from the point of view of paths within the module) and any item within a crate has a canonical module path denoting its location within the crate’s module tree.
[crate.input-source]
The Rust compiler is always invoked with a single source file as input, and always produces a single output crate. The processing of that source file may result in other source files being loaded as modules. Source files have the extension .rs.
[crate.module-def]
A Rust source file describes a module, the name and location of which — in the module tree of the current crate — are defined from outside the source file: either by an explicit Module item in a referencing source file, or by the name of the crate itself.
[crate.inline-module]
Every source file is a module, but not every module needs its own source file: module definitions can be nested within one file.
[crate.items]
Each source file contains a sequence of zero or more Item definitions, and may optionally begin with any number of attributes that apply to the containing module, most of which influence the behavior of the compiler.
[crate.attributes]
The anonymous crate module can have additional attributes that apply to the crate as a whole.
Note

The file’s contents may be preceded by a shebang.
// Specify the crate name.
#![crate_name = "projx"]

// Specify the type of output artifact.
#![crate_type = "lib"]

// Turn on a warning.
// This can be done in any module, not just the anonymous crate module.
#![warn(non_camel_case_types)]
[crate.main]
Main Functions
[crate.main.general]
A crate that contains a main function can be compiled to an executable.
[crate.main.restriction]
If a main function is present, it must take no arguments, must not declare any trait or lifetime bounds, must not have any where clauses, and its return type must implement the Termination trait.
fn main() {}
fn main() -> ! {
    std::process::exit(0);
}
fn main() -> impl std::process::Termination {
    std::process::ExitCode::SUCCESS
}
[crate.main.import]
The main function may be an import, e.g. from an external crate or from the current one.
mod foo {
    pub fn bar() {
        println!("Hello, world!");
    }
}
use foo::bar as main;
Note

Types with implementations of Termination in the standard library include:

()
!
Infallible
ExitCode
Result<T, E> where T: Termination, E: Debug
[crate.uncaught-foreign-unwinding]
Uncaught foreign unwinding
When a “foreign” unwind (e.g. an exception thrown from C++ code, or a panic! in Rust code using a different panic handler) propagates beyond the main function, the process will be safely terminated. This may take the form of an abort, in which case it is not guaranteed that any Drop calls will be executed, and the error output may be less informative than if the runtime had been terminated by a “native” Rust panic.
For more information, see the panic documentation.
[crate.no_main]
The no_main attribute
The no_main attribute may be applied at the crate level to disable emitting the main symbol for an executable binary. This is useful when some other object being linked to defines main.
[crate.crate_name]
The crate_name attribute
[crate.crate_name.general]
The crate_name attribute may be applied at the crate level to specify the name of the crate with the MetaNameValueStr syntax.
#![crate_name = "mycrate"]
[crate.crate_name.restriction]
The crate name must not be empty, and must only contain Unicode alphanumeric or _ (U+005F) characters.
This distinction would also exist in an interpreter. Static checks like syntactic analysis, type checking, and lints should happen before the program is executed regardless of when it is executed. ↩

A crate is somewhat analogous to an assembly in the ECMA-335 CLI model, a library in the SML/NJ Compilation Manager, a unit in the Owens and Flatt module system, or a configuration in Mesa. ↩

[cfg]
