class AStar:

    def __init__(self, problem):
        self.open = []
        self.precessed = set()
        self.problem = problem

    def GetPlan(self):
        self.open.clear()
        self.precessed.clear()

        start_node = self.problem.Initial()
        self._ConfigureNode(start_node, None, 0)
        self.open.append(start_node)

        while len(self.open) > 0:
            self.open.sort(key=lambda n: n.G() + n.H())
            current = self.open.pop(0)

            if self.problem.IsASolution(current):
                return self.ReconstructPath(current)

            self.precessed.add((current.x, current.y))

            for sucesor in self.problem.GetSucessors(current):
                if (sucesor.x, sucesor.y) in self.precessed:
                    continue

                tentative_g = current.G() + self.problem.GetGCostBetween(current, sucesor)

                nodo_en_abierta = self.GetSucesorInOpen(sucesor)
                if nodo_en_abierta is None:
                    self._ConfigureNode(sucesor, current, tentative_g)
                    self.open.append(sucesor)
                else:
                    if tentative_g < nodo_en_abierta.G():
                        self._ConfigureNode(nodo_en_abierta, current, tentative_g)

        return []

    def _ConfigureNode(self, node, parent, newG):
        node.SetParent(parent)
        node.SetG(newG)
        node.SetH(self.problem.Heuristic(node))

    def GetSucesorInOpen(self, sucesor):
        for node in self.open:
            if node.IsEqual(sucesor):
                return node
        return None

    def ReconstructPath(self, goal):
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = current.GetParent()
        return path[::-1]