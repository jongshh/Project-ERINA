from transformers import pipeline
import nltk
import json
import torch
import os
from nltk.sentiment import SentimentIntensityAnalyzer
from transformers import T5Tokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments

# Set device for GPU usage
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Is CUDA available:", torch.cuda.is_available())
print("Number of GPUs:", torch.cuda.device_count())
print("Current CUDA device:", torch.cuda.current_device() if torch.cuda.is_available() else "No GPU found")
print("CUDA device name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU found")

# Load the dataset from a JSON file
def load_dataset(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        dataset = json.load(file)
    return dataset

# Prepare training data
def prepare_weighted_data(conversations):
    inputs = [f"Input: {item['input']}" for item in conversations]
    outputs = [f"Output: {item['output']}" for item in conversations]
    weights = [item['rating'] for item in conversations]
    return inputs, outputs, weights

def load_saved_model():
    if os.path.exists('models/erina_t5'):
        model = T5ForConditionalGeneration.from_pretrained('models/erina_t5').to(device)  # Load custom model
        tokenizer = T5Tokenizer.from_pretrained('models/erina_t5')
        return model, tokenizer
    else:
        model = T5ForConditionalGeneration.from_pretrained("t5-small").to(device)  # Load base T5 model
        tokenizer = T5Tokenizer.from_pretrained("t5-small", legacy=False)
        return model, tokenizer

# Load model and tokenizer
model, tokenizer = load_saved_model()

# Fine-tune the model
def fine_tune_model(inputs, outputs, weights):
    # Tokenize the inputs and outputs
    input_encodings = tokenizer(inputs, truncation=True, padding=True, return_tensors="pt")
    output_encodings = tokenizer(outputs, truncation=True, padding=True, return_tensors="pt")

    # Ensure the labels have the same length as the inputs
    output_encodings['input_ids'] = output_encodings['input_ids'][:, :input_encodings['input_ids'].shape[1]]

    # Prepare the training dataset
    class ChatDataset(torch.utils.data.Dataset):
        def __init__(self, encodings, labels, weights):
            self.encodings = encodings
            self.labels = labels
            self.weights = weights  # Store weights for loss calculation

        def __getitem__(self, idx):
            item = {key: val[idx] for key, val in self.encodings.items()}  # Move to GPU
            item['labels'] = self.labels['input_ids'][idx]  # Move to GPU
            item['weight'] = self.weights[idx]  # Add weight to item
            return item

        def __len__(self):
            return len(self.encodings['input_ids'])

    dataset = ChatDataset(input_encodings, output_encodings, weights)

    # Training arguments
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=3,
        per_device_train_batch_size=2,
        save_steps=10_000,
        save_total_limit=2,
        fp16=True,  # Mixed precision training (optional)
        weight_decay=0.01,  # Add weight decay if needed
    )

    trainer = Trainer(
        model=model.to(device),  # Model is already on GPU
        args=training_args,
        train_dataset=dataset,
    )

    trainer.train()  # Train the model

    model.save_pretrained('models/erina_t5')  # Save the model
    tokenizer.save_pretrained('models/erina_t5')  # Save the tokenizer

# Load the pre-trained model using pipeline
def load_model():
    chatbot = pipeline("text2text-generation", model=model, tokenizer=tokenizer, device=0)  # Load model for text generation
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
def save_conversation(filename, conversations):
    try:
        # Load existing conversations
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as file:
                existing_conversations = json.load(file)
        else:
            existing_conversations = []

        # Remove duplicates from the current conversations
        unique_conversations = [entry for entry in conversations if entry not in existing_conversations]

        # Append new unique conversations to existing ones
        existing_conversations.extend(unique_conversations)

        # Write all conversations back to the file with indentation for readability
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(existing_conversations, file, ensure_ascii=False, indent=4)  # Add indent=4 for pretty printing

    except Exception as e:
        print(f"Error saving conversation: {e}")


def chat():
    dataset = load_dataset('data/erina_memory.json')
    inputs, outputs, weights = prepare_weighted_data(dataset)  # Use the new weighted data preparation
    fine_tune_model(inputs, outputs, weights)  # Initial fine-tuning with the dataset

    print("Hello! I am Erina. Type 'exit' to quit.")
    chatbot = load_model()
    context = []
    conversations = []  # Conversation history list

    conversations.extend(dataset)  # Merge existing data with new conversation history

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Erina: Goodbye!")
            break

        context.append(f"You: {user_input}")  # Add user input to context
        
        context_input = "\n".join(context[-5:])  # Use the last 5 messages
        response = chatbot(f"\n{context_input}\nErina:", max_new_tokens=50, do_sample=True, temperature=0.9, top_k=50, top_p=0.95)[0]['generated_text'].strip()

        response = response.split('Erina:')[-1].strip()  # Use only the text after 'Erina:'
        print(f"Erina: {response}")
        
        context.append(f"Erina: {response}")  # Add AI response to context

        try:
            rating = int(input("Rate my response from 1 to 10 (1 = terrible, 10 = excellent): "))
            if rating < 1 or rating > 10:
                print("Please enter a valid rating between 1 and 10.")
                continue
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 10.")
            continue

        conversations.append({"input": user_input, "output": response, "rating": rating})  # Record AI's response and rating

        if len(conversations) >= 10:  # Retrain after 10 exchanges
            inputs, outputs, weights = prepare_weighted_data(conversations)  # Prepare weighted data
            fine_tune_model(inputs, outputs, weights)  # Fine-tune the model
            conversations.clear()  # Clear conversation history

        save_conversation('data/erina_memory.json', conversations)
        conversations.clear()  # Clear conversation history

# Run the chat function if the script is executed directly
if __name__ == "__main__":
    chat()
