# exp -> term { opsuma term }
# opsuma -> + | -
# term -> factor { opmult factor }
# opmult -> * 
# factor -> ( exp ) | numero 

from enum import Enum 
from lexer import *
class TipoExpresion(Enum):
    #tipos de expresiones de la gramatica operadores + - * y constantes
    Op=0 
    Const=1

class NodoArbol:
    def __init__(self):
        #un nodo tiene un hijo izquierdo y un hijo derecho
        self.hijoIzq=None
        self.hijoDer=None
        #un nodo puede ser una expresion o una constante
        self.exp=None
        self.op=None
        self.val=None

def nuevoNodo(tipo):
    t=NodoArbol()
    if (t==None):
        print ("No hay memoria")
    else:
        t.exp=tipo
    return t

def errorSintaxis(mensaje):
    print ('>>>>> Error de sintaxis: ', mensaje)

#Mostrar el arbol 
def imprimeEspacios():
    print (' ' * endentacion, end='')

def imprimeAST(arbol):
    global endentacion
    endentacion += 2 #endentacion
    if arbol != None:
        imprimeEspacios()
        if arbol.exp == TipoExpresion.Op:
            print ('Op: ', arbol.op)
        elif arbol.exp == TipoExpresion.Const:
            print('Const: ', arbol.val,' ')
        else:
            print('ExpNodo de tipo desconocido')
        imprimeAST(arbol.hijoIzq)
        imprimeAST(arbol.hijoDer)
    endentacion -= 2 #decremento de endentacion

def match(tok):
    global ne_xt, pos
    if ne_xt==tok:
        pos +=1
        if pos == len(cadena):
            ne_xt= '$'
        else:
            ne_xt=cadena[pos]
    else:
        errorSintaxis('Token no esperado')

#Definiciones de las funciones de la gramatica

# exp -> term { opsuma term }
def exp():
    t=term()
    while ne_xt in '+-': #token traido por lexer
        p=nuevoNodo(TipoExpresion.Op)
        p.hijoIzq=t
        p.op=ne_xt
        t=p
        match(ne_xt)
        t.hijoDer=term()
    return t

# term -> factor { opmult factor }
def term():
    t=factor()
    while ne_xt in '*': #token traido por lexer
        p=nuevoNodo(TipoExpresion.Op)
        p.hijoIzq=t
        p.op=ne_xt
        t=p
        match(ne_xt)
        t.hijoDer=factor()
    return t

# factor -> ( exp ) | numero 
def factor():
    if ne_xt == '(':
        match('(')
        t=exp()
        match(')')
    elif ne_xt in '0123456789': #token traido por lexer
        t=nuevoNodo(TipoExpresion.Const)
        t.val=(ne_xt)
        match(ne_xt)
    else:
        errorSintaxis('Expresion no valida')
    return t

cadena=input('Ingrese la expresion: ')
pos=0
ne_xt=cadena[pos]
AST = exp()
endentacion =0
if ne_xt != '$':
    errorSintaxis('El código termina antes que el archivo')
else:
    imprimeAST(AST)