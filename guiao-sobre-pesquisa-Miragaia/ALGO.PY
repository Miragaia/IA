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
from math import hypot


# dominios de pesquisa
# permitem calcular as accoes possiveis em cada estado, etc
class SearchDomain(ABC):
    # construtor
    @abstractmethod
    def _init_(self):
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
        pass

    # test if the given "goal" is satisfied in "state"
    @abstractmethod
    def satisfies(self, state, goal):
        pass


# problemas concretos a resolver dentro de um determinado dominio
class SearchProblem:
    def _init_(self, domain, initial, goal):
        self.domain = domain
        self.initial = initial
        self.goal = goal

    def goal_test(self, state):
        return self.domain.satisfies(state, self.goal)

# nos de uma arvore de pesquisa


class SearchNode:
    def _init_(self, state, parent, depth=0, cost=0, heuristic=0, action=None):
        self.state = state
        self.parent = parent
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic
        self.action = action

    # previne ciclos na searchtree
    def in_parent(self, state: str):
        if self.parent == None:
            return False
        if self.parent.state == state:
            return True
        return self.parent.in_parent(state)

    def in_parent(self, state: list):
        if self.parent == None:
            return False
        if all(e in self.parent.state for e in state):
            return True
        return self.parent.in_parent(state)

    def in_parent(self, state: set):
        if self.parent == None:
            return False
        if all(e in self.parent.state for e in state):
            return True
        return self.parent.in_parent(state)

    def _str_(self):
        return "no(" + str(self.state) + "," + str(self.parent) + ")"

    def _repr_(self):
        return str(self)


# arvores de pesquisa
class SearchTree:
    # construtor
    def _init_(self, problem, strategy='breadth'):
        self.problem = problem
        root = SearchNode(problem.initial, None)
        self.open_nodes = [root]
        self.strategy = strategy
        self.solution = None

        self.terminals = 0
        self.non_terminals = 0

        self.highest_cost_nodes = [root]
        self._total_depth = 0

    # comprimento da solução desta árvore
    @property
    def length(self):
        return self.solution.depth

    # average branching ratio desta árvore
    @property
    def avg_branching(self):
        return (self.terminals + self.non_terminals - 1)/self.non_terminals

    # custo desta árvore
    @property
    def cost(self):
        return self.solution.cost

    # obter o caminho (sequencia de estados) da raiz ate um no
    def get_path(self, node):
        if node.parent == None:
            return [node.state]
        path = self.get_path(node.parent)
        path += [node.state]
        return (path)

    def get_operations(self, node):
        if node.parent == None:
            return []
        operations = self.get_operations(node.parent)
        operations += [node.action]
        return operations

    # procurar a solucao
    def search(self, limit=None):
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)

            if self.problem.goal_test(node.state):
                self.solution = node
                self.terminals = len(self.open_nodes) + 1
                self.accumulated_cost = node.cost
                self.average_depth = self._total_depth / (self.terminals + self.non_terminals)
                self.plan = self.get_operations(node)
                return self.get_path(node)

            lnewnodes = []
            for a in self.problem.domain.actions(node.state):
                newstate = self.problem.domain.result(node.state, a)
                if not node.in_parent(newstate) and (limit is None or node.depth < limit):
                    depth = node.depth + 1
                    cost = node.cost + self.problem.domain.cost(node.state, (node.state, newstate))
                    heuristic = self.problem.domain.heuristic(newstate, self.problem.goal)
                    action = a
                    newnode = SearchNode(newstate, node, depth, cost, heuristic, action)
                    lnewnodes.append(newnode)

                    self._total_depth += newnode.depth
                    if newnode.cost > self.highest_cost_nodes[0].cost:
                        self.highest_cost_nodes = [newnode]
                    elif newnode.cost == self.highest_cost_nodes[0].cost:
                        self.highest_cost_nodes.append(newnode)

            self.non_terminals += 1
            self.add_to_open(lnewnodes)

        return None

    # juntar novos nos a lista de nos abertos de acordo com a estrategia
    def add_to_open(self, lnewnodes):
        if self.strategy == 'breadth':  # adds new nodes in the end
            self.open_nodes.extend(lnewnodes)
        elif self.strategy == 'depth':  # adds new nodes in the beggining
            self.open_nodes[:0] = lnewnodes
        elif self.strategy == 'uniform':  # adds nodes with smaller cost before nodes with bigger cost
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.cost)
        elif self.strategy == 'greedy':  # adds new nodes with smaller heuristic first
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.heuristic)
        elif self.strategy == 'a*':  # joins uniform and greedy
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: node.cost + node.heuristic)