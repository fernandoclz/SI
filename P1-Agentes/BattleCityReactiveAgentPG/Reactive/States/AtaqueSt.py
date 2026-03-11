from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

class AtaqueSt(State):
    def __init__(self, name):
        super().__init__(name)
        self.evasion_dir = None

    def Start(self, agent):
        print("Estado Ataque iniciado")

    def Update(self, perception, map, agent):
        if perception[ac.PLAYER_X] >= 0:
            target_x, target_y = perception[ac.PLAYER_X], perception[ac.PLAYER_Y]
        else:
            target_x, target_y = perception[ac.COMMAND_CENTER_X], perception[ac.COMMAND_CENTER_Y]

        if target_x < 0 or target_y < 0:
            return ac.NO_MOVE, False

        # Trabajamos con los decimales reales
        ax, ay = perception[ac.AGENT_X], perception[ac.AGENT_Y]
        dx = target_x - ax
        dy = target_y - ay
        distancia_total = abs(dx) + abs(dy)

        orientation = perception[ac.ORIENTATION]

        # --- 1. MODO COMBATE A CORTA DISTANCIA (CQC) ---
        if distancia_total < 1.5:
            # Determinamos la dirección principal hacia la que debemos encararnos
            if abs(dx) > abs(dy):
                face_dir = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
            else:
                # ¡CORREGIDO EL EJE Y AQUÍ TAMBIÉN!
                face_dir = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN
                
            # Si no le estamos mirando de frente, giramos
            if orientation != face_dir:
                return face_dir, False
            else:
                # Si ya le estamos mirando, ¡FUEGO A DISCRECIÓN!
                # Al estar tan cerca no nos movemos para no colisionar las hitboxes
                return ac.NO_MOVE, True

        # --- 2. MODO PERSECUCIÓN Y NAVEGACIÓN NORMAL ---
        if abs(dx) > abs(dy):
            preferred = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
        else:
            # ¡CORREGIDO EL EJE Y PARA LA NAVEGACIÓN!
            preferred = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN

        action = ac.NO_MOVE
        if self._can_move(preferred, perception):
            action = preferred
            self.evasion_dir = None  
        else:
            if self.evasion_dir and self._can_move(self.evasion_dir, perception):
                action = self.evasion_dir
            else:
                if preferred in [ac.MOVE_UP, ac.MOVE_DOWN]:
                    opciones = [ac.MOVE_RIGHT, ac.MOVE_LEFT] if dx >= 0 else [ac.MOVE_LEFT, ac.MOVE_RIGHT]
                else:
                    # Eje Y corregido para la evasión
                    opciones = [ac.MOVE_UP, ac.MOVE_DOWN] if dy >= 0 else [ac.MOVE_DOWN, ac.MOVE_UP]

                for op in opciones:
                    if self._can_move(op, perception):
                        action = op
                        self.evasion_dir = op
                        break
                
                if action == ac.NO_MOVE:
                    opposite = self._opposite(preferred)
                    if opposite and self._can_move(opposite, perception):
                        action = opposite
                        self.evasion_dir = opposite

        # --- 3. LÓGICA DE DISPARO EN MOVIMIENTO (Larga Distancia) ---
        shot = False
        if perception[ac.CAN_FIRE] == 1:
            # Usamos un margen de error (0.5) en lugar de igualdad estricta matemática
            if abs(dx) < 0.5: # Prácticamente alineados verticalmente
                if dy > 0 and orientation == ac.MOVE_UP: shot = True
                elif dy < 0 and orientation == ac.MOVE_DOWN: shot = True
            elif abs(dy) < 0.5: # Prácticamente alineados horizontalmente
                if dx > 0 and orientation == ac.MOVE_RIGHT: shot = True
                elif dx < 0 and orientation == ac.MOVE_LEFT: shot = True

        return action, shot

    def Transit(self, perception, map):
        if perception[ac.PLAYER_X] < 0 and perception[ac.COMMAND_CENTER_X] < 0:
            return "Exploracion"
        if self._bala_entrante(perception):
            return "Defensa"
        return self.id

    def _can_move(self, action, perception):
        obj, dist = None, 999.0
        if action == ac.MOVE_UP: obj, dist = perception[ac.NEIGHBORHOOD_UP], perception[ac.NEIGHBORHOOD_DIST_UP]
        elif action == ac.MOVE_DOWN: obj, dist = perception[ac.NEIGHBORHOOD_DOWN], perception[ac.NEIGHBORHOOD_DIST_DOWN]
        elif action == ac.MOVE_LEFT: obj, dist = perception[ac.NEIGHBORHOOD_LEFT], perception[ac.NEIGHBORHOOD_DIST_LEFT]
        elif action == ac.MOVE_RIGHT: obj, dist = perception[ac.NEIGHBORHOOD_RIGHT], perception[ac.NEIGHBORHOOD_DIST_RIGHT]
        else: return False

        if obj in [ac.UNBREAKABLE, ac.BRICK, ac.COMMAND_CENTER]:
            if dist < 0.6: return False
        return True

    def _opposite(self, action):
        ops = {ac.MOVE_UP: ac.MOVE_DOWN, ac.MOVE_DOWN: ac.MOVE_UP, ac.MOVE_LEFT: ac.MOVE_RIGHT, ac.MOVE_RIGHT: ac.MOVE_LEFT}
        return ops.get(action, None)

    def _bala_entrante(self, perception):
        for dir_idx, dist_idx in [(ac.NEIGHBORHOOD_UP, ac.NEIGHBORHOOD_DIST_UP),
                                   (ac.NEIGHBORHOOD_DOWN, ac.NEIGHBORHOOD_DIST_DOWN),
                                   (ac.NEIGHBORHOOD_LEFT, ac.NEIGHBORHOOD_DIST_LEFT),
                                   (ac.NEIGHBORHOOD_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT)]:
            if perception[dir_idx] == ac.SHELL and perception[dist_idx] < 3: return True
        return False