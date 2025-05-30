import os
import sys
import yaml
import argparse
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env unless running on Render
if os.environ.get("RENDER") != "true":
    load_dotenv()

# ✅ Explicitly pass the API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Make sure it's in your .env file.")

client = OpenAI(api_key=api_key)

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_lines(path):
    with open(path, "r") as f:
        lines = f.read().split("\n")
        return [line.strip() for line in lines if line.strip() and not line.lower().startswith("msg")]

def build_system_prompt(config, script_lines):
    return f"""
You are {config['bot']['identity']}.
Speak casually and confidently over SMS — never say you're a bot.
You are the founder of Limitless, booking real buyer calls for life insurance agents.

Follow this message sequence exactly, step-by-step:

{chr(10).join([f"{i+1}. {line}" for i, line in enumerate(script_lines)])}

Only send one message at a time. If the user aligns early, skip ahead as needed.
If they object, reply briefly then return to the next step.
Never reintroduce yourself. Never repeat a message.
"""

def test_bot(config_path):
    config_path = os.path.abspath(config_path)
    base_path = os.path.dirname(config_path)
    config = load_yaml(config_path)

    script_path = os.path.join(base_path, config['bot']['script_file'])
    script_lines = load_lines(script_path)
    system_prompt = build_system_prompt(config, script_lines)

    step_index = 0
    conversation = []

    print("\n--- Limitless Bot Testing ---")
    print(f"Bot: {config['bot']['name']} | Channel: sms\n")

    while step_index < len(script_lines):
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        conversation.append({"role": "user", "content": user_input})
        messages = [{"role": "system", "content": system_prompt}] + conversation

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

        reply = response.choices[0].message.content.strip()
        print(f"\nMickey: {reply}\n")
        conversation.append({"role": "assistant", "content": reply})

        # Advance to next message unless user objects
        if any(word in user_input.lower() for word in ["no", "not interested", "wtf", "scam"]):
            continue  # Let the model reply, but don't advance yet
        else:
            step_index += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to config YAML file")
    args = parser.parse_args()
    test_bot(args.config)
