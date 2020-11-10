
grammar = r"""
goal            = (macro / def / core_syntax)*
core_syntax     = comment / byte_storage / word_storage / segment /
                  label / oper / _

comment         = ~r";\s*.*(?=\n|$)"

byte_storage    = ".byte" _ expr _ (comma _ expr _)*
word_storage    = ".word" _ expr _ (comma _ expr _)*

segment         = segment_name _ number?
segment_name    = ".zero" / ".text" / ".data" / ".bss"

include         = ".include" _ string

def             = ".def" _ ident _ expr

macro           = ".macro" _ macro_params _ macro_body _ ".endmacro"
macro_params    = ident _ (comma _ macro_params _)?
macro_body      = core_syntax*

label           = ident colon

expr8           = expr
expr16          = expr

# PEMDAS
expr            = sub / add / negate / lobyte / hibyte / term
negate          = minus _ term
lobyte          = lessthan _ term
hibyte          = morethan _ term
add             = term _ plus _ expr
sub             = term _ sub _ expr

term            = div / mul / exp
mul             = exp _ asterisk _ exp
div             = exp _ slash _ exp

exp = pow / fact
pow = fact carrot fact
fact = ident / string / number / group_expr

group_expr = lparen _ expr _ rparen

string          = quote (escapechar / stringchar)* quote
stringchar      = ~r'[^\"]+'
escapechar      = "\\" any

number          =  base2 / base16 / base10
base2           = "%" ~r"[01]{1,16}"
base16          = ~r"\$|0x" ~r"[0-9a-fA-F]{1,4}"
base10          = ~r"(\d+)"

ident           = ~r"[_a-zA-Z][_a-zA-Z0-9]*"

quote           = "\""
lparen          = "("
rparen          = ")"
plus            = "+"
minus           = "-"
slash           = "/"
carrot          = "^"
pipe            = "|"
ampersand       = "&"
comma           = ","
hash            = "#"
lessthan        = "<"
morethan        = ">"
colon           = ":"
asterisk        = "*"

any             = ~r"."
_              = ~r"\s*"

__ignored = "comment" / "quote" / "comma" / "hash" / "lparen" / "rparen" /
        "plus" / "minus" /
        "slash" / "carrot" / "pipe" / "ampersand" / "comma" / "hash" / "lessthan" /
        "morehtan" / "colon" / "asterisk" / "_"
"""

