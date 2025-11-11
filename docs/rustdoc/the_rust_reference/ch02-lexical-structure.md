# Lexical structure
[input]
## Input format

[input.syntax]
Lexer
CHAR → <a Unicode scalar value>

NUL → U+0000

TAB → U+0009

LF → U+000A

CR → U+000D

Show syntax diagrams

[input.intro]
This chapter describes how a source file is interpreted as a sequence of tokens.
See Crates and source files for a description of how programs are organised into files.
[input.encoding]
Source encoding
[input.encoding.utf8]
Tests
Each source file is interpreted as a sequence of Unicode characters encoded in UTF-8.
[input.encoding.invalid]
Tests
It is an error if the file is not valid UTF-8.
[input.byte-order-mark]
Tests
Byte order mark removal
If the first character in the sequence is U+FEFF (BYTE ORDER MARK), it is removed.
[input.crlf]
Tests
CRLF normalization
Each pair of characters U+000D (CR) immediately followed by U+000A (LF) is replaced by a single U+000A (LF). This happens once, not repeatedly, so after the normalization, there can still exist U+000D (CR) immediately followed by U+000A (LF) in the input (e.g. if the raw input contained “CR CR LF LF”).
Other occurrences of the character U+000D (CR) are left in place (they are treated as whitespace).
[input.shebang]
Tests
Shebang removal
[input.shebang.intro]
If the remaining sequence begins with the characters #!, the characters up to and including the first U+000A (LF) are removed from the sequence.
For example, the first line of the following file would be ignored:
#!/usr/bin/env rustx

fn main() {
    println!("Hello!");
}
[input.shebang.inner-attribute]
Tests
As an exception, if the #! characters are followed (ignoring intervening comments or whitespace) by a [ token, nothing is removed. This prevents an inner attribute at the start of a source file being removed.
Note

The standard library include! macro applies byte order mark removal, CRLF normalization, and shebang removal to the file it reads. The include_str! and include_bytes! macros do not.
[input.tokenization]
Tokenization
The resulting sequence of characters is then converted into tokens as described in the remainder of this chapter.
[lex.keywords]
## Keywords

Rust divides keywords into three categories:
strict
reserved
weak
[lex.keywords.strict]
Strict keywords
[lex.keywords.strict.intro]
These keywords can only be used in their correct contexts. They cannot be used as the names of:
Items
Variables and function parameters
Fields and variants
Type parameters
Lifetime parameters or loop labels
Macros or attributes
Macro placeholders
Crates
[lex.keywords.strict.list]
The following keywords are in all editions:
as
break
const
continue
crate
else
enum
extern
false
fn
for
if
impl
in
let
loop
match
mod
move
mut
pub
ref
return
self
Self
static
struct
super
trait
true
type
unsafe
use
where
while
[lex.keywords.strict.edition2018]
The following keywords were added beginning in the 2018 edition.
async
await
dyn
[lex.keywords.reserved]
Reserved keywords
[lex.keywords.reserved.intro]
These keywords aren’t used yet, but they are reserved for future use. They have the same restrictions as strict keywords. The reasoning behind this is to make current programs forward compatible with future versions of Rust by forbidding them to use these keywords.
[lex.keywords.reserved.list]
abstract
become
box
do
final
macro
override
priv
typeof
unsized
virtual
yield
[lex.keywords.reserved.edition2018]
The following keywords are reserved beginning in the 2018 edition.
try
[lex.keywords.reserved.edition2024]
The following keywords are reserved beginning in the 2024 edition.
gen
[lex.keywords.weak]
Weak keywords
[lex.keywords.weak.intro]
These keywords have special meaning only in certain contexts. For example, it is possible to declare a variable or method with the name union.
'static
macro_rules
raw
safe
union
[lex.keywords.weak.macro_rules]
macro_rules is used to create custom macros.
[lex.keywords.weak.union]
union is used to declare a union and is only a keyword when used in a union declaration.
[lex.keywords.weak.lifetime-static]
'static is used for the static lifetime and cannot be used as a generic lifetime parameter or loop label

// error[E0262]: invalid lifetime parameter name: `'static`
fn invalid_lifetime_parameter<'static>(s: &'static str) -> &'static str { s }
[lex.keywords.weak.safe]
safe is used for functions and statics, which has meaning in external blocks.
[lex.keywords.weak.raw]
raw is used for raw borrow operators, and is only a keyword when matching a raw borrow operator form (such as &raw const expr or &raw mut expr).
[lex.keywords.weak.dyn.edition2018]
2018
Edition differences

In the 2015 edition, dyn is a keyword when used in a type position followed by a path that does not start with :: or <, a lifetime, a question mark, a for keyword or an opening parenthesis.

Beginning in the 2018 edition, dyn has been promoted to a strict keyword.
[ident]
## Identifiers

[ident.syntax]
Lexer
IDENTIFIER_OR_KEYWORD →
      XID_Start XID_Continue*
    | _ XID_Continue+

XID_Start → <XID_Start defined by Unicode>

XID_Continue → <XID_Continue defined by Unicode>

RAW_IDENTIFIER → r# IDENTIFIER_OR_KEYWORDexcept crate, self, super, Self

NON_KEYWORD_IDENTIFIER → IDENTIFIER_OR_KEYWORDexcept a strict or reserved keyword

IDENTIFIER → NON_KEYWORD_IDENTIFIER | RAW_IDENTIFIER

RESERVED_RAW_IDENTIFIER → r#_

Show syntax diagrams

[ident.unicode]
Tests
Identifiers follow the specification in Unicode Standard Annex #31 for Unicode version 16.0, with the additions described below. Some examples of identifiers:
foo
_identifier
r#true
Москва
東京
[ident.profile]
The profile used from UAX #31 is:
Start := XID_Start, plus the underscore character (U+005F)
Continue := XID_Continue
Medial := empty
with the additional constraint that a single underscore character is not an identifier.
Note

Identifiers starting with an underscore are typically used to indicate an identifier that is intentionally unused, and will silence the unused warning in rustc.
[ident.keyword]
Identifiers may not be a strict or reserved keyword without the r# prefix described below in raw identifiers.
[ident.zero-width-chars]
Zero width non-joiner (ZWNJ U+200C) and zero width joiner (ZWJ U+200D) characters are not allowed in identifiers.
[ident.ascii-limitations]
Identifiers are restricted to the ASCII subset of XID_Start and XID_Continue in the following situations:
extern crate declarations (except the AsClause identifier)
External crate names referenced in a path
Module names loaded from the filesystem without a path attribute
no_mangle attributed items
Item names in external blocks
[ident.normalization]
Tests
Normalization
Identifiers are normalized using Normalization Form C (NFC) as defined in Unicode Standard Annex #15. Two identifiers are equal if their NFC forms are equal.
Procedural and declarative macros receive normalized identifiers in their input.
[ident.raw]
Raw identifiers
[ident.raw.intro]
A raw identifier is like a normal identifier, but prefixed by r#. (Note that the r# prefix is not included as part of the actual identifier.)
[ident.raw.allowed]
Unlike a normal identifier, a raw identifier may be any strict or reserved keyword except the ones listed above for RAW_IDENTIFIER.
[ident.raw.reserved]
It is an error to use the RESERVED_RAW_IDENTIFIER token r#_ in order to avoid confusion with the WildcardPattern.
[comments]
## Comments

[comments.syntax]
Lexer
LINE_COMMENT →
      // ( ~[/ ! LF] | // ) ~LF*
    | //

BLOCK_COMMENT →
      /*
        ( ~[* !] | ** | BLOCK_COMMENT_OR_DOC )
        ( BLOCK_COMMENT_OR_DOC | ~*/ )*
      */
    | /**/
    | /***/

INNER_LINE_DOC →
    //! ~[LF CR]*

INNER_BLOCK_DOC →
    /*! ( BLOCK_COMMENT_OR_DOC | ~[*/ CR] )* */

OUTER_LINE_DOC →
    /// ( ~/ ~[LF CR]* )?

OUTER_BLOCK_DOC →
    /**
      ( ~* | BLOCK_COMMENT_OR_DOC )
      ( BLOCK_COMMENT_OR_DOC | ~[*/ CR] )*
    */

BLOCK_COMMENT_OR_DOC →
      BLOCK_COMMENT
    | OUTER_BLOCK_DOC
    | INNER_BLOCK_DOC

Show syntax diagrams

[comments.normal]
Non-doc comments
Comments follow the general C++ style of line (//) and block (/* ... */) comment forms. Nested block comments are supported.
[comments.normal.tokenization]
Non-doc comments are interpreted as a form of whitespace.
[comments.doc]
Doc comments
[comments.doc.syntax]
Line doc comments beginning with exactly three slashes (///), and block doc comments (/** ... */), both outer doc comments, are interpreted as a special syntax for doc attributes.
[comments.doc.attributes]
That is, they are equivalent to writing #[doc="..."] around the body of the comment, i.e., /// Foo turns into #[doc="Foo"] and /** Bar */ turns into #[doc="Bar"]. They must therefore appear before something that accepts an outer attribute.
[comments.doc.inner-syntax]
Line comments beginning with //! and block comments /*! ... */ are doc comments that apply to the parent of the comment, rather than the item that follows.
[comments.doc.inner-attributes]
That is, they are equivalent to writing #![doc="..."] around the body of the comment. //! comments are usually used to document modules that occupy a source file.
[comments.doc.bare-crs]
The character U+000D (CR) is not allowed in doc comments.
Note

It is conventional for doc comments to contain Markdown, as expected by rustdoc. However, the comment syntax does not respect any internal Markdown. /** `glob = "*/*.rs";` */ terminates the comment at the first */, and the remaining code would cause a syntax error. This slightly limits the content of block doc comments compared to line doc comments.
Note

The sequence U+000D (CR) immediately followed by U+000A (LF) would have been previously transformed into a single U+000A (LF).
Examples
//! A doc comment that applies to the implicit anonymous module of this crate

pub mod outer_module {

    //!  - Inner line doc
    //!! - Still an inner line doc (but with a bang at the beginning)

    /*!  - Inner block doc */
    /*!! - Still an inner block doc (but with a bang at the beginning) */

    //   - Only a comment
    ///  - Outer line doc (exactly 3 slashes)
    //// - Only a comment

    /*   - Only a comment */
    /**  - Outer block doc (exactly) 2 asterisks */
    /*** - Only a comment */

    pub mod inner_module {}

    pub mod nested_comments {
        /* In Rust /* we can /* nest comments */ */ */

        // All three types of block comments can contain or be nested inside
        // any other type:

        /*   /* */  /** */  /*! */  */
        /*!  /* */  /** */  /*! */  */
        /**  /* */  /** */  /*! */  */
        pub mod dummy_item {}
    }

    pub mod degenerate_cases {
        // empty inner line doc
        //!

        // empty inner block doc
        /*!*/

        // empty line comment
        //

        // empty outer line doc
        ///

        // empty block comment
        /**/

        pub mod dummy_item {}

        // empty 2-asterisk block isn't a doc block, it is a block comment
        /***/

    }

    /* The next one isn't allowed because outer doc comments
       require an item that will receive the doc */

    /// Where is my item?
}
[lex.whitespace]
## Whitespace

[lex.whitespace.intro]
Whitespace is any non-empty string containing only characters that have the Pattern_White_Space Unicode property, namely:
U+0009 (horizontal tab, '\t')
U+000A (line feed, '\n')
U+000B (vertical tab)
U+000C (form feed)
U+000D (carriage return, '\r')
U+0020 (space, ' ')
U+0085 (next line)
U+200E (left-to-right mark)
U+200F (right-to-left mark)
U+2028 (line separator)
U+2029 (paragraph separator)
[lex.whitespace.token-sep]
Rust is a “free-form” language, meaning that all forms of whitespace serve only to separate tokens in the grammar, and have no semantic significance.
[lex.whitespace.replacement]
A Rust program has identical meaning if each whitespace element is replaced with any other legal whitespace element, such as a single space character.
[lex.token]
## Tokens

[lex.token.syntax]
Lexer
Token →
      IDENTIFIER_OR_KEYWORD
    | RAW_IDENTIFIER
    | CHAR_LITERAL
    | STRING_LITERAL
    | RAW_STRING_LITERAL
    | BYTE_LITERAL
    | BYTE_STRING_LITERAL
    | RAW_BYTE_STRING_LITERAL
    | C_STRING_LITERAL
    | RAW_C_STRING_LITERAL
    | INTEGER_LITERAL
    | FLOAT_LITERAL
    | LIFETIME_TOKEN
    | PUNCTUATION
    | RESERVED_TOKEN

Show syntax diagrams

[lex.token.intro]
Tokens are primitive productions in the grammar defined by regular (non-recursive) languages. Rust source input can be broken down into the following kinds of tokens:
Keywords
Identifiers
Literals
Lifetimes
Punctuation
Delimiters
Within this documentation’s grammar, “simple” tokens are given in string table production form, and appear in monospace font.
[lex.token.literal]
Literals
Literals are tokens used in literal expressions.
Examples
Characters and strings
Example	# sets1	Characters	Escapes
Character	'H'	0	All Unicode	Quote & ASCII & Unicode
String	"hello"	0	All Unicode	Quote & ASCII & Unicode
Raw string	r#"hello"#	<256	All Unicode	N/A
Byte	b'H'	0	All ASCII	Quote & Byte
Byte string	b"hello"	0	All ASCII	Quote & Byte
Raw byte string	br#"hello"#	<256	All ASCII	N/A
C string	c"hello"	0	All Unicode	Quote & Byte & Unicode
Raw C string	cr#"hello"#	<256	All Unicode	N/A
ASCII escapes
Name
\x41	7-bit character code (exactly 2 digits, up to 0x7F)
\n	Newline
\r	Carriage return
\t	Tab
\\	Backslash
\0	Null
Byte escapes
Name
\x7F	8-bit character code (exactly 2 digits)
\n	Newline
\r	Carriage return
\t	Tab
\\	Backslash
\0	Null
Unicode escapes
Name
\u{7FFF}	24-bit Unicode character code (up to 6 digits)
Quote escapes
Name
\'	Single quote
\"	Double quote
Numbers
Number literals2	Example	Exponentiation
Decimal integer	98_222	N/A
Hex integer	0xff	N/A
Octal integer	0o77	N/A
Binary integer	0b1111_0000	N/A
Floating-point	123.0E+77	Optional
[lex.token.literal.suffix]
Suffixes
[lex.token.literal.literal.suffix.intro]
A suffix is a sequence of characters following the primary part of a literal (without intervening whitespace), of the same form as a non-raw identifier or keyword.
[lex.token.literal.suffix.syntax]
Lexer
SUFFIX → IDENTIFIER_OR_KEYWORD

SUFFIX_NO_E → SUFFIXnot beginning with e or E

Show syntax diagrams

[lex.token.literal.suffix.validity]
Any kind of literal (string, integer, etc) with any suffix is valid as a token.
A literal token with any suffix can be passed to a macro without producing an error. The macro itself will decide how to interpret such a token and whether to produce an error or not. In particular, the literal fragment specifier for by-example macros matches literal tokens with arbitrary suffixes.
macro_rules! blackhole { ($tt:tt) => () }
macro_rules! blackhole_lit { ($l:literal) => () }

blackhole!("string"suffix); // OK
blackhole_lit!(1suffix); // OK
[lex.token.literal.suffix.parse]
However, suffixes on literal tokens which are interpreted as literal expressions or patterns are restricted. Any suffixes are rejected on non-numeric literal tokens, and numeric literal tokens are accepted only with suffixes from the list below.
Integer	Floating-point
u8, i8, u16, i16, u32, i32, u64, i64, u128, i128, usize, isize	f32, f64
Character and string literals
[lex.token.literal.char]
Character literals
[lex.token.literal.char.syntax]
Lexer
CHAR_LITERAL →
    '
        ( ~[' \ LF CR TAB] | QUOTE_ESCAPE | ASCII_ESCAPE | UNICODE_ESCAPE )
    ' SUFFIX?

QUOTE_ESCAPE → \' | \"

ASCII_ESCAPE →
      \x OCT_DIGIT HEX_DIGIT
    | \n | \r | \t | \\ | \0

UNICODE_ESCAPE →
    \u{ ( HEX_DIGIT _* )1..6 }

Show syntax diagrams

[lex.token.literal.char.intro]
A character literal is a single Unicode character enclosed within two U+0027 (single-quote) characters, with the exception of U+0027 itself, which must be escaped by a preceding U+005C character (\).
[lex.token.literal.str]
String literals
[lex.token.literal.str.syntax]
Lexer
STRING_LITERAL →
    " (
        ~[" \ CR]
      | QUOTE_ESCAPE
      | ASCII_ESCAPE
      | UNICODE_ESCAPE
      | STRING_CONTINUE
    )* " SUFFIX?

STRING_CONTINUE → \ LF

Show syntax diagrams

[lex.token.literal.str.intro]
A string literal is a sequence of any Unicode characters enclosed within two U+0022 (double-quote) characters, with the exception of U+0022 itself, which must be escaped by a preceding U+005C character (\).
[lex.token.literal.str.linefeed]
Line-breaks, represented by the character U+000A (LF), are allowed in string literals. The character U+000D (CR) may not appear in a string literal. When an unescaped U+005C character (\) occurs immediately before a line break, the line break does not appear in the string represented by the token. See String continuation escapes for details.
[lex.token.literal.char-escape]
Character escapes
[lex.token.literal.char-escape.intro]
Some additional escapes are available in either character or non-raw string literals. An escape starts with a U+005C (\) and continues with one of the following forms:
[lex.token.literal.char-escape.ascii]
A 7-bit code point escape starts with U+0078 (x) and is followed by exactly two hex digits with value up to 0x7F. It denotes the ASCII character with value equal to the provided hex value. Higher values are not permitted because it is ambiguous whether they mean Unicode code points or byte values.
[lex.token.literal.char-escape.unicode]
A 24-bit code point escape starts with U+0075 (u) and is followed by up to six hex digits surrounded by braces U+007B ({) and U+007D (}). It denotes the Unicode code point equal to the provided hex value.
[lex.token.literal.char-escape.whitespace]
A whitespace escape is one of the characters U+006E (n), U+0072 (r), or U+0074 (t), denoting the Unicode values U+000A (LF), U+000D (CR) or U+0009 (HT) respectively.
[lex.token.literal.char-escape.null]
The null escape is the character U+0030 (0) and denotes the Unicode value U+0000 (NUL).
[lex.token.literal.char-escape.slash]
The backslash escape is the character U+005C (\) which must be escaped in order to denote itself.
[lex.token.literal.str-raw]
Raw string literals
[lex.token.literal.str-raw.syntax]
Lexer
RAW_STRING_LITERAL → r RAW_STRING_CONTENT SUFFIX?

RAW_STRING_CONTENT →
      " ( ~CR )* (non-greedy) "
    | # RAW_STRING_CONTENT #

Show syntax diagrams

[lex.token.literal.str-raw.intro]
Raw string literals do not process any escapes. They start with the character U+0072 (r), followed by fewer than 256 of the character U+0023 (#) and a U+0022 (double-quote) character.
[lex.token.literal.str-raw.body]
The raw string body can contain any sequence of Unicode characters other than U+000D (CR). It is terminated only by another U+0022 (double-quote) character, followed by the same number of U+0023 (#) characters that preceded the opening U+0022 (double-quote) character.
[lex.token.literal.str-raw.content]
All Unicode characters contained in the raw string body represent themselves, the characters U+0022 (double-quote) (except when followed by at least as many U+0023 (#) characters as were used to start the raw string literal) or U+005C (\) do not have any special meaning.
Examples for string literals:
"foo"; r"foo";                     // foo
"\"foo\""; r#""foo""#;             // "foo"

"foo #\"# bar";
r##"foo #"# bar"##;                // foo #"# bar

"\x52"; "R"; r"R";                 // R
"\\x52"; r"\x52";                  // \x52
Byte and byte string literals
[lex.token.byte]
Byte literals
[lex.token.byte.syntax]
Lexer
BYTE_LITERAL →
    b' ( ASCII_FOR_CHAR | BYTE_ESCAPE ) ' SUFFIX?

ASCII_FOR_CHAR →
    <any ASCII (i.e. 0x00 to 0x7F) except ', \, LF, CR, or TAB>

BYTE_ESCAPE →
      \x HEX_DIGIT HEX_DIGIT
    | \n | \r | \t | \\ | \0 | \' | \"

Show syntax diagrams

[lex.token.byte.intro]
A byte literal is a single ASCII character (in the U+0000 to U+007F range) or a single escape preceded by the characters U+0062 (b) and U+0027 (single-quote), and followed by the character U+0027. If the character U+0027 is present within the literal, it must be escaped by a preceding U+005C (\) character. It is equivalent to a u8 unsigned 8-bit integer number literal.
[lex.token.str-byte]
Byte string literals
[lex.token.str-byte.syntax]
Lexer
BYTE_STRING_LITERAL →
    b" ( ASCII_FOR_STRING | BYTE_ESCAPE | STRING_CONTINUE )* " SUFFIX?

ASCII_FOR_STRING →
    <any ASCII (i.e 0x00 to 0x7F) except ", \, or CR>

Show syntax diagrams

[lex.token.str-byte.intro]
A non-raw byte string literal is a sequence of ASCII characters and escapes, preceded by the characters U+0062 (b) and U+0022 (double-quote), and followed by the character U+0022. If the character U+0022 is present within the literal, it must be escaped by a preceding U+005C (\) character. Alternatively, a byte string literal can be a raw byte string literal, defined below.
[lex.token.str-byte.linefeed]
Line-breaks, represented by the character U+000A (LF), are allowed in byte string literals. The character U+000D (CR) may not appear in a byte string literal. When an unescaped U+005C character (\) occurs immediately before a line break, the line break does not appear in the string represented by the token. See String continuation escapes for details.
[lex.token.str-byte.escape]
Some additional escapes are available in either byte or non-raw byte string literals. An escape starts with a U+005C (\) and continues with one of the following forms:
[lex.token.str-byte.escape-byte]
A byte escape escape starts with U+0078 (x) and is followed by exactly two hex digits. It denotes the byte equal to the provided hex value.
[lex.token.str-byte.escape-whitespace]
A whitespace escape is one of the characters U+006E (n), U+0072 (r), or U+0074 (t), denoting the bytes values 0x0A (ASCII LF), 0x0D (ASCII CR) or 0x09 (ASCII HT) respectively.
[lex.token.str-byte.escape-null]
The null escape is the character U+0030 (0) and denotes the byte value 0x00 (ASCII NUL).
[lex.token.str-byte.escape-slash]
The backslash escape is the character U+005C (\) which must be escaped in order to denote its ASCII encoding 0x5C.
[lex.token.str-byte-raw]
Raw byte string literals
[lex.token.str-byte-raw.syntax]
Lexer
RAW_BYTE_STRING_LITERAL →
    br RAW_BYTE_STRING_CONTENT SUFFIX?

RAW_BYTE_STRING_CONTENT →
      " ASCII_FOR_RAW* (non-greedy) "
    | # RAW_BYTE_STRING_CONTENT #

ASCII_FOR_RAW →
    <any ASCII (i.e. 0x00 to 0x7F) except CR>

Show syntax diagrams

[lex.token.str-byte-raw.intro]
Raw byte string literals do not process any escapes. They start with the character U+0062 (b), followed by U+0072 (r), followed by fewer than 256 of the character U+0023 (#), and a U+0022 (double-quote) character.
[lex.token.str-byte-raw.body]
The raw string body can contain any sequence of ASCII characters other than U+000D (CR). It is terminated only by another U+0022 (double-quote) character, followed by the same number of U+0023 (#) characters that preceded the opening U+0022 (double-quote) character. A raw byte string literal can not contain any non-ASCII byte.
[lex.token.literal.str-byte-raw.content]
All characters contained in the raw string body represent their ASCII encoding, the characters U+0022 (double-quote) (except when followed by at least as many U+0023 (#) characters as were used to start the raw string literal) or U+005C (\) do not have any special meaning.
Examples for byte string literals:
b"foo"; br"foo";                     // foo
b"\"foo\""; br#""foo""#;             // "foo"

b"foo #\"# bar";
br##"foo #"# bar"##;                 // foo #"# bar

b"\x52"; b"R"; br"R";                // R
b"\\x52"; br"\x52";                  // \x52
C string and raw C string literals
[lex.token.str-c]
C string literals
[lex.token.str-c.syntax]
Lexer
C_STRING_LITERAL →
    c" (
        ~[" \ CR NUL]
      | BYTE_ESCAPEexcept \0 or \x00
      | UNICODE_ESCAPEexcept \u{0}, \u{00}, …, \u{000000}
      | STRING_CONTINUE
    )* " SUFFIX?

Show syntax diagrams

[lex.token.str-c.intro]
A C string literal is a sequence of Unicode characters and escapes, preceded by the characters U+0063 (c) and U+0022 (double-quote), and followed by the character U+0022. If the character U+0022 is present within the literal, it must be escaped by a preceding U+005C (\) character. Alternatively, a C string literal can be a raw C string literal, defined below.
[lex.token.str-c.null]
C strings are implicitly terminated by byte 0x00, so the C string literal c"" is equivalent to manually constructing a &CStr from the byte string literal b"\x00". Other than the implicit terminator, byte 0x00 is not permitted within a C string.
[lex.token.str-c.linefeed]
Line-breaks, represented by the character U+000A (LF), are allowed in C string literals. The character U+000D (CR) may not appear in a C string literal. When an unescaped U+005C character (\) occurs immediately before a line break, the line break does not appear in the string represented by the token. See String continuation escapes for details.
[lex.token.str-c.escape]
Some additional escapes are available in non-raw C string literals. An escape starts with a U+005C (\) and continues with one of the following forms:
[lex.token.str-c.escape-byte]
A byte escape escape starts with U+0078 (x) and is followed by exactly two hex digits. It denotes the byte equal to the provided hex value.
[lex.token.str-c.escape-unicode]
A 24-bit code point escape starts with U+0075 (u) and is followed by up to six hex digits surrounded by braces U+007B ({) and U+007D (}). It denotes the Unicode code point equal to the provided hex value, encoded as UTF-8.
[lex.token.str-c.escape-whitespace]
A whitespace escape is one of the characters U+006E (n), U+0072 (r), or U+0074 (t), denoting the bytes values 0x0A (ASCII LF), 0x0D (ASCII CR) or 0x09 (ASCII HT) respectively.
[lex.token.str-c.escape-slash]
The backslash escape is the character U+005C (\) which must be escaped in order to denote its ASCII encoding 0x5C.
[lex.token.str-c.char-unicode]
A C string represents bytes with no defined encoding, but a C string literal may contain Unicode characters above U+007F. Such characters will be replaced with the bytes of that character’s UTF-8 representation.
The following C string literals are equivalent:
c"æ";        // LATIN SMALL LETTER AE (U+00E6)
c"\u{00E6}";
c"\xC3\xA6";
[lex.token.str-c.edition2021]
2021
Edition differences

C string literals are accepted in the 2021 edition or later. In earlier additions the token c"" is lexed as c "".
[lex.token.str-c-raw]
Raw C string literals
[lex.token.str-c-raw.syntax]
Lexer
RAW_C_STRING_LITERAL →
    cr RAW_C_STRING_CONTENT SUFFIX?

RAW_C_STRING_CONTENT →
      " ( ~[CR NUL] )* (non-greedy) "
    | # RAW_C_STRING_CONTENT #

Show syntax diagrams

[lex.token.str-c-raw.intro]
Raw C string literals do not process any escapes. They start with the character U+0063 (c), followed by U+0072 (r), followed by fewer than 256 of the character U+0023 (#), and a U+0022 (double-quote) character.
[lex.token.str-c-raw.body]
The raw C string body can contain any sequence of Unicode characters other than U+0000 (NUL) and U+000D (CR). It is terminated only by another U+0022 (double-quote) character, followed by the same number of U+0023 (#) characters that preceded the opening U+0022 (double-quote) character.
[lex.token.str-c-raw.content]
All characters contained in the raw C string body represent themselves in UTF-8 encoding. The characters U+0022 (double-quote) (except when followed by at least as many U+0023 (#) characters as were used to start the raw C string literal) or U+005C (\) do not have any special meaning.
[lex.token.str-c-raw.edition2021]
2021
Edition differences

Raw C string literals are accepted in the 2021 edition or later. In earlier additions the token cr"" is lexed as cr "", and cr#""# is lexed as cr #""# (which is non-grammatical).
Examples for C string and raw C string literals
c"foo"; cr"foo";                     // foo
c"\"foo\""; cr#""foo""#;             // "foo"

c"foo #\"# bar";
cr##"foo #"# bar"##;                 // foo #"# bar

c"\x52"; c"R"; cr"R";                // R
c"\\x52"; cr"\x52";                  // \x52
[lex.token.literal.num]
Number literals
A number literal is either an integer literal or a floating-point literal. The grammar for recognizing the two kinds of literals is mixed.
[lex.token.literal.int]
Integer literals
[lex.token.literal.int.syntax]
Lexer
INTEGER_LITERAL →
    ( DEC_LITERAL | BIN_LITERAL | OCT_LITERAL | HEX_LITERAL ) SUFFIX_NO_E?

DEC_LITERAL → DEC_DIGIT ( DEC_DIGIT | _ )*

BIN_LITERAL → 0b ( BIN_DIGIT | _ )* BIN_DIGIT ( BIN_DIGIT | _ )*

OCT_LITERAL → 0o ( OCT_DIGIT | _ )* OCT_DIGIT ( OCT_DIGIT | _ )*

HEX_LITERAL → 0x ( HEX_DIGIT | _ )* HEX_DIGIT ( HEX_DIGIT | _ )*

BIN_DIGIT → [0-1]

OCT_DIGIT → [0-7]

DEC_DIGIT → [0-9]

HEX_DIGIT → [0-9 a-f A-F]

Show syntax diagrams

[lex.token.literal.int.kind]
An integer literal has one of four forms:
[lex.token.literal.int.kind-dec]
A decimal literal starts with a decimal digit and continues with any mixture of decimal digits and underscores.
[lex.token.literal.int.kind-hex]
A hex literal starts with the character sequence U+0030 U+0078 (0x) and continues as any mixture (with at least one digit) of hex digits and underscores.
[lex.token.literal.int.kind-oct]
An octal literal starts with the character sequence U+0030 U+006F (0o) and continues as any mixture (with at least one digit) of octal digits and underscores.
[lex.token.literal.int.kind-bin]
A binary literal starts with the character sequence U+0030 U+0062 (0b) and continues as any mixture (with at least one digit) of binary digits and underscores.
[lex.token.literal.int.restriction]
Like any literal, an integer literal may be followed (immediately, without any spaces) by a suffix as described above. The suffix may not begin with e or E, as that would be interpreted as the exponent of a floating-point literal. See Integer literal expressions for the effect of these suffixes.
Examples of integer literals which are accepted as literal expressions:
123;
123i32;
123u32;
123_u32;

0xff;
0xff_u8;
0x01_f32; // integer 7986, not floating-point 1.0
0x01_e3;  // integer 483, not floating-point 1000.0

0o70;
0o70_i16;

0b1111_1111_1001_0000;
0b1111_1111_1001_0000i64;
0b________1;

0usize;

// These are too big for their type, but are accepted as literal expressions.
128_i8;
256_u8;

// This is an integer literal, accepted as a floating-point literal expression.
5f32;
Note that -1i8, for example, is analyzed as two tokens: - followed by 1i8.
Examples of integer literals which are not accepted as literal expressions:
0invalidSuffix;
123AFB43;
0b010a;
0xAB_CD_EF_GH;
0b1111_f32;
[lex.token.literal.int.tuple-field]
Tuple index
[lex.token.literal.int.tuple-field.syntax]
Lexer
TUPLE_INDEX → INTEGER_LITERAL

Show syntax diagrams

[lex.token.literal.int.tuple-field.intro]
A tuple index is used to refer to the fields of tuples, tuple structs, and tuple variants.
[lex.token.literal.int.tuple-field.eq]
Tuple indices are compared with the literal token directly. Tuple indices start with 0 and each successive index increments the value by 1 as a decimal value. Thus, only decimal values will match, and the value must not have any extra 0 prefix characters.
let example = ("dog", "cat", "horse");
let dog = example.0;
let cat = example.1;
// The following examples are invalid.
let cat = example.01;  // ERROR no field named `01`
let horse = example.0b10;  // ERROR no field named `0b10`
Note

Tuple indices may include certain suffixes, but this is not intended to be valid, and may be removed in a future version. See https://github.com/rust-lang/rust/issues/60210 for more information.
[lex.token.literal.float]
Floating-point literals
[lex.token.literal.float.syntax]
Lexer
FLOAT_LITERAL →
      DEC_LITERAL .not immediately followed by ., _ or an XID_Start character
    | DEC_LITERAL . DEC_LITERAL SUFFIX_NO_E?
    | DEC_LITERAL ( . DEC_LITERAL )? FLOAT_EXPONENT SUFFIX?

FLOAT_EXPONENT →
    ( e | E ) ( + | - )? ( DEC_DIGIT | _ )* DEC_DIGIT ( DEC_DIGIT | _ )*

Show syntax diagrams

[lex.token.literal.float.form]
A floating-point literal has one of two forms:
A decimal literal followed by a period character U+002E (.). This is optionally followed by another decimal literal, with an optional exponent.
A single decimal literal followed by an exponent.
[lex.token.literal.float.suffix]
Like integer literals, a floating-point literal may be followed by a suffix, so long as the pre-suffix part does not end with U+002E (.). The suffix may not begin with e or E if the literal does not include an exponent. See Floating-point literal expressions for the effect of these suffixes.
Examples of floating-point literals which are accepted as literal expressions:
123.0f64;
0.1f64;
0.1f32;
12E+99_f64;
let x: f64 = 2.;
This last example is different because it is not possible to use the suffix syntax with a floating point literal end.token.ing in a period. 2.f64 would attempt to call a method named f64 on 2.
Note that -1.0, for example, is analyzed as two tokens: - followed by 1.0.
Examples of floating-point literals which are not accepted as literal expressions:
2.0f80;
2e5f80;
2e5e6;
2.0e5e6;
1.3e10u64;
[lex.token.literal.reserved]
Reserved forms similar to number literals
[lex.token.literal.reserved.syntax]
Lexer
RESERVED_NUMBER →
      BIN_LITERAL [2-9]
    | OCT_LITERAL [8-9]
    | ( BIN_LITERAL | OCT_LITERAL | HEX_LITERAL ) .not immediately followed by ., _ or an XID_Start character
    | ( BIN_LITERAL | OCT_LITERAL ) ( e | E )
    | 0b _* <end of input or not BIN_DIGIT>
    | 0o _* <end of input or not OCT_DIGIT>
    | 0x _* <end of input or not HEX_DIGIT>
    | DEC_LITERAL ( . DEC_LITERAL )? ( e | E ) ( + | - )? <end of input or not DEC_DIGIT>

Show syntax diagrams

[lex.token.literal.reserved.intro]
The following lexical forms similar to number literals are reserved forms. Due to the possible ambiguity these raise, they are rejected by the tokenizer instead of being interpreted as separate tokens.
[lex.token.literal.reserved.out-of-range]
An unsuffixed binary or octal literal followed, without intervening whitespace, by a decimal digit out of the range for its radix.
[lex.token.literal.reserved.period]
An unsuffixed binary, octal, or hexadecimal literal followed, without intervening whitespace, by a period character (with the same restrictions on what follows the period as for floating-point literals).
[lex.token.literal.reserved.exp]
An unsuffixed binary or octal literal followed, without intervening whitespace, by the character e or E.
[lex.token.literal.reserved.empty-with-radix]
Input which begins with one of the radix prefixes but is not a valid binary, octal, or hexadecimal literal (because it contains no digits).
[lex.token.literal.reserved.empty-exp]
Input which has the form of a floating-point literal with no digits in the exponent.
Examples of reserved forms:
0b0102;  // this is not `0b010` followed by `2`
0o1279;  // this is not `0o127` followed by `9`
0x80.0;  // this is not `0x80` followed by `.` and `0`
0b101e;  // this is not a suffixed literal, or `0b101` followed by `e`
0b;      // this is not an integer literal, or `0` followed by `b`
0b_;     // this is not an integer literal, or `0` followed by `b_`
2e;      // this is not a floating-point literal, or `2` followed by `e`
2.0e;    // this is not a floating-point literal, or `2.0` followed by `e`
2em;     // this is not a suffixed literal, or `2` followed by `em`
2.0em;   // this is not a suffixed literal, or `2.0` followed by `em`
[lex.token.life]
Lifetimes and loop labels
[lex.token.life.syntax]
Lexer
LIFETIME_TOKEN →
      ' IDENTIFIER_OR_KEYWORDnot immediately followed by '
    | '_not immediately followed by '
    | RAW_LIFETIME

LIFETIME_OR_LABEL →
      ' NON_KEYWORD_IDENTIFIERnot immediately followed by '
    | RAW_LIFETIME

RAW_LIFETIME →
    'r# IDENTIFIER_OR_KEYWORDexcept crate, self, super, Self and not immediately followed by '

RESERVED_RAW_LIFETIME → 'r#_not immediately followed by '

Show syntax diagrams

[lex.token.life.intro]
Lifetime parameters and loop labels use LIFETIME_OR_LABEL tokens. Any LIFETIME_TOKEN will be accepted by the lexer, and for example, can be used in macros.
[lex.token.life.raw.intro]
A raw lifetime is like a normal lifetime, but its identifier is prefixed by r#. (Note that the r# prefix is not included as part of the actual lifetime.)
[lex.token.life.raw.allowed]
Unlike a normal lifetime, a raw lifetime may be any strict or reserved keyword except the ones listed above for RAW_LIFETIME.
[lex.token.life.raw.reserved]
It is an error to use the RESERVED_RAW_LIFETIME token 'r#_ in order to avoid confusion with the placeholder lifetime.
[lex.token.life.raw.edition2021]
2021
Edition differences

Raw lifetimes are accepted in the 2021 edition or later. In earlier additions the token 'r#lt is lexed as 'r # lt.
[lex.token.punct]
Punctuation
[lex.token.punct.syntax]
Lexer
PUNCTUATION →
      =
    | <
    | <=
    | ==
    | !=
    | >=
    | >
    | &&
    | ||
    | !
    | ~
    | +
    | -
    | *
    | /
    | %
    | ^
    | &
    | |
    | <<
    | >>
    | +=
    | -=
    | *=
    | /=
    | %=
    | ^=
    | &=
    | |=
    | <<=
    | >>=
    | @
    | .
    | ..
    | ...
    | ..=
    | ,
    | ;
    | :
    | ::
    | ->
    | <-
    | =>
    | #
    | $
    | ?
    | _
    | {
    | }
    | [
    | ]
    | (
    | )

Show syntax diagrams

[lex.token.punct.intro]
Punctuation symbol tokens are listed here for completeness. Their individual usages and meanings are defined in the linked pages.
Symbol	Name	Usage
+	Plus	Addition, Trait Bounds, Macro Kleene Matcher
-	Minus	Subtraction, Negation
*	Star	Multiplication, Dereference, Raw Pointers, Macro Kleene Matcher, Use wildcards
/	Slash	Division
%	Percent	Remainder
^	Caret	Bitwise and Logical XOR
!	Not	Bitwise and Logical NOT, Macro Calls, Inner Attributes, Never Type, Negative impls
&	And	Bitwise and Logical AND, Borrow, References, Reference patterns
|	Or	Bitwise and Logical OR, Closures, Patterns in match, if let, and while let
&&	AndAnd	Lazy AND, Borrow, References, Reference patterns
||	OrOr	Lazy OR, Closures
<<	Shl	Shift Left, Nested Generics
>>	Shr	Shift Right, Nested Generics
+=	PlusEq	Addition assignment
-=	MinusEq	Subtraction assignment
*=	StarEq	Multiplication assignment
/=	SlashEq	Division assignment
%=	PercentEq	Remainder assignment
^=	CaretEq	Bitwise XOR assignment
&=	AndEq	Bitwise And assignment
|=	OrEq	Bitwise Or assignment
<<=	ShlEq	Shift Left assignment
>>=	ShrEq	Shift Right assignment, Nested Generics
=	Eq	Assignment, Attributes, Various type definitions
==	EqEq	Equal
!=	Ne	Not Equal
>	Gt	Greater than, Generics, Paths
<	Lt	Less than, Generics, Paths
>=	Ge	Greater than or equal to, Generics
<=	Le	Less than or equal to
@	At	Subpattern binding
_	Underscore	Wildcard patterns, Inferred types, Unnamed items in constants, extern crates, use declarations, and destructuring assignment
.	Dot	Field access, Tuple index
..	DotDot	Range, Struct expressions, Patterns, Range Patterns
...	DotDotDot	Variadic functions, Range patterns
..=	DotDotEq	Inclusive Range, Range patterns
,	Comma	Various separators
;	Semi	Terminator for various items and statements, Array types
:	Colon	Various separators
::	PathSep	Path separator
->	RArrow	Function return type, Closure return type, Function pointer type
=>	FatArrow	Match arms, Macros
<-	LArrow	The left arrow symbol has been unused since before Rust 1.0, but it is still treated as a single token
#	Pound	Attributes
$	Dollar	Macros
?	Question	Try propagation expressions, Questionably sized, Macro Kleene Matcher
~	Tilde	The tilde operator has been unused since before Rust 1.0, but its token may still be used
[lex.token.delim]
Delimiters
Bracket punctuation is used in various parts of the grammar. An open bracket must always be paired with a close bracket. Brackets and the tokens within them are referred to as “token trees” in macros. The three types of brackets are:
Bracket	Type
{ }	Curly braces
[ ]	Square brackets
( )	Parentheses
[lex.token.reserved]
Reserved tokens
[lex.token.reserved.intro]
Several token forms are reserved for future use. It is an error for the source input to match one of these forms.
[lex.token.reserved.syntax]
Lexer
RESERVED_TOKEN →
      RESERVED_GUARDED_STRING_LITERAL
    | RESERVED_NUMBER
    | RESERVED_POUNDS
    | RESERVED_RAW_IDENTIFIER
    | RESERVED_RAW_LIFETIME
    | RESERVED_TOKEN_DOUBLE_QUOTE
    | RESERVED_TOKEN_LIFETIME
    | RESERVED_TOKEN_POUND
    | RESERVED_TOKEN_SINGLE_QUOTE

Show syntax diagrams

[lex.token.reserved-prefix]
Reserved prefixes
[lex.token.reserved-prefix.syntax]
Lexer
RESERVED_TOKEN_DOUBLE_QUOTE →
    ( IDENTIFIER_OR_KEYWORDexcept b or c or r or br or cr | _ ) "

RESERVED_TOKEN_SINGLE_QUOTE →
    ( IDENTIFIER_OR_KEYWORDexcept b | _ ) '

RESERVED_TOKEN_POUND →
    ( IDENTIFIER_OR_KEYWORDexcept r or br or cr | _ ) #

RESERVED_TOKEN_LIFETIME →
    ' ( IDENTIFIER_OR_KEYWORDexcept r | _ ) #

Show syntax diagrams

[lex.token.reserved-prefix.intro]
Some lexical forms known as reserved prefixes are reserved for future use.
[lex.token.reserved-prefix.id]
Source input which would otherwise be lexically interpreted as a non-raw identifier (or a keyword or _) which is immediately followed by a #, ', or " character (without intervening whitespace) is identified as a reserved prefix.
[lex.token.reserved-prefix.raw-token]
Note that raw identifiers, raw string literals, and raw byte string literals may contain a # character but are not interpreted as containing a reserved prefix.
[lex.token.reserved-prefix.strings]
Similarly the r, b, br, c, and cr prefixes used in raw string literals, byte literals, byte string literals, raw byte string literals, C string literals, and raw C string literals are not interpreted as reserved prefixes.
[lex.token.reserved-prefix.life]
Source input which would otherwise be lexically interpreted as a non-raw lifetime (or a keyword or _) which is immediately followed by a # character (without intervening whitespace) is identified as a reserved lifetime prefix.
[lex.token.reserved-prefix.edition2021]
2021
Edition differences

Starting with the 2021 edition, reserved prefixes are reported as an error by the lexer (in particular, they cannot be passed to macros).

Before the 2021 edition, reserved prefixes are accepted by the lexer and interpreted as multiple tokens (for example, one token for the identifier or keyword, followed by a # token).

Examples accepted in all editions:

macro_rules! lexes {($($_:tt)*) => {}}
lexes!{a #foo}
lexes!{continue 'foo}
lexes!{match "..." {}}
lexes!{r#let#foo}         // three tokens: r#let # foo
lexes!{'prefix #lt}
Examples accepted before the 2021 edition but rejected later:

macro_rules! lexes {($($_:tt)*) => {}}
lexes!{a#foo}
lexes!{continue'foo}
lexes!{match"..." {}}
lexes!{'prefix#lt}
[lex.token.reserved-guards]
Reserved guards
[lex.token.reserved-guards.syntax]
Lexer
RESERVED_GUARDED_STRING_LITERAL → #+ STRING_LITERAL

RESERVED_POUNDS → #2..

Show syntax diagrams

[lex.token.reserved-guards.intro]
The reserved guards are syntax reserved for future use, and will generate a compile error if used.
[lex.token.reserved-guards.string-literal]
The reserved guarded string literal is a token of one or more U+0023 (#) immediately followed by a STRING_LITERAL.
[lex.token.reserved-guards.pounds]
The reserved pounds is a token of two or more U+0023 (#).
[lex.token.reserved-guards.edition2024]
2024
Edition differences

Before the 2024 edition, reserved guards are accepted by the lexer and interpreted as multiple tokens. For example, the #"foo"# form is interpreted as three tokens. ## is interpreted as two tokens.
The number of #s on each side of the same literal must be equivalent. ↩

All number literals allow _ as a visual separator: 1_234.0E+18f64 ↩

[macro]
