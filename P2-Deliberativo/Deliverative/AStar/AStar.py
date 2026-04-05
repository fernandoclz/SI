# Algoritmo A* genérico que resuelve cualquier problema descrito usando la plantilla de la
# clase Problem que tenga como nodos hijos de la clase Node
class AStar:

    def __init__(self, problem):
        self.open = []          # lista de abiertos o frontera de exploración
        self.precessed = set()  # set, conjunto de cerrados (más eficiente que una lista)
        self.problem = problem  # problema a resolver

    def GetPlan(self):
        self.open.clear()
        self.precessed.clear()

        start_node = self.problem.Initial()
        self._ConfigureNode(start_node, None, 0)
        self.open.append(start_node)

        while len(self.open) > 0:
            # Ordenamos por f = g + h y cogemos el nodo con menor coste
            self.open.sort(key=lambda n: n.G() + n.H())
            current = self.open.pop(0)

            # ¿Hemos llegado a la meta?
            if self.problem.IsGoal(current):
                return self.ReconstructPath(current)

            # Marcamos el nodo como procesado
            self.precessed.add((current.x, current.y))

            # Generamos los sucesores del nodo actual
            sucesores = self.problem.GetSucessors(current)

            for sucesor in sucesores:
                # Si ya está en cerrados, lo ignoramos
                if (sucesor.x, sucesor.y) in self.precessed:
                    continue

                # Coste acumulado para llegar a este sucesor por este camino
                tentative_g = current.G() + self.problem.GetGCost(sucesor)

                nodo_en_abierta = self.GetSucesorInOpen(sucesor)
                if nodo_en_abierta is None:
                    # No está en abiertos: lo configuramos y añadimos
                    self._ConfigureNode(sucesor, current, tentative_g)
                    self.open.append(sucesor)
                else:
                    # Ya está en abiertos: si encontramos un camino mejor, actualizamos
                    if tentative_g < nodo_en_abierta.G():
                        self._ConfigureNode(nodo_en_abierta, current, tentative_g)

        # Sin solución: devolvemos lista vacía
        return []

    # Configura un nodo con su padre, su G y su heurística
    def _ConfigureNode(self, node, parent, newG):
        node.SetParent(parent)
        node.SetG(newG)
        node.SetH(self.problem.Heuristic(node))

    def ApendInOpen(self, node):
        self.open.append(node)

    # Busca si un sucesor ya está en la lista de abiertos
    def GetSucesorInOpen(self, sucesor):
        for node in self.open:
            if node.IsEqual(sucesor):
                return node
        return None

    # Reconstruye el path desde la meta hasta el inicio y lo devuelve invertido (Inicio -> Meta)
    def ReconstructPath(self, goal):
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = current.GetParent()
        return path[::-1]