"""Heuristic nutrition lookup; extend _KNOWN or plug USDA/Nutritionix for production."""

from dataclasses import dataclass


@dataclass
class NutritionFacts:
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


# Per typical serving unless quantity applied elsewhere (rough averages).
_KNOWN: dict[str, NutritionFacts] = {
    "default": NutritionFacts(200, 10, 25, 8),
    "egg": NutritionFacts(78, 6, 0.6, 5.3),
    "boiled egg": NutritionFacts(78, 6, 0.6, 5.3),
    "eggs": NutritionFacts(78, 6, 0.6, 5.3),
    "scrambled egg": NutritionFacts(90, 6.5, 1, 6.5),
    "black coffee": NutritionFacts(2, 0, 0, 0),
    "coffee": NutritionFacts(5, 0, 1, 0),
    "latte": NutritionFacts(190, 13, 19, 6),
    "cappuccino": NutritionFacts(120, 8, 10, 4),
    "banana": NutritionFacts(105, 1.3, 27, 0.3),
    "apple": NutritionFacts(95, 0.5, 25, 0.3),
    "orange": NutritionFacts(62, 1.2, 15, 0.2),
    "milk": NutritionFacts(150, 8, 12, 8),
    "oat milk": NutritionFacts(120, 3, 16, 5),
    "protein shake": NutritionFacts(140, 24, 8, 3),
    "poha": NutritionFacts(250, 6, 45, 5),
    "rice": NutritionFacts(205, 4.3, 45, 0.4),
    "brown rice": NutritionFacts(216, 5, 45, 1.8),
    "bread": NutritionFacts(80, 3, 15, 1),
    "toast": NutritionFacts(75, 2.5, 14, 1),
    "butter": NutritionFacts(100, 0.1, 0, 11),
    "cheese": NutritionFacts(110, 7, 1, 9),
    "yogurt": NutritionFacts(100, 17, 6, 0.7),
    "greek yogurt": NutritionFacts(100, 17, 6, 0.5),
    "chicken": NutritionFacts(231, 43, 0, 5),
    "grilled chicken": NutritionFacts(200, 38, 0, 4.5),
    "salmon": NutritionFacts(206, 22, 0, 13),
    "fish": NutritionFacts(180, 28, 0, 6),
    "tuna": NutritionFacts(180, 39, 0, 1.3),
    "beef": NutritionFacts(250, 26, 0, 15),
    "steak": NutritionFacts(280, 30, 0, 18),
    "pork": NutritionFacts(240, 27, 0, 14),
    "turkey": NutritionFacts(180, 30, 0, 4),
    "bacon": NutritionFacts(42, 3, 0.1, 3.3),
    "sausage": NutritionFacts(280, 12, 1, 25),
    "pizza": NutritionFacts(285, 12, 36, 10),
    "burger": NutritionFacts(540, 25, 40, 30),
    "sandwich": NutritionFacts(350, 20, 35, 14),
    "pasta": NutritionFacts(220, 8, 43, 1.3),
    "noodles": NutritionFacts(200, 7, 38, 2),
    "ramen": NutritionFacts(380, 10, 52, 14),
    "salad": NutritionFacts(120, 8, 10, 6),
    "soup": NutritionFacts(120, 8, 12, 4),
    "potato": NutritionFacts(160, 4.3, 37, 0.2),
    "fries": NutritionFacts(365, 4, 63, 17),
    "chips": NutritionFacts(150, 2, 15, 9),
    "chocolate": NutritionFacts(230, 2, 25, 13),
    "cookie": NutritionFacts(140, 1.5, 19, 7),
    "ice cream": NutritionFacts(210, 3.5, 24, 11),
    "honey": NutritionFacts(60, 0, 17, 0),
    "peanut butter": NutritionFacts(190, 8, 6, 16),
    "almonds": NutritionFacts(164, 6, 6, 14),
    "nuts": NutritionFacts(170, 5, 6, 15),
    "avocado": NutritionFacts(240, 3, 12, 22),
    "tomato": NutritionFacts(22, 1.1, 4.8, 0.3),
    "cucumber": NutritionFacts(8, 0.3, 1.9, 0.1),
    "carrot": NutritionFacts(25, 0.6, 6, 0.1),
    "broccoli": NutritionFacts(55, 3.7, 11, 0.6),
    "spinach": NutritionFacts(7, 0.9, 1.1, 0.1),
    "lentils": NutritionFacts(230, 18, 40, 0.8),
    "beans": NutritionFacts(240, 16, 44, 0.8),
    "chickpea": NutritionFacts(180, 10, 30, 3),
    "quinoa": NutritionFacts(222, 8, 39, 3.6),
    "oatmeal": NutritionFacts(150, 5, 27, 3),
    "cereal": NutritionFacts(150, 3, 33, 1.5),
    "waffle": NutritionFacts(220, 5, 28, 10),
    "pancake": NutritionFacts(175, 5, 30, 4),
    "dosa": NutritionFacts(250, 6, 38, 8),
    "idli": NutritionFacts(150, 4, 28, 2),
    "sambar": NutritionFacts(120, 6, 18, 2),
    "dal": NutritionFacts(200, 12, 28, 4),
    "roti": NutritionFacts(120, 4, 18, 3.5),
    "naan": NutritionFacts(320, 9, 50, 8),
    "biryani": NutritionFacts(480, 18, 65, 16),
    "sushi": NutritionFacts(300, 12, 45, 8),
    "burrito": NutritionFacts(500, 20, 60, 20),
    "taco": NutritionFacts(180, 12, 15, 8),
    "wine": NutritionFacts(125, 0.1, 4, 0),
    "beer": NutritionFacts(150, 1, 13, 0),
    "juice": NutritionFacts(110, 0.5, 26, 0.2),
    "soda": NutritionFacts(140, 0, 39, 0),
    "water": NutritionFacts(0, 0, 0, 0),
}


def lookup_food(name: str, quantity: float = 1.0, unit: str = "serving") -> NutritionFacts:
    key = name.strip().lower()
    for token in sorted(_KNOWN.keys(), key=len, reverse=True):
        if token != "default" and token in key:
            base = _KNOWN[token]
            return NutritionFacts(
                calories=round(base.calories * quantity, 1),
                protein_g=round(base.protein_g * quantity, 1),
                carbs_g=round(base.carbs_g * quantity, 1),
                fat_g=round(base.fat_g * quantity, 1),
            )
    base = _KNOWN["default"]
    q = quantity if quantity > 0 else 1.0
    return NutritionFacts(
        calories=round(base.calories * q, 1),
        protein_g=round(base.protein_g * q, 1),
        carbs_g=round(base.carbs_g * q, 1),
        fat_g=round(base.fat_g * q, 1),
    )


def sum_totals(facts_list: list[NutritionFacts]) -> NutritionFacts:
    c = p = cb = f = 0.0
    for n in facts_list:
        c += n.calories
        p += n.protein_g
        cb += n.carbs_g
        f += n.fat_g
    return NutritionFacts(round(c, 1), round(p, 1), round(cb, 1), round(f, 1))
