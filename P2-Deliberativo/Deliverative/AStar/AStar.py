
#Algoritmo A* genérico que resuelve cualquier problema descrito usando la plantilla de la
#la calse Problem que tenga como nodos hijos de la clase Node
class AStar:

    def __init__(self, problem):
        self.open = [] # lista de abiertos o frontera de exploración
        self.precessed = set() # set, conjunto de cerrados (más eficiente que una lista)
        self.problem = problem #problema a resolver

    def GetPlan(self):
        #Implementar el algoritmo A*
        #cosas a tener en cuenta:
        #Si el número de sucesores es 0 es que el algoritmo no ha encontrado una solución, devolvemos el path vacio []
        #Hay que invertir el path para darlo en el orden correcto al devolverlo (path[::-1])
        #GetSucesorInOpen(sucesor) nos devolverá None si no lo encuentra, si lo encuentra
        #es que ese sucesor ya está en la frontera de exploración, DEBEMOS MIRAR SI EL NUEVO COSTE ES MENOR QUE EL QUE TENIA ALMACENADO
        #SI esto es asi, hay que cambiarle el padre y setearle el nuevo coste.
        self.open.clear()
        self.precessed.clear()
        start_node = self.problem.Initial()
        self._ConfigureNode(start_node, None, 0)
        self.open.append(self.problem.Initial())
        path = []
        #mientras no encontremos la meta y haya elementos en open....
        #TODO implementar el bucle de búsqueda del algoritmo A*
        while len(self.open) > 0:
            self.open.sort(key=lambda n: n.g + n.h)
            current = self.open.pop(0)

            if self.problem.IsGoal(current):
                return self.ReconstructPath(current)
            
            self.precessed.add((current.x, current.y))

            for sucesor in self.problem.getSuccesors(current):
                if (sucesor.x, sucesor.y) in self.precessed:
                    continue    
                map_val = self.problem.GetCost(map_val)
                coste_paso = self.problem.GetCost(map_val)
                tentative_g = current.g + coste_paso
                
                nodo_en_abierta = self.GetSucesorInOpen(sucesor)
                if nodo_en_abierta is None:
                    self._ConfigureNode(sucesor, current, tentative_g)
                    self.open.append(sucesor)
                else:
                    if tentative_g < nodo_en_abierta.g:
                        self._ConfigureNode(nodo_en_abierta, current, tentative_g)
        return path

    #nos permite configurar un nodo (node) con el padre y la nueva G
    def _ConfigureNode(self, node, parent, newG):
        node.SetParent(parent)
        node.SetG(newG)
        #TODO Setearle la heuristica que está implementada en el problema. (si ya la tenía será la misma pero por si reutilizais este método para otras cosas)
        heuristica = self.problem.Heuristic(node)

        if hasattr(node, 'SetH'):
            node.SetH(heuristica)
        else:
            node.h = heuristica


    def ApendInOpen(self, node):
        if node.g == None:
            print("ApendInOpen ", node.x, node.y)
        self.open.append(node)

    #nos dice si un sucesor está en abierta. Si esta es que ya ha sido expandido y tendrá un coste, comprobar que le nuevo camino no es más eficiente
    #En caso de serlos, _ConfigureNode para setearle el nuevo padre y el nuevo G, asi como su heurística
    def GetSucesorInOpen(self,sucesor):
        i = 0
        found = None
        while found == None and i < len(self.open):
            node = self.open[i]
            i += 1
            if hasattr(node, 'IsEqual'):
                if node.IsEqual(sucesor):
                    found = node
            elif node == sucesor:
                found = node
        return found

    #reconstruye el path desde la meta encontrada.
    def ReconstructPath(self, goal):
        path = []
        #Devuelve el path invertido desde la meta hasta que el padre sea None.
        current = goal
        
        # Retrocedemos desde la meta hasta el inicio saltando de padre en padre
        while current is not None:
            path.append(current)
            # Usamos el getter si existe, sino la propiedad directa
            if hasattr(current, 'GetParent'):
                current = current.GetParent()
            else:
                current = current.parent
                
        # devolvemos el path invertido [::-1] para que vaya de Inicio -> Meta
        return path[::-1] 
      



