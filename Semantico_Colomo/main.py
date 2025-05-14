# main.py de prueba para el análisis semántico de C-

from globalTypes import *
from Parser import *
from Semantica import *

# Leer el archivo de entrada
f = open('testerTabla.txt', 'r')
programa = f.read()
progLong = len(programa)
programa = programa + '$'  # Agregar EOF
posicion = 0  # Inicializar la posición

# Pasar valores globales
globales(programa, posicion, progLong)

# Generar el AST
AST = parser(True)


# Ejecutar el análisis semántico
semantica(AST, True)
