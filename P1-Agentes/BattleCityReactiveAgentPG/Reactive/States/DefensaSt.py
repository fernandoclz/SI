from StateMachine.State import State
from States.AgentConsts import AgentConsts as ac

class DefensaSt(State):
    def __init__(self, name):
        super().__init__(name)
        # Diccionario para traducir dónde detectamos la bala a qué acción realizar
        self.react = {
            ac.NEIGHBORHOOD_UP:    ac.MOVE_UP,
            ac.NEIGHBORHOOD_DOWN:  ac.MOVE_DOWN,
            ac.NEIGHBORHOOD_LEFT:  ac.MOVE_LEFT,
            ac.NEIGHBORHOOD_RIGHT: ac.MOVE_RIGHT
        }

    def Update(self, perception, map, agent):
        # Valores por defecto: quietos y sin disparar
        action = ac.NO_MOVE
        shoot = False

        # 1. DETECTAR BALA PELIGROSA
        for dir_idx, dist_idx in [(ac.NEIGHBORHOOD_UP, ac.NEIGHBORHOOD_DIST_UP), (ac.NEIGHBORHOOD_DOWN, ac.NEIGHBORHOOD_DIST_DOWN),
                                  (ac.NEIGHBORHOOD_LEFT, ac.NEIGHBORHOOD_DIST_LEFT), (ac.NEIGHBORHOOD_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT)]:
            print("Ataque ha detectado la bala a menos de 5")
            if perception[dir_idx] == ac.SHELL:
                print("Defensa detecta la bala")
                # Dirección para encarar la amenaza
                face_bullet_dir = self.react[dir_idx]
                
                # 2. DEFENSA OFENSIVA: Si tenemos munición, disparamos HACIA la bala
                if perception[ac.CAN_FIRE] == 1.0:
                    action = ac.NO_MOVE
                    shoot = True
                    return action, shoot  # Ejecutamos disparo y salimos
                print("No tiene bala")
                # 3. ESQUIVA: Si no podemos disparar, esquivamos lateralmente
                perp_moves = [ac.MOVE_LEFT, ac.MOVE_RIGHT] if face_bullet_dir in [ac.MOVE_UP, ac.MOVE_DOWN] else [ac.MOVE_UP, ac.MOVE_DOWN]
                
                for escape in perp_moves:
                    if self._can_move(escape, perception):
                        action = escape
                        shoot = False
                        return action, shoot  # Ejecutamos huida y salimos
                
        # Si llegamos aquí, es que no hay peligro o estamos totalmente acorralados
        return action, shoot

    def Transit(self, perception, map):
        # Si no hay balas cerca, volvemos a explorar
        for dir_idx, dist_idx in [(ac.NEIGHBORHOOD_UP, ac.NEIGHBORHOOD_DIST_UP), (ac.NEIGHBORHOOD_DOWN, ac.NEIGHBORHOOD_DIST_DOWN),
                                  (ac.NEIGHBORHOOD_LEFT, ac.NEIGHBORHOOD_DIST_LEFT), (ac.NEIGHBORHOOD_RIGHT, ac.NEIGHBORHOOD_DIST_RIGHT)]:
            if perception[dir_idx] == ac.SHELL and perception[dist_idx] < 5.0: return self.id
        return "Exploracion"

    def _can_move(self, action, perception):
        # Simplificación de colisiones (solo muros duros a menos de 0.6)
        # Usamos los mismos índices de neighborhood para ahorrar código
        idx = {ac.MOVE_UP: ac.NEIGHBORHOOD_UP, ac.MOVE_DOWN: ac.NEIGHBORHOOD_DOWN,
               ac.MOVE_LEFT: ac.NEIGHBORHOOD_LEFT, ac.MOVE_RIGHT: ac.NEIGHBORHOOD_RIGHT}[action]
        dist_idx = {ac.MOVE_UP: ac.NEIGHBORHOOD_DIST_UP, ac.MOVE_DOWN: ac.NEIGHBORHOOD_DIST_DOWN,
                    ac.MOVE_LEFT: ac.NEIGHBORHOOD_DIST_LEFT, ac.MOVE_RIGHT: ac.NEIGHBORHOOD_DIST_RIGHT}[action]
        
        return not (perception[idx] in [ac.UNBREAKABLE, ac.BRICK] and perception[dist_idx] < 0.6)
    