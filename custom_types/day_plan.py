from dataclasses import dataclass

from custom_types.recipe import Recipe


@dataclass
class DayPlan:
    description: str
    recipes: list[Recipe]
