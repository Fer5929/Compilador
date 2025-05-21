#Analizador Semantico para C- 
#Sylvia Fernanda Colomo Fuente
#A01781983

from globalTypes import *
from lexer import *
from Parser import *

current_function_type = None
semantic_error = False  # Bandera global de error
#Variables globales para el analizador semantico
def globales(prog, pos, long):
    global programa
    global posicion
    global progLong
    programa = prog
    posicion = pos
    progLong = long
    recibeParser(programa, posicion, progLong)

#Clase símbolo para la tabla de símbolos
class Symbol:
    def __init__(self, name, sym_type, data_type, is_array=False, size=None, linea=None, parametros=None):
        self.name = name #nombre 
        self.sym_type = sym_type  # puede ser una variable, una función o un parámetro
        self.data_type = data_type  # int o void
        self.is_array = is_array #true si es un arreglo
        self.size = size #tamaño del arreglo
        self.linea = linea if linea is not None else '?' #línea del código
        self.references = [] #referencias a la variable
        self.parametros = parametros or []  # Nueva lista para funciones
        self.param = False

#Clase para la tabla de símbolos
class SymbolTable:
    def __init__(self, scope_name, parent=None):
        self.scope_name = scope_name
        self.symbols = {}
        self.parent = parent
        self.children = []

    #insertar un símbolo en la tabla de símbolos
    def insert(self, symbol):
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True
    #buscar un símbolo en la tabla de símbolos
    def lookup(self, name):
        t = self
        while t:
            if name in t.symbols:
                return t.symbols[name]
            t = t.parent
        return None
    #imprimir la tabla de símbolos
    def __str__(self):
        out = f"\nScope: {self.scope_name}"
        out += f"\n{'Nombre':<12} | {'Tipo':<6} | {'Parámetros':<20} | {'Es Array':<9} | {'Size':<5} | {'Línea':<5}"
        out += f"\n{'-'*12}-+-{'-'*6}-+-{'-'*20}-+-{'-'*9}-+-{'-'*5}-+-{'-'*5}"
        for sym in self.symbols.values():
            if sym.name in ["input", "output"]:
                continue  # ocultar input/output
            params = ', '.join(sym.parametros) if sym.sym_type == "fun" else "–"
            size_str = ( #imprimir el tamaño del arreglo
                "void" if sym.is_array and (sym.size is None or sym.size == '[]') else
                str(sym.size) if sym.is_array else
                "–"
                )
            out += f"\n{sym.name:<12} | {sym.data_type:<6} | {params:<20} | {str(sym.is_array):<9} | {size_str:<5} | {str(sym.linea):<5}"
        return out

#Función para construir la tabla de símbolos
def tabla(tree, imprime=True):
    global current_scope
    current_scope = SymbolTable("global")

    # Funciones predefinidas
    current_scope.insert(Symbol("input", "fun", "int", False, None, 0))
    current_scope.insert(Symbol("output", "fun", "void", False, None, 0))

    for nodo in tree: #recorrer el árbol sintáctico
        recorrer(nodo)
    if imprime:
        imprimir_tablas(current_scope)
    return current_scope

#imprimir la tabla de símbolos
def imprimir_tablas(tabla, nivel=0):
    print("  " * nivel + str(tabla))
    for hijo in tabla.children:
        imprimir_tablas(hijo, nivel + 1)

# Función para manejar errores semánticos con el mismo formato que el parser
#Se obtuvo el apoyo de copilot para la implementación de esta función
def errorSemantico(mensaje, linea, nombre=None):
    global semantic_error
    semantic_error = True  # <-- Marca error
    
    # Encontrar la posición del error en el programa
    posicionError = 0
    lineas = programa.split('\n')
    if linea <= len(lineas):
        # Buscar la posición del identificador en la línea
        if nombre:
            posicionError = lineas[linea-1].find(nombre)
            if posicionError == -1:  # Si no encuentra el nombre, usar el inicio de la línea
                posicionError = 0
        else:
            posicionError = 0
            
        # Calcular la posición absoluta en el programa
        posicionAbsoluta = sum(len(l) + 1 for l in lineas[:linea-1]) + posicionError
        
        # Obtener información de la línea anterior
        inicioLineaAnterior = programa.rfind('\n', 0, posicionAbsoluta-1)
        if inicioLineaAnterior == -1:
            inicioLineaAnterior = 0
        else:
            inicioLineaAnterior += 1
            
        # Obtener el contenido de la línea actual
        inicioErrorLinea = programa.rfind('\n', 0, posicionAbsoluta)
        if inicioErrorLinea == -1:
            inicioErrorLinea = 0
        else:
            inicioErrorLinea += 1
            
        finErrorLinea = programa.find('\n', posicionAbsoluta)
        if finErrorLinea == -1:
            finErrorLinea = len(programa)
            
        contenido = programa[inicioErrorLinea:finErrorLinea]
        contenido_anterior = programa[inicioLineaAnterior:inicioErrorLinea-1]
        
        # Imprimir el error con el formato deseado
        print(f"\nLínea {linea}: {mensaje}")
        if contenido_anterior:
            print(contenido_anterior)
        print(contenido)
        print(" " * posicionError + "^")

#Función para recorrer el árbol sintáctico en preorden
def recorrer(nodo):
    global current_scope
    if nodo is None:
        return
    #si el nodo es una función 
    if nodo.exp == TipoExpresion.FunDecl:
        nombre = nodo.nombre
        tipo = nodo.tipo
        linea = getattr(nodo, 'linea', '?')
        # Crear lista de tipos de parámetros
        lista_params = []
        for param in nodo.parametros:
            tipo_param = param.tipo
            es_arreglo = param.size is not None or getattr(param, 'esArreglo', False)
            if es_arreglo:
                lista_params.append(f"{tipo_param} [array]")
            else:
                lista_params.append(tipo_param)

        # Caso especial: función sin parámetros = void
        if len(lista_params) == 0 and tipo == "void":
            lista_params = ["void"]
        
        simbolo = Symbol(nombre, "fun", tipo, False, None, linea, lista_params)
        
        if not current_scope.insert(simbolo):
            errorSemantico(f"Error, función '{nombre}' redeclarada.", linea, nombre)
        nuevo = SymbolTable(nombre, current_scope)
        current_scope.children.append(nuevo)
        old = current_scope
        current_scope = nuevo
        for param in nodo.parametros:
            declarar(param, "param")
        recorrer(nodo.cuerpo)
        current_scope = old
    #si el nodo es una declaración de variable
    elif nodo.exp == TipoExpresion.VarDecl:
        declarar(nodo, "var")
    #si el nodo es un bloque
    elif nodo.exp == TipoExpresion.Compound:
        decl_zone = True
        for stmt in nodo.sentencias:
            if stmt.exp == TipoExpresion.VarDecl:
                if not decl_zone:
                    errorSemantico("Error, declaración después de sentencias.", getattr(stmt, 'linea', '?'), stmt.nombre)
                declarar(stmt, "var")
            else:
                decl_zone = False
                recorrer(stmt)
    #si el nodo es un while, return o if pasa lo mismo
    elif nodo.exp == TipoExpresion.While:
        recorrer(nodo.condicion)
        recorrer(nodo.cuerpo)

    elif nodo.exp == TipoExpresion.If:
        recorrer(nodo.condicion)
        recorrer(nodo.entonces)
        if nodo.sino:
            recorrer(nodo.sino)

    elif nodo.exp == TipoExpresion.Return:
        if nodo.expresion:
            recorrer(nodo.expresion)
    #si el nodo es un operador
    elif nodo.exp == TipoExpresion.Op:
        if nodo.hijoIzq:
            recorrer(nodo.hijoIzq)
        if nodo.hijoDer:
            recorrer(nodo.hijoDer)
    #si el nodo es una expresión
    elif nodo.exp == TipoExpresion.ExprStmt:
        if nodo.expresion:
            recorrer(nodo.expresion)
    #si el nodo es una llamada a función
    elif nodo.exp == TipoExpresion.Call:
        ref = current_scope.lookup(nodo.nombre)
        if not ref:
            errorSemantico(f"Error, llamada a función no declarada '{nodo.nombre}'.", getattr(nodo, 'linea', '?'), nodo.nombre)
        for arg in nodo.args:
            recorrer(arg)
    #si el nodo es una variable
    elif nodo.exp == TipoExpresion.Var:
        ref = current_scope.lookup(nodo.nombre)
        if not ref:
            errorSemantico(f"Error, variable '{nodo.nombre}' no declarada.", getattr(nodo, 'linea', '?'), nodo.nombre)

    else:
        for attr in ["hijoIzq", "hijoDer", "condicion", "expresion", "entonces", "sino", "cuerpo"]:
            sub = getattr(nodo, attr, None)
            if isinstance(sub, NodoArbol):
                recorrer(sub)
        if hasattr(nodo, "args"):
            for a in nodo.args:
                recorrer(a)
        if hasattr(nodo, "parametros"):
            for p in nodo.parametros:
                recorrer(p)
        if hasattr(nodo, "sentencias"):
            for s in nodo.sentencias:
                recorrer(s)
#Función declara una variable o parámetro y lo registra en el scope actual.
def declarar(nodo, tipo_simbolo):
    global current_scope
    nombre = nodo.nombre
    tipo = nodo.tipo
    linea = getattr(nodo, 'linea', '?')
    es_arreglo = nodo.size is not None or getattr(nodo, 'esArreglo', False)
    simbolo = Symbol(nombre, tipo_simbolo, tipo, es_arreglo, nodo.size, linea)
    if tipo_simbolo == "param":
        simbolo.param = True
    if not current_scope.insert(simbolo):
        errorSemantico(f"Error, identificador '{nombre}' ya declarado en este ámbito.", linea, nombre)

#-------------- TYPECHECKING --------------
#Recorre en postorden el árbol sintáctico para verificar los tipos de las expresiones
def typeCheck(nodo):
    global current_scope
    global current_function_type

    if nodo is None:
        return None

    if nodo.exp == TipoExpresion.Const:
        return "int"

    elif nodo.exp == TipoExpresion.Var:
        ref = current_scope.lookup(nodo.nombre)
        if not ref: #si la variable no está declarada, se lanza un error
            errorSemantico(f"Error, variable '{nodo.nombre}' no declarada.", nodo.linea, nodo.nombre)
            return "error"

        # Validación si se usa índice con variable que no es arreglo
        if not ref.is_array and nodo.indice:
            errorSemantico(f"Error, la variable '{nodo.nombre}' no es un arreglo, no puede usarse con índice.", nodo.linea, nodo.nombre)
            return ref.data_type

        # Validación si es arreglo
        if ref.is_array:
            if nodo.indice:
                tipo_indice = typeCheck(nodo.indice)
                if tipo_indice != "int":
                    errorSemantico(f"Error, el índice del arreglo '{nodo.nombre}' debe ser de tipo int.", nodo.linea, nodo.nombre)
                if nodo.indice.exp == TipoExpresion.Const:
                    indice_val = nodo.indice.val
                    if indice_val >= ref.size: #si el índice es mayor al tamaño del arreglo, se lanza un error
                        errorSemantico(f"Error, índice {indice_val} fuera del límite del arreglo '{nodo.nombre}'.", nodo.linea, nodo.nombre)
            else:
                pass  # No se marca error

        return ref.data_type

    elif nodo.exp == TipoExpresion.Call:
        ref = current_scope.lookup(nodo.nombre)
        if not ref:
            errorSemantico(f"Error, función '{nodo.nombre}' no declarada.", nodo.linea, nodo.nombre)
            return "error"
        if ref.sym_type != "fun":
            errorSemantico(f"Error, '{nodo.nombre}' no es una función.", nodo.linea, nodo.nombre)
            return "error"

        # Excepción: 'output' acepta cualquier número de argumentos
        if ref.name != "output" and len(ref.parametros) != len(nodo.args):
            errorSemantico(f"Error, número de argumentos incorrecto para función '{nodo.nombre}'.", nodo.linea, nodo.nombre)
            return "error"

        # Verificar tipos de argumentos 
        if ref.name != "output":
            for i, arg in enumerate(nodo.args):
                tipo_arg = typeCheck(arg)
                tipo_esperado = ref.parametros[i].split()[0]  
                if tipo_arg != tipo_esperado:
                    errorSemantico(f"Error, argumento {i+1} debe ser '{tipo_esperado}', pero se encontró '{tipo_arg}'.", nodo.linea, nodo.nombre)
                    return "error"
        else:
            for arg in nodo.args:
                typeCheck(arg)  

        return ref.data_type

    elif nodo.exp == TipoExpresion.Op:
        tipo_izq = typeCheck(nodo.hijoIzq)
        tipo_der = typeCheck(nodo.hijoDer)
        op = nodo.op
        #si el tipo de la izquierda o derecha no es int, se lanza un error
        if tipo_izq != "int" or tipo_der != "int":
            errorSemantico(f"Error, operador '{op}' solo se puede aplicar entre enteros.", nodo.linea)
            return "error"
        #si el operador no es uno de los permitidos, se lanza un error
        if op in ["<", ">", "<=", ">=", "==", "!="]:
            return "int"  # En C-, condiciones son tipo int
        elif op in ["+", "-", "*", "/"]:
            return "int"
        #si el operador es =, se verifica si los tipos son compatibles
        elif op == "=":
            #si los tipos no son compatibles, se lanza un error
            if tipo_izq != tipo_der:
                errorSemantico(f"Error, tipos incompatibles en asignación.", nodo.linea)
                return "error"
            return tipo_izq
        else:
            errorSemantico(f"Error, operador desconocido '{op}'.", nodo.linea)
            return "error"

    elif nodo.exp == TipoExpresion.ExprStmt:
        return typeCheck(nodo.expresion)

    elif nodo.exp == TipoExpresion.Return:
        tipo_expr = typeCheck(nodo.expresion) if nodo.expresion else "void"
        if current_function_type == "void" and tipo_expr != "void":
            #si la función es void y se retorna un valor, se lanza un error
            errorSemantico(f"Error, no se puede retornar un valor en una función void.", nodo.linea)
        elif current_function_type == "int" and tipo_expr != "int":
            #si la función es int y se retorna un valor de otro tipo, se lanza un error
            errorSemantico(f"Error, se esperaba retorno de tipo int.", nodo.linea)
        return None

    elif nodo.exp == TipoExpresion.If or nodo.exp == TipoExpresion.While:
        tipo_cond = typeCheck(nodo.condicion)
        if tipo_cond != "int":
            #si la condición no es de tipo int, se lanza un error
            errorSemantico(f"Error, la condición debe ser de tipo int.", nodo.linea)
        typeCheck(nodo.entonces)
        if hasattr(nodo, 'sino') and nodo.sino:
            typeCheck(nodo.sino)
        return None

    elif nodo.exp == TipoExpresion.Compound:
        for stmt in nodo.sentencias:
            typeCheck(stmt)

    elif nodo.exp == TipoExpresion.FunDecl:
        current_function_type = nodo.tipo

        for child_scope in current_scope.children:
            if child_scope.scope_name == nodo.nombre:
                old_scope = current_scope
                current_scope = child_scope
                break
        else:
            old_scope = current_scope  # fallback

        typeCheck(nodo.cuerpo)
        current_scope = old_scope
        current_function_type = None

    return None

tabla_global = None

def semantica(tree, imprime=True):
    global tabla_global

    if imprime:
        print(">> Iniciando análisis semántico...")

    # 👇 Asignar tabla_global justo al inicio
    tabla_global = tabla(tree, imprime=False)

    # 👇 Mover validación después
    if tabla_global is None:
        errorSemantico("No se pudo construir la tabla de símbolos", 1)
        return

    main_func = tabla_global.lookup("main")
    if not main_func or main_func.sym_type != "fun":
        errorSemantico("Error semántico: no se encontró la función 'main'.", 1)
        return  

    if imprime:
        imprimir_tablas(tabla_global)

    for nodo in tree:
        typeCheck(nodo)

    if imprime:
        print(">> Análisis semántico finalizado.")
