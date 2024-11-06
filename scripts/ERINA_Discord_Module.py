import json
import discord
import os
import ollama
import psutil
import subprocess
import sys
import re
import io
import contextlib

from datetime import datetime
from dotenv import load_dotenv
from googlesearch import search  

#Global Variable
GlobalModel = 'Erina'
Erina_model_loaded = False 
config_file = 'discord_config.json'

Erina_prompt_filenames = [
    'character_prompt_01.txt', 'character_prompt_05.txt' # Remove 2,3,4 Because lack of information
]

prompt_path = os.path.join(os.getcwd(), "prompt")

#Initial Prompt (To Match with STT-TTS Module)

def load_character_prompt():
    global Erina_prompt_filenames, prompt_path

    character_prompts = []

    for filename in Erina_prompt_filenames:
        path = os.path.join(prompt_path, filename)
        # print(f"Attempting to load: {path}")
        try:
            with open(path, 'r', encoding='utf-8') as file:
                character_prompt = file.read()
                # print(f"Loaded content from {filename}: {character_prompt[:100]}...")  # 처음 100자만 출력
                character_prompts.append(character_prompt)
        except FileNotFoundError:
            print(f"File not found: {path}")
            character_prompts.append("")  # 파일이 없을 경우 빈 프롬프트 추가
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            character_prompts.append("")  # 다른 예외가 발생할 경우 빈 프롬프트 추가

    return character_prompts

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
    config = load_config('discord_config.json')
    while True:
        print("\n=== ERINA Discord Module Main Menu ===")
        print("0. Set Ollama Path")
        print("1. Start Ollama")
        print("2. Start Discord Chat Module")
        print("3. Custom Erina")
        print("4. Exit")

        choice = input("Select an option (0/1/2/3/4): ")

        if choice == "0":
            set_ollama_path()
        elif choice == "1":
            start_ollama(config['ollama_path'])
        elif choice == "2":
            discord_chat()
        elif choice == "3":
            custom_erina_settings()
        elif choice == "4":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please select 0, 1, 2, 3, or 4.")
            
def custom_erina_settings():
    config = load_config('discord_config.json')
    
    while True:
        print("\n=== Custom Erina Settings ===")
        print(f"1. Short-term Memory Length: {config['short_term_memory_length']}")
        print("2. Save and Exit")

        choice = input("Select an option (1/2): ")

        if choice == "1":
            new_length = input("Enter new short-term memory length: ")
            if new_length.isdigit():
                config['short_term_memory_length'] = int(new_length)
            else:
                print("Invalid input. Please enter a valid number.")
        elif choice == "2":
            with open('discord_config.json', 'w', encoding='utf-8') as file:
                json.dump(config, file, ensure_ascii=False, indent=4)
            print("Settings saved successfully.")
            break
        else:
            print("Invalid choice. Please select 1 or 2.")

# Ollama Module
def set_ollama_path():
    config = load_config('discord_config.json')
    ollama_path = input("Enter the full path to Ollama executable: ").strip()
    config['ollama_path'] = ollama_path
    
    with open('discord_config.json', 'w', encoding='utf-8') as file:
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


# T.O.O.L Module
def execute_tool(code, tool_type):
    if tool_type == "Python-exe":
        return execute_Python_code(code)
    elif tool_type == "google-search":
        return perform_google_search(code)
    return "Invalid tool type"

def perform_google_search(query):
    results = []
    for j in search(query, num_results=5, advanced=True):
        results.append(f"TITLE: {j.title}\n DESC: {j.description}\n")
    return '\n'.join(results)


def execute_Python_code(code):
     # A string stream to capture the outputs of exec
    output = io.StringIO() 
    try:
        # Redirect stdout to the StringIO object
        with contextlib.redirect_stdout(output):  
            # Allow imports 
            exec(code, globals())
    except Exception as e:
        # If an error occurs, capture it as part of the output
        print(f"Error: {e}", file=output)  
    return output.getvalue()

def interact_with_model(initial_messages):
    history = initial_messages
    response_complete = False
    while not response_complete:
        stream = ollama.chat(
                    model=GlobalModel,
                    messages=history,
                    stream=True
                )
                
        full_response = ""

        for chunk in stream:
            if 'message' in chunk and 'content' in chunk['message']:
                response_part = chunk['message']['content']
                full_response += response_part
                sys.stdout.write(response_part)
                sys.stdout.flush()
        

                match = re.search(r'```(Python-exe|google-search)\s*[\n](.*?)\s*```', full_response, re.DOTALL)
                if match:
                    tool_type, code = match.groups()
                    execution_result = execute_tool(code.strip(), tool_type)
                    print(f"\nExecuted {tool_type} Result: {execution_result}")
                    if execution_result.strip():
                        history.append({"role": "assistant", "content": full_response})
                        history.append({'role': 'user', 'content': f"Executed {tool_type} Result: " + execution_result.strip()})
                    else:
                        history.append({"role": "assistant", "content": full_response})
                        history.append({"role": "user", "content": full_response + f"\nExecution {tool_type} is successful without outputs"})
                    break

        # If code was executed, we will contiune the loop and feed the model with executed outputs
        if match:
            continue
        else:
            print()  # Move to the next line if no code was detected and streaming finished
            history.append({'role': 'assistant', 'content': full_response})
            response_complete = True  # Exit the while loop as normal continuation if no code block found
    return history, full_response

# Basic Text-2-Text Discord Module

def discord_chat():
    load_dotenv()  # .env token load
    TOKEN = os.getenv('DISCORD_TOKEN')

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    allowed_channel_id = 1303526310450167849

    @client.event
    async def on_ready():
        print(f'We have logged in as {client.user.name}')
        await client.change_presence(activity=discord.Game(name="Whac-the-Jongsh"))
        print("Name:",client.user.name,"ID:",client.user.id,"Version:",discord.__version__)

    @client.event
    async def on_message(message):
        
        # Check if the message is from the allowed channel
        if message.channel.id != allowed_channel_id:
            return  # If it's not the allowed channel, ignore the message
        
        # S.T.M load
        history = []
        
        memory = load_short_term_memory('data/erina_short_term_memory_discord.json')
        config = load_config('discord_config.json')
        MemoryLength = config['short_term_memory_length']
        short_term_context = [f"{entry['input']} | Erina: {entry['output']}" for entry in memory]

        if message.author == client.user:
            return  # Ignore Bot Message

        # Receive User Message
        user_input = message.content
        user_name = message.author.nick if message.author.nick else message.author.name  # Handle missing nicknames

        # Merge short-term memory long-term memory to context
        character_prompts = load_character_prompt() 

        # Combine all character prompts into a single string
        context_input = "\n".join(character_prompts + short_term_context[-MemoryLength:])
        
        # Merge User's Input
        user_prompt = f"{user_name}: {user_input}" 
        context_input += user_prompt
        
        # Final message sent to the language model
        final_message = context_input
        
        history.append({"role": "user", "content": final_message})
        
        try:
            
            history, full_response = interact_with_model(history)
            await message.channel.send(full_response)

            # Update and save short-term memory
            memory.append({"input": user_input, "output": full_response, "rating": 5})
            save_short_term_memory('data/erina_short_term_memory_discord.json', memory)

        except Exception as e:
            print(f"Error generating response: {e}")
            await message.channel.send("I'm having trouble responding right now. Please try again later.")

    client.run(TOKEN)

if __name__ == "__main__":
    initialize_model()
    load_character_prompt()
    main_menu()