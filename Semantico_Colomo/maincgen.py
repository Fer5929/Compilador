from globalTypes import *
from Parser import *
from Semantica import *
from cgen import *

f = open('prueba.txt', 'r')
programa = f.read()
progLong = len(programa)
programa = programa + '$'
posicion = 0

globales(programa, posicion, progLong)

AST = parser(True)
semantica(AST, True)
codeGen(AST, "prueba.s")