# Reference
This section contains reference material for Rust and WebAssembly development. It is not intended to provide a narrative and be read start to finish. Instead, each subsection should stand on its own.

## Crates You Should Know

This is a curated list of awesome crates you should know about for doing Rust and WebAssembly development.

You can also browse all the crates published to crates.io in the WebAssembly category.

Interacting with JavaScript and the DOM

wasm-bindgen | crates.io | repository

wasm-bindgen facilitates high-level interactions between Rust and JavaScript. It allows one to import JavaScript things into Rust and export Rust things to JavaScript.

wasm-bindgen-futures | crates.io | repository

wasm-bindgen-futures is a bridge connecting JavaSript Promises and Rust Futures. It can convert in both directions and is useful when working with asynchronous tasks in Rust, and allows interacting with DOM events and I/O operations.

js-sys | crates.io | repository

Raw wasm-bindgen imports for all the JavaScript global types and methods, such as Object, Function, eval, etc. These APIs are portable across all standard ECMAScript environments, not just the Web, such as Node.js.

web-sys | crates.io | repository

Raw wasm-bindgen imports for all the Web's APIs, such as DOM manipulation, setTimeout, Web GL, Web Audio, etc.

Error Reporting and Logging

console_error_panic_hook | crates.io | repository

This crate lets you debug panics on wasm32-unknown-unknown by providing a panic hook that forwards panic messages to console.error.

console_log | crates.io | repository

This crate provides a backend for the log crate that routes logged messages to the devtools console.

Dynamic Allocation

wee_alloc | crates.io | repository

The Wasm-Enabled, Elfin Allocator. A small (~1K uncompressed .wasm) allocator implementation for when code size is a greater concern than allocation performance.

Parsing and Generating .wasm Binaries

parity-wasm | crates.io | repository

Low-level WebAssembly format library for serializing, deserializing, and building .wasm binaries. Good support for well-known custom sections, such as the "names" section and "reloc.WHATEVER" sections.

wasmparser | crates.io | repository

A simple, event-driven library for parsing WebAssembly binary files. Provides the byte offsets of each parsed thing, which is necessary when interpreting relocs, for example.

Interpreting and Compiling WebAssembly

wasmi | crates.io | repository

An embeddable WebAssembly interpreter from Parity.

cranelift-wasm | crates.io | repository

Compile WebAssembly to the native host's machine code. Part of the Cranelift (né Cretonne) code generator project.

## Tools You Should Know

This is a curated list of awesome tools you should know about when doing Rust and WebAssembly development.

Development, Build, and Workflow Orchestration

wasm-pack | repository

wasm-pack seeks to be a one-stop shop for building and working with Rust- generated WebAssembly that you would like to interoperate with JavaScript, on the Web or with Node.js. wasm-pack helps you build and publish Rust-generated WebAssembly to the npm registry to be used alongside any other JavaScript package in workflows that you already use.

Optimizing and Manipulating .wasm Binaries

wasm-opt | repository

The wasm-opt tool reads WebAssembly as input, runs transformation, optimization, and/or instrumentation passes on it, and then emits the transformed WebAssembly as output. Running it on the .wasm binaries produced by LLVM by way of rustc will usually create .wasm binaries that are both smaller and execute faster. This tool is a part of the binaryen project.

wasm2js | repository

The wasm2js tool compiles WebAssembly into "almost asm.js". This is great for supporting browsers that don't have a WebAssembly implementation, such as Internet Explorer 11. This tool is a part of the binaryen project.

wasm-gc | repository

A small tool to garbage collect a WebAssembly module and remove all unneeded exports, imports, functions, etc. This is effectively a --gc-sections linker flag for WebAssembly.

You don't usually need to use this tool yourself because of two reasons:

rustc now has a new enough version of lld that it supports the --gc-sections flag for WebAssembly. This is automatically enabled for LTO builds.
The wasm-bindgen CLI tool runs wasm-gc for you automatically.
wasm-snip | repository

wasm-snip replaces a WebAssembly function's body with an unreachable instruction.

Maybe you know that some function will never be called at runtime, but the compiler can't prove that at compile time? Snip it! Then run wasm-gc again and all the functions it transitively called (which could also never be called at runtime) will get removed too.

This is useful for forcibly removing Rust's panicking infrastructure in non-debug production builds.

Inspecting .wasm Binaries

twiggy | repository

twiggy is a code size profiler for .wasm binaries. It analyzes a binary's call graph to answer questions like:

Why was this function included in the binary in the first place? I.e. which exported functions are transitively calling it?
What is the retained size of this function? I.e. how much space would be saved if I removed it and all the functions that become dead code after its removal.
Use twiggy to make your binaries slim!

wasm-objdump | repository

Print low-level details about a .wasm binary and each of its sections. Also supports disassembling into the WAT text format. It's like objdump but for WebAssembly. This is a part of the WABT project.

wasm-nm | repository

List the imported, exported, and private function symbols defined within a .wasm binary. It's like nm but for WebAssembly.

## Project Templates

The Rust and WebAssembly working group curates and maintains a variety of project templates to help you kickstart new projects and hit the ground running.

wasm-pack-template

This template is for starting a Rust and WebAssembly project to be used with wasm-pack.

Use cargo generate to clone this project template:


cargo install cargo-generate
cargo generate --git https://github.com/rustwasm/wasm-pack-template.git
create-wasm-app

This template is for JavaScript projects that consume packages from npm that were created from Rust with wasm-pack.

Use it with npm init:


mkdir my-project
cd my-project/
npm init wasm-app
This template is often used alongside wasm-pack-template, where wasm-pack-template projects are installed locally with npm link, and pulled in as a dependency for a create-wasm-app project.

rust-webpack-template

This template comes pre-configured with all the boilerplate for compiling Rust to WebAssembly and hooking that directly into a Webpack build pipeline with Webpack's rust-loader.

Use it with npm init:


mkdir my-project
cd my-project/
npm init rust-webpack
## Debugging

This section contains tips for debugging Rust-generated WebAssembly.

Building with Debug Symbols

⚡ When debugging, always make sure you are building with debug symbols!

If you don't have debug symbols enabled, then the "name" custom section won't be present in the compiled .wasm binary, and stack traces will have function names like wasm-function[42] rather than the Rust name of the function, like wasm_game_of_life::Universe::live_neighbor_count.

When using a "debug" build (aka wasm-pack build --debug or cargo build) debug symbols are enabled by default.

With a "release" build, debug symbols are not enabled by default. To enable debug symbols, ensure that you debug = true in the [profile.release] section of your Cargo.toml:


[profile.release]
debug = true
Logging with the console APIs

Logging is one of the most effective tools we have for proving and disproving hypotheses about why our programs are buggy. On the Web, the console.log function is the way to log messages to the browser's developer tools console.

We can use the web-sys crate to get access to the console logging functions:



extern crate web_sys;

web_sys::console::log_1(&"Hello, world!".into());
Alternatively, the console.error function has the same signature as console.log, but developer tools tend to also capture and display a stack trace alongside the logged message when console.error is used.

References

Using console.log with the web-sys crate:
web_sys::console::log takes an array of values to log
web_sys::console::log_1 logs a single value
web_sys::console::log_2 logs two values
Etc...
Using console.error with the web-sys crate:
web_sys::console::error takes an array of values to log
web_sys::console::error_1 logs a single value
web_sys::console::error_2 logs two values
Etc...
The console object on MDN
Firefox Developer Tools — Web Console
Microsoft Edge Developer Tools — Console
Get Started with the Chrome DevTools Console
Logging Panics

The console_error_panic_hook crate logs unexpected panics to the developer console via console.error. Rather than getting cryptic, difficult-to-debug RuntimeError: unreachable executed error messages, this gives you Rust's formatted panic message.

All you need to do is install the hook by calling console_error_panic_hook::set_once() in an initialization function or common code path:



#[wasm_bindgen]
pub fn init_panic_hook() {
    console_error_panic_hook::set_once();
}
Using a Debugger

Unfortunately, the debugging story for WebAssembly is still immature. On most Unix systems, DWARF is used to encode the information that a debugger needs to provide source-level inspection of a running program. There is an alternative format that encodes similar information on Windows. Currently, there is no equivalent for WebAssembly. Therefore, debuggers currently provide limited utility, and we end up stepping through raw WebAssembly instructions emitted by the compiler, rather than the Rust source text we authored.

There is a sub-charter of the W3C WebAssembly group for debugging, so expect this story to improve in the future!

Nonetheless, debuggers are still useful for inspecting the JavaScript that interacts with our WebAssembly, and inspecting raw wasm state.

References

Firefox Developer Tools — Debugger
Microsoft Edge Developer Tools — Debugger
Get Started with Debugging JavaScript in Chrome DevTools
Avoid the Need to Debug WebAssembly in the First Place

If the bug is specific to interactions with JavaScript or Web APIs, then write tests with wasm-bindgen-test.

If a bug does not involve interaction with JavaScript or Web APIs, then try to reproduce it as a normal Rust #[test] function, where you can leverage your OS's mature native tooling when debugging. Use testing crates like quickcheck and its test case shrinkers to mechanically reduce test cases. Ultimately, you will have an easier time finding and fixing bugs if you can isolate them in a smaller test cases that don't require interacting with JavaScript.

Note that in order to run native #[test]s without compiler and linker errors, you will need to ensure that "rlib" is included in the [lib.crate-type] array in your Cargo.toml file.


[lib]
crate-type ["cdylib", "rlib"]
## Time Profiling

This section describes how to profile Web pages using Rust and WebAssembly where the goal is improving throughput or latency.

⚡ Always make sure you are using an optimized build when profiling! wasm-pack build will build with optimizations by default.

Available Tools

The window.performance.now() Timer

The performance.now() function returns a monotonic timestamp measured in milliseconds since the Web page was loaded.

Calling performance.now has little overhead, so we can create simple, granular measurements from it without distorting the performance of the rest of the system and inflicting bias upon our measurements.

We can use it to time various operations, and we can access window.performance.now() via the web-sys crate:



extern crate web_sys;

fn now() -> f64 {
    web_sys::window()
        .expect("should have a Window")
        .performance()
        .expect("should have a Performance")
        .now()
}
The web_sys::window function
The web_sys::Window::performance method
The web_sys::Performance::now method
Developer Tools Profilers

All Web browsers' built-in developer tools include a profiler. These profilers display which functions are taking the most time with the usual kinds of visualizations like call trees and flame graphs.

If you build with debug symbols so that the "name" custom section is included in the wasm binary, then these profilers should display the Rust function names instead of something opaque like wasm-function[123].

Note that these profilers won't show inlined functions, and since Rust and LLVM rely on inlining so heavily, the results might still end up a bit perplexing.

Screenshot of profiler with Rust symbols

Resources

Firefox Developer Tools — Performance
Microsoft Edge Developer Tools — Performance
Chrome DevTools JavaScript Profiler
The console.time and console.timeEnd Functions

The console.time and console.timeEnd functions allow you to log the timing of named operations to the browser's developer tools console. You call console.time("some operation") when the operation begins, and call console.timeEnd("some operation") when it finishes. The string label naming the operation is optional.

You can use these functions directly via the web-sys crate:

web_sys::console::time_with_label("some operation")
web_sys::console::time_end_with_label("some operation")
Here is a screenshot of console.time logs in the browser's console:

Screenshot of console.time logs

Additionally, console.time and console.timeEnd logs will show up in your browser's profiler's "timeline" or "waterfall" view:

Screenshot of console.time logs

Using #[bench] with Native Code

The same way we can often leverage our operating system's native code debugging tools by writing #[test]s rather than debugging on the Web, we can leverage our operating system's native code profiling tools by writing #[bench] functions.

Write your benchmarks in the benches subdirectory of your crate. Make sure that your crate-type includes "rlib" or else the bench binaries won't be able to link your main lib.

However! Make sure that you know the bottleneck is in the WebAssembly before investing much energy in native code profiling! Use your browser's profiler to confirm this, or else you risk wasting your time optimizing code that isn't hot.

Resources

Using the perf profiler on Linux
Using the Instruments.app profiler on macOS
The VTune profiler supports Windows and Linux
## Shrinking .wasm Size

This section will teach you how to optimize your .wasm build for a small code size footprint, and how to identify opportunities to change your Rust source such that less .wasm code is emitted.

Why Care About Code Size?

When serving a .wasm file over the network, the smaller it is, the faster the client can download it. Faster .wasm downloads lead to faster page load times, and that leads to happier users.

However, it's important to remember though that code size likely isn't the end-all-be-all metric you're interested in, but rather something much more vague and hard to measure like "time to first interaction". While code size plays a large factor in this measurement (can't do anything if you don't even have all the code yet!) it's not the only factor.

WebAssembly is typically served to users gzip'd so you'll want to be sure to compare differences in gzip'd size for transfer times over the wire. Also keep in mind that the WebAssembly binary format is quite amenable to gzip compression, often getting over 50% reductions in size.

Furthermore, WebAssembly's binary format is optimized for very fast parsing and processing. Browsers nowadays have "baseline compilers" which parses WebAssembly and emits compiled code as fast as wasm can come in over the network. This means that if you're using instantiateStreaming the second the Web request is done the WebAssembly module is probably ready to go. JavaScript, on the other hand, can often take longer to not only parse but also get up to speed with JIT compilation and such.

And finally, remember that WebAssembly is also far more optimized than JavaScript for execution speed. You'll want to be sure to measure for runtime comparisons between JavaScript and WebAssembly to factor that in to how important code size is.

All this to say basically don't dismay immediately if your .wasm file is larger than expected! Code size may end up only being one of many factors in the end-to-end story. Comparisons between JavaScript and WebAssembly that only look at code size are missing the forest for the trees.

Optimizing Builds for Code Size

There are a bunch of configuration options we can use to get rustc to make smaller .wasm binaries. In some cases, we are trading longer compile times for smaller .wasm sizes. In other cases, we are trading runtime speed of the WebAssembly for smaller code size. We should be cognizant of the trade offs of each option, and in the cases where we trade runtime speed for code size, profile and measure to make an informed decision about whether the trade is worth it.

Compiling with Link Time Optimizations (LTO)

In Cargo.toml, add lto = true in the [profile.release] section:


[profile.release]
lto = true
This gives LLVM many more opportunities to inline and prune functions. Not only will it make the .wasm smaller, but it will also make it faster at runtime! The downside is that compilation will take longer.

Tell LLVM to Optimize for Size Instead of Speed

LLVM's optimization passes are tuned to improve speed, not size, by default. We can change the goal to code size by modifying the [profile.release] section in Cargo.toml to this:


[profile.release]
opt-level = 's'
Or, to even more aggressively optimize for size, at further potential speed costs:


[profile.release]
opt-level = 'z'
Note that, surprisingly enough, opt-level = "s" can sometimes result in smaller binaries than opt-level = "z". Always measure!

Use the wasm-opt Tool

The Binaryen toolkit is a collection of WebAssembly-specific compiler tools. It goes much further than LLVM's WebAssembly backend does, and using its wasm-opt tool to post-process a .wasm binary generated by LLVM can often get another 15-20% savings on code size. It will often produce runtime speed ups at the same time!


# Optimize for size.
wasm-opt -Os -o output.wasm input.wasm

# Optimize aggressively for size.
wasm-opt -Oz -o output.wasm input.wasm

# Optimize for speed.
wasm-opt -O -o output.wasm input.wasm

# Optimize aggressively for speed.
wasm-opt -O3 -o output.wasm input.wasm
Notes about Debug Information

One of the biggest contributors to wasm binary size can be debug information and the names section of the wasm binary. The wasm-pack tool, however, removes debuginfo by default. Additionally wasm-opt removes the names section by default unless -g is also specified.

This means that if you follow the above steps you should by default not have either debuginfo or the names section in the wasm binary. If, however, you are manually otherwise preserving this debug information in the wasm binary be sure to be mindful of this!

Size Profiling

If tweaking build configurations to optimize for code size isn't resulting in a small enough .wasm binary, it is time to do some profiling to see where the remaining code size is coming from.

⚡ Just like how we let time profiling guide our speed up efforts, we want to let size profiling guide our code size shrinking efforts. Fail to do this and you risk wasting your own time!

The twiggy Code Size Profiler

twiggy is a code size profiler that supports WebAssembly as input. It analyzes a binary's call graph to answer questions like:

Why was this function included in the binary in the first place?

What is the retained size of this function? I.e. how much space would be saved if I removed it and all the functions that become dead code after its removal?


$ twiggy top -n 20 pkg/wasm_game_of_life_bg.wasm
 Shallow Bytes │ Shallow % │ Item
───────────────┼───────────┼────────────────────────────────────────────────────────────────────────────────────────
          9158 ┊    19.65% ┊ "function names" subsection
          3251 ┊     6.98% ┊ dlmalloc::dlmalloc::Dlmalloc::malloc::h632d10c184fef6e8
          2510 ┊     5.39% ┊ <str as core::fmt::Debug>::fmt::he0d87479d1c208ea
          1737 ┊     3.73% ┊ data[0]
          1574 ┊     3.38% ┊ data[3]
          1524 ┊     3.27% ┊ core::fmt::Formatter::pad::h6825605b326ea2c5
          1413 ┊     3.03% ┊ std::panicking::rust_panic_with_hook::h1d3660f2e339513d
          1200 ┊     2.57% ┊ core::fmt::Formatter::pad_integral::h06996c5859a57ced
          1131 ┊     2.43% ┊ core::str::slice_error_fail::h6da90c14857ae01b
          1051 ┊     2.26% ┊ core::fmt::write::h03ff8c7a2f3a9605
           931 ┊     2.00% ┊ data[4]
           864 ┊     1.85% ┊ dlmalloc::dlmalloc::Dlmalloc::free::h27b781e3b06bdb05
           841 ┊     1.80% ┊ <char as core::fmt::Debug>::fmt::h07742d9f4a8c56f2
           813 ┊     1.74% ┊ __rust_realloc
           708 ┊     1.52% ┊ core::slice::memchr::memchr::h6243a1b2885fdb85
           678 ┊     1.45% ┊ <core::fmt::builders::PadAdapter<'a> as core::fmt::Write>::write_str::h96b72fb7457d3062
           631 ┊     1.35% ┊ universe_tick
           631 ┊     1.35% ┊ dlmalloc::dlmalloc::Dlmalloc::dispose_chunk::hae6c5c8634e575b8
           514 ┊     1.10% ┊ std::panicking::default_hook::{{closure}}::hfae0c204085471d5
           503 ┊     1.08% ┊ <&'a T as core::fmt::Debug>::fmt::hba207e4f7abaece6
Manually Inspecting LLVM-IR

LLVM-IR is the final intermediate representation in the compiler toolchain before LLVM generates WebAssembly. Therefore, it is very similar to the WebAssembly that is ultimately emitted. More LLVM-IR generally means more .wasm size, and if a function takes up 25% of the LLVM-IR, then it generally will take up 25% of the .wasm. While these numbers only hold in general, the LLVM-IR has crucial information that is not present in the .wasm (because of WebAssembly's lack of a debugging format like DWARF): which subroutines were inlined into a given function.

You can generate LLVM-IR with this cargo command:


cargo rustc --release -- --emit llvm-ir
Then, you can use find to locate the .ll file containing the LLVM-IR in cargo's target directory:


find target/release -type f -name '*.ll'
References

LLVM Language Reference Manual
More Invasive Tools and Techniques

Tweaking build configurations to get smaller .wasm binaries is pretty hands off. When you need to go the extra mile, however, you are prepared to use more invasive techniques, like rewriting source code to avoid bloat. What follows is a collection of get-your-hands-dirty techniques you can apply to get smaller code sizes.

Avoid String Formatting

format!, to_string, etc... can bring in a lot of code bloat. If possible, only do string formatting in debug mode, and in release mode use static strings.

Avoid Panicking

This is definitely easier said than done, but tools like twiggy and manually inspecting LLVM-IR can help you figure out which functions are panicking.

Panics do not always appear as a panic!() macro invocation. They arise implicitly from many constructs, such as:

Indexing a slice panics on out of bounds indices: my_slice[i]

Division will panic if the divisor is zero: dividend / divisor

Unwrapping an Option or Result: opt.unwrap() or res.unwrap()

The first two can be translated into the third. Indexing can be replaced with fallible my_slice.get(i) operations. Division can be replaced with checked_div calls. Now we only have a single case to contend with.

Unwrapping an Option or Result without panicking comes in two flavors: safe and unsafe.

The safe approach is to abort instead of panicking when encountering a None or an Error:



#[inline]
pub fn unwrap_abort<T>(o: Option<T>) -> T {
    use std::process;
    match o {
        Some(t) => t,
        None => process::abort(),
    }
}
Ultimately, panics translate into aborts in wasm32-unknown-unknown anyways, so this gives you the same behavior but without the code bloat.

Alternatively, the unreachable crate provides an unsafe unchecked_unwrap extension method for Option and Result which tells the Rust compiler to assume that the Option is Some or the Result is Ok. It is undefined behavior what happens if that assumption does not hold. You really only want to use this unsafe approach when you 110% know that the assumption holds, and the compiler just isn't smart enough to see it. Even if you go down this route, you should have a debug build configuration that still does the checking, and only use unchecked operations in release builds.

Avoid Allocation or Switch to wee_alloc

Rust's default allocator for WebAssembly is a port of dlmalloc to Rust. It weighs in somewhere around ten kilobytes. If you can completely avoid dynamic allocation, then you should be able to shed those ten kilobytes.

Completely avoiding dynamic allocation can be very difficult. But removing allocation from hot code paths is usually much easier (and usually helps make those hot code paths faster, as well). In these cases, replacing the default global allocator with wee_alloc should save you most (but not quite all) of those ten kilobytes. wee_alloc is an allocator designed for situations where you need some kind of allocator, but do not need a particularly fast allocator, and will happily trade allocation speed for smaller code size.

Use Trait Objects Instead of Generic Type Parameters

When you create generic functions that use type parameters, like this:



fn whatever<T: MyTrait>(t: T) { ... }
Then rustc and LLVM will create a new copy of the function for each T type that the function is used with. This presents many opportunities for compiler optimizations based on which particular T each copy is working with, but these copies add up quickly in terms of code size.

If you use trait objects instead of type parameters, like this:



fn whatever(t: Box<MyTrait>) { ... }
// or
fn whatever(t: &MyTrait) { ... }
// etc...
Then dynamic dispatch via virtual calls is used, and only a single version of the function is emitted in the .wasm. The downside is the loss of the compiler optimization opportunities and the added cost of indirect, dynamically dispatched function calls.

Use the wasm-snip Tool

wasm-snip replaces a WebAssembly function's body with an unreachable instruction. This is a rather heavy, blunt hammer for functions that kind of look like nails if you squint hard enough.

Maybe you know that some function will never be called at runtime, but the compiler can't prove that at compile time? Snip it! Afterwards, run wasm-opt again with the --dce flag, and all the functions that the snipped function transitively called (which could also never be called at runtime) will get removed too.

This tool is particularly useful for removing the panicking infrastructure, since panics ultimately translate into traps anyways.

## JavaScript Interoperation

Importing and Exporting JS Functions

From the Rust Side

When using wasm within a JS host, importing and exporting functions from the Rust side is straightforward: it works very similarly to C.

WebAssembly modules declare a sequence of imports, each with a module name and an import name. The module name for an extern { ... } block can be specified using #[link(wasm_import_module)], currently it defaults to "env".

Exports have only a single name. In addition to any extern functions the WebAssembly instance's default linear memory is exported as "memory".



// import a JS function called `foo` from the module `mod`
#[link(wasm_import_module = "mod")]
extern { fn foo(); }

// export a Rust function called `bar`
#[no_mangle]
pub extern fn bar() { /* ... */ }
Because of wasm's limited value types, these functions must operate only on primitive numeric types.

From the JS Side

Within JS, a wasm binary turns into an ES6 module. It must be instantiated with linear memory and have a set of JS functions matching the expected imports. The details of instantiation are available on MDN.

The resulting ES6 module will contain all of the functions exported from Rust, now available as JS functions.

Here is a very simple example of the whole setup in action.

Going Beyond Numerics

When using wasm within JS, there is a sharp split between the wasm module's memory and the JS memory:

Each wasm module has a linear memory (described at the top of this document), which is initialized during instantiation. JS code can freely read and write to this memory.

By contrast, wasm code has no direct access to JS objects.

Thus, sophisticated interop happens in two main ways:

Copying in or out binary data to the wasm memory. For example, this is one way to provide an owned String to the Rust side.

Setting up an explicit "heap" of JS objects which are then given "addresses". This allows wasm code to refer to JS objects indirectly (using integers), and operate on those objects by invoking imported JS functions.

Fortunately, this interop story is very amenable to treatment through a generic "bindgen"-style framework: wasm-bindgen. The framework makes it possible to write idiomatic Rust function signatures that map to idiomatic JS functions, automatically.

Custom Sections

Custom sections allow embedding named arbitrary data into a wasm module. The section data is set at compile time and is read directly from the wasm module, it cannot be modified at runtime.

In Rust, custom sections are static arrays ([T; size]) exposed with the #[link_section] attribute:



#[link_section = "hello"]
pub static SECTION: [u8; 24] = *b"This is a custom section";
This adds a custom section named hello to the wasm file, the rust variable name SECTION is arbitrary, changing it wouldn't alter the behaviour. The contents are bytes of text here but could be any arbitrary data.

The custom sections can be read on the JS side using the WebAssembly.Module.customSections function, it takes a wasm Module and the section name as arguments and returns an Array of ArrayBuffers. Multiple sections may be specified using the same name, in which case they will all appear in this array.


WebAssembly.compileStreaming(fetch("sections.wasm"))
.then(mod => {
  const sections = WebAssembly.Module.customSections(mod, "hello");

  const decoder = new TextDecoder();
  const text = decoder.decode(sections[0]);

  console.log(text); // -> "This is a custom section"
});
## Which Crates Will Work Off-the-Shelf with WebAssembly?

It is easiest to list the things that do not currently work with WebAssembly; crates which avoid these things tend to be portable to WebAssembly and usually Just Work. A good rule of thumb is that if a crate supports embedded and #![no_std] usage, it probably also supports WebAssembly.

Things a Crate Might do that Won't Work with WebAssembly

C and System Library Dependencies

There are no system libraries in wasm, so any crate that tries to bind to a system library won't work.

Using C libraries will also probably fail to work, since wasm doesn't have a stable ABI for cross-language communication, and cross-language linking for wasm is very finicky. Everyone wants this to work eventually, especially since clang is shipping their wasm32 target by default now, but the story isn't quite there yet.

File I/O

WebAssembly does not have access to a file system, so crates that assume the existence of a file system — and don't have wasm-specific workarounds — will not work.

Spawning Threads

There are plans to add threading to WebAssembly, but it isn't shipping yet. Attempts to spawn on a thread on the wasm32-unknown-unknown target will panic, which triggers a wasm trap.

So Which General Purpose Crates Tend to Work Off-the-Shelf with WebAssembly?

Algorithms and Data Structures

Crates that provide the implementation of a particular algorithm or data structure, for example A* graph search or splay trees, tend to work well with WebAssembly.

#![no_std]

Crates that do not rely on the standard library tend to work well with WebAssembly.

Parsers

Parsers — so long as they just take input and don't perform their own I/O — tend to work well with WebAssembly.

Text Processing

Crates that deal with the complexities of human language when expressed in textual form tend to work well with WebAssembly.

Rust Patterns

Shared solutions for particular situations specific to programming in Rust tend to work well with WebAssembly.

## How to Add WebAssembly Support to a General-Purpose Crate

This section is for general-purpose crate authors who want to support WebAssembly.

Maybe Your Crate Already Supports WebAssembly!

Review the information about what kinds of things can make a general-purpose crate not portable for WebAssembly. If your crate doesn't have any of those things, it likely already supports WebAssembly!

You can always check by running cargo build for the WebAssembly target:


cargo build --target wasm32-unknown-unknown
If that command fails, then your crate doesn't support WebAssembly right now. If it doesn't fail, then your crate might support WebAssembly. You can be 100% sure that it does (and continues to do so!) by adding tests for wasm and running those tests in CI.

Adding Support for WebAssembly

Avoid Performing I/O Directly

On the Web, I/O is always asynchronous, and there isn't a file system. Factor I/O out of your library, let users perform the I/O and then pass the input slices to your library instead.

For example, refactor this:



use std::fs;
use std::path::Path;

pub fn parse_thing(path: &Path) -> Result<MyThing, MyError> {
    let contents = fs::read(path)?;
    // ...
}
Into this:



pub fn parse_thing(contents: &[u8]) -> Result<MyThing, MyError> {
    // ...
}
Add wasm-bindgen as a Dependency

If you need to interact with the outside world (i.e. you can't have library consumers drive that interaction for you) then you'll need to add wasm-bindgen (and js-sys and web-sys if you need them) as a dependency for when compilation is targeting WebAssembly:


[target.'cfg(target_arch = "wasm32")'.dependencies]
wasm-bindgen = "0.2"
js-sys = "0.3"
web-sys = "0.3"
Avoid Synchronous I/O

If you must perform I/O in your library, then it cannot be synchronous. There is only asynchronous I/O on the Web. Use the futures crate and the wasm-bindgen-futures crate to manage asynchronous I/O. If your library functions are generic over some future type F, then that future can be implemented via fetch on the Web or via non-blocking I/O provided by the operating system.



pub fn do_stuff<F>(future: F) -> impl Future<Item = MyOtherThing>
where
    F: Future<Item = MyThing>,
{
    // ...
}
You can also define a trait and implement it for WebAssembly and the Web and also for native targets:



trait ReadMyThing {
    type F: Future<Item = MyThing>;
    fn read(&self) -> Self::F;
}

#[cfg(target_arch = "wasm32")]
struct WebReadMyThing {
    // ...
}

#[cfg(target_arch = "wasm32")]
impl ReadMyThing for WebReadMyThing {
    // ...
}

#[cfg(not(target_arch = "wasm32"))]
struct NativeReadMyThing {
    // ...
}

#[cfg(not(target_arch = "wasm32"))]
impl ReadMyThing for NativeReadMyThing {
    // ...
}
Avoid Spawning Threads

Wasm doesn't support threads yet (but experimental work is ongoing), so attempts to spawn threads in wasm will panic.

You can use #[cfg(..)]s to enable threaded and non-threaded code paths depending on if the target is WebAssembly or not:



#![cfg(target_arch = "wasm32")]
fn do_work() {
    // Do work with only this thread...
}

#![cfg(not(target_arch = "wasm32"))]
fn do_work() {
    use std::thread;

    // Spread work to helper threads....
    thread::spawn(|| {
        // ...
    });
}
Another option is to factor out thread spawning from your library and allow users to "bring their own threads" similar to factoring out file I/O and allowing users to bring their own I/O. This has the side effect of playing nice with applications that want to own their own custom thread pool.

Maintaining Ongoing Support for WebAssembly

Building for wasm32-unknown-unknown in CI

Ensure that compilation doesn't fail when targeting WebAssembly by having your CI script run these commands:


rustup target add wasm32-unknown-unknown
cargo check --target wasm32-unknown-unknown
For example, you can add this to your .travis.yml configuration for Travis CI:



matrix:
  include:
    - language: rust
      rust: stable
      name: "check wasm32 support"
      install: rustup target add wasm32-unknown-unknown
      script: cargo check --target wasm32-unknown-unknown
Testing in Node.js and Headless Browsers

You can use wasm-bindgen-test and the wasm-pack test subcommand to run wasm tests in either Node.js or a headless browser. You can even integrate these tests into your CI.

Learn more about testing wasm here.

## Deploying Rust and WebAssembly to Production

⚡ Deploying Web applications built with Rust and WebAssembly is nearly identical to deploying any other Web application!

To deploy a Web application that uses Rust-generated WebAssembly on the client, copy the built Web application's files to your production server's file system and configure your HTTP server to make them accessible.

Ensure that Your HTTP Server Uses the application/wasm MIME Type

For the fastest page loads, you'll want to use the WebAssembly.instantiateStreaming function to pipeline wasm compilation and instantiation with network transfer (or make sure your bundler is able to use that function). However, instantiateStreaming requires that the HTTP response has the application/wasm MIME type set, or else it will throw an error.

How to configure MIME types for the Apache HTTP server
How to configure MIME types for the NGINX HTTP server
More Resources

Best Practices for Webpack in Production. Many Rust and WebAssembly projects use Webpack to bundle their Rust-generated WebAssembly, JavaScript, CSS, and HTML. This guide has tips for getting the most out of Webpack when deploying to production environments.
Apache documentation. Apache is a popular HTTP server for use in production.
NGINX documentation. NGINX is a popular HTTP server for use in production.
