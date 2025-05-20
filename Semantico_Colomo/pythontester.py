def suma(a, b):
    return a + b

def main():
    x = 0
    y = 0
    z = 0
    i = 0
    datos = [0] * 3

    x = 1
    y = 2
    z = suma(x, y)

    datos[0] = 4
    datos[1] = 5
    datos[2] = 6

    i = 0
    while i < 3:
        if datos[i] == 4:
            z = suma(z, datos[i])
            print ('valor de z en el if', z)
        else:
            z = z + 1
            print ('valor de z en el else', z)
        i = i + 1

    if z > 10:
        if x > 0:
            z = z + 1
        else:
            z = z + 100

    while x < 2:
        while y < 4:
            y = y + 1
        x = x + 1

    z = z  # no tiene efecto, pero se mantiene por fidelidad al original
    return z

# Ejecutar main y mostrar el resultado
resultado = main()
print(resultado)
