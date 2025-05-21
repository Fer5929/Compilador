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

def generar_data_section():
    data_lines = [".data"]
    global_scope = Semantica.tabla_global
    for var in global_scope.symbols.values():
        if var.sym_type == "var":
            if var.is_array and var.size:
                data_lines.append(f"{var.name}: .space {int(var.size)*4}")
            else:
                data_lines.append(f"{var.name}: .word 0")
    return data_lines

def codeGen(AST, filename):
    global output, temp_count, offsets, offset_actual
    output = []
    temp_count = 0
    offsets = {}
    offset_actual = 0

    # Generar sección .data primero
    data_section = generar_data_section()
    output.extend(data_section)
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
                        if getattr(var, "is_array", False) and getattr(var, "size", 0):
                            offset_actual -= int (var.size) * 4
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

    # Detectar tipo de función
    global_scope = Semantica.tabla_global
    fun_symbol = global_scope.symbols.get(nodo.nombre)
    tipo_funcion = getattr(fun_symbol, "tipo", None)

    # Bandera para saber si hubo return
    hubo_return = False

    # Generar cuerpo de la función
    if nodo.cuerpo:
        for stmt in nodo.cuerpo.sentencias:
            if stmt.exp == TipoExpresion.Return:
                hubo_return = True
            genStmt(stmt)

    # Si es función int y no hubo return, devolver 1 por defecto
    if tipo_funcion == "int" and not hubo_return:
        output.append("li $v0, 1  # return por defecto")

    # Liberar espacio para locales si fue reservado
    if local_size > 0:
        output.append(f"add $sp, $sp, {local_size}")

    if is_main:
        # Detectar tipo de función main
        global_scope = Semantica.tabla_global
        fun_symbol = global_scope.symbols.get(nodo.nombre)
        tipo_funcion = getattr(fun_symbol, "tipo", None)

        if tipo_funcion == "int":
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
        # Detectar si es variable global
        global_scope = Semantica.tabla_global
        is_global = nodo.nombre in global_scope.symbols and global_scope.symbols[nodo.nombre].sym_type == "var"
        if offset is not None and not is_global:
            if nodo.indice:
                indice_reg = genExp(nodo.indice)
                output.append(f"li {reg}, {offset}")
                output.append(f"mul {indice_reg}, {indice_reg}, 4")
                output.append(f"add {reg}, {reg}, {indice_reg}")
                output.append(f"add {reg}, {reg}, $fp")
                output.append(f"lw {reg}, 0({reg})")
            else:
                output.append(f"lw {reg}, {offset}($fp)  # cargar var/param {nodo.nombre}")
        elif is_global:
            if nodo.indice:
                base_reg = nueva_temp()
                output.append(f"la {base_reg}, {nodo.nombre}")
                indice_reg = genExp(nodo.indice)
                output.append(f"mul {indice_reg}, {indice_reg}, 4")
                output.append(f"add {base_reg}, {base_reg}, {indice_reg}")
                output.append(f"lw {reg}, 0({base_reg})")
            else:
                output.append(f"la {reg}, {nodo.nombre}")
                output.append(f"lw {reg}, 0({reg})")
        else:
            output.append(f"# ERROR: variable {nodo.nombre} no tiene offset asignado")
        return reg

    elif nodo.exp == TipoExpresion.Op and nodo.op == '=':
        var_name = nodo.hijoIzq.nombre
        valor = genExp(nodo.hijoDer)
        offset = offsets.get(var_name)
        # Detectar si es variable global
        global_scope = Semantica.tabla_global
        is_global = var_name in global_scope.symbols and global_scope.symbols[var_name].sym_type == "var"
        if offset is not None and not is_global:
            if nodo.hijoIzq.indice:
                indice_reg = genExp(nodo.hijoIzq.indice)
                temp_reg = nueva_temp()
                output.append(f"li {temp_reg}, {offset}")
                output.append(f"mul {indice_reg}, {indice_reg}, 4")
                output.append(f"add {temp_reg}, {temp_reg}, {indice_reg}")
                output.append(f"add {temp_reg}, {temp_reg}, $fp")
                output.append(f"sw {valor}, 0({temp_reg})  # {var_name}[...] = ...")
            else:
                output.append(f"sw {valor}, {offset}($fp)  # asignar var/param {var_name}")
        elif is_global:
            if nodo.hijoIzq.indice:
                base_reg = nueva_temp()
                output.append(f"la {base_reg}, {var_name}")
                indice_reg = genExp(nodo.hijoIzq.indice)
                output.append(f"mul {indice_reg}, {indice_reg}, 4")
                output.append(f"add {base_reg}, {base_reg}, {indice_reg}")
                output.append(f"sw {valor}, 0({base_reg})  # {var_name}[...] = ...")
            else:
                addr_reg = nueva_temp()
                output.append(f"la {addr_reg}, {var_name}")
                output.append(f"sw {valor}, 0({addr_reg})  # asignar global {var_name}")
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
        # Soporte para output(x)
        if nodo.nombre == "output" and len(nodo.args) == 1:
            val = genExp(nodo.args[0])
            output.append(f"move $a0, {val}")
            output.append("li $v0, 1")  # syscall: print int
            output.append("syscall")
            return "$zero"
        # Soporte para input()
        if nodo.nombre == "input" and len(nodo.args) == 0:
            reg = nueva_temp()
            output.append("li $v0, 5")  # syscall: read int
            output.append("syscall")
            output.append(f"move {reg}, $v0")
            return reg
        # Llamadas normales
        for arg in reversed(nodo.args):
            val = genExp(arg)
            output.append("sub $sp, $sp, 4")
            output.append(f"sw {val}, 0($sp)")
        output.append(f"jal {nodo.nombre}")
        output.append(f"add $sp, $sp, {len(nodo.args) * 4}")
        # Detectar si la función es void
        global_scope = Semantica.tabla_global
        fun_symbol = global_scope.symbols.get(nodo.nombre)
        if fun_symbol and getattr(fun_symbol, "tipo", None) == "void":
            return None  # No retorna valor
        res = nueva_temp()
        output.append(f"move {res}, $v0")
        return res

    return "$zero"  # Por defecto, retornar $zero si no se cumple ninguna condición