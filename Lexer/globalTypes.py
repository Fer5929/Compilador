#Sylvia Fernanda Colomo Fuente A01781983
from enum import Enum, auto


class TokenType(Enum):
    NUM = auto()
    ID = auto()
    ERROR = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    RETURN = auto()
    INT = auto()
    VOID = auto()
    PLUS = auto()
    MINUS = auto()
    MULT = auto()
    DIV = auto()
    LPAREN = auto()
    RPAREN = auto()
    LT = auto()
    GT = auto()
    LE = auto() #menor o igual que <=
    GE = auto() #mayor o igual que >=
    EQ = auto()
    NEQ = auto()
    EE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    COMMENT = auto() 
    LKEY = auto()#{
    RKEY = auto()#}
    ENDFILE = auto()
