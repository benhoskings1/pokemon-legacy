from pokemon_legacy.engine.general.storage_system.storage_system_containers import StorageBox

class StorageSystem:
    def __init__(self):
        self.boxes = {
            StorageBox(idx) for idx in range(1, 19)
        }