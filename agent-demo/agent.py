import os
import json
import requests
import dotenv

dotenv.load_dotenv()

# set API base url, model, and api key
default_base_url = "https://litellm.dreamlab.ucsb.edu"
default_model = "gemini-3-flash-preview"
api_base_url = os.getenv("LLM_API_BASE_URL") or default_base_url
model_name = os.getenv("LLM_API_MODEL") or default_model
api_key = os.getenv("LLM_API_KEY")

# inboxes is a fake email inbox used by our `send_message` tool. It's a dict
# that maps recipient names to a list of received messages.
inboxes = {}


# primary agent loop: initial prompt and tool definitions.
def agent_loop(prompt, tools=None):
    """
    Run the main agent loop, interacting with the LLM and executing any requested tools.

    Args:
        prompt (str): The initial user prompt.
        tools (list, optional): A list of tuples containing (tool_schema, tool_function). Defaults to None.

    Returns:
        list: The complete conversation history including user, assistant, and tool messages.
    """
    tools = tools or []

    # Separate schemas for the API and build a dictionary of implementations
    tool_schemas = [schema for schema, func in tools]
    tool_funcs = {schema["function"]["name"]: func for schema, func in tools}

    # messages is our full context. Initially, just the user prompt
    messages = [{"role": "user", "content": prompt}]
    while True:
        msg = call_llm(messages, tools=tool_schemas)
        messages.append(msg)

        # break the loop when the response is not a tool call
        if not msg.get("tool_calls"):
            break

        # run all tool calls in the message and append
        # tool call results to messages
        for call in msg.get("tool_calls", []):
            args = json.loads(call["function"]["arguments"])
            name = call["function"]["name"]

            if name in tool_funcs:
                func = tool_funcs[name]
                try:
                    result = func(**args)
                except Exception as e:
                    result = f"Error executing {name}: {e}"
            else:
                result = f"Error: Tool {name} not found."

            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": str(result)}
            )

    return messages


# call_llm is used to make requests to the model provider.
def call_llm(messages=None, tools=None):
    """
    Make a request to the LLM Chat Completion API.

    Args:
        messages (list, optional): The conversation history. Defaults to an empty list.
        tools (list, optional): A list of tool schemas available for the LLM to use. Defaults to None.

    Returns:
        dict: The message response from the LLM.

    Raises:
        requests.exceptions.HTTPError: If the API request fails.
    """
    messages = messages or []
    request_url = f"{api_base_url}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": model_name,
        "messages": messages,
    }
    if tools:
        data["tools"] = tools

    response = requests.post(request_url, headers=headers, json=data, timeout=60)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Server Error: {response.text}")
        raise e

    resp = response.json()
    return resp["choices"][0]["message"]


# get_weather_schema is metadata describing the `get_weather` tool
# that is included in our llm requests. It describes what the function
# does and its required parameters. This structure conforms with the
# Chat Completion API (`ChatCompletionTool`).
get_weather_schema = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "A place name (e.g., Paris)",
                }
            },
            "required": ["location"],
        },
    },
}


# get_weather is a our implementation of the function described in
# get_weather_schema.
def get_weather(location: str) -> str:
    """
    Fetch the current weather for a given location using wttr.in.

    Args:
        location (str): The name of the city or location.

    Returns:
        str: A short text description of the weather.
    """
    # A simple implementation using wttr.in
    url = f"https://wttr.in/{location}?format=4"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        return f"Could not get weather for {location}: {e}"


# send_message is metadata describing the `send_message` tool that is included
# in our llm requests.
send_message_schema = {
    "type": "function",
    "function": {
        "name": "send_message",
        "description": "send a message to someone",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "the person to send the message to",
                },
                "message": {
                    "type": "string",
                    "description": "the body of the messsage",
                },
            },
            "required": ["to", "message"],
        },
    },
}


# send message implements the function described in send_message_schema
def send_message(to: str, message: str):
    to_key = to.lower()
    if to_key not in inboxes:
        inboxes[to_key] = []
    inboxes[to_key].append(message)
    return f"Message sent to {to}"


# print_context is a convenience function used to display the conversation
# history
def print_context(messages):
    """
    Print the conversation messages clearly labeled by role, formatting tool calls.

    Args:
        messages (list): A list of message dictionaries from the conversation context.
    """
    for msg in messages:
        role = msg.get("role", "assistant").upper()

        # Print tool calls
        if msg.get("tool_calls"):
            for call in msg["tool_calls"]:
                name = call["function"]["name"]
                args = call["function"]["arguments"]
                print(f"[{role}] Tool Call: {name}({args})")

        # Print message content
        content = msg.get("content")
        if content:
            print(f"[{role}] {content}")


if __name__ == "__main__":
    prompt = "Send a message to Tom about the weather in paris."
    tools = [(get_weather_schema, get_weather), (send_message_schema, send_message)]
    messages = agent_loop(prompt, tools=tools)
    print("--- Conversation Transcript ---")
    print_context(messages)
    print("\n--- Inboxes ---")
    for recipient, user_messages in inboxes.items():
        print(f"## {recipient}'s messages:")
        for msg in user_messages:
            print(f"  - {msg}")
