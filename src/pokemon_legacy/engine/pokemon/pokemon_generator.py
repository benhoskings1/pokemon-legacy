from pokemon_legacy.engine.pokemon.pokemon import Pokemon
from pokemon_legacy.engine.general.Animations import createAnimation


class PokemonGenerator:
    def __init__(self):
        self.animations = {}

    def generate_pokemon(
            self,
            pokemon_name: str,
            **kwargs
    ):
        pk_animations = self.animations.get(pokemon_name)
        if pk_animations is None:
            pk_animations = createAnimation(pokemon_name)
            self.animations[pokemon_name] = pk_animations

        return Pokemon(pokemon_name, animations=pk_animations, **kwargs)