import copy
import json
import os
import random

from custom_types.meal_component import MealComponent
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

def meal_planner(recipes_needed: int) -> None:
    recipes = load_recipes()
    main_recipes = []
    carb_recipes = []
    vegetable_recipes = []
    for recipe in recipes:
        if MealComponent("meat") in recipe.meal_components:
            main_recipes.append(recipe)
        elif MealComponent("carb") in recipe.meal_components:
            carb_recipes.append(recipe)
        elif MealComponent("vegetable") in recipe.meal_components:
            vegetable_recipes.append(recipe)

    random.shuffle(main_recipes)
    random.shuffle(carb_recipes)
    random.shuffle(vegetable_recipes)

    print(f"Loaded {len(main_recipes)} main and {len(recipes)} total recipes.")

    if len(main_recipes) < recipes_needed:
        print(f"Not enough main recipes available. Found {len(main_recipes)}, but needed {recipes_needed}.")
        return
    
    chosen_mains = main_recipes[:recipes_needed]
    
    all_recipes = copy.deepcopy(chosen_mains) 
    print("Selected recipes:")
    for recipe in chosen_mains:
        side_recipes = []
        if MealComponent("carb") not in recipe.meal_components:
            carb_recipe = random.choice(carb_recipes)
            side_recipes.append(carb_recipe)
        if MealComponent("vegetable") not in recipe.meal_components:
            vegetable_recipe = vegetable_recipes.pop()
            side_recipes.append(vegetable_recipe)
        output = f"- {recipe.name}"
        if side_recipes:
            output += f" with {', '.join(r.name for r in side_recipes)}"
        print(output)
        all_recipes.extend(side_recipes)
    
    necessary_ingredients = {}
    for recipe in all_recipes:
        for ingredient in recipe.ingredients:
            if ingredient.name not in necessary_ingredients:
                necessary_ingredients[ingredient.name] = {"amount": 0, "unit": ingredient.unit}

            if ingredient.unit != necessary_ingredients[ingredient.name]["unit"]:
                print(f"Warning: Ingredient '{ingredient.name}' has mixed units ({ingredient.unit} vs {necessary_ingredients[ingredient.name]['unit']}).")
            else:
                necessary_ingredients[ingredient.name]["amount"] += ingredient.amount
    
    print("\nNecessary ingredients for the selected recipes:")
    sorted_keys = sorted(necessary_ingredients.keys())
    for ingredient_name in sorted_keys:
        details = necessary_ingredients[ingredient_name]
        print(f"- {ingredient_name}: {details['amount']} {details['unit']}")

    
if __name__ == "__main__":
    print("Welcome to the Meal Planner!")
    num_recipes = int(input("How many recipes do you want to plan? "))
    meal_planner(num_recipes)