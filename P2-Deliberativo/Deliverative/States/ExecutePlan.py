from StateMachine.State import State
from States.AgentConsts import AgentConsts
from MyProblem.BCProblem import BCProblem
import random


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
        self.stuckCounter = 0          # ticks consecutivos en la misma posición exacta
        self.lastExactPos = (-1, -1)   # posición exacta del tick anterior
        self.escapeMove = None         # movimiento de escape activo
        self.escapeTicks = 0           # ticks restantes de escape

    def Update(self, perception, map, agent):
        shot = False
        move = self.lastMove
        xW = perception[AgentConsts.AGENT_X]
        yW = perception[AgentConsts.AGENT_Y]

        # --- Detección de atasco por posición congelada ---
        # Usamos la posición exacta del servidor (sin float drift) para detectar
        # que realmente no nos hemos movido ni un píxel
        currentPos = (round(xW, 3), round(yW, 3))
        if currentPos == self.lastExactPos:
            self.stuckCounter += 1
            shot =True
        else:
            self.stuckCounter = 0
        self.lastExactPos = currentPos

        # --- Detección de atasco por distancia acumulada (backup) ---
        distance = abs(self.XPos - xW) + abs(self.YPos - yW)
        self.XPos = xW
        self.YPos = yW
        if distance < 0.05:
            self.noMovements += 1
        else:
            self.noMovements = 0

        # --- Modo escape activo: ignoramos el plan y empujamos en dirección libre ---
        if self.escapeTicks > 0:
            self.escapeTicks -= 1
            self.lastMove = self.escapeMove
            return self.escapeMove, False

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

        if goal.value == AgentConsts.PLAYER or goal.value == AgentConsts.COMMAND_CENTER:
            tx = perception[AgentConsts.PLAYER_X] if perception[AgentConsts.PLAYER_X] >= 0 \
                 else perception[AgentConsts.COMMAND_CENTER_X]
            ty = perception[AgentConsts.PLAYER_Y] if perception[AgentConsts.PLAYER_Y] >= 0 \
                 else perception[AgentConsts.COMMAND_CENTER_Y]
            if tx >= 0 and ty >= 0:
                TOLERANCIA_ALINEAMIENTO = 0.6  # margen en unidades de mundo
                aligned = abs(ty - yW) <= TOLERANCIA_ALINEAMIENTO or \
                          abs(tx - xW) <= TOLERANCIA_ALINEAMIENTO
                if aligned:
                    print(f"[ExecutePlan] Alineado con objetivo → Ataque (dx={tx-xW:.2f}, dy={ty-yW:.2f})")
                    self.transition = "Ataque"

        # Disparo oportunista en ruta
        if perception[AgentConsts.PLAYER_X] >= 0:
            shot = self._opportunistic_shot(perception)

        if len(plan) <= 1 and (goal.value == AgentConsts.PLAYER or
                               goal.value == AgentConsts.COMMAND_CENTER):
            dist_to_node_x = abs((nextNode.x + 0.5) - x)
            dist_to_node_y = abs((nextNode.y + 0.5) - y)
            if dist_to_node_x < 0.17 and dist_to_node_y < 0.17:
                self.transition = "Ataque"
                return AgentConsts.NO_MOVE, shot

            move = self.GetDirection(nextNode, x, y)
            agent.directionToLook = move - 1
            shot = shot or (self.lastMove == move and perception[AgentConsts.CAN_FIRE] == 1)

        elif len(plan) <= 1 and goal.value == AgentConsts.EXIT:
            move = self.GetDirection(nextNode, x, y)
            dist_x = abs((nextNode.x + 0.5) - x)
            dist_y = abs((nextNode.y + 0.5) - y)
            if dist_x < 0.15 and dist_y < 0.15:
                move = AgentConsts.NO_MOVE
            if nextNode.value == AgentConsts.BRICK:
                shot = True
        else:
            move = self.GetDirection(nextNode, x, y)
            if nextNode.value == AgentConsts.BRICK or nextNode.value == AgentConsts.COMMAND_CENTER:
                shot = True

        self.lastMove = move
        return move, shot

    def Transit(self, perception, map):
        if self._bala_entrante(perception):
            return "Defensa"

        if perception[AgentConsts.HEALTH] <= 1 and perception[AgentConsts.LIFE_X] >= 0:
            goal = self.agent.problem.GetGoal() if hasattr(self.agent, 'problem') and self.agent.problem else None
            if goal is None or goal.value != AgentConsts.LIFE:
                return "Huida"

        if self.transition is not None and self.transition != "":
            t = self.transition
            self.transition = ""
            return t

        if self.stuckCounter > 4:
            self.stuckCounter = 0
            self.noMovements = 0
            self._activar_escape(perception)
            if hasattr(self.agent, 'goalMonitor'):
                self.agent.goalMonitor.ForceToRecalculate()
            return self.id

        # Backup: por distancia acumulada
        if self.noMovements > 3:
            self.noMovements = 0
            self.stuckCounter = 0
            self._activar_escape(perception)
            if hasattr(self.agent, 'goalMonitor'):
                self.agent.goalMonitor.ForceToRecalculate()
            return self.id

        return self.id

    def _activar_escape(self, perception):
        """
        Elige la dirección lateral libre (sin UNBREAKABLE inmediato) y activa
        el modo escape durante 3 ticks para sacar al agente del punto muerto.
        """
        # Orden de preferencia: perpendicular al último movimiento, luego el resto
        perp = {
            AgentConsts.MOVE_UP:    [AgentConsts.MOVE_RIGHT, AgentConsts.MOVE_LEFT,
                                     AgentConsts.MOVE_DOWN],
            AgentConsts.MOVE_DOWN:  [AgentConsts.MOVE_LEFT,  AgentConsts.MOVE_RIGHT,
                                     AgentConsts.MOVE_UP],
            AgentConsts.MOVE_RIGHT: [AgentConsts.MOVE_DOWN,  AgentConsts.MOVE_UP,
                                     AgentConsts.MOVE_LEFT],
            AgentConsts.MOVE_LEFT:  [AgentConsts.MOVE_UP,    AgentConsts.MOVE_DOWN,
                                     AgentConsts.MOVE_RIGHT],
            AgentConsts.NO_MOVE:    [AgentConsts.MOVE_RIGHT, AgentConsts.MOVE_DOWN,
                                     AgentConsts.MOVE_LEFT,  AgentConsts.MOVE_UP],
        }
        neighborhood = {
            AgentConsts.MOVE_UP:    (AgentConsts.NEIGHBORHOOD_UP,    AgentConsts.NEIGHBORHOOD_DIST_UP),
            AgentConsts.MOVE_DOWN:  (AgentConsts.NEIGHBORHOOD_DOWN,  AgentConsts.NEIGHBORHOOD_DIST_DOWN),
            AgentConsts.MOVE_RIGHT: (AgentConsts.NEIGHBORHOOD_RIGHT, AgentConsts.NEIGHBORHOOD_DIST_RIGHT),
            AgentConsts.MOVE_LEFT:  (AgentConsts.NEIGHBORHOOD_LEFT,  AgentConsts.NEIGHBORHOOD_DIST_LEFT),
        }

        candidates = perp.get(self.lastMove, list(neighborhood.keys()))
        chosen = None
        for direction in candidates:
            dir_idx, dist_idx = neighborhood[direction]
            cell = perception[dir_idx]
            dist = perception[dist_idx]
            # Libre si no hay UNBREAKABLE pegado (dist > 0.5 o celda no bloqueante)
            if cell != AgentConsts.UNBREAKABLE and (dist > 0.5 or dist == 0):
                chosen = direction
                break

        if chosen is None:
            # Todas bloqueadas: elegimos cualquiera que no sea UNBREAKABLE a 0 distancia
            chosen = random.choice(candidates)

        self.escapeMove = chosen
        self.escapeTicks = 3   # empujamos 3 ticks en esa dirección
        print(f"[ExecutePlan] ESCAPE activado → dir={chosen} (stuckCounter={self.stuckCounter})")

    # ------------------------------------------------------------------ #
    # Disparo oportunista en ruta                                          #
    # ------------------------------------------------------------------ #

    def _opportunistic_shot(self, perception):
        if perception[AgentConsts.CAN_FIRE] != 1:
            return False
        ax, ay = perception[AgentConsts.AGENT_X], perception[AgentConsts.AGENT_Y]
        px, py = perception[AgentConsts.PLAYER_X], perception[AgentConsts.PLAYER_Y]
        dx, dy = px - ax, py - ay
        orientation = perception[AgentConsts.TANK_ORIENTATION]
        if abs(dy) < 0.6:
            if dx > 0 and orientation == AgentConsts.MOVE_RIGHT:
                return True
            if dx < 0 and orientation == AgentConsts.MOVE_LEFT:
                return True
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
        
        if distanceX < 0.38 and distanceY < 0.38:
            return True
            
        return False

    @staticmethod
    def GetDirectionVector(direction):
        if direction == AgentConsts.NO_MOVE:    return 0.0,  0.0
        if direction == AgentConsts.MOVE_UP:    return 0.0, -1.0
        if direction == AgentConsts.MOVE_DOWN:  return 0.0,  1.0
        if direction == AgentConsts.MOVE_RIGHT: return 1.0,  0.0
        return -1.0, 0.0

    def GetDirection(self, current_node, x, y):
        target_x = current_node.x + 0.5
        target_y = current_node.y + 0.5
        diff_x = target_x - x
        diff_y = target_y - y

        tolerance = 0.25

        if abs(diff_x) < 0.15: diff_x = 0
        if abs(diff_y) < 0.15: diff_y = 0

        if abs(diff_x) > abs(diff_y):
            if abs(diff_y) > tolerance:
                return AgentConsts.MOVE_DOWN if diff_y > 0 else AgentConsts.MOVE_UP
            return AgentConsts.MOVE_RIGHT if diff_x > 0 else AgentConsts.MOVE_LEFT
        else:
            if abs(diff_x) > tolerance:
                return AgentConsts.MOVE_RIGHT if diff_x > 0 else AgentConsts.MOVE_LEFT
            return AgentConsts.MOVE_DOWN if diff_y > 0 else AgentConsts.MOVE_UP