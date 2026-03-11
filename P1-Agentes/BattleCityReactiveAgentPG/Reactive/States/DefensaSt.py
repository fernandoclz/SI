from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

class DefensaSt(State):
    def __init__(self, name):
        super().__init__(name)

    def Start(self, agent):
        print("Estado Defensa iniciado")

    def Update(self, perception, map, agent):
        bala_dir = self._bala_entrante(perception)
        if bala_dir is None:
            return ac.NO_MOVE, False

        if perception[ac.CAN_FIRE] == 1:
            action = self._dir_to_action(bala_dir)
            if perception[ac.ORIENTATION] == action:
                return action, True
            else:
                return action, False
        else:
            if bala_dir in [ac.NEIGHBORHOOD_UP, ac.NEIGHBORHOOD_DOWN]:
                if self._can_move(ac.MOVE_LEFT, perception): return ac.MOVE_LEFT, False
                elif self._can_move(ac.MOVE_RIGHT, perception): return ac.MOVE_RIGHT, False
            else:
                if self._can_move(ac.MOVE_UP, perception): return ac.MOVE_UP, False
                elif self._can_move(ac.MOVE_DOWN, perception): return ac.MOVE_DOWN, False
            
            return ac.NO_MOVE, False

    def Transit(self, perception, map):
        if self._bala_entrante(perception) is None:
            return "Exploracion"
        return self.id

    def _bala_entrante(self, perception):
        for dir_idx, dist_idx in [(ac.NEIGHBORHOOD_UP, ac.NEIGHBORHOOD_DIST_UP),
                                   (ac.NEIGHBORHOOD_DOWN, ac.NEIGHBORHOOD_DIST_DOWN),
                                   (ac.NEIGHBORHOOD_LEFT, ac.NEIGHBORHOOD_DIST_LEFT),
                                   (ac.NEIGHBORHOOD_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT)]:
            if perception[dir_idx] == ac.SHELL and perception[dist_idx] < 5: return dir_idx
        return None

    def _dir_to_action(self, dir_idx):
        if dir_idx == ac.NEIGHBORHOOD_UP: return ac.MOVE_UP
        elif dir_idx == ac.NEIGHBORHOOD_DOWN: return ac.MOVE_DOWN
        elif dir_idx == ac.NEIGHBORHOOD_LEFT: return ac.MOVE_LEFT
        elif dir_idx == ac.NEIGHBORHOOD_RIGHT: return ac.MOVE_RIGHT
        return ac.NO_MOVE

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