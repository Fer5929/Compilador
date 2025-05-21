#Sylvia Fernanda Colomo Fuente A01781983
from globalTypes import *

linea = 1
inicioLinea = 0
posicionTokenActual = 0
errorToken=False
lexer_error = False  # Bandera global de error
#Funcion para inicializar las variables globales como pedida en las instrucciones
#Se hizo el cambio de nombre de función para que no se confunda con la función de globales
#Como referencia de este cambio se revisó la parte de el scanner.py y parser.py para TINY proporcionados
def recibeLexer(prog, pos, long):
    global programa #corresponde al programa en un string
    global posicion #corresponde a la posicion siguiente del caracter a leer dentro del string
    global progLong #corresponde a la longitud del programa
    programa = prog
    posicion = pos
    progLong = long

#Funcion para obtener los tokens
def getToken(imprime=True):
    global programa
    global posicion
    global progLong
    global linea
    global inicioLinea
    global posicionTokenActual 
    progLong = len(programa)
    #agrega un espacio en blanco antes del $ para que el lexer lo reconozca como un fin de archivo
    if programa.endswith('$') and progLong >= 2 and programa[-2] not in [' ', '\t', '\n']:
        programa = programa[:-1] + ' $'
        progLong = len(programa)
    # Ignorar espacios en blanco
    while posicion < progLong and programa[posicion] in [' ', '\t', '\n']:
        if programa[posicion] == '\n':
            #Linea guarda el numero de linea actual del programa para poder imprimirlo en caso de error
            linea += 1
            inicioLinea = posicion + 1 #posicion de inicio de la linea va ir avanzando
        posicion += 1
    posicionTokenActual = posicion 

    #Revisa por el fin de archivo 
    #print('la posicion es', posicion , 'la longitud es', progLong)
    if posicion >= progLong or programa[posicion] == '$':
        #if imprime:
            #print('$ =', TokenType.ENDFILE)
        token = TokenType.ENDFILE
        token.linea = linea
        return token, '$'
    
    #Se llama a reconocer para obtener el token y el lexema
    token, lexema = reconocer()
    if token == TokenType.COMMENT:
        return getToken(imprime)

    #Variable de imprime que sirve dado que si es true imprime el token y el lexema 
    #if imprime and token != TokenType.COMMENT:
        #print(lexema, "=", token)
    
    # Attach line number to token
    token.linea = linea
    return token, lexema
    



#Esta función reconoce los tokens para C- y se basa en if´s para simular un DFA
def reconocer():
    global programa 
    global posicion
    global progLong
    global linea
    global inicioLinea
    global lexer_error

    estado = 0
    lexema = ''

    digitos = ['0','1','2','3','4','5','6','7','8','9'] #lista de numeros posibles 
    letras = [
        'a','b','c','d','e','f','g','h','i','j','k','l','m',
        'n','o','p','q','r','s','t','u','v','w','x','y','z',
        'A','B','C','D','E','F','G','H','I','J','K','L','M',
        'N','O','P','Q','R','S','T','U','V','W','X','Y','Z'
    ] #lista de letras posibles

    palabrasReservadas = {
        'if': TokenType.IF, 'else': TokenType.ELSE, 'while': TokenType.WHILE,
        'return': TokenType.RETURN, 'int': TokenType.INT, 'void': TokenType.VOID
    }#diccionario de palabras reservadas

    separadores = [' ', '\t', '\n', '\r']#lista de separadores
    simbolos_validos = ['+', '-', '*', '/', '(', ')', '[', ']', '{', '}', '<', '>', '=', '!', ',', ';']
    while posicion < progLong:#mientras la posicion sea menor a la longitud del programa se revisará todo el programa
        c = programa[posicion]

        if estado == 0:#estado inicial
            if c in digitos: #si hay un digito se pasa al estado 1
                estado = 1
                lexema += c
                posicion += 1
            elif c in letras: #si hay una letra se pasa al estado 2
                estado = 2
                lexema += c
                posicion += 1
            elif c == '+': #si hay un + se pasa al estado 3
                estado = 3
                lexema += c
                posicion += 1
            elif c == '-': #si hay un - se pasa al estado 4
                estado = 4
                lexema += c
                posicion += 1
            elif c == '*': #si hay un * se pasa al estado 5
                estado = 5
                lexema += c
                posicion += 1
            elif c == '/':
                if posicion + 1 < progLong and programa[posicion + 1] == '*':
                # Inicio de comentario
                    estado = 20
                    lexema += c
                    posicion += 1
                    lexema += programa[posicion]
                    posicion += 1
                else: #siginifca que es un DIV y no un inicio de comentario
                    estado = 6
                    lexema += c
                    posicion += 1
            elif c == '(': #si hay un ( se pasa al estado 7
                estado = 7
                lexema += c
                posicion += 1
            elif c == ')': #si hay un ) se pasa al estado 8
                estado = 8
                lexema += c
                posicion += 1
            elif c == '<': #si hay un < se pasa al estado 9
                estado = 9
                lexema += c
                posicion += 1
                if posicion < progLong and programa[posicion] == '=':
                    #si hay un = despues del < se pasa al estado 11 para el <=
                    estado = 11 
                    lexema += programa[posicion]
                    posicion += 1
            elif c == '>': #si hay un > se pasa al estado 10
                estado = 10
                lexema += c
                posicion += 1
                if posicion < progLong and programa[posicion] == '=':
                    #si hay un = despues del > se pasa al estado 12 para el >=
                    estado = 12
                    lexema += programa[posicion]
                    posicion += 1
            elif c == '>=': #si hay un >= se pasa al estado 12
                estado = 12
                lexema += c
                posicion += 1
            elif c == '=': #si hay un = se pasa al estado 13
                estado = 13
                lexema += c
                posicion += 1
                if posicion < progLong and programa[posicion] == '=':
                    estado = 15
                    lexema += programa[posicion]
                    posicion += 1
            elif c == '!': #si hay un ! se pasa al estado 14
                lexema += c
                posicion += 1
                if posicion < progLong and programa[posicion] == '=':
                    #si hay un = despues del ! se pasa al estado 14 para el !=
                    estado = 14
                    lexema += programa[posicion]
                    posicion += 1
                else: #significa que es un ! y no un != entonces es un error
                    estado = 99
                    posicionError = posicion-1
                    
            elif c == '[': #si hay un [ se pasa al estado 16
                estado = 16
                lexema += c
                posicion += 1
            elif c == ']': #si hay un ] se pasa al estado 17
                estado = 17
                lexema += c
                posicion += 1
            elif c == ';': #si hay un ; se pasa al estado 18
                estado = 18
                lexema += c
                posicion += 1
            elif c == ',': #si hay un , se pasa al estado 19
                estado = 19
                lexema += c
                posicion += 1
            elif c == '{': #si hay un { se pasa al estado 20
                estado = 24
                lexema += c
                posicion += 1
            elif c == '}': #si hay un } se pasa al estado 21
                estado = 25
                lexema += c
                posicion += 1
            #cualquier caracter no definido en C- 
            elif c not in separadores and c not in simbolos_validos and not c in digitos and not c in letras:
                estado = 99
                posicionError = posicion
                lexema += c
                posicion += 1
            else:
                break

        elif estado == 1:
            if c in digitos: #si hay un digito se pasa al estado 1, se quedará en el mismo estado si siguen numeros 
                lexema += c
                posicion += 1
            elif c in letras or c == '!': #si hay una letra se pasa al estado 99
                estado = 99
                posicionError = posicion
                lexema += c
                posicion += 1
            elif c not in letras and c not in digitos and c not in simbolos_validos and c not in separadores:
                estado = 99
                posicionError = posicion
                lexema += c
                posicion += 1
            else:
                break

        elif estado == 2:
            if c in letras : #si hay una letra se pasa al estado 2, se quedará en el mismo estado si siguen letras
                lexema += c
                posicion += 1
            elif  c == '!'or c in digitos: #si hay un ! solo
                estado = 99
                posicionError = posicion    
                lexema += c
                posicion += 1
            elif c not in letras and c not in digitos and c not in simbolos_validos and c not in separadores:
                estado = 99
                posicionError = posicion
                lexema += c
                posicion += 1
            else:
                break

        elif estado == 3:
            return TokenType.PLUS, lexema
        elif estado == 4:
            return TokenType.MINUS, lexema
        elif estado == 5:
            return TokenType.MULT, lexema
        elif estado == 6:
            return TokenType.DIV, lexema
        elif estado == 7:
            return TokenType.LPAREN, lexema
        elif estado == 8:
            return TokenType.RPAREN, lexema
        elif estado == 9:
            return TokenType.LT, lexema
        elif estado == 10:
            return TokenType.GT, lexema
        elif estado == 11:
            return TokenType.LE, lexema
        elif estado == 12:
            return TokenType.GE, lexema
        elif estado == 13:
            return TokenType.EQ, lexema
        elif estado == 14:
            return TokenType.NEQ, lexema
        elif estado == 15:
            return TokenType.EE, lexema
        elif estado == 16:
            return TokenType.LBRACKET, lexema
        elif estado == 17:
            return TokenType.RBRACKET, lexema
        elif estado == 18:
            return TokenType.SEMICOLON, lexema
        elif estado == 19:
            return TokenType.COMMA, lexema
        elif estado == 20: #comentario
            while posicion < progLong:#revisa todo hasta el fin del programa
                c = programa[posicion]
                lexema += c

                if c == '\n':#si hay un salto de línea aun considera el comentario pero hacemos los aumentos del contador 
                    linea += 1
                    inicioLinea = posicion + 1

                if c == '*' and posicion + 1 < progLong and programa[posicion + 1] == '/':
                    #si encuentra el cierre */ significa que si es un comentario y se regresa el token
                    lexema += programa[posicion + 1]
                    posicion += 2
                    return TokenType.COMMENT, lexema

                posicion += 1

                # no hubo cierre de comentario y por lo tanto es un error
            posicionError = posicion-1
            estado = 99
        elif estado == 24:
            return TokenType.LKEY, lexema
        elif estado == 25:
            return TokenType.RKEY, lexema
        elif estado == 99:
            break

    if estado == 1:
        return TokenType.NUM, lexema

    elif estado == 2:
        if lexema in palabrasReservadas: #si la palabra es una palabra reservada 
            return palabrasReservadas[lexema], lexema
        else:
            return TokenType.ID, lexema

    #Si el estado es 99, significa que hay un error
    elif estado == 99:
        lexer_error = True
        while posicion < progLong:
            c = programa[posicion]
            if c in separadores:
                break
            else:
                lexema += c
                posicion += 1

 
    #La finalidad del código es imprimir el error desde la posición donde rompió la regla
        inicioErrorLinea = programa.rfind('\n', 0, posicionError)#busca el salto de linea
        if inicioErrorLinea == -1:#si no hay salto de linea entonces inicioErrorLinea es 0
            inicioErrorLinea = 0
        else:
            inicioErrorLinea += 1 #de lo contrario se aumenta en 1

        finErrorLinea = programa.find('\n', posicionError)#busca el salto de linea en la posicion donde rompió la regla
        if finErrorLinea == -1:#si no hay salto de linea entonces finErrorLinea es la longitud del programa
            finErrorLinea = progLong

        contenido = programa[inicioErrorLinea:finErrorLinea]#se toma el contenido de la linea(s)
        pos_error = posicionError - inicioErrorLinea#se calcula la posicion del error para el ^



        print(f"Línea {linea}: Error en la formación de un token:")
        print(contenido)
        print(" " * pos_error + "^")
        return TokenType.ERROR, lexema
    else:
        return TokenType.ERROR, ''
    
#Función nueva para pasar los datos del error al parser 
def info_error():
    global programa, progLong, posicionTokenActual, errorToken

    linea = programa.count('\n', 0, posicionTokenActual) + 1

    # Encontrar el último token válido antes del error
    posicionTokenAnterior = posicionTokenActual - 1
    while posicionTokenAnterior >= 0 and programa[posicionTokenAnterior].isspace():
        posicionTokenAnterior -= 1

    inicioErrorLinea = programa.rfind('\n', 0, posicionTokenActual)
    if inicioErrorLinea == -1:
        inicioErrorLinea = 0
    else:
        inicioErrorLinea += 1

    finErrorLinea = programa.find('\n', posicionTokenActual)
    if finErrorLinea == -1:
        finErrorLinea = progLong

    contenido = programa[inicioErrorLinea:finErrorLinea]
    pos_error = posicionTokenActual - inicioErrorLinea 

    # Obtener contenido de la línea anterior
    inicioLineaAnterior = programa.rfind('\n', 0, inicioErrorLinea-1)
    if inicioLineaAnterior == -1:
        inicioLineaAnterior = 0
    else:
        inicioLineaAnterior += 1
    contenido_anterior = programa[inicioLineaAnterior:inicioErrorLinea-1]

    return linea, contenido, pos_error, inicioErrorLinea, finErrorLinea, posicionTokenAnterior, posicionTokenActual, contenido_anterior


