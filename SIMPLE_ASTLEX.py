# Versión mejorada de SIMPLE_ASTLEX.py usando la gramática EBNF completa para expresiones aritméticas y sentencias

from enum import Enum
from lexer import *
from globalTypes import *

class TipoExpresion(Enum):
    Op = 0
    Const = 1
    Var = 2
    Call = 3
    Return = 4
    ExprStmt = 5
    Compound = 6
    If = 7
    While = 8
    VarDecl = 9 

class NodoArbol:
    def __init__(self):
        self.hijoIzq = None
        self.hijoDer = None
        self.exp = None
        self.op = None
        self.val = None
        self.nombre = None
        self.args = []
        self.indice = None

        # Para sentencias
        self.stmtTipo = None

        # Para return y exprstmt
        self.expresion = None

        # Para compound
        self.sentencias = []

        # Para if y while
        self.condicion = None
        self.entonces = None
        self.sino = None

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
        elif arbol.exp == TipoExpresion.Var:
            print(f'Var: {arbol.nombre}')
            if arbol.indice:
                imprimeAST(arbol.indice)
        elif arbol.exp == TipoExpresion.Call:
            print(f'Call: {arbol.nombre}')
            for arg in arbol.args:
                imprimeAST(arg)
        elif arbol.exp == TipoExpresion.Return:
            print('Return')
            imprimeAST(arbol.expresion)
        elif arbol.exp == TipoExpresion.ExprStmt:
            print('ExprStmt')
            imprimeAST(arbol.expresion)
        elif arbol.exp == TipoExpresion.Compound:
            print('CompoundStmt')
            for stmt in arbol.sentencias:
                imprimeAST(stmt)
        elif arbol.exp == TipoExpresion.If:
            print('If')
            imprimeEspacios(); print('Condición:')
            imprimeAST(arbol.condicion)
            imprimeEspacios(); print('Entonces:')
            imprimeAST(arbol.entonces)
            if arbol.sino:
                imprimeEspacios(); print('Sino:')
                imprimeAST(arbol.sino)
        elif arbol.exp == TipoExpresion.While:
            print('While')
            imprimeEspacios(); print('Condición:')
            imprimeAST(arbol.condicion)
            imprimeEspacios(); print('Cuerpo:')
            imprimeAST(arbol.entonces)
        elif arbol.exp == TipoExpresion.VarDecl:
            print(f'VarDecl: {arbol.tipo} {arbol.nombre}')
            if hasattr(arbol, 'size'):
                imprimeEspacios()
                print(f'size: {arbol.size}')
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
        t = expression()
        match(TokenType.RPAREN)
    elif token == TokenType.NUM:
        t = nuevoNodo(TipoExpresion.Const)
        t.val = tokenString
        match(TokenType.NUM)
    elif token == TokenType.ID:
        nombre_id = tokenString
        match(TokenType.ID)
        if token == TokenType.LPAREN:
            t = call(nombre_id)
        else:
            t = var(nombre_id)
    else:
        errorSintaxis('Expresión no válida en factor')
    return t

def var(nombre_id):
    nodo = nuevoNodo(TipoExpresion.Var)
    nodo.nombre = nombre_id
    if token == TokenType.LBRACKET:
        match(TokenType.LBRACKET)
        nodo.indice = expression()
        match(TokenType.RBRACKET)
    return nodo

def call(nombre_id):
    nodo = nuevoNodo(TipoExpresion.Call)
    nodo.nombre = nombre_id
    match(TokenType.LPAREN)
    nodo.args = args()
    match(TokenType.RPAREN)
    return nodo

def args():
    global token
    lista = []
    if token != TokenType.RPAREN:
        lista.append(expression())
        while token == TokenType.COMMA:
            match(TokenType.COMMA)
            lista.append(expression())
    return lista

def term():
    global token
    t = factor()
    while token in (TokenType.MULT, TokenType.DIV):
        p = nuevoNodo(TipoExpresion.Op)
        p.hijoIzq = t
        if token == TokenType.MULT:
            p.op = '*'
            match(TokenType.MULT)
        else:
            p.op = '/'
            match(TokenType.DIV)
        p.hijoDer = factor()
        t = p
    return t

def additive_expression():
    global token
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

def simple_expression():
    return additive_expression()

def expression():
    return simple_expression()

def expression_stmt():
    global token
    if token == TokenType.SEMICOLON:
        match(TokenType.SEMICOLON)
        nodo = nuevoNodo(TipoExpresion.ExprStmt)
        nodo.expresion = None
    else:
        nodo = nuevoNodo(TipoExpresion.ExprStmt)
        nodo.expresion = expression()
        match(TokenType.SEMICOLON)
    return nodo

def return_stmt():
    global token
    nodo = nuevoNodo(TipoExpresion.Return)
    match(TokenType.RETURN)
    if token != TokenType.SEMICOLON:
        nodo.expresion = expression()
    match(TokenType.SEMICOLON)
    return nodo

...

def compound_stmt():
    match(TokenType.LKEY)
    nodo = nuevoNodo(TipoExpresion.Compound)
    nodo.sentencias = []
    while token != TokenType.RKEY and token != TokenType.ENDFILE:
        nodo.sentencias.append(statement())
    match(TokenType.RKEY)
    return nodo

def selection_stmt():
    nodo = nuevoNodo(TipoExpresion.If)
    match(TokenType.IF)
    match(TokenType.LPAREN)
    nodo.condicion = expression()
    match(TokenType.RPAREN)
    nodo.entonces = statement()
    if token == TokenType.ELSE:
        match(TokenType.ELSE)
        nodo.sino = statement()
    return nodo

def iteration_stmt():
    nodo = nuevoNodo(TipoExpresion.While)
    match(TokenType.WHILE)
    match(TokenType.LPAREN)
    nodo.condicion = expression()
    match(TokenType.RPAREN)
    nodo.entonces = statement()
    return nodo

def return_stmt():
    nodo = nuevoNodo(TipoExpresion.Return)
    match(TokenType.RETURN)
    if token != TokenType.SEMICOLON:
        nodo.expresion = expression()
    match(TokenType.SEMICOLON)
    return nodo

def expression_stmt():
    if token == TokenType.SEMICOLON:
        match(TokenType.SEMICOLON)
        nodo = nuevoNodo(TipoExpresion.ExprStmt)
        nodo.expresion = None
    else:
        nodo = nuevoNodo(TipoExpresion.ExprStmt)
        nodo.expresion = expression()
        match(TokenType.SEMICOLON)
    return nodo

def statement():
    if token == TokenType.IF:
        return selection_stmt()
    elif token == TokenType.WHILE:
        return iteration_stmt()
    elif token == TokenType.RETURN:
        return return_stmt()
    elif token == TokenType.LKEY:
        return compound_stmt()
    else:
        return expression_stmt()

def expression():
    return simple_expression()

def simple_expression():
    return additive_expression()

def additive_expression():
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

def term():
    t = factor()
    while token in (TokenType.MULT, TokenType.DIV):
        p = nuevoNodo(TipoExpresion.Op)
        p.hijoIzq = t
        if token == TokenType.MULT:
            p.op = '*'
            match(TokenType.MULT)
        else:
            p.op = '/'
            match(TokenType.DIV)
        p.hijoDer = factor()
        t = p
    return t

def factor():
    global tokenString
    if token == TokenType.LPAREN:
        match(TokenType.LPAREN)
        t = expression()
        match(TokenType.RPAREN)
    elif token == TokenType.NUM:
        t = nuevoNodo(TipoExpresion.Const)
        t.val = tokenString
        match(TokenType.NUM)
    elif token == TokenType.ID:
        nombre_id = tokenString
        match(TokenType.ID)
        if token == TokenType.LPAREN:
            t = call(nombre_id)
        else:
            t = var(nombre_id)
    else:
        errorSintaxis('Expresión no válida en factor')
    return t

def call(nombre_id):
    nodo = nuevoNodo(TipoExpresion.Call)
    nodo.nombre = nombre_id
    match(TokenType.LPAREN)
    nodo.args = args()
    match(TokenType.RPAREN)
    return nodo

def var(nombre_id):
    nodo = nuevoNodo(TipoExpresion.Var)
    nodo.nombre = nombre_id
    if token == TokenType.LBRACKET:
        match(TokenType.LBRACKET)
        nodo.indice = expression()
        match(TokenType.RBRACKET)
    return nodo

def args():
    lista = []
    if token != TokenType.RPAREN:
        lista.append(expression())
        while token == TokenType.COMMA:
            match(TokenType.COMMA)
            lista.append(expression())
    return lista
def declaration():
    if token in (TokenType.INT, TokenType.VOID):
        tipo = tokenString
        match(token)
        nombre = tokenString
        match(TokenType.ID)
        if token == TokenType.SEMICOLON or token == TokenType.LBRACKET:
            return var_declaration(tipo, nombre)
        else:
            errorSintaxis("Se esperaba declaración de variable")
    else:
        errorSintaxis("Se esperaba tipo de dato (int o void)")

def var_declaration(tipo, nombre):
    nodo = nuevoNodo(TipoExpresion.VarDecl)
    nodo.nombre = nombre
    nodo.tipo = tipo
    if token == TokenType.LBRACKET:
        match(TokenType.LBRACKET)
        nodo.size = tokenString
        match(TokenType.NUM)
        match(TokenType.RBRACKET)
    match(TokenType.SEMICOLON)
    return nodo

def match(expectedToken):
    global token, tokenString
    if token == expectedToken:
        token, tokenString = getToken()
    else:
        errorSintaxis(f"Se esperaba {expectedToken} pero se encontró {token}")

def parser(imprime=True):
    global token, tokenString, endentacion
    token, tokenString = getToken()
    AST = statement()
    if token != TokenType.ENDFILE:
        errorSintaxis("El archivo no terminó correctamente")
    elif imprime:
        endentacion = 0
        imprimeAST(AST)
    return AST
