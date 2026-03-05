from StateMachine.State import State
from States.AgentConsts import AgentConsts

class HuidaSt(State):
    
    def __init__(self, id):
        super().__init__(id)

    def Update(self, perception, map, agent):
        action = AgentConsts.NOTHING
        shot = False
        can_fire = (perception[AgentConsts.CAN_FIRE] == 1.0)

        # 1. Obtenemos nuestras coordenadas y las de la vida extra
        agent_x = perception[AgentConsts.AGENT_X]
        agent_y = perception[AgentConsts.AGENT_Y]
        target_x = perception[AgentConsts.LIFE_X]
        target_y = perception[AgentConsts.LIFE_Y]

        # Si no hay vida extra, no hacemos nada
        if target_x < 0 or target_y < 0:
            return AgentConsts.NOTHING, False

        # 2. Navegación 
        dx = target_x - agent_x
        dy = target_y - agent_y

        if abs(dx) > abs(dy):
            if dx > 0:
                action = AgentConsts.MOVE_RIGHT
                if perception[AgentConsts.NEIGHBORHOOD_RIGHT] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:  
                    action = AgentConsts.MOVE_DOWN if dy > 0 else AgentConsts.MOVE_UP
                elif perception[AgentConsts.NEIGHBORHOOD_RIGHT] == AgentConsts.BRICK and can_fire:
                    shot = True
            else:
                action = AgentConsts.MOVE_LEFT
                if perception[AgentConsts.NEIGHBORHOOD_LEFT] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:  
                    action = AgentConsts.MOVE_DOWN if dy > 0 else AgentConsts.MOVE_UP
                elif perception[AgentConsts.NEIGHBORHOOD_LEFT] == AgentConsts.BRICK and can_fire:
                    shot = True
        else:
            if dy > 0:
                action = AgentConsts.MOVE_DOWN
                if perception[AgentConsts.NEIGHBORHOOD_DOWN] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:  
                    action = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
                elif perception[AgentConsts.NEIGHBORHOOD_DOWN] == AgentConsts.BRICK and can_fire:
                    shot = True
            else:
                action = AgentConsts.MOVE_UP
                if perception[AgentConsts.NEIGHBORHOOD_UP] in [AgentConsts.UNBREAKABLE, AgentConsts.SEMI_UNBREKABLE]:  
                    action = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
                elif perception[AgentConsts.NEIGHBORHOOD_UP] == AgentConsts.BRICK and can_fire:
                    shot = True

        # 3. FILTRO DE SEGURIDAD CONTRA MUROS
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

        return self.id

    def Reset(self):
        pass