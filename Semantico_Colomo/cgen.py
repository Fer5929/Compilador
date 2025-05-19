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

    for nodo in AST:
        if nodo.exp == TipoExpresion.FunDecl:
            scope = None
            for child in Semantica.tabla_global.children:
                if child.scope_name == nodo.nombre:
                    scope = child
                    break
            if scope:
                offsets = {}
                offset_actual = 0
                param_index = 0
                for var in scope.symbols.values():
                    if getattr(var, "param", False):
                        offsets[var.name] = 8 + 4 * param_index
                        param_index += 1
                    else:
                        offset_actual -= 4
                        offsets[var.name] = offset_actual

            if nodo.nombre == "main":
                output.append(".globl main")
                output.append("main:")
                genFun(nodo, is_main=True)
            else:
                output.append(f"{nodo.nombre}:")
                genFun(nodo)




    with open(filename, "w") as f:
        for line in output:
            f.write(line + "\n")

def genFun(nodo, is_main=False):
    output.append("sub $sp, $sp, 8")      # espacio para $fp y $ra
    output.append("sw $ra, 4($sp)")
    output.append("sw $fp, 0($sp)")
    output.append("move $fp, $sp")

    # Solo reservar espacio si hay variables locales
    locals_only = [offset for offset in offsets.values() if offset < 0]
    local_size = -min(locals_only) if locals_only else 0
    if local_size > 0:
        output.append(f"sub $sp, $sp, {local_size}")

    # Generar cuerpo de la función
    if nodo.cuerpo:
        for stmt in nodo.cuerpo.sentencias:
            genStmt(stmt)

    # Liberar espacio para locales si fue reservado
    if local_size > 0:
        output.append(f"add $sp, $sp, {local_size}")

    if is_main:
        # Imprimir el valor de retorno (ya en $v0)
        output.append("move $a0, $v0")
        output.append("li $v0, 1")         # syscall: print int
        output.append("syscall")

        output.append("li $v0, 10")        # syscall: exit
        output.append("syscall")
    else:
        output.append("move $sp, $fp")
        output.append("lw $fp, 0($sp)")
        output.append("lw $ra, 4($sp)")
        output.append("add $sp, $sp, 8")
        output.append("jr $ra")


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

    elif nodo.exp == TipoExpresion.If:
        et_else = nueva_etiqueta()
        et_end = nueva_etiqueta()

        cond_reg = genExp(nodo.condicion)
        output.append(f"beq {cond_reg}, $zero, {et_else}  # if false -> else")

        if nodo.entonces:
            if nodo.entonces.exp == TipoExpresion.Compound:
                for stmt in nodo.entonces.sentencias:
                    genStmt(stmt)
            else:
                genStmt(nodo.entonces)

        output.append(f"j {et_end}")

        output.append(f"{et_else}:")
        if nodo.sino:
            if nodo.sino.exp == TipoExpresion.Compound:
                for stmt in nodo.sino.sentencias:
                    genStmt(stmt)
            else:
                genStmt(nodo.sino)

        output.append(f"{et_end}:")



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

    elif nodo.exp == TipoExpresion.Return:
        if nodo.expresion:
            valor = genExp(nodo.expresion)
            output.append(f"move $v0, {valor}  # return valor")


def genExp(nodo):
    if nodo.exp == TipoExpresion.Const:
        reg = nueva_temp()
        output.append(f"li {reg}, {nodo.val}")
        return reg

    elif nodo.exp == TipoExpresion.Var:
        offset = offsets.get(nodo.nombre)
        reg = nueva_temp()
        if offset is not None:
            if nodo.indice:
                indice_reg = genExp(nodo.indice)
                output.append(f"li {reg}, {offset}")
                output.append(f"mul {indice_reg}, {indice_reg}, 4")
                output.append(f"add {reg}, {reg}, {indice_reg}")
                if offset >= 0:
                    output.append(f"add {reg}, {reg}, $fp")
                else:
                    output.append(f"add {reg}, {reg}, $sp")
                output.append(f"lw {reg}, 0({reg})")
            else:
                if offset >= 0:
                    output.append(f"lw {reg}, {offset}($fp)  # cargar param {nodo.nombre}")
                else:
                    output.append(f"lw {reg}, {offset}($sp)  # cargar var {nodo.nombre}")
        else:
            output.append(f"# ERROR: variable {nodo.nombre} no tiene offset asignado")
        return reg

    elif nodo.exp == TipoExpresion.Op and nodo.op == '=':
        var_name = nodo.hijoIzq.nombre
        valor = genExp(nodo.hijoDer)
        offset = offsets.get(var_name)
        if offset is not None:
            if nodo.hijoIzq.indice:
                indice_reg = genExp(nodo.hijoIzq.indice)
                temp_reg = nueva_temp()
                output.append(f"li {temp_reg}, {offset}")
                output.append(f"mul {indice_reg}, {indice_reg}, 4")
                output.append(f"add {temp_reg}, {temp_reg}, {indice_reg}")
                if offset >= 0:
                    output.append(f"add {temp_reg}, $fp, {temp_reg}")
                else:
                    output.append(f"add {temp_reg}, $sp, {temp_reg}")
                output.append(f"sw {valor}, 0({temp_reg})  # {var_name}[...] = ...")
            else:
                if offset >= 0:
                    output.append(f"sw {valor}, {offset}($fp)  # asignar param {var_name}")
                else:
                    output.append(f"sw {valor}, {offset}($sp)  # asignar var {var_name}")
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

    elif nodo.exp == TipoExpresion.Call:
        if nodo.nombre == "input":
            output.append("li $v0, 5")      # syscall: read int 
            output.append("syscall")
            res = nueva_temp()
            output.append(f"move {res}, $v0")
            output.append("# leyendo entero con input()")
            return res
        elif nodo.nombre == "output":
            val = genExp(nodo.args[0])
            output.append(f"move $a0, {val}")
            output.append("li $v0, 1")      # syscall: print int
            output.append("syscall")
            output.append("# imprimiendo entero con output()")
            res = nueva_temp()
            output.append(f"li {res}, 0")
            return res
        else:
            for arg in reversed(nodo.args): # empujar argumentos en la pila
                val = genExp(arg)
                output.append("sub $sp, $sp, 4")
                output.append(f"sw {val}, 0($sp)")
            output.append(f"jal {nodo.nombre}")
            output.append(f"add $sp, $sp, {len(nodo.args) * 4}")
            res = nueva_temp()
            output.append(f"move {res}, $v0")
            return res
