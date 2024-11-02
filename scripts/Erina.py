import json
import os
import ollama
import random
import time
import threading
from Identity import *

GlobalModel = 'Erina'
ollama.create(model=GlobalModel, modelfile=modelfile)

# Load the dataset from a JSON file
def load_dataset(filename):
    print(f"Loading dataset from {filename}...")
    with open(filename, 'r', encoding='utf-8') as file:
        dataset = json.load(file)
    print("Dataset loaded successfully.")
    return dataset

# Prepare training data
def prepare_weighted_data(conversations):
    print("Preparing training data...")
    inputs = [f"Input: {item['input']}" for item in conversations]
    outputs = [f"Output: {item['output']}" for item in conversations]
    weights = [item['rating'] for item in conversations]
    return inputs, outputs, weights

def save_conversation(filename, conversations):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            existing_conversations = json.load(file)
    else:
        existing_conversations = []

    unique_conversations = [entry for entry in conversations if entry not in existing_conversations]
    existing_conversations.extend(unique_conversations)

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(existing_conversations, file, ensure_ascii=False, indent=4)

def generate_random_message(context):
    # Generate a random message based on the context
    prompt = "\n".join(context[-5:]) + "\nErina:"
    response = ollama.chat(model=GlobalModel, messages=[{'role': 'user', 'content': prompt}])
    return response['message']['content'].strip()

def random_message_thread(context, random_speak_enabled):
    while True:
        time.sleep(random.randint(10, 30))  # Random interval between 10 to 30 seconds
        if random_speak_enabled.is_set() and context:  # Check if random speak is enabled and if there is context available
            random_message = generate_random_message(context)
            print(f"Erina (random message): {random_message}")
            context.append(f"Erina: {random_message}")

def chat():
    dataset = load_dataset('data/erina_memory.json')
    inputs, outputs, weights = prepare_weighted_data(dataset)

    print("Chat Started, Type 'exit' to quit.")
    context = []
    conversations = []
    conversations.extend(dataset)

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

        response = ollama.chat(model=GlobalModel, messages=[{'role': 'user', 'content': context_input + "\nErina:"}])
        response_text = response['message']['content'].strip()
        print(f"Erina: {response_text}")
        context.append(f"Erina: {response_text}")

        if rating_mode:
            try:
                rating = int(input("Rate my response from 1 to 10 (1 = terrible, 10 = excellent): "))
                if rating < 1 or rating > 10:
                    print("Please enter a valid rating between 1 and 10.")
                    continue
            except ValueError:
                print("Invalid input. Please enter a number between 1 and 10.")
                continue

            conversations.append({"input": user_input, "output": response_text, "rating": rating})

            if len(conversations) >= 10:
                inputs, outputs, weights = prepare_weighted_data(conversations)
                conversations.clear()

            save_conversation('data/erina_memory.json', conversations)
            conversations.clear()

if __name__ == "__main__":
    chat()