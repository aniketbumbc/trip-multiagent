# Project Flow

TripMate is a multi-agent travel planner. A React client sends one free-text trip request to a FastAPI server, which runs a LangGraph pipeline of four agents (flights → hotels → itinerary → final write-up) and streams each step back to the UI. Graph state is checkpointed in Postgres per `thread_id`, so a trip can be continued with follow-up requests.

## High-level flow

```
┌──────────────────────┐   POST /api/travel/stream    ┌──────────────────────────┐
│  React client (Vite) │ ───────────────────────────▶ │  FastAPI (server/app.py) │
│  client/src/App.jsx  │ ◀─────────────────────────── │                          │
└──────────────────────┘   SSE: step / result / error └────────────┬─────────────┘
                                                                    │ travel_graph.stream(...)
                                                                    ▼
          ┌──────────────────────── LangGraph (server/graph.py) ────────────────────────┐
          │                                                                             │
          │  START → flight_agent → hotel_agent → itinerary_agent → result_agent → END  │
          │              │              │               │                 │             │
          │       AviationStack      Tavily        OpenAI LLM        OpenAI LLM         │
          └─────────────────────────────────────────────────────────────────────────────┘
                                                                    │ checkpoint per thread_id
                                                                    ▼
                                                           Postgres (PostgresSaver)
```

## 1. Client (`client/`)

| File | Role |
|------|------|
| `src/App.jsx` | Single-page UI: trip textarea, sample prompts, live step tracker, result tabs |
| `src/api.js` | `checkHealth()`, `planTripStream()` (SSE reader), `planTrip()` (non-streaming) |
| `src/formatAnswer.js` | Cleans agent text before Markdown render (expands collapsed tables, converts ISO timestamps to local time) |
| `vite.config.js` | Dev server on `:5173`, proxies `/api` to `http://127.0.0.1:8000` |

Request lifecycle in the UI:

1. On load, `checkHealth()` hits `GET /api/health` and shows "Planner is up / offline".
2. On submit, `planTripStream(query, threadId, onStep)` POSTs `{ user_query, thread_id }` to `/api/travel/stream`.
3. The response body is read as a stream and split on blank lines into SSE blocks:
   - `step` → `onStep({ step, status })` marks an agent `started` or `completed` in the progress bar.
   - `result` → final payload stored in state.
   - `error` → thrown and shown as an error banner.
4. The returned `thread_id` is kept, so the next submit says "Continue this trip" and reuses the same graph thread. "Start a new trip" clears it.
5. Results render in four tabs: **The plan** (`answer`), **Flights**, **Hotels**, **Day by day**. Tabs whose text contains "failed" / "could not" / "not available" are tagged "partial".

## 2. API (`server/app.py`)

| Endpoint | Behaviour |
|----------|-----------|
| `POST /api/travel/stream` | Main path used by the UI. Returns `text/event-stream`. |
| `POST /api/travel` | Blocking version; runs the whole graph and returns JSON once. |
| `GET /api/health` | Returns `{ "status": "ok" }`. |
| `GET /api/docs` | Redirects to FastAPI's `/docs`. |

Request body (`TravelRequest` in `server/base.py`):

```json
{ "user_query": "5 days in New York from Mumbai", "thread_id": null }
```

If `thread_id` is missing, the server generates `user_<uuid>`.

### Streaming internals

1. `travel_planner_stream` validates the query and returns a `StreamingResponse` over `_travel_events(...)`.
2. `_travel_events` starts `_stream_travel` in a daemon thread and relays items from a `queue.Queue` to the async response.
3. `_stream_travel`:
   - emits `step: flight_agent started`;
   - runs `travel_graph.stream(graph_input, config, stream_mode="updates")` under a global `_graph_lock` (one graph run at a time);
   - for each node update, emits `step: <node> completed`, then `step: <next node> started` using the fixed `AGENT_STEPS` order;
   - after the run, reads `travel_graph.get_state(config).values` and emits one `result` event;
   - on exception, emits `error`; always ends by pushing `None` to close the stream.

SSE event shapes:

```
event: step
data: {"step": "hotel_agent", "status": "started"}

event: result
data: {"thread_id": "...", "answer": "...", "flight_results": "...",
       "hotel_results": "...", "itinerary": "...", "llm_calls": 4}

event: error
data: {"error": "..."}
```

## 3. Graph and state

**Compilation** (`server/agent_orchestration.py`): connects to `DATABASE_URL` with psycopg, creates a `PostgresSaver`, runs `setup()` to create checkpoint tables, and compiles `graph` into `travel_graph` with that checkpointer.

**Topology** (`server/graph.py`): strictly linear, no conditional edges.

```
START → flight_agent → hotel_agent → itinerary_agent → result_agent → END
```

**State** (`TravelState` in `server/base.py`):

| Key | Written by | Notes |
|-----|-----------|-------|
| `messages` | every agent | `operator.add` reducer, so messages append (and accumulate across a thread) |
| `user_query` | API input | Raw user text |
| `flight_results` | `flight_agent` | Formatted flight text |
| `hotel_results` | `hotel_agent` | Formatted search results |
| `itinerary` | `itinerary_agent` | LLM-generated plan |
| `llm_calls` | every agent | Incremented once per node (including the two non-LLM agents) |

Each request resets `flight_results`, `hotel_results`, `itinerary` and `llm_calls` in the input; only `messages` carries history within a thread.

## 4. Agents (`server/agents/`)

Every agent catches its own errors and writes a readable failure string instead of raising, so the graph always reaches `result_agent`.

### 4.1 `flight_agent` (`flight_agent.py`)
- Calls `search_flights(user_query)` from `tools/flight_tool.py`.
- Writes `flight_results` and appends an `AIMessage`.

**Flight tool flow** (`server/tools/flight_tool.py`):
1. `parse_route(query)` extracts origin/destination:
   - "all/global/worldwide flights" → no filter;
   - two uppercase IATA codes (e.g. `BOM to JFK`);
   - "from X to Y" / "to Y from X" / "from X" / "to Y" patterns;
   - fallback: city/country mentions; with only one mention, origin defaults to `DEFAULT_ORIGIN_IATA` (env, default `DAC`).
2. `resolve_location_to_iata` maps each place to an airport: direct IATA → city map → country main airport → fuzzy match over `airportsdata`.
3. Calls AviationStack `GET /v1/flights` with `dep_iata` / `arr_iata` (limit 5).
4. `format_flight` renders airline, flight number, status, terminals, gates, scheduled times, delays.
5. Missing API key, request errors, API errors and empty results all return explanatory text. Note: AviationStack gives live/status data, not fares.

### 4.2 `hotel_agent` (`tavily_agent.py`)
- Calls `search_tavily(user_query)` from `tools/tavily_tool.py` (top 3 web results: title, snippet ≤ 300 chars, URL).
- Writes `hotel_results` and appends an `AIMessage`.

### 4.3 `itinerary_agent` (`itinerary_agent.py`)
- Prompts `ChatOpenAI` with flight results, hotel results and the user query, asking for a cost-friendly, time-efficient itinerary.
- Writes `itinerary`; if `OPENAI_API_KEY` is missing or the call fails, writes "Itinerary generation failed: …".

### 4.4 `result_agent` (`result_agent.py`)
- Prompts `ChatOpenAI` (`gpt-4o-mini`) to produce the final answer in sections: Trip Summary, Flight Details, Hotel Details, Day-by-Day Itinerary, Estimated Budget, Final Recommendations.
- Appends the answer as the last `AIMessage`; the API returns that last message as `answer`.
- On failure, falls back to a plain dump of flights, hotels and itinerary with the error reason.

## 5. Persistence and threads

- `config = {"configurable": {"thread_id": thread_id}}` is passed on every run.
- `PostgresSaver` stores a checkpoint after each node, keyed by thread.
- Re-using a `thread_id` resumes the same thread: prior `messages` are kept, and the new run appends to them.
- `server/db.py` is a standalone connectivity check (`python db.py`).

## 6. Configuration

`server/.env`:

| Variable | Used by |
|----------|---------|
| `DATABASE_URL` | Postgres checkpointer (required at startup) |
| `OPENAI_API_KEY` | `itinerary_agent`, `result_agent` |
| `TAVILY_API_KEY` | `hotel_agent` |
| `AVIATIONSTACK_API_KEY` | `flight_agent` |
| `DEFAULT_ORIGIN_IATA` | Default origin when only a destination is given (default `DAC`) |

## 7. Running locally

```bash
# API
cd server
pip install -r requirements.txt
python app.py            # uvicorn on http://127.0.0.1:8000

# Client
cd client
npm install
npm run dev              # http://localhost:5173, /api proxied to :8000
```

`server/test.py` runs one query through `run_travel_agent` from the terminal without the UI.

## 8. End-to-end example

1. User types "5 days in New York from Mumbai in December" and clicks **Plan this trip**.
2. UI → `POST /api/travel/stream` with `thread_id: null`; server assigns `user_<uuid>`.
3. `flight_agent`: `parse_route` → `BOM`, `JFK` → AviationStack → flight list. UI marks Flights done, Hotels active.
4. `hotel_agent`: Tavily search → 3 results. UI marks Hotels done.
5. `itinerary_agent`: OpenAI builds the day plan. UI marks Days done.
6. `result_agent`: OpenAI writes the final sectioned plan. UI marks Write-up done.
7. Server reads final state from the checkpointer and emits `result`; UI shows the tabs and keeps `thread_id` for follow-ups.

## 9. Known gaps

- `GET /api/docs` uses `RedirectResponse`, which is not imported in `app.py`, so that route will error.
- `result_agent` returns a `final_response` key that is not part of `TravelState`.
- `_graph_lock` serialises all graph runs, so concurrent users wait on each other.
- `llm_calls` counts nodes, not actual LLM calls (flight and hotel agents make none).
