from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

class ExploracionSt(State):
    def __init__(self, name):
        super().__init__(name)
        self.evasion_dir = None

    def Start(self, agent):
        print("Estado Exploración iniciado")

    def Update(self, perception, map, agent):
        if perception[ac.HEALTH] <= 1 and perception[ac.LIFE_X] >= 0:
            target_x, target_y = perception[ac.LIFE_X], perception[ac.LIFE_Y]
        else:
            target_x, target_y = perception[ac.COMMAND_CENTER_X], perception[ac.COMMAND_CENTER_Y]

        if target_x < 0 or target_y < 0:
            target_x, target_y = perception[ac.EXIT_X], perception[ac.EXIT_Y]

        if target_x < 0 or target_y < 0:
            return ac.NO_MOVE, False

        agent_x, agent_y = int(perception[ac.AGENT_X]), int(perception[ac.AGENT_Y])
        dx, dy = target_x - agent_x, target_y - agent_y

        # CORREGIDO EL EJE Y
        if abs(dx) > abs(dy):
            preferred = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
        else:
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
                    opciones = [ac.MOVE_UP, ac.MOVE_DOWN] if dy >= 0 else [ac.MOVE_DOWN, ac.MOVE_UP]

                for op in opciones:
                    if self._can_move(op, perception):
                        action = op
                        self.evasion_dir = op
                        break
            
                if action == ac.NO_MOVE:
                    ops = {ac.MOVE_UP: ac.MOVE_DOWN, ac.MOVE_DOWN: ac.MOVE_UP, ac.MOVE_LEFT: ac.MOVE_RIGHT, ac.MOVE_RIGHT: ac.MOVE_LEFT}
                    opposite = ops.get(preferred, None)
                    if opposite and self._can_move(opposite, perception):
                        action = opposite
                        self.evasion_dir = opposite

        shot = False
        mapping = {ac.MOVE_UP: ac.NEIGHBORHOOD_UP, ac.MOVE_DOWN: ac.NEIGHBORHOOD_DOWN, 
                   ac.MOVE_LEFT: ac.NEIGHBORHOOD_LEFT, ac.MOVE_RIGHT: ac.NEIGHBORHOOD_RIGHT}
        
        if perception[mapping[preferred]] == ac.BRICK and perception[ac.NEIGHBORHOOD_DIST_UP + preferred - 1] < 1.0:
            action = preferred
            if perception[ac.ORIENTATION] == preferred and perception[ac.CAN_FIRE] == 1:
                shot = True

        return action, shot

    def Transit(self, perception, map):
        if self._bala_entrante(perception):
            return "Defensa"
        if perception[ac.HEALTH] <= 1 and perception[ac.LIFE_X] >= 0:
            return "Huida"
        if perception[ac.PLAYER_X] >= 0 and perception[ac.PLAYER_Y] >= 0:
            return "Ataque"
        return self.id
        
    def _bala_entrante(self, perception):
        for dir_idx, dist_idx in [(ac.NEIGHBORHOOD_UP, ac.NEIGHBORHOOD_DIST_UP),
                                (ac.NEIGHBORHOOD_DOWN, ac.NEIGHBORHOOD_DIST_DOWN),
                                (ac.NEIGHBORHOOD_LEFT, ac.NEIGHBORHOOD_DIST_LEFT),
                                (ac.NEIGHBORHOOD_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT)]:
            if perception[dir_idx] == ac.SHELL and perception[dist_idx] < 3: return True
        return False

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