import spacy
from spacy.pipeline import EntityRuler
import inflect
from rag import graph

# This function will run once on app startup to establish entity ruler patterns based on the data from the neo4j knowledge graph
# This ensures that any parameter that is in the knowledge graph will be recognized by the parser
def build_patterns():
    # initialize pluralizer
    m = inflect.engine()
    
    # get list of ingredients from neo4j to store as patterns
    ingredients_query = """
    MATCH (i:Ingredient)
    RETURN i.name AS name
    """
    records = graph.query(ingredients_query)
    ingredients = [record['name'].lower() for record in records]
    
    # get list of cuisines 
    cuisine_query = """
    MATCH (i:Cuisine)
    RETURN i.value AS value
    """
    records = graph.query(cuisine_query)
    origins = [record['value'].lower() for record in records]
    
    # get list of categories 
    category_query = """
    MATCH (i:Category)
    RETURN i.value AS value
    """
    records = graph.query(category_query)
    categories = [record['value'].lower() for record in records]
    
    # load spacy model and create entity ruler
    nlp = spacy.load("en_core_web_sm")
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    
    # establish patterns for ratings/diet
    patterns = [
        {"label": "RATING_VALUE", "pattern": [{"LIKE_NUM": True}, {"LOWER": "stars"}]},
        {"label": "RATING_VALUE", "pattern": [{"LIKE_NUM": True}, {"LOWER": "star"}]},
        {"label": "RATING_VALUE", "pattern": [{"LIKE_NUM": True}, {"TEXT": "★"}]},

        {"label": "DIET_LABEL", "pattern": [{"LOWER": "healthy"}]},
        {"label": "DIET_LABEL", "pattern": [{"LOWER": "vegan"}]},
        {"label": "DIET_LABEL", "pattern": [{"LOWER": "vegetarian"}]},
    ]
    
    # add pattern for every origin in the list from neo4j
    for origin in origins:
        patterns.append({"label": "CUISINE", "pattern": [{"LOWER": f"{origin}"}]})
    
    # add pattern for ingredients
    for ingredient in ingredients:
        
        # generalize patterns by including both plural and singular form
        if(not m.singular_noun(ingredient)): # m.singular_noun(x) returns false if x is already singular
            # ingredient is singular, add it and its plural form to pattern
            patterns.append({"label": "INGREDIENT", "pattern": [{"LOWER": f"{ingredient}"}]})
            patterns.append({"label": "INGREDIENT", "pattern": [{"LOWER": f"{m.plural(ingredient)}"}]})
        else: # ingredient is in plural form
            #add it and its singular form to pattern
            patterns.append({"label": "INGREDIENT", "pattern": [{"LOWER": f"{m.singular_noun(ingredient)}"}]})
            patterns.append({"label": "INGREDIENT", "pattern": [{"LOWER": f"{ingredient}"}]})
    
    # add pattern for every category in the list from neo4j
    for category in categories:
        # generalize patterns 
        if(not m.singular_noun(category)): # category is in singular form
            patterns.append({"label": "CATEGORY", "pattern": [{"LOWER": f"{category}"}]})
            patterns.append({"label": "CATEGORY", "pattern": [{"LOWER": f"{m.plural(category)}"}]})
        else: # category is in plural form
            patterns.append({"label": "CATEGORY", "pattern": [{"LOWER": f"{m.singular_noun(category)}"}]})
            patterns.append({"label": "CATEGORY", "pattern": [{"LOWER": f"{category}"}]})

    # apply patterns to entity ruler
    ruler.add_patterns(patterns)
    
    # return the language object which now includes patterns from entity ruler
    return nlp


# This function will use the doc object (list of individual words/entities) to extract key information from a user query
# This will be called any time the user asks a question about recipes
# Return value is a dictionary of the key information: category, cuisine, ingredients, and allergies
def extract_recipe_criteria(doc, allergies):
    # initialize variables and pluralizer
    cuisine = []
    ingredients = []
    category = []
    m = inflect.engine()

    # check each entity in doc object and add to its respective list based on its label
    for ent in doc.ents:
        if ent.label_ == "CUISINE":
            cuisine.append(ent.text.capitalize())
        elif ent.label_ == "INGREDIENT":
            # if ingredient, add any non allergen to list
            if ent.label_ not in allergies and m.plural(ent.lemma_) not in allergies:
                # add both singular and plural version to list. ent.lemma_ is the base singular form of the word
                ingredients.append(ent.lemma_)
                ingredients.append(m.plural(ent.lemma_))
        elif ent.label_ == "CATEGORY":
            # add both singular and plural version to list
            category.append(ent.lemma_)
            category.append(m.plural(ent.lemma_))

    # return dict holding criteria
    return {
        "category": category,
        "cuisine": cuisine,
        "ingredients": ingredients,
        "allergies": allergies
    }
    
    
# This function will use the doc object (list of individual words/entities) to extract key information from a user query
# This will be called any time the user asks a question about restaurants
# Return value is a dictionary of the key information: cuisine, rating, time, and allergies
def extract_restaurant_criteria(doc, city):
    # initialize variables
    cuisine = []
    rating = None
    time = None
    
    # check each entity in doc object and add to its respective list based on its label
    for ent in doc.ents:
        if ent.label_ == "TIME":
            if "minute" in ent.text:
                # if it is a time identifier, set time to the integer part 
                max_time = int(''.join(filter(str.isdigit, ent.text)))
        elif ent.label_ == "RATING_VALUE":
            # set rating to the integer part 
            rating = int(''.join(filter(str.isdigit, ent.text)))
        elif ent.label_ == "CUISINE":
            cuisine = ent.text.capitalize()

    # return dict holding criteria
    return {
        "cuisine": cuisine,
        "min_rating": rating,
        "max_time": time,
        "city": city
    }