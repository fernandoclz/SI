from AStar.Node import Node

class BCNode(Node):
    def __init__(self, parent, g, value, x, y):
        super().__init__(parent, g)
        self.value = value
        self.x = int(x)
        self.y = int(y)

    def __repr__(self):
        return f"BCNode(x={self.x}, y={self.y}, g={self.G()}, h={self.H()})"

    def __eq__(self, other):
        if other is None:
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def IsEqual(self, node):
        # Dos nodos son iguales cuando sus coordenadas x e y son iguales
        if node is None:
            return False
        return self.x == node.x and self.y == node.y