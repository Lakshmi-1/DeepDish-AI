from openai import OpenAI
import numpy as np
import os
import random
from datetime import datetime
import openai
#from sentence_transformers import SentenceTransformer, util
import re
import json

client = OpenAI()

def get_last_k_messages(memory, k = 5):
    # Get the underlying messages
    messages = memory.chat_memory.messages
    # Safely slice the last k (or fewer) messages
    return messages[-k:] if k <= len(messages) else messages


def ask_openai(user_input, system_instruction, temperature=0.0):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_input}
        ],
        temperature=temperature
    )
    return response.choices[0].message.content

class intent_parser(object):
  def __init__(self):
    self.global_intents = ['Find a recipe', 'Find a restaurant', 'Quit Chat', 'Greetings', 'Express Gratitude',
                           'Ask a Question', 'Other']
    
    self.question_intent = ['Food Related Question', 'Non Food Related Question']
    
  def parse_global_user_intent(self, user_input):
    system_instruction = 'Please classify the user\'s intent into one of the following categories. Please provide only the option you choose: ' + ', '.join(self.global_intents)
    global_intent = ask_openai(user_input, system_instruction)

    normalized_intents = [intent.lower() for intent in self.global_intents]
    normalized_response = global_intent.lower()

    if normalized_response not in normalized_intents:
        global_intent = ask_openai(user_input, system_instruction, temperature=0.5)
        normalized_response = global_intent.strip().lower()
    if normalized_response not in normalized_intents:
        return 'unknown'

    intent_index = normalized_intents.index(normalized_response)
    return self.global_intents[intent_index]
  
  
  def respond_to_greeting(self, user_input): #async
    system_instruction = """You are a friendly assistant that can help users find recipes or resturnats. 
    Please give a friendly response to this user greeting and let them know some of the things that you are able to do such as find a healhty recipe, find a recipe with certain ingredients, 
    find a resturant, etc."""
    greeting_response = ask_openai(user_input, system_instruction)
    
    return greeting_response
  
  def respond_to_quit_chat(self, user_input):
    system_instruction = """You are a friendly assistant that can help users find recipes or resturnats. 
    The user has expressed that they are done with their current session. Please give them a kind farewell and let them know you are here to help for any future cooking needs"""
    quit_chat_response = ask_openai(user_input, system_instruction)

    return quit_chat_response

  def respond_to_gratitude(self, user_input):
    system_instruction = """You are a friendly assistant that can help users find recipes or resturnats. 
    The user has expressed gratitude for your help. Please provide a friendly answer and let them know you can continue to help them or help them with any new food questions"""
    gratitude_response = ask_openai(user_input, system_instruction)

    return gratitude_response
  def respond_to_question(self, user_input):
    system_instruction = """You are an assistant that determines whether a user has asked a food related or non food related question. 
    Please respond exactly Food Related Question or Non Food Related Question"""
    food_question_response = ask_openai(user_input, system_instruction)
    return food_question_response
  
  def respond_to_food_question(self, user_input):
    system_instruction = """You are a friendly assistant that can help users answer food related questions. 
    Please refer to the current user question and previous input to answer as accurately as possible. 
    Only respond to the most recent user question and use previous input as context"""
    food_question_response = ask_openai(user_input, system_instruction)
    return food_question_response
    
  def respond_to_NonFood_question(self, user_input):
    system_instruction = """You are a friendly assistant that can help users find recipes or resturnats. 
    The user has asked a non food related question. Please let them know that unfortunately you cannot help with this as you are designed to only help with food related tasks"""
    NonFood_response = ask_openai(user_input, system_instruction)

    return NonFood_response
  
  def respond_to_other(self, user_input):
    system_instruction = """You are a friendly assistant that can help users find recipes or resturnats. 
    The user has given a response that is irrelevant to food. Please redirct the user by informing them that you are only trained for food related tasks."""
    other_response = ask_openai(user_input, system_instruction)

    return other_response
  def find_relevant_information(self, current_query, memory):
    system_instruction = """You are an information synthesis expert. I am going to give you a conversation and a current user question.
    Please take the conversation and extract only the relevant details to the current user question. Return your response as {'relevant context': ...}
    Do not restate the users current or previous questions simply extract the relevant information to their current question"""
    user_input = f"""previous conversation: {memory}
    current question: {current_query}"""
    find_info = ask_openai(user_input, system_instruction)

    return find_info 
     

class backup_IR(object):
    def __init__(self, backup_recipe_flat_file):
        with open(backup_recipe_flat_file) as f:
            self.recipes = json.load(f)

    def get_healthy_recipes(self, min_score=4):
        healthy_recipes = [recipe for recipe in self.recipes if recipe.get("healthy", 0) >= min_score]
        return healthy_recipes

    def get_ingredients_recipes(self, ingredients_list):
        ingredient_recipes = [
            recipe for recipe in self.recipes
            if all(any(ing.lower() in ingredient.lower() for ingredient in recipe.get("ingredients", [])) for ing in ingredients_list)
        ]

        if not ingredient_recipes:
            ingredient_recipes = [
                recipe for recipe in self.recipes
                if any(ing.lower() in ingredient.lower() for ing in ingredients_list for ingredient in recipe.get("ingredients", []))
            ]
        return ingredient_recipes

    def get_culture_recipes(self, culture):
        culture = str(culture[0])
        culture_recipes = [
              recipe for recipe in self.recipes
              if culture.lower() in recipe.get("origin", "").lower()
          ]        
        return culture_recipes

class dialogue(object):
    def __init__(self, backup_ir_object):
      self.backup_ir_object = backup_ir_object
      self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
      self.recipe_capabilities = ['Search for a healthy recipe',
                                  'Search for a recipe with certain ingredients',
                                  'Search for a recipe from a certain culture']

      self.restruant_capabilities = ['Search for a restruant near me',
                                     'Search for a resturant with a certain dish',
                                     'Search for a resturant from a certain culture']

      self.valid_capabilities = ["healthy", "ingredients", "culture_recipe", "near_me", "dish", "culture_resturant"]

      self.intent_examples = {
    "find_recipe": [
        "Find me a recipe",
        "I want to cook something",
        "Show me recipes with chicken",
        "Give me a dish with mushrooms",
        "I need a vegetarian meal idea"
    ],
    "find_restaurant": [
        "Where can I eat nearby?",
        "Find restaurants near me",
        "I’m hungry, any good spots?",
        "Suggest a place to eat",
        "What restaurants are open now?"
    ]
}
      self.layer_one_intent = None
      self.layer_two_intent = None
      self.current_user_response = None

    def get_greeting(self):
        day_of_week = datetime.now().strftime('%A')
        greetings = [
            "Hello there!",
            "Good to see you!",
            f"Happy {day_of_week}!",
            "Hey! How's it going?",
            "Hi! Hope you're having a great day!"
        ]
        return random.choice(greetings)
    def handle_appreciation(self, user_input):
        """Detect if the user is thanking the bot and respond accordingly."""
        appreciation_patterns = re.compile(r"\b(thanks|thank you|thx)\b", re.IGNORECASE)
        if appreciation_patterns.search(user_input):
            return "You're welcome! I'm glad I could help. If you need anything else, just let me know."
        return None
    def get_purpose(self):
      #sample collection of uses
      purposes = [
            "help you find the perfect restaurant.",
            "help you find the perfect recipe.",
            "help you discover new dishes and where to get the ingredients.",
            "find you a nearby spot for a datenight or a dinner with friends.",
            "find you a healthy recipe that fits with your diet goals."
        ]
      const_purpose_statement = f'My name is DeepDishAI I am here to help you with all of your food needs. For example I can {random.choice(purposes)} Please let me know what I can help you with today!'
      return const_purpose_statement

    def get_healthy_graph(self):
        return None

    def get_ingredients_graph(self):
        return None

    def get_culture_recipe_graph(self):
        return None

    def get_near_me_graph(self):
        pass

    def get_dish_graph(self):
        pass

    def get_culture_resturant_graph(self):
        pass

    def get_healthy_backup(self):
        #print(self.backup_ir_object.get_healthy_recipes())
        return self.backup_ir_object.get_healthy_recipes()

    def get_ingredients_backup(self, ingredients):
        ingredients = [x.lower() for x in ingredients]
        return self.backup_ir_object.get_ingredients_recipes(ingredients)
        #return self.backup_ir_object.get_ingredients_recipes()

    def get_culture_recipe_backup(self, origin):
         culture = origin # Need to update this to use NLP
         return self.backup_ir_object.get_culture_recipes(culture)

    def get_near_me_backup(self):
        pass

    def get_dish_backup(self):
        pass

    def get_culture_resturant_backup(self):
        pass

    def get_healthy(self):
        print('here')
        try:
          r = self.get_healthy_graph()
          if r is None:
            return self.get_healthy_backup()
        except:
          return None

    def get_ingredients(self, ingredients):
      try:
        r = self.get_ingredients_graph()
        if r is None:
          return self.get_ingredients_backup(ingredients)
      except:
        return None

    def get_culture_recipe(self, origin):
      try:
        r = self.get_culture_recipe_graph()
        if r is None:
          return self.get_culture_recipe_backup(origin)
      except:
        return None

    def get_near_me(self):
        try:
          return self.get_near_me_graph()
        except:
          return self.get_near_me_backup()

    def get_dish(self):
        try:
          return self.get_dish_graph()
        except:
          return self.get_dish_backup()

    def get_culture_resturant(self):
        try:
          return self.get_culture_resturant_graph()
        except:
          return self.get_culture_resturant_backup()

class dialogue_helper(object):
  def __init__(self, backup_ir_object):
    self.backup_ir_object = backup_ir_object
    self.recipe_capabilities = ['Search for a healthy recipe',
                                  'Search for a recipe with certain ingredients',
                                  'Search for a recipe from a certain culture']

    self.restruant_capabilities = ['Search for a restruant near me',
                                     'Search for a resturant with a certain dish',
                                     'Search for a resturant from a certain culture']
  def get_recipe_capabilities(self):
    return self.recipe_capabilities
  def get_restruant_capabilities(self):
    return self.restruant_capabilities


import spacy

nlp = spacy.load("en_core_web_sm")

def extract_food_origin_entities(text):
    doc = nlp(text)
    origin_entities = [
        ent.text for ent in doc.ents
        if ent.label_ in ("GPE", "NORP")
    ]
    return origin_entities

class FoodChatBot:
    def __init__(self, recipe_file, intent_parser):
        self.dialogue_helper = dialogue_helper(recipe_file)
        self.intent_parser = intent_parser
        self.backup_ir = backup_IR(recipe_file)
        self.dialogue_system = dialogue(self.backup_ir)
        self.conversation_state = {
            'layer_one_confirmed': False,
            'layer_two_confirmed': False,
            'current_intent': None,
            'current_capability': None
        }

    def start_conversation(self):
        print(self.dialogue_system.get_greeting())
        print(self.dialogue_system.get_purpose())
        self.handle_user_input()

    def handle_user_input(self):
      user_input = 'None'
      global_intent = 'None'
      specific_intent = 'None'
      conversational_intent = 'None'

# ['Find a recipe', 'Find a resturant', 'Quit Chat', 'None of the Above'] global
# ['Express Gratitude', 'Ask a Question', 'None of the Above'] conversational
# ['Find a healthy recipe', 'Find a recipe that includes certain ingredients', 'Find a recipe from a certain culture', 'None of the Above'] specific

      #I will continue the chat until the user says they want to end it 
      while global_intent != 'Quit Chat':
        
        user_input = input("\nUser: ")
        global_intent, conversational_intent, specific_intent = self.intent_parser.parse_all_intents(user_input)
        
        if specific_intent == 'None of the Above':
          #print(global_intent)
          if global_intent == 'Find a recipe':
            capabilities = self.dialogue_helper.get_recipe_capabilities()
            if len(capabilities) > 1:
                formatted = ', '.join(capabilities[:-1]) + f", and {capabilities[-1]}"
            else:
                formatted = capabilities[0]

            print(f"Sure, I can help with many different recipes. For example, I can {formatted}. What kind of recipe can I help you find?")
          elif global_intent == 'Find a restaurant':
            capabilities = self.dialogue_helper.get_restruant_capabilities()
            if len(capabilities) > 1:
                formatted = ', '.join(capabilities[:-1]) + f", and {capabilities[-1]}"
            else:
                formatted = capabilities[0]
            print(f"Sure, I can help with many different restaurants. For example, I can {formatted}. What kind of restaurant can I help you find?")
        elif specific_intent == 'Find a healthy recipe':
          print('Here are some healthy recipes:')
          print(self.dialogue_system.get_healthy())
        elif specific_intent == 'Find a recipe that includes certain ingredients':
          print('Here are some recipes with similar ingredients:')

          ingredients = self.intent_parser.parse_ingredients(user_input)
          ingredients = ingredients.split(',')
          ingredients = [x.strip() for x in ingredients]
          #print(ingredients)

          print(self.dialogue_system.get_ingredients(ingredients))
        elif specific_intent == 'Find a recipe from a certain culture':
          origin = extract_food_origin_entities(user_input)
          if len(origin) == 0:
            print('failed on origin') #should probably call GPT to get this if it fails also probably need soft matching for like Mexican vs Mexico etc. 
          else:
            print('Here are some recipes matching your description:')
            print(self.dialogue_system.get_culture_recipe(origin))
        else:
          print('error')
          
if __name__ == "__main__":
  test = intent_parser()
  bot = FoodChatBot("example_flat_file.json", test)
  bot.start_conversation()
