from langchain_openai import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain_core.prompts.prompt import PromptTemplate
from langchain.graphs import Neo4jGraph
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Neo4j connection
graph = Neo4jGraph(
    os.getenv('NEO4J_URI'),
    os.getenv('NEO4J_USERNAME'),
    os.getenv('NEO4J_PASSWORD')
)

# Define Cypher Generation and QA Prompts using dynamic schema
CYPHER_GENERATION_TEMPLATE = """
Role:
You are an expert Neo4j Developer generating Cypher queries based on the provided schema. Assume the user wants a real answer unless the question is clearly just "hello" or "hi". Do NOT define custom functions. Do NOT filter out real queries.


Guidelines:
Keep Restaurants and Recipes Separate

Never query them together since they are disjoint entities.

Use Only Explicit Relationships & Constraints

Do not add extra relationships unless the question explicitly requires them.

Use the Category node to classify the recipe type. Example: "dessert" or "appetizer" or "smoothie".

Always query Category when filtering recipe types (e.g., desserts, appetizers).

Default to Recipes for General Questions

If the user asks about food without specifying, assume they mean recipes.

Check Singular & Plural Forms for Node Properties

Example: If checking for "dessert", also check for "desserts".

Ensure Case Insensitivity for All Node Properties

Use toLower() or case-insensitive regex ((?i)) to match property values.

Handle and spelling or grammar errors in the user query before processing. All stopword removal has be done for u

Example:
MATCH (r:Recipe)-[:BELONGS_TO]->(c:Category),
    (r)-[:CONTAINS]->(i:Ingredient)
WHERE toLower(c.value) IN ["dessert", "desserts"]
AND toLower(i.name) IN ["strawberry", "strawberries"]
RETURN r.name AS RecipeName;

Schema:
{schema}

User Question:
{question}
"""

CYPHER_GENERATION_TEMPLATE_RECIPE = """
Role:
You are an expert Neo4j Developer generating recipe Cypher queries based on the provided schema.

Guidelines:

Use Only Explicit Relationships & Constraints

Do not add extra relationships unless the question explicitly requires them.

Use the Category node to classify the recipe type. Example: "dessert" or "appetizer" or "smoothie".

Always query Category when filtering recipe types (e.g., desserts, appetizers).

Check Singular & Plural Forms for Node Properties

Example: If checking for "dessert", also check for "desserts".

Ensure Case Insensitivity for All Node Properties

Use toLower() or case-insensitive regex ((?i)) to match property values.

Handle and spelling or grammar errors in the user query before processing. All stopword removal has be done for you

Example:
MATCH (r:Recipe)-[:BELONGS_TO]->(c:Category),
    (r)-[:CONTAINS]->(i:Ingredient)
WHERE toLower(c.value) IN ["dessert", "desserts"]
AND toLower(i.name) IN ["strawberry", "strawberries"]
RETURN r.name AS RecipeName;

Schema:
{schema}

User Question:
{question}
"""

CYPHER_GENERATION_TEMPLATE_RESTURANTS = """
Role:
You are an expert Neo4j Developer generating resturant Cypher queries based on the provided schema.

Guidelines:

Use Only Explicit Relationships & Constraints

Do not add extra relationships unless the question explicitly requires them.

Check Singular & Plural Forms for Node Properties

Ensure Case Insensitivity for All Node Properties

Use toLower() or case-insensitive regex ((?i)) to match property values.

Handle and spelling or grammar errors in the user query before processing. All stopword removal has be done for you

Example:
MATCH (n:Restaurant)-[:HAS_TYPE]->(t:Type), (n)-[:HAS_RATING]->(r:Rating)
WHERE toLower(t.type) in ['donuts']
RETURN n.name AS RestaurantName

Schema:
{schema}

User Question:
{question}
"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE
)
CYPHER_GENERATION_PROMPT_RECIPE = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE_RECIPE
)
CYPHER_GENERATION_PROMPT_RESTURANTS = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE_RESTURANTS
)

CYPHER_QA_TEMPLATE = """You are an assistant that helps to form nice and human understandable answers. Generate your answer to the question only from the context provided unless the context is empty.
You do not need to refer to the context when the user is exchanging pleasantries. Make sure all other responses are one from the given context no matter the user's question.
Context: {context}
Question: {question}
"""

CYPHER_QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are an assistant that helps to form nice and human understandable answers.
Generate your answer to the question only from the context provided unless the context is empty.
You do not need to refer to the context when the user is exchanging pleasantries.
Make sure all other responses are one from the given context no matter the user's question.

Question: {question}
Context: {context}
"""
)

graph_chain = GraphCypherQAChain.from_llm(
    ChatOpenAI(model="gpt-4o-mini", temperature=0),
    graph=graph,
    qa_prompt=CYPHER_QA_PROMPT,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    verbose=True,
    allow_dangerous_requests=True
)

graph_chain_recipe = GraphCypherQAChain.from_llm(
    ChatOpenAI(model="gpt-4o-mini", temperature=0),
    graph=graph,
    qa_prompt=CYPHER_QA_PROMPT,
    cypher_prompt=CYPHER_GENERATION_PROMPT_RECIPE,
    verbose=True,
    allow_dangerous_requests=True
)

graph_chain_resturants = GraphCypherQAChain.from_llm(
    ChatOpenAI(model="gpt-4o-mini", temperature=0),
    graph=graph,
    qa_prompt=CYPHER_QA_PROMPT,
    cypher_prompt=CYPHER_GENERATION_PROMPT_RESTURANTS,
    verbose=True,
    allow_dangerous_requests=True
)

async def query_cypher(query, intent, extracted_ingredients=None):
    if extracted_ingredients:
        ingredient_text = ", ".join(extracted_ingredients)
        query += f" Please make sure the cypher query checks for these ingredients: {ingredient_text}."
    if intent == 'find a recipe':
        return graph_chain_recipe.invoke({"query": query})
    elif intent == 'find a restaurant':
        return graph_chain_resturants.invoke({"query": query})
    else:
        return graph_chain.invoke({"query": query})
    
