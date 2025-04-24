import enum

class MealComponent(enum.Enum):
    """
    Enum representing the different components of a meal.
    """
    MEAT = "meat"
    VEGETABLE = "vegetable"
    CARB = "carb"