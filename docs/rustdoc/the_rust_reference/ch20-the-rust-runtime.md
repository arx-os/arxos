# The Rust runtime
This section documents features that define some aspects of the Rust runtime.
[runtime.global_allocator]
The global_allocator attribute
[runtime.global_allocator.intro]
The global_allocator attribute selects a memory allocator.
Example

use core::alloc::{GlobalAlloc, Layout};
use std::alloc::System;

struct MyAllocator;

unsafe impl GlobalAlloc for MyAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        unsafe { System.alloc(layout) }
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        unsafe { System.dealloc(ptr, layout) }
    }
}

#[global_allocator]
static GLOBAL: MyAllocator = MyAllocator;
[runtime.global_allocator.syntax]
The global_allocator attribute uses the MetaWord syntax.
[runtime.global_allocator.allowed-positions]
The global_allocator attribute may only be applied to a static item whose type implements the GlobalAlloc trait.
[runtime.global_allocator.duplicates]
The global_allocator attribute may only be used once on an item.
[runtime.global_allocator.single]
The global_allocator attribute may only be used once in the crate graph.
[runtime.global_allocator.stdlib]
The global_allocator attribute is exported from the standard library prelude.
[runtime.windows_subsystem]
The windows_subsystem attribute
[runtime.windows_subsystem.intro]
The windows_subsystem attribute sets the subsystem when linking on a Windows target.
Example

#![windows_subsystem = "windows"]
[runtime.windows_subsystem.syntax]
The windows_subsystem attribute uses the MetaNameValueStr syntax. Accepted values are "console" and "windows".
[runtime.windows_subsystem.allowed-positions]
The windows_subsystem attribute may only be applied to the crate root.
[runtime.windows_subsystem.duplicates]
Only the first use of windows_subsystem has effect.
Note

rustc lints against any use following the first. This may become an error in the future.
[runtime.windows_subsystem.ignored]
The windows_subsystem attribute is ignored on non-Windows targets and non-bin crate types.
[runtime.windows_subsystem.console]
The "console" subsystem is the default. If a console process is run from an existing console then it will be attached to that console; otherwise a new console window will be created.
[runtime.windows_subsystem.windows]
The "windows" subsystem will run detached from any existing console.
Note

The "windows" subsystem is commonly used by GUI applications that do not want to display a console window on startup.
