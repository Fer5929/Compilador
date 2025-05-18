from globalTypes import *
import Semantica
from Parser import *
import sys

temp_count = 0
output = []
offsets = {}  # { varName: offset }
offset_actual = 0
label_count = 0

def nueva_etiqueta():
    global label_count
    etiqueta = f"L{label_count}"
    label_count += 1
    return etiqueta

def nueva_temp():
    global temp_count
    reg = f"$t{temp_count % 10}"
    temp_count += 1
    return reg

def codeGen(AST, filename):
    global output, temp_count, offsets, offset_actual
    output = []
    temp_count = 0
    offsets = {}
    offset_actual = 0

    output.append(".text")
    output.append(".globl main")
    output.append("main:")

    # Buscar función main en el AST
    for nodo in AST:
        if nodo.exp == TipoExpresion.FunDecl and nodo.nombre == "main":
            # Generar offsets para variables locales
            scope_main = None
            for child in Semantica.tabla_global.children:
                if child.scope_name == "main":
                    scope_main = child
                    break
            if scope_main:
                for var in scope_main.symbols.values():
                    offset_actual -= 4
                    offsets[var.name] = offset_actual
            # Generar código
            genFunMain(nodo)

    # Exit syscall
    output.append("li $v0, 10")
    output.append("syscall")

    with open(filename, "w") as f:
        for line in output:
            f.write(line + "\n")

def genFunMain(nodo):
    if nodo.cuerpo:
        for stmt in nodo.cuerpo.sentencias:
            genStmt(stmt)

def genStmt(nodo):
    # Expresión sola: x = ...;
    if nodo.exp == TipoExpresion.ExprStmt:
        if nodo.expresion:
            genExp(nodo.expresion)

    # Asignación como sentencia: x = ...;
    elif nodo.exp == TipoExpresion.Op and nodo.op == '=':
        var_name = nodo.hijoIzq.nombre
        valor = genExp(nodo.hijoDer)
        offset = offsets.get(var_name)
        if offset is not None:
            output.append(f"sw {valor}, {offset}($sp)  # {var_name} = ...")
        else:
            output.append(f"# ERROR: variable {var_name} no tiene offset asignado")

    # Sentencia if (...) { ... } [else { ... }]
    elif nodo.exp == TipoExpresion.If:
        et_else = nueva_etiqueta()
        et_end = nueva_etiqueta()

        cond_reg = genExp(nodo.condicion)
        output.append(f"beq {cond_reg}, $zero, {et_else}  # if false -> else")

        # bloque 'then'
        # Ejecuta múltiples sentencias si es Compound
        if nodo.entonces.exp == TipoExpresion.Compound:
            for stmt in nodo.entonces.sentencias:
                genStmt(stmt)
        else:
            genStmt(nodo.entonces)
        
        output.append(f"j {et_end}")  # salto a fin del if
        # ELSE block
        output.append(f"{et_else}:")
        if nodo.sino:
            if nodo.sino.exp == TipoExpresion.Compound:
                for stmt in nodo.sino.sentencias:
                    genStmt(stmt)
            else:
                genStmt(nodo.sino)

        output.append(f"{et_end}:")

    # Sentencia while (...) { ... }
    elif nodo.exp == TipoExpresion.While:
        et_start = nueva_etiqueta()
        et_exit = nueva_etiqueta()

        output.append(f"{et_start}:")
        cond_reg = genExp(nodo.condicion)
        output.append(f"beq {cond_reg}, $zero, {et_exit}  # while false -> exit")

        if nodo.entonces.exp == TipoExpresion.Compound:
            for stmt in nodo.entonces.sentencias:
                genStmt(stmt)
        else:
            genStmt(nodo.entonces)
        output.append(f"j {et_start}")
        output.append(f"{et_exit}:")

    # Sentencia return ...;
    elif nodo.exp == TipoExpresion.Return:
        if nodo.expresion:
            valor = genExp(nodo.expresion)
            output.append(f"move $v0, {valor}  # return valor")

            # imprimir el valor (debug)
            output.append(f"move $a0, {valor}  # valor a imprimir")
            output.append("li $v0, 1          # syscall: print int")
            output.append("syscall")

def genExp(nodo):
    if nodo.exp == TipoExpresion.Const:
        reg = nueva_temp()
        output.append(f"li {reg}, {nodo.val}")
        return reg

    elif nodo.exp == TipoExpresion.Var:
        offset = offsets.get(nodo.nombre)
        reg = nueva_temp()
        if offset is not None:
            if nodo.indice:  # Si es acceso a arreglo
                # Generar código para el índice
                indice_reg = genExp(nodo.indice)
                # Calcular offset del arreglo
                output.append(f"li {reg}, {offset}")  # Cargar offset base
                output.append(f"mul {indice_reg}, {indice_reg}, 4")  # Multiplicar índice por 4 (tamaño de int)
                output.append(f"add {reg}, {reg}, {indice_reg}")  # Sumar offset base + offset del índice
                output.append(f"add {reg}, {reg}, $sp")  # Sumar $sp para obtener dirección final
                output.append(f"lw {reg}, 0({reg})")  # Cargar valor del arreglo
            else:  # Si es variable normal
                output.append(f"lw {reg}, {offset}($sp)  # cargar {nodo.nombre}")
        else:
            output.append(f"# ERROR: variable {nodo.nombre} no tiene offset asignado")
        return reg

    elif nodo.exp == TipoExpresion.Op and nodo.op == '=':
        var_name = nodo.hijoIzq.nombre
        valor = genExp(nodo.hijoDer)
        offset = offsets.get(var_name)
        if offset is not None:
            if nodo.hijoIzq.indice:  # Si es asignación a arreglo
                # Generar código para el índice
                indice_reg = genExp(nodo.hijoIzq.indice)
                # Calcular offset del arreglo
                temp_reg = nueva_temp()
                output.append(f"li {temp_reg}, {offset}")  # Cargar offset base
                output.append(f"mul {indice_reg}, {indice_reg}, 4")  # Multiplicar índice por 4
                output.append(f"add {temp_reg}, {temp_reg}, {indice_reg}")  # Sumar offset base + offset del índice
                output.append(f"add {temp_reg}, {temp_reg}, $sp")  # Sumar $sp para obtener dirección final
                output.append(f"sw {valor}, 0({temp_reg})  # {var_name}[{nodo.hijoIzq.indice.val}] = ...")
            else:  # Si es asignación a variable normal
                output.append(f"sw {valor}, {offset}($sp)  # {var_name} = ...")
        else:
            output.append(f"# ERROR: variable {var_name} no tiene offset asignado")
        return valor

    elif nodo.exp == TipoExpresion.Op:
        izq = genExp(nodo.hijoIzq)
        der = genExp(nodo.hijoDer)
        res = nueva_temp()

        if nodo.op == '+':
            output.append(f"add {res}, {izq}, {der}")
        elif nodo.op == '-':
            output.append(f"sub {res}, {izq}, {der}")
        elif nodo.op == '*':
            output.append(f"mul {res}, {izq}, {der}")
        elif nodo.op == '/':
            output.append(f"div {res}, {izq}, {der}")
        elif nodo.op == '<':
            output.append(f"slt {res}, {izq}, {der}")
        elif nodo.op == '>':
            output.append(f"slt {res}, {der}, {izq}")
        elif nodo.op == '<=':
            output.append(f"slt {res}, {der}, {izq}")
            output.append(f"xori {res}, {res}, 1")
        elif nodo.op == '>=':
            output.append(f"slt {res}, {izq}, {der}")
            output.append(f"xori {res}, {res}, 1")
        elif nodo.op == '==':
            output.append(f"seq {res}, {izq}, {der}")
        elif nodo.op == '!=':
            output.append(f"sne {res}, {izq}, {der}")
        else:
            output.append(f"# ERROR: operador desconocido {nodo.op}")
        return res