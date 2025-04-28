import spacy
from spacy.pipeline import EntityRuler
import inflect
from rag import graph

def build_patterns():
    m = inflect.engine()
    
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
    
    category_query = """
    MATCH (i:Category)
    RETURN i.value AS value
    """
    records = graph.query(category_query)
    categories = [record['value'].lower() for record in records]
    
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
        if(not m.singular_noun(ingredient)):
            patterns.append({"label": "INGREDIENT", "pattern": [{"LOWER": f"{ingredient}"}]})
            patterns.append({"label": "INGREDIENT", "pattern": [{"LOWER": f"{m.plural(ingredient)}"}]})
        else:
            patterns.append({"label": "INGREDIENT", "pattern": [{"LOWER": f"{m.singular_noun(ingredient)}"}]})
            patterns.append({"label": "INGREDIENT", "pattern": [{"LOWER": f"{ingredient}"}]})
            
    for category in categories:
        if(not m.singular_noun(category)):
            patterns.append({"label": "CATEGORY", "pattern": [{"LOWER": f"{category}"}]})
            patterns.append({"label": "CATEGORY", "pattern": [{"LOWER": f"{m.plural(category)}"}]})
        else:
            patterns.append({"label": "CATEGORY", "pattern": [{"LOWER": f"{m.singular_noun(category)}"}]})
            patterns.append({"label": "CATEGORY", "pattern": [{"LOWER": f"{category}"}]})

            
        
        
    ruler.add_patterns(patterns)
    return nlp


def extract_recipe_criteria(doc):
    cuisine = []
def extract_recipe_criteria(doc, allergies):
    cuisine = None
    ingredients = []
    category = []
    m = inflect.engine()

    # check entities
    for ent in doc.ents:
        if ent.label_ == "CUISINE":
            cuisine.append(ent.text.capitalize())
        elif ent.label_ == "INGREDIENT":
            ingredients.append(ent.lemma_)
            ingredients.append(m.plural(ent.lemma_))
        elif ent.label_ == "DIET_LABEL":
            diet = ent.text.capitalize()
        elif ent.label_ == "CATEGORY":
            category.append(ent.lemma_)
            category.append(m.plural(ent.lemma_))

    return {
        "category": category,
        "cuisine": cuisine,
        "ingredients": ingredients,
        "allergies": allergies
    }