# AI Inventory

FastAPI inventory persisted in `products.csv`, with a plain-Python CLI agent and no agent framework. See [README.es.md](README.es.md) for Spanish instructions.

## Setup

Requires Python 3.10+, uv, and a Groq API key with access to your selected model. From the project root:

```bash
uv add fastapi uvicorn groq python-dotenv
```

Commands using `uv run` use the project's `.venv` without requiring manual activation.

Configure `.env` (never commit your key):

```dotenv
GROQ_API_KEY=your_key
GROQ_MODEL=qwen/qwen3.8-27b
INVENTORY_API_URL=http://127.0.0.1:8000
```

Only the key is required; the model and URL default to the values above. The API also accepts `INVENTORY_CSV` and `INVENTORY_ALERT_THRESHOLD` environment variables (default threshold: 10). The agent loads `.env`; use `uv run uvicorn api.app:app --reload --env-file .env` to load it for the API too.

## Start

Keep two terminals open at the project root. The API must be running before the agent starts.

Terminal 1: start the API.

```bash
uv run uvicorn api.app:app --reload
```

Terminal 2: start the agent.

```bash
uv run python agent.py
```

API documentation: http://127.0.0.1:8000/docs. Ask the agent to list stock, register a product, record deliveries or sales, or check low-stock alerts. Type `salir` to exit.

## Stop and Restart

Press Ctrl + C in each terminal, stopping the agent first and then the API. `conversation_log.csv` is appended incrementally and closed after every event, preserving already logged data when a session is interrupted. An interrupted request may have changed stock: check it before repeating the operation.

Run `uv run python agent.py` again in Terminal 2 to restart without restarting the API. In-memory history starts fresh, while previous sessions remain intact in the CSV: new rows are always appended, never overwritten.

Log columns: `actor`, `message`, `tool_call`, `timestamp` (ISO 8601 UTC). User messages, assistant responses, tool calls and tool results are recorded. Logs may contain sensitive inventory information.

## API and Agent

- `GET /inventory`: list products.
- `POST /inventory`: create a product with `name`, `quantity`, `unit`.
- `PATCH /inventory/{product_id}`: update stock using positive or negative `delta`.
- `GET /inventory/alerts?threshold=10`: quantities strictly below the threshold.

The agent observes input, asks the LLM, executes typed tools, feeds results back and repeats until a final response with no pending tools. Each message is limited to 20 rounds; API errors return to the LLM and writes are not automatically retried.

## Truncated Responses

Each Groq request allows up to 4096 generation tokens. If Groq reports reaching that limit, the agent requests a text continuation and joins the fragments before printing. Continuations share the 20-round budget and cannot execute new tools.

Tool calls received in truncated responses are not executed and trigger a warning. If the agent cannot finish the text or exhausts its rounds, it preserves the available fragments and warns about the interruption. Each received fragment is logged separately in the CSV.
