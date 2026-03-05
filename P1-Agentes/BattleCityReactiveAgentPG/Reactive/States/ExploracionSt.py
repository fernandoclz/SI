from StateMachine.State import State
from States.AgentConsts import AgentConsts

class ExploracionSt(State):
    
    def __init__(self, id):
        super().__init__(id)
        # NUEVO: Pequeña memoria para no quedarnos atrapados en bucles de izquierda-derecha
        self.last_evade = AgentConsts.MOVE_RIGHT

    def Update(self, perception, map, agent):
        action = AgentConsts.NOTHING
        shot = False
        can_fire = (perception[AgentConsts.CAN_FIRE] == 1.0)

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
            target_x = perception[AgentConsts.LIFE_X]
            target_y = perception[AgentConsts.LIFE_Y]

        if target_x < 0 or target_y < 0:
            return AgentConsts.NOTHING, False

        dx = target_x - agent_x
        dy = target_y - agent_y

        # NAVEGACIÓN CON MEMORIA ANTI-BUCLES
        if abs(dx) > abs(dy):
            if dx > 0:
                action = AgentConsts.MOVE_RIGHT
                if perception[AgentConsts.NEIGHBORHOOD_RIGHT] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:
                    if dy > 0:
                        action = AgentConsts.MOVE_DOWN
                        self.last_evade = action
                    elif dy < 0:
                        action = AgentConsts.MOVE_UP
                        self.last_evade = action
                    else:
                        action = self.last_evade # Usamos la memoria
                elif perception[AgentConsts.NEIGHBORHOOD_RIGHT] == AgentConsts.BRICK and can_fire:
                    shot = True
            else:
                action = AgentConsts.MOVE_LEFT
                if perception[AgentConsts.NEIGHBORHOOD_LEFT] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:  
                    if dy > 0:
                        action = AgentConsts.MOVE_DOWN
                        self.last_evade = action
                    elif dy < 0:
                        action = AgentConsts.MOVE_UP
                        self.last_evade = action
                    else:
                        action = self.last_evade
                elif perception[AgentConsts.NEIGHBORHOOD_LEFT] == AgentConsts.BRICK and can_fire:
                    shot = True
        else:
            if dy > 0:
                action = AgentConsts.MOVE_DOWN
                if perception[AgentConsts.NEIGHBORHOOD_DOWN] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:  
                    if dx > 0:
                        action = AgentConsts.MOVE_RIGHT
                        self.last_evade = action
                    elif dx < 0:
                        action = AgentConsts.MOVE_LEFT
                        self.last_evade = action
                    else:
                        action = self.last_evade
                elif perception[AgentConsts.NEIGHBORHOOD_DOWN] == AgentConsts.BRICK and can_fire:
                    shot = True
            else:
                action = AgentConsts.MOVE_UP
                if perception[AgentConsts.NEIGHBORHOOD_UP] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:  
                    if dx > 0:
                        action = AgentConsts.MOVE_RIGHT
                        self.last_evade = action
                    elif dx < 0:
                        action = AgentConsts.MOVE_LEFT
                        self.last_evade = action
                    else:
                        action = self.last_evade
                elif perception[AgentConsts.NEIGHBORHOOD_UP] == AgentConsts.BRICK and can_fire:
                    shot = True

        # FILTRO DE SEGURIDAD EXTREMA
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

        if player_x >= 0 and player_y >= 0:
            if abs(agent_x - player_x) < 1.0 or abs(agent_y - player_y) < 1.0:
                return "Ataque"
        
        elif cc_x >= 0 and cc_y >= 0:
            if abs(agent_x - cc_x) < 1.0 or abs(agent_y - cc_y) < 1.0:
                return "Ataque"

        return self.id

    def Reset(self):
        pass