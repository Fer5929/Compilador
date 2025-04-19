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
    FunDecl = 10

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
        self.expresion = None
        self.sentencias = []
        self.condicion = None
        self.entonces = None
        self.sino = None
        self.tipo = None
        self.size = None
        #para funciones
        self.parametros = []
        self.cuerpo = None

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
        if arbol.exp == TipoExpresion.VarDecl:
            print(f'VarDecl: {arbol.tipo} {arbol.nombre}')
            if arbol.size:
                imprimeEspacios()
                print(f'Size: {arbol.size}')
        elif arbol.exp == TipoExpresion.FunDecl:
            print(f'FunDecl: {arbol.tipo} {arbol.nombre}')
            imprimeEspacios(); print('Parámetros:')
            for param in arbol.parametros:
                imprimeAST(param)
            imprimeEspacios(); print('Cuerpo:')
            imprimeAST(arbol.cuerpo)
        elif arbol.exp == TipoExpresion.Op:
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
        else:
            print('Nodo de tipo desconocido')
        if hasattr(arbol, 'hijoIzq') and arbol.hijoIzq:
            imprimeAST(arbol.hijoIzq)
        if hasattr(arbol, 'hijoDer') and arbol.hijoDer:
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


#args → [ arg-list ]
def args():
    global token
    lista = []
    if token != TokenType.RPAREN:
        lista.append(expression())
        while token == TokenType.COMMA:
            match(TokenType.COMMA)
            lista.append(expression())
    return lista


# compound-stmt → "{" declaration-list "}"
def compound_stmt():
    match(TokenType.LKEY)
    nodo = nuevoNodo(TipoExpresion.Compound)
    nodo.sentencias = []

    while token in (TokenType.INT, TokenType.VOID):
        nodo.sentencias.append(declaration())  # ← solo acepta var-declaration por ahora

    while token != TokenType.RKEY and token != TokenType.ENDFILE:
        nodo.sentencias.append(statement())

    match(TokenType.RKEY)
    return nodo

# selection-stmt → "if" "(" expression ")" statement [ "else" statement ]
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

# iteration-stmt → "while" "(" expression ")" statement
def iteration_stmt():
    nodo = nuevoNodo(TipoExpresion.While)
    match(TokenType.WHILE)
    match(TokenType.LPAREN)
    nodo.condicion = expression()
    match(TokenType.RPAREN)
    nodo.entonces = statement()
    return nodo

#return-stmt → "return" [ expression ] ";"
def return_stmt():
    nodo = nuevoNodo(TipoExpresion.Return)
    match(TokenType.RETURN)
    if token != TokenType.SEMICOLON:
        nodo.expresion = expression()
    match(TokenType.SEMICOLON)
    return nodo

# expression-stmt → [expression] ";"
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

# statement → expression-stmt | compound-stmt | selection-stmt | iteration-stmt | return-stmt
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

# expression → var = expression | simple-expression
def expression():
    global token, tokenString
    if token == TokenType.ID:
        nombre_id = tokenString

        if peek_EQ_or_index_or_call():
            match(TokenType.ID)
            if token == TokenType.LPAREN:
                return call(nombre_id)
            elif token == TokenType.LBRACKET:
                var_nodo = var(nombre_id)
                if token == TokenType.EQ:
                    nodo = nuevoNodo(TipoExpresion.Op)
                    nodo.op = '='
                    nodo.hijoIzq = var_nodo
                    match(TokenType.EQ)
                    nodo.hijoDer = expression()
                    return nodo
                return var_nodo
            elif token == TokenType.EQ:
                var_nodo = nuevoNodo(TipoExpresion.Var)
                var_nodo.nombre = nombre_id
                match(TokenType.EQ)
                nodo = nuevoNodo(TipoExpresion.Op)
                nodo.op = '='
                nodo.hijoIzq = var_nodo
                nodo.hijoDer = expression()
                return nodo

    return simple_expression()

def peek_EQ_or_index_or_call():
    return token in (TokenType.EQ, TokenType.LPAREN, TokenType.LBRACKET)

# simple-expression → additive-expression
# simple-expression → additive-expression ( relop additive-expression )?
# relop → < | <= | > | >= | == | !=
def simple_expression():
    print("📥 Entrando a simple_expression con token:", token, tokenString)
    t = additive_expression()
    if token in (TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE, TokenType.EQ, TokenType.NEQ,TokenType.EE):
        print("📍 RELACIONAL detectado:", token, tokenString)
        p = nuevoNodo(TipoExpresion.Op)
        p.hijoIzq = t
        p.op = tokenString
        match(token)
        print("📦 Después de relop, ahora token =", token, tokenString)
        p.hijoDer = additive_expression()
        return p
    else:
        return t

# additive-expression → term { addop term }
# addop → + | -
def additive_expression():
    print("🧮 Entrando a additive_expression con token:", token, tokenString)
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

#term  → factor { mulop factor }
# mulop → * | /
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

#factor → "(" expression ")" | number | ID
def factor():
    global token, tokenString

    if token == TokenType.LPAREN:
        match(TokenType.LPAREN)
        t = expression()
        match(TokenType.RPAREN)
        return t  

    elif token == TokenType.NUM:
        nodo = nuevoNodo(TipoExpresion.Const)
        nodo.val = tokenString
        match(TokenType.NUM)
        return nodo

    elif token == TokenType.ID:
        nombre_id = tokenString
        match(TokenType.ID)
        if token == TokenType.LPAREN:
            return call(nombre_id)
        elif token == TokenType.LBRACKET:
            return var(nombre_id)  # arreglo
        else:
            nodo = nuevoNodo(TipoExpresion.Var)
            nodo.nombre = nombre_id
            return nodo

    else:
        errorSintaxis("Expresión no válida en factor")


# call → ID "(" args ")"
def call(nombre_id):
    nodo = nuevoNodo(TipoExpresion.Call)
    nodo.nombre = nombre_id
    match(TokenType.LPAREN)
    nodo.args = args()
    match(TokenType.RPAREN)
    return nodo

# var → ID [ expression ]
def var(nombre_id):
    nodo = nuevoNodo(TipoExpresion.Var)
    nodo.nombre = nombre_id
    if token == TokenType.LBRACKET:
        match(TokenType.LBRACKET)
        nodo.indice = expression()
        match(TokenType.RBRACKET)
    return nodo

# args → expression { "," expression }
def args():
    lista = []
    if token != TokenType.RPAREN:
        lista.append(expression())
        while token == TokenType.COMMA:
            match(TokenType.COMMA)
            lista.append(expression())
    return lista

# declaration-list → declaration { declaration }
def declaration_list():
    lista = []
    while token in (TokenType.INT, TokenType.VOID):
        lista.append(declaration())
    return lista

# declaration → var-declaration | fun-declaration
def declaration():
    if token in (TokenType.INT, TokenType.VOID):
        tipo = tokenString
        match(token)
        nombre = tokenString
        match(TokenType.ID)
        if token == TokenType.LBRACKET or token == TokenType.SEMICOLON:
            return var_declaration(tipo, nombre)
        elif token == TokenType.LPAREN:
            return fun_declaration(tipo, nombre)
        else:
            errorSintaxis("Se esperaba ;, [, o ( en declaración")
    else:
        errorSintaxis("Se esperaba tipo de dato")

# var-declaration → type-specifier ID [ "[" NUM "]" ] ;
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


# fun-declaration → type-specifier ID ‘(’ params ‘)’ compound-stmt
def fun_declaration(tipo, nombre):
    nodo = nuevoNodo(TipoExpresion.FunDecl)
    nodo.tipo = tipo
    nodo.nombre = nombre
    match(TokenType.LPAREN)
    nodo.parametros = params()
    match(TokenType.RPAREN)
    nodo.cuerpo = compound_stmt()
    return nodo

# params → void | param-list
def params():
    lista = []
    if token == TokenType.VOID:
        match(TokenType.VOID)
        return lista
    elif token == TokenType.RPAREN:
        return lista
    else:
        lista.append(param())
        while token == TokenType.COMMA:
            match(TokenType.COMMA)
            lista.append(param())
    return lista

# param-list → param { , param }
# param → type-specifier ID ([ ])
def param():
    tipo = tokenString
    match(token)
    nombre = tokenString
    match(TokenType.ID)
    nodo = nuevoNodo(TipoExpresion.VarDecl)
    nodo.tipo = tipo
    nodo.nombre = nombre
    if token == TokenType.LBRACKET:
        match(TokenType.LBRACKET)
        match(TokenType.RBRACKET)
        nodo.size = '[]'
    return nodo

# program → { declaration }
def program():
    return declaration_list()

def match(expectedToken):
    global token, tokenString
    if token == expectedToken:
        token, tokenString = getToken()
    else:
        errorSintaxis(f"Se esperaba {expectedToken} pero se encontró {token}")

def parser(imprime=True):
    global token, tokenString, endentacion
    global programa
    global posicion
    global progLong
    token, tokenString = getToken()
    endentacion = 0

    AST = program()  # o statement(), o program(), según lo que estés probando

    if token != TokenType.ENDFILE:
        errorSintaxis("El archivo no terminó correctamente")

    if imprime:
        if isinstance(AST, list):
            for nodo in AST:
                imprimeAST(nodo)
        else:
            imprimeAST(AST)

    return AST
