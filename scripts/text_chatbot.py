from transformers import pipeline
import nltk
import json
import torch
from nltk.sentiment import SentimentIntensityAnalyzer
from transformers import GPT2Tokenizer, GPT2LMHeadModel, Trainer, TrainingArguments

print("Is CUDA available:", torch.cuda.is_available())
print("Number of GPUs:", torch.cuda.device_count())
print("Current CUDA device:", torch.cuda.current_device())
print("CUDA device name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU found")

# Load the dataset from a JSON file
def load_dataset(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        dataset = json.load(file)
    return dataset

# Prepare training data
def prepare_data(dataset):
    inputs = [item['input'] for item in dataset]
    outputs = [item['output'] for item in dataset]
    return inputs, outputs

# Load tokenizer and model
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

# Set padding token to eos_token
tokenizer.pad_token = tokenizer.eos_token

model = GPT2LMHeadModel.from_pretrained("gpt2")

# Fine-tune the model
def fine_tune_model(inputs, outputs):
    # Tokenize the inputs and outputs
    input_encodings = tokenizer(inputs, truncation=True, padding=True, return_tensors="pt")
    output_encodings = tokenizer(outputs, truncation=True, padding=True, return_tensors="pt")

    # Ensure the labels have the same length as the inputs
    output_encodings['input_ids'] = output_encodings['input_ids'][:, :input_encodings['input_ids'].shape[1]]

    # Prepare the training dataset
    class ChatDataset(torch.utils.data.Dataset):
        def __init__(self, encodings, labels):
            self.encodings = encodings
            self.labels = labels

        def __getitem__(self, idx):
            item = {key: val[idx] for key, val in self.encodings.items()}
            item['labels'] = self.labels['input_ids'][idx]
            return item

        def __len__(self):
            return len(self.encodings['input_ids'])

    dataset = ChatDataset(input_encodings, output_encodings)

    # Training arguments
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=3,
        per_device_train_batch_size=2,
        save_steps=10_000,
        save_total_limit=2,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
    )

    trainer.train()  # Train the model

# Load the pre-trained model using pipeline
def load_model():
    chatbot = pipeline("text-generation", model="gpt2")  # Load GPT-2 model for text generation
    return chatbot

# Initialize sentiment intensity analyzer
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

# Analyze sentiment of user input
def analyze_sentiment(user_input):
    sentiment_score = sia.polarity_scores(user_input)
    return sentiment_score

# Main chat function to handle user input and chatbot response
# Save conversation to a JSON file
def save_conversation(filename, user_input, response):
    memory = {
        "input": user_input,
        "output": response
    }
    try:
        with open(filename, 'a', encoding='utf-8') as file:  # Append mode
            json.dump(memory, file, ensure_ascii=False)
            file.write('\n')  # Newline for each entry
    except Exception as e:
        print(f"Error saving conversation: {e}")

def chat():
    # Load and prepare dataset
    dataset = load_dataset('data/erina-memory.json')  # Change to your dataset file name
    inputs, outputs = prepare_data(dataset)

    # Fine-tune the model with the dataset
    fine_tune_model(inputs, outputs)

    print("Hello! I am Erina. Type 'exit' to quit.")
    chatbot = load_model()
    context = []

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Erina: Goodbye!")
            break
        
        # Append user input to context
        context.append(f"You: {user_input}")

        # Generate response from the conversational model
        response = chatbot(user_input, max_new_tokens=50)[0]['generated_text']

        # Clean response to remove unnecessary parts
        response = response.split('\n')[0]  # Keep only the first line
        print(f"Erina: {response.strip()}")

        # Maintain the conversation context
        context.append(f"Erina: {response.strip()}")

        # Save the conversation to memory
        save_conversation('erina_memory.json', user_input, response)

# Run the chat function if the script is executed directly
if __name__ == "__main__":
    chat()
