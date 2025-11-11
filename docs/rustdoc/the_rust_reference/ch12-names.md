# Names
[names.intro]
An entity is a language construct that can be referred to in some way within the source program, usually via a path. Entities include types, items, generic parameters, variable bindings, loop labels, lifetimes, fields, attributes, and lints.
[names.decl]
A declaration is a syntactical construct that can introduce a name to refer to an entity. Entity names are valid within a scope — a region of source text where that name may be referenced.
[names.explicit-decl]
Some entities are explicitly declared in the source code, and some are implicitly declared as part of the language or compiler extensions.
[names.path]
Paths are used to refer to an entity, possibly in another module or type.
[names.lifetime]
Lifetimes and loop labels use a dedicated syntax using a leading quote.
[names.namespace]
Names are segregated into different namespaces, allowing entities in different namespaces to share the same name without conflict.
[names.resolution]
Name resolution is the compile-time process of tying paths, identifiers, and labels to entity declarations.
[names.visibility]
Access to certain names may be restricted based on their visibility.
[names.explicit]
Explicitly declared entities
[names.explicit.list]
Entities that explicitly introduce a name in the source code are:
[names.explicit.item-decl]
Items:
Module declarations
External crate declarations
Use declarations
Function declarations and function parameters
Type aliases
struct, union, enum, enum variant declarations, and their named fields
Constant item declarations
Static item declarations
Trait item declarations and their associated items
External block items
macro_rules declarations and matcher metavariables
Implementation associated items
[names.explicit.expr]
Expressions:
Closure parameters
while let pattern bindings
for pattern bindings
if let pattern bindings
match pattern bindings
Loop labels
[names.explicit.generics]
Generic parameters
[names.explicit.higher-ranked-bounds]
Higher ranked trait bounds
[names.explicit.binding]
let statement pattern bindings
[names.explicit.macro_use]
The macro_use attribute can introduce macro names from another crate
[names.explicit.macro_export]
The macro_export attribute can introduce an alias for the macro into the crate root
[names.explicit.macro-invocation]
Additionally, macro invocations and attributes can introduce names by expanding to one of the above items.
[names.implicit]
Implicitly declared entities
[names.implicit.list]
The following entities are implicitly defined by the language, or are introduced by compiler options and extensions:
[names.implicit.primitive-types]
Language prelude:
Boolean type — bool
Textual types — char and str
Integer types — i8, i16, i32, i64, i128, u8, u16, u32, u64, u128
Machine-dependent integer types — usize and isize
floating-point types — f32 and f64
[names.implicit.builtin-attributes]
Built-in attributes
[names.implicit.prelude]
Standard library prelude items, attributes, and macros
[names.implicit.stdlib]
Standard library crates in the root module
[names.implicit.extern-prelude]
External crates linked by the compiler
[names.implicit.tool-attributes]
Tool attributes
[names.implicit.lints]
Lints and tool lint attributes
[names.implicit.derive-helpers]
Derive helper attributes are valid within an item without being explicitly imported
[names.implicit.lifetime-static]
The 'static lifetime
[names.implicit.root]
Additionally, the crate root module does not have a name, but can be referred to with certain path qualifiers or aliases.
[names.namespaces]
## Namespaces

[names.namespaces.intro]
A namespace is a logical grouping of declared names. Names are segregated into separate namespaces based on the kind of entity the name refers to. Namespaces allow the occurrence of a name in one namespace to not conflict with the same name in another namespace.
There are several different namespaces that each contain different kinds of entities. The usage of a name will look for the declaration of that name in different namespaces, based on the context, as described in the name resolution chapter.
[names.namespaces.kinds]
The following is a list of namespaces, with their corresponding entities:
Type Namespace
Module declarations
External crate declarations
External crate prelude items
Struct, union, enum, enum variant declarations
Trait item declarations
Type aliases
Associated type declarations
Built-in types: boolean, numeric, and textual
Generic type parameters
Self type
Tool attribute modules
Value Namespace
Function declarations
Constant item declarations
Static item declarations
Struct constructors
Enum variant constructors
Self constructors
Generic const parameters
Associated const declarations
Associated function declarations
Local bindings — let, if let, while let, for, match arms, function parameters, closure parameters
Captured closure variables
Macro Namespace
macro_rules declarations
Built-in attributes
Tool attributes
Function-like procedural macros
Derive macros
Derive macro helpers
Attribute macros
Lifetime Namespace
Generic lifetime parameters
Label Namespace
Loop labels
Block labels
An example of how overlapping names in different namespaces can be used unambiguously:
// Foo introduces a type in the type namespace and a constructor in the value
// namespace.
struct Foo(u32);

// The `Foo` macro is declared in the macro namespace.
macro_rules! Foo {
    () => {};
}

// `Foo` in the `f` parameter type refers to `Foo` in the type namespace.
// `'Foo` introduces a new lifetime in the lifetime namespace.
fn example<'Foo>(f: Foo) {
    // `Foo` refers to the `Foo` constructor in the value namespace.
    let ctor = Foo;
    // `Foo` refers to the `Foo` macro in the macro namespace.
    Foo!{}
    // `'Foo` introduces a label in the label namespace.
    'Foo: loop {
        // `'Foo` refers to the `'Foo` lifetime parameter, and `Foo`
        // refers to the type namespace.
        let x: &'Foo Foo;
        // `'Foo` refers to the label.
        break 'Foo;
    }
}
[names.namespaces.without]
Named entities without a namespace
The following entities have explicit names, but the names are not a part of any specific namespace.
Fields
[names.namespaces.without.fields]
Even though struct, enum, and union fields are named, the named fields do not live in an explicit namespace. They can only be accessed via a field expression, which only inspects the field names of the specific type being accessed.
Use declarations
[names.namespaces.without.use]
A use declaration has named aliases that it imports into scope, but the use item itself does not belong to a specific namespace. Instead, it can introduce aliases into multiple namespaces, depending on the item kind being imported.
[names.namespaces.sub-namespaces]
Sub-namespaces
[names.namespaces.sub-namespaces.intro]
The macro namespace is split into two sub-namespaces: one for bang-style macros and one for attributes. When an attribute is resolved, any bang-style macros in scope will be ignored. And conversely resolving a bang-style macro will ignore attribute macros in scope. This prevents one style from shadowing another.
For example, the cfg attribute and the cfg macro are two different entities with the same name in the macro namespace, but they can still be used in their respective context.
[names.namespaces.sub-namespaces.use-shadow]
It is still an error for a use import to shadow another macro, regardless of their sub-namespaces.
[names.scopes]
## Scopes

[names.scopes.intro]
A scope is the region of source text where a named entity may be referenced with that name. The following sections provide details on the scoping rules and behavior, which depend on the kind of entity and where it is declared. The process of how names are resolved to entities is described in the name resolution chapter. More information on “drop scopes” used for the purpose of running destructors may be found in the destructors chapter.
[names.scopes.items]
Item scopes
[names.scopes.items.module]
The name of an item declared directly in a module has a scope that extends from the start of the module to the end of the module. These items are also members of the module and can be referred to with a path leading from their module.
[names.scopes.items.statement]
The name of an item declared as a statement has a scope that extends from the start of the block the item statement is in until the end of the block.
[names.scopes.items.duplicate]
It is an error to introduce an item with a duplicate name of another item in the same namespace within the same module or block. Asterisk glob imports have special behavior for dealing with duplicate names and shadowing, see the linked chapter for more details.
[names.scopes.items.shadow-prelude]
Items in a module may shadow items in a prelude.
[names.scopes.items.nested-modules]
Item names from outer modules are not in scope within a nested module. A path may be used to refer to an item in another module.
[names.scopes.associated-items]
Associated item scopes
[names.scopes.associated-items.scope]
Associated items are not scoped and can only be referred to by using a path leading from the type or trait they are associated with. Methods can also be referred to via call expressions.
[names.scopes.associated-items.duplicate]
Similar to items within a module or block, it is an error to introduce an item within a trait or implementation that is a duplicate of another item in the trait or impl in the same namespace.
[names.scopes.pattern-bindings]
Pattern binding scopes
The scope of a local variable pattern binding depends on where it is used:
[names.scopes.pattern-bindings.let]
let statement bindings range from just after the let statement until the end of the block where it is declared.
[names.scopes.pattern-bindings.parameter]
Function parameter bindings are within the body of the function.
[names.scopes.pattern-bindings.closure]
Closure parameter bindings are within the closure body.
[names.scopes.pattern-bindings.loop]
for bindings are within the loop body.
[names.scopes.pattern-bindings.let-chains]
if let and while let bindings are valid in the following conditions as well as the consequent block.
[names.scopes.pattern-bindings.match-arm]
match arms bindings are within the match guard and the match arm expression.
[names.scopes.pattern-bindings.items]
Local variable scopes do not extend into item declarations.
Pattern binding shadowing
[names.scopes.pattern-bindings.shadow]
Pattern bindings are allowed to shadow any name in scope with the following exceptions which are an error:
Const generic parameters
Static items
Const items
Constructors for structs and enums
The following example illustrates how local bindings can shadow item declarations:
fn shadow_example() {
    // Since there are no local variables in scope yet, this resolves to the function.
    foo(); // prints `function`
    let foo = || println!("closure");
    fn foo() { println!("function"); }
    // This resolves to the local closure since it shadows the item.
    foo(); // prints `closure`
}
[names.scopes.generic-parameters]
Generic parameter scopes
[names.scopes.generic-parameters.param-list]
Generic parameters are declared in a GenericParams list. The scope of a generic parameter is within the item it is declared on.
[names.scopes.generic-parameters.order-independent]
All parameters are in scope within the generic parameter list regardless of the order they are declared. The following shows some examples where a parameter may be referenced before it is declared:
// The 'b bound is referenced before it is declared.
fn params_scope<'a: 'b, 'b>() {}

// The const N is referenced in the trait bound before it is declared.
fn f<T: SomeTrait<N>, const N: usize>() {}
[names.scopes.generic-parameters.bounds]
Generic parameters are also in scope for type bounds and where clauses, for example:
// The <'a, U> for `SomeTrait` refer to the 'a and U parameters of `bounds_scope`.
fn bounds_scope<'a, T: SomeTrait<'a, U>, U>() {}

fn where_scope<'a, T, U>()
    where T: SomeTrait<'a, U>
{}
[names.scopes.generic-parameters.inner-items]
It is an error for items declared inside a function to refer to a generic parameter from their outer scope.
fn example<T>() {
    fn inner(x: T) {} // ERROR: can't use generic parameters from outer function
}
Generic parameter shadowing
[names.scopes.generic-parameters.shadow]
It is an error to shadow a generic parameter with the exception that items declared within functions are allowed to shadow generic parameter names from the function.
fn example<'a, T, const N: usize>() {
    // Items within functions are allowed to shadow generic parameter in scope.
    fn inner_lifetime<'a>() {} // OK
    fn inner_type<T>() {} // OK
    fn inner_const<const N: usize>() {} // OK
}
trait SomeTrait<'a, T, const N: usize> {
    fn example_lifetime<'a>() {} // ERROR: 'a is already in use
    fn example_type<T>() {} // ERROR: T is already in use
    fn example_const<const N: usize>() {} // ERROR: N is already in use
    fn example_mixed<const T: usize>() {} // ERROR: T is already in use
}
[names.scopes.lifetimes]
Lifetime scopes
Lifetime parameters are declared in a GenericParams list and higher-ranked trait bounds.
[names.scopes.lifetimes.special]
The 'static lifetime and placeholder lifetime '_ have a special meaning and cannot be declared as a parameter.
Lifetime generic parameter scopes
[names.scopes.lifetimes.generic]
Constant and static items and const contexts only ever allow 'static lifetime references, so no other lifetime may be in scope within them. Associated consts do allow referring to lifetimes declared in their trait or implementation.
Higher-ranked trait bound scopes
[names.scopes.lifetimes.higher-ranked]
The scope of a lifetime parameter declared as a higher-ranked trait bound depends on the scenario where it is used.
As a TypeBoundWhereClauseItem the declared lifetimes are in scope in the type and the type bounds.
As a TraitBound the declared lifetimes are in scope within the bound type path.
As a BareFunctionType the declared lifetimes are in scope within the function parameters and return type.

fn where_clause<T>()
    // 'a is in scope in both the type and the type bounds.
    where for <'a> &'a T: Trait<'a>
{}

fn bound<T>()
    // 'a is in scope within the bound.
    where T: for <'a> Trait<'a>
{}


// 'a is in scope in both the parameters and return type.
type FnExample = for<'a> fn(x: Example<'a>) -> Example<'a>;
Impl trait restrictions
[names.scopes.lifetimes.impl-trait]
Impl trait types can only reference lifetimes declared on a function or implementation.
// The `impl Trait2` here is not allowed to refer to 'b but it is allowed to
// refer to 'a.
fn foo<'a>() -> impl for<'b> Trait1<Item = impl Trait2<'a> + use<'a>> {
    // ...
}
[names.scopes.loop-label]
Loop label scopes
[names.scopes.loop-label.scope]
Loop labels may be declared by a loop expression. The scope of a loop label is from the point it is declared till the end of the loop expression. The scope does not extend into items, closures, async blocks, const arguments, const contexts, and the iterator expression of the defining for loop.
'a: for n in 0..3 {
    if n % 2 == 0 {
        break 'a;
    }
    fn inner() {
        // Using 'a here would be an error.
        // break 'a;
    }
}

// The label is in scope for the expression of `while` loops.
'a: while break 'a {}         // Loop does not run.
'a: while let _ = break 'a {} // Loop does not run.

// The label is not in scope in the defining `for` loop:
'a: for outer in 0..5 {
    // This will break the outer loop, skipping the inner loop and stopping
    // the outer loop.
    'a: for inner in { break 'a; 0..1 } {
        println!("{}", inner); // This does not run.
    }
    println!("{}", outer); // This does not run, either.
}

[names.scopes.loop-label.shadow]
Loop labels may shadow labels of the same name in outer scopes. References to a label refer to the closest definition.
// Loop label shadowing example.
'a: for outer in 0..5 {
    'a: for inner in 0..5 {
        // This terminates the inner loop, but the outer loop continues to run.
        break 'a;
    }
}
[names.scopes.prelude]
Prelude scopes
[names.scopes.prelude.intro]
Preludes bring entities into scope of every module. The entities are not members of the module, but are implicitly queried during name resolution.
[names.scopes.prelude.shadow]
The prelude names may be shadowed by declarations in a module.
[names.scopes.prelude.layers]
The preludes are layered such that one shadows another if they contain entities of the same name. The order that preludes may shadow other preludes is the following where earlier entries may shadow later ones:
Extern prelude
Tool prelude
macro_use prelude
Standard library prelude
Language prelude
[names.scopes.macro_rules]
macro_rules scopes
The scope of macro_rules macros is described in the Macros By Example chapter. The behavior depends on the use of the macro_use and macro_export attributes.
[names.scopes.derive]
Derive macro helper attributes
[names.scopes.derive.scope]
Derive macro helper attributes are in scope in the item where their corresponding derive attribute is specified. The scope extends from just after the derive attribute to the end of the item.
[names.scopes.derive.shadow]
Helper attributes shadow other attributes of the same name in scope.
[names.scopes.self]
Self scope
[names.scopes.self.intro]
Although Self is a keyword with special meaning, it interacts with name resolution in a way similar to normal names.
[names.scopes.self.def-scope]
The implicit Self type in the definition of a struct, enum, union, trait, or implementation is treated similarly to a generic parameter, and is in scope in the same way as a generic type parameter.
[names.scopes.self.impl-scope]
The implicit Self constructor in the value namespace of an implementation is in scope within the body of the implementation (the implementation’s associated items).
// Self type within struct definition.
struct Recursive {
    f1: Option<Box<Self>>
}

// Self type within generic parameters.
struct SelfGeneric<T: Into<Self>>(T);

// Self value constructor within an implementation.
struct ImplExample();
impl ImplExample {
    fn example() -> Self { // Self type
        Self() // Self value constructor
    }
}
[names.preludes]
## Preludes

[names.preludes.intro]
A prelude is a collection of names that are automatically brought into scope of every module in a crate.
These prelude names are not part of the module itself: they are implicitly queried during name resolution. For example, even though something like Box is in scope in every module, you cannot refer to it as self::Box because it is not a member of the current module.
[names.preludes.kinds]
There are several different preludes:
Standard library prelude
Extern prelude
Language prelude
macro_use prelude
Tool prelude
[names.preludes.std]
Standard library prelude
[names.preludes.std.intro]
Each crate has a standard library prelude, which consists of the names from a single standard library module.
[names.preludes.std.module]
The module used depends on the crate’s edition, and on whether the no_std attribute is applied to the crate:
Edition	no_std not applied	no_std applied
2015	std::prelude::rust_2015	core::prelude::rust_2015
2018	std::prelude::rust_2018	core::prelude::rust_2018
2021	std::prelude::rust_2021	core::prelude::rust_2021
2024	std::prelude::rust_2024	core::prelude::rust_2024
Note

std::prelude::rust_2015 and std::prelude::rust_2018 have the same contents as std::prelude::v1.

core::prelude::rust_2015 and core::prelude::rust_2018 have the same contents as core::prelude::v1.
[names.preludes.extern]
Extern prelude
[names.preludes.extern.intro]
External crates imported with extern crate in the root module or provided to the compiler (as with the --extern flag with rustc) are added to the extern prelude. If imported with an alias such as extern crate orig_name as new_name, then the symbol new_name is instead added to the prelude.
[names.preludes.extern.core]
The core crate is always added to the extern prelude.
[names.preludes.extern.std]
The std crate is added as long as the no_std attribute is not specified in the crate root.
[names.preludes.extern.edition2018]
2018
Edition differences

In the 2015 edition, crates in the extern prelude cannot be referenced via use declarations, so it is generally standard practice to include extern crate declarations to bring them into scope.

Beginning in the 2018 edition, use declarations can reference crates in the extern prelude, so it is considered unidiomatic to use extern crate.
Note

Additional crates that ship with rustc, such as alloc, and test, are not automatically included with the --extern flag when using Cargo. They must be brought into scope with an extern crate declaration, even in the 2018 edition.

extern crate alloc;
use alloc::rc::Rc;
Cargo does bring in proc_macro to the extern prelude for proc-macro crates only.
[names.preludes.extern.no_std]
The no_std attribute
[names.preludes.extern.no_std.intro]
By default, the standard library is automatically included in the crate root module. The std crate is added to the root, along with an implicit macro_use attribute pulling in all macros exported from std into the macro_use prelude. Both core and std are added to the extern prelude.
[names.preludes.extern.no_std.allowed-positions]
The no_std attribute may be applied at the crate level to prevent the std crate from being automatically added into scope.
It does three things:
[names.preludes.extern.no_std.extern]
Prevents std from being added to the extern prelude.
[names.preludes.extern.no_std.module]
Affects which module is used to make up the standard library prelude (as described above).
[names.preludes.extern.no_std.core]
Injects the core crate into the crate root instead of std, and pulls in all macros exported from core in the macro_use prelude.
Note

Using the core prelude over the standard prelude is useful when either the crate is targeting a platform that does not support the standard library or is purposefully not using the capabilities of the standard library. Those capabilities are mainly dynamic memory allocation (e.g. Box and Vec) and file and network capabilities (e.g. std::fs and std::io).
Warning

Using no_std does not prevent the standard library from being linked in. It is still valid to put extern crate std; into the crate and dependencies can also link it in.
[names.preludes.lang]
Language prelude
[names.preludes.lang.intro]
The language prelude includes names of types and attributes that are built-in to the language. The language prelude is always in scope.
[names.preludes.lang.entities]
It includes the following:
Type namespace
Boolean type — bool
Textual types — char and str
Integer types — i8, i16, i32, i64, i128, u8, u16, u32, u64, u128
Machine-dependent integer types — usize and isize
floating-point types — f32 and f64
Macro namespace
Built-in attributes
Built-in derive macros
[names.preludes.macro_use]
macro_use prelude
[names.preludes.macro_use.intro]
The macro_use prelude includes macros from external crates that were imported by the macro_use attribute applied to an extern crate.
[names.preludes.tool]
Tool prelude
[names.preludes.tool.intro]
The tool prelude includes tool names for external tools in the type namespace. See the tool attributes section for more details.
[names.preludes.no_implicit_prelude]
The no_implicit_prelude attribute
[names.preludes.no_implicit_prelude.intro]
The no_implicit_prelude attribute may be applied at the crate level or on a module to indicate that it should not automatically bring the standard library prelude, extern prelude, or tool prelude into scope for that module or any of its descendants.
[names.preludes.no_implicit_prelude.lang]
This attribute does not affect the language prelude.
[names.preludes.no_implicit_prelude.edition2018]
2018
Edition differences

In the 2015 edition, the no_implicit_prelude attribute does not affect the macro_use prelude, and all macros exported from the standard library are still included in the macro_use prelude. Starting in the 2018 edition, it will remove the macro_use prelude.
[paths]
## Paths

[paths.intro]
A path is a sequence of one or more path segments separated by :: tokens. Paths are used to refer to items, values, types, macros, and attributes.
Two examples of simple paths consisting of only identifier segments:
x;
x::y::z;
Types of paths
[paths.simple]
Simple Paths
[paths.simple.syntax]
Syntax
SimplePath →
    ::? SimplePathSegment ( :: SimplePathSegment )*

SimplePathSegment →
    IDENTIFIER | super | self | crate | $crate

Show syntax diagrams

[paths.simple.intro]
Simple paths are used in visibility markers, attributes, macros, and use items. For example:
use std::io::{self, Write};
mod m {
    #[clippy::cyclomatic_complexity = "0"]
    pub (in super) fn f1() {}
}
[paths.expr]
Paths in expressions
[paths.expr.syntax]
Syntax
PathInExpression →
    ::? PathExprSegment ( :: PathExprSegment )*

PathExprSegment →
    PathIdentSegment ( :: GenericArgs )?

PathIdentSegment →
    IDENTIFIER | super | self | Self | crate | $crate

GenericArgs →
      < >
    | < ( GenericArg , )* GenericArg ,? >

GenericArg →
    Lifetime | Type | GenericArgsConst | GenericArgsBinding | GenericArgsBounds

GenericArgsConst →
      BlockExpression
    | LiteralExpression
    | - LiteralExpression
    | SimplePathSegment

GenericArgsBinding →
    IDENTIFIER GenericArgs? = Type

GenericArgsBounds →
    IDENTIFIER GenericArgs? : TypeParamBounds

Show syntax diagrams

[paths.expr.intro]
Paths in expressions allow for paths with generic arguments to be specified. They are used in various places in expressions and patterns.
[paths.expr.turbofish]
The :: token is required before the opening < for generic arguments to avoid ambiguity with the less-than operator. This is colloquially known as “turbofish” syntax.
(0..10).collect::<Vec<_>>();
Vec::<u8>::with_capacity(1024);
[paths.expr.argument-order]
The order of generic arguments is restricted to lifetime arguments, then type arguments, then const arguments, then equality constraints.
[paths.expr.complex-const-params]
Const arguments must be surrounded by braces unless they are a literal, an inferred const, or a single segment path. An inferred const may not be surrounded by braces.
mod m {
    pub const C: usize = 1;
}
const C: usize = m::C;
fn f<const N: usize>() -> [u8; N] { [0; N] }

let _ = f::<1>(); // Literal.
let _: [_; 1] = f::<_>(); // Inferred const.
let _: [_; 1] = f::<(((_)))>(); // Inferred const.
let _ = f::<C>(); // Single segment path.
let _ = f::<{ m::C }>(); // Multi-segment path must be braced.
fn f<const N: usize>() -> [u8; N] { [0; _] }
let _: [_; 1] = f::<{ _ }>();
//                    ^ ERROR `_` not allowed here
Note

In a generic argument list, an inferred const is parsed as an inferred type but then semantically treated as a separate kind of const generic argument.
[paths.expr.impl-trait-params]
The synthetic type parameters corresponding to impl Trait types are implicit, and these cannot be explicitly specified.
[paths.qualified]
Qualified paths
[paths.qualified.syntax]
Syntax
QualifiedPathInExpression → QualifiedPathType ( :: PathExprSegment )+

QualifiedPathType → < Type ( as TypePath )? >

QualifiedPathInType → QualifiedPathType ( :: TypePathSegment )+

Show syntax diagrams

[paths.qualified.intro]
Fully qualified paths allow for disambiguating the path for trait implementations and for specifying canonical paths. When used in a type specification, it supports using the type syntax specified below.
struct S;
impl S {
    fn f() { println!("S"); }
}
trait T1 {
    fn f() { println!("T1 f"); }
}
impl T1 for S {}
trait T2 {
    fn f() { println!("T2 f"); }
}
impl T2 for S {}
S::f();  // Calls the inherent impl.
<S as T1>::f();  // Calls the T1 trait function.
<S as T2>::f();  // Calls the T2 trait function.
[paths.type]
Paths in types
[paths.type.syntax]
Syntax
TypePath → ::? TypePathSegment ( :: TypePathSegment )*

TypePathSegment → PathIdentSegment ( ::? ( GenericArgs | TypePathFn ) )?

TypePathFn → ( TypePathFnInputs? ) ( -> TypeNoBounds )?

TypePathFnInputs → Type ( , Type )* ,?

Show syntax diagrams

[paths.type.intro]
Type paths are used within type definitions, trait bounds, type parameter bounds, and qualified paths.
[paths.type.turbofish]
Although the :: token is allowed before the generics arguments, it is not required because there is no ambiguity like there is in PathInExpression.
impl ops::Index<ops::Range<usize>> for S { /*...*/ }
fn i<'a>() -> impl Iterator<Item = ops::Example<'a>> {
    // ...
}
type G = std::boxed::Box<dyn std::ops::FnOnce(isize) -> isize>;
[paths.qualifiers]
Path qualifiers
Paths can be denoted with various leading qualifiers to change the meaning of how it is resolved.
[paths.qualifiers.global-root]
::
[paths.qualifiers.global-root.intro]
Paths starting with :: are considered to be global paths where the segments of the path start being resolved from a place which differs based on edition. Each identifier in the path must resolve to an item.
[paths.qualifiers.global-root.edition2018]
2018
Edition differences

In the 2015 Edition, identifiers resolve from the “crate root” (crate:: in the 2018 edition), which contains a variety of different items, including external crates, default crates such as std or core, and items in the top level of the crate (including use imports).

Beginning with the 2018 Edition, paths starting with :: resolve from crates in the extern prelude. That is, they must be followed by the name of a crate.
pub fn foo() {
    // In the 2018 edition, this accesses `std` via the extern prelude.
    // In the 2015 edition, this accesses `std` via the crate root.
    let now = ::std::time::Instant::now();
    println!("{:?}", now);
}
// 2015 Edition
mod a {
    pub fn foo() {}
}
mod b {
    pub fn foo() {
        ::a::foo(); // call `a`'s foo function
        // In Rust 2018, `::a` would be interpreted as the crate `a`.
    }
}
[paths.qualifiers.mod-self]
self
[paths.qualifiers.mod-self.intro]
self resolves the path relative to the current module.
[paths.qualifiers.mod-self.restriction]
self can only be used as the first segment, without a preceding ::.
[paths.qualifiers.self-pat]
In a method body, a path which consists of a single self segment resolves to the method’s self parameter.
fn foo() {}
fn bar() {
    self::foo();
}
struct S(bool);
impl S {
  fn baz(self) {
        self.0;
    }
}
[paths.qualifiers.type-self]
Self
[paths.qualifiers.type-self.intro]
Self, with a capital “S”, is used to refer to the current type being implemented or defined. It may be used in the following situations:
[paths.qualifiers.type-self.trait]
In a trait definition, it refers to the type implementing the trait.
[paths.qualifiers.type-self.impl]
In an implementation, it refers to the type being implemented. When implementing a tuple or unit struct, it also refers to the constructor in the value namespace.
[paths.qualifiers.type-self.type]
In the definition of a struct, enumeration, or union, it refers to the type being defined. The definition is not allowed to be infinitely recursive (there must be an indirection).
[paths.qualifiers.type-self.scope]
The scope of Self behaves similarly to a generic parameter; see the Self scope section for more details.
[paths.qualifiers.type-self.allowed-positions]
Self can only be used as the first segment, without a preceding ::.
[paths.qualifiers.type-self.no-generics]
The Self path cannot include generic arguments (as in Self::<i32>).
trait T {
    type Item;
    const C: i32;
    // `Self` will be whatever type that implements `T`.
    fn new() -> Self;
    // `Self::Item` will be the type alias in the implementation.
    fn f(&self) -> Self::Item;
}
struct S;
impl T for S {
    type Item = i32;
    const C: i32 = 9;
    fn new() -> Self {           // `Self` is the type `S`.
        S
    }
    fn f(&self) -> Self::Item {  // `Self::Item` is the type `i32`.
        Self::C                  // `Self::C` is the constant value `9`.
    }
}

// `Self` is in scope within the generics of a trait definition,
// to refer to the type being defined.
trait Add<Rhs = Self> {
    type Output;
    // `Self` can also reference associated items of the
    // type being implemented.
    fn add(self, rhs: Rhs) -> Self::Output;
}

struct NonEmptyList<T> {
    head: T,
    // A struct can reference itself (as long as it is not
    // infinitely recursive).
    tail: Option<Box<Self>>,
}
[paths.qualifiers.super]
super
[paths.qualifiers.super.intro]
super in a path resolves to the parent module.
[paths.qualifiers.super.allowed-positions]
It may only be used in leading segments of the path, possibly after an initial self segment.
mod a {
    pub fn foo() {}
}
mod b {
    pub fn foo() {
        super::a::foo(); // call a's foo function
    }
}
[paths.qualifiers.super.repetition]
super may be repeated several times after the first super or self to refer to ancestor modules.
mod a {
    fn foo() {}

    mod b {
        mod c {
            fn foo() {
                super::super::foo(); // call a's foo function
                self::super::super::foo(); // call a's foo function
            }
        }
    }
}
[paths.qualifiers.crate]
crate
[paths.qualifiers.crate.intro]
crate resolves the path relative to the current crate.
[paths.qualifiers.crate.allowed-positions]
crate can only be used as the first segment, without a preceding ::.
fn foo() {}
mod a {
    fn bar() {
        crate::foo();
    }
}
[paths.qualifiers.macro-crate]
$crate
[paths.qualifiers.macro-crate.allowed-positions]
$crate is only used within macro transcribers, and can only be used as the first segment, without a preceding ::.
[paths.qualifiers.macro-crate.hygiene]
$crate will expand to a path to access items from the top level of the crate where the macro is defined, regardless of which crate the macro is invoked.
pub fn increment(x: u32) -> u32 {
    x + 1
}

#[macro_export]
macro_rules! inc {
    ($x:expr) => ( $crate::increment($x) )
}
[paths.canonical]
Canonical paths
[paths.canonical.intro]
Items defined in a module or implementation have a canonical path that corresponds to where within its crate it is defined.
[paths.canonical.alias]
All other paths to these items are aliases.
[paths.canonical.def]
The canonical path is defined as a path prefix appended by the path segment the item itself defines.
[paths.canonical.non-canonical]
Implementations and use declarations do not have canonical paths, although the items that implementations define do have them. Items defined in block expressions do not have canonical paths. Items defined in a module that does not have a canonical path do not have a canonical path. Associated items defined in an implementation that refers to an item without a canonical path, e.g. as the implementing type, the trait being implemented, a type parameter or bound on a type parameter, do not have canonical paths.
[paths.canonical.module-prefix]
The path prefix for modules is the canonical path to that module.
[paths.canonical.bare-impl-prefix]
For bare implementations, it is the canonical path of the item being implemented surrounded by angle (<>) brackets.
[paths.canonical.trait-impl-prefix]
For trait implementations, it is the canonical path of the item being implemented followed by as followed by the canonical path to the trait all surrounded in angle (<>) brackets.
[paths.canonical.local-canonical-path]
The canonical path is only meaningful within a given crate. There is no global namespace across crates; an item’s canonical path merely identifies it within the crate.
// Comments show the canonical path of the item.

mod a { // crate::a
    pub struct Struct; // crate::a::Struct

    pub trait Trait { // crate::a::Trait
        fn f(&self); // crate::a::Trait::f
    }

    impl Trait for Struct {
        fn f(&self) {} // <crate::a::Struct as crate::a::Trait>::f
    }

    impl Struct {
        fn g(&self) {} // <crate::a::Struct>::g
    }
}

mod without { // crate::without
    fn canonicals() { // crate::without::canonicals
        struct OtherStruct; // None

        trait OtherTrait { // None
            fn g(&self); // None
        }

        impl OtherTrait for OtherStruct {
            fn g(&self) {} // None
        }

        impl OtherTrait for crate::a::Struct {
            fn g(&self) {} // None
        }

        impl crate::a::Trait for OtherStruct {
            fn f(&self) {} // None
        }
    }
}

## Name resolution

Note

This is a placeholder for future expansion.
[vis]
## Visibility and privacy

[vis.syntax]
Syntax
Visibility →
      pub
    | pub ( crate )
    | pub ( self )
    | pub ( super )
    | pub ( in SimplePath )

Show syntax diagrams

[vis.intro]
These two terms are often used interchangeably, and what they are attempting to convey is the answer to the question “Can this item be used at this location?”
[vis.name-hierarchy]
Rust’s name resolution operates on a global hierarchy of namespaces. Each level in the hierarchy can be thought of as some item. The items are one of those mentioned above, but also include external crates. Declaring or defining a new module can be thought of as inserting a new tree into the hierarchy at the location of the definition.
[vis.privacy]
To control whether interfaces can be used across modules, Rust checks each use of an item to see whether it should be allowed or not. This is where privacy warnings are generated, or otherwise “you used a private item of another module and weren’t allowed to.”
[vis.default]
By default, everything is private, with two exceptions: Associated items in a pub Trait are public by default; Enum variants in a pub enum are also public by default. When an item is declared as pub, it can be thought of as being accessible to the outside world. For example:
// Declare a private struct
struct Foo;

// Declare a public struct with a private field
pub struct Bar {
    field: i32,
}

// Declare a public enum with two public variants
pub enum State {
    PubliclyAccessibleState,
    PubliclyAccessibleState2,
}
[vis.access]
With the notion of an item being either public or private, Rust allows item accesses in two cases:
If an item is public, then it can be accessed externally from some module m if you can access all the item’s ancestor modules from m. You can also potentially be able to name the item through re-exports. See below.
If an item is private, it may be accessed by the current module and its descendants.
These two cases are surprisingly powerful for creating module hierarchies exposing public APIs while hiding internal implementation details. To help explain, here’s a few use cases and what they would entail:
A library developer needs to expose functionality to crates which link against their library. As a consequence of the first case, this means that anything which is usable externally must be pub from the root down to the destination item. Any private item in the chain will disallow external accesses.
A crate needs a global available “helper module” to itself, but it doesn’t want to expose the helper module as a public API. To accomplish this, the root of the crate’s hierarchy would have a private module which then internally has a “public API”. Because the entire crate is a descendant of the root, then the entire local crate can access this private module through the second case.
When writing unit tests for a module, it’s often a common idiom to have an immediate child of the module to-be-tested named mod test. This module could access any items of the parent module through the second case, meaning that internal implementation details could also be seamlessly tested from the child module.
In the second case, it mentions that a private item “can be accessed” by the current module and its descendants, but the exact meaning of accessing an item depends on what the item is.
[vis.usage]
Accessing a module, for example, would mean looking inside of it (to import more items). On the other hand, accessing a function would mean that it is invoked. Additionally, path expressions and import statements are considered to access an item in the sense that the import/expression is only valid if the destination is in the current visibility scope.
Here’s an example of a program which exemplifies the three cases outlined above:
// This module is private, meaning that no external crate can access this
// module. Because it is private at the root of this current crate, however, any
// module in the crate may access any publicly visible item in this module.
mod crate_helper_module {

    // This function can be used by anything in the current crate
    pub fn crate_helper() {}

    // This function *cannot* be used by anything else in the crate. It is not
    // publicly visible outside of the `crate_helper_module`, so only this
    // current module and its descendants may access it.
    fn implementation_detail() {}
}

// This function is "public to the root" meaning that it's available to external
// crates linking against this one.
pub fn public_api() {}

// Similarly to 'public_api', this module is public so external crates may look
// inside of it.
pub mod submodule {
    use crate::crate_helper_module;

    pub fn my_method() {
        // Any item in the local crate may invoke the helper module's public
        // interface through a combination of the two rules above.
        crate_helper_module::crate_helper();
    }

    // This function is hidden to any module which is not a descendant of
    // `submodule`
    fn my_implementation() {}

    #[cfg(test)]
    mod test {

        #[test]
        fn test_my_implementation() {
            // Because this module is a descendant of `submodule`, it's allowed
            // to access private items inside of `submodule` without a privacy
            // violation.
            super::my_implementation();
        }
    }
}

For a Rust program to pass the privacy checking pass, all paths must be valid accesses given the two rules above. This includes all use statements, expressions, types, etc.
[vis.scoped]
pub(in path), pub(crate), pub(super), and pub(self)
[vis.scoped.intro]
In addition to public and private, Rust allows users to declare an item as visible only within a given scope. The rules for pub restrictions are as follows:
[vis.scoped.in]
pub(in path) makes an item visible within the provided path. path must be a simple path which resolves to an ancestor module of the item whose visibility is being declared. Each identifier in path must refer directly to a module (not to a name introduced by a use statement).
[vis.scoped.crate]
pub(crate) makes an item visible within the current crate.
[vis.scoped.super]
pub(super) makes an item visible to the parent module. This is equivalent to pub(in super).
[vis.scoped.self]
pub(self) makes an item visible to the current module. This is equivalent to pub(in self) or not using pub at all.
[vis.scoped.edition2018]
2018
Edition differences

Starting with the 2018 edition, paths for pub(in path) must start with crate, self, or super. The 2015 edition may also use paths starting with :: or modules from the crate root.
Here’s an example:
pub mod outer_mod {
    pub mod inner_mod {
        // This function is visible within `outer_mod`
        pub(in crate::outer_mod) fn outer_mod_visible_fn() {}
        // Same as above, this is only valid in the 2015 edition.
        pub(in outer_mod) fn outer_mod_visible_fn_2015() {}

        // This function is visible to the entire crate
        pub(crate) fn crate_visible_fn() {}

        // This function is visible within `outer_mod`
        pub(super) fn super_mod_visible_fn() {
            // This function is visible since we're in the same `mod`
            inner_mod_visible_fn();
        }

        // This function is visible only within `inner_mod`,
        // which is the same as leaving it private.
        pub(self) fn inner_mod_visible_fn() {}
    }
    pub fn foo() {
        inner_mod::outer_mod_visible_fn();
        inner_mod::crate_visible_fn();
        inner_mod::super_mod_visible_fn();

        // This function is no longer visible since we're outside of `inner_mod`
        // Error! `inner_mod_visible_fn` is private
        //inner_mod::inner_mod_visible_fn();
    }
}

fn bar() {
    // This function is still visible since we're in the same crate
    outer_mod::inner_mod::crate_visible_fn();

    // This function is no longer visible since we're outside of `outer_mod`
    // Error! `super_mod_visible_fn` is private
    //outer_mod::inner_mod::super_mod_visible_fn();

    // This function is no longer visible since we're outside of `outer_mod`
    // Error! `outer_mod_visible_fn` is private
    //outer_mod::inner_mod::outer_mod_visible_fn();

    outer_mod::foo();
}

fn main() { bar() }
Note

This syntax only adds another restriction to the visibility of an item. It does not guarantee that the item is visible within all parts of the specified scope. To access an item, all of its parent items up to the current scope must still be visible as well.
[vis.reexports]
Re-exporting and Visibility
[vis.reexports.intro]
Rust allows publicly re-exporting items through a pub use directive. Because this is a public directive, this allows the item to be used in the current module through the rules above. It essentially allows public access into the re-exported item. For example, this program is valid:
pub use self::implementation::api;

mod implementation {
    pub mod api {
        pub fn f() {}
    }
}

This means that any external crate referencing implementation::api::f would receive a privacy violation, while the path api::f would be allowed.
[vis.reexports.private-item]
When re-exporting a private item, it can be thought of as allowing the “privacy chain” being short-circuited through the reexport instead of passing through the namespace hierarchy as it normally would.
[memory]
