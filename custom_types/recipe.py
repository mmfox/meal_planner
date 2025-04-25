from dataclasses import dataclass
from typing import Optional

from custom_types.ingredient import Ingredient
from custom_types.meal_component import MealComponent


@dataclass
class Recipe:
    name: str
    ingredients: list[Ingredient]
    cooking_time_min: int
    servings: int
    meal_components: list[MealComponent]
    recipe_link: Optional[str] = None

    def __str__(self):
        ingredients_str = ", ".join(str(ingredient) for ingredient in self.ingredients)
        components_str = ", ".join(
            component.value for component in self.meal_components
        )
        return (
            f"Recipe: {self.name}\n"
            f"Ingredients: {ingredients_str}\n"
            f"Cooking Time: {self.cooking_time_min} minutes\n"
            f"Servings: {self.servings}\n"
            f"Meal Components: {components_str}"
        )

    def to_dict(self):
        return {
            "name": self.name,
            "ingredients": [ingredient.to_dict() for ingredient in self.ingredients],
            "cooking_time_min": self.cooking_time_min,
            "servings": self.servings,
            "meal_components": [component.value for component in self.meal_components],
            "recipe_link": self.recipe_link,
        }

    @classmethod
    def from_dict(cls, data: dict):
        ingredients = [Ingredient.from_dict(ing) for ing in data["ingredients"]]
        meal_components = [
            MealComponent(component) for component in data["meal_components"]
        ]
        return cls(
            name=data["name"],
            ingredients=ingredients,
            cooking_time_min=data["cooking_time_min"],
            servings=data["servings"],
            meal_components=meal_components,
            recipe_link=data.get("recipe_link", None),
        )
