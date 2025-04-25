import json
import os
import random
from collections import defaultdict
from typing import cast

import questionary

from custom_types.cooking_time_constraint import CookingTimeConstraint
from custom_types.day_plan import DayPlan
from custom_types.meal_component import MealComponent
from custom_types.recipe import Recipe

RECIPE_DIR = "recipes"
ORDERED_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def load_recipes() -> list[Recipe]:
    recipes: list[Recipe] = []
    if not os.path.exists(RECIPE_DIR):
        print(f"Recipe directory '{RECIPE_DIR}' does not exist.")
        return recipes

    for filename in os.listdir(RECIPE_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(RECIPE_DIR, filename)
            with open(filepath, "r") as file:
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
            cooking_time_constraint = CookingTimeConstraint.from_cooking_time(
                recipe.cooking_time_min
            )
            main_recipes_by_time_constraint[cooking_time_constraint].append(recipe)
        elif MealComponent("carb") in recipe.meal_components:
            carb_recipes.append(recipe)
        elif MealComponent("vegetable") in recipe.meal_components:
            vegetable_recipes.append(recipe)

    day_plans: dict[str, DayPlan] = {}
    days_by_constraint = defaultdict(list)
    for day, constraint in daily_constraints.items():
        if constraint in (
            CookingTimeConstraint.NO_COOKING,
            CookingTimeConstraint.LEFTOVER_DAY,
        ):
            day_plans[day] = DayPlan(constraint.value, [])
        else:
            days_by_constraint[constraint].append(day)

    # Print and shuffle recipes.
    print(f"Loaded {len(recipes)} total recipes.")
    random.shuffle(carb_recipes)
    random.shuffle(vegetable_recipes)

    # Select recipes for each day based on constraints.
    recipes_meeting_constraints = []
    should_replan = True
    main_recipes_to_avoid: list[Recipe] = []
    while should_replan:
        should_replan = False
        for constraint in CookingTimeConstraint:
            if constraint not in days_by_constraint:
                continue

            recipes_meeting_constraints.extend(
                [
                    r
                    for r in main_recipes_by_time_constraint[constraint]
                    if r not in main_recipes_to_avoid
                ]
            )
            random.shuffle(recipes_meeting_constraints)
            recipes_needed = len(days_by_constraint[constraint])
            if len(recipes_meeting_constraints) < recipes_needed:
                raise ValueError(
                    f"Not enough recipes available for {constraint.value}. Found {len(recipes_meeting_constraints)}, but needed {recipes_needed}."
                )

            chosen_mains = recipes_meeting_constraints[:recipes_needed]
            recipes_meeting_constraints = recipes_meeting_constraints[recipes_needed:]
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
                day_plans[day] = DayPlan(output, [main_recipe] + side_recipes)

        # Print selected recipes by day.
        print("\nSelected recipes for the week:")

        for day in ORDERED_DAYS:
            print(f"{day}: {day_plans[day].description}")

        replan_days = questionary.checkbox(
            "Choose any days that you want to replan with different recipes.",
            choices=[day for day in ORDERED_DAYS if day_plans[day].recipes],
        ).ask()
        if replan_days:
            should_replan = True
            main_recipes_to_avoid = []
            for day_plan in day_plans.values():
                for recipe in day_plan.recipes:
                    if MealComponent.MEAT in recipe.meal_components:
                        main_recipes_to_avoid.append(recipe)
                    elif MealComponent.VEGETABLE in recipe.meal_components:
                        vegetable_recipes.append(recipe)

            random.shuffle(vegetable_recipes)
            days_by_constraint = defaultdict(list)
            for day in replan_days:
                constraint = daily_constraints[day]
                if constraint not in (
                    CookingTimeConstraint.NO_COOKING,
                    CookingTimeConstraint.LEFTOVER_DAY,
                ):
                    days_by_constraint[constraint].append(day)

    # Calculate necessary ingredients and print them.
    all_recipes = []
    for day_plan in day_plans.values():
        all_recipes.extend(day_plan.recipes)

    necessary_ingredients = {}
    for recipe in all_recipes:
        for ingredient in recipe.ingredients:
            if ingredient.name not in necessary_ingredients:
                necessary_ingredients[ingredient.name] = {
                    "amount": 0,
                    "unit": ingredient.unit,
                }

            if ingredient.unit != necessary_ingredients[ingredient.name]["unit"]:
                print(
                    f"Warning: Ingredient '{ingredient.name}' has mixed units ({ingredient.unit} vs {necessary_ingredients[ingredient.name]['unit']})."
                )
            else:
                necessary_ingredients[ingredient.name]["amount"] = (
                    cast(float, necessary_ingredients[ingredient.name]["amount"])
                    + ingredient.amount
                )

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
            choices=[
                cooking_time_constraint.value
                for cooking_time_constraint in CookingTimeConstraint
            ],
        ).ask()
        daily_constraints[day] = CookingTimeConstraint(choice)

    meal_planner(daily_constraints)
