from Agent.BaseAgent import BaseAgent
from StateMachine.StateMachine import StateMachine
from States.ExecutePlan import ExecutePlan
from GoalMonitor import GoalMonitor
from AStar.AStar import AStar
from MyProblem.BCNode import BCNode
from MyProblem.BCProblem import BCProblem
from States.AgentConsts import AgentConsts
from States.AtaqueSt import AtaqueSt
from States.DefensaSt import DefensaSt
from States.HuidaSt import HuidaSt


class GoalOrientedAgent(BaseAgent):

    # Dimensiones del mapa en coordenadas de mapa (no de mundo)
    MAP_X_SIZE = 15
    MAP_Y_SIZE = 15

    def __init__(self, id, name):
        super().__init__(id, name)
        dictionary = {
            "ExecutePlan": ExecutePlan("ExecutePlan"),
            "Ataque":      AtaqueSt("Ataque"),
            "Defensa":     DefensaSt("Defensa"),
            "Huida":       HuidaSt("Huida"),
        }
        self.stateMachine = StateMachine("GoalOrientedBehavior", dictionary, "ExecutePlan")
        self.problem     = None
        self.aStar       = None
        self.plan        = None
        self.goalMonitor = None
        self.agentInit   = False

    def Start(self):
        print("Inicio del agente GoalOriented")
        self.stateMachine.Start(self)
        self.problem     = None
        self.aStar       = None
        self.plan        = None
        self.goalMonitor = None
        self.agentInit   = False

    def Update(self, perception, map):
        if perception is True or perception is False: return 0, True
        if not self.agentInit:
            self.InitAgent(perception, map)
            self.agentInit = True

        # 1. ACTUALIZAR OBJETIVOS (Percepción fresca)
        if perception[AgentConsts.PLAYER_X] >= 0:
            goal3Player = self._CreatePlayerGoal(perception)
            self.goalMonitor.UpdateGoals(goal3Player, GoalMonitor.GOAL_PLAYER)

        # 2. REPLANIFICAR SI ES NECESARIO (Antes de moverte)
        # Añadimos "or not self.plan" por seguridad
        if self.goalMonitor.NeedReplaning(perception, map, self) or not self.plan or len(self.plan) == 0:
            self.problem.InitMap(map)
            self.plan = self._CreatePlan(perception, map)
            print(f"🔄 Plan actualizado/generado. Pasos: {len(self.plan) if self.plan else 0}")

        # 3. ACTUAR (Con el plan ya listo)
        action, shot = self.stateMachine.Update(perception, map, self)

        # 4. DEBUG A PRUEBA DE BALAS
        # Si curentState es un objeto usamos su .id, si es un string (que es lo que te daba el error), lo casteamos directo.
        curr_state = self.stateMachine.curentState
        state_name = curr_state.id if hasattr(curr_state, 'id') else str(curr_state)
        
        # Extraemos el goal de forma segura
        goal = self.problem.GetGoal() if self.problem else None
        goal_val = goal.value if goal else "NONE"
        
        plan_len = len(self.plan) if self.plan else 0
        
        # Sacamos la posición actual del agente para compararla con el plan
        ag_x = perception[AgentConsts.AGENT_X]
        ag_y = perception[AgentConsts.AGENT_Y]
        
        # Un print limpio y alineado
        print(f"[{state_name[:12]:<12}] Pos:({ag_x:.1f}, {ag_y:.1f}) | Goal:{goal_val} | Plan:{plan_len:2} | Act:{action} | Shot:{shot}")
        
        if plan_len > 0:
            print(f"       -> Siguiente nodo: ({self.plan[0].x}, {self.plan[0].y})")
        elif state_name == "ExecutePlan" or state_name == "GoalOrientedBehavior":
            print(f"       ⚠️ ALERTA: Estado de ejecución, pero el PLAN ESTÁ VACÍO. El tanque podría quedarse congelado.")

        return action, shot

    def _CreatePlan(self, perception, map):
        if self.goalMonitor is not None:
            # 1. Seleccionamos la meta mas apropiada segun la estrategia
            currentGoal = self.goalMonitor.SelectGoal(perception, map, self)

            # 2. Nodo inicial: posicion actual del agente en coordenadas mapa
            initial_node = self._CreateInitialNode(perception)
            self.problem.SetInitial(initial_node)

            # 3. Comunicamos la meta al problema para que A* la use
            self.problem.SetGoal(currentGoal)

        # 4. Ejecutamos A* y devolvemos el plan
        plan = self.aStar.GetPlan()
        # Eliminamos el nodo inicial del plan (es donde ya estamos)
        if len(plan) > 1:
            plan.pop(0)
        return plan

    # ------------------------------------------------------------------ #
    # Helpers para crear nodos desde la percepcion                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def CreateNodeByPerception(perception, value, perceptionID_X, perceptionID_Y, ySize):
        xMap, yMap = BCProblem.WorldToMapCoord(
            perception[perceptionID_X],
            perception[perceptionID_Y],
            ySize
        )
        newNode = BCNode(None, BCProblem.GetCost(value), value, xMap, yMap)
        return newNode

    def _CreateInitialNode(self, perception):
        node = GoalOrientedAgent.CreateNodeByPerception(
            perception, AgentConsts.NOTHING,
            AgentConsts.AGENT_X, AgentConsts.AGENT_Y,
            self.MAP_Y_SIZE
        )
        node.SetG(0)
        return node

    def _CreateDefaultGoal(self, perception):
        return GoalOrientedAgent.CreateNodeByPerception(
            perception, AgentConsts.COMMAND_CENTER,
            AgentConsts.COMMAND_CENTER_X, AgentConsts.COMMAND_CENTER_Y,
            self.MAP_Y_SIZE
        )

    def _CreateLifeGoal(self, perception):
        return GoalOrientedAgent.CreateNodeByPerception(
            perception, AgentConsts.LIFE,
            AgentConsts.LIFE_X, AgentConsts.LIFE_Y,
            self.MAP_Y_SIZE
        )

    def _CreatePlayerGoal(self, perception):
        return GoalOrientedAgent.CreateNodeByPerception(
            perception, AgentConsts.PLAYER,
            AgentConsts.PLAYER_X, AgentConsts.PLAYER_Y,
            self.MAP_Y_SIZE
        )

    def _CreateExitGoal(self, perception):
        return GoalOrientedAgent.CreateNodeByPerception(
            perception, AgentConsts.EXIT,
            AgentConsts.EXIT_X, AgentConsts.EXIT_Y,
            self.MAP_Y_SIZE
        )

    # ------------------------------------------------------------------ #
    # Inicializacion diferida (requiere mapa y percepciones reales)        #
    # ------------------------------------------------------------------ #

    def InitAgent(self, perception, map):
        initial_node       = self._CreateInitialNode(perception)
        goal1CommandCenter = self._CreateDefaultGoal(perception)

        # Creamos el problema con las dimensiones del mapa
        self.problem = BCProblem(
            initial_node,
            goal1CommandCenter,
            self.MAP_X_SIZE,
            self.MAP_Y_SIZE
        )
        self.problem.InitMap(map)

        # Inicializamos A*
        self.aStar = AStar(self.problem)

        # Creamos los goals disponibles
        goal2Life   = self._CreateLifeGoal(perception)
        goal3Player = self._CreatePlayerGoal(perception)
        exitGoal    = self._CreateExitGoal(perception)

        # GoalMonitor gestiona que meta perseguir y cuando replanificar
        self.goalMonitor = GoalMonitor(
            self.problem,
            [goal1CommandCenter, goal2Life, goal3Player],
            exitGoal
        )

        # Plan inicial
        self.plan = self._CreatePlan(perception, map)

    # ------------------------------------------------------------------ #
    # Utilidades                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def ShowPlan(plan):
        for n in plan:
            print("X:", n.x, "Y:", n.y, "[", n.value, "]{", n.G(), "} =>")

    def GetPlan(self):
        return self.plan

    def End(self, win):
        super().End(win)
        self.stateMachine.End(win)