# Appendices
## Grammar summary

The following is a summary of the grammar production rules. For details on the syntax of this grammar, see notation.grammar.syntax.
Lexer summary
Lexer
CHAR → <a Unicode scalar value>

NUL → U+0000

TAB → U+0009

LF → U+000A

CR → U+000D

IDENTIFIER_OR_KEYWORD →
      XID_Start XID_Continue*
    | _ XID_Continue+

XID_Start → <XID_Start defined by Unicode>

XID_Continue → <XID_Continue defined by Unicode>

RAW_IDENTIFIER → r# IDENTIFIER_OR_KEYWORDexcept crate, self, super, Self

NON_KEYWORD_IDENTIFIER → IDENTIFIER_OR_KEYWORDexcept a strict or reserved keyword

IDENTIFIER → NON_KEYWORD_IDENTIFIER | RAW_IDENTIFIER

RESERVED_RAW_IDENTIFIER → r#_

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

SUFFIX → IDENTIFIER_OR_KEYWORD

SUFFIX_NO_E → SUFFIXnot beginning with e or E

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

STRING_LITERAL →
    " (
        ~[" \ CR]
      | QUOTE_ESCAPE
      | ASCII_ESCAPE
      | UNICODE_ESCAPE
      | STRING_CONTINUE
    )* " SUFFIX?

STRING_CONTINUE → \ LF

RAW_STRING_LITERAL → r RAW_STRING_CONTENT SUFFIX?

RAW_STRING_CONTENT →
      " ( ~CR )* (non-greedy) "
    | # RAW_STRING_CONTENT #

BYTE_LITERAL →
    b' ( ASCII_FOR_CHAR | BYTE_ESCAPE ) ' SUFFIX?

ASCII_FOR_CHAR →
    <any ASCII (i.e. 0x00 to 0x7F) except ', \, LF, CR, or TAB>

BYTE_ESCAPE →
      \x HEX_DIGIT HEX_DIGIT
    | \n | \r | \t | \\ | \0 | \' | \"

BYTE_STRING_LITERAL →
    b" ( ASCII_FOR_STRING | BYTE_ESCAPE | STRING_CONTINUE )* " SUFFIX?

ASCII_FOR_STRING →
    <any ASCII (i.e 0x00 to 0x7F) except ", \, or CR>

RAW_BYTE_STRING_LITERAL →
    br RAW_BYTE_STRING_CONTENT SUFFIX?

RAW_BYTE_STRING_CONTENT →
      " ASCII_FOR_RAW* (non-greedy) "
    | # RAW_BYTE_STRING_CONTENT #

ASCII_FOR_RAW →
    <any ASCII (i.e. 0x00 to 0x7F) except CR>

C_STRING_LITERAL →
    c" (
        ~[" \ CR NUL]
      | BYTE_ESCAPEexcept \0 or \x00
      | UNICODE_ESCAPEexcept \u{0}, \u{00}, …, \u{000000}
      | STRING_CONTINUE
    )* " SUFFIX?

RAW_C_STRING_LITERAL →
    cr RAW_C_STRING_CONTENT SUFFIX?

RAW_C_STRING_CONTENT →
      " ( ~[CR NUL] )* (non-greedy) "
    | # RAW_C_STRING_CONTENT #

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

TUPLE_INDEX → INTEGER_LITERAL

FLOAT_LITERAL →
      DEC_LITERAL .not immediately followed by ., _ or an XID_Start character
    | DEC_LITERAL . DEC_LITERAL SUFFIX_NO_E?
    | DEC_LITERAL ( . DEC_LITERAL )? FLOAT_EXPONENT SUFFIX?

FLOAT_EXPONENT →
    ( e | E ) ( + | - )? ( DEC_DIGIT | _ )* DEC_DIGIT ( DEC_DIGIT | _ )*

RESERVED_NUMBER →
      BIN_LITERAL [2-9]
    | OCT_LITERAL [8-9]
    | ( BIN_LITERAL | OCT_LITERAL | HEX_LITERAL ) .not immediately followed by ., _ or an XID_Start character
    | ( BIN_LITERAL | OCT_LITERAL ) ( e | E )
    | 0b _* <end of input or not BIN_DIGIT>
    | 0o _* <end of input or not OCT_DIGIT>
    | 0x _* <end of input or not HEX_DIGIT>
    | DEC_LITERAL ( . DEC_LITERAL )? ( e | E ) ( + | - )? <end of input or not DEC_DIGIT>

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

RESERVED_TOKEN_DOUBLE_QUOTE →
    ( IDENTIFIER_OR_KEYWORDexcept b or c or r or br or cr | _ ) "

RESERVED_TOKEN_SINGLE_QUOTE →
    ( IDENTIFIER_OR_KEYWORDexcept b | _ ) '

RESERVED_TOKEN_POUND →
    ( IDENTIFIER_OR_KEYWORDexcept r or br or cr | _ ) #

RESERVED_TOKEN_LIFETIME →
    ' ( IDENTIFIER_OR_KEYWORDexcept r | _ ) #

RESERVED_GUARDED_STRING_LITERAL → #+ STRING_LITERAL

RESERVED_POUNDS → #2..

Show syntax diagrams

Macros summary
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

Attributes summary
Syntax
ProcMacroDeriveAttribute →
    proc_macro_derive ( DeriveMacroName ( , DeriveMacroAttributes )? ,? )

DeriveMacroName → IDENTIFIER

DeriveMacroAttributes →
    attributes ( ( IDENTIFIER ( , IDENTIFIER )* ,? )? )

InnerAttribute → # ! [ Attr ]

OuterAttribute → # [ Attr ]

Attr →
      SimplePath AttrInput?
    | unsafe ( SimplePath AttrInput? )

AttrInput →
      DelimTokenTree
    | = Expression

MetaItem →
      SimplePath
    | SimplePath = Expression
    | SimplePath ( MetaSeq? )

MetaSeq →
    MetaItemInner ( , MetaItemInner )* ,?

MetaItemInner →
      MetaItem
    | Expression

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

InlineAttribute →
      inline ( always )
    | inline ( never )
    | inline

CollapseDebuginfoAttribute → collapse_debuginfo ( CollapseDebuginfoOption )

CollapseDebuginfoOption →
      yes
    | no
    | external

Show syntax diagrams

Items summary
Syntax
Crate →
    InnerAttribute*
    Item*

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

Module →
      unsafe? mod IDENTIFIER ;
    | unsafe? mod IDENTIFIER {
        InnerAttribute*
        Item*
      }

ExternCrate → extern crate CrateRef AsClause? ;

CrateRef → IDENTIFIER | self

AsClause → as ( IDENTIFIER | _ )

UseDeclaration → use UseTree ;

UseTree →
      ( SimplePath? :: )? *
    | ( SimplePath? :: )? { ( UseTree ( , UseTree )* ,? )? }
    | SimplePath ( as ( IDENTIFIER | _ ) )?

Function →
    FunctionQualifiers fn IDENTIFIER GenericParams?
        ( FunctionParameters? )
        FunctionReturnType? WhereClause?
        ( BlockExpression | ; )

FunctionQualifiers → const? async? ItemSafety? ( extern Abi? )?

ItemSafety → safe | unsafe

Abi → STRING_LITERAL | RAW_STRING_LITERAL

FunctionParameters →
      SelfParam ,?
    | ( SelfParam , )? FunctionParam ( , FunctionParam )* ,?

SelfParam → OuterAttribute* ( ShorthandSelf | TypedSelf )

ShorthandSelf → ( & | & Lifetime )? mut? self

TypedSelf → mut? self : Type

FunctionParam → OuterAttribute* ( FunctionParamPattern | ... | Type )

FunctionParamPattern → PatternNoTopAlt : ( Type | ... )

FunctionReturnType → -> Type

TypeAlias →
    type IDENTIFIER GenericParams? ( : TypeParamBounds )?
        WhereClause?
        ( = Type WhereClause? )? ;

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

Enumeration →
    enum IDENTIFIER GenericParams? WhereClause? { EnumVariants? }

EnumVariants → EnumVariant ( , EnumVariant )* ,?

EnumVariant →
    OuterAttribute* Visibility?
    IDENTIFIER ( EnumVariantTuple | EnumVariantStruct )? EnumVariantDiscriminant?

EnumVariantTuple → ( TupleFields? )

EnumVariantStruct → { StructFields? }

EnumVariantDiscriminant → = Expression

Union →
    union IDENTIFIER GenericParams? WhereClause? { StructFields? }

ConstantItem →
    const ( IDENTIFIER | _ ) : Type ( = Expression )? ;

StaticItem →
    ItemSafety? static mut? IDENTIFIER : Type ( = Expression )? ;

Trait →
    unsafe? trait IDENTIFIER GenericParams? ( : TypeParamBounds? )? WhereClause?
    {
        InnerAttribute*
        AssociatedItem*
    }

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

ExternBlock →
    unsafe? extern Abi? {
        InnerAttribute*
        ExternalItem*
    }

ExternalItem →
    OuterAttribute* (
        MacroInvocationSemi
      | Visibility? StaticItem
      | Visibility? Function
    )

GenericParams → < ( GenericParam ( , GenericParam )* ,? )? >

GenericParam → OuterAttribute* ( LifetimeParam | TypeParam | ConstParam )

LifetimeParam → Lifetime ( : LifetimeBounds )?

TypeParam → IDENTIFIER ( : TypeParamBounds? )? ( = Type )?

ConstParam →
    const IDENTIFIER : Type
    ( = BlockExpression | IDENTIFIER | -? LiteralExpression )?

WhereClause → where ( WhereClauseItem , )* WhereClauseItem?

WhereClauseItem →
      LifetimeWhereClauseItem
    | TypeBoundWhereClauseItem

LifetimeWhereClauseItem → Lifetime : LifetimeBounds

TypeBoundWhereClauseItem → ForLifetimes? Type : TypeParamBounds?

AssociatedItem →
    OuterAttribute* (
        MacroInvocationSemi
      | ( Visibility? ( TypeAlias | ConstantItem | Function ) )
    )

Visibility →
      pub
    | pub ( crate )
    | pub ( self )
    | pub ( super )
    | pub ( in SimplePath )

Show syntax diagrams

Configuration summary
Syntax
ConfigurationPredicate →
      ConfigurationOption
    | ConfigurationAll
    | ConfigurationAny
    | ConfigurationNot
    | true
    | false

ConfigurationOption →
    IDENTIFIER ( = ( STRING_LITERAL | RAW_STRING_LITERAL ) )?

ConfigurationAll →
    all ( ConfigurationPredicateList? )

ConfigurationAny →
    any ( ConfigurationPredicateList? )

ConfigurationNot →
    not ( ConfigurationPredicate )

ConfigurationPredicateList →
    ConfigurationPredicate ( , ConfigurationPredicate )* ,?

CfgAttribute → cfg ( ConfigurationPredicate )

CfgAttrAttribute → cfg_attr ( ConfigurationPredicate , CfgAttrs? )

CfgAttrs → Attr ( , Attr )* ,?

Show syntax diagrams

Statements summary
Syntax
Statement →
      ;
    | Item
    | LetStatement
    | ExpressionStatement
    | OuterAttribute* MacroInvocationSemi

LetStatement →
    OuterAttribute* let PatternNoTopAlt ( : Type )?
    (
          = Expression
        | = Expressionexcept LazyBooleanExpression or end with a } else BlockExpression
    )? ;

ExpressionStatement →
      ExpressionWithoutBlock ;
    | ExpressionWithBlock ;?

Show syntax diagrams

Expressions summary
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

PathExpression →
      PathInExpression
    | QualifiedPathInExpression

BlockExpression →
    {
        InnerAttribute*
        Statements?
    }

Statements →
      Statement+
    | Statement+ ExpressionWithoutBlock
    | ExpressionWithoutBlock

AsyncBlockExpression → async move? BlockExpression

ConstBlockExpression → const BlockExpression

UnsafeBlockExpression → unsafe BlockExpression

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

BorrowExpression →
      ( & | && ) Expression
    | ( & | && ) mut Expression
    | ( & | && ) raw const Expression
    | ( & | && ) raw mut Expression

DereferenceExpression → * Expression

TryPropagationExpression → Expression ?

NegationExpression →
      - Expression
    | ! Expression

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

ComparisonExpression →
      Expression == Expression
    | Expression != Expression
    | Expression > Expression
    | Expression < Expression
    | Expression >= Expression
    | Expression <= Expression

LazyBooleanExpression →
      Expression || Expression
    | Expression && Expression

TypeCastExpression → Expression as TypeNoBounds

AssignmentExpression → Expression = Expression

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

GroupedExpression → ( Expression )

ArrayExpression → [ ArrayElements? ]

ArrayElements →
      Expression ( , Expression )* ,?
    | Expression ; Expression

IndexExpression → Expression [ Expression ]

TupleExpression → ( TupleElements? )

TupleElements → ( Expression , )+ Expression?

TupleIndexingExpression → Expression . TUPLE_INDEX

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

CallExpression → Expression ( CallParams? )

CallParams → Expression ( , Expression )* ,?

MethodCallExpression → Expression . PathExprSegment ( CallParams? )

FieldExpression → Expression . IDENTIFIER

ClosureExpression →
    async?
    move?
    ( || | | ClosureParameters? | )
    ( Expression | -> TypeNoBounds BlockExpression )

ClosureParameters → ClosureParam ( , ClosureParam )* ,?

ClosureParam → OuterAttribute* PatternNoTopAlt ( : Type )?

LoopExpression →
    LoopLabel? (
        InfiniteLoopExpression
      | PredicateLoopExpression
      | IteratorLoopExpression
      | LabelBlockExpression
    )

InfiniteLoopExpression → loop BlockExpression

PredicateLoopExpression → while Conditions BlockExpression

IteratorLoopExpression →
    for Pattern in Expressionexcept StructExpression BlockExpression

LoopLabel → LIFETIME_OR_LABEL :

BreakExpression → break LIFETIME_OR_LABEL? Expression?

LabelBlockExpression → BlockExpression

ContinueExpression → continue LIFETIME_OR_LABEL?

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

ReturnExpression → return Expression?

AwaitExpression → Expression . await

UnderscoreExpression → _

Show syntax diagrams

Patterns summary
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

LiteralPattern → -? LiteralExpression

IdentifierPattern → ref? mut? IDENTIFIER ( @ PatternNoTopAlt )?

WildcardPattern → _

RestPattern → ..

RangePattern →
      RangeExclusivePattern
    | RangeInclusivePattern
    | RangeFromPattern
    | RangeToExclusivePattern
    | RangeToInclusivePattern
    | ObsoleteRangePattern

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

ReferencePattern → ( & | && ) mut? PatternWithoutRange

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

TupleStructPattern → PathInExpression ( TupleStructItems? )

TupleStructItems → Pattern ( , Pattern )* ,?

TuplePattern → ( TuplePatternItems? )

TuplePatternItems →
      Pattern ,
    | RestPattern
    | Pattern ( , Pattern )+ ,?

GroupedPattern → ( Pattern )

SlicePattern → [ SlicePatternItems? ]

SlicePatternItems → Pattern ( , Pattern )* ,?

PathPattern → PathExpression

Show syntax diagrams

Types summary
Syntax
Type →
      TypeNoBounds
    | ImplTraitType
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

ParenthesizedType → ( Type )

NeverType → !

TupleType →
      ( )
    | ( ( Type , )+ Type? )

ArrayType → [ Type ; Expression ]

SliceType → [ Type ]

ReferenceType → & Lifetime? mut? TypeNoBounds

RawPointerType → * ( mut | const ) TypeNoBounds

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

TraitObjectType → dyn? TypeParamBounds

TraitObjectTypeOneBound → dyn? TraitBound

ImplTraitType → impl TypeParamBounds

ImplTraitTypeOneBound → impl TraitBound

InferredType → _

Show syntax diagrams

Miscellaneous summary
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

ForLifetimes → for GenericParams

Show syntax diagrams

Paths summary
Syntax
SimplePath →
    ::? SimplePathSegment ( :: SimplePathSegment )*

SimplePathSegment →
    IDENTIFIER | super | self | crate | $crate

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

QualifiedPathInExpression → QualifiedPathType ( :: PathExprSegment )+

QualifiedPathType → < Type ( as TypePath )? >

QualifiedPathInType → QualifiedPathType ( :: TypePathSegment )+

TypePath → ::? TypePathSegment ( :: TypePathSegment )*

TypePathSegment → PathIdentSegment ( ::? ( GenericArgs | TypePathFn ) )?

TypePathFn → ( TypePathFnInputs? ) ( -> TypeNoBounds )?

TypePathFnInputs → Type ( , Type )* ,?

Show syntax diagrams

Assembly summary
Syntax
AsmArgs → FormatString ( , FormatString )* ( , AsmOperand )* ,?

FormatString → STRING_LITERAL | RAW_STRING_LITERAL | MacroInvocation

AsmOperand →
      ClobberAbi
    | AsmOptions
    | RegOperand

ClobberAbi → clobber_abi ( Abi ( , Abi )* ,? )

AsmOptions →
    options ( ( AsmOption ( , AsmOption )* ,? )? )

AsmOption →
      pure
    | nomem
    | readonly
    | preserves_flags
    | noreturn
    | nostack
    | att_syntax
    | raw

RegOperand → ( ParamName = )?
    (
          DirSpec ( RegSpec ) Expression
        | DualDirSpec ( RegSpec ) DualDirSpecExpression
        | sym PathExpression
        | const Expression
        | label { Statements? }
    )

ParamName → IDENTIFIER_OR_KEYWORD | RAW_IDENTIFIER

DualDirSpecExpression →
      Expression
    | Expression => Expression

RegSpec → RegisterClass | ExplicitRegister

RegisterClass → IDENTIFIER_OR_KEYWORD

ExplicitRegister → STRING_LITERAL

DirSpec →
      in
    | out
    | lateout

DualDirSpec →
      inout
    | inlateout

Show syntax diagrams

[macro.ambiguity]
## Macro Follow-Set Ambiguity Formal Specification

This page documents the formal specification of the follow rules for Macros By Example. They were originally specified in RFC 550, from which the bulk of this text is copied, and expanded upon in subsequent RFCs.
[macro.ambiguity.convention]
Definitions & Conventions
[macro.ambiguity.convention.defs]
macro: anything invocable as foo!(...) in source code.
MBE: macro-by-example, a macro defined by macro_rules.
matcher: the left-hand-side of a rule in a macro_rules invocation, or a subportion thereof.
macro parser: the bit of code in the Rust parser that will parse the input using a grammar derived from all of the matchers.
fragment: The class of Rust syntax that a given matcher will accept (or “match”).
repetition : a fragment that follows a regular repeating pattern
NT: non-terminal, the various “meta-variables” or repetition matchers that can appear in a matcher, specified in MBE syntax with a leading $ character.
simple NT: a “meta-variable” non-terminal (further discussion below).
complex NT: a repetition matching non-terminal, specified via repetition operators (*, +, ?).
token: an atomic element of a matcher; i.e. identifiers, operators, open/close delimiters, and simple NT’s.
token tree: a tree structure formed from tokens (the leaves), complex NT’s, and finite sequences of token trees.
delimiter token: a token that is meant to divide the end of one fragment and the start of the next fragment.
separator token: an optional delimiter token in an complex NT that separates each pair of elements in the matched repetition.
separated complex NT: a complex NT that has its own separator token.
delimited sequence: a sequence of token trees with appropriate open- and close-delimiters at the start and end of the sequence.
empty fragment: The class of invisible Rust syntax that separates tokens, i.e. whitespace, or (in some lexical contexts), the empty token sequence.
fragment specifier: The identifier in a simple NT that specifies which fragment the NT accepts.
language: a context-free language.
Example:
macro_rules! i_am_an_mbe {
    (start $foo:expr $($i:ident),* end) => ($foo)
}
[macro.ambiguity.convention.matcher]
(start $foo:expr $($i:ident),* end) is a matcher. The whole matcher is a delimited sequence (with open- and close-delimiters ( and )), and $foo and $i are simple NT’s with expr and ident as their respective fragment specifiers.
[macro.ambiguity.convention.complex-nt]
$(i:ident),* is also an NT; it is a complex NT that matches a comma-separated repetition of identifiers. The , is the separator token for the complex NT; it occurs in between each pair of elements (if any) of the matched fragment.
Another example of a complex NT is $(hi $e:expr ;)+, which matches any fragment of the form hi <expr>; hi <expr>; ... where hi <expr>; occurs at least once. Note that this complex NT does not have a dedicated separator token.
(Note that Rust’s parser ensures that delimited sequences always occur with proper nesting of token tree structure and correct matching of open- and close-delimiters.)
[macro.ambiguity.convention.vars]
We will tend to use the variable “M” to stand for a matcher, variables “t” and “u” for arbitrary individual tokens, and the variables “tt” and “uu” for arbitrary token trees. (The use of “tt” does present potential ambiguity with its additional role as a fragment specifier; but it will be clear from context which interpretation is meant.)
[macro.ambiguity.convention.set]
“SEP” will range over separator tokens, “OP” over the repetition operators *, +, and ?, “OPEN”/“CLOSE” over matching token pairs surrounding a delimited sequence (e.g. [ and ]).
[macro.ambiguity.convention.sequence-vars]
Greek letters “α” “β” “γ” “δ” stand for potentially empty token-tree sequences. (However, the Greek letter “ε” (epsilon) has a special role in the presentation and does not stand for a token-tree sequence.)
This Greek letter convention is usually just employed when the presence of a sequence is a technical detail; in particular, when we wish to emphasize that we are operating on a sequence of token-trees, we will use the notation “tt …” for the sequence, not a Greek letter.
Note that a matcher is merely a token tree. A “simple NT”, as mentioned above, is an meta-variable NT; thus it is a non-repetition. For example, $foo:ty is a simple NT but $($foo:ty)+ is a complex NT.
Note also that in the context of this formalism, the term “token” generally includes simple NTs.
Finally, it is useful for the reader to keep in mind that according to the definitions of this formalism, no simple NT matches the empty fragment, and likewise no token matches the empty fragment of Rust syntax. (Thus, the only NT that can match the empty fragment is a complex NT.) This is not actually true, because the vis matcher can match an empty fragment. Thus, for the purposes of the formalism, we will treat $v:vis as actually being $($v:vis)?, with a requirement that the matcher match an empty fragment.
[macro.ambiguity.invariant]
The Matcher Invariants
[macro.ambiguity.invariant.list]
To be valid, a matcher must meet the following three invariants. The definitions of FIRST and FOLLOW are described later.
For any two successive token tree sequences in a matcher M (i.e. M = ... tt uu ...) with uu ... nonempty, we must have FOLLOW(... tt) ∪ {ε} ⊇ FIRST(uu ...).
For any separated complex NT in a matcher, M = ... $(tt ...) SEP OP ..., we must have SEP ∈ FOLLOW(tt ...).
For an unseparated complex NT in a matcher, M = ... $(tt ...) OP ..., if OP = * or +, we must have FOLLOW(tt ...) ⊇ FIRST(tt ...).
[macro.ambiguity.invariant.follow-matcher]
The first invariant says that whatever actual token that comes after a matcher, if any, must be somewhere in the predetermined follow set. This ensures that a legal macro definition will continue to assign the same determination as to where ... tt ends and uu ... begins, even as new syntactic forms are added to the language.
[macro.ambiguity.invariant.separated-complex-nt]
The second invariant says that a separated complex NT must use a separator token that is part of the predetermined follow set for the internal contents of the NT. This ensures that a legal macro definition will continue to parse an input fragment into the same delimited sequence of tt ...’s, even as new syntactic forms are added to the language.
[macro.ambiguity.invariant.unseparated-complex-nt]
The third invariant says that when we have a complex NT that can match two or more copies of the same thing with no separation in between, it must be permissible for them to be placed next to each other as per the first invariant. This invariant also requires they be nonempty, which eliminates a possible ambiguity.
NOTE: The third invariant is currently unenforced due to historical oversight and significant reliance on the behaviour. It is currently undecided what to do about this going forward. Macros that do not respect the behaviour may become invalid in a future edition of Rust. See the tracking issue.
[macro.ambiguity.sets]
FIRST and FOLLOW, informally
[macro.ambiguity.sets.intro]
A given matcher M maps to three sets: FIRST(M), LAST(M) and FOLLOW(M).
Each of the three sets is made up of tokens. FIRST(M) and LAST(M) may also contain a distinguished non-token element ε (“epsilon”), which indicates that M can match the empty fragment. (But FOLLOW(M) is always just a set of tokens.)
Informally:
[macro.ambiguity.sets.first]
FIRST(M): collects the tokens potentially used first when matching a fragment to M.
[macro.ambiguity.sets.last]
LAST(M): collects the tokens potentially used last when matching a fragment to M.
[macro.ambiguity.sets.follow]
FOLLOW(M): the set of tokens allowed to follow immediately after some fragment matched by M.

In other words: t ∈ FOLLOW(M) if and only if there exists (potentially empty) token sequences α, β, γ, δ where:

M matches β,

t matches γ, and

The concatenation α β γ δ is a parseable Rust program.

[macro.ambiguity.sets.universe]
We use the shorthand ANYTOKEN to denote the set of all tokens (including simple NTs). For example, if any token is legal after a matcher M, then FOLLOW(M) = ANYTOKEN.
(To review one’s understanding of the above informal descriptions, the reader at this point may want to jump ahead to the examples of FIRST/LAST before reading their formal definitions.)
[macro.ambiguity.sets.def]
FIRST, LAST
[macro.ambiguity.sets.def.intro]
Below are formal inductive definitions for FIRST and LAST.
[macro.ambiguity.sets.def.notation]
“A ∪ B” denotes set union, “A ∩ B” denotes set intersection, and “A \ B” denotes set difference (i.e. all elements of A that are not present in B).
[macro.ambiguity.sets.def.first]
FIRST
[macro.ambiguity.sets.def.first.intro]
FIRST(M) is defined by case analysis on the sequence M and the structure of its first token-tree (if any):
[macro.ambiguity.sets.def.first.epsilon]
if M is the empty sequence, then FIRST(M) = { ε },
[macro.ambiguity.sets.def.first.token]
if M starts with a token t, then FIRST(M) = { t },

(Note: this covers the case where M starts with a delimited token-tree sequence, M = OPEN tt ... CLOSE ..., in which case t = OPEN and thus FIRST(M) = { OPEN }.)

(Note: this critically relies on the property that no simple NT matches the empty fragment.)
[macro.ambiguity.sets.def.first.complex]
Otherwise, M is a token-tree sequence starting with a complex NT: M = $( tt ... ) OP α, or M = $( tt ... ) SEP OP α, (where α is the (potentially empty) sequence of token trees for the rest of the matcher).

Let SEP_SET(M) = { SEP } if SEP is present and ε ∈ FIRST(tt ...); otherwise SEP_SET(M) = {}.
Let ALPHA_SET(M) = FIRST(α) if OP = * or ? and ALPHA_SET(M) = {} if OP = +.
FIRST(M) = (FIRST(tt ...) \ {ε}) ∪ SEP_SET(M) ∪ ALPHA_SET(M).
The definition for complex NTs deserves some justification. SEP_SET(M) defines the possibility that the separator could be a valid first token for M, which happens when there is a separator defined and the repeated fragment could be empty. ALPHA_SET(M) defines the possibility that the complex NT could be empty, meaning that M’s valid first tokens are those of the following token-tree sequences α. This occurs when either * or ? is used, in which case there could be zero repetitions. In theory, this could also occur if + was used with a potentially-empty repeating fragment, but this is forbidden by the third invariant.
From there, clearly FIRST(M) can include any token from SEP_SET(M) or ALPHA_SET(M), and if the complex NT match is nonempty, then any token starting FIRST(tt ...) could work too. The last piece to consider is ε. SEP_SET(M) and FIRST(tt ...) \ {ε} cannot contain ε, but ALPHA_SET(M) could. Hence, this definition allows M to accept ε if and only if ε ∈ ALPHA_SET(M) does. This is correct because for M to accept ε in the complex NT case, both the complex NT and α must accept it. If OP = +, meaning that the complex NT cannot be empty, then by definition ε ∉ ALPHA_SET(M). Otherwise, the complex NT can accept zero repetitions, and then ALPHA_SET(M) = FOLLOW(α). So this definition is correct with respect to \varepsilon as well.
[macro.ambiguity.sets.def.last]
LAST
[macro.ambiguity.sets.def.last.intro]
LAST(M), defined by case analysis on M itself (a sequence of token-trees):
[macro.ambiguity.sets.def.last.empty]
if M is the empty sequence, then LAST(M) = { ε }
[macro.ambiguity.sets.def.last.token]
if M is a singleton token t, then LAST(M) = { t }
[macro.ambiguity.sets.def.last.rep-star]
if M is the singleton complex NT repeating zero or more times, M = $( tt ... ) *, or M = $( tt ... ) SEP *

Let sep_set = { SEP } if SEP present; otherwise sep_set = {}.

if ε ∈ LAST(tt ...) then LAST(M) = LAST(tt ...) ∪ sep_set

otherwise, the sequence tt ... must be non-empty; LAST(M) = LAST(tt ...) ∪ {ε}.

[macro.ambiguity.sets.def.last.rep-plus]
if M is the singleton complex NT repeating one or more times, M = $( tt ... ) +, or M = $( tt ... ) SEP +

Let sep_set = { SEP } if SEP present; otherwise sep_set = {}.

if ε ∈ LAST(tt ...) then LAST(M) = LAST(tt ...) ∪ sep_set

otherwise, the sequence tt ... must be non-empty; LAST(M) = LAST(tt ...)

[macro.ambiguity.sets.def.last.rep-question]
if M is the singleton complex NT repeating zero or one time, M = $( tt ...) ?, then LAST(M) = LAST(tt ...) ∪ {ε}.
[macro.ambiguity.sets.def.last.delim]
if M is a delimited token-tree sequence OPEN tt ... CLOSE, then LAST(M) = { CLOSE }.
[macro.ambiguity.sets.def.last.sequence]
if M is a non-empty sequence of token-trees tt uu ...,

If ε ∈ LAST(uu ...), then LAST(M) = LAST(tt) ∪ (LAST(uu ...) \ { ε }).

Otherwise, the sequence uu ... must be non-empty; then LAST(M) = LAST(uu ...).

Examples of FIRST and LAST
Below are some examples of FIRST and LAST. (Note in particular how the special ε element is introduced and eliminated based on the interaction between the pieces of the input.)
Our first example is presented in a tree structure to elaborate on how the analysis of the matcher composes. (Some of the simpler subtrees have been elided.)
INPUT:  $(  $d:ident   $e:expr   );*    $( $( h )* );*    $( f ; )+   g
            ~~~~~~~~   ~~~~~~~                ~
                |         |                   |
FIRST:   { $d:ident }  { $e:expr }          { h }


INPUT:  $(  $d:ident   $e:expr   );*    $( $( h )* );*    $( f ; )+
            ~~~~~~~~~~~~~~~~~~             ~~~~~~~           ~~~
                        |                      |               |
FIRST:          { $d:ident }               { h, ε }         { f }

INPUT:  $(  $d:ident   $e:expr   );*    $( $( h )* );*    $( f ; )+   g
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~    ~~~~~~~~~~~~~~    ~~~~~~~~~   ~
                        |                       |              |       |
FIRST:        { $d:ident, ε }            {  h, ε, ;  }      { f }   { g }


INPUT:  $(  $d:ident   $e:expr   );*    $( $( h )* );*    $( f ; )+   g
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                        |
FIRST:                       { $d:ident, h, ;,  f }
Thus:
FIRST($($d:ident $e:expr );* $( $(h)* );* $( f ;)+ g) = { $d:ident, h, ;, f }
Note however that:
FIRST($($d:ident $e:expr );* $( $(h)* );* $($( f ;)+ g)*) = { $d:ident, h, ;, f, ε }
Here are similar examples but now for LAST.
LAST($d:ident $e:expr) = { $e:expr }
LAST($( $d:ident $e:expr );*) = { $e:expr, ε }
LAST($( $d:ident $e:expr );* $(h)*) = { $e:expr, ε, h }
LAST($( $d:ident $e:expr );* $(h)* $( f ;)+) = { ; }
LAST($( $d:ident $e:expr );* $(h)* $( f ;)+ g) = { g }
[macro.ambiguity.sets.def.follow]
FOLLOW(M)
[macro.ambiguity.sets.def.follow.intro]
Finally, the definition for FOLLOW(M) is built up as follows. pat, expr, etc. represent simple nonterminals with the given fragment specifier.
[macro.ambiguity.sets.def.follow.pat]
FOLLOW(pat) = {=>, ,, =, |, if, in}`.
[macro.ambiguity.sets.def.follow.expr-stmt]
FOLLOW(expr) = FOLLOW(expr_2021) = FOLLOW(stmt) = {=>, ,, ;}`.
[macro.ambiguity.sets.def.follow.ty-path]
FOLLOW(ty) = FOLLOW(path) = {{, [, ,, =>, :, =, >, >>, ;, |, as, where, block nonterminals}.
[macro.ambiguity.sets.def.follow.vis]
FOLLOW(vis) = {,l any keyword or identifier except a non-raw priv; any token that can begin a type; ident, ty, and path nonterminals}.
[macro.ambiguity.sets.def.follow.simple]
FOLLOW(t) = ANYTOKEN for any other simple token, including block, ident, tt, item, lifetime, literal and meta simple nonterminals, and all terminals.
[macro.ambiguity.sets.def.follow.other-matcher]
FOLLOW(M), for any other M, is defined as the intersection, as t ranges over (LAST(M) \ {ε}), of FOLLOW(t).
[macro.ambiguity.sets.def.follow.type-first]
The tokens that can begin a type are, as of this writing, {(, [, !, *, &, &&, ?, lifetimes, >, >>, ::, any non-keyword identifier, super, self, Self, extern, crate, $crate, _, for, impl, fn, unsafe, typeof, dyn}, although this list may not be complete because people won’t always remember to update the appendix when new ones are added.
Examples of FOLLOW for complex M:
FOLLOW($( $d:ident $e:expr )*) = FOLLOW($e:expr)
FOLLOW($( $d:ident $e:expr )* $(;)*) = FOLLOW($e:expr) ∩ ANYTOKEN = FOLLOW($e:expr)
FOLLOW($( $d:ident $e:expr )* $(;)* $( f |)+) = ANYTOKEN
Examples of valid and invalid matchers
With the above specification in hand, we can present arguments for why particular matchers are legal and others are not.
($ty:ty < foo ,) : illegal, because FIRST(< foo ,) = { < } ⊈ FOLLOW(ty)
($ty:ty , foo <) : legal, because FIRST(, foo <) = { , } is ⊆ FOLLOW(ty).
($pa:pat $pb:pat $ty:ty ,) : illegal, because FIRST($pb:pat $ty:ty ,) = { $pb:pat } ⊈ FOLLOW(pat), and also FIRST($ty:ty ,) = { $ty:ty } ⊈ FOLLOW(pat).
( $($a:tt $b:tt)* ; ) : legal, because FIRST($b:tt) = { $b:tt } is ⊆ FOLLOW(tt) = ANYTOKEN, as is FIRST(;) = { ; }.
( $($t:tt),* , $(t:tt),* ) : legal, (though any attempt to actually use this macro will signal a local ambiguity error during expansion).
($ty:ty $(; not sep)* -) : illegal, because FIRST($(; not sep)* -) = { ;, - } is not in FOLLOW(ty).
($($ty:ty)-+) : illegal, because separator - is not in FOLLOW(ty).
($($e:expr)*) : illegal, because expr NTs are not in FOLLOW(expr NT).
## Influences

Rust is not a particularly original language, with design elements coming from a wide range of sources. Some of these are listed below (including elements that have since been removed):
SML, OCaml: algebraic data types, pattern matching, type inference, semicolon statement separation
C++: references, RAII, smart pointers, move semantics, monomorphization, memory model
ML Kit, Cyclone: region based memory management
Haskell (GHC): typeclasses, type families
Newsqueak, Alef, Limbo: channels, concurrency
Erlang: message passing, thread failure, linked thread failure, lightweight concurrency
Swift: optional bindings
Scheme: hygienic macros
C#: attributes
Ruby: closure syntax, block syntax
NIL, Hermes: typestate
Unicode Annex #31: identifier and pattern syntax
## Test summary

The following is a summary of the total tests that are linked to individual rule identifiers within the reference.
Rules	Tests	Uncovered Rules	Coverage
Introduction	1	0	
1	0.0%
1. Notation	5	0	
5	0.0%
2. Lexical structure	0			
      2.1. Input format	12	21	
6	50.0%
      2.2. Keywords	18	0	
18	0.0%
      2.3. Identifiers	12	2	
10	16.7%
      2.4. Comments	10	0	
10	0.0%
      2.5. Whitespace	4	0	
4	0.0%
      2.6. Tokens	116	0	
116	0.0%
3. Macros	12	0	
12	0.0%
      3.1. Macros By Example	50	0	
50	0.0%
      3.2. Procedural Macros	37	0	
37	0.0%
4. Crates and source files	19	0	
19	0.0%
5. Conditional compilation	75	0	
75	0.0%
6. Items	10	0	
10	0.0%
      6.1. Modules	19	0	
19	0.0%
      6.2. Extern crates	17	0	
17	0.0%
      6.3. Use declarations	44	0	
44	0.0%
      6.4. Functions	52	0	
52	0.0%
      6.5. Type aliases	8	0	
8	0.0%
      6.6. Structs	7	0	
7	0.0%
      6.7. Enumerations	33	0	
33	0.0%
      6.8. Unions	31	0	
31	0.0%
      6.9. Constant items	14	0	
14	0.0%
      6.10. Static items	19	0	
19	0.0%
      6.11. Traits	32	0	
32	0.0%
      6.12. Implementations	31	0	
31	0.0%
      6.13. External blocks	89	0	
89	0.0%
      6.14. Generic parameters	26	0	
26	0.0%
      6.15. Associated Items	45	0	
45	0.0%
7. Attributes	23	0	
23	0.0%
      7.1. Testing	23	0	
23	0.0%
      7.2. Derive	15	0	
15	0.0%
      7.3. Diagnostics	51	30	
38	25.5%
      7.4. Code generation	66	0	
66	0.0%
      7.5. Limits	9	0	
9	0.0%
      7.6. Type System	9	0	
9	0.0%
      7.7. Debugger	20	0	
20	0.0%
8. Statements and expressions	1	0	
1	0.0%
      8.1. Statements	23	0	
23	0.0%
      8.2. Expressions	38	0	
38	0.0%
            8.2.1. Literal expressions	87	0	
87	0.0%
            8.2.2. Path expressions	6	0	
6	0.0%
            8.2.3. Block expressions	40	0	
40	0.0%
            8.2.4. Operator expressions	106	0	
106	0.0%
            8.2.5. Grouped expressions	6	0	
6	0.0%
            8.2.6. Array and index expressions	22	0	
22	0.0%
            8.2.7. Tuple and index expressions	16	0	
16	0.0%
            8.2.8. Struct expressions	14	0	
14	0.0%
            8.2.9. Call expressions	11	0	
11	0.0%
            8.2.10. Method call expressions	12	0	
12	0.0%
            8.2.11. Field access expressions	8	0	
8	0.0%
            8.2.12. Closure expressions	17	0	
17	0.0%
            8.2.13. Loop expressions	56	0	
56	0.0%
            8.2.14. Range expressions	5	0	
5	0.0%
            8.2.15. If expressions	18	0	
18	0.0%
            8.2.16. Match expressions	25	0	
25	0.0%
            8.2.17. Return expressions	4	0	
4	0.0%
            8.2.18. Await expressions	9	0	
9	0.0%
            8.2.19. Underscore expressions	5	0	
5	0.0%
9. Patterns	140	0	
140	0.0%
10. Type system	0			
      10.1. Types	22	0	
22	0.0%
            10.1.1. Boolean type	23	0	
23	0.0%
            10.1.2. Numeric types	10	0	
10	0.0%
            10.1.3. Textual types	9	0	
9	0.0%
            10.1.4. Never type	5	0	
5	0.0%
            10.1.5. Tuple types	9	0	
9	0.0%
            10.1.6. Array types	5	0	
5	0.0%
            10.1.7. Slice types	5	0	
5	0.0%
            10.1.8. Struct types	7	0	
7	0.0%
            10.1.9. Enumerated types	6	0	
6	0.0%
            10.1.10. Union types	6	0	
6	0.0%
            10.1.11. Function item types	6	0	
6	0.0%
            10.1.12. Closure types	41	0	
41	0.0%
            10.1.13. Pointer types	22	0	
22	0.0%
            10.1.14. Function pointer types	7	0	
7	0.0%
            10.1.15. Trait object types	11	0	
11	0.0%
            10.1.16. Impl trait type	23	0	
23	0.0%
            10.1.17. Type parameters	1	0	
1	0.0%
            10.1.18. Inferred type	4	0	
4	0.0%
      10.2. Dynamically Sized Types	7	0	
7	0.0%
      10.3. Type layout	68	0	
68	0.0%
      10.4. Interior mutability	9	0	
9	0.0%
      10.5. Subtyping and Variance	12	0	
12	0.0%
      10.6. Trait and lifetime bounds	22	0	
22	0.0%
      10.7. Type coercions	45	0	
45	0.0%
      10.8. Destructors	46	0	
46	0.0%
      10.9. Lifetime elision	24	0	
24	0.0%
11. Special types and traits	54	0	
54	0.0%
12. Names	31	0	
31	0.0%
      12.1. Namespaces	9	0	
9	0.0%
      12.2. Scopes	46	0	
46	0.0%
      12.3. Preludes	28	0	
28	0.0%
      12.4. Paths	54	0	
54	0.0%
      12.5. Name resolution	0			
      12.6. Visibility and privacy	18	0	
18	0.0%
13. Memory model	6	0	
6	0.0%
      13.1. Memory allocation and lifetime	3	0	
3	0.0%
      13.2. Variables	6	0	
6	0.0%
14. Panic	21	0	
21	0.0%
15. Linkage	27	0	
27	0.0%
16. Inline assembly	117	0	
117	0.0%
17. Unsafety	11	0	
11	0.0%
      17.1. The unsafe keyword	16	0	
16	0.0%
      17.2. Behavior considered undefined	42	0	
42	0.0%
      17.3. Behavior not considered unsafe	0			
18. Constant Evaluation	40	0	
40	0.0%
19. Application Binary Interface	19	0	
19	0.0%
20. The Rust runtime	16	0	
16	0.0%
21. Appendices	0			
      21.1. Grammar summary	0			
      21.2. Macro Follow-Set Ambiguity Formal Specification	45	0	
45	0.0%
      21.3. Influences	0			
      21.4. Test summary	0			
      21.5. Glossary	0			
Total:	2797	53	2776	0.8%
## Glossary

Abstract syntax tree
An ‘abstract syntax tree’, or ‘AST’, is an intermediate representation of the structure of the program when the compiler is compiling it.
Alignment
The alignment of a value specifies what addresses values are preferred to start at. Always a power of two. References to a value must be aligned. More.
Arity
Arity refers to the number of arguments a function or operator takes. For some examples, f(2, 3) and g(4, 6) have arity 2, while h(8, 2, 6) has arity 3. The ! operator has arity 1.
Array
An array, sometimes also called a fixed-size array or an inline array, is a value describing a collection of elements, each selected by an index that can be computed at run time by the program. It occupies a contiguous region of memory.
Associated item
An associated item is an item that is associated with another item. Associated items are defined in implementations and declared in traits. Only functions, constants, and type aliases can be associated. Contrast to a free item.
Blanket implementation
Any implementation where a type appears uncovered. impl<T> Foo for T, impl<T> Bar<T> for T, impl<T> Bar<Vec<T>> for T, and impl<T> Bar<T> for Vec<T> are considered blanket impls. However, impl<T> Bar<Vec<T>> for Vec<T> is not a blanket impl, as all instances of T which appear in this impl are covered by Vec.
Bound
Bounds are constraints on a type or trait. For example, if a bound is placed on the argument a function takes, types passed to that function must abide by that constraint.
Combinator
Combinators are higher-order functions that apply only functions and earlier defined combinators to provide a result from its arguments. They can be used to manage control flow in a modular fashion.
Crate
A crate is the unit of compilation and linking. There are different types of crates, such as libraries or executables. Crates may link and refer to other library crates, called external crates. A crate has a self-contained tree of modules, starting from an unnamed root module called the crate root. Items may be made visible to other crates by marking them as public in the crate root, including through paths of public modules. More.
Dispatch
Dispatch is the mechanism to determine which specific version of code is actually run when it involves polymorphism. Two major forms of dispatch are static dispatch and dynamic dispatch. Rust supports dynamic dispatch through the use of trait objects.
Dynamically sized type
A dynamically sized type (DST) is a type without a statically known size or alignment.
Entity
An entity is a language construct that can be referred to in some way within the source program, usually via a path. Entities include types, items, generic parameters, variable bindings, loop labels, lifetimes, fields, attributes, and lints.
Expression
An expression is a combination of values, constants, variables, operators and functions that evaluate to a single value, with or without side-effects.
For example, 2 + (3 * 4) is an expression that returns the value 14.
Free item
An item that is not a member of an implementation, such as a free function or a free const. Contrast to an associated item.
Fundamental traits
A fundamental trait is one where adding an impl of it for an existing type is a breaking change. The Fn traits and Sized are fundamental.
Fundamental type constructors
A fundamental type constructor is a type where implementing a blanket implementation over it is a breaking change. &, &mut, Box, and Pin are fundamental.
Any time a type T is considered local, &T, &mut T, Box<T>, and Pin<T> are also considered local. Fundamental type constructors cannot cover other types. Any time the term “covered type” is used, the T in &T, &mut T, Box<T>, and Pin<T> is not considered covered.
Inhabited
A type is inhabited if it has constructors and therefore can be instantiated. An inhabited type is not “empty” in the sense that there can be values of the type. Opposite of Uninhabited.
Inherent implementation
An implementation that applies to a nominal type, not to a trait-type pair. More.
Inherent method
A method defined in an inherent implementation, not in a trait implementation.
Initialized
A variable is initialized if it has been assigned a value and hasn’t since been moved from. All other memory locations are assumed to be uninitialized. Only unsafe Rust can create a memory location without initializing it.
Local trait
A trait which was defined in the current crate. A trait definition is local or not independent of applied type arguments. Given trait Foo<T, U>, Foo is always local, regardless of the types substituted for T and U.
Local type
A struct, enum, or union which was defined in the current crate. This is not affected by applied type arguments. struct Foo is considered local, but Vec<Foo> is not. LocalType<ForeignType> is local. Type aliases do not affect locality.
Module
A module is a container for zero or more items. Modules are organized in a tree, starting from an unnamed module at the root called the crate root or the root module. Paths may be used to refer to items from other modules, which may be restricted by visibility rules. More
Name
A name is an identifier or lifetime or loop label that refers to an entity. A name binding is when an entity declaration introduces an identifier or label associated with that entity. Paths, identifiers, and labels are used to refer to an entity.
Name resolution
Name resolution is the compile-time process of tying paths, identifiers, and labels to entity declarations.
Namespace
A namespace is a logical grouping of declared names based on the kind of entity the name refers to. Namespaces allow the occurrence of a name in one namespace to not conflict with the same name in another namespace.
Within a namespace, names are organized in a hierarchy, where each level of the hierarchy has its own collection of named entities.
Nominal types
Types that can be referred to by a path directly. Specifically enums, structs, unions, and trait object types.
Dyn-compatible traits
Traits that can be used in trait object types (dyn Trait). Only traits that follow specific rules are dyn compatible.
These were formerly known as object safe traits.
Path
A path is a sequence of one or more path segments used to refer to an entity in the current scope or other levels of a namespace hierarchy.
Prelude
Prelude, or The Rust Prelude, is a small collection of items - mostly traits - that are imported into every module of every crate. The traits in the prelude are pervasive.
Scope
A scope is the region of source text where a named entity may be referenced with that name.
Scrutinee
A scrutinee is the expression that is matched on in match expressions and similar pattern matching constructs. For example, in match x { A => 1, B => 2 }, the expression x is the scrutinee.
Size
The size of a value has two definitions.
The first is that it is how much memory must be allocated to store that value.
The second is that it is the offset in bytes between successive elements in an array with that item type.
It is a multiple of the alignment, including zero. The size can change depending on compiler version (as new optimizations are made) and target platform (similar to how usize varies per-platform).
More.
Slice
A slice is dynamically-sized view into a contiguous sequence, written as [T].
It is often seen in its borrowed forms, either mutable or shared. The shared slice type is &[T], while the mutable slice type is &mut [T], where T represents the element type.
Statement
A statement is the smallest standalone element of a programming language that commands a computer to perform an action.
String literal
A string literal is a string stored directly in the final binary, and so will be valid for the 'static duration.
Its type is 'static duration borrowed string slice, &'static str.
String slice
A string slice is the most primitive string type in Rust, written as str. It is often seen in its borrowed forms, either mutable or shared. The shared string slice type is &str, while the mutable string slice type is &mut str.
Strings slices are always valid UTF-8.
Trait
A trait is a language item that is used for describing the functionalities a type must provide. It allows a type to make certain promises about its behavior.
Generic functions and generic structs can use traits to constrain, or bound, the types they accept.
Turbofish
Paths with generic parameters in expressions must prefix the opening brackets with a ::. Combined with the angular brackets for generics, this looks like a fish ::<>. As such, this syntax is colloquially referred to as turbofish syntax.
Examples:
let ok_num = Ok::<_, ()>(5);
let vec = [1, 2, 3].iter().map(|n| n * 2).collect::<Vec<_>>();
This :: prefix is required to disambiguate generic paths with multiple comparisons in a comma-separate list. See the bastion of the turbofish for an example where not having the prefix would be ambiguous.
Uncovered type
A type which does not appear as an argument to another type. For example, T is uncovered, but the T in Vec<T> is covered. This is only relevant for type arguments.
Undefined behavior
Compile-time or run-time behavior that is not specified. This may result in, but is not limited to: process termination or corruption; improper, incorrect, or unintended computation; or platform-specific results. More.
Uninhabited
A type is uninhabited if it has no constructors and therefore can never be instantiated. An uninhabited type is “empty” in the sense that there are no values of the type. The canonical example of an uninhabited type is the never type !, or an enum with no variants enum Never { }. Opposite of Inhabited.
