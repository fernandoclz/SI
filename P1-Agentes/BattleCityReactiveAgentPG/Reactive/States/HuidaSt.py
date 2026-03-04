from StateMachine.State import State
from States.AgentConsts import AgentConsts

class HuidaSt(State):
    
    def __init__(self, id):
        super().__init__(id)
        self.Reset()