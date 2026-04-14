from States.AgentConsts import AgentConsts


class GoalMonitor:

    GOAL_COMMAND_CENTER = 0
    GOAL_LIFE = 1
    GOAL_PLAYER = 2

    PLAYER_CHASE_DISTANCE = 5

    def __init__(self, problem, goals, finalGoal):
        self.goals = goals
        self.finalGoal = finalGoal
        self.problem = problem
        self.lastTime = -1
        self.recalculate = False

    def ForceToRecalculate(self):
        self.recalculate = True

    def NeedReplaning(self, perception, map, agent):
        tiempo_actual = perception[AgentConsts.TIME]

        if self.recalculate:
            self.recalculate = False
            self.lastTime = tiempo_actual
            return True

        if tiempo_actual - self.lastTime > 20:
            self.lastTime = tiempo_actual
            return True

        if perception[AgentConsts.HEALTH] <= 1:
            self.lastTime = tiempo_actual
            return True

        return False

    def SelectGoal(self, perception, map, agent):
        from MyProblem.BCProblem import BCProblem

        # 1. Vida baja y power-up disponible
        if (perception[AgentConsts.HEALTH] <= 1 and
                perception[AgentConsts.LIFE_X] >= 0 and
                self.goals[self.GOAL_LIFE] is not None):
            return self.goals[self.GOAL_LIFE]

        # 2. Jugador visible y cerca
        if (self.goals[self.GOAL_PLAYER] is not None and
                perception[AgentConsts.PLAYER_X] >= 0):
            ax, ay = BCProblem.WorldToMapCoord(
                perception[AgentConsts.AGENT_X],
                perception[AgentConsts.AGENT_Y],
                self.problem.ySize
            )
            px, py = BCProblem.WorldToMapCoord(
                perception[AgentConsts.PLAYER_X],
                perception[AgentConsts.PLAYER_Y],
                self.problem.ySize
            )
            dist = abs(ax - px) + abs(ay - py)
            if dist <= self.PLAYER_CHASE_DISTANCE:
                return self.goals[self.GOAL_PLAYER]

        # 3. CommandCenter si sigue en pie (valor 3 en el mapa)
        if self.goals[self.GOAL_COMMAND_CENTER] is not None:
            g = self.goals[self.GOAL_COMMAND_CENTER]
            if self.problem.map[g.x][g.y] == AgentConsts.COMMAND_CENTER:
                return g

        # 4. CC destruido: perseguir al jugador aunque esté lejos
        if (self.goals[self.GOAL_PLAYER] is not None and
                perception[AgentConsts.PLAYER_X] >= 0):
            return self.goals[self.GOAL_PLAYER]

        # 5. Sin jugador visible: ir a por la vida si existe
        if (self.goals[self.GOAL_LIFE] is not None and
                perception[AgentConsts.LIFE_X] >= 0):
            return self.goals[self.GOAL_LIFE]

        # 6. Sin ningún objetivo: ir a la salida
        return self.finalGoal

    def UpdateGoals(self, goal, goalId):
        self.goals[goalId] = goal