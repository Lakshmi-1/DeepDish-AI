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
     