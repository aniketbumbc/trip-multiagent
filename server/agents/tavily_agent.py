from typing import TypedDict,Annotated
from tools.tavily_tool import search_tavily
from base import TravelState
from langchain_core.messages import AIMessage




def hotel_agent(state:TravelState) -> TravelState:
    """
    Hotel agent is responsible for finding the best hotel for the user.
    """
    query = state.get("user_query","")
    llm_calls = state.get("llm_calls",0) + 1
    if not query:
        hotel_dict = "No hotel query provided"
    else:
        try:
            hotel_dict = search_tavily(query)
        except Exception as exc:
            hotel_dict = f"Hotel search failed: {exc}"
    return {
        "hotel_results":hotel_dict,
        "messages":[AIMessage(content=hotel_dict)],
        "llm_calls":llm_calls,
    }