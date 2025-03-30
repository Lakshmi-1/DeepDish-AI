import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import JSONLoader
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_core.output_parsers import CommaSeparatedListOutputParser
import csv

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

parser = CommaSeparatedListOutputParser()

prompt = ChatPromptTemplate.from_messages([
    ("system", """
        Format the output as a list:
        - The core ingredient name (no amounts, adjectives, or descriptors).
        - Example: ["Flour", "Eggs", "Milk"]
        - DO NOT RETURN AN EMPTY LIST. INFER THE INGREDIENTS FROM THE TEXT.
    """),
    ("user", "{input}")
])

prompt2 = ChatPromptTemplate.from_messages([
    ("system", """
        Format the output as a string:
        - Extract as a **single string** with each step **numbered**.  
        - REMOVE ANY NEW LINE OR ADDITIONAL SPACING OR EXTRA BACKSLASH CHARACTERS.
        - Example:  
            "Instructions": "1. Preheat oven to 350°F. 2. Mix ingredients. 3. Bake for 30 minutes."
    """),
    ("user", "{input}")
])

chain = prompt | llm | parser
chain_instructions = prompt2 | llm

def parse_instructions(instructions_text):
    """Parse the instructions text using the Groq model."""
    result = chain_instructions.invoke({"input": instructions_text})
    return result.content.strip()

def parse_ingredients(ingredients_text):
    """Parse the ingredients text using the Groq model."""
    result = chain.invoke({"input": ingredients_text})
    result = result[1:]
    result = [item.lstrip('- ').strip() for item in result]
    return result

def process_files_in_directory(directory_path):
    results = []
    
    for filename in os.listdir(directory_path):
        if not filename.endswith(".csv"):
            continue
        
        file_path = os.path.join(directory_path, filename)
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            
            
            for row in reader:
                ingredients_text = row.get("ingredients", "")
                instructions_text = row.get("directions", "")

                
                parsed_ingredients = parse_ingredients(ingredients_text) if ingredients_text else []
                parsed_instructions = parse_instructions(instructions_text) if instructions_text else ""
                category = row.get("cuisine_path", "")
                parts = category.split('/')
                category = parts[1]
                cuisine = row.get("cuisine", "")
                difficulty = row.get("difficulty", "")
                results.append({"Category":category, "Cuisine": cuisine, "Difficulty":difficulty, "Recipe Name": row.get("recipe_name", ''), "Ingredients": row.get("ingredients",''), "Instructions": parsed_instructions, "Yield": row.get('servings',''), "Total Time": row.get("total_time",''), "Nutrition": row.get("nutrition",''), "Ingredients_list": parsed_ingredients})
                print(len(results))

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
    for name in ingredients:
        query = """
        MERGE (i:Ingredient {name: $ingredient_name})
        WITH i
        MATCH (r:Recipe {name: $recipe_name})
        MERGE (r)-[:CONTAINS]->(i)
        """
        with driver.session() as session:
            session.run(query, ingredient_name=name.lower(), recipe_name=recipe_name)

def create_optional_field(driver, recipe_name, field_value, node_label, relationship_type):
    query = f"""
    MERGE (n:{node_label} {{value: $field_value}})
    WITH n
    MATCH (r:Recipe {{name: $recipe_name}})
    MERGE (r)-[:{relationship_type}]->(n)
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
            create_optional_field(driver, recipe["Recipe Name"], recipe["Yield"], "Servings", "SERVES")
        
        if recipe["Nutrition"] != '':
            create_optional_field(driver, recipe["Recipe Name"], recipe["Nutrition"], "Nutrition", "HAS_NUTRITION")
        
        if recipe["Category"] != '':
            create_optional_field(driver, recipe["Recipe Name"], recipe["Category"], "Category", "BELONGS_TO")
        
        if recipe["Cuisine"] != '':
            create_optional_field(driver, recipe["Recipe Name"], recipe["Cuisine"], "Cuisine", "HAS_CUISINE")
        
        if recipe["Difficulty"] != '':
            create_optional_field(driver, recipe["Recipe Name"], recipe["Difficulty"], "Difficulty", "HAS_DIFFICULTY")
        
        print("Added recipe to Neo4j.")
    
    close_neo4j_driver(driver)
        

directory_path = r"C:\Users\lalit\Desktop\DeepDish-AI\server\data"  
output_file = "standardized_recipes.json"

# results = process_files_in_directory(directory_path)

# with open(output_file, "a", encoding="utf-8") as f:
#     json.dump(results, f, indent=4)

with open(output_file, "r", encoding="utf-8") as f:
    data = json.load(f)
save_results_to_neo4j(data)