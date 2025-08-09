import json
import os
import random
from collections import defaultdict
from typing import cast, Optional

import click
import questionary
from rapidfuzz import process

from custom_types.cooking_time_constraint import CookingTimeConstraint
from custom_types.day_plan import DayPlan
from custom_types.ingredient import Ingredient
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


def combine_recipe_names(main_recipe: Recipe, side_recipes: list[Recipe]) -> str:
    output = f"{main_recipe.name}"
    if side_recipes:
        output += f" with {', '.join(r.name for r in side_recipes)}"

    output += f" ({main_recipe.cooking_time_min} min)"
    return output


def print_week_plan(day_plans: dict[str, DayPlan]) -> None:
    # Print selected recipes by day.
    print("\nSelected recipes for the week:")

    for day in ORDERED_DAYS:
        print(f"{day}: {day_plans[day].description}")


def meal_planner(daily_constraints: dict[str, CookingTimeConstraint]) -> None:
    # Parse recipes and categorize them by cooking time constraints.
    recipes = load_recipes()
    main_recipes_by_time_constraint = defaultdict(list)
    main_recipes = []
    carb_recipes = []
    vegetable_recipes = []
    for recipe in recipes:
        if MealComponent("meat") in recipe.meal_components:
            main_recipes.append(recipe)
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
            recipes_meeting_constraints.extend(
                [
                    r
                    for r in main_recipes_by_time_constraint[constraint]
                    if r not in main_recipes_to_avoid
                ]
            )

            if constraint not in days_by_constraint:
                continue

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

                day_plans[day] = DayPlan(combine_recipe_names(main_recipe, side_recipes), [main_recipe] + side_recipes)

        print_week_plan(day_plans)

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

    # Allow for any manual overrides
    manual_days = questionary.checkbox(
        "Do you want to manually choose a recipe for any days?",
        choices=[
            questionary.Choice(day, day)
            for day in ORDERED_DAYS
            if day_plans[day].recipes
        ],
    ).ask()

    for day in manual_days:
        main_recipe = questionary.select(
           f"On {day}, which main dish would you like?",
           choices=[
               questionary.Choice(main_recipe.name, main_recipe)
               for main_recipe in main_recipes 
           ],
        ).ask()
        side_recipes = []

        if MealComponent("carb") not in main_recipe.meal_components:
            carb_recipe = questionary.select(
               f"On {day}, which carb would you like?",
               choices=[
                   questionary.Choice(carb_recipe.name, carb_recipe)
                   for carb_recipe in carb_recipes 
               ],
            ).ask()
            side_recipes.append(carb_recipe)
        if MealComponent("vegetable") not in main_recipe.meal_components:
            veg_recipe = questionary.select(
               f"On {day}, which vegetable would you like?",
               choices=[
                   questionary.Choice(veg_recipe.name, veg_recipe)
                   for veg_recipe in vegetable_recipes 
               ],
            ).ask()
            side_recipes.append(veg_recipe)

        day_plans[day] = DayPlan(combine_recipe_names(main_recipe, side_recipes), [main_recipe] + side_recipes)


    # Check if we want to scale any recipes.
    scale_factors = {}
    scale_days = questionary.checkbox(
        "Do you want to scale any recipes? Select the days you want to scale.",
        choices=[
            questionary.Choice(day, day)
            for day in ORDERED_DAYS
            if day_plans[day].recipes
        ],
    ).ask()
    if scale_days:
        for day in scale_days:
            scale_factor = questionary.text(
                f"Enter scale factor for {day}:",
            ).ask()
            try:
                scale_factors[day] = float(scale_factor)
            except ValueError:
                print(f"Invalid scale factor '{scale_factor}' for {day}. Using 1.")
                scale_factors[day] = 1.0

    # Calculate necessary ingredients and print them.
    necessary_ingredients = {}
    for day, day_plan in day_plans.items():
        scale_factor = scale_factors.get(day, 1.0)
        for recipe in day_plan.recipes:
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
                        + ingredient.amount * scale_factor
                    )

    print_week_plan(day_plans)

    print("\nNecessary ingredients for the selected recipes:")
    sorted_keys = sorted(necessary_ingredients.keys())
    for ingredient_name in sorted_keys:
        details = necessary_ingredients[ingredient_name]
        print(f"- {ingredient_name}: {details['amount']} {details['unit']}")


def find_ingredient_match(
    new_ingredient_name: str, known_ingredient_names: list[str], threshold=80
) -> Optional[str]:
    match = process.extractOne(
        new_ingredient_name, known_ingredient_names, score_cutoff=threshold
    )
    if match:
        return match[0]  # return the matched ingredient
    return None


@click.group()
def cli():
    """Meal Planner CLI."""
    pass


@cli.command()
def run():
    """Run the meal planner."""
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


@cli.command()
def list_recipes():
    """List all available recipes."""
    recipes = load_recipes()
    if not recipes:
        print("No recipes found.")
        return

    print("Available recipes:")
    for recipe in recipes:
        print(f"- {recipe.name} ({recipe.cooking_time_min} min)")


@cli.command()
def add_recipe():
    """Add a new recipe."""
    recipes = load_recipes()
    known_ingredient_units = {}
    for recipe in recipes:
        for ingredient in recipe.ingredients:
            if ingredient.name not in known_ingredient_units:
                known_ingredient_units[ingredient.name] = ingredient.unit
    known_ingredient_names = list(known_ingredient_units.keys())

    name = questionary.text("Enter recipe name:").ask()
    cooking_time_min = questionary.text(
        "Enter cooking time in minutes:", default="30"
    ).ask()
    servings = questionary.text("Enter number of servings:", default="4").ask()
    recipe_link = questionary.text("Enter recipe link, if relevant:").ask()

    ingredients = []
    while True:
        # Add ingredients, one at a time.  Allow entering no name as a way to finish.
        ingredient_name = questionary.text(
            "Enter ingredient name (or nothing to complete ingredient setup):",
        ).ask()
        if ingredient_name == "":
            break

        potential_ingredient_match = find_ingredient_match(
            ingredient_name,
            known_ingredient_names,
        )
        if potential_ingredient_match:
            use_existing = questionary.confirm(
                f"Found existing ingredient '{potential_ingredient_match}'. Use it instead of creating a new one?"
            ).ask()
            if use_existing:
                ingredient_name = potential_ingredient_match

        # TODO: sanitize and look for pre-existing ingredients as a match
        ingredient_units = questionary.text(
            "Enter ingredient units, pluralized:",
            default=known_ingredient_units.get(ingredient_name, ""),
        ).ask()
        ingredient_amount = questionary.text(
            "Enter ingredient amount:",
        ).ask()
        ingredients.append(
            Ingredient(
                ingredient_name.strip(),
                float(ingredient_amount),
                ingredient_units.strip(),
            )
        )

    meal_components = questionary.checkbox(
        "Select meal components:",
        choices=[component.value for component in MealComponent],
    ).ask()

    recipe = Recipe(
        name=name,
        ingredients=ingredients,
        cooking_time_min=int(cooking_time_min),
        servings=int(servings),
        meal_components=[MealComponent(component) for component in meal_components],
        recipe_link=recipe_link if recipe_link else None,
    )

    if not os.path.exists(RECIPE_DIR):
        os.makedirs(RECIPE_DIR)

    filename = "_".join(name.lower().split())
    filepath = os.path.join(RECIPE_DIR, f"{filename}.json")
    with open(filepath, "w") as file:
        json.dump(recipe.to_dict(), file, indent=4)

    print(f"Recipe '{name}' added successfully.")


if __name__ == "__main__":
    print("Welcome to the Meal Planner CLI!")
    cli()
