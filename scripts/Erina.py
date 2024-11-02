import json
import os
import ollama
import random
import psutil
import subprocess
import time
import threading
from datetime import datetime
from Identity import *

#Global Variable
GlobalModel = 'Erina'
model_loaded = False 
config_file = 'config.json'


#Config Module
def load_config():
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as file:
            config = json.load(file)
            return config.get('ollama_path', "")
    return ""

def set_ollama_path():
    ollama_path = input("Enter the full path to Ollama executable: ").strip()
    config = {"ollama_path": ollama_path}
    with open(config_file, 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    print("Ollama path saved successfully.")
    return ollama_path


# Ollama Module
def start_ollama(ollama_path):
    for proc in psutil.process_iter(['name']):
        if 'ollama' in proc.info['name'].lower():
            print("Ollama is already running.")
            return True

    try:
        subprocess.Popen([ollama_path])  
        print("Ollama started successfully.")
        return True
    except Exception as e:
        print(f"Failed to start Ollama: {e}")
        return False
    
# Model Module
def initialize_model():
    global model_loaded
    if not model_loaded:
        try:
            ollama.create(model=GlobalModel, modelfile=modeltype)
            model_loaded = True
            print("Model initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize model: {e}")

# Memory Module
def load_memory(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    print("Memory Module loaded successfully.")
    return []

def save_memory(filename, memory):
    existing_memory = load_memory(filename)
    existing_memory.extend(memory)  
    
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(existing_memory, file, ensure_ascii=False, indent=4)
        #print("Memory Module Saved successfully.") #After, Enabling this for Debugging.
        
def add_to_memory(memory, user_input, response, rating=None):
    memory.append({
        "timestamp": datetime.now().isoformat(),
        "input": user_input,
        "output": response,
        "rating": rating
    })

# Randomspeak Module
def generate_random_message(context):
    # Generate a random message with streaming
    prompt = "\n".join(context[-5:]) + "\nErina:"
    response_stream = ollama.chat(model=GlobalModel, messages=[{'role': 'user', 'content': prompt}], stream=True)
    response_text = ""

    print("Erina (random message): ", end="", flush=True)
    for response in response_stream:
        print(response['message']['content'], end="", flush=True)
        response_text += response['message']['content']
        time.sleep(0.1)  # Simulate streaming delay
    print()  # New line after response
    return response_text.strip()

def random_message_thread(context, random_speak_enabled):
    while True:
        time.sleep(random.randint(10, 30))  # Random interval between 10 to 30 seconds
        if random_speak_enabled.is_set() and context:  # Check if random speak is enabled and if there is context available
            random_message = generate_random_message(context)
            context.append(f"Erina: {random_message}")

# Basic Text-2-Text Module
def chat():
    memory = load_memory('data/erina_memory.json')  # Load persistent memory

    print("Chat Started, Type 'exit' to quit.")
    context = [f"You: {entry['input']} | Erina: {entry['output']}" for entry in memory[-5:]]
    conversations = memory[:]

    # Create a threading Event to toggle random speak mode
    random_speak_enabled = threading.Event()
    random_speak_enabled.clear()  # Start with random speaking disabled

    # Start the random message generation thread
    threading.Thread(target=random_message_thread, args=(context, random_speak_enabled), daemon=True).start()

    rating_mode = False

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            context.append(f"You: {user_input}")
            context_input = "\n".join(context[-5:])

            response = ollama.chat(model=GlobalModel, messages=[{'role': 'user', 'content': context_input + "\nErina:"}])
            response_text = response['message']['content'].strip()
            print(f"Erina: {response_text}")
            break

        if user_input.startswith("/ratemode"):
            rating_mode = not rating_mode
            mode_status = "on" if rating_mode else "off"
            print(f"Rating mode is now {mode_status}.")
            continue

        if user_input.startswith("/randomspeak"):
            if random_speak_enabled.is_set():
                random_speak_enabled.clear()  # Disable random speaking
                print("Random speaking mode is now OFF.")
            else:
                random_speak_enabled.set()  # Enable random speaking
                print("Random speaking mode is now ON.")
            continue

        context.append(f"You: {user_input}")
        context_input = "\n".join(context[-5:])

        # Stream Erina's response
        response_stream = ollama.chat(model=GlobalModel, messages=[{'role': 'user', 'content': context_input + "\nErina:"}], stream=True)
        response_text = ""
        print("Erina: ", end="", flush=True)

        for response in response_stream:
            print(response['message']['content'], end="", flush=True)
            response_text += response['message']['content']
            time.sleep(0.1)  # Simulate streaming delay
        print()  # New line after response

        context.append(f"Erina: {response_text}")

        if rating_mode:
            try:
                rating = int(input("Rate my response from 1 to 10 (1 = terrible, 10 = excellent): "))
                if rating < 1 or rating > 10:
                    print("Please enter a valid rating between 1 and 10.")
                    rating = 5

            except ValueError:
                print("Invalid input. Rating set to default value of 5.")
                rating = 5  # Default to 5 on ValueError

            conversations.append({"input": user_input, "output": response_text, "rating": rating})

            save_memory('data/erina_memory.json', conversations)
            conversations.clear()

        else:
            # Default rating to 5 when rating mode is off
            conversations.append({"input": user_input, "output": response_text, "rating": 5})
            save_memory('data/erina_memory.json', conversations)
            conversations.clear()
            
# UI Module
def main_menu():
    ollama_path = load_config()

    while True:
        print("\n=== Main Menu ===")
        print("0. Set Ollama Path")
        print("1. Start Ollama")
        print("2. Start Chat")
        print("3. Exit")

        choice = input("Select an option (0/1/2/3): ")

        if choice == "0":
            ollama_path = set_ollama_path()
            continue
        elif choice == "1":
            if ollama_path == "":
                print("Ollama path is not set. Please set it first.")
            elif start_ollama(ollama_path):
                initialize_model()  
            continue
        elif choice == "2":
            if not model_loaded:
                print("Please start Ollama first.")
            else:
                chat()  
            continue
        elif choice == "3":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please select 0, 1, 2, or 3.")

if __name__ == "__main__":
    main_menu()
