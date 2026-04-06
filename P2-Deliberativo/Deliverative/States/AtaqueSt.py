from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

# Distancia mínima para poder disparar sin solaparse
DIST_MIN_DISPARO = 1.5

class AtaqueSt(State):
    def __init__(self, name):
        super().__init__(name)

    def Start(self, agent):
        print("Estado Ataque iniciado")

    def Update(self, perception, map, agent):
        orientation = perception[ac.TANK_ORIENTATION]
        can_fire = perception[ac.CAN_FIRE] == 1

        # Objetivo: jugador o command center
        tx = perception[ac.PLAYER_X] if perception[ac.PLAYER_X] >= 0 else perception[ac.COMMAND_CENTER_X]
        ty = perception[ac.PLAYER_Y] if perception[ac.PLAYER_Y] >= 0 else perception[ac.COMMAND_CENTER_Y]

        if tx < 0 or ty < 0:
            return ac.NO_MOVE, False

        ax, ay = perception[ac.AGENT_X], perception[ac.AGENT_Y]
        dx, dy = tx - ax, ty - ay
        dist = abs(dx) + abs(dy)

        # Si estamos solapados con el objetivo no podemos disparar: retrocedemos
        if dist < DIST_MIN_DISPARO:
            # Nos alejamos en dirección contraria al objetivo
            if abs(dx) >= abs(dy):
                retroceso = ac.MOVE_LEFT if dx > 0 else ac.MOVE_RIGHT
            else:
                retroceso = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN
            return retroceso, False

        # Orientamos hacia el objetivo por el eje de mayor diferencia
        if abs(dx) >= abs(dy):
            face_dir = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
        else:
            face_dir = ac.MOVE_DOWN if dy > 0 else ac.MOVE_UP

        # Si no estamos bien orientados, giramos
        if orientation != face_dir:
            return face_dir, False

        # Orientados y a buena distancia: disparamos
        return ac.NO_MOVE, can_fire

    def Transit(self, perception, map):
        if self._bala_entrante(perception):
            return "Defensa"

        if perception[ac.HEALTH] <= 1 and perception[ac.LIFE_X] >= 0:
            return "Huida"

        # Sin objetivo visible: volver a planificar
        if perception[ac.PLAYER_X] < 0 and perception[ac.COMMAND_CENTER_X] < 0:
            return "ExecutePlan"

        return self.id

    def _bala_entrante(self, perception):
        dirs = [
            (ac.NEIGHBORHOOD_UP,    ac.NEIGHBORHOOD_DIST_UP),
            (ac.NEIGHBORHOOD_DOWN,  ac.NEIGHBORHOOD_DIST_DOWN),
            (ac.NEIGHBORHOOD_LEFT,  ac.NEIGHBORHOOD_DIST_LEFT),
            (ac.NEIGHBORHOOD_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT),
        ]
        for dir_idx, dist_idx in dirs:
            if perception[dir_idx] == ac.SHELL and perception[dist_idx] < 5:
                return True
        return False