# Panic
[panic.intro]
Rust provides a mechanism to prevent a function from returning normally, and instead “panic,” which is a response to an error condition that is typically not expected to be recoverable within the context in which the error is encountered.
[panic.lang-ops]
Some language constructs, such as out-of-bounds array indexing, panic automatically.
[panic.control]
There are also language features that provide a level of control over panic behavior:
A panic handler defines the behavior of a panic.
FFI ABIs may alter how panics behave.
Note

The standard library provides the capability to explicitly panic via the panic! macro.
[panic.panic_handler]
The panic_handler attribute
[panic.panic_handler.intro]
The panic_handler attribute can be applied to a function to define the behavior of panics.
[panic.panic_handler.allowed-positions]
The panic_handler attribute can only be applied to a function with signature fn(&PanicInfo) -> !.
Note

The PanicInfo struct contains information about the location of the panic.
[panic.panic_handler.unique]
There must be a single panic_handler function in the dependency graph.
Below is shown a panic_handler function that logs the panic message and then halts the thread.
#![no_std]

use core::fmt::{self, Write};
use core::panic::PanicInfo;

struct Sink {
    // ..
}

#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    let mut sink = Sink::new();

    // logs "panicked at '$reason', src/main.rs:27:4" to some `sink`
    let _ = writeln!(sink, "{}", info);

    loop {}
}
[panic.panic_handler.std]
Standard behavior
[panic.panic_handler.std.kinds]
std provides two different panic handlers:
unwind — unwinds the stack and is potentially recoverable.
abort –– aborts the process and is non-recoverable.
Not all targets may provide the unwind handler.
Note

The panic handler used when linking with std can be set with the -C panic CLI flag. The default for most targets is unwind.

The standard library’s panic behavior can be modified at runtime with the std::panic::set_hook function.
[panic.panic_handler.std.no_std]
Linking a no_std binary, dylib, cdylib, or staticlib will require specifying your own panic handler.
[panic.strategy]
Panic strategy
[panic.strategy.intro]
The panic strategy defines the kind of panic behavior that a crate is built to support.
Note

The panic strategy can be chosen in rustc with the -C panic CLI flag.

When generating a binary, dylib, cdylib, or staticlib and linking with std, the -C panic CLI flag also influences which panic handler is used.
Note

When compiling code with the abort panic strategy, the optimizer may assume that unwinding across Rust frames is impossible, which can result in both code-size and runtime speed improvements.
Note

See link.unwinding for restrictions on linking crates with different panic strategies. An implication is that crates built with the unwind strategy can use the abort panic handler, but the abort strategy cannot use the unwind panic handler.
[panic.unwind]
Unwinding
[panic.unwind.intro]
Panicking may either be recoverable or non-recoverable, though it can be configured (by choosing a non-unwinding panic handler) to always be non-recoverable. (The converse is not true: the unwind handler does not guarantee that all panics are recoverable, only that panicking via the panic! macro and similar standard library mechanisms is recoverable.)
[panic.unwind.destruction]
When a panic occurs, the unwind handler “unwinds” Rust frames, just as C++’s throw unwinds C++ frames, until the panic reaches the point of recovery (for instance at a thread boundary). This means that as the panic traverses Rust frames, live objects in those frames that implement Drop will have their drop methods called. Thus, when normal execution resumes, no-longer-accessible objects will have been “cleaned up” just as if they had gone out of scope normally.
Note

As long as this guarantee of resource-cleanup is preserved, “unwinding” may be implemented without actually using the mechanism used by C++ for the target platform.
Note

The standard library provides two mechanisms for recovering from a panic, std::panic::catch_unwind (which enables recovery within the panicking thread) and std::thread::spawn (which automatically sets up panic recovery for the spawned thread so that other threads may continue running).
[panic.unwind.ffi]
Unwinding across FFI boundaries
[panic.unwind.ffi.intro]
It is possible to unwind across FFI boundaries using an appropriate ABI declaration. While useful in certain cases, this creates unique opportunities for undefined behavior, especially when multiple language runtimes are involved.
[panic.unwind.ffi.undefined]
Unwinding with the wrong ABI is undefined behavior:
Causing an unwind into Rust code from a foreign function that was called via a function declaration or pointer declared with a non-unwinding ABI, such as "C", "system", etc. (For example, this case occurs when such a function written in C++ throws an exception that is uncaught and propagates to Rust.)
Calling a Rust extern function that unwinds (with extern "C-unwind" or another ABI that permits unwinding) from code that does not support unwinding, such as code compiled with GCC or Clang using -fno-exceptions
[panic.unwind.ffi.catch-foreign]
Catching a foreign unwinding operation (such as a C++ exception) using std::panic::catch_unwind, std::thread::JoinHandle::join, or by letting it propagate beyond the Rust main() function or thread root will have one of two behaviors, and it is unspecified which will occur:
The process aborts.
The function returns a Result::Err containing an opaque type.
Note

Rust code compiled or linked with a different instance of the Rust standard library counts as a “foreign exception” for the purpose of this guarantee. Thus, a library that uses panic! and is linked against one version of the Rust standard library, invoked from an application that uses a different version of the standard library, may cause the entire application to abort even if the library is only used within a child thread.
[panic.unwind.ffi.dispose-panic]
There are currently no guarantees about the behavior that occurs when a foreign runtime attempts to dispose of, or rethrow, a Rust panic payload. In other words, an unwind originated from a Rust runtime must either lead to termination of the process or be caught by the same runtime.
[link]
