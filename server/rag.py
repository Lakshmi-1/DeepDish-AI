from langchain_openai import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain_core.prompts.prompt import PromptTemplate
from langchain_community.graphs import Neo4jGraph
from dotenv import load_dotenv
import getpass
import os

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
neo4j_uri = os.getenv('NEO4J_URI')
neo4j_username = os.getenv('NEO4J_USERNAME')
neo4j_password = os.getenv('NEO4J_PASSWORD')

# Get necessary config variables from user if not in 
if openai_api_key is None:
    openai_api_key = getpass.getpass("Please enter your OpenAI API key: ")
    os.environ["OPENAI_API_KEY"] = openai_api_key

if neo4j_uri is None:
    neo4j_uri = getpass.getpass("Please enter your Neo4j Uri: ")
    os.environ["NEO4J_URI"] = neo4j_uri

if neo4j_username is None:
    neo4j_username = getpass.getpass("Please enter your Neo4j username: ")
    os.environ["NEO4J_USERNAME"] = neo4j_username

if neo4j_password is None:
    neo4j_password = getpass.getpass("Please enter your Neo4j password: ")
    os.environ["NEO4J_PASSWORD"] = neo4j_password

# Initialize Neo4j connection
graph = Neo4jGraph(
     neo4j_uri,
     neo4j_username,
     neo4j_password
)

# Define Cypher Generation and QA Prompts using dynamic schema
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

Properly account for all of the user's allergies in the cypher query.

Always MATCH the ingredients of a recipe and use WHERE NOT toLower(i.name) IN [...] for any allergies the user provides you. 

Do not use WHERE toLower(i.name) NOT IN [...].

Some input keys can be empty.

Example:
MATCH (r:Recipe)-[:BELONGS_TO]->(c:Category),
    (r)-[:CONTAINS]->(i:Ingredient)
WHERE toLower(c.value) IN ["dessert"]
AND toLower(i.name) IN ["strawberry"]
AND NOT toLower(i.name) IN ["avocado"]
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

If a city is provided to you, check that the restaurant is in that city using the address property.

Do not add extra relationships unless the question explicitly requires them.

Check Singular & Plural Forms for Node Properties

Ensure Case Insensitivity for All Node Properties

Use toLower() or case-insensitive regex ((?i)) to match property values.

Handle and spelling or grammar errors in the user query before processing. All stopword removal has be done for you

Some input keys can be empty.

Example:
MATCH (n:Restaurant)-[:HAS_TYPE]->(t:Type)
WHERE toLower(t.type) in ['donuts']
AND n.address CONTAINS "Plano"
RETURN n.name AS RestaurantName

Schema:
{schema}

User Question:
{question}
"""

CYPHER_GENERATION_PROMPT_RECIPE = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE_RECIPE
)
CYPHER_GENERATION_PROMPT_RESTURANTS = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE_RESTURANTS
)

CYPHER_QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are tasked with forming nice and human understandable answers. 
Format whatever data you are given in the context in a human-readable way. Do not let the user know about the fact that you are referring to a provided context.
If you disclude recipes due to allergies, mention that to the user.
Only disclude ingredients if they are an allergy.
Just provide a direct answer without any additional text unless you have to explain something regarding the allergies they specified.
If the context is empty, try your best to answer the user's question.
Refer to the user in the second person.

Question: {question}
Context: {context}
"""
)

# Define the graph chains for recipes and restaurants
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

# Query the graph with the criteria
async def query_cypher(query, graph_intent, criteria=None, name=None):
    query += str(criteria)
    if name:
        query = f"Address the user by their name, {name}, when answering.\n" + query

    if graph_intent == 'find a recipe':
        return graph_chain_recipe.invoke({"query": query})
    else:
        return graph_chain_resturants.invoke({"query": query})