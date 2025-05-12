# semantica.py

from globalTypes import *
from lexer import *
from Parser import *
current_function_type = None

def globales(prog, pos, long):
    global programa
    global posicion
    global progLong
    programa = prog
    posicion = pos
    progLong = long
    recibeLexer(programa, posicion, progLong)

class Symbol:
    def __init__(self, name, sym_type, data_type, is_array=False, size=None, linea=None, parametros=None):
        self.name = name
        self.sym_type = sym_type  # 'var', 'fun', 'param'
        self.data_type = data_type  # 'int', 'void'
        self.is_array = is_array
        self.size = size
        self.linea = linea if linea is not None else '?'
        self.references = []
        self.parametros = parametros or []  # Nueva lista para funciones


class SymbolTable:
    def __init__(self, scope_name, parent=None):
        self.scope_name = scope_name
        self.symbols = {}
        self.parent = parent
        self.children = []

    def insert(self, symbol):
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup(self, name):
        t = self
        while t:
            if name in t.symbols:
                return t.symbols[name]
            t = t.parent
        return None

    def __str__(self):
        out = f"\nScope: {self.scope_name}"
        out += f"\n{'Nombre':<12} | {'Tipo':<6} | {'Parámetros':<20} | {'Es Array':<9} | {'Línea':<5}"
        out += f"\n{'-'*12}-+-{'-'*6}-+-{'-'*20}-+-{'-'*9}-+-{'-'*5}"
        for sym in self.symbols.values():
            if sym.name in ["input", "output"]:
                continue  # nunca los mostramos pero si se consideran 
            params = ', '.join(sym.parametros) if sym.sym_type == "fun" else "–"
            out += f"\n{sym.name:<12} | {sym.data_type:<6} | {params:<20} | {str(sym.is_array):<9} | {str(sym.linea):<5}"
        return out



# tabla()
def tabla(tree, imprime=True):
    global current_scope
    current_scope = SymbolTable("global")

    # Funciones predefinidas
    current_scope.insert(Symbol("input", "fun", "int", False, None, 0))
    current_scope.insert(Symbol("output", "fun", "void", False, None, 0))

    for nodo in tree:
        recorrer(nodo)
    if imprime:
        imprimir_tablas(current_scope)
    return current_scope

def imprimir_tablas(tabla, nivel=0):
    print("  " * nivel + str(tabla))
    for hijo in tabla.children:
        imprimir_tablas(hijo, nivel + 1)

def recorrer(nodo):
    global current_scope
    if nodo is None:
        return

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
            print(f"Línea {linea}: Error, función '{nombre}' redeclarada.")
        nuevo = SymbolTable(nombre, current_scope)
        current_scope.children.append(nuevo)
        old = current_scope
        current_scope = nuevo
        for param in nodo.parametros:
            declarar(param, "param")
        recorrer(nodo.cuerpo)
        current_scope = old

    elif nodo.exp == TipoExpresion.VarDecl:
        declarar(nodo, "var")

    elif nodo.exp == TipoExpresion.Compound:
        decl_zone = True
        for stmt in nodo.sentencias:
            if stmt.exp == TipoExpresion.VarDecl:
                if not decl_zone:
                    print(f"Línea {getattr(stmt, 'linea', '?')}: Error, declaración después de sentencias.")
                declarar(stmt, "var")
            else:
                decl_zone = False
                recorrer(stmt)

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

    elif nodo.exp == TipoExpresion.Op:
        if nodo.hijoIzq:
            recorrer(nodo.hijoIzq)
        if nodo.hijoDer:
            recorrer(nodo.hijoDer)

    elif nodo.exp == TipoExpresion.ExprStmt:
        if nodo.expresion:
            recorrer(nodo.expresion)

    elif nodo.exp == TipoExpresion.Call:
        ref = current_scope.lookup(nodo.nombre)
        if not ref:
            print(f"Línea {getattr(nodo, 'linea', '?')}: Error, llamada a función no declarada '{nodo.nombre}'.")
        for arg in nodo.args:
            recorrer(arg)

    elif nodo.exp == TipoExpresion.Var:
        ref = current_scope.lookup(nodo.nombre)
        if not ref:
            print(f"Línea {getattr(nodo, 'linea', '?')}: Error, variable '{nodo.nombre}' no declarada.")

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

def declarar(nodo, tipo_simbolo):
    global current_scope
    nombre = nodo.nombre
    tipo = nodo.tipo
    linea = getattr(nodo, 'linea', '?')
    es_arreglo = nodo.size is not None or getattr(nodo, 'esArreglo', False)
    simbolo = Symbol(nombre, tipo_simbolo, tipo, es_arreglo, nodo.size, linea)
    if not current_scope.insert(simbolo):
        print(f"Línea {linea}: Error, identificador '{nombre}' ya declarado en este ámbito.")

#-------------- TYPECHECKING --------------
def typeCheck(nodo):
    global current_scope
    global current_function_type

    if nodo is None:
        return None

    if nodo.exp == TipoExpresion.Const:
        return "int"

    elif nodo.exp == TipoExpresion.Var:
        ref = current_scope.lookup(nodo.nombre)
        if not ref:
            print(f"Línea {nodo.linea}: Error, variable '{nodo.nombre}' no declarada.")
            return "error"
        return ref.data_type

    elif nodo.exp == TipoExpresion.Call:
        ref = current_scope.lookup(nodo.nombre)
        if not ref:
            print(f"Línea {nodo.linea}: Error, función '{nodo.nombre}' no declarada.")
            return "error"
        if ref.sym_type != "fun":
            print(f"Línea {nodo.linea}: Error, '{nodo.nombre}' no es una función.")
            return "error"

        if len(ref.parametros) != len(nodo.args):
            print(f"Línea {nodo.linea}: Error, número de argumentos incorrecto para función '{nodo.nombre}'.")
            return "error"

        # Verificar tipos de argumentos
        for i, arg in enumerate(nodo.args):
            tipo_arg = typeCheck(arg)
            tipo_esperado = ref.parametros[i].split()[0]  # por ej. "int [array]" → "int"
            if tipo_arg != tipo_esperado:
                print(f"Línea {nodo.linea}: Error, argumento {i+1} debe ser '{tipo_esperado}', pero se encontró '{tipo_arg}'.")
                return "error"

        return ref.data_type

    elif nodo.exp == TipoExpresion.Op:
        tipo_izq = typeCheck(nodo.hijoIzq)
        tipo_der = typeCheck(nodo.hijoDer)
        op = nodo.op

        if tipo_izq != "int" or tipo_der != "int":
            print(f"Línea {nodo.linea}: Error, operador '{op}' solo se puede aplicar entre enteros.")
            return "error"

        if op in ["<", ">", "<=", ">=", "==", "!="]:
            return "int"  # En C-, condiciones son tipo int
        elif op in ["+", "-", "*", "/"]:
            return "int"
        elif op == "=":
            if tipo_izq != tipo_der:
                print(f"Línea {nodo.linea}: Error, tipos incompatibles en asignación.")
                return "error"
            return tipo_izq
        else:
            print(f"Línea {nodo.linea}: Error, operador desconocido '{op}'.")
            return "error"

    elif nodo.exp == TipoExpresion.ExprStmt:
        return typeCheck(nodo.expresion)

    elif nodo.exp == TipoExpresion.Return:
        tipo_expr = typeCheck(nodo.expresion) if nodo.expresion else "void"
        if current_function_type == "void" and tipo_expr != "void":
            print(f"Línea {nodo.linea}: Error, no se puede retornar un valor en una función void.")
        elif current_function_type == "int" and tipo_expr != "int":
            print(f"Línea {nodo.linea}: Error, se esperaba retorno de tipo int.")
        return None

    elif nodo.exp == TipoExpresion.If or nodo.exp == TipoExpresion.While:
        tipo_cond = typeCheck(nodo.condicion)
        if tipo_cond != "int":
            print(f"Línea {nodo.linea}: Error, la condición debe ser de tipo int.")
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

def semantica(tree, imprime=True):
    if imprime:
        print(">> Iniciando análisis semántico...")
    tabla(tree, imprime)
    for nodo in tree:
        typeCheck(nodo)
    if imprime:
        print(">> Análisis semántico finalizado.")

