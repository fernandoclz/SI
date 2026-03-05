from StateMachine.State import State
from States.AgentConsts import AgentConsts

class AtaqueSt(State):
    
    def __init__(self, id):
        super().__init__(id)

    def Update(self, perception, map, agent):
        action = AgentConsts.NOTHING
        shot = (perception[AgentConsts.CAN_FIRE] == 1.0)

        agent_x = perception[AgentConsts.AGENT_X]
        agent_y = perception[AgentConsts.AGENT_Y]
        player_x = perception[AgentConsts.PLAYER_X]
        player_y = perception[AgentConsts.PLAYER_Y]
        cc_x = perception[AgentConsts.COMMAND_CENTER_X]
        cc_y = perception[AgentConsts.COMMAND_CENTER_Y]

        target_x, target_y = -1, -1
        if player_x >= 0:
            target_x, target_y = player_x, player_y
        elif cc_x >= 0:
            target_x, target_y = cc_x, cc_y

        if abs(agent_x - target_x) < 1.0:
            if target_y > agent_y:
                action = AgentConsts.MOVE_DOWN
            else:
                action = AgentConsts.MOVE_UP
                
        elif abs(agent_y - target_y) < 1.0:
            if target_x > agent_x:
                action = AgentConsts.MOVE_RIGHT
            else:
                action = AgentConsts.MOVE_LEFT

        if action == AgentConsts.MOVE_UP and perception[AgentConsts.NEIGHBORHOOD_UP] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:
            action = AgentConsts.NOTHING
        elif action == AgentConsts.MOVE_DOWN and perception[AgentConsts.NEIGHBORHOOD_DOWN] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:
            action = AgentConsts.NOTHING
        elif action == AgentConsts.MOVE_RIGHT and perception[AgentConsts.NEIGHBORHOOD_RIGHT] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:
            action = AgentConsts.NOTHING
        elif action == AgentConsts.MOVE_LEFT and perception[AgentConsts.NEIGHBORHOOD_LEFT] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:
            action = AgentConsts.NOTHING

        return action, shot

    def Transit(self, perception, map):
        neighbors = [
            perception[AgentConsts.NEIGHBORHOOD_UP],
            perception[AgentConsts.NEIGHBORHOOD_DOWN],
            perception[AgentConsts.NEIGHBORHOOD_LEFT],
            perception[AgentConsts.NEIGHBORHOOD_RIGHT]
        ]
        if AgentConsts.SHELL in neighbors:
            return "Defensa"

        agent_x = perception[AgentConsts.AGENT_X]
        agent_y = perception[AgentConsts.AGENT_Y]
        player_x = perception[AgentConsts.PLAYER_X]
        player_y = perception[AgentConsts.PLAYER_Y]
        cc_x = perception[AgentConsts.COMMAND_CENTER_X]
        cc_y = perception[AgentConsts.COMMAND_CENTER_Y]

        target_x, target_y = -1, -1
        if player_x >= 0:
            target_x, target_y = player_x, player_y
        elif cc_x >= 0:
            target_x, target_y = cc_x, cc_y
        else:
            return "Exploracion"

        # 1. Si ya no está alineado
        if abs(agent_x - target_x) >= 1.0 and abs(agent_y - target_y) >= 1.0:
            return "Exploracion"

        # 2. NUEVO: Si está alineado, pero un muro le tapa la cara, forzamos salida para rodearlo
        if abs(agent_x - target_x) < 1.0:
            if target_y < agent_y and perception[AgentConsts.NEIGHBORHOOD_UP] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:
                return "Exploracion"
            elif target_y > agent_y and perception[AgentConsts.NEIGHBORHOOD_DOWN] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:
                return "Exploracion"
        elif abs(agent_y - target_y) < 1.0:
            if target_x < agent_x and perception[AgentConsts.NEIGHBORHOOD_LEFT] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:
                return "Exploracion"
            elif target_x > agent_x and perception[AgentConsts.NEIGHBORHOOD_RIGHT] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:
                return "Exploracion"

        return self.id

    def Reset(self):
        pass