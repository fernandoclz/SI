from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

class DefensaSt(State):
    def __init__(self, name):
        super().__init__(name)
        # Mapeo de dirección de amenaza a dirección de movimiento/giro
        self.dir_map = {
            ac.NEIGHBORHOOD_UP:    (ac.MOVE_UP, ac.NEIGHBORHOOD_DIST_UP),
            ac.NEIGHBORHOOD_DOWN:  (ac.MOVE_DOWN, ac.NEIGHBORHOOD_DIST_DOWN),
            ac.NEIGHBORHOOD_LEFT:  (ac.MOVE_LEFT, ac.NEIGHBORHOOD_DIST_LEFT),
            ac.NEIGHBORHOOD_RIGHT: (ac.MOVE_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT)
        }

    def Update(self, perception, map, agent):
        action = ac.NO_MOVE
        shoot = False

        # 1. BUSCAR AMENAZA MÁS CERCANA
        threat = self._get_nearest_shell(perception)
        
        if threat:
            threat_dir, distance = threat
            face_dir = self.dir_map[threat_dir][0]

            # 2. DEFENSA OFENSIVA: Siempre intentar disparar si podemos
            if perception[ac.CAN_FIRE] == 1.0:
                if perception[ac.TANK_ORIENTATION] == face_dir:
                    return ac.NO_MOVE, True  # ¡Fuego!
                else:
                    return face_dir, False   # Girar para encarar
            else:
                # 3. ESQUIVA: Si no podemos disparar, esquivamos lateralmente
                action = self._get_escape_route(face_dir, perception)
                return action, False

        return action, shoot

    def Transit(self, perception, map):
        # Si no hay proyectiles a la vista en rango de peligro, volvemos
        if not self._get_nearest_shell(perception):
            return "ExecutePlan"
        return self.id

    def _get_nearest_shell(self, perception):
        closest_dist = 5.0
        best_threat = None

        for threat_idx, (move_cmd, dist_idx) in self.dir_map.items():
            if perception[threat_idx] == ac.SHELL:
                dist = perception[dist_idx]
                if dist < closest_dist:
                    closest_dist = dist
                    best_threat = (threat_idx, dist)
        return best_threat

    def _get_escape_route(self, threat_dir, perception):
        # Definir laterales según la dirección de la amenaza
        escapes = [ac.MOVE_LEFT, ac.MOVE_RIGHT] if threat_dir in [ac.MOVE_UP, ac.MOVE_DOWN] else [ac.MOVE_UP, ac.MOVE_DOWN]
        
        for move in escapes:
            if self._can_move(move, perception):
                return move
        return ac.NO_MOVE

    def _can_move(self, action, perception):
        # Mapeo rápido para colisiones
        lookup = {
            ac.MOVE_UP: (ac.NEIGHBORHOOD_UP, ac.NEIGHBORHOOD_DIST_UP),
            ac.MOVE_DOWN: (ac.NEIGHBORHOOD_DOWN, ac.NEIGHBORHOOD_DIST_DOWN),
            ac.MOVE_LEFT: (ac.NEIGHBORHOOD_LEFT, ac.NEIGHBORHOOD_DIST_LEFT),
            ac.MOVE_RIGHT: (ac.NEIGHBORHOOD_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT)
        }
        idx, dist_idx = lookup[action]
        # No entrar si hay obstáculo o muro a menos de 0.8 (margen de seguridad)
        return not (perception[idx] in [ac.UNBREAKABLE, ac.BRICK] and perception[dist_idx] < 0.8)