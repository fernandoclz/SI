from StateMachine.State import State
from States.AgentConsts import AgentConsts
from MyProblem.BCProblem import BCProblem


class ExecutePlan(State):

    def __init__(self, id):
        super().__init__(id)
        self.nextNode = 0
        self.lastMove = 0
        self.transition = ""

    def Start(self, agent):
        self.agent = agent
        self.transition = ""
        self.XPos = -1
        self.YPos = -1
        self.noMovements = 0

    def Update(self, perception, map, agent):
        shot = False
        move = self.lastMove
        xW = perception[AgentConsts.AGENT_X]
        yW = perception[AgentConsts.AGENT_Y]
        distance = abs(self.XPos - xW) + abs(self.YPos - yW)
        self.XPos = xW
        self.YPos = yW
        if distance < 0.1:
            self.noMovements += 1
        else:
            self.noMovements = 0

        x, y = BCProblem.WorldToMapCoordFloat(xW, yW, agent.problem.ySize)

        plan = agent.GetPlan()
        if len(plan) == 0:
            agent.goalMonitor.ForceToRecalculate()
            return AgentConsts.NO_MOVE, False

        nextNode = plan[0]
        if self.IsInNode(nextNode, x, y, self.lastMove, 0.17) and len(plan) >= 1:
            plan.pop(0)
            if len(plan) == 0:
                agent.goalMonitor.ForceToRecalculate()
                return AgentConsts.NO_MOVE, False
            nextNode = plan[0]

        goal = agent.problem.GetGoal()

        # Oportunidad de disparo en ruta: si el jugador está alineado, disparamos sin detenernos
        if perception[AgentConsts.PLAYER_X] >= 0:
            shot = self._opportunistic_shot(perception)

        # Al llegar al último nodo hacia un objetivo atacable, transitamos a Ataque
        if len(plan) <= 1 and (goal.value == AgentConsts.PLAYER or
                               goal.value == AgentConsts.COMMAND_CENTER):
            self.transition = "Ataque"
            move = self.GetDirection(nextNode, x, y)
            agent.directionToLook = move - 1
            shot = shot or (self.lastMove == move and perception[AgentConsts.CAN_FIRE] == 1)
        elif len(plan) <= 1 and goal.value == AgentConsts.EXIT:
            # Llegamos a la salida: replanificamos (el juego debería terminar o buscar otro objetivo)
            agent.goalMonitor.ForceToRecalculate()
            move = self.GetDirection(nextNode, x, y)
        else:
            move = self.GetDirection(nextNode, x, y)
            # Disparar para romper ladrillos en ruta
            if nextNode.value == AgentConsts.BRICK or nextNode.value == AgentConsts.COMMAND_CENTER:
                shot = True

        self.lastMove = move
        return move, shot

    def Transit(self, perception, map):
        # Bala entrante: reacción inmediata
        if self._bala_entrante(perception):
            return "Defensa"

        # Vida baja y power-up disponible: solo si el goal actual NO es ya la vida
        if perception[AgentConsts.HEALTH] <= 1 and perception[AgentConsts.LIFE_X] >= 0:
            goal = self.agent.problem.GetGoal() if hasattr(self.agent, 'problem') and self.agent.problem else None
            if goal is None or goal.value != AgentConsts.LIFE:
                return "Huida"

        # Transición solicitada por Update (p.ej. a Ataque)
        if self.transition is not None and self.transition != "":
            t = self.transition
            self.transition = ""
            return t

        # Atascado: reseteamos y dejamos que GoalMonitor replanifique
        if self.noMovements > 5:
            self.noMovements = 0
            if hasattr(self.agent, 'goalMonitor'):
                self.agent.goalMonitor.ForceToRecalculate()
                
            # Si tienes un estado de "Idle" o "Espera", podrías transicionar a él aquí,
            # pero si retornas self.id, al menos ahora el plan estará vacío en el próximo Update
            # y se generará una nueva ruta.
            return self.id

        return self.id

    # ------------------------------------------------------------------ #
    # Disparo oportunista en ruta                                          #
    # ------------------------------------------------------------------ #

    def _opportunistic_shot(self, perception):
        """Dispara al jugador si está alineado y podemos disparar, sin interrumpir la navegación."""
        if perception[AgentConsts.CAN_FIRE] != 1:
            return False
        ax, ay = perception[AgentConsts.AGENT_X], perception[AgentConsts.AGENT_Y]
        px, py = perception[AgentConsts.PLAYER_X], perception[AgentConsts.PLAYER_Y]
        dx, dy = px - ax, py - ay
        orientation = perception[AgentConsts.TANK_ORIENTATION]
        # Alineado en X (mismo carril horizontal)
        if abs(dy) < 0.6:
            if dx > 0 and orientation == AgentConsts.MOVE_RIGHT:
                return True
            if dx < 0 and orientation == AgentConsts.MOVE_LEFT:
                return True
        # Alineado en Y (mismo carril vertical)
        if abs(dx) < 0.6:
            if dy > 0 and orientation == AgentConsts.MOVE_DOWN:
                return True
            if dy < 0 and orientation == AgentConsts.MOVE_UP:
                return True
        return False

    # ------------------------------------------------------------------ #
    # Utilidades estáticas                                                 #
    # ------------------------------------------------------------------ #

    def _bala_entrante(self, perception):
        dirs = [
            (AgentConsts.NEIGHBORHOOD_UP,    AgentConsts.NEIGHBORHOOD_DIST_UP),
            (AgentConsts.NEIGHBORHOOD_DOWN,  AgentConsts.NEIGHBORHOOD_DIST_DOWN),
            (AgentConsts.NEIGHBORHOOD_LEFT,  AgentConsts.NEIGHBORHOOD_DIST_LEFT),
            (AgentConsts.NEIGHBORHOOD_RIGHT, AgentConsts.NEIGHBORHOOD_DIST_RIGHT),
        ]
        for dir_idx, dist_idx in dirs:
            if perception[dir_idx] == AgentConsts.SHELL and perception[dist_idx] < 5:
                return True
        return False

    @staticmethod
    def MoveDown(node, x, y):
        return abs(node.x + 0.5 - x) <= abs(node.y + 0.5 - y) and (node.y + 0.5) >= y

    @staticmethod
    def MoveUp(node, x, y):
        return abs(node.x + 0.5 - x) <= abs(node.y + 0.5 - y) and (node.y + 0.5) <= y

    @staticmethod
    def MoveRight(node, x, y):
        return abs(node.x + 0.5 - x) >= abs(node.y + 0.5 - y) and (node.x + 0.5) >= x

    @staticmethod
    def MoveLeft(node, x, y):
        return abs(node.x + 0.5 - x) >= abs(node.y + 0.5 - y) and (node.x + 0.5) <= x

    @staticmethod
    def IsInNode(node, x, y, lastDir, threshold):
        distanceX = abs((node.x + 0.5) - x)
        distanceY = abs((node.y + 0.5) - y)
        if distanceX < threshold and distanceY < threshold:
            return True
        directionX, directionY = ExecutePlan.GetDirectionVector(lastDir)
        simulateX = x + directionX * threshold
        simulateY = y + directionY * threshold
        if (abs((node.x + 0.5) - simulateX) + abs((node.y + 0.5) - simulateY)) > (distanceX + distanceY):
            return True
        return False

    @staticmethod
    def GetDirectionVector(direction):
        if direction == AgentConsts.NO_MOVE:   return 0.0,  0.0
        if direction == AgentConsts.MOVE_UP:   return 0.0, -1.0
        if direction == AgentConsts.MOVE_DOWN: return 0.0,  1.0
        if direction == AgentConsts.MOVE_RIGHT: return 1.0, 0.0
        return -1.0, 0.0

    def GetDirection(self, current_node, x, y):
        target_x = current_node.x + 0.5
        target_y = current_node.y + 0.5
        diff_x = target_x - x
        diff_y = target_y - y
        
        # Tolerancia dinámica: si ya estamos alineados, permitimos más error
        # para evitar el "serpenteo"
        tolerance = 0.15

        # Si la diferencia en un eje es mínima, ignoramos la corrección de ese eje
        if abs(diff_x) < 0.1: diff_x = 0
        if abs(diff_y) < 0.1: diff_y = 0

        # Priorizar el eje donde la distancia es mayor
        if abs(diff_x) > abs(diff_y):
            # Si el desvío lateral (Y) es muy grande, corregimos antes de avanzar en X
            if abs(diff_y) > tolerance:
                return AgentConsts.MOVE_DOWN if diff_y > 0 else AgentConsts.MOVE_UP
            return AgentConsts.MOVE_RIGHT if diff_x > 0 else AgentConsts.MOVE_LEFT
        else:
            # Si el desvío lateral (X) es muy grande, corregimos antes de avanzar en Y
            if abs(diff_x) > tolerance:
                return AgentConsts.MOVE_RIGHT if diff_x > 0 else AgentConsts.MOVE_LEFT
            return AgentConsts.MOVE_DOWN if diff_y > 0 else AgentConsts.MOVE_UP