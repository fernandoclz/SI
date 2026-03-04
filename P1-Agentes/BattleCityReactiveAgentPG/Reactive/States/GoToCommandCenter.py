from StateMachine.State import State
from States.AgentConsts import AgentConsts

class GoToCommandCenter(State):
    
    def __init__(self, id):
        super().__init__(id)

    def Update(self, perception, map, agent):
        action = AgentConsts.NOTHING
        shot = False
        can_fire = (perception[AgentConsts.CAN_FIRE] == 1.0)

        # 1. COORDENADAS
        agent_x = perception[AgentConsts.AGENT_X]
        agent_y = perception[AgentConsts.AGENT_Y]
        player_x = perception[AgentConsts.PLAYER_X]
        player_y = perception[AgentConsts.PLAYER_Y]
        cc_x = perception[AgentConsts.COMMAND_CENTER_X]
        cc_y = perception[AgentConsts.COMMAND_CENTER_Y]

        # 2. SELECCIÓN DE OBJETIVO (Prioridad: Player > Base > Salida)
        target_x, target_y = -1, -1
        if player_x >= 0:
            target_x, target_y = player_x, player_y
        elif cc_x >= 0:
            target_x, target_y = cc_x, cc_y
        else:
            # Si ambos están destruidos, ir a la estrella de salida
            target_x = perception[AgentConsts.EXIT_X]
            target_y = perception[AgentConsts.EXIT_Y]

        # 3. NAVEGACIÓN Y EVASIÓN DE OBSTÁCULOS
        dx = target_x - agent_x
        dy = target_y - agent_y

        # Intentamos movernos en el eje donde haya más distancia
        if abs(dx) > abs(dy):
            if dx > 0:
                action = AgentConsts.MOVE_RIGHT
                # Si hay obstáculo, intentar rodear por el eje Y
                if perception[AgentConsts.NEIGHBORHOOD_RIGHT] in [AgentConsts.METAL, AgentConsts.WATER]:
                    action = AgentConsts.MOVE_DOWN if dy > 0 else AgentConsts.MOVE_UP
                # Si es ladrillo, ¡disparamos para romperlo!
                elif perception[AgentConsts.NEIGHBORHOOD_RIGHT] == AgentConsts.BRICK and can_fire:
                    shot = True
            else:
                action = AgentConsts.MOVE_LEFT
                if perception[AgentConsts.NEIGHBORHOOD_LEFT] in [AgentConsts.METAL, AgentConsts.WATER]:
                    action = AgentConsts.MOVE_DOWN if dy > 0 else AgentConsts.MOVE_UP
                elif perception[AgentConsts.NEIGHBORHOOD_LEFT] == AgentConsts.BRICK and can_fire:
                    shot = True
        else:
            if dy > 0:
                action = AgentConsts.MOVE_DOWN
                if perception[AgentConsts.NEIGHBORHOOD_DOWN] in [AgentConsts.METAL, AgentConsts.WATER]:
                    action = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
                elif perception[AgentConsts.NEIGHBORHOOD_DOWN] == AgentConsts.BRICK and can_fire:
                    shot = True
            else:
                action = AgentConsts.MOVE_UP
                if perception[AgentConsts.NEIGHBORHOOD_UP] in [AgentConsts.METAL, AgentConsts.WATER]:
                    action = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
                elif perception[AgentConsts.NEIGHBORHOOD_UP] == AgentConsts.BRICK and can_fire:
                    shot = True

        return action, shot

    def Transit(self, perception, map):
        # TRANSICIÓN 1: ¡Peligro! Viene una bala
        neighbors = [
            perception[AgentConsts.NEIGHBORHOOD_UP],
            perception[AgentConsts.NEIGHBORHOOD_DOWN],
            perception[AgentConsts.NEIGHBORHOOD_LEFT],
            perception[AgentConsts.NEIGHBORHOOD_RIGHT]
        ]
        if AgentConsts.SHELL in neighbors:
            return "DEFENSA"

        # TRANSICIÓN 2: ¡Objetivo a tiro! (Alineado en X o en Y)
        agent_x = perception[AgentConsts.AGENT_X]
        agent_y = perception[AgentConsts.AGENT_Y]
        player_x = perception[AgentConsts.PLAYER_X]
        player_y = perception[AgentConsts.PLAYER_Y]
        cc_x = perception[AgentConsts.COMMAND_CENTER_X]
        cc_y = perception[AgentConsts.COMMAND_CENTER_Y]

        # Comprobar si el jugador está vivo y alineado
        if player_x >= 0 and player_y >= 0:
            if abs(agent_x - player_x) < 1.0 or abs(agent_y - player_y) < 1.0:
                return "ATAQUE"
        
        # Comprobar si la base está viva y alineada (si el jugador ya murió)
        elif cc_x >= 0 and cc_y >= 0:
            if abs(agent_x - cc_x) < 1.0 or abs(agent_y - cc_y) < 1.0:
                return "ATAQUE"

        # Si no pasa nada de lo anterior, seguimos explorando
        return self.id

    def Reset(self):
        pass