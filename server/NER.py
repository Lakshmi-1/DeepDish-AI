import spacy
from spacy.pipeline import EntityRuler
import inflect
from rag import graph

def build_patterns():
    ingredients_query = """
    MATCH (i:Ingredient)
    RETURN i.name AS name
    """
    records = graph.query(ingredients_query)
    ingredients = [record['name'].lower() for record in records]
    
    cuisine_query = """
    MATCH (i:Cuisine)
    RETURN i.value AS value
    """
    records = graph.query(cuisine_query)
    origins = [record['value'].lower() for record in records]
    
    nlp = spacy.load("en_core_web_sm")
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    
    patterns = [
        {"label": "RATING_VALUE", "pattern": [{"LIKE_NUM": True}, {"LOWER": "stars"}]},
        {"label": "RATING_VALUE", "pattern": [{"LIKE_NUM": True}, {"LOWER": "star"}]},
        {"label": "RATING_VALUE", "pattern": [{"LIKE_NUM": True}, {"TEXT": "★"}]},

        {"label": "DIET_LABEL", "pattern": [{"LOWER": "healthy"}]},
        {"label": "DIET_LABEL", "pattern": [{"LOWER": "vegan"}]},
        {"label": "DIET_LABEL", "pattern": [{"LOWER": "vegetarian"}]},
    ]
    for origin in origins:
        patterns.append({"label": "CUISINE", "pattern": [{"LOWER": f"{origin}"}]})
    for ingredient in ingredients:
        patterns.append({"label": "INGREDIENT", "pattern": [{"LOWER": f"{ingredient}"}]})
    ruler.add_patterns(patterns)
    return nlp


def extract_recipe_criteria(doc):
    cuisine = None
    ingredients = []
    max_time = None
    healthy = None
    
    m = inflect.engine()

    # check entities
    for ent in doc.ents:
        if ent.label_ == "TIME":
            if "minute" in ent.text:
                max_time = int(''.join(filter(str.isdigit, ent.text)))
        elif ent.label_ == "CUISINE":
            cuisine = ent.text.capitalize()
        elif ent.label_ == "INGREDIENT":
            ingredients.append(ent.lemma_)
            ingredients.append(m.plural(ent.lemma_))
        elif ent.label_ == "DIET_LABEL":
            diet = ent.text.capitalize()

    return {
        "cuisine": cuisine,
        "ingredients": ingredients,
        "max_time": max_time,
        "healthy": healthy,
    }
    
    
"""
def extract_restaurant_criteria(doc):
    diet = None
    cuisine = None
    rating = None
    max_time = None

    # check for time
    for ent in doc.ents:
        if ent.label_ == "TIME":
            if "minute" in ent.text:
                max_time = int(''.join(filter(str.isdigit, ent.text)))
        elif ent.label_ == "CUISINE":
            cuisine = ent.text.capitalize()
        elif ent.label_ == "RATING_VALUE":
            rating = int(''.join(filter(str.isdigit, ent.text)))
        elif ent.label_ == "DIET_LABEL":
            diet = ent.text.capitalize()

    return {
        "diet": diet,
        "cuisine": cuisine,
        "rating": rating,
        "max_time": max_time
    }


def generate_cypher_query(criteria, query="recipe"):
    if query == "restaurant":
        cypher = "MATCH (r:Restaurant)"
        filters = []

        if cuisine := criteria.get("cuisine"):
            filters.append(f'r.cuisine = "{cuisine}"')

        if rating := criteria.get("rating_threshold"):
            filters.append(f"r.rating >= {rating}")

        if time := criteria.get("max_time"):
            filters.append(f"r.time <= {time}")

        if filters:
            cypher += " WHERE " + " AND ".join(filters)

        cypher += " RETURN r.name AS RestaurantName"

    elif query == "recipe":
        cypher = "MATCH (r:Recipe)"
        filters = []

        if cuisine := criteria.get("cuisine"):
            filters.append(f'r.cuisine = "{cuisine}"')

        if diet := criteria.get("diet"):
            filters.append(f'r.diet = "{diet}"')

        if ingredients := criteria.get("ingredients"):
            for ingredient in ingredients:
                filters.append(f'"{ingredient}" IN i.ingredients')

        if cook_time := criteria.get("cook_time"):
            filters.append(f"r.cook_time <= {cook_time}")

        if health := criteria.get("health_score"):
            filters.append(f"r.health_score >= {health}")

        if filters:
            cypher += " WHERE " + " AND ".join(filters)

        cypher += " RETURN r.name AS RecipeName"

    else:
        raise ValueError("Invalid query type: must be 'restaurant' or 'recipe'")

    return cypher

text = "Show me a recipe for a healthy Greek dish that I can make within 30 minutes which includes chicken and broccoli"
doc = nlp(text)
#for ent in doc.ents:
#    print(f"{ent.text} , {ent.label_}")
x = extract_recipe_criteria(doc)
z = generate_cypher_query(x, "recipe")
print(text)
print(x)
print(z)
"""