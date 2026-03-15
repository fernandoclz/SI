from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

# Salud máxima asumida. Si HEALTH < HEALTH_MAX, merece la pena recoger vida
# aunque no estemos en estado crítico.
HEALTH_MAX = 3


class ExploracionSt(State):
    def __init__(self, name):
        super().__init__(name)
        self.evasion_dir  = None
        self.last_x       = -999.0
        self.last_y       = -999.0
        self.stuck_ticks  = 0

    def Start(self, agent):
        print("Estado Exploración iniciado")

    def Update(self, perception, map, agent):

        # ------------------------------------------------------------------ #
        # 1. OBJETIVO                                                          #
        #                                                                      #
        # Prioridad de objetivos:                                              #
        #   1. Ítem de vida visible y salud no máxima → recogerlo siempre     #
        #   2. Base enemiga visible                                            #
        #   3. Salida del nivel                                                #
        # ------------------------------------------------------------------ #
        life_visible = perception[ac.LIFE_X] >= 0
        health_baja  = perception[ac.HEALTH] < HEALTH_MAX

        if life_visible and health_baja:
            target_x, target_y = perception[ac.LIFE_X], perception[ac.LIFE_Y]
        else:
            target_x, target_y = perception[ac.COMMAND_CENTER_X], perception[ac.COMMAND_CENTER_Y]

        if target_x < 0 or target_y < 0:
            target_x, target_y = perception[ac.EXIT_X], perception[ac.EXIT_Y]

        if target_x < 0 or target_y < 0:
            return ac.NO_MOVE, False

        # ------------------------------------------------------------------ #
        # 2. GEOMETRÍA                                                         #
        # ------------------------------------------------------------------ #
        ax = perception[ac.AGENT_X]
        ay = perception[ac.AGENT_Y]
        dx = target_x - ax
        dy = target_y - ay
        dist_total = abs(dx) + abs(dy)

        # Si ya estamos encima del objetivo, no hacer nada
        # (el juego debería recogerlo automáticamente)
        if dist_total < 0.5:
            self.evasion_dir = None
            return ac.NO_MOVE, False

        if abs(dx) > abs(dy):
            preferred = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
        else:
            preferred = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN

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

        def obj_en(d):  return perception[mapping[d]]
        def dist_en(d): return perception[dist_map[d]]

        def es_muro_duro(d):
            return obj_en(d) in [ac.UNBREAKABLE, ac.COMMAND_CENTER] and dist_en(d) < 0.7

        def es_ladrillo(d):
            return obj_en(d) in [ac.BRICK, ac.SEMI_BREKABLE] and dist_en(d) < 1.5

        def es_transitable(d):
            return not es_muro_duro(d)

        def mover_o_disparar(d):
            """Devuelve (accion, disparo) para avanzar en dirección d,
            destruyendo el ladrillo si hay uno delante."""
            if es_ladrillo(d):
                if perception[ac.ORIENTATION] != d:
                    return d, False
                if perception[ac.CAN_FIRE] == 1:
                    return ac.NO_MOVE, True
                return ac.NO_MOVE, False
            return d, False

        # ------------------------------------------------------------------ #
        # 3. DETECTOR DE ATASCOS                                               #
        # ------------------------------------------------------------------ #
        dist_moved = abs(ax - self.last_x) + abs(ay - self.last_y)
        if dist_moved < 0.05:
            self.stuck_ticks += 1
        else:
            self.stuck_ticks = 0
        self.last_x, self.last_y = ax, ay

        if self.stuck_ticks >= 4:
            self.evasion_dir = None
            self.stuck_ticks = 0

        # ------------------------------------------------------------------ #
        # 4. DIRECCIÓN PREFERIDA LIBRE → avanzar                             #
        # ------------------------------------------------------------------ #
        if es_transitable(preferred):
            self.evasion_dir = None
            return mover_o_disparar(preferred)

        # ------------------------------------------------------------------ #
        # 5. EVASIÓN                                                           #
        #                                                                      #
        # La evasión se mantiene mientras:                                    #
        #   - La evasión elegida siga siendo transitable, Y                   #
        #   - La dirección preferred siga bloqueada (si se despeja, paso 4    #
        #     ya lo captura en el tick siguiente)                              #
        #                                                                      #
        # Criterio para elegir evasión: la perpendicular que maximiza la      #
        # reducción de dist_total. Esto evita que el agente rodee un          #
        # obstáculo en la dirección equivocada (alejándose más).              #
        # ------------------------------------------------------------------ #
        if self.evasion_dir is not None and es_transitable(self.evasion_dir):
            return mover_o_disparar(self.evasion_dir)

        # Calcular nueva evasión
        if preferred in [ac.MOVE_UP, ac.MOVE_DOWN]:
            perps = [ac.MOVE_RIGHT, ac.MOVE_LEFT]
        else:
            perps = [ac.MOVE_UP, ac.MOVE_DOWN]

        opuesta = {
            ac.MOVE_UP: ac.MOVE_DOWN, ac.MOVE_DOWN: ac.MOVE_UP,
            ac.MOVE_LEFT: ac.MOVE_RIGHT, ac.MOVE_RIGHT: ac.MOVE_LEFT,
        }.get(preferred)

        # Ordenar perpendiculares por cuál reduce más la distancia al objetivo.
        # Simular un paso en cada dirección y ver cuánto cambia dist_total.
        def dist_si_muevo(d):
            """Distancia Manhattan estimada al objetivo si damos un paso en d."""
            nx = ax + (1 if d == ac.MOVE_RIGHT else -1 if d == ac.MOVE_LEFT else 0)
            ny = ay + (1 if d == ac.MOVE_UP    else -1 if d == ac.MOVE_DOWN  else 0)
            return abs(target_x - nx) + abs(target_y - ny)

        perps_ordenadas = sorted(
            [p for p in perps if es_transitable(p)],
            key=dist_si_muevo
        )

        candidatas = perps_ordenadas
        if opuesta and es_transitable(opuesta):
            candidatas = candidatas + [opuesta]

        for cand in candidatas:
            self.evasion_dir = cand
            return mover_o_disparar(cand)

        return ac.NO_MOVE, False

    # ------------------------------------------------------------------ #
    # TRANSICIONES                                                         #
    # ------------------------------------------------------------------ #
    def Transit(self, perception, map):
        if self._bala_entrante(perception):
            return "Defensa"
        # Ir a Huida si la vida está muy baja (crítico)
        if perception[ac.HEALTH] <= 1 and perception[ac.LIFE_X] >= 0:
            return "Huida"
        if perception[ac.PLAYER_X] >= 0 and perception[ac.PLAYER_Y] >= 0:
            return "Ataque"
        return self.id

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