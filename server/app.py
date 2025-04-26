from flask import Flask, jsonify, request
from flask_cors import CORS
from rag import query_cypher
from NER import build_patterns, extract_recipe_criteria
import asyncio

app = Flask(__name__)
cors = CORS(app, origins='*')

nlp = build_patterns() #create patterns for NER

@app.route("/api/test", methods=['GET'])
def test():
    return jsonify({"message": "Hello, from Flask!"})

@app.route('/query', methods=['POST'])
async def query():
    user_query = request.json.get('query', '')
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    # Log the query received for debugging
    app.logger.debug(f"Received query: {user_query}")
    
    try:
        # Get lemmatized ingredients using NER
        doc = nlp(user_query)
        criteria = extract_recipe_criteria(doc)
        ingredients = criteria.get("ingredients", [])
        
        # Await the async query_cypher function
        result = await query_cypher(user_query, ingredients)
        
        return jsonify({"result": result})
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080, use_reloader=False)