from StateMachine.State import State
from States.AgentConsts import AgentConsts

class Attack(State):

    def __init__(self, id):
        super().__init__(id)
        self.directionToLook = -1

    def Update(self, perception, map, agent):
        self.directionToLook=agent.directionToLook
        return 0, True

    def Transit(self,perception, map):
        
        target = perception[self.directionToLook]
        #targetDist = perception[self.directionToLook+4]
        if target != AgentConsts.PLAYER or target != AgentConsts.COMMAND_CENTER:
            return "ExecutePlan"
        return self.id
    