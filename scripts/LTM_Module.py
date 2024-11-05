import json
import os
import ollama

# Flag to check if the L.T.M model is loaded
ltm_model_loaded = False

# Pull the necessary L.T.M model

#Do this on Terminal.

# Define the L.T.M model template // This will Pre-trained
# LTMmodel = '''
# FROM models/LTM/Llama-LTM.gguf
# SYSTEM Your task is extract relevant keywords about Erina's "appearance," "personality," "acquaintances"(merge as single keyword e.g. "(Name)-(Relationship)" single keyword) "likes," "dislikes," and "important-thing" From the conversation. Store this keywords in separate arrays as JSON format. Only Result. No Markdown and Annotation. No Extra description or title.
# '''

# Initialize the L.T.M module
# ollama.create(model='LTM', modelfile=LTMmodel) # Use ollama.chat to use pre-setting LTM
print("LTM Model initialized successfully.")

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
        
        # 각 키에 대해 새로운 데이터를 병합합니다.
        for key in new_data:
            if key == "acquaintances":
                # acquaintances는 dict 객체 리스트이므로 중복 확인을 위한 고유 키 생성
                existing_acquaintances = {f"{item['name']}-{item['relationship']}" for item in long_term_memory[key]}
                
                for new_acquaintance in new_data[key]:
                    # 고유 키가 기존 데이터에 없을 때만 추가
                    unique_key = f"{new_acquaintance['name']}-{new_acquaintance['relationship']}"
                    if unique_key not in existing_acquaintances:
                        long_term_memory[key].append(new_acquaintance)
            else:
                # 나머지 키들은 set을 사용해 중복을 제거한 후 병합
                existing_values = set(long_term_memory[key])
                new_values = set(new_data[key])
                long_term_memory[key] = list(existing_values | new_values)

        # 파일을 갱신합니다.
        file.seek(0)
        json.dump(long_term_memory, file, ensure_ascii=False, indent=4)
        file.truncate()


# Generate long-term memory from recent conversations

CovLength = 15 # 1~16 is Best Option to do.

def generate_long_term_memory(recent_conversations):
    if len(recent_conversations) < CovLength:
        print("Warning: Not enough recent conversations to generate long-term memory.")
        return

    # Extract traits with LTM model
    context = "\n".join([f"User: {conv['input']} | Erina: {conv['output']}" for conv in recent_conversations])
    print("Context Length: " + str(CovLength))

    response = ollama.chat(model='LTM', messages=[{'role': 'user', 'content': context}])
    
    # Check the response type
    print("Response from LTM model:")
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
