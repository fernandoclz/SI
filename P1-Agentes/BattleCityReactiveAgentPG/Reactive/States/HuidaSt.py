from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

class HuidaSt(State):
    def __init__(self, name):
        super().__init__(name)

    def Start(self, agent):
        print("Estado Huida iniciado")

    def Update(self, perception, map, agent):
        if perception[ac.LIFE_X] >= 0:
            target_x, target_y = perception[ac.LIFE_X], perception[ac.LIFE_Y]
            agent_x, agent_y = int(perception[ac.AGENT_X]), int(perception[ac.AGENT_Y])
            dx, dy = target_x - agent_x, target_y - agent_y
            
            # CORREGIDO EL EJE Y
            if abs(dx) > abs(dy):
                action = ac.MOVE_RIGHT if dx > 0 else ac.MOVE_LEFT
            else:
                action = ac.MOVE_UP if dy > 0 else ac.MOVE_DOWN
                
            if self._can_move(action, perception):
                return action, False
            else:
                for a in [ac.MOVE_UP, ac.MOVE_DOWN, ac.MOVE_LEFT, ac.MOVE_RIGHT]:
                    if self._can_move(a, perception):
                        return a, False
                return ac.NO_MOVE, False
        else:
            return ac.NO_MOVE, False

    def Transit(self, perception, map):
        if perception[ac.LIFE_X] < 0 or perception[ac.HEALTH] > 1:
            return "Exploracion"
        if self._bala_entrante(perception):
            return "Defensa"
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