# Type system
[type]
## Types

[type.intro]
Every variable, item, and value in a Rust program has a type. The type of a value defines the interpretation of the memory holding it and the operations that may be performed on the value.
[type.builtin]
Built-in types are tightly integrated into the language, in nontrivial ways that are not possible to emulate in user-defined types.
[type.user-defined]
User-defined types have limited capabilities.
[type.kinds]
The list of types is:
Primitive types:
Boolean — bool
Numeric — integer and float
Textual — char and str
Never — ! — a type with no values
Sequence types:
Tuple
Array
Slice
User-defined types:
Struct
Enum
Union
Function types:
Functions
Closures
Pointer types:
References
Raw pointers
Function pointers
Trait types:
Trait objects
Impl trait
[type.name]
Type expressions
[type.name.syntax]
Syntax
Type →
      TypeNoBounds
### Impl trait type
    | TraitObjectType

TypeNoBounds →
      ParenthesizedType
    | ImplTraitTypeOneBound
    | TraitObjectTypeOneBound
    | TypePath
    | TupleType
    | NeverType
    | RawPointerType
    | ReferenceType
    | ArrayType
    | SliceType
    | InferredType
    | QualifiedPathInType
    | BareFunctionType
    | MacroInvocation

Show syntax diagrams

[type.name.intro]
A type expression as defined in the Type grammar rule above is the syntax for referring to a type. It may refer to:
[type.name.sequence]
Sequence types (tuple, array, slice).
[type.name.path]
Type paths which can reference:
Primitive types (boolean, numeric, textual).
Paths to an item (struct, enum, union, type alias, trait).
Self path where Self is the implementing type.
Generic type parameters.
[type.name.pointer]
Pointer types (reference, raw pointer, function pointer).
[type.name.inference]
The inferred type which asks the compiler to determine the type.
[type.name.grouped]
Parentheses which are used for disambiguation.
[type.name.trait]
Trait types: Trait objects and impl trait.
[type.name.never]
The never type.
[type.name.macro-expansion]
Macros which expand to a type expression.
[type.name.parenthesized]
Parenthesized types
[type.name.parenthesized.syntax]
Syntax
ParenthesizedType → ( Type )

Show syntax diagrams

[type.name.parenthesized.intro]
In some situations the combination of types may be ambiguous. Use parentheses around a type to avoid ambiguity. For example, the + operator for type boundaries within a reference type is unclear where the boundary applies, so the use of parentheses is required. Grammar rules that require this disambiguation use the TypeNoBounds rule instead of Type.
type T<'a> = &'a (dyn Any + Send);
[type.recursive]
Recursive types
[type.recursive.intro]
Nominal types — structs, enumerations, and unions — may be recursive. That is, each enum variant or struct or union field may refer, directly or indirectly, to the enclosing enum or struct type itself.
[type.recursive.constraint]
Such recursion has restrictions:
Recursive types must include a nominal type in the recursion (not mere type aliases, or other structural types such as arrays or tuples). So type Rec = &'static [Rec] is not allowed.
The size of a recursive type must be finite; in other words the recursive fields of the type must be pointer types.
An example of a recursive type and its use:
enum List<T> {
    Nil,
    Cons(T, Box<List<T>>)
}

let a: List<i32> = List::Cons(7, Box::new(List::Cons(13, Box::new(List::Nil))));
[type.bool]
### Boolean type

let b: bool = true;
[type.bool.intro]
The boolean type or bool is a primitive data type that can take on one of two values, called true and false.
[type.bool.literal]
Values of this type may be created using a literal expression using the keywords true and false corresponding to the value of the same name.
[type.bool.namespace]
This type is a part of the language prelude with the name bool.
[type.bool.layout]
An object with the boolean type has a size and alignment of 1 each.
[type.bool.repr]
The value false has the bit pattern 0x00 and the value true has the bit pattern 0x01. It is undefined behavior for an object with the boolean type to have any other bit pattern.
[type.bool.usage]
The boolean type is the type of many operands in various expressions:
[type.bool.usage-condition]
The condition operand in if expressions and while expressions
[type.bool.usage-lazy-operator]
The operands in lazy boolean operator expressions
Note

The boolean type acts similarly to but is not an enumerated type. In practice, this mostly means that constructors are not associated to the type (e.g. bool::true).
[type.bool.traits]
Like all primitives, the boolean type implements the traits Clone, Copy, Sized, Send, and Sync.
Note

See the standard library docs for library operations.
[type.bool.expr]
Operations on boolean values
When using certain operator expressions with a boolean type for its operands, they evaluate using the rules of boolean logic.
[type.bool.expr.not]
Logical not
b	!b
true	false
false	true
[type.bool.expr.or]
Logical or
a	b	a | b
true	true	true
true	false	true
false	true	true
false	false	false
[type.bool.expr.and]
Logical and
a	b	a & b
true	true	true
true	false	false
false	true	false
false	false	false
[type.bool.expr.xor]
Logical xor
a	b	a ^ b
true	true	false
true	false	true
false	true	true
false	false	false
[type.bool.expr.cmp]
Comparisons
[type.bool.expr.cmp.eq]
a	b	a == b
true	true	true
true	false	false
false	true	false
false	false	true
[type.bool.expr.cmp.greater]
a	b	a > b
true	true	false
true	false	true
false	true	false
false	false	false
[type.bool.expr.cmp.not-eq]
a != b is the same as !(a == b)
[type.bool.expr.cmp.greater-eq]
a >= b is the same as a == b | a > b
[type.bool.expr.cmp.less]
a < b is the same as !(a >= b)
[type.bool.expr.cmp.less-eq]
a <= b is the same as a == b | a < b
[type.bool.validity]
Bit validity
The single byte of a bool is guaranteed to be initialized (in other words, transmute::<bool, u8>(...) is always sound – but since some bit patterns are invalid bools, the inverse is not always sound).
[type.numeric]
### Numeric types

[type.numeric.int]
Integer types
[type.numeric.int.unsigned]
The unsigned integer types consist of:
Type	Minimum	Maximum
u8	0	28-1
u16	0	216-1
u32	0	232-1
u64	0	264-1
u128	0	2128-1
[type.numeric.int.signed]
The signed two’s complement integer types consist of:
Type	Minimum	Maximum
i8	-(27)	27-1
i16	-(215)	215-1
i32	-(231)	231-1
i64	-(263)	263-1
i128	-(2127)	2127-1
[type.numeric.float]
Floating-point types
The IEEE 754-2008 “binary32” and “binary64” floating-point types are f32 and f64, respectively.
[type.numeric.int.size]
Machine-dependent integer types
[type.numeric.int.size.usize]
The usize type is an unsigned integer type with the same number of bits as the platform’s pointer type. It can represent every memory address in the process.
Note

While a usize can represent every address, converting a pointer to a usize is not necessarily a reversible operation. For more information, see the documentation for type cast expressions, std::ptr, and provenance in particular.
[type.numeric.int.size.isize]
The isize type is a signed integer type with the same number of bits as the platform’s pointer type. The theoretical upper bound on object and array size is the maximum isize value. This ensures that isize can be used to calculate differences between pointers into an object or array and can address every byte within an object along with one byte past the end.
[type.numeric.int.size.minimum]
usize and isize are at least 16-bits wide.
Note

Many pieces of Rust code may assume that pointers, usize, and isize are either 32-bit or 64-bit. As a consequence, 16-bit pointer support is limited and may require explicit care and acknowledgment from a library to support.
[type.numeric.validity]
Bit validity
For every numeric type, T, the bit validity of T is equivalent to the bit validity of [u8; size_of::<T>()]. An uninitialized byte is not a valid u8.
[type.text]
### Textual types

[type.text.intro]
The types char and str hold textual data.
[type.text.char-value]
A value of type char is a Unicode scalar value (i.e. a code point that is not a surrogate), represented as a 32-bit unsigned word in the 0x0000 to 0xD7FF or 0xE000 to 0x10FFFF range.
[type.text.char-precondition]
It is immediate undefined behavior to create a char that falls outside this range. A [char] is effectively a UCS-4 / UTF-32 string of length 1.
[type.text.str-value]
A value of type str is represented the same way as [u8], a slice of 8-bit unsigned bytes. However, the Rust standard library makes extra assumptions about str: methods working on str assume and ensure that the data in there is valid UTF-8. Calling a str method with a non-UTF-8 buffer can cause undefined behavior now or in the future.
[type.text.str-unsized]
Since str is a dynamically sized type, it can only be instantiated through a pointer type, such as &str. The layout of &str is the same as the layout of &[u8].
[type.text.layout]
Layout and bit validity
[type.layout.char-layout]
char is guaranteed to have the same size and alignment as u32 on all platforms.
[type.layout.char-validity]
Every byte of a char is guaranteed to be initialized (in other words, transmute::<char, [u8; size_of::<char>()]>(...) is always sound – but since some bit patterns are invalid chars, the inverse is not always sound).
[type.never]
### Never type

[type.never.syntax]
Syntax
NeverType → !

Show syntax diagrams

[type.never.intro]
The never type ! is a type with no values, representing the result of computations that never complete.
[type.never.coercion]
Expressions of type ! can be coerced into any other type.
[type.never.constraint]
The ! type can only appear in function return types presently, indicating it is a diverging function that never returns.
fn foo() -> ! {
    panic!("This call never returns.");
}
unsafe extern "C" {
    pub safe fn no_return_extern_func() -> !;
}
[type.tuple]
### Tuple types

[type.tuple.syntax]
Syntax
TupleType →
      ( )
    | ( ( Type , )+ Type? )

Show syntax diagrams

[type.tuple.intro]
Tuple types are a family of structural types1 for heterogeneous lists of other types.
The syntax for a tuple type is a parenthesized, comma-separated list of types.
[type.tuple.restriction]
1-ary tuples require a comma after their element type to be disambiguated with a parenthesized type.
[type.tuple.field-number]
A tuple type has a number of fields equal to the length of the list of types. This number of fields determines the arity of the tuple. A tuple with n fields is called an n-ary tuple. For example, a tuple with 2 fields is a 2-ary tuple.
[type.tuple.field-name]
Fields of tuples are named using increasing numeric names matching their position in the list of types. The first field is 0. The second field is 1. And so on. The type of each field is the type of the same position in the tuple’s list of types.
[type.tuple.unit]
For convenience and historical reasons, the tuple type with no fields (()) is often called unit or the unit type. Its one value is also called unit or the unit value.
Some examples of tuple types:
() (unit)
(i32,) (1-ary tuple)
(f64, f64)
(String, i32)
(i32, String) (different type from the previous example)
(i32, f64, Vec<String>, Option<bool>)
[type.tuple.constructor]
Values of this type are constructed using a tuple expression. Furthermore, various expressions will produce the unit value if there is no other meaningful value for it to evaluate to.
[type.tuple.access]
Tuple fields can be accessed by either a tuple index expression or pattern matching.
Structural types are always equivalent if their internal types are equivalent. For a nominal version of tuples, see tuple structs. ↩

[type.array]
### Array types

[type.array.syntax]
Syntax
ArrayType → [ Type ; Expression ]

Show syntax diagrams

[type.array.intro]
An array is a fixed-size sequence of N elements of type T. The array type is written as [T; N].
[type.array.constraint]
The size is a constant expression that evaluates to a usize.
Examples:
// A stack-allocated array
let array: [i32; 3] = [1, 2, 3];

// A heap-allocated array, coerced to a slice
let boxed_array: Box<[i32]> = Box::new([1, 2, 3]);
[type.array.index]
All elements of arrays are always initialized, and access to an array is always bounds-checked in safe methods and operators.
Note

The Vec<T> standard library type provides a heap-allocated resizable array type.
[type.slice]
### Slice types

[type.slice.syntax]
Syntax
SliceType → [ Type ]

Show syntax diagrams

[type.slice.intro]
A slice is a dynamically sized type representing a ‘view’ into a sequence of elements of type T. The slice type is written as [T].
[type.slice.unsized]
Slice types are generally used through pointer types. For example:
&[T]: a ‘shared slice’, often just called a ‘slice’. It doesn’t own the data it points to; it borrows it.
&mut [T]: a ‘mutable slice’. It mutably borrows the data it points to.
Box<[T]>: a ‘boxed slice’
Examples:
// A heap-allocated array, coerced to a slice
let boxed_array: Box<[i32]> = Box::new([1, 2, 3]);

// A (shared) slice into an array
let slice: &[i32] = &boxed_array[..];
[type.slice.safe]
All elements of slices are always initialized, and access to a slice is always bounds-checked in safe methods and operators.
[type.struct]
### Struct types

[type.struct.intro]
A struct type is a heterogeneous product of other types, called the fields of the type.1
[type.struct.constructor]
New instances of a struct can be constructed with a struct expression.
[type.struct.layout]
The memory layout of a struct is undefined by default to allow for compiler optimizations like field reordering, but it can be fixed with the repr attribute. In either case, fields may be given in any order in a corresponding struct expression; the resulting struct value will always have the same memory layout.
[type.struct.field-visibility]
The fields of a struct may be qualified by visibility modifiers, to allow access to data in a struct outside a module.
[type.struct.tuple]
A tuple struct type is just like a struct type, except that the fields are anonymous.
[type.struct.unit]
A unit-like struct type is like a struct type, except that it has no fields. The one value constructed by the associated struct expression is the only value that inhabits such a type.
struct types are analogous to struct types in C, the record types of the ML family, or the struct types of the Lisp family. ↩

[type.enum]
### Enumerated types

[type.enum.intro]
An enumerated type is a nominal, heterogeneous disjoint union type, denoted by the name of an enum item. 1
[type.enum.declaration]
An enum item declares both the type and a number of variants, each of which is independently named and has the syntax of a struct, tuple struct or unit-like struct.
[type.enum.constructor]
New instances of an enum can be constructed with a struct expression.
[type.enum.value]
Any enum value consumes as much memory as the largest variant for its corresponding enum type, as well as the size needed to store a discriminant.
[type.enum.name]
Enum types cannot be denoted structurally as types, but must be denoted by named reference to an enum item.
The enum type is analogous to a data constructor declaration in Haskell, or a pick ADT in Limbo. ↩

[type.union]
### Union types

[type.union.intro]
A union type is a nominal, heterogeneous C-like union, denoted by the name of a union item.
[type.union.access]
Unions have no notion of an “active field”. Instead, every union access transmutes parts of the content of the union to the type of the accessed field.
[type.union.safety]
Since transmutes can cause unexpected or undefined behaviour, unsafe is required to read from a union field.
[type.union.constraint]
Union field types are also restricted to a subset of types which ensures that they never need dropping. See the item documentation for further details.
[type.union.layout]
The memory layout of a union is undefined by default (in particular, fields do not have to be at offset 0), but the #[repr(...)] attribute can be used to fix a layout.
[type.fn-item]
### Function item types

[type.fn-item.intro]
When referred to, a function item, or the constructor of a tuple-like struct or enum variant, yields a zero-sized value of its function item type.
[type.fn-item.unique]
That type explicitly identifies the function - its name, its type arguments, and its early-bound lifetime arguments (but not its late-bound lifetime arguments, which are only assigned when the function is called) - so the value does not need to contain an actual function pointer, and no indirection is needed when the function is called.
[type.fn-item.name]
There is no syntax that directly refers to a function item type, but the compiler will display the type as something like fn(u32) -> i32 {fn_name} in error messages.
Because the function item type explicitly identifies the function, the item types of different functions - different items, or the same item with different generics - are distinct, and mixing them will create a type error:
fn foo<T>() { }
let x = &mut foo::<i32>;
*x = foo::<u32>; //~ ERROR mismatched types
[type.fn-item.coercion]
However, there is a coercion from function items to function pointers with the same signature, which is triggered not only when a function item is used when a function pointer is directly expected, but also when different function item types with the same signature meet in different arms of the same if or match:

// `foo_ptr_1` has function pointer type `fn()` here
let foo_ptr_1: fn() = foo::<i32>;

// ... and so does `foo_ptr_2` - this type-checks.
let foo_ptr_2 = if want_i32 {
    foo::<i32>
} else {
    foo::<u32>
};
[type.fn-item.traits]
All function items implement Copy, Clone, Send, and Sync.
Fn, FnMut, and FnOnce are implemented unless the function has any of the following:
an unsafe qualifier
a target_feature attribute
an ABI other than "Rust"
[type.closure]
### Closure types

[type.closure.intro]
A closure expression produces a closure value with a unique, anonymous type that cannot be written out. A closure type is approximately equivalent to a struct which contains the captured values. For instance, the following closure:
#[derive(Debug)]
struct Point { x: i32, y: i32 }
struct Rectangle { left_top: Point, right_bottom: Point }

fn f<F : FnOnce() -> String> (g: F) {
    println!("{}", g());
}

let mut rect = Rectangle {
    left_top: Point { x: 1, y: 1 },
    right_bottom: Point { x: 0, y: 0 }
};

let c = || {
    rect.left_top.x += 1;
    rect.right_bottom.x += 1;
    format!("{:?}", rect.left_top)
};
f(c); // Prints "Point { x: 2, y: 1 }".
generates a closure type roughly like the following:
// Note: This is not exactly how it is translated, this is only for
// illustration.

struct Closure<'a> {
    left_top : &'a mut Point,
    right_bottom_x : &'a mut i32,
}

impl<'a> FnOnce<()> for Closure<'a> {
    type Output = String;
    extern "rust-call" fn call_once(self, args: ()) -> String {
        self.left_top.x += 1;
        *self.right_bottom_x += 1;
        format!("{:?}", self.left_top)
    }
}
so that the call to f works as if it were:
f(Closure{ left_top: &mut rect.left_top, right_bottom_x: &mut rect.right_bottom.x });
[type.closure.capture]
Capture modes
[type.closure.capture.intro]
A capture mode determines how a place expression from the environment is borrowed or moved into the closure. The capture modes are:
Immutable borrow (ImmBorrow) — The place expression is captured as a shared reference.
Unique immutable borrow (UniqueImmBorrow) — This is similar to an immutable borrow, but must be unique as described below.
Mutable borrow (MutBorrow) — The place expression is captured as a mutable reference.
Move (ByValue) — The place expression is captured by moving the value into the closure.
[type.closure.capture.precedence]
Place expressions from the environment are captured from the first mode that is compatible with how the captured value is used inside the closure body. The mode is not affected by the code surrounding the closure, such as the lifetimes of involved variables or fields, or of the closure itself.
[type.closure.capture.copy]
Copy values
Values that implement Copy that are moved into the closure are captured with the ImmBorrow mode.
let x = [0; 1024];
let c = || {
    let y = x; // x captured by ImmBorrow
};
[type.closure.async.input]
Async input capture
Async closures always capture all input arguments, regardless of whether or not they are used within the body.
Capture Precision
[type.closure.capture.precision.capture-path]
A capture path is a sequence starting with a variable from the environment followed by zero or more place projections that were applied to that variable.
[type.closure.capture.precision.place-projection]
A place projection is a field access, tuple index, dereference (and automatic dereferences), or array or slice index expression applied to a variable.
[type.closure.capture.precision.intro]
The closure borrows or moves the capture path, which may be truncated based on the rules described below.
For example:
struct SomeStruct {
    f1: (i32, i32),
}
let s = SomeStruct { f1: (1, 2) };

let c = || {
    let x = s.f1.1; // s.f1.1 captured by ImmBorrow
};
c();
Here the capture path is the local variable s, followed by a field access .f1, and then a tuple index .1. This closure captures an immutable borrow of s.f1.1.
[type.closure.capture.precision.shared-prefix]
Shared prefix
In the case where a capture path and one of the ancestor’s of that path are both captured by a closure, the ancestor path is captured with the highest capture mode among the two captures, CaptureMode = max(AncestorCaptureMode, DescendantCaptureMode), using the strict weak ordering:
ImmBorrow < UniqueImmBorrow < MutBorrow < ByValue
Note that this might need to be applied recursively.
// In this example, there are three different capture paths with a shared ancestor:
let s = String::from("S");
let t = (s, String::from("T"));
let mut u = (t, String::from("U"));

let c = || {
    println!("{:?}", u); // u captured by ImmBorrow
    u.1.truncate(0); // u.0 captured by MutBorrow
    move_value(u.0.0); // u.0.0 captured by ByValue
};
c();
Overall this closure will capture u by ByValue.
[type.closure.capture.precision.dereference-shared]
Rightmost shared reference truncation
The capture path is truncated at the rightmost dereference in the capture path if the dereference is applied to a shared reference.
This truncation is allowed because fields that are read through a shared reference will always be read via a shared reference or a copy. This helps reduce the size of the capture when the extra precision does not yield any benefit from a borrow checking perspective.
The reason it is the rightmost dereference is to help avoid a shorter lifetime than is necessary. Consider the following example:
struct Int(i32);
struct B<'a>(&'a i32);

struct MyStruct<'a> {
   a: &'static Int,
   b: B<'a>,
}

fn foo<'a, 'b>(m: &'a MyStruct<'b>) -> impl FnMut() + 'static {
    let c = || drop(&m.a.0);
    c
}
If this were to capture m, then the closure would no longer outlive 'static, since m is constrained to 'a. Instead, it captures (*(*m).a) by ImmBorrow.
[type.closure.capture.precision.wildcard]
Wildcard pattern bindings
Closures only capture data that needs to be read. Binding a value with a wildcard pattern does not count as a read, and thus won’t be captured. For example, the following closures will not capture x:
let x = String::from("hello");
let c = || {
    let _ = x;  // x is not captured
};
c();

let c = || match x {  // x is not captured
    _ => println!("Hello World!")
};
c();
This also includes destructuring of tuples, structs, and enums. Fields matched with the RestPattern or StructPatternEtCetera are also not considered as read, and thus those fields will not be captured. The following illustrates some of these:
let x = (String::from("a"), String::from("b"));
let c = || {
    let (first, ..) = x;  // captures `x.0` ByValue
};
// The first tuple field has been moved into the closure.
// The second tuple field is still accessible.
println!("{:?}", x.1);
c();
struct Example {
    f1: String,
    f2: String,
}

let e = Example {
    f1: String::from("first"),
    f2: String::from("second"),
};
let c = || {
    let Example { f2, .. } = e; // captures `e.f2` ByValue
};
// Field f2 cannot be accessed since it is moved into the closure.
// Field f1 is still accessible.
println!("{:?}", e.f1);
c();
[type.closure.capture.precision.wildcard.array-slice]
Partial captures of arrays and slices are not supported; the entire slice or array is always captured even if used with wildcard pattern matching, indexing, or sub-slicing. For example:
#[derive(Debug)]
struct Example;
let x = [Example, Example];

let c = || {
    let [first, _] = x; // captures all of `x` ByValue
};
c();
println!("{:?}", x[1]); // ERROR: borrow of moved value: `x`
[type.closure.capture.precision.wildcard.initialized]
Values that are matched with wildcards must still be initialized.
let x: i32;
let c = || {
    let _ = x; // ERROR: used binding `x` isn't initialized
};
[type.closure.capture.precision.move-dereference]
Capturing references in move contexts
Because it is not allowed to move fields out of a reference, move closures will only capture the prefix of a capture path that runs up to, but not including, the first dereference of a reference. The reference itself will be moved into the closure.
struct T(String, String);

let mut t = T(String::from("foo"), String::from("bar"));
let t_mut_ref = &mut t;
let mut c = move || {
    t_mut_ref.0.push_str("123"); // captures `t_mut_ref` ByValue
};
c();
[type.closure.capture.precision.raw-pointer-dereference]
Raw pointer dereference
Because it is unsafe to dereference a raw pointer, closures will only capture the prefix of a capture path that runs up to, but not including, the first dereference of a raw pointer.
struct T(String, String);

let t = T(String::from("foo"), String::from("bar"));
let t_ptr = &t as *const T;

let c = || unsafe {
    println!("{}", (*t_ptr).0); // captures `t_ptr` by ImmBorrow
};
c();
[type.closure.capture.precision.union]
Union fields
Because it is unsafe to access a union field, closures will only capture the prefix of a capture path that runs up to the union itself.
union U {
    a: (i32, i32),
    b: bool,
}
let u = U { a: (123, 456) };

let c = || {
    let x = unsafe { u.a.0 }; // captures `u` ByValue
};
c();

// This also includes writing to fields.
let mut u = U { a: (123, 456) };

let mut c = || {
    u.b = true; // captures `u` with MutBorrow
};
c();
[type.closure.capture.precision.unaligned]
Reference into unaligned structs
Because it is undefined behavior to create references to unaligned fields in a structure, closures will only capture the prefix of the capture path that runs up to, but not including, the first field access into a structure that uses the packed representation. This includes all fields, even those that are aligned, to protect against compatibility concerns should any of the fields in the structure change in the future.
#[repr(packed)]
struct T(i32, i32);

let t = T(2, 5);
let c = || {
    let a = t.0; // captures `t` with ImmBorrow
};
// Copies out of `t` are ok.
let (a, b) = (t.0, t.1);
c();
Similarly, taking the address of an unaligned field also captures the entire struct:
#[repr(packed)]
struct T(String, String);

let mut t = T(String::new(), String::new());
let c = || {
    let a = std::ptr::addr_of!(t.1); // captures `t` with ImmBorrow
};
let a = t.0; // ERROR: cannot move out of `t.0` because it is borrowed
c();
but the above works if it is not packed since it captures the field precisely:
struct T(String, String);

let mut t = T(String::new(), String::new());
let c = || {
    let a = std::ptr::addr_of!(t.1); // captures `t.1` with ImmBorrow
};
// The move here is allowed.
let a = t.0;
c();
[type.closure.capture.precision.box-deref]
Box vs other Deref implementations
The implementation of the Deref trait for Box is treated differently from other Deref implementations, as it is considered a special entity.
For example, let us look at examples involving Rc and Box. The *rc is desugared to a call to the trait method deref defined on Rc, but since *box is treated differently, it is possible to do a precise capture of the contents of the Box.
[type.closure.capture.precision.box-non-move.not-moved]
Box with non-move closure
In a non-move closure, if the contents of the Box are not moved into the closure body, the contents of the Box are precisely captured.
struct S(String);

let b = Box::new(S(String::new()));
let c_box = || {
    let x = &(*b).0; // captures `(*b).0` by ImmBorrow
};
c_box();

// Contrast `Box` with another type that implements Deref:
let r = std::rc::Rc::new(S(String::new()));
let c_rc = || {
    let x = &(*r).0; // captures `r` by ImmBorrow
};
c_rc();
[type.closure.capture.precision.box-non-move.moved]
However, if the contents of the Box are moved into the closure, then the box is entirely captured. This is done so the amount of data that needs to be moved into the closure is minimized.
// This is the same as the example above except the closure
// moves the value instead of taking a reference to it.

struct S(String);

let b = Box::new(S(String::new()));
let c_box = || {
    let x = (*b).0; // captures `b` with ByValue
};
c_box();
[type.closure.capture.precision.box-move.read]
Box with move closure
Similarly to moving contents of a Box in a non-move closure, reading the contents of a Box in a move closure will capture the Box entirely.
struct S(i32);

let b = Box::new(S(10));
let c_box = move || {
    let x = (*b).0; // captures `b` with ByValue
};
[type.closure.unique-immutable]
Unique immutable borrows in captures
Captures can occur by a special kind of borrow called a unique immutable borrow, which cannot be used anywhere else in the language and cannot be written out explicitly. It occurs when modifying the referent of a mutable reference, as in the following example:
let mut b = false;
let x = &mut b;
let mut c = || {
    // An ImmBorrow and a MutBorrow of `x`.
    let a = &x;
    *x = true; // `x` captured by UniqueImmBorrow
};
// The following line is an error:
// let y = &x;
c();
// However, the following is OK.
let z = &x;
In this case, borrowing x mutably is not possible, because x is not mut. But at the same time, borrowing x immutably would make the assignment illegal, because a & &mut reference might not be unique, so it cannot safely be used to modify a value. So a unique immutable borrow is used: it borrows x immutably, but like a mutable borrow, it must be unique.
In the above example, uncommenting the declaration of y will produce an error because it would violate the uniqueness of the closure’s borrow of x; the declaration of z is valid because the closure’s lifetime has expired at the end of the block, releasing the borrow.
[type.closure.call]
Call traits and coercions
[type.closure.call.intro]
Closure types all implement FnOnce, indicating that they can be called once by consuming ownership of the closure. Additionally, some closures implement more specific call traits:
[type.closure.call.fn-mut]
A closure which does not move out of any captured variables implements FnMut, indicating that it can be called by mutable reference.
[type.closure.call.fn]
A closure which does not mutate or move out of any captured variables implements Fn, indicating that it can be called by shared reference.
Note

move closures may still implement Fn or FnMut, even though they capture variables by move. This is because the traits implemented by a closure type are determined by what the closure does with captured values, not how it captures them.
[type.closure.non-capturing]
Non-capturing closures are closures that don’t capture anything from their environment. Non-async, non-capturing closures can be coerced to function pointers (e.g., fn()) with the matching signature.
let add = |x, y| x + y;

let mut x = add(5,7);

type Binop = fn(i32, i32) -> i32;
let bo: Binop = add;
x = bo(5,7);
[type.closure.async.traits]
Async closure traits
[type.closure.async.traits.fn-family]
Async closures have a further restriction of whether or not they implement FnMut or Fn.
The Future returned by the async closure has similar capturing characteristics as a closure. It captures place expressions from the async closure based on how they are used. The async closure is said to be lending to its Future if it has either of the following properties:
The Future includes a mutable capture.
The async closure captures by value, except when the value is accessed with a dereference projection.
If the async closure is lending to its Future, then FnMut and Fn are not implemented. FnOnce is always implemented.
Example: The first clause for a mutable capture can be illustrated with the following:

fn takes_callback<Fut: Future>(c: impl FnMut() -> Fut) {}

fn f() {
    let mut x = 1i32;
    let c = async || {
        x = 2;  // x captured with MutBorrow
    };
    takes_callback(c);  // ERROR: async closure does not implement `FnMut`
}
The second clause for a regular value capture can be illustrated with the following:

fn takes_callback<Fut: Future>(c: impl Fn() -> Fut) {}

fn f() {
    let x = &1i32;
    let c = async move || {
        let a = x + 2;  // x captured ByValue
    };
    takes_callback(c);  // ERROR: async closure does not implement `Fn`
}
The exception of the the second clause can be illustrated by using a dereference, which does allow Fn and FnMut to be implemented:

fn takes_callback<Fut: Future>(c: impl Fn() -> Fut) {}

fn f() {
    let x = &1i32;
    let c = async move || {
        let a = *x + 2;
    };
    takes_callback(c);  // OK: implements `Fn`
}
[type.closure.async.traits.async-family]
Async closures implement AsyncFn, AsyncFnMut, and AsyncFnOnce in an analogous way as regular closures implement Fn, FnMut, and FnOnce; that is, depending on the use of the captured variables in its body.
[type.closure.traits]
Other traits
[type.closure.traits.intro]
All closure types implement Sized. Additionally, closure types implement the following traits if allowed to do so by the types of the captures it stores:
Clone
Copy
Sync
Send
[type.closure.traits.behavior]
The rules for Send and Sync match those for normal struct types, while Clone and Copy behave as if derived. For Clone, the order of cloning of the captured values is left unspecified.
Because captures are often by reference, the following general rules arise:
A closure is Sync if all captured values are Sync.
A closure is Send if all values captured by non-unique immutable reference are Sync, and all values captured by unique immutable or mutable reference, copy, or move are Send.
A closure is Clone or Copy if it does not capture any values by unique immutable or mutable reference, and if all values it captures by copy or move are Clone or Copy, respectively.
[type.closure.drop-order]
Drop Order
If a closure captures a field of a composite types such as structs, tuples, and enums by value, the field’s lifetime would now be tied to the closure. As a result, it is possible for disjoint fields of a composite types to be dropped at different times.
{
    let tuple =
      (String::from("foo"), String::from("bar")); // --+
    { //                                               |
        let c = || { // ----------------------------+  |
            // tuple.0 is captured into the closure |  |
            drop(tuple.0); //                       |  |
        }; //                                       |  |
    } // 'c' and 'tuple.0' dropped here ------------+  |
} // tuple.1 dropped here -----------------------------+
[type.closure.capture.precision.edition2018.entirety]
Edition 2018 and before
Closure types difference
In Edition 2018 and before, closures always capture a variable in its entirety, without its precise capture path. This means that for the example used in the Closure types section, the generated closure type would instead look something like this:
struct Closure<'a> {
    rect : &'a mut Rectangle,
}

impl<'a> FnOnce<()> for Closure<'a> {
    type Output = String;
    extern "rust-call" fn call_once(self, args: ()) -> String {
        self.rect.left_top.x += 1;
        self.rect.right_bottom.x += 1;
        format!("{:?}", self.rect.left_top)
    }
}
and the call to f would work as follows:
f(Closure { rect: rect });
[type.closure.capture.precision.edition2018.composite]
Capture precision difference
Composite types such as structs, tuples, and enums are always captured in its entirety, not by individual fields. As a result, it may be necessary to borrow into a local variable in order to capture a single field:
struct SetVec {
    set: HashSet<u32>,
    vec: Vec<u32>
}

impl SetVec {
    fn populate(&mut self) {
        let vec = &mut self.vec;
        self.set.iter().for_each(|&n| {
            vec.push(n);
        })
    }
}
If, instead, the closure were to use self.vec directly, then it would attempt to capture self by mutable reference. But since self.set is already borrowed to iterate over, the code would not compile.
[type.closure.capture.precision.edition2018.move]
If the move keyword is used, then all captures are by move or, for Copy types, by copy, regardless of whether a borrow would work. The move keyword is usually used to allow the closure to outlive the captured values, such as if the closure is being returned or used to spawn a new thread.
[type.closure.capture.precision.edition2018.wildcard]
Regardless of if the data will be read by the closure, i.e. in case of wild card patterns, if a variable defined outside the closure is mentioned within the closure the variable will be captured in its entirety.
[type.closure.capture.precision.edition2018.drop-order]
Drop order difference
As composite types are captured in their entirety, a closure which captures one of those composite types by value would drop the entire captured variable at the same time as the closure gets dropped.
{
    let tuple =
      (String::from("foo"), String::from("bar"));
    {
        let c = || { // --------------------------+
            // tuple is captured into the closure |
            drop(tuple.0); //                     |
        }; //                                     |
    } // 'c' and 'tuple' dropped here ------------+
}
[type.pointer]
### Pointer types

[type.pointer.intro]
All pointers are explicit first-class values. They can be moved or copied, stored into data structs, and returned from functions.
[type.pointer.reference]
References (& and &mut)
[type.pointer.reference.syntax]
Syntax
ReferenceType → & Lifetime? mut? TypeNoBounds

Show syntax diagrams

[type.pointer.reference.shared]
Shared references (&)
[type.pointer.reference.shared.intro]
Shared references point to memory which is owned by some other value.
[type.pointer.reference.shared.constraint-mutation]
## Interior mutability
[type.pointer.reference.shared.copy]
Copying a reference is a “shallow” operation: it involves only copying the pointer itself, that is, pointers are Copy. Releasing a reference has no effect on the value it points to, but referencing of a temporary value will keep it alive during the scope of the reference itself.
[type.pointer.reference.mut]
Mutable references (&mut)
[type.pointer.reference.mut.intro]
Mutable references point to memory which is owned by some other value. A mutable reference type is written &mut type or &'a mut type.
[type.pointer.reference.mut.copy]
A mutable reference (that hasn’t been borrowed) is the only way to access the value it points to, so is not Copy.
[type.pointer.raw]
Raw pointers (*const and *mut)
[type.pointer.raw.syntax]
Syntax
RawPointerType → * ( mut | const ) TypeNoBounds

Show syntax diagrams

[type.pointer.raw.intro]
Raw pointers are pointers without safety or liveness guarantees. Raw pointers are written as *const T or *mut T. For example *const i32 means a raw pointer to a 32-bit integer.
[type.pointer.raw.copy]
Copying or dropping a raw pointer has no effect on the lifecycle of any other value.
[type.pointer.raw.safety]
Dereferencing a raw pointer is an unsafe operation.
This can also be used to convert a raw pointer to a reference by reborrowing it (&* or &mut *). Raw pointers are generally discouraged; they exist to support interoperability with foreign code, and writing performance-critical or low-level functions.
[type.pointer.raw.cmp]
When comparing raw pointers they are compared by their address, rather than by what they point to. When comparing raw pointers to dynamically sized types they also have their additional data compared.
[type.pointer.raw.constructor]
Raw pointers can be created directly using &raw const for *const pointers and &raw mut for *mut pointers.
[type.pointer.smart]
Smart Pointers
The standard library contains additional ‘smart pointer’ types beyond references and raw pointers.
[type.pointer.validity]
Bit validity
[type.pointer.validity.pointer-fragment]
Despite pointers and references being similar to usizes in the machine code emitted on most platforms, the semantics of transmuting a reference or pointer type to a non-pointer type is currently undecided. Thus, it may not be valid to transmute a pointer or reference type, P, to a [u8; size_of::<P>()].
[type.pointer.validity.raw]
For thin raw pointers (i.e., for P = *const T or P = *mut T for T: Sized), the inverse direction (transmuting from an integer or array of integers to P) is always valid. However, the pointer produced via such a transmutation may not be dereferenced (not even if T has size zero).
[type.fn-pointer]
### Function pointer types

[type.fn-pointer.syntax]
Syntax
BareFunctionType →
    ForLifetimes? FunctionTypeQualifiers fn
       ( FunctionParametersMaybeNamedVariadic? ) BareFunctionReturnType?

FunctionTypeQualifiers → unsafe? ( extern Abi? )?

BareFunctionReturnType → -> TypeNoBounds

FunctionParametersMaybeNamedVariadic →
    MaybeNamedFunctionParameters | MaybeNamedFunctionParametersVariadic

MaybeNamedFunctionParameters →
    MaybeNamedParam ( , MaybeNamedParam )* ,?

MaybeNamedParam →
    OuterAttribute* ( ( IDENTIFIER | _ ) : )? Type

MaybeNamedFunctionParametersVariadic →
    ( MaybeNamedParam , )* MaybeNamedParam , OuterAttribute* ...

Show syntax diagrams

[type.fn-pointer.intro]
Function pointer types, written using the fn keyword, refer to a function whose identity is not necessarily known at compile-time.
An example where Binop is defined as a function pointer type:
fn add(x: i32, y: i32) -> i32 {
    x + y
}

let mut x = add(5,7);

type Binop = fn(i32, i32) -> i32;
let bo: Binop = add;
x = bo(5,7);
[type.fn-pointer.coercion]
Function pointers can be created via a coercion from both function items and non-capturing, non-async closures.
[type.fn-pointer.qualifiers]
The unsafe qualifier indicates that the type’s value is an unsafe function, and the extern qualifier indicates it is an extern function.
[type.fn-pointer.constraint-variadic]
Variadic parameters can only be specified with extern function types with the "C" or "cdecl" calling convention.
This also includes the corresponding -unwind variants.
[type.fn-pointer.attributes]
Attributes on function pointer parameters
Attributes on function pointer parameters follow the same rules and restrictions as regular function parameters.
[type.trait-object]
Trait objects

[type.trait-object.syntax]
Syntax
TraitObjectType → dyn? TypeParamBounds

TraitObjectTypeOneBound → dyn? TraitBound

Show syntax diagrams

[type.trait-object.intro]
A trait object is an opaque value of another type that implements a set of traits. The set of traits is made up of a dyn compatible base trait plus any number of auto traits.
[type.trait-object.impls]
Trait objects implement the base trait, its auto traits, and any supertraits of the base trait.
[type.trait-object.name]
Trait objects are written as the keyword dyn followed by a set of trait bounds, but with the following restrictions on the trait bounds.
[type.trait-object.constraint]
There may not be more than one non-auto trait, no more than one lifetime, and opt-out bounds (e.g. ?Sized) are not allowed. Furthermore, paths to traits may be parenthesized.
For example, given a trait Trait, the following are all trait objects:
dyn Trait
dyn Trait + Send
dyn Trait + Send + Sync
dyn Trait + 'static
dyn Trait + Send + 'static
dyn Trait +
dyn 'static + Trait.
dyn (Trait)
[type.trait-object.syntax-edition2021]
2021
Edition differences

Before the 2021 edition, the dyn keyword may be omitted.
[type.trait-object.syntax-edition2018]
2018
Edition differences

In the 2015 edition, if the first bound of the trait object is a path that starts with ::, then the dyn will be treated as a part of the path. The first path can be put in parenthesis to get around this. As such, if you want a trait object with the trait ::your_module::Trait, you should write it as dyn (::your_module::Trait).

Beginning in the 2018 edition, dyn is a true keyword and is not allowed in paths, so the parentheses are not necessary.
[type.trait-object.alias]
### Trait object types
[type.trait-object.unsized]
Due to the opaqueness of which concrete type the value is of, trait objects are dynamically sized types. Like all DSTs, trait objects are used behind some type of pointer; for example &dyn SomeTrait or Box<dyn SomeTrait>. Each instance of a pointer to a trait object includes:
a pointer to an instance of a type T that implements SomeTrait
a virtual method table, often just called a vtable, which contains, for each method of SomeTrait and its supertraits that T implements, a pointer to T’s implementation (i.e. a function pointer).
The purpose of trait objects is to permit “late binding” of methods. Calling a method on a trait object results in virtual dispatch at runtime: that is, a function pointer is loaded from the trait object vtable and invoked indirectly. The actual implementation for each vtable entry can vary on an object-by-object basis.
An example of a trait object:
trait Printable {
    fn stringify(&self) -> String;
}

impl Printable for i32 {
    fn stringify(&self) -> String { self.to_string() }
}

fn print(a: Box<dyn Printable>) {
    println!("{}", a.stringify());
}

fn main() {
    print(Box::new(10) as Box<dyn Printable>);
}
In this example, the trait Printable occurs as a trait object in both the type signature of print, and the cast expression in main.
[type.trait-object.lifetime-bounds]
Trait Object Lifetime Bounds
Since a trait object can contain references, the lifetimes of those references need to be expressed as part of the trait object. This lifetime is written as Trait + 'a. There are defaults that allow this lifetime to usually be inferred with a sensible choice.
[type.impl-trait]
Impl trait

[type.impl-trait.syntax]
Syntax
ImplTraitType → impl TypeParamBounds

ImplTraitTypeOneBound → impl TraitBound

Show syntax diagrams

[type.impl-trait.intro]
impl Trait provides ways to specify unnamed but concrete types that implement a specific trait. It can appear in two sorts of places: argument position (where it can act as an anonymous type parameter to functions), and return position (where it can act as an abstract return type).
trait Trait {}

// argument position: anonymous type parameter
fn foo(arg: impl Trait) {
}

// return position: abstract return type
fn bar() -> impl Trait {
}
[type.impl-trait.param]
Anonymous type parameters
Note

This is often called “impl Trait in argument position”. (The term “parameter” is more correct here, but “impl Trait in argument position” is the phrasing used during the development of this feature, and it remains in parts of the implementation.)
[type.impl-trait.param.intro]
Functions can use impl followed by a set of trait bounds to declare a parameter as having an anonymous type. The caller must provide a type that satisfies the bounds declared by the anonymous type parameter, and the function can only use the methods available through the trait bounds of the anonymous type parameter.
For example, these two forms are almost equivalent:
trait Trait {}

// generic type parameter
fn with_generic_type<T: Trait>(arg: T) {
}

// impl Trait in argument position
fn with_impl_trait(arg: impl Trait) {
}
[type.impl-trait.param.generic]
That is, impl Trait in argument position is syntactic sugar for a generic type parameter like <T: Trait>, except that the type is anonymous and doesn’t appear in the GenericParams list.
Note

For function parameters, generic type parameters and impl Trait are not exactly equivalent. With a generic parameter such as <T: Trait>, the caller has the option to explicitly specify the generic argument for T at the call site using GenericArgs, for example, foo::<usize>(1). Changing a parameter from either one to the other can constitute a breaking change for the callers of a function, since this changes the number of generic arguments.
[type.impl-trait.return]
Abstract return types
Note

This is often called “impl Trait in return position”.
[type.impl-trait.return.intro]
Functions can use impl Trait to return an abstract return type. These types stand in for another concrete type where the caller may only use the methods declared by the specified Trait.
[type.impl-trait.return.constraint-body]
Each possible return value from the function must resolve to the same concrete type.
impl Trait in return position allows a function to return an unboxed abstract type. This is particularly useful with closures and iterators. For example, closures have a unique, un-writable type. Previously, the only way to return a closure from a function was to use a trait object:
fn returns_closure() -> Box<dyn Fn(i32) -> i32> {
    Box::new(|x| x + 1)
}
This could incur performance penalties from heap allocation and dynamic dispatch. It wasn’t possible to fully specify the type of the closure, only to use the Fn trait. That means that the trait object is necessary. However, with impl Trait, it is possible to write this more simply:
fn returns_closure() -> impl Fn(i32) -> i32 {
    |x| x + 1
}
which also avoids the drawbacks of using a boxed trait object.
Similarly, the concrete types of iterators could become very complex, incorporating the types of all previous iterators in a chain. Returning impl Iterator means that a function only exposes the Iterator trait as a bound on its return type, instead of explicitly specifying all of the other iterator types involved.
[type.impl-trait.return-in-trait]
Return-position impl Trait in traits and trait implementations
[type.impl-trait.return-in-trait.intro]
Functions in traits may also use impl Trait as a syntax for an anonymous associated type.
[type.impl-trait.return-in-trait.desugaring]
Every impl Trait in the return type of an associated function in a trait is desugared to an anonymous associated type. The return type that appears in the implementation’s function signature is used to determine the value of the associated type.
[type.impl-trait.generic-captures]
Capturing
Behind each return-position impl Trait abstract type is some hidden concrete type. For this concrete type to use a generic parameter, that generic parameter must be captured by the abstract type.
[type.impl-trait.generic-capture.auto]
Automatic capturing
[type.impl-trait.generic-capture.auto.intro]
Return-position impl Trait abstract types automatically capture all in-scope generic parameters, including generic type, const, and lifetime parameters (including higher-ranked ones).
[type.impl-trait.generic-capture.edition2024]
2024
Edition differences

Before the 2024 edition, on free functions and on associated functions and methods of inherent impls, generic lifetime parameters that do not appear in the bounds of the abstract return type are not automatically captured.
[type.impl-trait.generic-capture.precise]
Precise capturing
[type.impl-trait.generic-capture.precise.use]
The set of generic parameters captured by a return-position impl Trait abstract type may be explicitly controlled with a use<..> bound. If present, only the generic parameters listed in the use<..> bound will be captured. E.g.:
fn capture<'a, 'b, T>(x: &'a (), y: T) -> impl Sized + use<'a, T> {
  //                                      ~~~~~~~~~~~~~~~~~~~~~~~
  //                                     Captures `'a` and `T` only.
  (x, y)
}
[type.impl-trait.generic-capture.precise.constraint-single]
Currently, only one use<..> bound may be present in a bounds list, all in-scope type and const generic parameters must be included, and all lifetime parameters that appear in other bounds of the abstract type must be included.
[type.impl-trait.generic-capture.precise.constraint-lifetime]
Within the use<..> bound, any lifetime parameters present must appear before all type and const generic parameters, and the elided lifetime ('_) may be present if it is otherwise allowed to appear within the impl Trait return type.
[type.impl-trait.generic-capture.precise.constraint-param-impl-trait]
Because all in-scope type parameters must be included by name, a use<..> bound may not be used in the signature of items that use argument-position impl Trait, as those items have anonymous type parameters in scope.
[type.impl-trait.generic-capture.precise.constraint-in-trait]
Any use<..> bound that is present in an associated function in a trait definition must include all generic parameters of the trait, including the implicit Self generic type parameter of the trait.
Differences between generics and impl Trait in return position
In argument position, impl Trait is very similar in semantics to a generic type parameter. However, there are significant differences between the two in return position. With impl Trait, unlike with a generic type parameter, the function chooses the return type, and the caller cannot choose the return type.
The function:
fn foo<T: Trait>() -> T {
    // ...
}
allows the caller to determine the return type, T, and the function returns that type.
The function:
fn foo() -> impl Trait {
    // ...
}
doesn’t allow the caller to determine the return type. Instead, the function chooses the return type, but only promises that it will implement Trait.
[type.impl-trait.constraint]
Limitations
impl Trait can only appear as a parameter or return type of a non-extern function. It cannot be the type of a let binding, field type, or appear inside a type alias.
[type.generic]
### Type parameters

Within the body of an item that has type parameter declarations, the names of its type parameters are types:
fn to_vec<A: Clone>(xs: &[A]) -> Vec<A> {
    if xs.is_empty() {
        return vec![];
    }
    let first: A = xs[0].clone();
    let mut rest: Vec<A> = to_vec(&xs[1..]);
    rest.insert(0, first);
    rest
}
Here, first has type A, referring to to_vec’s A type parameter; and rest has type Vec<A>, a vector with element type A.
[type.inferred]
### Inferred type

[type.inferred.syntax]
Syntax
InferredType → _

Show syntax diagrams

[type.inferred.intro]
The inferred type asks the compiler to infer the type if possible based on the surrounding information available.
[type.inferred.constraint]
It cannot be used in item signatures.
It is often used in generic arguments:
let x: Vec<_> = (0..10).collect();
[dynamic-sized]
## Dynamically Sized Types

[dynamic-sized.intro]
Most types have a fixed size that is known at compile time and implement the trait Sized. A type with a size that is known only at run-time is called a dynamically sized type (DST) or, informally, an unsized type. Slices, trait objects, and str are examples of DSTs.
[dynamic-sized.restriction]
Such types can only be used in certain cases:
[dynamic-sized.pointer-types]
Pointer types to DSTs are sized but have twice the size of pointers to sized types
Pointers to slices and str also store the number of elements.
Pointers to trait objects also store a pointer to a vtable.
[dynamic-sized.question-sized]
DSTs can be provided as type arguments to generic type parameters having the special ?Sized bound. They can also be used for associated type definitions when the corresponding associated type declaration has a ?Sized bound. By default, any type parameter or associated type has a Sized bound, unless it is relaxed using ?Sized.
[dynamic-sized.trait-impl]
Traits may be implemented for DSTs. Unlike with generic type parameters, Self: ?Sized is the default in trait definitions.
[dynamic-sized.struct-field]
Structs may contain a DST as the last field; this makes the struct itself a DST.
Note

Variables, function parameters, const items, and static items must be Sized.
[layout]
## Type layout

[layout.intro]
The layout of a type is its size, alignment, and the relative offsets of its fields. For enums, how the discriminant is laid out and interpreted is also part of type layout.
[layout.guarantees]
Type layout can be changed with each compilation. Instead of trying to document exactly what is done, we only document what is guaranteed today.
Note that even types with the same layout can still differ in how they are passed across function boundaries. For function call ABI compatibility of types, see here.
[layout.properties]
Size and Alignment
All values have an alignment and size.
[layout.properties.align]
The alignment of a value specifies what addresses are valid to store the value at. A value of alignment n must only be stored at an address that is a multiple of n. For example, a value with an alignment of 2 must be stored at an even address, while a value with an alignment of 1 can be stored at any address. Alignment is measured in bytes, and must be at least 1, and always a power of 2. The alignment of a value can be checked with the align_of_val function.
[layout.properties.size]
The size of a value is the offset in bytes between successive elements in an array with that item type including alignment padding. The size of a value is always a multiple of its alignment. Note that some types are zero-sized; 0 is considered a multiple of any alignment (for example, on some platforms, the type [u16; 0] has size 0 and alignment 2). The size of a value can be checked with the size_of_val function.
[layout.properties.sized]
Types where all values have the same size and alignment, and both are known at compile time, implement the Sized trait and can be checked with the size_of and align_of functions. Types that are not Sized are known as dynamically sized types. Since all values of a Sized type share the same size and alignment, we refer to those shared values as the size of the type and the alignment of the type respectively.
[layout.primitive]
Primitive Data Layout
[layout.primitive.size]
The size of most primitives is given in this table.
Type	size_of::<Type>()
bool	1
u8 / i8	1
u16 / i16	2
u32 / i32	4
u64 / i64	8
u128 / i128	16
usize / isize	See below
f32	4
f64	8
char	4
[layout.primitive.size-int]
usize and isize have a size big enough to contain every address on the target platform. For example, on a 32 bit target, this is 4 bytes, and on a 64 bit target, this is 8 bytes.
[layout.primitive.align]
The alignment of primitives is platform-specific. In most cases, their alignment is equal to their size, but it may be less. In particular, i128 and u128 are often aligned to 4 or 8 bytes even though their size is 16, and on many 32-bit platforms, i64, u64, and f64 are only aligned to 4 bytes, not 8.
[layout.pointer]
Pointers and References Layout
[layout.pointer.intro]
Pointers and references have the same layout. Mutability of the pointer or reference does not change the layout.
[layout.pointer.thin]
Pointers to sized types have the same size and alignment as usize.
[layout.pointer.unsized]
Pointers to unsized types are sized. The size and alignment is guaranteed to be at least equal to the size and alignment of a pointer.
Note

Though you should not rely on this, all pointers to DSTs are currently twice the size of the size of usize and have the same alignment.
[layout.array]
Array Layout
An array of [T; N] has a size of size_of::<T>() * N and the same alignment of T. Arrays are laid out so that the zero-based nth element of the array is offset from the start of the array by n * size_of::<T>() bytes.
[layout.slice]
Slice Layout
Slices have the same layout as the section of the array they slice.
Note

This is about the raw [T] type, not pointers (&[T], Box<[T]>, etc.) to slices.
[layout.str]
str Layout
String slices are a UTF-8 representation of characters that have the same layout as slices of type [u8]. A reference &str has the same layout as a reference &[u8].
[layout.tuple]
Tuple Layout
[layout.tuple.general]
Tuples are laid out according to the Rust representation.
[layout.tuple.unit]
The exception to this is the unit tuple (()), which is guaranteed as a zero-sized type to have a size of 0 and an alignment of 1.
[layout.trait-object]
Trait Object Layout
Trait objects have the same layout as the value the trait object is of.
Note

This is about the raw trait object types, not pointers (&dyn Trait, Box<dyn Trait>, etc.) to trait objects.
[layout.closure]
Closure Layout
Closures have no layout guarantees.
[layout.repr]
Representations
[layout.repr.intro]
All user-defined composite types (structs, enums, and unions) have a representation that specifies what the layout is for the type.
[layout.repr.kinds]
The possible representations for a type are:
Rust (default)
C
The primitive representations
transparent
[layout.repr.attribute]
The representation of a type can be changed by applying the repr attribute to it. The following example shows a struct with a C representation.
#[repr(C)]
struct ThreeInts {
    first: i16,
    second: i8,
    third: i32
}
[layout.repr.align-packed]
The alignment may be raised or lowered with the align and packed modifiers respectively. They alter the representation specified in the attribute. If no representation is specified, the default one is altered.
// Default representation, alignment lowered to 2.
#[repr(packed(2))]
struct PackedStruct {
    first: i16,
    second: i8,
    third: i32
}

// C representation, alignment raised to 8
#[repr(C, align(8))]
struct AlignedStruct {
    first: i16,
    second: i8,
    third: i32
}
Note

As a consequence of the representation being an attribute on the item, the representation does not depend on generic parameters. Any two types with the same name have the same representation. For example, Foo<Bar> and Foo<Baz> both have the same representation.
[layout.repr.inter-field]
The representation of a type can change the padding between fields, but does not change the layout of the fields themselves. For example, a struct with a C representation that contains a struct Inner with the Rust representation will not change the layout of Inner.
[layout.repr.rust]
The Rust Representation
[layout.repr.rust.intro]
The Rust representation is the default representation for nominal types without a repr attribute. Using this representation explicitly through a repr attribute is guaranteed to be the same as omitting the attribute entirely.
[layout.repr.rust.layout]
The only data layout guarantees made by this representation are those required for soundness. They are:
The fields are properly aligned.
The fields do not overlap.
The alignment of the type is at least the maximum alignment of its fields.
[layout.repr.rust.alignment]
Formally, the first guarantee means that the offset of any field is divisible by that field’s alignment.
[layout.repr.rust.field-storage]
The second guarantee means that the fields can be ordered such that the offset plus the size of any field is less than or equal to the offset of the next field in the ordering. The ordering does not have to be the same as the order in which the fields are specified in the declaration of the type.
Be aware that the second guarantee does not imply that the fields have distinct addresses: zero-sized types may have the same address as other fields in the same struct.
[layout.repr.rust.unspecified]
There are no other guarantees of data layout made by this representation.
[layout.repr.c]
The C Representation
[layout.repr.c.intro]
The C representation is designed for dual purposes. One purpose is for creating types that are interoperable with the C Language. The second purpose is to create types that you can soundly perform operations on that rely on data layout such as reinterpreting values as a different type.
Because of this dual purpose, it is possible to create types that are not useful for interfacing with the C programming language.
[layout.repr.c.constraint]
This representation can be applied to structs, unions, and enums. The exception is zero-variant enums for which the C representation is an error.
[layout.repr.c.struct]
#[repr(C)] Structs
[layout.repr.c.struct.align]
The alignment of the struct is the alignment of the most-aligned field in it.
[layout.repr.c.struct.size-field-offset]
The size and offset of fields is determined by the following algorithm.
Start with a current offset of 0 bytes.
For each field in declaration order in the struct, first determine the size and alignment of the field. If the current offset is not a multiple of the field’s alignment, then add padding bytes to the current offset until it is a multiple of the field’s alignment. The offset for the field is what the current offset is now. Then increase the current offset by the size of the field.
Finally, the size of the struct is the current offset rounded up to the nearest multiple of the struct’s alignment.
Here is this algorithm described in pseudocode.
/// Returns the amount of padding needed after `offset` to ensure that the
/// following address will be aligned to `alignment`.
fn padding_needed_for(offset: usize, alignment: usize) -> usize {
    let misalignment = offset % alignment;
    if misalignment > 0 {
        // round up to next multiple of `alignment`
        alignment - misalignment
    } else {
        // already a multiple of `alignment`
        0
    }
}

struct.alignment = struct.fields().map(|field| field.alignment).max();

let current_offset = 0;

for field in struct.fields_in_declaration_order() {
    // Increase the current offset so that it's a multiple of the alignment
    // of this field. For the first field, this will always be zero.
    // The skipped bytes are called padding bytes.
    current_offset += padding_needed_for(current_offset, field.alignment);

    struct[field].offset = current_offset;

    current_offset += field.size;
}

struct.size = current_offset + padding_needed_for(current_offset, struct.alignment);
Warning

This pseudocode uses a naive algorithm that ignores overflow issues for the sake of clarity. To perform memory layout computations in actual code, use Layout.
Note

This algorithm can produce zero-sized structs. In C, an empty struct declaration like struct Foo { } is illegal. However, both gcc and clang support options to enable such structs, and assign them size zero. C++, in contrast, gives empty structs a size of 1, unless they are inherited from or they are fields that have the [[no_unique_address]] attribute, in which case they do not increase the overall size of the struct.
[layout.repr.c.union]
#[repr(C)] Unions
[layout.repr.c.union.intro]
A union declared with #[repr(C)] will have the same size and alignment as an equivalent C union declaration in the C language for the target platform.
[layout.repr.c.union.size-align]
The union will have a size of the maximum size of all of its fields rounded to its alignment, and an alignment of the maximum alignment of all of its fields. These maximums may come from different fields.
#[repr(C)]
union Union {
    f1: u16,
    f2: [u8; 4],
}

assert_eq!(std::mem::size_of::<Union>(), 4);  // From f2
assert_eq!(std::mem::align_of::<Union>(), 2); // From f1

#[repr(C)]
union SizeRoundedUp {
   a: u32,
   b: [u16; 3],
}

assert_eq!(std::mem::size_of::<SizeRoundedUp>(), 8);  // Size of 6 from b,
                                                      // rounded up to 8 from
                                                      // alignment of a.
assert_eq!(std::mem::align_of::<SizeRoundedUp>(), 4); // From a
[layout.repr.c.enum]
#[repr(C)] Field-less Enums
For field-less enums, the C representation has the size and alignment of the default enum size and alignment for the target platform’s C ABI.
Note

The enum representation in C is implementation defined, so this is really a “best guess”. In particular, this may be incorrect when the C code of interest is compiled with certain flags.
Warning

There are crucial differences between an enum in the C language and Rust’s field-less enums with this representation. An enum in C is mostly a typedef plus some named constants; in other words, an object of an enum type can hold any integer value. For example, this is often used for bitflags in C. In contrast, Rust’s field-less enums can only legally hold the discriminant values, everything else is undefined behavior. Therefore, using a field-less enum in FFI to model a C enum is often wrong.
[layout.repr.c.adt]
#[repr(C)] Enums With Fields
[layout.repr.c.adt.intro]
The representation of a repr(C) enum with fields is a repr(C) struct with two fields, also called a “tagged union” in C:
[layout.repr.c.adt.tag]
a repr(C) version of the enum with all fields removed (“the tag”)
[layout.repr.c.adt.fields]
a repr(C) union of repr(C) structs for the fields of each variant that had them (“the payload”)
Note

Due to the representation of repr(C) structs and unions, if a variant has a single field there is no difference between putting that field directly in the union or wrapping it in a struct; any system which wishes to manipulate such an enum’s representation may therefore use whichever form is more convenient or consistent for them.
// This Enum has the same representation as ...
#[repr(C)]
enum MyEnum {
    A(u32),
    B(f32, u64),
    C { x: u32, y: u8 },
    D,
 }

// ... this struct.
#[repr(C)]
struct MyEnumRepr {
    tag: MyEnumDiscriminant,
    payload: MyEnumFields,
}

// This is the discriminant enum.
#[repr(C)]
enum MyEnumDiscriminant { A, B, C, D }

// This is the variant union.
#[repr(C)]
union MyEnumFields {
    A: MyAFields,
    B: MyBFields,
    C: MyCFields,
    D: MyDFields,
}

#[repr(C)]
#[derive(Copy, Clone)]
struct MyAFields(u32);

#[repr(C)]
#[derive(Copy, Clone)]
struct MyBFields(f32, u64);

#[repr(C)]
#[derive(Copy, Clone)]
struct MyCFields { x: u32, y: u8 }

// This struct could be omitted (it is a zero-sized type), and it must be in
// C/C++ headers.
#[repr(C)]
#[derive(Copy, Clone)]
struct MyDFields;
[layout.repr.primitive]
Primitive representations
[layout.repr.primitive.intro]
The primitive representations are the representations with the same names as the primitive integer types. That is: u8, u16, u32, u64, u128, usize, i8, i16, i32, i64, i128, and isize.
[layout.repr.primitive.constraint]
Primitive representations can only be applied to enumerations and have different behavior whether the enum has fields or no fields. It is an error for zero-variant enums to have a primitive representation. Combining two primitive representations together is an error.
[layout.repr.primitive.enum]
Primitive Representation of Field-less Enums
For field-less enums, primitive representations set the size and alignment to be the same as the primitive type of the same name. For example, a field-less enum with a u8 representation can only have discriminants between 0 and 255 inclusive.
[layout.repr.primitive.adt]
Primitive Representation of Enums With Fields
The representation of a primitive representation enum is a repr(C) union of repr(C) structs for each variant with a field. The first field of each struct in the union is the primitive representation version of the enum with all fields removed (“the tag”) and the remaining fields are the fields of that variant.
Note

This representation is unchanged if the tag is given its own member in the union, should that make manipulation more clear for you (although to follow the C++ standard the tag member should be wrapped in a struct).
// This enum has the same representation as ...
#[repr(u8)]
enum MyEnum {
    A(u32),
    B(f32, u64),
    C { x: u32, y: u8 },
    D,
 }

// ... this union.
#[repr(C)]
union MyEnumRepr {
    A: MyVariantA,
    B: MyVariantB,
    C: MyVariantC,
    D: MyVariantD,
}

// This is the discriminant enum.
#[repr(u8)]
#[derive(Copy, Clone)]
enum MyEnumDiscriminant { A, B, C, D }

#[repr(C)]
#[derive(Clone, Copy)]
struct MyVariantA(MyEnumDiscriminant, u32);

#[repr(C)]
#[derive(Clone, Copy)]
struct MyVariantB(MyEnumDiscriminant, f32, u64);

#[repr(C)]
#[derive(Clone, Copy)]
struct MyVariantC { tag: MyEnumDiscriminant, x: u32, y: u8 }

#[repr(C)]
#[derive(Clone, Copy)]
struct MyVariantD(MyEnumDiscriminant);
[layout.repr.primitive-c]
Combining primitive representations of enums with fields and #[repr(C)]
For enums with fields, it is also possible to combine repr(C) and a primitive representation (e.g., repr(C, u8)). This modifies the repr(C) by changing the representation of the discriminant enum to the chosen primitive instead. So, if you chose the u8 representation, then the discriminant enum would have a size and alignment of 1 byte.
The discriminant enum from the example earlier then becomes:
#[repr(C, u8)] // `u8` was added
enum MyEnum {
    A(u32),
    B(f32, u64),
    C { x: u32, y: u8 },
    D,
 }

// ...

#[repr(u8)] // So `u8` is used here instead of `C`
enum MyEnumDiscriminant { A, B, C, D }

// ...
For example, with a repr(C, u8) enum it is not possible to have 257 unique discriminants (“tags”) whereas the same enum with only a repr(C) attribute will compile without any problems.
Using a primitive representation in addition to repr(C) can change the size of an enum from the repr(C) form:
#[repr(C)]
enum EnumC {
    Variant0(u8),
    Variant1,
}

#[repr(C, u8)]
enum Enum8 {
    Variant0(u8),
    Variant1,
}

#[repr(C, u16)]
enum Enum16 {
    Variant0(u8),
    Variant1,
}

// The size of the C representation is platform dependent
assert_eq!(std::mem::size_of::<EnumC>(), 8);
// One byte for the discriminant and one byte for the value in Enum8::Variant0
assert_eq!(std::mem::size_of::<Enum8>(), 2);
// Two bytes for the discriminant and one byte for the value in Enum16::Variant0
// plus one byte of padding.
assert_eq!(std::mem::size_of::<Enum16>(), 4);
[layout.repr.alignment]
The alignment modifiers
[layout.repr.alignment.intro]
The align and packed modifiers can be used to respectively raise or lower the alignment of structs and unions. packed may also alter the padding between fields (although it will not alter the padding inside of any field). On their own, align and packed do not provide guarantees about the order of fields in the layout of a struct or the layout of an enum variant, although they may be combined with representations (such as C) which do provide such guarantees.
[layout.repr.alignment.constraint-alignment]
The alignment is specified as an integer parameter in the form of #[repr(align(x))] or #[repr(packed(x))]. The alignment value must be a power of two from 1 up to 229. For packed, if no value is given, as in #[repr(packed)], then the value is 1.
[layout.repr.alignment.align]
For align, if the specified alignment is less than the alignment of the type without the align modifier, then the alignment is unaffected.
[layout.repr.alignment.packed]
For packed, if the specified alignment is greater than the type’s alignment without the packed modifier, then the alignment and layout is unaffected.
[layout.repr.alignment.packed-fields]
The alignments of each field, for the purpose of positioning fields, is the smaller of the specified alignment and the alignment of the field’s type.
[layout.repr.alignment.packed-padding]
Inter-field padding is guaranteed to be the minimum required in order to satisfy each field’s (possibly altered) alignment (although note that, on its own, packed does not provide any guarantee about field ordering). An important consequence of these rules is that a type with #[repr(packed(1))] (or #[repr(packed)]) will have no inter-field padding.
[layout.repr.alignment.constraint-exclusive]
The align and packed modifiers cannot be applied on the same type and a packed type cannot transitively contain another aligned type. align and packed may only be applied to the Rust and C representations.
[layout.repr.alignment.enum]
The align modifier can also be applied on an enum. When it is, the effect on the enum’s alignment is the same as if the enum was wrapped in a newtype struct with the same align modifier.
Note

References to unaligned fields are not allowed because it is undefined behavior. When fields are unaligned due to an alignment modifier, consider the following options for using references and dereferences:

#[repr(packed)]
struct Packed {
    f1: u8,
    f2: u16,
}
let mut e = Packed { f1: 1, f2: 2 };
// Instead of creating a reference to a field, copy the value to a local variable.
let x = e.f2;
// Or in situations like `println!` which creates a reference, use braces
// to change it to a copy of the value.
println!("{}", {e.f2});
// Or if you need a pointer, use the unaligned methods for reading and writing
// instead of dereferencing the pointer directly.
let ptr: *const u16 = &raw const e.f2;
let value = unsafe { ptr.read_unaligned() };
let mut_ptr: *mut u16 = &raw mut e.f2;
unsafe { mut_ptr.write_unaligned(3) }
[layout.repr.transparent]
The transparent Representation
[layout.repr.transparent.constraint-field]
The transparent representation can only be used on a struct or an enum with a single variant that has:
any number of fields with size 0 and alignment 1 (e.g. PhantomData<T>), and
at most one other field.
[layout.repr.transparent.layout-abi]
Structs and enums with this representation have the same layout and ABI as the only non-size 0 non-alignment 1 field, if present, or unit otherwise.
This is different than the C representation because a struct with the C representation will always have the ABI of a C struct while, for example, a struct with the transparent representation with a primitive field will have the ABI of the primitive field.
[layout.repr.transparent.constraint-exclusive]
Because this representation delegates type layout to another type, it cannot be used with any other representation.
[interior-mut]
Interior Mutability

[interior-mut.intro]
Sometimes a type needs to be mutated while having multiple aliases. In Rust this is achieved using a pattern called interior mutability.
[interior-mut.shared-ref]
A type has interior mutability if its internal state can be changed through a shared reference to it.
[interior-mut.no-constraint]
This goes against the usual requirement that the value pointed to by a shared reference is not mutated.
[interior-mut.unsafe-cell]
std::cell::UnsafeCell<T> type is the only allowed way to disable this requirement. When UnsafeCell<T> is immutably aliased, it is still safe to mutate, or obtain a mutable reference to, the T it contains.
[interior-mut.mut-unsafe-cell]
As with all other types, it is undefined behavior to have multiple &mut UnsafeCell<T> aliases.
[interior-mut.abstraction]
Other types with interior mutability can be created by using UnsafeCell<T> as a field. The standard library provides a variety of types that provide safe interior mutability APIs.
[interior-mut.ref-cell]
For example, std::cell::RefCell<T> uses run-time borrow checks to ensure the usual rules around multiple references.
[interior-mut.atomic]
The std::sync::atomic module contains types that wrap a value that is only accessed with atomic operations, allowing the value to be shared and mutated across threads.
[subtype]
## Subtyping and Variance

[subtype.intro]
Subtyping is implicit and can occur at any stage in type checking or inference.
[subtype.kinds]
Subtyping is restricted to two cases: variance with respect to lifetimes and between types with higher ranked lifetimes. If we were to erase lifetimes from types, then the only subtyping would be due to type equality.
Consider the following example: string literals always have 'static lifetime. Nevertheless, we can assign s to t:
fn bar<'a>() {
    let s: &'static str = "hi";
    let t: &'a str = s;
}
Since 'static outlives the lifetime parameter 'a, &'static str is a subtype of &'a str.
[subtype.higher-ranked]
Higher-ranked function pointers and trait objects have another subtype relation. They are subtypes of types that are given by substitutions of the higher-ranked lifetimes. Some examples:
// Here 'a is substituted for 'static
let subtype: &(for<'a> fn(&'a i32) -> &'a i32) = &((|x| x) as fn(&_) -> &_);
let supertype: &(fn(&'static i32) -> &'static i32) = subtype;

// This works similarly for trait objects
let subtype: &(dyn for<'a> Fn(&'a i32) -> &'a i32) = &|x| x;
let supertype: &(dyn Fn(&'static i32) -> &'static i32) = subtype;

// We can also substitute one higher-ranked lifetime for another
let subtype: &(for<'a, 'b> fn(&'a i32, &'b i32)) = &((|x, y| {}) as fn(&_, &_));
let supertype: &for<'c> fn(&'c i32, &'c i32) = subtype;
[subtyping.variance]
Variance
[subtyping.variance.intro]
Variance is a property that generic types have with respect to their arguments. A generic type’s variance in a parameter is how the subtyping of the parameter affects the subtyping of the type.
[subtyping.variance.covariant]
F<T> is covariant over T if T being a subtype of U implies that F<T> is a subtype of F<U> (subtyping “passes through”)
[subtyping.variance.contravariant]
F<T> is contravariant over T if T being a subtype of U implies that F<U> is a subtype of F<T>
[subtyping.variance.invariant]
F<T> is invariant over T otherwise (no subtyping relation can be derived)
[subtyping.variance.builtin-types]
Variance of types is automatically determined as follows
Type	Variance in 'a	Variance in T
&'a T	covariant	covariant
&'a mut T	covariant	invariant
*const T		covariant
*mut T		invariant
[T] and [T; n]		covariant
fn() -> T		covariant
fn(T) -> ()		contravariant
std::cell::UnsafeCell<T>		invariant
std::marker::PhantomData<T>		covariant
dyn Trait<T> + 'a	covariant	invariant
[subtyping.variance.user-composite-types]
The variance of other struct, enum, and union types is decided by looking at the variance of the types of their fields. If the parameter is used in positions with different variances then the parameter is invariant. For example the following struct is covariant in 'a and T and invariant in 'b, 'c, and U.
use std::cell::UnsafeCell;
struct Variance<'a, 'b, 'c, T, U: 'a> {
    x: &'a U,               // This makes `Variance` covariant in 'a, and would
                            // make it covariant in U, but U is used later
    y: *const T,            // Covariant in T
    z: UnsafeCell<&'b f64>, // Invariant in 'b
    w: *mut U,              // Invariant in U, makes the whole struct invariant

    f: fn(&'c ()) -> &'c () // Both co- and contravariant, makes 'c invariant
                            // in the struct.
}
[subtyping.variance.builtin-composite-types]
When used outside of an struct, enum, or union, the variance for parameters is checked at each location separately.
fn generic_tuple<'short, 'long: 'short>(
    // 'long is used inside of a tuple in both a co- and invariant position.
    x: (&'long u32, UnsafeCell<&'long u32>),
) {
    // As the variance at these positions is computed separately,
    // we can freely shrink 'long in the covariant position.
    let _: (&'short u32, UnsafeCell<&'long u32>) = x;
}

fn takes_fn_ptr<'short, 'middle: 'short>(
    // 'middle is used in both a co- and contravariant position.
    f: fn(&'middle ()) -> &'middle (),
) {
    // As the variance at these positions is computed separately,
    // we can freely shrink 'middle in the covariant position
    // and extend it in the contravariant position.
    let _: fn(&'static ()) -> &'short () = f;
}
[bound]
## Trait and lifetime bounds

[bound.syntax]
Syntax
TypeParamBounds → TypeParamBound ( + TypeParamBound )* +?

TypeParamBound → Lifetime | TraitBound | UseBound

TraitBound →
      ( ? | ForLifetimes )? TypePath
    | ( ( ? | ForLifetimes )? TypePath )

LifetimeBounds → ( Lifetime + )* Lifetime?

Lifetime →
      LIFETIME_OR_LABEL
    | 'static
    | '_

UseBound → use UseBoundGenericArgs

UseBoundGenericArgs →
      < >
    | < ( UseBoundGenericArg , )* UseBoundGenericArg ,? >

UseBoundGenericArg →
      Lifetime
    | IDENTIFIER
    | Self

Show syntax diagrams

[bound.intro]
Trait and lifetime bounds provide a way for generic items to restrict which types and lifetimes are used as their parameters. Bounds can be provided on any type in a where clause. There are also shorter forms for certain common cases:
Bounds written after declaring a generic parameter: fn f<A: Copy>() {} is the same as fn f<A>() where A: Copy {}.
In trait declarations as supertraits: trait Circle : Shape {} is equivalent to trait Circle where Self : Shape {}.
In trait declarations as bounds on associated types: trait A { type B: Copy; } is equivalent to trait A where Self::B: Copy { type B; }.
[bound.satisfaction]
Bounds on an item must be satisfied when using the item. When type checking and borrow checking a generic item, the bounds can be used to determine that a trait is implemented for a type. For example, given Ty: Trait
In the body of a generic function, methods from Trait can be called on Ty values. Likewise associated constants on the Trait can be used.
Associated types from Trait can be used.
Generic functions and types with a T: Trait bounds can be used with Ty being used for T.
trait Shape {
    fn draw(&self, surface: Surface);
    fn name() -> &'static str;
}

fn draw_twice<T: Shape>(surface: Surface, sh: T) {
    sh.draw(surface);           // Can call method because T: Shape
    sh.draw(surface);
}

fn copy_and_draw_twice<T: Copy>(surface: Surface, sh: T) where T: Shape {
    let shape_copy = sh;        // doesn't move sh because T: Copy
    draw_twice(surface, sh);    // Can use generic function because T: Shape
}

struct Figure<S: Shape>(S, S);

fn name_figure<U: Shape>(
    figure: Figure<U>,          // Type Figure<U> is well-formed because U: Shape
) {
    println!(
        "Figure of two {}",
        U::name(),              // Can use associated function
    );
}
[bound.trivial]
Bounds that don’t use the item’s parameters or higher-ranked lifetimes are checked when the item is defined. It is an error for such a bound to be false.
[bound.special]
Copy, Clone, and Sized bounds are also checked for certain generic types when using the item, even if the use does not provide a concrete type. It is an error to have Copy or Clone as a bound on a mutable reference, trait object, or slice. It is an error to have Sized as a bound on a trait object or slice.
struct A<'a, T>
where
    i32: Default,           // Allowed, but not useful
    i32: Iterator,          // Error: `i32` is not an iterator
    &'a mut T: Copy,        // (at use) Error: the trait bound is not satisfied
    [T]: Sized,             // (at use) Error: size cannot be known at compilation
{
    f: &'a T,
}
struct UsesA<'a, T>(A<'a, T>);
[bound.trait-object]
Trait and lifetime bounds are also used to name trait objects.
[bound.sized]
?Sized
? is only used to relax the implicit Sized trait bound for type parameters or associated types. ?Sized may not be used as a bound for other types.
[bound.lifetime]
Lifetime bounds
[bound.lifetime.intro]
Lifetime bounds can be applied to types or to other lifetimes.
[bound.lifetime.outlive-lifetime]
The bound 'a: 'b is usually read as 'a outlives 'b. 'a: 'b means that 'a lasts at least as long as 'b, so a reference &'a () is valid whenever &'b () is valid.
fn f<'a, 'b>(x: &'a i32, mut y: &'b i32) where 'a: 'b {
    y = x;                      // &'a i32 is a subtype of &'b i32 because 'a: 'b
    let r: &'b &'a i32 = &&0;   // &'b &'a i32 is well formed because 'a: 'b
}
[bound.lifetime.outlive-type]
T: 'a means that all lifetime parameters of T outlive 'a. For example, if 'a is an unconstrained lifetime parameter, then i32: 'static and &'static str: 'a are satisfied, but Vec<&'a ()>: 'static is not.
[bound.higher-ranked]
Higher-ranked trait bounds
[bound.higher-ranked.syntax]
Syntax
ForLifetimes → for GenericParams

Show syntax diagrams

[bound.higher-ranked.intro]
Trait bounds may be higher ranked over lifetimes. These bounds specify a bound that is true for all lifetimes. For example, a bound such as for<'a> &'a T: PartialEq<i32> would require an implementation like
impl<'a> PartialEq<i32> for &'a T {
    // ...
}
and could then be used to compare a &'a T with any lifetime to an i32.
Only a higher-ranked bound can be used here, because the lifetime of the reference is shorter than any possible lifetime parameter on the function:
fn call_on_ref_zero<F>(f: F) where for<'a> F: Fn(&'a i32) {
    let zero = 0;
    f(&zero);
}
[bound.higher-ranked.trait]
Higher-ranked lifetimes may also be specified just before the trait: the only difference is the scope of the lifetime parameter, which extends only to the end of the following trait instead of the whole bound. This function is equivalent to the last one.
fn call_on_ref_zero<F>(f: F) where F: for<'a> Fn(&'a i32) {
    let zero = 0;
    f(&zero);
}
[bound.implied]
Implied bounds
[bound.implied.intro]
Lifetime bounds required for types to be well-formed are sometimes inferred.
fn requires_t_outlives_a<'a, T>(x: &'a T) {}
The type parameter T is required to outlive 'a for the type &'a T to be well-formed. This is inferred because the function signature contains the type &'a T which is only valid if T: 'a holds.
[bound.implied.context]
Implied bounds are added for all parameters and outputs of functions. Inside of requires_t_outlives_a you can assume T: 'a to hold even if you don’t explicitly specify this:
fn requires_t_outlives_a_not_implied<'a, T: 'a>() {}

fn requires_t_outlives_a<'a, T>(x: &'a T) {
    // This compiles, because `T: 'a` is implied by
    // the reference type `&'a T`.
    requires_t_outlives_a_not_implied::<'a, T>();
}
fn not_implied<'a, T>() {
    // This errors, because `T: 'a` is not implied by
    // the function signature.
    requires_t_outlives_a_not_implied::<'a, T>();
}
[bound.implied.trait]
Only lifetime bounds are implied, trait bounds still have to be explicitly added. The following example therefore causes an error:
use std::fmt::Debug;
struct IsDebug<T: Debug>(T);
// error[E0277]: `T` doesn't implement `Debug`
fn doesnt_specify_t_debug<T>(x: IsDebug<T>) {}
[bound.implied.def]
Lifetime bounds are also inferred for type definitions and impl blocks for any type:
struct Struct<'a, T> {
    // This requires `T: 'a` to be well-formed
    // which is inferred by the compiler.
    field: &'a T,
}

enum Enum<'a, T> {
    // This requires `T: 'a` to be well-formed,
    // which is inferred by the compiler.
    //
    // Note that `T: 'a` is required even when only
    // using `Enum::OtherVariant`.
    SomeVariant(&'a T),
    OtherVariant,
}

trait Trait<'a, T: 'a> {}

// This would error because `T: 'a` is not implied by any type
// in the impl header.
//     impl<'a, T> Trait<'a, T> for () {}

// This compiles as `T: 'a` is implied by the self type `&'a T`.
impl<'a, T> Trait<'a, T> for &'a T {}
[bound.use]
Use bounds
Certain bounds lists may include a use<..> bound to control which generic parameters are captured by the impl Trait abstract return type. See precise capturing for more details.
[coerce]
## Type coercions

[coerce.intro]
Type coercions are implicit operations that change the type of a value. They happen automatically at specific locations and are highly restricted in what types actually coerce.
[coerce.as]
Any conversions allowed by coercion can also be explicitly performed by the type cast operator, as.
Coercions are originally defined in RFC 401 and expanded upon in RFC 1558.
[coerce.site]
Coercion sites
[coerce.site.intro]
A coercion can only occur at certain coercion sites in a program; these are typically places where the desired type is explicit or can be derived by propagation from explicit types (without type inference). Possible coercion sites are:
[coerce.site.let]
let statements where an explicit type is given.

For example, &mut 42 is coerced to have type &i8 in the following:

let _: &i8 = &mut 42;
[coerce.site.value]
static and const item declarations (similar to let statements).
[coerce.site.argument]
Arguments for function calls

The value being coerced is the actual parameter, and it is coerced to the type of the formal parameter.

For example, &mut 42 is coerced to have type &i8 in the following:

fn bar(_: &i8) { }

fn main() {
    bar(&mut 42);
}
For method calls, the receiver (self parameter) type is coerced differently, see the documentation on method-call expressions for details.
[coerce.site.constructor]
Instantiations of struct, union, or enum variant fields

For example, &mut 42 is coerced to have type &i8 in the following:

struct Foo<'a> { x: &'a i8 }

fn main() {
    Foo { x: &mut 42 };
}
[coerce.site.return]
Function results—either the final line of a block if it is not semicolon-terminated or any expression in a return statement

For example, x is coerced to have type &dyn Display in the following:

use std::fmt::Display;
fn foo(x: &u32) -> &dyn Display {
    x
}
[coerce.site.subexpr]
If the expression in one of these coercion sites is a coercion-propagating expression, then the relevant sub-expressions in that expression are also coercion sites. Propagation recurses from these new coercion sites. Propagating expressions and their relevant sub-expressions are:
[coerce.site.array]
Array literals, where the array has type [U; n]. Each sub-expression in the array literal is a coercion site for coercion to type U.
[coerce.site.repeat]
Array literals with repeating syntax, where the array has type [U; n]. The repeated sub-expression is a coercion site for coercion to type U.
[coerce.site.tuple]
Tuples, where a tuple is a coercion site to type (U_0, U_1, ..., U_n). Each sub-expression is a coercion site to the respective type, e.g. the zeroth sub-expression is a coercion site to type U_0.
[coerce.site.parenthesis]
Parenthesized sub-expressions ((e)): if the expression has type U, then the sub-expression is a coercion site to U.
[coerce.site.block]
Blocks: if a block has type U, then the last expression in the block (if it is not semicolon-terminated) is a coercion site to U. This includes blocks which are part of control flow statements, such as if/else, if the block has a known type.
[coerce.types]
Coercion types
[coerce.types.intro]
Coercion is allowed between the following types:
[coerce.types.reflexive]
T to U if T is a subtype of U (reflexive case)
[coerce.types.transitive]
T_1 to T_3 where T_1 coerces to T_2 and T_2 coerces to T_3 (transitive case)

Note that this is not fully supported yet.
[coerce.types.mut-reborrow]
&mut T to &T
[coerce.types.mut-pointer]
*mut T to *const T
[coerce.types.ref-to-pointer]
&T to *const T
[coerce.types.mut-to-pointer]
&mut T to *mut T
[coerce.types.deref]
&T or &mut T to &U if T implements Deref<Target = U>. For example:

use std::ops::Deref;

struct CharContainer {
    value: char,
}

impl Deref for CharContainer {
    type Target = char;

    fn deref<'a>(&'a self) -> &'a char {
        &self.value
    }
}

fn foo(arg: &char) {}

fn main() {
    let x = &mut CharContainer { value: 'y' };
    foo(x); //&mut CharContainer is coerced to &char.
}
[coerce.types.deref-mut]
&mut T to &mut U if T implements DerefMut<Target = U>.
[coerce.types.unsize]
TyCtor(T) to TyCtor(U), where TyCtor(T) is one of

&T
&mut T
*const T
*mut T
Box<T>
and where U can be obtained from T by unsized coercion.
[coerce.types.fn]
Function item types to fn pointers
[coerce.types.closure]
Non capturing closures to fn pointers
[coerce.types.never]
! to any T
[coerce.unsize]
Unsized Coercions
[coerce.unsize.intro]
The following coercions are called unsized coercions, since they relate to converting types to unsized types, and are permitted in a few cases where other coercions are not, as described above. They can still happen anywhere else a coercion can occur.
[coerce.unsize.trait]
Two traits, Unsize and CoerceUnsized, are used to assist in this process and expose it for library use. The following coercions are built-ins and, if T can be coerced to U with one of them, then an implementation of Unsize<U> for T will be provided:
[coerce.unsize.slice]
[T; n] to [T].
[coerce.unsize.trait-object]
T to dyn U, when T implements U + Sized, and U is dyn compatible.
[coerce.unsize.trait-upcast]
dyn T to dyn U, when U is one of T’s supertraits.
This allows dropping auto traits, i.e. dyn T + Auto to dyn U is allowed.
This allows adding auto traits if the principal trait has the auto trait as a super trait, i.e. given trait T: U + Send {}, dyn T to dyn T + Send or to dyn U + Send coercions are allowed.
[coerce.unsized.composite]
Foo<..., T, ...> to Foo<..., U, ...>, when:
Foo is a struct.
T implements Unsize<U>.
The last field of Foo has a type involving T.
If that field has type Bar<T>, then Bar<T> implements Unsize<Bar<U>>.
T is not part of the type of any other fields.
[coerce.unsized.pointer]
Additionally, a type Foo<T> can implement CoerceUnsized<Foo<U>> when T implements Unsize<U> or CoerceUnsized<Foo<U>>. This allows it to provide an unsized coercion to Foo<U>.
Note

While the definition of the unsized coercions and their implementation has been stabilized, the traits themselves are not yet stable and therefore can’t be used directly in stable Rust.
[coerce.least-upper-bound]
Least upper bound coercions
[coerce.least-upper-bound.intro]
In some contexts, the compiler must coerce together multiple types to try and find the most general type. This is called a “Least Upper Bound” coercion. LUB coercion is used and only used in the following situations:
To find the common type for a series of if branches.
To find the common type for a series of match arms.
To find the common type for array elements.
To find the type for the return type of a closure with multiple return statements.
To check the type for the return type of a function with multiple return statements.
[coerce.least-upper-bound.target]
In each such case, there are a set of types T0..Tn to be mutually coerced to some target type T_t, which is unknown to start.
[coerce.least-upper-bound.computation]
Computing the LUB coercion is done iteratively. The target type T_t begins as the type T0. For each new type Ti, we consider whether
[coerce.least-upper-bound.computation-identity]
If Ti can be coerced to the current target type T_t, then no change is made.
[coerce.least-upper-bound.computation-replace]
Otherwise, check whether T_t can be coerced to Ti; if so, the T_t is changed to Ti. (This check is also conditioned on whether all of the source expressions considered thus far have implicit coercions.)
[coerce.least-upper-bound.computation-unify]
If not, try to compute a mutual supertype of T_t and Ti, which will become the new target type.
Examples:
// For if branches
let bar = if true {
    a
} else if false {
    b
} else {
    c
};

// For match arms
let baw = match 42 {
    0 => a,
    1 => b,
    _ => c,
};

// For array elements
let bax = [a, b, c];

// For closure with multiple return statements
let clo = || {
    if true {
        a
    } else if false {
        b
    } else {
        c
    }
};
let baz = clo();

// For type checking of function with multiple return statements
fn foo() -> i32 {
    let (a, b, c) = (0, 1, 2);
    match 42 {
        0 => a,
        1 => b,
        _ => c,
    }
}
In these examples, types of the ba* are found by LUB coercion. And the compiler checks whether LUB coercion result of a, b, c is i32 in the processing of the function foo.
Caveat
This description is obviously informal. Making it more precise is expected to proceed as part of a general effort to specify the Rust type checker more precisely.
[destructors]
## Destructors

[destructors.intro]
When an initialized variable or temporary goes out of scope, its destructor is run, or it is dropped. Assignment also runs the destructor of its left-hand operand, if it’s initialized. If a variable has been partially initialized, only its initialized fields are dropped.
[destructors.operation]
The destructor of a type T consists of:
If T: Drop, calling <T as std::ops::Drop>::drop
Recursively running the destructor of all of its fields.
The fields of a struct are dropped in declaration order.
The fields of the active enum variant are dropped in declaration order.
The fields of a tuple are dropped in order.
The elements of an array or owned slice are dropped from the first element to the last.
The variables that a closure captures by move are dropped in an unspecified order.
Trait objects run the destructor of the underlying type.
Other types don’t result in any further drops.
[destructors.drop_in_place]
If a destructor must be run manually, such as when implementing your own smart pointer, std::ptr::drop_in_place can be used.
Some examples:
struct PrintOnDrop(&'static str);

impl Drop for PrintOnDrop {
    fn drop(&mut self) {
        println!("{}", self.0);
    }
}

let mut overwritten = PrintOnDrop("drops when overwritten");
overwritten = PrintOnDrop("drops when scope ends");

let tuple = (PrintOnDrop("Tuple first"), PrintOnDrop("Tuple second"));

let moved;
// No destructor run on assignment.
moved = PrintOnDrop("Drops when moved");
// Drops now, but is then uninitialized.
moved;

// Uninitialized does not drop.
let uninitialized: PrintOnDrop;

// After a partial move, only the remaining fields are dropped.
let mut partial_move = (PrintOnDrop("first"), PrintOnDrop("forgotten"));
// Perform a partial move, leaving only `partial_move.0` initialized.
core::mem::forget(partial_move.1);
// When partial_move's scope ends, only the first field is dropped.
[destructors.scope]
Drop scopes
[destructors.scope.intro]
Each variable or temporary is associated to a drop scope. When control flow leaves a drop scope all variables associated to that scope are dropped in reverse order of declaration (for variables) or creation (for temporaries).
[destructors.scope.desugaring]
Drop scopes can be determined by replacing for, if, and while expressions with equivalent expressions using match, loop and break.
[destructors.scope.operators]
Overloaded operators are not distinguished from built-in operators and binding modes are not considered.
[destructors.scope.list]
Given a function, or closure, there are drop scopes for:
[destructors.scope.function]
The entire function
[destructors.scope.statement]
Each statement
[destructors.scope.expression]
Each expression
[destructors.scope.block]
Each block, including the function body
In the case of a block expression, the scope for the block and the expression are the same scope.
[destructors.scope.match-arm]
Each arm of a match expression
[destructors.scope.nesting]
Drop scopes are nested within one another as follows. When multiple scopes are left at once, such as when returning from a function, variables are dropped from the inside outwards.
[destructors.scope.nesting.function]
The entire function scope is the outer most scope.
[destructors.scope.nesting.function-body]
The function body block is contained within the scope of the entire function.
[destructors.scope.nesting.expr-statement]
The parent of the expression in an expression statement is the scope of the statement.
[destructors.scope.nesting.let-initializer]
The parent of the initializer of a let statement is the let statement’s scope.
[destructors.scope.nesting.statement]
The parent of a statement scope is the scope of the block that contains the statement.
[destructors.scope.nesting.match-guard]
The parent of the expression for a match guard is the scope of the arm that the guard is for.
[destructors.scope.nesting.match-arm]
The parent of the expression after the => in a match expression is the scope of the arm that it’s in.
[destructors.scope.nesting.match]
The parent of the arm scope is the scope of the match expression that it belongs to.
[destructors.scope.nesting.other]
The parent of all other scopes is the scope of the immediately enclosing expression.
[destructors.scope.params]
Scopes of function parameters
All function parameters are in the scope of the entire function body, so are dropped last when evaluating the function. Each actual function parameter is dropped after any bindings introduced in that parameter’s pattern.
// Drops `y`, then the second parameter, then `x`, then the first parameter
fn patterns_in_parameters(
    (x, _): (PrintOnDrop, PrintOnDrop),
    (_, y): (PrintOnDrop, PrintOnDrop),
) {}

// drop order is 3 2 0 1
patterns_in_parameters(
    (PrintOnDrop("0"), PrintOnDrop("1")),
    (PrintOnDrop("2"), PrintOnDrop("3")),
);
[destructors.scope.bindings]
Scopes of local variables
[destructors.scope.bindings.intro]
Local variables declared in a let statement are associated to the scope of the block that contains the let statement. Local variables declared in a match expression are associated to the arm scope of the match arm that they are declared in.
let declared_first = PrintOnDrop("Dropped last in outer scope");
{
    let declared_in_block = PrintOnDrop("Dropped in inner scope");
}
let declared_last = PrintOnDrop("Dropped first in outer scope");
[destructors.scope.bindings.patterns]
Variables in patterns are dropped in reverse order of declaration within the pattern.
let (declared_first, declared_last) = (
    PrintOnDrop("Dropped last"),
    PrintOnDrop("Dropped first"),
);
[destructors.scope.bindings.or-patterns]
For the purpose of drop order, or-patterns declare bindings in the order given by the first subpattern.
// Drops `x` before `y`.
fn or_pattern_drop_order<T>(
    (Ok([x, y]) | Err([y, x])): Result<[T; 2], [T; 2]>
//   ^^^^^^^^^^   ^^^^^^^^^^^ This is the second subpattern.
//   |
//   This is the first subpattern.
//
//   In the first subpattern, `x` is declared before `y`. Since it is
//   the first subpattern, that is the order used even if the second
//   subpattern, where the bindings are declared in the opposite
//   order, is matched.
) {}

// Here we match the first subpattern, and the drops happen according
// to the declaration order in the first subpattern.
or_pattern_drop_order(Ok([
    PrintOnDrop("Declared first, dropped last"),
    PrintOnDrop("Declared last, dropped first"),
]));

// Here we match the second subpattern, and the drops still happen
// according to the declaration order in the first subpattern.
or_pattern_drop_order(Err([
    PrintOnDrop("Declared last, dropped first"),
    PrintOnDrop("Declared first, dropped last"),
]));
[destructors.scope.temporary]
Temporary scopes
[destructors.scope.temporary.intro]
The temporary scope of an expression is the scope that is used for the temporary variable that holds the result of that expression when used in a place context, unless it is promoted.
[destructors.scope.temporary.enclosing]
Apart from lifetime extension, the temporary scope of an expression is the smallest scope that contains the expression and is one of the following:
The entire function.
A statement.
The body of an if, while or loop expression.
The else block of an if expression.
The non-pattern matching condition expression of an if or while expression, or a match guard.
The body expression for a match arm.
Each operand of a lazy boolean expression.
The pattern-matching condition(s) and consequent body of if (destructors.scope.temporary.edition2024).
The pattern-matching condition and loop body of while.
The entirety of the tail expression of a block (destructors.scope.temporary.edition2024).
Note

The scrutinee of a match expression is not a temporary scope, so temporaries in the scrutinee can be dropped after the match expression. For example, the temporary for 1 in match 1 { ref mut z => z }; lives until the end of the statement.
[destructors.scope.temporary.edition2024]
2024
Edition differences

The 2024 edition added two new temporary scope narrowing rules: if let temporaries are dropped before the else block, and temporaries of tail expressions of blocks are dropped immediately after the tail expression is evaluated.
Some examples:
let local_var = PrintOnDrop("local var");

// Dropped once the condition has been evaluated
if PrintOnDrop("If condition").0 == "If condition" {
    // Dropped at the end of the block
    PrintOnDrop("If body").0
} else {
    unreachable!()
};

if let "if let scrutinee" = PrintOnDrop("if let scrutinee").0 {
    PrintOnDrop("if let consequent").0
    // `if let consequent` dropped here
}
// `if let scrutinee` is dropped here
else {
    PrintOnDrop("if let else").0
    // `if let else` dropped here
};

while let x = PrintOnDrop("while let scrutinee").0 {
    PrintOnDrop("while let loop body").0;
    break;
    // `while let loop body` dropped here.
    // `while let scrutinee` dropped here.
}

// Dropped before the first ||
(PrintOnDrop("first operand").0 == ""
// Dropped before the )
|| PrintOnDrop("second operand").0 == "")
// Dropped before the ;
|| PrintOnDrop("third operand").0 == "";

// Scrutinee is dropped at the end of the function, before local variables
// (because this is the tail expression of the function body block).
match PrintOnDrop("Matched value in final expression") {
    // Dropped once the condition has been evaluated
    _ if PrintOnDrop("guard condition").0 == "" => (),
    _ => (),
}
[destructors.scope.operands]
Operands
Temporaries are also created to hold the result of operands to an expression while the other operands are evaluated. The temporaries are associated to the scope of the expression with that operand. Since the temporaries are moved from once the expression is evaluated, dropping them has no effect unless one of the operands to an expression breaks out of the expression, returns, or panics.
loop {
    // Tuple expression doesn't finish evaluating so operands drop in reverse order
    (
        PrintOnDrop("Outer tuple first"),
        PrintOnDrop("Outer tuple second"),
        (
            PrintOnDrop("Inner tuple first"),
            PrintOnDrop("Inner tuple second"),
            break,
        ),
        PrintOnDrop("Never created"),
    );
}
[destructors.scope.const-promotion]
Constant promotion
Promotion of a value expression to a 'static slot occurs when the expression could be written in a constant and borrowed, and that borrow could be dereferenced where the expression was originally written, without changing the runtime behavior. That is, the promoted expression can be evaluated at compile-time and the resulting value does not contain interior mutability or destructors (these properties are determined based on the value where possible, e.g. &None always has the type &'static Option<_>, as it contains nothing disallowed).
[destructors.scope.lifetime-extension]
Temporary lifetime extension
Note

The exact rules for temporary lifetime extension are subject to change. This is describing the current behavior only.
[destructors.scope.lifetime-extension.let]
The temporary scopes for expressions in let statements are sometimes extended to the scope of the block containing the let statement. This is done when the usual temporary scope would be too small, based on certain syntactic rules. For example:
let x = &mut 0;
// Usually a temporary would be dropped by now, but the temporary for `0` lives
// to the end of the block.
println!("{}", x);
[destructors.scope.lifetime-extension.static]
Lifetime extension also applies to static and const items, where it makes temporaries live until the end of the program. For example:
const C: &Vec<i32> = &Vec::new();
// Usually this would be a dangling reference as the `Vec` would only
// exist inside the initializer expression of `C`, but instead the
// borrow gets lifetime-extended so it effectively has `'static` lifetime.
println!("{:?}", C);
[destructors.scope.lifetime-extension.sub-expressions]
If a borrow, dereference, field, or tuple indexing expression has an extended temporary scope then so does its operand. If an indexing expression has an extended temporary scope then the indexed expression also has an extended temporary scope.
[destructors.scope.lifetime-extension.patterns]
Extending based on patterns
[destructors.scope.lifetime-extension.patterns.extending]
An extending pattern is either:
An identifier pattern that binds by reference or mutable reference.

let ref x = temp(); // Binds by reference.
let ref mut x = temp(); // Binds by mutable reference.
A struct, tuple, tuple struct, slice, or or-pattern where at least one of the direct subpatterns is an extending pattern.

struct W<T>(T);
let W { 0: ref x } = W(()); // Struct pattern.
let W(ref x) = W(()); // Tuple struct pattern.
let (W(ref x),) = (W(()),); // Tuple pattern.
let [W(ref x), ..] = [W(())]; // Slice pattern.
let (Ok(W(ref x)) | Err(&ref x)) = Ok(W(())); // Or pattern.
//
// All of the temporaries above are still live here.
So ref x, V(ref x) and [ref x, y] are all extending patterns, but x, &ref x and &(ref x,) are not.
[destructors.scope.lifetime-extension.patterns.let]
If the pattern in a let statement is an extending pattern then the temporary scope of the initializer expression is extended.
// This is an extending pattern, so the temporary scope is extended.
let ref x = *&temp(); // OK
// This is neither an extending pattern nor an extending expression,
// so the temporary is dropped at the semicolon.
let &ref x = *&&temp(); // ERROR
// This is not an extending pattern but it is an extending expression,
// so the temporary lives beyond the `let` statement.
let &ref x = &*&temp(); // OK
[destructors.scope.lifetime-extension.exprs]
Extending based on expressions
For a let statement with an initializer, an extending expression is an expression which is one of the following:
The initializer expression.
The operand of an extending borrow expression.
The operand(s) of an extending array, cast, braced struct, or tuple expression.
The arguments to an extending tuple struct or tuple variant constructor expression.
The final expression of an extending block expression except for an async block expression.
The final expression of an extending if expression’s consequent, else if, or else block.
An arm expression of an extending match expression.
So the borrow expressions in &mut 0, (&1, &mut 2), and Some(&mut 3) are all extending expressions. The borrows in &0 + &1 and f(&mut 0) are not.
The operand of any extending borrow expression has its temporary scope extended.
Note

rustc does not treat array repeat operands of extending array expressions as extending expressions. Whether it should is an open question.

For details, see Rust issue #146092.
Examples
Here are some examples where expressions have extended temporary scopes:
let x = &temp(); // Operand of borrow.
let x = &raw const *&temp(); // Operand of raw borrow.
let x = &temp() as &dyn Send; // Operand of cast.
let x = (&*&temp(),); // Operand of tuple constructor.
let x = { [Some(&temp())] }; // Final expr of block.
let x = const { &temp() }; // Final expr of `const` block.
let x = unsafe { &temp() }; // Final expr of `unsafe` block.
let x = if true { &temp() } else { &temp() };
//              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
//           Final exprs of `if`/`else` blocks.
let x = match () { _ => &temp() }; // `match` arm expression.
//
// All of the temporaries above are still live here.
Here are some examples where expressions don’t have extended temporary scopes:
// Arguments to function calls are not extending expressions. The
// temporary is dropped at the semicolon.
let x = core::convert::identity(&temp()); // ERROR
// Receivers of method calls are not extending expressions.
let x = (&temp()).use_temp(); // ERROR
// Scrutinees of match expressions are not extending expressions.
let x = match &temp() { x => x }; // ERROR
// Final expressions of `async` blocks are not extending expressions.
let x = async { &temp() }; // ERROR
// Final expressions of closures are not extending expressions.
let x = || &temp(); // ERROR
// Operands of loop breaks are not extending expressions.
let x = loop { break &temp() }; // ERROR
// Operands of breaks to labels are not extending expressions.
let x = 'a: { break 'a &temp() }; // ERROR
[destructors.forget]
Not running destructors
[destructors.manually-suppressing]
Manually suppressing destructors
std::mem::forget can be used to prevent the destructor of a variable from being run, and std::mem::ManuallyDrop provides a wrapper to prevent a variable or field from being dropped automatically.
Note

Preventing a destructor from being run via std::mem::forget or other means is safe even if it has a type that isn’t 'static. Besides the places where destructors are guaranteed to run as defined by this document, types may not safely rely on a destructor being run for soundness.
[destructors.process-termination]
Process termination without unwinding
There are some ways to terminate the process without unwinding, in which case destructors will not be run.
The standard library provides std::process::exit and std::process::abort to do this explicitly. Additionally, if the panic handler is set to abort, panicking will always terminate the process without destructors being run.
There is one additional case to be aware of: when a panic reaches a non-unwinding ABI boundary, either no destructors will run, or all destructors up until the ABI boundary will run.
[lifetime-elision]
## Lifetime elision

Rust has rules that allow lifetimes to be elided in various places where the compiler can infer a sensible default choice.
[lifetime-elision.function]
Lifetime elision in functions
[lifetime-elision.function.intro]
In order to make common patterns more ergonomic, lifetime arguments can be elided in function item, function pointer, and closure trait signatures. The following rules are used to infer lifetime parameters for elided lifetimes.
[lifetime-elision.function.lifetimes-not-inferred]
It is an error to elide lifetime parameters that cannot be inferred.
[lifetime-elision.function.explicit-placeholder]
The placeholder lifetime, '_, can also be used to have a lifetime inferred in the same way. For lifetimes in paths, using '_ is preferred.
[lifetime-elision.function.only-functions]
Trait object lifetimes follow different rules discussed below.
[lifetime-elision.function.implicit-lifetime-parameters]
Each elided lifetime in the parameters becomes a distinct lifetime parameter.
[lifetime-elision.function.output-lifetime]
If there is exactly one lifetime used in the parameters (elided or not), that lifetime is assigned to all elided output lifetimes.
[lifetime-elision.function.receiver-lifetime]
In method signatures there is another rule
If the receiver has type &Self or &mut Self, then the lifetime of that reference to Self is assigned to all elided output lifetime parameters.
Examples:
fn print1(s: &str);                                   // elided
fn print2(s: &'_ str);                                // also elided
fn print3<'a>(s: &'a str);                            // expanded

fn debug1(lvl: usize, s: &str);                       // elided
fn debug2<'a>(lvl: usize, s: &'a str);                // expanded

fn substr1(s: &str, until: usize) -> &str;            // elided
fn substr2<'a>(s: &'a str, until: usize) -> &'a str;  // expanded

fn get_mut1(&mut self) -> &mut dyn T;                 // elided
fn get_mut2<'a>(&'a mut self) -> &'a mut dyn T;       // expanded

fn args1<T: ToCStr>(&mut self, args: &[T]) -> &mut Command;                  // elided
fn args2<'a, 'b, T: ToCStr>(&'a mut self, args: &'b [T]) -> &'a mut Command; // expanded

fn other_args1<'a>(arg: &str) -> &'a str;             // elided
fn other_args2<'a, 'b>(arg: &'b str) -> &'a str;      // expanded

fn new1(buf: &mut [u8]) -> Thing<'_>;                 // elided - preferred
fn new2(buf: &mut [u8]) -> Thing;                     // elided
fn new3<'a>(buf: &'a mut [u8]) -> Thing<'a>;          // expanded

type FunPtr1 = fn(&str) -> &str;                      // elided
type FunPtr2 = for<'a> fn(&'a str) -> &'a str;        // expanded

type FunTrait1 = dyn Fn(&str) -> &str;                // elided
type FunTrait2 = dyn for<'a> Fn(&'a str) -> &'a str;  // expanded
// The following examples show situations where it is not allowed to elide the
// lifetime parameter.

// Cannot infer, because there are no parameters to infer from.
fn get_str() -> &str;                                 // ILLEGAL

// Cannot infer, ambiguous if it is borrowed from the first or second parameter.
fn frob(s: &str, t: &str) -> &str;                    // ILLEGAL
[lifetime-elision.trait-object]
Default trait object lifetimes
[lifetime-elision.trait-object.intro]
The assumed lifetime of references held by a trait object is called its default object lifetime bound. These were defined in RFC 599 and amended in RFC 1156.
[lifetime-elision.trait-object.explicit-bound]
These default object lifetime bounds are used instead of the lifetime parameter elision rules defined above when the lifetime bound is omitted entirely.
[lifetime-elision.trait-object.explicit-placeholder]
If '_ is used as the lifetime bound then the bound follows the usual elision rules.
[lifetime-elision.trait-object.containing-type]
If the trait object is used as a type argument of a generic type then the containing type is first used to try to infer a bound.
[lifetime-elision.trait-object.containing-type-unique]
If there is a unique bound from the containing type then that is the default
[lifetime-elision.trait-object.containing-type-explicit]
If there is more than one bound from the containing type then an explicit bound must be specified
[lifetime-elision.trait-object.trait-bounds]
If neither of those rules apply, then the bounds on the trait are used:
[lifetime-elision.trait-object.trait-unique]
If the trait is defined with a single lifetime bound then that bound is used.
[lifetime-elision.trait-object.static-lifetime]
If 'static is used for any lifetime bound then 'static is used.
[lifetime-elision.trait-object.default]
If the trait has no lifetime bounds, then the lifetime is inferred in expressions and is 'static outside of expressions.
// For the following trait...
trait Foo { }

// These two are the same because Box<T> has no lifetime bound on T
type T1 = Box<dyn Foo>;
type T2 = Box<dyn Foo + 'static>;

// ...and so are these:
impl dyn Foo {}
impl dyn Foo + 'static {}

// ...so are these, because &'a T requires T: 'a
type T3<'a> = &'a dyn Foo;
type T4<'a> = &'a (dyn Foo + 'a);

// std::cell::Ref<'a, T> also requires T: 'a, so these are the same
type T5<'a> = std::cell::Ref<'a, dyn Foo>;
type T6<'a> = std::cell::Ref<'a, dyn Foo + 'a>;
// This is an example of an error.
struct TwoBounds<'a, 'b, T: ?Sized + 'a + 'b> {
    f1: &'a i32,
    f2: &'b i32,
    f3: T,
}
type T7<'a, 'b> = TwoBounds<'a, 'b, dyn Foo>;
//                                  ^^^^^^^
// Error: the lifetime bound for this object type cannot be deduced from context
[lifetime-elision.trait-object.innermost-type]
Note that the innermost object sets the bound, so &'a Box<dyn Foo> is still &'a Box<dyn Foo + 'static>.
// For the following trait...
trait Bar<'a>: 'a { }

// ...these two are the same:
type T1<'a> = Box<dyn Bar<'a>>;
type T2<'a> = Box<dyn Bar<'a> + 'a>;

// ...and so are these:
impl<'a> dyn Bar<'a> {}
impl<'a> dyn Bar<'a> + 'a {}
[lifetime-elision.const-static]
const and static elision
[lifetime-elision.const-static.implicit-static]
Both constant and static declarations of reference types have implicit 'static lifetimes unless an explicit lifetime is specified. As such, the constant declarations involving 'static above may be written without the lifetimes.
// STRING: &'static str
const STRING: &str = "bitstring";

struct BitsNStrings<'a> {
    mybits: [u32; 2],
    mystring: &'a str,
}

// BITS_N_STRINGS: BitsNStrings<'static>
const BITS_N_STRINGS: BitsNStrings<'_> = BitsNStrings {
    mybits: [1, 2],
    mystring: STRING,
};
[lifetime-elision.const-static.fn-references]
Note that if the static or const items include function or closure references, which themselves include references, the compiler will first try the standard elision rules. If it is unable to resolve the lifetimes by its usual rules, then it will error. By way of example:
// Resolved as `for<'a> fn(&'a str) -> &'a str`.
const RESOLVED_SINGLE: fn(&str) -> &str = |x| x;

// Resolved as `for<'a, 'b, 'c> Fn(&'a Foo, &'b Bar, &'c Baz) -> usize`.
const RESOLVED_MULTIPLE: &dyn Fn(&Foo, &Bar, &Baz) -> usize = &somefunc;
// There is insufficient information to bound the return reference lifetime
// relative to the argument lifetimes, so this is an error.
const RESOLVED_STATIC: &dyn Fn(&Foo, &Bar) -> &Baz = &somefunc;
//                                            ^
// this function's return type contains a borrowed value, but the signature
// does not say whether it is borrowed from argument 1 or argument 2
[lang-types]
