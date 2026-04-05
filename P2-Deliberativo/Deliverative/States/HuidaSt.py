from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

class HuidaSt(State):
    def __init__(self, name):
        super().__init__(name)
        self.last_pos = (-999, -999)
        self.stuck_ticks = 0
        
        # Añadimos los mapeos para poder "ver" igual que en Exploracion
        self.mapping = {ac.MOVE_UP: ac.NEIGHBORHOOD_UP, ac.MOVE_DOWN: ac.NEIGHBORHOOD_DOWN,
                        ac.MOVE_LEFT: ac.NEIGHBORHOOD_LEFT, ac.MOVE_RIGHT: ac.NEIGHBORHOOD_RIGHT}
        self.dist_map = {ac.MOVE_UP: ac.NEIGHBORHOOD_DIST_UP, ac.MOVE_DOWN: ac.NEIGHBORHOOD_DIST_DOWN,
                         ac.MOVE_LEFT: ac.NEIGHBORHOOD_DIST_LEFT, ac.MOVE_RIGHT: ac.NEIGHBORHOOD_DIST_RIGHT}

    def Start(self, agent):
        print("Estado Huida iniciado")

    def Update(self, perception, map, agent):
        # 1. OBJETIVO: Solo nos interesa la vida
        if perception[ac.LIFE_X] < 0:
            return ac.NO_MOVE, False

        tx, ty = perception[ac.LIFE_X], perception[ac.LIFE_Y]
        ax, ay = perception[ac.AGENT_X], perception[ac.AGENT_Y]
        dx, dy = tx - ax, ty - ay

        # 2. DETECCIÓN DE ATASCOS
        if abs(ax - self.last_pos[0]) + abs(ay - self.last_pos[1]) < 0.05:
            self.stuck_ticks += 1
        else:
            self.stuck_ticks = 0
        self.last_pos = (ax, ay)

        # 3. LÓGICA DE NAVEGACIÓN (Estilo Exploracion)
        pref_x = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
        pref_y = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN
        order = [pref_x, pref_y] if abs(dx) > abs(dy) else [pref_y, pref_x]
        
        # Direcciones opuestas como plan de respaldo
        order += [self._opp(order[1]), self._opp(order[0])]

        chosen_move = ac.NO_MOVE
        for move in order:
            if self._is_passable(move, perception):
                chosen_move = move
                break

        # 4. DESATASCO FORZADO (Prioridad Máxima: ¡Antes de disparar!)
        if self.stuck_ticks > 4:
            # Si nos atascamos yendo en horizontal, forzamos un paso vertical (y viceversa)
            if chosen_move in [ac.MOVE_LEFT, ac.MOVE_RIGHT]:
                alt = ac.MOVE_UP if self._is_passable(ac.MOVE_UP, perception) else ac.MOVE_DOWN
            else:
                alt = ac.MOVE_RIGHT if self._is_passable(ac.MOVE_RIGHT, perception) else ac.MOVE_LEFT
            
            # Reseteamos los ticks para darle tiempo a colocarse bien
            self.stuck_ticks = 0 
            return alt, False

        # 5. GESTIÓN DE LADRILLOS Y DISPARO
        shoot = False
        if chosen_move != ac.NO_MOVE:
            obj = perception[self.mapping[chosen_move]]
            dist = perception[self.dist_map[chosen_move]]
            
            # Si el camino directo a la vida tiene un ladrillo, lo volamos
            if obj in [ac.BRICK, ac.SEMI_BREKABLE] and dist < 1.2:
                if perception[ac.ORIENTATION] == chosen_move:
                    shoot = True
                    if dist < 0.6: 
                        chosen_move = ac.NO_MOVE # Parar para no chocar mientras disparamos
                else:
                    shoot = False # Primero girar

        # 5. DESATASCO FORZADO
        if self.stuck_ticks > 4:
            alt = ac.MOVE_UP if chosen_move in [ac.MOVE_LEFT, ac.MOVE_RIGHT] else ac.MOVE_RIGHT
            return alt, False

        return chosen_move, shoot

    # ------------------------------------------------------------------ #
    # TRANSICIONES Y UTILIDADES                                            #
    # ------------------------------------------------------------------ #
    def Transit(self, perception, map):
        if perception[ac.LIFE_X] < 0 or perception[ac.HEALTH] > 1:
            return "Exploracion"
        if self._bala_entrante(perception):
            return "Defensa"
        return self.id

    def _is_passable(self, move, perception):
        if move not in self.mapping: return False
        obj = perception[self.mapping[move]]
        dist = perception[self.dist_map[move]]
        # Los ladrillos ahora son transitables (porque los vamos a destruir en ruta)
        return not (obj in [ac.UNBREAKABLE, ac.COMMAND_CENTER] and dist < 0.6)

    def _opp(self, move):
        ops = {ac.MOVE_UP: ac.MOVE_DOWN, ac.MOVE_DOWN: ac.MOVE_UP, 
               ac.MOVE_LEFT: ac.MOVE_RIGHT, ac.MOVE_RIGHT: ac.MOVE_LEFT}
        return ops.get(move, ac.NO_MOVE)

    def _bala_entrante(self, perception):
        for dir_idx, dist_idx in [(ac.NEIGHBORHOOD_UP, ac.NEIGHBORHOOD_DIST_UP),
                                  (ac.NEIGHBORHOOD_DOWN, ac.NEIGHBORHOOD_DIST_DOWN),
                                  (ac.NEIGHBORHOOD_LEFT, ac.NEIGHBORHOOD_DIST_LEFT),
                                  (ac.NEIGHBORHOOD_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT)]:
            if perception[dir_idx] == ac.SHELL and perception[dist_idx] < 3: return True
        return False