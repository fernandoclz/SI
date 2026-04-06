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
            self.map[x][y] = int(m[i])  # cast explícito para evitar np.int64

    def ShowMap(self):
        for j in range(self.ySize):
            s = ""
            for i in range(self.xSize):
                s += ("[" + str(i) + "," + str(j) + "," + str(self.map[i][j]) + "]")
            print(s)

    def Heuristic(self, node):
        goal = self.GetGoal()
        if goal is None:
            return 0
        return abs(node.x - goal.x) + abs(node.y - goal.y)

    def GetSucessors(self, node):
        successors = []
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        for dx, dy in directions:
            nx, ny = node.x + dx, node.y + dy
            if 0 <= nx < self.xSize and 0 <= ny < self.ySize:
                value = int(self.map[nx][ny])  # cast explícito
                cost = BCProblem.GetCost(value)
                if cost < sys.maxsize:
                    nuevo_nodo = BCNode(None, cost, value, nx, ny)
                    successors.append(nuevo_nodo)
        return successors

    def GetGCostBetween(self, nodeFrom, nodeTo):
        return BCProblem.GetCost(nodeTo.value)

    # ------------------------------------------------------------------ #
    # Métodos estáticos                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def CanMove(value):
        return (value != AgentConsts.UNBREAKABLE and
                value != AgentConsts.SEMI_UNBREKABLE)

    @staticmethod
    def Vector2MatrixCoord(pos, xSize, ySize):
        x = pos % xSize
        y = pos // xSize
        return x, y

    @staticmethod
    def Matrix2VectorCoord(x, y, xSize):
        return y * xSize + x

    @staticmethod
    def MapToWorldCoord(x, y, ySize):
        xW = x * 2
        yW = (ySize - y - 1) * 2
        return xW, yW

    @staticmethod
    def WorldToMapCoord(xW, yW, ySize):
        x = int(xW) // 2
        y = int(yW) // 2
        y = ySize - y - 1
        return x, y

    @staticmethod
    def WorldToMapCoordFloat(xW, yW, ySize):
        x = xW / 2
        invY = (ySize * 2) - yW
        invY = invY / 2
        return x, invY

    @staticmethod
    def GetCost(value):
        value = int(value)  # cast defensivo
        if value == AgentConsts.NOTHING or value == AgentConsts.COMMAND_CENTER:
            return 1
        elif value == AgentConsts.BRICK or value == AgentConsts.SEMI_BREKABLE:
            return 3
        else:
            return sys.maxsize

    def CreateNode(self, successors, parent, x, y):
        value = int(self.map[x][y])
        g = BCProblem.GetCost(value)
        rightNode = BCNode(parent, g, value, x, y)
        rightNode.SetH(self.Heuristic(rightNode))
        successors.append(rightNode)