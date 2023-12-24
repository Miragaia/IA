#Exercicio 4.1
import math


impar = lambda x: x % 2 == 1

#Exercicio 4.2
positivo = lambda x: x >= 0

#Exercicio 4.3
comparar_modulo = lambda x,y: abs(x) < abs(y)

#Exercicio 4.4
cart2pol = lambda x, y: (math.sqrt(x**2 + y**2), math.atan2(y, x))


#Exercicio 4.5
ex5 = lambda f, g, h: lambda x, y, z: h(f(x, y), g(y, z))

#Exercicio 4.6
def quantificador_universal(lista, f):
    return all(f(x) for x in lista)

#Exercicio 4.8
def subconjunto(lista1, lista2):
    if not lista1:
        return True
    elif not lista2:
        return False
    elif lista1[0] in lista2:
        return subconjunto(lista1[1:], lista2)
    else:
        return False

#Exercicio 4.9 (nao percebi o que querem dizer com relacao de ordem)
def menor_ordem(lista, f):
    pass 

#Exercicio 4.10 (nao percebi o que querem dizer com relacao de ordem)
def menor_e_resto_ordem(lista, f):
    pass

#Exercicio 5.2 (nao percebi o que querem dizer com relacao de ordem)
def ordenar_seleccao(lista, ordem):
    pass
