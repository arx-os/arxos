# Items
[items.syntax]
Syntax
Item →
    OuterAttribute* ( VisItem | MacroItem )

VisItem →
    Visibility?
    (
        Module
      | ExternCrate
      | UseDeclaration
      | Function
      | TypeAlias
      | Struct
      | Enumeration
      | Union
      | ConstantItem
      | StaticItem
      | Trait
      | Implementation
      | ExternBlock
    )

MacroItem →
      MacroInvocationSemi
    | MacroRulesDefinition

Show syntax diagrams

[items.intro]
An item is a component of a crate. Items are organized within a crate by a nested set of modules. Every crate has a single “outermost” anonymous module; all further items within the crate have paths within the module tree of the crate.
[items.static-def]
Items are entirely determined at compile-time, generally remain fixed during execution, and may reside in read-only memory.
[items.kinds]
There are several kinds of items:
modules
extern crate declarations
use declarations
function definitions
type definitions
struct definitions
enumeration definitions
union definitions
## Constant items
## Static items
trait definitions
## Implementations
extern blocks
[items.locations]
Items may be declared in the root of the crate, a module, or a block expression.
[items.associated-locations]
## Associated Items
[items.extern-locations]
## External blocks
[items.decl-order]
Items may be defined in any order, with the exception of macro_rules which has its own scoping behavior.
[items.name-resolution]
Name resolution of item names allows items to be defined before or after where the item is referred to in the module or block.
See item scopes for information on the scoping rules of items.
[items.mod]
## Modules

[items.mod.syntax]
Syntax
Module →
      unsafe? mod IDENTIFIER ;
    | unsafe? mod IDENTIFIER {
        InnerAttribute*
        Item*
      }

Show syntax diagrams

[items.mod.intro]
A module is a container for zero or more items.
[items.mod.def]
A module item is a module, surrounded in braces, named, and prefixed with the keyword mod. A module item introduces a new, named module into the tree of modules making up a crate.
[items.mod.nesting]
Modules can nest arbitrarily.
An example of a module:
mod math {
    type Complex = (f64, f64);
    fn sin(f: f64) -> f64 {
        /* ... */
    }
    fn cos(f: f64) -> f64 {
        /* ... */
    }
    fn tan(f: f64) -> f64 {
        /* ... */
    }
}
[items.mod.namespace]
Modules are defined in the type namespace of the module or block where they are located.
[items.mod.multiple-items]
It is an error to define multiple items with the same name in the same namespace within a module. See the scopes chapter for more details on restrictions and shadowing behavior.
[items.mod.unsafe]
The unsafe keyword is syntactically allowed to appear before the mod keyword, but it is rejected at a semantic level. This allows macros to consume the syntax and make use of the unsafe keyword, before removing it from the token stream.
[items.mod.outlined]
Module Source Filenames
[items.mod.outlined.intro]
A module without a body is loaded from an external file. When the module does not have a path attribute, the path to the file mirrors the logical module path.
[items.mod.outlined.search]
Ancestor module path components are directories, and the module’s contents are in a file with the name of the module plus the .rs extension. For example, the following module structure can have this corresponding filesystem structure:
Module Path	Filesystem Path	File Contents
crate	lib.rs	mod util;
crate::util	util.rs	mod config;
crate::util::config	util/config.rs	
[items.mod.outlined.search-mod]
Module filenames may also be the name of the module as a directory with the contents in a file named mod.rs within that directory. The above example can alternately be expressed with crate::util’s contents in a file named util/mod.rs. It is not allowed to have both util.rs and util/mod.rs.
Note

Prior to rustc 1.30, using mod.rs files was the way to load a module with nested children. It is encouraged to use the new naming convention as it is more consistent, and avoids having many files named mod.rs within a project.
[items.mod.outlined.path]
The path attribute
[items.mod.outlined.path.intro]
The directories and files used for loading external file modules can be influenced with the path attribute.
[items.mod.outlined.path.search]
For path attributes on modules not inside inline module blocks, the file path is relative to the directory the source file is located. For example, the following code snippet would use the paths shown based on where it is located:
#[path = "foo.rs"]
mod c;
Source File	c’s File Location	c’s Module Path
src/a/b.rs	src/a/foo.rs	crate::a::b::c
src/a/mod.rs	src/a/foo.rs	crate::a::c
[items.mod.outlined.path.search-nested]
For path attributes inside inline module blocks, the relative location of the file path depends on the kind of source file the path attribute is located in. “mod-rs” source files are root modules (such as lib.rs or main.rs) and modules with files named mod.rs. “non-mod-rs” source files are all other module files. Paths for path attributes inside inline module blocks in a mod-rs file are relative to the directory of the mod-rs file including the inline module components as directories. For non-mod-rs files, it is the same except the path starts with a directory with the name of the non-mod-rs module. For example, the following code snippet would use the paths shown based on where it is located:
mod inline {
    #[path = "other.rs"]
    mod inner;
}
Source File	inner’s File Location	inner’s Module Path
src/a/b.rs	src/a/b/inline/other.rs	crate::a::b::inline::inner
src/a/mod.rs	src/a/inline/other.rs	crate::a::inline::inner
An example of combining the above rules of path attributes on inline modules and nested modules within (applies to both mod-rs and non-mod-rs files):
#[path = "thread_files"]
mod thread {
    // Load the `local_data` module from `thread_files/tls.rs` relative to
    // this source file's directory.
    #[path = "tls.rs"]
    mod local_data;
}
[items.mod.attributes]
Attributes on Modules
[items.mod.attributes.intro]
Modules, like all items, accept outer attributes. They also accept inner attributes: either after { for a module with a body, or at the beginning of the source file, after the optional BOM and shebang.
[items.mod.attributes.supported]
The built-in attributes that have meaning on a module are cfg, deprecated, doc, the lint check attributes, path, and no_implicit_prelude. Modules also accept macro attributes.
[items.extern-crate]
Extern crate declarations

[items.extern-crate.syntax]
Syntax
ExternCrate → extern crate CrateRef AsClause? ;

CrateRef → IDENTIFIER | self

AsClause → as ( IDENTIFIER | _ )

Show syntax diagrams

[items.extern-crate.intro]
An extern crate declaration specifies a dependency on an external crate.
[items.extern-crate.namespace]
The external crate is then bound into the declaring scope as the given identifier in the type namespace.
[items.extern-crate.extern-prelude]
Additionally, if the extern crate appears in the crate root, then the crate name is also added to the extern prelude, making it automatically in scope in all modules.
[items.extern-crate.as]
The as clause can be used to bind the imported crate to a different name.
[items.extern-crate.lookup]
The external crate is resolved to a specific soname at compile time, and a runtime linkage requirement to that soname is passed to the linker for loading at runtime. The soname is resolved at compile time by scanning the compiler’s library path and matching the optional crate_name provided against the crate_name attributes that were declared on the external crate when it was compiled. If no crate_name is provided, a default name attribute is assumed, equal to the identifier given in the extern crate declaration.
[items.extern-crate.self]
The self crate may be imported which creates a binding to the current crate. In this case the as clause must be used to specify the name to bind it to.
Three examples of extern crate declarations:
extern crate pcre;

extern crate std; // equivalent to: extern crate std as std;

extern crate std as ruststd; // linking to 'std' under another name
[items.extern-crate.name-restrictions]
When naming Rust crates, hyphens are disallowed. However, Cargo packages may make use of them. In such case, when Cargo.toml doesn’t specify a crate name, Cargo will transparently replace - with _ (Refer to RFC 940 for more details).
Here is an example:
// Importing the Cargo package hello-world
extern crate hello_world; // hyphen replaced with an underscore
[items.extern-crate.underscore]
Underscore Imports
[items.extern-crate.underscore.intro]
## Extern crates
[items.extern-crate.underscore.macro_use]
The macro_use attribute works as usual and imports the macro names into the macro_use prelude.
[items.extern-crate.no_link]
The no_link attribute
[items.extern-crate.no_link.intro]
The no_link attribute may be applied to an extern crate item to prevent linking the crate.
Note

This is helpful, e.g., when only the macros of a crate are needed.
Example

#[no_link]
extern crate other_crate;

other_crate::some_macro!();
[items.extern-crate.no_link.syntax]
The no_link attribute uses the MetaWord syntax.
[items.extern-crate.no_link.allowed-positions]
The no_link attribute may only be applied to an extern crate declaration.
Note

rustc ignores use in other positions but lints against it. This may become an error in the future.
[items.extern-crate.no_link.duplicates]
Only the first use of no_link on an extern crate declaration has effect.
Note

rustc lints against any use following the first. This may become an error in the future.
[items.use]
## Use declarations

[items.use.syntax]
Syntax
UseDeclaration → use UseTree ;

UseTree →
      ( SimplePath? :: )? *
    | ( SimplePath? :: )? { ( UseTree ( , UseTree )* ,? )? }
    | SimplePath ( as ( IDENTIFIER | _ ) )?

Show syntax diagrams

[items.use.intro]
A use declaration creates one or more local name bindings synonymous with some other path. Usually a use declaration is used to shorten the path required to refer to a module item. These declarations may appear in modules and blocks, usually at the top. A use declaration is also sometimes called an import, or, if it is public, a re-export.
[items.use.forms]
Use declarations support a number of convenient shortcuts:
[items.use.forms.multiple]
Simultaneously binding a list of paths with a common prefix, using the brace syntax use a::b::{c, d, e::f, g::h::i};
[items.use.forms.self]
Simultaneously binding a list of paths with a common prefix and their common parent module, using the self keyword, such as use a::b::{self, c, d::e};
[items.use.forms.as]
Rebinding the target name as a new local name, using the syntax use p::q::r as x;. This can also be used with the last two features: use a::b::{self as ab, c as abc}.
[items.use.forms.glob]
Binding all paths matching a given prefix, using the asterisk wildcard syntax use a::b::*;.
[items.use.forms.nesting]
Nesting groups of the previous features multiple times, such as use a::b::{self as ab, c, d::{*, e::f}};
An example of use declarations:
use std::collections::hash_map::{self, HashMap};

fn foo<T>(_: T){}
fn bar(map1: HashMap<String, usize>, map2: hash_map::HashMap<String, usize>){}

fn main() {
## Functions
    use std::option::Option::{Some, None};

    // Equivalent to 'foo(vec![std::option::Option::Some(1.0f64),
    // std::option::Option::None]);'
    foo(vec![Some(1.0f64), None]);

    // Both `hash_map` and `HashMap` are in scope.
    let map1 = HashMap::new();
    let map2 = hash_map::HashMap::new();
    bar(map1, map2);
}
[items.use.visibility]
use Visibility
[items.use.visibility.intro]
Like items, use declarations are private to the containing module, by default. Also like items, a use declaration can be public, if qualified by the pub keyword. Such a use declaration serves to re-export a name. A public use declaration can therefore redirect some public name to a different target definition: even a definition with a private canonical path, inside a different module.
[items.use.visibility.unambiguous]
If a sequence of such redirections form a cycle or cannot be resolved unambiguously, they represent a compile-time error.
An example of re-exporting:
mod quux {
    pub use self::foo::{bar, baz};
    pub mod foo {
        pub fn bar() {}
        pub fn baz() {}
    }
}

fn main() {
    quux::bar();
    quux::baz();
}
In this example, the module quux re-exports two public names defined in foo.
[items.use.path]
use Paths
[items.use.path.intro]
The paths that are allowed in a use item follow the SimplePath grammar and are similar to the paths that may be used in an expression. They may create bindings for:
Nameable items
Enum variants
Built-in types
