# Attributes
Derive macros
[items.use.path.disallowed]
They cannot import associated items, generic parameters, local variables, paths with Self, or tool attributes. More restrictions are described below.
[items.use.path.namespace]
use will create bindings for all namespaces from the imported entities, with the exception that a self import will only import from the type namespace (as described below). For example, the following illustrates creating bindings for the same name in two namespaces:
mod stuff {
    pub struct Foo(pub i32);
}

// Imports the `Foo` type and the `Foo` constructor.
use stuff::Foo;

fn example() {
    let ctor = Foo; // Uses `Foo` from the value namespace.
    let x: Foo = ctor(123); // Uses `Foo` From the type namespace.
}
[items.use.path.edition2018]
2018
Edition differences

In the 2015 edition, use paths are relative to the crate root. For example:

mod foo {
    pub mod example { pub mod iter {} }
    pub mod baz { pub fn foobaz() {} }
}
mod bar {
    // Resolves `foo` from the crate root.
    use foo::example::iter;
    // The `::` prefix explicitly resolves `foo`
    // from the crate root.
    use ::foo::baz::foobaz;
}

The 2015 edition does not allow use declarations to reference the extern prelude. Thus, extern crate declarations are still required in 2015 to reference an external crate in a use declaration. Beginning with the 2018 edition, use declarations can specify an external crate dependency the same way extern crate can.
[items.use.as]
as renames
The as keyword can be used to change the name of an imported entity. For example:
// Creates a non-public alias `bar` for the function `foo`.
use inner::foo as bar;

mod inner {
    pub fn foo() {}
}
[items.use.multiple-syntax]
Brace syntax
[items.use.multiple-syntax.intro]
Braces can be used in the last segment of the path to import multiple entities from the previous segment, or, if there are no previous segments, from the current scope. Braces can be nested, creating a tree of paths, where each grouping of segments is logically combined with its parent to create a full path.
// Creates bindings to:
// - `std::collections::BTreeSet`
// - `std::collections::hash_map`
// - `std::collections::hash_map::HashMap`
use std::collections::{BTreeSet, hash_map::{self, HashMap}};
[items.use.multiple-syntax.empty]
An empty brace does not import anything, though the leading path is validated that it is accessible.
[items.use.multiple-syntax.edition2018]
2018
Edition differences

In the 2015 edition, paths are relative to the crate root, so an import such as use {foo, bar}; will import the names foo and bar from the crate root, whereas starting in 2018, those names are relative to the current scope.
[items.use.self]
self imports
[items.use.self.intro]
The keyword self may be used within brace syntax to create a binding of the parent entity under its own name.
mod stuff {
    pub fn foo() {}
    pub fn bar() {}
}
mod example {
    // Creates a binding for `stuff` and `foo`.
    use crate::stuff::{self, foo};
    pub fn baz() {
        foo();
        stuff::bar();
    }
}
[items.use.self.namespace]
self only creates a binding from the type namespace of the parent entity. For example, in the following, only the foo mod is imported:
mod bar {
    pub mod foo {}
    pub fn foo() {}
}

// This only imports the module `foo`. The function `foo` lives in
// the value namespace and is not imported.
use bar::foo::{self};

fn main() {
    foo(); //~ ERROR `foo` is a module
}
Note

self may also be used as the first segment of a path. The usage of self as the first segment and inside a use brace is logically the same; it means the current module of the parent segment, or the current module if there is no parent segment. See self in the paths chapter for more information on the meaning of a leading self.
[items.use.glob]
Glob imports
[items.use.glob.intro]
The * character may be used as the last segment of a use path to import all importable entities from the entity of the preceding segment. For example:
// Creates a non-public alias to `bar`.
use foo::*;

mod foo {
    fn i_am_private() {}
    enum Example {
        V1,
        V2,
    }
    pub fn bar() {
        // Creates local aliases to `V1` and `V2`
        // of the `Example` enum.
        use Example::*;
        let x = V1;
    }
}
[items.use.glob.shadowing]
Items and named imports are allowed to shadow names from glob imports in the same namespace. That is, if there is a name already defined by another item in the same namespace, the glob import will be shadowed. For example:
// This creates a binding to the `clashing::Foo` tuple struct
// constructor, but does not import its type because that would
// conflict with the `Foo` struct defined here.
//
// Note that the order of definition here is unimportant.
use clashing::*;
struct Foo {
    field: f32,
}

fn do_stuff() {
    // Uses the constructor from `clashing::Foo`.
    let f1 = Foo(123);
    // The struct expression uses the type from
    // the `Foo` struct defined above.
    let f2 = Foo { field: 1.0 };
    // `Bar` is also in scope due to the glob import.
    let z = Bar {};
}

mod clashing {
    pub struct Foo(pub i32);
    pub struct Bar {}
}
[items.use.glob.last-segment-only]
* cannot be used as the first or intermediate segments.
[items.use.glob.self-import]
* cannot be used to import a module’s contents into itself (such as use self::*;).
[items.use.glob.edition2018]
2018
Edition differences

In the 2015 edition, paths are relative to the crate root, so an import such as use *; is valid, and it means to import everything from the crate root. This cannot be used in the crate root itself.
[items.use.as-underscore]
Underscore Imports
[items.use.as-underscore.intro]
Items can be imported without binding to a name by using an underscore with the form use path as _. This is particularly useful to import a trait so that its methods may be used without importing the trait’s symbol, for example if the trait’s symbol may conflict with another symbol. Another example is to link an external crate without importing its name.
[items.use.as-underscore.glob]
Asterisk glob imports will import items imported with _ in their unnameable form.
mod foo {
    pub trait Zoo {
        fn zoo(&self) {}
    }

    impl<T> Zoo for T {}
}

use self::foo::Zoo as _;
struct Zoo;  // Underscore import avoids name conflict with this item.

fn main() {
    let z = Zoo;
    z.zoo();
}
[items.use.as-underscore.macro]
The unique, unnameable symbols are created after macro expansion so that macros may safely emit multiple references to _ imports. For example, the following should not produce an error:
macro_rules! m {
    ($item: item) => { $item $item }
}

m!(use std as _;);
// This expands to:
// use std as _;
// use std as _;
[items.use.restrictions]
Restrictions
The following are restrictions for valid use declarations:
[items.use.restrictions.crate]
use crate; must use as to define the name to which to bind the crate root.
[items.use.restrictions.self]
use {self}; is an error; there must be a leading segment when using self.
[items.use.restrictions.duplicate-name]
As with any item definition, use imports cannot create duplicate bindings of the same name in the same namespace in a module or block.
[items.use.restrictions.macro-crate]
use paths with $crate are not allowed in a macro_rules expansion.
[items.use.restrictions.variant]
use paths cannot refer to enum variants through a type alias. For example:
enum MyEnum {
    MyVariant
}
type TypeAlias = MyEnum;

use MyEnum::MyVariant; //~ OK
use TypeAlias::MyVariant; //~ ERROR
[items.use.ambiguities]
Ambiguities
Note

This section is incomplete.
[items.use.ambiguities.intro]
Some situations are an error when there is an ambiguity as to which name a use declaration refers. This happens when there are two name candidates that do not resolve to the same entity.
[items.use.ambiguities.glob]
Glob imports are allowed to import conflicting names in the same namespace as long as the name is not used. For example:
mod foo {
    pub struct Qux;
}

mod bar {
    pub struct Qux;
}

use foo::*;
use bar::*; //~ OK, no name conflict.

fn main() {
    // This would be an error, due to the ambiguity.
    //let x = Qux;
}
Multiple glob imports are allowed to import the same name, and that name is allowed to be used, if the imports are of the same item (following re-exports). The visibility of the name is the maximum visibility of the imports. For example:
mod foo {
    pub struct Qux;
}

mod bar {
    pub use super::foo::Qux;
}

// These both import the same `Qux`. The visibility of `Qux`
// is `pub` because that is the maximum visibility between
// these two `use` declarations.
pub use bar::*;
use foo::*;

fn main() {
    let _: Qux = Qux;
}
[items.fn]
Functions

[items.fn.syntax]
Syntax
Function →
    FunctionQualifiers fn IDENTIFIER GenericParams?
        ( FunctionParameters? )
        FunctionReturnType? WhereClause?
        ( BlockExpression | ; )

FunctionQualifiers → const? async?​1 ItemSafety?​2 ( extern Abi? )?

ItemSafety → safe​3 | unsafe

Abi → STRING_LITERAL | RAW_STRING_LITERAL

FunctionParameters →
      SelfParam ,?
    | ( SelfParam , )? FunctionParam ( , FunctionParam )* ,?

SelfParam → OuterAttribute* ( ShorthandSelf | TypedSelf )

ShorthandSelf → ( & | & Lifetime )? mut? self

TypedSelf → mut? self : Type

FunctionParam → OuterAttribute* ( FunctionParamPattern | ... | Type​4 )

FunctionParamPattern → PatternNoTopAlt : ( Type | ... )

FunctionReturnType → -> Type

Show syntax diagrams

[items.fn.intro]
A function consists of a block (that’s the body of the function), along with a name, a set of parameters, and an output type. Other than a name, all these are optional.
[items.fn.namespace]
Functions are declared with the keyword fn which defines the given name in the value namespace of the module or block where it is located.
[items.fn.signature]
Functions may declare a set of input variables as parameters, through which the caller passes arguments into the function, and the output type of the value the function will return to its caller on completion.
[items.fn.implicit-return]
If the output type is not explicitly stated, it is the unit type.
[items.fn.fn-item-type]
When referred to, a function yields a first-class value of the corresponding zero-sized function item type, which when called evaluates to a direct call to the function.
For example, this is a simple function:
fn answer_to_life_the_universe_and_everything() -> i32 {
    return 42;
}
[items.fn.safety-qualifiers]
The safe function is semantically only allowed when used in an extern block.
[items.fn.params]
Function parameters
[items.fn.params.intro]
Function parameters are irrefutable patterns, so any pattern that is valid in an else-less let binding is also valid as a parameter:
fn first((value, _): (i32, i32)) -> i32 { value }
[items.fn.params.self-pat]
If the first parameter is a SelfParam, this indicates that the function is a method.
[items.fn.params.self-restriction]
Functions with a self parameter may only appear as an associated function in a trait or implementation.
[items.fn.params.varargs]
A parameter with the ... token indicates a variadic function, and may only be used as the last parameter of an external block function. The variadic parameter may have an optional identifier, such as args: ....
[items.fn.body]
Function body
[items.fn.body.intro]
The body block of a function is conceptually wrapped in another block that first binds the argument patterns and then returns the value of the function’s body. This means that the tail expression of the block, if evaluated, ends up being returned to the caller. As usual, an explicit return expression within the body of the function will short-cut that implicit return, if reached.
For example, the function above behaves as if it was written as:
// argument_0 is the actual first argument passed from the caller
let (value, _) = argument_0;
return {
    value
};
[items.fn.body.bodyless]
Functions without a body block are terminated with a semicolon. This form may only appear in a trait or external block.
[items.fn.generics]
Generic functions
[items.fn.generics.intro]
A generic function allows one or more parameterized types to appear in its signature. Each type parameter must be explicitly declared in an angle-bracket-enclosed and comma-separated list, following the function name.
// foo is generic over A and B

fn foo<A, B>(x: A, y: B) {
[items.fn.generics.param-names]
Inside the function signature and body, the name of the type parameter can be used as a type name.
[items.fn.generics.param-bounds]
Trait bounds can be specified for type parameters to allow methods with that trait to be called on values of that type. This is specified using the where syntax:
fn foo<T>(x: T) where T: Debug {
[items.fn.generics.mono]
When a generic function is referenced, its type is instantiated based on the context of the reference. For example, calling the foo function here:
use std::fmt::Debug;

fn foo<T>(x: &[T]) where T: Debug {
    // details elided
}

foo(&[1, 2]);
will instantiate type parameter T with i32.
[items.fn.generics.explicit-arguments]
The type parameters can also be explicitly supplied in a trailing path component after the function name. This might be necessary if there is not sufficient context to determine the type parameters. For example, mem::size_of::<u32>() == 4.
[items.fn.extern]
Extern function qualifier
[items.fn.extern.intro]
The extern function qualifier allows providing function definitions that can be called with a particular ABI:
extern "ABI" fn foo() { /* ... */ }
[items.fn.extern.def]
These are often used in combination with external block items which provide function declarations that can be used to call functions without providing their definition:
unsafe extern "ABI" {
  unsafe fn foo(); /* no body */
  safe fn bar(); /* no body */
}
unsafe { foo() };
bar();
[items.fn.extern.default-abi]
When "extern" Abi?* is omitted from FunctionQualifiers in function items, the ABI "Rust" is assigned. For example:
fn foo() {}
is equivalent to:
extern "Rust" fn foo() {}
[items.fn.extern.foreign-call]
Functions can be called by foreign code, and using an ABI that differs from Rust allows, for example, to provide functions that can be called from other programming languages like C:
// Declares a function with the "C" ABI
extern "C" fn new_i32() -> i32 { 0 }

// Declares a function with the "stdcall" ABI
extern "stdcall" fn new_i32_stdcall() -> i32 { 0 }
[items.fn.extern.default-extern]
Just as with external block, when the extern keyword is used and the "ABI" is omitted, the ABI used defaults to "C". That is, this:
extern fn new_i32() -> i32 { 0 }
let fptr: extern fn() -> i32 = new_i32;
is equivalent to:
extern "C" fn new_i32() -> i32 { 0 }
let fptr: extern "C" fn() -> i32 = new_i32;
[items.fn.extern.unwind]
Unwinding
[items.fn.extern.unwind.intro]
Most ABI strings come in two variants, one with an -unwind suffix and one without. The Rust ABI always permits unwinding, so there is no Rust-unwind ABI. The choice of ABI, together with the runtime panic handler, determines the behavior when unwinding out of a function.
[items.fn.extern.unwind.behavior]
The table below indicates the behavior of an unwinding operation reaching each type of ABI boundary (function declaration or definition using the corresponding ABI string). Note that the Rust runtime is not affected by, and cannot have an effect on, any unwinding that occurs entirely within another language’s runtime, that is, unwinds that are thrown and caught without reaching a Rust ABI boundary.
The panic-unwind column refers to panicking via the panic! macro and similar standard library mechanisms, as well as to any other Rust operations that cause a panic, such as out-of-bounds array indexing or integer overflow.
The “unwinding” ABI category refers to "Rust" (the implicit ABI of Rust functions not marked extern), "C-unwind", and any other ABI with -unwind in its name. The “non-unwinding” ABI category refers to all other ABI strings, including "C" and "stdcall".
Native unwinding is defined per-target. On targets that support throwing and catching C++ exceptions, it refers to the mechanism used to implement this feature. Some platforms implement a form of unwinding referred to as “forced unwinding”; longjmp on Windows and pthread_exit in glibc are implemented this way. Forced unwinding is explicitly excluded from the “Native unwind” column in the table.
panic runtime	ABI	panic-unwind	Native unwind (unforced)
panic=unwind	unwinding	unwind	unwind
panic=unwind	non-unwinding	abort (see notes below)	undefined behavior
panic=abort	unwinding	panic aborts without unwinding	abort
panic=abort	non-unwinding	panic aborts without unwinding	undefined behavior
[items.fn.extern.abort]
With panic=unwind, when a panic is turned into an abort by a non-unwinding ABI boundary, either no destructors (Drop calls) will run, or all destructors up until the ABI boundary will run. It is unspecified which of those two behaviors will happen.
For other considerations and limitations regarding unwinding across FFI boundaries, see the relevant section in the Panic documentation.
[items.fn.const]
Const functions
[items.fn.const.intro]
Functions qualified with the const keyword are const functions, as are tuple struct and tuple variant constructors. Const functions can be called from within const contexts.
[items.fn.const.extern]
Const functions may use the extern function qualifier.
[items.fn.const.exclusivity]
Const functions are not allowed to be async.
[items.fn.async]
Async functions
[items.fn.async.intro]
Functions may be qualified as async, and this can also be combined with the unsafe qualifier:
async fn regular_example() { }
async unsafe fn unsafe_example() { }
[items.fn.async.future]
Async functions do no work when called: instead, they capture their arguments into a future. When polled, that future will execute the function’s body.
[items.fn.async.desugar-brief]
An async function is roughly equivalent to a function that returns impl Future and with an async move block as its body:
// Source
async fn example(x: &str) -> usize {
    x.len()
}
is roughly equivalent to:
// Desugared
fn example<'a>(x: &'a str) -> impl Future<Output = usize> + 'a {
    async move { x.len() }
}
[items.fn.async.desugar]
The actual desugaring is more complex:
[items.fn.async.lifetime-capture]
The return type in the desugaring is assumed to capture all lifetime parameters from the async fn declaration. This can be seen in the desugared example above, which explicitly outlives, and hence captures, 'a.
[items.fn.async.param-capture]
The async move block in the body captures all function parameters, including those that are unused or bound to a _ pattern. This ensures that function parameters are dropped in the same order as they would be if the function were not async, except that the drop occurs when the returned future has been fully awaited.
For more information on the effect of async, see async blocks.
[items.fn.async.edition2018]
2018
Edition differences

Async functions are only available beginning with Rust 2018.
[items.fn.async.safety]
Combining async and unsafe
[items.fn.async.safety.intro]
It is legal to declare a function that is both async and unsafe. The resulting function is unsafe to call and (like any async function) returns a future. This future is just an ordinary future and thus an unsafe context is not required to “await” it:
// Returns a future that, when awaited, dereferences `x`.
//
// Soundness condition: `x` must be safe to dereference until
// the resulting future is complete.
async unsafe fn unsafe_example(x: *const i32) -> i32 {
  *x
}

async fn safe_example() {
    // An `unsafe` block is required to invoke the function initially:
    let p = 22;
    let future = unsafe { unsafe_example(&p) };

    // But no `unsafe` block required here. This will
    // read the value of `p`:
    let q = future.await;
}
Note that this behavior is a consequence of the desugaring to a function that returns an impl Future – in this case, the function we desugar to is an unsafe function, but the return value remains the same.
Unsafe is used on an async function in precisely the same way that it is used on other functions: it indicates that the function imposes some additional obligations on its caller to ensure soundness. As in any other unsafe function, these conditions may extend beyond the initial call itself – in the snippet above, for example, the unsafe_example function took a pointer x as argument, and then (when awaited) dereferenced that pointer. This implies that x would have to be valid until the future is finished executing, and it is the caller’s responsibility to ensure that.
[items.fn.attributes]
Attributes on functions
[items.fn.attributes.intro]
Outer attributes are allowed on functions. Inner attributes are allowed directly after the { inside its body block.
This example shows an inner attribute on a function. The function is documented with just the word “Example”.
fn documented() {
    #![doc = "Example"]
}
Note

Except for lints, it is idiomatic to only use outer attributes on function items.
[items.fn.attributes.builtin-attributes]
The attributes that have meaning on a function are:
cfg_attr
cfg
cold
deprecated
doc
export_name
inline
link_section
must_use
no_mangle
Lint check attributes
Procedural macro attributes
Testing attributes
[items.fn.param-attributes]
Attributes on function parameters
[items.fn.param-attributes.intro]
Outer attributes are allowed on function parameters and the permitted built-in attributes are restricted to cfg, cfg_attr, allow, warn, deny, and forbid.
fn len(
    #[cfg(windows)] slice: &[u16],
    #[cfg(not(windows))] slice: &[u8],
) -> usize {
    slice.len()
}
[items.fn.param-attributes.parsed-attributes]
Inert helper attributes used by procedural macro attributes applied to items are also allowed but be careful to not include these inert attributes in your final TokenStream.
For example, the following code defines an inert some_inert_attribute attribute that is not formally defined anywhere and the some_proc_macro_attribute procedural macro is responsible for detecting its presence and removing it from the output token stream.
#[some_proc_macro_attribute]
fn foo_oof(#[some_inert_attribute] arg: u8) {
}
The async qualifier is not allowed in the 2015 edition. ↩

Relevant to editions earlier than Rust 2024: Within extern blocks, the safe or unsafe function qualifier is only allowed when the extern is qualified as unsafe. ↩

The safe function qualifier is only allowed semantically within extern blocks. ↩

Function parameters with only a type are only allowed in an associated function of a trait item in the 2015 edition. ↩

[items.type]
Type aliases

[items.type.syntax]
Syntax
TypeAlias →
    type IDENTIFIER GenericParams? ( : TypeParamBounds )?
        WhereClause?
        ( = Type WhereClause? )? ;

Show syntax diagrams

[items.type.intro]
A type alias defines a new name for an existing type in the type namespace of the module or block where it is located. Type aliases are declared with the keyword type. Every value has a single, specific type, but may implement several different traits, and may be compatible with several different type constraints.
For example, the following defines the type Point as a synonym for the type (u8, u8), the type of pairs of unsigned 8 bit integers:
type Point = (u8, u8);
let p: Point = (41, 68);
[items.type.constructor-alias]
A type alias to a tuple-struct or unit-struct cannot be used to qualify that type’s constructor:
struct MyStruct(u32);

use MyStruct as UseAlias;
type TypeAlias = MyStruct;

let _ = UseAlias(5); // OK
let _ = TypeAlias(5); // Doesn't work
[items.type.associated-type]
A type alias, when not used as an associated type, must include a Type and may not include TypeParamBounds.
[items.type.associated-trait]
A type alias, when used as an associated type in a trait, must not include a Type specification but may include TypeParamBounds.
[items.type.associated-impl]
A type alias, when used as an associated type in a trait impl, must include a Type specification and may not include TypeParamBounds.
[items.type.deprecated]
Where clauses before the equals sign on a type alias in a trait impl (like type TypeAlias<T> where T: Foo = Bar<T>) are deprecated. Where clauses after the equals sign (like type TypeAlias<T> = Bar<T> where T: Foo) are preferred.
[items.struct]
Structs

[items.struct.syntax]
Syntax
Struct →
      StructStruct
    | TupleStruct

StructStruct →
    struct IDENTIFIER GenericParams? WhereClause? ( { StructFields? } | ; )

TupleStruct →
    struct IDENTIFIER GenericParams? ( TupleFields? ) WhereClause? ;

StructFields → StructField ( , StructField )* ,?

StructField → OuterAttribute* Visibility? IDENTIFIER : Type

TupleFields → TupleField ( , TupleField )* ,?

TupleField → OuterAttribute* Visibility? Type

Show syntax diagrams

[items.struct.intro]
A struct is a nominal struct type defined with the keyword struct.
[items.struct.namespace]
A struct declaration defines the given name in the type namespace of the module or block where it is located.
An example of a struct item and its use:
struct Point {x: i32, y: i32}
let p = Point {x: 10, y: 11};
let px: i32 = p.x;
[items.struct.tuple]
A tuple struct is a nominal tuple type, and is also defined with the keyword struct. In addition to defining a type, it also defines a constructor of the same name in the value namespace. The constructor is a function which can be called to create a new instance of the struct. For example:
struct Point(i32, i32);
let p = Point(10, 11);
let px: i32 = match p { Point(x, _) => x };
[items.struct.unit]
A unit-like struct is a struct without any fields, defined by leaving off the list of fields entirely. Such a struct implicitly defines a constant of its type with the same name. For example:
struct Cookie;
let c = [Cookie, Cookie {}, Cookie, Cookie {}];
is equivalent to
struct Cookie {}
const Cookie: Cookie = Cookie {};
let c = [Cookie, Cookie {}, Cookie, Cookie {}];
[items.struct.layout]
The precise memory layout of a struct is not specified. One can specify a particular layout using the repr attribute.
[items.enum]
Enumerations

[items.enum.syntax]
Syntax
Enumeration →
    enum IDENTIFIER GenericParams? WhereClause? { EnumVariants? }

EnumVariants → EnumVariant ( , EnumVariant )* ,?

EnumVariant →
    OuterAttribute* Visibility?
    IDENTIFIER ( EnumVariantTuple | EnumVariantStruct )? EnumVariantDiscriminant?

EnumVariantTuple → ( TupleFields? )

EnumVariantStruct → { StructFields? }

EnumVariantDiscriminant → = Expression

Show syntax diagrams

[items.enum.intro]
An enumeration, also referred to as an enum, is a simultaneous definition of a nominal enumerated type as well as a set of constructors, that can be used to create or pattern-match values of the corresponding enumerated type.
[items.enum.decl]
Enumerations are declared with the keyword enum.
[items.enum.namespace]
The enum declaration defines the enumeration type in the type namespace of the module or block where it is located.
An example of an enum item and its use:
enum Animal {
    Dog,
    Cat,
}

let mut a: Animal = Animal::Dog;
a = Animal::Cat;
[items.enum.constructor]
Enum constructors can have either named or unnamed fields:
enum Animal {
    Dog(String, f64),
    Cat { name: String, weight: f64 },
}

let mut a: Animal = Animal::Dog("Cocoa".to_string(), 37.2);
a = Animal::Cat { name: "Spotty".to_string(), weight: 2.7 };
In this example, Cat is a struct-like enum variant, whereas Dog is simply called an enum variant.
[items.enum.fieldless]
An enum where no constructors contain fields are called a field-less enum. For example, this is a fieldless enum:
enum Fieldless {
    Tuple(),
    Struct{},
    Unit,
}
[items.enum.unit-only]
If a field-less enum only contains unit variants, the enum is called an unit-only enum. For example:
enum Enum {
    Foo = 3,
    Bar = 2,
    Baz = 1,
}
[items.enum.constructor-names]
Variant constructors are similar to struct definitions, and can be referenced by a path from the enumeration name, including in use declarations.
[items.enum.constructor-namespace]
Each variant defines its type in the type namespace, though that type cannot be used as a type specifier. Tuple-like and unit-like variants also define a constructor in the value namespace.
[items.enum.struct-expr]
A struct-like variant can be instantiated with a struct expression.
[items.enum.tuple-expr]
A tuple-like variant can be instantiated with a call expression or a struct expression.
[items.enum.path-expr]
A unit-like variant can be instantiated with a path expression or a struct expression. For example:
enum Examples {
    UnitLike,
    TupleLike(i32),
    StructLike { value: i32 },
}

use Examples::*; // Creates aliases to all variants.
let x = UnitLike; // Path expression of the const item.
let x = UnitLike {}; // Struct expression.
let y = TupleLike(123); // Call expression.
let y = TupleLike { 0: 123 }; // Struct expression using integer field names.
let z = StructLike { value: 123 }; // Struct expression.
[items.enum.discriminant]
Discriminants
[items.enum.discriminant.intro]
Each enum instance has a discriminant: an integer logically associated to it that is used to determine which variant it holds.
[items.enum.discriminant.repr-rust]
Under the Rust representation, the discriminant is interpreted as an isize value. However, the compiler is allowed to use a smaller type (or another means of distinguishing variants) in its actual memory layout.
Assigning discriminant values
[items.enum.discriminant.explicit]
Explicit discriminants
[items.enum.discriminant.explicit.intro]
In two circumstances, the discriminant of a variant may be explicitly set by following the variant name with = and a constant expression:
[items.enum.discriminant.explicit.unit-only]
if the enumeration is “unit-only”.
[items.enum.discriminant.explicit.primitive-repr]
if a primitive representation is used. For example:

#[repr(u8)]
enum Enum {
    Unit = 3,
    Tuple(u16),
    Struct {
        a: u8,
        b: u16,
    } = 1,
}
[items.enum.discriminant.implicit]
Implicit discriminants
If a discriminant for a variant is not specified, then it is set to one higher than the discriminant of the previous variant in the declaration. If the discriminant of the first variant in the declaration is unspecified, then it is set to zero.
enum Foo {
    Bar,            // 0
    Baz = 123,      // 123
    Quux,           // 124
}

let baz_discriminant = Foo::Baz as u32;
assert_eq!(baz_discriminant, 123);
[items.enum.discriminant.restrictions]
Restrictions
[items.enum.discriminant.restrictions.same-discriminant]
It is an error when two variants share the same discriminant.
enum SharedDiscriminantError {
    SharedA = 1,
    SharedB = 1
}

enum SharedDiscriminantError2 {
    Zero,       // 0
    One,        // 1
    OneToo = 1  // 1 (collision with previous!)
}
[items.enum.discriminant.restrictions.above-max-discriminant]
It is also an error to have an unspecified discriminant where the previous discriminant is the maximum value for the size of the discriminant.
#[repr(u8)]
enum OverflowingDiscriminantError {
    Max = 255,
    MaxPlusOne // Would be 256, but that overflows the enum.
}

#[repr(u8)]
enum OverflowingDiscriminantError2 {
    MaxMinusOne = 254, // 254
    Max,               // 255
    MaxPlusOne         // Would be 256, but that overflows the enum.
}
Accessing discriminant
Via mem::discriminant
[items.enum.discriminant.access-opaque]
std::mem::discriminant returns an opaque reference to the discriminant of an enum value which can be compared. This cannot be used to get the value of the discriminant.
[items.enum.discriminant.coercion]
Casting
[items.enum.discriminant.coercion.intro]
If an enumeration is unit-only (with no tuple and struct variants), then its discriminant can be directly accessed with a numeric cast; e.g.:
enum Enum {
    Foo,
    Bar,
    Baz,
}

assert_eq!(0, Enum::Foo as isize);
assert_eq!(1, Enum::Bar as isize);
assert_eq!(2, Enum::Baz as isize);
[items.enum.discriminant.coercion.fieldless]
Field-less enums can be casted if they do not have explicit discriminants, or where only unit variants are explicit.
enum Fieldless {
    Tuple(),
    Struct{},
    Unit,
}

assert_eq!(0, Fieldless::Tuple() as isize);
assert_eq!(1, Fieldless::Struct{} as isize);
assert_eq!(2, Fieldless::Unit as isize);

#[repr(u8)]
enum FieldlessWithDiscriminants {
    First = 10,
    Tuple(),
    Second = 20,
    Struct{},
    Unit,
}

assert_eq!(10, FieldlessWithDiscriminants::First as u8);
assert_eq!(11, FieldlessWithDiscriminants::Tuple() as u8);
assert_eq!(20, FieldlessWithDiscriminants::Second as u8);
assert_eq!(21, FieldlessWithDiscriminants::Struct{} as u8);
assert_eq!(22, FieldlessWithDiscriminants::Unit as u8);
Pointer casting
[items.enum.discriminant.access-memory]
If the enumeration specifies a primitive representation, then the discriminant may be reliably accessed via unsafe pointer casting:
#[repr(u8)]
enum Enum {
    Unit,
    Tuple(bool),
    Struct{a: bool},
}

impl Enum {
    fn discriminant(&self) -> u8 {
        unsafe { *(self as *const Self as *const u8) }
    }
}

let unit_like = Enum::Unit;
let tuple_like = Enum::Tuple(true);
let struct_like = Enum::Struct{a: false};

assert_eq!(0, unit_like.discriminant());
assert_eq!(1, tuple_like.discriminant());
assert_eq!(2, struct_like.discriminant());
[items.enum.empty]
Zero-variant enums
[items.enum.empty.intro]
Enums with zero variants are known as zero-variant enums. As they have no valid values, they cannot be instantiated.
enum ZeroVariants {}
[items.enum.empty.uninhabited]
Zero-variant enums are equivalent to the never type, but they cannot be coerced into other types.
let x: ZeroVariants = panic!();
let y: u32 = x; // mismatched type error
[items.enum.variant-visibility]
Variant visibility
Enum variants syntactically allow a Visibility annotation, but this is rejected when the enum is validated. This allows items to be parsed with a unified syntax across different contexts where they are used.
macro_rules! mac_variant {
    ($vis:vis $name:ident) => {
        enum $name {
            $vis Unit,

            $vis Tuple(u8, u16),

            $vis Struct { f: u8 },
        }
    }
}

// Empty `vis` is allowed.
mac_variant! { E }

// This is allowed, since it is removed before being validated.
#[cfg(false)]
enum E {
    pub U,
    pub(crate) T(u8),
    pub(super) T { f: String }
}
[items.union]
Unions

[items.union.syntax]
Syntax
Union →
    union IDENTIFIER GenericParams? WhereClause? { StructFields? }

Show syntax diagrams

[items.union.intro]
A union declaration uses the same syntax as a struct declaration, except with union in place of struct.
[items.union.namespace]
A union declaration defines the given name in the type namespace of the module or block where it is located.
#[repr(C)]
union MyUnion {
    f1: u32,
    f2: f32,
}
[items.union.common-storage]
The key property of unions is that all fields of a union share common storage. As a result, writes to one field of a union can overwrite its other fields, and size of a union is determined by the size of its largest field.
[items.union.field-restrictions]
Union field types are restricted to the following subset of types:
[items.union.field-copy]
Copy types
[items.union.field-references]
References (&T and &mut T for arbitrary T)
[items.union.field-manually-drop]
ManuallyDrop<T> (for arbitrary T)
[items.union.field-tuple]
Tuples and arrays containing only allowed union field types
[items.union.drop]
This restriction ensures, in particular, that union fields never need to be dropped. Like for structs and enums, it is possible to impl Drop for a union to manually define what happens when it gets dropped.
[items.union.fieldless]
Unions without any fields are not accepted by the compiler, but can be accepted by macros.
[items.union.init]
Initialization of a union
[items.union.init.intro]
A value of a union type can be created using the same syntax that is used for struct types, except that it must specify exactly one field:
let u = MyUnion { f1: 1 };
[items.union.init.result]
The expression above creates a value of type MyUnion and initializes the storage using field f1. The union can be accessed using the same syntax as struct fields:
let f = unsafe { u.f1 };
[items.union.fields]
Reading and writing union fields
[items.union.fields.intro]
Unions have no notion of an “active field”. Instead, every union access just interprets the storage as the type of the field used for the access.
[items.union.fields.read]
Reading a union field reads the bits of the union at the field’s type.
[items.union.fields.offset]
Fields might have a non-zero offset (except when the C representation is used); in that case the bits starting at the offset of the fields are read
[items.union.fields.validity]
It is the programmer’s responsibility to make sure that the data is valid at the field’s type. Failing to do so results in undefined behavior. For example, reading the value 3 from a field of the boolean type is undefined behavior. Effectively, writing to and then reading from a union with the C representation is analogous to a transmute from the type used for writing to the type used for reading.
[items.union.fields.read-safety]
Consequently, all reads of union fields have to be placed in unsafe blocks:
unsafe {
    let f = u.f1;
}
Commonly, code using unions will provide safe wrappers around unsafe union field accesses.
[items.union.fields.write-safety]
In contrast, writes to union fields are safe, since they just overwrite arbitrary data, but cannot cause undefined behavior. (Note that union field types can never have drop glue, so a union field write will never implicitly drop anything.)
[items.union.pattern]
Pattern matching on unions
[items.union.pattern.intro]
Another way to access union fields is to use pattern matching.
[items.union.pattern.one-field]
Pattern matching on union fields uses the same syntax as struct patterns, except that the pattern must specify exactly one field.
[items.union.pattern.safety]
Since pattern matching is like reading the union with a particular field, it has to be placed in unsafe blocks as well.
fn f(u: MyUnion) {
    unsafe {
        match u {
            MyUnion { f1: 10 } => { println!("ten"); }
            MyUnion { f2 } => { println!("{}", f2); }
        }
    }
}
[items.union.pattern.subpattern]
Pattern matching may match a union as a field of a larger structure. In particular, when using a Rust union to implement a C tagged union via FFI, this allows matching on the tag and the corresponding field simultaneously:
#[repr(u32)]
enum Tag { I, F }

#[repr(C)]
union U {
    i: i32,
    f: f32,
}

#[repr(C)]
struct Value {
    tag: Tag,
    u: U,
}

fn is_zero(v: Value) -> bool {
    unsafe {
        match v {
            Value { tag: Tag::I, u: U { i: 0 } } => true,
            Value { tag: Tag::F, u: U { f: num } } if num == 0.0 => true,
            _ => false,
        }
    }
}
[items.union.ref]
References to union fields
[items.union.ref.intro]
Since union fields share common storage, gaining write access to one field of a union can give write access to all its remaining fields.
[items.union.ref.borrow]
Borrow checking rules have to be adjusted to account for this fact. As a result, if one field of a union is borrowed, all its remaining fields are borrowed as well for the same lifetime.
// ERROR: cannot borrow `u` (via `u.f2`) as mutable more than once at a time
fn test() {
    let mut u = MyUnion { f1: 1 };
    unsafe {
        let b1 = &mut u.f1;
//                    ---- first mutable borrow occurs here (via `u.f1`)
        let b2 = &mut u.f2;
//                    ^^^^ second mutable borrow occurs here (via `u.f2`)
        *b1 = 5;
    }
//  - first borrow ends here
    assert_eq!(unsafe { u.f1 }, 5);
}
[items.union.ref.usage]
As you could see, in many aspects (except for layouts, safety, and ownership) unions behave exactly like structs, largely as a consequence of inheriting their syntactic shape from structs. This is also true for many unmentioned aspects of Rust language (such as privacy, name resolution, type inference, generics, trait implementations, inherent implementations, coherence, pattern checking, etc etc etc).
[items.const]
Constant items

[items.const.syntax]
Syntax
ConstantItem →
    const ( IDENTIFIER | _ ) : Type ( = Expression )? ;

Show syntax diagrams

[items.const.intro]
A constant item is an optionally named constant value which is not associated with a specific memory location in the program.
[items.const.behavior]
Constants are essentially inlined wherever they are used, meaning that they are copied directly into the relevant context when used. This includes usage of constants from external crates, and non-Copy types. References to the same constant are not necessarily guaranteed to refer to the same memory address.
[items.const.namespace]
The constant declaration defines the constant value in the value namespace of the module or block where it is located.
[items.const.static]
Constants must be explicitly typed. The type must have a 'static lifetime: any references in the initializer must have 'static lifetimes. References in the type of a constant default to 'static lifetime; see static lifetime elision.
[items.const.static-temporary]
A reference to a constant will have 'static lifetime if the constant value is eligible for promotion; otherwise, a temporary will be created.
const BIT1: u32 = 1 << 0;
const BIT2: u32 = 1 << 1;

const BITS: [u32; 2] = [BIT1, BIT2];
const STRING: &'static str = "bitstring";

struct BitsNStrings<'a> {
    mybits: [u32; 2],
    mystring: &'a str,
}

const BITS_N_STRINGS: BitsNStrings<'static> = BitsNStrings {
    mybits: BITS,
    mystring: STRING,
};
[items.const.no-mut-refs]
The final value of a const item cannot contain any mutable references.
static mut S: u8 = 0;
const C: &u8 = unsafe { &mut S }; // OK
static S: AtomicU8 = AtomicU8::new(0);
const C: &AtomicU8 = &S; // OK
static mut S: u8 = 0;
const C: &mut u8 = unsafe { &mut S }; // ERROR not allowed
Note

We also disallow, in the final value, shared references to mutable statics created in the initializer for a separate reason. Consider:

const C: &AtomicU8 = &AtomicU8::new(0); // ERROR
Here, the AtomicU8 is a temporary that is lifetime extended to 'static (see destructors.scope.lifetime-extension.static), and references to lifetime-extended temporaries with interior mutability are not allowed in the final value of a constant expression (see const-eval.const-expr.borrows).
[items.const.expr-omission]
The constant expression may only be omitted in a trait definition.
[items.const.destructor]
Constants with Destructors
Constants can contain destructors. Destructors are run when the value goes out of scope.
struct TypeWithDestructor(i32);

impl Drop for TypeWithDestructor {
    fn drop(&mut self) {
        println!("Dropped. Held {}.", self.0);
    }
}

const ZERO_WITH_DESTRUCTOR: TypeWithDestructor = TypeWithDestructor(0);

fn create_and_drop_zero_with_destructor() {
    let x = ZERO_WITH_DESTRUCTOR;
    // x gets dropped at end of function, calling drop.
    // prints "Dropped. Held 0.".
}
[items.const.unnamed]
Unnamed constant
[items.const.unnamed.intro]
Unlike an associated constant, a free constant may be unnamed by using an underscore instead of the name. For example:
const _: () =  { struct _SameNameTwice; };

// OK although it is the same name as above:
const _: () =  { struct _SameNameTwice; };
[items.const.unnamed.repetition]
As with underscore imports, macros may safely emit the same unnamed constant in the same scope more than once. For example, the following should not produce an error:
macro_rules! m {
    ($item: item) => { $item $item }
}

m!(const _: () = (););
// This expands to:
// const _: () = ();
// const _: () = ();
[items.const.eval]
Evaluation
Free constants are always evaluated at compile-time to surface panics. This happens even within an unused function:
// Compile-time panic
const PANIC: () = std::unimplemented!();

fn unused_generic_function<T>() {
    // A failing compile-time assertion
    const _: () = assert!(usize::BITS == 0);
}
[items.static]
Static items

[items.static.syntax]
Syntax
StaticItem →
    ItemSafety?​1 static mut? IDENTIFIER : Type ( = Expression )? ;

Show syntax diagrams

[items.static.intro]
A static item is similar to a constant, except that it represents an allocation in the program that is initialized with the initializer expression. All references and raw pointers to the static refer to the same allocation.
[items.static.lifetime]
Static items have the static lifetime, which outlives all other lifetimes in a Rust program. Static items do not call drop at the end of the program.
[items.static.storage-disjointness]
If the static has a size of at least 1 byte, this allocation is disjoint from all other such static allocations as well as heap allocations and stack-allocated variables. However, the storage of immutable static items can overlap with allocations that do not themselves have a unique address, such as promoteds and const items.
[items.static.namespace]
The static declaration defines a static value in the value namespace of the module or block where it is located.
[items.static.init]
The static initializer is a constant expression evaluated at compile time. Static initializers may refer to and read from other statics. When reading from mutable statics, they read the initial value of that static.
[items.static.read-only]
Non-mut static items that contain a type that is not interior mutable may be placed in read-only memory.
[items.static.safety]
All access to a static is safe, but there are a number of restrictions on statics:
[items.static.sync]
The type must have the Sync trait bound to allow thread-safe access.
[items.static.init.omission]
The initializer expression must be omitted in an external block, and must be provided for free static items.
[items.static.safety-qualifiers]
The safe and unsafe qualifiers are semantically only allowed when used in an external block.
[items.static.generics]
Statics & generics
A static item defined in a generic scope (for example in a blanket or default implementation) will result in exactly one static item being defined, as if the static definition was pulled out of the current scope into the module. There will not be one item per monomorphization.
This code:
use std::sync::atomic::{AtomicUsize, Ordering};

trait Tr {
    fn default_impl() {
        static COUNTER: AtomicUsize = AtomicUsize::new(0);
        println!("default_impl: counter was {}", COUNTER.fetch_add(1, Ordering::Relaxed));
    }

    fn blanket_impl();
}

struct Ty1 {}
struct Ty2 {}

impl<T> Tr for T {
    fn blanket_impl() {
        static COUNTER: AtomicUsize = AtomicUsize::new(0);
        println!("blanket_impl: counter was {}", COUNTER.fetch_add(1, Ordering::Relaxed));
    }
}

fn main() {
    <Ty1 as Tr>::default_impl();
    <Ty2 as Tr>::default_impl();
    <Ty1 as Tr>::blanket_impl();
    <Ty2 as Tr>::blanket_impl();
}
prints
default_impl: counter was 0
default_impl: counter was 1
blanket_impl: counter was 0
blanket_impl: counter was 1
[items.static.mut]
Mutable statics
[items.static.mut.intro]
If a static item is declared with the mut keyword, then it is allowed to be modified by the program. One of Rust’s goals is to make concurrency bugs hard to run into, and this is obviously a very large source of race conditions or other bugs.
[items.static.mut.safety]
For this reason, an unsafe block is required when either reading or writing a mutable static variable. Care should be taken to ensure that modifications to a mutable static are safe with respect to other threads running in the same process.
[items.static.mut.extern]
Mutable statics are still very useful, however. They can be used with C libraries and can also be bound from C libraries in an extern block.

static mut LEVELS: u32 = 0;

// This violates the idea of no shared state, and this doesn't internally
// protect against races, so this function is `unsafe`
unsafe fn bump_levels_unsafe() -> u32 {
    unsafe {
        let ret = LEVELS;
        LEVELS += 1;
        return ret;
    }
}

// As an alternative to `bump_levels_unsafe`, this function is safe, assuming
// that we have an atomic_add function which returns the old value. This
// function is safe only if no other code accesses the static in a non-atomic
// fashion. If such accesses are possible (such as in `bump_levels_unsafe`),
// then this would need to be `unsafe` to indicate to the caller that they
// must still guard against concurrent access.
fn bump_levels_safe() -> u32 {
    unsafe {
        return atomic_add(&raw mut LEVELS, 1);
    }
}
[items.static.mut.sync]
Mutable statics have the same restrictions as normal statics, except that the type does not have to implement the Sync trait.
[items.static.alternate]
Using Statics or Consts
It can be confusing whether or not you should use a constant item or a static item. Constants should, in general, be preferred over statics unless one of the following are true:
Large amounts of data are being stored.
The single-address property of statics is required.
Interior mutability is required.
The safe and unsafe function qualifiers are only allowed semantically within extern blocks. ↩

[items.traits]
Traits

[items.traits.syntax]
Syntax
Trait →
    unsafe? trait IDENTIFIER GenericParams? ( : TypeParamBounds? )? WhereClause?
    {
        InnerAttribute*
        AssociatedItem*
    }

Show syntax diagrams

[items.traits.intro]
A trait describes an abstract interface that types can implement. This interface consists of associated items, which come in three varieties:
functions
types
constants
[items.traits.namespace]
The trait declaration defines a trait in the type namespace of the module or block where it is located.
[items.traits.associated-item-namespaces]
Associated items are defined as members of the trait within their respective namespaces. Associated types are defined in the type namespace. Associated constants and associated functions are defined in the value namespace.
[items.traits.self-param]
All traits define an implicit type parameter Self that refers to “the type that is implementing this interface”. Traits may also contain additional type parameters. These type parameters, including Self, may be constrained by other traits and so forth as usual.
[items.traits.impls]
Traits are implemented for specific types through separate implementations.
[items.traits.associated-item-decls]
Trait functions may omit the function body by replacing it with a semicolon. This indicates that the implementation must define the function. If the trait function defines a body, this definition acts as a default for any implementation which does not override it. Similarly, associated constants may omit the equals sign and expression to indicate implementations must define the constant value. Associated types must never define the type, the type may only be specified in an implementation.
// Examples of associated trait items with and without definitions.
trait Example {
    const CONST_NO_DEFAULT: i32;
    const CONST_WITH_DEFAULT: i32 = 99;
    type TypeNoDefault;
    fn method_without_default(&self);
    fn method_with_default(&self) {}
}
[items.traits.const-fn]
Trait functions are not allowed to be const.
[items.traits.bounds]
Trait bounds
Generic items may use traits as bounds on their type parameters.
[items.traits.generic]
Generic traits
Type parameters can be specified for a trait to make it generic. These appear after the trait name, using the same syntax used in generic functions.
trait Seq<T> {
    fn len(&self) -> u32;
    fn elt_at(&self, n: u32) -> T;
    fn iter<F>(&self, f: F) where F: Fn(T);
}
[items.traits.dyn-compatible]
Dyn compatibility
[items.traits.dyn-compatible.intro]
A dyn-compatible trait can be the base trait of a trait object. A trait is dyn compatible if it has the following qualities:
[items.traits.dyn-compatible.supertraits]
All supertraits must also be dyn compatible.
[items.traits.dyn-compatible.sized]
Sized must not be a supertrait. In other words, it must not require Self: Sized.
[items.traits.dyn-compatible.associated-consts]
It must not have any associated constants.
[items.traits.dyn-compatible.associated-types]
It must not have any associated types with generics.
[items.traits.dyn-compatible.associated-functions]
All associated functions must either be dispatchable from a trait object or be explicitly non-dispatchable:
Dispatchable functions must:
Not have any type parameters (although lifetime parameters are allowed).
Be a method that does not use Self except in the type of the receiver.
Have a receiver with one of the following types:
&Self (i.e. &self)
&mut Self (i.e &mut self)
Box<Self>
Rc<Self>
Arc<Self>
Pin<P> where P is one of the types above
Not have an opaque return type; that is,
Not be an async fn (which has a hidden Future type).
Not have a return position impl Trait type (fn example(&self) -> impl Trait).
Not have a where Self: Sized bound (receiver type of Self (i.e. self) implies this).
Explicitly non-dispatchable functions require:
Have a where Self: Sized bound (receiver type of Self (i.e. self) implies this).
[items.traits.dyn-compatible.async-traits]
The AsyncFn, AsyncFnMut, and AsyncFnOnce traits are not dyn-compatible.
Note

This concept was formerly known as object safety.
// Examples of dyn compatible methods.
trait TraitMethods {
    fn by_ref(self: &Self) {}
    fn by_ref_mut(self: &mut Self) {}
    fn by_box(self: Box<Self>) {}
    fn by_rc(self: Rc<Self>) {}
    fn by_arc(self: Arc<Self>) {}
    fn by_pin(self: Pin<&Self>) {}
    fn with_lifetime<'a>(self: &'a Self) {}
    fn nested_pin(self: Pin<Arc<Self>>) {}
}
// This trait is dyn compatible, but these methods cannot be dispatched on a trait object.
trait NonDispatchable {
    // Non-methods cannot be dispatched.
    fn foo() where Self: Sized {}
    // Self type isn't known until runtime.
    fn returns(&self) -> Self where Self: Sized;
    // `other` may be a different concrete type of the receiver.
    fn param(&self, other: Self) where Self: Sized {}
    // Generics are not compatible with vtables.
    fn typed<T>(&self, x: T) where Self: Sized {}
}

struct S;
impl NonDispatchable for S {
    fn returns(&self) -> Self where Self: Sized { S }
}
let obj: Box<dyn NonDispatchable> = Box::new(S);
obj.returns(); // ERROR: cannot call with Self return
obj.param(S);  // ERROR: cannot call with Self parameter
obj.typed(1);  // ERROR: cannot call with generic type
// Examples of dyn-incompatible traits.
trait DynIncompatible {
    const CONST: i32 = 1;  // ERROR: cannot have associated const

    fn foo() {}  // ERROR: associated function without Sized
    fn returns(&self) -> Self; // ERROR: Self in return type
    fn typed<T>(&self, x: T) {} // ERROR: has generic type parameters
    fn nested(self: Rc<Box<Self>>) {} // ERROR: nested receiver cannot be downcasted
}

struct S;
impl DynIncompatible for S {
    fn returns(&self) -> Self { S }
}
let obj: Box<dyn DynIncompatible> = Box::new(S); // ERROR
// `Self: Sized` traits are dyn-incompatible.
trait TraitWithSize where Self: Sized {}

struct S;
impl TraitWithSize for S {}
let obj: Box<dyn TraitWithSize> = Box::new(S); // ERROR
// Dyn-incompatible if `Self` is a type argument.
trait Super<A> {}
trait WithSelf: Super<Self> where Self: Sized {}

struct S;
impl<A> Super<A> for S {}
impl WithSelf for S {}
let obj: Box<dyn WithSelf> = Box::new(S); // ERROR: cannot use `Self` type parameter
[items.traits.supertraits]
Supertraits
[items.traits.supertraits.intro]
Supertraits are traits that are required to be implemented for a type to implement a specific trait. Furthermore, anywhere a generic or trait object is bounded by a trait, it has access to the associated items of its supertraits.
[items.traits.supertraits.decl]
Supertraits are declared by trait bounds on the Self type of a trait and transitively the supertraits of the traits declared in those trait bounds. It is an error for a trait to be its own supertrait.
[items.traits.supertraits.subtrait]
The trait with a supertrait is called a subtrait of its supertrait.
The following is an example of declaring Shape to be a supertrait of Circle.
trait Shape { fn area(&self) -> f64; }
trait Circle: Shape { fn radius(&self) -> f64; }
And the following is the same example, except using where clauses.
trait Shape { fn area(&self) -> f64; }
trait Circle where Self: Shape { fn radius(&self) -> f64; }
This next example gives radius a default implementation using the area function from Shape.
trait Circle where Self: Shape {
    fn radius(&self) -> f64 {
        // A = pi * r^2
        // so algebraically,
        // r = sqrt(A / pi)
        (self.area() / std::f64::consts::PI).sqrt()
    }
}
This next example calls a supertrait method on a generic parameter.
fn print_area_and_radius<C: Circle>(c: C) {
    // Here we call the area method from the supertrait `Shape` of `Circle`.
    println!("Area: {}", c.area());
    println!("Radius: {}", c.radius());
}
Similarly, here is an example of calling supertrait methods on trait objects.
let circle = Box::new(circle) as Box<dyn Circle>;
let nonsense = circle.radius() * circle.area();
[items.traits.safety]
Unsafe traits
[items.traits.safety.intro]
Traits items that begin with the unsafe keyword indicate that implementing the trait may be unsafe. It is safe to use a correctly implemented unsafe trait. The trait implementation must also begin with the unsafe keyword.
Sync and Send are examples of unsafe traits.
[items.traits.params]
Parameter patterns
[items.traits.params.patterns-no-body]
Parameters in associated functions without a body only allow IDENTIFIER or _ wild card patterns, as well as the form allowed by SelfParam. mut IDENTIFIER is currently allowed, but it is deprecated and will become a hard error in the future.
trait T {
    fn f1(&self);
    fn f2(x: Self, _: i32);
}
trait T {
    fn f2(&x: &i32); // ERROR: patterns aren't allowed in functions without bodies
}
[items.traits.params.patterns-with-body]
Parameters in associated functions with a body only allow irrefutable patterns.
trait T {
    fn f1((a, b): (i32, i32)) {} // OK: is irrefutable
}
trait T {
    fn f1(123: i32) {} // ERROR: pattern is refutable
    fn f2(Some(x): Option<i32>) {} // ERROR: pattern is refutable
}
[items.traits.params.pattern-required.edition2018]
2018
Edition differences

Prior to the 2018 edition, the pattern for an associated function parameter is optional:

// 2015 Edition
trait T {
    fn f(i32); // OK: parameter identifiers are not required
}
Beginning in the 2018 edition, patterns are no longer optional.
[items.traits.params.restriction-patterns.edition2018]
2018
Edition differences

Prior to the 2018 edition, parameters in associated functions with a body are limited to the following kinds of patterns:

IDENTIFIER
mut IDENTIFIER
_
& IDENTIFIER
&& IDENTIFIER
// 2015 Edition
trait T {
    fn f1((a, b): (i32, i32)) {} // ERROR: pattern not allowed
}
Beginning in 2018, all irrefutable patterns are allowed as described in items.traits.params.patterns-with-body.
[items.traits.associated-visibility]
Item visibility
[items.traits.associated-visibility.intro]
Trait items syntactically allow a Visibility annotation, but this is rejected when the trait is validated. This allows items to be parsed with a unified syntax across different contexts where they are used. As an example, an empty vis macro fragment specifier can be used for trait items, where the macro rule may be used in other situations where visibility is allowed.
macro_rules! create_method {
    ($vis:vis $name:ident) => {
        $vis fn $name(&self) {}
    };
}

trait T1 {
    // Empty `vis` is allowed.
    create_method! { method_of_t1 }
}

struct S;

impl S {
    // Visibility is allowed here.
    create_method! { pub method_of_s }
}

impl T1 for S {}

fn main() {
    let s = S;
    s.method_of_t1();
    s.method_of_s();
}
[items.impl]
Implementations

[items.impl.syntax]
Syntax
Implementation → InherentImpl | TraitImpl

InherentImpl →
    impl GenericParams? Type WhereClause? {
        InnerAttribute*
        AssociatedItem*
    }

TraitImpl →
    unsafe? impl GenericParams? !? TypePath for Type
    WhereClause?
    {
        InnerAttribute*
        AssociatedItem*
    }

Show syntax diagrams

[items.impl.intro]
An implementation is an item that associates items with an implementing type. Implementations are defined with the keyword impl and contain functions that belong to an instance of the type that is being implemented or to the type statically.
[items.impl.kinds]
There are two types of implementations:
inherent implementations
trait implementations
[items.impl.inherent]
Inherent Implementations
[items.impl.inherent.intro]
An inherent implementation is defined as the sequence of the impl keyword, generic type declarations, a path to a nominal type, a where clause, and a bracketed set of associable items.
[items.impl.inherent.implementing-type]
The nominal type is called the implementing type and the associable items are the associated items to the implementing type.
[items.impl.inherent.associated-items]
Inherent implementations associate the contained items to the implementing type.
[items.impl.inherent.associated-items.allowed-items]
Inherent implementations can contain associated functions (including methods) and associated constants.
[items.impl.inherent.type-alias]
They cannot contain associated type aliases.
[items.impl.inherent.associated-item-path]
The path to an associated item is any path to the implementing type, followed by the associated item’s identifier as the final path component.
[items.impl.inherent.coherence]
A type can also have multiple inherent implementations. An implementing type must be defined within the same crate as the original type definition.
pub mod color {
    pub struct Color(pub u8, pub u8, pub u8);

    impl Color {
        pub const WHITE: Color = Color(255, 255, 255);
    }
}

mod values {
    use super::color::Color;
    impl Color {
        pub fn red() -> Color {
            Color(255, 0, 0)
        }
    }
}

pub use self::color::Color;
fn main() {
    // Actual path to the implementing type and impl in the same module.
    color::Color::WHITE;

    // Impl blocks in different modules are still accessed through a path to the type.
    color::Color::red();

    // Re-exported paths to the implementing type also work.
    Color::red();

    // Does not work, because use in `values` is not pub.
    // values::Color::red();
}
[items.impl.trait]
Trait Implementations
[items.impl.trait.intro]
A trait implementation is defined like an inherent implementation except that the optional generic type declarations are followed by a trait, followed by the keyword for, followed by a path to a nominal type.
[items.impl.trait.implemented-trait]
The trait is known as the implemented trait. The implementing type implements the implemented trait.
[items.impl.trait.def-requirement]
A trait implementation must define all non-default associated items declared by the implemented trait, may redefine default associated items defined by the implemented trait, and cannot define any other items.
[items.impl.trait.associated-item-path]
The path to the associated items is < followed by a path to the implementing type followed by as followed by a path to the trait followed by > as a path component followed by the associated item’s path component.
[items.impl.trait.safety]
Unsafe traits require the trait implementation to begin with the unsafe keyword.
struct Circle {
    radius: f64,
    center: Point,
}

impl Copy for Circle {}

impl Clone for Circle {
    fn clone(&self) -> Circle { *self }
}

impl Shape for Circle {
    fn draw(&self, s: Surface) { do_draw_circle(s, *self); }
    fn bounding_box(&self) -> BoundingBox {
        let r = self.radius;
        BoundingBox {
            x: self.center.x - r,
            y: self.center.y - r,
            width: 2.0 * r,
            height: 2.0 * r,
        }
    }
}
[items.impl.trait.coherence]
Trait Implementation Coherence
[items.impl.trait.coherence.intro]
A trait implementation is considered incoherent if either the orphan rules check fails or there are overlapping implementation instances.
[items.impl.trait.coherence.overlapping]
Two trait implementations overlap when there is a non-empty intersection of the traits the implementation is for, the implementations can be instantiated with the same type.
[items.impl.trait.orphan-rule]
Orphan rules
[items.impl.trait.orphan-rule.intro]
The orphan rule states that a trait implementation is only allowed if either the trait or at least one of the types in the implementation is defined in the current crate. It prevents conflicting trait implementations across different crates and is key to ensuring coherence.
An orphan implementation is one that implements a foreign trait for a foreign type. If these were freely allowed, two crates could implement the same trait for the same type in incompatible ways, creating a situation where adding or updating a dependency could break compilation due to conflicting implementations.
The orphan rule enables library authors to add new implementations to their traits without fear that they’ll break downstream code. Without these restrictions, a library couldn’t add an implementation like impl<T: Display> MyTrait for T without potentially conflicting with downstream implementations.
[items.impl.trait.orphan-rule.general]
Given impl<P1..=Pn> Trait<T1..=Tn> for T0, an impl is valid only if at least one of the following is true:
Trait is a local trait
All of
At least one of the types T0..=Tn must be a local type. Let Ti be the first such type.
No uncovered type parameters P1..=Pn may appear in T0..Ti (excluding Ti)
[items.impl.trait.uncovered-param]
Only the appearance of uncovered type parameters is restricted.
[items.impl.trait.fundamental]
Note that for the purposes of coherence, fundamental types are special. The T in Box<T> is not considered covered, and Box<LocalType> is considered local.
[items.impl.generics]
Generic Implementations
[items.impl.generics.intro]
An implementation can take generic parameters, which can be used in the rest of the implementation. Implementation parameters are written directly after the impl keyword.
impl<T> Seq<T> for Vec<T> {
    /* ... */
}
impl Seq<bool> for u32 {
    /* Treat the integer as a sequence of bits */
}
[items.impl.generics.usage]
Generic parameters constrain an implementation if the parameter appears at least once in one of:
The implemented trait, if it has one
The implementing type
As an associated type in the bounds of a type that contains another parameter that constrains the implementation
[items.impl.generics.constrain]
Type and const parameters must always constrain the implementation. Lifetimes must constrain the implementation if the lifetime is used in an associated type.
Examples of constraining situations:
// T constrains by being an argument to GenericTrait.
impl<T> GenericTrait<T> for i32 { /* ... */ }

// T constrains by being an argument to GenericStruct
impl<T> Trait for GenericStruct<T> { /* ... */ }

// Likewise, N constrains by being an argument to ConstGenericStruct
impl<const N: usize> Trait for ConstGenericStruct<N> { /* ... */ }

// T constrains by being in an associated type in a bound for type `U` which is
// itself a generic parameter constraining the trait.
impl<T, U> GenericTrait<U> for u32 where U: HasAssocType<Ty = T> { /* ... */ }

// Like previous, except the type is `(U, isize)`. `U` appears inside the type
// that includes `T`, and is not the type itself.
impl<T, U> GenericStruct<U> where (U, isize): HasAssocType<Ty = T> { /* ... */ }
Examples of non-constraining situations:
// The rest of these are errors, since they have type or const parameters that
// do not constrain.

// T does not constrain since it does not appear at all.
impl<T> Struct { /* ... */ }

// N does not constrain for the same reason.
impl<const N: usize> Struct { /* ... */ }

// Usage of T inside the implementation does not constrain the impl.
impl<T> Struct {
    fn uses_t(t: &T) { /* ... */ }
}

// T is used as an associated type in the bounds for U, but U does not constrain.
impl<T, U> Struct where U: HasAssocType<Ty = T> { /* ... */ }

// T is used in the bounds, but not as an associated type, so it does not constrain.
impl<T, U> GenericTrait<U> for u32 where U: GenericTrait<T> {}
Example of an allowed unconstraining lifetime parameter:
impl<'a> Struct {}
Example of a disallowed unconstraining lifetime parameter:
impl<'a> HasAssocType for Struct {
    type Ty = &'a Struct;
}
[items.impl.attributes]
Attributes on Implementations
Implementations may contain outer attributes before the impl keyword and inner attributes inside the brackets that contain the associated items. Inner attributes must come before any associated items. The attributes that have meaning here are cfg, deprecated, doc, and the lint check attributes.
[items.extern]
External blocks

[items.extern.syntax]
Syntax
ExternBlock →
    unsafe?​1 extern Abi? {
        InnerAttribute*
        ExternalItem*
    }

ExternalItem →
    OuterAttribute* (
        MacroInvocationSemi
      | Visibility? StaticItem
      | Visibility? Function
    )

Show syntax diagrams

[items.extern.intro]
External blocks provide declarations of items that are not defined in the current crate and are the basis of Rust’s foreign function interface. These are akin to unchecked imports.
[items.extern.allowed-kinds]
Two kinds of item declarations are allowed in external blocks: functions and statics.
[items.extern.safety]
Calling unsafe functions or accessing unsafe statics that are declared in external blocks is only allowed in an unsafe context.
[items.extern.namespace]
The external block defines its functions and statics in the value namespace of the module or block where it is located.
[items.extern.unsafe-required]
The unsafe keyword is semantically required to appear before the extern keyword on external blocks.
[items.extern.edition2024]
2024
Edition differences

Prior to the 2024 edition, the unsafe keyword is optional. The safe and unsafe item qualifiers are only allowed if the external block itself is marked as unsafe.
[items.extern.fn]
Functions
[items.extern.fn.body]
Functions within external blocks are declared in the same way as other Rust functions, with the exception that they must not have a body and are instead terminated by a semicolon.
[items.extern.fn.param-patterns]
Patterns are not allowed in parameters, only IDENTIFIER or _ may be used.
[items.extern.fn.qualifiers]
The safe and unsafe function qualifiers are allowed, but other function qualifiers (e.g. const, async, extern) are not.
[items.extern.fn.foreign-abi]
Functions within external blocks may be called by Rust code, just like functions defined in Rust. The Rust compiler automatically translates between the Rust ABI and the foreign ABI.
[items.extern.fn.safety]
A function declared in an extern block is implicitly unsafe unless the safe function qualifier is present.
[items.extern.fn.fn-ptr]
When coerced to a function pointer, a function declared in an extern block has type extern "abi" for<'l1, ..., 'lm> fn(A1, ..., An) -> R, where 'l1, … 'lm are its lifetime parameters, A1, …, An are the declared types of its parameters, R is the declared return type.
[items.extern.static]
Statics
[items.extern.static.intro]
Statics within external blocks are declared in the same way as statics outside of external blocks, except that they do not have an expression initializing their value.
[items.extern.static.safety]
Unless a static item declared in an extern block is qualified as safe, it is unsafe to access that item, whether or not it’s mutable, because there is nothing guaranteeing that the bit pattern at the static’s memory is valid for the type it is declared with, since some arbitrary (e.g. C) code is in charge of initializing the static.
[items.extern.static.mut]
Extern statics can be either immutable or mutable just like statics outside of external blocks.
[items.extern.static.read-only]
An immutable static must be initialized before any Rust code is executed. It is not enough for the static to be initialized before Rust code reads from it. Once Rust code runs, mutating an immutable static (from inside or outside Rust) is UB, except if the mutation happens to bytes inside of an UnsafeCell.
[items.extern.abi]
ABI
[items.extern.abi.intro]
By default external blocks assume that the library they are calling uses the standard C ABI on the specific platform. Other ABIs may be specified using an abi string, as shown here:
// Interface to the Windows API
unsafe extern "system" { }
[items.extern.abi.standard]
The following ABI strings are supported on all platforms:
[items.extern.abi.rust]
unsafe extern "Rust" – The default ABI when you write a normal fn foo() in any Rust code.
[items.extern.abi.c]
unsafe extern "C" – This is the same as extern fn foo(); whatever the default your C compiler supports.
[items.extern.abi.system]
unsafe extern "system" – Usually the same as extern "C", except on Win32, in which case it’s "stdcall", or what you should use to link to the Windows API itself
[items.extern.abi.unwind]
extern "C-unwind" and extern "system-unwind" – identical to "C" and "system", respectively, but with different behavior when the callee unwinds (by panicking or throwing a C++ style exception).
[items.extern.abi.platform]
There are also some platform-specific ABI strings:
[items.extern.abi.cdecl]
unsafe extern "cdecl" – The default for x86_32 C code.
[items.extern.abi.stdcall]
unsafe extern "stdcall" – The default for the Win32 API on x86_32.
[items.extern.abi.win64]
unsafe extern "win64" – The default for C code on x86_64 Windows.
[items.extern.abi.sysv64]
unsafe extern "sysv64" – The default for C code on non-Windows x86_64.
[items.extern.abi.aapcs]
unsafe extern "aapcs" – The default for ARM.
[items.extern.abi.fastcall]
unsafe extern "fastcall" – The fastcall ABI – corresponds to MSVC’s __fastcall and GCC and clang’s __attribute__((fastcall))
[items.extern.abi.thiscall]
unsafe extern "thiscall" – The default for C++ member functions on x86_32 MSVC – corresponds to MSVC’s __thiscall and GCC and clang’s __attribute__((thiscall))
[items.extern.abi.efiapi]
unsafe extern "efiapi" – The ABI used for UEFI functions.
[items.extern.abi.platform-unwind-variants]
Like "C" and "system", most platform-specific ABI strings also have a corresponding -unwind variant; specifically, these are:
"aapcs-unwind"
"cdecl-unwind"
"fastcall-unwind"
"stdcall-unwind"
"sysv64-unwind"
"thiscall-unwind"
"win64-unwind"
[items.extern.variadic]
Variadic functions
Functions within external blocks may be variadic by specifying ... as the last argument. The variadic parameter may optionally be specified with an identifier.
unsafe extern "C" {
    unsafe fn foo(...);
    unsafe fn bar(x: i32, ...);
    unsafe fn with_name(format: *const u8, args: ...);
    // SAFETY: This function guarantees it will not access
    // variadic arguments.
    safe fn ignores_variadic_arguments(x: i32, ...);
}
Warning

The safe qualifier should not be used on a function in an extern block unless that function guarantees that it will not access the variadic arguments at all. Passing an unexpected number of arguments or arguments of unexpected type to a variadic function may lead to undefined behavior.
[items.extern.attributes]
Attributes on extern blocks
[items.extern.attributes.intro]
The following attributes control the behavior of external blocks.
[items.extern.attributes.link]
The link attribute
[items.extern.attributes.link.intro]
The link attribute specifies the name of a native library that the compiler should link with for the items within an extern block.
[items.extern.attributes.link.syntax]
It uses the MetaListNameValueStr syntax to specify its inputs. The name key is the name of the native library to link. The kind key is an optional value which specifies the kind of library with the following possible values:
[items.extern.attributes.link.dylib]
dylib — Indicates a dynamic library. This is the default if kind is not specified.
[items.extern.attributes.link.static]
static — Indicates a static library.
[items.extern.attributes.link.framework]
framework — Indicates a macOS framework. This is only valid for macOS targets.
[items.extern.attributes.link.raw-dylib]
raw-dylib — Indicates a dynamic library where the compiler will generate an import library to link against (see dylib versus raw-dylib below for details). This is only valid for Windows targets.
[items.extern.attributes.link.name-requirement]
The name key must be included if kind is specified.
[items.extern.attributes.link.modifiers]
The optional modifiers argument is a way to specify linking modifiers for the library to link.
[items.extern.attributes.link.modifiers.syntax]
Modifiers are specified as a comma-delimited string with each modifier prefixed with either a + or - to indicate that the modifier is enabled or disabled, respectively.
[items.extern.attributes.link.modifiers.multiple]
Specifying multiple modifiers arguments in a single link attribute, or multiple identical modifiers in the same modifiers argument is not currently supported.
Example: #[link(name = "mylib", kind = "static", modifiers = "+whole-archive")].
[items.extern.attributes.link.wasm_import_module]
The wasm_import_module key may be used to specify the WebAssembly module name for the items within an extern block when importing symbols from the host environment. The default module name is env if wasm_import_module is not specified.
#[link(name = "crypto")]
unsafe extern {
    // …
}

#[link(name = "CoreFoundation", kind = "framework")]
unsafe extern {
    // …
}

#[link(wasm_import_module = "foo")]
unsafe extern {
    // …
}
[items.extern.attributes.link.empty-block]
It is valid to add the link attribute on an empty extern block. You can use this to satisfy the linking requirements of extern blocks elsewhere in your code (including upstream crates) instead of adding the attribute to each extern block.
[items.extern.attributes.link.modifiers.bundle]
Linking modifiers: bundle
[items.extern.attributes.link.modifiers.bundle.allowed-kinds]
This modifier is only compatible with the static linking kind. Using any other kind will result in a compiler error.
[items.extern.attributes.link.modifiers.bundle.behavior]
When building a rlib or staticlib +bundle means that the native static library will be packed into the rlib or staticlib archive, and then retrieved from there during linking of the final binary.
[items.extern.attributes.link.modifiers.bundle.behavior-negative]
When building a rlib -bundle means that the native static library is registered as a dependency of that rlib “by name”, and object files from it are included only during linking of the final binary, the file search by that name is also performed during final linking.
When building a staticlib -bundle means that the native static library is simply not included into the archive and some higher level build system will need to add it later during linking of the final binary.
[items.extern.attributes.link.modifiers.bundle.no-effect]
This modifier has no effect when building other targets like executables or dynamic libraries.
[items.extern.attributes.link.modifiers.bundle.default]
The default for this modifier is +bundle.
More implementation details about this modifier can be found in bundle documentation for rustc.
[items.extern.attributes.link.modifiers.whole-archive]
Linking modifiers: whole-archive
[items.extern.attributes.link.modifiers.whole-archive.allowed-kinds]
This modifier is only compatible with the static linking kind. Using any other kind will result in a compiler error.
[items.extern.attributes.link.modifiers.whole-archive.behavior]
+whole-archive means that the static library is linked as a whole archive without throwing any object files away.
[items.extern.attributes.link.modifiers.whole-archive.default]
The default for this modifier is -whole-archive.
More implementation details about this modifier can be found in whole-archive documentation for rustc.
[items.extern.attributes.link.modifiers.verbatim]
Linking modifiers: verbatim
[items.extern.attributes.link.modifiers.verbatim.allowed-kinds]
This modifier is compatible with all linking kinds.
[items.extern.attributes.link.modifiers.verbatim.behavior]
+verbatim means that rustc itself won’t add any target-specified library prefixes or suffixes (like lib or .a) to the library name, and will try its best to ask for the same thing from the linker.
[items.extern.attributes.link.modifiers.verbatim.behavior-negative]
-verbatim means that rustc will either add a target-specific prefix and suffix to the library name before passing it to linker, or won’t prevent linker from implicitly adding it.
[items.extern.attributes.link.modifiers.verbatim.default]
The default for this modifier is -verbatim.
More implementation details about this modifier can be found in verbatim documentation for rustc.
[items.extern.attributes.link.kind-raw-dylib]
dylib versus raw-dylib
[items.extern.attributes.link.kind-raw-dylib.intro]
On Windows, linking against a dynamic library requires that an import library is provided to the linker: this is a special static library that declares all of the symbols exported by the dynamic library in such a way that the linker knows that they have to be dynamically loaded at runtime.
[items.extern.attributes.link.kind-raw-dylib.import]
Specifying kind = "dylib" instructs the Rust compiler to link an import library based on the name key. The linker will then use its normal library resolution logic to find that import library. Alternatively, specifying kind = "raw-dylib" instructs the compiler to generate an import library during compilation and provide that to the linker instead.
[items.extern.attributes.link.kind-raw-dylib.platform-specific]
raw-dylib is only supported on Windows. Using it when targeting other platforms will result in a compiler error.
[items.extern.attributes.link.import_name_type]
The import_name_type key
[items.extern.attributes.link.import_name_type.intro]
On x86 Windows, names of functions are “decorated” (i.e., have a specific prefix and/or suffix added) to indicate their calling convention. For example, a stdcall calling convention function with the name fn1 that has no arguments would be decorated as _fn1@0. However, the PE Format does also permit names to have no prefix or be undecorated. Additionally, the MSVC and GNU toolchains use different decorations for the same calling conventions which means, by default, some Win32 functions cannot be called using the raw-dylib link kind via the GNU toolchain.
[items.extern.attributes.link.import_name_type.values]
To allow for these differences, when using the raw-dylib link kind you may also specify the import_name_type key with one of the following values to change how functions are named in the generated import library:
decorated: The function name will be fully-decorated using the MSVC toolchain format.
noprefix: The function name will be decorated using the MSVC toolchain format, but skipping the leading ?, @, or optionally _.
undecorated: The function name will not be decorated.
[items.extern.attributes.link.import_name_type.default]
If the import_name_type key is not specified, then the function name will be fully-decorated using the target toolchain’s format.
[items.extern.attributes.link.import_name_type.variables]
Variables are never decorated and so the import_name_type key has no effect on how they are named in the generated import library.
[items.extern.attributes.link.import_name_type.platform-specific]
The import_name_type key is only supported on x86 Windows. Using it when targeting other platforms will result in a compiler error.
[items.extern.attributes.link_name]
The link_name attribute
[items.extern.attributes.link_name.intro]
The link_name attribute may be applied to declarations inside an extern block to specify the symbol to import for the given function or static.
Example

unsafe extern "C" {
    #[link_name = "actual_symbol_name"]
    safe fn name_in_rust();
}
[items.extern.attributes.link_name.syntax]
The link_name attribute uses the MetaNameValueStr syntax.
[items.extern.attributes.link_name.allowed-positions]
The link_name attribute may only be applied to a function or static item in an extern block.
Note

rustc ignores use in other positions but lints against it. This may become an error in the future.
[items.extern.attributes.link_name.duplicates]
Only the last use of link_name on an item has effect.
Note

rustc lints against any use preceding the last. This may become an error in the future.
[items.extern.attributes.link_name.link_ordinal]
The link_name attribute may not be used with the link_ordinal attribute.
[items.extern.attributes.link_ordinal]
The link_ordinal attribute
[items.extern.attributes.link_ordinal.intro]
The link_ordinal attribute can be applied on declarations inside an extern block to indicate the numeric ordinal to use when generating the import library to link against. An ordinal is a unique number per symbol exported by a dynamic library on Windows and can be used when the library is being loaded to find that symbol rather than having to look it up by name.
Warning

link_ordinal should only be used in cases where the ordinal of the symbol is known to be stable: if the ordinal of a symbol is not explicitly set when its containing binary is built then one will be automatically assigned to it, and that assigned ordinal may change between builds of the binary.
#[link(name = "exporter", kind = "raw-dylib")]
unsafe extern "stdcall" {
    #[link_ordinal(15)]
    safe fn imported_function_stdcall(i: i32);
}
[items.extern.attributes.link_ordinal.allowed-kinds]
This attribute is only used with the raw-dylib linking kind. Using any other kind will result in a compiler error.
[items.extern.attributes.link_ordinal.exclusive]
Using this attribute with the link_name attribute will result in a compiler error.
[items.extern.attributes.fn-parameters]
Attributes on function parameters
Attributes on extern function parameters follow the same rules and restrictions as regular function parameters.
Starting with the 2024 Edition, the unsafe keyword is required semantically. ↩

[items.generics]
Generic parameters

[items.generics.syntax]
Syntax
GenericParams → < ( GenericParam ( , GenericParam )* ,? )? >

GenericParam → OuterAttribute* ( LifetimeParam | TypeParam | ConstParam )

LifetimeParam → Lifetime ( : LifetimeBounds )?

TypeParam → IDENTIFIER ( : TypeParamBounds? )? ( = Type )?

ConstParam →
    const IDENTIFIER : Type
    ( = BlockExpression | IDENTIFIER | -? LiteralExpression )?

Show syntax diagrams

[items.generics.syntax.intro]
Functions, type aliases, structs, enumerations, unions, traits, and implementations may be parameterized by types, constants, and lifetimes. These parameters are listed in angle brackets (<...>), usually immediately after the name of the item and before its definition. For implementations, which don’t have a name, they come directly after impl.
[items.generics.syntax.decl-order]
The order of generic parameters is restricted to lifetime parameters and then type and const parameters intermixed.
[items.generics.syntax.duplicate-params]
The same parameter name may not be declared more than once in a GenericParams list.
Some examples of items with type, const, and lifetime parameters:
fn foo<'a, T>() {}
trait A<U> {}
struct Ref<'a, T> where T: 'a { r: &'a T }
struct InnerArray<T, const N: usize>([T; N]);
struct EitherOrderWorks<const N: bool, U>(U);
[items.generics.syntax.scope]
Generic parameters are in scope within the item definition where they are declared. They are not in scope for items declared within the body of a function as described in item declarations. See generic parameter scopes for more details.
[items.generics.builtin-generic-types]
References, raw pointers, arrays, slices, tuples, and function pointers have lifetime or type parameters as well, but are not referred to with path syntax.
[items.generics.invalid-lifetimes]
'_ and 'static are not valid lifetime parameter names.
[items.generics.const]
Const generics
[items.generics.const.intro]
Const generic parameters allow items to be generic over constant values.
[items.generics.const.namespace]
The const identifier introduces a name in the value namespace for the constant parameter, and all instances of the item must be instantiated with a value of the given type.
[items.generics.const.allowed-types]
The only allowed types of const parameters are u8, u16, u32, u64, u128, usize, i8, i16, i32, i64, i128, isize, char and bool.
[items.generics.const.usage]
Const parameters can be used anywhere a const item can be used, with the exception that when used in a type or array repeat expression, it must be standalone (as described below). That is, they are allowed in the following places:
As an applied const to any type which forms a part of the signature of the item in question.
As part of a const expression used to define an associated const, or as a parameter to an associated type.
As a value in any runtime expression in the body of any functions in the item.
As a parameter to any type used in the body of any functions in the item.
As a part of the type of any fields in the item.
// Examples where const generic parameters can be used.

// Used in the signature of the item itself.
fn foo<const N: usize>(arr: [i32; N]) {
    // Used as a type within a function body.
    let x: [i32; N];
    // Used as an expression.
    println!("{}", N * 2);
}

// Used as a field of a struct.
struct Foo<const N: usize>([i32; N]);

impl<const N: usize> Foo<N> {
    // Used as an associated constant.
    const CONST: usize = N * 4;
}

trait Trait {
    type Output;
}

impl<const N: usize> Trait for Foo<N> {
    // Used as an associated type.
    type Output = [i32; N];
}
// Examples where const generic parameters cannot be used.
fn foo<const N: usize>() {
    // Cannot use in item definitions within a function body.
    const BAD_CONST: [usize; N] = [1; N];
    static BAD_STATIC: [usize; N] = [1; N];
    fn inner(bad_arg: [usize; N]) {
        let bad_value = N * 2;
    }
    type BadAlias = [usize; N];
    struct BadStruct([usize; N]);
}
[items.generics.const.standalone]
As a further restriction, const parameters may only appear as a standalone argument inside of a type or array repeat expression. In those contexts, they may only be used as a single segment path expression, possibly inside a block (such as N or {N}). That is, they cannot be combined with other expressions.
// Examples where const parameters may not be used.

// Not allowed to combine in other expressions in types, such as the
// arithmetic expression in the return type here.
fn bad_function<const N: usize>() -> [u8; {N + 1}] {
    // Similarly not allowed for array repeat expressions.
    [1; {N + 1}]
}
[items.generics.const.argument]
A const argument in a path specifies the const value to use for that item.
[items.generics.const.argument.const-expr]
The argument must either be an inferred const or be a const expression of the type ascribed to the const parameter. The const expression must be a block expression (surrounded with braces) unless it is a single path segment (an IDENTIFIER) or a literal (with a possibly leading - token).
Note

This syntactic restriction is necessary to avoid requiring infinite lookahead when parsing an expression inside of a type.
struct S<const N: i64>;
const C: i64 = 1;
fn f<const N: i64>() -> S<N> { S }

let _ = f::<1>(); // Literal.
let _ = f::<-1>(); // Negative literal.
let _ = f::<{ 1 + 2 }>(); // Constant expression.
let _ = f::<C>(); // Single segment path.
let _ = f::<{ C + 1 }>(); // Constant expression.
let _: S<1> = f::<_>(); // Inferred const.
let _: S<1> = f::<(((_)))>(); // Inferred const.
Note

In a generic argument list, an inferred const is parsed as an inferred type but then semantically treated as a separate kind of const generic argument.
[items.generics.const.inferred]
Where a const argument is expected, an _ (optionally surrounded by any number of matching parentheses), called the inferred const (path rules, array expression rules), can be used instead. This asks the compiler to infer the const argument if possible based on surrounding information.
fn make_buf<const N: usize>() -> [u8; N] {
    [0; _]
    //  ^ Infers `N`.
}
let _: [u8; 1024] = make_buf::<_>();
//                             ^ Infers `1024`.
Note

An inferred const is not semantically an expression and so is not accepted within braces.

fn f<const N: usize>() -> [u8; N] { [0; _] }
let _: [_; 1] = f::<{ _ }>();
//                    ^ ERROR `_` not allowed here
[items.generics.const.inferred.constraint]
The inferred const cannot be used in item signatures.
fn f<const N: usize>(x: [u8; N]) -> [u8; _] { x }
//                                       ^ ERROR not allowed
[items.generics.const.type-ambiguity]
When there is ambiguity if a generic argument could be resolved as either a type or const argument, it is always resolved as a type. Placing the argument in a block expression can force it to be interpreted as a const argument.
type N = u32;
struct Foo<const N: usize>;
// The following is an error, because `N` is interpreted as the type alias `N`.
fn foo<const N: usize>() -> Foo<N> { todo!() } // ERROR
// Can be fixed by wrapping in braces to force it to be interpreted as the `N`
// const parameter:
fn bar<const N: usize>() -> Foo<{ N }> { todo!() } // ok
[items.generics.const.variance]
Unlike type and lifetime parameters, const parameters can be declared without being used inside of a parameterized item, with the exception of implementations as described in generic implementations:
// ok
struct Foo<const N: usize>;
enum Bar<const M: usize> { A, B }

// ERROR: unused parameter
struct Baz<T>;
struct Biz<'a>;
struct Unconstrained;
impl<const N: usize> Unconstrained {}
[items.generics.const.exhaustiveness]
When resolving a trait bound obligation, the exhaustiveness of all implementations of const parameters is not considered when determining if the bound is satisfied. For example, in the following, even though all possible const values for the bool type are implemented, it is still an error that the trait bound is not satisfied:
struct Foo<const B: bool>;
trait Bar {}
impl Bar for Foo<true> {}
impl Bar for Foo<false> {}

fn needs_bar(_: impl Bar) {}
fn generic<const B: bool>() {
    let v = Foo::<B>;
    needs_bar(v); // ERROR: trait bound `Foo<B>: Bar` is not satisfied
}
[items.generics.where]
Where clauses
[items.generics.where.syntax]
Syntax
WhereClause → where ( WhereClauseItem , )* WhereClauseItem?

WhereClauseItem →
      LifetimeWhereClauseItem
    | TypeBoundWhereClauseItem

LifetimeWhereClauseItem → Lifetime : LifetimeBounds

TypeBoundWhereClauseItem → ForLifetimes? Type : TypeParamBounds?

Show syntax diagrams

[items.generics.where.intro]
Where clauses provide another way to specify bounds on type and lifetime parameters as well as a way to specify bounds on types that aren’t type parameters.
[items.generics.where.higher-ranked-lifetimes]
The for keyword can be used to introduce higher-ranked lifetimes. It only allows LifetimeParam parameters.
struct A<T>
where
    T: Iterator,            // Could use A<T: Iterator> instead
    T::Item: Copy,          // Bound on an associated type
    String: PartialEq<T>,   // Bound on `String`, using the type parameter
    i32: Default,           // Allowed, but not useful
{
    f: T,
}
[items.generics.attributes]
Attributes
Generic lifetime and type parameters allow attributes on them. There are no built-in attributes that do anything in this position, although custom derive attributes may give meaning to it.
This example shows using a custom derive attribute to modify the meaning of a generic parameter.
// Assume that the derive for MyFlexibleClone declared `my_flexible_clone` as
// an attribute it understands.
#[derive(MyFlexibleClone)]
struct Foo<#[my_flexible_clone(unbounded)] H> {
    a: *const H
}
[items.associated]
Associated Items

[items.associated.syntax]
Syntax
AssociatedItem →
    OuterAttribute* (
        MacroInvocationSemi
      | ( Visibility? ( TypeAlias | ConstantItem | Function ) )
    )

Show syntax diagrams

[items.associated.intro]
Associated Items are the items declared in traits or defined in implementations. They are called this because they are defined on an associate type — the type in the implementation.
[items.associated.kinds]
They are a subset of the kinds of items you can declare in a module. Specifically, there are associated functions (including methods), associated types, and associated constants.
[items.associated.related]
Associated items are useful when the associated item is logically related to the associating item. For example, the is_some method on Option is intrinsically related to Options, so should be associated.
[items.associated.decl-def]
Every associated item kind comes in two varieties: definitions that contain the actual implementation and declarations that declare signatures for definitions.
[items.associated.trait-items]
It is the declarations that make up the contract of traits and what is available on generic types.
[items.associated.fn]
Associated functions and methods
[items.associated.fn.intro]
Associated functions are functions associated with a type.
[items.associated.fn.decl]
An associated function declaration declares a signature for an associated function definition. It is written as a function item, except the function body is replaced with a ;.
[items.associated.name]
The identifier is the name of the function.
[items.associated.same-signature]
The generics, parameter list, return type, and where clause of the associated function must be the same as the associated function declarations’s.
[items.associated.fn.def]
An associated function definition defines a function associated with another type. It is written the same as a function item.
Note

A common example is an associated function named new that returns a value of the type with which it is associated.
struct Struct {
    field: i32
}

impl Struct {
    fn new() -> Struct {
        Struct {
            field: 0i32
        }
    }
}

fn main () {
    let _struct = Struct::new();
}
[items.associated.fn.qualified-self]
When the associated function is declared on a trait, the function can also be called with a path that is a path to the trait appended by the name of the trait. When this happens, it is substituted for <_ as Trait>::function_name.
trait Num {
    fn from_i32(n: i32) -> Self;
}

impl Num for f64 {
    fn from_i32(n: i32) -> f64 { n as f64 }
}

// These 4 are all equivalent in this case.
let _: f64 = Num::from_i32(42);
let _: f64 = <_ as Num>::from_i32(42);
let _: f64 = <f64 as Num>::from_i32(42);
let _: f64 = f64::from_i32(42);
[items.associated.fn.method]
Methods
[items.associated.fn.method.intro]
Associated functions whose first parameter is named self are called methods and may be invoked using the method call operator, for example, x.foo(), as well as the usual function call notation.
[items.associated.fn.method.self-ty]
If the type of the self parameter is specified, it is limited to types resolving to one generated by the following grammar (where 'lt denotes some arbitrary lifetime):
P = &'lt S | &'lt mut S | Box<S> | Rc<S> | Arc<S> | Pin<P>
S = Self | P
The Self terminal in this grammar denotes a type resolving to the implementing type. This can also include the contextual type alias Self, other type aliases, or associated type projections resolving to the implementing type.
// Examples of methods implemented on struct `Example`.
struct Example;
type Alias = Example;
trait Trait { type Output; }
impl Trait for Example { type Output = Example; }
impl Example {
    fn by_value(self: Self) {}
    fn by_ref(self: &Self) {}
    fn by_ref_mut(self: &mut Self) {}
    fn by_box(self: Box<Self>) {}
    fn by_rc(self: Rc<Self>) {}
    fn by_arc(self: Arc<Self>) {}
    fn by_pin(self: Pin<&Self>) {}
    fn explicit_type(self: Arc<Example>) {}
    fn with_lifetime<'a>(self: &'a Self) {}
    fn nested<'a>(self: &mut &'a Arc<Rc<Box<Alias>>>) {}
    fn via_projection(self: <Example as Trait>::Output) {}
}
[associated.fn.method.self-pat-shorthands]
Shorthand syntax can be used without specifying a type, which have the following equivalents:
Shorthand	Equivalent
self	self: Self
&'lifetime self	self: &'lifetime Self
&'lifetime mut self	self: &'lifetime mut Self
Note

Lifetimes can be, and usually are, elided with this shorthand.
[associated.fn.method.self-pat-mut]
If the self parameter is prefixed with mut, it becomes a mutable variable, similar to regular parameters using a mut identifier pattern. For example:
trait Changer: Sized {
    fn change(mut self) {}
    fn modify(mut self: Box<Self>) {}
}
As an example of methods on a trait, consider the following:
trait Shape {
    fn draw(&self, surface: Surface);
    fn bounding_box(&self) -> BoundingBox;
}
This defines a trait with two methods. All values that have implementations of this trait while the trait is in scope can have their draw and bounding_box methods called.
struct Circle {
    // ...
}

impl Shape for Circle {
    // ...
}

let circle_shape = Circle::new();
let bounding_box = circle_shape.bounding_box();
[items.associated.fn.params.edition2018]
2018
Edition differences

In the 2015 edition, it is possible to declare trait methods with anonymous parameters (e.g. fn foo(u8)). This is deprecated and an error as of the 2018 edition. All parameters must have an argument name.
[items.associated.fn.param-attributes]
Attributes on method parameters
Attributes on method parameters follow the same rules and restrictions as regular function parameters.
[items.associated.type]
Associated Types
[items.associated.type.intro]
Associated types are type aliases associated with another type.
[items.associated.type.restrictions]
Associated types cannot be defined in inherent implementations nor can they be given a default implementation in traits.
[items.associated.type.decl]
An associated type declaration declares a signature for associated type definitions. It is written in one of the following forms, where Assoc is the name of the associated type, Params is a comma-separated list of type, lifetime or const parameters, Bounds is a plus-separated list of trait bounds that the associated type must meet, and WhereBounds is a comma-separated list of bounds that the parameters must meet:
type Assoc;
type Assoc: Bounds;
type Assoc<Params>;
type Assoc<Params>: Bounds;
type Assoc<Params> where WhereBounds;
type Assoc<Params>: Bounds where WhereBounds;
[items.associated.type.name]
The identifier is the name of the declared type alias.
[items.associated.type.impl-fulfillment]
The optional trait bounds must be fulfilled by the implementations of the type alias.
[items.associated.type.sized]
There is an implicit Sized bound on associated types that can be relaxed using the special ?Sized bound.
[items.associated.type.def]
An associated type definition defines a type alias for the implementation of a trait on a type
[items.associated.type.def.restriction]
They are written similarly to an associated type declaration, but cannot contain Bounds, but instead must contain a Type:
type Assoc = Type;
type Assoc<Params> = Type; // the type `Type` here may reference `Params`
type Assoc<Params> = Type where WhereBounds;
type Assoc<Params> where WhereBounds = Type; // deprecated, prefer the form above
[items.associated.type.alias]
If a type Item has an associated type Assoc from a trait Trait, then <Item as Trait>::Assoc is a type that is an alias of the type specified in the associated type definition
[items.associated.type.param]
Furthermore, if Item is a type parameter, then Item::Assoc can be used in type parameters.
[items.associated.type.generic]
Associated types may include generic parameters and where clauses; these are often referred to as generic associated types, or GATs. If the type Thing has an associated type Item from a trait Trait with the generics <'a> , the type can be named like <Thing as Trait>::Item<'x>, where 'x is some lifetime in scope. In this case, 'x will be used wherever 'a appears in the associated type definitions on impls.
trait AssociatedType {
    // Associated type declaration
    type Assoc;
}

struct Struct;

struct OtherStruct;

impl AssociatedType for Struct {
    // Associated type definition
    type Assoc = OtherStruct;
}

impl OtherStruct {
    fn new() -> OtherStruct {
        OtherStruct
    }
}

fn main() {
    // Usage of the associated type to refer to OtherStruct as <Struct as AssociatedType>::Assoc
    let _other_struct: OtherStruct = <Struct as AssociatedType>::Assoc::new();
}
An example of associated types with generics and where clauses:
struct ArrayLender<'a, T>(&'a mut [T; 16]);

trait Lend {
    // Generic associated type declaration
    type Lender<'a> where Self: 'a;
    fn lend<'a>(&'a mut self) -> Self::Lender<'a>;
}

impl<T> Lend for [T; 16] {
    // Generic associated type definition
    type Lender<'a> = ArrayLender<'a, T> where Self: 'a;

    fn lend<'a>(&'a mut self) -> Self::Lender<'a> {
        ArrayLender(self)
    }
}

fn borrow<'a, T: Lend>(array: &'a mut T) -> <T as Lend>::Lender<'a> {
    array.lend()
}

fn main() {
    let mut array = [0usize; 16];
    let lender = borrow(&mut array);
}
Associated Types Container Example
Consider the following example of a Container trait. Notice that the type is available for use in the method signatures:
trait Container {
    type E;
    fn empty() -> Self;
    fn insert(&mut self, elem: Self::E);
}
In order for a type to implement this trait, it must not only provide implementations for every method, but it must specify the type E. Here’s an implementation of Container for the standard library type Vec:
impl<T> Container for Vec<T> {
    type E = T;
    fn empty() -> Vec<T> { Vec::new() }
    fn insert(&mut self, x: T) { self.push(x); }
}
Relationship between Bounds and WhereBounds
In this example:
trait Example {
    type Output<T>: Ord where T: Debug;
}
Given a reference to the associated type like <X as Example>::Output<Y>, the associated type itself must be Ord, and the type Y must be Debug.
[items.associated.type.generic-where-clause]
Required where clauses on generic associated types
[items.associated.type.generic-where-clause.intro]
Generic associated type declarations on traits currently may require a list of where clauses, dependent on functions in the trait and how the GAT is used. These rules may be loosened in the future; updates can be found on the generic associated types initiative repository.
[items.associated.type.generic-where-clause.valid-fn]
In a few words, these where clauses are required in order to maximize the allowed definitions of the associated type in impls. To do this, any clauses that can be proven to hold on functions (using the parameters of the function or trait) where a GAT appears as an input or output must also be written on the GAT itself.
trait LendingIterator {
    type Item<'x> where Self: 'x;
    fn next<'a>(&'a mut self) -> Self::Item<'a>;
}
In the above, on the next function, we can prove that Self: 'a, because of the implied bounds from &'a mut self; therefore, we must write the equivalent bound on the GAT itself: where Self: 'x.
[items.associated.type.generic-where-clause.intersection]
When there are multiple functions in a trait that use the GAT, then the intersection of the bounds from the different functions are used, rather than the union.
trait Check<T> {
    type Checker<'x>;
    fn create_checker<'a>(item: &'a T) -> Self::Checker<'a>;
    fn do_check(checker: Self::Checker<'_>);
}
In this example, no bounds are required on the type Checker<'a>;. While we know that T: 'a on create_checker, we do not know that on do_check. However, if do_check was commented out, then the where T: 'x bound would be required on Checker.
[items.associated.type.generic-where-clause.forward]
The bounds on associated types also propagate required where clauses.
trait Iterable {
    type Item<'a> where Self: 'a;
    type Iterator<'a>: Iterator<Item = Self::Item<'a>> where Self: 'a;
    fn iter<'a>(&'a self) -> Self::Iterator<'a>;
}
Here, where Self: 'a is required on Item because of iter. However, Item is used in the bounds of Iterator, the where Self: 'a clause is also required there.
[items.associated.type.generic-where-clause.static]
Finally, any explicit uses of 'static on GATs in the trait do not count towards the required bounds.
trait StaticReturn {
    type Y<'a>;
    fn foo(&self) -> Self::Y<'static>;
}
[items.associated.const]
Associated Constants
[items.associated.const.intro]
Associated constants are constants associated with a type.
[items.associated.const.decl]
An associated constant declaration declares a signature for associated constant definitions. It is written as const, then an identifier, then :, then a type, finished by a ;.
[items.associated.const.name]
The identifier is the name of the constant used in the path. The type is the type that the definition has to implement.
[items.associated.const.def]
An associated constant definition defines a constant associated with a type. It is written the same as a constant item.
[items.associated.const.eval]
Associated constant definitions undergo constant evaluation only when referenced. Further, definitions that include generic parameters are evaluated after monomorphization.
struct Struct;
struct GenericStruct<const ID: i32>;

impl Struct {
    // Definition not immediately evaluated
    const PANIC: () = panic!("compile-time panic");
}

impl<const ID: i32> GenericStruct<ID> {
    // Definition not immediately evaluated
    const NON_ZERO: () = if ID == 0 {
        panic!("contradiction")
    };
}

fn main() {
    // Referencing Struct::PANIC causes compilation error
    let _ = Struct::PANIC;

    // Fine, ID is not 0
    let _ = GenericStruct::<1>::NON_ZERO;

    // Compilation error from evaluating NON_ZERO with ID=0
    let _ = GenericStruct::<0>::NON_ZERO;
}
Associated Constants Examples
A basic example:
trait ConstantId {
    const ID: i32;
}

struct Struct;

impl ConstantId for Struct {
    const ID: i32 = 1;
}

fn main() {
    assert_eq!(1, Struct::ID);
}
Using default values:
trait ConstantIdDefault {
    const ID: i32 = 1;
}

struct Struct;
struct OtherStruct;

impl ConstantIdDefault for Struct {}

impl ConstantIdDefault for OtherStruct {
    const ID: i32 = 5;
}

fn main() {
    assert_eq!(1, Struct::ID);
    assert_eq!(5, OtherStruct::ID);
}
[attributes]
Attributes

[attributes.syntax]
Syntax
InnerAttribute → # ! [ Attr ]

OuterAttribute → # [ Attr ]

Attr →
      SimplePath AttrInput?
    | unsafe ( SimplePath AttrInput? )

AttrInput →
      DelimTokenTree
    | = Expression

Show syntax diagrams

[attributes.intro]
An attribute is a general, free-form metadatum that is interpreted according to name, convention, language, and compiler version. Attributes are modeled on Attributes in ECMA-335, with the syntax coming from ECMA-334 (C#).
[attributes.inner]
Inner attributes, written with a bang (!) after the hash (#), apply to the item that the attribute is declared within. Outer attributes, written without the bang after the hash, apply to the thing that follows the attribute.
[attributes.input]
The attribute consists of a path to the attribute, followed by an optional delimited token tree whose interpretation is defined by the attribute. Attributes other than macro attributes also allow the input to be an equals sign (=) followed by an expression. See the meta item syntax below for more details.
[attributes.safety]
An attribute may be unsafe to apply. To avoid undefined behavior when using these attributes, certain obligations that cannot be checked by the compiler must be met. To assert these have been, the attribute is wrapped in unsafe(..), e.g. #[unsafe(no_mangle)].
The following attributes are unsafe:
export_name
link_section
naked
no_mangle
[attributes.kind]
Attributes can be classified into the following kinds:
Built-in attributes
Proc macro attributes
Derive macro helper attributes
Tool attributes
[attributes.allowed-position]
Attributes may be applied to many things in the language:
All item declarations accept outer attributes while external blocks, functions, implementations, and modules accept inner attributes.
Most statements accept outer attributes (see Expression Attributes for limitations on expression statements).
Block expressions accept outer and inner attributes, but only when they are the outer expression of an expression statement or the final expression of another block expression.
Enum variants and struct and union fields accept outer attributes.
Match expression arms accept outer attributes.
Generic lifetime or type parameter accept outer attributes.
Expressions accept outer attributes in limited situations, see Expression Attributes for details.
Function, closure and function pointer parameters accept outer attributes. This includes attributes on variadic parameters denoted with ... in function pointers and external blocks.
Some examples of attributes:
// General metadata applied to the enclosing module or crate.
#![crate_type = "lib"]

// A function marked as a unit test
#[test]
fn test_foo() {
    /* ... */
}

// A conditionally-compiled module
#[cfg(target_os = "linux")]
mod bar {
    /* ... */
}

// A lint attribute used to suppress a warning/error
#[allow(non_camel_case_types)]
type int8_t = i8;

// Inner attribute applies to the entire function.
fn some_unused_variables() {
  #![allow(unused_variables)]

  let x = ();
  let y = ();
  let z = ();
}
[attributes.meta]
Meta Item Attribute Syntax
[attributes.meta.intro]
A “meta item” is the syntax used for the Attr rule by most built-in attributes. It has the following grammar:
[attributes.meta.syntax]
Syntax
MetaItem →
      SimplePath
    | SimplePath = Expression
    | SimplePath ( MetaSeq? )

MetaSeq →
    MetaItemInner ( , MetaItemInner )* ,?

MetaItemInner →
      MetaItem
    | Expression

Show syntax diagrams

[attributes.meta.literal-expr]
Expressions in meta items must macro-expand to literal expressions, which must not include integer or float type suffixes. Expressions which are not literal expressions will be syntactically accepted (and can be passed to proc-macros), but will be rejected after parsing.
[attributes.meta.order]
Note that if the attribute appears within another macro, it will be expanded after that outer macro. For example, the following code will expand the Serialize proc-macro first, which must preserve the include_str! call in order for it to be expanded:
#[derive(Serialize)]
struct Foo {
    #[doc = include_str!("x.md")]
    x: u32
}
[attributes.meta.order-macro]
Additionally, macros in attributes will be expanded only after all other attributes applied to the item:
#[macro_attr1] // expanded first
#[doc = mac!()] // `mac!` is expanded fourth.
#[macro_attr2] // expanded second
#[derive(MacroDerive1, MacroDerive2)] // expanded third
fn foo() {}
[attributes.meta.builtin]
Various built-in attributes use different subsets of the meta item syntax to specify their inputs. The following grammar rules show some commonly used forms:
[attributes.meta.builtin.syntax]
Syntax
MetaWord →
    IDENTIFIER

MetaNameValueStr →
    IDENTIFIER = ( STRING_LITERAL | RAW_STRING_LITERAL )

MetaListPaths →
    IDENTIFIER ( ( SimplePath ( , SimplePath )* ,? )? )

MetaListIdents →
    IDENTIFIER ( ( IDENTIFIER ( , IDENTIFIER )* ,? )? )

MetaListNameValueStr →
    IDENTIFIER ( ( MetaNameValueStr ( , MetaNameValueStr )* ,? )? )

Show syntax diagrams

Some examples of meta items are:
Style	Example
MetaWord	no_std
MetaNameValueStr	doc = "example"
MetaListPaths	allow(unused, clippy::inline_always)
MetaListIdents	macro_use(foo, bar)
MetaListNameValueStr	link(name = "CoreFoundation", kind = "framework")
[attributes.activity]
Active and inert attributes
[attributes.activity.intro]
An attribute is either active or inert. During attribute processing, active attributes remove themselves from the thing they are on while inert attributes stay on.
The cfg and cfg_attr attributes are active. Attribute macros are active. All other attributes are inert.
[attributes.tool]
Tool attributes
[attributes.tool.intro]
The compiler may allow attributes for external tools where each tool resides in its own module in the tool prelude. The first segment of the attribute path is the name of the tool, with one or more additional segments whose interpretation is up to the tool.
[attributes.tool.ignored]
When a tool is not in use, the tool’s attributes are accepted without a warning. When the tool is in use, the tool is responsible for processing and interpretation of its attributes.
[attributes.tool.prelude]
Tool attributes are not available if the no_implicit_prelude attribute is used.
// Tells the rustfmt tool to not format the following element.
#[rustfmt::skip]
struct S {
}

// Controls the "cyclomatic complexity" threshold for the clippy tool.
#[clippy::cyclomatic_complexity = "100"]
pub fn f() {}
Note

rustc currently recognizes the tools “clippy”, “rustfmt”, “diagnostic”, “miri” and “rust_analyzer”.
[attributes.builtin]
Built-in attributes index
The following is an index of all built-in attributes.
Conditional compilation

cfg — Controls conditional compilation.
cfg_attr — Conditionally includes attributes.
## Testing

test — Marks a function as a test.
ignore — Disables a test function.
should_panic — Indicates a test should generate a panic.
## Derive

derive — Automatic trait implementations.
automatically_derived — Marker for implementations created by derive.
Macros

macro_export — Exports a macro_rules macro for cross-crate usage.
macro_use — Expands macro visibility, or imports macros from other crates.
proc_macro — Defines a function-like macro.
proc_macro_derive — Defines a derive macro.
proc_macro_attribute — Defines an attribute macro.
## Diagnostics

allow, expect, warn, deny, forbid — Alters the default lint level.
deprecated — Generates deprecation notices.
must_use — Generates a lint for unused values.
diagnostic::on_unimplemented — Hints the compiler to emit a certain error message if a trait is not implemented.
diagnostic::do_not_recommend — Hints the compiler to not show a certain trait impl in error messages.
ABI, linking, symbols, and FFI

link — Specifies a native library to link with an extern block.
link_name — Specifies the name of the symbol for functions or statics in an extern block.
link_ordinal — Specifies the ordinal of the symbol for functions or statics in an extern block.
no_link — Prevents linking an extern crate.
repr — Controls type layout.
crate_type — Specifies the type of crate (library, executable, etc.).
no_main — Disables emitting the main symbol.
export_name — Specifies the exported symbol name for a function or static.
link_section — Specifies the section of an object file to use for a function or static.
no_mangle — Disables symbol name encoding.
used — Forces the compiler to keep a static item in the output object file.
crate_name — Specifies the crate name.
## Code generation

inline — Hint to inline code.
cold — Hint that a function is unlikely to be called.
naked — Prevent the compiler from emitting a function prologue and epilogue.
no_builtins — Disables use of certain built-in functions.
target_feature — Configure platform-specific code generation.
track_caller — Pass the parent call location to std::panic::Location::caller().
instruction_set — Specify the instruction set used to generate a functions code
Documentation

doc — Specifies documentation. See The Rustdoc Book for more information. Doc comments are transformed into doc attributes.
Preludes

no_std — Removes std from the prelude.
no_implicit_prelude — Disables prelude lookups within a module.
Modules

path — Specifies the filename for a module.
## Limits

recursion_limit — Sets the maximum recursion limit for certain compile-time operations.
type_length_limit — Sets the maximum size of a polymorphic type.
Runtime

panic_handler — Sets the function to handle panics.
global_allocator — Sets the global memory allocator.
windows_subsystem — Specifies the windows subsystem to link with.
Features

feature — Used to enable unstable or experimental compiler features. See The Unstable Book for features implemented in rustc.
## Type System

non_exhaustive — Indicate that a type will have more fields/variants added in future.
## Debugger

debugger_visualizer — Embeds a file that specifies debugger output for a type.
collapse_debuginfo — Controls how macro invocations are encoded in debuginfo.
[attributes.testing]
Testing attributes

The following attributes are used for specifying functions for performing tests. Compiling a crate in “test” mode enables building the test functions along with a test harness for executing the tests. Enabling the test mode also enables the test conditional compilation option.
[attributes.testing.test]
The test attribute
[attributes.testing.test.intro]
The test attribute marks a function to be executed as a test.
Example

#[test]
fn it_works() {
    let result = add(2, 2);
    assert_eq!(result, 4);
}
[attributes.testing.test.syntax]
The test attribute uses the MetaWord syntax.
[attributes.testing.test.allowed-positions]
The test attribute may only be applied to free functions that are monomorphic, that take no arguments, and where the return type implements the Termination trait.
Note

Some of types that implement the Termination trait include:

()
Result<T, E> where T: Termination, E: Debug
[attributes.testing.test.duplicates]
Only the first use of test on a function has effect.
Note

rustc lints against any use following the first. This may become an error in the future.
[attributes.testing.test.stdlib]
The test attribute is exported from the standard library prelude as std::prelude::v1::test.
[attributes.testing.test.enabled]
These functions are only compiled when in test mode.
Note

The test mode is enabled by passing the --test argument to rustc or using cargo test.
[attributes.testing.test.success]
The test harness calls the returned value’s report method, and classifies the test as passed or failed depending on whether the resulting ExitCode represents successful termination. In particular:
Tests that return () pass as long as they terminate and do not panic.
Tests that return a Result<(), E> pass as long as they return Ok(()).
Tests that return ExitCode::SUCCESS pass, and tests that return ExitCode::FAILURE fail.
Tests that do not terminate neither pass nor fail.
Example

#[test]
fn test_the_thing() -> io::Result<()> {
    let state = setup_the_thing()?; // expected to succeed
    do_the_thing(&state)?;          // expected to succeed
    Ok(())
}
[attributes.testing.ignore]
The ignore attribute
[attributes.testing.ignore.intro]
The ignore attribute can be used with the test attribute to tell the test harness to not execute that function as a test.
Example

#[test]
#[ignore]
fn check_thing() {
    // …
}
Note

The rustc test harness supports the --include-ignored flag to force ignored tests to be run.
[attributes.testing.ignore.syntax]
The ignore attribute uses the MetaWord and MetaNameValueStr syntaxes.
[attributes.testing.ignore.reason]
The MetaNameValueStr form of the ignore attribute provides a way to specify a reason why the test is ignored.
Example

#[test]
#[ignore = "not yet implemented"]
fn mytest() {
    // …
}
[attributes.testing.ignore.allowed-positions]
The ignore attribute may only be applied to functions annotated with the test attribute.
Note

rustc ignores use in other positions but lints against it. This may become an error in the future.
[attributes.testing.ignore.duplicates]
Only the first use of ignore on a function has effect.
Note

rustc lints against any use following the first. This may become an error in the future.
[attributes.testing.ignore.behavior]
Ignored tests are still compiled when in test mode, but they are not executed.
[attributes.testing.should_panic]
The should_panic attribute
[attributes.testing.should_panic.intro]
The should_panic attribute causes a test to pass only if the test function to which the attribute is applied panics.
Example

#[test]
#[should_panic(expected = "values don't match")]
fn mytest() {
    assert_eq!(1, 2, "values don't match");
}
[attributes.testing.should_panic.syntax]
The should_panic attribute has these forms:
MetaWord

Example

#[test]
#[should_panic]
fn mytest() { panic!("error: some message, and more"); }
MetaNameValueStr — The given string must appear within the panic message for the test to pass.

Example

#[test]
#[should_panic = "some message"]
fn mytest() { panic!("error: some message, and more"); }
MetaListNameValueStr — As with the MetaNameValueStr syntax, the given string must appear within the panic message.

Example

#[test]
#[should_panic(expected = "some message")]
fn mytest() { panic!("error: some message, and more"); }
[attributes.testing.should_panic.allowed-positions]
The should_panic attribute may only be applied to functions annotated with the test attribute.
Note

rustc ignores use in other positions but lints against it. This may become an error in the future.
[attributes.testing.should_panic.duplicates]
Only the first use of should_panic on a function has effect.
Note

rustc lints against any use following the first with a future-compatibility warning. This may become an error in the future.
[attributes.testing.should_panic.expected]
When the MetaNameValueStr form or the MetaListNameValueStr form with the expected key is used, the given string must appear somewhere within the panic message for the test to pass.
[attributes.testing.should_panic.return]
The return type of the test function must be ().
[attributes.derive]
Derive

[attributes.derive.intro]
The derive attribute invokes one or more derive macros, allowing new items to be automatically generated for data structures. You can create derive macros with procedural macros.
Example

The PartialEq derive macro emits an implementation of PartialEq for Foo<T> where T: PartialEq. The Clone derive macro does likewise for Clone.

#[derive(PartialEq, Clone)]
struct Foo<T> {
    a: i32,
    b: T,
}
The generated impl items are equivalent to:

impl<T: PartialEq> PartialEq for Foo<T> {
    fn eq(&self, other: &Foo<T>) -> bool {
        self.a == other.a && self.b == other.b
    }
}

impl<T: Clone> Clone for Foo<T> {
    fn clone(&self) -> Self {
        Foo { a: self.a.clone(), b: self.b.clone() }
    }
}
[attributes.derive.syntax]
The derive attribute uses the MetaListPaths syntax to specify a list of paths to derive macros to invoke.
[attributes.derive.allowed-positions]
The derive attribute may only be applied to structs, enums, and unions.
[attributes.derive.duplicates]
The derive attribute may be used any number of times on an item. All derive macros listed in all attributes are invoked.
[attributes.derive.stdlib]
The derive attribute is exported in the standard library prelude as core::prelude::v1::derive.
[attributes.derive.built-in]
Built-in derives are defined in the language prelude. The list of built-in derives are:
Clone
Copy
Debug
Default
Eq
Hash
Ord
PartialEq
PartialOrd
[attributes.derive.built-in-automatically_derived]
The built-in derives include the automatically_derived attribute on the implementations they generate.
[attributes.derive.behavior]
During macro expansion, for each element in the list of derives, the corresponding derive macro expands to zero or more items.
[attributes.derive.automatically_derived]
The automatically_derived attribute
[attributes.derive.automatically_derived.intro]
The automatically_derived attribute is used to annotate an implementation to indicate that it was automatically created by a derive macro. It has no direct effect, but it may be used by tools and diagnostic lints to detect these automatically generated implementations.
Example

Given #[derive(Clone)] on struct Example, the derive macro may produce:

#[automatically_derived]
impl ::core::clone::Clone for Example {
    #[inline]
    fn clone(&self) -> Self {
        Example
    }
}
[attributes.derive.automatically_derived.syntax]
The automatically_derived attribute uses the MetaWord syntax.
[attributes.derive.automatically_derived.allowed-positions]
The automatically_derived attribute may only be applied to an implementation.
Note

rustc ignores use in other positions but lints against it. This may become an error in the future.
[attributes.derive.automatically_derived.duplicates]
Using automatically_derived more than once on an implementation has the same effect as using it once.
Note

rustc lints against any use following the first.
[attributes.derive.automatically_derived.behavior]
The automatically_derived attribute has no behavior.
[attributes.diagnostics]
Diagnostic attributes

The following attributes are used for controlling or generating diagnostic messages during compilation.
[attributes.diagnostics.lint]
Lint check attributes
A lint check names a potentially undesirable coding pattern, such as unreachable code or omitted documentation.
[attributes.diagnostics.lint.level]
The lint attributes allow, expect, warn, deny, and forbid use the MetaListPaths syntax to specify a list of lint names to change the lint level for the entity to which the attribute applies.
For any lint check C:
[attributes.diagnostics.lint.allow]
#[allow(C)] overrides the check for C so that violations will go unreported.
[attributes.diagnostics.lint.expect]
#[expect(C)] indicates that lint C is expected to be emitted. The attribute will suppress the emission of C or issue a warning, if the expectation is unfulfilled.
[attributes.diagnostics.lint.warn]
#[warn(C)] warns about violations of C but continues compilation.
[attributes.diagnostics.lint.deny]
#[deny(C)] signals an error after encountering a violation of C,
[attributes.diagnostics.lint.forbid]
#[forbid(C)] is the same as deny(C), but also forbids changing the lint level afterwards,
Note

The lint checks supported by rustc can be found via rustc -W help, along with their default settings and are documented in the rustc book.
pub mod m1 {
    // Missing documentation is ignored here
    #[allow(missing_docs)]
    pub fn undocumented_one() -> i32 { 1 }

    // Missing documentation signals a warning here
    #[warn(missing_docs)]
    pub fn undocumented_too() -> i32 { 2 }

    // Missing documentation signals an error here
    #[deny(missing_docs)]
    pub fn undocumented_end() -> i32 { 3 }
}
[attributes.diagnostics.lint.override]
Lint attributes can override the level specified from a previous attribute, as long as the level does not attempt to change a forbidden lint (except for deny, which is allowed inside a forbid context, but ignored). Previous attributes are those from a higher level in the syntax tree, or from a previous attribute on the same entity as listed in left-to-right source order.
This example shows how one can use allow and warn to toggle a particular check on and off:
#[warn(missing_docs)]
pub mod m2 {
    #[allow(missing_docs)]
    pub mod nested {
        // Missing documentation is ignored here
        pub fn undocumented_one() -> i32 { 1 }

        // Missing documentation signals a warning here,
        // despite the allow above.
        #[warn(missing_docs)]
        pub fn undocumented_two() -> i32 { 2 }
    }

    // Missing documentation signals a warning here
    pub fn undocumented_too() -> i32 { 3 }
}
This example shows how one can use forbid to disallow uses of allow or expect for that lint check:
#[forbid(missing_docs)]
pub mod m3 {
    // Attempting to toggle warning signals an error here
    #[allow(missing_docs)]
    /// Returns 2.
    pub fn undocumented_too() -> i32 { 2 }
}
Note

rustc allows setting lint levels on the command-line, and also supports setting caps on the lints that are reported.
[attributes.diagnostics.lint.reason]
Lint Reasons
All lint attributes support an additional reason parameter, to give context why a certain attribute was added. This reason will be displayed as part of the lint message if the lint is emitted at the defined level.
// `keyword_idents` is allowed by default. Here we deny it to
// avoid migration of identifiers when we update the edition.
#![deny(
    keyword_idents,
    reason = "we want to avoid these idents to be future compatible"
)]

// This name was allowed in Rust's 2015 edition. We still aim to avoid
// this to be future compatible and not confuse end users.
fn dyn() {}
Here is another example, where the lint is allowed with a reason:
use std::path::PathBuf;

pub fn get_path() -> PathBuf {
    // The `reason` parameter on `allow` attributes acts as documentation for the reader.
    #[allow(unused_mut, reason = "this is only modified on some platforms")]
    let mut file_name = PathBuf::from("git");

    #[cfg(target_os = "windows")]
    file_name.set_extension("exe");

    file_name
}
[attributes.diagnostics.expect]
The #[expect] attribute
[attributes.diagnostics.expect.intro]
The #[expect(C)] attribute creates a lint expectation for lint C. The expectation will be fulfilled, if a #[warn(C)] attribute at the same location would result in a lint emission. If the expectation is unfulfilled, because lint C would not be emitted, the unfulfilled_lint_expectations lint will be emitted at the attribute.
fn main() {
    // This `#[expect]` attribute creates a lint expectation, that the `unused_variables`
    // lint would be emitted by the following statement. This expectation is
    // unfulfilled, since the `question` variable is used by the `println!` macro.
    // Therefore, the `unfulfilled_lint_expectations` lint will be emitted at the
    // attribute.
    #[expect(unused_variables)]
    let question = "who lives in a pineapple under the sea?";
    println!("{question}");

    // This `#[expect]` attribute creates a lint expectation that will be fulfilled, since
    // the `answer` variable is never used. The `unused_variables` lint, that would usually
    // be emitted, is suppressed. No warning will be issued for the statement or attribute.
    #[expect(unused_variables)]
    let answer = "SpongeBob SquarePants!";
}
[attributes.diagnostics.expect.fulfillment]
The lint expectation is only fulfilled by lint emissions which have been suppressed by the expect attribute. If the lint level is modified in the scope with other level attributes like allow or warn, the lint emission will be handled accordingly and the expectation will remain unfulfilled.
#[expect(unused_variables)]
fn select_song() {
    // This will emit the `unused_variables` lint at the warn level
    // as defined by the `warn` attribute. This will not fulfill the
    // expectation above the function.
    #[warn(unused_variables)]
    let song_name = "Crab Rave";

    // The `allow` attribute suppresses the lint emission. This will not
    // fulfill the expectation as it has been suppressed by the `allow`
    // attribute and not the `expect` attribute above the function.
    #[allow(unused_variables)]
    let song_creator = "Noisestorm";

    // This `expect` attribute will suppress the `unused_variables` lint emission
    // at the variable. The `expect` attribute above the function will still not
    // be fulfilled, since this lint emission has been suppressed by the local
    // expect attribute.
    #[expect(unused_variables)]
    let song_version = "Monstercat Release";
}
[attributes.diagnostics.expect.independent]
If the expect attribute contains several lints, each one is expected separately. For a lint group it’s enough if one lint inside the group has been emitted:
// This expectation will be fulfilled by the unused value inside the function
// since the emitted `unused_variables` lint is inside the `unused` lint group.
#[expect(unused)]
pub fn thoughts() {
    let unused = "I'm running out of examples";
}

pub fn another_example() {
    // This attribute creates two lint expectations. The `unused_mut` lint will be
    // suppressed and with that fulfill the first expectation. The `unused_variables`
    // wouldn't be emitted, since the variable is used. That expectation will therefore
    // be unsatisfied, and a warning will be emitted.
    #[expect(unused_mut, unused_variables)]
    let mut link = "https://www.rust-lang.org/";

    println!("Welcome to our community: {link}");
}
Note

The behavior of #[expect(unfulfilled_lint_expectations)] is currently defined to always generate the unfulfilled_lint_expectations lint.
[attributes.diagnostics.lint.group]
Lint groups
Lints may be organized into named groups so that the level of related lints can be adjusted together. Using a named group is equivalent to listing out the lints within that group.
// This allows all lints in the "unused" group.
#[allow(unused)]
// This overrides the "unused_must_use" lint from the "unused"
// group to deny.
#[deny(unused_must_use)]
fn example() {
    // This does not generate a warning because the "unused_variables"
    // lint is in the "unused" group.
    let x = 1;
    // This generates an error because the result is unused and
    // "unused_must_use" is marked as "deny".
    std::fs::remove_file("some_file"); // ERROR: unused `Result` that must be used
}
[attributes.diagnostics.lint.group.warnings]
There is a special group named “warnings” which includes all lints at the “warn” level. The “warnings” group ignores attribute order and applies to all lints that would otherwise warn within the entity.
// The order of these two attributes does not matter.
#[deny(warnings)]
// The unsafe_code lint is normally "allow" by default.
#[warn(unsafe_code)]
fn example_err() {
    // This is an error because the `unsafe_code` warning has
    // been lifted to "deny".
    unsafe { an_unsafe_fn() } // ERROR: usage of `unsafe` block
}
[attributes.diagnostics.lint.tool]
Tool lint attributes
[attributes.diagnostics.lint.tool.intro]
Tool lints allows using scoped lints, to allow, warn, deny or forbid lints of certain tools.
[attributes.diagnostics.lint.tool.activation]
Tool lints only get checked when the associated tool is active. If a lint attribute, such as allow, references a nonexistent tool lint, the compiler will not warn about the nonexistent lint until you use the tool.
Otherwise, they work just like regular lint attributes:
// set the entire `pedantic` clippy lint group to warn
#![warn(clippy::pedantic)]
// silence warnings from the `filter_map` clippy lint
#![allow(clippy::filter_map)]

fn main() {
    // ...
}

// silence the `cmp_nan` clippy lint just for this function
#[allow(clippy::cmp_nan)]
fn foo() {
    // ...
}
Note

rustc currently recognizes the tool lints for “clippy” and “rustdoc”.
[attributes.diagnostics.deprecated]
The deprecated attribute
[attributes.diagnostics.deprecated.intro]
The deprecated attribute marks an item as deprecated. rustc will issue warnings on usage of #[deprecated] items. rustdoc will show item deprecation, including the since version and note, if available.
[attributes.diagnostics.deprecated.syntax]
The deprecated attribute has several forms:
deprecated — Issues a generic message.
deprecated = "message" — Includes the given string in the deprecation message.
MetaListNameValueStr syntax with two optional fields:
since — Specifies a version number when the item was deprecated. rustc does not currently interpret the string, but external tools like Clippy may check the validity of the value.
note — Specifies a string that should be included in the deprecation message. This is typically used to provide an explanation about the deprecation and preferred alternatives.
[attributes.diagnostic.deprecated.allowed-positions]
The deprecated attribute may be applied to any item, trait item, enum variant, struct field, external block item, or macro definition. It cannot be applied to trait implementation items. When applied to an item containing other items, such as a module or implementation, all child items inherit the deprecation attribute.
Here is an example:
#[deprecated(since = "5.2.0", note = "foo was rarely used. Users should instead use bar")]
pub fn foo() {}

pub fn bar() {}
The RFC contains motivations and more details.
[attributes.diagnostics.must_use]
The must_use attribute
[attributes.diagnostics.must_use.intro]
The must_use attribute is used to issue a diagnostic warning when a value is not “used”.
[attributes.diagnostics.must_use.allowed-positions]
The must_use attribute can be applied to user-defined composite types (structs, enums, and unions), functions, and traits.
[attributes.diagnostics.must_use.message]
The must_use attribute may include a message by using the MetaNameValueStr syntax such as #[must_use = "example message"]. The message will be given alongside the warning.
[attributes.diagnostics.must_use.type]
When used on user-defined composite types, if the expression of an expression statement has that type, then the unused_must_use lint is violated.
#[must_use]
struct MustUse {
    // some fields
}

// Violates the `unused_must_use` lint.
MustUse::new();
[attributes.diagnostics.must_use.fn]
When used on a function, if the expression of an expression statement is a call expression to that function, then the unused_must_use lint is violated.
#[must_use]
fn five() -> i32 { 5i32 }

// Violates the unused_must_use lint.
five();
[attributes.diagnostics.must_use.trait]
When used on a trait declaration, a call expression of an expression statement to a function that returns an impl trait or a dyn trait of that trait violates the unused_must_use lint.
#[must_use]
trait Critical {}
impl Critical for i32 {}

fn get_critical() -> impl Critical {
    4i32
}

// Violates the `unused_must_use` lint.
get_critical();
[attributes.diagnostics.must_use.trait-function]
When used on a function in a trait declaration, then the behavior also applies when the call expression is a function from an implementation of the trait.
trait Trait {
    #[must_use]
    fn use_me(&self) -> i32;
}

impl Trait for i32 {
    fn use_me(&self) -> i32 { 0i32 }
}

// Violates the `unused_must_use` lint.
5i32.use_me();
[attributes.diagnostics.must_use.trait-impl-function]
When used on a function in a trait implementation, the attribute does nothing.
Note

Trivial no-op expressions containing the value will not violate the lint. Examples include wrapping the value in a type that does not implement Drop and then not using that type and being the final expression of a block expression that is not used.

#[must_use]
fn five() -> i32 { 5i32 }

// None of these violate the unused_must_use lint.
(five(),);
Some(five());
{ five() };
if true { five() } else { 0i32 };
match true {
    _ => five()
};
Note

It is idiomatic to use a let statement with a pattern of _ when a must-used value is purposely discarded.

#[must_use]
fn five() -> i32 { 5i32 }

// Does not violate the unused_must_use lint.
let _ = five();
[attributes.diagnostic.namespace]
The diagnostic tool attribute namespace
[attributes.diagnostic.namespace.intro]
The #[diagnostic] attribute namespace is a home for attributes to influence compile-time error messages. The hints provided by these attributes are not guaranteed to be used.
[attributes.diagnostic.namespace.unknown-invalid-syntax]
Tests
Unknown attributes in this namespace are accepted, though they may emit warnings for unused attributes. Additionally, invalid inputs to known attributes will typically be a warning (see the attribute definitions for details). This is meant to allow adding or discarding attributes and changing inputs in the future to allow changes without the need to keep the non-meaningful attributes or options working.
[attributes.diagnostic.on_unimplemented]
The diagnostic::on_unimplemented attribute
[attributes.diagnostic.on_unimplemented.intro]
Tests
The #[diagnostic::on_unimplemented] attribute is a hint to the compiler to supplement the error message that would normally be generated in scenarios where a trait is required but not implemented on a type.
[attributes.diagnostic.on_unimplemented.allowed-positions]
The attribute should be placed on a trait declaration, though it is not an error to be located in other positions.
[attributes.diagnostic.on_unimplemented.syntax]
Tests
The attribute uses the MetaListNameValueStr syntax to specify its inputs, though any malformed input to the attribute is not considered as an error to provide both forwards and backwards compatibility.
[attributes.diagnostic.on_unimplemented.keys]
Tests
The following keys have the given meaning:
message — The text for the top level error message.
label — The text for the label shown inline in the broken code in the error message.
note — Provides additional notes.
[attributes.diagnostic.on_unimplemented.note-repetition]
Tests
The note option can appear several times, which results in several note messages being emitted.
[attributes.diagnostic.on_unimplemented.repetition]
Tests
If any of the other options appears several times the first occurrence of the relevant option specifies the actually used value. Subsequent occurrences generates a warning.
[attributes.diagnostic.on_unimplemented.unknown-keys]
Tests
A warning is generated for any unknown keys.
[attributes.diagnostic.on_unimplemented.format-string]
All three options accept a string as an argument, interpreted using the same formatting as a std::fmt string.
[attributes.diagnostic.on_unimplemented.format-parameters]
Tests
Format parameters with the given named parameter will be replaced with the following text:
{Self} — The name of the type implementing the trait.
{ GenericParameterName } — The name of the generic argument’s type for the given generic parameter.
[attributes.diagnostic.on_unimplemented.invalid-formats]
Tests
Any other format parameter will generate a warning, but will otherwise be included in the string as-is.
[attributes.diagnostic.on_unimplemented.invalid-string]
Tests
Invalid format strings may generate a warning, but are otherwise allowed, but may not display as intended. Format specifiers may generate a warning, but are otherwise ignored.
In this example:
#[diagnostic::on_unimplemented(
    message = "My Message for `ImportantTrait<{A}>` implemented for `{Self}`",
    label = "My Label",
    note = "Note 1",
    note = "Note 2"
)]
trait ImportantTrait<A> {}

fn use_my_trait(_: impl ImportantTrait<i32>) {}

fn main() {
    use_my_trait(String::new());
}
the compiler may generate an error message which looks like this:
error[E0277]: My Message for `ImportantTrait<i32>` implemented for `String`
  --> src/main.rs:14:18
   |
14 |     use_my_trait(String::new());
   |     ------------ ^^^^^^^^^^^^^ My Label
   |     |
   |     required by a bound introduced by this call
   |
   = help: the trait `ImportantTrait<i32>` is not implemented for `String`
   = note: Note 1
   = note: Note 2
[attributes.diagnostic.do_not_recommend]
The diagnostic::do_not_recommend attribute
[attributes.diagnostic.do_not_recommend.intro]
Tests
The #[diagnostic::do_not_recommend] attribute is a hint to the compiler to not show the annotated trait implementation as part of a diagnostic message.
Note

Suppressing the recommendation can be useful if you know that the recommendation would normally not be useful to the programmer. This often occurs with broad, blanket impls. The recommendation may send the programmer down the wrong path, or the trait implementation may be an internal detail that you don’t want to expose, or the bounds may not be able to be satisfied by the programmer.

For example, in an error message about a type not implementing a required trait, the compiler may find a trait implementation that would satisfy the requirements if it weren’t for specific bounds in the trait implementation. The compiler may tell the user that there is an impl, but the problem is the bounds in the trait implementation. The #[diagnostic::do_not_recommend] attribute can be used to tell the compiler to not tell the user about the trait implementation, and instead simply tell the user the type doesn’t implement the required trait.
[attributes.diagnostic.do_not_recommend.allowed-positions]
Tests
The attribute should be placed on a trait implementation item, though it is not an error to be located in other positions.
[attributes.diagnostic.do_not_recommend.syntax]
Tests
The attribute does not accept any arguments, though unexpected arguments are not considered as an error.
In the following example, there is a trait called AsExpression which is used for casting arbitrary types to the Expression type used in an SQL library. There is a method called check which takes an AsExpression.

// Uncomment this line to change the recommendation.
// #[diagnostic::do_not_recommend]
impl<T, ST> AsExpression<ST> for T
where
    T: Expression<SqlType = ST>,
{
    type Expression = T;
}

trait Foo: Expression + Sized {
    fn check<T>(&self, _: T) -> <T as AsExpression<<Self as Expression>::SqlType>>::Expression
    where
        T: AsExpression<Self::SqlType>,
    {
        todo!()
    }
}

fn main() {
    SelectInt.check("bar");
}
The SelectInt type’s check method is expecting an Integer type. Calling it with an i32 type works, as it gets converted to an Integer by the AsExpression trait. However, calling it with a string does not, and generates a an error that may look like this:
error[E0277]: the trait bound `&str: Expression` is not satisfied
  --> src/main.rs:53:15
   |
53 |     SelectInt.check("bar");
   |               ^^^^^ the trait `Expression` is not implemented for `&str`
   |
   = help: the following other types implement trait `Expression`:
             Bound<T>
             SelectInt
note: required for `&str` to implement `AsExpression<Integer>`
  --> src/main.rs:45:13
   |
45 | impl<T, ST> AsExpression<ST> for T
   |             ^^^^^^^^^^^^^^^^     ^
46 | where
47 |     T: Expression<SqlType = ST>,
   |        ------------------------ unsatisfied trait bound introduced here
By adding the #[diagnostic::do_not_recommend] attribute to the blanket impl for AsExpression, the message changes to:
error[E0277]: the trait bound `&str: AsExpression<Integer>` is not satisfied
  --> src/main.rs:53:15
   |
53 |     SelectInt.check("bar");
   |               ^^^^^ the trait `AsExpression<Integer>` is not implemented for `&str`
   |
   = help: the trait `AsExpression<Integer>` is not implemented for `&str`
           but trait `AsExpression<Text>` is implemented for it
   = help: for that trait implementation, expected `Text`, found `Integer`
The first error message includes a somewhat confusing error message about the relationship of &str and Expression, as well as the unsatisfied trait bound in the blanket impl. After adding #[diagnostic::do_not_recommend], it no longer considers the blanket impl for the recommendation. The message should be a little clearer, with an indication that a string cannot be converted to an Integer.
[attributes.codegen]
Code generation attributes

The following attributes are used for controlling code generation.
[attributes.codegen.inline]
The inline attribute
[attributes.codegen.inline.intro]
The inline attribute suggests whether a copy of the attributed function’s code should be placed in the caller rather than generating a call to the function.
Example

#[inline]
pub fn example1() {}

#[inline(always)]
pub fn example2() {}

#[inline(never)]
pub fn example3() {}
Note

rustc automatically inlines functions when doing so seems worthwhile. Use this attribute carefully as poor decisions about what to inline can slow down programs.
[attributes.codegen.inline.syntax]
The syntax for the inline attribute is:
Syntax
InlineAttribute →
      inline ( always )
    | inline ( never )
    | inline

Show syntax diagrams

[attributes.codegen.inline.allowed-positions]
The inline attribute may only be applied to functions with bodies — closures, async blocks, free functions, associated functions in an inherent impl or trait impl, and associated functions in a trait definition when those functions have a default definition .
Note

rustc ignores use in other positions but lints against it. This may become an error in the future.
Note

Though the attribute can be applied to closures and async blocks, the usefulness of this is limited as we do not yet support attributes on expressions.

// We allow attributes on statements.
#[inline] || (); // OK
#[inline] async {}; // OK
// We don't yet allow attributes on expressions.
let f = #[inline] || (); // ERROR
[attributes.codegen.inline.duplicates]
Only the first use of inline on a function has effect.
Note

rustc lints against any use following the first. This may become an error in the future.
[attributes.codegen.inline.modes]
The inline attribute supports these modes:
#[inline] suggests performing inline expansion.
#[inline(always)] suggests that inline expansion should always be performed.
#[inline(never)] suggests that inline expansion should never be performed.
Note

In every form the attribute is a hint. The compiler may ignore it.
[attributes.codegen.inline.trait]
When inline is applied to a function in a trait, it applies only to the code of the default definition.
[attributes.codegen.inline.async]
When inline is applied to an async function or async closure, it applies only to the code of the generated poll function.
Note

For more details, see Rust issue #129347.
[attributes.codegen.inline.externally-exported]
The inline attribute is ignored if the function is externally exported with no_mangle or export_name.
[attributes.codegen.cold]
The cold attribute
[attributes.codegen.cold.intro]
The cold attribute suggests that the attributed function is unlikely to be called which may help the compiler produce better code.
Example

#[cold]
pub fn example() {}
[attributes.codegen.cold.syntax]
The cold attribute uses the MetaWord syntax.
[attributes.codegen.cold.allowed-positions]
The cold attribute may only be applied to functions with bodies — closures, async blocks, free functions, associated functions in an inherent impl or trait impl, and associated functions in a trait definition when those functions have a default definition .
Note

rustc ignores use in other positions but lints against it. This may become an error in the future.
Note

Though the attribute can be applied to closures and async blocks, the usefulness of this is limited as we do not yet support attributes on expressions.
[attributes.codegen.cold.duplicates]
Only the first use of cold on a function has effect.
Note

rustc lints against any use following the first. This may become an error in the future.
[attributes.codegen.cold.trait]
When cold is applied to a function in a trait, it applies only to the code of the default definition.
[attributes.codegen.naked]
The naked attribute
[attributes.codegen.naked.intro]
The naked attribute prevents the compiler from emitting a function prologue and epilogue for the attributed function.
[attributes.codegen.naked.body]
The function body must consist of exactly one naked_asm! macro invocation.
[attributes.codegen.naked.prologue-epilogue]
No function prologue or epilogue is generated for the attributed function. The assembly code in the naked_asm! block constitutes the full body of a naked function.
[attributes.codegen.naked.unsafe-attribute]
The naked attribute is an unsafe attribute. Annotating a function with #[unsafe(naked)] comes with the safety obligation that the body must respect the function’s calling convention, uphold its signature, and either return or diverge (i.e., not fall through past the end of the assembly code).
[attributes.codegen.naked.call-stack]
The assembly code may assume that the call stack and register state are valid on entry as per the signature and calling convention of the function.
[attributes.codegen.naked.no-duplication]
The assembly code may not be duplicated by the compiler except when monomorphizing polymorphic functions.
Note

Guaranteeing when the assembly code may or may not be duplicated is important for naked functions that define symbols.
[attributes.codegen.naked.unused-variables]
The unused_variables lint is suppressed within naked functions.
[attributes.codegen.naked.inline]
The inline attribute cannot by applied to a naked function.
[attributes.codegen.naked.track_caller]
The track_caller attribute cannot be applied to a naked function.
[attributes.codegen.naked.testing]
The testing attributes cannot be applied to a naked function.
[attributes.codegen.no_builtins]
The no_builtins attribute
[attributes.codegen.no_builtins.intro]
The no_builtins attribute disables optimization of certain code patterns related to calls to library functions that are assumed to exist.
Example

#![no_builtins]
[attributes.codegen.no_builtins.syntax]
The no_builtins attribute uses the MetaWord syntax.
[attributes.codegen.no_builtins.allowed-positions]
The no_builtins attribute can only be applied to the crate root.
[attributes.codegen.no_builtins.duplicates]
Only the first use of the no_builtins attribute has effect.
Note

rustc lints against any use following the first.
[attributes.codegen.target_feature]
The target_feature attribute
[attributes.codegen.target_feature.intro]
The target_feature attribute may be applied to a function to enable code generation of that function for specific platform architecture features. It uses the MetaListNameValueStr syntax with a single key of enable whose value is a string of comma-separated feature names to enable.
#[target_feature(enable = "avx2")]
fn foo_avx2() {}
[attributes.codegen.target_feature.arch]
Each target architecture has a set of features that may be enabled. It is an error to specify a feature for a target architecture that the crate is not being compiled for.
[attributes.codegen.target_feature.closures]
Closures defined within a target_feature-annotated function inherit the attribute from the enclosing function.
[attributes.codegen.target_feature.target-ub]
It is undefined behavior to call a function that is compiled with a feature that is not supported on the current platform the code is running on, except if the platform explicitly documents this to be safe.
[attributes.codegen.target_feature.safety-restrictions]
The following restrictions apply unless otherwise specified by the platform rules below:
Safe #[target_feature] functions (and closures that inherit the attribute) can only be safely called within a caller that enables all the target_features that the callee enables. This restriction does not apply in an unsafe context.
Safe #[target_feature] functions (and closures that inherit the attribute) can only be coerced to safe function pointers in contexts that enable all the target_features that the coercee enables. This restriction does not apply to unsafe function pointers.
Implicitly enabled features are included in this rule. For example an sse2 function can call ones marked with sse.
#[target_feature(enable = "sse")]
fn foo_sse() {}

fn bar() {
    // Calling `foo_sse` here is unsafe, as we must ensure that SSE is
    // available first, even if `sse` is enabled by default on the target
    // platform or manually enabled as compiler flags.
    unsafe {
        foo_sse();
    }
}

#[target_feature(enable = "sse")]
fn bar_sse() {
    // Calling `foo_sse` here is safe.
    foo_sse();
    || foo_sse();
}

#[target_feature(enable = "sse2")]
fn bar_sse2() {
    // Calling `foo_sse` here is safe because `sse2` implies `sse`.
    foo_sse();
}
[attributes.codegen.target_feature.fn-traits]
A function with a #[target_feature] attribute never implements the Fn family of traits, although closures inheriting features from the enclosing function do.
[attributes.codegen.target_feature.allowed-positions]
The #[target_feature] attribute is not allowed on the following places:
the main function
a panic_handler function
safe trait methods
safe default functions in traits
[attributes.codegen.target_feature.inline]
Functions marked with target_feature are not inlined into a context that does not support the given features. The #[inline(always)] attribute may not be used with a target_feature attribute.
[attributes.codegen.target_feature.availability]
Available features
The following is a list of the available feature names.
[attributes.codegen.target_feature.x86]
x86 or x86_64
Executing code with unsupported features is undefined behavior on this platform. Hence on this platform usage of #[target_feature] functions follows the above restrictions.
Feature	Implicitly Enables	Description
adx		ADX — Multi-Precision Add-Carry Instruction Extensions
aes	sse2	AES — Advanced Encryption Standard
avx	sse4.2	AVX — Advanced Vector Extensions
avx2	avx	AVX2 — Advanced Vector Extensions 2
avx512bf16	avx512bw	AVX512-BF16 — Advanced Vector Extensions 512-bit - Bfloat16 Extensions
avx512bitalg	avx512bw	AVX512-BITALG — Advanced Vector Extensions 512-bit - Bit Algorithms
avx512bw	avx512f	AVX512-BW — Advanced Vector Extensions 512-bit - Byte and Word Instructions
avx512cd	avx512f	AVX512-CD — Advanced Vector Extensions 512-bit - Conflict Detection Instructions
avx512dq	avx512f	AVX512-DQ — Advanced Vector Extensions 512-bit - Doubleword and Quadword Instructions
avx512f	avx2, fma, f16c	AVX512-F — Advanced Vector Extensions 512-bit - Foundation
avx512fp16	avx512bw	AVX512-FP16 — Advanced Vector Extensions 512-bit - Float16 Extensions
avx512ifma	avx512f	AVX512-IFMA — Advanced Vector Extensions 512-bit - Integer Fused Multiply Add
avx512vbmi	avx512bw	AVX512-VBMI — Advanced Vector Extensions 512-bit - Vector Byte Manipulation Instructions
avx512vbmi2	avx512bw	AVX512-VBMI2 — Advanced Vector Extensions 512-bit - Vector Byte Manipulation Instructions 2
avx512vl	avx512f	AVX512-VL — Advanced Vector Extensions 512-bit - Vector Length Extensions
avx512vnni	avx512f	AVX512-VNNI — Advanced Vector Extensions 512-bit - Vector Neural Network Instructions
avx512vp2intersect	avx512f	AVX512-VP2INTERSECT — Advanced Vector Extensions 512-bit - Vector Pair Intersection to a Pair of Mask Registers
avx512vpopcntdq	avx512f	AVX512-VPOPCNTDQ — Advanced Vector Extensions 512-bit - Vector Population Count Instruction
avxifma	avx2	AVX-IFMA — Advanced Vector Extensions - Integer Fused Multiply Add
avxneconvert	avx2	AVX-NE-CONVERT — Advanced Vector Extensions - No-Exception Floating-Point conversion Instructions
avxvnni	avx2	AVX-VNNI — Advanced Vector Extensions - Vector Neural Network Instructions
avxvnniint16	avx2	AVX-VNNI-INT16 — Advanced Vector Extensions - Vector Neural Network Instructions with 16-bit Integers
avxvnniint8	avx2	AVX-VNNI-INT8 — Advanced Vector Extensions - Vector Neural Network Instructions with 8-bit Integers
bmi1		BMI1 — Bit Manipulation Instruction Sets
bmi2		BMI2 — Bit Manipulation Instruction Sets 2
cmpxchg16b		cmpxchg16b — Compares and exchange 16 bytes (128 bits) of data atomically
f16c	avx	F16C — 16-bit floating point conversion instructions
fma	avx	FMA3 — Three-operand fused multiply-add
fxsr		fxsave and fxrstor — Save and restore x87 FPU, MMX Technology, and SSE State
gfni	sse2	GFNI — Galois Field New Instructions
kl	sse2	KEYLOCKER — Intel Key Locker Instructions
lzcnt		lzcnt — Leading zeros count
movbe		movbe — Move data after swapping bytes
pclmulqdq	sse2	pclmulqdq — Packed carry-less multiplication quadword
popcnt		popcnt — Count of bits set to 1
rdrand		rdrand — Read random number
rdseed		rdseed — Read random seed
sha	sse2	SHA — Secure Hash Algorithm
sha512	avx2	SHA512 — Secure Hash Algorithm with 512-bit digest
sm3	avx	SM3 — ShangMi 3 Hash Algorithm
sm4	avx2	SM4 — ShangMi 4 Cipher Algorithm
sse		SSE — Streaming SIMD Extensions
sse2	sse	SSE2 — Streaming SIMD Extensions 2
sse3	sse2	SSE3 — Streaming SIMD Extensions 3
sse4.1	ssse3	SSE4.1 — Streaming SIMD Extensions 4.1
sse4.2	sse4.1	SSE4.2 — Streaming SIMD Extensions 4.2
sse4a	sse3	SSE4a — Streaming SIMD Extensions 4a
ssse3	sse3	SSSE3 — Supplemental Streaming SIMD Extensions 3
tbm		TBM — Trailing Bit Manipulation
vaes	avx2, aes	VAES — Vector AES Instructions
vpclmulqdq	avx, pclmulqdq	VPCLMULQDQ — Vector Carry-less multiplication of Quadwords
widekl	kl	KEYLOCKER_WIDE — Intel Wide Keylocker Instructions
xsave		xsave — Save processor extended states
xsavec		xsavec — Save processor extended states with compaction
xsaveopt		xsaveopt — Save processor extended states optimized
xsaves		xsaves — Save processor extended states supervisor
[attributes.codegen.target_feature.aarch64]
aarch64
On this platform the usage of #[target_feature] functions follows the above restrictions.
Further documentation on these features can be found in the ARM Architecture Reference Manual, or elsewhere on developer.arm.com.
Note

The following pairs of features should both be marked as enabled or disabled together if used:

paca and pacg, which LLVM currently implements as one feature.
Feature	Implicitly Enables	Feature Name
aes	neon	FEAT_AES & FEAT_PMULL — Advanced SIMD AES & PMULL instructions
bf16		FEAT_BF16 — BFloat16 instructions
bti		FEAT_BTI — Branch Target Identification
crc		FEAT_CRC — CRC32 checksum instructions
dit		FEAT_DIT — Data Independent Timing instructions
dotprod	neon	FEAT_DotProd — Advanced SIMD Int8 dot product instructions
dpb		FEAT_DPB — Data cache clean to point of persistence
dpb2	dpb	FEAT_DPB2 — Data cache clean to point of deep persistence
f32mm	sve	FEAT_F32MM — SVE single-precision FP matrix multiply instruction
f64mm	sve	FEAT_F64MM — SVE double-precision FP matrix multiply instruction
fcma	neon	FEAT_FCMA — Floating point complex number support
fhm	fp16	FEAT_FHM — Half-precision FP FMLAL instructions
flagm		FEAT_FLAGM — Conditional flag manipulation
fp16	neon	FEAT_FP16 — Half-precision FP data processing
frintts		FEAT_FRINTTS — Floating-point to int helper instructions
i8mm		FEAT_I8MM — Int8 Matrix Multiplication
jsconv	neon	FEAT_JSCVT — JavaScript conversion instruction
lor		FEAT_LOR — Limited Ordering Regions extension
lse		FEAT_LSE — Large System Extensions
mte		FEAT_MTE & FEAT_MTE2 — Memory Tagging Extension
neon		FEAT_AdvSimd & FEAT_FP — Floating Point and Advanced SIMD extension
paca		FEAT_PAUTH — Pointer Authentication (address authentication)
pacg		FEAT_PAUTH — Pointer Authentication (generic authentication)
pan		FEAT_PAN — Privileged Access-Never extension
pmuv3		FEAT_PMUv3 — Performance Monitors extension (v3)
rand		FEAT_RNG — Random Number Generator
ras		FEAT_RAS & FEAT_RASv1p1 — Reliability, Availability and Serviceability extension
rcpc		FEAT_LRCPC — Release consistent Processor Consistent
rcpc2	rcpc	FEAT_LRCPC2 — RcPc with immediate offsets
rdm	neon	FEAT_RDM — Rounding Double Multiply accumulate
sb		FEAT_SB — Speculation Barrier
sha2	neon	FEAT_SHA1 & FEAT_SHA256 — Advanced SIMD SHA instructions
sha3	sha2	FEAT_SHA512 & FEAT_SHA3 — Advanced SIMD SHA instructions
sm4	neon	FEAT_SM3 & FEAT_SM4 — Advanced SIMD SM3/4 instructions
spe		FEAT_SPE — Statistical Profiling Extension
ssbs		FEAT_SSBS & FEAT_SSBS2 — Speculative Store Bypass Safe
sve	neon	FEAT_SVE — Scalable Vector Extension
sve2	sve	FEAT_SVE2 — Scalable Vector Extension 2
sve2-aes	sve2, aes	FEAT_SVE_AES & FEAT_SVE_PMULL128 — SVE AES instructions
sve2-bitperm	sve2	FEAT_SVE2_BitPerm — SVE Bit Permute
sve2-sha3	sve2, sha3	FEAT_SVE2_SHA3 — SVE SHA3 instructions
sve2-sm4	sve2, sm4	FEAT_SVE2_SM4 — SVE SM4 instructions
tme		FEAT_TME — Transactional Memory Extension
vh		FEAT_VHE — Virtualization Host Extensions
[attributes.codegen.target_feature.loongarch]
loongarch
On this platform the usage of #[target_feature] functions follows the above restrictions.
Feature	Implicitly Enables	Description
f		F — Single-precision float-point instructions
d	f	D — Double-precision float-point instructions
frecipe		FRECIPE — Reciprocal approximation instructions
lasx	lsx	LASX — 256-bit vector instructions
lbt		LBT — Binary translation instructions
lsx	d	LSX — 128-bit vector instructions
lvz		LVZ — Virtualization instructions
[attributes.codegen.target_feature.riscv]
riscv32 or riscv64
On this platform the usage of #[target_feature] functions follows the above restrictions.
Further documentation on these features can be found in their respective specification. Many specifications are described in the RISC-V ISA Manual or in another manual hosted on the RISC-V GitHub Account.
Feature	Implicitly Enables	Description
a		A — Atomic instructions
c		C — Compressed instructions
m		M — Integer Multiplication and Division instructions
zb	zba, zbc, zbs	Zb — Bit Manipulation instructions
zba		Zba — Address Generation instructions
zbb		Zbb — Basic bit-manipulation
zbc		Zbc — Carry-less multiplication
zbkb		Zbkb — Bit Manipulation Instructions for Cryptography
zbkc		Zbkc — Carry-less multiplication for Cryptography
zbkx		Zbkx — Crossbar permutations
zbs		Zbs — Single-bit instructions
zk	zkn, zkr, zks, zkt, zbkb, zbkc, zkbx	Zk — Scalar Cryptography
zkn	zknd, zkne, zknh, zbkb, zbkc, zkbx	Zkn — NIST Algorithm suite extension
zknd		Zknd — NIST Suite: AES Decryption
zkne		Zkne — NIST Suite: AES Encryption
zknh		Zknh — NIST Suite: Hash Function Instructions
zkr		Zkr — Entropy Source Extension
zks	zksed, zksh, zbkb, zbkc, zkbx	Zks — ShangMi Algorithm Suite
zksed		Zksed — ShangMi Suite: SM4 Block Cipher Instructions
zksh		Zksh — ShangMi Suite: SM3 Hash Function Instructions
zkt		Zkt — Data Independent Execution Latency Subset
[attributes.codegen.target_feature.wasm]
wasm32 or wasm64
Safe #[target_feature] functions may always be used in safe contexts on Wasm platforms. It is impossible to cause undefined behavior via the #[target_feature] attribute because attempting to use instructions unsupported by the Wasm engine will fail at load time without the risk of being interpreted in a way different from what the compiler expected.
Feature	Implicitly Enables	Description
bulk-memory		WebAssembly bulk memory operations proposal
extended-const		WebAssembly extended const expressions proposal
mutable-globals		WebAssembly mutable global proposal
nontrapping-fptoint		WebAssembly non-trapping float-to-int conversion proposal
relaxed-simd	simd128	WebAssembly relaxed simd proposal
sign-ext		WebAssembly sign extension operators Proposal
simd128		WebAssembly simd proposal
multivalue		WebAssembly multivalue proposal
reference-types		WebAssembly reference-types proposal
tail-call		WebAssembly tail-call proposal
[attributes.codegen.target_feature.info]
Additional information
[attributes.codegen.target_feature.remark-cfg]
See the target_feature conditional compilation option for selectively enabling or disabling compilation of code based on compile-time settings. Note that this option is not affected by the target_feature attribute, and is only driven by the features enabled for the entire crate.
[attributes.codegen.target_feature.remark-rt]
See the is_x86_feature_detected or is_aarch64_feature_detected macros in the standard library for runtime feature detection on these platforms.
Note

rustc has a default set of features enabled for each target and CPU. The CPU may be chosen with the -C target-cpu flag. Individual features may be enabled or disabled for an entire crate with the -C target-feature flag.
[attributes.codegen.track_caller]
The track_caller attribute
[attributes.codegen.track_caller.allowed-positions]
The track_caller attribute may be applied to any function with "Rust" ABI with the exception of the entry point fn main.
[attributes.codegen.track_caller.traits]
When applied to functions and methods in trait declarations, the attribute applies to all implementations. If the trait provides a default implementation with the attribute, then the attribute also applies to override implementations.
[attributes.codegen.track_caller.extern]
When applied to a function in an extern block the attribute must also be applied to any linked implementations, otherwise undefined behavior results. When applied to a function which is made available to an extern block, the declaration in the extern block must also have the attribute, otherwise undefined behavior results.
[attributes.codegen.track_caller.behavior]
Behavior
Applying the attribute to a function f allows code within f to get a hint of the Location of the “topmost” tracked call that led to f’s invocation. At the point of observation, an implementation behaves as if it walks up the stack from f’s frame to find the nearest frame of an unattributed function outer, and it returns the Location of the tracked call in outer.
#[track_caller]
fn f() {
    println!("{}", std::panic::Location::caller());
}
Note

core provides core::panic::Location::caller for observing caller locations. It wraps the core::intrinsics::caller_location intrinsic implemented by rustc.
Note

Because the resulting Location is a hint, an implementation may halt its walk up the stack early. See Limitations for important caveats.
Examples
When f is called directly by calls_f, code in f observes its callsite within calls_f:
fn calls_f() {
    f(); // <-- f() prints this location
}
When f is called by another attributed function g which is in turn called by calls_g, code in both f and g observes g’s callsite within calls_g:
#[track_caller]
fn g() {
    println!("{}", std::panic::Location::caller());
    f();
}

fn calls_g() {
    g(); // <-- g() prints this location twice, once itself and once from f()
}
When g is called by another attributed function h which is in turn called by calls_h, all code in f, g, and h observes h’s callsite within calls_h:
#[track_caller]
fn h() {
    println!("{}", std::panic::Location::caller());
    g();
}

fn calls_h() {
    h(); // <-- prints this location three times, once itself, once from g(), once from f()
}
And so on.
[attributes.codegen.track_caller.limits]
Limitations
[attributes.codegen.track_caller.hint]
This information is a hint and implementations are not required to preserve it.
[attributes.codegen.track_caller.decay]
In particular, coercing a function with #[track_caller] to a function pointer creates a shim which appears to observers to have been called at the attributed function’s definition site, losing actual caller information across virtual calls. A common example of this coercion is the creation of a trait object whose methods are attributed.
Note

The aforementioned shim for function pointers is necessary because rustc implements track_caller in a codegen context by appending an implicit parameter to the function ABI, but this would be unsound for an indirect call because the parameter is not a part of the function’s type and a given function pointer type may or may not refer to a function with the attribute. The creation of a shim hides the implicit parameter from callers of the function pointer, preserving soundness.
[attributes.codegen.instruction_set]
The instruction_set attribute
[attributes.codegen.instruction_set.intro]
The instruction_set attribute specifies the instruction set that a function will use during code generation. This allows mixing more than one instruction set in a single program.
Example

#[instruction_set(arm::a32)]
fn arm_code() {}

#[instruction_set(arm::t32)]
fn thumb_code() {}
[attributes.codegen.instruction_set.syntax]
The instruction_set attribute uses the MetaListPaths syntax to specify a single path consisting of the architecture family name and instruction set name.
[attributes.codegen.instruction_set.allowed-positions]
The instruction_set attribute may only be applied to functions with bodies — closures, async blocks, free functions, associated functions in an inherent impl or trait impl, and associated functions in a trait definition when those functions have a default definition .
Note

rustc ignores use in other positions but lints against it. This may become an error in the future.
Note

Though the attribute can be applied to closures and async blocks, the usefulness of this is limited as we do not yet support attributes on expressions.
[attributes.codegen.instruction_set.duplicates]
The instruction_set attribute may be used only once on a function.
[attributes.codegen.instruction_set.target-limits]
The instruction_set attribute may only be used with a target that supports the given value.
[attributes.codegen.instruction_set.inline-asm]
When the instruction_set attribute is used, any inline assembly in the function must use the specified instruction set instead of the target default.
[attributes.codegen.instruction_set.arm]
instruction_set on ARM
When targeting the ARMv4T and ARMv5te architectures, the supported values for instruction_set are:
arm::a32 — Generate the function as A32 “ARM” code.
arm::t32 — Generate the function as T32 “Thumb” code.
If the address of the function is taken as a function pointer, the low bit of the address will depend on the selected instruction set:
For arm::a32 (“ARM”), it will be 0.
For arm::t32 (“Thumb”), it will be 1.
[attributes.limits]
Limits

The following attributes affect compile-time limits.
[attributes.limits.recursion_limit]
The recursion_limit attribute
[attributes.limits.recursion_limit.intro]
The recursion_limit attribute may be applied at the crate level to set the maximum depth for potentially infinitely-recursive compile-time operations like macro expansion or auto-dereference.
[attributes.limits.recursion_limit.syntax]
It uses the MetaNameValueStr syntax to specify the recursion depth.
Note

The default in rustc is 128.
#![recursion_limit = "4"]

macro_rules! a {
    () => { a!(1); };
    (1) => { a!(2); };
    (2) => { a!(3); };
    (3) => { a!(4); };
    (4) => { };
}

// This fails to expand because it requires a recursion depth greater than 4.
a!{}
#![recursion_limit = "1"]

// This fails because it requires two recursive steps to auto-dereference.
(|_: &u8| {})(&&&1);
[attributes.limits.type_length_limit]
The type_length_limit attribute
[attributes.limits.type_length_limit.intro]
The type_length_limit attribute sets the maximum number of type substitutions allowed when constructing a concrete type during monomorphization.
Note

rustc only enforces the limit when the nightly -Zenforce-type-length-limit flag is active.

For more information, see Rust PR #127670.
Example

#![type_length_limit = "4"]

fn f<T>(x: T) {}

// This fails to compile because monomorphizing to
// `f::<((((i32,), i32), i32), i32)>` requires more
// than 4 type elements.
f(((((1,), 2), 3), 4));
Note

The default value in rustc is 1048576.
[attributes.limits.type_length_limit.syntax]
The type_length_limit attribute uses the MetaNameValueStr syntax. The value in the string must be a non-negative number.
[attributes.limits.type_length_limit.allowed-positions]
The type_length_limit attribute may only be applied to the crate root.
Note

rustc ignores use in other positions but lints against it. This may become an error in the future.
[attributes.limits.type_length_limit.duplicates]
Only the first use of type_length_limit on an item has effect.
Note

rustc lints against any use following the first. This may become an error in the future.
[attributes.type-system]
Type system attributes

The following attributes are used for changing how a type can be used.
[attributes.type-system.non_exhaustive]
The non_exhaustive attribute
[attributes.type-system.non_exhaustive.intro]
The non_exhaustive attribute indicates that a type or variant may have more fields or variants added in the future.
[attributes.type-system.non_exhaustive.allowed-positions]
It can be applied to structs, enums, and enum variants.
[attributes.type-system.non_exhaustive.syntax]
The non_exhaustive attribute uses the MetaWord syntax and thus does not take any inputs.
[attributes.type-system.non_exhaustive.same-crate]
Within the defining crate, non_exhaustive has no effect.
#[non_exhaustive]
pub struct Config {
    pub window_width: u16,
    pub window_height: u16,
}

#[non_exhaustive]
pub struct Token;

#[non_exhaustive]
pub struct Id(pub u64);

#[non_exhaustive]
pub enum Error {
    Message(String),
    Other,
}

pub enum Message {
    #[non_exhaustive] Send { from: u32, to: u32, contents: String },
    #[non_exhaustive] Reaction(u32),
    #[non_exhaustive] Quit,
}

// Non-exhaustive structs can be constructed as normal within the defining crate.
let config = Config { window_width: 640, window_height: 480 };
let token = Token;
let id = Id(4);

// Non-exhaustive structs can be matched on exhaustively within the defining crate.
let Config { window_width, window_height } = config;
let Token = token;
let Id(id_number) = id;

let error = Error::Other;
let message = Message::Reaction(3);

// Non-exhaustive enums can be matched on exhaustively within the defining crate.
match error {
    Error::Message(ref s) => { },
    Error::Other => { },
}

match message {
    // Non-exhaustive variants can be matched on exhaustively within the defining crate.
    Message::Send { from, to, contents } => { },
    Message::Reaction(id) => { },
    Message::Quit => { },
}
[attributes.type-system.non_exhaustive.external-crate]
Outside of the defining crate, types annotated with non_exhaustive have limitations that preserve backwards compatibility when new fields or variants are added.
[attributes.type-system.non_exhaustive.construction]
Non-exhaustive types cannot be constructed outside of the defining crate:
Non-exhaustive variants (struct or enum variant) cannot be constructed with a StructExpression (including with functional update syntax).
The implicitly defined same-named constant of a unit-like struct, or the same-named constructor function of a tuple struct, has a visibility no greater than pub(crate). That is, if the struct’s visibility is pub, then the constant or constructor’s visibility is pub(crate), and otherwise the visibility of the two items is the same (as is the case without #[non_exhaustive]).
enum instances can be constructed.
The following examples of construction do not compile when outside the defining crate:
// These are types defined in an upstream crate that have been annotated as
// `#[non_exhaustive]`.
use upstream::{Config, Token, Id, Error, Message};

// Cannot construct an instance of `Config`; if new fields were added in
// a new version of `upstream` then this would fail to compile, so it is
// disallowed.
let config = Config { window_width: 640, window_height: 480 };

// Cannot construct an instance of `Token`; if new fields were added, then
// it would not be a unit-like struct any more, so the same-named constant
// created by it being a unit-like struct is not public outside the crate;
// this code fails to compile.
let token = Token;

// Cannot construct an instance of `Id`; if new fields were added, then
// its constructor function signature would change, so its constructor
// function is not public outside the crate; this code fails to compile.
let id = Id(5);

// Can construct an instance of `Error`; new variants being introduced would
// not result in this failing to compile.
let error = Error::Message("foo".to_string());

// Cannot construct an instance of `Message::Send` or `Message::Reaction`;
// if new fields were added in a new version of `upstream` then this would
// fail to compile, so it is disallowed.
let message = Message::Send { from: 0, to: 1, contents: "foo".to_string(), };
let message = Message::Reaction(0);

// Cannot construct an instance of `Message::Quit`; if this were converted to
// a tuple-variant `upstream` then this would fail to compile.
let message = Message::Quit;
[attributes.type-system.non_exhaustive.match]
There are limitations when matching on non-exhaustive types outside of the defining crate:
When pattern matching on a non-exhaustive variant (struct or enum variant), a StructPattern must be used which must include a ... A tuple variant’s constructor’s visibility is reduced to be no greater than pub(crate).
When pattern matching on a non-exhaustive enum, matching on a variant does not contribute towards the exhaustiveness of the arms.
The following examples of matching do not compile when outside the defining crate:
// These are types defined in an upstream crate that have been annotated as
// `#[non_exhaustive]`.
use upstream::{Config, Token, Id, Error, Message};

// Cannot match on a non-exhaustive enum without including a wildcard arm.
match error {
  Error::Message(ref s) => { },
  Error::Other => { },
  // would compile with: `_ => {},`
}

// Cannot match on a non-exhaustive struct without a wildcard.
if let Ok(Config { window_width, window_height }) = config {
    // would compile with: `..`
}

// Cannot match a non-exhaustive unit-like or tuple struct except by using
// braced struct syntax with a wildcard.
// This would compile as `let Token { .. } = token;`
let Token = token;
// This would compile as `let Id { 0: id_number, .. } = id;`
let Id(id_number) = id;

match message {
  // Cannot match on a non-exhaustive struct enum variant without including a wildcard.
  Message::Send { from, to, contents } => { },
  // Cannot match on a non-exhaustive tuple or unit enum variant.
  Message::Reaction(type) => { },
  Message::Quit => { },
}
It’s also not allowed to use numeric casts (as) on enums that contain any non-exhaustive variants.
For example, the following enum can be cast because it doesn’t contain any non-exhaustive variants:
#[non_exhaustive]
pub enum Example {
    First,
    Second
}
However, if the enum contains even a single non-exhaustive variant, casting will result in an error. Consider this modified version of the same enum:
#[non_exhaustive]
pub enum EnumWithNonExhaustiveVariants {
    First,
    #[non_exhaustive]
    Second
}
use othercrate::EnumWithNonExhaustiveVariants;

// Error: cannot cast an enum with a non-exhaustive variant when it's defined in another crate
let _ = EnumWithNonExhaustiveVariants::First as u8;
Non-exhaustive types are always considered inhabited in downstream crates.
[attributes.debugger]
Debugger attributes

The following attributes are used for enhancing the debugging experience when using third-party debuggers like GDB or WinDbg.
[attributes.debugger.debugger_visualizer]
The debugger_visualizer attribute
[attributes.debugger.debugger_visualizer.intro]
The debugger_visualizer attribute can be used to embed a debugger visualizer file into the debug information. This improves the debugger experience when displaying values.
Example

#![debugger_visualizer(natvis_file = "Example.natvis")]
#![debugger_visualizer(gdb_script_file = "example.py")]
[attributes.debugger.debugger_visualizer.syntax]
The debugger_visualizer attribute uses the MetaListNameValueStr syntax to specify its inputs. One of the following keys must be specified:
natvis_file
gdb_script_file
[attributes.debugger.debugger_visualizer.allowed-positions]
The debugger_visualizer attribute may only be applied to a module or to the crate root.
[attributes.debugger.debugger_visualizer.duplicates]
The debugger_visualizer attribute may be used any number of times on a form. All specified visualizer files will be loaded.
[attributes.debugger.debugger_visualizer.natvis]
Using debugger_visualizer with Natvis
[attributes.debugger.debugger_visualizer.natvis.intro]
Natvis is an XML-based framework for Microsoft debuggers (such as Visual Studio and WinDbg) that uses declarative rules to customize the display of types. For detailed information on the Natvis format, refer to Microsoft’s Natvis documentation.
[attributes.debugger.debugger_visualizer.natvis.msvc]
This attribute only supports embedding Natvis files on -windows-msvc targets.
[attributes.debugger.debugger_visualizer.natvis.path]
The path to the Natvis file is specified with the natvis_file key, which is a path relative to the source file.
Example

#![debugger_visualizer(natvis_file = "Rectangle.natvis")]

struct FancyRect {
    x: f32,
    y: f32,
    dx: f32,
    dy: f32,
}

fn main() {
    let fancy_rect = FancyRect { x: 10.0, y: 10.0, dx: 5.0, dy: 5.0 };
    println!("set breakpoint here");
}
Rectangle.natvis contains:

<?xml version="1.0" encoding="utf-8"?>
<AutoVisualizer xmlns="http://schemas.microsoft.com/vstudio/debugger/natvis/2010">
    <Type Name="foo::FancyRect">
      <DisplayString>({x},{y}) + ({dx}, {dy})</DisplayString>
      <Expand>
        <Synthetic Name="LowerLeft">
          <DisplayString>({x}, {y})</DisplayString>
        </Synthetic>
        <Synthetic Name="UpperLeft">
          <DisplayString>({x}, {y + dy})</DisplayString>
        </Synthetic>
        <Synthetic Name="UpperRight">
          <DisplayString>({x + dx}, {y + dy})</DisplayString>
        </Synthetic>
        <Synthetic Name="LowerRight">
          <DisplayString>({x + dx}, {y})</DisplayString>
        </Synthetic>
      </Expand>
    </Type>
</AutoVisualizer>
When viewed under WinDbg, the fancy_rect variable would be shown as follows:

> Variables:
  > fancy_rect: (10.0, 10.0) + (5.0, 5.0)
    > LowerLeft: (10.0, 10.0)
    > UpperLeft: (10.0, 15.0)
    > UpperRight: (15.0, 15.0)
    > LowerRight: (15.0, 10.0)
[attributes.debugger.debugger_visualizer.gdb]
Using debugger_visualizer with GDB
[attributes.debugger.debugger_visualizer.gdb.pretty]
GDB supports the use of a structured Python script, called a pretty printer, that describes how a type should be visualized in the debugger view. For detailed information on pretty printers, refer to GDB’s pretty printing documentation.
Note

Embedded pretty printers are not automatically loaded when debugging a binary under GDB.

There are two ways to enable auto-loading embedded pretty printers:

Launch GDB with extra arguments to explicitly add a directory or binary to the auto-load safe path: gdb -iex "add-auto-load-safe-path safe-path path/to/binary" path/to/binary For more information, see GDB’s auto-loading documentation.
Create a file named gdbinit under $HOME/.config/gdb (you may need to create the directory if it doesn’t already exist). Add the following line to that file: add-auto-load-safe-path path/to/binary.
[attributes.debugger.debugger_visualizer.gdb.path]
These scripts are embedded using the gdb_script_file key, which is a path relative to the source file.
Example

#![debugger_visualizer(gdb_script_file = "printer.py")]

struct Person {
    name: String,
    age: i32,
}

fn main() {
    let bob = Person { name: String::from("Bob"), age: 10 };
    println!("set breakpoint here");
}
printer.py contains:

import gdb

class PersonPrinter:
    "Print a Person"

    def __init__(self, val):
        self.val = val
        self.name = val["name"]
        self.age = int(val["age"])

    def to_string(self):
        return "{} is {} years old.".format(self.name, self.age)

def lookup(val):
    lookup_tag = val.type.tag
    if lookup_tag is None:
        return None
    if "foo::Person" == lookup_tag:
        return PersonPrinter(val)

    return None

gdb.current_objfile().pretty_printers.append(lookup)
When the crate’s debug executable is passed into GDB1, print bob will display:

"Bob" is 10 years old.
[attributes.debugger.collapse_debuginfo]
The collapse_debuginfo attribute
[attributes.debugger.collapse_debuginfo.intro]
The collapse_debuginfo attribute controls whether code locations from a macro definition are collapsed into a single location associated with the macro’s call site when generating debuginfo for code calling this macro.
Example

#[collapse_debuginfo(yes)]
macro_rules! example {
    () => {
        println!("hello!");
    };
}
When using a debugger, invoking the example macro may appear as though it is calling a function. That is, when you step to the invocation site, it may show the macro invocation rather than the expanded code.
[attributes.debugger.collapse_debuginfo.syntax]
The syntax for the collapse_debuginfo attribute is:
Syntax
CollapseDebuginfoAttribute → collapse_debuginfo ( CollapseDebuginfoOption )

CollapseDebuginfoOption →
      yes
    | no
    | external

Show syntax diagrams

[attributes.debugger.collapse_debuginfo.allowed-positions]
The collapse_debuginfo attribute may only be applied to a macro_rules definition.
[attributes.debugger.collapse_debuginfo.duplicates]
The collapse_debuginfo attribute may used only once on a macro.
[attributes.debugger.collapse_debuginfo.options]
The collapse_debuginfo attribute accepts these options:
#[collapse_debuginfo(yes)] — Code locations in debuginfo are collapsed.
#[collapse_debuginfo(no)] — Code locations in debuginfo are not collapsed.
#[collapse_debuginfo(external)] — Code locations in debuginfo are collapsed only if the macro comes from a different crate.
[attributes.debugger.collapse_debuginfo.default]
The external behavior is the default for macros that don’t have this attribute unless they are built-in macros. For built-in macros the default is yes.
Note

rustc has a -C collapse-macro-debuginfo CLI option to override both the default behavior and the values of any #[collapse_debuginfo] attributes.
Note: This assumes you are using the rust-gdb script which configures pretty-printers for standard library types like String. ↩

[stmt-expr]
