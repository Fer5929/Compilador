from globalTypes import *
from Parser import *


f = open("euclides.txt", "r")
programa = f.read()
progLong = len(programa)
programa = programa + " $"
posicion = 0

globales(programa, posicion, progLong)

AST = parser(True)
