from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac
from GoalMonitor import GoalMonitor


class HuidaSt(State):
    def __init__(self, name):
        super().__init__(name)
        self.replanned = False

    def Start(self, agent):
        print("Estado Huida iniciado")
        self.replanned = False

    def Update(self, perception, map, agent):
        # Sin power-up: no hay adonde huir
        if perception[ac.LIFE_X] < 0:
            return ac.NO_MOVE, False

        # Forzamos replanificación hacia life solo una vez al entrar al estado
        if not self.replanned:
            lifeGoal = self._CreateLifeGoal(perception, agent)
            agent.goalMonitor.UpdateGoals(lifeGoal, GoalMonitor.GOAL_LIFE)
            agent.goalMonitor.ForceToRecalculate()
            self.replanned = True

        return ac.NO_MOVE, False

    def Transit(self, perception, map):
        if self._bala_entrante(perception):
            return "Defensa"

        # Solo volvemos a ExecutePlan cuando ya replanificamos
        if self.replanned:
            self.replanned = False
            return "ExecutePlan"

        return self.id

    def _CreateLifeGoal(self, perception, agent):
        from MyProblem.BCProblem import BCProblem
        from MyProblem.BCNode import BCNode
        xMap, yMap = BCProblem.WorldToMapCoord(
            perception[ac.LIFE_X],
            perception[ac.LIFE_Y],
            agent.problem.ySize
        )
        return BCNode(None, BCProblem.GetCost(ac.NOTHING), ac.LIFE, xMap, yMap)

    def _bala_entrante(self, perception):
        dirs = [
            (ac.NEIGHBORHOOD_UP,    ac.NEIGHBORHOOD_DIST_UP),
            (ac.NEIGHBORHOOD_DOWN,  ac.NEIGHBORHOOD_DIST_DOWN),
            (ac.NEIGHBORHOOD_LEFT,  ac.NEIGHBORHOOD_DIST_LEFT),
            (ac.NEIGHBORHOOD_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT),
        ]
        for dir_idx, dist_idx in dirs:
            if perception[dir_idx] == ac.SHELL and perception[dist_idx] < 3:
                return True
        return False