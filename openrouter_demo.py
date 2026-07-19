"""
OpenRouter-backed agent demo (uses your API key, gitignored in .env).

NOTE: Microsoft Agent Framework 1.0's OpenAIChatClient is Responses-API-only,
and OpenRouter does NOT support the Responses API (it returns
"Invalid Responses API request" on previous_response_id). OpenRouter only
supports the Chat Completions API. So this demo uses the standard `openai`
SDK chat.completions transport directly -- the correct, working path for
OpenRouter -- with real tool-calling, which is what Agent Framework would do
under the hood.

The key is read from .env (OPENROUTER_API_KEY), never committed.
Default model: deepseek/deepseek-v4-flash. Override with OPENROUTER_MODEL.

Run:  source .venv/bin/activate
      python openrouter_demo.py
"""
import json
import os

from openai import OpenAI

LAB_DIR = os.path.dirname(os.path.abspath(__file__))


def load_key() -> str:
    env_path = os.path.join(LAB_DIR, ".env")
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            if line.strip().startswith("OPENROUTER_API_KEY"):
                return line.strip().split("=", 1)[1].strip()
    return os.environ["OPENROUTER_API_KEY"]


# A simple local tool the model can call
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_revenue_growth",
            "description": "Return the revenue growth percentage from the sample dataset.",
            "parameters": {"type": "object", "properties": {}},
        },
    }
]


def get_revenue_growth() -> str:
    # In a real app this would read the CSV; hardcoded result here for the demo.
    return "Revenue grew from $12,000 (Jan) to $17,500 (Jun), a 45.8% increase."


def main() -> None:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=load_key(),
    )
    model = os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")

    messages = [
        {"role": "system", "content": "You are a concise data analyst."},
        {"role": "user", "content": "Summarize our revenue growth using the data tool."},
    ]

    # first call -- model may request the tool
    resp = client.chat.completions.create(model=model, messages=messages, tools=TOOLS)
    msg = resp.choices[0].message
    messages.append(msg.model_dump())

    if msg.tool_calls:
        for call in msg.tool_calls:
            if call.function.name == "get_revenue_growth":
                result = get_revenue_growth()
                messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": result}
                )

    # second call -- model produces the final answer using the tool result
    resp2 = client.chat.completions.create(model=model, messages=messages)
    print("=== OpenRouter agent reply ===\n")
    print(resp2.choices[0].message.content)


if __name__ == "__main__":
    main()
