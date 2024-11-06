import json
import discord
import os
import ollama
import random
import psutil
import subprocess
import time
import threading
from datetime import datetime
from dotenv import load_dotenv
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
    
    # Long-Term Memory context generation
    for key, values in long_term_memory.items():
        if values:  # Only add if there's any value
            formatted_values = []
            for value in values:
                if isinstance(value, dict):
                    # Convert dictionary items into a readable string
                    dict_entries = ", ".join([f"{k}: {v}" for k, v in value.items()])
                    formatted_values.append(f"({dict_entries})")
                else:
                    formatted_values.append(value)
            ltm_context.append(f"{key.capitalize()}: {', '.join(formatted_values)}")

    # Short-Term Memory context generation (user's input and bot's response)
    short_term_context = [f"User: {entry['input']} | Erina: {entry['output']}" for entry in short_term_memory]
    
    # Combine the short-term memory and long-term memory context
    return "\n".join(short_term_context[-MemoryLength:] + ltm_context)


# Basic Text-2-Text Module

def discord_chat():
    load_dotenv()  # .env 파일에서 디스코드 토큰을 로드
    TOKEN = os.getenv('DISCORD_TOKEN')

    # 디스코드 클라이언트 설정
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'We have logged in as {client.user.name}')

    @client.event
    async def on_message(message):
        # 단기 기억 및 장기 기억 로드
        memory = load_short_term_memory('data/erina_short_term_memory.json')
        long_term_memory = load_long_term_memory('data/erina_long-term-memory.json')

        if message.author == client.user:
            return  # 봇이 보낸 메시지는 무시

        # 유저 메시지 수신
        user_input = message.content

        # short-term memory와 long-term memory를 합친 컨텍스트 생성
        context_input = generate_context_with_ltm(memory, long_term_memory)

        # 유저의 입력을 기존의 컨텍스트에 추가하여 새로운 대화 문맥 생성
        context_input += f"\nUser: {user_input}"  # 유저 입력을 추가

        # 대화 처리 (스트림 모드 없이 바로 응답 반환)
        response = ollama.chat(model=GlobalModel, messages=[{'role': 'user', 'content': context_input}], stream=False)
        response_text = response['message']['content']

        # Erina의 이름 없이 메시지 전송
        await message.channel.send(response_text)

        # 새로운 대화 기록을 단기 기억에 추가 (사용자 입력과 봇 응답 별도로 저장)
        memory.append({"input": user_input, "output": response_text, "rating": 5})

        # 단기 기억 저장
        save_short_term_memory('data/erina_short_term_memory.json', memory)

    # 디스코드 클라이언트 실행
    client.run(TOKEN)

if __name__ == "__main__":
    initialize_model()
    main_menu()
