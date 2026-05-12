## `agent.py`

`agent.py` is a Python script that demonstrates the basic features of an AI agent:

- **Agent Loop**: A loop where the agent receives a prompt, calls the LLM, processes the response (including requested tool calls), executes the tools, and feeds the results back to the LLM until the task is complete (i.e., no more tool calls).
- **Tool Calling**: The ability to provide the LLM with a schema of available functions (tools) it can use. In this example, the agent has two tools:
  - `get_weather(location)`: Fetches the current weather for a specified location using `wttr.in`.
  - `send_message(to, message)`: Simulates sending an email or message to a specific recipient (stores messages in an in-memory dictionary).

The script uses a default user prompt: *"Send a message to Tom about the weather in paris."* The LLM orchestrates calling both tools in sequence to achieve this goal.

### Prerequisites

Before running the script, make sure you have the required dependencies installed (e.g., `requests`, `python-dotenv`) and configure your LLM API settings in a `.env` file or environment variables:
- `LLM_API_KEY` (required)
- `LLM_API_BASE_URL` (optional, defaults to `https://litellm.dreamlab.ucsb.edu`)
- `LLM_API_MODEL` (optional, defaults to `gemini-3-flash-preview`)

### Example Output

When you run `python agent.py`, you'll see a transcript of the conversation as the agent executes tool calls, followed by the contents of the simulated message inboxes.

```console
$ python agent.py
--- Conversation Transcript ---
[USER] Send a message to Tom about the weather in paris.
[ASSISTANT] Tool Call: get_weather({"location": "Paris"})
[TOOL] paris: ☁️  🌡️+59°F 🌬️↘9mph
[ASSISTANT] Tool Call: send_message({"to": "Tom", "message": "The current weather in Paris is ☁️ 59°F with a 9mph wind."})
[TOOL] Message sent to Tom
[ASSISTANT] OK. I've sent that message to Tom.

--- Inboxes ---
## tom's messages:
  - The current weather in Paris is ☁️ 59°F with a 9mph wind.
```
