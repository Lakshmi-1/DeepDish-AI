from flask import Flask, jsonify, request
from flask_cors import CORS
from rag import query_cypher
from langchain.memory import ConversationBufferMemory
from NER import build_patterns, extract_recipe_criteria
from basicChatStructure import intent_parser, get_last_k_messages
import asyncio

app = Flask(__name__)
cors = CORS(app, origins='*')

# Simple memory store per user (by IP)
user_memory = {}
nlp = build_patterns() #create patterns for NER

@app.route("/api/test", methods=['GET'])
def test():
    return jsonify({"message": "Hello, from Flask!"})

#decalres intent parser object 
conservational_intent_parser = intent_parser()

@app.route('/reset_memory', methods=['POST'])
def reset_memory():
    user_id = request.remote_addr
    if user_id in user_memory:
        user_memory[user_id].clear()  
    return

@app.route('/query', methods=['POST'])
async def query():
    user_query = request.json.get('query', '')
    allergies = request.json.get('allergies', '')
    city = request.json.get('city', '')
    name = request.json.get('name', '')
    user_id = request.remote_addr

    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    # Initialize memory for this user if it doesn't exist 
    if user_id not in user_memory:
        user_memory[user_id] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    memory = user_memory[user_id]
    memory.chat_memory.add_user_message(user_query)

    #memory_pass = str(get_last_k_messages(memory))
    global_intent = conservational_intent_parser.parse_global_user_intent(user_query)
    print(global_intent)

    if global_intent.strip().lower() == 'greetings':
        temp = conservational_intent_parser.respond_to_greeting(user_query) 
        return jsonify({"result": {"result": temp}})
    elif global_intent.strip().lower() == 'quit chat':
        temp = conservational_intent_parser.respond_to_quit_chat(user_query) 
        return jsonify({"result": {"result": temp}})
    elif global_intent.strip().lower() == 'express gratitude':
        temp = conservational_intent_parser.respond_to_gratitude(user_query) 
        return jsonify({"result": {"result": temp}})
    elif global_intent.strip().lower() == 'ask a question':
        #print('entering question pipeline')
        memory_pass = str(get_last_k_messages(memory))
        temp = conservational_intent_parser.respond_to_question(memory_pass)
        if temp.strip().lower() == 'non food related question':
            #print('entering non food related')
            temp = conservational_intent_parser.respond_to_NonFood_question(user_query) 
            return jsonify({"result": {"result": temp}})
        elif temp.strip().lower() == 'food related question':
            #print('entering food related')
            temp = conservational_intent_parser.respond_to_food_question(memory_pass) 
            return jsonify({"result": {"result": temp}})
    elif global_intent.strip().lower() == 'other':
        temp = conservational_intent_parser.respond_to_other(user_query)
        return jsonify({"result": {"result": temp}})
        
    else:
        try:
            # Get lemmatized ingredients using NER
            doc = nlp(user_query)
            criteria = extract_recipe_criteria(doc, allergies)

            chat_history_msgs = memory.load_memory_variables({})["chat_history"]
            chat_history_str = "\n".join([msg.content for msg in chat_history_msgs])
            question_with_memory = chat_history_str + f"\nUser: {criteria}"

            result = await query_cypher(question_with_memory, criteria, city=city, name=name)

            # Save AI response to memory
            memory.chat_memory.add_ai_message(str(result))

            return jsonify({"result": result})
        except Exception as e:
            app.logger.error(f"Error: {e}")
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080, use_reloader=False)
