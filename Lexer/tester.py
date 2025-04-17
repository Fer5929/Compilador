from globalTypes import *
from lexer import *


f = open('test.txt', 'r')
programa = f.read()
progLong = len(programa)
programa = programa + '$'  
print (programa[progLong])
posicion = 0


globales(programa, posicion, progLong)


token, tokenString = getToken(True)
while token != TokenType.ENDFILE:
    token, tokenString = getToken(True)
