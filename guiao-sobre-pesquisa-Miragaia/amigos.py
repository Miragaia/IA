from constraintsearch import *

amigos = ["Andre", "Bernardo", "Claudio"]

def constraint(amigo1, item1, amigo2, item2):
    b1, c1 = item1
    b2, c2 = item2

    if amigo1 in item1 or amigo2 in item2:
        return False
    
    if b1==c1 or b2==c2:
        return False
    
    if c1 == "Claudio" and b1 != "Bernardo":
        return False
    
    if c2 == "Claudio" and b2 != "Bernardo":
        return False

    return True

def make_constraint_graph(amigos):
    return { (X,Y): constraint for X in amigos for Y in amigos if X!=Y }

def make_domain(amigos):
    return {r: [(b,c) for b in amigos for c in amigos ] for r in amigos}

cs = ConstraintSearch(make_domain(amigos),make_constraint_graph(amigos))

print(cs.search())
