import os
from openai import OpenAI
import json
#from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_core.output_parsers import CommaSeparatedListOutputParser
import csv
import argparse
import re
import json
import requests
from pathlib import Path
from urllib.parse import urlparse

from recipe_scrapers import scrape_me           
import extruct                                   
from bs4 import BeautifulSoup 

import json
import traceback
from openai import OpenAI

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
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

completion_prompt = ChatPromptTemplate.from_messages([
    ("system", """
        You are a helpful assistant that fills in missing fields for a recipe.
        Given a recipe object, your task is to predict and fill in these fields:
        - "Category" (e.g., "Dessert", "Main Course", "Appetizer")
        - "Cuisine" (e.g., "American", "Italian", "French")
        - "Difficulty" (e.g., "Easy", "Intermediate", "Hard")

        ONLY output a JSON dictionary with exactly these keys.
        If you are uncertain, make your best reasonable guess based on the ingredients and instructions.

        Example output:
        "Format the fields like {{\"Category\"}}, {{\"Cuisine\"}}, etc."
    """),
    ("user", "{input}")
])

fill_fields_chain = completion_prompt | llm

def fill_missing_fields(recipe: dict) -> dict:
    """Given a recipe dictionary, fills missing fields Category, Cuisine, Difficulty using GPT-4o-mini."""

    input_text = {
        "Recipe Name": recipe.get("Recipe Name", ""),
        "Ingredients": recipe.get("Ingredients", ""),
        "Instructions": recipe.get("Instructions", ""),
        "Yield": recipe.get("Yield", ""),
        "Total Time": recipe.get("Total Time", "")
    }
    response = fill_fields_chain.invoke({"input": str(input_text)})
    try:
        filled = json.loads(response.content)
    except Exception as e:
        print(f"Failed to parse model output: {e}")
        print("Raw response:", response.content)
        return recipe  
    recipe.update({
        "Category": filled.get("Category", recipe.get("Category", "")),
        "Cuisine": filled.get("Cuisine", recipe.get("Cuisine", "")),
        "Difficulty": filled.get("Difficulty", recipe.get("Difficulty", "")),
    })
    return recipe

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

def _slug_to_cuisine(slug: str) -> str:
    """Cheap guess: pull 'mexican', 'italian', etc. from the domain or url path."""

    cuisines = {"mexican", "italian", "french", "indian", "thai", "japanese",
                "greek", "chinese", "spanish", "korean", "vietnamese", "lebanese"}

    for word in re.split(r"[/\-_.]", slug.lower()):
        if word in cuisines:
            return word.capitalize()
    return ""

def _extract_json_ld(html, url):
    """Return the first Recipe‑type JSON‑LD block if present, else None."""
    data = extruct.extract(html, base_url=url, syntaxes=["json-ld"])
    for block in data.get("json-ld", []):
        if isinstance(block, dict) and block.get("@type") in {"Recipe", ["Recipe"]}:
            return block
    return None
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

def close_neo4j_driver(driver):
    driver.close()

def init_neo4j_driver():
    uri = os.getenv('NEO4J_URI')  
    username = os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')

    driver = GraphDatabase.driver(uri, auth=(username, password))

    return driver

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


def scrape_recipe(url: str) -> dict:
    """
    Return a dict shaped for save_results_to_neo4j().

    Fields:
        Category, Cuisine, Difficulty, Recipe Name, Ingredients, Instructions,
        Yield, Total Time, Nutrition, Ingredients_list
    """
    try:
        scraper = scrape_me(url)        
        raw_ingredients = "\n".join(scraper.ingredients())
        raw_instructions = scraper.instructions()
        meta = {
            "name": scraper.title() or "",
            "total_time": f"{scraper.total_time()} mins" if scraper.total_time() else "",
            "servings": scraper.yields() or "",
            "nutrition": scraper.nutrients() or "",
            "category": ", ".join(scraper.categories()) if hasattr(scraper, "categories") else "",
        }
    except Exception:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        html = resp.text

        data = _extract_json_ld(html, url)
        if not data:                      
            soup = BeautifulSoup(html, "html.parser")
            ingredients_tags = soup.select("[itemprop=recipeIngredient], .ingredients li")
            instruction_tags = soup.select("[itemprop=recipeInstructions], .instructions li, .directions li")
            raw_ingredients = "\n".join(t.get_text(" ", strip=True) for t in ingredients_tags)
            raw_instructions = " ".join(t.get_text(" ", strip=True) for t in instruction_tags)
            meta = {
                "name": soup.title.string.strip() if soup.title else Path(urlparse(url).path).stem,
                "total_time": "",
                "servings": "",
                "nutrition": "",
                "category": "",
            }
        else:
            def _norm(field):
                val = data.get(field, "")
                return " ".join(val.split()) if isinstance(val, str) else val

            raw_ingredients = "\n".join(data.get("recipeIngredient", []))
            instructions = data.get("recipeInstructions", "")
            if isinstance(instructions, list):
                raw_instructions = " ".join(
                    step if isinstance(step, str) else step.get("text", "")
                    for step in instructions
                )
            else:
                raw_instructions = instructions
            meta = {
                "name": _norm("name"),
                "total_time": _norm("totalTime"),
                "servings": _norm("recipeYield"),
                "nutrition": json.dumps(data.get("nutrition", {})),
                "category": ", ".join(data.get("recipeCategory", [])) if isinstance(data.get("recipeCategory", []), list) else data.get("recipeCategory", ""),
            }

    ingredients_list = parse_ingredients(raw_ingredients)
    instructions_std = parse_instructions(raw_instructions)

    domain_bits = urlparse(url).netloc.split(".")
    cuisine_guess = _slug_to_cuisine("/".join(domain_bits + url.split("/")))

    record = {
        "Category": meta["category"],
        "Cuisine": cuisine_guess,
        "Difficulty": "",                     
        "Recipe Name": meta["name"],
        "Ingredients": raw_ingredients,
        "Instructions": instructions_std,
        "Yield": meta["servings"],
        "Total Time": meta["total_time"],
        "Nutrition": meta["nutrition"],
        "Ingredients_list": ingredients_list,
    }
    return record


def scrape_and_ingest(url: str):
    """High‑level helper: scrape → push to Neo4j."""
    try:
      recipe = scrape_recipe(url)
      filled_recipe = fill_missing_fields(recipe)
    except:
      pass

client = OpenAI()

def clean_json_string(s):
    """Removes markdown code fences if present."""
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1]  
    if s.endswith("```"):
        s = s.rsplit("\n", 1)[0] 
    return s

def regenerate_recipe_via_search(url):
    """If scraping + GPT filling fails, fallback: ask GPT-4o with search tool."""
    prompt = f"""
    I tried to scrape a recipe from this URL but it failed:
    {url}

    Please search the web if needed, and reconstruct a clean recipe in JSON format.
    Fields you must include:
    - "Recipe Name"
    - "Ingredients" (raw string)
    - "Instructions" (steps as a single string, numbered)
    - "Category" (like Dessert, Main Course, etc.)
    - "Cuisine" (like American, Italian, etc.)
    - "Difficulty" (Easy, Medium, Hard)
    - "Yield"
    - "Total Time"
    - "Nutrition" (calories, etc.)

    Output ONLY a valid JSON object, nothing else.
    """

    response = response = client.responses.create(
    model="gpt-4o-mini",
    tools=[{"type": "web_search_preview"}],
    temperature=0,
    input=prompt
)

    content = response.output_text

    try:
      try:
        regenerated_recipe = json.loads(content)
        print("Successfully parsed regenerated recipe JSON:")
      except:
        regenerated_recipe = json.loads(clean_json_string(content))
        print("Cleaned up regenerated recipe JSON:")
    except Exception as e:
        print("Failed to parse regenerated recipe JSON:", e)
        print("Raw model output:", content)
        regenerated_recipe = {}

    return regenerated_recipe

def safe_scrape_and_fill(url):
    """
    Try scraping and filling a recipe.
    If that fails, fall back to GPT-4o with search to reconstruct the recipe.
    """
    try:
        recipe = scrape_recipe(url)
        filled_recipe = fill_missing_fields(recipe)
        print(f"Successfully scraped and filled {filled_recipe.get('Recipe Name', '(unknown)')}")
        return filled_recipe
    except Exception as e:
        print(f"Primary scrape and fill failed for {url}: {e}")
        print(traceback.format_exc())
        print("Falling back to GPT-4o with search...")

        fallback_recipe = regenerate_recipe_via_search(url)
        if fallback_recipe:
            print(f"Recovered recipe via GPT-4o for {fallback_recipe.get('Recipe Name', '(unknown)')}")
            return fallback_recipe
        else:
            print(f"Completely failed to retrieve recipe for {url}")
            return None
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape a recipe URL and ingest it into Neo4j.")
    parser.add_argument("url", help="Web address of the recipe page")
    args = parser.parse_args()
    data = safe_scrape_and_fill(args.url)
    save_results_to_neo4j(data)