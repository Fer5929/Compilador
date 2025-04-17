from globalTypes import *
from SIMPLE_ASTLEX import *


f = open("testerASTSimple.txt", "r")
programa = f.read()
progLong = len(programa)
programa = programa + " $"
posicion = 0

globales(programa, posicion, progLong)

AST = parser(True)
