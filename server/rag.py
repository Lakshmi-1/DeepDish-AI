from langchain_openai import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain_core.prompts.prompt import PromptTemplate
from langchain.graphs import Neo4jGraph
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Neo4j connection
graph = Neo4jGraph(
    "neo4j+s://00008022.databases.neo4j.io",
    "neo4j",
    "162KYtL3kzcf5qklj2nVb9f6L4z0xBOAUz8YIckZYpw"
)

# Define Cypher Generation and QA Prompts using dynamic schema
CYPHER_GENERATION_TEMPLATE = """
Role:
You are an expert Neo4j Developer generating Cypher queries based on the provided schema and given input dictionary. Assume the user wants a real answer unless the question is clearly just "hello" or "hi". Do NOT define custom functions. Do NOT filter out real queries.


Guidelines:
Use Only Explicit Relationships & Constraints

Do not add extra relationships unless the question explicitly requires them.

If the user asks about food without specifying, assume they mean recipes.

Ensure Case Insensitivity for All Node Properties

Use toLower() to match property values.

Handle and spelling or grammar errors in the user query before processing.

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

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE
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

graph_chain = GraphCypherQAChain.from_llm(
    ChatOpenAI(model="gpt-4o-mini", temperature=0),
    graph=graph,
    qa_prompt=CYPHER_QA_PROMPT,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    verbose=True,
    allow_dangerous_requests=True
)

async def query_cypher(query, criteria=None):
    query += str(criteria)
    return graph_chain.invoke({"query": query})
