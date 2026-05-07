# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.23.5",
#     "requests",
# ]
# ///

import marimo

__generated_with = "0.23.5"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # LLM API Tutorial
    """)
    return


@app.cell
def _():
    import marimo as mo
    import requests
    import os

    return mo, requests


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Setup

    For this tutorial, we will use the Open AI chat completions API to make requests to an LLM model provider. We are using the DREAM Lab's AI gateways as the API endpoint. In addition to the gateway's base URL, we need to configure the model to call, and our personal API key.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    api_base_url = mo.ui.text(value="https://litellm.dreamlab.ucsb.edu/v1", 
                              label="API Base URL", 
                              full_width=True)
    model_name = mo.ui.text(value="gemini-3-flash-preview", 
                            label="Model Name", 
                            full_width= True)
    api_key = mo.ui.text(label="API Key (required)", 
                         kind="password", 
                         full_width=True)
    mo.vstack([api_base_url, model_name, api_key])
    return api_base_url, api_key, model_name


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A simple LLM request

    First, we'll define a python function (`call_llm`) that uses an http client library (`requests`) to call the Open AI-compatible endpoint. The function takes a `prompt` and an optional list of `tool` definitions as arguments. It uses the base url, model name, and API key set in the input above. Note the structure of the `data` object in this function: `model` and `messages` are required by the chat completions API. We'll talk more about `tools` below.
    """)
    return


@app.cell
def _(api_base_url, api_key, model_name, requests):
    def call_llm(prompt_or_messages, tools = []):
        request_url = f"{api_base_url.value}/chat/completions"

        # http headers is where we set our api key
        headers = {
            "Authorization": f"Bearer {api_key.value}",
            "Content-Type": "application/json"
        }

        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        else:
            messages = prompt_or_messages

        # the request includes the model name and the prompt.
        data = {
            "model": model_name.value,
            "messages": messages,
            "tools": tools
        }

        # run the request
        return requests.post(request_url, headers=headers, json=data, timeout=60)


    return (call_llm,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's call the function with a question about the whether in Paris. The response is a json data structure with message content.
    """)
    return


@app.cell
def _(call_llm, mo):
    response = call_llm("what is the weather like in Paris?")
    content = response.json()["choices"][0]["message"]["content"]
    mo.md(content) #render the content as markdown below
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The response above is likely wrong. The model doesn't actually know what the current whether in Paris is, so it's "halucinates" a (convincing) answer.

    ## Add a Tool Definition

    To avoid this hallucination, we can add a tool definition to our response. Tool definitions give the LLM additional ways to answer questions they encounter when responding to the prompt. We'll define a `get_weather` tool and included it in our request. In the models response, it may invoke the tool with specific arguments. Let's see how this works.
    """)
    return


@app.cell
def _():
    # get_weather_tool is a tool definition that is included in our LLM API request
    get_weather_tool = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "A place name (e.g., Paris)"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        }
    }
    return (get_weather_tool,)


@app.cell
def _(call_llm, get_weather_tool):
    # The LLM's response now includes a "tool call" to the get_weather tool
    prompt = "what is the weather like in Paris?"
    tool_response = call_llm(prompt, tools = [get_weather_tool])
    tool_response.json()["choices"][0]["message"]["tool_calls"][0]["function"]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Implement get_weather

    Here we implement a Python function that gets the current weather for a location.
    """)
    return


@app.cell
def _(requests):
    def get_weather(location: str, unit: str = "celsius") -> str:
        # A simple implementation using wttr.in
        url = f"https://wttr.in/{location}?format=%C+%t"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text.strip()
        except Exception as e:
            return f"Could not get weather for {location}: {e}"


    return (get_weather,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Using the tool call

    Now we create an `agent_loop` function that takes a prompt and tools. It checks if the model wants to call a tool, runs it if so, and sends the result back to get the final answer.
    """)
    return


@app.cell
def _(call_llm, get_weather):
    import json
    def agent_loop(prompt, tools=[]):
        messages = [{"role": "user", "content": prompt}]
    
        response = call_llm(messages, tools=tools).json()
    
        # Extract the assistant's message
        message = response["choices"][0]["message"]
        messages.append(message)
    
        # Check if the model decided to call any tools
        if "tool_calls" in message and message["tool_calls"]:
            for tool_call in message["tool_calls"]:
                if tool_call["function"]["name"] == "get_weather":
                    # Parse arguments
                    args = json.loads(tool_call["function"]["arguments"])
                    location = args.get("location")
                
                    # Call our actual Python function
                    weather_result = get_weather(location)
                
                    # Append the tool's response to the message history
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": "get_weather",
                        "content": weather_result
                    })
        
            # Second LLM call with the tool results included
            second_response = call_llm(messages, tools=tools).json()
            return second_response["choices"][0]["message"]["content"]
        else:
            # If no tools were called, just return the initial response
            return message["content"]


    return (agent_loop,)


@app.cell(hide_code=True)
def _(agent_loop, get_weather_tool, mo):
    agent_response = agent_loop("What is the weather like in Paris?", tools=[get_weather_tool])
    mo.md(f"**Final Agent Response:** {agent_response}")
    return


if __name__ == "__main__":
    app.run()
