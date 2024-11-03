import json
import os
import ollama

# Flag to check if the L.T.M model is loaded
ltm_model_loaded = False

# Pull the necessary L.T.M model

ollama.pull('rolandroland/llama3.1-uncensored')
# Define the L.T.M model template
LMTmodel = '''
FROM rolandroland/llama3.1-uncensored
SYSTEM Your task is extract relevant keywords about Erina's "appearance," "personality," "acquaintances"(merge as single keyword e.g. "(Name)-(Relationship)" single keyword) "likes," "dislikes," and "important-thing" From the conversation. Store this keywords in separate arrays as JSON format. Only Result. No Markdown and Annotation. No Extra description or title.
'''

# Initialize the L.T.M module
ollama.create(model='LMT', modelfile=LMTmodel)
print("LMT Model initialized successfully.")

# Load short-term memory from the specified filename
def load_short_term_memory(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            print("Memory Module loaded successfully.")
            return json.load(file)
    print(f"Warning: Memory file '{filename}' not found.")
    return []

# Initialize long-term memory file if it doesn't exist
def initialize_long_term_memory():
    ltm_file = 'data/erina_long-term-memory.json'
    if not os.path.exists(ltm_file):
        ltm_data = {
            "appearance": [],
            "personality": [],
            "acquaintances": [],
            "likes": [],
            "dislikes": [],
            "important-thing": []
        }
        with open(ltm_file, 'w', encoding='utf-8') as file:
            json.dump(ltm_data, file, ensure_ascii=False, indent=4)
        print(f"Initialized long-term memory file: '{ltm_file}'.")

# Load short-term memory
memory = load_short_term_memory('data/erina_short_term_memory.json')
initialize_long_term_memory()  # Ensure long-term memory is initialized

# Merge new data into existing long-term memory
def merge_long_term_memory(new_data):
    ltm_file = 'data/erina_long-term-memory.json'
    
    with open(ltm_file, 'r+', encoding='utf-8') as file:
        long_term_memory = json.load(file)
        
        # Merge new data into existing data
        for key in new_data:
            # Avoid duplicates by converting lists to sets
            existing_values = set(long_term_memory[key])
            new_values = set(new_data[key])
            
            # Update existing values with new values
            existing_values.update(new_values)
            
            # Convert back to list and assign to long_term_memory
            long_term_memory[key] = list(existing_values)
        
        # Move the cursor to the beginning of the file and truncate
        file.seek(0)
        json.dump(long_term_memory, file, ensure_ascii=False, indent=4)
        file.truncate()

# Generate long-term memory from recent conversations

CovLength = 8 # 1~16 is Best Option to do.

def generate_long_term_memory(recent_conversations):
    if len(recent_conversations) < CovLength:
        print("Warning: Not enough recent conversations to generate long-term memory.")
        return

    # Extract traits with LMT model
    context = "\n".join([f"You: {conv['input']} | Erina: {conv['output']}" for conv in recent_conversations])
    print("Context Length: " + str(CovLength))

    response = ollama.chat(model='LMT', messages=[{'role': 'user', 'content': context}])
    
    # Check the response type
    print("Response from LMT model:")
    print(response['message']['content'])  # Debugging: Show the model's response

    # Parse the response as JSON
    new_data = json.loads(response['message']['content'])

    # Merge the newly generated data into long-term memory
    merge_long_term_memory(new_data)

# Call to generate long-term memory using the last 15 entries
if len(memory) >= CovLength:
    generate_long_term_memory(memory[-CovLength:])
else:
    print("Insufficient short-term memory entries to generate long-term memory.")
