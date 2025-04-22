from globalTypes import *
from Parser import *


f = open("euclides.txt", "r")#archivo de prueba
programa = f.read()
progLong = len(programa)
programa = programa + " $"
posicion = 0

globales(programa, posicion, progLong) #funcion para pasar los datos a parser

AST = parser(True)
