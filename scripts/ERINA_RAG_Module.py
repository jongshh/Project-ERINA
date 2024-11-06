import json
import discord
import os
import ollama
import psutil
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# from Identity import *
# from Model_Erina import *

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
        
        # Check if the message is from the allowed channe
        if message.channel.id != allowed_channel_id:
            return  # If it's not the allowed channel, ignore the message
        
        # S.T.M load
        memory = load_short_term_memory('data/erina_short_term_memory_discord.json')
        config = load_config('discord_config.json')
        MemoryLength = config['short_term_memory_length']
        short_term_context = [f"{entry['input']} | Erina: {entry['output']}" for entry in memory]

        if message.author == client.user:
            return  # Ignore Bot Message

        # Receive User Message
        user_input = message.content
        user_name = message.author.nick # User name Sometime Messing Around

        # Merge short-term memory long-term memory to context
        character_prompts = load_character_prompt() # Combine this with STM Make her stupid Machine, Maybe Check the Prompt First.

        # Combine all character prompts into a single string
        # context_input = "\n".join(short_term_context[-MemoryLength:]) # Use Only One.
        context_input = "\n".join(character_prompts + short_term_context[-MemoryLength:])
        
        # Merge User's Input
        user_prompt = f"{user_name} : {user_input}" 
        context_input += user_prompt
        
        final_message = context_input
        
        openai_client = OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='Erina'
        )
        
        try:
            # Generate response from OpenAI API - Ollama
            response = openai_client.chat.completions.create(
                model="Erina",
                messages=[{'role': 'user', 'content': final_message}],
                temperature=0.90,
                stream=False,
            )

            # Retrieve the response text correctly
            response_text = response.choices[0].message.content
            await message.channel.send(response_text)

            # Update and save short-term memory
            memory.append({"input": user_input, "output": response_text, "rating": 5})
            save_short_term_memory('data/erina_short_term_memory_discord.json', memory)

        except Exception as e:
            print(f"Error generating response: {e}")
            await message.channel.send("I'm having trouble responding right now. Please try again later.")

    client.run(TOKEN)

if __name__ == "__main__":
    initialize_model()
    load_character_prompt()
    main_menu()