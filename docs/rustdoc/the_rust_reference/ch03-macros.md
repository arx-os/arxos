# Macros
[macro.intro]
The functionality and syntax of Rust can be extended with custom definitions called macros. They are given names, and invoked through a consistent syntax: some_extension!(...).
There are two ways to define new macros:
Macros by Example define new syntax in a higher-level, declarative way.
Procedural Macros define function-like macros, custom derives, and custom attributes using functions that operate on input tokens.
[macro.invocation]
Macro Invocation
[macro.invocation.syntax]
Syntax
MacroInvocation →
    SimplePath ! DelimTokenTree

DelimTokenTree →
      ( TokenTree* )
    | [ TokenTree* ]
    | { TokenTree* }

TokenTree →
    Tokenexcept delimiters | DelimTokenTree

MacroInvocationSemi →
      SimplePath ! ( TokenTree* ) ;
    | SimplePath ! [ TokenTree* ] ;
    | SimplePath ! { TokenTree* }

Show syntax diagrams

[macro.invocation.intro]
A macro invocation expands a macro at compile time and replaces the invocation with the result of the macro. Macros may be invoked in the following situations:
[macro.invocation.expr]
Expressions and statements
[macro.invocation.pattern]
Patterns
[macro.invocation.type]
Types
[macro.invocation.item]
Items including associated items
[macro.invocation.nested]
macro_rules transcribers
[macro.invocation.extern]
External blocks
[macro.invocation.item-statement]
When used as an item or a statement, the MacroInvocationSemi form is used where a semicolon is required at the end when not using curly braces. Visibility qualifiers are never allowed before a macro invocation or macro_rules definition.
// Used as an expression.
let x = vec![1,2,3];

// Used as a statement.
println!("Hello!");

// Used in a pattern.
macro_rules! pat {
    ($i:ident) => (Some($i))
}

if let pat!(x) = Some(1) {
    assert_eq!(x, 1);
}

// Used in a type.
macro_rules! Tuple {
    { $A:ty, $B:ty } => { ($A, $B) };
}

type N2 = Tuple!(i32, i32);

// Used as an item.
thread_local!(static FOO: RefCell<u32> = RefCell::new(1));

// Used as an associated item.
macro_rules! const_maker {
    ($t:ty, $v:tt) => { const CONST: $t = $v; };
}
trait T {
    const_maker!{i32, 7}
}

// Macro calls within macros.
macro_rules! example {
    () => { println!("Macro call in a macro!") };
}
// Outer macro `example` is expanded, then inner macro `println` is expanded.
example!();
[macro.decl]
## Macros By Example

[macro.decl.syntax]
Syntax
MacroRulesDefinition →
    macro_rules ! IDENTIFIER MacroRulesDef

MacroRulesDef →
      ( MacroRules ) ;
    | [ MacroRules ] ;
    | { MacroRules }

MacroRules →
    MacroRule ( ; MacroRule )* ;?

MacroRule →
    MacroMatcher => MacroTranscriber

MacroMatcher →
      ( MacroMatch* )
    | [ MacroMatch* ]
    | { MacroMatch* }

MacroMatch →
      Tokenexcept $ and delimiters
    | MacroMatcher
    | $ ( IDENTIFIER_OR_KEYWORDexcept crate | RAW_IDENTIFIER | _ ) : MacroFragSpec
    | $ ( MacroMatch+ ) MacroRepSep? MacroRepOp

MacroFragSpec →
      block | expr | expr_2021 | ident | item | lifetime | literal
    | meta | pat | pat_param | path | stmt | tt | ty | vis

MacroRepSep → Tokenexcept delimiters and MacroRepOp

MacroRepOp → * | + | ?

MacroTranscriber → DelimTokenTree

Show syntax diagrams

[macro.decl.intro]
macro_rules allows users to define syntax extension in a declarative way. We call such extensions “macros by example” or simply “macros”.
Each macro by example has a name, and one or more rules. Each rule has two parts: a matcher, describing the syntax that it matches, and a transcriber, describing the syntax that will replace a successfully matched invocation. Both the matcher and the transcriber must be surrounded by delimiters. Macros can expand to expressions, statements, items (including traits, impls, and foreign items), types, or patterns.
[macro.decl.transcription]
Transcribing
[macro.decl.transcription.intro]
When a macro is invoked, the macro expander looks up macro invocations by name, and tries each macro rule in turn. It transcribes the first successful match; if this results in an error, then future matches are not tried.
[macro.decl.transcription.lookahead]
When matching, no lookahead is performed; if the compiler cannot unambiguously determine how to parse the macro invocation one token at a time, then it is an error. In the following example, the compiler does not look ahead past the identifier to see if the following token is a ), even though that would allow it to parse the invocation unambiguously:
macro_rules! ambiguity {
    ($($i:ident)* $j:ident) => { };
}

ambiguity!(error); // Error: local ambiguity
[macro.decl.transcription.syntax]
In both the matcher and the transcriber, the $ token is used to invoke special behaviours from the macro engine (described below in Metavariables and Repetitions). Tokens that aren’t part of such an invocation are matched and transcribed literally, with one exception. The exception is that the outer delimiters for the matcher will match any pair of delimiters. Thus, for instance, the matcher (()) will match {()} but not {{}}. The character $ cannot be matched or transcribed literally.
[macro.decl.transcription.fragment]
Forwarding a matched fragment
When forwarding a matched fragment to another macro-by-example, matchers in the second macro will see an opaque AST of the fragment type. The second macro can’t use literal tokens to match the fragments in the matcher, only a fragment specifier of the same type. The ident, lifetime, and tt fragment types are an exception, and can be matched by literal tokens. The following illustrates this restriction:
macro_rules! foo {
    ($l:expr) => { bar!($l); }
// ERROR:               ^^ no rules expected this token in macro call
}

macro_rules! bar {
    (3) => {}
}

foo!(3);
The following illustrates how tokens can be directly matched after matching a tt fragment:
// compiles OK
macro_rules! foo {
    ($l:tt) => { bar!($l); }
}

macro_rules! bar {
    (3) => {}
}

foo!(3);
[macro.decl.meta]
Metavariables
[macro.decl.meta.intro]
In the matcher, $ name : fragment-specifier matches a Rust syntax fragment of the kind specified and binds it to the metavariable $name.
[macro.decl.meta.specifier]
Valid fragment specifiers are:
block: a BlockExpression
expr: an Expression
expr_2021: an Expression except UnderscoreExpression and ConstBlockExpression (see macro.decl.meta.edition2024)
ident: an IDENTIFIER_OR_KEYWORD, RAW_IDENTIFIER, or $crate
item: an Item
lifetime: a LIFETIME_TOKEN
literal: matches -?LiteralExpression
meta: an Attr, the contents of an attribute
pat: a Pattern (see macro.decl.meta.edition2021)
pat_param: a PatternNoTopAlt
path: a TypePath style path
stmt: a Statement without the trailing semicolon (except for item statements that require semicolons)
tt: a TokenTree (a single token or tokens in matching delimiters (), [], or {})
ty: a Type
vis: a possibly empty Visibility qualifier
[macro.decl.meta.transcription]
In the transcriber, metavariables are referred to simply by $name, since the fragment kind is specified in the matcher. Metavariables are replaced with the syntax element that matched them. Metavariables can be transcribed more than once or not at all.
[macro.decl.meta.dollar-crate]
The keyword metavariable $crate can be used to refer to the current crate.
[macro.decl.meta.edition2021]
2021
Edition differences

Starting with the 2021 edition, pat fragment-specifiers match top-level or-patterns (that is, they accept Pattern).

Before the 2021 edition, they match exactly the same fragments as pat_param (that is, they accept PatternNoTopAlt).

The relevant edition is the one in effect for the macro_rules! definition.
[macro.decl.meta.edition2024]
2024
Edition differences

Before the 2024 edition, expr fragment specifiers do not match UnderscoreExpression or ConstBlockExpression at the top level. They are allowed within subexpressions.

The expr_2021 fragment specifier exists to maintain backwards compatibility with editions before 2024.
[macro.decl.repetition]
Repetitions
[macro.decl.repetition.intro]
In both the matcher and transcriber, repetitions are indicated by placing the tokens to be repeated inside $(…), followed by a repetition operator, optionally with a separator token between.
[macro.decl.repetition.separator]
The separator token can be any token other than a delimiter or one of the repetition operators, but ; and , are the most common. For instance, $( $i:ident ),* represents any number of identifiers separated by commas. Nested repetitions are permitted.
[macro.decl.repetition.operators]
The repetition operators are:
* — indicates any number of repetitions.
+ — indicates any number but at least one.
? — indicates an optional fragment with zero or one occurrence.
[macro.decl.repetition.optional-restriction]
Since ? represents at most one occurrence, it cannot be used with a separator.
[macro.decl.repetition.fragment]
The repeated fragment both matches and transcribes to the specified number of the fragment, separated by the separator token. Metavariables are matched to every repetition of their corresponding fragment. For instance, the $( $i:ident ),* example above matches $i to all of the identifiers in the list.
During transcription, additional restrictions apply to repetitions so that the compiler knows how to expand them properly:
A metavariable must appear in exactly the same number, kind, and nesting order of repetitions in the transcriber as it did in the matcher. So for the matcher $( $i:ident ),*, the transcribers => { $i }, => { $( $( $i)* )* }, and => { $( $i )+ } are all illegal, but => { $( $i );* } is correct and replaces a comma-separated list of identifiers with a semicolon-separated list.
Each repetition in the transcriber must contain at least one metavariable to decide how many times to expand it. If multiple metavariables appear in the same repetition, they must be bound to the same number of fragments. For instance, ( $( $i:ident ),* ; $( $j:ident ),* ) => (( $( ($i,$j) ),* )) must bind the same number of $i fragments as $j fragments. This means that invoking the macro with (a, b, c; d, e, f) is legal and expands to ((a,d), (b,e), (c,f)), but (a, b, c; d, e) is illegal because it does not have the same number. This requirement applies to every layer of nested repetitions.
[macro.decl.scope]
Scoping, Exporting, and Importing
[macro.decl.scope.intro]
For historical reasons, the scoping of macros by example does not work entirely like items. Macros have two forms of scope: textual scope, and path-based scope. Textual scope is based on the order that things appear in source files, or even across multiple files, and is the default scoping. It is explained further below. Path-based scope works exactly the same way that item scoping does. The scoping, exporting, and importing of macros is controlled largely by attributes.
[macro.decl.scope.unqualified]
When a macro is invoked by an unqualified identifier (not part of a multi-part path), it is first looked up in textual scoping. If this does not yield any results, then it is looked up in path-based scoping. If the macro’s name is qualified with a path, then it is only looked up in path-based scoping.
use lazy_static::lazy_static; // Path-based import.

macro_rules! lazy_static { // Textual definition.
    (lazy) => {};
}

lazy_static!{lazy} // Textual lookup finds our macro first.
self::lazy_static!{} // Path-based lookup ignores our macro, finds imported one.
[macro.decl.scope.textual]
Textual Scope
[macro.decl.scope.textual.intro]
Textual scope is based largely on the order that things appear in source files, and works similarly to the scope of local variables declared with let except it also applies at the module level. When macro_rules! is used to define a macro, the macro enters the scope after the definition (note that it can still be used recursively, since names are looked up from the invocation site), up until its surrounding scope, typically a module, is closed. This can enter child modules and even span across multiple files:
//// src/lib.rs
mod has_macro {
    // m!{} // Error: m is not in scope.

    macro_rules! m {
        () => {};
    }
    m!{} // OK: appears after declaration of m.

    mod uses_macro;
}

// m!{} // Error: m is not in scope.

//// src/has_macro/uses_macro.rs

m!{} // OK: appears after declaration of m in src/lib.rs
[macro.decl.scope.textual.shadow]
It is not an error to define a macro multiple times; the most recent declaration will shadow the previous one unless it has gone out of scope.
macro_rules! m {
    (1) => {};
}

m!(1);

mod inner {
    m!(1);

    macro_rules! m {
        (2) => {};
    }
    // m!(1); // Error: no rule matches '1'
    m!(2);

    macro_rules! m {
        (3) => {};
    }
    m!(3);
}

m!(1);
Macros can be declared and used locally inside functions as well, and work similarly:
fn foo() {
    // m!(); // Error: m is not in scope.
    macro_rules! m {
        () => {};
    }
    m!();
}

// m!(); // Error: m is not in scope.
[macro.decl.scope.macro_use]
The macro_use attribute
[macro.decl.scope.macro_use.mod-decl]
The macro_use attribute has two purposes. First, it can be used to make a module’s macro scope not end when the module is closed, by applying it to a module:
#[macro_use]
mod inner {
    macro_rules! m {
        () => {};
    }
}

m!();
[macro.decl.scope.macro_use.prelude]
Second, it can be used to import macros from another crate, by attaching it to an extern crate declaration appearing in the crate’s root module. Macros imported this way are imported into the macro_use prelude, not textually, which means that they can be shadowed by any other name. While macros imported by #[macro_use] can be used before the import statement, in case of a conflict, the last macro imported wins. Optionally, a list of macros to import can be specified using the MetaListIdents syntax; this is not supported when #[macro_use] is applied to a module.
#[macro_use(lazy_static)] // Or #[macro_use] to import all macros.
extern crate lazy_static;

lazy_static!{}
// self::lazy_static!{} // Error: lazy_static is not defined in `self`
[macro.decl.scope.macro_use.export]
Macros to be imported with #[macro_use] must be exported with #[macro_export], which is described below.
[macro.decl.scope.path]
Path-Based Scope
[macro.decl.scope.path.intro]
By default, a macro has no path-based scope. However, if it has the #[macro_export] attribute, then it is declared in the crate root scope and can be referred to normally as such:
self::m!();
m!(); // OK: Path-based lookup finds m in the current module.

mod inner {
    super::m!();
    crate::m!();
}

mod mac {
    #[macro_export]
    macro_rules! m {
        () => {};
    }
}
[macro.decl.scope.path.export]
Macros labeled with #[macro_export] are always pub and can be referred to by other crates, either by path or by #[macro_use] as described above.
[macro.decl.hygiene]
Hygiene
[macro.decl.hygiene.intro]
Macros by example have mixed-site hygiene. This means that loop labels, block labels, and local variables are looked up at the macro definition site while other symbols are looked up at the macro invocation site. For example:
let x = 1;
fn func() {
    unreachable!("this is never called")
}

macro_rules! check {
    () => {
        assert_eq!(x, 1); // Uses `x` from the definition site.
        func();           // Uses `func` from the invocation site.
    };
}

{
    let x = 2;
    fn func() { /* does not panic */ }
    check!();
}
Labels and local variables defined in macro expansion are not shared between invocations, so this code doesn’t compile:
macro_rules! m {
    (define) => {
        let x = 1;
    };
    (refer) => {
        dbg!(x);
    };
}

m!(define);
m!(refer);
[macro.decl.hygiene.crate]
A special case is the $crate metavariable. It refers to the crate defining the macro, and can be used at the start of the path to look up items or macros which are not in scope at the invocation site.
//// Definitions in the `helper_macro` crate.
#[macro_export]
macro_rules! helped {
    // () => { helper!() } // This might lead to an error due to 'helper' not being in scope.
    () => { $crate::helper!() }
}

#[macro_export]
macro_rules! helper {
    () => { () }
}

//// Usage in another crate.
// Note that `helper_macro::helper` is not imported!
use helper_macro::helped;

fn unit() {
    helped!();
}
Note that, because $crate refers to the current crate, it must be used with a fully qualified module path when referring to non-macro items:
pub mod inner {
    #[macro_export]
    macro_rules! call_foo {
        () => { $crate::inner::foo() };
    }

    pub fn foo() {}
}
[macro.decl.hygiene.vis]
Additionally, even though $crate allows a macro to refer to items within its own crate when expanding, its use has no effect on visibility. An item or macro referred to must still be visible from the invocation site. In the following example, any attempt to invoke call_foo!() from outside its crate will fail because foo() is not public.
#[macro_export]
macro_rules! call_foo {
    () => { $crate::foo() };
}

fn foo() {}
Version differences: Prior to Rust 1.30, $crate and local_inner_macros (below) were unsupported. They were added alongside path-based imports of macros (described above), to ensure that helper macros did not need to be manually imported by users of a macro-exporting crate. Crates written for earlier versions of Rust that use helper macros need to be modified to use $crate or local_inner_macros to work well with path-based imports.

[macro.decl.hygiene.local_inner_macros]
When a macro is exported, the #[macro_export] attribute can have the local_inner_macros keyword added to automatically prefix all contained macro invocations with $crate::. This is intended primarily as a tool to migrate code written before $crate was added to the language to work with Rust 2018’s path-based imports of macros. Its use is discouraged in new code.
#[macro_export(local_inner_macros)]
macro_rules! helped {
    () => { helper!() } // Automatically converted to $crate::helper!().
}

#[macro_export]
macro_rules! helper {
    () => { () }
}
[macro.decl.follow-set]
Follow-set Ambiguity Restrictions
[macro.decl.follow-set.intro]
The parser used by the macro system is reasonably powerful, but it is limited in order to prevent ambiguity in current or future versions of the language.
[macro.decl.follow-set.token-restriction]
In particular, in addition to the rule about ambiguous expansions, a nonterminal matched by a metavariable must be followed by a token which has been decided can be safely used after that kind of match.
As an example, a macro matcher like $i:expr [ , ] could in theory be accepted in Rust today, since [,] cannot be part of a legal expression and therefore the parse would always be unambiguous. However, because [ can start trailing expressions, [ is not a character which can safely be ruled out as coming after an expression. If [,] were accepted in a later version of Rust, this matcher would become ambiguous or would misparse, breaking working code. Matchers like $i:expr, or $i:expr; would be legal, however, because , and ; are legal expression separators. The specific rules are:
[macro.decl.follow-set.token-expr-stmt]
expr and stmt may only be followed by one of: =>, ,, or ;.
[macro.decl.follow-set.token-pat_param]
pat_param may only be followed by one of: =>, ,, =, |, if, or in.
[macro.decl.follow-set.token-pat]
pat may only be followed by one of: =>, ,, =, if, or in.
[macro.decl.follow-set.token-path-ty]
path and ty may only be followed by one of: =>, ,, =, |, ;, :, >, >>, [, {, as, where, or a macro variable of block fragment specifier.
[macro.decl.follow-set.token-vis]
vis may only be followed by one of: ,, an identifier other than a non-raw priv, any token that can begin a type, or a metavariable with a ident, ty, or path fragment specifier.
[macro.decl.follow-set.token-other]
All other fragment specifiers have no restrictions.
[macro.decl.follow-set.edition2021]
2021
Edition differences

Before the 2021 edition, pat may also be followed by |.
[macro.decl.follow-set.repetition]
When repetitions are involved, then the rules apply to every possible number of expansions, taking separators into account. This means:
If the repetition includes a separator, that separator must be able to follow the contents of the repetition.
If the repetition can repeat multiple times (* or +), then the contents must be able to follow themselves.
The contents of the repetition must be able to follow whatever comes before, and whatever comes after must be able to follow the contents of the repetition.
If the repetition can match zero times (* or ?), then whatever comes after must be able to follow whatever comes before.
For more detail, see the formal specification.
[macro.proc]
## Procedural Macros

[macro.proc.intro]
Procedural macros allow creating syntax extensions as execution of a function. Procedural macros come in one of three flavors:
Function-like macros - custom!(...)
Derive macros - #[derive(CustomDerive)]
Attribute macros - #[CustomAttribute]
Procedural macros allow you to run code at compile time that operates over Rust syntax, both consuming and producing Rust syntax. You can sort of think of procedural macros as functions from an AST to another AST.
[macro.proc.def]
Procedural macros must be defined in the root of a crate with the crate type of proc-macro. The macros may not be used from the crate where they are defined, and can only be used when imported in another crate.
Note

When using Cargo, Procedural macro crates are defined with the proc-macro key in your manifest:

[lib]
proc-macro = true
[macro.proc.result]
As functions, they must either return syntax, panic, or loop endlessly. Returned syntax either replaces or adds the syntax depending on the kind of procedural macro. Panics are caught by the compiler and are turned into a compiler error. Endless loops are not caught by the compiler which hangs the compiler.
Procedural macros run during compilation, and thus have the same resources that the compiler has. For example, standard input, error, and output are the same that the compiler has access to. Similarly, file access is the same. Because of this, procedural macros have the same security concerns that Cargo’s build scripts have.
[macro.proc.error]
Procedural macros have two ways of reporting errors. The first is to panic. The second is to emit a compile_error macro invocation.
[macro.proc.proc_macro]
The proc_macro crate
[macro.proc.proc_macro.intro]
Procedural macro crates almost always will link to the compiler-provided proc_macro crate. The proc_macro crate provides types required for writing procedural macros and facilities to make it easier.
[macro.proc.proc_macro.token-stream]
This crate primarily contains a TokenStream type. Procedural macros operate over token streams instead of AST nodes, which is a far more stable interface over time for both the compiler and for procedural macros to target. A token stream is roughly equivalent to Vec<TokenTree> where a TokenTree can roughly be thought of as lexical token. For example foo is an Ident token, . is a Punct token, and 1.2 is a Literal token. The TokenStream type, unlike Vec<TokenTree>, is cheap to clone.
[macro.proc.proc_macro.span]
All tokens have an associated Span. A Span is an opaque value that cannot be modified but can be manufactured. Spans represent an extent of source code within a program and are primarily used for error reporting. While you cannot modify a Span itself, you can always change the Span associated with any token, such as through getting a Span from another token.
[macro.proc.hygiene]
Procedural macro hygiene
Procedural macros are unhygienic. This means they behave as if the output token stream was simply written inline to the code it’s next to. This means that it’s affected by external items and also affects external imports.
Macro authors need to be careful to ensure their macros work in as many contexts as possible given this limitation. This often includes using absolute paths to items in libraries (for example, ::std::option::Option instead of Option) or by ensuring that generated functions have names that are unlikely to clash with other functions (like __internal_foo instead of foo).
[macro.proc.function]
Function-like procedural macros
[macro.proc.function.intro]
Function-like procedural macros are procedural macros that are invoked using the macro invocation operator (!).
[macro.proc.function.def]
These macros are defined by a public function with the proc_macro attribute and a signature of (TokenStream) -> TokenStream. The input TokenStream is what is inside the delimiters of the macro invocation and the output TokenStream replaces the entire macro invocation.
[macro.proc.function.namespace]
The proc_macro attribute defines the macro in the macro namespace in the root of the crate.
For example, the following macro definition ignores its input and outputs a function answer into its scope.
extern crate proc_macro;
use proc_macro::TokenStream;

#[proc_macro]
pub fn make_answer(_item: TokenStream) -> TokenStream {
    "fn answer() -> u32 { 42 }".parse().unwrap()
}
And then we use it in a binary crate to print “42” to standard output.
extern crate proc_macro_examples;
use proc_macro_examples::make_answer;

make_answer!();

fn main() {
    println!("{}", answer());
}
[macro.proc.function.invocation]
Function-like procedural macros may be invoked in any macro invocation position, which includes statements, expressions, patterns, type expressions, item positions, including items in extern blocks, inherent and trait implementations, and trait definitions.
[macro.proc.derive]
The proc_macro_derive attribute
[macro.proc.derive.intro]
Applying the proc_macro_derive attribute to a function defines a derive macro that can be invoked by the derive attribute. These macros are given the token stream of a struct, enum, or union definition and can emit new items after it. They can also declare and use derive macro helper attributes.
Example

This derive macro ignores its input and appends tokens that define a function.

extern crate proc_macro;
use proc_macro::TokenStream;

#[proc_macro_derive(AnswerFn)]
pub fn derive_answer_fn(_item: TokenStream) -> TokenStream {
    "fn answer() -> u32 { 42 }".parse().unwrap()
}
To use it, we might write:

extern crate proc_macro_examples;
use proc_macro_examples::AnswerFn;

#[derive(AnswerFn)]
struct Struct;

fn main() {
    assert_eq!(42, answer());
}
[macro.proc.derive.syntax]
The syntax for the proc_macro_derive attribute is:
Syntax
ProcMacroDeriveAttribute →
    proc_macro_derive ( DeriveMacroName ( , DeriveMacroAttributes )? ,? )

DeriveMacroName → IDENTIFIER

DeriveMacroAttributes →
    attributes ( ( IDENTIFIER ( , IDENTIFIER )* ,? )? )

Show syntax diagrams

The name of the derive macro is given by DeriveMacroName. The optional attributes argument is described in macro.proc.derive.attributes.
[macro.proc.derive.allowed-positions]
The proc_macro_derive attribute may only be applied to a pub function with the Rust ABI defined in the root of the crate with a type of fn(TokenStream) -> TokenStream where TokenStream comes from the proc_macro crate. The function may be const and may use extern to explicitly specify the Rust ABI, but it may not use any other qualifiers (e.g. it may not be async or unsafe).
[macro.proc.derive.duplicates]
The proc_macro_derive attribute may be used only once on a function.
[macro.proc.derive.namespace]
The proc_macro_derive attribute publicly defines the derive macro in the macro namespace in the root of the crate.
[macro.proc.derive.output]
The input TokenStream is the token stream of the item to which the derive attribute is applied. The output TokenStream must be a (possibly empty) set of items. These items are appended following the input item within the same module or block.
[macro.proc.derive.attributes]
Derive macro helper attributes
[macro.proc.derive.attributes.intro]
Derive macros can declare derive macro helper attributes to be used within the scope of the item to which the derive macro is applied. These attributes are inert. While their purpose is to be used by the macro that declared them, they can be seen by any macro.
[macro.proc.derive.attributes.decl]
A helper attribute for a derive macro is declared by adding its identifier to the attributes list in the proc_macro_derive attribute.
Example

This declares a helper attribute and then ignores it.

#[proc_macro_derive(WithHelperAttr, attributes(helper))]
pub fn derive_with_helper_attr(_item: TokenStream) -> TokenStream {
    TokenStream::new()
}
To use it, we might write:

#[derive(WithHelperAttr)]
struct Struct {
    #[helper] field: (),
}
[macro.proc.attribute]
Attribute macros
[macro.proc.attribute.intro]
Attribute macros define new outer attributes which can be attached to items, including items in extern blocks, inherent and trait implementations, and trait definitions.
[macro.proc.attribute.def]
Attribute macros are defined by a public function with the proc_macro_attribute attribute that has a signature of (TokenStream, TokenStream) -> TokenStream. The first TokenStream is the delimited token tree following the attribute’s name, not including the outer delimiters. If the attribute is written as a bare attribute name, the attribute TokenStream is empty. The second TokenStream is the rest of the item including other attributes on the item. The returned TokenStream replaces the item with an arbitrary number of items.
[macro.proc.attribute.namespace]
The proc_macro_attribute attribute defines the attribute in the macro namespace in the root of the crate.
For example, this attribute macro takes the input stream and returns it as is, effectively being the no-op of attributes.

#[proc_macro_attribute]
pub fn return_as_is(_attr: TokenStream, item: TokenStream) -> TokenStream {
    item
}
This following example shows the stringified TokenStreams that the attribute macros see. The output will show in the output of the compiler. The output is shown in the comments after the function prefixed with “out:”.
// my-macro/src/lib.rs

#[proc_macro_attribute]
pub fn show_streams(attr: TokenStream, item: TokenStream) -> TokenStream {
    println!("attr: \"{attr}\"");
    println!("item: \"{item}\"");
    item
}
// src/lib.rs
extern crate my_macro;

use my_macro::show_streams;

// Example: Basic function
#[show_streams]
fn invoke1() {}
// out: attr: ""
// out: item: "fn invoke1() {}"

// Example: Attribute with input
#[show_streams(bar)]
fn invoke2() {}
// out: attr: "bar"
// out: item: "fn invoke2() {}"

// Example: Multiple tokens in the input
#[show_streams(multiple => tokens)]
fn invoke3() {}
// out: attr: "multiple => tokens"
// out: item: "fn invoke3() {}"

// Example:
#[show_streams { delimiters }]
fn invoke4() {}
// out: attr: "delimiters"
// out: item: "fn invoke4() {}"
[macro.proc.token]
Declarative macro tokens and procedural macro tokens
[macro.proc.token.intro]
Declarative macro_rules macros and procedural macros use similar, but different definitions for tokens (or rather TokenTrees.)
[macro.proc.token.macro_rules]
Token trees in macro_rules (corresponding to tt matchers) are defined as
Delimited groups ((...), {...}, etc)
All operators supported by the language, both single-character and multi-character ones (+, +=).
Note that this set doesn’t include the single quote '.
Literals ("string", 1, etc)
Note that negation (e.g. -1) is never a part of such literal tokens, but a separate operator token.
Identifiers, including keywords (ident, r#ident, fn)
Lifetimes ('ident)
Metavariable substitutions in macro_rules (e.g. $my_expr in macro_rules! mac { ($my_expr: expr) => { $my_expr } } after the mac’s expansion, which will be considered a single token tree regardless of the passed expression)
[macro.proc.token.tree]
Token trees in procedural macros are defined as
Delimited groups ((...), {...}, etc)
All punctuation characters used in operators supported by the language (+, but not +=), and also the single quote ' character (typically used in lifetimes, see below for lifetime splitting and joining behavior)
Literals ("string", 1, etc)
Negation (e.g. -1) is supported as a part of integer and floating point literals.
Identifiers, including keywords (ident, r#ident, fn)
[macro.proc.token.conversion.intro]
Mismatches between these two definitions are accounted for when token streams are passed to and from procedural macros.
Note that the conversions below may happen lazily, so they might not happen if the tokens are not actually inspected.
[macro.proc.token.conversion.to-proc_macro]
When passed to a proc-macro
All multi-character operators are broken into single characters.
Lifetimes are broken into a ' character and an identifier.
The keyword metavariable $crate is passed as a single identifier.
All other metavariable substitutions are represented as their underlying token streams.
Such token streams may be wrapped into delimited groups (Group) with implicit delimiters (Delimiter::None) when it’s necessary for preserving parsing priorities.
tt and ident substitutions are never wrapped into such groups and always represented as their underlying token trees.
[macro.proc.token.conversion.from-proc_macro]
When emitted from a proc macro
Punctuation characters are glued into multi-character operators when applicable.
Single quotes ' joined with identifiers are glued into lifetimes.
Negative literals are converted into two tokens (the - and the literal) possibly wrapped into a delimited group (Group) with implicit delimiters (Delimiter::None) when it’s necessary for preserving parsing priorities.
[macro.proc.token.doc-comment]
Note that neither declarative nor procedural macros support doc comment tokens (e.g. /// Doc), so they are always converted to token streams representing their equivalent #[doc = r"str"] attributes when passed to macros.
[crate]
