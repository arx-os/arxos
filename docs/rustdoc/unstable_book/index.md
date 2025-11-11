# The Rust Unstable Book

The Unstable Book
 
The Unstable Book

Welcome to the Unstable Book! This book consists of a number of chapters, each one organized by a "feature flag." That is, when using an unstable feature of Rust, you must use a flag, like this:

#![feature(coroutines, coroutine_trait, stmt_expr_attributes)]

use std::ops::{Coroutine, CoroutineState};
use std::pin::Pin;

fn main() {
    let mut coroutine = #[coroutine] || {
        yield 1;
        return "foo"
    };

    match Pin::new(&mut coroutine).resume(()) {
        CoroutineState::Yielded(1) => {}
        _ => panic!("unexpected value from resume"),
    }
    match Pin::new(&mut coroutine).resume(()) {
        CoroutineState::Complete("foo") => {}
        _ => panic!("unexpected value from resume"),
    }
}
The coroutines feature has a chapter describing how to use it.

Because this documentation relates to unstable features, we make no guarantees that what is contained here is accurate or up to date. It's developed on a best-effort basis. Each page will have a link to its tracking issue with the latest developments; you might want to check those as well.

## Chapters
- [1. Compiler environment variables](ch01-compiler-environment-variables.md)
- [2. Compiler flags](ch02-compiler-flags.md)
- [3. Language features](ch03-language-features.md)
- [4. Library Features](ch04-library-features.md)
