# Gramática:
# exp     → term { opsuma term }
# opsuma  → + | -
# term    → factor { opmult factor }
# opmult  → *
# factor  → ( exp ) | numero

from enum import Enum
from lexer import *  # Usa tu lexer original
from globalTypes import *  # Asegúrate de que TokenType está aquí

class TipoExpresion(Enum):
    Op = 0
    Const = 1

class NodoArbol:
    def __init__(self):
        self.hijoIzq = None
        self.hijoDer = None
        self.exp = None
        self.op = None
        self.val = None

def nuevoNodo(tipo):
    t = NodoArbol()
    t.exp = tipo
    return t

def errorSintaxis(mensaje):
    print(f'>>>>> Error de sintaxis: {mensaje}')
    exit()

def imprimeEspacios():
    print(' ' * endentacion, end='')

def imprimeAST(arbol):
    global endentacion
    endentacion += 2
    if arbol is not None:
        imprimeEspacios()
        if arbol.exp == TipoExpresion.Op:
            print(f'Op: {arbol.op}')
        elif arbol.exp == TipoExpresion.Const:
            print(f'Const: {arbol.val}')
        else:
            print('Nodo de tipo desconocido')
        imprimeAST(arbol.hijoIzq)
        imprimeAST(arbol.hijoDer)
    endentacion -= 2

def match(expectedToken):
    global token, tokenString
    if token == expectedToken:
        token, tokenString = getToken()
    else:
        errorSintaxis(f"Se esperaba {expectedToken} pero se encontró {token}")

def factor():
    global token, tokenString
    if token == TokenType.LPAREN:
        match(TokenType.LPAREN)
        t = exp()
        match(TokenType.RPAREN)
    elif token == TokenType.NUM:
        t = nuevoNodo(TipoExpresion.Const)
        t.val = tokenString
        match(TokenType.NUM)
    else:
        errorSintaxis('Expresión no válida en factor')
    return t

def term():
    global token, tokenString
    t = factor()
    while token == TokenType.MULT:
        p = nuevoNodo(TipoExpresion.Op)
        p.hijoIzq = t
        p.op = '*'
        match(TokenType.MULT)
        p.hijoDer = factor()
        t = p
    return t

def exp():
    global token, tokenString
    t = term()
    while token in (TokenType.PLUS, TokenType.MINUS):
        p = nuevoNodo(TipoExpresion.Op)
        p.hijoIzq = t
        if token == TokenType.PLUS:
            p.op = '+'
            match(TokenType.PLUS)
        else:
            p.op = '-'
            match(TokenType.MINUS)
        p.hijoDer = term()
        t = p
    return t

# 👇 Esta es la función que el script de prueba va a llamar
def parser(imprime=True):
    global token, tokenString, endentacion
    token, tokenString = getToken()
    AST = exp()

    if token != TokenType.ENDFILE:
        errorSintaxis("El archivo no terminó correctamente")
    elif imprime:
        endentacion = 0
        imprimeAST(AST)

    return AST
#se llama con el tester del Victor  que en mi caso se llama testerAST.py y se llama con 2+8^6