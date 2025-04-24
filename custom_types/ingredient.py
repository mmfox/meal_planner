from dataclasses import dataclass

@dataclass
class Ingredient:
    name: str
    amount: float
    unit: str

    def __str__(self):
        return f"{self.amount} {self.unit} of {self.name}"
    
    def __repr__(self):
        return f"Ingredient(name={self.name!r}, amount={self.amount!r}, unit={self.unit!r})"

    def to_dict(self):
        return {
            "name": self.name,
            "amount": self.amount,
            "unit": self.unit
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            amount=data["amount"],
            unit=data["unit"]
        )