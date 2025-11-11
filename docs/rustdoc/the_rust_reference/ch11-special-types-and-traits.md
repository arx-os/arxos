# Special types and traits
[lang-types.intro]
Certain types and traits that exist in the standard library are known to the Rust compiler. This chapter documents the special features of these types and traits.
[lang-types.box]
Box<T>
[lang-types.box.intro]
Box<T> has a few special features that Rust doesn’t currently allow for user defined types.
[lang-types.box.deref]
The dereference operator for Box<T> produces a place which can be moved from. This means that the * operator and the destructor of Box<T> are built-in to the language.
[lang-types.box.receiver]
Methods can take Box<Self> as a receiver.
[lang-types.box.fundamental]
A trait may be implemented for Box<T> in the same crate as T, which the orphan rules prevent for other generic types.
[lang-types.rc]
Rc<T>
[lang-types.rc.receiver]
Methods can take Rc<Self> as a receiver.
[lang-types.arc]
Arc<T>
[lang-types.arc.receiver]
Methods can take Arc<Self> as a receiver.
[lang-types.pin]
Pin<P>
[lang-types.pin.receiver]
Methods can take Pin<P> as a receiver.
[lang-types.unsafe-cell]
UnsafeCell<T>
[lang-types.unsafe-cell.interior-mut]
std::cell::UnsafeCell<T> is used for interior mutability. It ensures that the compiler doesn’t perform optimisations that are incorrect for such types.
[lang-types.unsafe-cell.read-only-alloc]
It also ensures that static items which have a type with interior mutability aren’t placed in memory marked as read only.
[lang-types.phantom-data]
PhantomData<T>
std::marker::PhantomData<T> is a zero-sized, minimum alignment, type that is considered to own a T for the purposes of variance, drop check, and auto traits.
[lang-types.ops]
Operator Traits
The traits in std::ops and std::cmp are used to overload operators, indexing expressions, and call expressions.
[lang-types.deref]
Deref and DerefMut
As well as overloading the unary * operator, Deref and DerefMut are also used in method resolution and deref coercions.
[lang-types.drop]
Drop
The Drop trait provides a destructor, to be run whenever a value of this type is to be destroyed.
[lang-types.copy]
Copy
[lang-types.copy.intro]
The Copy trait changes the semantics of a type implementing it.
[lang-types.copy.behavior]
Values whose type implements Copy are copied rather than moved upon assignment.
[lang-types.copy.constraint]
Copy can only be implemented for types which do not implement Drop, and whose fields are all Copy. For enums, this means all fields of all variants have to be Copy. For unions, this means all variants have to be Copy.
[lang-types.copy.builtin-types]
Copy is implemented by the compiler for
[lang-types.copy.tuple]
Tuples of Copy types
[lang-types.copy.fn-pointer]
Function pointers
[lang-types.copy.fn-item]
Function items
[lang-types.copy.closure]
Closures that capture no values or that only capture values of Copy types
[lang-types.clone]
Clone
[lang-types.clone.intro]
The Clone trait is a supertrait of Copy, so it also needs compiler generated implementations.
[lang-types.clone.builtin-types]
It is implemented by the compiler for the following types:
[lang-types.clone.builtin-copy]
Types with a built-in Copy implementation (see above)
[lang-types.clone.tuple]
Tuples of Clone types
[lang-types.clone.closure]
Closures that only capture values of Clone types or capture no values from the environment
[lang-types.send]
Send
The Send trait indicates that a value of this type is safe to send from one thread to another.
[lang-types.sync]
Sync
[lang-types.sync.intro]
The Sync trait indicates that a value of this type is safe to share between multiple threads.
[lang-types.sync.static-constraint]
This trait must be implemented for all types used in immutable static items.
[lang-types.termination]
Termination
The Termination trait indicates the acceptable return types for the main function and test functions.
[lang-types.auto-traits]
Auto traits
The Send, Sync, Unpin, UnwindSafe, and RefUnwindSafe traits are auto traits. Auto traits have special properties.
[lang-types.auto-traits.auto-impl]
If no explicit implementation or negative implementation is written out for an auto trait for a given type, then the compiler implements it automatically according to the following rules:
[lang-types.auto-traits.builtin-composite]
&T, &mut T, *const T, *mut T, [T; n], and [T] implement the trait if T does.
[lang-types.auto-traits.fn-item-pointer]
Function item types and function pointers automatically implement the trait.
[lang-types.auto-traits.aggregate]
Structs, enums, unions, and tuples implement the trait if all of their fields do.
[lang-types.auto-traits.closure]
Closures implement the trait if the types of all of their captures do. A closure that captures a T by shared reference and a U by value implements any auto traits that both &T and U do.
[lang-types.auto-traits.generic-impl]
For generic types (counting the built-in types above as generic over T), if a generic implementation is available, then the compiler does not automatically implement it for types that could use the implementation except that they do not meet the requisite trait bounds. For instance, the standard library implements Send for all &T where T is Sync; this means that the compiler will not implement Send for &T if T is Send but not Sync.
[lang-types.auto-traits.negative]
Auto traits can also have negative implementations, shown as impl !AutoTrait for T in the standard library documentation, that override the automatic implementations. For example *mut T has a negative implementation of Send, and so *mut T is not Send, even if T is. There is currently no stable way to specify additional negative implementations; they exist only in the standard library.
[lang-types.auto-traits.trait-object-marker]
Auto traits may be added as an additional bound to any trait object, even though normally only one trait is allowed. For instance, Box<dyn Debug + Send + UnwindSafe> is a valid type.
[lang-types.sized]
Sized
[lang-types.sized.intro]
The Sized trait indicates that the size of this type is known at compile-time; that is, it’s not a dynamically sized type.
[lang-types.sized.implicit-sized]
Type parameters (except Self in traits) are Sized by default, as are associated types.
[lang-types.sized.implicit-impl]
Sized is always implemented automatically by the compiler, not by implementation items.
[lang-types.sized.relaxation]
These implicit Sized bounds may be relaxed by using the special ?Sized bound.
[names]
