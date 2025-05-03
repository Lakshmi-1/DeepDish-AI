# DeepDish-AI
Github Repo Link: https://github.com/Lakshmi-1/DeepDish-AI/
Youtube Demo Link: 

## Overview
DeepDish-AI is an intelligent, food-focused chatbot designed to assist users with recipe discovery and restaurant recommendations through a conversational interface. Whether you're planning a home-cooked meal or looking for a great place to eat nearby, DeepDish-AI provides fast, personalized, and context-aware suggestions.  By leveraging OpenAI's language models and integrating both recipe and location-based restaurant data, the chatbot delivers highly relevant results tailored to the user's dietary needs, preferences, and location.

## How to Run
1) Clone the git repo
2) Create a free Neo4j graph instance here: [Neo4j AuraDB](https://neo4j.com/docs/aura/classic/auradb/getting-started/create-database/)
3) Load the neo4j .backup file into your instance using this path: ... > Backup & Restore > Restore from Backup File
4) Setup a .env file with your OPENAI_API_KEY, NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD (The the program will prompt for these if they are not configured)
5) Run the command 'pip install -r requirements.txt'
6) Run the command 'python -m spacy download en_core_web_sm'
7) Navigate into the client folder and run the 'npm install' command.
8) Use the 'npm run dev' command to start localhost.
9) Open a new terminal
10) Navigate into the server folder and use the 'flask run' command.
11) Provide an OpenAI key, Neo4j uri, Neo4j username, and Neo4j password to the program when prompted
12) Open the application in your browser
13) Happy chatting 😊

## Features
**Recipe Search**
Allow users to find recipes based on various filters and attributes:
- Cuisine Type: Select from global cuisines (e.g., Italian, Indian, Mexican).
- Category: Choose by meal type (e.g., breakfast, lunch, dinner, dessert).
- Ingredients: Search by including or excluding specific ingredients.
- Instructions: Step-by-step preparation and cooking instructions.
- Time: Filter recipes by total cooking/prep time.
- Nutrition Information: View calories, macros, and dietary information.
- Servings: Specify or adjust number of servings needed.

**Restaurant Recommendations**
Provide users with curated lists of nearby or popular restaurants:
- Rating: Show restaurants based on user ratings or reviews.
- Type: Filter by cuisine or service style (e.g., fast food, fine dining, vegan).
- Location: If enabled, use user’s current location to suggest relevant options.

**Profile Customization**
Enable users to personalize their experience:
- Name: Allows the chatbot to address users personally for a more conversational experience.
- Allergen Information: Helps the chatbot account for allergies when making any recipe suggestions.
- Location: Enables the chatbot to make tailored local restaurant recommendations.

## Notes
- For more details on the project, please refer to the report.
- The files inside server/Recipe_Extraction_Scripts can be used to upload more recipes into your own Neo4j graph instance.
- Please note that our code may or may not be fully compatible with customized configurations beyond those provided in the snapshot.

## Attributions
Pizza Icon & Utensil Background created by Freepik
