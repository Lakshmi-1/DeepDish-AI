from flask import Flask, jsonify, request
from flask_cors import CORS
from rag import query_cypher
from langchain.memory import ConversationBufferMemory
from NER import build_patterns, extract_recipe_criteria
import asyncio

app = Flask(__name__)
cors = CORS(app, origins='*')

# Simple memory store per user (by IP)
user_memory = {}
nlp = build_patterns() #create patterns for NER

@app.route("/api/test", methods=['GET'])
def test():
    return jsonify({"message": "Hello, from Flask!"})

@app.route('/query', methods=['POST'])
async def query():
    user_query = request.json.get('query', '')
    user_id = request.remote_addr

    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    # Initialize memory for this user if it doesn't exist
    if user_id not in user_memory:
        user_memory[user_id] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    memory = user_memory[user_id]
    memory.chat_memory.add_user_message(user_query)

    try:
        # Get lemmatized ingredients using NER
        doc = nlp(user_query)
        criteria = extract_recipe_criteria(doc)

        # Await the async query_cypher function
        chat_history_msgs = memory.load_memory_variables({})["chat_history"]
        chat_history_str = "\n".join([msg.content for msg in chat_history_msgs])
        question_with_memory = chat_history_str + f"\nUser: {user_query}"
        
        result = await query_cypher({"query": question_with_memory}, criteria)

        # Save AI response to memory
        memory.chat_memory.add_ai_message(str(result))

        return jsonify({"result": result})
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080, use_reloader=False)
