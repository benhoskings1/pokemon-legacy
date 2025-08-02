"""
This
"""

import pandas as pd
import pickle
from re import sub

# Define a function to convert a string to snake case
def snake_case(s):
    # Replace hyphens with spaces, then apply regular expression substitutions for title case conversion
    # and add an underscore between words, finally convert the result to lowercase
    return ''.join(
        sub('([A-Z][a-z]+)', r' \1',
        sub('([A-Z]+)', r' \1',
        s.replace('-', ' '))).split()
    ).lower()


class PokedexWriter:
    def __init__(self):
        """
        This class creates a new pokedex file as a json.
        """

        with open('pokedex/LocalDex/LocalDex.pickle', 'rb') as file:
            self.existing_data: pd.DataFrame = pickle.load(file)


    def write_pokedex(self, path, file_format="json"):
        self.existing_data.columns = [snake_case(col_name) for col_name in self.existing_data.columns]
        self.existing_data.reset_index().rename(columns={"index":"name"}).to_json(path, orient='records', indent=4)


if __name__ == "__main__":
    pokedexWriter = PokedexWriter()
    pokedexWriter.write_pokedex("pokedex/sinnoh.json")