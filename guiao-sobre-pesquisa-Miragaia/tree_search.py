
# Module: tree_search
# 
# This module provides a set o classes for automated
# problem solving through tree search:
#    SearchDomain  - problem domains
#    SearchProblem - concrete problems to be solved
#    SearchNode    - search tree nodes
#    SearchTree    - search tree with the necessary methods for searhing
#
#  (c) Luis Seabra Lopes
#  Introducao a Inteligencia Artificial, 2012-2019,
#  Inteligência Artificial, 2014-2019

from abc import ABC, abstractmethod

# Dominios de pesquisa
# Permitem calcular
# as accoes possiveis em cada estado, etc
class SearchDomain(ABC):

    # construtor
    @abstractmethod
    def __init__(self):
        pass

    # lista de accoes possiveis num estado
    @abstractmethod
    def actions(self, state):
        pass

    # resultado de uma accao num estado, ou seja, o estado seguinte
    @abstractmethod
    def result(self, state, action):
        pass

    # custo de uma accao num estado
    @abstractmethod
    def cost(self, state, action):
        pass

    # custo estimado de chegar de um estado a outro
    @abstractmethod
    def heuristic(self, state, goal):
        [x1, y1] = self.coordinates[state]
        [x2, y2] = self.coordinates[goal]
        d = ((x1-x2)**2+(y1-y2)**2)**(1/2)
        return d

    # test if the given "goal" is satisfied in "state"
    @abstractmethod
    def satisfies(self, state, goal):
        pass


# Problemas concretos a resolver
# dentro de um determinado dominio
class SearchProblem:
    def __init__(self, domain, initial, goal):
        self.domain = domain
        self.initial = initial
        self.goal = goal
    def goal_test(self, state):
        return self.domain.satisfies(state,self.goal)

# Nos de uma arvore de pesquisa
class SearchNode:
    def __init__(self,state,parent, depth, cost, heuristic=0): 
        self.state = state
        self.parent = parent
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic

    def in_parent(self, newstate):
        if self.state == newstate:
            return True
        if self.parent == None:
            return False
        return self.parent.in_parent(newstate)
    def __str__(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"
    def __repr__(self):
        return str(self)

# Arvores de pesquisa
class SearchTree:

    # construtor
    def __init__(self,problem, strategy='breadth'): 
        self.problem = problem
        root = SearchNode(problem.initial, None, 0, cost=0)
        self.open_nodes = [root]
        self.strategy = strategy
        self.solution = None
        self.terminals = 1
        self.non_terminals = 0
        self.total_branching = 0
        self.highest_cost_nodes = [root]
        self._total_depth = 0

    # length:
    @property
    def length(self):
        return self.solution.depth    
    
    #cost:
    @property
    def cost(self):
        return self.solution.cost

    # avg_branching:
    @property
    def avg_branching(self):
        if self.non_terminals == 0:
            return 0
        return self.total_branching / self.non_terminals
    
    # average_depth:
    @property
    def average_depth(self):
        return self._total_depth / (self.non_terminals + self.terminals)
    
    # plan:
    @property
    def plan(self):
        _plan = [self.solution.action]
        no = self.solution.parent
        while no.parent:
            _plan[:0] = [no.action]
            no = no.parent
        return _plan

    # obter o caminho (sequencia de estados) da raiz ate um no
    def get_path(self,node):
        if node.parent == None:
            return [node.state]
        path = self.get_path(node.parent)
        path += [node.state]
        return(path)

    # procurar a solucao
    def search(self, limit=None):
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            if self.problem.goal_test(node.state):
                self.solution = node
                return self.get_path(node)
            self.terminals -= 1
            self.non_terminals += 1
            lnewnodes = []
            for a in self.problem.domain.actions(node.state):
                newstate = self.problem.domain.result(node.state,a)
                if not node.in_parent(newstate) and (limit == None or node.depth < limit):
                    newnode = SearchNode(newstate,node, node.depth+1, node.cost + self.problem.domain.cost(node.state, a), self.problem.domain.heuristic(newstate, self.problem.goal))
                    lnewnodes.append(newnode)
                    if newnode.cost > self.highest_cost_nodes[0].cost:
                        self.highest_cost_nodes = [newnode]
                    elif newnode.cost == self.highest_cost_nodes[0].cost:
                        self.highest_cost_nodes.append(newnode)
                    self._total_depth += newnode.depth
            self.add_to_open(lnewnodes)
            self.terminals += len(lnewnodes)
            self.total_branching += len(lnewnodes)
        return None

    # juntar novos nos a lista de nos abertos de acordo com a estrategia
    def add_to_open(self,lnewnodes):
        if self.strategy == 'breadth':
            self.open_nodes.extend(lnewnodes)
        elif self.strategy == 'depth':
            self.open_nodes[:0] = lnewnodes
        elif self.strategy == 'uniform':
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.cost)
        elif self.strategy == "greedy":
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.heuristic)
        elif self.strategy == 'a*':
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.cost + node.heuristic)
            
