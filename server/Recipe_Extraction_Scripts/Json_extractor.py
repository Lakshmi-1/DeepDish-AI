import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import JSONLoader
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

parser = JsonOutputParser(pydantic_object={
    "type": "object",
    "properties": {
        "Recipe Name": {"type": "string"},
        "Ingredients": {"type": "string"},
        "Ingredients_list": {
            "type": "array",
            "items": {
                "type": "array",
                "items": [
                    {"type": "string"},  
                    {"type": "string"}   
                ]
            }
        },
        "Instructions": {"type": "string"},
        "Total Time": {"type": "string"},
        "Yield": {"type": "string"},
        "Category": {"type": "string"},
        "Cuisine": {"type": "string"},
        "Nutrition": {"type": "string"},
        "Difficulty": {"type": "string"}
    }
})


prompt = ChatPromptTemplate.from_messages([
    ("system", """Extract all recipes from the provided text into JSON format with the following structure:

        {{
            "Recipe Name": "recipe name here",
            "Ingredients": "string listing the ingredients with adjectives and amounts, comma-separated",
            "Ingredients_list": ["ingredient name", "ingredient name", ...],
            "Instructions": "step-by-step instructions here",
            "Total Time": "total time required",
            "Yield": "number of servings",
            "Category": "category of recipe",
            "Cuisine": "type of cuisine",
            "Nutrition": "nutritional info",
            "Difficulty": "difficulty level"
        }}

        ### Extraction Rules:

        1. **Required Fields**: Every recipe **must** include `"Recipe Name"`, `"Ingredients"`, and `"Instructions"`. **Exclude any recipe missing any of these three fields.**  

        2. **Ingredients_list Formatting**:
        Format the output as a list:
        - The core ingredient name (no amounts, adjectives, or descriptors).
        - Example: ["Flour", "Eggs", "Milk"]
        - For **ingredient name** remove adjectives and descriptors like: Fresh, organic, frozen, dried, chopped, minced, sliced, diced, ground, whole, crushed, canned, etc.
        - For **ingredient name** preserve only the core ingredient name (e.g., "Tomatoes", "Chicken", "Basil", "Pasta", "Flour", "Eggs", "Milk").

        3. **Instructions Formatting**:  
        - Extract as a **single string** with each step **numbered**.  
        - Example:  
            "Instructions": "1. Preheat oven to 350°F. 2. Mix ingredients. 3. Bake for 30 minutes."  

        4. **Total Time**:  
        - If both **prep time** and **cook time** are available, **sum them up**.  
        - If only one is provided, use that as the total time.  

        5. **Category & Cuisine**:  
        - `"Category"` should be a **single word** summarizing the type of dish (e.g., "Dessert", "Soup", "Pasta").
        - Do not include the word "recipe(s)" in the category.
        - `"Cuisine"` should be a **single word** summarizing the type of cuisine (e.g., "Italian", "Mexican", "Indian").

        6. **Nutrition & Difficulty**:  
        - Make `"Nutrition"` **well-formatted** (e.g., `"Calories: 250 kcal, Protein: 10g, Fat: 15g"`).  
        - Extract `"Difficulty"` only if explicitly mentioned in the text.  

        7. **Ingredients Formatting**:
        - "Ingredients" should be a single string listing ingredients exactly as they appear, including adjectives, descriptors, and amounts, separated by commas.
        - Example:
            "Ingredients": "2 cups Fresh basil leaves, 1 Organic chicken breast, 1 can Diced tomatoes, 1 tsp Ground black pepper, 1 cup Whole milk"
        
        8. **Yield Formatting**:
        - Extract ONLY the number or range of servings as a string.
        - DO NOT INCLUDE ANY ADDITION TEXT OR UNITS. JUST THE NUMBER OR NUMBER RANGE.

        9. **If you cannot confidently extract a field, make the field an empty string.**
    """),
    ("user", "{input}")
])

chain = prompt | llm | parser

def parse_recipe(description):
    """Parse the recipe description using the Groq model."""
    result = chain.invoke({"input": description})
    return result

def process_files_in_directory(directory_path):
    results = []
    
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        if os.path.isdir(file_path):
            continue

        loader = JSONLoader(file_path, jq_schema=".", text_content=False)
        data = loader.load()
        content = "\n".join([doc.page_content for doc in data])

        result = parse_recipe(content)
        
        for r in result:
            if r not in results:
                results.extend(result)
            
    return results

def init_neo4j_driver():
    uri = os.getenv('NEO4J_URI')  
    username = os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')

    driver = GraphDatabase.driver(uri, auth=(username, password))

    return driver

def close_neo4j_driver(driver):
    driver.close()

def create_recipe(driver, recipe):
    query = """
    MERGE (r:Recipe {name: $name})
    SET r.instructions = $instructions
    SET r.ingredients = $ingredients
    """
    parameters = {
        "name": recipe["Recipe Name"],
        "instructions": recipe["Instructions"],
        "ingredients": recipe["Ingredients"]
    }

    with driver.session() as session:
        session.run(query, parameters)

def create_ingredients(driver, recipe_name, ingredients):
     with driver.session() as session:
        for name in ingredients:
            query = """
            MERGE (i:Ingredient {name: $ingredient_name})
            WITH i
            MATCH (r:Recipe {name: $recipe_name})
            CREATE (r)-[:CONTAINS]->(i)
            """
            session.run(query, ingredient_name=name.lower(), recipe_name=recipe_name)

def create_optional_field(driver, recipe_name, field_value, node_label, relationship_type):
    query = f"""
    MERGE (n:{node_label} {{value: $field_value}})
    WITH n
    MATCH (r:Recipe {{name: $recipe_name}})
    CREATE (r)-[:{relationship_type}]->(n)
    """
    
    parameters = {
        "recipe_name": recipe_name,
        "field_value": field_value,
        "node_label": node_label, 
        "relationship_type": relationship_type
    }

    with driver.session() as session:
        session.run(query, parameters)

def save_results_to_neo4j(data):
    driver = init_neo4j_driver()
    for recipe in data:
        create_recipe(driver, recipe)
        
        create_ingredients(driver, recipe["Recipe Name"], recipe["Ingredients_list"])

        if recipe["Total Time"] != '':
            create_optional_field(driver, recipe["Recipe Name"], recipe["Total Time"], "TotalTime", "HAS_TOTAL_TIME")
        
        if recipe["Yield"] != '':
            create_optional_field(driver, recipe["Recipe Name"], recipe["Yield"], "Yield", "HAS_YIELD")
        
        if recipe["Nutrition"] != '':
            create_optional_field(driver, recipe["Recipe Name"], recipe["Nutrition"], "Nutrition", "HAS_NUTRITION")
        
        if recipe["Category"] != '':
            create_optional_field(driver, recipe["Recipe Name"], recipe["Category"], "Category", "BELONGS_TO_CATEGORY")
        
        if recipe["Cuisine"] != '':
            create_optional_field(driver, recipe["Recipe Name"], recipe["Cuisine"], "Cuisine", "HAS_CUISINE")
        
        if recipe["Difficulty"] != '':
            create_optional_field(driver, recipe["Recipe Name"], recipe["Difficulty"], "Difficulty", "HAS_DIFFICULTY")
        
        print("Added recipe to Neo4j.")
    
    close_neo4j_driver(driver)
        

directory_path = r"C:\Users\lalit\Desktop\DeepDish-AI\server\data"  
output_file = "standardized_recipes.json"

results = process_files_in_directory(directory_path)

save_results_to_neo4j(results)
