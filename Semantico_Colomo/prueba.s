.text
.globl main
main:
li $t0, 2
li $t1, 3
add $t2, $t0, $t1
sw $t2, -4($sp)  # x = ...
lw $t3, -4($sp)  # cargar x
li $t4, 2
mul $t5, $t3, $t4
sw $t5, -4($sp)  # x = ...
li $v0, 10
syscall
