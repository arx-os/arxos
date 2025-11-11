# Implementing Arc and Mutex
Knowing the theory is all fine and good, but the best way to understand something is to use it. To better understand atomics and interior mutability, we'll be implementing versions of the standard library's Arc and Mutex types.

TODO: Write Mutex chapters.

Implementing Arc

In this section, we'll be implementing a simpler version of std::sync::Arc. Similarly to the implementation of Vec we made earlier, we won't be taking advantage of as many optimizations, intrinsics, or unstable code as the standard library may.

This implementation is loosely based on the standard library's implementation (technically taken from alloc::sync in 1.49, as that's where it's actually implemented), but it will not support weak references at the moment as they make the implementation slightly more complex.

Please note that this section is very work-in-progress at the moment.

### Layout

Let's start by making the layout for our implementation of Arc.

An Arc<T> provides thread-safe shared ownership of a value of type T, allocated in the heap. Sharing implies immutability in Rust, so we don't need to design anything that manages access to that value, right? Although interior mutability types like Mutex allow Arc's users to create shared mutability, Arc itself doesn't need to concern itself with these issues.

However there is one place where Arc needs to concern itself with mutation: destruction. When all the owners of the Arc go away, we need to be able to drop its contents and free its allocation. So we need a way for an owner to know if it's the last owner, and the simplest way to do that is with a count of the owners -- Reference Counting.

Unfortunately, this reference count is inherently shared mutable state, so Arc does need to think about synchronization. We could use a Mutex for this, but that's overkill. Instead, we'll use atomics. And since everyone already needs a pointer to the T's allocation, we might as well put the reference count in that same allocation.

Naively, it would look something like this:

use std::sync::atomic;

pub struct Arc<T> {
    ptr: *mut ArcInner<T>,
}

pub struct ArcInner<T> {
    rc: atomic::AtomicUsize,
    data: T,
}
This would compile, however it would be incorrect. First of all, the compiler will give us too strict variance. For example, an Arc<&'static str> couldn't be used where an Arc<&'a str> was expected. More importantly, it will give incorrect ownership information to the drop checker, as it will assume we don't own any values of type T. As this is a structure providing shared ownership of a value, at some point there will be an instance of this structure that entirely owns its data. See the chapter on ownership and lifetimes for all the details on variance and drop check.

To fix the first problem, we can use NonNull<T>. Note that NonNull<T> is a wrapper around a raw pointer that declares that:

We are covariant over T
Our pointer is never null
To fix the second problem, we can include a PhantomData marker containing an ArcInner<T>. This will tell the drop checker that we have some notion of ownership of a value of ArcInner<T> (which itself contains some T).

With these changes we get our final structure:

use std::marker::PhantomData;
use std::ptr::NonNull;
use std::sync::atomic::AtomicUsize;

pub struct Arc<T> {
    ptr: NonNull<ArcInner<T>>,
    phantom: PhantomData<ArcInner<T>>,
}

pub struct ArcInner<T> {
    rc: AtomicUsize,
    data: T,
}
### Base Code

Now that we've decided the layout for our implementation of Arc, let's create some basic code.

Constructing the Arc

We'll first need a way to construct an Arc<T>.

This is pretty simple, as we just need to box the ArcInner<T> and get a NonNull<T> pointer to it.

impl<T> Arc<T> {
    pub fn new(data: T) -> Arc<T> {
        // We start the reference count at 1, as that first reference is the
        // current pointer.
        let boxed = Box::new(ArcInner {
            rc: AtomicUsize::new(1),
            data,
        });
        Arc {
            // It is okay to call `.unwrap()` here as we get a pointer from
            // `Box::into_raw` which is guaranteed to not be null.
            ptr: NonNull::new(Box::into_raw(boxed)).unwrap(),
            phantom: PhantomData,
        }
    }
}
Send and Sync

Since we're building a concurrency primitive, we'll need to be able to send it across threads. Thus, we can implement the Send and Sync marker traits. For more information on these, see the section on Send and Sync.

This is okay because:

You can only get a mutable reference to the value inside an Arc if and only if it is the only Arc referencing that data (which only happens in Drop)
We use atomics for the shared mutable reference counting
unsafe impl<T: Sync + Send> Send for Arc<T> {}
unsafe impl<T: Sync + Send> Sync for Arc<T> {}
We need to have the bound T: Sync + Send because if we did not provide those bounds, it would be possible to share values that are thread-unsafe across a thread boundary via an Arc, which could possibly cause data races or unsoundness.

For example, if those bounds were not present, Arc<Rc<u32>> would be Sync or Send, meaning that you could clone the Rc out of the Arc to send it across a thread (without creating an entirely new Rc), which would create data races as Rc is not thread-safe.

Getting the ArcInner

To dereference the NonNull<T> pointer into a &T, we can call NonNull::as_ref. This is unsafe, unlike the typical as_ref function, so we must call it like this:

unsafe { self.ptr.as_ref() }
We'll be using this snippet a few times in this code (usually with an associated let binding).

This unsafety is okay because while this Arc is alive, we're guaranteed that the inner pointer is valid.

Deref

Alright. Now we can make Arcs (and soon will be able to clone and destroy them correctly), but how do we get to the data inside?

What we need now is an implementation of Deref.

We'll need to import the trait:

use std::ops::Deref;
And here's the implementation:

impl<T> Deref for Arc<T> {
    type Target = T;

    fn deref(&self) -> &T {
        let inner = unsafe { self.ptr.as_ref() };
        &inner.data
    }
}
Pretty simple, eh? This simply dereferences the NonNull pointer to the ArcInner<T>, then gets a reference to the data inside.

Code

Here's all the code from this section:

use std::ops::Deref;

impl<T> Arc<T> {
    pub fn new(data: T) -> Arc<T> {
        // We start the reference count at 1, as that first reference is the
        // current pointer.
        let boxed = Box::new(ArcInner {
            rc: AtomicUsize::new(1),
            data,
        });
        Arc {
            // It is okay to call `.unwrap()` here as we get a pointer from
            // `Box::into_raw` which is guaranteed to not be null.
            ptr: NonNull::new(Box::into_raw(boxed)).unwrap(),
            phantom: PhantomData,
        }
    }
}

unsafe impl<T: Sync + Send> Send for Arc<T> {}
unsafe impl<T: Sync + Send> Sync for Arc<T> {}


impl<T> Deref for Arc<T> {
    type Target = T;

    fn deref(&self) -> &T {
        let inner = unsafe { self.ptr.as_ref() };
        &inner.data
    }
}
### Cloning

Now that we've got some basic code set up, we'll need a way to clone the Arc.

Basically, we need to:

Increment the atomic reference count
Construct a new instance of the Arc from the inner pointer
First, we need to get access to the ArcInner:

let inner = unsafe { self.ptr.as_ref() };
We can update the atomic reference count as follows:

let old_rc = inner.rc.fetch_add(1, Ordering::???);
But what ordering should we use here? We don't really have any code that will need atomic synchronization when cloning, as we do not modify the internal value while cloning. Thus, we can use a Relaxed ordering here, which implies no happens-before relationship but is atomic. When Dropping the Arc, however, we'll need to atomically synchronize when decrementing the reference count. This is described more in the section on the Drop implementation for Arc. For more information on atomic relationships and Relaxed ordering, see the section on atomics.

Thus, the code becomes this:

let old_rc = inner.rc.fetch_add(1, Ordering::Relaxed);
We'll need to add another import to use Ordering:

use std::sync::atomic::Ordering;
However, we have one problem with this implementation right now. What if someone decides to mem::forget a bunch of Arcs? The code we have written so far (and will write) assumes that the reference count accurately portrays how many Arcs are in memory, but with mem::forget this is false. Thus, when more and more Arcs are cloned from this one without them being Dropped and the reference count being decremented, we can overflow! This will cause use-after-free which is INCREDIBLY BAD!

To handle this, we need to check that the reference count does not go over some arbitrary value (below usize::MAX, as we're storing the reference count as an AtomicUsize), and do something.

The standard library's implementation decides to just abort the program (as it is an incredibly unlikely case in normal code and if it happens, the program is probably incredibly degenerate) if the reference count reaches isize::MAX (about half of usize::MAX) on any thread, on the assumption that there are probably not about 2 billion threads (or about 9 quintillion on some 64-bit machines) incrementing the reference count at once. This is what we'll do.

It's pretty simple to implement this behavior:

if old_rc >= isize::MAX as usize {
    std::process::abort();
}
Then, we need to return a new instance of the Arc:

Self {
    ptr: self.ptr,
    phantom: PhantomData
}
Now, let's wrap this all up inside the Clone implementation:

use std::sync::atomic::Ordering;

impl<T> Clone for Arc<T> {
    fn clone(&self) -> Arc<T> {
        let inner = unsafe { self.ptr.as_ref() };
        // Using a relaxed ordering is alright here as we don't need any atomic
        // synchronization here as we're not modifying or accessing the inner
        // data.
        let old_rc = inner.rc.fetch_add(1, Ordering::Relaxed);

        if old_rc >= isize::MAX as usize {
            std::process::abort();
        }

        Self {
            ptr: self.ptr,
            phantom: PhantomData,
        }
    }
}
### Dropping

We now need a way to decrease the reference count and drop the data once it is low enough, otherwise the data will live forever on the heap.

To do this, we can implement Drop.

Basically, we need to:

Decrement the reference count
If there is only one reference remaining to the data, then:
Atomically fence the data to prevent reordering of the use and deletion of the data
Drop the inner data
First, we'll need to get access to the ArcInner:

let inner = unsafe { self.ptr.as_ref() };
Now, we need to decrement the reference count. To streamline our code, we can also return if the returned value from fetch_sub (the value of the reference count before decrementing it) is not equal to 1 (which happens when we are not the last reference to the data).

if inner.rc.fetch_sub(1, Ordering::Release) != 1 {
    return;
}
We then need to create an atomic fence to prevent reordering of the use of the data and deletion of the data. As described in the standard library's implementation of Arc:

This fence is needed to prevent reordering of use of the data and deletion of the data. Because it is marked Release, the decreasing of the reference count synchronizes with this Acquire fence. This means that use of the data happens before decreasing the reference count, which happens before this fence, which happens before the deletion of the data.

As explained in the Boost documentation,

It is important to enforce any possible access to the object in one thread (through an existing reference) to happen before deleting the object in a different thread. This is achieved by a "release" operation after dropping a reference (any access to the object through this reference must obviously happened before), and an "acquire" operation before deleting the object.

In particular, while the contents of an Arc are usually immutable, it's possible to have interior writes to something like a Mutex<T>. Since a Mutex is not acquired when it is deleted, we can't rely on its synchronization logic to make writes in thread A visible to a destructor running in thread B.

Also note that the Acquire fence here could probably be replaced with an Acquire load, which could improve performance in highly-contended situations. See 2.

To do this, we do the following:

use std::sync::atomic;
atomic::fence(Ordering::Acquire);
Finally, we can drop the data itself. We use Box::from_raw to drop the boxed ArcInner<T> and its data. This takes a *mut T and not a NonNull<T>, so we must convert using NonNull::as_ptr.

unsafe { Box::from_raw(self.ptr.as_ptr()); }
This is safe as we know we have the last pointer to the ArcInner and that its pointer is valid.

Now, let's wrap this all up inside the Drop implementation:

impl<T> Drop for Arc<T> {
    fn drop(&mut self) {
        let inner = unsafe { self.ptr.as_ref() };
        if inner.rc.fetch_sub(1, Ordering::Release) != 1 {
            return;
        }
        // This fence is needed to prevent reordering of the use and deletion
        // of the data.
        atomic::fence(Ordering::Acquire);
        // This is safe as we know we have the last pointer to the `ArcInner`
        // and that its pointer is valid.
        unsafe { Box::from_raw(self.ptr.as_ptr()); }
    }
}
### Final Code

Here's the final code, with some added comments and re-ordered imports:

use std::marker::PhantomData;
use std::ops::Deref;
use std::ptr::NonNull;
use std::sync::atomic::{self, AtomicUsize, Ordering};

pub struct Arc<T> {
    ptr: NonNull<ArcInner<T>>,
    phantom: PhantomData<ArcInner<T>>,
}

pub struct ArcInner<T> {
    rc: AtomicUsize,
    data: T,
}

impl<T> Arc<T> {
    pub fn new(data: T) -> Arc<T> {
        // We start the reference count at 1, as that first reference is the
        // current pointer.
        let boxed = Box::new(ArcInner {
            rc: AtomicUsize::new(1),
            data,
        });
        Arc {
            // It is okay to call `.unwrap()` here as we get a pointer from
            // `Box::into_raw` which is guaranteed to not be null.
            ptr: NonNull::new(Box::into_raw(boxed)).unwrap(),
            phantom: PhantomData,
        }
    }
}

unsafe impl<T: Sync + Send> Send for Arc<T> {}
unsafe impl<T: Sync + Send> Sync for Arc<T> {}

impl<T> Deref for Arc<T> {
    type Target = T;

    fn deref(&self) -> &T {
        let inner = unsafe { self.ptr.as_ref() };
        &inner.data
    }
}

impl<T> Clone for Arc<T> {
    fn clone(&self) -> Arc<T> {
        let inner = unsafe { self.ptr.as_ref() };
        // Using a relaxed ordering is alright here as we don't need any atomic
        // synchronization here as we're not modifying or accessing the inner
        // data.
        let old_rc = inner.rc.fetch_add(1, Ordering::Relaxed);

        if old_rc >= isize::MAX as usize {
            std::process::abort();
        }

        Self {
            ptr: self.ptr,
            phantom: PhantomData,
        }
    }
}

impl<T> Drop for Arc<T> {
    fn drop(&mut self) {
        let inner = unsafe { self.ptr.as_ref() };
        if inner.rc.fetch_sub(1, Ordering::Release) != 1 {
            return;
        }
        // This fence is needed to prevent reordering of the use and deletion
        // of the data.
        atomic::fence(Ordering::Acquire);
        // This is safe as we know we have the last pointer to the `ArcInner`
        // and that its pointer is valid.
        unsafe { Box::from_raw(self.ptr.as_ptr()); }
    }
}
Foreign Function Interface

Introduction

This guide will use the snappy compression/decompression library as an introduction to writing bindings for foreign code. Rust is currently unable to call directly into a C++ library, but snappy includes a C interface (documented in snappy-c.h).

A note about libc

Many of these examples use the libc crate, which provides various type definitions for C types, among other things. If you’re trying these examples yourself, you’ll need to add libc to your Cargo.toml:

[dependencies]
libc = "0.2.0"
Prepare the build script

Because snappy is a static library by default. So there is no C++ std linked in the output artifact. n order to use this foreign library in Rust, we have to manually specify that we want to link stdc++ in our project. The easiest way to do this is by setting up a build script.

First edit Cargo.toml, inside package add build = "build.rs":

[package]
...
build = "build.rs"
Then create a new file at the root of your workspace, named build.rs:

// build.rs
fn main() {
    println!("cargo:rustc-link-lib=dylib=stdc++"); // This line may be unnecessary for some environment.
    println!("cargo:rustc-link-search=<YOUR SNAPPY LIBRARY PATH>");
}
For more information, please read The Cargo Book - build script.

Calling foreign functions

The following is a minimal example of calling a foreign function which will compile if snappy is installed:

use libc::size_t;

#[link(name = "snappy")]
unsafe extern "C" {
    fn snappy_max_compressed_length(source_length: size_t) -> size_t;
}

fn main() {
    let x = unsafe { snappy_max_compressed_length(100) };
    println!("max compressed length of a 100 byte buffer: {}", x);
}
The extern block is a list of function signatures in a foreign library, in this case with the platform's C ABI. The #[link(...)] attribute is used to instruct the linker to link against the snappy library so the symbols are resolved.

Foreign functions are assumed to be unsafe so calls to them need to be wrapped with unsafe {} as a promise to the compiler that everything contained within truly is safe. C libraries often expose interfaces that aren't thread-safe, and almost any function that takes a pointer argument isn't valid for all possible inputs since the pointer could be dangling, and raw pointers fall outside of Rust's safe memory model.

When declaring the argument types to a foreign function, the Rust compiler cannot check if the declaration is correct, so specifying it correctly is part of keeping the binding correct at runtime.

The extern block can be extended to cover the entire snappy API:

use libc::{c_int, size_t};

#[link(name = "snappy")]
unsafe extern "C" {
    fn snappy_compress(input: *const u8,
                       input_length: size_t,
                       compressed: *mut u8,
                       compressed_length: *mut size_t) -> c_int;
    fn snappy_uncompress(compressed: *const u8,
                         compressed_length: size_t,
                         uncompressed: *mut u8,
                         uncompressed_length: *mut size_t) -> c_int;
    fn snappy_max_compressed_length(source_length: size_t) -> size_t;
    fn snappy_uncompressed_length(compressed: *const u8,
                                  compressed_length: size_t,
                                  result: *mut size_t) -> c_int;
    fn snappy_validate_compressed_buffer(compressed: *const u8,
                                         compressed_length: size_t) -> c_int;
}
Creating a safe interface

The raw C API needs to be wrapped to provide memory safety and make use of higher-level concepts like vectors. A library can choose to expose only the safe, high-level interface and hide the unsafe internal details.

Wrapping the functions which expect buffers involves using the slice::raw module to manipulate Rust vectors as pointers to memory. Rust's vectors are guaranteed to be a contiguous block of memory. The length is the number of elements currently contained, and the capacity is the total size in elements of the allocated memory. The length is less than or equal to the capacity.

pub fn validate_compressed_buffer(src: &[u8]) -> bool {
    unsafe {
        snappy_validate_compressed_buffer(src.as_ptr(), src.len() as size_t) == 0
    }
}
The validate_compressed_buffer wrapper above makes use of an unsafe block, but it makes the guarantee that calling it is safe for all inputs by leaving off unsafe from the function signature.

The snappy_compress and snappy_uncompress functions are more complex, since a buffer has to be allocated to hold the output too.

The snappy_max_compressed_length function can be used to allocate a vector with the maximum required capacity to hold the compressed output. The vector can then be passed to the snappy_compress function as an output parameter. An output parameter is also passed to retrieve the true length after compression for setting the length.

pub fn compress(src: &[u8]) -> Vec<u8> {
    unsafe {
        let srclen = src.len() as size_t;
        let psrc = src.as_ptr();

        let mut dstlen = snappy_max_compressed_length(srclen);
        let mut dst = Vec::with_capacity(dstlen as usize);
        let pdst = dst.as_mut_ptr();

        snappy_compress(psrc, srclen, pdst, &mut dstlen);
        dst.set_len(dstlen as usize);
        dst
    }
}
Decompression is similar, because snappy stores the uncompressed size as part of the compression format and snappy_uncompressed_length will retrieve the exact buffer size required.

pub fn uncompress(src: &[u8]) -> Option<Vec<u8>> {
    unsafe {
        let srclen = src.len() as size_t;
        let psrc = src.as_ptr();

        let mut dstlen: size_t = 0;
        snappy_uncompressed_length(psrc, srclen, &mut dstlen);

        let mut dst = Vec::with_capacity(dstlen as usize);
        let pdst = dst.as_mut_ptr();

        if snappy_uncompress(psrc, srclen, pdst, &mut dstlen) == 0 {
            dst.set_len(dstlen as usize);
            Some(dst)
        } else {
            None // SNAPPY_INVALID_INPUT
        }
    }
}
Then, we can add some tests to show how to use them.

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid() {
        let d = vec![0xde, 0xad, 0xd0, 0x0d];
        let c: &[u8] = &compress(&d);
        assert!(validate_compressed_buffer(c));
        assert!(uncompress(c) == Some(d));
    }

    #[test]
    fn invalid() {
        let d = vec![0, 0, 0, 0];
        assert!(!validate_compressed_buffer(&d));
        assert!(uncompress(&d).is_none());
    }

    #[test]
    fn empty() {
        let d = vec![];
        assert!(!validate_compressed_buffer(&d));
        assert!(uncompress(&d).is_none());
        let c = compress(&d);
        assert!(validate_compressed_buffer(&c));
        assert!(uncompress(&c) == Some(d));
    }
}
Destructors

Foreign libraries often hand off ownership of resources to the calling code. When this occurs, we must use Rust's destructors to provide safety and guarantee the release of these resources (especially in the case of panic).

For more about destructors, see the Drop trait.

Calling Rust code from C

You may wish to compile Rust code in a way so that it can be called from C. This is fairly easy, but requires a few things.

Rust side

First, we assume you have a lib crate named as rust_from_c. lib.rs should have Rust code as following:

#[unsafe(no_mangle)]
pub extern "C" fn hello_from_rust() {
    println!("Hello from Rust!");
}
The extern "C" makes this function adhere to the C calling convention, as discussed below in "Foreign Calling Conventions". The no_mangle attribute turns off Rust's name mangling, so that it has a well defined symbol to link to.

Then, to compile Rust code as a shared library that can be called from C, add the following to your Cargo.toml:

[lib]
crate-type = ["cdylib"]
(NOTE: We could also use the staticlib crate type but it needs to tweak some linking flags.)

Run cargo build and you're ready to go on the Rust side.

C side

We'll create a C file to call the hello_from_rust function and compile it by gcc.

C file should look like:

extern void hello_from_rust();

int main(void) {
    hello_from_rust();
    return 0;
}
We name the file as call_rust.c and place it on the crate root. Run the following to compile:

gcc call_rust.c -o call_rust -lrust_from_c -L./target/debug
-l and -L tell gcc to find our Rust library.

Finally, we can call Rust code from C with LD_LIBRARY_PATH specified:

$ LD_LIBRARY_PATH=./target/debug ./call_rust
Hello from Rust!
That's it! For more realistic example, check the cbindgen.

Callbacks from C code to Rust functions

Some external libraries require the usage of callbacks to report back their current state or intermediate data to the caller. It is possible to pass functions defined in Rust to an external library. The requirement for this is that the callback function is marked as extern with the correct calling convention to make it callable from C code.

The callback function can then be sent through a registration call to the C library and afterwards be invoked from there.

A basic example is:

Rust code:

extern fn callback(a: i32) {
    println!("I'm called from C with value {0}", a);
}

#[link(name = "extlib")]
unsafe extern {
   fn register_callback(cb: extern fn(i32)) -> i32;
   fn trigger_callback();
}

fn main() {
    unsafe {
        register_callback(callback);
        trigger_callback(); // Triggers the callback.
    }
}
C code:

typedef void (*rust_callback)(int32_t);
rust_callback cb;

int32_t register_callback(rust_callback callback) {
    cb = callback;
    return 1;
}

void trigger_callback() {
  cb(7); // Will call callback(7) in Rust.
}
In this example Rust's main() will call trigger_callback() in C, which would, in turn, call back to callback() in Rust.

Targeting callbacks to Rust objects

The former example showed how a global function can be called from C code. However it is often desired that the callback is targeted to a special Rust object. This could be the object that represents the wrapper for the respective C object.

This can be achieved by passing a raw pointer to the object down to the C library. The C library can then include the pointer to the Rust object in the notification. This will allow the callback to unsafely access the referenced Rust object.

Rust code:

struct RustObject {
    a: i32,
    // Other members...
}

unsafe extern "C" fn callback(target: *mut RustObject, a: i32) {
    println!("I'm called from C with value {0}", a);
    unsafe {
        // Update the value in RustObject with the value received from the callback:
        (*target).a = a;
    }
}

#[link(name = "extlib")]
unsafe extern {
   fn register_callback(target: *mut RustObject,
                        cb: unsafe extern fn(*mut RustObject, i32)) -> i32;
   fn trigger_callback();
}

fn main() {
    // Create the object that will be referenced in the callback:
    let mut rust_object = Box::new(RustObject { a: 5 });

    unsafe {
        register_callback(&mut *rust_object, callback);
        trigger_callback();
    }
}
C code:

typedef void (*rust_callback)(void*, int32_t);
void* cb_target;
rust_callback cb;

int32_t register_callback(void* callback_target, rust_callback callback) {
    cb_target = callback_target;
    cb = callback;
    return 1;
}

void trigger_callback() {
  cb(cb_target, 7); // Will call callback(&rustObject, 7) in Rust.
}
Asynchronous callbacks

In the previously given examples the callbacks are invoked as a direct reaction to a function call to the external C library. The control over the current thread is switched from Rust to C to Rust for the execution of the callback, but in the end the callback is executed on the same thread that called the function which triggered the callback.

Things get more complicated when the external library spawns its own threads and invokes callbacks from there. In these cases access to Rust data structures inside the callbacks is especially unsafe and proper synchronization mechanisms must be used. Besides classical synchronization mechanisms like mutexes, one possibility in Rust is to use channels (in std::sync::mpsc) to forward data from the C thread that invoked the callback into a Rust thread.

If an asynchronous callback targets a special object in the Rust address space it is also absolutely necessary that no more callbacks are performed by the C library after the respective Rust object gets destroyed. This can be achieved by unregistering the callback in the object's destructor and designing the library in a way that guarantees that no callback will be performed after deregistration.

Linking

The link attribute on extern blocks provides the basic building block for instructing rustc how it will link to native libraries. There are two accepted forms of the link attribute today:

#[link(name = "foo")]
#[link(name = "foo", kind = "bar")]
In both of these cases, foo is the name of the native library that we're linking to, and in the second case bar is the type of native library that the compiler is linking to. There are currently three known types of native libraries:

Dynamic - #[link(name = "readline")]
Static - #[link(name = "my_build_dependency", kind = "static")]
Frameworks - #[link(name = "CoreFoundation", kind = "framework")]
Note that frameworks are only available on macOS targets.

The different kind values are meant to differentiate how the native library participates in linkage. From a linkage perspective, the Rust compiler creates two flavors of artifacts: partial (rlib/staticlib) and final (dylib/binary). Native dynamic library and framework dependencies are propagated to the final artifact boundary, while static library dependencies are not propagated at all, because the static libraries are integrated directly into the subsequent artifact.

A few examples of how this model can be used are:

A native build dependency. Sometimes some C/C++ glue is needed when writing some Rust code, but distribution of the C/C++ code in a library format is a burden. In this case, the code will be archived into libfoo.a and then the Rust crate would declare a dependency via #[link(name = "foo", kind = "static")].

Regardless of the flavor of output for the crate, the native static library will be included in the output, meaning that distribution of the native static library is not necessary.

A normal dynamic dependency. Common system libraries (like readline) are available on a large number of systems, and often a static copy of these libraries cannot be found. When this dependency is included in a Rust crate, partial targets (like rlibs) will not link to the library, but when the rlib is included in a final target (like a binary), the native library will be linked in.

On macOS, frameworks behave with the same semantics as a dynamic library.

Unsafe blocks

Some operations, like dereferencing raw pointers or calling functions that have been marked unsafe are only allowed inside unsafe blocks. Unsafe blocks isolate unsafety and are a promise to the compiler that the unsafety does not leak out of the block.

Unsafe functions, on the other hand, advertise it to the world. An unsafe function is written like this:

unsafe fn kaboom(ptr: *const i32) -> i32 { *ptr }
This function can only be called from an unsafe block or another unsafe function.

Accessing foreign globals

Foreign APIs often export a global variable which could do something like track global state. In order to access these variables, you declare them in extern blocks with the static keyword:

#[link(name = "readline")]
unsafe extern {
    static rl_readline_version: libc::c_int;
}

fn main() {
    println!("You have readline version {} installed.",
             unsafe { rl_readline_version as i32 });
}
Alternatively, you may need to alter global state provided by a foreign interface. To do this, statics can be declared with mut so we can mutate them.
