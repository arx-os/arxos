# Constant Evaluation
[const-eval.general]
Constant evaluation is the process of computing the result of expressions during compilation. Only a subset of all expressions can be evaluated at compile-time.
[const-eval.const-expr]
Constant expressions
[const-eval.const-expr.general]
Certain forms of expressions, called constant expressions, can be evaluated at compile time.
[const-eval.const-expr.const-context]
In const contexts, these are the only allowed expressions, and are always evaluated at compile time.
[const-eval.const-expr.runtime-context]
In other places, such as let statements, constant expressions may be, but are not guaranteed to be, evaluated at compile time.
[const-eval.const-expr.error]
Behaviors such as out of bounds array indexing or overflow are compiler errors if the value must be evaluated at compile time (i.e. in const contexts). Otherwise, these behaviors are warnings, but will likely panic at run-time.
[const-eval.const-expr.list]
The following expressions are constant expressions, so long as any operands are also constant expressions and do not cause any Drop::drop calls to be run.
[const-eval.const-expr.literal]
Literals.
[const-eval.const-expr.parameter]
Const parameters.
[const-eval.const-expr.path-item]
Paths to functions and constants. Recursively defining constants is not allowed.
[const-eval.const-expr.path-static]
Paths to statics with these restrictions:

Writes to static items are not allowed in any constant evaluation context.
Reads from extern statics are not allowed in any constant evaluation context.
If the evaluation is not carried out in an initializer of a static item, then reads from any mutable static are not allowed. A mutable static is a static mut item, or a static item with an interior-mutable type.
These requirements are checked only when the constant is evaluated. In other words, having such accesses syntactically occur in const contexts is allowed as long as they never get executed.
[const-eval.const-expr.tuple]
Tuple expressions.
[const-eval.const-expr.array]
Array expressions.
[const-eval.const-expr.constructor]
Struct expressions.
[const-eval.const-expr.block]
Block expressions, including unsafe and const blocks.
let statements and thus irrefutable patterns, including mutable bindings
assignment expressions
compound assignment expressions
expression statements
[const-eval.const-expr.field]
Field expressions.
[const-eval.const-expr.index]
Index expressions, array indexing or slice with a usize.
[const-eval.const-expr.range]
Range expressions.
[const-eval.const-expr.closure]
Closure expressions which don’t capture variables from the environment.
[const-eval.const-expr.builtin-arith-logic]
Built-in negation, arithmetic, logical, comparison or lazy boolean operators used on integer and floating point types, bool, and char.
[const-eval.const-expr.borrows]
All forms of borrows, including raw borrows, except borrows of expressions whose temporary scopes would be extended (see temporary lifetime extension) to the end of the program and which are either:

Mutable borrows.
Shared borrows of expressions that result in values with interior mutability.
// Due to being in tail position, this borrow extends the scope of the
// temporary to the end of the program. Since the borrow is mutable,
// this is not allowed in a const expression.
const C: &u8 = &mut 0; // ERROR not allowed
// Const blocks are similar to initializers of `const` items.
let _: &u8 = const { &mut 0 }; // ERROR not allowed
// This is not allowed as 1) the temporary scope is extended to the
// end of the program and 2) the temporary has interior mutability.
const C: &AtomicU8 = &AtomicU8::new(0); // ERROR not allowed
// As above.
let _: &_ = const { &AtomicU8::new(0) }; // ERROR not allowed
// Even though this borrow is mutable, it's not of a temporary, so
// this is allowed.
const C: &u8 = unsafe { static mut S: u8 = 0; &mut S }; // OK
// Even though this borrow is of a value with interior mutability,
// it's not of a temporary, so this is allowed.
const C: &AtomicU8 = {
    static S: AtomicU8 = AtomicU8::new(0); &S // OK
};
// This shared borrow of an interior mutable temporary is allowed
// because its scope is not extended.
const C: () = { _ = &AtomicU8::new(0); }; // OK
// Even though the borrow is mutable and the temporary lives to the
// end of the program due to promotion, this is allowed because the
// borrow is not in tail position and so the scope of the temporary
// is not extended via temporary lifetime extension.
const C: () = { let _: &'static mut [u8] = &mut []; }; // OK
//                                              ~~
//                                     Promoted temporary.
Note

In other words — to focus on what’s allowed rather than what’s not allowed — shared borrows of interior mutable data and mutable borrows are only allowed in a const context when the borrowed place expression is transient, indirect, or static.

A place expression is transient if it is a variable local to the current const context or an expression whose temporary scope is contained inside the current const context.

// The borrow is of a variable local to the initializer, therefore
// this place expresssion is transient.
const C: () = { let mut x = 0; _ = &mut x; };
// The borrow is of a temporary whose scope has not been extended,
// therefore this place expression is transient.
const C: () = { _ = &mut 0u8; };
// When a temporary is promoted but not lifetime extended, its
// place expression is still treated as transient.
const C: () = { let _: &'static mut [u8] = &mut []; };
A place expression is indirect if it is a dereference expression.

const C: () = { _ = &mut *(&mut 0); };
A place expression is static if it is a static item.

const C: &u8 = unsafe { static mut S: u8 = 0; &mut S };
Note

One surprising consequence of these rules is that we allow this,

const C: &[u8] = { let x: &mut [u8] = &mut []; x }; // OK
//                                    ~~~~~~~
// Empty arrays are promoted even behind mutable borrows.
but we disallow this similar code:

const C: &[u8] = &mut []; // ERROR
//               ~~~~~~~
//           Tail expression.
The difference between these is that, in the first, the empty array is promoted but its scope does not undergo temporary lifetime extension, so we consider the place expression to be transient (even though after promotion the place indeed lives to the end of the program). In the second, the scope of the empty array temporary does undergo lifetime extension, and so it is rejected due to being a mutable borrow of a lifetime-extended temporary (and therefore borrowing a non-transient place expression).

The effect is surprising because temporary lifetime extension, in this case, causes less code to compile than would without it.

See issue #143129 for more details.
[const-eval.const-expr.deref]
The dereference operator except for raw pointers.
[const-eval.const-expr.group]
Grouped expressions.
[const-eval.const-expr.cast]
Cast expressions, except
pointer to address casts and
function pointer to address casts.
[const-eval.const-expr.const-fn]
Calls of const functions and const methods.
[const-eval.const-expr.loop]
loop and while expressions.
[const-eval.const-expr.if-match]
if and match expressions.
[const-eval.const-context]
Const context
[const-eval.const-context.general]
A const context is one of the following:
[const-eval.const-context.array-length]
Array type length expressions
[const-eval.const-context.repeat-length]
Array repeat length expressions
[const-eval.const-context.init]
The initializer of
constants
statics
enum discriminants
[const-eval.const-context.generic]
A const generic argument
[const-eval.const-context.block]
A const block
[const-eval.const-context.outer-generics]
Const contexts that are used as parts of types (array type and repeat length expressions as well as const generic arguments) can only make restricted use of surrounding generic parameters: such an expression must either be a single bare const generic parameter, or an arbitrary expression not making use of any generics.
[const-eval.const-fn]
Const Functions
[const-eval.const-fn.general]
A const fn is a function that one is permitted to call from a const context.
[const-eval.const-fn.usage]
Declaring a function const has no effect on any existing uses, it only restricts the types that arguments and the return type may use, and restricts the function body to constant expressions.
[const-eval.const-fn.const-context]
When called from a const context, the function is interpreted by the compiler at compile time. The interpretation happens in the environment of the compilation target and not the host. So usize is 32 bits if you are compiling against a 32 bit system, irrelevant of whether you are building on a 64 bit or a 32 bit system.
[abi]
