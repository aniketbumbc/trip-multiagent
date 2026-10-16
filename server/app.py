import uuid
from langchain_core.messages import HumanMessage
from agent_orchestration import travel_graph
from pathlib import Path
import traceback
import uvicorn

from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from base import TravelRequest
load_dotenv()

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