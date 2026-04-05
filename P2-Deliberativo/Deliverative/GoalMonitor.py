import random
from States.AgentConsts import AgentConsts

class GoalMonitor:

    GOAL_COMMAND_CENTRER = 0
    GOAL_LIFE = 1
    GOAL_PLAYER = 2
    GOAL_EXIT = 3
    def __init__(self, problem, goals, finalGoal):
        self.goals = goals
        self.finalGoal = finalGoal
        self.problem = problem
        self.lastTime = -1
        self.recalculate = False

    def ForceToRecalculate(self):
        self.recalculate = True

    def NeedReplaning(self, perception, map, agent):
        if self.recalculate:
            self.lastTime = perception[AgentConsts.TIME]
            return True
        #Definir la estrategia de cuando queremos recalcular
        #puede ser , por ejemplo cada cierto tiempo o cuanod tenemos poca vida.
        if tiempo_actual - self.lastTime > 20:
            self.lastTime = tiempo_actual
            return True
        if (perception[AgentConsts.HEALTH] <= 1) or (not agent.current_plan):
            return True
        return False

    
    #selecciona la meta mas adecuada al estado actual
    def SelectGoal(self, perception, map, agent):
        if perception[ac.HEALTH] <= 1 and perception[ac.LIFE_X] >= 0:
            for goal in self.goals:
                if goal.name == "LifeGoal": # Suponiendo que le asignaste nombres a tus goals
                    return goal
                    
        if perception[ac.PLAYER_X] >= 0:
            for goal in self.goals:
                if goal.name == "PlayerGoal":
                    return goal

        for goal in self.goals:
            if goal.name == "CommandCenterGoal":
                return goal
                
        return self.goals[0]

    def UpdateGoals(self,goal, goalId):
        self.goals[goalId] = goal
