from enum import Enum
import networkx as nx
from statemachine import StateMachine, State


class GameState(Enum):
    no_objective = 100
    new_game = 1
    meeting_mum = 2
    mum_warning = 3
    meeting_rival = 4
    following_rival = 5
    going_to_lake_verity = 6
    going_to_sandgem_town = 7

    def __gt__(self, other):
        return self.value > other.value
    def __lt__(self, other):
        return self.value < other.value
    def __ge__(self, other):
        return self.value >= other.value
    def __le__(self, other):
        return self.value <= other.value
    def __eq__(self, other):
        return self.value == other.value

    __hash__ = Enum.__hash__

def build_game_state_machine(initial: GameState = GameState.new_game) -> StateMachine:
    graph = nx.DiGraph()

    valid_states = [s for s in GameState if s.value >= initial.value]

    graph.add_nodes_from([s for s in valid_states])

    # Add transitions only if both ends are in valid_states
    def add_valid_edge(a, b):
        if a in valid_states and b in valid_states:
            graph.add_edge(a, b)

    add_valid_edge(GameState.new_game, GameState.meeting_mum)
    add_valid_edge(GameState.meeting_mum, GameState.mum_warning)
    add_valid_edge(GameState.mum_warning, GameState.meeting_rival)
    add_valid_edge(GameState.meeting_rival, GameState.following_rival)
    add_valid_edge(GameState.following_rival, GameState.going_to_lake_verity)
    add_valid_edge(GameState.going_to_lake_verity, GameState.going_to_sandgem_town)
    add_valid_edge(GameState.going_to_sandgem_town, GameState.no_objective)

    # Create State objects
    state_objs = {
        s: State(
            name=s.name,
            value=s,
            initial=s == initial,
            final=s == GameState.no_objective
        ) for s in graph.nodes
    }

    attrs = {"strict_states": False}

    # Add state definitions as class attributes
    for s, obj in state_objs.items():
        attrs[s.name] = obj

    # Add transitions
    for src, dst in graph.edges:
        trans_name = f"{src.name}_to_{dst.name}"
        attrs[trans_name] = state_objs[src].to(state_objs[dst])

    # Create the new Machine class
    Machine = type("GameStateMachine", (StateMachine,), attrs)

    # Instantiate and return
    return Machine()


# Example usage:
if __name__ == "__main__":

    sm = build_game_state_machine(initial=GameState.new_game)

    print(type(sm))
    print("Initial state:", sm.current_state.id)

    sm.new_game_to_meeting_mum()
    print("After transition:", type(sm.current_state_value))
