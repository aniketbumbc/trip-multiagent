# TripMate

A multi-agent travel planner. Describe a trip in one sentence and four agents work through it in order: flights, hotels, a day-by-day itinerary, then one final write-up. Progress streams to the browser as each agent finishes.

Built with LangGraph, FastAPI, OpenAI, Tavily, AviationStack, Postgres and React (Vite + Tailwind).

## How it works

```
React client ──POST /api/travel/stream──▶ FastAPI ──▶ LangGraph
                                                       START → flight_agent → hotel_agent → itinerary_agent → result_agent → END
                ◀────── SSE step / result ──────                  │              │               │                 │
                                                             AviationStack     Tavily        OpenAI LLM        OpenAI LLM
                                                       State checkpointed in Postgres per thread_id
```

| Agent | Source | What it does |
|-------|--------|--------------|
| `flight_agent` | AviationStack | Parses origin/destination from the query and fetches live flights |
| `hotel_agent` | Tavily | Web search for stays |
| `itinerary_agent` | OpenAI | Builds a cost- and time-efficient day plan |
| `result_agent` | OpenAI | Writes the final sectioned answer (summary, flights, hotels, days, budget, tips) |

Each agent catches its own errors, so the graph always produces an answer even if one step fails. Sending a follow-up with the same `thread_id` continues the same trip.

See [project-flow.md](project-flow.md) for the full request flow, state shape and SSE event formats.

## Project layout

```
client/              React UI (Vite, Tailwind)
  src/App.jsx        Trip form, live step tracker, result tabs
  src/api.js         Health check and SSE stream reader
server/
  app.py             FastAPI app and endpoints
  graph.py           LangGraph topology
  agent_orchestration.py  Compiles the graph with the Postgres checkpointer
  base.py            TravelState and TravelRequest
  agents/            flight, hotel (tavily), itinerary, result agents
  tools/             AviationStack and Tavily clients
  db.py              Database connectivity check
  test.py            Run one query from the terminal
```

## Setup

### Requirements

- Python 3.10+
- Node.js 18+
- A Postgres database
- API keys for OpenAI, Tavily and AviationStack

### Environment

Create `server/.env`:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
OPENAI_API_KEY=...
TAVILY_API_KEY=...
AVIATIONSTACK_API_KEY=...
# Optional: origin used when the query names only a destination (default DAC)
DEFAULT_ORIGIN_IATA=BOM
```

### Run the API

```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python db.py      # optional: check the database connection
python app.py     # http://127.0.0.1:8000
```

Checkpoint tables are created automatically on startup.

### Run the client

```bash
cd client
npm install
npm run dev       # http://localhost:5173
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/travel/stream` | Runs the graph and streams `step`, `result` and `error` events (SSE) |
| `POST` | `/api/travel` | Runs the graph and returns the full result as JSON |
| `GET` | `/api/health` | Returns `{ "status": "ok" }` |

Request body:

```json
{ "user_query": "5 days in New York from Mumbai in December", "thread_id": null }
```

Response (`result` event or JSON body):

```json
{
  "thread_id": "user_...",
  "answer": "...",
  "flight_results": "...",
  "hotel_results": "...",
  "itinerary": "...",
  "llm_calls": 4
}
```

Interactive API docs are at `http://127.0.0.1:8000/docs`.

## Notes

- AviationStack returns live flight status, not ticket prices.
- The server runs one graph at a time (`_graph_lock`), so concurrent requests queue.
