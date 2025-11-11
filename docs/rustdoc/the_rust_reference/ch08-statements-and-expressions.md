# Statements and expressions
Rust is primarily an expression language. This means that most forms of value-producing or effect-causing evaluation are directed by the uniform syntax category of expressions. Each kind of expression can typically nest within each other kind of expression, and rules for evaluation of expressions involve specifying both the value produced by the expression and the order in which its sub-expressions are themselves evaluated.
In contrast, statements serve mostly to contain and explicitly sequence expression evaluation.
[statement]
## Statements

[statement.syntax]
Syntax
Statement →
      ;
    | Item
    | LetStatement
    | ExpressionStatement
    | OuterAttribute* MacroInvocationSemi

Show syntax diagrams

[statement.intro]
A statement is a component of a block, which is in turn a component of an outer expression or function.
[statement.kind]
Rust has two kinds of statement: declaration statements and expression statements.
[statement.decl]
Declaration statements
A declaration statement is one that introduces one or more names into the enclosing statement block. The declared names may denote new variables or new items.
The two kinds of declaration statements are item declarations and let statements.
[statement.item]
Item declarations
[statement.item.intro]
An item declaration statement has a syntactic form identical to an item declaration within a module.
[statement.item.scope]
Declaring an item within a statement block restricts its scope to the block containing the statement. The item is not given a canonical path nor are any sub-items it may declare.
[statement.item.associated-scope]
The exception to this is that associated items defined by implementations are still accessible in outer scopes as long as the item and, if applicable, trait are accessible. It is otherwise identical in meaning to declaring the item inside a module.
[statement.item.outer-generics]
There is no implicit capture of the containing function’s generic parameters, parameters, and local variables. For example, inner may not access outer_var.
fn outer() {
  let outer_var = true;

  fn inner() { /* outer_var is not in scope here */ }

  inner();
}
[statement.let]
let statements
[statement.let.syntax]
Syntax
LetStatement →
    OuterAttribute* let PatternNoTopAlt ( : Type )?
    (
          = Expression
        | = Expressionexcept LazyBooleanExpression or end with a } else BlockExpression
    )? ;

Show syntax diagrams

[statement.let.intro]
A let statement introduces a new set of variables, given by a pattern. The pattern is followed optionally by a type annotation and then either ends, or is followed by an initializer expression plus an optional else block.
[statement.let.inference]
When no type annotation is given, the compiler will infer the type, or signal an error if insufficient type information is available for definite inference.
[statement.let.scope]
Any variables introduced by a variable declaration are visible from the point of declaration until the end of the enclosing block scope, except when they are shadowed by another variable declaration.
[statement.let.constraint]
If an else block is not present, the pattern must be irrefutable. If an else block is present, the pattern may be refutable.
[statement.let.behavior]
If the pattern does not match (this requires it to be refutable), the else block is executed. The else block must always diverge (evaluate to the never type).
let (mut v, w) = (vec![1, 2, 3], 42); // The bindings may be mut or const
let Some(t) = v.pop() else { // Refutable patterns require an else block
    panic!(); // The else block must diverge
};
let [u, v] = [v[0], v[1]] else { // This pattern is irrefutable, so the compiler
                                 // will lint as the else block is redundant.
    panic!();
};
[statement.expr]
Expression statements
[statement.expr.syntax]
Syntax
ExpressionStatement →
      ExpressionWithoutBlock ;
    | ExpressionWithBlock ;?

Show syntax diagrams

[statement.expr.intro]
An expression statement is one that evaluates an expression and ignores its result. As a rule, an expression statement’s purpose is to trigger the effects of evaluating its expression.
[statement.expr.restriction-semicolon]
An expression that consists of only a block expression or control flow expression, if used in a context where a statement is permitted, can omit the trailing semicolon. This can cause an ambiguity between it being parsed as a standalone statement and as a part of another expression; in this case, it is parsed as a statement.
[statement.expr.constraint-block]
The type of ExpressionWithBlock expressions when used as statements must be the unit type.
v.pop();          // Ignore the element returned from pop
if v.is_empty() {
    v.push(5);
} else {
    v.remove(0);
}                 // Semicolon can be omitted.
[1];              // Separate expression statement, not an indexing expression.
When the trailing semicolon is omitted, the result must be type ().
// bad: the block's type is i32, not ()
// Error: expected `()` because of default return type
// if true {
//   1
// }

// good: the block's type is i32
if true {
  1
} else {
  2
};
[statement.attribute]
Attributes on Statements
Statements accept outer attributes. The attributes that have meaning on a statement are cfg, and the lint check attributes.
[expr]
## Expressions

[expr.syntax]
Syntax
Expression →
      ExpressionWithoutBlock
    | ExpressionWithBlock

ExpressionWithoutBlock →
    OuterAttribute*
    (
        LiteralExpression
      | PathExpression
      | OperatorExpression
      | GroupedExpression
      | ArrayExpression
      | AwaitExpression
      | IndexExpression
      | TupleExpression
      | TupleIndexingExpression
      | StructExpression
      | CallExpression
      | MethodCallExpression
      | FieldExpression
      | ClosureExpression
      | AsyncBlockExpression
      | ContinueExpression
      | BreakExpression
      | RangeExpression
      | ReturnExpression
      | UnderscoreExpression
      | MacroInvocation
    )

ExpressionWithBlock →
    OuterAttribute*
    (
        BlockExpression
      | ConstBlockExpression
      | UnsafeBlockExpression
      | LoopExpression
      | IfExpression
      | MatchExpression
    )

Show syntax diagrams

[expr.intro]
An expression may have two roles: it always produces a value, and it may have effects (otherwise known as “side effects”).
[expr.evaluation]
An expression evaluates to a value, and has effects during evaluation.
[expr.operands]
Many expressions contain sub-expressions, called the operands of the expression.
[expr.behavior]
The meaning of each kind of expression dictates several things:
Whether or not to evaluate the operands when evaluating the expression
The order in which to evaluate the operands
How to combine the operands’ values to obtain the value of the expression
[expr.structure]
In this way, the structure of expressions dictates the structure of execution. Blocks are just another kind of expression, so blocks, statements, expressions, and blocks again can recursively nest inside each other to an arbitrary depth.
Note

We give names to the operands of expressions so that we may discuss them, but these names are not stable and may be changed.
[expr.precedence]
Expression precedence
The precedence of Rust operators and expressions is ordered as follows, going from strong to weak. Binary Operators at the same precedence level are grouped in the order given by their associativity.
Operator/Expression	Associativity
Paths	
Method calls	
Field expressions	left to right
Function calls, array indexing	
?	
Unary - ! * borrow	
as	left to right
* / %	left to right
+ -	left to right
<< >>	left to right
&	left to right
^	left to right
|	left to right
== != < > <= >=	Require parentheses
&&	left to right
||	left to right
.. ..=	Require parentheses
= += -= *= /= %=
&= |= ^= <<= >>=	right to left
return break closures	
[expr.operand-order]
Evaluation order of operands
[expr.operand-order.default]
The following list of expressions all evaluate their operands the same way, as described after the list. Other expressions either don’t take operands or evaluate them conditionally as described on their respective pages.
Dereference expression
Error propagation expression
Negation expression
Arithmetic and logical binary operators
Comparison operators
Type cast expression
Grouped expression
Array expression
Await expression
Index expression
Tuple expression
Tuple index expression
Struct expression
Call expression
Method call expression
Field expression
Break expression
Range expression
Return expression
[expr.operand-order.operands-before-primary]
The operands of these expressions are evaluated prior to applying the effects of the expression. Expressions taking multiple operands are evaluated left to right as written in the source code.
Note

Which subexpressions are the operands of an expression is determined by expression precedence as per the previous section.
For example, the two next method calls will always be called in the same order:
let mut one_two = vec![1, 2].into_iter();
assert_eq!(
    (1, 2),
    (one_two.next().unwrap(), one_two.next().unwrap())
);
Note

Since this is applied recursively, these expressions are also evaluated from innermost to outermost, ignoring siblings until there are no inner subexpressions.
[expr.place-value]
Place Expressions and Value Expressions
[expr.place-value.intro]
Expressions are divided into two main categories: place expressions and value expressions; there is also a third, minor category of expressions called assignee expressions. Within each expression, operands may likewise occur in either place context or value context. The evaluation of an expression depends both on its own category and the context it occurs within.
[expr.place-value.place-memory-location]
A place expression is an expression that represents a memory location.
[expr.place-value.place-expr-kinds]
### Array and index expressions
[expr.place-value.value-expr-kinds]
All other expressions are value expressions.
[expr.place-value.value-result]
A value expression is an expression that represents an actual value.
[expr.place-value.place-context]
The following contexts are place expression contexts:
The left operand of a compound assignment expression.
The operand of a unary borrow, raw borrow or dereference operator.
The operand of a field expression.
The indexed operand of an array indexing expression.
The operand of any implicit borrow.
The initializer of a let statement.
The scrutinee of an if let, match, or while let expression.
The base of a functional update struct expression.
Note

Historically, place expressions were called lvalues and value expressions were called rvalues.
[expr.place-value.assignee]
An assignee expression is an expression that appears in the left operand of an assignment expression. Explicitly, the assignee expressions are:
Place expressions.
Underscores.
Tuples of assignee expressions.
Slices of assignee expressions.
Tuple structs of assignee expressions.
Structs of assignee expressions (with optionally named fields).
Unit structs
[expr.place-value.parenthesis]
Arbitrary parenthesisation is permitted inside assignee expressions.
[expr.move]
Moved and copied types
[expr.move.intro]
When a place expression is evaluated in a value expression context, or is bound by value in a pattern, it denotes the value held in that memory location.
[expr.move.copy]
If the type of that value implements Copy, then the value will be copied.
[expr.move.requires-sized]
In the remaining situations, if that type is Sized, then it may be possible to move the value.
[expr.move.movable-place]
Only the following place expressions may be moved out of:
Variables which are not currently borrowed.
Temporary values.
Fields of a place expression which can be moved out of and don’t implement Drop.
The result of dereferencing an expression with type Box<T> and that can also be moved out of.
[expr.move.deinitialization]
After moving out of a place expression that evaluates to a local variable, the location is deinitialized and cannot be read from again until it is reinitialized.
[expr.move.place-invalid]
In all other cases, trying to use a place expression in a value expression context is an error.
[expr.mut]
Mutability
[expr.mut.intro]
For a place expression to be assigned to, mutably borrowed, implicitly mutably borrowed, or bound to a pattern containing ref mut, it must be mutable. We call these mutable place expressions. In contrast, other place expressions are called immutable place expressions.
[expr.mut.valid-places]
The following expressions can be mutable place expression contexts:
Mutable variables which are not currently borrowed.
Mutable static items.
Temporary values.
Fields: this evaluates the subexpression in a mutable place expression context.
Dereferences of a *mut T pointer.
Dereference of a variable, or field of a variable, with type &mut T. Note: This is an exception to the requirement of the next rule.
Dereferences of a type that implements DerefMut: this then requires that the value being dereferenced is evaluated in a mutable place expression context.
Array indexing of a type that implements IndexMut: this then evaluates the value being indexed, but not the index, in mutable place expression context.
[expr.temporary]
Temporaries
When using a value expression in most place expression contexts, a temporary unnamed memory location is created and initialized to that value. The expression evaluates to that location instead, except if promoted to a static. The drop scope of the temporary is usually the end of the enclosing statement.
[expr.implicit-borrow]
Implicit Borrows
[expr.implicit-borrow-intro]
Certain expressions will treat an expression as a place expression by implicitly borrowing it. For example, it is possible to compare two unsized slices for equality directly, because the == operator implicitly borrows its operands:
let a: &[i32];
let b: &[i32];
// ...
*a == *b;
// Equivalent form:
::std::cmp::PartialEq::eq(&*a, &*b);
[expr.implicit-borrow.application]
Implicit borrows may be taken in the following expressions:
### Method call expressions
Left operand in field expressions.
Left operand in call expressions.
Left operand in array indexing expressions.
Operand of the dereference operator (*).
Operands of comparison.
Left operands of the compound assignment.
[expr.overload]
Overloading Traits
Many of the following operators and expressions can also be overloaded for other types using traits in std::ops or std::cmp. These traits also exist in core::ops and core::cmp with the same names.
[expr.attr]
Expression Attributes
[expr.attr.restriction]
Outer attributes before an expression are allowed only in a few specific cases:
Before an expression used as a statement.
Elements of array expressions, tuple expressions, call expressions, and tuple-style struct expressions.
The tail expression of block expressions.
[expr.attr.never-before]
They are never allowed before:
Range expressions.
Binary operator expressions (ArithmeticOrLogicalExpression, ComparisonExpression, LazyBooleanExpression, TypeCastExpression, AssignmentExpression, CompoundAssignmentExpression).
[expr.literal]
### Literal expressions

[expr.literal.syntax]
Syntax
LiteralExpression →
      CHAR_LITERAL
    | STRING_LITERAL
    | RAW_STRING_LITERAL
    | BYTE_LITERAL
    | BYTE_STRING_LITERAL
    | RAW_BYTE_STRING_LITERAL
    | C_STRING_LITERAL
    | RAW_C_STRING_LITERAL
    | INTEGER_LITERAL
    | FLOAT_LITERAL
    | true
    | false

Show syntax diagrams

[expr.literal.intro]
A literal expression is an expression consisting of a single token, rather than a sequence of tokens, that immediately and directly denotes the value it evaluates to, rather than referring to it by name or some other evaluation rule.
[expr.literal.const-expr]
A literal is a form of constant expression, so is evaluated (primarily) at compile time.
[expr.literal.literal-token]
Each of the lexical literal forms described earlier can make up a literal expression, as can the keywords true and false.
"hello";   // string type
'5';       // character type
5;         // integer type
[expr.literal.string-representation]
In the descriptions below, the string representation of a token is the sequence of characters from the input which matched the token’s production in a Lexer grammar snippet.
Note

This string representation never includes a character U+000D (CR) immediately followed by U+000A (LF): this pair would have been previously transformed into a single U+000A (LF).
[expr.literal.escape]
Escapes
[expr.literal.escape.intro]
The descriptions of textual literal expressions below make use of several forms of escape.
[expr.literal.escape.sequence]
Each form of escape is characterised by:
an escape sequence: a sequence of characters, which always begins with U+005C (\)
an escaped value: either a single character or an empty sequence of characters
In the definitions of escapes below:
An octal digit is any of the characters in the range [0-7].
A hexadecimal digit is any of the characters in the ranges [0-9], [a-f], or [A-F].
[expr.literal.escape.simple]
Simple escapes
Each sequence of characters occurring in the first column of the following table is an escape sequence.
In each case, the escaped value is the character given in the corresponding entry in the second column.
Escape sequence	Escaped value
\0	U+0000 (NUL)
\t	U+0009 (HT)
\n	U+000A (LF)
\r	U+000D (CR)
\"	U+0022 (QUOTATION MARK)
\'	U+0027 (APOSTROPHE)
\\	U+005C (REVERSE SOLIDUS)
[expr.literal.escape.hex-octet]
8-bit escapes
The escape sequence consists of \x followed by two hexadecimal digits.
The escaped value is the character whose Unicode scalar value is the result of interpreting the final two characters in the escape sequence as a hexadecimal integer, as if by u8::from_str_radix with radix 16.
Note

The escaped value therefore has a Unicode scalar value in the range of u8.
[expr.literal.escape.hex-ascii]
7-bit escapes
The escape sequence consists of \x followed by an octal digit then a hexadecimal digit.
The escaped value is the character whose Unicode scalar value is the result of interpreting the final two characters in the escape sequence as a hexadecimal integer, as if by u8::from_str_radix with radix 16.
[expr.literal.escape.unicode]
Unicode escapes
The escape sequence consists of \u{, followed by a sequence of characters each of which is a hexadecimal digit or _, followed by }.
The escaped value is the character whose Unicode scalar value is the result of interpreting the hexadecimal digits contained in the escape sequence as a hexadecimal integer, as if by u32::from_str_radix with radix 16.
Note

The permitted forms of a CHAR_LITERAL or STRING_LITERAL token ensure that there is such a character.
[expr.literal.continuation]
String continuation escapes
The escape sequence consists of \ followed immediately by U+000A (LF), and all following whitespace characters before the next non-whitespace character. For this purpose, the whitespace characters are U+0009 (HT), U+000A (LF), U+000D (CR), and U+0020 (SPACE).
The escaped value is an empty sequence of characters.
Note

The effect of this form of escape is that a string continuation skips following whitespace, including additional newlines. Thus a, b and c are equal:

let a = "foobar";
let b = "foo\
         bar";
let c = "foo\

     bar";

assert_eq!(a, b);
assert_eq!(b, c);
Skipping additional newlines (as in example c) is potentially confusing and unexpected. This behavior may be adjusted in the future. Until a decision is made, it is recommended to avoid relying on skipping multiple newlines with line continuations. See this issue for more information.
[expr.literal.char]
Character literal expressions
[expr.literal.char.intro]
A character literal expression consists of a single CHAR_LITERAL token.
[expr.literal.char.type]
The expression’s type is the primitive char type.
[expr.literal.char.no-suffix]
The token must not have a suffix.
[expr.literal.char.literal-content]
The token’s literal content is the sequence of characters following the first U+0027 (') and preceding the last U+0027 (') in the string representation of the token.
[expr.literal.char.represented]
The literal expression’s represented character is derived from the literal content as follows:
[expr.literal.char.escape]
If the literal content is one of the following forms of escape sequence, the represented character is the escape sequence’s escaped value:
Simple escapes
7-bit escapes
Unicode escapes
[expr.literal.char.single]
Otherwise the represented character is the single character that makes up the literal content.
[expr.literal.char.result]
The expression’s value is the char corresponding to the represented character’s Unicode scalar value.
Note

The permitted forms of a CHAR_LITERAL token ensure that these rules always produce a single character.
Examples of character literal expressions:
'R';                               // R
'\'';                              // '
'\x52';                            // R
'\u{00E6}';                        // LATIN SMALL LETTER AE (U+00E6)
[expr.literal.string]
String literal expressions
[expr.literal.string.intro]
A string literal expression consists of a single STRING_LITERAL or RAW_STRING_LITERAL token.
[expr.literal.string.type]
The expression’s type is a shared reference (with static lifetime) to the primitive str type. That is, the type is &'static str.
[expr.literal.string.no-suffix]
The token must not have a suffix.
[expr.literal.string.literal-content]
The token’s literal content is the sequence of characters following the first U+0022 (") and preceding the last U+0022 (") in the string representation of the token.
[expr.literal.string.represented]
The literal expression’s represented string is a sequence of characters derived from the literal content as follows:
[expr.literal.string.escape]
If the token is a STRING_LITERAL, each escape sequence of any of the following forms occurring in the literal content is replaced by the escape sequence’s escaped value.

Simple escapes
7-bit escapes
Unicode escapes
String continuation escapes
These replacements take place in left-to-right order. For example, the token "\\x41" is converted to the characters \ x 4 1.
[expr.literal.string.raw]
If the token is a RAW_STRING_LITERAL, the represented string is identical to the literal content.
[expr.literal.string.result]
The expression’s value is a reference to a statically allocated str containing the UTF-8 encoding of the represented string.
Examples of string literal expressions:
"foo"; r"foo";                     // foo
"\"foo\""; r#""foo""#;             // "foo"

"foo #\"# bar";
r##"foo #"# bar"##;                // foo #"# bar

"\x52"; "R"; r"R";                 // R
"\\x52"; r"\x52";                  // \x52
[expr.literal.byte-char]
Byte literal expressions
[expr.literal.byte-char.intro]
A byte literal expression consists of a single BYTE_LITERAL token.
[expr.literal.byte-char.literal]
The expression’s type is the primitive u8 type.
[expr.literal.byte-char.no-suffix]
The token must not have a suffix.
[expr.literal.byte-char.literal-content]
The token’s literal content is the sequence of characters following the first U+0027 (') and preceding the last U+0027 (') in the string representation of the token.
[expr.literal.byte-char.represented]
The literal expression’s represented character is derived from the literal content as follows:
[expr.literal.byte-char.escape]
If the literal content is one of the following forms of escape sequence, the represented character is the escape sequence’s escaped value:
Simple escapes
8-bit escapes
[expr.literal.byte-char.single]
Otherwise the represented character is the single character that makes up the literal content.
[expr.literal.byte-char.result]
The expression’s value is the represented character’s Unicode scalar value.
Note

The permitted forms of a BYTE_LITERAL token ensure that these rules always produce a single character, whose Unicode scalar value is in the range of u8.
Examples of byte literal expressions:
b'R';                              // 82
b'\'';                             // 39
b'\x52';                           // 82
b'\xA0';                           // 160
[expr.literal.byte-string]
Byte string literal expressions
[expr.literal.byte-string.intro]
A byte string literal expression consists of a single BYTE_STRING_LITERAL or RAW_BYTE_STRING_LITERAL token.
[expr.literal.byte-string.type]
The expression’s type is a shared reference (with static lifetime) to an array whose element type is u8. That is, the type is &'static [u8; N], where N is the number of bytes in the represented string described below.
[expr.literal.byte-string.no-suffix]
The token must not have a suffix.
[expr.literal.byte-string.literal-content]
The token’s literal content is the sequence of characters following the first U+0022 (") and preceding the last U+0022 (") in the string representation of the token.
[expr.literal.byte-string.represented]
The literal expression’s represented string is a sequence of characters derived from the literal content as follows:
[expr.literal.byte-string.escape]
If the token is a BYTE_STRING_LITERAL, each escape sequence of any of the following forms occurring in the literal content is replaced by the escape sequence’s escaped value.

Simple escapes
8-bit escapes
String continuation escapes
These replacements take place in left-to-right order. For example, the token b"\\x41" is converted to the characters \ x 4 1.
[expr.literal.byte-string.raw]
If the token is a RAW_BYTE_STRING_LITERAL, the represented string is identical to the literal content.
[expr.literal.byte-string.result]
The expression’s value is a reference to a statically allocated array containing the Unicode scalar values of the characters in the represented string, in the same order.
Note

The permitted forms of BYTE_STRING_LITERAL and RAW_BYTE_STRING_LITERAL tokens ensure that these rules always produce array element values in the range of u8.
Examples of byte string literal expressions:
b"foo"; br"foo";                     // foo
b"\"foo\""; br#""foo""#;             // "foo"

b"foo #\"# bar";
br##"foo #"# bar"##;                 // foo #"# bar

b"\x52"; b"R"; br"R";                // R
b"\\x52"; br"\x52";                  // \x52
[expr.literal.c-string]
C string literal expressions
[expr.literal.c-string.intro]
A C string literal expression consists of a single C_STRING_LITERAL or RAW_C_STRING_LITERAL token.
[expr.literal.c-string.type]
The expression’s type is a shared reference (with static lifetime) to the standard library CStr type. That is, the type is &'static core::ffi::CStr.
[expr.literal.c-string.no-suffix]
The token must not have a suffix.
[expr.literal.c-string.literal-content]
The token’s literal content is the sequence of characters following the first " and preceding the last " in the string representation of the token.
[expr.literal.c-string.represented]
The literal expression’s represented bytes are a sequence of bytes derived from the literal content as follows:
[expr.literal.c-string.escape]
If the token is a C_STRING_LITERAL, the literal content is treated as a sequence of items, each of which is either a single Unicode character other than \ or an escape. The sequence of items is converted to a sequence of bytes as follows:
Each single Unicode character contributes its UTF-8 representation.
Each simple escape contributes the Unicode scalar value of its escaped value.
Each 8-bit escape contributes a single byte containing the Unicode scalar value of its escaped value.
Each unicode escape contributes the UTF-8 representation of its escaped value.
Each string continuation escape contributes no bytes.
[expr.literal.c-string.raw]
If the token is a RAW_C_STRING_LITERAL, the represented bytes are the UTF-8 encoding of the literal content.
Note

The permitted forms of C_STRING_LITERAL and RAW_C_STRING_LITERAL tokens ensure that the represented bytes never include a null byte.
[expr.literal.c-string.result]
The expression’s value is a reference to a statically allocated CStr whose array of bytes contains the represented bytes followed by a null byte.
Examples of C string literal expressions:
c"foo"; cr"foo";                     // foo
c"\"foo\""; cr#""foo""#;             // "foo"

c"foo #\"# bar";
cr##"foo #"# bar"##;                 // foo #"# bar

c"\x52"; c"R"; cr"R";                // R
c"\\x52"; cr"\x52";                  // \x52

c"æ";                                // LATIN SMALL LETTER AE (U+00E6)
c"\u{00E6}";                         // LATIN SMALL LETTER AE (U+00E6)
c"\xC3\xA6";                         // LATIN SMALL LETTER AE (U+00E6)

c"\xE6".to_bytes();                  // [230]
c"\u{00E6}".to_bytes();              // [195, 166]
[expr.literal.int]
Integer literal expressions
[expr.literal.int.intro]
An integer literal expression consists of a single INTEGER_LITERAL token.
[expr.literal.int.suffix]
If the token has a suffix, the suffix must be the name of one of the primitive integer types: u8, i8, u16, i16, u32, i32, u64, i64, u128, i128, usize, or isize, and the expression has that type.
[expr.literal.int.infer]
If the token has no suffix, the expression’s type is determined by type inference:
[expr.literal.int.inference-unique-type]
If an integer type can be uniquely determined from the surrounding program context, the expression has that type.
[expr.literal.int.inference-default]
If the program context under-constrains the type, it defaults to the signed 32-bit integer i32.
[expr.literal.int.inference-error]
If the program context over-constrains the type, it is considered a static type error.
Examples of integer literal expressions:
123;                               // type i32
123i32;                            // type i32
123u32;                            // type u32
123_u32;                           // type u32
let a: u64 = 123;                  // type u64

0xff;                              // type i32
0xff_u8;                           // type u8

0o70;                              // type i32
0o70_i16;                          // type i16

0b1111_1111_1001_0000;             // type i32
0b1111_1111_1001_0000i64;          // type i64

0usize;                            // type usize
[expr.literal.int.representation]
The value of the expression is determined from the string representation of the token as follows:
[expr.literal.int.radix]
An integer radix is chosen by inspecting the first two characters of the string, as follows:

0b indicates radix 2
0o indicates radix 8
0x indicates radix 16
otherwise the radix is 10.
[expr.literal.int.radix-prefix-stripped]
If the radix is not 10, the first two characters are removed from the string.
[expr.literal.int.type-suffix-stripped]
Any suffix is removed from the string.
[expr.literal.int.separators-stripped]
Any underscores are removed from the string.
[expr.literal.int.u128-value]
The string is converted to a u128 value as if by u128::from_str_radix with the chosen radix. If the value does not fit in u128, it is a compiler error.
[expr.literal.int.cast]
The u128 value is converted to the expression’s type via a numeric cast.
Note

The final cast will truncate the value of the literal if it does not fit in the expression’s type. rustc includes a lint check named overflowing_literals, defaulting to deny, which rejects expressions where this occurs.
Note

-1i8, for example, is an application of the negation operator to the literal expression 1i8, not a single integer literal expression. See Overflow for notes on representing the most negative value for a signed type.
[expr.literal.float]
Floating-point literal expressions
[expr.literal.float.intro]
A floating-point literal expression has one of two forms:
a single FLOAT_LITERAL token
a single INTEGER_LITERAL token which has a suffix and no radix indicator
[expr.literal.float.suffix]
If the token has a suffix, the suffix must be the name of one of the primitive floating-point types: f32 or f64, and the expression has that type.
[expr.literal.float.infer]
If the token has no suffix, the expression’s type is determined by type inference:
[expr.literal.float.inference-unique-type]
If a floating-point type can be uniquely determined from the surrounding program context, the expression has that type.
[expr.literal.float.inference-default]
If the program context under-constrains the type, it defaults to f64.
[expr.literal.float.inference-error]
If the program context over-constrains the type, it is considered a static type error.
Examples of floating-point literal expressions:
123.0f64;        // type f64
0.1f64;          // type f64
0.1f32;          // type f32
12E+99_f64;      // type f64
5f32;            // type f32
let x: f64 = 2.; // type f64
[expr.literal.float.result]
The value of the expression is determined from the string representation of the token as follows:
[expr.literal.float.type-suffix-stripped]
Any suffix is removed from the string.
[expr.literal.float.separators-stripped]
Any underscores are removed from the string.
[expr.literal.float.value]
The string is converted to the expression’s type as if by f32::from_str or f64::from_str.
Note

-1.0, for example, is an application of the negation operator to the literal expression 1.0, not a single floating-point literal expression.
Note

inf and NaN are not literal tokens. The f32::INFINITY, f64::INFINITY, f32::NAN, and f64::NAN constants can be used instead of literal expressions. In rustc, a literal large enough to be evaluated as infinite will trigger the overflowing_literals lint check.
[expr.literal.bool]
Boolean literal expressions
[expr.literal.bool.intro]
A boolean literal expression consists of one of the keywords true or false.
[expr.literal.bool.result]
The expression’s type is the primitive boolean type, and its value is:
true if the keyword is true
false if the keyword is false
[expr.path]
### Path expressions

[expr.path.syntax]
Syntax
PathExpression →
      PathInExpression
    | QualifiedPathInExpression

Show syntax diagrams

[expr.path.intro]
A path used as an expression context denotes either a local variable or an item.
[expr.path.place]
Path expressions that resolve to local or static variables are place expressions, other paths are value expressions.
[expr.path.safety]
Using a static mut variable requires an unsafe block.
local_var;
globals::STATIC_VAR;
unsafe { globals::STATIC_MUT_VAR };
let some_constructor = Some::<i32>;
let push_integer = Vec::<i32>::push;
let slice_reverse = <[i32]>::reverse;
[expr.path.const]
Evaluation of associated constants is handled the same way as const blocks.
[expr.block]
### Block expressions

[expr.block.syntax]
Syntax
BlockExpression →
    {
        InnerAttribute*
        Statements?
    }

Statements →
      Statement+
    | Statement+ ExpressionWithoutBlock
    | ExpressionWithoutBlock

Show syntax diagrams

[expr.block.intro]
A block expression, or block, is a control flow expression and anonymous namespace scope for items and variable declarations.
[expr.block.sequential-evaluation]
As a control flow expression, a block sequentially executes its component non-item declaration statements and then its final optional expression.
[expr.block.namespace]
As an anonymous namespace scope, item declarations are only in scope inside the block itself and variables declared by let statements are in scope from the next statement until the end of the block. See the scopes chapter for more details.
[expr.block.inner-attributes]
The syntax for a block is {, then any inner attributes, then any number of statements, then an optional expression, called the final operand, and finally a }.
[expr.block.statements]
Statements are usually required to be followed by a semicolon, with two exceptions:
Item declaration statements do not need to be followed by a semicolon.
Expression statements usually require a following semicolon except if its outer expression is a flow control expression.
[expr.block.null-statement]
Furthermore, extra semicolons between statements are allowed, but these semicolons do not affect semantics.
[expr.block.evaluation]
When evaluating a block expression, each statement, except for item declaration statements, is executed sequentially.
[expr.block.result]
Then the final operand is executed, if given.
[expr.block.type]
The type of a block is the type of the final operand, or () if the final operand is omitted.
let _: () = {
    fn_call();
};

let five: i32 = {
    fn_call();
    5
};

assert_eq!(5, five);
Note

As a control flow expression, if a block expression is the outer expression of an expression statement, the expected type is () unless it is followed immediately by a semicolon.
[expr.block.value]
Blocks are always value expressions and evaluate the last operand in value expression context.
Note

This can be used to force moving a value if really needed. For example, the following example fails on the call to consume_self because the struct was moved out of s in the block expression.

struct Struct;

impl Struct {
    fn consume_self(self) {}
    fn borrow_self(&self) {}
}

fn move_by_block_expression() {
    let s = Struct;

    // Move the value out of `s` in the block expression.
    (&{ s }).borrow_self();

    // Fails to execute because `s` is moved out of.
    s.consume_self();
}
[expr.block.async]
async blocks
[expr.block.async.syntax]
Syntax
AsyncBlockExpression → async move? BlockExpression

Show syntax diagrams

[expr.block.async.intro]
An async block is a variant of a block expression which evaluates to a future.
[expr.block.async.future-result]
The final expression of the block, if present, determines the result value of the future.
[expr.block.async.anonymous-type]
Executing an async block is similar to executing a closure expression: its immediate effect is to produce and return an anonymous type.
[expr.block.async.future]
Whereas closures return a type that implements one or more of the std::ops::Fn traits, however, the type returned for an async block implements the std::future::Future trait.
[expr.block.async.layout-unspecified]
The actual data format for this type is unspecified.
Note

The future type that rustc generates is roughly equivalent to an enum with one variant per await point, where each variant stores the data needed to resume from its corresponding point.
[expr.block.async.edition2018]
2018
Edition differences

Async blocks are only available beginning with Rust 2018.
[expr.block.async.capture]
Capture modes
Async blocks capture variables from their environment using the same capture modes as closures. Like closures, when written async { .. } the capture mode for each variable will be inferred from the content of the block. async move { .. } blocks however will move all referenced variables into the resulting future.
[expr.block.async.context]
Async context
Because async blocks construct a future, they define an async context which can in turn contain await expressions. Async contexts are established by async blocks as well as the bodies of async functions, whose semantics are defined in terms of async blocks.
[expr.block.async.function]
Control-flow operators
[expr.block.async.function.intro]
Async blocks act like a function boundary, much like closures.
[expr.block.async.function.return-try]
### Return expressions
[expr.block.async.function.control-flow]
Finally, the break and continue keywords cannot be used to branch out from an async block. Therefore the following is illegal:
loop {
    async move {
        break; // error[E0267]: `break` inside of an `async` block
    }
}
[expr.block.const]
const blocks
[expr.block.const.syntax]
Syntax
ConstBlockExpression → const BlockExpression

Show syntax diagrams

[expr.block.const.intro]
A const block is a variant of a block expression whose body evaluates at compile-time instead of at runtime.
[expr.block.const.context]
Const blocks allows you to define a constant value without having to define new constant items, and thus they are also sometimes referred as inline consts. It also supports type inference so there is no need to specify the type, unlike constant items.
[expr.block.const.generic-params]
Const blocks have the ability to reference generic parameters in scope, unlike free constant items. They are desugared to constant items with generic parameters in scope (similar to associated constants, but without a trait or type they are associated with). For example, this code:
fn foo<T>() -> usize {
    const { std::mem::size_of::<T>() + 1 }
}
is equivalent to:
fn foo<T>() -> usize {
    {
        struct Const<T>(T);
        impl<T> Const<T> {
            const CONST: usize = std::mem::size_of::<T>() + 1;
        }
        Const::<T>::CONST
    }
}
[expr.block.const.evaluation]
If the const block expression is executed at runtime, then the constant is guaranteed to be evaluated, even if its return value is ignored:
fn foo<T>() -> usize {
    // If this code ever gets executed, then the assertion has definitely
    // been evaluated at compile-time.
    const { assert!(std::mem::size_of::<T>() > 0); }
    // Here we can have unsafe code relying on the type being non-zero-sized.
    /* ... */
    42
}
[expr.block.const.not-executed]
If the const block expression is not executed at runtime, it may or may not be evaluated:
if false {
    // The panic may or may not occur when the program is built.
    const { panic!(); }
}
[expr.block.unsafe]
unsafe blocks
[expr.block.unsafe.syntax]
Syntax
UnsafeBlockExpression → unsafe BlockExpression

Show syntax diagrams

[expr.block.unsafe.intro]
See unsafe blocks for more information on when to use unsafe.
A block of code can be prefixed with the unsafe keyword to permit unsafe operations. Examples:
unsafe {
    let b = [13u8, 17u8];
    let a = &b[0] as *const u8;
    assert_eq!(*a, 13);
    assert_eq!(*a.offset(1), 17);
}

let a = unsafe { an_unsafe_fn() };
[expr.block.label]
Labelled block expressions
Labelled block expressions are documented in the Loops and other breakable expressions section.
[expr.block.attributes]
Attributes on block expressions
[expr.block.attributes.inner-attributes]
Inner attributes are allowed directly after the opening brace of a block expression in the following situations:
Function and method bodies.
Loop bodies (loop, while, and for).
Block expressions used as a statement.
Block expressions as elements of array expressions, tuple expressions, call expressions, and tuple-style struct expressions.
A block expression as the tail expression of another block expression.
[expr.block.attributes.valid]
The attributes that have meaning on a block expression are cfg and the lint check attributes.
For example, this function returns true on unix platforms and false on other platforms.
fn is_unix_platform() -> bool {
    #[cfg(unix)] { true }
    #[cfg(not(unix))] { false }
}
[expr.operator]
### Operator expressions

[expr.operator.syntax]
Syntax
OperatorExpression →
      BorrowExpression
    | DereferenceExpression
    | TryPropagationExpression
    | NegationExpression
    | ArithmeticOrLogicalExpression
    | ComparisonExpression
    | LazyBooleanExpression
    | TypeCastExpression
    | AssignmentExpression
    | CompoundAssignmentExpression

Show syntax diagrams

[expr.operator.intro]
Operators are defined for built in types by the Rust language.
[expr.operator.trait]
Many of the following operators can also be overloaded using traits in std::ops or std::cmp.
[expr.operator.int-overflow]
Overflow
[expr.operator.int-overflow.intro]
Integer operators will panic when they overflow when compiled in debug mode. The -C debug-assertions and -C overflow-checks compiler flags can be used to control this more directly. The following things are considered to be overflow:
[expr.operator.int-overflow.binary-arith]
When +, * or binary - create a value greater than the maximum value, or less than the minimum value that can be stored.
[expr.operator.int-overflow.unary-neg]
Applying unary - to the most negative value of any signed integer type, unless the operand is a literal expression (or a literal expression standing alone inside one or more grouped expressions).
[expr.operator.int-overflow.div]
Using / or %, where the left-hand argument is the smallest integer of a signed integer type and the right-hand argument is -1. These checks occur even when -C overflow-checks is disabled, for legacy reasons.
[expr.operator.int-overflow.shift]
Using << or >> where the right-hand argument is greater than or equal to the number of bits in the type of the left-hand argument, or is negative.
Note

The exception for literal expressions behind unary - means that forms such as -128_i8 or let j: i8 = -(128) never cause a panic and have the expected value of -128.

In these cases, the literal expression already has the most negative value for its type (for example, 128_i8 has the value -128) because integer literals are truncated to their type per the description in Integer literal expressions.

Negation of these most negative values leaves the value unchanged due to two’s complement overflow conventions.

In rustc, these most negative expressions are also ignored by the overflowing_literals lint check.
[expr.operator.borrow]
Borrow operators
[expr.operator.borrow.syntax]
Syntax
BorrowExpression →
      ( & | && ) Expression
    | ( & | && ) mut Expression
    | ( & | && ) raw const Expression
    | ( & | && ) raw mut Expression

Show syntax diagrams

[expr.operator.borrow.intro]
The & (shared borrow) and &mut (mutable borrow) operators are unary prefix operators.
[expr.operator.borrow.result]
When applied to a place expression, this expressions produces a reference (pointer) to the location that the value refers to.
[expr.operator.borrow.lifetime]
The memory location is also placed into a borrowed state for the duration of the reference. For a shared borrow (&), this implies that the place may not be mutated, but it may be read or shared again. For a mutable borrow (&mut), the place may not be accessed in any way until the borrow expires.
[expr.operator.borrow.mut]
&mut evaluates its operand in a mutable place expression context.
[expr.operator.borrow.temporary]
If the & or &mut operators are applied to a value expression, then a temporary value is created.
These operators cannot be overloaded.
{
    // a temporary with value 7 is created that lasts for this scope.
    let shared_reference = &7;
}
let mut array = [-2, 3, 9];
{
    // Mutably borrows `array` for this scope.
    // `array` may only be used through `mutable_reference`.
    let mutable_reference = &mut array;
}
[expr.borrow.and-and-syntax]
Even though && is a single token (the lazy ‘and’ operator), when used in the context of borrow expressions it works as two borrows:
// same meanings:
let a = &&  10;
let a = & & 10;

// same meanings:
let a = &&&&  mut 10;
let a = && && mut 10;
let a = & & & & mut 10;
[expr.borrow.raw]
Raw borrow operators
[expr.borrow.raw.intro]
&raw const and &raw mut are the raw borrow operators.
[expr.borrow.raw.place]
The operand expression of these operators is evaluated in place expression context.
[expr.borrow.raw.result]
&raw const expr then creates a const raw pointer of type *const T to the given place, and &raw mut expr creates a mutable raw pointer of type *mut T.
[expr.borrow.raw.invalid-ref]
The raw borrow operators must be used instead of a borrow operator whenever the place expression could evaluate to a place that is not properly aligned or does not store a valid value as determined by its type, or whenever creating a reference would introduce incorrect aliasing assumptions. In those situations, using a borrow operator would cause undefined behavior by creating an invalid reference, but a raw pointer may still be constructed.
The following is an example of creating a raw pointer to an unaligned place through a packed struct:
#[repr(packed)]
struct Packed {
    f1: u8,
    f2: u16,
}

let packed = Packed { f1: 1, f2: 2 };
// `&packed.f2` would create an unaligned reference, and thus be undefined behavior!
let raw_f2 = &raw const packed.f2;
assert_eq!(unsafe { raw_f2.read_unaligned() }, 2);
The following is an example of creating a raw pointer to a place that does not contain a valid value:
use std::mem::MaybeUninit;

struct Demo {
    field: bool,
}

let mut uninit = MaybeUninit::<Demo>::uninit();
// `&uninit.as_mut().field` would create a reference to an uninitialized `bool`,
// and thus be undefined behavior!
let f1_ptr = unsafe { &raw mut (*uninit.as_mut_ptr()).field };
unsafe { f1_ptr.write(true); }
let init = unsafe { uninit.assume_init() };
[expr.deref]
The dereference operator
[expr.deref.syntax]
Syntax
DereferenceExpression → * Expression

Show syntax diagrams

[expr.deref.intro]
The * (dereference) operator is also a unary prefix operator.
[expr.deref.result]
When applied to a pointer it denotes the pointed-to location.
[expr.deref.mut]
If the expression is of type &mut T or *mut T, and is either a local variable, a (nested) field of a local variable or is a mutable place expression, then the resulting memory location can be assigned to.
[expr.deref.safety]
Dereferencing a raw pointer requires unsafe.
[expr.deref.traits]
On non-pointer types *x is equivalent to *std::ops::Deref::deref(&x) in an immutable place expression context and *std::ops::DerefMut::deref_mut(&mut x) in a mutable place expression context.
let x = &7;
assert_eq!(*x, 7);
let y = &mut 9;
*y = 11;
assert_eq!(*y, 11);
[expr.try]
The try propagation expression
[expr.try.syntax]
Syntax
TryPropagationExpression → Expression ?

Show syntax diagrams

[expr.try.intro]
The try propagation expression uses the value of the inner expression and the Try trait to decide whether to produce a value, and if so, what value to produce, or whether to return a value to the caller, and if so, what value to return.
Example

fn try_to_parse() -> Result<i32, ParseIntError> {
    let x: i32 = "123".parse()?; // `x` is `123`.
    let y: i32 = "24a".parse()?; // Returns an `Err()` immediately.
    Ok(x + y)                    // Doesn't run.
}

let res = try_to_parse();
println!("{res:?}");
fn try_option_some() -> Option<u8> {
    let val = Some(1)?;
    Some(val)
}
assert_eq!(try_option_some(), Some(1));

fn try_option_none() -> Option<u8> {
    let val = None?;
    Some(val)
}
assert_eq!(try_option_none(), None);
use std::ops::ControlFlow;

pub struct TreeNode<T> {
    value: T,
    left: Option<Box<TreeNode<T>>>,
    right: Option<Box<TreeNode<T>>>,
}

impl<T> TreeNode<T> {
    pub fn traverse_inorder<B>(&self, f: &mut impl FnMut(&T) -> ControlFlow<B>) -> ControlFlow<B> {
        if let Some(left) = &self.left {
            left.traverse_inorder(f)?;
        }
        f(&self.value)?;
        if let Some(right) = &self.right {
            right.traverse_inorder(f)?;
        }
        ControlFlow::Continue(())
    }
}
Note

The Try trait is currently unstable, and thus cannot be implemented for user types.

The try propagation expression is currently roughly equivalent to:

match core::ops::Try::branch(expr) {
    core::ops::ControlFlow::Continue(val) => val,
    core::ops::ControlFlow::Break(residual) =>
        return core::ops::FromResidual::from_residual(residual),
}
Note

The try propagation operator is sometimes called the question mark operator, the ? operator, or the try operator.
[expr.try.restricted-types]
The try propagation operator can be applied to expressions with the type of:
Result<T, E>
Result::Ok(val) evaluates to val.
Result::Err(e) returns Result::Err(From::from(e)).
Option<T>
Option::Some(val) evaluates to val.
Option::None returns Option::None.
ControlFlow<B, C>
ControlFlow::Continue(c) evaluates to c.
ControlFlow::Break(b) returns ControlFlow::Break(b).
Poll<Result<T, E>>
Poll::Ready(Ok(val)) evaluates to Poll::Ready(val).
Poll::Ready(Err(e)) returns Poll::Ready(Err(From::from(e))).
Poll::Pending evaluates to Poll::Pending.
Poll<Option<Result<T, E>>>
Poll::Ready(Some(Ok(val))) evaluates to Poll::Ready(Some(val)).
Poll::Ready(Some(Err(e))) returns Poll::Ready(Some(Err(From::from(e)))).
Poll::Ready(None) evaluates to Poll::Ready(None).
Poll::Pending evaluates to Poll::Pending.
[expr.negate]
Negation operators
[expr.negate.syntax]
Syntax
NegationExpression →
      - Expression
    | ! Expression

Show syntax diagrams

[expr.negate.intro]
These are the last two unary operators.
[expr.negate.results]
This table summarizes the behavior of them on primitive types and which traits are used to overload these operators for other types. Remember that signed integers are always represented using two’s complement. The operands of all of these operators are evaluated in value expression context so are moved or copied.
Symbol	Integer	bool	Floating Point	Overloading Trait
-	Negation*		Negation	std::ops::Neg
!	Bitwise NOT	Logical NOT		std::ops::Not
* Only for signed integer types.
Here are some example of these operators
let x = 6;
assert_eq!(-x, -6);
assert_eq!(!x, -7);
assert_eq!(true, !false);
[expr.arith-logic]
Arithmetic and Logical Binary Operators
[expr.arith-logic.syntax]
Syntax
ArithmeticOrLogicalExpression →
      Expression + Expression
    | Expression - Expression
    | Expression * Expression
    | Expression / Expression
    | Expression % Expression
    | Expression & Expression
    | Expression | Expression
    | Expression ^ Expression
    | Expression << Expression
    | Expression >> Expression

Show syntax diagrams

[expr.arith-logic.intro]
Binary operators expressions are all written with infix notation.
[expr.arith-logic.behavior]
This table summarizes the behavior of arithmetic and logical binary operators on primitive types and which traits are used to overload these operators for other types. Remember that signed integers are always represented using two’s complement. The operands of all of these operators are evaluated in value expression context so are moved or copied.
Symbol	Integer	bool	Floating Point	Overloading Trait	Overloading Compound Assignment Trait
+	Addition		Addition	std::ops::Add	std::ops::AddAssign
-	Subtraction		Subtraction	std::ops::Sub	std::ops::SubAssign
*	Multiplication		Multiplication	std::ops::Mul	std::ops::MulAssign
/	Division*†		Division	std::ops::Div	std::ops::DivAssign
%	Remainder**†		Remainder	std::ops::Rem	std::ops::RemAssign
&	Bitwise AND	Logical AND		std::ops::BitAnd	std::ops::BitAndAssign
|	Bitwise OR	Logical OR		std::ops::BitOr	std::ops::BitOrAssign
^	Bitwise XOR	Logical XOR		std::ops::BitXor	std::ops::BitXorAssign
<<	Left Shift			std::ops::Shl	std::ops::ShlAssign
>>	Right Shift***			std::ops::Shr	std::ops::ShrAssign
* Integer division rounds towards zero.
** Rust uses a remainder defined with truncating division. Given remainder = dividend % divisor, the remainder will have the same sign as the dividend.
*** Arithmetic right shift on signed integer types, logical right shift on unsigned integer types.
† For integer types, division by zero panics.
Here are examples of these operators being used.
assert_eq!(3 + 6, 9);
assert_eq!(5.5 - 1.25, 4.25);
assert_eq!(-5 * 14, -70);
assert_eq!(14 / 3, 4);
assert_eq!(100 % 7, 2);
assert_eq!(0b1010 & 0b1100, 0b1000);
assert_eq!(0b1010 | 0b1100, 0b1110);
assert_eq!(0b1010 ^ 0b1100, 0b110);
assert_eq!(13 << 3, 104);
assert_eq!(-10 >> 2, -3);
[expr.cmp]
Comparison Operators
[expr.cmp.syntax]
Syntax
ComparisonExpression →
      Expression == Expression
    | Expression != Expression
    | Expression > Expression
    | Expression < Expression
    | Expression >= Expression
    | Expression <= Expression

Show syntax diagrams

[expr.cmp.intro]
Comparison operators are also defined both for primitive types and many types in the standard library.
[expr.cmp.paren-chaining]
Parentheses are required when chaining comparison operators. For example, the expression a == b == c is invalid and may be written as (a == b) == c.
[expr.cmp.trait]
Unlike arithmetic and logical operators, the traits for overloading these operators are used more generally to show how a type may be compared and will likely be assumed to define actual comparisons by functions that use these traits as bounds. Many functions and macros in the standard library can then use that assumption (although not to ensure safety).
[expr.cmp.place]
Unlike the arithmetic and logical operators above, these operators implicitly take shared borrows of their operands, evaluating them in place expression context:
a == b;
// is equivalent to
::std::cmp::PartialEq::eq(&a, &b);
This means that the operands don’t have to be moved out of.
[expr.cmp.behavior]
Symbol	Meaning	Overloading method
==	Equal	std::cmp::PartialEq::eq
!=	Not equal	std::cmp::PartialEq::ne
>	Greater than	std::cmp::PartialOrd::gt
<	Less than	std::cmp::PartialOrd::lt
>=	Greater than or equal to	std::cmp::PartialOrd::ge
<=	Less than or equal to	std::cmp::PartialOrd::le
Here are examples of the comparison operators being used.
assert!(123 == 123);
assert!(23 != -12);
assert!(12.5 > 12.2);
assert!([1, 2, 3] < [1, 3, 4]);
assert!('A' <= 'B');
assert!("World" >= "Hello");
[expr.bool-logic]
Lazy boolean operators
[expr.bool-logic.syntax]
Syntax
LazyBooleanExpression →
      Expression || Expression
    | Expression && Expression

Show syntax diagrams

[expr.bool-logic.intro]
The operators || and && may be applied to operands of boolean type. The || operator denotes logical ‘or’, and the && operator denotes logical ‘and’.
[expr.bool-logic.conditional-evaluation]
They differ from | and & in that the right-hand operand is only evaluated when the left-hand operand does not already determine the result of the expression. That is, || only evaluates its right-hand operand when the left-hand operand evaluates to false, and && only when it evaluates to true.
let x = false || true; // true
let y = false && panic!(); // false, doesn't evaluate `panic!()`
[expr.as]
Type cast expressions
[expr.as.syntax]
Syntax
TypeCastExpression → Expression as TypeNoBounds

Show syntax diagrams

[expr.as.intro]
A type cast expression is denoted with the binary operator as.
[expr.as.result]
Executing an as expression casts the value on the left-hand side to the type on the right-hand side.
An example of an as expression:
fn average(values: &[f64]) -> f64 {
    let sum: f64 = sum(values);
    let size: f64 = len(values) as f64;
    sum / size
}
[expr.as.coercions]
as can be used to explicitly perform coercions, as well as the following additional casts. Any cast that does not fit either a coercion rule or an entry in the table is a compiler error. Here *T means either *const T or *mut T. m stands for optional mut in reference types and mut or const in pointer types.
Type of e	U	Cast performed by e as U
Integer or Float type	Integer or Float type	Numeric cast
Enumeration	Integer type	Enum cast
bool or char	Integer type	Primitive to integer cast
u8	char	u8 to char cast
*T	*V 1	Pointer to pointer cast
*T where T: Sized	Integer type	Pointer to address cast
Integer type	*V where V: Sized	Address to pointer cast
&m₁ [T; n]	*m₂ T 2	Array to pointer cast
*m₁ [T; n]	*m₂ T 2	Array to pointer cast
Function item	Function pointer	Function item to function pointer cast
Function item	*V where V: Sized	Function item to pointer cast
Function item	Integer	Function item to address cast
Function pointer	*V where V: Sized	Function pointer to pointer cast
Function pointer	Integer	Function pointer to address cast
Closure 3	Function pointer	Closure to function pointer cast
Semantics
[expr.as.numeric]
Numeric cast
[expr.as.numeric.int-same-size]
Casting between two integers of the same size (e.g. i32 -> u32) is a no-op (Rust uses 2’s complement for negative values of fixed integers)

assert_eq!(42i8 as u8, 42u8);
assert_eq!(-1i8 as u8, 255u8);
assert_eq!(255u8 as i8, -1i8);
assert_eq!(-1i16 as u16, 65535u16);
[expr.as.numeric.int-truncation]
Casting from a larger integer to a smaller integer (e.g. u32 -> u8) will truncate

assert_eq!(42u16 as u8, 42u8);
assert_eq!(1234u16 as u8, 210u8);
assert_eq!(0xabcdu16 as u8, 0xcdu8);

assert_eq!(-42i16 as i8, -42i8);
assert_eq!(1234u16 as i8, -46i8);
assert_eq!(0xabcdi32 as i8, -51i8);
[expr.as.numeric.int-extension]
Casting from a smaller integer to a larger integer (e.g. u8 -> u32) will

zero-extend if the source is unsigned
sign-extend if the source is signed
assert_eq!(42i8 as i16, 42i16);
assert_eq!(-17i8 as i16, -17i16);
assert_eq!(0b1000_1010u8 as u16, 0b0000_0000_1000_1010u16, "Zero-extend");
assert_eq!(0b0000_1010i8 as i16, 0b0000_0000_0000_1010i16, "Sign-extend 0");
assert_eq!(0b1000_1010u8 as i8 as i16, 0b1111_1111_1000_1010u16 as i16, "Sign-extend 1");
[expr.as.numeric.float-as-int]
Casting from a float to an integer will round the float towards zero

NaN will return 0
Values larger than the maximum integer value, including INFINITY, will saturate to the maximum value of the integer type.
Values smaller than the minimum integer value, including NEG_INFINITY, will saturate to the minimum value of the integer type.
assert_eq!(42.9f32 as i32, 42);
assert_eq!(-42.9f32 as i32, -42);
assert_eq!(42_000_000f32 as i32, 42_000_000);
assert_eq!(std::f32::NAN as i32, 0);
assert_eq!(1_000_000_000_000_000f32 as i32, 0x7fffffffi32);
assert_eq!(std::f32::NEG_INFINITY as i32, -0x80000000i32);
[expr.as.numeric.int-as-float]
Casting from an integer to float will produce the closest possible float *

if necessary, rounding is according to roundTiesToEven mode ***
on overflow, infinity (of the same sign as the input) is produced
note: with the current set of numeric types, overflow can only happen on u128 as f32 for values greater or equal to f32::MAX + (0.5 ULP)
assert_eq!(1337i32 as f32, 1337f32);
assert_eq!(123_456_789i32 as f32, 123_456_790f32, "Rounded");
assert_eq!(0xffffffff_ffffffff_ffffffff_ffffffff_u128 as f32, std::f32::INFINITY);
[expr.as.numeric.float-widening]
Casting from an f32 to an f64 is perfect and lossless

assert_eq!(1_234.5f32 as f64, 1_234.5f64);
assert_eq!(std::f32::INFINITY as f64, std::f64::INFINITY);
assert!((std::f32::NAN as f64).is_nan());
[expr.as.numeric.float-narrowing]
Casting from an f64 to an f32 will produce the closest possible f32 **

if necessary, rounding is according to roundTiesToEven mode ***
on overflow, infinity (of the same sign as the input) is produced
assert_eq!(1_234.5f64 as f32, 1_234.5f32);
assert_eq!(1_234_567_891.123f64 as f32, 1_234_567_890f32, "Rounded");
assert_eq!(std::f64::INFINITY as f32, std::f32::INFINITY);
assert!((std::f64::NAN as f32).is_nan());
* if integer-to-float casts with this rounding mode and overflow behavior are not supported natively by the hardware, these casts will likely be slower than expected.
** if f64-to-f32 casts with this rounding mode and overflow behavior are not supported natively by the hardware, these casts will likely be slower than expected.
*** as defined in IEEE 754-2008 §4.3.1: pick the nearest floating point number, preferring the one with an even least significant digit if exactly halfway between two floating point numbers.
[expr.as.enum]
Enum cast
[expr.as.enum.discriminant]
Casts an enum to its discriminant, then uses a numeric cast if needed. Casting is limited to the following kinds of enumerations:
Unit-only enums
Field-less enums without explicit discriminants, or where only unit-variants have explicit discriminants
enum Enum { A, B, C }
assert_eq!(Enum::A as i32, 0);
assert_eq!(Enum::B as i32, 1);
assert_eq!(Enum::C as i32, 2);
[expr.as.enum.no-drop]
Casting is not allowed if the enum implements Drop.
[expr.as.bool-char-as-int]
Primitive to integer cast
false casts to 0, true casts to 1
char casts to the value of the code point, then uses a numeric cast if needed.
assert_eq!(false as i32, 0);
assert_eq!(true as i32, 1);
assert_eq!('A' as i32, 65);
assert_eq!('Ö' as i32, 214);
[expr.as.u8-as-char]
u8 to char cast
Casts to the char with the corresponding code point.
assert_eq!(65u8 as char, 'A');
assert_eq!(214u8 as char, 'Ö');
[expr.as.pointer-as-int]
Pointer to address cast
Casting from a raw pointer to an integer produces the machine address of the referenced memory. If the integer type is smaller than the pointer type, the address may be truncated; using usize avoids this.
[expr.as.int-as-pointer]
Address to pointer cast
Casting from an integer to a raw pointer interprets the integer as a memory address and produces a pointer referencing that memory.
Warning

This interacts with the Rust memory model, which is still under development. A pointer obtained from this cast may suffer additional restrictions even if it is bitwise equal to a valid pointer. Dereferencing such a pointer may be undefined behavior if aliasing rules are not followed.
A trivial example of sound address arithmetic:
let mut values: [i32; 2] = [1, 2];
let p1: *mut i32 = values.as_mut_ptr();
let first_address = p1 as usize;
let second_address = first_address + 4; // 4 == size_of::<i32>()
let p2 = second_address as *mut i32;
unsafe {
    *p2 += 1;
}
assert_eq!(values[1], 3);
[expr.as.pointer]
Pointer-to-pointer cast
[expr.as.pointer.behavior]
*const T / *mut T can be cast to *const U / *mut U with the following behavior:
[expr.as.pointer.sized]
If T and U are both sized, the pointer is returned unchanged.
[expr.as.pointer.unsized]
If T and U are both unsized, the pointer is also returned unchanged. In particular, the metadata is preserved exactly.

For instance, a cast from *const [T] to *const [U] preserves the number of elements. Note that, as a consequence, such casts do not necessarily preserve the size of the pointer’s referent (e.g., casting *const [u16] to *const [u8] will result in a raw pointer which refers to an object of half the size of the original). The same holds for str and any compound type whose unsized tail is a slice type, such as struct Foo(i32, [u8]) or (u64, Foo).
[expr.as.pointer.discard-metadata]
If T is unsized and U is sized, the cast discards all metadata that completes the wide pointer T and produces a thin pointer U consisting of the data part of the unsized pointer.
[expr.assign]
Assignment expressions
[expr.assign.syntax]
Syntax
AssignmentExpression → Expression = Expression

Show syntax diagrams

[expr.assign.intro]
An assignment expression moves a value into a specified place.
[expr.assign.assignee]
An assignment expression consists of a mutable assignee expression, the assignee operand, followed by an equals sign (=) and a value expression, the assigned value operand.
[expr.assign.behavior-basic]
In its most basic form, an assignee expression is a place expression, and we discuss this case first.
[expr.assign.behavior-destructuring]
The more general case of destructuring assignment is discussed below, but this case always decomposes into sequential assignments to place expressions, which may be considered the more fundamental case.
[expr.assign.basic]
Basic assignments
[expr.assign.evaluation-order]
Evaluating assignment expressions begins by evaluating its operands. The assigned value operand is evaluated first, followed by the assignee expression.
[expr.assign.destructuring-order]
For destructuring assignment, subexpressions of the assignee expression are evaluated left-to-right.
Note

This is different than other expressions in that the right operand is evaluated before the left one.
[expr.assign.drop-target]
It then has the effect of first dropping the value at the assigned place, unless the place is an uninitialized local variable or an uninitialized field of a local variable.
[expr.assign.behavior]
Next it either copies or moves the assigned value to the assigned place.
[expr.assign.result]
An assignment expression always produces the unit value.
Example:
let mut x = 0;
let y = 0;
x = y;
[expr.assign.destructure]
Destructuring assignments
[expr.assign.destructure.intro]
Destructuring assignment is a counterpart to destructuring pattern matches for variable declaration, permitting assignment to complex values, such as tuples or structs. For instance, we may swap two mutable variables:
let (mut a, mut b) = (0, 1);
// Swap `a` and `b` using destructuring assignment.
(b, a) = (a, b);
[expr.assign.destructure.assignee]
In contrast to destructuring declarations using let, patterns may not appear on the left-hand side of an assignment due to syntactic ambiguities. Instead, a group of expressions that correspond to patterns are designated to be assignee expressions, and permitted on the left-hand side of an assignment. Assignee expressions are then desugared to pattern matches followed by sequential assignment.
[expr.assign.destructure.irrefutable]
The desugared patterns must be irrefutable: in particular, this means that only slice patterns whose length is known at compile-time, and the trivial slice [..], are permitted for destructuring assignment.
The desugaring method is straightforward, and is illustrated best by example.
(a, b) = (3, 4);

[a, b] = [3, 4];

Struct { x: a, y: b } = Struct { x: 3, y: 4};

// desugars to:

{
    let (_a, _b) = (3, 4);
    a = _a;
    b = _b;
}

{
    let [_a, _b] = [3, 4];
    a = _a;
    b = _b;
}

{
    let Struct { x: _a, y: _b } = Struct { x: 3, y: 4};
    a = _a;
    b = _b;
}
[expr.assign.destructure.repeat-ident]
Identifiers are not forbidden from being used multiple times in a single assignee expression.
[expr.assign.destructure.discard-value]
### Underscore expressions
[expr.assign.destructure.default-binding]
Note that default binding modes do not apply for the desugared expression.
[expr.compound-assign]
Compound assignment expressions
[expr.compound-assign.syntax]
Syntax
CompoundAssignmentExpression →
      Expression += Expression
    | Expression -= Expression
    | Expression *= Expression
    | Expression /= Expression
    | Expression %= Expression
    | Expression &= Expression
    | Expression |= Expression
    | Expression ^= Expression
    | Expression <<= Expression
    | Expression >>= Expression

Show syntax diagrams

[expr.compound-assign.intro]
Compound assignment expressions combine arithmetic and logical binary operators with assignment expressions.
For example:
let mut x = 5;
x += 1;
assert!(x == 6);
The syntax of compound assignment is a mutable place expression, the assigned operand, then one of the operators followed by an = as a single token (no whitespace), and then a value expression, the modifying operand.
[expr.compound-assign.place]
Unlike other place operands, the assigned place operand must be a place expression.
[expr.compound-assign.no-value]
Attempting to use a value expression is a compiler error rather than promoting it to a temporary.
[expr.compound-assign.operand-order]
Evaluation of compound assignment expressions depends on the types of the operands.
[expr.compound-assign.primitives]
If the types of both operands are known, prior to monomorphization, to be primitive, the right hand side is evaluated first, the left hand side is evaluated next, and the place given by the evaluation of the left hand side is mutated by applying the operator to the values of both sides.
trait Equate {}
impl<T> Equate for (T, T) {}

fn f1(x: (u8,)) {
    let mut order = vec![];
    // The RHS is evaluated first as both operands are of primitive
    // type.
    { order.push(2); x }.0 += { order.push(1); x }.0;
    assert!(order.is_sorted());
}

fn f2(x: (Wrapping<u8>,)) {
    let mut order = vec![];
    // The LHS is evaluated first as `Wrapping<_>` is not a primitive
    // type.
    { order.push(1); x }.0 += { order.push(2); (0u8,) }.0;
    assert!(order.is_sorted());
}

fn f3<T: AddAssign<u8> + Copy>(x: (T,)) where (T, u8): Equate {
    let mut order = vec![];
    // The LHS is evaluated first as one of the operands is a generic
    // parameter, even though that generic parameter can be unified
    // with a primitive type due to the where clause bound.
    { order.push(1); x }.0 += { order.push(2); (0u8,) }.0;
    assert!(order.is_sorted());
}

fn main() {
    f1((0u8,));
    f2((Wrapping(0u8),));
    // We supply a primitive type as the generic argument, but this
    // does not affect the evaluation order in `f3` when
    // monomorphized.
    f3::<u8>((0u8,));
}
Note

This is unusual. Elsewhere left to right evaluation is the norm.

See the eval order test for more examples.
[expr.compound-assign.trait]
Otherwise, this expression is syntactic sugar for using the corresponding trait for the operator (see expr.arith-logic.behavior) and calling its method with the left hand side as the receiver and the right hand side as the next argument.
For example, the following two statements are equivalent:
fn f<T: AddAssign + Copy>(mut x: T, y: T) {
    x += y; // Statement 1.
    x.add_assign(y); // Statement 2.
}
Note

Surprisingly, desugaring this further to a fully qualified method call is not equivalent, as there is special borrow checker behavior when the mutable reference to the first operand is taken via autoref.

fn f<T: AddAssign + Copy>(mut x: T) {
    // Here we used `x` as both the LHS and the RHS. Because the
    // mutable borrow of the LHS needed to call the trait method
    // is taken implicitly by autoref, this is OK.
    x += x; //~ OK
    x.add_assign(x); //~ OK
}
fn f<T: AddAssign + Copy>(mut x: T) {
    // We can't desugar the above to the below, as once we take the
    // mutable borrow of `x` to pass the first argument, we can't
    // pass `x` by value in the second argument because the mutable
    // reference is still live.
    <T as AddAssign>::add_assign(&mut x, x);
    //~^ ERROR cannot use `x` because it was mutably borrowed
}
fn f<T: AddAssign + Copy>(mut x: T) {
    // As above.
    (&mut x).add_assign(x);
    //~^ ERROR cannot use `x` because it was mutably borrowed
}
[expr.compound-assign.result]
As with normal assignment expressions, compound assignment expressions always produce the unit value.
Warning

Avoid writing code that depends on the evaluation order of operands in compound assignments as it can be unusual and surprising.
where T and V have compatible metadata:

V: Sized, or
Both slice metadata (*[u16] -> *[u8], *str -> *(u8, [u32])), or
Both the same trait object metadata, modulo dropping auto traits (*dyn Debug -> *(u16, dyn Debug), *dyn Debug + Send -> *dyn Debug)
Note: adding auto traits is only allowed if the principal trait has the auto trait as a super trait (given trait T: Send {}, *dyn T -> *dyn T + Send is valid, but *dyn Debug -> *dyn Debug + Send is not)
Note: Generics (including lifetimes) must match (*dyn T<'a, A> -> *dyn T<'b, B> requires 'a = 'b and A = B)
↩
only when m₁ is mut or m₂ is const. Casting mut reference/pointer to const pointer is allowed. ↩ ↩2

only for closures that do not capture (close over) any local variables can be casted to function pointers. ↩

[expr.paren]
### Grouped expressions

[expr.paren.syntax]
Syntax
GroupedExpression → ( Expression )

Show syntax diagrams

[expr.paren.intro]
A parenthesized expression wraps a single expression, evaluating to that expression. The syntax for a parenthesized expression is a (, then an expression, called the enclosed operand, and then a ).
[expr.paren.evaluation]
Parenthesized expressions evaluate to the value of the enclosed operand.
[expr.paren.place-or-value]
Unlike other expressions, parenthesized expressions are both place expressions and value expressions. When the enclosed operand is a place expression, it is a place expression and when the enclosed operand is a value expression, it is a value expression.
[expr.paren.override-precedence]
Parentheses can be used to explicitly modify the precedence order of subexpressions within an expression.
An example of a parenthesized expression:
let x: i32 = 2 + 3 * 4; // not parenthesized
let y: i32 = (2 + 3) * 4; // parenthesized
assert_eq!(x, 14);
assert_eq!(y, 20);
An example of a necessary use of parentheses is when calling a function pointer that is a member of a struct:
assert_eq!( a.f (), "The method f");
assert_eq!((a.f)(), "The field f");
[expr.array]
Array and array index expressions

Array expressions
[expr.array.syntax]
Syntax
ArrayExpression → [ ArrayElements? ]

ArrayElements →
      Expression ( , Expression )* ,?
    | Expression ; Expression

Show syntax diagrams

[expr.array.constructor]
Array expressions construct arrays. Array expressions come in two forms.
[expr.array.array]
The first form lists out every value in the array.
[expr.array.array-syntax]
The syntax for this form is a comma-separated list of expressions of uniform type enclosed in square brackets.
[expr.array.array-behavior]
This produces an array containing each of these values in the order they are written.
[expr.array.repeat]
The syntax for the second form is two expressions separated by a semicolon (;) enclosed in square brackets.
[expr.array.repeat-operand]
The expression before the ; is called the repeat operand.
[expr.array.length-operand]
The expression after the ; is called the length operand.
[expr.array.length-restriction]
The length operand must either be an inferred const or be a constant expression of type usize (e.g. a literal or a constant item).
const C: usize = 1;
let _: [u8; C] = [0; 1]; // Literal.
let _: [u8; C] = [0; C]; // Constant item.
let _: [u8; C] = [0; _]; // Inferred const.
let _: [u8; C] = [0; (((_)))]; // Inferred const.
Note

In an array expression, an inferred const is parsed as an expression but then semantically treated as a separate kind of const generic argument.
[expr.array.repeat-behavior]
An array expression of this form creates an array with the length of the value of the length operand with each element being a copy of the repeat operand. That is, [a; b] creates an array containing b copies of the value of a.
[expr.array.repeat-copy]
If the length operand has a value greater than 1 then this requires the repeat operand to have a type that implements Copy, to be a const block expression, or to be a path to a constant item.
[expr.array.repeat-const-item]
When the repeat operand is a const block or a path to a constant item, it is evaluated the number of times specified in the length operand.
[expr.array.repeat-evaluation-zero]
If that value is 0, then the const block or constant item is not evaluated at all.
[expr.array.repeat-non-const]
For expressions that are neither a const block nor a path to a constant item, it is evaluated exactly once, and then the result is copied the length operand’s value times.
[1, 2, 3, 4];
["a", "b", "c", "d"];
[0; 128];              // array with 128 zeros
[0u8, 0u8, 0u8, 0u8,];
[[1, 0, 0], [0, 1, 0], [0, 0, 1]]; // 2D array
const EMPTY: Vec<i32> = Vec::new();
[EMPTY; 2];
[expr.array.index]
Array and slice indexing expressions
[expr.array.index.syntax]
Syntax
IndexExpression → Expression [ Expression ]

Show syntax diagrams

[expr.array.index.array]
Array and slice-typed values can be indexed by writing a square-bracket-enclosed expression of type usize (the index) after them. When the array is mutable, the resulting memory location can be assigned to.
[expr.array.index.trait]
For other types an index expression a[b] is equivalent to *std::ops::Index::index(&a, b), or *std::ops::IndexMut::index_mut(&mut a, b) in a mutable place expression context. Just as with methods, Rust will also insert dereference operations on a repeatedly to find an implementation.
[expr.array.index.zero-index]
Indices are zero-based for arrays and slices.
[expr.array.index.const]
Array access is a constant expression, so bounds can be checked at compile-time with a constant index value. Otherwise a check will be performed at run-time that will put the thread in a panicked state if it fails.
// lint is deny by default.
#![warn(unconditional_panic)]

([1, 2, 3, 4])[2];        // Evaluates to 3

let b = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
b[1][2];                  // multidimensional array indexing

let x = (["a", "b"])[10]; // warning: index out of bounds

let n = 10;
let y = (["a", "b"])[n];  // panics

let arr = ["a", "b"];
arr[10];                  // warning: index out of bounds
[expr.array.index.trait-impl]
The array index expression can be implemented for types other than arrays and slices by implementing the Index and IndexMut traits.
[expr.tuple]
### Tuple and index expressions

Tuple expressions
[expr.tuple.syntax]
Syntax
TupleExpression → ( TupleElements? )

TupleElements → ( Expression , )+ Expression?

Show syntax diagrams

[expr.tuple.result]
A tuple expression constructs tuple values.
[expr.tuple.intro]
The syntax for tuple expressions is a parenthesized, comma separated list of expressions, called the tuple initializer operands.
[expr.tuple.unary-tuple-restriction]
1-ary tuple expressions require a comma after their tuple initializer operand to be disambiguated with a parenthetical expression.
[expr.tuple.value]
Tuple expressions are a value expression that evaluate into a newly constructed value of a tuple type.
[expr.tuple.type]
The number of tuple initializer operands is the arity of the constructed tuple.
[expr.tuple.unit]
Tuple expressions without any tuple initializer operands produce the unit tuple.
[expr.tuple.fields]
For other tuple expressions, the first written tuple initializer operand initializes the field 0 and subsequent operands initializes the next highest field. For example, in the tuple expression ('a', 'b', 'c'), 'a' initializes the value of the field 0, 'b' field 1, and 'c' field 2.
Examples of tuple expressions and their types:
Expression	Type
()	() (unit)
(0.0, 4.5)	(f64, f64)
("x".to_string(), )	(String, )
("a", 4usize, true)	(&'static str, usize, bool)
[expr.tuple-index]
Tuple indexing expressions
[expr.tuple-index.syntax]
Syntax
TupleIndexingExpression → Expression . TUPLE_INDEX

Show syntax diagrams

[expr.tuple-index.intro]
A tuple indexing expression accesses fields of tuples and tuple structs.
The syntax for a tuple index expression is an expression, called the tuple operand, then a ., then finally a tuple index.
[expr.tuple-index.index-syntax]
The syntax for the tuple index is a decimal literal with no leading zeros, underscores, or suffix. For example 0 and 2 are valid tuple indices but not 01, 0_, nor 0i32.
[expr.tuple-index.required-type]
The type of the tuple operand must be a tuple type or a tuple struct.
[expr.tuple-index.index-name-operand]
The tuple index must be a name of a field of the type of the tuple operand.
[expr.tuple-index.result]
Evaluation of tuple index expressions has no side effects beyond evaluation of its tuple operand. As a place expression, it evaluates to the location of the field of the tuple operand with the same name as the tuple index.
Examples of tuple indexing expressions:
// Indexing a tuple
let pair = ("a string", 2);
assert_eq!(pair.1, 2);

// Indexing a tuple struct
let point = Point(1.0, 0.0);
assert_eq!(point.0, 1.0);
assert_eq!(point.1, 0.0);
Note

Unlike field access expressions, tuple index expressions can be the function operand of a call expression as it cannot be confused with a method call since method names cannot be numbers.
Note

Although arrays and slices also have elements, you must use an array or slice indexing expression or a slice pattern to access their elements.
[expr.struct]
### Struct expressions

[expr.struct.syntax]
Syntax
StructExpression →
    PathInExpression { ( StructExprFields | StructBase )? }

StructExprFields →
    StructExprField ( , StructExprField )* ( , StructBase | ,? )

StructExprField →
    OuterAttribute*
    (
        IDENTIFIER
      | ( IDENTIFIER | TUPLE_INDEX ) : Expression
    )

StructBase → .. Expression

Show syntax diagrams

[expr.struct.intro]
A struct expression creates a struct, enum, or union value. It consists of a path to a struct, enum variant, or union item followed by the values for the fields of the item.
The following are examples of struct expressions:
Point {x: 10.0, y: 20.0};
NothingInMe {};
let u = game::User {name: "Joe", age: 35, score: 100_000};
Enum::Variant {};
Note

Tuple structs and tuple enum variants are typically instantiated using a call expression referring to the constructor in the value namespace. These are distinct from a struct expression using curly braces referring to the constructor in the type namespace.

struct Position(i32, i32, i32);
Position(0, 0, 0);  // Typical way of creating a tuple struct.
let c = Position;  // `c` is a function that takes 3 arguments.
let pos = c(8, 6, 7);  // Creates a `Position` value.

enum Version { Triple(i32, i32, i32) };
Version::Triple(0, 0, 0);
let f = Version::Triple;
let ver = f(8, 6, 7);
The last segment of the call path cannot refer to a type alias:

trait Tr { type T; }
impl<T> Tr for T { type T = T; }

struct Tuple();
enum Enum { Tuple() }

// <Unit as Tr>::T(); // causes an error -- `::T` is a type, not a value
<Enum as Tr>::T::Tuple(); // OK
Unit structs and unit enum variants are typically instantiated using a path expression referring to the constant in the value namespace.

struct Gamma;
// Gamma unit value, referring to the const in the value namespace.
let a = Gamma;
// Exact same value as `a`, but constructed using a struct expression
// referring to the type namespace.
let b = Gamma {};

enum ColorSpace { Oklch }
let c = ColorSpace::Oklch;
let d = ColorSpace::Oklch {};
[expr.struct.field]
Field struct expression
[expr.struct.field.intro]
A struct expression with fields enclosed in curly braces allows you to specify the value for each individual field in any order. The field name is separated from its value with a colon.
[expr.struct.field.union-constraint]
A value of a union type can only be created using this syntax, and it must specify exactly one field.
[expr.struct.update]
Functional update syntax
[expr.struct.update.intro]
A struct expression that constructs a value of a struct type can terminate with the syntax .. followed by an expression to denote a functional update.
[expr.struct.update.base-same-type]
The expression following .. (the base) must have the same struct type as the new struct type being formed.
[expr.struct.update.fields]
The entire expression uses the given values for the fields that were specified and moves or copies the remaining fields from the base expression.
[expr.struct.update.visibility-constraint]
As with all struct expressions, all of the fields of the struct must be visible, even those not explicitly named.
let mut base = Point3d {x: 1, y: 2, z: 3};
let y_ref = &mut base.y;
Point3d {y: 0, z: 10, .. base}; // OK, only base.x is accessed
drop(y_ref);
[expr.struct.brace-restricted-positions]
Struct expressions can’t be used directly in a loop or if expression’s head, or in the scrutinee of an if let or match expression. However, struct expressions can be used in these situations if they are within another expression, for example inside parentheses.
[expr.struct.tuple-field]
The field names can be decimal integer values to specify indices for constructing tuple structs. This can be used with base structs to fill out the remaining indices not specified:
struct Color(u8, u8, u8);
let c1 = Color(0, 0, 0);  // Typical way of creating a tuple struct.
let c2 = Color{0: 255, 1: 127, 2: 0};  // Specifying fields by index.
let c3 = Color{1: 0, ..c2};  // Fill out all other fields using a base struct.
[expr.struct.field.named]
Struct field init shorthand
When initializing a data structure (struct, enum, union) with named (but not numbered) fields, it is allowed to write fieldname as a shorthand for fieldname: fieldname. This allows a compact syntax with less duplication. For example:
Point3d { x: x, y: y_value, z: z };
Point3d { x, y: y_value, z };
[expr.call]
### Call expressions

[expr.call.syntax]
Syntax
CallExpression → Expression ( CallParams? )

CallParams → Expression ( , Expression )* ,?

Show syntax diagrams

[expr.call.intro]
A call expression calls a function. The syntax of a call expression is an expression, called the function operand, followed by a parenthesized comma-separated list of expression, called the argument operands.
[expr.call.convergence]
If the function eventually returns, then the expression completes.
[expr.call.trait]
For non-function types, the expression f(...) uses the method on one of the following traits based on the function operand:
Fn or AsyncFn — shared reference.
FnMut or AsyncFnMut — mutable reference.
FnOnce or AsyncFnOnce — value.
[expr.call.autoref-deref]
An automatic borrow will be taken if needed. The function operand will also be automatically dereferenced as required.
Some examples of call expressions:
let three: i32 = add(1i32, 2i32);
let name: &'static str = (|| "Rust")();
[expr.call.desugar]
Disambiguating Function Calls
[expr.call.desugar.fully-qualified]
All function calls are sugar for a more explicit fully-qualified syntax.
[expr.call.desugar.ambiguity]
Function calls may need to be fully qualified, depending on the ambiguity of a call in light of in-scope items.
Note

In the past, the terms “Unambiguous Function Call Syntax”, “Universal Function Call Syntax”, or “UFCS”, have been used in documentation, issues, RFCs, and other community writings. However, these terms lack descriptive power and potentially confuse the issue at hand. We mention them here for searchability’s sake.
[expr.call.desugar.limits]
Several situations often occur which result in ambiguities about the receiver or referent of method or associated function calls. These situations may include:
Multiple in-scope traits define methods with the same name for the same types
Auto-deref is undesirable; for example, distinguishing between methods on a smart pointer itself and the pointer’s referent
Methods which take no arguments, like default(), and return properties of a type, like size_of()
[expr.call.desugar.explicit-path]
To resolve the ambiguity, the programmer may refer to their desired method or function using more specific paths, types, or traits.
For example,
trait Pretty {
    fn print(&self);
}

trait Ugly {
    fn print(&self);
}

struct Foo;
impl Pretty for Foo {
    fn print(&self) {}
}

struct Bar;
impl Pretty for Bar {
    fn print(&self) {}
}
impl Ugly for Bar {
    fn print(&self) {}
}

fn main() {
    let f = Foo;
    let b = Bar;

    // we can do this because we only have one item called `print` for `Foo`s
    f.print();
    // more explicit, and, in the case of `Foo`, not necessary
    Foo::print(&f);
    // if you're not into the whole brevity thing
    <Foo as Pretty>::print(&f);

    // b.print(); // Error: multiple 'print' found
    // Bar::print(&b); // Still an error: multiple `print` found

    // necessary because of in-scope items defining `print`
    <Bar as Pretty>::print(&b);
}
Refer to RFC 132 for further details and motivations.
[expr.method]
Method-call expressions

[expr.method.syntax]
Syntax
MethodCallExpression → Expression . PathExprSegment ( CallParams? )

Show syntax diagrams

[expr.method.intro]
A method call consists of an expression (the receiver) followed by a single dot, an expression path segment, and a parenthesized expression-list.
[expr.method.target]
Method calls are resolved to associated methods on specific traits, either statically dispatching to a method if the exact self-type of the left-hand-side is known, or dynamically dispatching if the left-hand-side expression is an indirect trait object.
let pi: Result<f32, _> = "3.14".parse();
let log_pi = pi.unwrap_or(1.0).log(2.72);
[expr.method.autoref-deref]
When looking up a method call, the receiver may be automatically dereferenced or borrowed in order to call a method. This requires a more complex lookup process than for other functions, since there may be a number of possible methods to call. The following procedure is used:
[expr.method.candidate-receivers]
The first step is to build a list of candidate receiver types. Obtain these by repeatedly dereferencing the receiver expression’s type, adding each type encountered to the list, then finally attempting an unsized coercion at the end, and adding the result type if that is successful.
[expr.method.candidate-receivers-refs]
Then, for each candidate T, add &T and &mut T to the list immediately after T.
For instance, if the receiver has type Box<[i32;2]>, then the candidate types will be Box<[i32;2]>, &Box<[i32;2]>, &mut Box<[i32;2]>, [i32; 2] (by dereferencing), &[i32; 2], &mut [i32; 2], [i32] (by unsized coercion), &[i32], and finally &mut [i32].
[expr.method.candidate-search]
Then, for each candidate type T, search for a visible method with a receiver of that type in the following places:
T’s inherent methods (methods implemented directly on T).
Any of the methods provided by a visible trait implemented by T. If T is a type parameter, methods provided by trait bounds on T are looked up first. Then all remaining methods in scope are looked up.
Note

The lookup is done for each type in order, which can occasionally lead to surprising results. The below code will print “In trait impl!”, because &self methods are looked up first, the trait method is found before the struct’s &mut self method is found.

struct Foo {}

trait Bar {
  fn bar(&self);
}

impl Foo {
  fn bar(&mut self) {
    println!("In struct impl!")
  }
}

impl Bar for Foo {
  fn bar(&self) {
    println!("In trait impl!")
  }
}

fn main() {
  let mut f = Foo{};
  f.bar();
}
[expr.method.ambiguous-target]
If this results in multiple possible candidates, then it is an error, and the receiver must be converted to an appropriate receiver type to make the method call.
[expr.method.receiver-constraints]
This process does not take into account the mutability or lifetime of the receiver, or whether a method is unsafe. Once a method is looked up, if it can’t be called for one (or more) of those reasons, the result is a compiler error.
[expr.method.ambiguous-search]
If a step is reached where there is more than one possible method, such as where generic methods or traits are considered the same, then it is a compiler error. These cases require a disambiguating function call syntax for method and function invocation.
[expr.method.edition2021]
2021
Edition differences

Before the 2021 edition, during the search for visible methods, if the candidate receiver type is an array type, methods provided by the standard library IntoIterator trait are ignored.

The edition used for this purpose is determined by the token representing the method name.

This special case may be removed in the future.
Warning

For trait objects, if there is an inherent method of the same name as a trait method, it will give a compiler error when trying to call the method in a method call expression. Instead, you can call the method using disambiguating function call syntax, in which case it calls the trait method, not the inherent method. There is no way to call the inherent method. Just don’t define inherent methods on trait objects with the same name as a trait method and you’ll be fine.
[expr.field]
### Field access expressions

[expr.field.syntax]
Syntax
FieldExpression → Expression . IDENTIFIER

Show syntax diagrams

[expr.field.intro]
A field expression is a place expression that evaluates to the location of a field of a struct or union.
[expr.field.mut]
When the operand is mutable, the field expression is also mutable.
[expr.field.form]
The syntax for a field expression is an expression, called the container operand, then a ., and finally an identifier.
[expr.field.not-method-call]
Field expressions cannot be followed by a parenthetical comma-separated list of expressions, as that is instead parsed as a method call expression. That is, they cannot be the function operand of a call expression.
Note

Wrap the field expression in a parenthesized expression to use it in a call expression.

let holds_callable = HoldsCallable { callable: || () };

// Invalid: Parsed as calling the method "callable"
// holds_callable.callable();

// Valid
(holds_callable.callable)();
Examples:
mystruct.myfield;
foo().x;
(Struct {a: 10, b: 20}).a;
(mystruct.function_field)() // Call expression containing a field expression
[expr.field.autoref-deref]
Automatic dereferencing
If the type of the container operand implements Deref or DerefMut depending on whether the operand is mutable, it is automatically dereferenced as many times as necessary to make the field access possible. This process is also called autoderef for short.
[expr.field.borrow]
Borrowing
The fields of a struct or a reference to a struct are treated as separate entities when borrowing. If the struct does not implement Drop and is stored in a local variable, this also applies to moving out of each of its fields. This also does not apply if automatic dereferencing is done through user-defined types other than Box.
struct A { f1: String, f2: String, f3: String }
let mut x: A;
let a: &mut String = &mut x.f1; // x.f1 borrowed mutably
let b: &String = &x.f2;         // x.f2 borrowed immutably
let c: &String = &x.f2;         // Can borrow again
let d: String = x.f3;           // Move out of x.f3
[expr.closure]
### Closure expressions

[expr.closure.syntax]
Syntax
ClosureExpression →
    async?​1
    move?
    ( || | | ClosureParameters? | )
    ( Expression | -> TypeNoBounds BlockExpression )

ClosureParameters → ClosureParam ( , ClosureParam )* ,?

ClosureParam → OuterAttribute* PatternNoTopAlt ( : Type )?

Show syntax diagrams

[expr.closure.intro]
A closure expression, also known as a lambda expression or a lambda, defines a closure type and evaluates to a value of that type. The syntax for a closure expression is an optional async keyword, an optional move keyword, then a pipe-symbol-delimited (|) comma-separated list of patterns, called the closure parameters each optionally followed by a : and a type, then an optional -> and type, called the return type, and then an expression, called the closure body operand.
[expr.closure.param-type]
The optional type after each pattern is a type annotation for the pattern.
[expr.closure.explicit-type-body]
If there is a return type, the closure body must be a block.
[expr.closure.parameter-restriction]
A closure expression denotes a function that maps a list of parameters onto the expression that follows the parameters. Just like a let binding, the closure parameters are irrefutable patterns, whose type annotation is optional and will be inferred from context if not given.
[expr.closure.unique-type]
Each closure expression has a unique, anonymous type.
[expr.closure.captures]
Significantly, closure expressions capture their environment, which regular function definitions do not.
[expr.closure.capture-inference]
Without the move keyword, the closure expression infers how it captures each variable from its environment, preferring to capture by shared reference, effectively borrowing all outer variables mentioned inside the closure’s body.
[expr.closure.capture-mut-ref]
If needed the compiler will infer that instead mutable references should be taken, or that the values should be moved or copied (depending on their type) from the environment.
[expr.closure.capture-move]
A closure can be forced to capture its environment by copying or moving values by prefixing it with the move keyword. This is often used to ensure that the closure’s lifetime is 'static.
[expr.closure.trait-impl]
Closure trait implementations
Which traits the closure type implement depends on how variables are captured, the types of the captured variables, and the presence of async. See the call traits and coercions chapter for how and when a closure implements Fn, FnMut, and FnOnce. The closure type implements Send and Sync if the type of every captured variable also implements the trait.
[expr.closure.async]
Async closures
[expr.closure.async.intro]
Closures marked with the async keyword indicate that they are asynchronous in an analogous way to an async function.
[expr.closure.async.future]
Calling the async closure does not perform any work, but instead evaluates to a value that implements Future that corresponds to the computation of the body of the closure.
async fn takes_async_callback(f: impl AsyncFn(u64)) {
    f(0).await;
    f(1).await;
}

async fn example() {
    takes_async_callback(async |i| {
        core::future::ready(i).await;
        println!("done with {i}.");
    }).await;
}
[expr.closure.async.edition2018]
2018
Edition differences

Async closures are only available beginning with Rust 2018.
Example
In this example, we define a function ten_times that takes a higher-order function argument, and we then call it with a closure expression as an argument, followed by a closure expression that moves values from its environment.
fn ten_times<F>(f: F) where F: Fn(i32) {
    for index in 0..10 {
        f(index);
    }
}

ten_times(|j| println!("hello, {}", j));
// With type annotations
ten_times(|j: i32| -> () { println!("hello, {}", j) });

let word = "konnichiwa".to_owned();
ten_times(move |j| println!("{}, {}", word, j));
Attributes on closure parameters
[expr.closure.param-attributes]
Attributes on closure parameters follow the same rules and restrictions as regular function parameters.
The async qualifier is not allowed in the 2015 edition. ↩

[expr.loop]
Loops and other breakable expressions

[expr.loop.syntax]
Syntax
LoopExpression →
    LoopLabel? (
        InfiniteLoopExpression
      | PredicateLoopExpression
      | IteratorLoopExpression
      | LabelBlockExpression
    )

Show syntax diagrams

[expr.loop.intro]
### Loop expressions
A loop expression denotes an infinite loop.
A while expression loops until a predicate is false.
A for expression extracts values from an iterator, looping until the iterator is empty.
A labelled block expression runs a loop exactly once, but allows exiting the loop early with break.
[expr.loop.break-label]
All four types of loop support break expressions, and labels.
[expr.loop.continue-label]
All except labelled block expressions support continue expressions.
[expr.loop.explicit-result]
Only loop and labelled block expressions support evaluation to non-trivial values.
[expr.loop.infinite]
Infinite loops
[expr.loop.infinite.syntax]
Syntax
InfiniteLoopExpression → loop BlockExpression

Show syntax diagrams

[expr.loop.infinite.intro]
A loop expression repeats execution of its body continuously: loop { println!("I live."); }.
[expr.loop.infinite.diverging]
A loop expression without an associated break expression is diverging and has type !.
[expr.loop.infinite.break]
A loop expression containing associated break expression(s) may terminate, and must have type compatible with the value of the break expression(s).
[expr.loop.while]
Predicate loops
[expr.loop.while.grammar]
Syntax
PredicateLoopExpression → while Conditions BlockExpression

Show syntax diagrams

[expr.loop.while.intro]
A while loop expression allows repeating the evaluation of a block while a set of conditions remain true.
[expr.loop.while.syntax]
The syntax of a while expression is a sequence of one or more condition operands separated by &&, followed by a BlockExpression.
[expr.loop.while.condition]
Condition operands must be either an Expression with a boolean type or a conditional let match. If all of the condition operands evaluate to true and all of the let patterns successfully match their scrutinees, then the loop body block executes.
[expr.loop.while.repeat]
After the loop body successfully executes, the condition operands are re-evaluated to determine if the body should be executed again.
[expr.loop.while.exit]
If any condition operand evaluates to false or any let pattern does not match its scrutinee, the body is not executed and execution continues after the while expression.
[expr.loop.while.eval]
A while expression evaluates to ().
An example:
let mut i = 0;

while i < 10 {
    println!("hello");
    i = i + 1;
}
[expr.loop.while.let]
while let patterns
[expr.loop.while.let.intro]
let patterns in a while condition allow binding new variables into scope when the pattern matches successfully. The following examples illustrate bindings using let patterns:
let mut x = vec![1, 2, 3];

while let Some(y) = x.pop() {
    println!("y = {}", y);
}

while let _ = 5 {
    println!("Irrefutable patterns are always true");
    break;
}
[expr.loop.while.let.desugar]
A while let loop is equivalent to a loop expression containing a match expression as follows.
'label: while let PATS = EXPR {
    /* loop body */
}
is equivalent to
'label: loop {
    match EXPR {
        PATS => { /* loop body */ },
        _ => break,
    }
}
[expr.loop.while.let.or-pattern]
### Match expressions
let mut vals = vec![2, 3, 1, 2, 2];
while let Some(v @ 1) | Some(v @ 2) = vals.pop() {
    // Prints 2, 2, then 1
    println!("{}", v);
}
[expr.loop.while.chains]
while condition chains
[expr.loop.while.chains.intro]
Multiple condition operands can be separated with &&. These have the same semantics and restrictions as if condition chains.
The following is an example of chaining multiple expressions, mixing let bindings and boolean expressions, and with expressions able to reference pattern bindings from previous expressions:
fn main() {
    let outer_opt = Some(Some(1i32));

    while let Some(inner_opt) = outer_opt
        && let Some(number) = inner_opt
        && number == 1
    {
        println!("Peek a boo");
        break;
    }
}
[expr.loop.for]
Iterator loops
[expr.loop.for.syntax]
Syntax
IteratorLoopExpression →
    for Pattern in Expressionexcept StructExpression BlockExpression

Show syntax diagrams

[expr.loop.for.intro]
A for expression is a syntactic construct for looping over elements provided by an implementation of std::iter::IntoIterator.
[expr.loop.for.condition]
If the iterator yields a value, that value is matched against the irrefutable pattern, the body of the loop is executed, and then control returns to the head of the for loop. If the iterator is empty, the for expression completes.
An example of a for loop over the contents of an array:
let v = &["apples", "cake", "coffee"];

for text in v {
    println!("I like {}.", text);
}
An example of a for loop over a series of integers:
let mut sum = 0;
for n in 1..11 {
    sum += n;
}
assert_eq!(sum, 55);
[expr.loop.for.desugar]
A for loop is equivalent to a loop expression containing a match expression as follows:
'label: for PATTERN in iter_expr {
    /* loop body */
}
is equivalent to
{
    let result = match IntoIterator::into_iter(iter_expr) {
        mut iter => 'label: loop {
            let mut next;
            match Iterator::next(&mut iter) {
                Option::Some(val) => next = val,
                Option::None => break,
            };
            let PATTERN = next;
            let () = { /* loop body */ };
        },
    };
    result
}
[expr.loop.for.lang-items]
IntoIterator, Iterator, and Option are always the standard library items here, not whatever those names resolve to in the current scope.
The variable names next, iter, and val are for exposition only, they do not actually have names the user can type.
Note

The outer match is used to ensure that any temporary values in iter_expr don’t get dropped before the loop is finished. next is declared before being assigned because it results in types being inferred correctly more often.
[expr.loop.label]
Loop labels
[expr.loop.label.syntax]
Syntax
LoopLabel → LIFETIME_OR_LABEL :

Show syntax diagrams

[expr.loop.label.intro]
A loop expression may optionally have a label. The label is written as a lifetime preceding the loop expression, as in 'foo: loop { break 'foo; }, 'bar: while false {}, 'humbug: for _ in 0..0 {}.
[expr.loop.label.control-flow]
If a label is present, then labeled break and continue expressions nested within this loop may exit out of this loop or return control to its head. See break expressions and continue expressions.
[expr.loop.label.ref]
Labels follow the hygiene and shadowing rules of local variables. For example, this code will print “outer loop”:
'a: loop {
    'a: loop {
        break 'a;
    }
    print!("outer loop");
    break 'a;
}
'_ is not a valid loop label.
[expr.loop.break]
break expressions
[expr.loop.break.syntax]
Syntax
BreakExpression → break LIFETIME_OR_LABEL? Expression?

Show syntax diagrams

[expr.loop.break.intro]
When break is encountered, execution of the associated loop body is immediately terminated, for example:
let mut last = 0;
for x in 1..100 {
    if x > 12 {
        break;
    }
    last = x;
}
assert_eq!(last, 12);
[expr.loop.break.label]
A break expression is normally associated with the innermost loop, for or while loop enclosing the break expression, but a label can be used to specify which enclosing loop is affected. Example:
'outer: loop {
    while true {
        break 'outer;
    }
}
[expr.loop.break.value]
A break expression is only permitted in the body of a loop, and has one of the forms break, break 'label or (see below) break EXPR or break 'label EXPR.
[expr.loop.block-labels]
Labelled block expressions
[expr.loop.block-labels.syntax]
Syntax
LabelBlockExpression → BlockExpression

Show syntax diagrams

[expr.loop.block-labels.intro]
Labelled block expressions are exactly like block expressions, except that they allow using break expressions within the block.
[expr.loop.block-labels.break]
Unlike loops, break expressions within a labelled block expression must have a label (i.e. the label is not optional).
[expr.loop.block-labels.label-required]
Similarly, labelled block expressions must begin with a label.
let result = 'block: {
    do_thing();
    if condition_not_met() {
        break 'block 1;
    }
    do_next_thing();
    if condition_not_met() {
        break 'block 2;
    }
    do_last_thing();
    3
};
[expr.loop.continue]
continue expressions
[expr.loop.continue.syntax]
Syntax
ContinueExpression → continue LIFETIME_OR_LABEL?

Show syntax diagrams

[expr.loop.continue.intro]
When continue is encountered, the current iteration of the associated loop body is immediately terminated, returning control to the loop head.
[expr.loop.continue.while]
In the case of a while loop, the head is the conditional operands controlling the loop.
[expr.loop.continue.for]
In the case of a for loop, the head is the call-expression controlling the loop.
[expr.loop.continue.label]
Like break, continue is normally associated with the innermost enclosing loop, but continue 'label may be used to specify the loop affected.
[expr.loop.continue.in-loop-only]
A continue expression is only permitted in the body of a loop.
[expr.loop.break-value]
break and loop values
[expr.loop.break-value.intro]
When associated with a loop, a break expression may be used to return a value from that loop, via one of the forms break EXPR or break 'label EXPR, where EXPR is an expression whose result is returned from the loop. For example:
let (mut a, mut b) = (1, 1);
let result = loop {
    if b > 10 {
        break b;
    }
    let c = a + b;
    a = b;
    b = c;
};
// first number in Fibonacci sequence over 10:
assert_eq!(result, 13);
[expr.loop.break-value.loop]
In the case a loop has an associated break, it is not considered diverging, and the loop must have a type compatible with each break expression. break without an expression is considered identical to break with expression ().
[expr.range]
### Range expressions

[expr.range.syntax]
Syntax
RangeExpression →
      RangeExpr
    | RangeFromExpr
    | RangeToExpr
    | RangeFullExpr
    | RangeInclusiveExpr
    | RangeToInclusiveExpr

RangeExpr → Expression .. Expression

RangeFromExpr → Expression ..

RangeToExpr → .. Expression

RangeFullExpr → ..

RangeInclusiveExpr → Expression ..= Expression

RangeToInclusiveExpr → ..= Expression

Show syntax diagrams

[expr.range.behavior]
The .. and ..= operators will construct an object of one of the std::ops::Range (or core::ops::Range) variants, according to the following table:
Production	Syntax	Type	Range
RangeExpr	start..end	std::ops::Range	start ≤ x < end
RangeFromExpr	start..	std::ops::RangeFrom	start ≤ x
RangeToExpr	..end	std::ops::RangeTo	x < end
RangeFullExpr	..	std::ops::RangeFull	-
RangeInclusiveExpr	start..=end	std::ops::RangeInclusive	start ≤ x ≤ end
RangeToInclusiveExpr	..=end	std::ops::RangeToInclusive	x ≤ end
Examples:
1..2;   // std::ops::Range
3..;    // std::ops::RangeFrom
..4;    // std::ops::RangeTo
..;     // std::ops::RangeFull
5..=6;  // std::ops::RangeInclusive
..=7;   // std::ops::RangeToInclusive
[expr.range.equivalence]
The following expressions are equivalent.
let x = std::ops::Range {start: 0, end: 10};
let y = 0..10;

assert_eq!(x, y);
[expr.range.for]
Ranges can be used in for loops:
for i in 1..11 {
    println!("{}", i);
}
[expr.if]
### If expressions

[expr.if.syntax]
Syntax
IfExpression →
    if Conditions BlockExpression
    ( else ( BlockExpression | IfExpression ) )?

Conditions →
      Expressionexcept StructExpression
    | LetChain

LetChain → LetChainCondition ( && LetChainCondition )*

LetChainCondition →
      Expressionexcept ExcludedConditions
    | OuterAttribute* let Pattern = Scrutineeexcept ExcludedConditions

ExcludedConditions →
      StructExpression
    | LazyBooleanExpression
    | RangeExpr
    | RangeFromExpr
    | RangeInclusiveExpr
    | AssignmentExpression
    | CompoundAssignmentExpression

Show syntax diagrams

[expr.if.intro]
The syntax of an if expression is a sequence of one or more condition operands separated by &&, followed by a consequent block, any number of else if conditions and blocks, and an optional trailing else block.
[expr.if.condition]
Condition operands must be either an Expression with a boolean type or a conditional let match.
[expr.if.condition-true]
If all of the condition operands evaluate to true and all of the let patterns successfully match their scrutinees, the consequent block is executed and any subsequent else if or else block is skipped.
[expr.if.else-if]
If any condition operand evaluates to false or any let pattern does not match its scrutinee, the consequent block is skipped and any subsequent else if condition is evaluated.
[expr.if.else]
If all if and else if conditions evaluate to false then any else block is executed.
[expr.if.result]
An if expression evaluates to the same value as the executed block, or () if no block is evaluated.
[expr.if.type]
An if expression must have the same type in all situations.
if x == 4 {
    println!("x is four");
} else if x == 3 {
    println!("x is three");
} else {
    println!("x is something else");
}

// `if` can be used as an expression.
let y = if 12 * 15 > 150 {
    "Bigger"
} else {
    "Smaller"
};
assert_eq!(y, "Bigger");
[expr.if.let]
if let patterns
[expr.if.let.intro]
let patterns in an if condition allow binding new variables into scope when the pattern matches successfully.
The following examples illustrate bindings using let patterns:
let dish = ("Ham", "Eggs");

// This body will be skipped because the pattern is refuted.
if let ("Bacon", b) = dish {
    println!("Bacon is served with {}", b);
} else {
    // This block is evaluated instead.
    println!("No bacon will be served");
}

// This body will execute.
if let ("Ham", b) = dish {
    println!("Ham is served with {}", b);
}

if let _ = 5 {
    println!("Irrefutable patterns are always true");
}
[expr.if.let.or-pattern]
Multiple patterns may be specified with the | operator. This has the same semantics as with | in match expressions:
enum E {
    X(u8),
    Y(u8),
    Z(u8),
}
let v = E::Y(12);
if let E::X(n) | E::Y(n) = v {
    assert_eq!(n, 12);
}
[expr.if.chains]
Chains of conditions
[expr.if.chains.intro]
Multiple condition operands can be separated with &&.
[expr.if.chains.order]
Similar to a && LazyBooleanExpression, each operand is evaluated from left-to-right until an operand evaluates as false or a let match fails, in which case the subsequent operands are not evaluated.
[expr.if.chains.bindings]
The bindings of each pattern are put into scope to be available for the next condition operand and the consequent block.
The following is an example of chaining multiple expressions, mixing let bindings and boolean expressions, and with expressions able to reference pattern bindings from previous expressions:
fn single() {
    let outer_opt = Some(Some(1i32));

    if let Some(inner_opt) = outer_opt
        && let Some(number) = inner_opt
        && number == 1
    {
        println!("Peek a boo");
    }
}
The above is equivalent to the following without using chains of conditions:
fn nested() {
    let outer_opt = Some(Some(1i32));

    if let Some(inner_opt) = outer_opt {
        if let Some(number) = inner_opt {
            if number == 1 {
                println!("Peek a boo");
            }
        }
    }
}
[expr.if.chains.or]
If any condition operand is a let pattern, then none of the condition operands can be a || lazy boolean operator expression due to ambiguity and precedence with the let scrutinee. If a || expression is needed, then parentheses can be used. For example:
// Parentheses are required here.
if let Some(x) = foo && (condition1 || condition2) { /*...*/ }
[expr.if.edition2024]
2024
Edition differences

Before the 2024 edition, let chains are not supported. That is, the LetChain grammar is not allowed in an if expression.
[expr.match]
match expressions

[expr.match.syntax]
Syntax
MatchExpression →
    match Scrutinee {
        InnerAttribute*
        MatchArms?
    }

Scrutinee → Expressionexcept StructExpression

MatchArms →
    ( MatchArm => ( ExpressionWithoutBlock , | ExpressionWithBlock ,? ) )*
    MatchArm => Expression ,?

MatchArm → OuterAttribute* Pattern MatchArmGuard?

MatchArmGuard → if Expression

Show syntax diagrams

[expr.match.intro]
A match expression branches on a pattern. The exact form of matching that occurs depends on the pattern.
[expr.match.scrutinee]
A match expression has a scrutinee expression, which is the value to compare to the patterns.
[expr.match.scrutinee-constraint]
The scrutinee expression and the patterns must have the same type.
[expr.match.scrutinee-behavior]
A match behaves differently depending on whether or not the scrutinee expression is a place expression or value expression.
[expr.match.scrutinee-value]
If the scrutinee expression is a value expression, it is first evaluated into a temporary location, and the resulting value is sequentially compared to the patterns in the arms until a match is found. The first arm with a matching pattern is chosen as the branch target of the match, any variables bound by the pattern are assigned to local variables in the arm’s block, and control enters the block.
[expr.match.scrutinee-place]
When the scrutinee expression is a place expression, the match does not allocate a temporary location; however, a by-value binding may copy or move from the memory location. When possible, it is preferable to match on place expressions, as the lifetime of these matches inherits the lifetime of the place expression rather than being restricted to the inside of the match.
An example of a match expression:
let x = 1;

match x {
    1 => println!("one"),
    2 => println!("two"),
    3 => println!("three"),
    4 => println!("four"),
    5 => println!("five"),
    _ => println!("something else"),
}
[expr.match.pattern-vars]
Variables bound within the pattern are scoped to the match guard and the arm’s expression.
[expr.match.pattern-var-binding]
The binding mode (move, copy, or reference) depends on the pattern.
[expr.match.or-pattern]
Multiple match patterns may be joined with the | operator. Each pattern will be tested in left-to-right sequence until a successful match is found.
let x = 9;
let message = match x {
    0 | 1  => "not many",
    2 ..= 9 => "a few",
    _      => "lots"
};

assert_eq!(message, "a few");

// Demonstration of pattern match order.
struct S(i32, i32);

match S(1, 2) {
    S(z @ 1, _) | S(_, z @ 2) => assert_eq!(z, 1),
    _ => panic!(),
}
Note

The 2..=9 is a Range Pattern, not a Range Expression. Thus, only those types of ranges supported by range patterns can be used in match arms.
[expr.match.or-patterns-restriction]
Every binding in each | separated pattern must appear in all of the patterns in the arm.
[expr.match.binding-restriction]
Every binding of the same name must have the same type, and have the same binding mode.
[expr.match.guard]
Match guards
[expr.match.guard.intro]
Match arms can accept match guards to further refine the criteria for matching a case.
[expr.match.guard.type]
Pattern guards appear after the pattern and consist of a bool-typed expression following the if keyword.
[expr.match.guard.behavior]
When the pattern matches successfully, the pattern guard expression is executed. If the expression evaluates to true, the pattern is successfully matched against.
[expr.match.guard.next]
Otherwise, the next pattern, including other matches with the | operator in the same arm, is tested.
let message = match maybe_digit {
    Some(x) if x < 10 => process_digit(x),
    Some(x) => process_other(x),
    None => panic!(),
};
Note

Multiple matches using the | operator can cause the pattern guard and the side effects it has to execute multiple times. For example:

let i : Cell<i32> = Cell::new(0);
match 1 {
    1 | _ if { i.set(i.get() + 1); false } => {}
    _ => {}
}
assert_eq!(i.get(), 2);
[expr.match.guard.bound-variables]
A pattern guard may refer to the variables bound within the pattern they follow.
[expr.match.guard.shared-ref]
Before evaluating the guard, a shared reference is taken to the part of the scrutinee the variable matches on. While evaluating the guard, this shared reference is then used when accessing the variable.
[expr.match.guard.value]
Only when the guard evaluates to true is the value moved, or copied, from the scrutinee into the variable. This allows shared borrows to be used inside guards without moving out of the scrutinee in case guard fails to match.
[expr.match.guard.no-mutation]
Moreover, by holding a shared reference while evaluating the guard, mutation inside guards is also prevented.
[expr.match.attributes]
Attributes on match arms
[expr.match.attributes.outer]
Outer attributes are allowed on match arms. The only attributes that have meaning on match arms are cfg and the lint check attributes.
[expr.match.attributes.inner]
Inner attributes are allowed directly after the opening brace of the match expression in the same expression contexts as attributes on block expressions.
[expr.return]
return expressions

[expr.return.syntax]
Syntax
ReturnExpression → return Expression?

Show syntax diagrams

[expr.return.intro]
Return expressions are denoted with the keyword return.
[expr.return.behavior]
Evaluating a return expression moves its argument into the designated output location for the current function call, destroys the current function activation frame, and transfers control to the caller frame.
An example of a return expression:
fn max(a: i32, b: i32) -> i32 {
    if a > b {
        return a;
    }
    return b;
}
[expr.await]
### Await expressions

[expr.await.syntax]
Syntax
AwaitExpression → Expression . await

Show syntax diagrams

[expr.await.intro]
An await expression is a syntactic construct for suspending a computation provided by an implementation of std::future::IntoFuture until the given future is ready to produce a value.
[expr.await.construct]
The syntax for an await expression is an expression with a type that implements the IntoFuture trait, called the future operand, then the token ., and then the await keyword.
[expr.await.allowed-positions]
Await expressions are legal only within an async context, like an async fn, async closure, or async block.
[expr.await.effects]
More specifically, an await expression has the following effect.
Create a future by calling IntoFuture::into_future on the future operand.
Evaluate the future to a future tmp;
Pin tmp using Pin::new_unchecked;
This pinned future is then polled by calling the Future::poll method and passing it the current task context;
If the call to poll returns Poll::Pending, then the future returns Poll::Pending, suspending its state so that, when the surrounding async context is re-polled,execution returns to step 3;
Otherwise the call to poll must have returned Poll::Ready, in which case the value contained in the Poll::Ready variant is used as the result of the await expression itself.
[expr.await.edition2018]
2018
Edition differences

Await expressions are only available beginning with Rust 2018.
[expr.await.task]
Task context
The task context refers to the Context which was supplied to the current async context when the async context itself was polled. Because await expressions are only legal in an async context, there must be some task context available.
[expr.await.desugar]
Approximate desugaring
Effectively, an await expression is roughly equivalent to the following non-normative desugaring:
match operand.into_future() {
    mut pinned => loop {
        let mut pin = unsafe { Pin::new_unchecked(&mut pinned) };
        match Pin::future::poll(Pin::borrow(&mut pin), &mut current_context) {
            Poll::Ready(r) => break r,
            Poll::Pending => yield Poll::Pending,
        }
    }
}
where the yield pseudo-code returns Poll::Pending and, when re-invoked, resumes execution from that point. The variable current_context refers to the context taken from the async environment.
[expr.placeholder]
_ expressions

[expr.placeholder.syntax]
Syntax
UnderscoreExpression → _

Show syntax diagrams

[expr.placeholder.intro]
Underscore expressions, denoted with the symbol _, are used to signify a placeholder in a destructuring assignment.
[expr.placeholder.lhs-assignment-only]
They may only appear in the left-hand side of an assignment.
[expr.placeholder.pattern]
Note that this is distinct from the wildcard pattern.
Examples of _ expressions:
let p = (1, 2);
let mut a = 0;
(_, a) = p;

struct Position {
    x: u32,
    y: u32,
}

Position { x: a, y: _ } = Position{ x: 2, y: 3 };

// unused result, assignment to `_` used to declare intent and remove a warning
_ = 2 + 2;
// triggers unused_must_use warning
// 2 + 2;

// equivalent technique using a wildcard pattern in a let-binding
let _ = 2 + 2;
[patterns]
