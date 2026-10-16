import asyncio
import json
import queue
import threading
import traceback
import uuid

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import HumanMessage

from agent_orchestration import travel_graph
from base import TravelRequest

load_dotenv()

AGENT_STEPS = ["flight_agent", "hotel_agent", "itinerary_agent", "result_agent"]
_graph_lock = threading.Lock()

app = FastAPI(title="Travel Agent API",description="LangGraph multi-agent travel planner API",version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def run_travel_agent(user_query:str,thread_id:str | None = None):
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable":{
            "thread_id":thread_id
        }
    }
    with _graph_lock:
        result = travel_graph.invoke({
            "messages":[HumanMessage(content=user_query)],
            "user_query":user_query,
            "flight_results":"",
            "hotel_results":"",
            "itinerary":"",
            "llm_calls":0
        },config=config)

    final_result = result.get("messages",[])[-1].content
    return {
        "thread_id":thread_id,
        "answer":final_result,
        "flight_results":result.get("flight_results",""),
        "hotel_results":result.get("hotel_results",""),
        "itinerary":result.get("itinerary",""),
        "llm_calls":result.get("llm_calls",0)
    }
 


@app.post("/api/travel")
async def travel_planner(request:TravelRequest):
    try:
        user_query = request.user_query.strip()
        if not user_query:
            raise HTTPException(status_code=400,detail="User query is required")
        thread_id = request.thread_id or f"user_{uuid.uuid4().hex}"
        result = run_travel_agent(user_query,thread_id)
        return JSONResponse(
            content={
                "thread_id":result["thread_id"],
                "answer":result["answer"],
                "flight_results":result["flight_results"],
                "hotel_results":result["hotel_results"],
                "itinerary":result["itinerary"],
                "llm_calls":result["llm_calls"]
            },
            status_code=200,
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            content={"error":str(e)},
            status_code=500,
            headers={"Content-Type":"application/json"}
        )

def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _message_text(message) -> str:
    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content", "")
    return content or ""


def _result_payload(thread_id: str, values: dict) -> dict:
    messages = values.get("messages") or []
    answer = _message_text(messages[-1]) if messages else ""
    return {
        "thread_id": thread_id,
        "answer": answer,
        "flight_results": values.get("flight_results", ""),
        "hotel_results": values.get("hotel_results", ""),
        "itinerary": values.get("itinerary", ""),
        "llm_calls": values.get("llm_calls", 0),
    }


def _next_step(step: str) -> str | None:
    try:
        index = AGENT_STEPS.index(step)
    except ValueError:
        return None
    if index + 1 >= len(AGENT_STEPS):
        return None
    return AGENT_STEPS[index + 1]


def _stream_travel(user_query: str, thread_id: str, events: queue.Queue) -> None:
    config = {"configurable": {"thread_id": thread_id}}
    graph_input = {
        "messages": [HumanMessage(content=user_query)],
        "user_query": user_query,
        "flight_results": "",
        "hotel_results": "",
        "itinerary": "",
        "llm_calls": 0,
    }
    try:
        events.put(_sse("step", {"step": AGENT_STEPS[0], "status": "started"}))
        with _graph_lock:
            for chunk in travel_graph.stream(graph_input, config, stream_mode="updates"):
                for step in chunk:
                    events.put(_sse("step", {"step": step, "status": "completed"}))
                    following = _next_step(step)
                    if following:
                        events.put(_sse("step", {"step": following, "status": "started"}))
            values = travel_graph.get_state(config).values
        events.put(_sse("result", _result_payload(thread_id, values)))
    except Exception as exc:
        traceback.print_exc()
        events.put(_sse("error", {"error": str(exc)}))
    finally:
        events.put(None)


async def _travel_events(user_query: str, thread_id: str):
    events = queue.Queue()
    threading.Thread(
        target=_stream_travel,
        args=(user_query, thread_id, events),
        daemon=True,
    ).start()
    loop = asyncio.get_running_loop()
    while True:
        item = await loop.run_in_executor(None, events.get)
        if item is None:
            break
        yield item


@app.post("/api/travel/stream")
async def travel_planner_stream(request: TravelRequest):
    user_query = request.user_query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="User query is required")
    thread_id = request.thread_id or f"user_{uuid.uuid4().hex}"
    return StreamingResponse(
        _travel_events(user_query, thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


#health check endpoint
@app.get("/api/health")
async def health_check():
    return JSONResponse(content={"status":"ok"},status_code=200)

#documentation endpoint
@app.get("/api/docs")
async def get_docs():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run("app:app",host="127.0.0.1",port=8000,reload=True)