from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

HEALTH_MAX = 3

class ExploracionSt(State):
    def __init__(self, name):
        super().__init__(name)
        self.last_pos = (-999, -999)
        self.stuck_ticks = 0
        # Mapeos estáticos
        self.mapping = {ac.MOVE_UP: ac.NEIGHBORHOOD_UP, ac.MOVE_DOWN: ac.NEIGHBORHOOD_DOWN,
                        ac.MOVE_LEFT: ac.NEIGHBORHOOD_LEFT, ac.MOVE_RIGHT: ac.NEIGHBORHOOD_RIGHT}
        self.dist_map = {ac.MOVE_UP: ac.NEIGHBORHOOD_DIST_UP, ac.MOVE_DOWN: ac.NEIGHBORHOOD_DIST_DOWN,
                         ac.MOVE_LEFT: ac.NEIGHBORHOOD_DIST_LEFT, ac.MOVE_RIGHT: ac.NEIGHBORHOOD_DIST_RIGHT}

    def Update(self, perception, map, agent):
        # 1. SELECCIÓN DE OBJETIVO (Prioridad: Vida -> Base -> Salida)
        tx, ty = -1, -1
        if perception[ac.LIFE_X] >= 0 and perception[ac.HEALTH] < HEALTH_MAX:
            tx, ty = perception[ac.LIFE_X], perception[ac.LIFE_Y]
        elif perception[ac.COMMAND_CENTER_X] >= 0:
            tx, ty = perception[ac.COMMAND_CENTER_X], perception[ac.COMMAND_CENTER_Y]
        else:
            tx, ty = perception[ac.EXIT_X], perception[ac.EXIT_Y]

        if tx < 0: return ac.NO_MOVE, False

        ax, ay = perception[ac.AGENT_X], perception[ac.AGENT_Y]
        dx, dy = tx - ax, ty - ay
        dist_total = abs(dx) + abs(dy)
        if dist_total < 0.5: return ac.NO_MOVE, False

        # 2. DETECCIÓN DE ATASCOS (Solo para muros irrompibles)
        if abs(ax - self.last_pos[0]) + abs(ay - self.last_pos[1]) < 0.05:
            self.stuck_ticks += 1
        else:
            self.stuck_ticks = 0
        self.last_pos = (ax, ay)

        # 3. LÓGICA DE NAVEGACIÓN SIMPLIFICADA
        # Decidimos dirección ideal (la que más reduce distancia)
        pref_x = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
        pref_y = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN
        order = [pref_x, pref_y] if abs(dx) > abs(dy) else [pref_y, pref_x]
        
        # Añadimos las opuestas como último recurso para salir de callejones
        order += [self._opp(order[1]), self._opp(order[0])]

        chosen_move = ac.NO_MOVE
        for move in order:
            if self._is_passable(move, perception):
                chosen_move = move
                break
        
        # 4. GESTIÓN DE LADRILLOS Y DISPARO
        # Si el movimiento elegido nos lleva contra un ladrillo, disparamos
        if chosen_move != ac.NO_MOVE:
            obj = perception[self.mapping[chosen_move]]
            dist = perception[self.dist_map[chosen_move]]
            
            if obj in [ac.BRICK, ac.SEMI_BREKABLE] and dist < 1.2:
                if perception[ac.ORIENTATION] == chosen_move:
                    # Si ya estamos mirando, nos paramos y disparamos
                    return (ac.NO_MOVE if dist < 0.6 else chosen_move), True
                else:
                    # Girar hacia el ladrillo
                    return chosen_move, False

        # Si estamos atascados por un muro duro (no ladrillo), forzamos cambio
        if self.stuck_ticks > 4:
            # Movimiento perpendicular simple para deslizar por el muro
            alt = ac.MOVE_UP if chosen_move in [ac.MOVE_LEFT, ac.MOVE_RIGHT] else ac.MOVE_RIGHT
            return alt, False

        return chosen_move, False

    # --- UTILIDADES ---
    def _is_passable(self, move, perception):
        obj = perception[self.mapping[move]]
        dist = perception[self.dist_map[move]]
        # Transitable es todo lo que no sea muro duro o base aliada a menos de 0.6
        return not (obj in [ac.UNBREAKABLE, ac.COMMAND_CENTER] and dist < 0.6)

    def _opp(self, move):
        return {ac.MOVE_UP: ac.MOVE_DOWN, ac.MOVE_DOWN: ac.MOVE_UP, 
                ac.MOVE_LEFT: ac.MOVE_RIGHT, ac.MOVE_RIGHT: ac.MOVE_LEFT}.get(move, ac.NO_MOVE)

    def Transit(self, perception, map):
        if self._bala_entrante(perception): return "Defensa"
        if perception[ac.HEALTH] <= 1 and perception[ac.LIFE_X] >= 0: return "Huida"
        if perception[ac.PLAYER_X] >= 0: return "Ataque"
        return self.id

    def _bala_entrante(self, perception):
        for d in [ac.NEIGHBORHOOD_UP, ac.NEIGHBORHOOD_DOWN, ac.NEIGHBORHOOD_LEFT, ac.NEIGHBORHOOD_RIGHT]:
            idx_dist = self.dist_map[{v:k for k,v in self.mapping.items()}[d]] # Inverso para buscar dist
            if perception[d] == ac.SHELL and perception[idx_dist] < 5: return True
        return False