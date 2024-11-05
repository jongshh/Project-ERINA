import json
import os
import ollama
import random
import psutil
import subprocess
import time
import threading
from datetime import datetime
# from Identity import *
# from Model_Erina import *

#Global Variable
GlobalModel = 'Erina'
Erina_model_loaded = False 
config_file = 'config.json'

#Config Module
def load_config(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        default_config = {
            "default_ratemode": True,
            "default_randomspeak": False,
            "short_term_memory_length": 5,
            "ollama_path": ""
        }
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(default_config, file, ensure_ascii=False, indent=4)
        return default_config

# UI Module
def main_menu():
    config = load_config('config.json')
    while True:
        print("\n=== Main Menu ===")
        print("0. Set Ollama Path")
        print("1. Start Ollama")
        print("2. Start Chat")
        print("3. Custom Erina")
        print("4. Exit")

        choice = input("Select an option (0/1/2/3/4): ")

        if choice == "0":
            set_ollama_path()
        elif choice == "1":
            start_ollama(config['ollama_path'])
        elif choice == "2":
            chat()
        elif choice == "3":
            custom_erina_settings()
        elif choice == "4":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please select 0, 1, 2, 3, or 4.")
            
def custom_erina_settings():
    config = load_config('config.json')
    
    while True:
        print("\n=== Custom Erina Settings ===")
        print(f"1. Default Ratemode: {'On' if config['default_ratemode'] else 'Off'}")
        print(f"2. Default Randomspeak: {'On' if config['default_randomspeak'] else 'Off'}")
        print(f"3. Short-term Memory Length: {config['short_term_memory_length']}")
        print("4. Save and Exit")

        choice = input("Select an option (1/2/3/4): ")

        if choice == "1":
            config['default_ratemode'] = not config['default_ratemode']
        elif choice == "2":
            config['default_randomspeak'] = not config['default_randomspeak']
        elif choice == "3":
            new_length = input("Enter new short-term memory length: ")
            if new_length.isdigit():
                config['short_term_memory_length'] = int(new_length)
            else:
                print("Invalid input. Please enter a valid number.")
        elif choice == "4":
            with open('config.json', 'w', encoding='utf-8') as file:
                json.dump(config, file, ensure_ascii=False, indent=4)
            print("Settings saved successfully.")
            break
        else:
            print("Invalid choice. Please select 1, 2, 3, or 4.")

# Ollama Module
def set_ollama_path():
    config = load_config('config.json')
    ollama_path = input("Enter the full path to Ollama executable: ").strip()
    config['ollama_path'] = ollama_path
    
    with open('config.json', 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    
    print("Ollama path saved successfully.")
    return ollama_path

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
# Erina Module
def initialize_model():
    global Erina_model_loaded
    if not Erina_model_loaded:
        try:
            #ollama.create(model=GlobalModel, modelfile='models/ERINA') # This works in only in terminal.
            Erina_model_loaded = True
            print("ERINA Model initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize ERINA model: {e}")

# Memory Module
# S.T.M (Short-Term-Memory)
def load_short_term_memory(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    print("Memory Module loaded successfully.")
    return []

def save_short_term_memory(filename, memory):
    existing_memory = load_short_term_memory(filename)
    
    unique_memory = []
    existing_inputs = {entry['input'] for entry in existing_memory}  
    
    for entry in memory:
        if entry['input'] not in existing_inputs:  
            unique_memory.append(entry)

    combined_memory = existing_memory + unique_memory  

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(combined_memory, file, ensure_ascii=False, indent=4)
        #print("Memory Module Saved successfully.") #After, Enabling this for Debugging.

def add_to_short_term_memory(memory, user_input, response, rating=None):
    memory.append({
        "timestamp": datetime.now().isoformat(),
        "input": user_input,
        "output": response,
        "rating": rating
    })
    
# L.T.M (Long-Term-Memory)
def load_long_term_memory(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    print("Long-term memory module loaded successfully.")
    return {
        "appearance": [],
        "personality": [],
        "acquaintances": [],
        "likes": [],
        "dislikes": [],
        "important-thing": []
    }
    
def generate_context_with_ltm(short_term_memory, long_term_memory):
    config = load_config('config.json')
    MemoryLength = config['short_term_memory_length']
    ltm_context = []
    
    for key, values in long_term_memory.items():
        if values:  # Only add if there's any value
            ltm_context.append(f"{key.capitalize()}: {', '.join(values)}")
            
    # print("LTM Keywords")
    # print(ltm_context)
    
    short_term_context = [f"User: {entry['input']} | Erina: {entry['output']}" for entry in short_term_memory]
    return "\n".join(short_term_context[-MemoryLength:] + ltm_context)  # Combine LTM and Configured STM entries

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
    config = load_config('config.json')
    memory = load_short_term_memory('data/erina_short_term_memory.json')  # Load short-term memory
    long_term_memory = load_long_term_memory('data/erina_long-term-memory.json')  # Load long-term memory
    MemoryLength = config['short_term_memory_length']
    
    print("Chat Started, Type 'exit' to quit.")
    
    # Generate initial context
    context_input = generate_context_with_ltm(memory, long_term_memory)

    conversations = memory[:]

    # Create a threading Event to toggle random speak mode
    random_speak_enabled = threading.Event()
    if config['default_randomspeak']:
        random_speak_enabled.set()  # Enable random speaking if configured
    else:
        random_speak_enabled.clear()  # Disable random speaking if configured

    # Start the random message generation thread
    threading.Thread(target=random_message_thread, args=(memory, random_speak_enabled), daemon=True).start()

    rating_mode = config['default_ratemode']  # Use config setting

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            context_input += f"\nYou: {user_input}"
            response = ollama.chat(model=GlobalModel, messages=[{'role': 'user', 'content': context_input + "\nErina:"}])
            response_text = response['message']['content'].strip()
            print(f"Erina: {response_text}")
            conversations.append({"input": user_input, "output": response_text, "rating": rating})
            save_short_term_memory('data/erina_short_term_memory.json', conversations)
            conversations.clear()
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

        context_input += f"\nUser: {user_input}"
        rating = 5

        # Use the updated context with long-term memory for generating the response
        response_stream = ollama.chat(model=GlobalModel, messages=[{'role': 'user', 'content': context_input + "\nErina:"}], stream=True)
        response_text = ""
        print("Erina: ", end="", flush=True)

        for response in response_stream:
            print(response['message']['content'], end="", flush=True)
            response_text += response['message']['content']
            time.sleep(0.1)  # Simulate streaming delay
        print()  # New line after response

        # Add the response to the context
        context_input += f"\nErina: {response_text}"

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

            save_short_term_memory('data/erina_short_term_memory.json', conversations)
            conversations.clear()

        else:
            # Default rating to 5 when rating mode is off
            conversations.append({"input": user_input, "output": response_text, "rating": 5})
            save_short_term_memory('data/erina_short_term_memory.json', conversations)
            conversations.clear()

if __name__ == "__main__":
    initialize_model()
    main_menu()
