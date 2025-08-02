"""
game_log .py

"""
import os
import datetime
from enum import Enum


class GameEventType(Enum):
    error = -1
    system = 0
    game = 1
    user = 1


class GameEvent:
    def __init__(self, name: str, event_type: GameEventType = GameEventType.system):
        """

        :param name: event name
        """
        self.name: str = name
        self.timestamp: datetime.datetime = datetime.datetime.now()
        self.event_type: GameEventType = event_type

    def __str__(self):
        return f"[{self.event_type.name.upper()}] {self.name} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    def __repr__(self):
        return self.__str__()


class GameLog:
    def __init__(self):
        self.events: list[GameEvent] = []

    def add_event(self, event: GameEvent):
        self.events.append(event)

    def write_log(self, log_dir: str):
        with open(os.path.join(log_dir, f"game_log_{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"), "w") as log:
            for event in self.events:
                log.write(str(event) + "\n")
