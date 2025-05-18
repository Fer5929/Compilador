from globalTypes import *
import Semantica
from Parser import *
import sys

temp_count = 0
output = []
offsets = {}  # { varName: offset }
offset_actual = 0

def nueva_temp():
    global temp_count
    reg = f"$t{temp_count}"
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
    if nodo.exp == TipoExpresion.ExprStmt:
        if nodo.expresion:
            genExp(nodo.expresion)

    elif nodo.exp == TipoExpresion.Op and nodo.op == '=':
        var_name = nodo.hijoIzq.nombre
        valor = genExp(nodo.hijoDer)
        offset = offsets.get(var_name)
        if offset is not None:
            output.append(f"sw {valor}, {offset}($sp)  # {var_name} = ...")
        else:
            output.append(f"# ERROR: variable {var_name} no tiene offset asignado")
    elif nodo.exp == TipoExpresion.Return:
        if nodo.expresion:
            valor = genExp(nodo.expresion)
            output.append(f"move $v0, {valor}  # return valor")
        
                # Imprimir resultado antes de salir (debug)
            output.append(f"move $a0, {valor}    # valor a imprimir")
            output.append("li $v0, 1            # syscall: print int")
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
            output.append(f"lw {reg}, {offset}($sp)  # cargar {nodo.nombre}")
        else:
            output.append(f"# ERROR: variable {nodo.nombre} no tiene offset asignado")
        return reg

    elif nodo.exp == TipoExpresion.Op and nodo.op != '=':
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
        return res
    elif nodo.exp == TipoExpresion.Op and nodo.op == '=':
        # Asignación dentro de expresión
        var_name = nodo.hijoIzq.nombre
        valor = genExp(nodo.hijoDer)
        offset = offsets.get(var_name)
        if offset is not None:
            output.append(f"sw {valor}, {offset}($sp)  # {var_name} = ...")
        else:
            output.append(f"# ERROR: variable {var_name} no tiene offset asignado")
        return valor
