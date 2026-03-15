from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

# Distancia mínima desde la que disparamos. Por debajo de este valor
# la bala sale desde dentro del hitbox del enemigo y no impacta.
DIST_MIN_DISPARO = 1.2
# Distancia ideal a la que queremos quedarnos para disparar.
DIST_OBJETIVO    = 1.8

class AtaqueSt(State):
    def __init__(self, name):
        super().__init__(name)
        self.evasion_dir    = None
        self.last_x         = -999.0
        self.last_y         = -999.0
        self.last_action    = ac.NO_MOVE
        self.stuck_ticks    = 0
        self.unstuck_action = ac.NO_MOVE

    def Start(self, agent):
        print("Estado Ataque iniciado")

    def Update(self, perception, map, agent):
        # ------------------------------------------------------------------ #
        # 1. OBJETIVO                                                          #
        # ------------------------------------------------------------------ #
        if perception[ac.PLAYER_X] >= 0:
            target_x, target_y = perception[ac.PLAYER_X], perception[ac.PLAYER_Y]
        else:
            target_x, target_y = perception[ac.COMMAND_CENTER_X], perception[ac.COMMAND_CENTER_Y]

        if target_x < 0 or target_y < 0:
            return ac.NO_MOVE, False

        # ------------------------------------------------------------------ #
        # 2. GEOMETRÍA                                                         #
        # ------------------------------------------------------------------ #
        ax, ay      = perception[ac.AGENT_X], perception[ac.AGENT_Y]
        dx          = target_x - ax
        dy          = target_y - ay
        dist_total  = abs(dx) + abs(dy)
        orientation = perception[ac.ORIENTATION]

        mapping = {
            ac.MOVE_UP:    ac.NEIGHBORHOOD_UP,
            ac.MOVE_DOWN:  ac.NEIGHBORHOOD_DOWN,
            ac.MOVE_LEFT:  ac.NEIGHBORHOOD_LEFT,
            ac.MOVE_RIGHT: ac.NEIGHBORHOOD_RIGHT,
        }
        dist_map = {
            ac.MOVE_UP:    ac.NEIGHBORHOOD_DIST_UP,
            ac.MOVE_DOWN:  ac.NEIGHBORHOOD_DIST_DOWN,
            ac.MOVE_LEFT:  ac.NEIGHBORHOOD_DIST_LEFT,
            ac.MOVE_RIGHT: ac.NEIGHBORHOOD_DIST_RIGHT,
        }

        # ------------------------------------------------------------------ #
        # 3. DETECCIÓN DE ATASCOS                                              #
        # ------------------------------------------------------------------ #
        dist_moved = abs(ax - self.last_x) + abs(ay - self.last_y)
        if dist_moved < 0.1 and self.last_action != ac.NO_MOVE:
            self.stuck_ticks += 1
        else:
            self.stuck_ticks    = 0
            self.unstuck_action = ac.NO_MOVE
        self.last_x, self.last_y = ax, ay

        if self.stuck_ticks > 0:
            if self.stuck_ticks == 1:
                if self.last_action in [ac.MOVE_UP, ac.MOVE_DOWN]:
                    self.unstuck_action = ac.MOVE_RIGHT if (round(ax) - ax) > 0 else ac.MOVE_LEFT
                else:
                    self.unstuck_action = ac.MOVE_UP if (round(ay) - ay) > 0 else ac.MOVE_DOWN
            self.last_action = self.unstuck_action
            return self.unstuck_action, (perception[ac.CAN_FIRE] == 1)

        # ------------------------------------------------------------------ #
        # 4. ALINEACIÓN Y DISTANCIA DE COMBATE                                #
        #                                                                      #
        # Queremos estar en la misma fila o columna que el objetivo, a entre  #
        # DIST_MIN_DISPARO y DIST_OBJETIVO casillas. Nunca nos superponemos:  #
        # disparar desde dentro del hitbox del enemigo no causa daño.         #
        # ------------------------------------------------------------------ #
        aligned_x = abs(dx) < 0.5   # misma columna → disparar arriba/abajo
        aligned_y = abs(dy) < 0.5   # misma fila    → disparar izq/der

        if aligned_x or aligned_y:
            if aligned_x:
                face_dir    = ac.MOVE_UP    if dy > 0 else ac.MOVE_DOWN
                dist_lineal = abs(dy)
            else:
                face_dir    = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
                dist_lineal = abs(dx)

            obj_frente = perception[mapping[face_dir]]

            if obj_frente != ac.UNBREAKABLE:
                # Línea de fuego despejada (o ladrillo rompible)

                if dist_lineal < DIST_MIN_DISPARO:
                    # Demasiado cerca: retroceder para salir del hitbox
                    retroceso = self._opposite(face_dir)
                    if retroceso and self._can_move(retroceso, perception, mapping, dist_map):
                        self.last_action = retroceso
                        return retroceso, False
                    # Sin espacio para retroceder: desalinearse girando 90°
                    perp = self._perpendicular(face_dir, dx, dy)
                    if perp and self._can_move(perp, perception, mapping, dist_map):
                        self.last_action = perp
                        return perp, False
                    # Sin opciones de movimiento: disparar de todas formas
                    self.last_action = ac.NO_MOVE
                    return ac.NO_MOVE, (perception[ac.CAN_FIRE] == 1)

                # Distancia correcta (>= DIST_MIN_DISPARO)
                if orientation != face_dir:
                    # Primero girar hacia el objetivo
                    self.last_action = face_dir
                    return face_dir, False

                # Ya apuntamos en la dirección correcta
                if dist_lineal > DIST_OBJETIVO + 0.5:
                    # Todavía algo lejos: avanzar un paso más
                    if self._can_move(face_dir, perception, mapping, dist_map):
                        self.last_action = face_dir
                        return face_dir, (perception[ac.CAN_FIRE] == 1)

                # Posición óptima: quietos y disparamos
                self.last_action = ac.NO_MOVE
                return ac.NO_MOVE, (perception[ac.CAN_FIRE] == 1)

        # ------------------------------------------------------------------ #
        # 5. NAVEGACIÓN: buscar alinearse con el objetivo                     #
        #                                                                      #
        # Preferimos el eje donde la desviación lateral es menor, ya que      #
        # necesitamos menos pasos para entrar en línea de fuego.              #
        # Nunca nos acercamos tanto que nos superponemos.                     #
        # ------------------------------------------------------------------ #
        if abs(dx) <= abs(dy):
            # Reducir dx primero → alinearse en columna (disparar arriba/abajo)
            preferred = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
            secondary = ac.MOVE_UP    if dy > 0 else ac.MOVE_DOWN
        else:
            # Reducir dy primero → alinearse en fila (disparar izq/der)
            preferred = ac.MOVE_UP    if dy > 0 else ac.MOVE_DOWN
            secondary = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT

        def bloqueado(act):
            if act not in mapping:
                return True
            obj  = perception[mapping[act]]
            dist = perception[dist_map[act]]
            if obj in [ac.UNBREAKABLE, ac.COMMAND_CENTER]:
                return dist < 0.6
            # No avanzar si nos metería dentro del hitbox del objetivo
            if act == secondary and dist_total - 1.0 < DIST_MIN_DISPARO:
                return True
            return False

        action = ac.NO_MOVE
        if not bloqueado(preferred):
            action = preferred
            self.evasion_dir = None
        elif self.evasion_dir and not bloqueado(self.evasion_dir):
            action = self.evasion_dir
        else:
            if not bloqueado(secondary):
                action = secondary
                self.evasion_dir = secondary
            else:
                opposite = self._opposite(preferred)
                if opposite and not bloqueado(opposite):
                    action = opposite
                    self.evasion_dir = opposite

        # ------------------------------------------------------------------ #
        # 6. DISPAROS OPORTUNISTAS MIENTRAS NAVEGAMOS                         #
        # ------------------------------------------------------------------ #
        shot = False
        if perception[ac.CAN_FIRE] == 1 and dist_total >= DIST_MIN_DISPARO:
            if aligned_x:
                if dy > 0 and orientation == ac.MOVE_UP:    shot = True
                if dy < 0 and orientation == ac.MOVE_DOWN:  shot = True
            if aligned_y:
                if dx > 0 and orientation == ac.MOVE_RIGHT: shot = True
                if dx < 0 and orientation == ac.MOVE_LEFT:  shot = True

        # ------------------------------------------------------------------ #
        # 7. DESTRUCCIÓN DE MUROS EN RUTA                                     #
        # ------------------------------------------------------------------ #
        if action != ac.NO_MOVE and action in mapping:
            obj_frente  = perception[mapping[action]]
            dist_frente = perception[dist_map[action]]
            if obj_frente == ac.BRICK and dist_frente < 1.0:
                if orientation != action:
                    self.last_action = action
                    return action, False
                else:
                    if dist_frente < 0.6:
                        action = ac.NO_MOVE
                    if perception[ac.CAN_FIRE] == 1:
                        shot = True

        self.last_action = action
        return action, shot

    # ------------------------------------------------------------------ #
    # TRANSICIONES                                                         #
    # ------------------------------------------------------------------ #
    def Transit(self, perception, map):
        if perception[ac.PLAYER_X] < 0 and perception[ac.COMMAND_CENTER_X] < 0:
            return "Exploracion"
        if self._bala_entrante(perception):
            return "Defensa"
        return self.id

    # ------------------------------------------------------------------ #
    # UTILIDADES                                                           #
    # ------------------------------------------------------------------ #
    def _opposite(self, action):
        ops = {
            ac.MOVE_UP:    ac.MOVE_DOWN,
            ac.MOVE_DOWN:  ac.MOVE_UP,
            ac.MOVE_LEFT:  ac.MOVE_RIGHT,
            ac.MOVE_RIGHT: ac.MOVE_LEFT,
        }
        return ops.get(action, None)

    def _perpendicular(self, face_dir, dx, dy):
        """Dirección perpendicular al eje de disparo, hacia el lado con más espacio."""
        if face_dir in [ac.MOVE_UP, ac.MOVE_DOWN]:
            return ac.MOVE_RIGHT if dx >= 0 else ac.MOVE_LEFT
        else:
            return ac.MOVE_UP if dy >= 0 else ac.MOVE_DOWN

    def _can_move(self, action, perception, mapping, dist_map):
        obj  = perception[mapping[action]]
        dist = perception[dist_map[action]]
        if obj in [ac.UNBREAKABLE, ac.BRICK, ac.COMMAND_CENTER]:
            return dist >= 0.6
        return True

    def _bala_entrante(self, perception):
        for dir_idx, dist_idx in [
            (ac.NEIGHBORHOOD_UP,    ac.NEIGHBORHOOD_DIST_UP),
            (ac.NEIGHBORHOOD_DOWN,  ac.NEIGHBORHOOD_DIST_DOWN),
            (ac.NEIGHBORHOOD_LEFT,  ac.NEIGHBORHOOD_DIST_LEFT),
            (ac.NEIGHBORHOOD_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT),
        ]:
            if perception[dir_idx] == ac.SHELL and perception[dist_idx] < 3:
                return True
        return False