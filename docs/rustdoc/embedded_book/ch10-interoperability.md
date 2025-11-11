# Interoperability
Interoperability between Rust and C code is always dependent on transforming data between the two languages. For this purpose, there is a dedicated module in the stdlib called std::ffi.

std::ffi provides type definitions for C primitive types, such as char, int, and long. It also provides some utility for converting more complex types such as strings, mapping both &str and String to C types that are easier and safer to handle.

As of Rust 1.30, functionalities of std::ffi are available in either core::ffi or alloc::ffi depending on whether or not memory allocation is involved. The cty crate and the cstr_core crate also offer similar functionalities.

Rust type	Intermediate	C type
String	CString	char *
&str	CStr	const char *
()	c_void	void
u32 or u64	c_uint	unsigned int
etc	...	...
A value of a C primitive type can be used as one of the corresponding Rust type and vice versa, since the former is simply a type alias of the latter. For example, the following code compiles on platforms where unsigned int is 32-bit long.

fn foo(num: u32) {
    let c_num: c_uint = num;
    let r_num: u32 = c_num;
}
Interoperability with other build systems

A common requirement for including Rust in your embedded project is combining Cargo with your existing build system, such as make or cmake.

We are collecting examples and use cases for this on our issue tracker in issue #61.

Interoperability with RTOSs

Integrating Rust with an RTOS such as FreeRTOS or ChibiOS is still a work in progress; especially calling RTOS functions from Rust can be tricky.

We are collecting examples and use cases for this on our issue tracker in issue #62.

## A little C with your Rust

Using C or C++ inside of a Rust project consists of two major parts:

Wrapping the exposed C API for use with Rust
Building your C or C++ code to be integrated with the Rust code
As C++ does not have a stable ABI for the Rust compiler to target, it is recommended to use the C ABI when combining Rust with C or C++.

Defining the interface

Before consuming C or C++ code from Rust, it is necessary to define (in Rust) what data types and function signatures exist in the linked code. In C or C++, you would include a header (.h or .hpp) file which defines this data. In Rust, it is necessary to either manually translate these definitions to Rust, or use a tool to generate these definitions.

First, we will cover manually translating these definitions from C/C++ to Rust.

Wrapping C functions and Datatypes

Typically, libraries written in C or C++ will provide a header file defining all types and functions used in public interfaces. An example file may look like this:

/* File: cool.h */
typedef struct CoolStruct {
    int x;
    int y;
} CoolStruct;

void cool_function(int i, char c, CoolStruct* cs);
When translated to Rust, this interface would look as such:

/* File: cool_bindings.rs */
#[repr(C)]
pub struct CoolStruct {
    pub x: cty::c_int,
    pub y: cty::c_int,
}

extern "C" {
    pub fn cool_function(
        i: cty::c_int,
        c: cty::c_char,
        cs: *mut CoolStruct
    );
}
Let's take a look at this definition one piece at a time, to explain each of the parts.

#[repr(C)]
pub struct CoolStruct { ... }
By default, Rust does not guarantee order, padding, or the size of data included in a struct. In order to guarantee compatibility with C code, we include the #[repr(C)] attribute, which instructs the Rust compiler to always use the same rules C does for organizing data within a struct.

pub x: cty::c_int,
pub y: cty::c_int,
Due to the flexibility of how C or C++ defines an int or char, it is recommended to use primitive data types defined in cty, which will map types from C to types in Rust.

extern "C" { pub fn cool_function( ... ); }
This statement defines the signature of a function that uses the C ABI, called cool_function. By defining the signature without defining the body of the function, the definition of this function will need to be provided elsewhere, or linked into the final library or binary from a static library.

    i: cty::c_int,
    c: cty::c_char,
    cs: *mut CoolStruct
Similar to our datatype above, we define the datatypes of the function arguments using C-compatible definitions. We also retain the same argument names, for clarity.

We have one new type here, *mut CoolStruct. As C does not have a concept of Rust's references, which would look like this: &mut CoolStruct, we instead have a raw pointer. As dereferencing this pointer is unsafe, and the pointer may in fact be a null pointer, care must be taken to ensure the guarantees typical of Rust when interacting with C or C++ code.

Automatically generating the interface

Rather than manually generating these interfaces, which may be tedious and error prone, there is a tool called bindgen which will perform these conversions automatically. For instructions of the usage of bindgen, please refer to the bindgen user's manual, however the typical process consists of the following:

Gather all C or C++ headers defining interfaces or datatypes you would like to use with Rust.
Write a bindings.h file, which #include "..."'s each of the files you gathered in step one.
Feed this bindings.h file, along with any compilation flags used to compile your code into bindgen. Tip: use Builder.ctypes_prefix("cty") / --ctypes-prefix=cty and Builder.use_core() / --use-core to make the generated code #![no_std] compatible.
bindgen will produce the generated Rust code to the output of the terminal window. This output may be piped to a file in your project, such as bindings.rs. You may use this file in your Rust project to interact with C/C++ code compiled and linked as an external library. Tip: don't forget to use the cty crate if your types in the generated bindings are prefixed with cty.
Building your C/C++ code

As the Rust compiler does not directly know how to compile C or C++ code (or code from any other language, which presents a C interface), it is necessary to compile your non-Rust code ahead of time.

For embedded projects, this most commonly means compiling the C/C++ code to a static archive (such as cool-library.a), which can then be combined with your Rust code at the final linking step.

If the library you would like to use is already distributed as a static archive, it is not necessary to rebuild your code. Just convert the provided interface header file as described above, and include the static archive at compile/link time.

If your code exists as a source project, it will be necessary to compile your C/C++ code to a static library, either by triggering your existing build system (such as make, CMake, etc.), or by porting the necessary compilation steps to use a tool called the cc crate. For both of these steps, it is necessary to use a build.rs script.

Rust build.rs build scripts

A build.rs script is a file written in Rust syntax, that is executed on your compilation machine, AFTER dependencies of your project have been built, but BEFORE your project is built.

The full reference may be found here. build.rs scripts are useful for generating code (such as via bindgen), calling out to external build systems such as Make, or directly compiling C/C++ through use of the cc crate.

Triggering external build systems

For projects with complex external projects or build systems, it may be easiest to use std::process::Command to "shell out" to your other build systems by traversing relative paths, calling a fixed command (such as make library), and then copying the resulting static library to the proper location in the target build directory.

While your crate may be targeting a no_std embedded platform, your build.rs executes only on machines compiling your crate. This means you may use any Rust crates which will run on your compilation host.

Building C/C++ code with the cc crate

For projects with limited dependencies or complexity, or for projects where it is difficult to modify the build system to produce a static library (rather than a final binary or executable), it may be easier to instead utilize the cc crate, which provides an idiomatic Rust interface to the compiler provided by the host.

In the simplest case of compiling a single C file as a dependency to a static library, an example build.rs script using the cc crate would look like this:

fn main() {
    cc::Build::new()
        .file("src/foo.c")
        .compile("foo");
}
The build.rs is placed at the root of the package. Then cargo build will compile and execute it before the build of the package. A static archive named libfoo.a is generated and placed in the target directory.

## A little Rust with your C

Using Rust code inside a C or C++ project mostly consists of two parts.

Creating a C-friendly API in Rust
Embedding your Rust project into an external build system
Apart from cargo and meson, most build systems don't have native Rust support. So you're most likely best off just using cargo for compiling your crate and any dependencies.

Setting up a project

Create a new cargo project as usual.

There are flags to tell cargo to emit a systems library, instead of its regular rust target. This also allows you to set a different output name for your library, if you want it to differ from the rest of your crate.

[lib]
name = "your_crate"
crate-type = ["cdylib"]      # Creates dynamic lib
# crate-type = ["staticlib"] # Creates static lib
Building a C API

Because C++ has no stable ABI for the Rust compiler to target, we use C for any interoperability between different languages. This is no exception when using Rust inside of C and C++ code.

#[no_mangle]

The Rust compiler mangles symbol names differently than native code linkers expect. As such, any function that Rust exports to be used outside of Rust needs to be told not to be mangled by the compiler.

extern "C"

By default, any function you write in Rust will use the Rust ABI (which is also not stabilized). Instead, when building outwards facing FFI APIs we need to tell the compiler to use the system ABI.

Depending on your platform, you might want to target a specific ABI version, which are documented here.

Putting these parts together, you get a function that looks roughly like this.

#[no_mangle]
pub extern "C" fn rust_function() {

}
Just as when using C code in your Rust project you now need to transform data from and to a form that the rest of the application will understand.

Linking and greater project context.

So then, that's one half of the problem solved. How do you use this now?

This very much depends on your project and/or build system

cargo will create a my_lib.so/my_lib.dll or my_lib.a file, depending on your platform and settings. This library can simply be linked by your build system.

However, calling a Rust function from C requires a header file to declare the function signatures.

Every function in your Rust-ffi API needs to have a corresponding header function.

#[no_mangle]
pub extern "C" fn rust_function() {}
would then become

void rust_function();
etc.

There is a tool to automate this process, called cbindgen which analyses your Rust code and then generates headers for your C and C++ projects from it.

At this point, using the Rust functions from C is as simple as including the header and calling them!

#include "my-rust-project.h"
rust_function();
