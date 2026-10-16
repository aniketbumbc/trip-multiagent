from typing import TypedDict,Annotated
from tools.flight_tool import search_flights
from base import TravelState
from langchain_core.messages import AIMessage
def flight_agent(state:TravelState) -> TravelState:
    """
    Flight agent is responsible for finding the best flight for the user.
    """
    query = state.get("user_query","")
    llm_calls = state.get("llm_calls",0) + 1
    if not query:
        flights_data = "No flight query provided"
    else:
        try:
            flights_data = search_flights(query)
        except Exception as exc:
            flights_data = f"Flight search failed: {exc}"
    return {
        "flight_results":flights_data,
        "messages":[AIMessage(content=flights_data)],
        "llm_calls":llm_calls,
    }