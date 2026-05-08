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
    import json

    return json, mo, os, requests


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Setup

    For this tutorial, we will use the Open AI chat completions API to make requests to an LLM model provider. We are using the DREAM Lab's AI gateways as the API endpoint. In addition to the gateway's base URL, we need to configure the model to call, and our personal API key.
    """)
    return


@app.cell(hide_code=True)
def _(mo, os):
    # set API base url, model, and api key
    default_base_url = "https://litellm.dreamlab.ucsb.edu"
    default_model = "gemini-3-flash-preview"
    api_base_url = os.getenv("LLM_API_BASE_URL") or default_base_url
    model_name = os.getenv("LLM_API_MODEL") or default_model
    api_key = os.getenv("LLM_API_KEY")
    mo.md(
        "**Configuration**:\n"
        + f"- API Base URL (`api_base_url`): {api_base_url}\n"
        + f"- Model Name (`model_name`): {model_name}"
    )
    return api_base_url, api_key, model_name


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A simple LLM request

    First, we'll define a python function (`call_llm`) that uses an http client library (`requests`) to call the Open AI-compatible API. The function takes a single argument, the prompt to send to the llm. It uses a pre-configured API base url, model name, and API key. Note the structure of the `data` object in this function: `model` and `messages` are required by the chat completions API.
    """)
    return


@app.cell
def _(api_base_url, api_key, model_name, requests):
    def call_llm(prompt):
        # URL for the chat completions API endpoint:
        request_url = f"{api_base_url}/v1/chat/completions"

        # http headers is where we set our api key and
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # the request includes the model name and the prompt.
        data = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        # return the json response of the request
        return requests.post(
            request_url,
            headers=headers,
            json=data,
            timeout=60
        ).json()


    return (call_llm,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's call the function with a question about the whether in Paris. The response is a json data structure with the llm's output (and lots of other information we can mostly ignore).
    """)
    return


@app.cell
def _(call_llm):
    paris_weather_response = call_llm("what is the weather in Paris?")
    paris_weather_response
    return (paris_weather_response,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The part of the response we really want `paris_weather_response["choices"][0]["message"]`. This is the LLM's message back to us, responding to the prompt.
    """)
    return


@app.cell(hide_code=True)
def _(paris_weather_response):
    paris_weather_response["choices"][0]["message"]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Here is the message content rendered as markdown:
    """)
    return


@app.cell(hide_code=True)
def _(mo, paris_weather_response):
    mo.md(paris_weather_response["choices"][0]["message"]["content"])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This description of the weather in Paris is likely wrong. The model doesn't actually know what the current conditions are in Paris, so it makes up (or "hallucinates") a convicning reply.

    ## Use 'Tools' to Avoid Hallucinations

    One way to avoid hallucinations in LLM responses is by providing the model with "tools" that it can use. Tool definitions give the LLMs additional ways to answer questions or perform tasks in responding to the prompt. To illustrate, we'll define a `get_weather` tool and included it in our request. In the models response, it may invoke the tool with specific arguments. Let's see how this works.
    """)
    return


@app.cell
def _():
    # get_weather_tool is a tool definition to include in our API request.
    # The tool defines a function (get_weather) that takes one argument.
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
                    }
                },
                "required": ["location"]
            }
        }
    }
    return (get_weather_tool,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We also need to revise our previous `call_llm` function to include the tool definition in the request.
    """)
    return


@app.cell
def _(api_base_url, api_key, model_name, requests):
    def call_llm_with_tool(prompt, tools = []):
        request_url = f"{api_base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "tools": tools # Include tool definitions in the request!
        }
        return requests.post(
            request_url,
            headers=headers,
            json=data,
            timeout=60
        ).json()

    return (call_llm_with_tool,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's see how the LLM response changes with the `get_weather` tool definition included in the request.
    """)
    return


@app.cell
def _(call_llm_with_tool, get_weather_tool):
    paris_weather_toolcall = call_llm_with_tool(
        "what is the weather in Paris?",
        tools = [get_weather_tool]
    )
    paris_weather_toolcall["choices"][0]["message"]
    return (paris_weather_toolcall,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The structure of the response `message` has changed. The (hallucinated) `content` is gone. It has been replaced with a list of `tool_calls`. Let's take a closer look at the first tool call in the list, and specifically, its `function` block.
    """)
    return


@app.cell
def _(paris_weather_toolcall):
    paris_weather_toolcall["choices"][0]["message"]["tool_calls"][0]["function"]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `tool_calls` block includes the names and arguments for functions we defined in the tool definitions. The expectation is that we will run these tools ourselve: the output from `get_weather("Paris")` is used as additional context for grounding the LLM's response.

    Our `get_weather_tool` is just a tool *definition*, which is included in our request. We have yet to implement the `get_weather` function so we can run it. Let's do that next.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Implement get_weather

    Here is a simple implementation of the `get_weather` function that uses the https://wttr.in API.
    """)
    return


@app.cell
def _(requests):
    def get_weather(location: str) -> str:
        # A simple implementation using wttr.in
        url = f"https://wttr.in/{location}"
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
    ## Running the tool calls

    For the LLM to use the output from the tool call, we need run the tool and send a new request with the additional context. To do this, let's once again revise our function for calling the llm.
    """)
    return


@app.cell
def _(
    api_base_url,
    api_key,
    get_weather,
    get_weather_tool,
    json,
    mo,
    model_name,
    requests,
):
    def call_llm_with_context(messages = [], tools = []):
        request_url = f"{api_base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model_name,
            "messages": messages,
            "tools": tools
        }
        resp = requests.post(
            request_url,
            headers=headers,
            json=data,
            timeout=60
        ).json()
        return resp["choices"][0]["message"]



    # messages is our full context. Initially, just the user prompt
    messages = [
        {"role": "user", "content": "What is the weather in Paris?"}
    ]

    # initial response with tool calls
    msg1 = call_llm_with_context(messages,[get_weather_tool])

    # add llm's initial response to the context
    messages.append(msg1)

    # run tool_calls and add output to context
    for call in msg1["tool_calls"]:
        args = json.loads(call["function"]["arguments"])
        name = call["function"]["name"]
        if name == "get_weather":
            weather = get_weather(args["location"])
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": weather
            })
    
    # llm request with initial response + tool call output
    msg2 = call_llm_with_context(messages, tools = [get_weather_tool])

    # show the final response
    mo.md(msg2["content"])
    return


if __name__ == "__main__":
    app.run()
