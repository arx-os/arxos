# Patterns
[patterns.syntax]
Syntax
Pattern → |? PatternNoTopAlt ( | PatternNoTopAlt )*

PatternNoTopAlt →
      PatternWithoutRange
    | RangePattern

PatternWithoutRange →
      LiteralPattern
    | IdentifierPattern
    | WildcardPattern
    | RestPattern
    | ReferencePattern
    | StructPattern
    | TupleStructPattern
    | TuplePattern
    | GroupedPattern
    | SlicePattern
    | PathPattern
    | MacroInvocation

Show syntax diagrams

[patterns.intro]
Patterns are used to match values against structures and to, optionally, bind variables to values inside these structures. They are also used in variable declarations and parameters for functions and closures.
The pattern in the following example does four things:
Tests if person has the car field filled with something.
Tests if the person’s age field is between 13 and 19, and binds its value to the person_age variable.
Binds a reference to the name field to the variable person_name.
Ignores the rest of the fields of person. The remaining fields can have any value and are not bound to any variables.
if let
    Person {
        car: Some(_),
        age: person_age @ 13..=19,
        name: ref person_name,
        ..
    } = person
{
    println!("{} has a car and is {} years old.", person_name, person_age);
}
[patterns.usage]
Patterns are used in:
[patterns.let]
let declarations
[patterns.param]
Function and closure parameters
[patterns.match]
match expressions
[patterns.if-let]
if let expressions
[patterns.while-let]
while let expressions
[patterns.for]
for expressions
[patterns.destructure]
Destructuring
[patterns.destructure.intro]
Patterns can be used to destructure structs, enums, and tuples. Destructuring breaks up a value into its component pieces. The syntax used is almost the same as when creating such values.
[patterns.destructure.wildcard]
In a pattern whose scrutinee expression has a struct, enum or tuple type, a wildcard pattern (_) stands in for a single data field, whereas an et cetera or rest pattern (..) stands in for all the remaining fields of a particular variant.
[patterns.destructure.named-field-shorthand]
When destructuring a data structure with named (but not numbered) fields, it is allowed to write fieldname as a shorthand for fieldname: fieldname.
match message {
    Message::Quit => println!("Quit"),
    Message::WriteString(write) => println!("{}", &write),
    Message::Move{ x, y: 0 } => println!("move {} horizontally", x),
    Message::Move{ .. } => println!("other move"),
    Message::ChangeColor { 0: red, 1: green, 2: _ } => {
        println!("color change, red: {}, green: {}", red, green);
    }
};
[patterns.refutable]
Refutability
A pattern is said to be refutable when it has the possibility of not being matched by the value it is being matched against. Irrefutable patterns, on the other hand, always match the value they are being matched against. Examples:
let (x, y) = (1, 2);               // "(x, y)" is an irrefutable pattern

if let (a, 3) = (1, 2) {           // "(a, 3)" is refutable, and will not match
    panic!("Shouldn't reach here");
} else if let (a, 4) = (3, 4) {    // "(a, 4)" is refutable, and will match
    println!("Matched ({}, 4)", a);
}
[patterns.literal]
Literal patterns
[patterns.literal.syntax]
Syntax
LiteralPattern → -? LiteralExpression

Show syntax diagrams

[patterns.literal.intro]
Literal patterns match exactly the same value as what is created by the literal. Since negative numbers are not literals, literals in patterns may be prefixed by an optional minus sign, which acts like the negation operator.
Warning

C string and raw C string literals are accepted in literal patterns, but &CStr doesn’t implement structural equality (#[derive(Eq, PartialEq)]) and therefore any such match on a &CStr will be rejected with a type error.
[patterns.literal.refutable]
Literal patterns are always refutable.
Examples:
for i in -2..5 {
    match i {
        -1 => println!("It's minus one"),
        1 => println!("It's a one"),
        2|4 => println!("It's either a two or a four"),
        _ => println!("Matched none of the arms"),
    }
}
[patterns.ident]
Identifier patterns
[patterns.ident.syntax]
Syntax
IdentifierPattern → ref? mut? IDENTIFIER ( @ PatternNoTopAlt )?

Show syntax diagrams

[patterns.ident.intro]
Identifier patterns bind the value they match to a variable in the value namespace.
[patterns.ident.unique]
The identifier must be unique within the pattern.
[patterns.ident.scope]
The variable will shadow any variables of the same name in scope. The scope of the new binding depends on the context of where the pattern is used (such as a let binding or a match arm).
[patterns.ident.bare]
Patterns that consist of only an identifier, possibly with a mut, match any value and bind it to that identifier. This is the most commonly used pattern in variable declarations and parameters for functions and closures.
let mut variable = 10;
fn sum(x: i32, y: i32) -> i32 {
[patterns.ident.scrutinized]
To bind the matched value of a pattern to a variable, use the syntax variable @ subpattern. For example, the following binds the value 2 to e (not the entire range: the range here is a range subpattern).
let x = 2;

match x {
    e @ 1 ..= 5 => println!("got a range element {}", e),
    _ => println!("anything"),
}
[patterns.ident.move]
By default, identifier patterns bind a variable to a copy of or move from the matched value depending on whether the matched value implements Copy.
[patterns.ident.ref]
This can be changed to bind to a reference by using the ref keyword, or to a mutable reference using ref mut. For example:
match a {
    None => (),
    Some(value) => (),
}

match a {
    None => (),
    Some(ref value) => (),
}
In the first match expression, the value is copied (or moved). In the second match, a reference to the same memory location is bound to the variable value. This syntax is needed because in destructuring subpatterns the & operator can’t be applied to the value’s fields. For example, the following is not valid:
if let Person { name: &person_name, age: 18..=150 } = value { }
To make it valid, write the following:
if let Person { name: ref person_name, age: 18..=150 } = value { }
[patterns.ident.ref-ignored]
Thus, ref is not something that is being matched against. Its objective is exclusively to make the matched binding a reference, instead of potentially copying or moving what was matched.
[patterns.ident.precedent]
Path patterns take precedence over identifier patterns.
[patterns.ident.constraint]
It is an error if ref or ref mut is specified and the identifier shadows a constant.
[patterns.ident.refutable]
Identifier patterns are irrefutable if the @ subpattern is irrefutable or the subpattern is not specified.
[patterns.ident.binding]
Binding modes
[patterns.ident.binding.intro]
To service better ergonomics, patterns operate in different binding modes in order to make it easier to bind references to values. When a reference value is matched by a non-reference pattern, it will be automatically treated as a ref or ref mut binding. Example:
let x: &Option<i32> = &Some(3);
if let Some(y) = x {
    // y was converted to `ref y` and its type is &i32
}
[patterns.ident.binding.non-reference]
Non-reference patterns include all patterns except bindings, wildcard patterns (_), const patterns of reference types, and reference patterns.
[patterns.ident.binding.default-mode]
If a binding pattern does not explicitly have ref, ref mut, or mut, then it uses the default binding mode to determine how the variable is bound.
[patterns.ident.binding.move]
The default binding mode starts in “move” mode which uses move semantics.
[patterns.ident.binding.top-down]
When matching a pattern, the compiler starts from the outside of the pattern and works inwards.
[patterns.ident.binding.auto-deref]
Each time a reference is matched using a non-reference pattern, it will automatically dereference the value and update the default binding mode.
[patterns.ident.binding.ref]
References will set the default binding mode to ref.
[patterns.ident.binding.ref-mut]
Mutable references will set the mode to ref mut unless the mode is already ref in which case it remains ref.
[patterns.ident.binding.nested-references]
If the automatically dereferenced value is still a reference, it is dereferenced and this process repeats.
[patterns.ident.binding.mode-limitations-binding]
The binding pattern may only explicitly specify a ref or ref mut binding mode, or specify mutability with mut, when the default binding mode is “move”. For example, these are not accepted:
let [mut x] = &[()]; //~ ERROR
let [ref x] = &[()]; //~ ERROR
let [ref mut x] = &mut [()]; //~ ERROR
[patterns.ident.binding.mode-limitations.edition2024]
2024
Edition differences

Before the 2024 edition, bindings could explicitly specify a ref or ref mut binding mode even when the default binding mode was not “move”, and they could specify mutability on such bindings with mut. In these editions, specifying mut on a binding set the binding mode to “move” regardless of the current default binding mode.
[patterns.ident.binding.mode-limitations-reference]
Similarly, a reference pattern may only appear when the default binding mode is “move”. For example, this is not accepted:
let [&x] = &[&()]; //~ ERROR
[patterns.ident.binding.mode-limitations-reference.edition2024]
2024
Edition differences

Before the 2024 edition, reference patterns could appear even when the default binding mode was not “move”, and had both the effect of matching against the scrutinee and of causing the default binding mode to be reset to “move”.
[patterns.ident.binding.mixed]
Move bindings and reference bindings can be mixed together in the same pattern. Doing so will result in partial move of the object bound to and the object cannot be used afterwards. This applies only if the type cannot be copied.
In the example below, name is moved out of person. Trying to use person as a whole or person.name would result in an error because of partial move.
Example:
// `name` is moved from person and `age` referenced
let Person { name, ref age } = person;
[patterns.wildcard]
Wildcard pattern
[patterns.wildcard.syntax]
Syntax
WildcardPattern → _

Show syntax diagrams

[patterns.wildcard.intro]
The wildcard pattern (an underscore symbol) matches any value. It is used to ignore values when they don’t matter.
[patterns.wildcard.struct-matcher]
Inside other patterns it matches a single data field (as opposed to the .. which matches the remaining fields).
[patterns.wildcard.no-binding]
Unlike identifier patterns, it does not copy, move or borrow the value it matches.
Examples:
let (a, _) = (10, x);   // the x is always matched by _

// ignore a function/closure param
let real_part = |a: f64, _: f64| { a };

// ignore a field from a struct
let RGBA{r: red, g: green, b: blue, a: _} = color;

// accept any Some, with any value
if let Some(_) = x {}
[patterns.wildcard.refutable]
The wildcard pattern is always irrefutable.
[patterns.rest]
Rest patterns
[patterns.rest.syntax]
Syntax
RestPattern → ..

Show syntax diagrams

[patterns.rest.intro]
The rest pattern (the .. token) acts as a variable-length pattern which matches zero or more elements that haven’t been matched already before and after.
[patterns.rest.allowed-patterns]
It may only be used in tuple, tuple struct, and slice patterns, and may only appear once as one of the elements in those patterns. It is also allowed in an identifier pattern for slice patterns only.
[patterns.rest.refutable]
The rest pattern is always irrefutable.
Examples:
match slice {
    [] => println!("slice is empty"),
    [one] => println!("single element {}", one),
    [head, tail @ ..] => println!("head={} tail={:?}", head, tail),
}

match slice {
    // Ignore everything but the last element, which must be "!".
    [.., "!"] => println!("!!!"),

    // `start` is a slice of everything except the last element, which must be "z".
    [start @ .., "z"] => println!("starts with: {:?}", start),

    // `end` is a slice of everything but the first element, which must be "a".
    ["a", end @ ..] => println!("ends with: {:?}", end),

    // 'whole' is the entire slice and `last` is the final element
    whole @ [.., last] => println!("the last element of {:?} is {}", whole, last),

    rest => println!("{:?}", rest),
}

if let [.., penultimate, _] = slice {
    println!("next to last is {}", penultimate);
}

// Rest patterns may also be used in tuple and tuple struct patterns.
match tuple {
    (1, .., y, z) => println!("y={} z={}", y, z),
    (.., 5) => println!("tail must be 5"),
    (..) => println!("matches everything else"),
}
[patterns.range]
Range patterns
[patterns.range.syntax]
Syntax
RangePattern →
      RangeExclusivePattern
    | RangeInclusivePattern
    | RangeFromPattern
    | RangeToExclusivePattern
    | RangeToInclusivePattern
    | ObsoleteRangePattern​1

RangeExclusivePattern →
      RangePatternBound .. RangePatternBound

RangeInclusivePattern →
      RangePatternBound ..= RangePatternBound

RangeFromPattern →
      RangePatternBound ..

RangeToExclusivePattern →
      .. RangePatternBound

RangeToInclusivePattern →
      ..= RangePatternBound

ObsoleteRangePattern →
    RangePatternBound ... RangePatternBound

RangePatternBound →
      LiteralPattern
    | PathExpression

Show syntax diagrams

[patterns.range.intro]
Range patterns match scalar values within the range defined by their bounds. They comprise a sigil (.. or ..=) and a bound on one or both sides.
A bound on the left of the sigil is called a lower bound. A bound on the right is called an upper bound.
[patterns.range.exclusive]
The exclusive range pattern matches all values from the lower bound up to, but not including the upper bound. It is written as its lower bound, followed by .., followed by the upper bound.
For example, a pattern 'm'..'p' will match only 'm', 'n' and 'o', specifically not including 'p'.
[patterns.range.inclusive]
The inclusive range pattern matches all values from the lower bound up to and including the upper bound. It is written as its lower bound, followed by ..=, followed by the upper bound.
For example, a pattern 'm'..='p' will match only the values 'm', 'n', 'o', and 'p'.
[patterns.range.from]
The from range pattern matches all values greater than or equal to the lower bound. It is written as its lower bound followed by ...
For example, 1.. will match any integer greater than or equal to 1, such as 1, 9, or 9001, or 9007199254740991 (if it is of an appropriate size), but not 0, and not negative numbers for signed integers.
[patterns.range.to-exclusive]
The to exclusive range pattern matches all values less than the upper bound. It is written as .. followed by the upper bound.
For example, ..10 will match any integer less than 10, such as 9, 1, 0, and for signed integer types, all negative values.
[patterns.range.to-inclusive]
The to inclusive range pattern matches all values less than or equal to the upper bound. It is written as ..= followed by the upper bound.
For example, ..=10 will match any integer less than or equal to 10, such as 10, 1, 0, and for signed integer types, all negative values.
[patterns.range.constraint-less-than]
The lower bound cannot be greater than the upper bound. That is, in a..=b, a ≤ b must be the case. For example, it is an error to have a range pattern 10..=0.
[patterns.range.bound]
A bound is written as one of:
A character, byte, integer, or float literal.
A - followed by an integer or float literal.
A path.
Note

We syntactically accept more than this for a RangePatternBound. We later reject the other things semantically.
[patterns.range.constraint-bound-path]
If a bound is written as a path, after macro resolution, the path must resolve to a constant item of the type char, an integer type, or a float type.
[patterns.range.type]
The range pattern matches the type of its upper and lower bounds, which must be the same type.
[patterns.range.path-value]
If a bound is a path, the bound matches the type and has the value of the constant the path resolves to.
[patterns.range.literal-value]
If a bound is a literal, the bound matches the type and has the value of the corresponding literal expression.
[patterns.range.negation]
If a bound is a literal preceded by a -, the bound matches the same type as the corresponding literal expression and has the value of negating the value of the corresponding literal expression.
[patterns.range.float-restriction]
For float range patterns, the constant may not be a NaN.
Examples:
let valid_variable = match c {
    'a'..='z' => true,
    'A'..='Z' => true,
    'α'..='ω' => true,
    _ => false,
};

println!("{}", match ph {
    0..7 => "acid",
    7 => "neutral",
    8..=14 => "base",
    _ => unreachable!(),
});

match uint {
    0 => "zero!",
    1.. => "positive number!",
};

// using paths to constants:
println!("{}", match altitude {
    TROPOSPHERE_MIN..=TROPOSPHERE_MAX => "troposphere",
    STRATOSPHERE_MIN..=STRATOSPHERE_MAX => "stratosphere",
    MESOSPHERE_MIN..=MESOSPHERE_MAX => "mesosphere",
    _ => "outer space, maybe",
});

if let size @ binary::MEGA..=binary::GIGA = n_items * bytes_per_item {
    println!("It fits and occupies {} bytes", size);
}

// using qualified paths:
println!("{}", match 0xfacade {
    0 ..= <u8 as MaxValue>::MAX => "fits in a u8",
    0 ..= <u16 as MaxValue>::MAX => "fits in a u16",
    0 ..= <u32 as MaxValue>::MAX => "fits in a u32",
    _ => "too big",
});
[patterns.range.refutable]
Range patterns for fix-width integer and char types are irrefutable when they span the entire set of possible values of a type. For example, 0u8..=255u8 is irrefutable.
[patterns.range.refutable-integer]
The range of values for an integer type is the closed range from its minimum to maximum value.
[patterns.range.refutable-char]
The range of values for a char type are precisely those ranges containing all Unicode Scalar Values: '\u{0000}'..='\u{D7FF}' and '\u{E000}'..='\u{10FFFF}'.
[patterns.range.constraint-slice]
RangeFromPattern cannot be used as a top-level pattern for subpatterns in slice patterns. For example, the pattern [1.., _] is not a valid pattern.
[patterns.range.edition2021]
2021
Edition differences

Before the 2021 edition, range patterns with both a lower and upper bound may also be written using ... in place of ..=, with the same meaning.
[patterns.ref]
Reference patterns
[patterns.ref.syntax]
Syntax
ReferencePattern → ( & | && ) mut? PatternWithoutRange

Show syntax diagrams

[patterns.ref.intro]
Reference patterns dereference the pointers that are being matched and, thus, borrow them.
For example, these two matches on x: &i32 are equivalent:
let int_reference = &3;

let a = match *int_reference { 0 => "zero", _ => "some" };
let b = match int_reference { &0 => "zero", _ => "some" };

assert_eq!(a, b);
[patterns.ref.ref-ref]
The grammar production for reference patterns has to match the token && to match a reference to a reference because it is a token by itself, not two & tokens.
[patterns.ref.mut]
Adding the mut keyword dereferences a mutable reference. The mutability must match the mutability of the reference.
[patterns.ref.refutable]
Reference patterns are always irrefutable.
[patterns.struct]
Struct patterns
[patterns.struct.syntax]
Syntax
StructPattern →
    PathInExpression {
        StructPatternElements?
    }

StructPatternElements →
      StructPatternFields ( , | , StructPatternEtCetera )?
    | StructPatternEtCetera

StructPatternFields →
    StructPatternField ( , StructPatternField )*

StructPatternField →
    OuterAttribute*
    (
        TUPLE_INDEX : Pattern
      | IDENTIFIER : Pattern
      | ref? mut? IDENTIFIER
    )

StructPatternEtCetera → ..

Show syntax diagrams

[patterns.struct.intro]
Struct patterns match struct, enum, and union values that match all criteria defined by its subpatterns. They are also used to destructure a struct, enum, or union value.
[patterns.struct.ignore-rest]
On a struct pattern, the fields are referenced by name, index (in the case of tuple structs) or ignored by use of ..:
match s {
    Point {x: 10, y: 20} => (),
    Point {y: 10, x: 20} => (),    // order doesn't matter
    Point {x: 10, ..} => (),
    Point {..} => (),
}

match t {
    PointTuple {0: 10, 1: 20} => (),
    PointTuple {1: 10, 0: 20} => (),   // order doesn't matter
    PointTuple {0: 10, ..} => (),
    PointTuple {..} => (),
}

match m {
    Message::Quit => (),
    Message::Move {x: 10, y: 20} => (),
    Message::Move {..} => (),
}
[patterns.struct.constraint-struct]
If .. is not used, a struct pattern used to match a struct is required to specify all fields:
match struct_value {
    Struct{a: 10, b: 'X', c: false} => (),
    Struct{a: 10, b: 'X', ref c} => (),
    Struct{a: 10, b: 'X', ref mut c} => (),
    Struct{a: 10, b: 'X', c: _} => (),
    Struct{a: _, b: _, c: _} => (),
}
[patterns.struct.constraint-union]
A struct pattern used to match a union must specify exactly one field (see Pattern matching on unions).
[patterns.struct.binding-shorthand]
The ref and/or mut IDENTIFIER syntax matches any value and binds it to a variable with the same name as the given field.
let Struct{a: x, b: y, c: z} = struct_value;          // destructure all fields
[patterns.struct.refutable]
A struct pattern is refutable if the PathInExpression resolves to a constructor of an enum with more than one variant, or one of its subpatterns is refutable.
[patterns.struct.namespace]
A struct pattern matches against the struct, union, or enum variant whose constructor is resolved from PathInExpression in the type namespace. See patterns.tuple-struct.namespace for more details.
[patterns.tuple-struct]
Tuple struct patterns
[patterns.tuple-struct.syntax]
Syntax
TupleStructPattern → PathInExpression ( TupleStructItems? )

TupleStructItems → Pattern ( , Pattern )* ,?

Show syntax diagrams

[patterns.tuple-struct.intro]
Tuple struct patterns match tuple struct and enum values that match all criteria defined by its subpatterns. They are also used to destructure a tuple struct or enum value.
[patterns.tuple-struct.refutable]
A tuple struct pattern is refutable if the PathInExpression resolves to a constructor of an enum with more than one variant, or one of its subpatterns is refutable.
[patterns.tuple-struct.namespace]
A tuple struct pattern matches against the tuple struct or tuple-like enum variant whose constructor is resolved from PathInExpression in the value namespace.
Note

Conversely, a struct pattern for a tuple struct or tuple-like enum variant, e.g. S { 0: _ }, matches against the tuple struct or variant whose constructor is resolved in the type namespace.

enum E1 { V(u16) }
enum E2 { V(u32) }

// Import `E1::V` from the type namespace only.
mod _0 {
    const V: () = (); // For namespace masking.
    pub(super) use super::E1::*;
}
use _0::*;

// Import `E2::V` from the value namespace only.
mod _1 {
    struct V {} // For namespace masking.
    pub(super) use super::E2::*;
}
use _1::*;

fn f() {
    // This struct pattern matches against the tuple-like
    // enum variant whose constructor was found in the type
    // namespace.
    let V { 0: ..=u16::MAX } = (loop {}) else { loop {} };
    // This tuple struct pattern matches against the tuple-like
    // enum variant whose constructor was found in the value
    // namespace.
    let V(..=u32::MAX) = (loop {}) else { loop {} };
}
The Lang team has made certain decisions, such as in PR #138458, that raise questions about the desirability of using the value namespace in this way for patterns, as described in PR #140593. It might be prudent to not intentionally rely on this nuance in your code.
[patterns.tuple]
Tuple patterns
[patterns.tuple.syntax]
Syntax
TuplePattern → ( TuplePatternItems? )

TuplePatternItems →
      Pattern ,
    | RestPattern
    | Pattern ( , Pattern )+ ,?

Show syntax diagrams

[patterns.tuple.intro]
Tuple patterns match tuple values that match all criteria defined by its subpatterns. They are also used to destructure a tuple.
[patterns.tuple.rest-syntax]
The form (..) with a single RestPattern is a special form that does not require a comma, and matches a tuple of any size.
[patterns.tuple.refutable]
The tuple pattern is refutable when one of its subpatterns is refutable.
An example of using tuple patterns:
let pair = (10, "ten");
let (a, b) = pair;

assert_eq!(a, 10);
assert_eq!(b, "ten");
[patterns.paren]
Grouped patterns
[patterns.paren.syntax]
Syntax
GroupedPattern → ( Pattern )

Show syntax diagrams

[patterns.paren.intro]
Enclosing a pattern in parentheses can be used to explicitly control the precedence of compound patterns. For example, a reference pattern next to a range pattern such as &0..=5 is ambiguous and is not allowed, but can be expressed with parentheses.
let int_reference = &3;
match int_reference {
    &(0..=5) => (),
    _ => (),
}
[patterns.slice]
Slice patterns
[patterns.slice.syntax]
Syntax
SlicePattern → [ SlicePatternItems? ]

SlicePatternItems → Pattern ( , Pattern )* ,?

Show syntax diagrams

[patterns.slice.intro]
Slice patterns can match both arrays of fixed size and slices of dynamic size.
// Fixed size
let arr = [1, 2, 3];
match arr {
    [1, _, _] => "starts with one",
    [a, b, c] => "starts with something else",
};
// Dynamic size
let v = vec![1, 2, 3];
match v[..] {
    [a, b] => { /* this arm will not apply because the length doesn't match */ }
    [a, b, c] => { /* this arm will apply */ }
    _ => { /* this wildcard is required, since the length is not known statically */ }
};
[patterns.slice.refutable-array]
Slice patterns are irrefutable when matching an array as long as each element is irrefutable.
[patterns.slice.refutable-slice]
When matching a slice, it is irrefutable only in the form with a single .. rest pattern or identifier pattern with the .. rest pattern as a subpattern.
[patterns.slice.restriction]
Within a slice, a range pattern without both lower and upper bound must be enclosed in parentheses, as in (a..), to clarify it is intended to match against a single slice element. A range pattern with both lower and upper bound, like a..=b, is not required to be enclosed in parentheses.
[patterns.path]
Path patterns
[patterns.path.syntax]
Syntax
PathPattern → PathExpression

Show syntax diagrams

[patterns.path.intro]
Path patterns are patterns that refer either to constant values or to structs or enum variants that have no fields.
[patterns.path.unqualified]
Unqualified path patterns can refer to:
enum variants
structs
constants
associated constants
[patterns.path.qualified]
Qualified path patterns can only refer to associated constants.
[patterns.path.refutable]
Path patterns are irrefutable when they refer to structs or an enum variant when the enum has only one variant or a constant whose type is irrefutable. They are refutable when they refer to refutable constants or enum variants for enums with multiple variants.
[patterns.const]
Constant patterns
[patterns.const.partial-eq]
When a constant C of type T is used as a pattern, we first check that T: PartialEq.
[patterns.const.structural-equality]
Furthermore we require that the value of C has (recursive) structural equality, which is defined recursively as follows:
[patterns.const.primitive]
Integers as well as str, bool and char values always have structural equality.
[patterns.const.builtin-aggregate]
Tuples, arrays, and slices have structural equality if all their fields/elements have structural equality. (In particular, () and [] always have structural equality.)
[patterns.const.ref]
References have structural equality if the value they point to has structural equality.
[patterns.const.aggregate]
A value of struct or enum type has structural equality if its PartialEq instance is derived via #[derive(PartialEq)], and all fields (for enums: of the active variant) have structural equality.
[patterns.const.pointer]
A raw pointer has structural equality if it was defined as a constant integer (and then cast/transmuted).
[patterns.const.float]
A float value has structural equality if it is not a NaN.
[patterns.const.exhaustive]
Nothing else has structural equality.
[patterns.const.generic]
In particular, the value of C must be known at pattern-building time (which is pre-monomorphization). This means that associated consts that involve generic parameters cannot be used as patterns.
[patterns.const.immutable]
The value of C must not contain any references to mutable statics (static mut items or interior mutable static items) or extern statics.
[patterns.const.translation]
After ensuring all conditions are met, the constant value is translated into a pattern, and now behaves exactly as-if that pattern had been written directly. In particular, it fully participates in exhaustiveness checking. (For raw pointers, constants are the only way to write such patterns. Only _ is ever considered exhaustive for these types.)
[patterns.or]
Or-patterns
Or-patterns are patterns that match on one of two or more sub-patterns (for example A | B | C). They can nest arbitrarily. Syntactically, or-patterns are allowed in any of the places where other patterns are allowed (represented by the Pattern production), with the exceptions of let-bindings and function and closure arguments (represented by the PatternNoTopAlt production).
[patterns.constraints]
Static semantics
[patterns.constraints.pattern]
Given a pattern p | q at some depth for some arbitrary patterns p and q, the pattern is considered ill-formed if:

the type inferred for p does not unify with the type inferred for q, or
the same set of bindings are not introduced in p and q, or
the type of any two bindings with the same name in p and q do not unify with respect to types or binding modes.
Unification of types is in all instances aforementioned exact and implicit type coercions do not apply.

[patterns.constraints.match-type-check]
When type checking an expression match e_s { a_1 => e_1, ... a_n => e_n }, for each match arm a_i which contains a pattern of form p_i | q_i, the pattern p_i | q_i is considered ill formed if, at the depth d where it exists the fragment of e_s at depth d, the type of the expression fragment does not unify with p_i | q_i.
[patterns.constraints.exhaustiveness-or-pattern]
With respect to exhaustiveness checking, a pattern p | q is considered to cover p as well as q. For some constructor c(x, ..) the distributive law applies such that c(p | q, ..rest) covers the same set of value as c(p, ..rest) | c(q, ..rest) does. This can be applied recursively until there are no more nested patterns of form p | q other than those that exist at the top level.

Note that by “constructor” we do not refer to tuple struct patterns, but rather we refer to a pattern for any product type. This includes enum variants, tuple structs, structs with named fields, arrays, tuples, and slices.

[patterns.behavior]
Dynamic semantics
[patterns.behavior.nested-or-patterns]
The dynamic semantics of pattern matching a scrutinee expression e_s against a pattern c(p | q, ..rest) at depth d where c is some constructor, p and q are arbitrary patterns, and rest is optionally any remaining potential factors in c, is defined as being the same as that of c(p, ..rest) | c(q, ..rest).
[patterns.precedence]
Precedence with other undelimited patterns
As shown elsewhere in this chapter, there are several types of patterns that are syntactically undelimited, including identifier patterns, reference patterns, and or-patterns. Or-patterns always have the lowest-precedence. This allows us to reserve syntactic space for a possible future type ascription feature and also to reduce ambiguity. For example, x @ A(..) | B(..) will result in an error that x is not bound in all patterns. &A(x) | B(x) will result in a type mismatch between x in the different subpatterns.
The ObsoleteRangePattern syntax has been removed in the 2021 edition. ↩
