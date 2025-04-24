import json
import os

from custom_types.recipe import Recipe

RECIPE_DIR = 'recipes'

def load_recipes() -> list[Recipe]:
    recipes = []
    if not os.path.exists(RECIPE_DIR):
        print(f"Recipe directory '{RECIPE_DIR}' does not exist.")
        return recipes

    for filename in os.listdir(RECIPE_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(RECIPE_DIR, filename)
            with open(filepath, 'r') as file:
                try:
                    recipe_dict = json.load(file)
                    recipes.append(Recipe.from_dict(recipe_dict))
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from {filename}")
    return recipes

def meal_planner():
    print("Welcome to the Meal Planner!")
    recipes = load_recipes()
    breakpoint()
    print(f"Loaded {len(recipes)} recipes.")
    

    
if __name__ == "__main__":
    meal_planner()