from collections import Counter
from statistics import mean
from functools import reduce

# Guiao de representacao do conhecimento
# -- Redes semanticas
# 
# Inteligencia Artificial & Introducao a Inteligencia Artificial
# DETI / UA
#
# (c) Luis Seabra Lopes, 2012-2020
# v1.9 - 2019/10/20
#


# Classe Relation, com as seguintes classes derivadas:
#     - Association - uma associacao generica entre duas entidades
#     - Subtype     - uma relacao de subtipo entre dois tipos
#     - Member      - uma relacao de pertenca de uma instancia a um tipo
#

class Relation:
    def __init__(self,e1,rel,e2):
        self.entity1 = e1
#       self.relation = rel  # obsoleto
        self.name = rel
        self.entity2 = e2
    def __str__(self):
        return self.name + "(" + str(self.entity1) + "," + \
               str(self.entity2) + ")"
    def __repr__(self):
        return str(self)


# Subclasse Association
class Association(Relation):
    def __init__(self,e1,assoc,e2):
        Relation.__init__(self,e1,assoc,e2)

#   Exemplo:
#   a = Association('socrates','professor','filosofia')

# Subclasse Subtype
class Subtype(Relation):
    def __init__(self,sub,super):
        Relation.__init__(self,sub,"subtype",super)


#   Exemplo:
#   s = Subtype('homem','mamifero')

# Subclasse Member
class Member(Relation):
    def __init__(self,obj,type):
        Relation.__init__(self,obj,"member",type)

#   Exemplo:
#   m = Member('socrates','homem')

# classe Declaration
# -- associa um utilizador a uma relacao por si inserida
#    na rede semantica
#
class Declaration:
    def __init__(self,user,rel):
        self.user = user
        self.relation = rel
    def __str__(self):
        return "decl("+str(self.user)+","+str(self.relation)+")"
    def __repr__(self):
        return str(self)

#   Exemplos:
#   da = Declaration('descartes',a)
#   ds = Declaration('darwin',s)
#   dm = Declaration('descartes',m)

# classe SemanticNetwork
# -- composta por um conjunto de declaracoes
#    armazenado na forma de uma lista
#

#ex: 15
class AssocOne(Association):
    def _init_(self, e1, assoc, e2):
        Association._init_(self, e1, assoc, e2)

class AssocNum(Association):
    def _init_(self, e1, assoc, e2):
        Association._init_(self, e1, assoc, e2)



class SemanticNetwork:
    def __init__(self,ldecl=None):
        self.declarations = [] if ldecl==None else ldecl
    def __str__(self):
        return str(self.declarations)
    def insert(self,decl):
        self.declarations.append(decl)
    def query_local(self,user=None,e1=None,rel=None,e2=None, rel_type=None):
        self.query_result = \
            [ d for d in self.declarations
                if  (user == None or d.user==user)
                and (e1 == None or d.relation.entity1 == e1)
                and (rel == None or d.relation.name == rel)
                and (e2 == None or d.relation.entity2 == e2)
                and (rel_type == None or isinstance(d.relation, rel_type)) ]
        return self.query_result
    def show_query_result(self):
        for d in self.query_result:
            print(str(d))
    
    #1
    def list_associations(self):
        lassoc = [d.relation.name for d in self.declarations
                  if isinstance(d.relation,Association)]
        return list(set(lassoc))
    
    #2
    def list_objects(self):
        lobj = [d.relation.entity1 for d in self.declarations
                if isinstance(d.relation,Member)]
        return list(set(lobj))
    
    #3
    def list_users(self):
        lusers = [d.user for d in self.declarations]
        return list(set(lusers))
    
    #4
    def list_types(self):
        ltypes = [d.relation.entity2 for d in self.declarations
                    if isinstance(d.relation, Member)
                    or  isinstance(d.relation, Subtype)]
        return list(set(ltypes))
    
    #5
    def list_local_associations(self, obj):
        lassoc = [d.relation.name for d in self.declarations
                  if isinstance(d.relation,Association)
                  and d.relation.entity1 == obj]
        return list(set(lassoc))
    
    #6
    def list_relations_by_user(self, user):
        lrel = [d.relation.name for d in self.declarations
                if d.user == user]
        return list(set(lrel))

    #7
    def associations_by_user(self, user):
        lassoc = [d.relation.name for d in self.declarations
                  if isinstance(d.relation,Association)
                  and d.user == user]
        return len(list(set(lassoc)))
    
    #8
    def list_local_associations_by_entity(self, obj):
        lassoc = [(d.relation.name, d.user) for d in self.declarations
                  if isinstance(d.relation,Association)
                  and d.relation.entity1 == obj]
        return list(set(lassoc))
    
    #9
    def predecessor(self, e1, e2):
        query = self.query_local(e2=e1)
        if query == []:
            return False
        for i in query:
            if type(i.relation) in (Member, Subtype) and i.relation.entity1 == e2:
                return True
        return self.predecessor(i.relation.entity1, e2)
    
    #10
    def predecessor_path(self, e1, e2):
        query = self.query_local(e2=e1)
        if query == []:
            return None
        for i in query:
            if type(i.relation) in (Member, Subtype) and i.relation.entity1 == e2:
                return [e1, e2]
        return [e1] + self.predecessor_path(i.relation.entity1, e2)

    #11
    def query(self, entity, rel=None):
        decl_local = self.query_local(e1=entity, rel=rel, rel_type=Association) + self.query_local(e2=entity, rel=rel, rel_type=Association)
        pred_direct = self.query_local(e1=entity, rel_type=(Member, Subtype))
        decl = decl_local
        for dp in pred_direct:
            decl += self.query(dp.relation.entity2, rel)
        return decl
    
    #11
    def query2(self, entity, rel=None):
        decl_local = self.query_local(e1=entity, rel=rel, rel_type=(Member, Subtype)) + self.query_local(e2=entity, rel=rel, rel_type=(Member, Subtype))
        return decl_local + self.query(entity, rel)
    
    #12
    def query_cancel(self, entity, rel=None):
        decl_local = self.query_local(e1=entity, rel=rel, rel_type=Association) + self.query_local(e2=entity, rel=rel, rel_type=Association)
        pred_direct = self.query_local(e1=entity, rel_type=(Member, Subtype))
        decl = decl_local
        decl_name = [d.relation.name for d in decl]
        for pd in pred_direct:
            decl += [p for p in self.query_cancel(pd.relation.entity2, rel) if p.relation.name not in decl_name]
        return decl
        
    
    #13
    def query_down(self, tipo, assoc, first=True):
        if not first:
            decl = self.query_local(e1=tipo, rel=assoc) + self.query_local(e2=tipo, rel=assoc)
        else:
            decl = []
        desc_direct = self.query_local(e2=tipo, rel_type=(Member, Subtype))
        for dd in desc_direct:
            decl += [p for p in self.query_down(dd.relation.entity1, assoc, False)]
        return decl

    #14
    def query_induce(self, tipo, assoc):
        decl = self.query_down(tipo, assoc)
        valor, _ = Counter([d.relation.entity2 for d in decl]).most_common(1)[0]
        return valor
    
    #15
    def query_local_assoc(self, entidade, assoc):
        local = self.query_local(e1=entidade, rel=assoc)
        for d in local:
            if isinstance(d.relation, AssocOne):
                valor, count = Counter([d.relation.entity2 for d in local]).most_common(1)[0]
                return valor, count/len(local)
            elif isinstance(d.relation, AssocNum):
                return mean([d.relation.entity2 for d in local])
            elif isinstance(d.relation, Association):
                all_assoc = [(val, c/len(local)) for (val, c) in Counter([d.relation.entity2 for d in local]).most_common()]
                def aux(carry, elem):
                    l, lim = carry
                    val, freq = elem
                    return (l+[elem], lim+freq) if lim < 0.75 else l
                return reduce(aux, all_assoc, ([], 0))
    
    def query_assoc_value(self, E, A):
        local = self.query_local(e1=E, rel=A)
        local_count = Counter([d.relation.entity2 for d in local]).most_common()
        if len(local_count) == 1:
            return local_count[0][0]
        herdadas = self.query(entity=E, rel=A)
        herdadas_count = Counter([d.relation.entity2 for d in herdadas]).most_common()
        F = {}
        for v, c in local_count:
            F[v] = c
        for v, c in herdadas_count:
            if v in F:
                F[v] += c
            else:
                F[v] = c
        return sorted(F.items(), key=lambda e: e[1], reverse=True)[0][0]