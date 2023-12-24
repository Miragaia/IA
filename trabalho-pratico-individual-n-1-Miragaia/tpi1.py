#STUDENT NAME: Miguel Aido Miragaia
#STUDENT NUMBER: 108317

#DISCUSSED TPI-1 WITH: (names and numbers):
#Tomás Matos 108624

from tree_search import *
import math

class OrderDelivery(SearchDomain):

    def __init__(self,connections, coordinates):
        self.connections = connections
        self.coordinates = coordinates
        # ANY NEEDED CODE CAN BE ADDED HERE
        self.map = {}
        for a, b, c in connections:
            self.map.setdefault(a, {})[b] = c
            self.map.setdefault(b, {})[a] = c

    def actions(self,state):
        city = state[0]
        actlist = []
        for (C1,C2,D) in self.connections:
            if (C1==city):
                actlist += [(C1,C2)]
            elif (C2==city):
               actlist += [(C2,C1)]
        return actlist 

    def result(self,state,action):
        #IMPLEMENT HERE
        city = state[0]
        targets = state[1:-1]
        start = state[-1]
        next = action[1]
        for t in targets:
            if t == next:
                targets.remove(t)
        return ([next] + targets + [start])

    def satisfies(self, state, goal):
        #IMPLEMENT HERE
        city = state[0]
        targets = state[1:-1]
        possible_goal = state[-1]
        if city == goal and targets == []:
            return True
        else:
            return False

    def cost(self, state, action):
        #IMPLEMENT HERE
        source = action[0]
        destination = action[1]
        return self.map[source][destination]
    
    def heuristic(self, state, goal):
        #IMPLEMENT HERE
        city = state[0]
        targets = state[1:-1]
        if targets == []:
            return 0
        [x1, y1] = self.coordinates[city]
        d = 0
        for t in targets:
            [x2, y2] = self.coordinates[t]
            d += abs(x1 - x2) + abs(y1 - y2)
        return d/len(targets)

 
class MyNode(SearchNode):

    def __init__(self,state,parent,depth= 0,cost= 0,heuristic = 0,eval = 0, marked_for_deletion=False):
        super().__init__(state,parent)
        #ADD HERE ANY CODE YOU NEED
        self.state = state
        self.parent = parent
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic
        self.eval = eval
        self.marked_for_deletion = marked_for_deletion

class MyTree(SearchTree):

    def __init__(self,problem, strategy='breadth',maxsize=None):
        super().__init__(problem,strategy)
        #ADD HERE ANY CODE YOU NEED
        self.maxsize = maxsize
        root = MyNode(problem.initial, None)
        self.open_nodes = [root]
        self.solution = None
        self.non_terminals = 0
        self.terminals = 0 

    def astar_add_to_open(self,lnewnodes):
        if self.strategy == 'breadth':
            self.open_nodes.extend(lnewnodes)
        elif self.strategy == 'A*':
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda node: (node.eval, node.state[0]))

    def search2(self):  
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            if self.problem.goal_test(node.state):
                self.solution = node
                self.terminals = len(self.open_nodes) + 1  #aqui
                return self.get_path(node)
            self.non_terminals += 1
            lnewnodes = []
            for action in self.problem.domain.actions(node.state):
                newstate = self.problem.domain.result(node.state, action)
                if newstate not in self.get_path(node):
                    newnode = MyNode(newstate, node)
                    newnode.depth = node.depth + 1
                    newnode.cost = node.cost + self.problem.domain.cost(node.state, action)
                    newnode.heuristic = self.problem.domain.heuristic(newstate, self.problem.goal)
                    newnode.eval = newnode.cost + newnode.heuristic
                    lnewnodes.append(newnode)
            
            self.terminals = len(self.open_nodes) + 1
            #print(len(self.open_nodes))
            #print(self.terminals)
            #print(self.non_terminals)
            self.add_to_open(lnewnodes)
            if self.strategy == 'A*' and self.maxsize is not None and (len(self.open_nodes) + self.non_terminals) > self.maxsize:
                #print("DEUUU")
                self.manage_memory()

            
        return None

    def manage_memory(self):
        #IMPLEMENT HERE
        # Sort nodes by eval in descending order (highest eval first)
        self.open_nodes.sort(key=lambda node: node.eval, reverse=True)
        soma_nos = len(self.open_nodes)+ self.non_terminals
        while soma_nos > self.maxsize:
            node = self.open_nodes.pop()
            self.non_terminals -= 1
            if not node.marked_for_deletion:
                # Mark the node for deletion
                node.marked_for_deletion = True

                # Check if there are any siblings not marked for deletion
                parent = node.parent
                siblings = [n for n in self.open_nodes if n.parent == parent and not n.marked_for_deletion]
                #print(siblings)
                if not siblings:
                    continue

                # Calculate the minimum eval value from non-deleted siblings
                min_eval = min(child.eval for child in siblings)

                # Set the parent's eval to the minimum eval value
                parent.eval = min_eval
                soma_nos -= len(siblings)

        # After managing memory, re-sort the open list
        self.open_nodes.sort(key=lambda node: (node.eval, node.state[0]))


def orderdelivery_search(domain,city,targetcities,strategy='breadth',maxsize=None):
    #IMPLEMENT HERE
    initial_state = [city] + targetcities + [city]
    problem = SearchProblem(domain, initial_state, city)
    tree = MyTree(problem, strategy, maxsize)
    path = tree.search2()

    if path:
        export_path = [node[0] for node in path]
        return tree, export_path

# If needed, auxiliary functions can be added here


