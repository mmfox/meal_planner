from collections import defaultdict

import copy
import json
import os
import questionary
import random

from custom_types.cooking_time_constraint import CookingTimeConstraint
from custom_types.meal_component import MealComponent
from custom_types.recipe import Recipe

RECIPE_DIR = 'recipes'
ORDERED_DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]

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

def meal_planner(daily_constraints: dict[str, CookingTimeConstraint]) -> None:

    # Parse recipes and categorize them by cooking time constraints.
    recipes = load_recipes()
    main_recipes_by_time_constraint = defaultdict(list)
    carb_recipes = []
    vegetable_recipes = []
    for recipe in recipes:
        if MealComponent("meat") in recipe.meal_components:
            cooking_time_constraint = CookingTimeConstraint.from_cooking_time(recipe.cooking_time_min)
            main_recipes_by_time_constraint[cooking_time_constraint].append(recipe)
        elif MealComponent("carb") in recipe.meal_components:
            carb_recipes.append(recipe)
        elif MealComponent("vegetable") in recipe.meal_components:
            vegetable_recipes.append(recipe)

    chosen_recipes: dict[str, str] = {}
    days_by_constraint = defaultdict(list)
    for day, constraint in daily_constraints.items():
        if constraint in (CookingTimeConstraint.NO_COOKING, CookingTimeConstraint.LEFTOVER_DAY):
            chosen_recipes[day] = constraint.value
        else:
            days_by_constraint[constraint].append(day)
    

    # Print and shuffle recipes.
    print(f"Loaded {len(recipes)} total recipes.")
    random.shuffle(carb_recipes)
    random.shuffle(vegetable_recipes)


    # Select recipes for each day based on constraints.
    recipes_meeting_constraints = []
    all_recipes = []
    for constraint in CookingTimeConstraint:
        if constraint not in days_by_constraint:
            continue

        recipes_meeting_constraints.extend(main_recipes_by_time_constraint[constraint])
        random.shuffle(recipes_meeting_constraints)
        recipes_needed = len(days_by_constraint[constraint])
        if len(recipes_meeting_constraints) < recipes_needed:
            raise ValueError(f"Not enough recipes available for {constraint.value}. Found {len(recipes_meeting_constraints)}, but needed {recipes_needed}.")

    
        chosen_mains = recipes_meeting_constraints[:recipes_needed]
        recipes_meeting_constraints = recipes_meeting_constraints[recipes_needed:]
        all_recipes.extend(chosen_mains)
        for day in days_by_constraint[constraint]:
            main_recipe = chosen_mains.pop()
            side_recipes = []
            if MealComponent("carb") not in main_recipe.meal_components:
                carb_recipe = random.choice(carb_recipes)
                side_recipes.append(carb_recipe)
            if MealComponent("vegetable") not in main_recipe.meal_components:
                vegetable_recipe = vegetable_recipes.pop()
                side_recipes.append(vegetable_recipe)
            output = f"{main_recipe.name}"
            if side_recipes:
                output += f" with {', '.join(r.name for r in side_recipes)}"
            
            output += f" ({main_recipe.cooking_time_min} min)"
            chosen_recipes[day] = output
            all_recipes.extend(side_recipes)

    # Print selected recipes by day.
    print("\nSelected recipes for the week:")

    for day in ORDERED_DAYS:
        print(f"{day}: {chosen_recipes[day]}")

    # Calculate necessary ingredients and print them. 
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
    daily_constraints = {}
    for day in ORDERED_DAYS:
        choice = questionary.select(
            f"Select cooking availability for {day}:",
            choices=[cooking_time_constraint.value for cooking_time_constraint in CookingTimeConstraint],
        ).ask()
        daily_constraints[day] = CookingTimeConstraint(choice)
    

    meal_planner(daily_constraints)