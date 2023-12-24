#encoding: utf8

# YOUR NAME: Miguel Aido Miragaia
# YOUR NUMBER: 108317

# COLLEAGUES WITH WHOM YOU DISCUSSED THIS ASSIGNMENT (names, numbers):
# - Tomas Matos nmec: 108624
# - ...

from collections import defaultdict
from itertools import product
import math


from semantic_network import *
from constraintsearch import *
from collections import deque

class MySN(SemanticNetwork):

    def __init__(self):
        SemanticNetwork.__init__(self)
        self.assoc_stats =  {}
        # ADD CODE HERE IF NEEDED
        pass

    def query_local(self,user=None,e1=None,rel=None,e2=None):
        self.query_result = []

        for u, data in self.declarations.items():
            if user is not None and user != u:
                continue

            for (entity1, relation_name), entity2 in data.items():
                if (e1 is None or e1 == entity1) and (rel is None or rel == relation_name) and (e2 is None or e2 == entity2):
                    if isinstance(entity2, set):
                        for subj in entity2:
                            self.query_result.append(Declaration(u, Relation(entity1, relation_name, subj)))
                    else:
                        self.query_result.append(Declaration(u, Relation(entity1, relation_name, entity2)))

        return self.query_result
    
    def query(self,entity,assoc=None):
        self.query_result = []

        local_declarations = self.query_local(e1=entity, rel=assoc)
        # print('LOCAL',local_declarations)

        inherited_declarations = self.query_local(e1=entity, rel='subtype') + self.query_local(e1=entity, rel='member')
        # print('INHERITED',inherited_declarations)

        all_decl = local_declarations
        for decl in inherited_declarations:
            # print("REL",decl.relation)
            # print("NAME", decl.relation.name)
            e2 = decl.relation.entity2
            all_decl.extend(self.query(e2, assoc=assoc))

        for i in all_decl:
            if i.relation.name == 'subtype' or i.relation.name == 'member':
                all_decl.remove(i)
                    
        self.query_result = all_decl

        return self.query_result
    


    def update_assoc_stats(self, assoc, user=None):
        assoc_key = (assoc, user)
        
        if user is None:
            declarations = self.query_local(rel=assoc)
        else:
            declarations = self.query_local(user=user, rel=assoc)

        if assoc_key not in self.assoc_stats:
            self.assoc_stats[assoc_key] = ({}, {})

        stats_e1, stats_e2 = self.assoc_stats[assoc_key]

        entities1 = {}
        entities2 = {}

        for d in declarations:
            decl = d.relation
            e1 = decl.entity1
            e2 = decl.entity2

            if e1 not in entities1:
                entities1[e1] = 0
            if e2 not in entities2:
                entities2[e2] = 0

            entities1[e1] += 1
            entities2[e2] += 1

        stats_e1 = {}
        stats_e2 = {}

        for e1 in entities1.keys():
            stats_e1 = self.get_stats_entity(user, e1, e2, stats_e1, entities1, entities1[e1])

        for e2 in entities2.keys():
            stats_e2 = self.get_stats_entity(user, e2, e1, stats_e2, entities2, entities2[e2])

        res_e1 = sum(entities1.values()) - (sum(entities1.values()) - sum(entities1.values())) + (sum(entities1.values()) - sum(entities1.values())) ** 0.5
        res_e2 = sum(entities2.values()) - (sum(entities2.values()) - sum(entities2.values())) + (sum(entities2.values()) - sum(entities2.values())) ** 0.5

        for s1 in stats_e1.keys():
            self.assoc_stats[assoc_key][0][s1] = stats_e1[s1] / res_e1

        for s2 in stats_e2.keys():
            self.assoc_stats[assoc_key][1][s2] = stats_e2[s2] / res_e2

        return self.assoc_stats
    
    def get_stats_entity(self, user, e1, e2, stats_a_e, es, count):
        decls = self.query_local(user=user, e1=e1, rel="member")  + self.query_local(user=user, e1=e1, rel="subtype")
        for d in decls:
            decl = d.relation
            # s2 = decl.entity1 #troquei a ordem aqui
            # s1 = decl.entity2 #tal como aqui
            if decl.entity2 == decl.entity1:
                s = decl.entity1
            else:
                s = decl.entity2
            
            if s not in stats_a_e:
                stats_a_e[s] = 0
            stats_a_e[s] += count
            stats_a_e = self.get_stats_entity(user, s, e2, stats_a_e, es, count)
        return stats_a_e


class ConstraintSearch:

    def __init__(self, domains, constraints):
        self.domains = domains
        self.constraints = constraints
        self.calls = 0

    def search(self,domains=None):
        self.calls += 1 
        
        if domains==None:
            domains = self.domains

        if any([lv==[] for lv in domains.values()]):
            return None

        if all([len(lv)==1 for lv in list(domains.values())]):
            for (var1,var2) in self.constraints:
                constraint = self.constraints[var1,var2]
                if not constraint(var1,domains[var1][0],var2,domains[var2][0]):
                    return None 
            return { v:lv[0] for (v,lv) in domains.items() }
       
        for var in domains.keys():
            if len(domains[var])>1:
                for val in domains[var]:
                    newdomains = dict(domains)
                    newdomains[var] = [val]

                    newdomains = self.propagate(newdomains,var,val)
                    if newdomains == None:
                        continue
                    solution = self.search(newdomains)
                    if solution != None:
                        return solution
        return None


class MyCS(ConstraintSearch):

    def __init__(self, domains, constraints):
        super().__init__(domains, constraints)
        self.results_set = set()

    def search_all(self, domains=None, max_solutions=None):
        self.results_set = set()
        self.calls = 0

        if domains is None:
            domains = self.domains

        stack = deque([domains.copy()])

        while stack and (max_solutions is None or len(self.results_set) < max_solutions):
            current_domains = stack.pop()

            if any([lv == [] for lv in current_domains.values()]):
                continue

            if all([len(lv) == 1 for lv in current_domains.values()]):
                valid_solution = all(
                    self.constraints[var1, var2](var1, current_domains[var1][0], var2, current_domains[var2][0])
                    for (var1, var2) in self.constraints
                )

                if valid_solution:
                    result = tuple(sorted((v, lv[0]) for (v, lv) in current_domains.items()))
                    self.results_set.add(result)
                continue

            var_to_expand = self.select_variable(current_domains)

            if var_to_expand is not None and len(current_domains[var_to_expand]) > 1:
                values_to_explore = current_domains[var_to_expand]

                for val in values_to_explore:
                    new_domains = current_domains.copy()
                    new_domains[var_to_expand] = [val]
                    new_domains = self.propagate(new_domains, var_to_expand, val)
                    if new_domains is not None:
                        stack.append(new_domains)

        return [dict(result) for result in self.results_set]

    def select_variable(self, domains):
        return min(domains.keys(), key=lambda var: len(domains[var]) if len(domains[var]) > 1 else float('inf'))

    def propagate(self,domains,var,value):
        for v, domain in domains.items():
            if v == var:
                continue
            if (v,var) in self.constraints:
                constraint = self.constraints[v,var]
                new_domain = [val for val in domain if constraint(v,val,var,value)]
                if new_domain == []:
                    return None
                domains[v] = new_domain

        return domains
