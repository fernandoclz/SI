from AStar.Problem import Problem
from MyProblem.BCNode import BCNode
from States.AgentConsts import AgentConsts
import sys
import numpy as np


class BCProblem(Problem):

    def __init__(self, initial, goal, xSize, ySize):
        super().__init__(initial, goal)
        self.map = np.zeros((xSize, ySize), dtype=int)
        self.xSize = xSize
        self.ySize = ySize

    def InitMap(self, m):
        for i in range(len(m)):
            x, y = BCProblem.Vector2MatrixCoord(i, self.xSize, self.ySize)
            self.map[x][y] = m[i]

    # Muestra el mapa por consola
    def ShowMap(self):
        for j in range(self.ySize):
            s = ""
            for i in range(self.xSize):
                s += ("[" + str(i) + "," + str(j) + "," + str(self.map[i][j]) + "]")
            print(s)

    # Heurística: distancia Manhattan hasta la meta
    def Heuristic(self, node):
        goal = self.getGoal()
        if goal is None:
            return 0
        return abs(node.x - goal.x) + abs(node.y - goal.y)

    # Genera la lista de sucesores del nodo dado (4-conectividad: arriba/abajo/izq/der)
    def GetSucessors(self, node):
        successors = []
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        for dx, dy in directions:
            nx, ny = node.x + dx, node.y + dy
            # Comprobamos que la casilla está dentro de los límites del mapa
            if 0 <= nx < self.xSize and 0 <= ny < self.ySize:
                value = self.map[nx][ny]
                cost = BCProblem.GetCost(value)
                # Solo añadimos si el coste no es infinito (casilla transitable o rompible)
                if cost < sys.maxsize:
                    nuevo_nodo = BCNode(None, cost, value, nx, ny)
                    successors.append(nuevo_nodo)
        return successors

    # ------------------------------------------------------------------ #
    # Métodos estáticos                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def CanMove(value):
        return (value != AgentConsts.UNBREAKABLE and
                value != AgentConsts.SEMI_UNBREKABLE)

    # Convierte posición en formato vector a coordenadas (x, y) de la matriz
    @staticmethod
    def Vector2MatrixCoord(pos, xSize, ySize):
        x = pos % xSize
        y = pos // xSize  # división entera por xSize (número de columnas)
        return x, y

    # Convierte coordenadas (x, y) de la matriz a posición en formato vector
    @staticmethod
    def Matrix2VectorCoord(x, y, xSize):
        return y * xSize + x

    # Coordenadas mapa -> coordenadas mundo (la Y está invertida en el motor)
    @staticmethod
    def MapToWorldCoord(x, y, ySize):
        xW = x * 2
        yW = (ySize - y - 1) * 2
        return xW, yW

    # Coordenadas mundo -> coordenadas mapa (la Y está invertida en el motor)
    @staticmethod
    def WorldToMapCoord(xW, yW, ySize):
        x = int(xW) // 2
        y = int(yW) // 2
        y = ySize - y - 1
        return x, y

    # Versión flotante para buscar los centros de las celdas con precisión
    @staticmethod
    def WorldToMapCoordFloat(xW, yW, ySize):
        x = xW / 2
        invY = (ySize * 2) - yW
        invY = invY / 2
        return x, invY

    # Coste de paso según el tipo de casilla del mapa
    @staticmethod
    def GetCost(value):
        # Casillas transitables sin coste extra
        if value == AgentConsts.NOTHING or value == AgentConsts.COMMAND_CENTER:
            return 1
        # Casillas rompibles: tienen coste mayor (hay que disparar para pasar)
        elif value == AgentConsts.BRICK or value == AgentConsts.SEMI_BREKABLE:
            return 3
        # Muros irrompibles: coste infinito, no se pueden atravesar
        else:
            return sys.maxsize

    # Crea un nodo y lo añade a successors con el padre indicado
    def CreateNode(self, successors, parent, x, y):
        value = self.map[x][y]
        g = BCProblem.GetCost(value)
        rightNode = BCNode(parent, g, value, x, y)
        rightNode.SetH(self.Heuristic(rightNode))
        successors.append(rightNode)

    # Coste de moverse al nodo destino (g-cost del paso)
    def GetGCost(self, nodeTo):
        return BCProblem.GetCost(nodeTo.value)