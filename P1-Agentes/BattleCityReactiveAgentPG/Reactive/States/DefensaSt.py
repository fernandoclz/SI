from StateMachine.State import State
from States.AgentConsts import AgentConsts

class DefensaSt(State):
    
    def __init__(self, id):
        super().__init__(id)
        # Eliminamos el temporizador, ya no nos hace falta

    def Update(self, perception, map, agent):
        action = AgentConsts.NOTHING
        shot = False
        can_fire = (perception[AgentConsts.CAN_FIRE] == 1.0)

        # 1. EVALUAR AMENAZAS INMEDIATAS (Jugador o Balas)
        neighbors = {
            AgentConsts.NEIGHBORHOOD_UP: AgentConsts.MOVE_UP,
            AgentConsts.NEIGHBORHOOD_DOWN: AgentConsts.MOVE_DOWN,
            AgentConsts.NEIGHBORHOOD_RIGHT: AgentConsts.MOVE_RIGHT,
            AgentConsts.NEIGHBORHOOD_LEFT: AgentConsts.MOVE_LEFT
        }
        
        # Movimientos opuestos para esquivar
        evade_moves = {
            AgentConsts.NEIGHBORHOOD_UP: AgentConsts.MOVE_DOWN,
            AgentConsts.NEIGHBORHOOD_DOWN: AgentConsts.MOVE_UP,
            AgentConsts.NEIGHBORHOOD_LEFT: AgentConsts.MOVE_RIGHT,
            AgentConsts.NEIGHBORHOOD_RIGHT: AgentConsts.MOVE_LEFT
        }

        for n_index, move_action in neighbors.items():
            # Si hay un jugador o una bala adyacente
            if perception[n_index] == AgentConsts.PLAYER or perception[n_index] == AgentConsts.SHELL:
                if can_fire:
                    shot = True
                    # IMPORTANTE: Nos movemos hacia la amenaza para "encararla" y poder dispararle
                    action = move_action 
                else:
                    # Esquivamos en dirección opuesta
                    action = evade_moves[n_index]
                
                return action, shot

        # 2. NO HAY AMENAZA: IR AL COMMAND CENTER A DEFENDER
        agent_x = perception[AgentConsts.AGENT_X]
        agent_y = perception[AgentConsts.AGENT_Y]
        cc_x = perception[AgentConsts.COMMAND_CENTER_X]
        cc_y = perception[AgentConsts.COMMAND_CENTER_Y]

        dx = cc_x - agent_x
        dy = cc_y - agent_y

        if dx == 0 and dy == 0:
            action = AgentConsts.NOTHING
        elif abs(dx) > abs(dy):
            action = AgentConsts.MOVE_RIGHT if dx > 0 else AgentConsts.MOVE_LEFT
        else:
            action = AgentConsts.MOVE_DOWN if dy > 0 else AgentConsts.MOVE_UP

        # Nota: Si te quedas atascado contra un muro con esta lógica, 
        # tendrás que añadir comprobaciones de "si no hay muro delante" en el futuro.

        return action, shot

    def Transit(self, perception, map):
        # CONDICIÓN DE SALIDA:
        # Si estamos defendiendo la base pero vemos al jugador "a tiro" a lo lejos
        # (coincide en X o en Y), pasamos al estado ATAQUE.
        
        agent_x = perception[AgentConsts.AGENT_X]
        agent_y = perception[AgentConsts.AGENT_Y]
        player_x = perception[AgentConsts.PLAYER_X]
        player_y = perception[AgentConsts.PLAYER_Y]
        
        # Si el jugador está vivo (coordenadas positivas) y alineado
        if player_x >= 0 and player_y >= 0:
            if abs(agent_x - player_x) < 1.0 or abs(agent_y - player_y) < 1.0:
                return "ATAQUE" # Asumiendo que has llamado así a tu estado de ataque
                
        return self.id

    def Reset(self):
        pass # Ya no necesitamos resetear nada