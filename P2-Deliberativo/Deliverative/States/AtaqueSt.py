from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

class AtaqueSt(State):
    def __init__(self, name):
        super().__init__(name)
        # Reducimos el margen. Si el paso del agente es de ~1.2, 
        # un margen de 1.5 garantiza el rebote infinito.
        self.dist_min_disparo = 0.8 

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

        # 1. Tolerancia para evitar que intente corregir desviaciones milimétricas
        TOLERANCIA = 0.5
        aligned_x = abs(dy) <= TOLERANCIA
        aligned_y = abs(dx) <= TOLERANCIA

        # 2. ¡DISPARAR PRIMERO! 
        # Si ya estamos alineados y miramos al objetivo, priorizamos el disparo.
        # Esto evita que le demos la espalda para retroceder si ya tenemos el tiro limpio.
        if aligned_x:
            face_dir = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
            if orientation == face_dir:
                return ac.NO_MOVE, can_fire
                
        elif aligned_y:
            face_dir = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN
            if orientation == face_dir:
                return ac.NO_MOVE, can_fire

        # 3. Retroceso (Solo si de verdad estamos muy, muy pegados y no estábamos apuntando bien)
        if dist < self.dist_min_disparo:
            if abs(dx) >= abs(dy):
                retroceso = ac.MOVE_LEFT if dx > 0 else ac.MOVE_RIGHT
            else:
                retroceso = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN
            return retroceso, False

        # 4. Orientar y movernos hacia el objetivo si aún no estamos alineados
        if abs(dx) >= abs(dy):
            face_dir = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
        else:
            face_dir = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN

        return face_dir, can_fire

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