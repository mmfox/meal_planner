import enum

class CookingTimeConstraint(enum.Enum):
    """
    Enum representing the types of cooking time constraints.
    """
    NO_COOKING = "No cooking"
    QUICK_MEAL = "Quick meal (30 min)"
    NORMAL_MEAL = "Normal meal (1 hour)"
    EXTENDED_MEAL = "Extended meal (2+ hours)"
    LEFTOVER_DAY = "Leftover day"

    def __str__(self):
        return self.value

    @classmethod
    def from_cooking_time(cls, cooking_time: int) -> 'CookingTimeConstraint':
        """
        Convert a cooking time in minutes to a CookingTimeConstraint.
        """
        if cooking_time == 0:
            return cls.NO_COOKING
        elif cooking_time <= 30:
            return cls.QUICK_MEAL
        elif cooking_time <= 60:
            return cls.NORMAL_MEAL
        else:
            return cls.EXTENDED_MEAL