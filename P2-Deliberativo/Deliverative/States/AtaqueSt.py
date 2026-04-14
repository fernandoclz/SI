from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac


class AtaqueSt(State):
    def __init__(self, name):
        super().__init__(name)
        self.dist_min_disparo = 0.8
        self._ticks_sin_progreso = 0
        self._last_dist = None
        self._en_posicion = False  # flag: estamos dentro del umbral disparando

    def Start(self, agent):
        print("Estado Ataque iniciado")
        self._ticks_sin_progreso = 0
        self._last_dist = None
        self._en_posicion = False

    def Update(self, perception, map, agent):
        orientation = perception[ac.TANK_ORIENTATION]
        can_fire = perception[ac.CAN_FIRE] == 1

        tx = perception[ac.PLAYER_X] if perception[ac.PLAYER_X] >= 0 else perception[ac.COMMAND_CENTER_X]
        ty = perception[ac.PLAYER_Y] if perception[ac.PLAYER_Y] >= 0 else perception[ac.COMMAND_CENTER_Y]

        if tx < 0 or ty < 0:
            return ac.NO_MOVE, False

        ax, ay = perception[ac.AGENT_X], perception[ac.AGENT_Y]
        dx, dy = tx - ax, ty - ay
        dist = abs(dx) + abs(dy)

        # Paso del motor físico observado empíricamente (~1.2 unidades/tick)
        # El umbral debe ser mayor que un paso para absorber overshoot
        UMBRAL_PARADA = 1.8

        # Calcular la mejor dirección de disparo
        if abs(dx) >= abs(dy):
            best_dir = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
        else:
            best_dir = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN

        # --- 1. Dentro del umbral: modo estático ---
        if dist < UMBRAL_PARADA:
            self._en_posicion = True
            # Resetear contador: no estamos atascados, estamos en posición
            self._ticks_sin_progreso = 0
            self._last_dist = None

            if orientation == best_dir:
                # Apuntando: disparar sin moverse
                return ac.NO_MOVE, can_fire
            else:
                # Girando: disparar igualmente en la dirección actual
                # (puede acertar si hay algo en esa línea)
                agent.directionToLook = best_dir - 1
                return ac.NO_MOVE, can_fire

        # --- 2. Fuera del umbral: tracking de progreso ---
        self._en_posicion = False
        if self._last_dist is not None:
            if dist >= self._last_dist - 0.05:
                self._ticks_sin_progreso += 1
            else:
                self._ticks_sin_progreso = 0
        self._last_dist = dist

        TOLERANCIA = 0.5
        aligned_x = abs(dy) <= TOLERANCIA
        aligned_y = abs(dx) <= TOLERANCIA

        # --- 3. Alineado: disparar desde aquí sin moverse ---
        # Si estamos en la misma fila/columna que el objetivo, no hay que acercarse:
        # giramos, disparamos y esperamos. Marcamos _en_posicion para no detectar atasco.
        if aligned_x:
            self._en_posicion = True
            self._ticks_sin_progreso = 0
            face_dir = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
            agent.directionToLook = face_dir - 1
            return ac.NO_MOVE, can_fire

        elif aligned_y:
            self._en_posicion = True
            self._ticks_sin_progreso = 0
            face_dir = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN
            agent.directionToLook = face_dir - 1
            return ac.NO_MOVE, can_fire
            

        # --- 4. Mover hacia el objetivo ---
        return best_dir, can_fire

    def Transit(self, perception, map):
        if self._bala_entrante(perception):
            return "Defensa"

        if perception[ac.HEALTH] <= 1 and perception[ac.LIFE_X] >= 0:
            return "Huida"

        player_visible = perception[ac.PLAYER_X] >= 0
        cc_visible     = perception[ac.COMMAND_CENTER_X] >= 0

        if not player_visible and not cc_visible:
            return "ExecutePlan"

        # Solo detectar atasco si NO estamos en posición de disparo
        if not self._en_posicion and self._ticks_sin_progreso > 8:
            print(f"[Ataque] Atasco real tras {self._ticks_sin_progreso} ticks → ExecutePlan")
            self._ticks_sin_progreso = 0
            self._last_dist = None
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