from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

DIST_MIN_DISPARO = 1.2
DIST_OBJETIVO    = 1.8

class AtaqueSt(State):
    def __init__(self, name):
        super().__init__(name)
        self.evasion_dir = None
        self.last_x, self.last_y = -999.0, -999.0
        self.last_action = ac.NO_MOVE
        self.stuck_ticks = 0
        self.unstuck_action = ac.NO_MOVE
        
        # Guardamos los mapas como atributos de clase para no recrearlos
        self.mapping = {ac.MOVE_UP: ac.NEIGHBORHOOD_UP, ac.MOVE_DOWN: ac.NEIGHBORHOOD_DOWN,
                        ac.MOVE_LEFT: ac.NEIGHBORHOOD_LEFT, ac.MOVE_RIGHT: ac.NEIGHBORHOOD_RIGHT}
        self.dist_map = {ac.MOVE_UP: ac.NEIGHBORHOOD_DIST_UP, ac.MOVE_DOWN: ac.NEIGHBORHOOD_DIST_DOWN,
                         ac.MOVE_LEFT: ac.NEIGHBORHOOD_DIST_LEFT, ac.MOVE_RIGHT: ac.NEIGHBORHOOD_DIST_RIGHT}

    def Start(self, agent):
        print("Estado Ataque iniciado")

    def Update(self, perception, map, agent):
        # 1. OBJETIVO Y GEOMETRÍA
        tx = perception[ac.PLAYER_X] if perception[ac.PLAYER_X] >= 0 else perception[ac.COMMAND_CENTER_X]
        ty = perception[ac.PLAYER_Y] if perception[ac.PLAYER_Y] >= 0 else perception[ac.COMMAND_CENTER_Y]
        if tx < 0 or ty < 0: return ac.NO_MOVE, False

        ax, ay = perception[ac.AGENT_X], perception[ac.AGENT_Y]
        dx, dy = tx - ax, ty - ay
        dist_total = abs(dx) + abs(dy)
        orientation = perception[ac.ORIENTATION]
        can_fire = perception[ac.CAN_FIRE] == 1

        # 2. DETECCIÓN DE ATASCOS
        dist_moved = abs(ax - self.last_x) + abs(ay - self.last_y)
        if dist_moved < 0.1 and self.last_action != ac.NO_MOVE:
            self.stuck_ticks += 1
        else:
            self.stuck_ticks, self.unstuck_action = 0, ac.NO_MOVE
        self.last_x, self.last_y = ax, ay

        if self.stuck_ticks > 0:
            if self.stuck_ticks == 1:
                if self.last_action in [ac.MOVE_UP, ac.MOVE_DOWN]:
                    self.unstuck_action = ac.MOVE_RIGHT if (round(ax) - ax) > 0 else ac.MOVE_LEFT
                else:
                    self.unstuck_action = ac.MOVE_UP if (round(ay) - ay) > 0 else ac.MOVE_DOWN
            self.last_action = self.unstuck_action
            return self.unstuck_action, can_fire

        # 3. DETERMINAR ACCIÓN (Alineación y Combate vs Navegación)
        aligned_x, aligned_y = abs(dx) < 0.5, abs(dy) < 0.5
        action, shoot = ac.NO_MOVE, False

        if aligned_x or aligned_y:
            # LÓGICA DE COMBATE
            face_dir = (ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN) if aligned_x else (ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT)
            dist_lin = abs(dy) if aligned_x else abs(dx)

            if dist_lin < DIST_MIN_DISPARO:
                # Muy cerca: retroceder o apartarse
                retroceso = self._opposite(face_dir)
                if retroceso and self._can_move(retroceso, perception): action = retroceso
                else: action = self._perpendicular(face_dir, dx, dy)
            elif dist_lin > DIST_OBJETIVO + 2.0:
                # Lejos: acercarse
                action = face_dir
            elif orientation != face_dir:
                # Distancia correcta, mal orientado
                action = face_dir
            else:
                # Posición perfecta
                shoot = True
        else:
            # LÓGICA DE NAVEGACIÓN
            pref_x = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
            pref_y = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN
            preferred, secondary = (pref_x, pref_y) if abs(dx) <= abs(dy) else (pref_y, pref_x)
            dist_moved = abs(ax - self.last_x) + abs(ay - self.last_y)

            # Evitar meterse en el hitbox al avanzar por el eje secundario
            sec_blocked = (dist_total - 1.0 < DIST_MIN_DISPARO)

            if self._can_move(preferred, perception):
                action = preferred
            elif self.evasion_dir and self._can_move(self.evasion_dir, perception):
                action = self.evasion_dir
            elif self._can_move(secondary, perception) and not sec_blocked:
                action, self.evasion_dir = secondary, secondary
            else:
                opp = self._opposite(preferred)
                if opp and self._can_move(opp, perception):
                    action, self.evasion_dir = opp, opp

            if action in self.mapping:
                obj_frente = perception[self.mapping[action]]
                dist_frente = perception[self.dist_map[action]]

                if obj_frente == ac.BRICK and dist_frente < 1.0:
                    if orientation == action:
                        if dist_frente < 0.6:
                            action, shoot = ac.NO_MOVE, True

            # Disparo oportunista
            if can_fire and dist_total >= DIST_MIN_DISPARO:
                if (aligned_x and dy * (1 if orientation == ac.MOVE_UP else -1) > 0) or \
                   (aligned_y and dx * (1 if orientation == ac.MOVE_RIGHT else -1) > 0):
                    shoot = True

        # 4. DESTRUCCIÓN DE MUROS EN RUTA
        if action != ac.NO_MOVE and action in self.mapping:
            obj, dist = perception[self.mapping[action]], perception[self.dist_map[action]]
            if obj == ac.BRICK and dist < 1.0:
                if orientation != action:
                    shoot = False # Primero girar
                else:
                    if dist < 0.6: action = ac.NO_MOVE # Parar antes de chocar
                    shoot = True

        self.last_action = action
        return action, (shoot and can_fire)

    # ------------------------------------------------------------------ #
    # TRANSICIONES Y UTILIDADES                                            #
    # ------------------------------------------------------------------ #
    def Transit(self, perception, map):
        if perception[ac.PLAYER_X] < 0 and perception[ac.COMMAND_CENTER_X] < 0:
            return "Exploracion"
        if self._bala_entrante(perception):
            return "Defensa"
        return self.id

    def _opposite(self, action):
        ops = {ac.MOVE_UP: ac.MOVE_DOWN, ac.MOVE_DOWN: ac.MOVE_UP, ac.MOVE_LEFT: ac.MOVE_RIGHT, ac.MOVE_RIGHT: ac.MOVE_LEFT}
        return ops.get(action, None)

    def _perpendicular(self, face_dir, dx, dy):
        if face_dir in [ac.MOVE_UP, ac.MOVE_DOWN]: return ac.MOVE_RIGHT if dx >= 0 else ac.MOVE_LEFT
        return ac.MOVE_UP if dy >= 0 else ac.MOVE_DOWN

    def _can_move(self, action, perception):
        if action not in self.mapping: return False
        obj = perception[self.mapping[action]]
        dist = perception[self.dist_map[action]]
        return not (obj in [ac.UNBREAKABLE, ac.COMMAND_CENTER] and dist < 0.6)

    def _bala_entrante(self, perception):
        for dir_idx, dist_idx in [(ac.NEIGHBORHOOD_UP, ac.NEIGHBORHOOD_DIST_UP), (ac.NEIGHBORHOOD_DOWN, ac.NEIGHBORHOOD_DIST_DOWN),
                                  (ac.NEIGHBORHOOD_LEFT, ac.NEIGHBORHOOD_DIST_LEFT), (ac.NEIGHBORHOOD_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT)]:
            if perception[dir_idx] == ac.SHELL and perception[dist_idx] < 5: return True
        return False