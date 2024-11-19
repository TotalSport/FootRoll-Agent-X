import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'swarm')))
import time
import json
from swarm import Swarm
from swarm.repl.repl import run_demo_loop
from agents import based_agent
import openai
import io
from dotenv import load_dotenv
from twitter_utils import TwitterBot, api_v1, client_v2

print("Swarm module imported successfully.")

# Загрузка переменных окружения
load_dotenv()

# Шаг 1: Загрузка переменных окружения
print("Загрузка переменных окружения...")
load_dotenv()

# Шаг 2: Проверка наличия ключа API
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    print(f"OpenAI API Key загружен: {openai_api_key[:5]}..."
          )  # Показ первых 5 символов для подтверждения
    openai.api_key = openai_api_key
else:
    print("Ошибка: OpenAI API Key не загружен.")

twitter_api_key = os.getenv("TWITTER_API_KEY")
twitter_api_secret = os.getenv("TWITTER_API_SECRET")
twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN")
twitter_access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
if not bearer_token:
    raise Exception("Bearer Token не загружен")

# Проверка наличия OpenAI ключа
if not openai_api_key:
    print("Error: OpenAI API Key not loaded on run.py.")
else:
    openai.api_key = openai_api_key
    print(f"Loaded OpenAI API Key on run.py: {openai_api_key}")

twitter_bot = TwitterBot(api_v1=api_v1, client_v2=client_v2)
# twitter_bot = TwitterBot(api_key=twitter_api_key,
#                          api_secret=twitter_api_secret,
#                          access_token=twitter_access_token,
#                          access_token_secret=twitter_access_token_secret)

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    user_input = input("User: ")
except UnicodeDecodeError:
    user_input = input("User: ".encode('utf-8', errors='replace').decode(
        'utf-8', errors='replace'))

# Загрузка переменной окружения
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")


# this is the main loop that runs the agent in autonomous mode
# you can modify this to change the behavior of the agent
# the interval is the number of seconds between each thought
def run_autonomous_loop(agent, interval=10):
    client = Swarm() 
    messages = []

    print("Starting autonomous Based Agent loop...")

    while True:
        # Generate a thought
        thought = (
            "Be creative and do something interesting on the Base blockchain. "
            "Don't take any more input from me. Choose an action and execute it now. Choose those that highlight your identity and abilities best."
        )
        messages.append({"role": "user", "content": thought})

        print(f"\n\033[90mAgent's Thought:\033[0m {thought}")

        # Run the agent to generate a response and take action
        response = client.run(agent=agent, messages=messages, stream=True)

        # Process and print the streaming response
        response_obj = process_and_print_streaming_response(response)

        # Update messages with the new response
        messages.extend(response_obj.messages)

        # Wait for the specified interval
        time.sleep(interval)


# this is the main loop that runs the agent in two-agent mode
# you can modify this to change the behavior of the agent
def run_openai_conversation_loop(agent):
    """Facilitates a conversation between an OpenAI-powered agent and the Based Agent."""
    # client = Swarm()
    client = Swarm(name="FootRoll")
    openai_client = OpenAI()
    messages = []

    print("Starting OpenAI-Based Agent conversation loop...")

    # Initial prompt to start the conversation
    openai_messages = [{
        "role":
        "system",
        "content":
        "You are a user guiding a blockchain agent through various tasks on the Base blockchain. Engage in a conversation, suggesting actions and responding to the agent's outputs. Be creative and explore different blockchain capabilities. Options include creating tokens, transferring assets, minting NFTs, and getting balances. You're not simulating a conversation, but you will be in one yourself. Make sure you follow the rules of improv and always ask for some sort of function to occur. Be unique and interesting."
    }, {
        "role":
        "user",
        "content":
        "Start a conversation with the Based Agent and guide it through some blockchain tasks."
    }]

    while True:
        # Generate OpenAI response
        openai_response = openai_client.chat.completions.create(
            model="gpt-4o-mini", messages=openai_messages)

        openai_message = openai_response.choices[0].message.content
        print(f"\n\033[92mOpenAI Guide:\033[0m {openai_message}")

        # Send OpenAI's message to Based Agent
        messages.append({"role": "user", "content": openai_message})
        response = client.run(agent=agent, messages=messages, stream=True)
        response_obj = process_and_print_streaming_response(response)

        # Update messages with Based Agent's response
        messages.extend(response_obj.messages)

        # Add Based Agent's response to OpenAI conversation
        based_agent_response = response_obj.messages[-1][
            "content"] if response_obj.messages else "No response from Based Agent."
        openai_messages.append({
            "role":
            "user",
            "content":
            f"Based Agent response: {based_agent_response}"
        })

        # Check if user wants to continue
        user_input = input(
            "\nPress Enter to continue the conversation, or type 'exit' to end: "
        )
        if user_input.lower() == 'exit':
            break


def choose_mode():
    while True:
        print("\nAvailable modes:")
        print("1. chat    - Interactive chat mode")
        print("2. auto    - Autonomous action mode")
        print("3. two-agent - AI-to-agent conversation mode")

        choice = input(
            "\nChoose a mode (enter number or name): ").lower().strip()

        mode_map = {
            '1': 'chat',
            '2': 'auto',
            '3': 'two-agent',
            'chat': 'chat',
            'auto': 'auto',
            'two-agent': 'two-agent'
        }

        if choice in mode_map:
            return mode_map[choice]
        print("Invalid choice. Please try again.")


# Boring stuff to make the logs pretty
def process_and_print_streaming_response(response):
    content = ""
    last_sender = ""

    for chunk in response:
        if "sender" in chunk:
            last_sender = chunk["sender"]

        if "content" in chunk and chunk["content"] is not None:
            if not content and last_sender:
                print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                last_sender = ""
            print(chunk["content"], end="", flush=True)
            content += chunk["content"]

        if "tool_calls" in chunk and chunk["tool_calls"] is not None:
            for tool_call in chunk["tool_calls"]:
                f = tool_call["function"]
                name = f["name"]
                if not name:
                    continue
                print(f"\033[94m{last_sender}: \033[95m{name}\033[0m()")

        if "delim" in chunk and chunk["delim"] == "end" and content:
            print()  # End of response message
            content = ""

        if "response" in chunk:
            return chunk["response"]


def pretty_print_messages(messages) -> None:
    for message in messages:
        if message["role"] != "assistant":
            continue

        # print agent name in blue
        print(f"\033[94m{message['sender']}\033[0m:", end=" ")

        # print response, if any
        if message["content"]:
            print(message["content"])

        # print tool calls in purple, if any
        tool_calls = message.get("tool_calls") or []
        if len(tool_calls) > 1:
            print()
        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = json.dumps(json.loads(args)).replace(":", "=")
            print(f"\033[95m{name}\033[0m({arg_str[1:-1]})")


def main():
    mode = choose_mode()

    mode_functions = {
        'chat': lambda: run_demo_loop(based_agent),
        'auto': lambda: run_autonomous_loop(based_agent),
        'two-agent': lambda: run_openai_conversation_loop(based_agent)
    }

    print(f"\nStarting {mode} mode...")
    mode_functions[mode]()


if __name__ == "__main__":
    print("Starting Based Agent...")
    main()
