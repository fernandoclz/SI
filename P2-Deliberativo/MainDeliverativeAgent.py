import sys
sys.path.insert(0,"./LGym")
sys.path.insert(0,"./Agent")
sys.path.insert(0,"./Deliverative")
from LGym.LGymClient import agentLoop
from Agent.BaseAgent import BaseAgent
from Deliverative.GoalOrientedAgent import GoalOrientedAgent


agent = GoalOrientedAgent("1","Isma")
agentLoop(agent,True)

 