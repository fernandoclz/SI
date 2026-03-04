### Purpose
This file helps AI coding agents become productive in this repository quickly by describing architecture, key files, run/debug flows, and coding patterns discovered in the codebase.

### Big-picture architecture
- Core agent runtime: `BattleCityReactiveAgentPG/MainReactiveAgent.py` instantiates a `ReactiveAgent` and calls `agentLoop` in `LGym/LGymClient.py`.
- Agent model: `Reactive/ReactiveAgent.py` subclasses `Agent/BaseAgent.py` and composes a `StateMachine` from `StateMachine/StateMachine.py` using `Reactive/States/*` implementations.
- Communication: `LGym/*` implements a simple text protocol over sockets (`LGymConnect.py`) used by `LGymClient.py` to receive perceptions and send actions. The server helper is `LGymServer.py`.
- Utilities: `Utils/Utils.py` contains MLP export helpers (uses `skl2onnx` and `onnx2json`).

### How to run locally (useful commands)
- Start a local LGym server (for testing):

```bash
python3 BattleCityReactiveAgentPG/LGym/LGymServer.py
```

- Run the agent (from repository root):

```bash
python3 BattleCityReactiveAgentPG/MainReactiveAgent.py
```

Notes: the client/server use plain sockets and default port 80. `MainReactiveAgent.py` passes `debug=True` into `agentLoop` showing the LGym exchange logs.

### Protocol & integration patterns (concrete examples)
- LGym messages are key=value pairs joined by `&`. Parsing happens in `LGym/LGymClient.py::_ParseDataToAttributes`.
- Perception messages use `command=perception_map` or `command=perception` and include `parameters` and `map` fields. See `LGym/LGymClient.py::_precessingPerception` and `RecivePerception()` for how the client unpacks them.
- Actions are sent with `SendAction` in `LGym/LGymClient.py` and expect parameter names matching IDs (example call inside `agentLoop` uses `['movement','fire']`). The sent command looks like `command=actions&id=<id>&movement=<val>&fire=<val>`.
- State machine: Each state class in `Reactive/States` implements `Start`, `Update(perception,map,agent)`, `Transit(perception,map)` and optional `End` and `Reset`. `StateMachine.Update` calls `Update` then `Transit`, and handles state transitions.
- Perception indexing: `Reactive/States/AgentConsts.py` defines integer indices for the perception array (e.g., `CAN_FIRE=14`, `TIME=18`). Use these constants rather than magic indices.

### Coding conventions and project-specific patterns
- State classes live under `Reactive/States`. Use the `State` base API (same method names and signatures).
- Agents subclass `Agent/BaseAgent.py` and must implement `Start()`, `Update(perception,map)` -> returns `(action, shot_bool)`, and `End(win)`.
- Keep protocol formatting consistent with the `LGymClient` helpers when creating tests or tools.

### Dependencies and environment notes
- Python 3 required. For full functionality (MLP export) install: `pip install skl2onnx onnx2json`.
- The LGym client/server communicate using hostname and port (defaults in code use `LGymConnect.getHostName()` and port `80`). Adjust network permissions or change port if 80 is restricted.

### Where to look for changes or extensions
- Add new behaviors by creating a new state in `Reactive/States` and registering it in `Reactive/ReactiveAgent.py`'s state dictionary.
- If changing message format, update `LGym/LGymClient.py` parsing and `LGym/LGymServer.py` expected commands.

### Quick troubleshooting tips
- If no perceptions are received, check `LGymConnect` socket setup and buffer sizes (`LGym/LGymConnect.py`).
- To inspect perception contents, `agentLoop` prints the raw message before parsing; enable `debug=True` in `MainReactiveAgent.py`.

### Ask me if unclear
If any protocol fields, state transitions, or run flows are unclear, tell me which file or interaction you'd like expanded and I will update this guidance.
