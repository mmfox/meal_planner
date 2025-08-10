from dataclasses import dataclass

from custom_types.recipe import Recipe


@dataclass
class DayPlan:
    description: str
    cooking_time_min: int
    recipes: list[Recipe]
