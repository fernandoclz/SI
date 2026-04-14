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
        path = path[::-1]

        if len(path) <= 2:
            return path[1:] if len(path) > 1 else path 
        
        clean = [path[0]]

        for i in range(1, len(path) - 1):
            prev_node = path[i - 1]
            curr_node = path[i]
            next_node = path[i + 1]
            
            # Calcular vectores de dirección (deltas)
            dx1 = curr_node.x - prev_node.x
            dy1 = curr_node.y - prev_node.y
            
            dx2 = next_node.x - curr_node.x
            dy2 = next_node.y - curr_node.y
            
            # Si la dirección cambia, es una esquina. La guardamos.
            if dx1 != dx2 or dy1 != dy2:
                clean.append(curr_node)
                
        # 3. Siempre incluimos el nodo final (la meta)
        clean.append(path[-1])

        return clean[1:]