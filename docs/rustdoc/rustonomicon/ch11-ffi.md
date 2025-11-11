# FFI
use std::ptr;

#[link(name = "readline")]
unsafe extern {
    static mut rl_prompt: *const libc::c_char;
}

fn main() {
    let prompt = CString::new("[my-awesome-shell] $").unwrap();
    unsafe {
        rl_prompt = prompt.as_ptr();

        println!("{:?}", rl_prompt);

        rl_prompt = ptr::null();
    }
}
Note that all interaction with a static mut is unsafe, both reading and writing. Dealing with global mutable state requires a great deal of care.

Foreign calling conventions

Most foreign code exposes a C ABI, and Rust uses the platform's C calling convention by default when calling foreign functions. Some foreign functions, most notably the Windows API, use other calling conventions. Rust provides a way to tell the compiler which convention to use:

#[cfg(all(target_os = "win32", target_arch = "x86"))]
#[link(name = "kernel32")]
#[allow(non_snake_case)]
unsafe extern "stdcall" {
    fn SetEnvironmentVariableA(n: *const u8, v: *const u8) -> libc::c_int;
}
This applies to the entire extern block. The list of supported ABI constraints are:

stdcall
aapcs
cdecl
fastcall
thiscall
vectorcall This is currently hidden behind the abi_vectorcall gate and is subject to change.
Rust
system
C
win64
sysv64
Most of the abis in this list are self-explanatory, but the system abi may seem a little odd. This constraint selects whatever the appropriate ABI is for interoperating with the target's libraries. For example, on win32 with a x86 architecture, this means that the abi used would be stdcall. On x86_64, however, windows uses the C calling convention, so C would be used. This means that in our previous example, we could have used extern "system" { ... } to define a block for all windows systems, not only x86 ones.

Interoperability with foreign code

Rust guarantees that the layout of a struct is compatible with the platform's representation in C only if the #[repr(C)] attribute is applied to it. #[repr(C, packed)] can be used to lay out struct members without padding. #[repr(C)] can also be applied to an enum.

Rust's owned boxes (Box<T>) use non-nullable pointers as handles which point to the contained object. However, they should not be manually created because they are managed by internal allocators. References can safely be assumed to be non-nullable pointers directly to the type. However, breaking the borrow checking or mutability rules is not guaranteed to be safe, so prefer using raw pointers (*) if that's needed because the compiler can't make as many assumptions about them.

Vectors and strings share the same basic memory layout, and utilities are available in the vec and str modules for working with C APIs. However, strings are not terminated with \0. If you need a NUL-terminated string for interoperability with C, you should use the CString type in the std::ffi module.

The libc crate on crates.io includes type aliases and function definitions for the C standard library in the libc module, and Rust links against libc and libm by default.

Variadic functions

In C, functions can be 'variadic', meaning they accept a variable number of arguments. This can be achieved in Rust by specifying ... within the argument list of a foreign function declaration:

unsafe extern {
    fn foo(x: i32, ...);
}

fn main() {
    unsafe {
        foo(10, 20, 30, 40, 50);
    }
}
Normal Rust functions can not be variadic:

// This will not compile

fn foo(x: i32, ...) {}
The "nullable pointer optimization"

Certain Rust types are defined to never be null. This includes references (&T, &mut T), boxes (Box<T>), and function pointers (extern "abi" fn()). When interfacing with C, pointers that might be null are often used, which would seem to require some messy transmutes and/or unsafe code to handle conversions to/from Rust types. However, trying to construct/work with these invalid values is undefined behavior, so you should use the following workaround instead.

As a special case, an enum is eligible for the "nullable pointer optimization" if it contains exactly two variants, one of which contains no data and the other contains a field of one of the non-nullable types listed above. This means no extra space is required for a discriminant; rather, the empty variant is represented by putting a null value into the non-nullable field. This is called an "optimization", but unlike other optimizations it is guaranteed to apply to eligible types.

The most common type that takes advantage of the nullable pointer optimization is Option<T>, where None corresponds to null. So Option<extern "C" fn(c_int) -> c_int> is a correct way to represent a nullable function pointer using the C ABI (corresponding to the C type int (*)(int)).

Here is a contrived example. Let's say some C library has a facility for registering a callback, which gets called in certain situations. The callback is passed a function pointer and an integer and it is supposed to run the function with the integer as a parameter. So we have function pointers flying across the FFI boundary in both directions.

use libc::c_int;

unsafe extern "C" {
    /// Registers the callback.
    fn register(cb: Option<extern "C" fn(Option<extern "C" fn(c_int) -> c_int>, c_int) -> c_int>);
}

/// This fairly useless function receives a function pointer and an integer
/// from C, and returns the result of calling the function with the integer.
/// In case no function is provided, it squares the integer by default.
extern "C" fn apply(process: Option<extern "C" fn(c_int) -> c_int>, int: c_int) -> c_int {
    match process {
        Some(f) => f(int),
        None    => int * int
    }
}

fn main() {
    unsafe {
        register(Some(apply));
    }
}
And the code on the C side looks like this:

void register(int (*f)(int (*)(int), int)) {
    ...
}
No transmute required!

FFI and unwinding

It’s important to be mindful of unwinding when working with FFI. Most ABI strings come in two variants, one with an -unwind suffix and one without. The Rust ABI always permits unwinding, so there is no Rust-unwind ABI.

If you expect Rust panics or foreign (e.g. C++) exceptions to cross an FFI boundary, that boundary must use the appropriate -unwind ABI string. Conversely, if you do not expect unwinding to cross an ABI boundary, use one of the non-unwind ABI strings.

Note: Compiling with panic=abort will still cause panic! to immediately abort the process, regardless of which ABI is specified by the function that panics.

If an unwinding operation does encounter an ABI boundary that is not permitted to unwind, the behavior depends on the source of the unwinding (Rust panic or a foreign exception):

panic will cause the process to safely abort.
A foreign exception entering Rust will cause undefined behavior.
Note that the interaction of catch_unwind with foreign exceptions is undefined, as is the interaction of panic with foreign exception-catching mechanisms (notably C++'s try/catch).

Rust panic with "C-unwind"

#[unsafe(no_mangle)]
unsafe extern "C-unwind" fn example() {
    panic!("Uh oh");
}
This function (when compiled with panic=unwind) is permitted to unwind C++ stack frames.

[Rust function with `catch_unwind`, which stops the unwinding]
      |
     ...
      |
[C++ frames]
      |                           ^
      | (calls)                   | (unwinding
      v                           |  goes this
[Rust function `example`]         |  way)
      |                           |
      +--- rust function panics --+
If the C++ frames have objects, their destructors will be called.

C++ throw with "C-unwind"

#[link(...)]
unsafe extern "C-unwind" {
    // A C++ function that may throw an exception
    fn may_throw();
}

#[unsafe(no_mangle)]
unsafe extern "C-unwind" fn rust_passthrough() {
    let b = Box::new(5);
    unsafe { may_throw(); }
    println!("{:?}", &b);
}
A C++ function with a try block may invoke rust_passthrough and catch an exception thrown by may_throw.

[C++ function with `try` block that invokes `rust_passthrough`]
      |
     ...
      |
[Rust function `rust_passthrough`]
      |                            ^
      | (calls)                    | (unwinding
      v                            |  goes this
[C++ function `may_throw`]         |  way)
      |                            |
      +--- C++ function throws ----+
If may_throw does throw an exception, b will be dropped. Otherwise, 5 will be printed.

panic can be stopped at an ABI boundary

#[unsafe(no_mangle)]
extern "C" fn assert_nonzero(input: u32) {
    assert!(input != 0)
}
If assert_nonzero is called with the argument 0, the runtime is guaranteed to (safely) abort the process, whether or not compiled with panic=abort.

Catching panic preemptively

If you are writing Rust code that may panic, and you don't wish to abort the process if it panics, you must use catch_unwind:

use std::panic::catch_unwind;

#[unsafe(no_mangle)]
pub extern "C" fn oh_no() -> i32 {
    let result = catch_unwind(|| {
        panic!("Oops!");
    });
    match result {
        Ok(_) => 0,
        Err(_) => 1,
    }
}

fn main() {}
Please note that catch_unwind will only catch unwinding panics, not those that abort the process. See the documentation of catch_unwind for more information.

Representing opaque structs

Sometimes, a C library wants to provide a pointer to something, but not let you know the internal details of the thing it wants. A stable and simple way is to use a void * argument:

void foo(void *arg);
void bar(void *arg);
We can represent this in Rust with the c_void type:

unsafe extern "C" {
    pub fn foo(arg: *mut libc::c_void);
    pub fn bar(arg: *mut libc::c_void);
}
This is a perfectly valid way of handling the situation. However, we can do a bit better. To solve this, some C libraries will instead create a struct, where the details and memory layout of the struct are private. This gives some amount of type safety. These structures are called ‘opaque’. Here’s an example, in C:

struct Foo; /* Foo is a structure, but its contents are not part of the public interface */
struct Bar;
void foo(struct Foo *arg);
void bar(struct Bar *arg);
To do this in Rust, let’s create our own opaque types:

#[repr(C)]
pub struct Foo {
    _data: (),
    _marker:
        core::marker::PhantomData<(*mut u8, core::marker::PhantomPinned)>,
}
#[repr(C)]
pub struct Bar {
    _data: (),
    _marker:
        core::marker::PhantomData<(*mut u8, core::marker::PhantomPinned)>,
}

unsafe extern "C" {
    pub fn foo(arg: *mut Foo);
    pub fn bar(arg: *mut Bar);
}
By including at least one private field and no constructor, we create an opaque type that we can't instantiate outside of this module. (A struct with no field could be instantiated by anyone.) We also want to use this type in FFI, so we have to add #[repr(C)]. The marker ensures the compiler does not mark the struct as Send, Sync, and Unpin. (*mut u8 is not Send or Sync, PhantomPinned is not Unpin)

But because our Foo and Bar types are different, we’ll get type safety between the two of them, so we cannot accidentally pass a pointer to Foo to bar().

Notice that it is a really bad idea to use an empty enum as FFI type. The compiler relies on empty enums being uninhabited, so handling values of type &Empty is a huge footgun and can lead to buggy program behavior (by triggering undefined behavior).

NOTE: The simplest way would use "extern types". But it's currently (as of June 2021) unstable and has some unresolved questions, see the RFC page and the tracking issue for more details.
