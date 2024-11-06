import ollama
import sys
import re
import io
import contextlib
import requests
from googlesearch import search 
from bs4 import BeautifulSoup

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
                    model="Erina",
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
    return history
    pass

def main():
    history = []
    print("OLLAMA Chat Interface. Press CTRL+C to interrupt the response or CTRL+D to exit.")

    try:
        while True:
            user_input = input(">>> ")
            if user_input.lower() == "/exit":
                print("Exiting chat.")
                break

            history.append({"role": "user", "content": user_input})
            
            try:
                # Process interaction with model including execution of code blocks
                history = interact_with_model(history)

            except KeyboardInterrupt:
                print("\nResponse interrupted by user.")
                history.append({'role': 'assistant', 'content': '[Interrupted by user]'})
                print()  # Ensure the next user prompt appears on a new line

    except EOFError:
        print("\nChat terminated via CTRL+D.")

if __name__ == "__main__":
    main()