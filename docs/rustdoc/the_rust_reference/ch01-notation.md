# Notation
[notation.grammar]
Grammar
[notation.grammar.syntax]
The following notations are used by the Lexer and Syntax grammar snippets:
Notation	Examples	Meaning
CAPITAL	KW_IF, INTEGER_LITERAL	A token produced by the lexer
ItalicCamelCase	LetStatement, Item	A syntactical production
string	x, while, *	The exact character(s)
x?	pub?	An optional item
x*	OuterAttribute*	0 or more of x
x+	MacroMatch+	1 or more of x
xa..b	HEX_DIGIT1..6	a to b repetitions of x
Rule1 Rule2	fn Name Parameters	Sequence of rules in order
|	u8 | u16, Block | Item	Either one or another
[ ]	[b B]	Any of the characters listed
[ - ]	[a-z]	Any of the characters in the range
~[ ]	~[b B]	Any characters, except those listed
~string	~\n, ~*/	Any characters, except this sequence
( )	(, Parameter)?	Groups items
U+xxxx	U+0060	A single unicode character
<text>	<any ASCII char except CR>	An English description of what should be matched
Rule suffix	IDENTIFIER_OR_KEYWORD except crate	A modification to the previous rule
Sequences have a higher precedence than | alternation.
[notation.grammar.string-tables]
String table productions
Some rules in the grammar — notably unary operators, binary operators, and keywords — are given in a simplified form: as a listing of printable strings. These cases form a subset of the rules regarding the token rule, and are assumed to be the result of a lexical-analysis phase feeding the parser, driven by a DFA, operating over the disjunction of all such string table entries.
When such a string in monospace font occurs inside the grammar, it is an implicit reference to a single member of such a string table production. See tokens for more information.
[notation.grammar.visualizations]
Grammar visualizations
Below each grammar block is a button to toggle the display of a syntax diagram. A square element is a non-terminal rule, and a rounded rectangle is a terminal.
